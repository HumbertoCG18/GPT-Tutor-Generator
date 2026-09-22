"""W-U (CRU-02): cobertura de relacoes explicitas recuperaveis de OUTRO documento do pacote.

NAO mede regra do motor, NAO toca src/: constroi um INDICE de relacoes (expressao -> topico)
a partir dos documentos do pacote e so DEPOIS usa o gold para contar A/B.

Definicoes congeladas (pre-declaradas):
(E) EXPRESSAO = chave stem6 do W-P1 (`expressoes` de wp1_inventario_matriz_22-09.json).
    Genericos/stopwords/<4 letras ja saem por construcao (ok_token do W-P1).
(T) TOPICO   = (unit_slug, slug) da taxonomia do curso. "Mencao a T" numa linha =
    a sequencia stem6 do label OU de um alias de T aparece como subsequencia contigua
    da sequencia stem6 da linha.
(P1) HIERARQUIA: E num heading/item de lista de OUTRO material cujo heading ANCESTRAL menciona T.
(P2) MESMA LINHA: E e mencao a T na mesma linha de heading/lista/tabela de qualquer documento.
(P3) PLANO/TIMELINE: E no texto de um bloco/sessao cujo texto (topic_text/topics/labels) menciona T.
(P4) SYLLABUS/GLOSSARIO/CRONOGRAMA/PLANO DE ENSINO: linha com E sob heading que menciona T.

Regras: o documento de origem NAO pode ser o proprio material (filtro na avaliacao);
guarda sempre doc + trecho literal (<=160c) + padrao; nao decide "assunto principal".

Read-only. Sem build, rede, LLM ou git.
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
DATA = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
sys.path.insert(0, str(DATA))

from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.builder.text import stopwords as SW  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor",
         "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
CATEGORIA = {"MF", "IA"}

GENERIC = set(SW.UNIT_GENERIC_TOKENS) | set(SW.UNIT_STRUCTURAL_TOKENS) | set(SW.TOPIC_FALLBACK_STOPWORDS)
STEMS = tuple(sorted(SW.MOTOR_GENERIC_STEMS))
NGRAM_MAX, STEM, TRECHO = 3, 6, 160

# Documentos do pacote que sao SAIDA da propria classificacao do motor (vazamento) ou
# cuja proveniencia nao e determinavel: EXCLUIDOS por decisao pre-declarada.
EXCLUIDOS = {
    "course/FILE_MAP.md": "saida do file map (classificacao do motor)",
    "course/FILE_MAP_TRACE.md": "trace da classificacao do motor",
    "course/COURSE_MAP.md": "deriva do file map",
    "course/CODE_HEALTH.md": "relatorio derivado do build",
    "course/CRONOGRAMA_HEALTH.md": "relatorio derivado do build",
    "course/.block_identity.json": "identidade de bloco computada no build",
    "course/.tag_catalog.json": "tags auto computadas",
    "course/.semantic_profile.generated.json": "perfil gerado pelo build",
    "course/.assessment_context.json": "contexto computado no build",
    "course/.card_block_map.json": "mapa card->bloco computado no build",
    "manifest.json (computed_*)": "campos computados pelo motor",
    "BUILD_REPORT.md": "relatorio do build",
    "README.md": "boilerplate do pacote",
}


def ok_token(tok):
    return len(tok) >= 4 and tok.isalpha() and tok not in GENERIC and not tok.startswith(STEMS)


def toks(text):
    return [t[:STEM] for t in normalize_match_text(str(text or "")).split() if ok_token(t)]


def ngram_keys(seq):
    out = set()
    for n in range(1, NGRAM_MAX + 1):
        for i in range(len(seq) - n + 1):
            out.add(" ".join(seq[i:i + n]))
    return out


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def corta(linha):
    s = " ".join(str(linha or "").split())
    return s[:TRECHO]


# ---------------------------------------------------------------- taxonomia (T)
def carrega_topicos(root):
    """[(unit_slug, slug, label)] + indice de frases stem6 -> {(unit,slug)}."""
    dados = read_json(root / "course/.content_taxonomy.json")
    topicos, frases = [], collections.defaultdict(set)
    for unit in dados.get("units", []):
        us = str(unit.get("slug") or "")
        for topic in unit.get("topics", []):
            slug = str(topic.get("slug") or "")
            if not slug:
                continue
            key = (us, slug)
            topicos.append({"unit_slug": us, "slug": slug, "label": str(topic.get("label") or "")})
            for frase in [topic.get("label")] + list(topic.get("aliases") or []):
                seq = tuple(toks(frase))
                if seq:
                    frases[seq].add(key)
    por_inicio = collections.defaultdict(list)
    for seq, keys in frases.items():
        por_inicio[seq[0]].append((seq, keys))
    return topicos, por_inicio


def mencoes(seq, por_inicio):
    """Topicos mencionados numa linha ja tokenizada (stem6)."""
    achados = set()
    for i, tok in enumerate(seq):
        for frase, keys in por_inicio.get(tok, ()):
            if tuple(seq[i:i + len(frase)]) == frase:
                achados |= keys
    return achados


# ---------------------------------------------------------------- varredura
LISTA = ("-", "*", "+")


def kind_of(linha):
    s = linha.strip()
    if not s:
        return None
    if s.startswith("#"):
        return "heading"
    if s.startswith(LISTA) or (s[:1].isdigit() and s[1:3] in (". ", ") ") or s[:3].rstrip(".) ").isdigit() and "." in s[:4]):
        return "lista"
    if s.startswith("|"):
        return "tabela"
    return "texto"


def varre_markdown(texto, so_estrutura):
    """(kind, linha_crua, seq_stem6, [seq dos headings ancestrais]) por linha util."""
    pilha = []  # (nivel, seq_stem6, texto)
    for linha in texto.splitlines():
        kind = kind_of(linha)
        if kind is None:
            continue
        if kind == "heading":
            s = linha.strip()
            nivel = len(s) - len(s.lstrip("#"))
            corpo = s.lstrip("#").strip()
            while pilha and pilha[-1][0] >= nivel:
                pilha.pop()
            seq = toks(corpo)
            yield "heading", corpo, seq, [p[1] for p in pilha]
            pilha.append((nivel, seq, corpo))
            continue
        if so_estrutura and kind not in ("lista", "tabela"):
            continue
        yield kind, linha.strip(), toks(linha), [p[1] for p in pilha]


def relacoes_do_documento(texto, doc_id, universo, por_inicio, padrao_hier, so_estrutura):
    """Gera (E, (unit,slug), doc, trecho, padrao) para um documento markdown-like."""
    for kind, crua, seq, ancestrais in varre_markdown(texto, so_estrutura):
        if not seq:
            continue
        achadas = ngram_keys(seq) & universo
        if not achadas:
            continue
        mesma_linha = mencoes(seq, por_inicio)
        acima = set()
        for anc in ancestrais:
            acima |= mencoes(anc, por_inicio)
        acima -= mesma_linha
        for e in achadas:
            if kind in ("heading", "lista", "tabela"):
                for t in mesma_linha:
                    yield e, t, doc_id, corta(crua), "P2"
            for t in acima:
                if padrao_hier == "P1" and kind not in ("heading", "lista"):
                    continue
                yield e, t, doc_id, corta(crua), padrao_hier


def relacoes_do_plano(blocos, doc_id, universo, por_inicio):
    """P3: E no texto do bloco/sessao cujo texto menciona T."""
    for bloco in blocos:
        linhas = [str(bloco.get("topic_text") or "")]
        linhas += [str(t) for t in bloco.get("topics") or []]
        linhas += [str(bloco.get("period_label") or "")]
        for s in bloco.get("sessions") or []:
            linhas.append(str(s.get("label") or ""))
        seqs = [(l, toks(l)) for l in linhas if l.strip()]
        alvo = set()
        for _, seq in seqs:
            alvo |= mencoes(seq, por_inicio)
        if not alvo:
            continue
        for crua, seq in seqs:
            for e in ngram_keys(seq) & universo:
                for t in alvo:
                    yield e, t, doc_id, corta(crua), "P3"


def blocos_de_licoes(dados):
    """Normaliza .lessons_index.json para a forma de bloco usada em P3."""
    itens = dados.get("lessons") or dados.get("days") or dados.get("entries") or []
    if isinstance(itens, dict):
        itens = list(itens.values())
    saida = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        texto = " ".join(str(item.get(k) or "") for k in ("title", "label", "summary", "topic_text", "roteiro"))
        saida.append({"topic_text": texto, "topics": [str(t) for t in item.get("topics") or []],
                      "period_label": str(item.get("date") or ""),
                      "sessions": [{"label": str(s)} for s in item.get("sections") or []]})
    return saida


# ---------------------------------------------------------------- indice
def constroi_indice(materiais_por_curso, universo_por_curso):
    indice = collections.defaultdict(list)   # (curso, E) -> [rel]
    vistos = set()
    docs_por_curso = {}
    for sig, nome in NOMES.items():
        universo = universo_por_curso.get(sig) or set()
        if not universo:
            continue
        base = ".frzero/pacote_categoria_17-09" if sig in CATEGORIA else ".frzero/pacote_fontes_15-09"
        root = DATA / base / nome
        topicos, por_inicio = carrega_topicos(root)
        usados, ignorados = [], []

        def emite(gen):
            for e, t, doc, trecho, padrao in gen:
                chave = (sig, e, t, doc, padrao)
                if chave in vistos:
                    continue
                vistos.add(chave)
                indice[(sig, e)].append({"unit_slug": t[0], "topico": t[1], "doc": doc,
                                         "trecho": trecho, "padrao": padrao})

        # (a) markdown de CADA material do pacote -> P1/P2
        entries = read_json(root / "manifest.json").get("entries", [])
        n_md = 0
        for entry in entries:
            texto = _entry_markdown_text_for_file_map(root, entry) or ""
            if not texto.strip():
                continue
            n_md += 1
            emite(relacoes_do_documento(texto, "material:" + str(entry.get("id")), universo,
                                        por_inicio, "P1", so_estrutura=True))
        usados.append({"doc": "markdown dos materiais", "n": n_md, "padroes": ["P1", "P2"]})

        # (b) documentos de plano/curso -> P4/P2
        for rel in ("course/SYLLABUS.md", "course/CRONOGRAMA_DETALHADO.md", "course/GLOSSARY.md",
                    "course/COURSE_IDENTITY.md", "course/SOURCE_REGISTRY.yaml"):
            caminho = root / rel
            if not caminho.exists():
                ignorados.append({"doc": rel, "motivo": "inexistente"})
                continue
            emite(relacoes_do_documento(read_text(caminho), rel, universo, por_inicio,
                                        "P4", so_estrutura=False))
            usados.append({"doc": rel, "n": 1, "padroes": ["P4", "P2"]})

        # (c) plano de ensino e ementa do perfil (entrada do professor) -> P4/P2
        inputs = root / "_inputs_15-09.json"
        if inputs.exists():
            perfil = read_json(inputs).get("profile_input") or {}
            for campo in ("teaching_plan", "syllabus"):
                texto = str(perfil.get(campo) or "")
                if texto.strip():
                    emite(relacoes_do_documento(texto, "_inputs_15-09.json:" + campo, universo,
                                                por_inicio, "P4", so_estrutura=False))
                    usados.append({"doc": "_inputs_15-09.json:" + campo, "n": 1, "padroes": ["P4", "P2"]})
        else:
            ignorados.append({"doc": "_inputs_15-09.json", "motivo": "inexistente"})

        # (d) timeline e licoes -> P3
        tl = root / "course/.timeline_index.json"
        if tl.exists():
            emite(relacoes_do_plano(read_json(tl).get("blocks") or [], "course/.timeline_index.json",
                                    universo, por_inicio))
            usados.append({"doc": "course/.timeline_index.json", "n": 1, "padroes": ["P3"]})
        li = root / "course/.lessons_index.json"
        if li.exists():
            emite(relacoes_do_plano(blocos_de_licoes(read_json(li)), "course/.lessons_index.json",
                                    universo, por_inicio))
            usados.append({"doc": "course/.lessons_index.json", "n": 1, "padroes": ["P3"]})
        else:
            ignorados.append({"doc": "course/.lessons_index.json", "motivo": "inexistente"})

        docs_por_curso[sig] = {"usados": usados, "excluidos_por_proveniencia": EXCLUIDOS,
                               "ignorados": ignorados, "topicos_taxonomia": len(topicos)}
    return indice, docs_por_curso


def sha_indice(indice):
    plano = []
    for (sig, e), rels in sorted(indice.items()):
        for r in sorted(rels, key=lambda x: (x["padrao"], x["doc"], x["unit_slug"], x["topico"], x["trecho"])):
            plano.append([sig, e, r["unit_slug"], r["topico"], r["doc"], r["padrao"], r["trecho"]])
    blob = json.dumps(plano, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), len(plano)


# ---------------------------------------------------------------- relatorio
GRUPOS_ORDEM = ("relacao_ausente_106", "falha_selecao_53", "certos_84")


def relatorio_md(d, sha_json):
    L = []
    a = L.append
    a("# W-U (CRU-02) - cobertura de relacoes explicitas recuperaveis do proprio pacote")
    a("")
    a("Read-only, fora de `src/`. Branch `feat/motor-atribuicao`, HEAD `410592d`, 22/09.")
    a("Gold SO AVALIA: indice construido para todos os topicos/materiais e congelado antes de ler o gold.")
    a("")
    a("- congelamento do indice (sha256, antes do gold): `%s`" % d["congelamento_sha256"])
    a("- sha256 do JSON: `%s`" % sha_json)
    a("")
    a("## 1. Definicoes congeladas")
    a("")
    for k in ("E", "T", "P1", "P2", "P3", "P4"):
        a("- **%s**: %s" % (k, d["definicoes"][k]))
    a("- n-grama 1..%s tokens, stem%s, trecho <= %s c. Relacao so vale se o documento de origem NAO e o proprio material."
      % (d["definicoes"]["ngram_max"], d["definicoes"]["stem"], d["definicoes"]["trecho_max"]))
    a("")
    a("## 2. Documentos do pacote: usados e excluidos")
    a("")
    a("| curso | markdown de materiais | docs de course/ | plano+ementa (_inputs_15-09.json) | timeline | lessons |")
    a("|---|---|---|---|---|---|")
    for sig in sorted(d["documentos"]):
        docs = {u["doc"]: u["n"] for u in d["documentos"][sig]["usados"]}
        md = docs.get("markdown dos materiais", 0)
        plano = sum(1 for k in docs if k.startswith("course/") and (k.endswith(".md") or k.endswith(".yaml")))
        perfil = sum(1 for k in docs if k.startswith("_inputs"))
        a("| %s | %s | %s | %s | %s | %s |" % (
            sig, md, plano, perfil,
            "sim" if "course/.timeline_index.json" in docs else "nao",
            "sim" if "course/.lessons_index.json" in docs else "nao"))
    a("")
    a("Docs de `course/` usados: SYLLABUS.md, CRONOGRAMA_DETALHADO.md, GLOSSARY.md, COURSE_IDENTITY.md, SOURCE_REGISTRY.yaml.")
    a("`course/.lessons_index.json` so existe em ES2, IA e MF.")
    a("")
    a("Excluidos por proveniencia (vazamento da propria classificacao do motor):")
    a("")
    for k, why in sorted(EXCLUIDOS.items()):
        a("- `%s` - %s" % (k, why))
    a("")
    a("De `.timeline_index.json` usou-se apenas o TEXTO (topic_text, topics, period_label, sessions[].label);")
    a("`primary_topic_slug` e `topic_candidates` sao escore do proprio motor sobre a taxonomia e ficaram de fora.")
    a("")
    idx = d["indice"]
    a("## 3. Tamanho do indice")
    a("")
    a("- relacoes (E, T, doc, trecho, padrao) distintas: **%s**" % idx["relacoes"])
    a("- por padrao: " + ", ".join("%s=%s" % kv for kv in sorted(idx["por_padrao"].items())))
    a("- por curso: " + ", ".join("%s=%s" % kv for kv in sorted(idx["por_curso"].items())))
    a("- E distintas com ao menos uma relacao: **%s** (dessas, %s nao sao `ja_conhecida` do W-P1)"
      % (idx["expressoes_com_relacao"], idx["expressoes_com_relacao_nao_ja_conhecidas"]))
    a("- universo de E por curso: " + ", ".join("%s=%s" % kv for kv in sorted(idx["expressoes_no_universo"].items())))
    a("- topicos (unit_slug, slug) alcancados: **%s**" % idx["topicos_distintos_alcancados"])
    dt = idx["distribuicao_T_por_E"]
    tot = sum(dt.values())
    a("- distribuicao de T por E: 1 topico=%s, 2-4=%s, >=5=%s -> **%s de %s E sao ambiguas (>=2 topicos)**"
      % (dt.get("1", 0), dt.get("2-4", 0), dt.get(">=5", 0), tot - dt.get("1", 0), tot))
    a("")
    a("## 4. Cobertura A / A-conflitante / B")
    a("")
    a("| grupo | n | A | A-conflitante | B | A total | % A total |")
    a("|---|---|---|---|---|---|---|")
    for nome in GRUPOS_ORDEM:
        g = d["cobertura"][nome]
        c = g["classes"]
        A, AC, B = c.get("A", 0), c.get("A-conflitante", 0), c.get("B", 0)
        a("| %s | %s | %s | %s | %s | %s | %.0f%% |" % (nome, g["n"], A, AC, B, A + AC, (A + AC) * 100.0 / g["n"]))
    a("")
    for nome in GRUPOS_ORDEM:
        g = d["cobertura"][nome]
        a("### %s" % nome)
        a("")
        a("| curso | A | A-conflitante | B |")
        a("|---|---|---|---|")
        for curso in sorted(g["por_curso"]):
            c = g["por_curso"][curso]
            a("| %s | %s | %s | %s |" % (curso, c.get("A", 0), c.get("A-conflitante", 0), c.get("B", 0)))
        a("")
        a("Materiais cujo acerto no gold veio de cada padrao (um material pode ter varios): "
          + ", ".join("%s=%s" % kv for kv in sorted(g["materiais_por_padrao_com_hit_no_gold"].items())))
        a("")
        a("Topicos conflitantes por material (entre A/A-conflitante): "
          + ", ".join("%s=%s" % kv for kv in sorted(g["topicos_conflitantes_por_material"].items())))
        a("")
        if g["B_ids"]:
            a("Sobreposicao dos B com o residual do W-P1: "
              + ", ".join("%s=%s" % kv for kv in sorted(g["B_sobreposicao_residual_wp1"].items())))
            a("")
            a("Lista dos B (curso / entry_id / gold / classes do W-P1):")
            a("")
            for b in sorted(g["B_ids"], key=lambda x: (x["curso"], x["entry_id"])):
                a("- %s / `%s` / gold `%s` / %s" % (b["curso"], b["entry_id"],
                                                    ", ".join(b["gold"]) or "(vazio)", ", ".join(b["classes_wp1"])))
            a("")
    a("## 5. Ruido do indice (controle nos 84 certos)")
    a("")
    r = d["ruido_do_indice_nos_certos"]
    a("- certos com relacao para o gold: **%s/84**" % r["com_relacao_para_o_gold"])
    a("- certos sem relacao para o gold: **%s/84**" % r["sem_relacao_para_o_gold"])
    a("- certos que, alem do gold, tem relacao para outros topicos: **%s** (todo certo coberto e tambem conflitante)"
      % r["com_gold_e_tambem_outros"])
    a("")
    a("## 6. Exemplos")
    a("")
    a("Dez relacoes recuperadas para materiais dos 106:")
    a("")
    for e in d["exemplos_recuperados_106"]:
        a("- %s `%s` gold `%s` <- E `%s` -> T `%s` [%s] em `%s`: \"%s\"" % (
            e["curso"], e["entry_id"], ", ".join(e["gold"]), e["expressao"], e["topico"],
            e["padrao"], e["doc"], e["trecho"]))
    a("")
    a("Cinco conflitos:")
    a("")
    for c in d["exemplos_conflito_106"]:
        a("- %s `%s` gold `%s`: %s topicos concorrentes (ex.: %s)" % (
            c["curso"], c["entry_id"], ", ".join(c["gold"]), c["n_outros_topicos"],
            ", ".join(c["outros_topicos"][:5])))
    a("")
    a("## 7. Limitacoes")
    a("")
    for lim in d["limitacoes"]:
        a("- %s" % lim)
    a("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main
def main():
    fonte = HERE / "wp1_inventario_matriz_22-09.json"
    bruto = read_json(fonte)

    # --- SEM GOLD: so os campos de entrada do W-P1 ---
    materiais = [{k: v for k, v in m.items()
                  if k in ("curso", "entry_id", "gold_id", "titulo", "source_path", "presente",
                           "unidade_vigente", "subunidade_predita", "expressoes", "expressoes_novas")}
                 for m in bruto["materiais"]]
    universo = collections.defaultdict(set)
    ja_conhecida = {}
    for e in bruto["expressoes"]:
        universo[e["curso"]].add(e["chave"])
        ja_conhecida[(e["curso"], e["chave"])] = bool(e.get("ja_conhecida"))
    for m in materiais:
        universo[m["curso"]].update(m["expressoes"])

    indice, docs = constroi_indice(materiais, universo)
    congelamento, n_rel = sha_indice(indice)
    print("congelamento_sha256 (indice, ANTES do gold):", congelamento, "| relacoes:", n_rel)

    # --- estatisticas do indice (ainda sem gold) ---
    por_padrao = collections.Counter()
    por_curso = collections.Counter()
    t_por_e = {}
    for (sig, e), rels in indice.items():
        por_curso[sig] += len(rels)
        for r in rels:
            por_padrao[r["padrao"]] += 1
        t_por_e[(sig, e)] = {(r["unit_slug"], r["topico"]) for r in rels}
    dist_t = collections.Counter()
    for k, ts in t_por_e.items():
        dist_t["1" if len(ts) == 1 else ("2-4" if len(ts) <= 4 else ">=5")] += 1
    e_novas = sum(1 for k in t_por_e if not ja_conhecida.get(k, False))

    # --- GOLD ENTRA AQUI, so para contar A/B ---
    gold = {(m["curso"], m["entry_id"], m["gold_id"]): m for m in bruto["materiais"]}

    def avalia(mat):
        chave_m = (mat["curso"], mat["entry_id"], mat["gold_id"])
        g = [s for s in (gold[chave_m].get("gold_primario") or []) if s]
        alvo = set(g)
        proprio = "material:" + str(mat["entry_id"])
        hits, outros, padroes_ok = [], set(), set()
        for e in mat["expressoes"]:
            for r in indice.get((mat["curso"], e), ()):
                if r["doc"] == proprio:
                    continue
                if r["topico"] in alvo:
                    hits.append({"expressao": e, **r})
                    padroes_ok.add(r["padrao"])
                else:
                    outros.add((r["unit_slug"], r["topico"]))
        classe = "A" if hits else "B"
        if hits and outros:
            classe = "A-conflitante"
        return {"curso": mat["curso"], "entry_id": mat["entry_id"], "gold_id": mat["gold_id"],
                "gold": g, "classe": classe, "n_hits": len(hits), "n_outros": len(outros),
                "padroes": sorted(padroes_ok), "hits": hits[:3],
                "outros_topicos": sorted(t[1] for t in outros)[:10]}

    grupos = {
        "relacao_ausente_106": [m for m in bruto["materiais"] if "relacao_ausente" in m["classes"]],
        "falha_selecao_53": [m for m in bruto["materiais"] if "falha_selecao" in m["classes"]],
        "certos_84": [m for m in bruto["materiais"] if m["certo_primario"]],
    }
    por_id = {(m["curso"], m["entry_id"], m["gold_id"]): m for m in materiais}
    saida_grupos, exemplos, conflitos = {}, [], []
    for nome, lista in grupos.items():
        avaliados = [avalia(por_id[(m["curso"], m["entry_id"], m["gold_id"])]) for m in lista]
        cont = collections.Counter(a["classe"] for a in avaliados)
        p_curso = collections.defaultdict(collections.Counter)
        p_padrao = collections.Counter()
        for a in avaliados:
            p_curso[a["curso"]][a["classe"]] += 1
            for p in a["padroes"]:
                p_padrao[p] += 1
        sobrep = collections.Counter()
        outros_bucket = collections.Counter()
        for a in avaliados:
            if a["classe"] == "B":
                continue
            n = a["n_outros"]
            outros_bucket["0" if n == 0 else ("1-4" if n <= 4 else ("5-19" if n < 20 else ">=20"))] += 1
        bs = []
        for a, m in zip(avaliados, lista):
            if a["classe"] != "B":
                continue
            bs.append({"curso": a["curso"], "entry_id": a["entry_id"], "gold": a["gold"],
                       "classes_wp1": m["classes"]})
            marcas = [c for c in ("bloqueio_unidade", "indisponivel", "gold_fora_da_taxonomia")
                      if c in m["classes"]]
            sobrep["+".join(marcas) if marcas else "B_puro"] += 1
        saida_grupos[nome] = {
            "n": len(avaliados), "classes": dict(cont),
            "por_curso": {k: dict(v) for k, v in sorted(p_curso.items())},
            "materiais_por_padrao_com_hit_no_gold": dict(p_padrao),
            "B_sobreposicao_residual_wp1": dict(sobrep),
            "topicos_conflitantes_por_material": dict(outros_bucket),
            "B_ids": bs,
        }
        if nome == "relacao_ausente_106":
            for a in avaliados:
                if a["hits"] and len(exemplos) < 10:
                    h = a["hits"][0]
                    exemplos.append({"curso": a["curso"], "entry_id": a["entry_id"], "gold": a["gold"],
                                     "expressao": h["expressao"], "topico": h["topico"],
                                     "doc": h["doc"], "padrao": h["padrao"], "trecho": h["trecho"]})
                if a["classe"] == "A-conflitante" and len(conflitos) < 5:
                    conflitos.append({"curso": a["curso"], "entry_id": a["entry_id"], "gold": a["gold"],
                                      "n_outros_topicos": a["n_outros"],
                                      "outros_topicos": a["outros_topicos"],
                                      "exemplo_hit": a["hits"][0] if a["hits"] else None})

    # ruido do indice: entre os certos, relacao para o gold vs so para outros
    certos = saida_grupos["certos_84"]
    ruido = {"com_relacao_para_o_gold": certos["classes"].get("A", 0) + certos["classes"].get("A-conflitante", 0),
             "sem_relacao_para_o_gold": certos["classes"].get("B", 0),
             "com_gold_e_tambem_outros": certos["classes"].get("A-conflitante", 0)}

    saida = {
        "escopo": "W-U (CRU-02): cobertura de relacoes explicitas recuperaveis de OUTRO documento do pacote.",
        "estado": {"branch": "feat/motor-atribuicao", "head": "410592d", "gold": "so avalia"},
        "definicoes": {"E": "chave stem6 do W-P1", "T": "(unit_slug, slug) da taxonomia",
                       "P1": "E em heading/lista de outro material sob heading ancestral que menciona T",
                       "P2": "E e mencao a T na mesma linha de heading/lista/tabela",
                       "P3": "E no texto de bloco/sessao do plano cujo texto menciona T",
                       "P4": "E sob heading que menciona T em syllabus/glossario/cronograma/plano de ensino",
                       "ngram_max": NGRAM_MAX, "stem": STEM, "trecho_max": TRECHO},
        "congelamento_sha256": congelamento,
        "documentos": docs,
        "indice": {"relacoes": n_rel, "por_padrao": dict(por_padrao), "por_curso": dict(por_curso),
                   "expressoes_com_relacao": len(t_por_e),
                   "expressoes_no_universo": {k: len(v) for k, v in universo.items()},
                   "expressoes_com_relacao_nao_ja_conhecidas": e_novas,
                   "topicos_distintos_alcancados": len({t for ts in t_por_e.values() for t in ts}),
                   "distribuicao_T_por_E": dict(dist_t)},
        "cobertura": saida_grupos,
        "ruido_do_indice_nos_certos": ruido,
        "exemplos_recuperados_106": exemplos,
        "exemplos_conflito_106": conflitos,
        "limitacoes": [
            "Documentos excluidos por proveniencia de saida do motor listados em documentos[*].excluidos_por_proveniencia.",
            "P3 usa apenas o TEXTO do bloco/sessao (topic_text/topics/labels); primary_topic_slug e topic_candidates "
            "sao escores do proprio motor sobre a taxonomia e foram excluidos.",
            "Mencao a T exige label/alias contiguo em stem6; topicos cujo label so aparece parafraseado nao sao detectados.",
            "Relacao = existencia, nao 'assunto principal'.",
        ],
    }
    out = HERE / "wu_cobertura_relacoes_22-09.json"
    texto = json.dumps(saida, ensure_ascii=False, indent=1, sort_keys=True)
    out.write_text(texto, encoding="utf-8")
    sha_json = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    (HERE / "wu_cobertura_relacoes_22-09.md").write_text(relatorio_md(saida, sha_json), encoding="utf-8")
    print("json_sha256:", sha_json)
    for nome, g in saida_grupos.items():
        print(nome, g["n"], g["classes"], "| padroes:", g["materiais_por_padrao_com_hit_no_gold"])
    print("indice:", n_rel, dict(por_padrao), "| E com relacao:", len(t_por_e), "| dist T/E:", dict(dist_t))
    print("ruido certos:", ruido)


if __name__ == "__main__":
    main()
