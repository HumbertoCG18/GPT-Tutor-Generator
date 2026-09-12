"""Injetor do EXEC_SUMMARY e idempotente: a 2a chamada nao muda o arquivo (antes: +1 linha em branco por build)."""
from pathlib import Path

from src.builder.artifacts.navigation import _inject_executive_summary


def _doc(tmp_path: Path) -> Path:
    p = tmp_path / "doc.md"
    p.write_text('---\ntitle: "x"\n---\n\n# Titulo\n\n## Secao A\n\ntexto\n\n## Secao B\n\ntexto\n', encoding="utf-8")
    return p


def test_inject_exec_summary_e_idempotente(tmp_path: Path):
    p = _doc(tmp_path)
    assert _inject_executive_summary(p) is True
    depois_1 = p.read_text(encoding="utf-8")
    assert "<!-- EXEC_SUMMARY_START -->" in depois_1
    assert _inject_executive_summary(p) is False
    assert p.read_text(encoding="utf-8") == depois_1


def test_inject_exec_summary_nao_acumula_linhas_em_branco(tmp_path: Path):
    p = _doc(tmp_path)
    for _ in range(5):
        _inject_executive_summary(p)
    texto = p.read_text(encoding="utf-8")
    assert "\n\n\n" not in texto
    assert texto.count("EXEC_SUMMARY_START") == 1
