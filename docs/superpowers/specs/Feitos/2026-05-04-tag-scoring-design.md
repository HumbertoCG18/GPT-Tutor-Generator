# Tag Scoring Redesign

**Status:** Implementado

## Goal

Refactor the tag system so tags become a complementary evidence layer for automatic unit assignment and enable subunit assignment with the same scoring philosophy.

The first implementation should establish a robust base, not a complete rule engine. Tags improve confidence and precision, but they do not replace existing assignment signals.

## Scope

This design covers:

- Automatic tag generation from the course plan, timeline, and material signals.
- A per-subject tag profile.
- Hierarchical scoring: unit first, subunit second.
- Manual correction through the existing review/assignment UI.
- Automatic learning from user corrections, restricted to the current subject.
- A compact `?` tooltip explaining why a unit or subunit was suggested.

This design does not cover:

- Global cross-subject learning.
- A standalone tag-management interface.
- LLM-based tag generation in the initial version.
- A full rules engine with complex boolean conditions.

## Core Decisions

### Tags Are Complementary Evidence

Tags should boost or reduce scoring confidence, not become the only classification mechanism.

Reasoning: the current assignment system already has useful signals. Replacing it with tags would create a fragile new source of truth. Tags are most valuable as structured evidence that makes borderline decisions more reliable.

### Subunit Assignment Is Hierarchical

The pipeline must assign the unit before assigning the subunit.

```text
entry signals
  -> unit scoring with tag evidence
  -> selected unit
  -> subunit scoring within selected unit only
  -> selected subunit
```

Subunit tags must not select a subunit outside the winning unit. If the unit is wrong, the user corrects the unit and the correction feeds subject-local learning.

### Learning Is Subject-Local

Corrections improve only the current subject's tag profile.

Reasoning: academic terms are context-sensitive. A tag such as `pipeline`, `modelo`, `arquitetura`, `processo`, or `teste` can mean different things across disciplines. Global learning risks contaminating unrelated subjects.

### UI Stays Embedded

No standalone tag-management UI should be created for the first version.

The user should correct tags indirectly in the existing review/assignment flow:

- See suggested unit.
- See suggested subunit.
- Hover over a `?` icon for explanation.
- Correct unit/subunit when needed.
- Let the system learn automatically from that correction.

## Data Model

### SubjectTagProfile

A subject-local profile derived automatically and enriched over time.

Conceptual fields:

```text
subject_id
source_version
generated_at
unit_tags
subunit_tags
aliases
learned_corrections
```

`unit_tags` map normalized tags or phrases to unit-level evidence.

```text
tag: "devops"
unit_id: "unidade-02"
weight: 3
source: "course_plan"
```

`subunit_tags` map normalized tags or phrases to subunit-level evidence inside a unit.

```text
tag: "ci-cd"
unit_id: "unidade-02"
subunit_id: "integracao-continua"
weight: 3
source: "course_plan"
```

`aliases` normalize equivalent terms.

```text
"github actions" -> "ci-cd"
"pipeline" -> "ci-cd"
```

`learned_corrections` preserve auditability.

```text
entry_id
corrected_unit_id
corrected_subunit_id
learned_terms
created_at
```

The concrete storage format should follow existing project persistence conventions once implementation starts.

## Tag Sources

### Course-Derived Tags

Generate from the course plan and timeline:

- Unit titles.
- Topic names.
- Timeline row themes.
- Known aliases derived from normalized phrase variants.

### Material-Derived Tags

Extract from each material using deterministic, testable signals:

- Entry title.
- File name.
- Headings.
- Existing metadata.
- Frequent or high-signal terms from extracted text.

The initial version should avoid LLM-generated tags. Deterministic tags are easier to test, explain, and debug.

### Learned Tags

When the user corrects a unit or subunit, the system should automatically learn moderate-weight evidence for similar future entries in the same subject.

Learning should use conservative weights so one correction influences matching cases but does not dominate all future scoring.

## Scoring Flow

### Unit Scoring

Inputs:

- Existing assignment signals.
- Material-derived tags.
- Course-derived tags.
- Learned subject-local corrections.

Output:

```text
unit_id
score
confidence
evidence[]
```

Tag evidence can add boosts or penalties, but the score should remain comparable with current scoring.

### Subunit Scoring

Inputs:

- Winning unit.
- Subunit candidates for that unit.
- Material-derived tags.
- Course-derived subunit tags.
- Learned corrections for that subject and unit.

Output:

```text
subunit_id
score
confidence
evidence[]
```

If subunit confidence is low, the system may leave the subunit unset or mark it as uncertain while keeping the unit assignment.

## User Correction Flow

```text
suggested unit/subunit shown in review UI
  -> user corrects unit and/or subunit
  -> system records correction event
  -> system extracts candidate learned terms from entry signals
  -> system updates SubjectTagProfile for this subject only
  -> future scoring uses the learned evidence
```

Corrections should be automatic, but not invisible. The explanation layer must be able to show when a suggestion used learned evidence.

## Explanation UI

Add a compact `?` icon next to suggested unit and suggested subunit.

Tooltip content should be short and user-facing:

```text
Sugerido por:
- tag "ci-cd" (+3)
- termo "pipeline" no titulo (+2)
- cronograma: "Integracao Continua" (+2)

Confianca: alta
```

For subunits:

```text
Sugerido por:
- tag "ci-cd" (+3)
- tag "automacao" (+2)
- restrito a Unidade 02 - DevOps

Confianca: media
```

The tooltip should not expose raw debug logs.

## Error Handling

- If no reliable tags are generated, fall back to the current assignment behavior.
- If unit confidence is low, subunit scoring should not force a precise subunit.
- If the user corrects only the unit, learned evidence should target unit assignment and avoid inventing a subunit.
- If the user corrects only the subunit, learned evidence should be scoped to the current unit.
- If learned tags conflict with course-derived tags, both should appear in evidence and scoring should reflect source weights.

## Testing Strategy

Add or update tests around:

- Tag catalog/profile generation from course plan and timeline data.
- Deterministic material tag extraction.
- Unit scoring with tag boosts.
- Subunit scoring constrained to the selected unit.
- Manual correction learning restricted to the current subject.
- Explanation evidence formatting for UI tooltip consumption.
- Fallback behavior when tags are missing or low-confidence.

Relevant existing test areas from the brief:

- `tests/test_tag_catalog.py`
- `tests/test_unit_fallback.py`
- `tests/test_timeline_signals.py`
- `tests/test_timeline_scoring_ignored.py`
- `tests/test_timeline_index_kind.py`

## Rollout Plan

Implement in increments:

1. Add subject-local tag profile generation from course/timeline data.
2. Add material tag extraction.
3. Integrate tag boosts into unit scoring.
4. Add subunit scoring constrained to the winning unit.
5. Add correction-event learning for the current subject.
6. Add explanation payloads and `?` tooltip display.
7. Add tests for fallback and low-confidence behavior.

## Success Criteria

- Unit assignment remains compatible with current behavior when no tags are available.
- Tags improve unit confidence without overriding strong existing evidence incorrectly.
- Subunit assignment is available only within the selected unit.
- User corrections automatically improve future suggestions for the same subject.
- No global tag learning occurs.
- The UI does not introduce a standalone tag-management screen.
- Users can inspect a concise explanation through a `?` tooltip.
