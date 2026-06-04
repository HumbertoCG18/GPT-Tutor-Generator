from src.builder.core.reference_topic import assign_concepts_to_unit


def _units():
    return [
        {"slug": "unidade-01-seguranca", "normalized_title": "seguranca de aplicacoes",
         "topic_phrases": ["autenticacao", "autorizacao", "spring security"],
         "topic_tokens": ["autenticacao", "autorizacao", "seguranca"], "distinctive_tokens": ["oauth"]},
        {"slug": "unidade-02-microservicos", "normalized_title": "microservicos",
         "topic_phrases": ["service discovery", "api gateway"],
         "topic_tokens": ["microservico", "discovery", "gateway"], "distinctive_tokens": ["eureka"]},
    ]


def test_maps_concepts_to_matching_unit():
    out = assign_concepts_to_unit(["service discovery", "eureka registry"], "", _units())
    assert out["unit_slug"] == "unidade-02-microservicos"
    assert out["confidence"] > 0.0


def test_no_match_returns_empty_slug():
    out = assign_concepts_to_unit(["fotossintese", "mitocondria"], "", _units())
    assert out["unit_slug"] == ""


def test_falls_back_to_text_when_no_concepts():
    out = assign_concepts_to_unit([], "tutorial de spring security e autenticacao", _units())
    assert out["unit_slug"] == "unidade-01-seguranca"


def test_empty_everything_returns_empty():
    out = assign_concepts_to_unit([], "", _units())
    assert out["unit_slug"] == ""
    assert out["topics"] == []
