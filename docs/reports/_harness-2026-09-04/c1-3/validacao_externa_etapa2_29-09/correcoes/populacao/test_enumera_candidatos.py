"""Testes do enumerador v2 com repositório git e fontes SINTÉTICAS (nenhum curso real é lido)."""
import io
import json
import subprocess
import sys
import tokenize
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import enumera_candidatos as E  # noqa: E402


def git(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    for raiz in E.EVIDENCIA_RAIZES:
        (r / raiz).mkdir(parents=True)
        (r / raiz / "LEIA.md").write_text("vazio\n", encoding="utf-8")
    (r / "docs" / "handoff.md").write_text("Dissecação do Curso Exposto em 28/08.\n", encoding="utf-8")
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@example.invalid")
    git(r, "config", "user.name", "t")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    return r, git(r, "rev-parse", "HEAD")


def cand(sigla="NOVO", padrao=r"Curso Novo", **extra):
    return {"sigla": sigla, "nome": sigla, "fonte": "~/inexistente", "padrao": padrao, **extra}


def test_exposto_vira_n1_e_nao_exposto_n0(repo):
    r, base = repo
    assert E.exposicao(cand(padrao=r"Curso Exposto"), repo=r, base=base, github=r.parent)["nivel"] == "N1"
    assert E.exposicao(cand(), repo=r, base=base, github=r.parent)["nivel"] == "N0"


@pytest.mark.parametrize("caso", ["commit_inexistente", "nao_e_repositorio", "padrao_invalido", "git_ausente",
                                  "raiz_ausente", "subpasta_do_repositorio"])
def test_falha_da_busca_vira_indeterminado_nunca_n0(repo, tmp_path, monkeypatch, caso):
    r, base = repo
    c, alvo, b = cand(), r, base
    if caso == "commit_inexistente":
        b = "0" * 40
    elif caso == "nao_e_repositorio":
        alvo = tmp_path / "sem_git"
        alvo.mkdir()
    elif caso == "padrao_invalido":
        c = cand(padrao="(")
    elif caso == "git_ausente":
        def sem_git(*a, **k):
            raise OSError("git não encontrado")
        monkeypatch.setattr(E.subprocess, "run", sem_git)
    elif caso == "raiz_ausente":
        git(r, "rm", "-q", "-r", ".mex")
        git(r, "commit", "-q", "-m", "sem .mex")
        b = git(r, "rev-parse", "HEAD")
    elif caso == "subpasta_do_repositorio":   # o defeito real da 1ª versão da v2: pathspec relativo "não acha nada"
        alvo = r / "docs"
    ex = E.exposicao(c, repo=alvo, base=b, github=tmp_path)
    assert ex["nivel"] == "INDETERMINADO" and ex["falhas_da_busca"], ex


def test_indeterminado_nunca_entra_em_populacao(monkeypatch, tmp_path):
    fonte = tmp_path / "fonte"
    for i in range(12):
        (fonte / f"aula{i}.pdf").parent.mkdir(parents=True, exist_ok=True)
        (fonte / f"aula{i}.pdf").write_bytes(f"%PDF {i}".encode())
    (fonte / "plano.pdf").write_bytes(b"%PDF plano")
    monkeypatch.setattr(E, "exposicao", lambda c: {"nivel": "INDETERMINADO", "falhas_da_busca": ["x"], "tutor_construido": False,
                                                   "mencoes_repo": 0, "exemplos": [], "commits": []})
    linha = E.classifica(cand(fonte=str(fonte)))
    assert linha["E2_plano"] and linha["E3_tamanho"] and linha["E4_fonte_local"]
    assert linha["populacao"] == "indeterminado"
    assert E.seleciona([linha], "geral") == ([], []) and E.seleciona([linha], "piloto") == ([], [])


@pytest.mark.parametrize("local, total, passa", [(1800, 2001, False), (1801, 2001, True), (9, 10, True), (899, 1000, False),
                                                 (0, 0, False), (21, 28, False)])
def test_e4_exato_sem_arredondamento(local, total, passa):
    assert E.e4({"com_fonte_local": local, "potencialmente_adjudicaveis": total}) is passa


def test_candidatos_sao_dados_validados(tmp_path):
    ok = {"esquema": "candidatos-1", "candidatos": [cand("A"), cand("B")]}
    p = tmp_path / "c.json"
    for ruim in ({**ok, "esquema": "x"},
                 {**ok, "candidatos": [cand("A"), cand("A")]},
                 {**ok, "candidatos": [cand("A", extra_desconhecido=1)]},
                 {**ok, "candidatos": [{"sigla": "A", "nome": "A", "fonte": "x"}]},
                 {**ok, "candidatos": [cand("a minúscula")]}):
        p.write_text(json.dumps(ruim), encoding="utf-8")
        with pytest.raises(E.DadosInvalidos):
            E.carrega_candidatos(p)
    p.write_text(json.dumps(ok), encoding="utf-8")
    assert [c["sigla"] for c in E.carrega_candidatos(p)["candidatos"]] == ["A", "B"]


def test_algoritmo_nao_contem_nenhum_candidato():
    dados = json.loads((AQUI / "candidatos_29-09.json").read_text(encoding="utf-8"))
    proibidos = {c["sigla"] for c in dados["candidatos"]} | {c["nome"] for c in dados["candidatos"]} | \
        {c.get("tutor") for c in dados["candidatos"] if c.get("tutor")}
    texto = (AQUI / "enumera_candidatos.py").read_text(encoding="utf-8")
    for t in tokenize.generate_tokens(io.StringIO(texto).readline):
        if t.type == tokenize.STRING and not t.string.startswith('"""'):
            valor = t.string.strip("\"'rf")
            assert valor not in proibidos, (t.start[0], t.string)
    assert "CANDIDATOS = [" not in texto and "DESENVOLVIMENTO = {" not in texto


def test_estrutura_devolve_fracao_inteira(tmp_path):
    f = tmp_path / "f"
    for nome in ("a.pdf", "b.pdf", "plano.pdf"):
        (f / nome).parent.mkdir(parents=True, exist_ok=True)
        (f / nome).write_bytes(nome.encode())
    (f / "raw/moodle").mkdir(parents=True)
    (f / "raw/moodle/contents.json").write_text(json.dumps([{"modules": [{"modname": "url"}, {"modname": "resource"}]}]),
                                               encoding="utf-8")
    est = E.estrutura(f)
    assert est["fracao_com_fonte_local"] == {"num": 2, "den": 3} and est["potencialmente_adjudicaveis"] == 3
    assert E.e4(est) is False
