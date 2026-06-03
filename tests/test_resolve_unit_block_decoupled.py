"""Integration test: REAL scorer end-to-end (no stubbed period_fn).

Exercita o scorer real `select_probable_period_for_entry` (via o wrapper
`_select_probable_period_for_entry` da engine, que injeta TODOS os callables
reais — normalize_match_text, score_text_against_row, score_card_evidence,
build_timeline_index etc.), NAO um lambda stub.

Objetivo: provar a claim de manchete da Fase 1 — um material cujo palpite de
unidade e fraco/ambiguo mas que tem uma data/titulo obvios ainda recebe o bloco
correto, mesmo que o bloco correto pertenca a uma unidade DIFERENTE do palpite
(colocando a penalidade off-unit de -0.45 em file_map.py:720 efetivamente em
jogo).
"""

import pytest

from src.builder.engine import _select_probable_period_for_entry


def test_real_scorer_assigns_offunit_block_when_date_and_title_are_obvious():
    # Palpite de unidade da ENTRY = unidade-01 (fraco). O bloco CORRETO
    # (bloco-02) esta na unidade-02 -> a penalidade off-unit (-0.45) incide
    # sobre o bloco certo, e o boost on-unit (+0.35 + conf*0.25) favorece o
    # bloco errado (bloco-01). Mesmo assim, a data DD.MM (18.03 -> 18/03/2026)
    # e o titulo distintivo ("Inducao Estrutural") devem vencer.
    weak_unit_guess = {
        "slug": "unidade-01-metodos-formais",
        "title": "Unidade 1 — Métodos Formais",
    }

    blocks = [
        # Bloco da unidade do palpite fraco (ganha +0.35 + 0.95*0.25 de boost),
        # mas conteudo generico e sem casar data/titulo.
        {
            "id": "bloco-01",
            "period_label": "09/03/2026 a 11/03/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "rows": [
                {"index": 1, "date_text": "09/03/2026", "content": "Aula expositiva geral"},
                {"index": 2, "date_text": "11/03/2026", "content": "Aula expositiva geral"},
            ],
        },
        # Bloco CORRETO, mas em unidade DIFERENTE (-0.45 off-unit). Casa a data
        # DD.MM e o titulo distintivo da entry.
        {
            "id": "bloco-02",
            "period_label": "16/03/2026 a 18/03/2026",
            "unit_slug": "unidade-02-verificacao-de-programas",
            "unit_confidence": 0.95,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "rows": [
                {
                    "index": 3,
                    "date_text": "16/03/2026",
                    "content": "Inducao Estrutural sobre conjuntos indutivos",
                },
                {
                    "index": 4,
                    "date_text": "18/03/2026",
                    "content": "Inducao Estrutural sobre conjuntos indutivos",
                },
            ],
        },
    ]

    entry = {
        "title": "Inducao Estrutural sobre conjuntos indutivos",
        "category": "listas",
        "tags": "",
        # prefixo DD.MM (18.03) casa com a row 18/03/2026 do bloco-02 (+0.30)
        "raw_target": "raw/pdfs/listas/18.03 inducao estrutural.pdf",
    }

    period, confidence, ambiguous, reasons = _select_probable_period_for_entry(
        entry=entry,
        unit=weak_unit_guess,
        candidate_rows=blocks,
        markdown_text="# Inducao Estrutural\n\nInducao estrutural sobre conjuntos indutivos",
        preferred_topic_slug="",
    )

    # A claim: apesar do bloco correto ser off-unit (-0.45) e o bloco errado
    # ganhar o boost on-unit, a data/titulo obvios vencem.
    assert period == "16/03/2026 a 18/03/2026", (
        f"esperava bloco-02 (off-unit, mas data/titulo corretos); "
        f"got period={period!r} reasons={reasons}"
    )
    assert confidence > 0.0
