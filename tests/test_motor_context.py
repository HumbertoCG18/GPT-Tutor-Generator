"""FASE 4 item 5: loader único do motor + memoização por-contexto."""
import json

from src.builder.routing.motor.context import build_motor_context, load_repo_artifact


def _write(repo, rel, data):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")


def _fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "course/.timeline_index.json", {"blocks": [
        {"id": "bloco-01", "block_uuid": "u-1", "period_start": "2026-03-01",
         "sessions": [{"date": "2026-03-02", "label": "Aula 1"}]},
        {"id": "bloco-02", "block_uuid": "u-2", "period_start": "2026-03-08",
         "sessions": [{"date": "2026-03-09", "label": "Aula 2"}]},
    ]})
    _write(repo, "course/.card_block_map.json", {"card x": {"blocks": ["bloco-01"]}})
    _write(repo, "course/.lessons_index.json", {"by_date": {"2026-03-02": "inducao"}})
    return repo


def test_build_motor_context_loads_artifacts(tmp_path):
    ctx = build_motor_context(_fixture_repo(tmp_path), "Curso X")
    assert [b["id"] for b in ctx.blocks] == ["bloco-01", "bloco-02"]
    assert ctx.lessons_index == {"2026-03-02": "inducao"}
    assert ctx.course_name == "Curso X"
    assert ctx.block_by_ref("u-2")["id"] == "bloco-02"


def test_load_repo_artifact_missing_or_corrupt(tmp_path):
    assert load_repo_artifact(tmp_path, "nao/existe.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{quebrado", encoding="utf-8")
    assert load_repo_artifact(tmp_path, "bad.json") == {}


def test_global_df_memoized_per_context(tmp_path):
    from src.builder.routing.motor.disambiguator import _global_df
    ctx = build_motor_context(_fixture_repo(tmp_path))
    first = _global_df(ctx)
    assert _global_df(ctx) is first          # mesma instância = cache hit
    ctx2 = build_motor_context(_fixture_repo(tmp_path))
    assert _global_df(ctx2) is not first     # contexto novo = cache próprio


def test_modal_years_memoized_per_context(tmp_path):
    from src.builder.routing.motor.window_provider import _modal_years
    ctx = build_motor_context(_fixture_repo(tmp_path))
    first = _modal_years(ctx)
    assert _modal_years(ctx) is first
    assert "2026" in first
