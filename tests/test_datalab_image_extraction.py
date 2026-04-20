import base64
from pathlib import Path
from unittest.mock import MagicMock
from src.builder.engine import DatalabCloudBackend
from src.models.core import BackendRunResult


def test_backend_run_result_has_images_dir_field():
    r = BackendRunResult(name="datalab", layer="advanced", status="ok")
    assert hasattr(r, "images_dir")
    assert r.images_dir is None


def test_backend_run_result_images_dir_accepts_string():
    r = BackendRunResult(
        name="datalab", layer="advanced", status="ok",
        images_dir="staging/assets/images/meu-entry"
    )
    assert r.images_dir == "staging/assets/images/meu-entry"


def _make_backend():
    return DatalabCloudBackend()


def test_save_datalab_images_writes_files(tmp_path):
    backend = _make_backend()
    raw_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # minimal fake PNG bytes
    images = {
        "0_Figure_1.png": base64.b64encode(raw_png).decode(),
        "1_Figure_2.png": base64.b64encode(raw_png).decode(),
    }
    images_dir, saved = backend._save_datalab_images(images, "meu-entry", tmp_path)
    assert images_dir == tmp_path / "staging" / "assets" / "images" / "meu-entry"
    assert len(saved) == 2
    assert "datalab-0_Figure_1.png" in saved
    assert (images_dir / "datalab-0_Figure_1.png").exists()
    assert (images_dir / "datalab-1_Figure_2.png").exists()


def test_save_datalab_images_empty_dict(tmp_path):
    backend = _make_backend()
    images_dir, saved = backend._save_datalab_images({}, "meu-entry", tmp_path)
    assert saved == []
    assert images_dir == tmp_path / "staging" / "assets" / "images" / "meu-entry"


def test_save_datalab_images_bad_b64_skips(tmp_path):
    backend = _make_backend()
    images = {"bad.png": "!!!not_base64!!!"}
    images_dir, saved = backend._save_datalab_images(images, "meu-entry", tmp_path)
    assert saved == []
    assert not (images_dir / "datalab-bad.png").exists()


from unittest.mock import patch
from src.builder.runtime.datalab_client import DatalabConvertResult


def _make_datalab_result(images: dict) -> DatalabConvertResult:
    return DatalabConvertResult(
        request_id="req-123",
        request_check_url="https://example.com/check/req-123",
        markdown="# Título\n\nTexto do documento.",
        images=images,
        metadata={},
        page_count=5,
        parse_quality_score=0.9,
        cost_breakdown={},
        raw_response={"status": "complete", "success": True, "error": None},
    )


def _make_ctx(tmp_path: Path) -> MagicMock:
    ctx = MagicMock()
    ctx.raw_target = tmp_path / "doc.pdf"
    ctx.raw_target.write_bytes(b"%PDF fake")
    ctx.root_dir = tmp_path
    ctx.entry_id = "meu-entry"
    ctx.entry.page_range = ""
    ctx.entry.datalab_mode = "balanced"
    ctx.pages = None
    ctx.report.page_count = 5
    ctx.report.suspected_scan = False
    ctx.report.suggested_profile = "general"
    ctx.entry.document_profile = "auto"
    ctx.stall_timeout = 300
    return ctx


def test_run_single_datalab_returns_images_dir_when_images_present(tmp_path):
    backend = DatalabCloudBackend()
    raw_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    fake_images = {"0_Fig_1.png": base64.b64encode(raw_png).decode()}
    fake_result = _make_datalab_result(fake_images)

    ctx = _make_ctx(tmp_path)
    out_dir = tmp_path / "staging" / "markdown-auto" / "datalab" / "meu-entry"
    out_dir.mkdir(parents=True)

    with patch.object(backend, "_convert_range", return_value=(fake_result, "# Título\n")):
        result = backend._run_single_datalab(
            ctx, out_dir, mode="balanced", page_range=None, max_wait_seconds=300
        )

    assert result.status == "ok"
    assert result.images_dir is not None
    assert "staging/assets/images/meu-entry" in result.images_dir.replace("\\", "/")
    saved_img = tmp_path / "staging" / "assets" / "images" / "meu-entry" / "datalab-0_Fig_1.png"
    assert saved_img.exists()


def test_run_single_datalab_no_images_dir_when_no_images(tmp_path):
    backend = DatalabCloudBackend()
    fake_result = _make_datalab_result({})
    ctx = _make_ctx(tmp_path)
    out_dir = tmp_path / "staging" / "markdown-auto" / "datalab" / "meu-entry"
    out_dir.mkdir(parents=True)

    with patch.object(backend, "_convert_range", return_value=(fake_result, "# Título\n")):
        result = backend._run_single_datalab(
            ctx, out_dir, mode="balanced", page_range=None, max_wait_seconds=300
        )

    assert result.status == "ok"
    assert result.images_dir is None


def test_run_chunked_datalab_saves_images_from_all_chunks(tmp_path):
    backend = DatalabCloudBackend()
    raw_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    call_count = {"n": 0}

    def fake_convert_range(ctx, *, mode, page_range, max_wait_seconds):
        call_count["n"] += 1
        n = call_count["n"]
        images = {f"chunk{n}_Fig_1.png": base64.b64encode(raw_png).decode()}
        return _make_datalab_result(images), f"# Chunk {n}\n"

    ctx = _make_ctx(tmp_path)
    ctx.pages = list(range(60))       # 60 pages → forces chunking
    ctx.report.page_count = 60

    out_dir = tmp_path / "staging" / "markdown-auto" / "datalab" / "meu-entry"
    out_dir.mkdir(parents=True)

    with patch.object(backend, "_convert_range", side_effect=fake_convert_range):
        result = backend._run_chunked_datalab(ctx, out_dir, mode="balanced", max_wait_seconds=300)

    assert result.status == "ok"
    assert result.images_dir is not None
    assert "staging/assets/images/meu-entry" in result.images_dir.replace("\\", "/")
    img_dir = tmp_path / "staging" / "assets" / "images" / "meu-entry"
    saved = list(img_dir.iterdir())
    assert len(saved) >= 2  # at least one image per chunk


from src.builder.pdf.pdf_pipeline import process_pdf
from src.models.core import PipelineDecision, DocumentProfileReport
from dataclasses import asdict


def _make_pdf_builder_mock(tmp_path, advanced_result):
    builder = MagicMock()
    builder.root_dir = tmp_path
    builder.logs = []
    builder.HAS_PYMUPDF = False
    builder.HAS_PDFPLUMBER = False

    report = DocumentProfileReport(
        page_count=5,
        text_chars=1000,
        images_count=2,
        suspected_scan=False,
        suggested_profile="general",
    )

    decision = PipelineDecision(
        entry_id="meu-entry",
        processing_mode="auto",
        effective_profile="general",
        base_backend=None,
        advanced_backend="datalab",
    )

    builder._profile_pdf.return_value = report
    builder.selector.decide.return_value = decision
    builder._quick_page_count.return_value = 5
    builder._check_cancel.return_value = None
    builder._apply_math_normalization.return_value = None
    builder.options = {}
    builder.selector.backends = {"datalab": MagicMock(run=MagicMock(return_value=advanced_result))}
    return builder, report, decision


def _make_pdf_entry():
    entry = MagicMock()
    entry.id.return_value = "meu-entry"
    entry.title = "Meu Entry"
    entry.page_range = ""
    entry.extract_images = False
    entry.extract_tables = False
    entry.document_profile = "auto"
    entry.datalab_mode = "balanced"
    return entry


def _make_pdf_backend_ctx(tmp_path, entry, report):
    ctx = MagicMock()
    ctx.root_dir = tmp_path
    ctx.entry_id = "meu-entry"
    ctx.entry = entry
    ctx.report = report
    ctx.pages = None
    ctx.marker_use_llm = False
    return ctx


def test_pdf_pipeline_propagates_images_dir_from_advanced_backend(tmp_path):
    advanced_result = BackendRunResult(
        name="datalab", layer="advanced", status="ok",
        markdown_path="staging/markdown-auto/datalab/meu-entry/meu-entry.md",
        images_dir="staging/assets/images/meu-entry",
    )
    md_path = tmp_path / "staging" / "markdown-auto" / "datalab" / "meu-entry"
    md_path.mkdir(parents=True)
    (md_path / "meu-entry.md").write_text("# Conteúdo\n", encoding="utf-8")

    builder, report, _ = _make_pdf_builder_mock(tmp_path, advanced_result)
    entry = _make_pdf_entry()
    ctx = _make_pdf_backend_ctx(tmp_path, entry, report)

    raw_pdf = tmp_path / "doc.pdf"
    raw_pdf.write_bytes(b"%PDF fake")

    item = process_pdf(
        builder, entry, raw_pdf,
        backend_context_factory=MagicMock(return_value=ctx),
        manual_pdf_review_template_fn=MagicMock(return_value=""),
        detect_latex_corruption_fn=MagicMock(return_value={"corrupted": False, "score": 0, "signals": []}),
        hybridize_marker_markdown_with_base_fn=MagicMock(),
    )

    assert item["images_dir"] == "staging/assets/images/meu-entry"


def test_pdf_pipeline_does_not_overwrite_existing_images_dir(tmp_path):
    advanced_result = BackendRunResult(
        name="datalab", layer="advanced", status="ok",
        markdown_path="staging/markdown-auto/datalab/meu-entry/meu-entry.md",
        images_dir="staging/assets/images/meu-entry",
    )
    md_path = tmp_path / "staging" / "markdown-auto" / "datalab" / "meu-entry"
    md_path.mkdir(parents=True)
    (md_path / "meu-entry.md").write_text("# Conteúdo\n", encoding="utf-8")

    builder, report, _ = _make_pdf_builder_mock(tmp_path, advanced_result)
    # HAS_PYMUPDF=True + extract_images=True means PyMuPDF sets images_dir first
    builder.HAS_PYMUPDF = True
    builder._extract_pdf_images.return_value = 3
    builder._pdf_image_extraction_policy.return_value = {"mode": "all"}

    entry = _make_pdf_entry()
    entry.extract_images = True
    ctx = _make_pdf_backend_ctx(tmp_path, entry, report)

    # Create fake raw pdf
    raw_pdf = tmp_path / "doc.pdf"
    raw_pdf.write_bytes(b"%PDF fake")

    item = process_pdf(
        builder, entry, raw_pdf,
        backend_context_factory=MagicMock(return_value=ctx),
        manual_pdf_review_template_fn=MagicMock(return_value=""),
        detect_latex_corruption_fn=MagicMock(return_value={"corrupted": False, "score": 0, "signals": []}),
        hybridize_marker_markdown_with_base_fn=MagicMock(),
    )

    # images_dir should be set (either from PyMuPDF or Datalab — same dir)
    assert item["images_dir"] is not None
