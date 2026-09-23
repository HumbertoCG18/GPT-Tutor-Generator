"""W-Y (#52): medicao do tipo de bloco decidido por LINHA (prototipo) vs classificador atual.

A. toda linha do cronograma dos 8 cursos vivos: tipo atual (linha/bloco vivo) x tipo novo (prototipo) e regra.
B. segmentacao: indice reconstruido em memoria (pipeline real `_build_file_map_timeline_context_from_course`,
   persist=False) com o codigo atual (controle) e com o prototipo; diff contra o indice vivo e entre si.
C. placar dos 3 eixos nos builds-base (cadeia do aceite #49: replay_bloco -> replay_unidade) com 3 bracos:
   indice gravado (baseline), indice reconstruido com codigo atual (controle) e com prototipo. Gold de bloco
   mapeado por linhas do cronograma (source_rows) quando o id muda.
D. obsoletos (lista estatica conferida por grep no src/tests atual).
Patches SO em memoria (restaurados no finally). Sem rede/LLM (tripwires). Nada gravado alem de wy_*.{json,md}.
Uso: python wy_kind_por_linha_22-09.py [--sem-c]
"""
import collections
import contextlib
import copy
import csv
import hashlib
import importlib.util
import json
import pathlib
import re
import socket
import sys
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
T0 = time.perf_counter()
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
GH = DATA.parent
sys.path.insert(0, str(DATA))
OUT_JSON = HERE / "wy_kind_por_linha_22-09.json"
OUT_MD = HERE / "wy_kind_por_linha_22-09.md"
PERMITIDOS = {OUT_JSON.resolve(), OUT_MD.resolve()}


# ---------------------------------------------------------------- tripwires (rede, LLM, escrita)
def _bloqueado(*a, **k):
    raise RuntimeError("bloqueado (tripwire W-Y)")


socket.socket.connect = _bloqueado
socket.create_connection = _bloqueado
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None
_gc.GeminiClient.__init__ = _bloqueado
from src.builder.runtime import datalab_client  # noqa: E402
datalab_client.convert_document_to_markdown = _bloqueado
_orig_wt, _orig_wb = pathlib.Path.write_text, pathlib.Path.write_bytes


def _guard_write(orig):
    def w(self, *a, **k):
        if Path(self).resolve() not in PERMITIDOS:
            raise RuntimeError(f"escrita bloqueada (tripwire W-Y): {self}")
        return orig(self, *a, **k)
    return w


pathlib.Path.write_text = _guard_write(_orig_wt)
pathlib.Path.write_bytes = _guard_write(_orig_wb)

from src.builder.core.core_utils import persist_enriched_timeline_index  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing.motor import context as MCTX  # noqa: E402
from src.builder.timeline import block_identity as BI  # noqa: E402
from src.builder.timeline import classifier as CL  # noqa: E402
from src.builder.timeline import index as IX  # noqa: E402
from src.builder.timeline.kinds import BlockKind  # noqa: E402
from src.utils.helpers import ATIVIDADE_KIND_MAP, norm_ascii_lower  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- prototipo: tipo por LINHA
def rot(text):
    """Rotulo cru normalizado SEM descartar palavra ("ao", "IP" ficam)."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", norm_ascii_lower(str(text or ""))).split())


FERIADO_NOMES = {"carnaval", "tiradentes", "corpus christi", "paixao de cristo", "sexta feira santa", "independencia",
                 "finados", "proclamacao da republica", "consciencia negra", "nossa senhora aparecida", "natal",
                 "pascoa", "dia do trabalho", "dia do trabalhador", "confraternizacao universal"}
REGRAS_ROTULO = [  # (kind, regex ancorada na CABECA); ordem = prioridade
    ("holiday", re.compile(r"^feriado\b")),
    ("suspended", re.compile(r"^(suspens\w*|greve|paralisacao|assembleia)\b")),
    ("reserved", re.compile(r"^reserva( tecnica)?$")),
    ("academic_event", re.compile(r"^(semana academica|semana cientifica|evento academico|aula magna|simposio|congresso"
                                  r"|jornada|ciclo de palestras|seminario integrador)\b")),
    ("results", re.compile(r"^(divulgacao|devolucao|devolutiva)\b")),
    ("makeup", re.compile(r"^(reposicao|prova de substituicao|substituicao)\b")),
    ("workshop", re.compile(r"^oficina\b")),
    ("deliverable", re.compile(r"^(entrega|apresentacao) (do |de |da )?(trabalho|t\d|tp\d|tf)\b")),
    ("review", re.compile(r"^(exercicios de )?revisao\b")),
    ("office_hours", re.compile(r"^(aula de duvidas|duvidas|atendimento|plantao|monitoria)\b")),
    # overview: cue academico SEM topico depois ("introducao" inteiro; "apresentacao da disciplina[ e introducao]"
    # inteiro); plano de ensino/ementa aceitam cauda (descricao administrativa do proprio plano).
    ("overview", re.compile(r"^(introducao|apresentacao (da|do) (disciplina|curso)( e introducao)?)$|^(plano de ensino|ementa)\b")),
    # assessment: cabeca de prova E sinal forte (STRONG_EXAM_RE) no rotulo; "correcao da p1" nao tem cabeca de prova.
    ("assessment", re.compile(r"^(prova|avaliacao|exame|p[1-4]|pf|g2|ps)\b")),
    ("planning", re.compile(r"^(planejamento|reuniao|conselho)\b")),
]
MARCADOR_TRADUZ = {"suspension": "suspended", "event": "academic_event"}
PULA_ADJ = {"holiday", "suspended", "academic_event", "reserved"}
PROVA = {"assessment", "makeup"}
PRIORIDADE = list(IX._SOURCE_KIND_PRIORITY) + ["overview"]


def kind_rotulo(label):
    for kind, rx in REGRAS_ROTULO:
        hit = rx.match(label)
        if hit and (kind != "assessment" or CL.STRONG_EXAM_RE.search(label)):
            return kind, f"4:{kind}"
    if label in FERIADO_NOMES:
        return "holiday", "4:holiday(nome)"
    return "class", "4:class"


def proto_linha(raw_content, atividade_raw, ajuste=False):
    """(kind, regra) por linha, antes do passo de adjacencia (office_hours -> review).
    ajuste=True (P1) aplica as correcoes propostas pelos dados: (a) Atividade "prova de substituicao" = makeup;
    (b) marcador suspension/event e metadado: rotulo nao-class decide ("Feriado {kind=suspension}" = holiday);
    (c) g2/ps com rotulo vazio = o marcador decide (como hoje)."""
    m = IX._KIND_TOKEN_RE.search(raw_content or "")
    marcador = m.group(1).strip().lower() if m else ""
    label = rot(IX._KIND_TOKEN_RE.sub("", raw_content or ""))
    atividade = norm_ascii_lower(atividade_raw or "")
    if ajuste and "substituicao" in atividade:                            # P1(a)
        return "makeup", "2:atividade=substituicao(P1a)", marcador, label
    for needle, mapped in ATIVIDADE_KIND_MAP.items():                     # regra 2
        if needle in atividade:
            return MARCADOR_TRADUZ.get(mapped, mapped), f"2:atividade={needle}", marcador, label
    if marcador:                                                          # regra 3
        if marcador in {"g2", "ps"}:
            if CL.STRONG_EXAM_RE.search(label) or label.startswith("prova"):
                return {"g2": "assessment", "ps": "makeup"}[marcador], f"3:{marcador}+rotulo_prova", marcador, label
            if ajuste and not label:                                      # P1(c)
                return {"g2": "assessment", "ps": "makeup"}[marcador], f"3:{marcador}+rotulo_vazio(P1c)", marcador, label
            k, r = kind_rotulo(label)
            return k, f"3:{marcador}_metadado>{r}", marcador, label
        if marcador in MARCADOR_TRADUZ:
            if ajuste:                                                    # P1(b)
                k, r = kind_rotulo(label)
                if k != "class":
                    return k, f"3:{marcador}_metadado>{r}(P1b)", marcador, label
            return MARCADOR_TRADUZ[marcador], f"3:{marcador}", marcador, label
        if marcador in IX._VALID_KIND_VALUES:
            return marcador, f"3:{marcador}", marcador, label
    k, r = kind_rotulo(label)                                             # regra 4
    return k, r, marcador, label


def rotulo_keys(timeline):
    """Colunas de CONTEUDO sem a coluna Atividade (que o indice junta ao content)."""
    keys, _ = IX._infer_timeline_keys(timeline)
    return [k for k in keys if "atividade" not in k] or keys


def proto_linhas(timeline, ajuste=False):
    """Tipo novo de cada linha (lista paralela a timeline) + adjacencia de duvidas/plantao.
    ajuste=True (P1d): a busca da proxima linha decisiva tambem pula outra linha de duvidas/plantao (cadeia)."""
    content_keys = rotulo_keys(timeline)
    out = []
    for row in timeline:
        raw = " ".join(row.get(k, "") for k in content_keys).strip()
        k, r, marcador, label = proto_linha(raw, IX._row_atividade(row), ajuste)
        out.append({"kind": k, "regra": r, "marcador": marcador, "label": label, "vazia": not IX._collapse_ws(
            IX._KIND_TOKEN_RE.sub("", raw))})
    for i, o in enumerate(out):
        if o["kind"] != "office_hours":
            continue
        prox = ""
        for p in out[i + 1:]:
            if p["vazia"] or p["kind"] in PULA_ADJ or (ajuste and p["regra"].startswith("4:office_hours")):
                continue
            prox = p["kind"]
            break
        if prox in PROVA:
            o["kind"], o["regra"] = "review", f"{o['regra']}>review(proxima={prox})"
        else:
            o["regra"] = f"{o['regra']}(proxima={prox or 'fim'})"
    return out


def agrega(kinds):
    present = set(kinds)
    for k in PRIORIDADE:
        if k in present:
            return k
    return "class"


@contextlib.contextmanager
def prototipo(ajuste=False):
    """Patch em memoria: linhas com tipo do prototipo; bloco = agregacao (override manual vence)."""
    orig_rows, orig_agg, orig_cls = IX._build_timeline_candidate_rows, IX._aggregate_source_kind, IX.classify_block

    def rows(timeline):
        cand = orig_rows(timeline)
        novos = proto_linhas(timeline, ajuste)
        for c in cand:
            c["kind"] = novos[c["index"]]["kind"]  # ignored (metadado g2/ps/suspension/event) fica como hoje
        return cand

    def agg(rs):
        k = agrega(str(r.get("kind") or "") for r in rs or [])
        return "" if k == "class" else k

    def cls(block):
        ov = block.get("manual_kind_override")
        if isinstance(ov, str):
            try:
                return BlockKind(ov)
            except ValueError:
                pass
        if "rows" not in block:
            FALLBACK_SEM_ROWS.append(str(block.get("id")))
            return orig_cls(block)
        return BlockKind(agrega(str(r.get("kind") or "") for r in block["rows"]))

    IX._build_timeline_candidate_rows, IX._aggregate_source_kind, IX.classify_block = rows, agg, cls
    try:
        yield
    finally:
        IX._build_timeline_candidate_rows, IX._aggregate_source_kind, IX.classify_block = orig_rows, orig_agg, orig_cls


FALLBACK_SEM_ROWS: list = []


@contextlib.contextmanager
def uuid_deterministico(tag):
    orig = BI.uuid4
    n = [0]

    def mint():
        n[0] += 1
        return uuid.UUID(hashlib.sha256(f"{tag}:{n[0]}".encode()).hexdigest()[:32])

    BI.uuid4 = mint
    try:
        yield
    finally:
        BI.uuid4 = orig


# ---------------------------------------------------------------- reconstrucao do indice (pipeline real)
RU = load("wy_ru", HERE / "replay_unidade_21-09.py")


def rebuild(repo, profile, proto, tag):
    course_meta = (read(repo / "manifest.json").get("course") or {}) if (repo / "manifest.json").exists() else {}
    meta = {**course_meta, "_repo_root": repo}
    tax = load_internal_content_taxonomy(repo)
    ctxm = prototipo(proto == "P1") if proto else contextlib.nullcontext()
    with ctxm, uuid_deterministico(tag):
        ctx = IX._build_file_map_timeline_context_from_course(
            meta, profile, content_taxonomy=tax, persist=False,
            build_file_map_unit_index_from_course=RU.course_index,
            build_file_map_content_taxonomy_from_course=lambda *a, **k: tax)
    idx = persist_enriched_timeline_index(ctx["timeline_index"])
    return json.loads(json.dumps(idx, ensure_ascii=False, default=str)), ctx["timeline"]


def rows_of(b):
    return tuple(int(x) for x in b.get("source_rows") or [])


def seg_diff(antes, depois):
    """Grupos de blocos (antes x depois) ligados por linha compartilhada que nao sao 1:1 identicos."""
    a = {rows_of(b): b for b in antes}
    d = {rows_of(b): b for b in depois}
    iguais = set(a) & set(d)
    ra = {r: b for b in antes if rows_of(b) not in iguais for r in rows_of(b)}
    rd = {r: b for b in depois if rows_of(b) not in iguais for r in rows_of(b)}
    grupos, vistos = [], set()
    for b in antes:
        if rows_of(b) in iguais or b["id"] in vistos:
            continue
        ga, gd, fila = {b["id"]: b}, {}, list(rows_of(b))
        while fila:
            r = fila.pop()
            for src, dst in ((ra, ga), (rd, gd)):
                x = src.get(r)
                if x and x["id"] not in dst:
                    dst[x["id"]] = x
                    fila.extend(rows_of(x))
        vistos |= set(ga)
        tipo = "fusao" if len(ga) > 1 and len(gd) == 1 else "separacao" if len(ga) == 1 and len(gd) > 1 else \
            "redistribuicao" if gd else "sumiu"
        fmt = lambda bs: [{"id": x["id"], "kind": x.get("kind"), "de": x.get("period_start"), "ate": x.get("period_end"),
                           "linhas": list(rows_of(x))} for x in bs.values()]
        grupos.append({"tipo": tipo, "antes": fmt(ga), "depois": fmt(gd)})
    novos = [b for b in depois if rows_of(b) not in iguais and not any(r in ra for r in rows_of(b))]
    for b in novos:
        grupos.append({"tipo": "novo", "antes": [], "depois": [{"id": b["id"], "kind": b.get("kind"),
                       "de": b.get("period_start"), "ate": b.get("period_end"), "linhas": list(rows_of(b))}]})
    return {"blocos_antes": len(antes), "blocos_depois": len(depois), "identicos": len(iguais), "grupos": grupos}


# ---------------------------------------------------------------- A + B: 8 cursos vivos
SIG = {"Metodos-Formais-Tutor": "MF", "Inteligencia-Artifical-Tutor": "IA", "TCC-Tutor": "TCC",
       "Sistemas-Operacionais-Tutor": "SO", "Engenharia-Software-2-Tutor": "ES2", "Laboratorio-de-Redes-Tutor": "LR",
       "Computacao-Grafica-Tutor": "CG", "Fundamentos-de-Redes-Tutor": "FR"}


def perfis_vivos():
    d = read(Path.home() / "AppData/Roaming/GPTTutorGenerator/subjects.json")
    out = {}
    for s in d.values():
        repo = Path(s["repo_root"])
        out[SIG[repo.name]] = (repo, SimpleNamespace(**s))
    return dict(sorted(out.items()))


def alvo_de(sig, label, marcador, bloco_vivo_kind, override):
    if sig == "FR" and label.startswith("introducao ao roteamento"):
        return "alvo:FR-introducao-ao-roteamento"
    if sig == "IA" and label.startswith("ml introducao a ml"):
        return "alvo:IA-ml-introducao"
    if sig == "TCC" and marcador == "g2" and label.startswith("atendimento"):
        return "alvo:TCC-atendimento-g2"
    if sig == "TCC" and label.startswith("oficina"):
        return "alvo:TCC-oficina"
    if bloco_vivo_kind == "office_hours":
        return "alvo:duvidas-office_hours"
    if bloco_vivo_kind in {"holiday", "suspended"}:
        return "legitimo:feriado/suspensao"
    if bloco_vivo_kind == "review":
        return "legitimo:revisao"
    if bloco_vivo_kind == "overview":
        return "legitimo:overview"
    return ""


def parte_ab():
    linhas, blocos_mudam, por_curso, seg = [], [], {}, {}
    tot = {k: collections.Counter() for k in ("linha_atual", "linha_P0", "linha_P1", "bloco_vivo", "bloco_controle",
                                              "bloco_P0", "bloco_P1")}
    for sig, (repo, prof) in perfis_vivos().items():
        vivo = read(repo / "course/.timeline_index.json")["blocks"]
        ctrl, timeline = rebuild(repo, prof, False, f"{sig}:ctrl")
        p0, _ = rebuild(repo, prof, "P0", f"{sig}:p0")
        p1, _ = rebuild(repo, prof, "P1", f"{sig}:p1")
        cand = IX._build_timeline_candidate_rows(timeline)
        novos, novos1 = proto_linhas(timeline), proto_linhas(timeline, True)
        by_row = lambda bs: {r: b for b in bs for r in rows_of(b)}
        bv, bc, b0, b1 = by_row(vivo), by_row(ctrl["blocks"]), by_row(p0["blocks"]), by_row(p1["blocks"])
        rk = rotulo_keys(timeline)
        c = {k: collections.Counter() for k in tot}
        for cr, n0, n1 in zip(cand, novos, novos1):
            i = cr["index"]
            v, k0, q0, q1 = bv.get(i), bc.get(i), b0.get(i), b1.get(i)
            rec = {"curso": sig, "linha": i, "data": cr["date_text"], "rotulo": " ".join(cr["row"].get(k, "") for k in rk).strip(),
                   "atividade": IX._row_atividade(cr["row"]), "marcador": n0["marcador"],
                   "tipo_linha_atual": cr["kind"], "bloco_vivo": v and v["id"], "tipo_bloco_vivo": v and v.get("kind"),
                   "override_vivo": v and v.get("manual_kind_override"),
                   "bloco_controle": k0 and k0["id"], "tipo_bloco_controle": k0 and k0.get("kind"),
                   "tipo_linha_P0": n0["kind"], "regra_P0": n0["regra"], "bloco_P0": q0 and q0["id"], "tipo_bloco_P0": q0 and q0.get("kind"),
                   "tipo_linha_P1": n1["kind"], "regra_P1": n1["regra"], "bloco_P1": q1 and q1["id"], "tipo_bloco_P1": q1 and q1.get("kind")}
            rec["caso"] = alvo_de(sig, n0["label"], n0["marcador"], rec["tipo_bloco_vivo"], rec["override_vivo"])
            rec["muda_linha_P0"] = rec["tipo_linha_atual"] != rec["tipo_linha_P0"]
            rec["muda_bloco_P0"] = (rec["tipo_bloco_controle"] or "") != (rec["tipo_bloco_P0"] or "")
            rec["muda_bloco_P1"] = (rec["tipo_bloco_controle"] or "") != (rec["tipo_bloco_P1"] or "")
            linhas.append(rec)
            c["linha_atual"][cr["kind"]] += 1
            c["linha_P0"][n0["kind"]] += 1
            c["linha_P1"][n1["kind"]] += 1
        for key, bs in (("bloco_vivo", vivo), ("bloco_controle", ctrl["blocks"]), ("bloco_P0", p0["blocks"]), ("bloco_P1", p1["blocks"])):
            c[key].update(str(b.get("kind")) for b in bs)
        for variante, idx in (("P0", p0), ("P1", p1)):
            by_rows = {rows_of(b): b for b in idx["blocks"]}
            for b in ctrl["blocks"]:
                p = by_rows.get(rows_of(b))
                if p is None or p.get("kind") != b.get("kind") or p.get("unit_slug") != b.get("unit_slug"):
                    blocos_mudam.append({"variante": variante, "curso": sig, "controle": b["id"], "de": b.get("period_start"),
                                         "ate": b.get("period_end"), "kind_controle": b.get("kind"), "unit_controle": b.get("unit_slug"),
                                         "novo": p and p["id"], "kind_novo": p and p.get("kind"), "unit_novo": p and p.get("unit_slug"),
                                         "segmentacao_mudou": p is None,
                                         "sessoes": [s.get("label") for s in b.get("sessions") or []][:4]})
        por_curso[sig] = {k: dict(sorted(v.items())) for k, v in c.items()}
        for k in tot:
            tot[k].update(c[k])
        vb = vivo
        seg[sig] = {"vivo_x_controle": seg_diff(vb, ctrl["blocks"]), "controle_x_P0": seg_diff(ctrl["blocks"], p0["blocks"]),
                    "controle_x_P1": seg_diff(ctrl["blocks"], p1["blocks"]),
                    "vivo_x_controle_kind_diverge": sorted({b["id"] for b in vb} - {b["id"] for b in vb
                        if any(rows_of(b) == rows_of(x) and b.get("kind") == x.get("kind") for x in ctrl["blocks"])})}
        print(sig, por_curso[sig]["bloco_controle"], "-> P0", por_curso[sig]["bloco_P0"], "-> P1", por_curso[sig]["bloco_P1"], flush=True)
    return linhas, blocos_mudam, {k: dict(sorted(v.items())) for k, v in tot.items()}, por_curso, seg


# ---------------------------------------------------------------- C: placar 3 eixos nos builds-base
def parte_c():
    rb = load("wy_rb", HERE / "replay_bloco_21-09.py")
    compare = load("wy_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    orig_ru_read, orig_load = RU.read, MCTX.load_repo_artifact
    tot = {a: collections.Counter() for a in ("base", "controle", "P0", "P1")}
    cursos, perdas, mapeamento, seg = {}, [], {}, {}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        prof = SimpleNamespace(**read(root / "_inputs_15-09.json")["profile_input"])
        base_idx = read(root / "course/.timeline_index.json")
        ctrl_idx, _ = rebuild(root, prof, False, f"C:{sig}:ctrl")
        p0_idx, _ = rebuild(root, prof, "P0", f"C:{sig}:p0")
        p1_idx, _ = rebuild(root, prof, "P1", f"C:{sig}:p1")
        seg[sig] = {"base_x_controle": seg_diff(base_idx["blocks"], ctrl_idx["blocks"]),
                    "controle_x_P0": seg_diff(ctrl_idx["blocks"], p0_idx["blocks"]),
                    "controle_x_P1": seg_diff(ctrl_idx["blocks"], p1_idx["blocks"])}
        arms = {"base": base_idx, "controle": ctrl_idx, "P0": p0_idx, "P1": p1_idx}
        preds = {}
        for arm, idx in arms.items():
            def art(repo, rel, _idx=idx):
                if rel == "course/.timeline_index.json":
                    return copy.deepcopy(_idx)
                return orig_load(repo, rel)
            MCTX.load_repo_artifact = art
            try:
                saved, bloco, _, _ = rb.replay(root)
            finally:
                MCTX.load_repo_artifact = orig_load
            feed = [copy.deepcopy(bloco[i]) for i in bloco]

            def patched(path, _feed=feed, _idx=idx):
                p = Path(path)
                if p.name == "manifest.json":
                    return {**orig_ru_read(path), "entries": _feed}
                if p.name == ".timeline_index.json":
                    return copy.deepcopy(_idx)
                return orig_ru_read(path)
            RU.read = patched
            try:
                _, novo, _ = RU.replay(root)
            finally:
                RU.read = orig_ru_read
            preds[arm] = (saved, novo)
        base_by_id = {b["id"]: b for b in base_idx["blocks"]}
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / name / "manifest.json")["entries"]}
        saved = preds["base"][0]
        index = compare.indexed(list(saved.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gb, gu, gs, gsp = mede.golds(sig)
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        c = {a: collections.Counter() for a in arms}
        gold_map = {}
        for row in rows:
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            eid = str(hits[0]["id"]) if hits else None
            ok_arm = {}
            for arm, idx in arms.items():
                lookup = {str(b.get("block_uuid")): b for b in idx["blocks"] if b.get("block_uuid")}
                lookup.update({str(b["id"]): b for b in idx["blocks"]})
                e = preds[arm][1][eid] if eid else None
                bid = str((e or {}).get("manual_timeline_block_id") or (e or {}).get("temporal_block_id") or "")
                pb = lookup.get(bid)
                ok = {}
                if row["bloco"] != "":
                    g = base_by_id.get(gb[gid])
                    grows = set(rows_of(g)) if g else set()
                    strict = [b["id"] for b in idx["blocks"] if g and rows_of(b) == rows_of(g)]
                    lenient = {b["id"] for b in idx["blocks"] if grows & set(rows_of(b))}
                    if arm != "base" and g and not strict:
                        gold_map.setdefault(gb[gid], {"gold_base": gb[gid], "linhas": sorted(grows),
                                                      "de": g.get("period_start"), "ate": g.get("period_end")})[arm] = sorted(lenient)
                    c[arm]["bloco_n"] += 1
                    ok["bloco"] = bool(pb and strict and pb["id"] == strict[0])
                    ok["bloco_leniente"] = bool(pb and pb["id"] in lenient)
                    c[arm]["bloco"] += ok["bloco"]
                    c[arm]["bloco_leniente"] += ok["bloco_leniente"]
                pr = (str((e or {}).get("computed_unit_slug") or ""), str((e or {}).get("computed_subunit_slug") or ""))
                if row["unidade"] != "":
                    c[arm]["unidade_n"] += 1
                    ok["unidade"] = bool(e and pr[0] in gu[gid]); c[arm]["unidade"] += ok["unidade"]
                if row["sub_primario"] != "":
                    c[arm]["sub_n"] += 1
                    ok["sub_primaria"] = bool(e and pr[1] in gsp[gid]); c[arm]["sub_primaria"] += ok["sub_primaria"]
                    ok["sub_aceita"] = bool(e and pr[1] in gs[gid]); c[arm]["sub_aceita"] += ok["sub_aceita"]
                ok_arm[arm] = ok
            for de, para in (("base", "controle"), ("controle", "P0"), ("controle", "P1")):
                for eixo, v in ok_arm[de].items():
                    if v != ok_arm[para].get(eixo):
                        perdas.append({"curso": sig, "id": eid, "gold_id": gid, "eixo": eixo, "de": de, "para": para,
                                       "tipo": "perda" if v else "ganho"})
        mapeamento[sig] = list(gold_map.values())
        cursos[sig] = {a: dict(sorted(v.items())) for a, v in c.items()}
        for a in tot:
            tot[a].update(c[a])
        print("C", sig, {a: (v["bloco"], v["unidade"], v["sub_primaria"], v["sub_aceita"]) for a, v in c.items()}, flush=True)
    return {"totais": {a: dict(sorted(v.items())) for a, v in tot.items()}, "cursos": cursos,
            "diferencas_por_id": sorted(perdas, key=lambda p: (p["de"], p["para"], p["curso"], p["eixo"], str(p["id"]))),
            "gold_remapeado": mapeamento, "segmentacao_builds_base": seg}


# ---------------------------------------------------------------- D: obsoletos (conferidos por grep em main())
OBSOLETOS = [
    ("src/builder/timeline/classifier.py", "CLASS_INTRO_TERMS", "regra 1 OVERVIEW por substring no conteudo agregado"),
    ("src/builder/timeline/classifier.py", "KIND_KEYWORDS", "regra 3 keywords sobre conteudo agregado + period_label"),
    ("src/builder/timeline/classifier.py", "def _content_text", "insumo das heuristicas de conteudo"),
    ("src/builder/timeline/classifier.py", "def _session_text", "insumo de _session_exam_or_review"),
    ("src/builder/timeline/classifier.py", "def _session_exam_or_review", "regras 2/3b (sessao revela prova/revisao)"),
    ("src/builder/timeline/classifier.py", "def _office_hours_session_majority", "guard maioria de sessoes (SO bloco-18)"),
    ("src/builder/timeline/classifier.py", "def _text_of", "conteudo+period_label para keywords"),
    ("src/builder/timeline/classifier.py", "def _has_unit_evidence", "guard planning/trabalho por evidencia de unidade"),
    ("src/builder/timeline/classifier.py", "def _cue_e_conteudo_do_plano", "guard cue x conteudo do plano (F2/F3)"),
    ("src/builder/timeline/classifier.py", "WEAK_EXAM_TOKENS", "guard 'prova'/'teste' nus (motor window_provider tambem importa)"),
    ("src/builder/timeline/classifier.py", "def row_kind_from_text", "linha classificada via classify_block sintetico"),
    ("src/builder/timeline/classifier.py", "ROW_TEXT_KINDS", "subconjunto de kinds por texto de linha"),
    ("src/builder/timeline/index.py", "def plan_phrases_para_classificacao", "so alimenta _cue_e_conteudo_do_plano"),
    ("src/builder/timeline/index.py", "_IGNORED_KIND_AS_SOURCE", "g2/ps viram assessment/makeup sem olhar o rotulo"),
    ("src/builder/timeline/index.py", "def _promote_preexam_reviews", "heuristica de label de sessao 'revisao' (pos-classificacao)"),
]


def parte_d():
    out = []
    for arq, needle, porque in OBSOLETOS:
        linhas = (DATA / arq).read_text(encoding="utf-8").splitlines()
        n = next((i + 1 for i, l in enumerate(linhas) if needle in l and not l.lstrip().startswith("#")), None)
        out.append({"arquivo": arq, "linha": n, "simbolo": needle, "motivo": porque})
    usos = {}
    for t in sorted((DATA / "tests").glob("test_*.py")):
        txt = t.read_text(encoding="utf-8", errors="replace")
        hits = [s for s in ("row_kind_from_text", "classify_block", "_cue_e_conteudo_do_plano", "WEAK_EXAM_TOKENS",
                            "_office_hours_session_majority", "CLASS_INTRO_TERMS", "_aggregate_source_kind",
                            "_promote_preexam_reviews", "KIND_KEYWORDS") if s in txt]
        if hits:
            usos[t.name] = hits
    return {"simbolos": out, "testes_que_referenciam": usos}


# ---------------------------------------------------------------- relatorio
AJUSTES_P1 = ["P1a: Atividade 'prova de substituicao' = makeup (senao 'prova' do ATIVIDADE_KIND_MAP vira assessment)",
              "P1b: marcador suspension/event e metadado de periodo; rotulo nao-class decide ('Feriado {kind=suspension}' = holiday)",
              "P1c: g2/ps com rotulo vazio = o marcador decide (assessment/makeup, como hoje)",
              "P1d: adjacencia de duvidas/plantao pula outra linha de duvidas/plantao (cadeia antes da prova)"]


def fmtb(xs):
    return ", ".join(f"{x['id']}({x['kind']},{x['de']}..{x['ate']},L{x['linhas']})" for x in xs)


def md(rep):
    A = rep["A"]
    kinds = sorted(set().union(*[set(v) for v in A["totais"].values()]))
    L = ["# W-Y (#52) — tipo de bloco decidido por linha (prototipo)", "",
         f"HEAD {rep['head']}; decisoes sha256 `{rep['sha256_decisoes']}`; resultado sha256 `{rep['sha256_resultado']}`.",
         "Script `wy_kind_por_linha_22-09.py` (patch so em memoria). P0 = regras do brief; P1 = P0 + ajustes:", ""]
    L += [f"- {a}" for a in AJUSTES_P1]
    L += ["", "## A. Totais (8 cursos vivos)", "", "| contagem | " + " | ".join(kinds) + " |", "|---|" + "---|" * len(kinds)]
    for k, v in A["totais"].items():
        L.append(f"| {k} | " + " | ".join(str(v.get(x, 0)) for x in kinds) + " |")
    L += ["", "Por curso (blocos controle -> P0 -> P1):", ""]
    for sig, v in A["por_curso"].items():
        L.append(f"- {sig}: {v['bloco_controle']} -> {v['bloco_P0']} -> {v['bloco_P1']}")
    L += ["", "### Casos-alvo e legitimos (tipo do bloco vivo -> P0 | P1, por linha)", ""]
    for k, v in A["casos"].items():
        L.append(f"- {k}: {v}")
    L += ["", "### Linhas cujo tipo muda (linha P0, bloco P0 ou bloco P1) + alvos", "",
          "| curso | L | data | rotulo | Atividade | marc | linha atual | bloco vivo | bloco controle | linha P0 | regra P0 | bloco P0 | linha P1 | regra P1 | bloco P1 | caso |",
          "|" + "---|" * 16]
    for r in A["linhas"]:
        if r["muda_linha_P0"] or r["muda_bloco_P0"] or r["muda_bloco_P1"] or r["caso"].startswith("alvo"):
            ov = " (override)" if r["override_vivo"] else ""
            L.append(f"| {r['curso']} | {r['linha']} | {r['data']} | {r['rotulo'][:60]} | {r['atividade']} | {r['marcador']} | "
                     f"{r['tipo_linha_atual']} | {r['bloco_vivo']}={r['tipo_bloco_vivo']}{ov} | "
                     f"{r['bloco_controle']}={r['tipo_bloco_controle']} | {r['tipo_linha_P0']} | {r['regra_P0']} | "
                     f"{r['bloco_P0']}={r['tipo_bloco_P0']} | {r['tipo_linha_P1']} | {r['regra_P1']} | {r['bloco_P1']}={r['tipo_bloco_P1']} | {r['caso']} |")
    L += ["", "Tabela completa (todas as linhas) em `A.linhas` do JSON.", "",
          "## B. Segmentacao (indice reconstruido em memoria; controle x P0/P1, mesmo insumo)", ""]
    for sig, s in rep["B"].items():
        L.append(f"- {sig}: vivo x controle = {len(s['vivo_x_controle']['grupos'])} grupos de segmentacao, "
                 f"{len(s['vivo_x_controle_kind_diverge'])} blocos com kind divergente")
        for var in ("controle_x_P0", "controle_x_P1"):
            g = s[var]
            L.append(f"  - {var}: {g['blocos_antes']} -> {g['blocos_depois']} blocos, {g['identicos']} identicos")
            for gr in g["grupos"]:
                L.append(f"    - {gr['tipo']}: {fmtb(gr['antes'])} -> {fmtb(gr['depois'])}")
    if rep.get("C"):
        C = rep["C"]
        L += ["", "## C. Placar 3 eixos (builds-base)", "",
              "| braco | bloco (estrito) | bloco leniente | unidade | sub prim | sub aceita |", "|---|---|---|---|---|---|"]
        for a, v in C["totais"].items():
            L.append(f"| {a} | {v.get('bloco')}/{v.get('bloco_n')} | {v.get('bloco_leniente')} | {v.get('unidade')}/{v.get('unidade_n')} | "
                     f"{v.get('sub_primaria')}/{v.get('sub_n')} | {v.get('sub_aceita')}/{v.get('sub_n')} |")
        L += ["", "Por curso (bloco, unidade, sub prim, sub aceita):", ""]
        for sig, v in C["cursos"].items():
            L.append(f"- {sig}: " + "; ".join(f"{a} {x.get('bloco')}/{x.get('unidade')}/{x.get('sub_primaria')}/{x.get('sub_aceita')}"
                                              for a, x in v.items()))
        L += ["", "Diferencas por ID (de -> para):", ""]
        for p in C["diferencas_por_id"]:
            L.append(f"- {p['de']}->{p['para']} {p['tipo']} {p['curso']} {p['eixo']} {p['id']} (gold {p['gold_id']})")
        L += ["", "Gold de bloco remapeado (bloco base sem bloco de linhas identicas no braco):", ""]
        for sig, lst in C["gold_remapeado"].items():
            for g in lst:
                L.append(f"- {sig} {g['gold_base']} ({g['de']}..{g['ate']}, linhas {g['linhas']}): "
                         + "; ".join(f"{a} -> {g[a]}" for a in ("controle", "P0", "P1") if a in g))
        L += ["", "Segmentacao nos builds-base:", ""]
        for sig, s in C["segmentacao_builds_base"].items():
            for var, g in s.items():
                L.append(f"- {sig} {var}: {g['blocos_antes']} -> {g['blocos_depois']}, {g['identicos']} identicos, {len(g['grupos'])} grupos")
                for gr in g["grupos"]:
                    L.append(f"  - {gr['tipo']}: {fmtb(gr['antes'])} -> {fmtb(gr['depois'])}")
    L += ["", "## D. Obsoletos com o prototipo", ""]
    for s in rep["D"]["simbolos"]:
        L.append(f"- {s['arquivo']}:{s['linha']} `{s['simbolo']}` — {s['motivo']}")
    L += ["", "Testes que referenciam esses simbolos: " + json.dumps(rep["D"]["testes_que_referenciam"], ensure_ascii=False), ""]
    return "\n".join(L) + "\n"


def snapshot(paths):
    """sha256 de manifest + course/ dos repos usados (prova de que nada foi escrito)."""
    h = hashlib.sha256()
    for root in paths:
        for f in sorted([root / "manifest.json"] + [x for x in (root / "course").rglob("*") if x.is_file()]):
            if f.exists():
                h.update(str(f).encode())
                h.update(f.read_bytes())
    return h.hexdigest()


def main():
    import subprocess
    head = subprocess.run(["git", "-C", str(DATA), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    nomes = load("wy_mede_nomes", HERE / "mede_3eixos_12-09.py").NOMES
    roots = [r for r, _ in perfis_vivos().values()] + [
        DATA / (".frzero/pacote_categoria_17-09" if s in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / n
        for s, n in nomes.items()]
    antes = snapshot(roots)
    decisoes = {"regras_rotulo": [(k, rx.pattern) for k, rx in REGRAS_ROTULO], "feriado_nomes": sorted(FERIADO_NOMES),
                "marcador_traduz": MARCADOR_TRADUZ, "pula_adj": sorted(PULA_ADJ), "prova": sorted(PROVA),
                "prioridade": PRIORIDADE, "atividade_map": ATIVIDADE_KIND_MAP, "ajustes_P1": AJUSTES_P1,
                "assessment_exige": CL.STRONG_EXAM_RE.pattern}
    linhas, blocos_mudam, tot, por_curso, seg = parte_ab()
    casos = collections.defaultdict(collections.Counter)
    for r in linhas:
        if r["caso"]:
            casos[r["caso"]][f"{r['tipo_bloco_vivo']}->{r['tipo_bloco_P0']}|{r['tipo_bloco_P1']}"] += 1
    rep = {"head": head, "sha256_decisoes": sha(decisoes), "decisoes": decisoes,
           "A": {"totais": tot, "por_curso": por_curso, "linhas": linhas,
                 "blocos_que_mudam_controle_x_prototipo": blocos_mudam,
                 "casos": {k: dict(sorted(v.items())) for k, v in sorted(casos.items())}},
           "B": seg, "C": None if "--sem-c" in sys.argv else parte_c(), "D": parte_d(),
           "fallback_classify_sem_rows": sorted(set(FALLBACK_SEM_ROWS))}
    rep["sha256_resultado"] = sha(rep)
    depois = snapshot(roots)
    rep["repos_intocados"] = {"sha256_antes": antes, "sha256_depois": depois, "iguais": antes == depois}
    OUT_JSON.write_text(json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(md(rep), encoding="utf-8")
    print("SHA256 json", hashlib.sha256(OUT_JSON.read_bytes()).hexdigest())
    print("SHA256 decisoes", rep["sha256_decisoes"], "repos intocados", antes == depois)
    print(f"TEMPO {time.perf_counter() - T0:.1f}s")
    assert antes == depois, "repo/build-base alterado"


if __name__ == "__main__":
    main()


