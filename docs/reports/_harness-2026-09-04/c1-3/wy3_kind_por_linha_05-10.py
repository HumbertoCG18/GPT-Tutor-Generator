"""W-Y v3 (#52, MOTOR-08, 05/10): tipo de bloco por LINHA remedido na base vigente (dev f404c6de, referencia 87).

Gate 1 de medicao do usuario em 05/10 ("Rodar a v3"), depois da v2 (wy2_*, reprovada: TCC bloco -6 pela
adjudicacao 2; FR desloca 4 sem gold pela 3). PRE-REGISTRO, fixado antes de qualquer leitura de gold:
- base: indice gravado nas raizes do harness; DEVE reproduzir por ID a referencia 87 (`referencia87_replay_ap1.json`,
  6299edfd), senao aborta antes do gold.
- controle: indice reconstruido em memoria com o codigo atual (pipeline real, persist=False).
- P1adj: prototipo P1 do W-Y (wy_kind_por_linha_22-09.py) + adjudicacoes do usuario de 05/10, revistas apos a v2:
  (2) REVISTA: "Oficina de problemas - Entrega T2" (Atividade Aula) segue workshop (regra do prototipo, sem cauda);
  (3) REVISTA: "apresentacao da disciplina/do curso[ e introducao]" = class (sai do cue de overview do prototipo);
  (4) review que o pipeline demove a class volta ao DP de unidades (2a reconstrucao com essas linhas = class);
  (1) gold do SO inalterado (bloco-09).
- P1adjH: P1adj + H-duvidas: bloco review cujas linhas review vem TODAS de duvidas/atendimento pre-prova
  (regra "office_hours>review") nao e alvo do prep-prova (`anchor_engine.resolve_exam_prep`), que segue para o bloco
  hospedavel anterior. Review de "Revisao" continua alvo.
ACEITE (cada braco contra controle): 0 perda por ID em bloco, unidade, sub primaria e sub aceita; nenhum curso regride
em nenhum eixo; segmentacao identica (ids e linhas). Sem parametro livre.
Cadeia de placar = a da referencia 87 (verifica_integracao.py): replay_bloco -> wz2.rodar com o callback real de
subunidade; gold (wx_gold_v2_final) so depois das decisoes congeladas por sha256.
Patches so em memoria; sem rede/LLM/build; escrita so nas saidas wy3_*. Tabelas A/B nos 8 cursos vivos (so leitura).
Uso: python -B wy3_kind_por_linha_05-10.py --worktree <raiz com o src da dev>
"""
import argparse
import collections
import copy
import hashlib
import importlib.util
import inspect
import json
import re
import subprocess
import sys
import time
from pathlib import Path

T0 = time.time()
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
OUT_JSON = HERE / "wy3_kind_por_linha_05-10.json"
OUT_MD = HERE / "wy3_kind_por_linha_05-10.md"
OUT_CONG = HERE / "wy3_kind_por_linha_05-10_congelado.json"
CAMPOS = ("bloco", "unidade", "sub")
EIXOS = ("bloco", "unidade", "sub_primaria", "sub_aceita")
BRACOS = ("base", "controle", "P1adj", "P1adjH")

ap = argparse.ArgumentParser()
ap.add_argument("--worktree", required=True)
ARGS = ap.parse_args()
WT = Path(ARGS.worktree).resolve()
sys.path.insert(0, str(WT))
import src  # noqa: E402
src.__path__ = [str(WT / "src")]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


# W-Y original: instala os tripwires (rede, Gemini, Datalab, escrita) e fornece o prototipo P1.
W = load("wy1", HERE / "wy_kind_por_linha_22-09.py")
W.PERMITIDOS |= {OUT_JSON.resolve(), OUT_MD.resolve(), OUT_CONG.resolve()}
from src.builder.routing.motor import anchor_engine as AE  # noqa: E402
from src.builder.routing.motor import context as MCTX  # noqa: E402
from src.utils.helpers import collapse_ws  # noqa: E402

IX = W.IX


# ---------------------------------------------------------------- P1adj: adjudicacoes (2) e (4)
CAUDA_ENTREGA = re.compile(r"\bentrega (do |de |da )?(trabalho|t\d+|tp\d+|tf)\b")
KIND_ROTULO_W = W.kind_rotulo
FORCA = set()          # linhas (indice da timeline) forcadas a class: review demovida (adjudicacao 4)


def kind_rotulo_adj(label):
    k, r = KIND_ROTULO_W(label)
    if k == "overview" and label.startswith("apresentacao"):             # adjudicacao (3) revista
        return "class", "4:overview>class(apresentacao-adj3)"
    return k, r


def proto_linhas_adj(timeline, ajuste=False):
    """W.proto_linhas com P1 (ajuste=True), kind_rotulo_adj e as linhas de FORCA = class."""
    content_keys = W.rotulo_keys(timeline)
    out = []
    for row in timeline:
        raw = " ".join(row.get(k, "") for k in content_keys).strip()
        k, r, marcador, label = W.proto_linha(raw, IX._row_atividade(row), ajuste)
        out.append({"kind": k, "regra": r, "marcador": marcador, "label": label,
                    "vazia": not collapse_ws(IX._KIND_TOKEN_RE.sub("", raw))})
    for i, o in enumerate(out):
        if o["kind"] != "office_hours":
            continue
        prox = ""
        for p in out[i + 1:]:
            if p["vazia"] or p["kind"] in W.PULA_ADJ or (ajuste and p["regra"].startswith("4:office_hours")):
                continue
            prox = p["kind"]
            break
        if prox in W.PROVA:
            o["kind"], o["regra"] = "review", f"{o['regra']}>review(proxima={prox})"
        else:
            o["regra"] = f"{o['regra']}(proxima={prox or 'fim'})"
    for i in FORCA:                                                       # adjudicacao (4)
        if out[i]["kind"] == "review":
            out[i]["kind"], out[i]["regra"] = "class", f"{out[i]['regra']}>class(review-demovida-no-DP)"
    return out


def perfis_vivos():
    """Os 8 cursos do W-Y; perfis sem repo (Metodos Numericos, 05/10) ficam fora."""
    d = read(Path.home() / "AppData/Roaming/GPTTutorGenerator/subjects.json")
    out = {W.SIG[Path(s["repo_root"]).name]: (Path(s["repo_root"]), W.SimpleNamespace(**s))
           for s in d.values() if s.get("repo_root") and Path(s["repo_root"]).name in W.SIG}
    assert len(out) == len(W.SIG), sorted(out)
    return dict(sorted(out.items()))


W.kind_rotulo = kind_rotulo_adj
W.proto_linhas = proto_linhas_adj
W.perfis_vivos = perfis_vivos
rows_of = W.rows_of


def rebuild_adj(repo, prof, tag):
    """Duas reconstrucoes: a 1a acha os blocos review que o pipeline demove a class; a 2a os poe no DP."""
    FORCA.clear()
    idx1, timeline = W.rebuild(repo, prof, "P1", f"{tag}:f1")
    linhas = proto_linhas_adj(timeline, True)
    demov = []
    for b in idx1["blocks"]:
        if b.get("kind") == "class" and not b.get("manual_kind_override"):
            rr = [r for r in rows_of(b) if linhas[r]["kind"] == "review"]
            if rr:
                demov.append({"bloco": b["id"], "linhas": rr, "unit_f1": b.get("unit_slug")})
    FORCA.update(r for d in demov for r in d["linhas"])
    try:
        idx2, _ = W.rebuild(repo, prof, "P1", f"{tag}:f2")
        linhas2 = proto_linhas_adj(timeline, True)
    finally:
        FORCA.clear()
    by_id = {b["id"]: b for b in idx2["blocks"]}
    for d in demov:
        b = by_id.get(d["bloco"]) or {}
        d["kind_f2"], d["unit_f2"] = b.get("kind"), b.get("unit_slug")
    skip_h = sorted(b["id"] for b in idx2["blocks"] if b.get("kind") == "review"
                    and [r for r in rows_of(b) if linhas2[r]["kind"] == "review"]
                    and all(">review(proxima=" in linhas2[r]["regra"] for r in rows_of(b) if linhas2[r]["kind"] == "review"))
    return idx2, timeline, linhas2, demov, skip_h


# ---------------------------------------------------------------- H: prep-prova pula review de duvidas
ORIG_PREP = AE.resolve_exam_prep
PREP_SRC = inspect.getsource(ORIG_PREP)
for trecho in ('mains = [b for b in ctx.blocks if is_main_exam_block(b)]',
               'if str(b.get("kind") or "") in _NOT_PREP_HOSTS or not b.get("id"):',
               'provider="prep-prova", method="prep-prova", window=[ref])'):
    assert trecho in PREP_SRC, f"resolve_exam_prep mudou: {trecho}"
SKIP_H, CUR = {}, {"sig": ""}


def prep_h(entry, ctx):
    n = AE._exam_number(entry)
    if n <= 0:
        return None
    mains = [b for b in ctx.blocks if AE.is_main_exam_block(b)]
    if n > len(mains):
        return None
    target = mains[n - 1]
    pula = SKIP_H.get(CUR["sig"], ())
    prev = None
    for b in ctx.blocks:
        if b is target:
            break
        if str(b.get("kind") or "") in AE._NOT_PREP_HOSTS or not b.get("id"):
            continue
        if str(b.get("id")) in pula:                                      # H-duvidas
            continue
        prev = b
    if prev is None:
        return None
    ref = str(prev.get("id"))
    return AE.AnchorDecision(block_ref=ref, conf=0.0, band="media", flag=False,
                             provider="prep-prova", method="prep-prova", window=[ref])


# ---------------------------------------------------------------- A + B: 8 cursos vivos (so leitura)
def parte_ab():
    linhas, blocos_mudam, seg, demovidos, skip = [], [], {}, {}, {}
    tot = {k: collections.Counter() for k in ("linha_atual", "linha_P1adj", "bloco_vivo", "bloco_controle", "bloco_P1adj")}
    class_com_cauda = []
    for sig, (repo, prof) in W.perfis_vivos().items():
        vivo = read(repo / "course/.timeline_index.json")["blocks"]
        ctrl, timeline = W.rebuild(repo, prof, False, f"{sig}:ctrl")
        adj, _, novos, demovidos[sig], skip[sig] = rebuild_adj(repo, prof, f"{sig}:adj")
        cand = IX._build_timeline_candidate_rows(timeline)
        by_row = lambda bs: {r: b for b in bs for r in rows_of(b)}
        bv, bc, ba = by_row(vivo), by_row(ctrl["blocks"]), by_row(adj["blocks"])
        rk = W.rotulo_keys(timeline)
        for cr in cand:
            i = cr["index"]
            n1 = novos[i]
            v, kc, ka = bv.get(i), bc.get(i), ba.get(i)
            rec = {"curso": sig, "linha": i, "data": cr["date_text"], "rotulo": " ".join(cr["row"].get(k, "") for k in rk).strip(),
                   "atividade": IX._row_atividade(cr["row"]), "marcador": n1["marcador"], "tipo_linha_atual": cr["kind"],
                   "bloco_vivo": v and v["id"], "tipo_bloco_vivo": v and v.get("kind"), "override_vivo": v and v.get("manual_kind_override"),
                   "bloco_controle": kc and kc["id"], "tipo_bloco_controle": kc and kc.get("kind"), "unit_controle": kc and kc.get("unit_slug"),
                   "tipo_linha_P1adj": n1["kind"], "regra_P1adj": n1["regra"], "bloco_P1adj": ka and ka["id"],
                   "tipo_bloco_P1adj": ka and ka.get("kind"), "unit_P1adj": ka and ka.get("unit_slug")}
            rec["caso"] = W.alvo_de(sig, n1["label"], n1["marcador"], rec["tipo_bloco_vivo"], rec["override_vivo"])
            rec["muda_linha"] = rec["tipo_linha_atual"] != rec["tipo_linha_P1adj"]
            rec["muda_bloco"] = (rec["tipo_bloco_controle"] or "") != (rec["tipo_bloco_P1adj"] or "")
            rec["muda_unidade"] = (rec["unit_controle"] or "") != (rec["unit_P1adj"] or "")
            linhas.append(rec)
            tot["linha_atual"][cr["kind"]] += 1
            tot["linha_P1adj"][n1["kind"]] += 1
            if n1["kind"] == "class" and CAUDA_ENTREGA.search(n1["label"]):
                class_com_cauda.append({"curso": sig, "linha": i, "rotulo": rec["rotulo"][:90]})
        for key, bs in (("bloco_vivo", vivo), ("bloco_controle", ctrl["blocks"]), ("bloco_P1adj", adj["blocks"])):
            tot[key].update(str(b.get("kind")) for b in bs)
        by_rows = {rows_of(b): b for b in adj["blocks"]}
        for b in ctrl["blocks"]:
            p = by_rows.get(rows_of(b))
            if p is None or p.get("kind") != b.get("kind") or p.get("unit_slug") != b.get("unit_slug"):
                blocos_mudam.append({"curso": sig, "controle": b["id"], "de": b.get("period_start"), "kind_controle": b.get("kind"),
                                     "unit_controle": b.get("unit_slug"), "novo": p and p["id"], "kind_novo": p and p.get("kind"),
                                     "unit_novo": p and p.get("unit_slug"), "segmentacao_mudou": p is None,
                                     "sessoes": [s.get("label") for s in b.get("sessions") or []][:4]})
        seg[sig] = {"vivo_x_controle": W.seg_diff(vivo, ctrl["blocks"]), "controle_x_P1adj": W.seg_diff(ctrl["blocks"], adj["blocks"])}
        print("AB", sig, "blocos mudam:", sum(1 for m in blocos_mudam if m["curso"] == sig), "| demovidos:",
              [d["bloco"] for d in demovidos[sig]], "| skip H:", skip[sig], round(time.time() - T0), "s", flush=True)
    return {"totais": {k: dict(sorted(v.items())) for k, v in tot.items()}, "linhas": linhas, "blocos_que_mudam": blocos_mudam,
            "demovidos_no_DP": demovidos, "skip_H": skip, "class_com_cauda_entrega_nao_alteradas": class_com_cauda}, seg


# ---------------------------------------------------------------- C: placar pela cadeia da referencia 87
C13 = HERE
wz2 = load("wz2", C13 / "wz2_diagnostico_causal_23-09.py")
compare = wz2.load("d_cmp", C13 / "compara_herancas_15-09.py")
rb = wz2.load("d_rb", C13 / "replay_bloco_21-09.py")
ru = wz2.load("d_ru", C13 / "replay_unidade_21-09.py")
wz = wz2.load("d_wz", C13 / "wz_bloco_cobertura_22-09.py")
wx = wz2.load("d_wx", C13 / "wx_regua_corrigida_22-09.py")
from src.builder.engine import _auto_map_entry_subtopic  # noqa: E402
ru.auto_sub = _auto_map_entry_subtopic
NOMES = compare.mede.NOMES
RAIZES = {s: wz.root_de(s, NOMES) for s in NOMES}


def identidade(blocks):
    return [(b["id"], rows_of(b)) for b in blocks]


def alinhar_uuid(stored, idx):
    """Mesma segmentacao -> block_uuid do indice gravado (o comparador mapeia uuid -> id pelo gravado)."""
    if identidade(stored["blocks"]) != identidade(idx["blocks"]):
        return False
    uu = {b["id"]: b.get("block_uuid") for b in stored["blocks"]}
    for b in idx["blocks"]:
        b["block_uuid"] = uu[b["id"]]
    return True


def saidas_de(dec):
    return {sig: {eid: {k: (r.get("final") or {}).get(k) for k in CAMPOS} for eid, r in dec[sig].items() if "final" in r}
            for sig in dec}


def rodar_braco(arm, idxs, prep=None):
    por_raiz = {str(RAIZES[s].resolve()): idxs[s] for s in idxs} if idxs else {}
    orig_load, orig_read = MCTX.load_repo_artifact, ru.read

    def art(repo, rel):
        if rel == "course/.timeline_index.json" and por_raiz:
            return copy.deepcopy(por_raiz[str(Path(repo).resolve())])
        return orig_load(repo, rel)

    def rd(path):
        p = Path(path)
        if p.name == ".timeline_index.json" and por_raiz:
            return copy.deepcopy(por_raiz[str(p.parent.parent.resolve())])
        return orig_read(path)

    estado = {}
    MCTX.load_repo_artifact, AE.resolve_exam_prep = art, prep or ORIG_PREP
    try:
        for sig in NOMES:
            CUR["sig"] = sig
            saved, bloco_novo, dec_motor, _ = rb.replay(RAIZES[sig])
            estado[sig] = {"root": RAIZES[sig], "saved": saved, "decisoes": dec_motor,
                           "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
    finally:
        MCTX.load_repo_artifact, AE.resolve_exam_prep = orig_load, ORIG_PREP
    ru.read = rd
    try:
        novo = wz2.rodar(arm, estado, ru, compare, pontuar=False)
    finally:
        ru.read = orig_read
    prep_motor = {s: sorted(e for e, d in v["decisoes"].items() if d.get("provider") == "prep-prova") for s, v in estado.items()}
    return estado, saidas_de(novo), prep_motor


def mudancas(a, b):
    return [{"curso": s, "eid": e, "de": a.get(s, {}).get(e), "para": b.get(s, {}).get(e)}
            for s in sorted(set(a) | set(b)) for e in sorted(set(a.get(s, {})) | set(b.get(s, {})))
            if a.get(s, {}).get(e) != b.get(s, {}).get(e)]


def parte_c():
    stored = {s: read(RAIZES[s] / "course/.timeline_index.json") for s in NOMES}
    idx = {"controle": {}, "P1adj": {}}
    extra = {"segmentacao": {}, "demovidos_no_DP": {}, "skip_H": {}}
    for s in NOMES:
        prof = W.SimpleNamespace(**read(RAIZES[s] / "_inputs_15-09.json")["profile_input"])
        ctrl, _ = W.rebuild(RAIZES[s], prof, False, f"C:{s}:ctrl")
        adj, _, _, extra["demovidos_no_DP"][s], extra["skip_H"][s] = rebuild_adj(RAIZES[s], prof, f"C:{s}:adj")
        extra["segmentacao"][s] = {"controle": alinhar_uuid(stored[s], ctrl), "P1adj": alinhar_uuid(stored[s], adj)}
        idx["controle"][s], idx["P1adj"][s] = ctrl, adj
        print("C rebuild", s, extra["segmentacao"][s], "| demovidos:", [d["bloco"] for d in extra["demovidos_no_DP"][s]],
              "| skip H:", extra["skip_H"][s], round(time.time() - T0), "s", flush=True)
    if not all(all(v.values()) for v in extra["segmentacao"].values()):
        return {"abortado": "segmentacao mudou: ids de bloco do gold nao valem; gold nao consultado", **extra}
    SKIP_H.update(extra["skip_H"])
    res = {}
    for arm in BRACOS:
        est, dec, prep = rodar_braco(arm, None if arm == "base" else idx["P1adj" if arm == "P1adjH" else arm],
                                     prep_h if arm == "P1adjH" else None)
        res[arm] = {"estado": est, "decisoes": dec, "prep_prova": prep}
        print("C braco", arm, "ids:", sum(len(v) for v in dec.values()), round(time.time() - T0), "s", flush=True)
    ref_path = WT / "docs/reports/2026-10-04-integracao-ap1/referencia87_replay_ap1.json"
    ref = read(ref_path)["decisoes"]
    gate = mudancas(ref, res["base"]["decisoes"])
    out = {**extra, "referencia": {"arquivo": str(ref_path), "sha256": hashlib.sha256(ref_path.read_bytes()).hexdigest()},
           "base_x_referencia87": gate,
           "mudancas_sem_gold": {f"{a}->{b}": mudancas(res[a]["decisoes"], res[b]["decisoes"])
                                 for a, b in (("base", "controle"), ("controle", "P1adj"), ("controle", "P1adjH"), ("P1adj", "P1adjH"))},
           "prep_prova_por_braco": {a: res[a]["prep_prova"] for a in BRACOS}}
    cong = {"decisoes": {a: res[a]["decisoes"] for a in BRACOS}}
    cong["sha256"] = sha(cong["decisoes"])
    OUT_CONG.write_text(json.dumps(cong, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    out["congelado"] = {"arquivo": OUT_CONG.name, "sha256_decisoes": cong["sha256"],
                        "sha256_arquivo": hashlib.sha256(OUT_CONG.read_bytes()).hexdigest()}
    print("congelado", cong["sha256"], "| base x ref87:", len(gate), flush=True)
    if gate:
        out["abortado"] = "base difere da referencia 87; gold nao consultado"
        return out
    # ======================= gold entra aqui (so placar)
    est = res["base"]["estado"]
    wz.preparar_avaliacao(est, compare, compare.mede, wx)
    placar, flags = {}, {}
    for a in BRACOS:
        assert saidas_de(wz2.CAP[a]) == res[a]["decisoes"], f"decisoes de {a} mudaram apos gold"
        placar[a], flags[a] = wz.avaliar(est, res[a]["decisoes"])
    out["placar"] = {a: {"total": wz.totais(placar[a]), "por_curso": placar[a]} for a in BRACOS}
    out["por_id"] = {}
    out["aceite"] = {}
    for de, para in (("base", "controle"), ("controle", "P1adj"), ("controle", "P1adjH"), ("P1adj", "P1adjH")):
        dif = [{"curso": k[0], "gold_id": k[1], "eixo": k[2], "tipo": "ganho" if flags[para].get(k) else "perda"}
               for k in sorted(flags[de]) if flags[de][k] != flags[para].get(k)]
        out["por_id"][f"{de}->{para}"] = dif
        if de == "controle":
            regride = sorted({(s, e) for s in placar[de] for e in EIXOS if placar[para][s].get(e, 0) < placar[de][s].get(e, 0)})
            out["aceite"][para] = {"perdas": sum(d["tipo"] == "perda" for d in dif), "ganhos": sum(d["tipo"] == "ganho" for d in dif),
                                   "cursos_que_regridem": regride,
                                   "passa": not any(d["tipo"] == "perda" for d in dif) and not regride}
    return out


# ---------------------------------------------------------------- D: obsoletos (no src da worktree)
def parte_d():
    out = []
    for arq, needle, porque in W.OBSOLETOS:
        linhas = (WT / arq).read_text(encoding="utf-8").splitlines()
        n = next((i + 1 for i, l in enumerate(linhas) if needle in l and not l.lstrip().startswith("#")), None)
        out.append({"arquivo": arq, "linha": n, "simbolo": needle, "motivo": porque})
    return out


# ---------------------------------------------------------------- relatorio
def md(rep):
    A, C = rep["A"], rep["C"]
    L = ["# W-Y v3 (#52, MOTOR-08) — tipo de bloco por linha na base vigente", "",
         f"src: `{rep['worktree']}` @ {rep['head']}; pre-registro sha256 `{rep['sha256_preregistro']}`; "
         f"resultado sha256 `{rep['sha256_resultado']}`; {rep['segundos']} s. Repos intocados: {rep['repos_intocados']['iguais']}.", "",
         "Bracos: base (indice gravado = referencia 87), controle (indice reconstruido com o codigo atual), P1adj (prototipo "
         "P1 do W-Y + adjudicacoes 2 e 4 de 05/10), P1adjH (P1adj + H-duvidas no prep-prova). Aceite contra controle.", ""]
    if C.get("placar"):
        L += ["## C. Placar (cadeia da referencia 87)", "", "| braco | bloco | unidade | sub prim | sub aceita |", "|---|---|---|---|---|"]
        for a, v in C["placar"].items():
            t = v["total"]
            L.append(f"| {a} | {t.get('bloco')}/{t.get('bloco_n')} | {t.get('unidade')}/{t.get('unidade_n')} | "
                     f"{t.get('sub_primaria')}/{t.get('sub_n')} | {t.get('sub_aceita')}/{t.get('sub_n')} |")
        L += ["", "Aceite (contra controle): " + json.dumps(C["aceite"], ensure_ascii=False), "", "Diferencas por ID (gold):", ""]
        for k, lst in C["por_id"].items():
            L.append(f"- {k}: " + ("; ".join(f"{d['tipo']} {d['curso']} {d['eixo']} {d['gold_id']}" for d in lst) or "nenhuma"))
        L += ["", "Por curso (bloco/unidade/sub prim/sub aceita):", ""]
        for s in C["placar"]["base"]["por_curso"]:
            L.append(f"- {s}: " + "; ".join(f"{a} {v['por_curso'][s].get('bloco')}/{v['por_curso'][s].get('unidade')}/"
                                             f"{v['por_curso'][s].get('sub_primaria')}/{v['por_curso'][s].get('sub_aceita')}"
                                             for a, v in C["placar"].items()))
    else:
        L += ["## C. ABORTADO", "", str(C.get("abortado"))]
    L += ["", f"Base x referencia 87: {len(C.get('base_x_referencia87', []))} mudancas por ID. Congelado: "
          + json.dumps(C.get("congelado"), ensure_ascii=False), "", "Mudancas de decisao sem gold:", ""]
    for k, lst in (C.get("mudancas_sem_gold") or {}).items():
        L.append(f"- {k}: {len(lst)}")
        for m in lst:
            L.append(f"  - {m['curso']} {m['eid']}: {m['de']} -> {m['para']}")
    L += ["", "Raizes do placar: demovidos no DP = " + json.dumps({s: [d['bloco'] for d in v] for s, v in C.get("demovidos_no_DP", {}).items()},
                                                                  ensure_ascii=False)
          + "; skip H = " + json.dumps(C.get("skip_H"), ensure_ascii=False), "",
          "## A. Tipos nos 8 cursos vivos (controle -> P1adj)", "", "| contagem | " + " | ".join(sorted(set().union(*A["totais"].values()))) + " |"]
    kinds = sorted(set().union(*A["totais"].values()))
    L.append("|---|" + "---|" * len(kinds))
    for k, v in A["totais"].items():
        L.append(f"| {k} | " + " | ".join(str(v.get(x, 0)) for x in kinds) + " |")
    L += ["", "Demovidos que voltam ao DP: " + json.dumps({s: v for s, v in A["demovidos_no_DP"].items() if v}, ensure_ascii=False),
          "", "Skip H (review de duvidas, nao alvo do prep-prova): " + json.dumps(A["skip_H"], ensure_ascii=False), "",
          "Linhas class com cauda entrega (informativo; regra (2) revista, nao aplicada): " + json.dumps(A["class_com_cauda_entrega_nao_alteradas"], ensure_ascii=False),
          "", "### Linhas cujo tipo (linha ou bloco) ou unidade do bloco muda, + alvos", "",
          "| curso | L | data | rotulo | Atividade | marc | linha atual | bloco vivo | bloco controle | linha P1adj | regra P1adj | bloco P1adj | unidade ctrl -> P1adj | caso |",
          "|" + "---|" * 14]
    for r in A["linhas"]:
        if r["muda_linha"] or r["muda_bloco"] or r["muda_unidade"] or r["caso"].startswith("alvo"):
            ov = " (override)" if r["override_vivo"] else ""
            L.append(f"| {r['curso']} | {r['linha']} | {r['data']} | {r['rotulo'][:60]} | {r['atividade']} | {r['marcador']} | "
                     f"{r['tipo_linha_atual']} | {r['bloco_vivo']}={r['tipo_bloco_vivo']}{ov} | {r['bloco_controle']}={r['tipo_bloco_controle']} | "
                     f"{r['tipo_linha_P1adj']} | {r['regra_P1adj']} | {r['bloco_P1adj']}={r['tipo_bloco_P1adj']} | "
                     f"{r['unit_controle']} -> {r['unit_P1adj']} | {r['caso']} |")
    L += ["", "## B. Segmentacao (8 cursos vivos)", ""]
    for s, g in rep["B"].items():
        L.append(f"- {s}: vivo x controle {len(g['vivo_x_controle']['grupos'])} grupos; controle x P1adj "
                 f"{g['controle_x_P1adj']['blocos_antes']} -> {g['controle_x_P1adj']['blocos_depois']}, {len(g['controle_x_P1adj']['grupos'])} grupos")
    L += ["", "## D. Obsoletos no src da dev", ""] + [f"- {d['arquivo']}:{d['linha']} `{d['simbolo']}` — {d['motivo']}" for d in rep["D"]]
    return "\n".join(L) + "\n"


def main():
    head = subprocess.run(["git", "-C", str(WT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    roots = [r for r, _ in W.perfis_vivos().values()] + list(RAIZES.values())
    antes = W.snapshot(roots)
    prereg = {"regras_rotulo": [(k, rx.pattern) for k, rx in W.REGRAS_ROTULO], "cauda_entrega": CAUDA_ENTREGA.pattern,
              "adjudicacoes": ["1 gold SO bloco-09 inalterado", "2 revista: oficina segue workshop", "3 revista: apresentacao = class",
                               "4 review demovida volta ao DP"],
              "H": "review com todas as linhas review vindas de office_hours>review nao e alvo do prep-prova",
              "aceite": "contra controle: 0 perda por ID em bloco/unidade/sub primaria/sub aceita; nenhum curso regride; segmentacao identica",
              "resolve_exam_prep_sha256": hashlib.sha256(PREP_SRC.encode()).hexdigest()}
    print("pre-registro", sha(prereg), "| head", head, flush=True)
    A, B = parte_ab()
    C = parte_c()
    rep = {"worktree": str(WT), "head": head, "sha256_preregistro": sha(prereg), "preregistro": prereg, "A": A, "B": B, "C": C,
           "D": parte_d(), "fallback_classify_sem_rows": sorted(set(W.FALLBACK_SEM_ROWS)),
           "src_fora_da_worktree": sorted(n for n, m in sys.modules.items() if (n == "src" or n.startswith("src."))
                                          and getattr(m, "__file__", None) and not Path(m.__file__).resolve().is_relative_to(WT))}
    rep["segundos"] = round(time.time() - T0)
    rep["sha256_resultado"] = sha({k: v for k, v in rep.items() if k != "segundos"})
    depois = W.snapshot(roots)
    rep["repos_intocados"] = {"sha256_antes": antes, "sha256_depois": depois, "iguais": antes == depois}
    OUT_JSON.write_text(json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    OUT_MD.write_text(md(rep), encoding="utf-8")
    print("SHA256 json", hashlib.sha256(OUT_JSON.read_bytes()).hexdigest(), "| src fora:", rep["src_fora_da_worktree"] or "nenhum")
    if C.get("placar"):
        print("placar", {a: (v["total"].get("bloco"), v["total"].get("unidade"), v["total"].get("sub_primaria"), v["total"].get("sub_aceita"))
                         for a, v in C["placar"].items()}, "| aceite", {a: v["passa"] for a, v in C["aceite"].items()})
    else:
        print("ABORTADO:", C.get("abortado"))
    print(f"TEMPO {rep['segundos']} s")
    assert antes == depois, "repo/raiz alterado"


if __name__ == "__main__":
    main()
