"""Os erros de UNIDADE no regime cru, um a um (12/09 noite).

A medicao dos 3 eixos (§19) poe a unidade do regime `regua` em 253/284 = 89,1%, contra a meta de 90% (= 256 de 284).
Aqui saem os 31 erros, com o que o motor decidiu, o que a regua curricular aceita, e o que o PRODUTO decide no mesmo
material — para separar "o cru perde e o produto acerta" de "os dois erram" (teto de dado, nao alavanca).

0 chamadas: le so os manifests da copia `.motor3eixos/` e do produto.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/erros_unidade_cru_12-09.py
"""
import csv
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
ORIG = GEN.parent
COPIA = GEN / ".motor3eixos"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import carrega_regua_unidade  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}

linhas = []
for sig, nm in NOMES.items():
    gu = carrega_regua_unidade(sig)
    if not gu:
        continue
    cp = COPIA / nm / "manifest.json"
    if not cp.exists():
        print(f"  (sem copia para {sig})")
        continue
    cru = {e["id"]: e for e in json.loads(cp.read_text(encoding="utf-8"))["entries"]}
    prod = {e["id"]: e for e in json.loads((ORIG / nm / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    for eid, aceitas in gu.items():
        e = cru.get(eid)
        if e is None:
            continue
        got = str(e.get("computed_unit_slug") or "")
        if got in aceitas:
            continue
        p = prod.get(eid) or {}
        got_p = str(p.get("computed_unit_slug") or "")
        linhas.append(dict(
            curso=sig, entry_id=eid,
            gold=" | ".join(aceitas),
            cru=got or "(vazio)",
            produto=got_p or "(vazio)",
            produto_acerta=int(got_p in aceitas),
            na_fila_cru=int(revisar_de(e) in ("duvida", "mudou")),
            conflito=int(bool(e.get("unit_block_conflict"))),
            bloco_cru=str(e.get("temporal_block_id") or ""),
            metodo_bloco=str(e.get("temporal_block_method") or ""),
            categoria=str(e.get("category") or ""),
        ))

n = len(linhas)
pa = sum(r["produto_acerta"] for r in linhas)
fila = sum(r["na_fila_cru"] for r in linhas)
print(f"ERROS DE UNIDADE no regime cru (configuracao 'regua'): {n}")
print(f"  o PRODUTO acerta {pa} deles e tambem erra {n - pa}")
print(f"  na fila do cru (o motor avisou): {fila} · confiantes e errados: {n - fila}")
print(f"  com conflito unidade x bloco marcado: {sum(r['conflito'] for r in linhas)}")
print()
print("por curso:")
for sig in NOMES:
    s = [r for r in linhas if r["curso"] == sig]
    if s:
        print(f"  {sig:5} {len(s):>3}  (produto acerta {sum(r['produto_acerta'] for r in s):>2} · na fila {sum(r['na_fila_cru'] for r in s):>2})")
print()
print("=" * 140)
for r in linhas:
    print(f"{r['curso']:4} {r['entry_id']:44} ({r['categoria']})")
    print(f"     GOLD   : {r['gold']}")
    print(f"     CRU    : {r['cru']:56} [{'FILA' if r['na_fila_cru'] else 'CONFIANTE'}{', conflito' if r['conflito'] else ''}]")
    print(f"     PRODUTO: {r['produto']:56} [{'acerta' if r['produto_acerta'] else 'ERRA TAMBEM'}]")
    print(f"     bloco  : {r['bloco_cru']} ({r['metodo_bloco']})")

out = Path(__file__).resolve().parent / "erros_unidade_cru_12-09.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
    w.writeheader()
    w.writerows(linhas)
print()
print(f"CSV: {out}")
