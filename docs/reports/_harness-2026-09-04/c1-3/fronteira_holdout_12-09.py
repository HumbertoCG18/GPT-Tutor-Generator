"""HOLDOUT leave-one-course-out da fronteira de abstencao (regime CRU) + taxa de troca marginal.

Protocolo: para cada curso h, escolhe a MELHOR regra nos outros 6 e mede no 7o.
Dois criterios de escolha, os dois publicados:
  (a) utilidade U_k = C - k*E (k = quantas entregas certas vale um erro confiante; e o numero
      que o astra CHUTOU como 4);
  (b) custo limitado: maximiza erros removidos gastando no maximo D entregas certas nos 6.
Publica o ganho DENTRO da amostra de escolha e FORA dela, e a diferenca.
Reimporta a familia de regras de fronteira.py (mesmo arquivo, mesma definicao).
"""
import runpy
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent   # 12/09: saida no proprio harness (era o scratchpad da sessao)
sys.stdout = open(OUT / "_tmp_sink.txt", "w", encoding="utf-8")
G = runpy.run_path(str(OUT / "fronteira_fronteira_12-09.py"))
sys.stdout = sys.__stdout__
TODAS, CRU, PROD, ponto, CURSOS = G["TODAS"], G["CRU"], G["PROD"], G["ponto"], G["CURSOS"]
pts = G["pts"]


def por_curso(rows, sig):
    return [r for r in rows if r["curso"] == sig]


def U(p, k):
    return p["C"] - k * p["E"]


print("=" * 108)
print("1. TAXA DE TROCA MARGINAL AO LONGO DA FRONTEIRA DO CRU (o numero que substitui o '4' chutado)")
print("   cada degrau: quantas entregas certas se perde por erro confiante removido")
front = [p for p in pts if not p["dominado"]]
print(f"{'degrau (regra que fecha)':46} {'C':>4} {'E':>3} {'dC':>4} {'dE':>4} {'dC/dE marginal':>15} {'precisao':>9}")
ant = dict(C=113, E=77)
for p in front:
    c = p["cru"]
    dC, dE = ant["C"] - c["C"], ant["E"] - c["E"]
    tx = (dC / dE) if dE else float("inf")
    print(f"{p['nome'][:46]:46} {c['C']:>4} {c['E']:>3} {-dC:>4} {-dE:>4} {tx:>15.2f} {c['precisao']:>8.1%}")
    ant = c
print()
print("Leitura: um degrau so compensa se o erro confiante custar MAIS que a taxa marginal dele.")
for k in (1, 2, 4, 8):
    best = max(front, key=lambda p: U(p["cru"], k))
    base = 113 - k * 77
    print(f"  k={k}: melhor ponto da fronteira = '{best['nome']}' (U={U(best['cru'], k)}, baseline U={base}, "
          f"abster-tudo U=0) -> C {best['cru']['C']} E {best['cru']['E']}")

print()
print("=" * 108)
print("2. HOLDOUT leave-one-course-out, criterio U_k (escolhe em 6 cursos, mede no 7o)")
for k in (1, 2, 4):
    print(f"\n--- k = {k} ---")
    print(f"{'fora':5} {'regra escolhida nos 6':44} {'ganho/mat DENTRO':>17} {'ganho/mat FORA':>15} "
          f"{'dif':>7} {'C_h':>4} {'E_h':>4} {'(base C/E)':>12}")
    somas = []
    for h in CURSOS:
        tr = [r for r in CRU if r["curso"] != h]
        te = por_curso(CRU, h)
        base_tr, base_te = ponto(tr, lambda r: False), ponto(te, lambda r: False)
        melhor = max(TODAS, key=lambda nf: U(ponto(tr, nf[1]), k))
        p_tr, p_te = ponto(tr, melhor[1]), ponto(te, melhor[1])
        g_tr = (U(p_tr, k) - U(base_tr, k)) / len(tr)
        g_te = (U(p_te, k) - U(base_te, k)) / max(1, len(te))
        somas.append((g_tr, g_te, len(te)))
        print(f"{h:5} {melhor[0][:44]:44} {g_tr:>+17.3f} {g_te:>+15.3f} {g_te - g_tr:>+7.3f} "
              f"{p_te['C']:>4} {p_te['E']:>4} {str(base_te['C']) + '/' + str(base_te['E']):>12}")
    tot_tr = sum(g * n for g, _, n in somas) / sum(n for _, _, n in somas)
    tot_te = sum(g * n for _, g, n in somas) / sum(n for _, _, n in somas)
    print(f"{'MEDIA':5} {'(ponderada por material)':44} {tot_tr:>+17.3f} {tot_te:>+15.3f} {tot_te - tot_tr:>+7.3f}")

print()
print("=" * 108)
print("3. HOLDOUT com criterio de CUSTO LIMITADO (max erros removidos gastando <= D entregas nos 6)")
for D in (1, 3, 5, 10):
    print(f"\n--- D = {D} entregas certas (dos 6 cursos de treino) ---")
    print(f"{'fora':5} {'regra escolhida nos 6':44} {'dE/dC treino':>13} {'dE/dC holdout':>14} "
          f"{'dC_h':>5} {'dE_h':>5} {'prec_h':>8} {'(base)':>8}")
    for h in CURSOS:
        tr = [r for r in CRU if r["curso"] != h]
        te = por_curso(CRU, h)
        b_tr, b_te = ponto(tr, lambda r: False), ponto(te, lambda r: False)
        cand = [(n, f) for n, f in TODAS if b_tr["C"] - ponto(tr, f)["C"] <= D]
        melhor = max(cand, key=lambda nf: b_tr["E"] - ponto(tr, nf[1])["E"])
        p_tr, p_te = ponto(tr, melhor[1]), ponto(te, melhor[1])
        dC_tr, dE_tr = b_tr["C"] - p_tr["C"], b_tr["E"] - p_tr["E"]
        dC_te, dE_te = b_te["C"] - p_te["C"], b_te["E"] - p_te["E"]
        print(f"{h:5} {melhor[0][:44]:44} {str(dE_tr) + ' por ' + str(dC_tr):>13} "
              f"{str(dE_te) + ' por ' + str(dC_te):>14} {dC_te:>5} {dE_te:>5} "
              f"{p_te['precisao']:>7.1%} {b_te['precisao']:>7.1%}")

print()
print("=" * 108)
print("4. AS REGRAS DA FRONTEIRA, CURSO A CURSO (quem so ganha dentro da amostra aparece aqui)")
alvo = [p for p in front if p["nome"] != "pred_peso_doador<=4.4"]
for p in alvo:
    f = p["f"]
    print(f"\n{p['nome']}   (cru total: C {p['cru']['C']} E {p['cru']['E']} prec {p['cru']['precisao']:.1%})")
    print(f"  {'curso':5} {'dispara em':>11} {'-dC':>5} {'-dE':>5} {'prec antes':>11} {'prec depois':>12}")
    for sig in CURSOS:
        te = por_curso(CRU, sig)
        b, q = ponto(te, lambda r: False), ponto(te, f)
        disp = sum(1 for r in te if r["confiante"] and f(r))
        print(f"  {sig:5} {disp:>11} {b['C'] - q['C']:>5} {b['E'] - q['E']:>5} "
              f"{b['precisao']:>10.1%} {q['precisao']:>11.1%}")
