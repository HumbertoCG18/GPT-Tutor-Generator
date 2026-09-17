#!/usr/bin/env python3
"""Diff before-pinfix vs manifesto-novo. Critério de LIMPO FIXADO ANTES do resultado.

LIMPO  <=>  nenhum material ALÉM de `artigo-usando-agrupamento` muda QUALQUER um de:
            {computed_block_id, temporal_block_id, manual_timeline_block_id}.
IGNORA:     updated_at, logs, ordem, serialização, campos não-bloco.
SUJO:       qualquer campo-de-bloco de QUALQUER outro material muda = CASCATEAMENTO de pin.

O critério está no código ANTES do diff rodar — não se racionaliza mudança depois de ver.
READ-ONLY. Roda DEPOIS de [deletar pin do artigo + Reprocessar].

Uso:  python scripts/diff_pinfix_IA.py
"""
from __future__ import annotations

import json
import os
import sys

# stdout UTF-8: console cp1252 (Windows) crasha em char fora do Latin-1 (ex.: titulo TCC).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO = r"C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor"
BEFORE = os.path.join(REPO, "manifest.json.before-pinfix.20260626.bak")
AFTER = os.path.join(REPO, "manifest.json")
ART = "artigo-usando-agrupamento"
BLOCK_FIELDS = ("computed_block_id", "temporal_block_id", "manual_timeline_block_id")


def load(p):
    return {str(e.get("id")): e for e in json.load(open(p, encoding="utf-8")).get("entries", [])}


def disp(x, u2d):
    s = str(x or "").strip()
    return u2d.get(s, s) if s else "(vazio)"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not os.path.isfile(BEFORE):
        print(f"FALTA snapshot before: {BEFORE}"); sys.exit(2)
    bi = json.load(open(os.path.join(REPO, "course/.block_identity.json"), encoding="utf-8"))
    u2d = {str(b.get("uuid")): str(b.get("display_id_last")) for b in bi}

    before, after = load(BEFORE), load(AFTER)
    bar = "=" * 72
    print(bar); print("DIFF PIN-FIX  (before-pinfix vs manifesto-novo)  [critério pré-fixado]"); print(bar)

    # entries adicionados/removidos (esperado: nenhum)
    added = set(after) - set(before)
    removed = set(before) - set(after)
    if added or removed:
        print(f"  ⚠ entries ADD={sorted(added)} REMOVED={sorted(removed)} (esperado: vazio)")

    changes = {}  # id -> [(campo, antes, depois)]
    for eid in set(before) & set(after):
        for f in BLOCK_FIELDS:
            b, a = before[eid].get(f), after[eid].get(f)
            if str(b or "") != str(a or ""):
                changes.setdefault(eid, []).append((f, disp(b, u2d), disp(a, u2d)))

    # artigo (esperado: muda)
    print("\n[ARTIGO — esperado mudar]")
    if ART in changes:
        for f, b, a in changes[ART]:
            print(f"  {f:28} {b:10} -> {a}")
    else:
        print("  NENHUMA mudança no artigo — fix NÃO aplicou (clicou errado / sem rebuild?).")

    # outros (esperado: NENHUM)
    others = {k: v for k, v in changes.items() if k != ART}
    print("\n[OUTROS materiais com campo-de-bloco mudado — esperado: NENHUM]")
    if others:
        for eid, ch in others.items():
            for f, b, a in ch:
                print(f"  CASCATA {eid[:40]:40} {f:24} {b:10} -> {a}")
    else:
        print("  nenhum. (sem cascateamento)")

    # veredito
    print("\n" + bar)
    art_moved = ART in changes
    clean = art_moved and not others and not added and not removed
    if clean:
        print("VEREDITO: LIMPO ✓  — só artigo mudou. Loop medir→achar→consertar→re-medir validado.")
        print("  Próximo: re-eval (i+ii) — eval_ground_truth + classify_discriminant.")
    elif not art_moved:
        print("VEREDITO: FIX NÃO APLICOU — artigo não mudou. Revert do snapshot se quiser, re-tenta o clique.")
    else:
        print("VEREDITO: SUJO ✗  — CASCATEAMENTO. Outro material moveu de bloco. PARA, não confia em conserto.")
    print(bar)
    sys.exit(0 if clean else 1)


if __name__ == "__main__":
    main()
