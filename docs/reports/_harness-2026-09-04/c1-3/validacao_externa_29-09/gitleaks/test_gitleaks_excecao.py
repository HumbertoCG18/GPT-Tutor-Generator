"""Teste reproduzível da exceção do gitleaks para sha256 de `resumo*.json` no harness (commit 71dff722).

Repositório git temporário com o `.gitleaks.toml` do projeto; gitleaks 8.30.1 (a versão fixada pelo CI) nos dois modos
usados: `--staged` (pre-commit) e histórico (job `secrets`). Os valores falsos são montados em tempo de execução, para
este arquivo não conter nada que o scanner reconheça. Sem rede.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[6]
CONFIG = REPO / ".gitleaks.toml"
GITLEAKS = shutil.which("gitleaks")
H64 = hashlib.sha256(b"valor de teste").hexdigest()                                         # 64 hex minusculos
ALNUM64 = (hashlib.sha256(b"a").hexdigest()[:32] + "QwErTyUiOpAsDfGhJkLzXcVbNmQwErTy")[:64]  # 64 alfanuméricos mistos
PALAVRA = "su" + "mo"
HARNESS = "docs/reports/_harness-2026-09-04/x"

CASOS = {
    # caminho: (conteúdo, deve ser detectado)
    f"{HARNESS}/manifesto.json": (json.dumps({"arquivos": {f"{HARNESS}/re{PALAVRA}_vl.json": H64}}, indent=1), False),
    f"docs/fora_do_harness/manifesto.json": (json.dumps({"arquivos": {f"x/re{PALAVRA}_vl.json": H64}}, indent=1), True),
    f"{HARNESS}/config.py": (f'{PALAVRA.upper()}_ACCESS_KEY = "{ALNUM64}"\n', True),
    f"{HARNESS}/outro.json": (json.dumps({f"{PALAVRA}_key.json": H64}, indent=1), True),
}


def git(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


def achados(repo, *modo):
    rel = repo / "r.json"
    subprocess.run([GITLEAKS, "git", *modo, "--config", str(repo / ".gitleaks.toml"), "--report-format", "json",
                    "--report-path", str(rel), "--redact", "--no-banner", "--exit-code", "0"], cwd=repo,
                   capture_output=True, text=True, encoding="utf-8")
    return {(f["RuleID"], f["File"].replace("\\", "/")) for f in json.loads(rel.read_text(encoding="utf-8"))}


@pytest.fixture
def repo(tmp_path):
    if not GITLEAKS:
        pytest.skip("gitleaks ausente")
    versao = subprocess.run([GITLEAKS, "version"], capture_output=True, text=True).stdout.strip()
    assert versao.lstrip("v") == "8.30.1", versao
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "teste@example.invalid")
    git(tmp_path, "config", "user.name", "teste")
    shutil.copyfile(CONFIG, tmp_path / ".gitleaks.toml")
    for rel, (conteudo, _) in CASOS.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(conteudo, encoding="utf-8", newline="\n")
    git(tmp_path, "add", "-A")
    return tmp_path


def esperado():
    return {rel for rel, (_, detecta) in CASOS.items() if detecta}


def test_modo_staged_do_pre_commit(repo):
    arquivos = {f for _, f in achados(repo, "--staged")}
    assert arquivos == esperado()


def test_modo_historico_do_ci(repo):
    git(repo, "commit", "-q", "-m", "casos")
    arquivos = {f for _, f in achados(repo, "--log-opts=--all")}
    assert arquivos == esperado()


def test_sem_a_excecao_o_falso_positivo_volta(repo):
    cfg = (repo / ".gitleaks.toml").read_text(encoding="utf-8")
    corte = cfg.index("# Manifestos do harness")
    (repo / ".gitleaks.toml").write_text(cfg[:corte], encoding="utf-8")
    arquivos = {f for _, f in achados(repo, "--staged")}
    assert f"{HARNESS}/manifesto.json" in arquivos   # a exceção é o que suprime, não outro fator
