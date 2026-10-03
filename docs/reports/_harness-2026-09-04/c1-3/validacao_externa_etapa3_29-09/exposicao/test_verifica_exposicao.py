"""Verificador de exposição num repositório git sintético (sem rede; nenhum dado real)."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verifica_exposicao as V  # noqa: E402

EXCLUI = re.compile(r"\.(pdf|png)$")


@pytest.fixture
def repo(tmp_path):
    arquivos = {"src/cursos.py": "CURSO = 'Curso Sintetico Avancado'  # usado no build\n",
                "docs/reports/relatorio.md": "Sem relação. Citamos Curso Sintetico Avancado de passagem.\n",
                "docs/reports/placar_x.json": '{"curso": "Curso Sintetico Avancado", "computed_unit_slug": "u1"}\n',
                "docs/reports/notas.md": "linha com Curso Sintetico Avancado e computed_block_id=bloco-02\n",
                "docs/outro.md": "Curso Sintetico Avancado II é outro curso\n",
                "tests/test_x.py": "pass\n"}
    for rel, txt in arquivos.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(txt, encoding="utf-8")
    for cmd in (["init", "-q"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "build Curso Sintetico Avancado"]):
        subprocess.run(["git", *cmd], cwd=tmp_path, check=True, capture_output=True)
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True).stdout.strip()
    return tmp_path, base


def test_categorias_termo_trecho_e_omissao(repo):
    raiz, base = repo
    r = V.verifica({"id": "x", "nome": "Curso Sintetico Avancado", "padrao": "Curso Sintetico Avancado"}, raiz, base,
                   ["src", "docs", "tests"], EXCLUI, [])
    assert r["status_da_busca"] == "ok" and "nivel" not in r
    por = {o["arquivo"]: o for o in r["ocorrencias"]}
    assert por["src/cursos.py"]["categoria"] == "codigo"
    assert por["docs/reports/relatorio.md"]["categoria"] == "relatorio_ou_handoff"
    assert "de passagem" in por["docs/reports/relatorio.md"]["trecho"]
    assert por["docs/reports/placar_x.json"]["categoria"] == "resultado_do_motor"
    assert "omitido" in por["docs/reports/placar_x.json"]["trecho"] and "omitido" in por["docs/reports/notas.md"]["trecho"]
    assert por["docs/outro.md"]["termo"] == "Curso Sintetico Avancado" and "Avancado II" in por["docs/outro.md"]["trecho"]
    assert por["docs/outro.md"]["vizinhanca"] == {"antes": "", "depois": " II"}
    assert r["sinais"]["arquivos_codigo_teste_dados_ou_resultado"] == 2 and r["sinais"]["commits"] == 1


@pytest.mark.parametrize("base, raizes, padrao", [
    ("0" * 40, ["src"], "x"), (None, ["naoexiste"], "x"), (None, ["src"], "(("),
])
def test_falha_de_busca_e_indeterminado(repo, base, raizes, padrao):
    raiz, b = repo
    r = V.verifica({"id": "x", "nome": "x", "padrao": padrao}, raiz, base or b, raizes, EXCLUI, [])
    assert r["status_da_busca"] == "INDETERMINADO" and r["falhas"]


def test_subpasta_nao_e_raiz(repo):
    raiz, base = repo
    r = V.verifica({"id": "x", "nome": "x", "padrao": "Curso"}, raiz / "docs", base, ["reports"], EXCLUI, [])
    assert r["status_da_busca"] == "INDETERMINADO"
