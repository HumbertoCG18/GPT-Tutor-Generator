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

REFERENCE_MATCHER_VERSION = 1
_REFERENCE_CATEGORIES = {"referencias", "bibliografia"}


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

    refs = [e for e in manifest.get("entries", [])
            if str(e.get("category") or "").lower() in _REFERENCE_CATEGORIES]
    for idx, entry in enumerate(refs):
        eid = entry.get("id")
        if not eid:
            continue
        text = fetch_reference_text(entry)
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
        fallback = " ".join([str(entry.get("title", "") or ""), text])
        topic = assign_concepts_to_unit(concepts, fallback, units)
        cache[eid] = {
            "ref_summary": (summary_dict or {}).get("summary", "") or "",
            "ref_concepts": concepts,
            "computed_ref_unit": topic["unit_slug"],
            "computed_ref_topics": topic["topics"],
            "content_hash": h,
            "matcher_version": REFERENCE_MATCHER_VERSION,
        }
        if progress_cb:
            progress_cb(idx, len(refs), entry.get("title", ""), "ok")

    write_reference_curation(builder.root_dir, curation)
    return curation
