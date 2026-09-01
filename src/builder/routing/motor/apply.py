"""Producer D9 (FASE 4): AnchorEngine -> temporal_* nas entries, in place.

Substitui apply_anchor_placement no call-site quando use_anchor_engine=ON
(caminho legado intacto até o cutover FASE 5). Invariantes:
- ANCHOR-ONLY: nunca toca computed_* nem manual_timeline_block_id.
- Pino manual válido = verdade humana: motor NÃO escreve e REMOVE temporal
  stale (leitor resolve_temporal_block cai no fallback manual>computed).
- TIER 0: grupo md5 (content_key) recebe UMA decisão (dup-divergence = 0).
- TIER 2 janela-de-prazo (FASE 5): due-window plugado ANTES do fora-de-escopo,
  decisão por-entry SEM dup-cache (escopo é atributo da ENTRY, review F4 I1).
- Sem âncora (None) = funil-piso: temporal_* removido se existia.

Cascata: pino > tier2_due_scope(provider due-window) > is_out_of_disamb_scope
> dup-cache (TIER 0) > engine (janela+disambig+voto).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

from src.builder.routing.motor.anchor_engine import (
    AnchorEngine, is_out_of_disamb_scope, resolve_generic_reference,
)
from src.builder.routing.motor.context import build_motor_context
from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.builder.routing.motor.due_window import resolve_due_window, tier2_due_scope
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
    entry["temporal_block_window"] = [str(r) for r in (decision.window or []) if r]


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
        if tier2_due_scope(entry):
            # TIER 2 janela-de-prazo (spec 2026-07-22): decisão por-entry, sem
            # dup-cache — escopo é atributo da ENTRY (lição review F4 I1).
            decision = resolve_due_window(entry, ctx)
            if decision is None:
                # B-4/B-6: sem due casado, provas/trabalhos percorrem a cascata de
                # janela (card manual/datado, data, ordinal, topico -> desempate ->
                # voto) e so entao o llm-funil. Um card manual cobre o cluster
                # inteiro de uma vez (TCC "Semana 14 - Apresentacoes T2").
                decision = engine.resolve_unscoped(
                    entry, ctx, markdown=str(md_of(entry) or ""), lexical=False)
            if decision is None:
                _clear_temporal(entry)
                continue
            _write_temporal(entry, decision, ctx)
            continue
        if is_out_of_disamb_scope(entry):
            # review F4 I1: escopo é atributo da ENTRY, não do conteúdo. Sem este
            # skip ANTES do lookup em `decided`, um gêmeo md5 fora-de-escopo
            # (bibliografia/TDE) herdaria a decisão do gêmeo in-scope (cache-hit)
            # OU, na ordem inversa, gravaria decided[key]=None e apagaria a
            # decisão do gêmeo in-scope processado depois (cache-poison).
            _clear_temporal(entry)
            continue
        # B-6: referencia sem card -> primeiro bloco de aula (convencao dos pinos).
        # Antes do cache por conteudo: escopo e atributo da ENTRY (review F4 I1).
        decision = resolve_generic_reference(entry, ctx)
        if decision is not None:
            _write_temporal(entry, decision, ctx)
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
    _inherit_from_numbered_sibling(entries, ctx, md_of)
    return entries


_SIBLING_RE = re.compile(r"^([a-z]+?)[-_]?(\d{1,2})(?!\d)")


def _sibling_key(entry: dict):
    """(card, radical, numero) de ids como `roteiro4` / `roteiro4-circuitbreaker`."""
    m = _SIBLING_RE.match(str(entry.get("id") or "").lower())
    card = str(entry.get("source_section") or "").strip().casefold()
    return (card, m.group(1), m.group(2)) if (m and card) else None


def _inherit_from_numbered_sibling(entries: list, ctx: MotorContext, md_of) -> None:
    """Irmão numerado no card (2026-08-25): entry SEM texto herda o bloco do
    irmão COM texto que partilha card + radical + número.

    ES2: `roteiro4.zip` (código sem markdown, o LLM vota no vazio) mora no
    mesmo card que `Roteiro4_circuitbreaker.pdf`, que o motor acerta. Censo
    nos 5 cursos: 8 grupos com gold, 8 concordam (MF, IA, ES2) — estrutura do
    Moodle, não regra por curso/categoria. Só entries sem texto, em escopo e
    sem pino mudam; irmãos com texto que discordam entre si não decidem."""
    groups: dict = {}
    for e in entries:
        key = _sibling_key(e)
        if key:
            groups.setdefault(key, []).append(e)
    for members in groups.values():
        if len(members) < 2:
            continue
        has_text = {e["id"]: bool(str(md_of(e) or "").strip()) for e in members}
        refs = {str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or "").strip()
                for e in members if has_text[e["id"]]}
        refs.discard("")
        if len(refs) != 1:
            continue
        block = ctx.block_by_ref(refs.pop())
        if block is None:
            continue
        ref = str(block.get("id") or "")
        for e in members:
            if has_text[e["id"]] or _valid_manual_pin(e, ctx) or tier2_due_scope(e) \
                    or is_out_of_disamb_scope(e):
                continue
            _write_temporal(e, AnchorDecision(block_ref=ref, conf=0.0, band="media", flag=False,
                                              provider="irmao-card", method="irmao-card",
                                              window=[ref]), ctx)
