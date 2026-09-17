"""Recalcula a COBERTURA das referencias de um repo gerado (so a camada de refs).

`reprocess_assignments` nao passa pela camada de referencia — ela roda dentro do
enriquecimento do build. Este driver roda so ela, deterministico e sem Gemini
(sem client, o mapeamento sai do texto), gravando `course/references_curation.json`.

Uso:
    python scripts/refresh_reference_coverage.py "C:/.../X-Tutor" ["C:/.../Y-Tutor"] ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.core.reference_summary import summarize_all_reference_entries  # noqa: E402
from src.builder.engine import _build_file_map_unit_index_from_course  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def refresh(repo: Path, store, profile_name: str = "") -> None:
    manifest_path = repo / "manifest.json"
    if not manifest_path.exists():
        print(f"[skip] {repo.name}: sem manifest.json")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = store.get(profile_name) if profile_name else store.find_by_repo_root(repo)
    if profile is None:
        profile = store.get(str((manifest.get("course") or {}).get("name") or ""))
    if profile is None:
        print(f"[erro] {repo.name}: perfil nao resolvido — o indice de unidades cairia no "
              f"fallback repo-derived e a medicao seria invalida. Use --profile \"<nome>\".")
        return
    course_meta = {**(manifest.get("course") or {}), "_repo_root": repo}
    units = _build_file_map_unit_index_from_course(course_meta, profile)

    builder = type("B", (), {"root_dir": repo})()
    curation = summarize_all_reference_entries(builder, units, None)

    entries = curation.get("entries", {}) or {}
    mapeadas = sum(1 for rec in entries.values() if rec.get("coverage_units"))
    multi = sum(1 for rec in entries.values() if len(rec.get("coverage_units") or []) > 1)
    print(f"[ok] {repo.name}: {len(entries)} refs na curation | {mapeadas} com cobertura "
          f"| {multi} multi-unidade | perfil={'sim' if profile else 'NAO'} | {len(units)} unidades")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    store = SubjectStore()
    alvos, nome = [], ""
    it = iter(argv[1:])
    for arg in it:
        if arg == "--profile":
            nome = next(it, "")
        else:
            alvos.append(arg)
    for raw in alvos:
        refresh(Path(raw).resolve(), store, nome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
