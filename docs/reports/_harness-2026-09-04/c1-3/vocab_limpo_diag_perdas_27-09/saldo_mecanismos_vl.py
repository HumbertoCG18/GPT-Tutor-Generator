"""Saldo por mecanismo das transições da subunidade primária (VOCAB_LIMPO contra CRU_LIMPO), 27/09. Pós-gold.

Para cada ID que mudou de certo/errado, classifica onde a decisão final do VOCAB_LIMPO nasceu: 1ª passada mantida, ou
2ª passada (propagação por headings, seção que nomeia subtópico, outra). Mesma leitura para o CRU_LIMPO. Só lê capturas
congeladas e a avaliação; nada é alterado.
"""
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
C13, DATA = AQUI.parent, AQUI.parents[4]
sys.path.insert(0, str(C13 / "vocab_limpo_26-09"))
import comum as K  # noqa: E402

MAN = K.carrega_json_estrito(C13 / "vocab_limpo_26-09/manifesto_capturas_vl.json")["capturas"]
CAP = {}
for b in ("CRU_LIMPO", "VOCAB_LIMPO"):
    p = DATA / MAN[b]["arquivo"]
    assert K.sha_arq(p) == MAN[b]["sha256"], b
    CAP[b] = K.carrega_json_estrito(p)
AV = K.carrega_json_estrito(C13 / "vocab_limpo_avaliacao_26-09/avaliacao_vl_1.json")


def origem(d):
    motivos = d["final"]["motivos_sub"]
    p1 = (d["p1"] or {}).get("vencedor", {}).get("topico", "")
    if "propagado-headings" in motivos:
        return "2a:propagado-headings"
    if "secao-nomeia-subtopico" in motivos:
        return "2a:secao-nomeia-subtopico"
    if d["final"]["sub"] != p1:
        return "2a:outra"
    return "1a:vazio" if not p1 else "1a"


saldo = collections.defaultdict(lambda: collections.Counter())
for x in AV["comparacoes"]["VOCAB_LIMPO"]["sub_primaria"]["registros"]:
    if x["certo_antes"] == x["certo_depois"] or x["eid"] is None:
        continue
    tipo = "correcao" if x["certo_depois"] else "perda"
    o = origem(CAP["VOCAB_LIMPO"]["decisoes"][x["curso"]][x["eid"]])
    oc = origem(CAP["CRU_LIMPO"]["decisoes"][x["curso"]][x["eid"]])
    saldo[o][tipo] += 1
    saldo[f"cru={oc}"][tipo] += 1
out = {k: dict(v) | {"saldo": v["correcao"] - v["perda"]} for k, v in sorted(saldo.items())}
K.grava_atomico(AQUI / "saldo_mecanismos_vl.json", out)
for k, v in out.items():
    print(f"{k:32s} correções {v.get('correcao', 0):3d}  perdas {v.get('perda', 0):2d}  saldo {v['saldo']:+d}")
