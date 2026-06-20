"""Ledger de identidade de blocos do cronograma.

Cada bloco recebe um uuid persistido re-anexado a cada rebuild por best-overlap
de datas (period_start..period_end) + desempate por overlap de topic_tokens.
NÃO usa hash de conteúdo — hash quebra exatamente no split que queremos proteger.

Arquivo: <course_dir>/.block_identity.json (append-only, trackeado no git).
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from uuid import uuid4

from src.utils.helpers import norm_ascii_lower
from src.builder.text.stopwords import CARD_BLOCK_STOP as _STOP

_LEDGER_NAME = ".block_identity.json"
_CURATION_NAME = ".timeline_curation.json"
_CARD_MAP_NAME = ".card_block_map.json"

_NEAR_TIE_EPSILON = 0.05  # margem relativa para near-tie radar

# Positional ids (bloco-NN, índice nu) are legacy; only uuid-format refs trigger the guard.
_POSITIONAL_RE = re.compile(r"^bloco-\d+$|^\d+$")


class BlockIdentityError(Exception):
    pass


def _today() -> str:
    return date.today().isoformat()


def _tokens(text: str) -> set:
    return {t for t in norm_ascii_lower(text).split() if t and t not in _STOP and len(t) > 2}


def _block_topic_tokens(block: dict) -> set:
    parts = [str(block.get("topic_text") or "")]
    for t in block.get("topics") or []:
        if isinstance(t, dict):
            parts.append(str(t.get("label") or t.get("slug") or ""))
        else:
            parts.append(str(t))
    parts += [str(a) for a in (block.get("aliases") or [])]
    return _tokens(" ".join(parts))


def _parse_date(s: str) -> Optional[date]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _overlap_days(a_start: Optional[date], a_end: Optional[date],
                  b_start: Optional[date], b_end: Optional[date]) -> int:
    if not (a_start and a_end and b_start and b_end):
        return 0
    lo = max(a_start, b_start)
    hi = min(a_end, b_end)
    delta = (hi - lo).days + 1
    return max(0, delta)


def _token_overlap(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / max(len(set_a), len(set_b))


def _has_human_ref(record: dict) -> bool:
    anchor = record.get("anchor") or {}
    return bool(
        record.get("manual_timeline_block_id")
        or record.get("true_block_id")
        or record.get("expected_block_id")
        or anchor.get("has_human_ref")
    )


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def load_identity_ledger(course_dir) -> List[dict]:
    path = Path(course_dir) / _LEDGER_NAME
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_identity_ledger(course_dir, records: List[dict]) -> None:
    path = Path(course_dir) / _LEDGER_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    import os
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Re-attach
# ---------------------------------------------------------------------------


def reattach_block_uuids(
    runtime_blocks: List[dict],
    ledger: List[dict],
    *,
    has_existing_refs: bool,
    mint: Callable[[], str] = lambda: str(uuid4()),
) -> Tuple[List[dict], List[dict], List[str]]:
    """Attach block_uuid to each runtime_block via best date-overlap matching.

    Returns (blocks_with_uuid, updated_ledger, flags).
    Ledger is append-only: existing records are never deleted.
    """
    if not ledger and has_existing_refs:
        raise BlockIdentityError(
            "Ledger ausente/vazio mas existem referências persistidas apontando para blocos. "
            "Abortar para não orfanar referências existentes. "
            "Restaure .block_identity.json do git antes de continuar."
        )

    today = _today()
    updated_ledger = list(ledger)
    flags: List[str] = []

    for block in runtime_blocks:
        b_start = _parse_date(str(block.get("period_start") or ""))
        b_end = _parse_date(str(block.get("period_end") or ""))
        b_tokens = _block_topic_tokens(block)
        display_id = str(block.get("id") or "")

        if not (b_start and b_end):
            new_uuid = mint()
            flags.append(f"no-date:mint:{new_uuid}:{display_id}")
            updated_ledger.append({
                "uuid": new_uuid,
                "anchor": {
                    "period_start": str(block.get("period_start") or ""),
                    "period_end": str(block.get("period_end") or ""),
                    "topic_tokens": sorted(b_tokens),
                },
                "display_id_last": display_id,
                "first_seen": today,
                "last_seen": today,
            })
            block["block_uuid"] = new_uuid
            continue

        # Score every ledger record
        scored: List[Tuple[int, float, int, dict]] = []
        for rec in updated_ledger:
            anchor = rec.get("anchor") or {}
            r_start = _parse_date(str(anchor.get("period_start") or ""))
            r_end = _parse_date(str(anchor.get("period_end") or ""))
            ov = _overlap_days(b_start, b_end, r_start, r_end)
            if ov == 0:
                continue
            tok_ov = _token_overlap(b_tokens, set(anchor.get("topic_tokens") or []))
            idx = updated_ledger.index(rec)
            scored.append((ov, tok_ov, idx, rec))

        if not scored:
            new_uuid = mint()
            updated_ledger.append({
                "uuid": new_uuid,
                "anchor": {
                    "period_start": b_start.isoformat(),
                    "period_end": b_end.isoformat(),
                    "topic_tokens": sorted(b_tokens),
                },
                "display_id_last": display_id,
                "first_seen": today,
                "last_seen": today,
            })
            block["block_uuid"] = new_uuid
            continue

        # Sort by (overlap_days DESC, token_overlap DESC)
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_ov, best_tok, best_idx, best_rec = scored[0]

        # Near-tie radar: second candidate within epsilon of best
        if len(scored) >= 2:
            second_ov, second_tok, _, second_rec = scored[1]
            if best_ov > 0:
                relative_gap = (best_ov - second_ov) / best_ov
                if relative_gap < _NEAR_TIE_EPSILON and (_has_human_ref(best_rec) or _has_human_ref(second_rec)):
                    flags.append(
                        f"near-tie:{best_rec['uuid']}:{second_rec['uuid']}:{display_id}"
                    )

        # Exact tie on overlap with no token differentiation → mint
        if len(scored) >= 2:
            second_ov, second_tok, _, _ = scored[1]
            if best_ov == second_ov and best_tok == second_tok and best_tok == 0.0:
                new_uuid = mint()
                flags.append(f"exact-tie:mint:{new_uuid}:{display_id}")
                updated_ledger.append({
                    "uuid": new_uuid,
                    "anchor": {
                        "period_start": b_start.isoformat(),
                        "period_end": b_end.isoformat(),
                        "topic_tokens": sorted(b_tokens),
                    },
                    "display_id_last": display_id,
                    "first_seen": today,
                    "last_seen": today,
                })
                block["block_uuid"] = new_uuid
                continue

        # Inherit best match
        inherited_uuid = best_rec["uuid"]
        # Refresh anchor and last_seen in-place
        updated_ledger[best_idx] = {
            **best_rec,
            "anchor": {
                "period_start": b_start.isoformat(),
                "period_end": b_end.isoformat(),
                "topic_tokens": sorted(b_tokens),
            },
            "display_id_last": display_id,
            "last_seen": today,
        }
        block["block_uuid"] = inherited_uuid

    return runtime_blocks, updated_ledger, flags


# ---------------------------------------------------------------------------
# scan_existing_block_refs
# ---------------------------------------------------------------------------


def _is_uuid_ref(value: str) -> bool:
    """True if value looks like a uuid (not a legacy bloco-NN / bare int)."""
    return bool(value) and not _POSITIONAL_RE.match(str(value).strip())


def scan_existing_block_refs(course_dir, manifest: dict) -> bool:
    """True if any uuid-format block reference exists in persisted surfaces.

    Legacy positional refs (bloco-NN, bare N) are NOT counted — they predated
    the ledger and can be safely minted over during initial bootstrap.
    """
    course_dir = Path(course_dir)

    # manifest fields — only uuid-format triggers guard
    for field in ("manual_timeline_block_id", "computed_block_id"):
        val = str(manifest.get(field) or "").strip()
        if _is_uuid_ref(val):
            return True

    # card_block_map — block_ids list
    cbm_path = course_dir / _CARD_MAP_NAME
    if cbm_path.is_file():
        try:
            cbm = json.loads(cbm_path.read_text(encoding="utf-8"))
            for v in cbm.values():
                if isinstance(v, dict):
                    for bid in (v.get("block_ids") or []):
                        if _is_uuid_ref(str(bid)):
                            return True
        except (json.JSONDecodeError, OSError):
            pass

    # timeline curation — keys are block ids
    curation_path = course_dir / _CURATION_NAME
    if curation_path.is_file():
        try:
            curation = json.loads(curation_path.read_text(encoding="utf-8"))
            for key in (curation.get("blocks") or {}):
                if _is_uuid_ref(str(key)):
                    return True
        except (json.JSONDecodeError, OSError):
            pass

    return False
