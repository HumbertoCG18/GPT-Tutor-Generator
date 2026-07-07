# tests/test_motor_import_guard.py
import ast
from pathlib import Path

# Símbolos condenados no cutover da FASE 5 (spec §7, revisão 03/07).
CONDENADOS = frozenset({
    "block_token_weights",
    "score_entry_against_timeline_block",
    "select_probable_period_for_entry",
})

MOTOR_DIR = Path(__file__).resolve().parents[1] / "src" / "builder" / "routing" / "motor"


def _imported_names(tree: ast.AST) -> set:
    """Nomes trazidos para o namespace por import/from-import (last segment)."""
    names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)              # from x import <name>
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
    return names


def test_motor_package_exists():
    assert MOTOR_DIR.is_dir(), f"pacote do motor ausente: {MOTOR_DIR}"


def test_motor_never_imports_condemned_symbols():
    offenders: dict = {}
    for py in sorted(MOTOR_DIR.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        bad = _imported_names(tree) & CONDENADOS
        if bad:
            offenders[py.name] = sorted(bad)
    assert not offenders, (
        f"motor importa condenados do cutover: {offenders}. "
        "Whitelist: concept_resolver puro, card_block, thresholds, entry_signals, text/*."
    )
