"""Sincroniza um tutor com o Moodle do curso (campanha SYNC, 2026-09-03). Headless, como o reprocess.

    python scripts/sync_moodle.py "Laboratório de Redes de Computadores" --dry-run   # S1: so o diff estrutural
    python scripts/sync_moodle.py laboratorio-de-redes-de-computadores --dry-run       # por slug
    python scripts/sync_moodle.py <slug> --apply [--repo <copia>] [--no-prune]         # S2+S3: sincroniza

--dry-run (S1): pull da estrutura (moodle_pull --dry-run numa raiz temporaria, sem downloads), diff contra o manifest
(novos / alterados / sumidos / iguais / links / fora) e nada mais. Token lido de moddle/.env, nunca impresso.
--apply (S2/S3): pull --pdf na raiz do curso (pai do stash do perfil; baixa SO o que nao existe; paginas entram como .html, S6d), varre o
stash, monta o plano (plan_import), executa: unprocess dos alterados e dos sumidos (--no-prune: so marca
`moodle_missing_since`), incremental_build com os novos + links de referencia (extrai so o novo; motor em tudo).
--repo aponta para uma COPIA do tutor (protocolo: copia antes do original).
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
sys.path.insert(0, str(GEN / "scripts"))
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


def _run_pull(course_id: str, root: Path, pdf: bool) -> list:
    cmd = [sys.executable, str(GEN / "scripts" / "moodle_pull.py"), "--course", str(course_id), "--root", str(root),
           "--pdf" if pdf else "--dry-run"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"moodle_pull falhou ({r.returncode}):\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    return json.loads((root / "raw" / "moodle" / "contents.json").read_text(encoding="utf-8"))


def pull_structure(course_id: str, root: Path) -> list:
    """core_course_get_contents cru via moodle_pull --dry-run (sem downloads)."""
    return _run_pull(course_id, root, pdf=False)


def apply_sync(prof, repo: Path, manifest: dict, store, *, root=None, prune: bool = True) -> int:
    """S2+S3: pull --pdf, plano, unprocess/marca, incremental_build (extrai o novo, motor em tudo)."""
    from datetime import date
    import reprocess_assignments as ra
    from src.builder.core.stash_import import scan_stash_cards
    from src.builder.engine import RepoBuilder
    from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan
    from src.builder.sources.moodle_sync import (decision_diff, formula_index, mark_sync_changes, plan_import,
                                                 render_sync_report, snapshot_decisions)
    from src.utils.helpers import write_json_manifest

    stash = Path(getattr(prof, "stash_folder", "") or "")
    root = root or (stash.parent if stash.name == "stash" else stash)
    stash = root / "stash"
    contents = _run_pull(prof.moodle_course_id, root, pdf=True)
    links = json.loads((root / "links.json").read_text(encoding="utf-8")) if (root / "links.json").is_file() else []
    nomes_path = stash / ".moodle_nomes.json"
    nomes = json.loads(nomes_path.read_text(encoding="utf-8")) if nomes_path.is_file() else {}
    entries = manifest.get("entries", [])
    diff = sync_diff(entries, contents)
    print(f"[sync --apply] {prof.name} x {repo.name}: {len(entries)} entries")
    print(format_diff(diff))
    frases = []
    for titulo, topicos in (_parse_units_from_teaching_plan(getattr(prof, "teaching_plan", "") or "") or []):
        frases.append(str(titulo or "").lower())
        frases.extend(str(t[0] if isinstance(t, (tuple, list)) else t).lower() for t in topicos or [])
    scan = scan_stash_cards(stash, frases_do_plano=[f for f in frases if len(f) >= 6])
    defaults = {"processing_mode": prof.default_mode, "ocr_language": prof.default_ocr_lang,
                "preferred_backend": prof.default_backend, "datalab_mode": prof.default_datalab_mode, "document_profile": ""}
    plan = plan_import(diff, contents, scan, links, entries, nomes=nomes, defaults=defaults, prune_removed=prune)
    print(f"[plano] add {len(plan.add)} · readd {len(plan.readd)} · prune {len(plan.prune)} · mark {len(plan.mark)} · "
          f"links {len(plan.links)} · review {len(plan.review)} · ignorados {plan.ignorados[:8]}")
    # raw/moodle do pull vai para o repo: e a estrutura que o hook da Fase 3a le na regeneracao
    (repo / "raw" / "moodle").mkdir(parents=True, exist_ok=True)
    for f in ("contents.json", "sections.json", "labels.json"):
        src = root / "raw" / "moodle" / f
        if src.is_file():
            (repo / "raw" / "moodle" / f).write_bytes(src.read_bytes())
    options = manifest.get("options", {}) or {}
    profile = ra._find_subject_profile(repo, store) or prof
    ra._merge_profile_flags(options, profile)
    course_meta = manifest.get("course", {}) or {}
    before = snapshot_decisions(entries)
    builder = RepoBuilder(root_dir=repo, course_meta=course_meta, entries=[], options=options, subject_profile=profile)
    for eid in plan.readd + plan.prune:
        print(f"  unprocess {eid}")
        builder.unprocess(eid)
    if plan.mark:
        m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
        for e in m.get("entries", []):
            if e.get("id") in plan.mark:
                e["moodle_missing_since"] = date.today().isoformat()
                e["include_in_bundle"] = False
        write_json_manifest(repo / "manifest.json", m)
    new_entries = plan.add + plan.links
    builder = RepoBuilder(root_dir=repo, course_meta=course_meta, entries=new_entries, options=options, subject_profile=profile,
                          progress_callback=lambda i, n, t: print(f"  ({i + 1}/{n}) {t[:70]}", flush=True))
    builder.incremental_build()
    failed = list(getattr(builder, "failed_entries", []) or [])
    # S3: diff de decisoes antes -> depois, "mudou, confira", SYNC_REPORT
    when = date.today().isoformat()
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    dd = decision_diff(before, m.get("entries", []))
    n_mark = mark_sync_changes(m.get("entries", []), dd["moved"], when=when)
    write_json_manifest(repo / "manifest.json", m)
    report = render_sync_report(diff, dd, when=when, curso=prof.name, ignorados=plan.ignorados, review=plan.review,
                                formulas=formula_index(m.get("entries", []), repo),
                                plan_counts=f"add {len(plan.add)} readd {len(plan.readd)} prune {len(plan.prune)} mark {len(plan.mark)} links {len(plan.links)}")
    (repo / "course").mkdir(parents=True, exist_ok=True)
    (repo / "course" / "SYNC_REPORT.md").write_text(report, encoding="utf-8")
    print(f"[sync] {repo.name}: {len(new_entries)} entries novas ({len(plan.links)} links), {len(failed)} falha(s) | "
          f"decisoes que se moveram: {len(dd['moved'])} (marcadas {n_mark}) | removidas {len(dd['removed'])} | course/SYNC_REPORT.md")
    for f in failed[:10]:
        print("   !!", str(f)[:160])
    return 0 if not failed else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("curso", help="nome ou slug do perfil em subjects.json")
    ap.add_argument("--dry-run", action="store_true", help="S1: so o diff estrutural")
    ap.add_argument("--apply", action="store_true", help="S2/S3: baixa o delta, importa, regenera")
    ap.add_argument("--repo", help="repo-tutor alvo (default: repo_root do perfil; use uma COPIA primeiro)")
    ap.add_argument("--root", help="raiz do pull (default: dry-run = pasta temporaria; apply = pai do stash do perfil)")
    ap.add_argument("--no-prune", action="store_true", help="sumidos ficam marcados (moodle_missing_since) em vez de removidos")
    args = ap.parse_args(argv)
    if not (args.dry_run or args.apply):
        print("use --dry-run ou --apply")
        return 2
    store = SubjectStore()
    prof = _profile(store, args.curso)
    if prof is None or not getattr(prof, "moodle_course_id", "") or not getattr(prof, "repo_root", ""):
        print(f"perfil nao encontrado ou sem moodle_course_id/repo_root: {args.curso!r}")
        return 1
    repo = Path(args.repo) if args.repo else Path(prof.repo_root)
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if args.dry_run:
        root = Path(args.root) if args.root else Path(tempfile.mkdtemp(prefix="sync-"))
        contents = pull_structure(prof.moodle_course_id, root)
        print(f"[sync --dry-run] {prof.name} (curso {prof.moodle_course_id}) x {repo.name}: {len(entries)} entries")
        print(format_diff(sync_diff(entries, contents)))
        return 0
    return apply_sync(prof, repo, manifest, store, root=Path(args.root) if args.root else None, prune=not args.no_prune)


if __name__ == "__main__":
    raise SystemExit(main())
