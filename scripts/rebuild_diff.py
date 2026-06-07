"""Rebuild-diff dry-run dos cursos reais: compara unit_slug/kind por bloco
(indice gravado x rebuild com o codigo atual). NAO grava. Guard de regressao
do matcher posicional.

Uso: python scripts/rebuild_diff.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.core import SubjectStore  # noqa: E402
import src.builder.engine as engine  # noqa: E402
from src.builder.timeline.index import _serialize_timeline_index  # noqa: E402

BASE = Path(os.environ.get("TUTOR_COURSES_DIR", r"C:\Users\Humberto\Documents\GitHub"))


def _safe(s: str) -> str:
    """Drop chars the Windows console (cp1252) can't encode, so prints never crash."""
    return (s or "").encode("cp1252", "ignore").decode("cp1252")


def diff_course(name: str, sp) -> None:
    repo = Path(getattr(sp, "repo_root", "") or "")
    idx_path = repo / "course" / ".timeline_index.json"
    if not idx_path.exists():
        print(f"[skip] {name}: sem indice ({idx_path})")
        return
    old = {b.get("id"): b for b in json.loads(idx_path.read_text(encoding="utf-8")).get("blocks", [])}
    cm = json.loads((repo / "manifest.json").read_text(encoding="utf-8")).get("course", {}) if (repo / "manifest.json").exists() else {}
    ctx = engine._build_file_map_timeline_context_from_course({**cm, "_repo_root": repo}, sp, content_taxonomy=None)
    new = _serialize_timeline_index(ctx.get("timeline_index") or {"version": 4, "blocks": []})
    print(f"=== {name} ({len(new['blocks'])} blocos) ===")
    changed = 0
    for b in new["blocks"]:
        ob = old.get(b["id"], {})
        du = (ob.get("unit_slug", ""), b.get("unit_slug", ""))
        dk = (ob.get("kind", ""), b.get("kind", ""))
        if du[0] != du[1] or dk[0] != dk[1]:
            changed += 1
            print(f"  {b['id']:9} unit {du[0][:20] or '-'} -> {du[1][:20] or '-'} | kind {dk[0] or '-'} -> {dk[1] or '-'} | {_safe(b.get('primary_topic_label') or '')[:30]}")
    print(f"  ({changed} blocos mudaram)\n")


def main() -> int:
    store = SubjectStore()
    for name in store.names():
        sp = store.get(name)
        if sp is not None:
            diff_course(name, sp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
