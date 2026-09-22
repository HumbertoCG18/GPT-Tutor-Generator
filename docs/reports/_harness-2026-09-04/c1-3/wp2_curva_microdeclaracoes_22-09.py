"""W-P2' (CRU-02): curva de microdeclaracoes do professor por prefixo de perguntas.

Mede quantas perguntas do tipo "a expressao X pertence a qual subunidade?" sao precisas para
elevar a subunidade primaria a partir da base 84/251, em TRES ordens de perguntas pre-declaradas.
A resposta do professor e SIMULADA pelo gold; a fase e REAL (replay 1a passada + 2a passada
`propagar_vocabulario_por_headings`, via `replay_subunidade_21-09.replay`).

Read-only: nao toca src/, nao faz build, rede nem LLM. O patch e SO em memoria (taxonomia
copiada com `copy.deepcopy` e aliases acrescentados; nada gravado em `.frzero/`).

DEFINICOES PRE-DECLARADAS (congeladas por sha256 ANTES de carregar o gold)

(O1) ORDEM NAIVE   = `perguntas[curso]` do W-P1, como esta (controle).
(O2) ORDEM CAP-25  = mesma greedy do W-P1 (cobertura marginal; desempate por `peso_forte`,
     depois alfabetico), recomputada sobre as expressoes NOVAS do W-P1 excluindo (a) as que
     alcancam > 25% dos materiais presentes do curso (df por curso) e (b) fragmentos de
     hifenizacao de PDF.
(O3) ORDEM CAP-50  = idem, cap 50%.
     Os caps 25% e 50% sao fixos A PRIORI (subunidade e mais fina que 1/4 do curso; 50% e a
     variante frouxa). Os dois sao reportados; nenhum e escolhido pelo gold.
     Hifenizacao: a juncao nao foi implementada (ambigua sem re-extrair o texto cru). Regra
     de exclusao aplicada: um n-grama e fragmento se a juncao de duas formas adjacentes
     (stem6) e chave de 1 token do MESMO curso (ex.: `exerc icio` -> `exerci`); excluem-se o
     n-grama e as chaves de 1 token iguais ao pedaco-SUFIXO detectado (ex.: `icio`). O pedaco
     prefixo permanece. Contagens em `hifenizacao` do JSON.
(P)  PREFIXOS = 5, 10, 20, 40 perguntas por curso, cumulativos (menos se a ordem for menor).
(R)  RESPOSTA SIMULADA a (curso, expressao, materiais alcancados): interseccao das primarias
     do gold (`gsp`) dos materiais alcancados que tem gold. Interseccao vazia -> "depende"
     (nada declarado). Interseccao nao vazia mas sem nenhum slug na taxonomia do curso, ou
     nenhum material com gold -> "nao_associar". Caso contrario -> "declara": TODAS as
     `formas` da expressao viram alias do topico (interseccao com >1 slug: o menor
     lexicografico; contado em `declaracoes_intersecao_multipla`). O professor NAO corrige
     unidade nem bloco.
(E)  ESTADO POR PREFIXO = taxonomia base + aliases das perguntas DECLARADAS do prefixo (sem
     revisao retroativa); replay integral (1a + 2a passada) por prefixo; custo = perguntas
     examinadas (inclui "depende"/"nao_associar") + tempo de replay.
(A)  AVALIACAO: primaria x/251 (ausentes e abstencoes contam erro), aceita x/251, ganhos e
     perdas contra a base 84, por curso e total; abstencao que vira decisao: certa/errada.

GOLD: usado SO (a) para simular a resposta do professor a cada pergunta examinada e (b) para
avaliar. As tres ordens e a selecao de expressoes saem do W-P1 e de (O2)/(O3), calculadas
antes, sobre campos PRE-GOLD do JSON do W-P1 (whitelist explicita em `PRE_GOLD_*`).

DESEMPENHO: `compare.read`, `load_code_curation` e `_entry_markdown_text_for_file_map` sao
memoizados em memoria (leem arquivos que nao mudam durante a corrida); o replay continua
deepcopiando as entries. Estados com o MESMO conjunto de declaracoes reusam o replay.
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

CAPS = {"CAP25": 0.25, "CAP50": 0.50}          # fixos a priori, nao escolhidos pelo gold
PREFIXOS = (5, 10, 20, 40)
STEM = 6
PRE_GOLD_MAT = ("curso", "gold_id", "entry_id", "presente", "unidade_vigente",
                "subunidade_predita", "expressoes", "expressoes_novas")
PRE_GOLD_EXPR = ("curso", "chave", "formas", "materiais", "ja_conhecida", "peso_forte")
PRE_GOLD_PERG = ("ordem", "expressao", "formas", "materiais_alcancados", "cobertura_marginal")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RP = load("wp2_replay", HERE / "replay_subunidade_21-09.py")
diag, compare, mede = RP.diag, RP.compare, RP.mede


def memoizar():
    """Cache de leitura (arquivos imutaveis durante a corrida). O replay deepcopia as entries."""
    _read, _md, _cur = compare.read, diag._entry_markdown_text_for_file_map, RP.load_code_curation
    cr, cm, cc = {}, {}, {}

    def read(path):
        k = str(path)
        if k not in cr:
            cr[k] = _read(path)
        return cr[k]

    def md(root, entry):
        k = (str(root), str(entry.get("id") or ""), str(entry.get("source_path") or ""))
        if k not in cm:
            cm[k] = _md(root, entry)
        return cm[k]

    def cur(root):
        k = str(root)
        if k not in cc:
            cc[k] = _cur(root)
        return cc[k]

    compare.read = read
    diag._entry_markdown_text_for_file_map = md
    RP.load_code_curation = cur


memoizar()


# --------------------------------------------------------------------------- fase pre-gold
def carregar_wp1():
    """So os campos PRE-GOLD do W-P1 (o JSON tambem tem colunas derivadas do gold)."""
    dados = json.loads((HERE / "wp1_inventario_matriz_22-09.json").read_text(encoding="utf-8"))
    materiais = {(m["curso"], m["gold_id"]): {k: m[k] for k in PRE_GOLD_MAT} for m in dados["materiais"]}
    expressoes = collections.defaultdict(dict)
    for e in dados["expressoes"]:
        expressoes[e["curso"]][e["chave"]] = {k: e[k] for k in PRE_GOLD_EXPR}
    perguntas = {sig: [{k: q[k] for k in PRE_GOLD_PERG} for q in lst] for sig, lst in dados["perguntas"].items()}
    return materiais, expressoes, perguntas, dados["congelamento_sha256"], dados["materiais"], dados["cobertura_nao_certos"]


def hifenizacao(expr):
    """Fragmentos de hifenizacao de PDF (ver O2). Devolve (n-gramas quebrados, sufixos)."""
    um_token = {k for k in expr if " " not in k}
    quebrados, sufixos = set(), set()
    for chave, e in expr.items():
        toks = chave.split()
        if len(toks) < 2:
            continue
        for forma in e["formas"]:
            ft = forma.split()
            if len(ft) != len(toks):
                continue
            for i in range(len(ft) - 1):
                junta = (ft[i] + ft[i + 1])[:STEM]
                if junta in um_token and junta != toks[i]:
                    quebrados.add(chave)
                    sufixos.add(toks[i + 1])
    return quebrados, sufixos


def greedy(expr, candidatas, universo):
    """Mesma greedy do W-P1: cobertura marginal, desempate por peso_forte e depois alfabetico."""
    cand = {k: set(expr[k]["materiais"]) for k in candidatas}
    cobertos, ordem = set(), []
    while cand:
        melhor, best = None, None
        for k, mats in cand.items():
            novos = mats - cobertos
            if not novos:
                continue
            score = (len(novos), expr[k]["peso_forte"], [-ord(c) for c in k])
            if best is None or score > best:
                melhor, best = k, score
        if melhor is None:
            break
        mats = cand.pop(melhor)
        novos = sorted(mats - cobertos)
        cobertos |= set(novos)
        ordem.append({"ordem": len(ordem) + 1, "expressao": melhor, "formas": list(expr[melhor]["formas"]),
                      "materiais_alcancados": sorted(mats), "materiais_novos": novos,
                      "cobertura_marginal": len(novos),
                      "cobertura_acumulada_pct": round(100.0 * len(cobertos) / max(1, len(universo)), 1)})
    return ordem


def montar_ordens(materiais, expressoes, perguntas_naive):
    ordens = {"NAIVE": {sig: [dict(q, materiais_novos=[]) for q in lst] for sig, lst in perguntas_naive.items()}}
    diagnostico = {}
    for nome, cap in CAPS.items():
        ordens[nome] = {}
    for sig in mede.NOMES:
        expr = expressoes[sig]
        universo = {g for (s, g), m in materiais.items() if s == sig and m["presente"]}
        quebrados, sufixos = hifenizacao(expr)
        novas = [k for k, e in expr.items() if not e["ja_conhecida"]]
        frag = [k for k in novas if k in quebrados or (set(k.split()) & sufixos)]
        d = {"expressoes_novas": len(novas), "materiais_presentes": len(universo),
             "fragmentos_hifenizacao_excluidos": len(frag),
             "fragmentos_exemplos": sorted(frag)[:10], "sufixos_detectados": sorted(sufixos)}
        for nome, cap in CAPS.items():
            limite = cap * len(universo)
            acima = [k for k in novas if len(expr[k]["materiais"]) > limite]
            cand = [k for k in novas if k not in set(frag) and k not in set(acima)]
            ordens[nome][sig] = greedy(expr, cand, universo)
            d[f"{nome}_limite_materiais"] = round(limite, 2)
            d[f"{nome}_excluidas_por_df"] = len(acima)
            d[f"{nome}_excluidas_por_df_top"] = sorted(acima, key=lambda k: -len(expr[k]["materiais"]))[:8]
            d[f"{nome}_perguntas"] = len(ordens[nome][sig])
        diagnostico[sig] = d
    return ordens, diagnostico


def congelar(ordens):
    payload = {"caps": CAPS, "prefixos": list(PREFIXOS), "stem": STEM,
               "ordens": {nome: {sig: [[q["ordem"], q["expressao"], sorted(q["materiais_alcancados"])]
                                       for q in lst] for sig, lst in sorted(por_curso.items())}
                          for nome, por_curso in sorted(ordens.items())}}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------ fase gold
def contexto_curso(sig):
    """root, mapa gold_id -> entry_id novo (None se ausente), gold primario e aceito, taxonomia crua."""
    name = mede.NOMES[sig]
    root = ROOT / diag.NEW.get(sig, diag.REF) / name
    ref_root = ROOT / diag.REF / name
    ref_by_id = {e["id"]: e for e in compare.read(ref_root / "manifest.json")["entries"]}
    by_source = compare.indexed(compare.read(root / "manifest.json")["entries"])
    mapping = {e["entry_id"]: e["new_id"] for e in compare.read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
    with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
        rows = [r["entry_id"] for r in csv.DictReader(stream) if r["sub_primario"] != ""]
    alvo = {}
    for gid in rows:
        old = ref_by_id.get(mapping.get(gid) or "")
        entry = (by_source.get(compare.source(old)) or [None])[0] if old else None
        alvo[gid] = str(entry.get("id")) if entry is not None else None
    gb, gu, gs, gsp = mede.golds(sig)
    tax = compare.read(root / "course/.content_taxonomy.json")
    slugs = {str(t.get("slug")) for u in tax.get("units", []) for t in u.get("topics", []) or []}
    return {"root": root, "ids": rows, "entry_de": alvo, "gsp": gsp, "gs": gs, "slugs": slugs}


def responder(q, ctx):
    """(R): resposta simulada do professor. Nao usa nada alem do gold primario."""
    sets = [set(ctx["gsp"].get(g) or ()) for g in q["materiais_alcancados"] if ctx["gsp"].get(g)]
    if not sets:
        return {"resposta": "nao_associar", "topico": None, "motivo": "sem gold"}
    inter = set.intersection(*sets)
    if not inter:
        return {"resposta": "depende", "topico": None, "motivo": "primarias divergem"}
    na_tax = sorted(s for s in inter if s in ctx["slugs"])
    if not na_tax:
        return {"resposta": "nao_associar", "topico": None, "motivo": "fora da taxonomia"}
    return {"resposta": "declara", "topico": na_tax[0], "multipla": len(na_tax) > 1}


def taxonomia_com(ctx, declaracoes):
    """Copia da taxonomia do curso com os aliases declarados (nada e gravado em disco)."""
    tax = copy.deepcopy(compare.read(ctx["root"] / "course/.content_taxonomy.json"))
    por_slug = {str(t.get("slug")): t for u in tax.get("units", []) for t in u.get("topics", []) or []}
    for slug, formas in declaracoes:
        topic = por_slug.get(slug)
        if topic is None:
            continue
        aliases = list(topic.get("aliases") or [])
        for f in formas:
            if f not in aliases:
                aliases.append(f)
        topic["aliases"] = aliases
    return tax


def rodar(ctx, tax):
    """Replay integral (1a + 2a passada) com a taxonomia injetada. Devolve pred por gold_id."""
    original = RP.load_internal_content_taxonomy
    RP.load_internal_content_taxonomy = lambda root: tax
    try:
        t0 = time.time()
        entries, processadas = RP.replay(ctx["root"], "base")
    finally:
        RP.load_internal_content_taxonomy = original
    pred = {gid: (str(entries[eid].get("computed_subunit_slug") or "") if eid else None)
            for gid, eid in ctx["entry_de"].items()}
    return pred, entries, processadas, round(time.time() - t0, 2)


def avaliar(pred, base, ctx):
    c = collections.Counter()
    perdas, novas_certas, novas_erradas = [], [], []
    for gid in ctx["ids"]:
        gsp, gs = set(ctx["gsp"].get(gid) or ()), set(ctx["gs"].get(gid) or ())
        p, b = pred[gid], base[gid]
        c["n"] += 1
        if p is None:
            c["ausente"] += 1
            continue
        c["primaria"] += p in gsp
        c["aceita"] += p in gs
        if p in gsp and b not in gsp:
            c["ganho"] += 1
        if b in gsp and p not in gsp:
            c["perda"] += 1
            perdas.append({"gold_id": gid, "base": b, "novo": p, "gold": sorted(gsp)})
        if not b and p:
            c["abst_decisao"] += 1
            if p in gsp:
                c["abst_certa"] += 1
                novas_certas.append(gid)
            else:
                c["abst_errada"] += 1
                novas_erradas.append(gid)
    return dict(c), perdas, novas_certas, novas_erradas


def main():
    materiais, expressoes, perguntas_naive, sha_wp1, mat_full, cob_wp1 = carregar_wp1()
    ordens, diag_ordens = montar_ordens(materiais, expressoes, perguntas_naive)
    sha_congelamento = congelar(ordens)
    print("CONGELAMENTO_W_P2", sha_congelamento, flush=True)
    print("PERGUNTAS_POR_ORDEM", {n: {s: len(l) for s, l in p.items()} for n, p in ordens.items()}, flush=True)

    # ---- gold entra aqui -----------------------------------------------------------------
    ctxs = {sig: contexto_curso(sig) for sig in mede.NOMES}
    alvos = {sig: sorted(m["gold_id"] for m in mat_full
                         if m["curso"] == sig and not m["certo_primario"] and m["expressoes_novas"])
             for sig in mede.NOMES}

    base_pred, base_stats, fidelidade = {}, {}, collections.Counter()
    for sig, ctx in ctxs.items():
        tax = taxonomia_com(ctx, [])
        pred, entries, processadas, dt = rodar(ctx, tax)
        gravado = {str(e.get("id")): e for e in compare.read(ctx["root"] / "manifest.json")["entries"]}
        for eid in processadas:
            fidelidade["processadas"] += 1
            fidelidade["fieis"] += (str(entries[eid].get("computed_subunit_slug") or "")
                                    == str(gravado[eid].get("computed_subunit_slug") or ""))
        base_pred[sig] = pred
        base_stats[sig], _, _, _ = avaliar(pred, pred, ctx)
        base_stats[sig]["tempo_s"] = dt
    base_total = {k: sum(v.get(k, 0) for v in base_stats.values()) for k in ("n", "ausente", "primaria", "aceita")}
    print("BASE", base_total, "fidelidade", dict(fidelidade), flush=True)
    assert fidelidade["fieis"] == fidelidade["processadas"], "replay base diverge do manifest gravado"
    assert base_total["primaria"] == 84 and base_total["n"] == 251, f"base nao reproduz 84/251: {base_total}"

    # ---- perguntas: resposta simulada e declaracoes acumuladas ---------------------------
    respostas = {nome: {} for nome in ordens}
    for nome, por_curso in ordens.items():
        for sig, lst in por_curso.items():
            ctx = ctxs[sig]
            saida = []
            for q in lst[:max(PREFIXOS)]:
                r = responder(q, ctx)
                saida.append({"ordem": q["ordem"], "expressao": q["expressao"], "formas": q["formas"],
                              "materiais_alcancados": len(q["materiais_alcancados"]),
                              "cobertura_marginal": q["cobertura_marginal"], **r})
            respostas[nome][sig] = saida

    # ---- estados por prefixo -------------------------------------------------------------
    resultados, detalhe_perdas = {}, []
    for nome in ordens:
        resultados[nome] = {}
        for p in PREFIXOS:
            cursos, cache = {}, {}
            for sig, ctx in ctxs.items():
                qs = respostas[nome][sig][:p]
                decl = tuple(sorted({(q["topico"], tuple(sorted(q["formas"]))) for q in qs if q["resposta"] == "declara"}))
                chave = (sig, decl)
                if chave not in cache:
                    pred, _, _, dt = rodar(ctx, taxonomia_com(ctx, [(s, list(f)) for s, f in decl]))
                    cache[chave] = (pred, dt)
                pred, dt = cache[chave]
                stats, perdas, certas, erradas = avaliar(pred, base_pred[sig], ctx)
                corrigidos = sum(1 for g in alvos[sig] if pred[g] is not None and pred[g] in set(ctx["gsp"].get(g) or ()))
                stats.update({
                    "examinadas": len(qs), "declaradas": sum(1 for q in qs if q["resposta"] == "declara"),
                    "depende": sum(1 for q in qs if q["resposta"] == "depende"),
                    "nao_associar": sum(1 for q in qs if q["resposta"] == "nao_associar"),
                    "declaracoes_distintas": len(decl), "tempo_s": dt,
                    "base_primaria": base_stats[sig]["primaria"], "alvos": len(alvos[sig]),
                    "alvos_corrigidos": corrigidos, "abst_certas_ids": certas, "abst_erradas_ids": erradas})
                cursos[sig] = stats
                for d in perdas:
                    detalhe_perdas.append({"ordem_nome": nome, "prefixo": p, "curso": sig, **d})
            tot = {k: sum(v.get(k, 0) for v in cursos.values())
                   for k in ("n", "ausente", "primaria", "aceita", "ganho", "perda", "abst_decisao",
                             "abst_certa", "abst_errada", "examinadas", "declaradas", "depende",
                             "nao_associar", "alvos", "alvos_corrigidos")}
            tot["tempo_s"] = round(sum(v["tempo_s"] for v in cursos.values()), 2)
            tot["cursos_que_regridem"] = sorted(s for s, v in cursos.items() if v.get("perda", 0) > 0)
            resultados[nome][p] = {"cursos": cursos, "total": tot}
            print(nome, p, json.dumps(tot, ensure_ascii=False), flush=True)
            gravar(locals())   # grava parcial cedo e a cada estado

    print("FIM", flush=True)
    return resultados


ESTADO = {}


def gravar(scope=None):
    """Grava o JSON (sobrescreve; sem `assert not exists`, para permitir reexecucao)."""
    if scope:
        ESTADO.update({k: scope[k] for k in ("resultados", "detalhe_perdas", "respostas", "ordens",
                                             "diag_ordens", "sha_congelamento", "base_stats", "base_total",
                                             "fidelidade", "alvos", "sha_wp1", "cob_wp1") if k in scope})
    if "resultados" not in ESTADO:
        return None
    r = {
        "escopo": __doc__,
        "estado": {"branch": "feat/motor-atribuicao", "head": "b726d4c", "src": "intocado"},
        "congelamento_sha256": ESTADO["sha_congelamento"],
        "congelamento_wp1_sha256": ESTADO["sha_wp1"],
        "caps": CAPS, "prefixos": list(PREFIXOS),
        "base": {"total": ESTADO["base_total"], "por_curso": ESTADO["base_stats"],
                 "fidelidade_manifest": dict(ESTADO["fidelidade"])},
        "alvos_por_curso": {s: {"n": len(v), "ids": v} for s, v in ESTADO["alvos"].items()},
        "diagnostico_ordens": ESTADO["diag_ordens"],
        "perguntas_por_ordem": {n: {s: len(l) for s, l in p.items()} for n, p in ESTADO["ordens"].items()},
        "resultados": ESTADO["resultados"],
        "perdas": ESTADO["detalhe_perdas"],
        "respostas": ESTADO["respostas"],
        "ordens": {n: {s: [{k: q[k] for k in ("ordem", "expressao", "formas", "cobertura_marginal",
                                              "materiais_alcancados")}
                           for q in l[:max(PREFIXOS)]] for s, l in p.items()}
                   for n, p in ESTADO["ordens"].items()},
        "cobertura_wp1": ESTADO["cob_wp1"],
        "marcos_alvos": ESTADO.get("marcos"),
    }
    out = HERE / "wp2_curva_microdeclaracoes_22-09.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(out.read_bytes()).hexdigest()


def escrever_md(sha):
    r = ESTADO
    L = ["# W-P2' — curva de microdeclaracoes do professor por prefixo (22/09)", "",
         f"JSON: `wp2_curva_microdeclaracoes_22-09.json` sha256 `{sha}`  ",
         f"Congelamento (3 ordens, pre-gold) sha256 `{r['sha_congelamento']}`  ",
         f"Congelamento herdado do W-P1 sha256 `{r['sha_wp1']}`  ",
         "Estado: branch `feat/motor-atribuicao`, HEAD `b726d4c`, `src/` intocado.", "",
         "## 1. Base (0 declaracoes)", "",
         f"- primaria {r['base_total']['primaria']}/{r['base_total']['n']}, aceita {r['base_total']['aceita']}/"
         f"{r['base_total']['n']}, ausentes {r['base_total']['ausente']}",
         f"- fidelidade do replay contra o manifest gravado: {r['fidelidade']['fieis']}/{r['fidelidade']['processadas']}",
         "", "| curso | n | primaria | aceita | ausente | alvos |", "|---|---|---|---|---|---|"]
    for sig, v in r["base_stats"].items():
        L.append(f"| {sig} | {v['n']} | {v['primaria']} | {v['aceita']} | {v.get('ausente', 0)} | {len(r['alvos'][sig])} |")
    L += ["", "## 2. Totais por ordem x prefixo", "",
          "| ordem | prefixo | examinadas | declaradas | depende | nao assoc. | primaria/251 | aceita/251 | ganhos | perdas | abst->dec (certas/erradas) | alvos corrigidos | tempo (s) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for nome, por_p in r["resultados"].items():
        for p, v in por_p.items():
            t = v["total"]
            L.append(f"| {nome} | {p} | {t['examinadas']} | {t['declaradas']} | {t['depende']} | {t['nao_associar']} | "
                     f"{t['primaria']} | {t['aceita']} | {t['ganho']} | {t['perda']} | "
                     f"{t['abst_decisao']} ({t['abst_certa']}/{t['abst_errada']}) | {t['alvos_corrigidos']}/{t['alvos']} | "
                     f"{t['tempo_s']} |")
    L += ["", "## 3. Por curso (ordem x prefixo)", ""]
    for nome, por_p in r["resultados"].items():
        L += [f"### {nome}", "",
              "| prefixo | curso | exam. | decl. | dep. | n/a | primaria | aceita | ganhos | perdas | abst->dec | alvos corr. | tempo |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for p, v in por_p.items():
            for sig, c in v["cursos"].items():
                L.append(f"| {p} | {sig} | {c['examinadas']} | {c['declaradas']} | {c['depende']} | {c['nao_associar']} | "
                         f"{c.get('primaria', 0)} | {c.get('aceita', 0)} | {c.get('ganho', 0)} | {c.get('perda', 0)} | "
                         f"{c.get('abst_decisao', 0)} ({c.get('abst_certa', 0)}/{c.get('abst_errada', 0)}) | "
                         f"{c['alvos_corrigidos']}/{c['alvos']} | {c['tempo_s']} |")
        L.append("")
    if r.get("marcos"):
        L += ["## 3b. Marcos 50/80/100% dos alvos (perguntas na ordem; `declarados` ignora depende/nao associar)", "",
              "| ordem | modo | curso | alvos | alcance final | ate 50% | ate 80% | ate 100% |",
              "|---|---|---|---|---|---|---|---|"]
        for nome, m in r["marcos"].items():
            for sig, v in m.items():
                if sig == "TOTAL":
                    continue
                for modo in ("alcancados", "declarados"):
                    d = v[modo]
                    L.append(f"| {nome} | {modo} | {sig} | {d['alvos']} | {d['alcance_final']} | {d['p50']} | "
                             f"{d['p80']} | {d['p100']} |")
        L += ["", "Totais (soma das perguntas por curso):", ""]
        for nome, m in r["marcos"].items():
            for modo in ("alcancados", "declarados"):
                t = m["TOTAL"][modo]
                L.append(f"- **{nome} / {modo}**: alvos {t['alvos']}, alcance final {t['alcance_final']}, "
                         f"perguntas ate 50% = {t['perguntas_p50']}, ate 80% = {t['perguntas_p80']}"
                         + (f" (cursos sem 80%: {', '.join(t['cursos_sem_p80'])})" if t["cursos_sem_p80"] else ""))
        L.append("")
    L += ["## 4. Selecao das ordens CAP (pre-gold)", "",
          "| curso | mat. presentes | expr. novas | frag. hifen. excl. | CAP25 limite | CAP25 excl. df | CAP25 perguntas | CAP50 limite | CAP50 excl. df | CAP50 perguntas |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for sig, d in r["diag_ordens"].items():
        L.append(f"| {sig} | {d['materiais_presentes']} | {d['expressoes_novas']} | {d['fragmentos_hifenizacao_excluidos']} | "
                 f"{d['CAP25_limite_materiais']} | {d['CAP25_excluidas_por_df']} | {d['CAP25_perguntas']} | "
                 f"{d['CAP50_limite_materiais']} | {d['CAP50_excluidas_por_df']} | {d['CAP50_perguntas']} |")
    L += ["", "Expressoes de maior df excluidas pelo cap 25% (topo por curso):", ""]
    for sig, d in r["diag_ordens"].items():
        L.append(f"- **{sig}**: " + ", ".join(f"`{k}`" for k in d["CAP25_excluidas_por_df_top"]))
    L += ["", "## 5. Perdas (declaracao derruba material hoje certo)", ""]
    if not r["detalhe_perdas"]:
        L.append("- nenhuma perda em nenhum estado medido.")
    else:
        L += ["| ordem | prefixo | curso | gold_id | base | novo | gold primario |", "|---|---|---|---|---|---|---|"]
        for d in r["detalhe_perdas"]:
            L.append(f"| {d['ordem_nome']} | {d['prefixo']} | {d['curso']} | {d['gold_id']} | `{d['base']}` | "
                     f"`{d['novo']}` | {', '.join(d['gold'])} |")
    L += ["", "## 6. Perguntas examinadas e resposta simulada (ate 40 por ordem/curso)", ""]
    for nome, por_curso in r["respostas"].items():
        L += [f"### {nome}", ""]
        for sig, lst in por_curso.items():
            if not lst:
                continue
            L += [f"**{sig}**", "", "| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |",
                  "|---|---|---|---|---|---|"]
            for q in lst[:40]:
                L.append(f"| {q['ordem']} | {', '.join(q['formas'])[:60]} | {q['materiais_alcancados']} | "
                         f"{q['cobertura_marginal']} | {q['resposta']} | {q['topico'] or ''} |")
            L.append("")
    (HERE / "wp2_curva_microdeclaracoes_22-09.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def marcos_pos_hoc():
    """Marcos 50/80/100% dos ALVOS por ordem, sem replay: reconstroi as ordens (mesmo sha),
    le as respostas ja medidas do JSON e conta as perguntas ate alcancar cada fracao dos alvos.
    `alcancados` conta toda pergunta examinada; `declarados` so as que o professor declarou."""
    alvo_json = HERE / "wp2_curva_microdeclaracoes_22-09.json"
    r = json.loads(alvo_json.read_text(encoding="utf-8"))
    materiais, expressoes, perguntas_naive, sha_wp1, mat_full, cob_wp1 = carregar_wp1()
    ordens, diag_ordens = montar_ordens(materiais, expressoes, perguntas_naive)
    assert congelar(ordens) == r["congelamento_sha256"], "ordens nao reproduzem o congelamento"
    alvos = {s: set(v["ids"]) for s, v in r["alvos_por_curso"].items()}
    marcos = {}
    for nome, por_curso in ordens.items():
        m = {}
        for sig, lst in por_curso.items():
            resp = {q["ordem"]: q["resposta"] for q in r["respostas"][nome][sig]}
            saida = {}
            for modo in ("alcancados", "declarados"):
                vistos, marco = set(), {}
                for q in lst[:max(PREFIXOS)]:
                    if modo == "declarados" and resp.get(q["ordem"]) != "declara":
                        continue
                    vistos |= set(q["materiais_alcancados"]) & alvos[sig]
                    for pct in (50, 80, 100):
                        if pct not in marco and alvos[sig] and len(vistos) >= pct / 100.0 * len(alvos[sig]):
                            marco[pct] = q["ordem"]
                saida[modo] = {"alvos": len(alvos[sig]), "alcance_final": len(vistos),
                               "p50": marco.get(50), "p80": marco.get(80), "p100": marco.get(100)}
            m[sig] = saida
        m["TOTAL"] = {modo: {"alvos": sum(v[modo]["alvos"] for k, v in m.items() if k != "TOTAL"),
                             "alcance_final": sum(v[modo]["alcance_final"] for k, v in m.items() if k != "TOTAL"),
                             "perguntas_p50": sum(v[modo]["p50"] or 0 for k, v in m.items() if k != "TOTAL"),
                             "perguntas_p80": sum(v[modo]["p80"] or 0 for k, v in m.items() if k != "TOTAL"),
                             "cursos_sem_p80": sorted(k for k, v in m.items() if k != "TOTAL" and v[modo]["p80"] is None)}
                      for modo in ("alcancados", "declarados")}
        marcos[nome] = m
    ESTADO.update({"resultados": r["resultados"], "detalhe_perdas": r["perdas"], "respostas": r["respostas"],
                   "ordens": ordens, "diag_ordens": r["diagnostico_ordens"],
                   "sha_congelamento": r["congelamento_sha256"], "base_stats": r["base"]["por_curso"],
                   "base_total": r["base"]["total"], "fidelidade": r["base"]["fidelidade_manifest"],
                   "alvos": {s: v["ids"] for s, v in r["alvos_por_curso"].items()},
                   "sha_wp1": r["congelamento_wp1_sha256"], "cob_wp1": r["cobertura_wp1"], "marcos": marcos})
    sha = gravar()
    print("MARCOS", json.dumps({n: m["TOTAL"] for n, m in marcos.items()}, ensure_ascii=False))
    print("JSON_SHA256", sha)
    escrever_md(sha)
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
