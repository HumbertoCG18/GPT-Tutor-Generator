"""Sincroniza um tutor com o Moodle do curso (campanha SYNC, 2026-09-03). Headless, como o reprocess.

    python scripts/sync_moodle.py "Laboratório de Redes de Computadores" --dry-run   # S1: so o diff estrutural
    python scripts/sync_moodle.py laboratorio-de-redes-de-computadores --dry-run       # por slug

--dry-run (S1): pull da estrutura (moodle_pull --dry-run numa raiz temporaria, sem downloads), diff contra o manifest
(novos / alterados / sumidos / iguais / links / fora) e nada mais. Token lido de moddle/.env, nunca impresso.
S2/S3 (import do delta, regeneracao, SYNC_REPORT) entram nos proximos itens.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

GEN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GEN))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.builder.sources.moodle_sync import format_diff, sync_diff  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402


def _profile(store, key: str):
    for name in store.names():
        p = store.get(name)
        if name == key or getattr(p, "slug", "") == key:
            return p
    return None


def pull_structure(course_id: str, root: Path) -> list:
    """core_course_get_contents cru via moodle_pull --dry-run (sem downloads)."""
    cmd = [sys.executable, str(GEN / "scripts" / "moodle_pull.py"), "--course", str(course_id), "--root", str(root), "--dry-run"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"moodle_pull falhou ({r.returncode}):\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    return json.loads((root / "raw" / "moodle" / "contents.json").read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("curso", help="nome ou slug do perfil em subjects.json")
    ap.add_argument("--dry-run", action="store_true", help="S1: so o diff estrutural (unico modo por enquanto)")
    ap.add_argument("--root", help="raiz do pull (default: pasta temporaria)")
    args = ap.parse_args(argv)
    if not args.dry_run:
        print("so --dry-run por enquanto (S2/S3 entram nos proximos itens)")
        return 2
    prof = _profile(SubjectStore(), args.curso)
    if prof is None or not getattr(prof, "moodle_course_id", "") or not getattr(prof, "repo_root", ""):
        print(f"perfil nao encontrado ou sem moodle_course_id/repo_root: {args.curso!r}")
        return 1
    repo = Path(prof.repo_root)
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    root = Path(args.root) if args.root else Path(tempfile.mkdtemp(prefix="sync-"))
    contents = pull_structure(prof.moodle_course_id, root)
    diff = sync_diff(manifest.get("entries", []), contents)
    print(f"[sync --dry-run] {prof.name} (curso {prof.moodle_course_id}) x {repo.name}: {len(manifest.get('entries', []))} entries")
    print(format_diff(diff))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
