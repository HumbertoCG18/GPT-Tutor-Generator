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


from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map


def test_markdown_fallback_uses_image_description(tmp_path):
    entry = {"id": "img1", "file_type": "image",
             "image_description": "Hierarquia de Chomsky e automatos"}
    # sem .md no disco -> deve cair na descricao de imagem
    txt = _entry_markdown_text_for_file_map(tmp_path, entry)
    assert "Chomsky" in txt


def test_markdown_real_md_takes_precedence(tmp_path):
    md = tmp_path / "x.md"
    md.write_text("conteudo real", encoding="utf-8")
    entry = {"id": "e", "base_markdown": "x.md", "image_description": "ignorar"}
    txt = _entry_markdown_text_for_file_map(tmp_path, entry)
    assert "conteudo real" in txt
