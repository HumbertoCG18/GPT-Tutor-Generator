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
