"""Aquisição leve de conteúdo de referência (sem clone).

GitHub -> README via API (resolve branch default sozinho). Doc/URL -> texto de
página via o extrator HTML existente. Funções com I/O de rede isolado; erros de
rede degradam para "" (nunca levantam para o caller do build).
"""
from __future__ import annotations

import re
from typing import Optional

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
