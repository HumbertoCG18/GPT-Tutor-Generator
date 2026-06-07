"""Matcher posicional bloco->unidade: afinidade token-overlap + anchor-fill."""

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
