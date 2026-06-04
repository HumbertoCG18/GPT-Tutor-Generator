"""Harness de avaliacao da atribuicao arquivo->bloco temporal.

Roda cada material rotulado do gold set pelo SCORER REAL (via
content_taxonomy.resolve_unit_block_tags, o mesmo caminho que escreve o
manifest), le computed_block_id/computed_block_band e compara com o bloco
esperado. Reporta acuracia, matriz de confusao e calibracao de band.

Sem disco, sem Datalab, sem Gemini. Deterministico.

Uso:
    python scripts/eval_assignments.py [tests/fixtures/eval/assignments_gold.json]
    python scripts/eval_assignments.py --json   # so o dump de metricas
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.engine import _select_probable_period_for_entry  # noqa: E402
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags  # noqa: E402


def load_gold(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _stub_unit_match(slug: str, confidence: float, ambiguous: bool):
    """Duck-type do UnitMatch real (cf. tests/test_resolve_unit_block_band.py)."""
    class M:
        pass
    m = M()
    m.slug = slug
    m.confidence = float(confidence)
    m.ambiguous = bool(ambiguous)
    m.reasons = []
    return m


def _stub_topic_match():
    """Duck-type do TopicMatch real (cf. tests/test_resolve_unit_block_band.py linhas 49-59)."""
    class M:
        pass
    m = M()
    m.topic_slug = ""
    m.topic_label = ""
    m.unit_slug = ""
    m.confidence = 0.0
    m.ambiguous = True
    m.reasons = []
    return m


def _entry_from_case(case: dict) -> dict:
    return {
        "id": str(case.get("id", "")),
        "title": str(case.get("title", "")),
        "category": str(case.get("category", "material-de-aula")),
        "file_type": "pdf",
        "source_path": str(case.get("raw_target", "")),
        "raw_target": str(case.get("raw_target", "")),
        "tags": str(case.get("tags", "")),
        "manual_tags": [],
        "auto_tags": [],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
        "manual_subunit_slug": "",
    }


def predict_block(case: dict, blocks: list) -> tuple[str, str]:
    """Retorna (computed_block_id, computed_block_band) do scorer real."""
    guess = case.get("unit_guess") or {}
    unit_stub = _stub_unit_match(
        guess.get("slug", ""),
        guess.get("confidence", 0.0),
        guess.get("ambiguous", True),
    )
    markdown = str(case.get("markdown", ""))

    out = resolve_unit_block_tags(
        [_entry_from_case(case)],
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": list(blocks)},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: unit_stub,
        select_probable_period_for_entry_fn=_select_probable_period_for_entry,
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: markdown,
    )[0]
    return str(out.get("computed_block_id", "")), str(out.get("computed_block_band", ""))
