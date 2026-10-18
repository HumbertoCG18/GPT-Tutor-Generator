"""Guards de igualdade de set para Task 1.3 — stopwords unificadas.

Cada assert captura os membros REAIS no momento do snapshot (17/06/2026).
Se qualquer set mudar, o guard falha — intencionalmente.
"""
import pytest


def test_timeline_generic_tokens_membership():
    from src.builder.timeline.index import _TIMELINE_GENERIC_TOKENS
    assert _TIMELINE_GENERIC_TOKENS == {
        "apresentacao", "assincrona", "assincrono", "atividade", "aula", "aulas",
        "caso", "complementar", "conteudo", "conteudos", "continuacao", "dia",
        "estudo", "estudos", "exercicio", "exercicios", "finalizacao", "gabarito",
        "gabaritos", "hora", "leituras", "lista", "listas", "materia", "material",
        "pagina", "paginas", "pratica", "praticas", "prova", "provas", "recomendadas",
        "recursos", "resposta", "respostas", "revisao", "revisoes", "semana",
        "teorica", "teoricas", "unidade",
    }


def test_timeline_unit_neutral_tokens_membership():
    from src.builder.timeline.index import _TIMELINE_UNIT_NEUTRAL_TOKENS
    assert _TIMELINE_UNIT_NEUTRAL_TOKENS == {
        "algoritmo", "algoritmos", "aplicacao", "aplicacoes", "computa",
        "computacao", "computacoes", "estado", "estados", "formais", "formal",
        "fundamentos", "logica", "logicas", "metodos", "modelo", "modelos",
        "para", "passo", "passos", "predicado", "predicados", "programa",
        "programas", "proposicional", "semantica", "sequencia", "sequencias",
        "simplificacao", "sintaxe", "sistemas", "software", "softwares",
        "substituicao", "suporte", "variaveis", "variavel", "verificacao",
        "verificacoes",
    }


def test_unit_generic_tokens_membership():
    from src.builder.routing.file_map import UNIT_GENERIC_TOKENS
    assert UNIT_GENERIC_TOKENS == {
        "aplicacoes", "concorrentes", "especificacao", "especificacoes",
        "formais", "formal", "fundamentos", "linguagens", "logica", "logicas",
        "metodos", "modelo", "modelos", "programa", "programas", "propriedades",
        "sequenciais", "sistemas", "software", "softwares", "suporte",
        "verificacao", "verificacoes",
    }


def test_unit_matcher_stopwords_membership():
    from src.builder.timeline.unit_matcher import _STOPWORDS
    assert _STOPWORDS == {
        "a", "ao", "aos", "as", "aula", "com", "da", "das", "de", "do", "dos",
        "e", "em", "introducao", "modulo", "na", "nas", "no", "nos", "o", "os",
        "para", "parte", "que", "sobre", "um", "uma",
    }


def test_card_block_stop_membership():
    from src.builder.text.stopwords import CARD_BLOCK_STOP as _STOP
    assert _STOP == {
        "a", "da", "de", "do", "e", "em", "o", "of", "para", "por", "the",
    }


def test_card_block_e_block_identity_usam_o_tokenizador_unico():
    """Consolidacao 07/09: o `_tokens` duplicado byte a byte virou `text.tokens.card_stop_tokens`."""
    from src.builder.text.tokens import card_stop_tokens
    from src.builder.timeline import block_identity, card_block
    assert card_block._tokens is card_stop_tokens and block_identity._tokens is card_stop_tokens
    assert card_stop_tokens("A Logica de Hoare para o Dafny") == {"logica", "hoare", "dafny"}


def test_listas_de_genericos_moram_so_em_stopwords():
    """Consolidacao 07/09 (tier B): os modulos importam por alias; a definicao e uma so."""
    from src.builder.text import stopwords as sw
    from src.builder.timeline import unit_matcher, index
    from src.builder.extraction import content_taxonomy
    from src.builder.core import semantic_config
    from src.builder.routing.motor import disambiguator
    assert unit_matcher._UNIT_GENERIC is sw.UNIT_MATCHER_GENERIC
    assert content_taxonomy._UNIT_TITLE_GENERIC is sw.UNIT_TITLE_GENERIC
    assert semantic_config._SEMANTIC_TOKEN_STOPWORDS is sw.SEMANTIC_TOKEN_STOPWORDS
    assert index._LABEL_STOP is sw.LABEL_PART_STOP and index._TOPIC_FALLBACK_STOPWORDS is sw.TOPIC_FALLBACK_STOPWORDS
    assert disambiguator._GENERIC_STEMS is sw.MOTOR_GENERIC_STEMS
    assert sw.TOPIC_SUPPORT_STOP == {"sobre", "para", "com", "sem", "entre"}
    assert sw.FILE_MAP_TITLE_ANCHOR_STOP == {"unidade", "aprendizagem", "verificacao"}



def test_descricao_de_imagem_sai_do_texto_que_o_scorer_pontua():
    """07/09: a descricao de imagem serve ao ALUNO e fica no markdown, mas nao pontua — a caption generica em ingles
    entrava no vocabulario propagado do curso e desviava a subunidade de materiais que nem tem imagem."""
    from src.builder.extraction.entry_signals import texto_para_score
    md = (
        "# Morfologia\n\n"
        "<!-- IMAGE_DESCRIPTION: datalab-abc_img.jpg -->\n"
        "<!-- Tipo: generico -->\n"
        "> **[Descricao de imagem]** A 4x4 grid showing the result of erosion.\n"
        "<!-- /IMAGE_DESCRIPTION -->\n\n"
        "Segmentacao de imagens por limiarizacao.\n"
    )
    limpo = texto_para_score(md)
    assert "IMAGE_DESCRIPTION" not in limpo and "erosion" not in limpo
    assert "Segmentacao de imagens por limiarizacao." in limpo and "# Morfologia" in limpo
    # texto sem bloco passa intacto (no-op barato)
    assert texto_para_score("# so texto") == "# so texto"
