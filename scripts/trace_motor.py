#!/usr/bin/env python3
"""Trace READ-ONLY do motor de atribuição proposto (WindowProvider + Disambiguator).

Para cada material de uma seção com card-window, mostra: a janela (card_block_map),
os tópicos dos blocos, o score content↔topic por bloco, o vencedor, a margem e a
band/flag resultante. NÃO muta manifest — só lê e imprime.

LIMITAÇÃO (conservador): tokenizer cru — sem IDF (token raro deveria pesar mais),
sem split camelCase, roteiro entra parcial. O motor real é MAIS afiado; este trace
é um PISO. Serve pra visualizar o fluxo e a higiene-soft de kind, não pra medir.

Uso:  python scripts/trace_motor.py [REPO_ROOT] [secao1] [secao2] ...
      (sem args -> Metodos-Formais-Tutor, seções com janela >1 bloco)
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console cp1252 -> utf-8

DEFAULT_REPO = r"C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor"

# Stems genéricos: não discriminam bloco (espelha anchor_placement._GENERIC_STEMS).
_GEN = {"introduc", "continua", "exercici", "revisao", "conteudo", "material",
        "aplicac", "apresent", "sobre", "parte", "exemplo", "usando", "aula", "para"}


def _load(root, p):
    fp = os.path.join(root, p)
    return json.load(open(fp, encoding="utf-8")) if os.path.isfile(fp) else {}


def _toks(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return {t for t in re.split(r"[^a-z0-9]+", s) if len(t) >= 4 and t[:8] not in _GEN}


def _mlabel(e):
    ml = e.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else (ml or "")


def trace_section(card, ents, cbm, byid, u2d, bydate, nmax=4):
    def disp(x):
        return u2d.get(str(x), str(x))

    def btoks(b):
        tk = _toks(b.get("topic_text") or b.get("primary_topic_label") or "")
        for s in b.get("sessions") or []:
            tk |= _toks(bydate.get(str(s.get("date") or ""), ""))
        return tk

    info = cbm.get(card, {})
    win = [byid[str(x)] for x in (info.get("block_ids") or []) if str(x) in byid]
    print(f"\n{'=' * 76}\nSEÇÃO: {card}   [card-window {info.get('source')}, {len(win)} blocos]")
    for b in win:
        print(f"    {disp(b.get('block_uuid') or b.get('id')):9} "
              f"({str(b.get('kind') or ''):13}) "
              f"topic='{str(b.get('topic_text') or b.get('primary_topic_label') or '')[:38]}'")
    if not win:
        print("    (sem card-window -> resíduo sem-janela: scorer + FLAG)")
        return
    mats = [x for x in ents if str(x.get("source_section") or "").strip() == card][:nmax]
    for e in mats:
        sig = _toks(str(e.get("title") or "") + " " + str(_mlabel(e)))
        sc = sorted(((len(sig & btoks(b)), disp(b.get("block_uuid") or b.get("id")),
                      str(b.get("kind") or "")) for b in win), reverse=True)
        best = sc[0]
        run = sc[1] if len(sc) > 1 else (0, "-", "-")
        margin = best[0] - run[0]
        if best[0] == 0:
            band = "SILÊNCIO -> scorer-bounded + FLAG"
        elif margin >= 1:
            band = "ALTA (ancora)"
        else:
            band = "BAIXA + FLAG (empate/ambíguo)"
        print(f"\n  - \"{str(e.get('title'))[:50]}\"")
        print(f"      scores: " + " | ".join(f"{bid}={o}" for o, bid, _k in sc))
        print(f"      => vence {best[1]} margem={margin} -> {band}")


def main(argv):
    root = argv[0] if argv and not argv[0].startswith("-") else DEFAULT_REPO
    sections = [a for a in argv[1:] if not a.startswith("-")]
    ents = (_load(root, "manifest.json") or {}).get("entries") or []
    cbm = _load(root, "course/.card_block_map.json")
    bi = _load(root, "course/.block_identity.json")
    u2d = {str(b.get("uuid")): str(b.get("display_id_last")) for b in (bi or [])}
    bydate = (_load(root, "course/.lessons_index.json") or {}).get("by_date", {})
    tl = _load(root, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    byid = {}
    for b in blocks:
        for k in (str(b.get("block_uuid") or ""), str(b.get("id") or "")):
            if k:
                byid[k] = b
    if not sections:
        # auto: seções cuja card-window tem >1 bloco (os casos interessantes)
        sections = [c for c, e in cbm.items() if len(e.get("block_ids") or []) > 1]
    print(f"REPO: {os.path.basename(root)}  | seções traçadas: {len(sections)}")
    for c in sections:
        trace_section(c, ents, cbm, byid, u2d, bydate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
