from src.builder.core.code_summarization import code_curation_signal_text


def _curation_entry():
    return {
        "content_hash": "abc",
        "summary": {
            "inferred_title": "Verificação de Correção com Tripla de Hoare",
            "language": "dafny",
            "concepts": ["Tripla de Hoare", "Pré-condição", "Pós-condição"],
            "summary": "Exemplo em Dafny ilustra a verificação de um programa.",
        },
    }


def test_signal_text_uses_inferred_title_as_heading():
    text = code_curation_signal_text(_curation_entry())
    # título vira heading markdown (campo de maior peso no scorer de subunidade)
    assert text.splitlines()[0].startswith("# ")
    assert "Tripla de Hoare" in text.splitlines()[0]


def test_signal_text_includes_concepts_and_summary_and_language():
    text = code_curation_signal_text(_curation_entry())
    assert "Pré-condição" in text
    assert "Pós-condição" in text
    assert "verificação de um programa" in text
    assert "dafny" in text


def test_signal_text_empty_when_no_summary():
    assert code_curation_signal_text({}) == ""
    assert code_curation_signal_text({"summary": {}}) == ""
    assert code_curation_signal_text({"summary": {"language": ""}}) == ""


def test_signal_text_handles_missing_fields_gracefully():
    # só conceitos, sem título/summary/language
    entry = {"summary": {"concepts": ["Indução estrutural"]}}
    text = code_curation_signal_text(entry)
    assert "Indução estrutural" in text
    # sem título → não começa com heading vazio
    assert "# \n" not in text
