"""AUTODOACAO x GANHO TRANSFERIVEL, material a material, para um braco de relacoes (14/09).

Para cada material cuja subunidade mudou entre o snapshot do braco C (base) e o do braco: o material le o MESMO arquivo que
doou alguma relacao para o topico que ele passou a escolher? Se sim, e autodoacao (entrada legitima, nao transferivel).
Separa ganho e perda transferiveis no primario e no aceito; lista as mudancas em material SEM gold (a regua nao ve).

0 chamadas. Uso: PYTHONUTF8=1 python -B autodoacao_14-09.py <regime>   (le relacoes_<regime>_14-09.json e snapshot_braco_<regime>_14-09.csv)
"""
import collections
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GH = HERE.parents[4]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}


def main():
    R = sys.argv[1]
    rel = json.loads((HERE / f"relacoes_{R}_14-09.json").read_text(encoding="utf-8"))["relacoes"]
    fontes = collections.defaultdict(set)
    for r in rel:
        fontes[r["curso"]].add(r["fonte"].split(":")[0])
    man = {c: {e["id"]: e for e in json.loads((GH / n / "manifest.json").read_text(encoding="utf-8"))["entries"]}
           for c, n in NOMES.items()}

    def doc(c, eid):
        e = man[c].get(eid) or {}
        for k in ("approved_markdown", "curated_markdown", "base_markdown"):
            if e.get(k):
                return Path(e[k]).name
        return ""

    ler = lambda f: {(x["curso"], x["entry_id"]): x for x in csv.DictReader((HERE / f).open(encoding="utf-8-sig", newline=""))}
    base, braco = ler("snapshot_bracoC_14-09.csv"), ler(f"snapshot_braco_{R}_14-09.csv")
    tot = collections.Counter()
    print(f"{'curso':4} {'material':38} {'eixo':12} {'mudanca':8} {'tipo':14} base -> braco")
    for k in sorted(base):
        b, r = base[k], braco.get(k)
        if not r or b["pred_sub"] == r["pred_sub"]:
            continue
        c, eid = k
        auto = doc(c, eid) in fontes[c] and doc(c, eid) != ""
        tipo = "autodoacao" if auto else "transferivel"
        if b["sub_primario"] == "" and b["sub_aceito"] == "":
            tot["mudou_sem_gold"] += 1
            print(f"{c:4} {eid[:36]:38} {'(sem gold)':12} {'':8} {tipo:14} {b['pred_sub'][:24]} -> {r['pred_sub'][:24]}")
            continue
        for eixo in ("sub_primario", "sub_aceito"):
            if b[eixo] != r[eixo]:
                m = "ganho" if r[eixo] == "1" else "perda"
                tot[f"{eixo}_{m}_{tipo}"] += 1
                print(f"{c:4} {eid[:36]:38} {eixo:12} {m:8} {tipo:14} {b['pred_sub'][:24]} -> {r['pred_sub'][:24]}")
    print(f"\nRESUMO {R}: {dict(tot)}")
    for eixo in ("sub_primario", "sub_aceito"):
        g, p = tot[f"{eixo}_ganho_transferivel"], tot[f"{eixo}_perda_transferivel"]
        print(f"  {eixo}: transferivel +{g} -{p} = {g - p:+d} · autodoacao +{tot[f'{eixo}_ganho_autodoacao']} -{tot[f'{eixo}_perda_autodoacao']}")
    print(f"  materiais SEM gold que mudaram: {tot['mudou_sem_gold']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
