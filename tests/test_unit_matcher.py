"""Matcher posicional bloco->unidade: afinidade token-overlap + anchor-fill."""

import json as _json
from pathlib import Path as _Path

from src.builder.timeline.unit_matcher import score_block_unit_affinity


def _unit(slug, title, *topic_labels):
    return {"slug": slug, "title": title,
            "topics": [{"label": t, "aliases": []} for t in topic_labels]}


def _block(*session_labels, topic_text=""):
    return {"sessions": [{"label": s} for s in session_labels], "topic_text": topic_text}


U_REC = _unit("unidade-01-conjuntos", "Conjuntos Enumeraveis e Funcoes Recursivas",
              "Conjuntos Enumeraveis", "Funcoes Recursivas Primitivas")
U_TUR = _unit("unidade-02-turing", "Turing e Computabilidade",
              "Maquinas de Turing", "Conjectura de Church-Turing")


def test_affinity_matches_recursivas_to_unit01_not_turing():
    b = _block("funcoes recursivas primitivas", topic_text="funcoes recursivas")
    assert score_block_unit_affinity(b, U_REC) > score_block_unit_affinity(b, U_TUR)


def test_affinity_matches_turing_block_to_turing_unit():
    b = _block("maquinas de turing")
    assert score_block_unit_affinity(b, U_TUR) > score_block_unit_affinity(b, U_REC)


def test_affinity_zero_when_no_overlap():
    b = _block("feriado nacional")
    assert score_block_unit_affinity(b, U_REC) == 0.0


def test_affinity_ignores_stopwords_and_short_tokens():
    # "de", "e" (stopwords) e tokens <3 nao contam
    b = _block("a de e")
    assert score_block_unit_affinity(b, U_REC) == 0.0


from src.builder.timeline.unit_matcher import assign_units_positional

UNITS3 = [
    _unit("u1", "Alfa", "alfa primeiro tema", "alfa segundo tema"),
    _unit("u2", "Beta", "beta terceiro tema", "beta quarto tema"),
    _unit("u3", "Gama", "gama quinto tema", "gama sexto tema"),
]


def test_positional_strong_anchors_in_order():
    blocks = [_block("alfa primeiro"), _block("beta terceiro"), _block("gama quinto")]
    out = assign_units_positional(blocks, UNITS3)
    assert [s for s, _ in out] == ["u1", "u2", "u3"]


def test_positional_fills_no_signal_block_between_anchors():
    # meio sem sinal -> herda a unidade da ancora anterior (u1)
    blocks = [_block("alfa primeiro"), _block("xyz sem sinal"), _block("alfa segundo")]
    out = assign_units_positional(blocks, UNITS3)
    assert [s for s, _ in out] == ["u1", "u1", "u1"]


def test_positional_weak_out_of_order_anchor_demoted():
    # bloco 2 tem leve sinal de u1 mas vem depois de u2 -> rebaixado, segue u2
    blocks = [_block("beta terceiro tema"), _block("alfa"), _block("gama quinto")]
    out = assign_units_positional(blocks, UNITS3)
    assert out[0][0] == "u2" and out[2][0] == "u3"
    assert out[1][0] == "u2"  # nao recua pra u1 (ancora fraca rebaixada)


def test_positional_empty_when_no_anchor():
    blocks = [_block("xyz"), _block("qwe")]
    assert assign_units_positional(blocks, UNITS3) == []


def test_positional_empty_when_single_unit():
    assert assign_units_positional([_block("alfa")], [UNITS3[0]]) == []


def test_positional_pre_first_anchor_blocks_get_first_unit():
    # ancora so no ultimo bloco -> blocos anteriores herdam a 1a unidade, nao a do anchor
    blocks = [_block("xyz sem sinal"), _block("gama quinto")]
    out = assign_units_positional(blocks, UNITS3)
    assert out[0][0] == "u1"   # primeira unidade (curso comeca no inicio)
    assert out[1][0] == "u3"   # ancora


def test_positional_strong_out_of_order_is_demoted_strict_monotonic():
    # mesmo com margem alta, ancora fora de ordem nao recua a sequencia
    blocks = [_block("gama quinto tema"), _block("alfa primeiro tema segundo")]
    out = assign_units_positional(blocks, UNITS3)
    assert out[0][0] == "u3"
    assert out[1][0] == "u3"   # nao recua pra u1


def test_real_metodos_hoare_unit_sane():
    import os
    from src.models.core import SubjectStore
    import src.builder.engine as engine
    base = os.environ.get("TUTOR_COURSES_DIR", r"C:\Users\Humberto\Documents\GitHub")
    repo = _Path(base) / "Metodos-Formais-Tutor"
    if not repo.exists():
        import pytest
        pytest.skip("corpus indisponivel")
    sp = SubjectStore().get("Metodos-Formais")
    cm = _json.loads((repo / "manifest.json").read_text(encoding="utf-8")).get("course", {})
    ctx = engine._build_file_map_timeline_context_from_course({**cm, "_repo_root": repo}, sp, content_taxonomy=None)
    blocks = ctx["timeline_index"]["blocks"]
    hoare = next((b for b in blocks if "hoare" in (b.get("primary_topic_label") or "").lower()), None)
    if hoare:
        assert "verificacao-de-programas" in (hoare.get("unit_slug") or "")
