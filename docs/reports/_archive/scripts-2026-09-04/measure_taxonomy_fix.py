"""Medicao do fix de perda de topicos do plano de ensino (2026-08-18) em sandbox.

BEFORE = o repo como esta em producao (taxonomia gerada pelo codigo antigo).
AFTER  = mesmo repo reprocessado com o codigo atual. Reusa a mecanica de
`measure_flip` (snapshot -> analyze: gold de unidade, pinos, deltas) e soma a
regua por material (`eval_ground_truth`) e a contagem de topicos da taxonomia.

Uso:
    robocopy "<repo-tutor>" "<SANDBOX_DIR>/sandbox-<SIGLA>" /E /XD .git
    python scripts/measure_taxonomy_fix.py <SIGLA> <SANDBOX_DIR>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.core import SubjectStore  # noqa: E402
from scripts.measure_flip import COURSES, FixedStore, analyze, snap  # noqa: E402
from scripts.reprocess_assignments import reprocess  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _taxonomy_counts(sandbox: Path) -> dict:
    path = sandbox / "course" / ".content_taxonomy.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {u.get("slug", ""): len(u.get("topics", []) or []) for u in data.get("units", [])}


def _material_ruler(sandbox: Path, sigla: str) -> dict:
    """Regua arquivo->bloco. Roda o harness oficial (nao reimplementa o score)."""
    labels = ROOT / "docs" / "reports" / f"ground_truth_{sigla}.csv"
    if not labels.exists():
        return {}
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "eval_ground_truth.py"), str(sandbox), str(labels), "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return {"erro": (proc.stderr or "")[-400:]}
    try:
        return json.loads(proc.stdout)
    except Exception:
        return {"erro": "saida nao-JSON"}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2 or args[0] not in COURSES:
        print(__doc__)
        return 2
    sigla, base = args[0], Path(args[1])
    sandbox = base / f"sandbox-{sigla}"
    if not (sandbox / "manifest.json").exists():
        print(f"[erro] sandbox nao copiado: {sandbox}")
        return 2

    profile = SubjectStore().get(COURSES[sigla])
    if profile is None:
        print(f"[erro] perfil nao achado: {COURSES[sigla]}")
        return 2

    tax_before = _taxonomy_counts(sandbox)
    ruler_before = _material_ruler(sandbox, sigla)
    snap(sandbox, "before")  # producao como esta: nada roda antes do snapshot

    print(f"=== {sigla} reprocess com o codigo atual ===")
    reprocess(sandbox, [], store=FixedStore(profile))
    snap(sandbox, "after")

    rep = analyze(sigla, sandbox)
    rep["taxonomy_before"] = tax_before
    rep["taxonomy_after"] = _taxonomy_counts(sandbox)
    rep["ruler_before"] = ruler_before
    rep["ruler_after"] = _material_ruler(sandbox, sigla)
    out = base / f"taxfix_{sigla}.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    tb, ta = sum(tax_before.values()), sum(rep["taxonomy_after"].values())
    rb = rep["ruler_before"] or {}
    ra = rep["ruler_after"] or {}
    c = rep["counts"]
    print(f"\n=== RESUMO {sigla} ===")
    print(f"topicos na taxonomia: {tb} -> {ta}")
    print(f"gold de unidade: {rep['eval_before']['ok']}/{rep['eval_before']['total']}"
          f" -> {rep['eval_after']['ok']}/{rep['eval_after']['total']}"
          f" | regressao: {rep['eval_regression']}")
    print(f"regua por material: {rb.get('correct', '?')}/{rb.get('total', '?')}"
          f" -> {ra.get('correct', '?')}/{ra.get('total', '?')}"
          f" | confiante-e-errado: {rb.get('confident_wrong', '?')} -> {ra.get('confident_wrong', '?')}")
    print(f"pinos violados/perdidos: {len(rep['pins_violados'])}/{rep['pins_total']}")
    print(f"delta bloco {c['block_delta']}/{c['entries']} | unit {c['unit_delta']}"
          f" | subunit {c['subunit_delta']}")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
