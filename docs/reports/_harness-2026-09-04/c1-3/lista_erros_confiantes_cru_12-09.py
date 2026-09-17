"""Os ERROS CONFIANTES do regime cru, um a um (12/09 tarde, pergunta do user: "como aumentar o numero do cru?").

`calibra_fila_cru_12-09.py` contou: no cru sao 77 dos 190 confiantes (o motor entrega errado sem avisar), contra 15 de
193 no produto. Este script LISTA esses 77 com o que decide o diagnostico: gold (primario + extras), predicao do cru,
predicao do produto, confianca e `winner_score` da decisao, as reasons (que dizem QUAL passada decidiu), e a unidade.

Sai tambem o cruzamento que interessa: o erro confiante do cru e erro confiante no produto tambem? Se o produto acerta,
o vocabulario do LLM resolveu — e a pergunta vira "que sinal cru substitui aquele alias?". Se o produto tambem erra, o
vocabulario nao e a resposta.

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/lista_erros_confiantes_cru_12-09.py
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
SCORE_RE = re.compile(r"winner_score=([\d.]+)")


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


def gold_rows(sig):
    p = Path(f"docs/reports/subunit_gt_{sig}.csv")
    return {r["entry_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


linhas = []
for sig in CURSOS:
    cru = rp.evaluate(sig, "com", new=False, taxmod=sem_llm(sig), escopo="produto")
    prod = rp.evaluate(sig, "com", new=False, escopo="produto")
    entries = {e["id"]: e for e in cru[6]}
    gold = gold_rows(sig)
    for eid, row in gold.items():
        e = entries.get(eid)
        # `revisar_de` e o criterio da fila (inclui "mudou" por sync_changed, que `motivos_de` nao ve: sao 5
        # materiais). Contar por motivos_de dava 82 confiantes errados em vez dos 77 que o calibra publica.
        if e is None or revisar_de(e) in ("duvida", "mudou"):
            continue
        aceitos = ({row["gold_subunit"]} | set(filter(None, row.get("gold_subunits_extra", "").split(";")))
                   if row["gold_subunit"] else {""})
        p = cru[3].get(eid, "")
        if p in aceitos:
            continue
        reasons = [str(r) for r in (e.get("subunit_match_reasons") or [])]
        m = SCORE_RE.search(" ".join(reasons))
        passada = ("2a:" + next((r for r in reasons if r in
                                 ("propagado-headings", "rotulo-decomposto", "titulo-nomeia-subtopico",
                                  "secao-nomeia-subtopico")), "?")
                   if any(r in reasons for r in ("propagado-headings", "rotulo-decomposto",
                                                 "titulo-nomeia-subtopico", "secao-nomeia-subtopico")) else "1a")
        linhas.append({
            "curso": sig, "entry_id": eid,
            "categoria": e.get("category") or "", "tipo": e.get("file_type") or "",
            "gold_primario": row["gold_subunit"], "gold_extras": row.get("gold_subunits_extra", ""),
            "cru": p, "produto": prod[3].get(eid, ""),
            "produto_acerta": int(prod[3].get(eid, "") in aceitos),
            "conf": f"{float(e.get('subunit_match_confidence') or 0):.3f}",
            "winner_score": m.group(1) if m else "",
            "passada": passada, "reasons": " | ".join(reasons)[:200],
            "unidade": e.get("computed_unit_slug") or "",
            "secao_moodle": e.get("source_section") or "", "titulo": e.get("title") or "",
        })

print(f"ERROS CONFIANTES DO REGIME CRU: {len(linhas)} (o motor entrega errado e NAO poe na fila)")
prod_ok = sum(r["produto_acerta"] for r in linhas)
print(f"  destes, o PRODUTO (com vocab LLM) acerta {prod_ok} e tambem erra {len(linhas) - prod_ok}")
print(f"  decididos na 1a passada: {sum(1 for r in linhas if r['passada'] == '1a')} · na 2a: "
      f"{sum(1 for r in linhas if r['passada'] != '1a')}")
print(f"  com predicao VAZIA: {sum(1 for r in linhas if not r['cru'])}")
print()
print("por curso:")
for sig in CURSOS:
    s = [r for r in linhas if r["curso"] == sig]
    print(f"  {sig:5} {len(s):>3}  (produto acerta {sum(r['produto_acerta'] for r in s):>3})")
print()
print("por passada que decidiu:")
cnt = {}
for r in linhas:
    cnt[r["passada"]] = cnt.get(r["passada"], 0) + 1
for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"  {k:28} {v:>3}")
print()
print("por UNIDADE de destino errado (o colapso: para onde o cru manda tudo):")
cnt = {}
for r in linhas:
    cnt[(r["curso"], r["cru"] or "(vazio)")] = cnt.get((r["curso"], r["cru"] or "(vazio)"), 0) + 1
for (sig, slug), v in sorted(cnt.items(), key=lambda x: -x[1])[:12]:
    print(f"  {sig:5} {slug:52} {v:>3}")
print()
print("=" * 150)
for r in linhas:
    ex = f" [extras: {r['gold_extras']}]" if r["gold_extras"] else ""
    print(f"{r['curso']:4} {r['entry_id']}   ({r['categoria']}/{r['tipo']})")
    print(f"     GOLD    : {r['gold_primario'] or '(vazio)'}{ex}")
    print(f"     CRU     : {r['cru'] or '(vazio)'}   conf {r['conf']} score {r['winner_score'] or '-'} [{r['passada']}]")
    print(f"     PRODUTO : {r['produto'] or '(vazio)'}   [{'acerta' if r['produto_acerta'] else 'ERRA TAMBEM'}]")
    print(f"     reasons : {r['reasons']}")
    print(f"     secao   : {r['secao_moodle']}   | titulo: {r['titulo'][:70]}")

out = HERE / "lista_erros_confiantes_cru_12-09.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
    w.writeheader()
    w.writerows(linhas)
print()
print(f"CSV: {out}")
