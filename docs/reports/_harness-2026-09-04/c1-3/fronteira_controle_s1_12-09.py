"""CONTROLE: o piso global de winner_score (REFUTADO 5x) como braco de comparacao, nao como proposta.

Se a familia exact_hits / peso_doador (rho de Spearman +0,88 a +0,97 com s1) so reproduz o piso
refutado, o piso deve aparecer NA fronteira. Se a fronteira domina o piso, a familia e outra coisa.
Varre s1 < x em 25 pontos e cruza com a fronteira ja medida.
"""
import runpy
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent   # 12/09: saida no proprio harness (era o scratchpad da sessao)
sys.stdout = open(OUT / "_tmp_sink2.txt", "w", encoding="utf-8")
G = runpy.run_path(str(OUT / "fronteira_fronteira_12-09.py"))
sys.stdout = sys.__stdout__
CRU, PROD, ponto, pts = G["CRU"], G["PROD"], G["ponto"], G["pts"]
front = [p for p in pts if not p["dominado"]]

PISOS = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 20, 25, 30, 40, 60]
print("CONTROLE — piso global de winner_score (s1 < x), CRU:")
print(f"{'x':>6} {'C':>4} {'E':>3} {'entrega':>8} {'precisao':>9} {'dominado pela fronteira?':>26}")
ctrl = []
for x in PISOS:
    f = lambda r, x=x: r["s1"] < x  # noqa: E731
    p = ponto(CRU, f)
    dom = [q for q in front if q["cru"]["C"] >= p["C"] and q["cru"]["precisao"] >= p["precisao"]
           and (q["cru"]["C"] > p["C"] or q["cru"]["precisao"] > p["precisao"])]
    ctrl.append((x, p, dom))
    d = f"sim: {dom[0]['nome'][:30]}" if dom else "NAO (esta na fronteira)"
    print(f"{x:>6} {p['C']:>4} {p['E']:>3} {p['entrega']:>7.1%} {p['precisao']:>8.1%} {d:>26}")

print()
print("Comparacao direta nos pontos de mesma ENTREGA (piso de s1 x regra medida):")
for q in front:
    if q["nome"] == "(nenhuma)":
        continue
    cand = [(x, p) for x, p, _ in ctrl if p["C"] >= q["cru"]["C"]]
    if not cand:
        continue
    x, p = min(cand, key=lambda t: t[1]["C"])
    print(f"  {q['nome'][:44]:44} C {q['cru']['C']:>3} prec {q['cru']['precisao']:>6.1%}  |  "
          f"piso s1<{x:<5} C {p['C']:>3} prec {p['precisao']:>6.1%}  |  "
          f"{'regra GANHA' if q['cru']['precisao'] > p['precisao'] else 'piso empata/ganha'}")
