"""Testes diretos para src.builder.routing.coverage_rules.

Tres regras (A: meta, B: avaliacao, C: card) e constantes de fronteira
(_FRACAO_META, _MIN_TOPICOS_PARA_UNIDADE, _MIN_TOKEN_DISTINTIVO).
Regra D (unidade 1:1 como fallback) testada implicitamente em B e C.
"""
import pytest
from src.builder.routing.coverage_rules import (
    derive_coverage_units,
    _topicos_por_unidade,
    _casa,
    _FRACAO_META,
    _MIN_TOPICOS_PARA_UNIDADE,
    _MIN_TOKEN_DISTINTIVO,
    META_CATEGORIES,
    AVALIACAO_CATEGORIES,
)


def _norm(t: str) -> str:
    """Normalizacao minima para testes."""
    return t.lower().strip()


class TestRegra_A_Meta:
    """Regra A: meta-material (plano, programa, apresentacao) cobre TODAS as unidades."""

    def test_categoria_cronograma_retorna_todas(self):
        """Se categoria eh 'cronograma', retorna todas as unidades."""
        entry = {"category": "cronograma", "title": "", "source_section": ""}
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
            {"slug": "u2", "normalized_title": "redes"},
        ]
        result = derive_coverage_units(
            entry, units, "", normalize=_norm
        )
        assert len(result) == 2
        assert all(r["rule"] == "meta" for r in result)
        assert {r["unit_slug"] for r in result} == {"u1", "u2"}
        assert all(r["confidence"] == 1.0 for r in result)

    def test_fracao_meta_limiar_80_porcento(self):
        """Se >= 80% dos titulos sao citados, retorna todas as unidades."""
        # 3 unidades com titulos: precisa citar pelo menos 3 (100%), 2.4 arredonda pra 3
        # Testamos: citar 3 de 4 = 75%, nao deve ativar
        # Citar 3 de 3 = 100%, deve ativar
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
            {"slug": "u2", "normalized_title": "redes"},
            {"slug": "u3", "normalized_title": "criptografia"},
        ]
        # 2 de 3 = 66%, abaixo do limiar
        entry_low = {
            "category": "referencia",
            "title": "",
            "source_section": "",
        }
        texto = "seguranca e redes sao importantes"
        result = derive_coverage_units(
            entry_low, units, texto, normalize=_norm
        )
        # Nao ativa regra A por conteudo
        assert not any(r["rule"] == "meta-por-conteudo" for r in result)

        # 3 de 3 = 100%, acima do limiar
        entry_high = {
            "category": "referencia",
            "title": "",
            "source_section": "",
        }
        texto = "seguranca e redes e criptografia sao importantes"
        result = derive_coverage_units(
            entry_high, units, texto, normalize=_norm
        )
        assert len(result) == 3
        assert all(r["rule"] == "meta-por-conteudo" for r in result)

    def test_fracao_meta_ignora_titulos_curtos(self):
        """Titulos com < 6 caracteres sao ignorados para calculo de fracao."""
        units = [
            {"slug": "u1", "normalized_title": "seg"},  # < 6, ignorado
            {"slug": "u2", "normalized_title": "seguranca"},
            {"slug": "u3", "normalized_title": "redes"},
        ]
        # "seg" e ignorado, restam 2. Se citar "seguranca" e "redes", e 2 de 2 = 100%
        entry = {
            "category": "referencia",
            "title": "",
            "source_section": "",
        }
        texto = "seguranca e redes"
        result = derive_coverage_units(
            entry, units, texto, normalize=_norm
        )
        assert len(result) == 3
        assert all(r["rule"] == "meta-por-conteudo" for r in result)


class TestRegra_B_Avaliacao:
    """Regra B: lista/prova/gabarito com padrao PX cobre unidades citadas no enunciado."""

    def test_prova_1_encontra_topicos_e_titulo(self):
        """'Prova 1' encontra unidades cujos topicos aparecem no texto."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
            {"slug": "u2", "normalized_title": "redes"},
        ]
        topic_index = [
            {"unit_slug": "u1", "topic_label": "autenticacao", "aliases": []},
            {"unit_slug": "u1", "topic_label": "autorizacao", "aliases": []},
            {"unit_slug": "u2", "topic_label": "roteamento", "aliases": []},
        ]
        entry = {
            "category": "provas",
            "title": "Prova 1",
            "source_section": "",
        }
        # Enunciado cita "autenticacao" (de u1) mas nao "roteamento" (de u2)
        texto = "questao 1 sobre autenticacao"
        result = derive_coverage_units(
            entry, units, texto, normalize=_norm, topic_index=topic_index
        )
        # Encontra u1 (1 topico >= MIN_TOPICOS=2? Nao, mas tem titulo? Nao).
        # Sem titulo e sem 2 topicos, u1 nao entra
        assert not any(r["unit_slug"] == "u1" for r in result)
        # u2 nao tem nada citado
        assert not any(r["unit_slug"] == "u2" for r in result)

    def test_prova_2_com_titulo_unidade(self):
        """Se o titulo da unidade aparece, entra na cobertura mesmo com < 2 topicos."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
            {"slug": "u2", "normalized_title": "redes"},
            {"slug": "u3", "normalized_title": "cripto"},
        ]
        entry = {
            "category": "provas",
            "title": "Prova 2",
            "source_section": "",
        }
        # Enunciado cita o titulo "seguranca" (1 de 3 = 33%, abaixo de 80%)
        texto = "questoes sobre seguranca"
        result = derive_coverage_units(
            entry, units, texto, normalize=_norm, topic_index=None
        )
        assert len(result) == 1
        assert result[0]["unit_slug"] == "u1"
        assert result[0]["rule"] == "avaliacao"
        # Confidence: 0.4 (base) + 0.2 * 0 (0 topicos) = 0.4
        assert result[0]["confidence"] == 0.4

    def test_lista_1_com_2_topicos_cita_unidade(self):
        """'Lista 1' com 2+ topicos citados entra com confidence alta."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
        ]
        topic_index = [
            {"unit_slug": "u1", "topic_label": "autenticacao", "aliases": []},
            {"unit_slug": "u1", "topic_label": "autorizacao", "aliases": []},
        ]
        entry = {
            "category": "listas",
            "title": "Lista 1 - Seguranca",
            "source_section": "",
        }
        texto = "problema 1: autenticacao. problema 2: autorizacao"
        result = derive_coverage_units(
            entry, units, texto, normalize=_norm, topic_index=topic_index
        )
        assert len(result) == 1
        assert result[0]["unit_slug"] == "u1"
        assert result[0]["rule"] == "avaliacao"
        # Confidence: 0.4 + 0.2 * 2 = 0.8
        assert result[0]["confidence"] == 0.8

    def test_padrao_prova_case_insensitive(self):
        """Padrao 'P1', 'Prova 1', 'Av2' funciona case-insensitive."""
        units = [{"slug": "u1", "normalized_title": "algo"}]
        topic_index = [
            {"unit_slug": "u1", "topic_label": "complexidade", "aliases": []},
            {"unit_slug": "u1", "topic_label": "computabilidade", "aliases": []},
        ]

        # "av 3" com 2 topicos
        entry = {"category": "provas", "title": "AV 3", "source_section": ""}
        texto = "complexidade computabilidade"
        result = derive_coverage_units(
            entry, units, texto, normalize=_norm, topic_index=topic_index
        )
        assert len(result) == 1
        assert result[0]["rule"] == "avaliacao"

        # "P-5" com 2 topicos
        entry = {"category": "provas", "title": "P-5", "source_section": ""}
        result = derive_coverage_units(
            entry, units, texto, normalize=_norm, topic_index=topic_index
        )
        assert len(result) == 1
        assert result[0]["rule"] == "avaliacao"

    def test_sem_padrao_prova_ignora_regra_b(self):
        """Sem P/Prova/Av/Lista seguido de numero, regra B nao ativa."""
        units = [{"slug": "u1", "normalized_title": "algo"}]
        topic_index = [
            {"unit_slug": "u1", "topic_label": "complexidade", "aliases": []},
        ]
        entry = {
            "category": "listas",
            "title": "Exercicios gerais",  # Sem numero
            "source_section": "",
        }
        texto = "complexidade"
        result = derive_coverage_units(
            entry, units, texto, normalize=_norm, topic_index=topic_index
        )
        # Nao entra por regra B
        assert not any(r["rule"] == "avaliacao" for r in result)


class TestRegra_C_Card:
    """Regra C: card do Moodle nomeia a unidade/topico -> entra na cobertura."""

    def test_card_bate_titulo_unidade(self):
        """Se card contem titulo da unidade, entra com confidence 0.9."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
        ]
        entry = {
            "category": "referencia",
            "title": "Material",
            "source_section": "seguranca",
        }
        result = derive_coverage_units(
            entry, units, "", normalize=_norm
        )
        assert len(result) == 1
        assert result[0]["unit_slug"] == "u1"
        assert result[0]["confidence"] == 0.9
        assert result[0]["rule"] == "card"

    def test_card_bate_topico(self):
        """Se card contem topico da unidade, entra com confidence 0.7."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
        ]
        topic_index = [
            {"unit_slug": "u1", "topic_label": "autenticacao", "aliases": []},
        ]
        entry = {
            "category": "referencia",
            "title": "Material",
            "source_section": "autenticacao",
        }
        result = derive_coverage_units(
            entry, units, "", normalize=_norm, topic_index=topic_index
        )
        assert len(result) == 1
        assert result[0]["unit_slug"] == "u1"
        assert result[0]["confidence"] == 0.7
        assert result[0]["rule"] == "card"
        assert result[0]["topics"] == ["autenticacao"]

    def test_card_token_distintivo_min(self):
        """Card usa _casa(): contencao OU token >= _MIN_TOKEN_DISTINTIVO."""
        units = [
            {"slug": "u1", "normalized_title": "unidade"},
        ]
        topic_index = [
            # "entscheidungsproblem" tem 18 chars, >= 10
            {"unit_slug": "u1", "topic_label": "entscheidungsproblem", "aliases": []},
        ]
        entry = {
            "category": "referencia",
            "title": "Material",
            "source_section": "Halteproblem und Entscheidungsproblem",
        }
        result = derive_coverage_units(
            entry, units, "", normalize=_norm, topic_index=topic_index
        )
        # "entscheidungsproblem" aparece como token em ambos
        assert len(result) == 1
        assert result[0]["topics"] == ["entscheidungsproblem"]

    def test_card_multiplos_candidatos_fica_melhor(self):
        """Multiplos candidatos: fica a de MAIOR evidencia (titulo > topicos > nada)."""
        units = [
            {"slug": "u1", "normalized_title": "microsservicos"},
            {"slug": "u2", "normalized_title": "arquitetura"},
        ]
        topic_index = [
            {"unit_slug": "u1", "topic_label": "microsservicos", "aliases": []},
            {"unit_slug": "u1", "topic_label": "containerizacao", "aliases": []},
            {"unit_slug": "u2", "topic_label": "microsservicos", "aliases": []},
        ]
        entry = {
            "category": "referencia",
            "title": "Material",
            "source_section": "microsservicos",
        }
        result = derive_coverage_units(
            entry, units, "", normalize=_norm, topic_index=topic_index
        )
        # Ambas casam "microsservicos", mas u1 tem titulo exato
        # u1: bate_titulo=True, n_topicos=1
        # u2: bate_titulo=False, n_topicos=1
        # Melhor = (True, 1), que e u1
        assert len(result) == 1
        assert result[0]["unit_slug"] == "u1"
        assert result[0]["confidence"] == 0.9

    def test_card_empate_verdadeiro_mantem_ambas(self):
        """Empate genuino (mesmo titulo e topicos): mantem ambas as unidades."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
            {"slug": "u2", "normalized_title": "seguranca"},  # Mesmo titulo
        ]
        entry = {
            "category": "referencia",
            "title": "Material",
            "source_section": "seguranca",
        }
        result = derive_coverage_units(
            entry, units, "", normalize=_norm
        )
        # Ambas bate_titulo=True, n_topicos=0, empate mantido
        assert len(result) == 2
        assert {r["unit_slug"] for r in result} == {"u1", "u2"}
        assert all(r["confidence"] == 0.9 for r in result)

    def test_card_vazio_ignora_regra_c(self):
        """Card vazio ou < 4 chars ignora regra C."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
        ]
        entry = {
            "category": "referencia",
            "title": "Material",
            "source_section": "a",  # < 4 chars
        }
        result = derive_coverage_units(
            entry, units, "", normalize=_norm
        )
        # Regra C desativada
        assert not any(r["rule"] == "card" for r in result)


class TestRegra_D_Fallback:
    """Regra D: unidade 1:1 atribuida entra como fallback com confidence 0.5."""

    def test_fallback_unit_entra_se_nenhuma_regra_casa(self):
        """Se nenhuma outra regra ativa, fallback_unit_slug entra."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
        ]
        entry = {
            "category": "referencia",
            "title": "Material",
            "source_section": "",
        }
        result = derive_coverage_units(
            entry, units, "", normalize=_norm, fallback_unit_slug="u1"
        )
        assert len(result) == 1
        assert result[0]["unit_slug"] == "u1"
        assert result[0]["confidence"] == 0.5
        assert result[0]["rule"] == "unidade-atribuida"

    def test_fallback_ignorado_se_regra_ja_cobriu(self):
        """Se outra regra ja cobriu a unidade, fallback nao re-entra."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
        ]
        entry = {
            "category": "referencia",
            "title": "Material",
            "source_section": "seguranca",  # Regra C bate
        }
        result = derive_coverage_units(
            entry, units, "", normalize=_norm, fallback_unit_slug="u1"
        )
        # Deveria ter 1 entrada com rule "card", nao "unidade-atribuida"
        assert len(result) == 1
        assert result[0]["rule"] == "card"
        assert result[0]["confidence"] == 0.9


class TestConstantes:
    """Validar constantes de fronteira."""

    def test_fracao_meta_eh_ponto_oito(self):
        """_FRACAO_META constante e 0.8."""
        assert _FRACAO_META == 0.8

    def test_min_topicos_para_unidade_eh_dois(self):
        """_MIN_TOPICOS_PARA_UNIDADE constante e 2."""
        assert _MIN_TOPICOS_PARA_UNIDADE == 2

    def test_min_token_distintivo_eh_dez(self):
        """_MIN_TOKEN_DISTINTIVO constante e 10."""
        assert _MIN_TOKEN_DISTINTIVO == 10


class TestHelper_Casa:
    """Helper _casa(): contencao OU token distintivo >= 10 chars — so com token distintivo (R2)."""

    def test_casa_contencao_exata(self):
        """Contencao conta quando a frase tem 2 tokens distintivos ou 1 longo (R2, 2026-08-27):
        "processos" dentro de "gerencia de processos cpu" NAO sustenta unidade."""
        assert _casa("seguranca de redes", "topico seguranca de redes avancado")
        assert _casa("criptografia", "aula de criptografia")          # 12 chars, longo
        assert not _casa("processos", "gerencia de processos cpu")    # 1 token curto
        assert not _casa("seg", "auth")

    def test_casa_token_distintivo_10_chars(self):
        """Token >= 10 chars compartilhado retorna True."""
        # "autenticacao" tem 12 chars
        assert _casa("autenticacao funciona", "mecanismo autenticacao")
        # "auth" tem 4 chars, ignorado
        assert not _casa("auth token", "authentication")

    def test_casa_vazio_retorna_false(self):
        """Vazio em qualquer lado retorna False."""
        assert not _casa("", "algo")
        assert not _casa("algo", "")
        assert not _casa("", "")


class TestHelper_TopicosPorUnidade:
    """Helper _topicos_por_unidade(): extrai topicos da taxonomia."""

    def test_extrai_labels_e_aliases(self):
        """Label e aliases sao usados."""
        topic_index = [
            {
                "unit_slug": "u1",
                "topic_label": "autenticacao",
                "aliases": ["autenticacao forte", "sistema de autenticacao"],
            },
        ]
        result = _topicos_por_unidade(topic_index, _norm)
        assert "u1" in result
        assert "autenticacao" in result["u1"]
        assert "autenticacao forte" in result["u1"]
        assert "sistema de autenticacao" in result["u1"]

    def test_ignora_topicos_curtos(self):
        """Topicos normalizados com < 6 chars sao ignorados."""
        topic_index = [
            {"unit_slug": "u1", "topic_label": "a", "aliases": []},
            {"unit_slug": "u1", "topic_label": "autenticacao", "aliases": []},
        ]
        result = _topicos_por_unidade(topic_index, _norm)
        assert "u1" in result
        assert "autenticacao" in result["u1"]
        assert "a" not in result["u1"]

    def test_sem_unit_slug_ignorado(self):
        """Topicos sem unit_slug sao ignorados."""
        topic_index = [
            {"topic_label": "orfao", "aliases": []},  # Sem unit_slug
            {"unit_slug": "u1", "topic_label": "autenticacao", "aliases": []},
        ]
        result = _topicos_por_unidade(topic_index, _norm)
        assert "u1" in result
        assert len(result) == 1


class TestOrdenacao:
    """Resultado retorna ordenado por confidence desc, slug asc."""

    def test_ordena_por_confidence_desc_depois_slug_asc(self):
        """Resultado: (-confidence, slug)."""
        units = [
            {"slug": "u1", "normalized_title": "seguranca"},
            {"slug": "u2", "normalized_title": "redes"},
            {"slug": "u3", "normalized_title": "cripto"},
        ]
        topic_index = [
            {"unit_slug": "u1", "topic_label": "autenticacao", "aliases": []},
            {"unit_slug": "u1", "topic_label": "autorizacao", "aliases": []},
            {"unit_slug": "u2", "topic_label": "roteamento", "aliases": []},
        ]
        entry = {
            "category": "listas",
            "title": "Lista 1",
            "source_section": "seguranca redes",
        }
        result = derive_coverage_units(
            entry, units, "autenticacao autorizacao roteamento",
            normalize=_norm, topic_index=topic_index
        )
        # u1 por regra C (card "seguranca"): confidence 0.9
        # u2 por regra C (card "redes"): confidence 0.9
        # u1 por regra B (2 topicos): confidence 0.8
        # u2 por regra B (1 topico): confidence 0.6
        # Deveria estar em ordem: u1@0.9, u2@0.9, u1@0.8, u2@0.6
        # Mas a estrutura cobertas usa dict com slug como chave, entao cada unit entra 1x
        # com a melhor confidence. Entao: u1@0.9, u2@0.9, depois u3 se entra.
        # Se nenhuma regra cobrir u3, nao entra.
        assert result[0]["confidence"] >= result[1]["confidence"]


# ---------------------------------------------------------------- 2026-08-27: R2/R4/R5/R6/R7
def _ti(unit_slug, *labels):
    return [{"unit_slug": unit_slug, "topic_label": lb, "aliases": []} for lb in labels]


_U = [{"slug": "u1", "normalized_title": "introducao"}, {"slug": "u2", "normalized_title": "processador"},
      {"slug": "u3", "normalized_title": "concorrencia"}]


class TestR2_GenericoNaoDistingue:
    def test_topico_de_uma_palavra_curta_no_card_nao_adiciona_unidade(self):
        """SO `exercicios`: card 'Gerencia de Processos CPU' casava u03 pelo topico 'processos'."""
        entry = {"category": "listas", "title": "Exercicios", "source_section": "gerencia de processos cpu"}
        ti = _ti("u3", "processos") + _ti("u2", "escalonamento")
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u2", topic_index=ti)
        assert [c["unit_slug"] for c in out] == ["u2"]

    def test_topico_multi_token_ou_longo_continua_casando(self):
        entry = {"category": "material-de-aula", "title": "x", "source_section": "comunicacao entre processos"}
        ti = _ti("u3", "comunicacao entre processos")
        out = derive_coverage_units(entry, _U, "", normalize=_norm, topic_index=ti)
        assert [c["unit_slug"] for c in out] == ["u3"]

    def test_generico_do_curso_carimbado_no_indice_e_ignorado(self):
        """Token generico por curso (A2, `generic_tokens` no indice) nao e distintivo."""
        units = [dict(_U[0], generic_tokens=["gerencia"]), _U[1], _U[2]]
        entry = {"category": "material-de-aula", "title": "x", "source_section": "gerencia"}
        out = derive_coverage_units(entry, units, "", normalize=_norm, topic_index=_ti("u2", "gerencia"))
        assert out == []


class TestR4_FallbackSoSemRegra:
    def test_scorer_nao_soma_ao_card_que_ja_decidiu(self):
        """4 sobre-coberturas do gold (MF formalizacao/exemplos-zip, TCC aula-12, SO exercicios)."""
        entry = {"category": "material-de-aula", "title": "x", "source_section": "exercicios de logica de hoare"}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u3",
                                    topic_index=_ti("u1", "logica de hoare"))
        assert [c["unit_slug"] for c in out] == ["u1"]

    def test_scorer_entra_quando_nenhuma_regra_disparou(self):
        entry = {"category": "material-de-aula", "title": "x", "source_section": "informacoes gerais"}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u3", topic_index=[])
        assert [(c["unit_slug"], c["rule"]) for c in out] == [("u3", "unidade-atribuida")]


class TestR5_PraticoCobreTodasDoCard:
    TI = _ti("u1", "orientada a microsservicos", "criando um par de microsservicos") + _ti("u2", "estudo de caso integracao de microsservicos")

    def test_roteiro_mantem_as_duas_unidades_do_card(self):
        """ES2 ruling 2026-08-26: roteiros 2-8 cobrem u01 E u02. 'Roteiro2' sem fronteira de palavra."""
        entry = {"id": "roteiro2-nameserver", "category": "material-de-aula", "title": "Roteiro2 - NameServer", "source_section": "microsservicos"}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u1", topic_index=self.TI)
        assert {c["unit_slug"] for c in out} == {"u1", "u2"}
        assert {c["rule"] for c in out} == {"card", "card-pratica"}

    def test_expositivo_fica_com_a_de_maior_evidencia(self):
        entry = {"id": "microsservicos2", "category": "material-de-aula", "title": "Microsservicos 2", "source_section": "microsservicos"}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u1", topic_index=self.TI)
        assert [c["unit_slug"] for c in out] == ["u1"]


class TestR6_CalendarioDaProva:
    BLOCKS = [{"id": "b1", "kind": "class", "unit_slug": "u1"}, {"id": "b2", "kind": "review"},
              {"id": "b3", "kind": "assessment", "topic_text": "P1"}, {"id": "b4", "kind": "class", "unit_slug": "u2"},
              {"id": "b5", "kind": "assessment", "topic_text": "Entrega T1"},
              {"id": "b6", "kind": "class", "unit_slug": "u3"}, {"id": "b7", "kind": "assessment", "topic_text": "P2"}]

    def test_revisao_p1_sem_topico_no_texto_cobre_o_que_veio_antes_da_p1(self):
        """MF revisao-p1-gabarito: titulo 'Revisao_P1_Gabarito' (underscore), 0 topicos no texto."""
        entry = {"id": "revisao-p1-gabarito", "category": "provas", "title": "Revisao_P1_Gabarito", "source_section": "revisao"}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u2", topic_index=[], blocks=self.BLOCKS)
        assert [(c["unit_slug"], c["rule"]) for c in out] == [("u1", "calendario")]

    def test_p2_cobre_a_janela_entre_p1_e_p2_ignorando_entrega(self):
        entry = {"id": "lista-p2", "category": "listas", "title": "Lista P2", "source_section": ""}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, topic_index=[], blocks=self.BLOCKS)
        assert [c["unit_slug"] for c in out] == ["u2", "u3"]

    def test_texto_com_topicos_manda_sobre_o_calendario(self):
        entry = {"id": "lista-p2", "category": "listas", "title": "Lista P2", "source_section": ""}
        out = derive_coverage_units(entry, _U, "escalonamento e quantum", normalize=_norm,
                                    topic_index=_ti("u2", "escalonamento", "quantum"), blocks=self.BLOCKS)
        assert [(c["unit_slug"], c["rule"]) for c in out] == [("u2", "avaliacao")]

    def test_sem_blocks_cai_no_fallback(self):
        entry = {"id": "lista-p2", "category": "listas", "title": "Lista P2", "source_section": ""}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u3", topic_index=[])
        assert [c["rule"] for c in out] == ["unidade-atribuida"]


class TestR7_AvaliacaoGlobal:
    def test_enade_cobre_todas(self):
        entry = {"id": "questoes-do-enade-sobre-sisop", "category": "listas", "title": "Questoes do ENADE sobre SISOP", "source_section": "informacoes gerais"}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u1", topic_index=[])
        assert {c["unit_slug"] for c in out} == {"u1", "u2", "u3"}
        assert {c["rule"] for c in out} == {"avaliacao-global"}

    def test_lista_p1_nao_e_global(self):
        entry = {"id": "lista-p1", "category": "listas", "title": "Lista P1", "source_section": ""}
        out = derive_coverage_units(entry, _U, "", normalize=_norm, fallback_unit_slug="u1", topic_index=[])
        assert [c["unit_slug"] for c in out] == ["u1"]
