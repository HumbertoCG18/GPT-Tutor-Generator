"""Diagnóstico delimitado (23/09): identidade de `frases_topico` e proveniência da 2ª passada (CRU-05). Só medição.

0 mudança em src/, régua e critério. Não desliga a 2ª passada, não cria grade de confiança, não escolhe doadores.

(1) IDENTIDADE. `propagar_vocabulario_por_headings` (resolver_apply.py:315-316) monta `frases_topico` por `topic_slug`
    sem `unit_slug`; `_subtopico_nomeado_no_titulo` (:226-236) consulta `frases_topico[vencedor]` para a guarda "o título
    não nomeia o vencedor". Com slug repetido em duas unidades, a última unidade sobrescreve a primeira.
    (a) teste mínimo com a função REAL e taxonomia sintética: slug repetido x controle sem repetição;
    (b) base v2 instrumentada: em cada chamada da regra do título, resultado atual x resultado com as frases do PAR
        (unidade, vencedor). Conta alcance (vencedor com slug repetido; frases diferentes) e efeito (resultado muda).
(2) CRU-05. Na mesma passada, envolve a 2ª passada e registra, sem alterar nada:
    - aliases acrescentados por (unidade, tópico) = taxonomia estendida que a 2ª passada entrega ao scorer menos a
      original; origem de cada um: parte de rótulo do plano (`_partes_de_rotulo`) ou token propagado;
    - doadores de cada token propagado: materiais confiantes da 1ª passada no mesmo (unidade, tópico) cujos tokens de
      headings/título contêm o token (mesmas funções do módulo: `collect_entry_unit_signals`, `_tokens_headings`);
    - cada material que a 2ª passada mudou: 1ª x 2ª decisão, razão, termos acrescentados presentes no título/texto.
    O gold entra só DEPOIS: fidelidade por ID contra a captura congelada do W-Z2 e avaliação (ganho/perda, doadores
    certos). O gold avalia; não seleciona nada.
Saídas: diag_identidade_propagacao_23-09.json e .md.
"""
import collections
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
OUT = HERE / "diag_identidade_propagacao_23-09"


def teste_minimo(RA):
    def roda(slug_u2):
        tax = {"units": [
            {"slug": "u1", "title": "Unidade Um", "topics": [
                {"slug": "introducao", "label": "Introducao ao pipeline grafico"},
                {"slug": "bezier", "label": "Bezier e Algoritmo de Casteljau"}]},
            {"slug": "u2", "title": "Unidade Dois", "topics": [
                {"slug": slug_u2, "label": "Introducao a iluminacao"}]}]}
        entry = {"id": "m1", "title": "Introducao ao pipeline grafico e Bezier"}
        match = SimpleNamespace(topic_slug="introducao", ambiguous=False, confidence=0.9, reasons=["1a"])
        RA.propagar_vocabulario_por_headings([(entry, "", "u1", match)], tax, lambda *a, **k: None,
                                             conf_min=0.5, min_entries=99, df_max=1.0)
        return entry.get("computed_subunit_slug", "")
    r = {"slug_repetido_em_u1_e_u2": roda("introducao"), "controle_slug_unico": roda("introducao-iluminacao")}
    # correto nos dois: o título nomeia o vencedor de u1 -> a guarda bloqueia -> nada muda
    r["confirmado"] = r["slug_repetido_em_u1_e_u2"] == "bezier" and r["controle_slug_unico"] == ""
    return r


def main():
    t0 = time.time()
    import importlib.util
    spec = importlib.util.spec_from_file_location("wz2", HERE / "wz2_diagnostico_causal_23-09.py")
    wz2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wz2)
    compare = wz2.load("d_cmp", HERE / "compara_herancas_15-09.py")
    rb = wz2.load("d_rb", HERE / "replay_bloco_21-09.py")
    ru = wz2.load("d_ru", HERE / "replay_unidade_21-09.py")
    wz = wz2.load("d_wz", HERE / "wz_bloco_cobertura_22-09.py")
    wx = wz2.load("d_wx", HERE / "wx_regua_corrigida_22-09.py")
    RA = ru.RA
    from src.builder.text.stopwords import MOTOR_GENERIC_STEMS as GENERIC

    minimo = teste_minimo(RA)
    print("TESTE MINIMO", minimo, flush=True)

    REG = {"titulo": [], "prop": {}}
    CUR = {}
    orig_prop, orig_tit = RA.propagar_vocabulario_por_headings, RA._subtopico_nomeado_no_titulo

    def tit_wrapper(entry, unit_slug, vencedor, partes, frases_topico):
        res = orig_tit(entry, unit_slug, vencedor, partes, frases_topico)
        t = next((t for t in (CUR["units"].get(unit_slug) or {}).get("topics") or []
                  if str(t.get("slug") or "") == vencedor), None)
        frases_par = ([str(t.get("label") or "")] + list(t.get("aliases") or [])) if t else []
        res_par = orig_tit(entry, unit_slug, vencedor, partes, {vencedor: frases_par})
        REG["titulo"].append({"curso": wz2.CTX["sig"], "eid": str(entry.get("id")), "titulo": str(entry.get("title") or ""),
                              "unidade": unit_slug, "vencedor": vencedor, "slug_repetido": CUR["rep"][vencedor] >= 2,
                              "frases_iguais": list(frases_topico.get(vencedor, [])) == frases_par,
                              "resultado_atual": res, "resultado_por_par": res_par})
        return res

    def prop_wrapper(passe1, content_taxonomy, fn, *, conf_min, min_entries, df_max):
        units = {str(u.get("slug") or ""): u for u in (content_taxonomy or {}).get("units", []) or []}
        CUR["units"] = units
        CUR["rep"] = collections.Counter(str(t.get("slug") or "") for u in units.values() for t in u.get("topics") or [])
        ext = {}

        def fn_wrapper(entry, tax, texto, **kw):
            ext.setdefault("tax", tax)
            return fn(entry, tax, texto, **kw)

        antes = {id(e): (e.get("computed_subunit_slug"), list(e.get("subunit_match_reasons") or [])) for e, *_ in passe1}
        n = orig_prop(passe1, content_taxonomy, fn_wrapper, conf_min=conf_min, min_entries=min_entries, df_max=df_max)

        added = {}
        for u in (ext.get("tax") or {}).get("units", []) or []:
            ou = units.get(str(u.get("slug") or "")) or {}
            orig_al = {str(t.get("slug") or ""): set(t.get("aliases") or []) for t in ou.get("topics") or []}
            for t in u.get("topics") or []:
                novos = set(t.get("aliases") or []) - orig_al.get(str(t.get("slug") or ""), set())
                if novos:
                    added[(str(u.get("slug") or ""), str(t.get("slug") or ""))] = novos
        partes = RA._partes_de_rotulo(units, passe1, df_max)
        toks = {id(e): RA._tokens_headings(RA.collect_entry_unit_signals(e, texto), GENERIC) for e, texto, _, _ in passe1}
        conf = [(e, u, m) for e, _, u, m in passe1
                if m and m.topic_slug and not m.ambiguous and m.confidence >= conf_min]
        termos = {}
        for (u, t), als in added.items():
            for a in sorted(als):
                parte = a in partes.get((u, t), set())
                doad = [] if parte else sorted(str(e.get("id")) for e, uu, m in conf
                                               if uu == u and str(m.topic_slug) == t and a in toks[id(e)])
                termos[f"{u}|{t}|{a}"] = {"origem": "parte_de_rotulo" if parte else "propagado", "doadores": doad}
        mudancas = []
        for e, texto, u, m in passe1:
            s, rs = e.get("computed_subunit_slug"), list(e.get("subunit_match_reasons") or [])
            if (s, rs) == antes[id(e)]:
                continue
            tn = RA.normalize_match_text(f"{e.get('title') or ''} {texto or ''}")
            pres = sorted(a for a in added.get((u, str(s or "")), set()) if RA._frase_no_texto(tn, a))
            mudancas.append({"eid": str(e.get("id")), "unidade": u, "sub_1a": str(getattr(m, "topic_slug", "") or ""),
                             "sub_2a": str(s or ""), "razao": rs[-1] if rs else "",
                             "termos_presentes": [{"termo": a, **termos[f"{u}|{s}|{a}"]} for a in pres]})
        REG["prop"][wz2.CTX["sig"]] = {"mudou": n, "termos": termos, "mudancas": mudancas,
                                       "slugs_repetidos": {k: v for k, v in CUR["rep"].items() if v >= 2}}
        return n

    raizes = {sig: wz.root_de(sig, compare.mede.NOMES) for sig in compare.mede.NOMES}
    estado = {}
    for sig in compare.mede.NOMES:
        saved, bloco_novo, decisoes, _ = rb.replay(raizes[sig])
        estado[sig] = {"root": raizes[sig], "saved": saved, "decisoes": decisoes,
                       "feed": [wz2.copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
    print("bloco ok", round(time.time() - t0), "s", flush=True)
    RA.propagar_vocabulario_por_headings, RA._subtopico_nomeado_no_titulo = prop_wrapper, tit_wrapper
    try:
        novo = wz2.rodar("base", estado, ru, compare, pontuar=False)
    finally:
        RA.propagar_vocabulario_por_headings, RA._subtopico_nomeado_no_titulo = orig_prop, orig_tit

    # fidelidade por ID contra a captura congelada do W-Z2 (sem gold)
    cong = wz2.read(wz2.CAP_BASE)
    assert cong["sha256_base"].startswith("f941ac33")
    div = [[s, i] for s in novo for i in set(novo[s]) | set(cong["base"][s])
           if (novo[s].get(i) or {}).get("final") != (cong["base"][s].get(i) or {}).get("final")]
    print("FIDELIDADE instrumentada x congelada:", "igual" if not div else div[:5], flush=True)
    assert not div, "instrumentacao mudou decisao"
    sha_reg = wz2.sha(REG)

    # ======================= gold entra aqui (só avaliação)
    wz.preparar_avaliacao(estado, compare, compare.mede, wx)
    gsp_de, gid_de, pontuado = {}, {}, {}
    for sig, v in estado.items():
        gsp_de[sig] = v["golds"][3]
        gid_de[sig] = {e: g for g, e in v["eid_de"].items() if e}
        pontuado[sig] = {r["entry_id"] for r in v["rows"] if r["sub_primario"] != ""}

    def gold(sig, eid):
        g = gid_de[sig].get(eid)
        return sorted(gsp_de[sig][g]) if g in pontuado[sig] else None

    saidas = {sig: {eid: {k: (r.get("final") or {}).get(k) for k in ("bloco", "unidade", "sub")}
                    for eid, r in novo[sig].items() if "final" in r} for sig in novo}
    placar_curso, _ = wz.avaliar(estado, saidas)
    placar = {k: sum(c.get(k, 0) for c in placar_curso.values())
              for k in ("bloco", "bloco_n", "unidade", "unidade_n", "sub_primaria", "sub_n")}
    print("PLACAR", placar, flush=True)

    tit = REG["titulo"]
    for r in tit:
        r["gold"] = gold(r["curso"], r["eid"])
    ident = {"chamadas_regra_titulo": len(tit),
             "vencedor_com_slug_repetido": sum(r["slug_repetido"] for r in tit),
             "frases_diferentes_do_par": sum(not r["frases_iguais"] for r in tit),
             "resultado_muda_com_par": [r for r in tit if r["resultado_atual"] != r["resultado_por_par"]],
             "slugs_repetidos_por_curso": {s: v["slugs_repetidos"] for s, v in REG["prop"].items()}}

    efeitos = collections.Counter()
    for sig, p in REG["prop"].items():
        for mu in p["mudancas"]:
            g = gold(sig, mu["eid"])
            mu["gold"] = g
            if g is None:
                mu["efeito"] = "sem_gold"
            else:
                a, d = mu["sub_1a"] in g, mu["sub_2a"] in g
                mu["efeito"] = "ganho" if d and not a else "perda" if a and not d else "certo_mantido" if a else "erro_mantido"
            for tp in mu["termos_presentes"]:
                com = [x for x in tp["doadores"] if gold(sig, x) is not None]
                sub1 = {x: (novo[sig].get(x, {}).get("sub_1a") or {}).get("slug") for x in com}
                tp["doadores_com_gold"] = len(com)
                tp["doadores_certos_1a"] = sum(1 for x in com if sub1[x] in (gold(sig, x) or []))
            origens = {tp["origem"] for tp in mu["termos_presentes"]} or {"nenhum_termo_acrescentado"}
            for o in origens:
                efeitos[(mu["razao"], o, mu["efeito"])] += 1
    res = {"teste_minimo": minimo, "fidelidade": "igual", "placar": placar, "placar_por_curso": placar_curso,
           "sha256_registro_pre_gold": sha_reg, "identidade": ident,
           "propagacao_por_curso": REG["prop"],
           "efeitos_razao_origem": [[r, o, e, n] for (r, o, e), n in sorted(efeitos.items())],
           "segundos": round(time.time() - t0)}
    (OUT.with_suffix(".json")).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("IDENTIDADE", {k: (len(v) if isinstance(v, list) else v) for k, v in ident.items() if k != "slugs_repetidos_por_curso"})
    print("EFEITOS", res["efeitos_razao_origem"])
    print("segundos", res["segundos"])


if __name__ == "__main__":
    main()
