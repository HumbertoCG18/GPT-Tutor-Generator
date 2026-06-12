"""Teto de confiança por método + computed_block_method universal (P2.2/P2.3)."""
# (mesmo _pblock/rig de tests/test_eval_golden_real.py — duplicação
#  intencional entre arquivos de teste)
import importlib.util
import json
import tempfile
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "eval_assignments",
    Path(__file__).resolve().parents[1] / "scripts" / "eval_assignments.py",
)
eval_assignments = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(eval_assignments)


def _pblock(bid, topic, start, end, unit="unidade-01-metodos-formais"):
    return {
        "id": bid, "period_start": start, "period_end": end,
        "period_label": f"{start}..{end}", "kind": "class",
        "unit_slug": unit, "unit_confidence": 0.8,
        "primary_topic_slug": topic.replace(" ", "-"),
        "primary_topic_label": topic, "primary_topic_confidence": 0.8,
        "topic_ambiguous": False, "topic_candidates": [],
        "topic_text": topic, "topics": [topic],
        "aliases": [], "card_evidence": [],
        "sessions": [{"label": topic, "date": start}],
        "source_rows": [{"date": start, "description": topic}],
    }


BLOCKS = [
    _pblock("bloco-01", "logica predicados", "2026-03-09", "2026-03-09"),
    _pblock("bloco-02", "inducao arvores", "2026-03-30", "2026-04-01"),
]


def _resolve_entry(case: dict, blocks: list, card_map: dict | None = None) -> dict:
    """resolve_unit_block_tags com os MESMOS stubs do harness (predict_block),
    mas devolvendo a entry processada inteira (method/confidence)."""
    guess = case.get("unit_guess") or {}
    unit_stub = eval_assignments._stub_unit_match(
        guess.get("slug", ""), guess.get("confidence", 0.0),
        guess.get("ambiguous", True),
    )
    markdown = str(case.get("markdown", ""))
    entry = eval_assignments._entry_from_case(case)
    for extra in (
        "manual_timeline_block_id", "computed_block_id", "computed_block_method",
        "computed_block_match_confidence", "computed_block_rationale",
    ):
        if case.get(extra):
            entry[extra] = case[extra]

    with tempfile.TemporaryDirectory() as td:
        course_meta: dict = {}
        if card_map:
            course_dir = Path(td) / "course"
            course_dir.mkdir(parents=True)
            (course_dir / ".card_block_map.json").write_text(
                json.dumps(card_map, ensure_ascii=False), encoding="utf-8")
            course_meta = {"_repo_root": td}
        return eval_assignments.resolve_unit_block_tags(
            [entry],
            course_meta=course_meta,
            subject_profile=None,
            build_file_map_unit_index_from_course_fn=lambda c, s: [],
            build_file_map_timeline_context_from_course_fn=lambda c, s: {
                "blocks_by_unit": {},
                "unassigned_blocks": [],
                "timeline_index": {"blocks": list(blocks)},
            },
            iter_content_taxonomy_topics_fn=lambda t: [],
            auto_map_entry_subtopic_fn=lambda e, t, m: eval_assignments._stub_topic_match(),
            auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: unit_stub,
            select_probable_period_for_entry_fn=eval_assignments._select_probable_period_for_entry,
            resolve_entry_manual_timeline_block_fn=lambda e, tc: next(
                (b for b in blocks
                 if str(b.get("id")) == str(e.get("manual_timeline_block_id") or "")),
                None,
            ),
            entry_markdown_text_for_file_map_fn=lambda root, e: markdown,
        )[0]


def test_method_card_com_teto():
    # entry com source_section cujo card map tem 1 bloco ->
    # computed_block_method == "card", confidence == 0.85 (CARD_SINGLE_CONF)
    out = _resolve_entry(
        {"id": "e1", "title": "Inducao", "source_section_real": "Secao X",
         "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                        "ambiguous": False},
         "markdown": "inducao estrutural"},
        BLOCKS,
        card_map={"Secao X": {"block_ids": ["bloco-02"], "source": "manual"}},
    )
    assert out["computed_block_id"] == "bloco-02"
    assert out["computed_block_method"] == "card"
    assert out["computed_block_confidence"] == 0.85


def test_method_scorer_only_com_teto():
    # entry SEM section -> method == "scorer_only", confidence <= 0.70
    out = _resolve_entry(
        {"id": "e2", "title": "Inducao em arvores", "source_section_real": "",
         "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                        "ambiguous": False},
         "markdown": "inducao estrutural arvores"},
        BLOCKS,
    )
    assert out["computed_block_id"]  # sempre atribui o melhor instrucional
    assert out["computed_block_method"] == "scorer_only"
    assert out["computed_block_confidence"] <= 0.70


def test_method_manual():
    # entry com manual_timeline_block_id -> method == "manual", confidence 1.0
    out = _resolve_entry(
        {"id": "e3", "title": "Qualquer", "source_section_real": "",
         "manual_timeline_block_id": "bloco-01",
         "unit_guess": {"slug": "", "confidence": 0.0, "ambiguous": True},
         "markdown": ""},
        BLOCKS,
    )
    assert out["computed_block_id"] == "bloco-01"
    assert out["computed_block_method"] == "manual"
    assert out["computed_block_confidence"] == 1.0


def test_method_card_scorer():
    # card map com 2 blocos (scorer desempata) -> method == "card+scorer",
    # confidence <= 0.80
    out = _resolve_entry(
        {"id": "e4", "title": "Inducao", "source_section_real": "Secao X",
         "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                        "ambiguous": False},
         "markdown": "inducao estrutural arvores"},
        BLOCKS,
        card_map={"Secao X": {"block_ids": ["bloco-01", "bloco-02"],
                              "source": "manual"}},
    )
    assert out["computed_block_id"] in {"bloco-01", "bloco-02"}
    assert out["computed_block_method"] == "card+scorer"
    assert out["computed_block_confidence"] <= 0.80


def test_method_codigo_preservado_quando_bloco_nao_muda():
    # Entry com computed_block_method de CÓDIGO (consensus, gravado por
    # pedagogical_regeneration.attach_block_summary_fields) e computed_block_id
    # que NÃO muda no retag -> o retag NÃO sobrescreve o method de código.
    out = _resolve_entry(
        {"id": "e5", "title": "Inducao em arvores", "source_section_real": "",
         "computed_block_id": "bloco-02", "computed_block_method": "consensus",
         "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                        "ambiguous": False},
         "markdown": "inducao estrutural arvores"},
        BLOCKS,
    )
    assert out["computed_block_id"] == "bloco-02"  # mesmo bloco recomputado
    assert out["computed_block_method"] == "consensus"  # código vence


def test_method_codigo_bloco_muda_limpa_campos_stale():
    # Entry com method de CÓDIGO (consensus) e bloco recomputado DIFERENTE do
    # que estava salvo → funil assume o method do funil E os campos do Gemini
    # (computed_block_match_confidence / computed_block_rationale) são removidos
    # pois descrevem o bloco antigo; regeneração posterior os reporá.
    # Usamos card_map para forçar bloco-01, enquanto a entry tinha bloco-02 salvo.
    out = _resolve_entry(
        {"id": "e6", "title": "Logica predicados", "source_section_real": "Secao Y",
         # bloco salvo = bloco-02; card_map vai forçar bloco-01 → bloco muda
         "computed_block_id": "bloco-02", "computed_block_method": "consensus",
         "computed_block_match_confidence": 0.91,
         "computed_block_rationale": "Gemini achou bloco-02 como melhor match",
         "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                        "ambiguous": False},
         "markdown": "logica predicados"},
        BLOCKS,
        card_map={"Secao Y": {"block_ids": ["bloco-01"], "source": "manual"}},
    )
    # card_map força bloco-01 → bloco mudou → method não é consensus + campos limpos
    assert out["computed_block_id"] == "bloco-01"
    assert out["computed_block_method"] != "consensus"
    assert "computed_block_match_confidence" not in out
    assert "computed_block_rationale" not in out


def test_method_caps_valores():
    from src.builder.routing.thresholds import METHOD_CAPS
    assert METHOD_CAPS == {
        "manual": 1.0,
        "review_rule": 0.95,
        "card": 0.85,
        "card+scorer": 0.80,
        "scorer_only": 0.70,
    }
