from src.builder.routing.thresholds import margin_confidence, T


def test_margin_confidence_formula():
    # (winner - runner) + winner*k, clamp 0..1
    assert margin_confidence(2.0, 1.0, k=0.18) == 1.0  # 1.0 + 0.36 -> clamp 1.0
    assert round(margin_confidence(1.2, 1.0, k=0.18), 3) == round((0.2) + 1.2 * 0.18, 3)
    assert margin_confidence(0.0, 0.0, k=0.18) == 0.0


def test_thresholds_present():
    # limiares nomeados centralizados (BLOCK_UNIT_*/VOTE_* morreram com o
    # fallback keyword de unidade no cutover passo 3)
    # UNIT_TAG: 0.65 -> 0.50 em 2026-08-18, sweep ponta-a-ponta contra
    # `scripts/eval_entry_unit.py` (191 entries, 5 cursos): +6 gravadas certas,
    # +1 errada, -7 vazias. Satura em 0.40. Ver thresholds.py para a tabela.
    assert T.UNIT_TAG == 0.50
    assert T.SUBUNIT_TAG == 0.10  # calibrado 01/09 (sweep 93 golds; ver thresholds.py)


def test_margin_matches_old_inline_018():
    # reproduz a formula inline antiga p/ K=0.18
    winner, runner = 1.5, 0.9
    old = min(1.0, max(0.0, (winner - runner) + (winner * 0.18)))
    from src.builder.routing.thresholds import margin_confidence
    assert margin_confidence(winner, runner, k=0.18) == old


def test_margin_topic_usa_thresholds():
    # paridade da inline antiga de timeline/index._select_primary_topic
    # (k=0.20 = T.MARGIN_K_TOPIC), incluindo o clamp [0,1]
    assert T.MARGIN_K_TOPIC == 0.20
    for winner, runner in [(1.5, 0.9), (0.4, 0.1), (3.0, 0.5), (0.0, 0.0), (0.2, 0.9)]:
        old = min(1.0, max(0.0, (winner - runner) + (winner * 0.2)))
        assert margin_confidence(winner, runner, k=T.MARGIN_K_TOPIC) == old


def test_date_boosts_centralizados():
    from src.builder.routing.thresholds import DATE_STRONG_BOOST, DATE_WEAK_BOOST
    from src.builder.routing import file_map

    assert DATE_STRONG_BOOST == 0.30
    assert DATE_WEAK_BOOST == 0.10
    assert file_map.DATE_STRONG_BOOST is DATE_STRONG_BOOST
    assert file_map.DATE_WEAK_BOOST is DATE_WEAK_BOOST


def test_signal_token_set_fonte_unica():
    from src.builder.text.normalize import signal_token_set
    from src.builder.extraction import content_taxonomy as ct

    # default (canonico): strip de +-./
    assert signal_token_set("Logica de Hoare e C++ 2024") == {"logica", "hoare", "2024"}
    # wrapper da taxonomy preserva a copia divergente local (mantem +-./)
    assert ct._signal_token_set("isabelle/hol provas") == {"isabelle/hol", "provas"}


def test_smv_e_linguagem_de_codigo_reconhecida():
    """NuSMV e ferramenta central do MF e `.smv` nao estava na lista.

    `concept_resolver.py:442` ja documentava "a ferramenta (.dfy/.thy/.smv)
    ancora a UNIDADE", mas `CODE_EXTENSIONS` so tinha .thy e .dfy — o
    `exemplos.zip` do MF (5 arquivos .smv de model checking) saia com
    `extracted_files=[]`, sem resumo do Gemini e sem sinal nenhum
    (medido 2026-08-19: era o UNICO zip sem extracao nos 5 cursos).
    """
    from src.utils.helpers import CODE_EXTENSIONS, LANG_MAP
    from src.builder.routing.thresholds import TOOL_EXTENSIONS

    assert ".smv" in CODE_EXTENSIONS
    assert LANG_MAP["smv"] == "nusmv"
    assert TOOL_EXTENSIONS[".smv"] == "nusmv"
    # os tres pares de metodos formais andam juntos
    for ext, lang in ((".thy", "isabelle"), (".dfy", "dafny"), (".smv", "nusmv")):
        assert ext in CODE_EXTENSIONS and TOOL_EXTENSIONS[ext] == lang
