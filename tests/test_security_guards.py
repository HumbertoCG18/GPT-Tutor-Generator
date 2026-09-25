"""Proteções contra credencial versionada (#80-#82; incidente de 24/09).

Tudo roda em repositórios git temporários, com configuração git isolada e valores sintéticos gerados em runtime; nada é
commitado no repositório do projeto. Sem gitleaks, os testes que dependem dele pulam, exceto com REQUIRE_GITLEAKS=1 (CI).
"""
import hashlib
import importlib.util
import io
import json
import os
import secrets
import shutil
import string
import subprocess
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCAN = RAIZ / "scripts" / "security" / "gitleaks_scan.py"
HIGIENE = RAIZ / "scripts" / "security" / "check_repo_hygiene.py"
HOOK = RAIZ / "scripts" / "hooks" / "pre-commit.sh"
REGRA = "oauth-refresh-access-token"

precisa_gitleaks = pytest.mark.skipif(
    not shutil.which("gitleaks") and os.environ.get("REQUIRE_GITLEAKS") != "1", reason="gitleaks ausente")


def _opaco() -> str:
    """Valor no feitio do refresh token do Entra: opaco, sem prefixo, com '*' que as regras padrão não aceitam."""
    return "*".join(secrets.token_urlsafe(6) for _ in range(12))


def _ghp() -> str:
    return "ghp_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))


@pytest.fixture
def repo(tmp_path):
    raiz = tmp_path / "repo"
    raiz.mkdir()
    cfg = tmp_path / "gitconfig-vazio"
    cfg.write_text("", encoding="utf-8")
    env = dict(os.environ, GIT_CONFIG_GLOBAL=str(cfg), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="teste", GIT_AUTHOR_EMAIL="teste@exemplo.invalid",
               GIT_COMMITTER_NAME="teste", GIT_COMMITTER_EMAIL="teste@exemplo.invalid")
    env.pop("GITLEAKS_CONFIG", None)

    def git(*args, check=True):
        r = subprocess.run(["git", *args], cwd=raiz, env=env, capture_output=True, text=True, encoding="utf-8")
        if check and r.returncode != 0:
            raise AssertionError(f"git {args[0]} falhou: {r.stderr}")
        return r

    def escrever(rel, texto):
        p = raiz / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")

    def commit(msg, *arquivos):
        git("add", *arquivos)
        git("commit", "-q", "-m", msg)
        return git("rev-parse", "HEAD").stdout.strip()

    def rodar(script, *args, env_extra=None):
        return subprocess.run([sys.executable, str(script), *args], cwd=raiz, env={**env, **(env_extra or {})},
                              capture_output=True, text=True, encoding="utf-8")

    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "base")
    base = git("rev-parse", "HEAD").stdout.strip()
    return SimpleNamespace(path=raiz, env=env, git=git, escrever=escrever, commit=commit, rodar=rodar, base=base)


def _saida(r) -> str:
    return r.stdout + r.stderr


def _env_sem_gitleaks(env):
    dirs = [d for d in env["PATH"].split(os.pathsep)
            if d and not any((Path(d) / n).exists() for n in ("gitleaks", "gitleaks.exe"))]
    novo = dict(env, PATH=os.pathsep.join(dirs))
    novo.pop("GITLEAKS_BIN", None)
    return novo


# 4. hook bloqueia sem o scanner (com o wrapper e no caminho de branch antiga, sem scripts/security)
@pytest.mark.skipif(not shutil.which("sh"), reason="sh ausente")
@pytest.mark.parametrize("com_wrapper", [True, False])
def test_hook_bloqueia_commit_sem_gitleaks(repo, com_wrapper):
    hooks = repo.path / ".git" / "hooks"
    shutil.copyfile(HOOK, hooks / "pre-commit")
    (hooks / "pre-commit").chmod(0o755)
    if com_wrapper:
        (repo.path / "scripts" / "security").mkdir(parents=True)
        for f in (SCAN, HIGIENE):
            shutil.copyfile(f, repo.path / "scripts" / "security" / f.name)
        shutil.copyfile(RAIZ / ".gitleaks.toml", repo.path / ".gitleaks.toml")
    repo.escrever("nota.txt", "sem segredo\n")
    repo.git("add", "-A")
    env = _env_sem_gitleaks(repo.env)
    r = subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=repo.path, env=env,
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode != 0
    assert "gitleaks ausente" in r.stderr
    assert repo.git("rev-parse", "HEAD").stdout.strip() == repo.base

    if shutil.which("gitleaks"):  # controle: com o scanner e stage limpo, o mesmo hook deixa passar
        ok = subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=repo.path, env=repo.env,
                            capture_output=True, text=True, encoding="utf-8")
        assert ok.returncode == 0, ok.stderr


# 5. credencial sintética no stage é detectada; o que não está no stage não conta, e o stage vale mesmo após editar
@precisa_gitleaks
@pytest.mark.parametrize("modelo", [
    '{"refresh_token":"%s"}',
    '{\n  "token_type": "Bearer",\n  "refresh_token"  :\n      "%s",\n  "expires_in": 3600\n}\n',
    "tok = {'refresh_token': '%s'}\n",
    '{"refreshToken": "%s"}',
    'refresh-token: "%s"\n',
    'ACCESS_TOKEN="%s"\n',
])
def test_credencial_no_stage_detectada(repo, modelo):
    valor = _opaco()
    repo.escrever("cache/sessao.json", modelo % valor)
    limpo = repo.rodar(SCAN, "staged")
    assert limpo.returncode == 0, _saida(limpo)
    repo.git("add", "cache/sessao.json")
    repo.escrever("cache/sessao.json", "{}\n")
    r = repo.rodar(SCAN, "staged")
    assert r.returncode == 1, _saida(r)
    assert REGRA in r.stderr and "cache/sessao.json" in r.stderr
    assert valor not in _saida(r)


@precisa_gitleaks
@pytest.mark.parametrize("texto", [
    '{"refresh_token": "curto"}',
    '{"refresh_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}',
    'data = {"refresh_token": rt, "scope": SCOPE}',
    "p.write_text('{\"refresh_token\": \"%s\"}' % antigo)",
])
def test_regra_ignora_marcador_e_variavel(repo, texto):
    repo.escrever("modulo.py", texto + "\n")
    repo.git("add", "modulo.py")
    r = repo.rodar(SCAN, "staged")
    assert r.returncode == 0, _saida(r)


# 6. regra personalizada soma às padrão; sem ela, as padrão não pegam o formato do incidente
@precisa_gitleaks
def test_regra_personalizada_com_padroes(repo, tmp_path):
    opaco, ghp = _opaco(), _ghp()
    repo.escrever("cfg.json", '{"refresh_token": "%s"}\n' % opaco)
    repo.escrever("outro.txt", "GH=%s\n" % ghp)
    repo.git("add", "-A")
    r = repo.rodar(SCAN, "staged", "--report", str(tmp_path / "rel.json"))
    assert r.returncode == 1, _saida(r)
    regras = {a["RuleID"] for a in json.loads((tmp_path / "rel.json").read_text(encoding="utf-8"))}
    assert {REGRA, "github-pat"} <= regras

    so_padrao = tmp_path / "padrao.toml"
    so_padrao.write_text("[extend]\nuseDefault = true\n", encoding="utf-8")
    repo.git("rm", "-q", "--cached", "outro.txt")
    r2 = repo.rodar(SCAN, "staged", "--config", str(so_padrao))
    assert r2.returncode == 0, _saida(r2)


# 7. versionado que o .gitignore manda ignorar falha a verificação
def test_versionado_ignorado_falha(repo):
    repo.escrever("saida.log", "x\n")
    repo.commit("log", "saida.log")
    repo.escrever(".gitignore", "*.log\n")
    repo.commit("ignore", ".gitignore")
    r = repo.rodar(HIGIENE, "tree")
    assert r.returncode == 1 and "saida.log" in r.stderr
    repo.git("rm", "-q", "--cached", "saida.log")
    repo.git("commit", "-q", "-m", "higiene")
    assert repo.rodar(HIGIENE, "tree").returncode == 0


# 8. caminho de credencial é barrado sem regra no .gitignore; JSONs e exemplos continuam permitidos
def test_caminho_proibido_sem_gitignore(repo):
    repo.escrever("moddle/.m365_token.json", "{}\n")
    repo.escrever("sub/.env", "X=1\n")
    repo.escrever(".env.example", "X=\n")
    repo.escrever("dados/config.json", "{}\n")
    repo.git("add", "-A")
    st = repo.rodar(HIGIENE, "staged")
    assert st.returncode == 1
    assert "moddle/.m365_token.json" in st.stderr and "sub/.env" in st.stderr
    assert ".env.example" not in st.stderr and "config.json" not in st.stderr
    repo.git("commit", "-q", "-m", "x")
    assert repo.rodar(HIGIENE, "tree").returncode == 1


# 9. segredo adicionado e removido em seguida é detectado no intervalo (commit intermediário)
@precisa_gitleaks
def test_segredo_adicionado_e_removido_no_intervalo(repo):
    repo.escrever("cache.json", '{"refresh_token": "%s"}\n' % _opaco())
    repo.escrever("moddle/.m365_token.json", "{}\n")
    c1 = repo.commit("adiciona", "-A")
    repo.git("rm", "-q", "cache.json", "moddle/.m365_token.json")
    repo.git("commit", "-q", "-m", "remove")
    intervalo = f"{repo.base}..HEAD"

    r = repo.rodar(SCAN, "range", intervalo)
    assert r.returncode == 1, _saida(r)
    assert f"commit={c1[:12]}" in r.stderr and REGRA in r.stderr
    h = repo.rodar(HIGIENE, "range", intervalo)
    assert h.returncode == 1 and c1[:12] in h.stderr
    assert repo.rodar(HIGIENE, "tree").returncode == 0  # a ponta limpa sozinha não basta


@precisa_gitleaks
def test_segredo_so_na_resolucao_do_merge(repo):
    repo.git("checkout", "-q", "-b", "lado")
    repo.escrever("a.txt", "a\n")
    repo.commit("lado", "a.txt")
    repo.git("checkout", "-q", "-")
    repo.escrever("b.txt", "b\n")
    repo.commit("principal", "b.txt")
    repo.git("merge", "-q", "--no-commit", "lado")
    repo.escrever("cfg.json", '{"refresh_token": "%s"}\n' % _opaco())
    merge = repo.commit("merge", "cfg.json")
    r = repo.rodar(SCAN, "range", f"{repo.base}..HEAD")
    assert r.returncode == 1, _saida(r)
    assert f"commit={merge[:12]}" in r.stderr


def test_intervalo_le_nomes_com_escape_e_maiusculas(repo):
    blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=repo.path, env=repo.env, input="X=1\n",
                          capture_output=True, text=True).stdout.strip()
    for nome in ("pasta\tcom tab/.env", "sub/.ENV", "x/Chave.DPAPI"):  # tab: só pelo índice, sem arquivo no disco
        repo.git("-c", "core.protectNTFS=false", "update-index", "--add", "--cacheinfo", f"100644,{blob},{nome}")
    repo.git("commit", "-q", "-m", "adiciona")
    c1 = repo.git("rev-parse", "HEAD").stdout.strip()
    for nome in ("pasta\tcom tab/.env", "sub/.ENV", "x/Chave.DPAPI"):
        repo.git("-c", "core.protectNTFS=false", "update-index", "--force-remove", nome)
    repo.git("commit", "-q", "-m", "remove")
    h = repo.rodar(HIGIENE, "range", f"{repo.base}..HEAD")
    assert h.returncode == 1
    for nome in ("pasta\tcom tab/.env", "sub/.ENV", "x/Chave.DPAPI"):
        assert f"{c1[:12]}: {nome}" in h.stderr


# 10. saídas e relatório não expõem os valores
@precisa_gitleaks
def test_saidas_e_relatorio_sanitizados(repo, tmp_path):
    valores = [_opaco(), _opaco(), _ghp()]
    repo.escrever("a.json", '{"refresh_token": "%s", "access_token": "%s"}\n' % tuple(valores[:2]))
    repo.escrever("b.txt", "token %s\n" % valores[2])
    repo.commit("segredos", "-A")
    rel = tmp_path / "rel.json"
    r = repo.rodar(SCAN, "history", "--report", str(rel))
    assert r.returncode == 1, _saida(r)
    achados = json.loads(rel.read_text(encoding="utf-8"))
    assert achados and all(set(a) == {"RuleID", "File", "StartLine", "Commit"} for a in achados)
    texto = _saida(r) + rel.read_text(encoding="utf-8")
    for v in valores:
        assert v not in texto
        for pedaco in (v[:12], v[-12:]):
            assert pedaco not in texto


@pytest.mark.skipif(not shutil.which("sh"), reason="sh ausente")
def test_setup_nuvem_instala_hook_so_na_nuvem(repo, tmp_path):
    (repo.path / "scripts" / "hooks").mkdir(parents=True)
    shutil.copyfile(HOOK, repo.path / "scripts" / "hooks" / "pre-commit.sh")
    home = tmp_path / "home"
    falso = home / ".local" / "bin" / "gitleaks"  # já "instalado": o teste não baixa nada
    falso.parent.mkdir(parents=True)
    falso.write_text("#!/bin/sh\necho 8.30.1\n", encoding="utf-8")
    falso.chmod(0o755)
    script = RAIZ / "scripts" / "security" / "setup_nuvem.sh"
    env = dict(repo.env, HOME=str(home), CLAUDE_PROJECT_DIR=str(repo.path), CLAUDE_ENV_FILE=str(tmp_path / "envfile"))
    env.pop("CLAUDE_CODE_REMOTE", None)
    hook = repo.path / ".git" / "hooks" / "pre-commit"
    shutil.rmtree(hook.parent)  # clone sem templates: o diretório de hooks não existe

    local =subprocess.run(["sh", str(script)], cwd=repo.path, env=env, capture_output=True, text=True)
    assert local.returncode == 0 and not hook.exists() and not (tmp_path / "envfile").exists()

    nuvem = subprocess.run(["sh", str(script)], cwd=repo.path, env=dict(env, CLAUDE_CODE_REMOTE="true"),
                           capture_output=True, text=True)
    assert nuvem.returncode == 0 and "gitleaks: 8.30.1" in nuvem.stdout
    assert hook.read_bytes() == HOOK.read_bytes() and os.access(hook, os.X_OK)
    assert ".local/bin" in (tmp_path / "envfile").read_text(encoding="utf-8").replace("\\", "/")


def _modulo_scan():
    spec = importlib.util.spec_from_file_location("gitleaks_scan_teste", SCAN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_instalacao_recusa_checksum_divergente(tmp_path, monkeypatch):
    mod = _modulo_scan()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        info = tarfile.TarInfo("gitleaks")
        info.size = 4
        t.addfile(info, io.BytesIO(b"bin\n"))
    dados = buf.getvalue()
    with pytest.raises(mod.ScanError, match="SHA-256 não confere"):
        mod.extrair_binario(dados, "linux_x64.tar.gz", tmp_path / "dest")
    assert not (tmp_path / "dest").exists()

    monkeypatch.setitem(mod.CHECKSUMS, "linux_x64.tar.gz", hashlib.sha256(dados).hexdigest())
    saida = mod.extrair_binario(dados, "linux_x64.tar.gz", tmp_path / "dest")
    assert saida.read_bytes() == b"bin\n"


def test_instalacao_mantem_versao_fixada_e_troca_divergente(tmp_path, monkeypatch):
    mod = _modulo_scan()
    chave = mod._alvo_plataforma()
    (tmp_path / ("gitleaks.exe" if chave.endswith(".zip") else "gitleaks")).write_bytes(b"x")
    baixados = []

    class _Resp(io.BytesIO):
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(mod.urllib.request, "urlopen", lambda url, timeout=0: baixados.append(url) or _Resp(b"z"))
    monkeypatch.setattr(mod, "_versao", lambda b: mod.GITLEAKS_VERSION)
    mod.instalar(tmp_path)
    assert baixados == []
    monkeypatch.setattr(mod, "_versao", lambda b: "8.0.0")
    with pytest.raises(mod.ScanError, match="SHA-256"):
        mod.instalar(tmp_path)
    assert len(baixados) == 1


def test_versao_divergente_ou_ausente_e_erro(monkeypatch):
    mod = _modulo_scan()
    monkeypatch.delenv("GITLEAKS_BIN", raising=False)
    monkeypatch.setattr(mod.shutil, "which", lambda n: None)
    with pytest.raises(mod.ScanError, match="ausente"):
        mod.localizar()
    monkeypatch.setattr(mod.shutil, "which", lambda n: sys.executable)
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout="8.29.0\n"))
    with pytest.raises(mod.ScanError, match="fixada"):
        mod.localizar()
    assert mod.main(["range", "sem-intervalo"]) == 2
