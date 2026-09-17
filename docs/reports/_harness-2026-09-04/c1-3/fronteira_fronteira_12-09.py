"""FRONTEIRA entrega x precisao no regime CRU (e o espelho no PRODUTO), com holdout LOCO.

Definicoes (base 251, escopo=produto, aceito com-extras):
  C = confiante CERTO   E = confiante ERRADO   Q = fila (251 - C - E)
  entrega = C/251   precisao = C/(C+E)   cobertura = (C+E)/251
Uma REGRA DE ABSTENCAO move confiantes para a fila. Nunca traz da fila para o confiante.
Le fronteira_sinais_12-09.csv (produzido por sinais_v2.py). 0 chamadas.
"""
import csv
import itertools
from pathlib import Path

OUT = Path(__file__).resolve().parent   # 12/09: saida no proprio harness (era o scratchpad da sessao)
ROWS = list(csv.DictReader((OUT / "fronteira_sinais_12-09.csv").open(encoding="utf-8-sig")))
NUM = ("s1", "s2", "margem", "razao", "share_score", "cobertura", "peso_doador", "share_unid",
       "pred_peso_doador", "pred_cobertura", "pred_score")
INT = ("confiante", "aceito", "primario", "vazio", "n_pos", "n_cand", "frase", "exact_hits",
       "max_tok_frase", "tok_frase_doador", "n_topic_tokens", "n_overlap", "n_alias",
       "pred_frase", "pred_exact_hits", "pred_max_tok_frase", "pred_tok_frase_doador",
       "pred_n_topic_tokens", "pred_n_overlap", "pred_n_alias", "n_mat_unid", "n_iguais")
for r in ROWS:
    for k in NUM:
        r[k] = float(r[k] or 0)
    for k in INT:
        r[k] = int(r[k] or 0)
CRU = [r for r in ROWS if r["regime"] == "cru"]
PROD = [r for r in ROWS if r["regime"] == "produto"]
CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]


def ponto(rows, abster):
    C = E = Q = 0
    for r in rows:
        if not r["confiante"] or abster(r):
            Q += 1
        elif r["aceito"]:
            C += 1
        else:
            E += 1
    n = len(rows)
    return dict(C=C, E=E, Q=Q, n=n, entrega=C / n, precisao=(C / (C + E) if C + E else 1.0),
                cobertura=(C + E) / n)


# ---------------------------------------------------------------- familia de regras
def mk(nome, f):
    return (nome, f)


REGRAS = [mk("(nenhuma)", lambda r: False)]

# 1. exact_hits do topico ENTREGUE e do VENCEDOR do score
for k in (0, 1, 2, 3, 4):
    REGRAS.append(mk(f"pred_exact_hits<={k}", lambda r, k=k: r["pred_exact_hits"] <= k))
    REGRAS.append(mk(f"win_exact_hits<={k}", lambda r, k=k: r["exact_hits"] <= k))

# 2. peso do campo doador da frase que casou (topico entregue)
for w in (0.0, 0.15, 0.22, 0.9, 1.1, 2.8, 3.0, 3.8, 4.4):
    REGRAS.append(mk(f"pred_peso_doador<={w}", lambda r, w=w: r["pred_peso_doador"] <= w + 1e-9))
REGRAS.append(mk("doador in {corpo,raw,auto,legacy}",
                 lambda r: r["pred_doador"] in ("markdown_text", "raw_text", "auto_tags_text", "legacy_tags_text")))
REGRAS.append(mk("doador != heading/titulo",
                 lambda r: r["pred_doador"] not in ("markdown_headings_text", "title_text")))
REGRAS.append(mk("origem != label", lambda r: r["pred_origem"] != "label"))
REGRAS.append(mk("origem == slug/vazio", lambda r: r["pred_origem"] in ("slug", "")))

# 3. tamanho em tokens da frase que casou
for t in (0, 1, 2, 3):
    REGRAS.append(mk(f"pred_max_tok_frase<={t}", lambda r, t=t: r["pred_max_tok_frase"] <= t))
    REGRAS.append(mk(f"pred_tok_doador<={t}", lambda r, t=t: r["pred_tok_frase_doador"] <= t))

# 4. passada que decidiu
REGRAS.append(mk("rota==2a (toda)", lambda r: r["passada"] == "2a"))
for sub in ("2a-propagado", "2a-rotulo", "2a-titulo", "2a-secao"):
    REGRAS.append(mk(f"rota=={sub}", lambda r, s=sub: r["rota"] == s))
REGRAS.append(mk("rota in {2a-propagado,2a-rotulo}", lambda r: r["rota"] in ("2a-propagado", "2a-rotulo")))
REGRAS.append(mk("rota==1a", lambda r: r["rota"] == "1a"))

# 5. share do vencedor por SCORE (s1 / soma dos positivos da unidade)
for s in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90):
    REGRAS.append(mk(f"share_score<{s:.2f}", lambda r, s=s: r["share_score"] < s))

# 5b. share do vencedor por MATERIAIS da unidade (concentracao do corpus)
for s in (0.10, 0.20, 0.30, 0.40, 0.50):
    REGRAS.append(mk(f"share_unid<{s:.2f}", lambda r, s=s: r["share_unid"] < s))
for k in (1, 2, 3, 5):
    REGRAS.append(mk(f"n_iguais<={k}", lambda r, k=k: r["n_iguais"] <= k))

# 6. numero de topicos com score > 0
for m in (2, 3, 4, 5, 6, 7, 8, 10, 12):
    REGRAS.append(mk(f"n_pos>={m}", lambda r, m=m: r["n_pos"] >= m))
REGRAS.append(mk("n_pos==n_cand (todos pontuam)", lambda r: r["n_pos"] >= r["n_cand"] > 0))

# 7. predicao vazia
REGRAS.append(mk("pred vazia", lambda r: r["vazio"] == 1))

# 8. cobertura de tokens do topico entregue / overlap
for c in (0.2, 0.3, 0.4, 0.5, 0.6, 0.8):
    REGRAS.append(mk(f"pred_cobertura<{c:.1f}", lambda r, c=c: r["pred_cobertura"] < c))
for k in (0, 1, 2, 3, 4, 6):
    REGRAS.append(mk(f"pred_n_overlap<={k}", lambda r, k=k: r["pred_n_overlap"] <= k))

# 9. riqueza de alias do topico entregue
REGRAS.append(mk("pred_n_alias==0", lambda r: r["pred_n_alias"] == 0))
for k in (1, 2, 3, 5):
    REGRAS.append(mk(f"pred_n_alias<={k}", lambda r, k=k: r["pred_n_alias"] <= k))

# 10. razao s2/s1 (eixo VIZINHO do winner_score ja refutado; entra so para mostrar onde cai)
for q in (0.30, 0.50, 0.70, 0.85, 0.95):
    REGRAS.append(mk(f"razao>{q:.2f}", lambda r, q=q: r["razao"] > q))


def aplica(rows, f):
    return frozenset(r["entry_id"] + "@" + r["curso"] for r in rows if r["confiante"] and f(r))


# dedupe por conjunto abstido no CRU (mantem o nome mais curto)
vistos = {}
for nome, f in REGRAS:
    chave = aplica(CRU, f)
    if chave not in vistos or len(nome) < len(vistos[chave][0]):
        vistos[chave] = (nome, f)
BASE = [(n, f) for n, f in sorted(vistos.values(), key=lambda x: x[0])]

# 11. conjuncoes 2 a 2 (AND) das que SEPARAM: remove >=3 erros e nao e trivial
sep = []
for nome, f in BASE:
    p = ponto(CRU, f)
    dE = 77 - p["E"]
    dC = 113 - p["C"]
    if dE >= 3 and p["C"] > 0 and nome != "(nenhuma)":
        sep.append((nome, f, dE, dC))
sep.sort(key=lambda x: (x[3] / max(1, x[2])))
TOP = sep[:14]
PARES = []
for (n1, f1, _, _), (n2, f2, _, _) in itertools.combinations(TOP, 2):
    PARES.append((f"{n1} E {n2}", lambda r, a=f1, b=f2: a(r) and b(r)))
    PARES.append((f"{n1} OU {n2}", lambda r, a=f1, b=f2: a(r) or b(r)))

TODAS = BASE + PARES
vistos2 = {}
for nome, f in TODAS:
    chave = aplica(CRU, f)
    if chave not in vistos2 or len(nome) < len(vistos2[chave][0]):
        vistos2[chave] = (nome, f)
TODAS = sorted(vistos2.values(), key=lambda x: x[0])

# ---------------------------------------------------------------- tabela de pontos
pts = []
for nome, f in TODAS:
    pc, pp = ponto(CRU, f), ponto(PROD, f)
    dE, dC = 77 - pc["E"], 113 - pc["C"]
    pts.append(dict(nome=nome, f=f, cru=pc, prod=pp, dE=dE, dC=dC,
                    custo=(dC / dE if dE else float("inf"))))
pts.sort(key=lambda x: (-x["cru"]["entrega"], -x["cru"]["precisao"]))

# Pareto no CRU: nao dominado em (entrega, precisao)
for p in pts:
    p["dominado"] = any(q is not p and q["cru"]["C"] >= p["cru"]["C"] and q["cru"]["precisao"] >= p["cru"]["precisao"]
                        and (q["cru"]["C"] > p["cru"]["C"] or q["cru"]["precisao"] > p["cru"]["precisao"])
                        for q in pts)

print("=" * 118)
print("TODOS OS PONTOS (regime CRU), ordenados por entrega. '*' = na fronteira de Pareto do CRU")
print(f"{'':2} {'regra':46} {'C':>4} {'E':>3} {'Q':>4} {'entrega':>8} {'precis':>7} {'cobert':>7} "
      f"{'-dC':>4} {'-dE':>4} {'dC/dE':>6} | PRODUTO {'C':>4} {'E':>3} {'entrega':>8} {'precis':>7}")
print("-" * 118)
for p in pts:
    c, q = p["cru"], p["prod"]
    print(f"{'*' if not p['dominado'] else ' ':2} {p['nome'][:46]:46} {c['C']:>4} {c['E']:>3} {c['Q']:>4} "
          f"{c['entrega']:>7.1%} {c['precisao']:>7.1%} {c['cobertura']:>7.1%} "
          f"{p['dC']:>4} {p['dE']:>4} {p['custo']:>6.2f} |         {q['C']:>4} {q['E']:>3} "
          f"{q['entrega']:>7.1%} {q['precisao']:>7.1%}")

print()
print("=" * 118)
print("FRONTEIRA DE PARETO DO CRU (so nao dominados), por entrega decrescente")
print(f"{'regra':46} {'C':>4} {'E':>3} {'Q':>4} {'entrega':>8} {'precis':>7} {'dC/dE':>6} | "
      f"PROD {'C':>4} {'E':>3} {'entrega':>8} {'precis':>7} {'regride?':>9}")
print("-" * 118)
front = [p for p in pts if not p["dominado"]]
for p in front:
    c, q = p["cru"], p["prod"]
    reg = []
    if q["precisao"] < 0.9222 - 1e-9:
        reg.append("prec")
    if q["C"] < 178:
        reg.append("entrega")
    print(f"{p['nome'][:46]:46} {c['C']:>4} {c['E']:>3} {c['Q']:>4} {c['entrega']:>7.1%} {c['precisao']:>7.1%} "
          f"{p['custo']:>6.2f} |      {q['C']:>4} {q['E']:>3} {q['entrega']:>7.1%} {q['precisao']:>7.1%} "
          f"{'+'.join(reg) or '-':>9}")

print()
print("PONTO DE QUEBRA DO PRODUTO (primeiro da fronteira, por entrega decrescente, que regride):")
for p in front:
    q = p["prod"]
    if q["precisao"] < 0.9222 - 1e-9 or q["C"] < 178:
        print(f"  {p['nome']}: produto C {q['C']} (era 178), precisao {q['precisao']:.1%} (era 92,2%), "
              f"cru entrega {p['cru']['entrega']:.1%} precisao {p['cru']['precisao']:.1%}")
        break
print("Regras da fronteira que NAO regridem o produto (C>=178 e precisao>=92,2%):")
nao = [p for p in front if p["prod"]["C"] >= 178 and p["prod"]["precisao"] >= 0.9222 - 1e-9]
for p in nao:
    print(f"  {p['nome']}: cru C {p['cru']['C']} E {p['cru']['E']} ({p['cru']['precisao']:.1%}) | "
          f"produto C {p['prod']['C']} E {p['prod']['E']} ({p['prod']['precisao']:.1%})")
if not nao:
    print("  nenhuma alem da regra vazia")
