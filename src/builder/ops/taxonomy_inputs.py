"""Montador UNICO de insumos de taxonomia (campanha gerador-indice-unico, C2).

Producao (pedagogical_regeneration.py:394-402) monta taxonomia com as entries
VIVAS do manifest; sondas e rebuild passavam content_taxonomy=None e caiam no
fallback pobre (index.py:1363, manifest_entries=None) - causa-raiz do flip de
kind do TCC bloco-13. Todo caminho fora da regeneracao monta a taxonomia POR
AQUI para que sonda == producao por construcao.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def build_rich_content_taxonomy(
    repo_root,
    course_meta: dict,
    subject_profile,
    *,
    taxonomy_fn: Callable[..., dict],
    filter_live_fn: Callable[..., list],
    entries: Optional[list] = None,
) -> dict:
    if entries is None:
        manifest_path = Path(repo_root) / "manifest.json"
        entries = []
        if manifest_path.is_file():
            try:
                entries = json.loads(manifest_path.read_text(encoding="utf-8")).get("entries", []) or []
            except (json.JSONDecodeError, OSError):
                logger.warning("manifest.json ilegivel em %s — taxonomia degrada pra pobre (0 entries)", repo_root)
                entries = []
        else:
            logger.warning("manifest.json ausente em %s — taxonomia degrada pra pobre (0 entries)", repo_root)
    live = filter_live_fn(repo_root, entries)
    return taxonomy_fn(course_meta, subject_profile, live)
