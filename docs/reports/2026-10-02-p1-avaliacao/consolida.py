import json, sys
C = "C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-cru05/docs/reports/2026-10-01-cru05-cru03/"
L = lambda p: json.load(open(p, encoding="utf-8"))
base, A = L(C + "replay_base.json")["decisoes"], L(C + "replay_candidato.json")["decisoes"]
out = {}
for nome, ctrl in (("p1", base), ("ap1", A)):
    r = L(f"replay_{nome}.json")
    d = r["decisoes"]
    escopo = [[s, e, k] for s in ctrl for e in ctrl[s] for k in ("bloco", "unidade") if (d.get(s, {}).get(e) or {}).get(k) != ctrl[s][e].get(k)]
    out[nome] = {"src_sha256": r.get("src_sha256"), "src_fora": r["src_fora_da_worktree"], "ids": sum(map(len, d.values())),
                 "sha256_mudancas_pre_gold": r["sha256_mudancas_pre_gold"], "mudancas_vs_base": len(r["mudancas_por_id"]),
                 "violacoes_escopo_vs_braco_sem_p1": escopo, "placar_base": r["placar_referencia"], "placar": r["placar_execucao"],
                 "ganhos": r["ganhos"], "perdas": r["perdas"]}
    print(nome, "ids", out[nome]["ids"], "src_fora", r["src_fora_da_worktree"], "escopo", len(escopo), "mud", len(r["mudancas_por_id"]))
    print(" total base", r["placar_referencia"]["total"], "\n total exec", r["placar_execucao"]["total"])
    print(" ganhos", {k: v for k, v in r["ganhos"].items()}, "\n perdas", {k: v for k, v in r["perdas"].items()})
    print(" por_curso", {s: v for s, v in r["placar_execucao"]["por_curso"].items()})
out["ap1_vs_A_mudancas"] = [[s, e, A[s][e], out and L("replay_ap1.json")["decisoes"][s].get(e)] for s in A for e in A[s] if L("replay_ap1.json")["decisoes"][s].get(e) != A[s][e]] if False else None
json.dump(out, open("consolidado.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
