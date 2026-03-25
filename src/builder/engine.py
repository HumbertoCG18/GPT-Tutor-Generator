from __future__ import annotations
import csv
import html as html_lib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.models.core import (
    BackendRunResult, DocumentProfileReport, FileEntry,
    PipelineDecision, StudentProfile, SubjectProfile
)
from src.utils.helpers import (
    APP_NAME, DEFAULT_OCR_LANGUAGE, DOCLING_CLI, EXAM_CATEGORIES, EXERCISE_CATEGORIES,
    HAS_PDFPLUMBER, HAS_PYMUPDF, HAS_PYMUPDF4LLM, IMAGE_CATEGORIES, MARKER_CLI,
    CODE_EXTENSIONS, LANG_MAP, CODE_CATEGORIES, ASSIGNMENT_CATEGORIES,
    WHITEBOARD_CATEGORIES, STUDENT_BRANCHES,
    ensure_dir, file_size_mb, json_str, pages_to_marker_range,
    parse_page_range, safe_rel, slugify, write_text,
)

if HAS_PYMUPDF:
    import pymupdf
if HAS_PYMUPDF4LLM:
    import pymupdf4llm
if HAS_PDFPLUMBER:
    import pdfplumber

logger = logging.getLogger(__name__)


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _truncate_markdown_blocks(blocks: List[str], max_chars: int = 15000) -> str:
    if not blocks:
        return ""
    out: List[str] = []
    size = 0
    for block in blocks:
        if not block:
            continue
        next_size = size + len(block) + 2
        if next_size <= max_chars:
            out.append(block)
            size = next_size
            continue
        remaining = max_chars - size
        if remaining > 160:
            clipped = block[:remaining].rstrip()
            out.append(clipped + "\n\n> Conteúdo truncado.")
        else:
            out.append("> Conteúdo truncado.")
        break
    return "\n\n".join(out).strip()


def _extract_url_page_metadata(soup) -> Dict[str, str]:
    title = ""
    description = ""

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        title = _collapse_ws(html_lib.unescape(og_title["content"]))

    if not title and soup.title and soup.title.string:
        title = _collapse_ws(html_lib.unescape(soup.title.string))

    desc_tag = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
    )
    if desc_tag and desc_tag.get("content"):
        description = _collapse_ws(html_lib.unescape(desc_tag["content"]))

    return {"title": title, "description": description}


def _is_probably_noise_container(tag) -> bool:
    attrs = " ".join(
        str(v) for key, v in tag.attrs.items()
        if key in {"id", "class", "role", "aria-label"}
    ).lower()
    noise_tokens = {
        "nav", "menu", "sidebar", "aside", "footer", "header", "breadcrumb",
        "cookie", "consent", "banner", "popup", "modal", "share", "social",
        "related", "recommend", "newsletter", "comment", "advert", "ads",
        "pagination", "toolbar",
    }
    return any(token in attrs for token in noise_tokens)


def _content_score(tag) -> int:
    text_len = len(tag.get_text(" ", strip=True))
    p_count = len(tag.find_all("p"))
    li_count = len(tag.find_all("li"))
    heading_count = len(tag.find_all(re.compile(r"^h[1-6]$")))
    table_count = len(tag.find_all("table"))
    article_bonus = 0
    attrs = " ".join(
        str(v) for key, v in tag.attrs.items()
        if key in {"id", "class", "role"}
    ).lower()
    if tag.name in {"article", "main"}:
        article_bonus += 600
    if any(token in attrs for token in {"content", "article", "post", "entry", "main", "markdown", "doc"}):
        article_bonus += 400
    if _is_probably_noise_container(tag):
        article_bonus -= 900
    return text_len + p_count * 180 + li_count * 40 + heading_count * 120 + table_count * 160 + article_bonus


def _pick_best_content_root(soup):
    direct = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
    )
    if direct and not _is_probably_noise_container(direct):
        return direct

    candidates = []
    for tag in soup.find_all(["article", "main", "section", "div"]):
        text_len = len(tag.get_text(" ", strip=True))
        attrs = " ".join(
            str(v) for key, v in tag.attrs.items()
            if key in {"id", "class", "role"}
        ).lower()
        has_content_hint = any(token in attrs for token in {"content", "article", "post", "entry", "main", "markdown", "doc"})
        if text_len < 80:
            continue
        if text_len < 250 and not has_content_hint and tag.name not in {"article", "main"}:
            continue
        score = _content_score(tag)
        candidates.append((score, text_len, tag))

    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return candidates[0][2]

    return soup.body or soup


def _inline_html_to_markdown(node) -> str:
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""

    name = node.name.lower()
    if name == "br":
        return "\n"

    content = "".join(_inline_html_to_markdown(child) for child in node.children)
    content = html_lib.unescape(content)

    if name == "a":
        text = _collapse_ws(content)
        href = (node.get("href") or "").strip()
        if text and href and href != text:
            return f"[{text}]({href})"
        return text or href
    if name in {"strong", "b"}:
        text = _collapse_ws(content)
        return f"**{text}**" if text else ""
    if name in {"em", "i"}:
        text = _collapse_ws(content)
        return f"*{text}*" if text else ""
    if name == "code":
        text = _collapse_ws(content)
        return f"`{text}`" if text else ""

    return content


def _render_html_block_to_markdown(tag) -> str:
    name = tag.name.lower()

    if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = min(int(name[1]), 6)
        text = _collapse_ws(_inline_html_to_markdown(tag))
        return f"{'#' * level} {text}" if text else ""

    if name == "p":
        return _collapse_ws(_inline_html_to_markdown(tag))

    if name in {"ul", "ol"}:
        lines: List[str] = []
        for idx, li in enumerate(tag.find_all("li", recursive=False), start=1):
            text = _collapse_ws(_inline_html_to_markdown(li))
            if not text:
                continue
            prefix = f"{idx}." if name == "ol" else "-"
            lines.append(f"{prefix} {text}")
        return "\n".join(lines)

    if name == "blockquote":
        text = "\n".join(_collapse_ws(line) for line in tag.get_text("\n").splitlines() if _collapse_ws(line))
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
            row = [_collapse_ws(cell.get_text(" ", strip=True)) for cell in cells]
            if any(row):
                rows.append(row)
        return rows_to_markdown_table(rows)

    return ""


def _html_to_structured_markdown(html: str, url: str, title: str) -> str:
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

    meta = _extract_url_page_metadata(soup)
    page_title = title or meta["title"] or url
    description = meta["description"]
    content_root = _pick_best_content_root(soup)

    blocks: List[str] = []
    seen: set = set()
    block_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "blockquote", "pre", "table"]
    for tag in content_root.find_all(block_tags):
        if any(parent.name in block_tags for parent in tag.parents if getattr(parent, "name", None)):
            continue
        block = _render_html_block_to_markdown(tag).strip()
        normalized = _collapse_ws(block.replace("\n", " "))
        if not block or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        blocks.append(block)

    if not blocks:
        text = content_root.get_text("\n", strip=True)
        paragraphs = [_collapse_ws(part) for part in text.splitlines() if _collapse_ws(part)]
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
    header_lines.extend([
        f"- URL: [{url}]({url})",
        f"- Domínio: `{host or 'desconhecido'}`",
        f"- Capturado em: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Conteúdo Extraído",
        "",
    ])

    body = _truncate_markdown_blocks(blocks)
    if not body:
        body = "> Nenhum conteúdo textual relevante foi extraído."
    return "\n".join(header_lines) + body + "\n"

# ---------------------------------------------------------------------------
# Unicode math → LaTeX normalization
# ---------------------------------------------------------------------------

# Mapa de símbolos Unicode matemáticos → comandos LaTeX.
# Aplicado pós-extração para normalizar output de OCR/backends.
_UNICODE_MATH_TO_LATEX = {
    # Quantificadores e lógica
    "∃": r"\exists", "∄": r"\nexists", "∀": r"\forall",
    "∧": r"\land", "∨": r"\lor", "¬": r"\neg", "⊻": r"\oplus",
    "⊢": r"\vdash", "⊣": r"\dashv", "⊨": r"\models",
    "⊤": r"\top", "⊥": r"\bot",
    "⇒": r"\Rightarrow", "⇐": r"\Leftarrow", "⇔": r"\Leftrightarrow",
    "↔": r"\leftrightarrow", "↦": r"\mapsto",
    # Teoria dos conjuntos
    "∈": r"\in", "∉": r"\notin", "∋": r"\ni",
    "⊂": r"\subset", "⊃": r"\supset",
    "⊆": r"\subseteq", "⊇": r"\supseteq",
    "⊄": r"\not\subset", "⊅": r"\not\supset",
    "∪": r"\cup", "∩": r"\cap",
    "∅": r"\emptyset", "∖": r"\setminus",
    # Relações
    "≤": r"\leq", "≥": r"\geq", "≠": r"\neq",
    "≈": r"\approx", "≡": r"\equiv", "≅": r"\cong",
    "∼": r"\sim", "≺": r"\prec", "≻": r"\succ",
    "≪": r"\ll", "≫": r"\gg",
    "≜": r"\triangleq", "≐": r"\doteq",
    # Operadores
    "×": r"\times", "÷": r"\div", "±": r"\pm", "∓": r"\mp",
    "∘": r"\circ", "⊕": r"\oplus", "⊗": r"\otimes",
    "⊙": r"\odot", "†": r"\dagger", "‡": r"\ddagger",
    # Cálculo e análise
    "∫": r"\int", "∬": r"\iint", "∭": r"\iiint",
    "∂": r"\partial", "∇": r"\nabla",
    "∑": r"\sum", "∏": r"\prod", "∐": r"\coprod",
    "∞": r"\infty", "√": r"\sqrt",
    "ℓ": r"\ell", "ℏ": r"\hbar", "ℜ": r"\Re", "ℑ": r"\Im",
    # Letras gregas minúsculas
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\epsilon", "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta",
    "ι": r"\iota", "κ": r"\kappa", "λ": r"\lambda", "μ": r"\mu",
    "ν": r"\nu", "ξ": r"\xi", "ρ": r"\rho", "σ": r"\sigma",
    "τ": r"\tau", "υ": r"\upsilon", "φ": r"\phi", "χ": r"\chi",
    "ψ": r"\psi", "ω": r"\omega", "ϵ": r"\varepsilon", "ϕ": r"\varphi",
    "ϑ": r"\vartheta", "ϱ": r"\varrho", "ς": r"\varsigma",
    # Letras gregas maiúsculas
    "Γ": r"\Gamma", "Δ": r"\Delta", "Θ": r"\Theta", "Λ": r"\Lambda",
    "Ξ": r"\Xi", "Π": r"\Pi", "Σ": r"\Sigma", "Υ": r"\Upsilon",
    "Φ": r"\Phi", "Ψ": r"\Psi", "Ω": r"\Omega",
    # Setas (apenas as inambíguas)
    "⟶": r"\longrightarrow", "⟵": r"\longleftarrow",
    "⟹": r"\Longrightarrow", "⟸": r"\Longleftarrow",
    "↑": r"\uparrow", "↓": r"\downarrow",
    "⟨": r"\langle", "⟩": r"\rangle",
    # Miscelânea
    "□": r"\square", "◇": r"\diamond", "△": r"\triangle",
    "▽": r"\triangledown", "★": r"\star", "⋆": r"\star",
    "⋅": r"\cdot", "…": r"\ldots", "⋯": r"\cdots", "⋮": r"\vdots",
    "ℕ": r"\mathbb{N}", "ℤ": r"\mathbb{Z}", "ℚ": r"\mathbb{Q}",
    "ℝ": r"\mathbb{R}", "ℂ": r"\mathbb{C}",
}

# Regex para encontrar regiões de math (inline e display)
_MATH_INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
_MATH_DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
_MATH_PAREN_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
_MATH_BRACKET_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)

# Build regex para substituição — escapar caracteres regex-special
_UNICODE_MATH_PATTERN = re.compile(
    "|".join(re.escape(ch) for ch in sorted(_UNICODE_MATH_TO_LATEX.keys(), key=len, reverse=True))
)


def _normalize_unicode_math(text: str) -> str:
    """Replace Unicode math symbols with LaTeX commands in a markdown string.

    Strategy:
    - Inside math delimiters ($...$, $$...$$, \\(...\\), \\[...\\]):
      replace Unicode symbols with LaTeX commands (e.g., ∀ → \\forall)
    - Outside math: wrap isolated Unicode math symbols with $...$
    """
    if not text:
        return text

    # Phase 1: Replace inside existing math regions
    def _replace_in_math(m):
        content = m.group(0)
        return _UNICODE_MATH_PATTERN.sub(
            lambda sym: _UNICODE_MATH_TO_LATEX.get(sym.group(0), sym.group(0)),
            content,
        )

    for pattern in (_MATH_DISPLAY_RE, _MATH_INLINE_RE, _MATH_PAREN_RE, _MATH_BRACKET_RE):
        text = pattern.sub(_replace_in_math, text)

    # Phase 2: Wrap remaining Unicode math symbols outside of math delimiters.
    # We split by math regions, process only non-math parts.
    def _wrap_outside_math(text_str: str) -> str:
        # Split on all math delimiters to identify non-math segments
        math_regions = re.compile(
            r"(\$\$.+?\$\$"          # display $$...$$
            r"|(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)"  # inline $...$
            r"|\\\(.+?\\\)"          # \(...\)
            r"|\\\[.+?\\\])",        # \[...\]
            re.DOTALL,
        )
        parts = math_regions.split(text_str)
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # This is a math region — keep as-is
                result.append(part)
            else:
                # Non-math — wrap isolated Unicode math symbols
                part = _UNICODE_MATH_PATTERN.sub(
                    lambda sym: f"${_UNICODE_MATH_TO_LATEX[sym.group(0)]}$",
                    part,
                )
                result.append(part)
        return "".join(result)

    text = _wrap_outside_math(text)
    return text


# ---------------------------------------------------------------------------
# Backend architecture
# ---------------------------------------------------------------------------

class BackendContext:
    def __init__(self, root_dir: Path, raw_target: Path, entry: FileEntry, report: DocumentProfileReport,
                 cancel_check=None, stall_timeout: int = 300):
        self.root_dir = root_dir
        self.raw_target = raw_target
        self.entry = entry
        self.report = report
        self.entry_id = entry.id()
        self.pages = parse_page_range(entry.page_range)
        self.cancel_check = cancel_check    # callable que levanta InterruptedError se cancelado
        self.stall_timeout = stall_timeout  # segundos sem output antes de matar o processo

    def page_label(self) -> str:
        return self.entry.page_range.strip() or "all"


class ExtractionBackend:
    name = "base"
    layer = "base"

    def available(self) -> bool:
        return False

    def run(self, ctx: BackendContext) -> BackendRunResult:
        raise NotImplementedError


class PyMuPDF4LLMBackend(ExtractionBackend):
    name = "pymupdf4llm"
    layer = "base"

    def available(self) -> bool:
        return HAS_PYMUPDF4LLM

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "pymupdf4llm"
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        # Nota: NÃO usar force_ocr=True — pymupdf4llm tem um bug onde chama
        # ocr_function(page) sem verificar se é None quando force_ocr=True.
        # Em vez disso, usamos use_ocr=True (default) que detecta páginas
        # scaneadas automaticamente e usa o OCR embutido do pymupdf (pdfocr_tobytes).
        wants_ocr = bool(ctx.entry.force_ocr) or ctx.report.suspected_scan
        kwargs = {
            "pages": ctx.pages,
            "write_images": bool(ctx.entry.preserve_pdf_images_in_markdown),
            "image_path": str((ctx.root_dir / "staging" / "assets" / "inline-images" / ctx.entry_id).resolve()),
            "use_ocr": wants_ocr,
            "page_separators": True,
        }
        if wants_ocr:
            kwargs["ocr_language"] = ctx.entry.ocr_language.replace(",", "+")
        if not ctx.entry.preserve_pdf_images_in_markdown:
            kwargs["write_images"] = False
            kwargs.pop("image_path", None)
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        md = pymupdf4llm.to_markdown(str(ctx.raw_target), **kwargs)
        if isinstance(md, list):
            body = "\n\n".join(chunk.get("text", "") for chunk in md)
        else:
            body = md

        write_text(out_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, body))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(ctx.root_dir / "staging" / "assets" / "inline-images" / ctx.entry_id, ctx.root_dir) if ctx.entry.preserve_pdf_images_in_markdown else None,
            notes=["Markdown gerado com PyMuPDF4LLM."],
        )


class PyMuPDFBackend(ExtractionBackend):
    name = "pymupdf"
    layer = "base"

    def available(self) -> bool:
        return HAS_PYMUPDF

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "pymupdf"
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        doc = pymupdf.open(str(ctx.raw_target))
        try:
            target_pages = ctx.pages or list(range(doc.page_count))
            pieces = [f"# {ctx.entry.title}", ""]
            for i in target_pages:
                if i < 0 or i >= doc.page_count:
                    continue
                page = doc[i]
                pieces.append(f"## Página {i + 1}")
                pieces.append("")
                text = page.get_text("text")
                text = re.sub(r"[ \t]+\n", "\n", text)
                text = re.sub(r"\n{3,}", "\n\n", text)
                pieces.append(text.strip())
                pieces.append("")
            body = "\n".join(pieces).strip() + "\n"
        finally:
            doc.close()

        write_text(out_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, body))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            notes=["Markdown bruto gerado com PyMuPDF."],
        )


def _run_cli_with_timeout(cmd: list, backend_name: str, ctx: "BackendContext"):
    """Run an external CLI process with stall timeout and cancel support.

    Returns (returncode, stdout_lines, stderr_lines).
    Raises InterruptedError if cancelled, TimeoutError if stalled.
    """
    import threading as _th
    import time as _time

    stdout_lines: list = []
    stderr_lines: list = []
    last_output_time = _time.monotonic()
    lock = _th.Lock()
    killed_by_cancel = _th.Event()
    killed_by_stall = _th.Event()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    logger.info("  [%s] PID=%d — aguardando saída...", backend_name, proc.pid)

    def _read_stderr():
        nonlocal last_output_time
        for line in proc.stderr:
            line = line.rstrip()
            if line:
                with lock:
                    stderr_lines.append(line)
                    last_output_time = _time.monotonic()
                logger.info("  [%s stderr] %s", backend_name, line)

    stderr_thread = _th.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    def _watchdog():
        """Mata o processo se parar de produzir output ou se cancelado."""
        while proc.poll() is None:
            _time.sleep(2)
            # Check cancel
            if ctx.cancel_check:
                try:
                    ctx.cancel_check()
                except InterruptedError:
                    logger.warning("  [%s] Cancelado pelo usuário — matando PID %d",
                                   backend_name, proc.pid)
                    killed_by_cancel.set()
                    proc.kill()
                    return
            # Check stall
            with lock:
                elapsed = _time.monotonic() - last_output_time
            if elapsed > ctx.stall_timeout:
                logger.error("  [%s] Sem output por %ds — matando PID %d (stall timeout)",
                             backend_name, ctx.stall_timeout, proc.pid)
                killed_by_stall.set()
                proc.kill()
                return

    watchdog_thread = _th.Thread(target=_watchdog, daemon=True)
    watchdog_thread.start()

    for line in proc.stdout:
        line = line.rstrip()
        if line:
            stdout_lines.append(line)
            with lock:
                last_output_time = _time.monotonic()
            logger.info("  [%s stdout] %s", backend_name, line)

    proc.wait()
    stderr_thread.join(timeout=5)
    watchdog_thread.join(timeout=2)

    if killed_by_cancel.is_set():
        raise InterruptedError(f"{backend_name} cancelado pelo usuário.")

    if killed_by_stall.is_set():
        last_line = (stderr_lines or stdout_lines or ["(nenhum)"])[-1]
        raise TimeoutError(
            f"{backend_name} travou (sem output por {ctx.stall_timeout}s). "
            f"Último output:\n{last_line}"
        )

    returncode = proc.returncode
    logger.info("  [%s] Processo finalizado com código %d", backend_name, returncode)
    return returncode, stdout_lines, stderr_lines


_MARKER_CAPABILITIES_CACHE = None


def _detect_marker_capabilities() -> Dict[str, object]:
    """
    Detecta quais flags a versão instalada do Marker suporta.

    Resultado esperado:
    {
        "page_range_flag": "--page_range" | "--page-range" | None,
        "force_ocr_flag": "--force_ocr" | "--force-ocr" | None,
        "language_flag": "--languages" | "--language" | "--lang" | "--langs" | None,
    }
    """
    global _MARKER_CAPABILITIES_CACHE

    if _MARKER_CAPABILITIES_CACHE is not None:
        return dict(_MARKER_CAPABILITIES_CACHE)

    caps = {
        "page_range_flag": "--page_range",
        "force_ocr_flag": "--force_ocr",
        "language_flag": None,
    }

    if not MARKER_CLI:
        _MARKER_CAPABILITIES_CACHE = dict(caps)
        return dict(caps)

    try:
        proc = subprocess.run(
            [MARKER_CLI, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        help_text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).lower()
    except Exception as e:
        logger.warning("  [marker] Não foi possível inspecionar --help: %s", e)
        _MARKER_CAPABILITIES_CACHE = dict(caps)
        return dict(caps)

    # Page range
    if "--page-range" in help_text:
        caps["page_range_flag"] = "--page-range"
    elif "--page_range" in help_text:
        caps["page_range_flag"] = "--page_range"
    else:
        caps["page_range_flag"] = None

    # Force OCR
    if "--force-ocr" in help_text:
        caps["force_ocr_flag"] = "--force-ocr"
    elif "--force_ocr" in help_text:
        caps["force_ocr_flag"] = "--force_ocr"
    else:
        caps["force_ocr_flag"] = None

    # OCR language flag
    for candidate in ("--languages", "--language", "--langs", "--lang"):
        if candidate in help_text:
            caps["language_flag"] = candidate
            break

    _MARKER_CAPABILITIES_CACHE = dict(caps)
    logger.info("  [marker] Capabilities detectadas: %s", caps)
    return dict(caps)

class DoclingCLIBackend(ExtractionBackend):
    name = "docling"
    layer = "advanced"

    def available(self) -> bool:
        return bool(DOCLING_CLI)

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "docling" / ctx.entry_id
        ensure_dir(out_dir)

        cmd = [
            DOCLING_CLI,
            str(ctx.raw_target),
            "--to", "md",
            "--output", str(out_dir),
            "--image-export-mode", "referenced",
            "--tables",
            "--ocr",
            "--ocr-lang", ctx.entry.ocr_language,
            "--table-mode", "accurate",
            "-vv",
        ]

        if ctx.entry.force_ocr or ctx.report.suspected_scan:
            cmd.append("--force-ocr")
        if ctx.entry.formula_priority or ctx.report.suggested_profile in {"math_heavy", "exam_pdf"}:
            cmd.append("--enrich-formula")
        if ctx.report.suggested_profile in {"layout_heavy", "exam_pdf", "math_light"}:
            cmd.append("--enrich-picture-classes")

        logger.info("  [docling] Comando: %s", " ".join(cmd))
        logger.info("  [docling] Iniciando processo...")

        try:
            returncode, stdout_lines, stderr_lines = _run_cli_with_timeout(cmd, "docling", ctx)
        except (InterruptedError, TimeoutError) as e:
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )
        except Exception as e:
            logger.error("  [docling] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )

        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)

        if returncode != 0:
            error_msg = (stderr_text or stdout_text or "Docling CLI falhou")[-4000:]
            logger.error("  [docling] Falhou: %s", error_msg[:500])
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=error_msg,
            )

        produced_md = sorted(out_dir.glob("**/*.md"))
        md_path = produced_md[0] if produced_md else None
        metadata_path = out_dir / "docling-run.json"
        write_text(metadata_path, json.dumps({
            "command": cmd,
            "stdout_tail": stdout_text[-2000:],
            "stderr_tail": stderr_text[-2000:],
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(md_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            command=cmd,
            notes=["Saída avançada gerada com Docling CLI."],
        )


class MarkerCLIBackend(ExtractionBackend):
    name = "marker"
    layer = "advanced"

    def available(self) -> bool:
        return bool(MARKER_CLI)

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "marker" / ctx.entry_id
        ensure_dir(out_dir)

        caps = _detect_marker_capabilities()

        cmd = [
            MARKER_CLI,
            str(ctx.raw_target),
            "--output_format", "markdown",
            "--output_dir", str(out_dir),
        ]

        marker_range = pages_to_marker_range(ctx.pages)
        page_range_flag = caps.get("page_range_flag")
        if marker_range and page_range_flag:
            cmd.extend([page_range_flag, marker_range])
        elif marker_range:
            logger.info("  [marker] Versão atual não suporta page_range; processando o documento inteiro.")

        wants_force_ocr = ctx.entry.force_ocr or ctx.entry.formula_priority or ctx.report.suspected_scan
        force_ocr_flag = caps.get("force_ocr_flag")
        if wants_force_ocr and force_ocr_flag:
            cmd.append(force_ocr_flag)
        elif wants_force_ocr:
            logger.info("  [marker] Versão atual não suporta force_ocr; prosseguindo sem essa flag.")

        ocr_lang = getattr(ctx.entry, "ocr_language", None)
        language_flag = caps.get("language_flag")
        if language_flag and ocr_lang and ocr_lang.strip():
            cmd.extend([language_flag, ocr_lang.strip()])
        elif ocr_lang and ocr_lang.strip():
            logger.info("  [marker] Versão atual não suporta flag de idioma OCR; ignorando ocr_language=%s", ocr_lang)

        logger.info("  [marker] Comando: %s", " ".join(cmd))
        logger.info("  [marker] Iniciando processo...")

        try:
            returncode, stdout_lines, stderr_lines = _run_cli_with_timeout(cmd, "marker", ctx)
        except (InterruptedError, TimeoutError) as e:
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )
        except Exception as e:
            logger.error("  [marker] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )

        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)

        if returncode != 0:
            error_msg = (stderr_text or stdout_text or "Marker CLI falhou")[-4000:]
            logger.error("  [marker] Falhou: %s", error_msg[:500])
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=error_msg,
            )

        produced_md = sorted(out_dir.glob("**/*.md"))
        md_path = produced_md[0] if produced_md else None
        metadata_path = out_dir / "marker-run.json"
        write_text(metadata_path, json.dumps({
            "command": cmd,
            "stdout_tail": stdout_text[-2000:],
            "stderr_tail": stderr_text[-2000:],
            "capabilities": caps,
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(md_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            command=cmd,
            notes=["Saída avançada gerada com Marker CLI."],
        )


# ---------------------------------------------------------------------------
# Selection / profiling
# ---------------------------------------------------------------------------

class BackendSelector:
    def __init__(self):
        self.backends: Dict[str, ExtractionBackend] = {
            "pymupdf4llm": PyMuPDF4LLMBackend(),
            "pymupdf": PyMuPDFBackend(),
            "docling": DoclingCLIBackend(),
            "marker": MarkerCLIBackend(),
        }

    def available_backends(self) -> Dict[str, bool]:
        return {name: backend.available() for name, backend in self.backends.items()}

    def decide(self, entry: FileEntry, report: DocumentProfileReport) -> PipelineDecision:
        mode = entry.processing_mode or "auto"
        effective_profile = entry.document_profile if entry.document_profile != "auto" else report.suggested_profile
        reasons: List[str] = []

        available = self.available_backends()

        def pick_first(names: Iterable[str]) -> Optional[str]:
            for name in names:
                if available.get(name):
                    return name
            return None

        base_backend: Optional[str] = None
        advanced_backend: Optional[str] = None

        if entry.preferred_backend != "auto" and available.get(entry.preferred_backend):
            preferred = entry.preferred_backend
            if preferred in {"docling", "marker"}:
                advanced_backend = preferred
                base_backend = pick_first(["pymupdf4llm", "pymupdf"])
                reasons.append(f"Backend preferido manualmente: {preferred}.")
            else:
                base_backend = preferred
                reasons.append(f"Backend base preferido manualmente: {preferred}.")

        if mode == "quick":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            reasons.append("Modo quick prioriza velocidade e baixo custo.")

        elif mode == "manual_assisted":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile in {"math_heavy", "math_light", "layout_heavy", "scanned", "exam_pdf"}:
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
            reasons.append("Modo manual_assisted gera base automática e exige revisão humana guiada.")

        elif mode == "high_fidelity":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile == "math_heavy":
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                reasons.append("Documento math_heavy pede backend avançado com enrich-formula.")
            elif effective_profile == "math_light":
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                reasons.append("Documento math_light pede backend avançado para fórmulas moderadas.")
            elif effective_profile in {"layout_heavy", "scanned", "exam_pdf"}:
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                reasons.append("Documento com layout/scan/exam pede backend avançado.")
            else:
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                if advanced_backend:
                    reasons.append("Modo high_fidelity tenta saída avançada além da base.")

        else:  # auto
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile in {"math_heavy", "math_light", "layout_heavy", "scanned", "exam_pdf"}:
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                reasons.append(f"Modo auto detectou perfil {effective_profile} e ativou camada avançada.")
            else:
                reasons.append("Modo auto detectou documento geral; saída base é suficiente.")

        if entry.formula_priority and not advanced_backend:
            advanced_backend = pick_first(["docling", "marker"])
            if advanced_backend:
                reasons.append("formula_priority ativou backend avançado.")

        if not base_backend and advanced_backend:
            reasons.append("Sem backend base disponível; usando apenas backend avançado.")

        return PipelineDecision(
            entry_id=entry.id(),
            processing_mode=mode,
            effective_profile=effective_profile,
            base_backend=base_backend,
            advanced_backend=advanced_backend,
            reasons=reasons,
        )


# ---------------------------------------------------------------------------
# Repo builder
# ---------------------------------------------------------------------------

class RepoBuilder:
    def __init__(self, root_dir: Path, course_meta: Dict[str, str], entries: List[FileEntry],
                 options: Dict[str, object], *,
                 student_profile: Optional[StudentProfile] = None,
                 subject_profile: Optional[SubjectProfile] = None,
                 progress_callback=None):
        self.root_dir = root_dir
        self.course_meta = course_meta
        self.entries = entries
        self.options = options
        self.student_profile = student_profile
        self.subject_profile = subject_profile
        self.progress_callback = progress_callback  # Callable[[int, int, str], None] | None
        self.logs: List[Dict[str, object]] = []
        self.selector = BackendSelector()

    def build(self) -> None:
        logger.info("Building repository at %s", self.root_dir)
        logger.info("Creating directory structure...")
        self._create_structure()
        logger.info("Writing root/pedagogical files...")
        self._write_root_files()
        logger.info("Root files written. Starting entry processing...")

        manifest = {
            "app": APP_NAME,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "course": self.course_meta,
            "options": self.options,
            "environment": {
                "python": sys.version.split()[0],
                "pymupdf": HAS_PYMUPDF,
                "pymupdf4llm": HAS_PYMUPDF4LLM,
                "pdfplumber": HAS_PDFPLUMBER,
                "docling_cli": bool(DOCLING_CLI),
                "marker_cli": bool(MARKER_CLI),
            },
            "entries": [],
        }

        manifest_path = self.root_dir / "manifest.json"
        active_entries = [e for e in self.entries if getattr(e, "enabled", True)]
        skipped = len(self.entries) - len(active_entries)
        if skipped:
            logger.info("Pulando %d entries desabilitados.", skipped)
        total = len(active_entries)
        for i, entry in enumerate(active_entries):
            logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
            if self.progress_callback:
                self.progress_callback(i, total, entry.title)
            item_result = self._process_entry(entry)
            manifest["entries"].append(item_result)
            # Salva manifest após cada entry para não perder progresso
            manifest["logs"] = self.logs
            write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
            logger.info("[%d/%d] Concluído e salvo: %s", i + 1, total, entry.title)
        if self.progress_callback:
            self.progress_callback(total, total, "")

        manifest["logs"] = self.logs
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)

        # FILE_MAP — generated after all entries are processed
        write_text(self.root_dir / "course" / "FILE_MAP.md",
                   file_map_md(self.course_meta, manifest["entries"]))

        # Resolve image references in markdowns → content/images/
        self._resolve_content_images()

        logger.info("Repository built successfully at %s", self.root_dir)

    def _create_structure(self) -> None:
        dirs = [
            "system",
            "course",
            "content/units",
            "content/concepts",
            "content/summaries",
            "content/references",
            "content/curated",
            "content/images",
            "exercises/lists",
            "exercises/solved",
            "exercises/index",
            "exams/past-exams",
            "exams/answer-keys",
            "exams/exam-index",
            "student",
            "scripts",
            "raw/pdfs/material-de-aula",
            "raw/pdfs/provas",
            "raw/pdfs/listas",
            "raw/pdfs/gabaritos",
            "raw/pdfs/cronograma",
            "raw/pdfs/referencias",
            "raw/pdfs/bibliografia",
            "raw/pdfs/fotos-de-prova",
            "raw/pdfs/outros",
            "raw/images/fotos-de-prova",
            "raw/images/provas",
            "raw/images/material-de-aula",
            "raw/images/outros",
            "code/professor", "code/student",
            "raw/code/professor", "raw/code/student",
            "raw/zip", "raw/repos",
            "assignments/enunciados", "assignments/entregas",
            "raw/pdfs/trabalhos",
            "whiteboard/raw", "whiteboard/transcriptions",
            "raw/images/quadro-branco",
            "staging/markdown-auto/pymupdf4llm",
            "staging/markdown-auto/pymupdf",
            "staging/markdown-auto/docling",
            "staging/markdown-auto/marker",
            "staging/markdown-auto/scanned",
            "staging/markdown-auto/code", "staging/zip-extract",
            "manual-review/code",
            "staging/assets/images",
            "staging/assets/inline-images",
            "staging/assets/tables",
            "staging/assets/table-detections",
            "manual-review/pdfs",
            "manual-review/images",
            "build/claude-knowledge",
        ]
        for d in dirs:
            ensure_dir(self.root_dir / d)

    def _write_root_files(self) -> None:
        course_slug = self.course_meta["course_slug"]

        # ── COURSE_IDENTITY ──────────────────────────────────────────
        write_text(
            self.root_dir / "course" / "COURSE_IDENTITY.md",
            f"""---
course_slug: {course_slug}
course_name: {self.course_meta['course_name']}
semester: {self.course_meta['semester']}
professor: {self.course_meta['professor']}
institution: {self.course_meta['institution']}
created_at: {datetime.now().isoformat(timespec='seconds')}
---

# COURSE_IDENTITY

## Disciplina
- Nome: {self.course_meta['course_name']}
- Slug: {course_slug}
- Semestre: {self.course_meta['semester']}
- Professor: {self.course_meta['professor']}
- Instituição: {self.course_meta['institution']}

## Objetivo
Este repositório organiza o conhecimento da disciplina em formato rastreável,
curado e reutilizável para um tutor acadêmico baseado no Claude.
""",
        )

        # ── System files ─────────────────────────────────────────────
        write_text(self.root_dir / "system" / "TUTOR_POLICY.md", tutor_policy_md())
        write_text(self.root_dir / "system" / "PEDAGOGY.md", pedagogy_md())
        write_text(self.root_dir / "system" / "MODES.md", modes_md())
        write_text(self.root_dir / "system" / "OUTPUT_TEMPLATES.md", output_templates_md())

        # ── Documentação interna do app — fica em build/, não no repo do tutor
        write_text(self.root_dir / "build" / "PDF_CURATION_GUIDE.md", pdf_curation_guide())
        write_text(self.root_dir / "build" / "BACKEND_ARCHITECTURE.md", backend_architecture_md())
        write_text(self.root_dir / "build" / "BACKEND_POLICY.yaml", backend_policy_yaml(self.options))

        # ── Course files ─────────────────────────────────────────────
        write_text(self.root_dir / "course" / "COURSE_MAP.md",
                   course_map_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "course" / "GLOSSARY.md",
                   glossary_md(self.course_meta, self.subject_profile))

        # ── Student files ─────────────────────────────────────────────
        write_text(self.root_dir / "student" / "STUDENT_STATE.md",
                   student_state_md(self.course_meta, self.student_profile))
        write_text(self.root_dir / "build" / "PROGRESS_SCHEMA.md", progress_schema_md())

        # ── Student profile ───────────────────────────────────────────
        if self.student_profile:
            write_text(self.root_dir / "student" / "STUDENT_PROFILE.md",
                       student_profile_md(self.student_profile))

        # ── Syllabus ──────────────────────────────────────────────────
        if self.subject_profile and self.subject_profile.syllabus:
            write_text(self.root_dir / "course" / "SYLLABUS.md",
                       syllabus_md(self.subject_profile))

        # ── Bibliography ──────────────────────────────────────────────
        bib_entries = [e for e in self.entries if e.category == "bibliografia"]
        write_text(self.root_dir / "content" / "BIBLIOGRAPHY.md",
                   bibliography_md(self.course_meta, bib_entries, self.subject_profile))

        # ── Exam & Exercise indexes ───────────────────────────────────
        exam_entries = [e for e in self.entries if e.category in EXAM_CATEGORIES]
        if exam_entries:
            write_text(self.root_dir / "exams" / "EXAM_INDEX.md",
                       exam_index_md(self.course_meta, exam_entries))

        exercise_entries = [e for e in self.entries if e.category in EXERCISE_CATEGORIES]
        if exercise_entries:
            write_text(self.root_dir / "exercises" / "EXERCISE_INDEX.md",
                       exercise_index_md(self.course_meta, exercise_entries))

        # ── Assignment, Code & Whiteboard indexes ─────────────────────
        assignment_entries = [e for e in self.entries if e.category in ASSIGNMENT_CATEGORIES]
        if assignment_entries:
            write_text(self.root_dir / "assignments" / "ASSIGNMENT_INDEX.md",
                       assignment_index_md(self.course_meta, assignment_entries))

        code_entries = [e for e in self.entries if e.category in CODE_CATEGORIES]
        if code_entries:
            write_text(self.root_dir / "code" / "CODE_INDEX.md",
                       code_index_md(self.course_meta, code_entries))

        wb_entries = [e for e in self.entries if e.category in WHITEBOARD_CATEGORIES]
        if wb_entries:
            write_text(self.root_dir / "whiteboard" / "WHITEBOARD_INDEX.md",
                       whiteboard_index_md(self.course_meta, wb_entries))

        # ── Root files ────────────────────────────────────────────────
        write_text(self.root_dir / "README.md", root_readme(self.course_meta))
        gitignore = "\n".join([
            "# === Não essencial para o Tutor ===",
            "# Cache de build (assets, markdowns intermediários)",
            "staging/",
            "# Fontes originais (tutor lê os markdowns convertidos)",
            "raw/",
            "# Artefatos de build",
            "build/",
            "# Workspace de revisão manual",
            "manual-review/",
            "# Scripts utilitários locais",
            "scripts/",
            "",
            "# === Sistema ===",
            "__pycache__/",
            "*.pyc",
            ".DS_Store",
            "Thumbs.db",
            "",
        ])
        write_text(self.root_dir / ".gitignore", gitignore)

        # ── Claude Project instructions (replaces INSTRUCOES_DO_GPT.txt)
        # Note: flags are False here because entries haven't been processed yet.
        # _regenerate_pedagogical_files() re-generates this with real flags.
        instructions = generate_claude_project_instructions(
            self.course_meta, self.student_profile, self.subject_profile,
            has_assignments=any(e.category in ASSIGNMENT_CATEGORIES for e in self.entries),
            has_code=any(e.category in CODE_CATEGORIES for e in self.entries),
            has_whiteboard=any(e.category in WHITEBOARD_CATEGORIES for e in self.entries),
            first_session_pending=self._first_session_pending(),
        )
        write_text(self.root_dir / "INSTRUCOES_CLAUDE_PROJETO.md", instructions)

        # Instruções para outras plataformas
        _common_flags = dict(
            has_assignments=any(e.category in ASSIGNMENT_CATEGORIES for e in self.entries),
            has_code=any(e.category in CODE_CATEGORIES for e in self.entries),
            has_whiteboard=any(e.category in WHITEBOARD_CATEGORIES for e in self.entries),
            first_session_pending=self._first_session_pending(),
        )
        write_text(self.root_dir / "INSTRUCOES_GPT_PROJETO.md",
                   generate_gpt_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))
        write_text(self.root_dir / "INSTRUCOES_GEMINI_PROJETO.md",
                   generate_gemini_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))

    # ------------------------------------------------------------------
    # Image resolution — copies referenced images into content/images/
    # ------------------------------------------------------------------

    _IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def _resolve_content_images(self) -> None:
        """Scan markdowns under content/ and staging/markdown-auto/ for image
        references.  Copy each referenced image into ``content/images/`` with a
        short, deterministic name and rewrite the markdown link to a relative
        path.  This keeps the repo uploadable to Claude Projects without
        thousands of staging assets.

        Incremental: keeps existing images and only copies new ones.
        Stale images (from removed entries) are cleaned up at the end.
        """
        images_dir = self.root_dir / "content" / "images"
        ensure_dir(images_dir)

        # Track existing files for stale cleanup later
        existing_files = {f for f in images_dir.iterdir() if f.is_file()} if images_dir.exists() else set()
        referenced_files: set = set()

        # Directories to scan for markdowns that the tutor will read
        scan_dirs = [
            self.root_dir / "content",
            self.root_dir / "staging" / "markdown-auto",
        ]

        target_ext = f".{self._image_format}" if self._image_format != "jpeg" else ".jpg"
        seen: Dict[str, Path] = {}  # original_path -> new_path (dedup)
        copied = 0

        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            for md_file in scan_dir.rglob("*.md"):
                # Skip markdowns inside content/images/ itself
                if images_dir in md_file.parents:
                    continue
                try:
                    text = md_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                replacements: List[tuple] = []
                for match in self._IMG_RE.finditer(text):
                    alt = match.group(1)
                    raw_path = match.group(2)

                    # Skip references already pointing to content/images/
                    if "content/images/" in raw_path.replace("\\", "/"):
                        # Track the file as referenced so it doesn't get cleaned up
                        ref_path = self._find_image(raw_path, md_file)
                        if ref_path and ref_path.exists():
                            referenced_files.add(ref_path)
                        continue

                    # Resolve the image file
                    img_path = self._find_image(raw_path, md_file)
                    if img_path is None or not img_path.exists():
                        continue

                    # Skip noise images (too small or solid color)
                    if img_path.stat().st_size < self._MIN_IMG_BYTES:
                        continue
                    if self._is_noise_image(img_path.read_bytes()):
                        continue

                    img_key = str(img_path)
                    if img_key in seen:
                        new_path = seen[img_key]
                    else:
                        # Build a short name: <parent-slug>-<filename>
                        parent_slug = slugify(img_path.parent.name) if img_path.parent.name else ""
                        short_name = f"{parent_slug}-{img_path.name}" if parent_slug else img_path.name
                        new_path = images_dir / short_name

                        # Handle collisions
                        if new_path.exists() and new_path.stat().st_size != img_path.stat().st_size:
                            stem = new_path.stem
                            suffix = new_path.suffix
                            counter = 2
                            while new_path.exists():
                                new_path = images_dir / f"{stem}-{counter}{suffix}"
                                counter += 1

                        if not new_path.exists():
                            shutil.copy2(str(img_path), str(new_path))
                            new_path = self._convert_image_format(new_path)
                            copied += 1
                        elif new_path.suffix.lower() not in (target_ext, ".jpeg" if target_ext == ".jpg" else ""):
                            # Existing file in wrong format — convert
                            new_path = self._convert_image_format(new_path)
                        seen[img_key] = new_path

                    referenced_files.add(new_path)

                    # Build relative path from this markdown to the image
                    try:
                        rel = Path(new_path).relative_to(md_file.parent)
                    except ValueError:
                        # Different directory trees — use repo-relative path
                        rel = Path(new_path).relative_to(self.root_dir)

                    rel_str = str(rel).replace("\\", "/")
                    old_ref = match.group(0)
                    new_ref = f"![{alt}]({rel_str})"
                    if old_ref != new_ref:
                        replacements.append((old_ref, new_ref))

                if replacements:
                    for old, new in replacements:
                        text = text.replace(old, new)
                    md_file.write_text(text, encoding="utf-8")

        # Clean up stale images (from removed entries)
        stale = existing_files - referenced_files
        for f in stale:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass
        if stale:
            logger.info("Cleaned up %d stale images from content/images/", len(stale))

        if copied:
            logger.info("Resolved %d new images into content/images/", copied)

    def _find_image(self, raw_path: str, md_file: Path) -> Optional[Path]:
        """Try to locate an image file from a markdown reference path."""
        # Normalize separators
        normalized = raw_path.replace("\\", "/")

        # 1) Absolute path — use directly
        p = Path(normalized)
        if p.is_absolute() and p.exists():
            return p

        # 2) Try relative to the markdown file's directory
        rel_to_md = md_file.parent / normalized
        if rel_to_md.exists():
            return rel_to_md

        # 3) Try relative to repo root
        rel_to_root = self.root_dir / normalized
        if rel_to_root.exists():
            return rel_to_root

        # 4) Extract the staging-relative portion from absolute paths
        # Pattern: .../staging/assets/... or .../staging/markdown-auto/...
        for marker in ("staging/assets/", "staging/markdown-auto/"):
            idx = normalized.find(marker)
            if idx >= 0:
                staging_rel = normalized[idx:]
                candidate = self.root_dir / staging_rel
                if candidate.exists():
                    return candidate

        return None

    def _write_source_registry(self, manifest: Dict[str, object]) -> None:
        lines = [
            f"generated_at: {manifest['generated_at']}",
            "sources:",
        ]
        for item in manifest["entries"]:
            lines.extend(
                [
                    f"  - id: {item['id']}",
                    f"    title: {json_str(item['title'])}",
                    f"    category: {item['category']}",
                    f"    file_type: {item['file_type']}",
                    f"    source_path: {json_str(item['source_path'])}",
                    f"    raw_target: {json_str(item.get('raw_target'))}",
                    f"    processing_mode: {item.get('processing_mode', 'auto')}",
                    f"    effective_profile: {item.get('effective_profile', 'general')}",
                    f"    include_in_bundle: {str(item.get('include_in_bundle', True)).lower()}",
                    f"    professor_signal: {json_str(item.get('professor_signal', ''))}",
                ]
            )
        write_text(self.root_dir / "course" / "SOURCE_REGISTRY.yaml", "\n".join(lines) + "\n")

    def _write_bundle_seed(self, manifest: Dict[str, object]) -> None:
        selected = [e for e in manifest["entries"] if e.get("include_in_bundle")]
        seed = {
            "generated_at": manifest["generated_at"],
            "course_slug": self.course_meta["course_slug"],
            "target_platform": "claude-projects",
            "bundle_candidates": [
                {
                    "id": e["id"],
                    "title": e["title"],
                    "category": e["category"],
                    "preferred_manual_review": e.get("manual_review"),
                    "base_markdown": e.get("base_markdown"),
                    "advanced_markdown": e.get("advanced_markdown"),
                    "effective_profile": e.get("effective_profile"),
                }
                for e in selected
            ],
        }
        write_text(
            self.root_dir / "build" / "claude-knowledge" / "bundle.seed.json",
            json.dumps(seed, indent=2, ensure_ascii=False)
        )

    def _write_build_report(self, manifest: Dict[str, object]) -> None:
        platform = (
            getattr(self, "_selected_platform", None)
            or getattr(self.subject_profile, "preferred_llm", "claude")
            or "claude"
        )
        platform_map = {
            "claude": ("INSTRUCOES_CLAUDE_PROJETO.md",
                       "Cole no campo 'Instructions' do Projeto Claude"),
            "gpt":    ("INSTRUCOES_GPT_PROJETO.md",
                       "Cole no campo 'Instructions' do GPT / Custom GPT"),
            "gemini": ("INSTRUCOES_GEMINI_PROJETO.md",
                       "Cole no campo de instruções do Gem no Google AI Studio"),
        }
        filename, instruction = platform_map.get(platform, platform_map["claude"])

        report = [
            "# BUILD_REPORT",
            "",
            f"- generated_at: {manifest['generated_at']}",
            f"- preferred_platform: {platform}",
            f"- pymupdf: {HAS_PYMUPDF}",
            f"- pymupdf4llm: {HAS_PYMUPDF4LLM}",
            f"- pdfplumber: {HAS_PDFPLUMBER}",
            f"- docling_cli: {bool(DOCLING_CLI)}",
            f"- marker_cli: {bool(MARKER_CLI)}",
            "",
            f"## Plataforma principal: {platform.upper()}",
            "",
            f"> Copie o conteúdo de `{filename}`",
            f"> {instruction}",
            "",
            "Os três arquivos de instruções foram gerados:",
        ]
        for k, (f, _) in platform_map.items():
            marker = " **<< atual**" if k == platform else ""
            report.append(f"- `{f}`{marker}")

        report.extend([
            "",
            "## Regras práticas de curadoria",
            "- PDFs simples: camada base costuma bastar.",
            "- PDFs com fórmulas, scans, layout complexo ou provas: camada avançada + revisão manual.",
            "- O conhecimento final do tutor deve sair de `manual-review/` e depois ser promovido.",
            "- Atualizar `student/STUDENT_STATE.md` após cada sessão de estudo.",
        ])
        write_text(self.root_dir / "BUILD_REPORT.md", "\n".join(report) + "\n")

    def _process_entry(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "id": entry.id(),
            "title": entry.title,
            "category": entry.category,
            "file_type": entry.file_type,
            "source_path": entry.source_path,
            "tags": entry.tags,
            "notes": entry.notes,
            "professor_signal": entry.professor_signal,
            "include_in_bundle": entry.include_in_bundle,
            "relevant_for_exam": entry.relevant_for_exam,
            "processing_mode": entry.processing_mode,
            "document_profile": entry.document_profile,
            "preferred_backend": entry.preferred_backend,
        }

        src = Path(entry.source_path)
        if entry.file_type not in ("url", "github-repo") and not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        if entry.file_type == "url":
            item.update(self._process_url(entry))
            return item

        if entry.file_type == "github-repo":
            item.update(self._process_github_repo(entry))
            return item

        safe_name = f"{entry.id()}{src.suffix.lower()}"

        if entry.file_type == "code":
            code_subdir = "student" if entry.category == "codigo-aluno" else "professor"
            raw_target  = self.root_dir / "raw" / "code" / code_subdir / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_code(entry, raw_target))
            return item

        if entry.file_type == "zip":
            raw_target = self.root_dir / "raw" / "zip" / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_zip(entry, raw_target))
            return item

        if entry.file_type == "pdf":
            raw_target = self.root_dir / "raw" / "pdfs" / entry.category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_pdf(entry, raw_target))
        else:
            image_category = entry.category if entry.category in IMAGE_CATEGORIES else "outros"
            raw_target = self.root_dir / "raw" / "images" / image_category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_image(entry, raw_target))

        return item

    def _process_url(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "document_report": None, "pipeline_decision": None,
            "base_markdown": None, "advanced_markdown": None,
            "advanced_backend": None, "base_backend": "url_fetcher",
            "manual_review": None,
        }
        url_dest = self.root_dir / "staging" / "markdown-auto" / "url_fetcher"
        ensure_dir(url_dest)
        md_file = url_dest / f"{entry.id()}.md"
        url = entry.source_path
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                charset = response.info().get_content_charset('utf-8')
                html = response.read().decode(charset, errors='replace')
            try:
                markdown_content = _html_to_structured_markdown(html, url, entry.title)
            except ImportError:
                markdown_content = (
                    f"# {entry.title}\n\n"
                    f"- URL: [{url}]({url})\n\n"
                    "> BeautifulSoup não instalado. Conteúdo HTML não foi convertido para Markdown estruturado.\n"
                )
            self.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "ok"})
        except Exception as e:
            logger.warning(f"Failed to fetch content from URL {url}: {e}")
            markdown_content = (
                f"# {entry.title}\n\n"
                f"- URL: [{url}]({url})\n\n"
                f"> Não foi possível carregar o conteúdo: {e}\n"
            )
            self.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "error", "error": str(e)})
        write_text(md_file, markdown_content)
        item["base_markdown"] = safe_rel(md_file, self.root_dir)
        manual = self.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
        write_text(manual, manual_pdf_review_template(entry, item))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        return item

    def _check_cancel(self):
        """Levanta InterruptedError se o build foi cancelado."""
        if self.progress_callback:
            # O progress_callback da UI verifica o cancel_event e levanta InterruptedError
            try:
                self.progress_callback(-1, -1, "")
            except InterruptedError:
                raise

    @staticmethod
    def _quick_page_count(pdf_path: Path) -> int:
        if not HAS_PYMUPDF:
            return 0
        try:
            doc = pymupdf.open(str(pdf_path))
            n = doc.page_count
            doc.close()
            return n
        except Exception:
            return 0

    def _first_session_pending(self) -> bool:
        """Retorna True se FILE_MAP.md ainda tem status: pending_review."""
        file_map_path = self.root_dir / "course" / "FILE_MAP.md"
        if not file_map_path.exists():
            return True
        try:
            content = file_map_path.read_text(encoding="utf-8")
            return "status: pending_review" in content
        except Exception:
            return True

    def _apply_math_normalization(self, md_rel_path: Optional[str]) -> None:
        """Read a generated markdown file and normalize Unicode math → LaTeX."""
        if not md_rel_path:
            return
        try:
            md_path = self.root_dir / md_rel_path
            if not md_path.exists():
                return
            original = md_path.read_text(encoding="utf-8")
            normalized = _normalize_unicode_math(original)
            if normalized != original:
                write_text(md_path, normalized)
                logger.info("  [math-norm] Normalizado símbolos Unicode → LaTeX em %s", md_rel_path)
        except Exception as e:
            logger.warning("  [math-norm] Falha ao normalizar %s: %s", md_rel_path, e)

    
    def _render_scanned_pdf_as_images(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        """
        Para PDFs escaneados:
        - renderiza cada página como imagem
        - cria um markdown base que referencia essas imagens
        - usa JPG / JPEG para reduzir peso
        """
        if not HAS_PYMUPDF:
            raise RuntimeError("PyMuPDF é obrigatório para tratar PDFs scanned como imagens.")

        from PIL import Image as PILImage

        entry_id = entry.id()
        images_dir = self.root_dir / "content" / "images" / "scanned" / entry_id
        md_dir = self.root_dir / "staging" / "markdown-auto" / "scanned"

        ensure_dir(md_dir)
        if images_dir.exists():
            shutil.rmtree(images_dir)
        ensure_dir(images_dir)

        md_path = md_dir / f"{entry_id}.md"

        doc = pymupdf.open(str(raw_target))
        refs = []
        try:
            pages = parse_page_range(entry.page_range) or list(range(doc.page_count))
            pages = [p for p in pages if 0 <= p < doc.page_count]

            for page_num in pages:
                page = doc[page_num]
                pix = page.get_pixmap(matrix=pymupdf.Matrix(1.35, 1.35), alpha=False)

                pil_img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
                img_path = images_dir / f"page-{page_num + 1:03d}.jpg"
                pil_img.save(img_path, format="JPEG", quality=82, optimize=True)

                rel = os.path.relpath(str(img_path), str(md_path.parent)).replace("\\", "/")
                refs.append(
                    f"## Página {page_num + 1}\n\n"
                    f"![Página {page_num + 1}]({rel})\n"
                )
        finally:
            doc.close()

        body = (
            f"# {entry.title}\n\n"
            "> Documento tratado como **imagem** porque o perfil efetivo foi `scanned`.\n"
            "> Cada página foi convertida em imagem para leitura visual.\n\n"
            + "\n".join(refs)
        )

        write_text(md_path, wrap_frontmatter({
            "entry_id": entry_id,
            "title": entry.title,
            "backend": "scanned-pages",
            "source_pdf": safe_rel(raw_target, self.root_dir),
            "page_range": entry.page_range,
            "effective_profile": "scanned",
        }, body))

        return {
            "base_markdown": safe_rel(md_path, self.root_dir),
            "base_backend": "scanned-pages",
            "advanced_markdown": None,
            "advanced_backend": None,
            "rendered_pages_dir": safe_rel(images_dir, self.root_dir),
        }
        



    def _process_pdf(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        import time
        item: Dict[str, object] = {
            "document_report": None,
            "pipeline_decision": None,
            "base_markdown": None,
            "advanced_markdown": None,
            "advanced_backend": None,
            "base_backend": None,
            "images_dir": None,
            "tables_dir": None,
            "table_detection_dir": None,
            "manual_review": None,
            "raw_target": safe_rel(raw_target, self.root_dir),
        }
        t0 = time.time()

        logger.info(
            "  [1/6] Profiling PDF: %s (%d págs, %.1f MB)",
            entry.title,
            self._quick_page_count(raw_target),
            raw_target.stat().st_size / 1048576,
        )
        report = self._profile_pdf(raw_target, entry)
        decision = self.selector.decide(entry, report)
        logger.info(
            "  [1/6] Profile=%s, Paginas=%d, Texto=%d chars, Imagens=%d, Scan=%s",
            decision.effective_profile,
            report.page_count,
            report.text_chars,
            report.images_count,
            report.suspected_scan,
        )

        item["document_report"] = asdict(report)
        item["pipeline_decision"] = asdict(decision)
        item["effective_profile"] = decision.effective_profile
        item["base_backend"] = decision.base_backend
        item["advanced_backend"] = decision.advanced_backend

        stall_timeout = int(self.options.get("stall_timeout", 300))
        ctx = BackendContext(
            self.root_dir,
            raw_target,
            entry,
            report,
            cancel_check=self._check_cancel,
            stall_timeout=stall_timeout,
        )

        self._check_cancel()

        # PDFs scanned: 1 página = 1 imagem
        if decision.effective_profile == "scanned":
            logger.info("  [2/6] Perfil scanned detectado → convertendo páginas em imagens.")
            try:
                scanned_result = self._render_scanned_pdf_as_images(entry, raw_target)
                item.update(scanned_result)
                self.logs.append({
                    "entry": entry.id(),
                    "step": "scanned_pages",
                    "status": "ok",
                    "rendered_pages_dir": scanned_result.get("rendered_pages_dir"),
                })
            except Exception as e:
                logger.error("  [2/6] Falha ao tratar scanned como imagens: %s", e)
                self.logs.append({
                    "entry": entry.id(),
                    "step": "scanned_pages",
                    "status": "error",
                    "error": str(e),
                })
                raise

            manual = self.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
            write_text(manual, manual_pdf_review_template(entry, item))
            item["manual_review"] = safe_rel(manual, self.root_dir)

            logger.info("  ✓ PDF scanned concluído como páginas-imagem: %s", entry.title)
            return item

        if decision.base_backend:
            logger.info("  [2/6] Backend base: %s → iniciando...", decision.base_backend)
            t1 = time.time()
            backend = self.selector.backends[decision.base_backend]
            result = backend.run(ctx)
            logger.info(
                "  [2/6] Backend base: %s → %s (%.1fs)",
                decision.base_backend,
                result.status,
                time.time() - t1,
            )
            self._log_backend_result(entry.id(), result)

            if result.status == "ok":
                item["base_markdown"] = result.markdown_path
                self._apply_math_normalization(result.markdown_path)
            else:
                logger.warning("  Base backend %s failed: %s", decision.base_backend, result.error)
                item.setdefault("backend_errors", []).append({decision.base_backend: result.error})
        else:
            logger.info("  [2/6] Backend base: nenhum selecionado")

        self._check_cancel()

        if decision.advanced_backend:
            logger.info("  [3/6] Backend avançado: %s → iniciando...", decision.advanced_backend)
            t1 = time.time()
            backend = self.selector.backends[decision.advanced_backend]
            result = backend.run(ctx)
            logger.info(
                "  [3/6] Backend avançado: %s → %s (%.1fs)",
                decision.advanced_backend,
                result.status,
                time.time() - t1,
            )
            self._log_backend_result(entry.id(), result)

            if result.status == "ok":
                item["advanced_markdown"] = result.markdown_path
                item["advanced_asset_dir"] = result.asset_dir
                item["advanced_metadata_path"] = result.metadata_path
                self._apply_math_normalization(result.markdown_path)
            else:
                logger.warning("  Advanced backend %s failed: %s", decision.advanced_backend, result.error)
                item.setdefault("backend_errors", []).append({decision.advanced_backend: result.error})
        else:
            logger.info("  [3/6] Backend avançado: nenhum selecionado")

        self._check_cancel()

        if HAS_PYMUPDF and entry.extract_images:
            logger.info("  [4/6] Extraindo imagens...")
            try:
                images_dir = self.root_dir / "staging" / "assets" / "images" / entry.id()
                count = self._extract_pdf_images(
                    raw_target,
                    images_dir,
                    pages=parse_page_range(entry.page_range),
                )
                item["images_dir"] = safe_rel(images_dir, self.root_dir)
                logger.info("  [4/6] %d imagens extraídas", count)
                self.logs.append({
                    "entry": entry.id(),
                    "step": "extract_images",
                    "status": "ok",
                    "count": count,
                })
            except Exception as e:
                logger.error("  [4/6] Falha na extração de imagens: %s", e)
                self.logs.append({
                    "entry": entry.id(),
                    "step": "extract_images",
                    "status": "error",
                    "error": str(e),
                })
        else:
            logger.info("  [4/6] Extração de imagens: pulado")

        self._check_cancel()

        if entry.extract_tables:
            logger.info("  [6/6] Extraindo tabelas...")

            if HAS_PDFPLUMBER:
                try:
                    tables_dir = self.root_dir / "staging" / "assets" / "tables" / entry.id()
                    count = self._extract_tables_pdfplumber(
                        raw_target,
                        tables_dir,
                        pages=parse_page_range(entry.page_range),
                    )
                    item["tables_dir"] = safe_rel(tables_dir, self.root_dir)
                    logger.info("  [6/6] pdfplumber: %d tabelas extraídas", count)
                    self.logs.append({
                        "entry": entry.id(),
                        "step": "extract_tables_pdfplumber",
                        "status": "ok",
                        "count": count,
                    })
                except Exception as e:
                    logger.error("  [6/6] pdfplumber falhou: %s", e)
                    self.logs.append({
                        "entry": entry.id(),
                        "step": "extract_tables_pdfplumber",
                        "status": "error",
                        "error": str(e),
                    })

            if HAS_PYMUPDF:
                try:
                    det_dir = self.root_dir / "staging" / "assets" / "table-detections" / entry.id()
                    count = self._detect_tables_pymupdf(
                        raw_target,
                        det_dir,
                        pages=parse_page_range(entry.page_range),
                    )
                    item["table_detection_dir"] = safe_rel(det_dir, self.root_dir)
                    logger.info("  [6/6] pymupdf: %d detecções de tabela", count)
                    self.logs.append({
                        "entry": entry.id(),
                        "step": "detect_tables_pymupdf",
                        "status": "ok",
                        "count": count,
                    })
                except Exception as e:
                    logger.error("  [6/6] pymupdf table detection falhou: %s", e)
                    self.logs.append({
                        "entry": entry.id(),
                        "step": "detect_tables_pymupdf",
                        "status": "error",
                        "error": str(e),
                    })
        else:
            logger.info("  [6/6] Tabelas: pulado")

        logger.info("  ✓ PDF concluído em %.1fs: %s", time.time() - t0, entry.title)

        manual = self.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
        write_text(manual, manual_pdf_review_template(entry, item))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        return item

    def _process_image(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        item: Dict[str, object] = {"manual_review": None}
        manual = self.root_dir / "manual-review" / "images" / f"{entry.id()}.md"
        write_text(manual, manual_image_review_template(entry, raw_target, self.root_dir))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        self.logs.append({"entry": entry.id(), "step": "image_import", "status": "ok"})
        return item

    def _process_code(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        item: Dict[str, object] = {"manual_review": None, "base_markdown": None}
        ext  = raw_target.suffix.lower().lstrip(".")
        lang = LANG_MAP.get(ext, ext)
        try:
            code_content = raw_target.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error("Could not read code file %s: %s", raw_target, e)
            code_content = f"[Erro ao ler arquivo: {e}]"

        curated_subdir = "student" if entry.category == "codigo-aluno" else "professor"
        curated_dir    = self.root_dir / "code" / curated_subdir
        ensure_dir(curated_dir)
        curated_path   = curated_dir / f"{entry.id()}.md"

        body  = f"# {entry.title}\n\n"
        body += f"> **Linguagem:** {lang}"
        if entry.tags:
            body += f"  |  **Unidade:** {entry.tags}"
        if entry.notes:
            body += f"\n> {entry.notes}"
        body += f"\n\n```{lang}\n{code_content}\n```\n"

        write_text(curated_path, wrap_frontmatter({
            "entry_id": entry.id(), "title": entry.title,
            "language": lang, "category": entry.category,
            "unit": entry.tags, "source": safe_rel(raw_target, self.root_dir),
        }, body))

        item["base_markdown"] = safe_rel(curated_path, self.root_dir)
        item["language"]      = lang

        manual = self.root_dir / "manual-review" / "code" / f"{entry.id()}.md"
        write_text(manual, f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_code_review
category: {entry.category}
language: {lang}
unit: {entry.tags}
---

# Revisão — {entry.title}

## Checklist
- [ ] Código compila/executa sem erros
- [ ] Anotar padrões de estilo do professor
- [ ] Identificar conceitos demonstrados

## Destino
`{safe_rel(curated_path, self.root_dir)}`
""")
        item["manual_review"] = safe_rel(manual, self.root_dir)
        self.logs.append({"entry": entry.id(), "step": "code_import",
                          "status": "ok", "language": lang})
        return item

    def _process_zip(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        import zipfile
        item: Dict[str, object] = {"extracted_files": [], "base_markdown": None,
                                    "extraction_error": None}
        extract_dir = self.root_dir / "staging" / "zip-extract" / entry.id()
        ensure_dir(extract_dir)
        try:
            with zipfile.ZipFile(raw_target, "r") as zf:
                zf.extractall(extract_dir)
        except Exception as e:
            item["extraction_error"] = str(e)
            self.logs.append({"entry": entry.id(), "step": "zip_extract",
                              "status": "error", "error": str(e)})
            return item

        processed = []
        for code_path in sorted(extract_dir.rglob("*")):
            if not code_path.is_file():
                continue
            parts = code_path.relative_to(extract_dir).parts
            if any(p.startswith(".") or p in {
                "__pycache__", "node_modules", "dist", "build", ".git"
            } for p in parts):
                continue
            if code_path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            if code_path.stat().st_size > 500_000:
                continue

            relative_name = str(code_path.relative_to(extract_dir))
            sub_entry = FileEntry(
                source_path=str(code_path), file_type="code",
                category=entry.category, title=relative_name,
                tags=entry.tags, notes=f"Extraído de: {entry.title}",
                professor_signal=entry.professor_signal,
                include_in_bundle=entry.include_in_bundle,
            )
            code_subdir  = "student" if entry.category == "codigo-aluno" else "professor"
            safe_name_c  = f"{sub_entry.id()}{code_path.suffix.lower()}"
            raw_target_c = self.root_dir / "raw" / "code" / code_subdir / safe_name_c
            ensure_dir(raw_target_c.parent)
            shutil.copy2(code_path, raw_target_c)

            sub_result = self._process_code(sub_entry, raw_target_c)
            sub_result["title"] = relative_name
            processed.append(sub_result)

        item["extracted_files"] = processed
        item["file_count"]      = len(processed)
        self.logs.append({"entry": entry.id(), "step": "zip_extract",
                          "status": "ok", "file_count": len(processed)})
        return item

    def _process_github_repo(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {"extracted_files": [], "base_markdown": None,
                                    "clone_error": None}
        url    = entry.source_path
        branch = entry.tags.strip() or "main"
        slug   = entry.id()
        clone_dir = self.root_dir / "raw" / "repos" / slug / branch
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
        ensure_dir(clone_dir.parent)

        cmd = ["git", "clone", "--depth", "1", "--branch", branch,
               "--single-branch", url, str(clone_dir)]
        try:
            proc = subprocess.run(cmd, check=False, capture_output=True,
                                  text=True, timeout=120)
        except FileNotFoundError:
            err = "git não encontrado no PATH."
            item["clone_error"] = err
            self.logs.append({"entry": slug, "step": "github_clone",
                              "status": "error", "error": err})
            return item

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "git clone falhou")[-2000:]
            item["clone_error"] = err
            self.logs.append({"entry": slug, "step": "github_clone",
                              "status": "error", "error": err})
            return item

        category  = "codigo-aluno" if branch.lower() in STUDENT_BRANCHES \
                    else "codigo-professor"
        processed = []
        for code_path in sorted(clone_dir.rglob("*")):
            if not code_path.is_file():
                continue
            parts = code_path.relative_to(clone_dir).parts
            if any(p.startswith(".") or p in {
                "__pycache__", "node_modules", "dist", "build", ".git"
            } for p in parts):
                continue
            if code_path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            if code_path.stat().st_size > 500_000:
                continue

            relative_name = str(code_path.relative_to(clone_dir))
            sub_entry = FileEntry(
                source_path=str(code_path), file_type="code",
                category=category, title=relative_name,
                tags=entry.tags, notes=f"Branch: {branch} — {url}",
                professor_signal=entry.professor_signal,
                include_in_bundle=entry.include_in_bundle,
            )
            code_subdir  = "student" if category == "codigo-aluno" else "professor"
            safe_name_c  = f"{sub_entry.id()}{code_path.suffix.lower()}"
            raw_target_c = self.root_dir / "raw" / "code" / code_subdir / safe_name_c
            ensure_dir(raw_target_c.parent)
            shutil.copy2(code_path, raw_target_c)

            sub_result = self._process_code(sub_entry, raw_target_c)
            sub_result["title"]  = relative_name
            sub_result["branch"] = branch
            processed.append(sub_result)

        item["extracted_files"] = processed
        item["file_count"]      = len(processed)
        item["category"]        = category
        self.logs.append({"entry": slug, "step": "github_clone",
                          "status": "ok", "file_count": len(processed)})
        return item

    def _profile_pdf(self, pdf_path: Path, entry: FileEntry) -> DocumentProfileReport:
        report = DocumentProfileReport()
        if not HAS_PYMUPDF:
            report.suggested_profile = entry.document_profile if entry.document_profile != "auto" else "general"
            report.notes.append("PyMuPDF não disponível; perfil automático limitado.")
            return report
        doc = pymupdf.open(str(pdf_path))
        try:
            pages = parse_page_range(entry.page_range) or list(range(doc.page_count))
            pages = [p for p in pages if 0 <= p < doc.page_count]
            report.page_count = len(pages)
            total_text = 0
            total_images = 0
            table_candidates = 0
            low_text_pages = 0
            for page_num in pages:
                page = doc[page_num]
                text = page.get_text("text") or ""
                total_text += len(text.strip())
                images = page.get_images(full=True) or []
                total_images += len(images)
                try:
                    tables = page.find_tables()
                    table_candidates += len(getattr(tables, "tables", []) or [])
                except Exception:
                    pass
                if len(text.strip()) < 60 and len(images) > 0:
                    low_text_pages += 1
            report.text_chars = total_text
            report.images_count = total_images
            report.table_candidates = table_candidates
            report.text_density = round(total_text / max(report.page_count, 1), 2)
            report.suspected_scan = (low_text_pages / max(report.page_count, 1)) >= 0.5 and total_images > 0
        finally:
            doc.close()
        if entry.document_profile != "auto":
            report.suggested_profile = entry.document_profile
            report.notes.append("Perfil definido manualmente pelo usuário.")
            return report
        name_hint = f"{entry.title} {entry.tags} {entry.notes}".lower()
        if report.suspected_scan:
            report.suggested_profile = "scanned"
            report.notes.append("Muitas páginas com pouco texto e imagens presentes: provável scan.")
        elif entry.category == "provas" or "prova" in name_hint or "questão" in name_hint or "questao" in name_hint:
            report.suggested_profile = "exam_pdf"
            report.notes.append("Detectado como material de prova/exame.")
        elif entry.formula_priority or re.search(r"\b(latex|equação|equation|fórmula|teorema|prova formal|indução)\b", name_hint):
            report.suggested_profile = "math_heavy"
            report.notes.append("Sinais de conteúdo matemático/formal.")
        elif report.table_candidates >= 2 or report.images_count >= max(3, report.page_count):
            report.suggested_profile = "layout_heavy"
            report.notes.append("Layout com tabelas/imagens relevantes.")
        else:
            report.suggested_profile = "general"
            report.notes.append("Documento geral detectado.")
        return report

    def _log_backend_result(self, entry_id: str, result: BackendRunResult) -> None:
        payload = {
            "entry": entry_id, "step": result.name, "layer": result.layer,
            "status": result.status, "markdown_path": result.markdown_path,
            "asset_dir": result.asset_dir, "metadata_path": result.metadata_path,
            "notes": result.notes,
        }
        if result.command:
            payload["command"] = result.command
        if result.error:
            payload["error"] = result.error
        self.logs.append(payload)

    # Minimum thresholds to skip noise images (tiny icons, solid-color rects, etc.)
    _MIN_IMG_BYTES = 2000     # < 2 KB is almost always an artifact
    _MIN_IMG_DIMENSION = 20   # width or height < 20px
    _MAX_ASPECT_RATIO = 8.0   # extreme aspect ratios are banners/bars (e.g. 1500x74)
    _MAX_NOISE_COLORS = 4     # images with ≤4 unique colors are decorative

    @staticmethod
    def _is_noise_image(data: bytes) -> bool:
        """Return True if image is noise: solid color, near-solid, or extreme aspect ratio."""
        try:
            from PIL import Image as PILImage
            import io
            img = PILImage.open(io.BytesIO(data))
            w, h = img.size

            # Extreme aspect ratio — banners, header/footer bars
            if w > 0 and h > 0:
                ratio = max(w / h, h / w)
                if ratio > RepoBuilder._MAX_ASPECT_RATIO:
                    return True

            # Very few unique colors — solid or near-solid (decorative elements)
            colors = img.getcolors(maxcolors=RepoBuilder._MAX_NOISE_COLORS + 1)
            if colors is not None and len(colors) <= RepoBuilder._MAX_NOISE_COLORS:
                return True

            return False
        except Exception:
            return False

    @property
    def _image_format(self) -> str:
        """Return the configured image format ('png' or 'jpeg')."""
        fmt = self.options.get("image_format", "png")
        return fmt if fmt in ("png", "jpeg") else "png"

    def _convert_image_format(self, src: Path) -> Path:
        """Convert image at *src* to the configured format. Returns new path (or src if already correct)."""
        target_ext = f".{self._image_format}" if self._image_format != "jpeg" else ".jpg"
        if src.suffix.lower() in (target_ext, ".jpeg" if target_ext == ".jpg" else ""):
            return src
        try:
            from PIL import Image as PILImage
            img = PILImage.open(src)
            if self._image_format == "jpeg" and img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            new_path = src.with_suffix(target_ext)
            save_kwargs = {"quality": 90} if self._image_format == "jpeg" else {}
            img.save(new_path, **save_kwargs)
            if new_path != src:
                src.unlink(missing_ok=True)
            return new_path
        except Exception:
            return src

    def _extract_pdf_images(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        doc = pymupdf.open(str(pdf_path))
        seen_xrefs: set = set()  # deduplicate images that appear on multiple pages
        try:
            target_pages = pages or list(range(doc.page_count))
            count = 0
            for page_num in target_pages:
                if not (0 <= page_num < doc.page_count):
                    continue
                page = doc[page_num]
                for img_idx, img in enumerate(page.get_images(full=True), start=1):
                    xref = img[0]
                    if xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)

                    image = doc.extract_image(xref)
                    if not image or "image" not in image:
                        continue

                    data = image["image"]
                    w = image.get("width", 0)
                    h = image.get("height", 0)

                    # Skip noise: too small or too few bytes
                    if len(data) < self._MIN_IMG_BYTES:
                        continue
                    if w < self._MIN_IMG_DIMENSION or h < self._MIN_IMG_DIMENSION:
                        continue
                    # Skip solid-color images (all white, all black, etc.)
                    if self._is_noise_image(data):
                        continue

                    ext = image.get("ext", "png")
                    fname = out_dir / f"page-{page_num + 1:03d}-img-{img_idx:02d}.{ext}"
                    fname.write_bytes(data)
                    # Conversão de formato acontece na consolidação final
                    count += 1
            return count
        finally:
            doc.close()

    def _extract_tables_pdfplumber(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        count = 0
        with pdfplumber.open(str(pdf_path)) as pdf:
            selected = pages or list(range(len(pdf.pages)))
            for page_num in selected:
                if not (0 <= page_num < len(pdf.pages)):
                    continue
                page = pdf.pages[page_num]
                tables = page.extract_tables() or []
                for table_idx, table in enumerate(tables, start=1):
                    normalized = [
                        [("" if cell is None else str(cell).strip()) for cell in row]
                        for row in table if row and any(cell not in (None, "", " ") for cell in row)
                    ]
                    if not normalized:
                        continue
                    csv_path = out_dir / f"page-{page_num + 1:03d}-table-{table_idx:02d}.csv"
                    ensure_dir(csv_path.parent)
                    with csv_path.open("w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerows(normalized)
                    md_path = out_dir / f"page-{page_num + 1:03d}-table-{table_idx:02d}.md"
                    write_text(md_path, rows_to_markdown_table(normalized))
                    count += 1
        return count

    def _detect_tables_pymupdf(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        doc = pymupdf.open(str(pdf_path))
        try:
            selected = pages or list(range(doc.page_count))
            count = 0
            for page_num in selected:
                if not (0 <= page_num < doc.page_count):
                    continue
                page = doc[page_num]
                try:
                    tables = page.find_tables()
                    found = getattr(tables, "tables", []) or []
                    if not found:
                        continue
                    serializable = []
                    for idx, tbl in enumerate(found, start=1):
                        bbox = getattr(tbl, "bbox", None)
                        rows = []
                        try:
                            extracted = tbl.extract() or []
                            rows = [["" if cell is None else str(cell) for cell in row] for row in extracted]
                        except Exception:
                            pass
                        serializable.append({"table_index": idx, "bbox": list(bbox) if bbox else None, "rows": rows})
                    meta_path = out_dir / f"page-{page_num + 1:03d}.json"
                    write_text(meta_path, json.dumps(serializable, indent=2, ensure_ascii=False))
                    count += len(serializable)
                except Exception:
                    continue
            return count
        finally:
            doc.close()

    def incremental_build(self) -> None:
        """Adiciona novos arquivos a um repositório existente sem recriar do zero."""
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            logger.info("No existing manifest found, falling back to full build.")
            self.build()
            return

        logger.info("Incremental build at %s", self.root_dir)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}
        new_entries = [e for e in self.entries
                       if e.source_path not in existing_sources and getattr(e, "enabled", True)]

        if not new_entries:
            logger.info("No new entries to process — regenerating pedagogical files only.")
        else:
            logger.info("Processing %d new entries (skipping %d existing).",
                         len(new_entries), len(self.entries) - len(new_entries))

            self._create_structure()

            total = len(new_entries)
            for i, entry in enumerate(new_entries):
                logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
                if self.progress_callback:
                    self.progress_callback(i, total, entry.title)
                item_result = self._process_entry(entry)
                manifest["entries"].append(item_result)
                # Salva manifest após cada entry para não perder progresso
                manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
                manifest.setdefault("logs", []).extend(self.logs)
                self.logs = []
                write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
                logger.info("[%d/%d] Concluído e salvo: %s", i + 1, total, entry.title)
            if self.progress_callback:
                self.progress_callback(total, total, "")

        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).extend(self.logs)

        # Regenera todos os arquivos pedagógicos (indexes, course map, glossary, etc.)
        # Nota: _regenerate_pedagogical_files já escreve STUDENT_PROFILE.md
        self._regenerate_pedagogical_files(manifest)

        # Atualiza ou cria student state / progress schema
        state_path = self.root_dir / "student" / "STUDENT_STATE.md"
        if state_path.exists():
            content = state_path.read_text(encoding="utf-8")
            content = re.sub(
                r"last_updated:.*",
                f"last_updated: {datetime.now().strftime('%Y-%m-%d')}",
                content
            )
            state_path.write_text(content, encoding="utf-8")
        else:
            write_text(state_path,
                       student_state_md(self.course_meta, self.student_profile))
        progress_path = self.root_dir / "build" / "PROGRESS_SCHEMA.md"
        if not progress_path.exists():
            write_text(progress_path, progress_schema_md())

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)
        logger.info("Incremental build completed. %d new entries added.", len(new_entries))

    def _regenerate_pedagogical_files(self, manifest: dict) -> None:
        """Regenera todos os arquivos pedagógicos a partir do manifest atual.

        Chamado por process_single() e pode ser reutilizado em outros contextos.
        Garante que COURSE_MAP, GLOSSARY, indexes e system prompt estejam
        sincronizados com o conjunto atual de entries.
        """
        # Limpa arquivos internos que foram movidos para build/ em versões anteriores
        _stale_files = [
            self.root_dir / "system" / "PDF_CURATION_GUIDE.md",
            self.root_dir / "system" / "BACKEND_ARCHITECTURE.md",
            self.root_dir / "system" / "BACKEND_POLICY.yaml",
            self.root_dir / "student" / "PROGRESS_SCHEMA.md",
        ]
        for stale in _stale_files:
            if stale.exists():
                try:
                    stale.unlink()
                    logger.info("Removido arquivo obsoleto: %s", stale)
                except Exception as e:
                    logger.warning("Falha ao remover %s: %s", stale, e)

        try:
            all_entries = [FileEntry.from_dict(e) for e in manifest.get("entries", [])]
        except Exception:
            all_entries = []

        # System prompt (with conditional file references)
        _common_flags = dict(
            has_assignments=any(e.category in ASSIGNMENT_CATEGORIES for e in all_entries),
            has_code=any(e.category in CODE_CATEGORIES for e in all_entries),
            has_whiteboard=any(e.category in WHITEBOARD_CATEGORIES for e in all_entries),
            first_session_pending=self._first_session_pending(),
        )
        write_text(self.root_dir / "INSTRUCOES_CLAUDE_PROJETO.md",
                   generate_claude_project_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))
        write_text(self.root_dir / "INSTRUCOES_GPT_PROJETO.md",
                   generate_gpt_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))
        write_text(self.root_dir / "INSTRUCOES_GEMINI_PROJETO.md",
                   generate_gemini_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))

        # Course map (com timeline cronograma × unidades)
        write_text(self.root_dir / "course" / "COURSE_MAP.md",
                   course_map_md(self.course_meta, self.subject_profile))

        # Glossary
        write_text(self.root_dir / "course" / "GLOSSARY.md",
                   glossary_md(self.course_meta, self.subject_profile))

        # Syllabus
        if self.subject_profile and self.subject_profile.syllabus:
            write_text(self.root_dir / "course" / "SYLLABUS.md",
                       syllabus_md(self.subject_profile))

        # Exam index
        exam_entries = [e for e in all_entries if e.category in EXAM_CATEGORIES]
        if exam_entries:
            write_text(self.root_dir / "exams" / "EXAM_INDEX.md",
                       exam_index_md(self.course_meta, exam_entries))

        # Exercise index
        exercise_entries = [e for e in all_entries if e.category in EXERCISE_CATEGORIES]
        if exercise_entries:
            write_text(self.root_dir / "exercises" / "EXERCISE_INDEX.md",
                       exercise_index_md(self.course_meta, exercise_entries))

        # Bibliography
        bib_entries = [e for e in all_entries if e.category == "bibliografia"]
        if bib_entries or getattr(self.subject_profile, "teaching_plan", ""):
            write_text(self.root_dir / "content" / "BIBLIOGRAPHY.md",
                       bibliography_md(self.course_meta, bib_entries, self.subject_profile))

        # Assignment index
        assignment_entries = [e for e in all_entries if e.category in ASSIGNMENT_CATEGORIES]
        if assignment_entries:
            write_text(self.root_dir / "assignments" / "ASSIGNMENT_INDEX.md",
                       assignment_index_md(self.course_meta, assignment_entries))

        # Code index
        code_entries = [e for e in all_entries if e.category in CODE_CATEGORIES]
        if code_entries:
            write_text(self.root_dir / "code" / "CODE_INDEX.md",
                       code_index_md(self.course_meta, code_entries))

        # Whiteboard index
        wb_entries = [e for e in all_entries if e.category in WHITEBOARD_CATEGORIES]
        if wb_entries:
            write_text(self.root_dir / "whiteboard" / "WHITEBOARD_INDEX.md",
                       whiteboard_index_md(self.course_meta, wb_entries))

        # FILE_MAP
        write_text(self.root_dir / "course" / "FILE_MAP.md",
                   file_map_md(self.course_meta, manifest.get("entries", [])))

        # Student files
        if self.student_profile:
            write_text(self.root_dir / "student" / "STUDENT_PROFILE.md",
                       student_profile_md(self.student_profile))
        state_path = self.root_dir / "student" / "STUDENT_STATE.md"
        if not state_path.exists():
            write_text(state_path, student_state_md(self.course_meta, self.student_profile))
        progress_path = self.root_dir / "build" / "PROGRESS_SCHEMA.md"
        if not progress_path.exists():
            write_text(progress_path, progress_schema_md())

        # Resolve image references in markdowns → content/images/
        self._resolve_content_images()

    def process_single(self, entry: "FileEntry", force: bool = False) -> str:
        """
        Processa um único FileEntry e adiciona ao repositório existente.
        Chamado pelo botão '⚡ Processar' da UI para processar item a item.
        Se o repositório ainda não existir, cria a estrutura primeiro.

        Returns:
            "ok" — processado com sucesso
            "already_exists" — já existia no manifest (quando force=False)
        """
        manifest_path = self.root_dir / "manifest.json"

        # Garante estrutura mínima existente
        self._create_structure()

        # Carrega ou inicializa manifest
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        else:
            # Primeiro item — cria manifest + arquivos raiz
            self._write_root_files()
            manifest = {
                "app": APP_NAME,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "course": self.course_meta,
                "options": self.options,
                "environment": {
                    "python": sys.version.split()[0],
                    "pymupdf": HAS_PYMUPDF,
                    "pymupdf4llm": HAS_PYMUPDF4LLM,
                    "pdfplumber": HAS_PDFPLUMBER,
                    "docling_cli": bool(DOCLING_CLI),
                    "marker_cli": bool(MARKER_CLI),
                },
                "entries": [],
                "logs": [],
            }

        # Verifica duplicata por source_path
        existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}
        if entry.source_path in existing_sources:
            if not force:
                logger.info("Entry already processed: %s", entry.source_path)
                return "already_exists"
            # force=True: remove a entrada antiga antes de reprocessar
            old_id = entry.id()
            logger.info("Reprocessing (force): removing old entry %s", old_id)
            self.unprocess(old_id)
            # Reload manifest after unprocess
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        logger.info("Processing single entry: %s (%s)", entry.title, entry.file_type)
        item_result = self._process_entry(entry)
        # TODO(token-optimization): adicionar etapa de limpeza pós-extração
        # para remover ruído do pymupdf4llm (cabeçalhos repetidos, rodapés,
        # numeração de página, linhas em branco excessivas).
        # Estimativa: redução de ~25% no tamanho dos arquivos de content/.
        manifest["entries"].append(item_result)
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).extend(self.logs)
        self.logs = []  # reset para próxima chamada

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)

        # Regenera arquivos pedagógicos que dependem do conjunto completo de entries
        self._regenerate_pedagogical_files(manifest)

        logger.info("Single entry processed: %s", entry.id())
        return "ok"

    def unprocess(self, entry_id: str) -> bool:
        """
        Remove todos os arquivos gerados para um entry_id e o retira do manifest.
        Chamado pelo botão '🗑 Limpar Processamento' da UI.
        Retorna True se removeu com sucesso, False caso contrário.
        """
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("No manifest found at %s", manifest_path)
            return False

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
        if not target:
            logger.warning("Entry not found in manifest: %s", entry_id)
            return False

        paths_to_remove: List[str] = []
        for key in ["raw_target", "base_markdown", "advanced_markdown", "manual_review",
                    "images_dir", "tables_dir", "table_detection_dir",
                    "advanced_asset_dir", "advanced_metadata_path"]:
            val = target.get(key)
            if val:
                paths_to_remove.append(val)

        removed_count = 0
        for rel_path in paths_to_remove:
            full = self.root_dir / rel_path
            try:
                if full.is_dir():
                    shutil.rmtree(full)
                    removed_count += 1
                elif full.is_file():
                    full.unlink()
                    removed_count += 1
            except Exception as e:
                logger.warning("Could not remove %s: %s", full, e)

        manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)

        # Re-resolve content/images/ — clears stale images from removed entry
        self._resolve_content_images()

        logger.info("Unprocessed entry %s (%d files removed)", entry_id, removed_count)
        return True

    def reject(self, entry_id: str) -> Optional[Dict[str, object]]:
        """
        Reprova um entry: remove arquivos gerados mas preserva o raw PDF.
        Retorna os dados do manifest entry (para reconstruir FileEntry na fila)
        ou None se não encontrou.
        """
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("reject: manifest não encontrado em %s", manifest_path)
            return None

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
        if not target:
            logger.warning("reject: entry %s não encontrada no manifest", entry_id)
            return None

        # Preservar dados para reconstruir FileEntry
        entry_data = dict(target)

        # Remover apenas arquivos gerados (NÃO raw_target)
        keys_to_clean = [
            "base_markdown", "advanced_markdown", "manual_review",
            "images_dir", "tables_dir", "table_detection_dir",
            "advanced_asset_dir", "advanced_metadata_path",
            "approved_markdown", "curated_markdown",
            "rendered_pages_dir",
        ]
        removed_count = 0
        for key in keys_to_clean:
            val = target.get(key)
            if not val:
                continue
            full = self.root_dir / val
            try:
                if full.is_dir():
                    shutil.rmtree(full)
                    removed_count += 1
                elif full.is_file():
                    full.unlink()
                    removed_count += 1
            except Exception as e:
                logger.warning("reject: não foi possível remover %s: %s", full, e)

        # Remover entry do manifest
        manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).append({
            "entry": entry_id,
            "step": "curator_reject",
            "status": "ok",
        })

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)

        # Re-resolve content/images/ — limpa imagens órfãs
        self._resolve_content_images()

        logger.info("Rejected entry %s (%d files removed, raw preserved)", entry_id, removed_count)
        return entry_data


def generate_claude_project_instructions(
    course_meta: dict,
    student_profile=None,
    subject_profile=None,
    has_assignments: bool = False,
    has_code: bool = False,
    has_whiteboard: bool = False,
    first_session_pending: bool = True,
) -> str:
    """
    Gera o system prompt no formato ideal para Claude Projects.
    Resultado: INSTRUCOES_CLAUDE_PROJETO.md
    Cole este conteúdo no campo 'Instructions' do Projeto no Claude.ai.
    """
    course_name = course_meta.get("course_name", "Curso")
    professor = course_meta.get("professor", "")
    institution = course_meta.get("institution", "")
    semester = course_meta.get("semester", "")

    nick = "Aluno"
    personality_block = ""
    if student_profile and student_profile.full_name:
        nick = student_profile.nickname or student_profile.full_name
        if student_profile.personality:
            personality_block = f"\n**Estilo de aprendizado do aluno:** {student_profile.personality}\n"

    schedule_block = ""
    if subject_profile and subject_profile.schedule:
        schedule_block = f"\n**Horário:** {subject_profile.schedule}"

    # Build conditional file reference table
    file_rows = [
        "| `system/TUTOR_POLICY.md` | Sempre — regras de comportamento |",
        "| `system/PEDAGOGY.md` | Ao explicar qualquer conceito |",
        "| `system/MODES.md` | Para identificar o modo da sessão |",
        "| `system/OUTPUT_TEMPLATES.md` | Para formatar respostas |",
        "| `course/COURSE_IDENTITY.md` | Dados gerais da disciplina |",
        "| `course/COURSE_MAP.md` | Ordem dos tópicos e dependências |",
        "| `course/SYLLABUS.md` | Cronograma e datas |",
        "| `course/GLOSSARY.md` | Terminologia da disciplina |",
        "| `course/FILE_MAP.md` | Mapeamento arquivo→unidade — **consulte para rastreabilidade** |",
        "| `student/STUDENT_STATE.md` | Estado atual do aluno — SEMPRE consulte |",
        "| `student/STUDENT_PROFILE.md` | Perfil e estilo do aluno |",
        "| `content/BIBLIOGRAPHY.md` | Referências bibliográficas |",
        "| `content/` | Material de aula curado |",
        "| `exercises/` | Listas de exercícios |",
        "| `exams/` | Provas anteriores e gabaritos |",
    ]
    if has_assignments:
        file_rows.append("| `assignments/` | Enunciados de trabalhos — consulte antes de guiar |")
    if has_code:
        file_rows.append("| `code/professor/` | Código do professor — exemplos e implementações |")
    if has_whiteboard:
        file_rows.append("| `whiteboard/` | Explicações do professor no quadro |")
    file_table = "\n".join(file_rows)

    first_session_block = ""
    if first_session_pending:
        first_session_block = f"""
## Protocolo de Primeira Sessão

Quando o aluno abrir o **primeiro chat** deste Projeto (ou quando `course/FILE_MAP.md` tiver `status: pending_review`), execute este protocolo antes de qualquer outra coisa:

**Mensagem de boas-vindas:**
> "Olá {nick}! Sou seu tutor de {course_name}. Antes de começarmos a estudar, preciso organizar seus materiais. Vou analisar cada arquivo e mapear para a unidade correspondente do curso. Isso vai levar um momento."

**Checklist de inicialização:**

1. **Mapear arquivos → unidades**: Leia `course/FILE_MAP.md`. Para cada arquivo com a coluna "Unidade" vazia:
   - Abra o arquivo Markdown referenciado na coluna "Markdown"
   - Leia o conteúdo e identifique o(s) tópico(s) abordado(s)
   - Cruze com as unidades em `course/COURSE_MAP.md`
   - Se necessário, use `course/SYLLABUS.md` para identificar o período
   - Preencha a coluna "Unidade" com o slug correto (ex: `unidade-01-métodos-formais`)
   - Preencha "Tags" com informações adicionais relevantes (ex: `pré-P1`, `Dafny`, `laboratório`)

2. **Preencher alta incidência em provas**: Se existirem provas em `exams/`, analise-as e preencha a seção "Tópicos de alta incidência em prova" em `course/COURSE_MAP.md`

3. **Semear glossário**: Leia `course/GLOSSARY.md`. Para cada termo aguardando preenchimento, escreva uma definição baseada no material disponível

4. **Apresentar resultado**: Mostre o FILE_MAP preenchido ao aluno em formato de tabela e peça confirmação

5. **Confirmar com o aluno**: Após apresentar o FILE_MAP preenchido, diga ao aluno:
   > "Mapeamento concluído. Você pode sincronizar com o GitHub rodando
   > `git pull` na sua máquina para puxar as edições, e `git push` se
   > quiser versionar o estado atual."

**Pré-requisito de escrita:** Para que o tutor consiga editar os arquivos do Projeto (FILE_MAP, COURSE_MAP, GLOSSARY), o repositório GitHub deve estar conectado ao Projeto Claude com permissão de escrita. Se o aluno não habilitou isso, o tutor deve ditar as alterações e pedir ao aluno que cole manualmente nos arquivos.

**Após a primeira sessão**, nas sessões seguintes, consulte `course/FILE_MAP.md` para saber qual arquivo pertence a qual unidade. Se o FILE_MAP tiver `status: pending_review`, execute o protocolo novamente.
"""

    return f"""# Instruções do Tutor — {course_name}

## Identidade

Você é o tutor acadêmico da disciplina **{course_name}**, ministrada pelo professor **{professor}** na **{institution}**, semestre **{semester}**.

Chame o aluno de **{nick}**.{personality_block}{schedule_block}

## Arquivos de referência deste Projeto

Antes de responder, consulte os arquivos relevantes abaixo. Eles são sua fonte de verdade — não invente conteúdo que não esteja neles.

| Arquivo | Quando consultar |
|---|---|
{file_table}

## Modos de operação

Identifique o modo da sessão pela frase do aluno e ajuste seu comportamento:

- **`study`** — "quero entender X", "explica Y" → ensinar do zero
- **`assignment`** — "tenho uma lista", "exercício X" → guiar sem entregar tudo
- **`exam_prep`** — "prova semana que vem", "revisão" → foco em incidência e padrões; provas são cumulativas com peso maior no conteúdo mais recente
- **`class_companion`** — "estou na aula", "o prof falou X" → resumir e contextualizar
- **`code_review`** — "revisa meu código", "o que está errado", "como melhorar" → analisar comparando com `code/professor/` quando disponível; guiar sem reescrever tudo de uma vez

Se o modo não for claro, pergunte: *"Você quer entender o conceito, resolver um exercício ou revisar para prova?"*

## Sincronização temporal

Antes de responder, identifique **onde o aluno está no semestre**:
1. Consulte a seção **"Timeline — Cronograma × Unidades"** em `course/COURSE_MAP.md`
2. Cruze a data atual com o período de cada unidade
3. Isso determina: qual unidade é a atual, quais já foram vistas, quais ainda virão

Use essa informação para:
- Contextualizar explicações ("isso é da Unidade 2, que vocês viram na semana passada")
- Priorizar revisão ("a P1 cobre Unidades 1 e 2, que vão até [data]")
- Antecipar o próximo conteúdo ("na próxima semana começa Unidade 3")

## Lógica de escopo das provas

As provas são **cumulativas com peso progressivo**. Sempre que entrar em modo `exam_prep`, identifique qual prova está próxima via `course/SYLLABUS.md` e a seção Timeline do `course/COURSE_MAP.md`, e aplique esta lógica:

| Prova | Escopo total | Foco principal | Foco secundário |
|---|---|---|---|
| P1 | Início → P1 | Todo o conteúdo (100%) | — |
| P2 | Início → P2 | Conteúdo entre P1 e P2 (~70%) | Conteúdo pré-P1 (~30%) |
| P3 | Início → P3 | Conteúdo entre P2 e P3 (~70%) | P1→P2 (~20%), pré-P1 (~10%) |

**Regra:** comece sempre pelos tópicos do período mais recente. Sinalize claramente o que é foco principal vs secundário antes de iniciar a revisão.

## Regras fundamentais

1. **Nunca invente** conteúdo não presente nos arquivos do Projeto
2. **Sempre cite a fonte** — ao usar conteúdo dos arquivos, indique o nome do PDF original e o arquivo markdown correspondente (ex: *"Conforme o material **Aula 03 - Derivadas** (`staging/markdown-auto/pymupdf4llm/aula-03-derivadas.md`, PDF original: `raw/pdfs/material-de-aula/aula-03-derivadas.pdf`)"*). Isso permite ao aluno acompanhar com o arquivo aberto no computador.
3. **Consulte `STUDENT_STATE.md`** antes de responder — não repita o que já foi explicado
4. **Não entregue** a resposta de exercícios de imediato — guie o raciocínio
5. **Ao final de cada sessão**, sugira atualizar `student/STUDENT_STATE.md`

## Rastreabilidade de fontes

Toda vez que usar informação dos arquivos do Projeto, inclua ao final do bloco uma referência no formato:

> 📄 **Fonte:** `[título do material]` — arquivo: `[caminho do markdown]` | PDF: `[caminho do PDF original]`

Isso é fundamental para que o aluno consiga abrir o material no computador e acompanhar a explicação.

## Atualização de estado e progresso

Ao final de cada sessão de estudo, gere um bloco para atualizar `student/STUDENT_STATE.md`:

```markdown
## Atualização sugerida para STUDENT_STATE.md
- Data: [YYYY-MM-DD]
- Tópico estudado: [tópico]
- Unidade: [unidade correspondente do COURSE_MAP]
- Status: [compreendido / em progresso / com dúvidas]
- Dúvidas pendentes: [lista]
- Exercícios feitos: [lista de exercícios, se houver]
- Próximo passo sugerido: [próximo tópico]
```

**Instrua o aluno a fazer commit no GitHub** com a mensagem sugerida:
```
git add student/STUDENT_STATE.md
git commit -m "study: [tópico] - [status]"
git push
```

Na próxima sessão, o estado estará atualizado automaticamente.

## Captura de conteúdo novo (fotos, anotações)

Quando o aluno enviar uma **foto** (do quadro, caderno, anotação, etc.) no chat:

1. Analise o conteúdo da imagem e resuma os pontos principais
2. Pergunte: *"Quer que eu prepare esse conteúdo para salvar no repositório da matéria?"*
3. Se sim, gere:
   - Um arquivo markdown com o conteúdo extraído da foto
   - O caminho sugerido: `content/curated/[slug-do-topico].md`
   - Instruções de commit:
```
# Salve a foto e o markdown gerado:
git add content/curated/[arquivo].md
git add raw/images/material-de-aula/[foto].jpg
git commit -m "add: [descrição do conteúdo capturado]"
git push
```

Isso transforma anotações efêmeras em conhecimento permanente no repositório.
{first_session_block}"""


def generate_gpt_instructions(
    course_meta: dict,
    student_profile=None,
    subject_profile=None,
    has_assignments: bool = False,
    has_code: bool = False,
    has_whiteboard: bool = False,
    first_session_pending: bool = True,
) -> str:
    """
    Gera o system prompt para GPT (ChatGPT Projects / Custom GPT).
    Resultado: INSTRUCOES_GPT_PROJETO.md

    Diferenças em relação ao Claude:
    - Regras críticas no INÍCIO (GPT tende a ignorar o final de prompts longos)
    - Linguagem mais imperativa e direta
    - Acesso a arquivos via GitHub RAW URLs
    - Protocolo de Primeira Sessão adaptado (sem edição nativa de arquivos)
    """
    course_name = course_meta.get("course_name", "Curso")
    professor = course_meta.get("professor", "")
    institution = course_meta.get("institution", "")
    semester = course_meta.get("semester", "")
    github_url = (getattr(subject_profile, "github_url", "") or "").rstrip("/")

    raw_base = f"{github_url.replace('github.com', 'raw.githubusercontent.com')}/main" if github_url else ""
    github_block = ""
    if github_url:
        github_block = f"""
## Repositório GitHub

URL base: {github_url}
Acesso direto aos arquivos: {raw_base}/[caminho do arquivo]

**IMPORTANTE:** Sempre que precisar do conteúdo de um arquivo, acesse
a URL raw diretamente. O aluno atualiza o repositório via git push —
então você sempre terá a versão mais recente buscando do GitHub.

Exemplos de acesso:
- `{raw_base}/course/COURSE_MAP.md`
- `{raw_base}/student/STUDENT_STATE.md`
- `{raw_base}/course/FILE_MAP.md`
"""
    else:
        github_block = """
## Documentos disponíveis

Os documentos desta disciplina foram carregados no Knowledge desta
conversa. Se o aluno fornecer uma URL do GitHub, acesse os arquivos
diretamente de lá para ter sempre a versão mais atualizada.
"""

    nick = "Aluno"
    personality_block = ""
    if student_profile and student_profile.full_name:
        nick = student_profile.nickname or student_profile.full_name
        if student_profile.personality:
            personality_block = f"\nEstilo de aprendizado do aluno: {student_profile.personality}\n"

    first_session_block = ""
    if first_session_pending:
        file_map_url = f"{raw_base}/course/FILE_MAP.md" if raw_base else "FILE_MAP.md"
        course_map_url = f"{raw_base}/course/COURSE_MAP.md" if raw_base else "COURSE_MAP.md"
        first_session_block = f"""
## Protocolo de Primeira Sessão

Na primeira sessão, ANTES de responder qualquer pergunta:

1. Acesse {file_map_url}
2. Para cada arquivo com coluna "Unidade" vazia:
   - Acesse o arquivo Markdown pelo link na coluna "Markdown"
     (substitua o caminho relativo pela URL raw do GitHub)
   - Leia o conteúdo e cruze com {course_map_url}
   - Identifique a unidade correspondente
3. Apresente ao aluno uma tabela com o mapeamento proposto
4. Dite as alterações — o aluno atualiza FILE_MAP.md manualmente
   e faz git push para sincronizar
5. Confirme com o aluno antes de iniciar o estudo

Após a primeira sessão, sempre busque FILE_MAP.md do GitHub antes
de responder para ter o estado mais atualizado.
"""

    return f"""# Instruções do Tutor — {course_name}

## REGRAS CRÍTICAS (leia antes de qualquer coisa)

1. NUNCA invente conteúdo — use apenas os arquivos do repositório
2. SEMPRE acesse STUDENT_STATE.md antes de responder
3. NUNCA entregue a resposta de exercícios sem guiar o raciocínio
4. SEMPRE cite qual arquivo você está usando como fonte
5. Se o aluno disser "atualize sua base", busque novamente os arquivos
   do GitHub — o repositório pode ter mudado desde o início da sessão

## Identidade

Você é o tutor acadêmico de **{course_name}**.
Professor: {professor} | Instituição: {institution} | Semestre: {semester}
Chame o aluno de **{nick}**.{personality_block}
{github_block}
## Arquivos principais

Acesse estes arquivos sempre que relevante:
- `course/COURSE_MAP.md` — estrutura e ordem dos tópicos
- `course/FILE_MAP.md` — mapeamento arquivo → unidade
- `course/SYLLABUS.md` — cronograma e datas
- `student/STUDENT_STATE.md` — progresso atual do aluno
- `student/STUDENT_PROFILE.md` — perfil do aluno
- `system/MODES.md` — modos de operação detalhados
- `system/PEDAGOGY.md` — como estruturar explicações
- `content/` — material de aula curado
- `exercises/` — listas de exercícios
- `exams/` — provas anteriores

## Modos de operação

Identifique o modo pela frase do aluno:

- **study** — "quero entender X" → ensinar do zero com exemplos
- **assignment** — "tenho uma lista" → guiar sem entregar a resposta
- **exam_prep** — "tenho prova" → focar em incidência e padrões
- **class_companion** — "estou na aula" → respostas curtas e diretas
- **code_review** — "revisa meu código" → diagnosticar sem reescrever tudo

## Regras de comportamento

- Use LaTeX para fórmulas matemáticas
- Use blocos de código para código
- Máximo 3 conceitos novos por resposta
- Ao final de cada sessão, gere um bloco de atualização do STUDENT_STATE.md

## Atualização de progresso

Ao final de cada sessão, dite este bloco para o aluno salvar em
`student/STUDENT_STATE.md` e fazer git push:

```
- Data: [YYYY-MM-DD]
- Tópico: [tópico estudado]
- Unidade: [slug da unidade]
- Status: [compreendido / em progresso / com dúvidas]
- Dúvidas pendentes: [lista]
- Próximo passo: [próximo tópico]
```
{first_session_block}"""


def generate_gemini_instructions(
    course_meta: dict,
    student_profile=None,
    subject_profile=None,
    has_assignments: bool = False,
    has_code: bool = False,
    has_whiteboard: bool = False,
    first_session_pending: bool = True,
) -> str:
    """
    Gera o system prompt para Gemini (Google AI Studio Gems).
    Resultado: INSTRUCOES_GEMINI_PROJETO.md

    Diferenças em relação ao Claude:
    - Gemini Gems tem integração NATIVA com GitHub (aba "Conhecimento")
    - Caminhos relativos funcionam igual ao Claude
    - Gems não editam arquivos nativamente — aluno faz as alterações
    """
    course_name = course_meta.get("course_name", "Curso")
    professor = course_meta.get("professor", "")
    institution = course_meta.get("institution", "")
    semester = course_meta.get("semester", "")
    github_url = (getattr(subject_profile, "github_url", "") or "").rstrip("/")

    nick = "Aluno"
    personality_block = ""
    if student_profile and student_profile.full_name:
        nick = student_profile.nickname or student_profile.full_name
        if student_profile.personality:
            personality_block = f"\n**Estilo de aprendizado:** {student_profile.personality}\n"

    github_note = ""
    if github_url:
        github_note = f"\n> Repositório conectado: {github_url}\n"

    file_rows = [
        "| `system/TUTOR_POLICY.md` | Regras de comportamento — SEMPRE consulte |",
        "| `student/STUDENT_STATE.md` | Progresso atual — SEMPRE consulte |",
        "| `course/COURSE_MAP.md` | Estrutura e ordem dos tópicos |",
        "| `course/FILE_MAP.md` | Mapeamento arquivo → unidade |",
        "| `course/SYLLABUS.md` | Cronograma e datas |",
        "| `course/GLOSSARY.md` | Terminologia da disciplina |",
        "| `system/PEDAGOGY.md` | Como estruturar explicações |",
        "| `system/MODES.md` | Modos de operação |",
        "| `system/OUTPUT_TEMPLATES.md` | Templates de resposta |",
        "| `content/` | Material de aula curado |",
        "| `exercises/` | Listas de exercícios |",
        "| `exams/` | Provas anteriores |",
    ]
    if has_assignments:
        file_rows.append("| `assignments/` | Enunciados de trabalhos |")
    if has_code:
        file_rows.append("| `code/` | Código do professor |")
    if has_whiteboard:
        file_rows.append("| `whiteboard/` | Registros do quadro |")

    file_table = "\n".join(file_rows)

    first_session_block = ""
    if first_session_pending:
        first_session_block = """
## Protocolo de Primeira Sessão

Quando o aluno iniciar o primeiro chat, antes de qualquer coisa:

1. Leia `course/FILE_MAP.md`
2. Para cada arquivo com coluna "Unidade" vazia:
   - Leia o Markdown correspondente (caminho na coluna "Markdown")
   - Identifique os tópicos e cruze com `course/COURSE_MAP.md`
3. Apresente ao aluno uma tabela com o mapeamento proposto
4. Peça confirmação antes de prosseguir
5. Dite as alterações — o aluno atualiza `course/FILE_MAP.md`
   e faz git push para sincronizar

Após a primeira sessão, sempre releia `course/FILE_MAP.md` antes de
responder para garantir que está com a versão mais recente.
"""

    return f"""# Instruções do Tutor — {course_name}

Você é o tutor acadêmico de **{course_name}**, ministrada pelo professor
**{professor}** na **{institution}**, semestre **{semester}**.

Chame o aluno de **{nick}**.{personality_block}

## Fonte de verdade
{github_note}
Os arquivos desta disciplina estão conectados via repositório GitHub
(aba "Conhecimento" deste Gem). Eles são sua única fonte de verdade —
**nunca invente** conteúdo que não esteja nesses arquivos.

## Arquivos de referência

| Arquivo | Quando consultar |
|---|---|
{file_table}

## Modos de operação

Identifique o modo pela frase do aluno:

- **`study`** — "quero entender X", "explica Y" → ensinar do zero
- **`assignment`** — "tenho uma lista", "exercício X" → guiar sem entregar
- **`exam_prep`** — "tenho prova", "revisão" → foco em incidência e padrões
- **`class_companion`** — "estou na aula" → respostas curtas e diretas
- **`code_review`** — "revisa meu código" → diagnosticar e guiar

Consulte `system/MODES.md` e `system/OUTPUT_TEMPLATES.md` para detalhes.

## Sincronização temporal

Antes de responder, identifique onde o aluno está no semestre:
1. Leia a seção "Timeline" em `course/COURSE_MAP.md`
2. Cruze a data atual com o período de cada unidade
3. Use isso para contextualizar explicações e priorizar revisão

## Regras fundamentais

1. **Nunca invente** — use apenas os arquivos do repositório
2. **Consulte `student/STUDENT_STATE.md`** antes de toda resposta
3. **Cite a fonte** ao usar conteúdo dos arquivos
4. **Não entregue respostas de exercícios** — guie o raciocínio
5. **Ao final da sessão**, gere bloco de atualização do `STUDENT_STATE.md`

## Atualização de progresso

Ao final de cada sessão, gere este bloco e instrua o aluno a salvar
em `student/STUDENT_STATE.md` e fazer git push:

```markdown
- Data: [YYYY-MM-DD]
- Tópico estudado: [tópico]
- Unidade: [slug da unidade do COURSE_MAP]
- Status: [compreendido / em progresso / com dúvidas]
- Dúvidas pendentes: [lista]
- Próximo passo sugerido: [próximo tópico]
```
{first_session_block}"""


# ---------------------------------------------------------------------------
# Free functions — Pedagogical file generators
# ---------------------------------------------------------------------------

def tutor_policy_md() -> str:
    return """# TUTOR_POLICY

## Propósito
Define as regras de comportamento do tutor acadêmico.
Este arquivo é lido pelo Claude antes de responder qualquer pergunta.

## Regras de comportamento

### O que o tutor SEMPRE faz
- Consulta `STUDENT_STATE.md` antes de explicar qualquer tópico
- Cita o arquivo de origem ao usar conteúdo curado
- Adapta a profundidade da explicação ao nível atual do aluno
- Conecta cada conceito novo ao que o aluno já estudou
- Sinaliza quando um tópico tem alta incidência em provas
- Ao revisar código do aluno, consulta `code/CODE_INDEX.md` para verificar se há exemplo do professor sobre o mesmo tema

### O que o tutor NUNCA faz
- Inventa conteúdo não presente nos arquivos do Projeto
- Entrega a resposta de exercícios sem guiar o raciocínio
- Avança para tópico novo sem confirmar entendimento do atual
- Repete explicação idêntica se o aluno já entendeu
- Ignora o progresso registrado em `STUDENT_STATE.md`
- Reescreve o código completo do aluno sem que ele tente corrigir primeiro
- Diz que o código do professor é "o correto" — usa como referência de estilo

### Ao receber uma pergunta ambígua
Identifique o modo antes de responder:
> "Você quer entender o conceito, resolver um exercício ou revisar para prova?"

### Ao detectar erro conceitual do aluno
1. Não corrija abruptamente
2. Faça uma pergunta que revele a inconsistência
3. Guie o aluno ao raciocínio correto
4. Confirme a compreensão antes de continuar

### Qualidade das respostas
- Use LaTeX para fórmulas: `$f(x)$` inline, `$$...$$` em bloco
- Use code blocks para código
- Prefira exemplos concretos antes de definições formais
- Máximo de 3 conceitos novos por resposta
"""


def pedagogy_md() -> str:
    return """# PEDAGOGY

## Estrutura padrão de explicação

Para cada conceito novo, siga esta sequência:

1. **Contexto** — Por que este conceito existe? Que problema resolve?
2. **Definição** — O que é, em termos precisos
3. **Intuição** — Como pensar sobre isso sem formalismo
4. **Exemplo mínimo** — O caso mais simples possível
5. **Aplicação** — Como aparece na disciplina / em computação
6. **Erros comuns** — O que os alunos costumam confundir
7. **Exercício guiado** — Uma pergunta para o aluno aplicar
8. **Resumo** — Uma frase que captura a essência

## Adaptação de profundidade

| Situação | Ajuste |
|---|---|
| Aluno nunca viu o tópico | Comece pelo contexto e intuição |
| Aluno tem dúvida pontual | Vá direto ao ponto de dúvida |
| Aluno preparando prova | Foque em erros comuns e formatos de questão |
| Aluno resolvendo exercício | Guie sem revelar resposta |

## Princípios pedagógicos

- **Concretude antes da abstração** — Exemplo antes de definição
- **Andaime** — Construa sobre o que o aluno já sabe
- **Verificação ativa** — Pergunte antes de continuar
- **Espaçamento** — Reforce tópicos anteriores ao introduzir novos
- **Erros como dados** — Erros do aluno revelam onde focar

## Quando usar provas anteriores

Ao explicar um tópico, verifique `exams/EXAM_INDEX.md`:
- Se o tópico tem alta incidência → mencione o padrão de cobrança
- Se há questão representativa → use como exercício guiado
- Se há erro recorrente registrado → alerte proativamente

## Lógica de escopo das provas

As provas seguem um modelo cumulativo com foco progressivo:

```
P1: cobre TODO o conteúdo do início até a P1
        → foco: 100% no conteúdo pré-P1

P2: cobre TODO o conteúdo do início até a P2
        → foco primário:   conteúdo entre P1 e P2  (~70%)
        → foco secundário: conteúdo pré-P1          (~30%)

P3: cobre TODO o conteúdo do início até a P3
        → foco primário:   conteúdo entre P2 e P3  (~70%)
        → foco secundário: conteúdo entre P1 e P2  (~20%)
        → foco terciário:  conteúdo pré-P1          (~10%)
```

**Regra prática para o tutor:**

Ao entrar no modo `exam_prep`, identifique qual prova está próxima consultando
`course/SYLLABUS.md`. Então:

1. Liste todos os tópicos no escopo daquela prova
2. Priorize os tópicos do período mais recente (entre a última prova e esta)
3. Reserve tempo menor para revisar tópicos de provas anteriores
4. Use provas antigas do mesmo tipo para calibrar o peso de cada assunto

**Exemplo de resposta em exam_prep:**

> "Para a P2, vou focar primeiro em [tópicos pós-P1] porque esse é o
> conteúdo novo desta prova. Depois revisamos [tópicos pré-P1] que
> costumam aparecer com menos peso mas ainda caem."
"""


def modes_md() -> str:
    return """# MODES

## Modos de operação do tutor

O tutor opera em quatro modos. Cada modo tem objetivo, postura e formato de resposta diferentes.

---

## study — Aprendizado de conceito novo

**Ativado por:** "quero entender X", "o que é Y", "explica Z"

**Objetivo:** construir compreensão sólida do zero

**Postura:**
- Siga a estrutura completa de PEDAGOGY.md
- Não assuma conhecimento prévio
- Verifique compreensão antes de avançar

**Formato de resposta:**
- Contexto → Intuição → Definição → Exemplo → Exercício

---

## assignment — Resolução de exercício

**Ativado por:** "tenho uma lista", "não entendi essa questão", "como resolver X"

**Objetivo:** desenvolver habilidade de resolução sem dependência

**Postura:**
- NUNCA entregue a resposta diretamente
- Identifique onde o aluno está travado
- Faça perguntas que revelem o próximo passo
- Consulte `exercises/EXERCISE_INDEX.md` para localizar o exercício no mapa da disciplina
- Entregue a resolução completa só depois que o aluno chegou lá

**Formato de resposta:**
- Diagnóstico → Pergunta socrática → Dica mínima → Confirmação

---

## exam_prep — Preparação para prova

**Ativado por:** "tenho prova", "revisão", "o que cai", "resumo para prova"

**Objetivo:** maximizar performance na avaliação

**Primeira ação obrigatória:** identificar qual prova está próxima via `course/SYLLABUS.md`

**Lógica de escopo (regra fundamental):**

As provas são cumulativas mas com peso progressivo:

- **P1** → cobre tudo do início até a P1. Foco total no conteúdo pré-P1.
- **P2** → cobre tudo até a P2. Foco principal no conteúdo entre P1 e P2 (~70%). Conteúdo da P1 ainda cai, mas com menos peso (~30%).
- **P3** → cobre tudo até a P3. Foco principal no conteúdo entre P2 e P3 (~70%). Conteúdo entre P1-P2 cai menos (~20%). Conteúdo pré-P1 cai pouco (~10%).

**Postura:**
- Comece sempre pelos tópicos do período mais recente
- Sinalize explicitamente quais tópicos são "foco principal" vs "foco secundário"
- Consulte `exams/EXAM_INDEX.md` para identificar tópicos com alta incidência e padrões recorrentes
- Use questões de provas anteriores para calibrar o nível de cobrança
- Sinalize armadilhas e erros recorrentes de cada tópico

**Formato de resposta:**
- Identificar a prova → Mapear escopo completo → Priorizar por período → Questão representativa → Armadilha → Checklist

---

## class_companion — Acompanhamento de aula

**Ativado por:** "estou na aula", "o professor falou X", "não entendi o que ele disse"

**Objetivo:** apoio em tempo real durante ou logo após a aula

**Postura:**
- Respostas curtas e diretas
- Contextualize o que o professor disse com o material curado
- Não entre em detalhes desnecessários — o aluno está ocupado
- Sugira registrar dúvidas para explorar depois

**Formato de resposta:**
- Resposta em até 3 parágrafos → Conexão com material → Sugestão de follow-up

---

## code_review — Revisão de código do aluno

**Ativado por:** "revisa meu código", "o que está errado aqui",
"como melhorar", "por que não funciona", "feedback no meu código"

**Objetivo:** desenvolver autonomia para identificar e corrigir
problemas no próprio código

**Primeira ação obrigatória:**
1. Consulte `code/CODE_INDEX.md` para verificar se há código do professor
   sobre o mesmo tema
2. Se houver, use como referência de comparação — não como gabarito a copiar

**Postura:**
- NUNCA reescreva o código inteiro de uma vez
- Identifique o problema mais importante primeiro
- Faça uma pergunta que leve o aluno a perceber o erro sozinho
- Mostre o trecho problemático, não a solução completa
- Quando o aluno corrigir, valide e aponte o próximo ponto

**Comparação com código do professor:**
- Use `code/professor/` como referência de estilo e abordagem
- Aponte diferenças de forma pedagógica: "o professor resolveu isso de um
  jeito diferente — consegue ver qual é a diferença de abordagem?"
- Nunca diga "o correto é o do professor" — diga "essa é uma abordagem
  possível, qual você acha mais clara?"

**Formato de resposta:**
- Diagnóstico do problema principal → Pergunta socrática → Trecho relevante
  → Aguarda tentativa → Valida → Próximo ponto
"""


def output_templates_md() -> str:
    return """# OUTPUT_TEMPLATES

## Templates de resposta por modo

### study — Conceito novo

```
## [Nome do conceito]

**Por que existe:** [contexto em 1-2 frases]

**Intuição:** [analogia ou imagem mental]

**Definição formal:**
[definição precisa, com LaTeX se necessário]

**Exemplo mínimo:**
[exemplo mais simples possível]

**Como aparece na disciplina:**
[conexão com o conteúdo do curso]

**Cuidado com:**
[erro mais comum]

**Agora você:** [pergunta para o aluno aplicar o conceito]

*Fonte: [arquivo de origem]*
```

---

### assignment — Guia de exercício

```
## Analisando a questão

[Identifica o que está sendo pedido]

**O que você já tentou?** [pergunta ao aluno]

*Se o aluno tentou algo:*
> Você está no caminho certo / Tem um ponto a revisar em [etapa X]

**Dica mínima:** [menor hint possível que desbloqueie o raciocínio]

[Aguarda o aluno tentar antes de revelar mais]
```

---

### exam_prep — Revisão para prova

```
## Revisão para [P1 / P2 / P3] — [Disciplina]

**Escopo desta prova:** [todo o conteúdo até esta prova]

### 🎯 Foco principal — conteúdo do período recente
*Estes tópicos têm maior peso nesta prova*

- [Tópico A] | Incidência: Alta | Formato: [dissertativa/cálculo/múltipla]
- [Tópico B] | Incidência: Alta
- [Tópico C] | Incidência: Média

### 📌 Foco secundário — conteúdo de provas anteriores
*Ainda cai, mas com menos peso*

- [Tópico X] — revisão rápida suficiente
- [Tópico Y] — revisar definição e um exemplo

### Questão representativa
[questão de prova anterior ou similar ao estilo do professor]

### Armadilha mais comum
[o que os alunos erram com frequência]

### Checklist de prontidão
Foco principal:
- [ ] Sei definir [Tópico A]
- [ ] Sei calcular / aplicar [Tópico A]
- [ ] Identifiquei em questão de prova anterior

Foco secundário:
- [ ] Consigo lembrar a definição de [Tópico X]
- [ ] Consigo resolver um exemplo básico de [Tópico X]
```

---

### class_companion — Suporte durante aula

```
**[Conceito mencionado]**

[Explicação em 2-3 frases diretas]

*Isso está em: [arquivo relevante]*

Para explorar melhor depois: [sugestão rápida]
```

---

### code_review — Revisão de código

`````
## Analisando seu código

**Contexto:** [qual exercício/trabalho é esse, conforme assignments/ ou
EXERCISE_INDEX.md]

**Problema principal identificado:**
[descreve o problema sem dar a solução]

**Pergunta:** [pergunta que leva o aluno a perceber o erro]

*Trecho relevante:*
``` [linguagem]
[só o trecho problemático, não o arquivo inteiro]
```

**Dica mínima:** [só se o aluno travar após a pergunta]

---

*Se houver código do professor para comparação:*

**Para referência:** o professor resolveu um problema parecido em
`code/professor/[arquivo].md` — consegue identificar a diferença de
abordagem?

📄 **Fonte:** `code/professor/[arquivo].md`
`````
"""


_TEACHING_PLAN_SECTION_STOP = re.compile(
    r'^(?:PROCEDIMENTOS|AVALIA[ÇC][AÃ]O|BIBLIOGRAFIA|METODOLOGIA)',
    re.IGNORECASE,
)

def _parse_units_from_teaching_plan(text: str):
    """
    Extrai (título_da_unidade, [tópicos]) do texto livre do plano de ensino.

    Suporta dois formatos:
      Formato PUCRS:  "N°. DA UNIDADE: N" seguido de "CONTEÚDO: Título"
                      Tópicos numerados como "1.1.", "1.2.1." etc.
      Formato genérico: "Unidade N – Título" / "UNIDADE N: Título"
                        Tópicos com marcadores (-, •, *) ou numerados (1.1)

    Para quando encontra seções pós-conteúdo (PROCEDIMENTOS, AVALIAÇÃO, BIBLIOGRAFIA).

    Cada tópico é uma tupla (texto, depth):
      - depth 0 → tópico principal (1.1., 1.2.)
      - depth 1 → sub-tópico (1.2.1., 1.2.2.)
      - depth 2+ → sub-sub-tópico (1.2.1.1.)
      - marcadores (-, •) → depth 0

    Retorna lista de (str, List[tuple[str, int]]).

    Para compatibilidade, tópicos como strings simples ainda funcionam
    nos consumidores que fazem ``for t in topics`` — eles verão tuplas.
    """
    units: list = []
    current_title: Optional[str] = None
    current_unit_num: Optional[str] = None
    current_topics: list = []

    pucrs_unit_re = re.compile(r'N[°º]?\.\s*DA\s+UNIDADE\s*:\s*(\d+)', re.IGNORECASE)
    pucrs_content_re = re.compile(r'CONTE[ÚU]DO\s*:\s*(.+)', re.IGNORECASE)
    generic_unit_re = re.compile(r'^#{0,4}\s*unidade\s+[\divxlc]+[\s\-–:—]+(.+)', re.IGNORECASE)
    numbered_topic_re = re.compile(r'^(\d+\.\d+(?:\.\d+)*)\.\s+(.+)')
    bullet_topic_re = re.compile(r'^[-•*]\s+(.+)')

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if _TEACHING_PLAN_SECTION_STOP.match(line):
            break

        # PUCRS: "N°. DA UNIDADE: N"
        m = pucrs_unit_re.match(line)
        if m:
            if current_title is not None:
                units.append((current_title, current_topics))
            current_unit_num = m.group(1)
            current_title = None
            current_topics = []
            continue

        # PUCRS: "CONTEÚDO: Título" — título da unidade atual
        if current_unit_num is not None and current_title is None:
            m = pucrs_content_re.match(line)
            if m:
                current_title = f"Unidade {current_unit_num} — {m.group(1).strip()}"
                continue

        # Genérico: "Unidade N – Título" ou "### Unidade N – Título"
        m = generic_unit_re.match(line)
        if m:
            if current_title is not None:
                units.append((current_title, current_topics))
            current_title = line.lstrip("#").strip()
            current_unit_num = None
            current_topics = []
            continue

        # Tópicos numerados (1.1., 1.2.1.) ou com marcador (-, •)
        if current_title is not None:
            m = numbered_topic_re.match(line)
            if m:
                numbering = m.group(1)  # e.g. "1.2.1"
                # depth = number of dots minus 1 (1.1 → 0, 1.2.1 → 1, 1.2.1.1 → 2)
                depth = numbering.count(".") - 1
                current_topics.append((m.group(2).strip(), max(depth, 0)))
                continue
            m = bullet_topic_re.match(line)
            if m:
                current_topics.append((m.group(1).strip(), 0))

    if current_title is not None:
        units.append((current_title, current_topics))

    return units


def _topic_text(topic) -> str:
    """Extrai o texto de um tópico, seja tupla (text, depth) ou string legada."""
    if isinstance(topic, tuple):
        return topic[0]
    return str(topic)


def _topic_depth(topic) -> int:
    """Extrai a profundidade de um tópico, seja tupla (text, depth) ou string legada."""
    if isinstance(topic, tuple):
        return topic[1]
    return 0


def _format_units_for_prompt(units) -> str:
    """Formata unidades parseadas em texto compacto e estruturado para prompts LLM.

    Retorna algo como:
        Unidade 01 — Métodos Formais [slug: unidade-01-metodos-formais]
          1. Sistemas Formais
          2. Linguagens de Especificação e Lógicas
            2.1. Fundamentos de Lógica de Primeira Ordem
    """
    from src.utils.helpers import slugify
    lines = []
    for title, topics in units:
        slug = slugify(title)
        lines.append(f"{title} [slug: {slug}]")
        for topic in topics:
            text = _topic_text(topic)
            depth = _topic_depth(topic)
            indent = "  " * (depth + 1)
            lines.append(f"{indent}- {text}")
        lines.append("")
    return "\n".join(lines)


def _parse_syllabus_timeline(syllabus: str) -> List[Dict[str, str]]:
    """
    Parseia o cronograma (Markdown table) e retorna lista de dicts.

    Cada dict tem chaves normalizadas das colunas do cronograma.
    Exemplo de retorno:
        [
            {"semana": "1", "data": "2026-03-02", "conteúdo": "Unidade 1: Métodos Formais"},
            {"semana": "2", "data": "2026-03-09", "conteúdo": "Continuação Unidade 1"},
            ...
        ]

    Suporta tabelas Markdown com qualquer nome de coluna — normaliza para minúsculas.
    """
    if not syllabus or not syllabus.strip():
        return []

    lines = [l.strip() for l in syllabus.strip().splitlines() if l.strip()]

    # Find header line (first line with |)
    header_line = None
    data_start = 0
    for i, line in enumerate(lines):
        if "|" in line and not all(c in "|-: " for c in line):
            header_line = line
            data_start = i + 1
            break

    if not header_line:
        return []

    headers = [h.strip().lower() for h in header_line.split("|") if h.strip()]
    if not headers:
        return []

    result = []
    for line in lines[data_start:]:
        # Skip separator lines (|---|---|)
        if not line.startswith("|"):
            continue
        stripped = line.replace("|", " | ")
        if all(c in "-|: " for c in line):
            continue

        cells = [c.strip() for c in line.split("|") if c.strip() or line.count("|") > 1]
        # Re-split properly
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c or len(cells) > len(headers)]
        # Remove empty leading/trailing from pipe split
        if cells and not cells[0]:
            cells = cells[1:]
        if cells and not cells[-1]:
            cells = cells[:-1]

        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))

        row = {}
        for j, h in enumerate(headers):
            row[h] = cells[j].strip() if j < len(cells) else ""
        result.append(row)

    return result


def _match_timeline_to_units(
    timeline: List[Dict[str, str]],
    units: list,
) -> List[Dict[str, str]]:
    """
    Cruza linhas do cronograma com unidades do plano de ensino.

    Para cada unidade, tenta encontrar a(s) linha(s) do cronograma que
    mencionam o título ou número da unidade. Retorna lista de dicts:
        [{"unit_title": str, "unit_slug": str, "period": str, "dates": str}, ...]

    O matching usa heurísticas:
      - Busca "unidade N", "unid N", "un N" no texto do conteúdo
      - Busca o título da unidade (ou parte dele) no conteúdo
      - Busca "P1", "P2", "P3" para marcar provas
    """
    if not timeline or not units:
        return []

    # Detect which column has the content
    content_keys = []
    for key in timeline[0].keys():
        if any(k in key for k in ["conteúdo", "conteudo", "assunto", "tema", "descrição",
                                    "descricao", "atividade", "tópico", "topico", "content"]):
            content_keys.append(key)
    if not content_keys:
        # Fallback: use the column with longest average text
        avg_lens = {}
        for key in timeline[0].keys():
            avg_lens[key] = sum(len(row.get(key, "")) for row in timeline) / max(len(timeline), 1)
        if avg_lens:
            content_keys = [max(avg_lens, key=avg_lens.get)]

    # Detect date/week column
    date_keys = []
    for key in timeline[0].keys():
        if any(k in key for k in ["data", "date", "semana", "week", "sem", "aula"]):
            date_keys.append(key)
    if not date_keys:
        # First column as fallback
        date_keys = [list(timeline[0].keys())[0]] if timeline[0] else []

    result = []
    for unit_title, _ in units:
        # Extract unit number from title: "Unidade 01 — Métodos Formais" → "01", "1"
        unit_num_match = re.search(r'(\d+)', unit_title)
        unit_num = unit_num_match.group(1) if unit_num_match else ""
        unit_num_int = str(int(unit_num)) if unit_num else ""  # "01" → "1"

        # Extract the descriptive part: "Métodos Formais"
        desc_match = re.search(r'[—–\-:]\s*(.+)', unit_title)
        unit_desc = desc_match.group(1).strip().lower() if desc_match else ""
        # Use first significant words for matching
        desc_words = [w for w in unit_desc.split() if len(w) > 3][:3]

        matched_dates = []
        for row in timeline:
            content = " ".join(row.get(k, "") for k in content_keys).lower()
            if not content.strip():
                continue

            matched = False
            # Try: "unidade 01", "unidade 1", "unid 1", "un 1"
            if unit_num:
                patterns = [
                    rf'\bunidade\s*{unit_num}\b',
                    rf'\bunidade\s*{unit_num_int}\b',
                    rf'\bunid\.?\s*{unit_num_int}\b',
                    rf'\bun\.?\s*{unit_num_int}\b',
                ]
                for pat in patterns:
                    if re.search(pat, content, re.IGNORECASE):
                        matched = True
                        break

            # Try: descriptive words match
            if not matched and desc_words:
                matches = sum(1 for w in desc_words if w in content)
                if matches >= min(2, len(desc_words)):
                    matched = True

            if matched:
                date_str = " / ".join(row.get(k, "") for k in date_keys if row.get(k, "")).strip()
                if date_str:
                    matched_dates.append(date_str)

        result.append({
            "unit_title": unit_title,
            "unit_slug": slugify(unit_title),
            "period": f"{matched_dates[0]} → {matched_dates[-1]}" if len(matched_dates) > 1 else (matched_dates[0] if matched_dates else ""),
            "dates": ", ".join(matched_dates),
        })

    return result


def _parse_bibliography_from_teaching_plan(text: str) -> dict:
    """
    Extrai referências bibliográficas do texto do plano de ensino.
    Detecta seção BIBLIOGRAFIA com sub-seções BÁSICA e COMPLEMENTAR.
    Retorna {"basica": [str, ...], "complementar": [str, ...]}.
    """
    result: dict = {"basica": [], "complementar": []}

    bib_match = re.search(r'^BIBLIOGRAFIA', text, re.MULTILINE | re.IGNORECASE)
    if not bib_match:
        return result

    bib_text = text[bib_match.start():]
    current_section: Optional[str] = None
    current_ref: Optional[str] = None
    ref_start_re = re.compile(r'^\d+\.\s+(.+)')

    def _flush():
        if current_ref and current_section:
            result[current_section].append(current_ref.strip())

    for raw in bib_text.splitlines():
        line = raw.strip()

        if re.match(r'^B[ÁA]SICA\s*:', line, re.IGNORECASE):
            _flush()
            current_ref = None
            current_section = "basica"
            continue

        if re.match(r'^COMPLEMENTAR\s*:', line, re.IGNORECASE):
            _flush()
            current_ref = None
            current_section = "complementar"
            continue

        if not current_section:
            continue

        if not line:
            _flush()
            current_ref = None
            continue

        m = ref_start_re.match(line)
        if m:
            _flush()
            current_ref = m.group(1).strip()
        elif current_ref is not None:
            current_ref += " " + line

    _flush()
    return result


def syllabus_md(subject_profile) -> str:
    """Gera o conteúdo de course/SYLLABUS.md a partir do SubjectProfile."""
    subj = subject_profile
    return f"""---
course: {subj.name}
professor: {subj.professor}
schedule: {subj.schedule}
---

# Cronograma — {subj.name}

**Horário:** {subj.schedule}

{subj.syllabus}
"""


def student_profile_md(student_profile) -> str:
    """Gera o conteúdo de student/STUDENT_PROFILE.md a partir do StudentProfile."""
    sp = student_profile
    return f"""---
nickname: {sp.nickname or sp.full_name}
---

# Perfil do Aluno

- **Nome:** {sp.full_name}
- **Apelido:** {sp.nickname or sp.full_name}

## Estilo de aprendizado preferido

{sp.personality}
"""


def course_map_md(course_meta: dict, subject_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")

    lines = [
        f"# COURSE_MAP — {course_name}",
        "",
        "> **Como usar:** Este arquivo define a ordem pedagógica dos tópicos.",
        "> O tutor consulta este mapa para saber o que o aluno já deveria ter visto",
        "> e o que ainda não foi apresentado formalmente.",
    ]

    if subject_profile and subject_profile.syllabus:
        lines.append("> Cronograma completo disponível em `course/SYLLABUS.md`")
    lines.append("")

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    units = _parse_units_from_teaching_plan(teaching_plan) if teaching_plan else []

    lines.append("## Estrutura do curso")
    lines.append("")

    if units:
        for unit_title, topics in units:
            lines.append(f"### {unit_title}")
            if topics:
                for topic in topics:
                    text = _topic_text(topic)
                    depth = _topic_depth(topic)
                    indent = "  " * depth
                    lines.append(f"{indent}- [ ] {text}")
            else:
                lines.append("- [ ] [tópicos a preencher]")
            lines.append("")
    else:
        lines += [
            "<!--",
            "INSTRUÇÃO PARA O MANTENEDOR:",
            "Preencha os tópicos abaixo em ordem pedagógica.",
            "Use indentação para indicar subtópicos.",
            "Marque dependências com '→ requer: [tópico]'",
            "-->",
            "",
            "### Unidade 1 — [Nome da unidade]",
            "- [ ] Tópico 1.1",
            "- [ ] Tópico 1.2",
            "",
            "### Unidade 2 — [Nome da unidade]",
            "- [ ] Tópico 2.1 → requer: Tópico 1.2",
            "- [ ] Tópico 2.2",
            "",
        ]

    # ── Timeline: cruzamento cronograma ↔ unidades ──────────────
    syllabus = getattr(subject_profile, "syllabus", "") if subject_profile else ""
    if units and syllabus:
        try:
            timeline = _parse_syllabus_timeline(syllabus)
            mapping = _match_timeline_to_units(timeline, units)
            has_dates = any(m["period"] for m in mapping)
            if has_dates:
                lines += [
                    "## Timeline — Cronograma × Unidades",
                    "",
                    "> Mapeamento automático entre o cronograma e as unidades do plano de ensino.",
                    "> O tutor usa esta tabela para saber em qual unidade o aluno está baseado na data atual.",
                    "",
                    "| Unidade | Período | Slug (referência) |",
                    "|---|---|---|",
                ]
                for m in mapping:
                    period = m["period"] or "[não identificado]"
                    lines.append(f"| {m['unit_title']} | {period} | `{m['unit_slug']}` |")
                lines.append("")
        except Exception as e:
            logger.debug("Could not generate timeline mapping: %s", e)

    lines += [
        "## Tópicos de alta incidência em prova",
        "",
        "> ⏳ **Aguardando análise do tutor** — na primeira sessão, o tutor cruzará as provas",
        "> em `exams/` com as unidades acima e preencherá esta tabela.",
        "",
        "| Tópico | Unidade | Incidência |",
        "|---|---|---|",
        "",
        "## Notas do professor",
        "",
        "> ⏳ **Aguardando análise do tutor** — padrões de cobrança serão identificados",
        "> a partir das provas e gabaritos disponíveis.",
        "",
    ]

    return "\n".join(lines)


def glossary_md(course_meta: dict, subject_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")

    lines = [
        f"# GLOSSARY — {course_name}",
        "",
        "> **Como usar:** Terminologia oficial da disciplina.",
        "> O tutor consulta este arquivo para usar os mesmos termos que o professor.",
        "> Inconsistência terminológica é fonte de confusão em provas.",
        "",
        "## Formato de entrada",
        "",
        "```",
        "## [Termo]",
        "**Definição:** [definição precisa usada nesta disciplina]",
        "**Sinônimos aceitos:** [outros nomes para o mesmo conceito]",
        "**Não confundir com:** [termo similar mas diferente]",
        "**Aparece em:** [unidades / tópicos onde é usado]",
        "```",
        "",
        "---",
        "",
        "## Termos",
        "",
    ]

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    units = _parse_units_from_teaching_plan(teaching_plan) if teaching_plan else []

    # Collect all topics as candidate terms, preserving unit association
    candidates = []  # List of (term_text, unit_title)
    for unit_title, topics in units:
        for topic in topics:
            candidates.append((_topic_text(topic), unit_title))

    if candidates:
        lines.append("> Termos extraídos automaticamente do plano de ensino.")
        lines.append("> ⏳ **Definições serão preenchidas pelo tutor na primeira sessão.**")
        lines.append("")
        for term, unit_title in candidates:
            lines += [
                f"## {term}",
                "**Definição:** ⏳ aguardando análise do tutor",
                "**Sinônimos aceitos:** —",
                "**Não confundir com:** —",
                f"**Aparece em:** {unit_title}",
                "",
            ]
    else:
        lines.append("> ⏳ **Termos serão adicionados pelo tutor na primeira sessão.**")
        lines.append("")

    return "\n".join(lines)


_NO_UNIT_CATEGORIES = {"cronograma", "bibliografia", "referencias"}


def file_map_md(course_meta: dict, manifest_entries: list) -> str:
    """Gera FILE_MAP.md a partir das entries do manifest.

    Cada entry é um dict vindo do manifest.json (não FileEntry).
    Campos usados: id, title, category, tags, base_markdown, raw_target.
    """
    course_name = course_meta.get("course_name", "Curso")
    lines = [
        "---",
        f"course: {course_name}",
        "status: pending_review",
        "---",
        "",
        f"# FILE_MAP — {course_name}",
        "",
        "> **Status:** ⏳ Aguardando mapeamento de unidades pelo tutor.",
        "> Na primeira sessão, o tutor lerá cada arquivo e preencherá as colunas",
        "> **Unidade** e **Tags** cruzando com `course/COURSE_MAP.md` e `course/SYLLABUS.md`.",
        "",
        "## Arquivos do repositório",
        "",
    ]

    if not manifest_entries:
        lines.append("Nenhum arquivo processado ainda.")
        return "\n".join(lines)

    lines += [
        "| # | Título | Categoria | Markdown | Raw | Unidade | Tags |",
        "|---|---|---|---|---|---|---|",
    ]

    for i, entry in enumerate(manifest_entries, 1):
        title = entry.get("title", "")
        category = entry.get("category", "")
        tags = entry.get("tags", "")
        md_path = (entry.get("approved_markdown")
                   or entry.get("curated_markdown")
                   or entry.get("base_markdown")
                   or entry.get("advanced_markdown")
                   or "")
        raw_path = entry.get("raw_target") or ""

        # Categories that cover the whole course get auto-tagged
        if category in _NO_UNIT_CATEGORIES and not tags:
            unit = "curso-inteiro"
        else:
            unit = ""

        md_cell = f"`{md_path}`" if md_path else "—"
        raw_cell = f"`{raw_path}`" if raw_path else "—"
        unit_cell = unit or ""
        tags_cell = tags or ""

        lines.append(
            f"| {i} | {title} | {category} | {md_cell} | {raw_cell} | {unit_cell} | {tags_cell} |"
        )

    lines += [
        "",
        "## Legenda",
        "",
        "- **Unidade**: slug da unidade do COURSE_MAP (ex: `unidade-01-métodos-formais`)",
        "- **Tags**: informações adicionais (ex: `pré-P1`, `Dafny`, `exercício-lab`)",
        "- **Categoria**: tipo do arquivo — **não** deve ser alterada pelo tutor",
        "",
    ]

    return "\n".join(lines)


def student_state_md(course_meta: dict, student_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    nick = "Aluno"
    if student_profile and student_profile.full_name:
        nick = student_profile.nickname or student_profile.full_name

    today = datetime.now().strftime("%Y-%m-%d")

    return f"""---
course: {course_name}
student: {nick}
last_updated: {today}
---

# STUDENT_STATE — {nick}

> **Como usar:** Este arquivo é a memória do tutor sobre o progresso do aluno.
> Atualize após cada sessão de estudo. Faça commit no GitHub.
> O tutor lê este arquivo SEMPRE antes de responder.

## Posição atual no curso

- **Último tópico estudado:** [a preencher]
- **Unidade atual:** [a preencher]
- **Status geral:** Início do semestre

## Tópicos concluídos

<!-- Marque com ✅ quando o aluno demonstrar compreensão sólida -->

| Tópico | Status | Data |
|---|---|---|
| [a preencher] | | |

## Dúvidas pendentes

<!-- Registre dúvidas que ficaram em aberto para retomar -->

- [ ] [a preencher]

## Erros recorrentes

<!-- Padrões de erro observados — ajuda o tutor a antecipar problemas -->

| Tópico | Erro observado | Frequência |
|---|---|---|
| [a preencher] | | |

## Próximos passos sugeridos

1. [a preencher após primeira sessão]

## Histórico de sessões

| Data | Modo | Tópicos | Observações |
|---|---|---|---|
| {today} | — | Início | Repositório criado |
"""


def progress_schema_md() -> str:
    return """# PROGRESS_SCHEMA

## Schema do estado do aluno

Define a estrutura esperada de `STUDENT_STATE.md`.
Use este arquivo como referência ao atualizar o estado manualmente
ou ao pedir ao Claude para gerar uma atualização.

## Campos obrigatórios

```yaml
---
course: string          # Nome da disciplina
student: string         # Nome/apelido do aluno
last_updated: YYYY-MM-DD
---
```

## Status válidos para tópicos

| Status | Significado |
|---|---|
| `não iniciado` | Ainda não foi estudado |
| `em progresso` | Estudado mas não consolidado |
| `com dúvidas` | Estudado com pontos em aberto |
| `concluído` | Compreensão sólida demonstrada |
| `revisão` | Concluído mas precisa reforçar para prova |

## Ciclo de atualização recomendado

```
Sessão de estudo
    → Claude sugere bloco de atualização
    → Aluno revisa e ajusta
    → Aluno faz commit no GitHub
    → Na próxima sessão: Claude lê o estado atualizado
```

## Template de atualização (gerado pelo Claude ao final da sessão)

```markdown
## Atualização sugerida — [DATA]

**Tópico estudado:** [nome]
**Status:** [status válido acima]
**Dúvidas identificadas:** [lista ou "nenhuma"]
**Erros observados:** [lista ou "nenhum"]
**Próximo passo:** [próximo tópico sugerido]
```
"""


def bibliography_md(course_meta: dict, entries: List[FileEntry] = None, subject_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# BIBLIOGRAPHY — {course_name}",
        "",
        "> **Como usar:** Links e referências da disciplina.",
        "> O tutor consulta este arquivo quando o aluno pede fontes",
        "> ou quando uma explicação pode ser aprofundada com leitura adicional.",
        "",
    ]

    # Referências extraídas do plano de ensino
    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    parsed = _parse_bibliography_from_teaching_plan(teaching_plan) if teaching_plan else {}
    basica = parsed.get("basica", [])
    complementar = parsed.get("complementar", [])

    if basica or complementar:
        lines.append("## Bibliografia do plano de ensino")
        lines.append("")
        if basica:
            lines.append("### Básica")
            lines.append("")
            for ref in basica:
                lines.append(f"- {ref}")
            lines.append("")
        if complementar:
            lines.append("### Complementar")
            lines.append("")
            for ref in complementar:
                lines.append(f"- {ref}")
            lines.append("")

    # Referências importadas manualmente via app (categoria "bibliografia")
    if entries:
        lines.append("## Referências importadas")
        lines.append("")
        for entry in entries:
            lines.append(f"### {entry.title}")
            lines.append(f"- **URL:** {entry.source_path}")
            if entry.tags:
                lines.append(f"- **Tags:** {entry.tags}")
            if entry.notes:
                lines.append(f"- **Nota:** {entry.notes}")
            if entry.professor_signal:
                lines.append(f"- **Indicação do professor:** {entry.professor_signal}")
            lines.append(f"- **Incluir no bundle:** {'sim' if entry.include_in_bundle else 'não'}")
            lines.append("")

    if not basica and not complementar and not entries:
        lines += [
            "## Referências",
            "",
            "<!-- Adicione referências aqui, importe links pelo app,",
            "     ou preencha o Plano de Ensino no Gerenciador de Matérias. -->",
            "",
        ]

    lines += [
        "## Mapa de relevância por tópico",
        "",
        "<!-- Preencha após organizar as referências -->",
        "",
        "| Tópico | Referência principal | Acessível | Incidência em prova |",
        "|---|---|---|---|",
        "| [a preencher] | | | |",
        "",
    ]

    return "\n".join(lines)


def exam_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# EXAM_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice de provas anteriores por tópico.",
        "> O tutor consulta este arquivo no modo `exam_prep` para identificar",
        "> quais tópicos têm maior incidência e quais padrões de questão se repetem.",
        "",
        "## Provas disponíveis",
        "",
    ]

    lines.append("| Arquivo | Tipo | Prova | Observação | Padrão do professor |")
    lines.append("|---|---|---|---|---|")
    for entry in entries:
        tipo = "foto" if entry.category == "fotos-de-prova" else "original"
        lines.append(
            f"| {Path(entry.source_path).name} | {tipo} | {entry.title} "
            f"| {entry.notes or ''} | {entry.professor_signal or ''} |"
        )

    lines += [
        "",
        "## Incidência de tópicos por prova",
        "",
        "> Preencha após revisar cada prova. O tutor usa esta tabela no modo `exam_prep`.",
        "",
        "| Tópico | P1 | P2 | P3 | Total | Peso estimado |",
        "|---|---|---|---|---|---|",
        "| [a preencher] | | | | | |",
        "",
        "## Padrões de questão observados",
        "",
        "<!-- Liste padrões recorrentes: tipos de enunciado, estrutura, pegadinhas comuns -->",
        "",
    ]

    return "\n".join(lines)


def exercise_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# EXERCISE_INDEX — {course_name}",
        "",
        "> **Como usar:** Mapa de listas de exercícios por tópico.",
        "> O tutor consulta este arquivo no modo `assignment` para contextualizar",
        "> exercícios e no modo `exam_prep` para indicar prática por tema.",
        "",
        "## Listas disponíveis",
        "",
    ]

    if entries:
        lines.append("| Arquivo | Título | Categoria | Observação |")
        lines.append("|---|---|---|---|")
        for entry in entries:
            lines.append(
                f"| {Path(entry.source_path).name} | {entry.title} "
                f"| {entry.category} | {entry.notes or ''} |"
            )
    else:
        lines.append("| Arquivo | Título | Categoria | Observação |")
        lines.append("|---|---|---|---|")
        lines.append("| [a preencher] | | | |")

    lines += [
        "",
        "## Mapeamento de exercícios por tópico",
        "",
        "> Preencha após organizar as listas. O tutor usa esta tabela para sugerir exercícios relevantes.",
        "",
        "| Tópico | Lista | Exercícios | Dificuldade | Notas |",
        "|---|---|---|---|---|",
        "| [a preencher] | | | | |",
        "",
    ]

    return "\n".join(lines)


def assignment_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [f"# ASSIGNMENT_INDEX — {course_name}", "",
             "> **Como usar:** Índice de trabalhos e projetos.",
             "> Consulte antes de guiar o aluno — não entregue a solução.", "",
             "## Trabalhos", ""]
    if entries:
        lines += ["| Arquivo | Título | Unidade | Status |", "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} "
                         f"| {e.tags or ''} | pendente |")
    else:
        lines += ["| Arquivo | Título | Unidade | Status |", "|---|---|---|---|",
                  "| [a preencher] | | | |"]
    lines += ["", "## Padrões do professor", "",
              "- [a preencher]", ""]
    return "\n".join(lines)


def code_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    prof_entries = [e for e in entries if e.category == "codigo-professor"]
    lines = [
        f"# CODE_INDEX — {course_name}", "",
        "> **Como usar:** Mapa do código do professor disponível na disciplina.",
        "> No modo `code_review`, localize exemplos e compare com o código do aluno.", "",
    ]
    if prof_entries:
        lines += [
            "## Código do professor", "",
            "| Arquivo | Linguagem | Unidade | Conceito demonstrado | Notas |",
            "|---|---|---|---|---|",
        ]
        for e in prof_entries:
            conceito = e.professor_signal or "[a preencher]"
            unit_str = ""
            if e.notes and "Unidade:" in e.notes:
                try:
                    unit_str = e.notes.split("Unidade:")[1].strip()
                except (IndexError, AttributeError):
                    pass
            lines.append(
                f"| {Path(e.source_path).name} "
                f"| {e.tags or ''} "
                f"| {unit_str} "
                f"| {conceito} "
                f"| |"
            )
        lines.append("")
    else:
        lines += ["Nenhum arquivo de código do professor importado ainda.", ""]
    lines += [
        "## Padrões de estilo do professor", "",
        "<!-- Preencha conforme analisar o código -->",
        "- [a preencher]", "",
    ]
    return "\n".join(lines)


def whiteboard_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [f"# WHITEBOARD_INDEX — {course_name}", "",
             "> Fotos de quadro branco com explicações do professor.", ""]
    if entries:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |",
                  "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} "
                         f"| {e.tags or ''} | {e.professor_signal or ''} |")
    else:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |",
                  "|---|---|---|---|", "| [a preencher] | | | |"]
    lines += ["", "## Padrões pedagógicos", "",
              "- [a preencher]", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Free functions — existing templates (unchanged)
# ---------------------------------------------------------------------------

def root_readme(course_meta: dict) -> str:
    return f"""# {course_meta.get('course_name', 'Curso')}

Repositório gerado pelo **Academic Tutor Repo Builder V3**.
Plataforma alvo: **Claude Projects** (claude.ai)

## Como usar com Claude

1. Crie um **Projeto** no Claude.ai com o nome desta disciplina
2. Cole o conteúdo de `INSTRUCOES_CLAUDE_PROJETO.md` no campo **Instructions** do Projeto
3. Conecte este repositório GitHub ao Projeto (aba Settings → GitHub)
4. Inicie uma conversa — o Claude lerá os arquivos automaticamente

## Estrutura
- `system/` — política do tutor, pedagogia, modos, templates
- `course/` — identidade, mapa, cronograma, glossário, bibliografia
- `student/` — estado atual, perfil, schema de progresso
- `content/` — material de aula curado
- `exercises/` — listas de exercícios
- `exams/` — provas anteriores e gabaritos
- `raw/` — materiais originais (PDFs, imagens)
- `staging/` — extração automática (para revisão)
- `manual-review/` — revisão humana guiada
- `build/claude-knowledge/` — bundle para upload manual se necessário

## Arquivos-chave para o tutor

| Arquivo | Função |
|---|---|
| `INSTRUCOES_CLAUDE_PROJETO.md` | System prompt do Projeto |
| `student/STUDENT_STATE.md` | Estado atual do aluno — atualizar após cada sessão |
| `course/COURSE_MAP.md` | Preencher com os tópicos em ordem |
| `course/GLOSSARY.md` | Preencher com terminologia da disciplina |
| `content/BIBLIOGRAPHY.md` | Referências bibliográficas |

## Fluxo recomendado

1. Rodar extração automática no app
2. Revisar `manual-review/`
3. Promover conteúdo curado para `content/`, `exercises/`, `exams/`
4. Preencher `COURSE_MAP.md` e `GLOSSARY.md`
5. Conectar ao Projeto no Claude.ai
6. Após cada sessão de estudo: atualizar `student/STUDENT_STATE.md` e fazer push
"""


def wrap_frontmatter(meta: dict, body: str) -> str:
    header = ["---"]
    for k, v in meta.items():
        header.append(f"{k}: {json_str(v)}")
    header.append("---")
    header.append("")
    return "\n".join(header) + body.strip() + "\n"


def rows_to_markdown_table(rows: list) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    fixed = [r + [""] * (width - len(r)) for r in rows]
    header = fixed[0]
    sep = ["---"] * width
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in fixed[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def manual_pdf_review_template(entry: FileEntry, item: Dict[str, object]) -> str:
    report = item.get("document_report") or {}
    decision = item.get("pipeline_decision") or {}
    return f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_pdf_review
category: {entry.category}
source_pdf: {json_str(item.get('raw_target'))}
processing_mode: {json_str(entry.processing_mode)}
document_profile: {json_str(entry.document_profile)}
effective_profile: {json_str(item.get('effective_profile'))}
base_backend: {json_str(item.get('base_backend'))}
advanced_backend: {json_str(item.get('advanced_backend'))}
base_markdown: {json_str(item.get('base_markdown'))}
advanced_markdown: {json_str(item.get('advanced_markdown'))}
---

# Revisão Manual — {entry.title}

## Perfil detectado
- Perfil efetivo: `{item.get('effective_profile')}`
- Páginas: `{report.get('page_count')}`
- Texto: `{report.get('text_chars')}` chars
- Imagens: `{report.get('images_count')}`
- Tabelas: `{report.get('table_candidates')}`
- Scan: `{report.get('suspected_scan')}`

## Pipeline
- Modo: `{decision.get('processing_mode')}`
- Base: `{decision.get('base_backend')}`
- Avançado: `{decision.get('advanced_backend')}`

## Checklist
- [ ] Conferir títulos e subtítulos
- [ ] Corrigir ordem de leitura
- [ ] Revisar fórmulas e converter para LaTeX
- [ ] Revisar tabelas exportadas
- [ ] Verificar imagens/figuras importantes
- [ ] Registrar pistas sobre o professor

## Markdown corrigido
<!-- Cole aqui a versão corrigida -->

## Destino curado sugerido
- [ ] `content/curated/`
- [ ] `exercises/lists/`
- [ ] `exams/past-exams/`
"""


def manual_image_review_template(entry: FileEntry, raw_target: Path, root_dir: Path) -> str:
    image_path = safe_rel(raw_target, root_dir)
    return f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_image_review
category: {entry.category}
source_image: {json_str(image_path)}
---

# Revisão Manual — Imagem

## Metadados
- Tags: `{entry.tags}`
- Relevante para prova: `{entry.relevant_for_exam}`
- Sinal do professor: `{entry.professor_signal}`

## Transcrição fiel
<!-- Escreva o texto da imagem aqui -->

## Destino curado sugerido
- [ ] `exams/past-exams/`
- [ ] `content/curated/`
"""


def pdf_curation_guide() -> str:
    return """# PDF_CURATION_GUIDE

## Regra central
PDF bruto não é conhecimento final.
Ele é insumo para:
1. extração automática
2. revisão manual
3. curadoria por função pedagógica

## Quando usar cada camada
- Base: PDFs simples, texto corrido, listas e cronogramas.
- Avançada: fórmulas, tabelas difíceis, layout complexo, scans, provas.
- Manual assisted: qualquer material que influencie a lógica de prova.

## Artefatos gerados
- `raw/`: arquivo original
- `staging/`: extração automática
- `manual-review/`: revisão humana guiada
- `content/` e `exams/`: conhecimento curado

## Destino final no Claude Project
Todo arquivo curado deve estar em formato Markdown limpo
para ser lido eficientemente pelo Claude via integração GitHub.
"""


def backend_architecture_md() -> str:
    return """# BACKEND_ARCHITECTURE

## Visão geral
A V3 usa arquitetura de backends em camadas.

```text
PDF bruto
 -> camada base
 -> camada avançada (quando necessário)
 -> extração de artefatos
 -> revisão manual guiada
 -> conteúdo curado
 -> Claude Project (via GitHub sync)
```

## Camada base
- `pymupdf4llm`: Markdown rápido para PDFs digitais.
- `pymupdf`: fallback bruto.

## Camada avançada
- `docling`: OCR, fórmulas, tabelas e imagens referenciadas.
- `marker`: equações, inline math, tabelas e imagens.

## Modos de processamento
- `quick`: só camada base.
- `high_fidelity`: base + avançada.
- `manual_assisted`: base + artefatos + revisão humana.
- `auto`: decide pelo perfil do documento.

## Regra de ouro
O tutor não deve consumir o PDF bruto como fonte final.
A fonte final deve ser o Markdown curado derivado da revisão manual,
sincronizado com o Claude Project via GitHub.
"""


def backend_policy_yaml(options: Dict[str, object]) -> str:
    return f"""version: 3
target_platform: claude-projects
policy:
  default_processing_mode: {options.get('default_processing_mode', 'auto')}
  default_ocr_language: {json_str(options.get('default_ocr_language', DEFAULT_OCR_LANGUAGE))}
  require_manual_review_for:
    - math_heavy
    - scanned
    - exam_pdf
    - layout_heavy
  base_layer_priority:
    - pymupdf4llm
    - pymupdf
  advanced_layer_priority:
    - docling
    - marker
  asset_pipeline:
    extract_images: true
    extract_tables: true
  promotion_rule: |
    Nenhum arquivo de staging é conhecimento final.
    O conhecimento final deve sair de manual-review/ e depois ser promovido
    para content/, exercises/ ou exams/, e então sincronizado com o Claude Project.
"""
