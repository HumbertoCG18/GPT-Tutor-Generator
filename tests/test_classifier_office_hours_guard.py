"""Guard anti-sequestro de OFFICE_HOURS: keyword ('duvidas' etc.) so classifica
o bloco quando aparece no proprio label da MAIORIA das sessoes, nao so no
topic_text agregado. Caso real: SO bloco-18 (3 sessoes de "gerencia de
arquivos", 16/06+18/06+23/06) vira office_hours porque o topic_text agregado
carrega "duvidas" de um trecho que nao sobrevive nos labels de sessao
individuais. Fixtures espelham os blocos reais (.timeline_index.json real do
SO/IA, conferido em disco em 2026-08-10; ver institutional.md Contratos)."""
from src.builder.timeline.classifier import classify_block
from src.builder.timeline.kinds import BlockKind


def _bloco18_so():
    # Espelho do bloco real (SO .timeline_index.json, bloco-18): unit_slug
    # vazio (so auto_unit_slug), has_topic via primary_topic_label real.
    return {
        "id": "bloco-18",
        "kind": "",
        "period_label": "3 dias · 16/06/2026 a 23/06/2026",
        "unit_slug": "",
        "auto_unit_slug": "unidade-06-gerencia-de-arquivos",
        "primary_topic_label": "**7.1** Arquivos",
        "topic_text": "gerencia arquivos duvidas para",
        "topics": ["gerencia arquivos", "gerencia arquivos duvidas para"],
        "sessions": [
            {"label": "gerencia de arquivos aula"},
            {"label": "gerencia de arquivos aula"},
            {"label": "gerencia de arquivos"},
        ],
    }


def test_bloco18_so_com_topic_text_contaminado_nao_vira_office_hours():
    assert classify_block(_bloco18_so()) is BlockKind.CLASS


def _bloco_single_session(label, topic_text, primary_topic_label):
    return {
        "id": "bloco-x",
        "kind": "",
        "period_label": "",
        "unit_slug": "",
        "primary_topic_label": primary_topic_label,
        "topic_text": topic_text,
        "topics": [],
        "sessions": [{"label": label}],
    }


def test_so_bloco08_duvidas_prova_sessao_unica_continua_office_hours():
    # SO bloco-08 real: sessao unica "duvidas prova aula".
    b = _bloco_single_session("duvidas prova aula", "duvidas", "Duvidas")
    assert classify_block(b) is BlockKind.OFFICE_HOURS


def test_so_bloco09_duvidas_tp1_p1_continua_office_hours():
    # SO bloco-09 real: sessao unica "duvidas tp1 duvidas p1 aula".
    b = _bloco_single_session("duvidas tp1 duvidas p1 aula", "duvidas", "Duvidas")
    assert classify_block(b) is BlockKind.OFFICE_HOURS


def test_ia_bloco07_duvidas_para_t1_continua_office_hours():
    # IA bloco-07 real: sessao unica "duvidas para t1 aula".
    b = _bloco_single_session("duvidas para t1 aula", "duvidas para", "Duvidas")
    assert classify_block(b) is BlockKind.OFFICE_HOURS


def test_ia_bloco17_duvidas_t2_continua_office_hours():
    # IA bloco-17 real: sessao unica "duvidas t2 aula".
    b = _bloco_single_session("duvidas t2 aula", "duvidas", "Duvidas")
    assert classify_block(b) is BlockKind.OFFICE_HOURS


def test_maioria_das_sessoes_com_duvidas_ainda_vira_office_hours():
    # Guard e sobre MAIORIA, nao unanimidade: 2 de 3 sessoes com duvidas
    # ainda deve classificar office_hours.
    b = {
        "id": "bloco-y",
        "kind": "",
        "period_label": "",
        "unit_slug": "",
        "primary_topic_label": "Duvidas",
        "topic_text": "duvidas",
        "topics": [],
        "sessions": [
            {"label": "duvidas aula"},
            {"label": "duvidas aula"},
            {"label": "gerencia de arquivos aula"},
        ],
    }
    assert classify_block(b) is BlockKind.OFFICE_HOURS
