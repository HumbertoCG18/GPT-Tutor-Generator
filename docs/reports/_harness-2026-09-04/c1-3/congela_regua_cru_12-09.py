"""Passo 0 da frente 'regime cru' (handoff 12/09 §7): CONGELAR A REGUA.

Refaz a partida de `replay_regime_cru_12-09.py` corrigindo o que o passo 0 pede e o que a auditoria de 12/09
encontrou no caminho:
  (a) ESCOPO. O replay historico processava `category in CATEGORIAS or computed_block_id`; o produto processa
      `_is_material and (bloco or bloco temporal or categoria sem eixo temporal)`. No CG isso eram 68 de 93
      entradas, e as 25 puladas ficavam com o `computed_subunit_slug` DO MANIFEST DO PRODUTO -- 22 delas estao
      no gold e o "regime cru" marcava 16 aceito / 14 primario herdados de uma decisao tomada COM vocabulario
      LLM. Aqui a regua roda em `escopo="produto"`; o escopo historico sai ao lado, para rastrear a mudanca.
  (b) toda tabela sai com ACEITO **e** PRIMARIO (e o denominador n de cada curso);
  (c) a lista de erros sai com a coluna GOLD (primario + extras) e com os slugs INTEIROS, sem truncar;
  (d) sai tambem um CSV com os 251 materiais (nao so os erros), para o brief e para diffs futuros.

Regimes de taxonomia (identicos aos de 12/09, para o numero nao mudar de significado):
  produto   = taxonomia como esta em disco (codigo + plano + manual + LLM)
  sem_llm   = tira os sinonimos vindos de `course/.glossary_curation.llm.json` (cru + curadoria humana)
  so_codigo = fica so o alias que comeca com digito (codigo de outline): o mais cru possivel

Metricas (definicao em `replay_subunidade.evaluate`):
  ACEITO   = pred ∈ {gold_subunit} ∪ gold_subunits_extra   (com-extras)
  PRIMARIO = pred == gold_subunit

0 chamadas de rede (socket bloqueado no replay_subunidade). Nao escreve nada no produto nem em .ablacao/.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/congela_regua_cru_12-09.py
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

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]
REGIMES = ["produto", "sem_llm", "so_codigo"]


def llm_norms(sig):
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    if not p.exists():
        return set()
    d = json.loads(p.read_text(encoding="utf-8"))
    return {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}


def sem_llm(sig):
    vet = llm_norms(sig)

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
    """entry_id -> linha do gold (so scorable=yes), igual ao filtro de replay_subunidade.load."""
    p = Path(f"docs/reports/subunit_gt_{sig}.csv")
    return {r["entry_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


def corre(sig, escopo):
    return {
        "produto": rp.evaluate(sig, "com", new=False, escopo=escopo),
        "sem_llm": rp.evaluate(sig, "com", new=False, taxmod=sem_llm(sig), escopo=escopo),
        "so_codigo": rp.evaluate(sig, "com", new=False, taxmod=so_codigo, escopo=escopo),
    }


rows_out = []
placar = {esc: {r: {} for r in REGIMES} for esc in ("produto", "replay")}
for sig in CURSOS:
    res = corre(sig, "produto")
    old = corre(sig, "replay")
    gold = gold_rows(sig)
    n = len(res["produto"][2])
    assert n == len(gold), f"{sig}: evaluate {n} != gold {len(gold)}"
    for reg in REGIMES:
        placar["produto"][reg][sig] = (res[reg][0], res[reg][1], n)
        placar["replay"][reg][sig] = (old[reg][0], old[reg][1], n)
    unidade = {e["id"]: e.get("computed_unit_slug", "") for e in res["sem_llm"][6]}
    fora_do_escopo_antigo = set(gold) - old["sem_llm"][8]
    for eid, row in gold.items():
        rec = {"curso": sig, "entry_id": eid,
               "unidade": unidade.get(eid, ""),
               "gold_primario": row["gold_subunit"],
               "gold_extras": row.get("gold_subunits_extra", ""),
               "gold_fonte": row.get("gold_fonte", "")}
        for reg in REGIMES:
            pred = res[reg][3].get(eid, "")
            rec[f"pred_{reg}"] = pred
            rec[f"aceito_{reg}"] = int(bool(res[reg][2].get(eid)))
            rec[f"primario_{reg}"] = int(pred == row["gold_subunit"])
        rec["pred_sem_llm_escopo_antigo"] = old["sem_llm"][3].get(eid, "")
        rec["herdado_no_escopo_antigo"] = int(eid in fora_do_escopo_antigo)
        m = res["sem_llm"][4].get(eid)
        rec["cru_conf_1a"] = f"{getattr(m, 'confidence', 0) or 0:.3f}"
        rec["cru_slug_1a"] = getattr(m, "topic_slug", "") or ""
        rec["cru_reasons_1a"] = " | ".join(getattr(m, "reasons", []) or [])[:300]
        rec["tipo_erro_cru"] = ("ok" if rec["aceito_sem_llm"] else
                                ("vazio" if not rec["pred_sem_llm"] else "trocado"))
        rows_out.append(rec)
    print(f"{sig:4} n={n:3} · " + " · ".join(
        f"{reg} {placar['produto'][reg][sig][0]:3} aceito / {placar['produto'][reg][sig][1]:3} prim"
        for reg in REGIMES), flush=True)

N = sum(placar["produto"]["produto"][s][2] for s in CURSOS)
print()
print(f"== PLACAR CONGELADO (escopo = produto; aceito E primario, base {N}) ==")
print(f"{'regime':10} {'aceito':>14} {'primario':>14}    (escopo antigo do replay)")
for reg in REGIMES:
    a = sum(placar["produto"][reg][s][0] for s in CURSOS)
    p = sum(placar["produto"][reg][s][1] for s in CURSOS)
    ao = sum(placar["replay"][reg][s][0] for s in CURSOS)
    po = sum(placar["replay"][reg][s][1] for s in CURSOS)
    print(f"{reg:10} {a:4}/{N} {a/N:6.1%} {p:4}/{N} {p/N:6.1%}    {ao} aceito / {po} prim")

print()
print("== POR CURSO (aceito/primario/n), escopo produto ==")
print(f"{'curso':5} {'n':>4} " + " ".join(f"{reg:>18}" for reg in REGIMES))
for sig in CURSOS:
    print(f"{sig:5} {placar['produto']['produto'][sig][2]:>4} " + " ".join(
        f"{placar['produto'][reg][sig][0]:>7}/{placar['produto'][reg][sig][1]:<10}" for reg in REGIMES))

herd = [r for r in rows_out if r["herdado_no_escopo_antigo"]]
print()
print(f"== VAZAMENTO DO ESCOPO ANTIGO: {len(herd)} materiais do gold nao eram recalculados pelo replay "
      f"(ficavam com o valor do manifest do produto)")
print(f"   desses, o escopo antigo marcava {sum(1 for r in herd if r['pred_sem_llm_escopo_antigo'] and (r['pred_sem_llm_escopo_antigo'] in ({r['gold_primario']} | set(filter(None, r['gold_extras'].split(';'))))))} aceito no regime cru; "
      f"no escopo corrigido o cru marca {sum(r['aceito_sem_llm'] for r in herd)}")
for r in herd:
    print(f"   {r['curso']:4} {r['entry_id']}")
    print(f"        gold  : {r['gold_primario'] or '(vazio)'}"
          f"{' [extras: ' + r['gold_extras'] + ']' if r['gold_extras'] else ''}")
    print(f"        antigo: {r['pred_sem_llm_escopo_antigo'] or '(vazio)'}   (herdado do produto)")
    print(f"        cru   : {r['pred_sem_llm'] or '(vazio)'}   (recalculado)")

erros = [r for r in rows_out if not r["aceito_sem_llm"]]
nprim = [r for r in rows_out if not r["primario_sem_llm"]]
vaz = sum(1 for r in erros if r["tipo_erro_cru"] == "vazio")
print()
print(f"== ERROS DO REGIME CRU (sem_llm) por ACEITO: {len(erros)} "
      f"({vaz} vazios · {len(erros) - vaz} trocados; produto acerta {sum(1 for r in erros if r['aceito_produto'])})")
print(f"== nao-primarios no mesmo regime: {len(nprim)}")
print()
for r in erros:
    extras = f" [extras: {r['gold_extras']}]" if r["gold_extras"] else ""
    print(f"{r['curso']:4} {r['entry_id']}")
    print(f"     GOLD     : {r['gold_primario'] or '(vazio)'}{extras}")
    print(f"     CRU      : {r['pred_sem_llm'] or '(vazio)'}   [{r['tipo_erro_cru']}, conf 1a {r['cru_conf_1a']}]")
    print(f"     PRODUTO  : {r['pred_produto'] or '(vazio)'}   [{'acerta' if r['aceito_produto'] else 'erra'}]")
    print(f"     SO_CODIGO: {r['pred_so_codigo'] or '(vazio)'}   [{'acerta' if r['aceito_so_codigo'] else 'erra'}]")
    print(f"     UNIDADE  : {r['unidade']}")

out = HERE / "congela_regua_cru_12-09.csv"
cols = ["curso", "entry_id", "unidade", "gold_primario", "gold_extras", "gold_fonte",
        "pred_produto", "aceito_produto", "primario_produto",
        "pred_sem_llm", "aceito_sem_llm", "primario_sem_llm",
        "pred_so_codigo", "aceito_so_codigo", "primario_so_codigo",
        "tipo_erro_cru", "cru_conf_1a", "cru_slug_1a", "cru_reasons_1a",
        "pred_sem_llm_escopo_antigo", "herdado_no_escopo_antigo"]
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows_out)
print()
print(f"CSV dos {len(rows_out)} materiais: {out}")
