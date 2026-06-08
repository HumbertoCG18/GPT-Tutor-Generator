from src.builder.sources.moodle import sanitize_folder_name, iter_section_files, SectionFile, MoodleClient


def test_sanitize_removes_invalid_windows_chars():
    assert sanitize_folder_name("Avisos | Dúvidas | Notícias") == "Avisos Dúvidas Notícias"
    assert sanitize_folder_name("Revisão - Lógica/Especificação") == "Revisão - Lógica Especificação"
    assert sanitize_folder_name("  Provas por Indução. ") == "Provas por Indução"
    assert sanitize_folder_name("") == "sem-secao"


def test_iter_section_files_extracts_files_by_section():
    contents = [
        {"name": "Plano de Ensino", "modules": [
            {"contents": [{"type": "file", "filename": "plano.pdf", "fileurl": "https://m/pluginfile.php/1/plano.pdf"}]},
        ]},
        {"name": "Vazia", "modules": []},
        {"name": "Verificação de Programas", "modules": [
            {"contents": [
                {"type": "file", "filename": "hoare.pdf", "fileurl": "https://m/pluginfile.php/2/hoare.pdf"},
                {"type": "url", "filename": "link", "fileurl": "https://x"},  # ignora não-file
            ]},
        ]},
    ]
    files = iter_section_files(contents)
    assert SectionFile("Plano de Ensino", "plano.pdf", "https://m/pluginfile.php/1/plano.pdf") in files
    assert any(f.section == "Verificação de Programas" and f.filename == "hoare.pdf" for f in files)
    assert all(f.filename != "link" for f in files)   # url ignorado
    assert len(files) == 2


def test_download_url_appends_token():
    c = MoodleClient("https://moodle.pucrs.br/", "TOK")
    u1 = c._download_url("https://moodle.pucrs.br/webservice/pluginfile.php/1/a.pdf")
    assert "token=TOK" in u1
    # preserva query existente
    u2 = c._download_url("https://moodle.pucrs.br/webservice/pluginfile.php/1/a.pdf?forcedownload=1")
    assert "token=TOK" in u2 and "forcedownload=1" in u2
