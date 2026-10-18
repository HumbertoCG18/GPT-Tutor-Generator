
"""F2/F3/F11: cue lexico (prova/substituicao/bibliografia) nao dispara quando a frase
e conteudo do PLANO daquele curso (censo Lab SO / Fund. Redes, 2026-08-28)."""
from src.builder.timeline.classifier import BlockKind, classify_block
from src.builder.timeline.index import plan_phrases_para_classificacao
from src.utils.helpers import auto_detect_category

FRASES_LAB_SO = (
    "avaliacao de desempenho da nova implementacao frente as implementacao pre-existentes",
    "algoritmos de substituicao de paginas",
)


def _bloco(texto, frases=FRASES_LAB_SO):
    return {"topic_text": texto, "topics": [], "sessions": [], "unit_slug": "",
            "_plan_phrases": frases}


class TestF2F3_CueXConteudoDoPlano:
    def test_avaliacao_de_desempenho_e_aula(self):
        assert classify_block(_bloco("avaliacao de desempenho de escalonamento")) is BlockKind.CLASS

    def test_substituicao_de_paginas_e_aula(self):
        assert classify_block(_bloco("algoritmos de substituicao de paginas")) is BlockKind.CLASS

    def test_substituicao_solta_continua_makeup(self):
        """MF bloco-21 "substituicao" (prova substituta) nao casa topico nenhum."""
        assert classify_block(_bloco("substituicao")) is BlockKind.MAKEUP

    def test_prova_p1_continua_assessment_mesmo_com_frases(self):
        """Sinal forte de exame nao e suprimido nem com "sistema de prova" no plano (MF)."""
        assert classify_block(_bloco("prova p1", frases=("sistema de prova",))) is BlockKind.ASSESSMENT

    def test_sem_frases_comportamento_antigo(self):
        b = {"topic_text": "avaliacao de desempenho de escalonamento", "topics": [],
             "sessions": [], "unit_slug": ""}
        assert classify_block(b) is BlockKind.ASSESSMENT

    def test_plan_phrases_vem_do_unit_index_e_nao_persiste(self):
        from src.builder.timeline.index import ensure_block_kind
        ui = [{"title": "Unidade 4", "topics": [("Algoritmos de substituição de páginas", 1)]}]
        frases = plan_phrases_para_classificacao(ui)
        assert any("substituicao de paginas" in f for f in frases)
        b = _bloco("algoritmos de substituicao de paginas", frases=frases)
        ensure_block_kind(b)
        assert b["kind"] == "class" and "_plan_phrases" not in b


class TestF11_CategoriaXConteudoDoPlano:
    FRASES_FR = ("modelos de referencia de interconexao de computadores osi/iso",)

    def test_modelos_de_referencia_nao_e_bibliografia(self):
        assert auto_detect_category("02 - modelos de referencia.pdf",
                                    frases_do_plano=self.FRASES_FR) != "bibliografia"

    def test_sem_frases_comportamento_antigo(self):
        assert auto_detect_category("02 - modelos de referencia.pdf") == "bibliografia"

    def test_referencia_de_verdade_continua_bibliografia(self):
        assert auto_detect_category("referencias bibliograficas.pdf",
                                    frases_do_plano=self.FRASES_FR) == "bibliografia"
