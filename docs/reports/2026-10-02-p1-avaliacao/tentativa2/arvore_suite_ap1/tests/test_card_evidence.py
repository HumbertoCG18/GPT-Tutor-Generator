from src.builder.vision.card_evidence import extract_card_evidence


def test_extract_card_evidence_reads_card_title_as_topic_signal():
    text = "Card: Especificacoes Indutivas e Recursivas"

    items = extract_card_evidence(text)

    assert len(items) == 1
    assert items[0]["title"] == "Especificacoes Indutivas e Recursivas"
    assert items[0]["normalized_title"] == "especificacoes indutivas e recursivas"
    assert items[0]["source_kind"] == "card-title"


def test_extract_card_evidence_reads_topico_with_and_without_accent():
    text = "Topico: Provas por inducao\nTópico: Especificacoes recursivas"

    items = extract_card_evidence(text)

    assert [item["source_kind"] for item in items] == ["topic-title", "topic-title"]
    assert items[0]["normalized_title"] == "provas por inducao"
    assert items[1]["normalized_title"] == "especificacoes recursivas"


def test_extract_card_evidence_ignores_week_heading_without_card_label():
    text = "Semana 30/03/2026 a 03/04/2026: Especificacoes recursivas e provas por inducao"

    assert extract_card_evidence(text) == []
