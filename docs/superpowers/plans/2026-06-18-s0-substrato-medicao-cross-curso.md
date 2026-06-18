# S0 — Substrato de Medição Cross-Curso Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capturar `posting_date` e chave de turma na fonte (Moodle API) de forma estritamente aditiva, mais probe empírico e gold full file→bloco cross-curso, para tornar as alavancas A1..A6 eval-gated em qualquer cadeira — sem mudar atribuição.

**Architecture:** Captura na fonte (extensão de `SectionFile`/`iter_section_files`/`parse_moodle_course` + 2 campos em `FileEntry`/`SubjectProfile`). Split DRY do backfill in-place de `import_moodle_courses` em `_additive` (não muda atribuição) e `_consumed` (muda — fica para o S0b). Migrador CLI roda só o additive (dry-run + `.apibak`). Probe e gold reusam scripts existentes.

**Tech Stack:** Python 3.11, stdlib only (urllib, dataclasses, csv, datetime), pytest. Sem dependências novas.

## Global Constraints

- Spec de referência: `docs/superpowers/specs/2026-06-18-s0-substrato-medicao-cross-curso-design.md`.
- **S0 é estritamente não-mutante para atribuição.** Só captura sinais que NENHUM caminho de produção consome (ou consome só atrás de flag OFF). `rebuild_diff` nos 5 cursos deve dar **0**.
- `source_section` (overwrite) e `.card_block_map.json` (regen) NÃO entram no S0 — ficam no `_consumed`/S0b (eval-gated). `moodle_label` é fill-if-empty (seguro).
- Nova lógica vai no subpacote correto, nunca em `engine.py`. Imports de submódulos focados.
- Gemini usa `google-genai` (lazy) — não relevante aqui, mas não introduzir `google.generativeai`.
- Sem comentários óbvios; só WHY não-óbvio. Sem docstrings multi-parágrafo.
- Invariantes GOLDEN intocados: `assign_units_positional`, `_build_timeline_index`, `finalize_block`, review rule, flag `use_concept_resolver` OFF. Golden PDF 5/5 (`python scripts/eval_assignments.py`) nunca regride.
- Commits frequentes, mensagem conventional, terminando com:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Suíte: `python -m pytest tests -q` (baseline ≥1456 verde).
- **`HTMLImportDialog` é o caminho ATIVO de import do cronograma** (só-URL; ex.: `https://sarc.pucrs.br/Default/Export.aspx?id=<GUID>&ano=2026&sem=1`). NÃO foi deixado de lado — só o paste de HTML saiu da UI. A URL passa por ele no fetch, então `schedule_url` é capturado ali (Task 5b), sem deferir. `turma` vem automaticamente do fullname Moodle (`import_moodle_courses`).
- **READ-ONLY com o SARC:** o aluno é read-only; o sistema só faz GET do `Export.aspx` (`fetch_schedule_html`, helpers.py:555). NUNCA escrever no SARC. O `schedule_url` é guardado/parseado localmente (`parse_sarc_turma_key`), sem nenhuma chamada de escrita.

---

### Task 1: `SectionFile` + `iter_section_files` capturam timestamps

**Files:**
- Modify: `src/builder/sources/moodle.py:97` (dataclass `SectionFile`) e `:122` (`iter_section_files`)
- Test: `tests/test_moodle.py`

**Interfaces:**
- Produces: `SectionFile.timemodified: int`, `SectionFile.timecreated: int` (epoch, default 0).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_moodle.py
from src.builder.sources.moodle import iter_section_files

def test_iter_section_files_captures_timestamps():
    contents = [{"name": "Semana 1", "modules": [
        {"name": "Aula", "contents": [
            {"type": "file", "filename": "a.pdf", "fileurl": "http://x/a.pdf",
             "timemodified": 1739361600, "timecreated": 1739000000}]}]}]
    sf = iter_section_files(contents)[0]
    assert sf.timemodified == 1739361600
    assert sf.timecreated == 1739000000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_moodle.py::test_iter_section_files_captures_timestamps -v`
Expected: FAIL (`AttributeError: 'SectionFile' object has no attribute 'timemodified'`)

- [ ] **Step 3: Add fields to `SectionFile`**

Em `src/builder/sources/moodle.py`, no dataclass `SectionFile` (após `label`):

```python
    label: str = ""        # mod.get("name") — label do recurso no Moodle (alavanca 1)
    timemodified: int = 0  # epoch do upload/modificacao no Moodle (posting_date) — S0, nao consumido
    timecreated: int = 0   # epoch de criacao do blob no Moodle
```

- [ ] **Step 4: Ler os timestamps em `iter_section_files`**

Na chamada `SectionFile(...)` dentro de `iter_section_files`:

```python
                out.append(SectionFile(section, original, str(f["fileurl"]), savename,
                                       label=str(mod.get("name") or ""),
                                       timemodified=int(f.get("timemodified") or 0),
                                       timecreated=int(f.get("timecreated") or 0)))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_moodle.py::test_iter_section_files_captures_timestamps -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_moodle.py
git commit -m "feat(moodle): SectionFile captura timemodified/timecreated (S0)"
```

---

### Task 2: `backfill_posting_date_from_api` + helper ISO

**Files:**
- Modify: `src/builder/sources/moodle.py` (após `backfill_moodle_label_from_api:137`)
- Test: `tests/test_moodle.py`

**Interfaces:**
- Consumes: `iter_section_files` (Task 1).
- Produces: `backfill_posting_date_from_api(manifest_entries, contents) -> dict` ({id: {"timemodified": int, "timecreated": int}}); `posting_date_iso(ts) -> str` (epoch→"YYYY-MM-DD" UTC, "" se <=0/inválido).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle.py
from src.builder.sources.moodle import backfill_posting_date_from_api, posting_date_iso

def test_posting_date_iso_utc():
    assert posting_date_iso(1739361600) == "2025-02-12"   # 12:00 UTC
    assert posting_date_iso(0) == ""
    assert posting_date_iso(None) == ""

def test_backfill_posting_date_unique_match():
    contents = [{"name": "S1", "modules": [
        {"name": "Aula", "contents": [
            {"type": "file", "filename": "main.pdf", "fileurl": "u",
             "timemodified": 1739361600, "timecreated": 1739000000}]}]}]
    entries = [{"id": "e1", "source_path": "C:/x/main.pdf"}]
    out = backfill_posting_date_from_api(entries, contents)
    assert out["e1"] == {"timemodified": 1739361600, "timecreated": 1739000000}

def test_backfill_posting_date_skips_ambiguous_basename():
    contents = [{"name": "S1", "modules": [
        {"name": "A", "contents": [{"type": "file", "filename": "main.pdf", "fileurl": "u",
                                     "timemodified": 1, "timecreated": 1}]},
        {"name": "B", "contents": [{"type": "file", "filename": "main.pdf", "fileurl": "u2",
                                     "timemodified": 2, "timecreated": 2}]}]}]
    entries = [{"id": "e1", "source_path": "main.pdf"}]
    assert backfill_posting_date_from_api(entries, contents) == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_moodle.py -k posting_date -v`
Expected: FAIL (`ImportError: cannot import name 'backfill_posting_date_from_api'`)

- [ ] **Step 3: Implement**

Em `src/builder/sources/moodle.py` (após `backfill_moodle_label_from_api`):

```python
def posting_date_iso(ts) -> str:
    from datetime import datetime, timezone
    try:
        n = int(ts)
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    return datetime.fromtimestamp(n, tz=timezone.utc).strftime("%Y-%m-%d")


def backfill_posting_date_from_api(manifest_entries, contents):
    """Casa entries -> {timemodified, timecreated} por basename UNICO (igual ao
    source_section). Basename em >1 modulo -> pulado (ambiguo)."""
    from collections import Counter
    counts = Counter()
    ts_by_name = {}
    for sf in iter_section_files(contents):
        key = sf.filename.casefold()
        counts[key] += 1
        if (sf.timemodified or sf.timecreated):
            ts_by_name.setdefault(key, {"timemodified": sf.timemodified,
                                        "timecreated": sf.timecreated})
    out = {}
    for e in manifest_entries or []:
        eid = str(e.get("id") or "")
        base = Path(str(e.get("source_path") or "")).name.casefold()
        if base in ts_by_name and counts[base] == 1:
            out[eid or base] = ts_by_name[base]
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_moodle.py -k posting_date -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_moodle.py
git commit -m "feat(moodle): backfill_posting_date_from_api + posting_date_iso (S0)"
```

---

### Task 3: `FileEntry` ganha `posting_date` / `posting_date_created`

**Files:**
- Modify: `src/models/core.py:111` (dataclass `FileEntry`, após `moodle_label`)
- Test: `tests/test_core.py`

**Interfaces:**
- Produces: `FileEntry.posting_date: str`, `FileEntry.posting_date_created: str` (ISO, default "").

- [ ] **Step 1: Write the failing test**

```python
# tests/test_core.py
from src.models.core import FileEntry

def test_fileentry_posting_date_roundtrip():
    e = FileEntry(source_path="a.pdf", file_type="pdf", category="material", title="A",
                  posting_date="2026-02-12", posting_date_created="2026-02-10")
    d = e.to_dict()
    assert d["posting_date"] == "2026-02-12"
    back = FileEntry.from_dict(d)
    assert back.posting_date == "2026-02-12"
    assert back.posting_date_created == "2026-02-10"

def test_fileentry_posting_date_default_omitted_in_to_dict():
    e = FileEntry(source_path="a.pdf", file_type="pdf", category="material", title="A")
    assert "posting_date" not in e.to_dict()   # default "" e omitido (to_dict so grava nao-default)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_core.py -k posting_date -v`
Expected: FAIL (`TypeError: __init__() got an unexpected keyword argument 'posting_date'`)

- [ ] **Step 3: Add fields**

Em `src/models/core.py`, no `FileEntry`, logo após `moodle_label: str = ""`:

```python
    moodle_label: str = ""
    # Data de upload/postagem (ISO YYYY-MM-DD) do timemodified Moodle/M365.
    # Capturada no import (S0). NAO consumida pela atribuicao (consumo = A2).
    # ""=ausente (HTML sem timestamp, ou fonte sem data).
    posting_date: str = ""
    posting_date_created: str = ""   # ISO do timecreated (diagnostico do probe)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core.py -k posting_date -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py tests/test_core.py
git commit -m "feat(core): FileEntry.posting_date(+_created) com round-trip (S0)"
```

---

### Task 4: `parse_moodle_course` captura `turma`

**Files:**
- Modify: `src/builder/sources/moodle.py:32` (`parse_moodle_course`)
- Test: `tests/test_moodle.py`

**Interfaces:**
- Produces: `parse_moodle_course(course)["turma"]` (str; "" se ausente).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle.py
from src.builder.sources.moodle import parse_moodle_course

def test_parse_turma_single():
    c = {"id": 1, "fullname": "4646M-04 - Métodos Formais - Turma 031 - 2026/1 - Prof. X"}
    assert parse_moodle_course(c)["turma"] == "031"

def test_parse_turma_multiple():
    c = {"id": 2, "fullname": "98702-04 - Prática em Pesquisa - Turmas 010 - 011 - 012 - 2026/1 - Profs. Y"}
    assert parse_moodle_course(c)["turma"] == "010 - 011 - 012"

def test_parse_turma_absent():
    c = {"id": 3, "fullname": "Curso de Ciência da Computação"}
    assert parse_moodle_course(c)["turma"] == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_moodle.py -k turma -v`
Expected: FAIL (`KeyError: 'turma'`)

- [ ] **Step 3: Implement**

Em `parse_moodle_course`, antes do `return`, adicionar a captura (turma = 3 dígitos, `\b` impede capturar o ano 2026):

```python
    turma = ""
    m_t = _re.search(r"Turmas?\s+(\d{3}\b(?:\s*-\s*\d{3}\b)*)", full, _re.IGNORECASE)
    if m_t:
        turma = _re.sub(r"\s+", " ", m_t.group(1)).strip()
```

E no dict de retorno adicionar:

```python
        "turma": turma,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_moodle.py -k turma -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_moodle.py
git commit -m "feat(moodle): parse_moodle_course captura turma (S0)"
```

---

### Task 5: `SubjectProfile` ganha `turma`/`schedule_url` + `parse_sarc_turma_key`

**Files:**
- Modify: `src/models/core.py:206` (`SubjectProfile`)
- Modify: `src/utils/helpers.py` (após `is_sarc_url:509`)
- Test: `tests/test_core.py`, `tests/test_sarc_import.py`

**Interfaces:**
- Produces: `SubjectProfile.turma: str`, `SubjectProfile.schedule_url: str`;
  `helpers.parse_sarc_turma_key(url) -> {"guid": str, "ano": str, "sem": str}`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_core.py
from src.models.core import SubjectProfile

def test_subjectprofile_turma_schedule_roundtrip():
    sp = SubjectProfile(name="MF", turma="031",
                        schedule_url="https://sarc.pucrs.br/Default/Export.aspx?id=abc&ano=2026&sem=1")
    d = sp.to_dict()
    back = SubjectProfile.from_dict(d)
    assert back.turma == "031"
    assert back.schedule_url.endswith("sem=1")
```

```python
# tests/test_sarc_import.py
from src.utils.helpers import parse_sarc_turma_key

def test_parse_sarc_turma_key():
    url = "https://sarc.pucrs.br/Default/Export.aspx?id=9b679f12-aaaa&ano=2026&sem=1"
    assert parse_sarc_turma_key(url) == {"guid": "9b679f12-aaaa", "ano": "2026", "sem": "1"}

def test_parse_sarc_turma_key_malformed():
    assert parse_sarc_turma_key("not a url") == {"guid": "", "ano": "", "sem": ""}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_core.py::test_subjectprofile_turma_schedule_roundtrip tests/test_sarc_import.py -k "turma_key or turma_schedule" -v`
Expected: FAIL (campo/função inexistentes)

- [ ] **Step 3: Implement (SubjectProfile)**

Em `src/models/core.py`, no `SubjectProfile`, após `m365_filter`:

```python
    m365_filter: str = ""        # substring do path OneDrive p/ filtrar insights (M365)
    turma: str = ""              # turma(s) do curso Moodle (ex.: "031"); registro, nao scoped (S0)
    schedule_url: str = ""       # URL do SARC Export.aspx (GUID/ano/sem da turma); registro (S0)
```

- [ ] **Step 4: Implement (`parse_sarc_turma_key`)**

Em `src/utils/helpers.py`, após `is_sarc_url`:

```python
def parse_sarc_turma_key(url: Optional[str]) -> dict:
    """Extrai {guid, ano, sem} da query da URL do SARC Export.aspx. Ausentes -> ""."""
    from urllib.parse import urlparse, parse_qs
    try:
        q = parse_qs(urlparse(str(url or "")).query)
    except Exception:
        return {"guid": "", "ano": "", "sem": ""}
    return {
        "guid": (q.get("id") or [""])[0].strip(),
        "ano": (q.get("ano") or [""])[0].strip(),
        "sem": (q.get("sem") or [""])[0].strip(),
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_core.py::test_subjectprofile_turma_schedule_roundtrip tests/test_sarc_import.py -k "turma_key" -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/models/core.py src/utils/helpers.py tests/test_core.py tests/test_sarc_import.py
git commit -m "feat(core): SubjectProfile.turma/schedule_url + parse_sarc_turma_key (S0)"
```

---

### Task 5b: Persistir `schedule_url` pela UI (HTMLImportDialog → SubjectManagerDialog)

**Files:**
- Modify: `src/ui/dialogs.py` (`HTMLImportDialog._fetch_and_process:1219`; `SubjectManagerDialog.__init__:1267`, `_on_select:1457`, `_new:1473`, `_save:1487`)

**Interfaces:**
- Consumes: `SubjectProfile.schedule_url`/`turma` (Task 5).

**Nota:** tkinter não tem unit test nesta base — esta task é edição + smoke-test manual (Step 5). Mantém o `schedule_url` ao salvar (preserva do existente quando não houve novo import; turma idem, pois vem do import Moodle, não do form).

- [ ] **Step 1: Stash da URL no parent no momento do fetch**

Em `HTMLImportDialog._fetch_and_process`, logo no início (antes de desabilitar o botão):

```python
    def _fetch_and_process(self, url: str):
        """Fetch the SARC HTML on a background thread, then parse on the UI thread."""
        import threading
        # READ-ONLY: só GET; guarda a URL p/ o parent persistir schedule_url ao salvar.
        try:
            self.parent._imported_schedule_url = url
        except Exception:
            pass
```

- [ ] **Step 2: Inicializar/limpar o campo no parent**

Em `SubjectManagerDialog.__init__` (após `self._current_name = None`):

```python
        self._imported_schedule_url = ""
```

Em `_new` (após `self._current_name = None`):

```python
        self._imported_schedule_url = ""
```

Em `_on_select` (após `self._current_name = name`):

```python
        self._imported_schedule_url = getattr(sp, "schedule_url", "")
```

- [ ] **Step 3: Persistir no `_save` (preserva existente + turma)**

Em `SubjectManagerDialog._save`, na construção do `SubjectProfile`, adicionar (após `processing_profile=...`):

```python
            processing_profile=self._vars["processing_profile"].get(),
            schedule_url=(getattr(self, "_imported_schedule_url", "")
                          or (existing.schedule_url if existing else "")),
            turma=(existing.turma if existing else ""),
            queue=existing_queue,
```

- [ ] **Step 4: Verificar import compila**

Run: `python -c "import src.ui.dialogs"`
Expected: sem erro.

- [ ] **Step 5: Smoke-test manual (UI)**

1. `python app.py` → Gerenciador de Matérias → selecionar/criar matéria.
2. Importar Cronograma (SARC) colando a URL `...Export.aspx?id=<GUID>&ano=2026&sem=1` → cronograma carrega.
3. Salvar. Reselecionar a matéria. Confirmar no store (`subjects.json`) que `schedule_url` persistiu e `turma` foi preservada.

- [ ] **Step 6: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(ui): persiste schedule_url do SARC no SubjectProfile (S0)"
```

---

### Task 6: Split DRY do backfill — `_additive` vs `_consumed`

**Files:**
- Modify: `src/builder/sources/moodle.py` (extrair de `import_moodle_courses:392-454`)
- Test: `tests/test_moodle.py`

**Interfaces:**
- Consumes: `backfill_source_section_from_api`, `backfill_moodle_label_from_api`, `backfill_posting_date_from_api`, `posting_date_iso`, `moodle_labels.*`.
- Produces:
  - `backfill_repo_signals_additive(repo_root, contents, info, write=True) -> dict` — NÃO toca `source_section` nem `.card_block_map.json`. Aplica `moodle_label` (fill-if-empty), `posting_date`(+created), `.lessons_index.json`, e grava `manifest["turma"]`/`manifest["schedule_url"]` de `info`. Retorna contagens.
  - `backfill_repo_signals_consumed(repo_root, contents, info, write=True) -> dict` — `source_section` (overwrite) + `.card_block_map.json`/`assign_due`. Retorna contagens.
- `import_moodle_courses` passa a chamar as duas (paridade com hoje).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle.py
import json
from pathlib import Path
from src.builder.sources.moodle import (
    backfill_repo_signals_additive, backfill_repo_signals_consumed,
)

def _fake_repo(tmp_path, entries):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps({"entries": entries}), encoding="utf-8")
    (repo / "course" / ".timeline_index.json").write_text(
        json.dumps({"blocks": [{"id": "bloco-01", "period_start": "2026-02-20",
                                "period_end": "2026-02-28", "unit_slug": "u1"}]}),
        encoding="utf-8")
    return repo

_CONTENTS = [{"name": "Semana 1", "modules": [
    {"name": "Exemplos (Hoare)", "contents": [
        {"type": "file", "filename": "main.pdf", "fileurl": "u",
         "timemodified": 1739361600, "timecreated": 1739000000}]}]}]

def test_additive_sets_posting_and_label_not_section(tmp_path):
    repo = _fake_repo(tmp_path, [{"id": "e1", "source_path": "main.pdf",
                                  "source_section": "OLD", "moodle_label": ""}])
    backfill_repo_signals_additive(repo, _CONTENTS, {"name": "MF", "semester": "2026/1",
                                                     "turma": "031", "schedule_url": ""}, write=True)
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    e = m["entries"][0]
    assert e["posting_date"] == "2025-02-12"
    assert e["moodle_label"] == "Exemplos (Hoare)"
    assert e["source_section"] == "OLD"          # additive NAO toca source_section
    assert m["turma"] == "031"

def test_additive_does_not_write_card_block_map(tmp_path):
    repo = _fake_repo(tmp_path, [{"id": "e1", "source_path": "main.pdf"}])
    backfill_repo_signals_additive(repo, _CONTENTS, {"name": "MF", "semester": "2026/1"}, write=True)
    assert not (repo / "course" / ".card_block_map.json").exists()

def test_consumed_overwrites_section(tmp_path):
    repo = _fake_repo(tmp_path, [{"id": "e1", "source_path": "main.pdf", "source_section": "OLD"}])
    backfill_repo_signals_consumed(repo, _CONTENTS, {"name": "MF", "semester": "2026/1"}, write=True)
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    assert m["entries"][0]["source_section"] == "Semana 1"   # consumed overwrita
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_moodle.py -k "additive or consumed" -v`
Expected: FAIL (funções inexistentes)

- [ ] **Step 3: Implement as duas funções**

Em `src/builder/sources/moodle.py`, adicionar (antes de `import_moodle_courses`):

```python
def backfill_repo_signals_additive(repo_root, contents, info, write: bool = True) -> dict:
    """Backfill que NAO muda atribuicao: moodle_label (fill-if-empty), posting_date,
    .lessons_index.json, e meta turma/schedule_url. Grava in-place se write."""
    import json as _json
    repo = Path(repo_root)
    mpath = repo / "manifest.json"
    if not mpath.is_file():
        return {"labels": 0, "posting": 0, "lessons": 0}
    manifest = _json.loads(mpath.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    labels = backfill_moodle_label_from_api(entries, contents)
    posting = backfill_posting_date_from_api(entries, contents)
    n_lab = n_post = 0
    for e in entries:
        eid = str(e.get("id") or "") or Path(str(e.get("source_path") or "")).name
        if labels.get(eid) and not str(e.get("moodle_label") or "").strip():
            e["moodle_label"] = labels[eid]
            n_lab += 1
        if eid in posting:
            e["posting_date"] = posting_date_iso(posting[eid]["timemodified"])
            e["posting_date_created"] = posting_date_iso(posting[eid]["timecreated"])
            n_post += 1
    if info.get("turma"):
        manifest["turma"] = info["turma"]
    if info.get("schedule_url"):
        manifest["schedule_url"] = info["schedule_url"]
    if write:
        write_json_manifest(mpath, manifest)
    # lessons_index (nao consumido em producao)
    n_lessons = 0
    try:
        from src.builder.sources.moodle_labels import build_lesson_topic_index
        year = int((info.get("semester") or "0/0").split("/")[0] or 0)
        lessons_index = build_lesson_topic_index(contents, year)
        if lessons_index.get("by_date") and write:
            (repo / "course" / ".lessons_index.json").write_text(
                _json.dumps(lessons_index, ensure_ascii=False, indent=1), encoding="utf-8")
            n_lessons = len(lessons_index["by_date"])
    except Exception:
        logger.warning("lessons_index falhou para %s", info.get("name"), exc_info=True)
    return {"labels": n_lab, "posting": n_post, "lessons": n_lessons}


def backfill_repo_signals_consumed(repo_root, contents, info, write: bool = True) -> dict:
    """Backfill que MUDA atribuicao: source_section (overwrite) + card_block_map/assign_due.
    Usado pelo import normal e pelo S0b (eval-gated). Grava in-place se write."""
    import json as _json
    repo = Path(repo_root)
    mpath = repo / "manifest.json"
    if not mpath.is_file():
        return {"sections": 0, "card_labels": 0}
    manifest = _json.loads(mpath.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    assignments, _u, _a = backfill_source_section_from_api(entries, contents)
    n_sec = 0
    for e in entries:
        eid = str(e.get("id") or "") or Path(str(e.get("source_path") or "")).name
        if eid in assignments:
            e["source_section"] = assignments[eid]
            n_sec += 1
    if write:
        write_json_manifest(mpath, manifest)
    n_card = 0
    try:
        from src.builder.sources.moodle_labels import (
            parse_card_dates, derive_card_block_map, merge_card_block_map,
            extract_assign_deadlines,
        )
        ti_path = repo / "course" / ".timeline_index.json"
        map_path = repo / "course" / ".card_block_map.json"
        if ti_path.is_file():
            blocks = (_json.loads(ti_path.read_text(encoding="utf-8")) or {}).get("blocks") or []
            year = int((info.get("semester") or "0/0").split("/")[0] or 0)
            derived = derive_card_block_map(parse_card_dates(contents, year), blocks)
            for _card, _due in extract_assign_deadlines(contents, year).items():
                if _card in derived:
                    derived[_card]["assign_due"] = _due
                else:
                    derived[_card] = {"block_ids": [], "source": "labels", "assign_due": _due}
            existing = _json.loads(map_path.read_text(encoding="utf-8")) if map_path.is_file() else {}
            merged = merge_card_block_map(existing, derived)
            if merged != existing and write:
                map_path.write_text(_json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
            n_card = sum(1 for _ in derived.values())
    except Exception:
        logger.warning("card_block_map via labels falhou para %s", info.get("name"), exc_info=True)
    return {"sections": n_sec, "card_labels": n_card}
```

- [ ] **Step 4: Rewire `import_moodle_courses` para usar as duas (paridade)**

Substituir o bloco `# --- metadados: estrutura de cards + backfill ---` ... até o fim do bloco `card_block_map automático` (moodle.py:386-454) por:

```python
        # --- metadados: estrutura de cards + backfill ---
        contents = client.get_course_contents(cid)
        st = build_card_structure(base / info["slug"], contents)
        folders += st["folders"]
        expected_files += st["expected_files"]
        sp.turma = info.get("turma", "") or getattr(sp, "turma", "")
        repo = getattr(sp, "repo_root", "") or ""
        if repo and (Path(repo) / "manifest.json").is_file():
            info_repo = {**info, "turma": sp.turma, "schedule_url": getattr(sp, "schedule_url", "")}
            add = backfill_repo_signals_additive(repo, contents, info_repo, write=True)
            con = backfill_repo_signals_consumed(repo, contents, info_repo, write=True)
            backfilled += con["sections"]
            card_map_labels += con["card_labels"]
```

(Remover `card_map_manual` se virar sempre 0; manter a chave no return como 0 para não quebrar callers da UI. Verificar no Step 6.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_moodle.py -k "additive or consumed" -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Run the full moodle suite (paridade do import)**

Run: `python -m pytest tests/test_moodle.py -q`
Expected: PASS (sem regressão; se algum teste lê `card_map_manual`, manter a chave no return de `import_moodle_courses` como `0`).

- [ ] **Step 7: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_moodle.py
git commit -m "refactor(moodle): split backfill additive vs consumed; import usa ambos (S0)"
```

---

### Task 7: `scripts/migrate_signals.py` (additive, dry-run + .apibak)

**Files:**
- Create: `scripts/migrate_signals.py`
- Test: `tests/test_migrate_signals.py`

**Interfaces:**
- Consumes: `MoodleClient`, `load_moodle_token`, `backfill_repo_signals_additive` (Task 6), `parse_sarc_turma_key` (Task 5).
- Produces: `migrate_repo_additive(repo_root, contents, info, write=False) -> dict` (faz `.apibak` antes de gravar quando write).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_migrate_signals.py
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.migrate_signals import migrate_repo_additive

_CONTENTS = [{"name": "S1", "modules": [
    {"name": "L", "contents": [{"type": "file", "filename": "main.pdf", "fileurl": "u",
                                "timemodified": 1739361600, "timecreated": 1739000000}]}]}]

def test_dry_run_does_not_write(tmp_path):
    repo = tmp_path / "r"; (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps(
        {"entries": [{"id": "e1", "source_path": "main.pdf"}]}), encoding="utf-8")
    migrate_repo_additive(repo, _CONTENTS, {"name": "MF", "semester": "2026/1"}, write=False)
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    assert "posting_date" not in m["entries"][0]            # dry-run nao grava
    assert not (repo / "manifest.json.apibak").exists()

def test_write_makes_backup_and_sets_posting(tmp_path):
    repo = tmp_path / "r"; (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps(
        {"entries": [{"id": "e1", "source_path": "main.pdf"}]}), encoding="utf-8")
    migrate_repo_additive(repo, _CONTENTS, {"name": "MF", "semester": "2026/1"}, write=True)
    assert (repo / "manifest.json.apibak").exists()
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    assert m["entries"][0]["posting_date"] == "2025-02-12"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_migrate_signals.py -v`
Expected: FAIL (`ModuleNotFoundError: scripts.migrate_signals`)

- [ ] **Step 3: Implement**

```python
# scripts/migrate_signals.py
"""Migrador ADITIVO de sinais (S0): aplica posting_date/moodle_label/lessons_index/turma
aos repos ja gerados via API Moodle. NAO toca source_section nem card_block_map (= S0b).

Uso:
    python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>]          # dry-run
    python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>] --write  # grava (.apibak)
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.builder.sources.moodle import (
    MoodleClient, load_moodle_token, backfill_repo_signals_additive,
)
from src.utils.helpers import parse_sarc_turma_key


def migrate_repo_additive(repo_root, contents, info, write: bool = False) -> dict:
    repo = Path(repo_root)
    mpath = repo / "manifest.json"
    if write and mpath.is_file():
        (mpath.with_suffix(".json.apibak")).write_text(
            mpath.read_text(encoding="utf-8"), encoding="utf-8")
    return backfill_repo_signals_additive(repo, contents, info, write=write)


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    write = "--write" in argv
    course = sarc = ""
    if "--course" in argv:
        i = argv.index("--course"); course = argv[i + 1] if i + 1 < len(argv) else ""
    if "--sarc" in argv:
        i = argv.index("--sarc"); sarc = argv[i + 1] if i + 1 < len(argv) else ""
    pos = [a for a in argv if not a.startswith("-") and a not in (course, sarc)]
    if not pos or not course:
        print("uso: python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>] [--write]")
        return 2
    repo = Path(pos[0])
    url, tok = load_moodle_token()
    if not tok:
        print("Faltando MOODLE_TOKEN (.env raiz ou moddle/.env).")
        return 2
    contents = MoodleClient(url, tok).get_course_contents(course)
    info = {"name": repo.name, "semester": "", "schedule_url": sarc}
    if sarc:
        key = parse_sarc_turma_key(sarc)
        info["semester"] = f"{key['ano']}/{key['sem']}" if key["ano"] else ""
    res = migrate_repo_additive(repo, contents, info, write=write)
    print(f"posting={res['posting']}  labels={res['labels']}  lessons={res['lessons']}")
    print("Gravado (.apibak feito)." if write else "Dry-run. Use --write para gravar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_migrate_signals.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_signals.py tests/test_migrate_signals.py
git commit -m "feat(scripts): migrate_signals additive (dry-run + .apibak) (S0)"
```

---

### Task 8: `scripts/posting_date_probe.py` (read-only, métrica por curso)

**Files:**
- Create: `scripts/posting_date_probe.py`
- Test: `tests/test_posting_date_probe.py`

**Interfaces:**
- Consumes: `MoodleClient`, `load_moodle_token`, `iter_section_files`, `posting_date_iso`.
- Produces: `summarize_posting_dates(contents, semester_year) -> dict` ({total, stale, by_month, batch_month, off_batch}).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_posting_date_probe.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.posting_date_probe import summarize_posting_dates

def test_summarize_batch_and_offbatch():
    # 3 em 2026-02 (batch), 1 em 2026-05 (off-batch), 0 stale
    def f(ts): return {"type": "file", "filename": f"{ts}.pdf", "fileurl": "u",
                       "timemodified": ts, "timecreated": ts}
    contents = [{"name": "S", "modules": [{"name": "m", "contents": [
        f(1738800000), f(1738900000), f(1739000000),  # fev/2026
        f(1746000000),                                  # mai/2026
    ]}]}]
    r = summarize_posting_dates(contents, 2026)
    assert r["total"] == 4
    assert r["stale"] == 0
    assert r["batch_month"] == "2026-02"
    assert r["off_batch"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_posting_date_probe.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Implement**

```python
# scripts/posting_date_probe.py
"""Probe READ-ONLY do posting_date (S0): mede, por curso, o cluster de inicio-de-semestre
(batch), a fracao off-batch (sinal informativo p/ A2) e contagem stale (ano anterior).

Uso:
    python -m scripts.posting_date_probe --course <id> [--year 2026]
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.builder.sources.moodle import MoodleClient, load_moodle_token, iter_section_files


def summarize_posting_dates(contents, semester_year: int) -> dict:
    months = []
    stale = 0
    for sf in iter_section_files(contents):
        if not sf.timemodified:
            continue
        d = datetime.fromtimestamp(sf.timemodified, tz=timezone.utc)
        months.append(f"{d.year}-{d.month:02d}")
        if semester_year and d.year < semester_year:
            stale += 1
    by_month = Counter(months)
    batch_month = by_month.most_common(1)[0][0] if by_month else ""
    off_batch = sum(c for m, c in by_month.items() if m != batch_month)
    return {"total": len(months), "stale": stale, "by_month": dict(sorted(by_month.items())),
            "batch_month": batch_month, "off_batch": off_batch}


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    course = year = ""
    if "--course" in argv:
        i = argv.index("--course"); course = argv[i + 1] if i + 1 < len(argv) else ""
    if "--year" in argv:
        i = argv.index("--year"); year = argv[i + 1] if i + 1 < len(argv) else ""
    if not course:
        print("uso: python -m scripts.posting_date_probe --course <id> [--year 2026]")
        return 2
    url, tok = load_moodle_token()
    if not tok:
        print("Faltando MOODLE_TOKEN."); return 2
    contents = MoodleClient(url, tok).get_course_contents(course)
    r = summarize_posting_dates(contents, int(year or 0))
    print(f"total={r['total']}  stale={r['stale']}  batch={r['batch_month']}  off_batch={r['off_batch']}")
    print(f"por mes: {r['by_month']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_posting_date_probe.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/posting_date_probe.py tests/test_posting_date_probe.py
git commit -m "feat(scripts): posting_date_probe (cluster/off-batch/stale) (S0)"
```

---

### Task 9: Gate cross-curso — gold auto-contido + `check_baseline`

**Files:**
- Modify: `scripts/eval_ground_truth.py` (add `load_predictions_from_gold`, `check_baseline`)
- Test: `tests/test_eval_ground_truth_gold.py`

**Interfaces:**
- Consumes: `evaluate_ground_truth`, `load_labels_csv` (existentes).
- Produces:
  - `load_predictions_from_gold(csv_path) -> dict` (lê `predicted_block_id`/`predicted_band`/`id` do CSV rotulado → mesmo shape de `load_predictions`).
  - `check_baseline(report, baseline) -> int` (0 ok, 1 regressão): `block_accuracy >= baseline["block_accuracy_min"]` E `confident_wrong <= baseline["confident_wrong_max"]`. Baseline vazio nunca regride.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_eval_ground_truth_gold.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.eval_ground_truth import evaluate_ground_truth, check_baseline

def _report(acc_correct, total, cw):
    # constroi predictions/labels minimas p/ evaluate_ground_truth
    labels = {f"e{i}": "bloco-01" for i in range(total)}
    preds = {}
    for i in range(total):
        ok = i < acc_correct
        preds[f"e{i}"] = {"block_id": "bloco-01" if ok else "bloco-99",
                          "band": "alta" if (not ok and i < acc_correct + cw) else "media"}
    return evaluate_ground_truth(preds, labels, {})

def test_check_baseline_passes_at_floor():
    r = _report(7, 10, 0)   # 0.7 acc, 0 cw
    assert check_baseline(r, {"block_accuracy_min": 0.7, "confident_wrong_max": 0}) == 0

def test_check_baseline_regresses_accuracy():
    r = _report(5, 10, 0)   # 0.5
    assert check_baseline(r, {"block_accuracy_min": 0.7, "confident_wrong_max": 0}) == 1

def test_check_baseline_regresses_confident_wrong():
    r = _report(7, 10, 2)
    assert check_baseline(r, {"block_accuracy_min": 0.7, "confident_wrong_max": 1}) == 1

def test_check_baseline_empty_never_regresses():
    r = _report(0, 10, 9)
    assert check_baseline(r, {}) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_eval_ground_truth_gold.py -v`
Expected: FAIL (`ImportError: cannot import name 'check_baseline'`)

- [ ] **Step 3: Implement**

Em `scripts/eval_ground_truth.py` (após `load_labels_csv`):

```python
def load_predictions_from_gold(csv_path) -> dict:
    """Predicoes auto-contidas do CSV rotulado (snapshot), sem repo live."""
    preds = {}
    with Path(csv_path).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            eid = str(row.get("id", "")).strip()
            if eid:
                preds[eid] = {"block_id": str(row.get("predicted_block_id", "")),
                              "band": str(row.get("predicted_band", "")),
                              "title": str(row.get("title", ""))}
    return preds


def check_baseline(report: dict, baseline: dict) -> int:
    """0 = ok, 1 = regressao. Baseline vazio nunca regride."""
    if not baseline:
        return 0
    acc_min = float(baseline.get("block_accuracy_min", 0.0))
    cw_max = baseline.get("confident_wrong_max")
    if report.get("block_accuracy", 0.0) + 1e-9 < acc_min:
        return 1
    if cw_max is not None and report.get("confident_wrong", 0) > int(cw_max):
        return 1
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_eval_ground_truth_gold.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Run full suite (sem regressão)**

Run: `python -m pytest tests -q`
Expected: PASS (≥1456 + os novos).

- [ ] **Step 6: Commit**

```bash
git add scripts/eval_ground_truth.py tests/test_eval_ground_truth_gold.py
git commit -m "feat(eval): gold auto-contido cross-curso + check_baseline (S0)"
```

---

### Task 10: Checkpoint operacional (USER-SIDE) — migrar, medir, rotular, travar

Não-TDD; depende do app/Moodle real + rotulagem manual. Executar APÓS Tasks 1-9 verdes.

- [ ] **Step 1: rebuild_diff antes (prova inércia futura)**

Run: `python scripts/rebuild_diff.py`
Anotar o estado atual (referência).

- [ ] **Step 2: Dry-run do migrador additive num repo real**

Run: `python -m scripts.migrate_signals "C:\Users\Humberto\Documents\GitHub\Metodos-Formais-Tutor" --course 92717`
Conferir contagens `posting/labels/lessons`. Confirmar que NÃO menciona source_section/card_block_map.

- [ ] **Step 3: Gravar (com .apibak) nos 5 repos**

Run (por repo, com `--write` e `--course <id>` e `--sarc <url>` quando houver):
`python -m scripts.migrate_signals "<repo>" --course <id> --sarc "<url SARC>" --write`
Cursos 2026/1: MF=92717, IA=93156, SO=92854, ES2=92714, TCC=93728.

- [ ] **Step 4: rebuild_diff depois = 0**

Run: `python scripts/rebuild_diff.py`
Expected: **0 diffs** de unit/kind (S0 é inerte). Se ≠0, PARAR e investigar (algum campo aditivo está sendo consumido).

- [ ] **Step 5: Golden + suíte**

Run: `python scripts/eval_assignments.py` (5/5, confiante-errado 0) e `python -m pytest tests -q` (verde).

- [ ] **Step 6: Probe nas 5 cadeiras**

Run (por curso): `python -m scripts.posting_date_probe --course <id> --year 2026`
Anotar batch_month/off_batch/stale por curso (alimenta a decisão do A2).

- [ ] **Step 7: Gerar templates de gold cross-curso**

Run (por repo): `python scripts/make_ground_truth_template.py "<repo>" "docs/reports/gold_<curso>.csv"`
Gerar p/ ES2 e IA (e re-confirmar MF). **USER rotula** `true_block_id` corrigindo os errados.

- [ ] **Step 8: Salvar golds rotulados como fixtures + travar baseline**

Mover os CSVs rotulados p/ `tests/fixtures/eval/ground_truth_<curso>.csv`. Medir baseline por curso:
`python -c "from scripts.eval_ground_truth import *; r=evaluate_ground_truth(load_predictions_from_gold('tests/fixtures/eval/ground_truth_es2.csv'), load_labels_csv('tests/fixtures/eval/ground_truth_es2.csv'), {}); print(r['block_accuracy'], r['confident_wrong'])"`
Gravar os números num teste de gate por curso (mirror de `test_eval_code_block_gold.py`, usando `check_baseline`).

- [ ] **Step 9: Atualizar Overview (AGENTS non-negotiable)**

Em `docs/Overview-Sistema.html`: marcar `posting_date` e chave de turma como CAPTURADOS (não consumidos) na aba de sinais (§0/§5); registrar os números do probe por curso.

- [ ] **Step 10: Commit**

```bash
git add tests/fixtures/eval/ground_truth_*.csv tests/test_eval_ground_truth_gold.py docs/Overview-Sistema.html
git commit -m "test(eval): golds cross-curso (ES2/IA/MF) + baseline travado + probe (S0)"
```

---

## Self-Review

**Spec coverage:**
- C1 posting_date na fonte → Tasks 1, 2, 3. ✓
- C2 turma + schedule_url na fonte → Tasks 4, 5 (campo + helper), 5b (persistência UI pelo dialog ativo). ✓ (completo)
- C3 migrador aditivo DRY → Tasks 6, 7. ✓
- C4 probe → Task 8. ✓
- C5 gold + gate → Task 9 (código) + Task 10 (dados, user-side). ✓
- S0b (consumed) → função criada na Task 6 (`backfill_repo_signals_consumed`); execução/gate é sub-projeto próprio (fora deste plano). ✓
- Non-goal "rebuild_diff=0" → Task 10 Step 4 valida. ✓

**Placeholder scan:** sem TBD/TODO; todo step de código tem código real; comandos com expected output. ✓

**Type consistency:** `posting_date_iso`/`backfill_posting_date_from_api` (Task 2) usadas em Task 6; `backfill_repo_signals_additive` (Task 6) usada em Task 7; `parse_sarc_turma_key` (Task 5) usada em Task 7; `check_baseline`/`load_predictions_from_gold` (Task 9) usadas em Task 10. Nomes batem. ✓

**Riscos:** Task 6 é a de maior risco (refactor com paridade) — Step 6 roda a suíte moodle inteira para pegar regressão. `card_map_manual` no return de `import_moodle_courses`: manter a chave (=0) se algum caller/teste lê.

**Gap pré-existente observado (FORA do escopo S0):** `SubjectManagerDialog._save` (dialogs.py:1496) reconstrói o `SubjectProfile` só com os campos do form + `queue`, sem preservar `moodle_course_id` nem `m365_filter` do perfil existente → salvar a matéria por esse dialog os zera. A Task 5b preserva `schedule_url`/`turma`, mas o gap maior (moodle_course_id/m365_filter) é dívida própria, a tratar separadamente (não introduzida pelo S0).
