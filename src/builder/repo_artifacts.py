from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.utils.helpers import json_str


def student_state_md(
    course_meta: dict,
    student_profile=None,
    *,
    render_student_state_md_fn: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    nick = "Aluno"
    if student_profile and getattr(student_profile, "full_name", ""):
        nick = getattr(student_profile, "nickname", "") or getattr(student_profile, "full_name", "")

    today = datetime.now().strftime("%Y-%m-%d")

    return render_student_state_md_fn(
        course_name=course_name,
        student_nickname=nick,
        today=today,
        active=None,
        active_unit_progress=[],
        recent=[],
        closed_units=[],
        next_topic="",
    )


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


def bundle_priority_score(
    entry: dict,
    *,
    normalize_document_profile_fn: Callable[[str], str],
    exam_categories: set[str],
    exercise_categories: set[str],
) -> int:
    score = 0
    category = (entry.get("category") or "").strip().lower()
    title = (entry.get("title") or "").strip().lower()
    profile = normalize_document_profile_fn(entry.get("effective_profile"))

    if entry.get("include_in_bundle"):
        score += 30
    if entry.get("relevant_for_exam"):
        score += 40
    if category in exam_categories:
        score += 45
    elif category in exercise_categories:
        score += 35
    elif category in {"material-de-aula", "codigo-professor", "quadro-branco"}:
        score += 20
    elif category in {"bibliografia", "referencias", "cronograma"}:
        score += 5

    if profile in {"math_heavy", "diagram_heavy"}:
        score += 10

    if "resumo" in title or "summary" in title:
        score += 10
    if "lista" in title or "exerc" in title:
        score += 8
    return score


def bundle_reason_labels(
    entry: dict,
    *,
    normalize_document_profile_fn: Callable[[str], str],
    exam_categories: set[str],
    exercise_categories: set[str],
) -> List[str]:
    reasons: List[str] = []
    category = (entry.get("category") or "").strip().lower()
    profile = normalize_document_profile_fn(entry.get("effective_profile"))
    if entry.get("include_in_bundle"):
        reasons.append("marcado-manualmente")
    if entry.get("relevant_for_exam"):
        reasons.append("relevante-para-prova")
    if category in exam_categories:
        reasons.append("categoria-prova")
    elif category in exercise_categories:
        reasons.append("categoria-exercicio")
    elif category in {"material-de-aula", "codigo-professor", "quadro-branco"}:
        reasons.append("material-base")
    if profile in {"math_heavy", "diagram_heavy"}:
        reasons.append(f"perfil-{profile}")
    return reasons or ["prioridade-geral"]


def entry_existing_reference_count(
    root_dir: Path,
    entry: dict,
    *,
    entry_image_source_dirs_fn: Callable[[Path, dict], List[Path]],
) -> int:
    refs: List[Path] = []
    for key in [
        "raw_target",
        "base_markdown",
        "advanced_markdown",
        "manual_review",
        "tables_dir",
        "table_detection_dir",
        "advanced_asset_dir",
        "advanced_metadata_path",
        "approved_markdown",
        "curated_markdown",
    ]:
        value = entry.get(key)
        if value:
            refs.append(root_dir / value)
    refs.extend(entry_image_source_dirs_fn(root_dir, entry))
    return sum(1 for path in refs if path.exists())


def filter_live_manifest_entries(
    root_dir: Optional[Path],
    manifest_entries: list,
    *,
    entry_existing_reference_count_fn: Callable[[Path, dict], int],
) -> list:
    if not root_dir:
        return list(manifest_entries or [])

    live_entries = []
    for entry in manifest_entries or []:
        if not isinstance(entry, dict):
            continue

        ref_count = entry_existing_reference_count_fn(root_dir, entry)
        if ref_count > 0:
            live_entries.append(entry)
            continue

        has_any_reference = any(
            entry.get(key)
            for key in [
                "raw_target",
                "base_markdown",
                "advanced_markdown",
                "manual_review",
                "images_dir",
                "tables_dir",
                "table_detection_dir",
                "advanced_asset_dir",
                "advanced_metadata_path",
                "approved_markdown",
                "curated_markdown",
                "rendered_pages_dir",
            ]
        )
        if not has_any_reference:
            live_entries.append(entry)

    return live_entries


def bundle_seed_candidate(
    entry: dict,
    score: int,
    *,
    bundle_reason_labels_fn: Callable[[dict], List[str]],
) -> dict:
    return {
        "id": entry["id"],
        "title": entry["title"],
        "category": entry["category"],
        "preferred_manual_review": entry.get("manual_review"),
        "approved_markdown": entry.get("approved_markdown"),
        "curated_markdown": entry.get("curated_markdown"),
        "advanced_markdown": entry.get("advanced_markdown"),
        "base_markdown": entry.get("base_markdown"),
        "effective_profile": entry.get("effective_profile"),
        "relevant_for_exam": bool(entry.get("relevant_for_exam")),
        "bundle_priority_score": score,
        "bundle_reasons": bundle_reason_labels_fn(entry),
    }


def bibliography_md(
    course_meta: dict,
    entries=None,
    subject_profile=None,
    *,
    parse_bibliography_from_teaching_plan_fn: Callable[[str], dict],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
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

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    parsed = parse_bibliography_from_teaching_plan_fn(teaching_plan) if teaching_plan else {}
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

    return clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def exam_index_md(course_meta: dict, entries=None, *, clamp_navigation_artifact: Callable[..., str]) -> str:
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

    return clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=12000,
        label="course/FILE_MAP.md",
    )


def assignment_index_md(course_meta: dict, entries=None, *, clamp_navigation_artifact: Callable[..., str]) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [
        f"# ASSIGNMENT_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice de trabalhos e projetos.",
        "> Consulte antes de guiar o aluno — não entregue a solução.",
        "",
        "## Trabalhos",
        "",
    ]
    if entries:
        lines += ["| Arquivo | Título | Unidade | Status |", "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} | {e.tags or ''} | pendente |")
    else:
        lines += ["| Arquivo | Título | Unidade | Status |", "|---|---|---|---|", "| [a preencher] | | | |"]
    lines += ["", "## Padrões do professor", "", "- [a preencher]", ""]
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=12000, label="course/FILE_MAP.md")


def code_index_md(
    course_meta: dict,
    entries=None,
    subject_profile=None,
    *,
    code_review_profile_fn: Callable[[Optional[dict], object], dict],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    prof_entries = [e for e in entries if e.category == "codigo-professor"]
    profile = code_review_profile_fn(course_meta, subject_profile)
    lines = [
        f"# CODE_INDEX — {course_name}",
        "",
        profile["code_index_intro"],
        profile["code_index_review_line"],
        "",
    ]
    if prof_entries:
        lines += [
            profile["code_index_section"],
            "",
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
                f"| {Path(e.source_path).name} | {e.tags or ''} | {unit_str} | {conceito} | |"
            )
        lines.append("")
    else:
        lines += [profile["code_index_empty"], ""]
    lines += [
        profile["code_index_patterns"],
        "",
        "<!-- Preencha conforme analisar o código -->",
        "- [a preencher]",
        "",
    ]
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=14000, label="course/COURSE_MAP.md")


def whiteboard_index_md(course_meta: dict, entries=None, *, clamp_navigation_artifact: Callable[..., str]) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [f"# WHITEBOARD_INDEX — {course_name}", "", "> Fotos de quadro branco com explicações do professor.", ""]
    if entries:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |", "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} | {e.tags or ''} | {e.professor_signal or ''} |")
    else:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |", "|---|---|---|---|", "| [a preencher] | | | |"]
    lines += ["", "## Padrões pedagógicos", "", "- [a preencher]", ""]
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=12000, label="course/FILE_MAP.md")


def clamp_navigation_artifact(text: str, *, max_chars: int, label: str) -> str:
    compact = (text or "").strip()
    if len(compact) <= max_chars:
        return compact

    note = f"> Conteúdo truncado para manter {label} compacto e roteável."
    cutoff = max(0, max_chars - len(note) - 4)
    clipped = compact[:cutoff].rstrip()
    if "\n" in clipped:
        clipped = clipped.rsplit("\n", 1)[0].rstrip()
    return f"{clipped}\n\n{note}"


def extract_markdown_headings(
    raw_markdown: str,
    *,
    collapse_ws: Callable[[str], str],
    limit: int = 8,
) -> List[str]:
    headings: List[str] = []
    for line in (raw_markdown or "").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = collapse_ws(match.group(1))
        if not heading:
            continue
        headings.append(heading)
        if len(headings) >= limit:
            break
    return headings


def collect_glossary_evidence(
    root_dir: Optional[Path],
    *,
    manifest_entries: Optional[List[dict]] = None,
    collapse_ws: Callable[[str], str],
    strip_frontmatter_block: Callable[[str], str],
    extract_markdown_headings_fn: Callable[[str], List[str]],
) -> List[Dict[str, str]]:
    if not root_dir:
        return []
    curated_dir = root_dir / "content" / "curated"
    if not curated_dir.exists():
        return []

    manifest_by_markdown: Dict[str, str] = {}
    for entry in manifest_entries or []:
        markdown_path = (
            entry.get("approved_markdown")
            or entry.get("curated_markdown")
            or entry.get("advanced_markdown")
            or entry.get("base_markdown")
            or ""
        )
        if markdown_path:
            manifest_by_markdown[Path(markdown_path).name.lower()] = collapse_ws(
                entry.get("title") or entry.get("name") or ""
            )

    docs: List[Dict[str, str]] = []
    for md_path in sorted(curated_dir.glob("*.md")):
        try:
            raw = md_path.read_text(encoding="utf-8")
        except Exception:
            continue
        body = collapse_ws(strip_frontmatter_block(raw))
        if not body:
            continue
        stripped = strip_frontmatter_block(raw)
        title_match = re.search(r"^#\s+(.+)$", stripped, flags=re.MULTILINE)
        title = collapse_ws(title_match.group(1)) if title_match else md_path.stem.replace("-", " ")
        docs.append({
            "title": title,
            "manifest_title": manifest_by_markdown.get(md_path.name.lower(), ""),
            "headings": extract_markdown_headings_fn(stripped),
            "text": body[:4000],
        })
    return docs


def glossary_tokens(text: str) -> List[str]:
    words = re.findall(r"[a-zà-ÿ0-9]+", (text or "").lower())
    stopwords = {
        "de", "da", "do", "das", "dos", "e", "em", "para", "com", "por", "na",
        "no", "nas", "nos", "um", "uma", "as", "os", "o", "a", "ou", "ao", "à",
        "ii", "iii", "iv", "v", "unidade", "aprendizagem",
    }
    return [word for word in words if len(word) > 2 and word not in stopwords]


def trim_glossary_prefix(text: str, prefixes: List[str], *, collapse_ws: Callable[[str], str]) -> str:
    cleaned = collapse_ws(text)
    if not cleaned:
        return ""
    for prefix in prefixes:
        prefix = collapse_ws(prefix)
        if not prefix:
            continue
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].lstrip(" -:|#")
    return collapse_ws(cleaned)


def shorten_glossary_sentence(sentence: str, *, collapse_ws: Callable[[str], str], max_chars: int = 180) -> str:
    sent = collapse_ws(sentence)
    if len(sent) <= max_chars:
        return sent
    truncated = sent[:max_chars].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip(" ,;:") + "..."


def is_bad_glossary_evidence(sentence: str, *, collapse_ws: Callable[[str], str]) -> bool:
    sent = collapse_ws(sentence)
    if not sent or len(sent) < 40:
        return True
    if sent.count("**") >= 2:
        return True
    if sent.lower().startswith("exemplo:"):
        return True
    if re.match(r"^[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][\wÁÀÂÃÉÊÍÓÔÕÚÇáàâãéêíóôõúç-]+\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ]", sent):
        if re.search(r"\d", sent) and len(sent) <= 80:
            return True
    return False


def normalize_glossary_sentence(
    term: str,
    unit_title: str,
    sentence: str,
    *,
    collapse_ws: Callable[[str], str],
    shorten_glossary_sentence_fn: Callable[[str], str],
) -> str:
    sent = collapse_ws(sentence)
    if not sent:
        return ""
    sent = re.sub(r"^(?:#+\s*)+", "", sent)
    for prefix in [term, unit_title]:
        prefix = collapse_ws(prefix)
        if not prefix:
            continue
        if sent.lower().startswith(prefix.lower()):
            sent = sent[len(prefix):].lstrip(" -:|#")
    sent = collapse_ws(sent)
    if not sent:
        return shorten_glossary_sentence_fn(term, 120)
    if len(sent) > 180:
        sent = shorten_glossary_sentence_fn(sent, 180)
    return sent


def best_glossary_sentence(
    term: str,
    unit_title: str,
    doc: Dict[str, str],
    *,
    collapse_ws: Callable[[str], str],
    glossary_tokens_fn: Callable[[str], List[str]],
    trim_glossary_prefix_fn: Callable[[str, List[str]], str],
    is_bad_glossary_evidence_fn: Callable[[str], bool],
    normalize_glossary_sentence_fn: Callable[[str, str, str], str],
    shorten_glossary_sentence_fn: Callable[[str, int], str],
) -> str:
    prefixes = [
        doc.get("manifest_title", ""),
        doc.get("title", ""),
        *doc.get("headings", []),
    ]
    sources = [
        doc.get("manifest_title", ""),
        doc.get("title", ""),
        " ".join(doc.get("headings", [])),
        trim_glossary_prefix_fn(doc.get("text", ""), prefixes),
    ]
    term_tokens = glossary_tokens_fn(term) + glossary_tokens_fn(unit_title)
    candidate_sentences: List[str] = []
    for source in sources:
        if not source:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", collapse_ws(source)):
            sent = collapse_ws(sentence)
            if len(sent) < 40 or len(sent) > 220:
                continue
            if is_bad_glossary_evidence_fn(sent):
                continue
            candidate_sentences.append(sent)
    best_sentence = ""
    best_score = 0
    for sent in candidate_sentences:
        sent = normalize_glossary_sentence_fn(term, unit_title, sent)
        sent_lower = sent.lower()
        score = 0
        if term.lower() in sent_lower:
            score += 6
        score += sum(1 for token in dict.fromkeys(term_tokens) if token in sent_lower)
        if score > best_score:
            best_score = score
            best_sentence = sent
    fallback = trim_glossary_prefix_fn(doc.get("text", ""), prefixes)
    return best_sentence or shorten_glossary_sentence_fn(fallback or collapse_ws(doc.get("text", "")), 180)


def find_glossary_evidence(
    term: str,
    unit_title: str,
    docs: List[Dict[str, str]],
    *,
    glossary_tokens_fn: Callable[[str], List[str]],
    best_glossary_sentence_fn: Callable[[str, str, Dict[str, str]], str],
) -> str:
    if not docs:
        return ""

    term_lower = (term or "").lower()
    tokens = glossary_tokens_fn(term) + glossary_tokens_fn(unit_title)
    best_score = 0
    best_text = ""

    for doc in docs:
        haystack = " ".join([
            doc.get("manifest_title", ""),
            doc.get("title", ""),
            " ".join(doc.get("headings", [])),
            doc.get("text", ""),
        ]).lower()
        score = 0
        if term_lower and term_lower in haystack:
            score += 8
        score += sum(1 for token in dict.fromkeys(tokens) if token in haystack)
        if score < 3 or score <= best_score:
            continue
        best_score = score
        best_text = best_glossary_sentence_fn(term, unit_title, doc)

    return best_text[:600]


def refine_glossary_definition_from_evidence(
    term: str,
    unit_hint: str,
    evidence: str,
    *,
    collapse_ws: Callable[[str], str],
    glossary_tokens_fn: Callable[[str], List[str]],
    normalize_glossary_sentence_fn: Callable[[str, str, str], str],
    shorten_glossary_sentence_fn: Callable[[str, int], str],
) -> str:
    compact = collapse_ws(evidence)
    if compact:
        sentences = re.split(r"(?<=[.!?])\s+", compact)
        term_tokens = glossary_tokens_fn(term)
        for sentence in sentences:
            sent = normalize_glossary_sentence_fn(term, unit_hint, sentence)
            sent_lower = sent.lower()
            if len(sent) < 40:
                continue
            if term.lower() in sent_lower or sum(1 for token in term_tokens if token in sent_lower) >= 2:
                cleaned = re.sub(r"^[^A-Za-zÀ-ÿ0-9]*", "", sent).rstrip(" .")
                cleaned = shorten_glossary_sentence_fn(cleaned, 180)
                if not cleaned.endswith("."):
                    cleaned += "."
                return cleaned
    return f"Conceito central de {unit_hint} que deve ser reconhecido e usado corretamente nas respostas e revisões."


def seed_glossary_fields(
    term: str,
    unit_title: str,
    *,
    evidence: str = "",
    collapse_ws: Callable[[str], str],
    refine_glossary_definition_from_evidence_fn: Callable[[str, str, str], str],
) -> tuple[str, str, str]:
    text = collapse_ws(term)
    lower = text.lower()
    unit_lower = (unit_title or "").lower()

    def _unit_hint() -> str:
        if "visão geral" in unit_lower or "visao geral" in unit_lower:
            return "visão geral"
        if "aprendizado de máquina" in unit_lower or "machine" in unit_lower:
            return "aprendizado de máquina"
        if "incerteza" in unit_lower or "probabilidade" in unit_lower:
            return "raciocínio sob incerteza"
        if "planejamento" in unit_lower:
            return "planejamento e representação de conhecimento"
        if "problemas" in unit_lower or "busca" in unit_lower:
            return "solução de problemas"
        if "verificação de programas" in unit_lower:
            return "verificação de programas"
        if "verificação de modelos" in unit_lower:
            return "verificação de modelos"
        if "métodos formais" in unit_lower:
            return "métodos formais"
        return "esta unidade"

    def _generic_definition() -> str:
        return refine_glossary_definition_from_evidence_fn(text, _unit_hint(), evidence)

    if "lógica de hoare" in lower:
        return (
            "Formalismo para especificar e verificar programas com pré-condições, pós-condições e invariantes.",
            "tripla de Hoare",
            "lógica temporal",
        )
    if "model checking" in lower or "verificação de modelos" in lower:
        return (
            "Técnica automática que checa se um modelo de sistema satisfaz propriedades formais.",
            "checagem de modelos",
            "prova de teoremas",
        )
    if "provadores de teoremas" in lower or "prova interativa de teoremas" in lower:
        return (
            "Ferramentas e técnicas usadas para construir provas formais com assistência mecânica.",
            "assistentes de prova",
            "model checking",
        )
    if "métodos formais" in lower:
        return (
            "Conjunto de técnicas matemáticas para especificar, modelar e verificar sistemas de software.",
            "formal methods",
            "testes informais",
        )
    if "máquinas de estado" in lower:
        return (
            "Modelo que representa um sistema por estados e transições entre eles.",
            "state machines",
            "árvores de derivação",
        )
    if "modelos de kripke" in lower:
        return (
            "Estruturas de estados rotulados usadas para interpretar propriedades em lógica temporal.",
            "estruturas de Kripke",
            "máquina de Turing",
        )
    if "lógica temporal linear" in lower:
        return (
            "Lógica temporal que descreve propriedades ao longo de sequências lineares de estados.",
            "LTL",
            "CTL",
        )
    if "lógica temporal ramificada" in lower:
        return (
            "Lógica temporal que considera múltiplos futuros possíveis a partir de um estado.",
            "CTL",
            "LTL",
        )
    if "pré e pós" in lower:
        return (
            "Condições que descrevem o que deve valer antes e depois da execução de um programa.",
            "precondições e pós-condições",
            "invariantes de laço",
        )
    if "invariante e variante de laço" in lower:
        return (
            "Propriedades usadas para demonstrar correção parcial e terminação de laços.",
            "invariante de laço",
            "pré-condições",
        )
    if "planejamento clássico" in lower or lower == "planejamento":
        return (
            "Abordagem que busca sequências de ações para atingir objetivos em um modelo explícito de estados.",
            "planning",
            "busca adversária",
        )
    if "agentes em lógica" in lower or "introdução a agentes" in lower:
        return (
            "Modelo de agente que percebe o ambiente e escolhe ações segundo uma representação formal.",
            "agentes racionais",
            "classificadores supervisionados",
        )
    if "busca informada" in lower:
        return (
            "Busca guiada por heurísticas para explorar primeiro estados mais promissores.",
            "busca heurística",
            "busca cega",
        )
    if "algoritmos de busca" in lower:
        return (
            "Procedimentos para explorar espaços de estados e encontrar soluções para problemas modelados.",
            "search algorithms",
            "métodos de otimização contínua",
        )
    if "busca adversária" in lower:
        return (
            "Estratégia de decisão para problemas competitivos em que as ações dependem do oponente.",
            "jogos adversariais",
            "busca heurística simples",
        )
    if "representação de problemas" in lower:
        return (
            "Forma de modelar estados, ações, restrições e objetivos para permitir resolução algorítmica.",
            "modelagem do problema",
            "pré-processamento de dados",
        )
    if "probabilidade" in lower or "regra de bayes" in lower or "independência e permutabilidade" in lower:
        return (
            "Conceito central de raciocínio sob incerteza usado para modelar crenças e atualizar evidências.",
            "inferência probabilística",
            "lógica determinística",
        )
    if "aprendizado de máquina" in lower:
        return (
            "Área da IA que aprende padrões a partir de dados para descrever ou prever comportamentos.",
            "machine learning",
            "planejamento clássico",
        )
    if "paradigmas de aprendizado" in lower:
        return (
            "Categorias de estratégias de aprendizado, como supervisionado, não supervisionado e por reforço.",
            "tipos de aprendizado",
            "métricas de avaliação",
        )
    if "modelos preditivos" in lower:
        return (
            "Modelos voltados a prever saídas, classes ou valores a partir de exemplos observados.",
            "modelos supervisionados",
            "modelos descritivos",
        )
    if "modelos descritivos" in lower:
        return (
            "Modelos usados para revelar estrutura, agrupamentos ou relações presentes nos dados.",
            "modelos exploratórios",
            "modelos preditivos",
        )
    if "métricas de avaliação" in lower:
        return (
            "Critérios quantitativos usados para comparar desempenho e qualidade de modelos.",
            "medidas de desempenho",
            "função objetivo do problema",
        )
    if "k-means" in lower:
        return (
            "Algoritmo de agrupamento que particiona exemplos em grupos definidos por centróides.",
            "agrupamento k-means",
            "k-NN",
        )
    if "k-nn" in lower:
        return (
            "Método que classifica ou estima saídas com base nos vizinhos mais próximos no espaço de atributos.",
            "k nearest neighbors",
            "k-means",
        )
    if "árvores de decisão" in lower:
        return (
            "Modelo que organiza decisões em divisões sucessivas sobre atributos dos dados.",
            "decision trees",
            "grafos de busca",
        )
    if "mlp" in lower or "rede neural" in lower or "perceptron" in lower:
        return (
            "Família de modelos conexionistas que aprende transformações por camadas a partir de exemplos.",
            "redes neurais artificiais",
            "árvore de decisão",
        )
    if "conceituação" in lower:
        return (
            refine_glossary_definition_from_evidence_fn(text, _unit_hint(), evidence),
            "visão geral",
            "detalhamento técnico",
        )
    if "histórico" in lower:
        return (
            refine_glossary_definition_from_evidence_fn(text, _unit_hint(), evidence),
            "contexto histórico",
            "estado da arte detalhado",
        )

    return (
        _generic_definition(),
        "—",
        "—",
    )


def glossary_md(
    course_meta: dict,
    subject_profile=None,
    *,
    root_dir: Optional[Path] = None,
    manifest_entries: Optional[List[dict]] = None,
    parse_units_from_teaching_plan_fn: Callable[[str], list],
    topic_text_fn: Callable[[object], str],
    collect_glossary_evidence_fn: Callable[[Optional[Path]], List[Dict[str, str]]],
    find_glossary_evidence_fn: Callable[[str, str, List[Dict[str, str]]], str],
    seed_glossary_fields_fn: Callable[[str, str, str], tuple[str, str, str]],
    clamp_navigation_artifact_fn: Callable[..., str],
) -> str:
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
    units = parse_units_from_teaching_plan_fn(teaching_plan) if teaching_plan else []
    evidence_docs = collect_glossary_evidence_fn(root_dir, manifest_entries=manifest_entries) if root_dir else []

    candidates = []
    for unit_title, topics in units:
        for topic in topics:
            candidates.append((topic_text_fn(topic), unit_title))

    if candidates:
        lines.append("> Termos extraídos automaticamente do plano de ensino.")
        lines.append("> Definições iniciais curtas são geradas no build para reduzir custo de contexto no tutor web.")
        lines.append("")
        for term, unit_title in candidates:
            evidence = find_glossary_evidence_fn(term, unit_title, evidence_docs)
            definition, synonyms, not_confuse = seed_glossary_fields_fn(term, unit_title, evidence=evidence)
            lines += [
                f"## {term}",
                f"**Definição:** {definition}",
                f"**Sinônimos aceitos:** {synonyms}",
                f"**Não confundir com:** {not_confuse}",
                f"**Aparece em:** {unit_title}",
                "",
            ]
    else:
        lines.append("> ⏳ **Termos serão adicionados pelo tutor na primeira sessão.**")
        lines.append("")

    return clamp_navigation_artifact_fn(
        "\n".join(lines),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def root_readme(course_meta: dict) -> str:
    return f"""# {course_meta.get('course_name', 'Curso')}

Repositório gerado pelo **Academic Tutor Repo Builder V3**.
Plataforma alvo: **Claude Projects** (claude.ai)

## Como usar com Claude

1. Crie um **Projeto** no Claude.ai com o nome desta disciplina
2. Cole o conteúdo de `setup/INSTRUCOES_CLAUDE_PROJETO.md` no campo **Instructions** do Projeto
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
| `setup/INSTRUCOES_CLAUDE_PROJETO.md` | System prompt do Projeto (não indexado pelo tutor) |
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


def wrap_frontmatter(meta: dict, body: str, *, json_str_fn: Optional[Callable[[Any], str]] = None) -> str:
    json_str_fn = json_str_fn or json_str
    header = ["---"]
    for k, v in meta.items():
        header.append(f"{k}: {json_str_fn(v)}")
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


def manual_pdf_review_template(entry, item: Dict[str, object], *, json_str_fn: Callable[[Any], str]) -> str:
    report = item.get("document_report") or {}
    decision = item.get("pipeline_decision") or {}
    return f"""---
id: {entry.id()}
title: {json_str_fn(entry.title)}
type: manual_pdf_review
category: {entry.category}
source_pdf: {json_str_fn(item.get('raw_target'))}
processing_mode: {json_str_fn(entry.processing_mode)}
document_profile: {json_str_fn(entry.document_profile)}
page_range: {json_str_fn(entry.page_range)}
effective_profile: {json_str_fn(item.get('effective_profile'))}
base_backend: {json_str_fn(item.get('base_backend'))}
advanced_backend: {json_str_fn(item.get('advanced_backend'))}
base_markdown: {json_str_fn(item.get('base_markdown'))}
advanced_markdown: {json_str_fn(item.get('advanced_markdown'))}
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


def manual_image_review_template(entry, raw_target: Path, root_dir: Path, *, safe_rel_fn: Callable[[Path, Path], str]) -> str:
    image_path = safe_rel_fn(raw_target, root_dir)
    return f"""---
id: {entry.id()}
title: {json.dumps(entry.title, ensure_ascii=False)}
type: manual_image_review
category: {entry.category}
source_image: {json.dumps(image_path, ensure_ascii=False)}
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


def manual_url_review_template(entry, item: Dict[str, object], *, json_str_fn: Callable[[Any], str]) -> str:
    source_url = entry.source_path
    return f"""---
id: {entry.id()}
title: {json_str_fn(entry.title)}
type: manual_url_review
category: {entry.category}
source_url: {json_str_fn(source_url)}
processing_mode: {json_str_fn(entry.processing_mode)}
base_backend: {json_str_fn(item.get('base_backend'))}
base_markdown: {json_str_fn(item.get('base_markdown'))}
---

# Revisão Manual — Página Web

## Origem
- URL: <{source_url}>
- Backend base: `{item.get('base_backend')}`

## Checklist
- [ ] Conferir se o conteúdo baixado corresponde à página correta
- [ ] Remover navegação, rodapé, anúncios e texto irrelevante
- [ ] Corrigir títulos e hierarquia de seções
- [ ] Verificar se links importantes foram preservados
- [ ] Destacar trechos úteis para o tutor

## Markdown corrigido
<!-- Cole aqui a versão corrigida -->

## Destino curado sugerido
- [ ] `content/curated/`
- [ ] `course/references/`
"""


def migrate_legacy_url_manual_reviews(
    root_dir: Path,
    *,
    ensure_dir_fn: Callable[[Path], None],
    safe_rel_fn: Callable[[Path, Path], str],
    write_text_fn: Callable[[Path, str], None],
    logger,
) -> int:
    manual_pdfs_dir = root_dir / "manual-review" / "pdfs"
    manual_web_dir = root_dir / "manual-review" / "web"
    if not manual_pdfs_dir.exists():
        return 0

    ensure_dir_fn(manual_web_dir)
    manifest_path = root_dir / "manifest.json"
    manifest = None
    manifest_changed = False
    moved = 0

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not read manifest.json during URL review migration: %s", exc)
            manifest = None

    for review_path in manual_pdfs_dir.rglob("*.md"):
        try:
            content = review_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        fm = {}
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            for line in match.group(1).strip().split("\n"):
                if ":" not in line:
                    continue
                key, _, value = line.partition(":")
                fm[key.strip()] = value.strip().strip('"').strip("'")

        if fm.get("type") != "manual_url_review" and fm.get("base_backend") != "url_fetcher":
            continue

        destination = manual_web_dir / review_path.name
        if destination.exists():
            try:
                review_path.unlink()
            except Exception as exc:
                logger.warning("Could not remove duplicate legacy URL review %s: %s", review_path, exc)
            else:
                moved += 1
            continue

        ensure_dir_fn(destination.parent)
        try:
            shutil.move(str(review_path), str(destination))
        except Exception as exc:
            logger.warning("Could not migrate legacy URL review %s: %s", review_path, exc)
            continue

        moved += 1
        entry_id = fm.get("id") or destination.stem
        if manifest:
            for entry in manifest.get("entries", []):
                if entry.get("id") == entry_id and entry.get("manual_review"):
                    old_rel = safe_rel_fn(review_path, root_dir)
                    if entry.get("manual_review") == old_rel:
                        entry["manual_review"] = safe_rel_fn(destination, root_dir)
                        manifest_changed = True
                    break

    if manifest and manifest_changed:
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        write_text_fn(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))

    return moved


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


def backend_policy_yaml(options: Dict[str, object], *, json_str_fn: Callable[[Any], str]) -> str:
    return f"""version: 3
target_platform: claude-projects
policy:
  default_processing_mode: {options.get('default_processing_mode', 'auto')}
  default_ocr_language: {json_str_fn(options.get('default_ocr_language', 'por,eng'))}
  require_manual_review_for:
    - math_heavy
    - scanned
    - diagram_heavy
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


def exercise_index_md(
    course_meta: dict,
    entries=None,
    *,
    collapse_ws_fn: Callable[[str], str],
    merge_manual_and_auto_tags_fn: Callable[..., str],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [
        f"# EXERCISE_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice operacional de prática da disciplina.",
        "> O tutor consulta este arquivo para localizar listas, provas antigas",
        "> e recursos de exercícios por unidade, prioridade e finalidade.",
        "",
        "| Recurso | Tipo | Unidade | Solução | Prioridade | Quando usar |",
        "|---|---|---|---|---|---|",
    ]
    if entries:
        for entry in entries:
            notes = collapse_ws_fn(entry.notes or "")
            tags = collapse_ws_fn(
                merge_manual_and_auto_tags_fn(
                    list(entry.manual_tags or []),
                    list(entry.auto_tags or []),
                    fallback_tags=entry.tags or "",
                    limit=3,
                )
            )
            category = collapse_ws_fn(entry.category or "")
            category_lower = category.lower()
            kind = "prova" if "prova" in category_lower else "lista" if "lista" in category_lower else "exercício"
            has_solution = "sim" if any(token in notes.lower() for token in ["gabarito", "resolu", "soluç"]) else "não"
            priority = "alta" if "prova" in category_lower or has_solution == "sim" else "média"
            usage = "revisão de prova" if "prova" in category_lower else "fixação por unidade"
            lines.append(
                f"| {entry.title} | {kind} | {tags or 'não mapeado'} | {has_solution} | {priority} | {usage} |"
            )
    else:
        lines.append("| [a preencher] | | | | | |")
        lines += [
            "",
            "> Adicione listas ou provas antigas para o tutor conseguir sugerir prática com baixo custo de contexto.",
        ]
    lines.append("")
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=14000, label="exercises/EXERCISE_INDEX.md")
