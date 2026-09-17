# -*- coding: utf-8 -*-
"""Guard byte-idêntico dos normalizadores — Fase 1 / P2 (pré-consolidação).

Congela o comportamento ATUAL de cada normalizador antes da unificação (Task 1.2+).
Se qualquer normalizador mudar de saída este teste FALHA — é esse o objetivo.

Valores esperados capturados rodando cada função sobre o corpus em 2026-06-17.
NÃO altere os `expected` sem re-capturar via execução real.

# Tabela de diferenças entre normalizadores
#
# | Aspecto                  | normalize_match_text(keep="") | _normalize_match_text(keep="+-./") | _norm (classifier)         |
# |--------------------------|-------------------------------|------------------------------------|----------------------------|
# | Módulo                   | src/builder/text/normalize.py | src/builder/extraction/content_taxonomy.py | src/builder/timeline/classifier.py |
# | Implementação            | fonte única                   | delega para normalize_match_text   | inline independente         |
# | NFKD + strip acentos     | sim                           | sim (herda)                        | sim                         |
# | lower()                  | sim                           | sim (herda)                        | sim                         |
# | — / – → -                | sim                           | sim (herda)                        | NÃO (vira espaço via regex) |
# | fix "propocional"        | sim                           | sim (herda)                        | NÃO                         |
# | chars extras mantidos    | nenhum                        | + - . /                            | nenhum                      |
# | regex strip              | [^a-z0-9 ws] -> espaco        | [^a-z0-9+-./ ws] -> espaco        | [^a-z0-9 ws] -> espaco     |
# | colapso de espaços       | sim                           | sim (herda)                        | sim                         |
# | strip()                  | sim                           | sim (herda)                        | sim                         |
#
# Divergências observadas no corpus:
#   "pre-condicao/pos-condicao" → keep="" vira "pre condicao pos condicao";
#                                  keep="+-./" mantém "pre-condicao/pos-condicao"
#   "C:/Moodle/Métodos Formais/intro.thy" → keep="" vira "c moodle metodos formais intro thy";
#                                            keep="+-./" → "c /moodle/metodos formais/intro.thy"
#   "P1 — Prova" → keep="" e _norm: "P1 - Prova" → keep="" = "p1 prova" (_norm: "p1 prova"),
#                   keep="+-./" = "p1 - prova" (— é convertido para - antes do strip)
#   _norm nao faz substituicao em-dash -> -: o travessao vira espaco via regex [^a-z0-9 espaco]
"""

import pytest

from src.builder.text.normalize import normalize_match_text
from src.builder.extraction.content_taxonomy import _normalize_match_text as taxonomy_normalize
from src.builder.timeline.classifier import _norm as classifier_norm

# ---------------------------------------------------------------------------
# Corpus: títulos, tópicos e labels reais do projeto (acentos, slugs, paths,
# hífens, em-dash, espaços múltiplos, códigos de prova).
# ---------------------------------------------------------------------------

_CORPUS = [
    "Lógica de Hoare",
    "Especificação de Conjuntos Indutivos",
    "pre-condicao/pos-condicao",
    "C:/Moodle/Métodos Formais/intro.thy",
    "P1 — Prova",
    "Verificação de Programas",
    "TDE Trabalho",
    "  espaços   múltiplos  ",
    "Árvores Binárias e Indução",
]

# ---------------------------------------------------------------------------
# Valores capturados em 2026-06-17 — NÃO alterar sem re-execução real
# ---------------------------------------------------------------------------

_EXPECTED_BASE: list[str] = [
    "logica de hoare",
    "especificacao de conjuntos indutivos",
    "pre condicao pos condicao",
    "c moodle metodos formais intro thy",
    "p1 prova",
    "verificacao de programas",
    "tde trabalho",
    "espacos multiplos",
    "arvores binarias e inducao",
]

_EXPECTED_TAXONOMY: list[str] = [
    "logica de hoare",
    "especificacao de conjuntos indutivos",
    "pre-condicao/pos-condicao",
    "c /moodle/metodos formais/intro.thy",
    "p1 - prova",
    "verificacao de programas",
    "tde trabalho",
    "espacos multiplos",
    "arvores binarias e inducao",
]

_EXPECTED_CLASSIFIER: list[str] = [
    "logica de hoare",
    "especificacao de conjuntos indutivos",
    "pre condicao pos condicao",
    "c moodle metodos formais intro thy",
    "p1 prova",
    "verificacao de programas",
    "tde trabalho",
    "espacos multiplos",
    "arvores binarias e inducao",
]


@pytest.mark.parametrize("text,expected", zip(_CORPUS, _EXPECTED_BASE))
def test_normalize_match_text_base(text: str, expected: str) -> None:
    """normalize_match_text com keep="" (fonte única, sem chars extras)."""
    assert normalize_match_text(text) == expected


@pytest.mark.parametrize("text,expected", zip(_CORPUS, _EXPECTED_TAXONOMY))
def test_normalize_match_text_taxonomy(text: str, expected: str) -> None:
    """_normalize_match_text de content_taxonomy (keep='+-./': mantém slugs e paths)."""
    assert taxonomy_normalize(text) == expected


@pytest.mark.parametrize("text,expected", zip(_CORPUS, _EXPECTED_CLASSIFIER))
def test_norm_classifier(text: str, expected: str) -> None:
    """_norm de classifier.py (NFKD+lower+[a-z0-9 ], sem fix de em-dash)."""
    assert classifier_norm(text) == expected
