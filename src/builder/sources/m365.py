"""Cliente Microsoft Graph (OneDrive/SharePoint) — fonte secundária de cards.

Arquivos que o professor hospeda no OneDrive dele não aparecem na API do Moodle.
Descoberta via /me/insights/shared (o que a página /shared do OneDrive mostra),
download via /me/insights/shared/{id}/resource. Auth device-code (client público
"Microsoft Graph Command Line Tools"); só leitura. Token em moddle/.m365_token.json.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.parse
from pathlib import Path

import requests

from src.builder.sources.moodle import (
    looks_like_expected, sanitize_folder_name, default_token_path,
)

_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"  # Microsoft Graph Command Line Tools
_AUTHORITY = "https://login.microsoftonline.com/organizations/oauth2/v2.0"
_SCOPE = "Files.Read.All Sites.Read.All offline_access"
_GRAPH = "https://graph.microsoft.com/v1.0"
_ROOT_CARD = "_geral"


def parse_onedrive_path(web_url: str) -> list:
    p = urllib.parse.urlparse(str(web_url or ""))
    return [seg for seg in urllib.parse.unquote(p.path).split("/") if seg]


def subfolder_for(web_url: str, m365_filter: str, default: str = _ROOT_CARD) -> str:
    segs = parse_onedrive_path(web_url)
    fl = (m365_filter or "").lower()
    idx = next((i for i, s in enumerate(segs) if fl and fl in s.lower()), None)
    if idx is None:
        return default
    after = segs[idx + 1:]
    if len(after) <= 1:                       # só o nome do arquivo -> raiz do curso
        return default
    return sanitize_folder_name(after[0])


def select_for_subject(items, m365_filter: str) -> list:
    fl = (m365_filter or "").lower()
    if not fl:
        return []
    return [it for it in items if fl in str(it.get("web_url", "")).lower()]


def _norm_tokens(s: str) -> set:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii").lower()
    return {t for t in re.split(r"[\s_\-./]+", s) if len(t) > 2}


def _token_affinity(a: set, b: set) -> float:
    """Sobreposição tolerante: conta tokens iguais OU um contido no outro."""
    if not a or not b:
        return 0.0
    hits = 0
    for ta in a:
        if any(ta == tb or ta in tb or tb in ta for tb in b):
            hits += 1
    return hits / min(len(a), len(b))


def match_card(subfolder: str, moodle_sections, threshold: float = 0.34):
    sf = _norm_tokens(subfolder)
    best, best_score = None, 0.0
    for sec in moodle_sections or []:
        score = _token_affinity(sf, _norm_tokens(sec))
        if score > best_score:
            best, best_score = sec, score
    if best and best_score >= threshold:
        return best, True
    return sanitize_folder_name(subfolder), False
