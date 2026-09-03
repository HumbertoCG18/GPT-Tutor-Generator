"""Card do Moodle como DOCUMENTO ORDENADO (Fase 3b, item 3): a posicao do professor vira janela.

Le os campos da Fase 3a (moodle_section_index / moodle_module_index / moodle_week_label). Por secao, em
ordem de modulo, entries consecutivas com o MESMO week_label formam um grupo alinhado ao run de semanas
daquele texto ("W1 || W2 || ..."): DP monotonica por FLUXO (categoria) — a ordem dos materiais nao volta
no tempo — com score = tokens do material (moodle_label + titulo) x tokens da semana (texto do label +
assinatura SARC dos blocos); empate -> semana mais cedo. Semana "dd/mm/aaaa a dd/mm/aaaa" -> blocos com
sessao no intervalo que hospedam material (sem hospedeiro: bloco cuja sessao/periodo contem a 1a data);
"dd/mm Topico" (modulo datado) -> ano modal do cronograma.
Medido 02/09 (`_harness-2026-09-02/mede_card_ordenado.py --stream --only-flagged`): +12/-5 nos golds de AULA.
So age em decisao FLAGADA ou sem janela (anchor_engine): estrutura estreita, texto decide, estrutura NUNCA
sobrepoe decisao confiante (a tudo: +13/-10).
"""
from __future__ import annotations

import re
from datetime import date
from typing import Dict, List

from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.disambiguator import _block_signature, _moodle_label_text, _toks
from src.builder.routing.motor.window_provider import _modal_years, hosts_material

_DATE_DMY = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_RANGE = re.compile(r"\d{1,2}/\d{1,2}/\d{4}\s*a\s*\d{1,2}/\d{1,2}/\d{4}")
_DATE_DM = re.compile(r"^\s*\[?\s*(\d{1,2})[./](\d{1,2})(?![./]?\d)")


def _bid(b: dict) -> str:
    return str(b.get("id") or "")


def _blocks_in_range(ctx: MotorContext, d1: date, d2: date) -> List[str]:
    a, z = d1.isoformat(), d2.isoformat()
    return [_bid(b) for b in ctx.blocks if _bid(b) and hosts_material(b)
            and any(a <= str(s.get("date") or "")[:10] <= z for s in (b.get("sessions") or []))]


def _date_to_block(ctx: MotorContext, d: date) -> str:
    iso = d.isoformat()
    for b in ctx.blocks:
        if any(str(s.get("date") or "")[:10] == iso for s in (b.get("sessions") or [])):
            return _bid(b)
    for b in ctx.blocks:
        ps, pe = str(b.get("period_start") or "")[:10], str(b.get("period_end") or "")[:10]
        if ps and pe and ps <= iso <= pe:
            return _bid(b)
    return ""


def _week_blocks(text: str, ctx: MotorContext) -> List[str]:
    """Blocos hospedeiros da semana descrita no texto; [] = sem data resolvivel."""
    try:
        ds = _DATE_DMY.findall(text)
        if ds:
            d1 = date(int(ds[0][2]), int(ds[0][1]), int(ds[0][0]))
            d2 = date(int(ds[1][2]), int(ds[1][1]), int(ds[1][0])) if len(ds) > 1 and _RANGE.search(text) else d1
        else:
            m = _DATE_DM.match(text)
            years = _modal_years(ctx)
            if not m or not years:
                return []
            d1 = d2 = date(int(years[0]), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return []
    if d2 < d1:
        d1, d2 = d2, d1
    blocks = _blocks_in_range(ctx, d1, d2)
    if not blocks:
        ref = _date_to_block(ctx, d1)
        blocks = [ref] if ref and hosts_material(ctx.block_by_ref(ref)) else []
    return blocks


def _align(mats: List[tuple], weeks: List[tuple], ctx: MotorContext) -> Dict[str, List[str]]:
    """DP monotonica: materiais (ordem) -> semanas (ordem); score = tokens em comum - 0.001*j."""
    W = [(bl, _toks(txt + " " + " ".join(" ".join(sorted(_block_signature(ctx.block_by_ref(b) or {}, ctx)))
                                             for b in bl))) for bl, txt in weeks]
    M = [(eid, _toks(name)) for eid, name in mats]
    n, k = len(M), len(W)
    neg = float("-inf")
    dp = [[neg] * k for _ in range(n)]
    back = [[-1] * k for _ in range(n)]

    def sc(i: int, j: int) -> float:
        return len(M[i][1] & W[j][1]) - 0.001 * j

    for j in range(k):
        dp[0][j] = sc(0, j)
    for i in range(1, n):
        best, bj = neg, -1
        for j in range(k):
            if dp[i - 1][j] > best + 1e-12:
                best, bj = dp[i - 1][j], j
            dp[i][j] = best + sc(i, j)
            back[i][j] = bj
    j = max(range(k), key=lambda jj: dp[n - 1][jj])
    out: Dict[str, List[str]] = {}
    for i in range(n - 1, -1, -1):
        out[M[i][0]] = list(W[j][0])
        j = back[i][j] if i > 0 else j
    return out


def card_windows(entries: list, ctx: MotorContext) -> Dict[str, List[str]]:
    """{entry id: janela DISPLAY} para toda entry com posicao e week_label resolviveis."""
    by_sec: Dict[int, list] = {}
    for e in entries or []:
        si, mi = e.get("moodle_section_index"), e.get("moodle_module_index")
        wl = str(e.get("moodle_week_label") or "").strip()
        eid = str(e.get("id") or "")
        if si is None or mi is None or not wl or not eid:
            continue
        by_sec.setdefault(int(si), []).append((int(mi), eid, e, wl))
    out: Dict[str, List[str]] = {}
    for si in sorted(by_sec):
        items = sorted(by_sec[si], key=lambda t: (t[0], t[1]))
        i = 0
        while i < len(items):
            wl = items[i][3]
            group = []
            while i < len(items) and items[i][3] == wl:
                group.append(items[i])
                i += 1
            weeks = [(bl, part) for part in wl.split(" || ") for bl in [_week_blocks(part, ctx)] if bl]
            if not weeks:
                continue
            streams: Dict[str, list] = {}
            for _mi, eid, e, _wl in group:
                name = _moodle_label_text(e) + " " + str(e.get("title") or "")
                streams.setdefault(str(e.get("category") or ""), []).append((eid, name))
            for mats in streams.values():
                out.update(_align(mats, weeks, ctx))
    return out
