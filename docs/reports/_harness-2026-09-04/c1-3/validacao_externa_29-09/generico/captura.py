"""Harness genérico (validação externa, 29/09): preflight SEM GOLD e captura isolada por braço, para qualquer rodada.

Cópia do captura.py da rodada VOCAB_LIMPO (../../vocab_limpo_26-09/captura.py) com SÓ: cursos, raízes, braços,
tutores proibidos, caminhos, protocolo, régua e referência do CRU lidos da configuração da rodada (`rodada.py`);
literais de braço trocados pelos papéis (K.CRU, K.CANDIDATO, K.CTRL_MAIOR, K.CTRL_ALEAT); e, quando a rodada não tem
referência publicada do CRU (cursos novos), o P4 registra a captura sem comparação e a fase de captura recaptura o CRU
num worker novo, exigindo decisões idênticas por ID às do preflight (controle de determinismo no lugar da referência).
Nunca lê gold: não importa módulos de avaliação; as travas (comum.Travas) invalidam qualquer acesso proibido, mesmo
quando uma camada intermediária engole a exceção.

Garantia "código executado = código validado" (estratégia declarada): o processo se relança com ambiente controlado,
`-B` e `-X pycache_prefix=<área vazia isolada>` (compila sempre a partir do fonte, sem bytecode em cache); os hashes do
harness, dos helpers e de todo `src/` são conferidos ANTES dos imports do produto e de novo no fim; DEPOIS dos imports,
a origem (`__file__`) e o hash de cada módulo `src.*` e dos helpers carregados são conferidos contra o congelamento.
A assinatura das distribuições instaladas é recalculada e conferida no início e no fim de cada worker e pelo
coordenador antes de aceitar; o inventário congelado inteiro (pacotes, externos, palco e snapshots do braço) também.

Uso:
  python -B captura.py --preflight          P0-P5 sem gold; grava preflight_v5.{json,md} e o congelamento.
  python -B captura.py --capturar           exige preflight v5 aprovado; captura os seis braços em sequência e valida
                                            as sete capturas; grava manifesto_capturas_v5.json. Não lê gold.
  python -B captura.py --worker ...         uso interno (processo isolado por braço).
Braços liberados em comum.CAPTURA_LIBERADA, conferidos antes de lançar, de reutilizar e de aceitar.
"""
import argparse
import collections
import copy
import functools
import json
import os
import platform
import re
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
C13 = HERE.parents[1]   # pasta c1-3 (o genérico fica um nível abaixo)
DATA = HERE.parents[5]
ORIG = DATA.parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(DATA))   # src/ importável (import tardio, depois das travas e das verificações)
import comum as K  # noqa: E402  (só stdlib)

AMBIENTE_INICIAL = dict(os.environ)   # antes de qualquer import do produto, que grava em os.environ (TESSDATA_PREFIX)

RODADA = K.R
BASE = DATA / RODADA.CFG["saida_base"]
PALCOS, SNAP, CAPS, FALHAS = BASE / "palcos", BASE / "snapshots", BASE / "capturas", BASE / "falhas"
PYCACHE = BASE / "pycache_vazio"
CONG = BASE / "congelamento.json"
CONG_ENTRADAS = BASE / "congelamento_entradas.json"
ADENDO = DATA / RODADA.CFG["protocolo"]
VL = DATA / RODADA.CFG["recompilacao"]          # recompilação congelada do candidato (sidecars, compilação, sanidade)
VL_SIDECARS, VL_SANIDADE, VL_COMP, VL_CONG = VL / "sidecars", VL / "sanidade.json", VL / "compilacao.json", VL / "congelamento_recompilacao.json"
PROIBIDOS_RODADA = {DATA / p: m for p, m in RODADA.CFG["proibidos"].items()}
CAP_WAB = DATA / RODADA.CFG["referencia_cru"]["arquivo"] if RODADA.CFG["referencia_cru"] else None   # None = sem referência
SUF = RODADA.CFG["sufixo"]
OUT_JSON, OUT_MD = HERE / f"preflight_{SUF}.json", HERE / f"preflight_{SUF}.md"
OUT_CAP_JSON, OUT_CAP_MD = HERE / f"manifesto_capturas_{SUF}.json", HERE / f"capturas_{SUF}.md"
ORDEM_CAPTURA = (K.CANDIDATO, K.CTRL_MAIOR, *K.CTRL_ALEAT)
BASE_PRETENDIDA = RODADA.CFG["base_produto"]
HELPERS = {"replay_bloco_21-09.py": C13 / "replay_bloco_21-09.py", "replay_unidade_21-09.py": C13 / "replay_unidade_21-09.py"}
CODIGO = {"captura.py": HERE / "captura.py", "comum.py": HERE / "comum.py", "avaliador.py": HERE / "avaliador.py",
          "rodada.py": HERE / "rodada.py", "rodada_config.json": RODADA.CAMINHO, "gold_externo.py": HERE / "gold_externo.py",
          "test_wad4.py": HERE / "test_wad4.py", "test_defeitos_v4.py": HERE / "test_defeitos_v4.py",
          "test_ajustes_v5.py": HERE / "test_ajustes_v5.py", "test_generico.py": HERE / "test_generico.py", **HELPERS}
LLM, MANUAL = ".glossary_curation.llm.json", ".glossary_curation.json"
TUTORES = list(K.NOMES.values()) + list(RODADA.CFG["tutores_proibidos"])
RAIZES = {c["sigla"]: DATA / c["raiz_pacote"] for c in RODADA.CFG["cursos"]}
TENTATIVAS_ALEAT = 2000
ARTEFATOS_TEMPORAIS = (".timeline_index.json", ".card_block_map.json", ".lessons_index.json")
# Proveniência da avaliação (§7): caminhos EXPLÍCITOS da configuração da rodada. Nada é aberto aqui: blob IDs vêm do índice.
UNI = tuple(s for s in K.NOMES if s in RODADA.UNI)
REGUA_ARQUIVOS = {papel: dict(m) for papel, m in RODADA.CFG["regua"]["arquivos"].items()}
REGUA_MANIFESTOS = dict(RODADA.CFG["regua"]["manifestos"])
REGUA_CODIGO = dict(RODADA.CFG["regua"]["codigo"])

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
    for alvo, motivo in PROIBIDOS_RODADA.items():
        t.proibe(alvo, motivo)
    return t


def travas_principal():
    """Configuração das travas do processo principal (não instala). Código somente leitura; relatórios nomeados."""
    t = K.Travas("principal")
    t.permite("codigo", *raizes_codigo(), *HELPERS.values(), somente_leitura=True)
    t.permite("protocolo", ADENDO, somente_leitura=True)
    t.permite("comum", *RAIZES.values(), somente_leitura=True)
    t.permite("preparo", *[ORIG / n / "course" for n in TUTORES], somente_leitura=True)
    t.permite("referencia", *([CAP_WAB] if CAP_WAB else []), *[DATA / p for p in REGUA_MANIFESTOS.values()], VL_SIDECARS, VL_SANIDADE, VL_COMP,
              VL_CONG, somente_leitura=True)
    t.permite("saida", BASE, OUT_JSON, OUT_MD)
    t.nega(DATA / ".env", "arquivo .env da raiz (pode conter segredos e configuração)")
    for alvo, motivo in PROIBIDOS_RODADA.items():
        t.proibe(alvo, motivo)
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
        prob += verifica_distribuicoes(cong)
    return prob


def verifica_distribuicoes(cong):
    """Assinatura das distribuições instaladas (mesmo procedimento do congelamento: sha_json(distribuicoes())) contra o
    valor congelado. Ausente, inválido ou divergente reprova; o esperado nunca é preenchido com o valor atual."""
    esperado = ((cong.get("normativo") or {}).get("interprete") or {}).get("distribuicoes_sha")
    if not isinstance(esperado, str) or not re.fullmatch(r"[0-9a-f]{64}", esperado):
        return ["assinatura das distribuições ausente ou inválida no congelamento"]
    if K.sha_json(distribuicoes()) != esperado:
        return ["distribuições instaladas divergem da assinatura congelada"]
    return []


def verifica_fim(cong):
    """Fim do worker, antes de aceitar a captura: código, src/ e distribuições ainda iguais ao congelamento."""
    fim = K.verifica_codigo(cong["normativo"]["codigo"], CODIGO)
    if K.arvore(DATA / "src") != cong["normativo"]["produto"]["src_arquivos"]:
        fim.append("src/ mudou durante a execução")
    return fim + verifica_distribuicoes(cong)


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
    out = {"_provenance": "controle-wad3", "_nota": "reendereçamento das relações efetivas do candidato (adendo v2 §4)"}
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
            travas.congela(PALCOS / braco / K.NOMES[sig], ins[sig]["palco"])
            travas.congela(SNAP / braco / sig, {"taxonomia.json": ins[sig]["taxonomia_arquivo_sha"],
                                                "indice_unidade.json": ins[sig]["indice_arquivo_sha"]})
        faltam = travas.confere_congelados()   # inventário esperado inteiro, antes de qualquer import do produto
        exige(not faltam, f"inventário congelado não confere antes do worker: {faltam[:4]}")
        M = modulos(travas, cong["normativo"]["produto"]["src_arquivos"])
        cap = executa(M, travas, braco, modo, cong, ins)
        cap["verificacoes"]["modulos_src_verificados"] = M.n_modulos_src
        cap["verificacoes"]["inventario_congelado_conferido"] = len(travas.congelados)
        fim = verifica_fim(cong)
        exige(not fim, f"código, src/ ou distribuições mudaram durante a execução: {fim[:4]}")
        travas.rehash_leituras()   # leituras + inventário congelado inteiro
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
        if braco != K.CRU:
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
        dist = verifica_distribuicoes(cong)
        exige(not dist, f"captura em cache de {braco}/{modo} não reutilizada: {dist}")
        return cap, "reutilizada"
    cmd = [sys.executable, "-B", "-X", f"pycache_prefix={PYCACHE}", str(HERE / "captura.py"), "--worker",
           "--braco", braco, "--modo", modo, "--controlado"]
    with travas.comandos({Path(sys.executable).name}):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=K.ambiente_controlado(AMBIENTE_INICIAL))
    exige(r.returncode == 0, f"worker {braco}/{modo} saiu {r.returncode}: {r.stdout[-600:]} {r.stderr[-900:]}")
    dist = verifica_distribuicoes(cong)
    if dist:   # mudou durante o worker: a captura sai do caminho de reúso e fica preservada como falha
        FALHAS.mkdir(parents=True, exist_ok=True)
        if destino.exists():
            destino.replace(FALHAS / f"rejeitada_{destino.name}")
        raise Falha(f"captura de {braco}/{modo} recusada: {dist}")
    cap = read(destino)
    prob = K.valida_captura(cap, congelamento=cong, braco=braco, modo=modo)
    exige(not prob, f"captura de {braco}/{modo} inválida: {prob[:4]}")
    exige(modo != "capturar" or cap.get("braco") in K.CAPTURA_LIBERADA, "aceitação recusada: braço não autorizado")
    return cap, "nova"


def confere_determinismo_cru(anterior, novo):
    """Rodada sem referência publicada: a recaptura do CRU tem de repetir, por ID, todas as decisões do preflight."""
    prob = []
    if anterior.get("braco") != novo.get("braco") or anterior.get("insumos_braco") != novo.get("insumos_braco"):
        prob.append("braço ou insumos diferentes")
    if set(anterior.get("decisoes") or {}) != set(novo.get("decisoes") or {}):
        prob.append("cursos diferentes")
    for sig in sorted(set(anterior.get("decisoes") or {}) & set(novo.get("decisoes") or {})):
        a, b = anterior["decisoes"][sig], novo["decisoes"][sig]
        if set(a) != set(b):
            prob.append(f"{sig}: IDs diferentes")
        prob += [f"{sig}/{e}: decisão diferente" for e in sorted(set(a) & set(b)) if K.sha_json(a[e]) != K.sha_json(b[e])]
    return prob


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
        print(f"{OUT_JSON.name} já existe: preservar evidência (usar nova versão)", flush=True)
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

        # P1 fonte do VOCAB_LIMPO: sidecars da recompilação limpa congelada (tutores vivos NÃO são lidos)
        travas.permitidos.pop("preparo")
        for nome in TUTORES:
            travas.proibe(ORIG / nome, "tutor vivo (rodada limpa não lê tutores vivos)")
        san, comp, vlc = read(VL_SANIDADE), read(VL_COMP), read(VL_CONG)
        exige(san["aprovado"] is True and comp["completa"] is True and san["id_recompilacao"] == comp["id_recompilacao"]
              == vlc["id_recompilacao"], "recompilação limpa incompleta, reprovada ou de outro congelamento")
        limpo = {}
        for sig in K.NOMES:
            p = VL_SIDECARS / K.NOMES[sig] / LLM
            exige(K.sha_arq(p, abrir) == san["sidecars"][sig]["sha256"], f"{sig}: sidecar {K.CANDIDATO} != congelado")
            limpo[sig] = read(p)
        R["P1_vocab_limpo"] = {"id_recompilacao": vlc["id_recompilacao"], "sidecars": san["sidecars"]}
        for sig in K.NOMES:
            grava_palco(K.CRU, sig, abrir=abrir)
            grava_palco(K.CANDIDATO, sig, limpo[sig], abrir=abrir)
        manual_real = {b: {s: (PALCOS / b / K.NOMES[s] / "course" / MANUAL).exists() for s in K.NOMES} for b in K.BRACOS}
        ok["P1 nenhum manual em nenhum palco (mapa declarado)"] = manual_real == K.MANUAL_ESPERADO
        exige(ok["P1 nenhum manual em nenhum palco (mapa declarado)"], "manual presente em algum palco")

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
            "referencias": {CAP_WAB.name: K.sha_arq(CAP_WAB, abrir)} if CAP_WAB else {},
            "vocab_limpo": {"id_recompilacao": vlc["id_recompilacao"], "sidecars": san["sidecars"],
                            "compilacao_sha256": K.sha_arq(VL_COMP, abrir), "sanidade_sha256": K.sha_arq(VL_SANIDADE, abrir),
                            "congelamento_recompilacao_sha256": K.sha_arq(VL_CONG, abrir)},
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
            sem[sig] = reconstroi(M, root, PALCOS / K.CRU / K.NOMES[sig])
            difA = diferencas_completas(congelada[sig], sem[sig])
            e = {"A_igual": congelada[sig] == sem[sig], "A_n_diferencas": len(difA), "A_exemplos": difA[:5]}
            snaps = {K.CRU: congelada[sig]}
            for b in (K.CANDIDATO,):
                com = reconstroi(M, root, PALCOS / b / K.NOMES[sig])
                rel = relacoes(com, sem[sig])
                if b == K.CANDIDATO:
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
        ok[f"P2 delta não vazio no {K.CANDIDATO}"] = all(not e[b]["delta_vazio"] for e in R["P2"].values()
                                                     for b in (K.CANDIDATO,))
        ok["P2 B: diferenças só de ordem de aliases (inspeção integral)"] = all(
            e[b]["B_diagnostico"]["somente_ordem_de_aliases"] for e in R["P2"].values() for b in (K.CANDIDATO,))
        exige(ok["P2 A (sem sidecar == congelada) nos 7"], "equivalência A falhou; parar antes de qualquer avaliação")
        for b in (K.CRU, K.CANDIDATO):
            fecha_insumos(cong, b)
        K.grava_atomico(CONG, cong, abrir)

        # P4 captura CRU (processo isolado) e reprodução por ID
        cru, origem = roda_worker(K.CRU, "capturar", cong, travas)
        # sem referência publicada (cursos novos): o determinismo do CRU é exigido na fase de captura (recaptura)
        prob, difs = compara_referencia(cru, CAP_WAB) if CAP_WAB else ([], [])
        R["P4"] = {"referencia": CAP_WAB.name if CAP_WAB else None, "origem": origem, "problemas_estrutura": prob, "divergencias": difs[:20], "n_divergencias": len(difs),
                   "conteudo_sha": cru["conteudo_sha"], "chamados": sum(1 for v in cru["decisoes"].values() for d in v.values() if d["chamado"]),
                   "nao_chamados_por_motivo": dict(collections.Counter(d["motivo_nao_chamado"] for v in cru["decisoes"].values()
                                                                      for d in v.values() if not d["chamado"])),
                   "taxonomia_congelada_lida": cru["verificacoes"]["taxonomia_congelada_lida"] != [],
                   "nao_chamados": [{"curso": s, "id": e, "motivo": d["motivo_nao_chamado"], "final": d["final"]}
                                    for s, v in cru["decisoes"].items() for e, d in sorted(v.items()) if not d["chamado"]]}
        ok["P4 CRU = referência por ID (conjuntos completos)" if CAP_WAB else
           "P4 CRU capturado (sem referência publicada; determinismo exigido na captura)"] = not prob and not difs

        # P3 controles (a partir das decisões do CRU desta execução)
        R["P3"], bloqueados = {}, []
        for sig, root in RAIZES.items():
            tax = sem[sig]
            ident = {k: r["add"] for k, r in rel_llm[sig].items() if r["add"]}
            grava_palco("_IDENTIDADE", sig, sidecar_de(ident, tax), abrir=abrir)
            com_id = reconstroi(M, root, PALCOS / "_IDENTIDADE" / K.NOMES[sig])
            idx_id = indice_unidade(M, root, PALCOS / "_IDENTIDADE" / K.NOMES[sig], com_id)
            vocab = read(SNAP / K.CANDIDATO / sig / "taxonomia.json")
            difC = diferencas_completas(vocab, com_id)
            rec = {"C_identidade": {"taxonomia_igual_ordenada": vocab == com_id, "n_diferencas": len(difC),
                                    "exemplos": difC[:5], "indice_igual": idx_id == idx[K.CANDIDATO][sig]}}
            dec_cru = {e: d["final"] for e, d in cru["decisoes"][sig].items()}
            atrib, info = controle_maior(rel_llm[sig], tax, dec_cru)
            grava_palco(K.CTRL_MAIOR, sig, sidecar_de(atrib, tax), abrir=abrir)
            com = reconstroi(M, root, PALCOS / K.CTRL_MAIOR / K.NOMES[sig])
            grava_snapshot(K.CTRL_MAIOR, sig, com, indice_unidade(M, root, PALCOS / K.CTRL_MAIOR / K.NOMES[sig], com), abrir)
            rec[K.CTRL_MAIOR] = {"definicao": info, "verificacao": verifica_controle(atrib, tax, com)}
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
        ok[f"P3 C: identidade == {K.CANDIDATO} (taxonomia ordenada e índice)"] = all(
            r["C_identidade"]["taxonomia_igual_ordenada"] and r["C_identidade"]["indice_igual"] for r in R["P3"].values())
        ok[f"P3 {K.CTRL_MAIOR}: pares, estrutura e remoções"] = all(r[K.CTRL_MAIOR]["verificacao"]["aprovado"] for r in R["P3"].values())
        ok["P3 aleatórios: pares, contagem, multiconjunto, multiplicidade, sem duplicata/remoção"] = all(
            r[b]["verificacao"]["aprovado"] for r in R["P3"].values() for b in K.SEMENTES)
        ok["P3 nenhum aleatório bloqueado por orçamento"] = not bloqueados
        cong["controles"] = {"bloqueados": bloqueados}
        for b in (K.CTRL_MAIOR, *K.SEMENTES):
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
        ok["P5 braços não-CRU não leem a taxonomia congelada"] = all(not P5[b]["taxonomia_congelada_lida"] for b in K.BRACOS if b != K.CRU)
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
        ok["P5 distribuições iguais à assinatura congelada"] = not verifica_distribuicoes(cong)
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


def capturar_bracos():
    """Gate de captura: exige o preflight v5 aprovado com este mesmo congelamento; captura os seis braços não-CRU em
    sequência (um worker isolado por braço), valida o conjunto das sete capturas com o validador completo e grava o
    manifesto final. Não lê gold, não calcula acerto nem compara braços."""
    platform.uname()
    platform.platform()   # aquece o cache antes das travas
    travas = travas_principal()
    travas.permitidos.pop("preparo")   # nesta etapa o coordenador não lê tutores vivos
    for nome in TUTORES:
        travas.proibe(ORIG / nome, "tutor vivo")
    travas.permite("referencia", CONG, CONG_ENTRADAS, OUT_JSON, somente_leitura=True)
    travas.permite("saida", OUT_CAP_JSON, OUT_CAP_MD)
    travas.instala()
    abrir = travas._abrir_original
    R, ok = {"escopo": "captura dos cinco braços não-CRU da rodada limpa e validação das seis capturas; sem gold"}, {}
    if OUT_CAP_JSON.exists():   # nunca sobrescrever evidência anterior
        print(f"{OUT_CAP_JSON.name} já existe: preservar evidência", flush=True)
        sys.exit(1)
    try:
        cong = read(CONG)
        entradas = read(CONG_ENTRADAS)
        pf = read(OUT_JSON)
        R["congelamento_id_comum"] = cong["id_comum"]
        prob = K.valida_congelamento(cong) + verifica_processo(cong)
        if K.sha_json(entradas) != cong["normativo"]["entradas_arquivo_sha"]:
            prob.append("congelamento de entradas divergente")
        R["pre_condicoes"] = prob
        ok["preflight da rodada aprovado com este congelamento"] = (pf.get("aprovado") is True
                                                             and pf.get("congelamento_id_comum") == cong["id_comum"])
        ok["processo, código, src/ e distribuições = congelamento (início)"] = not prob
        ok["CAPTURA_LIBERADA = os seis braços da rodada"] = K.CAPTURA_LIBERADA == frozenset(K.BRACOS)
        exige(all(ok.values()), f"pré-condições da captura não atendidas: {prob[:4]}")
        for sig, root in RAIZES.items():
            travas.congela(root, entradas[sig])
        travas.congela_arquivos(entradas["_externos"])
        faltam = travas.confere_congelados()
        ok["inventário de entradas confere (início)"] = not faltam
        exige(not faltam, f"inventário de entradas não confere: {faltam[:4]}")

        caps, R["bracos"] = {}, {}
        for b in (K.CRU, *ORDEM_CAPTURA):   # o CRU é o do preflight desta rodada (mesmo congelamento), revalidado
            exige(not verifica_distribuicoes(cong), f"distribuições divergem antes de {b}")
            if b == K.CRU and CAP_WAB is None:
                # rodada sem referência publicada: preserva o CRU do preflight e recaptura num worker novo
                destino_cru = CAPS / f"capturar_{b}_{cong['id_comum'][:16]}_{cong['insumos_braco'][b][:16]}.json"
                preservado = CAPS / f"preflight_{destino_cru.name}"
                exige(destino_cru.exists() and not preservado.exists(), "CRU do preflight ausente ou já preservado")
                anterior = read(destino_cru)
                destino_cru.replace(preservado)
                caps[b], origem = roda_worker(b, "capturar", cong, travas)
                det = confere_determinismo_cru(anterior, caps[b])
                R["determinismo_cru"] = {"preservado": preservado.name, "problemas": det}
                ok["CRU recapturado = CRU do preflight (decisões por ID)"] = not det
                exige(not det, f"CRU não determinístico: {det[:3]}")
            else:
                caps[b], origem = roda_worker(b, "capturar", cong, travas)
            R["bracos"][b] = {"origem": origem}
            print("  captura", b, origem, round(time.time() - T0), "s", flush=True)

        # conferência final do conjunto (sem gold)
        destinos = {b: CAPS / f"capturar_{b}_{cong['id_comum'][:16]}_{cong['insumos_braco'][b][:16]}.json" for b in K.BRACOS}
        prob_conj = {b: K.valida_historica(caps[b], cong, braco=b) for b in K.BRACOS}
        ok["seis capturas completas, validador completo sem problemas"] = (set(caps) == set(K.BRACOS)
                                                                            and not any(prob_conj.values()))
        ok["350 registros por captura, IDs = inventário congelado"] = all(
            sum(len(v) for v in c["decisoes"].values()) == K.INVENTARIO_ESPERADO
            and {s: sorted(v) for s, v in c["decisoes"].items()} == cong["normativo"]["inventario"] for c in caps.values())
        ok["mesmo congelamento comum e insumos do próprio braço"] = all(
            c["congelamento_comum"] == cong["id_comum"] and c["insumos_braco"] == cong["insumos_braco"][b]
            and c["esquema"] == K.ESQUEMA_CAPTURA and c["modo"] == "capturar" and c["braco"] == b for b, c in caps.items())
        ok["nenhuma violação nas capturas"] = all(c["violacoes"] == [] for c in caps.values())
        ok["arquivos de captura = conteúdo validado"] = all(read(destinos[b])["conteudo_sha"] == caps[b]["conteudo_sha"]
                                                          for b in K.BRACOS)
        ok["palcos e snapshots = insumos congelados (fim)"] = all(
            arquivos_do_palco(b, s) == cong["insumos"][b][s]["palco"]
            and K.sha_arq(SNAP / b / s / "taxonomia.json", abrir) == cong["insumos"][b][s]["taxonomia_arquivo_sha"]
            and K.sha_arq(SNAP / b / s / "indice_unidade.json", abrir) == cong["insumos"][b][s]["indice_arquivo_sha"]
            for b in K.BRACOS for s in K.NOMES)
        fim = verifica_fim(cong)
        ok["código, src/ e distribuições = congelamento (fim)"] = not fim
        ok["entradas comuns preservadas (árvores inteiras)"] = all(K.arvore(root, abrir) == entradas[s] for s, root in RAIZES.items())
        ok["inventário de entradas confere (fim)"] = not travas.confere_congelados()
        R["problemas_por_braco"] = prob_conj
        R["fim"] = fim
        R["capturas"] = {b: {"arquivo": destinos[b].relative_to(DATA).as_posix(), "sha256": K.sha_arq(destinos[b], abrir),
                             "conteudo_sha": c["conteudo_sha"], "origem": R["bracos"][b]["origem"],
                             "materiais": sum(len(v) for v in c["decisoes"].values()),
                             "chamados": sum(1 for v in c["decisoes"].values() for d in v.values() if d["chamado"]),
                             "nao_chamados": sum(1 for v in c["decisoes"].values() for d in v.values() if not d["chamado"]),
                             "violacoes": len(c["violacoes"]), "negados": sorted({Path(n["caminho"]).name for n in c["negados"]}),
                             "manual_carregado": sorted(s for s, v in c["verificacoes"]["manual_carregado"].items() if v),
                             "inventario_congelado_conferido": c["verificacoes"].get("inventario_congelado_conferido"),
                             "segundos": c.get("segundos")}
                         for b, c in caps.items()}
        R["referencias"] = {
            "protocolo": {"arquivo": ADENDO.relative_to(DATA).as_posix(), "sha256": K.sha_arq(ADENDO, abrir),
                          "protocolo_sha_normativo": cong["normativo"]["protocolo_sha"]},
            "congelamento": {"arquivo": CONG.relative_to(DATA).as_posix(), "sha256": K.sha_arq(CONG, abrir)},
            "congelamento_entradas": {"arquivo": CONG_ENTRADAS.relative_to(DATA).as_posix(), "sha256": K.sha_arq(CONG_ENTRADAS, abrir)},
            "preflight": {"arquivo": OUT_JSON.relative_to(DATA).as_posix(), "sha256": K.sha_arq(OUT_JSON, abrir)},
            "codigo": cong["normativo"]["codigo"], "produto_src_arvore_sha": cong["normativo"]["produto"]["src_arvore_sha"],
            "interprete": {k: v for k, v in cong["normativo"]["interprete"].items() if k != "estrategia"},
            "ambiente": cong["normativo"]["ambiente"], "insumos_braco": cong["insumos_braco"],
            "snapshots": {b: {s: {k: v[k] for k in ("taxonomia_arquivo_sha", "indice_arquivo_sha")} for s, v in ins.items()}
                          for b, ins in cong["insumos"].items()}}
        travas.rehash_leituras()
    except Exception as exc:  # noqa: BLE001  (qualquer falha interrompe com relatório e saída != 0)
        R["interrompido"] = f"{type(exc).__name__}: {exc}"
    ok["coordenador sem violações"] = not travas.violacoes
    R["violacoes_coordenador"] = travas.violacoes
    R["negados_coordenador"] = travas.negados
    R["condicoes"] = ok
    R["aprovado"] = bool(ok) and all(ok.values()) and "interrompido" not in R
    R["segundos"] = round(time.time() - T0, 1)
    K.grava_atomico(OUT_CAP_JSON, R, abrir)
    L = [f"# Rodada {SUF} — captura dos braços, sem gold", "", f"Congelamento comum: `{R.get('congelamento_id_comum', '—')}`.",
         f"Resultado: **{'APROVADO' if R['aprovado'] else 'REPROVADO'}**"
         + (f" — interrompido: {R['interrompido']}" if "interrompido" in R else ""), "", "## Condições", ""]
    L += [f"- {'✅' if v else '❌'} {k}" for k, v in ok.items()]
    if "capturas" in R:
        L += ["", "## Capturas", "", "| braço | origem | materiais | chamados | não chamados | violações | manual | conteudo_sha | sha256 do arquivo |",
              "|---|---|---:|---:|---:|---:|---|---|---|"]
        L += [f"| {b} | {c['origem']} | {c['materiais']} | {c['chamados']} | {c['nao_chamados']} | {c['violacoes']} | "
              f"{', '.join(c['manual_carregado']) or '—'} | `{c['conteudo_sha']}` | `{c['sha256']}` |" for b, c in R["capturas"].items()]
    with abrir(OUT_CAP_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    for k, v in ok.items():
        print(("OK    " if v else "FALHA ") + k, flush=True)
    if "interrompido" in R:
        print("INTERROMPIDO:", R["interrompido"], flush=True)
    print("CAPTURA", "APROVADA" if R["aprovado"] else "REPROVADA", round(time.time() - T0), "s", flush=True)
    K.encerra(travas, ok=R["aprovado"], codigo_falha=1)


def escreve_md(R, abrir):
    L = [f"# Rodada {SUF} — preflight sem gold", "", f"Congelamento comum: `{R.get('congelamento_id_comum', '—')}`.",
         f"Resultado: **{'APROVADO' if R['aprovado'] else 'REPROVADO'}**" + (f" — interrompido: {R['interrompido']}" if "interrompido" in R else ""),
         "", "## Condições", ""]
    L += [f"- {'✅' if v else '❌'} {k}" for k, v in R["condicoes"].items()]
    if "P2" in R:
        L += ["", "## P2 por curso", "", "| curso | A | B candidato só ordem | +candidato | -candidato |", "|---|---|---|---:|---:|"]
        for s, e in R["P2"].items():
            L.append(f"| {s} | {e['A_igual']} | {e[K.CANDIDATO]['B_diagnostico']['somente_ordem_de_aliases']} | "
                     f"{e[K.CANDIDATO]['aliases_add']} | {e[K.CANDIDATO]['aliases_rem']} |")
    if "P3" in R:
        L += ["", "## P3 por curso", "", "| curso | C taxonomia | C índice | MAIOR | ALEAT 1/2/3 | estados das unidades (3 sementes) |", "|---|---|---|---|---|---|"]
        for s, r in R["P3"].items():
            est = collections.Counter(i["estado"] for b in K.SEMENTES for i in r[b]["unidades"].values())
            L.append(f"| {s} | {r['C_identidade']['taxonomia_igual_ordenada']} | {r['C_identidade']['indice_igual']} | "
                     f"{r[K.CTRL_MAIOR]['verificacao']['aprovado']} | {'/'.join(str(r[b]['verificacao']['aprovado']) for b in K.SEMENTES)} | {dict(est)} |")
    if "P4" in R:
        p = R["P4"]
        L += ["", "## P4", "", f"- {K.CRU} ({p['origem']}): problemas de estrutura {len(p['problemas_estrutura'])}, divergências {p['n_divergencias']}, "
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
    ap.add_argument("--capturar", action="store_true")
    ap.add_argument("--controlado", action="store_true")
    a = ap.parse_args(argv)
    if a.worker:
        worker(a.braco, a.modo)
    elif a.capturar:
        capturar_bracos()
    elif a.preflight:
        preflight()
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
