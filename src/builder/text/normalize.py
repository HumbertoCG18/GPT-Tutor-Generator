from __future__ import annotations

import re
import unicodedata
from typing import Callable, Optional


def normalize_match_text(
    text: str,
    *,
    keep: str = "",
    em_dash_to_hyphen: bool = True,
    fix_typos: bool = True,
) -> str:
    """NFKD + remove acentos + lower + so [a-z0-9 ] (+ chars em `keep`).

    Fonte unica do projeto (antes duplicada em ~6 modulos).

    `keep` preserva caracteres extras: content_taxonomy usa keep="+-./"
    porque os dados reais tem datas ("11/03/2026"), prefixos de outline
    ("1.2.3."), paths ("consensys/eth2.0-dafny") e slugs com hifen que
    viram tokens distintivos — medido sobre o indice real de MF
    (51/211 textos divergem sem o keep).

    `em_dash_to_hyphen=False`: nao converte — / – para -; o classifier usa
    False porque seu comportamento historico e deixar o travessao virar
    espaco via regex (divergencia preservada intencionalmente).
    `fix_typos=False`: pula o fix propocional->proposicional; idem classifier.
    """
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    if em_dash_to_hyphen:
        text = text.replace("—", "-").replace("–", "-")
    if fix_typos:
        text = text.replace("propocional", "proposicional")
    text = re.sub(rf"[^a-z0-9{re.escape(keep)}\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[a-z])(?=\d)")


def split_camel_case(text: str) -> str:
    """Insere espaço em fronteiras minúscula→Maiúscula e minúscula→dígito.

    "LogicaDeHoare2" → "Logica De Hoare 2". Siglas puras (IHC, P1) intactas —
    a fronteira letra→dígito só vale após MINÚSCULA, senão "P1" viraria "P 1".
    Pré-processamento de TÍTULO antes do normalize (P4/S1) — não mexe na fonte
    única normalize_match_text."""
    return _CAMEL_BOUNDARY.sub(" ", text or "")


def signal_token_set(
    signal_text: str,
    *,
    normalize: Optional[Callable[[str], str]] = None,
    min_token_len: int = 4,
) -> set:
    """Tokens >= min_token_len do texto normalizado. Fonte unica (P4 Fase 0).

    Antes duplicada em content_taxonomy e timeline/index. O parametro
    `normalize` permite injetar variantes (content_taxonomy passa a fonte
    unica com keep="+-./").
    """
    normalizer = normalize or normalize_match_text
    return {token for token in normalizer(signal_text).split() if len(token) >= min_token_len}
