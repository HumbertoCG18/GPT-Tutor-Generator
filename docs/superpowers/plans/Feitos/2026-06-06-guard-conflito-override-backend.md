# Guard de conflito override-vs-auto (Backend) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detectar e reportar quando um override manual de bloco do cronograma contradiz um sinal de auto-atribuição forte (unidade: topic confiante ≥0.65 não-ambíguo; kind: `source_kind` do SARC), surfaceando no health report e no `CRONOGRAMA_HEALTH.md`.

**Architecture:** Um módulo de detecção puro (`conflicts.py`) opera sobre blocos serializados — sem recomputar taxonomia, usando campos já gravados (`block_manual_unit_slug`, `manual_kind_override`, `source_kind`, `primary_topic_confidence`, `topic_ambiguous`, `topic_candidates`). O health report e o artefato `CRONOGRAMA_HEALTH.md` consomem essa detecção (warning, não falha dura).

**Tech Stack:** Python 3.11/3.13, pytest.

**Spec:** `docs/superpowers/specs/2026-06-06-guard-conflito-override-curadoria-design.md` (Parte A).

---

## File Structure

- `src/builder/timeline/conflicts.py` — **novo**: `UNIT_AUTO_MIN_CONFIDENCE`, `auto_suggested_unit`, `detect_block_conflicts`, `detect_timeline_conflicts`. Detecção pura.
- `scripts/validate_timeline.py` — `health_report` ganha `override_conflicts`; `validate_file` emite linha de warning.
- `src/builder/artifacts/cronograma_health.py` — seção "Conflitos de curadoria" em `cronograma_health_md`.
- `tests/test_curation_conflicts.py` — **novo**: testes do módulo + health report + render.

---

## Task 1: Módulo de detecção `conflicts.py`

**Files:**
- Create: `src/builder/timeline/conflicts.py`
- Test: `tests/test_curation_conflicts.py` (novo)

- [ ] **Step 1: Write the failing test**

Criar `tests/test_curation_conflicts.py`:

```python
"""Guard de conflito: override manual de bloco vs auto-atribuicao forte."""

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
    # estilo TCC bloco-02: manual unidade-02, auto unidade-01 (conf 1.0)
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
    # estilo bloco-10: override legitimo, auto ambiguo
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
    # estilo bloco-05: review manual, sem source_kind SARC -> override legitimo
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_curation_conflicts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.timeline.conflicts'`.

- [ ] **Step 3: Write minimal implementation**

Criar `src/builder/timeline/conflicts.py`:

```python
"""Guard de conflito entre override manual de bloco e auto-atribuicao forte.

Deteccao pura sobre blocos serializados (.timeline_index.json), sem recomputar
taxonomia. Override manual continua vencendo funcionalmente; este modulo so
torna o conflito visivel para health-check/UI.
"""

from __future__ import annotations

from typing import Iterable, List, Mapping

from src.builder.extraction.teaching_plan import _normalize_unit_slug

# Espelha o gate de topic-derive do build (index.py): o auto so "teria decidido"
# a unidade quando o topico primario e confiante e nao-ambiguo.
UNIT_AUTO_MIN_CONFIDENCE = 0.65


def auto_suggested_unit(block: Mapping) -> tuple[str, float]:
    """(unit_slug, confidence) que o auto atribuiria, ignorando override.

    Abstem ("", 0.0) quando o topico e ambiguo, pouco confiante, ou sem
    candidatos — espelhando exatamente quando o build NAO topic-derivaria.
    """
    if block.get("topic_ambiguous"):
        return ("", 0.0)
    conf = float(block.get("primary_topic_confidence") or 0.0)
    if conf < UNIT_AUTO_MIN_CONFIDENCE:
        return ("", 0.0)
    candidates = block.get("topic_candidates") or []
    if not candidates:
        return ("", 0.0)
    unit = str((candidates[0] or {}).get("unit_slug") or "")
    return (unit, conf) if unit else ("", 0.0)


def detect_block_conflicts(block: Mapping) -> List[dict]:
    """Conflitos override-vs-auto de UM bloco (unidade e kind)."""
    out: List[dict] = []
    block_id = str(block.get("id") or "")

    manual_unit = str(block.get("block_manual_unit_slug") or "").strip()
    if manual_unit:
        auto_unit, conf = auto_suggested_unit(block)
        if auto_unit and _normalize_unit_slug(auto_unit) != _normalize_unit_slug(manual_unit):
            out.append({
                "block_id": block_id,
                "field": "unit",
                "manual": manual_unit,
                "auto": auto_unit,
                "confidence": conf,
            })

    manual_kind = str(block.get("manual_kind_override") or "").strip()
    source_kind = str(block.get("source_kind") or "").strip()
    if manual_kind and source_kind and manual_kind != source_kind:
        out.append({
            "block_id": block_id,
            "field": "kind",
            "manual": manual_kind,
            "auto": source_kind,
            "confidence": 1.0,
        })
    return out


def detect_timeline_conflicts(blocks: Iterable[Mapping]) -> List[dict]:
    """Achata detect_block_conflicts sobre todos os blocos."""
    result: List[dict] = []
    for block in blocks or []:
        if isinstance(block, Mapping):
            result.extend(detect_block_conflicts(block))
    return result
```

NOTA: confirmar que `_normalize_unit_slug` existe em
`src/builder/extraction/teaching_plan.py` (verificado: linha 191) e que esse
módulo NÃO importa de `conflicts` (sem ciclo).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_curation_conflicts.py -v`
Expected: PASS (todos os testes do módulo).

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/conflicts.py tests/test_curation_conflicts.py
git commit -m "feat(timeline): detect manual-override vs auto-assignment conflicts"
```

---

## Task 2: `override_conflicts` no health report

**Files:**
- Modify: `scripts/validate_timeline.py` (imports; `health_report` ~59-85; `validate_file` ~104-123)
- Test: `tests/test_curation_conflicts.py` (APPEND)

- [ ] **Step 1: Write the failing test**

Append em `tests/test_curation_conflicts.py`:

```python
from scripts.validate_timeline import health_report


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_curation_conflicts.py -k health_report -v`
Expected: FAIL — `KeyError: 'override_conflicts'`.

- [ ] **Step 3: Write minimal implementation**

Em `scripts/validate_timeline.py`, adicionar o import (junto dos outros imports do topo do arquivo):
```python
from src.builder.timeline.conflicts import detect_timeline_conflicts
```

No `health_report`, no dict de retorno (após `"class_defect_rate": ...`), adicionar a chave:
```python
        "class_defect_rate": (class_defects / class_blocks) if class_blocks else 0.0,
        "override_conflicts": detect_timeline_conflicts(blocks),
    }
```

Em `validate_file`, após a linha de `msgs.append(f"saúde: ...")`, adicionar o warning (não-bloqueante — não altera `ok`):
```python
    conflicts = report.get("override_conflicts") or []
    if conflicts:
        msgs.append(
            f"warning: {len(conflicts)} override(s) conflitam com auto-atribuicao: "
            + ", ".join(f"{c['block_id']}/{c['field']}" for c in conflicts)
        )
```
Não alterar o cálculo de `ok` (conflito é warning, não gate). 

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_curation_conflicts.py -k health_report -v` (2 pass)
Run: `python -m pytest tests/test_timeline_schema.py -q` (não regrediu — health_report ainda usado lá)

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_timeline.py tests/test_curation_conflicts.py
git commit -m "feat(timeline): surface override conflicts in health report (warning)"
```

---

## Task 3: Seção "Conflitos de curadoria" no `CRONOGRAMA_HEALTH.md`

**Files:**
- Modify: `src/builder/artifacts/cronograma_health.py` (`cronograma_health_md` ~159-234; imports no topo)
- Test: `tests/test_curation_conflicts.py` (APPEND)

- [ ] **Step 1: Write the failing test**

Append em `tests/test_curation_conflicts.py`:

```python
from src.builder.artifacts.cronograma_health import cronograma_health_md


def _conflict_blocks():
    return [
        {"id": "bloco-02", "period_label": "1 dia 04/03/2026",
         "kind": "class",
         "block_manual_unit_slug": "unidade-02-turing",
         "topic_ambiguous": False, "primary_topic_confidence": 1.0,
         "topic_candidates": [{"unit_slug": "unidade-01-conjuntos"}]},
    ]


def test_cronograma_health_lists_conflict():
    md = cronograma_health_md({"name": "TCC"}, [], _conflict_blocks())
    assert "Conflitos de curadoria" in md
    assert "bloco-02" in md
    assert "unidade-02-turing" in md
    assert "unidade-01-conjuntos" in md


def test_cronograma_health_empty_conflicts_phrase():
    blocks = [{"id": "b", "period_label": "x", "kind": "class",
               "unit_slug": "u1"}]
    md = cronograma_health_md({"name": "TCC"}, [], blocks)
    assert "Conflitos de curadoria" in md
    assert "_Nenhum conflito de curadoria._" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_curation_conflicts.py -k cronograma_health -v`
Expected: FAIL — seção ausente (`Conflitos de curadoria` não está no MD).

- [ ] **Step 3: Write minimal implementation**

Em `src/builder/artifacts/cronograma_health.py`, adicionar o import no topo:
```python
from src.builder.timeline.conflicts import detect_timeline_conflicts
```

Em `cronograma_health_md`, ANTES do `return "\n".join(lines) + "\n"` (após o bloco "Blocos mais ricos"), adicionar a seção:
```python
    conflicts = detect_timeline_conflicts(blocks or [])
    period_by_id = {
        str(b.get("id") or ""): str(b.get("period_label") or "")
        for b in (blocks or [])
    }
    lines += [
        "",
        "## Conflitos de curadoria",
        "",
    ]
    if not conflicts:
        lines.append("_Nenhum conflito de curadoria._")
    else:
        for c in conflicts:
            period = period_by_id.get(c["block_id"], "")
            field_label = "unidade" if c["field"] == "unit" else "kind"
            lines.append(
                f"- ⚠️ `{c['block_id']}` ({period}) {field_label}: "
                f"manual `{c['manual']}` ≠ auto `{c['auto']}` "
                f"({c['confidence']:.0%})"
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_curation_conflicts.py -q` (todos pass)
Run: `python -m pytest -q` (suíte completa verde)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/cronograma_health.py tests/test_curation_conflicts.py
git commit -m "feat(cronograma): render curation conflicts section in CRONOGRAMA_HEALTH"
```

---

## Task 4: Verificação fim-a-fim

**Files:** nenhum (verificação)

- [ ] **Step 1: Suíte completa**

Run: `python -m pytest -q`
Expected: PASS (anotar total).

- [ ] **Step 2: Sanidade no corpus real (TCC — snapshot pré-correção do bloco-02 já foi revertido em disco, então 0 conflitos esperado agora; usar um bloco sintético p/ provar o caminho)**

Run:
```bash
python -c "
from src.builder.timeline.conflicts import detect_block_conflicts
b = {'id':'bloco-02','block_manual_unit_slug':'unidade-02-turing-computabilidade','topic_ambiguous':False,'primary_topic_confidence':1.0,'topic_candidates':[{'unit_slug':'unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas'}]}
print('conflito detectado:', detect_block_conflicts(b))
"
```
Expected: imprime 1 conflito unit (manual unidade-02 ≠ auto unidade-01).

- [ ] **Step 3: Commit (só se algo ajustado)**

Se 1-2 passarem sem mudança, sem commit.

---

## Notas de execução

- Hook `code-review-graph.exe` imprime `UnicodeEncodeError` cosmético (cp1252) no commit; o commit **passa**. Ignorar.
- Trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Parte B (UI: aviso no tab + reverter) é plano separado, depois deste.
