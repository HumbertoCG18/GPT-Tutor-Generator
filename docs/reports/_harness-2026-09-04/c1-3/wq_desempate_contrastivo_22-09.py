"""W-Q (CRU-04 residual): desempate CONTRASTIVO na janela, patch SO EM MEMORIA.

Regra pre-declarada R-contrastiva (unica variante):
  Entre os candidatos da janela, um termo e EXCLUSIVO quando aparece na
  assinatura de exatamente 1 candidato (e COMUM quando aparece em >= 2).
  Candidato i tem "evidencia distintiva" quando o material casa >= 1 termo
  exclusivo de i. Troca-se a escolha atual SOMENTE quando existe EXATAMENTE
  UM candidato com evidencia distintiva e ele nao e o vencedor atual (o
  vencedor atual, por construcao, nao casa nenhum exclusivo seu nesse caso).
  Caso contrario mantem. Termos vindos de secoes de revisao/referencia do
  Markdown sao descartados do material quando o heading as identifica.
  Sem expansao de janela, sem data, sem limiar ajustavel (a regra e binaria:
  nao ha parametro a calibrar, logo nao ha LOCO a reportar).

Patch: `anchor_engine.disambiguate` (o engine importa o NOME no modulo dele,
linha 14) e substituido por um wrapper que delega ao original e so troca
`block_ref` quando a regra dispara em decisao `disamb`/`disamb-curto` com
janela >= 2 refs resolviveis. Atributo restaurado no __exit__.

Reusa replay_bloco_21-09.replay (fase real de bloco, TEMPORAL_KEYS removidas,
voter=None) e replay_unidade_21-09.replay (fase real de unidade). Decisoes
congeladas por sha256 ANTES de carregar o gold. Sem build, rede, LLM, escrita
em src/, commit ou git add.
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
import time
from dataclasses import replace as dc_replace
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.path.insert(0, str(DATA))

from src.builder.routing.motor import anchor_engine as AE
from src.builder.routing.motor import disambiguator as D
from src.builder.text.normalize import normalize_match_text

CAMPOS = ("temporal_block_id", "temporal_block_method", "temporal_block_band",
          "temporal_block_flag", "temporal_block_provider")
T0 = time.time()
OUT = HERE / "wq_desempate_contrastivo_22-09.json"

_HEAD = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_REV = re.compile(r"\b(revisao|revisoes|referencia|referencias|bibliografia|"
                  r"leitura|leituras|fontes|links)\b")


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def strip_revisao(md: str):
    """Remove secoes cujo HEADING as identifica como revisao/referencia.

    Devolve (texto, n_secoes_removidas). Sem heading nao ha como identificar:
    nada e removido (e isso e reportado)."""
    if not md:
        return md, 0
    out, skip, n = [], None, 0
    for line in md.splitlines():
        m = _HEAD.match(line)
        if m:
            lvl = len(m.group(1))
            if skip is not None and lvl <= skip:
                skip = None
            if skip is None and _REV.search(normalize_match_text(m.group(2))):
                skip, n = lvl, n + 1
                continue
        if skip is None:
            out.append(line)
    return "\n".join(out), n


def analisa(entry, win, ctx, markdown, short_vocab):
    """Estado contrastivo da janela + o que a regra faria. Puro (nao decide nada)."""
    blocks = [ctx.block_by_ref(r) for r in win]
    blocks = [b for b in blocks if b is not None]
    if len(blocks) < 2:
        return None
    md, n_rev = strip_revisao(markdown or "")
    mat = D.entry_tokens(entry, md, short_vocab)
    mat_full = D.entry_tokens(entry, markdown or "", short_vocab)
    sigs = [D._block_signature(b, ctx, short_vocab) for b in blocks]
    refs = [str(b.get("id") or b.get("block_uuid") or "") for b in blocks]
    df = collections.Counter()
    for sig in sigs:
        df.update(set(sig))
    m = len(blocks)
    scores = [D._score(mat_full, sig, m, dict(df)) for sig in sigs]
    exclusivos = [{t for t in sig if df[t] == 1} for sig in sigs]
    comuns = sorted({t for t in df if df[t] >= 2})
    dist = [sorted(mat & ex) for ex in exclusivos]
    dist_full = [sorted(mat_full & ex) for ex in exclusivos]
    cands = [i for i, d in enumerate(dist) if d]
    return {"refs": refs, "scores": scores, "tam_sig": [len(s) for s in sigs],
            "comuns_n": len(comuns), "exclusivos_n": [len(e) for e in exclusivos],
            "distintivos": {refs[i]: dist[i] for i in range(m) if dist[i]},
            "distintivos_sem_poda": {refs[i]: dist_full[i] for i in range(m) if dist_full[i]},
            "secoes_revisao_removidas": n_rev,
            "poda_mudou_distintivos": dist != dist_full,
            "vencedor_regra": refs[cands[0]] if len(cands) == 1 else None,
            "n_candidatos_distintivos": len(cands)}


def contrafactual(est, escolha_atual, ks=(1, 3, 5, 10)):
    """Astra: termos que NAO casam o material mudam a escolha atual so por comprimento?

    raw_i = score_i * sqrt(|sig_i|) e invariante a tokens que nao casam; adicionar
    K termos novos a UM candidato so muda o divisor sqrt(|sig_i| + K)."""
    refs, scores, tam = est["refs"], est["scores"], est["tam_sig"]
    raw = [s * math.sqrt(t) if t else 0.0 for s, t in zip(scores, tam)]
    atual = refs.index(escolha_atual) if escolha_atual in refs else int(
        max(range(len(scores)), key=lambda i: scores[i]))
    flips = {}
    for k in ks:
        alvos = []
        for j in range(len(refs)):
            novo = [raw[i] / math.sqrt(tam[i] + (k if i == j else 0)) if tam[i] + (k if i == j else 0) else 0.0
                    for i in range(len(refs))]
            top = max(range(len(novo)), key=lambda i: novo[i])
            if top != atual:
                alvos.append({"inflado": refs[j], "nova_escolha": refs[top]})
        if alvos:
            flips[str(k)] = alvos
    return {"muda_por_comprimento": bool(flips), "flips": flips}


class PatchContrastivo:
    """Substitui anchor_engine.disambiguate; delega ao original e so troca o ref."""

    def __init__(self, capturar=None):
        self.toques = []
        self.capturar = capturar

    def __enter__(self):
        self.orig = AE.disambiguate
        assert getattr(self.orig, "__module__", "").endswith("disambiguator"), "patch sobre original"
        orig, toques, cap = self.orig, self.toques, self.capturar

        def wrapper(entry, window, ctx, markdown="", provider=""):
            dec = orig(entry, window, ctx, markdown, provider=provider)
            if dec.method not in ("disamb", "disamb-curto"):
                if cap is not None:
                    cap.append({"id": str(entry.get("id") or ""), "method": dec.method,
                                "window": list(window or []), "ref": dec.block_ref,
                                "band": dec.band, "flag": dec.flag, "provider": provider,
                                "est": None})
                return dec
            vocab = D.course_short_vocab(ctx) if dec.method == "disamb-curto" else frozenset()
            est = analisa(entry, list(window or []), ctx, markdown, vocab)
            if cap is not None:
                cap.append({"id": str(entry.get("id") or ""), "method": dec.method,
                            "window": list(window or []), "ref": dec.block_ref,
                            "band": dec.band, "flag": dec.flag, "provider": provider,
                            "est": est,
                            "contrafactual": contrafactual(est, dec.block_ref) if est else None})
            if est is None or not est["vencedor_regra"] or est["vencedor_regra"] == dec.block_ref:
                return dec
            toques.append({"id": str(entry.get("id") or ""), "de": dec.block_ref,
                           "para": est["vencedor_regra"], "method": dec.method,
                           "distintivos": est["distintivos"]})
            return dc_replace(dec, block_ref=est["vencedor_regra"])

        AE.disambiguate = wrapper
        return self

    def __exit__(self, *exc):
        AE.disambiguate = self.orig


def snap(entries):
    return {eid: {c: e.get(c) for c in CAMPOS} for eid, e in entries.items()}


def main():
    assert not OUT.exists(), "preservar evidencia existente"
    rb = load("rb_wq", HERE / "replay_bloco_21-09.py")
    ru = load("ru_wq", HERE / "replay_unidade_21-09.py")
    compare = load("cmp_wq", HERE / "compara_herancas_15-09.py")
    mede = compare.mede   # golds() so depois do congelamento

    estado, capturas = {}, {}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"}
                       else ".frzero/pacote_fontes_15-09") / name
        cap = []
        # base COM captura, SEM regra: wrapper que so observa
        orig = AE.disambiguate

        def observador(entry, window, ctx, markdown="", provider="", _o=orig, _cap=cap):
            dec = _o(entry, window, ctx, markdown, provider=provider)
            if dec.method in ("disamb", "disamb-curto"):
                vocab = D.course_short_vocab(ctx) if dec.method == "disamb-curto" else frozenset()
                est = analisa(entry, list(window or []), ctx, markdown, vocab)
                _cap.append({"id": str(entry.get("id") or ""), "method": dec.method,
                             "window": list(window or []), "ref": dec.block_ref, "band": dec.band,
                             "flag": dec.flag, "provider": provider, "est": est,
                             "contrafactual": contrafactual(est, dec.block_ref) if est else None})
            return dec

        AE.disambiguate = observador
        try:
            saved, base, dec_base, _ = rb.replay(root)
        finally:
            AE.disambiguate = orig
        with PatchContrastivo() as p:
            _, novo, dec_novo, _ = rb.replay(root)
            toques = list(p.toques)
        capturas[sig] = cap
        mudou = [i for i in base if base[i].get("temporal_block_id") != novo[i].get("temporal_block_id")]
        estado[sig] = {"root": root, "saved": saved, "base": base, "novo": novo,
                       "dec_base": dec_base, "dec_novo": dec_novo, "toques": toques,
                       "mudou": mudou}
        log(sig, "bloco ok | toques:", len(toques), "| ids que mudam:", len(mudou))

    # ---------- congelamento das decisoes ANTES do gold ----------
    congelado = {sig: {"base": snap(st["base"]), "R": snap(st["novo"])} for sig, st in estado.items()}
    freeze = hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True)
                            .encode("utf-8")).hexdigest()
    log("FREEZE", freeze)

    # ---------- avaliacao de BLOCO (gold a partir daqui) ----------
    tot = {"base": collections.Counter(), "R": collections.Counter()}
    cursos = {"base": {}, "R": {}}
    gold_por_id, acertos = {}, {"base": {}, "R": {}}
    for sig, st in estado.items():
        root = st["root"]
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig]
                                             / "manifest.json")["entries"]}
        index = compare.indexed(list(st["saved"].values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gb = mede.golds(sig)[0]
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        c = {v: collections.Counter() for v in ("base", "R")}
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
            for v, key in (("base", "base"), ("R", "novo")):
                c[v]["bloco_n"] += 1
                ent = st[key].get(eid) if eid else None
                if ent is None:
                    c[v]["bloco_ausente"] += 1
                    continue
                ok = compare.predictions(root, ent)[0] == gb[gid]
                c[v]["bloco"] += ok
                acertos[v][(sig, eid)] = ok
        for v in ("base", "R"):
            cursos[v][sig] = dict(c[v])
            tot[v].update(c[v])
        log(sig, "bloco", dict(c["base"]), "->", dict(c["R"]))

    ganhos = sorted(f"{s}:{e}" for (s, e) in acertos["base"]
                    if acertos["base"][(s, e)] is False and acertos["R"].get((s, e)) is True)
    perdas = sorted(f"{s}:{e}" for (s, e) in acertos["base"]
                    if acertos["base"][(s, e)] is True and acertos["R"].get((s, e)) is False)

    # ---------- inventario das janelas multicandidatas ----------
    # SO a decisao FINAL de cada entry conta: `disambiguate` e chamada ate 2x por entry
    # (a 2a com a janela do card, anchor_engine.py:287) e a chamada descartada nao decide.
    inventario, janelas, descartadas = {}, [], collections.Counter()
    for sig, cap in capturas.items():
        c = collections.Counter()
        fin = estado[sig]["dec_base"]
        porid = {}
        for it in cap:
            d = fin.get(it["id"])
            if (d and d.get("method") == it["method"] and list(d.get("window") or []) == it["window"]
                    and d.get("block_ref") == it["ref"]):
                porid[it["id"]] = it     # ultima chamada que casa a decisao gravada
            else:
                descartadas[sig] += 1
        for it in porid.values():
            if it["est"] is None:
                # janela com >=2 refs mas <2 blocos RESOLVIVEIS (ref fantasma): nao ha
                # desempate real; fora do inventario e fora da regra.
                c["janela_degradada_menos_de_2_blocos"] += 1
                continue
            c["disamb_ge2"] += 1
            c[f'banda_{it["band"]}'] += 1
            g = gold_por_id.get((sig, it["id"]))
            ok = None if g is None else (it["ref"] == g)
            if ok is True:
                c["certas"] += 1
            elif ok is False:
                c["erradas"] += 1
            else:
                c["sem_gold"] += 1
            if it["est"]["poda_mudou_distintivos"]:
                c["poda_revisao_mudou"] += 1
            if it["est"]["secoes_revisao_removidas"]:
                c["com_secao_revisao"] += 1
            if it["contrafactual"] and it["contrafactual"]["muda_por_comprimento"]:
                c["contrafactual_muda"] += 1
            regra = it["est"]["vencedor_regra"]
            janelas.append({
                "curso": sig, "id": it["id"], "method": it["method"], "band": it["band"],
                "flag": it["flag"], "provider": it["provider"], "janela": it["est"]["refs"],
                "escolha_atual": it["ref"], "gold": g, "certa_hoje": ok,
                "tam_sig": it["est"]["tam_sig"], "comuns_n": it["est"]["comuns_n"],
                "exclusivos_n": it["est"]["exclusivos_n"],
                "distintivos": it["est"]["distintivos"],
                "n_candidatos_distintivos": it["est"]["n_candidatos_distintivos"],
                "vencedor_regra": regra,
                "regra_dispara": bool(regra and regra != it["ref"]),
                "depois_da_regra": regra if (regra and regra != it["ref"]) else it["ref"],
                "secoes_revisao_removidas": it["est"]["secoes_revisao_removidas"],
                "contrafactual": it["contrafactual"],
            })
        inventario[sig] = dict(c)

    erros_desempate = [j for j in janelas if j["certa_hoje"] is False
                       and j["gold"] in j["janela"]]
    parcial = {"head": "9220a57+diff48", "freeze_sha256_decisoes": freeze,
               "placar_bloco": {v: f'{tot[v]["bloco"]}/{tot[v]["bloco_n"]}' for v in tot},
               "ganhos_bloco": ganhos, "perdas_bloco": perdas,
               "inventario": inventario, "cursos_bloco": cursos,
               "toques": {s: st["toques"] for s, st in estado.items()},
               "janelas": janelas, "erros_de_desempate": erros_desempate,
               "status": "PARCIAL — falta a fase de unidade"}
    OUT.write_text(json.dumps(parcial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log("PARCIAL gravado", OUT.name)
    print("PLACAR_BLOCO", json.dumps(parcial["placar_bloco"], ensure_ascii=False))
    print("GANHOS", ganhos, "PERDAS", perdas)

    # ---------- unidade encadeada, so nos cursos cujo bloco mudou ----------
    uni = {"base": collections.Counter(), "R": collections.Counter()}
    uni_cursos = {"base": {}, "R": {}}
    uni_mud = []
    orig_read = ru.read
    upos = {}
    algum = any(st["mudou"] for st in estado.values())
    for sig, st in (estado.items() if algum else []):
        planos = [("base", st["base"])] + ([("R", st["novo"])] if st["mudou"] else [])
        for nome, entries in planos:
            feed = [copy.deepcopy(entries[i]) for i in entries]

            def patched(path, _feed=feed, _orig=orig_read):
                data = _orig(path)
                if Path(path).name == "manifest.json":
                    data = {**data, "entries": _feed}
                return data

            ru.read = patched
            try:
                _, pos, _ = ru.replay(st["root"])
            finally:
                ru.read = orig_read
            upos[(sig, nome)] = pos
        if not st["mudou"]:
            upos[(sig, "R")] = upos[(sig, "base")]
        log(sig, "unidade ok | reexecutada:", bool(st["mudou"]))

    for sig, st in (estado.items() if algum else []):
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig]
                                             / "manifest.json")["entries"]}
        index = compare.indexed(list(st["saved"].values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gu = mede.golds(sig)[1]
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        c = {v: collections.Counter() for v in ("base", "R")}
        for row in rows:
            if row["unidade"] == "":
                continue
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            eid = str(hits[0]["id"]) if hits else None
            for v in ("base", "R"):
                c[v]["unidade_n"] += 1
                ent = upos[(sig, v)].get(eid) if eid else None
                c[v]["unidade"] += bool(ent) and str(ent.get("computed_unit_slug") or "") in gu[gid]
        for v in ("base", "R"):
            uni_cursos[v][sig] = dict(c[v])
            uni[v].update(c[v])
        for eid in st["mudou"]:
            ub = str(upos[(sig, "base")][eid].get("computed_unit_slug") or "")
            ur = str(upos[(sig, "R")][eid].get("computed_unit_slug") or "")
            uni_mud.append({"curso": sig, "id": eid, "unidade_base": ub, "unidade_R": ur,
                            "mudou_unidade": ub != ur,
                            "bloco_base": st["base"][eid].get("temporal_block_id"),
                            "bloco_R": st["novo"][eid].get("temporal_block_id"),
                            "gold_bloco": gold_por_id.get((sig, eid))})
        log(sig, "unidade", dict(c["base"]), "->", dict(c["R"]))

    checks = {
        "base_reproduz_bloco_214_de_237": (tot["base"]["bloco"], tot["base"]["bloco_n"]) == (214, 237),
        "bloco_maior_igual_215": tot["R"]["bloco"] >= 215,
        "zero_perda_de_bloco": not perdas,
        "nenhum_curso_regride_bloco": all(cursos["R"][s].get("bloco", 0) >= cursos["base"][s].get("bloco", 0)
                                          for s in cursos["R"]),
        "unidade_nao_regride": (not algum) or uni["R"]["unidade"] >= uni["base"]["unidade"],
        "nenhum_curso_regride_unidade": all(uni_cursos["R"][s].get("unidade", 0) >= uni_cursos["base"][s].get("unidade", 0)
                                            for s in uni_cursos["R"]),
    }
    checks["ACEITE"] = all(v is True for v in checks.values())

    report = {
        "head": "9220a57 + diff nao commitado da #48 em src/",
        "regra": "R-contrastiva (termo EXCLUSIVO = assinatura de 1 so candidato; troca so com "
                 "exatamente 1 candidato com exclusivo casado e != escolha atual)",
        "formula_atual_do_disamb": "src/builder/routing/motor/disambiguator.py:121-129 "
                                   "_score = sum(peso_t * log(1+m/df_t) para t em mat&sig) / sqrt(len(sig)) "
                                   "-> normalizacao pela RAIZ DO TAMANHO DA ASSINATURA (confirma o Astra); "
                                   "escolha e argmax + gate D4 em :232-255.",
        "freeze_sha256_decisoes": freeze,
        "patch": "anchor_engine.disambiguate (nome importado em anchor_engine.py:14) trocado por wrapper "
                 "que delega ao original de disambiguator.py e so substitui block_ref quando a regra dispara; "
                 "atributo restaurado no __exit__. src/ intocado.",
        "checks": checks,
        "placar_bloco": {v: f'{tot[v]["bloco"]}/{tot[v]["bloco_n"]}' for v in tot},
        "placar_unidade": ({v: f'{uni[v]["unidade"]}/{uni[v]["unidade_n"]}' for v in uni} if algum else
                           "VACUO — nenhuma entry muda de bloco, a fase de unidade recebe entrada identica; "
                           "na 1a execucao deste script a fase foi rodada nos 7 cursos e a base bateu 246/284 "
                           "(MF 61/66, SO 30/37, IA 39/42, ES2 25/28, TCC 17/18, CG 74/93, FR 0/0)"),
        "chamadas_descartadas_ignoradas": dict(descartadas),
        "ganhos_bloco": ganhos, "perdas_bloco": perdas,
        "cursos_bloco": cursos, "cursos_unidade": uni_cursos,
        "inventario_janelas_multicandidatas": inventario,
        "toques": {s: st["toques"] for s, st in estado.items()},
        "efeito_na_unidade_dos_que_mudam": uni_mud,
        "erros_de_desempate": erros_desempate,
        "janelas": janelas,
        "scope": "apply_anchor_engine e apply_unit_subunit_fields reais importados de src/; patch so em "
                 "atributo de modulo, restaurado; voter=None; gold carregado depois do congelamento.",
        "limitations": [
            "Sem build/rebuild, rede ou LLM; sidecar de votos nao usado.",
            "Ausentes permanecem no denominador da regua.",
            "Poda de revisao/referencia so onde HA heading Markdown que a identifique; material sem "
            "heading nao e podado (contado em com_secao_revisao/poda_revisao_mudou).",
            "Regra binaria, sem limiar: nao ha parametro para calibrar por LOCO.",
            "Unidade re-executada apenas nos cursos cujo bloco mudou (identica por construcao nos demais).",
            "Inventario cobre 97 das 99 decisoes finais disamb/disamb-curto com janela >= 2: IA `lista1` e "
            "`minimax` REUSAM a decisao cacheada por content_key (apply.py:117-123) e nao chamam "
            "`disambiguate`, logo nao aparecem na captura; como reusam a MESMA decisao, a regra as "
            "acompanharia automaticamente.",
            "1 toque da regra (MF exerciciosdafny1, bloco-12 -> bloco-11, gold bloco-12) NAO alterou o bloco "
            "final: o fallback de card do proprio engine (anchor_engine.py:283-291) reconduz ao bloco-12. "
            "Mecanismo nao instrumentado nesta medicao; o que esta MEDIDO e o id final inalterado.",
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PLACAR", json.dumps({"bloco": report["placar_bloco"], "unidade": report["placar_unidade"]},
                               ensure_ascii=False))
    print("CHECKS", json.dumps(checks, ensure_ascii=False))
    print("INVENTARIO", json.dumps(inventario, ensure_ascii=False))
    print("SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
