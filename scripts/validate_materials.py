"""Gate de cobertura de material (espelha validate_timeline.py).

Uso: python scripts/validate_materials.py [manifest_globs...]
Sem args: valida fixtures (se houver). Saida != 0 se cobertura < MATERIAL_COVERAGE_MIN.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.artifacts.cronograma_health import material_coverage  # noqa: E402

_MATERIAL_COVERAGE_MIN: float = 0.70  # gate local; constante removida do thresholds (P4)


def coverage_gate_failures(entries: list) -> list:
    rep = material_coverage(entries)
    fails = []
    if rep["total"] and rep["coverage"] < _MATERIAL_COVERAGE_MIN:
        fails.append(
            f"cobertura {rep['coverage']:.0%} < {_MATERIAL_COVERAGE_MIN:.0%} "
            f"({rep['orphans']} orfaos de {rep['total']})"
        )
    return fails


def main(argv: list) -> int:
    patterns = argv or []
    paths = []
    for pat in patterns:
        paths.extend(glob.glob(pat))
    if not paths:
        print("nenhum manifest informado")
        return 0
    ok = True
    for p in paths:
        try:
            entries = json.loads(Path(p).read_text(encoding="utf-8")).get("entries", [])
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[FAIL] {p}: {exc}")
            ok = False
            continue
        fails = coverage_gate_failures(entries)
        rep = material_coverage(entries)
        marker = "OK " if not fails else "FAIL"
        print(f"[{marker}] {p}  cobertura={rep['coverage']:.0%} orfaos={rep['orphans']}/{rep['total']}")
        for f in fails:
            print(f"        {f}")
        ok = ok and not fails
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
