"""Reprocessa repositorios gerados (reaplica atribuicao arquivo->unidade/bloco)
sem passar nenhum arquivo pelo Datalab/Marker.

Replica o caminho do botao "Reprocessar Repositorio" da UI de forma headless:
RepoBuilder(entries=[]).incremental_build() -> como nao ha novas entries, o loop
de _process_entry/PDF e pulado e so roda regenerate_pedagogical_files
(refresh_manifest_auto_tags -> resolve_unit_block_tags -> indices), lendo o
markdown ja gerado no repo.

Uso:
    python scripts/reprocess_assignments.py "C:/.../X-Tutor"  ["C:/.../*-Tutor"] ...

Faz backup de manifest.json (.bak) antes e imprime cobertura antes/depois.
Deterministico: o residuo Gemini (enable_material_residual) NAO e ligado aqui.
"""
from __future__ import annotations

import glob
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.engine import RepoBuilder  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _apply_flags(options: dict, flag_names: list) -> None:
    """Merge {flag: True} nas options (flags ficam FLAT, como _build_options_from_config)."""
    for name in flag_names:
        options[str(name)] = True


def _parse_argv(argv: list) -> tuple[list, list]:
    """['--flags', 'a,b', pat...] -> (['a','b'], [pat...]); sem --flags -> ([], argv)."""
    pats = list(argv)
    flags: list = []
    if pats and pats[0] == "--flags":
        if len(pats) < 2:
            return [], []
        flags = [f for f in pats[1].split(",") if f]
        pats = pats[2:]
    return flags, pats


def _find_subject_profile(repo: Path, store):
    """Perfil do SubjectStore cujo repo_root resolve para o mesmo dir de `repo`.
    None se nao ha match (ou store vazio, ex.: sem subjects.json)."""
    return store.find_by_repo_root(repo)


def _merge_profile_flags(options: dict, profile) -> None:
    """Injeta feature_flags do perfil VIVO nas options (mesmo padrao flat de
    _build_options_from_config, src/ui/app.py:101-102). Chamado ANTES de
    _apply_flags: o --flags da CLI e aplicado depois e sempre vence."""
    for key, value in (getattr(profile, "feature_flags", None) or {}).items():
        options[str(key)] = value


def _coverage(manifest_path: Path) -> tuple[int, int]:
    """(materiais_com_bloco, total_materiais) lendo auto_tags bloco: do manifest."""
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    total = with_block = 0
    for e in m.get("entries", []):
        if e.get("file_type") == "pdf" or e.get("category"):
            total += 1
            tags = e.get("auto_tags") or []
            if any(str(t).startswith("bloco:") for t in tags) or e.get("manual_timeline_block_id"):
                with_block += 1
    return with_block, total


def reprocess(repo: Path, flags: list, store=None) -> None:
    manifest_path = repo / "manifest.json"
    if not manifest_path.exists():
        print(f"[skip] {repo.name}: sem manifest.json")
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    course_meta = manifest.get("course", {}) or {}
    options = manifest.get("options", {}) or {}

    if store is None:
        store = SubjectStore()
    profile = _find_subject_profile(repo, store)
    if profile is not None:
        _merge_profile_flags(options, profile)
        print(f"[profile] {repo.name}: perfil '{profile.name}' aplicado (feature_flags={profile.feature_flags})")

    _apply_flags(options, flags)  # CLI --flags aplicado por ultimo: sempre vence
    if flags:
        print(f"[flags] {repo.name}: {', '.join(flags)}")

    before = _coverage(manifest_path)
    backup = manifest_path.with_suffix(".json.bak")
    shutil.copy2(manifest_path, backup)

    builder = RepoBuilder(root_dir=repo, course_meta=course_meta, entries=[], options=options,
                          subject_profile=profile)
    builder.incremental_build()

    after = _coverage(manifest_path)
    print(
        f"[ok] {repo.name}: bloco {before[0]}/{before[1]} -> {after[0]}/{after[1]} "
        f"(backup: {backup.name})"
    )


def main(argv: list) -> int:
    flags, argv = _parse_argv(argv)
    if not argv:
        print(__doc__)
        return 2
    repos: list[Path] = []
    for pat in argv:
        hits = [Path(p) for p in glob.glob(pat)]
        repos.extend(h for h in (hits or [Path(pat)]) if h.is_dir())
    if not repos:
        print("nenhum repo encontrado")
        return 1
    for repo in repos:
        reprocess(repo, flags)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
