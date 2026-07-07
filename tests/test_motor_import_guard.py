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
    """Nomes trazidos para o namespace por import/from-import (last segment).

    Inclui o literal "*" quando houver `from modulo import *` — o wildcard
    não corresponde a nenhum símbolo condenado por nome, então precisa ser
    tratado como violação à parte (ver test_motor_never_usa_star_import).
    """
    names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)              # from x import <name> (ou "*")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
    return names


def _attribute_names(tree: ast.AST) -> set:
    """Nomes de atributo acessados via `obj.nome` (ex.: file_map.block_token_weights).

    Cobre o vetor `import modulo as m; m.block_token_weights(...)`: o símbolo
    condenado nunca é "importado" diretamente (não aparece em
    _imported_names), só é acessado como atributo do módulo/objeto após o
    alias. Flag simples pelo nome do atributo, ignorando de quem é: falso
    positivo é aceitável aqui, pois nenhum símbolo legítimo do pacote do
    motor compartilha esses nomes.
    """
    names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
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


def test_motor_never_usa_star_import():
    """`from modulo import *` contorna qualquer whitelist de nomes — o guard
    acima só enxerga o que foi explicitamente importado, então um wildcard
    escondendo um dos condenados passaria batido. Por isso o pacote do motor
    proíbe star-import por inteiro, independente do módulo de origem conter
    ou não símbolo condenado."""
    offenders: dict = {}
    for py in sorted(MOTOR_DIR.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        if "*" in _imported_names(tree):
            offenders[py.name] = ["* (star-import proibido)"]
    assert not offenders, (
        f"motor usa star-import, o que contorna a whitelist de nomes: {offenders}."
    )


def test_motor_never_acessa_condenados_via_atributo():
    """Cobre o vetor `import modulo as m` seguido de `m.block_token_weights(...)`:
    nada é "importado" com o nome condenado, só acessado depois via atributo.
    """
    offenders: dict = {}
    for py in sorted(MOTOR_DIR.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        bad = _attribute_names(tree) & CONDENADOS
        if bad:
            offenders[py.name] = sorted(bad)
    assert not offenders, (
        f"motor acessa condenados via atributo module-qualified: {offenders}. "
        "Whitelist: concept_resolver puro, card_block, thresholds, entry_signals, text/*."
    )
