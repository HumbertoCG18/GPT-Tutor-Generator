"""W-V (#51): importacao OFFLINE dos snapshots locais dos materiais ausentes + pipeline completo sem rede/LLM.

1. Baseline: cadeia real bloco -> unidade (molde de aceite_v1_49_22-09.py:55-110) nos builds-base dos 7 cursos com o
   src/ atual; confere 217/237, 246/284, 84/251, 107/251.
2. Importacao: copia os builds-base de MF, IA e CG para .frzero/wv_importacao_22-09/<nome> e injeta, do manifest do
   repo-tutor REAL, as entradas ausentes PRESERVANDO identidade/origem e DESCARTANDO decisoes do motor/curadoria;
   copia os arquivos referenciados para os mesmos caminhos relativos. `t1-2026-1` NAO e injetado: o build-base do MF ja
   tem a mesma entrada (mesmo id, mesmos bytes do PDF, outro source_path; ausentes_21-09.md) -> ligado por identidade.
   CONTROLE de atribuicao: outra copia (.frzero/wv_importacao_22-09/_controle_reprocess/<nome>) com o MESMO reprocess e
   sem injecao, para separar efeito do reprocess de efeito da importacao. Os outros 4 cursos ficam sem copia.
3. Pipeline: reprocess_assignments.reprocess(copia, []) com tripwires (socket, Gemini, Datalab) e perfil do build
   (_inputs_15-09.json, voter/vocab LLM desligados), depois a cadeia real sobre a copia. Decisoes congeladas por sha256
   ANTES de carregar o gold. Placar direto por id (regua de mede_3eixos_12-09) cruzado com a cadeia.
4. Relatorio .json (deterministico, sem tempos) + .md (com tempo).
Uso: python -B wv_importacao_offline_22-09.py
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import sys
import time
from pathlib import Path
from types import SimpleNamespace

T0 = time.perf_counter()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
GH = DATA.parent
OUT = DATA / ".frzero/wv_importacao_22-09"
CTRL = OUT / "_controle_reprocess"
sys.path.insert(0, str(DATA))
sys.path.insert(0, str(DATA / "scripts"))
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"

# ---------------------------------------------------------------- tripwires (antes de qualquer import de src/)
CALLS = collections.Counter()


def _bloqueado(*a, **k):
    CALLS["rede_ou_llm"] += 1
    raise RuntimeError("REDE/LLM BLOQUEADO (wv_importacao_offline)")


socket.socket.connect = _bloqueado
socket.create_connection = _bloqueado
from src.builder.runtime import gemini_client, datalab_client  # noqa: E402
gemini_client.get_gemini_client = lambda config=None: None
gemini_client.GeminiClient.__init__ = _bloqueado
datalab_client.convert_document_to_markdown = _bloqueado
from src.builder import engine  # noqa: E402
engine.convert_document_to_markdown = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402

ALVOS = {
    "MF": ["eth2", "aws-encryption-sdk", "archive-of-formal-proofs-355fb8", "t1-2026-1"],
    "IA": ["o-que-é-inteligência-artificial-ia-oracle-brasil-43437f", "ia-responsável-7c4626"],
    "CG": ["video-sobre-origens-da-computacao-grafica-806e66", "video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758",
           "video-sobre-o-algoritmo-de-recorte-por-subdivisao-binaria-db7e2e", "video-sobre-mapeamento-em-opengl-1dad3c",
           "aula-gravada-975b85", "video-sobre-prechimento-de-areas-duracao-330-defae7",
           "video-sobre-prechimento-de-areas-duracao-1300-d87e5f"],
}
JA_PRESENTE = {("MF", "t1-2026-1")}   # mesmos bytes no build-base; nao injetar (duplicaria id e material)
BASELINE = {"bloco": (217, 237), "unidade": (246, 284), "sub_primaria": (84, 251), "sub_aceita": (107, 251)}
EIXOS = ("bloco", "unidade", "sub_primaria", "sub_aceita")

# Classificacao de campos da entrada real. Mantidos = identidade, origem, configuracao de extracao e texto/proveniencia.
MANTIDOS = {
    "id": "identidade (== id do gold)", "title": "identidade", "source_path": "origem", "file_type": "origem",
    "category": "origem (categoria de entrada)", "source_section": "origem (card Moodle)", "moodle_label": "origem Moodle",
    "moodle_section_index": "origem Moodle", "moodle_module_index": "origem Moodle", "moodle_week_label": "origem Moodle",
    "posting_date": "data de origem", "posting_date_created": "data de origem",
    "tags": "campo do usuario na entrada (vazio nos 12)", "notes": "entrada", "professor_signal": "entrada",
    "include_in_bundle": "entrada", "relevant_for_exam": "entrada",
    "processing_mode": "config de extracao", "ocr_language": "config de extracao", "document_profile": "config de extracao",
    "preferred_backend": "config de extracao", "datalab_mode": "config de extracao", "formula_priority": "config de extracao",
    "preserve_pdf_images_in_markdown": "config de extracao", "force_ocr": "config de extracao",
    "extract_images": "config de extracao", "extract_tables": "config de extracao", "page_range": "config de extracao",
    "effective_profile": "proveniencia de extracao", "base_backend": "proveniencia de extracao",
    "advanced_backend": "proveniencia de extracao", "document_report": "proveniencia de extracao",
    "pipeline_decision": "proveniencia de extracao (backend, nao atribuicao)", "extracted_files": "proveniencia de extracao",
    "clone_error": "proveniencia de extracao (clone falhou na origem)",
    "base_markdown": "texto (snapshot local)", "advanced_markdown": "texto", "approved_markdown": "texto curado",
    "curated_markdown": "texto curado", "approved_source_markdown": "proveniencia do texto curado",
    "approved_at": "data de origem da curadoria de TEXTO", "review_status": "estado da curadoria de TEXTO",
    "raw_target": "arquivo bruto", "advanced_metadata_path": "proveniencia de extracao",
}
DESCARTE_PREFIXO = {"temporal_block_": "decisao de bloco do motor (id/metodo/banda/flag/provider/janela)",
                    "computed_": "decisao do motor (bloco/unidade/subunidade computados)",
                    "manual_": "pino/curadoria manual (manual_tags/unit/block) ou artefato de revisao (manual_review)",
                    "auto_": "tags automaticas derivadas de decisoes", "unit_": "evidencia/conflito da decisao de unidade",
                    "subunit_": "evidencia da decisao de subunidade", "coverage_": "cobertura derivada da unidade"}
DESCARTE_CAMPO = {"revisar": "fila de revisao derivada das bandas/flags", "unit_slug": "decisao de unidade"}
DEFAULT_ENTRADA_NOVA = {"manual_tags": [], "manual_unit_slug": "", "manual_timeline_block_id": ""}   # FileEntry sem pino
ARQUIVOS = ("base_markdown", "advanced_markdown", "approved_markdown", "curated_markdown", "approved_source_markdown",
            "raw_target", "advanced_metadata_path")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).exists() else None


compare = load("wv_cmp", HERE / "compara_herancas_15-09.py")
mede = compare.mede
rb = load("wv_rb", HERE / "replay_bloco_21-09.py")
ru = load("wv_ru", HERE / "replay_unidade_21-09.py")
ORIG_READ = ru.read


def base_root(sig):
    return DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / mede.NOMES[sig]


def digests(root):
    return {p: sha(root / p) for p in ("manifest.json", "course/.timeline_index.json", "course/.content_taxonomy.json")}


def cadeia(root):
    """Cadeia real: rb.replay -> ru.replay com o manifest alimentado pelas entries do bloco novo."""
    saved, bloco_novo, _, _ = rb.replay(root)
    feed = [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]

    def patched(path, _feed=feed):
        data = ORIG_READ(path)
        if Path(path).name == "manifest.json":
            data = {**data, "entries": _feed}
        return data

    ru.read = patched
    try:
        _, novo, _ = ru.replay(root)
    finally:
        ru.read = ORIG_READ
    return saved, novo


def decisoes(root, entries):
    return {eid: list(compare.predictions(root, e)) for eid, e in sorted(entries.items())}


def classifica(key):
    if key in DESCARTE_CAMPO:
        return "descartado", DESCARTE_CAMPO[key]
    for prefix, why in DESCARTE_PREFIXO.items():
        if key.startswith(prefix):
            return "descartado", why
    if key in MANTIDOS or key.startswith("moodle_"):
        return "mantido", MANTIDOS.get(key, "origem Moodle")
    if key in ("images_dir", "tables_dir", "table_detection_dir", "advanced_asset_dir", "image_extraction", "latex_corruption"):
        return "mantido", "proveniencia de extracao"
    raise AssertionError(f"campo nao classificado: {key}")


def importa(sig, dest):
    """Injeta as entradas reais ausentes na copia. Retorna o registro por id."""
    real_root = GH / mede.NOMES[sig]
    real = {str(e["id"]): e for e in read(real_root / "manifest.json")["entries"]}
    manifest = read(dest / "manifest.json")
    ids = {str(e["id"]) for e in manifest["entries"]}
    fontes = {compare.source(e) for e in manifest["entries"]}
    registro = {}
    for gid in ALVOS[sig]:
        src = real[gid]
        if (sig, gid) in JA_PRESENTE:
            base = next(e for e in manifest["entries"] if str(e["id"]) == gid)
            iguais = sha(real_root / src["raw_target"]) == sha(dest / base["raw_target"])
            assert iguais, (sig, gid, "bytes divergem; nao e a mesma entrada")
            registro[gid] = {"acao": "nao_injetado_ja_presente", "sha256_bytes_iguais": iguais,
                             "source_path_real": src["source_path"], "source_path_build": base["source_path"],
                             "raw_real": src["raw_target"], "raw_build": base["raw_target"]}
            continue
        assert gid not in ids and compare.source(src) not in fontes, (sig, gid, "colisao de id/origem")
        nova, mantidos, descartados, arquivos = {}, {}, {}, []
        for key, value in src.items():
            destino, why = classifica(key)
            if destino == "mantido":
                nova[key] = value
                mantidos[key] = why
            else:
                descartados[key] = why
        nova.update({k: copy.deepcopy(v) for k, v in DEFAULT_ENTRADA_NOVA.items()})
        for key in ARQUIVOS:
            rel = nova.get(key)
            if not rel:
                continue
            origem = real_root / rel
            if not origem.is_file():
                arquivos.append({"campo": key, "path": rel, "copiado": False, "motivo": "inexistente no repo real"})
                continue
            alvo = dest / rel
            if alvo.exists():
                assert sha(alvo) == sha(origem), (sig, gid, rel, "arquivo diferente ja existe na copia")
            else:
                alvo.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origem, alvo)
            arquivos.append({"campo": key, "path": rel, "copiado": True, "bytes": origem.stat().st_size, "sha256": sha(origem)})
        manifest["entries"].append(nova)
        ids.add(gid)
        registro[gid] = {"acao": "injetado", "mantidos": mantidos, "descartados": descartados,
                         "defaults_entrada_nova": sorted(DEFAULT_ENTRADA_NOVA), "arquivos": arquivos}
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return registro


def perfil(sig, dest):
    """Perfil do build: SubjectStore do repo real + campos de _inputs_15-09.json; voter/vocab LLM desligados."""
    prof = copy.deepcopy(SubjectStore().find_by_repo_root(GH / mede.NOMES[sig]))
    assert prof is not None, sig
    for key, value in read(dest / "_inputs_15-09.json")["profile_input"].items():
        setattr(prof, key, value)
    prof.repo_root = str(dest)
    prof.queue = []
    prof.feature_flags = {**(prof.feature_flags or {}), "use_llm_voter": False, "compile_vocabulary": False}
    return SimpleNamespace(find_by_repo_root=lambda repo, _p=prof: _p)


def reprocessa(sig, dest):
    antes = dict(CALLS)
    ra.reprocess(dest, [], store=perfil(sig, dest))
    assert dict(CALLS) == antes and not CALLS, f"rede/LLM tentado em {sig}: {dict(CALLS)}"


def direto(sig, root, entries, gold):
    """Regua direta por id (mede_3eixos_12-09 main): so entries cujo id esta no gold."""
    gb, gu, gs, gsp = gold
    c = collections.Counter()
    for eid, (pb, pu, ps) in entries.items():
        if eid in gb:
            c["bloco_n"] += 1; c["bloco"] += pb == gb[eid]
        if eid in gu:
            c["unidade_n"] += 1; c["unidade"] += pu in gu[eid]
        if eid in gsp:
            c["sub_n"] += 1; c["sub_primaria"] += ps in gsp[eid]; c["sub_aceita"] += ps in gs[eid]
    return dict(c)


def avalia(sig, dec_cadeia, dec_gravado, gold, estendida):
    """Regua da cadeia (aceite_v1_49): gold -> herancas -> pacote_fontes -> origem unica no build.
    `estendida`: para os 13 sem ponte (new_id nulo), liga pelo id preservado (== gold_id) na copia."""
    gb, gu, gs, gsp = gold
    ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig] / "manifest.json")["entries"]}
    index = compare.indexed(list(dec_gravado["_entries"].values()))
    mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
    with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    c, linhas = collections.Counter(), {}
    for row in rows:
        gid = row["entry_id"]
        old = ref.get(mapping.get(gid) or "")
        hits = index.get(compare.source(old), []) if old else []
        assert len(hits) <= 1, (sig, gid)
        eid, ponte = (str(hits[0]["id"]), "oficial") if hits else (None, None)
        if eid is None and estendida and gid in ALVOS.get(sig, []) and gid in dec_cadeia:
            eid, ponte = gid, "id_preservado"
        pred = dec_cadeia.get(eid) if eid else None
        ok = {}
        if row["bloco"] != "":
            ok["bloco"] = bool(pred and pred[0] == gb[gid])
        if row["unidade"] != "":
            ok["unidade"] = bool(pred and pred[1] in gu[gid])
        if row["sub_primario"] != "":
            ok["sub_primaria"] = bool(pred and pred[2] in gsp[gid])
            ok["sub_aceita"] = bool(pred and pred[2] in gs[gid])
        for eixo, v in ok.items():
            c[f"{eixo}_n"] += 1
            c[eixo] += v
        linhas[gid] = {"entry_id": eid, "ponte": ponte, "pred": pred, "ok": ok,
                       "gold": {"bloco": gb.get(gid), "unidade": sorted(gu.get(gid) or []),
                                "sub_primaria": sorted(gsp.get(gid) or [])}}
    return dict(c), linhas


def soma(por_curso):
    t = collections.Counter()
    for v in por_curso.values():
        t.update(v)
    return {e: [t[e], t[f"{e}_n"]] for e in EIXOS}


def main():
    alvo_cursos = list(ALVOS)
    assert OUT.parent == DATA / ".frzero" and OUT.name == "wv_importacao_22-09"
    hash_base_antes = {sig: digests(base_root(sig)) for sig in mede.NOMES}
    hash_real_antes = {sig: sha(GH / mede.NOMES[sig] / "manifest.json") for sig in alvo_cursos}

    # ------------------------------------------------ fase SEM gold
    estado = {"antes": {}, "controle": {}, "depois": {}}
    for sig in mede.NOMES:
        root = base_root(sig)
        saved, novo = cadeia(root)
        estado["antes"][sig] = (root, saved, novo)
        print("baseline", sig, len(novo), flush=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    registro = {}
    for sig in alvo_cursos:
        name = mede.NOMES[sig]
        for dest in (OUT / name, CTRL / name):
            shutil.copytree(base_root(sig), dest)
        registro[sig] = importa(sig, OUT / name)
        for cenario, dest in (("controle", CTRL / name), ("depois", OUT / name)):
            reprocessa(sig, dest)
            saved, novo = cadeia(dest)
            estado[cenario][sig] = (dest, saved, novo)
            print(cenario, sig, len(novo), flush=True)
            if cenario == "depois":
                faltam = [g for g in ALVOS[sig] if g not in novo]
                assert not faltam, (sig, "entrada injetada sumiu no reprocess", faltam)
    for sig in mede.NOMES:   # os 4 cursos sem copia: controle e depois = baseline
        for cenario in ("controle", "depois"):
            estado[cenario].setdefault(sig, estado["antes"][sig])
    assert not CALLS, dict(CALLS)

    congelado = {cen: {sig: {"cadeia": decisoes(root, novo), "gravado": decisoes(root, saved)}
                       for sig, (root, saved, novo) in v.items()} for cen, v in estado.items()}
    sha_congelamento = hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    print("CONGELAMENTO", sha_congelamento, flush=True)

    # ------------------------------------------------ avaliacao (gold entra aqui)
    placar = {"antes": {}, "antes_ponte_estendida": {}, "controle": {}, "depois": {}}
    linhas = {k: {} for k in placar}
    diretos = {"antes": {}, "depois": {}}
    for sig in mede.NOMES:
        gold = mede.golds(sig)
        for cen, fonte, est in (("antes", "antes", False), ("antes_ponte_estendida", "antes", True),
                                ("controle", "controle", True), ("depois", "depois", True)):
            _, saved, _ = estado[fonte][sig]
            dg = {"_entries": saved}
            placar[cen][sig], linhas[cen][sig] = avalia(sig, congelado[fonte][sig]["cadeia"], dg, gold, est)
        for cen in diretos:
            diretos[cen][sig] = {"gravado_pelo_reprocess_ou_build": direto(sig, None, congelado[cen][sig]["gravado"], gold),
                                 "cadeia": direto(sig, None, congelado[cen][sig]["cadeia"], gold)}
    totais = {cen: soma(v) for cen, v in placar.items()}
    base_ok = {e: tuple(totais["antes"][e]) == BASELINE[e] for e in EIXOS}

    # tabela dos 13
    tabela = []
    for sig, gids in ALVOS.items():
        gold = mede.golds(sig)
        for gid in gids:
            a, d, c = linhas["antes"][sig][gid], linhas["depois"][sig][gid], linhas["controle"][sig][gid]
            ae = linhas["antes_ponte_estendida"][sig][gid]
            grav = congelado["depois"][sig]["gravado"].get(d["entry_id"]) if d["entry_id"] else None
            tabela.append({"curso": sig, "gold_id": gid, "acao": registro[sig][gid]["acao"],
                           "unidade_gold": d["gold"]["unidade"], "bloco_gold": d["gold"]["bloco"],
                           "sub_gold_primaria": d["gold"]["sub_primaria"],
                           "antes": {"ponte": a["ponte"], "pred": a["pred"], "ok": a["ok"]},
                           "antes_ponte_estendida": {"pred": ae["pred"], "ok": ae["ok"]},
                           "depois": {"ponte": d["ponte"], "pred": d["pred"], "ok": d["ok"]},
                           "reprocess_gravou": grav, "cadeia_igual_ao_gravado": grav == d["pred"] if grav else None})

    # qualquer outro id que mude (antes -> depois), atribuido via controle
    alvos = {(s, g) for s, gs in ALVOS.items() for g in gs}
    outros, perdas = [], {e: [] for e in EIXOS}
    for sig in mede.NOMES:
        for gid, a in linhas["antes"][sig].items():
            d, c = linhas["depois"][sig][gid], linhas["controle"][sig][gid]
            for eixo in EIXOS:
                if a["ok"].get(eixo) and not d["ok"].get(eixo):
                    perdas[eixo].append({"curso": sig, "gold_id": gid})
            if (sig, gid) in alvos:
                continue
            if a["pred"] != d["pred"] or a["ok"] != d["ok"]:
                outros.append({"curso": sig, "gold_id": gid, "antes": a["pred"], "depois": d["pred"], "controle": c["pred"],
                               "ok_antes": a["ok"], "ok_depois": d["ok"], "gold": d["gold"],
                               "causa": "reprocess (controle tambem muda)" if c["pred"] == d["pred"] else
                                        "importacao (controle nao muda)" if c["pred"] == a["pred"] else "reprocess+importacao"})
    # decisoes (todas as entries, nao so gold) que mudam no curso copiado: cadeia antes x depois
    mud_entries = {}
    for sig in alvo_cursos:
        a, d, c = (congelado[k][sig]["cadeia"] for k in ("antes", "depois", "controle"))
        mud_entries[sig] = {"mudam_vs_antes": sorted(e for e in a if e in d and a[e] != d[e]),
                            "mudam_vs_controle": sorted(e for e in c if e in d and c[e] != d[e]),
                            "novas": sorted(set(d) - set(a))}

    hash_base_depois = {sig: digests(base_root(sig)) for sig in mede.NOMES}
    hash_real_depois = {sig: sha(GH / mede.NOMES[sig] / "manifest.json") for sig in alvo_cursos}
    un = totais["depois"]["unidade"]
    checks = {
        "baseline_217_246_84_107": all(base_ok.values()),
        "builds_base_intocados": hash_base_antes == hash_base_depois,
        "repos_reais_intocados": hash_real_antes == hash_real_depois,
        "zero_rede_llm": not CALLS,
        "zero_perda": not any(perdas.values()),
        "unidade_ge_256_de_284": un[0] >= 256 and un[1] == 284,
    }
    report = {
        "issue": 51, "worker": "W-V", "head": "493119e",
        "checks": checks, "veredito_unidade_ge_256_sem_perda": checks["unidade_ge_256_de_284"] and checks["zero_perda"],
        "sha256_congelamento": sha_congelamento,
        "totais": totais, "por_curso": placar, "baseline_esperado": {k: list(v) for k, v in BASELINE.items()},
        "baseline_confere": base_ok, "tabela_13": tabela, "outros_ids_que_mudam": outros, "perdas": perdas,
        "decisoes_que_mudam_nos_cursos_copiados": mud_entries,
        "placar_direto_por_id": diretos,
        "importacao": registro,
        "campos": {"mantidos": MANTIDOS, "descartado_por_prefixo": DESCARTE_PREFIXO, "descartado_campo": DESCARTE_CAMPO,
                   "default_entrada_nova": DEFAULT_ENTRADA_NOVA},
        "hash_builds_base": hash_base_antes,
        "limitacoes": [
            "Ponte gold->build: os 13 tem new_id nulo em herancas_<sig>_15-09.json; a regua oficial nao os liga. Depois da "
            "importacao, liga pelo id preservado (== gold_id), com origem unica asserida na importacao.",
            "t1-2026-1 nao foi injetado: o build-base do MF ja tem a entrada com o mesmo id e bytes identicos do PDF "
            "(source_path do stash, nao de Downloads); injetar duplicaria o material. Ligado por id tambem em "
            "'antes_ponte_estendida' para separar ganho de ponte de ganho de importacao.",
            "Entradas injetadas vao ao fim da lista de entries (como uma entrada nova do produto).",
            "Perfil do reprocess = SubjectStore do repo real + profile_input do build (_inputs_15-09.json), "
            "use_llm_voter/compile_vocabulary desligados e TUTOR_NO_VOCAB_COMPILE=1 (mesma politica do build-base).",
            "Os 4 cursos sem copia (SO, ES2, TCC, FR) usam o baseline em controle e depois.",
        ],
    }
    out = HERE / "wv_importacao_offline_22-09.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sha_json = hashlib.sha256(out.read_bytes()).hexdigest()
    escreve_md(report, sha_json, time.perf_counter() - T0)
    print("TOTAIS", json.dumps(totais, ensure_ascii=False))
    print("CHECKS", checks)
    print("SHA256_JSON", sha_json)
    print(f"TEMPO {time.perf_counter() - T0:.1f}s")


def escreve_md(r, sha_json, segundos):
    L = [f"# W-V (#51) — importação offline dos ausentes (22/09/2026)", "",
         f"Veredito: unidade ≥ 256/284 sem perda = **{'SIM' if r['veredito_unidade_ge_256_sem_perda'] else 'NÃO'}**.",
         f"sha256 JSON `{sha_json}` · congelamento `{r['sha256_congelamento']}` · tempo {segundos:.0f}s · HEAD {r['head']}.", "",
         "## Placar (cadeia real rb→ru→régua)", "", "| cenário | bloco | unidade | sub primária | sub aceita |", "|---|---|---|---|---|"]
    for cen, t in r["totais"].items():
        L.append(f"| {cen} | " + " | ".join(f"{t[e][0]}/{t[e][1]}" for e in EIXOS) + " |")
    L += ["", "Por curso (antes → depois):", "", "| curso | bloco | unidade | sub prim. | sub aceita |", "|---|---|---|---|---|"]
    for sig in r["por_curso"]["antes"]:
        a, d = r["por_curso"]["antes"][sig], r["por_curso"]["depois"][sig]
        L.append(f"| {sig} | " + " | ".join(f"{a.get(e, 0)}→{d.get(e, 0)}/{d.get(e + '_n', 0)}" for e in EIXOS) + " |")
    L += ["", "## Os 13", "", "| curso | gold_id | ação | unidade gold | antes | depois unidade | acertou | bloco previsto (gold) | sub prevista (gold) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for t in r["tabela_13"]:
        p = t["depois"]["pred"] or ["", "", ""]
        L.append(f"| {t['curso']} | `{t['gold_id']}` | {t['acao']} | {', '.join(t['unidade_gold'])} | "
                 f"{'ausente' if not t['antes']['pred'] else t['antes']['pred'][1]} | {p[1]} | "
                 f"{'sim' if t['depois']['ok'].get('unidade') else 'não'} | {p[0]} ({t['bloco_gold']}) | {p[2]} ({', '.join(t['sub_gold_primaria'])}) |")
    L += ["", "## Outros ids que mudam", ""]
    L += [f"- {o['curso']} `{o['gold_id']}`: {o['antes']} → {o['depois']} (controle {o['controle']}); ok {o['ok_antes']} → {o['ok_depois']}; causa: {o['causa']}"
          for o in r["outros_ids_que_mudam"]] or ["- nenhum"]
    L += ["", "## Perdas por eixo", ""] + [f"- {e}: {v or 'nenhuma'}" for e, v in r["perdas"].items()]
    L += ["", "## Checks", ""] + [f"- {k}: {v}" for k, v in r["checks"].items()]
    L += ["", "## Campos da entrada real", "", "Mantidos: " + ", ".join(f"`{k}` ({v})" for k, v in r["campos"]["mantidos"].items()),
          "", "Descartados: " + ", ".join(f"`{k}*` ({v})" for k, v in r["campos"]["descartado_por_prefixo"].items())
          + ", " + ", ".join(f"`{k}` ({v})" for k, v in r["campos"]["descartado_campo"].items())
          + f". Defaults de entrada nova (sem pino): {r['campos']['default_entrada_nova']}.",
          "", "## Limitações", ""] + [f"- {x}" for x in r["limitacoes"]]
    (HERE / "wv_importacao_offline_22-09.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
