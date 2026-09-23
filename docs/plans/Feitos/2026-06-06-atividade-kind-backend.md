# Atividade → kind do bloco (Plano 1 de C) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Derivar o kind do bloco da coluna *Atividade* do cronograma (já presente na tabela do syllabus como `row["atividade"]`), para que provas/trabalhos/feriados sejam classificados corretamente mesmo em syllabi sem marcador `{kind=}`, e saiam da atribuição de unidade.

**Architecture:** Em `_build_timeline_candidate_rows`, quando não há `{kind=...}` explícito no conteúdo, mapear o valor da coluna Atividade via `_ATIVIDADE_KIND_MAP` (reuso de `helpers.py`). Isso seta `row["kind"]`, que agrega em `block["source_kind"]` (mecanismo existente) → `classify_block` retorna o kind → `finalize_block` zera unidade de não-aula.

**Tech Stack:** Python 3.11/3.13, pytest.

**Spec:** `docs/superpowers/specs/2026-06-06-precisao-bloco-unidade-design.md` (Parte 1).

---

## File Structure

- `src/builder/timeline/index.py` — import de `_ATIVIDADE_KIND_MAP`/`_norm_ascii_lower`; helper `_row_atividade`; derivação de kind da Atividade em `_build_timeline_candidate_rows`.
- `tests/test_atividade_kind.py` — **novo**: testes unitários + integração.

---

## Task 1: Derivar kind da coluna Atividade

**Files:**
- Modify: `src/builder/timeline/index.py` (import ~linha 18; novo helper perto de `_build_timeline_candidate_rows` ~452; bloco de kind ~458-465)
- Test: `tests/test_atividade_kind.py` (novo)

- [ ] **Step 1: Write the failing test**

Criar `tests/test_atividade_kind.py`:

```python
"""Deriva kind do bloco a partir da coluna Atividade do cronograma (sem {kind=})."""

from src.builder.timeline.index import _build_timeline_candidate_rows


def _row(descricao, atividade, data="03/07/2026"):
    # chaves espelham os headers normalizados da tabela do syllabus
    return {"data": data, "descricao": descricao, "atividade": atividade}


def test_atividade_prova_sets_assessment_kind():
    rows = _build_timeline_candidate_rows([_row("Prova P2", "Prova")])
    assert rows[0]["kind"] == "assessment"


def test_atividade_aula_stays_class():
    rows = _build_timeline_candidate_rows([_row("Maquinas de Turing", "Aula")])
    assert rows[0]["kind"] == "class"


def test_atividade_trabalho_sets_deliverable():
    rows = _build_timeline_candidate_rows([_row("Apresentacao T1", "Trabalho")])
    assert rows[0]["kind"] == "deliverable"


def test_atividade_feriado_sets_holiday():
    rows = _build_timeline_candidate_rows([_row("Feriado", "Feriado")])
    assert rows[0]["kind"] == "holiday"


def test_atividade_accented_prova_substituicao_maps_assessment():
    rows = _build_timeline_candidate_rows([_row("Prova PS", "Prova de Substituição")])
    assert rows[0]["kind"] == "assessment"


def test_explicit_kind_marker_wins_over_atividade():
    # {kind=holiday} no conteudo vence a coluna Atividade=Prova
    rows = _build_timeline_candidate_rows(
        [{"data": "03/07/2026", "descricao": "X {kind=holiday}", "atividade": "Prova"}]
    )
    assert rows[0]["kind"] == "holiday"


def test_no_atividade_column_defaults_class():
    rows = _build_timeline_candidate_rows([{"data": "03/07/2026", "conteudo": "Aula normal"}])
    assert rows[0]["kind"] == "class"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_atividade_kind.py -v`
Expected: FAIL — `test_atividade_prova_sets_assessment_kind` etc. (hoje Atividade não dirige kind; "Prova" só vira texto no content).

- [ ] **Step 3: Write minimal implementation**

(a) Em `src/builder/timeline/index.py`, estender o import existente (linha 18):
```python
from src.utils.helpers import slugify, write_text, _ATIVIDADE_KIND_MAP, _norm_ascii_lower
```

(b) Logo antes de `def _build_timeline_candidate_rows` (~linha 452), adicionar o helper:
```python
def _row_atividade(row: Dict[str, str]) -> str:
    """Valor da coluna 'Atividade' da row do cronograma (qualquer header que a contenha)."""
    for key in row or {}:
        if "atividade" in str(key).lower():
            return str(row.get(key) or "")
    return ""
```

(c) Em `_build_timeline_candidate_rows`, o bloco atual é:
```python
        kind = "class"
        match = _KIND_TOKEN_RE.search(content)
        if match:
            raw = match.group(1).strip().lower() or "class"
            kind = raw if (raw in _VALID_KIND_VALUES or raw in _IGNORED_KINDS) else "class"
            content = _collapse_ws(_KIND_TOKEN_RE.sub("", content))
        ignored = kind in _IGNORED_KINDS
```
Trocar por (adiciona o `else` que deriva da Atividade quando não há marcador):
```python
        kind = "class"
        match = _KIND_TOKEN_RE.search(content)
        if match:
            raw = match.group(1).strip().lower() or "class"
            kind = raw if (raw in _VALID_KIND_VALUES or raw in _IGNORED_KINDS) else "class"
            content = _collapse_ws(_KIND_TOKEN_RE.sub("", content))
        else:
            # Sem marcador {kind=}: a coluna Atividade do SARC e o sinal autoritativo.
            atividade = _norm_ascii_lower(_row_atividade(row))
            for needle, mapped in _ATIVIDADE_KIND_MAP.items():
                if needle in atividade:
                    kind = mapped
                    break
        ignored = kind in _IGNORED_KINDS
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_atividade_kind.py -v`
Expected: PASS (7 testes).

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py tests/test_atividade_kind.py
git commit -m "feat(timeline): derive block kind from Atividade column (no {kind=} marker)"
```

---

## Task 2: Integração — prova real do syllabus vira assessment

**Files:**
- Test: `tests/test_atividade_kind.py` (APPEND)

- [ ] **Step 1: Write the failing test**

Append em `tests/test_atividade_kind.py` (usa o agregador + classifier reais):

```python
from src.builder.timeline.index import _aggregate_source_kind
from src.builder.timeline.classifier import classify_block
from src.builder.timeline.kinds import BlockKind


def test_prova_rows_aggregate_to_assessment_source_kind():
    rows = _build_timeline_candidate_rows([
        {"data": "01/07/2026", "descricao": "Revisao para Prova P2", "atividade": "Aula"},
        {"data": "03/07/2026", "descricao": "Prova P2", "atividade": "Prova"},
    ])
    assert [r["kind"] for r in rows] == ["class", "assessment"]
    # bloco que agrupa as duas linhas herda source_kind assessment (mais forte)
    assert _aggregate_source_kind(rows) == "assessment"
    block = {"source_kind": _aggregate_source_kind(rows), "unit_slug": "u1"}
    assert classify_block(block) == BlockKind.ASSESSMENT
```

- [ ] **Step 2: Run test to verify it fails (or passes once Task 1 done)**

Run: `python -m pytest tests/test_atividade_kind.py -k aggregate -v`
Expected: PASS após Task 1 (a derivação de kind alimenta `_aggregate_source_kind`). Se falhar, revisar Task 1.

- [ ] **Step 3: Verificação no syllabus real do TCC (dry, sem gravar)**

Run:
```bash
python -c "
import json
from pathlib import Path
from src.models.core import SubjectStore
import src.builder.engine as engine
sp = SubjectStore().get('Teoria da Computabilidade e Complexidade')
repo = Path(sp.repo_root)
cm = json.loads((repo/'manifest.json').read_text(encoding='utf-8')).get('course', {})
ctx = engine._build_file_map_timeline_context_from_course({**cm, '_repo_root': repo}, sp, content_taxonomy=None)
provas = [b for b in ctx['timeline_index']['blocks'] if b.get('source_kind') == 'assessment']
print('blocos com source_kind=assessment:', [(b['id'], b.get('period_label')) for b in provas])
" 2>&1 | grep -v "WARNING\|INFO\|approach\|load_reference"
```
Expected: lista NÃO vazia — os blocos das provas P1/P2 do TCC agora carregam `source_kind=assessment` (antes não tinham, pois o syllabus não tem `{kind=}`).

- [ ] **Step 4: Suíte completa**

Run: `python -m pytest -q`
Expected: PASS (anotar total). Atenção a regressões em `test_timeline_kinds.py` / `test_curation_conflicts.py` / `test_sarc_kind_flow.py`.

- [ ] **Step 5: Commit (se algo ajustado; senão, sem commit)**

```bash
git add tests/test_atividade_kind.py
git commit -m "test(timeline): integration — Atividade-derived prova rows reach assessment"
```

---

## Notas de execução

- `_ATIVIDADE_KIND_MAP` mapeia "prova/avaliacao/exame/teste"→assessment. Logo
  "Prova de Substituição"/"Prova de G2" (sem cor no syllabus-tabela) viram
  `assessment` em vez de ignorados (o ignore por cor só existe no parse HTML do
  SARC). Aceitável — são avaliações; não bloqueia. Registrar se o rebuild-diff
  do Plano 2 mostrar incômodo.
- Hook `code-review-graph.exe` imprime `UnicodeEncodeError` cosmético (cp1252) no
  commit; o commit **passa**. Ignorar.
- Trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- O Plano 2 (matcher posicional de unidade + rebuild-diff + bônus guard) é
  separado, escrito depois deste.
