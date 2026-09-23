"""W-Z (CRU-03, 22/09 noite): (1) R1/R2 reexecutadas na NOVA base; (2) rastreio dos 18 "bloco certo, gold diverge";
(3) variante de cobertura R3/R4 pre-declarada. Tudo pela cadeia real (replay_bloco_21-09 -> replay_unidade_21-09),
decisoes congeladas por sha256 ANTES de carregar qualquer gold. Sem build, rede, LLM; 0 mudanca em src/tests/builds.

NOVA BASE: regua v2 final (c1-3/wx_gold_v2_final_22-09 == docs/reports vigente) + 13 presentes (MF/IA/CG lidos de
.frzero/wv_importacao_22-09, demais nos builds-base), exatamente como wt_anatomia_unidade_v2_22-09.py (223/248/86/109).

DEFINICAO OPERACIONAL (pre-declarada) de "a unidade do bloco NAO cobre o conteudo":
  cov(u) := max, sobre os topicos t da unidade u, de _score_entry_against_taxonomy_topic(sinais, t, stem_fallback=True)
            -- a MESMA grandeza best_topic_score que auto_map_entry_unit ja calcula por unidade (file_map.py:520-540);
            sinais = collect_entry_unit_signals(entry, texto): titulo, headings, lead, corpo, tags, raw.
  Pesos do scorer (timeline/index.py:_score_entry_against_taxonomy_topic): headings 4.4, titulo 3.8, tags manuais 3.0,
  lead 2.8, corpo 1.1, raw 0.9, tags auto 0.22, x fator da frase (label 1.0, alias 0.82, slug 0.65).
  "b nao cobre" := cov(b) < theta_neg   (AUSENCIA lexical: condicao NECESSARIA, nunca suficiente)
  "g cobre"     := cov(g) >= theta_pos  (evidencia POSITIVA: um topico de g nomeia o conteudo; a suficiencia vem daqui)
  Limitacao declarada: cov=0 na unidade CERTA por vocabulario diferente ("halting problem" vs "problema da parada") so
  pode BLOQUEAR a regra (o bloco fica), nunca virar a decisao para o lado errado; o erro possivel e cov(g)>0 espuria
  numa unidade errada com cov(b)<theta_neg -- e isso que as perdas por ID medem.

REGRAS (escritas ANTES de medir; nenhum parametro ajustado ao gold; grade fechada; escolha por LOCO):
  R2  = wt_regra_unidade_22-09: no ramo `reconciliada_do_bloco`, texto gated g != b vence o bloco, sem parametro.
  R1  = R2 com unit_confidence >= tau, tau em GRID_TAU por LOCO.
  R3(theta_pos, theta_neg): no ramo `reconciliada_do_bloco` (bloco com unidade propria, texto gated g != b):
        texto vence sse cov(g) >= theta_pos E cov(b) < theta_neg. reason `texto-cobre-bloco-nao=<id>`.
  R4(theta_pos, theta_neg): R3 + o mesmo teste no ramo `herdada_do_bloco` quando o vencedor BRUTO r do scorer NAO e
        ambiguo mas ficou abaixo do gate (conf < T.UNIT_TAG) e r != b: texto vence sse cov(r) >= theta_pos E
        cov(b) < theta_neg. reason `bruto-cobre-bloco-nao=<id>`. Declarada JUNTO com R3, nao depois: 5 dos 12
        recuperaveis da anatomia v2 estao abaixo do gate e sao inalcancaveis por R1/R2/R3 por construcao.
  GRID: theta_pos in {0.55, 2.8, 3.8} (piso que o scorer ja usa para desambiguar; uma frase no lead; titulo/heading);
        theta_neg in {0.25, 1.1, 2.8} (piso que o scorer usa para somar topico; uma frase so no corpo; frase no lead).
  LOCO: para cada curso f em UNI (ordem alfabetica), escolhe a celula que maximiza acertos de unidade nos outros 5;
        empate -> celula mais conservadora (maior theta_pos, depois menor theta_neg; em R1, maior tau); celula final =
        moda dos folds (empate -> primeira na ordem dos folds). Todas as celulas sao reportadas; nada muda apos o gold.

RISCO PRE-DECLARADO: populacao que passa por `reconciliada_do_bloco` (R1/R2/R3) e por `herdada_do_bloco` com bruto
nao-ambiguo abaixo do gate (R4), por curso, com acertos atuais; distribuicao de (cov_b, cov_g) em acertos vs erros.

RASTREIO DOS 18 (base, sem regra): para cada caso, bloco (id, kind, unit_slug, auto_unit_slug, pino, confianca),
origem da unidade do bloco (pino | posicional com afinidade | posicional com afinidade 0 = preenchimento | vizinho),
afinidade token-overlap por unidade (a grandeza do DP, unit_matcher._block_tokens & _unit_tokens), censo do bloco no
denominador (gold por material, maioria, bloco == maioria?), mecanismo do material (reconciliada | herdada | vizinho),
compensacao no bloco (acertos que so existem porque o bloco sobrepos texto errado), veredito:
  origem        := unidade do bloco != maioria do gold dos materiais do bloco (a atribuicao do bloco falha);
  homogeneidade := unidade do bloco == maioria, mas o gold DESTE material difere (a suposicao "todo material do bloco
                   e da mesma unidade" falha);
  empate        := maioria empatada.

ACEITE (campanha): unidade >= 256/284, 0 perda de unidade, nenhum curso regride, bloco 223/237, sub primaria >= 86,
sub aceita >= 109. Metas por curso (usuario 22/09): CG >= 84/93, SO >= 34/37 -- reportadas, nao sao aceite.
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

T0 = time.time()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
REP = DATA / "docs/reports"
FINAL = HERE / "wx_gold_v2_final_22-09"
WV = DATA / ".frzero/wv_importacao_22-09"
OUT_JSON = HERE / "wz_bloco_cobertura_22-09.json"
OUT_MD = HERE / "wz_bloco_cobertura_22-09.md"
CONG = DATA / ".frzero/wz_congelado_22-09.json"     # decisoes congeladas (pre-gold), fora do repo
sys.path.insert(0, str(DATA))

from src.builder.routing import file_map as FM  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402
from src.builder.timeline.unit_matcher import _block_tokens, _unit_tokens  # noqa: E402

GRID_TAU = (0.50, 0.60, 0.70, 0.80, 0.90)
GRID_POS = (0.55, 2.8, 3.8)
GRID_NEG = (0.25, 1.1, 2.8)
BASE_ESPERADA = {"bloco": 223, "bloco_n": 237, "unidade": 248, "unidade_n": 284, "sub_primaria": 86, "sub_aceita": 109, "sub_n": 251}
META_TOTAL = 256
METAS_CURSO = {"CG": 84, "SO": 34}
RAZOES_DE_BLOCO = ("herdada_do_bloco=", "reconciliada_do_bloco=", "unidade_do_bloco_manual", "herdada_do_vizinho=")
RAZOES_DE_TEXTO = ("secao-vence-bloco=", "explicita-vence-bloco=", "texto-vence-vizinho=", "texto-vence-bloco=",
                   "texto-cobre-bloco-nao=", "bruto-cobre-bloco-nao=")
EIXOS = ("unidade", "sub_primaria", "sub_aceita")

CTX = {"eid": None}     # entry corrente (definido no wrapper do scorer, lido pela regra em memoria)
COV = {}                # {sig: {eid: {unidade_normalizada: cov}}} -- calculado uma vez, independe da regra
RAW = {}                # {sig: {eid: {slug, confidence, ambiguous}}}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def base_root(sig, nomes):
    return DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / nomes[sig]


def root_de(sig, nomes):
    alt = WV / nomes[sig]
    return alt if (alt / "manifest.json").exists() else base_root(sig, nomes)


# ------------------------------------------------------------------------------------------- scorer + cobertura
def fazer_wrapper(ru, sig, orig_auto):
    norm = ru._normalize_unit_slug

    def wrapper(entry, units, text, topic_index=None, **kw):
        eid = str(entry["id"])
        CTX["eid"] = eid
        match = orig_auto(entry, units, text, topic_index=topic_index, **kw)
        if eid not in COV[sig]:
            sinais = ru.collect_entry_unit_signals(entry, text)
            cov = {}
            for t in topic_index or []:
                u = norm(str(t.get("unit_slug") or ""))
                if not u:
                    continue
                s = float(ru._score_entry_against_taxonomy_topic(sinais, t, stem_fallback=True))
                if s > cov.get(u, 0.0):
                    cov[u] = s
            COV[sig][eid] = cov
        RAW[sig][eid] = {"slug": str(match.slug or ""), "confidence": float(match.confidence or 0.0),
                         "ambiguous": bool(match.ambiguous)}
        return match
    return wrapper


def fazer_regra(orig, norm, sig, kind, tau=None, pos=None, neg=None):
    """kind: R1 (tau) | R2 | R3 (pos, neg) | R4 (pos, neg)."""
    def regra(**kw):
        slug, reasons, conflict = orig(**kw)
        rs = [str(r) for r in reasons]
        gated_raw = str(kw.get("computed_unit_slug") or "")
        gated, bloco = norm(gated_raw), norm(str(kw.get("block_unit_slug") or ""))
        bid = str(kw.get("computed_block_id") or "")
        reconciliada = any(r.startswith("reconciliada_do_bloco=") for r in rs)
        herdada = any(r.startswith("herdada_do_bloco=") for r in rs)
        if kind in ("R1", "R2"):
            if not reconciliada or not gated or gated == bloco:
                return slug, reasons, conflict
            if tau is not None and float(kw.get("unit_confidence") or 0.0) < tau:
                return slug, reasons, conflict
            return gated_raw, [f"texto-vence-bloco={bid}"], {"unit": gated_raw, "block_unit": kw.get("block_unit_slug"), "block_id": bid}
        cov = COV[sig].get(CTX["eid"]) or {}
        cov_b = cov.get(bloco, 0.0)
        if reconciliada and gated and gated != bloco:
            if cov.get(gated, 0.0) >= pos and cov_b < neg:
                return gated_raw, [f"texto-cobre-bloco-nao={bid}"], {"unit": gated_raw, "block_unit": kw.get("block_unit_slug"), "block_id": bid}
            return slug, reasons, conflict
        if kind == "R4" and herdada:
            raw = RAW[sig].get(CTX["eid"]) or {}
            r = norm(raw.get("slug") or "")
            if r and r != bloco and not raw.get("ambiguous") and raw.get("confidence", 0.0) < T.UNIT_TAG:
                if cov.get(r, 0.0) >= pos and cov_b < neg:
                    return raw["slug"], [f"bruto-cobre-bloco-nao={bid}"], {"unit": raw["slug"], "block_unit": kw.get("block_unit_slug"), "block_id": bid}
        return slug, reasons, conflict
    return regra


def rodar(estado, ru, compare, variante):
    """Cadeia unidade->subunidade sobre o bloco ja decidido; variante = (kind, params) ou None (base)."""
    orig_reconcile, orig_read, orig_auto = FM.reconcile_unit_with_block, ru.read, ru.auto_unit
    norm = ru._normalize_unit_slug
    saidas = {}
    try:
        for sig, v in estado.items():
            if variante is None:
                FM.reconcile_unit_with_block = orig_reconcile
            else:
                kind, params = variante
                FM.reconcile_unit_with_block = fazer_regra(orig_reconcile, norm, sig, kind, **params)
            ru.auto_unit = fazer_wrapper(ru, sig, orig_auto)
            feed = [copy.deepcopy(e) for e in v["feed"]]

            def patched(path, _feed=feed):
                data = orig_read(path)
                if Path(path).name == "manifest.json":
                    data = {**data, "entries": _feed}
                return data

            ru.read = patched
            try:
                _, novo, raw = ru.replay(v["root"])
            finally:
                ru.read = orig_read
            saidas[sig] = {eid: {"bloco": compare.predictions(v["root"], e)[0],
                                 "unidade": str(e.get("computed_unit_slug") or ""),
                                 "sub": str(e.get("computed_subunit_slug") or ""),
                                 "reasons": [str(r) for r in e.get("unit_match_reasons") or []],
                                 "conflict": e.get("unit_block_conflict") or {},
                                 "raw": raw.get(eid)}
                           for eid, e in novo.items()}
    finally:
        FM.reconcile_unit_with_block, ru.read, ru.auto_unit = orig_reconcile, orig_read, orig_auto
    return saidas


# ------------------------------------------------------------------------------------------- avaliacao (gold)
def preparar_avaliacao(estado, compare, mede, wx):
    for sig, v in estado.items():
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig] / "manifest.json")["entries"]}
        index = compare.indexed(list(v["saved"].values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        eid_de, ponte = {}, set()
        for row in rows:
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            eid = str(hits[0]["id"]) if hits else None
            if eid is None and gid in v["saved"]:
                eid, _ = gid, ponte.add(gid)
            eid_de[gid] = eid
        v["rows"], v["eid_de"], v["ponte"] = rows, eid_de, ponte
        v["golds"] = wx.golds_de(sig, FINAL, mede.UNI)


def avaliar(estado, saidas):
    por_curso, flags = {}, {}
    for sig, v in estado.items():
        c = collections.Counter()
        gb, gu, gs, gsp = v["golds"]
        for row in v["rows"]:
            gid = row["entry_id"]
            eid = v["eid_de"].get(gid)
            dec = saidas[sig].get(eid) if eid else None
            if row["bloco"] != "":
                c["bloco_n"] += 1
                ok = bool(dec and dec["bloco"] == gb[gid])
                c["bloco"] += ok
                flags[(sig, gid, "bloco")] = ok
            if row["unidade"] != "":
                c["unidade_n"] += 1
                ok = bool(dec and dec["unidade"] in gu[gid])
                c["unidade"] += ok
                flags[(sig, gid, "unidade")] = ok
            if row["sub_primario"] != "":
                c["sub_n"] += 1
                okp = bool(dec and dec["sub"] in gsp[gid])
                oka = bool(dec and dec["sub"] in gs[gid])
                c["sub_primaria"] += okp
                c["sub_aceita"] += oka
                flags[(sig, gid, "sub_primaria")] = okp
                flags[(sig, gid, "sub_aceita")] = oka
        por_curso[sig] = dict(c)
    return por_curso, flags


def totais(por_curso):
    tot = collections.Counter()
    for c in por_curso.values():
        tot.update(c)
    return dict(tot)


def diff_ids(base_fl, fl):
    ganhos = {e: sorted((k[0], k[1]) for k, ok in base_fl.items() if k[2] == e and not ok and fl.get(k)) for e in EIXOS}
    perdas = {e: sorted((k[0], k[1]) for k, ok in base_fl.items() if k[2] == e and ok and not fl.get(k)) for e in EIXOS}
    return ganhos, perdas


def loco(res, celulas, folds, conservadora):
    out = {}
    for f in folds:
        def chave(c):
            return (sum(res[c]["por_curso"][s].get("unidade", 0) for s in folds if s != f), conservadora(c))
        melhor = max(celulas, key=chave)
        out[f] = {"celula": melhor, "unidade_nos_5_de_treino": chave(melhor)[0],
                  "unidade_no_fold": res[melhor]["por_curso"][f].get("unidade", 0),
                  "n_no_fold": res[melhor]["por_curso"][f].get("unidade_n", 0)}
    final = collections.Counter(v["celula"] for v in out.values()).most_common(1)[0][0]
    return out, final


def aceite(nome, res, base):
    tot, pc = res[nome]["total"], res[nome]["por_curso"]
    regride = [s for s in base["por_curso"] if pc[s].get("unidade", 0) < base["por_curso"][s].get("unidade", 0)]
    return {
        "unidade_maior_igual_256": tot.get("unidade", 0) >= META_TOTAL,
        "zero_perda_unidade": not res[nome]["perdas"]["unidade"],
        "nenhum_curso_regride": not regride,
        "bloco_223_237": (tot.get("bloco"), tot.get("bloco_n")) == (BASE_ESPERADA["bloco"], BASE_ESPERADA["bloco_n"]),
        "sub_primaria_maior_igual_86": tot.get("sub_primaria", 0) >= BASE_ESPERADA["sub_primaria"],
        "sub_aceita_maior_igual_109": tot.get("sub_aceita", 0) >= BASE_ESPERADA["sub_aceita"],
        "cursos_que_regridem": regride,
        "metas_por_curso": {s: {"acertos": pc[s].get("unidade", 0), "meta": m, "ok": pc[s].get("unidade", 0) >= m} for s, m in METAS_CURSO.items()},
    }


# ------------------------------------------------------------------------------------------- rastreio dos 18
def classe_do_erro(dec, bloco_ok):
    reasons = dec["reasons"] if dec else []
    de_bloco = any(str(r).startswith(RAZOES_DE_BLOCO) or str(r) in RAZOES_DE_BLOCO for r in reasons)
    de_texto = any(str(r).startswith(RAZOES_DE_TEXTO) for r in reasons)
    if dec is None:
        return "ausente"
    if not dec["unidade"]:
        return "abstencao"
    if de_bloco and not de_texto:
        return "herdada_do_bloco_errado" if not bloco_ok else "herdada_do_bloco_certo_mas_gold_diverge"
    return "texto_vence_errado"


def mecanismo(reasons):
    rs = " ".join(reasons)
    if "unidade_do_bloco_manual" in rs:
        return "bloco_manual"
    if "manual" in reasons:
        return "unidade_manual"
    for tag, nome in (("reconciliada_do_bloco=", "reconciliada"), ("herdada_do_vizinho=", "vizinho"),
                      ("herdada_do_bloco=", "herdada"), ("secao-vence-bloco=", "secao"), ("explicita-vence-bloco=", "explicita"),
                      ("texto-vence-vizinho=", "texto_vence_vizinho")):
        if tag in rs:
            return nome
    return "concorda"


def rastreio(estado, base_saidas, base_flags, ru):
    norm = ru._normalize_unit_slug
    casos, censo_blocos, compensacao, populacao = [], {}, collections.Counter(), []
    for sig, v in estado.items():
        gb, gu, gs, gsp = v["golds"]
        blocos = read(v["root"] / "course/.timeline_index.json")["blocks"]
        tax = read(v["root"] / "course/.content_taxonomy.json").get("units", []) or []
        por_id = {str(b.get("id")): b for b in blocos}
        ordem = sorted(blocos, key=lambda b: str(b.get("period_start") or ""))
        # denominador de unidade por bloco previsto (base)
        por_bloco = collections.defaultdict(list)
        for row in v["rows"]:
            if row["unidade"] == "":
                continue
            gid = row["entry_id"]
            eid = v["eid_de"].get(gid)
            dec = base_saidas[sig].get(eid) if eid else None
            if dec is None:
                continue
            hit = base_flags.get((sig, gid, "unidade"), False)
            mec = mecanismo(dec["reasons"])
            raw = dec.get("raw") or {}
            raw_ok = bool(raw.get("slug")) and raw.get("slug") in gu[gid]
            cov = COV[sig].get(eid) or {}
            cov_b = cov.get(norm(dec["unidade"] if mec in ("reconciliada", "herdada", "vizinho") else ""), 0.0)
            cov_gold = max([cov.get(norm(g), 0.0) for g in gu[gid]] or [0.0])
            cov_raw = cov.get(norm(raw.get("slug") or ""), 0.0)
            rec = {"gold_id": gid, "entry_id": eid, "gold": sorted(gu[gid]), "pred": dec["unidade"], "hit": hit,
                   "mecanismo": mec, "raw_slug": raw.get("slug"), "raw_conf": raw.get("confidence"),
                   "raw_ambiguo": raw.get("ambiguous"), "raw_acertaria": raw_ok,
                   "compensado": bool(hit and mec == "reconciliada" and not raw_ok),
                   "cov_bloco": round(cov_b, 3), "cov_gold": round(cov_gold, 3), "cov_raw": round(cov_raw, 3)}
            por_bloco[dec["bloco"]].append(rec)
            compensacao[(sig, mec, "acerto" if hit else "erro")] += 1
            if mec in ("reconciliada", "herdada"):
                populacao.append({"curso": sig, **rec})
        for bid, mats in por_bloco.items():
            b = por_id.get(bid) or {}
            votos = collections.Counter()
            for m in mats:
                for g in m["gold"]:
                    votos[g] += 1
            top = votos.most_common()
            maioria = [u for u, n in top if n == top[0][1]] if top else []
            unit = str(b.get("unit_slug") or "")
            censo_blocos[(sig, bid)] = {
                "curso": sig, "bloco": bid, "kind": b.get("kind"), "unit_slug": unit,
                "auto_unit_slug": b.get("auto_unit_slug"), "pino": b.get("block_manual_unit_slug"),
                "unit_confidence": b.get("unit_confidence"), "period_start": b.get("period_start"),
                "rotulo": " / ".join(str(s.get("label", "")) for s in (b.get("sessions") or []) if isinstance(s, dict))[:200],
                "afinidade_dp": {str(u.get("slug")): len(_block_tokens(b) & _unit_tokens(u)) for u in tax} if b else {},
                "n_materiais_denominador": len(mats), "votos_gold": dict(votos), "maioria": maioria,
                "bloco_igual_maioria": unit in maioria if unit else None,
                "acertos": sum(m["hit"] for m in mats), "compensados": sum(m["compensado"] for m in mats),
                "por_mecanismo": {f"{m}|{h}": n for (m, h), n in collections.Counter(
                    (m["mecanismo"], "acerto" if m["hit"] else "erro") for m in mats).items()},
                "materiais": mats,
            }
        for row in v["rows"]:
            if row["unidade"] == "":
                continue
            gid = row["entry_id"]
            eid = v["eid_de"].get(gid)
            dec = base_saidas[sig].get(eid) if eid else None
            if base_flags.get((sig, gid, "unidade")):
                continue
            bloco_ok = bool(dec and dec["bloco"] == gb.get(gid))
            if classe_do_erro(dec, bloco_ok) != "herdada_do_bloco_certo_mas_gold_diverge":
                continue
            b = por_id.get(dec["bloco"]) or {}
            censo = censo_blocos[(sig, dec["bloco"])]
            mat = next(m for m in censo["materiais"] if m["gold_id"] == gid)
            aff = censo["afinidade_dp"]
            unit = censo["unit_slug"]
            viz = next((r.split("=", 1)[1] for r in dec["reasons"] if r.startswith("herdada_do_vizinho=")), "")
            if censo["pino"]:
                origem = "pino_manual"
            elif viz:
                bv = por_id.get(viz) or {}
                origem = f"vizinho:{viz} (bloco {b.get('kind')} sem unidade propria; vizinho {bv.get('kind')} unit={bv.get('unit_slug')})"
            elif not unit:
                origem = "bloco_sem_unidade"
            elif not any(aff.values()):
                origem = "posicional_preenchimento_afinidade_0"
            else:
                argmax = max(aff, key=lambda u: (aff[u], u == unit))
                origem = "posicional_afinidade_argmax" if argmax == unit else f"posicional_contra_argmax(argmax={argmax})"
            if censo["bloco_igual_maioria"] and len(censo["maioria"]) == 1:
                veredito = "homogeneidade"
            elif censo["bloco_igual_maioria"] is False:
                veredito = "origem"
            else:
                veredito = "empate"
            # posicao do bloco entre os vizinhos de conteudo (para ler fronteira/desvio)
            idx = next((i for i, x in enumerate(ordem) if str(x.get("id")) == dec["bloco"]), None)
            vizinhos = []
            if idx is not None:
                for j in (idx - 1, idx + 1):
                    if 0 <= j < len(ordem):
                        vizinhos.append(f"{ordem[j].get('id')}:{ordem[j].get('kind')}:{ordem[j].get('unit_slug') or '-'}")
            casos.append({"curso": sig, "gold_id": gid, "entry_id": eid, "gold": sorted(gu[gid]), "pred": dec["unidade"],
                          "bloco": dec["bloco"], "bloco_kind": b.get("kind"), "bloco_unit": unit,
                          "bloco_auto_unit": censo["auto_unit_slug"], "bloco_pino": censo["pino"],
                          "bloco_conf": censo["unit_confidence"], "bloco_rotulo": censo["rotulo"],
                          "origem_da_unidade_do_bloco": origem, "afinidade_dp": aff,
                          "afinidade_unit_vs_gold": {unit: aff.get(unit), **{g: aff.get(g) for g in gu[gid]}},
                          "vizinhos": vizinhos, "mecanismo_do_material": mat["mecanismo"],
                          "raw": {k: mat[k] for k in ("raw_slug", "raw_conf", "raw_ambiguo", "raw_acertaria")},
                          "cov": {"bloco": mat["cov_bloco"], "gold": mat["cov_gold"], "raw": mat["cov_raw"]},
                          "censo_bloco": {k: censo[k] for k in ("n_materiais_denominador", "votos_gold", "maioria",
                                                                 "bloco_igual_maioria", "acertos", "compensados", "por_mecanismo")},
                          "regua_ambigua": len(gu[gid]) > 1, "veredito": veredito})
    return casos, censo_blocos, compensacao, populacao


# ------------------------------------------------------------------------------------------- main
def main():
    assert not OUT_JSON.exists(), "preservar evidencia existente"
    compare = load("wz_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    wx = load("wz_wx", HERE / "wx_regua_corrigida_22-09.py")
    rb = load("wz_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wz_ru", HERE / "replay_unidade_21-09.py")
    nomes, uni = mede.NOMES, mede.UNI
    folds = sorted(uni)

    declaracao = {"doc": __doc__, "grid_tau": GRID_TAU, "grid_pos": GRID_POS, "grid_neg": GRID_NEG, "unit_tag": T.UNIT_TAG,
                  "base_esperada": BASE_ESPERADA, "meta_total": META_TOTAL, "metas_curso": METAS_CURSO, "folds": folds}
    sha_decl = sha(declaracao)
    print("DECLARACAO", sha_decl, flush=True)

    raizes = {sig: root_de(sig, nomes) for sig in nomes}
    for sig in ("MF", "IA", "CG"):
        assert raizes[sig].parent == WV, f"{sig}: copia do W-V ausente"
    estado = {}
    for sig in nomes:
        COV[sig], RAW[sig] = {}, {}
        saved, bloco_novo, _, _ = rb.replay(raizes[sig])
        estado[sig] = {"root": raizes[sig], "saved": saved, "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
        print("bloco", sig, round(time.time() - T0), "s", flush=True)

    variantes = {"base": None, "R2": ("R2", {})}
    for tau in GRID_TAU:
        variantes[f"R1_tau{tau:.2f}"] = ("R1", {"tau": tau})
    for pos in GRID_POS:
        for neg in GRID_NEG:
            variantes[f"R3_pos{pos:.2f}_neg{neg:.2f}"] = ("R3", {"pos": pos, "neg": neg})
    for pos in GRID_POS:
        for neg in GRID_NEG:
            variantes[f"R4_pos{pos:.2f}_neg{neg:.2f}"] = ("R4", {"pos": pos, "neg": neg})
    saidas, tempos = {}, {}
    if "--reavaliar" in sys.argv:
        # Reavaliacao a partir do congelamento persistido (mesma declaracao; decisoes intocadas). Custa segundos.
        cong = read(CONG)
        assert cong["sha256_declaracao"] == sha_decl, "declaracao mudou: congelamento invalido"
        saidas, tempos = cong["saidas"], cong["tempos"]
        for sig in nomes:
            COV[sig], RAW[sig] = cong["cov"][sig], cong["raw"][sig]
        sha_cong, sha_cov = sha(saidas), sha(COV)
        assert (sha_cong, sha_cov) == (cong["sha256_congelamento"], cong["sha256_cobertura"]), "congelamento corrompido"
        print("REAVALIACAO a partir de", CONG.name, flush=True)
    else:
        for nome, var in variantes.items():
            t1 = time.time()
            saidas[nome] = rodar(estado, ru, compare, var)
            tempos[nome] = round(time.time() - t1, 1)
            print("rodado", nome, tempos[nome], "s", round(time.time() - T0), "s total", flush=True)
        sha_cong = sha(saidas)
        sha_cov = sha(COV)
        # Persistido ANTES do gold (evidencia do congelamento; reavaliacao com --reavaliar). Fora do repo (.frzero/).
        CONG.write_text(json.dumps({"sha256_declaracao": sha_decl, "sha256_congelamento": sha_cong, "sha256_cobertura": sha_cov,
                                    "saidas": saidas, "cov": COV, "raw": RAW, "tempos": tempos},
                                   ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    print("CONGELAMENTO", sha_cong, "COV", sha_cov, flush=True)

    # ------------------------------------------------------------------ gold entra aqui
    preparar_avaliacao(estado, compare, mede, wx)
    arquivos_gold = {}
    for sig in folds:
        for nome in (f"ground_truth_{sig}.csv", f"material_gt_{sig}.csv", f"subunit_gt_{sig}.csv"):
            p = FINAL / nome if (FINAL / nome).exists() else REP / nome
            if p.exists():
                arquivos_gold[str(p.relative_to(DATA))] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    res = {}
    for nome in saidas:
        pc, fl = avaliar(estado, saidas[nome])
        res[nome] = {"por_curso": pc, "total": totais(pc), "flags": fl}
    base = res["base"]
    base_ok = all(base["total"].get(k) == v for k, v in BASE_ESPERADA.items())
    print("BASE", {k: base["total"].get(k) for k in BASE_ESPERADA}, "== anatomia v2:", base_ok, flush=True)
    for nome in saidas:
        ganhos, perdas = diff_ids(base["flags"], res[nome]["flags"])
        res[nome]["ganhos"], res[nome]["perdas"] = ganhos, perdas
        res[nome]["ids_unidade_tocados"] = sorted({(sig, eid) for sig in nomes for eid, d in saidas[nome][sig].items()
                                                    if d["unidade"] != saidas["base"][sig][eid]["unidade"]})
        res[nome]["aceite"] = aceite(nome, res, base)
        print(nome, {k: res[nome]["total"].get(k) for k in ("unidade", "sub_primaria", "sub_aceita")},
              "ganhos", len(ganhos["unidade"]), "perdas", len(perdas["unidade"]), flush=True)

    taus = [f"R1_tau{t:.2f}" for t in GRID_TAU]
    loco_r1, r1_final = loco(res, taus, folds, lambda c: float(c.split("tau")[1]))
    def cons(c):
        p, n = c.split("_pos")[1].split("_neg")
        return (float(p), -float(n))
    r3 = [n for n in variantes if n.startswith("R3_")]
    r4 = [n for n in variantes if n.startswith("R4_")]
    loco_r3, r3_final = loco(res, r3, folds, cons)
    loco_r4, r4_final = loco(res, r4, folds, cons)

    casos, censo, compensacao, populacao = rastreio(estado, saidas["base"], base["flags"], ru)
    ids_18 = sorted((c["curso"], c["gold_id"]) for c in casos)
    anat = read(HERE / "wt_anatomia_unidade_v2_22-09.json")["resultado"]["v2_final"]["erros"]
    ids_anat = sorted((e["curso"], e["gold_id"]) for e in anat if e["classe"] == "herdada_do_bloco_certo_mas_gold_diverge")
    recuperaveis = sorted((e["curso"], e["gold_id"]) for e in anat if e["bruto_acertaria"])
    print("RASTREIO", len(casos), "casos; iguais a anatomia v2:", ids_18 == ids_anat, flush=True)

    # risco: populacao das clausulas e separabilidade por (cov_b, cov_g)
    risco = {"reconciliada": collections.Counter(), "herdada_bruto_abaixo_gate": collections.Counter()}
    for p in populacao:
        if p["mecanismo"] == "reconciliada":
            risco["reconciliada"][p["curso"]] += 1
            risco["reconciliada"]["total"] += 1
            risco["reconciliada"]["total_acerto"] += p["hit"]
        elif p["mecanismo"] == "herdada" and p["raw_slug"] and not p["raw_ambiguo"] and (p["raw_conf"] or 0) < T.UNIT_TAG:
            risco["herdada_bruto_abaixo_gate"][p["curso"]] += 1
            risco["herdada_bruto_abaixo_gate"]["total"] += 1
            risco["herdada_bruto_abaixo_gate"]["total_acerto"] += p["hit"]
    separabilidade = {}
    for pos in GRID_POS:
        for neg in GRID_NEG:
            k = f"pos{pos:.2f}_neg{neg:.2f}"
            fire_hit = fire_err = 0
            for p in populacao:
                if p["mecanismo"] != "reconciliada":
                    continue
                if p["cov_raw"] >= pos and p["cov_bloco"] < neg:
                    fire_hit += p["hit"]
                    fire_err += not p["hit"]
            separabilidade[k] = {"dispara_em_acertos(perda_potencial)": fire_hit, "dispara_em_erros(ganho_potencial)": fire_err}

    relatorio = {
        "escopo": __doc__, "sha256_declaracao": sha_decl, "sha256_congelamento_decisoes": sha_cong, "sha256_cobertura": sha_cov,
        "raizes": {s: str(p.relative_to(DATA)) for s, p in raizes.items()}, "arquivos_gold_sha16": arquivos_gold,
        "pontes_por_id": {s: sorted(v["ponte"]) for s, v in estado.items()},
        "base_igual_anatomia_v2": base_ok, "tempos_s": tempos,
        "resultados": {n: {k: v for k, v in r.items() if k != "flags"} for n, r in res.items()},
        "loco": {"R1": {"por_fold": loco_r1, "final": r1_final}, "R3": {"por_fold": loco_r3, "final": r3_final},
                 "R4": {"por_fold": loco_r4, "final": r4_final}},
        "risco_clausulas": {k: dict(v) for k, v in risco.items()}, "separabilidade_reconciliada": separabilidade,
        "rastreio_18": casos, "rastreio_igual_anatomia_v2": ids_18 == ids_anat,
        "recuperaveis_anatomia_v2": recuperaveis,
        "veredito_18": dict(collections.Counter(c["veredito"] for c in casos)),
        "veredito_18_por_curso": {s: dict(collections.Counter(c["veredito"] for c in casos if c["curso"] == s)) for s in folds},
        "origem_18": dict(collections.Counter(c["origem_da_unidade_do_bloco"].split("(")[0].split(":")[0] for c in casos)),
        "mecanismo_18": dict(collections.Counter(c["mecanismo_do_material"] for c in casos)),
        "compensacao_por_mecanismo": {f"{s}|{m}|{h}": n for (s, m, h), n in sorted(compensacao.items())},
        "compensacao_total": {f"{m}|{h}": sum(n for (s, mm, hh), n in compensacao.items() if mm == m and hh == h)
                              for m in ("concorda", "herdada", "vizinho", "reconciliada", "secao", "explicita", "texto_vence_vizinho", "unidade_manual", "bloco_manual") for h in ("acerto", "erro")},
        "censo_blocos_dos_18": [censo[k] for k in sorted({(c["curso"], c["bloco"]) for c in casos})],
        "populacao_clausulas": populacao,
        "segundos": round(time.time() - T0, 1),
    }
    OUT_JSON.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    escreve_md(relatorio, res, casos, censo, folds, nomes)
    print("OK", OUT_JSON.name, hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()[:16], relatorio["segundos"], "s", flush=True)


def escreve_md(r, res, casos, censo, folds, nomes):
    b = res["base"]["total"]
    L = ["# W-Z — R1/R2 na nova base, rastreio dos 18 e variante de cobertura R3/R4 (22/09, noite)", "",
         f"Declaração `{r['sha256_declaracao'][:16]}…`; congelamento das decisões (25 variantes) `{r['sha256_congelamento_decisoes'][:16]}…`; "
         f"cobertura `{r['sha256_cobertura'][:16]}…`. Raízes: MF/IA/CG em `.frzero/wv_importacao_22-09/`, demais builds-base. "
         f"Régua v2 final (hashes no JSON). Base reproduzida = anatomia v2: **{'sim' if r['base_igual_anatomia_v2'] else 'NÃO'}** "
         f"({b.get('bloco')}/{b.get('bloco_n')}, {b.get('unidade')}/{b.get('unidade_n')}, {b.get('sub_primaria')}/{b.get('sub_aceita')} de {b.get('sub_n')}). Tempo {r['segundos']} s.", ""]
    L += ["## 1. Placar por variante (unidade; subunidade primária/aceita; ganhos/perdas de unidade por ID vs base)", "",
          "| variante | unidade | sub prim | sub aceita | ganhos | perdas | cursos que regridem | " + " | ".join(folds) + " |",
          "|---|---:|---:|---:|---:|---:|---|" + "---:|" * len(folds)]
    for n in res:
        t, a = res[n]["total"], res[n]["aceite"]
        L.append(f"| {n} | {t.get('unidade')} | {t.get('sub_primaria')} | {t.get('sub_aceita')} | {len(res[n]['ganhos']['unidade'])} | "
                 f"{len(res[n]['perdas']['unidade'])} | {','.join(a['cursos_que_regridem']) or '—'} | "
                 + " | ".join(str(res[n]["por_curso"][s].get("unidade", 0)) for s in folds) + " |")
    L += ["", f"Metas: total ≥ {META_TOTAL}; CG ≥ {METAS_CURSO['CG']}/93; SO ≥ {METAS_CURSO['SO']}/37. Bloco é igual em todas as variantes (fase de bloco não muda).", ""]
    L += ["## 2. LOCO", ""]
    for k, v in r["loco"].items():
        L.append(f"- **{k}** → célula final `{v['final']}`; por fold: " + "; ".join(
            f"{f}: {d['celula']} (treino {d['unidade_nos_5_de_treino']}, fold {d['unidade_no_fold']}/{d['n_no_fold']})" for f, d in v["por_fold"].items()))
    L += ["", "## 3. Aceite e IDs das células escolhidas por LOCO (e R2)", ""]
    for n in ("R2", r["loco"]["R1"]["final"], r["loco"]["R3"]["final"], r["loco"]["R4"]["final"]):
        a = res[n]["aceite"]
        L.append(f"### {n}")
        L.append("- aceite: " + ", ".join(f"{k}={v}" for k, v in a.items() if k not in ("cursos_que_regridem", "metas_por_curso")) +
                 f"; metas por curso: {a['metas_por_curso']}")
        for e in EIXOS:
            L.append(f"- {e}: ganhos {res[n]['ganhos'][e]} | perdas {res[n]['perdas'][e]}")
        L.append("")
    L += ["## 4. Risco das cláusulas e separabilidade por (cov_bloco, cov_texto) na população `reconciliada_do_bloco`", "",
          f"- população: {r['risco_clausulas']}",
          "- por célula (dispara em acertos = perda potencial; dispara em erros = ganho potencial): " +
          "; ".join(f"{k}: −{v['dispara_em_acertos(perda_potencial)']}/+{v['dispara_em_erros(ganho_potencial)']}" for k, v in r["separabilidade_reconciliada"].items()), ""]
    L += ["## 5. Rastreio dos 18 (bloco certo, gold diverge)", "",
          f"Iguais à anatomia v2: {r['rastreio_igual_anatomia_v2']}. Veredito: {r['veredito_18']} (por curso {r['veredito_18_por_curso']}). "
          f"Origem da unidade do bloco: {r['origem_18']}. Mecanismo do material: {r['mecanismo_18']}.", "",
          "| curso | id | gold → previsto | bloco (kind, unit, conf) | origem da unidade do bloco | afinidade DP unit vs gold | censo do bloco (n, votos gold, maioria, compensados) | mecanismo / bruto | cov b/gold/raw | veredito |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(casos, key=lambda c: (c["curso"], c["bloco"], c["gold_id"])):
        cb = c["censo_bloco"]
        L.append(f"| {c['curso']} | `{c['gold_id']}` | {'|'.join(c['gold'])} → {c['pred']} | {c['bloco']} ({c['bloco_kind']}, {c['bloco_unit'] or '∅'}, {c['bloco_conf']}) | "
                 f"{c['origem_da_unidade_do_bloco']} | {c['afinidade_unit_vs_gold']} | n={cb['n_materiais_denominador']} {cb['votos_gold']} maioria={cb['maioria']} "
                 f"bloco==maioria={cb['bloco_igual_maioria']} compensados={cb['compensados']} | {c['mecanismo_do_material']} / {c['raw']['raw_slug']} "
                 f"conf={round(c['raw']['raw_conf'] or 0, 2)}{' amb' if c['raw']['raw_ambiguo'] else ''}{' bruto=gold' if c['raw']['raw_acertaria'] else ''} | "
                 f"{c['cov']['bloco']}/{c['cov']['gold']}/{c['cov']['raw']} | {c['veredito']}{' (régua ambígua)' if c['regua_ambigua'] else ''} |")
    L += ["", "### Blocos dos 18 — rótulo do cronograma e afinidade do DP", ""]
    for k in sorted({(c["curso"], c["bloco"]) for c in casos}):
        cb = censo[k]
        L.append(f"- {k[0]} {k[1]} [{cb['kind']}] unit={cb['unit_slug'] or '∅'} auto={cb['auto_unit_slug']} pino={cb['pino']} conf={cb['unit_confidence']} "
                 f"início={cb['period_start']}; rótulo: “{cb['rotulo'][:120]}”; afinidade={cb['afinidade_dp']}; materiais={cb['n_materiais_denominador']} "
                 f"votos={cb['votos_gold']} acertos={cb['acertos']} compensados={cb['compensados']} mecanismos={cb['por_mecanismo']}")
    L += ["", "## 6. Compensação posterior (toda a população de unidade, base)", "",
          f"- por mecanismo × acerto/erro: {r['compensacao_total']}",
          "- 'reconciliada|acerto' = acertos que existem porque o bloco sobrepôs o texto gated discordante (compensação); "
          "'herdada|acerto' = texto abstido, bloco acertou; 'concorda|acerto' = texto e bloco iguais.", ""]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
