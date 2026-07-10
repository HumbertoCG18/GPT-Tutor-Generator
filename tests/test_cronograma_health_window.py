# tests/test_cronograma_health_window.py
"""Item 8 F4 (decisão D-C): health usa a janela serializada do motor;
S2 legado só quando a entry não passou pelo motor."""
from src.builder.artifacts.cronograma_health import _candidate_refs


def test_janela_do_motor_substitui_scoring_s2():
    entry = {"temporal_block_window": ["bloco-03", "bloco-04"]}
    refs = _candidate_refs(entry, blocks=[])
    assert refs == [("bloco-03", None), ("bloco-04", None)]


def test_sem_janela_cai_no_caminho_legado():
    # blocks=[] faz o caminho legado degradar para [] (comportamento atual
    # documentado de _top_candidate_blocks) — o que importa é NÃO explodir
    # e NÃO inventar candidatos.
    assert _candidate_refs({}, blocks=[]) == []
