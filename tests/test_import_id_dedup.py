"""Testes TDD para o dedup de entry id (bug B5).

Comportamentos esperados (ver Task 10 do plano):
- 2 arquivos mesmo basename, categorias diferentes -> ids únicos com sufixo de categoria
- 3º mesmo id+categoria -> contador
- mesmo source_path -> fluxo already_exists intacto (não passa por _dedup_entry_id)
- dedup acontece ANTES do processamento (id_override no FileEntry): assets em
  disco (raw/, manual-review/, code/) ficam em paths distintos e unprocess de
  uma entry não remove arquivos da outra
"""
import json

from src.builder import engine as engine_module
from src.builder.ops.lifecycle_ops import _dedup_entry_id
from src.models.core import FileEntry


def test_ids_sem_colisao_retorna_original():
    existing = {"introducao", "aula-01"}
    assert _dedup_entry_id("introducao-slides", "slides", existing) == "introducao-slides"


def test_ids_duplicados_ganham_sufixo_de_categoria():
    # "introducao" existe (de outro source_path) -> ganha sufixo da categoria
    existing = {"introducao"}
    result = _dedup_entry_id("introducao", "codigo-professor", existing)
    assert result == "introducao-codigo-professor"
    assert result not in existing  # novo id nao colide


def test_ids_duplicados_categoria_vazia_ganha_contador():
    # sem categoria -> sufixo numérico
    existing = {"introducao"}
    result = _dedup_entry_id("introducao", "", existing)
    assert result == "introducao-2"


def test_mesmo_id_mesma_categoria_ganha_contador():
    # 3o arquivo "introducao" também codigo-professor (outra pasta)
    # -> "introducao-codigo-professor-2"
    existing = {"introducao", "introducao-codigo-professor"}
    result = _dedup_entry_id("introducao", "codigo-professor", existing)
    assert result == "introducao-codigo-professor-2"


def test_contador_incrementa_ate_livre():
    # varios ja existentes -> continua contando
    existing = {
        "introducao",
        "introducao-slides",
        "introducao-slides-2",
        "introducao-slides-3",
    }
    result = _dedup_entry_id("introducao", "slides", existing)
    assert result == "introducao-slides-4"


def test_categoria_slugificada():
    # categoria com espaços/maiúsculas é slugificada
    existing = {"introducao"}
    result = _dedup_entry_id("introducao", "Código Professor", existing)
    # slugify("Código Professor") -> "codigo-professor"
    assert result == "introducao-codigo-professor"


# ---------------------------------------------------------------------------
# id_override no FileEntry (mecanismo que leva o id deduplicado ao pipeline)
# ---------------------------------------------------------------------------


def test_id_override_substitui_id_computado():
    entry = FileEntry(source_path="/x/intro.py", file_type="code", category="codigo-professor", title="intro")
    assert entry.id() == "intro"
    entry.id_override = "intro-codigo-professor"
    assert entry.id() == "intro-codigo-professor"


def test_id_override_round_trip_to_dict_from_dict():
    entry = FileEntry(source_path="/x/intro.py", file_type="code", category="codigo-professor", title="intro")
    # vazio (default) -> omitido do dict
    assert "id_override" not in entry.to_dict()
    entry.id_override = "intro-2"
    d = entry.to_dict()
    assert d["id_override"] == "intro-2"
    assert FileEntry.from_dict(d).id() == "intro-2"


# ---------------------------------------------------------------------------
# Integração em disco: dedup ANTES do processamento -> assets distintos,
# unprocess isolado (cenário do bug B5)
# ---------------------------------------------------------------------------


def _code_entry(path, category):
    return FileEntry(
        source_path=str(path),
        file_type="code",
        category=category,
        title=path.stem,
    )


def _setup_two_same_basename_imports(tmp_path, monkeypatch):
    """2 arquivos `intro.py` em pastas/categorias diferentes, importados em série."""
    repo = tmp_path / "repo"
    file_a = tmp_path / "prof" / "intro.py"
    file_b = tmp_path / "aluno" / "intro.py"
    file_a.parent.mkdir(parents=True)
    file_b.parent.mkdir(parents=True)
    file_a.write_text("print('professor')", encoding="utf-8")
    file_b.write_text("print('aluno')", encoding="utf-8")

    builder = engine_module.RepoBuilder(
        repo, {"course_slug": "mf", "course_name": "Métodos Formais"}, [], {}
    )
    # Regeneração pedagógica é pesada e irrelevante para o dedup de assets.
    monkeypatch.setattr(builder, "_regenerate_pedagogical_files", lambda manifest: None)
    # Manifest mínimo pré-existente evita o bootstrap completo de root files
    # (_write_root_files exige course_meta completo, fora do escopo daqui).
    repo.mkdir()
    (repo / "manifest.json").write_text(
        json.dumps({"generated_at": "2026-01-01T00:00:00", "entries": [], "logs": []}),
        encoding="utf-8",
    )

    entry_a = _code_entry(file_a, "codigo-professor")
    entry_b = _code_entry(file_b, "codigo-aluno")
    assert builder._process_single_impl(entry_a) == "ok"
    assert builder._process_single_impl(entry_b) == "ok"

    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    return repo, builder, manifest


def test_disco_mesmo_basename_gera_paths_de_assets_distintos(tmp_path, monkeypatch):
    repo, _builder, manifest = _setup_two_same_basename_imports(tmp_path, monkeypatch)

    entries = manifest["entries"]
    assert len(entries) == 2
    rec_a = next(e for e in entries if e["category"] == "codigo-professor")
    rec_b = next(e for e in entries if e["category"] == "codigo-aluno")

    # ids únicos; o 2º ganhou o sufixo da categoria e persiste o override
    assert rec_a["id"] == "intro"
    assert rec_b["id"] == "intro-codigo-aluno"
    assert rec_b["id_override"] == "intro-codigo-aluno"
    assert "id_override" not in rec_a

    # todo path de asset/raw das 2 entries é DIFERENTE (sem sobrescrita)
    for key in ("raw_target", "base_markdown", "manual_review"):
        assert rec_a[key] != rec_b[key], key

    # arquivos em disco existem em paths distintos com o conteúdo certo
    assert (repo / rec_a["raw_target"]).read_text(encoding="utf-8") == "print('professor')"
    assert (repo / rec_b["raw_target"]).read_text(encoding="utf-8") == "print('aluno')"
    assert "print('professor')" in (repo / rec_a["base_markdown"]).read_text(encoding="utf-8")
    assert "print('aluno')" in (repo / rec_b["base_markdown"]).read_text(encoding="utf-8")
    assert (repo / rec_a["manual_review"]).exists()
    assert (repo / rec_b["manual_review"]).exists()

    # releitura do manifest via from_dict mantém o id deduplicado
    assert FileEntry.from_dict(rec_b).id() == "intro-codigo-aluno"
    assert FileEntry.from_dict(rec_a).id() == "intro"


def test_disco_unprocess_de_uma_entry_nao_remove_assets_da_outra(tmp_path, monkeypatch):
    repo, builder, manifest = _setup_two_same_basename_imports(tmp_path, monkeypatch)

    rec_a = next(e for e in manifest["entries"] if e["category"] == "codigo-professor")
    rec_b = next(e for e in manifest["entries"] if e["category"] == "codigo-aluno")

    assert builder.unprocess(rec_b["id"]) is True

    # assets da entry B removidos; assets da entry A intactos
    for key in ("base_markdown", "manual_review"):
        assert not (repo / rec_b[key]).exists(), key
        assert (repo / rec_a[key]).exists(), key
    assert (repo / rec_a["raw_target"]).exists()

    manifest_after = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    remaining = [e["id"] for e in manifest_after["entries"]]
    assert remaining == ["intro"]


# ---------------------------------------------------------------------------
# force-reprocess com entry deduplicada (fix bug B5 pela porta do force)
# ---------------------------------------------------------------------------


def _setup_two_deduped_imports(tmp_path, monkeypatch):
    """2 arquivos `intro.py` nas categorias codigo-professor / codigo-aluno.

    Reproduz o estado em que a segunda entry tem id_override no manifest:
      entries[0]: id="intro",               category="codigo-professor"
      entries[1]: id="intro-codigo-aluno",  category="codigo-aluno"
    """
    repo = tmp_path / "repo"
    file_a = tmp_path / "prof" / "intro.py"
    file_b = tmp_path / "aluno" / "intro.py"
    file_a.parent.mkdir(parents=True)
    file_b.parent.mkdir(parents=True)
    file_a.write_text("print('professor')", encoding="utf-8")
    file_b.write_text("print('aluno')", encoding="utf-8")

    builder = engine_module.RepoBuilder(
        repo, {"course_slug": "mf", "course_name": "Métodos Formais"}, [], {}
    )
    monkeypatch.setattr(builder, "_regenerate_pedagogical_files", lambda manifest: None)
    repo.mkdir()
    (repo / "manifest.json").write_text(
        json.dumps({"generated_at": "2026-01-01T00:00:00", "entries": [], "logs": []}),
        encoding="utf-8",
    )

    entry_a = _code_entry(file_a, "codigo-professor")
    entry_b = _code_entry(file_b, "codigo-aluno")
    assert builder._process_single_impl(entry_a) == "ok"
    assert builder._process_single_impl(entry_b) == "ok"

    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    return repo, builder, manifest, file_a, file_b


def test_force_reprocess_entry_deduplicada_remove_segunda_nao_primeira(tmp_path, monkeypatch):
    """force-reprocess do source_path da entry DEDUPLICADA (intro-codigo-aluno)
    deve remover apenas essa entry e deixar a primeira (intro) intacta.

    Antes do fix, `old_id = entry.id()` retornava "intro" (id base sem
    override), e `unprocess("intro")` removia a primeira entry — reintroduzindo
    o bug B5.
    """
    repo, builder, manifest, _file_a, file_b = _setup_two_deduped_imports(tmp_path, monkeypatch)

    rec_a = next(e for e in manifest["entries"] if e["category"] == "codigo-professor")
    rec_b = next(e for e in manifest["entries"] if e["category"] == "codigo-aluno")

    # Garante que a segunda entry está de fato deduplicada no manifest
    assert rec_a["id"] == "intro"
    assert rec_b["id"] == "intro-codigo-aluno"
    assert rec_b.get("id_override") == "intro-codigo-aluno"

    # FileEntry FRESCO (sem id_override) — simula o que chega via force-reprocess
    fresh_entry_b = _code_entry(file_b, "codigo-aluno")
    assert fresh_entry_b.id() == "intro"  # recomputa do source_path: id base

    result = builder._process_single_impl(fresh_entry_b, force=True)
    assert result == "ok"

    manifest_after = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ids_after = [e["id"] for e in manifest_after["entries"]]

    # A primeira entry (intro) deve permanecer intacta
    assert "intro" in ids_after, f"Entry 'intro' foi removida indevidamente; ids: {ids_after}"

    # assets da primeira entry ainda existem no disco
    assert (repo / rec_a["base_markdown"]).exists(), "base_markdown da entry A foi removido"
    assert (repo / rec_a["raw_target"]).exists(), "raw_target da entry A foi removido"
