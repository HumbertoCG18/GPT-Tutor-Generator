# Contexto Temporal + Prontidão Pré-Prova — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerar `setup/CONTEXTO_TEMPORAL.md` (cronograma compacto) + regras de instrução para o tutor LLM calcular sozinho, a cada sessão, a semana atual, a próxima avaliação e a prontidão pré-prova — sem reprocessar a matéria.

**Architecture:** Dado estável (cronograma) é emitido no build a partir de `.timeline_index.json`; lógica dinâmica ("hoje", prontidão) é delegada ao tutor via uma seção fixa injetada nos geradores de instrução. Rótulos de unidade (`U1`) saem de um módulo base novo, compartilhado entre builder e UI.

**Tech Stack:** Python 3, pytest. Sem libs novas. Datas ISO via `datetime.date`.

**Spec:** `docs/superpowers/specs/2026-06-10-contexto-temporal-tutor-design.md`

---

## Estrutura de arquivos

- **Criar** `src/builder/timeline/unit_labels.py` — base: `unit_short_label`, `unit_name_from_slug`, `unit_number`, regex `_UNIT_NUM_RE`. Sem dependências para cima.
- **Modificar** `src/ui/timeline_dashboard.py:91-101` — remover regex+def locais, importar do módulo base com alias `_unit_short_label`.
- **Criar** `src/builder/artifacts/temporal_context.py` — `build_temporal_context_rows`, `build_unit_legend`, `temporal_context_md`, `current_block_for_date` + helper `_tipo_label`.
- **Modificar** `src/builder/artifacts/prompts.py` — `_temporal_context_instructions()` + injeção nos 3 geradores.
- **Modificar** `src/builder/ops/bootstrap_ops.py` — gravar `setup/CONTEXTO_TEMPORAL.md` (import direto, padrão do `cronograma_detalhado_md`).
- **Modificar** `src/builder/ops/pedagogical_regeneration.py` — idem, no caminho incremental.
- **Criar** `tests/test_unit_labels.py`, `tests/test_temporal_context.py`.
- **Modificar** `tests/test_core.py` (~4446) — assert do artefato no teste de `incremental_build` existente.

---

### Task 1: Módulo base `unit_labels.py` + refactor da UI

**Files:**
- Create: `src/builder/timeline/unit_labels.py`
- Test: `tests/test_unit_labels.py`
- Modify: `src/ui/timeline_dashboard.py:91-101`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_unit_labels.py`:

```python
"""Rótulo curto e nome de unidade a partir de slugs canônicos."""

from src.builder.timeline.unit_labels import (
    unit_short_label,
    unit_name_from_slug,
    unit_number,
)


def test_unit_short_label():
    assert unit_short_label("unidade-01-limites") == "U1"
    assert unit_short_label("unidade-10-series") == "U10"
    assert unit_short_label("unidade_02_derivadas") == "U2"
    assert unit_short_label("topico-avulso") == "topico-avulso"  # fora do padrão
    assert unit_short_label("") == ""
    assert unit_short_label(None) == ""


def test_unit_name_from_slug():
    assert unit_name_from_slug("unidade-01-limites") == "Limites"
    assert unit_name_from_slug("unidade-02-derivadas-parciais") == "Derivadas parciais"
    assert unit_name_from_slug("unidade-03") == "unidade-03"  # sem sufixo -> slug
    assert unit_name_from_slug("topico-avulso") == "topico-avulso"
    assert unit_name_from_slug("") == ""


def test_unit_number():
    assert unit_number("unidade-01-limites") == 1
    assert unit_number("unidade-10-series") == 10
    assert unit_number("topico-avulso") is None
    assert unit_number("") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_unit_labels.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.builder.timeline.unit_labels'`

- [ ] **Step 3: Create the module**

Create `src/builder/timeline/unit_labels.py`:

```python
"""Rótulos curtos e nomes de unidade a partir de slugs canônicos.

Base compartilhada: o builder (artifacts/temporal_context) e a UI
(timeline_dashboard) consomem daqui. Sem dependências para cima.
"""

from __future__ import annotations

import re
from typing import Optional

_UNIT_NUM_RE = re.compile(r"unidade[-_\s]*0*(\d+)", re.IGNORECASE)


def unit_number(slug: str) -> Optional[int]:
    """Número da unidade no slug, ou None se não casar o padrão."""
    m = _UNIT_NUM_RE.search(str(slug or ""))
    return int(m.group(1)) if m else None


def unit_short_label(slug: str) -> str:
    """'unidade-01-limites' -> 'U1'. Mantém o original se não casar o padrão."""
    s = str(slug or "").strip()
    if not s:
        return ""
    n = unit_number(s)
    return f"U{n}" if n is not None else s


def unit_name_from_slug(slug: str) -> str:
    """'unidade-01-limites' -> 'Limites'. Sem sufixo de nome -> o próprio slug."""
    s = str(slug or "").strip()
    if not s:
        return ""
    m = _UNIT_NUM_RE.search(s)
    if not m:
        return s
    tail = s[m.end():].lstrip("-_ ")
    name = tail.replace("-", " ").replace("_", " ").strip()
    if not name:
        return s
    return name[:1].upper() + name[1:]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_unit_labels.py -q`
Expected: PASS (3 tests)

- [ ] **Step 5: Refactor the UI to import from the base module**

In `src/ui/timeline_dashboard.py`, remove the local regex and function (lines 91-101):

```python
_UNIT_NUM_RE = re.compile(r"unidade[-_\s]*0*(\d+)", re.IGNORECASE)


def _unit_short_label(slug: str) -> str:
    """Converte slug de unidade em rótulo curto: 'unidade-01-...' -> 'U1'.
    Mantém o original se não casar o padrão."""
    s = str(slug or "").strip()
    if not s:
        return ""
    m = _UNIT_NUM_RE.search(s)
    return f"U{int(m.group(1))}" if m else s
```

Replace that whole block with an import alias (keeps the private name that existing tests import):

```python
from src.builder.timeline.unit_labels import unit_short_label as _unit_short_label
```

Place the import next to the other `from src.builder...` imports near the top of the file (after line 16). Leave a one-line comment where the def was if helpful, but no code.

- [ ] **Step 6: Verify UI still imports `_unit_short_label` and the regex is unused**

Run: `python -m pytest tests/test_timeline_sort.py tests/test_ui_queue_dashboard.py -q`
Expected: PASS (27 tests). `tests/test_timeline_sort.py` imports `_unit_short_label` from the UI module — the alias keeps it working.

Note: `_UNIT_NUM_RE` was only used inside the removed function (verified). If a stray reference remains, the test run will surface a `NameError`.

- [ ] **Step 7: Commit**

```bash
git add src/builder/timeline/unit_labels.py tests/test_unit_labels.py src/ui/timeline_dashboard.py
git commit -m "refactor(timeline): extrai unit_short_label/unit_name_from_slug pra módulo base"
```

---

### Task 2: `build_temporal_context_rows` + rótulo de tipo

**Files:**
- Create: `src/builder/artifacts/temporal_context.py`
- Test: `tests/test_temporal_context.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_temporal_context.py`:

```python
"""Gerador do artefato setup/CONTEXTO_TEMPORAL.md."""

from src.builder.artifacts.temporal_context import build_temporal_context_rows


def _class_block():
    return {
        "id": "bloco-01",
        "period_start": "2026-03-03",
        "period_end": "2026-03-10",
        "kind": "class",
        "unit_slug": "unidade-01-limites",
        "topics": ["Definição de limite", "Limites laterais"],
        "primary_topic_label": "Definição de limite",
    }


def _assessment_block():
    return {
        "id": "bloco-09",
        "period_start": "2026-04-28",
        "period_end": "2026-04-28",
        "kind": "assessment",
        "sessions": [{"label": "prova p1 prova"}],
        "scope_unit_slugs": ["unidade-01-limites", "unidade-02-derivadas"],
    }


def test_class_row_uses_full_topics_list_and_short_unit():
    rows = build_temporal_context_rows([_class_block()])
    assert len(rows) == 1
    r = rows[0]
    assert r["id"] == "bloco-01"
    assert r["inicio"] == "2026-03-03"
    assert r["fim"] == "2026-03-10"
    assert r["tipo"] == "aula"
    assert r["unidade"] == "U1"
    assert r["unidade_slug"] == "unidade-01-limites"
    assert r["topico"] == "Definição de limite; Limites laterais"
    assert r["escopo"] == []


def test_class_row_falls_back_to_primary_topic_when_no_topics():
    blk = _class_block()
    blk["topics"] = []
    rows = build_temporal_context_rows([blk])
    assert rows[0]["topico"] == "Definição de limite"


def test_assessment_row_has_exam_code_and_short_scope():
    rows = build_temporal_context_rows([_assessment_block()])
    r = rows[0]
    assert r["tipo"] == "prova P1"
    assert r["escopo"] == ["U1", "U2"]
    assert r["escopo_slugs"] == ["unidade-01-limites", "unidade-02-derivadas"]


def test_review_and_holiday_tipo_labels():
    review = {"id": "b7", "period_start": "2026-04-21", "kind": "review",
              "scope_unit_slugs": ["unidade-01-limites"]}
    holiday = {"id": "b8", "period_start": "2026-04-22", "kind": "holiday"}
    rows = build_temporal_context_rows([review, holiday])
    assert rows[0]["tipo"] == "revisão"
    assert rows[0]["escopo"] == ["U1"]
    assert rows[1]["tipo"] == "feriado"


def test_block_without_start_date_is_omitted():
    blk = {"id": "x", "kind": "class", "topics": ["t"]}  # sem period_start
    assert build_temporal_context_rows([blk]) == []


def test_end_falls_back_to_start_when_missing():
    blk = {"id": "b", "period_start": "2026-03-03", "kind": "class"}
    assert build_temporal_context_rows([blk])[0]["fim"] == "2026-03-03"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_temporal_context.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.builder.artifacts.temporal_context'`

- [ ] **Step 3: Create the module with rows builder**

Create `src/builder/artifacts/temporal_context.py`:

```python
"""Gera setup/CONTEXTO_TEMPORAL.md: cronograma compacto que o tutor LLM usa
para calcular, a cada sessão, a semana atual, a próxima avaliação e a
prontidão pré-prova. Datas ISO; rótulos de unidade curtos (U1) com legenda.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from src.builder.extraction.content_taxonomy import _exam_code_from_block
from src.builder.timeline.unit_labels import (
    unit_name_from_slug,
    unit_number,
    unit_short_label,
)

# kind do bloco -> rótulo curto pra coluna "tipo" (assessment é tratado à parte).
_KIND_TIPO = {
    "class": "aula",
    "review": "revisão",
    "holiday": "feriado",
    "suspended": "suspensão",
    "makeup": "reposição",
    "academic_event": "evento acadêmico",
    "office_hours": "atendimento",
    "workshop": "oficina",
    "deliverable": "entrega",
    "planning": "planejamento",
    "reserved": "reserva",
    "results": "resultados",
    "overview": "introdução",
    "unknown": "—",
}


def _tipo_label(block: dict) -> str:
    kind = str(block.get("kind") or "")
    if kind == "assessment":
        code = _exam_code_from_block(block)
        if code == "EXAME":
            return "exame"
        if code == "PF":
            return "prova final"
        return f"prova {code}" if code else "prova"
    return _KIND_TIPO.get(kind, kind or "—")


def build_temporal_context_rows(timeline_blocks: list) -> list:
    """Mapeia blocos do cronograma em linhas compactas. Blocos sem data ISO
    de início são omitidos (não dá pra localizá-los no tempo)."""
    rows = []
    for b in timeline_blocks or []:
        start = str(b.get("period_start") or "").strip()
        if not start:
            continue
        end = str(b.get("period_end") or "").strip() or start
        unit_slug = str(b.get("unit_slug") or "").strip()
        topics = [str(t).strip() for t in (b.get("topics") or []) if str(t).strip()]
        if topics:
            topico = "; ".join(topics)
        else:
            topico = str(b.get("primary_topic_label") or "").strip()
        scope_slugs = [str(s).strip() for s in (b.get("scope_unit_slugs") or []) if str(s).strip()]
        rows.append({
            "id": str(b.get("id") or ""),
            "inicio": start,
            "fim": end,
            "tipo": _tipo_label(b),
            "unidade": unit_short_label(unit_slug),
            "unidade_slug": unit_slug,
            "topico": topico,
            "escopo": [unit_short_label(s) for s in scope_slugs],
            "escopo_slugs": scope_slugs,
        })
    return rows
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_temporal_context.py -q`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/temporal_context.py tests/test_temporal_context.py
git commit -m "feat(artifacts): build_temporal_context_rows (linhas do cronograma compacto)"
```

---

### Task 3: `build_unit_legend`

**Files:**
- Modify: `src/builder/artifacts/temporal_context.py`
- Test: `tests/test_temporal_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_temporal_context.py`:

```python
from src.builder.artifacts.temporal_context import build_unit_legend


def test_unit_legend_collects_units_from_unit_and_scope_sorted_deduped():
    rows = [
        {"unidade_slug": "unidade-02-derivadas", "escopo_slugs": []},
        {"unidade_slug": "", "escopo_slugs": ["unidade-01-limites", "unidade-02-derivadas"]},
        {"unidade_slug": "unidade-01-limites", "escopo_slugs": []},
    ]
    legend = build_unit_legend(rows)
    assert legend == [
        {"label": "U1", "slug": "unidade-01-limites", "nome": "Limites"},
        {"label": "U2", "slug": "unidade-02-derivadas", "nome": "Derivadas"},
    ]


def test_unit_legend_empty_when_no_units():
    rows = [{"unidade_slug": "", "escopo_slugs": []}]
    assert build_unit_legend(rows) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_temporal_context.py::test_unit_legend_collects_units_from_unit_and_scope_sorted_deduped -v`
Expected: FAIL with `ImportError: cannot import name 'build_unit_legend'`

- [ ] **Step 3: Implement `build_unit_legend`**

Add to `src/builder/artifacts/temporal_context.py` (after `build_temporal_context_rows`):

```python
def build_unit_legend(rows: list) -> list:
    """Legenda U1/U2 -> slug + nome, só das unidades que aparecem nas linhas
    (em 'unidade_slug' ou no escopo). Ordenada por número da unidade."""
    seen = set()
    slugs = []
    for r in rows:
        candidates = []
        if r.get("unidade_slug"):
            candidates.append(r["unidade_slug"])
        candidates.extend(r.get("escopo_slugs") or [])
        for s in candidates:
            if s and s not in seen:
                seen.add(s)
                slugs.append(s)
    slugs.sort(key=lambda s: (unit_number(s) if unit_number(s) is not None else 9999, s))
    return [
        {"label": unit_short_label(s), "slug": s, "nome": unit_name_from_slug(s)}
        for s in slugs
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_temporal_context.py -q`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/temporal_context.py tests/test_temporal_context.py
git commit -m "feat(artifacts): build_unit_legend (mapa U1/U2 -> slug + nome)"
```

---

### Task 4: `temporal_context_md` + `current_block_for_date`

**Files:**
- Modify: `src/builder/artifacts/temporal_context.py`
- Test: `tests/test_temporal_context.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_temporal_context.py`:

```python
from datetime import date

from src.builder.artifacts.temporal_context import (
    temporal_context_md,
    current_block_for_date,
)


def test_md_has_legend_table_iso_dates_and_short_labels():
    blocks = [_class_block(), _assessment_block()]
    md = temporal_context_md({"course_name": "Cálculo I"}, blocks)
    assert "# CONTEXTO TEMPORAL — Cálculo I" in md
    assert "## Unidades" in md
    assert "- **U1** = `unidade-01-limites` — Limites" in md
    assert "## Cronograma" in md
    assert "| bloco | inicio | fim | tipo | unidade | topico | escopo |" in md
    assert "2026-03-03" in md
    assert "| bloco-09 | 2026-04-28 | 2026-04-28 | prova P1 | — | — | U1, U2 |" in md


def test_md_empty_timeline_shows_unavailable_note():
    md = temporal_context_md({"course_name": "X"}, [])
    assert "Cronograma indisponível" in md
    assert "## Cronograma" not in md
    assert "## Unidades" not in md


def test_current_block_for_date_inside_window():
    rows = build_temporal_context_rows([_class_block()])
    found = current_block_for_date(rows, date(2026, 3, 5))
    assert found is not None and found["id"] == "bloco-01"


def test_current_block_for_date_inclusive_bounds():
    rows = build_temporal_context_rows([_class_block()])
    assert current_block_for_date(rows, date(2026, 3, 3))["id"] == "bloco-01"
    assert current_block_for_date(rows, date(2026, 3, 10))["id"] == "bloco-01"


def test_current_block_for_date_outside_returns_none():
    rows = build_temporal_context_rows([_class_block()])
    assert current_block_for_date(rows, date(2026, 1, 1)) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_temporal_context.py -k "md_ or current_block" -q`
Expected: FAIL with `ImportError: cannot import name 'temporal_context_md'`

- [ ] **Step 3: Implement the renderer and date lookup**

Add to `src/builder/artifacts/temporal_context.py`:

```python
def _parse_iso(value) -> Optional[date]:
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def current_block_for_date(rows: list, ref_date: date) -> Optional[dict]:
    """Primeira linha cujo intervalo [inicio, fim] contém ref_date. Bordas
    inclusivas. None se nenhuma janela contém a data."""
    for r in rows:
        start = _parse_iso(r.get("inicio"))
        end = _parse_iso(r.get("fim")) or start
        if start and end and start <= ref_date <= end:
            return r
    return None


def temporal_context_md(course_meta: dict, timeline_blocks: list) -> str:
    """Renderiza o artefato CONTEXTO_TEMPORAL.md (cabeçalho + legenda + tabela).
    Cronograma vazio -> nota de indisponível."""
    course_name = (course_meta or {}).get("course_name", "Curso")
    rows = build_temporal_context_rows(timeline_blocks)
    lines = [
        f"# CONTEXTO TEMPORAL — {course_name}",
        "",
        "> Cronograma compacto. Você (tutor) calcula a semana atual e a prontidão",
        "> pré-prova A CADA sessão comparando com a data de hoje. Datas ISO YYYY-MM-DD.",
        "",
    ]
    if not rows:
        lines += ["_Cronograma indisponível._", ""]
        return "\n".join(lines)

    legend = build_unit_legend(rows)
    if legend:
        lines += ["## Unidades", ""]
        for u in legend:
            nome = f" — {u['nome']}" if u["nome"] else ""
            lines.append(f"- **{u['label']}** = `{u['slug']}`{nome}")
        lines.append("")

    lines += [
        "## Cronograma",
        "",
        "| bloco | inicio | fim | tipo | unidade | topico | escopo |",
        "|-------|--------|-----|------|---------|--------|--------|",
    ]
    for r in rows:
        unidade = r["unidade"] or "—"
        topico = r["topico"] or "—"
        escopo = ", ".join(r["escopo"]) if r["escopo"] else "—"
        lines.append(
            f"| {r['id']} | {r['inicio']} | {r['fim']} | {r['tipo']} | "
            f"{unidade} | {topico} | {escopo} |"
        )
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_temporal_context.py -q`
Expected: PASS (13 tests)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/temporal_context.py tests/test_temporal_context.py
git commit -m "feat(artifacts): temporal_context_md + current_block_for_date"
```

---

### Task 5: Seção de instrução nos geradores (prompts.py)

**Files:**
- Modify: `src/builder/artifacts/prompts.py` (add `_temporal_context_instructions`; inject in 3 generators)
- Test: `tests/test_temporal_context_prompts.py` (novo)

- [ ] **Step 1: Write the failing test**

Create `tests/test_temporal_context_prompts.py`:

```python
"""A seção de contexto temporal entra nas instruções dos 3 geradores."""

from src.builder.artifacts.prompts import (
    generate_claude_project_instructions,
    generate_gpt_instructions,
    generate_gemini_instructions,
)

META = {"course_name": "Cálculo I", "professor": "P", "institution": "I", "semester": "2026/1"}


def test_claude_instructions_include_temporal_section():
    out = generate_claude_project_instructions(META)
    assert "## Contexto temporal" in out
    assert "setup/CONTEXTO_TEMPORAL.md" in out
    assert "prova ≤ 7 dias" in out


def test_gpt_instructions_include_temporal_section():
    out = generate_gpt_instructions(META)
    assert "## Contexto temporal" in out
    assert "setup/CONTEXTO_TEMPORAL.md" in out


def test_gemini_instructions_include_temporal_section():
    out = generate_gemini_instructions(META)
    assert "## Contexto temporal" in out
    assert "setup/CONTEXTO_TEMPORAL.md" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_temporal_context_prompts.py -q`
Expected: FAIL (assertion: `## Contexto temporal` not in output)

- [ ] **Step 3: Add the helper and inject it**

In `src/builder/artifacts/prompts.py`, add the helper near the other section helpers (e.g., after the function that ends at line 294, before `_low_token_generate_claude_project_instructions` at line 327):

```python
def _temporal_context_instructions() -> str:
    return """
## Contexto temporal — calcule no início de cada sessão
Abra `setup/CONTEXTO_TEMPORAL.md`. Com a data de HOJE:
1. **Semana atual**: linha onde hoje ∈ [inicio, fim]. Diga unidade + tópico vigente.
   Se hoje for depois do último bloco, o semestre acabou; se antes do 1º, ainda não começou.
2. **Próxima avaliação**: 1ª linha tipo=prova/exame com inicio ≥ hoje. Diga qual, a data,
   dias restantes e o escopo (unidades — resolva o rótulo U1/U2 pela seção `## Unidades`).
3. **Prontidão pré-prova** (só se houver prova futura): pra cada unidade do escopo →
   tópicos no `COURSE_MAP.md` → status em `STUDENT_STATE.md` / `student/batteries/<slug>/`.
   Liste tópicos sem registro ou pendentes. Priorize se a prova ≤ 7 dias.
Se `CONTEXTO_TEMPORAL.md` não existir ou estiver vazio, pule este bloco.
"""
```

Now inject the section into each generator by appending to its returned string.

**Claude** — the public wrapper at line 463-480 returns `_low_token_generate_claude_project_instructions(...)`. Change the `return` to concatenate:

```python
    return _low_token_generate_claude_project_instructions(
        course_meta,
        student_profile=student_profile,
        subject_profile=subject_profile,
        has_assignments=has_assignments,
        has_code=has_code,
        has_whiteboard=has_whiteboard,
    ) + _temporal_context_instructions()
```

**GPT** — `generate_gpt_instructions` ends with `return f"""# Instruções do Tutor — {course_name}` ... `"""` at line 544. Append the helper to that f-string return. Locate the closing `"""` of that return and change it to:

```python
"""  # (fim do f-string existente)
    return _gpt_text + _temporal_context_instructions()
```

If the function returns the f-string directly (no intermediate variable), wrap it: assign the f-string to a local `_gpt_text` and then `return _gpt_text + _temporal_context_instructions()`. Minimal diff: replace `    return f"""# Instruções do Tutor — {course_name}` with `    _gpt_text = f"""# Instruções do Tutor — {course_name}` and add after its closing `"""`:

```python
    return _gpt_text + _temporal_context_instructions()
```

**Gemini** — `generate_gemini_instructions` returns `f"""# Instruções do Tutor | {course_name}` ... `"""` at line 694. Apply the same pattern: rename the returned f-string to `_gemini_text` and append:

```python
    return _gemini_text + _temporal_context_instructions()
```

- [ ] **Step 4: Run the new test to verify it passes**

Run: `python -m pytest tests/test_temporal_context_prompts.py -q`
Expected: PASS (3 tests)

- [ ] **Step 5: Verify the existing instruction-content test still passes**

Run: `python -m pytest "tests/test_core.py" -k "incremental or instruct" -q`
Expected: PASS — appending a section does not remove the strings that `tests/test_core.py:4457-4459` asserts (`Ordem de leitura econômica`, etc.).

- [ ] **Step 6: Commit**

```bash
git add src/builder/artifacts/prompts.py tests/test_temporal_context_prompts.py
git commit -m "feat(prompts): seção de contexto temporal nos 3 geradores de instrução"
```

---

### Task 6: Wire `CONTEXTO_TEMPORAL.md` no build (completo + incremental)

**Files:**
- Modify: `src/builder/ops/bootstrap_ops.py:222-228` (após CODE_HEALTH, antes do README)
- Modify: `src/builder/ops/pedagogical_regeneration.py` (após o bloco CODE_HEALTH ~356, antes do whiteboard/README)
- Test: `tests/test_core.py` (~4446, teste de `incremental_build` existente)

- [ ] **Step 1: Write the failing assertion**

In `tests/test_core.py`, in the existing `incremental_build` integration test, after the line that reads `INSTRUCOES_CLAUDE_PROJETO.md` (around line 4446), add:

```python
        contexto_temporal = (repo / "setup" / "CONTEXTO_TEMPORAL.md").read_text(encoding="utf-8")
```

And add an assertion alongside the existing instruction asserts (around line 4459):

```python
        assert "CONTEXTO TEMPORAL" in contexto_temporal
```

(The header is always present even when the timeline has no dated blocks — the empty-timeline path still emits `# CONTEXTO TEMPORAL — ...`.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest "tests/test_core.py" -k incremental -q`
Expected: FAIL with `FileNotFoundError: ... setup/CONTEXTO_TEMPORAL.md` (incremental path doesn't write it yet).

- [ ] **Step 3: Wire into the incremental path (`pedagogical_regeneration.py`)**

In `src/builder/ops/pedagogical_regeneration.py`, after the `CODE_HEALTH.md` write block (the `write_text(... "course" / "CODE_HEALTH.md" ...)` near line 356-366), add an unconditional write (follows the existing `from src.builder.artifacts.repo import ...` local-import pattern):

```python
    from src.builder.artifacts.temporal_context import temporal_context_md as _temporal_context_md
    write_text(
        builder.root_dir / "setup" / "CONTEXTO_TEMPORAL.md",
        _temporal_context_md(builder.course_meta, builder._load_timeline_blocks()),
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest "tests/test_core.py" -k incremental -q`
Expected: PASS.

- [ ] **Step 5: Wire into the full-build path (`bootstrap_ops.py`)**

In `src/builder/ops/bootstrap_ops.py`, after the `CODE_HEALTH.md` write (ends line 222) and before `write_text(builder.root_dir / "README.md", ...)` (line 228), add:

```python
    from src.builder.artifacts.temporal_context import temporal_context_md as _temporal_context_md
    write_text(
        builder.root_dir / "setup" / "CONTEXTO_TEMPORAL.md",
        _temporal_context_md(builder.course_meta, builder._load_timeline_blocks()),
    )
```

`write_text` already cria o diretório pai (`ensure_dir`) e é atômico.

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS (all). The new artifact write is exercised by the incremental integration test; the full-build path shares `temporal_context_md`, which is unit-tested in Task 4.

- [ ] **Step 7: Commit**

```bash
git add src/builder/ops/bootstrap_ops.py src/builder/ops/pedagogical_regeneration.py tests/test_core.py
git commit -m "feat(build): grava setup/CONTEXTO_TEMPORAL.md no build completo e incremental"
```

---

## Final verification

- [ ] Run full suite: `python -m pytest -q` — all green.
- [ ] Sanity: gerar/abrir um repo e conferir `setup/CONTEXTO_TEMPORAL.md` (legenda + tabela) e a seção "Contexto temporal" em `setup/INSTRUCOES_CLAUDE_PROJETO.md`.
- [ ] Atualizar `docs/reports/2026-06-09-relatorio-sistema.html`: marcar #12+#13 como feito (changelog + tabela de priorização).
