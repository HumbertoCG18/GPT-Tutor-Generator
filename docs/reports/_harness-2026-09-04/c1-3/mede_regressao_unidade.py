"""Diff de UNIDADE e SUBUNIDADE por material entre tres estados de cada tutor: A = ultimo commit ate 08/09 (antes dos rollouts
de 11/09), B = HEAD do tutor (pre-correcao) e C = arvore de trabalho (corrigido). Gold: `_load_truth` (unidade) e
`subunit_gt_<sig>.csv` (subunidade). Nasceu em 12/09 para o gate "sem regressao em bloco e unidade" da Fase 1, que os rollouts de
11/09 nao mediram na unidade. 0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/mede_regressao_unidade.py [SIGLA ...]"""
import csv
import json
import subprocess
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
sys.path.insert(0, str(GEN / "scripts"))
from eval_entry_unit import _load_truth  # noqa: E402

TUTORES = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
           "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor",
           "FR": "Fundamentos-de-Redes-Tutor", "LR": "Laboratorio-de-Redes-Tutor"}


def git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, encoding="utf-8").stdout


def manifest(repo, ref):
    txt = (repo / "manifest.json").read_text(encoding="utf-8") if ref is None else git(repo, "show", f"{ref}:manifest.json")
    return {e["id"]: e for e in json.loads(txt)["entries"]}


def gold_sub(sig):
    p = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    if not p.exists():
        return {}
    out = {}
    for r in csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
        if r["scorable"] == "yes":
            out[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
    return out


def veredito(antes, depois, gold):
    if gold is None:
        return "sem gold"
    ok_a, ok_d = antes in gold, depois in gold
    return "PIOROU" if ok_a and not ok_d else "melhorou" if ok_d and not ok_a else "igual p/ gold"


def diff(sig, ref_a, ref_b, rot):
    repo = GH / TUTORES[sig]
    a, b = manifest(repo, ref_a), manifest(repo, ref_b)
    gu, gs = _load_truth(sig), gold_sub(sig)
    tot = {"unidade": [0, 0, 0], "subunidade": [0, 0, 0]}  # mudou, piorou, melhorou
    for eid in b:
        if eid not in a:
            continue
        for eixo, campo, gold in (("unidade", "computed_unit_slug", {gu[eid]} if eid in gu else None),
                                  ("subunidade", "computed_subunit_slug", gs.get(eid))):
            va, vb = a[eid].get(campo) or "", b[eid].get(campo) or ""
            if va == vb:
                continue
            v = veredito(va, vb, gold)
            tot[eixo][0] += 1; tot[eixo][1] += v == "PIOROU"; tot[eixo][2] += v == "melhorou"
            print(f"    {sig:3} {eixo:10} {eid[:44]:44} {va[:22] or '(vazio)':22} -> {vb[:22] or '(vazio)':22} {v}")
    print(f"  {sig:3} {rot}: unidade mudou {tot['unidade'][0]} (piorou {tot['unidade'][1]}, melhorou {tot['unidade'][2]}) · "
          f"subunidade mudou {tot['subunidade'][0]} (piorou {tot['subunidade'][1]}, melhorou {tot['subunidade'][2]})", flush=True)
    return tot


sigs = sys.argv[1:] or list(TUTORES)
for sig in sigs:
    repo = GH / TUTORES[sig]
    log = git(repo, "log", "--format=%h", "--until=2026-09-09").splitlines()
    ref_a = log[0] if log else None
    print(f"== {sig}: A={ref_a} (ultimo commit ate 08/09) · B=HEAD · C=arvore de trabalho")
    diff(sig, ref_a, "HEAD", "A -> B (07/09 -> pre-correcao)")
    diff(sig, "HEAD", None, "B -> C (pre -> corrigido)")
    diff(sig, ref_a, None, "A -> C (07/09 -> corrigido)")
