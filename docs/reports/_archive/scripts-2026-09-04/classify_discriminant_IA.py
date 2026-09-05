#!/usr/bin/env python3
"""Classifica os 33 scorable em DISCRIMINANTE vs TRIVIAL por regra GEOMETRICA fixa.

CEGO AO RESULTADO (anti-circularidade): a classe e decidida SO pela geometria
data-vs-span, NUNCA por acerto/erro. So DEPOIS de classificar conta-se acerto.

Regra: material e DISCRIMINANTE se mover data_real +-1 AULA-SARC-adjacente MUDA o
bloco (a aula anterior OU a proxima no cronograma real cai em bloco != true_block).
TRIVIAL se ambas as vizinhas caem no mesmo bloco (meio de span largo / monstro).

"+-1 sessao" = +-1 AULA-SARC (cronograma real), NAO +-1 dia de calendario. A escolha
e explicita; o script reporta qualquer material cuja classe MUDE entre as duas
definicoes (pra "sessao" nao ser decisao escondida que move a regua).

READ-ONLY. Nada commitado.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import date, timedelta

# stdout UTF-8: console cp1252 (Windows) crasha em char fora do Latin-1 (ex.: titulo TCC).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO = r"C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor"
CSV = r"C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/ground_truth_IA.csv"


def loadj(p):
    return json.load(open(os.path.join(REPO, p), encoding="utf-8"))


def iso(dd_mm):
    d, m = dd_mm.split("/")
    return f"2026-{int(m):02d}-{int(d):02d}"


def to_date(dd_mm):
    d, m = dd_mm.split("/")
    return date(2026, int(m), int(d))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    # blocos -> spans [inicio, proximo inicio)
    tl = loadj("course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else tl.get("blocks", [])
    starts = sorted([(b.get("id"), b.get("period_start")) for b in blocks], key=lambda x: x[1])

    def block_for(d_iso):
        cur = None
        for bid, st in starts:
            if st <= d_iso:
                cur = bid
            else:
                break
        return cur

    # sessoes AULA-SARC academicas do syllabus (exclui suspensao/evento/feriado)
    syl = json.load(open(os.path.expandvars(r"%APPDATA%/GPTTutorGenerator/subjects.json"),
                         encoding="utf-8"))["Inteligencia Artificial"]["syllabus"]
    sessions, excluded = set(), []
    for ln in syl.splitlines():
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 8 and re.match(r"\d{2}/\d{2}/2026", parts[3] or ""):
            dt = parts[3][:5]
            desc, act = (parts[5] or "").lower(), (parts[6] or "").lower()
            nonacad = ("suspens" in desc) or ("es day" in desc) or ("evento" in act) or ("feriado" in act)
            if nonacad:
                excluded.append((dt, parts[5], parts[6]))
            else:
                sessions.add(dt)
    sess = sorted(sessions, key=iso)
    sess_iso = [iso(s) for s in sess]

    def neighbors_session(d_iso):
        prev = max([s for s in sess_iso if s < d_iso], default=None)
        nxt = min([s for s in sess_iso if s > d_iso], default=None)
        return prev, nxt

    def neighbors_calendar(d_iso):
        y, m, d = map(int, d_iso.split("-"))
        base = date(y, m, d)
        return (base - timedelta(days=1)).isoformat(), (base + timedelta(days=1)).isoformat()

    bar = "=" * 74
    print(bar); print("SESSOES AULA-SARC usadas (academicas; +-1 sessao anda nesta lista)"); print(bar)
    print("  " + "  ".join(sess))
    print(f"  EXCLUIDAS (nao-aula): {[f'{d}({desc[:14]})' for d,desc,act in excluded]}")

    # 33 scorable do CSV
    rows = [r for r in csv.DictReader(open(CSV, encoding="utf-8")) if r["id"] and r["true_block_id"]]

    def classify(d_iso, true_block, neigh_fn):
        p, n = neigh_fn(d_iso)
        bp = block_for(p) if p else true_block
        bn = block_for(n) if n else true_block
        disc = (bp != true_block) or (bn != true_block)
        why = []
        if bp != true_block:
            why.append(f"prev {p[5:]}→{bp}")
        if bn != true_block:
            why.append(f"next {n[5:]}→{bn}")
        return disc, "; ".join(why)

    disc_rows, triv_rows, divergence = [], [], []
    for r in rows:
        dr = r["data_real"]
        if not dr:
            triv_rows.append((r, "sem data_real (subt-single, meio de monstro)"))
            continue
        d_iso = iso(dr)
        tb = r["true_block_id"]
        ds, why_s = classify(d_iso, tb, neighbors_session)
        dc, _ = classify(d_iso, tb, neighbors_calendar)
        if ds != dc:
            divergence.append((r, ds, dc))
        (disc_rows if ds else triv_rows).append((r, why_s if ds else "vizinhas-sessao no mesmo bloco"))

    # --- DISCRIMINANTES enumerados (SEM contagem antes) ---
    print("\n" + bar); print("DISCRIMINANTES (regra geometrica ±1 aula-SARC; cega ao acerto)"); print(bar)
    for r, why in disc_rows:
        print(f"  {r['id'][:44]:44} | true {r['true_block_id']:8} | data_real {r['data_real']:5} | {why}")

    print("\n" + bar); print("TRIVIAIS (vizinhas no mesmo bloco)"); print(bar)
    for r, why in triv_rows:
        print(f"  {r['id'][:44]:44} | true {r['true_block_id']:8} | data_real {r['data_real'] or '-':5} | temporal {r['temporal_block_id']}")

    if divergence:
        print("\n" + bar); print("DIVERGENCIA ±1-sessao vs ±1-dia-calendario (a escolha MOVE a classe)"); print(bar)
        for r, ds, dc in divergence:
            print(f"  {r['id'][:44]:44} | data_real {r['data_real']} | sessao={'DISC' if ds else 'triv'} calendario={'DISC' if dc else 'triv'}")
    else:
        print("\n(±1-sessao e ±1-dia-calendario classificam IGUAL — escolha nao moveu nada.)")

    # --- SO AGORA: acerto/erro DENTRO da classe discriminante ---
    print("\n" + bar); print("ACURACIA POR CLASSE (contada DEPOIS da classificacao geometrica)"); print(bar)
    def acc(rows_):
        ok = sum(1 for r, _ in rows_ if r["true_block_id"] == r["temporal_block_id"])
        return ok, len(rows_)
    od, nd = acc(disc_rows)
    ot, nt = acc(triv_rows)
    print(f"  DISCRIMINANTE : {od}/{nd}" + (f" ({100*od/nd:.0f}%)" if nd else ""))
    print(f"  TRIVIAL       : {ot}/{nt}" + (f" ({100*ot/nt:.0f}%)" if nt else "") + "   <- inflado-monstro")
    print(f"  AGREGADO      : {od+ot}/{nd+nt}" + (f" ({100*(od+ot)/(nd+nt):.0f}%)" if (nd+nt) else "") + "   <- a taxa do monstro, nao do sistema")


if __name__ == "__main__":
    main()
