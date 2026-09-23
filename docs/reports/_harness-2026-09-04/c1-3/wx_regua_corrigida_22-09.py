"""W-X: regua corrigida (v2) auditavel, sustentada por MATERIAL + TAXONOMIA, e remedicao do estado #49.

Parecer do Astra (5a resposta, astra_ideias_motor_22-09.md): regua historica congelada; versao corrigida so pelos
materiais e pela taxonomia, nunca pela resposta do motor; materiais e denominadores permanecem; diferencas de anotacao
separadas de ganho de algoritmo.

Fases (nesta ordem):
  A. varredura dos 7 cursos SEM motor: (i) sub gold fora da unidade gold na taxonomia; (ii) unidade gold fora da
     taxonomia; (iii) id do gold sem material no build (so lista, W-V); (iv) gold vazio/duplicado; (v) slug repetido
     entre unidades; (vi) bloco gold fora do .timeline_index.json; (vii) scorable inconsistente.
  B. decisao por inconsistencia (tabela DECISOES, escrita a mao a partir do material e da taxonomia); cada evidencia e
     um (arquivo, regex) resolvido para (caminho, linha, texto) e verificado aqui -- se o texto sumir, o script falha.
  C. regua v2 = copia byte a byte dos CSV historicos, alterando SO as linhas corrigidas (wx_gold_v2_22-09/).
  D. cadeia real bloco -> unidade -> subunidade (molde aceite_v1_49_22-09.py 55-110) sobre os builds-base; decisoes
     congeladas por sha256 ANTES de carregar qualquer gold; avaliadas sob a regua historica e a v2.
  E. JSON (deterministico, sem tempo) + MD. Reexecucao compara o JSON byte a byte com o existente.

Sem rede/LLM (tripwires Gemini/Datalab/socket), sem tocar src/, tests/, CSV historicos nem builds.
Uso: python -B wx_regua_corrigida_22-09.py
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import io
import json
import re
import socket
import sys
import time
from pathlib import Path

T0 = time.time()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
REP = DATA / "docs/reports"
FIX = DATA / "tests/fixtures/eval"
V2 = HERE / "wx_gold_v2_22-09"
OUT_JSON = HERE / "wx_regua_corrigida_22-09.json"
OUT_MD = HERE / "wx_regua_corrigida_22-09.md"
sys.path.insert(0, str(DATA))
sys.path.insert(0, str(DATA / "scripts"))


# ------------------------------------------------------------------ tripwires (repara_paginas_cg.py 18-33 + socket)
def _bloqueado(*a, **k):
    raise RuntimeError("bloqueado (tripwire W-X: rede/LLM)")


import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None
_gc.GeminiClient.__init__ = _bloqueado
from src.builder.runtime import datalab_client  # noqa: E402
from src.builder import engine as engine_module  # noqa: E402
datalab_client.convert_document_to_markdown = _bloqueado
engine_module.convert_document_to_markdown = _bloqueado
socket.socket.connect = _bloqueado
socket.create_connection = _bloqueado

from eval_ground_truth import load_labels_csv  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rel(p):
    return Path(p).resolve().relative_to(DATA).as_posix()


def build_root(sig, nomes):
    return DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / nomes[sig]


def taxonomia(root):
    por_unidade, por_slug, rotulo = collections.defaultdict(set), collections.defaultdict(set), {}
    for unit in read(root / "course/.content_taxonomy.json").get("units", []) or []:
        u = str(unit.get("slug") or "")
        por_unidade[u]
        for t in unit.get("topics", []) or []:
            s = str(t.get("slug") or "")
            if s:
                por_unidade[u].add(s)
                por_slug[s].add(u)
                rotulo[(u, s)] = " / ".join(t.get("aliases") or [t.get("label") or s])
    return por_unidade, por_slug, rotulo


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------------ regua parametrizada por diretorio
def regua_unidade(sig, material_gt):
    """Copia fiel de scripts/eval_entry_unit.carrega_regua_unidade com o material_gt como parametro."""
    truth = {}
    gu_fix, gt = FIX / f"gold_units_{sig}.csv", REP / f"ground_truth_{sig}.csv"
    if gu_fix.exists() and gt.exists():
        by_uuid = {(r.get("block_uuid") or "").strip(): (r.get("true_unit") or "").strip()
                   for r in csv_rows(gu_fix) if (r.get("true_unit") or "").strip()}
        for r in csv_rows(gt):
            if (r.get("scorable") or "").strip().lower() != "yes":
                continue
            unit = by_uuid.get((r.get("true_block_uuid") or "").strip())
            if unit:
                truth[r["id"]] = (unit,)
    if not material_gt.exists():
        return truth
    for r in csv_rows(material_gt):
        if (r.get("scorable") or "yes").strip().lower() != "yes":
            continue
        units = [u.strip() for u in str(r.get("gold_units") or "").split("|") if u.strip()]
        if units:
            truth[str(r.get("entry_id") or "").strip()] = tuple(units)
    return truth


def golds_de(sig, base, uni):
    """(gb, gu, gs, gsp) como mede_3eixos_12-09.golds, lendo de `base` o que existir la e do historico o resto."""
    def p(nome):
        return base / nome if (base / nome).exists() else REP / nome
    gt = p(f"ground_truth_{sig}.csv")
    gb = load_labels_csv(gt) if gt.exists() else {}
    gu = regua_unidade(sig, p(f"material_gt_{sig}.csv")) if sig in uni else {}
    gs, gsp = {}, {}
    sp = p(f"subunit_gt_{sig}.csv")
    if sp.exists():
        for r in csv_rows(sp):
            if r["scorable"] == "yes":
                gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
                gsp[r["entry_id"]] = {r["gold_subunit"]}
    return gb, gu, gs, gsp


# ------------------------------------------------------------------ DECISOES (material + taxonomia; nunca predicao)
# evidencia: (arquivo relativo ao build | "@repo:" relativo ao repo, regex). Resolvida para caminho:linha:texto.
M_SO_TH = "staging/markdown-auto/pymupdf4llm/3103-threads.md"
M_ES2 = "staging/markdown-auto/pymupdf4llm/{}.md"
TOPICO_THREADS = ("unidade-03-programacao-concorrente", "programas-multithreads")
NOTA_V2 = " | W-X 22/09 (proposta v2, nao adotada): {}"

DECISOES = {
    # ---- (i) SO: gold de unidade u03 (material_gt, plano 4.1) x gold de subunidade conceitos-basicos (so u02/u04)
    **{("SO", eid, "i"): {
        "acao": "corrigir", "arquivo": "subunit_gt_SO.csv", "eixo": "subunidade primaria",
        "campos": {"gold_subunit": ("conceitos-basicos", "programas-multithreads"),
                   "unit_slug": ("unidade-02-gerencia-do-processador", "unidade-03-programacao-concorrente")},
        "motivo": ("material trata de threads/programa multithread; a taxonomia so tem topico de threads em u03 "
                   "(4.1 Programas multithreads), a mesma unidade do gold de unidade (material_gt: 'plano-de-ensino: "
                   "topico 4.1 Programas multithreads na u03'). conceitos-basicos existe so em u02 (3.1) e u04 (5.1); "
                   "a anotacao de 25/08 foi feita sob u02 ('u02 nao tem topico de threads; encaixe menos ruim'), "
                   "premissa desfeita pela adjudicacao curricular u03. unit_slug (coluna nao pontuada) acompanha."),
        "evidencias": ev,
        "taxonomia": [TOPICO_THREADS, ("unidade-02-gerencia-do-processador", "conceitos-basicos"),
                      ("unidade-04-deadlock", "conceitos-basicos")]}
        for eid, ev in {
            "3103-threads": [(M_SO_TH, r"^## Threads\s*$"), (M_SO_TH, r"Exemplo de Programa Multithread \(1\)"),
                             (M_SO_TH, r"Threads vs Processos \(1\)"),
                             ("@repo:docs/reports/material_gt_SO.csv", r"^3103-threads,.*4\.1 Programas multithreads")],
            **{f"exemplo-threads-em-c-exemplo{k}": [
                (f"code/professor/exemplo-threads-em-c-exemplo{k}.md", r"#include <pthread\.h>"),
                (f"code/professor/exemplo-threads-em-c-exemplo{k}.md", r"pthread_create"),
                ("@repo:docs/reports/material_gt_SO.csv", rf"^exemplo-threads-em-c-exemplo{k},.*4\.1 Programas multithreads")]
               for k in (1, 2, 3)}}.items()},
    # ---- (i) ES2 microsservicos5: gold de unidade u01 x subunidade u02 -> corrigir a UNIDADE (material = implantacao)
    ("ES2", "microsservicos5", "i"): {
        "acao": "corrigir", "arquivo": "material_gt_ES2.csv", "eixo": "unidade",
        "campos": {"gold_units": ("unidade-01-arquitetura-de-software",
                                  "unidade-02-integracao-de-desenvolvimento-e-operacao-devops")},
        "motivo": ("o material e implantacao de microsservicos em conteiner (Docker, VM x conteiner, ambientes de "
                   "implantacao em nuvem) = taxonomia u02 2.7 'integracao e IMPLANTACAO de microsservicos' e 2.6 "
                   "'Plataformas de DevOps'; u01 nao tem topico de implantacao/conteiner. A aula do cronograma leva o "
                   "nome literal do topico 2.7. O gold u01 vem de ruling em serie (19/08: 'a serie de microsservicos "
                   "cobre a unidade que fala de microsservicos'), que nao distingue 1.3.4/1.5 de 2.7; o gold de "
                   "subunidade (ruling 26/08) e o gold de bloco (gold_units bloco-08 -> u02) ja apontam u02."),
        "evidencias": [(M_ES2.format("microsservicos5"), r"^## Serviço em contêiner"),
                       (M_ES2.format("microsservicos5"), r"^## Arquitetura do Docker"),
                       (M_ES2.format("microsservicos5"), r"Importância do Ambiente de Implantação em Nuvem"),
                       ("course/.lessons_index.json", r"implantação de microsserviços em conteiners"),
                       ("@repo:tests/fixtures/eval/gold_units_ES2.csv", r"bloco-08,.*implantacao microservicos conteineres")],
        "taxonomia": [("unidade-02-integracao-de-desenvolvimento-e-operacao-devops", "estudo-de-caso-integracao-e-implantacao-de-microsservicos"),
                      ("unidade-02-integracao-de-desenvolvimento-e-operacao-devops", "plataformas-de-devops"),
                      ("unidade-01-arquitetura-de-software", "orientada-a-microsservicos")]},
    # ---- (i) ES2 microsservicos4 / 7: indecidivel
    **{("ES2", eid, "i"): {
        "acao": "indecidivel", "eixo": "unidade x subunidade",
        "motivo": ("o material e um padrao de microsservicos ({}) que cabe tanto em u01 (1.3.4 Orientada a "
                   "Microsservicos / 1.5 Estudo de caso: arquitetura orientada a microsservicos) quanto em u02 (2.7 "
                   "Estudo de caso: INTEGRACAO e implantacao de microsservicos). Duas rulings do usuario conflitam "
                   "(19/08 serie -> u01; 26/08 subunidade -> 2.7, apoiada na data pos-P1, criterio que a regua de "
                   "unidade rejeita: 'unidade = onde o plano poe o assunto'). O pacote (SYLLABUS/cronograma) nao "
                   "detalha em que topico o plano poe {}. Faltaria: adjudicacao se 2.7 'integracao' inclui {}, ou "
                   "plano de ensino detalhado por aula. Linha mantida como na historica.").format(tema, tema, tema),
        "evidencias": ev,
        "taxonomia": [("unidade-01-arquitetura-de-software", "orientada-a-microsservicos"),
                      ("unidade-01-arquitetura-de-software", "estudo-de-caso-arquitetura-orientada-a-microsservicos"),
                      ("unidade-02-integracao-de-desenvolvimento-e-operacao-devops", "estudo-de-caso-integracao-e-implantacao-de-microsservicos")]}
        for eid, tema, ev in (
            ("microsservicos4", "resiliencia/circuit breaker",
             [(M_ES2.format("microsservicos4"), r"^## Resiliência"), (M_ES2.format("microsservicos4"), r"^## Circuit Breaker"),
              ("course/.lessons_index.json", r"circuit-breaker")]),
            ("microsservicos7", "comunicacao assincrona/publish-subscribe",
             [(M_ES2.format("microsservicos7"), r"^## Comunicação entre Microsserviços"),
              (M_ES2.format("microsservicos7"), r"^## Arquitetura Publish/Subscribe"),
              (M_ES2.format("microsservicos7"), r"^## RabbitMQ")]))},
    # ---- (i) extras fora da unidade gold: aceitam, nao exigem -> manter
    ("CG", "programabasico3d", "i"): {
        "acao": "manter", "eixo": "subunidade aceita (extra)",
        "motivo": ("extra 'projecoes' (u06 6.3) fora da unidade gold u08, mas o primario (8.2 reflexao) esta em u08 e "
                   "o codigo de fato define projecao perspectiva; extra so ACEITA, nao exige resposta incompativel "
                   "com a unidade. Remove-lo seria endurecer a regua sem evidencia contra o conteudo."),
        "evidencias": [("code/professor/programabasico3d.md", r"gluPerspective"),
                       ("code/professor/programabasico3d.md", r"GL_LIGHT0, GL_DIFFUSE")],
        "taxonomia": [("unidade-06-processo-de-visualizacao-3d", "projecoes"),
                      ("unidade-08-sintese-de-imagens-realisticas", "modelos-de-reflexao-ambiente-difusa-especular")]},
    **{("FR", eid, "i"): {
        "acao": "manter", "eixo": "subunidade aceita (extra)",
        "motivo": ("extra '{}' fora da unidade anotada ({}); FR nao tem regua de unidade, o primario e compativel e o "
                   "extra so aceita conteudo que o material contem ({}). Nao ha exigencia incompativel.").format(ex, un, por),
        "evidencias": ev, "taxonomia": tx}
        for eid, ex, un, por, ev, tx in (
            ("03-tipos-de-redes", "classificacao-e-topologias-de-redes-de-computadores", "u01",
             "classificacao PAN/LAN/WAN = 6.1",
             [("staging/markdown-auto/pymupdf4llm/03-tipos-de-redes.md", r"^## Redes Pessoais \(PAN\)"),
              ("staging/markdown-auto/pymupdf4llm/03-tipos-de-redes.md", r"^## Redes Locais \(LAN\)")],
             [("unidade-06-nivel-fisico", "classificacao-e-topologias-de-redes-de-computadores"),
              ("unidade-01-introducao-a-redes-de-computadores", "conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia")]),
            *[(eid, proto, "u02", f"exemplo de socket {proto.split('-')[1].upper()} (sem markdown no pacote: zip; titulo e secao)",
               [("manifest.json", rf'"source_path": ".*{re.escape(src)}')],
               [("unidade-02-nivel-de-aplicacao", "implementacao-de-sockets"), ("unidade-03-nivel-de-transporte", proto)])
              for eid, proto, src in (("udp-example-c", "protocolo-udp", "udp_example_c.tar.gz"),
                                      ("udp-example-java", "protocolo-udp", "udp_example_java.tar.gz"),
                                      ("tcp-chat-c", "protocolo-tcp", "tcp_chat_c.tar.gz"),
                                      ("tcp-example", "protocolo-tcp", "tcp_example.tar.gz"))])},
    # ---- (iv) gold vazio
    ("TCC", "aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos", "iv"): {
        "acao": "manter", "eixo": "subunidade primaria",
        "motivo": ("vazio deliberado (ruling 25/08: 'revisao de pre-requisito; predizer qualquer subunidade e ERRO'). "
                   "O material se declara continuacao de Linguagens Formais e Automatos (outra disciplina) e revisa "
                   "alfabeto/cadeia/automatos/Chomsky, que nao sao topicos de u01 (anotada). Exige abstencao, que e "
                   "compativel com qualquer unidade (nao ha gold de unidade para este id). Risco registrado: a secao "
                   "'Linguagens Decidiveis vs. Reconheciveis' casa com u02 2.2; incluir como extra mudaria a ruling e "
                   "fica para o usuario."),
        "evidencias": [("staging/markdown-auto/pymupdf4llm/aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos.md", r"continuac.*Linguagens Formais e Aut"),
                       ("staging/markdown-auto/pymupdf4llm/aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos.md", r"^## A Hierarquia de Chomsky"),
                       ("staging/markdown-auto/pymupdf4llm/aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos.md", r"^## Linguagens Decid")],
        "taxonomia": [("unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas", "conjuntos-enumeraveis"),
                      ("unidade-02-turing-computabilidade", "linguagens-reconheciveis-e-decidiveis")]},
    **{("CG", eid, "iv"): {
        "acao": "manter", "eixo": "subunidade primaria",
        "motivo": ("vazio deliberado e consistente: gold de unidade u04 (oraculo Moodle/SARC 'Processo de Visualizacao "
                   "2D', ruling 06/09) e u04 nao tem topico de transformacoes/animacao/instanciamento (so coordenadas, "
                   "rasterizacao, recorte) -> exige abstencao. A questao de fundo e a UNIDADE (conteudo = u05 5.1 "
                   "Transformacoes geometricas; titulo/secao = visualizacao 2D): indecidivel pelo pacote, fica como "
                   "esta; faltaria adjudicar se 'instanciamento' pertence a u04 ou u05."),
        "evidencias": ev,
        "taxonomia": [("unidade-04-processo-de-visualizacao-2d", "algoritmos-de-rasterizacao"),
                      ("unidade-05-transformacoes-geometricas", "transformacoes-geometricas-e-coordenadas-homogeneas-2d")]}
        for eid, ev in (
            ("instanciamento", [("staging/markdown-auto/pymupdf4llm/instanciamento.md", r"Processo de Visualização Bidimensional INSTANCIAMENTO"),
                                ("staging/markdown-auto/pymupdf4llm/instanciamento.md", r"3 TRANSFORMAÇÕES GEOMÉTRICAS")]),
            ("transformacoesgl", [("staging/markdown-auto/html/transformacoesgl.md", r"Transformações Geométricas em"),
                                  ("staging/markdown-auto/html/transformacoesgl.md", r"glTranslatef\(tx, ty, tz\)")]),
            ("pagina-com-videos-sobre-instanciamento", [("manifest.json", r'"source_path": ".*6 - Processo de Visualização 2D.*nstanciamento')]),
            ("animacao-v2", [("manifest.json", r'"source_path": ".*6 - Processo de Visualização 2D.*Animacao-v2\.zip')]),
            ("transformacoesgeometricas", [("manifest.json", r'"source_path": ".*6 - Processo de Visualização 2D.*TransformacoesGeometricas\.zip')]))},
    # ---- regua ambigua herdada do W-T
    ("CG", "resolucao-de-prova-de-computacao-grafica-3d", "wt_regua_ambigua"): {
        "acao": "manter", "eixo": "unidade (conjunto aceito)",
        "motivo": ("prova resolvida cobre varias unidades; o conjunto u06|u07|u08 e desenho da regua ('qualquer uma "
                   "vale', 12/09), nao incoerencia; subunidade ja esta fora (scorable=no). O markdown do pacote so tem "
                   "o cabecalho ('Conteudo Extraido', 42 linhas): o pacote nao sustenta estreitar o conjunto."),
        "evidencias": [("staging/markdown-auto/html/resolucao-de-prova-de-computacao-grafica-3d.md", r"^## Conteúdo Extraído"),
                       ("@repo:docs/reports/material_gt_CG.csv", r"^resolucao-de-prova-de-computacao-grafica-3d,.*prova 3D")],
        "taxonomia": [("unidade-06-processo-de-visualizacao-3d", "projecoes"),
                      ("unidade-08-sintese-de-imagens-realisticas", "mapeamento-de-textura")]},
}

# regras gerais (tipos em lote), tambem sem predicao
REGRA = {
    "iii": ("listar", "assunto do W-V (#51, importacao offline); o gold nao muda: denominador congelado"),
    "v": ("manter", "fato da taxonomia, nao do gold: o gold usa o slug sob a unidade certa; a ambiguidade e do "
                    "METODO (regua compara so o slug), cuja troca seria mudanca de pontuacao, nao de anotacao"),
    "iv_id": ("manter", "linha scorable=no sem id (material sem entrada, ex.: prova antiga): ja fora da regua"),
    "vii": ("manter", "scorable=no motivado por unidade antiga/computada (coluna unit_slug != gold de unidade atual); "
                      "virar scorable=yes muda o DENOMINADOR, que o parecer do Astra manda congelar: fila para uma v3 "
                      "com decisao do usuario"),
    "i_info": ("manter", "coluna unit_slug do subunit_gt (nao pontuada) defasada em relacao ao gold de unidade; o slug "
                         "gold esta sob a unidade gold, sem exigencia incompativel"),
}


def resolve_evidencia(root, arq, rx):
    path = DATA / arq[len("@repo:"):] if arq.startswith("@repo:") else root / arq
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for n, line in enumerate(lines, 1):
        if re.search(rx, line):
            return {"arquivo": rel(path), "linha": n, "texto": line.strip()[:200]}
    raise AssertionError(f"evidencia nao encontrada: {path} /{rx}/")


# ------------------------------------------------------------------ fase A: varredura (sem motor, sem predicao)
def varredura(nomes, uni, compare):
    achados = []
    for sig in nomes:
        root = build_root(sig, nomes)
        por_unidade, por_slug, _ = taxonomia(root)
        blocos = {b["id"] for b in read(root / "course/.timeline_index.json")["blocks"]}
        gb, gu, gs, gsp = golds_de(sig, REP, uni)
        man = read(root / "manifest.json")["entries"]
        idx = compare.indexed(man)
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / nomes[sig] / "manifest.json")["entries"]}
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        her = {r["entry_id"]: r for r in csv_rows(HERE / f"herancas_{sig}_15-09.csv")}

        def add(tipo, eid, eixo, detalhe):
            achados.append({"curso": sig, "id": eid, "tipo": tipo, "eixo": eixo, "detalhe": detalhe})

        sub = csv_rows(REP / f"subunit_gt_{sig}.csv")
        com_i = set()
        for r in sub:
            eid = r["entry_id"]
            units = gu.get(eid) or ()
            if r["scorable"] == "yes":
                base = units or (r["unit_slug"],)
                slugs = [(r["gold_subunit"], "primario")] + [(x, "extra") for x in r["gold_subunits_extra"].split(";") if x]
                for s, papel in slugs:
                    if s and not any(s in por_unidade.get(u, ()) for u in base):
                        com_i.add(eid)
                        add("i", eid, f"subunidade ({papel})",
                            {"slug": s, "unidades_gold": list(base), "fonte_unidade": "regua de unidade" if units else "coluna unit_slug",
                             "slug_existe_em": sorted(por_slug.get(s, ()))})
                if not r["gold_subunit"]:
                    add("iv", eid, "subunidade primaria", {"gold": "", "extras": r["gold_subunits_extra"], "no_denominador": her.get(eid, {}).get("sub_primario", "") != ""})
                if units and r["unit_slug"] not in units and eid not in com_i:
                    add("i_info", eid, "subunidade (coluna unit_slug)", {"unit_slug": r["unit_slug"], "gold_unidade": list(units)})
            elif units and r["unit_slug"] not in units:
                add("vii", eid, "subunidade (scorable=no)", {"unit_slug": r["unit_slug"], "gold_unidade": list(units), "notas": r["notas"][:160]})
        for eid, units in gu.items():
            for u in units:
                if u not in por_unidade:
                    add("ii", eid, "unidade", {"unidade": u})
        for eid, b in gb.items():
            if b not in blocos:
                add("vi", eid, "bloco", {"bloco": b})
        for nome, chave in ((f"ground_truth_{sig}.csv", "id"), (f"material_gt_{sig}.csv", "entry_id"), (f"subunit_gt_{sig}.csv", "entry_id")):
            if not (REP / nome).exists():
                continue
            rows = csv_rows(REP / nome)
            cont = collections.Counter(r[chave].strip() for r in rows)
            for k, n in sorted(cont.items()):
                if k and n > 1:
                    add("iv", k, nome, {"duplicado": n})
            vazios = [r for r in rows if not r[chave].strip()]
            if vazios:
                add("iv_id", f"<{len(vazios)} linhas sem id>", nome,
                    {"scorable": dict(collections.Counter((r.get("scorable") or "").strip() for r in vazios))})
            for r in rows:
                sc = (r.get("scorable") or "yes").strip().lower()
                if sc not in ("yes", "no"):
                    add("vii", r[chave], nome, {"scorable": sc})
                vazio_gold = (not (r.get("true_block_id") or "").strip() if nome.startswith("ground") else
                              not (r.get("gold_units") or "").strip() if nome.startswith("material") else False)
                if sc == "yes" and r[chave].strip() and vazio_gold:
                    add("vii", r[chave], nome, {"scorable": "yes", "gold": "vazio (loader descarta em silencio)"})
        for eid, r in her.items():
            for eixo, g in (("bloco", gb), ("unidade", gu), ("sub_primario", gsp)):
                if (r[eixo] != "") != (eid in g):
                    add("vii", eid, f"herancas x gold ({eixo})", {"herancas": r[eixo], "no_gold": eid in g})
        for s, us in sorted(por_slug.items()):
            if len(us) > 1:
                usam = sorted(eid for eid, v in gs.items() if s in v)
                add("v", s, "taxonomia", {"unidades": sorted(us), "golds_que_usam": usam})
        for g in sorted(set(gb) | set(gu) | set(gs)):
            old = ref.get(mapping.get(g) or "")
            hits = idx.get(compare.source(old), []) if old else []
            if len(hits) != 1:
                motivo = "sem_mapeamento" if g not in mapping else ("new_id_fora_do_pacote_15-09" if not old else
                                                                   ("origem_nao_casa_no_build" if not hits else "origem_ambigua"))
                add("iii", g, "todos", {"motivo": motivo, "eixos": [a for a, x in (("bloco", gb), ("unidade", gu), ("sub", gs)) if g in x]})
    # flag herdada do W-T (la derivada da predicao; aqui so listada e decidida por material/taxonomia)
    for sig, eid in read(HERE / "wt_anatomia_unidade_49_22-09.json")["regua_ambigua_flag"]:
        achados.append({"curso": sig, "id": eid, "tipo": "wt_regua_ambigua", "eixo": "unidade",
                        "detalhe": {"gold_unidade": list(golds_de(sig, REP, uni)[1].get(eid, ()))}})
    return achados


def decidir(achados, nomes):
    out = []
    for a in achados:
        key = (a["curso"], a["id"], a["tipo"])
        root = build_root(a["curso"], nomes)
        if key in DECISOES:
            d = DECISOES[key]
            por_unidade, _, rotulo = taxonomia(root)
            tax = []
            for u, s in d["taxonomia"]:
                assert s in por_unidade.get(u, ()), ("taxonomia nao confirma", a["curso"], u, s)
                tax.append({"unidade": u, "topico": s, "rotulo": rotulo[(u, s)]})
            ev = [resolve_evidencia(root, arq, rx) for arq, rx in d["evidencias"]]
            out.append({**a, "acao": d["acao"], "motivo": d["motivo"], "evidencia_material": ev, "evidencia_taxonomia": tax,
                        "correcao": {k: {"de": v[0], "para": v[1]} for k, v in d.get("campos", {}).items()},
                        "arquivo_corrigido": d.get("arquivo"), "eixo_decisao": d["eixo"]})
        elif a["tipo"] in REGRA:
            acao, motivo = REGRA[a["tipo"]]
            out.append({**a, "acao": acao, "motivo": motivo, "evidencia_material": [], "evidencia_taxonomia": [],
                        "correcao": {}, "arquivo_corrigido": None})
        else:
            raise AssertionError(f"inconsistencia sem decisao: {key}")
    usadas = {(o["curso"], o["id"], o["tipo"]) for o in out}
    assert set(DECISOES) <= usadas, ("decisao sem inconsistencia correspondente", set(DECISOES) - usadas)
    return out


# ------------------------------------------------------------------ fase C: regua v2 (linhas corrigidas, resto byte a byte)
def escreve_v2(decisoes):
    por_arquivo = collections.defaultdict(dict)
    for d in decisoes:
        if d["acao"] == "corrigir":
            por_arquivo[d["arquivo_corrigido"]][d["id"]] = d
    V2.mkdir(exist_ok=True)
    diff, gerados = [], {}
    for nome, alvo in sorted(por_arquivo.items()):
        raw = (REP / nome).read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf") and raw.count(b"\r\n") == raw.count(b"\n"), nome   # BOM + CRLF
        texto = raw[3:].decode("utf-8")
        linhas = texto.split("\r\n")
        header = next(csv.reader([linhas[0]]))
        chave = header[0]
        feitos = set()
        for i, linha in enumerate(linhas[1:], 1):
            if not linha:
                continue
            campos = next(csv.reader([linha]))
            if len(campos) != len(header):   # linha com quebra dentro de aspas: nao e alvo (conferido abaixo)
                continue
            row = dict(zip(header, campos))
            d = alvo.get(row[chave])
            if not d:
                continue
            for campo, v in d["correcao"].items():
                assert row[campo] == v["de"], (nome, row[chave], campo, row[campo])
                row[campo] = v["para"]
                diff.append({"curso": d["curso"], "id": d["id"], "eixo": d["eixo_decisao"], "arquivo": nome, "campo": campo,
                             "de": v["de"], "para": v["para"],
                             "evidencia": "; ".join(f"{e['arquivo']}:{e['linha']}" for e in d["evidencia_material"])})
            mudancas = ", ".join(f"{c} {v['de']} -> {v['para']}" for c, v in d["correcao"].items())
            row["notas"] = row["notas"] + NOTA_V2.format(mudancas)
            buf = io.StringIO()
            csv.writer(buf, lineterminator="").writerow([row[h] for h in header])
            linhas[i] = buf.getvalue()
            feitos.add(row[chave])
        assert feitos == set(alvo), (nome, set(alvo) - feitos)
        novo = b"\xef\xbb\xbf" + "\r\n".join(linhas).encode("utf-8")
        (V2 / nome).write_bytes(novo)
        # conferencia: so as linhas-alvo mudaram; parse das demais identico
        a_rows, b_rows = csv_rows(REP / nome), csv_rows(V2 / nome)
        assert len(a_rows) == len(b_rows)
        mud = [(x[chave], [k for k in x if x[k] != y[k]]) for x, y in zip(a_rows, b_rows) if x != y]
        assert {m[0] for m in mud} == set(alvo), mud
        for eid, campos in mud:
            assert set(campos) == set(alvo[eid]["correcao"]) | {"notas"}, (eid, campos)
        gerados[nome] = {"sha256_historico": hashlib.sha256(raw).hexdigest(), "sha256_v2": hashlib.sha256(novo).hexdigest(),
                         "linhas_alteradas": sorted(feitos)}
    return diff, gerados


# ------------------------------------------------------------------ fase D: cadeia real + congelamento + avaliacao
def cadeia(nomes, compare):
    rb = load("wx_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wx_ru", HERE / "replay_unidade_21-09.py")
    orig_read = ru.read
    estado = {}
    for sig in nomes:
        root = build_root(sig, nomes)
        saved, bloco_novo, _, _ = rb.replay(root)
        feed = [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]

        def patched(path, _feed=feed):
            data = orig_read(path)
            if Path(path).name == "manifest.json":
                data = {**data, "entries": _feed}
            return data

        ru.read = patched
        try:
            _, novo, _ = ru.replay(root)
        finally:
            ru.read = orig_read
        estado[sig] = {"root": root, "saved": saved, "novo": novo}
        print("cadeia", sig, len(novo), flush=True)
    congelado = {sig: {eid: list(compare.predictions(v["root"], e)) for eid, e in v["novo"].items()} for sig, v in estado.items()}
    sha = hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return estado, congelado, sha


def avalia(nomes, compare, estado, congelado, golds_fn):
    tot, cursos, por_id, preds = collections.Counter(), {}, {}, {}
    for sig in nomes:
        saved = estado[sig]["saved"]
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / nomes[sig] / "manifest.json")["entries"]}
        index = compare.indexed(list(saved.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gb, gu, gs, gsp = golds_fn(sig)
        c = collections.Counter()
        for row in csv_rows(HERE / f"herancas_{sig}_15-09.csv"):
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            eid = str(hits[0]["id"]) if hits else None
            pred = congelado[sig].get(eid) if eid else None
            preds[(sig, gid)] = pred
            for eixo, col, ok in (("bloco", "bloco", lambda: pred[0] == gb[gid]), ("unidade", "unidade", lambda: pred[1] in gu[gid]),
                                  ("sub_primaria", "sub_primario", lambda: pred[2] in gsp[gid]),
                                  ("sub_aceita", "sub_primario", lambda: pred[2] in gs[gid])):
                if row[col] == "":
                    continue
                acerto = bool(pred and ok())
                c[f"{eixo}_n"] += 1
                c[eixo] += acerto
                por_id[(sig, gid, eixo)] = acerto
        cursos[sig] = dict(c)
        tot.update(c)
    return dict(tot), cursos, por_id, preds


def main():
    compare = load("wx_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    nomes, uni = mede.NOMES, mede.UNI
    for sig in nomes:   # a regua parametrizada reproduz a oficial
        assert golds_de(sig, REP, uni) == mede.golds(sig), sig

    # A + B (sem motor)
    achados = varredura(nomes, uni, compare)
    decisoes = decidir(achados, nomes)
    diff, gerados = escreve_v2(decisoes)
    tabela = collections.defaultdict(collections.Counter)
    for a in achados:
        tabela[a["curso"]][a["tipo"]] += 1
    print("INCONSISTENCIAS", {k: dict(v) for k, v in tabela.items()}, flush=True)

    # D: cadeia real, congelamento ANTES de qualquer gold da avaliacao
    estado, congelado, sha_cong = cadeia(nomes, compare)
    print("CONGELAMENTO", sha_cong, flush=True)
    hist_tot, hist_cur, hist_id, preds = avalia(nomes, compare, estado, congelado, lambda s: golds_de(s, REP, uni))
    v2_tot, v2_cur, v2_id, _ = avalia(nomes, compare, estado, congelado, lambda s: golds_de(s, V2, uni))
    assert set(hist_id) == set(v2_id), "denominador mudou"
    delta_ids = [{"curso": k[0], "id": k[1], "eixo": k[2], "historica": hist_id[k], "v2": v2_id[k], "rotulo": "anotacao"}
                 for k in sorted(hist_id) if hist_id[k] != v2_id[k]]
    delta_eixo = {e: v2_tot.get(e, 0) - hist_tot.get(e, 0) for e in ("bloco", "unidade", "sub_primaria", "sub_aceita")}
    delta_curso = {s: {e: v2_cur[s].get(e, 0) - hist_cur[s].get(e, 0) for e in ("bloco", "unidade", "sub_primaria", "sub_aceita")
                       if v2_cur[s].get(e, 0) != hist_cur[s].get(e, 0)} for s in nomes}
    delta_curso = {s: v for s, v in delta_curso.items() if v}
    base49 = (hist_tot["bloco"], hist_tot["unidade"], hist_tot["sub_primaria"], hist_tot["sub_aceita"])
    # sensibilidade do METODO (slug duplicado), diagnostico pos-decisao: acerto de sub com slug repetido entre
    # unidades e unidade predita fora do gold de unidade (a regua por slug credita um par (unidade, slug) errado)
    sens = []
    for d in decisoes:
        if d["tipo"] != "v":
            continue
        gu = golds_de(d["curso"], REP, uni)[1]
        creditados = sorted(gid for (s, gid, eixo), ok in hist_id.items()
                            if s == d["curso"] and eixo == "sub_aceita" and ok and preds[(s, gid)] and preds[(s, gid)][2] == d["id"]
                            and gid in gu and preds[(s, gid)][1] not in gu[gid])
        sens.append({"curso": d["curso"], "slug": d["id"], "golds_que_usam": d["detalhe"]["golds_que_usam"],
                     "acertos_por_slug_com_unidade_predita_fora_do_gold": creditados})
    checks = {
        "historica_reproduz_49_217_246_84_107": base49 == (217, 246, 84, 107),
        "denominadores_iguais_237_284_251": (hist_tot["bloco_n"], hist_tot["unidade_n"], hist_tot["sub_primaria_n"]) == (237, 284, 251)
                                            and all(hist_tot[k] == v2_tot[k] for k in ("bloco_n", "unidade_n", "sub_primaria_n", "sub_aceita_n")),
        "toda_inconsistencia_tem_decisao": len(decisoes) == len(achados),
        "correcoes_so_com_evidencia_material_e_taxonomia": all(d["evidencia_material"] and d["evidencia_taxonomia"] for d in decisoes if d["acao"] == "corrigir"),
    }
    report = {
        "tarefa": "W-X regua corrigida (v2) + remedicao #49",
        "head": "493119e (inclui #50)",
        "inconsistencias_por_curso_tipo": {k: dict(sorted(v.items())) for k, v in sorted(tabela.items())},
        "decisoes": decisoes,
        "diff_regua_v2": diff,
        "arquivos_v2": gerados,
        "sha256_congelamento": sha_cong,
        "placar": {"historica": {"totais": hist_tot, "cursos": hist_cur}, "v2": {"totais": v2_tot, "cursos": v2_cur}},
        "delta_anotacao": {"por_eixo": delta_eixo, "por_curso": delta_curso, "por_id": delta_ids},
        "slug_duplicado_golds_afetados": sens,
        "checks": checks,
        "conflito_de_interesse": ("as colunas pred_subunit/pred_unit e algumas notas dos CSV historicos citam predicoes antigas do "
                                  "motor; foram vistas na leitura, mas nenhuma decisao as usa. Decisoes: material do build + "
                                  "taxonomia + rulings registradas. A predicao do estado #49 so entra na fase D, depois das decisoes."),
        "limitacoes": [
            "evidencia de material de zips (CG animacao-v2/transformacoesgeometricas, FR sockets) e so titulo/secao via manifest: o pacote nao tem markdown deles",
            "ES2 microsservicos4/7 e a unidade dos 5 vazios de CG ficam indecidiveis pelo pacote (sem plano detalhado por aula)",
            "scorable=no motivados por unidade antiga nao foram reabertos: denominador congelado (fila para v3)",
        ],
    }
    blob = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    sha_json = hashlib.sha256(blob).hexdigest()
    reexec = None
    if OUT_JSON.exists():
        reexec = OUT_JSON.read_bytes() == blob
        print("REEXECUCAO byte-identica:", reexec, flush=True)
    if not OUT_JSON.exists() or reexec:
        OUT_JSON.write_bytes(blob)
    else:
        OUT_JSON.with_suffix(".divergente.json").write_bytes(blob)
    escreve_md(report, sha_json, reexec, time.time() - T0)
    print("TOTAIS hist", {k: hist_tot[k] for k in sorted(hist_tot)})
    print("TOTAIS v2  ", {k: v2_tot[k] for k in sorted(v2_tot)})
    print("DELTA", delta_eixo, delta_curso)
    print("CHECKS", checks)
    print("SHA256 json", sha_json, "| congelamento", sha_cong, f"| {time.time() - T0:.0f}s")
    assert all(checks.values()), checks


def escreve_md(r, sha_json, reexec, dur):
    L = ["# W-X — régua corrigida (v2) e remedição do estado #49 (22/09)", "",
         "Medição, 0 mudança de algoritmo. Régua histórica intocada; v2 em `c1-3/wx_gold_v2_22-09/` (proposta, não adotada).",
         "Decisões por material + taxonomia; predição do motor só entra depois, na remedição.", "",
         f"- sha256 JSON: `{sha_json}`", f"- sha256 congelamento (antes de qualquer gold): `{r['sha256_congelamento']}`",
         f"- tempo: {dur:.0f} s", f"- reexecução byte-idêntica: {'pendente (1ª execução)' if reexec is None else ('sim' if reexec else 'NÃO')}", "",
         "## Inconsistências por curso e tipo", "",
         "Tipos: i sub fora da unidade gold · i_info coluna unit_slug defasada · ii unidade fora da taxonomia · iii id sem material no build ·"
         " iv gold vazio/duplicado · iv_id linhas sem id · v slug repetido entre unidades · vi bloco fora do timeline · vii scorable inconsistente · wt_regua_ambigua (W-T)", ""]
    tipos = ["i", "i_info", "ii", "iii", "iv", "iv_id", "v", "vi", "vii", "wt_regua_ambigua"]
    L.append("| curso | " + " | ".join(tipos) + " | total |")
    L.append("|---|" + "---|" * (len(tipos) + 1))
    cont = collections.defaultdict(collections.Counter)
    for d in r["decisoes"]:
        cont[d["curso"]][d["tipo"]] += 1
    for sig in ("MF", "SO", "IA", "ES2", "TCC", "CG", "FR"):
        L.append(f"| {sig} | " + " | ".join(str(cont[sig][t]) for t in tipos) + f" | {sum(cont[sig].values())} |")
    L.append(f"| total | " + " | ".join(str(sum(cont[s][t] for s in cont)) for t in tipos) + f" | {len(r['decisoes'])} |")
    L += ["", "## Decisões com evidência", "", "| curso | id | tipo | eixo | ação | evidência (material) | taxonomia |", "|---|---|---|---|---|---|---|"]
    for d in r["decisoes"]:
        ev = "<br>".join(f"`{e['arquivo']}:{e['linha']}` {e['texto'][:70].replace('|', '/')}" for e in d["evidencia_material"]) or "—"
        tx = "<br>".join(f"{t['unidade'][:12]}… `{t['topico']}` ({t['rotulo'][:40]})" for t in d["evidencia_taxonomia"]) or "—"
        L.append(f"| {d['curso']} | `{d['id'][:60]}` | {d['tipo']} | {d['eixo']} | **{d['acao']}** | {ev} | {tx} |")
    L += ["", "### Motivos", ""]
    vistos = set()
    for d in r["decisoes"]:
        chave = (d["tipo"], d["motivo"])
        alvo = f"{d['curso']} `{d['id'][:60]}`"
        if d["acao"] in ("corrigir", "indecidivel") or d["tipo"] in ("i", "iv", "wt_regua_ambigua"):
            L.append(f"- {alvo} ({d['tipo']}, {d['acao']}): {d['motivo']}")
        elif chave not in vistos:
            vistos.add(chave)
            L.append(f"- tipo {d['tipo']} ({d['acao']}, regra geral): {d['motivo']}")
    L += ["", "## Diff da régua v2", "", "| curso | id | eixo | arquivo | campo | de | para | evidência |", "|---|---|---|---|---|---|---|---|"]
    for x in r["diff_regua_v2"]:
        L.append(f"| {x['curso']} | `{x['id']}` | {x['eixo']} | {x['arquivo']} | {x['campo']} | `{x['de']}` | `{x['para']}` | {x['evidencia']} |")
    L += ["", "Cada linha corrigida recebe em `notas` o sufixo `W-X 22/09 (proposta v2, não adotada)`; todas as outras linhas são byte a byte as históricas.", ""]
    for nome, g in r["arquivos_v2"].items():
        L.append(f"- `{nome}`: histórico `{g['sha256_historico'][:16]}…` → v2 `{g['sha256_v2'][:16]}…`, linhas {', '.join(g['linhas_alteradas'])}")
    ht, vt = r["placar"]["historica"]["totais"], r["placar"]["v2"]["totais"]
    L += ["", "## Placar do estado #49 (src/ atual, HEAD com #50) sob as duas réguas", "",
          "| eixo | histórica | v2 | delta (anotação) |", "|---|---|---|---|"]
    for e in ("bloco", "unidade", "sub_primaria", "sub_aceita"):
        L.append(f"| {e} | {ht[e]}/{ht[e + '_n']} | {vt[e]}/{vt[e + '_n']} | {vt[e] - ht[e]:+d} |")
    L += ["", "Por curso (só onde muda): " + (json.dumps(r["delta_anotacao"]["por_curso"], ensure_ascii=False) or "nenhum"), "",
          "| curso | id | eixo | histórica | v2 |", "|---|---|---|---|---|"]
    for x in r["delta_anotacao"]["por_id"]:
        L.append(f"| {x['curso']} | `{x['id']}` | {x['eixo']} | {int(x['historica'])} | {int(x['v2'])} |")
    L += ["", "## Checks", ""] + [f"- {k}: {v}" for k, v in r["checks"].items()]
    L += ["", "## Conflito de interesse", "", r["conflito_de_interesse"], "", "## Limitações", ""] + [f"- {x}" for x in r["limitacoes"]]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
