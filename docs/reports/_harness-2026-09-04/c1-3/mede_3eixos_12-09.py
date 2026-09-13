"""Mede os 3 EIXOS num conjunto de repos-tutor (produto ou copia), lendo so o manifest. 0 chamadas.

Mesma regua do `calibra_fila_como_regua.py`, parametrizada pela raiz e com a ACURACIA TOTAL ao lado da precisao do
confiante (12/09, decisao do astra: a meta de 90% e cobrada sobre TODOS os materiais avaliaveis — abster nao tira o
material do denominador).

  bloco       `ground_truth_<sig>.csv` (true_block_id), via manual_timeline_block_id > temporal_block_id
  unidade     `eval_entry_unit.carrega_regua_unidade` (regua CURRICULAR, tupla de unidades aceitas)
  subunidade  `subunit_gt_<sig>.csv`, ACEITO (primario + extras) e PRIMARIO

Uso: python -B mede_3eixos_12-09.py --raiz "C:/.../.motor3eixos" [--cursos TCC,SO]
"""
import argparse
import collections
import csv as _csv
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import carrega_regua_unidade  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC", "CG"}   # cursos com regua de unidade
EIXOS = ("bloco", "unidade", "subunidade", "subunid(prim)")


def golds(sig):
    p = GEN / "docs/reports" / f"ground_truth_{sig}.csv"
    gb = load_labels_csv(p) if p.exists() else {}
    gu = carrega_regua_unidade(sig) if sig in UNI else {}
    p = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    gs, gsp = {}, {}
    if p.exists():
        for r in _csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
            if r["scorable"] == "yes":
                gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
                gsp[r["entry_id"]] = {r["gold_subunit"]}
    return gb, gu, gs, gsp


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True, help="pasta que contem os <Tutor>/ (produto ou copia)")
    ap.add_argument("--cursos", default="")
    a = ap.parse_args(argv)
    raiz = Path(a.raiz)
    sigs = [s.strip() for s in a.cursos.split(",") if s.strip()] or list(NOMES)

    M = {e: collections.Counter() for e in EIXOS}
    POR_CURSO = collections.defaultdict(lambda: collections.Counter())
    for sig in sigs:
        root = raiz / NOMES[sig]
        if not (root / "manifest.json").exists():
            print(f"  (pulado: {sig} nao existe em {raiz})")
            continue
        man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
        ti = {}
        tp = root / "course/.timeline_index.json"
        if tp.exists():
            for b in json.loads(tp.read_text(encoding="utf-8"))["blocks"]:
                ti[b["block_uuid"]] = b["id"]
                ti[b["id"]] = b["id"]
        gb, gu, gs, gsp = golds(sig)
        for e in man:
            eid = e["id"]
            na_fila = revisar_de(e) in ("duvida", "mudou")
            cert = {}
            if eid in gb:
                cert["bloco"] = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "") == gb[eid]
            if eid in gu:
                cert["unidade"] = str(e.get("computed_unit_slug") or "") in gu[eid]
            if eid in gs:
                cert["subunidade"] = str(e.get("computed_subunit_slug") or "") in gs[eid]
            if eid in gsp:
                cert["subunid(prim)"] = str(e.get("computed_subunit_slug") or "") in gsp[eid]
            for eixo, ok in cert.items():
                for alvo in (M[eixo], POR_CURSO[(sig, eixo)]):
                    alvo["n"] += 1
                    alvo["certo"] += ok
                    if na_fila:
                        alvo["fila"] += 1
                        alvo["fila_certo"] += ok
                    else:
                        alvo["conf"] += 1
                        alvo["conf_certo"] += ok

    print(f"{'eixo':15} {'n':>5} {'ACURACIA TOTAL':>18} {'precisao do confiante':>24} {'cobertura':>11} {'erros conf':>11}")
    for eixo in EIXOS:
        c = M[eixo]
        if not c["n"]:
            continue
        print(f"{eixo:15} {c['n']:>5} {c['certo']:>6}/{c['n']:<5} {c['certo']/c['n']:>6.1%} "
              f"{c['conf_certo']:>9}/{c['conf']:<5} {c['conf_certo']/max(1,c['conf']):>7.1%} "
              f"{c['conf']/c['n']:>10.1%} {c['conf']-c['conf_certo']:>11}")
    print()
    print("POR CURSO (acuracia total)")
    print(f"{'curso':6} " + " ".join(f"{e:>18}" for e in EIXOS))
    for sig in sigs:
        linha = f"{sig:6} "
        for eixo in EIXOS:
            c = POR_CURSO[(sig, eixo)]
            linha += f" {c['certo']:>4}/{c['n']:<4} {c['certo']/c['n']:>6.1%} " if c["n"] else f" {'-':>16} "
        print(linha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
