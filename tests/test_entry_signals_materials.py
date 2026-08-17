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


def test_moodle_label_feeds_signal():
    # alavanca 1: o label do recurso Moodle vira canal proprio (identidade limpa)
    entry = {"title": "invariantes.zip",
             "moodle_label": "Exemplos (Logica de Floyd-Hoare)", "auto_tags": []}
    sig = collect_entry_unit_signals(entry, markdown_text="")
    assert "hoare" in sig["moodle_label_text"]
    assert "floyd" in sig["moodle_label_text"]


def test_no_moodle_label_is_empty():
    sig = collect_entry_unit_signals({"title": "x.pdf"}, markdown_text="")
    assert sig["moodle_label_text"] == ""


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


def test_exercise_notes_feed_signal():
    entry = {"title": "Lista 3.pdf", "category": "lista-de-exercicios",
             "notes": "exercicios sobre maquina de turing e decidibilidade",
             "auto_tags": []}
    sig = collect_entry_unit_signals(entry, markdown_text="")
    assert "decidibilidade" in sig["markdown_text"]


# ---------------------------------------------------------------------------
# S4b: ferramenta derivada da EXTENSÃO do arquivo (TOOL_EXTENSIONS) — movidos
# de test_block_scorer_signals.py no cutover passo 3 (única cobertura
# extensão→ferramenta; o scorer S2 daquele arquivo morreu com o funil).
# ---------------------------------------------------------------------------

def _entry_s4b(title, category="listas", auto_tags=None):
    return {"id": "e1", "title": title, "category": category,
            "manual_tags": [], "auto_tags": list(auto_tags or []), "tags": ""}


def test_ferramenta_por_extensao_thy_sem_auto_tags():
    """S4b: .thy SEM auto_tags ferramenta: deriva isabelle da EXTENSÃO do
    source_path — os .thy do manifest real não têm ferramenta:isabelle."""
    entry = _entry_s4b("intro")
    entry["source_path"] = "x/intro.thy"
    signals = collect_entry_unit_signals(entry, "")
    assert "isabelle" in signals["tool_tags_text"].split()


def test_ferramenta_por_extensao_dfy_via_raw_target():
    """S4b: a extensão também vale via raw_target (o harness do eval só
    repassa raw_target) e .dfy mapeia para dafny."""
    entry = _entry_s4b("exemplos")
    entry["raw_target"] = "Exemplos.DFY"
    signals = collect_entry_unit_signals(entry, "")
    assert "dafny" in signals["tool_tags_text"].split()


def test_ferramenta_extensao_uniao_com_auto_tags_dedupada():
    """União dos dois sinais, dedupada: auto_tag isabelle + .thy não duplica;
    extensão fora do mapa (.pdf) não acrescenta nada."""
    entry = _entry_s4b("intro", auto_tags=["ferramenta:isabelle"])
    entry["source_path"] = "x/intro.thy"
    signals = collect_entry_unit_signals(entry, "")
    assert signals["tool_tags_text"].split().count("isabelle") == 1
    entry_pdf = _entry_s4b("intro")
    entry_pdf["source_path"] = "x/intro.pdf"
    assert "tool" not in collect_entry_unit_signals(entry_pdf, "")["tool_tags_text"]
    assert collect_entry_unit_signals(entry_pdf, "")["tool_tags_text"] == ""
