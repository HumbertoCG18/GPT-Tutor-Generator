"""Harness com golden real: gabarito dispara com seção; null = pendente, não erro."""
import importlib.util
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


def _gold():
    return {
        "card_block_map": {
            "Secao X": {"block_ids": ["bloco-02"], "source": "manual"},
        },
        "timeline": {"blocks": [
            _pblock("bloco-01", "logica predicados", "2026-03-09", "2026-03-09"),
            _pblock("bloco-02", "inducao arvores", "2026-03-30", "2026-04-01"),
        ]},
        "cases": [
            {"id": "hit-gabarito", "title": "Inducao", "category": "material-de-aula",
             "source_section_real": "Secao X",
             "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                            "ambiguous": False},
             "markdown": "inducao estrutural",
             "expected_block_id": "bloco-02", "expected_origin": "gabarito_1bloco",
             "candidates": [], "note": ""},
            {"id": "pendente-1", "title": "Outro", "category": "material-de-aula",
             "source_section_real": "Secao Y",
             "unit_guess": {"slug": "", "confidence": 0.0, "ambiguous": True},
             "markdown": "",
             "expected_block_id": None, "expected_origin": "precisa_decisao",
             "candidates": ["bloco-01", "bloco-02"], "note": ""},
            {"id": "fora-1", "title": "Plano", "category": "cronograma",
             "source_section_real": "",
             "unit_guess": {"slug": "", "confidence": 0.0, "ambiguous": True},
             "markdown": "",
             "expected_block_id": None, "expected_origin": "excluido",
             "candidates": [], "note": "categoria fora da timeline"},
        ],
    }


def test_gabarito_dispara_com_secao_e_pendente_nao_conta_erro():
    report = eval_assignments.evaluate(_gold())
    assert report["correct"] == 1            # hit-gabarito acerta via card map
    assert report["total"] == 1              # só casos com expected não-null contam
    assert report["pending"] == 1            # null = pendente
    assert report["excluded"] == 1
    assert report["wrong"] == 0


def test_breakdown_com_e_sem_secao():
    gold = _gold()
    report = eval_assignments.evaluate(gold)
    assert report["with_section"]["total"] == 1
    assert report["with_section"]["correct"] == 1
    assert report["without_section"]["total"] == 0


def test_fixture_sintetica_antiga_continua_funcionando():
    import json
    gold_path = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "eval" / "assignments_gold.json"
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    report = eval_assignments.evaluate(gold)
    assert report["total"] == 5 and report["correct"] == 5
    assert report["pending"] == 0 and report["excluded"] == 0
