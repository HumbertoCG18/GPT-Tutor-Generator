# Task 1 Report: Guarda de Span Temporal em `_rows_belong_to_same_thematic_block`

## Summary

Successfully implemented a temporal-span guard in the thematic block grouping function to prevent over-merged blocks (e.g., 29-day IA blocks) from merging when the span exceeds 21 days. Implementation follows TDD strictly: failing tests created first, constant added, guard inserted at exact location, tests pass, non-regression suite confirms no breakage.

## What Was Implemented

1. **Constant Added** (`src/builder/timeline/index.py:663`):
   ```python
   MAX_THEMATIC_BLOCK_SPAN_DAYS = 21
   ```
   With full explanatory comment about the conservative 21-day cap, mention of slug-based grouping in degrau 3.

2. **Temporal Guard Inserted** (`src/builder/timeline/index.py:682-686`):
   ```python
   block_start_dt = (current_rows[0].get("date_dt") if current_rows else previous_row.get("date_dt"))
   current_dt = current_row.get("date_dt")
   if block_start_dt and current_dt:
       if (current_dt - block_start_dt).days > MAX_THEMATIC_BLOCK_SPAN_DAYS:
           return False
   ```
   - Placed exactly after `_timeline_row_is_review_or_assessment` check (line 680)
   - Before `block_tokens = set()` (now line 688)
   - Measures span from block start (`current_rows[0]`), not previous row
   - Only applies when BOTH dates exist; skips guard when either is None

3. **Test File Created** (`tests/test_thematic_block_temporal_guard.py`):
   - 4 test cases covering: close dates (merge), far dates (no merge), block-start measurement, missing dates (skip guard)

## TDD Evidence

### Step 1: RED Phase
```bash
$ python -m pytest tests/test_thematic_block_temporal_guard.py -v
ImportError: cannot import name 'MAX_THEMATIC_BLOCK_SPAN_DAYS'
```
✅ Tests fail at import (expected).

### Step 2: GREEN Phase (Constant Added)
Import error now resolved but tests still run with guard not yet in place. After adding the guard:

```bash
$ python -m pytest tests/test_thematic_block_temporal_guard.py -v
tests/test_thematic_block_temporal_guard.py::test_same_theme_close_dates_merges PASSED [ 25%]
tests/test_thematic_block_temporal_guard.py::test_same_theme_span_over_cap_does_not_merge PASSED [ 50%]
tests/test_thematic_block_temporal_guard.py::test_span_measured_from_block_start_not_previous_row PASSED [ 75%]
tests/test_thematic_block_temporal_guard.py::test_missing_date_skips_temporal_guard PASSED [100%]

============================== 4 passed in 1.00s ==============================
```
✅ All 4 new tests PASS.

### Step 3: Non-Regression Suite
```bash
$ python -m pytest tests/test_timeline_kinds.py tests/test_timeline_index_kind.py \
  tests/test_timeline_signals.py tests/test_ddmm_timeline_boost.py -v

============================== 115 passed in 1.17s ==============================
```
✅ All 115 existing timeline tests PASS — guard does not break existing behavior.

### Step 4: Full Suite (4 + 115 = 119 Tests)
```bash
$ python -m pytest tests/test_thematic_block_temporal_guard.py tests/test_timeline_kinds.py \
  tests/test_timeline_index_kind.py tests/test_timeline_signals.py tests/test_ddmm_timeline_boost.py -v

============================== 119 passed in 1.15s ==============================
```
✅ All tests GREEN.

## Self-Review Verification

| Requirement | Status | Evidence |
|---|---|---|
| Constant matches brief verbatim | ✅ | `MAX_THEMATIC_BLOCK_SPAN_DAYS = 21` + full comment |
| Guard matches brief verbatim | ✅ | Lines 682-686 in index.py |
| Guard location correct | ✅ | After review/assessment check, before `block_tokens = set()` |
| 4 new tests pass | ✅ | All 4 pass in 1.00s |
| Non-regression suite passes | ✅ | All 115 timeline tests pass |
| Guard skips when date_dt is None | ✅ | `test_missing_date_skips_temporal_guard` PASSED |
| No inline magic numbers | ✅ | All uses of 21 via constant |
| Function signature unchanged | ✅ | `_rows_belong_to_same_thematic_block(previous_row, current_row, current_rows=None) -> bool` |
| Call-site not changed | ✅ | No changes to any caller |
| Commit message exact match | ✅ | `fix(timeline): cap de span temporal no agrupamento tematico (quebra over-merge)` |

## Files Changed

- `src/builder/timeline/index.py` — constant (1 line) + guard (5 lines) + comment block (5 lines)
- `tests/test_thematic_block_temporal_guard.py` — new test file (48 lines)

## Commit

```
f912116 fix(timeline): cap de span temporal no agrupamento tematico (quebra over-merge)
```

## Concerns

None. Implementation is minimal, well-tested, non-breaking, and ready for degrau 3 (slug-based grouping).
