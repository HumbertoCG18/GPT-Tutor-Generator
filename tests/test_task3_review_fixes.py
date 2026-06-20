"""Task 3 review-fix tests.

CRITICAL-1: concept_resolver scorer keys by block_uuid (not bloco-NN id),
            so uuid-keyed votes actually land on their block.
CRITICAL-2: attach_block_summary_fields receives blocks so gemini_primary
            lazy-resolve actually runs.
IMPORTANT-3: migration functions are wired in the rebuild path
             (index.py _build_file_map_timeline_context_from_course).
"""
import json
import pytest


# ---------------------------------------------------------------------------
# CRITICAL-1 — concept_resolver scorer uses block_uuid as bid
# ---------------------------------------------------------------------------

def _make_block(bloco_id: str, uuid: str, concepts: list = None) -> dict:
    return {
        "id": bloco_id,
        "block_uuid": uuid,
        "title": bloco_id,
        "concepts": concepts or [bloco_id],
    }


def _make_llm_curation(uuid: str, score: float = 0.9) -> dict:
    # llm_curation passed to resolve_material_assignment is the summary dict directly
    return {"primary_block_id": uuid, "block_match_confidence": score}


def test_critical1_uuid_vote_lands_on_block():
    """UUID-keyed LLM vote must raise the fused score of the matching block."""
    from src.builder.routing.concept_resolver import resolve_material_assignment

    TARGET_UUID = "uuid-b2"
    blocks = [
        _make_block("bloco-01", "uuid-b1", ["alpha"]),
        _make_block("bloco-02", "uuid-b2", ["beta"]),
        _make_block("bloco-03", "uuid-b3", ["gamma"]),
    ]
    llm_curation = _make_llm_curation(TARGET_UUID)

    entry = {"id": "1", "title": "beta stuff", "file_type": "pdf"}
    result = resolve_material_assignment(
        entry, blocks, [],
        signals={"title_text": "beta stuff"},
        llm_curation=llm_curation,
    )

    assert result["block_id"] == TARGET_UUID, (
        f"Expected {TARGET_UUID} to win via LLM vote, got {result['block_id']!r}. "
        "Scorer is likely keying by bloco-NN instead of block_uuid."
    )


def test_critical1_scorer_bid_uses_block_uuid():
    """Scorer final Assignment must use block_uuid as block_id, not bloco-NN."""
    from src.builder.routing.concept_resolver import resolve_material_assignment

    TARGET_UUID = "uuid-b2"
    blocks = [
        _make_block("bloco-01", "uuid-b1", ["alpha"]),
        _make_block("bloco-02", "uuid-b2", ["beta"]),
    ]
    llm_curation = _make_llm_curation(TARGET_UUID)

    result = resolve_material_assignment(
        {"id": "1", "title": "beta"}, blocks, [],
        signals={"title_text": "beta"},
        llm_curation=llm_curation,
    )
    assert result["block_id"] == TARGET_UUID, (
        f"block_id should be uuid ({TARGET_UUID!r}), got {result['block_id']!r}. "
        "Final Assignment.block_id is returning bloco-NN instead of block_uuid."
    )


# ---------------------------------------------------------------------------
# CRITICAL-2 — attach_block_summary_fields receives blocks arg
# ---------------------------------------------------------------------------

def test_critical2_gemini_primary_resolved_when_blocks_passed():
    """Legacy bloco-NN gemini_primary must resolve to uuid when blocks passed."""
    from src.builder.ops.pedagogical_regeneration import attach_block_summary_fields

    blocks = [
        {"id": "bloco-01", "block_uuid": "uuid-b1"},
        {"id": "bloco-02", "block_uuid": "uuid-b2"},
    ]
    code_curation = {
        "entries": {
            "e1": {
                "summary": {
                    "primary_block_id": "bloco-02",
                    "block_match_confidence": 0.3,
                }
            }
        }
    }
    entries = [{"id": "e1", "file_type": "code", "computed_block_band": "baixa"}]
    result = attach_block_summary_fields(entries, code_curation, blocks=blocks)
    computed = result[0].get("computed_block_id", "")
    assert computed == "uuid-b2", (
        f"Expected uuid-b2 via resolved gemini_primary, got {computed!r}. "
        "blocks arg is likely not being used in the resolve path."
    )


def test_critical2_gemini_primary_no_resolve_without_blocks():
    """Without blocks, gemini_primary bloco-NN should remain as-is (not crash)."""
    from src.builder.ops.pedagogical_regeneration import attach_block_summary_fields

    code_curation = {
        "entries": {
            "e1": {
                "summary": {
                    "primary_block_id": "bloco-02",
                    "block_match_confidence": 0.3,
                }
            }
        }
    }
    entries = [{"id": "e1", "file_type": "code", "computed_block_band": "baixa"}]
    result = attach_block_summary_fields(entries, code_curation)
    computed = result[0].get("computed_block_id", "")
    assert computed == "bloco-02", (
        f"Without blocks, expected bloco-02 passthrough, got {computed!r}."
    )


def test_critical2_regenerate_passes_blocks_to_attach():
    """regenerate_pedagogical_files must pass blocks to attach_block_summary_fields."""
    import inspect, re
    from src.builder.ops import pedagogical_regeneration as pr

    src = inspect.getsource(pr.regenerate_pedagogical_files)
    assert "attach_block_summary_fields" in src
    calls = re.findall(r"attach_block_summary_fields\([^)]+\)", src)
    assert calls, "attach_block_summary_fields not found in regenerate_pedagogical_files"
    for call in calls:
        assert "blocks" in call, (
            f"attach_block_summary_fields called without blocks arg: {call!r}"
        )


# ---------------------------------------------------------------------------
# IMPORTANT-3 — migration wired in rebuild path (via index.py)
# ---------------------------------------------------------------------------

def _make_course_meta(tmp_path, manifest_entries, curation_blocks=None, ledger_entries=None, timeline_blocks=None):
    """Create minimal on-disk course dir and return course_meta dict."""
    from pathlib import Path

    course_dir = tmp_path / "course"
    course_dir.mkdir(exist_ok=True)

    ledger = {
        "version": 1,
        "entries": ledger_entries or [
            {"block_uuid": "uuid-b1", "bloco_id": "bloco-01", "position": 1},
            {"block_uuid": "uuid-b2", "bloco_id": "bloco-02", "position": 2},
        ],
    }
    (course_dir / ".block_identity_ledger.json").write_text(
        json.dumps(ledger), encoding="utf-8"
    )

    tl_blocks = timeline_blocks or [
        {"id": "bloco-01", "title": "B1", "unit_slug": "u1", "kind": "aula"},
        {"id": "bloco-02", "title": "B2", "unit_slug": "u1", "kind": "aula"},
    ]
    timeline_index = {"version": 4, "blocks": tl_blocks}
    (course_dir / ".timeline_index.json").write_text(
        json.dumps(timeline_index), encoding="utf-8"
    )

    manifest = {"entries": manifest_entries}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    raw_curation = {"version": 1, "blocks": curation_blocks or {}}
    (course_dir / ".timeline_curation.json").write_text(
        json.dumps(raw_curation), encoding="utf-8"
    )

    return {"_repo_root": str(tmp_path), "manifest": manifest}


def _call_build_timeline_context(course_meta, subject_profile=None):
    """Call the private function via the engine aliases so injected deps are wired."""
    from src.builder.engine import (
        _build_file_map_timeline_context_from_course as _fn,
    )
    return _fn(course_meta, subject_profile)


def test_important3_migration_runs_on_rebuild(tmp_path):
    """manual_timeline_block_id bloco-NN must be rewritten to uuid after rebuild."""
    course_meta = _make_course_meta(
        tmp_path,
        manifest_entries=[{"id": "e1", "title": "F1", "manual_timeline_block_id": "bloco-02"}],
        curation_blocks={"bloco-02": {"manual_kind_override": "lab"}},
    )

    _call_build_timeline_context(course_meta)

    updated = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    entry = updated["entries"][0]
    val = entry["manual_timeline_block_id"]
    import re as _re
    assert val != "bloco-02" and _re.match(r"[0-9a-f-]{36}", val), (
        f"Expected a real uuid after rebuild migration (not bloco-02), got {val!r}. "
        "migrate_human_truth_block_refs is likely unwired."
    )


def test_important3_curation_key_migrated_on_rebuild(tmp_path):
    """Timeline curation bloco-NN key must be migrated to uuid on rebuild."""
    course_meta = _make_course_meta(
        tmp_path,
        manifest_entries=[{"id": "e1", "title": "F1"}],
        curation_blocks={"bloco-02": {"manual_kind_override": "lab"}},
    )

    _call_build_timeline_context(course_meta)

    raw = json.loads(
        (tmp_path / "course" / ".timeline_curation.json").read_text(encoding="utf-8")
    )
    curation = raw.get("blocks", raw)  # handle both wrapped and flat formats
    assert "bloco-02" not in curation, (
        f"bloco-02 key must be replaced by uuid, still present in {list(curation.keys())}. "
        "Curation key migration is likely unwired."
    )
    import re as _re
    assert any(_re.match(r"[0-9a-f-]{36}", k) for k in curation), (
        f"Expected a uuid key in curation after rebuild, got {list(curation.keys())}."
    )


def test_important3_unresolvable_not_dropped(tmp_path):
    """Unresolvable manual_timeline_block_id must FLAG and preserve original value."""
    # Only bloco-01 exists in ledger — bloco-99 is unresolvable
    course_meta = _make_course_meta(
        tmp_path,
        manifest_entries=[{"id": "e1", "title": "F1", "manual_timeline_block_id": "bloco-99"}],
        ledger_entries=[{"block_uuid": "uuid-b1", "bloco_id": "bloco-01", "position": 1}],
        timeline_blocks=[{"id": "bloco-01", "title": "B1", "unit_slug": "u1", "kind": "aula"}],
    )

    _call_build_timeline_context(course_meta)

    updated = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    entry = updated["entries"][0]
    assert entry["manual_timeline_block_id"] == "bloco-99", (
        f"Unresolvable bloco-99 must be preserved, got {entry['manual_timeline_block_id']!r}. "
        "FLAG rule violated: value was dropped or guessed."
    )
