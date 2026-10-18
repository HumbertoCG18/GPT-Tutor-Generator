import json
R = "C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-cru05/docs/reports/2026-10-01-cru05-cru03/"
L = lambda p: json.load(open(p, encoding="utf-8"))
rb, ra = L(R + "replay_base.json"), L(R + "replay_candidato.json")
base, A = rb["decisoes"], ra["decisoes"]
EIXOS = ("bloco", "unidade", "sub")
def dif(x, y, eixos=EIXOS):
    return [[s, e, k, (y.get(s, {}).get(e) or {}).get(k), (x.get(s, {}).get(e) or {}).get(k)]
            for s in sorted(set(x) | set(y)) for e in sorted(set(x.get(s, {})) | set(y.get(s, {}))) for k in eixos
            if (x.get(s, {}).get(e) or {}).get(k) != (y.get(s, {}).get(e) or {}).get(k)]
out = {"controles": {"base": {"placar": rb["placar_execucao"]}, "A": {"placar": ra["placar_execucao"], "ganhos_vs_ref": ra["ganhos"], "perdas_vs_ref": ra["perdas"], "referencia": ra.get("referencia")}}}
for nome, ctrl in (("p1", base), ("ap1", A), ("ap1_desligado", A)):
    r, pre = L(f"replay_{nome}.json"), L(f"barreira/{nome}.json")
    d = r["decisoes"]
    o = {"carregados": pre["carregados"], "src_fora": pre["src_fora"], "sha256_decisoes_pre_gold": pre["sha256_decisoes"],
         "ids": sum(map(len, d.values())), "ids_por_curso": {s: len(v) for s, v in d.items()},
         "dif_vs_braco_sem_p1": dif(d, ctrl), "placar_ref": r["placar_referencia"], "placar": r["placar_execucao"],
         "ganhos_vs_ref": r["ganhos"], "perdas_vs_ref": r["perdas"], "referencia": r["referencia"]}
    o["escopo_bloco_unidade"] = [x for x in o["dif_vs_braco_sem_p1"] if x[2] != "sub"]
    if nome == "ap1": o["dif_vs_base"] = dif(d, base)
    out[nome] = o
    print(nome, "ids", o["ids"], "src_fora", o["src_fora"], "dif_vs_ctrl", len(o["dif_vs_braco_sem_p1"]), "escopo", len(o["escopo_bloco_unidade"]))
    print("  placar", o["placar"]["total"]); print("  ref   ", o["placar_ref"]["total"])
    print("  ganhos", o["ganhos_vs_ref"]); print("  perdas", o["perdas_vs_ref"])
print("A placar", ra["placar_execucao"]["total"])
json.dump(out, open("consolidado2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
