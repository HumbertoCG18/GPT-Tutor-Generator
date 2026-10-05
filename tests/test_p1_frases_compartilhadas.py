import pytest

from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.timeline.index import (
    TopicMatchResult,
    _divisores_de_frase,
    _normalize_match_text,
    _score_entry_against_taxonomy_topic,
    slugify,
)

# P1 (#90): no seletor da subunidade, cada acerto de frase vale peso x fator / F_top, onde F_top = nº de tópicos
# concorrentes com alguma chave que casa a frase. Desligado por padrão na função; a produção liga pelo callback da
# fachada (facade/file_map.py). Contrato com valores conferidos no pontuador real:
# docs/reports/2026-10-01-cru05-cru03/fase1-p1-desenho-congelado-v2.md (worktree cru05).

_CAMPOS = ("title_text", "markdown_headings_text", "markdown_lead_text", "markdown_text", "category_text",
           "manual_tags_text", "auto_tags_text", "legacy_tags_text", "raw_text")


def _topico(label, aliases=(), short=()):
    return {"unit_slug": "u1", "topic_slug": slugify(label), "topic_label": label, "kind": "topic",
            "aliases": list(aliases), "generic_tokens": ["zzzz"], "short_vocab": list(short)}


def _sinais(**campos):
    s = dict.fromkeys(_CAMPOS, "")
    s.update({k: _normalize_match_text(v) for k, v in campos.items()})
    return s


def _pontua(topicos, sinais, p1):
    div = _divisores_de_frase(topicos) if p1 else None
    return [_score_entry_against_taxonomy_topic(sinais, t, divisores_frase=div) for t in topicos]


def _seleciona(topicos, sinais, p1):
    return auto_map_entry_subtopic(
        {"id": "m", "title": ""}, topicos, "",
        collect_entry_unit_signals=lambda entry, md: sinais,
        iter_content_taxonomy_topics=lambda tax: list(tax),
        score_entry_against_taxonomy_topic=_score_entry_against_taxonomy_topic,
        topic_match_result_factory=TopicMatchResult,
        divisores_de_frase=_divisores_de_frase if p1 else None,
    )


_U1 = [_topico("Máquinas de Turing"), _topico("Variações de Máquinas de Turing"),
       _topico("Máquinas de Turing Universais")]


def test_divisores_contam_os_topicos_concorrentes_que_contem_a_frase():
    assert _divisores_de_frase(_U1) == {"maquinas de turing": 3, "variacoes de maquinas de turing": 1,
                                        "maquinas de turing universais": 1}


def test_e1_frase_compartilhada_sozinha_ainda_decide_sem_penalidade():
    s = _sinais(title_text="Máquinas de Turing")
    assert _pontua(_U1, s, False) == pytest.approx([5.64, 0.9072, 0.9072])
    assert _pontua(_U1, s, True) == pytest.approx([3.8 / 3 + 1.84, 0.9072, 0.9072])   # acerto exato preservado (E5)
    for p1 in (False, True):
        r = _seleciona(_U1, s, p1)
        assert (r.topic_slug, r.ambiguous) == ("maquinas-de-turing", False)


def test_e2_frase_especifica_deixa_de_perder_para_a_compartilhada_contida_nela():
    s = _sinais(title_text="Máquinas de Turing", markdown_headings_text="Variações de Máquinas de Turing")
    assert _pontua(_U1, s, False) == pytest.approx([10.04, 6.46, 0.9072])
    assert _pontua(_U1, s, True) == pytest.approx([8.2 / 3 + 1.84, 6.46, 0.9072])
    assert _seleciona(_U1, s, False).topic_slug == "maquinas-de-turing"
    r = _seleciona(_U1, s, True)
    assert r.topic_slug == "variacoes-de-maquinas-de-turing"
    assert r.confidence == pytest.approx((6.46 - (8.2 / 3 + 1.84)) / 6.46)


@pytest.mark.parametrize("campos", [{"title_text": "Memória Virtual"}, {"markdown_headings_text": "Paginação e Swapping"},
                                    {"markdown_text": "memoria virtual paginacao swapping"}])
def test_e3_sem_frase_compartilhada_e_identico(campos):
    u = [_topico("Swapping"), _topico("Memória Virtual"), _topico("Paginação")]
    s = _sinais(**campos)
    assert _pontua(u, s, True) == _pontua(u, s, False)


def test_e4_palavra_unica_compartilhada():
    u = [_topico("Escalonamento"), _topico("Algoritmos de Escalonamento")]
    assert _divisores_de_frase(u) == {"escalonamento": 2, "algoritmos de escalonamento": 1}
    s = _sinais(markdown_headings_text="Escalonamento")
    assert _pontua(u, s, False) == pytest.approx([5.3, 0.1224])
    assert _pontua(u, s, True) == pytest.approx([4.4 / 2 + 0.9, 0.1224])
    assert _seleciona(u, s, True).topic_slug == "escalonamento"


def test_e4b_palavra_unica_curta_tem_divisor_zero_e_nunca_acerta():
    u = [_topico("CPU", short=["cpu"]), _topico("Memória", short=["cpu"])]
    assert _divisores_de_frase(u)["cpu"] == 0
    s = _sinais(markdown_headings_text="CPU")
    assert _pontua(u, s, True) == _pontua(u, s, False) == pytest.approx([0.9 * 0.72 * 0.68, 0.0])


def test_e6_desligado_por_padrao_e_identico():
    s = _sinais(title_text="Máquinas de Turing", markdown_headings_text="Variações de Máquinas de Turing")
    for t in _U1:
        for stem in (False, True):
            assert _score_entry_against_taxonomy_topic(s, t, stem_fallback=stem) == \
                _score_entry_against_taxonomy_topic(s, t, stem_fallback=stem, divisores_frase=None)
    padrao = auto_map_entry_subtopic(
        {"id": "m", "title": ""}, _U1, "", collect_entry_unit_signals=lambda e, md: s,
        iter_content_taxonomy_topics=lambda tax: list(tax),
        score_entry_against_taxonomy_topic=_score_entry_against_taxonomy_topic,
        topic_match_result_factory=TopicMatchResult)
    assert padrao == _seleciona(_U1, s, False)


def test_e7_divisores_vem_da_taxonomia_de_cada_chamada():
    t1 = [_topico("Swapping"), _topico("Paginação")]
    t2 = [_topico("Swapping", aliases=["Paginação sob demanda"]), _topico("Paginação")]
    s = _sinais(markdown_headings_text="Paginação")
    assert _divisores_de_frase(t1)["paginacao"] == 1
    assert _divisores_de_frase(t2)["paginacao"] == 2
    assert _pontua(t1, s, True) == pytest.approx([0.0, 5.3])
    assert _pontua(t2, s, False) == pytest.approx([0.1224, 5.3])
    assert _pontua(t2, s, True) == pytest.approx([0.1224, 4.4 / 2 + 0.9])
    r1, r2 = _seleciona(t1, s, True), _seleciona(t2, s, True)   # em sequência: não reaproveita divisores de T1
    assert (r1.topic_slug, r1.confidence) == ("paginacao", pytest.approx(1.0))
    assert (r2.topic_slug, r2.confidence) == ("paginacao", pytest.approx((3.1 - 0.1224) / 3.1))

# --- Reforço pós-revisão (job-30, 02/10): lacunas de cobertura, sem mudar produto nem contrato ------------------------

def test_varias_chaves_do_mesmo_topico_contam_o_topico_uma_vez():
    # rótulo + alias distinto contendo a frase + alias repetido + alias que normaliza para vazio + slug igual ao rótulo
    a = _topico("Máquinas de Turing", aliases=["Máquinas de Turing MT", "Máquinas de Turing MT", "!!!"])
    u = [a, _topico("Variações de Máquinas de Turing")]
    assert _divisores_de_frase(u) == {"maquinas de turing": 2, "maquinas de turing mt": 1,
                                      "variacoes de maquinas de turing": 1}
    s = _sinais(title_text="Máquinas de Turing")
    assert _pontua(u, s, True)[0] == pytest.approx(3.8 / 2 + 1.84)   # dividido por 2 tópicos, não por 3 chaves


def test_divisores_respeitam_o_filtro_da_unidade_vencedora():
    def em(topico, unidade):
        return {**topico, "unit_slug": unidade}
    tax = [em(_U1[0], "u1"), em(_U1[1], "u1"), em(_U1[2], "u2")]
    s = _sinais(title_text="Máquinas de Turing")
    comuns = dict(collect_entry_unit_signals=lambda entry, md: s, iter_content_taxonomy_topics=lambda t: list(t),
                  score_entry_against_taxonomy_topic=_score_entry_against_taxonomy_topic,
                  topic_match_result_factory=TopicMatchResult, divisores_de_frase=_divisores_de_frase)
    r_u1 = auto_map_entry_subtopic({"id": "m", "title": ""}, tax, "", winning_unit_slug="u1", **comuns)
    r_todas = auto_map_entry_subtopic({"id": "m", "title": ""}, tax, "", **comuns)
    a_u1, a_todas = 3.8 / 2 + 1.84, 3.8 / 3 + 1.84   # F_top 2 só entre os concorrentes de u1; 3 sem filtro
    assert r_u1.topic_slug == r_todas.topic_slug == "maquinas-de-turing"
    assert r_u1.confidence == pytest.approx((a_u1 - 0.9072) / a_u1)
    assert r_todas.confidence == pytest.approx((a_todas - 0.9072) / a_todas)


def test_rotas_de_unidade_e_bloco_nao_recebem_divisores_com_o_p1_ligado(monkeypatch):
    from src.builder.routing.file_map import auto_map_entry_unit
    from src.builder.timeline import index as IX

    s = _sinais(title_text="Máquinas de Turing")
    assert _seleciona(_U1, s, True).topic_slug == "maquinas-de-turing"   # seletor da subunidade ligado no mesmo processo
    chamadas = []
    real = IX._score_entry_against_taxonomy_topic

    def espiao(signals, topic, **kw):
        chamadas.append(kw)
        return real(signals, topic, **kw)

    auto_map_entry_unit(
        {"id": "m", "title": ""}, [{"slug": "u1", "title": "Unidade Um"}], "", topic_index=_U1,
        build_file_map_unit_index=lambda units: [{"slug": "u1", "title": "Unidade Um"}],
        collect_entry_unit_signals=lambda entry, md: s,
        score_entry_against_unit=lambda signals, unit, unit_tag_boost=0.0: 0.0,
        normalize_unit_slug=lambda x: x, score_entry_against_taxonomy_topic=espiao)
    assert chamadas and all(kw == {"stem_fallback": True} for kw in chamadas)

    chamadas.clear()
    bloco = {"topic_text": "Máquinas de Turing", "rows": [{"content": "Máquinas de Turing"}]}
    esperado = IX._score_timeline_block_against_taxonomy_topic(bloco, _U1[0])
    monkeypatch.setattr(IX, "_score_entry_against_taxonomy_topic", espiao)
    assert IX._score_timeline_block_against_taxonomy_topic(bloco, _U1[0]) == esperado
    assert chamadas == [{}]


def test_propagacao_real_recalcula_divisores_na_taxonomia_enriquecida():
    from functools import partial

    from src.builder.extraction.entry_signals import collect_entry_unit_signals
    from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
    from src.builder.timeline.index import _iter_content_taxonomy_topics

    tax = {"units": [{"slug": "unidade-01-ml", "title": "Unidade Um", "topics": [
        {"slug": "modelos-preditivos", "label": "Modelos Preditivos", "aliases": []},
        {"slug": "agrupamento", "label": "Agrupamento", "aliases": []}]}]}
    recebidos = []

    def divisores_espiao(topicos):
        recebidos.append([(t["topic_slug"], list(t.get("aliases") or [])) for t in topicos])
        return _divisores_de_frase(topicos)

    seletor = partial(auto_map_entry_subtopic, collect_entry_unit_signals=collect_entry_unit_signals,
                      iter_content_taxonomy_topics=_iter_content_taxonomy_topics,
                      score_entry_against_taxonomy_topic=_score_entry_against_taxonomy_topic,
                      topic_match_result_factory=TopicMatchResult, divisores_de_frase=divisores_espiao)
    confiante = TopicMatchResult("modelos-preditivos", "Modelos Preditivos", "unidade-01-ml", 0.9, False, ["1a"])
    indeciso = TopicMatchResult("", "", "", 0.0, True, ["sem-sinal"])
    receptor = {"id": "r", "title": "Terceira"}
    passe1 = [({"id": "d1", "title": "Primeira"}, "# Perceptron\nTexto.", "unidade-01-ml", confiante),
              ({"id": "d2", "title": "Segunda"}, "# Perceptron\nOutro.", "unidade-01-ml", confiante),
              (receptor, "# Perceptron\nMais.", "unidade-01-ml", indeciso)]
    mudou = propagar_vocabulario_por_headings(passe1, tax, seletor, conf_min=0.7, min_entries=2, df_max=1.0)

    assert mudou == 1 and receptor["computed_subunit_slug"] == "modelos-preditivos"
    assert recebidos == [[("modelos-preditivos", ["perceptron"]), ("agrupamento", [])]]   # taxonomia ENRIQUECIDA
    assert tax["units"][0]["topics"][0]["aliases"] == []                                   # original intocada


# Integração A+P1 (#90): o callback de subunidade da produção (engine -> facade/file_map.py) liga o P1. O mesmo objeto
# chega à 1a passada (resolver_apply.apply_unit_subunit_fields) e à 2a (propagar_vocabulario_por_headings).
def _tax_turing():
    return {"units": [{"slug": "u1", "title": "Computabilidade", "topics": [
        {"slug": slugify(t), "label": t, "aliases": []} for t in [x["topic_label"] for x in _U1]]}]}


_ENTRADA_TURING = ({"id": "m", "title": "Máquinas de Turing"},
                   "# Variações de Máquinas de Turing\n\nFita múltipla e não determinismo.")


def test_callback_de_producao_liga_o_p1_na_primeira_passada():
    from src.builder.engine import _auto_map_entry_subtopic

    entry, md = _ENTRADA_TURING
    r = _auto_map_entry_subtopic(dict(entry), _tax_turing(), md, winning_unit_slug="u1")
    assert (r.topic_slug, r.ambiguous) == ("variacoes-de-maquinas-de-turing", False)   # sem P1: maquinas-de-turing


def test_callback_de_producao_liga_o_p1_na_segunda_passada():
    from src.builder.engine import _auto_map_entry_subtopic
    from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings

    entry, md = _ENTRADA_TURING
    receptor = dict(entry)
    passe1 = [(receptor, md, "u1", TopicMatchResult("", "", "", 0.0, True, ["sem-sinal"]))]
    mudou = propagar_vocabulario_por_headings(passe1, _tax_turing(), _auto_map_entry_subtopic,
                                              conf_min=0.7, min_entries=2, df_max=1.0)
    assert mudou == 1 and receptor["computed_subunit_slug"] == "variacoes-de-maquinas-de-turing"
