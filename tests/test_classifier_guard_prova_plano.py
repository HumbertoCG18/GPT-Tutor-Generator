"""Guard anti-falso-exame: 'prova' vindo de rotulo de taxonomia/plano e
demonstracao, nao exame (caso real: TCC bloco-13, 'Prova da Indecidibilidade
do Problema da Parada' -> assessment indevido). Fixture copia contrato real
do bloco (ver institutional.md §Contratos; kind/period/campos conferidos no
.timeline_index.json real do TCC em 2026-08-06)."""
from src.builder.timeline.classifier import classify_block
from src.builder.timeline.kinds import BlockKind


def _bloco13_tcc(primary_topic_label):
    # Espelho do bloco real (TCC .timeline_index.json, bloco-13, conferido em disco):
    # sem source_kind, sem unit apos finalize (o cenario da taxonomia rica poe
    # o label contaminado e o positional pode nao ter setado unit ainda).
    return {
        "id": "bloco-13",
        "kind": "",
        "period_label": "1 dia · 24/04/2026",
        "topic_text": "problema da correspondencia de post",
        "primary_topic_label": primary_topic_label,
        "topics": [],
        "unit_slug": "",
        "auto_unit_slug": "",
        "sessions": [{"label": "problema da correspondencia de post aula", "kind": "class"}],
    }


def test_prova_de_demonstracao_no_label_nao_vira_assessment():
    b = _bloco13_tcc("Prova da Indecidibilidade do Problema da Parada")
    assert classify_block(b) is BlockKind.CLASS


def test_teste_nu_em_conteudo_nao_vira_assessment():
    b = _bloco13_tcc("Teste de mesa de algoritmos")
    assert classify_block(b) is BlockKind.CLASS


def test_exame_real_com_sinal_forte_segue_assessment_via_keyword():
    b = _bloco13_tcc("")
    b["topic_text"] = "prova p1 conteudo unidades 1 e 2"
    b["sessions"] = []
    assert classify_block(b) is BlockKind.ASSESSMENT  # regex \bp[1-4]\b e forte


def test_prova_n_segue_assessment():
    b = _bloco13_tcc("")
    b["topic_text"] = "prova 2 de sistemas"
    b["sessions"] = []
    assert classify_block(b) is BlockKind.ASSESSMENT  # "prova N" casa _STRONG_EXAM_RE
