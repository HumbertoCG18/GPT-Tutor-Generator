# Artifact Quality and Routing Indexes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar a rodada atual de otimização low-token melhorando a qualidade dos artefatos gerados (`COURSE_MAP`, `GLOSSARY`, `EXERCISE_INDEX`, slugs e placeholders) sem quebrar compatibilidade com `Reprocessar Repositório`.

**Architecture:** A implementação mantém a arquitetura `map-first`: artefatos curtos, roteáveis e reaplicáveis via build/reprocessamento. O foco aqui não é extrair mais conteúdo, e sim melhorar a qualidade do conteúdo já roteado, reduzir ruído, padronizar identificadores e tornar índices como `EXERCISE_INDEX.md` utilitários de verdade para o tutor.

**Tech Stack:** Python 3.11, `src/builder/engine.py`, `src/utils/helpers.py`, Markdown, pytest, Tkinter docs/help, artefatos do repositório gerado.

---

## File Structure

**Core generation**
- Modify: `src/utils/helpers.py`
  Responsibility: padronizar `slugify()` para uso técnico consistente e sem acentuação.
- Modify: `src/builder/engine.py`
  Responsibility: gerar artefatos low-token de melhor qualidade (`COURSE_MAP.md`, `GLOSSARY.md`, `EXERCISE_INDEX.md`), segmentar timeline sem sobreposição, decidir política de placeholders e propagar slugs normalizados.

**UI / docs / instructions**
- Modify: `src/ui/dialogs.py`
  Responsibility: atualizar a Central de Ajuda com o papel do `EXERCISE_INDEX.md`, política de placeholders e comportamento esperado de reprocessamento.
- Modify: `README.md`
  Responsibility: refletir a arquitetura final dos artefatos de navegação e prática.

**Tests**
- Modify: `tests/test_core.py`
  Responsibility: cobrir slug sem acento, timeline em português com segmentação, filtragem de ruído no glossário, política de placeholders e formato do `EXERCISE_INDEX.md`.

**Generated repo artifacts affected**
- Regenerated: `course/COURSE_MAP.md`
- Regenerated: `course/GLOSSARY.md`
- Regenerated: `exercises/EXERCISE_INDEX.md`
- Regenerated: instruções que mencionam slugs/unidades/índices

## Task 1: Normalizar slugs técnicos sem acentuação em todos os artefatos

**Files:**
- Modify: `src/utils/helpers.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_slugify_removes_accents_for_technical_ids():
    assert slugify("Métodos Formais") == "metodos-formais"
    assert slugify("Verificação de Programas") == "verificacao-de-programas"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::TestSlugify::test_slugify_removes_accents_for_technical_ids -v`
Expected: FAIL porque a implementação atual preserva acentos.

- [ ] **Step 3: Write minimal implementation**

```python
def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "untitled"
```

Propagar esse `slugify()` para os pontos em `src/builder/engine.py` que gravam `unit_slug`, `Unidade`, tabelas de índices e instruções.

- [ ] **Step 4: Run targeted tests**

Run: `pytest tests/test_core.py -k "slugify or timeline" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/utils/helpers.py src/builder/engine.py tests/test_core.py
git commit -m "refactor: normalize technical slugs without accents"
```

## Task 2: Filtrar melhor evidências ruins no GLOSSARY sem inflar tokens

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_glossary_ignores_evidence_with_author_noise():
    evidence = "Júlio Machado Conjuntos Indutivos 1."
    definition = _refine_glossary_definition_from_evidence(
        "Especificação de Conjuntos Indutivos",
        "métodos formais",
        evidence,
    )
    assert "júlio machado" not in definition.lower()

def test_glossary_prefers_short_semantic_sentence_over_fragment():
    docs = [{
        "title": "Linguagens de Especificação e Lógicas",
        "headings": ["Visão geral"],
        "text": "Técnicas de V&V formais requerem o uso de linguagens formais de especificação e fundamentos matemáticos sólidos.",
    }]
    evidence = _find_glossary_evidence(
        "Linguagens de Especificação e Lógicas",
        "Unidade 01 — Métodos Formais",
        docs,
    )
    assert "linguagens formais de especificação" in evidence.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core.py -k "glossary and (author_noise or semantic_sentence)" -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
def _is_bad_glossary_evidence(sentence: str) -> bool:
    lowered = sentence.lower().strip()
    if re.match(r"^[a-záàâãéêíóôõúç]+\s+[a-záàâãéêíóôõúç]+.*\b\d+\.$", lowered):
        return True
    if lowered.count("**") >= 2:
        return True
    return len(lowered) < 35
```

Aplicar esse filtro antes de aceitar sentenças de evidência. Manter a regra de 1 sentença curta por termo.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core.py -k "glossary" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "fix: filter noisy glossary evidence while keeping definitions compact"
```

## Task 3: Fortalecer os testes de timeline com casos reais em português

**Files:**
- Modify: `tests/test_core.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Write the failing test using a realistic Portuguese schedule**

```python
def test_timeline_segments_portuguese_schedule_without_overlap():
    timeline = _parse_syllabus_timeline(\"\"\"\
| # | Dia | Data | Descrição |
|---|---|---|---|
| 16 | SEG | 27/04/2026 | Lógica de Hoare |
| 17 | QUA | 29/04/2026 | Lógica de Hoare |
| 19 | QUA | 06/05/2026 | Lógica de Programas, Correção Parcial, Correção Total e Terminação, Invariantes de Laço |
| 20 | SEG | 11/05/2026 | Terminação, introdução ao Dafny |
| 30 | SEG | 15/06/2026 | Verificação de modelos, lógica temporal |
\"\"\")
    units = [
        ("Unidade 01 — Métodos Formais", ["Sistemas Formais"]),
        ("Unidade 02 — Verificação de Programas", ["Lógica de Hoare", "Correção Parcial e Total", "Invariante e Variante de Laço"]),
        ("Unidade 03 — Verificação de Modelos", ["Modelos de Kripke", "Lógica Temporal Linear"]),
    ]
    mapping = _match_timeline_to_units(timeline, units)
    assert mapping[1]["period"] == "27/04/2026 a 11/05/2026"
    assert mapping[0]["period"] == ""
    assert mapping[2]["period"] == "15/06/2026"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::TestMatchTimelineToUnits::test_timeline_segments_portuguese_schedule_without_overlap -v`
Expected: FAIL if overlap or block closure still regresses.

- [ ] **Step 3: Write minimal implementation**

```python
# inside _match_timeline_to_units_generic
anchor_indexes_by_unit = [...]
for unit_idx, descriptor in enumerate(descriptors):
    start_idx = anchors[0]
    next_start_idx = first_anchor_of_next_unit(...)
    end_idx = next_start_idx - 1 if next_start_idx is not None else anchors[-1]
```

Se necessário, ajustar o threshold de score para evitar que “Exercícios” sozinho seja âncora de unidade.

- [ ] **Step 4: Run timeline test suite**

Run: `pytest tests/test_core.py -k "timeline" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "test: harden portuguese timeline segmentation coverage"
```

## Task 4: Definir e implementar a política de placeholders vazios

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `README.md`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_course_map_omits_exam_incidence_table_when_no_exam_signal():
    result = course_map_md({"course_name": "Teste"}, subject_profile=None)
    assert "Tópicos de alta incidência em prova" not in result

def test_exercise_index_keeps_actionable_placeholder_only_when_empty():
    result = exercise_index_md({"course_name": "Teste"}, [])
    assert "[a preencher]" in result
    assert "Mapeamento de exercícios por tópico" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core.py -k "placeholders or exam_incidence or exercise_index" -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
def _render_optional_section(title: str, body_lines: List[str]) -> List[str]:
    meaningful = [line for line in body_lines if line.strip() and "[a preencher]" not in line]
    if not meaningful:
        return []
    return [f"## {title}", ""] + body_lines + [""]
```

Aplicar política:
- `COURSE_MAP.md`: omitir seção de incidência em prova se não houver sinal real.
- `EXERCISE_INDEX.md`: manter um placeholder enxuto só na tabela principal quando não existirem listas; omitir tabela secundária vazia.
- `Notas do professor`: manter só se houver conteúdo real ou orientação operacional relevante.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core.py -k "placeholders or exercise_index or course_map" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py src/ui/dialogs.py README.md tests/test_core.py
git commit -m "refactor: omit empty navigation placeholders and document policy"
```

## Task 5: Refatorar `EXERCISE_INDEX.md` para virar roteador de prática

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `README.md`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_exercise_index_is_a_routing_table_not_a_blank_template():
    entries = [
        FileEntry(title="Lista 1", source_path="raw/lista1.pdf", category="listas", tags="unidade-01", notes="Tem gabarito"),
        FileEntry(title="P1 2025", source_path="raw/p1-2025.pdf", category="provas", tags="unidade-01;unidade-02", notes="Alta incidência"),
    ]
    result = exercise_index_md({"course_name": "Teste"}, entries)
    assert "| Recurso | Tipo | Unidade | Solução | Prioridade | Quando usar |" in result
    assert "Mapeamento de exercícios por tópico" not in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_exercise_index_is_a_routing_table_not_a_blank_template -v`
Expected: FAIL because the current index is still a generic template with empty mapping table.

- [ ] **Step 3: Write minimal implementation**

```python
def exercise_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    lines = [
        f"# EXERCISE_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice operacional de prática da disciplina.",
        "> Consulte este arquivo para localizar listas, provas antigas e exercícios por unidade e prioridade.",
        "",
        "| Recurso | Tipo | Unidade | Solução | Prioridade | Quando usar |",
        "|---|---|---|---|---|---|",
    ]
```

Mapear:
- `Tipo` a partir da categoria (`listas`, `provas`, `exercicios`, etc.)
- `Unidade` a partir de `tags` / notas quando houver
- `Solução` por pistas em `notes`
- `Prioridade` com heurística simples (`provas` e listas com gabarito → alta)
- `Quando usar` com texto curto (`fixação`, `revisão de prova`, `prática adicional`)

- [ ] **Step 4: Run focused tests**

Run: `pytest tests/test_core.py -k "exercise_index" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py src/ui/dialogs.py README.md tests/test_core.py
git commit -m "feat: turn exercise index into a low-token practice router"
```

## Task 6: Fechamento de instruções e validação de reprocessamento

**Files:**
- Modify: `README.md`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_reprocess_regenerates_slug_glossary_course_map_and_exercise_index(tmp_path):
    # fixture repo with stale accented slug and old exercise index
    ...
    builder.incremental_build([])
    assert "verificacao-de-programas" in (repo / "course" / "COURSE_MAP.md").read_text(encoding="utf-8")
    assert "# EXERCISE_INDEX" in (repo / "exercises" / "EXERCISE_INDEX.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_reprocess_regenerates_slug_glossary_course_map_and_exercise_index -v`
Expected: FAIL before all regeneration points are wired.

- [ ] **Step 3: Write minimal implementation**

```python
# ensure _regenerate_pedagogical_files rewrites:
write_text(self.root_dir / "course" / "COURSE_MAP.md", ...)
write_text(self.root_dir / "course" / "GLOSSARY.md", ...)
write_text(self.root_dir / "exercises" / "EXERCISE_INDEX.md", ...)
```

Atualizar docs/help para explicar:
- `EXERCISE_INDEX.md` é índice operacional, não template para apostila
- placeholders vazios são omitidos por padrão
- `Reprocessar Repositório` reaplica slugs, timeline, glossário e índices

- [ ] **Step 4: Run full core suite**

Run: `pytest tests/test_core.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py src/ui/dialogs.py README.md tests/test_core.py
git commit -m "docs: align routing artifacts and reprocessing behavior"
```

## Self-Review

**Spec coverage**
- Slug sem acento em todos os artefatos: coberto na Task 1.
- Revisão de definições ruins do glossário: coberto na Task 2.
- Timeline com mais casos reais em português: coberto na Task 3.
- Política de placeholders vazios: coberto na Task 4.
- Definição clara e útil para `EXERCISE_INDEX.md`: coberto na Task 5.
- Compatibilidade com `Reprocessar Repositório`: coberto na Task 6.
- Fechar rodada de otimização para depois reavaliar outros subsistemas (`Curator`, `Ollama`, etc.): este plano fecha os artefatos de navegação e prática; a revisão dos curators/vision fica como etapa posterior de auditoria, não misturada aqui.

**Placeholder scan**
- Sem `TODO`, `TBD` ou “similar à task anterior”.
- Cada task inclui arquivos, testes, comandos e implementação mínima.

**Type consistency**
- Funções e arquivos referenciados já existem no código atual (`slugify`, `course_map_md`, `exercise_index_md`, `incremental_build`).
- O plano assume apenas helpers pequenos adicionais dentro de `src/builder/engine.py`, sem criar camadas novas desnecessárias.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-01-artifact-quality-and-routing-indexes.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
