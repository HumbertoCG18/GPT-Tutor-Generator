from __future__ import annotations

from collections import Counter
import difflib
import re
import unicodedata
from typing import Dict, List, Tuple


UNICODE_MATH_TO_LATEX = {
    "∃": r"\exists",
    "∄": r"\nexists",
    "∀": r"\forall",
    "∧": r"\land",
    "∨": r"\lor",
    "¬": r"\neg",
    "⊻": r"\oplus",
    "⊢": r"\vdash",
    "⊣": r"\dashv",
    "⊨": r"\models",
    "⊤": r"\top",
    "⊥": r"\bot",
    "⇒": r"\Rightarrow",
    "⇐": r"\Leftarrow",
    "⇔": r"\Leftrightarrow",
    "↔": r"\leftrightarrow",
    "↦": r"\mapsto",
    "∈": r"\in",
    "∉": r"\notin",
    "∋": r"\ni",
    "⊂": r"\subset",
    "⊃": r"\supset",
    "⊆": r"\subseteq",
    "⊇": r"\supseteq",
    "⊄": r"\not\subset",
    "⊅": r"\not\supset",
    "∪": r"\cup",
    "∩": r"\cap",
    "∅": r"\emptyset",
    "∖": r"\setminus",
    "≤": r"\leq",
    "≥": r"\geq",
    "≠": r"\neq",
    "≈": r"\approx",
    "≡": r"\equiv",
    "≅": r"\cong",
    "∼": r"\sim",
    "≺": r"\prec",
    "≻": r"\succ",
    "≪": r"\ll",
    "≫": r"\gg",
    "≜": r"\triangleq",
    "≐": r"\doteq",
    "×": r"\times",
    "÷": r"\div",
    "±": r"\pm",
    "∓": r"\mp",
    "∘": r"\circ",
    "⊕": r"\oplus",
    "⊗": r"\otimes",
    "⊙": r"\odot",
    "†": r"\dagger",
    "‡": r"\ddagger",
    "∫": r"\int",
    "∬": r"\iint",
    "∭": r"\iiint",
    "∂": r"\partial",
    "∇": r"\nabla",
    "∑": r"\sum",
    "∏": r"\prod",
    "∐": r"\coprod",
    "∞": r"\infty",
    "√": r"\sqrt",
    "ℓ": r"\ell",
    "ℏ": r"\hbar",
    "ℜ": r"\Re",
    "ℑ": r"\Im",
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\epsilon",
    "ζ": r"\zeta",
    "η": r"\eta",
    "θ": r"\theta",
    "ι": r"\iota",
    "κ": r"\kappa",
    "λ": r"\lambda",
    "μ": r"\mu",
    "ν": r"\nu",
    "ξ": r"\xi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "υ": r"\upsilon",
    "φ": r"\phi",
    "χ": r"\chi",
    "ψ": r"\psi",
    "ω": r"\omega",
    "ϵ": r"\varepsilon",
    "ϕ": r"\varphi",
    "ϑ": r"\vartheta",
    "ϱ": r"\varrho",
    "ς": r"\varsigma",
    "Γ": r"\Gamma",
    "Δ": r"\Delta",
    "Θ": r"\Theta",
    "Λ": r"\Lambda",
    "Ξ": r"\Xi",
    "Π": r"\Pi",
    "Σ": r"\Sigma",
    "Υ": r"\Upsilon",
    "Φ": r"\Phi",
    "Ψ": r"\Psi",
    "Ω": r"\Omega",
    "⟶": r"\longrightarrow",
    "⟵": r"\longleftarrow",
    "⟹": r"\Longrightarrow",
    "⟸": r"\Longleftarrow",
    "↑": r"\uparrow",
    "↓": r"\downarrow",
    "⟨": r"\langle",
    "⟩": r"\rangle",
    "□": r"\square",
    "◇": r"\diamond",
    "△": r"\triangle",
    "▽": r"\triangledown",
    "★": r"\star",
    "⋆": r"\star",
    "⋅": r"\cdot",
    "…": r"\ldots",
    "⋯": r"\cdots",
    "⋮": r"\vdots",
    "ℕ": r"\mathbb{N}",
    "ℤ": r"\mathbb{Z}",
    "ℚ": r"\mathbb{Q}",
    "ℝ": r"\mathbb{R}",
    "ℂ": r"\mathbb{C}",
}
UNICODE_MATH_PATTERN = re.compile(
    "|".join(re.escape(ch) for ch in sorted(UNICODE_MATH_TO_LATEX.keys(), key=len, reverse=True))
)
MOJIBAKE_MARKERS = ("Ã", "Â", "â", "�")
MATH_INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
MATH_DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
MATH_PAREN_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
MATH_BRACKET_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
TEX_SIMPLE_ACCENT_RE = re.compile(r"""\\(?P<accent>['`^"~])(?:\{(?P<braced>[A-Za-z])\}|(?P<plain>[A-Za-z]))""")
TEX_CEDILLA_RE = re.compile(r"""\\c(?:\{(?P<braced>[A-Za-z])\}|(?P<plain>[A-Za-z]))""")
TEX_ACCENT_TO_UNICODE = {
    ("'", "A"): "Á", ("'", "E"): "É", ("'", "I"): "Í", ("'", "O"): "Ó", ("'", "U"): "Ú",
    ("'", "a"): "á", ("'", "e"): "é", ("'", "i"): "í", ("'", "o"): "ó", ("'", "u"): "ú",
    ("`", "A"): "À", ("`", "E"): "È", ("`", "I"): "Ì", ("`", "O"): "Ò", ("`", "U"): "Ù",
    ("`", "a"): "à", ("`", "e"): "è", ("`", "i"): "ì", ("`", "o"): "ò", ("`", "u"): "ù",
    ("^", "A"): "Â", ("^", "E"): "Ê", ("^", "I"): "Î", ("^", "O"): "Ô", ("^", "U"): "Û",
    ("^", "a"): "â", ("^", "e"): "ê", ("^", "i"): "î", ("^", "o"): "ô", ("^", "u"): "û",
    ('"', "A"): "Ä", ('"', "E"): "Ë", ('"', "I"): "Ï", ('"', "O"): "Ö", ('"', "U"): "Ü",
    ('"', "a"): "ä", ('"', "e"): "ë", ('"', "i"): "ï", ('"', "o"): "ö", ('"', "u"): "ü",
    ("~", "A"): "Ã", ("~", "N"): "Ñ", ("~", "O"): "Õ", ("~", "a"): "ã", ("~", "n"): "ñ", ("~", "o"): "õ",
}
TEX_CEDILLA_TO_UNICODE = {"C": "Ç", "c": "ç"}
PORTUGUESE_ACCENT_CHARS = set("áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ")


def normalize_tex_accents_in_math(text: str) -> str:
    if not text or "\\" not in text:
        return text

    def _replace_simple(match: re.Match) -> str:
        accent = match.group("accent")
        letter = match.group("braced") or match.group("plain") or ""
        return TEX_ACCENT_TO_UNICODE.get((accent, letter), match.group(0))

    def _replace_cedilla(match: re.Match) -> str:
        letter = match.group("braced") or match.group("plain") or ""
        return TEX_CEDILLA_TO_UNICODE.get(letter, match.group(0))

    text = TEX_SIMPLE_ACCENT_RE.sub(_replace_simple, text)
    text = TEX_CEDILLA_RE.sub(_replace_cedilla, text)
    return text


def normalize_unicode_math(text: str) -> str:
    if not text:
        return text

    def _replace_in_math(match: re.Match) -> str:
        content = normalize_tex_accents_in_math(match.group(0))
        return UNICODE_MATH_PATTERN.sub(
            lambda sym: UNICODE_MATH_TO_LATEX.get(sym.group(0), sym.group(0)),
            content,
        )

    for pattern in (MATH_DISPLAY_RE, MATH_INLINE_RE, MATH_PAREN_RE, MATH_BRACKET_RE):
        text = pattern.sub(_replace_in_math, text)

    def _wrap_outside_math(text_str: str) -> str:
        math_regions = re.compile(
            r"(\$\$.+?\$\$|(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)|\\\(.+?\\\)|\\\[.+?\\\])",
            re.DOTALL,
        )
        parts = math_regions.split(text_str)
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                result.append(part)
            else:
                part = UNICODE_MATH_PATTERN.sub(
                    lambda sym: f"${UNICODE_MATH_TO_LATEX[sym.group(0)]}$",
                    part,
                )
                result.append(part)
        return "".join(result)

    return _wrap_outside_math(text)


def mojibake_score(text: str) -> int:
    if not text:
        return 0
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)


def repair_mojibake_text(text: str) -> str:
    if not text:
        return text

    original_score = mojibake_score(text)
    if original_score == 0:
        return text

    candidates = [text]
    for source_encoding in ("latin-1", "cp1252"):
        try:
            candidates.append(text.encode(source_encoding).decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

    best = min(candidates, key=mojibake_score)
    return best if mojibake_score(best) < original_score else text


def sanitize_external_markdown_text(text: str) -> str:
    repaired = repair_mojibake_text(text)
    return repaired.replace("\r\n", "\n").replace("\r", "\n")


def detect_latex_corruption(content: str) -> dict:
    clean = str(content).replace("\r\n", "\n").replace("\r", "\n")
    clean = re.sub(r"^---\n.*?\n---\n?", "", clean, flags=re.DOTALL)
    clean = re.sub(r"```.*?```", "", clean, flags=re.DOTALL)
    clean = re.sub(r"`[^`\n]+`", "", clean)

    signals: List[str] = []
    score = 0

    def _add_signal(message: str, weight: int) -> None:
        nonlocal score
        signals.append(message)
        score += weight

    single_dollars = re.findall(r"(?<![\\$])\$(?!\$)", clean)
    if len(single_dollars) % 2 != 0:
        _add_signal("delimitadores $ desbalanceados", 30)

    begin_counter = Counter(re.findall(r"\\begin\{([^}]+)\}", clean))
    end_counter = Counter(re.findall(r"\\end\{([^}]+)\}", clean))
    unmatched_envs = []
    for env_name, count in begin_counter.items():
        if count > end_counter.get(env_name, 0):
            unmatched_envs.append(env_name)
    if unmatched_envs:
        sample = ", ".join(sorted(set(unmatched_envs))[:3])
        _add_signal(f"\\begin sem \\end: {sample}", min(len(unmatched_envs) * 15, 30))

    unicode_math_chars = re.findall(r"[∀∃∈∉∅∧∨¬→↔⇒⇔≤≥≠⊆⊂⊇⊃∪∩ℕℤℚℝℂ⊢⊨⊥⊤]", clean)
    latex_markers = re.findall(r"\$|\\[a-zA-Z]+", clean)
    if len(unicode_math_chars) >= 4 and len(latex_markers) < max(2, len(unicode_math_chars) // 2):
        _add_signal(
            f"{len(unicode_math_chars)} simbolos unicode sem estrutura LaTeX",
            min(len(unicode_math_chars) * 2, 20),
        )

    brace_issue_lines = 0
    brace_hint_lines = 0
    raw_command_lines = 0
    orphan_escapes = 0
    mathish_line_re = re.compile(r"\\[a-zA-Z]+|[$∀∃∈∉∧∨¬→↔⇒⇔≤≥≠⊆⊂⊇⊃∪∩ℕℤℚℝℂ⊢⊨⊥⊤]|^\s*\{")

    for line in clean.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.count("{") != stripped.count("}") and mathish_line_re.search(stripped):
            brace_issue_lines += 1
        if stripped.startswith("{") and stripped.count("{") > stripped.count("}"):
            brace_hint_lines += 1

        command_count = len(re.findall(r"\\[a-zA-Z]+", stripped))
        has_math_delimiter = bool(re.search(r"\$|\\\(|\\\[|\\begin\{", stripped))
        if command_count >= 2 and not has_math_delimiter:
            raw_command_lines += 1

        if re.search(r"(?<!\\)\\\s*$", stripped):
            orphan_escapes += 1

    if brace_issue_lines:
        _add_signal(
            f"{brace_issue_lines} linha(s) com chaves desbalanceadas em contexto matematico",
            min(brace_issue_lines * 10, 25),
        )
    if brace_hint_lines:
        _add_signal(
            f"{brace_hint_lines} possivel(is) tripla(s) de Hoare incompleta(s)",
            min(brace_hint_lines * 8, 16),
        )
    if raw_command_lines:
        _add_signal(
            f"{raw_command_lines} linha(s) com comandos LaTeX fora de delimitadores",
            min(raw_command_lines * 10, 20),
        )
    if orphan_escapes:
        _add_signal(
            f"{orphan_escapes} escape(s) orfao(s) no fim de linha",
            min(orphan_escapes * 6, 12),
        )

    return {"corrupted": score >= 25, "score": min(score, 100), "signals": signals}


def split_markdown_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    end += len("\n---\n")
    return text[:end], text[end:]


def is_plain_text_recovery_candidate(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 24:
        return False
    if not re.search(r"[A-Za-zÀ-ÿ]", stripped):
        return False
    if stripped.startswith(("```", "#", ">", "-", "*", "|", "<!--")):
        return False
    if stripped.startswith(tuple(f"{n}." for n in range(1, 10))):
        return False
    if any(token in stripped for token in ("![", "](", "<math", "</math>", "$$", "\\(", "\\)", "\\[", "\\]")):
        return False
    if stripped.count("|") >= 2:
        return False
    if sum(stripped.count(ch) for ch in "=^_{}\\") >= 3:
        return False
    return True


def normalize_recovery_line(line: str) -> str:
    normalized = unicodedata.normalize("NFKD", line)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[`*_>#\[\](){}|~]+", " ", normalized)
    normalized = re.sub(r"[^a-zA-Z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def accent_quality_score(line: str) -> int:
    accent_count = sum(1 for ch in line if ch in PORTUGUESE_ACCENT_CHARS)
    return accent_count * 2 - mojibake_score(line)


def hybridize_marker_markdown_with_base(base_markdown: str, marker_markdown: str) -> tuple[str, Dict[str, int]]:
    _, base_body = split_markdown_frontmatter(sanitize_external_markdown_text(base_markdown))
    marker_prefix, marker_body = split_markdown_frontmatter(sanitize_external_markdown_text(marker_markdown))

    base_lines = base_body.split("\n")
    marker_lines = marker_body.split("\n")
    replacements = 0
    matched_candidates = 0

    base_candidates = []
    for idx, line in enumerate(base_lines):
        if not is_plain_text_recovery_candidate(line):
            continue
        normalized = normalize_recovery_line(line)
        if normalized:
            base_candidates.append((idx, line, normalized))

    search_cursor = 0
    repaired_lines: List[str] = []
    for line in marker_lines:
        if not is_plain_text_recovery_candidate(line):
            repaired_lines.append(line)
            continue

        normalized_marker = normalize_recovery_line(line)
        if not normalized_marker:
            repaired_lines.append(line)
            continue

        best_match = None
        best_ratio = 0.0
        window_start = max(0, search_cursor - 2)
        window_end = min(len(base_candidates), search_cursor + 12)
        for idx in range(window_start, window_end):
            _, base_line, normalized_base = base_candidates[idx]
            ratio = difflib.SequenceMatcher(None, normalized_marker, normalized_base).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = (idx, base_line)

        if best_match and best_ratio >= 0.88:
            matched_candidates += 1
            candidate_idx, candidate_line = best_match
            if (
                accent_quality_score(candidate_line) > accent_quality_score(line)
                and normalize_recovery_line(candidate_line) == normalized_marker
            ):
                repaired_lines.append(candidate_line)
                replacements += 1
            else:
                repaired_lines.append(line)
            search_cursor = candidate_idx + 1
        else:
            repaired_lines.append(line)

    merged_body = "\n".join(repaired_lines)
    return marker_prefix + merged_body, {
        "candidate_matches": matched_candidates,
        "replacements": replacements,
        "base_candidates": len(base_candidates),
    }

