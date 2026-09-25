"""Higiene do repositório contra credenciais versionadas (#80, #82; incidente de 24/09).

Uso:
  python scripts/security/check_repo_hygiene.py tree              A) versionado que o .gitignore manda ignorar;
                                                                  B) caminho de credencial na árvore
  python scripts/security/check_repo_hygiene.py range BASE..HEAD  B) caminho de credencial criado ou alterado em
                                                                  qualquer commit do intervalo, inclusive intermediários
  python scripts/security/check_repo_hygiene.py staged            B) caminho de credencial no stage (pre-commit)

B independe do .gitignore: pega `git add -f` e branches sem a regra. Imprime só caminhos e commits, nunca conteúdo.
Saída: 0 limpo, 1 violação, 2 erro.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import PurePosixPath

# Caches de credencial conhecidos deste projeto; exemplos (.env.example) e JSONs em geral continuam permitidos.
NOMES_PROIBIDOS = {".env", ".m365_token.json"}
SUFIXOS_PROIBIDOS = (".dpapi",)


def proibido(caminho: str) -> bool:
    nome = PurePosixPath(caminho).name.casefold()  # .ENV e .env são o mesmo arquivo no Windows
    return nome in NOMES_PROIBIDOS or nome.endswith(SUFIXOS_PROIBIDOS)


def _git(*args: str) -> str:
    r = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"git {args[0]} falhou (código {r.returncode}): {r.stderr.strip()[:300]}")
    return r.stdout


def _lista(saida: str) -> list:
    return [p for p in saida.split("\0") if p]


def verificar_arvore() -> list:
    ignorados = _lista(_git("ls-files", "-ci", "--exclude-standard", "-z"))
    erros = [f"versionado mas ignorado pelo .gitignore: {p}" for p in ignorados]
    erros += [f"caminho de credencial versionado: {p}" for p in _lista(_git("ls-files", "-z")) if proibido(p)]
    return erros


def verificar_intervalo(intervalo: str) -> list:
    """Cada commit; merges contra cada pai (-m); nomes via -z, sem aspas nem escapes."""
    erros = set()
    for commit in _git("rev-list", intervalo).split():
        nomes = _git("diff-tree", "-m", "-r", "--root", "--no-commit-id", "--name-only", "--diff-filter=ACMR",
                     "-z", commit)
        erros.update(f"caminho de credencial no commit {commit[:12]}: {p}" for p in _lista(nomes) if proibido(p))
    return sorted(erros)


def verificar_stage() -> list:
    return [f"caminho de credencial no stage: {p}"
            for p in _lista(_git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")) if proibido(p)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("modo", choices=("tree", "range", "staged"))
    ap.add_argument("intervalo", nargs="?", default="")
    a = ap.parse_args(argv)
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    try:
        if a.modo == "range" and ".." not in a.intervalo:
            raise RuntimeError("modo range exige BASE..HEAD")
        if a.modo == "tree":
            erros = verificar_arvore()
        elif a.modo == "staged":
            erros = verificar_stage()
        else:
            erros = verificar_intervalo(a.intervalo)
    except (RuntimeError, OSError) as exc:
        print(f"[higiene] ERRO: {exc}", file=sys.stderr)
        return 2
    for e in erros:
        print(f"[higiene] {e}", file=sys.stderr)
    print(f"[higiene] {a.modo}: {len(erros)} violação(ões)", file=sys.stderr)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
