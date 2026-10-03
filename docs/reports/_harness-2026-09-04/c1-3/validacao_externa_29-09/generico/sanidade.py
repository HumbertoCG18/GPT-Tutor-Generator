"""Harness genérico — sanidade SEM GOLD do sidecar gerado (cópia de ../../vocab_limpo_26-09/sanidade.py). A comparação
descritiva com um sidecar histórico só roda quando a configuração declara `staging_fonte.historico_sidecars`.

Descritivo: nada aqui decide continuar/parar pela semântica dos termos; só integridade (parse, chaves, tópicos, contagens).
Também copia os sidecars para o namespace da rodada (`.frzero/vocab_limpo_26-09/sidecars/<curso>/`), com hash.
"""
import collections
import json
import platform
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import limpo as L  # noqa: E402  (constantes, travas e hashes da rodada; limpo.py não é alterado)

K, DATA, BASE = L.K, L.DATA, L.BASE
SIDECARS = BASE / "sidecars"
HIST = DATA / K.R.CFG["staging_fonte"]["historico_sidecars"] if K.R.CFG["staging_fonte"].get("historico_sidecars") else None


def main():
    t = L.travas_base("sanidade")
    t.permite("referencia", L.STAGING, L.CONG_LIMPO, L.INVENTARIO, BASE / "compilacao.json", *([HIST] if HIST else []), somente_leitura=True)
    t.permite("saida", SIDECARS, BASE / "sanidade.json", AQUI / f"sanidade_{K.R.CFG['sufixo']}.md", BASE)
    t.instala()
    exige = L.exige
    exige(not SIDECARS.exists(), "sidecars da rodada já copiados: não sobrescrevo")
    cong = K.carrega_json_estrito(L.CONG_LIMPO)
    comp = K.carrega_json_estrito(BASE / "compilacao.json")
    exige(comp["id_recompilacao"] == cong["id_recompilacao"], "compilação de outro congelamento")
    from src.builder.core import vocabulary_compile as VC
    modelo = cong["normativo"]["modelo"]["identificador"]
    R, linhas, comparacao = {"id_recompilacao": cong["id_recompilacao"], "compilacao_completa": comp["completa"], "cursos": {}}, [], {}
    for s, nome in K.NOMES.items():
        course = L.STAGING / nome / "course"
        p = course / L.LLM_VOCAB
        prob = []
        if not p.is_file():
            R["cursos"][s] = {"problemas": ["sidecar ausente"]}
            continue
        d = K.carrega_json_estrito(p)
        tax = json.loads((course / ".content_taxonomy.json").read_text(encoding="utf-8"))
        chaves_tax = {VC.topic_key(tp): u.get("slug") for u in tax.get("units") or [] for tp in u.get("topics") or [] if tp.get("label")}
        topicos = {k: v for k, v in d.items() if not k.startswith("_")}
        if d.get("_provenance") != "llm" or d.get("_modelo") != modelo:
            prob.append("metadados _provenance/_modelo inesperados")
        raw = d.get("_raw") or {}
        prob += [f"chave de _raw fora da taxonomia: {k}" for k in raw if k not in chaves_tax]
        prob += [f"tópico inexistente: {k}" for k in topicos if k not in chaves_tax]
        termos, vazios, dup_topico, mal_norm = [], 0, 0, 0
        onde = collections.defaultdict(set)
        for k, v in topicos.items():
            syn = v.get("synonyms") if isinstance(v, dict) else None
            if not isinstance(syn, list) or not syn:
                prob.append(f"{k}: synonyms ausente/vazio")
                continue
            vistos = set()
            for x in syn:
                if not isinstance(x, str) or not x.strip():
                    vazios += 1
                    continue
                if x != " ".join(x.split()):
                    mal_norm += 1
                n = VC._norm(x)
                dup_topico += n in vistos
                vistos.add(n)
                onde[n].add(k)
                termos.append(n)
        multi = sum(1 for ks in onde.values() if len(ks) > 1)
        if vazios or dup_topico or multi or mal_norm:
            prob.append(f"vazios={vazios} duplicatas_no_tópico={dup_topico} termo_em_>1_tópico={multi} espaços={mal_norm}")
        if (course / L.MANUAL_VOCAB).exists():
            prob.append("sidecar manual presente no staging")
        c = comp["cursos"].get(s, {})
        R["cursos"][s] = {"problemas": prob, "sidecar_sha256": K.sha_arq(p), "topicos_taxonomia": len(chaves_tax),
                          "topicos_com_termo": len(topicos), "termos_totais": len(termos), "termos_unicos": len(set(termos)),
                          "raw_topicos": len(raw), "raw_termos": sum(len(v) for v in raw.values()),
                          "chamadas": c.get("unidades_chamadas"), "tentativas": c.get("tentativas"), "retries": c.get("retries"),
                          "falhas": c.get("unidades_com_erro")}
        destino = SIDECARS / nome / L.LLM_VOCAB
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(p.read_bytes())
        exige(K.sha_arq(destino) == K.sha_arq(p), f"{s}: cópia do sidecar divergente")
        if HIST:   # comparação descritiva com um histórico declarado (não é critério nem alvo)
            h = K.carrega_json_estrito(HIST / nome / "course" / L.LLM_VOCAB)
            ht = {k: {VC._norm(x) for x in v.get("synonyms") or []} for k, v in h.items() if not k.startswith("_") and isinstance(v, dict)}
            lt = {k: {VC._norm(x) for x in v.get("synonyms") or []} for k, v in topicos.items()}
            hs, ls_ = set().union(*ht.values()) if ht else set(), set().union(*lt.values()) if lt else set()
            jac = {k: round(len(ht.get(k, set()) & lt.get(k, set())) / len(ht.get(k, set()) | lt.get(k, set())), 3)
                   for k in sorted(set(ht) | set(lt)) if ht.get(k, set()) | lt.get(k, set())}
            comparacao[s] = {"topicos_hist": len(ht), "topicos_limpo": len(lt), "topicos_em_ambos": len(set(ht) & set(lt)),
                             "termos_hist": len(hs), "termos_limpo": len(ls_), "termos_em_ambos": len(hs & ls_),
                             "surgiram": len(ls_ - hs), "sumiram": len(hs - ls_),
                             "jaccard_medio_por_topico": round(sum(jac.values()) / len(jac), 3) if jac else None,
                             "aliases_por_topico_hist": round(len(hs) / len(ht), 2) if ht else None,
                             "aliases_por_topico_limpo": round(len(ls_) / len(lt), 2) if lt else None,
                             "hist_sha256": K.sha_arq(HIST / nome / "course" / L.LLM_VOCAB)}
        v = R["cursos"][s]
        linhas.append(f"| {s} | {v['topicos_taxonomia']} | {v['topicos_com_termo']} | {v['termos_totais']} | {v['termos_unicos']} | "
                      f"{v['chamadas']} | {v['retries']} | {len(v['falhas'] or [])} | {'; '.join(prob) or '—'} |")
    R["comparacao_descritiva_com_historico"] = comparacao
    R["sidecars"] = {s: {"arquivo": L.rel(SIDECARS / n / L.LLM_VOCAB), "sha256": K.sha_arq(SIDECARS / n / L.LLM_VOCAB)}
                     for s, n in K.NOMES.items() if (SIDECARS / n / L.LLM_VOCAB).exists()}
    R["aprovado"] = comp["completa"] and len(R["sidecars"]) == len(K.NOMES) and not any(v["problemas"] for v in R["cursos"].values())
    K.grava_atomico(BASE / "sanidade.json", R)
    md = [f"# {K.R.CFG['sufixo']} — sanidade sem gold", "", f"Recompilação `{cong['id_recompilacao']}`. Aprovado: **{R['aprovado']}**.", "",
          "| curso | tópicos na taxonomia | tópicos com termo | termos | termos únicos | chamadas | retries | falhas | problemas |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---|", *linhas, "",
          "## Comparação descritiva com o histórico declarado (não é critério nem alvo)", "",
          "| curso | tópicos hist/limpo/ambos | termos hist/limpo/ambos | surgiram | sumiram | Jaccard médio por tópico | aliases por tópico hist → limpo |",
          "|---|---|---|---:|---:|---:|---|"]
    md += [f"| {s} | {c['topicos_hist']}/{c['topicos_limpo']}/{c['topicos_em_ambos']} | {c['termos_hist']}/{c['termos_limpo']}/{c['termos_em_ambos']} | "
           f"{c['surgiram']} | {c['sumiram']} | {c['jaccard_medio_por_topico']} | {c['aliases_por_topico_hist']} → {c['aliases_por_topico_limpo']} |"
           for s, c in comparacao.items()]
    with t._abrir_original(AQUI / f"sanidade_{K.R.CFG['sufixo']}.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    t.rehash_leituras()
    print("SANIDADE", "APROVADA" if R["aprovado"] else "REPROVADA", flush=True)
    K.encerra(t, ok=R["aprovado"], codigo_falha=1)


if __name__ == "__main__":
    platform.uname()
    platform.platform()
    main()
