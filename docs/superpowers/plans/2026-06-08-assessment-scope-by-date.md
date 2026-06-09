# Assessment Scope by Date + SARC Colors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give exams a content scope derived from the cronograma: regular exams (P1..PN) scope = the units taught in their date window (previous exam → this one); PS/G2 = whole semester; revision inherits the next exam's scope. Fix SARC colors so PS/G2 classify as exams.

**Architecture:** Pure helpers in `index.py` compute scope from the serialized timeline blocks (each has `kind`, `period_start`, `unit_slug`); the result is attached as `scope_unit_slugs` on assessment/review blocks during `_serialize_timeline_index`. SARC color parsing in `helpers.py` is corrected to promote PS/G2 to ASSESSMENT and route "Devolução" to results. Teaching-plan declared scope (existing) still takes precedence.

**Tech Stack:** Python 3.8+, BeautifulSoup (SARC HTML), existing timeline module (`src/builder/timeline/index.py`, `classifier.py`, `kinds.py`), `src/utils/helpers.py`.

---

## File Structure

- **Modify** `src/utils/helpers.py` — SARC color map + `_aspnet_row_canonical_kind` (PS/G2/devolução).
- **Modify** `src/builder/timeline/index.py` — `_canonical_assessment_label` (PS/G2); new pure `assessment_scope_by_date` + `_assessment_block_label` + `_link_review_scope`; attach scope in `_serialize_timeline_index`.
- **Tests** `tests/test_core.py` (timeline helpers live there per existing tests) and `tests/test_moodle.py` is unrelated — use `tests/test_core.py`.

---

## Task 1: SARC colors — promote PS/G2, route Devolução

**Files:**
- Modify: `src/utils/helpers.py` (`_ASPNET_COLOR_KIND_MAP` ~line 364; `_aspnet_row_canonical_kind` ~line 411)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def _sarc_row(html):
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "html.parser").find("tr")

def test_sarc_ps_is_assessment_not_ignored():
    from src.utils.helpers import _aspnet_row_canonical_kind
    row = _sarc_row('<tr style="background-color:#ff8c00"><td><span id="x_lblAtividade">Prova PS</span></td></tr>')
    kind, ignored = _aspnet_row_canonical_kind(row)
    assert kind == "assessment" and ignored is False

def test_sarc_g2_lightgrey_is_assessment():
    from src.utils.helpers import _aspnet_row_canonical_kind
    row = _sarc_row('<tr style="background-color:lightgrey"><td><span id="x_lblAtividade">Prova G2</span></td></tr>')
    kind, ignored = _aspnet_row_canonical_kind(row)
    assert kind == "assessment" and ignored is False

def test_sarc_lightgrey_devolucao_is_results():
    from src.utils.helpers import _aspnet_row_canonical_kind
    row = _sarc_row('<tr style="background-color:lightgrey"><td><span id="x_lblAtividade">Devolução de provas</span></td></tr>')
    kind, ignored = _aspnet_row_canonical_kind(row)
    assert kind == "results" and ignored is True

def test_sarc_regular_exam_orange_assessment():
    from src.utils.helpers import _aspnet_row_canonical_kind
    row = _sarc_row('<tr style="background-color:#ffa500"><td><span id="x_lblAtividade">Prova P1</span></td></tr>')
    kind, ignored = _aspnet_row_canonical_kind(row)
    assert kind == "assessment" and ignored is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py -q -k "sarc_ps or sarc_g2 or sarc_lightgrey or sarc_regular_exam"`
Expected: FAIL (PS→"ps"/ignored True; G2→"g2"/ignored True)

- [ ] **Step 3: Implement**

MINIMAL change — do NOT rename existing `suspension`/`event` tokens (tests depend on them). Only promote PS/G2 and route devolução. In `src/utils/helpers.py`, change exactly two entries of `_ASPNET_COLOR_KIND_MAP`:

- `#ff8c00` / `darkorange` (PS): from `("ps", True)` → `("assessment", False)`.
- `lightgrey` / `#d3d3d3` (G2 vs devolução): from `("g2", True)` → `("g2_or_results", False)` (sentinel resolved by Atividade).

Resulting map:

```python
_ASPNET_COLOR_KIND_MAP = {
    "red": ("suspension", True),
    "#ff0000": ("suspension", True),
    "lightgrey": ("g2_or_results", False),
    "#d3d3d3": ("g2_or_results", False),
    "#ffa500": ("assessment", False),
    "orange": ("assessment", False),
    "#ff8c00": ("assessment", False),
    "darkorange": ("assessment", False),
    "#8b0000": ("event", True),
    "darkred": ("event", True),
    "#ffff00": ("deliverable", False),
    "yellow": ("deliverable", False),
}
```

Then handle the `g2_or_results` sentinel in `_aspnet_row_canonical_kind`. Insert the sentinel resolution at the TOP of the function body (right after `color_kind, ignored = _aspnet_row_kind(row)`), before the existing `if ignored:` line:

```python
    color_kind, ignored = _aspnet_row_kind(row)
    atividade = norm_ascii_lower(_aspnet_row_cell(row, "Atividade"))
    if color_kind == "g2_or_results":
        # LightGrey = G2 (avaliação) OU devolução de provas. Atividade decide.
        return ("results", False) if "devolu" in atividade else ("assessment", False)
```

Keep the rest of the function unchanged (it already reads `atividade` again below — that's fine; or reuse this one). The existing final fallbacks (`if ignored:` / ATIVIDADE map / `("class", False)`) stay. `suspension`/`event` remain ignored exactly as before. `"ps"`/`"g2"` tokens are simply no longer emitted (the `_IGNORED_KINDS` leftovers in index.py are harmless dead entries — do NOT touch them).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core.py -q -k "sarc_ps or sarc_g2 or sarc_lightgrey or sarc_regular_exam"`
Expected: 4 passed

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -q`
Expected: all passed. `suspension`/`event` tokens are unchanged, so the existing `test_sarc_kind_flow.py` / `test_timeline_index_kind.py` assertions still hold. Only PS/G2/devolução behavior changed.

- [ ] **Step 6: Commit**

```bash
git add src/utils/helpers.py tests/test_core.py
git commit -m "feat(sarc): promote PS/G2 to assessment, route Devolução to results"
```

---

## Task 2: Canonical assessment label recognizes PS/G2

**Files:**
- Modify: `src/builder/timeline/index.py` (`_canonical_assessment_label` ~line 1022)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_canonical_assessment_label_ps_g2():
    from src.builder.timeline.index import _canonical_assessment_label
    from src.builder.text.normalize import normalize_match_text
    f = lambda s: _canonical_assessment_label(s, normalize_match_text=normalize_match_text)
    assert f("Prova PS") == "PS"
    assert f("Prova G2") == "G2"
    assert f("P2") == "P2"
    assert f("Prova final") == "PF"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py -q -k canonical_assessment_label_ps_g2`
Expected: FAIL ("Prova PS"→"PROVA PS", not "PS")

- [ ] **Step 3: Implement**

In `_canonical_assessment_label`, add PS/G2 recognition before the generic `prova`/upper fallthrough. After the `if normalized in {"pf", ...}: return "PF"` block, add:

```python
    if re.search(r"\bps\b", normalized):
        return "PS"
    if re.search(r"\bg2\b", normalized):
        return "G2"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core.py -q -k canonical_assessment_label_ps_g2`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py tests/test_core.py
git commit -m "feat(timeline): canonical label recognizes PS/G2"
```

---

## Task 3: assessment_scope_by_date (pure)

**Files:**
- Modify: `src/builder/timeline/index.py` (add helpers near the other assessment helpers, e.g. after `_assessment_scope_unit_slugs` ~line 1208)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_assessment_scope_by_date_windows_and_full():
    from src.builder.timeline.index import assessment_scope_by_date
    blocks = [
        {"id": "b1", "kind": "class", "period_start": "2026-03-02", "unit_slug": "unidade-1", "topic_text": "Lógica"},
        {"id": "b2", "kind": "class", "period_start": "2026-03-30", "unit_slug": "unidade-2", "topic_text": "Indução"},
        {"id": "p1", "kind": "assessment", "period_start": "2026-04-02", "topic_text": "Prova P1"},
        {"id": "b3", "kind": "class", "period_start": "2026-05-04", "unit_slug": "unidade-3", "topic_text": "Hoare"},
        {"id": "p2", "kind": "assessment", "period_start": "2026-07-06", "topic_text": "Prova P2"},
        {"id": "ps", "kind": "assessment", "period_start": "2026-07-08", "topic_text": "Prova PS"},
        {"id": "g2", "kind": "assessment", "period_start": "2026-07-15", "topic_text": "Prova G2"},
    ]
    scope = assessment_scope_by_date(blocks)
    assert scope["p1"] == ["unidade-1", "unidade-2"]          # antes da P1
    assert scope["p2"] == ["unidade-3"]                       # entre P1 e P2
    assert scope["ps"] == ["unidade-1", "unidade-2", "unidade-3"]   # semestre inteiro
    assert scope["g2"] == ["unidade-1", "unidade-2", "unidade-3"]   # semestre inteiro
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py -q -k assessment_scope_by_date_windows`
Expected: FAIL (`ImportError: cannot import name 'assessment_scope_by_date'`)

- [ ] **Step 3: Implement**

Add to `src/builder/timeline/index.py`:

```python
def _assessment_block_label(block: Dict[str, object]) -> str:
    """Rótulo canônico (P1/P2/PS/G2/PF/EXAME) a partir do texto do bloco, ou ""."""
    text = " ".join(
        str(block.get(k, "") or "")
        for k in ("topic_text", "primary_topic_label", "period_label")
    )
    for sess in block.get("sessions", []) or []:
        if isinstance(sess, dict):
            text += " " + str(sess.get("label", "") or "")
    if not _normalize_match_text(text):
        return ""
    return _canonical_assessment_label(text, normalize_match_text=_normalize_match_text)


_FULL_SCOPE_LABELS = {"PS", "G2", "PF", "EXAME"}


def assessment_scope_by_date(blocks: List[Dict[str, object]]) -> Dict[str, List[str]]:
    """Escopo de unidades por prova, derivado das datas dos blocos.

    Prova regular (Pk): unidades das aulas (CLASS) na janela (data P(k-1), data Pk].
    PS/G2/PF/EXAME: semestre inteiro (todas as unidades vistas em aulas).
    Retorna {block_id: [unit_slug]} (ordem de aparição). Provas sem data: ignoradas.
    """
    class_units_dated = []
    all_units: List[str] = []
    for b in blocks:
        if str(b.get("kind") or "") != BlockKind.CLASS.value:
            continue
        slug = str(b.get("unit_slug") or "").strip()
        dt = _parse_timeline_date_value(str(b.get("period_start") or ""))
        if slug and slug not in all_units:
            all_units.append(slug)
        if slug and dt:
            class_units_dated.append((dt, slug))

    exams = []
    for b in blocks:
        if str(b.get("kind") or "") != BlockKind.ASSESSMENT.value:
            continue
        dt = _parse_timeline_date_value(str(b.get("period_start") or ""))
        if not dt:
            continue
        exams.append({"id": str(b.get("id") or ""), "dt": dt, "label": _assessment_block_label(b)})

    regular = sorted(
        [e for e in exams if e["label"] not in _FULL_SCOPE_LABELS],
        key=lambda e: e["dt"],
    )
    out: Dict[str, List[str]] = {}
    prev_dt = None
    for e in regular:
        units = []
        for dt, slug in class_units_dated:
            if (prev_dt is None or dt > prev_dt) and dt <= e["dt"]:
                if slug not in units:
                    units.append(slug)
        out[e["id"]] = units
        prev_dt = e["dt"]

    for e in exams:
        if e["label"] in _FULL_SCOPE_LABELS:
            out[e["id"]] = list(all_units)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core.py -q -k assessment_scope_by_date_windows`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py tests/test_core.py
git commit -m "feat(timeline): assessment_scope_by_date (window + full-semester)"
```

---

## Task 4: Revision inherits the next exam's scope

**Files:**
- Modify: `src/builder/timeline/index.py` (add `_link_review_scope` near `assessment_scope_by_date`)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_link_review_scope_inherits_next_exam():
    from src.builder.timeline.index import link_review_scope
    blocks = [
        {"id": "rev", "kind": "review", "period_start": "2026-07-01"},
        {"id": "p2", "kind": "assessment", "period_start": "2026-07-06", "topic_text": "Prova P2"},
    ]
    scope = {"p2": ["unidade-3"]}
    out = link_review_scope(blocks, scope)
    assert out["rev"] == ["unidade-3"]       # revisão herda a próxima prova (P2)

def test_link_review_scope_no_next_exam_empty():
    from src.builder.timeline.index import link_review_scope
    blocks = [{"id": "rev", "kind": "review", "period_start": "2026-07-20"},
              {"id": "p2", "kind": "assessment", "period_start": "2026-07-06"}]
    out = link_review_scope(blocks, {"p2": ["u3"]})
    assert out.get("rev", []) == []          # nenhuma prova depois -> vazio
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py -q -k link_review_scope`
Expected: FAIL (`ImportError: cannot import name 'link_review_scope'`)

- [ ] **Step 3: Implement**

Add to `src/builder/timeline/index.py`:

```python
def link_review_scope(blocks: List[Dict[str, object]], exam_scope: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Cada bloco REVIEW herda o escopo da PRÓXIMA prova (ASSESSMENT) por data.

    Retorna {review_block_id: [unit_slug]} (vazio se não houver prova depois)."""
    dated = []
    for b in blocks:
        dt = _parse_timeline_date_value(str(b.get("period_start") or ""))
        dated.append((dt, b))
    out: Dict[str, List[str]] = {}
    for dt, b in dated:
        if str(b.get("kind") or "") != BlockKind.REVIEW.value or not dt:
            continue
        nxt = None
        for odt, ob in dated:
            if (str(ob.get("kind") or "") == BlockKind.ASSESSMENT.value
                    and odt and odt >= dt):
                if nxt is None or odt < nxt[0]:
                    nxt = (odt, ob)
        out[str(b.get("id") or "")] = list(exam_scope.get(str(nxt[1].get("id")), [])) if nxt else []
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core.py -q -k link_review_scope`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py tests/test_core.py
git commit -m "feat(timeline): review inherits next exam scope"
```

---

## Task 5: Attach scope in _serialize_timeline_index (fallback to declared)

**Files:**
- Modify: `src/builder/timeline/index.py` (`_serialize_timeline_index` ~line 890-941)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_serialize_attaches_scope_unit_slugs():
    from src.builder.timeline.index import _serialize_timeline_index
    ti = {"blocks": [
        {"id": "b1", "kind": "class", "period_start": "2026-03-02", "unit_slug": "unidade-1", "topic_text": "Lógica", "rows": []},
        {"id": "p1", "kind": "assessment", "period_start": "2026-04-02", "topic_text": "Prova P1", "rows": []},
        {"id": "rev", "kind": "review", "period_start": "2026-04-01", "topic_text": "Exercícios de revisão", "rows": []},
    ]}
    out = _serialize_timeline_index(ti)
    by_id = {b["id"]: b for b in out["blocks"]}
    assert by_id["p1"]["scope_unit_slugs"] == ["unidade-1"]
    assert by_id["rev"]["scope_unit_slugs"] == ["unidade-1"]   # herda P1
    assert "scope_unit_slugs" not in by_id["b1"] or by_id["b1"]["scope_unit_slugs"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py -q -k serialize_attaches_scope`
Expected: FAIL (`KeyError: 'scope_unit_slugs'`)

- [ ] **Step 3: Implement**

In `_serialize_timeline_index`, after the `blocks.append(payload)` loop completes and before `return {"version": ..., "blocks": blocks}`, insert a scope pass:

```python
    # Escopo de prova por data (fallback) + revisão herda a próxima prova.
    exam_scope = assessment_scope_by_date(blocks)
    review_scope = link_review_scope(blocks, exam_scope)
    for b in blocks:
        bid = b.get("id")
        scope = None
        if b.get("kind") == BlockKind.ASSESSMENT.value:
            # Precedência: unidades declaradas no plano (se já vieram do matcher) vencem.
            declared = b.get("scope_unit_slugs")
            scope = declared if declared else exam_scope.get(bid, [])
        elif b.get("kind") == BlockKind.REVIEW.value:
            scope = review_scope.get(bid, [])
        if scope is not None:
            b["scope_unit_slugs"] = list(scope)
            if scope and not b.get("primary_topic_label"):
                b["primary_topic_label"] = "Conteúdo: " + ", ".join(scope)
    return {"version": TIMELINE_INDEX_VERSION, "blocks": blocks}
```

(The existing `return` line at the end of the function is replaced by the block above.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core.py -q -k serialize_attaches_scope`
Expected: 1 passed

- [ ] **Step 5: Full suite**

Run: `python -m pytest -q`
Expected: all passed.

- [ ] **Step 6: Commit**

```bash
git add src/builder/timeline/index.py tests/test_core.py
git commit -m "feat(timeline): attach scope_unit_slugs to exams/review on serialize"
```

---

## Task 6: Full suite + spec status

- [ ] **Step 1: Run the whole suite**

Run: `python -m pytest -q`
Expected: all passed (baseline 1083 + new timeline tests).

- [ ] **Step 2: Mark spec implemented**

In `docs/superpowers/specs/2026-06-08-assessment-scope-by-date-design.md`, set `status:` to `implementado`.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-06-08-assessment-scope-by-date-design.md
git commit -m "docs(timeline): mark assessment-scope spec implemented"
```

---

## Self-Review (completed by plan author)

**Spec coverage:** SARC colors PS/G2/devolução → Task 1. PS/G2 canonical label → Task 2. Date-window + full-semester scope → Task 3. Revision inherits next exam → Task 4. Attach scope + declared-units precedence → Task 5. Classification (kind=assessment for PS/G2) → Task 1 (color promotion) + existing classifier ("prova"/regex). `finalize_block` already clears units for non-CLASS (no task needed).

**Placeholder scan:** none — full code in every code step. Task 1 inserts the sentinel resolution at the top of `_aspnet_row_canonical_kind` and leaves the rest of the function intact (the read of that function was truncated mid-body; the engineer keeps the existing fallbacks below the insertion).

**Type consistency:** `assessment_scope_by_date(blocks) -> {id:[slug]}`, `link_review_scope(blocks, exam_scope) -> {id:[slug]}`, `_assessment_block_label(block)`, `_canonical_assessment_label(text, normalize_match_text=...)`, `scope_unit_slugs` payload key, BlockKind.value comparisons — consistent across tasks.

**Non-breaking confirmed:** Task 1 keeps `suspension`/`event` tokens (2 existing tests depend on them) and only changes PS (`#ff8c00`→assessment), G2/devolução (`lightgrey`→sentinel), so no token-rename fallout. `_IGNORED_KINDS` in index.py keeps its dead `ps`/`g2` entries untouched (harmless).
