from src.builder.text.normalize import split_camel_case


def test_camel_case_basico():
    assert split_camel_case("LogicaDeHoare") == "Logica De Hoare"


def test_camel_case_com_digito():
    assert split_camel_case("LogicaDeHoare2") == "Logica De Hoare 2"


def test_sigla_pura_preservada():
    assert split_camel_case("IHC") == "IHC"
    assert split_camel_case("P1") == "P1"


def test_snake_e_espacos_intactos():
    assert split_camel_case("logicaProposicional_semantica") == "logica Proposicional_semantica"


def test_texto_normal_intacto():
    assert split_camel_case("provas por inducao") == "provas por inducao"
