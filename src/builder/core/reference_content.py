"""Aquisição leve de conteúdo de referência (sem clone).

GitHub -> README via API (resolve branch default sozinho). Doc/URL -> texto de
página via o extrator HTML existente. Funções com I/O de rede isolado; erros de
rede degradam para "" (nunca levantam para o caller do build).
"""
from __future__ import annotations

import re
from typing import Optional

import requests

_GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)", re.I)


def parse_github_repo(url: str) -> Optional[tuple[str, str]]:
    """(owner, repo) de uma URL GitHub, ou None. Remove sufixo .git e path extra."""
    if not url:
        return None
    m = _GITHUB_RE.search(url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo:
        return None
    return owner, repo


def fetch_github_readme(owner: str, repo: str, *, timeout: float = 10.0) -> str:
    """README do branch DEFAULT via API do GitHub (Accept raw). "" em erro/404.

    A API resolve o branch default sozinha — contorna o bug de branch hardcoded
    do clone. Anônima (sem token): 60 req/h por IP; o cache do batch protege.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    try:
        resp = requests.get(
            url,
            headers={"Accept": "application/vnd.github.raw", "User-Agent": "gpt-tutor-generator"},
            timeout=timeout,
        )
    except Exception:
        return ""
    if resp.status_code != 200:
        return ""
    return resp.text or ""
