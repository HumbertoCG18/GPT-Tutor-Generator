"""Resumo de referência via Gemini (lazy) + batch com cache por content-hash.

Espelha core/code_summarization, mas o alvo é UMA referência bibliográfica
(repo/doc), não um bundle de código, e o resultado dá contexto base ao tutor.
"""
from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel, Field

from src.builder.core.reference_content import fetch_reference_text
from src.builder.core.reference_topic import assign_concepts_to_unit

logger = logging.getLogger(__name__)


class ReferenceSummary(BaseModel):
    inferred_title: str = Field(..., description="Título descritivo da referência")
    summary: str = Field(..., description="3-5 linhas: o que a referência cobre e como ajuda o aluno")
    concepts: list[str] = Field(..., description="3-8 termos técnicos do domínio cobertos")


REFERENCE_SYSTEM_INSTRUCTION = """Você resume referências bibliográficas (repos
GitHub, documentações, artigos) de uma disciplina universitária para um tutor LLM.

A saída dá ao tutor CONTEXTO BASE: o que a referência ensina/demonstra e quais
conceitos ela cobre, para o tutor aprofundar explicações.

Regras:
- inferred_title: descritivo, não repita a URL.
- summary: 3-5 frases. O que a referência cobre, que problema resolve, como
  serve de apoio ao estudo. Não invente o que não está no texto.
- concepts: 3-8 termos técnicos do domínio.
- Português brasileiro. Saída APENAS JSON válido conforme schema."""


def summarize_reference(text: str, client) -> Optional[dict]:
    """{summary, concepts, inferred_title} via Gemini, ou None (sem client, texto
    vazio, ou falha). Lazy: nunca quebra o build."""
    if client is None or not (text or "").strip():
        return None
    try:
        result: ReferenceSummary = client.summarize_bundle(
            bundle_text=text,
            schema=ReferenceSummary,
            system_instruction=REFERENCE_SYSTEM_INSTRUCTION,
        )
        return result.model_dump()
    except Exception as exc:
        logger.error("[ReferenceSummary] falha: %s", exc)
        return None


import json
import hashlib
from pathlib import Path

# v2 (2026-08-18): cobertura N:N, texto local do repo antes da rede, card no
# fallback e casamento de frase por palavra. Bump invalida o cache antigo.
REFERENCE_MATCHER_VERSION = 2
# O dado real tem 3 grafias: a UI documenta `referencias`, o manifest tambem
# traz `references` (MF 1, IA 2 entries vivas em 2026-08-18).
_REFERENCE_CATEGORIES = {"referencias", "references", "bibliografia"}


def load_reference_curation(repo_dir: Path) -> dict:
    p = Path(repo_dir) / "course" / "references_curation.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {"entries": {}}
    return {"entries": {}}


def write_reference_curation(repo_dir: Path, data: dict) -> None:
    p = Path(repo_dir) / "course" / "references_curation.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def _ref_hash(entry: dict, text: str) -> str:
    key = (str(entry.get("source_path") or "") + "\n" + (text or "")).encode("utf-8", "replace")
    return hashlib.sha1(key).hexdigest()


def summarize_all_reference_entries(builder, units: list, client, progress_cb=None) -> dict:
    """Processa entries de referência do manifest e grava SÓ references_curation.json
    (keyed por entry id). NÃO escreve o manifest — os campos ref vivem só na
    curation, como os resumos de código em code_curation.json. Cache por hash.
    Sem client -> mapeia por texto, sem resumo."""
    manifest_path = Path(builder.root_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    curation = load_reference_curation(builder.root_dir)
    cache = curation.setdefault("entries", {})

    entries = manifest.get("entries", []) or []
    # Poda de orfaos: a curation guardava entries que sumiram do manifest (ES2 6/6,
    # TCC 2/2 em 2026-08-18). code_curation ja podava; esta nao.
    ids_vivos = {str(e.get("id") or "") for e in entries}
    for eid in [k for k in cache if k not in ids_vivos]:
        cache.pop(eid, None)

    refs = [e for e in entries
            if str(e.get("category") or "").lower() in _REFERENCE_CATEGORIES]
    for idx, entry in enumerate(refs):
        eid = entry.get("id")
        if not eid:
            continue
        text = fetch_reference_text(entry, repo_root=builder.root_dir)
        h = _ref_hash(entry, text)
        existing = cache.get(eid, {})
        if (existing.get("content_hash") == h
                and existing.get("matcher_version") == REFERENCE_MATCHER_VERSION
                and (existing.get("ref_summary") or client is None)):
            if progress_cb:
                progress_cb(idx, len(refs), entry.get("title", ""), "cached")
            continue
        summary_dict = summarize_reference(text, client)
        concepts = (summary_dict or {}).get("concepts", []) or []
        # o card (`source_section`) e sinal humano forte: o professor postou o
        # material naquela secao. Ja validado no eixo de unidade (2026-08-18).
        fallback = " ".join([str(entry.get("title", "") or ""),
                             str(entry.get("source_section", "") or ""), text])
        topic = assign_concepts_to_unit(concepts, fallback, units)
        cache[eid] = {
            "ref_summary": (summary_dict or {}).get("summary", "") or "",
            "ref_concepts": concepts,
            # cobertura N:N; os dois campos abaixo sao a unidade vencedora e seguem
            # existindo porque COURSE_MAP/BIBLIOGRAPHY consomem uma unidade so.
            "coverage_units": topic.get("units", []),
            "computed_ref_unit": topic["unit_slug"],
            "computed_ref_topics": topic["topics"],
            "content_hash": h,
            "matcher_version": REFERENCE_MATCHER_VERSION,
        }
        if progress_cb:
            progress_cb(idx, len(refs), entry.get("title", ""), "ok")

    write_reference_curation(builder.root_dir, curation)
    return curation
