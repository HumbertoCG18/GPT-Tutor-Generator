from __future__ import annotations

from datetime import datetime
import html as html_lib
import re
from typing import Callable, Dict, List

from src.builder.repo_artifacts import rows_to_markdown_table


def extract_url_page_metadata(soup, *, collapse_ws: Callable[[str], str]) -> Dict[str, str]:
    title = ""
    description = ""

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        title = collapse_ws(html_lib.unescape(og_title["content"]))

    if not title and soup.title and soup.title.string:
        title = collapse_ws(html_lib.unescape(soup.title.string))

    desc_tag = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
    )
    if desc_tag and desc_tag.get("content"):
        description = collapse_ws(html_lib.unescape(desc_tag["content"]))

    return {"title": title, "description": description}


def is_probably_noise_container(tag) -> bool:
    attrs = " ".join(
        str(v) for key, v in tag.attrs.items() if key in {"id", "class", "role", "aria-label"}
    ).lower()
    noise_tokens = {
        "nav",
        "menu",
        "sidebar",
        "aside",
        "footer",
        "header",
        "breadcrumb",
        "cookie",
        "consent",
        "banner",
        "popup",
        "modal",
        "share",
        "social",
        "related",
        "recommend",
        "newsletter",
        "comment",
        "advert",
        "ads",
        "pagination",
        "toolbar",
    }
    return any(token in attrs for token in noise_tokens)


def content_score(tag) -> int:
    text_len = len(tag.get_text(" ", strip=True))
    p_count = len(tag.find_all("p"))
    li_count = len(tag.find_all("li"))
    heading_count = len(tag.find_all(re.compile(r"^h[1-6]$")))
    table_count = len(tag.find_all("table"))
    article_bonus = 0
    attrs = " ".join(str(v) for key, v in tag.attrs.items() if key in {"id", "class", "role"}).lower()
    if tag.name in {"article", "main"}:
        article_bonus += 600
    if any(token in attrs for token in {"content", "article", "post", "entry", "main", "markdown", "doc"}):
        article_bonus += 400
    if is_probably_noise_container(tag):
        article_bonus -= 900
    return text_len + p_count * 180 + li_count * 40 + heading_count * 120 + table_count * 160 + article_bonus


def pick_best_content_root(soup):
    direct = soup.find("article") or soup.find("main") or soup.find(attrs={"role": "main"})
    if direct and not is_probably_noise_container(direct):
        return direct

    candidates = []
    for tag in soup.find_all(["article", "main", "section", "div"]):
        text_len = len(tag.get_text(" ", strip=True))
        attrs = " ".join(str(v) for key, v in tag.attrs.items() if key in {"id", "class", "role"}).lower()
        has_content_hint = any(
            token in attrs for token in {"content", "article", "post", "entry", "main", "markdown", "doc"}
        )
        if text_len < 80:
            continue
        if text_len < 250 and not has_content_hint and tag.name not in {"article", "main"}:
            continue
        score = content_score(tag)
        candidates.append((score, text_len, tag))

    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return candidates[0][2]

    return soup.body or soup


def inline_html_to_markdown(node, *, collapse_ws: Callable[[str], str]) -> str:
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""

    name = node.name.lower()
    if name == "br":
        return "\n"

    content = "".join(inline_html_to_markdown(child, collapse_ws=collapse_ws) for child in node.children)
    content = html_lib.unescape(content)

    if name == "a":
        text = collapse_ws(content)
        href = (node.get("href") or "").strip()
        if text and href and href != text:
            return f"[{text}]({href})"
        return text or href
    if name in {"strong", "b"}:
        text = collapse_ws(content)
        return f"**{text}**" if text else ""
    if name in {"em", "i"}:
        text = collapse_ws(content)
        return f"*{text}*" if text else ""
    if name == "code":
        text = collapse_ws(content)
        return f"`{text}`" if text else ""

    return content


def render_html_block_to_markdown(tag, *, collapse_ws: Callable[[str], str]) -> str:
    name = tag.name.lower()

    if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = min(int(name[1]), 6)
        text = collapse_ws(inline_html_to_markdown(tag, collapse_ws=collapse_ws))
        return f"{'#' * level} {text}" if text else ""

    if name == "p":
        return collapse_ws(inline_html_to_markdown(tag, collapse_ws=collapse_ws))

    if name in {"ul", "ol"}:
        lines: List[str] = []
        for idx, li in enumerate(tag.find_all("li", recursive=False), start=1):
            text = collapse_ws(inline_html_to_markdown(li, collapse_ws=collapse_ws))
            if not text:
                continue
            prefix = f"{idx}." if name == "ol" else "-"
            lines.append(f"{prefix} {text}")
        return "\n".join(lines)

    if name == "blockquote":
        text = "\n".join(collapse_ws(line) for line in tag.get_text("\n").splitlines() if collapse_ws(line))
        return "\n".join(f"> {line}" for line in text.splitlines()) if text else ""

    if name == "pre":
        text = tag.get_text("\n", strip=True)
        if not text:
            return ""
        return f"```text\n{text}\n```"

    if name == "table":
        rows: List[List[str]] = []
        for tr in tag.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            row = [collapse_ws(cell.get_text(" ", strip=True)) for cell in cells]
            if any(row):
                rows.append(row)
        return rows_to_markdown_table(rows)

    return ""


def html_to_structured_markdown(
    html: str,
    url: str,
    title: str,
    *,
    collapse_ws: Callable[[str], str],
    truncate_markdown_blocks: Callable[[List[str]], str],
) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for unwanted in soup(["script", "style", "noscript", "svg"]):
        unwanted.extract()
    for selector in ("nav", "header", "footer", "aside", "form"):
        for node in soup.find_all(selector):
            node.decompose()
    for node in soup.find_all(attrs={"hidden": True}):
        node.decompose()
    for node in soup.find_all(style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)):
        node.decompose()

    meta = extract_url_page_metadata(soup, collapse_ws=collapse_ws)
    page_title = title or meta["title"] or url
    description = meta["description"]
    content_root = pick_best_content_root(soup)

    blocks: List[str] = []
    seen: set[str] = set()
    block_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "blockquote", "pre", "table"]
    for tag in content_root.find_all(block_tags):
        if any(parent.name in block_tags for parent in tag.parents if getattr(parent, "name", None)):
            continue
        block = render_html_block_to_markdown(tag, collapse_ws=collapse_ws).strip()
        normalized = collapse_ws(block.replace("\n", " "))
        if not block or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        blocks.append(block)

    if not blocks:
        text = content_root.get_text("\n", strip=True)
        paragraphs = [collapse_ws(part) for part in text.splitlines() if collapse_ws(part)]
        blocks.extend(paragraphs)

    host = ""
    try:
        from urllib.parse import urlparse

        host = urlparse(url).netloc
    except Exception:
        pass

    header_lines = [f"# {page_title}", ""]
    if description:
        header_lines.extend([description, ""])
    header_lines.extend(
        [
            f"- URL: [{url}]({url})",
            f"- Domínio: `{host or 'desconhecido'}`",
            f"- Capturado em: `{datetime.now().isoformat(timespec='seconds')}`",
            "",
            "## Conteúdo Extraído",
            "",
        ]
    )

    body = truncate_markdown_blocks(blocks)
    if not body:
        body = "> Nenhum conteúdo textual relevante foi extraído."
    return "\n".join(header_lines) + body + "\n"
