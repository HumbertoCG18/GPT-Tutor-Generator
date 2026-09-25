"""W-AB (24/09): unidade - M1 (texto confiante vence o bloco do fallback antigo) e M2 (pares de termos do pacote nas
fronteiras sem sinal do DP), sobre a base atual. 0 mudanca em src/tests/regua/defaults/configuracao persistida.

Autorizacao: Gate 1 de medicao do usuario em 24/09 ("Medir os +5 mesmo assim"); estado em
.workflow/local/unidade-caminhos-20260924.md; estimativa previa em unidade_caminhos_24-09.json. Gold so depois do
congelamento dos bracos por sha256.

BRACOS (replay real replay_bloco_21-09 -> replay_unidade_21-09; patches em memoria, restaurados no finally):
- base_atual: sem patch. Conferida por ID contra a base congelada do W-Z2 (f941ac33); divergencia = mudanca de src
  desde 23/09, relatada; os bracos comparam contra a base_atual.
- M1: se o bloco temporal do material vem do fallback (sem temporal_block_id e resolve_effective_block.source == "auto")
  e a reconciliacao daria "reconciliada_do_bloco" (bloco com unidade propria vence texto discordante), a unidade gated
  do texto (nao ambigua, >= T.UNIT_TAG) vence: razao "texto-vence-fallback=<bloco>". Mesmo padrao da #48 (vizinho).
- M2: pares "A (B[, C])" do pacote do curso (titulos dos materiais, headings do markdown dos materiais, plano de ensino e
  ementa do profile_input). A = ate 4 palavras antes do parentese; B = cada item do parentese separado por virgula ou
  ponto e virgula; tokens pelo tokenizador do DP (unit_matcher._tokens); par so com os dois lados nao vazios e
  disjuntos. Aplicacao so nos blocos-aula com afinidade 0 em todas as unidades E em fronteira (classe e posicao do
  W-Z2, calculadas sem gold): se B esta contido nos tokens do bloco, acrescenta A; se A esta contido, acrescenta B.
  DP refeito com esses tokens; a unidade do bloco muda onde o DP mudar e o bloco nao tiver unidade manual. A timeline
  alterada alimenta o motor de bloco (usa unit_slug do bloco) e a fase de unidade.
- M1M2: os dois.
ACEITE (por braco, contra base_atual): saldo > 0 na unidade; 0 perda por ID em bloco, unidade, subunidade primaria e
aceita; nenhum curso regride em nenhum eixo; bloco identico por ID. Sem parametro livre -> sem LOCO.
Sem build, rede, LLM, commit. Uso: python wab_unidade_fallback_fronteiras_24-09.py [--reavaliar]
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
OUT_JSON = HERE / "wab_unidade_fallback_fronteiras_24-09.json"
CAP_WAB = DATA / ".frzero/wab_captura_bracos_24-09.json"
CAP_WZ2 = DATA / ".frzero/wz2_captura_base_23-09.json"
WZ2_JSON = HERE / "wz2_diagnostico_causal_23-09.json"
BRACOS = ("base_atual", "M1", "M2", "M1M2")
PAR_RE = re.compile(r"([^()\n]{1,120}?)\(([^()\n]{2,120})\)")
PALAVRA_RE = re.compile(r"[^\W\d_][\w-]*", re.UNICODE)

from src.builder.routing import file_map as FM  # noqa: E402
from src.builder.routing.motor import context as MCTX  # noqa: E402
from src.builder.timeline import unit_matcher as UM  # noqa: E402

CTX = {"fb": False}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------------------- M2: pares e DP
def textos_do_pacote(root, ru):
    manifest = read(root / "manifest.json")
    linhas = []
    for e in manifest["entries"]:
        titulo = str(e.get("title") or "")
        if titulo:
            linhas.append(("titulo", str(e["id"]), titulo))
        md = ru._entry_markdown_text_for_file_map(root, e) or ""
        for ln in md.splitlines():
            if ln.lstrip().startswith("#"):
                linhas.append(("heading", str(e["id"]), ln.lstrip("# ").strip()))
    prof = read(root / "_inputs_15-09.json").get("profile_input") or {}
    for campo in ("teaching_plan", "syllabus"):
        for ln in str(prof.get(campo) or "").splitlines():
            linhas.append((campo, "", ln))
    return linhas


def pares_do_pacote(linhas):
    pares = {}
    for fonte, eid, ln in linhas:
        for m in PAR_RE.finditer(ln):
            antes = PALAVRA_RE.findall(m.group(1))[-4:]
            a = frozenset(UM._tokens(" ".join(antes)))
            for item in re.split(r"[,;]", m.group(2)):
                b = frozenset(UM._tokens(item))
                if a and b and not (a & b):
                    pares.setdefault((a, b), []).append({"fonte": fonte, "material": eid, "linha": ln[:160]})
    return pares


def aumento_das_fronteiras(sig, blocos, pares, dp_wz2):
    alvo = {b["bloco"] for b in dp_wz2 if b["curso"] == sig and b["classe"] == "sem_sinal" and b["posicao"] == "fronteira"}
    extra, log = {}, []
    for b in blocos:
        bid = str(b.get("id") or "")
        if bid not in alvo:
            continue
        toks = UM._block_tokens(b)
        add = set()
        for (a, bb), prov in pares.items():
            if bb <= toks and not a <= toks:
                add |= a
                log.append({"bloco": bid, "via": sorted(bb), "acrescenta": sorted(a), "prov": prov[0]})
            if a <= toks and not bb <= toks:
                add |= bb
                log.append({"bloco": bid, "via": sorted(a), "acrescenta": sorted(bb), "prov": prov[0]})
        if add:
            extra[bid] = add
    return alvo, extra, log


def dp_com_extra(blocos, units, extra):
    cand = [b for b in blocos if str(b.get("auto_unit_slug") or "")]
    orig = UM._block_tokens

    def tokens(b):
        return orig(b) | extra.get(str(b.get("id") or ""), set())

    try:
        UM._block_tokens = tokens
        res = UM.assign_units_positional(cand, units)
    finally:
        UM._block_tokens = orig
    if not res:  # DP inaplicavel (sem sinal em lugar nenhum)
        return {}
    return {str(b.get("id") or ""): s for b, (s, _c) in zip(cand, res, strict=True)}


def timeline_m2(root, extra):
    tl = read(root / "course/.timeline_index.json")
    blocos = tl["blocks"]
    units = read(root / "course/.content_taxonomy.json").get("units", []) or []
    antes = dp_com_extra(blocos, units, {})
    depois = dp_com_extra(blocos, units, extra) if extra else antes
    mud = []
    novos = copy.deepcopy(blocos)
    for b in novos:
        bid = str(b.get("id") or "")
        if bid in depois and depois[bid] != antes.get(bid):
            manual = str(b.get("unit_slug") or "") != str(b.get("auto_unit_slug") or "")
            mud.append({"bloco": bid, "de": antes.get(bid), "para": depois[bid], "manual": manual})
            if not manual:
                b["unit_slug"] = b["auto_unit_slug"] = depois[bid]
    return {**tl, "blocks": novos}, mud


# ------------------------------------------------------------------------------------------- M1
def instalar_m1():
    orig_rt, orig_rec = FM.resolve_temporal_block, FM.reconcile_unit_with_block

    def rt(entry, blocks=None):
        CTX["fb"] = (not str(entry.get("temporal_block_id") or "").strip()
                     and FM.resolve_effective_block(entry, blocks).source == "auto")
        return orig_rt(entry, blocks)

    def rec(**kw):
        unidade, razoes, conflito = orig_rec(**kw)
        if CTX["fb"] and razoes and str(razoes[0]).startswith("reconciliada_do_bloco=") and kw["computed_unit_slug"]:
            return kw["computed_unit_slug"], [f"texto-vence-fallback={kw['computed_block_id']}"], conflito
        return unidade, razoes, conflito

    FM.resolve_temporal_block, FM.reconcile_unit_with_block = rt, rec
    return orig_rt, orig_rec


# ------------------------------------------------------------------------------------------- bracos
def rodar(braco, raizes, rb, ru, compare, timelines):
    usa_m1, usa_m2 = braco in ("M1", "M1M2"), braco in ("M2", "M1M2")
    cap = {}
    orig_art, orig_read = MCTX.load_repo_artifact, ru.read
    guard_m1 = instalar_m1() if usa_m1 else None
    try:
        for sig, root in raizes.items():
            tl = timelines[sig] if usa_m2 else None
            if tl is not None:
                def art(repo, rel, _root=root, _tl=tl):
                    if Path(repo).resolve() == _root.resolve() and rel == "course/.timeline_index.json":
                        return copy.deepcopy(_tl)
                    return orig_art(repo, rel)
                MCTX.load_repo_artifact = art
            try:
                saved, bloco_novo, _, _ = rb.replay(root)
            finally:
                MCTX.load_repo_artifact = orig_art
            feed = [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]

            def patched(path, _feed=feed, _tl=tl):
                data = orig_read(path)
                if Path(path).name == "manifest.json":
                    data = {**data, "entries": _feed}
                elif _tl is not None and Path(path).name == ".timeline_index.json":
                    data = copy.deepcopy(_tl)
                return data

            ru.read = patched
            try:
                _, novo, _ = ru.replay(root)
            finally:
                ru.read = orig_read
            cap[sig] = {eid: {"bloco": compare.predictions(root, e)[0], "unidade": str(e.get("computed_unit_slug") or ""),
                              "sub": str(e.get("computed_subunit_slug") or ""),
                              "razoes_unidade": [str(r) for r in e.get("unit_match_reasons") or []][-2:]}
                        for eid, e in novo.items()}
            cap[sig]["__saved__"] = {eid: True for eid in saved}
            print("  braco", braco, sig, len(novo), round(time.time() - T0), "s", flush=True)
    finally:
        if guard_m1:
            FM.resolve_temporal_block, FM.reconcile_unit_with_block = guard_m1
        MCTX.load_repo_artifact, ru.read = orig_art, orig_read
        CTX["fb"] = False
    return cap


# ------------------------------------------------------------------------------------------- avaliacao
def avaliar(estado, nomes, CAP, dp_wz2, mud_m2):
    R = {"placar": {}, "mudancas": {}, "aceite": {}, "alteradas_sem_gold": {}, "blocos_m2_contra_gold_por_bloco": []}
    flags = {}
    for b in BRACOS:
        R["placar"][b], flags[b] = {}, {}
        for sig, v in estado.items():
            gb, gu, gs, gsp = v["golds"]
            c = collections.Counter()
            for row in v["rows"]:
                gid, eid = row["entry_id"], v["eid_de"].get(row["entry_id"])
                f = CAP[b][sig].get(eid) if eid else None
                ok = {}
                if row["bloco"] != "":
                    c["bloco_n"] += 1
                    ok["bloco"] = bool(f and f["bloco"] == gb[gid])
                    c["bloco"] += ok["bloco"]
                if row["unidade"] != "":
                    c["unidade_n"] += 1
                    ok["unidade"] = bool(f and f["unidade"] in gu[gid])
                    c["unidade"] += ok["unidade"]
                if row["sub_primario"] != "":
                    c["sub_n"] += 1
                    ok["sub_primaria"] = bool(f and f["sub"] in gsp[gid])
                    ok["sub_aceita"] = bool(f and f["sub"] in gs[gid])
                    c["sub_primaria"] += ok["sub_primaria"]
                    c["sub_aceita"] += ok["sub_aceita"]
                flags[b][(sig, gid)] = ok
            R["placar"][b][sig] = dict(c)
        tot = collections.Counter()
        for c in R["placar"][b].values():
            tot.update(c)
        R["placar"][b]["TOTAL"] = dict(tot)
    gold_eids = {sig: {v["eid_de"].get(r["entry_id"]) for r in v["rows"]} for sig, v in estado.items()}
    for b in BRACOS[1:]:
        g, p = collections.defaultdict(list), collections.defaultdict(list)
        for k, fb in flags["base_atual"].items():
            fa = flags[b][k]
            for eixo in fb:
                if fa.get(eixo) and not fb[eixo]:
                    g[eixo].append(f"{k[0]}|{k[1]}")
                if fb[eixo] and not fa.get(eixo):
                    p[eixo].append(f"{k[0]}|{k[1]}")
        bloco_dif = [(sig, eid) for sig in nomes for eid, r in CAP[b][sig].items() if eid != "__saved__"
                     and r["bloco"] != (CAP["base_atual"][sig].get(eid) or {}).get("bloco")]
        regride = {eixo: [s for s in nomes if R["placar"][b][s].get(eixo, 0) < R["placar"]["base_atual"][s].get(eixo, 0)]
                   for eixo in ("bloco", "unidade", "sub_primaria", "sub_aceita")}
        R["mudancas"][b] = {"ganhos": {k: sorted(v) for k, v in g.items()}, "perdas": {k: sorted(v) for k, v in p.items()},
                            "saldo_unidade": len(g["unidade"]) - len(p["unidade"]), "bloco_divergente_por_id": bloco_dif[:20],
                            "n_bloco_divergente": len(bloco_dif), "cursos_que_regridem": regride}
        R["alteradas_sem_gold"][b] = sorted(
            f"{sig}|{eid}" for sig in nomes for eid, r in CAP[b][sig].items()
            if eid != "__saved__" and eid not in gold_eids[sig]
            and (r["unidade"], r["sub"]) != ((CAP["base_atual"][sig].get(eid) or {}).get("unidade"),
                                            (CAP["base_atual"][sig].get(eid) or {}).get("sub")))
        R["aceite"][b] = {"saldo_positivo": R["mudancas"][b]["saldo_unidade"] > 0,
                          "zero_perda": not any(p.values()),
                          "nenhum_curso_regride": not any(regride.values()),
                          "bloco_identico": not bloco_dif}
        R["aceite"][b]["aprovado"] = all(R["aceite"][b].values())
    gold_bloco = {(x["curso"], x["bloco"]): x["gold_bloco"] for x in dp_wz2 if x.get("gold_bloco")}
    for sig, lista in mud_m2.items():
        for m in lista:
            gb = gold_bloco.get((sig, m["bloco"]))
            R["blocos_m2_contra_gold_por_bloco"].append({**m, "curso": sig, "gold_bloco": gb or "",
                                                         "antes_certo": gb == m["de"] if gb else None,
                                                         "depois_certo": gb == m["para"] if gb else None})
    return R


# ------------------------------------------------------------------------------------------- main
def main():
    reavaliar = "--reavaliar" in sys.argv
    if not reavaliar:
        assert not OUT_JSON.exists(), "preservar evidencia existente"
    compare = load("wab_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    wx = load("wab_wx", HERE / "wx_regua_corrigida_22-09.py")
    rb = load("wab_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wab_ru", HERE / "replay_unidade_21-09.py")
    wz = load("wab_wz", HERE / "wz_bloco_cobertura_22-09.py")
    nomes = mede.NOMES
    raizes = {s: wz.root_de(s, nomes) for s in nomes}
    dp_wz2 = read(WZ2_JSON)["dp_blocos"]
    sha_decl = sha({"doc": __doc__, "par_re": PAR_RE.pattern})
    print("DECLARACAO", sha_decl[:16], flush=True)

    # M2 (sem gold): pares, aumento das fronteiras, DP refeito
    m2 = {"pares_por_curso": {}, "fronteiras_alvo": {}, "aumentos": {}, "mudancas_de_bloco": {}}
    timelines, mud_m2 = {}, {}
    for sig, root in raizes.items():
        pares = pares_do_pacote(textos_do_pacote(root, ru))
        tl = read(root / "course/.timeline_index.json")
        alvo, extra, log = aumento_das_fronteiras(sig, tl["blocks"], pares, dp_wz2)
        timelines[sig], mud_m2[sig] = timeline_m2(root, extra)
        m2["pares_por_curso"][sig] = len(pares)
        m2["fronteiras_alvo"][sig] = sorted(alvo)
        m2["aumentos"][sig] = log
        m2["mudancas_de_bloco"][sig] = mud_m2[sig]
    print("M2 pares:", m2["pares_por_curso"], "| fronteiras-alvo:", {s: len(v) for s, v in m2["fronteiras_alvo"].items()},
          "| blocos com aumento:", {s: len({x["bloco"] for x in v}) for s, v in m2["aumentos"].items()},
          "| blocos que mudam:", {s: len(v) for s, v in mud_m2.items()}, flush=True)

    if reavaliar:
        cw = read(CAP_WAB)
        assert cw["sha256_declaracao"] == sha_decl
        CAP = {b: cw[b] for b in BRACOS}
        sha_bracos = cw["sha256_bracos"]
    else:
        CAP = {}
        for b in BRACOS:
            if b in ("M2", "M1M2") and not any(mud_m2.values()):
                CAP[b] = CAP["M1" if b == "M1M2" else "base_atual"]
                print("  braco", b, "= sem mudanca de bloco no M2; reaproveita", flush=True)
                continue
            CAP[b] = rodar(b, raizes, rb, ru, compare, timelines)
        sha_bracos = sha(CAP)
        CAP_WAB.write_text(json.dumps({"sha256_declaracao": sha_decl, "sha256_bracos": sha_bracos, **CAP},
                                      ensure_ascii=False), encoding="utf-8")
    print("CONGELAMENTO bracos", sha_bracos[:16], flush=True)

    # fidelidade da base_atual contra a base congelada do W-Z2 (sem gold)
    cz = read(CAP_WZ2)
    assert cz["sha256_base"].startswith("f941ac33"), "base congelada do W-Z2 inesperada"
    fid = collections.Counter()
    exemplos = []
    for sig in nomes:
        for eid, r in cz["base"][sig].items():
            if not isinstance(r, dict) or not r.get("final"):
                continue
            a = CAP["base_atual"][sig].get(eid)
            for eixo, ch in (("bloco", "bloco"), ("unidade", "unidade"), ("sub", "sub")):
                igual = bool(a) and a[ch] == r["final"][ch]
                fid[f"{eixo}_igual" if igual else f"{eixo}_diverge"] += 1
                if not igual and len(exemplos) < 15:
                    exemplos.append({"curso": sig, "material": eid, "eixo": eixo, "wz2": r["final"][ch], "atual": (a or {}).get(ch)})

    # ================================================================ GOLD entra aqui
    estado = {sig: {"root": raizes[sig], "saved": {str(e["id"]): e for e in read(raizes[sig] / "manifest.json")["entries"]}}
              for sig in nomes}
    wz.preparar_avaliacao(estado, compare, mede, wx)
    R = avaliar(estado, nomes, CAP, dp_wz2, mud_m2)
    R.update({"escopo": __doc__, "sha256_declaracao": sha_decl, "sha256_bracos": sha_bracos,
              "fidelidade_base_atual_vs_wz2": {"contagens": dict(fid), "exemplos": exemplos}, "m2": m2,
              "segundos": round(time.time() - T0, 1)})
    OUT_JSON.write_text(json.dumps(R, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    t = R["placar"]
    for b in BRACOS:
        x = t[b]["TOTAL"]
        print(b, "bloco", x.get("bloco"), "/", x.get("bloco_n"), "unidade", x.get("unidade"), "/", x.get("unidade_n"),
              "sub", x.get("sub_primaria"), "/", x.get("sub_n"), "aceita", x.get("sub_aceita"), flush=True)
    for b in BRACOS[1:]:
        print(b, "aceite", R["aceite"][b], "ganhos", {k: len(v) for k, v in R["mudancas"][b]["ganhos"].items()},
              "perdas", {k: len(v) for k, v in R["mudancas"][b]["perdas"].items()}, flush=True)
    print("fidelidade base_atual x W-Z2:", dict(fid))
    print("OK", OUT_JSON.name, hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()[:16], R["segundos"], "s", flush=True)


if __name__ == "__main__":
    main()
