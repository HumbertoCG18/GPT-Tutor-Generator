"""Gitleaks com versão fixada e saída sanitizada (#81; incidente de 24/09).

Uso:
  python scripts/security/gitleaks_scan.py install --dest DIR   instala a versão fixada, conferindo o SHA-256 oficial
  python scripts/security/gitleaks_scan.py staged               conteúdo no stage (pre-commit)
  python scripts/security/gitleaks_scan.py range BASE..HEAD     cada commit do intervalo, inclusive intermediários (CI)
  python scripts/security/gitleaks_scan.py history              todas as refs locais (investigação; não é o gate de CI)

Imprime só regra, arquivo, linha e commit. O relatório bruto do gitleaks fica num diretório temporário apagado ao fim;
`--report` grava apenas esses metadados. Saída: 0 limpo, 1 achados, 2 erro (scanner ausente, versão errada, falha).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

GITLEAKS_VERSION = "8.30.1"
# gitleaks_8.30.1_checksums.txt da release oficial (github.com/gitleaks/gitleaks/releases/tag/v8.30.1).
CHECKSUMS = {
    "darwin_arm64.tar.gz": "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5",
    "darwin_x64.tar.gz": "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709",
    "linux_arm64.tar.gz": "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080",
    "linux_x64.tar.gz": "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
    "windows_x64.zip": "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e",
}
REPO_ROOT = Path(__file__).resolve().parents[2]
CAMPOS = ("RuleID", "File", "StartLine", "Commit")
LEAKS_EXIT = 3  # distingue "achou segredo" (3) de erro de execução (1) no gitleaks


class ScanError(RuntimeError):
    pass


def _alvo_plataforma() -> str:
    so = {"linux": "linux", "darwin": "darwin", "win32": "windows"}.get(sys.platform)
    arq = {"x86_64": "x64", "amd64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine().lower())
    ext = "zip" if so == "windows" else "tar.gz"
    chave = f"{so}_{arq}.{ext}"
    if chave not in CHECKSUMS:
        raise ScanError(f"plataforma sem checksum fixado: {sys.platform}/{platform.machine()}")
    return chave


def extrair_binario(dados: bytes, chave: str, dest: Path) -> Path:
    """Confere o SHA-256 ANTES de abrir o arquivo; extrai só o executável, sem caminhos vindos do arquivo."""
    obtido = hashlib.sha256(dados).hexdigest()
    if obtido != CHECKSUMS[chave]:
        raise ScanError(f"SHA-256 não confere para {chave}: esperado {CHECKSUMS[chave]}, obtido {obtido}")
    nome = "gitleaks.exe" if chave.endswith(".zip") else "gitleaks"
    if chave.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            binario = z.read(nome)
    else:
        with tarfile.open(fileobj=io.BytesIO(dados), mode="r:gz") as t:
            membro = t.extractfile(nome)
            if membro is None:
                raise ScanError(f"{nome} ausente no arquivo")
            binario = membro.read()
    dest.mkdir(parents=True, exist_ok=True)
    saida = dest / nome
    saida.write_bytes(binario)
    saida.chmod(saida.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return saida


def instalar(dest: Path) -> Path:
    """Baixa e verifica a versão fixada; se o destino já tem essa versão, mantém."""
    chave = _alvo_plataforma()
    atual = dest / ("gitleaks.exe" if chave.endswith(".zip") else "gitleaks")
    if atual.exists() and _versao(str(atual)) == GITLEAKS_VERSION:
        return atual
    url = (f"https://github.com/gitleaks/gitleaks/releases/download/v{GITLEAKS_VERSION}/"
           f"gitleaks_{GITLEAKS_VERSION}_{chave}")
    with urllib.request.urlopen(url, timeout=120) as r:  # noqa: S310 (URL fixa, https)
        dados = r.read()
    return extrair_binario(dados, chave, dest)


def _versao(binario: str) -> str:
    try:
        r = subprocess.run([binario, "version"], capture_output=True, text=True)
    except OSError:
        return ""
    return r.stdout.strip().lstrip("v") if r.returncode == 0 else ""


def localizar() -> str:
    binario = os.environ.get("GITLEAKS_BIN") or shutil.which("gitleaks")
    if not binario or not Path(binario).exists():
        raise ScanError(f"gitleaks ausente: instale a versão {GITLEAKS_VERSION} com "
                        f"`python scripts/security/gitleaks_scan.py install --dest <dir no PATH>`")
    versao = _versao(binario)
    if versao != GITLEAKS_VERSION:
        raise ScanError(f"gitleaks {versao or '?'} encontrado; a versão fixada é {GITLEAKS_VERSION}")
    return binario


def varrer(modo: str, repo: Path, config: Path, intervalo: str = "") -> list:
    """Achados só com metadados. O stdout/stderr do gitleaks nunca é repassado."""
    binario = localizar()
    # Sem --diff-merges, o `git log -p` do gitleaks omite o diff dos merges: segredo posto só na resolução passaria.
    merges = "--diff-merges=first-parent"
    alvo = {"staged": ["--staged"], "history": [f"--log-opts={merges} --all"],
            "range": [f"--log-opts={merges} {intervalo}"]}[modo]
    with tempfile.TemporaryDirectory(prefix="gitleaks-") as tmp:
        relatorio = Path(tmp) / "bruto.json"
        r = subprocess.run(
            [binario, "git", *alvo, "--config", str(config), "--redact", "--no-banner", "--no-color",
             "--exit-code", str(LEAKS_EXIT), "--report-format", "json", "--report-path", str(relatorio), str(repo)],
            capture_output=True, text=True, cwd=str(repo))
        if r.returncode not in (0, LEAKS_EXIT):
            raise ScanError(f"gitleaks falhou (código {r.returncode}); rode-o manualmente com --redact para ver o erro")
        bruto = json.loads(relatorio.read_text(encoding="utf-8") or "[]") if relatorio.exists() else []
    if r.returncode == LEAKS_EXIT and not bruto:
        raise ScanError("gitleaks indicou achados, mas o relatório veio vazio")
    return [{k: a.get(k, "") for k in CAMPOS} for a in bruto]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("modo", choices=("install", "staged", "range", "history"))
    ap.add_argument("intervalo", nargs="?", default="", help="BASE..HEAD, no modo range")
    ap.add_argument("--dest", type=Path, help="diretório de instalação, no modo install")
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--config", type=Path, default=REPO_ROOT / ".gitleaks.toml")
    ap.add_argument("--report", type=Path, help="JSON sanitizado (só metadados)")
    a = ap.parse_args(argv)
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    try:
        if a.modo == "install":
            if not a.dest:
                raise ScanError("--dest é obrigatório no modo install")
            print(f"[gitleaks] instalado e verificado: {instalar(a.dest)}")
            return 0
        if a.modo == "range" and ".." not in a.intervalo:
            raise ScanError("modo range exige BASE..HEAD")
        achados = varrer(a.modo, a.repo, a.config, a.intervalo)
    except (ScanError, OSError, ValueError) as exc:
        print(f"[gitleaks] ERRO: {exc}", file=sys.stderr)
        return 2
    if a.report:
        a.report.write_text(json.dumps(achados, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in achados:
        print(f"[gitleaks] {f['RuleID']}  {f['File']}:{f['StartLine']}  commit={(f['Commit'] or 'stage')[:12]}",
              file=sys.stderr)
    print(f"[gitleaks] {a.modo}: {len(achados)} achado(s)", file=sys.stderr)
    return 1 if achados else 0


if __name__ == "__main__":
    sys.exit(main())
