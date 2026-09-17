import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.crosscheck_IA import (
    classify_crosscheck,
    crosscheck_rows,
    roteiro_block_for,
)


def test_roteiro_diverge_de_placement_sem_ancora_conf_baixa_acende_grave():
    # caso aula-29: sem card, sem ancora (anchored=False), roteiro aponta
    # bloco-05, funil chutou bloco-04 com conf 0.12. GRAVE.
    v = classify_crosscheck(
        card_blocks=[],
        roteiro_block="bloco-05",
        placement_block="bloco-04",
        anchored=False,
        computed_conf=0.12,
    )
    assert v.flagged is True
    assert v.severity == "grave"
    assert "roteiro!=placement:lowconf" in v.reasons


def test_placement_ancorado_nao_e_grave_mesmo_conf_baixa():
    # placement vem de temporal/manual (anchored=True) -> confiavel. roteiro
    # discorda -> no maximo AVISO, nunca grave (conf do computed e irrelevante).
    v = classify_crosscheck(
        card_blocks=[],
        roteiro_block="bloco-05",
        placement_block="bloco-04",
        anchored=True,
        computed_conf=0.12,
    )
    assert v.flagged is True
    assert v.severity == "aviso"
    assert "roteiro!=placement" in v.reasons


def test_card_diverge_do_roteiro_acende_aviso():
    # card (janela) diz {05}, roteiro (conteudo) diz 06, placement diz 05.
    v = classify_crosscheck(
        card_blocks=["bloco-05"],
        roteiro_block="bloco-06",
        placement_block="bloco-05",
        anchored=False,
        computed_conf=0.9,
    )
    assert v.flagged is True
    assert v.severity == "aviso"
    assert "card!=roteiro" in v.reasons


def test_todos_concordam_nao_acende():
    v = classify_crosscheck(
        card_blocks=["bloco-05"],
        roteiro_block="bloco-05",
        placement_block="bloco-05",
        anchored=True,
        computed_conf=0.9,
    )
    assert v.flagged is False
    assert v.reasons == []


def test_roteiro_block_for_casa_conteudo_com_data_da_sessao():
    blocks = [
        {"id": "bloco-04", "sessions": [{"date": "2026-03-12"}]},
        {"id": "bloco-05", "sessions": [{"date": "2026-04-08"}]},
    ]
    lessons_index = {"by_date": {
        "2026-03-12": "tipos de dados preparacao",
        "2026-04-08": "medidas de avaliacao acuracia precisao recall",
    }}
    signals = {
        "title_text": "Como analisar resultados Acc Pr Re F1",
        "moodle_label_text": "medidas de avaliacao",
    }
    assert roteiro_block_for(signals, blocks, lessons_index) == "bloco-05"


def test_roteiro_block_for_sem_overlap_retorna_vazio():
    blocks = [{"id": "bloco-01", "sessions": [{"date": "2026-03-02"}]}]
    lessons_index = {"by_date": {"2026-03-02": "apresentacao plano de ensino"}}
    signals = {"title_text": "Floyd Hoare logica", "moodle_label_text": ""}
    assert roteiro_block_for(signals, blocks, lessons_index) == ""


def test_crosscheck_rows_acende_no_caso_aula29():
    # duplicata sem card, sem temporal -> placement efetivo = computed (04),
    # roteiro=05, conf 0.12 -> GRAVE.
    blocks = [
        {"id": "bloco-04", "block_uuid": "uuid-04", "sessions": [{"date": "2026-03-12"}]},
        {"id": "bloco-05", "block_uuid": "uuid-05", "sessions": [{"date": "2026-04-08"}]},
    ]
    lessons_index = {"by_date": {
        "2026-03-12": "tipos de dados preparacao",
        "2026-04-08": "medidas de avaliacao acuracia precisao recall",
    }}
    u2d = {"uuid-04": "bloco-04", "uuid-05": "bloco-05"}
    entries = [
        {
            "id": "aula-29",
            "title": "Inteligencia Artificial Aula 29 - Medidas de avaliacao",
            "computed_block_id": "uuid-04",
            "computed_block_confidence": 0.12,
        },
        {
            "id": "kmeans",
            "title": "tipos de dados preparacao",
            "computed_block_id": "uuid-04",
            "computed_block_confidence": 0.9,
        },
    ]
    rows = crosscheck_rows(entries, blocks, card_map={}, lessons_index=lessons_index, u2d=u2d)
    ids = {r["id"]: r for r in rows}
    assert "aula-29" in ids
    assert ids["aula-29"]["severity"] == "grave"
    assert "roteiro!=placement:lowconf" in ids["aula-29"]["reasons"]
    assert ids["aula-29"]["roteiro"] == "bloco-05"
    assert ids["aula-29"]["placement"] == "bloco-04"
    assert ids["aula-29"]["anchored"] is False
    assert "kmeans" not in ids


def test_crosscheck_rows_placement_temporal_suprime_padrao_A():
    # caso agrupamento: temporal=06 (ancora) vence computed=07 (piso). roteiro=06.
    # placement efetivo = temporal = 06 = roteiro -> NAO flaga (Padrao A fantasma).
    blocks = [
        {"id": "bloco-06", "block_uuid": "uuid-06", "sessions": [{"date": "2026-04-08"}]},
        {"id": "bloco-07", "block_uuid": "uuid-07", "sessions": [{"date": "2026-04-20"}]},
    ]
    lessons_index = {"by_date": {
        "2026-04-08": "agrupamento hierarquico aglomerativo",
        "2026-04-20": "busca informada heuristica",
    }}
    u2d = {"uuid-06": "bloco-06", "uuid-07": "bloco-07"}
    entries = [{
        "id": "agrupamento",
        "title": "Agrupamento hierarquico exemplo",
        "temporal_block_id": "uuid-06",
        "computed_block_id": "uuid-07",
        "computed_block_confidence": 0.40,
    }]
    rows = crosscheck_rows(entries, blocks, card_map={}, lessons_index=lessons_index, u2d=u2d)
    assert rows == []
