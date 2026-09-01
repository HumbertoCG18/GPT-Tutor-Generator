"""Plano B — Task 2: batch de higiene sem mudanca de comportamento.

Um teste por item com efeito unitario testavel (spec-companion
docs/reports/2026-08-05-planob-investigacao.md §Mapa, itens 2,5,7-10,13,14,16).
A regua completa (scripts/fase*.py + pytest) e o gate de "sem regressao" —
estes testes so travam o comportamento NOVO introduzido por cada item.
"""
from __future__ import annotations

import json
from pathlib import Path


# ===== T9a — apply.py:50 — window sem "None" fantasma =====

def test_write_temporal_window_filtra_none():
    from src.builder.routing.motor.apply import _write_temporal
    from src.builder.routing.motor.contracts import AnchorDecision, MotorContext

    entry: dict = {}
    decision = AnchorDecision(block_ref="bloco-01", window=["bloco-01", None])
    ctx = MotorContext.from_artifacts(blocks=[], card_block_map={}, lessons_index={})
    _write_temporal(entry, decision, ctx)
    assert entry["temporal_block_window"] == ["bloco-01"]
    assert "None" not in entry["temporal_block_window"]


# ===== T2b — context.py:18-21 — logger.debug em artefato ilegivel =====

def test_load_repo_artifact_loga_debug_em_json_corrompido(tmp_path, caplog):
    from src.builder.routing.motor.context import load_repo_artifact

    bad = tmp_path / "bad.json"
    bad.write_text("{quebrado", encoding="utf-8")
    with caplog.at_level("DEBUG", logger="src.builder.routing.motor.context"):
        result = load_repo_artifact(tmp_path, "bad.json")
    assert result == {}
    assert any("ilegivel" in r.message for r in caplog.records)


# ===== T8 — llm_vote.py:77-82 — save_material_curation cria dir-pai =====

def test_save_material_curation_cria_diretorio_pai(tmp_path):
    from src.builder.routing.motor.llm_vote import save_material_curation

    path = tmp_path / "nested" / "dir" / "material_curation.json"
    save_material_curation(path, {"version": 1, "votes": {}})
    assert path.is_file()


# ===== T9 — llm_vote.py:131 — fold de acento/caixa em source_section =====

def _entry_llm(rid: str, title: str = "", section: str = "") -> dict:
    return {"id": rid, "title": title or rid, "source_section": section,
            "category": "material"}


def test_serie_agrupa_secao_com_acento_e_caixa_diferente():
    from src.builder.routing.motor.llm_vote import detect_same_theme_series

    entries = [
        _entry_llm("d1", title="Exercicios Dafny 1", section="Verificação"),
        _entry_llm("d2", title="Exercicios Dafny 2", section="verificacao"),
    ]
    assert detect_same_theme_series(entries) == {"d1", "d2"}


# ===== T10 — llm_vote.py:173-183 — match_window_ref strip/casefold =====

def _min_ctx():
    from src.builder.routing.motor.contracts import MotorContext

    blocks = [{"id": "bloco-13", "block_uuid": "uuid-13", "period_start": "2026-03-01"}]
    return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})


def test_match_window_ref_casefold():
    from src.builder.routing.motor.llm_vote import match_window_ref

    ctx = _min_ctx()
    assert match_window_ref("Bloco-13", ["bloco-13"], ctx) == "bloco-13"


# ===== T7a — llm_vote.py — memoize content_key por entry["id"] =====

def test_llm_voter_memoiza_content_key(tmp_path, monkeypatch):
    import src.builder.routing.motor.llm_vote as lv

    calls = {"n": 0}
    orig = lv.content_key

    def counting(entry, repo_dir):
        calls["n"] += 1
        return orig(entry, repo_dir)

    monkeypatch.setattr(lv, "content_key", counting)
    voter = lv.LlmVoter({}, cache_path=tmp_path / "c.json", repo_dir=tmp_path, client=None)
    e = {"id": "e1"}
    voter.has_vote(e)
    voter.has_vote(e)
    assert calls["n"] == 1


# ===== T16 — window_provider.py:120-121 — hoist _stems por bloco em ctx =====

def test_block_topic_stems_memoizado_por_contexto(tmp_path):
    from src.builder.routing.motor.context import build_motor_context
    from src.builder.routing.motor.window_provider import _block_topic_stems

    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "course" / ".timeline_index.json").write_text(json.dumps({"blocks": [
        {"id": "bloco-01", "period_start": "2026-03-01",
         "topic_text": "inducao estrutural", "sessions": []},
    ]}), encoding="utf-8")
    (repo / "course" / ".card_block_map.json").write_text("{}", encoding="utf-8")
    (repo / "course" / ".lessons_index.json").write_text(
        json.dumps({"by_date": {}}), encoding="utf-8")

    ctx = build_motor_context(repo)
    first = _block_topic_stems(ctx)
    assert _block_topic_stems(ctx) is first          # cache hit: mesma instancia
    ctx2 = build_motor_context(repo)
    assert _block_topic_stems(ctx2) is not first      # contexto novo = cache proprio


# ===== T14 — due_window.py — gate unico de due vazio na saida de _match_due =====

def test_match_due_gate_due_vazio(monkeypatch):
    import src.builder.routing.motor.due_window as dw
    from src.builder.routing.motor.contracts import MotorContext

    ctx = MotorContext.from_artifacts(blocks=[], card_block_map={}, lessons_index={})
    monkeypatch.setattr(
        dw, "_match_due_raw",
        lambda entry, ctx: {"name": "x", "due": "", "source": "structured"})
    assert dw._match_due({}, ctx) is None


# ===== T13 — moodle_labels.py:297-298 — extract_file_dues exige fileurl =====

def test_extract_file_dues_descarta_sem_fileurl():
    from src.builder.sources.moodle_labels import extract_file_dues

    contents = [{"name": "Card X", "modules": [
        {"name": "Doc", "modname": "resource", "contents": [
            {"type": "file", "filename": "a.pdf", "fileurl": "http://x/a.pdf"},
            {"type": "file", "filename": "b.pdf"},   # sem fileurl: placeholder Moodle
        ]},
        {"name": "Entrega", "modname": "assign",
         "dates": [{"dataid": "duedate", "timestamp": 1749513600}]},
    ]}]
    out = extract_file_dues(contents, year=2025)
    fdues = out.get("Card X", {})
    assert "a.pdf" in fdues
    assert "b.pdf" not in fdues
