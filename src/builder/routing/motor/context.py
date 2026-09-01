"""Loader único do motor (FASE 4 item 5): artefatos por-curso + memoizações.

Fonte única do que os probes fase0-3 duplicavam (build_context). READ-ONLY:
lê os 3 artefatos gerados do repo-tutor, nunca escreve.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from src.builder.routing.motor.contracts import MotorContext

logger = logging.getLogger(__name__)


def load_repo_artifact(repo: Path, rel: str):
    p = Path(repo) / rel
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("artefato %s ilegivel: %s", rel, exc)
        return {}


def build_motor_context(repo: Path, course_name: str = "") -> MotorContext:
    tl = load_repo_artifact(repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = load_repo_artifact(repo, "course/.card_block_map.json")
    lessons = (load_repo_artifact(repo, "course/.lessons_index.json") or {}).get("by_date", {})
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index=lessons,
        course_name=course_name,
    )
