"""Regua de TRAVESSIA do tutor (02/09): pergunta do aluno -> arquivo/bloco esperado.

Mede o que o tutor consegue achar lendo SO os indices de navegacao do repo (a "ordem de consulta
economica" do FILE_MAP): COURSE_MAP -> SYLLABUS -> CRONOGRAMA_DETALHADO -> FILE_MAP. Nao abre materiais.
LLM entra SO para medir (baseline), cacheado por (curso, pergunta, hash do contexto) — rerodar nao chama.
Piso deterministico (`--sem-llm`): sobreposicao de tokens da pergunta com titulo/label/subtopico/secoes.

    python scripts/eval_travessia.py IA --template   # cria docs/reports/travessia_gt_IA.csv (modelo; nao sobrescreve)
    python scripts/eval_travessia.py IA --sem-llm    # piso deterministico, 0 chamadas
    python scripts/eval_travessia.py IA              # baseline com LLM (Gemini, mesmo client do builder), cacheado
    python scripts/eval_travessia.py IA --cap 40     # teto de chamadas novas na rodada

Gold (`docs/reports/travessia_gt_<SIG>.csv`, utf-8, ';' como separador):
    pergunta ; esperado ; bloco ; tipo ; nota
    esperado = ids OU trechos de titulo/raw, separados por '|' (qualquer um vale como acerto)
    bloco    = bloco-NN (opcional; so conta onde preenchido)
    tipo     = conteudo | exercicio | prova | codigo | referencia | cronograma
Resultado: docs/reports/travessia_result_<SIG>_<modo>.json (por pergunta) + resumo no console.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.builder.text.normalize import normalize_match_text  # noqa: E402

GITHUB_DIR = Path(os.environ.get("TUTOR_REPOS_DIR") or ROOT.parent)
COURSES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
           "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
           "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
INDICES = ("COURSE_MAP.md", "SYLLABUS.md", "CRONOGRAMA_DETALHADO.md", "FILE_MAP.md")
MAX_CONTEXT = 160_000
REPORTS = ROOT / "docs" / "reports"


class Resposta(BaseModel):
    arquivos: List[str] = Field(default_factory=list, description="1 a 3 materiais, pelo Titulo EXATO do FILE_MAP ou pelo caminho raw, do mais provavel ao menos")
    bloco: str = Field(default="", description="bloco-NN do CRONOGRAMA_DETALHADO em que o assunto foi dado, ou vazio")
    porque: str = Field(default="", description="uma frase: qual linha do indice decidiu")


SYSTEM = (
    "Voce e o tutor de uma disciplina e recebeu SO os indices de navegacao do repositorio (COURSE_MAP, SYLLABUS, "
    "CRONOGRAMA_DETALHADO, FILE_MAP). Um aluno faz uma pergunta. Sem abrir nenhum material, escolha os 1 a 3 "
    "materiais que voce abriria PRIMEIRO para responder, na ordem, usando o Titulo EXATO como aparece na coluna "
    "Titulo do FILE_MAP (ou o caminho raw da linha de rastreabilidade). Se a pergunta e sobre quando/qual semana, "
    "informe tambem o bloco (bloco-NN) do CRONOGRAMA_DETALHADO. Nao invente titulos. Responda so o JSON do schema."
)


def _norm(t: str) -> str:
    return " ".join(normalize_match_text(str(t or "")).split())


def _toks(t: str) -> set:
    return {x for x in _norm(t).split() if len(x) >= 3}


def _label(e: dict) -> str:
    ml = e.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else str(ml or "")


def casar(esperado: str, entries: list) -> set:
    """'k-NN | Plano de Ensino' -> ids cujo id == trecho OU cujo titulo/label/raw CONTEM o trecho (normalizado)."""
    out = set()
    for part in str(esperado or "").split("|"):
        p = part.strip()
        if not p:
            continue
        pn = _norm(p)
        for e in entries:
            eid = str(e.get("id") or "")
            hay = " ".join(_norm(x) for x in (e.get("title"), _label(e), e.get("raw_target"), eid))
            if eid == p or (pn and pn in hay) or (p.lower() in str(e.get("raw_target") or "").lower()):
                out.add(eid)
    return out


_STOP = {"de", "do", "da", "dos", "das", "com", "em", "um", "uma", "para", "por", "usando", "the", "of", "and", "no", "na"}


def _toks2(t: str) -> set:
    """Tokens >= 2 chars (o gauge precisa ver 'nn' de k-NN), sem palavras-funcao."""
    return {x for x in _norm(t).split() if len(x) >= 2 and x not in _STOP}


_LINHA_RE = re.compile(r"(?:linha|#|item)\s*(\d{1,3})\b", re.I)


def filemap_rows(repo: Path, entries: list) -> dict:
    """{entry_id: {"num": N, "texto": linha inteira do FILE_MAP}} — o tutor cita a LINHA (descricao, 'linha N'),
    nao o Titulo. Linha de dados = '| N | Titulo | ...'; a de rastreabilidade seguinte traz o raw, que casa o entry."""
    p = Path(repo) / "course" / "FILE_MAP.md"
    if not p.is_file():
        return {}
    by_raw = {str(e.get("raw_target") or "").lower(): str(e.get("id") or "") for e in entries if e.get("raw_target")}
    by_title = {_norm(e.get("title")): str(e.get("id") or "") for e in entries if e.get("title")}
    out: dict = {}
    pend = None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|(.*)$", line)
        if m:
            cells = [c.strip() for c in m.group(2).split("|")]
            pend = {"num": int(m.group(1)), "texto": " ".join(cells), "titulo": cells[0] if cells else ""}
            continue
        if pend and "rastreabilidade" in line:
            raw = re.search(r"raw:\s*`([^`]+)`", line)
            eid = by_raw.get(str(raw.group(1)).lower(), "") if raw else ""
            if not eid:
                eid = by_title.get(_norm(pend["titulo"]), "")
            if eid:
                out[eid] = {"num": pend["num"], "texto": pend["texto"]}
            pend = None
    # CODE_INDEX: "| Titulo-resumo | Linguagem | Conceitos | `arquivo` |" — o arquivo casa o entry pelo nome no source_path
    ci = Path(repo) / "code" / "CODE_INDEX.md"
    if ci.is_file():
        by_file = {}
        for e in entries:
            sp = Path(str(e.get("source_path") or ""))
            if sp.name:
                by_file[sp.name.lower()] = str(e.get("id") or ""); by_file[_norm(sp.stem)] = str(e.get("id") or "")
        for line in ci.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|\s*`([^`]+)`", line)
            if not m or m.group(1).strip().lower() in ("título", "titulo", "---"):
                continue
            fn = m.group(2).strip()
            eid = by_file.get(fn.lower()) or by_file.get(_norm(Path(fn).stem)) or ""
            if not eid:
                # prefixo do nome (o CODE_INDEX pode truncar o arquivo)
                eid = next((v for k, v in by_file.items() if k.startswith(_norm(Path(fn).stem)[:30]) and _norm(Path(fn).stem)[:30]), "")
            if eid:
                cur = out.setdefault(eid, {"num": 0, "texto": ""})
                cur["texto"] = (cur["texto"] + " " + m.group(1).strip()).strip()
    return out


def casar_escolha(pick: str, entries: list, rows: Optional[dict] = None) -> str:
    """Escolha do LLM -> 1 id. 'linha N'/'#N' do FILE_MAP -> entry da linha; senao exato/contido (casar);
    senao o material com mais tokens em comum com titulo+label+linha do FILE_MAP (>= 2 tokens), desempate
    pelo titulo mais curto e pelo id. '' = nada plausivel."""
    rows = rows or {}
    m = _LINHA_RE.search(str(pick or ""))
    if m:
        n = int(m.group(1))
        for eid, r in rows.items():
            if r.get("num") == n:
                return eid
    exato = sorted(casar(pick, entries))
    if exato:
        return exato[0]
    q = _toks2(pick)
    best = []
    for e in entries:
        eid = str(e.get("id") or "")
        hay = _toks2(str(e.get("title") or "") + " " + _label(e) + " " + str((rows.get(eid) or {}).get("texto") or ""))
        s = len(q & hay)
        if s >= 2:
            best.append((-s, len(str(e.get("title") or "")), eid))
    best.sort()
    return best[0][2] if best else ""


def resumo_por_estilo(linhas: list) -> dict:
    """{estilo: {n, hit1, hit3}} sobre as linhas medidas (puladas fora). Estilo = estruturada | ambigua | malformada."""
    out: dict = {}
    for l in linhas:
        if "pulada" in l:
            continue
        est = str(l.get("estilo") or "") or "(sem estilo)"
        d = out.setdefault(est, {"n": 0, "hit1": 0, "hit3": 0})
        d["n"] += 1; d["hit1"] += bool(l.get("hit1")); d["hit3"] += bool(l.get("hit3"))
    return out


def pontuar(esperado_ids: set, picks: list) -> tuple:
    """(hit@1, hit@3): algum id esperado na 1a escolha / nas 3 primeiras."""
    if not esperado_ids or not picks:
        return False, False
    return picks[0] in esperado_ids, any(p in esperado_ids for p in picks[:3])


def escolher_sem_llm(pergunta: str, entries: list, k: int = 3) -> list:
    """Piso deterministico: ranking por |tokens(pergunta) & tokens(titulo+label+subtopico+secoes)|, desempate por id."""
    q = _toks(pergunta)
    scored = []
    for e in entries:
        hay = " ".join(str(x or "") for x in (e.get("title"), _label(e), e.get("computed_subunit_slug"), e.get("category"),
                                             e.get("markdown_headings_text"), e.get("source_section")))
        s = len(q & _toks(hay))
        if s:
            scored.append((-s, str(e.get("id") or "")))
    scored.sort()
    return [eid for _, eid in scored[:k]]


COMPLETO_ANTES = ("README.md", "system/TUTOR_POLICY.md")
COMPLETO_DEPOIS = ("code/CODE_INDEX.md", "exams/EXAM_INDEX.md", "exercises/EXERCISE_INDEX.md", "assignments/ASSIGNMENT_INDEX.md")


def contexto_navegacao(repo: Path, completo: bool = False) -> str:
    """Basico = os 4 indices da "ordem de consulta economica" do FILE_MAP. Completo = o que o tutor REAL tem:
    README + TUTOR_POLICY antes, indices por tipo (codigo/provas/exercicios/trabalhos) depois."""
    rels = [f"course/{n}" for n in INDICES]
    if completo:
        rels = list(COMPLETO_ANTES) + rels + list(COMPLETO_DEPOIS)
    parts = []
    for rel in rels:
        p = Path(repo) / rel
        if p.is_file():
            parts.append(f"\n\n===== {rel} =====\n" + p.read_text(encoding="utf-8", errors="replace"))
    return "".join(parts)[:MAX_CONTEXT]


def chave_cache(sig: str, pergunta: str, contexto: str) -> str:
    h = hashlib.sha1(contexto.encode("utf-8")).hexdigest()[:12]
    return hashlib.sha1(f"{sig}|{pergunta.strip()}|{h}".encode("utf-8")).hexdigest()


def _materiais(repo: Path) -> list:
    m = json.loads((Path(repo) / "manifest.json").read_text(encoding="utf-8"))
    return [e for e in m.get("entries", []) if str(e.get("file_type") or "") == "pdf" or e.get("category")]


def _bloco_display(repo: Path) -> dict:
    p = Path(repo) / "course" / ".timeline_index.json"
    if not p.is_file():
        return {}
    tl = json.loads(p.read_text(encoding="utf-8"))
    return {str(b.get("block_uuid") or ""): str(b.get("id") or "") for b in (tl.get("blocks") or [])}


def load_gold(path: Path) -> list:
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter=";"))
    return [r for r in rows if str(r.get("pergunta") or "").strip() and not str(r.get("pergunta")).startswith("#")]


def _picks_to_ids(resp: Resposta, entries: list, rows: Optional[dict] = None) -> list:
    ids: list = []
    for a in resp.arquivos or []:
        eid = casar_escolha(a, entries, rows)
        if eid and eid not in ids:
            ids.append(eid)
    return ids[:3]


def rodar(sig: str, repo: Path, gold: list, *, client=None, cache_path: Optional[Path] = None, cap: int = 60,
          completo: bool = False) -> dict:
    entries = _materiais(repo)
    u2d = _bloco_display(repo)
    rows = filemap_rows(repo, entries)
    modo = ("llm-completo" if completo else "llm") if client is not None else "sem-llm"
    contexto = contexto_navegacao(repo, completo=completo) if client is not None else ""
    cache: dict = {}
    if cache_path and Path(cache_path).is_file():
        cache = json.loads(Path(cache_path).read_text(encoding="utf-8"))
    chamadas = 0
    linhas = []
    hit1 = hit3 = bloco_ok = bloco_n = 0
    for r in gold:
        pergunta = str(r.get("pergunta") or "").strip()
        esperado = casar(str(r.get("esperado") or ""), entries)
        gold_bloco = str(r.get("bloco") or "").strip()
        if client is None:
            picks = escolher_sem_llm(pergunta, entries)
            bloco_llm = ""
            porque = ""
            escolhido_raw = []
        else:
            k = chave_cache(sig, pergunta, contexto)
            if k in cache:
                raw = cache[k]
            else:
                if chamadas >= cap:
                    linhas.append({"pergunta": pergunta, "pulada": "cap"}); continue
                resp = client.summarize_bundle(bundle_text=f"{contexto}\n\nPERGUNTA: {pergunta}", schema=Resposta,
                                               system_instruction=SYSTEM)
                chamadas += 1
                raw = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
                cache[k] = raw
                if cache_path:
                    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(cache_path).write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            resp = Resposta(**raw)
            picks = _picks_to_ids(resp, entries, rows)
            bloco_llm = str(resp.bloco or "")
            porque = str(resp.porque or "")
            escolhido_raw = list(resp.arquivos or [])
        h1, h3 = pontuar(esperado, picks)
        hit1 += h1; hit3 += h3
        # bloco: o que o LLM disse; senao, o bloco do 1o material escolhido
        bloco_pred = ""
        m = re.search(r"bloco-\d{2}", bloco_llm)
        if m:
            bloco_pred = m.group(0)
        elif picks:
            e0 = next((e for e in entries if e["id"] == picks[0]), {})
            bloco_pred = u2d.get(str(e0.get("temporal_block_id") or ""), "")
        b_ok = None
        if gold_bloco:
            bloco_n += 1; b_ok = bloco_pred == gold_bloco; bloco_ok += bool(b_ok)
        linhas.append({"pergunta": pergunta, "tipo": r.get("tipo", ""), "estilo": r.get("estilo", ""), "esperado": sorted(esperado), "escolhido": picks,
                       "hit1": h1, "hit3": h3, "bloco_gold": gold_bloco, "bloco_pred": bloco_pred, "bloco_ok": b_ok, "porque": porque,
                       "escolhido_raw": escolhido_raw})
    n = sum(1 for l in linhas if "pulada" not in l)
    return {"curso": sig, "modo": modo, "n": n, "hit1": hit1, "hit3": hit3, "bloco_ok": bloco_ok, "bloco_n": bloco_n,
            "chamadas": chamadas, "linhas": linhas}


TEMPLATE = """pergunta;esperado;bloco;tipo;nota
# Escreva uma pergunta de aluno por linha. 'esperado' = ids OU trechos do titulo/raw, separados por | (qualquer um vale).
# 'bloco' e opcional (bloco-NN do CRONOGRAMA_DETALHADO). Linhas que comecam com # sao ignoradas.
# Exemplos (APAGUE ou substitua):
como funciona o algoritmo k-NN para classificar?;k-NN;;conteudo;exemplo — materia dada em aula
tem algum codigo de exemplo de analise exploratoria?;analise exploratoria;;codigo;exemplo — notebook do professor
"""


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("curso")
    ap.add_argument("--sem-llm", action="store_true")
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--cap", type=int, default=60)
    ap.add_argument("--contexto-completo", action="store_true", help="README + TUTOR_POLICY + indices por tipo (o que o tutor real ve)")
    args = ap.parse_args(argv[1:])
    sig = args.curso.upper()
    repo = GITHUB_DIR / COURSES[sig]
    gold_path = REPORTS / f"travessia_gt_{sig}.csv"
    if args.template:
        if gold_path.exists():
            print(f"ja existe: {gold_path}"); return 1
        gold_path.write_text(TEMPLATE, encoding="utf-8")
        print(f"modelo criado: {gold_path}"); return 0
    if not gold_path.exists():
        print(f"sem gold: {gold_path} (use --template)"); return 2
    gold = load_gold(gold_path)
    client = None
    if not args.sem_llm:
        from src.builder.runtime.gemini_client import get_gemini_client
        cfg_path = Path.home() / ".gpt_tutor_config.json"
        config = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        client = get_gemini_client(config)
        if client is None:
            print("sem client Gemini (chave); use --sem-llm"); return 2
    cache_path = REPORTS / "_travessia_cache" / f"{sig}.json"
    r = rodar(sig, repo, gold, client=client, cache_path=cache_path if client else None, cap=args.cap,
              completo=args.contexto_completo)
    out = REPORTS / f"travessia_result_{sig}_{r['modo']}.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{sig} [{r['modo']}] perguntas={r['n']}  hit@1={r['hit1']}/{r['n']}  hit@3={r['hit3']}/{r['n']}  "
          f"bloco={r['bloco_ok']}/{r['bloco_n']}  chamadas novas={r['chamadas']}")
    for l in r["linhas"]:
        if "pulada" in l:
            print(f"  (pulada: cap) {l['pergunta'][:60]}"); continue
        mark = "OK " if l["hit1"] else ("ok3" if l["hit3"] else "ERR")
        print(f"  {mark} [{str(l.get('estilo') or '-')[:5]:5}] {l['pergunta'][:50]:50} esperado={','.join(l['esperado'])[:36]:36} escolhido={','.join(l['escolhido'])[:46]}"
              + (f"  bloco {l['bloco_pred'] or '-'}/{l['bloco_gold']}" if l["bloco_gold"] else ""))
        if not l["hit3"] and l.get("escolhido_raw"):
            print(f"       LLM disse: {' | '.join(str(a)[:70] for a in l['escolhido_raw'][:3])}  — {str(l.get('porque') or '')[:110]}")
    for est, d in resumo_por_estilo(r["linhas"]).items():
        print(f"  por estilo {est:12} hit@1={d['hit1']}/{d['n']}  hit@3={d['hit3']}/{d['n']}")
    print(f"resultado: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
