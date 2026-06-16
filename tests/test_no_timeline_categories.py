import importlib.util
import json
import tempfile
from pathlib import Path

from src.builder.extraction.content_taxonomy import _NO_TIMELINE_CATEGORIES

_SPEC = importlib.util.spec_from_file_location(
    "eval_assignments",
    Path(__file__).resolve().parents[1] / "scripts" / "eval_assignments.py",
)
eval_assignments = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(eval_assignments)


def test_references_en_esta_no_filtro():
    assert "references" in _NO_TIMELINE_CATEGORIES
    assert {"cronograma", "bibliografia", "referencias"} <= _NO_TIMELINE_CATEGORIES


def test_no_timeline_limpa_campos_orfaos():
    """Entry categoria 'references' com campos computed_block_* e auto_tag bloco:
    deve sair de resolve_unit_block_tags sem esses campos e sem a tag bloco:.
    Garante que residuo do bug B1 (archive-of-formal-proofs bloco-06 stale)
    nao persiste ao reprocessar o manifest.
    """
    entry = {
        "id": "afp-lib",
        "title": "Archive of Formal Proofs",
        "category": "references",
        "file_type": "url",
        "source_path": "",
        "raw_target": "",
        "source_section": "",
        "tags": "",
        "manual_tags": [],
        "auto_tags": ["bloco:bloco-06", "outro-tag"],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
        # campos orfaos do bug B1
        "computed_block_id": "bloco-06",
        "computed_block_confidence": 1.0,
        "computed_block_band": "instrucional",
        "computed_block_method": "manual",
    }

    blocks = [
        {"id": "bloco-06", "period_start": "2026-05-01", "period_end": "2026-05-31",
         "period_label": "2026-05-01..2026-05-31", "kind": "class",
         "unit_slug": "unidade-01", "unit_confidence": 0.8,
         "primary_topic_slug": "referencias", "primary_topic_label": "referencias",
         "primary_topic_confidence": 0.8, "topic_ambiguous": False,
         "topic_candidates": [], "topic_text": "referencias", "topics": [],
         "aliases": [], "card_evidence": [], "sessions": [],
         "source_rows": []},
    ]

    unit_stub = eval_assignments._stub_unit_match("", 0.0, True)

    with tempfile.TemporaryDirectory() as td:
        result = eval_assignments.resolve_unit_block_tags(
            [entry],
            course_meta={},
            subject_profile=None,
            build_file_map_unit_index_from_course_fn=lambda c, s: [],
            build_file_map_timeline_context_from_course_fn=lambda c, s: {
                "blocks_by_unit": {},
                "unassigned_blocks": [],
                "timeline_index": {"blocks": list(blocks)},
            },
            iter_content_taxonomy_topics_fn=lambda t: [],
            auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": eval_assignments._stub_topic_match(),
            auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: unit_stub,
            select_probable_period_for_entry_fn=eval_assignments._select_probable_period_for_entry,
            resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
            entry_markdown_text_for_file_map_fn=lambda root, e: "",
        )[0]

    # campos de bloco devem ter sido removidos
    assert "computed_block_id" not in result, "computed_block_id deve ser removido"
    assert "computed_block_confidence" not in result, "computed_block_confidence deve ser removido"
    assert "computed_block_band" not in result, "computed_block_band deve ser removido"
    assert "computed_block_method" not in result, "computed_block_method deve ser removido"

    # tag bloco: deve ter sido removida mas outros tags preservados
    tags = result.get("auto_tags", [])
    bloco_tags = [t for t in tags if str(t).startswith("bloco:")]
    assert bloco_tags == [], f"Tags bloco: orfas ainda presentes: {bloco_tags}"
    assert "outro-tag" in tags, "Tags nao-bloco devem ser preservadas"

    # manual_timeline_block_id NAO deve ser tocado (decisao do usuario)
    assert "manual_timeline_block_id" in result
