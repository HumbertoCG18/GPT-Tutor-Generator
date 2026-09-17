"""Frente A da Fase 1 (11/09): "algum candidato se aplica?" — abstencao na subunidade, 0 chamadas, produto real.
Le os manifests dos 7 tutores com gold e cruza com subunit_gt_<SIGLA>.csv:
  gold vazio  = o gold diz que o material nao tem subunidade (a decisao certa e abster-se)
  falso positivo = gold vazio e o motor gravou subunidade  ·  omissao = gold cheio e o motor nao gravou
Depois varre um piso de RESULTADO em winner_score e em conf (abster = nao gravar subunidade) medindo os dois lados:
falsos positivos que viram acerto x acertos que viram omissao. Piso global de score foi refutado em 07/09 na regua de
233; aqui e remedido no produto de 11/09 com os gold vazios contados. Uso: python mede_abstencao.py"""
import csv
import json
import re
import statistics
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.routing.revisar import revisar_de  # noqa: E402

T = {"CG": "Computacao-Grafica-Tutor", "ES2": "Engenharia-Software-2-Tutor", "FR": "Fundamentos-de-Redes-Tutor",
     "IA": "Inteligencia-Artifical-Tutor", "MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "TCC": "TCC-Tutor"}
rows = []   # dict por material com gold
for sig, repo in T.items():
    man = {e["id"]: e for e in json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    for r in csv.DictReader(open(GEN / f"docs/reports/subunit_gt_{sig}.csv", encoding="utf-8-sig")):
        if r["scorable"] != "yes" or r["entry_id"] not in man:
            continue
        e = man[r["entry_id"]]
        alvo = ({r["gold_subunit"]} | set(filter(None, r.get("gold_subunits_extra", "").split(";")))) if r["gold_subunit"] else {""}
        sc = re.search(r"winner_score=([\d.]+)", " ".join(e.get("subunit_match_reasons") or []))
        pred = e.get("computed_subunit_slug") or ""
        rows.append({"sig": sig, "id": r["entry_id"], "tipo": e.get("file_type"), "gold_vazio": not r["gold_subunit"], "pred": pred,
                     "certo": pred in alvo, "conf": float(e.get("subunit_match_confidence") or 0), "score": float(sc.group(1)) if sc else 0.0,
                     "fila": revisar_de(e) in ("duvida", "mudou")})

gv = [x for x in rows if x["gold_vazio"]]
fp = [x for x in gv if x["pred"]]
om = [x for x in rows if not x["gold_vazio"] and not x["pred"]]
print(f"materiais com gold {len(rows)} · gold vazio {len(gv)} (o motor se absteve em {len(gv) - len(fp)}, gravou subunidade em {len(fp)} = falsos positivos)"
      f" · gold cheio sem subunidade gravada (omissoes) {len(om)}")
print("\nfalsos positivos (gold vazio, motor gravou):")
for x in fp:
    print(f"  {x['sig']:4} {x['id'][:48]:48} {str(x['tipo']):5} -> {x['pred'][:30]:30} conf {x['conf']:.2f} score {x['score']:6.2f} {'fila' if x['fila'] else 'confiante'}")
print("\nomissoes (gold cheio, motor nao gravou):")
for x in om:
    print(f"  {x['sig']:4} {x['id'][:48]:48} {str(x['tipo']):5} gold-cheio conf {x['conf']:.2f} score {x['score']:6.2f} {'fila' if x['fila'] else 'confiante'}")


def q(vals):
    vals = sorted(vals)
    return "-" if not vals else f"min {vals[0]:.2f} · q1 {statistics.quantiles(vals, n=4)[0]:.2f} · med {statistics.median(vals):.2f} · q3 {statistics.quantiles(vals, n=4)[2]:.2f}" if len(vals) >= 4 else f"{[round(v, 2) for v in vals]}"


certos = [x for x in rows if x["certo"] and x["pred"]]
print(f"\nscore dos falsos positivos: {q([x['score'] for x in fp])}")
print(f"score dos acertos com subunidade (n={len(certos)}): {q([x['score'] for x in certos])}")
print(f"conf dos falsos positivos: {q([x['conf'] for x in fp])}")
print(f"conf dos acertos com subunidade: {q([x['conf'] for x in certos])}")

print(f"\n{'piso de RESULTADO (abster se ...)':34} {'FP que viram acerto':>20} {'acertos que viram omissao':>26} {'saldo':>6}")
for nome, f in [(f"score < {t}", (lambda t: lambda x: x["score"] < t)(t)) for t in (0.5, 1.0, 1.5, 2.0, 3.0, 5.0)] + \
               [(f"conf < {t}", (lambda t: lambda x: x["conf"] < t)(t)) for t in (0.15, 0.2, 0.25, 0.3)]:
    ganha = sum(1 for x in fp if f(x)); perde = sum(1 for x in certos if f(x))
    print(f"{nome:34} {ganha:>13}/{len(fp):<6} {perde:>18}/{len(certos):<7} {ganha - perde:>+6}")
