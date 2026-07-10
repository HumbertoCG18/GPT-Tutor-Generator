# tests/test_motor_apply.py
"""FASE 4 D9: producer do motor — ANCHOR-ONLY, pino manual intocável, TIER 0."""
import copy
import json

from src.builder.routing.motor.apply import TEMPORAL_KEYS, apply_anchor_engine


def _repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "course" / ".timeline_index.json").write_text(json.dumps({"blocks": [
        {"id": "bloco-01", "block_uuid": "u-1", "period_start": "2026-03-01",
         "sessions": [{"date": "2026-03-02", "label": "inducao estrutural"}]},
        {"id": "bloco-02", "block_uuid": "u-2", "period_start": "2026-03-08",
         "sessions": [{"date": "2026-03-09", "label": "logica de hoare"}]},
    ]}), encoding="utf-8")
    (repo / "course" / ".card_block_map.json").write_text(json.dumps(
        {"card a": {"source": "manual", "block_ids": ["bloco-01", "bloco-02"]}}),
        encoding="utf-8")
    (repo / "course" / ".lessons_index.json").write_text(json.dumps(
        {"by_date": {}}), encoding="utf-8")
    return repo


def _entries():
    return [
        {"id": "e1", "title": "inducao estrutural slides", "category": "materiais",
         "source_section": "card a", "computed_block_id": "u-1"},
        {"id": "pin", "title": "qualquer", "category": "materiais",
         "source_section": "card a", "computed_block_id": "u-1",
         "manual_timeline_block_id": "u-2",
         "temporal_block_id": "stale", "temporal_block_method": "anchor"},
        {"id": "fora", "title": "plano de ensino", "category": "bibliografia",
         "computed_block_id": "u-1"},
    ]


def test_flag_off_e_byte_identico(tmp_path):
    entries = _entries()
    before = copy.deepcopy(entries)
    out = apply_anchor_engine(entries, _repo(tmp_path), "MF", enabled=False)
    assert out == before


def test_pino_manual_nunca_recebe_temporal_e_stale_sai(tmp_path):
    entries = _entries()
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    pin = next(e for e in entries if e["id"] == "pin")
    assert pin["manual_timeline_block_id"] == "u-2"       # verdade humana intacta
    assert all(k not in pin for k in TEMPORAL_KEYS)        # temporal stale removido


def test_anchor_only_computed_intocado_e_temporal_escrito(tmp_path):
    entries = _entries()
    before = copy.deepcopy(entries)
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    for e, b in zip(entries, before):
        assert e.get("computed_block_id") == b.get("computed_block_id")
    e1 = next(e for e in entries if e["id"] == "e1")
    assert e1.get("temporal_block_id") in {"u-1", "u-2"}   # uuid, não display
    assert e1.get("temporal_block_window") == ["bloco-01", "bloco-02"]
    assert "temporal_block_band" in e1 and "temporal_block_provider" in e1


def test_fora_do_motor_nao_ganha_temporal(tmp_path):
    entries = _entries()
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    fora = next(e for e in entries if e["id"] == "fora")
    assert all(k not in fora for k in TEMPORAL_KEYS)       # bibliografia -> funil


def test_tier0_gemeos_md5_mesma_decisao(tmp_path):
    repo = _repo(tmp_path)
    twin = repo / "twin.pdf"
    twin.write_bytes(b"conteudo identico")
    entries = [
        {"id": "g1", "title": "inducao 1", "category": "materiais",
         "source_section": "card a", "source_path": "twin.pdf"},
        {"id": "g2", "title": "inducao 2", "category": "materiais",
         "source_section": "card a", "source_path": "twin.pdf"},
    ]
    apply_anchor_engine(entries, repo, "MF")
    assert entries[0].get("temporal_block_id") == entries[1].get("temporal_block_id")


def test_build_motor_voter_off_por_default(tmp_path):
    from src.builder.ops.pedagogical_regeneration import _build_motor_voter

    class _B:
        options = {}
        root_dir = tmp_path
    assert _build_motor_voter(_B()) is None


def test_build_motor_voter_on_sem_chave_degrada_none(tmp_path, monkeypatch):
    from src.builder.ops import pedagogical_regeneration as pr

    class _B:
        options = {"use_llm_voter": True}
        root_dir = tmp_path
    monkeypatch.setattr(pr.Path, "home", lambda: tmp_path)  # sem config -> sem chave
    assert pr._build_motor_voter(_B()) is None
