"""Compara dois snapshots material a material (`snapshot_3eixos_14-09.py`) e aplica o CORTE declarado ANTES do resultado (14/09).

Corte do experimento de relacoes explicitas (astra, §38.6), fixado antes de qualquer braco rodar:
  CONTINUA se, nos 7 cursos:  >= 5 ganhos no sub_primario  E  >= 5 ganhos no sub_aceito  E  ZERO perdas em qualquer eixo
  (bloco, unidade, sub_aceito, sub_primario). Ganho = 0 -> 1; perda = 1 -> 0; so conta material presente nos dois.

Imprime ganhos e perdas por eixo, por curso, e a lista nominal. O veredito sai numa linha propria.

0 chamadas. Uso: python -B compara_snapshots_14-09.py --base snapshot_bracoC_14-09.csv --braco snapshot_bracoR_14-09.csv
"""
import argparse
import collections
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EIXOS = ("bloco", "unidade", "sub_aceito", "sub_primario")
MIN_PRIM, MIN_ACEITO = 5, 5


def ler(p):
    p = Path(p) if Path(p).is_absolute() else HERE / p
    return {(r["curso"], r["entry_id"]): r for r in csv.DictReader(p.open(encoding="utf-8-sig", newline=""))}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--braco", required=True)
    a = ap.parse_args(argv)
    base, braco = ler(a.base), ler(a.braco)
    comuns = sorted(set(base) & set(braco))
    print(f"materiais: base {len(base)} · braco {len(braco)} · em comum {len(comuns)}")
    ganhos = collections.defaultdict(list)
    perdas = collections.defaultdict(list)
    for k in comuns:
        for eixo in EIXOS:
            b, r = base[k][eixo], braco[k][eixo]
            if b == "" or r == "":
                continue
            if b == "0" and r == "1":
                ganhos[eixo].append(k)
            elif b == "1" and r == "0":
                perdas[eixo].append(k)

    print(f"\n{'eixo':14} {'ganhos':>7} {'perdas':>7} {'saldo':>6}")
    for eixo in EIXOS:
        print(f"{eixo:14} {len(ganhos[eixo]):>7} {len(perdas[eixo]):>7} {len(ganhos[eixo]) - len(perdas[eixo]):>+6}")

    print("\npor curso (ganhos/perdas):")
    cursos = sorted({c for c, _ in comuns})
    for c in cursos:
        partes = [f"{e} +{sum(1 for x in ganhos[e] if x[0] == c)}/-{sum(1 for x in perdas[e] if x[0] == c)}" for e in EIXOS]
        print(f"  {c:4} " + " · ".join(partes))

    for rotulo, dic in (("GANHOS", ganhos), ("PERDAS", perdas)):
        print(f"\n{rotulo}:")
        for eixo in EIXOS:
            for c, eid in dic[eixo]:
                print(f"  [{eixo:12}] {c:4} {eid[:44]:46} {base[(c, eid)]['pred_sub'][:30]:32} -> {braco[(c, eid)]['pred_sub'][:30]}")

    total_perdas = sum(len(perdas[e]) for e in EIXOS)
    ok = len(ganhos["sub_primario"]) >= MIN_PRIM and len(ganhos["sub_aceito"]) >= MIN_ACEITO and total_perdas == 0
    print(f"\nCORTE (>= {MIN_PRIM} ganhos primario, >= {MIN_ACEITO} ganhos aceito, 0 perdas em qualquer eixo): "
          f"{'CONTINUA' if ok else 'ENCERRA'} — primario +{len(ganhos['sub_primario'])}, aceito +{len(ganhos['sub_aceito'])}, "
          f"perdas {total_perdas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
