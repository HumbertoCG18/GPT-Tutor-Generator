"""Aquisição leve de conteúdo de referência (sem clone).

GitHub -> README via API (resolve branch default sozinho). Doc/URL -> texto de
página via o extrator HTML existente. Funções com I/O de rede isolado; erros de
rede degradam para "" (nunca levantam para o caller do build).
"""
from __future__ import annotations

import re
from typing import Optional

import requests

from src.utils.helpers import collapse_ws as _collapse_ws

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


def _fetch_doc_text(url: str, *, timeout: float = 10.0) -> str:
    """Texto do corpo de uma página (doc/artigo) via o extrator HTML existente."""
    try:
        resp = requests.get(url, headers={"User-Agent": "gpt-tutor-generator"}, timeout=timeout)
    except Exception:
        return ""
    if resp.status_code != 200 or not resp.text:
        return ""
    from src.builder.text.url_markdown import html_to_structured_markdown, truncate_markdown_blocks
    try:
        return html_to_structured_markdown(
            resp.text, url, "",
            collapse_ws=_collapse_ws,
            truncate_markdown_blocks=truncate_markdown_blocks,
        )
    except Exception:
        return ""


def fetch_reference_text(entry: dict, *, max_chars: int = 16000) -> str:
    """Conteúdo leve de uma referência. GitHub -> README; doc/URL -> texto de
    página. "" se sem fonte ou em qualquer falha. Trunca em max_chars."""
    source = str(entry.get("source_path") or "").strip()
    if not source:
        return ""
    gh = parse_github_repo(source) if (
        str(entry.get("file_type") or "") == "github-repo" or "github.com" in source
    ) else None
    if gh:
        text = fetch_github_readme(*gh)
    else:
        text = _fetch_doc_text(source)
    text = text or ""
    return text[:max_chars]
