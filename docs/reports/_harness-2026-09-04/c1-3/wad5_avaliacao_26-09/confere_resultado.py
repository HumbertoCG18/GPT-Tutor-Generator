"""Conferência independente do resultado do avaliador congelado (26/09): recalcula os agregados a partir dos registros
por ID, confere somas, saldos e denominadores, e grava tabelas por ID para auditoria. Não muda nada do resultado."""
import collections
import csv
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "wad5_25-09"))
import comum as K  # noqa: E402

R = json.loads((AQUI / "avaliacao_espelho_1.json").read_text(encoding="utf-8"))
EIXOS = ("bloco", "unidade", "sub_primaria", "sub_aceita")
CURSOS = list(K.NOMES)
ok, notas = {}, []


def marca(nome, cond):
    ok[nome] = bool(cond)
    print(("OK    " if cond else "FALHA ") + nome, flush=True)


# 1. placar = registros por ID; somas por curso = total; denominadores
for b in K.BRACOS:
    regs = R["registros"][b]
    c = collections.defaultdict(lambda: [0, 0])
    for x in regs:
        c[(x["curso"], x["eixo"])][1] += 1
        c[(x["curso"], x["eixo"])][0] += int(x["certo"])
    pl = R["placar"][b]
    marca(f"{b}: placar por curso = registros por ID",
          all(pl[s][e] == {"acertos": c[(s, e)][0], "n": c[(s, e)][1]} for s in CURSOS for e in EIXOS))
    marca(f"{b}: soma dos cursos = TOTAL",
          all(pl["TOTAL"][e] == {"acertos": sum(pl[s][e]["acertos"] for s in CURSOS), "n": sum(pl[s][e]["n"] for s in CURSOS)} for e in EIXOS))
    marca(f"{b}: denominadores por curso = pré-registrados",
          all(pl[s][e]["n"] == K.DENOM_POR_CURSO[s][e] for s in CURSOS for e in ("bloco", "unidade", "sub_primaria"))
          and all(pl["TOTAL"][e]["n"] == K.DENOMINADORES[e] for e in ("bloco", "unidade", "sub_primaria"))
          and all(pl[s]["sub_aceita"]["n"] == pl[s]["sub_primaria"]["n"] for s in CURSOS))
marca("CRU = referência pré-registrada por curso e eixo oficial",
      all(R["placar"]["CRU"][s][e]["acertos"] == K.REFERENCIA_CRU[s][e] for s in CURSOS for e in ("bloco", "unidade", "sub_primaria")))

# 2. transições: células = registros; correções − perdas = diferença de acertos; derivadas recalculadas por ID
for b, v in R["comparacoes"].items():
    for e, tr in v.items():
        regs = tr["registros"]
        cor = sum(1 for x in regs if not x["certo_antes"] and x["certo_depois"])
        per = sum(1 for x in regs if x["certo_antes"] and not x["certo_depois"])
        d = R["placar"][b]["TOTAL"][e]["acertos"] - R["placar"]["CRU"]["TOTAL"][e]["acertos"]
        cond = (sum(tr["celulas"].values()) == len(regs) == R["placar"][b]["TOTAL"][e]["n"]
                and tr["derivadas"].get("correcao", 0) == cor and tr["derivadas"].get("perda", 0) == per and cor - per == d)
        alt = [x for x in regs if x["mudou"]]
        cond = cond and tr["precisao_alteradas"]["den"] == len(alt) and tr["precisao_alteradas"]["num"] == sum(x["certo_depois"] for x in alt)
        ok.setdefault("transições: células, correções, perdas, saldo e precisão = registros por ID", True)
        ok["transições: células, correções, perdas, saldo e precisão = registros por ID"] &= cond
print(("OK    " if ok["transições: células, correções, perdas, saldo e precisão = registros por ID"] else "FALHA ")
      + "transições: células, correções, perdas, saldo e precisão = registros por ID")

# 3. registros de captura intactos: cada registro por ID aponta um eid do inventário ou None (material ausente)
cong = K.carrega_json_estrito(AQUI.parents[4] / ".frzero/wad5_25-09/congelamento.json")
inv = {s: set(v) for s, v in cong["normativo"]["inventario"].items()}
marca("registros por ID: eid no inventário congelado ou ausente explícito",
      all(x["eid"] is None or x["eid"] in inv[x["curso"]] for b in K.BRACOS for x in R["registros"][b]))

# tabelas por ID (auditoria)
with open(AQUI / "transicoes_por_id.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["braco", "eixo", "curso", "gold_id", "eid", "cru", "braco_saida", "certo_cru", "certo_braco", "mudou"])
    for b, v in R["comparacoes"].items():
        for e, tr in v.items():
            for x in tr["registros"]:
                if x["mudou"] or x["certo_antes"] != x["certo_depois"]:
                    w.writerow([b, e, x["curso"], x["gold_id"], x["eid"], x["antes"], x["depois"],
                                int(x["certo_antes"]), int(x["certo_depois"]), int(x["mudou"])])
with open(AQUI / "placar_por_curso.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["braco", "curso", "eixo", "acertos", "n"])
    for b in K.BRACOS:
        for s in CURSOS + ["TOTAL"]:
            for e in EIXOS:
                p = R["placar"][b][s][e]
                w.writerow([b, s, e, p["acertos"], p["n"]])
res = {"aprovado": all(ok.values()), "condicoes": ok, "avaliacao_sha256": K.sha_arq(AQUI / "avaliacao_espelho_1.json")}
K.grava_atomico(AQUI / "conferencia_resultado.json", res)
print("CONFERENCIA", "APROVADA" if res["aprovado"] else "REPROVADA")
