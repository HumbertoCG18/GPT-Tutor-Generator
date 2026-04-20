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
