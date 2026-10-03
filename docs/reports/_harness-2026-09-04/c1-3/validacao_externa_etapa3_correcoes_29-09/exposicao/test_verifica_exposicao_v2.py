"""Contraexemplos da revisão (E3-EXP-01..09) para o verificador de exposição v2, escritos ANTES das correções.
Repositório git sintético; nenhum dado real; nenhuma rede."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verifica_exposicao as V  # noqa: E402

EXCLUI = re.compile(r"\.(pdf|png)$")
LINHA_DUPLA = "Engenharia de Software II e, bem depois, " + "x" * 200 + " Engenharia de Software I (outra disciplina)\n"


def git(raiz, *a):
    return subprocess.run(["git", *a], cwd=raiz, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    arquivos = {"docs/ação.md": "Menção a Curso Gamma.\n", "docs/uma_linha.json": LINHA_DUPLA,
                "tests/test_curso.py": "NOME = 'Curso Gamma'\n", "docs/resumo_curso.md": "Curso Gamma foi citado de passagem.\n",
                "docs/reports/placar_x.json": '{"curso": "Curso Gamma"}\n', "src/x.py": "pass\n"}
    for rel, txt in arquivos.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(txt, encoding="utf-8")
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", ".")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    return tmp_path, git(tmp_path, "rev-parse", "HEAD")


def gamma(raiz, base, **k):
    return V.verifica({"id": "x", "nome": "Curso Gamma", "padrao": "Curso Gamma"}, raiz, base, ["docs", "tests", "src"], EXCLUI,
                      k.get("pastas", []))


def test_EXP08_cor_do_git_nao_vira_zero(repo):
    raiz, base = repo
    git(raiz, "config", "color.grep", "always")
    git(raiz, "config", "color.ui", "always")
    r = gamma(raiz, base)
    assert r["status_da_busca"] == "ok" and r["sinais"]["ocorrencias"] == 4


def test_EXP06_saida_nao_interpretada_e_indeterminado(repo, monkeypatch):
    raiz, base = repo
    original = V.git

    def git_falso(repo_, *args):
        if "grep" in args:
            return 0, "linha fora do formato esperado\n"
        return original(repo_, *args)

    monkeypatch.setattr(V, "git", git_falso)
    assert gamma(raiz, base)["status_da_busca"] == "INDETERMINADO"


def test_EXP09_todos_os_matches_da_linha(repo):
    raiz, base = repo
    r = V.verifica({"id": "x", "nome": "ES I", "padrao": "Engenharia de Software I"}, raiz, base, ["docs"], EXCLUI, [])
    ocs = [o for o in r["ocorrencias"] if o["arquivo"] == "docs/uma_linha.json"]
    assert [o["vizinhanca"]["depois"][:1] for o in ocs] == ["I", " "]
    assert all(o["intervalo"][1] - o["intervalo"][0] == len("Engenharia de Software I") for o in ocs)


def test_EXP01_caminho_acentuado_sem_aspas(repo):
    raiz, base = repo
    arquivos = {o["arquivo"] for o in gamma(raiz, base)["ocorrencias"]}
    assert "docs/ação.md" in arquivos


def test_EXP05_categorias_e_motivo_de_omissao(repo):
    raiz, base = repo
    por = {o["arquivo"]: o for o in gamma(raiz, base)["ocorrencias"]}
    assert por["tests/test_curso.py"]["categoria"] == "teste_ou_fixture"
    assert por["docs/resumo_curso.md"]["categoria"] == "relatorio_ou_handoff" and "de passagem" in por["docs/resumo_curso.md"]["trecho"]
    assert por["docs/reports/placar_x.json"]["categoria"] == "resultado_do_motor"
    assert por["docs/reports/placar_x.json"]["motivo_omissao"] == "arquivo de resultado do motor"


def test_EXP03_fonte_de_pastas_ausente_e_indeterminado(repo, tmp_path, monkeypatch):
    raiz, base = repo
    entrada = {"base": base, "raizes": ["docs"], "exclui_caminho": r"\.pdf$", "catalogo": "x", "candidatos_locais": "x",
               "pastas_anteriores": str(tmp_path / "nao_existe"), "fora_ids": [], "fora_siglas": []}
    (tmp_path / "entrada.json").write_text(json.dumps(entrada), encoding="utf-8")
    monkeypatch.setattr(V, "REPO", raiz)
    monkeypatch.setattr(V, "candidatos", lambda e: [{"id": "x", "nome": "Curso Gamma", "padrao": "Curso Gamma", "origem": "t"}])
    monkeypatch.setattr(sys, "argv", ["v", str(tmp_path / "entrada.json"), str(tmp_path / "saida.json")])
    V.main()
    saida = json.loads((tmp_path / "saida.json").read_text(encoding="utf-8"))
    assert [c["status_da_busca"] for c in saida["candidatos"]] == ["INDETERMINADO"]
