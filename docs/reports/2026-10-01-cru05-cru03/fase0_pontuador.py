"""Fase 0 (pré-registro preregistro-fase0-pontuador.md, sha256 68ff436f…): medição descritiva de termos pouco
discriminantes no pontuador da subunidade. Sem gold, sem regra; instrumentação só em memória. Cursos MF, SO, IA, ES2, TCC.

Uso: python -B fase0_pontuador.py --worktree <src base> --referencia replay_base.json --saida <json>
"""
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import socket
import statistics
import sys
import time
from pathlib import Path

PRINCIPAL = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
C13 = PRINCIPAL / "docs/reports/_harness-2026-09-04/c1-3"
DEV = ("MF", "SO", "IA", "ES2", "TCC")
F_MAT_LIM = 0.25
CAMPOS_FRASE = [("markdown_headings_text", 4.4), ("title_text", 3.8), ("markdown_lead_text", 2.8),
                ("manual_tags_text", 3.0), ("markdown_text", 1.1), ("auto_tags_text", 0.22),
                ("legacy_tags_text", 0.15), ("raw_text", 0.9)]
CAMPOS_TOK = [("markdown_headings_text", True), ("title_text", True), ("markdown_lead_text", False),
              ("manual_tags_text", True), ("markdown_text", False), ("auto_tags_text", True),
              ("legacy_tags_text", False), ("raw_text", True)]


def sem_rede(*a, **k):
    raise AssertionError("rede vedada")


def main():
    p = argparse.ArgumentParser()
    for nome in ("--worktree", "--referencia", "--saida"):
        p.add_argument(nome, required=True)
    a = p.parse_args()
    t0 = time.time()
    socket.socket.connect = sem_rede
    socket.create_connection = sem_rede
    sys.dont_write_bytecode = True
    wt, saida = Path(a.worktree).resolve(), Path(a.saida).resolve()
    if saida.is_relative_to(PRINCIPAL.resolve()):
        raise SystemExit("--saida dentro da árvore principal")
    sys.path.insert(0, str(wt))
    import src
    src.__path__ = [str(wt / "src")]
    spec = importlib.util.spec_from_file_location("wz2", C13 / "wz2_diagnostico_causal_23-09.py")
    wz2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wz2)
    compare = wz2.load("d_cmp", C13 / "compara_herancas_15-09.py")
    rb = wz2.load("d_rb", C13 / "replay_bloco_21-09.py")
    ru = wz2.load("d_ru", C13 / "replay_unidade_21-09.py")
    wz = wz2.load("d_wz", C13 / "wz_bloco_cobertura_22-09.py")
    IX = sys.modules["src.builder.timeline.index"]
    FMm = sys.modules["src.builder.routing.file_map"]
    T = sys.modules["src.builder.routing.thresholds"].T
    N = IX._normalize_match_text

    # ------------------------------------------------------------------ captura da 1ª passada (só em memória)
    CAP = collections.defaultdict(dict)
    TAX = {}
    orig_sub = ru.auto_sub

    def cap_sub(entry, taxonomy, markdown_text, winning_unit_slug="", **kw):
        m = orig_sub(entry, taxonomy, markdown_text, winning_unit_slug=winning_unit_slug, **kw)
        if wz2.CTX.get("fase") == "1a":
            sig, eid = wz2.CTX["sig"], str(entry.get("id"))
            reg = CAP[sig].setdefault(eid, {"chamadas": 0})
            reg["chamadas"] += 1
            reg.update(unidade=str(winning_unit_slug or ""), sinais=ru.collect_entry_unit_signals(entry, markdown_text),
                       slug=str(m.topic_slug or ""), amb=bool(m.ambiguous),
                       titulo_id=f"{entry.get('title') or ''} {entry.get('id') or ''}")
            TAX.setdefault(sig, ru._iter_content_taxonomy_topics(taxonomy))
        return m

    nomes = compare.mede.NOMES
    estado = {}
    for sig in DEV:
        root = wz.root_de(sig, nomes)
        saved, bloco_novo, decisoes, _ = rb.replay(root)
        estado[sig] = {"root": root, "saved": saved, "decisoes": decisoes,
                       "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
    ru.auto_sub = cap_sub
    try:
        cap = wz2.rodar("base", estado, ru, compare, pontuar=False)
    finally:
        ru.auto_sub = orig_sub

    # ------------------------------------------------------------------ fidelidade 1: decisões finais
    ref = json.loads(Path(a.referencia).read_text(encoding="utf-8"))["decisoes"]
    div = [[s, e] for s in DEV for e in sorted(set(cap[s]) | set(ref.get(s, {})))
           if not e.startswith("__") and {k: ((cap[s].get(e) or {}).get("final") or {}).get(k) for k in ("bloco", "unidade", "sub")}
           != ref.get(s, {}).get(e)]
    src_fora = sorted(n for n, m in sys.modules.items() if (n == "src" or n.startswith("src.")) and getattr(m, "__file__", None)
                      and not Path(m.__file__).resolve().is_relative_to(wt))

    # ------------------------------------------------------------------ decomposição (espelho, conferido contra o real)
    def frases_do_topico(t):
        label = IX._collapse_ws(str(t.get("topic_label", "") or ""))
        slug = IX._collapse_ws(str(t.get("topic_slug", "") or ""))
        aliases = [str(x) for x in (t.get("aliases", []) or []) if IX._collapse_ws(str(x))]
        ph = {}
        if label:
            ph[N(label)] = (1.0, label)
        for al in aliases:
            an = N(al)
            if an and (an not in ph or ph[an][0] < 0.82):
                ph[an] = (0.82, an)
        if slug:
            sp = slug.replace("-", " ")
            sn = N(sp)
            if sn and sn not in ph:
                ph[sn] = (0.65, sp)
        ph.pop("", None)
        return label, slug, aliases, ph

    def tokens_do_topico(t, label, slug, aliases):
        generic = set(t.get("generic_tokens") or []) or IX.UNIT_GENERIC_TOKENS
        short = set(t.get("short_vocab") or [])

        def conta(tok):
            return len(tok) >= 4 or tok in short
        tt = {tok for tok in N(label).split() if conta(tok) and tok not in generic}
        for al in aliases:
            tt.update(tok for tok in N(al).split() if conta(tok) and tok not in generic)
        if slug:
            seqs = [N(label).split()] + [N(al).split() for al in aliases]
            proprios = {tok for s in seqs for tok in s}
            fusoes = {"".join(s[i:i + j]) for s in seqs for j in (2, 3) for i in range(len(s) - j + 1)} - proprios
            tt.update(tok for tok in N(slug.replace("-", " ")).split() if conta(tok) and tok not in generic and tok not in fusoes)
        return tt, short

    def sinal_tokens(sinais, short):
        return {tok for campo, forte in CAMPOS_TOK for tok in sinais.get(campo, "").split()
                if len(tok) >= 4 or (forte and tok in short)}

    def decompoe(sinais, t):
        label, slug, aliases, ph = frases_do_topico(t)
        if not label and not slug and not aliases:
            return None
        avals = [(campo, chave, peso * fator, bool(IX._matches_normalized_phrase(sinais.get(campo, ""), frase, False)))
                 for campo, peso in CAMPOS_FRASE for chave, (fator, frase) in ph.items()]
        hits = [(c, k, v) for c, k, v, ok in avals if ok]
        tt, short = tokens_do_topico(t, label, slug, aliases)
        return {"hits": hits, "avals": avals, "tt": tt, "st": sinal_tokens(sinais, short), "chaves": list(ph),
                "cat": sinais.get("category_text", "") in {"listas", "gabaritos"}, "sub": str(t.get("kind", "") or "") == "subtopic",
                "auto": bool(sinais.get("auto_tags_text", "")), "legacy": bool(sinais.get("legacy_tags_text", ""))}

    def recompoe(d, excl_frase=frozenset(), excl_tok=frozenset()):
        if d is None:
            return 0.0
        score, exact = 0.0, 0
        for campo, chave, v in d["hits"]:
            if (campo, chave) in excl_frase:
                continue
            score += v
            exact += 1
        tt = d["tt"] - excl_tok
        ov = tt & d["st"]
        if not tt:
            pass
        elif len(tt) == 1:
            if ov:
                score += 0.9
        elif len(ov) >= len(tt):
            score += 1.4 + (0.22 * len(ov))
        elif len(ov) >= 2:
            score += 0.9 + (0.18 * len(ov))
        elif len(ov) == 1:
            score += 0.25
        if d["cat"] and ov:
            score += 0.08
        if d["sub"]:
            score += 0.04
        if exact == 0 and score > 0.0:
            score *= 0.72
        if exact == 0 and len(ov) <= 1:
            score *= 0.68
        if d["auto"] and exact == 0 and len(ov) <= 1:
            score *= 0.88
        if d["legacy"] and exact == 0:
            score *= 0.9
        return score

    def seleciona(scored, titulo_id):
        scored = sorted(scored, key=lambda x: x[1], reverse=True)
        if not scored:
            return "", "vazio"
        w, ws = scored[0]
        rs = scored[1][1] if len(scored) > 1 else 0.0
        if ws <= 0.0 or (len(scored) > 1 and ws - rs == 0.0):
            return "", "vazio"
        if FMm._REVISAO_RE.search(titulo_id) and ws < T.SUBUNIT_REVISAO_FLOOR:
            return "", "vazio"
        if len(scored) == 1:
            return w, "decidido"
        return w, ("ambiguo" if (ws - rs) / max(ws, 1e-6) < T.SUBUNIT_AMBIG_MARGIN else "decidido")

    # ------------------------------------------------------------------ frequências (sem gold)
    def casa(norm_txt, toks, frase_norm):
        return frase_norm in toks if " " not in frase_norm else frase_norm in norm_txt

    checagens = {"pares": 0, "dif_max": 0.0, "captura_ok": 0, "captura_falha": [], "matcher_ok": 0, "matcher_falha": 0}
    saida_cursos, materiais, inventario = {}, {}, {}
    for sig in DEV:
        topicos = TAX.get(sig) or []
        por_u = collections.defaultdict(list)
        for t in topicos:
            por_u[str(t.get("unit_slug", "") or "")].append(t)
        mats = CAP[sig]
        # textos normalizados por material e campo
        norm = {e: {c: N(r["sinais"].get(c, "")) for c, _ in CAMPOS_FRASE} for e, r in mats.items()}
        toks = {e: {c: IX._signal_token_set(v) for c, v in d.items()} for e, d in norm.items()}
        n_mat = max(1, len(mats))
        decomp_t = {id(t): frases_do_topico(t) for t in topicos}
        short_curso = set((topicos[0].get("short_vocab") if topicos else None) or [])
        sinal_tok_mat = {e: sinal_tokens(r["sinais"], short_curso) for e, r in mats.items()}
        f_mat_frase, f_mat_tok = {}, collections.Counter()
        for t in topicos:
            for chave in decomp_t[id(t)][3]:
                if chave in f_mat_frase:
                    continue
                f_mat_frase[chave] = {c: sum(1 for e in mats if casa(norm[e][c], toks[e][c], chave)) / n_mat for c, _ in CAMPOS_FRASE}
        for e in mats:
            f_mat_tok.update(sinal_tok_mat[e])
        f_top_frase, f_top_tok = {}, {}
        for u, ts in por_u.items():
            chaves_t = [list(decomp_t[id(t)][3]) for t in ts]
            for ks in chaves_t:
                for k in ks:
                    f_top_frase[(u, k)] = sum(1 for ks2 in chaves_t if any(casa(q, IX._signal_token_set(q), k) for q in ks2))
            tts = [tokens_do_topico(t, *decomp_t[id(t)][:3])[0] for t in ts]
            for tt in tts:
                for k in tt:
                    f_top_tok[(u, k)] = sum(1 for tt2 in tts if k in tt2)

        reg_curso = collections.Counter()
        fracoes = {"top": [], "mat": [], "qualquer": []}
        uso_baixo = collections.Counter()
        for e, r in sorted(mats.items()):
            u = r["unidade"]
            ts = por_u.get(u, []) if u else topicos
            decs = [(t, decompoe(r["sinais"], t)) for t in ts]
            for t, d in decs:
                real = float(ru._score_entry_against_taxonomy_topic(r["sinais"], t))
                dif = abs(real - recompoe(d))
                checagens["pares"] += 1
                checagens["dif_max"] = max(checagens["dif_max"], dif)
                if d:
                    for campo, chave, _, real_ok in d["avals"]:
                        ok = casa(norm[e][campo], toks[e][campo], chave) == real_ok
                        checagens["matcher_ok" if ok else "matcher_falha"] += 1
            base_w, base_st = seleciona([(str(t.get("topic_slug")), recompoe(d)) for t, d in decs], r["titulo_id"])
            esperado = ("", "vazio") if not r["slug"] else (r["slug"], "ambiguo" if r["amb"] else "decidido")
            if (base_w, base_st) == esperado:
                checagens["captura_ok"] += 1
            else:
                checagens["captura_falha"].append([sig, e, [base_w, base_st], list(esperado)])
            ex_top_f = {(c, k) for c, _ in CAMPOS_FRASE for t, d in decs if d for k in d["chaves"] if f_top_frase.get((u, k), 1) >= 2}
            ex_top_t = {k for t, d in decs if d for k in d["tt"] if f_top_tok.get((u, k), 1) >= 2}
            ex_mat_f = {(c, k) for c, _ in CAMPOS_FRASE for t, d in decs if d for k in d["chaves"]
                        if f_mat_frase.get(k, {}).get(c, 0.0) > F_MAT_LIM}
            ex_mat_t = {k for t, d in decs if d for k in d["tt"] if f_mat_tok[k] / n_mat > F_MAT_LIM}
            versoes = {"R_top": (ex_top_f, ex_top_t), "R_mat": (ex_mat_f, ex_mat_t),
                       "R_both": (ex_top_f | ex_mat_f, ex_top_t | ex_mat_t)}
            rec = {"unidade": u, "chamadas": r["chamadas"], "base": [base_w, base_st]}
            for nome, (xf, xt) in versoes.items():
                w2, st2 = seleciona([(str(t.get("topic_slug")), recompoe(d, xf, xt)) for t, d in decs], r["titulo_id"])
                rec[nome] = [w2, st2]
                reg_curso[f"{nome}_argmax_muda"] += w2 != base_w
                reg_curso[f"{nome}_estado_muda"] += st2 != base_st
            if base_w:
                reg_curso["com_vencedor"] += 1
                d = next(d for t, d in decs if str(t.get("topic_slug")) == base_w)
                tot = sum(v for _, _, v in d["hits"])
                if tot > 0:
                    pt = sum(v for c, k, v in d["hits"] if (c, k) in ex_top_f)
                    pm = sum(v for c, k, v in d["hits"] if (c, k) in ex_mat_f)
                    pq = sum(v for c, k, v in d["hits"] if (c, k) in ex_top_f or (c, k) in ex_mat_f)
                    fracoes["top"].append(pt / tot)
                    fracoes["mat"].append(pm / tot)
                    fracoes["qualquer"].append(pq / tot)
                    rec["fracao_frases_vencedor"] = {"top": round(pt / tot, 4), "mat": round(pm / tot, 4), "qualquer": round(pq / tot, 4)}
                    for c, k, v in d["hits"]:
                        if (c, k) in ex_top_f or (c, k) in ex_mat_f:
                            uso_baixo[k] += 1
                else:
                    reg_curso["vencedor_sem_frase"] += 1
            materiais[f"{sig}|{e}"] = rec

        def resumo(xs):
            if not xs:
                return None
            q = statistics.quantiles(xs, n=4) if len(xs) >= 2 else [xs[0]] * 3
            return {"n": len(xs), "q1": round(q[0], 4), "mediana": round(statistics.median(xs), 4), "q3": round(q[2], 4),
                    "frac_maior_que_0": round(sum(1 for x in xs if x > 0) / len(xs), 4)}
        saida_cursos[sig] = {"materiais_1a": len(mats), **dict(reg_curso),
                             "fracao_frases_vencedor": {k: resumo(v) for k, v in fracoes.items()}, "_fracoes": fracoes}
        inventario[sig] = {
            "frases_F_top_ge2": sorted({k for (u, k), n in f_top_frase.items() if n >= 2}),
            "frases_F_mat_gt_lim": {k: {c: round(v, 3) for c, v in fm.items() if v > F_MAT_LIM}
                                    for k, fm in f_mat_frase.items() if any(v > F_MAT_LIM for v in fm.values())},
            "tokens_F_top_ge2": sorted({k for (u, k), n in f_top_tok.items() if n >= 2}),
            "uso_no_vencedor_de_frases_pouco_discriminantes": dict(uso_baixo.most_common()),
        }

    todas = {k: [x for s in DEV for x in saida_cursos[s]["_fracoes"][k]] for k in ("top", "mat", "qualquer")}
    total = collections.Counter()
    for s in DEV:
        total.update({k: v for k, v in saida_cursos[s].items() if isinstance(v, int)})
    for s in DEV:
        saida_cursos[s].pop("_fracoes")
    med = statistics.median(todas["qualquer"]) if todas["qualquer"] else 0.0
    inv_both = total["R_both_argmax_muda"] / max(1, total["com_vencedor"])
    fiel = not div and not src_fora and not checagens["captura_falha"] and checagens["dif_max"] < 1e-9 and not checagens["matcher_falha"]
    indicativo = ("inconclusivo: fidelidade falhou" if not fiel else
                  "perde força" if med < 0.10 and inv_both < 0.05 else
                  "ganha força" if med > 0.25 or inv_both > 0.25 else "inconclusivo")
    res = {"preregistro_sha256": "68ff436fe699991c4888887ff5edc06cff75f382a1c9dd9642670c0cd41ab2dd",
           "worktree": str(wt), "cursos": list(DEV), "f_mat_limiar": F_MAT_LIM,
           "identidade": {n: hashlib.sha256(Path(sys.modules[n].__file__).read_bytes()).hexdigest()
                          for n in ("src.builder.timeline.index", "src.builder.routing.file_map", "src.builder.text.normalize")},
           "fidelidade": {"decisoes_divergentes": div, "src_fora": src_fora, **checagens, "integral": fiel},
           "total": {**dict(total), "mediana_fracao_qualquer": round(med, 4), "argmax_muda_R_both_sobre_com_vencedor": round(inv_both, 4),
                     "fracao_frases_vencedor": {k: (lambda xs: None if not xs else {"n": len(xs), "mediana": round(statistics.median(xs), 4)})(v)
                                                for k, v in todas.items()}},
           "criterio_indicativo": indicativo, "por_curso": saida_cursos, "inventario": inventario, "materiais": materiais,
           "segundos": round(time.time() - t0)}
    saida.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("fidelidade:", fiel, "| div", len(div), "| src fora", src_fora or "nenhum", "| pares", checagens["pares"],
          "| dif_max", checagens["dif_max"], "| captura ok/falha", checagens["captura_ok"], len(checagens["captura_falha"]),
          "| matcher ok/falha", checagens["matcher_ok"], checagens["matcher_falha"])
    print("total:", json.dumps(res["total"], ensure_ascii=False))
    print("critério indicativo:", indicativo, "| segundos", res["segundos"])
    return 0 if fiel else 1


if __name__ == "__main__":
    sys.exit(main())
