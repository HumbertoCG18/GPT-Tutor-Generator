"""Producer D9 (FASE 4): AnchorEngine -> temporal_* nas entries, in place.

Substitui apply_anchor_placement no call-site quando use_anchor_engine=ON
(caminho legado intacto até o cutover FASE 5). Invariantes:
- ANCHOR-ONLY: nunca toca computed_* nem manual_timeline_block_id.
- Pino manual válido = verdade humana: motor NÃO escreve e REMOVE temporal
  stale (leitor resolve_temporal_block cai no fallback manual>computed).
- TIER 0: grupo md5 (content_key) recebe UMA decisão (dup-divergence = 0).
- Sem âncora (None) = funil-piso: temporal_* removido se existia.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from src.builder.routing.motor.anchor_engine import AnchorEngine, is_out_of_disamb_scope
from src.builder.routing.motor.context import build_motor_context
from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.builder.routing.motor.llm_vote import content_key, detect_same_theme_series

TEMPORAL_KEYS = (
    "temporal_block_id", "temporal_block_method", "temporal_block_band",
    "temporal_block_flag", "temporal_block_provider", "temporal_block_window",
)


def _valid_manual_pin(entry: dict, ctx: MotorContext) -> bool:
    pin = str(entry.get("manual_timeline_block_id") or "").strip()
    return bool(pin) and ctx.block_by_ref(pin) is not None


def _clear_temporal(entry: dict) -> None:
    for key in TEMPORAL_KEYS:
        entry.pop(key, None)


def _write_temporal(entry: dict, decision: AnchorDecision, ctx: MotorContext) -> None:
    block = ctx.block_by_ref(decision.block_ref) or {}
    entry["temporal_block_id"] = str(block.get("block_uuid") or decision.block_ref)
    entry["temporal_block_method"] = decision.method
    entry["temporal_block_band"] = decision.band
    entry["temporal_block_flag"] = bool(decision.flag)
    entry["temporal_block_provider"] = decision.provider
    entry["temporal_block_window"] = [str(r) for r in (decision.window or [])]


def apply_anchor_engine(
    entries: list,
    repo_dir,
    course_name: str,
    *,
    enabled: bool = True,
    voter=None,
    markdown_fn: Optional[Callable[[dict], str]] = None,
) -> list:
    if not enabled:
        return entries
    repo = Path(repo_dir)
    ctx = build_motor_context(repo, course_name)
    if not ctx.blocks:
        return entries
    series = detect_same_theme_series(entries)
    engine = AnchorEngine(voter=voter, series_ids=series)
    md_of = markdown_fn or (lambda e: "")
    decided: dict = {}
    for entry in entries:
        if _valid_manual_pin(entry, ctx):
            _clear_temporal(entry)
            continue
        if is_out_of_disamb_scope(entry):
            # review F4 I1: escopo é atributo da ENTRY, não do conteúdo. Sem este
            # skip ANTES do lookup em `decided`, um gêmeo md5 fora-de-escopo
            # (bibliografia/TDE) herdaria a decisão do gêmeo in-scope (cache-hit)
            # OU, na ordem inversa, gravaria decided[key]=None e apagaria a
            # decisão do gêmeo in-scope processado depois (cache-poison).
            _clear_temporal(entry)
            continue
        key = content_key(entry, repo)
        if key in decided:
            decision = decided[key]
        else:
            decision = engine.resolve(entry, ctx, markdown=str(md_of(entry) or ""))
            decided[key] = decision
        if decision is None:
            _clear_temporal(entry)
            continue
        _write_temporal(entry, decision, ctx)
    return entries
