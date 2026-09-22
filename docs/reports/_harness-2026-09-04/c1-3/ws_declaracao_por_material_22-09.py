"""W-S (CRU-02): guarda de escopo da declaracao + pergunta POR MATERIAL para os "depende".

Parte da ordem CAP-25 congelada do W-P2' (mesmo sha) e mede, na FASE REAL (1a passada +
2a passada `propagar_vocabulario_por_headings`), duas correcoes pre-declaradas:

(O) ORDEM = CAP-25 do W-P2', reproduzida por `montar_ordens`/`congelar` e conferida pelo sha
    38185c12... ANTES de carregar o gold.
(G) GUARDA DE ESCOPO: a declaracao (expressao -> topico) vale SO para os materiais alcancados
    pela pergunta (entry_ids derivados dos gold_ids congelados na ordem). Implementacao em
    memoria: um wrapper de `auto_map_entry_subtopic` monta, POR ENTRADA, uma taxonomia =
    (a taxonomia que o chamador passou) + os aliases DECLARADOS cujo escopo contem aquele
    entry_id. O mesmo wrapper e usado na 1a passada e dentro de `propagar_vocabulario_por_headings`
    (que passa a sua propria copia com os aliases derivados dos headings).
(M) PERGUNTA POR MATERIAL: quando (R) devolve "depende", cada material alcancado COM gold vira
    uma pergunta propria (custo +1). Resposta = primaria do gold daquele material; havendo mais
    de uma, a primeira em ordem alfabetica ENTRE AS QUE ESTAO NA TAXONOMIA; nenhuma na taxonomia
    -> "nao associar". Declaracao = todas as `expressoes_novas` do material (W-P1), nas FORMAS
    originais, viram alias do topico respondido, escopadas ao proprio material (G).
    Dedupe pre-declarado: um material e perguntado UMA vez por estado (perguntas "depende"
    posteriores que o alcancam de novo nao repetem a pergunta nem o custo).
(V) VARIANTES: V-G = so a guarda; V-GM = guarda + perguntas por material.
    Controle = W-P2' CAP-25 (sem guarda): 5 -> 99/251, 10 -> 113, 20=40 -> 118 (76 perguntas, 12 perdas).
(P) PREFIXOS = 5, 10, 20, 40 perguntas de EXPRESSAO por curso. As perguntas por material
    derivadas nao entram no prefixo, mas entram no custo.
(A) AVALIACAO como no W-P2': primaria/aceita x/251 (ausentes e abstencoes contam erro),
    ganhos/perdas contra a base 84, abstencao -> decisao certa/errada, por curso e total.

GOLD so simula a resposta do professor e avalia; nenhum limiar sai do gold.
Read-only: nao toca src/ nem tests/, sem build, rede, LLM. Patch so em memoria (taxonomia em
copia; nada em .frzero/). O JSON e SOBRESCRITO a cada estado (parcial cedo).
"""
import collections
import copy
import hashlib
import importlib.util
import json
import sys
import time
from functools import partial
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

SHA_CAP25_ESPERADO = "38185c126de98f08b71d4fbbadd4f9176c877f3467a64916063785a4cdf4059d"
PREFIXOS = (5, 10, 20, 40)
VARIANTES = ("V-G", "V-GM")
ORDEM = "CAP25"
CONTROLE_WP2 = {5: 99, 10: 113, 20: 118, 40: 118}   # CAP25 sem guarda (W-P2', primaria/251)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WP2 = load("wp2_curva", HERE / "wp2_curva_microdeclaracoes_22-09.py")   # ja chama memoizar()
RP = WP2.RP
RA, T, diag, compare, mede = RP.RA, RP.T, RP.diag, RP.compare, RP.mede


# ------------------------------------------------------------------ guarda de escopo (G)
def com_aliases(tax, decls):
    """Copia da taxonomia recebida + aliases declarados (decls = tupla de (slug, forma))."""
    novo = copy.deepcopy(tax)
    por_slug = {str(t.get("slug")): t for u in novo.get("units", []) or [] for t in u.get("topics") or []}
    for slug, forma in decls:
        topic = por_slug.get(slug)
        if topic is None:
            continue
        aliases = list(topic.get("aliases") or [])
        if forma not in aliases:
            aliases.append(forma)
        topic["aliases"] = aliases
    return novo


def wrap_auto(auto0, decl_por_entry):
    """auto(entry, taxonomy, texto, ...) -> auto com a taxonomia da ENTRADA (base do chamador +
    declaracoes escopadas aquele entry_id). Memo por (id da taxonomia do chamador, declaracoes);
    a taxonomia fica referenciada no memo, sem hazard de reuso de id."""
    memo = {}

    def auto(entry, taxonomy, texto, **kw):
        decls = decl_por_entry.get(str(entry.get("id") or ""))
        if not decls:
            return auto0(entry, taxonomy, texto, **kw)
        chave = (id(taxonomy), decls)
        if chave not in memo:
            memo[chave] = (taxonomy, com_aliases(taxonomy, decls))
        return auto0(entry, memo[chave][1], texto, **kw)
    return auto


def replay_guarda(ctx, decl_por_entry):
    """Copia local de `replay_subunidade_21-09.replay(root, "base")` (linhas 135-172) com o
    wrapper por entrada nas DUAS passadas. Sem editar o arquivo do replay."""
    root = ctx["root"]
    t0 = time.time()
    entries = copy.deepcopy(compare.read(root / "manifest.json")["entries"])
    taxonomy = WP2.taxonomia_com(ctx, [])           # mesma fonte de taxonomia do W-P2' (copia crua)
    curation = RP.load_code_curation(root).get("entries", {}) or {}
    auto = wrap_auto(partial(RP.AUTO.func, **RP.KW), decl_por_entry)
    passe1, processadas = [], set()
    for entry in entries:
        if not RA._is_material(entry):
            continue
        if not str(entry.get("computed_block_id") or "").strip() and not str(entry.get("temporal_block_id") or "").strip():
            if RA._collapse_ws_cat(str(entry.get("category") or "")).lower() not in RA._NO_TIMELINE_CATEGORIES:
                continue
        cobertura = entry.get("coverage_units") or []
        if str(entry.get("manual_subunit_slug") or "").strip() or (
                cobertura and str(cobertura[0].get("rule") or "") in RP.META_COVERAGE_RULES):
            continue
        md = diag._entry_markdown_text_for_file_map(root, entry)
        resumo = RP.code_curation_signal_text(curation.get(str(entry.get("id") or ""), {}) or {})
        texto = (f"{md}\n\n{resumo}" if md else resumo) if resumo else md
        unit = str(entry.get("computed_unit_slug") or "")
        match = auto(entry, taxonomy, texto, winning_unit_slug=unit)
        passe1.append((entry, texto, unit, match))
        processadas.add(str(entry.get("id")))
        entry["computed_subunit_slug"] = str(match.topic_slug or "")
        entry["subunit_match_reasons"] = list(match.reasons)
        entry["subunit_match_confidence"] = float(match.confidence)
    RA.propagar_vocabulario_por_headings(passe1, taxonomy, auto, conf_min=T.SUBUNIT_PROPAG_CONF,
                                         min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES, df_max=T.SUBUNIT_PROPAG_DF_MAX)
    por_id = {str(e.get("id")): e for e in entries}
    pred = {gid: (str(por_id[eid].get("computed_subunit_slug") or "") if eid else None)
            for gid, eid in ctx["entry_de"].items()}
    return pred, por_id, processadas, round(time.time() - t0, 2)


# ------------------------------------------------------------------ perguntas (R)+(M)
def declaracoes_do_prefixo(sig, ctx, variante, p, ordem, materiais, expressoes):
    """Devolve (decl_por_entry, registros, contagens) para o prefixo p do curso."""
    trip = set()          # (entry_id, slug, forma)
    registros = []
    perguntados = set()   # materiais ja perguntados por (M)
    c = collections.Counter()
    for q in ordem[sig][:p]:
        r = WP2.responder(q, ctx)
        c["examinadas"] += 1
        c[r["resposta"]] += 1
        escopo = [ctx["entry_de"].get(g) for g in q["materiais_alcancados"]]
        escopo = [e for e in escopo if e]
        registros.append({"tipo": "expressao", "ordem": q["ordem"], "expressao": q["expressao"],
                          "formas": q["formas"], "materiais_alcancados": len(q["materiais_alcancados"]),
                          "escopo_entries": len(escopo), "resposta": r["resposta"], "topico": r["topico"]})
        if r["resposta"] == "declara":
            for eid in escopo:
                for f in q["formas"]:
                    trip.add((eid, r["topico"], f))
        elif r["resposta"] == "depende" and variante == "V-GM":
            for g in sorted(q["materiais_alcancados"]):
                if g in perguntados:
                    continue
                gsp = sorted(s for s in (ctx["gsp"].get(g) or ()) if s)
                if not gsp:
                    continue
                perguntados.add(g)
                c["perguntas_material"] += 1
                na_tax = [s for s in gsp if s in ctx["slugs"]]
                eid = ctx["entry_de"].get(g)
                topico = na_tax[0] if na_tax else None
                formas = []
                if topico and eid:
                    for chave in materiais[(sig, g)]["expressoes_novas"]:
                        for f in expressoes[sig][chave]["formas"]:
                            formas.append(f)
                            trip.add((eid, topico, f))
                    c["material_declara"] += 1
                elif topico and not eid:
                    c["material_ausente"] += 1
                else:
                    c["material_nao_associar"] += 1
                registros.append({"tipo": "material", "ordem": q["ordem"], "expressao": q["expressao"],
                                  "gold_id": g, "gold_primario": gsp, "resposta": "declara" if (topico and eid)
                                  else ("nao_associar" if not topico else "ausente"),
                                  "topico": topico, "n_aliases": len(formas), "aliases": sorted(set(formas))[:12]})
    decl = collections.defaultdict(list)
    for eid, slug, forma in sorted(trip):
        decl[eid].append((slug, forma))
    decl = {eid: tuple(v) for eid, v in decl.items()}
    c["entries_com_declaracao"] = len(decl)
    c["aliases_escopados"] = len(trip)
    return decl, registros, dict(c)


def chave_estado(decl):
    return tuple(sorted((eid, d) for eid, d in decl.items()))


# ------------------------------------------------------------------ teto analitico (pergunta 6)
def teto_analitico(ctxs, ordem, mat_full):
    """Por que um material nao pode ser corrigido nem com V-GM esgotada."""
    por_curso, causas = {}, collections.Counter()
    detalhe = []
    for sig, ctx in ctxs.items():
        tax = WP2.taxonomia_com(ctx, [])
        unidade_do_topico = {str(t.get("slug")): str(u.get("slug") or "")
                             for u in tax.get("units", []) or [] for t in u.get("topics") or []}
        entradas = {str(e.get("id")): e for e in compare.read(ctx["root"] / "manifest.json")["entries"]}
        alcancados = set()
        for q in ordem[sig]:
            alcancados |= set(q["materiais_alcancados"])
        c = collections.Counter()
        for gid in ctx["ids"]:
            c["n"] += 1
            eid = ctx["entry_de"].get(gid)
            gsp = sorted(s for s in (ctx["gsp"].get(gid) or ()) if s)
            causa = None
            if eid is None:
                causa = "entry_ausente"
            elif not gsp:
                causa = "sem_gold_primario"
            elif not [s for s in gsp if s in ctx["slugs"]]:
                causa = "gold_fora_da_taxonomia"
            else:
                unidade = str(entradas[eid].get("computed_unit_slug") or "")
                if not any(unidade_do_topico.get(s) == unidade for s in gsp if s in ctx["slugs"]):
                    causa = "bloqueio_pela_unidade"
                elif eid not in {e for e in [ctx["entry_de"].get(g) for g in alcancados] if e}:
                    causa = "nao_alcancado_pela_ordem"
            if causa:
                c[causa] += 1
                causas[causa] += 1
                detalhe.append({"curso": sig, "gold_id": gid, "causa": causa, "gold": gsp})
            else:
                c["alcancavel"] += 1
        por_curso[sig] = dict(c)
    return {"por_curso": por_curso, "causas": dict(causas),
            "teto": sum(v["alcancavel"] for v in por_curso.values()),
            "n": sum(v["n"] for v in por_curso.values()), "detalhe": detalhe}


# ------------------------------------------------------------------ main
ESTADO = {}


def gravar(scope=None):
    if scope:
        ESTADO.update({k: scope[k] for k in ("resultados", "perdas", "registros", "contagens", "base_stats",
                                             "base_total", "fidelidade", "alvos", "sha_cap25", "sha_wp1",
                                             "teto", "ordem_tam") if k in scope})
    if "resultados" not in ESTADO:
        return None
    r = {"escopo": __doc__,
         "estado": {"branch": "feat/motor-atribuicao", "head": "b726d4c", "src": "intocado",
                    "json": "sobrescrito a cada estado"},
         "congelamento_cap25_sha256": ESTADO["sha_cap25"],
         "congelamento_wp1_sha256": ESTADO["sha_wp1"],
         "controle_wp2_sem_guarda": CONTROLE_WP2,
         "prefixos": list(PREFIXOS), "variantes": list(VARIANTES),
         "perguntas_por_curso_na_ordem": ESTADO.get("ordem_tam"),
         "base": {"total": ESTADO["base_total"], "por_curso": ESTADO["base_stats"],
                  "fidelidade_manifest": dict(ESTADO["fidelidade"])},
         "alvos_por_curso": {s: {"n": len(v), "ids": v} for s, v in ESTADO["alvos"].items()},
         "resultados": ESTADO["resultados"],
         "perdas": ESTADO["perdas"],
         "contagens": ESTADO["contagens"],
         "registros_perguntas": ESTADO["registros"],
         "teto_analitico": ESTADO.get("teto")}
    out = HERE / "ws_declaracao_por_material_22-09.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(out.read_bytes()).hexdigest()


def main():
    materiais, expressoes, perguntas_naive, sha_wp1, mat_full, _ = WP2.carregar_wp1()
    ordens, _ = WP2.montar_ordens(materiais, expressoes, perguntas_naive)
    sha_cap25 = WP2.congelar(ordens)
    assert sha_cap25 == SHA_CAP25_ESPERADO, f"ordem nao reproduz o congelamento do W-P2': {sha_cap25}"
    print("CONGELAMENTO_OK", sha_cap25, flush=True)
    ordem = ordens[ORDEM]
    ordem_tam = {s: len(l) for s, l in ordem.items()}
    print("PERGUNTAS_CAP25", ordem_tam, flush=True)

    # ---- gold entra aqui ----------------------------------------------------------------
    ctxs = {sig: WP2.contexto_curso(sig) for sig in mede.NOMES}
    alvos = {sig: sorted(m["gold_id"] for m in mat_full
                         if m["curso"] == sig and not m["certo_primario"] and m["expressoes_novas"])
             for sig in mede.NOMES}

    base_pred, base_stats, fidelidade = {}, {}, collections.Counter()
    for sig, ctx in ctxs.items():
        pred, por_id, processadas, dt = replay_guarda(ctx, {})
        gravado = {str(e.get("id")): e for e in compare.read(ctx["root"] / "manifest.json")["entries"]}
        for eid in processadas:
            fidelidade["processadas"] += 1
            fidelidade["fieis"] += (str(por_id[eid].get("computed_subunit_slug") or "")
                                    == str(gravado[eid].get("computed_subunit_slug") or ""))
        base_pred[sig] = pred
        base_stats[sig], _, _, _ = WP2.avaliar(pred, pred, ctx)
        base_stats[sig]["tempo_s"] = dt
    base_total = {k: sum(v.get(k, 0) for v in base_stats.values()) for k in ("n", "ausente", "primaria", "aceita")}
    print("BASE", base_total, "fidelidade", dict(fidelidade), flush=True)
    assert fidelidade["fieis"] == fidelidade["processadas"], "replay base diverge do manifest gravado"
    assert base_total["primaria"] == 84 and base_total["n"] == 251, f"base nao reproduz 84/251: {base_total}"

    teto = teto_analitico(ctxs, ordem, mat_full)
    print("TETO", teto["teto"], "/", teto["n"], teto["causas"], flush=True)

    resultados, perdas_det, registros, contagens = {}, [], {}, {}
    cache = {}
    for variante in VARIANTES:
        resultados[variante] = {}
        registros[variante] = {}
        contagens[variante] = {}
        for p in PREFIXOS:
            cursos = {}
            for sig, ctx in ctxs.items():
                decl, regs, cont = declaracoes_do_prefixo(sig, ctx, variante, p, ordem, materiais, expressoes)
                k = (sig, chave_estado(decl))
                if k not in cache:
                    pr, _, _, dt = replay_guarda(ctx, decl)
                    cache[k] = (pr, dt)
                pred, dt = cache[k]
                stats, perdas, certas, erradas = WP2.avaliar(pred, base_pred[sig], ctx)
                corrigidos = sum(1 for g in alvos[sig] if pred[g] is not None and pred[g] in set(ctx["gsp"].get(g) or ()))
                stats.update({"tempo_s": dt, "base_primaria": base_stats[sig]["primaria"],
                              "alvos": len(alvos[sig]), "alvos_corrigidos": corrigidos,
                              "abst_certas_ids": certas, "abst_erradas_ids": erradas, **cont})
                stats["custo"] = cont.get("examinadas", 0) + cont.get("perguntas_material", 0)
                cursos[sig] = stats
                registros[variante].setdefault(str(p), {})[sig] = regs
                for d in perdas:
                    perdas_det.append({"variante": variante, "prefixo": p, "curso": sig, **d})
            tot = {k2: sum(v.get(k2, 0) for v in cursos.values())
                   for k2 in ("n", "ausente", "primaria", "aceita", "ganho", "perda", "abst_decisao",
                              "abst_certa", "abst_errada", "examinadas", "declara", "depende", "nao_associar",
                              "perguntas_material", "material_declara", "material_nao_associar", "material_ausente",
                              "aliases_escopados", "entries_com_declaracao", "alvos", "alvos_corrigidos", "custo")}
            tot["tempo_s"] = round(sum(v["tempo_s"] for v in cursos.values()), 2)
            tot["cursos_que_regridem"] = sorted(s for s, v in cursos.items() if v.get("perda", 0) > 0)
            tot["controle_wp2_primaria"] = CONTROLE_WP2[p]
            resultados[variante][str(p)] = {"cursos": cursos, "total": tot}
            contagens[variante][str(p)] = tot
            print(variante, p, json.dumps(tot, ensure_ascii=False), flush=True)
            gravar({"resultados": resultados, "perdas": perdas_det, "registros": registros,
                    "contagens": contagens, "base_stats": base_stats, "base_total": base_total,
                    "fidelidade": fidelidade, "alvos": alvos, "sha_cap25": sha_cap25, "sha_wp1": sha_wp1,
                    "teto": teto, "ordem_tam": ordem_tam})
    print("FIM", flush=True)


def escrever_md(sha):
    r = ESTADO
    L = ["# W-S — guarda de escopo + declaracao por material (CRU-02, 22/09)", "",
         f"JSON: `ws_declaracao_por_material_22-09.json` sha256 `{sha}` (sobrescrito a cada estado)  ",
         f"Congelamento CAP-25 (herdado do W-P2') sha256 `{r['sha_cap25']}`  ",
         f"Congelamento W-P1 sha256 `{r['sha_wp1']}`  ",
         "Estado: branch `feat/motor-atribuicao`, HEAD `b726d4c`, `src/` e `tests/` intocados.", "",
         "## 1. Base (0 declaracoes, wrapper por entrada ativo)", "",
         f"- primaria {r['base_total']['primaria']}/{r['base_total']['n']}, aceita {r['base_total']['aceita']}"
         f"/{r['base_total']['n']}, ausentes {r['base_total']['ausente']}",
         f"- fidelidade do replay contra o manifest gravado: {r['fidelidade']['fieis']}/{r['fidelidade']['processadas']}",
         "", "| curso | n | primaria | aceita | ausente | alvos | perguntas CAP-25 |", "|---|---|---|---|---|---|---|"]
    for sig, v in r["base_stats"].items():
        L.append(f"| {sig} | {v['n']} | {v['primaria']} | {v['aceita']} | {v.get('ausente', 0)} | "
                 f"{len(r['alvos'][sig])} | {r['ordem_tam'][sig]} |")
    L += ["", "## 2. Totais: variante x prefixo", "",
          "| variante | prefixo | exam. expr | declaradas | depende | perg. material | custo | primaria/251 | "
          "(W-P2' sem guarda) | aceita/251 | ganhos | perdas | abst->dec (certas/erradas) | alvos corrigidos | tempo (s) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for variante, por_p in r["resultados"].items():
        for p in sorted(por_p, key=int):
            t = por_p[p]["total"]
            L.append(f"| {variante} | {p} | {t['examinadas']} | {t['declara']} | {t['depende']} | "
                     f"{t['perguntas_material']} | {t['custo']} | {t['primaria']} | {t['controle_wp2_primaria']} | "
                     f"{t['aceita']} | {t['ganho']} | {t['perda']} | "
                     f"{t['abst_decisao']} ({t['abst_certa']}/{t['abst_errada']}) | "
                     f"{t['alvos_corrigidos']}/{t['alvos']} | {t['tempo_s']} |")
    L += ["", "## 3. Por curso", ""]
    for variante, por_p in r["resultados"].items():
        L += [f"### {variante}", "",
              "| prefixo | curso | exam. | decl. | dep. | perg. mat. | custo | primaria | aceita | ganhos | perdas | "
              "abst->dec | alvos corr. | tempo |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for p in sorted(por_p, key=int):
            for sig, c in por_p[p]["cursos"].items():
                L.append(f"| {p} | {sig} | {c.get('examinadas', 0)} | {c.get('declara', 0)} | {c.get('depende', 0)} | "
                         f"{c.get('perguntas_material', 0)} | {c.get('custo', 0)} | {c.get('primaria', 0)} | "
                         f"{c.get('aceita', 0)} | {c.get('ganho', 0)} | {c.get('perda', 0)} | "
                         f"{c.get('abst_decisao', 0)} ({c.get('abst_certa', 0)}/{c.get('abst_errada', 0)}) | "
                         f"{c['alvos_corrigidos']}/{c['alvos']} | {c['tempo_s']} |")
        L.append("")
    L += ["## 4. Perdas (declaracao derruba material hoje certo)", ""]
    if not r["perdas"]:
        L.append("- nenhuma perda em nenhum estado medido.")
    else:
        L += ["| variante | prefixo | curso | gold_id | base | novo | gold primario |", "|---|---|---|---|---|---|---|"]
        for d in r["perdas"]:
            L.append(f"| {d['variante']} | {d['prefixo']} | {d['curso']} | {d['gold_id']} | `{d['base']}` | "
                     f"`{d['novo']}` | {', '.join(d['gold'])} |")
    t = r.get("teto") or {}
    L += ["", "## 5. Teto analitico (materiais que V-GM esgotada nao alcanca)", "",
          f"- alcancaveis {t.get('teto')}/{t.get('n')}; causas: {t.get('causas')}", "",
          "| curso | n | alcancavel | entry ausente | sem gold | gold fora da taxonomia | bloqueio pela unidade | nao alcancado pela ordem |",
          "|---|---|---|---|---|---|---|---|"]
    for sig, c in (t.get("por_curso") or {}).items():
        L.append(f"| {sig} | {c.get('n', 0)} | {c.get('alcancavel', 0)} | {c.get('entry_ausente', 0)} | "
                 f"{c.get('sem_gold_primario', 0)} | {c.get('gold_fora_da_taxonomia', 0)} | "
                 f"{c.get('bloqueio_pela_unidade', 0)} | {c.get('nao_alcancado_pela_ordem', 0)} |")
    if r.get("marcos"):
        L += ["", "## 5b. Marcos 50/80% dos alvos por CORRECAO EFETIVA (custo = expressao + material)", "",
              "| variante | marco | prefixo | custo | corrigidos/alvos | primaria/251 |", "|---|---|---|---|---|---|"]
        for variante, m in r["marcos"].items():
            for nome in ("p50", "p80"):
                d = m["TOTAL"][nome]
                L.append(f"| {variante} | {nome} | " + (f"{d['prefixo']} | {d['custo']} | "
                         f"{d['corrigidos']}/{d['alvos']} | {d['primaria']} |" if d else "nao atingido | - | - | - |"))
            f = m["TOTAL"]["final"]
            L.append(f"| {variante} | final (ordem esgotada) | {f['prefixo']} | {f['custo']} | "
                     f"{f['corrigidos']}/{f['alvos']} ({f['pct']}%) | - |")
        L += ["", "Por curso (ordem esgotada e marcos):", "",
              "| variante | curso | alvos | corrigidos finais | % | custo final | p50 (prefixo/custo) | p80 (prefixo/custo) |",
              "|---|---|---|---|---|---|---|---|"]
        for variante, m in r["marcos"].items():
            for sig, d in m.items():
                if sig == "TOTAL":
                    continue
                f = d["final"]
                p50 = f"{d['p50']['prefixo']}/{d['p50']['custo']}" if d["p50"] else "-"
                p80 = f"{d['p80']['prefixo']}/{d['p80']['custo']}" if d["p80"] else "-"
                L.append(f"| {variante} | {sig} | {f['alvos']} | {f['corrigidos']} | {f['pct']} | {f['custo']} | "
                         f"{p50} | {p80} |")
    L += ["", "## 6. Perguntas por material feitas (V-GM, prefixos 5 e 10)", ""]
    for p in ("5", "10"):
        regs = (r["registros"].get("V-GM") or {}).get(p) or {}
        L += [f"### prefixo {p}", "",
              "| curso | expr. que gerou | gold_id | gold primario | resposta | topico | n aliases |",
              "|---|---|---|---|---|---|---|"]
        for sig, lst in regs.items():
            for q in lst:
                if q["tipo"] != "material":
                    continue
                L.append(f"| {sig} | `{q['expressao']}` | {q['gold_id']} | {', '.join(q['gold_primario'])} | "
                         f"{q['resposta']} | {q['topico'] or ''} | {q['n_aliases']} |")
        L.append("")
    L += ["## 7. Perguntas de expressao e resposta simulada (V-G, prefixo 20)", "",
          "| curso | # | expressao | mat. alcancados | escopo (entries) | resposta | topico |",
          "|---|---|---|---|---|---|---|"]
    for sig, lst in ((r["registros"].get("V-G") or {}).get("20") or {}).items():
        for q in lst:
            if q["tipo"] != "expressao":
                continue
            L.append(f"| {sig} | {q['ordem']} | `{q['expressao']}` | {q['materiais_alcancados']} | "
                     f"{q['escopo_entries']} | {q['resposta']} | {q['topico'] or ''} |")
    (HERE / "ws_declaracao_por_material_22-09.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def marcos_pos_hoc():
    """Marcos 50/80% dos alvos por CORRECAO EFETIVA (alvos_corrigidos medidos), com o custo total
    (perguntas de expressao + perguntas por material). Sem replay: le o JSON ja medido."""
    alvo = HERE / "ws_declaracao_por_material_22-09.json"
    r = json.loads(alvo.read_text(encoding="utf-8"))
    marcos = {}
    for variante, por_p in r["resultados"].items():
        ps = sorted(por_p, key=int)
        m = {"TOTAL": {}}
        for pct in (50, 80):
            alcanca = None
            for p in ps:
                t = por_p[p]["total"]
                if t["alvos_corrigidos"] >= pct / 100.0 * t["alvos"]:
                    alcanca = {"prefixo": int(p), "custo": t["custo"], "corrigidos": t["alvos_corrigidos"],
                               "alvos": t["alvos"], "primaria": t["primaria"]}
                    break
            m["TOTAL"][f"p{pct}"] = alcanca
        ult = por_p[ps[-1]]["total"]
        m["TOTAL"]["final"] = {"prefixo": int(ps[-1]), "custo": ult["custo"],
                               "corrigidos": ult["alvos_corrigidos"], "alvos": ult["alvos"],
                               "pct": round(100.0 * ult["alvos_corrigidos"] / max(1, ult["alvos"]), 1)}
        for sig in por_p[ps[0]]["cursos"]:
            d = {}
            for pct in (50, 80):
                d[f"p{pct}"] = None
                for p in ps:
                    c = por_p[p]["cursos"][sig]
                    if c["alvos"] and c["alvos_corrigidos"] >= pct / 100.0 * c["alvos"]:
                        d[f"p{pct}"] = {"prefixo": int(p), "custo": c["custo"],
                                        "corrigidos": c["alvos_corrigidos"], "alvos": c["alvos"]}
                        break
            cf = por_p[ps[-1]]["cursos"][sig]
            d["final"] = {"custo": cf["custo"], "corrigidos": cf["alvos_corrigidos"], "alvos": cf["alvos"],
                          "pct": round(100.0 * cf["alvos_corrigidos"] / max(1, cf["alvos"]), 1)}
            m[sig] = d
        marcos[variante] = m
    r["marcos_alvos"] = marcos
    alvo.write_text(json.dumps(r, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    sha = hashlib.sha256(alvo.read_bytes()).hexdigest()
    ESTADO.update({"resultados": r["resultados"], "perdas": r["perdas"], "registros": r["registros_perguntas"],
                   "contagens": r["contagens"], "base_stats": r["base"]["por_curso"],
                   "base_total": r["base"]["total"], "fidelidade": r["base"]["fidelidade_manifest"],
                   "alvos": {s: v["ids"] for s, v in r["alvos_por_curso"].items()},
                   "sha_cap25": r["congelamento_cap25_sha256"], "sha_wp1": r["congelamento_wp1_sha256"],
                   "teto": r["teto_analitico"], "ordem_tam": r["perguntas_por_curso_na_ordem"],
                   "marcos": marcos})
    escrever_md(sha)
    print("MARCOS", json.dumps({v: m["TOTAL"] for v, m in marcos.items()}, ensure_ascii=False))
    print("JSON_SHA256", sha)
    print("MD regravado")


if __name__ == "__main__":
    if "--marcos" in sys.argv:
        marcos_pos_hoc()
    else:
        main()
        sha = gravar()
        print("JSON_SHA256", sha)
        escrever_md(sha)
        print("MD gravado")
