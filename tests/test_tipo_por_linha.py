"""#52: tipo do bloco decidido por LINHA (rotulo cru + sinal do professor), medido no W-Y v3 (05/10)."""

import json

from src.builder.routing.motor import anchor_engine as ae
from src.builder.routing.motor.contracts import MotorContext
from src.builder.timeline.index import (
    _build_timeline_candidate_rows,
    _build_timeline_index,
    _reviews_demovidas_para_aula,
    ensure_block_kind,
)


def _row(descricao, atividade="Aula", data="03/03/2026"):
    return {"data": data, "descricao": descricao, "atividade": atividade}


def _kinds(*rows):
    return [r["kind"] for r in _build_timeline_candidate_rows(list(rows))]


def test_introducao_com_topico_e_aula_e_sozinha_e_overview():
    assert _kinds(_row("Introdução ao roteamento IP"), _row("ML - Introdução à ML"), _row("Introdução")) == [
        "class", "class", "overview"]


def test_apresentacao_da_disciplina_e_aula():
    # adjudicacao (3) de 05/10: overview deslocava 4 materiais do FR
    assert _kinds(_row("Apresentação da disciplina"), _row("Apresentação da disciplina e introdução")) == [
        "class", "class"]


def test_oficina_com_entrega_sob_aula_segue_workshop():
    # adjudicacao (2) revista em 05/10: como deliverable capturava 6 materiais do T2 (gold no bloco Trabalho)
    assert _kinds(_row("Oficina de problemas - Entrega T2")) == ["workshop"]


def test_prova_so_com_sinal_forte():
    assert _kinds(_row("Prova de teoremas"), _row("P1")) == ["class", "assessment"]


def test_atividade_vence_marcador():
    assert _kinds({"data": "03/07/2026", "descricao": "X {kind=holiday}", "atividade": "Prova"}) == ["assessment"]


def test_marcador_g2_sem_rotulo_e_prova_e_com_rotulo_comum_e_metadado():
    # P1(c), adjudicado em 05/10: rotulo vazio = o marcador decide (como hoje)
    assert _kinds(_row("{kind=g2}"), _row("Atendimento a dúvidas {kind=g2}", data="10/03/2026")) == [
        "assessment", "office_hours"]


def test_substituicao_na_atividade_e_makeup():
    assert _kinds(_row("Prova PS", "Prova de Substituição")) == ["makeup"]


def test_feriado_com_marcador_de_suspensao_e_feriado():
    assert _kinds(_row("Feriado {kind=suspension}")) == ["holiday"]


def test_duvidas_antes_da_prova_viram_review_em_cadeia():
    rows = _build_timeline_candidate_rows([
        _row("Dúvidas TP1", data="28/04/2026"), _row("Dúvidas P1", data="30/04/2026"),
        _row("Feriado", data="01/05/2026"), _row("Prova P1", "Prova", data="05/05/2026"),
        _row("Aula de dúvidas", data="10/05/2026"), _row("Entrega T1", "Trabalho", data="12/05/2026")])
    assert [r["kind"] for r in rows] == ["review", "review", "holiday", "assessment", "office_hours", "deliverable"]
    assert [bool(r.get("review_duvidas")) for r in rows] == [True, True, False, False, False, False]


def test_bloco_e_agregacao_das_linhas_e_override_vence():
    assert ensure_block_kind({"rows": [{"kind": "class"}, {"kind": "overview"}]})["kind"] == "overview"
    assert ensure_block_kind({"rows": [{"kind": "class"}]})["kind"] == "class"
    assert ensure_block_kind({"rows": [{"kind": "review"}], "manual_kind_override": "class"})["kind"] == "class"


def test_review_de_duvidas_marca_o_bloco_e_revisao_nao():
    rows = _build_timeline_candidate_rows([
        _row("Processos", data="02/03/2026"), _row("Dúvidas P1", data="09/03/2026"),
        _row("P1", "Prova", data="16/03/2026"), _row("Threads", data="23/03/2026"),
        _row("Revisão para a P2", data="30/03/2026"), _row("P2", "Prova", data="06/04/2026")])
    blocos = {b["id"]: b for b in _build_timeline_index(rows, unit_index=[])["blocks"]}
    assert blocos["bloco-02"]["kind"] == "review" and blocos["bloco-02"].get("review_from_office_hours")
    assert blocos["bloco-05"]["kind"] == "review" and not blocos["bloco-05"].get("review_from_office_hours")


def test_revisao_fora_da_vespera_volta_a_aula_antes_do_dp():
    # adjudicacao (4): review que o pos-processamento demove a aula entra no DP de unidades
    rows = _build_timeline_candidate_rows([
        _row("Lógica proposicional", data="02/03/2026"), _row("Revisão: lógica proposicional", data="09/03/2026"),
        _row("Lógica de predicados", data="16/03/2026"), _row("Revisão para a P1", data="23/03/2026"),
        _row("P1", "Prova", data="30/03/2026")])
    _reviews_demovidas_para_aula(rows, {}, [], None, None)
    assert [r["kind"] for r in rows] == ["class", "class", "class", "review", "assessment"]


def test_previa_aplica_a_curadoria_antes_de_decidir_a_democao(tmp_path):
    # revisao job-34: override da P1 para aula tira a vespera das duvidas; a previa precisa ver a curadoria
    (tmp_path / "course").mkdir()
    (tmp_path / "course" / ".timeline_curation.json").write_text(
        json.dumps({"version": 1, "blocks": {"bloco-03": {"manual_kind_override": "class"}}}), encoding="utf-8")

    def linhas():
        return _build_timeline_candidate_rows([
            _row("Processos", data="02/03/2026"), _row("Dúvidas P1", data="09/03/2026"),
            _row("P1", "Prova", data="16/03/2026"), _row("Threads", data="23/03/2026")])
    sem, com = linhas(), linhas()
    _reviews_demovidas_para_aula(sem, {}, [], None, None)
    _reviews_demovidas_para_aula(com, {"_repo_root": tmp_path}, [], None, None)
    assert sem[1]["kind"] == "review" and com[1]["kind"] == "class"


def test_ui_mostra_o_kind_gravado_pelo_indice():
    # revisao job-34: a UI recalculava pelo conteudo e contradizia o tipo por linha
    from src.ui.timeline_dashboard import block_kind
    gravado = {"kind": "class", "topic_text": "Introdução", "sessions": [{"label": "introducao"}]}
    assert block_kind(gravado) == "class"
    assert block_kind({**gravado, "manual_kind_override": "holiday"}) == "holiday"
    assert block_kind({"topic_text": "Feriado", "sessions": [{"label": "feriado"}]}) == "holiday"


def _ctx_review(marca):
    return MotorContext.from_artifacts(
        blocks=[{"id": "bloco-01", "kind": "class", "period_start": "2026-04-23"},
                {"id": "bloco-02", "kind": "review", "period_start": "2026-05-05", "review_from_office_hours": marca},
                {"id": "bloco-03", "kind": "assessment", "period_start": "2026-05-07",
                 "sessions": [{"label": "prova p1 prova"}]}],
        card_block_map={}, lessons_index={})


def test_prep_prova_pula_review_de_duvidas_e_para_na_aula():
    # H (W-Y v3): SO lista-exercicios-p1, gold na aula anterior ao "Duvidas TP1, duvidas p1"
    entry = {"id": "lista-exercicios-p1", "category": "listas", "source_section": "Informações Gerais"}
    assert ae.resolve_exam_prep(entry, _ctx_review(True)).block_ref == "bloco-01"
    assert ae.resolve_exam_prep(entry, _ctx_review(False)).block_ref == "bloco-02"
