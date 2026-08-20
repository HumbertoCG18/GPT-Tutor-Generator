"""Cobertura do MATERIAL: `coverage_units[]`, N unidades por arquivo.

Eixo separado do 1:1. `computed_unit_slug` continua respondendo *em que unidade
este arquivo mora*; aqui a pergunta e *que unidades este arquivo cobre*, que para
prova, lista, plano de ensino e serie de laboratorio tem mais de uma resposta
certa — 53 arquivos avaliativos nos 5 cursos recebiam UMA subunidade so.

Formato identico ao da camada de referencia (`reference_summary.py:135`):
`[{unit_slug, topics, confidence, rule}]`, ordenado por confianca.

As tres regras vieram de rulings do user em 2026-08-19, rotulando 64 casos:
  A  meta-material (plano de ensino, programa, apresentacao) cobre TODAS
  B  "Lista PX" cobre as unidades da PROVA — extraidas do enunciado
  C  o card do Moodle nomeia a unidade/topico -> essa unidade entra
Sem elas, o mesmo julgamento teria de ser refeito a mao em cada curso novo.

Nenhuma regra olha nome de arquivo nem de cadeira: meta e detectado por CITAR o
titulo de quase todas as unidades, avaliacao pelo padrao "PX" no titulo, e o
card pela evidencia de topicos. Cadeira nova entra sem configuracao.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional

# Categorias cujo material DESCREVE o curso em vez de ensinar um pedaco dele.
# So um atalho: a deteccao real e por conteudo (`_FRACAO_META`), porque
# `apresentacao-da-disciplina` e `material-de-aula` e `programa` e `outros`.
META_CATEGORIES: frozenset = frozenset({"cronograma"})
# Fracao dos titulos de unidade que o texto precisa citar para ser meta.
# Medido no SO: plano/programa/apresentacao citam 7 de 7; a lista P1 cita 1 de 7.
_FRACAO_META = 0.8
# Categorias de avaliacao: cobrem o que a prova cobre, nao uma unidade so.
AVALIACAO_CATEGORIES: frozenset = frozenset({"listas", "gabaritos", "provas"})
# "P1", "Prova 2", "Av3", "Lista1" — avaliacao com escopo definido.
_PROVA_RE = re.compile(r"\b(?:p|prova|av|lista)\s*-?\s*([12345])\b", re.IGNORECASE)
# Um topico so nao sustenta a unidade inteira: exige 2 topicos OU o titulo dela.
_MIN_TOPICOS_PARA_UNIDADE = 2
# Token longo o bastante para ser termo tecnico proprio, nao conectivo. O card do
# TCC diz "Halteproblem und Entscheidungsproblem" (alemao) e o label da taxonomia
# e "entscheidungsproblem e introducao a reducibilidade de problemas": substring
# nao casa, token casa. 8 chars deixa `problema`/`sistema` de fora do acaso.
_MIN_TOKEN_DISTINTIVO = 10


def _casa(frase: str, alvo: str) -> bool:
    """Contencao OU token distintivo compartilhado."""
    if not frase or not alvo:
        return False
    if frase in alvo or alvo in frase:
        return True
    tokens_frase = {t for t in frase.split() if len(t) >= _MIN_TOKEN_DISTINTIVO}
    if not tokens_frase:
        return False
    return bool(tokens_frase & {t for t in alvo.split() if len(t) >= _MIN_TOKEN_DISTINTIVO})


def _topicos_por_unidade(topic_index: Optional[List[dict]], normalize: Callable[[str], str]) -> Dict[str, List[str]]:
    """{unit_slug: [label normalizado]} a partir da TAXONOMIA.

    De proposito nao usa `unit["topic_phrases"]`: aquilo mistura os topicos do
    plano com `extra_signals` do glossario, e palavra solta como `kernel` ou
    `sistema` entrava como se fosse topico — foi o que fez a lista P1 do SO
    reivindicar a unidade de gerencia de ARQUIVOS (medido 2026-08-19).
    """
    por_unidade: Dict[str, List[str]] = {}
    for topico in topic_index or []:
        slug = str(topico.get("unit_slug") or "")
        if not slug:
            continue
        # Label E aliases: os dois sao do TOPICO. O card do TCC diz
        # "Halteproblem und Entscheidungsproblem" e o label completo e
        # "entscheidungsproblem e introducao a reducibilidade de problemas" —
        # so o alias curto casa. Descartar aliases custou 2 acertos (medido).
        for bruto in [topico.get("topic_label")] + list(topico.get("aliases") or []):
            frase = normalize(str(bruto or ""))
            if frase and len(frase) >= 6:
                por_unidade.setdefault(slug, []).append(frase)
    return {k: sorted(dict.fromkeys(v)) for k, v in por_unidade.items()}


def derive_coverage_units(
    entry: dict,
    unit_index: List[dict],
    texto: str,
    *,
    normalize: Callable[[str], str],
    fallback_unit_slug: str = "",
    topic_index: Optional[List[dict]] = None,
) -> List[Dict[str, object]]:
    """[{unit_slug, topics, confidence, rule}] — vazio quando nenhuma regra casa."""
    if not unit_index:
        return []
    categoria = str(entry.get("category") or "").strip().lower()
    titulo = str(entry.get("title") or "")
    card_norm = normalize(str(entry.get("source_section") or ""))
    texto_norm = normalize(texto or "")
    topicos_taxonomia = _topicos_por_unidade(topic_index, normalize)

    def _todas(regra: str) -> List[Dict[str, object]]:
        return [
            {"unit_slug": str(u.get("slug")), "topics": [], "confidence": 1.0, "rule": regra}
            for u in unit_index
        ]

    # A) meta-material: descreve o curso inteiro. Detectado por CONTEUDO — cita o
    #    titulo de quase todas as unidades — e nao por nome de arquivo.
    if categoria in META_CATEGORIES:
        return _todas("meta")
    titulos = [str(u.get("normalized_title") or "") for u in unit_index]
    titulos = [t for t in titulos if len(t) >= 6]
    if titulos and texto_norm:
        citados = sum(1 for t in titulos if t in texto_norm)
        if citados / len(titulos) >= _FRACAO_META:
            return _todas("meta-por-conteudo")

    cobertas: Dict[str, Dict[str, object]] = {}

    # B) avaliacao com escopo: as unidades que o enunciado de fato cita.
    if categoria in AVALIACAO_CATEGORIES and _PROVA_RE.search(titulo):
        for unit in unit_index:
            slug = str(unit.get("slug"))
            achados = sorted({t for t in topicos_taxonomia.get(slug, []) if t in texto_norm})
            titulo_unidade = str(unit.get("normalized_title") or "")
            cita_titulo = bool(titulo_unidade) and len(titulo_unidade) >= 6 and titulo_unidade in texto_norm
            if len(achados) >= _MIN_TOPICOS_PARA_UNIDADE or cita_titulo:
                cobertas[slug] = {
                    "unit_slug": slug, "topics": achados,
                    "confidence": round(min(1.0, 0.4 + 0.2 * len(achados)), 3),
                    "rule": "avaliacao",
                }

    # C) o card do Moodle nomeia a unidade ou um topico dela (sinal humano: o
    #    professor postou o material naquela secao). 228 de 233 entries tem card.
    if card_norm and len(card_norm) >= 4:
        candidatos = []
        for unit in unit_index:
            slug = str(unit.get("slug"))
            titulo_unidade = str(unit.get("normalized_title") or "")
            bate_titulo = bool(titulo_unidade) and (titulo_unidade in card_norm or card_norm in titulo_unidade)
            topicos_card = sorted({
                t for t in topicos_taxonomia.get(slug, []) if _casa(t, card_norm)
            })
            if bate_titulo or topicos_card:
                candidatos.append((bate_titulo, len(topicos_card), slug, topicos_card))
        # Um card nomeia UMA coisa. Quando casa varias unidades e porque o termo
        # aparece em mais de uma (o card `Microsservicos` do ES2 casa a u01, com 3
        # topicos de microsservicos, e a u02, com 1). Fica a de MAIOR evidencia;
        # empate genuino mantem todas, que ai a ambiguidade e real.
        if candidatos:
            melhor = max((c[0], c[1]) for c in candidatos)
            for bate_titulo, n_top, slug, topicos_card in candidatos:
                if (bate_titulo, n_top) != melhor or slug in cobertas:
                    continue
                cobertas[slug] = {
                    "unit_slug": slug, "topics": topicos_card,
                    "confidence": 0.9 if bate_titulo else 0.7, "rule": "card",
                }

    # A unidade 1:1 ja decidida entra na cobertura: cobrir e superconjunto de morar.
    if fallback_unit_slug and fallback_unit_slug not in cobertas:
        cobertas[fallback_unit_slug] = {
            "unit_slug": fallback_unit_slug, "topics": [],
            "confidence": 0.5, "rule": "unidade-atribuida",
        }

    return sorted(cobertas.values(), key=lambda c: (-float(c["confidence"]), str(c["unit_slug"])))
