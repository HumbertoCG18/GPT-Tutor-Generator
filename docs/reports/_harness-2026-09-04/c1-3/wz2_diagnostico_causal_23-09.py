"""W-Z2 (23/09): diagnostico causal dos 3 eixos a partir do W-Z, sem R5 e sem regra nova. 0 mudanca em src/tests/regua.

Pedido literal: c1-3/wz2_pedido_usuario_23-09.md. Registro pre-medicao (pergunta / por que os artefatos nao bastam /
decisao que muda): .workflow/local/wz2-diagnostico-causal-20260923.md (Q1-Q6).

BASE: a do W-Z (regua v2 final + 13 presentes; MF/IA/CG em .frzero/wv_importacao_22-09). Cadeia real
replay_bloco_21-09 -> replay_unidade_21-09 (apply_unit_subunit_fields). O congelamento do W-Z (`788e4372...`,
.frzero/wz_congelado_22-09.json) NAO e reexecutado: e lido para provar que a base instrumentada decide igual por ID.

INSTRUMENTACAO (so em memoria, restaurada no finally; nao altera decisao na base):
  - `_entry_markdown_text_for_file_map` marca o material corrente (primeira chamada por material no laco);
  - `auto_unit` guarda o vencedor bruto do texto (slug, conf, ambiguo) e a `section_slug` (secao do Moodle, #47);
  - `auto_sub` guarda a decisao da 1a passada e, so na 1a, a pontuacao EXATA (a que o seletor usa) e por RADICAL
    (stem_fallback, que so a rota de unidade usa) de TODOS os topicos da taxonomia, com o mesmo coletor de sinais;
  - `propagar_vocabulario_por_headings` marca a 2a passada (chamadas de auto_sub dentro dela = 2a).

MODOS (tres replays completos; bloco igual nos tres):
  base            decisao real. Congelada por sha256 ANTES de ler qualquer gold.
  oraculo_unidade ALIMENTADO POR GOLD (diagnostico, nunca regra): `reconcile_unit_with_block` devolve a unidade do
                  oraculo quando ha gold COERENTE para o material; o resto decide igual. Subunidade, 2a passada e
                  vocabulario propagado sao RECOMPUTADOS. Oraculo por material (gold id -> eid pela mesma ponte do W-Z):
                    s* = gold primario de subunidade; T(s*) = unidades da taxonomia que contem o slug s*; U_g = gold de
                    unidade (conjunto aceito) ou vazio (FR sem regua de unidade).
                    s* != "":  C = T(s*) & U_g se U_g, senao T(s*); oraculo = C se |C| == 1, senao nenhum (incoerente).
                    s* == "" ou sem gold de subunidade: oraculo = U_g se |U_g| == 1, senao nenhum.
  oraculo_bloco   ALIMENTADO POR GOLD: a `unit_slug` de cada bloco que JA tem unidade e trocada pela `true_unit` do gold
                  POR BLOCO (tests/fixtures/eval/gold_units_<C>.csv, casado por (date_start, date_end) exatos; senao
                  sobreposicao de unidade unica). Blocos sem unidade continuam sem (heranca do vizinho segue o desenho).
                  CG, FR: sem gold por bloco -> intocados. Limite: nos cursos em que a regua de unidade E o gold do
                  bloco-gold (ground_truth |><| gold_units), o acerto de unidade dos materiais nao adjudicados sobe POR
                  CONSTRUCAO; o numero informativo e o efeito nos adjudicados e na subunidade.
  Os dois oraculos sao efeito diagnostico de intervencao ideal: nao sao regra, nao sao teto universal, nao se somam.
  (oraculo_bloco roda sem a pontuacao por topico da instrumentacao: so placar e mudancas por ID.)

DECOMPOSICAO DO DP POSICIONAL (Q1; funcao pura sobre o indice gravado, sem replay):
  candidatos = blocos com `auto_unit_slug` na ordem do indice (o que o DP recebeu; fidelidade = recomputar
  `assign_units_positional` e comparar com `auto_unit_slug` bloco a bloco). Afinidade = |tokens do bloco & tokens da
  unidade| (as funcoes do proprio unit_matcher). Classe do bloco pela unidade atribuida u:
    sem_sinal (afinidade 0 em todas; preenchido pela ordem) | contra_argmax (existe sinal e u nao e o maximo; ordem/
    janela forcou) | sinal_proprio_empatado (u e maximo empatado) | sinal_proprio_unico (u e maximo unico).
  Mecanismo: dp_puro | desvio (janela) | ancora (exclusiva/radical) | desvio+ancora, por ablacao das constantes do
  modulo (DETOUR_MIN_GAIN, ANCHOR_MIN_AFF -> inf), restauradas. Cabecalho: u e maximo com o titulo da unidade e deixa
  de ser sem os tokens do titulo. Fronteira: unidade do candidato anterior != do seguinte.
  Gold POR BLOCO (so MF, SO, IA, ES2, TCC) avalia o bloco; CG/FR nao tem.

INDICE DOCUMENTAL (Q5): o mesmo do W-U (P1 hierarquia de headings de outro material, P2 mesma linha, P3 bloco do
  timeline, P4 linha sob secao de syllabus/glossario/cronograma/plano), com as funcoes do proprio
  wu_cobertura_relacoes_22-09.py; universo = expressoes (W-P1: titulo, arquivo, moodle_label, headings, 1a linha da
  curadoria de codigo) de TODOS os materiais do manifest (nao depende da lista do gold). Fidelidade: o mesmo laco com as
  raizes e o universo do W-U reproduz o sha `c17786ef...` do W-U. Construido antes do gold.

FAMILIAS DA SUBUNIDADE PRIMARIA (pre-declaradas; causa primaria pela ordem do pipeline, demais condicoes como flags;
  cada material conta uma vez). u^ = unidade final prevista, s^ = subunidade final, s1 = decisao da 1a passada,
  S_acc = primario + extras, pont(s*) = pontuacao EXATA de s* entre os topicos de u^ (todos se u^ vazia).
  acerto            s^ == s* (inclui s* == "" com s^ == "").
  fora_da_fase      material fora do laco (valor gravado do build): indeterminado.
  F1_identidade     s* == "" (gold vazio exige abstencao) | s* fora da taxonomia | U_g conhecido e T(s*) & U_g vazio.
  F2_unidade        u^ != "" e u^ nao pertence a T(s*): o indice restrito a u^ exclui a resposta.
  F5_alterada_depois s1 == s* e s^ != s*.
  F8_varios_assuntos s^ em S_acc - {s*}: escolheu assunto legitimo nao primario.
  F4_selecao        pont(s*) > 0 (candidata gerada) e s^ != s*: F4a abstencao (s^ == "") | F4b escolha errada.
  F3_nao_gerada     pont(s*) == 0. Divide-se pelo ALCANCE INSPECIONADO fora do indice atual:
                    F6_relacao_fora_do_indice: radical > 0 | secao do Moodle nomeia s* (`_secao_nomeia_subtopico`
                      aplicado so a s*) | bloco do cronograma nomeia s* (primary_topic_slug ou topic_candidates) |
                      indice documental liga expressao do material a s* (documento != o proprio material);
                    F7_relacao_nao_encontrada: nenhum dos quatro.
  indeterminado     nenhuma condicao acima.
  Flags: slug_duplicado (|T(s*)| > 1), multi_assunto (>= 2 candidatos em u^ com pontuacao >= 50 % do vencedor),
  meta_material, 2a_mudou, oraculo_unidade_acerta, e o alcance de cada fonte com contagem de topicos concorrentes.

Sem build, rede, LLM, commit. Uso: python wz2_diagnostico_causal_23-09.py [--reavaliar]
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
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
FINAL = HERE / "wx_gold_v2_final_22-09"
OUT_JSON = HERE / "wz2_diagnostico_causal_23-09.json"
OUT_MD = HERE / "wz2_diagnostico_causal_23-09_anexo.md"
CAP_BASE = DATA / ".frzero/wz2_captura_base_23-09.json"
CAP_ORAC = DATA / ".frzero/wz2_captura_oraculos_23-09.json"
CONG_WZ = DATA / ".frzero/wz_congelado_22-09.json"
SHA_WU = "c17786ef89c2e59a"
sys.path.insert(0, str(DATA))

from src.builder.routing import file_map as FM  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402
from src.builder.timeline import unit_matcher as UM  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402

CTX = {"sig": None, "eid": None, "fase": "1a", "modo": None}
CAP = {}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def gpath(nome):
    return FINAL / nome if (FINAL / nome).exists() else REP / nome


# ============================================================================ replay instrumentado
def rodar(modo, estado, ru, compare, oracle_units=None, block_units=None, pontuar=True):
    RA = ru.RA
    orig = {"md": ru._entry_markdown_text_for_file_map, "unit": ru.auto_unit, "sub": ru.auto_sub,
            "prop": RA.propagar_vocabulario_por_headings, "rec": FM.reconcile_unit_with_block, "read": ru.read}
    CAP[modo] = {}
    CTX["modo"] = modo

    def md_wrapper(root, entry):
        CTX["eid"] = str(entry.get("id"))
        CAP[modo][CTX["sig"]].setdefault(CTX["eid"], {})["no_laco"] = True
        return orig["md"](root, entry)

    def unit_wrapper(entry, units, text, topic_index=None, **kw):
        m = orig["unit"](entry, units, text, topic_index=topic_index, **kw)
        CAP[modo][CTX["sig"]].setdefault(str(entry["id"]), {})["unidade_bruta"] = {
            "slug": str(m.slug or ""), "conf": round(float(m.confidence or 0.0), 6), "amb": bool(m.ambiguous),
            "secao": str(getattr(m, "section_slug", "") or ""), "reasons": [str(r) for r in m.reasons]}
        return m

    def sub_wrapper(entry, taxonomy, markdown_text, winning_unit_slug="", **kw):
        m = orig["sub"](entry, taxonomy, markdown_text, winning_unit_slug=winning_unit_slug, **kw)
        rec = CAP[modo][CTX["sig"]].setdefault(str(entry["id"]), {})
        info = {"slug": str(m.topic_slug or ""), "conf": round(float(m.confidence or 0.0), 6), "amb": bool(m.ambiguous),
                "reasons": [str(r) for r in m.reasons], "unidade": str(winning_unit_slug or "")}
        if CTX["fase"] == "1a":
            sinais = ru.collect_entry_unit_signals(entry, markdown_text)
            pont = []
            for t in (ru._iter_content_taxonomy_topics(taxonomy) or []) if pontuar else []:
                ex = float(ru._score_entry_against_taxonomy_topic(sinais, t))
                st = float(ru._score_entry_against_taxonomy_topic(sinais, t, stem_fallback=True))
                if ex > 0 or st > 0:
                    pont.append([str(t.get("unit_slug") or ""), str(t.get("topic_slug") or ""), round(ex, 4), round(st, 4)])
            info["pontuacoes"] = pont
            rec["sub_1a"] = info
        else:
            rec["sub_2a_chamada"] = info
        return m

    def prop_wrapper(*a, **kw):
        CTX["fase"] = "2a"
        try:
            n = orig["prop"](*a, **kw)
            CAP[modo][CTX["sig"]].setdefault("__curso__", {})["mudou_2a"] = n
            return n
        finally:
            CTX["fase"] = "1a"

    def rec_wrapper(**kw):
        slug, reasons, conflict = orig["rec"](**kw)
        alvo = (oracle_units or {}).get(CTX["sig"], {}).get(CTX["eid"])
        if alvo:
            return alvo, list(reasons) + ["oraculo-unidade"], conflict
        return slug, reasons, conflict

    try:
        ru._entry_markdown_text_for_file_map = md_wrapper
        ru.auto_unit = unit_wrapper
        ru.auto_sub = sub_wrapper
        RA.propagar_vocabulario_por_headings = prop_wrapper
        if oracle_units is not None:
            FM.reconcile_unit_with_block = rec_wrapper
        for sig, v in estado.items():
            CTX["sig"] = sig
            CTX["fase"] = "1a"
            CAP[modo][sig] = {}
            feed = [copy.deepcopy(e) for e in v["feed"]]
            trocas = (block_units or {}).get(sig) or {}

            def patched(path, _feed=feed, _trocas=trocas):
                data = orig["read"](path)
                nome = Path(path).name
                if nome == "manifest.json":
                    data = {**data, "entries": _feed}
                elif nome == ".timeline_index.json" and _trocas:
                    blocos = copy.deepcopy(data["blocks"])
                    for b in blocos:
                        nu = _trocas.get(str(b.get("id")))
                        if nu and str(b.get("unit_slug") or ""):
                            b["unit_slug"] = nu
                    data = {**data, "blocks": blocos}
                return data

            ru.read = patched
            try:
                _, novo, _raw = ru.replay(v["root"])
            finally:
                ru.read = orig["read"]
            for eid, e in novo.items():
                rec = CAP[modo][sig].setdefault(eid, {})
                rec["final"] = {"bloco": compare.predictions(v["root"], e)[0],
                                "unidade": str(e.get("computed_unit_slug") or ""),
                                "unit_reasons": [str(r) for r in e.get("unit_match_reasons") or []],
                                "sub": str(e.get("computed_subunit_slug") or ""),
                                "sub_reasons": [str(r) for r in e.get("subunit_match_reasons") or []],
                                "sub_conf": round(float(e.get("subunit_match_confidence") or 0.0), 6),
                                "cobertura": sorted({str(c.get("unit_slug") or "") for c in e.get("coverage_units") or []})}
            print("  replay", modo, sig, len(novo), round(time.time() - T0), "s", flush=True)
    finally:
        ru._entry_markdown_text_for_file_map = orig["md"]
        ru.auto_unit, ru.auto_sub, ru.read = orig["unit"], orig["sub"], orig["read"]
        RA.propagar_vocabulario_por_headings = orig["prop"]
        FM.reconcile_unit_with_block = orig["rec"]
        CTX["fase"] = "1a"
    return CAP[modo]


# ============================================================================ DP posicional (funcao pura)
def roda_dp(cand, units, desvio=True, ancora=True):
    guard = (UM.DETOUR_MIN_GAIN, UM.ANCHOR_MIN_AFF)
    try:
        if not desvio:
            UM.DETOUR_MIN_GAIN = float("inf")
        if not ancora:
            UM.ANCHOR_MIN_AFF = float("inf")
        res = UM.assign_units_positional(cand, units)
        return [s for s, _ in res], [c for _, c in res]
    finally:
        UM.DETOUR_MIN_GAIN, UM.ANCHOR_MIN_AFF = guard


def decompor_dp(root):
    blocos = read(root / "course/.timeline_index.json")["blocks"]
    units = read(root / "course/.content_taxonomy.json").get("units", []) or []
    uslugs = [str(u.get("slug") or "") for u in units]
    cand = [b for b in blocos if str(b.get("auto_unit_slug") or "")]
    full, conf = roda_dp(cand, units)
    sem_desvio, _ = roda_dp(cand, units, desvio=False)
    sem_ancora, _ = roda_dp(cand, units, ancora=False)
    puro, _ = roda_dp(cand, units, desvio=False, ancora=False)
    tit = [UM._tokens(str(u.get("title") or "")) - UM._UNIT_GENERIC for u in units]
    utok = [UM._unit_tokens(u) for u in units]
    out = {}
    for i, b in enumerate(cand):
        bt = UM._block_tokens(b)
        aff = [len(bt & utok[j]) for j in range(len(units))]
        aff_sem_titulo = [len(bt & (utok[j] - tit[j])) for j in range(len(units))]
        u = uslugs.index(full[i]) if full[i] in uslugs else -1
        mx = max(aff) if aff else 0
        if mx == 0:
            classe = "sem_sinal"
        elif u >= 0 and aff[u] == mx:
            classe = "sinal_proprio_unico" if sum(1 for a in aff if a == mx) == 1 else "sinal_proprio_empatado"
        else:
            classe = "contra_argmax"
        if full[i] == puro[i]:
            mec = "dp_puro"
        elif full[i] == sem_ancora[i]:
            mec = "desvio"
        elif full[i] == sem_desvio[i]:
            mec = "ancora"
        else:
            mec = "desvio+ancora"
        mx2 = max(aff_sem_titulo) if aff_sem_titulo else 0
        cabecalho = bool(u >= 0 and aff[u] == mx and mx > 0 and (mx2 == 0 or aff_sem_titulo[u] < mx2))
        ant = full[i - 1] if i > 0 else None
        seg = full[i + 1] if i + 1 < len(cand) else None
        out[str(b.get("id"))] = {
            "ordem": i, "kind": b.get("kind"), "unit_slug_gravada": str(b.get("unit_slug") or ""),
            "auto_unit_slug": str(b.get("auto_unit_slug") or ""), "dp_recomputado": full[i], "conf_dp": conf[i],
            "fiel": full[i] == str(b.get("auto_unit_slug") or ""), "puro": puro[i], "sem_desvio": sem_desvio[i],
            "sem_ancora": sem_ancora[i], "classe": classe, "mecanismo": mec, "cabecalho": cabecalho,
            "afinidade": dict(zip(uslugs, aff)), "afinidade_sem_titulo": dict(zip(uslugs, aff_sem_titulo)),
            "posicao": "borda" if ant is None or seg is None else ("interior" if ant == seg == full[i] else "fronteira"),
            "periodo": [str(b.get("period_start") or "")[:10], str(b.get("period_end") or b.get("period_start") or "")[:10]],
            "rotulo": " / ".join(str(s.get("label", "")) for s in (b.get("sessions") or []) if isinstance(s, dict))[:160],
        }
    return out, blocos


# ============================================================================ indice documental (W-U)
def indice_documental(wu, raizes, universo_por_curso):
    indice = collections.defaultdict(list)
    vistos = set()
    for sig, nome in wu.NOMES.items():
        universo = universo_por_curso.get(sig) or set()
        if not universo:
            continue
        root = raizes[sig]
        topicos, por_inicio = wu.carrega_topicos(root)

        def emite(gen, _sig=sig):
            for e, t, doc, trecho, padrao in gen:
                chave = (_sig, e, t, doc, padrao)
                if chave in vistos:
                    continue
                vistos.add(chave)
                indice[(_sig, e)].append({"unit_slug": t[0], "topico": t[1], "doc": doc, "trecho": trecho, "padrao": padrao})

        for entry in wu.read_json(root / "manifest.json").get("entries", []):
            texto = wu._entry_markdown_text_for_file_map(root, entry) or ""
            if texto.strip():
                emite(wu.relacoes_do_documento(texto, "material:" + str(entry.get("id")), universo, por_inicio, "P1", so_estrutura=True))
        for rel in ("course/SYLLABUS.md", "course/CRONOGRAMA_DETALHADO.md", "course/GLOSSARY.md",
                    "course/COURSE_IDENTITY.md", "course/SOURCE_REGISTRY.yaml"):
            if (root / rel).exists():
                emite(wu.relacoes_do_documento(wu.read_text(root / rel), rel, universo, por_inicio, "P4", so_estrutura=False))
        inputs = root / "_inputs_15-09.json"
        if inputs.exists():
            perfil = wu.read_json(inputs).get("profile_input") or {}
            for campo in ("teaching_plan", "syllabus"):
                texto = str(perfil.get(campo) or "")
                if texto.strip():
                    emite(wu.relacoes_do_documento(texto, "_inputs_15-09.json:" + campo, universo, por_inicio, "P4", so_estrutura=False))
        tl = root / "course/.timeline_index.json"
        if tl.exists():
            emite(wu.relacoes_do_plano(wu.read_json(tl).get("blocks") or [], "course/.timeline_index.json", universo, por_inicio))
        li = root / "course/.lessons_index.json"
        if li.exists():
            emite(wu.relacoes_do_plano(wu.blocos_de_licoes(wu.read_json(li)), "course/.lessons_index.json", universo, por_inicio))
    return indice


def expressoes_v2(wp1, raizes, nomes):
    from src.builder.core.code_summarization import load_code_curation
    por_mat, universo = {}, collections.defaultdict(set)
    for sig in nomes:
        root = raizes[sig]
        curation = load_code_curation(root).get("entries", {}) or {}
        por_mat[sig] = {}
        for entry in read(root / "manifest.json").get("entries", []):
            ks = set()
            for _campo, cru in wp1.campos_do_material(root, entry, curation):
                ks |= set(wp1.ngramas(cru))
            por_mat[sig][str(entry.get("id"))] = sorted(ks)
            universo[sig] |= ks
    return por_mat, universo


# ============================================================================ gold e proveniencia
def proveniencia_unidade(sig):
    mgt = {}
    p = gpath(f"material_gt_{sig}.csv")
    if p.exists():
        for r in csv_rows(p):
            if (r.get("scorable") or "yes").strip().lower() != "yes":
                continue
            units = [u.strip() for u in str(r.get("gold_units") or "").split("|") if u.strip()]
            if not units:
                continue
            txt = f"{r.get('gold_fonte') or ''} {r.get('notas') or ''}".lower()
            if "ruling" in txt:          # adjudicacao humana registrada (inclui ruling posterior a proposta por secao)
                cat = "ruling_usuario"
            elif "secao-moodle" in txt:
                cat = "secao_moodle"
            elif "conteudo" in txt or "conteúdo" in txt:
                cat = "conteudo"
            else:
                cat = "proposto"
            mgt[str(r.get("entry_id") or "").strip()] = {"cat": cat, "multi": len(units) > 1}
    via_bloco = set()
    gu_fix, gt = FIX / f"gold_units_{sig}.csv", REP / f"ground_truth_{sig}.csv"
    true_block_uuid = {}
    if gu_fix.exists() and gt.exists():
        uu = {(r.get("block_uuid") or "").strip() for r in csv_rows(gu_fix) if (r.get("true_unit") or "").strip()}
        for r in csv_rows(gt):
            if (r.get("scorable") or "").strip().lower() == "yes" and (r.get("true_block_uuid") or "").strip() in uu:
                via_bloco.add(r["id"])
                true_block_uuid[r["id"]] = (r.get("true_block_uuid") or "").strip()
    return mgt, via_bloco


def gold_por_bloco(sig, blocos):
    """{display_id: true_unit} por (date_start, date_end) exatos; senao sobreposicao com unidade unica."""
    p = FIX / f"gold_units_{sig}.csv"
    if not p.exists():
        return {}, {}
    gu = [r for r in csv_rows(p) if (r.get("true_unit") or "").strip()]
    out, como = {}, {}
    for b in blocos:
        ps = str(b.get("period_start") or "")[:10]
        pe = str(b.get("period_end") or b.get("period_start") or "")[:10]
        ex = [g for g in gu if g["date_start"] == ps and g["date_end"] == pe]
        if ex:
            out[str(b.get("id"))], como[str(b.get("id"))] = ex[0]["true_unit"].strip(), "data_exata"
            continue
        ov = {g["true_unit"].strip() for g in gu if g["date_start"] <= ps <= g["date_end"] or ps <= g["date_start"] <= pe}
        if len(ov) == 1:
            out[str(b.get("id"))], como[str(b.get("id"))] = next(iter(ov)), "sobreposicao"
    return out, como


def taxonomia_slug_unidades(root):
    out = collections.defaultdict(set)
    for u in read(root / "course/.content_taxonomy.json").get("units", []) or []:
        for t in u.get("topics", []) or []:
            if t.get("slug"):
                out[str(t["slug"])].add(str(u.get("slug") or ""))
    return out


def mecanismo_unidade(reasons):
    rs = " ".join(reasons)
    for tag, nome in (("oraculo-unidade", "oraculo"), ("unidade_do_bloco_manual", "bloco_manual"),
                      ("reconciliada_do_bloco=", "reconciliada"), ("herdada_do_vizinho=", "vizinho"),
                      ("herdada_do_bloco=", "herdada"), ("secao-vence-bloco=", "secao"),
                      ("explicita-vence-bloco=", "explicita"), ("texto-vence-vizinho=", "texto_vence_vizinho")):
        if tag in rs:
            return nome
    if "manual" in reasons:
        return "unidade_manual"
    return "concorda_ou_sem_bloco"


# ============================================================================ main
def main():
    reavaliar = "--reavaliar" in sys.argv
    if not reavaliar:
        assert not OUT_JSON.exists(), "preservar evidencia existente"
    compare = load("wz2_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    wx = load("wz2_wx", HERE / "wx_regua_corrigida_22-09.py")
    rb = load("wz2_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wz2_ru", HERE / "replay_unidade_21-09.py")
    wz = load("wz2_wz", HERE / "wz_bloco_cobertura_22-09.py")
    wu = load("wz2_wu", HERE / "wu_cobertura_relacoes_22-09.py")
    wp1 = load("wz2_wp1", HERE / "wp1_inventario_matriz_22-09.py")
    nomes, uni = mede.NOMES, mede.UNI
    raizes = {sig: wz.root_de(sig, nomes) for sig in nomes}
    declaracao = {"doc": __doc__, "raizes": {s: str(p.relative_to(DATA)) for s, p in raizes.items()},
                  "unit_tag": T.UNIT_TAG, "subunit_tag": T.SUBUNIT_TAG, "propag_conf": T.SUBUNIT_PROPAG_CONF}
    sha_decl = sha(declaracao)
    print("DECLARACAO", sha_decl, flush=True)

    # ---------------- fase de bloco (determinista, 5 s): decisoes do motor temporal
    estado = {}
    for sig in nomes:
        saved, bloco_novo, decisoes, _ = rb.replay(raizes[sig])
        estado[sig] = {"root": raizes[sig], "saved": saved, "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo],
                       "decisoes": decisoes}
    print("bloco ok", round(time.time() - T0), "s", flush=True)

    # ---------------- base instrumentada + DP + indice documental: SEM GOLD
    if reavaliar:
        cb = read(CAP_BASE)
        assert cb["sha256_declaracao"] == sha_decl, "declaracao mudou"
        CAP["base"] = cb["base"]
        dp, indice_rel, expr = cb["dp"], None, cb["expressoes"]
        rel_por_expr = {tuple(k.split("\x1f")): v for k, v in cb["indice_por_expressao"].items()}
        sha_base, sha_dp, sha_idx, fid_wu = cb["sha256_base"], cb["sha256_dp"], cb["sha256_indice"], cb["fidelidade_wu"]
        assert sha(CAP["base"]) == sha_base
    else:
        rodar("base", estado, ru, compare)
        sha_base = sha(CAP["base"])
        dp = {}
        for sig in nomes:
            dp[sig], _ = decompor_dp(raizes[sig])
        sha_dp = sha(dp)
        # fidelidade do laco do indice: raizes e universo do W-U reproduzem o sha do W-U
        antigo = {sig: DATA / (".frzero/pacote_categoria_17-09" if sig in wu.CATEGORIA else ".frzero/pacote_fontes_15-09") / n
                  for sig, n in nomes.items()}
        bruto = read(HERE / "wp1_inventario_matriz_22-09.json")
        uni_wu = collections.defaultdict(set)
        for e in bruto["expressoes"]:
            uni_wu[e["curso"]].add(e["chave"])
        for m in bruto["materiais"]:
            uni_wu[m["curso"]].update(m["expressoes"])
        sha_wu_rep, n_wu = wu.sha_indice(indice_documental(wu, antigo, uni_wu))
        fid_wu = {"sha_reproduzido": sha_wu_rep, "relacoes": n_wu, "igual_ao_wu": sha_wu_rep.startswith(SHA_WU)}
        print("FIDELIDADE indice W-U:", fid_wu, round(time.time() - T0), "s", flush=True)
        expr, universo = expressoes_v2(wp1, raizes, nomes)
        indice_rel = indice_documental(wu, raizes, universo)
        sha_idx, n_idx = wu.sha_indice(indice_rel)
        rel_por_expr = {k: [[r["unit_slug"], r["topico"], r["doc"], r["padrao"]] for r in v] for k, v in indice_rel.items()}
        print("indice v2", n_idx, "relacoes", round(time.time() - T0), "s", flush=True)
        CAP_BASE.write_text(json.dumps({"sha256_declaracao": sha_decl, "sha256_base": sha_base, "sha256_dp": sha_dp,
                                        "sha256_indice": sha_idx, "fidelidade_wu": fid_wu, "base": CAP["base"], "dp": dp,
                                        "expressoes": expr,
                                        "indice_por_expressao": {"\x1f".join(k): v for k, v in rel_por_expr.items()}},
                                       ensure_ascii=False), encoding="utf-8")
    print("CONGELAMENTO base", sha_base[:16], "dp", sha_dp[:16], "indice", sha_idx[:16], flush=True)

    # ---------------- fidelidade da base contra o congelamento do W-Z (por ID, sem gold)
    wzc = read(CONG_WZ)
    assert wzc["sha256_congelamento"].startswith("788e4372"), "congelamento do W-Z inesperado"
    divergencias = []
    for sig in nomes:
        for eid, d in wzc["saidas"]["base"][sig].items():
            f = CAP["base"][sig].get(eid, {}).get("final") or {}
            if (f.get("bloco"), f.get("unidade"), f.get("sub")) != (d["bloco"], d["unidade"], d["sub"]):
                divergencias.append([sig, eid])
    print("FIDELIDADE base x W-Z:", "igual" if not divergencias else divergencias[:5], flush=True)
    assert not divergencias, "instrumentacao mudou decisao"

    # ================================================================ GOLD entra aqui
    wz.preparar_avaliacao(estado, compare, mede, wx)
    tax = {sig: taxonomia_slug_unidades(raizes[sig]) for sig in nomes}
    blocos = {sig: read(raizes[sig] / "course/.timeline_index.json")["blocks"] for sig in nomes}
    gold_bloco, gold_bloco_como = {}, {}
    for sig in nomes:
        gold_bloco[sig], gold_bloco_como[sig] = gold_por_bloco(sig, blocos[sig])
    oracle_units, oracle_meta = {}, collections.Counter()
    for sig, v in estado.items():
        gb, gu, gs, gsp = v["golds"]
        oracle_units[sig] = {}
        sub_ids = {r["entry_id"] for r in v["rows"] if r["sub_primario"] != ""}
        uni_ids = {r["entry_id"] for r in v["rows"] if r["unidade"] != ""}
        for gid in sorted(sub_ids | uni_ids):
            eid = v["eid_de"].get(gid)
            if not eid:
                continue
            ug = set(gu.get(gid) or ()) if gid in uni_ids else set()
            sstar = next(iter(gsp[gid])) if gid in sub_ids else ""
            alvo = ""
            if gid in sub_ids and sstar:
                c = (tax[sig].get(sstar, set()) & ug) if ug else set(tax[sig].get(sstar, set()))
                alvo = next(iter(c)) if len(c) == 1 else ""
                oracle_meta["sub_coerente" if alvo else "sub_incoerente_ou_ambiguo"] += 1
            elif len(ug) == 1:
                alvo = next(iter(ug))
                oracle_meta["so_unidade"] += 1
            else:
                oracle_meta["sem_oraculo"] += 1
            if alvo:
                assert eid not in oracle_units[sig] or oracle_units[sig][eid] == alvo, (sig, eid)
                oracle_units[sig][eid] = alvo
    block_units = {sig: {bid: u for bid, u in gold_bloco[sig].items()} for sig in nomes if gold_bloco[sig]}

    if reavaliar and CAP_ORAC.exists():
        co = read(CAP_ORAC)
        CAP["oraculo_unidade"], CAP["oraculo_bloco"] = co["oraculo_unidade"], co["oraculo_bloco"]
    else:
        rodar("oraculo_unidade", estado, ru, compare, oracle_units=oracle_units)
        rodar("oraculo_bloco", estado, ru, compare, block_units=block_units, pontuar=False)
        CAP_ORAC.write_text(json.dumps({"oraculo_unidade": CAP["oraculo_unidade"], "oraculo_bloco": CAP["oraculo_bloco"]},
                                       ensure_ascii=False), encoding="utf-8")
    print("oraculos ok", round(time.time() - T0), "s", flush=True)

    relatorio = avaliar_tudo(estado, nomes, uni, tax, dp, blocos, gold_bloco, gold_bloco_como, expr, rel_por_expr,
                             ru, wz, oracle_meta, oracle_units)
    relatorio.update({"escopo": __doc__, "sha256_declaracao": sha_decl, "sha256_base": sha_base, "sha256_dp": sha_dp,
                      "sha256_indice_documental": sha_idx, "fidelidade_indice_wu": fid_wu,
                      "fidelidade_base_wz": "igual por ID (bloco, unidade, subunidade) ao congelamento 788e4372",
                      "raizes": declaracao["raizes"],
                      "arquivos_gold_sha16": {str(p.relative_to(DATA)): hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                                              for sig in nomes for p in [gpath(f"material_gt_{sig}.csv"), gpath(f"subunit_gt_{sig}.csv"),
                                                                         REP / f"ground_truth_{sig}.csv", FIX / f"gold_units_{sig}.csv"]
                                              if p.exists()},
                      "segundos": round(time.time() - T0, 1)})
    OUT_JSON.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    escreve_anexo(relatorio)
    print("OK", OUT_JSON.name, hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()[:16], relatorio["segundos"], "s", flush=True)


# ============================================================================ avaliacao
def avaliar_tudo(estado, nomes, uni, tax, dp, blocos, gold_bloco, gold_bloco_como, expr, rel_por_expr, ru, wz,
                 oracle_meta, oracle_units):
    RA = ru.RA
    R = {"oraculo_cobertura": dict(oracle_meta),
         "oraculo_unidade_n": {s: len(v) for s, v in oracle_units.items()}}
    modos = ("base", "oraculo_unidade", "oraculo_bloco")

    # ---------------- placar dos 3 modos por curso + ganhos/perdas por ID
    placar, flags = {}, {}
    for modo in modos:
        placar[modo], flags[modo] = {}, {}
        for sig, v in estado.items():
            gb, gu, gs, gsp = v["golds"]
            c = collections.Counter()
            for row in v["rows"]:
                gid = row["entry_id"]
                eid = v["eid_de"].get(gid)
                f = (CAP[modo][sig].get(eid) or {}).get("final") if eid else None
                if row["bloco"] != "":
                    c["bloco_n"] += 1
                    c["bloco"] += bool(f and f["bloco"] == gb[gid])
                if row["unidade"] != "":
                    c["unidade_n"] += 1
                    ok = bool(f and f["unidade"] in gu[gid])
                    c["unidade"] += ok
                    flags[modo][f"{sig}|{gid}|unidade"] = ok
                if row["sub_primario"] != "":
                    c["sub_n"] += 1
                    okp, oka = bool(f and f["sub"] in gsp[gid]), bool(f and f["sub"] in gs[gid])
                    c["sub_primaria"] += okp
                    c["sub_aceita"] += oka
                    flags[modo][f"{sig}|{gid}|sub_primaria"] = okp
                    flags[modo][f"{sig}|{gid}|sub_aceita"] = oka
            placar[modo][sig] = dict(c)
        tot = collections.Counter()
        for c in placar[modo].values():
            tot.update(c)
        placar[modo]["TOTAL"] = dict(tot)
    R["placar"] = placar
    R["mudancas_vs_base"] = {}
    for modo in modos[1:]:
        d = {}
        for eixo in ("unidade", "sub_primaria", "sub_aceita"):
            ks = [k for k in flags["base"] if k.endswith("|" + eixo)]
            d[eixo] = {"ganhos": sorted(k.rsplit("|", 1)[0] for k in ks if not flags["base"][k] and flags[modo].get(k)),
                       "perdas": sorted(k.rsplit("|", 1)[0] for k in ks if flags["base"][k] and not flags[modo].get(k))}
        R["mudancas_vs_base"][modo] = d

    # ---------------- Q6: eixo bloco
    erros_bloco = []
    for sig, v in estado.items():
        gb = v["golds"][0]
        for row in v["rows"]:
            if row["bloco"] == "":
                continue
            gid = row["entry_id"]
            eid = v["eid_de"].get(gid)
            f = (CAP["base"][sig].get(eid) or {}).get("final") if eid else None
            if f and f["bloco"] == gb[gid]:
                continue
            d = (v["decisoes"].get(eid) or {}) if eid else {}
            erros_bloco.append({"curso": sig, "gold_id": gid, "entry_id": eid, "previsto": (f or {}).get("bloco"),
                                "gold": gb[gid], "metodo": d.get("method"), "banda": d.get("band"), "flag": d.get("flag"),
                                "provedor": d.get("provider"), "janela": d.get("window"),
                                "gold_na_janela": gb[gid] in (d.get("window") or []),
                                "categoria": (v["saved"].get(eid) or {}).get("category") if eid else None,
                                "titulo": (v["saved"].get(eid) or {}).get("title") if eid else None})
    R["bloco_erros"] = erros_bloco

    # ---------------- Q1/Q2: unidade -- DP, proveniencia, mecanismo, votos independentes
    dp_tab, mat_uni, erros_uni = [], [], []
    for sig in nomes:
        for bid, d in dp[sig].items():
            gbu = gold_bloco[sig].get(bid)
            dp_tab.append({"curso": sig, "bloco": bid, **{k: d[k] for k in ("classe", "mecanismo", "cabecalho", "posicao", "fiel",
                                                                          "kind", "dp_recomputado", "conf_dp", "rotulo", "periodo")},
                           "afinidade_max": max(d["afinidade"].values()) if d["afinidade"] else 0,
                           "gold_bloco": gbu, "gold_bloco_como": gold_bloco_como[sig].get(bid),
                           "correto": (d["dp_recomputado"] == gbu) if gbu else None})
    R["dp_blocos"] = dp_tab
    R["dp_fidelidade"] = {sig: [sum(1 for d in dp[sig].values() if d["fiel"]), len(dp[sig])] for sig in nomes}

    def fonte_da_unidade_do_bloco(sig, bid):
        if not bid:
            return "sem_bloco", "", ""
        slug, viz = FM.unit_of_block_or_neighbor(bid, blocos[sig])
        if viz:
            cls = (dp[sig].get(viz) or {}).get("classe", "vizinho_nao_dp")
            return f"vizinho:{cls}", slug, viz
        if not slug:
            return "sem_unidade", "", ""
        if bid in dp[sig]:
            return dp[sig][bid]["classe"], slug, ""
        return "unidade_nao_dp", slug, ""

    feed_de = {sig: {str(e["id"]): e for e in v["feed"]} for sig, v in estado.items()}
    for sig, v in estado.items():
        gb, gu, gs, gsp = v["golds"]
        if sig not in uni:
            continue
        mgt, via_bloco = proveniencia_unidade(sig)
        for row in v["rows"]:
            if row["unidade"] == "":
                continue
            gid = row["entry_id"]
            eid = v["eid_de"].get(gid)
            rec = CAP["base"][sig].get(eid) or {} if eid else {}
            f = rec.get("final")
            if f is None:
                continue
            mec = mecanismo_unidade(f["unit_reasons"])
            fonte, bu, viz = fonte_da_unidade_do_bloco(sig, f["bloco"])
            gbu = gold_bloco[sig].get(f["bloco"]) if f["bloco"] else None
            prov = f"material_gt:{mgt[gid]['cat']}" if gid in mgt else ("bloco_gold" if gid in via_bloco else "?")
            ub = rec.get("unidade_bruta") or {}
            fe = feed_de[sig].get(eid) or {}
            origem_bloco = ("temporal" if fe.get("temporal_block_id") else "manual" if fe.get("manual_timeline_block_id")
                            else "computed_antigo" if fe.get("computed_block_id") else "nenhum")
            item = {"curso": sig, "gold_id": gid, "entry_id": eid, "acerto": f["unidade"] in gu[gid], "previsto": f["unidade"],
                    "origem_do_bloco_usado": origem_bloco,
                    "gold": sorted(gu[gid]), "mecanismo": mec, "bloco": f["bloco"], "bloco_certo": f["bloco"] == gb.get(gid),
                    "fonte_unidade_bloco": fonte, "unidade_do_bloco": bu, "vizinho": viz, "gold_do_bloco": gbu,
                    "unidade_do_bloco_certa_pelo_gold_de_bloco": (bu == gbu) if (gbu and bu) else None,
                    "proveniencia_gold": prov, "multi": len(gu[gid]) > 1,
                    "bruto": ub.get("slug"), "bruto_conf": ub.get("conf"), "bruto_amb": ub.get("amb"),
                    "bruto_gated": bool(ub.get("slug") and not ub.get("amb") and (ub.get("conf") or 0) >= T.UNIT_TAG),
                    "bruto_acertaria": bool(ub.get("slug") and ub.get("slug") in gu[gid]), "secao": ub.get("secao"),
                    "secao_acertaria": bool(ub.get("secao") and ub.get("secao") in gu[gid])}
            mat_uni.append(item)
            if not item["acerto"]:
                dec = {"unidade": f["unidade"], "reasons": f["unit_reasons"]}
                item["classe_anatomia"] = wz.classe_do_erro(dec, item["bloco_certo"])
                erros_uni.append(item)
    R["unidade_materiais"] = mat_uni
    R["unidade_erros"] = erros_uni

    # votos independentes do gold por bloco (todos os materiais do bloco, com ou sem gold)
    votos = []
    for sig in nomes:
        por_bloco = collections.defaultdict(list)
        for eid, rec in CAP["base"][sig].items():
            f = rec.get("final") if isinstance(rec, dict) else None
            if not f or not rec.get("no_laco") or not f.get("bloco"):
                continue
            por_bloco[f["bloco"]].append(rec)
        for bid, recs in por_bloco.items():
            fonte, bu, _ = fonte_da_unidade_do_bloco(sig, bid)
            vt, vs = collections.Counter(), collections.Counter()
            for rec in recs:
                ub = rec.get("unidade_bruta") or {}
                if ub.get("slug") and not ub.get("amb") and (ub.get("conf") or 0) >= T.UNIT_TAG:
                    vt[ub["slug"]] += 1
                if ub.get("secao"):
                    vs[ub["secao"]] += 1

            def maioria(c):
                if not c:
                    return None
                top = c.most_common()
                return top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else "empate"
            votos.append({"curso": sig, "bloco": bid, "fonte_unidade_bloco": fonte, "unidade_do_bloco": bu,
                          "gold_do_bloco": gold_bloco[sig].get(bid), "n_materiais": len(recs),
                          "votos_texto_gated": dict(vt), "votos_secao": dict(vs),
                          "maioria_texto": maioria(vt), "maioria_secao": maioria(vs)})
    R["votos_independentes_por_bloco"] = votos

    # ---------------- Q3/Q4/Q5: subunidade
    familias = {}
    for modo in ("base", "oraculo_unidade"):
        itens = []
        for sig, v in estado.items():
            gb, gu, gs, gsp = v["golds"]
            topicos = {t["topic_slug"]: t for t in ru._iter_content_taxonomy_topics(
                read(raizes_de(estado)[sig] / "course/.content_taxonomy.json"))}
            por_id_bloco = {str(b.get("id")): b for b in blocos[sig]}
            for row in v["rows"]:
                if row["sub_primario"] == "":
                    continue
                gid = row["entry_id"]
                eid = v["eid_de"].get(gid)
                rec = (CAP[modo][sig].get(eid) or {}) if eid else {}
                f = rec.get("final")
                sstar = next(iter(gsp[gid]))
                sacc = set(gs[gid])
                ug = set(gu.get(gid) or ()) if sig in uni and gid in gu else set()
                it = {"curso": sig, "gold_id": gid, "entry_id": eid, "gold": sstar, "aceitos": sorted(sacc), "gold_unidade": sorted(ug)}
                if f is None:
                    it.update({"familia": "indeterminado_ausente"})
                    itens.append(it)
                    continue
                uhat, shat = f["unidade"], f["sub"]
                s1 = (rec.get("sub_1a") or {}).get("slug")
                pont = (rec.get("sub_1a") or {}).get("pontuacoes") or []
                Ts = tax[sig].get(sstar, set()) if sstar else set()
                restr = [p for p in pont if (not uhat or p[0] == uhat)]
                ex_r = [p for p in restr if p[2] > 0]
                ex_r.sort(key=lambda p: -p[2])
                g_restr = max([p[2] for p in restr if p[1] == sstar] or [0.0])
                g_any = max([p[2] for p in pont if p[1] == sstar] or [0.0])
                g_stem = max([p[3] for p in pont if p[1] == sstar] or [0.0])
                rank = next((i + 1 for i, p in enumerate(ex_r) if p[1] == sstar), None)
                vencedor = ex_r[0][2] if ex_r else 0.0
                multi = sum(1 for p in ex_r if vencedor > 0 and p[2] >= 0.5 * vencedor) >= 2
                # alcance fora do indice
                entry = estado[sig]["saved"].get(eid) or {}
                tdict = topicos.get(sstar)
                secao_nomeia = bool(tdict and RA._secao_nomeia_subtopico(entry, [tdict], MOTOR_GENERIC_STEMS))
                secao_n = sum(1 for t in topicos.values() if RA._secao_nomeia_subtopico(entry, [t], MOTOR_GENERIC_STEMS)) if entry else 0
                bl = por_id_bloco.get(f["bloco"]) or {}
                cands_bloco = [str(c.get("topic_slug") or "") for c in (bl.get("topic_candidates") or [])]
                bloco_primario = str(bl.get("primary_topic_slug") or "") == sstar and bool(sstar)
                bloco_cand = sstar in cands_bloco if sstar else False
                rels = []
                for e in (expr.get(sig) or {}).get(eid, []):
                    for r in rel_por_expr.get((sig, e), []):
                        if r[2] != "material:" + str(eid):
                            rels.append(r)
                rel_gold = [r for r in rels if r[1] == sstar]
                rel_outros = {r[1] for r in rels if r[1] != sstar}
                alc = {"radical": g_stem > 0, "secao": secao_nomeia, "bloco": bloco_primario or bloco_cand,
                       "documental": bool(rel_gold)}
                it.update({"unidade_prevista": uhat, "sub_prevista": shat, "sub_1a": s1, "no_laco": bool(rec.get("no_laco")),
                           "T_gold": sorted(Ts), "slug_duplicado": len(Ts) > 1,
                           "pont_gold_na_unidade": g_restr, "pont_gold_qualquer": g_any, "pont_gold_radical": g_stem,
                           "rank_gold": rank, "n_candidatos": len(ex_r), "multi_assunto": multi,
                           "vencedor_1a": ex_r[0][1] if ex_r else "", "sub_reasons": f["sub_reasons"],
                           "meta": any(r.startswith("meta-material") for r in f["sub_reasons"]),
                           "manual": "manual" in f["sub_reasons"],
                           "2a_mudou": bool(s1 is not None and s1 != shat),
                           "razao_2a": next((r for r in f["sub_reasons"] if r in ("propagado-headings", "rotulo-decomposto",
                                                                                   "titulo-nomeia-subtopico", "secao-nomeia-subtopico")), ""),
                           "alcance": alc, "secao_nomeia_n_topicos": secao_n, "bloco_n_candidatos": len(cands_bloco),
                           "documental_padroes": sorted({r[3] for r in rel_gold}), "documental_outros_topicos": len(rel_outros),
                           "cobertura_contem_gold": bool(Ts & set(f["cobertura"]))})
                if shat == sstar:
                    fam = "acerto"
                elif not rec.get("no_laco"):
                    fam = "fora_da_fase"
                elif sstar == "" or not Ts or (ug and not (Ts & ug)):
                    fam = "F1_identidade"
                elif uhat and uhat not in Ts:
                    fam = "F2_unidade"
                elif s1 == sstar:
                    fam = "F5_alterada_depois"
                elif shat and shat in sacc:
                    fam = "F8_varios_assuntos"
                elif g_restr > 0:
                    fam = "F4a_abstencao" if not shat else "F4b_escolha_errada"
                elif g_restr == 0:
                    fam = "F6_relacao_fora_do_indice" if any(alc.values()) else "F7_relacao_nao_encontrada"
                else:
                    fam = "indeterminado"
                it["familia"] = fam
                if fam == "F1_identidade":
                    it["F1_motivo"] = ("gold_vazio" if sstar == "" else "fora_da_taxonomia" if not Ts else "unidade_x_sub_incoerente")
                itens.append(it)
        familias[modo] = itens
    R["subunidade_familias"] = familias

    # 2a passada: doadores da propagacao (1a confiante na mesma (unidade, topico)) e sua correcao pelo gold
    doadores = []
    for sig, v in estado.items():
        gsp = v["golds"][3]
        gid_de = {e: g for g, e in v["eid_de"].items() if e}
        conf1 = collections.defaultdict(list)
        for eid, rec in CAP["base"][sig].items():
            s1 = rec.get("sub_1a") if isinstance(rec, dict) else None
            if s1 and s1["slug"] and not s1["amb"] and s1["conf"] >= T.SUBUNIT_PROPAG_CONF:
                conf1[(s1["unidade"], s1["slug"])].append(eid)
        for it in familias["base"]:
            if it.get("curso") != sig or it.get("razao_2a") != "propagado-headings":
                continue
            ds = [d for d in conf1.get((it["unidade_prevista"], it["sub_prevista"]), []) if d != it["entry_id"]]
            com_gold = [d for d in ds if gid_de.get(d) in gsp]
            certos = [d for d in com_gold if (CAP["base"][sig][d].get("sub_1a") or {}).get("slug") in gsp[gid_de[d]]]
            doadores.append({"curso": sig, "gold_id": it["gold_id"], "sub_prevista": it["sub_prevista"], "acerto": it["familia"] == "acerto",
                             "sub_1a": it["sub_1a"], "gold": it["gold"], "n_doadores": len(ds), "doadores_com_gold": len(com_gold),
                             "doadores_certos": len(certos)})
    R["segunda_passada_doadores"] = doadores

    # ---------------- 18: reconciliacao pelo gold POR BLOCO
    anat = read(HERE / "wt_anatomia_unidade_v2_22-09.json")["resultado"]["v2_final"]["erros"]
    wzr = {(c["curso"], c["gold_id"]): c for c in read(HERE / "wz_bloco_cobertura_22-09.json")["rastreio_18"]}
    rec18 = []
    por_mat = {(m["curso"], m["gold_id"]): m for m in mat_uni}
    for e in anat:
        if e["classe"] != "herdada_do_bloco_certo_mas_gold_diverge":
            continue
        m = por_mat.get((e["curso"], e["gold_id"])) or {}
        z = wzr.get((e["curso"], e["gold_id"])) or {}
        gbu, bu = m.get("gold_do_bloco"), m.get("unidade_do_bloco")
        if gbu and bu:
            novo = "origem" if bu != gbu else "homogeneidade"
            base_ev = f"gold POR BLOCO ({gold_bloco_como[e['curso']].get(m.get('bloco'))}) true_unit={gbu}"
        else:
            novo = "indeterminado_sem_gold_de_bloco"
            base_ev = "sem gold por bloco (CG) ou bloco sem par no gold"
        rec18.append({"curso": e["curso"], "gold_id": e["gold_id"], "bloco": m.get("bloco"), "fonte_unidade_bloco": m.get("fonte_unidade_bloco"),
                      "unidade_do_bloco": bu, "gold_do_bloco": gbu, "gold_material": e["unidade_gold"],
                      "proveniencia_gold_material": m.get("proveniencia_gold"),
                      "veredito_wz": z.get("veredito"), "veredito_gold_de_bloco": novo, "evidencia": base_ev})
    R["reconciliacao_18"] = rec18
    return R


def raizes_de(estado):
    return {sig: v["root"] for sig, v in estado.items()}


# ============================================================================ anexo (tabelas geradas)
def escreve_anexo(r):
    L = ["# W-Z2 — anexo de tabelas geradas (diagnóstico causal, 23/09)", "",
         f"Declaração `{r['sha256_declaracao'][:16]}…`; base congelada `{r['sha256_base'][:16]}…`; DP `{r['sha256_dp'][:16]}…`; "
         f"índice documental `{r['sha256_indice_documental'][:16]}…`. Fidelidade: base = W-Z por ID; índice W-U reproduzido "
         f"{r['fidelidade_indice_wu']}. DP recomputado = gravado: {r['dp_fidelidade']}. Tempo {r['segundos']} s.", ""]
    L += ["## A1. Placar dos 3 modos (bloco, unidade, sub primária/aceita)", "",
          "| modo | curso | bloco | unidade | sub prim | sub aceita |", "|---|---|---|---|---|---|"]
    for modo, pc in r["placar"].items():
        for sig, c in pc.items():
            L.append(f"| {modo} | {sig} | {c.get('bloco', 0)}/{c.get('bloco_n', 0)} | {c.get('unidade', 0)}/{c.get('unidade_n', 0)} | "
                     f"{c.get('sub_primaria', 0)}/{c.get('sub_n', 0)} | {c.get('sub_aceita', 0)}/{c.get('sub_n', 0)} |")
    L += ["", "Mudanças por ID contra a base:", ""]
    for modo, d in r["mudancas_vs_base"].items():
        for eixo, gp in d.items():
            L.append(f"- {modo} · {eixo}: +{len(gp['ganhos'])} / −{len(gp['perdas'])}; perdas {gp['perdas']}")
    L += ["", "## A2. Erros de bloco (motor temporal)", "", "| curso | id | previsto → gold | método | banda | flag | provedor | gold na janela |",
          "|---|---|---|---|---|---|---|---|"]
    for e in r["bloco_erros"]:
        L.append(f"| {e['curso']} | `{e['gold_id']}` | {e['previsto']} → {e['gold'] or '∅'} | {e['metodo']} | {e['banda']} | {e['flag']} | "
                 f"{e['provedor']} | {e['gold_na_janela']} |")
    L += ["", "## A3. Blocos do DP posicional (classe × mecanismo × gold por bloco)", "",
          "| curso | bloco | classe | mecanismo | cabeçalho | posição | DP | gold do bloco | correto | rótulo |", "|---|---|---|---|---|---|---|---|---|---|"]
    for d in r["dp_blocos"]:
        L.append(f"| {d['curso']} | {d['bloco']} | {d['classe']} | {d['mecanismo']} | {d['cabecalho']} | {d['posicao']} | "
                 f"{d['dp_recomputado'][-22:]} | {(d['gold_bloco'] or '—')[-22:]} | {d['correto']} | {d['rotulo'][:60]} |")
    L += ["", "## A4. Erros de unidade (36) com mecanismo, fonte da unidade do bloco e proveniência do gold", "",
          "| curso | id | gold → previsto | classe | mecanismo | fonte da unidade do bloco | bloco (gold de bloco) | proveniência | bruto | seção |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for e in sorted(r["unidade_erros"], key=lambda e: (e["curso"], e["classe_anatomia"], e["gold_id"])):
        L.append(f"| {e['curso']} | `{e['gold_id']}` | {'|'.join(g[-18:] for g in e['gold'])} → {e['previsto'][-18:]} | {e['classe_anatomia']} | "
                 f"{e['mecanismo']} | {e['fonte_unidade_bloco']} | {e['bloco']} ({(e['gold_do_bloco'] or '—')[-18:]}) | {e['proveniencia_gold']} | "
                 f"{(e['bruto'] or '')[-18:]}{' gated' if e['bruto_gated'] else ''}{' =gold' if e['bruto_acertaria'] else ''} | "
                 f"{(e['secao'] or '')[-18:]}{' =gold' if e['secao_acertaria'] else ''} |")
    L += ["", "## A5. Reconciliação dos 18 pelo gold POR BLOCO", "",
          "| curso | id | bloco | unidade do bloco | gold do bloco | gold do material | proveniência | W-Z | gold de bloco |", "|---|---|---|---|---|---|---|---|---|"]
    for e in r["reconciliacao_18"]:
        L.append(f"| {e['curso']} | `{e['gold_id']}` | {e['bloco']} | {(e['unidade_do_bloco'] or '')[-22:]} | {(e['gold_do_bloco'] or '—')[-22:]} | "
                 f"{'|'.join(g[-18:] for g in e['gold_material'])} | {e['proveniencia_gold_material']} | {e['veredito_wz']} | {e['veredito_gold_de_bloco']} |")
    for modo in ("base", "oraculo_unidade"):
        itens = r["subunidade_familias"][modo]
        L += ["", f"## A6. Subunidade primária — famílias ({modo})", "",
              "| família | " + " | ".join(sorted({i['curso'] for i in itens})) + " | total |", "|---|" + "---|" * (len({i['curso'] for i in itens}) + 1)]
        cursos = sorted({i["curso"] for i in itens})
        fams = sorted({i["familia"] for i in itens})
        for fam in fams:
            L.append(f"| {fam} | " + " | ".join(str(sum(1 for i in itens if i['curso'] == s and i['familia'] == fam)) for s in cursos) +
                     f" | {sum(1 for i in itens if i['familia'] == fam)} |")
    L += ["", "## A7. Subunidade — materiais em erro na base (família, candidatos, alcance)", "",
          "| curso | id | gold | u^ / s^ (1a) | família | pont gold (unid/qualquer/radical) | rank / n cand | alcance fora do índice | oráculo acerta? |",
          "|---|---|---|---|---|---|---|---|---|"]
    oa = {(i["curso"], i["gold_id"]): i for i in r["subunidade_familias"]["oraculo_unidade"]}
    for i in sorted(r["subunidade_familias"]["base"], key=lambda i: (i["curso"], i["familia"], i["gold_id"])):
        if i["familia"] == "acerto":
            continue
        alc = ",".join(k for k, v in (i.get("alcance") or {}).items() if v) or "—"
        o = oa.get((i["curso"], i["gold_id"])) or {}
        L.append(f"| {i['curso']} | `{i['gold_id']}` | {i['gold'] or '∅'} | {(i.get('unidade_prevista') or '')[-16:]} / {i.get('sub_prevista') or '∅'} ({i.get('sub_1a') or '∅'}) | "
                 f"{i['familia']} | {i.get('pont_gold_na_unidade')}/{i.get('pont_gold_qualquer')}/{i.get('pont_gold_radical')} | {i.get('rank_gold')}/{i.get('n_candidatos')} | "
                 f"{alc} | {o.get('familia') == 'acerto'} |")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
