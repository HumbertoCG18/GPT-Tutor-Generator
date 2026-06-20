"""Task 4 TDD — measurement layer migrada p/ uuid.

T6_assignments : fixture com block_uuid nos blocos -> predict_block retorna uuid,
                 evaluate() retorna 5/5 cw0.
T6_code_block_gold: score_against_gold com true_block_id uuid e rows uuid -> 12/17 equiv.
T6_gold_tools_emit_uuid: build_card_rows e propose_rows emitem uuid em
                          candidate_block / proposed_true_block_id.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_U = {
    "bloco-01": "00000000-0000-0000-0000-000000000001",
    "bloco-02": "00000000-0000-0000-0000-000000000002",
    "bloco-03": "00000000-0000-0000-0000-000000000003",
    "bloco-04": "00000000-0000-0000-0000-000000000004",
    "bloco-05": "00000000-0000-0000-0000-000000000005",
}

GOLD_PATH = Path(__file__).parent / "fixtures" / "eval" / "assignments_gold.json"
CODE_GOLD_PATH = Path(__file__).parent / "fixtures" / "eval" / "code_block_gold.json"


# ---------------------------------------------------------------------------
# T6_assignments
# ---------------------------------------------------------------------------


def test_T6_assignments_predict_returns_uuid():
    """predict_block deve retornar uuid (nao bloco-NN) quando block_uuid esta no bloco."""
    from scripts.eval_assignments import predict_block

    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    blocks = gold["timeline"]["blocks"]
    for b in blocks:
        bid = b.get("id", "")
        assert b.get("block_uuid"), f"bloco {bid} sem block_uuid -- fixture nao migrada (3a)"

    case_date = next(c for c in gold["cases"] if c["id"] == "case-date")
    predicted, _band = predict_block(case_date, blocks)
    assert predicted == _U["bloco-01"], (
        f"esperado uuid {_U['bloco-01']}, obtido {predicted!r}"
    )


def test_T6_assignments_evaluate_5_5_cw0():
    """evaluate() com fixture migrada deve retornar 5/5 cw0."""
    from scripts.eval_assignments import evaluate

    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    for c in gold["cases"]:
        exp = c.get("expected_block_id", "")
        assert exp and not exp.startswith("bloco-"), (
            f"caso {c['id']} expected_block_id ainda e bloco-NN: {exp!r}"
        )

    report = evaluate(gold)
    assert report["correct"] == 5, f"esperado 5/5, obtido {report['correct']}/{report['total']}"
    assert report["confident_wrong"] == 0, f"confiante-errado: {report['confident_wrong']}"


# ---------------------------------------------------------------------------
# T6_code_block_gold
# ---------------------------------------------------------------------------

# Resolver predictions for the 17 entries (baseline 12/17, 5 errors):
# CORRECT: arvores(05), exemplos(04), provas(06), introducao-zip(12), tiposindutivos(13),
#          terminacao(12), invariantes(11), colecoes-arrays(13), colecoes-conjuntos(13),
#          colecoes-sequences(13), exercicios-conjuntos(13), classes-parte1(15)
# WRONG:   intro(res=06,gold=04), listas(res=06,gold=05), t1-2026-1-thy(res=05,gold=04),
#          hoare(res=11,gold=10), exemplos-zip(res=12,gold=16)
_RESOLVER_BLOCKS = {
    "arvores":              "7a5e29db-f228-4e96-bd4b-272d5b74e2ae",
    "exemplos":             "7ccdaf5e-76b8-48e5-82b5-05f80b3f054b",
    "intro":                "5599d015-10e0-4f6e-ad17-c526b903dc09",  # wrong (gold=04)
    "listas":               "5599d015-10e0-4f6e-ad17-c526b903dc09",  # wrong (gold=05)
    "provas":               "5599d015-10e0-4f6e-ad17-c526b903dc09",
    "t1-2026-1-thy":        "7a5e29db-f228-4e96-bd4b-272d5b74e2ae",  # wrong (gold=04)
    "introducao-zip":       "e3bc8a61-e729-4f25-9bc5-12b8a47151e3",
    "tiposindutivos":       "de7d1b70-fb58-4a18-ad49-d1a64c6c7684",
    "terminacao":           "e3bc8a61-e729-4f25-9bc5-12b8a47151e3",
    "hoare":                "c9f5f7cf-3477-4531-be7a-f7b68727009c",  # wrong (gold=10), cw=alta
    "invariantes":          "c9f5f7cf-3477-4531-be7a-f7b68727009c",
    "colecoes-arrays":      "de7d1b70-fb58-4a18-ad49-d1a64c6c7684",
    "colecoes-conjuntos":   "de7d1b70-fb58-4a18-ad49-d1a64c6c7684",
    "colecoes-sequences":   "de7d1b70-fb58-4a18-ad49-d1a64c6c7684",
    "exercicios-conjuntos": "de7d1b70-fb58-4a18-ad49-d1a64c6c7684",
    "classes-parte1":       "95d7c9fb-d9e3-43cd-b1fb-5fcebddb49f0",
    "exemplos-zip":         "e3bc8a61-e729-4f25-9bc5-12b8a47151e3",  # wrong (gold=16)
}
# funil: same as resolver except classes-parte1 (funil gives bloco-16)
_FUNIL_BLOCKS = {**_RESOLVER_BLOCKS,
                 "classes-parte1": "a6ac04f2-7611-4bef-b74a-54390cef4084"}


def test_T6_code_block_gold_true_block_ids_are_uuid():
    """code_block_gold.json deve ter true_block_id em formato uuid (nao bloco-NN)."""
    gold = json.loads(CODE_GOLD_PATH.read_text(encoding="utf-8"))
    for eid, entry in gold["entries"].items():
        true_block = entry.get("true_block_id", "")
        assert true_block and not true_block.startswith("bloco-"), (
            f"entrada {eid} ainda tem true_block_id=bloco-NN: {true_block!r}"
        )


def test_T6_code_block_gold_score_12_17():
    """score_against_gold com rows em uuid e gold em uuid deve reproduzir 12/17."""
    from scripts.eval_code_block_gold import score_against_gold

    gold = json.loads(CODE_GOLD_PATH.read_text(encoding="utf-8"))

    # hoare is the 1 confiante-errado (alta band, wrong answer)
    # other wrong entries have lower bands (media/baixa)
    _WRONG_LOW_BAND = {"intro", "listas", "t1-2026-1-thy", "exemplos-zip"}
    rows_by_id = {
        eid: {
            "funil_block": _FUNIL_BLOCKS[eid],
            "resolver_block": _RESOLVER_BLOCKS[eid],
            "funil_band": "alta",
            "resolver_band": "media" if eid in _WRONG_LOW_BAND else "alta",
        }
        for eid in _RESOLVER_BLOCKS
    }

    scored = score_against_gold(gold["entries"], rows_by_id)
    assert scored["resolver"]["correct"] == 12, (
        f"esperado 12/17, obtido {scored['resolver']['correct']}/17"
    )
    assert scored["resolver"]["confident_wrong"] == 1, (
        f"esperado 1 confiante-errado, obtido {scored['resolver']['confident_wrong']}"
    )


# ---------------------------------------------------------------------------
# T6_gold_tools_emit_uuid
# ---------------------------------------------------------------------------


def _make_mini_repo(tmp: Path, block_uuid: str, computed_block_id: str) -> None:
    """Cria repo sintetico minimo p/ testar gold tools."""
    course_dir = tmp / "course"
    course_dir.mkdir(parents=True)

    timeline = {"blocks": [{"id": "bloco-01", "block_uuid": block_uuid,
                             "topic_text": "Logica", "period_label": "11/03-13/03"}]}
    (course_dir / ".timeline_index.json").write_text(
        json.dumps(timeline), encoding="utf-8"
    )
    (course_dir / ".card_block_map.json").write_text("{}", encoding="utf-8")

    manifest = {"entries": [
        {"id": "mat-01", "title": "Slides aula 1",
         "category": "material-de-aula", "source_section": "Semana 1",
         "computed_block_id": computed_block_id, "computed_block_band": "alta"}
    ]}
    (tmp / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_T6_gold_tools_build_card_rows_emits_uuid():
    """build_card_rows deve emitir uuid em candidate_block quando computed_block_id e uuid."""
    from scripts.gold_by_card import build_card_rows

    uuid_val = "00000000-0000-0000-0000-000000000001"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _make_mini_repo(tmp, uuid_val, uuid_val)
        rows = build_card_rows(tmp)
    assert rows, "nenhuma linha retornada"
    cand = rows[0]["candidate_block"]
    assert cand == uuid_val, (
        f"candidate_block esperado uuid {uuid_val!r}, obtido {cand!r}"
    )


def test_T6_gold_tools_propose_rows_emits_uuid():
    """propose_rows deve emitir uuid em predicted_block_id / proposed_true_block_id."""
    from scripts.propose_gold import propose_rows

    uuid_val = "00000000-0000-0000-0000-000000000001"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _make_mini_repo(tmp, uuid_val, uuid_val)
        rows = propose_rows(tmp)
    assert rows, "nenhuma linha retornada"
    assert rows[0]["predicted_block_id"] == uuid_val, (
        f"predicted_block_id esperado {uuid_val!r}, obtido {rows[0]['predicted_block_id']!r}"
    )
    assert rows[0]["proposed_true_block_id"] == uuid_val, (
        f"proposed_true_block_id esperado {uuid_val!r}, obtido {rows[0]['proposed_true_block_id']!r}"
    )