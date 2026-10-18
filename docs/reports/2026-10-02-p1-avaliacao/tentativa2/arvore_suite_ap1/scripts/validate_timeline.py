"""Validação de `.timeline_index.json` contra o schema v4 + gates de saúde.

Uso:
    python scripts/validate_timeline.py [paths_or_globs...]

Sem argumentos: valida os fixtures versionados em tests/fixtures/timeline/.
Com argumentos: valida cada caminho/glob (ex.: cursos reais).

Saída != 0 se qualquer arquivo:
  - não bate no schema v4 (drift estrutural);
  - tem `unknown` > UNKNOWN_MAX dos blocos;
  - tem bloco `class` com needs_unit/needs_files acima de CLASS_DEFECT_MAX.

Compartilhado entre o teste (tests/test_timeline_schema.py) e o CI.
"""

from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Tuple

# Permite rodar como script solto (python scripts/validate_timeline.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.timeline.classifier import classify_block  # noqa: E402
from src.builder.timeline.conflicts import detect_timeline_conflicts  # noqa: E402
from src.builder.timeline.index import _backfill_timeline_index  # noqa: E402
from src.builder.timeline.status import derive_block_status  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "timeline_index.v4.json"
FIXTURES_GLOB = str(REPO_ROOT / "tests" / "fixtures" / "timeline" / "*.json")

# Gates (espelham a GitHub Action validate-timeline.yml)
UNKNOWN_MAX = 0.05         # > 5% blocos unknown reprova
CLASS_DEFECT_MAX = 0.10    # > 10% blocos class com needs_unit/needs_files reprova


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(index: dict) -> List[str]:
    """Erros de schema (lista vazia = válido). Aplica backfill v3->v4 antes."""
    from jsonschema import Draft7Validator

    normalized = _backfill_timeline_index(json.loads(json.dumps(index)))
    validator = Draft7Validator(load_schema())
    out = []
    for err in sorted(validator.iter_errors(normalized), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out


def health_report(blocks: Iterable[dict]) -> dict:
    """Métricas de saúde derivadas (não persistidas)."""
    blocks = list(blocks or [])
    total = len(blocks)
    kinds = Counter(classify_block(b).value for b in blocks)
    unknown = kinds.get("unknown", 0)

    class_blocks = 0
    class_defects = 0
    for b in blocks:
        kind = classify_block(b).value
        if kind != "class":
            continue
        class_blocks += 1
        status = derive_block_status(dict(b, kind=kind))
        if status in ("needs_unit", "needs_files"):
            class_defects += 1

    return {
        "total": total,
        "kinds": dict(kinds),
        "unknown": unknown,
        "unknown_rate": (unknown / total) if total else 0.0,
        "class_blocks": class_blocks,
        "class_defects": class_defects,
        "class_defect_rate": (class_defects / class_blocks) if class_blocks else 0.0,
        "override_conflicts": detect_timeline_conflicts(blocks),
    }


def gate_failures(report: dict) -> List[str]:
    """Falhas de gate de saúde (lista vazia = passou)."""
    fails = []
    if report["unknown_rate"] > UNKNOWN_MAX:
        fails.append(
            f"unknown {report['unknown']}/{report['total']} "
            f"({report['unknown_rate']:.0%}) > {UNKNOWN_MAX:.0%}"
        )
    if report["class_defect_rate"] > CLASS_DEFECT_MAX:
        fails.append(
            f"class needs_unit/files {report['class_defects']}/{report['class_blocks']} "
            f"({report['class_defect_rate']:.0%}) > {CLASS_DEFECT_MAX:.0%}"
        )
    return fails


def validate_file(path: Path) -> Tuple[bool, List[str]]:
    """Valida um arquivo. Retorna (ok, mensagens)."""
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return False, [f"leitura/parse falhou: {exc}"]

    msgs: List[str] = []
    errs = schema_errors(index)
    if errs:
        msgs.extend(f"schema: {e}" for e in errs)

    report = health_report(index.get("blocks", []))
    msgs.extend(f"gate: {g}" for g in gate_failures(report))
    msgs.append(
        f"saúde: {report['total']} blocos · unknown {report['unknown_rate']:.0%} · "
        f"class_defect {report['class_defect_rate']:.0%} · kinds={report['kinds']}"
    )
    conflicts = report.get("override_conflicts") or []
    if conflicts:
        msgs.append(
            f"warning: {len(conflicts)} override(s) conflitam com auto-atribuicao: "
            + ", ".join(f"{c['block_id']}/{c['field']}" for c in conflicts)
        )
    ok = not errs and not gate_failures(report)
    return ok, msgs


def _expand(patterns: List[str]) -> List[Path]:
    paths: List[Path] = []
    for pat in patterns:
        matched = [Path(p) for p in glob.glob(pat)]
        if not matched and Path(pat).exists():
            matched = [Path(pat)]
        paths.extend(matched)
    return paths


def main(argv: List[str]) -> int:
    patterns = argv or [FIXTURES_GLOB]
    paths = _expand(patterns)
    if not paths:
        print(f"nenhum arquivo encontrado para: {patterns}")
        return 1

    overall_ok = True
    for path in paths:
        ok, msgs = validate_file(path)
        marker = "OK " if ok else "FAIL"
        print(f"[{marker}] {path}")
        for m in msgs:
            print(f"        {m}")
        overall_ok = overall_ok and ok
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
