"""Tokenizador UNICO do motor (corte 3 do refactor, 2026-09-03).

Strangler: nasce como a fonte do `disambiguator._toks` (byte-identico ao que ele fazia) e os
outros 12 tokenizadores do repositorio migram para ca na limpa pre-web (C4), um por vez,
cada um com sentinela 0. Nao mude a semantica aqui sem remedir as reguas.
"""
from __future__ import annotations

import re

from src.builder.text.normalize import normalize_match_text

_CAMEL_RE = re.compile(r"(?<=[a-z])(?=[A-Z])")


def motor_tokens(text: str, *, generic_stems=frozenset(), short_vocab=frozenset(), min_len: int = 3) -> set:
    """Tokens normalizados >= min_len chars (ou CURTOS consagrados em `short_vocab`), sem
    digitos-puros nem stems genericos (t[:8] em generic_stems). Quebra camelCase ANTES do
    fold (LogicaDeHoare -> logica de hoare)."""
    out: set = set()
    for t in normalize_match_text(_CAMEL_RE.sub(" ", str(text or ""))).split():
        if t.isdigit() or t[:8] in generic_stems:
            continue
        if len(t) >= min_len or t in short_vocab:
            out.add(t)
    return out
