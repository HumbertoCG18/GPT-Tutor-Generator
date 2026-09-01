from src.builder.core.reference_topic import assign_concepts_to_unit


def _units():
    return [
        {"slug": "unidade-01-seguranca", "normalized_title": "seguranca de aplicacoes",
         "topic_phrases": ["autenticacao", "autorizacao", "spring security"],
         "topic_tokens": ["autenticacao", "autorizacao", "seguranca"], "distinctive_tokens": ["oauth"]},
        {"slug": "unidade-02-microservicos", "normalized_title": "microservicos",
         "topic_phrases": ["service discovery", "api gateway"],
         "topic_tokens": ["microservico", "discovery", "gateway"], "distinctive_tokens": ["eureka"]},
    ]


def test_maps_concepts_to_matching_unit():
    out = assign_concepts_to_unit(["service discovery", "eureka registry"], "", _units())
    assert out["unit_slug"] == "unidade-02-microservicos"
    assert out["confidence"] > 0.0


def test_no_match_returns_empty_slug():
    out = assign_concepts_to_unit(["fotossintese", "mitocondria"], "", _units())
    assert out["unit_slug"] == ""


def test_falls_back_to_text_when_no_concepts():
    out = assign_concepts_to_unit([], "tutorial de spring security e autenticacao", _units())
    assert out["unit_slug"] == "unidade-01-seguranca"


def test_empty_everything_returns_empty():
    out = assign_concepts_to_unit([], "", _units())
    assert out["unit_slug"] == ""
    assert out["topics"] == []


# --- cobertura N:N (2026-08-18) ---------------------------------------------
# Material transversal (prova, lista, bibliografia) cobre VARIAS unidades. O
# single-winner elegia uma e descartava o resto; e `topics` devolvia todos os
# topic_phrases da unidade vencedora, nao os que casaram.

def test_devolve_todas_as_unidades_acima_do_threshold():
    out = assign_concepts_to_unit(
        ["service discovery", "autenticacao", "api gateway", "oauth"], "", _units())

    slugs = [u["unit_slug"] for u in out["units"]]
    assert set(slugs) == {"unidade-01-seguranca", "unidade-02-microservicos"}
    assert out["unit_slug"] == slugs[0]                    # compat: 1a e a vencedora
    assert all(u["confidence"] > 0 for u in out["units"])


def test_topics_sao_os_que_casaram_e_nao_a_unidade_inteira():
    out = assign_concepts_to_unit(["service discovery"], "", _units())

    assert out["unit_slug"] == "unidade-02-microservicos"
    assert out["topics"] == ["service discovery"]          # nao inclui "api gateway"


def test_sem_match_devolve_lista_vazia():
    out = assign_concepts_to_unit(["fotossintese"], "", _units())
    assert out["units"] == [] and out["unit_slug"] == ""


def test_texto_bruto_mede_cobertura_da_unidade_nao_fracao_do_texto():
    """Sem Gemini os 'conceitos' viram o texto inteiro (~2000 termos): a fracao
    `overlap/len(termos)` fica diluida e NUNCA cruza o threshold — medido em
    2026-08-18, 0 de 10 refs mapeadas mesmo com o texto local disponivel.
    Com texto bruto a pergunta certa se inverte: quantos topicos DA UNIDADE o
    texto cita."""
    texto = ("Este material trata de service discovery e tambem de api gateway "
             "em profundidade, com exemplos praticos e muitas outras palavras de "
             "enchimento que nao dizem respeito a nenhuma unidade do plano.")

    out = assign_concepts_to_unit([], texto, _units())

    assert out["unit_slug"] == "unidade-02-microservicos"
    assert set(out["topics"]) == {"service discovery", "api gateway"}


def test_frase_distintiva_citada_cobre_a_unidade_mesmo_com_muitos_topicos():
    """A u03 do SO tem 29 topic_phrases (glossario infla a lista): exigir FRACAO
    fazia 1/29 = 0,03 nunca cruzar o threshold, e o material de sockets — cujo
    card e o proprio nome do topico 4.2 — ficava sem cobertura. Uma frase
    distintiva citada ja cobre a unidade; a fracao vira so a confianca."""
    unidade = {
        "slug": "u-conc", "normalized_title": "programacao concorrente",
        "topic_phrases": ["comunicacao e sincronizacao de processos"] + [f"ruido{i}" for i in range(28)],
        "topic_tokens": ["comunicacao", "sincronizacao"], "distinctive_tokens": [],
    }
    texto = "Programacao de sockets: comunicacao e sincronizacao de processos entre maquinas."

    out = assign_concepts_to_unit([], texto, [unidade])

    assert out["unit_slug"] == "u-conc"
    assert out["topics"] == ["comunicacao e sincronizacao de processos"]
    assert 0.0 < out["confidence"] < 0.34          # confianca honesta: 1 de 29


def test_frase_de_uma_palavra_sozinha_nao_cobre():
    """`termos`, `central`, `sumario` entram como topic_phrase pelo glossario —
    fracas demais para carregar uma unidade sozinhas."""
    unidade = {"slug": "u-x", "normalized_title": "unidade x",
               "topic_phrases": ["termos", "central"], "topic_tokens": ["termos"],
               "distinctive_tokens": []}
    out = assign_concepts_to_unit([], "o texto usa termos de forma central", [unidade])
    assert out["unit_slug"] == ""
