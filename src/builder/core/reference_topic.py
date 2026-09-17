"""Mapa de relevância de uma referência -> unidade/tópico (NÃO bloco).

Espelha code_summarization.assign_code_to_block, mas o alvo é a unidade: faz
overlap dos tokens de concept (ou, sem concepts, do texto) contra o "bag" de
tokens de cada unidade do índice. Determinístico, sem rede, sem Gemini.
"""
from __future__ import annotations

from typing import List

from src.builder.core.code_summarization import _normalize, _stem, _expand_concept_tokens


def _unit_bag(unit: dict) -> set[str]:
    bag: set[str] = set()
    fields: List[str] = []
    fields.append(unit.get("normalized_title", "") or "")
    fields.extend(unit.get("topic_phrases", []) or [])
    fields.extend(unit.get("topic_tokens", []) or [])
    fields.extend(unit.get("distinctive_tokens", []) or [])
    for f in fields:
        for tok in _normalize(f).split():
            if len(tok) >= 4:
                bag.add(tok)
                bag.add(_stem(tok))
    bag.discard("")
    return bag


def _phrase_bag(phrase: str) -> set[str]:
    bag: set[str] = set()
    for tok in _normalize(phrase).split():
        if len(tok) >= 4:
            bag.add(tok)
            bag.add(_stem(tok))
    return bag


def _palavra_citada(palavra: str, texto_bag: set[str]) -> bool:
    """A palavra aparece no texto — exata, pelo radical, ou como parte de palavra
    composta. O ultimo caso e necessario: "pthread"/"threads" precisa casar o
    topico "Programas multithreads" do plano do SO, e nenhum radical liga os dois.
    Piso de 6 caracteres para a contencao, senao radicais curtos casam qualquer
    coisa."""
    if palavra in texto_bag or _stem(palavra) in texto_bag:
        return True
    if len(palavra) < 6:
        return False
    return any(len(t) >= 6 and (palavra in t or t in palavra) for t in texto_bag)


def _frase_citada(phrase: str, texto_bag: set[str]) -> bool:
    """Toda palavra significativa da frase precisa aparecer. Exigir o conjunto
    inteiro de variantes (token E radical) era criterio impossivel — nenhuma frase
    passava, e a cobertura dava zero em 10 de 10 refs (medido 2026-08-18)."""
    palavras = [tok for tok in _normalize(phrase).split() if len(tok) >= 4]
    return bool(palavras) and all(_palavra_citada(w, texto_bag) for w in palavras)


def assign_concepts_to_unit(
    concepts: List[str],
    fallback_text: str,
    units: List[dict],
    *,
    primary_threshold: float = 0.34,
    margin_threshold: float = 0.10,
) -> dict:
    """Cobertura de uma referência: TODAS as unidades acima do threshold.

    Retorna {"unit_slug", "topics", "confidence", "units": [{unit_slug, topics,
    confidence}]}. As três primeiras chaves são a unidade vencedora e existem por
    compatibilidade (COURSE_MAP e BIBLIOGRAPHY consomem uma unidade só).

    Material transversal cobre VÁRIAS unidades — o single-winner elegia uma e
    descartava o resto. `topics` são os tópicos que de fato casaram, não todos os
    da unidade. `margin_threshold` é ignorado: margem separa vencedor de
    vice-campeão, o que não faz sentido quando a resposta certa é um conjunto.
    """
    terms = [c for c in (concepts or []) if c]
    if not terms and fallback_text:
        terms = [t for t in fallback_text.split() if len(t) >= 4]
    terms_norm = [_normalize(t) for t in terms]
    terms_norm = [t for t in terms_norm if t]
    vazio = {"unit_slug": "", "topics": [], "confidence": 0.0, "units": []}
    if not terms_norm or not units:
        return vazio

    term_token_sets = [_expand_concept_tokens(t) for t in terms_norm]
    # Sem `concepts` (build sem Gemini) os termos sao o texto inteiro. Medir a
    # fracao dos termos que casam dilui o score a zero — a pergunta certa passa a
    # ser quantos topicos DA UNIDADE o texto cita.
    por_texto_bruto = not [c for c in (concepts or []) if c]
    texto_bag: set[str] = set()
    if por_texto_bruto:
        for toks in term_token_sets:
            texto_bag |= toks

    cobertas = []
    for unit in units:
        bag = _unit_bag(unit)
        if not bag:
            continue
        phrases = [p for p in (unit.get("topic_phrases", []) or []) if p]
        if por_texto_bruto:
            citados = [p for p in phrases if _frase_citada(p, texto_bag)]
            # Uma frase DISTINTIVA citada ja cobre a unidade. Fracao como criterio
            # nao funciona: o glossario infla `topic_phrases` (29 na u03 do SO) e
            # 1/29 nunca cruza o threshold. A fracao fica sendo so a confianca.
            fortes = [p for p in citados
                      if len([w for w in _normalize(p).split() if len(w) >= 4]) >= 2]
            score = (len(citados) / len(phrases)) if phrases else 0.0
            if not fortes:
                continue
            cobertas.append({"unit_slug": unit.get("slug", ""), "topics": citados[:3],
                             "confidence": round(score, 3)})
            continue
        else:
            overlap = sum(1 for toks in term_token_sets if toks & bag)
            score = overlap / len(term_token_sets)
        if score < primary_threshold:
            continue
        if por_texto_bruto:
            casados = citados
        else:
            casados = [
                phrase for phrase in phrases
                if (lambda pb: pb and any(toks & pb for toks in term_token_sets))(_phrase_bag(phrase))
            ]
        cobertas.append({
            "unit_slug": unit.get("slug", ""),
            "topics": casados[:3],
            "confidence": round(score, 3),
        })

    if not cobertas:
        return vazio
    cobertas.sort(key=lambda u: u["confidence"], reverse=True)
    # Cobertura real de uma referencia raramente passa de 2 unidades. Sem corte, o
    # criterio de frase distintiva enche a lista de unidades marginais e derruba a
    # precisao (medido 2026-08-18). Mantem as que chegam a metade da confianca da
    # melhor, no maximo 2.
    teto = cobertas[0]["confidence"]
    cobertas = [u for u in cobertas if u["confidence"] >= teto * 0.5][:2]
    winner = cobertas[0]
    return {
        "unit_slug": winner["unit_slug"],
        "topics": list(winner["topics"]),
        "confidence": winner["confidence"],
        "units": cobertas,
    }
