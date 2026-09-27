"""W-AD4 (25/09): regime VOCAB, Fase 1 — harness v4 (preflights SEM GOLD e captura isolada por braço).

Protocolo normativo: docs/reports/2026-09-25-regime-vocab-adendo-fase1-v3.md (bloco NORMATIVO). v3 preservada em
../wad3_25-09/ (congelamento 05dc9cf1…). Nunca lê gold: não importa módulos de avaliação; as travas (comum.Travas)
invalidam qualquer acesso proibido, mesmo quando uma camada intermediária engole a exceção.

Garantia "código executado = código validado" (estratégia declarada): o processo se relança com ambiente controlado,
`-B` e `-X pycache_prefix=<área vazia isolada>` (compila sempre a partir do fonte, sem bytecode em cache); os hashes do
harness, dos helpers e de todo `src/` são conferidos ANTES dos imports do produto e de novo no fim; DEPOIS dos imports,
a origem (`__file__`) e o hash de cada módulo `src.*` e dos helpers carregados são conferidos contra o congelamento.

Uso:
  python -B captura.py --preflight          P0-P5 sem gold; grava preflight_v4.{json,md} e o congelamento.
  python -B captura.py --worker ...         uso interno (processo isolado por braço).
Captura completa só do CRU (comum.CAPTURA_LIBERADA), conferida antes de lançar, de reutilizar e de aceitar.
"""
import argparse
import collections
import copy
import functools
import json
import os
import platform
import random
import shutil
import site
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

T0 = time.time()
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
C13 = HERE.parent
DATA = HERE.parents[4]
ORIG = DATA.parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(DATA))   # src/ importável (import tardio, depois das travas e das verificações)
import comum as K  # noqa: E402  (só stdlib)

AMBIENTE_INICIAL = dict(os.environ)   # antes de qualquer import do produto, que grava em os.environ (TESSDATA_PREFIX)

BASE = DATA / ".frzero/wad4_25-09"
PALCOS, SNAP, CAPS, FALHAS = BASE / "palcos", BASE / "snapshots", BASE / "capturas", BASE / "falhas"
PYCACHE = BASE / "pycache_vazio"
CONG = BASE / "congelamento.json"
CONG_ENTRADAS = BASE / "congelamento_entradas.json"
ADENDO = DATA / "docs/reports/2026-09-25-regime-vocab-adendo-fase1-v3.md"
CAP_WAB = DATA / ".frzero/wab_captura_bracos_24-09.json"
OUT_JSON, OUT_MD = HERE / "preflight_v4.json", HERE / "preflight_v4.md"
BASE_PRETENDIDA = "2589ed5a95ab8dd841de384bd219d80ee27d2cbf"
HELPERS = {"replay_bloco_21-09.py": C13 / "replay_bloco_21-09.py", "replay_unidade_21-09.py": C13 / "replay_unidade_21-09.py"}
CODIGO = {"captura.py": HERE / "captura.py", "comum.py": HERE / "comum.py", "avaliador.py": HERE / "avaliador.py",
          "test_wad4.py": HERE / "test_wad4.py", "test_defeitos_v4.py": HERE / "test_defeitos_v4.py", **HELPERS}
LLM, MANUAL = ".glossary_curation.llm.json", ".glossary_curation.json"
OITAVO = "Laboratorio-de-Redes-Tutor"
TUTORES = list(K.NOMES.values()) + [OITAVO]
RAIZES = {s: DATA / (".frzero/wv_importacao_22-09" if s in ("MF", "IA", "CG") else ".frzero/pacote_fontes_15-09") / n
          for s, n in K.NOMES.items()}
TENTATIVAS_ALEAT = 2000
ARTEFATOS_TEMPORAIS = (".timeline_index.json", ".card_block_map.json", ".lessons_index.json")
# Proveniência da avaliação (§7): caminhos EXPLÍCITOS, iguais aos que a resolução histórica p(nome) escolhe hoje (a pasta
# final da v2 só tem 3 arquivos, com blobs idênticos aos de docs/reports). Nada é aberto aqui: blob IDs vêm do índice.
REP, FINAL, FIX = "docs/reports", "docs/reports/_harness-2026-09-04/c1-3/wx_gold_v2_final_22-09", "tests/fixtures/eval"
C13R = "docs/reports/_harness-2026-09-04/c1-3"
UNI = ("MF", "SO", "IA", "ES2", "TCC", "CG")
REGUA_ARQUIVOS = {
    "ground_truth": {s: f"{REP}/ground_truth_{s}.csv" for s in UNI},
    "material_gt": {s: f"{FINAL if s in ('CG', 'ES2') else REP}/material_gt_{s}.csv" for s in UNI},
    "subunit_gt": {s: f"{FINAL if s == 'SO' else REP}/subunit_gt_{s}.csv" for s in K.NOMES},
    "gold_units": {s: f"{FIX}/gold_units_{s}.csv" for s in ("MF", "SO", "IA", "ES2", "TCC")},
    "herancas_csv": {s: f"{C13R}/herancas_{s}_15-09.csv" for s in K.NOMES},
    "herancas_json": {s: f"{C13R}/herancas_{s}_15-09.json" for s in K.NOMES},
}
REGUA_MANIFESTOS = {s: f".frzero/pacote_fontes_15-09/{n}/manifest.json" for s, n in K.NOMES.items()}
REGUA_CODIGO = {n: f"{C13R}/{n}" for n in ("compara_herancas_15-09.py", "mede_3eixos_12-09.py",
                                            "wx_regua_corrigida_22-09.py", "wz_bloco_cobertura_22-09.py")}
REGUA_CODIGO.update({n: n for n in ("scripts/eval_ground_truth.py", "scripts/eval_entry_unit.py")})


class Falha(RuntimeError):
    pass


def exige(cond, msg):
    """Condição essencial: não depende de assert (que pode ser desativado)."""
    if not cond:
        raise Falha(msg)


def raizes_codigo():
    out = [DATA / "src", HERE, Path(sys.base_prefix), Path(sys.prefix)]
    for p in list(site.getsitepackages()) + [site.getusersitepackages()]:
        out.append(Path(p))
    return out


def travas_worker(braco):
    """Configuração das travas de um worker (não instala). Código somente leitura."""
    t = K.Travas(f"worker:{braco}")
    t.permite("codigo", *raizes_codigo(), *HELPERS.values(), somente_leitura=True)
    t.permite("comum", *RAIZES.values(), somente_leitura=True)
    t.permite("braco", PALCOS / braco, SNAP / braco, somente_leitura=True)
    t.permite("referencia", CONG, CONG_ENTRADAS, somente_leitura=True)
    t.permite("saida", CAPS, FALHAS)
    for outro in K.BRACOS + ("_IDENTIDADE",):
        if outro != braco:
            t.proibe(PALCOS / outro, f"palco de outro braço ({outro})")
            t.proibe(SNAP / outro, f"snapshot de outro braço ({outro})")
    for nome in TUTORES:
        t.proibe(ORIG / nome, "tutor vivo")
    t.nega(DATA / ".env", "arquivo .env da raiz (pode conter segredos e configuração)")
    return t


def travas_principal():
    """Configuração das travas do processo principal (não instala). Código somente leitura; relatórios nomeados."""
    t = K.Travas("principal")
    t.permite("codigo", *raizes_codigo(), *HELPERS.values(), somente_leitura=True)
    t.permite("protocolo", ADENDO, somente_leitura=True)
    t.permite("comum", *RAIZES.values(), somente_leitura=True)
    t.permite("preparo", *[ORIG / n / "course" for n in TUTORES], somente_leitura=True)
    t.permite("referencia", CAP_WAB, *[DATA / p for p in REGUA_MANIFESTOS.values()], somente_leitura=True)
    t.permite("saida", BASE, OUT_JSON, OUT_MD)
    t.nega(DATA / ".env", "arquivo .env da raiz (pode conter segredos e configuração)")
    return t


def verifica_processo(cong=None):
    """Antes dos imports do produto: ambiente, intérprete, caminhos e (worker) código contra o congelamento."""
    prob = K.verifica_ambiente(os.environ)
    if not sys.flags.dont_write_bytecode or not sys.flags.no_user_site:
        prob.append("intérprete sem -B/PYTHONDONTWRITEBYTECODE ou com site de usuário")
    if not sys.pycache_prefix or Path(sys.pycache_prefix).resolve() != PYCACHE.resolve():
        prob.append(f"pycache_prefix inesperado: {sys.pycache_prefix!r}")
    elif any(PYCACHE.rglob("*.pyc")):
        prob.append("área de pycache isolada não está vazia")
    if [str(p) for p in sys.path[:2]] != [str(HERE), str(DATA)]:
        prob.append(f"sys.path inicial inesperado: {sys.path[:2]}")
    if cong is not None:
        itp = cong["normativo"]["interprete"]
        if sys.executable != itp["executavel"] or sys.version != itp["versao"]:
            prob.append("intérprete diferente do congelado")
        prob += K.verifica_codigo(cong["normativo"]["codigo"], CODIGO)
        if K.arvore(DATA / "src") != cong["normativo"]["produto"]["src_arquivos"]:
            prob.append("árvore src/ diferente da congelada")
    return prob


# ------------------------------------------------------------------------------------------- produto (import tardio)
def modulos(travas, src_arquivos):
    from src.builder.artifacts import repo as REPO
    from src.builder.core import vocabulary_compile as VC
    from src.builder.routing import resolver_apply as RA
    from src.builder.routing.motor import context as MCTX
    travas.bloqueia_compilador(VC)
    ru = _load("wad4_ru", HELPERS["replay_unidade_21-09.py"])
    rb = _load("wad4_rb", HELPERS["replay_bloco_21-09.py"])
    prob = K.verifica_modulos(dict(sys.modules), raiz=DATA / "src", arvore=src_arquivos)
    for mod, nome in ((ru, "replay_unidade_21-09.py"), (rb, "replay_bloco_21-09.py")):
        if Path(mod.__file__).resolve() != HELPERS[nome].resolve():
            prob.append(f"helper {nome} carregado de outro caminho")
    exige(not prob, f"módulos carregados não conferem com o congelamento: {prob[:4]}")
    n = sum(1 for m in sys.modules if m == "src" or m.startswith("src."))
    return SimpleNamespace(REPO=REPO, RA=RA, MCTX=MCTX, ru=ru, rb=rb, n_modulos_src=n)


def _load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(p):
    return K.carrega_json_estrito(p)


def perfil(root):
    return SimpleNamespace(**read(root / "_inputs_15-09.json")["profile_input"])


def reconstroi(M, root, palco):
    from src.builder import engine
    man = read(root / "manifest.json")
    prof = perfil(root)
    orig = M.REPO.load_glossary_curation
    M.REPO.load_glossary_curation = lambda root_dir: orig(palco)
    try:
        tax = engine._build_rich_content_taxonomy(root, {"_repo_root": root, "course_name": prof.name}, prof,
                                                  entries=man["entries"])
    finally:
        M.REPO.load_glossary_curation = orig
    return json.loads(json.dumps(tax, ensure_ascii=False))


def indice_unidade(M, root, palco, tax):
    prof = perfil(root)
    orig = M.REPO.load_glossary_curation
    M.REPO.load_glossary_curation = lambda root_dir: orig(palco)
    try:
        idx = M.ru.course_index({"_repo_root": root, "course_name": prof.name, "_content_taxonomy": tax}, prof)
    finally:
        M.REPO.load_glossary_curation = orig
    return K.canon(idx)


def predicao_bloco(entry, blocos):
    lookup = {str(b.get("block_uuid")): b["id"] for b in blocos}
    lookup.update({str(b["id"]): b["id"] for b in blocos})
    bloco = str(entry.get("manual_timeline_block_id") or entry.get("temporal_block_id") or "")
    return lookup.get(bloco, bloco)


# ------------------------------------------------------------------------------------------- equivalências
def sem_aliases(tax):
    t = copy.deepcopy(tax)
    for u in t.get("units") or []:
        for tp in u.get("topics") or []:
            tp.pop("aliases", None)
    return t


def aliases_por_topico(tax):
    return {(str(u.get("slug") or ""), str(t.get("slug") or "")): list(t.get("aliases") or [])
            for u in tax.get("units") or [] for t in u.get("topics") or []}


def relacoes(com, sem):
    A, S = aliases_por_topico(com), aliases_por_topico(sem)
    out = {}
    for k in dict.fromkeys(list(S) + list(A)):
        add = [x for x in A.get(k, []) if x not in S.get(k, [])]
        rem = [x for x in S.get(k, []) if x not in A.get(k, [])]
        if add or rem:
            out[k] = {"add": add, "rem": rem}
    return out


def diferencas_completas(a, b, caminho=""):
    """TODAS as diferenças (sem limite de inspeção)."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in dict.fromkeys(list(a) + list(b)):
            if k not in a or k not in b:
                out.append({"caminho": f"{caminho}.{k}", "so_em": "a" if k in a else "b"})
            else:
                out.extend(diferencas_completas(a[k], b[k], f"{caminho}.{k}"))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append({"caminho": caminho, "tamanho": [len(a), len(b)]})
        else:
            for i, (x, y) in enumerate(zip(a, b, strict=True)):
                out.extend(diferencas_completas(x, y, f"{caminho}[{i}]"))
    elif a != b:
        out.append({"caminho": caminho, "a": a, "b": b})
    return out


def diagnostico_b(aditiva_tax, com):
    """Classifica integralmente as diferenças entre a união aditiva e a reconstrução: só ordem de aliases ou outra."""
    if sem_aliases(aditiva_tax) != sem_aliases(com):
        return {"somente_ordem_de_aliases": False, "motivo": "campos não-alias diferem",
                "n_diferencas": len(diferencas_completas(aditiva_tax, com))}
    A, C = aliases_por_topico(aditiva_tax), aliases_por_topico(com)
    ordem, outra = 0, 0
    for k in dict.fromkeys(list(A) + list(C)):
        if A.get(k, []) == C.get(k, []):
            continue
        if collections.Counter(A.get(k, [])) == collections.Counter(C.get(k, [])):
            ordem += 1
        else:
            outra += 1
    return {"somente_ordem_de_aliases": outra == 0, "topicos_so_ordem": ordem, "topicos_outra_diferenca": outra,
            "n_diferencas": len(diferencas_completas(aditiva_tax, com))}


def aditiva(congelada, rel):
    novo = copy.deepcopy(congelada)
    for u in novo.get("units") or []:
        for t in u.get("topics") or []:
            r = rel.get((str(u.get("slug") or ""), str(t.get("slug") or "")))
            if r:
                atual = [x for x in (t.get("aliases") or []) if x not in r["rem"]]
                t["aliases"] = atual + [x for x in r["add"] if x not in atual]
    return novo


def verifica_controle(pretendido, sem, com, *, vocab_rel=None):
    """Verificação pós-carregador de um controle. Canonização declarada: as adições de um tópico são comparadas como
    multiconjunto (a ordem em que o produto insere aliases não é promessa do controle); aliases preexistentes e todos os
    campos não-alias são comparados com ordem. vocab_rel (só nos aleatórios) ativa as propriedades de distribuição."""
    prob = []
    if sem_aliases(sem) != sem_aliases(com):
        prob.append("campos estruturais (não-alias) mudaram")
    S, C = aliases_por_topico(sem), aliases_por_topico(com)
    if set(S) != set(C):
        prob.append("identidades de tópico mudaram")
    efetivo = {}
    for k in S:
        antes, depois = S[k], C.get(k, [])
        preservados = [x for x in depois if x in antes]
        if preservados != antes:
            prob.append(f"remoção ou reordenação de alias preexistente em {k}")
        add = [x for x in depois if x not in antes]
        if add:
            efetivo[k] = add
    pt = {k: list(v) for k, v in pretendido.items() if v}
    for k in dict.fromkeys(list(pt) + list(efetivo)):
        if collections.Counter(pt.get(k, [])) != collections.Counter(efetivo.get(k, [])):
            prob.append(f"pares pretendidos != efetivos em {k}")
    props = {}
    if vocab_rel is not None:
        orig = {k: r["add"] for k, r in vocab_rel.items() if r["add"]}
        props = {
            "contagem_por_topico": {k: len(v) for k, v in orig.items()} == {k: len(v) for k, v in efetivo.items()},
            "multiconjunto_de_termos": collections.Counter(a for v in orig.values() for a in v)
            == collections.Counter(a for v in efetivo.values() for a in v),
            "multiplicidade_por_termo": collections.Counter(a for v in orig.values() for a in set(v))
            == collections.Counter(a for v in efetivo.values() for a in set(v)),
            "sem_duplicata_no_topico": all(len(set(v)) == len(v) for v in efetivo.values()),
        }
        for nome, ok in props.items():
            if not ok:
                prob.append(f"propriedade falhou: {nome}")
    return {"aprovado": not prob, "problemas": prob, "propriedades": props, "efetivo": {"|".join(k): v for k, v in efetivo.items()}}


# ------------------------------------------------------------------------------------------- controles
def chave_topico(t):
    return f"{str(t.get('code') or '').strip()} {str(t.get('label') or '').strip()}".strip()


def sidecar_de(atribuicao, tax):
    por_id = {(str(u.get("slug") or ""), str(t.get("slug") or "")): t for u in tax.get("units") or []
              for t in u.get("topics") or []}
    out = {"_provenance": "controle-wad3", "_nota": "reendereçamento das relações efetivas do VOCAB_LLM (adendo v2 §4)"}
    for k, termos in atribuicao.items():
        if termos:
            out.setdefault(chave_topico(por_id[k]), {"synonyms": []})["synonyms"].extend(termos)
    return out


def controle_maior(rel_llm, tax, decisoes_cru):
    cont = collections.Counter((d["unidade"], d["sub"]) for d in decisoes_cru.values() if d.get("sub"))
    sem = aliases_por_topico(tax)
    atrib, colisoes, info = {}, [], {}
    for u in tax.get("units") or []:
        us = str(u.get("slug") or "")
        tops = [str(t.get("slug") or "") for t in u.get("topics") or []]
        rels = [(a, k) for k, r in rel_llm.items() if k[0] == us for a in r["add"]]
        if not rels or not tops:
            continue
        com_decisao = any(cont[(us, t)] for t in tops)
        maior = max(tops, key=lambda t: (cont[(us, t)], -tops.index(t))) if com_decisao else tops[0]
        termos = []
        for a, _k in rels:
            if a in sem.get((us, maior), []):
                colisoes.append({"unidade": us, "topico": maior, "alias": a})
            elif a not in termos:
                termos.append(a)
        atrib[(us, maior)] = termos
        info[us] = {"majoritario": maior, "decisoes_no_majoritario": cont[(us, maior)], "sem_decisoes": not com_decisao,
                    "relacoes": len(rels), "termos_apos_dedup": len(termos)}
    return atrib, {"colisoes": colisoes, "unidades": info}


def embaralha_unidade(rels, vagas, sem, rng, tentativas=TENTATIVAS_ALEAT):
    """Primeira permutação válida das vagas (política pré-declarada). Devolve (pares, estado, n_tentativas).
    Estados: estruturalmente_nao_informativa | identidade_sorteada | pareado | sem_permutacao_valida_no_orcamento."""
    if len(set(vagas)) < 2:
        return [(a, o) for a, o in rels], "estruturalmente_nao_informativa", 0
    identidade = [(a, o) for a, o in rels]
    primeira = None
    for n in range(1, tentativas + 1):
        v = list(vagas)
        rng.shuffle(v)
        par = list(zip([a for a, _ in rels], v, strict=True))
        if primeira is None:
            primeira = par
        if any(a in sem.get(d, []) for a, d in par) or len(set(par)) != len(par):
            continue
        return par, ("identidade_sorteada" if par == identidade else "pareado"), n
    return primeira, "sem_permutacao_valida_no_orcamento", tentativas


def controle_aleatorio(rel_llm, tax, sig, semente, rng_de=None):
    sem = aliases_por_topico(tax)
    atrib, info = {}, {}
    for u in tax.get("units") or []:
        us = str(u.get("slug") or "")
        rels = [(a, k) for k, r in rel_llm.items() if k[0] == us for a in r["add"]]
        if not rels:
            continue
        vagas = [o for _a, o in rels]
        rng = (rng_de or (lambda s, c, uu: random.Random(f"{s}|{c}|{uu}")))(semente, sig, us)
        pares, estado, n = embaralha_unidade(rels, vagas, sem, rng)
        for a, d in pares:
            atrib.setdefault(d, []).append(a)
        info[us] = {"estado": estado, "relacoes": len(rels), "topicos_com_vaga": len(set(vagas)), "tentativas": n,
                    "mudaram_de_destino": sum(1 for (_a, d), (_b, o) in zip(pares, rels, strict=True) if d != o)}
    bloqueado = any(i["estado"] == "sem_permutacao_valida_no_orcamento" for i in info.values())
    return atrib, info, bloqueado


# ------------------------------------------------------------------------------------------- palcos e proveniência
def grava_palco(braco, sig, llm=None, manual=None, *, abrir):
    d = PALCOS / braco / K.NOMES[sig]
    (d / "course").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(RAIZES[sig] / "manifest.json", d / "manifest.json")
    for arq, dados in ((LLM, llm), (MANUAL, manual)):
        alvo = d / "course" / arq
        if dados:
            with abrir(alvo, "w", encoding="utf-8") as fh:
                json.dump(dados, fh, ensure_ascii=False, indent=1)
        elif alvo.exists():
            alvo.unlink()
    return d


def arquivos_do_palco(braco, sig):
    d = PALCOS / braco / K.NOMES[sig]
    return {p.relative_to(d).as_posix(): K.sha_arq(p) for p in sorted(d.rglob("*")) if p.is_file()}


def proveniencia():
    out = {}
    for nome in TUTORES:
        rec = {}
        for arq in (LLM, MANUAL):
            p = ORIG / nome / "course" / arq
            if not p.is_file():
                continue
            d = read(p)
            chaves = [k for k in d if not k.startswith("_")]
            prompt = d.get("_prompt") or d.get("_prompt_version") or d.get("_versao_prompt")
            rec[arq] = {"sha256": K.sha_arq(p), "origem": str(p.relative_to(ORIG)), "modificado_em": time.strftime(
                "%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime)), "_provenance": d.get("_provenance"),
                "_modelo": d.get("_modelo"), "tem_raw": "_raw" in d, "chaves": len(chaves),
                "termos": sum(len((d[k] or {}).get("synonyms") or []) for k in chaves if isinstance(d[k], dict)),
                "versao_prompt": prompt, "proveniencia_incompleta": not prompt}
        out[nome] = rec
    return out




# ------------------------------------------------------------------------------------------- worker
def worker(braco, modo):
    platform.uname()
    platform.platform()   # aquece o cache antes das travas: no Windows a 1ª consulta executa `ver` (só na preparação)
    travas = travas_worker(braco)
    travas.instala()      # antes de qualquer import de src/ e helpers
    status, cap, erro, cong = "falhou", None, "", None
    try:
        exige(modo in ("carga", "capturar"), f"modo desconhecido: {modo}")
        if modo == "capturar" and braco not in K.CAPTURA_LIBERADA:
            travas.registra("captura_nao_autorizada", braco)
            raise Falha(f"captura completa de {braco} não autorizada nesta etapa")
        cong = read(CONG)
        prob = K.valida_congelamento(cong)
        entradas = read(CONG_ENTRADAS)
        if K.sha_json(entradas) != cong["normativo"]["entradas_arquivo_sha"]:
            prob.append("congelamento de entradas divergente")
        prob += verifica_processo(cong)
        exige(not prob, f"pré-execução não confere com o congelamento: {prob[:4]}")
        for sig, root in RAIZES.items():
            travas.congela(root, entradas[sig])
        travas.congela_arquivos(entradas["_externos"])
        ins = cong["insumos"][braco]
        for sig in K.NOMES:
            exige(arquivos_do_palco(braco, sig) == ins[sig]["palco"], f"{sig}: palco em disco != congelado")
        M = modulos(travas, cong["normativo"]["produto"]["src_arquivos"])
        cap = executa(M, travas, braco, modo, cong, ins)
        cap["verificacoes"]["modulos_src_verificados"] = M.n_modulos_src
        fim = K.verifica_codigo(cong["normativo"]["codigo"], CODIGO)
        if K.arvore(DATA / "src") != cong["normativo"]["produto"]["src_arquivos"]:
            fim.append("src/ mudou durante a execução")
        exige(not fim, f"código mudou durante a execução: {fim[:4]}")
        travas.rehash_leituras()
        status = "concluida" if not travas.violacoes else "falhou"
    except Exception as exc:  # noqa: BLE001  (a falha vira diagnóstico; nunca vira sucesso)
        erro = f"{type(exc).__name__}: {str(exc)[:400]}"
    resumo = travas.resumo()
    if status == "concluida" and cap is not None:
        cap.update({"esquema": K.ESQUEMA_CAPTURA, "braco": braco, "modo": modo, "status": status,
                    "violacoes": resumo["violacoes"], "negados": resumo["negados"], "acessos": resumo["acessos"],
                    "congelamento_comum": cong["id_comum"], "insumos_braco": cong["insumos_braco"][braco],
                    "segundos": round(time.time() - T0, 1)})
        cap["conteudo_sha"] = K.conteudo_sha(cap)
        destino = CAPS / f"{modo}_{braco}_{cong['id_comum'][:16]}_{cong['insumos_braco'][braco][:16]}.json"
        prob = K.valida_captura(cap, congelamento=cong, braco=braco, modo=modo)
        if prob:
            status, erro = "falhou", "captura não passou na própria validação: " + "; ".join(prob[:5])
        else:
            K.grava_atomico(destino, cap)
            print(json.dumps({"captura": str(destino)}), flush=True)
    if status != "concluida":
        K.grava_atomico(FALHAS / f"{modo}_{braco}_{int(time.time())}.json",
                        {"braco": braco, "modo": modo, "erro": erro, "violacoes": resumo["violacoes"],
                         "negados": resumo["negados"]})
        print(json.dumps({"falha": erro, "violacoes": len(resumo["violacoes"])}), flush=True)
    K.encerra(travas, ok=status == "concluida")


def instrumenta(sub_orig, chamadas, estado):
    """Envolve o seletor de subunidade sem alterar a decisão: registra, por chamada, a unidade fornecida, as pontuações
    exatas calculadas pelo próprio pontuador do seletor (sem arredondar), o vencedor com unidade, confiança, ambiguidade e
    motivos completos. `chamadas[estado["sig"]][id]` recebe a lista de chamadas (1ª = 1ª passada)."""
    pontuador = sub_orig.keywords["score_entry_against_taxonomy_topic"]   # exatamente o que o seletor usa
    lista = {"atual": None}

    def pontua(signals, topic):
        s = pontuador(signals, topic)
        if lista["atual"] is not None:
            lista["atual"].append({"unidade": str(topic.get("unit_slug") or ""), "topico": str(topic.get("topic_slug") or ""),
                                   "score": float(s)})
        return s

    interno = functools.partial(sub_orig.func, *sub_orig.args,
                                **{**sub_orig.keywords, "score_entry_against_taxonomy_topic": pontua})

    def sub(entry, taxonomy, markdown_text, winning_unit_slug="", **kw):
        lista["atual"] = []
        try:
            m = interno(entry, taxonomy, markdown_text, winning_unit_slug=winning_unit_slug, **kw)
        finally:
            pontos, lista["atual"] = lista["atual"], None
        chamadas.setdefault(estado["sig"], {}).setdefault(str(entry["id"]), []).append({
            "unidade_fornecida": str(winning_unit_slug or ""), "pontuacoes": pontos,
            "vencedor": {"unidade": str(getattr(m, "unit_slug", "") or ""), "topico": str(m.topic_slug or "")},
            "conf": float(m.confidence or 0.0), "ambigua": bool(m.ambiguous), "motivos": [str(r) for r in (m.reasons or [])]})
        return m   # decisão do produto intacta

    return sub


def executa(M, travas, braco, modo, cong, ins):
    ru, rb, REPO, MCTX, RA = M.ru, M.rb, M.REPO, M.MCTX, M.RA
    orig_gloss, orig_art, orig_tax, orig_read, sub_orig = (REPO.load_glossary_curation, MCTX.load_repo_artifact,
                                                           ru.load_internal_content_taxonomy, ru.read, ru.auto_sub)
    chamadas, estado = {}, {"sig": None}
    sub = instrumenta(sub_orig, chamadas, estado)

    out = {"inventario": {}, "decisoes": {}, "verificacoes": {}, "por_curso": {}}
    for sig, root in RAIZES.items():
        estado["sig"] = sig
        chamadas[sig] = {}
        palco = PALCOS / braco / K.NOMES[sig]
        snap_tax = SNAP / braco / sig / "taxonomia.json"
        snap_idx = SNAP / braco / sig / "indice_unidade.json"
        exige(K.sha_arq(snap_tax) == ins[sig]["taxonomia_arquivo_sha"], f"{sig}: snapshot de taxonomia alterado")
        exige(K.sha_arq(snap_idx) == ins[sig]["indice_arquivo_sha"], f"{sig}: snapshot de índice alterado")
        tax = read(snap_tax)
        if braco != "CRU":
            exige(K.sha_json(reconstroi(M, root, palco)) == K.sha_json(tax), f"{sig}: reconstrução != snapshot")
        idx_atual, idx_snap = indice_unidade(M, root, palco, tax), read(snap_idx)
        if K.sha_json(idx_atual) != K.sha_json(idx_snap):
            raise Falha(f"{sig}: índice != snapshot; primeiras diferenças: {diferencas_completas(idx_snap, idx_atual)[:3]}")
        REPO.load_glossary_curation = lambda root_dir, _p=palco: orig_gloss(_p)
        ru.load_internal_content_taxonomy = lambda r, _t=tax: copy.deepcopy(_t)

        def art(repo, rel, _root=root, _t=tax):
            if Path(repo).resolve() == _root.resolve() and rel == "course/.content_taxonomy.json":
                return copy.deepcopy(_t)
            return orig_art(repo, rel)

        MCTX.load_repo_artifact = art
        try:
            ctx = MCTX.build_motor_context(root)
            info = {"unidades_motor": [[u.get("slug"), u.get("title")] for u in (ctx.units or [])],
                    "taxonomia_sha": K.sha_json(tax), "indice_sha": K.sha_json(read(snap_idx))}
            if modo == "capturar":
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
                dec = {}
                for eid, e in novo.items():
                    cs = chamadas[sig].get(eid, [])
                    motivo = ("" if cs else "manual_subunit" if str(e.get("manual_subunit_slug") or "").strip()
                              else "nao_material" if not RA._is_material(e)
                              else "sem_bloco" if not (e.get("computed_block_id") or e.get("temporal_block_id"))
                              else "nao_identificado")
                    dec[eid] = {"curso": sig, "id": eid, "chamado": bool(cs), "motivo_nao_chamado": motivo,
                                "p1": cs[0] if cs else None, "chamadas_posteriores": cs[1:],
                                "taxonomia_sha": info["taxonomia_sha"],
                                "final": {"bloco": predicao_bloco(e, blocos), "unidade": str(e.get("computed_unit_slug") or ""),
                                          "sub": str(e.get("computed_subunit_slug") or ""),
                                          "conf_sub": e.get("subunit_match_confidence"),
                                          "motivos_sub": [str(r) for r in e.get("subunit_match_reasons") or []],
                                          "motivos_unidade": [str(r) for r in e.get("unit_match_reasons") or []]}}
                out["decisoes"][sig] = dec
                out["inventario"][sig] = sorted(novo)
                print("  worker", braco, sig, len(novo), round(time.time() - T0), "s", flush=True)
            else:
                out["inventario"][sig] = sorted(str(e["id"]) for e in read(root / "manifest.json")["entries"])
            out["por_curso"][sig] = info
        finally:
            REPO.load_glossary_curation, MCTX.load_repo_artifact = orig_gloss, orig_art
            ru.load_internal_content_taxonomy, ru.read, ru.auto_sub = orig_tax, orig_read, sub_orig
    ace = {p: r for p, r in travas.acessos.items()}
    manual = {sig: any(p.replace("\\", "/").endswith(f"/palcos/{braco}/{K.NOMES[sig]}/course/{MANUAL}") and "r" in r["modo"]
                       for p, r in ace.items()) for sig in K.NOMES}
    temporais_lidos = {sig: sorted(Path(p).name for p in ace
                                   if p.startswith(str(root.resolve())) and Path(p).name in ARTEFATOS_TEMPORAIS)
                       for sig, root in RAIZES.items()}
    # Hash de TODOS os temporais presentes (independe do que o modo leu); cada leitura passa pela trava e pelo congelamento.
    temporais = {sig: {n: K.sha_arq(root / "course" / n) for n in ARTEFATOS_TEMPORAIS if (root / "course" / n).is_file()}
                 for sig, root in RAIZES.items()}
    tax_congelada_lida = [p for p in ace if p.endswith(".content_taxonomy.json") and "palcos" not in p and "snapshots" not in p]
    out["verificacoes"] = {"manual_carregado": manual, "artefatos_temporais_sha": temporais,
                           "temporais_lidos": temporais_lidos, "taxonomia_congelada_lida": tax_congelada_lida}
    if modo == "carga":
        out["decisoes"] = {}
    return out




# ------------------------------------------------------------------------------------------- coordenação
def roda_worker(braco, modo, cong, travas):
    """Autorização ANTES de lançar, de ler cache e de aceitar."""
    if modo == "capturar" and braco not in K.CAPTURA_LIBERADA:
        raise Falha(f"captura de {braco} não autorizada nesta etapa (liberados: {sorted(K.CAPTURA_LIBERADA)})")
    destino = CAPS / f"{modo}_{braco}_{cong['id_comum'][:16]}_{cong['insumos_braco'][braco][:16]}.json"
    if destino.exists():
        cap = read(destino)
        prob = K.valida_captura(cap, congelamento=cong, braco=braco, modo=modo)
        if prob:
            raise Falha(f"captura inválida no caminho esperado {destino.name}; não sobrescrevo: {prob[:4]}")
        return cap, "reutilizada"
    cmd = [sys.executable, "-B", "-X", f"pycache_prefix={PYCACHE}", str(HERE / "captura.py"), "--worker",
           "--braco", braco, "--modo", modo, "--controlado"]
    with travas.comandos({Path(sys.executable).name}):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=K.ambiente_controlado(AMBIENTE_INICIAL))
    exige(r.returncode == 0, f"worker {braco}/{modo} saiu {r.returncode}: {r.stdout[-600:]} {r.stderr[-900:]}")
    cap = read(destino)
    prob = K.valida_captura(cap, congelamento=cong, braco=braco, modo=modo)
    exige(not prob, f"captura de {braco}/{modo} inválida: {prob[:4]}")
    exige(modo != "capturar" or cap.get("braco") in K.CAPTURA_LIBERADA, "aceitação recusada: braço não autorizado")
    return cap, "nova"


def normativo_protocolo():
    txt = ADENDO.read_text(encoding="utf-8")
    ini, fim = "<!-- NORMATIVO:INICIO -->", "<!-- NORMATIVO:FIM -->"
    exige(txt.count(ini) == 1 and txt.count(fim) == 1, "marcadores do bloco normativo ausentes no adendo v3")
    return txt.split(ini, 1)[1].split(fim, 1)[0]


def externas(manifestos, abrir, travas):
    """{caminho absoluto: sha} dos arquivos de origem apontados por `source_path` fora dos pacotes. Cada caminho passa
    pelas proibições ANTES de ser lido (gold, .env e demais negados não são hasheados nem autorizados)."""
    out = {}
    for m in manifestos.values():
        for e in m["entries"]:
            p = str(e.get("source_path") or "")
            if p and Path(p).is_absolute():
                travas.checa_preparo(p)
                exige(Path(p).is_file(), f"entrada externa ausente: {p}")
                out[str(Path(p).resolve())] = K.sha_arq(p, abrir)
    return out


def descritor_regua(travas, abrir):
    """Proveniência da avaliação SEM ler gold: caminhos explícitos + blob IDs do índice do git (nenhum arquivo de régua é
    aberto nem hasheado). Código histórico dos carregadores: blob do índice + conferência de que a cópia de trabalho é a
    indexada (git diff; é código, não gold). Manifests de referência (não são gold): sha256 do conteúdo."""
    caminhos = sorted({c for papel in REGUA_ARQUIVOS.values() for c in papel.values()})
    with travas.comandos({"git"}):
        saida, erro = K.git("ls-files", "-s", "--", *caminhos, *REGUA_CODIGO.values(), cwd=DATA)
        mudado, erro2 = K.git("diff", "--name-only", "HEAD", "--", *REGUA_CODIGO.values(), cwd=DATA)
    exige(not erro and not erro2, f"git falhou no descritor da régua: {erro or erro2}")
    blobs = {}
    for linha in saida.splitlines():
        meta, caminho = linha.split("\t", 1)
        blobs[caminho] = meta.split()[1]
    arquivos = {papel: {s: {"caminho": c, "blob_git": blobs.get(c)} for s, c in m.items()} for papel, m in REGUA_ARQUIVOS.items()}
    manifestos = {}
    for s, c in REGUA_MANIFESTOS.items():
        travas.checa_preparo(DATA / c)
        manifestos[s] = {"caminho": c, "sha256": K.sha_arq(DATA / c, abrir)}
    codigo = {c: blobs.get(c) for c in REGUA_CODIGO.values()}
    pend = [f"sem blob no índice do git: {c}" for c in [*caminhos, *REGUA_CODIGO.values()] if c not in blobs]
    pend += [f"código histórico com mudança local: {c}" for c in mudado.split()]
    return {"arquivos": arquivos, "manifestos_referencia": manifestos, "codigo_historico_blob": codigo, "pendencias": pend,
            "nota": "blob IDs lidos do índice do git, sem abrir os arquivos de régua; a abertura autorizada confere os bytes "
                    "(blob_git) antes de usar"}


def distribuicoes():
    from importlib import metadata
    return sorted(f"{d.metadata['Name']}=={d.version}" for d in metadata.distributions() if d.metadata["Name"])


def compara_referencia(cru, ref_path):
    """P4: conjuntos completos de cursos e IDs, duplicatas e registros incompletos ANTES de canonizar."""
    ref = read(ref_path)["M1"]   # carregador estrito: chave duplicada = erro
    prob = []
    if set(ref) != set(K.NOMES):
        prob.append(f"referência: cursos {sorted(set(ref) ^ set(K.NOMES))} divergem")
    if set(cru["decisoes"]) != set(K.NOMES):
        prob.append(f"captura: cursos {sorted(set(cru['decisoes']) ^ set(K.NOMES))} divergem")
    difs = []
    for sig in K.NOMES:
        r = {e: v for e, v in (ref.get(sig) or {}).items() if e != "__saved__"}
        c = cru["decisoes"].get(sig) or {}
        if set(r) != set(c):
            prob.append(f"{sig}: IDs divergem (só referência {sorted(set(r) - set(c))[:5]}, só captura {sorted(set(c) - set(r))[:5]})")
        for eid in sorted(set(r) & set(c)):
            rv = r[eid]
            if not all(isinstance(rv.get(k), str) for k in ("bloco", "unidade", "sub")):
                prob.append(f"{sig}/{eid}: registro de referência incompleto")
                continue
            a = [rv["bloco"], rv["unidade"], rv["sub"]]
            b = [c[eid]["final"]["bloco"], c[eid]["final"]["unidade"], c[eid]["final"]["sub"]]
            if a != b:
                difs.append({"curso": sig, "id": eid, "referencia": a, "captura": b})
    return prob, difs


def preflight():
    platform.uname()
    plataforma = platform.platform()   # aquece o cache antes das travas: no Windows a 1ª consulta executa `ver`
    travas = travas_principal()
    travas.instala()
    abrir = travas._abrir_original
    R, ok = {"escopo": __doc__}, {}
    if OUT_JSON.exists():   # fora do try: nunca sobrescrever evidência anterior
        print("preflight_v4.json já existe: preservar evidência (usar nova versão)", flush=True)
        sys.exit(1)
    try:
        exige((DATA / "src").is_dir() and (DATA / ".git").exists() and (DATA / "docs").is_dir(),
              f"raiz do repositório errada: {DATA}")
        prob_proc = verifica_processo(None)
        R["P0_processo"] = {"problemas": prob_proc, "ambiente": K.descritor_ambiente(os.environ),
                            "executavel": sys.executable, "pycache_prefix": sys.pycache_prefix, "cwd": os.getcwd()}
        ok["P0 processo: ambiente declarado, -B, pycache isolado, sys.path"] = not prob_proc
        exige(not prob_proc, f"processo principal fora do controle declarado: {prob_proc[:4]}")
        codigo_inicio = {n: K.sha_arq(p, abrir) for n, p in CODIGO.items()}
        src_arquivos = K.arvore(DATA / "src", abrir)
        # P0 estado
        with travas.comandos({"git"}):
            head, e1 = K.git("rev-parse", "HEAD", cwd=DATA)
            staged, e2 = K.git("diff", "--cached", "--name-only", cwd=DATA)
            unstaged, e3 = K.git("diff", "--name-only", cwd=DATA)
            untracked, e4 = K.git("ls-files", "--others", "--exclude-standard", cwd=DATA)
            base_src, e5 = K.git("diff", "--name-only", BASE_PRETENDIDA, "--", "src", "tests", cwd=DATA)
        erros_git = [e for e in (e1, e2, e3, e4, e5) if e]
        R["P0"] = {"head": head.strip(), "staged": staged.split(), "unstaged": unstaged.split(),
                   "nao_versionados": untracked.split(), "src_tests_vs_base": base_src.split(), "erros_git": erros_git}
        ok["P0 comandos git sem erro"] = not erros_git
        ok["P0 src/tests idênticos à base pretendida"] = not erros_git and not base_src.split() and not [
            p for p in staged.split() + unstaged.split() if p.startswith(("src/", "tests/"))]
        exige(ok["P0 comandos git sem erro"] and ok["P0 src/tests idênticos à base pretendida"],
              "código efetivo difere da base pretendida ou git falhou; medição interrompida")
        arvores = {sig: K.arvore(root, abrir, checa=travas.checa_preparo) for sig, root in RAIZES.items()}
        for sig, root in RAIZES.items():
            travas.congela(root, arvores[sig])
        manifestos = {sig: read(root / "manifest.json") for sig, root in RAIZES.items()}
        externos = externas(manifestos, abrir, travas)
        travas.congela_arquivos(externos)
        inventario = {sig: sorted(str(e["id"]) for e in m["entries"]) for sig, m in manifestos.items()}
        dup = {sig: [e for e, n in collections.Counter(str(x["id"]) for x in m["entries"]).items() if n > 1]
               for sig, m in manifestos.items()}
        ok["P0 inventário congelado = 350 sem duplicatas"] = (sum(len(v) for v in inventario.values()) == K.INVENTARIO_ESPERADO
                                                              and not any(dup.values()))

        # P1 proveniência (única leitura dos tutores vivos) e palcos
        R["P1_proveniencia"] = proveniencia()
        vivos = {}
        for sig in K.NOMES:
            tutor = ORIG / K.NOMES[sig] / "course"
            vivos[sig] = {arq: (read(tutor / arq) if (tutor / arq).is_file() else None) for arq in (LLM, MANUAL)}
        travas.permitidos.pop("preparo")
        for nome in TUTORES:
            travas.proibe(ORIG / nome, "tutor vivo depois do preparo")
        manual_real = {b: {s: (b == "VOCAB_ATUAL" and vivos[s][MANUAL] is not None) for s in K.NOMES} for b in K.BRACOS}
        ok["P1 inventário de manuais = referência declarada"] = manual_real == K.MANUAL_ESPERADO
        exige(ok["P1 inventário de manuais = referência declarada"], f"mudança de insumo: manuais {manual_real['VOCAB_ATUAL']}")
        for sig in K.NOMES:
            grava_palco("CRU", sig, abrir=abrir)
            grava_palco("VOCAB_ATUAL", sig, vivos[sig][LLM], vivos[sig][MANUAL], abrir=abrir)
            grava_palco("VOCAB_LLM", sig, vivos[sig][LLM], abrir=abrir)

        # congelamento comum (normativo, sem resultados)
        entradas = {**{sig: arvores[sig] for sig in K.NOMES}, "_externos": externos}
        K.grava_atomico(CONG_ENTRADAS, entradas, abrir)
        normativo = {
            "protocolo_sha": K.sha_bytes(normativo_protocolo().encode("utf-8")),
            "codigo": codigo_inicio,
            "produto": {"base": BASE_PRETENDIDA, "src_arquivos": src_arquivos, "src_arvore_sha": K.sha_json(src_arquivos)},
            "interprete": {"executavel": sys.executable, "versao": sys.version, "plataforma": plataforma,
                           "flags": {"dont_write_bytecode": sys.flags.dont_write_bytecode, "no_user_site": sys.flags.no_user_site},
                           "pycache_prefix": str(PYCACHE), "distribuicoes_sha": K.sha_json(distribuicoes()),
                           "estrategia": "compila do fonte (-B, pycache_prefix vazio isolado); hashes antes dos imports e no "
                                         "fim; origem e hash dos módulos carregados conferidos"},
            "caminhos": {"raiz": str(DATA), "sys_path_inicio": [str(HERE), str(DATA)]},
            "ambiente": K.descritor_ambiente(os.environ),
            "temporais": {sig: {n: arvores[sig][f"course/{n}"] for n in ARTEFATOS_TEMPORAIS if f"course/{n}" in arvores[sig]}
                          for sig in K.NOMES},
            "avaliacao": descritor_regua(travas, abrir),
            "entradas_comuns": {sig: {"raiz": RAIZES[sig].relative_to(DATA).as_posix(), "arvore_sha": K.sha_json(arvores[sig])}
                                for sig in K.NOMES},
            "entradas_arquivo_sha": K.sha_json(entradas),
            "entradas_externas": {"n": len(externos), "sha": K.sha_json(externos)},
            "referencias": {"wab_captura_bracos_24-09.json": K.sha_arq(CAP_WAB, abrir)},
            "inventario": inventario,
            "esperado": {"manual": K.MANUAL_ESPERADO, "captura_liberada": sorted(K.CAPTURA_LIBERADA),
                         "denominadores": K.DENOMINADORES, "inventario_total": K.INVENTARIO_ESPERADO},
        }
        cong = {"normativo": normativo, "id_comum": K.id_congelamento(normativo), "insumos": {}, "insumos_braco": {},
                "controles": {}}
        R["congelamento_id_comum"] = cong["id_comum"]
        ok["P0 descritor da avaliação sem pendências (blob IDs; gold não aberto)"] = not normativo["avaliacao"]["pendencias"]
        M = modulos(travas, src_arquivos)
        R["P0_modulos_src_verificados"] = M.n_modulos_src

        # P2 equivalências e snapshots dos braços históricos
        congelada, sem, rel_llm, idx = {}, {}, {}, collections.defaultdict(dict)
        R["P2"] = {}
        for sig, root in RAIZES.items():
            congelada[sig] = read(root / "course/.content_taxonomy.json")
            sem[sig] = reconstroi(M, root, PALCOS / "CRU" / K.NOMES[sig])
            difA = diferencas_completas(congelada[sig], sem[sig])
            e = {"A_igual": congelada[sig] == sem[sig], "A_n_diferencas": len(difA), "A_exemplos": difA[:5]}
            snaps = {"CRU": congelada[sig]}
            for b in ("VOCAB_ATUAL", "VOCAB_LLM"):
                com = reconstroi(M, root, PALCOS / b / K.NOMES[sig])
                rel = relacoes(com, sem[sig])
                if b == "VOCAB_LLM":
                    rel_llm[sig] = rel
                e[b] = {"B_diagnostico": diagnostico_b(aditiva(congelada[sig], rel), com),
                        "aliases_add": sum(len(r["add"]) for r in rel.values()),
                        "aliases_rem": sum(len(r["rem"]) for r in rel.values()), "delta_vazio": not rel}
                snaps[b] = com
            for b, tax in snaps.items():
                i = indice_unidade(M, root, PALCOS / b / K.NOMES[sig], tax)
                idx[b][sig] = i
                grava_snapshot(b, sig, tax, i, abrir)
            R["P2"][sig] = e
        ok["P2 A (sem sidecar == congelada) nos 7"] = all(e["A_igual"] for e in R["P2"].values())
        ok["P2 delta não vazio nos braços históricos"] = all(not e[b]["delta_vazio"] for e in R["P2"].values()
                                                            for b in ("VOCAB_ATUAL", "VOCAB_LLM"))
        ok["P2 B: diferenças só de ordem de aliases (inspeção integral)"] = all(
            e[b]["B_diagnostico"]["somente_ordem_de_aliases"] for e in R["P2"].values() for b in ("VOCAB_ATUAL", "VOCAB_LLM"))
        exige(ok["P2 A (sem sidecar == congelada) nos 7"], "equivalência A falhou; parar antes de qualquer avaliação")
        for b in ("CRU", "VOCAB_ATUAL", "VOCAB_LLM"):
            fecha_insumos(cong, b)
        K.grava_atomico(CONG, cong, abrir)

        # P4 captura CRU (processo isolado) e reprodução por ID
        cru, origem = roda_worker("CRU", "capturar", cong, travas)
        prob, difs = compara_referencia(cru, CAP_WAB)
        R["P4"] = {"origem": origem, "problemas_estrutura": prob, "divergencias": difs[:20], "n_divergencias": len(difs),
                   "conteudo_sha": cru["conteudo_sha"], "chamados": sum(1 for v in cru["decisoes"].values() for d in v.values() if d["chamado"]),
                   "nao_chamados_por_motivo": dict(collections.Counter(d["motivo_nao_chamado"] for v in cru["decisoes"].values()
                                                                      for d in v.values() if not d["chamado"])),
                   "taxonomia_congelada_lida": cru["verificacoes"]["taxonomia_congelada_lida"] != [],
                   "nao_chamados": [{"curso": s, "id": e, "motivo": d["motivo_nao_chamado"], "final": d["final"]}
                                    for s, v in cru["decisoes"].items() for e, d in sorted(v.items()) if not d["chamado"]]}
        ok["P4 CRU = referência por ID (conjuntos completos)"] = not prob and not difs

        # P3 controles (a partir das decisões do CRU desta execução)
        R["P3"], bloqueados = {}, []
        for sig, root in RAIZES.items():
            tax = sem[sig]
            ident = {k: r["add"] for k, r in rel_llm[sig].items() if r["add"]}
            grava_palco("_IDENTIDADE", sig, sidecar_de(ident, tax), abrir=abrir)
            com_id = reconstroi(M, root, PALCOS / "_IDENTIDADE" / K.NOMES[sig])
            idx_id = indice_unidade(M, root, PALCOS / "_IDENTIDADE" / K.NOMES[sig], com_id)
            vocab = read(SNAP / "VOCAB_LLM" / sig / "taxonomia.json")
            difC = diferencas_completas(vocab, com_id)
            rec = {"C_identidade": {"taxonomia_igual_ordenada": vocab == com_id, "n_diferencas": len(difC),
                                    "exemplos": difC[:5], "indice_igual": idx_id == idx["VOCAB_LLM"][sig]}}
            dec_cru = {e: d["final"] for e, d in cru["decisoes"][sig].items()}
            atrib, info = controle_maior(rel_llm[sig], tax, dec_cru)
            grava_palco("CTRL_MAIOR", sig, sidecar_de(atrib, tax), abrir=abrir)
            com = reconstroi(M, root, PALCOS / "CTRL_MAIOR" / K.NOMES[sig])
            grava_snapshot("CTRL_MAIOR", sig, com, indice_unidade(M, root, PALCOS / "CTRL_MAIOR" / K.NOMES[sig], com), abrir)
            rec["CTRL_MAIOR"] = {"definicao": info, "verificacao": verifica_controle(atrib, tax, com)}
            for b, s in K.SEMENTES.items():
                atrib, info, bloq = controle_aleatorio(rel_llm[sig], tax, sig, s)
                if bloq:
                    bloqueados.append(f"{b}/{sig}")
                grava_palco(b, sig, sidecar_de(atrib, tax), abrir=abrir)
                com = reconstroi(M, root, PALCOS / b / K.NOMES[sig])
                grava_snapshot(b, sig, com, indice_unidade(M, root, PALCOS / b / K.NOMES[sig], com), abrir)
                n_rel = sum(i["relacoes"] for i in info.values())
                rec[b] = {"unidades": info, "bloqueado": bloq,
                          "verificacao": verifica_controle(atrib, tax, com, vocab_rel=rel_llm[sig]),
                          "fracao_mudou_destino": sum(i["mudaram_de_destino"] for i in info.values()) / n_rel if n_rel else None}
            R["P3"][sig] = rec
        ok["P3 C: identidade == VOCAB_LLM (taxonomia ordenada e índice)"] = all(
            r["C_identidade"]["taxonomia_igual_ordenada"] and r["C_identidade"]["indice_igual"] for r in R["P3"].values())
        ok["P3 CTRL_MAIOR: pares, estrutura e remoções"] = all(r["CTRL_MAIOR"]["verificacao"]["aprovado"] for r in R["P3"].values())
        ok["P3 aleatórios: pares, contagem, multiconjunto, multiplicidade, sem duplicata/remoção"] = all(
            r[b]["verificacao"]["aprovado"] for r in R["P3"].values() for b in K.SEMENTES)
        ok["P3 nenhum aleatório bloqueado por orçamento"] = not bloqueados
        cong["controles"] = {"bloqueados": bloqueados}
        for b in ("CTRL_MAIOR", *K.SEMENTES):
            fecha_insumos(cong, b)
        K.grava_atomico(CONG, cong, abrir)

        # P5 carga isolada por braço
        R["P5"] = {}
        for b in K.BRACOS:
            c, origem = roda_worker(b, "carga", cong, travas)
            R["P5"][b] = {"origem": origem, "manual_carregado": c["verificacoes"]["manual_carregado"],
                          "temporais": c["verificacoes"]["artefatos_temporais_sha"],
                          "taxonomia_congelada_lida": c["verificacoes"]["taxonomia_congelada_lida"],
                          "unidades_motor_sha": K.sha_json({s: v["unidades_motor"] for s, v in c["por_curso"].items()}),
                          "taxonomia_sha": {s: v["taxonomia_sha"] for s, v in c["por_curso"].items()},
                          "indice_sha": {s: v["indice_sha"] for s, v in c["por_curso"].items()}}
        P5 = R["P5"]
        ok["P5 manual efetivamente carregado = mapa esperado"] = all(P5[b]["manual_carregado"] == K.MANUAL_ESPERADO[b] for b in K.BRACOS)
        ok["P5 artefatos temporais idênticos entre braços"] = len({K.sha_json(P5[b]["temporais"]) for b in K.BRACOS}) == 1
        ok["P5 braços não-CRU não leem a taxonomia congelada"] = all(not P5[b]["taxonomia_congelada_lida"] for b in K.BRACOS if b != "CRU")
        ok["P5 unidades do motor iguais entre braços"] = len({P5[b]["unidades_motor_sha"] for b in K.BRACOS}) == 1
        ok["P5 taxonomia e índice = snapshots congelados"] = all(
            P5[b]["taxonomia_sha"][s] == cong["insumos"][b][s]["taxonomia_sha"]
            and P5[b]["indice_sha"][s] == cong["insumos"][b][s]["indice_sha"] for b in K.BRACOS for s in K.NOMES)
        # entradas comuns iguais antes/depois
        depois = {sig: K.arvore(root, abrir) for sig, root in RAIZES.items()}
        ok["P5 entradas comuns iguais antes/depois"] = depois == arvores
        ok["P5 entradas externas iguais antes/depois"] = externas(manifestos, abrir, travas) == externos
        fim = K.verifica_codigo(codigo_inicio, CODIGO)
        ok["P5 código do harness, helpers e src/ iguais antes/depois"] = not fim and K.arvore(DATA / "src", abrir) == src_arquivos
        travas.rehash_leituras()
    except Exception as exc:  # noqa: BLE001  (qualquer falha interrompe com relatório e saída != 0)
        R["interrompido"] = f"{type(exc).__name__}: {exc}"
    ok["principal sem violações"] = not travas.violacoes
    R["violacoes_principal"] = travas.violacoes
    R["negados_principal"] = travas.negados
    R["condicoes"] = ok
    R["aprovado"] = bool(ok) and all(ok.values()) and "interrompido" not in R
    R["segundos"] = round(time.time() - T0, 1)
    K.grava_atomico(OUT_JSON, R, abrir)
    escreve_md(R, abrir)
    for k, v in ok.items():
        print(("OK    " if v else "FALHA ") + k, flush=True)
    if "interrompido" in R:
        print("INTERROMPIDO:", R["interrompido"], flush=True)
    print("PREFLIGHT", "APROVADO" if R["aprovado"] else "REPROVADO", round(time.time() - T0), "s", flush=True)
    K.encerra(travas, ok=R["aprovado"], codigo_falha=1)


def grava_snapshot(braco, sig, tax, idx, abrir):
    d = SNAP / braco / sig
    d.mkdir(parents=True, exist_ok=True)
    K.grava_atomico(d / "taxonomia.json", tax, abrir)
    K.grava_atomico(d / "indice_unidade.json", idx, abrir)


def fecha_insumos(cong, braco):
    ins = {}
    for sig in K.NOMES:
        d = SNAP / braco / sig
        tax, idx = read(d / "taxonomia.json"), read(d / "indice_unidade.json")
        ins[sig] = {"palco": arquivos_do_palco(braco, sig), "taxonomia_arquivo_sha": K.sha_arq(d / "taxonomia.json"),
                    "indice_arquivo_sha": K.sha_arq(d / "indice_unidade.json"), "taxonomia_sha": K.sha_json(tax),
                    "indice_sha": K.sha_json(idx)}
    cong["insumos"][braco] = ins
    cong["insumos_braco"][braco] = K.sha_json(ins)


def escreve_md(R, abrir):
    L = ["# W-AD4 — preflight v4 sem gold (25/09)", "", f"Congelamento comum: `{R.get('congelamento_id_comum', '—')}`.",
         f"Resultado: **{'APROVADO' if R['aprovado'] else 'REPROVADO'}**" + (f" — interrompido: {R['interrompido']}" if "interrompido" in R else ""),
         "", "## Condições", ""]
    L += [f"- {'✅' if v else '❌'} {k}" for k, v in R["condicoes"].items()]
    if "P2" in R:
        L += ["", "## P2 por curso", "", "| curso | A | B ATUAL só ordem | B LLM só ordem | +LLM | +ATUAL |", "|---|---|---|---|---:|---:|"]
        for s, e in R["P2"].items():
            L.append(f"| {s} | {e['A_igual']} | {e['VOCAB_ATUAL']['B_diagnostico']['somente_ordem_de_aliases']} | "
                     f"{e['VOCAB_LLM']['B_diagnostico']['somente_ordem_de_aliases']} | {e['VOCAB_LLM']['aliases_add']} | {e['VOCAB_ATUAL']['aliases_add']} |")
    if "P3" in R:
        L += ["", "## P3 por curso", "", "| curso | C taxonomia | C índice | MAIOR | ALEAT 1/2/3 | estados das unidades (3 sementes) |", "|---|---|---|---|---|---|"]
        for s, r in R["P3"].items():
            est = collections.Counter(i["estado"] for b in K.SEMENTES for i in r[b]["unidades"].values())
            L.append(f"| {s} | {r['C_identidade']['taxonomia_igual_ordenada']} | {r['C_identidade']['indice_igual']} | "
                     f"{r['CTRL_MAIOR']['verificacao']['aprovado']} | {'/'.join(str(r[b]['verificacao']['aprovado']) for b in K.SEMENTES)} | {dict(est)} |")
    if "P4" in R:
        p = R["P4"]
        L += ["", "## P4", "", f"- CRU ({p['origem']}): problemas de estrutura {len(p['problemas_estrutura'])}, divergências {p['n_divergencias']}, "
              f"chamados {p['chamados']}, não chamados por motivo {p['nao_chamados_por_motivo']}."]
        L += ["", "Não chamados do CRU (motivo do harness; `nao_identificado` = sem evidência suficiente para outro motivo):", ""]
        L += [f"- {x['curso']}/{x['id']}: {x['motivo']}; final unidade={x['final']['unidade']!r}, sub={x['final']['sub']!r}, "
              f"motivos_sub={x['final']['motivos_sub']}, motivos_unidade={x['final']['motivos_unidade']}"
              for x in p["nao_chamados"]]
    with abrir(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    argv = sys.argv[1:]
    if "--controlado" not in argv:
        # Relança com ambiente controlado, sem bytecode em cache e sem site de usuário, antes de qualquer trava ou import
        # do produto. Nenhum valor do ambiente do terminal é copiado além das variáveis de sistema herdáveis (nomes).
        PYCACHE.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, "-B", "-X", f"pycache_prefix={PYCACHE}", str(Path(__file__).resolve()), *argv, "--controlado"]
        sys.exit(subprocess.run(cmd, env=K.ambiente_controlado(os.environ)).returncode)
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--braco")
    ap.add_argument("--modo")
    ap.add_argument("--controlado", action="store_true")
    a = ap.parse_args(argv)
    if a.worker:
        worker(a.braco, a.modo)
    elif a.preflight:
        preflight()
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
