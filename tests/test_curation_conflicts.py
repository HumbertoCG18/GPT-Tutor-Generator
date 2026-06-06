"""Guard de conflito: override manual de bloco vs auto-atribuicao forte."""

from scripts.validate_timeline import health_report
from src.builder.timeline.conflicts import (
    auto_suggested_unit,
    detect_block_conflicts,
    detect_timeline_conflicts,
)


# --- auto_suggested_unit ---------------------------------------------------

def test_auto_unit_abstains_when_ambiguous():
    block = {"topic_ambiguous": True, "primary_topic_confidence": 1.0,
             "topic_candidates": [{"unit_slug": "unidade-01-x"}]}
    assert auto_suggested_unit(block) == ("", 0.0)


def test_auto_unit_abstains_below_threshold():
    block = {"topic_ambiguous": False, "primary_topic_confidence": 0.5,
             "topic_candidates": [{"unit_slug": "unidade-01-x"}]}
    assert auto_suggested_unit(block) == ("", 0.0)


def test_auto_unit_returns_at_exact_threshold():
    block = {"topic_ambiguous": False, "primary_topic_confidence": 0.65,
             "topic_candidates": [{"unit_slug": "unidade-01-x"}]}
    assert auto_suggested_unit(block) == ("unidade-01-x", 0.65)


def test_auto_unit_abstains_just_below_threshold():
    block = {"topic_ambiguous": False, "primary_topic_confidence": 0.64,
             "topic_candidates": [{"unit_slug": "unidade-01-x"}]}
    assert auto_suggested_unit(block) == ("", 0.0)


def test_auto_unit_returns_top_candidate_when_confident():
    block = {"topic_ambiguous": False, "primary_topic_confidence": 1.0,
             "topic_candidates": [{"unit_slug": "unidade-01-conjuntos"}]}
    assert auto_suggested_unit(block) == ("unidade-01-conjuntos", 1.0)


def test_auto_unit_abstains_without_candidates():
    block = {"topic_ambiguous": False, "primary_topic_confidence": 1.0,
             "topic_candidates": []}
    assert auto_suggested_unit(block) == ("", 0.0)


# --- detect_block_conflicts: unidade ---------------------------------------

def test_unit_conflict_flagged():
    block = {
        "id": "bloco-02",
        "block_manual_unit_slug": "unidade-02-turing-computabilidade",
        "topic_ambiguous": False,
        "primary_topic_confidence": 1.0,
        "topic_candidates": [
            {"unit_slug": "unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas"}
        ],
    }
    conflicts = detect_block_conflicts(block)
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c["field"] == "unit"
    assert c["block_id"] == "bloco-02"
    assert c["manual"] == "unidade-02-turing-computabilidade"
    assert c["auto"] == "unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas"
    assert c["confidence"] == 1.0


def test_unit_no_conflict_when_auto_abstains():
    block = {
        "id": "bloco-10",
        "block_manual_unit_slug": "unidade-03-problemas-indecidiveis",
        "topic_ambiguous": True,
        "primary_topic_confidence": 0.2,
        "topic_candidates": [{"unit_slug": "unidade-02-turing"}],
    }
    assert detect_block_conflicts(block) == []


def test_unit_no_conflict_when_auto_matches_manual():
    block = {
        "id": "bloco-03",
        "block_manual_unit_slug": "unidade-01-conjuntos",
        "topic_ambiguous": False,
        "primary_topic_confidence": 1.0,
        "topic_candidates": [{"unit_slug": "unidade-01-conjuntos"}],
    }
    assert detect_block_conflicts(block) == []


def test_unit_no_conflict_without_manual_override():
    block = {
        "id": "bloco-03",
        "topic_ambiguous": False,
        "primary_topic_confidence": 1.0,
        "topic_candidates": [{"unit_slug": "unidade-01-conjuntos"}],
    }
    assert detect_block_conflicts(block) == []


# --- detect_block_conflicts: kind ------------------------------------------

def test_kind_conflict_flagged_against_source_kind():
    block = {"id": "b1", "manual_kind_override": "holiday",
             "source_kind": "assessment"}
    conflicts = detect_block_conflicts(block)
    assert len(conflicts) == 1
    assert conflicts[0]["field"] == "kind"
    assert conflicts[0]["manual"] == "holiday"
    assert conflicts[0]["auto"] == "assessment"


def test_kind_no_conflict_without_source_kind():
    block = {"id": "bloco-05", "manual_kind_override": "review"}
    assert detect_block_conflicts(block) == []


def test_kind_no_conflict_when_matches_source_kind():
    block = {"id": "b1", "manual_kind_override": "assessment",
             "source_kind": "assessment"}
    assert detect_block_conflicts(block) == []


# --- detect_timeline_conflicts ---------------------------------------------

def test_detect_timeline_conflicts_flattens():
    blocks = [
        {"id": "ok", "topic_ambiguous": True},
        {"id": "bad", "block_manual_unit_slug": "unidade-02-x",
         "topic_ambiguous": False, "primary_topic_confidence": 0.9,
         "topic_candidates": [{"unit_slug": "unidade-01-y"}]},
    ]
    out = detect_timeline_conflicts(blocks)
    assert [c["block_id"] for c in out] == ["bad"]


def test_health_report_includes_override_conflicts():
    blocks = [
        {"id": "bloco-02", "kind": "class",
         "block_manual_unit_slug": "unidade-02-turing",
         "topic_ambiguous": False, "primary_topic_confidence": 1.0,
         "topic_candidates": [{"unit_slug": "unidade-01-conjuntos"}]},
    ]
    rep = health_report(blocks)
    assert "override_conflicts" in rep
    assert len(rep["override_conflicts"]) == 1
    assert rep["override_conflicts"][0]["block_id"] == "bloco-02"


def test_health_report_no_conflicts_empty_list():
    blocks = [{"id": "b", "kind": "class", "unit_slug": "u1",
               "primary_topic_label": "t"}]
    rep = health_report(blocks)
    assert rep["override_conflicts"] == []
