"""Fase 3a (item 2): backfill ESTRUTURAL do Moodle nos manifests dos cursos encerrados.

Fixture: `tests/fixtures/moodle/contents_excerpt.json` = excertos REAIS de core_course_get_contents
(pull de 02/09/2026, versionado em `docs/reports/_harness-2026-09-02/moodle_contents/`), campos e
valores conferidos (secao/modname/name/description/contents[].filename). Entries: ids, source_section
e moodle_label copiados dos manifests reais (MF/SO/ES2); `p58-ben-ari` e o unico id sintetico (arquivo
real do Moodle que nao esta importado no MF-Tutor).
"""
import json
from pathlib import Path

import pytest

from src.builder.sources.moodle import backfill_moodle_structure_from_api, backfill_moodle_structure_repo

FX = json.loads((Path(__file__).parent / "fixtures" / "moodle" / "contents_excerpt.json").read_text(encoding="utf-8"))

MF_ENTRIES = [
    {"id": "t1-2026-1", "source_path": r"C:\stash\metodos-formais\TDE Trabalho Discente Efetivo\t1_2026_1.pdf",
     "source_section": "TDE Trabalho Discente Efetivo", "moodle_label": "Definição"},
    {"id": "t1-2026-1-thy", "source_path": r"C:\stash\metodos-formais\TDE Trabalho Discente Efetivo\T1_2026_1.thy",
     "source_section": "TDE Trabalho Discente Efetivo", "moodle_label": "Arquivo .thy"},
    {"id": "t2-2026-1", "source_path": r"C:\stash\metodos-formais\TDE Trabalho Discente Efetivo\t2_2026_1.pdf",
     "source_section": "TDE Trabalho Discente Efetivo", "moodle_label": "Definição"},
    {"id": "p58-ben-ari", "source_path": r"C:\stash\metodos-formais\Introdução a Métodos Formais\p58-ben-ari.pdf",
     "source_section": "Introdução a Métodos Formais", "moodle_label": "Motivação: The Bug That Destroyed a Rocket"},
    {"id": "rigorous-1-2", "source_path": r"C:\stash\metodos-formais\Introdução a Métodos Formais\RigorousSoftwareDevelopment-chapters-1-2.pdf",
     "source_section": "Introdução a Métodos Formais", "moodle_label": ""},
]


def _by(out, eid):
    return out[eid]


def test_section_and_module_index_follow_moodle_position():
    out = backfill_moodle_structure_from_api(MF_ENTRIES, FX["MF"], year=2026)
    assert _by(out, "t1-2026-1")["moodle_section_index"] == 4
    assert _by(out, "t1-2026-1")["moodle_module_index"] == 2
    assert _by(out, "t1-2026-1-thy")["moodle_module_index"] == 3
    assert _by(out, "t2-2026-1")["moodle_module_index"] == 6
    assert _by(out, "p58-ben-ari")["moodle_section_index"] == 5
    assert _by(out, "p58-ben-ari")["moodle_module_index"] == 1


def test_week_label_is_nearest_dated_label_text_before_module():
    out = backfill_moodle_structure_from_api(MF_ENTRIES, FX["MF"], year=2026)
    wl = _by(out, "p58-ben-ari")["moodle_week_label"]
    assert wl.startswith("Semana 02/03/2026 a 06/03/2026:")
    assert "(02/03/2026): apresentação da disciplina" in wl   # description, nao o name truncado


def test_undated_label_does_not_anchor_nor_reset_the_run():
    out = backfill_moodle_structure_from_api(MF_ENTRIES, FX["MF"], year=2026)
    # "Material de estudo: ... mar. 2025" (sem dd/mm/aaaa) fica entre a semana 02/03 e o resource
    assert _by(out, "rigorous-1-2")["moodle_week_label"].startswith("Semana 02/03/2026 a 06/03/2026:")
    # "Trabalho 1:" (description sem data; o name "Trabalho 1 (06/05/2026):" e stale) e "Trabalho 2:" nao ancoram
    assert _by(out, "t1-2026-1")["moodle_week_label"] == ""
    assert _by(out, "t2-2026-1")["moodle_week_label"] == ""


def test_label_text_of_other_year_is_ignored():
    ents = [{"id": "microsservicos", "source_path": r"C:\stash\es2\Microsserviços\microsservicos.pdf",
             "source_section": "Microsserviços", "moodle_label": "Microsserviços"}]
    # name do label diz 2025 (stale), description diz 2026: a description manda
    assert backfill_moodle_structure_from_api(ents, FX["ES2"], year=2026)["microsservicos"]["moodle_week_label"] \
        .startswith("Semana 23/03/2026 a 27/03/2026:")
    assert backfill_moodle_structure_from_api(ents, FX["ES2"], year=2025)["microsservicos"]["moodle_week_label"] == ""


def test_matches_by_savename_derived_from_module_title():
    # SO: todo resource e "slides.pdf"; no disco o nome vem do titulo do modulo (moodle_pull)
    ents = [{"id": "1703-chamada-de-sistema",
             "source_path": r"C:\stash\so\Processo e Estruturas de Controle\17.03 Chamada de Sistema.pdf",
             "source_section": "Processo e Estruturas de Controle", "moodle_label": "17/03 Chamada de Sistema"}]
    out = backfill_moodle_structure_from_api(ents, FX["SO"], year=2026)
    assert out["1703-chamada-de-sistema"] == {"moodle_section_index": 2, "moodle_module_index": 2, "moodle_week_label": ""}


def test_falls_back_to_unique_moodle_label_in_section():
    ents = [{"id": "x", "source_path": r"C:\stash\so\Processo e Estruturas de Controle\x.pdf",
             "source_section": "Processo e Estruturas de Controle", "moodle_label": "19/03 Estruturas de Controle"}]
    assert backfill_moodle_structure_from_api(ents, FX["SO"], year=2026)["x"]["moodle_module_index"] == 3


def test_unmatched_entry_is_absent_from_result():
    ents = [{"id": "ghost", "source_path": r"C:\stash\so\Processo e Estruturas de Controle\ghost.pdf",
             "source_section": "Processo e Estruturas de Controle", "moodle_label": "Nada"},
            {"id": "url", "source_path": "https://example.org", "source_section": None, "moodle_label": None}]
    assert backfill_moodle_structure_from_api(ents, FX["SO"], year=2026) == {}


def test_file_entry_round_trip_keeps_structure_fields():
    from src.models.core import FileEntry
    d = {"source_path": "a.pdf", "file_type": "pdf", "category": "material-de-aula", "title": "a",
         "moodle_section_index": 5, "moodle_module_index": 0, "moodle_week_label": "Semana 02/03/2026 a 06/03/2026:"}
    back = FileEntry.from_dict(d).to_dict()
    assert back["moodle_section_index"] == 5 and back["moodle_module_index"] == 0
    assert back["moodle_week_label"] == d["moodle_week_label"]
    bare = FileEntry.from_dict({"source_path": "b.pdf", "file_type": "pdf", "category": "x", "title": "b"}).to_dict()
    assert "moodle_section_index" not in bare and "moodle_week_label" not in bare


def _repo(tmp_path, contents, year_iso="2026-03-03"):
    (tmp_path / "raw" / "moodle").mkdir(parents=True)
    (tmp_path / "raw" / "moodle" / "contents.json").write_text(json.dumps(contents, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "course").mkdir()
    (tmp_path / "course" / ".timeline_index.json").write_text(
        json.dumps({"blocks": [{"id": "bloco-01", "period_start": year_iso, "sessions": []}]}), encoding="utf-8")
    return tmp_path


def test_repo_backfill_writes_fields_in_place_and_clears_stale(tmp_path):
    repo = _repo(tmp_path, FX["MF"])
    ents = [dict(e) for e in MF_ENTRIES]
    ents.append({"id": "stale", "source_path": r"C:\x\stale.pdf", "source_section": "Sumida",
                 "moodle_section_index": 9, "moodle_module_index": 9, "moodle_week_label": "velho"})
    res = backfill_moodle_structure_repo(repo, ents)
    assert res["matched"] == 5 and res["unmatched"] == ["stale"]
    assert ents[3]["moodle_week_label"].startswith("Semana 02/03/2026")
    assert "moodle_section_index" not in ents[-1] and "moodle_week_label" not in ents[-1]


def test_repo_backfill_is_noop_without_raw_contents(tmp_path):
    ents = [dict(e) for e in MF_ENTRIES]
    assert backfill_moodle_structure_repo(tmp_path, ents) is None
    assert ents == MF_ENTRIES


def test_repo_backfill_year_comes_from_timeline(tmp_path):
    ents = [{"id": "microsservicos", "source_path": r"C:\stash\es2\Microsserviços\microsservicos.pdf",
             "source_section": "Microsserviços", "moodle_label": "Microsserviços"}]
    backfill_moodle_structure_repo(_repo(tmp_path, FX["ES2"], year_iso="2025-08-18"), ents)
    assert ents[0]["moodle_week_label"] == ""   # texto e de 2026, curso de 2025 -> ruido


def test_regeneration_layer_calls_repo_backfill(tmp_path):
    from types import SimpleNamespace
    from src.builder.ops.pedagogical_regeneration import _run_moodle_structure_backfill
    repo = _repo(tmp_path, FX["MF"])
    ents = [dict(e) for e in MF_ENTRIES]
    _run_moodle_structure_backfill(SimpleNamespace(root_dir=repo), ents)
    assert ents[0]["moodle_section_index"] == 4
