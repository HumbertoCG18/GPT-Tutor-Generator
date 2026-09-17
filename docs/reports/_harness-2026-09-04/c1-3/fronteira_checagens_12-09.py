"""Checagens finais: (a) os novos eixos sao o winner_score refutado disfarcado? (b) o que as regras
que NAO regridem o produto disparam no produto; (c) o preco medido do piso de 80% do astra."""
import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent   # 12/09: saida no proprio harness (era o scratchpad da sessao)
ROWS = list(csv.DictReader((OUT / "fronteira_sinais_12-09.csv").open(encoding="utf-8-sig")))
for r in ROWS:
    for k in ("s1", "s2", "razao", "share_score", "pred_cobertura", "pred_peso_doador", "margem", "share_unid"):
        r[k] = float(r[k] or 0)
    for k in ("confiante", "aceito", "exact_hits", "pred_exact_hits", "n_pos"):
        r[k] = int(r[k] or 0)
CRU = [r for r in ROWS if r["regime"] == "cru"]
PROD = [r for r in ROWS if r["regime"] == "produto"]


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        m = (i + j) / 2 + 1
        for t in range(i, j + 1):
            rk[o[t]] = m
        i = j + 1
    return rk


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((y - mb) ** 2 for y in rb) ** 0.5
    return num / (da * db) if da and db else 0.0


conf = [r for r in CRU if r["confiante"]]
print(f"(a) Spearman contra o winner_score s1, nos {len(conf)} confiantes do CRU")
print("    (o piso global de winner_score ja foi REFUTADO 5x; eixo com |rho| alto e ele disfarcado)")
for col in ("margem", "razao", "share_score", "pred_cobertura", "pred_peso_doador", "pred_exact_hits",
            "exact_hits", "n_pos", "share_unid"):
    print(f"    rho(s1, {col:18}) = {spearman([r['s1'] for r in conf], [r[col] for r in conf]):+.3f}")

print()
print("(b) O que as duas regras SEM regressao no produto disparam, material a material (produto):")
regras = {
    "pred vazia": lambda r: not r["pred"],
    "pred_cobertura<0.2 E pred_peso_doador<=1.1": lambda r: r["pred_cobertura"] < 0.2 and r["pred_peso_doador"] <= 1.1,
}
for nome, f in regras.items():
    print(f"  {nome}")
    for reg, rows in (("cru", CRU), ("produto", PROD)):
        alvo = [r for r in rows if r["confiante"] and f(r)]
        print(f"    {reg:8} dispara em {len(alvo):>3} confiantes: "
              f"{sum(1 for r in alvo if not r['aceito'])} erros, {sum(r['aceito'] for r in alvo)} certos")
        if reg == "produto":
            for r in alvo:
                print(f"       {r['curso']:4} {r['entry_id'][:46]:46} {'ERRO' if not r['aceito'] else 'certo'} "
                      f"pred={r['pred'][:30]}")

print()
print("(c) Preco medido do piso de 80% de precisao no CRU (o numero que o astra escolheu no ar):")
print("    melhor regra medida que cruza 80%: rota==2a-propagado OU pred_peso_doador<=1.1")
f80 = lambda r: r["rota"] == "2a-propagado" or r["pred_peso_doador"] <= 1.1  # noqa: E731
for reg, rows in (("cru", CRU), ("produto", PROD)):
    C = sum(1 for r in rows if r["confiante"] and not f80(r) and r["aceito"])
    E = sum(1 for r in rows if r["confiante"] and not f80(r) and not r["aceito"])
    C0 = sum(1 for r in rows if r["confiante"] and r["aceito"])
    E0 = sum(1 for r in rows if r["confiante"] and not r["aceito"])
    print(f"    {reg:8} C {C0} -> {C} ({C - C0:+d})   E {E0} -> {E} ({E - E0:+d})   "
          f"precisao {C0/(C0+E0):.1%} -> {C/(C+E):.1%}   entrega {C0/251:.1%} -> {C/251:.1%}")

print()
print("(d) Sensibilidade do denominador: erros confiantes por curso e o que o n nao sustenta")
for reg, rows in (("cru", CRU), ("produto", PROD)):
    print(f"    {reg}: erros confiantes por curso = " + ", ".join(
        f"{s}:{sum(1 for r in rows if r['curso'] == s and r['confiante'] and not r['aceito'])}"
        for s in ("MF", "SO", "IA", "ES2", "TCC", "CG", "FR")))
