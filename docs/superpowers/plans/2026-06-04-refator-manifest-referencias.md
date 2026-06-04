# Rodada de Refatoração: Manifest enxuto + Referências curation-only

> **For agentic workers:** TDD task-by-task. Steps use `- [ ]`.

**Goal:** Fechar a verbosidade do manifest antes do PR para a main. (Opção 2) Mover os campos `ref_*` para `references_curation.json` apenas — como os resumos de código vivem só em `code_curation.json` — desfazendo o hack de reload do manifest e tirando 4 campos de toda entry. (Opção 1) `FileEntry.to_dict` passa a omitir campos iguais ao default, encolhendo toda entry.

**Architecture:** `bibliography_md` espelha `code_health_md`: recebe a curation e lê por `entry.id()`, em vez de ler atributos `ref_*` do objeto entry. O batch grava só a curation. `FileEntry.to_dict` filtra defaults (required sempre presentes; opcionais só se != default).

**Tech Stack:** Python 3, pytest, dataclasses.

## Fatos verificados (confie)

- `bibliography_md(course_meta, entries=None, subject_profile=None, *, parse_bibliography_from_teaching_plan_fn, clamp_navigation_artifact)` em `src/builder/artifacts/repo.py:654`. Hoje lê `getattr(entry, "ref_summary"|"computed_ref_unit"|"computed_ref_topics")`.
- Padrão a espelhar: `code_health_md(course_meta, entries, code_curation, ...)` (repo.py:1043) faz `curation_entries = (code_curation or {}).get("entries", {})` e `curation_entries.get(e.id())`.
- Call site da bibliografia: `pedagogical_regeneration.py:296-301`. `bib_entries` são `FileEntry` (`all_entries = [FileEntry.from_dict(e) ...]`, linha 278) — têm `.id()`. O `bibliography_md_fn` é partial com os 2 kwargs já bound; novo param com default não quebra a partial.
- `load_reference_curation(repo_dir) -> {"entries": {...}}` já existe em `reference_summary.py`. Curation keyed por `entry id` (manifest `entry.get("id")`, que == `FileEntry.id()`).
- `summarize_all_reference_entries(builder, units, client, progress_cb)` hoje atualiza manifest.json E references_curation.json. Vamos remover a escrita do manifest.
- Hack de reload a remover: `build_workflow.py`, linha após `_run_auto_code_summarization(builder, logger)` — `manifest = json.loads(manifest_path.read_text(...))` com comentário "Recarrega: o enriquecimento de referencias grava...".
- Campos a remover de `FileEntry` (`src/models/core.py:90-93`): `ref_summary`, `ref_concepts`, `computed_ref_unit`, `computed_ref_topics`.
- `FileEntry.to_dict` = `asdict(self)` (core.py:103-104). Campos required (sem default): `source_path`, `file_type`, `category`, `title`.

---

## Task 1: `bibliography_md` lê da curation (não do entry)

**Files:** Modify `src/builder/artifacts/repo.py`; Test `tests/test_reference_bibliography.py`.

- [ ] **Step 1: Reescrever o teste** para passar a curation keyed por id e entries com `.id()`.

Substituir o conteúdo de `tests/test_reference_bibliography.py` por:

```python
from src.builder.artifacts.repo import bibliography_md


class _Entry:
    def __init__(self, **kw):
        d = dict(title="GitHub - a/b", source_path="https://github.com/a/b", tags="",
                 notes="", professor_signal="", include_in_bundle=True, category="bibliografia")
        d.update(kw)
        self.__dict__.update(d)

    def id(self):
        return self.__dict__.get("_id", "ref-ab")


def _bib(entries, reference_curation=None):
    return bibliography_md(
        {"course_name": "Eng Soft"}, entries=entries, subject_profile=None,
        reference_curation=reference_curation,
        parse_bibliography_from_teaching_plan_fn=lambda t: {},
        clamp_navigation_artifact=lambda s, **k: s,
    )


def _curation(entry_id="ref-ab", **rec):
    base = dict(ref_summary="", computed_ref_unit="", computed_ref_topics=[])
    base.update(rec)
    return {"entries": {entry_id: base}}


def test_renders_summary_when_present():
    md = _bib([_Entry()], _curation(ref_summary="Framework de autenticacao.",
                                    computed_ref_unit="unidade-01-seguranca",
                                    computed_ref_topics=["autenticacao"]))
    assert "Framework de autenticacao." in md
    assert "unidade-01-seguranca" in md


def test_no_summary_line_when_absent():
    md = _bib([_Entry()], _curation())
    assert "**Resumo:**" not in md
    assert "https://github.com/a/b" in md  # ainda surfacea URL


def test_relevance_map_lists_mapped_reference():
    md = _bib([_Entry(title="Spring Sec")], _curation(computed_ref_unit="unidade-01-seguranca",
                                                      computed_ref_topics=["autenticacao"]))
    assert "[a preencher]" not in md
    assert "Spring Sec" in md


def test_no_curation_renders_url_only():
    md = _bib([_Entry()], None)  # sem curation -> degrada
    assert "**Resumo:**" not in md
    assert "[a preencher]" in md  # mapa volta a placeholder
    assert "https://github.com/a/b" in md
```

- [ ] **Step 2:** `python -m pytest tests/test_reference_bibliography.py -v` — FAIL (param `reference_curation` não existe; render lê do entry).

- [ ] **Step 3: Editar `bibliography_md`** (repo.py:654). Adicionar o param e ler da curation.

Na assinatura, após `subject_profile=None,` e antes de `*,` inserir nada; adicionar como keyword-only. Trocar a assinatura para:

```python
def bibliography_md(
    course_meta: dict,
    entries=None,
    subject_profile=None,
    *,
    reference_curation: dict | None = None,
    parse_bibliography_from_teaching_plan_fn: Callable[[str], dict],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
```

Logo após `entries = entries or []` adicionar:

```python
    _ref_entries = (reference_curation or {}).get("entries", {})

    def _rec(entry):
        try:
            return _ref_entries.get(entry.id()) or {}
        except Exception:
            return {}
```

No laço `for entry in entries:`, trocar o bloco que lê `getattr(entry, "ref_summary"...)`/`computed_ref_unit`/`computed_ref_topics` por:

```python
            rec = _rec(entry)
            ref_summary = rec.get("ref_summary") or ""
            if ref_summary:
                lines.append(f"- **Resumo:** {ref_summary}")
            ref_unit = rec.get("computed_ref_unit") or ""
            ref_topics = rec.get("computed_ref_topics") or []
            if ref_unit or ref_topics:
                rel = ref_unit + (f" / {', '.join(ref_topics)}" if ref_topics else "")
                lines.append(f"- **Relevante para:** {rel}")
```

Trocar o bloco do mapa de relevância (`mapped = [e for e in entries if (getattr(e, ...))]` … até o `else`) por:

```python
    mapped = [(e, _rec(e)) for e in entries]
    mapped = [(e, r) for (e, r) in mapped if (r.get("computed_ref_unit") or r.get("computed_ref_topics"))]
    lines += ["## Mapa de relevância por tópico", ""]
    if mapped:
        lines += ["| Tópico/Unidade | Referência | Acessível | Incidência em prova |", "|---|---|---|---|"]
        for e, r in mapped:
            unit = r.get("computed_ref_unit") or ""
            topics = ", ".join(r.get("computed_ref_topics") or [])
            alvo = " / ".join([p for p in (unit, topics) if p]) or "—"
            lines.append(f"| {alvo} | {e.title} | sim | — |")
        lines.append("")
    else:
        lines += ["<!-- Preencha após organizar as referências -->", "",
                  "| Tópico | Referência principal | Acessível | Incidência em prova |",
                  "|---|---|---|---|", "| [a preencher] | | | |", ""]
```

- [ ] **Step 4:** `python -m pytest tests/test_reference_bibliography.py -v` — 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_reference_bibliography.py
git commit -m "refactor(reference): bibliography_md reads ref data from curation, not entry"
```

---

## Task 2: batch grava só `references_curation.json`

**Files:** Modify `src/builder/core/reference_summary.py`; Test `tests/test_reference_summary.py`.

- [ ] **Step 1: Ajustar o teste de cache** para asseverar que o manifest NÃO é tocado e a curation guarda os campos.

Substituir `test_batch_caches_by_hash` em `tests/test_reference_summary.py` por:

```python
def test_batch_writes_only_curation(tmp_path):
    import json as _json
    from src.builder.core import reference_summary as rs
    root = tmp_path
    (root / "course").mkdir()
    manifest_blob = _json.dumps({"entries": [
        {"id": "r1", "category": "referencias", "file_type": "github-repo",
         "source_path": "https://github.com/a/b"}]})
    (root / "manifest.json").write_text(manifest_blob, encoding="utf-8")
    builder = type("B", (), {"root_dir": root})()
    units = [{"slug": "u1", "normalized_title": "x", "topic_phrases": [], "topic_tokens": [], "distinctive_tokens": []}]
    client = MagicMock()
    client.summarize_bundle.return_value = ReferenceSummary(inferred_title="t", summary="s", concepts=["c"])
    orig = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: "texto fixo"
        rs.summarize_all_reference_entries(builder, units, client)
        rs.summarize_all_reference_entries(builder, units, client)  # 2a vez: cache
    finally:
        rs.fetch_reference_text = orig
    # resumiu só 1x (cache por hash)
    assert client.summarize_bundle.call_count == 1
    # manifest.json intocado (sem campos ref_*)
    assert (root / "manifest.json").read_text(encoding="utf-8") == manifest_blob
    # curation guarda o resultado
    cur = _json.loads((root / "course" / "references_curation.json").read_text(encoding="utf-8"))
    assert cur["entries"]["r1"]["ref_summary"] == "s"
```

- [ ] **Step 2:** `python -m pytest tests/test_reference_summary.py -k curation -v` — FAIL (manifest é reescrito hoje).

- [ ] **Step 3: Reescrever `summarize_all_reference_entries`** — remover toda leitura/escrita de campos no manifest; gravar só a curation. Substituir o corpo da função por:

```python
def summarize_all_reference_entries(builder, units: list, client, progress_cb=None) -> dict:
    """Processa entries de referência do manifest e grava SÓ references_curation.json
    (keyed por entry id). NÃO escreve o manifest — os campos ref vivem só na
    curation, como os resumos de código em code_curation.json. Cache por hash.
    Sem client -> mapeia por texto, sem resumo."""
    manifest_path = Path(builder.root_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    curation = load_reference_curation(builder.root_dir)
    cache = curation.setdefault("entries", {})

    refs = [e for e in manifest.get("entries", [])
            if str(e.get("category") or "").lower() in _REFERENCE_CATEGORIES]
    for idx, entry in enumerate(refs):
        eid = entry.get("id")
        if not eid:
            continue
        text = fetch_reference_text(entry)
        h = _ref_hash(entry, text)
        existing = cache.get(eid, {})
        if (existing.get("content_hash") == h
                and existing.get("matcher_version") == REFERENCE_MATCHER_VERSION
                and (existing.get("ref_summary") or client is None)):
            if progress_cb:
                progress_cb(idx, len(refs), entry.get("title", ""), "cached")
            continue
        summary_dict = summarize_reference(text, client)
        concepts = (summary_dict or {}).get("concepts", []) or []
        fallback = " ".join([str(entry.get("title", "") or ""), text])
        topic = assign_concepts_to_unit(concepts, fallback, units)
        cache[eid] = {
            "ref_summary": (summary_dict or {}).get("summary", "") or "",
            "ref_concepts": concepts,
            "computed_ref_unit": topic["unit_slug"],
            "computed_ref_topics": topic["topics"],
            "content_hash": h,
            "matcher_version": REFERENCE_MATCHER_VERSION,
        }
        if progress_cb:
            progress_cb(idx, len(refs), entry.get("title", ""), "ok")

    write_reference_curation(builder.root_dir, curation)
    return curation
```

(Não reescreve `manifest_path`. Mantém imports `json`, `hashlib`, `Path` já presentes.)

- [ ] **Step 4:** `python -m pytest tests/test_reference_summary.py -v` — todos PASS.

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/reference_summary.py tests/test_reference_summary.py
git commit -m "refactor(reference): batch writes only references_curation.json (not manifest)"
```

---

## Task 3: tirar `ref_*` do FileEntry, remover reload, wirar curation na bibliografia

**Files:** Modify `src/models/core.py`, `src/builder/ops/build_workflow.py`, `src/builder/ops/pedagogical_regeneration.py`.

- [ ] **Step 1: Remover os 4 campos de `FileEntry`** (`src/models/core.py:88-93`). Apagar o bloco:

```python
    # Campos de referência bibliográfica (Task 6). Resumo lazy via Gemini e
    # mapeamento determinístico unidade/tópico persistidos no manifest.json.
    ref_summary: str = ""
    ref_concepts: List[str] = field(default_factory=list)
    computed_ref_unit: str = ""
    computed_ref_topics: List[str] = field(default_factory=list)
```

`from_dict` filtra chaves desconhecidas — manifests legados com `ref_*` carregam sem erro (chaves descartadas).

- [ ] **Step 2: Remover o hack de reload** em `src/builder/ops/build_workflow.py`. Apagar:

```python
    # Recarrega: o enriquecimento de referencias grava ref_summary/computed_ref_*
    # direto no manifest.json em disco. Sem reload, a regeneracao pedagogica e a
    # escrita final (abaixo) usariam o manifest em memoria sem esses campos.
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
```

(deixar `_run_auto_code_summarization(builder, logger)` seguido direto de `builder._resolve_content_images()`.)

- [ ] **Step 3: Wirar a curation no call site da bibliografia** (`pedagogical_regeneration.py:296-301`). Trocar por:

```python
    bib_entries = [e for e in all_entries if e.category == "bibliografia"]
    if bib_entries or getattr(builder.subject_profile, "teaching_plan", ""):
        from src.builder.core.reference_summary import load_reference_curation
        write_text(
            builder.root_dir / "content" / "BIBLIOGRAPHY.md",
            bibliography_md_fn(
                builder.course_meta, bib_entries, builder.subject_profile,
                reference_curation=load_reference_curation(builder.root_dir),
            ),
        )
```

- [ ] **Step 4: Rodar a suíte inteira** — `python -m pytest tests -q`. Esperado: verde (os testes de reference já cobrem a nova forma; nenhum teste depende dos campos `ref_*` em FileEntry — se algum quebrar, é consumidor real, reporte).

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py src/builder/ops/build_workflow.py src/builder/ops/pedagogical_regeneration.py
git commit -m "refactor(reference): drop ref_* from FileEntry; wire curation into bibliography"
```

---

## Task 4 (Opção 1): `FileEntry.to_dict` omite defaults

**Files:** Modify `src/models/core.py`; Test `tests/test_file_entry_serialization.py`.

- [ ] **Step 1: Teste** — criar `tests/test_file_entry_serialization.py`:

```python
from src.models.core import FileEntry


def _minimal():
    return FileEntry(source_path="raw/x.pdf", file_type="pdf", category="material", title="X")


def test_required_fields_always_present():
    d = _minimal().to_dict()
    for k in ("source_path", "file_type", "category", "title"):
        assert k in d


def test_default_valued_fields_omitted():
    d = _minimal().to_dict()
    # campos opcionais iguais ao default não devem aparecer
    assert "ocr_language" not in d
    assert "force_ocr" not in d
    assert "auto_tags" not in d
    assert "notes" not in d


def test_non_default_fields_kept():
    e = _minimal()
    e.notes = "revisar"
    e.force_ocr = True
    d = e.to_dict()
    assert d["notes"] == "revisar"
    assert d["force_ocr"] is True


def test_round_trip_through_from_dict():
    e = _minimal()
    e.notes = "n"
    e.manual_tags = ["a"]
    again = FileEntry.from_dict(e.to_dict())
    assert again.notes == "n"
    assert again.manual_tags == ["a"]
    assert again.ocr_language == _minimal().ocr_language  # default reaparece
```

- [ ] **Step 2:** `python -m pytest tests/test_file_entry_serialization.py -v` — FAIL (`asdict` inclui tudo).

- [ ] **Step 3: Reescrever `to_dict`** (core.py:103-104):

```python
    def to_dict(self) -> Dict:
        from dataclasses import fields as _fields, MISSING
        full = asdict(self)
        out: Dict = {}
        for f in _fields(self):
            val = full[f.name]
            if f.default is not MISSING:
                default = f.default
            elif f.default_factory is not MISSING:  # type: ignore[misc]
                default = f.default_factory()       # type: ignore[misc]
            else:
                out[f.name] = val  # required: sempre presente
                continue
            if val != default:
                out[f.name] = val
        return out
```

- [ ] **Step 4:** `python -m pytest tests/test_file_entry_serialization.py -v` — PASS.

- [ ] **Step 5: Suíte inteira** — `python -m pytest tests -q`. Se algum teste/consumidor ler uma chave omitida sem `.get`, ele falha aqui: reporte o local (é um consumidor que assume todas as chaves presentes) — NÃO reverter sem antes mostrar o ponto.

- [ ] **Step 6: Commit**

```bash
git add src/models/core.py tests/test_file_entry_serialization.py
git commit -m "refactor(model): FileEntry.to_dict omits default-valued fields (slim manifest)"
```

---

## Self-Review

**Cobertura:** Opção 2 = T1 (render lê curation) + T2 (batch só curation) + T3 (remove campos/reload/wire). Opção 1 = T4 (to_dict omit-defaults). ✓
**Round-trip:** `from_dict` filtra chaves desconhecidas e defaults preenchem ausentes → T3 e T4 seguros. ✓
**Consistência:** chave da curation = `entry.id()` em T1 (render) e batch grava por `entry.get("id")` (== `FileEntry.id()`). ✓
**Degradado:** sem curation → T1 cai para URL-only + placeholder do mapa (test_no_curation_renders_url_only). ✓

## Follow-ups (BACKLOG)
- Auditar consumidores diretos do manifest.json (dashboard/JS) após omit-defaults, se algum assumir chaves sempre presentes.
