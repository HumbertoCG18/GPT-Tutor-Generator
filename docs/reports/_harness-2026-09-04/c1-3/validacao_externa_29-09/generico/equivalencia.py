"""Equivalência de semântica das métricas: roda `avalia` de uma pasta de harness (rodada VOCAB_LIMPO ou genérico) sobre o
cenário sintético da suíte herdada (`test_wad4.py`, idêntico nas duas pastas) e imprime a saída canônica com os braços
renomeados para papéis (CRU, CAND, MAIOR, ALEAT_n). Uso: python equivalencia.py <pasta> [invariancia|bloco_mudou]."""
import json
import sys
from pathlib import Path

PASTA = Path(sys.argv[1]).resolve()
MODO = sys.argv[2] if len(sys.argv) > 2 else "padrao"
sys.path.insert(0, str(PASTA))
import avaliador as AV  # noqa: E402
import comum as K  # noqa: E402
import test_wad4 as T  # noqa: E402

K.INVENTARIO_ESPERADO = 8
K.DENOMINADORES = {"bloco": 0, "unidade": 0, "sub_primaria": 9}
K.DENOM_POR_CURSO = {"S": {"bloco": 0, "unidade": 0, "sub_primaria": 9}}
K.REFERENCIA_CRU = {"S": {"bloco": 0, "unidade": 0, "sub_primaria": 3}}
cru, cand = K.BRACOS[0], K.BRACOS[1]
papel = {cru: "CRU", cand: "CAND", K.BRACOS[2]: "MAIOR", **{b: f"ALEAT_{i}" for i, b in enumerate(K.BRACOS[3:], 1)}}
cong = T.congelamento(T.INV8)
if MODO == "padrao":
    subs_cand = T.SUB_LLM
else:   # candidato só com correções (B sem violação); em "bloco_mudou" um bloco muda por ID
    subs_cand = dict(T.SUB_CRU, e2="t2")
caps = {b: T.captura(cong, b, T.decisoes_de(T.SUB_CRU)) for b in K.BRACOS}
dec = T.decisoes_de(subs_cand)
if MODO == "bloco_mudou":
    dec["S"]["e5"]["final"]["bloco"] = "b2"
caps[cand] = T.captura(cong, cand, dec)
tax = T.tax_de([("u1", [(f"t{i}", []) for i in range(1, 10)])])
r = K.canon(AV.avalia(caps, cong, T.REGUA, {b: {"S": tax} for b in K.BRACOS}))
r.pop("proveniencia")   # hashes de código e de insumos diferem por construção entre as pastas


def renomeia(o):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            k2 = papel.get(k, k)
            if k.startswith("C_meta_"):
                k2 = "C_meta_" + papel.get(k[len("C_meta_"):], k[len("C_meta_"):])
            out[k2] = renomeia(v)
        return out
    if isinstance(o, list):
        return [renomeia(x) for x in o]
    return papel.get(o, o) if isinstance(o, str) else o


sys.stdout.reconfigure(encoding="utf-8")
print(json.dumps(renomeia(r), ensure_ascii=False, sort_keys=True))
