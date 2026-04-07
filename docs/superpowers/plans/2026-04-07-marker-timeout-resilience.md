# Marker Timeout Resilience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make long-running advanced PDF extraction more resilient by reducing unnecessary OCR pressure, using smaller Marker chunks only for genuinely large workloads, scaling stall timeouts for heavy documents, and preventing Windows sleep from interrupting builds.

**Architecture:** Keep the extraction pipeline centralized in `src/builder/engine.py`, but extract the current Marker and timeout heuristics into small pure helpers that can be tested directly. Add a tiny Windows-only power-management helper in `src/utils/power.py`, expose it through app settings, and wrap the top-level build entry points so the protection applies uniformly to full, incremental, and single-entry runs.

**Tech Stack:** Python, pytest, existing builder pipeline in `src/builder/engine.py`, Tk UI settings in `src/ui/dialogs.py`, Windows `SetThreadExecutionState`

---

## File Structure

- `src/builder/engine.py`
  - Extract pure helper functions for advanced-backend workload sizing, Marker chunk sizing, Marker OCR forcing, and adaptive stall timeouts.
  - Stop treating `formula_priority` as an implicit `--force_ocr` trigger for Marker.
  - Apply the adaptive chunk-size and timeout policies in Marker and Docling execution.
  - Add small wrapper methods so build entry points can run under a power guard without deeply nesting their existing bodies.
- `src/utils/power.py`
  - New Windows-specific power helper that prevents system sleep during active builds and becomes a no-op on non-Windows platforms.
- `src/ui/theme.py`
  - Add persistent config default for `prevent_sleep_during_build`.
- `src/ui/dialogs.py`
  - Add a settings checkbox for the new sleep-prevention option.
  - Refine backlog markdown-status helpers so “processed only” is not mislabeled as curated/final.
- `src/ui/app.py`
  - Pass `prevent_sleep_during_build` into builder options.
  - Add queue-pruning helpers that remove already-processed items from the active queue snapshot when a manifest checkpoint exists.
  - Reconcile pending-operation snapshots against the manifest before resuming builds.
  - Expose an explicit processing-status column in the backlog tree.
- `src/ui/repo_dashboard.py`
  - Stop reporting raw `subject.queue` length when part of that queue is already represented in the repo manifest.
- `tests/test_core.py`
  - Add focused tests for the new pure policy helpers and the app-to-builder options handoff.
- `tests/test_repo_dashboard.py`
  - Add coverage that queue metrics only count unprocessed items when manifest entries already exist.
- `tests/test_power_management.py`
  - Add direct tests for the Windows sleep-prevention helper.

## Implementation Notes

- Use processed-page count, not raw PDF page count alone, when deciding whether a workload is “large”. A 200-page PDF with `page_range="1-10"` should not switch to 10-page chunks.
- Marker chunk-size policy for heavy workloads:
  - keep `20` pages when the selected workload is below `80` pages
  - switch to `10` pages only when the selected workload is `>= 80` pages
- Marker `--force_ocr` policy:
  - enable only when the user explicitly checked `Forçar OCR`
  - or when profiling marked the PDF as `suspected_scan=True`
  - do **not** enable merely because `formula_priority=True`
- Queue/backlog reconciliation:
  - treat the repo manifest as the source of truth for “already processed”
  - when a file in the in-memory queue has `source_path` already present in `manifest.json`, prune it from the active queue snapshot
  - do this before resuming a paused build and during UI refresh checkpoints, so the visible queue and dashboard counts shrink as entries land in the manifest
  - keep the dedupe key based on normalized `source_path`, not only title or filename
- Processing-state model for UI:
  - `Processado (só staging)` means the file already virou `entry` no manifest, mas ainda não foi promovido para destino final do tutor
  - `Processado (sem markdown)` means a `manifest entry` existe, porém ainda não há markdown utilizável associado
  - `Curado/final` means existe markdown final em destino final do repositório
  - `Aprovado/final` means o `approved_markdown` é a referência final
  - removing an item from `Fila a processar` must happen as soon as it becomes `Processado`, not only when it becomes `Curado/final`
- Adaptive stall timeout policy:
  - Marker heavy/layout workload with `40-79` selected pages: `max(base_timeout, 1800)`
  - Marker heavy/layout workload with `>= 80` selected pages: `max(base_timeout, 2700)`
  - Docling heavy/scanned/exam workload with `40-79` selected pages: `max(base_timeout, 1200)`
  - Docling heavy/scanned/exam workload with `>= 80` selected pages or `images_count >= 200`: `max(base_timeout, 1800)`
- Sleep prevention:
  - Windows only
  - default enabled
  - no display wake-lock, only system-sleep prevention
  - release the lock in `finally` even on exception/cancel

---

### Task 1: Lock the new Marker and timeout policy with failing tests

**Files:**
- Modify: `tests/test_core.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Add failing tests for adaptive Marker chunking, OCR forcing, and timeout scaling**

Insert the following block near the existing Marker helper tests in `tests/test_core.py`:

```python
class TestAdvancedBackendPolicies:
    def _ctx(
        self,
        *,
        page_count=116,
        page_range="",
        profile="math_heavy",
        images_count=290,
        force_ocr=False,
        formula_priority=False,
        suspected_scan=False,
        stall_timeout=300,
    ):
        entry = FileEntry(
            source_path="C:/repo/raw/pdfs/material-de-aula/mlp.pdf",
            file_type="pdf",
            category="material-de-aula",
            title="MLP",
            document_profile=profile,
            preferred_backend="marker",
            page_range=page_range,
            force_ocr=force_ocr,
            formula_priority=formula_priority,
        )
        report = DocumentProfileReport(
            page_count=page_count,
            images_count=images_count,
            suggested_profile=profile,
            suspected_scan=suspected_scan,
        )
        return engine_module.BackendContext(
            Path("C:/repo"),
            Path("C:/repo/raw/pdfs/material-de-aula/mlp.pdf"),
            entry,
            report,
            stall_timeout=stall_timeout,
        )

    def test_large_heavy_marker_workload_uses_10_page_chunks(self):
        ctx = self._ctx(page_count=116, profile="math_heavy")
        assert engine_module._marker_chunk_size_for_workload(ctx) == 10

    def test_medium_heavy_marker_workload_keeps_20_page_chunks(self):
        ctx = self._ctx(page_count=60, profile="math_heavy")
        assert engine_module._marker_chunk_size_for_workload(ctx) == 20

    def test_formula_priority_no_longer_forces_marker_ocr(self):
        ctx = self._ctx(formula_priority=True, suspected_scan=False, force_ocr=False)
        assert engine_module._should_force_ocr_for_marker(ctx) is False

    def test_manual_force_ocr_still_forces_marker_ocr(self):
        ctx = self._ctx(force_ocr=True, suspected_scan=False)
        assert engine_module._should_force_ocr_for_marker(ctx) is True

    def test_scanned_pdf_still_forces_marker_ocr(self):
        ctx = self._ctx(suspected_scan=True)
        assert engine_module._should_force_ocr_for_marker(ctx) is True

    def test_large_heavy_marker_timeout_is_raised_to_2700(self):
        ctx = self._ctx(page_count=116, profile="math_heavy", stall_timeout=300)
        assert engine_module._advanced_cli_stall_timeout("marker", ctx) == 2700

    def test_large_heavy_docling_timeout_is_raised_to_1800(self):
        ctx = self._ctx(page_count=116, profile="math_heavy", stall_timeout=300)
        assert engine_module._advanced_cli_stall_timeout("docling", ctx) == 1800

    def test_page_range_drives_large_workload_decision(self):
        ctx = self._ctx(page_count=200, page_range="1-10", profile="math_heavy")
        assert engine_module._marker_chunk_size_for_workload(ctx) == 20
```

- [ ] **Step 2: Run the focused tests and confirm they fail because the helpers do not exist yet**

Run:

```bash
python -m pytest tests/test_core.py -k "TestAdvancedBackendPolicies" -v
```

Expected: FAIL with missing helper names such as `_marker_chunk_size_for_workload`, `_should_force_ocr_for_marker`, and `_advanced_cli_stall_timeout`.

- [ ] **Step 3: Commit the failing-test checkpoint**

```bash
git add tests/test_core.py
git commit -m "test: lock advanced backend workload policy"
```

---

### Task 2: Implement adaptive Marker chunk sizing and stricter OCR forcing

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Add small pure helpers for selected-page count, Marker chunk sizing, and Marker OCR forcing**

Insert these helpers near `_build_marker_page_chunks()` in `src/builder/engine.py`:

```python
def _selected_page_count(ctx: "BackendContext") -> int:
    if ctx.pages is not None:
        return len(ctx.pages)
    return max(int(ctx.report.page_count or 0), 0)


def _marker_chunk_size_for_workload(ctx: "BackendContext") -> int:
    effective_profile = (
        ctx.entry.document_profile
        if ctx.entry.document_profile != "auto"
        else ctx.report.suggested_profile
    )
    selected_pages = _selected_page_count(ctx)
    if effective_profile in {"math_heavy", "layout_heavy"} and selected_pages >= 80:
        return 10
    return 20


def _should_force_ocr_for_marker(ctx: "BackendContext") -> bool:
    return bool(ctx.entry.force_ocr) or bool(ctx.report.suspected_scan)
```

- [ ] **Step 2: Wire the new helpers into Marker command construction and chunking**

Replace the current hard-coded policy in `MarkerCLIBackend` with:

```python
chunk_size = _marker_chunk_size_for_workload(ctx)
chunks = _build_marker_page_chunks(ctx.pages, ctx.report.page_count, chunk_size=chunk_size)
```

and:

```python
wants_force_ocr = _should_force_ocr_for_marker(ctx)
```

Also add one explicit policy log before chunking:

```python
logger.info(
    "  [marker] Chunk policy: %d páginas por chunk para %d páginas selecionadas.",
    chunk_size,
    _selected_page_count(ctx),
)
```

- [ ] **Step 3: Run the focused policy tests**

Run:

```bash
python -m pytest tests/test_core.py -k "TestAdvancedBackendPolicies and (chunk or force or scanned or page_range)" -v
```

Expected: PASS for the chunk-size and OCR-forcing assertions.

- [ ] **Step 4: Commit the Marker policy changes**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: adapt marker chunking and ocr forcing"
```

---

### Task 3: Implement adaptive stall timeouts for Marker and Docling

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Add a shared advanced-backend timeout helper**

Insert this helper near the existing timeout logic in `src/builder/engine.py`:

```python
def _advanced_cli_stall_timeout(backend_name: str, ctx: "BackendContext") -> int:
    base_timeout = int(ctx.stall_timeout or 300)
    effective_profile = (
        ctx.entry.document_profile
        if ctx.entry.document_profile != "auto"
        else ctx.report.suggested_profile
    )
    selected_pages = _selected_page_count(ctx)
    heavy_profiles = {"math_heavy", "layout_heavy", "scanned", "exam_pdf"}

    if backend_name == "marker":
        if effective_profile in {"math_heavy", "layout_heavy"} and selected_pages >= 80:
            return max(base_timeout, 2700)
        if effective_profile in {"math_heavy", "layout_heavy"} and selected_pages >= 40:
            return max(base_timeout, 1800)
        return base_timeout

    if backend_name == "docling":
        if effective_profile in heavy_profiles and (selected_pages >= 80 or ctx.report.images_count >= 200):
            return max(base_timeout, 1800)
        if effective_profile in heavy_profiles and selected_pages >= 40:
            return max(base_timeout, 1200)
        return base_timeout

    return base_timeout
```

- [ ] **Step 2: Replace the Marker-only timeout special case and apply the helper to Docling too**

Update `DoclingCLIBackend.run()` and `MarkerCLIBackend.run()` to pass the adaptive value explicitly:

```python
stall_timeout = _advanced_cli_stall_timeout("docling", ctx)
returncode, stdout_lines, stderr_lines = _run_cli_with_timeout(
    cmd, "docling", ctx, stall_timeout=stall_timeout
)
```

and:

```python
stall_timeout = _advanced_cli_stall_timeout("marker", ctx)
```

Delete `_marker_stall_timeout()` after the helper fully replaces it.

- [ ] **Step 3: Add one log line that explains the effective timeout chosen**

Use:

```python
logger.info(
    "  [%s] Stall timeout efetivo: %ds para %d páginas selecionadas.",
    backend_name,
    stall_timeout,
    _selected_page_count(ctx),
)
```

Place this immediately before `_run_cli_with_timeout(...)` for both advanced backends.

- [ ] **Step 4: Run the timeout policy tests**

Run:

```bash
python -m pytest tests/test_core.py -k "TestAdvancedBackendPolicies and timeout" -v
```

Expected: PASS for the Marker and Docling timeout assertions.

- [ ] **Step 5: Commit the adaptive-timeout work**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: scale advanced backend stall timeouts"
```

---

### Task 4: Add a Windows-only sleep-prevention helper with direct tests

**Files:**
- Create: `src/utils/power.py`
- Create: `tests/test_power_management.py`

- [ ] **Step 1: Add failing tests for the power helper**

Create `tests/test_power_management.py` with:

```python
from unittest import mock

import src.utils.power as power


class TestPreventSystemSleep:
    def test_noop_on_non_windows(self, monkeypatch):
        monkeypatch.setattr(power.sys, "platform", "linux")
        with power.prevent_system_sleep(enabled=True, reason="build"):
            pass

    def test_calls_windows_api_on_enter_and_exit(self, monkeypatch):
        monkeypatch.setattr(power.sys, "platform", "win32")
        calls = []

        class _Kernel32:
            @staticmethod
            def SetThreadExecutionState(value):
                calls.append(value)
                return 1

        monkeypatch.setattr(
            power.ctypes,
            "windll",
            mock.Mock(kernel32=_Kernel32()),
            raising=False,
        )

        with power.prevent_system_sleep(enabled=True, reason="build"):
            pass

        assert calls == [
            power.ES_CONTINUOUS | power.ES_SYSTEM_REQUIRED,
            power.ES_CONTINUOUS,
        ]
```

- [ ] **Step 2: Run the new test file and confirm it fails because the module does not exist yet**

Run:

```bash
python -m pytest tests/test_power_management.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.utils.power'`.

- [ ] **Step 3: Implement the helper module**

Create `src/utils/power.py` with:

```python
from __future__ import annotations

import contextlib
import ctypes
import logging
import sys

logger = logging.getLogger(__name__)

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


@contextlib.contextmanager
def prevent_system_sleep(enabled: bool = True, reason: str = "build"):
    active = bool(enabled) and sys.platform == "win32"
    if not active:
        yield
        return

    try:
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        )
        logger.info("[power] Sleep prevention enabled: %s", reason)
        yield
    finally:
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            logger.info("[power] Sleep prevention released: %s", reason)
        except Exception:
            logger.warning("[power] Failed to release sleep prevention cleanly.", exc_info=True)
```

- [ ] **Step 4: Run the power-helper tests**

Run:

```bash
python -m pytest tests/test_power_management.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the helper**

```bash
git add src/utils/power.py tests/test_power_management.py
git commit -m "feat: add windows sleep prevention helper"
```

---

### Task 5: Wire sleep prevention through app config and top-level builds

**Files:**
- Modify: `src/ui/theme.py`
- Modify: `src/ui/dialogs.py`
- Modify: `src/ui/app.py`
- Modify: `src/builder/engine.py`
- Modify: `tests/test_core.py`

- [ ] **Step 1: Add a config default and a focused options-handoff test**

Extend `tests/test_core.py` with:

```python
def test_app_build_options_include_sleep_prevention(monkeypatch):
    from src.ui.app import TutorRepoBuilderApp

    app = TutorRepoBuilderApp.__new__(TutorRepoBuilderApp)
    app.var_default_mode = mock.Mock(get=lambda: "auto")
    app.var_default_ocr_language = mock.Mock(get=lambda: "por,eng")
    app.config_obj = mock.Mock(
        get=lambda key: {
            "image_format": "png",
            "stall_timeout": 300,
            "prevent_sleep_during_build": True,
        }[key]
    )

    options = TutorRepoBuilderApp._build_options(app)

    assert options["prevent_sleep_during_build"] is True
```

- [ ] **Step 2: Add the new config key to `AppConfig.DEFAULTS`**

In `src/ui/theme.py`, add:

```python
"prevent_sleep_during_build": True,
```

inside `AppConfig.DEFAULTS`.

- [ ] **Step 3: Add a settings checkbox and persist it**

In `src/ui/dialogs.py`, add a new `BooleanVar` and checkbox near the stall-timeout setting:

```python
self._var_prevent_sleep = tk.BooleanVar(
    value=bool(self.config.get("prevent_sleep_during_build", True))
)
ttk.Checkbutton(
    tab_proc,
    text="Impedir suspensão do Windows durante builds longos",
    variable=self._var_prevent_sleep,
).grid(row=next_row + 1, column=0, columnspan=2, sticky="w", pady=(8, 0))
```

Persist it in `_save()` with:

```python
self.config.set("prevent_sleep_during_build", self._var_prevent_sleep.get())
```

- [ ] **Step 4: Pass the option into builder options**

Update `TutorRepoBuilderApp._build_options()` in `src/ui/app.py`:

```python
return {
    "default_processing_mode": self.var_default_mode.get(),
    "default_ocr_language": self.var_default_ocr_language.get(),
    "image_format": self.config_obj.get("image_format"),
    "stall_timeout": self.config_obj.get("stall_timeout"),
    "prevent_sleep_during_build": self.config_obj.get("prevent_sleep_during_build", True),
}
```

- [ ] **Step 5: Wrap the top-level builder entry points with the power guard**

In `src/builder/engine.py`, import the helper:

```python
from src.utils.power import prevent_system_sleep
```

Then split each public top-level entry point into a thin wrapper plus implementation body:

```python
def build(self) -> None:
    with prevent_system_sleep(
        enabled=bool(self.options.get("prevent_sleep_during_build", True)),
        reason=f"build:{self.root_dir.name}",
    ):
        self._build_impl()
```

Apply the same pattern to:

```python
def incremental_build(self) -> None:
    with prevent_system_sleep(
        enabled=bool(self.options.get("prevent_sleep_during_build", True)),
        reason=f"incremental-build:{self.root_dir.name}",
    ):
        self._incremental_build_impl()


def process_single(self, entry: "FileEntry", force: bool = False) -> str:
    with prevent_system_sleep(
        enabled=bool(self.options.get("prevent_sleep_during_build", True)),
        reason=f"process-single:{entry.id()}",
    ):
        return self._process_single_impl(entry, force=force)
```

Move the current method bodies into `_build_impl`, `_incremental_build_impl`, and `_process_single_impl` with no logic changes besides indentation.

- [ ] **Step 6: Run the focused regression tests**

Run:

```bash
python -m pytest tests/test_core.py -k "TestAdvancedBackendPolicies or sleep_prevention" -v
python -m pytest tests/test_power_management.py -v
```

Expected: PASS.

- [ ] **Step 7: Run the broader builder regression slice**

Run:

```bash
python -m pytest tests/test_core.py -k "marker or docling or incremental_build" -v
python -m pytest tests/test_image_curation.py -k "inject or duplicate_exact_description" -v
```

Expected: PASS. The second command is a quick guard that the recent markdown-injection fix still holds after the engine edits.

- [ ] **Step 8: Commit the integration work**

```bash
git add src/builder/engine.py src/utils/power.py src/ui/theme.py src/ui/dialogs.py src/ui/app.py tests/test_core.py tests/test_power_management.py
git commit -m "feat: harden long-running advanced pdf builds"
```

---

### Task 6: Lock queue/backlog reconciliation behavior with failing tests

**Files:**
- Modify: `tests/test_core.py`
- Modify: `tests/test_repo_dashboard.py`
- Modify: `src/ui/app.py`
- Modify: `src/ui/repo_dashboard.py`

- [ ] **Step 1: Add failing app-level tests for queue pruning against the manifest**

Insert the following block in `tests/test_core.py` near the pending-operation tests:

```python
class TestQueueManifestReconciliation:
    def test_prune_processed_queue_entries_removes_manifest_sources(self, tmp_path):
        from src.ui.app import TutorRepoBuilderApp

        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "manifest.json").write_text(
            json.dumps({
                "entries": [
                    {"source_path": str(repo / "raw" / "pdfs" / "a.pdf")},
                ]
            }),
            encoding="utf-8",
        )

        app = TutorRepoBuilderApp.__new__(TutorRepoBuilderApp)
        app.entries = [
            FileEntry(source_path=str(repo / "raw" / "pdfs" / "a.pdf"), file_type="pdf", category="material-de-aula", title="A"),
            FileEntry(source_path=str(repo / "raw" / "pdfs" / "b.pdf"), file_type="pdf", category="material-de-aula", title="B"),
        ]

        remaining = TutorRepoBuilderApp._prune_processed_queue_entries(app, repo, persist=False)

        assert [entry.title for entry in remaining] == ["B"]

    def test_restore_pending_operation_context_drops_processed_entries(self, tmp_path):
        from src.ui.app import TutorRepoBuilderApp

        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "manifest.json").write_text(
            json.dumps({
                "entries": [
                    {"source_path": str(repo / "raw" / "pdfs" / "done.pdf")},
                ]
            }),
            encoding="utf-8",
        )

        app = TutorRepoBuilderApp.__new__(TutorRepoBuilderApp)
        app.var_course_name = mock.Mock(set=lambda *_: None)
        app.var_course_slug = mock.Mock(set=lambda *_: None)
        app.var_semester = mock.Mock(set=lambda *_: None)
        app.var_professor = mock.Mock(set=lambda *_: None)
        app.var_institution = mock.Mock(set=lambda *_: None)
        app.var_repo_root = mock.Mock(set=lambda *_: None)
        app._shutdown_after_build = mock.Mock(set=lambda *_: None)
        app._var_active_subject = mock.Mock(set=lambda *_: None)
        app.refresh_tree = mock.Mock()
        app._save_current_queue = mock.Mock()

        op = PendingOperation(
            operation_type="build",
            requested_mode="incremental",
            repo_root=str(repo),
            entries=[
                FileEntry(source_path=str(repo / "raw" / "pdfs" / "done.pdf"), file_type="pdf", category="material-de-aula", title="Done"),
                FileEntry(source_path=str(repo / "raw" / "pdfs" / "todo.pdf"), file_type="pdf", category="material-de-aula", title="Todo"),
            ],
        )

        TutorRepoBuilderApp._restore_pending_operation_context(app, op)

        assert [entry.title for entry in app.entries] == ["Todo"]
```

- [ ] **Step 2: Add a failing dashboard test that counts only unprocessed queue items**

Append this test to `tests/test_repo_dashboard.py`:

```python
def test_collect_repo_metrics_excludes_manifest_entries_from_queue_count(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    processed = repo_root / "raw" / "pdfs" / "done.pdf"
    queued = repo_root / "raw" / "pdfs" / "todo.pdf"
    processed.parent.mkdir(parents=True)
    (repo_root / "manifest.json").write_text(
        json.dumps({"entries": [{"source_path": str(processed)}]}),
        encoding="utf-8",
    )

    subject = SubjectProfile(
        name="Métodos Formais",
        repo_root=str(repo_root),
        queue=[
            FileEntry(source_path=str(processed), file_type="pdf", category="material-de-aula", title="Done"),
            FileEntry(source_path=str(queued), file_type="pdf", category="material-de-aula", title="Todo"),
        ],
    )

    row = collect_repo_metrics([subject], [])[0]

    assert row.queued_files == 1
```

- [ ] **Step 3: Run the focused tests and confirm they fail**

Run:

```bash
python -m pytest tests/test_core.py -k "QueueManifestReconciliation" -v
python -m pytest tests/test_repo_dashboard.py -k "queue_count" -v
```

Expected: FAIL because the pruning helper does not exist and dashboard still reports the raw queue size.

- [ ] **Step 4: Commit the failing-test checkpoint**

```bash
git add tests/test_core.py tests/test_repo_dashboard.py
git commit -m "test: lock queue and backlog reconciliation"
```

---

### Task 7: Implement queue pruning and safe resume against manifest checkpoints

**Files:**
- Modify: `src/ui/app.py`
- Modify: `src/ui/repo_dashboard.py`
- Modify: `tests/test_core.py`
- Modify: `tests/test_repo_dashboard.py`

- [ ] **Step 1: Add a manifest-source helper and queue-pruning helper to `TutorRepoBuilderApp`**

Insert these helpers near the existing backlog-source helpers in `src/ui/app.py`:

```python
    @staticmethod
    def _normalized_source_key(raw_path: str) -> str:
        return str(Path(raw_path or "")).replace("\\", "/").strip().lower()

    @classmethod
    def _manifest_source_keys_for_repo(cls, repo_dir: Optional[Path]) -> set[str]:
        if not repo_dir:
            return set()
        manifest_path = repo_dir / "manifest.json"
        if not manifest_path.exists():
            return set()
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return set()
        return {
            cls._normalized_source_key(entry.get("source_path", ""))
            for entry in data.get("entries", [])
            if entry.get("source_path")
        }

    def _prune_processed_queue_entries(self, repo_dir: Optional[Path], persist: bool = True) -> list[FileEntry]:
        processed = self._manifest_source_keys_for_repo(repo_dir)
        if not processed:
            return list(self.entries)
        remaining = [
            entry for entry in self.entries
            if self._normalized_source_key(entry.source_path) not in processed
        ]
        if len(remaining) != len(self.entries):
            self.entries = remaining
            self.refresh_tree()
            if persist:
                self._save_current_queue()
        return list(self.entries)
```

- [ ] **Step 2: Reconcile the queue during restore, refresh checkpoints, cancel, and build completion**

Apply the helper in these places:

```python
    def _restore_pending_operation_context(self, op: PendingOperation):
        ...
        self.entries = [FileEntry.from_dict(e.to_dict()) for e in op.entries]
        self._prune_processed_queue_entries(Path(op.repo_root) if op.repo_root else None, persist=False)
        self.refresh_tree()
        self._save_current_queue()
```

Inside both build progress callbacks, add:

```python
                self._prune_processed_queue_entries(repo_dir)
```

before updating the status line, so each new checkpoint shrinks the queue after the previous entry landed in the manifest.

Also call:

```python
self._prune_processed_queue_entries(repo_dir)
```

inside `_on_build_cancelled()`, `_on_build_error()`, and just before the final queue clear in `_on_build_complete()`.

- [ ] **Step 3: Make dashboard queue metrics manifest-aware**

In `src/ui/repo_dashboard.py`, add a small helper:

```python
def _remaining_subject_queue(subject: SubjectProfile, manifest_entries: list[dict]) -> int:
    processed = {
        str(Path(entry.get("source_path", ""))).replace("\\", "/").strip().lower()
        for entry in manifest_entries or []
        if entry.get("source_path")
    }
    return sum(
        1
        for entry in subject.queue
        if str(Path(entry.source_path)).replace("\\", "/").strip().lower() not in processed
    )
```

Then change:

```python
queued_files=len(subject.queue),
```

to:

```python
queued_files=_remaining_subject_queue(subject, manifest.get("entries", []) if repo_path and (repo_path / "manifest.json").exists() else []),
```

using the same manifest payload already loaded in `collect_repo_metrics()`.

- [ ] **Step 4: Run the focused reconciliation tests**

Run:

```bash
python -m pytest tests/test_core.py -k "QueueManifestReconciliation" -v
python -m pytest tests/test_repo_dashboard.py -k "queue_count or manifest_manual_review" -v
```

Expected: PASS.

- [ ] **Step 5: Run a broader regression slice covering incremental builds and pending-operation serialization**

Run:

```bash
python -m pytest tests/test_core.py -k "PendingOperation or incremental_build or QueueManifestReconciliation" -v
python -m pytest tests/test_repo_dashboard.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit the queue/backlog reconciliation work**

```bash
git add src/ui/app.py src/ui/repo_dashboard.py tests/test_core.py tests/test_repo_dashboard.py
git commit -m "feat: reconcile queue state with processed backlog"
```

---

### Task 8: Make backlog status explicit so processed is not confused with curated or approved

**Files:**
- Modify: `src/ui/dialogs.py`
- Modify: `src/ui/app.py`
- Modify: `tests/test_core.py`

- [ ] **Step 1: Add failing status tests that separate processed-only from curated/final**

Update the existing backlog markdown-status tests in `tests/test_core.py` to lock the new wording:

```python
class TestBacklogMarkdownStatus:
    def test_marks_staging_markdown_as_processed_only(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_markdown_status

        entry = {"base_markdown": "staging/markdown-auto/pymupdf4llm/item.md"}
        (tmp_path / "staging" / "markdown-auto" / "pymupdf4llm").mkdir(parents=True)
        (tmp_path / "staging" / "markdown-auto" / "pymupdf4llm" / "item.md").write_text("# x", encoding="utf-8")

        status = _resolve_backlog_markdown_status(entry, tmp_path)

        assert status["status"] == "Processado (só staging)"
        assert status["needs_reprocess"] == "true"

    def test_marks_curated_markdown_as_final(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_markdown_status

        entry = {"curated_markdown": "content/curated/item.md"}
        (tmp_path / "content" / "curated").mkdir(parents=True)
        (tmp_path / "content" / "curated" / "item.md").write_text("# x", encoding="utf-8")

        status = _resolve_backlog_markdown_status(entry, tmp_path)

        assert status["status"] == "Curado/final"
        assert status["needs_reprocess"] == "false"

    def test_marks_approved_markdown_as_approved_final(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_markdown_status

        entry = {"approved_markdown": "content/curated/item.md"}
        (tmp_path / "content" / "curated").mkdir(parents=True)
        (tmp_path / "content" / "curated" / "item.md").write_text("# x", encoding="utf-8")

        status = _resolve_backlog_markdown_status(entry, tmp_path)

        assert status["status"] == "Aprovado/final"
        assert status["needs_reprocess"] == "false"
```

- [ ] **Step 2: Run the focused status tests and confirm they fail under the current wording**

Run:

```bash
python -m pytest tests/test_core.py -k "BacklogMarkdownStatus" -v
```

Expected: FAIL because the current helper still returns coarse labels like `Só staging` and lumps final states together.

- [ ] **Step 3: Update `_resolve_backlog_markdown_status()` to model processed-only, curated, and approved separately**

In `src/ui/dialogs.py`, replace the current return values with these rules:

```python
    candidates = [
        ("approved_markdown", entry_data.get("approved_markdown") or ""),
        ("curated_markdown", entry_data.get("curated_markdown") or ""),
        ("advanced_markdown", entry_data.get("advanced_markdown") or ""),
        ("base_markdown", entry_data.get("base_markdown") or ""),
    ]
```

and:

```python
        if key == "approved_markdown" and rel_posix.startswith(final_prefixes):
            return {
                "status": "Aprovado/final",
                "path": rel,
                "source_key": key,
                "needs_reprocess": "false",
                "note": "Markdown final aprovado e pronto para o tutor.",
            }
        if rel_posix.startswith(final_prefixes):
            return {
                "status": "Curado/final",
                "path": rel,
                "source_key": key,
                "needs_reprocess": "false",
                "note": "Markdown final pronto para o tutor.",
            }
        if rel_posix.startswith("staging/"):
            return {
                "status": "Processado (só staging)",
                "path": rel,
                "source_key": key,
                "needs_reprocess": "true",
                "note": "Arquivo já foi processado, mas ainda não foi promovido para destino final.",
            }
```

Also change the fallback-without-markdown case to:

```python
    return {
        "status": "Processado (sem markdown)",
        "path": "",
        "source_key": "",
        "needs_reprocess": "true",
        "note": "A entry existe no manifest, mas ainda não há markdown associado.",
    }
```

- [ ] **Step 4: Add an explicit status column to the backlog tree**

In `src/ui/app.py`, change:

```python
columns_bk = ("category", "layer", "tags", "title", "backend", "file")
```

to:

```python
columns_bk = ("status", "category", "layer", "tags", "title", "backend", "file")
```

and configure the new column:

```python
self.repo_tree.heading("status", text="Status")
self.repo_tree.column("status", width=150, anchor="center")
```

Then update `_refresh_backlog()` so each row uses the helper:

```python
status = _resolve_backlog_markdown_status(f_data, repo_dir)
```

and inserts:

```python
values=(
    status.get("status", ""),
    f_data.get("category", ""),
    f_data.get("effective_profile", ""),
    f_data.get("tags", ""),
    f_data.get("title", ""),
    f_data.get("base_backend", ""),
    Path(f_data.get("source_path", f_data.get("source_file", ""))).name,
)
```

- [ ] **Step 5: Run the focused status regression**

Run:

```bash
python -m pytest tests/test_core.py -k "BacklogMarkdownStatus" -v
```

Expected: PASS.

- [ ] **Step 6: Run the broader queue/backlog regression slice**

Run:

```bash
python -m pytest tests/test_core.py -k "BacklogMarkdownStatus or QueueManifestReconciliation" -v
python -m pytest tests/test_repo_dashboard.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit the explicit-status UI work**

```bash
git add src/ui/dialogs.py src/ui/app.py tests/test_core.py
git commit -m "feat: distinguish processed backlog from curated and approved"
```

---

## Rollout Checks

- Re-run the problematic PDF with:
  - `document_profile=math_heavy`
  - `preferred_backend=marker`
  - `formula_priority=True`
  - `force_ocr=False`
- Confirm the Marker command no longer includes `--force_ocr` for that case.
- Confirm Marker logs `Chunk policy: 10 páginas por chunk...` only when the selected workload is `>= 80` pages.
- Confirm Docling uses the raised stall timeout on large heavy workloads.
- On Windows, close the lid/suspend behavior should no longer happen during an active build when the machine would otherwise sleep from inactivity.
- Start a long build, let at least one entry finish, then pause/cancel.
- Confirm the visible queue shrinks after manifest checkpoints instead of keeping already-processed items.
- Reopen the app and accept resume for the paused build.
- Confirm the restored queue contains only the remaining unprocessed files, and dashboard `Fila` is lower than the original snapshot when `entries` already exist in the manifest.
- In the backlog tab, confirm a file that only has `staging/...` markdown appears as `Processado (só staging)`, not `Curado/final`.
- Confirm only `approved_markdown` entries show `Aprovado/final`.

Plan complete and saved to `docs/superpowers/plans/2026-04-07-marker-timeout-resilience.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
