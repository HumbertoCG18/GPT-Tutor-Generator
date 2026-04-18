# Marker LaTeX and Parallel Image Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep `marker` as the preferred advanced backend for LaTeX/structure extraction while introducing a separate, context-aware image-extraction pipeline that preserves mathematically relevant raster content and guarantees that `Image Curator` renders the correct source PDF for each entry.

**Architecture:** The current pipeline mixes three different image concepts: inline images written by `pymupdf4llm`, brute-force PDF image extraction via PyMuPDF, and final `content/images/` consolidation driven only by markdown references. This plan separates concerns explicitly: text/LaTeX remains the responsibility of the text backends, while image recall becomes a dedicated PDF-image pipeline with profile-aware filtering, manifest persistence, and curator-first visibility. The `Image Curator` also stops guessing the PDF by fuzzy `rglob`; it will resolve the exact source PDF from manifest-backed metadata.

**Tech Stack:** Python 3.11, PyMuPDF (`pymupdf`), existing `RepoBuilder` pipeline in `src/builder/engine.py`, tkinter `ImageCurator`, pytest

---

## File Structure

- Modify: `src/builder/engine.py`
  - Introduce pure helpers for image-extraction policy, image-record persistence, and context-aware filtering.
  - Split raw image extraction from final markdown/image consolidation.
  - Persist the exact PDF source for curator usage.
- Modify: `src/ui/image_curator.py`
  - Resolve the correct PDF deterministically from manifest metadata.
  - Prefer entry-backed image groups and exact PDF source over broad repo search.
- Modify: `src/ui/dialogs.py`
  - Update help/settings text only if required by the new image-extraction semantics.
- Modify: `tests/test_core.py`
  - Add policy and pipeline tests for image extraction on math/scanned/exam workloads.
- Modify: `tests/test_image_curation.py`
  - Add tests for Image Curator PDF resolution and any new pure helpers used by the UI.

## Design Rules

- `marker` stays responsible for advanced markdown and LaTeX, not for being the source of truth of exported images.
- PDF image extraction becomes independent from whether the chosen markdown backend referenced the image.
- For `math_heavy`, `exam_pdf`, and `scanned`, optimize for recall first and noise-reduction second.
- Do not discard an image only because it is monochrome or has few colors.
- Preserve enough per-image metadata to support later context-aware decisions without re-opening the original PDF repeatedly.
- `Image Curator` must render the exact source PDF that produced the entry, not “the first matching PDF in raw/”.

## Current Gaps to Close

- `_extract_pdf_images()` in `src/builder/engine.py` is globally aggressive and can discard valid mathematical figures.
- The extracted-image gallery in `src/ui/dialogs.py` applies another aggressive filter and may hide saved images from the operator.
- `content/images/` currently only consolidates images that were referenced by markdown; images extracted in parallel but not linked in markdown are invisible in the final repo.
- `Image Curator._render_pdf_page()` falls back to broad `rglob()` matching when `source_path` is missing or stale, which can show the wrong PDF for an entry.

---

### Task 1: Lock the intended image-pipeline behavior with failing tests

**Files:**
- Modify: `tests/test_core.py`
- Modify: `tests/test_image_curation.py`

- [ ] **Step 1: Add failing tests for image-extraction policy by document profile**

Insert near the existing advanced-backend policy tests in `tests/test_core.py`:

```python
class TestPdfImageExtractionPolicy:
    def _ctx(
        self,
        *,
        profile="math_heavy",
        page_count=116,
        images_count=290,
        suspected_scan=False,
        page_range="",
        extract_images=True,
    ):
        entry = FileEntry(
            source_path="C:/repo/raw/pdfs/material-de-aula/mlp.pdf",
            file_type="pdf",
            category="material-de-aula",
            title="MLP",
            document_profile=profile,
            page_range=page_range,
            extract_images=extract_images,
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
            stall_timeout=300,
        )

    def test_math_heavy_pdf_uses_permissive_image_policy(self):
        ctx = self._ctx(profile="math_heavy")
        policy = engine_module._pdf_image_extraction_policy(ctx)
        assert policy["mode"] == "permissive"
        assert policy["keep_low_color"] is True

    def test_exam_pdf_uses_permissive_image_policy(self):
        ctx = self._ctx(profile="exam_pdf")
        policy = engine_module._pdf_image_extraction_policy(ctx)
        assert policy["mode"] == "permissive"

    def test_scanned_pdf_uses_permissive_image_policy(self):
        ctx = self._ctx(profile="scanned", suspected_scan=True)
        policy = engine_module._pdf_image_extraction_policy(ctx)
        assert policy["mode"] == "permissive"

    def test_general_pdf_keeps_aggressive_noise_filter(self):
        ctx = self._ctx(profile="general", page_count=20, images_count=3)
        policy = engine_module._pdf_image_extraction_policy(ctx)
        assert policy["mode"] == "standard"
        assert policy["keep_low_color"] is False
```

- [ ] **Step 2: Add failing tests for exact source-PDF resolution in the Image Curator**

Append to `tests/test_image_curation.py`:

```python
def test_resolve_entry_pdf_prefers_manifest_raw_target(tmp_path):
    from src.ui.image_curator import _resolve_entry_pdf_path

    repo = tmp_path / "repo"
    pdf_a = repo / "raw" / "pdfs" / "material-de-aula" / "entry-a.pdf"
    pdf_b = repo / "raw" / "pdfs" / "material-de-aula" / "entry-b.pdf"
    pdf_a.parent.mkdir(parents=True)
    pdf_a.write_bytes(b"%PDF-1.4 a")
    pdf_b.write_bytes(b"%PDF-1.4 b")

    entry = {
        "id": "entry-a",
        "source_path": "C:/stale/original.pdf",
        "raw_target": "raw/pdfs/material-de-aula/entry-a.pdf",
    }

    result = _resolve_entry_pdf_path(repo, entry)

    assert result == pdf_a


def test_resolve_entry_pdf_does_not_fallback_to_unrelated_pdf_when_raw_target_exists(tmp_path):
    from src.ui.image_curator import _resolve_entry_pdf_path

    repo = tmp_path / "repo"
    pdf_a = repo / "raw" / "pdfs" / "material-de-aula" / "entry-a.pdf"
    pdf_b = repo / "raw" / "pdfs" / "material-de-aula" / "other.pdf"
    pdf_a.parent.mkdir(parents=True)
    pdf_a.write_bytes(b"%PDF-1.4 a")
    pdf_b.write_bytes(b"%PDF-1.4 b")

    entry = {
        "id": "entry-a",
        "source_path": "",
        "raw_target": "raw/pdfs/material-de-aula/entry-a.pdf",
    }

    result = _resolve_entry_pdf_path(repo, entry)

    assert result == pdf_a
    assert result != pdf_b
```

- [ ] **Step 3: Run the focused failing tests**

Run:

```bash
python -m pytest tests/test_core.py -k "PdfImageExtractionPolicy" -v
python -m pytest tests/test_image_curation.py -k "resolve_entry_pdf" -v
```

Expected: FAIL because the policy helper and curator PDF resolver do not exist yet.

- [ ] **Step 4: Commit the failing-test checkpoint**

```bash
git add tests/test_core.py tests/test_image_curation.py
git commit -m "test: lock parallel image pipeline and curator pdf resolution"
```

---

### Task 2: Extract a dedicated PDF-image policy layer

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Add a pure helper that decides image-extraction policy from backend context**

Insert near the existing advanced-backend helper functions in `src/builder/engine.py`:

```python
def _pdf_image_extraction_policy(ctx: "BackendContext") -> Dict[str, object]:
    effective_profile = (
        ctx.entry.document_profile
        if ctx.entry.document_profile != "auto"
        else ctx.report.suggested_profile
    )
    if effective_profile in {"math_heavy", "exam_pdf", "scanned"} or ctx.report.suspected_scan:
        return {
            "mode": "permissive",
            "min_bytes": 512,
            "min_dimension": 8,
            "max_aspect_ratio": 20.0,
            "keep_low_color": True,
        }
    if effective_profile == "layout_heavy":
        return {
            "mode": "balanced",
            "min_bytes": 1200,
            "min_dimension": 16,
            "max_aspect_ratio": 12.0,
            "keep_low_color": True,
        }
    return {
        "mode": "standard",
        "min_bytes": RepoBuilder._MIN_IMG_BYTES,
        "min_dimension": RepoBuilder._MIN_IMG_DIMENSION,
        "max_aspect_ratio": RepoBuilder._MAX_ASPECT_RATIO,
        "keep_low_color": False,
    }
```

- [ ] **Step 2: Add a pure helper that evaluates whether one extracted image should be kept**

Insert near `_is_noise_image()` in `src/builder/engine.py`:

```python
@staticmethod
def _should_keep_extracted_pdf_image(
    *,
    data: bytes,
    width: int,
    height: int,
    policy: Dict[str, object],
) -> bool:
    if len(data) < int(policy["min_bytes"]):
        return False
    if width < int(policy["min_dimension"]) or height < int(policy["min_dimension"]):
        return False
    ratio = max(width / max(height, 1), height / max(width, 1))
    if ratio > float(policy["max_aspect_ratio"]):
        return False
    if policy.get("keep_low_color"):
        return True
    return not RepoBuilder._is_noise_image(data)
```

- [ ] **Step 3: Run the policy tests**

Run:

```bash
python -m pytest tests/test_core.py -k "PdfImageExtractionPolicy" -v
```

Expected: PASS.

- [ ] **Step 4: Commit the policy layer**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: add profile-aware pdf image extraction policy"
```

---

### Task 3: Make PDF image extraction a dedicated parallel pipeline

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write a failing test proving that math-heavy extraction keeps low-color images**

Add to `tests/test_core.py`:

```python
def test_extract_pdf_images_keeps_low_color_math_image(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    builder = RepoBuilder(repo, {"stall_timeout": 300})

    class FakeDoc:
        page_count = 1

        def __getitem__(self, _idx):
            class FakePage:
                @staticmethod
                def get_images(full=True):
                    return [(17,)]
            return FakePage()

        @staticmethod
        def extract_image(_xref):
            return {
                "image": b"x" * 1500,
                "width": 64,
                "height": 64,
                "ext": "png",
            }

        @staticmethod
        def close():
            return None

    monkeypatch.setattr(engine_module, "pymupdf", mock.Mock(open=lambda *_: FakeDoc()))
    monkeypatch.setattr(engine_module.RepoBuilder, "_is_noise_image", staticmethod(lambda _data: True))

    entry = FileEntry(
        source_path="C:/repo/raw/pdfs/math.pdf",
        file_type="pdf",
        category="material-de-aula",
        title="Math",
        document_profile="math_heavy",
        extract_images=True,
    )
    report = DocumentProfileReport(page_count=1, images_count=1, suggested_profile="math_heavy")
    ctx = engine_module.BackendContext(repo, Path("C:/repo/raw/pdfs/math.pdf"), entry, report, stall_timeout=300)

    out_dir = repo / "staging" / "assets" / "images" / entry.id()
    count = builder._extract_pdf_images(Path("dummy.pdf"), out_dir, ctx=ctx)

    assert count == 1
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/test_core.py -k "keeps_low_color_math_image" -v
```

Expected: FAIL because `_extract_pdf_images()` does not accept `ctx` and still discards low-color images globally.

- [ ] **Step 3: Thread backend context into `_extract_pdf_images()` and apply the policy**

Update `src/builder/engine.py`:

```python
def _extract_pdf_images(
    self,
    pdf_path: Path,
    out_dir: Path,
    pages: Optional[List[int]] = None,
    ctx: Optional["BackendContext"] = None,
) -> int:
    ensure_dir(out_dir)
    doc = pymupdf.open(str(pdf_path))
    policy = _pdf_image_extraction_policy(ctx) if ctx is not None else {
        "mode": "standard",
        "min_bytes": self._MIN_IMG_BYTES,
        "min_dimension": self._MIN_IMG_DIMENSION,
        "max_aspect_ratio": self._MAX_ASPECT_RATIO,
        "keep_low_color": False,
    }
    seen_xrefs: set = set()
    ...
                    if not self._should_keep_extracted_pdf_image(
                        data=data,
                        width=w,
                        height=h,
                        policy=policy,
                    ):
                        continue
```

And update the call site in `_process_pdf()`:

```python
count = self._extract_pdf_images(
    raw_target,
    images_dir,
    pages=parse_page_range(entry.page_range),
    ctx=ctx,
)
```

- [ ] **Step 4: Persist extraction-policy metadata on the manifest item**

In `_process_pdf()` after a successful extraction, add:

```python
item["image_extraction"] = {
    "mode": _pdf_image_extraction_policy(ctx)["mode"],
    "source": "pymupdf-pdf-images",
    "selected_pages": _selected_page_count(ctx),
}
```

- [ ] **Step 5: Run the focused extraction tests**

Run:

```bash
python -m pytest tests/test_core.py -k "PdfImageExtractionPolicy or keeps_low_color_math_image" -v
```

Expected: PASS.

- [ ] **Step 6: Commit the dedicated extraction path**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: run image extraction as a profile-aware parallel pdf pipeline"
```

---

### Task 4: Preserve image context without coupling it to markdown references

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Add a failing test that extracted images survive even when markdown does not reference them**

Append to `tests/test_core.py`:

```python
def test_compact_manifest_keeps_images_dir_even_without_markdown_reference(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    builder = RepoBuilder(repo, {})

    manifest = {
        "entries": [
            {
                "id": "item-1",
                "source_path": str(repo / "raw" / "pdfs" / "a.pdf"),
                "raw_target": "raw/pdfs/a.pdf",
                "images_dir": "staging/assets/images/item-1",
                "base_markdown": None,
                "advanced_markdown": None,
            }
        ]
    }

    result = builder._compact_manifest(manifest)

    assert result["entries"][0]["images_dir"] == "staging/assets/images/item-1"
```

- [ ] **Step 2: Run the focused test**

Run:

```bash
python -m pytest tests/test_core.py -k "keeps_images_dir_even_without_markdown_reference" -v
```

Expected: PASS or controlled baseline. This step exists to lock the contract before further refactors.

- [ ] **Step 3: Add an explicit helper to enumerate curator-visible image sources**

In `src/builder/engine.py`, add:

```python
def _entry_image_source_dirs(root_dir: Path, entry_data: dict) -> List[Path]:
    dirs: List[Path] = []
    entry_id = entry_data.get("id", "")
    if entry_id:
        dirs.append(root_dir / "staging" / "assets" / "inline-images" / entry_id)
    images_dir = entry_data.get("images_dir")
    if images_dir:
        dirs.append(root_dir / images_dir)
    rendered_pages_dir = entry_data.get("rendered_pages_dir")
    if rendered_pages_dir:
        dirs.append(root_dir / rendered_pages_dir)
    return dirs
```

This helper is not for `content/images/` rewrite; it formalizes which image sources are part of the entry’s real image pipeline.

- [ ] **Step 4: Use the helper where image source directories are interpreted**

Thread `_entry_image_source_dirs()` into places that currently manually reconstruct image-source directories, or at minimum reuse the same contract in any new code touched by this round.

- [ ] **Step 5: Run the broader regression slice**

Run:

```bash
python -m pytest tests/test_core.py -k "images_dir or image_extraction or compact_manifest" -v
```

Expected: PASS.

- [ ] **Step 6: Commit the context-preserving image metadata work**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "refactor: preserve entry image pipeline metadata independent of markdown links"
```

---

### Task 5: Make the extracted-image gallery follow the same image-source contract

**Files:**
- Modify: `src/ui/dialogs.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Add a failing test for the shared image-source helper**

Append to `tests/test_core.py`:

```python
def test_entry_image_source_dirs_include_inline_and_extracted_assets(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()

    entry = {
        "id": "abc",
        "images_dir": "staging/assets/images/abc",
        "rendered_pages_dir": "content/images/scanned/abc",
    }

    dirs = engine_module._entry_image_source_dirs(root, entry)

    assert root / "staging" / "assets" / "inline-images" / "abc" in dirs
    assert root / "staging" / "assets" / "images" / "abc" in dirs
    assert root / "content" / "images" / "scanned" / "abc" in dirs
```

- [ ] **Step 2: Run the focused test**

Run:

```bash
python -m pytest tests/test_core.py -k "entry_image_source_dirs" -v
```

Expected: FAIL until the helper exists.

- [ ] **Step 3: Replace duplicated directory guessing in `dialogs.py` with the shared contract**

In `src/ui/dialogs.py`, inside `_build_images_tab()`, replace the manual directory collection logic with a shared-source contract derived from the manifest entry data. If importing the helper directly from `engine.py` is too coupled, add a small UI-side helper with the exact same rules and test it separately.

The intended behavior:

```python
for directory in _entry_image_source_dirs(self._repo_dir, self._data):
    _collect_from(directory)
```

- [ ] **Step 4: Keep the gallery filter but make it UI-only**

Do not use the gallery’s “useful image” filter as a destructive persistence rule. It may stay as a presentation filter for the tab, but the extraction pipeline itself should already have decided what to keep.

- [ ] **Step 5: Run the focused regression**

Run:

```bash
python -m pytest tests/test_core.py -k "entry_image_source_dirs" -v
```

Expected: PASS.

- [ ] **Step 6: Commit the shared gallery-source contract**

```bash
git add src/ui/dialogs.py src/builder/engine.py tests/test_core.py
git commit -m "refactor: unify curator and gallery image source resolution"
```

---

### Task 6: Make Image Curator resolve the correct PDF deterministically

**Files:**
- Modify: `src/ui/image_curator.py`
- Test: `tests/test_image_curation.py`

- [ ] **Step 1: Add a pure resolver for the source PDF**

Insert near the top of `src/ui/image_curator.py`:

```python
def _resolve_entry_pdf_path(repo_dir: Path, entry_data: dict) -> Optional[Path]:
    source_path = str(entry_data.get("source_path") or "").strip()
    raw_target = str(entry_data.get("raw_target") or "").strip()

    if source_path:
        source = Path(source_path)
        if source.exists() and source.suffix.lower() == ".pdf":
            return source

    if raw_target:
        candidate = repo_dir / raw_target
        if candidate.exists() and candidate.suffix.lower() == ".pdf":
            return candidate

    return None
```

- [ ] **Step 2: Run the focused Image Curator resolver tests**

Run:

```bash
python -m pytest tests/test_image_curation.py -k "resolve_entry_pdf" -v
```

Expected: PASS.

- [ ] **Step 3: Replace fuzzy `rglob()` fallback in `_render_pdf_page()`**

Update `src/ui/image_curator.py`:

```python
pdf_path = _resolve_entry_pdf_path(self.repo_dir, self._current_entry)
if not pdf_path:
    self._pdf_canvas.delete("all")
    self._pdf_canvas.create_text(
        10, 10, text="PDF de origem não encontrado para esta entry.", anchor="nw", fill="gray"
    )
    return
```

Remove the current broad fallback:

```python
raw_dir = self.repo_dir / "raw"
...
candidates = list(raw_dir.rglob(f"*{entry_id}*.pdf"))
if not candidates:
    candidates = list(raw_dir.rglob("*.pdf"))
```

because it can bind the curator to the wrong document.

- [ ] **Step 4: Reuse the resolver in crop/save code paths too**

Replace the duplicated source-PDF lookup in `_save_cropped_region()` with `_resolve_entry_pdf_path(...)` so crop/export uses the same exact PDF selection.

- [ ] **Step 5: Run the broader Image Curator regression**

Run:

```bash
python -m pytest tests/test_image_curation.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit the deterministic PDF resolution**

```bash
git add src/ui/image_curator.py tests/test_image_curation.py
git commit -m "fix: resolve exact source pdf in image curator"
```

---

### Task 7: Add one end-to-end regression slice for the new split responsibilities

**Files:**
- Modify: `tests/test_core.py`
- Modify: `tests/test_image_curation.py`

- [ ] **Step 1: Add a regression test proving Marker remains the LaTeX backend while image extraction still runs**

Append to `tests/test_core.py`:

```python
def test_process_pdf_runs_parallel_image_extraction_alongside_marker_backend(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    builder = RepoBuilder(repo, {"stall_timeout": 300})

    entry = FileEntry(
        source_path=str(repo / "raw" / "pdfs" / "math.pdf"),
        file_type="pdf",
        category="material-de-aula",
        title="Math",
        preferred_backend="marker",
        document_profile="math_heavy",
        extract_images=True,
    )
    raw_target = repo / "raw" / "pdfs" / "math.pdf"
    raw_target.parent.mkdir(parents=True)
    raw_target.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(builder, "_profile_pdf", lambda *_: DocumentProfileReport(
        page_count=10,
        images_count=20,
        suggested_profile="math_heavy",
        suspected_scan=False,
    ))
    monkeypatch.setattr(builder.selector, "decide", lambda *_: mock.Mock(
        effective_profile="math_heavy",
        base_backend="pymupdf4llm",
        advanced_backend="marker",
    ))
    monkeypatch.setattr(builder.selector.backends["pymupdf4llm"], "run", lambda *_: BackendRunResult(
        name="pymupdf4llm", layer="base", status="ok", markdown_path="staging/base.md"
    ))
    monkeypatch.setattr(builder.selector.backends["marker"], "run", lambda *_: BackendRunResult(
        name="marker", layer="advanced", status="ok", markdown_path="staging/advanced.md"
    ))
    monkeypatch.setattr(builder, "_extract_pdf_images", lambda *_args, **_kwargs: 3)
    monkeypatch.setattr(builder, "_apply_math_normalization", lambda *_: None)

    item = builder._process_pdf(entry, raw_target)

    assert item["advanced_backend"] == "marker"
    assert item["advanced_markdown"] == "staging/advanced.md"
    assert item["images_dir"] is not None
    assert item["image_extraction"]["mode"] == "permissive"
```

- [ ] **Step 2: Run the focused integration tests**

Run:

```bash
python -m pytest tests/test_core.py -k "parallel_image_extraction_alongside_marker_backend" -v
python -m pytest tests/test_image_curation.py -k "resolve_entry_pdf" -v
```

Expected: PASS.

- [ ] **Step 3: Run the broader regression suite touched by this plan**

Run:

```bash
python -m pytest tests/test_core.py tests/test_image_curation.py tests/test_repo_dashboard.py tests/test_power_management.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit the final regression lock**

```bash
git add tests/test_core.py tests/test_image_curation.py
git commit -m "test: lock marker plus parallel image pipeline behavior"
```

---

## Rollout Checks

- Process a `math_heavy` PDF where some formulas are raster images and confirm:
  - `marker` still produces the advanced markdown.
  - the entry still receives `images_dir` with extracted assets.
  - low-color or monochrome mathematical figures are not silently discarded.
- Process an `exam_pdf` with embedded figure-based questions and confirm the extracted-image count is materially higher than before for affected pages.
- Open `Image Curator` on two entries from different PDFs with similar names and confirm the rendered PDF page belongs to the selected entry, not a repo-wide fallback.
- Confirm the curator can still crop from the same correct PDF after the resolver change.
- Confirm the extracted-images gallery still loads without errors for entries that only have `images_dir`, only inline-images, or both.

## Self-Review

- Spec coverage: the plan covers the split of responsibilities (`marker` for LaTeX, dedicated image pipeline for recall), profile-aware image retention, context-preserving metadata, and deterministic PDF resolution in `Image Curator`.
- Placeholder scan: no `TODO`/`TBD` placeholders remain; each task includes concrete files, code, commands, and expected outcomes.
- Type consistency: helper names and signatures are used consistently across tasks: `_pdf_image_extraction_policy`, `_should_keep_extracted_pdf_image`, `_entry_image_source_dirs`, and `_resolve_entry_pdf_path`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-07-marker-latex-and-parallel-image-pipeline.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
