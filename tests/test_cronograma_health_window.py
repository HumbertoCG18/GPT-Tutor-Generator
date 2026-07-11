# tests/test_cronograma_health_window.py
"""Item 8 F4 (decisão D-C): health usa a janela serializada do motor;
S2 legado só quando a entry não passou pelo motor."""
from src.builder.artifacts.cronograma_health import _candidate_refs


def test_janela_do_motor_substitui_scoring_s2():
    entry = {"temporal_block_window": ["bloco-03", "bloco-04"]}
    refs = _candidate_refs(entry, blocks=[])
    assert refs == [("bloco-03", None), ("bloco-04", None)]


def test_sem_janela_delega_ao_s2_legado(monkeypatch):
    from src.builder.artifacts import cronograma_health as ch
    sentinel = [("bloco-99", 1.23)]
    called = {}

    def _fake_top(entry, blocks, n=ch._TOP_N_CANDIDATES):
        called["with"] = (entry, blocks)
        return sentinel

    monkeypatch.setattr(ch, "_top_candidate_blocks", _fake_top)
    entry = {"id": "x"}
    blocks = [{"id": "bloco-01"}]
    assert ch._candidate_refs(entry, blocks) == sentinel
    assert called["with"] == (entry, blocks)


def test_janela_do_motor_nao_e_capada_em_top_n():
    """D-C literal: a janela ordenada do motor vai INTEIRA pro health (sem cap _TOP_N_CANDIDATES do S2)."""
    entry = {"temporal_block_window": ["b1", "b2", "b3", "b4", "b5"]}
    refs = _candidate_refs(entry, blocks=[])
    assert refs == [(f"b{i}", None) for i in range(1, 6)]
