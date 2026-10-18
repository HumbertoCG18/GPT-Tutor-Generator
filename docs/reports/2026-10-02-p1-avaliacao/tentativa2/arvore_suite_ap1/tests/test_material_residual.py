import json
import types
from src.builder.core.summary_core import (
    load_summary_cache, write_summary_cache, assign_concepts_to_block,
)


def _fake_builder(tmp_path, options, blocks):
    b = types.SimpleNamespace()
    b.root_dir = tmp_path
    b.options = options
    b._load_timeline_blocks = lambda: blocks
    return b


def test_residual_skipped_when_option_disabled(tmp_path, monkeypatch):
    """Regressao: sem opt-in, o residual NAO resolve client (zero rede).

    Operacoes leves (unprocess/reject) chamam regenerate na UI thread com
    options={}; se o client fosse resolvido e chamado aqui, o app travaria.
    """
    import src.builder.ops.pedagogical_regeneration as pr

    called = {"resolve": False}

    def _boom(builder):
        called["resolve"] = True
        raise AssertionError("client NAO deve ser resolvido com a opcao OFF")

    monkeypatch.setattr(pr, "_resolve_gemini_client", _boom)
    b = _fake_builder(tmp_path, {}, [{"id": "bloco-01", "topic_text": "x"}])
    entries = [{"id": "e1", "auto_tags": [], "title": "orfao"}]
    out = pr.run_material_residual(b, entries)
    assert called["resolve"] is False
    assert out == entries  # inalterado


def test_residual_runs_when_option_enabled(tmp_path, monkeypatch):
    import src.builder.ops.pedagogical_regeneration as pr

    class _FakeRes:
        keywords = ["maquina", "turing"]

    class _FakeClient:
        def summarize_bundle(self, **kw):
            return _FakeRes()

    monkeypatch.setattr(pr, "_resolve_gemini_client", lambda builder: _FakeClient())
    blocks = [{"id": "bloco-02", "topic_text": "maquina de turing",
               "primary_topic_label": "Turing"}]
    b = _fake_builder(tmp_path, {"enable_material_residual": True}, blocks)
    entries = [{"id": "e1", "auto_tags": [], "title": "slides turing machine"}]
    out = pr.run_material_residual(b, entries)
    assert "bloco:bloco-02" in out[0]["auto_tags"]


def test_cache_roundtrip(tmp_path):
    write_summary_cache(tmp_path, "material_curation.json", {"version": 1, "entries": {"e1": {"x": 1}}})
    data = load_summary_cache(tmp_path, "material_curation.json")
    assert data["entries"]["e1"]["x"] == 1


def test_cache_missing_returns_empty(tmp_path):
    assert load_summary_cache(tmp_path, "material_curation.json") == {"version": 1, "entries": {}}


def test_assign_concepts_picks_best_block():
    blocks = [
        {"id": "bloco-01", "topic_text": "logica de predicados", "primary_topic_label": "Logica"},
        {"id": "bloco-02", "topic_text": "maquina de turing", "primary_topic_label": "Turing"},
    ]
    bid, conf = assign_concepts_to_block(["maquina", "turing"], blocks)
    assert bid == "bloco-02"
    assert conf > 0


from src.builder.core.summary_core import summarize_residual_materials


class _Counter:
    """extract_concepts callable com contador de chamadas."""
    def __init__(self, concepts):
        self.concepts = concepts
        self.calls = 0
    def __call__(self, text):
        self.calls += 1
        return list(self.concepts)


def test_residual_assigns_block_and_caches(tmp_path):
    blocks = [{"id": "bloco-02", "topic_text": "maquina de turing", "primary_topic_label": "Turing"}]
    orphans = [{"id": "e1", "_text": "slides sobre turing machine"}]
    extract = _Counter(["maquina", "turing"])
    result = summarize_residual_materials(tmp_path, orphans, blocks, extract, cap=5)
    assert result["e1"]["primary_block_id"] == "bloco-02"
    from src.builder.core.summary_core import load_summary_cache
    cached = load_summary_cache(tmp_path, "material_curation.json")
    assert "e1" in cached["entries"]


def test_residual_respects_cap(tmp_path):
    orphans = [{"id": f"e{i}", "_text": "turing"} for i in range(10)]
    blocks = [{"id": "bloco-02", "topic_text": "turing"}]
    extract = _Counter(["turing"])
    summarize_residual_materials(tmp_path, orphans, blocks, extract, cap=3)
    assert extract.calls == 3


def test_residual_cache_hit_skips_client(tmp_path):
    from src.builder.core.summary_core import write_summary_cache
    write_summary_cache(tmp_path, "material_curation.json",
                        {"version": 1, "entries": {"e1": {"primary_block_id": "bloco-02", "concepts": ["x"]}}})
    extract = _Counter(["t"])
    summarize_residual_materials(tmp_path, [{"id": "e1", "_text": "t"}], [{"id": "bloco-02"}], extract, cap=5)
    assert extract.calls == 0  # cache hit
