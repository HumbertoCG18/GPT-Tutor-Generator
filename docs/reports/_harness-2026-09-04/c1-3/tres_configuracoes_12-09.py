"""As TRES CONFIGURACOES que o usuario pediu, no eixo SUBUNIDADE (12/09, noite).

  (a) CRU           taxonomia sem os sinonimos do sidecar LLM; texto = base_markdown (pymupdf4llm/html)
  (b) CRU+DATALAB   igual, mas onde existe `advanced_markdown` (Datalab) o motor le ELE no lugar do base
  (c) PRODUTO       taxonomia como esta (codigo + plano + manual + LLM); texto = a rota real do produto

ACHADO QUE LIMITA (b): so **31 dos 251** materiais da regua tem Datalab em disco — CG 17 e FR 14; MF, SO, IA, ES2 e
TCC tem ZERO. O handoff registra "163 materiais nos 8 tem Datalab que o motor nunca leu"; nos 7 cursos da regua sao 36
no manifest inteiro e 31 dentro do gold. Por isso a coluna (b) sai DUAS vezes: na regua inteira (onde ela quase nao
muda nada, por construcao) e na FATIA de 31 (a unica comparacao honesta).

O motor pontua `base_markdown`; `advanced_markdown` e a ultima opcao na precedencia
(`navigation._entry_markdown_path_for_file_map`: approved > curated > base > advanced). Aqui a precedencia e invertida
so para (b), em memoria, sem tocar em disco.

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/tres_configuracoes_12-09.py
"""
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
from src.builder.routing.revisar import revisar_de  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]
_getmd_orig = rp.getmd


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


def com_datalab(root_da_copia):
    """getmd que PREFERE o advanced_markdown (Datalab) quando o arquivo existe."""
    def getmd(root, e):
        rel = str(e.get("advanced_markdown") or "")
        if rel:
            p = Path(root) / rel
            if p.exists():
                try:
                    return p.read_text(encoding="utf-8")
                except Exception:
                    pass
        return _getmd_orig(root, e)
    return getmd


def gold_rows(sig):
    p = Path(f"docs/reports/subunit_gt_{sig}.csv")
    return {r["entry_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


def mede(sig, regime, datalab):
    rp.getmd = com_datalab(None) if datalab else _getmd_orig
    try:
        taxmod = sem_llm(sig) if regime == "cru" else None
        return rp.evaluate(sig, "com", new=False, taxmod=taxmod, escopo="produto")
    finally:
        rp.getmd = _getmd_orig


CONFIGS = [("(a) CRU", "cru", False), ("(b) CRU+DATALAB", "cru", True), ("(c) PRODUTO", "produto", False)]
res, tem_adv = {}, {}
for sig in CURSOS:
    man = {e["id"]: e for e in json.loads((Path("..") / rp.NAMES[sig] / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    gold = gold_rows(sig)
    tem_adv[sig] = {eid for eid in gold if (man.get(eid) or {}).get("advanced_markdown")}
    for nome, regime, dl in CONFIGS:
        r = mede(sig, regime, dl)
        ents = {e["id"]: e for e in r[6]}
        linha = {}
        for eid, row in gold.items():
            ac = ({row["gold_subunit"]} | set(filter(None, row.get("gold_subunits_extra", "").split(";")))
                  if row["gold_subunit"] else {""})
            p = r[3].get(eid, "")
            e = ents.get(eid)
            linha[eid] = dict(pred=p, aceito=int(p in ac), prim=int(p == row["gold_subunit"]),
                              conf=int(e is not None and revisar_de(e) not in ("duvida", "mudou")))
        res[(sig, nome)] = linha


def placar(nome, ids_por_curso):
    n = ac = pr = cf = cfa = 0
    for sig in CURSOS:
        ids = ids_por_curso(sig)
        for eid in ids:
            d = res[(sig, nome)].get(eid)
            if not d:
                continue
            n += 1; ac += d["aceito"]; pr += d["prim"]
            if d["conf"]:
                cf += 1; cfa += d["aceito"]
    return n, ac, pr, cf, cfa


print("SUBUNIDADE, as tres configuracoes — REGUA INTEIRA (251 materiais, 7 cursos)")
print(f"{'configuracao':18} {'n':>4} {'aceito':>14} {'primario':>14} {'confiantes':>11} {'aceito do confiante':>21} {'entrega':>14}")
for nome, _, _ in CONFIGS:
    n, ac, pr, cf, cfa = placar(nome, lambda s: set(res[(s, nome)]))
    print(f"{nome:18} {n:>4} {ac:>6} {ac/n:>7.1%} {pr:>6} {pr/n:>7.1%} {cf:>11} {cfa:>6}/{cf:<5} {cfa/max(1,cf):>6.1%} {cfa:>6}/{n} {cfa/n:>6.1%}")

print()
print("SUBUNIDADE, so a FATIA COM DATALAB (a unica comparacao honesta de (b))")
falt = {s: len(tem_adv[s]) for s in CURSOS}
print(f"  materiais com Datalab por curso: " + " · ".join(f"{s} {falt[s]}" for s in CURSOS) + f"  = {sum(falt.values())} de 251")
print(f"{'configuracao':18} {'n':>4} {'aceito':>14} {'primario':>14} {'confiantes':>11} {'aceito do confiante':>21}")
for nome, _, _ in CONFIGS:
    n, ac, pr, cf, cfa = placar(nome, lambda s: tem_adv[s])
    print(f"{nome:18} {n:>4} {ac:>6} {ac/max(1,n):>7.1%} {pr:>6} {pr/max(1,n):>7.1%} {cf:>11} {cfa:>6}/{cf:<5} {cfa/max(1,cf):>6.1%}")

print()
print("O QUE O DATALAB MUDA, material a material (so onde ele existe):")
mud = 0
for sig in CURSOS:
    for eid in sorted(tem_adv[sig]):
        a = res[(sig, "(a) CRU")][eid]
        b = res[(sig, "(b) CRU+DATALAB")][eid]
        if a["pred"] != b["pred"]:
            mud += 1
            sinal = "GANHA" if b["aceito"] > a["aceito"] else ("PERDE" if b["aceito"] < a["aceito"] else "troca")
            print(f"  {sig:4} {eid:46} {sinal:6} cru={a['pred'] or '(vazio)':38} datalab={b['pred'] or '(vazio)'}")
print(f"  ({mud} de {sum(falt.values())} materiais com Datalab mudam de predicao)")
