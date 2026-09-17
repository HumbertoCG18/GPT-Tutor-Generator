"""Os erros de SUBUNIDADE no motor COMPLETO, regime cru (12/09 noite) — o insumo do ataque a subunidade.

Ate agora a lista de erros vinha do replay (que herda unidade e bloco do produto). Esta sai da copia em que o motor
rodou INTEIRO na configuracao `regua` (curadoria humana, sem vocab LLM, voter off): e a medicao oficial.

Para cada erro: o gold (primario + extras), o que o cru decidiu, o que o PRODUTO decide, se esta na fila, a rota que
decidiu (1a passada / propagacao / rotulo decomposto / titulo / secao) e a unidade — porque erro de subunidade DENTRO da
unidade certa e dano contido, e com a unidade errada e dano grande.

Sai tambem a CONCENTRACAO por (curso, topico do gold), que e o que decide se a alavanca e dirigida ou difusa.

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/erros_subunidade_motor_12-09.py
"""
import collections
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
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}
ROTAS = ("propagado-headings", "rotulo-decomposto", "titulo-nomeia-subtopico", "secao-nomeia-subtopico")

marc = COPIA / "_CONFIG_ATUAL.txt"
print(f"copia em: {marc.read_text(encoding='utf-8').splitlines()[0] if marc.exists() else '(sem marcador)'}")
print()

linhas = []
for sig, nm in NOMES.items():
    cp = COPIA / nm / "manifest.json"
    if not cp.exists():
        continue
    cru = {e["id"]: e for e in json.loads(cp.read_text(encoding="utf-8"))["entries"]}
    prod = {e["id"]: e for e in json.loads((ORIG / nm / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    gu = carrega_regua_unidade(sig)
    p = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    if not p.exists():
        continue
    for r in csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
        if r["scorable"] != "yes":
            continue
        eid = r["entry_id"]
        e = cru.get(eid)
        if e is None:
            continue
        ac = ({r["gold_subunit"]} | set(filter(None, r.get("gold_subunits_extra", "").split(";")))
              if r["gold_subunit"] else {""})
        got = str(e.get("computed_subunit_slug") or "")
        if got in ac:
            continue
        reasons = [str(x) for x in (e.get("subunit_match_reasons") or [])]
        rota = next((x for x in ROTAS if x in reasons), "1a-passada")
        un = str(e.get("computed_unit_slug") or "")
        linhas.append(dict(
            curso=sig, entry_id=eid, gold=r["gold_subunit"], extras=r.get("gold_subunits_extra", ""),
            cru=got, produto=str((prod.get(eid) or {}).get("computed_subunit_slug") or ""),
            produto_acerta=int(str((prod.get(eid) or {}).get("computed_subunit_slug") or "") in ac),
            na_fila=int(revisar_de(e) in ("duvida", "mudou")), rota=rota,
            unidade=un, unidade_certa=int(un in gu.get(eid, (un,))) if eid in gu else -1,
            conf=f"{float(e.get('subunit_match_confidence') or 0):.3f}",
            categoria=str(e.get("category") or ""), tipo=str(e.get("file_type") or ""),
        ))

n = len(linhas)
print(f"ERROS DE SUBUNIDADE no motor completo, regime cru: {n} de 251")
print(f"  o PRODUTO acerta {sum(r['produto_acerta'] for r in linhas)} e tambem erra {n - sum(r['produto_acerta'] for r in linhas)}")
print(f"  na FILA (o motor avisou): {sum(r['na_fila'] for r in linhas)} · confiantes e errados: {n - sum(r['na_fila'] for r in linhas)}")
print(f"  com predicao VAZIA: {sum(1 for r in linhas if not r['cru'])}")
uc = [r for r in linhas if r["unidade_certa"] == 1]
ue = [r for r in linhas if r["unidade_certa"] == 0]
print(f"  DENTRO da unidade certa (dano contido): {len(uc)} · com a unidade TAMBEM errada (dano grande): {len(ue)}"
      f" · sem regua de unidade: {n - len(uc) - len(ue)}")
print()
print("por rota que decidiu:")
for k, v in collections.Counter(r["rota"] for r in linhas).most_common():
    s = [r for r in linhas if r["rota"] == k]
    print(f"  {k:26} {v:>3}  (produto acerta {sum(x['produto_acerta'] for x in s):>3})")
print()
print("por curso:")
for sig in NOMES:
    s = [r for r in linhas if r["curso"] == sig]
    if s:
        print(f"  {sig:5} {len(s):>3}  (produto acerta {sum(r['produto_acerta'] for r in s):>3} · na fila {sum(r['na_fila'] for r in s):>3})")
print()
print("CONCENTRACAO por (curso, topico do gold) — decide se a alavanca e dirigida ou difusa:")
cnt = collections.Counter((r["curso"], r["gold"]) for r in linhas)
acc = 0
for i, ((sig, slug), v) in enumerate(cnt.most_common(15), 1):
    acc += v
    print(f"  {i:>2}. {sig:4} {slug:52} {v:>3}   (acumulado {acc:>3} de {n} = {acc/n:.0%})")
print(f"  ... {len(cnt)} pares no total")
print()
print("=" * 150)
for r in linhas:
    ex = f" [extras: {r['extras']}]" if r["extras"] else ""
    print(f"{r['curso']:4} {r['entry_id']:46} ({r['categoria']}/{r['tipo']})")
    print(f"     GOLD   : {r['gold'] or '(vazio)'}{ex}")
    print(f"     CRU    : {r['cru'] or '(vazio)':50} conf {r['conf']} rota={r['rota']} "
          f"[{'FILA' if r['na_fila'] else 'CONFIANTE'}]")
    print(f"     PRODUTO: {r['produto'] or '(vazio)':50} [{'acerta' if r['produto_acerta'] else 'ERRA TAMBEM'}]")
    print(f"     unidade: {r['unidade']} [{'certa' if r['unidade_certa'] == 1 else 'ERRADA' if r['unidade_certa'] == 0 else 'sem regua'}]")

out = Path(__file__).resolve().parent / "erros_subunidade_motor_12-09.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
    w.writeheader()
    w.writerows(linhas)
print()
print(f"CSV: {out}")
