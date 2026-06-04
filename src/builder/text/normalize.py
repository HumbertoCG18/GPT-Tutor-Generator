from __future__ import annotations

import re
import unicodedata


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
