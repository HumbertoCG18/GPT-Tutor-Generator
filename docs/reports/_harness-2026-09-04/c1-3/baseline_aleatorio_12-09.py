"""O seletor seleciona alguma coisa, ou o ganho e so do vocabulario? (12/09 noite, desconfianca do usuario)

O usuario disse: "mas esse numero so aumentou por conta do gold". O teste que separa as hipoteses e o BASELINE
ALEATORIO: curar K topicos sorteados, com o mesmo orcamento, e comparar.

  se ALEATORIO ~= SELETOR  -> o ganho e do VOCABULARIO, e o seletor nao seleciona nada
  se SELETOR >> ALEATORIO  -> o seletor esta mesmo achando os topicos carentes

Tres baselines, todos com o mesmo K:
  ALEATORIO      K topicos sorteados entre todos os da taxonomia crua (varias sementes)
  MAIOR-UNIDADE  os K topicos das unidades com mais materiais, IGNORANDO suporte lexical
  SELETOR        sem suporte por FRASE, ordenado por materiais na unidade
  GOLD           os K pares (curso, topico) que mais concentram erro — usa a resposta, e o teto

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/baseline_aleatorio_12-09.py
"""
import collections
import csv
import importlib.util
import json
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]
_VET = {}


def vet(sig):
    if sig not in _VET:
        p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
        s = set()
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            s = {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}
        _VET[sig] = s
    return _VET[sig]


def taxmod(sig, liberados):
    v = vet(sig)

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                if t["slug"] in liberados:
                    continue
                t["aliases"] = [a for a in t.get("aliases", []) if _norm(a) not in v]
    return change


def gold_rows(sig):
    p = Path(f"docs/reports/subunit_gt_{sig}.csv")
    return {r["entry_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


def mede(escolhidos):
    ac = pr = 0
    for sig in CURSOS:
        lib = {slug for (c, slug) in escolhidos if c == sig}
        r = rp.evaluate(sig, "com", new=False, taxmod=taxmod(sig, lib), escopo="produto")
        for eid, row in gold_rows(sig).items():
            aceitos = ({row["gold_subunit"]} | set(filter(None, row.get("gold_subunits_extra", "").split(";")))
                       if row["gold_subunit"] else {""})
            p = r[3].get(eid, "")
            ac += p in aceitos
            pr += p == row["gold_subunit"]
    return ac, pr


sel = list(csv.DictReader((HERE / "seletor_topicos_carentes_12-09.csv").open(encoding="utf-8-sig")))
todos = [(r["curso"], r["topico"]) for r in sel]
mats = {(r["curso"], r["topico"]): int(r["materiais_na_unidade"]) for r in sel}

cand = [r for r in sel if r["suporte_por_frase"] == "0"]
cand.sort(key=lambda r: -int(r["materiais_na_unidade"]))
rank_sel = [(r["curso"], r["topico"]) for r in cand]

rank_mu = sorted(todos, key=lambda k: -mats[k])          # ignora suporte lexical

er = list(csv.DictReader((HERE / "erros_subunidade_motor_12-09.csv").open(encoding="utf-8-sig")))
rank_gold = [k for k, _ in collections.Counter((r["curso"], r["gold"]) for r in er if r["gold"]).most_common()]

base = mede(set())
print(f"base (cru, nada curado): {base[0]}/251 aceito · {base[1]} primario")
print(f"universo de topicos: {len(todos)} · candidatos do seletor: {len(rank_sel)}")
print()
SEMENTES = [1, 2, 3, 4, 5, 6, 7]
print(f"{'K':>3} {'ALEATORIO (media +- dp)':>28} {'MAIOR-UNIDADE':>15} {'SELETOR':>9} {'GOLD':>7}   leitura")
for K in (5, 10, 20):
    al = []
    for s in SEMENTES:
        random.seed(s)
        al.append(mede(set(random.sample(todos, K)))[0])
    m, dp = statistics.mean(al), (statistics.stdev(al) if len(al) > 1 else 0.0)
    mu = mede(set(rank_mu[:K]))[0]
    se = mede(set(rank_sel[:K]))[0]
    go = mede(set(rank_gold[:K]))[0]
    dif = se - m
    leitura = ("SELETOR ganha do acaso" if dif > 2 * max(dp, 1e-9) else
               "dentro do ruido do acaso" if abs(dif) <= 2 * max(dp, 1e-9) else "SELETOR PERDE do acaso")
    print(f"{K:>3} {m:>17.1f} +- {dp:<5.1f} {mu:>15} {se:>9} {go:>7}   {leitura} (dif {dif:+.1f})")
print()
print(f"sementes do aleatorio: {SEMENTES}")
print("todos os numeros sao ACEITO na base 251.")
