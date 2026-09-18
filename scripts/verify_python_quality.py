"""Ratchet de qualidade Python sem exigir limpeza imediata do legado."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import platform
import subprocess
import sys


def compare_counts(current: Counter[str], allowed: Counter[str]) -> dict[str, int]:
    """Retorna somente fingerprints cuja contagem aumentou."""
    return {
        fingerprint: count - allowed[fingerprint]
        for fingerprint, count in sorted(current.items())
        if count > allowed[fingerprint]
    }


def _imported_modules(node: ast.AST, package: tuple[str, ...]) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []

    base = node.module or ""
    if node.level:
        keep = max(0, len(package) - node.level + 1)
        base = ".".join((*package[:keep], *filter(None, base.split("."))))

    modules = [base] if base else []
    if base == "src":
        modules.extend(f"src.{alias.name}" for alias in node.names)
    return modules


def find_architecture_violations(root: Path) -> Counter[str]:
    """Impede que o core crie novas dependências da interface transitória."""
    root = root.resolve()
    violations: Counter[str] = Counter()
    for path in sorted((root / "src").rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if relative == "src/__main__.py" or relative.startswith("src/ui/"):
            continue
        package = tuple(path.relative_to(root).with_suffix("").parts[:-1])
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=relative)
        for node in ast.walk(tree):
            for module in _imported_modules(node, package):
                if module == "src.ui" or module.startswith("src.ui."):
                    violations[f"{relative}|{module}"] += 1
    return violations


def read_coverage_percent(report: Path) -> float:
    data = json.loads(report.read_text(encoding="utf-8-sig"))
    return float(data["totals"]["percent_covered"])


def coverage_minimum(baselines: dict[str, float], system: str | None = None) -> float:
    system = system or platform.system()
    try:
        return float(baselines[system])
    except KeyError as error:
        raise ValueError(f"Sem baseline de cobertura para {system}") from error


def _ruff_findings(root: Path) -> Counter[str]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "src",
            "tests",
            "scripts",
            "--output-format",
            "json",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or "Ruff falhou sem diagnóstico")

    findings: Counter[str] = Counter()
    for item in json.loads(result.stdout or "[]"):
        path = Path(item["filename"])
        try:
            path = path.resolve().relative_to(root.resolve())
        except ValueError:
            pass
        fingerprint = f"{path.as_posix()}|{item['code']}"
        findings[fingerprint] += 1
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=Path(".github/python-quality-baseline.json"))
    parser.add_argument("--coverage", type=Path, default=Path("coverage.json"))
    args = parser.parse_args()

    root = Path.cwd()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8-sig"))
    failures: list[str] = []

    ruff = _ruff_findings(root)
    ruff_excess = compare_counts(ruff, Counter(baseline["ruff"]))
    failures.extend(f"Ruff +{count}: {key}" for key, count in ruff_excess.items())

    architecture = find_architecture_violations(root)
    architecture_excess = compare_counts(architecture, Counter(baseline["architecture"]))
    failures.extend(f"Arquitetura +{count}: {key}" for key, count in architecture_excess.items())

    coverage = read_coverage_percent(args.coverage)
    minimum = coverage_minimum(baseline["coverage_percent"])
    if coverage + 1e-9 < minimum:
        failures.append(f"Cobertura {coverage:.12f}% < baseline {minimum:.12f}%")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        f"Qualidade OK: Ruff={sum(ruff.values())}, "
        f"arquitetura={sum(architecture.values())}, cobertura={coverage:.4f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
