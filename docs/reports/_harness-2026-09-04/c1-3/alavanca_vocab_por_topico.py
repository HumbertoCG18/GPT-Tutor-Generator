"""ALAVANCA: devolver vocabulario de dominio SO nos topicos que os 104 erros pedem. Ganho E perda nominais.

Proxy do trabalho humano: em vez de inventar o vocabulario, devolve ao regime cru os sinonimos que o sidecar LLM ja
tem PARA ESSES TOPICOS. Nao e o vocabulario que um humano escreveria, mas e um vocabulario real desses topicos, e
mede o que uma curadoria dirigida a eles faz no placar inteiro (251) -- ganho E perda, aceito E primario, confiante.

VIES DECLARADO: os topicos foram escolhidos OLHANDO O GOLD dos erros. Isto mede o teto de uma curadoria
perfeitamente dirigida DENTRO DA AMOSTRA; nao e ganho generalizavel para um curso novo.

0 chamadas de rede. Nao escreve no repo nem em .ablacao/.
"""
import collections
import csv
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator\docs\reports\_harness-2026-09-04\c1-3")
spec = importlib.util.spec_from_file_location("replay", HARN / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]
R = list(csv.DictReader((HERE / "inventario_fontes_104_cru.csv").open(encoding="utf-8-sig")))
CNT = collections.Counter((r["curso"], r["gold_primario"]) for r in R if r["gold_primario"])
TOP10 = {p for p, _ in CNT.most_common(10)}
TODOS = set(CNT)


def llm_norms(sig):
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    if not p.exists():
        return set()
    d = json.loads(p.read_text(encoding="utf-8"))
    return {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}


def taxmod(sig, manter):
    """Tira os sinonimos LLM de TODO topico, menos dos topicos de `manter` deste curso."""
    vet = llm_norms(sig)
    keep = {t for (s, t) in manter if s == sig}

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                if t["slug"] in keep:
                    continue
                t["aliases"] = [a for a in t.get("aliases", []) if _norm(a) not in vet]
    return change


def gold_rows(sig):
    return {r["entry_id"]: r for r in csv.DictReader(
        Path(f"docs/reports/subunit_gt_{sig}.csv").open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


def corre(manter):
    ac = pr = n = conf = conf_ac = 0
    okmap = {}
    for sig in CURSOS:
        r = rp.evaluate(sig, "com", new=False, taxmod=taxmod(sig, manter), escopo="produto")
        pred, ents = r[3], {e["id"]: e for e in r[6]}
        for eid, row in gold_rows(sig).items():
            if eid not in ents:
                continue
            aceitos = ({row["gold_subunit"]} | set(filter(None, row.get("gold_subunits_extra", "").split(";")))
                       if row["gold_subunit"] else {""})
            p = pred.get(eid, "")
            o = p in aceitos
            okmap[(sig, eid)] = (o, p)
            n += 1
            ac += o
            pr += p == row["gold_subunit"]
            if revisar_de(ents[eid]) not in ("duvida", "mudou"):
                conf += 1
                conf_ac += o
    return dict(n=n, aceito=ac, primario=pr, conf=conf, conf_ac=conf_ac), okmap


base, ok_base = corre(set())
print(f"{'braco':46} {'aceito':>10} {'primario':>10} {'confiante':>10} {'aceito do confiante':>21}")


def linha(nome, st):
    print(f"{nome:46} {st['aceito']:>4}/{st['n']} {st['aceito']/st['n']:>5.1%} {st['primario']:>4} "
          f"{st['primario']/st['n']:>5.1%} {st['conf']:>10} {st['conf_ac']:>6}/{st['conf']:<5} "
          f"{st['conf_ac']/max(1,st['conf']):>6.1%}")


linha("cru (baseline, 0 topicos com vocabulario)", base)
for nome, manter in (("cru + vocab LLM nos TOP-10 topicos", TOP10), (f"cru + vocab LLM nos {len(TODOS)} topicos do gold dos erros", TODOS)):
    st, okm = corre(manter)
    linha(nome, st)
    ganho = [k for k in ok_base if not ok_base[k][0] and okm[k][0]]
    perda = [k for k in ok_base if ok_base[k][0] and not okm[k][0]]
    print(f"    GANHO {len(ganho)} nominais: " + ", ".join(f"{s}/{e}" for s, e in sorted(ganho)[:40]))
    if len(ganho) > 40:
        print(f"      ... +{len(ganho)-40}")
    print(f"    PERDA {len(perda)} nominais: " + (", ".join(f"{s}/{e} (cru {ok_base[k][1] or 'vazio'} -> {okm[k][1] or 'vazio'})"
                                                            for k in sorted(perda) for s, e in [k]) or "nenhuma"))
    print()
print("PRODUTO (todo o vocab LLM, referencia da regua congelada): 224 aceito / 186 primario de 251; "
      "confiante 193; aceito do confiante 92,2%")
print(f"\nTOP-10 topicos: " + " · ".join(f"{s}/{t}" for s, t in sorted(TOP10)))
