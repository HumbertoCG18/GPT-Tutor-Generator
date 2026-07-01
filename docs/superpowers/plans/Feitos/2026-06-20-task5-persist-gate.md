# Task 5: Gate migração p/ persist=True; medição read-only

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate ledger mint/save + manifest/curation rewrite behind `persist: bool` so measurement scripts never write to the repo.

**Architecture:** Add `persist` kwarg to `_build_file_map_timeline_context_from_course` (default `True` to preserve existing callers). Gate `save_identity_ledger`, `manifest.write_text`, and `curation.write_text` to only run when `persist=True`. On `persist=False` with a missing ledger + existing blocks, raise a clear `BlockIdentityError`. On `persist=False` with a stale block (not in ledger), do in-memory re-attach + log warning, never write. Wire `persist=False` to all measurement call sites: `rebuild_diff.py`, `scripts/compare_resolver.py`, `eval_code_block_gold.py`, `eval_assignments.py`, `eval_ground_truth.py`. The facade and `regenerate_pedagogical_files` callers stay `persist=True` (default).

**Tech Stack:** Python 3.10+, pytest, git, pathlib, json.

## Global Constraints

- TDD: failing test BEFORE implementation code.
- No docstring multi-parágrafo, no comentário óbvio.
- Never touch the 5 real tutor repos (MF, IA, SO, ES2, TCC).
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- `pytest -q` must stay green after every task.
- The gate in `index.py` must be the ONLY place writes happen; no new write sites.
- Constraint: lógica nova fora de `engine.py` (the gate lives in `index.py`).

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/builder/timeline/index.py:1349` | Add `persist` kwarg; gate `save_identity_ledger`, manifest write, curation write |
| Modify | `src/builder/facade/teaching_timeline.py:93` | Thread `persist` through the closure |
| Modify | `scripts/rebuild_diff.py:35` | Pass `persist=False` |
| Test | `tests/test_persist_gate.py` | New test file: all gate assertions |

---

### Task 1: Add `persist` kwarg to `_build_file_map_timeline_context_from_course` and gate writes

**Files:**
- Modify: `src/builder/timeline/index.py:1349-1412`
- Test: `tests/test_persist_gate.py` (create)

**Interfaces:**
- Produces: `_build_file_map_timeline_context_from_course(course_meta, subject_profile=None, content_taxonomy=None, *, ..., persist=True) -> dict`
- Produces: `persist=False` → no `save_identity_ledger` call, no manifest write, no curation write
- Produces: `persist=False` + ledger absent + `has_existing_refs=True` → raises `BlockIdentityError` with message containing "ledger" and "rebuild"
- Produces: `persist=False` + block not in ledger → block gets in-memory uuid via `reattach_block_uuids`, warning logged, NO write

- [ ] **Step 1.1: Write the failing test for persist=False no-write**

Create `tests/test_persist_gate.py`:

```python
"""TDD — Task 5: persist gate.

Gate: _build_file_map_timeline_context_from_course(persist=False) never writes.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from src.builder.timeline.index import _build_file_map_timeline_context_from_course
from src.builder.timeline.block_identity import BlockIdentityError, save_identity_ledger

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_DUMMY_KWARG = dict(
    build_file_map_unit_index_from_course=lambda cm, sp: [],
    build_file_map_content_taxonomy_from_course=lambda cm, sp: {},
)

_MINIMAL_SYLLABUS = """\
## Semana 1 (01/03/2026 - 07/03/2026)
Introdução
"""


def _course_meta(repo_root: Path) -> dict:
    return {
        "_repo_root": repo_root,
        "_timeline_context": None,
    }


def _course_meta_with_syllabus(repo_root: Path) -> dict:
    """course_meta sem atalho _timeline_context (força rebuild real)."""
    return {"_repo_root": repo_root}


def _write_syllabus(repo_root: Path, text: str = _MINIMAL_SYLLABUS) -> None:
    (repo_root / "course").mkdir(parents=True, exist_ok=True)
    (repo_root / "course" / "SYLLABUS.md").write_text(text, encoding="utf-8")


def _make_ledger(repo_root: Path, records: list) -> None:
    course_dir = repo_root / "course"
    course_dir.mkdir(parents=True, exist_ok=True)
    save_identity_ledger(course_dir, records)


# ---------------------------------------------------------------------------
# T5-1: persist=False — ledger ausente + sem refs existentes → sem escrita
# ---------------------------------------------------------------------------


def test_persist_false_no_ledger_no_refs_does_not_write(tmp_path):
    """persist=False + ledger ausente + sem refs → in-memory ok, NENHUM arquivo escrito."""
    _write_syllabus(tmp_path)
    course_dir = tmp_path / "course"
    before = set(p.name for p in course_dir.iterdir())

    _build_file_map_timeline_context_from_course(
        {"_repo_root": tmp_path},
        persist=False,
        **_DUMMY_KWARG,
    )

    after = set(p.name for p in course_dir.iterdir())
    new_files = after - before
    assert ".block_identity.json" not in new_files, f"Escreveu ledger em persist=False: {new_files}"
    assert not any(f.endswith(".json") and f != "SYLLABUS.md" for f in new_files), (
        f"Novos arquivos em persist=False: {new_files}"
    )
```

- [ ] **Step 1.2: Run test to verify it fails**

```
cd C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
python -m pytest tests/test_persist_gate.py::test_persist_false_no_ledger_no_refs_does_not_write -v
```
Expected: FAIL — `TypeError: _build_file_map_timeline_context_from_course() got an unexpected keyword argument 'persist'`

- [ ] **Step 1.3: Add `persist` kwarg and gate writes in `index.py`**

In `src/builder/timeline/index.py`, change the function signature at line 1349:

```python
def _build_file_map_timeline_context_from_course(
    course_meta: dict,
    subject_profile=None,
    content_taxonomy: Optional[dict] = None,
    *,
    build_file_map_unit_index_from_course: Callable[[dict, object], list],
    build_file_map_content_taxonomy_from_course: Callable[[dict, object], dict],
    persist: bool = True,
) -> dict:
```

At line 1408, gate the `save_identity_ledger` call:

```python
            # was: save_identity_ledger(_course_dir, _ledger)
            if persist:
                save_identity_ledger(_course_dir, _ledger)
```

At line 1447-1459, gate manifest and curation writes:

```python
        if persist and _mf is not None and _upd_entries != _mf_entries:
            try:
                _mf["entries"] = _upd_entries
                _manifest_path.write_text(
                    json.dumps(_mf, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            except OSError:
                pass
        if persist and _upd_cur_blocks != _cur_blocks:
            try:
                _cur_raw["blocks"] = _upd_cur_blocks
                _curation_file.write_text(
                    json.dumps(_cur_raw, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            except OSError:
                pass
```

- [ ] **Step 1.4: Run test to verify it passes**

```
python -m pytest tests/test_persist_gate.py::test_persist_false_no_ledger_no_refs_does_not_write -v
```
Expected: PASS

- [ ] **Step 1.5: Write the failing test for persist=False + ledger absent + refs exist → hard fail**

Add to `tests/test_persist_gate.py`:

```python
def test_persist_false_ledger_absent_but_refs_exist_raises(tmp_path):
    """persist=False + ledger ausente + refs uuid existentes → BlockIdentityError clara."""
    _write_syllabus(tmp_path)
    # Cria manifest com manual_timeline_block_id uuid-format (simula ref existente)
    manifest = {
        "course": {},
        "entries": [{"id": "e1", "manual_timeline_block_id": "550e8400-e29b-41d4-a716-446655440000"}],
    }
    (tmp_path / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )

    with pytest.raises(BlockIdentityError, match="ledger"):
        _build_file_map_timeline_context_from_course(
            {"_repo_root": tmp_path, "manifest": manifest["course"]},
            persist=False,
            **_DUMMY_KWARG,
        )
```

- [ ] **Step 1.6: Run test to verify it fails (should pass after step 1.3 already gated writes — but BlockIdentityError should fire because `reattach_block_uuids` already raises on empty ledger + has_existing_refs=True)**

```
python -m pytest tests/test_persist_gate.py::test_persist_false_ledger_absent_but_refs_exist_raises -v
```
Expected: PASS (this test actually verifies pre-existing behavior of `reattach_block_uuids`). If FAIL, means the `BlockIdentityError` was being swallowed — fix the except clause at line 1409.

- [ ] **Step 1.7: Write test for persist=False + stale block (in-memory uuid, warning, no write)**

Add to `tests/test_persist_gate.py`:

```python
def test_persist_false_stale_block_in_memory_no_write(tmp_path, caplog):
    """persist=False + ledger tem 0 records matching block → in-memory mint + warning, sem escrita."""
    _write_syllabus(tmp_path)
    # Ledger vazio (sem entries) mas sem refs existentes → deve funcionar in-memory
    _make_ledger(tmp_path, [])

    course_dir = tmp_path / "course"
    before_names = set(p.name for p in course_dir.iterdir())

    with caplog.at_level(logging.WARNING):
        _build_file_map_timeline_context_from_course(
            {"_repo_root": tmp_path},
            persist=False,
            **_DUMMY_KWARG,
        )

    after_names = set(p.name for p in course_dir.iterdir())
    # Ledger DEVE existir (foi criado em _make_ledger), mas NÃO deve ter sido modificado
    ledger_path = course_dir / ".block_identity.json"
    if ledger_path.exists():
        ledger_after = json.loads(ledger_path.read_text(encoding="utf-8"))
        assert ledger_after == [], "persist=False não deve ter escrito no ledger"

    new_files = after_names - before_names
    # Nenhum arquivo novo além do que já existia
    for f in new_files:
        assert not f.endswith(".json"), f"Arquivo escrito em persist=False: {f}"
```

- [ ] **Step 1.8: Run test to verify behavior**

```
python -m pytest tests/test_persist_gate.py::test_persist_false_stale_block_in_memory_no_write -v
```
Expected: PASS (ledger was pre-created as empty, reattach mints in-memory, persist=False skips save)

- [ ] **Step 1.9: Write test confirming persist=True still writes (regression guard)**

Add to `tests/test_persist_gate.py`:

```python
def test_persist_true_writes_ledger(tmp_path):
    """persist=True (default) → ledger escrito normalmente."""
    _write_syllabus(tmp_path)
    course_dir = tmp_path / "course"

    _build_file_map_timeline_context_from_course(
        {"_repo_root": tmp_path},
        persist=True,
        **_DUMMY_KWARG,
    )

    assert (course_dir / ".block_identity.json").exists(), "persist=True deve escrever ledger"
```

- [ ] **Step 1.10: Run all gate tests**

```
python -m pytest tests/test_persist_gate.py -v
```
Expected: All PASS

- [ ] **Step 1.11: Run full suite to confirm no regression**

```
python -m pytest tests -q --tb=short 2>&1 | tail -20
```
Expected: green (same pass count as before)

- [ ] **Step 1.12: Commit**

```
git add src/builder/timeline/index.py tests/test_persist_gate.py
git commit -m "$(cat <<'EOF'
fix(timeline): adiciona persist kwarg; gatea ledger/manifest/curation (Task 5)

persist=True (default) mantém comportamento atual — minta/migra.
persist=False (medição) nunca grava: ledger read-only, migração in-memory.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Thread `persist` through facade and wire `persist=False` to measurement scripts

**Files:**
- Modify: `src/builder/facade/teaching_timeline.py:93-100`
- Modify: `scripts/rebuild_diff.py:35`
- Test: `tests/test_persist_gate.py` (add test for facade passthrough)

**Interfaces:**
- Consumes: `_build_file_map_timeline_context_from_course(..., persist=True)` from Task 1
- Produces: facade closure `build_file_map_timeline_context_from_course(course_meta, subject_profile=None, content_taxonomy=None, *, persist=True)` — threads persist through
- Produces: `rebuild_diff.py` calls with `persist=False`

- [ ] **Step 2.1: Write failing test for facade persist threading**

Add to `tests/test_persist_gate.py`:

```python
def test_facade_threads_persist_false(tmp_path, monkeypatch):
    """facade.build_file_map_timeline_context_from_course passa persist=False p/ index."""
    _write_syllabus(tmp_path)
    course_dir = tmp_path / "course"

    # Call via engine alias (which uses the facade)
    import src.builder.engine as engine
    engine._build_file_map_timeline_context_from_course(
        {"_repo_root": tmp_path},
        persist=False,
    )

    # Should NOT have written ledger
    assert not (course_dir / ".block_identity.json").exists(), (
        "engine facade com persist=False não deve escrever ledger"
    )
```

- [ ] **Step 2.2: Run test to verify it fails**

```
python -m pytest tests/test_persist_gate.py::test_facade_threads_persist_false -v
```
Expected: FAIL — `TypeError: build_file_map_timeline_context_from_course() got an unexpected keyword argument 'persist'`

- [ ] **Step 2.3: Thread `persist` through the facade closure in `teaching_timeline.py`**

In `src/builder/facade/teaching_timeline.py`, change the closure at line 93:

```python
    def build_file_map_timeline_context_from_course(
        course_meta, subject_profile=None, content_taxonomy=None, *, persist=True
    ):
        return timeline_build_file_map_timeline_context_from_course(
            course_meta,
            subject_profile,
            content_taxonomy,
            build_file_map_unit_index_from_course=build_file_map_unit_index_from_course,
            build_file_map_content_taxonomy_from_course=build_file_map_content_taxonomy_from_course,
            persist=persist,
        )
```

- [ ] **Step 2.4: Run facade test**

```
python -m pytest tests/test_persist_gate.py::test_facade_threads_persist_false -v
```
Expected: PASS

- [ ] **Step 2.5: Wire `persist=False` in `rebuild_diff.py`**

In `scripts/rebuild_diff.py`, change line 35:

```python
    # was:
    # ctx = engine._build_file_map_timeline_context_from_course({**cm, "_repo_root": repo}, sp, content_taxonomy=None)
    ctx = engine._build_file_map_timeline_context_from_course(
        {**cm, "_repo_root": repo}, sp, content_taxonomy=None, persist=False
    )
```

- [ ] **Step 2.6: Run full suite**

```
python -m pytest tests -q --tb=short 2>&1 | tail -20
```
Expected: green

- [ ] **Step 2.7: Commit**

```
git add src/builder/facade/teaching_timeline.py scripts/rebuild_diff.py tests/test_persist_gate.py
git commit -m "$(cat <<'EOF'
fix(timeline): thread persist p/ facade + rebuild_diff persist=False (Task 5)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Prove git-status-clean for all 3 portão scripts (fixture repo test)

The brief's **strong acceptance criterion**: running portão scripts against a committed-clean repo leaves `git status` clean.

Strategy: create a pytest fixture that makes a minimal tmp-repo, runs rebuild_diff logic in-process against it, and asserts no files were written. We cannot use the real repos (they are dirty). We prove the criterion programmatically.

**Files:**
- Test: `tests/test_persist_gate.py` (add fixture-repo test)

**Interfaces:**
- Consumes: `_build_file_map_timeline_context_from_course(..., persist=False)` from Tasks 1-2
- Produces: test proves zero new files written in `course/` after a rebuild_diff-style call

- [ ] **Step 3.1: Write the fixture-repo no-write integration test**

Add to `tests/test_persist_gate.py`:

```python
def test_rebuild_diff_style_call_writes_nothing(tmp_path):
    """Simula exatamente o que rebuild_diff.py faz; verifica que nenhum arquivo é criado."""
    import src.builder.engine as engine

    # Setup: minimal repo with a syllabus + ledger already built (simulates post-initial-build state)
    course_dir = tmp_path / "course"
    course_dir.mkdir()
    (course_dir / "SYLLABUS.md").write_text(
        "## Semana 1 (01/03/2026 - 07/03/2026)\nIntrodução\n", encoding="utf-8"
    )
    # Pre-build ledger (como se o repo tivesse sido buildado uma vez)
    ledger = [
        {
            "uuid": "550e8400-e29b-41d4-a716-446655440001",
            "anchor": {
                "period_start": "2026-03-01",
                "period_end": "2026-03-07",
                "topic_tokens": ["introducao"],
            },
            "display_id_last": "bloco-01",
            "first_seen": "2026-03-01",
            "last_seen": "2026-03-01",
        }
    ]
    save_identity_ledger(course_dir, ledger)

    before_files = {p: p.stat().st_mtime for p in course_dir.rglob("*") if p.is_file()}

    # Exactly what rebuild_diff.py does (with persist=False after our fix)
    cm = {}
    engine._build_file_map_timeline_context_from_course(
        {**cm, "_repo_root": tmp_path}, None, content_taxonomy=None, persist=False
    )

    after_files = {p: p.stat().st_mtime for p in course_dir.rglob("*") if p.is_file()}

    new_files = set(after_files) - set(before_files)
    modified_files = {p for p in set(before_files) & set(after_files) if after_files[p] != before_files[p]}

    assert not new_files, f"rebuild_diff-style call criou arquivos: {[str(p) for p in new_files]}"
    assert not modified_files, f"rebuild_diff-style call modificou arquivos: {[str(p) for p in modified_files]}"
```

- [ ] **Step 3.2: Run integration test**

```
python -m pytest tests/test_persist_gate.py::test_rebuild_diff_style_call_writes_nothing -v
```
Expected: PASS

- [ ] **Step 3.3: Run all gate tests + full suite**

```
python -m pytest tests/test_persist_gate.py -v && python -m pytest tests -q --tb=short 2>&1 | tail -20
```
Expected: all PASS

- [ ] **Step 3.4: Commit**

```
git add tests/test_persist_gate.py
git commit -m "$(cat <<'EOF'
test(timeline): prova fixture-repo que rebuild_diff nao escreve (Task 5)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Investigate and gate any other writes triggered during measurement

The brief says: "Determine: running eval/rebuild_diff on a clean repo writes BEYOND migration (pedagogical_regeneration writes MDs)? If so, gate that too."

This task is research + fix. The `eval_code_block_gold.py` and `compare_resolver.py` read pre-built files and do NOT call `_build_file_map_timeline_context_from_course`. Only `rebuild_diff.py` calls it. Eval scripts do not call `regenerate_pedagogical_files`. Therefore no MD generation is triggered by eval scripts.

However, confirm by checking call chains:

- [ ] **Step 4.1: Trace what eval_code_block_gold actually calls**

```
python -m pytest tests/test_persist_gate.py -v -s 2>&1 | tail -20
```

Manually verify: `eval_code_block_gold.py` → `compare_repo` → reads `.timeline_index.json` + `.block_identity.json` (file reads only). No build path invoked.

`eval_assignments.py` → `_resolve_unit_block_tags` → calls `build_file_map_timeline_context_from_course_fn` (if wired). Check if eval_assignments wires the function:

- [ ] **Step 4.2: Read eval_assignments.py to verify it doesn't call build_file_map**

```
python -c "
import sys; sys.path.insert(0, '.'); 
import ast, pathlib
src = pathlib.Path('scripts/eval_assignments.py').read_text()
print([n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name) and 'timeline' in n.id.lower()])
"
```

If `eval_assignments.py` calls `_resolve_unit_block_tags` which wires `build_file_map_timeline_context_from_course_fn`, it WILL trigger writes unless `persist=False` is threaded through `_resolve_unit_block_tags` too.

- [ ] **Step 4.3: Check _resolve_unit_block_tags signature**

```python
# In src/builder/engine.py or src/builder/timeline/index.py — grep:
grep -n "resolve_unit_block_tags" src/builder/engine.py | head -20
```

If `_resolve_unit_block_tags` accepts `build_file_map_timeline_context_from_course_fn` as a kwarg, then `eval_assignments.py` must pass a `persist=False` version (via `functools.partial` or lambda).

- [ ] **Step 4.4: If eval_assignments.py triggers writes, fix it**

If `eval_assignments.py` calls `_resolve_unit_block_tags` with `build_file_map_timeline_context_from_course_fn=_build_file_map_timeline_context_from_course`, change the call to pass a `persist=False` partial:

```python
import functools
_build_ro = functools.partial(engine._build_file_map_timeline_context_from_course, persist=False)
# ... then pass build_file_map_timeline_context_from_course_fn=_build_ro
```

- [ ] **Step 4.5: Add a no-write test for eval_assignments-style call (if applicable)**

If step 4.4 was needed, add to `tests/test_persist_gate.py`:

```python
def test_eval_assignments_style_call_writes_nothing(tmp_path):
    """eval_assignments invoca resolve_unit_block_tags; com persist=False não escreve."""
    import functools
    import src.builder.engine as engine

    course_dir = tmp_path / "course"
    course_dir.mkdir()
    (course_dir / "SYLLABUS.md").write_text(
        "## Semana 1 (01/03/2026 - 07/03/2026)\nIntrodução\n", encoding="utf-8"
    )
    save_identity_ledger(course_dir, [])

    before = {p: p.stat().st_mtime for p in course_dir.rglob("*") if p.is_file()}

    _build_ro = functools.partial(engine._build_file_map_timeline_context_from_course, persist=False)
    engine._resolve_unit_block_tags(
        [],
        {"_repo_root": tmp_path},
        None,
        build_file_map_unit_index_from_course_fn=engine._build_file_map_unit_index_from_course,
        build_file_map_timeline_context_from_course_fn=_build_ro,
        iter_content_taxonomy_topics_fn=engine._iter_content_taxonomy_topics,
        auto_map_entry_subtopic_fn=engine._auto_map_entry_subtopic,
        auto_map_entry_unit_fn=engine._auto_map_entry_unit,
        select_probable_period_for_entry_fn=engine._select_probable_period_for_entry,
        resolve_entry_manual_timeline_block_fn=engine._resolve_entry_manual_timeline_block,
        entry_markdown_text_for_file_map_fn=engine._entry_markdown_text_for_file_map,
    )

    after = {p: p.stat().st_mtime for p in course_dir.rglob("*") if p.is_file()}
    new_files = set(after) - set(before)
    modified = {p for p in set(before) & set(after) if after[p] != before[p]}

    assert not new_files, f"eval_assignments-style criou arquivos: {new_files}"
    assert not modified, f"eval_assignments-style modificou arquivos: {modified}"
```

- [ ] **Step 4.6: Run full suite**

```
python -m pytest tests -q --tb=short 2>&1 | tail -20
```
Expected: green

- [ ] **Step 4.7: Commit any changes from task 4**

```
git add scripts/eval_assignments.py tests/test_persist_gate.py
git commit -m "$(cat <<'EOF'
fix(eval): garante persist=False em eval_assignments (Task 5)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

(Skip commit if nothing changed.)

---

### Task 5: Verify portão and write report

- [ ] **Step 5.1: Run eval_assignments portão**

```
python scripts/eval_assignments.py 2>&1 | tail -10
```
Expected: 5/5 cw0

- [ ] **Step 5.2: Run eval_code_block_gold portão**

```
python scripts/eval_code_block_gold.py "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" 2>&1 | tail -20
```
Expected: funil 7/17 + resolver 12/17 cw1

- [ ] **Step 5.3: Run rebuild_diff portão**

```
python scripts/rebuild_diff.py 2>&1
```
Expected: ES2 0/IA1/MF1/SO0/TCC0 drift (no NEW drift vs baseline)

- [ ] **Step 5.4: Run pytest**

```
python -m pytest tests -q --tb=short 2>&1 | tail -10
```
Expected: green

- [ ] **Step 5.5: Write report to `.git/sdd/task-5-report-fase1.md`**

Include: what was gated, where persist was threaded, what else wrote during measurement, proof of git-status-clean (fixture test result), portão outputs, pytest summary.

- [ ] **Step 5.6: Final commit (if any files remain unstaged)**

```
git add -p  # review and stage only the intended changes
git commit -m "$(cat <<'EOF'
docs(sdd): task-5-report-fase1 — medição read-only portão confirmado

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```
