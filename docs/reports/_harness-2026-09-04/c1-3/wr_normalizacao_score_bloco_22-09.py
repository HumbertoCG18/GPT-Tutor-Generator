"""W-R (CRU-04 residual): normalizacao do `_score` do desempate, patch SO EM MEMORIA.

Variantes PRE-DECLARADAS (so o divisor muda; `raw` e o gate D4 intactos):
  V0 raw / sqrt(len(sig))                 (atual, controle)
  V1 raw                                  (sem divisor)
  V2 raw / sqrt(sum_{t in sig} (sig[t]*log(1+m/df[t]))**2)   (cosseno vs assinatura)
  V3 raw / log(2 + len(sig))              (penalidade suave)
  V4 raw / sqrt(|mat & sig|), 0 se nao casa nada

Patch: atributo de modulo `disambiguator._score`. `_lexical_decision` (:230) chama
`_score` pelo nome GLOBAL do proprio modulo, entao trocar o atributo basta
(conferido: unico call-site em src/ e disambiguator.py:230). Restaurado no finally.

Cadeia completa: replay_bloco_21-09.replay (fase real, TEMPORAL_KEYS removidas,
voter=None) -> id/banda FINAIS (inclui o fallback de card de anchor_engine.py:283-291)
-> replay_unidade_21-09.replay alimentado com as entries decididas. Decisoes de TODAS
as variantes congeladas por sha256 ANTES de carregar o gold. Sem build, rede, LLM,
escrita em src/, commit ou git add.
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.path.insert(0, str(DATA))

from src.builder.routing.motor import anchor_engine as AE
from src.builder.routing.motor import disambiguator as D

CAMPOS = ("temporal_block_id", "temporal_block_method", "temporal_block_band",
          "temporal_block_flag", "temporal_block_provider")
VARIANTES = ("V0", "V1", "V2", "V3", "V4")
KS = (1, 3, 5, 10)
PESO_EXTRA = D.W_TOPIC  # peso dos termos nao casantes do contrafactual (so V2 depende dele)
T0 = time.time()
OUT = HERE / "wr_normalizacao_score_bloco_22-09.json"


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------- as 5 formulas (mesma assinatura de src/) ----------------
def _raw(mat, sig, m, df):
    return sum(sig[t] * math.log(1.0 + m / df[t]) for t in sorted(mat & set(sig)))


def mk(nome):
    def score(mat, sig, m, df):
        if not sig:
            return 0.0
        raw = _raw(mat, sig, m, df)
        if nome == "V0":
            return raw / math.sqrt(len(sig))
        if nome == "V1":
            return raw
        if nome == "V2":
            den = math.sqrt(sum((sig[t] * math.log(1.0 + m / df[t])) ** 2 for t in sorted(sig)))
            return raw / den if den else 0.0
        if nome == "V3":
            return raw / math.log(2 + len(sig))
        if nome == "V4":
            k = len(mat & set(sig))
            return raw / math.sqrt(k) if k else 0.0
        raise AssertionError(nome)
    score.__name__ = f"_score_{nome}"
    return score


SCORE = {v: mk(v) for v in VARIANTES}


class Patch:
    """Troca disambiguator._score; restaura no __exit__."""

    def __init__(self, fn):
        self.fn = fn

    def __enter__(self):
        self.orig = D._score
        D._score = self.fn
        return self

    def __exit__(self, *exc):
        D._score = self.orig


def estado_janela(entry, win, ctx, markdown, short_vocab):
    """mat/sigs/df/m reais da janela (mesma construcao de _lexical_decision)."""
    blocks = [ctx.block_by_ref(r) for r in win]
    blocks = [b for b in blocks if b is not None]
    if len(blocks) < 2:
        return None
    mat = D.entry_tokens(entry, markdown or "", short_vocab)
    sigs = [D._block_signature(b, ctx, short_vocab) for b in blocks]
    m = len(blocks)
    df = {}
    for sig in sigs:
        for t in sig:
            df[t] = df.get(t, 0) + 1
    refs = [str(b.get("id") or b.get("block_uuid") or "") for b in blocks]
    return {"refs": refs, "mat": sorted(mat), "sigs": sigs, "m": m, "df": df}


def argmax(scores):
    return max(range(len(scores)), key=lambda i: scores[i])


def contrafactual(est, nome):
    """K termos NAO casantes acrescentados a UM candidato mudam o argmax?"""
    fn, mat = SCORE[nome], set(est["mat"])
    base = [fn(mat, s, est["m"], est["df"]) for s in est["sigs"]]
    top0 = argmax(base)
    flips = {}
    for k in KS:
        alvos = []
        for j in range(len(est["sigs"])):
            df2 = dict(est["df"])
            sigs2 = list(est["sigs"])
            extra = {f"__nc{i}": PESO_EXTRA for i in range(k)}
            for t in extra:
                df2[t] = 1
            sigs2[j] = {**est["sigs"][j], **extra}
            novo = [fn(mat, s, est["m"], df2) for s in sigs2]
            if argmax(novo) != top0:
                alvos.append({"inflado": est["refs"][j], "nova_escolha": est["refs"][argmax(novo)]})
        if alvos:
            flips[str(k)] = alvos
    return {"muda_por_comprimento": bool(flips), "flips": flips}


def snap(entries):
    return {eid: {c: e.get(c) for c in CAMPOS} for eid, e in entries.items()}


def main():
    assert not OUT.exists(), "preservar evidencia existente"
    assert D._score.__module__.endswith("disambiguator"), "patch sobre o original"
    rb = load("rb_wr", HERE / "replay_bloco_21-09.py")
    ru = load("ru_wr", HERE / "replay_unidade_21-09.py")
    compare = load("cmp_wr", HERE / "compara_herancas_15-09.py")
    mede = compare.mede   # golds() so DEPOIS do congelamento

    roots = {sig: DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"}
                          else ".frzero/pacote_fontes_15-09") / name
             for sig, name in mede.NOMES.items()}

    # `temporal_block_id` e UUID; gold e `block_ref` sao o id `bloco-NN`.
    # Mesmo mapa de compara_herancas.predictions, montado 1x por curso.
    lookup = {}
    for sig, root in roots.items():
        tl = root / "course/.timeline_index.json"
        bl = read(tl).get("blocks", []) if tl.exists() else []
        lookup[sig] = {**{str(b["block_uuid"]): b["id"] for b in bl},
                       **{str(b["id"]): b["id"] for b in bl}}

    def bnn(sig, ent):
        """id de bloco do entry no espaco do gold (bloco-NN), como predictions()."""
        if ent is None:
            return None
        v = str(ent.get("manual_timeline_block_id") or ent.get("temporal_block_id") or "")
        return lookup[sig].get(v, v)

    # ---------- 1) captura do estado das janelas (1x, na formula vigente) ----------
    capturas = {}
    saved_por_curso, dec_base, base_entries = {}, {}, {}
    for sig, root in roots.items():
        cap = []
        orig = AE.disambiguate

        def observador(entry, window, ctx, markdown="", provider="", _o=orig, _cap=cap):
            dec = _o(entry, window, ctx, markdown, provider=provider)
            if dec.method in ("disamb", "disamb-curto"):
                vocab = D.course_short_vocab(ctx) if dec.method == "disamb-curto" else frozenset()
                _cap.append({"id": str(entry.get("id") or ""), "method": dec.method,
                             "window": list(window or []), "ref": dec.block_ref,
                             "band": dec.band, "flag": dec.flag,
                             "est": estado_janela(entry, list(window or []), ctx, markdown, vocab)})
            return dec

        AE.disambiguate = observador
        try:
            saved, _base, decs, _ = rb.replay(root)
        finally:
            AE.disambiguate = orig
        saved_por_curso[sig] = saved
        base_entries[sig] = _base
        dec_base[sig] = decs
        capturas[sig] = cap
    log("captura das janelas ok")

    # ---------- 2) replay de BLOCO por variante ----------
    res = {}
    for v in VARIANTES:
        res[v] = {}
        with Patch(SCORE[v]):
            for sig, root in roots.items():
                saved, entries, decs, _ = rb.replay(root)
                res[v][sig] = {"entries": entries, "dec": decs}
        log("bloco replay", v, "ok")
    assert D._score.__module__.endswith("disambiguator"), "_score restaurado"

    # V0 tem de ser identico a base (mesma formula)
    v0_igual = all(snap(res["V0"][s]["entries"]) == snap(base_entries[s]) for s in roots)
    id_muda = {v: {sig: [i for i in res["V0"][sig]["entries"]
                         if res["V0"][sig]["entries"][i].get("temporal_block_id")
                         != res[v][sig]["entries"][i].get("temporal_block_id")]
                   for sig in roots} for v in VARIANTES}

    # ---------- 3) CONGELAMENTO antes do gold ----------
    congelado = {v: {sig: snap(res[v][sig]["entries"]) for sig in roots} for v in VARIANTES}
    freeze = hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True)
                            .encode("utf-8")).hexdigest()
    log("FREEZE", freeze)

    # ---------- 4) avaliacao de BLOCO (gold a partir daqui) ----------
    tot = {v: collections.Counter() for v in VARIANTES}
    cursos = {v: {} for v in VARIANTES}
    acertos = {v: {} for v in VARIANTES}
    gold_por_id, eid_por_curso = {}, {}
    for sig, root in roots.items():
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig]
                                             / "manifest.json")["entries"]}
        index = compare.indexed(list(saved_por_curso[sig].values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gb = mede.golds(sig)[0]
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        eid_por_curso[sig] = {}
        c = {v: collections.Counter() for v in VARIANTES}
        for row in rows:
            if row["bloco"] == "":
                continue
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            assert len(hits) <= 1, (sig, gid, "origem nao unica")
            eid = str(hits[0]["id"]) if hits else None
            if eid:
                gold_por_id[(sig, eid)] = gb[gid]
                eid_por_curso[sig][eid] = gb[gid]
            for v in VARIANTES:
                c[v]["bloco_n"] += 1
                ent = res[v][sig]["entries"].get(eid) if eid else None
                if ent is None:
                    c[v]["bloco_ausente"] += 1
                    continue
                ok = compare.predictions(root, ent)[0] == gb[gid]
                c[v]["bloco"] += ok
                acertos[v][(sig, eid)] = ok
        for v in VARIANTES:
            cursos[v][sig] = dict(c[v])
            tot[v].update(c[v])
    log("bloco:", {v: f'{tot[v]["bloco"]}/{tot[v]["bloco_n"]}' for v in VARIANTES})
    assert (tot["V0"]["bloco"], tot["V0"]["bloco_n"]) == (214, 237), "base 214/237"

    ganhos, perdas, detalhe_ids = {}, {}, {}
    for v in VARIANTES:
        ganhos[v] = sorted(f"{s}:{e}" for (s, e) in acertos["V0"]
                           if acertos["V0"][(s, e)] is False and acertos[v].get((s, e)) is True)
        perdas[v] = sorted(f"{s}:{e}" for (s, e) in acertos["V0"]
                           if acertos["V0"][(s, e)] is True and acertos[v].get((s, e)) is False)
        det = []
        for sig in roots:
            for eid in id_muda[v][sig]:
                det.append({"curso": sig, "id": eid,
                            "antes": bnn(sig, res["V0"][sig]["entries"][eid]),
                            "depois": bnn(sig, res[v][sig]["entries"][eid]),
                            "gold": gold_por_id.get((sig, eid)),
                            "com_gold": (sig, eid) in gold_por_id,
                            "banda_antes": res["V0"][sig]["entries"][eid].get("temporal_block_band"),
                            "banda_depois": res[v][sig]["entries"][eid].get("temporal_block_band"),
                            "flag_antes": res["V0"][sig]["entries"][eid].get("temporal_block_flag"),
                            "flag_depois": res[v][sig]["entries"][eid].get("temporal_block_flag"),
                            "metodo_antes": res["V0"][sig]["entries"][eid].get("temporal_block_method"),
                            "metodo_depois": res[v][sig]["entries"][eid].get("temporal_block_method")})
        detalhe_ids[v] = det

    # ---------- 5) banda/flag entre os que NAO mudam de bloco ----------
    banda = {}
    for v in VARIANTES:
        c = collections.Counter()
        exemplos = []
        for sig in roots:
            mud = set(id_muda[v][sig])
            for eid, e0 in res["V0"][sig]["entries"].items():
                if eid in mud:
                    continue
                e1 = res[v][sig]["entries"][eid]
                f0, f1 = bool(e0.get("temporal_block_flag")), bool(e1.get("temporal_block_flag"))
                b0, b1 = e0.get("temporal_block_band"), e1.get("temporal_block_band")
                if f0 == f1 and b0 == b1:
                    continue
                g = gold_por_id.get((sig, eid))
                certa = None if g is None else (bnn(sig, e1) == g)
                if f0 and not f1:
                    c["ficou_confiante"] += 1
                    c["ficou_confiante_certa" if certa else
                      ("ficou_confiante_errada" if certa is False else "ficou_confiante_sem_gold")] += 1
                elif f1 and not f0:
                    c["ficou_flagada"] += 1
                    c["ficou_flagada_certa" if certa else
                      ("ficou_flagada_errada" if certa is False else "ficou_flagada_sem_gold")] += 1
                else:
                    c["so_banda"] += 1
                c["id_vazio_depois"] += not str(e1.get("temporal_block_id") or "")
                exemplos.append({"curso": sig, "id": eid, "banda": [b0, b1], "flag": [f0, f1],
                                 "gold": g, "id_final_certo": certa})
        banda[v] = {"contagem": dict(c), "entradas": exemplos}

    # ---------- 6) inventario das janelas + contrafactual por variante ----------
    inventario, janelas = {}, []
    for sig, cap in capturas.items():
        fin = dec_base[sig]
        porid = {}
        for it in cap:
            d = fin.get(it["id"])
            if (d and d.get("method") == it["method"] and list(d.get("window") or []) == it["window"]
                    and d.get("block_ref") == it["ref"]):
                porid[it["id"]] = it
        c = collections.Counter()
        for it in porid.values():
            if it["est"] is None:
                c["janela_degradada"] += 1
                continue
            c["disamb_ge2"] += 1
            est = it["est"]
            g = gold_por_id.get((sig, it["id"]))
            ok = None if g is None else (it["ref"] == g)
            c["certas" if ok else ("erradas" if ok is False else "sem_gold")] += 1
            cf = {v: contrafactual(est, v) for v in VARIANTES}
            for v in VARIANTES:
                if cf[v]["muda_por_comprimento"]:
                    c[f"cf_muda_{v}"] += 1
            janelas.append({"curso": sig, "id": it["id"], "method": it["method"],
                            "janela": est["refs"], "escolha_atual": it["ref"], "gold": g,
                            "certa_hoje": ok, "tam_sig": [len(s) for s in est["sigs"]],
                            "contrafactual": {v: cf[v]["muda_por_comprimento"] for v in VARIANTES},
                            "contrafactual_flips": {v: cf[v]["flips"] for v in VARIANTES
                                                    if cf[v]["flips"]},
                            "id_final_por_variante": {
                                v: bnn(sig, res[v][sig]["entries"].get(it["id"]))
                                for v in VARIANTES}})
        inventario[sig] = dict(c)

    assert all(not j["id_final_por_variante"]["V0"]
               or str(j["id_final_por_variante"]["V0"]).startswith("bloco-")
               for j in janelas), "id final tem de estar no espaco do gold (bloco-NN), nao UUID"
    erros_desempate = [j for j in janelas if j["certa_hoje"] is False and j["gold"] in j["janela"]]
    corrige = {v: {"corrige": [], "permanece": [], "vira_outro_erro": []} for v in VARIANTES}
    for j in erros_desempate:
        for v in VARIANTES:
            fim = j["id_final_por_variante"][v]
            alvo = corrige[v]["corrige"] if fim == j["gold"] else (
                corrige[v]["permanece"] if fim == j["escolha_atual"] else corrige[v]["vira_outro_erro"])
            alvo.append({"curso": j["curso"], "id": j["id"], "gold": j["gold"], "final": fim})

    parcial = {"head": "b726d4c", "freeze_sha256_decisoes": freeze,
               "v0_identico_a_base": v0_igual,
               "placar_bloco": {v: f'{tot[v]["bloco"]}/{tot[v]["bloco_n"]}' for v in VARIANTES},
               "ganhos_bloco": ganhos, "perdas_bloco": perdas, "ids_que_mudam": detalhe_ids,
               "banda_flag_sem_mudar_bloco": {v: banda[v]["contagem"] for v in VARIANTES},
               "inventario": inventario, "erros_de_desempate": erros_desempate,
               "correcao_dos_erros_de_desempate": corrige,
               "status": "PARCIAL - falta a fase de unidade"}
    OUT.write_text(json.dumps(parcial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log("PARCIAL gravado")
    print("PLACAR_BLOCO", json.dumps(parcial["placar_bloco"], ensure_ascii=False))
    print("GANHOS", json.dumps(ganhos, ensure_ascii=False))
    print("PERDAS", json.dumps(perdas, ensure_ascii=False))

    # ---------- 7) unidade encadeada ----------
    uni = {v: collections.Counter() for v in VARIANTES}
    uni_cursos = {v: {} for v in VARIANTES}
    uni_mud = {v: [] for v in VARIANTES}
    orig_read = ru.read
    upos = {}

    def roda_unidade(root, entries):
        feed = [copy.deepcopy(entries[i]) for i in entries]

        def patched(path, _feed=feed, _o=orig_read):
            data = _o(path)
            if Path(path).name == "manifest.json":
                data = {**data, "entries": _feed}
            return data

        ru.read = patched
        try:
            _, pos, _ = ru.replay(root)
        finally:
            ru.read = orig_read
        return pos

    for sig, root in roots.items():
        upos[("V0", sig)] = roda_unidade(root, res["V0"][sig]["entries"])
        for v in VARIANTES[1:]:
            upos[(v, sig)] = (roda_unidade(root, res[v][sig]["entries"])
                              if id_muda[v][sig] else upos[("V0", sig)])
        log("unidade", sig, "ok")

    for sig, root in roots.items():
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig]
                                             / "manifest.json")["entries"]}
        index = compare.indexed(list(saved_por_curso[sig].values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gu = mede.golds(sig)[1]
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        c = {v: collections.Counter() for v in VARIANTES}
        for row in rows:
            if row["unidade"] == "":
                continue
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            eid = str(hits[0]["id"]) if hits else None
            for v in VARIANTES:
                c[v]["unidade_n"] += 1
                ent = upos[(v, sig)].get(eid) if eid else None
                c[v]["unidade"] += bool(ent) and str(ent.get("computed_unit_slug") or "") in gu[gid]
        for v in VARIANTES:
            uni_cursos[v][sig] = dict(c[v])
            uni[v].update(c[v])
            for eid in id_muda[v][sig]:
                ub = str(upos[("V0", sig)][eid].get("computed_unit_slug") or "")
                uv = str(upos[(v, sig)][eid].get("computed_unit_slug") or "")
                uni_mud[v].append({"curso": sig, "id": eid, "unidade_V0": ub, "unidade_variante": uv,
                                   "mudou_unidade": ub != uv})
    log("unidade:", {v: f'{uni[v]["unidade"]}/{uni[v]["unidade_n"]}' for v in VARIANTES})
    assert (uni["V0"]["unidade"], uni["V0"]["unidade_n"]) == (246, 284), "base 246/284"

    # ---------- 8) aceite ----------
    checks = {}
    for v in VARIANTES:
        checks[v] = {
            "bloco_maior_igual_215": tot[v]["bloco"] >= 215,
            "zero_perda_de_bloco": not perdas[v],
            "nenhum_curso_regride_bloco": all(cursos[v][s].get("bloco", 0) >= cursos["V0"][s].get("bloco", 0)
                                              for s in cursos[v]),
            "unidade_maior_igual_246": uni[v]["unidade"] >= 246,
            "unidade_sem_perda": uni[v]["unidade"] >= uni["V0"]["unidade"],
            "nenhum_curso_regride_unidade": all(uni_cursos[v][s].get("unidade", 0) >= uni_cursos["V0"][s].get("unidade", 0)
                                                for s in uni_cursos[v]),
        }
        checks[v]["ACEITE"] = all(checks[v].values())
    toques = {v: sum(len(id_muda[v][s]) for s in roots) for v in VARIANTES}

    report = {
        "head": "b726d4c (#48 commitada)",
        "variantes": {
            "V0": "raw / sqrt(len(sig)) [atual, controle]",
            "V1": "raw",
            "V2": "raw / sqrt(sum_{t in sig} (sig[t]*log(1+m/df[t]))**2)",
            "V3": "raw / log(2 + len(sig))",
            "V4": "raw / sqrt(|mat & sig|), 0 se nao casa nada",
        },
        "patch": "atributo de modulo disambiguator._score (unico call-site em src/: "
                 "disambiguator.py:230, nome global do proprio modulo); restaurado no finally. "
                 "src/ intocado; voter=None; sem rede/LLM.",
        "freeze_sha256_decisoes": freeze,
        "v0_identico_a_base": v0_igual,
        "placar_bloco": {v: f'{tot[v]["bloco"]}/{tot[v]["bloco_n"]}' for v in VARIANTES},
        "placar_unidade": {v: f'{uni[v]["unidade"]}/{uni[v]["unidade_n"]}' for v in VARIANTES},
        "toques_total_ids_que_mudam_bloco": toques,
        "ganhos_bloco": ganhos, "perdas_bloco": perdas,
        "ids_que_mudam": detalhe_ids,
        "cursos_bloco": cursos, "cursos_unidade": uni_cursos,
        "efeito_na_unidade_dos_que_mudam": uni_mud,
        "banda_flag_sem_mudar_bloco": banda,
        "inventario_janelas": inventario,
        "erros_de_desempate": erros_desempate,
        "correcao_dos_erros_de_desempate": corrige,
        "contrafactual_comprimento": {
            "peso_dos_termos_acrescentados": PESO_EXTRA,
            "ks": list(KS),
            "janelas_que_mudam_por_variante": {
                v: sum(1 for j in janelas if j["contrafactual"][v]) for v in VARIANTES},
            "n_janelas": len(janelas),
        },
        "checks": checks,
        "janelas": janelas,
        "limitations": [
            "Sem build/rebuild, rede ou LLM; sidecar de votos nao usado (voter=None).",
            "Ausentes permanecem no denominador da regua.",
            "Variantes fixas a priori, sem limiar: nada a calibrar, logo sem LOCO.",
            "Contrafactual acrescenta termos de peso W_TOPIC com df=1; so V2 depende desse peso "
            "(V0/V3 dependem so da contagem; V1/V4 nao dependem).",
            "Inventario cobre as decisoes finais disamb/disamb-curto com janela >= 2 capturadas; "
            "entries que REUSAM decisao cacheada por content_key (apply.py:117-123) nao chamam "
            "disambiguate e nao aparecem na captura (acompanham a decisao reusada).",
            "Unidade re-executada por variante apenas nos cursos cujo bloco mudou.",
            "O script grava com `assert not OUT.exists()`: nao sobrescreve evidencia.",
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PLACAR", json.dumps({"bloco": report["placar_bloco"],
                                "unidade": report["placar_unidade"],
                                "toques": toques}, ensure_ascii=False))
    print("CHECKS", json.dumps(checks, ensure_ascii=False))
    print("CF", json.dumps(report["contrafactual_comprimento"]["janelas_que_mudam_por_variante"],
                           ensure_ascii=False), "de", len(janelas))
    print("CORRIGE", json.dumps({v: {k: len(x) for k, x in corrige[v].items()} for v in VARIANTES},
                                ensure_ascii=False))
    print("SHA256_JSON", hashlib.sha256(OUT.read_bytes()).hexdigest())
    print("SHA256_SCRIPT", hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
