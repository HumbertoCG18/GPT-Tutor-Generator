"""Rótulos curtos e nomes de unidade a partir de slugs canônicos.

Base compartilhada: o builder (artifacts/temporal_context) e a UI
(timeline_dashboard) consomem daqui. Sem dependências para cima.
"""

from __future__ import annotations

import re
from typing import Optional

_UNIT_NUM_RE = re.compile(r"unidade[-_\s]*0*(\d+)", re.IGNORECASE)


def unit_number(slug: str) -> Optional[int]:
    """Número da unidade no slug, ou None se não casar o padrão."""
    m = _UNIT_NUM_RE.search(str(slug or ""))
    return int(m.group(1)) if m else None


def unit_short_label(slug: str) -> str:
    """'unidade-01-limites' -> 'U1'. Mantém o original se não casar o padrão."""
    s = str(slug or "").strip()
    if not s:
        return ""
    n = unit_number(s)
    return f"U{n}" if n is not None else s


def unit_name_from_slug(slug: str) -> str:
    """'unidade-01-limites' -> 'Limites'. Sem sufixo de nome -> o próprio slug."""
    s = str(slug or "").strip()
    if not s:
        return ""
    m = _UNIT_NUM_RE.search(s)
    if not m:
        return s
    tail = s[m.end():].lstrip("-_ ")
    name = tail.replace("-", " ").replace("_", " ").strip()
    if not name:
        return s
    return name[:1].upper() + name[1:]
