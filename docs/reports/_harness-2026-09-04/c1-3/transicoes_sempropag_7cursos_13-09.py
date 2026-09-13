"""Transicoes material a material do braco `sempropag` nos 7 cursos contra o braco C (cru honesto), eixo subunidade (13/09).

O `.motor3eixos/` guarda UMA configuracao por vez, entao os manifests do braco C nao existem mais. A referencia congelada
e `erros_subunidade_cru_honesto_13-09.csv` — os 109 erros de ACEITO do braco C, gerados daquela copia. Com ela:
  GANHO  = estava na lista de erros do C e agora esta certo (aceito)
  PERDA  = NAO estava na lista de erros do C (logo, certo no C) e agora esta errado (aceito)
O PRIMARIO do C nao e reconstruivel material a material por este caminho (o CSV so tem os erros de aceito); o agregado do
primario vem do log do motor. Aborta se a copia nao estiver na configuracao `sempropag`.

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/transicoes_sempropag_7cursos_13-09.py
"""
import collections
import csv
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
COPIA = GEN / ".motor3eixos"
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}


def main():
    marc = (COPIA / "_CONFIG_ATUAL.txt").read_text(encoding="utf-8") if (COPIA / "_CONFIG_ATUAL.txt").exists() else ""
    if "braco-motor=sempropag" not in marc or "SEM curadoria do benchmark=puro" not in marc:
        print(f"ABORTA: a copia nao esta em 'regua + puro + sempropag'. Marcador: {marc.strip()!r}")
        return 1
    erros_c = {(r["curso"], r["entry_id"]): r for r in
               csv.DictReader((HERE / "erros_subunidade_cru_honesto_13-09.csv").open(encoding="utf-8-sig", newline=""))}

    ganhos, perdas = [], []
    por = collections.Counter()
    for sig, nome in NOMES.items():
        gold = {}
        for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
            if r["scorable"] == "yes":
                gold[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
        for e in json.loads((COPIA / nome / "manifest.json").read_text(encoding="utf-8"))["entries"]:
            if e["id"] not in gold:
                continue
            agora = str(e.get("computed_subunit_slug") or "")
            ok = agora in gold[e["id"]]
            era_erro = (sig, e["id"]) in erros_c
            razoes = [x for x in (e.get("subunit_match_reasons") or []) if not str(x).startswith("winner")]
            if era_erro and ok:
                ganhos.append((sig, e["id"], erros_c[(sig, e["id"])]["cru"], agora, razoes))
                por[(sig, "ganho")] += 1
            elif not era_erro and not ok:
                perdas.append((sig, e["id"], agora, sorted(gold[e["id"]]), razoes))
                por[(sig, "perda")] += 1

    print(f"SUBUNIDADE ACEITO, sempropag x braco C, material a material: GANHOS {len(ganhos)} · PERDAS {len(perdas)} · "
          f"saldo {len(ganhos) - len(perdas):+d}\n")
    print(f"{'curso':6} {'ganhos':>7} {'perdas':>7} {'saldo':>6}")
    for sig in NOMES:
        g, p = por[(sig, "ganho")], por[(sig, "perda")]
        print(f"{sig:6} {g:>7} {p:>7} {g - p:>+6}")
    print("\nGANHOS (era erro no C, agora certo):")
    for sig, i, antes, agora, rz in ganhos:
        print(f"  {sig:4} {i[:40]:42} {antes[:30] or '(vazio)':32} -> {agora[:30]} {rz}")
    print("\nPERDAS (era certo no C, agora errado):")
    for sig, i, agora, g, rz in perdas:
        print(f"  {sig:4} {i[:40]:42} agora {agora[:30] or '(vazio)':32} gold {g} {rz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
