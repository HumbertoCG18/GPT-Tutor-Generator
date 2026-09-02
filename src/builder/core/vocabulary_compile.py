"""Fase 1b (plano 02/09): vocabulario por curso SEM mao — 1 chamada de LLM por unidade
COM material, gravado em `course/.glossary_curation.llm.json` no formato do loader
(`repo.load_glossary_curation`: `{"<codigo> <Label do plano>": {"synonyms": [...]}}`, chaves
`_*` sao metadados). O loader funde este arquivo com o sidecar MANUAL `.glossary_curation.json`.

Por que o LLM: medido em 02/09 (`docs/reports/_harness-2026-09-02/compila_vocab_v2.py`) —
co-heading deterministico 26 -> 31/93 (refutado); este prompt IA 5 -> 37/39, FR 12 -> 17/19.
O LLM NAO inventa: classifica titulos/headings dos materiais da unidade nos topicos do plano.

Regras (decisoes C e D + o que o reprocess real de 02/09 ensinou):
- sidecar MANUAL existe -> o curso ja tem vocabulario: NAO chama (SO/IA/ES2/TCC intactos).
- `.llm.json` existe -> cache; `recompile=True` (flag `recompile_vocab`) rechama; `refilter=True`
  (flag `refilter_vocab`) reaplica os filtros sobre `_raw` SEM chamar (filtro muda, dado nao rola).
- chave = "<codigo> <label>" como o glossario escreve (R8: termo numerado casa so pelo nucleo
  exato — "3.1 Conceitos basicos" != "5.1 Conceitos basicos"). Sem codigo, so o label.
- filtros: termo == label · termo em > 1 topico (exclusividade) · termo cujo normalizado e id/
  titulo de um arquivo do curso · termo sem token especifico (so genericos do curso) ·
  **identidade**: termo igual ao nome de OUTRA unidade/topico, ou (>= 2 tokens) contido nele
  (CG: a aula 1 enumera as outras unidades e 48 materiais foram sugados para u01).
- unidades = `computed_unit_slug` do manifest (estrutura). Build do zero ainda nao tem unidade:
  nao grava nada e o reprocess seguinte compila.
Arquivo separado do manual (deviacao registrada do plano, que dizia "mesmo arquivo"): o motor
puro apaga a curadoria manual e mantem o compilado — sem isso a regua "puro + vocab compilado"
precisaria de caso especial, e recompilar nunca sobrescreve trabalho humano.
"""
from __future__ import annotations

import collections
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map
from src.builder.extraction.content_taxonomy import _extract_markdown_headings, _topic_support_tokens
from src.builder.routing.resolver_apply import _is_material
from src.builder.text.normalize import normalize_match_text
from src.utils.helpers import write_text

logger = logging.getLogger(__name__)

LLM_VOCAB_NAME = ".glossary_curation.llm.json"
MANUAL_VOCAB_NAME = ".glossary_curation.json"
# Fora do vocabulario: avaliacoes e meta-material nao descrevem UM topico.
OUT_CATS = frozenset({"cronograma", "provas", "trabalhos", "fotos-de-prova"})
MAX_BUNDLE_CHARS = 24000
_UNIT_PREFIX_WORDS = {"unidade", "de", "aprendizagem", "modulo", "parte", "topico", "ua"}


class TopicoTermos(BaseModel):
    topico: str = Field(description="label do topico, exatamente como dado")
    termos: List[str] = Field(default_factory=list,
                              description="termos/expressoes DOS MATERIAIS que pertencem a este topico")


class Vocab(BaseModel):
    topicos: List[TopicoTermos] = Field(default_factory=list)


# Prompt v2 — o unico ajuste permitido, medido (IA 34 -> 37/39). Nao mexer sem remedir.
SYSTEM = (
    "Voce recebe os TOPICOS de uma unidade do plano de ensino e os titulos e headings dos MATERIAIS "
    "dessa unidade. Tarefa: para cada topico, liste os termos e expressoes curtas (1-4 palavras) que "
    "APARECEM nos materiais e que pertencem a esse topico (nomes de algoritmos, tecnicas, siglas, "
    "conceitos). Inclua os termos dos TITULOS e as VARIANTES que aparecem no texto (sigla, ingles e "
    "portugues, singular e plural, ex.: 'clustering', 'cluster', 'agrupamento', 'EDA', 'analise "
    "exploratoria'). Regras: (1) so termos presentes no texto dado — nao invente; (2) cada termo em no "
    "maximo um topico; (3) ignore palavras genericas (introducao, exercicio, aula, exemplo, revisao) "
    "e o nome da disciplina; (4) se nenhum material cobre um topico, devolva lista vazia; (5) responda "
    "apenas o JSON do schema."
)


def _norm(text: str) -> str:
    return " ".join(normalize_match_text(str(text or "")).split())


def _strip_code(text: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", " ".join(str(text or "").split()))


def topic_key(topic: dict) -> str:
    """Chave do sidecar = texto do topico como o glossario o escreve ("1.2 Modelos OSI e TCP/IP")."""
    code = str(topic.get("code") or "").strip()
    label = " ".join(str(topic.get("label") or "").split())
    return f"{code} {label}".strip()


def unit_title_core(title: str) -> str:
    """"Unidade de Aprendizagem 4 — Processo de Visualizacao 2D (10%)" -> "processo de visualizacao 2d"."""
    toks = _norm(title).split()
    while toks and (toks[0] in _UNIT_PREFIX_WORDS or toks[0].isdigit()):
        toks.pop(0)
    while toks and toks[-1].isdigit():
        toks.pop()
    return " ".join(toks)


def identities_of(taxonomy: dict) -> dict:
    """{"labels": {key: (unit_slug, label_norm)}, "units": {unit_slug: core_norm}} da taxonomia."""
    labels: Dict[str, tuple] = {}
    units: Dict[str, str] = {}
    for unit in (taxonomy or {}).get("units") or []:
        slug = str(unit.get("slug") or "")
        core = unit_title_core(str(unit.get("title") or ""))
        if core:
            units[slug] = core
        for topic in unit.get("topics") or []:
            if topic.get("label"):
                labels[topic_key(topic)] = (slug, _norm(topic["label"]))
    return {"labels": labels, "units": units}


def _generic_tokens(taxonomy: dict) -> set:
    """Genericos do curso (A2/df), os mesmos carimbados nos topicos pelo scorer de subunidade."""
    try:
        from src.builder.timeline.index import _iter_content_taxonomy_topics
        topics = _iter_content_taxonomy_topics(taxonomy) or []
        return set((topics[0].get("generic_tokens") if topics else None) or [])
    except Exception:
        return set()


def filter_terms(compilado: Dict[str, List[str]], *, generic: set, file_names: set,
                 identities: Optional[dict] = None) -> Dict[str, List[str]]:
    """Pos-filtro (decisao C + identidade). `compilado` = {chave: [termos crus]} -> {chave: [termos]}."""
    ids = identities or {"labels": {}, "units": {}}
    label_norm = {key: ids["labels"].get(key, ("", _norm(_strip_code(key))))[1] for key in compilado}
    onde: Dict[str, set] = collections.defaultdict(set)
    for key, termos in compilado.items():
        for t in termos:
            tn = _norm(t)
            if tn:
                onde[tn].add(key)
    out: Dict[str, List[str]] = {}
    for key, termos in compilado.items():
        own_unit = ids["labels"].get(key, ("", ""))[0]
        others = {v[1] for k, v in ids["labels"].items() if k != key} | \
                 {core for u, core in ids["units"].items() if u != own_unit}
        keep: List[str] = []
        seen: set = set()
        for t in termos:
            t = " ".join(str(t or "").split())
            tn = _norm(t)
            if not tn or tn in seen or tn == label_norm[key] or len(onde[tn]) > 1 or tn in file_names:
                continue
            if tn in others or (len(tn.split()) >= 2 and any(tn in o for o in others)):
                continue
            if not {x for x in _topic_support_tokens(t) if x not in generic}:
                continue
            seen.add(tn)
            keep.append(t)
        out[key] = keep
    return out


def _bundle(taxonomy: dict, unit: dict, labels: List[str], mats: List[dict], root: Path) -> str:
    linhas = []
    for e in mats:
        md = _entry_markdown_text_for_file_map(root, e) or ""
        heads = _extract_markdown_headings(md, limit=24)
        ml = e.get("moodle_label")
        ml = ml.get("text", "") if isinstance(ml, dict) else str(ml or "")
        linhas.append(f"- TITULO: {e.get('title')} | LABEL MOODLE: {ml}\n  HEADINGS: "
                      + " | ".join(h[:60] for h in heads[:24]))
    return (f"DISCIPLINA: {taxonomy.get('course_name') or ''}\nUNIDADE: {unit.get('title')}\nTOPICOS DO PLANO:\n"
            + "\n".join(f"  * {label}" for label in labels) + "\n\nMATERIAIS:\n" + "\n".join(linhas))[:MAX_BUNDLE_CHARS]


def _load(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _file_names(entries: list) -> set:
    out = set()
    for e in entries:
        for k in ("id", "title"):
            n = _norm(str(e.get(k) or ""))
            if n:
                out.add(n)
    return out


def _write(out_path: Path, root: Path, raw: Dict[str, List[str]], entries: list, taxonomy: dict, *,
           modelo: str, erros: List[str], chamadas: int) -> dict:
    filtrado = filter_terms(raw, generic=_generic_tokens(taxonomy), file_names=_file_names(entries),
                            identities=identities_of(taxonomy))
    out: dict = {
        "_provenance": "llm",
        "_modelo": modelo,
        "_nota": ("Vocabulario compilado por LLM (Fase 1b, 1 chamada por unidade com material; termos dos "
                  "titulos/headings dos materiais classificados nos topicos do plano). Cache: reprocess nao "
                  "rechama; recompilar = flag recompile_vocab; refiltrar sem chamar = refilter_vocab (usa _raw). "
                  f"Para curar a mao, edite/crie {MANUAL_VOCAB_NAME} (o loader funde os dois)."),
        "_raw": {k: list(v) for k, v in raw.items()},
    }
    if erros:
        out["_unidades_com_erro"] = erros
    for key, termos in filtrado.items():
        if termos:
            out[key] = {"synonyms": termos}
    write_text(out_path, json.dumps(out, ensure_ascii=False, indent=2))
    logger.info("vocab: %s — %d chamada(s), %d topico(s) com termos, %d termo(s)%s", root.name, chamadas,
                sum(1 for v in filtrado.values() if v), sum(len(v) for v in filtrado.values()),
                f", erro em {erros}" if erros else "")
    return out


def compile_course_vocabulary(root, entries: list, taxonomy: dict, client, *, recompile: bool = False,
                              refilter: bool = False) -> Optional[dict]:
    """Devolve o sidecar compilado (dict no formato do loader) ou None (nao compilou)."""
    root = Path(root)
    manual = root / "course" / MANUAL_VOCAB_NAME
    out_path = root / "course" / LLM_VOCAB_NAME
    if manual.is_file():
        logger.info("vocab: sidecar manual presente em %s — nao compila", root.name)
        return None
    if out_path.is_file() and not recompile:
        atual = _load(out_path)
        if refilter and atual and isinstance(atual.get("_raw"), dict) and taxonomy:
            return _write(out_path, root, atual["_raw"], entries, taxonomy, modelo=str(atual.get("_modelo") or ""),
                          erros=list(atual.get("_unidades_com_erro") or []), chamadas=0)
        return atual
    if client is None or not taxonomy:
        return None

    mats = [e for e in entries if _is_material(e) and str(e.get("category") or "").strip().lower() not in OUT_CATS]
    por_unidade: Dict[str, List[dict]] = collections.defaultdict(list)
    for e in mats:
        u = str(e.get("computed_unit_slug") or "").strip()
        if u:
            por_unidade[u].append(e)
    if not por_unidade:
        logger.info("vocab: nenhum material com unidade em %s (build do zero?) — compila no proximo reprocess", root.name)
        return None

    raw: Dict[str, List[str]] = {}
    erros: List[str] = []
    chamadas = 0
    for unit in taxonomy.get("units") or []:
        slug = str(unit.get("slug") or "")
        topics = [t for t in (unit.get("topics") or []) if t.get("label")]
        if not topics or not por_unidade.get(slug):
            continue
        key_of = {" ".join(str(t["label"]).split()): topic_key(t) for t in topics}
        for key in key_of.values():
            raw.setdefault(key, [])
        try:
            res = client.summarize_bundle(bundle_text=_bundle(taxonomy, unit, list(key_of), por_unidade[slug], root),
                                          schema=Vocab, system_instruction=SYSTEM)
            chamadas += 1
        except Exception as exc:
            logger.warning("vocab: unidade %s falhou (%s: %s)", slug, type(exc).__name__, exc)
            erros.append(slug)
            continue
        for tt in getattr(res, "topicos", None) or []:
            key = key_of.get(" ".join(str(tt.topico or "").split()))
            if key:
                raw[key].extend(" ".join(str(t).split()) for t in tt.termos if str(t or "").strip())
    return _write(out_path, root, raw, entries, taxonomy, modelo=str(getattr(client, "model", "") or ""),
                  erros=erros, chamadas=chamadas)
