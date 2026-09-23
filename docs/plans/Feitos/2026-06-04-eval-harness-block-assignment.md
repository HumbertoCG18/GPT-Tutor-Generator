# Eval Harness — Block Assignment Precision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a measurement harness that scores file→block assignment accuracy against a hand-labeled gold set, so every future scorer/threshold change can be evaluated instead of guessed.

**Architecture:** A gold JSON fixture defines one shared timeline plus N labeled materials (each with its correct block id). A headless runner feeds each material through the REAL block scorer via `content_taxonomy.resolve_unit_block_tags` (same path that writes `manifest.json`), reads the resulting `computed_block_id`/`computed_block_band`, and reports block accuracy, a confusion matrix, and band calibration (the critical "confident-but-wrong" count). A pytest test reads the recorded baseline and fails CI on regression. No disk repo, no Datalab, no Gemini.

**Tech Stack:** Python 3, pytest, stdlib only (`json`, `argparse`, `collections`, `dataclasses`). Reuses `src.builder.engine._select_probable_period_for_entry` (real scorer wiring) and `src.builder.extraction.content_taxonomy.resolve_unit_block_tags`.

---

## Why these files / design decisions (read before starting)

- **Measurement level = final manifest value.** We call `resolve_unit_block_tags` (not the raw scorer) because it includes the `best>=0.95` gate AND the "pega o melhor" fallback. The value it writes to `entry["computed_block_id"]` is exactly what lands in `manifest.json` and feeds `FILE_MAP.md` / `CRONOGRAMA_DETALHADO.md`. That is the number a user actually experiences. Source: `src/builder/extraction/content_taxonomy.py:1018-1052`.
- **Comparison key = block id, not period label.** The scorer returns `period_label`, but `resolve_unit_block_tags` maps it back to a block id internally (`content_taxonomy.py:998-1016`). The gold set stores `expected_block_id`; we read `computed_block_id`. Clean equality.
- **Per-case unit guess via stub.** `resolve_unit_block_tags` resolves the entry's unit through `auto_map_entry_unit_fn` over a unit index. Building a full taxonomy per case is out of scope (YAGNI). Instead each gold case carries an optional `unit_guess` and the harness injects a duck-typed stub match (same shape as `tests/test_resolve_unit_block_band.py:38-46`). This faithfully drives the on-unit boost/penalty (`file_map.py:804-808`) — including the off-unit headline case — without a taxonomy. When `unit_guess` is absent the stub is ambiguous/empty (no boost).
- **Real block scorer.** `select_probable_period_for_entry_fn = _select_probable_period_for_entry` (the engine wrapper that injects all real callables). This is the production scoring path, proven by `tests/test_resolve_unit_block_band.py:178`.
- **Engine untouched.** Non-negotiable: no new logic in `engine.py`. The harness wires `resolve_unit_block_tags` itself (the wiring is ~10 lambdas, already demonstrated in the band test). Keeps blast radius to new files only.

### Gold fixture schema (target shape)

```json
{
  "timeline": {
    "blocks": [
      {
        "id": "bloco-01",
        "period_label": "11/03/2026 a 13/03/2026",
        "unit_slug": "unidade-01-logica",
        "unit_confidence": 0.82,
        "primary_topic_slug": "logica-de-predicados",
        "primary_topic_confidence": 0.74,
        "topic_ambiguous": false,
        "topic_candidates": [],
        "topic_text": "Lógica de predicados",
        "administrative_only": false,
        "rows": [
          {"index": 1, "date_text": "11/03/2026", "content": "Lógica de predicados"},
          {"index": 2, "date_text": "13/03/2026", "content": "Lógica de predicados"}
        ]
      }
    ]
  },
  "cases": [
    {
      "id": "case-date",
      "title": "Processos",
      "raw_target": "raw/pdfs/12.03 processos.pdf",
      "category": "material-de-aula",
      "tags": "",
      "markdown": "# Processos\n\nslides da aula",
      "unit_guess": {"slug": "unidade-01-logica", "confidence": 0.40, "ambiguous": true},
      "expected_block_id": "bloco-01",
      "note": "data 12.03 cai no período do bloco-01"
    }
  ],
  "baseline": {"block_accuracy": 0.0}
}
```

---

## File Structure

- Create `tests/fixtures/eval/assignments_gold.json` — shared timeline + labeled cases + baseline. The data, no logic.
- Create `scripts/eval_assignments.py` — harness: load gold, run real scorer via `resolve_unit_block_tags`, compute metrics, print report, exit nonzero on regression. Importable functions so the test reuses them.
- Create `tests/test_eval_assignments.py` — CI gate: asserts measured block accuracy ≥ `gold["baseline"]["block_accuracy"]` and that the harness runs clean.

---

## Task 1: Gold fixture with one labeled case

**Files:**
- Create: `tests/fixtures/eval/assignments_gold.json`

- [ ] **Step 1: Create the fixture directory and file with a 5-block timeline and one case**

Create `tests/fixtures/eval/assignments_gold.json`:

```json
{
  "timeline": {
    "blocks": [
      {
        "id": "bloco-01",
        "period_label": "11/03/2026 a 13/03/2026",
        "unit_slug": "unidade-01-logica",
        "unit_confidence": 0.82,
        "primary_topic_slug": "logica-de-predicados",
        "primary_topic_confidence": 0.74,
        "topic_ambiguous": false,
        "topic_candidates": [],
        "topic_text": "Lógica de predicados",
        "administrative_only": false,
        "rows": [
          {"index": 1, "date_text": "11/03/2026", "content": "Lógica de predicados"},
          {"index": 2, "date_text": "13/03/2026", "content": "Lógica de predicados"}
        ]
      },
      {
        "id": "bloco-02",
        "period_label": "18/03/2026 a 18/03/2026",
        "unit_slug": "unidade-01-logica",
        "unit_confidence": 0.51,
        "primary_topic_slug": "",
        "primary_topic_confidence": 0.0,
        "topic_ambiguous": true,
        "topic_candidates": [],
        "topic_text": "indução estrutural sobre termos",
        "administrative_only": false,
        "rows": [
          {"index": 3, "date_text": "18/03/2026", "content": "indução estrutural sobre termos"}
        ]
      },
      {
        "id": "bloco-04",
        "period_label": "01/04/2026 a 01/04/2026",
        "unit_slug": "",
        "unit_confidence": 0.0,
        "primary_topic_slug": "",
        "primary_topic_confidence": 0.0,
        "topic_ambiguous": true,
        "topic_candidates": [],
        "topic_text": "Revisão geral da unidade 1",
        "administrative_only": false,
        "rows": [
          {"index": 5, "date_text": "01/04/2026", "content": "Revisão geral da unidade 1"}
        ]
      }
    ]
  },
  "cases": [
    {
      "id": "case-date",
      "title": "Processos",
      "raw_target": "raw/pdfs/12.03 processos.pdf",
      "category": "material-de-aula",
      "tags": "",
      "markdown": "# Processos\n\nslides da aula sobre processos",
      "unit_guess": {"slug": "unidade-01-logica", "confidence": 0.40, "ambiguous": true},
      "expected_block_id": "bloco-01",
      "note": "data 12.03 cai no periodo 11-13/03 do bloco-01"
    }
  ],
  "baseline": {"block_accuracy": 0.0}
}
```

- [ ] **Step 2: Verify it is valid JSON**

Run: `python -c "import json; json.load(open('tests/fixtures/eval/assignments_gold.json', encoding='utf-8')); print('ok')"`
Expected: prints `ok`

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/eval/assignments_gold.json
git commit -m "test(eval): add gold fixture for block assignment harness"
```

---

## Task 2: Harness core — run one case through the real scorer

**Files:**
- Create: `scripts/eval_assignments.py`
- Test: `tests/test_eval_assignments.py`

- [ ] **Step 1: Write the failing test for `predict_block`**

Create `tests/test_eval_assignments.py`:

```python
import json
from pathlib import Path

from scripts.eval_assignments import load_gold, predict_block

GOLD = Path("tests/fixtures/eval/assignments_gold.json")


def test_predict_block_returns_id_and_band_for_date_case():
    gold = load_gold(GOLD)
    case = next(c for c in gold["cases"] if c["id"] == "case-date")
    block_id, band = predict_block(case, gold["timeline"]["blocks"])
    assert block_id == "bloco-01"
    assert band in {"alta", "media", "baixa"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_eval_assignments.py::test_predict_block_returns_id_and_band_for_date_case -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.eval_assignments'`

- [ ] **Step 3: Implement `load_gold` and `predict_block`**

Create `scripts/eval_assignments.py`:

```python
"""Harness de avaliacao da atribuicao arquivo->bloco temporal.

Roda cada material rotulado do gold set pelo SCORER REAL (via
content_taxonomy.resolve_unit_block_tags, o mesmo caminho que escreve o
manifest), le computed_block_id/computed_block_band e compara com o bloco
esperado. Reporta acuracia, matriz de confusao e calibracao de band.

Sem disco, sem Datalab, sem Gemini. Deterministico.

Uso:
    python scripts/eval_assignments.py [tests/fixtures/eval/assignments_gold.json]
    python scripts/eval_assignments.py --json   # so o dump de metricas
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.engine import _select_probable_period_for_entry  # noqa: E402
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags  # noqa: E402


def load_gold(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _stub_unit_match(slug: str, confidence: float, ambiguous: bool):
    """Duck-type do UnitMatch real (cf. tests/test_resolve_unit_block_band.py)."""
    class M:
        pass
    m = M()
    m.slug = slug
    m.confidence = float(confidence)
    m.ambiguous = bool(ambiguous)
    m.reasons = []
    return m


def _entry_from_case(case: dict) -> dict:
    return {
        "id": str(case.get("id", "")),
        "title": str(case.get("title", "")),
        "category": str(case.get("category", "material-de-aula")),
        "file_type": "pdf",
        "source_path": str(case.get("raw_target", "")),
        "raw_target": str(case.get("raw_target", "")),
        "tags": str(case.get("tags", "")),
        "manual_tags": [],
        "auto_tags": [],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
        "manual_subunit_slug": "",
    }


def predict_block(case: dict, blocks: list) -> tuple[str, str]:
    """Retorna (computed_block_id, computed_block_band) do scorer real."""
    guess = case.get("unit_guess") or {}
    unit_stub = _stub_unit_match(
        guess.get("slug", ""),
        guess.get("confidence", 0.0),
        guess.get("ambiguous", True),
    )
    markdown = str(case.get("markdown", ""))

    out = resolve_unit_block_tags(
        [_entry_from_case(case)],
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": list(blocks)},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: None,
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: unit_stub,
        select_probable_period_for_entry_fn=_select_probable_period_for_entry,
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: markdown,
    )[0]
    return str(out.get("computed_block_id", "")), str(out.get("computed_block_band", ""))
```

Note on `auto_map_entry_subtopic_fn` returning `None`: subtopic resolution is not exercised by this harness (block precision only). `resolve_unit_block_tags` guards subtopic usage; returning `None` yields no `subunit:` tag, which is fine — we only read `computed_block_id`/`computed_block_band`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_eval_assignments.py::test_predict_block_returns_id_and_band_for_date_case -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/eval_assignments.py tests/test_eval_assignments.py
git commit -m "feat(eval): predict_block runs gold case through real scorer"
```

---

## Task 3: Metrics — accuracy, confusion, band calibration

**Files:**
- Modify: `scripts/eval_assignments.py`
- Test: `tests/test_eval_assignments.py`

- [ ] **Step 1: Write the failing test for `evaluate`**

Add to `tests/test_eval_assignments.py`:

```python
from scripts.eval_assignments import evaluate


def test_evaluate_reports_accuracy_and_band_calibration():
    gold = load_gold(GOLD)
    report = evaluate(gold)
    assert report["total"] == len(gold["cases"])
    assert 0.0 <= report["block_accuracy"] <= 1.0
    # cada caso classificado como correto/errado e atribuido a uma band
    assert report["correct"] + report["wrong"] == report["total"]
    # calibracao por band existe e soma o total
    band_total = sum(b["correct"] + b["wrong"] for b in report["bands"].values())
    assert band_total == report["total"]
    # o caso de data deve acertar o bloco-01
    by_id = {r["id"]: r for r in report["cases"]}
    assert by_id["case-date"]["predicted"] == "bloco-01"
    assert by_id["case-date"]["correct"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_eval_assignments.py::test_evaluate_reports_accuracy_and_band_calibration -v`
Expected: FAIL with `ImportError: cannot import name 'evaluate'`

- [ ] **Step 3: Implement `evaluate`**

Append to `scripts/eval_assignments.py`:

```python
def evaluate(gold: dict) -> dict:
    blocks = gold["timeline"]["blocks"]
    cases = gold["cases"]

    case_rows = []
    confusion: dict = {}
    bands = {
        "alta": {"correct": 0, "wrong": 0},
        "media": {"correct": 0, "wrong": 0},
        "baixa": {"correct": 0, "wrong": 0},
        "": {"correct": 0, "wrong": 0},  # orfao (sem band)
    }
    correct = 0
    orphans = 0

    for case in cases:
        expected = str(case.get("expected_block_id", ""))
        predicted, band = predict_block(case, blocks)
        is_correct = predicted == expected
        if is_correct:
            correct += 1
        if predicted == "":
            orphans += 1
        bands.setdefault(band, {"correct": 0, "wrong": 0})
        bands[band]["correct" if is_correct else "wrong"] += 1
        key = f"{expected}->{predicted or '(orfao)'}"
        confusion[key] = confusion.get(key, 0) + 1
        case_rows.append({
            "id": str(case.get("id", "")),
            "expected": expected,
            "predicted": predicted,
            "band": band,
            "correct": is_correct,
            "note": str(case.get("note", "")),
        })

    total = len(cases)
    return {
        "total": total,
        "correct": correct,
        "wrong": total - correct,
        "orphans": orphans,
        "block_accuracy": (correct / total) if total else 0.0,
        # confiante e ERRADO = pior falha (band alta mas bloco errado)
        "confident_wrong": bands["alta"]["wrong"],
        "bands": bands,
        "confusion": confusion,
        "cases": case_rows,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_eval_assignments.py::test_evaluate_reports_accuracy_and_band_calibration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/eval_assignments.py tests/test_eval_assignments.py
git commit -m "feat(eval): evaluate computes accuracy, confusion, band calibration"
```

---

## Task 4: Human-readable report + CLI + regression exit code

**Files:**
- Modify: `scripts/eval_assignments.py`

- [ ] **Step 1: Implement `format_report` and `main`**

Append to `scripts/eval_assignments.py`:

```python
def format_report(report: dict, gold: dict) -> str:
    lines = []
    acc = report["block_accuracy"]
    lines.append("=== Eval: atribuicao arquivo -> bloco ===")
    lines.append(
        f"Acuracia de bloco: {report['correct']}/{report['total']} "
        f"({acc * 100:.1f}%)   orfaos: {report['orphans']}"
    )
    lines.append(f"Confiante e ERRADO (band alta, bloco errado): {report['confident_wrong']}")
    lines.append("")
    lines.append("Calibracao por band (correto / errado):")
    for band in ("alta", "media", "baixa", ""):
        b = report["bands"].get(band, {"correct": 0, "wrong": 0})
        label = band or "(orfao)"
        lines.append(f"  {label:<8} {b['correct']:>3} ok / {b['wrong']:>3} erro")
    lines.append("")
    wrong = [c for c in report["cases"] if not c["correct"]]
    if wrong:
        lines.append("Erros:")
        for c in wrong:
            lines.append(
                f"  - {c['id']:<16} esperado={c['expected'] or '(orfao)'} "
                f"previu={c['predicted'] or '(orfao)'} band={c['band'] or '-'}"
                + (f"  [{c['note']}]" if c["note"] else "")
            )
    else:
        lines.append("Sem erros.")
    baseline = float((gold.get("baseline") or {}).get("block_accuracy", 0.0))
    lines.append("")
    lines.append(f"Baseline registrado: {baseline * 100:.1f}%")
    if acc + 1e-9 < baseline:
        lines.append(f"REGRESSAO: {acc * 100:.1f}% < baseline {baseline * 100:.1f}%")
    return "\n".join(lines)


def main(argv: list) -> int:
    as_json = "--json" in argv
    paths = [a for a in argv if not a.startswith("-")]
    gold_path = Path(paths[0]) if paths else Path(
        "tests/fixtures/eval/assignments_gold.json"
    )
    gold = load_gold(gold_path)
    report = evaluate(gold)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report, gold))
    baseline = float((gold.get("baseline") or {}).get("block_accuracy", 0.0))
    return 1 if report["block_accuracy"] + 1e-9 < baseline else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 2: Run the harness end-to-end and capture current accuracy**

Run: `python scripts/eval_assignments.py`
Expected: prints the report; with baseline 0.0 the exit code is 0. Read the printed `Acuracia de bloco` line — this is the FIRST real measurement of the system.

- [ ] **Step 3: Commit**

```bash
git add scripts/eval_assignments.py
git commit -m "feat(eval): human report, JSON output, regression exit code"
```

---

## Task 5: Expand the gold set to the known failure modes

**Files:**
- Modify: `tests/fixtures/eval/assignments_gold.json`

- [ ] **Step 1: Add cases covering topic-match, off-unit, weak/orphan, and date-decay**

In `tests/fixtures/eval/assignments_gold.json`, replace the `"cases"` array with these (keep the same `"timeline"` and `"baseline"` blocks):

```json
"cases": [
  {
    "id": "case-date",
    "title": "Processos",
    "raw_target": "raw/pdfs/12.03 processos.pdf",
    "category": "material-de-aula",
    "tags": "",
    "markdown": "# Processos\n\nslides da aula sobre processos",
    "unit_guess": {"slug": "unidade-01-logica", "confidence": 0.40, "ambiguous": true},
    "expected_block_id": "bloco-01",
    "note": "data 12.03 cai no periodo 11-13/03 do bloco-01"
  },
  {
    "id": "case-topic",
    "title": "Lista 02 - Inducao Estrutural",
    "raw_target": "raw/pdfs/listas/lista 02 inducao estrutural.pdf",
    "category": "listas",
    "tags": "",
    "markdown": "# Inducao Estrutural\n\ninducao estrutural sobre termos e conjuntos indutivos",
    "unit_guess": {"slug": "unidade-01-logica", "confidence": 0.40, "ambiguous": true},
    "expected_block_id": "bloco-02",
    "note": "texto casa o topic_text do bloco-02; sem data"
  },
  {
    "id": "case-offunit-date",
    "title": "Inducao Estrutural sobre conjuntos indutivos",
    "raw_target": "raw/pdfs/listas/18.03 inducao estrutural.pdf",
    "category": "listas",
    "tags": "",
    "markdown": "# Inducao Estrutural\n\ninducao estrutural sobre termos",
    "unit_guess": {"slug": "unidade-99-outra", "confidence": 0.40, "ambiguous": true},
    "expected_block_id": "bloco-02",
    "note": "palpite de unidade ERRADO (off-unit -0.45); data 18.03 + titulo devem vencer"
  },
  {
    "id": "case-weak",
    "title": "Material",
    "raw_target": "raw/pdfs/material.pdf",
    "category": "material-de-aula",
    "tags": "",
    "markdown": "conteudo generico sem pistas distintivas",
    "unit_guess": {"slug": "unidade-01-logica", "confidence": 0.40, "ambiguous": true},
    "expected_block_id": "bloco-01",
    "note": "material fraco: deve atribuir o melhor (nunca orfao) com band media/baixa"
  }
]
```

- [ ] **Step 2: Re-run the harness to see the multi-case scoreboard**

Run: `python scripts/eval_assignments.py`
Expected: report now shows 4 cases. Note the accuracy %, the confusion lines, and the band calibration. `case-weak` may land on either block — what matters is it is NOT an orphan (band media/baixa, not `(orfao)`).

- [ ] **Step 3: Record the measured accuracy as the baseline**

Set `"baseline": {"block_accuracy": X}` in the fixture, where `X` is the fraction just measured (e.g. if 3/4 → `0.75`). This locks the current behavior as the regression floor. Use the exact fraction printed.

Run again to confirm clean: `python scripts/eval_assignments.py`
Expected: no `REGRESSAO` line; exit code 0 (`echo $LASTEXITCODE` in PowerShell prints `0`).

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/eval/assignments_gold.json
git commit -m "test(eval): cover topic, off-unit, weak/orphan failure modes; lock baseline"
```

---

## Task 6: CI regression gate

**Files:**
- Modify: `tests/test_eval_assignments.py`

- [ ] **Step 1: Write the regression-gate test**

Add to `tests/test_eval_assignments.py`:

```python
def test_block_accuracy_not_below_baseline():
    gold = load_gold(GOLD)
    report = evaluate(gold)
    baseline = float(gold["baseline"]["block_accuracy"])
    assert report["block_accuracy"] + 1e-9 >= baseline, (
        f"REGRESSAO: {report['block_accuracy']:.3f} < baseline {baseline:.3f}. "
        f"Erros: {[c['id'] for c in report['cases'] if not c['correct']]}"
    )


def test_no_orphan_when_instructional_blocks_exist():
    # Spec: com blocos instrucionais presentes, nenhum material vira orfao.
    gold = load_gold(GOLD)
    report = evaluate(gold)
    assert report["orphans"] == 0, (
        f"orfaos inesperados: {[c['id'] for c in report['cases'] if c['predicted'] == '']}"
    )
```

- [ ] **Step 2: Run the full eval test file**

Run: `python -m pytest tests/test_eval_assignments.py -v`
Expected: all tests PASS

- [ ] **Step 3: Run the whole suite to confirm zero regressions**

Run: `python -m pytest tests -q`
Expected: no NEW failures vs the pre-existing baseline. (Project has known pre-existing failures; compare against `git stash` run if unsure.)

- [ ] **Step 4: Commit**

```bash
git add tests/test_eval_assignments.py
git commit -m "test(eval): CI gate on block accuracy + no-orphan invariant"
```

---

## Task 7: Document the harness

**Files:**
- Modify: `.mex/ROUTER.md`

- [ ] **Step 1: Add a line under "Current Project State -> Working"**

In `.mex/ROUTER.md`, in the `### Working` bullet list, add:

```markdown
- Harness de avaliacao de atribuicao bloco em `scripts/eval_assignments.py`:
  roda o gold set `tests/fixtures/eval/assignments_gold.json` pelo scorer real
  (resolve_unit_block_tags) e reporta acuracia/confusao/calibracao de band.
  Gate de regressao em `tests/test_eval_assignments.py` (baseline no fixture).
```

- [ ] **Step 2: Commit**

```bash
git add .mex/ROUTER.md
git commit -m "docs(eval): record block-assignment eval harness in ROUTER"
```

---

## Self-Review

**Spec coverage:**
- Measure block assignment precision → Tasks 2-4 (predict + evaluate + report). ✓
- Gold labeled set covering failure modes → Tasks 1, 5 (date, topic, off-unit, weak/orphan). ✓
- Band calibration / confident-wrong signal → Task 3 (`bands`, `confident_wrong`). ✓
- Regression gate → Tasks 4 (exit code) + 6 (pytest). ✓
- No scorer/threshold change (measure only) → all tasks touch new files + docs; `engine.py`, `file_map.py`, `content_taxonomy.py`, `thresholds.py` untouched. ✓

**Placeholder scan:** No "TBD"/"handle edge cases"/"similar to". Every code step shows full code. Baseline value in Task 5 Step 3 is computed from the actual run (the one legitimately runtime-derived number), with exact instruction. ✓

**Type consistency:**
- `predict_block(case, blocks) -> (block_id, band)` defined Task 2, consumed identically in Task 3. ✓
- `evaluate(gold) -> report` keys (`total`, `correct`, `wrong`, `orphans`, `block_accuracy`, `confident_wrong`, `bands`, `confusion`, `cases`) defined Task 3, consumed in `format_report` (Task 4) and tests (Tasks 3, 6). ✓
- `bands` dict keyed by `"alta"/"media"/"baixa"/""` everywhere. ✓
- `load_gold`, `evaluate`, `predict_block`, `format_report`, `main` names stable across tasks. ✓

---

## Open follow-ups (NOT in this plan)

Once the baseline exists, these become measurable (each gets its own plan):
1. Sequence/sibling signal (ordinal "Aula 0X" / import order) to disambiguate adjacent blocks.
2. Date distance-decay replacing the binary month-only weak boost (`file_map.py:888-890`), plus year-boundary fix.
3. Light PT stemming/synonym on topic matching — run the harness before/after to prove net gain.
4. Absolute-winner floor in `confidence_band` so weak-but-unambiguous matches still flag for review.
