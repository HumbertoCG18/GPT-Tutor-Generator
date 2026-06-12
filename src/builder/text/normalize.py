from __future__ import annotations

import re
import unicodedata
from typing import Callable, Optional


def normalize_match_text(text: str) -> str:
    """NFKD + remove acentos + lower + so [a-z0-9 ]. Fonte unica do projeto.

    Antes duplicada em ~6 modulos; agora todos re-importam daqui.
    """
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("propocional", "proposicional")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def signal_token_set(
    signal_text: str,
    *,
    normalize: Optional[Callable[[str], str]] = None,
    min_token_len: int = 4,
) -> set:
    """Tokens >= min_token_len do texto normalizado. Fonte unica (P4 Fase 0).

    Antes duplicada em content_taxonomy e timeline/index. O parametro
    `normalize` existe so porque content_taxonomy ainda usa a copia local
    divergente de normalize_match_text (preserva +-./) — some quando a
    Task 3 unificar o normalize.
    """
    normalizer = normalize or normalize_match_text
    return {token for token in normalizer(signal_text).split() if len(token) >= min_token_len}
