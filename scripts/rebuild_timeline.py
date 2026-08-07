"""Rebuild timeline-only dos cursos: regenera `.timeline_index.json` v4.

Reusa o pipeline real (`_build_file_map_timeline_context_from_course`) — roda
classifier + voto (Fase 3) + fallback de tópico (Fase 4) + merge de curation
(Fase 5) — e serializa em v4 com `kind` injetado. NÃO toca nenhum outro
artefato do repo (sem LLM, sem reescrever FILE_MAP/glossário/etc).

Uso:
    python scripts/rebuild_timeline.py            # dry-run: só mostra health
    python scripts/rebuild_timeline.py --write    # grava (.bak antes)

Sem argumentos de curso: processa todos os subjects com repo_root válido.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.core import SubjectStore  # noqa: E402
from src.builder import engine  # noqa: E402
from scripts.validate_timeline import (  # noqa: E402
    gate_failures,
    health_report,
    schema_errors,
)

WRITE = "--write" in sys.argv


def _old_health(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return health_report(d.get("blocks", []))


def rebuild_course(name: str, subject_profile) -> bool:
    repo_root = Path(getattr(subject_profile, "repo_root", "") or "")
    if not repo_root or not repo_root.exists():
        print(f"[skip] {name}: repo_root inválido ({repo_root})")
        return True

    manifest_path = repo_root / "manifest.json"
    course_meta = {}
    if manifest_path.exists():
        try:
            course_meta = json.loads(manifest_path.read_text(encoding="utf-8")).get("course", {}) or {}
        except (json.JSONDecodeError, OSError):
            course_meta = {}
    runtime_course_meta = {**course_meta, "_repo_root": repo_root}

    index_path = repo_root / "course" / ".timeline_index.json"
    before = _old_health(index_path)

    try:
        # read_only probe (Plano B): persist=WRITE — dry-run (padrao) fica
        # honesto com o proprio print "não grava"; --write mantem o
        # comportamento de hoje (ledger/manifest/curation migrados).
        rich_taxonomy = engine._build_rich_content_taxonomy(repo_root, runtime_course_meta, subject_profile)
        ctx = engine._build_file_map_timeline_context_from_course(
            runtime_course_meta, subject_profile, content_taxonomy=rich_taxonomy, persist=WRITE
        )
    except Exception as exc:  # pragma: no cover - diagnóstico
        print(f"[FAIL] {name}: build falhou: {exc}")
        return False

    timeline_index = ctx.get("timeline_index") or {"version": 4, "blocks": []}
    # Mesmo serializador do build da GUI (mantém blocos administrativos +
    # transforms já aplicados em build_file_map). NÃO usar _serialize_timeline_index:
    # ele filtra blocos admin e gera um índice divergente do que a GUI grava.
    serialized = engine._persist_enriched_timeline_index(timeline_index)

    after = health_report(serialized.get("blocks", []))
    errs = schema_errors(serialized)
    gates = gate_failures(after)

    def pct(r):
        return f"{r.get('unknown_rate', 0):.0%}/{r.get('class_defect_rate', 0):.0%}"

    print(f"=== {name}  (v{serialized.get('version')}, {after['total']} blocos)")
    print(f"    antes  unk/classdef = {pct(before) if before else 'n/a'}")
    print(f"    depois unk/classdef = {pct(after)}   schema_errs={len(errs)}   gates={gates or 'OK'}")
    print(f"    kinds={after['kinds']}")
    if errs:
        for e in errs[:5]:
            print(f"      schema: {e}")

    if WRITE:
        from src.builder.ops.pedagogical_regeneration import (
            _guard_units_not_silently_lost, UnitsShrinkError,
        )
        try:
            _guard_units_not_silently_lost(
                repo_root, name, len(rich_taxonomy.get("units") or []), serialized,
            )
        except UnitsShrinkError as exc:
            print(f"[FAIL] {name}: {exc} — indice NAO gravado")
            return False
        if index_path.exists():
            backup = index_path.with_suffix(".json.bak")
            backup.write_text(index_path.read_text(encoding="utf-8"), encoding="utf-8")
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"    GRAVADO -> {index_path}  (.bak salvo)")

    return not errs


def main() -> int:
    store = SubjectStore()
    names = store.names()
    if not names:
        print("nenhum subject em subjects.json")
        return 1

    print("MODO:", "WRITE (grava .timeline_index.json)" if WRITE else "DRY-RUN (não grava)")
    print()
    ok = True
    for name in names:
        sp = store.get(name)
        if sp is None:
            continue
        ok = rebuild_course(name, sp) and ok
        print()
    if not WRITE:
        print("dry-run concluído. Rode com --write pra gravar (.bak automático).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
