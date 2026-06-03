from src.builder.extraction.entry_signals import collect_entry_unit_signals


def test_image_description_feeds_signal():
    entry = {
        "title": "diagram.png",
        "file_type": "image",
        "image_description": "Máquina de Turing com fita infinita e cabeçote",
        "auto_tags": [],
    }
    sig = collect_entry_unit_signals(entry, markdown_text="")
    assert "maquina de turing" in sig["image_description_text"]
    # descricao tambem entra no markdown_text efetivo p/ o scorer
    assert "turing" in sig["markdown_text"]


def test_no_image_description_is_empty():
    sig = collect_entry_unit_signals({"title": "x.pdf"}, markdown_text="conteudo")
    assert sig["image_description_text"] == ""
