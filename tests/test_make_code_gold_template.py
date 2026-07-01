"""Testes para scripts/make_code_gold_template.py — build_code_gold_rows (pura, sem IO)."""
from __future__ import annotations

import pytest

from scripts.make_code_gold_template import build_code_gold_rows

COLUMNS = [
    "id", "inferred_title", "concepts", "card",
    "funil_band", "funil_block", "funil_period",
    "gemini_primary", "gemini_period",
    "resolver_block", "resolver_period", "resolver_unit",
    "true_block_id",
]


def _make_fixtures():
    manifest_entries = [
        {
            "id": "codigo-01",
            "file_type": "code",
            "source_section": "Aula 3",
            "computed_block_band": "alta",
            "computed_block_id": "bloco-05",
        },
        {
            "id": "pdf-01",
            "file_type": "pdf",
            "source_section": "",
            "computed_block_band": "media",
            "computed_block_id": "bloco-02",
        },
    ]
    code_curation = {
        "codigo-01": {
            "summary": {
                "inferred_title": "Árvores Binárias",
                "concepts": ["árvores", "busca binária"],
                "primary_block_id": "bloco-06",
            }
        }
    }
    resolver_rows_by_id = {
        "codigo-01": {
            "resolver_block": "bloco-05",
            "resolver_unit": "unidade-arvores",
            "funil_block": "bloco-05",
            "funil_band": "alta",
        },
        "pdf-01": {
            "resolver_block": "bloco-02",
            "resolver_unit": "unidade-intro",
            "funil_block": "bloco-02",
            "funil_band": "media",
        },
    }
    period_map = {
        "bloco-02": "Semana 2",
        "bloco-05": "Semana 5",
        "bloco-06": "Semana 6",
    }
    return manifest_entries, code_curation, resolver_rows_by_id, period_map


def test_filtra_apenas_codigo_ou_zip():
    entries, curation, resolver_rows, period_map = _make_fixtures()
    rows = build_code_gold_rows(entries, curation, resolver_rows, period_map)
    assert len(rows) == 1
    assert rows[0]["id"] == "codigo-01"


def test_true_block_id_vazio():
    entries, curation, resolver_rows, period_map = _make_fixtures()
    rows = build_code_gold_rows(entries, curation, resolver_rows, period_map)
    assert rows[0]["true_block_id"] == ""


def test_concepts_juntados_com_ponto_virgula():
    entries, curation, resolver_rows, period_map = _make_fixtures()
    rows = build_code_gold_rows(entries, curation, resolver_rows, period_map)
    assert rows[0]["concepts"] == "árvores; busca binária"


def test_periodos_resolvidos_via_period_map():
    entries, curation, resolver_rows, period_map = _make_fixtures()
    rows = build_code_gold_rows(entries, curation, resolver_rows, period_map)
    r = rows[0]
    assert r["funil_period"] == "Semana 5"
    assert r["gemini_period"] == "Semana 6"
    assert r["resolver_period"] == "Semana 5"


def test_card_reflete_source_section():
    entries, curation, resolver_rows, period_map = _make_fixtures()
    rows = build_code_gold_rows(entries, curation, resolver_rows, period_map)
    assert rows[0]["card"] is True

    entries_sem_card = [dict(entries[0], source_section="")]
    rows2 = build_code_gold_rows(entries_sem_card, curation, resolver_rows, period_map)
    assert rows2[0]["card"] is False


def test_todas_as_13_colunas_na_ordem():
    entries, curation, resolver_rows, period_map = _make_fixtures()
    rows = build_code_gold_rows(entries, curation, resolver_rows, period_map)
    assert list(rows[0].keys()) == COLUMNS


def test_entry_sem_code_curation_nao_crasha():
    """Entry de código sem registro em code_curation → campos vazios, sem crash."""
    manifest_entries = [
        {
            "id": "zip-sem-curation",
            "file_type": "zip",
            "source_section": "",
            "computed_block_band": "baixa",
            "computed_block_id": "bloco-03",
        }
    ]
    code_curation: dict = {}
    resolver_rows_by_id = {
        "zip-sem-curation": {
            "resolver_block": "bloco-03",
            "resolver_unit": "",
            "funil_block": "bloco-03",
            "funil_band": "baixa",
        }
    }
    period_map = {"bloco-03": "Semana 3"}

    rows = build_code_gold_rows(manifest_entries, code_curation, resolver_rows_by_id, period_map)
    assert len(rows) == 1
    r = rows[0]
    assert r["inferred_title"] == ""
    assert r["concepts"] == ""
    assert r["gemini_primary"] == ""
    assert r["true_block_id"] == ""
    assert list(r.keys()) == COLUMNS


def test_entry_ausente_de_resolver_rows_nao_e_descartada():
    """Entry cujo id está COMPLETAMENTE AUSENTE de resolver_rows_by_id não é descartada.

    Degrada graciosamente: a linha é emitida com resolver_block/period/unit vazios.
    Garante que um entry de código nunca se torna invisível no gold por falta de linha no resolver.
    """
    manifest_entries = [
        {
            "id": "code-sem-resolver",
            "file_type": "code",
            "source_section": "Aula 1",
            "computed_block_band": "media",
            "computed_block_id": "bloco-07",
        }
    ]
    code_curation: dict = {}
    resolver_rows_by_id: dict = {}
    period_map: dict = {}

    rows = build_code_gold_rows(manifest_entries, code_curation, resolver_rows_by_id, period_map)
    assert len(rows) == 1, "entry não deve ser descartada quando ausente do resolver"
    r = rows[0]
    assert r["resolver_block"] == ""
    assert r["resolver_period"] == ""
    assert r["resolver_unit"] == ""
