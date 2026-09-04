from pathlib import Path
from src.builder.core.stash_import import scan_stash_cards, StashItem, build_stash_entries, filter_already_processed
from src.models.core import FileEntry


def _make_tree(root: Path):
    (root / "Verificacao de Programas").mkdir(parents=True)
    (root / "Verificacao de Programas" / "hoare.pdf").write_text("x", encoding="utf-8")
    (root / "Verificacao de Programas" / "hoare.zip").write_bytes(b"PK\x03\x04")
    (root / "Introducao").mkdir()
    (root / "Introducao" / "slides.pdf").write_text("x", encoding="utf-8")
    (root / "Introducao" / "foto.png").write_bytes(b"\x89PNG")
    (root / "solto.pdf").write_text("x", encoding="utf-8")
    (root / "leiame.txt").write_text("x", encoding="utf-8")  # ext desconhecida


def test_scan_groups_files_by_immediate_card(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}

    assert by_name["hoare.pdf"].card_name == "Verificacao de Programas"
    assert by_name["hoare.pdf"].file_type == "pdf"
    assert by_name["hoare.zip"].card_name == "Verificacao de Programas"
    assert by_name["hoare.zip"].file_type == "zip"
    assert by_name["slides.pdf"].card_name == "Introducao"
    assert by_name["foto.png"].file_type == "image"
    assert by_name["foto.png"].category == "fotos-de-prova"


def test_scan_root_level_file_has_empty_card(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}
    assert by_name["solto.pdf"].card_name == ""


def test_scan_skips_unknown_extensions(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    names = {Path(i.source_path).name for i in res.items}
    assert "leiame.txt" not in names
    assert any(Path(p).name == "leiame.txt" for p in res.skipped)


def test_scan_missing_root_returns_empty(tmp_path):
    res = scan_stash_cards(tmp_path / "nao-existe")
    assert res.items == []
    assert res.skipped == []


def test_build_entries_stamps_source_section_and_category(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    entries = build_stash_entries(scan, existing_source_paths=set(),
                                  defaults={"processing_mode": "auto", "ocr_language": "por"})
    by_name = {Path(e.source_path).name: e for e in entries}
    assert by_name["hoare.zip"].source_section == "Verificacao de Programas"
    assert by_name["hoare.zip"].category == "codigo-professor"
    assert by_name["hoare.zip"].file_type == "zip"
    assert by_name["hoare.zip"].title == "hoare"
    assert by_name["hoare.zip"].processing_mode == "auto"
    assert by_name["hoare.zip"].ocr_language == "por"
    assert all(isinstance(e, FileEntry) for e in entries)


def test_build_entries_is_idempotent_by_source_path(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    already = {i.source_path for i in scan.items if Path(i.source_path).name == "hoare.pdf"}
    entries = build_stash_entries(scan, existing_source_paths=already, defaults={})
    names = {Path(e.source_path).name for e in entries}
    assert "hoare.pdf" not in names      # já existia -> pulado
    assert "hoare.zip" in names          # novo -> incluído


def test_filter_already_processed_drops_known_basenames(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    filtered = filter_already_processed(scan, {"hoare.pdf", "slides.pdf"})
    names = {Path(i.source_path).name for i in filtered.items}
    assert "hoare.pdf" not in names
    assert "slides.pdf" not in names
    assert "hoare.zip" in names
    assert filtered.skipped == scan.skipped


def test_filter_already_processed_empty_backlog_is_noop(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    filtered = filter_already_processed(scan, set())
    assert len(filtered.items) == len(scan.items)


def test_scan_nested_file_uses_top_level_card(tmp_path):
    deep = tmp_path / "Provas por Inducao" / "resolucoes"
    deep.mkdir(parents=True)
    (deep / "q1.pdf").write_text("x", encoding="utf-8")
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}
    assert by_name["q1.pdf"].card_name == "Provas por Inducao"


def test_build_stash_entries_propagates_backend_and_datalab_defaults(tmp_path):
    # cria 1 arquivo num card
    card = tmp_path / "Verificacao de Programas"
    card.mkdir()
    (card / "hoare.pdf").write_bytes(b"%PDF-1.7 x")
    res = scan_stash_cards(tmp_path)
    entries = build_stash_entries(res, existing_source_paths=set(), defaults={
        "processing_mode": "high_fidelity",
        "preferred_backend": "datalab",
        "datalab_mode": "fast",
    })
    assert entries
    e = entries[0]
    assert e.preferred_backend == "datalab"
    assert e.datalab_mode == "fast"
    assert e.processing_mode == "high_fidelity"


def test_build_stash_entries_backend_defaults_when_absent(tmp_path):
    card = tmp_path / "Introducao"
    card.mkdir()
    (card / "x.pdf").write_bytes(b"%PDF-1.7 x")
    res = scan_stash_cards(tmp_path)
    entries = build_stash_entries(res, existing_source_paths=set(), defaults={})
    assert entries[0].preferred_backend == "auto"
    assert entries[0].datalab_mode == "accurate"


def test_dfy_and_thy_classify_as_code_for_gemini(tmp_path):
    # Código (Dafny .dfy / Isabelle .thy) deve virar file_type "code" -> caminho
    # Gemini, NUNCA extração PDF/datalab.
    card = tmp_path / "Verificacao de Programas"
    card.mkdir()
    (card / "hoare.dfy").write_text("method M() {}", encoding="utf-8")
    (card / "arvores.thy").write_text("theory T begin end", encoding="utf-8")
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}
    assert by_name["hoare.dfy"].file_type == "code"
    assert by_name["arvores.thy"].file_type == "code"


def test_build_stash_entries_code_and_zip_never_inherit_backend(tmp_path):
    # Mesmo com default datalab, código/zip ficam "auto" (vão pro Gemini, não datalab).
    card = tmp_path / "Verificacao de Programas"
    card.mkdir()
    (card / "hoare.dfy").write_text("method M(){}", encoding="utf-8")
    (card / "exs.zip").write_bytes(b"PK\x03\x04zip")
    (card / "aula.pdf").write_bytes(b"%PDF-1.7 x")
    res = scan_stash_cards(tmp_path)
    entries = {Path(e.source_path).name: e for e in build_stash_entries(
        res, existing_source_paths=set(),
        defaults={"preferred_backend": "datalab", "datalab_mode": "fast"})}
    assert entries["hoare.dfy"].preferred_backend == "auto"
    assert entries["exs.zip"].preferred_backend == "auto"
    assert entries["aula.pdf"].preferred_backend == "datalab"   # PDF herda


def test_build_stash_entries_propagates_document_profile_pdf_only(tmp_path):
    card = tmp_path / "Aulas"
    card.mkdir()
    (card / "a.pdf").write_bytes(b"%PDF-1.7 x")
    (card / "x.dfy").write_text("method M(){}", encoding="utf-8")
    res = scan_stash_cards(tmp_path)
    entries = {Path(e.source_path).name: e for e in build_stash_entries(
        res, existing_source_paths=set(), defaults={"document_profile": "math_heavy"})}
    assert entries["a.pdf"].document_profile == "math_heavy"   # pdf herda
    assert entries["x.dfy"].document_profile == "auto"          # código não


class TestF10_NomeDoModuloNoSidecar:
    """F10: .moodle_nomes.json ("card/arquivo" -> nome do modulo) refina a categoria;
    sem sidecar, comportamento identico ao de antes."""

    def _monta(self, tmp_path, sidecar=None):
        card = tmp_path / "U1 - Redes de Computadores"
        card.mkdir(parents=True)
        (card / "03 - Tipos de Redes.pdf").write_bytes(b"%PDF")
        (card / "aula03 - buildroot-intro.pdf").write_bytes(b"%PDF")
        if sidecar is not None:
            import json
            (tmp_path / ".moodle_nomes.json").write_text(json.dumps(sidecar), encoding="utf-8")
        from src.builder.core.stash_import import scan_stash_cards
        return {i.source_path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]: i.category
                for i in scan_stash_cards(tmp_path).items}

    def test_modulo_com_slides_vira_material(self, tmp_path):
        cats = self._monta(tmp_path, sidecar={
            "U1 - Redes de Computadores/03 - Tipos de Redes.pdf": "Tipos de Redes (Slides)"})
        assert cats["03 - Tipos de Redes.pdf"] == "material-de-aula"

    def test_arquivo_aula_vence_modulo_livro(self, tmp_path):
        """Lab SO: modulo "Livro-texto: Buildroot", arquivo "aula03 - ..." -> material
        (cue "aula" vem antes de "livro" na ordem de prioridade)."""
        cats = self._monta(tmp_path, sidecar={
            "U1 - Redes de Computadores/aula03 - buildroot-intro.pdf": "Livro-texto: Buildroot"})
        assert cats["aula03 - buildroot-intro.pdf"] == "material-de-aula"

    def test_sem_sidecar_comportamento_antigo(self, tmp_path):
        cats = self._monta(tmp_path, sidecar=None)
        assert cats["03 - Tipos de Redes.pdf"] == "outros"
        assert cats["aula03 - buildroot-intro.pdf"] == "material-de-aula"


def test_tar_gz_e_classificado_como_zip_no_scan(tmp_path):
    """FR 2026/2 (P3, 01/09): 5 tar.gz de codigo-exemplo (tcp_example.tar.gz)
    eram pulados por extensao desconhecida — path.suffix de '.tar.gz' e so
    '.gz', o classificador nunca via o duplo sufixo."""
    from src.builder.core.stash_import import scan_stash_cards
    card = tmp_path / "U2 - Camada de Aplicação"
    card.mkdir()
    (card / "tcp_example.tar.gz").write_bytes(b"x")
    (card / "udp_example.tgz").write_bytes(b"x")
    (card / "lixo.rar").write_bytes(b"x")
    scan = scan_stash_cards(tmp_path)
    tipos = {Path(i.source_path).name: i.file_type for i in scan.items}
    assert tipos.get("tcp_example.tar.gz") == "zip"
    assert tipos.get("udp_example.tgz") == "zip"
    assert (card / "lixo.rar").as_posix() in [Path(s).as_posix() for s in scan.skipped]
    # convencao do zip: codigo do professor
    cats = {Path(i.source_path).name: i.category for i in scan.items}
    assert cats["tcp_example.tar.gz"] == "codigo-professor"


def test_process_zip_extrai_tar_gz(tmp_path, monkeypatch):
    """process_zip decide o formato por CONTEUDO (is_zipfile -> is_tarfile):
    o raw_target do tar.gz pode chegar nomeado so '.gz'."""
    import tarfile
    from types import SimpleNamespace
    from src.builder.core import source_importers as si
    from src.models.core import FileEntry

    fonte = tmp_path / "pkg"
    fonte.mkdir()
    (fonte / "servidor.py").write_text("print('tcp')\n", encoding="utf-8")
    alvo = tmp_path / "tcp_example.gz"  # nome truncado de proposito
    with tarfile.open(alvo, "w:gz") as tf:
        tf.add(fonte / "servidor.py", arcname="pkg/servidor.py")

    vistos = []
    monkeypatch.setattr(si, "process_code", lambda b, e, p: vistos.append(e.title) or {"id": e.id()})
    builder = SimpleNamespace(root_dir=tmp_path / "repo", logs=[])
    (tmp_path / "repo").mkdir()
    entry = FileEntry(source_path=str(alvo), file_type="zip", category="codigo-professor", title="tcp_example")
    item = si.process_zip(builder, entry, alvo)
    assert item["extraction_error"] is None
    assert item["file_count"] == 1


def test_id_de_tar_gz_nao_carrega_tar():
    """FileEntry.id() = slugify(stem do source_path); para 'x.tar.gz' o stem e
    'x.tar' e o id herdava o tar (tcp-chat-ctar)."""
    from src.models.core import FileEntry
    e = FileEntry(source_path=r"C:\stash\tcp_chat_c.tar.gz", file_type="zip",
                  category="codigo-professor", title="tcp_chat_c")
    assert e.id() == "tcp-chat-c"


def test_scan_classifies_html_pages_as_material_not_code(tmp_path):
    # SYNC S6b (03/09): paginas do professor (Curvas.htm) e do Moodle (.html) salvas no stash sao MATERIAL.
    # `.html` esta em CODE_EXTENSIONS (virava codigo-professor sem texto; por isso o pull imprimia PDF)
    # e `.htm` era ignorado.
    card = tmp_path / "7 - Curvas Parametricas"
    card.mkdir()
    (card / "Curvas.htm").write_text("<p>x</p>", encoding="utf-8")
    (card / "exercicios-sobre-curvas.html").write_text("<p>x</p>", encoding="utf-8")
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}
    assert by_name["Curvas.htm"].file_type == "html"
    assert by_name["Curvas.htm"].category == "outros"
    assert by_name["exercicios-sobre-curvas.html"].file_type == "html"
    assert by_name["exercicios-sobre-curvas.html"].category == "listas"
    assert res.skipped == []


def test_scan_treats_page_bundle_dir_as_one_html_item(tmp_path):
    # S6d: snapshot grava `stash/<card>/<Pagina>/<Pagina>.htm` + imagens (Curvas.fld/, irmas). As imagens do bundle
    # sao da pagina, nao itens (antes virariam entries `image`/fotos-de-prova). PDF e .html soltos no card seguem itens.
    card = tmp_path / "7 - Curvas Parametricas"
    (card / "Curvas" / "Curvas.fld").mkdir(parents=True)
    (card / "Curvas" / "Curvas.htm").write_text("<p>x</p>", encoding="utf-8")
    (card / "Curvas" / "Image1.gif").write_bytes(b"GIF89a")
    (card / "Curvas" / "Curvas.fld" / "image003.gif").write_bytes(b"GIF89a")
    (card / "slides.pdf").write_text("x", encoding="utf-8")
    (card / "exercicios.html").write_text("<p>x</p>", encoding="utf-8")
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}
    assert set(by_name) == {"Curvas.htm", "slides.pdf", "exercicios.html"}
    assert by_name["Curvas.htm"].file_type == "html" and by_name["Curvas.htm"].card_name == "7 - Curvas Parametricas"
    assert res.skipped == []
