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


from src.builder.core.reference_summary import process_reference_entry


def test_process_reference_entry_fills_fields():
    entry = {"id": "r1", "category": "referencias", "file_type": "github-repo",
             "source_path": "https://github.com/a/b", "auto_tags": []}
    units = [{"slug": "unidade-01", "normalized_title": "seguranca",
              "topic_phrases": ["autenticacao"], "topic_tokens": ["autenticacao"], "distinctive_tokens": ["oauth"]}]
    client = MagicMock()
    client.summarize_bundle.return_value = ReferenceSummary(
        inferred_title="t", summary="resumo base", concepts=["autenticacao", "oauth"])
    import src.builder.core.reference_summary as rs
    rs_fetch = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: "readme de autenticacao oauth"
        out = process_reference_entry(entry, units, client)
    finally:
        rs.fetch_reference_text = rs_fetch
    assert out["ref_summary"] == "resumo base"
    assert out["computed_ref_unit"] == "unidade-01"
    assert "oauth" in out["ref_concepts"]


def test_process_degrades_without_client():
    entry = {"id": "r1", "category": "referencias", "file_type": "github-repo",
             "source_path": "https://github.com/a/b"}
    units = [{"slug": "unidade-01", "normalized_title": "seguranca",
              "topic_phrases": ["autenticacao"], "topic_tokens": ["autenticacao"], "distinctive_tokens": ["oauth"]}]
    import src.builder.core.reference_summary as rs
    rs_fetch = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: "texto sobre autenticacao oauth"
        out = process_reference_entry(entry, units, None)  # sem Gemini
    finally:
        rs.fetch_reference_text = rs_fetch
    assert out["ref_summary"] == ""                 # sem resumo
    assert out["computed_ref_unit"] == "unidade-01" # mas mapeia por texto
