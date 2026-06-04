from unittest.mock import MagicMock
from src.builder.core.reference_summary import summarize_reference, ReferenceSummary


def test_returns_none_without_client():
    assert summarize_reference("algum texto", None) is None


def test_returns_none_on_empty_text():
    assert summarize_reference("   ", MagicMock()) is None


def test_returns_dict_with_summary_and_concepts():
    client = MagicMock()
    client.summarize_bundle.return_value = ReferenceSummary(
        inferred_title="Spring Security", summary="Framework de autenticacao.",
        concepts=["autenticacao", "oauth"],
    )
    out = summarize_reference("readme do spring security", client)
    assert out["summary"] == "Framework de autenticacao."
    assert out["concepts"] == ["autenticacao", "oauth"]


def test_returns_none_on_client_exception():
    client = MagicMock()
    client.summarize_bundle.side_effect = Exception("api down")
    assert summarize_reference("texto", client) is None
