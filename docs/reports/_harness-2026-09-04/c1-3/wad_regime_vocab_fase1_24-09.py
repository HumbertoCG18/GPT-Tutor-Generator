"""W-AD (24/09): regime separado VOCAB, Fase 1 — sem rede e sem mudanca em src, sobre os pacotes congelados da regua v2.

Desenho e decisoes: docs/reports/2026-09-24-regime-vocab-desenho.md (Fase 1 autorizada pelo usuario em 24/09; sidecars
manuais em quarentena, so no braco VOCAB_ATUAL; VOCAB-limpo fica para depois). Gold so depois do congelamento dos bracos.

INJECAO (fiel ao produto, isolada da deriva de reconstrucao):
- Sidecars do produto (`../<Tutor>/course/.glossary_curation{,.llm}.json`) copiados e congelados por sha256 em
  `.frzero/wad_sidecars_24-09/<braco>/<Tutor>/course/` (+ manifest do pacote, que o carregador usa para filtrar secoes).
- Taxonomia do braco = taxonomia congelada + delta de aliases por topico, onde delta = (taxonomia reconstruida pelo
  produto com o sidecar do braco) - (reconstruida sem sidecar); reconstrucao por engine._build_rich_content_taxonomy
  com `repo.load_glossary_curation` apontado para o palco do braco.
- Timeline: unidade dos blocos-aula refeita pelo DP do produto (unit_matcher.assign_units_positional) com as unidades da
  taxonomia do braco; muda so onde o DP mudar e o bloco nao tiver unidade manual. Demais campos do bloco ficam congelados.
- Replays reais bloco -> unidade (replay_bloco_21-09 -> replay_unidade_21-09) com a timeline e a taxonomia do braco em
  memoria e o carregador do glossario no palco (o indice de unidade tambem le o glossario). Rede bloqueada no processo.
BRACOS: CRU (sem patch); VOCAB_ATUAL (LLM + manual); VOCAB_LLM (so LLM); CTRL_MAIOR (termos do LLM de cada topico movidos
para o topico da mesma unidade com mais materiais na decisao do CRU); CTRL_ALEAT_1/2/3 (termos do LLM de cada topico
movidos para um topico sorteado da mesma unidade, sementes 1, 2, 3).
MEDIDAS: bloco, unidade, subunidade primaria e aceita por curso; ganhos/perdas por ID contra CRU; precisao das decisoes
de subunidade alteradas; geracao (gold entre os candidatos da 1a passada com pontuacao >= 0,05 na unidade final) separada
da selecao; 1a passada x final.
ACEITE da Fase 1 (desenho §5): VOCAB_LLM supera CRU e os controles na subunidade primaria sem piorar bloco nem unidade.
Sem build, LLM, rede ou commit. Uso: python wad_regime_vocab_fase1_24-09.py [--reavaliar]
"""
import collections
import copy
import hashlib
import importlib.util
import json
import os
import random
import shutil
import socket
import sys
import time
from pathlib import Path
from types import SimpleNamespace

T0 = time.time()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
ORIG = DATA.parent
sys.path.insert(0, str(DATA))
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
OUT_JSON = HERE / "wad_regime_vocab_fase1_24-09.json"
PALCO = DATA / ".frzero/wad_sidecars_24-09"
CAP_WAD = DATA / ".frzero/wad_captura_bracos_24-09.json"
CAP_WZ2 = DATA / ".frzero/wz2_captura_base_23-09.json"
LLM, MANUAL = ".glossary_curation.llm.json", ".glossary_curation.json"
BRACOS = ("CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3")
TENTATIVAS_REDE = []


def _sem_rede(*a, **k):
    TENTATIVAS_REDE.append(1)
    raise RuntimeError("REDE BLOQUEADA (W-AD)")


socket.socket.connect = _sem_rede
socket.create_connection = _sem_rede

from src.builder import engine  # noqa: E402
from src.builder.artifacts import repo as REPO  # noqa: E402
from src.builder.routing.motor import context as MCTX  # noqa: E402
from src.builder.timeline import unit_matcher as UM  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def sha_arquivo(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------------- sidecars por braco
def chave_do_topico(t):
    return f"{str(t.get('code') or '').strip()} {str(t.get('label') or '').strip()}".strip()


def topicos_por_chave(tax):
    out = {}
    for u in tax.get("units") or []:
        for t in u.get("topics") or []:
            out[REPO._glossary_curation_key(chave_do_topico(t))] = (str(u.get("slug") or ""), t)
    return out


def transforma(llm, tax, destino_de):
    """Move os sinonimos de cada chave do sidecar LLM para o topico destino (mesma unidade); metadados preservados."""
    por_chave = topicos_por_chave(tax)
    out = {k: v for k, v in llm.items() if k.startswith("_")}
    for k in sorted(k for k in llm if not k.startswith("_")):
        alvo = por_chave.get(REPO._glossary_curation_key(k))
        syn = (llm[k] or {}).get("synonyms") if isinstance(llm[k], dict) else llm[k]
        if not alvo or not syn:
            out.setdefault(k, {"synonyms": []})["synonyms"] = list(syn or [])
            continue
        u, t = alvo
        novo = destino_de(k, u, t)
        dst = out.setdefault(chave_do_topico(novo), {"synonyms": []})
        dst["synonyms"] = list(dict.fromkeys(dst["synonyms"] + list(syn)))
    return out


def destino_maior(unid, contagem):
    """Topico da mesma unidade com mais materiais na decisao do CRU (sem gold); empate -> ordem da taxonomia."""
    def destino(_k, u, t):
        tops = unid.get(u) or [t]
        return max(tops, key=lambda x: (contagem[(u, str(x.get("slug") or ""))], -tops.index(x)))
    return destino


def destino_aleatorio(unid, seed):
    rng = random.Random(seed)
    return lambda _k, u, t: rng.choice(unid.get(u) or [t])


def monta_palcos(nomes, raizes, base):
    prov = {}
    for sig, nome in nomes.items():
        root, tutor = raizes[sig], ORIG / nome / "course"
        tax = read(root / "course/.content_taxonomy.json")
        llm = read(tutor / LLM) if (tutor / LLM).is_file() else {}
        manual = read(tutor / MANUAL) if (tutor / MANUAL).is_file() else None
        unid = {str(u.get("slug") or ""): [t for t in u.get("topics") or []] for u in tax.get("units") or []}
        contagem = collections.Counter(
            (r["final"].get("unidade"), r["final"].get("sub")) for r in base[sig].values()
            if isinstance(r, dict) and r.get("final") and r["final"].get("sub"))
        conteudo = {"VOCAB_ATUAL": (llm, manual), "VOCAB_LLM": (llm, None),
                    "CTRL_MAIOR": (transforma(llm, tax, destino_maior(unid, contagem)), None)}
        for s in (1, 2, 3):
            conteudo[f"CTRL_ALEAT_{s}"] = (transforma(llm, tax, destino_aleatorio(unid, s)), None)
        for braco, (l, m) in conteudo.items():
            d = PALCO / braco / nome
            (d / "course").mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / "manifest.json", d / "manifest.json")
            for arq, dados in ((LLM, l), (MANUAL, m)):
                alvo = d / "course" / arq
                if dados:
                    alvo.write_text(json.dumps(dados, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
                elif alvo.exists():
                    alvo.unlink()
            prov.setdefault(braco, {})[sig] = {arq: sha_arquivo(d / "course" / arq)[:16]
                                               for arq in (LLM, MANUAL) if (d / "course" / arq).exists()}
        prov.setdefault("fonte_produto", {})[sig] = {arq: sha_arquivo(tutor / arq)[:16] for arq in (LLM, MANUAL)
                                                     if (tutor / arq).is_file()}
    return prov


# ------------------------------------------------------------------------------------------- taxonomia e timeline
def reconstroi(root, palco):
    man = read(root / "manifest.json")
    prof = SimpleNamespace(**read(root / "_inputs_15-09.json")["profile_input"])
    orig = REPO.load_glossary_curation
    REPO.load_glossary_curation = (lambda root_dir: orig(palco)) if palco else (lambda root_dir: {})
    try:
        return engine._build_rich_content_taxonomy(root, {"_repo_root": root, "course_name": prof.name}, prof,
                                                   entries=man["entries"])
    finally:
        REPO.load_glossary_curation = orig


def aliases(tax):
    return {(str(u.get("slug") or ""), str(t.get("slug") or "")): list(t.get("aliases") or [])
            for u in tax.get("units") or [] for t in u.get("topics") or []}


def taxonomia_do_braco(root, palco, sem):
    congelada = read(root / "course/.content_taxonomy.json")
    com = aliases(reconstroi(root, palco))
    novo, delta = copy.deepcopy(congelada), {"adicionados": 0, "removidos": 0}
    for u in novo.get("units") or []:
        for t in u.get("topics") or []:
            k = (str(u.get("slug") or ""), str(t.get("slug") or ""))
            add = [a for a in com.get(k, []) if a not in sem.get(k, [])]
            rem = {a for a in sem.get(k, []) if a not in com.get(k, [])}
            atual = [a for a in (t.get("aliases") or []) if a not in rem]
            t["aliases"] = atual + [a for a in add if a not in atual]
            delta["adicionados"] += len(add)
            delta["removidos"] += len(rem)
    return novo, delta


def timeline_do_braco(root, tax):
    tl = read(root / "course/.timeline_index.json")
    blocos = copy.deepcopy(tl["blocks"])
    cand = [b for b in blocos if str(b.get("auto_unit_slug") or "")]
    units_c = read(root / "course/.content_taxonomy.json").get("units") or []
    antes = [s for s, _ in UM.assign_units_positional(cand, units_c)] if cand else []
    depois = [s for s, _ in UM.assign_units_positional(cand, tax.get("units") or [])] if cand else []
    mud = []
    for b, a, d in zip(cand, antes or [None] * len(cand), depois or [None] * len(cand), strict=True):
        if a and d and a != d:
            manual = str(b.get("unit_slug") or "") != str(b.get("auto_unit_slug") or "")
            mud.append({"bloco": b.get("id"), "de": a, "para": d, "manual": manual})
            if not manual:
                b["unit_slug"] = b["auto_unit_slug"] = d
    return {**tl, "blocks": blocos}, mud, (not cand or [s for s in antes] == [str(b.get("auto_unit_slug")) for b in cand])


# ------------------------------------------------------------------------------------------- replay por braco
def rodar(braco, raizes, rb, ru, compare, injecao):
    cap = {}
    orig_art, orig_read, orig_tax = MCTX.load_repo_artifact, ru.read, ru.load_internal_content_taxonomy
    orig_gloss, orig_sub = REPO.load_glossary_curation, ru.auto_sub
    ctx = {"sig": None}

    def sub_wrapper(entry, taxonomy, markdown_text, winning_unit_slug="", **kw):
        m = orig_sub(entry, taxonomy, markdown_text, winning_unit_slug=winning_unit_slug, **kw)
        rec = cap[ctx["sig"]].setdefault(str(entry["id"]), {})
        if "sub_1a" not in rec:
            sinais = ru.collect_entry_unit_signals(entry, markdown_text)
            u = str(winning_unit_slug or "")
            cands = {}
            for t in ru._iter_content_taxonomy_topics(taxonomy) or []:
                if u and str(t.get("unit_slug") or "") != u:
                    continue
                s = float(ru._score_entry_against_taxonomy_topic(sinais, t))
                if s >= 0.05:
                    cands[str(t.get("topic_slug") or "")] = round(s, 4)
            rec["sub_1a"] = str(m.topic_slug or "")
            rec["candidatos"] = cands
        return m

    try:
        ru.auto_sub = sub_wrapper
        for sig, root in raizes.items():
            ctx["sig"] = sig
            cap[sig] = {}
            inj = injecao.get(sig)
            if inj:
                tl, tax, palco = inj["timeline"], inj["taxonomia"], inj["palco"]

                def art(repo, rel, _root=root, _tl=tl, _tax=tax):
                    if Path(repo).resolve() == _root.resolve():
                        if rel == "course/.timeline_index.json":
                            return copy.deepcopy(_tl)
                        if rel == "course/.content_taxonomy.json":
                            return copy.deepcopy(_tax)
                    return orig_art(repo, rel)
                MCTX.load_repo_artifact = art
                REPO.load_glossary_curation = lambda root_dir, _p=palco: orig_gloss(_p)
                ru.load_internal_content_taxonomy = lambda r, _tax=tax: copy.deepcopy(_tax)
            try:
                saved, bloco_novo, _, _ = rb.replay(root)
                feed = [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]

                def patched(path, _feed=feed, _inj=inj):
                    if _inj and Path(path).name == ".timeline_index.json":
                        return copy.deepcopy(_inj["timeline"])
                    data = orig_read(path)
                    if Path(path).name == "manifest.json":
                        data = {**data, "entries": _feed}
                    return data

                ru.read = patched
                _, novo, _ = ru.replay(root)
            finally:
                ru.read, MCTX.load_repo_artifact = orig_read, orig_art
                ru.load_internal_content_taxonomy, REPO.load_glossary_curation = orig_tax, orig_gloss
            for eid, e in novo.items():
                cap[sig].setdefault(eid, {})["final"] = {
                    "bloco": compare.predictions(root, e)[0], "unidade": str(e.get("computed_unit_slug") or ""),
                    "sub": str(e.get("computed_subunit_slug") or "")}
            print("  braco", braco, sig, len(novo), round(time.time() - T0), "s", flush=True)
    finally:
        ru.auto_sub = orig_sub
    return cap


# ------------------------------------------------------------------------------------------- avaliacao
def avaliar(estado, nomes, CAP):
    R = {"placar": {}, "mudancas": {}, "geracao_selecao": {}, "primeira_passada": {}}
    flags = {}
    for b in BRACOS:
        R["placar"][b], flags[b] = {}, {}
        gs_c = collections.Counter()
        pp = collections.Counter()
        for sig, v in estado.items():
            gb, gu, gs, gsp = v["golds"]
            c = collections.Counter()
            for row in v["rows"]:
                gid, eid = row["entry_id"], v["eid_de"].get(row["entry_id"])
                rec = CAP[b][sig].get(eid) if eid else None
                f = (rec or {}).get("final")
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
                    cands = (rec or {}).get("candidatos") or {}
                    gerado = any(s in gsp[gid] for s in cands)
                    gs_c["gold_gerado"] += gerado
                    gs_c["gerado_e_escolhido"] += gerado and ok["sub_primaria"]
                    pp["1a_certa"] += (rec or {}).get("sub_1a", "") in gsp[gid]
                    pp["final_certa"] += ok["sub_primaria"]
                flags[b][(sig, gid)] = {**ok, "sub": (f or {}).get("sub", "")}
            R["placar"][b][sig] = dict(c)
        tot = collections.Counter()
        for c in R["placar"][b].values():
            tot.update(c)
        R["placar"][b]["TOTAL"] = dict(tot)
        R["geracao_selecao"][b] = dict(gs_c)
        R["primeira_passada"][b] = dict(pp)
    for b in BRACOS[1:]:
        g, p = collections.defaultdict(list), collections.defaultdict(list)
        alt = []
        for k, fb in flags["CRU"].items():
            fa = flags[b][k]
            for eixo in ("bloco", "unidade", "sub_primaria", "sub_aceita"):
                if eixo not in fb:
                    continue
                if fa.get(eixo) and not fb[eixo]:
                    g[eixo].append(f"{k[0]}|{k[1]}")
                if fb[eixo] and not fa.get(eixo):
                    p[eixo].append(f"{k[0]}|{k[1]}")
            if "sub_primaria" in fb and fa["sub"] != fb["sub"]:
                alt.append(fa["sub_primaria"])
        regride = {e: [s for s in nomes if R["placar"][b][s].get(e, 0) < R["placar"]["CRU"][s].get(e, 0)]
                   for e in ("bloco", "unidade", "sub_primaria", "sub_aceita")}
        R["mudancas"][b] = {"ganhos": {k: len(v) for k, v in g.items()}, "perdas": {k: len(v) for k, v in p.items()},
                            "ids_ganhos_sub": sorted(g["sub_primaria"]), "ids_perdas_sub": sorted(p["sub_primaria"]),
                            "perdas_bloco_unidade": sorted(p["bloco"] + p["unidade"]),
                            "sub_alteradas": len(alt), "precisao_sub_alteradas": round(sum(alt) / len(alt), 3) if alt else None,
                            "cursos_que_regridem": regride}
    t = {b: R["placar"][b]["TOTAL"] for b in BRACOS}
    ctrl = max(t[b].get("sub_primaria", 0) for b in BRACOS if b.startswith("CTRL"))
    R["aceite_fase1"] = {
        "vocab_llm_supera_cru": t["VOCAB_LLM"].get("sub_primaria", 0) > t["CRU"].get("sub_primaria", 0),
        "vocab_llm_supera_melhor_controle": t["VOCAB_LLM"].get("sub_primaria", 0) > ctrl,
        "bloco_nao_piora": t["VOCAB_LLM"].get("bloco", 0) >= t["CRU"].get("bloco", 0),
        "unidade_nao_piora": t["VOCAB_LLM"].get("unidade", 0) >= t["CRU"].get("unidade", 0)}
    R["aceite_fase1"]["aprovado"] = all(R["aceite_fase1"].values())
    return R


# ------------------------------------------------------------------------------------------- main
def main():
    reavaliar = "--reavaliar" in sys.argv
    if not reavaliar:
        assert not OUT_JSON.exists(), "preservar evidencia existente"
    compare = load("wad_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    wx = load("wad_wx", HERE / "wx_regua_corrigida_22-09.py")
    rb = load("wad_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wad_ru", HERE / "replay_unidade_21-09.py")
    wz = load("wad_wz", HERE / "wz_bloco_cobertura_22-09.py")
    nomes = mede.NOMES
    raizes = {s: wz.root_de(s, nomes) for s in nomes}
    cz = read(CAP_WZ2)
    assert cz["sha256_base"].startswith("f941ac33"), "base congelada do W-Z2 inesperada"
    sha_decl = sha({"doc": __doc__})
    print("DECLARACAO", sha_decl[:16], flush=True)

    prov = monta_palcos(nomes, raizes, cz["base"])
    injecao, info = {}, {"delta_aliases": {}, "blocos_que_mudam": {}, "dp_cru_fiel": {}}
    for sig, root in raizes.items():
        sem = aliases(reconstroi(root, None))
        for braco in BRACOS[1:]:
            tax, delta = taxonomia_do_braco(root, PALCO / braco / nomes[sig], sem)
            tl, mud, fiel = timeline_do_braco(root, tax)
            injecao.setdefault(braco, {})[sig] = {"taxonomia": tax, "timeline": tl, "palco": PALCO / braco / nomes[sig]}
            info["delta_aliases"].setdefault(braco, {})[sig] = delta
            info["blocos_que_mudam"].setdefault(braco, {})[sig] = mud
            info["dp_cru_fiel"][sig] = fiel
    print("delta de aliases:", {b: {s: d["adicionados"] for s, d in v.items()} for b, v in info["delta_aliases"].items()},
          "| blocos que mudam:", {b: sum(len(x) for x in v.values()) for b, v in info["blocos_que_mudam"].items()},
          "| DP do CRU fiel:", info["dp_cru_fiel"], flush=True)

    if reavaliar:
        cw = read(CAP_WAD)
        assert cw["sha256_declaracao"] == sha_decl
        CAP, sha_bracos = {b: cw[b] for b in BRACOS}, cw["sha256_bracos"]
    else:
        CAP = {b: rodar(b, raizes, rb, ru, compare, injecao.get(b, {})) for b in BRACOS}
        sha_bracos = sha(CAP)
        CAP_WAD.write_text(json.dumps({"sha256_declaracao": sha_decl, "sha256_bracos": sha_bracos, **CAP},
                                      ensure_ascii=False), encoding="utf-8")
    print("CONGELAMENTO bracos", sha_bracos[:16], "| tentativas de rede:", len(TENTATIVAS_REDE), flush=True)

    fid = collections.Counter()
    for sig in nomes:
        for eid, r in cz["base"][sig].items():
            if isinstance(r, dict) and r.get("final"):
                a = (CAP["CRU"][sig].get(eid) or {}).get("final") or {}
                for eixo in ("bloco", "unidade", "sub"):
                    fid[f"{eixo}_{'igual' if a.get(eixo) == r['final'][eixo] else 'diverge'}"] += 1

    # ================================================================ GOLD entra aqui
    estado = {sig: {"root": raizes[sig], "saved": {str(e["id"]): e for e in read(raizes[sig] / "manifest.json")["entries"]}}
              for sig in nomes}
    wz.preparar_avaliacao(estado, compare, mede, wx)
    R = avaliar(estado, nomes, CAP)
    R.update({"escopo": __doc__, "sha256_declaracao": sha_decl, "sha256_bracos": sha_bracos, "proveniencia_sidecars": prov,
              "injecao": info, "tentativas_de_rede": len(TENTATIVAS_REDE),
              "fidelidade_cru_vs_wz2": dict(fid), "segundos": round(time.time() - T0, 1)})
    OUT_JSON.write_text(json.dumps(R, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    for b in BRACOS:
        x = R["placar"][b]["TOTAL"]
        print(f"{b:13} bloco {x.get('bloco')}/{x.get('bloco_n')} unidade {x.get('unidade')}/{x.get('unidade_n')} "
              f"sub {x.get('sub_primaria')}/{x.get('sub_n')} aceita {x.get('sub_aceita')} | gerado "
              f"{R['geracao_selecao'][b].get('gold_gerado')} escolhido {R['geracao_selecao'][b].get('gerado_e_escolhido')}",
              flush=True)
    print("aceite fase 1:", R["aceite_fase1"], "| fidelidade CRU x W-Z2:", dict(fid))
    print("OK", OUT_JSON.name, hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()[:16], R["segundos"], "s", flush=True)


if __name__ == "__main__":
    main()
