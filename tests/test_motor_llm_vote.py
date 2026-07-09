"""Testes do TIER 3 (llm_vote): cache, chave de conteudo, seed, serie, voto bounded."""
from __future__ import annotations

import json
from pathlib import Path

from src.builder.routing.motor.llm_vote import (
    content_key,
    detect_same_theme_series,
    import_marco1_seed,
    load_material_curation,
    save_material_curation,
)


def _entry(rid: str, source_path: str = "", title: str = "", section: str = "",
           category: str = "material") -> dict:
    return {"id": rid, "source_path": source_path, "title": title or rid,
            "source_section": section, "category": category}


def test_content_key_gemeos_compartilham_chave(tmp_path: Path):
    (tmp_path / "a.pdf").write_bytes(b"mesmo conteudo")
    (tmp_path / "b.pdf").write_bytes(b"mesmo conteudo")
    k1 = content_key(_entry("e1", "a.pdf"), tmp_path)
    k2 = content_key(_entry("e2", "b.pdf"), tmp_path)
    assert k1 == k2 and len(k1) == 32  # md5 hex


def test_content_key_fallback_id_sem_arquivo(tmp_path: Path):
    assert content_key(_entry("orfao", "nao/existe.pdf"), tmp_path) == "orfao"
    assert content_key(_entry("semsrc"), tmp_path) == "semsrc"


def test_cache_roundtrip_e_corrompido(tmp_path: Path):
    path = tmp_path / "material_curation.json"
    assert load_material_curation(path) == {"version": 1, "votes": {}}
    data = {"version": 1, "votes": {"k": {"block_id": "bloco-01"}}}
    save_material_curation(path, data)
    assert load_material_curation(path) == data
    assert not path.with_suffix(".json.tmp").exists()  # write atomico limpa tmp
    path.write_text("{ nao e json", encoding="utf-8")
    assert load_material_curation(path) == {"version": 1, "votes": {}}


def test_import_marco1_seed_rechaveia_por_conteudo(tmp_path: Path):
    (tmp_path / "x.pdf").write_bytes(b"conteudo X")
    entries = {"rid1": _entry("rid1", "x.pdf"), "rid3": _entry("rid3")}
    seed = {
        "rid1": {"block_id": "bloco-05", "confianca": "alta",
                 "justificativa": "j", "model": "gemini-2.5-flash"},
        "rid2": {"block_id": "bloco-01"},                # entry sumiu: pula
        "rid3": {"block_id": "", "erro": "timeout"},     # voto com erro: pula
    }
    votes = import_marco1_seed(seed, entries, tmp_path)
    key = content_key(entries["rid1"], tmp_path)
    assert set(votes) == {key}
    assert votes[key]["block_id"] == "bloco-05"


def test_serie_same_theme_detecta_membros():
    entries = [
        _entry("d1", title="Exercicios Dafny 1", section="Verificacao"),
        _entry("d2", title="Exercicios Dafny 2", section="Verificacao"),
        _entry("solo", title="Prova Especial 9", section="Outra"),
    ]
    assert detect_same_theme_series(entries) == {"d1", "d2"}


def test_serie_exige_ordinais_distintos_e_card():
    entries = [
        _entry("a1", title="Lista 1", section="Card A"),
        _entry("a2", title="Lista 1", section="Card A"),      # mesmo ordinal: nao
        _entry("b1", title="Lista 1", section=""),            # sem card: nao
        _entry("b2", title="Lista 2", section=""),
    ]
    assert detect_same_theme_series(entries) == set()


def test_serie_exclui_fora_de_escopo_d6():
    entries = [
        _entry("t1", title="TDE 1", section="Verificacao", category="trabalhos"),
        _entry("t2", title="TDE 2", section="Verificacao", category="trabalhos"),
    ]
    assert detect_same_theme_series(entries) == set()
