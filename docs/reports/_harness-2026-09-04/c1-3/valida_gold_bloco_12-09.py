"""O gold de BLOCO ainda aponta para os blocos que existem hoje? (12/09 noite, achado do astra)

O medidor dos 3 eixos compara o bloco do material com `true_block_id` (o id POSICIONAL, "bloco-NN"). Se o indice de
blocos foi regenerado desde que o gold foi escrito, "bloco-01" pode ser outro bloco hoje e o acerto seria acidental.

Medido: em MF, SO, IA, ES2 e TCC **100% dos `true_block_uuid` do gold existem no indice atual** — a ancora forte esta
de pe. No **CG, ZERO dos 35** existe: aquele gold foi escrito contra um indice anterior ao rebuild do curso.

Este script revalida o gold por uma ancora INDEPENDENTE do uuid: a coluna `data_real` do gold contra o
`period_start`/`period_end` do bloco no indice atual. Se a data real da aula cai dentro do periodo do bloco que o
`true_block_id` nomeia, o id posicional continua apontando para o mesmo lugar.

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/valida_gold_bloco_12-09.py [--raiz <pasta>]
"""
import argparse
import csv
import json
from datetime import date
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}


def _data(s, ano):
    """'08-04' ou '2026-08-04' -> date. Devolve None se nao der."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        if len(s) == 5 and "-" in s:
            m, d = s.split("-")
            return date(ano, int(m), int(d))
        p = s.split("-")
        if len(p) == 3:
            return date(int(p[0]), int(p[1]), int(p[2]))
    except Exception:
        return None
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=str(GEN.parent))
    a = ap.parse_args(argv)
    raiz = Path(a.raiz)
    print(f"raiz: {raiz}")
    print(f"{'curso':5} {'scorable':>9} {'uuid bate':>10} {'com data_real':>14} {'DATA BATE o bloco':>19} "
          f"{'data FORA do bloco':>20} {'sem como checar':>16}")
    tot = {"n": 0, "uuid": 0, "data": 0, "fora": 0, "sem": 0}
    detalhe = []
    for sig, nm in NOMES.items():
        p = GEN / "docs/reports" / f"ground_truth_{sig}.csv"
        tp = raiz / nm / "course/.timeline_index.json"
        if not p.exists() or not tp.exists():
            continue
        blocos = json.loads(tp.read_text(encoding="utf-8"))["blocks"]
        por_id = {b["id"]: b for b in blocos}
        uuids = {b["block_uuid"] for b in blocos}
        # ano de referencia: o do primeiro periodo do indice
        ano = 2026
        for b in blocos:
            ps = (b.get("period_start") or "")
            if len(ps) >= 4 and ps[:4].isdigit():
                ano = int(ps[:4])
                break
        n = u = d = f = s = 0
        for r in csv.DictReader(p.open(encoding="utf-8-sig")):
            if (r.get("scorable") or "").strip().lower() != "yes":
                continue
            n += 1
            if (r.get("true_block_uuid") or "").strip() in uuids:
                u += 1
            dt = _data(r.get("data_real"), ano)
            bid = (r.get("true_block_id") or "").strip()
            b = por_id.get(bid)
            if dt is None or b is None:
                s += 1
                continue
            ini = _data(b.get("period_start"), ano)
            fim = _data(b.get("period_end"), ano) or ini
            if ini and fim and ini <= dt <= fim:
                d += 1
            else:
                f += 1
                detalhe.append((sig, r.get("id"), bid, r.get("data_real"), b.get("period_start"), b.get("period_end")))
        print(f"{sig:5} {n:>9} {u:>10} {n - s:>14} {d:>19} {f:>20} {s:>16}")
        for k, v in (("n", n), ("uuid", u), ("data", d), ("fora", f), ("sem", s)):
            tot[k] += v
    print(f"{'TOT':5} {tot['n']:>9} {tot['uuid']:>10} {tot['n'] - tot['sem']:>14} {tot['data']:>19} "
          f"{tot['fora']:>20} {tot['sem']:>16}")
    if detalhe:
        print()
        print("LINHAS EM QUE A DATA REAL NAO CAI NO PERIODO DO BLOCO QUE O GOLD NOMEIA:")
        for sig, eid, bid, dr, ps, pe in detalhe:
            print(f"  {sig:4} {str(eid):44} gold={bid:10} data_real={dr:8} bloco atual={ps} a {pe}")
    print()
    print("LEITURA: 'uuid bate' e a ancora forte. Onde ela falha (CG), 'DATA BATE' e a verificacao independente:")
    print("se a data real da aula cai no periodo do bloco que o id posicional nomeia, o gold continua valido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
