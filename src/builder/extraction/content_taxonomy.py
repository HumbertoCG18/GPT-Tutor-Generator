from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

from src.builder.routing.thresholds import METHOD_CAPS, confidence_band, relative_margin_confidence, T
from src.builder.routing.file_map import reconcile_unit_with_block
from src.builder.core.semantic_config import (
    infer_semantic_profile,
    merge_semantic_profile,
    resolve_semantic_profile,
    write_internal_semantic_profile,
)
from src.builder.text.normalize import normalize_match_text, signal_token_set
from src.utils.helpers import slugify, write_text, collapse_ws as _collapse_ws
from src.builder.routing.sequence import annotate_class_ordinals
from src.builder.routing.file_map import (
    block_token_weights,
    score_entry_against_timeline_block,
    score_card_evidence_against_entry,
)
from src.builder.timeline.card_block import (
    lookup_card_blocks,
    load_card_block_map,
    lookup_card_assign_due,
)
from src.models.tag_profile import load_tag_profile, build_learned_unit_boosts
from src.builder.core.code_summarization import load_code_curation, code_curation_signal_text
from src.builder.timeline.index import timeline_block_is_administrative_only

# Categorias que não recebem auto-tags de timeline (unit/subunit/bloco).
# "references" é o equivalente EN de "referencias" (importado via Moodle EN).
_NO_TIMELINE_CATEGORIES: frozenset = frozenset(
    {"cronograma", "bibliografia", "referencias", "references"}
)

# S5 (P4): categorias de TRABALHO cuja atribuição de bloco respeita a janela
# de assign (period_start < assign_due do card). Código ("codigo-*") entra
# pela mesma janela quando o card tem assign_due (cf. resolve_unit_block_tags).
# "entregas" não existe nos dados reais medidos (12/06) — incluir se surgir.
ASSIGN_WINDOW_CATEGORIES: frozenset = frozenset({"trabalhos"})


def _normalize_match_text(text: str) -> str:
    # Fonte unica com keep="+-./": datas ("11/03/2026"), outline ("1.2.3."),
    # paths e slugs sao tokens distintivos nos dados reais (medido na Task 3
    # do P4: 51/211 textos do indice de MF divergem sem o keep).
    return normalize_match_text(text, keep="+-./")


def _strip_outline_prefix(text: str) -> str:
    cleaned = _collapse_ws(text)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", cleaned)
    return cleaned.strip()


# Exclusividade de nucleo de titulo (campanha 2 §4-U1): nucleo por TOKENS,
# nunca regex de prefixo — titulos reais variam ("Unidade NN —", "Unidade de
# Aprendizagem N —", "UNIDADE NN —") e nada garante padrao em curso futuro.
_UNIT_TITLE_GENERIC = {"unidade", "aprendizagem", "modulo", "parte", "topico"}
# _topic_support_tokens trunca tokens >=5 chars pro stem de 5 (mesma regra do
# fuzzy-match do modulo); comparar contra a palavra cheia nunca bate ("unidade"
# vira "unida" no toks, mas nao em _UNIT_TITLE_GENERIC) — TDD (Step 3) pegou:
# _unit_title_core_tokens("Unidade de Aprendizagem 5 -- ...") vazava "unida"/
# "apren" no nucleo. Pre-computa os mesmos stems pra comparar stem-a-stem.
_UNIT_TITLE_GENERIC_STEMS = {w[:5] if len(w) >= 5 else w for w in _UNIT_TITLE_GENERIC}
_TITLE_CORE_MIN_TOKENS = 2  # nucleo de 1 token ("Deadlock") nao move nada: falso-positivo > beneficio


def _unit_title_core_tokens(title: str) -> set:
    toks = _topic_support_tokens(_strip_topic_code(str(title or "")))
    return {t for t in toks if t not in _UNIT_TITLE_GENERIC_STEMS and not t.isdigit()}


def _extract_markdown_headings(raw_markdown: str, limit: int = 8) -> List[str]:
    headings: List[str] = []
    for line in (raw_markdown or "").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = _collapse_ws(match.group(1))
        if not heading:
            continue
        headings.append(heading)
        if len(headings) >= limit:
            break
    return headings


def _strip_topic_prefix(text: str) -> str:
    cleaned = _collapse_ws(text)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", cleaned)
    cleaned = re.sub(r"^(unidade|tema|topico)\s+\d+\s*[-—:]?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^(especificacao|especificação)\s+de\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" -:\t")


def _looks_like_tool_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    known_tools = list(effective_profile.get("known_tools") or [])
    normalized_tokens = set(normalized.split())
    for tool in known_tools:
        tool_norm = _normalize_match_text(tool)
        if not tool_norm:
            continue
        if len(tool_norm) < 4:
            if tool_norm in normalized_tokens:
                return True
        else:
            if tool_norm in normalized:
                return True
    return False


def _looks_like_bibliography_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    markers = list(effective_profile.get("bibliography_markers") or [])
    if any(marker in normalized for marker in markers):
        return True
    if re.search(r"\b(19|20)\d{2}\b", normalized):
        return True
    if normalized.count(" ") >= 9:
        return True
    if normalized.count("-") >= 2:
        return True
    if len(re.findall(r"\b[a-z]\b", normalized)) >= 3:
        return True
    return False


def _looks_like_goal_or_section_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    structural_headings = set(effective_profile.get("tag_structural_headings") or [])
    if normalized in structural_headings:
        return True
    if normalized.startswith(("entender ", "aprender ", "adquirir ", "julgar ", "compreender ")):
        return True
    if normalized.endswith((" software", " sistemas", " programas")) and normalized.count(" ") >= 5:
        return True
    return False


def _looks_like_weak_heading_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    if normalized in {"revisao", "exercicios", "atividade assincrona"}:
        return True
    effective_profile = merge_semantic_profile(semantic_profile)
    weak_heading_starters = tuple(effective_profile.get("weak_heading_starters") or [])
    if normalized.startswith(weak_heading_starters):
        return True
    if len(normalized.split()) > 6:
        return True
    return False


def _is_valid_topic_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    slug = slugify(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    generic_slugs = set(effective_profile.get("tag_generic_slugs") or [])
    if not slug or slug in generic_slugs:
        return False
    if len(slug) < 4:
        return False
    if _looks_like_weak_heading_candidate(text, semantic_profile=semantic_profile):
        return False
    if _looks_like_tool_candidate(text, semantic_profile=semantic_profile):
        return False
    if _looks_like_bibliography_candidate(text, semantic_profile=semantic_profile):
        return False
    if _looks_like_goal_or_section_candidate(text, semantic_profile=semantic_profile):
        return False
    return True


def _extract_topic_candidates(*sources: str, semantic_profile: Optional[dict] = None) -> List[str]:
    candidates: List[str] = []
    seen = set()
    for source in sources:
        for raw_line in (source or "").splitlines():
            line = _collapse_ws(raw_line)
            if not line:
                continue
            if line.startswith("## "):
                line = line[3:].strip()
            elif line.startswith("- [ ] "):
                line = line[6:].strip()
            elif line.startswith("- "):
                line = line[2:].strip()
            elif not re.match(r"^(?:\d+(?:\.\d+)*\.?|unidade\s+\d+)", line, flags=re.IGNORECASE):
                continue
            line = _strip_topic_prefix(line)
            slug = slugify(line)
            if not _is_valid_topic_candidate(line, semantic_profile=semantic_profile) or slug in seen:
                continue
            seen.add(slug)
            candidates.append(line)
    return candidates


def _extract_tool_candidates(*sources: str, semantic_profile: Optional[dict] = None) -> List[str]:
    found: List[str] = []
    seen = set()
    effective_profile = merge_semantic_profile(semantic_profile)
    known_tools = sorted(list(effective_profile.get("known_tools") or []), key=len, reverse=True)
    for source in sources:
        normalized = _normalize_match_text(source or "")
        for tool in known_tools:
            tool_norm = _normalize_match_text(tool)
            if tool_norm and tool_norm in normalized and tool_norm not in seen:
                seen.add(tool_norm)
                found.append(tool)
    return found


def _topic_support_tokens(text: str) -> set:
    normalized = _normalize_match_text(_strip_topic_prefix(text))
    return {
        token[:5] if len(token) >= 5 else token
        for token in normalized.split()
        if len(token) >= 4 and token not in {"sobre", "para", "com", "sem", "entre"}
    }


def _select_supported_taxonomy_topic(
    candidate: str,
    topic_records: List[dict],
    semantic_profile: Optional[dict] = None,
) -> Optional[dict]:
    candidate_norm = _normalize_match_text(candidate)
    candidate_tokens = _topic_support_tokens(candidate)
    if not candidate_norm or not candidate_tokens:
        return None

    best_topic: Optional[dict] = None
    best_score = 0.0
    for topic in topic_records or []:
        base_label = _collapse_ws(str(topic.get("label", "") or ""))
        base_norm = _normalize_match_text(base_label)
        base_tokens = _topic_support_tokens(base_label)
        if not base_norm or not base_tokens:
            continue

        overlap = candidate_tokens & base_tokens
        score = 0.0
        if candidate_norm == base_norm:
            score = 10.0
        elif candidate_norm in base_norm or base_norm in candidate_norm:
            score = 8.0
        elif len(overlap) >= 2:
            score = 5.5 + (0.4 * len(overlap))
        elif len(overlap) == 1 and 2 <= len(candidate_tokens) <= 6:
            effective_profile = merge_semantic_profile(semantic_profile)
            overlap_cues = tuple(effective_profile.get("heading_single_overlap_cues") or [])
            if any(cue in candidate_norm for cue in overlap_cues):
                score = 3.4
            elif any(
                cue in candidate_norm
                for cue in ("recursiv", "indutiv", "predicad", "isabelle", "kripke", "modelo")
            ):
                score = 2.8
        if str(topic.get("kind", "") or "") == "subtopic":
            score += 0.08
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic if best_score >= 2.8 else None


def _heading_topic_has_vocab_support(
    candidate: str,
    base_topics: List[str],
    semantic_profile: Optional[dict] = None,
) -> bool:
    candidate_norm = _normalize_match_text(candidate)
    candidate_tokens = _topic_support_tokens(candidate)
    if not candidate_tokens:
        return False
    for base_topic in base_topics or []:
        base_norm = _normalize_match_text(base_topic)
        base_tokens = _topic_support_tokens(base_topic)
        if not base_tokens:
            continue
        if candidate_norm == base_norm or candidate_norm in base_norm or base_norm in candidate_norm:
            return True
        overlap = candidate_tokens & base_tokens
        if len(overlap) < 2:
            if len(overlap) == 1 and 2 <= len(candidate_tokens) <= 4:
                effective_profile = merge_semantic_profile(semantic_profile)
                overlap_cues = tuple(effective_profile.get("heading_single_overlap_cues") or [])
                if any(cue in candidate_norm for cue in overlap_cues):
                    return True
            continue
        candidate_extra = candidate_tokens - base_tokens
        base_extra = base_tokens - candidate_tokens
        if overlap == base_tokens and len(candidate_extra) <= 1:
            return True
        if overlap == candidate_tokens and len(base_extra) <= 1:
            return True
    return False


def build_tag_catalog(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
    strong_headings: Optional[List[str]] = None,
    semantic_profile: Optional[dict] = None,
) -> dict:
    tags = set()
    heading_text = "\n".join(f"## {heading}" for heading in (strong_headings or []))
    base_topic_candidates = _extract_topic_candidates(
        teaching_plan, course_map_md, glossary_md, semantic_profile=semantic_profile
    )
    heading_topic_candidates = _extract_topic_candidates(heading_text, semantic_profile=semantic_profile)

    for raw_topic in base_topic_candidates:
        slug = slugify(raw_topic)
        if slug and _is_valid_topic_candidate(raw_topic, semantic_profile=semantic_profile):
            tags.add(f"topico:{slug}")

    for raw_topic in heading_topic_candidates:
        slug = slugify(raw_topic)
        if not slug or not _is_valid_topic_candidate(raw_topic, semantic_profile=semantic_profile):
            continue
        if base_topic_candidates and not _heading_topic_has_vocab_support(
            raw_topic, base_topic_candidates, semantic_profile=semantic_profile
        ):
            continue
        tags.add(f"topico:{slug}")

    for tool_name in _extract_tool_candidates(heading_text, semantic_profile=semantic_profile):
        slug = slugify(tool_name)
        if slug:
            tags.add(f"ferramenta:{slug}")

    return {"version": 1, "tags": sorted(tags)}


def _extract_topic_code(text: str) -> str:
    match = re.match(r"^\s*(\d+(?:\.\d+)*)(?:\.)?\s+", _collapse_ws(text))
    return match.group(1) if match else ""


def _strip_topic_code(text: str) -> str:
    cleaned = _collapse_ws(text)
    if not cleaned:
        return ""
    return re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", cleaned).strip()


def _parse_glossary_terms(glossary_md: str) -> List[Dict[str, object]]:
    terms: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None

    def _flush() -> None:
        nonlocal current
        if current and current.get("term"):
            current["synonyms"] = sorted(
                dict.fromkeys(_collapse_ws(item) for item in current.get("synonyms", []) if _collapse_ws(item))
            )
            terms.append(current)
        current = None

    for raw_line in (glossary_md or "").splitlines():
        line = _collapse_ws(raw_line)
        if not line:
            continue
        if line.startswith("## "):
            _flush()
            current = {"term": _collapse_ws(line[3:]), "unit_hint": "", "synonyms": [], "definition": ""}
            continue
        if current is None:
            continue

        match = re.match(r"^\*\*Sin[ôo]nimos aceitos:\*\*\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            values = [item.strip() for item in re.split(r"[,;/|]", match.group(1)) if item.strip()]
            current.setdefault("synonyms", []).extend(values)
            continue

        match = re.match(r"^\*\*Aparece em:\*\*\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            current["unit_hint"] = _collapse_ws(match.group(1))
            continue

        match = re.match(r"^\*\*Defini[çc][ãa]o:\*\*\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            current["definition"] = _collapse_ws(match.group(1))
            continue

    _flush()
    return terms


def _glossary_aliases_for_topic(topic_label: str, unit_title: str, glossary_terms: List[Dict[str, object]]) -> List[str]:
    topic_norm = _normalize_match_text(topic_label)
    unit_norm = _normalize_match_text(unit_title)
    aliases: List[str] = []
    seen = set()

    for term in glossary_terms or []:
        term_text = _collapse_ws(str(term.get("term", "")))
        if not term_text:
            continue
        term_norm = _normalize_match_text(term_text)
        if not term_norm:
            continue

        unit_hint = _normalize_match_text(str(term.get("unit_hint", "")))
        if unit_hint and unit_hint not in unit_norm and unit_norm not in unit_hint:
            continue

        if term_norm == topic_norm or term_norm in topic_norm or topic_norm in term_norm:
            for candidate in [term_text, *list(term.get("synonyms", []) or [])]:
                candidate_text = _collapse_ws(candidate)
                candidate_slug = slugify(candidate_text)
                if not candidate_text or not candidate_slug or candidate_slug in seen:
                    continue
                seen.add(candidate_slug)
                aliases.append(candidate_text)

    return aliases


def _dedupe_taxonomy_topics(topics: List[dict]) -> List[dict]:
    merged: Dict[str, dict] = {}
    for topic in topics or []:
        slug = _normalize_match_text(str(topic.get("slug", "") or ""))
        if not slug:
            continue
        current = merged.setdefault(
            slug,
            {
                "code": str(topic.get("code", "") or ""),
                "slug": str(topic.get("slug", "") or ""),
                "label": _collapse_ws(str(topic.get("label", "") or "")),
                "aliases": [],
                "kind": str(topic.get("kind", "") or "topic"),
                "unit_slug": str(topic.get("unit_slug", "") or ""),
            },
        )
        current["code"] = current["code"] or str(topic.get("code", "") or "")
        current["label"] = current["label"] or _collapse_ws(str(topic.get("label", "") or ""))
        current["kind"] = current["kind"] or str(topic.get("kind", "") or "topic")
        current["unit_slug"] = current["unit_slug"] or str(topic.get("unit_slug", "") or "")
        existing_aliases = {slugify(item) for item in current["aliases"]}
        for alias in topic.get("aliases", []) or []:
            alias_text = _collapse_ws(str(alias))
            alias_slug = slugify(alias_text)
            if alias_text and alias_slug and alias_slug not in existing_aliases:
                current["aliases"].append(alias_text)
                existing_aliases.add(alias_slug)
    for topic in merged.values():
        topic["aliases"] = sorted(dict.fromkeys(alias for alias in topic.get("aliases", []) if _collapse_ws(alias)))
    return list(merged.values())


def _infer_course_slug_from_units(units: List[tuple]) -> str:
    if not units:
        return ""
    first_title = _strip_outline_prefix(units[0][0] if isinstance(units[0], tuple) else str(units[0].get("title", "")))
    first_title = re.sub(r"^(unidade|tema|topico)\s+\d+\s*[-—:]?\s*", "", first_title, flags=re.IGNORECASE)
    return slugify(first_title)


def build_content_taxonomy(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
    strong_headings: Optional[List[str]] = None,
    semantic_profile: Optional[dict] = None,
    *,
    parse_units_from_teaching_plan: Callable[[str], list],
    topic_text: Callable[[object], str],
    normalize_unit_slug: Callable[[str], str],
) -> dict:
    units = parse_units_from_teaching_plan(teaching_plan or "")
    if not units and course_map_md:
        units = parse_units_from_teaching_plan(course_map_md)

    glossary_terms = _parse_glossary_terms(glossary_md or "")
    heading_sources = [heading for heading in (strong_headings or []) if _collapse_ws(heading)]

    result_units = []
    for unit_title, topics in units:
        unit_slug = normalize_unit_slug(unit_title)
        topic_records = []
        for topic in topics or []:
            current_topic_text = _collapse_ws(_strip_topic_code(topic_text(topic)))
            if not current_topic_text:
                continue
            topic_code = _extract_topic_code(topic_text(topic))
            # Filtrar noise topics: sem código numérico e que não passam na validação
            if not topic_code and not _is_valid_topic_candidate(
                current_topic_text, semantic_profile=semantic_profile
            ):
                continue
            topic_slug = slugify(current_topic_text)
            aliases = _glossary_aliases_for_topic(current_topic_text, unit_title, glossary_terms)
            topic_kind = "subtopic" if topic_code.count(".") >= 2 else "topic"
            topic_records.append(
                {
                    "code": topic_code,
                    "slug": topic_slug,
                    "label": current_topic_text,
                    "aliases": aliases,
                    "kind": topic_kind,
                    "unit_slug": unit_slug,
                }
            )

        result_units.append({"slug": unit_slug, "title": unit_title, "topics": _dedupe_taxonomy_topics(topic_records)})

    # (a) topico-preview cujo rotulo contem o nucleo do titulo de OUTRA unidade
    # migra pra unidade dona (bug MF: "1.3.1. Verificacao de Modelos" na abertura
    # da u01 empatava o DP 4x4 no bloco-16).
    title_cores = {}
    for unit in result_units:
        core = _unit_title_core_tokens(unit.get("title", ""))
        if len(core) >= _TITLE_CORE_MIN_TOKENS:
            title_cores[unit["slug"]] = core
    for unit in result_units:
        kept = []
        for topic in unit.get("topics", []) or []:
            label_toks = _topic_support_tokens(str(topic.get("label", "") or ""))
            owner = next(
                (slug for slug, core in title_cores.items()
                 if slug != unit["slug"] and core <= label_toks),
                None,
            )
            if owner is None:
                kept.append(topic)
                continue
            topic["unit_slug"] = owner
            dest = next(u for u in result_units if u["slug"] == owner)
            dest["topics"] = _dedupe_taxonomy_topics(list(dest.get("topics", []) or []) + [topic])
        unit["topics"] = kept

    for heading in heading_sources:
        heading_text = _collapse_ws(_strip_topic_code(heading))
        heading_slug = slugify(heading_text)
        if not heading_text or not heading_slug:
            continue
        best_unit: Optional[dict] = None
        best_topic: Optional[dict] = None
        best_score = 0.0
        # (b) heading que contem nucleo de titulo de unidade so enriquece a dona
        heading_toks = _topic_support_tokens(heading_text)
        owner_units = [u for u in result_units
                       if title_cores.get(u["slug"]) and title_cores[u["slug"]] <= heading_toks]
        search_units = owner_units or result_units
        for unit in search_units:
            candidate_topic = _select_supported_taxonomy_topic(
                heading_text,
                unit.get("topics", []) or [],
                semantic_profile=semantic_profile,
            )
            if not candidate_topic:
                continue
            topic_score = 0.0
            base_norm = _normalize_match_text(str(candidate_topic.get("label", "") or ""))
            heading_norm = _normalize_match_text(heading_text)
            if heading_norm == base_norm:
                topic_score = 10.0
            elif heading_norm in base_norm or base_norm in heading_norm:
                topic_score = 8.0
            else:
                overlap = _topic_support_tokens(heading_text) & _topic_support_tokens(str(candidate_topic.get("label", "") or ""))
                topic_score = 5.0 + (0.4 * len(overlap))
            if topic_score > best_score:
                best_score = topic_score
                best_unit = unit
                best_topic = candidate_topic
        if best_topic and best_unit:
            aliases = list(best_topic.get("aliases", []) or [])
            if heading_text not in aliases and slugify(heading_text) != slugify(str(best_topic.get("label", "") or "")):
                aliases.append(heading_text)
            best_topic["aliases"] = aliases
            best_unit["topics"] = _dedupe_taxonomy_topics(list(best_unit.get("topics", []) or []))

    return {"version": 1, "course_slug": _infer_course_slug_from_units(units), "units": result_units}


def write_internal_content_taxonomy(root_dir: Path, taxonomy: dict) -> None:
    write_text(root_dir / "course" / ".content_taxonomy.json", json.dumps(taxonomy, ensure_ascii=False, indent=2))


def load_internal_content_taxonomy(root_dir: Path) -> dict:
    """Lê course/.content_taxonomy.json de um repo. {} se ausente/ilegível.

    Contrapartida de write_internal_content_taxonomy. Usado como fallback quando
    a taxonomia não vem em memória (ex.: retag), evitando rodar o scorer de
    subunidade com taxonomia vazia.
    """
    try:
        path = Path(root_dir) / "course" / ".content_taxonomy.json"
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def build_unit_tag_index(taxonomy: dict) -> dict:
    """Map topico:slug tags to unit slugs from the content taxonomy.
    Returns {tag_str: {"unit_slug": str, "weight": float}} where weight reflects
    how specific the match is (3.0 = direct topic slug, 2.0 = alias)."""
    index: Dict[str, dict] = {}
    for unit in taxonomy.get("units", []) or []:
        unit_slug = str(unit.get("slug", "") or "")
        for topic in unit.get("topics", []) or []:
            topic_slug = str(topic.get("slug", "") or "")
            if topic_slug:
                index[f"topico:{topic_slug}"] = {"unit_slug": unit_slug, "weight": 3.0}
            for alias in topic.get("aliases", []) or []:
                alias_slug = slugify(str(alias))
                if alias_slug and alias_slug != topic_slug:
                    index[f"topico:{alias_slug}"] = {"unit_slug": unit_slug, "weight": 2.0}
    return index

def extract_markdown_lead_text(markdown_text: str, max_chars: int = 2600) -> str:
    stripped = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", markdown_text or "", flags=re.DOTALL)
    compact = _collapse_ws(stripped)
    if len(compact) <= max_chars:
        return compact
    clipped = compact[:max_chars]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped.strip()


_ADMIN_HEADING_NORMS = {
    "plano de ensino", "professor", "professor es", "professores",
    "sumario", "conteudo extraido", "imagens curadas", "referencias", "bibliografia",
}
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def _clean_heading_text(text: str) -> str:
    """Remove decoracao markdown (link, bold) e descarta heading administrativo
    ou linha de tabela antes de entrar no alias-enrichment (campanha 2 U1c).
    "" = descartar."""
    t = _MD_LINK_RE.sub(r"\1", str(text or ""))
    t = t.replace("**", "").replace("__", "")
    if "|" in t:  # linha de tabela nunca e heading legitimo
        return ""
    t = _collapse_ws(t)
    norm = _normalize_match_text(t)
    norm_alpha = " ".join(w for w in norm.split() if w.isalpha())
    if norm_alpha in _ADMIN_HEADING_NORMS:
        return ""
    return t


def collect_strong_heading_candidates(root_dir: Optional[Path], manifest_entries: Optional[List[dict]]) -> List[str]:
    if not root_dir:
        return []
    headings: List[str] = []
    seen = set()
    for entry in manifest_entries or []:
        for key in ["approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"]:
            rel_path = (entry.get(key) or "").replace("\\", "/")
            if not rel_path or rel_path.startswith("staging/"):
                continue
            md_path = root_dir / rel_path
            if not md_path.exists() or not md_path.is_file():
                logger.warning("heading skip: %s aponta md inexistente (%s)", entry.get("id"), rel_path)
                continue
            try:
                file_headings = _extract_markdown_headings(md_path.read_text(encoding="utf-8"))
            except Exception:
                file_headings = []
            for heading in file_headings[:4]:
                heading = _clean_heading_text(heading)
                heading_slug = slugify(heading)
                if heading_slug and heading_slug not in seen:
                    seen.add(heading_slug)
                    headings.append(heading)
            break
    return headings


def _signal_token_set(signal_text: str) -> set:
    # Logica unica em text.normalize.signal_token_set; passa o normalize LOCAL
    # (copia divergente, preserva +-./) ate a Task 3 unificar o normalize.
    return signal_token_set(signal_text, normalize=_normalize_match_text)


def _matches_tag_slug(signal_text: str, tag_slug: str) -> bool:
    normalized_signal = _normalize_match_text(signal_text)
    normalized_slug = _normalize_match_text(tag_slug.replace("-", " "))
    if not normalized_slug or not normalized_signal:
        return False
    if normalized_slug in normalized_signal:
        return True
    tokens = [tok for tok in normalized_slug.split() if len(tok) >= 4]
    if not tokens:
        return False
    signal_tokens = _signal_token_set(normalized_signal)
    direct_hits = sum(1 for token in tokens if token in signal_tokens)
    if len(tokens) == 1:
        token = tokens[0]
        if len(token) < 5:
            return False
        return direct_hits == 1
    if direct_hits == len(tokens):
        return True
    return False


def _is_exam_review_signal(signal_text: str) -> bool:
    normalized = _normalize_match_text(signal_text)
    if not normalized:
        return False

    review_cues = (
        "revisao",
        "revisao para prova",
        "revisao de prova",
        "preparacao para prova",
        "preparacao de prova",
        "preparatorio para prova",
        "simulado",
    )
    exam_cues = (
        "prova",
        "exame",
        "avaliacao",
        "teste",
        "p1",
        "p2",
        "p3",
        "pf",
        "av1",
        "av2",
        "n1",
        "n2",
    )

    has_review = any(cue in normalized for cue in review_cues)
    has_exam = any(re.search(rf"(?<![a-z0-9]){re.escape(cue)}(?![a-z0-9])", normalized) for cue in exam_cues)
    return has_review and has_exam


def infer_entry_auto_tags(entry: dict, markdown_text: str, vocabulary: dict) -> List[str]:
    title_text = _normalize_match_text(entry.get("title", ""))
    raw_target_text = _normalize_match_text(entry.get("raw_target", ""))
    markdown_headings_text = _normalize_match_text(" ".join(_extract_markdown_headings(markdown_text)))
    strong_signal_text = " ".join(part for part in [title_text, markdown_headings_text] if part)
    review_signal_text = " ".join(part for part in [title_text, raw_target_text, markdown_headings_text] if part)
    catalog_tags = list(vocabulary.get("tags") or [])
    inferred: List[str] = []
    seen = set()

    def _append(tag: str) -> None:
        if tag and tag not in seen:
            inferred.append(tag)
            seen.add(tag)

    for tag in catalog_tags:
        if not isinstance(tag, str) or ":" not in tag:
            continue
        prefix, slug = tag.split(":", 1)
        if prefix not in {"topico", "ferramenta"}:
            continue
        normalized_slug = _normalize_match_text(slug.replace("-", " "))
        slug_tokens = [tok for tok in normalized_slug.split() if len(tok) >= 4]
        if prefix == "topico" and len(slug_tokens) == 1:
            if len(slug_tokens[0]) < 5:
                continue
            strong_hits = slug_tokens[0] in _signal_token_set(strong_signal_text)
            if not strong_hits:
                continue
        if _matches_tag_slug(strong_signal_text, slug):
            _append(tag)

    category = _normalize_match_text(entry.get("category", ""))
    category_type_map = {
        "listas": "tipo:lista",
        "gabaritos": "tipo:gabarito",
        "provas": "tipo:prova",
        "material de aula": "tipo:material-base",
        "material-de-aula": "tipo:material-base",
        "codigo professor": "tipo:codigo",
        "codigo-professor": "tipo:codigo",
        "codigo aluno": "tipo:codigo",
        "codigo-aluno": "tipo:codigo",
    }
    for key, tag in category_type_map.items():
        if key in category:
            _append(tag)
            break

    if _is_exam_review_signal(review_signal_text):
        _append("uso:revisao-prova")

    return inferred[:6]


def write_tag_catalog(
    root_dir: Path,
    *,
    course_name: str,
    teaching_plan: str,
    course_map_text: str,
    glossary_text: str,
    manifest_entries: Optional[List[dict]],
) -> dict:
    catalog_path = root_dir / "course" / ".tag_catalog.json"
    strong_headings = collect_strong_heading_candidates(root_dir, manifest_entries)
    semantic_profile = resolve_semantic_profile(
        root_dir=root_dir,
        course_name=course_name,
        teaching_plan=teaching_plan,
        course_map_md=course_map_text,
        glossary_md=glossary_text,
        strong_headings=strong_headings,
    )
    write_internal_semantic_profile(
        root_dir,
        infer_semantic_profile(
            course_name=course_name,
            teaching_plan=teaching_plan,
            course_map_md=course_map_text,
            glossary_md=glossary_text,
            strong_headings=strong_headings,
        ),
    )

    existing_manual_tags: List[str] = []
    if catalog_path.exists():
        try:
            existing_payload = json.loads(catalog_path.read_text(encoding="utf-8"))
            existing_manual_tags = [
                str(tag).strip()
                for tag in (existing_payload.get("manual_tags") or [])
                if str(tag).strip()
            ]
        except Exception:
            existing_manual_tags = []

    generated = build_tag_catalog(
        teaching_plan=teaching_plan,
        course_map_md=course_map_text,
        glossary_md=glossary_text,
        strong_headings=strong_headings,
        semantic_profile=semantic_profile,
    )
    auto_tags = list(generated.get("tags") or [])
    merged: List[str] = []
    seen = set()
    for tag in existing_manual_tags + auto_tags:
        value = str(tag).strip()
        if not value or value in seen:
            continue
        merged.append(value)
        seen.add(value)

    catalog = {
        "version": 2,
        "scope": {
            "course_name": course_name or root_dir.name,
            "course_slug": slugify(course_name or root_dir.name),
        },
        "manual_tags": existing_manual_tags,
        "auto_tags": auto_tags,
        "tags": merged,
    }
    write_text(catalog_path, json.dumps(catalog, indent=2, ensure_ascii=False))
    return catalog


def refresh_manifest_auto_tags(
    root_dir: Path,
    manifest_entries: List[dict],
    vocabulary: dict,
    *,
    entry_markdown_text_for_file_map: Callable[[Path, dict], str],
) -> List[dict]:
    refreshed: List[dict] = []
    for entry in manifest_entries or []:
        item = dict(entry)
        manual_tags = item.get("manual_tags") or []
        if not manual_tags:
            raw_tags = str(item.get("tags", "") or "").strip()
            if raw_tags and ":" in raw_tags:
                manual_tags = [part.strip() for part in raw_tags.replace(",", ";").split(";") if part.strip()]
        item["manual_tags"] = list(manual_tags)
        markdown_text = entry_markdown_text_for_file_map(root_dir, item)
        item["auto_tags"] = infer_entry_auto_tags(item, markdown_text, vocabulary)
        refreshed.append(item)
    return refreshed


def _best_instructional_block_fallback(
    entry,
    markdown_text,
    instructional_blocks,
    preferred_unit_slug,
    preferred_topic_slug,
):
    """Spec "pega o melhor" (linhas 92-94/127-130): quando o scorer primario,
    com seu portao best>=0.95 (legitimo para o roteamento do FILE_MAP em
    navigation.py, mas inadequado aqui), recusa atribuir, ranqueia TODOS os
    blocos instrucionais pelo MESMO scorer real (score_entry_against_timeline_block)
    e atribui o melhor. Nada de scoring reimplementado nem numero magico: a
    confianca vem de relative_margin_confidence(best, runner_up) — a mesma
    formula de confianca de BLOCO usada pelo scorer primario (P2.1).

    Retorna (block, confidence) do vencedor, ou (None, 0.0) se nao ha bloco.
    """
    if not instructional_blocks:
        return None, 0.0
    annotate_class_ordinals(instructional_blocks)
    # import local: ciclo com entry_signals (entry_signals importa content_taxonomy no topo)
    from src.builder.extraction.entry_signals import (
        collect_entry_unit_signals,
        score_text_against_row,
    )
    signals = collect_entry_unit_signals(entry, markdown_text)
    # S2 (P4): IDF por raridade computado UMA vez por entry, sobre o conjunto
    # de candidatos deste ranking (instructional_blocks ou o recorte do card).
    # Repassa o mesmo normalize (keep="+-./") que o scorer usa neste caminho:
    # tokens com hífen/data/outline não escapam do IDF por ausência no dict.
    topic_token_weights = block_token_weights(instructional_blocks, normalize=_normalize_match_text)
    scored = [
        (
            block,
            score_entry_against_timeline_block(
                signals,
                block,
                normalize_match_text=_normalize_match_text,
                score_text_against_row=score_text_against_row,
                score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
                    s, items, normalize_match_text=_normalize_match_text
                ),
                preferred_unit_slug=preferred_unit_slug,
                preferred_topic_slug=preferred_topic_slug,
                topic_token_weights=topic_token_weights,
            ),
        )
        for block in instructional_blocks
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    best_block, best_score = scored[0]
    runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
    confidence = relative_margin_confidence(best_score, runner_up_score)
    return best_block, confidence


# Gabarito 1-bloco: a confianca e o proprio teto do metodo "card" (P2.2) —
# fonte unica em thresholds.METHOD_CAPS, sem literal duplicado.
CARD_SINGLE_CONF = METHOD_CAPS["card"]


def _card_scoped_block(entry, markdown_text, unit_index, instructional_blocks,
                       card_map, score_fallback_fn):
    """Degrau card->bloco. Retorna (block_id, confidence, method) ou ("", 0.0, "").

    method (P2.2): "card" quando o gabarito tem 1 bloco (decisão direta);
    "card+scorer" quando o scorer restrito desempatou entre 2+ blocos do card.

    score_fallback_fn(entry, markdown_text, scoped_blocks, unit_slug, topic_slug)
    -> (block, conf): o scorer real restrito aos blocos do card (sub-bloco).
    """
    card = str(entry.get("source_section") or "").strip()
    if not card:
        return "", 0.0, ""
    # lookup_card_blocks retorna uuids (lazy compat Task 2). O join e o retorno
    # casam por block_uuid (fallback id para blocos legados sem uuid).
    ids = set(lookup_card_blocks(card, card_map, unit_index, instructional_blocks))
    if not ids:
        return "", 0.0, ""

    def _block_key(b):
        return str(b.get("block_uuid") or b.get("id") or "")

    scoped = [b for b in instructional_blocks if _block_key(b) in ids]
    if not scoped:
        return "", 0.0, ""
    if len(scoped) == 1:
        return _block_key(scoped[0]), CARD_SINGLE_CONF, "card"
    block, conf = score_fallback_fn(entry, markdown_text, scoped, "", "")
    if block is None:
        return "", 0.0, ""
    return _block_key(block), float(conf), "card+scorer"


def _exam_code_from_text(text: str) -> str:
    """Código canônico da avaliação a partir de texto livre: P1/P2/PS/G2/PF/EXAME ou ""."""
    t = _normalize_match_text(text)
    if not t:
        return ""
    if re.search(r"\bps\b", t):
        return "PS"
    if re.search(r"\bg2\b", t):
        return "G2"
    if re.search(r"\bpf\b", t) or "prova final" in t:
        return "PF"
    m = re.search(r"\bp\s*(\d+)\b", t)
    if m:
        return f"P{int(m.group(1))}"
    if "exame" in t:
        return "EXAME"
    return ""


def _exam_code_from_block(block: dict) -> str:
    """Código da avaliação de um bloco (lê labels crus das sessões + period_label)."""
    parts = [str(block.get("topic_text") or ""), str(block.get("period_label") or "")]
    for sess in block.get("sessions", []) or []:
        if isinstance(sess, dict):
            parts.append(str(sess.get("label") or ""))
    return _exam_code_from_text(" ".join(parts))


def _entry_title_text(entry: dict) -> str:
    title = str(entry.get("title") or "").strip()
    if title:
        return title
    src = str(entry.get("source_path") or "")
    return src.replace("\\", "/").rsplit("/", 1)[-1]


def review_list_block_for_entry(entry: dict, blocks: list) -> str:
    """Regra léxica: arquivo cujo nome casa 'revisão' + prova (P1/P2/PS/G2/…) é
    atribuído ao bloco de REVISÃO que precede aquela prova. Retorna o id do
    bloco ou "" se o padrão não casar (cai no matching normal).

    Não agrupa revisões genéricas — exige tanto 'revis' quanto um código de
    prova no nome, evitando jogar todo material de revisão num bloco só.
    """
    title = _entry_title_text(entry)
    tnorm = _normalize_match_text(title)
    if "revis" not in tnorm:
        return ""
    code = _exam_code_from_text(title)
    if not code:
        return ""
    target_idx = None
    for i, b in enumerate(blocks):
        if str(b.get("kind") or "") == "assessment" and _exam_code_from_block(b) == code:
            target_idx = i
            break
    if target_idx is None:
        return ""
    # bloco de revisão imediatamente anterior à prova (ordem cronológica da lista)
    for j in range(target_idx - 1, -1, -1):
        if str(blocks[j].get("kind") or "") == "review":
            return str(blocks[j].get("block_uuid") or blocks[j].get("id") or "")
    return ""


def resolve_unit_block_tags(
    manifest_entries,
    course_meta,
    subject_profile=None,
    *,
    build_file_map_unit_index_from_course_fn,
    build_file_map_timeline_context_from_course_fn,
    iter_content_taxonomy_topics_fn,
    auto_map_entry_subtopic_fn,
    auto_map_entry_unit_fn,
    select_probable_period_for_entry_fn,
    resolve_entry_manual_timeline_block_fn,
    entry_markdown_text_for_file_map_fn,
):
    """Adiciona tags gerenciadas unit:, subunit: e bloco: ao auto_tags de cada
    entry no manifest.

    Thresholds:
    - unit:    confidence >= 0.65 AND nao ambiguo
    - subunit: confidence >= 0.60 AND nao ambiguo
    - bloco:   confidence >= 0.50 AND nao ambiguo (ou manual_timeline_block_id)

    manual_tags nunca sao tocadas. Tags com outros prefixos em auto_tags sao
    preservadas. manual_unit_slug e manual_timeline_block_id tem precedencia
    absoluta (confidence = 1.0).
    """
    _UNIT_PREFIX = "unit:"
    _SUBUNIT_PREFIX = "subunit:"
    _BLOCO_PREFIX = "bloco:"
    _MANAGED = (_UNIT_PREFIX, _SUBUNIT_PREFIX, _BLOCO_PREFIX)

    unit_index = build_file_map_unit_index_from_course_fn(course_meta, subject_profile)
    timeline_context = build_file_map_timeline_context_from_course_fn(
        course_meta, subject_profile
    )
    content_taxonomy = (
        course_meta.get("_content_taxonomy")
        or course_meta.get("_content_taxonomy_for_tests")
        or {}
    )
    # Dívida #5: callers como retag não passam _content_taxonomy. Sem fallback,
    # o scorer de subunidade rodaria com taxonomia vazia e LIMPARIA os slugs já
    # persistidos. Lê do disco do repo quando a versão em memória não veio.
    if not content_taxonomy and course_meta.get("_repo_root"):
        content_taxonomy = load_internal_content_taxonomy(course_meta["_repo_root"])
    topic_index = iter_content_taxonomy_topics_fn(content_taxonomy)
    blocks_by_unit = dict(timeline_context.get("blocks_by_unit") or {})
    unassigned_blocks = list(timeline_context.get("unassigned_blocks") or [])
    repo_root = course_meta.get("_repo_root")

    _tag_profile = None
    if repo_root:
        try:
            _tag_profile = load_tag_profile(Path(repo_root) / "course")
        except Exception:
            _tag_profile = None

    _card_block_map = {}
    if repo_root:
        try:
            _card_block_map = load_card_block_map(Path(repo_root) / "course")
        except Exception:
            _card_block_map = {}

    # Resumo de código curado (Gemini) como sinal de SUBUNIDADE — GERAL: zips e
    # códigos não têm .md convertido, então o scorer só via título e empatava no
    # ruído. Carregado 1x; aplicado só ao input do subunit scorer (bloco/unidade
    # mantêm o markdown original p/ não mexer no golden de bloco).
    _code_curation_entries = {}
    if repo_root:
        try:
            _code_curation_entries = load_code_curation(Path(repo_root)).get("entries", {}) or {}
        except Exception:
            _code_curation_entries = {}

    updated = []
    for entry in manifest_entries or []:
        category = _collapse_ws(str(entry.get("category") or "")).lower()
        if category in _NO_TIMELINE_CATEGORIES:
            # Categoria fora da timeline: limpa atribuicao antiga (senao um
            # manifest com historico carrega bloco orfao — caso real do B1).
            for k in ("computed_block_id", "computed_block_confidence",
                      "computed_block_band", "computed_block_method"):
                entry.pop(k, None)
            if entry.get("auto_tags"):
                entry["auto_tags"] = [t for t in entry["auto_tags"] if not str(t).startswith("bloco:")]
            updated.append(entry)
            continue

        markdown_text = entry_markdown_text_for_file_map_fn(repo_root, entry)

        # Texto de subunidade = markdown + resumo de código curado (se houver).
        # Só o caminho de SUBUNIDADE usa o texto enriquecido; bloco/unidade ficam
        # com o markdown original (preserva o golden de bloco).
        subunit_markdown_text = markdown_text
        _curation_entry = _code_curation_entries.get(str(entry.get("id") or ""))
        if _curation_entry:
            _curation_text = code_curation_signal_text(_curation_entry)
            if _curation_text:
                subunit_markdown_text = (
                    f"{markdown_text}\n\n{_curation_text}" if markdown_text else _curation_text
                )

        # --- Unit match (manual tem precedencia) ---
        manual_unit = _collapse_ws(str(entry.get("manual_unit_slug") or ""))
        if manual_unit:
            resolved_unit_slug = manual_unit
            unit_confidence = 1.0
            unit_ambiguous = False
            unit_reasons = ["manual"]
        else:
            _learned_boosts = build_learned_unit_boosts(_tag_profile, entry) if _tag_profile else {}
            unit_match = auto_map_entry_unit_fn(
                entry, unit_index, markdown_text, topic_index,
                learned_unit_boosts=_learned_boosts,
            )
            resolved_unit_slug = unit_match.slug
            unit_confidence = unit_match.confidence
            unit_ambiguous = unit_match.ambiguous
            unit_reasons = list(unit_match.reasons)

        # --- Topic/subunit match (manual tem precedencia) ---
        manual_subunit = _collapse_ws(str(entry.get("manual_subunit_slug") or ""))
        if manual_subunit:
            preferred_topic_slug = manual_subunit
            subunit_reasons = ["manual"]
            subunit_confidence = 1.0
            best_subunit_slug = manual_subunit
        else:
            topic_match = auto_map_entry_subtopic_fn(
                entry, content_taxonomy, subunit_markdown_text,
                winning_unit_slug=resolved_unit_slug,
            )
            preferred_topic_slug = ""
            subunit_reasons = list(getattr(topic_match, "reasons", []))
            subunit_confidence = float(getattr(topic_match, "confidence", 0.0))
            # Melhor candidato de subunidade (best-effort), independente do gate:
            # surfaçado no editor com a confiança, mesmo ambíguo/baixo. A tag
            # `subunit:` (roteamento) continua gated abaixo via preferred_topic_slug.
            best_subunit_slug = str(getattr(topic_match, "topic_slug", "") or "")
            if (
                topic_match.topic_slug
                and not topic_match.ambiguous
                and topic_match.confidence >= T.SUBUNIT_TAG
            ):
                preferred_topic_slug = topic_match.topic_slug

        # --- Block match: DESACOPLADO da unidade (Fase 1) ---
        # O bloco e SEMPRE computado direto, rodando o scorer sobre TODOS os
        # blocos instrucionais (nao-administrative_only). A unidade deixou de
        # ser portao (gate unit_confidence>=0.55 removido) e entra apenas como
        # BOOST aplicado DENTRO de score_entry_against_timeline_block: quando o
        # unit_slug do BLOCO casa com preferred_unit, soma +0.35 + (unit_confidence
        # DO BLOCO * 0.25) (file_map.py:716-719); caso contrario aplica -0.45.
        # Nao usa a confianca da unidade da ENTRY — so o preferred_unit_slug.
        period_block_id = ""
        block_confidence = 0.0
        # Método do funil (P2.3): manual > review_rule > card/card+scorer >
        # scorer_only. Gravado em computed_block_method para QUALQUER entry
        # com bloco (antes só o caminho de código Gemini gravava).
        block_method = ""
        manual_block = resolve_entry_manual_timeline_block_fn(entry, timeline_context)
        if manual_block:
            period_block_id = _collapse_ws(
                str(manual_block.get("block_uuid") or manual_block.get("id") or "")
            )
            block_confidence = 1.0
            block_method = "manual"
        else:
            # D2: aqui o timeline_index vem do runtime (_build_timeline_index, sem
            # _serialize) -> blocos admin (feriado/prova) presentes COM rows e SEM a
            # chave administrative_only. O key-lookup antigo era no-op e os deixava
            # vazar como candidatos do scorer material->bloco. O predicado lê rows
            # (filtra admin no runtime; inócuo no serializado, que ja removeu admin).
            instructional_blocks = [
                block
                for block in (timeline_context.get("timeline_index") or {}).get("blocks", [])
                or []
                if not timeline_block_is_administrative_only(block)
            ]
            # S5 (P4): janela de assign para trabalhos. Quando a entry é
            # trabalho (categoria) ou código cujo card tem deadline de entrega
            # (assign_due no card map), os candidatos do scorer ficam restritos
            # aos blocos com period_start < assign_due — o conteúdo foi dado
            # ANTES da entrega. O due NUNCA decide o bloco sozinho (heurística
            # "deadline 06/05 -> bloco-11" REPROVADA pelo usuário na demo de
            # 12/06: é convenção, não conteúdo); o scorer ranqueia DENTRO da
            # janela. Filtro que esvazia (nenhum bloco antes do due) não
            # restringe nada — nunca produz órfão.
            _assign_due = lookup_card_assign_due(
                entry.get("source_section"), _card_block_map)
            if _assign_due and (
                category in ASSIGN_WINDOW_CATEGORIES
                or category.startswith("codigo")
            ):
                _windowed = [
                    b for b in instructional_blocks
                    if str(b.get("period_start") or "") < _assign_due
                ]
                if _windowed:
                    instructional_blocks = _windowed
            _review_bid = review_list_block_for_entry(entry, instructional_blocks)
            if _review_bid:
                # Lista de revisão para prova (nome casa revisão + Pk) -> bloco de
                # revisão que precede a prova. Sinal léxico forte, vence card/score.
                period_block_id = _review_bid
                block_confidence = 0.95
                block_method = "review_rule"
            else:
                _card_bid, _card_conf, _card_method = _card_scoped_block(
                    entry, markdown_text, unit_index, instructional_blocks, _card_block_map,
                    lambda e, md, scoped, us, ts: _best_instructional_block_fallback(e, md, scoped, us, ts),
                )
                if _card_bid:
                    period_block_id = _card_bid
                    block_confidence = _card_conf
                    block_method = _card_method
                elif instructional_blocks:
                    # Passa a unidade resolvida (mesmo fraca) so para o boost; o
                    # scorer ranqueia TODOS os blocos instrucionais.
                    unit_obj = next(
                        (u for u in unit_index if u.get("slug") == resolved_unit_slug),
                        {"slug": resolved_unit_slug} if resolved_unit_slug else {},
                    )
                    _period, p_conf, _p_ambig, _ = select_probable_period_for_entry_fn(
                        entry=entry,
                        unit=unit_obj,
                        candidate_rows=instructional_blocks,
                        markdown_text=markdown_text,
                        preferred_topic_slug=preferred_topic_slug,
                    )
                    # O scorer primario aplica um portao best>=0.95 (file_map.py:1098;
                    # sessao-first em :1036) que e legitimo para o roteamento do
                    # FILE_MAP (navigation.py exige match forte para nao rotear lixo),
                    # mas viola a spec aqui: para atribuicao de bloco, SEMPRE se
                    # atribui o melhor candidato e a baixa confianca vira flag de
                    # revisao (band media/baixa), nunca orfao quando ha bloco
                    # (spec linhas 92-94/127-130). Quando o portao recusa (_period
                    # vazio), cai no "pega o melhor": ranqueia TODOS os blocos
                    # instrucionais pelo MESMO scorer real e atribui o top.
                    # le a flag de ambiguidade + piso trivial — palpite conf=0/ambig nunca vira atribuicao dura (investigacao 2026-08-05 §2b)
                    if _period and not _p_ambig and p_conf > 0:
                        for block in instructional_blocks:
                            if str(block.get("period_label") or "") == _period:
                                period_block_id = _collapse_ws(
                                    str(block.get("block_uuid") or block.get("id") or "")
                                )
                                # p_conf ja e relative_margin_confidence(best,
                                # runner_up) computada dentro do scorer — reusada.
                                block_confidence = float(p_conf)
                                block_method = "scorer_only"
                                break
                    else:
                        fallback_block, fallback_conf = _best_instructional_block_fallback(
                            entry,
                            markdown_text,
                            instructional_blocks,
                            resolved_unit_slug,
                            preferred_topic_slug,
                        )
                        if fallback_block is not None:
                            period_block_id = _collapse_ws(
                                str(fallback_block.get("block_uuid") or fallback_block.get("id") or "")
                            )
                            block_confidence = float(fallback_conf)
                            block_method = "scorer_only"

        # --- computed_* sao a FONTE UNICA (Fase 1) ---
        # O slug/id resolvido vive direto no entry; as tags unit:/bloco: abaixo
        # sao ESPELHO destes campos, nao um caminho de scoring paralelo.
        # block_confidence sempre vem de relative_margin_confidence(best,
        # runner_up) (P2.1) — seja a computada DENTRO de
        # select_probable_period_for_entry_fn (caminho do scorer aprovado), seja
        # a do fallback "pega o melhor", que chama a MESMA
        # thresholds.relative_margin_confidence sobre os scores do MESMO
        # scorer real. Nunca recomputado/duplicado aqui.
        computed_unit_slug = resolved_unit_slug if (not unit_ambiguous and unit_confidence >= T.UNIT_TAG) else ""
        computed_block_id = period_block_id
        # Teto por método (P2.2): léxico nunca passa do cap do seu degrau
        # (METHOD_CAPS em thresholds.py). manual=1.0 e review_rule=0.95 ficam
        # intactos; card/card+scorer/scorer_only são rebaixados quando a
        # margem relativa inflaria acima do que o método permite saber.
        computed_block_confidence = min(
            float(block_confidence), METHOD_CAPS.get(block_method, 1.0)
        )

        # Reconciliação unidade×bloco (F1): bloco manual é autoritativo; no auto,
        # bloco define a unidade só se block_confidence >= unit_confidence; senão
        # mantém a unidade forte e marca conflito. Absorve a herança (unit vazio).
        _blocks = (timeline_context.get("timeline_index") or {}).get("blocks", []) or []
        _blk = next((b for b in _blocks if str(b.get("block_uuid") or "") == computed_block_id), None)
        if _blk is None:
            _blk = next((b for b in _blocks if str(b.get("id") or "") == computed_block_id), None)
        _blk_unit = str((_blk or {}).get("unit_slug") or "").strip()
        _reconciled_unit, _unit_reason_suffix, _unit_conflict = reconcile_unit_with_block(
            computed_unit_slug=computed_unit_slug,
            unit_confidence=float(unit_confidence),
            computed_block_id=computed_block_id,
            block_confidence=float(block_confidence),
            block_unit_slug=_blk_unit,
            block_is_manual=bool(manual_block),
            has_manual_unit=bool(manual_unit),
        )
        computed_unit_slug = _reconciled_unit
        if _unit_reason_suffix:
            unit_reasons = list(unit_reasons) + _unit_reason_suffix
        # Faixa (Fase 3): so faz sentido quando ha bloco atribuido. Cutoffs
        # centralizados em thresholds.confidence_band (nada hardcoded aqui).
        # media/baixa ficam flagados pra revisao via o proprio valor da faixa.
        computed_block_band = confidence_band(computed_block_confidence) if computed_block_id else ""

        # --- Monta novo auto_tags ESPELHANDO os computed_* ---
        existing_auto = list(entry.get("auto_tags") or [])
        kept = [t for t in existing_auto if not any(t.startswith(p) for p in _MANAGED)]

        if computed_unit_slug:
            kept.append(f"{_UNIT_PREFIX}{computed_unit_slug}")

        if preferred_topic_slug:
            kept.append(f"{_SUBUNIT_PREFIX}{preferred_topic_slug}")

        if computed_block_id:
            # CRÍTICO: a tag bloco: deve continuar DISPLAY (bloco-NN), nunca uuid.
            # file_map.py:506 parseia bloco-(\d+) e QUEBRA com uuid. Resolve
            # uuid->display via índice; fallback = computed_block_id (já era legado).
            _display_id_for_tag = next(
                (
                    str(b.get("id") or "")
                    for b in _blocks
                    if str(b.get("block_uuid") or "") == computed_block_id
                ),
                computed_block_id,
            )
            kept.append(f"{_BLOCO_PREFIX}{_display_id_for_tag}")

        new_entry = dict(entry)
        new_entry["auto_tags"] = kept
        new_entry["computed_unit_slug"] = computed_unit_slug
        # computed_block_method (P2.3): ordem real de escrita —
        # regenerate_pedagogical_files roda resolve_unit_block_tags (aqui) e
        # DEPOIS attach_block_summary_fields, então no pipeline completo o
        # caminho de CÓDIGO (consensus/llm_only, do code_curation) sempre
        # reescreve por cima e vence, como hoje. O conflito real é o RETAG
        # avulso (scripts/retag_manifest.py), que chama só esta função: sem
        # proteção, apagaria um consensus/llm_only válido. Regra: preserva o
        # method de código SE a entry já o tem E o bloco recomputado é o MESMO
        # (curation continua válida); se o bloco mudou, o funil grava o seu.
        _prev_method = str(entry.get("computed_block_method") or "")
        if computed_block_id:
            if _prev_method in {"consensus", "llm_only"} and computed_block_id == str(
                entry.get("computed_block_id") or ""
            ):
                new_entry["computed_block_method"] = _prev_method
            else:
                new_entry["computed_block_method"] = block_method
                if _prev_method in {"consensus", "llm_only"}:
                    # campos do Gemini descrevem o bloco antigo — limpa; regeneração repõe
                    new_entry.pop("computed_block_match_confidence", None)
                    new_entry.pop("computed_block_rationale", None)
        else:
            new_entry.pop("computed_block_method", None)
        new_entry["computed_block_id"] = computed_block_id
        new_entry["computed_block_confidence"] = computed_block_confidence
        new_entry["computed_block_band"] = computed_block_band
        new_entry["unit_match_reasons"] = unit_reasons
        new_entry["unit_match_confidence"] = unit_confidence
        new_entry["unit_block_conflict"] = _unit_conflict
        new_entry["computed_subunit_slug"] = best_subunit_slug
        new_entry["subunit_match_reasons"] = subunit_reasons
        new_entry["subunit_match_confidence"] = subunit_confidence
        updated.append(new_entry)

    return updated
