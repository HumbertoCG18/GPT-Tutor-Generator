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


def process_reference_entry(entry: dict, units: list, client) -> dict:
    """Enriquece UMA entry de referência: busca texto, resume (lazy), mapeia
    unidade/tópico. Retorna um dict de campos a mesclar na entry.

    Sem client -> sem resumo, mas ainda mapeia por texto fetchado (determinístico).
    """
    text = fetch_reference_text(entry)
    summary_dict = summarize_reference(text, client)  # None sem client/texto
    concepts = (summary_dict or {}).get("concepts", []) or []
    fallback = " ".join([str(entry.get("title", "") or ""), text])
    topic = assign_concepts_to_unit(concepts, fallback, units)
    return {
        "ref_summary": (summary_dict or {}).get("summary", "") or "",
        "ref_concepts": concepts,
        "computed_ref_unit": topic["unit_slug"],
        "computed_ref_topics": topic["topics"],
    }
