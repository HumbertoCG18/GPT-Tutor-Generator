"""Piloto KE (23/09): execução local dos braços e avaliação. Regras em piloto_ke_declaracao_23-09.md.

  --braco base   replay da base v2 (harness do W-Z2, modo base) sem KE; tem de reproduzir por ID a captura congelada
  --braco ke     mesmo replay; a taxonomia com aliases KE (tabela congelada) vai SÓ para o mapeador de subtópico
  --congelar     sha256 das duas capturas, da tabela, do léxico, da declaração e dos scripts (antes do gold)
  --avaliar      confere o congelamento e só então lê o gold: placar, IDs, candidatos, abstenções, precisão
Cada braço roda em processo próprio (tempo e pico de memória limpos), com tripwires de rede e do cliente Gemini.
Candidatos (1ª passada) = tópicos da unidade vencedora com score exato > 0 (`_score_entry_against_taxonomy_topic`).
"""
import collections
import copy
import hashlib
import json
import socket
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
DIR = DATA / ".frzero/ke_piloto_23-09"
ALI = DIR / "aliases_ke_23-09.json"
LEX = DIR / "lexico_conceptnet_5.7.0_en_pt.json"
CAPS = {b: DIR / f"captura_{b}_23-09.json" for b in ("base", "ke")}
CONG = HERE / "piloto_ke_congelamento_23-09.json"
OUT = HERE / "piloto_ke_resultado_23-09.json"
DECL = HERE / "piloto_ke_declaracao_23-09.md"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
TENTATIVAS = []


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def carregar():
    import importlib.util
    spec = importlib.util.spec_from_file_location("wz2", HERE / "wz2_diagnostico_causal_23-09.py")
    wz2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wz2)
    m = {"wz2": wz2}
    for k, f in (("compare", "compara_herancas_15-09.py"), ("rb", "replay_bloco_21-09.py"),
                 ("ru", "replay_unidade_21-09.py"), ("wz", "wz_bloco_cobertura_22-09.py"),
                 ("wx", "wx_regua_corrigida_22-09.py")):
        m[k] = wz2.load(f"p_{k}", HERE / f)
    return m


def tripwires():
    def bloqueado(*a, **k):
        TENTATIVAS.append(repr(a[:2])[:120])
        raise OSError("rede bloqueada no piloto")
    socket.socket.connect = bloqueado
    socket.socket.connect_ex = bloqueado
    socket.create_connection = bloqueado
    socket.getaddrinfo = bloqueado
    import src.builder.runtime.gemini_client as gc
    gc.get_gemini_client = bloqueado
    gc.GeminiClient.__init__ = bloqueado


def estado_bloco(m):
    nomes = m["compare"].mede.NOMES
    raizes = {sig: m["wz"].root_de(sig, nomes) for sig in nomes}
    estado = {}
    for sig in nomes:
        saved, bloco_novo, decisoes, _ = m["rb"].replay(raizes[sig])
        estado[sig] = {"root": raizes[sig], "saved": saved, "decisoes": decisoes,
                       "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
    return estado


def braco(nome):
    import psutil
    m = carregar()
    wz2, ru = m["wz2"], m["ru"]
    tripwires()
    aliases = json.loads(ALI.read_text(encoding="utf-8")) if nome == "ke" else {}
    t0 = time.time()
    estado = estado_bloco(m)
    cand, cache = collections.defaultdict(dict), {}
    orig_sub = ru.auto_sub

    def estender(sig, tax):
        if id(tax) not in cache:
            t2 = copy.deepcopy(tax)
            for u in t2.get("units") or []:
                for t in u.get("topics") or []:
                    add = [a["alias"] for a in aliases.get(sig, {}).get(f"{u.get('slug')}|{t.get('slug')}", [])]
                    atuais = list(t.get("aliases") or [])
                    t["aliases"] = atuais + [a for a in add if a not in atuais]
            cache[id(tax)] = (tax, t2)
        return cache[id(tax)][1]

    def sub_piloto(entry, taxonomy, markdown_text, winning_unit_slug="", **kw):
        sig = wz2.CTX["sig"]
        tax = estender(sig, taxonomy) if aliases else taxonomy
        eid = str(entry.get("id"))
        if wz2.CTX["fase"] == "1a" and eid not in cand[sig]:
            sinais = ru.collect_entry_unit_signals(entry, markdown_text)
            cs = []
            for t in ru._iter_content_taxonomy_topics(tax):
                if winning_unit_slug and str(t.get("unit_slug") or "") != str(winning_unit_slug):
                    continue
                s = float(ru._score_entry_against_taxonomy_topic(sinais, t))
                if s > 0:
                    cs.append([str(t.get("topic_slug") or ""), round(s, 4)])
            cand[sig][eid] = {"unidade": str(winning_unit_slug or ""), "candidatos": sorted(cs)}
        return orig_sub(entry, tax, markdown_text, winning_unit_slug=winning_unit_slug, **kw)

    ru.auto_sub = sub_piloto
    try:
        cap = wz2.rodar(nome, estado, ru, m["compare"], pontuar=False)
    finally:
        ru.auto_sub = orig_sub
    mi = psutil.Process().memory_info()
    finais = {sig: {eid: r["final"] for eid, r in v.items() if "final" in r} for sig, v in cap.items()}
    dados = {"braco": nome, "finais": finais, "candidatos": cand, "tempo_s": round(time.time() - t0, 1),
             "pico_memoria_mb": round(getattr(mi, "peak_wset", mi.rss) / 2 ** 20, 1),
             "tentativas_rede": TENTATIVAS, "aliases_sha256": sha_file(ALI) if nome == "ke" else None}
    assert not TENTATIVAS, TENTATIVAS
    if nome == "base":
        cong = wz2.read(wz2.CAP_BASE)
        assert cong["sha256_base"].startswith("f941ac33")
        div = [[s, i] for s in finais for i in set(finais[s]) | {k for k, r in cong["base"][s].items() if "final" in r}
               if finais[s].get(i) != (cong["base"][s].get(i) or {}).get("final")]
        dados["fidelidade_captura_congelada"] = "igual" if not div else div
        assert not div, div[:5]
    CAPS[nome].write_text(json.dumps(dados, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(nome, "ok", dados["tempo_s"], "s", dados["pico_memoria_mb"], "MB", flush=True)


def congelar():
    cong = {k: sha_file(p) for k, p in (("captura_base", CAPS["base"]), ("captura_ke", CAPS["ke"]), ("aliases", ALI),
                                         ("lexico", LEX), ("declaracao", DECL), ("script_execucao", Path(__file__)),
                                         ("script_lexico", HERE / "piloto_ke_lexico_23-09.py"))}
    cong["momento"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    CONG.write_text(json.dumps(cong, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(cong, indent=1))


def avaliar():
    cong = json.loads(CONG.read_text(encoding="utf-8"))
    for k in ("captura_base", "captura_ke", "aliases"):
        p = {"captura_base": CAPS["base"], "captura_ke": CAPS["ke"], "aliases": ALI}[k]
        assert sha_file(p) == cong[k], f"{k} mudou depois do congelamento"
    m = carregar()
    wz2, ru, RA = m["wz2"], m["ru"], m["ru"].RA
    B = json.loads(CAPS["base"].read_text(encoding="utf-8"))
    K = json.loads(CAPS["ke"].read_text(encoding="utf-8"))
    aliases = json.loads(ALI.read_text(encoding="utf-8"))
    estado = estado_bloco(m)
    # ======================= gold entra aqui
    m["wz"].preparar_avaliacao(estado, m["compare"], m["compare"].mede, m["wx"])
    saidas = lambda X: {s: {e: {k: f.get(k) for k in ("bloco", "unidade", "sub")} for e, f in v.items()}  # noqa: E731
                        for s, v in X["finais"].items()}
    placar_b, _ = m["wz"].avaliar(estado, saidas(B))
    placar_k, _ = m["wz"].avaliar(estado, saidas(K))
    tot = lambda pc: {k: sum(c.get(k, 0) for c in pc.values()) for k in  # noqa: E731
                      ("bloco", "bloco_n", "unidade", "unidade_n", "sub_primaria", "sub_aceita", "sub_n")}
    cg5 = {"instanciamento", "transformacoesgl", "transformacoesgeometricas",
           "pagina-com-videos-sobre-instanciamento", "animacao-v2"}
    preserv = {"bloco_diverge": [], "unidade_diverge": []}
    for s in B["finais"]:
        for e in set(B["finais"][s]) | set(K["finais"][s]):
            fb, fk = B["finais"][s].get(e) or {}, K["finais"][s].get(e) or {}
            if fb.get("bloco") != fk.get("bloco"):
                preserv["bloco_diverge"].append([s, e])
            if fb.get("unidade") != fk.get("unidade"):
                preserv["unidade_diverge"].append([s, e])
    por_curso, ids = {}, []
    for sig, v in estado.items():
        gsp = v["golds"][3]
        c = collections.Counter()
        md_cache = {str(e["id"]): e for e in v["feed"]}
        for row in v["rows"]:
            if row["sub_primario"] == "":
                continue
            gid = row["entry_id"]
            eid = v["eid_de"].get(gid)
            g = set(gsp[gid])
            fb = (B["finais"][sig].get(eid) or {}) if eid else {}
            fk = (K["finais"][sig].get(eid) or {}) if eid else {}
            sb, sk = fb.get("sub", ""), fk.get("sub", "")
            ob, ok = sb in g, sk in g
            cb = {t for t, _ in (B["candidatos"].get(sig, {}).get(eid) or {}).get("candidatos", [])} if eid else set()
            ck = {t for t, _ in (K["candidatos"].get(sig, {}).get(eid) or {}).get("candidatos", [])} if eid else set()
            c["n"] += 1
            c["acerto_base"] += ob
            c["acerto_ke"] += ok
            c["gold_em_cand_base"] += bool(g & cb)
            c["gold_em_cand_ke"] += bool(g & ck)
            c["gold_so_em_cand_ke"] += bool(g & ck) and not (g & cb)
            c["cand_base_total"] += len(cb)
            c["cand_ke_total"] += len(ck)
            c["ganhou_2+_candidatos"] += len(ck - cb) >= 2
            c["ke_gold_em_cand_e_escolhido"] += bool(g & ck) and ok
            c["base_gold_em_cand_e_escolhido"] += bool(g & cb) and ob
            c["base_gold_em_cand_nao_escolhido"] += bool(g & cb) and not ob
            c["acerto_sem_gold_em_cand_base"] += ob and not (g & cb)
            c["acerto_sem_gold_em_cand_ke"] += ok and not (g & ck)
            c["ke_gold_em_cand_nao_escolhido"] += bool(g & ck) and not ok
            if sb != sk:
                efeito = "ganho" if ok and not ob else "perda" if ob and not ok else "erro_para_erro"
                c[efeito] += 1
                if sk:
                    c["alteradas_com_decisao"] += 1
                    c["alteradas_certas"] += ok
                if sb == "":
                    c["abstencao_para_certa" if ok else "abstencao_para_errada"] += 1
                if sk == "":
                    c["decisao_para_abstencao"] += 1
                entry = md_cache.get(eid) or {}
                txt = RA.normalize_match_text(f"{entry.get('title') or ''} "
                                              f"{ru._entry_markdown_text_for_file_map(v['root'], entry) or ''}")
                prov = [a for k2, als in aliases.get(sig, {}).items() if k2.endswith(f"|{sk}") for a in als
                        if RA._frase_no_texto(txt, a["alias"])]
                ids.append({"curso": sig, "eid": eid, "gold": sorted(g), "base": sb, "ke": sk, "efeito": efeito,
                            "gold_em_cand_base": bool(g & cb), "gold_em_cand_ke": bool(g & ck), "cg5": eid in cg5,
                            "aliases_ke_do_novo_topico_presentes": [{k3: a.get(k3) for k3 in
                                                                     ("alias", "via", "de", "lingua", "uri", "dataset",
                                                                      "frase_do_plano") if a.get(k3)} for a in prov]})
        por_curso[sig] = dict(c)
    total = collections.Counter()
    for c in por_curso.values():
        total.update(c)
    res = {"congelamento": cong, "fidelidade_base": B.get("fidelidade_captura_congelada"),
           "tempo_memoria": {b: {"tempo_s": X["tempo_s"], "pico_memoria_mb": X["pico_memoria_mb"],
                                 "tentativas_rede": len(X["tentativas_rede"])} for b, X in (("base", B), ("ke", K))},
           "placar": {"base": tot(placar_b), "ke": tot(placar_k)},
           "placar_por_curso": {"base": placar_b, "ke": placar_k},
           "preservacao": {k: len(v) for k, v in preserv.items()}, "preservacao_ids": preserv,
           "subunidade_por_curso": por_curso, "subunidade_total": dict(total), "mudancas_por_id": ids,
           "aliases_por_curso": {s: {"topicos_com_alias": len(v), "aliases": sum(len(x) for x in v.values())}
                                 for s, v in aliases.items()}}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("placar", "preservacao", "subunidade_total", "tempo_memoria")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if "--braco" in sys.argv:
        braco(sys.argv[sys.argv.index("--braco") + 1])
    elif "--congelar" in sys.argv:
        congelar()
    elif "--avaliar" in sys.argv:
        avaliar()
