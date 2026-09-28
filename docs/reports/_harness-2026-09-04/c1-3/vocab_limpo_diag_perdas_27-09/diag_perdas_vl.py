"""Diagnóstico das perdas da subunidade primária do VOCAB_LIMPO (27/09). PESQUISA PÓS-GOLD: o gold já foi visto.

Reexecuta em memória a fase real do braço VOCAB_LIMPO pelo mesmo caminho da captura (helpers replay_bloco/replay_unidade,
taxonomia e índice dos snapshots congelados, palco do braço) com o pontuador do produto instrumentado por
`captura.instrumenta`. O diagnóstico só vale se as pontuações da 1ª passada, o número de chamadas e a subunidade final
forem IDÊNTICOS aos da captura congelada em TODOS os materiais do curso. Depois, para cada perda, retira os aliases
acrescentados pelo vocabulário (um por vez e todos juntos) do tópico vencedor e do tópico certo e recalcula com o mesmo
pontuador e os mesmos sinais. Não muda src/, sidecars, capturas, régua nem avaliador. Rodar via roda_controlado.py.
"""
import collections
import copy
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
C13 = AQUI.parent
DATA = AQUI.parents[4]
VL = C13 / "vocab_limpo_26-09"

_read_text = Path.read_text


def _sem_env(self, *a, **k):   # o import do produto tenta ler o .env da raiz: bloqueado (o helper engole a exceção)
    if self.name == ".env":
        raise PermissionError(".env bloqueado no diagnóstico")
    return _read_text(self, *a, **k)


Path.read_text = _sem_env
sys.path.insert(0, str(VL))
import captura as CP  # noqa: E402  (constantes e helpers da rodada; só stdlib no import)
import comum as K  # noqa: E402

CONG = K.carrega_json_estrito(CP.CONG)
exige = CP.exige
exige(CONG["id_comum"] == "6a0f9652fb8cfaffde15cd9d113705536c7fcc5f9b303474a74438ceee8c0e81", "congelamento inesperado")
exige(K.sha_json(K.arvore(DATA / "src")) == CONG["normativo"]["produto"]["src_arvore_sha"], "src/ != congelado")
for n, p in CP.HELPERS.items():
    exige(K.sha_arq(p) == CONG["normativo"]["codigo"][n], f"helper {n} != congelado")
sys.path.insert(1, str(DATA))
from src.builder.artifacts import repo as REPO  # noqa: E402
from src.builder.routing.motor import context as MCTX  # noqa: E402
from src.builder.extraction.entry_signals import normalize_match_text  # noqa: E402

ru = CP._load("diag_ru", CP.HELPERS["replay_unidade_21-09.py"])
rb = CP._load("diag_rb", CP.HELPERS["replay_bloco_21-09.py"])
exige(not K.verifica_modulos(dict(sys.modules), raiz=DATA / "src", arvore=CONG["normativo"]["produto"]["src_arquivos"]),
      "módulos src carregados != congelados")

BRACO = "VOCAB_LIMPO"
MAN = K.carrega_json_estrito(VL / "manifesto_capturas_vl.json")["capturas"]
CAP = {b: K.carrega_json_estrito(DATA / MAN[b]["arquivo"]) for b in ("CRU_LIMPO", BRACO)}
for b, c in CAP.items():
    exige(K.sha_arq(DATA / MAN[b]["arquivo"]) == MAN[b]["sha256"], f"captura {b} != manifesto")
AV = K.carrega_json_estrito(C13 / "vocab_limpo_avaliacao_26-09/avaliacao_vl_1.json")
PERDAS = [x for x in AV["comparacoes"][BRACO]["sub_primaria"]["registros"] if x["certo_antes"] and not x["certo_depois"]]
exige(len(PERDAS) == 13, f"esperadas 13 perdas, há {len(PERDAS)}")
F1_CAP = K.carrega_json_estrito(DATA / ".frzero/wad5_25-09/capturas/capturar_VOCAB_LLM_3fe5d1ff97258644_eb322c734dd3b7ea.json")
F1_SNAP = DATA / ".frzero/wad5_25-09/snapshots/VOCAB_LLM"


def mapa_aliases(tax, iter_t):
    return {(t["unit_slug"], t["topic_slug"]): [str(a) for a in (t.get("aliases") or [])] for t in iter_t(tax)}


def onde_aparece(alias, signals):
    a = normalize_match_text(alias)
    campos = ("title_text", "markdown_headings_text", "markdown_lead_text", "markdown_text")
    return [c for c in campos if a and a in normalize_match_text(str(signals.get(c) or ""))]


def diagnostica(alvo, sub_orig, cru_aliases, f1_aliases):
    score = sub_orig.keywords["score_entry_against_taxonomy_topic"]
    collect = sub_orig.keywords["collect_entry_unit_signals"]
    iter_t = sub_orig.keywords["iter_content_taxonomy_topics"]
    signals = collect(alvo["entry"], alvo["texto"])
    topicos = [t for t in iter_t(alvo["tax"]) if str(t.get("unit_slug") or "") == alvo["unidade"]]
    base = {t["topic_slug"]: score(signals, t) for t in topicos}

    def ranking(troca):
        s = {t["topic_slug"]: score(signals, troca.get(t["topic_slug"], t)) for t in topicos}
        top = max(s.values())
        return s, sorted(k for k, v in s.items() if v == top)

    def lado(slug):
        t = next(x for x in topicos if x["topic_slug"] == slug)
        cru = set(cru_aliases.get((alvo["unidade"], slug), []))
        delta = [a for a in t.get("aliases") or [] if a not in cru]
        sem = {**t, "aliases": [a for a in t.get("aliases") or [] if a in cru]}
        contrib = []
        for a in delta:
            t2 = {**t, "aliases": [x for x in t["aliases"] if x != a]}
            d = base[slug] - score(signals, t2)
            if d:
                _, vence = ranking({slug: t2})
                contrib.append({"alias": a, "contribuicao": round(d, 6), "campos": onde_aparece(a, signals),
                                "no_historico_mesmo_topico": a in f1_aliases.get((alvo["unidade"], slug), []),
                                "sem_ele_vence": vence})
        contrib.sort(key=lambda x: -x["contribuicao"])
        s_sem, vence_sem = ranking({slug: sem})
        return t, {"score": base[slug], "score_sem_delta": s_sem[slug], "n_aliases": len(t.get("aliases") or []),
                   "n_delta": len(delta), "aliases_delta_que_pontuam": contrib, "sem_delta_vence": vence_sem}

    _, vencedor = lado(alvo["vencedor"])
    _, certo = lado(alvo["certo"])
    return {"scores_1a": {k: round(v, 6) for k, v in sorted(base.items(), key=lambda kv: -kv[1])},
            "vencedor": vencedor, "certo": certo}


out = {"escopo": "pesquisa pós-gold (gold visto na avaliação de 26/09); nada alterado", "perdas": [], "fidelidade": {}}
cursos = sorted({x["curso"] for x in PERDAS})
orig = (REPO.load_glossary_curation, MCTX.load_repo_artifact, ru.load_internal_content_taxonomy, ru.read, ru.auto_sub)
for sig in cursos:
    root, palco = CP.RAIZES[sig], CP.PALCOS / BRACO / K.NOMES[sig]
    ins = CONG["insumos"][BRACO][sig]
    snap = CP.SNAP / BRACO / sig / "taxonomia.json"
    exige(K.sha_arq(snap) == ins["taxonomia_arquivo_sha"] and CP.arquivos_do_palco(BRACO, sig) == ins["palco"],
          f"{sig}: snapshot/palco != congelado")
    tax = K.carrega_json_estrito(snap)
    tax_cru = K.carrega_json_estrito(CP.SNAP / "CRU_LIMPO" / sig / "taxonomia.json")
    exige(K.sha_json(tax_cru) == CONG["insumos"]["CRU_LIMPO"][sig]["taxonomia_sha"], f"{sig}: snapshot CRU != congelado")
    tax_f1 = K.carrega_json_estrito(F1_SNAP / sig / "taxonomia.json")
    alvos_ids = {x["eid"] for x in PERDAS if x["curso"] == sig}
    chamadas, estado, guardados = {}, {"sig": sig}, {}
    sub_orig = orig[4]
    inst = CP.instrumenta(sub_orig, chamadas, estado)

    def sub(entry, taxonomy, markdown_text, winning_unit_slug="", _inst=inst, _g=guardados, _a=alvos_ids, **kw):
        eid = str(entry["id"])
        if eid in _a and eid not in _g:
            _g[eid] = {"entry": copy.deepcopy(entry), "texto": markdown_text, "tax": copy.deepcopy(taxonomy),
                       "unidade": str(winning_unit_slug or "")}
        return _inst(entry, taxonomy, markdown_text, winning_unit_slug=winning_unit_slug, **kw)

    REPO.load_glossary_curation = lambda root_dir, _p=palco: orig[0](_p)
    ru.load_internal_content_taxonomy = lambda r, _t=tax: copy.deepcopy(_t)

    def art(repo_, rel, _root=root, _t=tax):
        if Path(repo_).resolve() == _root.resolve() and rel == "course/.content_taxonomy.json":
            return copy.deepcopy(_t)
        return orig[1](repo_, rel)

    MCTX.load_repo_artifact = art
    try:
        MCTX.build_motor_context(root)
        ru.auto_sub = sub
        _, bloco_novo, _, _ = rb.replay(root)
        feed = [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]

        def patched(path, _feed=feed):
            data = orig[3](path)
            return {**data, "entries": _feed} if Path(path).name == "manifest.json" else data

        ru.read = patched
        _, novo, _ = ru.replay(root)
    finally:
        REPO.load_glossary_curation, MCTX.load_repo_artifact = orig[0], orig[1]
        ru.load_internal_content_taxonomy, ru.read, ru.auto_sub = orig[2], orig[3], orig[4]

    capd = CAP[BRACO]["decisoes"][sig]
    div = [eid for eid, d in capd.items()
           if (chamadas[sig].get(eid, [None])[0] or None) != d["p1"]
           or chamadas[sig].get(eid, [])[1:] != d["chamadas_posteriores"]
           or str(novo[eid].get("computed_subunit_slug") or "") != d["final"]["sub"]]
    out["fidelidade"][sig] = {"materiais": len(capd), "divergencias": div[:10], "n_divergencias": len(div)}
    exige(not div and set(novo) == set(capd), f"{sig}: reexecução != captura congelada ({len(div)} divergências)")
    print(f"{sig}: reexecução idêntica à captura em {len(capd)} materiais", flush=True)

    iter_t = sub_orig.keywords["iter_content_taxonomy_topics"]
    cru_aliases, f1_aliases = mapa_aliases(tax_cru, iter_t), mapa_aliases(tax_f1, iter_t)
    for x in (p for p in PERDAS if p["curso"] == sig):
        d, dc = capd[x["eid"]], CAP["CRU_LIMPO"]["decisoes"][sig][x["eid"]]
        f1 = F1_CAP["decisoes"][sig].get(x["eid"])
        reg = {"curso": sig, "gold_id": x["gold_id"], "eid": x["eid"], "cru": x["antes"], "vocab": x["depois"],
               "cru_p1": dc["p1"]["vencedor"]["topico"], "vocab_p1": d["p1"]["vencedor"]["topico"],
               "vocab_motivos_final": d["final"]["motivos_sub"], "vocab_chamadas_posteriores": len(d["chamadas_posteriores"]),
               "fase1_vocab_llm": {"p1": f1["p1"]["vencedor"]["topico"] if f1 and f1["p1"] else None,
                                   "final": f1["final"]["sub"] if f1 else None}}
        reg["onde_perde"] = "1a_passada" if reg["vocab_p1"] != x["antes"] else "2a_passada"
        alvo = {**guardados[x["eid"]], "vencedor": reg["vocab_p1"], "certo": x["antes"]}
        if reg["vocab_p1"] and reg["vocab_p1"] != x["antes"]:
            reg["ablacao"] = diagnostica(alvo, sub_orig, cru_aliases, f1_aliases)
            exige(abs(reg["ablacao"]["vencedor"]["score"] - next(p["score"] for p in d["p1"]["pontuacoes"]
                                                                  if p["topico"] == reg["vocab_p1"])) == 0,
                  f"{x['eid']}: score do vencedor != capturado")
        out["perdas"].append(reg)

K.grava_atomico(AQUI / "diag_perdas_vl.json", out)
print("DIAGNOSTICO GRAVADO", len(out["perdas"]), "perdas", flush=True)
