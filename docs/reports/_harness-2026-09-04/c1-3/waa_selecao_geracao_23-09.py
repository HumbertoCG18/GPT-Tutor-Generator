"""W-AA (23/09): selecao por funcao+extensao (S) e geracao local por subordinacao (G), fatorial 2x2 sobre a base
congelada do W-Z2. 0 mudanca em src/tests/regua/defaults/configuracao persistida.

Desenho e definicoes: docs/reports/2026-09-23-waa-desenho.md, secoes 3 (mecanismo) e 7 (ajustes de interpretacao e
detalhes de implementacao, registrados antes da execucao). Autorizacao literal: c1-3/waa_pedido_execucao_23-09.md.

BRACOS: base = congelamento W-Z2 (.frzero/wz2_captura_base_23-09.json); A = S; B' = G com selecao atual; B = G + S.
Cada braco e um replay real (replay_bloco_21-09 -> replay_unidade_21-09) com o seletor da subunidade (`auto_sub`, usado
nas duas passadas) trocado em memoria e restaurado no finally. Bloco e unidade nao mudam por construcao; conferido por ID.
Decisoes dos 3 bracos congeladas por sha256 ANTES de ler qualquer gold.

S (funcao + extensao): secoes = headings markdown do texto que o seletor le (>= 2), senao itens numerados de 1o nivel
(>= 2); secao 0 = titulo + preambulo. Papel pelo rotulo da secao (lexico fixo abaixo; termo que aparece em rotulo/alias de
topico do curso e ignorado naquele curso). Ocorrencia = casamento exato de frase do seletor (rotulo, aliases, slug).
Extensao(T) = n de secoes de papel principal com ocorrencia de T. Primario = maior extensao; empate -> escore atual (exato);
sem ocorrencia em secao principal -> decisao atual. Decisao de S que troca o topico mantem a confianca original e fica nao
ambigua.

G (subordinacao local): expressoes fortes do material (W-P1); relacoes admissiveis P1 (heading/item de OUTRO material sob
heading ancestral que menciona T) e P4 so no plano de ensino/ementa de _inputs; excluidos P2, P3, GLOSSARY/IDENTITY/REGISTRY,
o proprio material, campos computados, gold. Exclusividade: a expressao liga exatamente 1 topico da unidade prevista (a da
base). Uso: alias local so para aquele material (copia da taxonomia por chamada); nenhum alias global.

Sem build, rede, LLM, commit. Uso: python waa_selecao_geracao_23-09.py [--reavaliar]
"""
import collections
import copy
import hashlib
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

T0 = time.time()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.path.insert(0, str(DATA))
OUT_JSON = HERE / "waa_selecao_geracao_23-09.json"
OUT_MD = HERE / "waa_selecao_geracao_23-09.md"
CAP_WAA = DATA / ".frzero/waa_captura_bracos_23-09.json"
CAP_WZ2 = DATA / ".frzero/wz2_captura_base_23-09.json"

from src.builder.timeline.index import _normalize_match_text, _signal_token_set  # noqa: E402

LEXICO = {
    "revisao": ["revisao", "relembrando", "recapitulando", "retomando"],
    "prerequisito": ["pre requisito", "pre requisitos", "prerequisito", "prerequisitos", "conhecimentos previos", "fundamentos previos"],
    "exemplo": ["exemplo", "exemplos", "exemplificando"],
    "comparacao": ["comparacao", "comparativo", "versus", "vs", "diferencas"],
    "indice": ["sumario", "agenda", "objetivos", "referencias", "bibliografia", "leituras", "links", "proxima aula"],
}
HEAD_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*\S)\s*$")
ITEM_RE = re.compile(r"^\s{0,3}\d{1,2}[.)]\s+\S")
FONTES_P4 = ("_inputs_15-09.json:teaching_plan", "_inputs_15-09.json:syllabus")
CTX = {"sig": None, "braco": None, "fase": "1a"}
CAP = {}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------------------- S
def lexico_do_curso(taxonomia):
    frases = set()
    for u in taxonomia.get("units", []) or []:
        for t in u.get("topics", []) or []:
            for f in [t.get("label")] + list(t.get("aliases") or []):
                n = _normalize_match_text(str(f or ""))
                if n:
                    frases.add(" " + n + " ")
    return {p: [c for c in termos if not any(" " + c + " " in f for f in frases)] for p, termos in LEXICO.items()}


def papel(rotulo, lexico):
    n = " " + _normalize_match_text(rotulo or "") + " "
    for p, termos in lexico.items():
        if any(" " + c + " " in n for c in termos):
            return p
    return "principal"


def secoes(titulo, texto):
    linhas = (texto or "").splitlines()
    heads = [i for i, l in enumerate(linhas) if HEAD_RE.match(l)]
    if len(heads) >= 2:
        inicios, tipo = heads, "heading"
    else:
        itens = [i for i, l in enumerate(linhas) if ITEM_RE.match(l)]
        inicios, tipo = (itens, "item") if len(itens) >= 2 else ([], "nenhum")
    out = [(titulo or "", "\n".join(linhas[:inicios[0]] if inicios else linhas))]
    for k, s in enumerate(inicios):
        fim = inicios[k + 1] if k + 1 < len(inicios) else len(linhas)
        m = HEAD_RE.match(linhas[s])
        rot = m.group(1) if (tipo == "heading" and m) else linhas[s].strip()
        out.append((rot, "\n".join(linhas[s + 1:fim])))
    return out, tipo


def frases_do_topico(t):
    fs = {_normalize_match_text(str(t.get("topic_label") or ""))}
    fs |= {_normalize_match_text(str(a)) for a in (t.get("aliases") or [])}
    fs.add(_normalize_match_text(str(t.get("topic_slug") or "").replace("-", " ")))
    fs.discard("")
    return fs


def ocorre(sec_norm, sec_toks, frases):
    for f in frases:
        if (" " not in f and f in sec_toks) or (" " in f and f in sec_norm):
            return True
    return False


# ------------------------------------------------------------------------------------------- G
def aumenta(taxonomia, unidade, locais):
    if not locais:
        return taxonomia
    tax = copy.deepcopy(taxonomia)
    for u in tax.get("units", []) or []:
        if str(u.get("slug") or "") != unidade:
            continue
        for t in u.get("topics", []) or []:
            extra = locais.get(str(t.get("slug") or ""))
            if extra:
                t["aliases"] = list(t.get("aliases") or []) + sorted(set(extra))
    return tax


def relacoes_locais(sig, eid, unidade, chaves, formas, indice):
    """{topico: [forma,...]} e proveniencia, so relacoes de subordinacao exclusivas na unidade prevista."""
    locais, prov = collections.defaultdict(list), []
    for e in chaves:
        rels = [r for r in indice.get((sig, e), [])
                if r["doc"] != "material:" + eid and (
                    (r["padrao"] == "P1" and r["doc"].startswith("material:")) or (r["padrao"] == "P4" and r["doc"] in FONTES_P4))]
        na_unidade = {r["topico"] for r in rels if r["unit_slug"] == unidade}
        if len(na_unidade) != 1 or not formas.get(e):
            continue
        t = next(iter(na_unidade))
        locais[t].append(formas[e])
        r0 = next(r for r in rels if r["unit_slug"] == unidade)
        prov.append({"expressao": e, "forma": formas[e], "topico": t, "doc": r0["doc"], "padrao": r0["padrao"],
                     "trecho": r0["trecho"], "topicos_no_curso": len({(r["unit_slug"], r["topico"]) for r in rels}),
                     "n_relacoes": len(rels)})
    return dict(locais), prov


# ------------------------------------------------------------------------------------------- replay por braco
def rodar(braco, estado, ru, compare, usa_s, usa_g, locais_de, lexicos, base_unidade):
    RA = ru.RA
    orig_sub, orig_read, orig_prop = ru.auto_sub, ru.read, RA.propagar_vocabulario_por_headings
    CAP[braco] = {}

    def prop_wrapper(*a, **k):
        CTX["fase"] = "2a"
        try:
            return orig_prop(*a, **k)
        finally:
            CTX["fase"] = "1a"

    def sub_wrapper(entry, taxonomy, markdown_text, winning_unit_slug="", **kw):
        sig, eid = CTX["sig"], str(entry["id"])
        rec = CAP[braco][sig].setdefault(eid, {})
        u = str(winning_unit_slug or "")
        if u != base_unidade[sig].get(eid, u):
            rec["unidade_divergente"] = True
        tax = aumenta(taxonomy, u, locais_de[sig].get(eid) or {}) if usa_g else taxonomy
        m = orig_sub(entry, tax, markdown_text, winning_unit_slug=winning_unit_slug, **kw)
        info = {"orig": str(m.topic_slug or ""), "orig_conf": round(float(m.confidence or 0), 6), "orig_amb": bool(m.ambiguous)}
        if not usa_s:
            rec["sub_" + CTX["fase"]] = info
            return m
        topicos = [t for t in (ru._iter_content_taxonomy_topics(tax) or []) if not u or str(t.get("unit_slug") or "") == u]
        secs, tipo = secoes(str(entry.get("title") or ""), markdown_text)
        lex = lexicos[sig]
        sec_info = []
        for rot, corpo in secs:
            n = _normalize_match_text(rot + "\n" + corpo)
            sec_info.append((papel(rot, lex), n, _signal_token_set(n), _normalize_match_text(rot)))
        sinais = ru.collect_entry_unit_signals(entry, markdown_text)
        ext, aux, rotulos = {}, {}, {}
        for t in topicos:
            fs = frases_do_topico(t)
            slug = str(t.get("topic_slug") or "")
            oc = [(pp, rn) for pp, n, toks, rn in sec_info if ocorre(n, toks, fs)]
            ext[slug] = sum(1 for pp, _ in oc if pp == "principal")
            aux[slug] = sum(1 for pp, _ in oc if pp != "principal")
            rotulos[slug] = [rn for pp, rn in oc if pp == "principal"]
        info.update({"n_secoes": len(secs), "tipo": tipo, "papeis": dict(collections.Counter(p for p, *_ in sec_info)),
                     "rotulos_distintos": len({rn for *_, rn in sec_info})})
        melhor = max(ext.values()) if ext else 0
        if melhor == 0:
            info["s_agiu"] = False
            rec["sub_" + CTX["fase"]] = info
            return m
        esc = {str(t.get("topic_slug") or ""): float(ru._score_entry_against_taxonomy_topic(sinais, t)) for t in topicos}
        ordem = {str(t.get("topic_slug") or ""): i for i, t in enumerate(topicos)}
        cands = sorted((s for s in ext if ext[s] == melhor), key=lambda s: (-esc.get(s, 0.0), ordem[s]))
        escolhido = cands[0]
        info.update({"s_agiu": True, "escolhido": escolhido, "ext_max": melhor, "empate_ext": len(cands) > 1,
                     "ext": {s: v for s, v in ext.items() if v}, "aux": {s: v for s, v in aux.items() if v},
                     "dup_rotulos_do_escolhido": len(rotulos[escolhido]) - len(set(rotulos[escolhido])),
                     "escore": {s: round(v, 4) for s, v in esc.items() if v > 0}})
        rec["sub_" + CTX["fase"]] = info
        if escolhido == str(m.topic_slug or ""):
            return m
        t = next(t for t in topicos if str(t.get("topic_slug") or "") == escolhido)
        return ru.TopicMatchResult(topic_slug=escolhido, topic_label=str(t.get("topic_label") or ""), unit_slug=u,
                                   confidence=float(m.confidence or 0.0), ambiguous=False,
                                   reasons=list(m.reasons) + [f"waa-S:ext={melhor}"])

    try:
        ru.auto_sub = sub_wrapper
        RA.propagar_vocabulario_por_headings = prop_wrapper
        for sig, v in estado.items():
            CTX["sig"], CTX["fase"] = sig, "1a"
            CAP[braco][sig] = {}
            feed = [copy.deepcopy(e) for e in v["feed"]]

            def patched(path, _feed=feed):
                data = orig_read(path)
                if Path(path).name == "manifest.json":
                    data = {**data, "entries": _feed}
                return data

            ru.read = patched
            try:
                _, novo, _ = ru.replay(v["root"])
            finally:
                ru.read = orig_read
            for eid, e in novo.items():
                CAP[braco][sig].setdefault(eid, {})["final"] = {
                    "bloco": compare.predictions(v["root"], e)[0], "unidade": str(e.get("computed_unit_slug") or ""),
                    "sub": str(e.get("computed_subunit_slug") or ""),
                    "sub_reasons": [str(r) for r in e.get("subunit_match_reasons") or []]}
            print("  braco", braco, sig, len(novo), round(time.time() - T0), "s", flush=True)
    finally:
        ru.auto_sub, ru.read = orig_sub, orig_read
        RA.propagar_vocabulario_por_headings = orig_prop
        CTX["fase"] = "1a"


# ------------------------------------------------------------------------------------------- main
def main():
    reavaliar = "--reavaliar" in sys.argv
    if not reavaliar:
        assert not OUT_JSON.exists(), "preservar evidencia existente"
    compare = load("waa_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    wx = load("waa_wx", HERE / "wx_regua_corrigida_22-09.py")
    rb = load("waa_rb", HERE / "replay_bloco_21-09.py")
    ru = load("waa_ru", HERE / "replay_unidade_21-09.py")
    wz = load("waa_wz", HERE / "wz_bloco_cobertura_22-09.py")
    z2 = load("waa_z2", HERE / "wz2_diagnostico_causal_23-09.py")
    wu = load("waa_wu", HERE / "wu_cobertura_relacoes_22-09.py")
    wp1 = load("waa_wp1", HERE / "wp1_inventario_matriz_22-09.py")
    from src.builder.core.code_summarization import load_code_curation
    nomes = mede.NOMES
    raizes = {s: wz.root_de(s, nomes) for s in nomes}
    sha_decl = sha({"doc": __doc__, "lexico": LEXICO, "fontes_p4": FONTES_P4})
    print("DECLARACAO", sha_decl, flush=True)
    cz = read(CAP_WZ2)
    assert cz["sha256_base"].startswith("f941ac33"), "base congelada do W-Z2 inesperada"
    base = cz["base"]
    base_unidade = {s: {e: r["final"]["unidade"] for e, r in base[s].items() if isinstance(r, dict) and r.get("final")} for s in nomes}

    # bloco (D9 efetivo) e alimentacao
    estado, d9 = {}, {}
    for sig in nomes:
        saved, bloco_novo, _, _ = rb.replay(raizes[sig])
        estado[sig] = {"root": raizes[sig], "saved": saved, "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
        d9[sig] = {"materiais": len(bloco_novo), "com_bloco_temporal": sum(1 for e in bloco_novo.values() if e.get("temporal_block_id"))}
    print("D9 efetivo (temporal_block_id no feed):", d9, flush=True)

    # G: indice documental v2 (mesmo do W-Z2) + formas das expressoes + pares locais (sem gold)
    expr_keys, universo = z2.expressoes_v2(wp1, raizes, nomes)
    indice = z2.indice_documental(wu, raizes, universo)
    locais_de, prov_de, lexicos = {}, {}, {}
    for sig in nomes:
        root = raizes[sig]
        lexicos[sig] = lexico_do_curso(read(root / "course/.content_taxonomy.json"))
        curation = load_code_curation(root).get("entries", {}) or {}
        ents = {str(e["id"]): e for e in read(root / "manifest.json")["entries"]}
        locais_de[sig], prov_de[sig] = {}, {}
        for eid, rec in base[sig].items():
            if not isinstance(rec, dict) or not rec.get("no_laco") or not rec.get("sub_1a"):
                continue
            formas = {}
            for _campo, cru in wp1.campos_do_material(root, ents[eid], curation):
                for k, f in wp1.ngramas(cru).items():
                    formas.setdefault(k, f)
            loc, prov = relacoes_locais(sig, eid, rec["final"]["unidade"], expr_keys[sig].get(eid, []), formas, indice)
            if loc:
                locais_de[sig][eid], prov_de[sig][eid] = loc, prov
    print("G pares locais:", {s: len(v) for s, v in locais_de.items()}, "lexicos:", {s: {p: len(t) for p, t in lx.items()} for s, lx in lexicos.items()}, flush=True)

    if reavaliar:
        cw = read(CAP_WAA)
        assert cw["sha256_declaracao"] == sha_decl
        for b in ("A", "Bp", "B"):
            CAP[b] = cw[b]
        sha_bracos = cw["sha256_bracos"]
    else:
        rodar("A", estado, ru, compare, True, False, locais_de, lexicos, base_unidade)
        rodar("Bp", estado, ru, compare, False, True, locais_de, lexicos, base_unidade)
        rodar("B", estado, ru, compare, True, True, locais_de, lexicos, base_unidade)
        sha_bracos = sha({b: CAP[b] for b in ("A", "Bp", "B")})
        CAP_WAA.write_text(json.dumps({"sha256_declaracao": sha_decl, "sha256_bracos": sha_bracos,
                                       **{b: CAP[b] for b in ("A", "Bp", "B")}}, ensure_ascii=False), encoding="utf-8")
    print("CONGELAMENTO bracos", sha_bracos[:16], flush=True)
    CAP["base"] = base

    # ================================================================ GOLD entra aqui
    wz.preparar_avaliacao(estado, compare, mede, wx)
    R = avaliar(estado, nomes, ru, locais_de, prov_de)
    R.update({"escopo": __doc__, "sha256_declaracao": sha_decl, "sha256_bracos": sha_bracos,
              "base_wz2": cz["sha256_base"], "d9_efetivo": d9, "lexicos_por_curso": lexicos,
              "g_pares_locais_por_curso": {s: len(v) for s, v in locais_de.items()},
              "segundos": round(time.time() - T0, 1)})
    OUT_JSON.write_text(json.dumps(R, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    escreve_md(R)
    print("OK", OUT_JSON.name, hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()[:16], R["segundos"], "s", flush=True)


def avaliar(estado, nomes, ru, locais_de, prov_de):
    bracos = ("base", "A", "Bp", "B")
    R = {"placar": {}, "mudancas": {}, "outros_eixos_identicos": {}, "materiais_sem_gold_alterados": {}}
    gold_ids = {}
    flags = {}
    for b in bracos:
        R["placar"][b], flags[b] = {}, {}
        for sig, v in estado.items():
            gb, gu, gs, gsp = v["golds"]
            c = collections.Counter()
            for row in v["rows"]:
                gid, eid = row["entry_id"], v["eid_de"].get(row["entry_id"])
                f = (CAP[b][sig].get(eid) or {}).get("final") if eid else None
                if row["bloco"] != "":
                    c["bloco_n"] += 1
                    c["bloco"] += bool(f and f["bloco"] == gb[gid])
                if row["unidade"] != "":
                    c["unidade_n"] += 1
                    c["unidade"] += bool(f and f["unidade"] in gu[gid])
                if row["sub_primario"] != "":
                    c["sub_n"] += 1
                    okp = bool(f and f["sub"] in gsp[gid])
                    c["sub_primaria"] += okp
                    c["sub_aceita"] += bool(f and f["sub"] in gs[gid])
                    flags[b][(sig, gid)] = {"ok": okp, "sub": (f or {}).get("sub", ""), "eid": eid}
                    gold_ids.setdefault(sig, set()).add(eid)
            R["placar"][b][sig] = dict(c)
        tot = collections.Counter()
        for c in R["placar"][b].values():
            tot.update(c)
        R["placar"][b]["TOTAL"] = dict(tot)
    for b in bracos[1:]:
        # outros eixos por ID (todos os materiais)
        dif = [(sig, eid) for sig in nomes for eid, r in CAP[b][sig].items()
               if (r.get("final") or {}).get("bloco") != ((CAP["base"][sig].get(eid) or {}).get("final") or {}).get("bloco")
               or (r.get("final") or {}).get("unidade") != ((CAP["base"][sig].get(eid) or {}).get("final") or {}).get("unidade")]
        R["outros_eixos_identicos"][b] = {"identicos": not dif, "divergentes": dif[:10],
                                          "unidade_divergente_na_chamada": sum(1 for sig in nomes for r in CAP[b][sig].values() if r.get("unidade_divergente"))}
        R["materiais_sem_gold_alterados"][b] = sum(
            1 for sig in nomes for eid, r in CAP[b][sig].items()
            if eid not in gold_ids.get(sig, set()) and (r.get("final") or {}).get("sub") != ((CAP["base"][sig].get(eid) or {}).get("final") or {}).get("sub"))
        g, p, alt = [], [], []
        ab = collections.Counter()
        for k, fb in flags["base"].items():
            fa = flags[b][k]
            if fa["sub"] != fb["sub"]:
                alt.append(fa["ok"])
                if not fb["sub"]:
                    ab["abstencao_para_certa" if fa["ok"] else "abstencao_para_errada"] += 1
                elif not fa["sub"]:
                    ab["decisao_para_abstencao_" + ("certa" if fa["ok"] else "errada")] += 1
            if fa["ok"] and not fb["ok"]:
                g.append(f"{k[0]}|{k[1]}")
            if fb["ok"] and not fa["ok"]:
                p.append(f"{k[0]}|{k[1]}")
            # direto (1a mudou) x indireto (so a final mudou)
        dir_ind = collections.Counter()
        for (sig, gid), fa in flags[b].items():
            fb = flags["base"][(sig, gid)]
            if fa["sub"] == fb["sub"]:
                continue
            eid = fa["eid"]
            b1 = (CAP["base"][sig].get(eid) or {}).get("sub_1a") or {}
            a1 = (CAP[b][sig].get(eid) or {}).get("sub_1a") or {}
            a1_final = a1.get("escolhido") if a1.get("s_agiu") else a1.get("orig")
            tipo = "direto_1a" if a1_final != b1.get("slug") else "indireto_2a"
            dir_ind[(tipo, "ganho" if fa["ok"] and not fb["ok"] else "perda" if fb["ok"] and not fa["ok"] else "neutro")] += 1
        R["mudancas"][b] = {"ganhos": sorted(g), "perdas": sorted(p), "saldo": len(g) - len(p), "abstencoes": dict(ab),
                            "alteradas_com_gold": len(alt), "precisao_alteradas": round(sum(alt) / len(alt), 3) if alt else None,
                            "direto_x_indireto": {f"{t}|{r}": n for (t, r), n in dir_ind.items()},
                            "cursos_que_regridem": [s for s in nomes if R["placar"][b][s].get("sub_primaria", 0) < R["placar"]["base"][s].get("sub_primaria", 0)]}
    # fatorial
    tb = {b: R["placar"][b]["TOTAL"].get("sub_primaria", 0) for b in bracos}
    R["fatorial"] = {"efeito_S": tb["A"] - tb["base"], "efeito_G": tb["Bp"] - tb["base"],
                     "interacao": tb["B"] - tb["A"] - tb["Bp"] + tb["base"], "B_menos_base": tb["B"] - tb["base"]}
    # aceite por braco
    R["aceite"] = {b: {"saldo_positivo": R["mudancas"][b]["saldo"] > 0, "zero_perda": not R["mudancas"][b]["perdas"],
                       "nenhum_curso_regride": not R["mudancas"][b]["cursos_que_regridem"],
                       "outros_eixos_identicos": R["outros_eixos_identicos"][b]["identicos"]} for b in bracos[1:]}
    # teste de sinal (exploratorio): gold em 1o pela ordem atual x pela ordem de S (1a passada do braco A)
    sinal = collections.Counter()
    for sig, v in estado.items():
        gsp = v["golds"][3]
        for row in v["rows"]:
            if row["sub_primario"] == "":
                continue
            gid, eid = row["entry_id"], v["eid_de"].get(row["entry_id"])
            s = next(iter(gsp[gid]))
            b1 = (CAP["base"][sig].get(eid) or {}).get("sub_1a") if eid else None
            a1 = (CAP["A"][sig].get(eid) or {}).get("sub_1a") if eid else None
            if not b1 or not a1:
                sinal["fora_do_laco"] += 1
                continue
            u = (CAP["base"][sig][eid].get("final") or {}).get("unidade")
            pont = [p for p in b1.get("pontuacoes") or [] if (not u or p[0] == u) and p[2] > 0]
            topo_atual = max(pont, key=lambda p: p[2])[1] if pont else ""
            topo_s = a1.get("escolhido") if a1.get("s_agiu") else a1.get("orig")
            sinal["gold_1o_ordem_atual"] += (topo_atual == s and s != "")
            sinal["gold_1o_ordem_S"] += (topo_s == s and s != "")
            sinal["s_agiu"] += bool(a1.get("s_agiu"))
            if a1.get("s_agiu") and s:
                ext, aux = a1.get("ext") or {}, a1.get("aux") or {}
                if ext.get(s, 0) == 0 and aux.get(s, 0) > 0:
                    sinal["gold_so_em_secao_auxiliar"] += 1
                if a1.get("dup_rotulos_do_escolhido", 0) > 0:
                    sinal["escolhido_com_rotulos_repetidos"] += 1
            bp1 = (CAP["Bp"][sig].get(eid) or {}).get("sub_1a") or {}
            if (locais_de.get(sig) or {}).get(eid, {}).get(s):
                sinal["G_liga_ao_gold"] += 1
    R["teste_de_sinal"] = dict(sinal)
    # G: proveniencia, novo x reforco, unicidade so pela unidade
    gstat = collections.Counter()
    exemplos = []
    for sig in nomes:
        for eid, prov in (prov_de.get(sig) or {}).items():
            b1 = (CAP["base"][sig].get(eid) or {}).get("sub_1a") or {}
            pont = {p[1]: p[2] for p in b1.get("pontuacoes") or []}
            for pr in prov:
                gstat["pares"] += 1
                gstat["candidato_novo" if pont.get(pr["topico"], 0) == 0 else "reforco"] += 1
                gstat["unico_so_pela_unidade" if pr["topicos_no_curso"] > 1 else "unico_no_curso"] += 1
                gstat["padrao_" + pr["padrao"]] += 1
                if len(exemplos) < 12:
                    exemplos.append({"curso": sig, "material": eid, **pr})
    R["G_proveniencia"] = {"contagens": dict(gstat), "exemplos": exemplos}
    # perdas e ganhos explicados (so explicacao)
    expl = {}
    for b in ("A", "Bp", "B"):
        itens = []
        for k in R["mudancas"][b]["ganhos"] + R["mudancas"][b]["perdas"]:
            sig, gid = k.split("|", 1)
            fa, fb = flags[b][(sig, gid)], flags["base"][(sig, gid)]
            eid = fa["eid"]
            a1 = (CAP[b][sig].get(eid) or {}).get("sub_1a") or {}
            gsp = estado[sig]["golds"][3]
            s = next(iter(gsp[gid]))
            itens.append({"curso": sig, "gold_id": gid, "tipo": "ganho" if fa["ok"] else "perda", "gold": s,
                          "base": fb["sub"], "braco": fa["sub"], "s_agiu": a1.get("s_agiu"), "ext": a1.get("ext"),
                          "aux": a1.get("aux"), "tipo_secao": a1.get("tipo"), "n_secoes": a1.get("n_secoes"),
                          "papeis": a1.get("papeis"), "dup_rotulos": a1.get("dup_rotulos_do_escolhido"),
                          "g_locais": sorted(((locais_de.get(sig) or {}).get(eid) or {}).keys()),
                          "g_liga_gold": bool(((locais_de.get(sig) or {}).get(eid) or {}).get(s)),
                          "sub_reasons_final": (CAP[b][sig].get(eid) or {}).get("final", {}).get("sub_reasons")})
        expl[b] = itens
    R["explicacao_ganhos_perdas"] = expl
    return R


def escreve_md(R):
    L = ["# W-AA — seleção por função+extensão (S) e geração local por subordinação (G), 23/09", "",
         f"Declaração `{R['sha256_declaracao'][:16]}…`; congelamento dos braços `{R['sha256_bracos'][:16]}…`; base W-Z2 `{R['base_wz2'][:16]}…`. "
         f"D9 efetivo: {R['d9_efetivo']}. Tempo {R['segundos']} s.", "",
         "## Placar (sub primária por curso; bloco e unidade no total)", "",
         "| braço | " + " | ".join(s for s in R["placar"]["base"] if s != "TOTAL") + " | TOTAL | aceita | unidade | bloco |",
         "|---|" + "---:|" * (len(R["placar"]["base"]) + 3)]
    for b, pc in R["placar"].items():
        t = pc["TOTAL"]
        L.append(f"| {b} | " + " | ".join(f"{c.get('sub_primaria', 0)}/{c.get('sub_n', 0)}" for s, c in pc.items() if s != "TOTAL") +
                 f" | {t.get('sub_primaria')}/{t.get('sub_n')} | {t.get('sub_aceita')} | {t.get('unidade')}/{t.get('unidade_n')} | {t.get('bloco')}/{t.get('bloco_n')} |")
    L += ["", f"Fatorial: {R['fatorial']}", "", "## Mudanças por braço (sub primária, vs base)", ""]
    for b, m in R["mudancas"].items():
        L += [f"### {b}", f"- saldo {m['saldo']} (+{len(m['ganhos'])}/−{len(m['perdas'])}); alteradas com gold {m['alteradas_com_gold']}, precisão {m['precisao_alteradas']}; "
              f"sem gold alteradas {R['materiais_sem_gold_alterados'][b]}; abstenções {m['abstencoes']}; direto×indireto {m['direto_x_indireto']}; "
              f"cursos que regridem {m['cursos_que_regridem']}; outros eixos idênticos {R['outros_eixos_identicos'][b]['identicos']}; aceite {R['aceite'][b]}",
              f"- ganhos: {m['ganhos']}", f"- perdas: {m['perdas']}", ""]
    L += ["## Teste de sinal (exploratório)", "", f"{R['teste_de_sinal']}", "", "## G: proveniência", "", f"{R['G_proveniencia']['contagens']}", ""]
    for e in R["G_proveniencia"]["exemplos"]:
        L.append(f"- {e['curso']} `{e['material'][:40]}`: “{e['forma']}” → {e['topico']} ({e['padrao']}, {e['doc'][:50]}; tópicos no curso {e['topicos_no_curso']}); trecho “{e['trecho'][:90]}”")
    L += ["", "## Explicação de ganhos e perdas (por ID)", ""]
    for b, itens in R["explicacao_ganhos_perdas"].items():
        for i in itens:
            L.append(f"- {b} {i['tipo']} {i['curso']} `{i['gold_id'][:40]}`: gold {i['gold'] or '∅'}, base {i['base'] or '∅'} → {i['braco'] or '∅'}; "
                     f"S agiu {i['s_agiu']} ext {i['ext']} aux {i['aux']} seções {i['n_secoes']} ({i['tipo_secao']}) papéis {i['papeis']} dup {i['dup_rotulos']}; "
                     f"G locais {i['g_locais']} liga gold {i['g_liga_gold']}")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
