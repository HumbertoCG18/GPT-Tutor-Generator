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
