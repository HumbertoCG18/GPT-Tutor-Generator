"""Checagem de sanidade do fronteira_sinais_12-09.csv contra a regua congelada de 12/09 (ESTADO MEDIDO do brief)."""
import csv
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent   # 12/09: saida no proprio harness (era o scratchpad da sessao)
rows = list(csv.DictReader((OUT / "fronteira_sinais_12-09.csv").open(encoding="utf-8-sig")))
print("linhas:", len(rows), "| fora do escopo:", sum(int(r["fora_do_escopo"]) for r in rows))

ESPERADO = {"cru": dict(n=251, aceito=147, prim=105, conf=190, conf_ac=113, err=77, fila=61, fila_ac=34),
            "produto": dict(n=251, aceito=224, prim=186, conf=193, conf_ac=178, err=15, fila=58, fila_ac=46)}
for reg in ("cru", "produto"):
    rs = [r for r in rows if r["regime"] == reg]
    conf = [r for r in rs if r["confiante"] == "1"]
    fila = [r for r in rs if r["confiante"] == "0"]
    got = dict(n=len(rs), aceito=sum(int(r["aceito"]) for r in rs), prim=sum(int(r["primario"]) for r in rs),
               conf=len(conf), conf_ac=sum(int(r["aceito"]) for r in conf),
               err=sum(1 for r in conf if r["aceito"] == "0"),
               fila=len(fila), fila_ac=sum(int(r["aceito"]) for r in fila))
    ok = got == ESPERADO[reg]
    print(f"{reg:8} {got}  {'OK' if ok else 'DIVERGE de ' + str(ESPERADO[reg])}")
    assert ok, reg

print()
print("rota x (confiante,aceito) no CRU:")
cru = [r for r in rows if r["regime"] == "cru"]
c = Counter((r["rota"], r["confiante"], r["aceito"]) for r in cru)
for k in sorted(c):
    print("  ", k, c[k])
print()
print("rota x (confiante,aceito) no PRODUTO:")
pr = [r for r in rows if r["regime"] == "produto"]
c = Counter((r["rota"], r["confiante"], r["aceito"]) for r in pr)
for k in sorted(c):
    print("  ", k, c[k])
print()
print("vazios confiantes:", {reg: sum(1 for r in rows if r["regime"] == reg and r["confiante"] == "1" and r["vazio"] == "1") for reg in ("cru", "produto")})
print("por curso (cru): conf/n, certos, erros")
for sig in ("MF", "SO", "IA", "ES2", "TCC", "CG", "FR"):
    rs = [r for r in cru if r["curso"] == sig]
    cf = [r for r in rs if r["confiante"] == "1"]
    print(f"  {sig:4} n={len(rs):3} conf={len(cf):3} C={sum(int(r['aceito']) for r in cf):3} E={sum(1 for r in cf if r['aceito']=='0'):3} Q={len(rs)-len(cf):3}")
print("por curso (produto):")
for sig in ("MF", "SO", "IA", "ES2", "TCC", "CG", "FR"):
    rs = [r for r in pr if r["curso"] == sig]
    cf = [r for r in rs if r["confiante"] == "1"]
    print(f"  {sig:4} n={len(rs):3} conf={len(cf):3} C={sum(int(r['aceito']) for r in cf):3} E={sum(1 for r in cf if r['aceito']=='0'):3} Q={len(rs)-len(cf):3}")
