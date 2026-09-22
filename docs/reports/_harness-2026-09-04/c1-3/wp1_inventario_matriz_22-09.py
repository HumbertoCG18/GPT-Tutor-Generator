"""W-P1 (CRU-02): inventario dos 251 da regua de subunidade, residual em 4 classes,
matriz de evidencias expressao->material e ordem das perguntas ao professor.

Read-only: nao toca src/, nao faz build, rede nem LLM. Gold SO AVALIA (coluna "certo?" do
inventario e classes do residual); a selecao de expressoes e a ordem das perguntas sao
calculadas ANTES de carregar o gold e congeladas por sha256 (`congelamento_sha256`).

DEFINICOES PRE-DECLARADAS (congeladas antes do gold)

(A) Expressao candidata = n-grama de 1 a 3 tokens sobre `normalize_match_text`, extraida de
    5 campos: `titulo`, `arquivo` (stem de source_path, nunca de URL), `moodle_label`,
    `heading` (linhas iniciadas por `#` do markdown via `_entry_markdown_text_for_file_map`)
    e `code_curation` (PRIMEIRA linha de `code_curation_signal_text`). O corpo do markdown
    NAO entra. Tokens genericos/stopwords sao REMOVIDOS da sequencia (nao a quebram): assim
    "arvore de decisao" -> ["arvore","decisao"] e o bigrama sobrevive. Token valido =
    somente letras a-z e len >= 4, fora de UNIT_GENERIC_TOKENS, UNIT_STRUCTURAL_TOKENS,
    TOPIC_FALLBACK_STOPWORDS e fora de qualquer prefixo de MOTOR_GENERIC_STEMS.
    Agrupamento de variantes lexicais: chave = tokens truncados em 6 caracteres (stem6),
    juntos por espaco. Nunca por sinonimo.
(B) Ocorrencia = (chave da expressao, material, campo, trecho literal <= 120 caracteres do
    texto CRU daquele campo).
(C) "Relacao ja conhecida" = a chave da expressao e um n-grama contiguo (1-3) da forma
    filtrada+stem6 do label ou de um alias de algum topico da taxonomia do curso
    (`course/.content_taxonomy.json`). Essas expressoes NAO viram pergunta; ficam em
    `expressoes_conhecidas` com os slugs de topico que ja as cobrem.
(D) Cobertura marginal = materiais adicionais do curso (universo = os materiais da regua de
    subunidade daquele curso presentes no pacote) que a expressao alcanca, descontados os ja
    cobertos por perguntas anteriores. Empate -> mais ocorrencias em titulo/heading, depois
    ordem alfabetica da chave. Cobertura e de OCORRENCIAS, nao de erros; nenhum uso de gold.
    Pergunta = (curso, expressao, materiais alcancados, unidade(s) vigente(s) como SUGESTAO,
    conflitos). Conflito pre-gold: materiais em mais de uma unidade vigente
    (`conflito_unidade`) ou com subunidade PREDITA diferente entre si
    (`conflito_subunidade_predita`). O conflito que depende do gold
    (`conflito_entre_certos`) e anexado DEPOIS do congelamento e nao influencia a ordem.
(E) Residual (so depois de congelar A-D), por material nao certo, com sobreposicao:
    `indisponivel`, `bloqueio_unidade`, `gold_fora_da_taxonomia`, `relacao_ausente`,
    `falha_selecao` (subdividido em `abstencao` e `escolha_errada`).

ESTADO VIGENTE: unidade = `computed_unit_slug` gravado no manifest SOBRESCRITO pelas
mudancas de #47/#48 (`aceite_v4_48_22-09.json` -> `mudancas_de_unidade`). Subunidade =
`computed_subunit_slug` gravado (base, 84/251; #47/#48 nao mudaram acertos de primaria).
"""
import collections
import csv
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diag = load("wp1_diag", HERE / "diagnostico_subunidade_17-09.py")
compare, mede = diag.compare, diag.mede
from src.builder.core.code_summarization import code_curation_signal_text, load_code_curation  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.builder.text import stopwords as SW  # noqa: E402

GENERIC = set(SW.UNIT_GENERIC_TOKENS) | set(SW.UNIT_STRUCTURAL_TOKENS) | set(SW.TOPIC_FALLBACK_STOPWORDS)
STEMS = tuple(sorted(SW.MOTOR_GENERIC_STEMS))
CAMPOS = ("titulo", "arquivo", "moodle_label", "heading", "code_curation")
CAMPOS_FORTES = ("titulo", "heading")
NGRAM_MAX = 3
STEM = 6


def ok_token(tok):
    return len(tok) >= 4 and tok.isalpha() and tok not in GENERIC and not tok.startswith(STEMS)


def toks(text):
    return [t for t in normalize_match_text(str(text or "")).split() if ok_token(t)]


def chave(seq):
    return " ".join(t[:STEM] for t in seq)


def ngramas(text):
    """(chave stem6, forma crua normalizada) para cada n-grama de 1..3 tokens validos."""
    seq = toks(text)
    saida = {}
    for n in range(1, NGRAM_MAX + 1):
        for i in range(len(seq) - n + 1):
            saida.setdefault(chave(seq[i:i + n]), " ".join(seq[i:i + n]))
    return saida


def campos_do_material(root, entry, curation):
    """Os 5 campos (A) com o texto CRU de cada um (o trecho literal sai daqui)."""
    saida = []
    titulo = str(entry.get("title") or "")
    if titulo:
        saida.append(("titulo", titulo))
    src = str(entry.get("source_path") or "")
    if src and not src.startswith(("http://", "https://")):
        stem = Path(src).stem
        if stem:
            saida.append(("arquivo", stem))
    label = str(entry.get("moodle_label") or "")
    if label:
        saida.append(("moodle_label", label))
    md = diag._entry_markdown_text_for_file_map(root, entry) or ""
    for linha in md.splitlines():
        s = linha.strip()
        if s.startswith("#"):
            s = s.lstrip("#").strip()
            if s:
                saida.append(("heading", s))
    resumo = code_curation_signal_text(curation.get(str(entry.get("id") or "")) or {}) or ""
    primeira = next((l.strip().lstrip("#").strip() for l in resumo.splitlines() if l.strip()), "")
    if primeira:
        saida.append(("code_curation", primeira))
    return saida


def taxonomia(root):
    """slug -> {label, aliases, unit_slug, tokens stem6}; e chave n-grama -> {slugs}."""
    dados = compare.read(root / "course/.content_taxonomy.json")
    topicos, conhecidas = {}, collections.defaultdict(set)
    for unit in dados.get("units", []):
        for topic in unit.get("topics", []):
            slug = topic.get("slug")
            frases = [str(topic.get("label") or "")] + [str(a) for a in topic.get("aliases") or []]
            tks = set()
            for frase in frases:
                seq = toks(frase)
                tks |= {t[:STEM] for t in seq}
                for n in range(1, NGRAM_MAX + 1):
                    for i in range(len(seq) - n + 1):
                        conhecidas[chave(seq[i:i + n])].add(slug)
            t = topicos.setdefault(slug, {"label": str(topic.get("label") or ""), "aliases": list(topic.get("aliases") or []),
                                          "units": set(), "tokens": set()})
            t["units"].add(str(topic.get("unit_slug") or unit.get("slug") or ""))
            t["tokens"] |= tks
    return topicos, conhecidas


def coletar():
    """Fase 1 (SEM gold): materiais, expressoes, ocorrencias, perguntas ordenadas."""
    mud = {(m["curso"], m["id"]): m["depois"]
           for m in compare.read(HERE / "aceite_v4_48_22-09.json")["mudancas_de_unidade"]}
    materiais, expressoes, ocorrencias, taxs = {}, {}, [], {}
    for sig, name in mede.NOMES.items():
        root = ROOT / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        ref_root = ROOT / ".frzero/pacote_fontes_15-09" / name
        topicos, conhecidas = taxonomia(root)
        taxs[sig] = (topicos, conhecidas)
        ref_by_id = {e["id"]: e for e in compare.read(ref_root / "manifest.json")["entries"]}
        by_source = compare.indexed(compare.read(root / "manifest.json")["entries"])
        mapping = {e["entry_id"]: e["new_id"] for e in compare.read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        curation = load_code_curation(root).get("entries", {}) or {}
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = [r for r in csv.DictReader(stream) if r["sub_primario"] != ""]
        for row in rows:
            gid = row["entry_id"]
            old = ref_by_id.get(mapping.get(gid) or "")
            entry = (by_source.get(compare.source(old)) or [None])[0] if old else None
            mat = {"curso": sig, "gold_id": gid, "entry_id": str(entry.get("id")) if entry else "",
                   "titulo": str((entry or old or {}).get("title") or ""),
                   "source_path": str((entry or old or {}).get("source_path") or ""),
                   "presente": entry is not None,
                   "unidade_vigente": "", "subunidade_predita": "", "expressoes": [], "expressoes_novas": []}
            materiais[(sig, gid)] = mat
            if entry is None:
                continue
            eid = str(entry.get("id"))
            mat["unidade_vigente"] = mud.get((sig, eid), str(entry.get("computed_unit_slug") or ""))
            mat["subunidade_predita"] = str(entry.get("computed_subunit_slug") or "")
            vistos = set()
            for campo, cru in campos_do_material(root, entry, curation):
                for k, forma in ngramas(cru).items():
                    slugs = sorted(conhecidas.get(k, ()))
                    e = expressoes.setdefault((sig, k), {"curso": sig, "chave": k, "formas": set(), "materiais": set(),
                                                         "campos": collections.Counter(), "ja_conhecida": slugs,
                                                         "peso_forte": 0})
                    e["formas"].add(forma)
                    e["materiais"].add(gid)
                    e["campos"][campo] += 1
                    if campo in CAMPOS_FORTES:
                        e["peso_forte"] += 1
                    if (k, campo) not in vistos:
                        vistos.add((k, campo))
                        ocorrencias.append({"curso": sig, "expressao": k, "forma": forma, "gold_id": gid,
                                            "entry_id": eid, "campo": campo, "trecho": cru[:120]})
                    if k not in mat["expressoes"]:
                        mat["expressoes"].append(k)
                        if not slugs:
                            mat["expressoes_novas"].append(k)

    # conflitos pre-gold + ordenacao greedy por cobertura marginal
    for (sig, k), e in expressoes.items():
        us = {materiais[(sig, g)]["unidade_vigente"] for g in e["materiais"]}
        ss = {materiais[(sig, g)]["subunidade_predita"] for g in e["materiais"]}
        e["unidades_vigentes"] = sorted(us)
        e["conflito_unidade"] = len(us) > 1
        e["conflito_subunidade_predita"] = len(ss) > 1
    perguntas = collections.defaultdict(list)
    for sig in mede.NOMES:
        universo = {g for (s, g) in materiais if s == sig and materiais[(s, g)]["presente"]}
        cand = {k: dict(e, materiais=set(e["materiais"])) for (s, k), e in expressoes.items()
                if s == sig and not e["ja_conhecida"]}
        cobertos, acumulado = set(), 0
        while cand:
            melhor, best = None, None
            for k, e in cand.items():
                novos = e["materiais"] - cobertos
                score = (len(novos), e["peso_forte"], [-ord(c) for c in k])
                if not novos:
                    continue
                if best is None or score > best:
                    melhor, best = k, score
            if melhor is None:
                break
            e = cand.pop(melhor)
            novos = sorted(e["materiais"] - cobertos)
            cobertos |= set(novos)
            acumulado = len(cobertos)
            perguntas[sig].append({
                "curso": sig, "ordem": len(perguntas[sig]) + 1, "expressao": melhor,
                "formas": sorted(expressoes[(sig, melhor)]["formas"]),
                "cobertura_marginal": len(novos), "cobertura_acumulada": acumulado,
                "cobertura_acumulada_pct": round(100.0 * acumulado / max(1, len(universo)), 1),
                "materiais_novos": novos, "materiais_alcancados": sorted(e["materiais"]),
                "unidades_vigentes_sugeridas": e["unidades_vigentes"],
                "conflito_unidade": e["conflito_unidade"],
                "conflito_subunidade_predita": e["conflito_subunidade_predita"],
                "campos": dict(e["campos"])})
    for e in expressoes.values():
        e["formas"] = sorted(e["formas"])
        e["materiais"] = sorted(e["materiais"])
        e["campos"] = dict(e["campos"])
    return materiais, expressoes, ocorrencias, perguntas, taxs


def congelar(expressoes, perguntas):
    """sha256 das decisoes de selecao/ordem, calculado ANTES de qualquer leitura de gold."""
    payload = {
        "definicoes": {"ngram_max": NGRAM_MAX, "stem": STEM, "campos": list(CAMPOS),
                       "campos_fortes": list(CAMPOS_FORTES)},
        "expressoes": sorted([[e["curso"], e["chave"], e["materiais"], e["ja_conhecida"]] for e in expressoes.values()]),
        "perguntas": {sig: [[q["ordem"], q["expressao"], q["cobertura_marginal"], q["materiais_novos"]] for q in lst]
                      for sig, lst in sorted(perguntas.items())}}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def avaliar(materiais, taxs):
    """Fase 2: GOLD entra aqui e SO aqui (coluna certo? + classes do residual)."""
    golds = {sig: mede.golds(sig) for sig in mede.NOMES}
    for (sig, gid), mat in materiais.items():
        topicos, conhecidas = taxs[sig]
        gsp = golds[sig][3].get(gid, set())
        gs = golds[sig][2].get(gid, set())
        mat["gold_primario"] = sorted(gsp)
        mat["gold_aceito"] = sorted(gs)
        mat["certo_primario"] = mat["subunidade_predita"] in gsp and mat["presente"]
        mat["certo_aceito"] = mat["subunidade_predita"] in gs and mat["presente"]
        classes = []
        if not mat["presente"]:
            classes.append("indisponivel")
            mat["classes"] = classes
            continue
        if mat["certo_primario"]:
            mat["classes"] = []
            continue
        na_tax = [s for s in gsp if s in topicos]
        if not na_tax:
            classes.append("gold_fora_da_taxonomia")
        else:
            units = set().union(*(topicos[s]["units"] for s in na_tax))
            if mat["unidade_vigente"] not in units:
                classes.append("bloqueio_unidade")
        gold_tokens = set().union(*(topicos[s]["tokens"] for s in na_tax)) if na_tax else set()
        alias_gold = {k for k, slugs in conhecidas.items() if set(slugs) & set(na_tax)}
        expr = set(mat["expressoes"])
        expr_tokens = {t for k in expr for t in k.split()}
        tem_relacao = bool(expr & alias_gold) or bool(expr_tokens & gold_tokens)
        if not tem_relacao:
            classes.append("relacao_ausente")
        else:
            classes.append("falha_selecao")
            classes.append("abstencao" if not mat["subunidade_predita"] else "escolha_errada")
        mat["classes"] = classes


def main():
    materiais, expressoes, ocorrencias, perguntas, taxs = coletar()
    sha_congelamento = congelar(expressoes, perguntas)
    print("CONGELAMENTO", sha_congelamento, flush=True)
    avaliar(materiais, taxs)

    # --- inventario por curso -------------------------------------------------
    CLASSES = ("indisponivel", "bloqueio_unidade", "gold_fora_da_taxonomia", "relacao_ausente",
               "falha_selecao", "abstencao", "escolha_errada")
    inventario = {}
    for sig in mede.NOMES:
        mats = [m for (s, _), m in materiais.items() if s == sig]
        inv = {"n": len(mats), "certos_primaria": sum(m["certo_primario"] for m in mats),
               "certos_aceita": sum(m["certo_aceito"] for m in mats), "classes": {}}
        for c in CLASSES:
            ids = sorted(m["gold_id"] for m in mats if c in m["classes"])
            inv["classes"][c] = {"n": len(ids), "ids": ids}
        inventario[sig] = inv
    tot = {"n": sum(v["n"] for v in inventario.values()),
           "certos_primaria": sum(v["certos_primaria"] for v in inventario.values()),
           "certos_aceita": sum(v["certos_aceita"] for v in inventario.values()),
           "classes": {c: sum(v["classes"][c]["n"] for v in inventario.values()) for c in CLASSES}}

    # --- matriz de evidencias (inclui os materiais hoje certos) ---------------
    por_expr = {(e["curso"], e["chave"]): e for e in expressoes.values()}
    matriz = []
    for oc in ocorrencias:
        mat = materiais[(oc["curso"], oc["gold_id"])]
        e = por_expr[(oc["curso"], oc["expressao"])]
        matriz.append({**oc, "unidade_sugerida": mat["unidade_vigente"],
                       "subunidade_predita": mat["subunidade_predita"],
                       "material_certo_hoje": mat["certo_primario"],
                       "relacoes_conhecidas": e["ja_conhecida"],
                       "conflito_unidade": e["conflito_unidade"],
                       "conflito_subunidade_predita": e["conflito_subunidade_predita"]})

    # --- enriquecimento pos-gold das perguntas (nao altera ordem) -------------
    for sig, lst in perguntas.items():
        for q in lst:
            certos = [g for g in q["materiais_alcancados"] if materiais[(sig, g)]["certo_primario"]]
            subs = {materiais[(sig, g)]["subunidade_predita"] for g in certos}
            q["materiais_certos_hoje"] = certos
            q["conflito_entre_certos"] = len(subs) > 1

    # --- cobertura sobre os NAO certos ----------------------------------------
    cobertura = {}
    for sig in mede.NOMES:
        mats = [m for (s, _), m in materiais.items() if s == sig]
        nao_certos = {m["gold_id"] for m in mats if not m["certo_primario"]}
        alvo = {m["gold_id"] for m in mats if not m["certo_primario"] and m["expressoes_novas"]}
        sem_pergunta = sorted(nao_certos - alvo)
        vistos, marcos = set(), {}
        for q in perguntas[sig]:
            vistos |= set(q["materiais_novos"]) & alvo
            for pct in (50, 80, 100):
                if pct not in marcos and alvo and len(vistos) >= pct / 100.0 * len(alvo):
                    marcos[pct] = q["ordem"]
        cobertura[sig] = {"nao_certos": len(nao_certos), "nao_certos_com_expressao_nova": len(alvo),
                          "nao_certos_sem_expressao_nova": len(sem_pergunta),
                          "ids_sem_expressao_nova": sem_pergunta,
                          "perguntas_total": len(perguntas[sig]),
                          "perguntas_para_50pct": marcos.get(50), "perguntas_para_80pct": marcos.get(80),
                          "perguntas_para_100pct": marcos.get(100),
                          "alcance_final_nao_certos": len(vistos)}

    # --- distribuicao de cobertura por expressao ------------------------------
    dist = {}
    for sig in mede.NOMES:
        es = [e for e in expressoes.values() if e["curso"] == sig]
        novas = [e for e in es if not e["ja_conhecida"]]
        c = collections.Counter()
        for e in novas:
            n = len(e["materiais"])
            c[">=5" if n >= 5 else ">=3" if n >= 3 else str(n)] += 1
        dist[sig] = {"expressoes_total": len(es), "ja_conhecidas": len(es) - len(novas), "novas": len(novas),
                     "novas_cobrem_>=5": sum(1 for e in novas if len(e["materiais"]) >= 5),
                     "novas_cobrem_>=3": sum(1 for e in novas if len(e["materiais"]) >= 3),
                     "novas_cobrem_2": sum(1 for e in novas if len(e["materiais"]) == 2),
                     "novas_cobrem_1": sum(1 for e in novas if len(e["materiais"]) == 1),
                     "ocorrencias": sum(1 for o in ocorrencias if o["curso"] == sig)}

    conflitos = {sig: {"perguntas": len(perguntas[sig]),
                       "com_mais_de_uma_unidade": sum(q["conflito_unidade"] for q in perguntas[sig]),
                       "tocam_material_certo": sum(1 for q in perguntas[sig] if q["materiais_certos_hoje"]),
                       "conflito_entre_certos": sum(q["conflito_entre_certos"] for q in perguntas[sig])}
                 for sig in mede.NOMES}

    coordenador = {"indisponiveis": 8, "bloqueio_unidade": 10, "gold_fora_da_taxonomia": 5,
                   "mesma_unidade_errada_ou_abstencao": 144, "abstencoes": 31,
                   "certos_primaria": 84, "certos_aceita": 107, "n": 251}
    todos = list(materiais.values())
    abst = [m for m in todos if m["presente"] and not m["certo_primario"] and not m["subunidade_predita"]]
    resto144 = [m for m in todos if m["presente"] and not m["certo_primario"]
                and "bloqueio_unidade" not in m["classes"] and "gold_fora_da_taxonomia" not in m["classes"]]
    conferencia = {
        "n": (tot["n"], coordenador["n"], tot["n"] == coordenador["n"]),
        "certos_primaria": (tot["certos_primaria"], coordenador["certos_primaria"],
                            tot["certos_primaria"] == coordenador["certos_primaria"]),
        "indisponiveis": (tot["classes"]["indisponivel"], 8, tot["classes"]["indisponivel"] == 8),
        "bloqueio_unidade": (tot["classes"]["bloqueio_unidade"], 10, tot["classes"]["bloqueio_unidade"] == 10),
        "gold_fora_da_taxonomia": (tot["classes"]["gold_fora_da_taxonomia"], 5, tot["classes"]["gold_fora_da_taxonomia"] == 5),
        "mesma_unidade_errada_ou_abstencao": (len(resto144), 144, len(resto144) == 144),
        "abstencoes_totais_entre_nao_certos": len(abst),
        "abstencoes_dentro_dos_144": sum(1 for m in abst if m in resto144),
        "soma_residual_com_sobreposicao": tot["classes"]["relacao_ausente"] + tot["classes"]["falha_selecao"],
        "divergencias": [
            "certos_aceita medido = %d vs 107 do coordenador: aqui a subunidade e a GRAVADA no manifest "
            "(estado 'antes' do aceite #48 = 84/108); os 107 sao o estado DEPOIS de #47 (perda de 1 aceita ja "
            "registrada em regra_secao_efeito_subunidade_21-09). A primaria (84) e identica nos dois estados."
            % tot["certos_aceita"],
            "abstencoes: 32 materiais nao certos com subunidade predita vazia; 1 deles tambem esta em "
            "bloqueio_unidade e por isso sai dos 144 do coordenador -> 31 dentro dos 144. Bate.",
            "relacao_ausente + falha_selecao = %d > 144 por sobreposicao deliberada (E): a diferenca de %d e "
            "exatamente bloqueio_unidade (10) + gold_fora_da_taxonomia (5), que tambem recebem classe de sinal."
            % (tot["classes"]["relacao_ausente"] + tot["classes"]["falha_selecao"],
               tot["classes"]["relacao_ausente"] + tot["classes"]["falha_selecao"] - 144),
        ]}
    relatorio = {
        "escopo": __doc__,
        "congelamento_sha256": sha_congelamento,
        "estado": {"branch": "feat/motor-atribuicao", "head": "9220a57", "unidade": "manifest + mudancas #47/#48",
                   "subunidade": "manifest gravado (base)"},
        "inventario": inventario, "inventario_total": tot, "contagem_coordenador": coordenador,
        "conferencia_coordenador": conferencia,
        "distribuicao_expressoes": dist, "cobertura_nao_certos": cobertura, "conflitos": conflitos,
        "perguntas": {sig: perguntas[sig] for sig in mede.NOMES},
        "expressoes": sorted(expressoes.values(), key=lambda e: (e["curso"], e["chave"])),
        "matriz": matriz,
        "materiais": sorted(({**m, "classes": m.get("classes", [])} for m in materiais.values()),
                            key=lambda m: (m["curso"], m["gold_id"])),
    }
    out = HERE / "wp1_inventario_matriz_22-09.json"
    out.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    print("TOTAL", json.dumps(tot, ensure_ascii=False))
    print("COBERTURA", json.dumps(cobertura, ensure_ascii=False, default=str)[:900])
    print("CONFLITOS", json.dumps(conflitos, ensure_ascii=False))
    print("DIST", json.dumps(dist, ensure_ascii=False))
    print("JSON_SHA256", sha)
    escrever_md(relatorio, sha)
    return relatorio


def escrever_md(r, sha):
    L = ["# W-P1 — inventario dos 251, residual e ordem das perguntas (22/09)", "",
         f"JSON: `wp1_inventario_matriz_22-09.json` sha256 `{sha}`  ",
         f"Congelamento (selecao/ordem, pre-gold) sha256 `{r['congelamento_sha256']}`  ",
         "Estado: branch `feat/motor-atribuicao`, HEAD `9220a57` + diff nao commitado da #48 em `src/`.", "",
         "## 1. Inventario por curso (regua de subunidade)", "",
         "| curso | n | certos prim. | certos aceit. | indisp. | bloq.unid. | gold fora tax. | relacao ausente | falha selecao | abstencao | escolha errada |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    C = ("indisponivel", "bloqueio_unidade", "gold_fora_da_taxonomia", "relacao_ausente", "falha_selecao",
         "abstencao", "escolha_errada")
    for sig, v in r["inventario"].items():
        L.append("| " + " | ".join([sig, str(v["n"]), str(v["certos_primaria"]), str(v["certos_aceita"])]
                                   + [str(v["classes"][c]["n"]) for c in C]) + " |")
    t = r["inventario_total"]
    L.append("| **TOTAL** | " + " | ".join([str(t["n"]), str(t["certos_primaria"]), str(t["certos_aceita"])]
                                           + [str(t["classes"][c]) for c in C]) + " |")
    L += ["", "### ids por classe", ""]
    for sig, v in r["inventario"].items():
        for c in C:
            if v["classes"][c]["ids"]:
                L.append(f"- **{sig} / {c}** ({v['classes'][c]['n']}): " + ", ".join(v["classes"][c]["ids"]))
    L += ["", "### conferencia contra a contagem do coordenador (22/09)", ""]
    for k, v in r["conferencia_coordenador"].items():
        if k != "divergencias":
            L.append(f"- `{k}`: {v}")
    for d in r["conferencia_coordenador"]["divergencias"]:
        L.append(f"- divergencia: {d}")
    L += ["", "## 2. Expressoes candidatas", "",
          "| curso | ocorrencias | expressoes | ja conhecidas (taxonomia) | novas | novas >=5 mat. | >=3 | 2 | 1 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for sig, d in r["distribuicao_expressoes"].items():
        L.append(f"| {sig} | {d['ocorrencias']} | {d['expressoes_total']} | {d['ja_conhecidas']} | {d['novas']} | "
                 f"{d['novas_cobrem_>=5']} | {d['novas_cobrem_>=3']} | {d['novas_cobrem_2']} | {d['novas_cobrem_1']} |")
    L += ["", "## 3. Cobertura sobre os nao certos", "",
          "| curso | nao certos | com expressao nova | sem nenhuma | perguntas | ate 50% | ate 80% | ate 100% |",
          "|---|---|---|---|---|---|---|---|"]
    for sig, c in r["cobertura_nao_certos"].items():
        L.append(f"| {sig} | {c['nao_certos']} | {c['nao_certos_com_expressao_nova']} | "
                 f"{c['nao_certos_sem_expressao_nova']} | {c['perguntas_total']} | {c['perguntas_para_50pct']} | "
                 f"{c['perguntas_para_80pct']} | {c['perguntas_para_100pct']} |")
    L += ["", "## 4. Conflitos das perguntas", "",
          "| curso | perguntas | >1 unidade vigente | tocam material certo | subunidade divergente entre certos |",
          "|---|---|---|---|---|"]
    for sig, c in r["conflitos"].items():
        L.append(f"| {sig} | {c['perguntas']} | {c['com_mais_de_uma_unidade']} | {c['tocam_material_certo']} | "
                 f"{c['conflito_entre_certos']} |")
    L += ["", "## 5. As 20 primeiras perguntas por curso", ""]
    for sig, lst in r["perguntas"].items():
        L += [f"### {sig}", "",
              "| # | expressao (forma) | marg. | acum. | acum.% | unidades vigentes sugeridas | conf.unid | toca certo |",
              "|---|---|---|---|---|---|---|---|"]
        for q in lst[:20]:
            forma = q["formas"][0] if q["formas"] else q["expressao"]
            u = ", ".join(x or "(vazia)" for x in q["unidades_vigentes_sugeridas"])[:70]
            L.append(f"| {q['ordem']} | {forma} | {q['cobertura_marginal']} | {q['cobertura_acumulada']} | "
                     f"{q['cobertura_acumulada_pct']} | {u} | {'sim' if q['conflito_unidade'] else ''} | "
                     f"{len(q['materiais_certos_hoje']) or ''} |")
        L.append("")
    (HERE / "wp1_inventario_matriz_22-09.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
