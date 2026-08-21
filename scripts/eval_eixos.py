"""Regua dos TRES eixos de atribuicao, pelo estado GRAVADO nos repos-tutor.

  BLOCO      eval_ground_truth (resolve_temporal_block vs ground_truth_<C>.csv)
  UNIDADE    computed_unit_slug vs verdade = unidade do bloco verdadeiro
             (ground_truth |><| gold_units) — NAO o scorer isolado de eval_entry_unit
  COBERTURA  coverage_units do MANIFEST vs material_gt_<C>.csv (eval_coverage.score)
             — eval_coverage.py <repo> <csv> le a camada de REFERENCIA e da 0/0 p/ material

Nao re-roda nenhum scorer: mede o que esta em disco (rode o reprocess antes).

Uso:
    python scripts/eval_eixos.py            # 5 cursos + totais
    python scripts/eval_eixos.py --course SO
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from eval_coverage import score as coverage_score  # noqa: E402
from eval_entry_unit import COURSES, GITHUB_DIR, _load_truth  # noqa: E402
from eval_ground_truth import (  # noqa: E402
    evaluate_ground_truth, load_block_period_map, load_labels_csv, load_pair_keys, load_predictions,
)
from src.builder.routing.resolver_apply import _is_material  # noqa: E402


def _coverage_pred(entry: dict) -> set:
    units = {str(u.get("unit_slug") or "").strip() for u in (entry.get("coverage_units") or [])}
    units.discard("")
    if not units:
        own = str(entry.get("computed_unit_slug") or "").strip()
        if own:
            units = {own}
    return units


def medir(sigla: str, repo_name: str) -> dict:
    repo = GITHUB_DIR / repo_name
    entries = json.loads((repo / "manifest.json").read_text(encoding="utf-8")).get("entries") or []
    by_id = {str(e.get("id")): e for e in entries}

    # BLOCO
    gt_csv = ROOT / "docs" / "reports" / f"ground_truth_{sigla}.csv"
    labels = load_labels_csv(gt_csv)
    # pair_keys: version-pairs colapsam em 1 unidade de pontuacao (regra do par),
    # igual ao eval_ground_truth CLI — sem isso o total sobe para 204.
    rep = evaluate_ground_truth(load_predictions(repo), labels, load_block_period_map(repo),
                                pair_keys=load_pair_keys(gt_csv))
    bloco = {"ok": rep["correct"], "n": rep["total"], "conf_err": rep["confident_wrong"],
             "fontes": {k: (v["correct"], v["wrong"]) for k, v in rep.get("sources", {}).items()}}

    # UNIDADE (gravada vs verdade = unidade do bloco verdadeiro)
    truth = _load_truth(sigla)
    ok = n = 0
    erros = []
    for eid, want in truth.items():
        e = by_id.get(eid)
        if not e or not _is_material(e):
            continue
        n += 1
        got = str(e.get("computed_unit_slug") or "").strip()
        if got == want:
            ok += 1
        else:
            erros.append(eid)
    unidade = {"ok": ok, "n": n, "erros": erros}

    # COBERTURA (manifest)
    gold = {}
    gt = ROOT / "docs" / "reports" / f"material_gt_{sigla}.csv"
    if gt.exists():
        with gt.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if str(row.get("scorable", "yes")).strip().lower() != "yes":
                    continue
                units = {p.strip() for p in str(row.get("gold_units") or "").split("|") if p.strip()}
                if units:
                    gold[row["entry_id"].strip()] = units
    cov = coverage_score(gold, {k: _coverage_pred(by_id[k]) for k in gold if k in by_id}) if gold else None
    cobertura = {"exact": cov["exact_set_match"], "n": cov["n"], "f1": cov["macro_f1"],
                 "sem_pred": cov["sem_predicao"]} if cov else None

    metodos = collections.Counter(str(e.get("temporal_block_method")) for e in entries
                                  if e.get("temporal_block_method"))
    pinos = sum(1 for e in entries if str(e.get("manual_timeline_block_id") or "").strip())
    return {"curso": sigla, "bloco": bloco, "unidade": unidade, "cobertura": cobertura,
            "metodos": dict(metodos), "pinos": pinos}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--course")
    args = ap.parse_args(argv[1:])
    alvos = {args.course.upper(): COURSES[args.course.upper()]} if args.course else COURSES

    tot = collections.Counter()
    cov_gold_all, cov_pred_all = {}, {}
    metodos = collections.Counter()
    print(f"{'curso':6}{'BLOCO':>10}{'conf-err':>9}{'UNIDADE':>10}{'COBERTURA':>12}{'F1':>6}{'pinos':>6}")
    for sigla, repo_name in alvos.items():
        r = medir(sigla, repo_name)
        b, u, c = r["bloco"], r["unidade"], r["cobertura"]
        tot["b_ok"] += b["ok"]; tot["b_n"] += b["n"]; tot["conf"] += b["conf_err"]
        tot["u_ok"] += u["ok"]; tot["u_n"] += u["n"]; tot["pinos"] += r["pinos"]
        metodos.update(r["metodos"])
        ctxt = f"{c['exact']}/{c['n']}" if c else "-"
        f1 = f"{c['f1']:.3f}" if c else "-"
        print(f"{sigla:6}{b['ok']:>4}/{b['n']:<5}{b['conf_err']:>9}{u['ok']:>5}/{u['n']:<4}{ctxt:>12}{f1:>6}{r['pinos']:>6}")
        if u["erros"]:
            print(f"       unidade errada: {', '.join(u['erros'][:8])}{' ...' if len(u['erros']) > 8 else ''}")
        # totais de cobertura agregados por (curso, id)
        if c:
            repo = GITHUB_DIR / repo_name
            by_id = {str(e.get("id")): e for e in json.loads((repo / "manifest.json").read_text(encoding="utf-8")).get("entries") or []}
            gt = ROOT / "docs" / "reports" / f"material_gt_{sigla}.csv"
            with gt.open(encoding="utf-8-sig", newline="") as fh:
                for row in csv.DictReader(fh):
                    units = {p.strip() for p in str(row.get("gold_units") or "").split("|") if p.strip()}
                    if units and str(row.get("scorable", "yes")).strip().lower() == "yes" and row["entry_id"] in by_id:
                        cov_gold_all[(sigla, row["entry_id"])] = units
                        cov_pred_all[(sigla, row["entry_id"])] = _coverage_pred(by_id[row["entry_id"]])
    cov = coverage_score(cov_gold_all, cov_pred_all) if cov_gold_all else None
    print("-" * 55)
    print(f"TOTAL  bloco {tot['b_ok']}/{tot['b_n']} ({tot['b_ok']/max(tot['b_n'],1):.1%}) conf-err {tot['conf']} | "
          f"unidade {tot['u_ok']}/{tot['u_n']} ({tot['u_ok']/max(tot['u_n'],1):.1%}) | "
          + (f"cobertura {cov['exact_set_match']}/{cov['n']} F1 {cov['macro_f1']:.3f} sem-pred {cov['sem_predicao']} | " if cov else "")
          + f"pinos {tot['pinos']}")
    print(f"metodos temporais: {dict(metodos.most_common())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
