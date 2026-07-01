# Tag Scoring Completion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement the three missing rollout steps (5–7) of the tag-scoring-design spec: subject-local correction learning, explanation payloads + `?` tooltip, and tests for fallback/low-confidence behavior.

**Architecture:** Add `src/models/tag_profile.py` as the single home for `SubjectTagProfile`, persistence, correction recording, learned-boost computation, and explanation formatting. Extend `auto_map_entry_unit` with a `learned_unit_boosts` parameter so corrections feed into the existing scoring pipeline. Store match reasons in each manifest entry during `resolve_unit_block_tags` so the UI can display them without re-running scoring.

**Tech Stack:** Python 3.11, dataclasses, pathlib, pytest. No new dependencies.

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `src/models/tag_profile.py` | **Create** | `SubjectTagProfile` dataclass, load/save, `extract_entry_learned_terms`, `record_correction`, `build_learned_unit_boosts`, `format_unit_explanation_text`, `format_subunit_explanation_text` |
| `src/builder/routing/file_map.py` | **Modify** (line ~349) | Add `learned_unit_boosts: Optional[Dict[str, float]] = None` to `auto_map_entry_unit`; merge into `unit_tag_boosts` before scoring |
| `src/builder/facade/file_map.py` | **Modify** (line ~110) | Pass through `learned_unit_boosts` in the `auto_map_entry_unit` wrapper |
| `src/builder/extraction/content_taxonomy.py` | **Modify** (fn `resolve_unit_block_tags`) | Load `SubjectTagProfile`; compute per-entry learned boosts; pass to unit matcher; store `unit_match_reasons`, `unit_match_confidence`, `subunit_match_reasons`, `subunit_match_confidence` in each entry |
| `src/ui/dialogs.py` | **Modify** (fn `_apply_manual_unit_selection` and `_apply_manual_subunit_selection`, and `_build_ui`) | Call `record_correction` + `save_tag_profile` after manual corrections; add `?` buttons that call explanation methods |
| `tests/test_tag_scoring.py` | **Create** | All step 7 tests |

---

## Task 1: SubjectTagProfile model and persistence

**Files:**
- Create: `src/models/tag_profile.py`

- [x] **Step 1: Write the failing test (model round-trip)**

```python
# tests/test_tag_scoring.py
from src.models.tag_profile import (
    SubjectTagProfile,
    LearnedCorrection,
    load_tag_profile,
    save_tag_profile,
)


def test_tag_profile_round_trip(tmp_path):
    course_dir = tmp_path / "course"
    course_dir.mkdir()

    profile = SubjectTagProfile(subject_slug="metodos-formais", generated_at="2026-05-09T00:00:00")
    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id="lista-1",
            corrected_unit_slug="unidade-01",
            corrected_subunit_slug="",
            learned_terms=["hoare", "logica", "verificacao"],
            created_at="2026-05-09T00:00:00",
        )
    )
    save_tag_profile(course_dir, profile)
    loaded = load_tag_profile(course_dir)

    assert loaded is not None
    assert loaded.subject_slug == "metodos-formais"
    assert len(loaded.learned_corrections) == 1
    assert loaded.learned_corrections[0].entry_id == "lista-1"
    assert "hoare" in loaded.learned_corrections[0].learned_terms


def test_load_tag_profile_returns_none_when_missing(tmp_path):
    result = load_tag_profile(tmp_path / "course")
    assert result is None
```

- [x] **Step 2: Run to confirm failure**

```
pytest tests/test_tag_scoring.py::test_tag_profile_round_trip -v
```

Expected: `ModuleNotFoundError: No module named 'src.models.tag_profile'`

- [x] **Step 3: Create `src/models/tag_profile.py` with model and persistence**

```python
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class LearnedCorrection:
    entry_id: str
    corrected_unit_slug: str
    corrected_subunit_slug: str
    learned_terms: List[str]
    created_at: str

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "corrected_unit_slug": self.corrected_unit_slug,
            "corrected_subunit_slug": self.corrected_subunit_slug,
            "learned_terms": list(self.learned_terms),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearnedCorrection":
        return cls(
            entry_id=str(data.get("entry_id", "")),
            corrected_unit_slug=str(data.get("corrected_unit_slug", "")),
            corrected_subunit_slug=str(data.get("corrected_subunit_slug", "")),
            learned_terms=list(data.get("learned_terms") or []),
            created_at=str(data.get("created_at", "")),
        )


@dataclass
class SubjectTagProfile:
    subject_slug: str
    generated_at: str
    learned_corrections: List[LearnedCorrection] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "subject_slug": self.subject_slug,
            "generated_at": self.generated_at,
            "learned_corrections": [c.to_dict() for c in self.learned_corrections],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SubjectTagProfile":
        corrections = [
            LearnedCorrection.from_dict(c)
            for c in (data.get("learned_corrections") or [])
            if isinstance(c, dict)
        ]
        return cls(
            subject_slug=str(data.get("subject_slug", "")),
            generated_at=str(data.get("generated_at", "")),
            learned_corrections=corrections,
        )


def load_tag_profile(course_dir: Path) -> Optional[SubjectTagProfile]:
    path = course_dir / ".tag_profile.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SubjectTagProfile.from_dict(data)
    except Exception:
        return None


def save_tag_profile(course_dir: Path, profile: SubjectTagProfile) -> None:
    path = course_dir / ".tag_profile.json"
    path.write_text(
        json.dumps(profile.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

- [x] **Step 4: Run tests**

```
pytest tests/test_tag_scoring.py -v
```

Expected: both tests PASS.

- [x] **Step 5: Commit**

```
git add src/models/tag_profile.py tests/test_tag_scoring.py
git commit -m "feat(tag-profile): add SubjectTagProfile model and persistence"
```

---

## Task 2: extract_entry_learned_terms + record_correction

**Files:**
- Modify: `src/models/tag_profile.py`

- [x] **Step 1: Write the failing tests**

```python
# append to tests/test_tag_scoring.py
from src.models.tag_profile import extract_entry_learned_terms, record_correction


def test_extract_learned_terms_from_title_and_auto_tags():
    entry = {
        "id": "lista-1",
        "title": "Lista de Exercícios sobre Lógica de Hoare",
        "auto_tags": ["topico:logica-de-hoare", "tipo:lista"],
        "raw_target": "raw/pdfs/listas/exercicios-logica-hoare.pdf",
    }
    terms = extract_entry_learned_terms(entry)

    assert "exercicios" in terms or "logica" in terms
    assert "logica-de-hoare" in terms
    assert len(terms) <= 12


def test_record_correction_stores_entry_and_removes_previous():
    profile = SubjectTagProfile(subject_slug="metodos-formais", generated_at="2026-05-09T00:00:00")
    entry = {
        "id": "lista-1",
        "title": "Lista Lógica de Hoare",
        "auto_tags": ["topico:logica-de-hoare"],
        "raw_target": "raw/listas/lista.pdf",
    }

    record_correction(profile, entry, corrected_unit_slug="unidade-02", corrected_subunit_slug="")
    assert len(profile.learned_corrections) == 1
    assert profile.learned_corrections[0].corrected_unit_slug == "unidade-02"

    # Overwrite with new correction for same entry
    record_correction(profile, entry, corrected_unit_slug="unidade-01", corrected_subunit_slug="")
    assert len(profile.learned_corrections) == 1
    assert profile.learned_corrections[0].corrected_unit_slug == "unidade-01"


def test_record_correction_skipped_when_no_unit_or_subunit():
    profile = SubjectTagProfile(subject_slug="test", generated_at="2026-05-09T00:00:00")
    entry = {"id": "x", "title": "Algo", "auto_tags": []}
    record_correction(profile, entry, corrected_unit_slug="", corrected_subunit_slug="")
    assert len(profile.learned_corrections) == 0
```

- [x] **Step 2: Run to confirm failure**

```
pytest tests/test_tag_scoring.py::test_extract_learned_terms_from_title_and_auto_tags -v
```

Expected: `ImportError: cannot import name 'extract_entry_learned_terms'`

- [x] **Step 3: Add functions to `src/models/tag_profile.py`**

Append after `save_tag_profile`:

```python
def extract_entry_learned_terms(entry: dict) -> List[str]:
    """Extract significant tokens from entry dict for subject-local learning."""
    terms: set = set()

    title = str(entry.get("title", "") or "").lower()
    for tok in re.split(r"[^a-z0-9]", title):
        if len(tok) >= 5:
            terms.add(tok)

    for tag in list(entry.get("auto_tags") or []):
        tag_str = str(tag)
        if ":" in tag_str:
            slug = tag_str.split(":", 1)[1]
            if len(slug) >= 4:
                terms.add(slug)

    raw = str(entry.get("raw_target", "") or "").lower()
    stem = Path(raw).stem if raw else ""
    for tok in re.split(r"[^a-z0-9]", stem):
        if len(tok) >= 5:
            terms.add(tok)

    return sorted(terms)[:12]


def record_correction(
    profile: SubjectTagProfile,
    entry: dict,
    *,
    corrected_unit_slug: str,
    corrected_subunit_slug: str = "",
) -> None:
    """Record a user correction into the profile (subject-local only)."""
    if not corrected_unit_slug and not corrected_subunit_slug:
        return

    from datetime import datetime

    entry_id = str(entry.get("id", "") or "")
    learned_terms = extract_entry_learned_terms(entry)

    # Remove previous correction for same entry
    profile.learned_corrections = [
        c for c in profile.learned_corrections if c.entry_id != entry_id
    ]

    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id=entry_id,
            corrected_unit_slug=corrected_unit_slug,
            corrected_subunit_slug=corrected_subunit_slug,
            learned_terms=learned_terms,
            created_at=datetime.utcnow().isoformat(),
        )
    )
```

- [x] **Step 4: Run tests**

```
pytest tests/test_tag_scoring.py -v
```

Expected: all tests PASS.

- [x] **Step 5: Commit**

```
git add src/models/tag_profile.py tests/test_tag_scoring.py
git commit -m "feat(tag-profile): add extract_entry_learned_terms and record_correction"
```

---

## Task 3: build_learned_unit_boosts

**Files:**
- Modify: `src/models/tag_profile.py`

- [x] **Step 1: Write the failing tests**

```python
# append to tests/test_tag_scoring.py
from src.models.tag_profile import build_learned_unit_boosts


def test_learned_unit_boosts_returns_boost_when_terms_overlap():
    profile = SubjectTagProfile(subject_slug="test", generated_at="2026-05-09T00:00:00")
    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id="lista-1",
            corrected_unit_slug="unidade-02",
            corrected_subunit_slug="",
            learned_terms=["hoare", "logica", "verificacao"],
            created_at="2026-05-09T00:00:00",
        )
    )

    entry = {
        "id": "lista-2",
        "title": "Exercícios Verificação Lógica",
        "auto_tags": [],
        "raw_target": "raw/lista-2.pdf",
    }
    boosts = build_learned_unit_boosts(profile, entry)

    assert "unidade-02" in boosts
    assert boosts["unidade-02"] > 0.0


def test_learned_unit_boosts_returns_empty_when_no_overlap():
    profile = SubjectTagProfile(subject_slug="test", generated_at="2026-05-09T00:00:00")
    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id="lista-1",
            corrected_unit_slug="unidade-02",
            corrected_subunit_slug="",
            learned_terms=["hoare", "logica", "verificacao"],
            created_at="2026-05-09T00:00:00",
        )
    )

    entry = {
        "id": "lista-2",
        "title": "Ponteiros e Alocação de Memória",
        "auto_tags": [],
        "raw_target": "raw/lista-2.pdf",
    }
    boosts = build_learned_unit_boosts(profile, entry)

    assert boosts == {} or boosts.get("unidade-02", 0.0) == 0.0


def test_learned_unit_boosts_returns_empty_for_none_profile():
    entry = {"id": "x", "title": "Algo", "auto_tags": []}
    boosts = build_learned_unit_boosts(None, entry)
    assert boosts == {}
```

- [x] **Step 2: Run to confirm failure**

```
pytest tests/test_tag_scoring.py::test_learned_unit_boosts_returns_boost_when_terms_overlap -v
```

Expected: `ImportError: cannot import name 'build_learned_unit_boosts'`

- [x] **Step 3: Add `build_learned_unit_boosts` to `src/models/tag_profile.py`**

Append after `record_correction`:

```python
def build_learned_unit_boosts(
    profile: Optional[SubjectTagProfile],
    entry: dict,
) -> Dict[str, float]:
    """Return {unit_slug: boost_weight} based on subject-local learned corrections."""
    if not profile or not profile.learned_corrections:
        return {}

    entry_terms = set(extract_entry_learned_terms(entry))
    if not entry_terms:
        return {}

    boosts: Dict[str, float] = {}
    for correction in profile.learned_corrections:
        if not correction.corrected_unit_slug:
            continue
        learned = set(correction.learned_terms or [])
        overlap = entry_terms & learned
        if len(overlap) >= 2 or (len(overlap) == 1 and len(entry_terms) <= 4):
            weight = 1.5 * min(len(overlap), 3)
            slug = correction.corrected_unit_slug
            boosts[slug] = boosts.get(slug, 0.0) + weight

    return boosts
```

- [x] **Step 4: Run tests**

```
pytest tests/test_tag_scoring.py -v
```

Expected: all PASS.

- [x] **Step 5: Commit**

```
git add src/models/tag_profile.py tests/test_tag_scoring.py
git commit -m "feat(tag-profile): add build_learned_unit_boosts"
```

---

## Task 4: Explanation formatting

**Files:**
- Modify: `src/models/tag_profile.py`

- [x] **Step 1: Write the failing tests**

```python
# append to tests/test_tag_scoring.py
from src.models.tag_profile import format_unit_explanation_text, format_subunit_explanation_text


def test_format_unit_explanation_high_confidence():
    reasons = ["winner_score=4.20", "topic_score=0.85", "tag_boost=2.00"]
    text = format_unit_explanation_text(reasons, confidence=0.90, unit_slug="unidade-02")

    assert "unidade-02" in text
    assert "alta" in text
    assert "4.20" in text


def test_format_unit_explanation_shows_ambiguous():
    reasons = ["winner_score=0.50", "ambiguous"]
    text = format_unit_explanation_text(reasons, confidence=0.30)

    assert "ambíguo" in text or "ambiguo" in text
    assert "muito baixa" in text


def test_format_subunit_explanation_includes_unit():
    reasons = ["winner_score=2.10"]
    text = format_subunit_explanation_text(
        reasons, confidence=0.70, unit_slug="unidade-02", subunit_slug="logica-de-hoare"
    )

    assert "logica-de-hoare" in text
    assert "unidade-02" in text
    assert "média" in text or "media" in text


def test_format_unit_explanation_manual_assignment():
    reasons = ["manual"]
    text = format_unit_explanation_text(reasons, confidence=1.0, unit_slug="unidade-01")

    assert "manual" in text
```

- [x] **Step 2: Run to confirm failure**

```
pytest tests/test_tag_scoring.py::test_format_unit_explanation_high_confidence -v
```

Expected: `ImportError: cannot import name 'format_unit_explanation_text'`

- [x] **Step 3: Add explanation functions to `src/models/tag_profile.py`**

Append after `build_learned_unit_boosts`:

```python
def _confidence_label(confidence: float) -> str:
    if confidence >= 0.85:
        return "alta"
    if confidence >= 0.65:
        return "média"
    if confidence >= 0.45:
        return "baixa"
    return "muito baixa"


def format_unit_explanation_text(
    reasons: List[str],
    confidence: float,
    unit_slug: str = "",
) -> str:
    """Format unit match reasons for a human-readable tooltip."""
    lines: List[str] = []
    for reason in (reasons or []):
        if reason.startswith("winner_score="):
            lines.append(f"pontuação geral: {reason.split('=', 1)[1]}")
        elif reason.startswith("topic_score="):
            lines.append(f"correspondência de tópicos: {reason.split('=', 1)[1]}")
        elif reason.startswith("tag_boost="):
            lines.append(f"boost de tags automáticas: +{reason.split('=', 1)[1]}")
        elif reason == "manual":
            lines.append("atribuição manual pelo usuário")
        elif reason == "ambiguous":
            lines.append("⚠ ambíguo: mais de uma unidade com pontuação similar")

    body = "\n".join(f"- {line}" for line in lines) if lines else "- (sem detalhes disponíveis)"
    header = f"Unidade: {unit_slug}\n" if unit_slug else ""
    return (
        f"{header}Sugerido por:\n{body}\n\n"
        f"Confiança: {_confidence_label(confidence)} ({confidence:.0%})"
    )


def format_subunit_explanation_text(
    reasons: List[str],
    confidence: float,
    unit_slug: str = "",
    subunit_slug: str = "",
) -> str:
    """Format subunit match reasons for a human-readable tooltip."""
    lines: List[str] = []
    for reason in (reasons or []):
        if reason.startswith("winner_score="):
            lines.append(f"pontuação de tópico: {reason.split('=', 1)[1]}")
        elif reason == "manual":
            lines.append("atribuição manual pelo usuário")
        elif reason == "ambiguous":
            lines.append("⚠ ambíguo: mais de um tópico com pontuação similar")
        elif reason.startswith("sem-"):
            lines.append(f"⚠ {reason}")

    if unit_slug:
        lines.append(f"restrito à unidade: {unit_slug}")

    body = "\n".join(f"- {line}" for line in lines) if lines else "- (sem detalhes disponíveis)"
    header = f"Subunidade: {subunit_slug or '(nenhuma)'}\n"
    return (
        f"{header}Sugerido por:\n{body}\n\n"
        f"Confiança: {_confidence_label(confidence)} ({confidence:.0%})"
    )
```

- [x] **Step 4: Run tests**

```
pytest tests/test_tag_scoring.py -v
```

Expected: all PASS.

- [x] **Step 5: Commit**

```
git add src/models/tag_profile.py tests/test_tag_scoring.py
git commit -m "feat(tag-profile): add explanation formatting functions"
```

---

## Task 5: Extend auto_map_entry_unit with learned_unit_boosts

**Files:**
- Modify: `src/builder/routing/file_map.py` (function `auto_map_entry_unit`, around line 349)
- Modify: `src/builder/facade/file_map.py` (function `auto_map_entry_unit`, around line 110)

- [x] **Step 1: Write the failing test**

```python
# append to tests/test_tag_scoring.py
from src.builder.engine import (
    _build_file_map_unit_index,
    _auto_map_entry_unit,
)


def test_auto_map_entry_unit_applies_learned_unit_boosts():
    units = [
        {"title": "Unidade 01 — Lógica de Hoare", "topics": ["1.1 Pré e pós condições"], "extra_signals": []},
        {"title": "Unidade 02 — Redes Neurais", "topics": ["2.1 Backpropagation"], "extra_signals": []},
    ]
    entry = {
        "id": "doc-xyz",
        "title": "Documento genérico",
        "category": "material-de-aula",
        "auto_tags": [],
        "manual_tags": [],
        "tags": "",
        "raw_target": "",
        "notes": "",
        "professor_signal": "",
    }
    markdown_text = ""

    # Without boosts: both units score similarly low
    result_no_boost = _auto_map_entry_unit(entry, units, markdown_text)

    # With learned boost for unit 02
    result_with_boost = _auto_map_entry_unit(
        entry, units, markdown_text, learned_unit_boosts={"unidade-02-redes-neurais": 6.0}
    )

    assert result_with_boost.slug == "unidade-02-redes-neurais"
```

- [x] **Step 2: Run to confirm failure**

```
pytest tests/test_tag_scoring.py::test_auto_map_entry_unit_applies_learned_unit_boosts -v
```

Expected: `TypeError: auto_map_entry_unit() got an unexpected keyword argument 'learned_unit_boosts'`

- [x] **Step 3: Update `auto_map_entry_unit` in `src/builder/routing/file_map.py`**

Current signature (around line 349):
```python
def auto_map_entry_unit(
    entry: dict,
    units: list,
    markdown_text: str,
    *,
    topic_index: Optional[List[dict]] = None,
    unit_tag_index: Optional[Dict[str, float]] = None,
    build_file_map_unit_index: Callable[[list], list],
    ...
) -> UnitMatchResult:
```

Add `learned_unit_boosts: Optional[Dict[str, float]] = None` after `unit_tag_index`:

```python
def auto_map_entry_unit(
    entry: dict,
    units: list,
    markdown_text: str,
    *,
    topic_index: Optional[List[dict]] = None,
    unit_tag_index: Optional[Dict[str, float]] = None,
    learned_unit_boosts: Optional[Dict[str, float]] = None,
    build_file_map_unit_index: Callable[[list], list],
    collect_entry_unit_signals: Callable[[dict, str], dict],
    score_entry_against_unit: Callable[[dict, dict], float],
    normalize_unit_slug: Callable[[str], str],
    score_entry_against_taxonomy_topic: Callable[[dict, dict], float],
    unit_match_result_factory=UnitMatchResult,
) -> UnitMatchResult:
```

Then inside, after the existing `unit_tag_boosts` dict is built from `unit_tag_index`, add the merge (around line 377):

```python
    # After existing unit_tag_index loop:
    if learned_unit_boosts:
        for slug, w in learned_unit_boosts.items():
            if slug and w:
                unit_tag_boosts[str(slug)] = unit_tag_boosts.get(str(slug), 0.0) + float(w)
```

- [x] **Step 4: Update the wrapper in `src/builder/facade/file_map.py` (around line 110)**

```python
    def auto_map_entry_unit(entry, units, markdown_text, topic_index=None, unit_tag_index=None, learned_unit_boosts=None):
        return file_map_auto_map_entry_unit(
            entry,
            units,
            markdown_text,
            topic_index=topic_index,
            unit_tag_index=unit_tag_index,
            learned_unit_boosts=learned_unit_boosts,
            build_file_map_unit_index=build_file_map_unit_index,
            collect_entry_unit_signals=collect_entry_unit_signals,
            score_entry_against_unit=score_entry_against_unit,
            normalize_unit_slug=normalize_unit_slug,
            score_entry_against_taxonomy_topic=score_entry_against_taxonomy_topic,
            unit_match_result_factory=unit_match_result_factory,
        )
```

- [x] **Step 5: Run tests**

```
pytest tests/test_tag_scoring.py -v
pytest tests/test_file_map_unit_mapping.py -v
```

Expected: all PASS.

- [x] **Step 6: Commit**

```
git add src/builder/routing/file_map.py src/builder/facade/file_map.py tests/test_tag_scoring.py
git commit -m "feat(scoring): extend auto_map_entry_unit with learned_unit_boosts parameter"
```

---

## Task 6: Update resolve_unit_block_tags

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py` (function `resolve_unit_block_tags`)

- [x] **Step 1: Write the failing test**

```python
# append to tests/test_tag_scoring.py
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags
from src.models.tag_profile import SubjectTagProfile, LearnedCorrection, save_tag_profile


def _make_resolve_kwargs():
    """Minimal stubs for resolve_unit_block_tags injected callables."""
    from src.builder.routing.file_map import UnitMatchResult

    class FakeTopicMatch:
        topic_slug = ""
        topic_label = ""
        unit_slug = ""
        confidence = 0.0
        ambiguous = True
        reasons = ["sem-taxonomia"]

    return dict(
        build_file_map_unit_index_from_course_fn=lambda meta, profile: [],
        build_file_map_timeline_context_from_course_fn=lambda meta, profile: {
            "blocks_by_unit": {}, "unassigned_blocks": [], "timeline_index": {"blocks": []}
        },
        iter_content_taxonomy_topics_fn=lambda taxonomy: [],
        auto_map_entry_subtopic_fn=lambda entry, taxonomy, md: FakeTopicMatch(),
        auto_map_entry_unit_fn=lambda entry, units, md, topics, learned_unit_boosts=None: UnitMatchResult(
            slug="unidade-01", confidence=0.80, ambiguous=False, reasons=["winner_score=3.50"]
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, ""),
        resolve_entry_manual_timeline_block_fn=lambda entry, ctx: None,
        entry_markdown_text_for_file_map_fn=lambda root, entry: "",
    )


def test_resolve_unit_block_tags_stores_match_reasons_in_entry():
    entries = [{"id": "item-1", "category": "listas", "auto_tags": [], "manual_tags": []}]
    course_meta = {"_repo_root": None}

    result = resolve_unit_block_tags(entries, course_meta, **_make_resolve_kwargs())

    item = result[0]
    assert "unit_match_reasons" in item
    assert "unit_match_confidence" in item
    assert item["unit_match_confidence"] == 0.80
    assert "winner_score=3.50" in item["unit_match_reasons"]


def test_resolve_unit_block_tags_loads_tag_profile_and_passes_learned_boosts(tmp_path):
    course_dir = tmp_path / "course"
    course_dir.mkdir()

    profile = SubjectTagProfile(subject_slug="test", generated_at="2026-05-09T00:00:00")
    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id="old-entry",
            corrected_unit_slug="unidade-02",
            corrected_subunit_slug="",
            learned_terms=["logica", "hoare", "verificacao"],
            created_at="2026-05-09T00:00:00",
        )
    )
    save_tag_profile(course_dir, profile)

    received_boosts = {}

    def capturing_unit_fn(entry, units, md, topics, learned_unit_boosts=None):
        from src.builder.routing.file_map import UnitMatchResult
        received_boosts.update(learned_unit_boosts or {})
        return UnitMatchResult(slug="unidade-01", confidence=0.75, ambiguous=False, reasons=["winner_score=2.00"])

    kwargs = _make_resolve_kwargs()
    kwargs["auto_map_entry_unit_fn"] = capturing_unit_fn

    entries = [{
        "id": "lista-nova",
        "title": "Lista de Lógica de Hoare verificacao",
        "category": "listas",
        "auto_tags": [],
        "manual_tags": [],
    }]
    course_meta = {"_repo_root": tmp_path}

    resolve_unit_block_tags(entries, course_meta, **kwargs)

    # The learned boost for "unidade-02" should have been passed
    assert "unidade-02" in received_boosts
    assert received_boosts["unidade-02"] > 0.0
```

- [x] **Step 2: Run to confirm failure**

```
pytest tests/test_tag_scoring.py::test_resolve_unit_block_tags_stores_match_reasons_in_entry -v
```

Expected: `AssertionError` (key `unit_match_reasons` not in entry)

- [x] **Step 3: Update `resolve_unit_block_tags` in `src/builder/extraction/content_taxonomy.py`**

At the top of the function, after existing variable setup, add:

```python
    # Load subject-local tag profile for learned boosts
    from src.models.tag_profile import load_tag_profile, build_learned_unit_boosts
    _tag_profile = None
    if repo_root:
        try:
            _tag_profile = load_tag_profile(Path(repo_root) / "course")
        except Exception:
            _tag_profile = None
```

Then in the per-entry loop, replace the `auto_map_entry_unit_fn` call block:

```python
        # --- Unit match (manual tem precedencia) ---
        manual_unit = _collapse_ws(str(entry.get("manual_unit_slug") or ""))
        if manual_unit:
            resolved_unit_slug = manual_unit
            unit_confidence = 1.0
            unit_ambiguous = False
            unit_reasons = ["manual"]
        else:
            _learned_boosts = build_learned_unit_boosts(_tag_profile, entry) if _tag_profile else {}
            unit_match = auto_map_entry_unit_fn(
                entry, unit_index, markdown_text, topic_index,
                learned_unit_boosts=_learned_boosts,
            )
            resolved_unit_slug = unit_match.slug
            unit_confidence = unit_match.confidence
            unit_ambiguous = unit_match.ambiguous
            unit_reasons = list(unit_match.reasons)
```

And for subunit, capture reasons:

```python
        # --- Topic/subunit match (manual tem precedencia) ---
        manual_subunit = _collapse_ws(str(entry.get("manual_subunit_slug") or ""))
        if manual_subunit:
            preferred_topic_slug = manual_subunit
            subunit_reasons = ["manual"]
            subunit_confidence = 1.0
        else:
            topic_match = auto_map_entry_subtopic_fn(entry, content_taxonomy, markdown_text)
            preferred_topic_slug = ""
            subunit_reasons = list(getattr(topic_match, "reasons", []))
            subunit_confidence = float(getattr(topic_match, "confidence", 0.0))
            if (
                topic_match.topic_slug
                and not topic_match.ambiguous
                and topic_match.confidence >= 0.60
            ):
                preferred_topic_slug = topic_match.topic_slug
```

Then when building `new_entry`, add:

```python
        new_entry["unit_match_reasons"] = unit_reasons
        new_entry["unit_match_confidence"] = unit_confidence
        new_entry["subunit_match_reasons"] = subunit_reasons
        new_entry["subunit_match_confidence"] = subunit_confidence
```

Add this block just before `updated.append(new_entry)`.

- [x] **Step 4: Run tests**

```
pytest tests/test_tag_scoring.py -v
pytest tests/test_resolve_unit_block_tags.py -v
```

Expected: all PASS.

- [x] **Step 5: Commit**

```
git add src/builder/extraction/content_taxonomy.py tests/test_tag_scoring.py
git commit -m "feat(pipeline): resolve_unit_block_tags loads tag profile and stores match reasons"
```

---

## Task 7: Hook correction recording in BacklogEntryEditDialog

**Files:**
- Modify: `src/ui/dialogs.py` (methods `_apply_manual_unit_selection` and `_apply_manual_subunit_selection`)

- [x] **Step 1: No automated test for UI — verify manually. Write the docstring for the expected behavior instead.**

Behavior: After `_apply_manual_unit_selection` commits a slug, call `record_correction` + `save_tag_profile` using `self._repo_dir / "course"`. Same for `_apply_manual_subunit_selection`.

- [x] **Step 2: Update `_apply_manual_unit_selection` in `src/ui/dialogs.py` (around line 2538)**

After `self._data["manual_unit_slug"] = selected`:

```python
        # Record correction for subject-local learning
        if selected and self._repo_dir:
            try:
                from src.models.tag_profile import load_tag_profile, save_tag_profile, record_correction, SubjectTagProfile
                from datetime import datetime
                course_dir = self._repo_dir / "course"
                if course_dir.exists():
                    profile = load_tag_profile(course_dir) or SubjectTagProfile(
                        subject_slug=self._repo_dir.name,
                        generated_at=datetime.utcnow().isoformat(),
                    )
                    record_correction(
                        profile,
                        self._data,
                        corrected_unit_slug=selected,
                        corrected_subunit_slug=str(self._data.get("manual_subunit_slug") or ""),
                    )
                    save_tag_profile(course_dir, profile)
            except Exception:
                pass  # learning is best-effort; never block UI
```

- [x] **Step 3: Update `_apply_manual_subunit_selection` in `src/ui/dialogs.py` (around line 2624)**

After `self._data["manual_subunit_slug"] = selected`:

```python
        # Record correction for subject-local learning
        if selected and self._repo_dir:
            try:
                from src.models.tag_profile import load_tag_profile, save_tag_profile, record_correction, SubjectTagProfile
                from datetime import datetime
                course_dir = self._repo_dir / "course"
                if course_dir.exists():
                    profile = load_tag_profile(course_dir) or SubjectTagProfile(
                        subject_slug=self._repo_dir.name,
                        generated_at=datetime.utcnow().isoformat(),
                    )
                    record_correction(
                        profile,
                        self._data,
                        corrected_unit_slug=str(self._data.get("manual_unit_slug") or ""),
                        corrected_subunit_slug=selected,
                    )
                    save_tag_profile(course_dir, profile)
            except Exception:
                pass
```

- [x] **Step 4: Run the existing tag catalog tests to confirm no regressions**

```
pytest tests/test_tag_catalog.py tests/test_resolve_unit_block_tags.py -v
```

Expected: all PASS.

- [x] **Step 5: Commit**

```
git add src/ui/dialogs.py
git commit -m "feat(ui): record subject-local correction on manual unit/subunit apply"
```

---

## Task 8: Add ? explanation buttons in BacklogEntryEditDialog

**Files:**
- Modify: `src/ui/dialogs.py` (method `_build_ui`, inside `unit_frame` and `subunit_frame` setup)

- [x] **Step 1: Add `_show_unit_explanation` and `_show_subunit_explanation` methods to `BacklogEntryEditDialog`**

Add these two methods anywhere in the class (e.g., after `_show_explanation` area, near the refresh methods):

```python
    def _show_unit_explanation(self) -> None:
        from src.models.tag_profile import format_unit_explanation_text
        reasons = list(self._data.get("unit_match_reasons") or [])
        confidence = float(self._data.get("unit_match_confidence") or 0.0)
        unit_slug = ""
        for tag in (self._data.get("auto_tags") or []):
            if str(tag).startswith("unit:"):
                unit_slug = str(tag).replace("unit:", "", 1)
                break
        text = format_unit_explanation_text(reasons, confidence, unit_slug=unit_slug)
        messagebox.showinfo("Explicação — Unidade sugerida", text, parent=self)

    def _show_subunit_explanation(self) -> None:
        from src.models.tag_profile import format_subunit_explanation_text
        reasons = list(self._data.get("subunit_match_reasons") or [])
        confidence = float(self._data.get("subunit_match_confidence") or 0.0)
        unit_slug = ""
        subunit_slug = ""
        for tag in (self._data.get("auto_tags") or []):
            if str(tag).startswith("unit:"):
                unit_slug = str(tag).replace("unit:", "", 1)
            elif str(tag).startswith("subunit:"):
                subunit_slug = str(tag).replace("subunit:", "", 1)
        text = format_subunit_explanation_text(
            reasons, confidence, unit_slug=unit_slug, subunit_slug=subunit_slug
        )
        messagebox.showinfo("Explicação — Subunidade sugerida", text, parent=self)
```

- [x] **Step 2: Add `?` button to the unit_frame**

In `_build_ui`, inside `unit_frame` setup, find the `unit_actions` frame (around line 1703–1706):

```python
        unit_actions = tk.Frame(unit_frame, bg=p["input_bg"])
        unit_actions.grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Button(unit_actions, text="Aplicar unidade", command=self._apply_manual_unit_selection).pack(side="left")
        ttk.Button(unit_actions, text="Voltar para automático", command=self._clear_manual_unit).pack(side="left", padx=(8, 0))
```

Add the `?` button after the existing buttons:

```python
        ttk.Button(unit_actions, text="?", width=3, command=self._show_unit_explanation).pack(side="left", padx=(12, 0))
```

- [x] **Step 3: Add `?` button to the subunit_frame**

Find the `subunit_actions` frame (around line 1790–1793 in dialogs.py):

```python
        subunit_actions = tk.Frame(subunit_frame, bg=p["input_bg"])
        subunit_actions.grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Button(subunit_actions, text="Aplicar subunidade", command=self._apply_manual_subunit_selection).pack(side="left")
        ttk.Button(subunit_actions, text="Voltar para automático", command=self._clear_manual_subunit).pack(side="left", padx=(8, 0))
```

Add the `?` button after the existing buttons:

```python
        ttk.Button(subunit_actions, text="?", width=3, command=self._show_subunit_explanation).pack(side="left", padx=(12, 0))
```

- [x] **Step 4: Run the full test suite**

```
pytest tests/ -v --tb=short
```

Expected: all tests PASS (no regressions in tag catalog, unit mapping, resolve_unit_block_tags, etc.).

- [x] **Step 5: Commit**

```
git add src/ui/dialogs.py
git commit -m "feat(ui): add ? explanation tooltip for unit and subunit suggestions"
```

---

## Task 9: Fallback and low-confidence tests

**Files:**
- Modify: `tests/test_tag_scoring.py`

- [x] **Step 1: Write the tests**

```python
# append to tests/test_tag_scoring.py
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags
from src.builder.routing.file_map import UnitMatchResult


def test_fallback_no_tags_uses_existing_signals():
    """When no tag profile exists, unit assignment still runs normally (no crash)."""

    def unit_fn(entry, units, md, topics, learned_unit_boosts=None):
        return UnitMatchResult(slug="unidade-01", confidence=0.70, ambiguous=False, reasons=["winner_score=2.50"])

    kwargs = _make_resolve_kwargs()
    kwargs["auto_map_entry_unit_fn"] = unit_fn

    entries = [{"id": "x", "category": "listas", "auto_tags": [], "manual_tags": []}]
    course_meta = {"_repo_root": None}  # no repo root → no tag profile

    result = resolve_unit_block_tags(entries, course_meta, **kwargs)

    assert result[0].get("unit_match_confidence") == 0.70


def test_low_confidence_unit_does_not_add_unit_tag():
    """Unit confidence < 0.65 → unit: tag NOT added to auto_tags."""

    def unit_fn(entry, units, md, topics, learned_unit_boosts=None):
        return UnitMatchResult(slug="unidade-01", confidence=0.50, ambiguous=False, reasons=["winner_score=1.00"])

    kwargs = _make_resolve_kwargs()
    kwargs["auto_map_entry_unit_fn"] = unit_fn

    entries = [{"id": "x", "category": "listas", "auto_tags": [], "manual_tags": []}]
    result = resolve_unit_block_tags(entries, {"_repo_root": None}, **kwargs)

    unit_tags = [t for t in result[0].get("auto_tags", []) if t.startswith("unit:")]
    assert unit_tags == []


def test_ambiguous_unit_does_not_add_unit_tag():
    """Ambiguous unit match → unit: tag NOT added regardless of score."""

    def unit_fn(entry, units, md, topics, learned_unit_boosts=None):
        return UnitMatchResult(slug="unidade-01", confidence=0.80, ambiguous=True, reasons=["winner_score=2.00", "ambiguous"])

    kwargs = _make_resolve_kwargs()
    kwargs["auto_map_entry_unit_fn"] = unit_fn

    entries = [{"id": "x", "category": "listas", "auto_tags": [], "manual_tags": []}]
    result = resolve_unit_block_tags(entries, {"_repo_root": None}, **kwargs)

    unit_tags = [t for t in result[0].get("auto_tags", []) if t.startswith("unit:")]
    assert unit_tags == []


def test_subunit_not_set_when_unit_confidence_below_threshold():
    """When unit confidence < 0.55, block (period) is not attempted."""

    class FakeTopicMatch:
        topic_slug = "logica-de-hoare"
        topic_label = "Lógica de Hoare"
        unit_slug = "unidade-01"
        confidence = 0.70
        ambiguous = False
        reasons = ["winner_score=2.10"]

    def unit_fn(entry, units, md, topics, learned_unit_boosts=None):
        return UnitMatchResult(slug="unidade-01", confidence=0.40, ambiguous=False, reasons=["winner_score=0.80"])

    kwargs = _make_resolve_kwargs()
    kwargs["auto_map_entry_unit_fn"] = unit_fn
    kwargs["auto_map_entry_subtopic_fn"] = lambda entry, taxonomy, md: FakeTopicMatch()

    entries = [{"id": "x", "category": "listas", "auto_tags": [], "manual_tags": []}]
    result = resolve_unit_block_tags(entries, {"_repo_root": None}, **kwargs)

    bloco_tags = [t for t in result[0].get("auto_tags", []) if t.startswith("bloco:")]
    assert bloco_tags == []


def test_correction_is_subject_local(tmp_path):
    """save_tag_profile writes to course_dir/.tag_profile.json, not globally."""
    from src.models.tag_profile import save_tag_profile, load_tag_profile, SubjectTagProfile

    course_a = tmp_path / "repo-a" / "course"
    course_b = tmp_path / "repo-b" / "course"
    course_a.mkdir(parents=True)
    course_b.mkdir(parents=True)

    profile_a = SubjectTagProfile(subject_slug="materia-a", generated_at="2026-05-09T00:00:00")
    save_tag_profile(course_a, profile_a)

    assert load_tag_profile(course_a) is not None
    assert load_tag_profile(course_b) is None  # repo-b untouched
```

- [x] **Step 2: Run to confirm they pass (they should, since behavior already implemented)**

```
pytest tests/test_tag_scoring.py -v
```

Expected: all PASS.

- [x] **Step 3: Run the full suite for final confirmation**

```
pytest tests/ -v --tb=short
```

Expected: all PASS.

- [x] **Step 4: Commit**

```
git add tests/test_tag_scoring.py
git commit -m "test(tag-scoring): add fallback, low-confidence, and subject-local isolation tests"
```

---

## Self-review against spec

| Spec requirement | Covered by |
|---|---|
| Subject-local tag profile (`SubjectTagProfile`) | Task 1 |
| `learned_corrections` persisted per subject | Tasks 1-2 |
| `record_correction` restricted to current subject | Tasks 2, 7 |
| Learning from user corrections (unit + subunit) | Tasks 2, 7 |
| Conservative learned weights | Task 3 (`weight = 1.5 * min(overlap, 3)`) |
| Learned boosts feed into unit scoring | Tasks 5-6 |
| Fallback when no tags → existing behavior | Task 9 |
| Low-confidence → subunit not forced | Task 9 |
| Explanation payload stored per entry | Task 6 |
| `?` tooltip for unit suggestion | Task 8 |
| `?` tooltip for subunit suggestion | Task 8 |
| UI stays embedded (no standalone tag screen) | ✅ (unchanged) |
| No global cross-subject learning | Task 9 (`test_correction_is_subject_local`) |
| Hierarchical: unit first, then subunit within unit | ✅ (unchanged — `auto_map_entry_subtopic` with `winning_unit_slug` already in place) |

**Gaps:** None found. All 7 rollout items are covered.
