"""A precisao do confiante NO REGIME CRU (12/09 tarde; achado do astra no brief v2).

`calibra_fila_como_regua.py` le o `manifest.json` do PRODUTO: ele mede a fila do produto, com o vocabulario do LLM
dentro. **A precisao do confiante do regime cru nunca tinha sido medida** — e e ela que o usuario escolheu como metrica
que ordena a frente ("aceito do confiante + cobertura + fila", 12/09).

Aqui a fila e recalculada a partir das decisoes do REPLAY: `revisar_de` e funcao pura do entry, e o unico gatilho que
muda entre regimes e o de subunidade (`sub-ambigua` / `sub-empate`, de `subunit_match_reasons`) — bloco, flag de bloco e
conflito unidade x bloco vem do manifest e sao iguais nos dois. Por isso o mesmo instrumento vale nos dois regimes.

Publica, por regime e por curso: n · confiante · na fila · PRECISAO DO CONFIANTE por aceito E por primario · cobertura
(confiante/n) · recall da fila · alarme falso. 0 chamadas.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/calibra_fila_cru_12-09.py
"""
import csv
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402
from src.builder.routing.revisar import motivos_de, revisar_de  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]


def sem_llm(sig):
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    vet = set()
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        vet = {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                t["aliases"] = [a for a in t.get("aliases", []) if _norm(a) not in vet]
    return change


def so_codigo(tax):
    for u in tax["units"]:
        for t in u["topics"]:
            t["aliases"] = [a for a in t.get("aliases", []) if re.match(r"^\d", a)]


def gold_rows(sig):
    p = Path(f"docs/reports/subunit_gt_{sig}.csv")
    return {r["entry_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


REGIMES = [("produto", None), ("cru", sem_llm), ("so_codigo", lambda sig: so_codigo)]
res = {}
motivos_cru = {}
for nome, mod in REGIMES:
    tot = dict(n=0, conf=0, fila=0, conf_ac=0, conf_pr=0, fila_ac=0, conf_vazio=0)
    por_curso = {}
    for sig in CURSOS:
        taxmod = mod(sig) if mod else None
        r = rp.evaluate(sig, "com", new=False, taxmod=taxmod, escopo="produto")
        entries, pred = {e["id"]: e for e in r[6]}, r[3]
        gold = gold_rows(sig)
        c = dict(n=0, conf=0, fila=0, conf_ac=0, conf_pr=0, fila_ac=0, conf_vazio=0)
        for eid, row in gold.items():
            e = entries.get(eid)
            if e is None:
                continue
            aceitos = ({row["gold_subunit"]} | set(filter(None, row.get("gold_subunits_extra", "").split(";")))
                       if row["gold_subunit"] else {""})
            p = pred.get(eid, "")
            ok_ac, ok_pr = p in aceitos, p == row["gold_subunit"]
            na_fila = revisar_de(e) in ("duvida", "mudou")
            c["n"] += 1
            if na_fila:
                c["fila"] += 1
                c["fila_ac"] += ok_ac
            else:
                c["conf"] += 1
                c["conf_ac"] += ok_ac
                c["conf_pr"] += ok_pr
                c["conf_vazio"] += not p
            if nome == "cru" and not ok_ac:
                motivos_cru[(sig, eid)] = (motivos_de(e), p, row["gold_subunit"])
        por_curso[sig] = c
        for k in tot:
            tot[k] += c[k]
    res[nome] = (tot, por_curso)

print("A PRECISAO DO CONFIANTE, POR REGIME (base 251; 'confiante' = o motor NAO poe na fila)")
print(f"{'regime':10} {'n':>4} {'confiante':>10} {'cobertura':>10} {'ACEITO do confiante':>21} "
      f"{'PRIMARIO do confiante':>23} {'fila':>5} {'recall da fila':>16} {'alarme falso':>14}")
for nome, _ in REGIMES:
    t = res[nome][0]
    err_ac = (t["conf"] - t["conf_ac"]) + (t["fila"] - t["fila_ac"])
    print(f"{nome:10} {t['n']:>4} {t['conf']:>10} {t['conf'] / t['n']:>9.1%} "
          f"{t['conf_ac']:>6}/{t['conf']:<5} {t['conf_ac'] / max(1, t['conf']):>6.1%} "
          f"{t['conf_pr']:>7}/{t['conf']:<5} {t['conf_pr'] / max(1, t['conf']):>7.1%} "
          f"{t['fila']:>5} {t['fila'] - t['fila_ac']:>4}/{err_ac:<4} {(t['fila'] - t['fila_ac']) / max(1, err_ac):>5.0%} "
          f"{t['fila_ac']:>4}/{t['fila']:<4} {t['fila_ac'] / max(1, t['fila']):>4.0%}")

print()
print("Predicao VAZIA entre os confiantes (o motor nao decidiu e nao avisou):")
for nome, _ in REGIMES:
    t = res[nome][0]
    print(f"  {nome:10} {t['conf_vazio']:>4} de {t['conf']} confiantes")

print()
print("POR CURSO (confiante / n · aceito do confiante · primario do confiante)")
print(f"{'curso':5} " + " ".join(f"{nome:>28}" for nome, _ in REGIMES))
for sig in CURSOS:
    linha = f"{sig:5} "
    for nome, _ in REGIMES:
        c = res[nome][1][sig]
        linha += (f" {c['conf']:>3}/{c['n']:<3} {c['conf_ac']:>3}ac {c['conf_ac'] / max(1, c['conf']):>5.0%} "
                  f"{c['conf_pr']:>3}pr {c['conf_pr'] / max(1, c['conf']):>5.0%}")
    print(linha)

print()
print("ERROS CONFIANTES DO REGIME CRU (o motor entrega errado sem avisar), por curso:")
conf_err = {k: v for k, v in motivos_cru.items() if not v[0]}
for sig in CURSOS:
    ids = [k[1] for k in conf_err if k[0] == sig]
    print(f"  {sig:5} {len(ids):>3}")
print(f"  TOTAL {len(conf_err)}")
print()
print("Os erros do cru que a FILA pega (tem motivo), por motivo:")
cnt = {}
for (sig, eid), (mot, p, g) in motivos_cru.items():
    for m in mot:
        cnt[m] = cnt.get(m, 0) + 1
for m, n in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"  {m:20} {n:>4}")
