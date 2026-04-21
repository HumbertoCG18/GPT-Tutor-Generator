from __future__ import annotations

from pathlib import Path
import re
from typing import Callable, List, Optional

from src.utils.helpers import (
    ASSIGNMENT_CATEGORIES,
    CODE_CATEGORIES,
    EXAM_CATEGORIES,
    EXERCISE_CATEGORIES,
    WHITEBOARD_CATEGORIES,
    write_text,
)


def _entry_priority_label(entry: dict) -> str:
    category = (entry.get("category") or "").strip().lower()
    if entry.get("relevant_for_exam") or entry.get("include_in_bundle"):
        return "alta"
    if category in EXAM_CATEGORIES or category in EXERCISE_CATEGORIES:
        return "alta"
    if category in {"material-de-aula", "codigo-professor", "quadro-branco"}:
        return "media"
    return "normal"


def _entry_usage_hint(entry: dict) -> str:
    category = (entry.get("category") or "").strip().lower()
    if category in {"material-de-aula", "slides", "apostila"}:
        return "teoria base"
    if category in EXAM_CATEGORIES:
        return "provas e revisão"
    if category in EXERCISE_CATEGORIES:
        return "exercícios"
    if category in ASSIGNMENT_CATEGORIES:
        return "trabalhos"
    if category in CODE_CATEGORIES:
        return "exemplos de código"
    if category in WHITEBOARD_CATEGORIES:
        return "explicações do professor"
    if category in {"cronograma", "bibliografia", "referencias"}:
        return "referência geral"
    return "consulta pontual"


def _entry_markdown_path_for_file_map(root_dir: Optional[Path], entry: dict) -> Optional[Path]:
    if not root_dir:
        return None
    for key in ["approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"]:
        rel_path = entry.get(key)
        if not rel_path or not str(rel_path).lower().endswith(".md"):
            continue
        md_path = root_dir / rel_path
        if md_path.exists() and md_path.is_file():
            return md_path
    return None


def _entry_markdown_text_for_file_map(root_dir: Optional[Path], entry: dict) -> str:
    if "_markdown_text_for_tests" in entry:
        return entry.get("_markdown_text_for_tests") or ""
    md_path = _entry_markdown_path_for_file_map(root_dir, entry)
    if not md_path:
        return ""
    try:
        return md_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _infer_unit_confidence(entry: dict) -> str:
    if str(entry.get("manual_unit_slug") or "").strip():
        return "Alta"

    resolved_unit = (
        str(entry.get("_resolved_unit_slug") or "").strip()
        or str(entry.get("unit_slug") or "").strip()
        or str(entry.get("unit") or "").strip()
    )
    if not resolved_unit:
        return "Baixa"
    if resolved_unit == "curso-inteiro":
        return "Alta"

    match_confidence = float(entry.get("_unit_match_confidence") or 0.0)
    ambiguous = bool(entry.get("_unit_match_ambiguous"))
    signal_count = sum(
        1
        for flag in (
            entry.get("_resolved_topic_slug"),
            entry.get("_resolved_period"),
            entry.get("manual_timeline_block_id"),
        )
        if flag
    )

    if ambiguous or match_confidence < 0.45:
        return "Baixa"
    if match_confidence >= 0.85 or signal_count >= 2:
        return "Alta"
    return "Média"


def _file_map_markdown_cell(md_path: str) -> str:
    rel = (md_path or "").strip()
    if not rel:
        return "—"
    rel_posix = rel.replace("\\", "/")
    if rel_posix.startswith("staging/"):
        return "A revisar"
    return f"`{rel}`"


def _extract_section_headers(md_content: str) -> list[dict]:
    headers: list[dict] = []
    in_code = False
    in_summary = False

    for i, line in enumerate((md_content or "").splitlines()):
        stripped = line.strip()

        if "<!-- EXEC_SUMMARY_START -->" in stripped:
            in_summary = True
            continue
        if "<!-- EXEC_SUMMARY_END -->" in stripped:
            in_summary = False
            continue
        if in_summary:
            continue

        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        match = re.match(r"^(#{2,3})\s+(.+)", line)
        if not match:
            continue

        level = len(match.group(1))
        title = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", match.group(2)).strip()
        if title:
            headers.append({"title": title, "level": level, "line": i})

    return headers


def _inject_executive_summary(md_path: Path) -> bool:
    if not md_path.exists():
        return False

    content = md_path.read_text(encoding="utf-8")
    summary_re = re.compile(
        r"<!-- EXEC_SUMMARY_START -->.*?<!-- EXEC_SUMMARY_END -->\n?",
        flags=re.DOTALL,
    )
    clean = summary_re.sub("", content)
    headers = _extract_section_headers(clean)

    if len(headers) < 2:
        if clean != content:
            write_text(md_path, clean)
            return True
        return False

    lines = [
        "<!-- EXEC_SUMMARY_START -->",
        "## Sumário",
        "> *Leia antes de varrer o arquivo. Vá direto à seção relevante para a pergunta do aluno.*",
        "",
    ]
    for header in headers:
        if header["level"] == 2:
            lines.append(f"- **{header['title']}**")
        else:
            lines.append(f"  - {header['title']}")
    lines += ["", "<!-- EXEC_SUMMARY_END -->", ""]
    block = "\n".join(lines)

    frontmatter = re.match(r"^---\n.*?\n---\n", clean, re.DOTALL)
    if frontmatter:
        new_content = clean[:frontmatter.end()] + "\n" + block + clean[frontmatter.end():]
    else:
        new_content = block + clean

    if new_content == content:
        return False

    write_text(md_path, new_content)
    return True


def _clean_extraction_noise(content: str) -> str:
    page_num_re = re.compile(
        r"^[\s\-\u2013\u2014]*\d{1,4}[\s\-\u2013\u2014]*$"
        r"|^[Pp][áa]gina\s+\d+$"
        r"|^[Pp]age\s+\d+\s+of\s+\d+$"
    )
    separator_re = re.compile(r"^[-_=]{4,}$")
    header_re = re.compile(r"^#{1,6}\s+")

    result: list[str] = []
    in_code = False
    in_math_block = False
    prev_header = None
    blank_run = 0

    for line in (content or "").splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code = not in_code
            result.append(line)
            blank_run = 0
            prev_header = None
            continue

        if in_code:
            result.append(line)
            blank_run = 0
            continue

        math_delimiters = line.count("$$")
        if in_math_block:
            result.append(line)
            blank_run = 0
            if math_delimiters % 2 == 1:
                in_math_block = False
            continue
        if math_delimiters % 2 == 1:
            in_math_block = True
            result.append(line)
            blank_run = 0
            prev_header = None
            continue

        if not stripped:
            blank_run += 1
            if blank_run <= 2:
                result.append("")
            continue
        blank_run = 0

        if page_num_re.match(stripped):
            continue
        if separator_re.match(stripped):
            continue

        if header_re.match(line):
            if stripped == prev_header:
                continue
            prev_header = stripped
        else:
            prev_header = None

        result.append(line)

    return "\n".join(result)


def _get_entry_sections(md_path: Path, max_h2: int = 4) -> str:
    if not md_path or not md_path.exists():
        return ""
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    h2 = [header["title"] for header in _extract_section_headers(text) if header["level"] == 2][:max_h2]
    return "  ".join(h2) if h2 else ""


def render_course_map_md(
    course_meta: dict,
    subject_profile=None,
    *,
    parse_units_from_teaching_plan: Callable[[str], list],
    topic_text: Callable[[object], str],
    topic_depth: Callable[[object], int],
    parse_syllabus_timeline: Callable[[str], list],
    match_timeline_to_units: Callable[[list, list], list],
    build_assessment_context_from_course: Callable[[dict, object], dict],
    assessment_conflict_section_lines: Callable[[Optional[dict], bool], List[str]],
    clamp_navigation_artifact: Callable[..., str],
    logger,
) -> str:
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
    units = parse_units_from_teaching_plan(teaching_plan) if teaching_plan else []

    lines.append("## Estrutura do curso")
    lines.append("")

    if units:
        for unit_title, topics in units:
            lines.append(f"### {unit_title}")
            if topics:
                for topic in topics:
                    text = topic_text(topic)
                    depth = topic_depth(topic)
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

    syllabus = getattr(subject_profile, "syllabus", "") if subject_profile else ""
    if units and syllabus:
        try:
            timeline = parse_syllabus_timeline(syllabus)
            mapping = match_timeline_to_units(timeline, units)
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
                for item in mapping:
                    period = item["period"] or "[não identificado]"
                    lines.append(f"| {item['unit_title']} | {period} | `{item['unit_slug']}` |")
                lines.append("")
        except Exception as exc:
            logger.debug("Could not generate timeline mapping: %s", exc)

    assessment_context = course_meta.get("_assessment_context") or (
        build_assessment_context_from_course(course_meta, subject_profile)
        if subject_profile and getattr(subject_profile, "teaching_plan", "") and getattr(subject_profile, "syllabus", "")
        else {"version": 1, "assessments": [], "conflicts": []}
    )
    lines += assessment_conflict_section_lines(assessment_context, compact=False)

    lines += [
        "## Tópicos de alta incidência em prova",
        "",
        "> ⏳ **Aguardando análise do tutor** — esta tabela pode ser refinada quando o tutor",
        "> cruzar as provas em `exams/` com as unidades acima.",
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

    return clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def render_low_token_course_map_md(
    course_meta: dict,
    subject_profile=None,
    *,
    build_file_map_timeline_context_from_course: Callable[[dict, object], dict],
    aggregate_unit_periods_from_blocks: Callable[[dict], dict],
    normalize_unit_slug: Callable[[str], str],
    parse_units_from_teaching_plan: Callable[[str], list],
    topic_text: Callable[[object], str],
    topic_depth: Callable[[object], int],
    build_assessment_context_from_course: Callable[[dict, object], dict],
    assessment_conflict_section_lines: Callable[[Optional[dict], bool], List[str]],
    clamp_navigation_artifact: Callable[..., str],
    logger,
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    timeline_context = dict(
        course_meta.get("_timeline_context")
        or course_meta.get("_timeline_context_for_tests")
        or build_file_map_timeline_context_from_course(course_meta, subject_profile)
    )
    lines = [
        f"# COURSE_MAP — {course_name}",
        "",
        "> Mapa pedagógico curto da disciplina.",
        "> Use este arquivo para ordem, dependências e foco atual; os detalhes vivem nos materiais referenciados.",
        "> Não replique explicações longas aqui.",
    ]

    if subject_profile and subject_profile.syllabus:
        lines.append("> Cronograma completo disponível em `course/SYLLABUS.md`.")
    lines.append("")

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    units = parse_units_from_teaching_plan(teaching_plan) if teaching_plan else []

    lines += ["## Estrutura do curso", ""]
    if units:
        for unit_title, topics in units:
            lines.append(f"### {unit_title}")
            if topics:
                for topic in topics:
                    indent = "  " * topic_depth(topic)
                    lines.append(f"{indent}- [ ] {topic_text(topic)}")
            else:
                lines.append("- [ ] [tópicos a preencher]")
            lines.append("")
    else:
        lines += [
            "### Unidade 1 — [Nome da unidade]",
            "- [ ] Tópico 1.1",
            "- [ ] Tópico 1.2",
            "",
            "### Unidade 2 — [Nome da unidade]",
            "- [ ] Tópico 2.1 -> requer: Tópico 1.2",
            "- [ ] Tópico 2.2",
            "",
        ]

    syllabus = getattr(subject_profile, "syllabus", "") if subject_profile else ""
    if units and syllabus:
        try:
            blocks_by_unit = timeline_context.get("blocks_by_unit", {}) if timeline_context else {}
            if blocks_by_unit:
                period_map = aggregate_unit_periods_from_blocks(blocks_by_unit)
                mapping = []
                for unit_title, _topics in units:
                    unit_slug = normalize_unit_slug(unit_title)
                    mapping.append(
                        {
                            "unit_title": unit_title,
                            "unit_slug": unit_slug,
                            "period": period_map.get(unit_slug, ""),
                        }
                    )
            else:
                mapping = []
            identified = [m for m in mapping if m["period"]]
            if identified:
                lines += [
                    "## Timeline — Cronograma x Unidades",
                    "",
                    "| Unidade | Período | Slug |",
                    "|---|---|---|",
                ]
                for item in identified:
                    lines.append(f"| {item['unit_title']} | {item['period']} | `{item['unit_slug']}` |")
                if len(identified) < len(mapping):
                    lines += [
                        "",
                        "> Unidades sem período explícito foram omitidas para manter o mapa enxuto.",
                    ]
                lines.append("")
        except Exception as exc:
            logger.debug("Could not generate timeline mapping: %s", exc)

    assessment_context = course_meta.get("_assessment_context") or (
        build_assessment_context_from_course(course_meta, subject_profile)
        if subject_profile and getattr(subject_profile, "teaching_plan", "") and getattr(subject_profile, "syllabus", "")
        else {"version": 1, "assessments": [], "conflicts": []}
    )
    lines += assessment_conflict_section_lines(assessment_context, compact=False)

    lines += [
        "## Tópicos de alta incidência em prova",
        "",
        "> Preencha só os tópicos realmente recorrentes nas provas.",
        "",
        "| Tópico | Unidade | Incidência |",
        "|---|---|---|",
        "",
        "## Notas do professor",
        "",
        "> Registre apenas padrões de cobrança, ênfases e avisos operacionais.",
        "",
    ]
    result = "\n".join(lines)
    return clamp_navigation_artifact(
        result,
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def render_low_token_course_map_md_v2(
    course_meta: dict,
    subject_profile=None,
    *,
    render_low_token_course_map_md_fn: Callable[[dict, object], str],
) -> str:
    base = render_low_token_course_map_md_fn(course_meta, subject_profile)
    lines = base.splitlines()
    stop_headers = {
        "## Tópicos de alta incidência em prova",
        "## Notas do professor",
    }
    trimmed: List[str] = []
    for line in lines:
        if line.strip() in stop_headers:
            break
        trimmed.append(line)
    return "\n".join(trimmed).rstrip() + "\n"


def render_low_token_file_map_md(
    course_meta: dict,
    manifest_entries: list,
    subject_profile=None,
    *,
    build_file_map_content_taxonomy_from_course: Callable[[dict, object, list], dict],
    build_file_map_unit_index_from_course: Callable[[dict, object], list],
    build_file_map_timeline_context_from_course: Callable[[dict, object], dict],
    iter_content_taxonomy_topics: Callable[[dict], list],
    merge_manual_and_auto_tags: Callable[..., str],
    resolve_entry_manual_timeline_block: Callable[[dict, dict], object],
    entry_markdown_text_for_file_map: Callable[[object, dict], str],
    auto_map_entry_subtopic: Callable[[dict, dict, str], object],
    resolve_entry_manual_unit_slug: Callable[[dict, list], str],
    unit_match_result_factory: Callable[..., object],
    derive_unit_from_topic_match: Callable[[object, dict], str],
    auto_map_entry_unit: Callable[[dict, list, str, list], object],
    select_probable_period_for_entry: Callable[..., tuple],
    file_map_markdown_cell: Callable[[str], str],
    entry_markdown_path_for_file_map: Callable[[object, dict], object],
    get_entry_sections: Callable[[object], str],
    infer_unit_confidence: Callable[[dict], str],
    entry_usage_hint: Callable[[dict], str],
    entry_priority_label: Callable[[dict], str],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    content_taxonomy = dict(
        course_meta.get("_content_taxonomy")
        or course_meta.get("_content_taxonomy_for_tests")
        or build_file_map_content_taxonomy_from_course(
            course_meta,
            subject_profile,
            manifest_entries,
        )
    )
    unit_index = build_file_map_unit_index_from_course(course_meta, subject_profile)
    temporal_context = dict(
        course_meta.get("_timeline_context")
        or course_meta.get("_timeline_context_for_tests")
        or build_file_map_timeline_context_from_course(course_meta, subject_profile)
    )
    topic_index = iter_content_taxonomy_topics(content_taxonomy)
    blocks_by_unit = temporal_context.get("blocks_by_unit", {}) if temporal_context else {}
    unassigned_blocks = temporal_context.get("unassigned_blocks", []) if temporal_context else []
    unit_by_slug = {unit.get("slug", ""): unit for unit in unit_index if unit.get("slug")}
    lines = [
        "---",
        f"course: {course_name}",
        "status: pending_review",
        "mode: routing_index",
        "---",
        "",
        f"# FILE_MAP — {course_name}",
        "",
        "> Índice de roteamento do repositório.",
        "> Use este arquivo para localizar o material certo antes de abrir arquivos longos.",
        "",
        "## Ordem de consulta econômica",
        "",
        "1. Leia `course/COURSE_MAP.md` para saber a unidade e o contexto.",
        "2. Use este `FILE_MAP.md` para escolher o material certo.",
        "3. Abra o markdown do item escolhido.",
        "4. Recorra ao PDF bruto apenas se o markdown não bastar.",
        "",
        "## Arquivos do repositório",
        "",
        "> **Como usar as novas colunas:**",
        "> - **Seções**: leia antes de abrir o arquivo; vá direto à seção relevante.",
        "> - **Confiança**: entradas `Baixa` têm mapeamento incerto; use override no backlog se necessário (não edite FILE_MAP manualmente).",
        "",
    ]

    if not manifest_entries:
        lines.append("Nenhum arquivo processado ainda.")
        return "\n".join(lines)

    lines += [
        "| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Seções | Unidade | Confiança | Período |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for i, entry in enumerate(manifest_entries, 1):
        title = entry.get("title", "")
        category = entry.get("category", "")
        tags = entry.get("tags", "")
        effective_tags = merge_manual_and_auto_tags(
            list(entry.get("manual_tags") or []),
            list(entry.get("auto_tags") or []),
            fallback_tags=tags,
            limit=3,
        )
        md_path = (
            entry.get("approved_markdown")
            or entry.get("curated_markdown")
            or entry.get("base_markdown")
            or entry.get("advanced_markdown")
            or ""
        )
        raw_path = entry.get("raw_target") or ""
        _NO_TIMELINE_CATEGORIES = {"cronograma", "bibliografia", "referencias", "references"}
        if category in _NO_TIMELINE_CATEGORIES:
            unit = "curso-inteiro"
            skip_timeline = True
        else:
            unit = ""
            skip_timeline = False
        period = ""
        match = unit_match_result_factory(slug="", confidence=0.0, ambiguous=True, reasons=[])
        preferred_topic_slug = ""
        manual_timeline_block = resolve_entry_manual_timeline_block(entry, temporal_context)
        markdown_text = entry_markdown_text_for_file_map(course_meta.get("_repo_root"), entry)
        if not skip_timeline and not unit and unit_index:
            topic_match = auto_map_entry_subtopic(entry, content_taxonomy, markdown_text)
            if topic_match.topic_slug and not topic_match.ambiguous and topic_match.confidence >= 0.45:
                preferred_topic_slug = topic_match.topic_slug
            manual_unit_slug = resolve_entry_manual_unit_slug(entry, unit_index)
            if manual_unit_slug:
                match = unit_match_result_factory(
                    slug=manual_unit_slug,
                    confidence=1.0,
                    ambiguous=False,
                    reasons=["manual-unit-override"],
                )
            else:
                derived_unit_slug = derive_unit_from_topic_match(topic_match, content_taxonomy)
                if topic_match.topic_slug and derived_unit_slug and not topic_match.ambiguous and topic_match.confidence >= 0.45:
                    match = unit_match_result_factory(
                        slug=derived_unit_slug,
                        confidence=topic_match.confidence,
                        ambiguous=topic_match.ambiguous,
                        reasons=[f"topic={topic_match.topic_slug}", *topic_match.reasons],
                    )
                else:
                    match = auto_map_entry_unit(entry, unit_index, markdown_text, topic_index)
            unit = (
                f"{match.slug} _(ambíguo)_"
                if match.slug and match.ambiguous
                else f"{match.slug} _(baixa confiança)_"
                if match.slug and match.confidence < 0.45
                else match.slug
            )
            unit_blocks = list(blocks_by_unit.get(match.slug, [])) if match.slug else []
            if match.slug and not match.ambiguous and match.confidence >= 0.45 and unit_blocks:
                probable_period, period_confidence, period_ambiguous, _ = select_probable_period_for_entry(
                    entry=entry,
                    unit=unit_by_slug.get(match.slug, {}),
                    candidate_rows=unit_blocks,
                    markdown_text=markdown_text,
                    preferred_topic_slug=preferred_topic_slug,
                )
                if probable_period and not period_ambiguous and period_confidence >= 0.5:
                    period = probable_period
            if (
                not period
                and match.slug
                and not match.ambiguous
                and match.confidence >= 0.55
                and unassigned_blocks
            ):
                probable_period, period_confidence, period_ambiguous, _ = select_probable_period_for_entry(
                    entry=entry,
                    unit=unit_by_slug.get(match.slug, {}),
                    candidate_rows=unassigned_blocks,
                    markdown_text=markdown_text,
                    preferred_topic_slug=preferred_topic_slug,
                )
                if probable_period and not period_ambiguous and period_confidence >= 0.5:
                    period = probable_period
            if not period and manual_timeline_block:
                period = str(manual_timeline_block.get("period_label", "") or "").strip()
        if not skip_timeline and not period and manual_timeline_block:
            period = str(manual_timeline_block.get("period_label", "") or "").strip()
        if skip_timeline:
            period = ""
        md_cell = file_map_markdown_cell(md_path)
        md_abs = entry_markdown_path_for_file_map(course_meta.get("_repo_root"), entry)
        sections = get_entry_sections(md_abs) if md_abs else ""
        confidence = infer_unit_confidence(
            {
                **entry,
                "_resolved_unit_slug": match.slug or unit,
                "_unit_match_confidence": match.confidence,
                "_unit_match_ambiguous": match.ambiguous,
                "_resolved_topic_slug": preferred_topic_slug,
                "_resolved_period": period,
            }
        )

        lines.append(
            f"| {i} | {title} | {category} | {entry_usage_hint(entry)} | "
            f"{entry_priority_label(entry)} | {md_cell} | {sections or ''} | "
            f"{unit or ''} | {confidence} | {period or ''} |"
        )
        if (
            raw_path
            or effective_tags
            or str(entry.get("manual_unit_slug") or "").strip()
            or str(entry.get("manual_timeline_block_id") or "").strip()
            or (md_path and md_path.replace('\\', '/').startswith("staging/"))
        ):
            details = []
            if raw_path:
                details.append(f"raw: `{raw_path}`")
            if effective_tags:
                details.append(f"tags: `{effective_tags}`")
            if str(entry.get("manual_unit_slug") or "").strip():
                details.append(f"unidade-manual: `{entry.get('manual_unit_slug')}`")
            if str(entry.get("manual_timeline_block_id") or "").strip():
                details.append(f"bloco-manual: `{entry.get('manual_timeline_block_id')}`")
            if md_path and md_path.replace('\\', '/').startswith("staging/"):
                details.append(f"markdown-base: `{md_path}`")
            lines.append(f"|  | ↳ rastreabilidade |  | {'; '.join(details)} |  |  |  |  |  |  |")

    lines += [
        "",
        "## Legenda",
        "",
        "- **Quando abrir**: atalho semântico para reduzir leitura desnecessária.",
        "- **Prioridade**: `alta` costuma merecer contexto antes dos demais.",
        "- **Seções**: principais headers `##` do markdown aprovado/curado.",
        "- **Unidade**: slug da unidade do COURSE_MAP.",
        "- **Confiança**: quão confiável está o roteamento de unidade atual.",
        "- **Período**: janela compacta da timeline associada à unidade.",
        "- **Markdown**: `A revisar` indica que o item ainda só tem extração de `staging/`, sem promoção final.",
        "- **Categoria**: tipo do arquivo; não deve ser alterada pelo tutor.",
        "",
    ]
    result = "\n".join(lines)
    return clamp_navigation_artifact(
        result,
        max_chars=12000,
        label="course/FILE_MAP.md",
    )


def low_token_course_map_md(
    course_meta: dict,
    subject_profile=None,
    *,
    build_file_map_timeline_context_from_course: Callable[[dict, object], dict],
    aggregate_unit_periods_from_blocks: Callable[[dict], dict],
    normalize_unit_slug: Callable[[str], str],
    parse_units_from_teaching_plan: Callable[[str], list],
    topic_text: Callable[[object], str],
    topic_depth: Callable[[object], int],
    build_assessment_context_from_course: Callable[[dict, object], dict],
    assessment_conflict_section_lines: Callable[[Optional[dict], bool], List[str]],
    clamp_navigation_artifact: Callable[..., str],
    logger,
) -> str:
    return render_low_token_course_map_md(
        course_meta,
        subject_profile,
        build_file_map_timeline_context_from_course=build_file_map_timeline_context_from_course,
        aggregate_unit_periods_from_blocks=aggregate_unit_periods_from_blocks,
        normalize_unit_slug=normalize_unit_slug,
        parse_units_from_teaching_plan=parse_units_from_teaching_plan,
        topic_text=topic_text,
        topic_depth=topic_depth,
        build_assessment_context_from_course=build_assessment_context_from_course,
        assessment_conflict_section_lines=assessment_conflict_section_lines,
        clamp_navigation_artifact=clamp_navigation_artifact,
        logger=logger,
    )


def low_token_course_map_md_v2(
    course_meta: dict,
    subject_profile=None,
    *,
    low_token_course_map_md_fn: Callable[[dict, object], str],
) -> str:
    return render_low_token_course_map_md_v2(
        course_meta,
        subject_profile,
        render_low_token_course_map_md_fn=low_token_course_map_md_fn,
    )


def low_token_file_map_md(
    course_meta: dict,
    manifest_entries: list,
    subject_profile=None,
    *,
    build_file_map_content_taxonomy_from_course: Callable[[dict, object, list], dict],
    build_file_map_unit_index_from_course: Callable[[dict, object], list],
    build_file_map_timeline_context_from_course: Callable[[dict, object], dict],
    iter_content_taxonomy_topics: Callable[[dict], list],
    merge_manual_and_auto_tags: Callable[..., str],
    resolve_entry_manual_timeline_block: Callable[[dict, dict], object],
    entry_markdown_text_for_file_map: Callable[[object, dict], str],
    auto_map_entry_subtopic: Callable[[dict, dict, str], object],
    resolve_entry_manual_unit_slug: Callable[[dict, list], str],
    unit_match_result_factory: Callable[..., object],
    derive_unit_from_topic_match: Callable[[object, dict], str],
    auto_map_entry_unit: Callable[[dict, list, str, list], object],
    select_probable_period_for_entry: Callable[..., tuple],
    file_map_markdown_cell: Callable[[str], str],
    entry_markdown_path_for_file_map: Callable[[object, dict], object],
    get_entry_sections: Callable[[object], str],
    infer_unit_confidence: Callable[[dict], str],
    entry_usage_hint: Callable[[dict], str],
    entry_priority_label: Callable[[dict], str],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    return render_low_token_file_map_md(
        course_meta,
        manifest_entries,
        subject_profile,
        build_file_map_content_taxonomy_from_course=build_file_map_content_taxonomy_from_course,
        build_file_map_unit_index_from_course=build_file_map_unit_index_from_course,
        build_file_map_timeline_context_from_course=build_file_map_timeline_context_from_course,
        iter_content_taxonomy_topics=iter_content_taxonomy_topics,
        merge_manual_and_auto_tags=merge_manual_and_auto_tags,
        resolve_entry_manual_timeline_block=resolve_entry_manual_timeline_block,
        entry_markdown_text_for_file_map=entry_markdown_text_for_file_map,
        auto_map_entry_subtopic=auto_map_entry_subtopic,
        resolve_entry_manual_unit_slug=resolve_entry_manual_unit_slug,
        unit_match_result_factory=unit_match_result_factory,
        derive_unit_from_topic_match=derive_unit_from_topic_match,
        auto_map_entry_unit=auto_map_entry_unit,
        select_probable_period_for_entry=select_probable_period_for_entry,
        file_map_markdown_cell=file_map_markdown_cell,
        entry_markdown_path_for_file_map=entry_markdown_path_for_file_map,
        get_entry_sections=get_entry_sections,
        infer_unit_confidence=infer_unit_confidence,
        entry_usage_hint=entry_usage_hint,
        entry_priority_label=entry_priority_label,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )


def budgeted_file_map_md(
    course_meta: dict,
    manifest_entries: list,
    subject_profile=None,
    *,
    filter_live_manifest_entries: Callable[[object, list], list],
    low_token_file_map_md_fn: Callable[[dict, list, object], str],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    return clamp_navigation_artifact(
        low_token_file_map_md_fn(
            course_meta,
            filter_live_manifest_entries(course_meta.get("_repo_root"), manifest_entries),
            subject_profile=subject_profile,
        ),
        max_chars=12000,
        label="course/FILE_MAP.md",
    )


def course_map_md(
    course_meta: dict,
    subject_profile=None,
    *,
    low_token_course_map_md_v2_fn: Callable[[dict, object], str],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    return clamp_navigation_artifact(
        low_token_course_map_md_v2_fn(course_meta, subject_profile),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def file_map_md(
    course_meta: dict,
    manifest_entries: list,
    subject_profile=None,
    *,
    budgeted_file_map_md_fn: Callable[[dict, list, object], str],
) -> str:
    return budgeted_file_map_md_fn(course_meta, manifest_entries, subject_profile)
