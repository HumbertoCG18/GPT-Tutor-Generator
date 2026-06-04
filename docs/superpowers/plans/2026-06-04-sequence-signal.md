# Sinal de Sequência (ordinal de aula) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a moderate tie-breaker boost so a material whose name carries a lecture ordinal ("Aula 03") is assigned to the Nth `kind=class` block of the timeline, disambiguating adjacent class blocks that today fall to the "pega o melhor" fallback with low confidence.

**Architecture:** A new pure-function module `src/builder/routing/sequence.py` provides ordinal extraction, class-block numbering, and the boost. The boost is summed inside the existing `score_entry_against_timeline_block` (one integration point, covering both the primary scorer and the fallback). Class ordinals are stamped onto block dicts at the two scoring entry points that hold the full block list. A new threshold constant `SEQUENCE_BOOST=0.20` lives in `thresholds.py`. The eval harness measures the gain.

**Tech Stack:** Python 3, pytest, stdlib `re`. Reuses `normalize_match_text` (NFKD→ascii→lower→`[a-z0-9 ]`→collapse spaces), so all extraction operates on space-separated lowercase tokens.

---

## Key facts (verified — trust these, do not re-investigate)

- `normalize_match_text("Aula 03 - slides")` → `"aula 03 slides"`. `"Aula03.pdf"` → `"aula03 pdf"` (glued, no space). So extraction must tolerate an optional space between marker and digits. Source: `src/builder/text/normalize.py`.
- The signals dict carries `signals["title_text"]` (from `entry["title"]`) and `signals["raw_text"]` (from `entry["raw_target"]`), both already normalized. Source: `src/builder/extraction/entry_signals.py:102,110`.
- `score_entry_against_timeline_block(signals, block, *, normalize_match_text, score_text_against_row, score_card_evidence_against_entry_fn, preferred_unit_slug="", preferred_topic_slug="")` is called by BOTH the primary scorer (`file_map.select_probable_period_for_entry`) and the fallback (`content_taxonomy._best_instructional_block_fallback`). Adding the boost inside it covers both. The date boost is summed at `file_map.py:838` (`score += _score_block_date_match(signals, block)`) — append the sequence boost right after.
- Blocks are plain dicts; `score_entry_against_timeline_block` already mutates them (sets `rows`, `scores`). Stamping `block["class_ordinal"]` follows the same pattern.
- Block `kind` values seen in fixtures: `"class"`, `"holiday"`, `"review"`, `"assessment"`. Only `"class"` counts for lecture ordinals. Source: `tests/fixtures/timeline/sample.v4.json`.
- The two annotate call sites: `file_map.select_probable_period_for_entry` builds `blocks` around `file_map.py:1060-1066`; `content_taxonomy._best_instructional_block_fallback` has `instructional_blocks` guarded at `content_taxonomy.py:818-819`.
- `content_taxonomy` and `entry_signals` have a circular-import history — `_best_instructional_block_fallback` already uses LATE imports (`content_taxonomy.py:822`). Follow that pattern there.

---

## File Structure

- Create `src/builder/routing/sequence.py` — ordinal extraction, class-block numbering, boost. Pure functions, no I/O, no deps beyond `re` + `thresholds`.
- Modify `src/builder/routing/thresholds.py` — add `SEQUENCE_BOOST` to `_Thresholds`.
- Modify `src/builder/routing/file_map.py` — sum the boost inside `score_entry_against_timeline_block`; annotate ordinals in `select_probable_period_for_entry`.
- Modify `src/builder/extraction/content_taxonomy.py` — annotate ordinals in `_best_instructional_block_fallback`.
- Create `tests/test_sequence_signal.py` — unit + integration tests.
- Modify `tests/fixtures/eval/assignments_gold.json` — add ordinal case(s); re-lock baseline.

---

## Task 1: Ordinal extraction

**Files:**
- Create: `src/builder/routing/sequence.py`
- Test: `tests/test_sequence_signal.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_sequence_signal.py`:

```python
from src.builder.routing.sequence import extract_lecture_ordinal


def test_extracts_ordinal_after_aula_marker():
    assert extract_lecture_ordinal("aula 03 slides") == 3


def test_extracts_ordinal_with_single_digit():
    assert extract_lecture_ordinal("aula 3") == 3


def test_extracts_ordinal_after_encontro_marker():
    assert extract_lecture_ordinal("encontro 2 logica") == 2


def test_extracts_ordinal_when_glued_to_marker():
    # "Aula03.pdf" normaliza para "aula03 pdf" (sem espaco)
    assert extract_lecture_ordinal("aula03 pdf") == 3


def test_picks_digit_adjacent_to_marker_not_trailing_year():
    assert extract_lecture_ordinal("aula 03 2024") == 3


def test_returns_none_for_lista_marker():
    assert extract_lecture_ordinal("lista 2 inducao") is None


def test_returns_none_for_prova_marker():
    assert extract_lecture_ordinal("prova 1") is None


def test_returns_none_for_subchapter_pair():
    # "Capitulo 5.12" normaliza para "capitulo 5 12" -> sem marcador de aula
    assert extract_lecture_ordinal("capitulo 5 12 introducao") is None


def test_returns_none_for_bare_year():
    assert extract_lecture_ordinal("slides 2024 revisao") is None


def test_returns_none_for_roman_numeral():
    assert extract_lecture_ordinal("aula iii predicados") is None


def test_returns_none_when_no_ordinal():
    assert extract_lecture_ordinal("slides de logica") is None


def test_returns_none_for_year_glued_to_marker():
    # "aula2024" nao deve casar (mais de 3 digitos colados, sem fronteira)
    assert extract_lecture_ordinal("aula2024 revisao") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_sequence_signal.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.builder.routing.sequence'`

- [ ] **Step 3: Implement `extract_lecture_ordinal`**

Create `src/builder/routing/sequence.py`:

```python
"""Sinal de sequencia: ordinal de aula ("Aula 03") -> bloco da N-esima aula.

Funcoes puras. Operam sobre texto JA normalizado por normalize_match_text
(NFKD->ascii->lower->[a-z0-9 ]->colapsa espacos), entao tokens sao palavras
minusculas separadas por espaco unico. Sem I/O, sem estado.
"""
from __future__ import annotations

import re
from typing import List, Optional

# Marcador de aula seguido (espaco opcional, p/ casar "aula03" colado) de um
# inteiro de ate 3 digitos com fronteira de palavra apos. A fronteira (\b)
# impede casar ano colado ("aula2024" -> 4 digitos, sem fronteira em 3) e exige
# que o numero termine o token. So "aula"/"encontro" disparam — "lista", "prova",
# "capitulo" nao tem marcador e retornam None.
_LECTURE_ORDINAL_RE = re.compile(r"\b(?:aula|encontro)\s*(\d{1,3})\b")


def extract_lecture_ordinal(text: str) -> Optional[int]:
    """Ordinal de aula do texto normalizado, ou None.

    Pega o numero adjacente ao primeiro marcador de aula. "aula 03 2024" -> 3.
    """
    match = _LECTURE_ORDINAL_RE.search(text or "")
    if not match:
        return None
    return int(match.group(1))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_sequence_signal.py -v`
Expected: all 12 tests PASS.

Note on `test_returns_none_for_year_glued_to_marker`: `\b(?:aula|encontro)\s*(\d{1,3})\b` against `"aula2024 revisao"` — `\d{1,3}` matches at most `"202"`, but the following char `"4"` is a word char so `\b` after `"202"` fails; backtracking to `"20"`/`"2"` also fails the trailing `\b` (next char still a digit). No match → None. Verify this actually passes; if the regex engine matches `"202"`, the test will catch it — do NOT loosen the regex to make a year pass.

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/sequence.py tests/test_sequence_signal.py
git commit -m "feat(routing): extract_lecture_ordinal for sequence signal"
```

---

## Task 2: Class-block numbering

**Files:**
- Modify: `src/builder/routing/sequence.py`
- Test: `tests/test_sequence_signal.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_sequence_signal.py`:

```python
from src.builder.routing.sequence import annotate_class_ordinals


def _blocks():
    return [
        {"id": "b1", "kind": "class"},
        {"id": "b2", "kind": "class"},
        {"id": "b3", "kind": "holiday"},
        {"id": "b4", "kind": "review"},
        {"id": "b5", "kind": "class"},
    ]


def test_numbers_only_class_blocks_in_order():
    blocks = annotate_class_ordinals(_blocks())
    by_id = {b["id"]: b["class_ordinal"] for b in blocks}
    assert by_id == {"b1": 1, "b2": 2, "b3": None, "b4": None, "b5": 3}


def test_block_without_kind_gets_none():
    blocks = annotate_class_ordinals([{"id": "x"}])
    assert blocks[0]["class_ordinal"] is None


def test_is_idempotent():
    blocks = _blocks()
    annotate_class_ordinals(blocks)
    annotate_class_ordinals(blocks)
    by_id = {b["id"]: b["class_ordinal"] for b in blocks}
    assert by_id == {"b1": 1, "b2": 2, "b3": None, "b4": None, "b5": 3}


def test_no_class_blocks_all_none():
    blocks = annotate_class_ordinals([{"id": "h", "kind": "holiday"}])
    assert blocks[0]["class_ordinal"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_sequence_signal.py -v`
Expected: FAIL with `ImportError: cannot import name 'annotate_class_ordinals'`

- [ ] **Step 3: Implement `annotate_class_ordinals`**

Append to `src/builder/routing/sequence.py`:

```python
def annotate_class_ordinals(blocks: List[dict]) -> List[dict]:
    """Carimba block["class_ordinal"] = 1,2,3... nos blocos kind=class, na ordem
    em que aparecem em `blocks` (o caller ja entrega ordenado cronologicamente).
    Blocos de outro kind (ou sem kind) recebem class_ordinal=None. Idempotente.
    Muta os dicts in-place (consistente com rows/scores) e retorna a lista.
    """
    counter = 0
    for block in blocks:
        if str(block.get("kind") or "") == "class":
            counter += 1
            block["class_ordinal"] = counter
        else:
            block["class_ordinal"] = None
    return blocks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_sequence_signal.py -v`
Expected: all tests PASS (Task 1 + Task 2).

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/sequence.py tests/test_sequence_signal.py
git commit -m "feat(routing): annotate_class_ordinals numbers kind=class blocks"
```

---

## Task 3: Threshold constant

**Files:**
- Modify: `src/builder/routing/thresholds.py:82-83`
- Test: `tests/test_sequence_signal.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sequence_signal.py`:

```python
from src.builder.routing.thresholds import T


def test_sequence_boost_is_moderate_tiebreaker():
    # Menor que data (0.30) e topico-compativel (0.48): desempata sem sobrepor.
    assert T.SEQUENCE_BOOST == 0.20
    assert T.SEQUENCE_BOOST < 0.30
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sequence_signal.py::test_sequence_boost_is_moderate_tiebreaker -v`
Expected: FAIL with `AttributeError: 'Thresholds' object has no attribute 'SEQUENCE_BOOST'` (or `AttributeError` on `_Thresholds`)

- [ ] **Step 3: Add the constant**

In `src/builder/routing/thresholds.py`, inside the `_Thresholds` dataclass, after the line `MATERIAL_COVERAGE_MIN: float = 0.70` (currently at line 83), add:

```python
    # sinal de sequencia (sequence.score_sequence_match): boost de DESEMPATE
    # quando o ordinal de aula do material casa o class_ordinal do bloco.
    # 0.20 < DATE_STRONG_BOOST(0.30) e < boost de topico(0.48): decide entre
    # blocos de aula adjacentes quando data/topico estao ausentes, sem
    # sobrepor um match forte. Nao rebalanceia thresholds existentes.
    SEQUENCE_BOOST: float = 0.20
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sequence_signal.py::test_sequence_boost_is_moderate_tiebreaker -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/thresholds.py tests/test_sequence_signal.py
git commit -m "feat(routing): SEQUENCE_BOOST=0.20 tie-breaker threshold"
```

---

## Task 4: The boost function

**Files:**
- Modify: `src/builder/routing/sequence.py`
- Test: `tests/test_sequence_signal.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_sequence_signal.py`:

```python
from src.builder.routing.sequence import score_sequence_match


def _signals(title="", raw=""):
    return {"title_text": title, "raw_text": raw}


def test_boost_when_title_ordinal_matches_class_ordinal():
    block = {"class_ordinal": 3}
    assert score_sequence_match(_signals(title="aula 03"), block) == 0.20


def test_boost_uses_raw_when_title_has_no_ordinal():
    block = {"class_ordinal": 2}
    assert score_sequence_match(_signals(title="slides", raw="aula 2"), block) == 0.20


def test_no_boost_when_ordinal_mismatches():
    block = {"class_ordinal": 1}
    assert score_sequence_match(_signals(title="aula 03"), block) == 0.0


def test_no_boost_when_material_has_no_ordinal():
    block = {"class_ordinal": 3}
    assert score_sequence_match(_signals(title="slides de logica"), block) == 0.0


def test_no_boost_when_block_is_not_class():
    block = {"class_ordinal": None}
    assert score_sequence_match(_signals(title="aula 03"), block) == 0.0


def test_no_boost_when_block_missing_ordinal_key():
    assert score_sequence_match(_signals(title="aula 03"), {}) == 0.0


def test_explicit_boost_value_overrides_default():
    block = {"class_ordinal": 3}
    assert score_sequence_match(_signals(title="aula 03"), block, boost=0.5) == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_sequence_signal.py -v`
Expected: FAIL with `ImportError: cannot import name 'score_sequence_match'`

- [ ] **Step 3: Implement `score_sequence_match`**

Append to `src/builder/routing/sequence.py` (the `from .thresholds import T` import goes at the TOP of the file with the other imports):

At the top of `src/builder/routing/sequence.py`, add after `import re`:

```python
from src.builder.routing.thresholds import T
```

Then append:

```python
def score_sequence_match(signals: dict, block: dict, *, boost: float = T.SEQUENCE_BOOST) -> float:
    """Boost de desempate quando o ordinal de aula do material casa o
    class_ordinal do bloco. Extrai do title_text; cai para raw_text. Retorna
    `boost` no match, senao 0.0. Inerte quando o material nao tem ordinal ou o
    bloco nao e de aula (class_ordinal None/ausente).
    """
    ordinal = extract_lecture_ordinal(signals.get("title_text", ""))
    if ordinal is None:
        ordinal = extract_lecture_ordinal(signals.get("raw_text", ""))
    if ordinal is None:
        return 0.0
    class_ordinal = block.get("class_ordinal")
    if class_ordinal is not None and class_ordinal == ordinal:
        return float(boost)
    return 0.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_sequence_signal.py -v`
Expected: all tests PASS.

Note: confirm importing `T` at module top of `sequence.py` does NOT create a circular import (`thresholds.py` imports only `dataclasses` — it does not import `sequence`, so this is safe).

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/sequence.py tests/test_sequence_signal.py
git commit -m "feat(routing): score_sequence_match tie-breaker boost"
```

---

## Task 5: Integrate into the scorer

**Files:**
- Modify: `src/builder/routing/file_map.py` (inside `score_entry_against_timeline_block` ~line 838; inside `select_probable_period_for_entry` ~line 1064)
- Modify: `src/builder/extraction/content_taxonomy.py` (inside `_best_instructional_block_fallback` ~line 819)
- Test: `tests/test_sequence_signal.py`

- [ ] **Step 1: Write the failing integration test**

Append to `tests/test_sequence_signal.py`:

```python
from src.builder.routing.file_map import score_entry_against_timeline_block
from src.builder.routing.sequence import annotate_class_ordinals
from src.builder.extraction.entry_signals import (
    normalize_match_text,
    score_text_against_row,
)
from src.builder.routing.file_map import score_card_evidence_against_entry


def _full_signals(title):
    # Mesmo formato dos signals reais; campos vazios exceto o titulo.
    return {
        "title_text": normalize_match_text(title),
        "markdown_headings_text": "",
        "markdown_lead_text": "",
        "markdown_text": "",
        "category_text": "",
        "manual_tags_text": "",
        "auto_tags_text": "",
        "legacy_tags_text": "",
        "tags_text": "",
        "raw_text": "",
    }


def _class_block(block_id):
    return {
        "id": block_id,
        "kind": "class",
        "rows": [{"content": "aula expositiva geral", "date_text": "", "ignored": False}],
        "unit_slug": "",
        "unit_confidence": 0.0,
        "primary_topic_slug": "",
        "primary_topic_confidence": 0.0,
        "topic_ambiguous": True,
        "topic_candidates": [],
        "topic_text": "",
        "card_evidence": [],
        "sessions": [],
        "period_label": block_id,
        "scores": [0.0],
    }


def _score(signals, block):
    return score_entry_against_timeline_block(
        signals,
        block,
        normalize_match_text=normalize_match_text,
        score_text_against_row=score_text_against_row,
        score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
            s, items, normalize_match_text=normalize_match_text
        ),
    )


def test_scorer_boosts_matching_class_ordinal_block():
    blocks = annotate_class_ordinals([_class_block("b1"), _class_block("b2"), _class_block("b3")])
    signals = _full_signals("Aula 03")
    score_third = _score(signals, blocks[2])   # class_ordinal == 3, matches
    score_first = _score(signals, blocks[0])   # class_ordinal == 1, no match
    assert score_third - score_first == 0.20


def test_scorer_no_sequence_delta_without_ordinal():
    blocks = annotate_class_ordinals([_class_block("b1"), _class_block("b2"), _class_block("b3")])
    signals = _full_signals("Slides de logica")
    score_third = _score(signals, blocks[2])
    score_first = _score(signals, blocks[0])
    assert score_third == score_first
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_sequence_signal.py::test_scorer_boosts_matching_class_ordinal_block -v`
Expected: FAIL — `score_third - score_first == 0.0`, not `0.20` (boost not wired yet).

- [ ] **Step 3: Wire the boost into `score_entry_against_timeline_block`**

In `src/builder/routing/file_map.py`, find this line inside `score_entry_against_timeline_block` (currently line 838):

```python
    score += _score_block_date_match(signals, block)

    return score
```

Replace it with:

```python
    score += _score_block_date_match(signals, block)

    score += score_sequence_match(signals, block)

    return score
```

Then add the import near the top of `src/builder/routing/file_map.py`, with the other imports (find the existing `from src.builder.routing` imports or the module-level import block):

```python
from src.builder.routing.sequence import score_sequence_match
```

If a top-level import causes a circular import at module load (run the test and check), use a late import inside `score_entry_against_timeline_block` instead:

```python
    from src.builder.routing.sequence import score_sequence_match
    score += score_sequence_match(signals, block)
```

- [ ] **Step 4: Annotate ordinals in `select_probable_period_for_entry`**

In `src/builder/routing/file_map.py`, inside `select_probable_period_for_entry`, find where `blocks` is finalized (currently lines 1060-1066):

```python
    if candidate_rows and "rows" in candidate_rows[0]:
        blocks = list(candidate_rows)
    else:
        timeline_index = build_timeline_index(candidate_rows, unit_index=[unit] if unit else [])
        blocks = list(timeline_index.get("blocks", []) or [])
    if not blocks:
        return "", 0.0, True, ["sem-blocos-candidato"]
```

Immediately AFTER the `if not blocks:` guard block (after the `return "", 0.0, True, ["sem-blocos-candidato"]` line), add:

```python
    annotate_class_ordinals(blocks)
```

Add the import near the top of `src/builder/routing/file_map.py` (same import block as Step 3; combine into one import line if you prefer):

```python
from src.builder.routing.sequence import annotate_class_ordinals
```

- [ ] **Step 5: Annotate ordinals in the fallback**

In `src/builder/extraction/content_taxonomy.py`, inside `_best_instructional_block_fallback`, find the guard (currently lines 818-819):

```python
    if not instructional_blocks:
        return None, 0.0
```

Immediately AFTER it, add a LATE import + annotate (late import to respect the circular-import pattern already used in this function):

```python
    from src.builder.routing.sequence import annotate_class_ordinals
    annotate_class_ordinals(instructional_blocks)
```

- [ ] **Step 6: Run the integration tests to verify they pass**

Run: `python -m pytest tests/test_sequence_signal.py -v`
Expected: all tests PASS, including `test_scorer_boosts_matching_class_ordinal_block` (delta == 0.20) and `test_scorer_no_sequence_delta_without_ordinal` (delta == 0.0).

- [ ] **Step 7: Run the full suite to confirm no regressions**

Run: `python -m pytest tests -q`
Expected: 788 prior tests + new sequence tests all PASS. Zero NEW failures. If any pre-existing scoring test now fails, inspect whether the sequence boost changed a previously-asserted score — if so, that test was relying on a material whose name contains a lecture ordinal that now matches a block; report it as DONE_WITH_CONCERNS with the specific test so the controller decides.

- [ ] **Step 8: Commit**

```bash
git add src/builder/routing/file_map.py src/builder/extraction/content_taxonomy.py tests/test_sequence_signal.py
git commit -m "feat(routing): wire sequence boost into block scorer + annotate ordinals"
```

---

## Task 6: Prove the gain in the eval harness

**Files:**
- Modify: `tests/fixtures/eval/assignments_gold.json`

- [ ] **Step 1: Add a timeline block and an ordinal case to the gold set**

The current timeline has `bloco-01` (class, 11-13/03), `bloco-02` (class, 18/03), `bloco-04` (no unit, 01/04). To exercise the sequence signal we need a THIRD class block plus a non-class block in between to prove the skip. In `tests/fixtures/eval/assignments_gold.json`, add these two blocks to the `"timeline"."blocks"` array (after `bloco-04`), preserving accents:

```json
,
      {
        "id": "bloco-03",
        "period_label": "25/03/2026 a 25/03/2026",
        "unit_slug": "",
        "unit_confidence": 0.0,
        "primary_topic_slug": "",
        "primary_topic_confidence": 0.0,
        "topic_ambiguous": true,
        "topic_candidates": [],
        "topic_text": "Feriado",
        "kind": "holiday",
        "administrative_only": false,
        "rows": [
          {"index": 4, "date_text": "25/03/2026", "content": "Feriado"}
        ]
      },
      {
        "id": "bloco-05",
        "period_label": "08/04/2026 a 08/04/2026",
        "unit_slug": "unidade-01-logica",
        "unit_confidence": 0.50,
        "primary_topic_slug": "",
        "primary_topic_confidence": 0.0,
        "topic_ambiguous": true,
        "topic_candidates": [],
        "topic_text": "recursao e relacoes de recorrencia",
        "kind": "class",
        "administrative_only": false,
        "rows": [
          {"index": 6, "date_text": "08/04/2026", "content": "recursao e relacoes de recorrencia"}
        ]
      }
```

Also add `"kind": "class"` to `bloco-01` and `bloco-02`, and `"kind": "review"` to `bloco-04`, if those keys are not already present (the harness blocks did not carry `kind` before; the sequence signal needs them). Edit each of the three existing blocks to include the `kind` key.

After this edit the class blocks in chronological order are: `bloco-01` (1), `bloco-02` (2), `bloco-05` (3). `bloco-03` (holiday) and `bloco-04` (review) are skipped.

Then add this case to the `"cases"` array (after `case-weak`), preserving accents:

```json
,
    {
      "id": "case-ordinal",
      "title": "Aula 03 - slides",
      "raw_target": "raw/pdfs/aula 03 slides.pdf",
      "category": "material-de-aula",
      "tags": "",
      "markdown": "# Aula 03\n\nslides da aula",
      "unit_guess": {"slug": "unidade-01-logica", "confidence": 0.40, "ambiguous": true},
      "expected_block_id": "bloco-05",
      "note": "ordinal 3 -> 3a aula (bloco-05), pulando feriado/revisao; sem data/topico forte"
    }
```

- [ ] **Step 2: Verify the fixture is valid JSON**

Run: `python -c "import json; json.load(open('tests/fixtures/eval/assignments_gold.json', encoding='utf-8')); print('ok')"`
Expected: prints `ok`

- [ ] **Step 3: Run the harness and confirm the ordinal case now lands on bloco-05**

Run: `python scripts/eval_assignments.py`
Expected: the report lists 5 cases; `case-ordinal` is NOT in the "Erros:" section (it correctly maps to bloco-05); orfaos == 0. Capture the full output. Confirm `Acuracia de bloco` is `5/5 (100.0%)`.

If `case-ordinal` lands on a different block (e.g. bloco-01), the sequence wiring from Task 5 is not taking effect in the harness path — STOP and report BLOCKED with the full output and the case's `note`. (The harness calls `resolve_unit_block_tags` → real scorer → `score_entry_against_timeline_block`, which now includes the boost, and the fallback annotates ordinals; both paths are covered.)

- [ ] **Step 4: Re-lock the baseline**

Set `"baseline": {"block_accuracy": X}` in the fixture to the exact fraction measured in Step 3 (5/5 → `1.0`). Use the exact value printed.

Run again to confirm clean: `python scripts/eval_assignments.py; echo "EXIT=$LASTEXITCODE"`
Expected: no `REGRESSAO` line; `EXIT=0`.

- [ ] **Step 5: Run the eval gate + full suite**

Run: `python -m pytest tests/test_eval_assignments.py tests/test_sequence_signal.py -q`
Expected: all PASS.

Run: `python -m pytest tests -q`
Expected: zero NEW failures.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/eval/assignments_gold.json
git commit -m "test(eval): ordinal case proves sequence signal; re-lock baseline"
```

---

## Self-Review

**Spec coverage:**
- Extraction with anti-false-positive rules → Task 1 (aula/encontro only, adjacent digit, glued tolerance, year/subchapter/roman → None). ✓
- Class-block numbering, skip non-class, idempotent → Task 2. ✓
- `SEQUENCE_BOOST=0.20` constant, moderate < date/topic → Task 3. ✓
- Boost function, title→raw source, inert cases → Task 4. ✓
- Integration inside `score_entry_against_timeline_block` (one point, both paths) + annotate at the 2 call sites → Task 5. ✓
- Harness gold case (≥3 class blocks with an interleaved non-class to prove skip), measure, re-lock baseline, regression gate → Task 6. ✓
- Edge cases from spec (Aula 09 out of range, Aula 03 2024, no class blocks, roman, Lista/Prova/Capitulo, two "Aula 03") → covered by Task 1/2/4 unit tests (out-of-range = no block has that ordinal → `score_sequence_match` returns 0 via the mismatch path; two-equal-ordinal materials both get the boost, tie broken by other signals — existing behavior, no new test needed). ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases". Every code step shows full code. The only runtime-derived value (baseline in Task 6 Step 4) has explicit derivation instructions. ✓

**Type consistency:**
- `extract_lecture_ordinal(text) -> Optional[int]` (Task 1) consumed by `score_sequence_match` (Task 4). ✓
- `annotate_class_ordinals(blocks) -> list`, stamps `block["class_ordinal"]: int|None` (Task 2), read by `score_sequence_match` via `block.get("class_ordinal")` (Task 4) and called in Task 5 at both sites. ✓
- `score_sequence_match(signals, block, *, boost=T.SEQUENCE_BOOST) -> float` (Task 4) called as `score_sequence_match(signals, block)` in Task 5 — default boost used. ✓
- `T.SEQUENCE_BOOST` (Task 3) referenced as default in Task 4. Task 3 precedes Task 4. ✓

---

## Open follow-ups (NOT in this plan)

1. Roman-numeral ordinals (`Aula III`).
2. `semana N` mapping (weeks → possibly multiple class blocks).
3. Per-category ordinal mapping (`Lista 02` against list-bearing blocks).
4. Reconcile against professor's explicit lecture numbers when the timeline carries them (today `class_ordinal` follows chronological order, which can diverge if the professor skips numbers).
