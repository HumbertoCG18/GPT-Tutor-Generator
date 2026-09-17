"""Passo 0 §(a): quanto o REPLAY diverge do PRODUTO, material a material, nos 7 cursos.

O handoff 12/09 §2 registra "6 de 7 cursos batem material a material; CG difere em 2 estaveis". Os totais nao
fecham com isso: replay modo `com`/new=False da 217/251 aceito e o produto em disco da 224/251
(`erros_subunidade_produto_12-09b.log`), diferenca de 7. Este script mede a divergencia de verdade: compara o
`computed_subunit_slug` que o replay produz com o que esta no `manifest.json` do tutor em disco, id a id.

Entrada: `congela_regua_cru_12-09.csv` (coluna pred_produto = replay) + ../<Tutor>/manifest.json (produto).
0 chamadas, nao escreve no produto.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/compara_replay_produto_12-09.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NAMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor",
         "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]

rows = list(csv.DictReader((HERE / "congela_regua_cru_12-09.csv").open(encoding="utf-8-sig")))
por_curso = {c: [r for r in rows if r["curso"] == c] for c in CURSOS}

tot_div = 0
detalhe = []
for sig in CURSOS:
    man = json.loads((ROOT.parent / NAMES[sig] / "manifest.json").read_text(encoding="utf-8"))["entries"]
    disco = {e["id"]: (e.get("computed_subunit_slug") or "") for e in man}
    conf = {e["id"]: e.get("subunit_match_confidence") for e in man}
    unid = {e["id"]: (e.get("computed_unit_slug") or "") for e in man}
    div = []
    for r in por_curso[sig]:
        eid = r["entry_id"]
        if eid not in disco:
            div.append((eid, r["pred_produto"], "<AUSENTE no manifest>", r["gold_primario"], r["gold_extras"], "", ""))
            continue
        if disco[eid] != r["pred_produto"]:
            div.append((eid, r["pred_produto"], disco[eid], r["gold_primario"], r["gold_extras"],
                        conf.get(eid), unid.get(eid)))
    tot_div += len(div)
    acertos_replay = sum(1 for r in por_curso[sig] if r["aceito_produto"] == "1")
    aceitos_disco = 0
    for r in por_curso[sig]:
        ok = {r["gold_primario"]} | set(filter(None, r["gold_extras"].split(";"))) if r["gold_primario"] else {""}
        aceitos_disco += disco.get(r["entry_id"], "\0") in ok
    print(f"{sig:4} n={len(por_curso[sig]):3} divergencias={len(div):3} · aceito replay {acertos_replay:3} "
          f"· aceito disco {aceitos_disco:3}", flush=True)
    detalhe.append((sig, div))

print(f"\n== TOTAL de divergencias replay x produto (base 251 do gold): {tot_div}\n")
for sig, div in detalhe:
    if not div:
        continue
    print(f"--- {sig} ({len(div)}) ---")
    for eid, rep, dis, gp, ge, cf, un in div:
        ok = {gp} | set(filter(None, ge.split(";"))) if gp else {""}
        quem = ("disco certo" if dis in ok and rep not in ok else
                "replay certo" if rep in ok and dis not in ok else
                "ambos certos" if rep in ok else "ambos errados")
        print(f"  {eid}")
        print(f"     replay : {rep or '(vazio)'}")
        print(f"     disco  : {dis or '(vazio)'}   [conf {cf}]")
        print(f"     gold   : {gp or '(vazio)'}{' [extras: ' + ge + ']' if ge else ''}   -> {quem}")
        print(f"     unidade: {un}")
    print()
