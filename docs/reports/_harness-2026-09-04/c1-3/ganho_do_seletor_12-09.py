"""Quanto se ganha curando o que o SELETOR aponta, contra curar o que o GOLD aponta (12/09 noite).

O seletor (`seletor_topicos_carentes_12-09.py`) escolhe topicos SEM olhar o gold: os que nao tem suporte por FRASE em
nenhum material da unidade, ordenados por quantos materiais a unidade tem (o dano potencial).

Aqui o ganho e medido do mesmo jeito que a alavanca dirigida pelo gold foi medida: devolvendo ao regime cru os
sinonimos que o sidecar do LLM ja tem PARA AQUELES TOPICOS. E um PROXY do que uma curadoria real produziria — mede "o
que vocabulario naqueles topicos faz", nao "o que o curador vai escrever".

As duas curvas (seletor x gold) contra o mesmo eixo K respondem a pergunta que importa: **escolher sem o gold custa
quantos pontos?**

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/ganho_do_seletor_12-09.py
"""
import collections
import csv
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]


def llm_por_topico(sig):
    """{topic_slug: set(_norm dos sinonimos)} — so para saber QUAIS devolver."""
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    if not p.exists():
        return {}, set()
    d = json.loads(p.read_text(encoding="utf-8"))
    todos = {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}
    return d, todos


def taxmod(sig, liberados):
    """Veta os aliases do sidecar LLM, MENOS nos topicos liberados."""
    _, vet = llm_por_topico(sig)

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                if t["slug"] in liberados:
                    continue
                t["aliases"] = [a for a in t.get("aliases", []) if _norm(a) not in vet]
    return change


def gold_rows(sig):
    p = Path(f"docs/reports/subunit_gt_{sig}.csv")
    return {r["entry_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


def mede(escolhidos):
    """escolhidos: set de (curso, topic_slug). Devolve (aceito, primario) na base 251."""
    ac = pr = 0
    for sig in CURSOS:
        lib = {slug for (c, slug) in escolhidos if c == sig}
        r = rp.evaluate(sig, "com", new=False, taxmod=taxmod(sig, lib), escopo="produto")
        gold = gold_rows(sig)
        for eid, row in gold.items():
            aceitos = ({row["gold_subunit"]} | set(filter(None, row.get("gold_subunits_extra", "").split(";")))
                       if row["gold_subunit"] else {""})
            p = r[3].get(eid, "")
            ac += p in aceitos
            pr += p == row["gold_subunit"]
    return ac, pr


# ranking do SELETOR (sem gold): sem suporte por frase, por dano potencial
sel = list(csv.DictReader((HERE / "seletor_topicos_carentes_12-09.csv").open(encoding="utf-8-sig")))
cand = [r for r in sel if r["suporte_por_frase"] == "0"]
cand.sort(key=lambda r: -int(r["materiais_na_unidade"]))
rank_sel = [(r["curso"], r["topico"]) for r in cand]

# ranking do GOLD: os pares que mais concentram erro
er = list(csv.DictReader((HERE / "erros_subunidade_motor_12-09.csv").open(encoding="utf-8-sig")))
rank_gold = [k for k, _ in collections.Counter((r["curso"], r["gold"]) for r in er if r["gold"]).most_common()]

base_ac, base_pr = mede(set())
print(f"base (regime cru, nenhum topico curado): {base_ac}/251 aceito · {base_pr} primario")
print()
print(f"{'K':>4} {'SELETOR (sem gold)':>28} {'GOLD (com gold)':>26} {'custo de nao ver o gold':>26}")
print(f"{'':>4} {'aceito':>12} {'primario':>13} {'aceito':>12} {'primario':>13}")
for K in (5, 10, 15, 20, 30, 40):
    s_ac, s_pr = mede(set(rank_sel[:K]))
    g_ac, g_pr = mede(set(rank_gold[:K]))
    print(f"{K:>4} {s_ac:>8} {s_ac/251:>6.1%} {s_pr:>8} {s_pr/251:>6.1%} "
          f"{g_ac:>8} {g_ac/251:>6.1%} {g_pr:>8} {g_pr/251:>6.1%} "
          f"{s_ac-g_ac:>+14} aceito")
print()
print(f"topicos candidatos do seletor: {len(rank_sel)} · pares com erro no gold: {len(rank_gold)}")
print()
print("TOP-20 do seletor (a fila de curadoria que um curso NOVO receberia):")
for i, (sig, slug) in enumerate(rank_sel[:20], 1):
    r = next(x for x in cand if x["curso"] == sig and x["topico"] == slug)
    print(f"  {i:>2}. {sig:4} {slug:52} unidade com {r['materiais_na_unidade']:>3} materiais"
          f"{'   <== esta nos 10 do gold' if r['e_alvo_do_gold'] == '1' else ''}")
