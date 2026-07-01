from src.ui.timeline_dashboard import _entry_label


def test_label_usa_nome_do_arquivo_com_extensao():
    # distingue exemplos.thy de exemplos.zip (ids/stems iguais e ambíguos)
    assert _entry_label({
        "file_type": "zip",
        "source_path": "C:/x/Modelos Destaque/exemplos.zip",
        "title": "exemplos",
        "id": "exemplos-zip",
    }) == "exemplos.zip"
    assert _entry_label({
        "file_type": "code",
        "source_path": "/x/Provas/exemplos.thy",
        "title": "exemplos",
        "id": "exemplos",
    }) == "exemplos.thy"


def test_label_lida_com_backslash_windows():
    assert _entry_label({
        "file_type": "zip",
        "source_path": r"C:\Users\h\Verificacao de Programas\introducao.zip",
        "title": "Introducao",
        "id": "introducao-zip",
    }) == "introducao.zip"


def test_label_url_usa_titulo():
    assert _entry_label({
        "file_type": "url",
        "source_path": "https://example.com/pagina",
        "title": "Página X",
    }) == "Página X"


def test_label_fallback_id_quando_sem_source():
    assert _entry_label({"file_type": "pdf", "source_path": "", "title": "", "id": "intro"}) == "intro"
