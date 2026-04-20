from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from src.builder.vision.image_classifier import extract_page_number

_IMAGE_DESC_BLOCK_RE = re.compile(
    r"<!-- IMAGE_DESCRIPTION: (?P<fname>[^\s]+) -->\n"
    r"<!-- Tipo: [^\n]+ -->\n"
    r"(?:>.*\n)+"
    r"<!-- /IMAGE_DESCRIPTION -->\n*",
    re.MULTILINE,
)
_IMAGE_DESC_ORPHANS_RE = re.compile(
    r"\n*<!-- IMAGE_DESCRIPTION_ORPHANS -->\n.*?<!-- /IMAGE_DESCRIPTION_ORPHANS -->\n*",
    re.DOTALL,
)


def _image_curation_heading(img_type: str) -> str:
    if (img_type or "").strip().lower() == "extração-latex":
        return "[LaTeX extraído]"
    return "[Descrição de imagem]"


def _compact_image_description_text(description: str, max_chars: int = 220) -> str:
    text = re.sub(r"\s+", " ", (description or "")).strip()
    if not text:
        return ""
    sentence_match = re.match(r"(.+?[.!?])(?:\s|$)", text)
    if sentence_match and len(sentence_match.group(1)) >= 40:
        text = sentence_match.group(1).strip()
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip(" ,;:") + "..."


def _normalize_match_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _tokenize_support_text(text: str) -> set[str]:
    weak = {
        "para", "com", "sem", "sobre", "entre", "imagem", "pagina", "figura",
        "teorema", "lista", "aula", "mais", "menos", "corpo", "principal",
    }
    return {
        token
        for token in _normalize_match_text(text).split()
        if len(token) >= 4 and token not in weak
    }


def _build_image_description_lookup(image_curation: dict) -> Dict[str, dict]:
    descriptions: Dict[str, dict] = {}
    compact_groups: Dict[str, List[dict]] = {}

    for page_data in image_curation.get("pages", {}).values():
        if not page_data.get("include_page", True):
            continue
        for fname, img_data in page_data.get("images", {}).items():
            if not img_data.get("include") or not img_data.get("description"):
                continue
            compact = _compact_image_description_text(img_data["description"])
            record = {
                "type": img_data.get("type", "genérico"),
                "description": img_data["description"],
                "compact_description": compact,
                "page_num": extract_page_number(fname),
            }
            descriptions[fname] = record
            compact_groups.setdefault(compact, []).append({"fname": fname, **record})

    for compact, items in compact_groups.items():
        if not compact or len(items) < 2:
            continue
        items.sort(key=lambda item: (item["page_num"] is None, item["page_num"] or 9999, item["fname"]))
        lead = items[0]
        for item in items[1:]:
            if lead["page_num"] is None or item["page_num"] is None:
                continue
            if abs(item["page_num"] - lead["page_num"]) > 1:
                continue
            descriptions[item["fname"]]["duplicate_of"] = {
                "fname": lead["fname"],
                "page_num": lead["page_num"],
                "compact_description": compact,
            }
    return descriptions


def _resolve_image_description_record(
    markdown_fname: str,
    descriptions: Dict[str, dict],
) -> Optional[Tuple[str, dict]]:
    if markdown_fname in descriptions:
        return markdown_fname, descriptions[markdown_fname]

    candidates: List[Tuple[str, dict]] = []
    for original_fname, record in descriptions.items():
        if markdown_fname.endswith(f"-{original_fname}") or markdown_fname == Path(original_fname).name:
            candidates.append((original_fname, record))

    if len(candidates) == 1:
        return candidates[0]

    if candidates:
        page_num = extract_page_number(markdown_fname)
        if page_num is not None:
            page_matches = [
                (original_fname, record)
                for original_fname, record in candidates
                if record.get("page_num") == page_num
            ]
            if len(page_matches) == 1:
                return page_matches[0]
        candidates.sort(key=lambda item: len(item[0]), reverse=True)
        return candidates[0]

    return None


def _build_image_description_block(
    original_fname: str,
    desc_info: dict,
    *,
    image_heading: Callable[[str], str],
) -> str:
    duplicate_of = desc_info.get("duplicate_of")
    desc_lines = []
    if duplicate_of:
        desc_lines.append(
            f"Mesma imagem da página {duplicate_of['page_num']}; mantendo só referência curta."
        )
    else:
        desc_lines.append(desc_info["compact_description"])

    heading = image_heading(desc_info["type"])
    block = (
        f"<!-- IMAGE_DESCRIPTION: {original_fname} -->\n"
        f"<!-- Tipo: {desc_info['type']} -->"
    )
    for i, dl in enumerate(desc_lines):
        if i == 0:
            block += f"\n> **{heading}** {dl}"
        else:
            block += f"\n> {dl}"
    block += "\n<!-- /IMAGE_DESCRIPTION -->"
    return block


def _build_orphan_image_section(
    orphan_items: List[Tuple[str, dict]],
    *,
    image_heading: Callable[[str], str],
) -> str:
    if not orphan_items:
        return ""

    orphan_items = sorted(
        orphan_items,
        key=lambda item: (
            item[1].get("page_num") is None,
            item[1].get("page_num") or 9999,
            item[0],
        ),
    )
    blocks = [
        _build_image_description_block(fname, info, image_heading=image_heading)
        for fname, info in orphan_items
    ]
    return (
        "\n\n<!-- IMAGE_DESCRIPTION_ORPHANS -->\n"
        "## Imagens Curadas\n\n"
        "Descrições preservadas para imagens detectadas no documento, mas sem referência markdown compatível no corpo principal.\n\n"
        + "\n\n".join(blocks)
        + "\n<!-- /IMAGE_DESCRIPTION_ORPHANS -->"
    )


def _split_markdown_sections(markdown: str) -> List[dict]:
    heading_re = re.compile(r"^#{2,6}\s+.+$", re.MULTILINE)
    matches = list(heading_re.finditer(markdown))
    sections: List[dict] = []

    if not matches:
        return [{"heading": "", "body": markdown, "tokens": _tokenize_support_text(markdown)}]

    if matches[0].start() > 0:
        preface = markdown[:matches[0].start()]
        sections.append(
            {"heading": "", "body": preface, "tokens": _tokenize_support_text(preface)}
        )

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        chunk = markdown[start:end]
        first_line, _, remainder = chunk.partition("\n")
        sections.append(
            {
                "heading": first_line.strip(),
                "body": chunk,
                "tokens": _tokenize_support_text(first_line + "\n" + remainder[:1600]),
            }
        )
    return sections


def _score_orphan_against_section(desc_info: dict, section: dict) -> int:
    desc_tokens = _tokenize_support_text(
        str(desc_info.get("compact_description") or desc_info.get("description") or "")
    )
    if not desc_tokens:
        return 0
    section_tokens = set(section.get("tokens") or set())
    overlap = desc_tokens & section_tokens
    score = len(overlap)
    heading_tokens = _tokenize_support_text(section.get("heading") or "")
    score += min(2, len(desc_tokens & heading_tokens))
    return score


def _inject_orphans_near_sections(
    markdown: str,
    orphan_items: List[Tuple[str, dict]],
    *,
    image_heading: Callable[[str], str],
) -> Tuple[str, List[Tuple[str, dict]]]:
    sections = _split_markdown_sections(markdown)
    if len(sections) <= 1:
        return markdown.rstrip(), orphan_items

    section_blocks: Dict[int, List[str]] = {}
    remaining: List[Tuple[str, dict]] = []

    for fname, info in orphan_items:
        best_idx = -1
        best_score = 0
        for idx, section in enumerate(sections):
            score = _score_orphan_against_section(info, section)
            if score > best_score:
                best_score = score
                best_idx = idx
        if best_idx >= 0 and best_score >= 2:
            section_blocks.setdefault(best_idx, []).append(
                _build_image_description_block(fname, info, image_heading=image_heading)
            )
        else:
            remaining.append((fname, info))

    rebuilt_sections: List[str] = []
    for idx, section in enumerate(sections):
        body = str(section["body"]).rstrip()
        blocks = section_blocks.get(idx) or []
        if blocks:
            body += "\n\n" + "\n\n".join(blocks)
        rebuilt_sections.append(body)

    rebuilt = "\n".join(part for part in rebuilt_sections if part).rstrip()
    return rebuilt, remaining


def _low_token_inject_image_descriptions(
    markdown: str,
    image_curation: dict,
    *,
    desc_block_re,
    image_heading: Callable[[str], str],
) -> str:
    if not image_curation or "pages" not in image_curation:
        return markdown

    descriptions = _build_image_description_lookup(image_curation)
    if not descriptions:
        return markdown

    markdown = desc_block_re.sub("", markdown)
    markdown = _IMAGE_DESC_ORPHANS_RE.sub("\n", markdown).rstrip()
    img_re = re.compile(
        r'(!\[[^\]]*\]\((?:[^)]*?/)?)'
        r'([^)/]+\.(?:png|jpg|jpeg|gif|bmp|webp))\)'
    )

    lines = markdown.split("\n")
    result_lines: List[str] = []
    matched_filenames: set[str] = set()
    for line in lines:
        match = img_re.search(line)
        if match:
            fname = match.group(2)
            matched = _resolve_image_description_record(fname, descriptions)
            if matched:
                original_fname, desc_info = matched
                matched_filenames.add(original_fname)
                result_lines.append(
                    _build_image_description_block(
                        original_fname,
                        desc_info,
                        image_heading=image_heading,
                    )
                )
        result_lines.append(line)

    result = "\n".join(result_lines).rstrip()
    orphan_items = [
        (fname, info)
        for fname, info in descriptions.items()
        if fname not in matched_filenames
    ]
    result, remaining_orphans = _inject_orphans_near_sections(
        result,
        orphan_items,
        image_heading=image_heading,
    )
    orphan_section = _build_orphan_image_section(
        remaining_orphans,
        image_heading=image_heading,
    )
    if orphan_section:
        result += orphan_section
    return result + "\n"
