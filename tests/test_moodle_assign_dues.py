"""Testes do produtor assign_dues (janela-de-prazo TIER 2, spec 2026-07-22)."""
import json

from src.builder.sources.moodle_labels import extract_assign_deadlines_detailed
from src.builder.sources.moodle import backfill_repo_signals_consumed


def _contents_tde():
    return [
        {"name": "TDE Trabalho Discente Efetivo", "modules": [
            {"modname": "resource", "name": "t1_2026_1.pdf"},
            {"modname": "assign", "name": "Entrega T1",
             "dates": [{"dataid": "duedate", "timestamp": 1781103600}]},   # 2026-06-10 12:00 local
            {"modname": "assign", "name": "Entrega T2 (29/06)", "dates": []},
        ]},
        {"name": "Materiais", "modules": [
            {"modname": "resource", "name": "aula01.pdf"},
        ]},
    ]


def test_detailed_um_item_por_modulo_sem_colapsar():
    out = extract_assign_deadlines_detailed(_contents_tde(), year=2026)
    dues = out["TDE Trabalho Discente Efetivo"]
    assert len(dues) == 2
    by_name = {d["name"]: d for d in dues}
    assert by_name["Entrega T1"]["source"] == "structured"
    assert by_name["Entrega T1"]["due"] == "2026-06-10"
    assert by_name["Entrega T2 (29/06)"] == {
        "name": "Entrega T2 (29/06)", "due": "2026-06-29", "source": "named"}


def test_detailed_secao_sem_fonte_fica_fora():
    out = extract_assign_deadlines_detailed(_contents_tde(), year=2026)
    assert "Materiais" not in out


def test_detailed_named_exige_entrega_no_nome():
    contents = [{"name": "X", "modules": [
        {"modname": "forum", "name": "Avisos (10/06)"}]}]
    assert extract_assign_deadlines_detailed(contents, year=2026) == {}


def test_backfill_grava_assign_dues_aditivo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    (repo / "course" / ".timeline_index.json").write_text(
        json.dumps({"blocks": []}), encoding="utf-8")
    stats = backfill_repo_signals_consumed(
        repo, _contents_tde(), {"name": "MF", "semester": "2026/1"}, write=True)
    card_map = json.loads(
        (repo / "course" / ".card_block_map.json").read_text(encoding="utf-8"))
    entry = card_map["TDE Trabalho Discente Efetivo"]
    assert entry.get("assign_due")                       # legado intacto
    assert len(entry["assign_dues"]) == 2                # novo, sem colapso
    assert stats["card_labels"] >= 1
