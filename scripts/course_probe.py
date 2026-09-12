"""Sonda canonica de indice/unidade: EXATAMENTE o caminho de producao
(W1/W2), persist=False. Regra da campanha 2 (U2): numero de sonda que nao
passe por aqui nao vale como gate. Padrao extraido de rebuild_diff.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.builder.engine as engine  # noqa: E402


def _course_meta(repo: Path) -> dict:
    mp = repo / "manifest.json"
    cm = json.loads(mp.read_text(encoding="utf-8")).get("course", {}) if mp.exists() else {}
    return {**cm, "_repo_root": repo}


def compute_production_taxonomy(sp) -> dict:
    repo = Path(getattr(sp, "repo_root", "") or "")
    return engine._build_rich_content_taxonomy(repo, _course_meta(repo), sp)


def compute_production_index(sp) -> dict:
    repo = Path(getattr(sp, "repo_root", "") or "")
    cm = _course_meta(repo)
    rich = engine._build_rich_content_taxonomy(repo, cm, sp)
    ctx = engine._build_file_map_timeline_context_from_course(
        cm, sp, content_taxonomy=rich, persist=False
    )
    return engine._persist_enriched_timeline_index(
        ctx.get("timeline_index") or {"version": 4, "blocks": []}
    )
