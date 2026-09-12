

def test_headings_de_slide_deck_nao_param_no_oitavo():
    """FR 02-modelos (2026-09-01): slide-deck com 30+ headings — o limite de 8
    parava em "OSI - Camada de Redes" e "TCP/IP" (17o) ficava invisivel para o
    scorer; a subunit certa perdia por token ausente no campo forte."""
    from src.builder.extraction.entry_signals import collect_entry_unit_signals
    md = "\n".join(f"# Heading {i} tema{i}" for i in range(1, 21)) + "\n# TCP-IP arquitetura\n"
    signals = collect_entry_unit_signals({"title": "x", "category": "material-de-aula"}, md)
    assert "tema9" in signals["markdown_headings_text"]
    assert "arquitetura" in signals["markdown_headings_text"]
