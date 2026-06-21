"""TDD — Commit B: surface durável de feature_flags por subject.

- SubjectProfile.feature_flags (dict, default {}); round-trip; ausente → {}.
- _build_options_from_config(subject=...) injeta feature_flags nas options.
- Genérico: injeta o que ESTÁ no dict; não força use_concept_resolver.
- subject=None / sem flags → options base inalteradas (byte-idêntico p/ os 4 sem flag).
"""
from __future__ import annotations

from src.models.core import SubjectProfile
from src.ui.app import _build_options_from_config


def _base_keys():
    return set(_build_options_from_config("auto", "pt", {}).keys())


def test_subject_profile_feature_flags_round_trip():
    sp = SubjectProfile.from_dict({
        "name": "IA", "feature_flags": {"use_anchor_placement": True},
    })
    assert sp.feature_flags == {"use_anchor_placement": True}
    d = sp.to_dict()
    assert d["feature_flags"] == {"use_anchor_placement": True}
    sp2 = SubjectProfile.from_dict(d)
    assert sp2.feature_flags == {"use_anchor_placement": True}


def test_subject_profile_feature_flags_absent_defaults_empty():
    sp = SubjectProfile.from_dict({"name": "X"})
    assert sp.feature_flags == {}


def test_build_options_injects_feature_flags():
    sp = SubjectProfile.from_dict({"name": "IA", "feature_flags": {"use_anchor_placement": True}})
    opts = _build_options_from_config("auto", "pt", {}, subject=sp)
    assert opts.get("use_anchor_placement") is True


def test_build_options_no_subject_is_base_only():
    """subject=None → nenhum flag-key novo (byte-idêntico aos outros 4 repos)."""
    base = _base_keys()
    opts = _build_options_from_config("auto", "pt", {}, subject=None)
    assert set(opts.keys()) == base


def test_build_options_empty_flags_is_base_only():
    sp = SubjectProfile.from_dict({"name": "ES2"})  # sem feature_flags → {}
    opts = _build_options_from_config("auto", "pt", {}, subject=sp)
    assert set(opts.keys()) == _base_keys()


def test_build_options_does_not_force_concept_resolver():
    """Surface genérica: só injeta o que está em feature_flags. IA com apenas
    use_anchor_placement NÃO liga use_concept_resolver."""
    sp = SubjectProfile.from_dict({"name": "IA", "feature_flags": {"use_anchor_placement": True}})
    opts = _build_options_from_config("auto", "pt", {}, subject=sp)
    assert "use_concept_resolver" not in opts
