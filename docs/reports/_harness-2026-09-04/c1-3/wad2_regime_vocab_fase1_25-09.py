"""W-AD2 (25/09): regime VOCAB, Fase 1 corrigida — preflights SEM GOLD e captura por braço em processo isolado.

Protocolo: docs/reports/2026-09-25-regime-vocab-adendo-fase1.md (adendo ao desenho de 24/09). Resultado nomeado "efeito do
vocabulário sobre a cadeia de atribuição, condicionado à timeline histórica congelada". Este script NUNCA lê gold: não
importa módulos de avaliação, e uma trava aborta qualquer leitura de arquivo de gold. A avaliação é outro script.

Modos:
  --preflight                          P0-P6 sem gold (estado, proveniência, equivalências A/B, captura CRU e reprodução por
                                       ID, controles e verificação pós-carregador, carga isolada por braço). Grava
                                       c1-3/wad2_preflight_25-09.{json,md}.
  --capturar BRACO                     captura um braço completo em processo próprio (NÃO autorizado nesta etapa, exceto
                                       CRU dentro do preflight).
  --worker --braco B --modo M --saida  uso interno (processo isolado por braço).
Sem build, rede, LLM, recompilação ou commit.
"""
import argparse
import builtins
import collections
import copy
import functools
import hashlib
import io
import json
import os
import random
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

T0 = time.time()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
ORIG = DATA.parent
sys.path.insert(0, str(DATA))
BASE = DATA / ".frzero/wad2_25-09"
PALCOS = BASE / "palcos"
CAPS = BASE / "capturas"
OUT_JSON = HERE / "wad2_preflight_25-09.json"
OUT_MD = HERE / "wad2_preflight_25-09.md"
CAP_WAB = DATA / ".frzero/wab_captura_bracos_24-09.json"
CAP_WZ2 = DATA / ".frzero/wz2_captura_base_23-09.json"
LLM, MANUAL = ".glossary_curation.llm.json", ".glossary_curation.json"
NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}
OITAVO = "Laboratorio-de-Redes-Tutor"   # sidecar LLM sem pacote congelado nem régua: só proveniência
RAIZES = {s: DATA / (".frzero/wv_importacao_22-09" if s in ("MF", "IA", "CG") else ".frzero/pacote_fontes_15-09") / n
          for s, n in NOMES.items()}
BRACOS = ("CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3")
SEMENTES = {"CTRL_ALEAT_1": 1, "CTRL_ALEAT_2": 2, "CTRL_ALEAT_3": 3}
TENTATIVAS_ALEAT = 2000
GOLD = ("wx_gold_v2_final", "gold_units_", "material_gt_", "subunit_gt_", "coverage_gt_", "herancas_",
        "ground_truth", "regua_historica", "_gt_")
LOG = {"leituras": collections.Counter(), "gold": [], "rede": 0, "compilador": 0}


# ------------------------------------------------------------------------------------------- travas
class GoldTocado(RuntimeError):
    pass


def instala_travas():
    abrir = io.open

    def aberto(file, *a, **k):
        nome = str(file).replace("\\", "/")
        if any(p in nome.lower() for p in GOLD):
            LOG["gold"].append(nome)
            raise GoldTocado(f"leitura de gold bloqueada: {nome}")
        if any(p in nome for p in (".glossary_curation", ".content_taxonomy.json", ".timeline_index.json", "wad2_25-09")):
            LOG["leituras"][nome.split("/GitHub/")[-1]] += 1
        return abrir(file, *a, **k)

    builtins.open = io.open = aberto

    def sem_rede(*a, **k):
        LOG["rede"] += 1
        raise RuntimeError("REDE BLOQUEADA (W-AD2)")

    socket.socket.connect = sem_rede
    socket.create_connection = sem_rede
    from src.builder.core import vocabulary_compile as VC

    def sem_compilar(*a, **k):
        LOG["compilador"] += 1
        raise RuntimeError("COMPILADOR BLOQUEADO (W-AD2)")

    VC.compile_course_vocabulary = sem_compilar


def read(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def sha_arq(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def predicao_bloco(root, entry, blocos):
    lookup = {str(b.get("block_uuid")): b["id"] for b in blocos}
    lookup.update({str(b["id"]): b["id"] for b in blocos})
    bloco = str(entry.get("manual_timeline_block_id") or entry.get("temporal_block_id") or "")
    return lookup.get(bloco, bloco)


# ------------------------------------------------------------------------------------------- taxonomia
def chave_topico(t):
    return f"{str(t.get('code') or '').strip()} {str(t.get('label') or '').strip()}".strip()


def reconstroi(root, palco):
    from src.builder import engine
    from src.builder.artifacts import repo as REPO
    man = read(root / "manifest.json")
    prof = SimpleNamespace(**read(root / "_inputs_15-09.json")["profile_input"])
    orig = REPO.load_glossary_curation
    REPO.load_glossary_curation = lambda root_dir: orig(palco)
    try:
        tax = engine._build_rich_content_taxonomy(root, {"_repo_root": root, "course_name": prof.name}, prof,
                                                  entries=man["entries"])
    finally:
        REPO.load_glossary_curation = orig
    # Mesma forma serializada do artefato em disco (tupla x lista não pode falsear a equivalência A).
    return json.loads(json.dumps(tax, ensure_ascii=False))


def diferencas(a, b, caminho="", out=None, limite=25):
    out = [] if out is None else out
    if len(out) >= limite:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in list(dict.fromkeys(list(a) + list(b))):
            if k not in a or k not in b:
                out.append({"caminho": f"{caminho}.{k}", "so_em": "a" if k in a else "b"})
            else:
                diferencas(a[k], b[k], f"{caminho}.{k}", out, limite)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append({"caminho": caminho, "tamanho": [len(a), len(b)],
                        "so_em_a": [x for x in a if x not in b][:5], "so_em_b": [x for x in b if x not in a][:5]})
        else:
            for i, (x, y) in enumerate(zip(a, b, strict=True)):
                diferencas(x, y, f"{caminho}[{i}]", out, limite)
    elif a != b:
        out.append({"caminho": caminho, "a": a, "b": b})
    return out


def aliases_por_topico(tax):
    return {(str(u.get("slug") or ""), str(t.get("slug") or "")): list(t.get("aliases") or [])
            for u in tax.get("units") or [] for t in u.get("topics") or []}


def relacoes_efetivas(com, sem):
    """{(unidade, topico): {"add": [...ordem do produto], "rem": [...]}} entre duas reconstruções."""
    A, S = aliases_por_topico(com), aliases_por_topico(sem)
    out = {}
    for k in dict.fromkeys(list(S) + list(A)):
        add = [x for x in A.get(k, []) if x not in S.get(k, [])]
        rem = [x for x in S.get(k, []) if x not in A.get(k, [])]
        if add or rem:
            out[k] = {"add": add, "rem": rem}
    return out


def aditiva(congelada, rel):
    novo = copy.deepcopy(congelada)
    for u in novo.get("units") or []:
        for t in u.get("topics") or []:
            r = rel.get((str(u.get("slug") or ""), str(t.get("slug") or "")))
            if r:
                atual = [x for x in (t.get("aliases") or []) if x not in r["rem"]]
                t["aliases"] = atual + [x for x in r["add"] if x not in atual]
    return novo


# ------------------------------------------------------------------------------------------- palcos
def grava_palco(braco, sig, llm=None, manual=None):
    d = PALCOS / braco / NOMES[sig]
    (d / "course").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(RAIZES[sig] / "manifest.json", d / "manifest.json")
    for arq, dados in ((LLM, llm), (MANUAL, manual)):
        alvo = d / "course" / arq
        if dados:
            alvo.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
        elif alvo.exists():
            alvo.unlink()
    return d


def sidecar_de(atribuicao, tax):
    """{(unidade, topico): [aliases]} -> sidecar {"<código> <rótulo>": {"synonyms": [...]}}."""
    por_id = {(str(u.get("slug") or ""), str(t.get("slug") or "")): t for u in tax.get("units") or []
              for t in u.get("topics") or []}
    out = {"_provenance": "controle-wad2", "_nota": "reendereçamento das relações efetivas do VOCAB_LLM (adendo 25/09 §4)"}
    for k, termos in atribuicao.items():
        if termos:
            out.setdefault(chave_topico(por_id[k]), {"synonyms": []})["synonyms"].extend(termos)
    return out


def proveniencia():
    out = {}
    for nome in list(NOMES.values()) + [OITAVO]:
        rec = {}
        for arq in (LLM, MANUAL):
            p = ORIG / nome / "course" / arq
            if not p.is_file():
                continue
            d = read(p)
            chaves = [k for k in d if not k.startswith("_")]
            rec[arq] = {"sha256": sha_arq(p)[:16], "origem": str(p.relative_to(ORIG)),
                        "modificado": time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime)),
                        "_provenance": d.get("_provenance"), "_modelo": d.get("_modelo"),
                        "_nota": str(d.get("_nota") or "")[:160], "tem_raw": "_raw" in d, "chaves": len(chaves),
                        "termos": sum(len((d[k] or {}).get("synonyms") or []) for k in chaves if isinstance(d[k], dict)),
                        "prompt_versao": d.get("_prompt") or d.get("_prompt_version"),
                        "proveniencia_incompleta": not (d.get("_prompt") or d.get("_prompt_version"))}
        out[nome] = rec
    return out


# ------------------------------------------------------------------------------------------- controles
def controle_maior(rel_llm, tax, cru_decisoes):
    cont = collections.Counter((d["unidade"], d["sub"]) for d in cru_decisoes.values() if d.get("sub"))
    atrib, colisoes, info = {}, [], {}
    sem = aliases_por_topico(tax)
    for u in tax.get("units") or []:
        us = str(u.get("slug") or "")
        tops = [str(t.get("slug") or "") for t in u.get("topics") or []]
        rels = [(a, k) for k, r in rel_llm.items() if k[0] == us for a in r["add"]]
        if not rels or not tops:
            continue
        maior = max(tops, key=lambda t: (cont[(us, t)], -tops.index(t))) if any(cont[(us, t)] for t in tops) else tops[0]
        destino = (us, maior)
        termos = []
        for a, _k in rels:
            if a in sem.get(destino, []):
                colisoes.append({"unidade": us, "topico": maior, "alias": a})
            elif a not in termos:
                termos.append(a)
        atrib[destino] = termos
        info[us] = {"majoritario": maior, "decisoes_no_majoritario": cont[(us, maior)], "relacoes": len(rels),
                    "termos_apos_dedup": len(termos)}
    return atrib, {"colisoes": colisoes, "unidades": info}


def controle_aleatorio(rel_llm, tax, sig, semente):
    sem = aliases_por_topico(tax)
    atrib, info = {}, {}
    for u in tax.get("units") or []:
        us = str(u.get("slug") or "")
        rels = [(a, k) for k, r in rel_llm.items() if k[0] == us for a in r["add"]]
        if not rels:
            continue
        vagas = [k for k, r in rel_llm.items() if k[0] == us for _ in r["add"]]
        topicos_com_vaga = sorted(set(vagas))
        rng = random.Random(f"{semente}|{sig}|{us}")
        escolhida, violacoes, tentativas = None, None, 0
        for tentativa in range(1, TENTATIVAS_ALEAT + 1):
            tentativas = tentativa
            v = vagas[:]
            rng.shuffle(v)
            par = list(zip([a for a, _ in rels], v, strict=True))
            viol = [(a, d) for a, d in par if a in sem.get(d, [])]
            dup = len(par) - len(set(par))
            if escolhida is None:
                escolhida, violacoes = par, {"colisao": viol, "duplicado": dup}
            if not viol and not dup:
                escolhida, violacoes = par, {"colisao": [], "duplicado": 0}
                break
        mudou = sum(1 for (a, d), (_a, o) in zip(escolhida, rels, strict=True) if d != o)
        estado = ("sem_embaralhamento_informativo" if len(topicos_com_vaga) < 2 or mudou == 0
                  else "pareado" if not violacoes["colisao"] and not violacoes["duplicado"]
                  else "inviavel_sob_restricoes")
        if estado == "sem_embaralhamento_informativo":
            escolhida = [(a, o) for a, o in rels]
            mudou = 0
        for a, d in escolhida:
            atrib.setdefault(d, []).append(a)
        info[us] = {"estado": estado, "relacoes": len(rels), "mudaram_de_destino": mudou,
                    "topicos_com_vaga": len(topicos_com_vaga), "tentativas": tentativas,
                    "colisoes": len(violacoes["colisao"]), "duplicados": violacoes["duplicado"]}
    return atrib, info


def verifica(pretendido, efetivo, rel_llm=None):
    """Compara a atribuição pretendida com as relações efetivas depois do carregador."""
    ef = {k: r["add"] for k, r in efetivo.items() if r["add"]}
    pt = {k: v for k, v in pretendido.items() if v}
    difs = [{"topico": list(k), "pretendido": sorted(pt.get(k, [])), "efetivo": sorted(ef.get(k, []))}
            for k in dict.fromkeys(list(pt) + list(ef)) if sorted(pt.get(k, [])) != sorted(ef.get(k, []))]
    out = {"identico_pos_carregador": not difs, "diferencas": difs[:15], "n_diferencas": len(difs),
           "remocoes_de_aliases": sum(len(r["rem"]) for r in efetivo.values())}
    if rel_llm is not None:
        orig_cont = collections.Counter({k: len(r["add"]) for k, r in rel_llm.items()})
        ef_cont = collections.Counter({k: len(v) for k, v in ef.items()})
        termos_o = collections.Counter(a for r in rel_llm.values() for a in r["add"])
        termos_e = collections.Counter(a for v in ef.values() for a in v)
        out.update({"contagem_por_topico_preservada": +orig_cont == +ef_cont,
                    "multiconjunto_de_termos_preservado": termos_o == termos_e,
                    "multiplicidade_por_termo_preservada": termos_o == termos_e})
    return out


# ------------------------------------------------------------------------------------------- worker (processo isolado)
def worker(braco, modo, saida):
    instala_travas()
    from src.builder.artifacts import repo as REPO
    from src.builder.routing.motor import context as MCTX
    ru = load("wad2_ru", HERE / "replay_unidade_21-09.py")
    rb = load("wad2_rb", HERE / "replay_bloco_21-09.py")
    orig_gloss, orig_art, orig_tax, orig_read = (REPO.load_glossary_curation, MCTX.load_repo_artifact,
                                                 ru.load_internal_content_taxonomy, ru.read)
    manual_presente, unidades_motor, decisoes = {}, {}, {}
    sub_orig = ru.auto_sub
    estado = {"scores": None, "sig": None}

    def pontua(signals, topic):
        s = ru._score_entry_against_taxonomy_topic(signals, topic)
        if estado["scores"] is not None:
            estado["scores"].append([str(topic.get("unit_slug") or ""), str(topic.get("topic_slug") or ""),
                                     round(float(s), 6)])
        return s

    interno = functools.partial(sub_orig.func, *sub_orig.args,
                                **{**sub_orig.keywords, "score_entry_against_taxonomy_topic": pontua})

    def sub(entry, taxonomy, markdown_text, winning_unit_slug="", **kw):
        estado["scores"] = []
        try:
            m = interno(entry, taxonomy, markdown_text, winning_unit_slug=winning_unit_slug, **kw)
        finally:
            pontos, estado["scores"] = estado["scores"], None
        rec = decisoes[estado["sig"]].setdefault(str(entry["id"]), {})
        if "p1" not in rec:
            rec["p1"] = {"unidade": str(winning_unit_slug or ""), "pontuacoes": pontos, "vencedor": str(m.topic_slug or ""),
                         "conf": round(float(m.confidence or 0), 6), "ambigua": bool(m.ambiguous),
                         "motivos": [str(r) for r in (m.reasons or [])][:6]}
            rec["n_2a"] = 0
        else:
            rec["n_2a"] += 1
        return m

    try:
        for sig, root in RAIZES.items():
            estado["sig"] = sig
            decisoes[sig] = {}
            palco = PALCOS / braco / NOMES[sig]
            assert (palco / "manifest.json").is_file(), f"palco ausente: {palco}"
            manual_presente[sig] = (palco / "course" / MANUAL).is_file()
            tax = read(root / "course/.content_taxonomy.json") if braco == "CRU" else reconstroi(root, palco)
            REPO.load_glossary_curation = lambda root_dir, _p=palco: orig_gloss(_p)
            ru.load_internal_content_taxonomy = lambda r, _t=tax: copy.deepcopy(_t)

            def art(repo, rel, _root=root, _t=tax):
                if Path(repo).resolve() == _root.resolve() and rel == "course/.content_taxonomy.json":
                    return copy.deepcopy(_t)
                return orig_art(repo, rel)

            MCTX.load_repo_artifact = art
            try:
                ctx = MCTX.build_motor_context(root)
                unidades_motor[sig] = [[u.get("slug"), u.get("title")] for u in (ctx.units or [])]
                if modo == "carga":
                    prof = SimpleNamespace(**read(root / "_inputs_15-09.json")["profile_input"])
                    idx = ru.course_index({"_repo_root": root, "course_name": prof.name, "_content_taxonomy": tax}, prof)
                    decisoes[sig] = {"indice_unidades": len(idx or []), "taxonomia_sha": sha(tax)[:16]}
                    continue
                ru.auto_sub = sub
                saved, bloco_novo, _, _ = rb.replay(root)
                feed = [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]

                def patched(path, _feed=feed):
                    data = orig_read(path)
                    if Path(path).name == "manifest.json":
                        data = {**data, "entries": _feed}
                    return data

                ru.read = patched
                _, novo, _ = ru.replay(root)
                blocos = read(root / "course/.timeline_index.json")["blocks"]
                for eid, e in novo.items():
                    rec = decisoes[sig].setdefault(eid, {})
                    rec["final"] = {"bloco": predicao_bloco(root, e, blocos), "unidade": str(e.get("computed_unit_slug") or ""),
                                    "sub": str(e.get("computed_subunit_slug") or ""),
                                    "motivos_sub": [str(r) for r in e.get("subunit_match_reasons") or []][-3:],
                                    "motivos_unidade": [str(r) for r in e.get("unit_match_reasons") or []][-2:]}
                print("  worker", braco, modo, sig, len(novo), round(time.time() - T0), "s", flush=True)
            finally:
                REPO.load_glossary_curation, MCTX.load_repo_artifact = orig_gloss, orig_art
                ru.load_internal_content_taxonomy, ru.read, ru.auto_sub = orig_tax, orig_read, sub_orig
    except GoldTocado:
        pass
    outros = [k for k in LOG["leituras"] if "wad2_25-09/palcos/" in k and f"/palcos/{braco}/" not in k]
    res = {"braco": braco, "modo": modo, "manual_presente": manual_presente, "unidades_motor": unidades_motor,
           "leituras": dict(LOG["leituras"]), "leituras_de_outro_braco": outros, "gold": LOG["gold"],
           "rede": LOG["rede"], "compilador": LOG["compilador"], "decisoes": decisoes,
           "sha_decisoes": sha(decisoes), "segundos": round(time.time() - T0, 1)}
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    Path(saida).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")


def roda_worker(braco, modo):
    # A versão do script entra no nome: captura de outra versão do protocolo nunca é reaproveitada.
    saida = CAPS / f"{modo}_{braco}_{sha_arq(__file__)[:8]}.json"
    if modo == "capturar" and saida.exists():
        return read(saida)
    r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "--braco", braco, "--modo", modo,
                        "--saida", str(saida)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"worker {braco}/{modo} falhou ({r.returncode}): {r.stderr[-1500:]}")
    return read(saida)


# ------------------------------------------------------------------------------------------- preflight
def canon(decisoes):
    return {sig: {eid: [d["final"]["bloco"], d["final"]["unidade"], d["final"]["sub"]] for eid, d in v.items()
                  if isinstance(d, dict) and d.get("final")} for sig, v in decisoes.items()}


def preflight():
    assert not OUT_JSON.exists(), "preservar evidência existente"
    instala_travas()
    R = {"escopo": __doc__, "script_sha256": sha_arq(__file__)[:16]}
    ok = {}

    # P0 estado
    git = lambda *a: subprocess.run(["git", *a], cwd=DATA, capture_output=True, text=True, encoding="utf-8").stdout.strip()  # noqa: E731
    R["P0_estado"] = {"head": git("rev-parse", "--short", "HEAD"), "status": git("status", "--short").splitlines(),
                      "diff_src_tests_vazio": git("diff", "--stat", "--", "src", "tests") == "",
                      "protocolo_anterior": {"script": "c1-3/wad_regime_vocab_fase1_24-09.py",
                                             "script_sha256": sha_arq(HERE / "wad_regime_vocab_fase1_24-09.py")[:16],
                                             "palcos": ".frzero/wad_sidecars_24-09 (não reutilizáveis)",
                                             "capturas": sorted(p.name for p in (DATA / ".frzero").glob("wad_captura*"))}}
    ok["P0 src/tests sem diff"] = R["P0_estado"]["diff_src_tests_vazio"]

    # P1 proveniência e palcos dos braços históricos
    R["P1_proveniencia"] = proveniencia()
    for sig in NOMES:
        tutor = ORIG / NOMES[sig] / "course"
        llm = read(tutor / LLM) if (tutor / LLM).is_file() else None
        manual = read(tutor / MANUAL) if (tutor / MANUAL).is_file() else None
        grava_palco("CRU", sig)
        grava_palco("VOCAB_ATUAL", sig, llm, manual)
        grava_palco("VOCAB_LLM", sig, llm)

    # P2 equivalências A e B
    congelada, sem_sidecar, rel_llm, R["P2_equivalencias"] = {}, {}, {}, {}
    for sig, root in RAIZES.items():
        congelada[sig] = read(root / "course/.content_taxonomy.json")
        sem_sidecar[sig] = reconstroi(root, PALCOS / "CRU" / NOMES[sig])
        eq = {"A_sem_sidecar_igual_congelada": congelada[sig] == sem_sidecar[sig],
              "A_diferencas": diferencas(congelada[sig], sem_sidecar[sig])}
        for braco in ("VOCAB_ATUAL", "VOCAB_LLM"):
            com = reconstroi(root, PALCOS / braco / NOMES[sig])
            rel = relacoes_efetivas(com, sem_sidecar[sig])
            if braco == "VOCAB_LLM":
                rel_llm[sig] = rel
            eq[braco] = {"B_aditiva_igual_reconstrucao": aditiva(congelada[sig], rel) == com,
                         "B_diferencas": diferencas(aditiva(congelada[sig], rel), com),
                         "delta_vazio": not rel, "aliases_acrescentados": sum(len(r["add"]) for r in rel.values()),
                         "aliases_removidos": sum(len(r["rem"]) for r in rel.values()),
                         "topicos_alterados": len(rel), "taxonomia_sha": sha(com)[:16]}
        R["P2_equivalencias"][sig] = eq
    ok["P2 A em todos os cursos"] = all(e["A_sem_sidecar_igual_congelada"] for e in R["P2_equivalencias"].values())
    ok["P2 delta não vazio nos braços com sidecar"] = all(
        not e[b]["delta_vazio"] for e in R["P2_equivalencias"].values() for b in ("VOCAB_ATUAL", "VOCAB_LLM"))

    # P4 captura CRU em processo próprio e reprodução por ID
    cru = roda_worker("CRU", "capturar")
    wab = read(CAP_WAB)["M1"]
    ref = {sig: {eid: [r["bloco"], r["unidade"], r["sub"]] for eid, r in v.items() if eid != "__saved__"} for sig, v in wab.items()}
    atual = canon(cru["decisoes"])
    difs = [(s, e) for s in ref for e in set(ref[s]) | set(atual.get(s, {})) if ref[s].get(e) != atual.get(s, {}).get(e)]
    p1_final = [(s, e) for s, v in cru["decisoes"].items() for e, d in v.items()
                if d.get("p1") and d.get("final") and d["p1"]["unidade"] != d["final"]["unidade"]]
    R["P4_cru"] = {"sha_decisoes_canon": sha(atual)[:16], "sha_referencia_wab_M1": sha(ref)[:16],
                   "igual_por_id_a_referencia": not difs, "divergencias": difs[:20],
                   "materiais": sum(len(v) for v in atual.values()),
                   "com_primeira_passada": sum(1 for v in cru["decisoes"].values() for d in v.values() if d.get("p1")),
                   "unidade_1a_diferente_da_final": p1_final[:20], "n_unidade_1a_diferente": len(p1_final),
                   "gold": cru["gold"], "rede": cru["rede"], "compilador": cru["compilador"],
                   "manual_presente": cru["manual_presente"], "segundos": cru["segundos"]}
    ok["P4 CRU = referência por ID"] = not difs
    ok["P4 unidade da 1a passada = final"] = not p1_final
    ok["P4 sem gold, rede, compilador"] = not cru["gold"] and not cru["rede"] and not cru["compilador"]

    # P3 controles
    R["P3_controles"] = {}
    for sig, root in RAIZES.items():
        tax = sem_sidecar[sig]
        cru_sig = {e: d["final"] for e, d in cru["decisoes"][sig].items() if d.get("final")}
        ident = {k: r["add"] for k, r in rel_llm[sig].items() if r["add"]}
        grava_palco("_IDENTIDADE", sig, sidecar_de(ident, tax))
        v_ident = verifica(ident, relacoes_efetivas(reconstroi(root, PALCOS / "_IDENTIDADE" / NOMES[sig]), tax))
        rec = {"sanidade_identidade": v_ident}
        atrib, info = controle_maior(rel_llm[sig], tax, cru_sig)
        grava_palco("CTRL_MAIOR", sig, sidecar_de(atrib, tax))
        rec["CTRL_MAIOR"] = {"definicao": info,
                             "verificacao": verifica(atrib, relacoes_efetivas(
                                 reconstroi(root, PALCOS / "CTRL_MAIOR" / NOMES[sig]), tax))}
        for braco, s in SEMENTES.items():
            atrib, info = controle_aleatorio(rel_llm[sig], tax, sig, s)
            grava_palco(braco, sig, sidecar_de(atrib, tax))
            rec[braco] = {"unidades": info,
                          "verificacao": verifica(atrib, relacoes_efetivas(
                              reconstroi(root, PALCOS / braco / NOMES[sig]), tax), rel_llm[sig]),
                          "fracao_mudou_destino": round(sum(i["mudaram_de_destino"] for i in info.values())
                                                        / max(1, sum(i["relacoes"] for i in info.values())), 3)}
        R["P3_controles"][sig] = rec
    ok["P3 identidade reproduz VOCAB_LLM"] = all(r["sanidade_identidade"]["identico_pos_carregador"]
                                                 for r in R["P3_controles"].values())
    ok["P3 controles idênticos ao pretendido pós-carregador"] = all(
        r[b]["verificacao"]["identico_pos_carregador"] for r in R["P3_controles"].values()
        for b in ("CTRL_MAIOR", *SEMENTES))

    # P5 carga isolada por braço
    R["P5_carga"] = {}
    for braco in BRACOS:
        c = roda_worker(braco, "carga")
        R["P5_carga"][braco] = {"manual_presente": c["manual_presente"], "leituras_de_outro_braco": c["leituras_de_outro_braco"],
                                "gold": c["gold"], "rede": c["rede"], "compilador": c["compilador"],
                                "unidades_motor_sha": sha(c["unidades_motor"])[:16],
                                "taxonomia_sha": {s: d.get("taxonomia_sha") for s, d in c["decisoes"].items()},
                                "indice_unidades": {s: d.get("indice_unidades") for s, d in c["decisoes"].items()}}
    cargas = R["P5_carga"]
    ok["P5 manual só no VOCAB_ATUAL"] = all(any(c["manual_presente"].values()) == (b == "VOCAB_ATUAL") for b, c in cargas.items())
    ok["P5 nenhuma leitura de outro braço"] = all(not c["leituras_de_outro_braco"] for c in cargas.values())
    ok["P5 sem gold, rede, compilador"] = all(not c["gold"] and not c["rede"] and not c["compilador"] for c in cargas.values())
    ok["P5 unidades do motor iguais em todos os braços"] = len({c["unidades_motor_sha"] for c in cargas.values()}) == 1
    ok["P5 taxonomia dos braços históricos = P2"] = all(
        cargas[b]["taxonomia_sha"][s] == R["P2_equivalencias"][s][b]["taxonomia_sha"] for b in ("VOCAB_ATUAL", "VOCAB_LLM")
        for s in NOMES)

    R["condicoes"] = ok
    R["preflight_aprovado"] = all(ok.values())
    R["gold_lido_no_preflight"] = LOG["gold"]
    R["segundos"] = round(time.time() - T0, 1)
    OUT_JSON.write_text(json.dumps(R, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    escreve_md(R)
    for k, v in ok.items():
        print(("OK  " if v else "FALHA ") + k, flush=True)
    print("PREFLIGHT", "APROVADO" if R["preflight_aprovado"] else "REPROVADO", OUT_JSON.name,
          sha_arq(OUT_JSON)[:16], R["segundos"], "s", flush=True)


def escreve_md(R):
    L = ["# W-AD2 — preflights sem gold (25/09)", "", f"Script `wad2_regime_vocab_fase1_25-09.py` sha256 `{R['script_sha256']}…`.",
         f"Preflight **{'APROVADO' if R['preflight_aprovado'] else 'REPROVADO'}**.", "", "## Condições", ""]
    L += [f"- {'✅' if v else '❌'} {k}" for k, v in R["condicoes"].items()]
    L += ["", "## Equivalências por curso", "", "| curso | A | B VOCAB_ATUAL | B VOCAB_LLM | aliases +LLM | +ATUAL |", "|---|---|---|---|---:|---:|"]
    for s, e in R["P2_equivalencias"].items():
        L.append(f"| {s} | {e['A_sem_sidecar_igual_congelada']} | {e['VOCAB_ATUAL']['B_aditiva_igual_reconstrucao']} | "
                 f"{e['VOCAB_LLM']['B_aditiva_igual_reconstrucao']} | {e['VOCAB_LLM']['aliases_acrescentados']} | "
                 f"{e['VOCAB_ATUAL']['aliases_acrescentados']} |")
    L += ["", "## Controles por curso", "", "| curso | identidade | MAIOR pós-carregador | colisões MAIOR | ALEAT 1/2/3 pós-carregador | fração mudou (1/2/3) | unidades inviáveis ou sem embaralhamento |", "|---|---|---|---:|---|---|---|"]
    for s, c in R["P3_controles"].items():
        al = [c[b] for b in SEMENTES]
        estados = collections.Counter(i["estado"] for b in SEMENTES for i in c[b]["unidades"].values())
        L.append(f"| {s} | {c['sanidade_identidade']['identico_pos_carregador']} | {c['CTRL_MAIOR']['verificacao']['identico_pos_carregador']} | "
                 f"{len(c['CTRL_MAIOR']['definicao']['colisoes'])} | {'/'.join(str(a['verificacao']['identico_pos_carregador']) for a in al)} | "
                 f"{'/'.join(str(a['fracao_mudou_destino']) for a in al)} | {dict(estados)} |")
    p4 = R["P4_cru"]
    L += ["", "## CRU", "", f"- Igual à referência por ID: {p4['igual_por_id_a_referencia']} (sha canônico `{p4['sha_decisoes_canon']}` × "
          f"referência `{p4['sha_referencia_wab_M1']}`); {p4['materiais']} materiais; 1ª passada registrada em {p4['com_primeira_passada']}.",
          f"- Unidade da 1ª passada diferente da final: {p4['n_unidade_1a_diferente']}.", ""]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--capturar")
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--braco")
    ap.add_argument("--modo")
    ap.add_argument("--saida")
    a = ap.parse_args()
    if a.worker:
        worker(a.braco, a.modo, a.saida)
    elif a.preflight:
        preflight()
    elif a.capturar:
        raise SystemExit("captura dos braços não autorizada nesta etapa (adendo 25/09 §9)")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
