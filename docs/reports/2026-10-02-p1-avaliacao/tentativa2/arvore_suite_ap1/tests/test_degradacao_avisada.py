import json
import logging

from src.builder.ops.taxonomy_inputs import build_rich_content_taxonomy
from src.builder.extraction.content_taxonomy import collect_strong_heading_candidates


def test_manifest_ausente_avisa(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        out = build_rich_content_taxonomy(
            tmp_path, {"_repo_root": tmp_path}, None,
            taxonomy_fn=lambda cm, sp, live: {"units": [], "n": len(live)},
            filter_live_fn=lambda root, entries: entries,
        )
    assert out["n"] == 0
    assert any("manifest" in r.message.lower() for r in caplog.records)


def test_entries_em_memoria_nao_le_disco(tmp_path):
    # manifest.json NAO existe; entries explicitas passam direto (caminho W1)
    out = build_rich_content_taxonomy(
        tmp_path, {"_repo_root": tmp_path}, None,
        taxonomy_fn=lambda cm, sp, live: {"units": [], "n": len(live)},
        filter_live_fn=lambda root, entries: entries,
        entries=[{"id": "x"}],
    )
    assert out["n"] == 1


def test_heading_md_inexistente_avisa(tmp_path, caplog):
    # caso real vivo: IA artigo-usando-agrupamento -> content/curated/*.md ausente
    entries = [{"id": "quebrado", "approved_markdown": "content/curated/nao-existe.md"}]
    with caplog.at_level(logging.WARNING):
        out = collect_strong_heading_candidates(tmp_path, entries)
    assert out == []
    assert any("nao-existe.md" in r.message for r in caplog.records)
