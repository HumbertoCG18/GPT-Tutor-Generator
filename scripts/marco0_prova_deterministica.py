#!/usr/bin/env python3
"""MARCO 0 — prova READ-ONLY do disambiguator deterministico + ordinal-no-nome (MF).

Mede o PISO deterministico do motor (D8 TIER 1-2) contra a regua oficial
`docs/reports/ground_truth_MF.csv` (colapso de par igual ao eval_ground_truth):

  A   content-IDF janela-local (titulo+label+markdown), score cru
  A'  A com normalizacao por tamanho de assinatura (anti-sumidouro)
  C   A' + serie same-theme com restricao de MONOTONICIDADE (DP exato,
      sem peso magico): ordinais crescentes nao podem regredir de bloco.

Roteamento D6 (trabalho/prova/TDE) fica FORA do disambiguator — reportado a
parte (o motor real resolve por janela-de-prazo, que ja existe: assign_due).

O gate de margem (proxy do D4) marca FLAGGED — o remanescente de C e a ENTRADA
do MARCO 1 (voto LLM). Emite docs/reports/marco0_flagged_MF.json (uncommitted).

NAO muta manifest nem artefato de curso. So le e imprime.

Uso:  python scripts/marco0_prova_deterministica.py [--repo PATH] [--gold CSV]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_MF.csv"
FLAG_OUT = Path(__file__).resolve().parents[1] / "docs" / "reports" / "marco0_flagged_MF.json"

MARGIN_TAU = 0.25   # gate proxy D4 (calibracao fina = fase 2 do plano)
MD_CAP = 6000       # chars de markdown por material
D6_CATEGORIES = {"trabalhos", "provas"}
D6_SECTION_PREFIX = "TDE"

# Stems genericos que nao discriminam bloco (espelha trace_motor/_GENERIC_STEMS)
_GEN = {"introduc", "continua", "exercici", "revisao", "conteudo", "material",
        "aplicac", "apresent", "sobre", "parte", "exemplo", "usando", "aula", "para",
        "resposta", "solucao", "lista"}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return s.lower()


def _toks(s: str) -> set:
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(s or ""))  # camelCase antes do fold
    out = set()
    for t in re.split(r"[^a-z0-9]+", _fold(s)):
        if len(t) >= 3 and not t.isdigit() and t[:8] not in _GEN:
            out.add(t)
    return out


def _mlabel(e) -> str:
    ml = e.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else (ml or "")


def _md_text(repo: Path, e) -> str:
    for k in ("approved_markdown", "curated_markdown", "base_markdown"):
        rel = str(e.get(k) or "")
        p = repo / rel
        if rel and p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:MD_CAP]
            except OSError:
                pass
    return ""


class Motor:
    """Janela (card_block_map) + assinatura de bloco (topic + roteiro) + IDF local."""

    def __init__(self, repo: Path):
        self.repo = repo
        man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
        self.byid_entry = {}
        for e in man.get("entries") or []:
            self.byid_entry.setdefault(str(e.get("id")), e)
        self.cbm = self._load("course/.card_block_map.json")
        bi = self._load("course/.block_identity.json") or []
        self.u2d = {str(b.get("uuid")): str(b.get("display_id_last")) for b in bi}
        self.roteiro = (self._load("course/.lessons_index.json") or {}).get("by_date", {})
        tl = self._load("course/.timeline_index.json")
        blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
        self.blocks = sorted(blocks, key=lambda b: str(b.get("period_start") or ""))
        self.byid_block = {}
        for b in self.blocks:
            for k in (str(b.get("block_uuid") or ""), str(b.get("id") or "")):
                if k:
                    self.byid_block[k] = b

    def _load(self, rel: str):
        p = self.repo / rel
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}

    def disp(self, block) -> str:
        bid = str(block.get("id") or "")
        if bid.startswith("bloco-"):
            return bid
        return self.u2d.get(str(block.get("block_uuid") or bid), bid)

    def window(self, section: str) -> list:
        info = self.cbm.get(str(section or "").strip()) or {}
        win = [self.byid_block[str(x)] for x in (info.get("block_ids") or [])
               if str(x) in self.byid_block]
        return sorted(win, key=lambda b: str(b.get("period_start") or ""))

    def block_sig(self, b) -> set:
        sig = _toks(str(b.get("topic_text") or "") + " " + str(b.get("primary_topic_label") or ""))
        for s in b.get("sessions") or []:
            sig |= _toks(self.roteiro.get(str(s.get("date") or ""), ""))
        return sig

    def is_d6(self, e) -> bool:
        cat = str(e.get("category") or "")
        sec = str(e.get("source_section") or "")
        return cat in D6_CATEGORIES or sec.startswith(D6_SECTION_PREFIX)


def idf_scores(mat: set, win: list, sigs: list, len_norm: bool) -> list:
    m = len(win)
    df = defaultdict(int)
    for sig in sigs:
        for t in sig:
            df[t] += 1
    out = []
    for sig in sigs:
        s = sum(math.log(1.0 + m / df[t]) for t in (mat & sig))
        if len_norm and sig:
            s /= math.sqrt(len(sig))
        out.append(s)
    return out


def detect_series(rows, motor: Motor):
    """Serie same-theme: mesmo card + mesmo stem (nome sem digitos), >=2 ordinais."""
    groups = defaultdict(list)
    for r in rows:
        e = motor.byid_entry.get(r["id"])
        if not e or motor.is_d6(e):
            continue
        name = str(e.get("title") or r["id"])
        nums = re.findall(r"(\d+)", name)
        stem = re.sub(r"\d+", "", _fold(name)).strip()
        sec = str(e.get("source_section") or "").strip()
        if nums and stem and sec:
            groups[(sec, stem)].append((r["id"], int(nums[-1])))
    series = {}
    for key, members in groups.items():
        if len(members) >= 2 and len({o for _, o in members}) >= 2:
            ranked = [rid for rid, _o in sorted(members, key=lambda x: x[1])]
            series[key] = ranked
    return series


def monotone_dp(score_rows: list) -> list:
    """Atribuicao p_1<=...<=p_n maximizando a soma dos scores. Retorna indices."""
    n, m = len(score_rows), len(score_rows[0])
    NEG = float("-inf")
    dp = [[NEG] * m for _ in range(n)]
    par = [[0] * m for _ in range(n)]
    for p in range(m):
        dp[0][p] = score_rows[0][p]
    for r in range(1, n):
        best, bestp = NEG, 0
        for p in range(m):
            if dp[r - 1][p] > best:
                best, bestp = dp[r - 1][p], p
            dp[r][p] = score_rows[r][p] + best
            par[r][p] = bestp
    p = max(range(m), key=lambda x: dp[n - 1][x])
    out = [p]
    for r in range(n - 1, 0, -1):
        p = par[r][p]
        out.append(p)
    return out[::-1]


def collapse(results: dict, rows: list) -> tuple:
    by_unit = defaultdict(list)
    for r in rows:
        if r["id"] not in results:
            continue
        by_unit[r["pair_key"] or r["id"]].append(results[r["id"]]["correct"])
    total = len(by_unit)
    ok = sum(int(all(v)) for v in by_unit.values())
    return ok, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    args = ap.parse_args()
    repo, gold_path = Path(args.repo), Path(args.gold)

    motor = Motor(repo)
    rows = [r for r in csv.DictReader(open(gold_path, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    print(f"MARCO 0 — repo={repo.name}  gold={gold_path.name}  scorable={len(rows)}")

    d6_rows = [r for r in rows
               if motor.byid_entry.get(r["id"]) and motor.is_d6(motor.byid_entry[r["id"]])]
    d6_ids = {r["id"] for r in d6_rows}
    scope = [r for r in rows if r["id"] not in d6_ids]
    print(f"roteados D6 (trabalho/prova/TDE — fora do disambiguator): {len(d6_rows)}")

    series = detect_series(scope, motor)
    print(f"series same-theme: {len(series)} (cobrindo {sum(len(v) for v in series.values())} materiais)")

    cfgs = ("A", "A'", "C")
    res = {c: {} for c in cfgs}
    cache = {}
    no_window = 0
    for r in scope:
        rid, true = r["id"], r["true_block_id"]
        e = motor.byid_entry.get(rid)
        win = motor.window(e.get("source_section")) if e else []
        base = {"id": rid, "true": true, "material": r["material"]}
        if not e or not win:
            no_window += 1
            pred = r["computed_block_id"] or ""  # funil = piso (D9)
            for c in cfgs:
                res[c][rid] = {**base, "pred": pred, "correct": pred == true,
                               "mode": "sem-janela(funil)", "flag": not pred}
            continue
        sigs = [motor.block_sig(b) for b in win]
        mat = _toks(str(e.get("title") or "") + " " + _mlabel(e) + " " + _md_text(repo, e))
        raw = idf_scores(mat, win, sigs, len_norm=False)
        ln = idf_scores(mat, win, sigs, len_norm=True)
        cache[rid] = {"win": win, "ln": ln}
        for c, sc in (("A", raw), ("A'", ln)):
            order = sorted(range(len(win)), key=lambda i: sc[i], reverse=True)
            s1 = sc[order[0]]
            s2 = sc[order[1]] if len(order) > 1 else 0.0
            flag = (len(win) > 1) and (s1 <= 0 or (s1 - s2) / max(s1, 1e-9) < MARGIN_TAU)
            pred = motor.disp(win[order[0]])
            res[c][rid] = {**base, "pred": pred, "correct": pred == true, "flag": flag,
                           "mode": "janela-1" if len(win) == 1 else f"multi-{len(win)}",
                           "janela": [motor.disp(b) for b in win]}
        res["C"][rid] = dict(res["A'"][rid])  # serie sobrescreve abaixo

    # Config C: DP monotone por serie (mesma janela p/ todos os membros do card)
    for key, ranked in series.items():
        members = [rid for rid in ranked if rid in cache]
        if len(members) < 2:
            continue
        win = cache[members[0]]["win"]
        if any(cache[rid]["win"] != win for rid in members) or len(win) < 2:
            continue
        picks = monotone_dp([cache[rid]["ln"] for rid in members])
        for rid, p in zip(members, picks):
            v = res["C"][rid]
            v["pred"] = motor.disp(win[p])
            v["correct"] = v["pred"] == v["true"]
            v["mode"] += "+serieDP"

    # baseline temporal na MESMA regua (sanidade)
    res_t = {r["id"]: {"correct": (r["temporal_block_id"] or r["computed_block_id"]) == r["true_block_id"]}
             for r in rows}

    bar = "=" * 74
    print(f"\nsem-janela (funil): {no_window}")
    print(f"\n{bar}\nPLACAR (unidades pos-colapso; escopo disambiguator = {len(scope)} linhas)\n{bar}")
    ok_t, tot_t = collapse(res_t, rows)
    print(f"  temporal baseline (66 un, com D6)     : {ok_t}/{tot_t} = {ok_t / tot_t * 100:.1f}%")
    ok_ts, tot_ts = collapse({k: v for k, v in res_t.items() if k not in d6_ids}, scope)
    print(f"  temporal baseline (escopo disamb.)    : {ok_ts}/{tot_ts} = {ok_ts / tot_ts * 100:.1f}%")
    for c in cfgs:
        ok, tot = collapse(res[c], scope)
        multi = [v for v in res[c].values() if v["mode"].startswith("multi")]
        mok = sum(v["correct"] for v in multi)
        print(f"  Config {c:2} {'(cru)' if c == 'A' else '(len-norm)' if c == chr(65) + chr(39) else '(+serieDP)':10}"
              f"                : {ok}/{tot} = {ok / tot * 100:.1f}%   multi: {mok}/{len(multi)}")

    print(f"\n{bar}\nSERIES — caso a caso (true / A' / C)\n{bar}")
    for key, ranked in sorted(series.items()):
        for rid in ranked:
            if rid not in res["A'"]:
                continue
            a, c = res["A'"][rid], res["C"][rid]
            print(f"  [{key[1][:26]:26}] true={a['true']:9} A'={a['pred']:9}{'ok' if a['correct'] else 'X '} "
                  f"C={c['pred']:9}{'ok' if c['correct'] else 'X '}  {a['material'][:34]}")

    flagged = [v for v in res["C"].values() if v["flag"]]
    err_blind = [v for v in res["C"].values() if not v["correct"] and not v["flag"]]
    print(f"\n{bar}\nFLAGGED da Config C (entrada MARCO 1): {len(flagged)}  "
          f"(errados dentro: {sum(1 for v in flagged if not v['correct'])})\n{bar}")
    for v in flagged:
        print(f"  {v['id'][:52]:52} pred={v['pred']:9} [{'ok' if v['correct'] else 'ERRA'}] "
              f"janela={','.join(v.get('janela', []))}")
    print(f"\nconfiante-e-ERRADO fora do flag (cego pro LLM): {len(err_blind)}")
    for v in err_blind:
        print(f"  {v['id'][:56]:56} pred={v['pred']} true={v['true']}")
    print(f"\nD6-roteados (fora desta prova; motor real usa janela-de-prazo assign_due):")
    for r in d6_rows:
        t = r["temporal_block_id"] or r["computed_block_id"]
        print(f"  {r['id'][:44]:44} true={r['true_block_id']} temporal-hoje={t or '-'}")

    FLAG_OUT.write_text(json.dumps(flagged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nflagged salvo (uncommitted): {FLAG_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
