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


def _contents_posicional():
    """Espelha a seção TDE real do MF: 2 grupos label→resources→assign;
    savenames colidem ('Definição.pdf' 2x), originais são únicos."""
    return [
        {"name": "TDE Trabalho Discente Efetivo", "modules": [
            {"modname": "label", "name": "Trabalho 1 (06/05/2026):"},
            {"modname": "resource", "name": "Definição",
             "contents": [{"type": "file", "filename": "t1_2026_1.pdf", "fileurl": "u"}]},
            {"modname": "resource", "name": "Arquivo .thy",
             "contents": [{"type": "file", "filename": "T1_2026_1.thy", "fileurl": "u"}]},
            {"modname": "assign", "name": "Sala de entrega",
             "dates": [{"dataid": "duedate", "timestamp": 1778122740}]},   # 2026-05-06 local
            {"modname": "label", "name": "Trabalho 2:"},
            {"modname": "resource", "name": "Definição",
             "contents": [{"type": "file", "filename": "t2_2026_1.pdf", "fileurl": "u"}]},
            {"modname": "assign", "name": "Sala de entrega",
             "dates": [{"dataid": "duedate", "timestamp": 1783393140}]},   # 2026-07-06 local
            {"modname": "resource", "name": "Gabarito",
             "contents": [{"type": "file", "filename": "gab.pdf", "fileurl": "u"}]},
        ]},
    ]


def test_file_dues_posicional_resource_herda_proximo_assign():
    from src.builder.sources.moodle_labels import extract_file_dues
    fd = extract_file_dues(_contents_posicional(), year=2026)["TDE Trabalho Discente Efetivo"]
    assert fd["t1_2026_1.pdf"] == {"due": "2026-05-06", "source": "structured"}
    assert fd["t1_2026_1.thy"] == {"due": "2026-05-06", "source": "structured"}
    assert fd["t2_2026_1.pdf"] == {"due": "2026-07-06", "source": "structured"}


def test_file_dues_savename_ambiguo_descartado_originais_ficam():
    from src.builder.sources.moodle_labels import extract_file_dues
    fd = extract_file_dues(_contents_posicional(), year=2026)["TDE Trabalho Discente Efetivo"]
    # savename 'Definição.pdf' aparece nos 2 grupos -> key ambígua NUNCA casa
    assert "definição.pdf" not in fd
    assert "t1_2026_1.pdf" in fd and "t2_2026_1.pdf" in fd


def test_file_dues_arquivo_apos_ultimo_due_fica_fora():
    from src.builder.sources.moodle_labels import extract_file_dues
    fd = extract_file_dues(_contents_posicional(), year=2026)["TDE Trabalho Discente Efetivo"]
    assert "gab.pdf" not in fd


def test_file_dues_secao_sem_modulo_com_due_fica_fora():
    from src.builder.sources.moodle_labels import extract_file_dues
    contents = [{"name": "Materiais", "modules": [
        {"modname": "resource", "name": "Aula",
         "contents": [{"type": "file", "filename": "aula01.pdf", "fileurl": "u"}]},
    ]}]
    assert extract_file_dues(contents, year=2026) == {}


def test_backfill_grava_file_dues_aditivo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    (repo / "course" / ".timeline_index.json").write_text(
        json.dumps({"blocks": []}), encoding="utf-8")
    backfill_repo_signals_consumed(
        repo, _contents_posicional(), {"name": "MF", "semester": "2026/1"}, write=True)
    card_map = json.loads(
        (repo / "course" / ".card_block_map.json").read_text(encoding="utf-8"))
    entry = card_map["TDE Trabalho Discente Efetivo"]
    assert entry["file_dues"]["t1_2026_1.pdf"]["due"] == "2026-05-06"
    assert entry["assign_dues"]                          # aditivo: não substitui
