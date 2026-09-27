"""Conferência independente do resultado do avaliador congelado da rodada VOCAB_LIMPO (§15 da autorização).

Adaptação de ../wad5_avaliacao_26-09/confere_resultado.py (nomes da rodada) + recálculo das derivadas por ID, veredictos
A_limpo/B_limpo/C_limpo pelos critérios literais do §12, identidade das duas execuções e hashes de entrada depois da
avaliação. Não muda nada do resultado. Grava tabelas por ID e um resumo para o relatório.
"""
import collections
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
DATA = AQUI.parents[4]
PACOTE = AQUI.parent / "vocab_limpo_26-09"
sys.path.insert(0, str(PACOTE))
import comum as K  # noqa: E402

A1, A2 = AQUI / "avaliacao_vl_1.json", AQUI / "avaliacao_vl_2_conferencia.json"
R = K.carrega_json_estrito(A1)
EIXOS = ("bloco", "unidade", "sub_primaria", "sub_aceita")
OFICIAIS = ("bloco", "unidade", "sub_primaria")
CURSOS = list(K.NOMES)
CONTROLES = ("CRU_LIMPO", "CTRL_MAIOR_LIMPO", "CTRL_ALEAT_LIMPO_1", "CTRL_ALEAT_LIMPO_2", "CTRL_ALEAT_LIMPO_3")
ok = {}


def marca(nome, cond):
    ok[nome] = ok.get(nome, True) and bool(cond)


# 0. as duas execuções
marca("execução original e de conferência byte-idênticas", A1.read_bytes() == A2.read_bytes())

# 1. placar = registros por ID; somas por curso = total; denominadores; CRU_LIMPO = referência
for b in K.BRACOS:
    c = collections.defaultdict(lambda: [0, 0])
    for x in R["registros"][b]:
        c[(x["curso"], x["eixo"])][1] += 1
        c[(x["curso"], x["eixo"])][0] += int(x["certo"])
    pl = R["placar"][b]
    marca("placar por curso = registros por ID (todos os braços)",
          all(pl[s][e] == {"acertos": c[(s, e)][0], "n": c[(s, e)][1]} for s in CURSOS for e in EIXOS))
    marca("soma dos cursos = TOTAL (todos os braços)",
          all(pl["TOTAL"][e] == {"acertos": sum(pl[s][e]["acertos"] for s in CURSOS), "n": sum(pl[s][e]["n"] for s in CURSOS)}
              for e in EIXOS))
    marca("denominadores por curso e total = oficiais; aceita com o n da primária",
          all(pl[s][e]["n"] == K.DENOM_POR_CURSO[s][e] for s in CURSOS for e in OFICIAIS)
          and all(pl["TOTAL"][e]["n"] == K.DENOMINADORES[e] for e in OFICIAIS)
          and all(pl[s]["sub_aceita"]["n"] == pl[s]["sub_primaria"]["n"] for s in CURSOS))
marca("CRU_LIMPO = referência por curso e eixo oficial (223/249/86)",
      all(R["placar"]["CRU_LIMPO"][s][e]["acertos"] == K.REFERENCIA_CRU[s][e] for s in CURSOS for e in OFICIAIS)
      and [R["placar"]["CRU_LIMPO"]["TOTAL"][e]["acertos"] for e in OFICIAIS] == [223, 249, 86])

# 2. transições: células = registros = n; derivadas e precisões recalculadas por ID; correções − perdas = diferença
DEF = {"correcao": lambda x: not x["certo_antes"] and x["certo_depois"],
       "perda": lambda x: x["certo_antes"] and not x["certo_depois"],
       "erro_para_outro_erro": lambda x: not x["certo_antes"] and not x["certo_depois"] and x["mudou"],
       "correta_para_outra_correta": lambda x: x["certo_antes"] and x["certo_depois"] and x["mudou"],
       "abstencao_para_certa": lambda x: x["vazio_antes"] and not x["vazio_depois"] and x["certo_depois"],
       "abstencao_para_errada": lambda x: x["vazio_antes"] and not x["vazio_depois"] and not x["certo_depois"],
       "decisao_para_vazio": lambda x: not x["vazio_antes"] and x["vazio_depois"]}
por_curso = {}
for b, v in R["comparacoes"].items():
    for e, tr in v.items():
        regs = tr["registros"]
        der = {k: sum(1 for x in regs if f(x)) for k, f in DEF.items()}
        d = R["placar"][b]["TOTAL"][e]["acertos"] - R["placar"]["CRU_LIMPO"]["TOTAL"][e]["acertos"]
        alt = [x for x in regs if x["mudou"]]
        nv = [x for x in alt if not x["vazio_depois"]]
        marca("transições: células = registros = n do eixo",
              sum(tr["celulas"].values()) == len(regs) == R["placar"][b]["TOTAL"][e]["n"])
        marca("transições: derivadas = recálculo por ID", {k: n for k, n in der.items() if n} == tr["derivadas"])
        marca("transições: correções − perdas = diferença de acertos", der["correcao"] - der["perda"] == d)
        marca("precisão sobre TODAS as alteradas = recálculo por ID",
              tr["precisao_alteradas"]["den"] == len(alt) and tr["precisao_alteradas"]["num"] == sum(x["certo_depois"] for x in alt))
        marca("precisão das alteradas não vazias = recálculo por ID",
              tr["precisao_alteradas_nao_vazias"]["den"] == len(nv)
              and tr["precisao_alteradas_nao_vazias"]["num"] == sum(x["certo_depois"] for x in nv))
        por_curso.setdefault(b, {})[e] = {s: {k: sum(1 for x in regs if x["curso"] == s and f(x)) for k, f in DEF.items()}
                                          for s in CURSOS}
# categorias derivadas se sobrepõem (não são partição): ex. abstenção→certa ⊂ correção
tr = R["comparacoes"]["VOCAB_LIMPO"]["sub_primaria"]["registros"]
ids = {k: {(x["curso"], x["gold_id"]) for x in tr if f(x)} for k, f in DEF.items()}
marca("derivadas sobrepostas tratadas como sobrepostas (abstenção→certa ⊆ correção; abstenção→errada ⊆ erro→erro)",
      ids["abstencao_para_certa"] <= ids["correcao"] and ids["abstencao_para_errada"] <= ids["erro_para_outro_erro"])

# 3. registros por ID apontam um eid do inventário congelado ou material ausente explícito
cong = K.carrega_json_estrito(DATA / ".frzero/vocab_limpo_26-09/captura/congelamento.json")
inv = {s: set(v) for s, v in cong["normativo"]["inventario"].items()}
marca("registros por ID: eid no inventário congelado ou ausente explícito",
      all(x["eid"] is None or x["eid"] in inv[x["curso"]] for b in K.BRACOS for x in R["registros"][b]))

# 4. veredictos pelos critérios literais do §12 (independentes do texto do avaliador)
sp = {b: R["placar"][b]["TOTAL"]["sub_primaria"]["acertos"] for b in K.BRACOS}
A = all(sp["VOCAB_LIMPO"] > sp[c] for c in CONTROLES)
comp = R["comparacoes"]["VOCAB_LIMPO"]
perdas = {e: sum(1 for x in comp[e]["registros"] if DEF["perda"](x)) for e in OFICIAIS}
regride = {e: [s for s in CURSOS if R["placar"]["VOCAB_LIMPO"][s][e]["acertos"] < R["placar"]["CRU_LIMPO"][s][e]["acertos"]]
           for e in OFICIAIS}
B = sp["VOCAB_LIMPO"] > sp["CRU_LIMPO"] and not any(perdas.values()) and not any(regride.values())
C = {s: {e: (R["placar"]["VOCAB_LIMPO"][s][e]["acertos"] * 10 > 9 * R["placar"]["VOCAB_LIMPO"][s][e]["n"])
         if R["placar"]["VOCAB_LIMPO"][s][e]["n"] else "não aplicável" for e in OFICIAIS} for s in CURSOS}
C_total = all(v is True for m in C.values() for v in m.values() if v != "não aplicável")
v = R["veredictos"]
marca("A_limpo recalculado = avaliador", A == v["A_sinal_exploratorio"] and v["A_detalhe"] == {b: sp[b] for b in v["A_detalhe"]})
marca("B_limpo: perdas e regressões recalculadas = avaliador (só eixos oficiais)",
      perdas == v["B_perdas"] and regride == v["B_cursos_que_regridem"])
marca("B_limpo: texto do avaliador coerente com o recálculo",
      (v["B_integracao"].startswith("sem violação") if B else v["B_integracao"] != "" and not v["B_integracao"].startswith("sem violação")))
marca("C_limpo recalculado (acertos*10 > 9*n) = avaliador", C == v["C_meta_VOCAB_LIMPO"])
marca("aceita auxiliar não veta B (B recalculado sem sub_aceita)", "sub_aceita" not in perdas and "sub_aceita" not in regride)

# 5. hashes de entrada depois da avaliação
MR = K.carrega_json_estrito(PACOTE / "manifesto_rodada_vl.json")
marca("entradas intactas depois da avaliação: 279 hashes do manifesto da rodada",
      all(K.sha_arq(DATA / r) == h for g in ("captura", "chamadas", "pacote", "recompilacao", "sidecars") for r, h in MR[g].items())
      and all(K.sha_arq(DATA / MR[g]["arquivo"]) == MR[g]["sha256"] for g in ("protocolo", "errata_fase1")))
EM = K.carrega_json_estrito(AQUI / "espelho_manifesto_vl.json")
esp = Path(EM["espelho"])
marca("espelho intacto depois da avaliação (régua por blob, manifests e código por sha256)",
      all(K.blob_git((esp / c).read_bytes()) == it["blob_git"] for c, it in EM["regua"].items())
      and all(K.sha_arq(esp / c) == h for d in ("manifestos_referencia", "manifestos_salvos") for c, h in EM[d].items())
      and all(K.sha_arq(esp / "docs/reports/_harness-2026-09-04/c1-3/vocab_limpo_26-09" / n) == h for n, h in EM["codigo"].items()))
pv = R["proveniencia"]
marca("proveniência: id_comum, protocolo, avaliador, comum e capturas = congelados",
      pv["congelamento_id_comum"] == cong["id_comum"] and pv["protocolo_sha"] == cong["normativo"]["protocolo_sha"]
      and pv["avaliador_sha"] == cong["normativo"]["codigo"]["avaliador.py"] and pv["comum_sha"] == cong["normativo"]["codigo"]["comum.py"]
      and pv["insumos_braco"] == cong["insumos_braco"]
      and set(pv["regua"]["arquivos_conferidos"].items()) == {(c, it["blob_git"]) for c, it in EM["regua"].items()})

# tabelas por ID e resumo
with open(AQUI / "transicoes_por_id_vl.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["braco", "eixo", "curso", "gold_id", "eid", "cru_limpo", "braco_saida", "certo_cru", "certo_braco", "mudou"])
    for b, vv in R["comparacoes"].items():
        for e, t in vv.items():
            for x in t["registros"]:
                if x["mudou"] or x["certo_antes"] != x["certo_depois"]:
                    w.writerow([b, e, x["curso"], x["gold_id"], x["eid"], x["antes"], x["depois"],
                                int(x["certo_antes"]), int(x["certo_depois"]), int(x["mudou"])])
with open(AQUI / "placar_por_curso_vl.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["braco", "curso", "eixo", "acertos", "n"])
    for b in K.BRACOS:
        for s in CURSOS + ["TOTAL"]:
            for e in EIXOS:
                p = R["placar"][b][s][e]
                w.writerow([b, s, e, p["acertos"], p["n"]])
resumo = {"placar": R["placar"], "derivadas_total": {b: {e: t["derivadas"] for e, t in vv.items()} for b, vv in R["comparacoes"].items()},
          "precisao": {b: {e: {"alteradas": t["precisao_alteradas"], "nao_vazias": t["precisao_alteradas_nao_vazias"]}
                           for e, t in vv.items()} for b, vv in R["comparacoes"].items()},
          "derivadas_por_curso": por_curso,
          "geracao_selecao": {b: {k: g[k] for k in ("escada", "grupos", "selecao_subconjunto_comum", "estados_1a")}
                              for b, g in R["geracao_selecao"].items()},
          "veredictos_recalculados": {"A_limpo": A, "B_limpo": B, "B_perdas": perdas, "B_regride": regride,
                                      "C_limpo_por_curso": C, "C_limpo_todos": C_total},
          "veredictos_avaliador": v}
K.grava_atomico(AQUI / "resumo_vl.json", resumo)
res = {"aprovado": all(ok.values()), "condicoes": ok, "avaliacao_sha256": K.sha_arq(A1), "conferencia_sha256": K.sha_arq(A2)}
K.grava_atomico(AQUI / "conferencia_resultado_vl.json", res)
for k, c in ok.items():
    print(("OK    " if c else "FALHA ") + k, flush=True)
print("CONFERENCIA", "APROVADA" if res["aprovado"] else "REPROVADA", f"({sum(ok.values())}/{len(ok)})", flush=True)
sys.exit(0 if res["aprovado"] else 1)
