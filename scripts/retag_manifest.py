"""Re-roda resolve_unit_block_tags sobre o manifest de um repo (re-tag file->bloco).

NAO re-extrai markdown - so recomputa computed_block_id/unit/band e auto_tags com
a logica atual (inclui o degrau card->bloco). Aplica o gabarito-cards a repos ja
processados. Dry-run por padrao; --write grava com backup .bak.

Uso:
    python -m scripts.retag_manifest <repo_root> [--subject NOME] [--write]
"""
from __future__ import annotations

import json
import sys
from functools import partial
from pathlib import Path


def summarize_changes(before, after) -> dict:
    after_by_id = {str(e.get("id")): e for e in after}
    changes = []
    for b in before:
        eid = str(b.get("id"))
        a = after_by_id.get(eid, {})
        old = str(b.get("computed_block_id") or "")
        new = str(a.get("computed_block_id") or "")
        if old != new:
            changes.append({"id": eid, "from": old, "to": new})
    return {"total": len(before), "changed": len(changes), "changes": changes}


def _resolve_subject_profile(repo_root: Path, subject_name: str):
    from src.models.core import SubjectStore
    store = SubjectStore()
    if subject_name:
        return store.get(subject_name)
    target = str(repo_root).replace("\\", "/").rstrip("/").casefold()
    for name in store.names():
        sp = store.get(name)
        rr = str(getattr(sp, "repo_root", "") or "").replace("\\", "/").rstrip("/").casefold()
        if rr and rr == target:
            return sp
    return None


def retag(repo_root: Path, subject_profile):
    from src.builder.engine import (
        _resolve_unit_block_tags, _build_file_map_unit_index_from_course,
        _build_file_map_timeline_context_from_course, _iter_content_taxonomy_topics,
        _auto_map_entry_subtopic, _auto_map_entry_unit, _select_probable_period_for_entry,
        _resolve_entry_manual_timeline_block, _entry_markdown_text_for_file_map,
    )
    manifest = json.loads((repo_root / "manifest.json").read_text(encoding="utf-8"))
    before = manifest.get("entries", [])
    # read_only probe (Plano B): retag() so LE (mesmo com --write, quem grava o
    # manifest e o proprio script, abaixo); persist=False evita que o helper
    # migre/grave ledger, manifest.json e curation por baixo dos panos so por
    # ter sido chamado (achado: Task 4 §0 do Plano B).
    after = _resolve_unit_block_tags(
        before, {"_repo_root": repo_root}, subject_profile,
        build_file_map_unit_index_from_course_fn=_build_file_map_unit_index_from_course,
        build_file_map_timeline_context_from_course_fn=partial(
            _build_file_map_timeline_context_from_course, persist=False
        ),
        iter_content_taxonomy_topics_fn=_iter_content_taxonomy_topics,
        auto_map_entry_subtopic_fn=_auto_map_entry_subtopic,
        auto_map_entry_unit_fn=_auto_map_entry_unit,
        select_probable_period_for_entry_fn=_select_probable_period_for_entry,
        resolve_entry_manual_timeline_block_fn=_resolve_entry_manual_timeline_block,
        entry_markdown_text_for_file_map_fn=_entry_markdown_text_for_file_map,
    )
    return manifest, before, after


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    write = "--write" in argv
    subject_name = ""
    if "--subject" in argv:
        i = argv.index("--subject")
        if i + 1 < len(argv):
            subject_name = argv[i + 1]
    pos = [a for a in argv if not a.startswith("-") and a != subject_name]
    if not pos:
        print("uso: python -m scripts.retag_manifest <repo_root> [--subject NOME] [--write]")
        return 2
    repo_root = Path(pos[0])
    sp = _resolve_subject_profile(repo_root, subject_name)
    if sp is None:
        print(f"AVISO: nenhum SubjectProfile casou repo_root={repo_root}. Unidades virao do repo (fallback).")
    manifest, before, after = retag(repo_root, sp)
    rep = summarize_changes(before, after)
    print(f"Entries: {rep['total']}  |  computed_block_id mudados: {rep['changed']}")
    for c in rep["changes"]:
        print(f"  {c['id']:<40} {c['from'] or '(orfao)':<12} -> {c['to'] or '(orfao)'}")
    if not write:
        print("\nDry-run. Use --write para gravar.")
        return 0
    manifest["entries"] = after
    path = repo_root / "manifest.json"
    backup = path.with_suffix(".json.retag.bak")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGravado. Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
