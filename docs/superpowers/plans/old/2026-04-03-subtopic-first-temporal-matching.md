# Subtopic-First Temporal Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refatorar o mapeamento pedagógico para decidir `subtópico -> unidade -> bloco temporal`, substituindo o modelo atual centrado em unidade por uma arquitetura mais precisa, depurável e robusta para todos os repositórios.

**Architecture:** O sistema passa a construir uma taxonomia oficial da disciplina a partir de `teaching_plan`, `COURSE_MAP` e `GLOSSARY`, usar essa taxonomia para classificar cada entry primeiro no nível de subtópico, derivar a unidade a partir do subtópico vencedor e só então localizar o bloco temporal mais provável dentro dessa unidade. O cronograma deixa de ser a fonte principal da unidade; ele vira refinador temporal. Dados de avaliação entram em paralelo apenas para detectar inconsistências entre cobertura de prova e cronograma, sem sobrescrever o match conceitual.

**Tech Stack:** Python, markdown parsing leve, JSON interno (`.timeline_index.json`, `.content_taxonomy.json`), pytest, Tkinter dialogs existentes, pipeline estrutural em `src/builder/engine.py`.

---

## File Structure

**Create:**
- `docs/superpowers/plans/2026-04-03-subtopic-first-temporal-matching.md`
- `tests/fixtures/subtopic_taxonomy_cases.py`

**Modify:**
- `src/builder/engine.py`
- `tests/test_file_map_unit_mapping.py`
- `tests/test_core.py`

**Responsibilities:**
- `src/builder/engine.py`
  - gerar taxonomia oficial da disciplina
  - classificar entry por subtópico
  - derivar unidade a partir do subtópico vencedor
  - anotar blocos do cronograma com subtópicos candidatos
  - gerar `.content_taxonomy.json` e o novo `.timeline_index.json`
  - fazer `COURSE_MAP.md` e `FILE_MAP.md` consumirem esse pipeline
- `tests/fixtures/subtopic_taxonomy_cases.py`
  - fixtures de disciplinas e casos reais/limítrofes
- `tests/test_file_map_unit_mapping.py`
  - testes do matcher `subtópico -> unidade -> bloco`
- `tests/test_core.py`
  - testes de integração dos artefatos estruturais e regressões do fluxo do app

## Architectural Contract

1. **Conteúdo primeiro, tempo depois, avaliação em paralelo**
   - `subtópico` é a primeira decisão
   - `unidade` é derivada do subtópico
   - `bloco temporal` é escolhido dentro da unidade
   - `avaliação` não redefine unidade nem bloco; só produz alertas de inconsistência

2. **Taxonomia oficial por disciplina**
   - toda disciplina gera seu próprio `course/.content_taxonomy.json`
   - não existe taxonomia global entre repositórios
   - fontes permitidas:
     - `SubjectProfile.teaching_plan`
     - `COURSE_MAP.md`
     - `GLOSSARY.md`
     - headings fortes do conteúdo curado apenas como reforço controlado

3. **Cutover por estrangulamento**
   - o pipeline novo entra em paralelo ao legado
   - `FILE_MAP.md` e `COURSE_MAP.md` passam a consumir o novo caminho
   - só depois removemos o matcher legado baseado em unidade macro

4. **Regra estrutural**
   - `course/.content_taxonomy.json`, `course/.timeline_index.json`, `COURSE_MAP.md` e `FILE_MAP.md` são artefatos estruturais
   - devem ser recalculados em `_regenerate_pedagogical_files(...)`
   - isso vale para:
     - `build()`
     - `incremental_build()`
     - `process_single()`
     - `Reprocessar Repositório`
   - não podem depender da existência de arquivos novos

5. **Low-token**
   - `.content_taxonomy.json` e `.timeline_index.json` são internos do app
   - tutor não é instruído a ler esses arquivos por padrão
   - `FILE_MAP.md` expõe só:
     - `Unidade`
     - `Período`
     - opcionalmente rastreabilidade curta

## Runtime Model

### 1. Taxonomia oficial

Exemplo de `course/.content_taxonomy.json`:

```json
{
  "version": 1,
  "course_slug": "metodos-formais",
  "units": [
    {
      "slug": "unidade-01-metodos-formais",
      "title": "Unidade 01  Métodos Formais",
      "topics": [
        {
          "code": "1.1",
          "slug": "sistemas-formais",
          "label": "Sistemas Formais",
          "aliases": ["sistema formal"],
          "kind": "topic",
          "unit_slug": "unidade-01-metodos-formais"
        },
        {
          "code": "1.3.3",
          "slug": "provadores-de-teoremas",
          "label": "Provadores de Teoremas",
          "aliases": ["isabelle", "prova interativa de teoremas"],
          "kind": "subtopic",
          "unit_slug": "unidade-01-metodos-formais"
        }
      ]
    }
  ]
}
```

### 2. Matching de entry

O pipeline de decisão passa a ser:

```text
entry
  -> sinais do arquivo (title, markdown, category, manual_tags, auto_tags)
  -> score contra tópicos/subtópicos da taxonomia
  -> subtópico vencedor
  -> unidade derivada do subtópico vencedor
  -> score temporal apenas contra blocos dessa unidade
  -> período provável
```

### 3. Matching de blocos do cronograma

Cada bloco do cronograma recebe:
- `topic_candidates`
- `primary_topic_slug`
- `unit_slug` derivada do tópico vencedor, não da string da unidade no bloco
- `assessment_conflicts`

Exemplo:

```json
{
  "id": "bloco-07",
  "period_label": "06/04/2026 a 08/04/2026",
  "primary_topic_slug": "provadores-de-teoremas",
  "topic_candidates": [
    {"topic_slug": "provadores-de-teoremas", "score": 1.62},
    {"topic_slug": "verificacao-de-programas", "score": 0.31}
  ],
  "unit_slug": "unidade-01-metodos-formais",
  "assessment_conflicts": []
}
```

### 4. Conflitos com avaliação

Exemplo real de Métodos Formais:
- avaliação diz: `P1 cobre unidades 1 e 2`
- cronograma diz: `Lógica de Hoare` aparece só depois da P1

O sistema não deve “forçar” `Lógica de Hoare` para antes da prova. Ele deve registrar:

```json
{
  "assessment_id": "p1",
  "declared_units": ["unidade-01-metodos-formais", "unidade-02-verificacao-de-programas"],
  "timeline_coverage_until_exam": ["unidade-01-metodos-formais"],
  "warning": "Plano de avaliação menciona unidade 2 antes de tópicos explícitos da unidade 2 aparecerem no cronograma."
}
```

Esse warning é interno ou vai para observação curta no `COURSE_MAP.md`, nunca redefine o match do conteúdo.

## Task 1: Add a Discipline Content Taxonomy

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/fixtures/subtopic_taxonomy_cases.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Write the failing tests for taxonomy generation**

```python
from src.builder.engine import _build_content_taxonomy


def test_build_content_taxonomy_emits_unit_topic_tree():
    taxonomy = _build_content_taxonomy(
        teaching_plan="""
        Unidade 01 - Métodos Formais
        1.3.3 Provadores de Teoremas
        Unidade 02 - Verificação de Programas
        2.1 Lógica de Hoare
        """,
        course_map_md="# COURSE_MAP",
        glossary_md="""
        ## Provadores de Teoremas
        **Aparece em:** Unidade 01

        ## Lógica de Hoare
        **Aparece em:** Unidade 02
        """,
    )
    unit_slugs = [unit["slug"] for unit in taxonomy["units"]]
    assert "unidade-01-metodos-formais" in unit_slugs
    assert "unidade-02-verificacao-de-programas" in unit_slugs
    topic_slugs = {
        topic["slug"]
        for unit in taxonomy["units"]
        for topic in unit["topics"]
    }
    assert "provadores-de-teoremas" in topic_slugs
    assert "logica-de-hoare" in topic_slugs


def test_build_content_taxonomy_keeps_topics_repo_scoped():
    taxonomy = _build_content_taxonomy(
        teaching_plan="Unidade 01 - Métodos Formais\n1.1 Sistemas Formais",
        course_map_md="# COURSE_MAP",
        glossary_md="## Sistemas Formais\n**Aparece em:** Unidade 01",
    )
    topic_slugs = {
        topic["slug"]
        for unit in taxonomy["units"]
        for topic in unit["topics"]
    }
    assert "sistemas-formais" in topic_slugs
    assert "logica-de-hoare" not in topic_slugs
```

- [ ] **Step 2: Run the taxonomy tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests\test_file_map_unit_mapping.py -k taxonomy -q`
Expected: FAIL with `ImportError` or missing `_build_content_taxonomy`

- [ ] **Step 3: Implement the taxonomy builder and serializer**

```python
def _build_content_taxonomy(teaching_plan: str, course_map_md: str, glossary_md: str) -> dict:
    parsed_units = _build_file_map_unit_index(teaching_plan)
    glossary_terms = _parse_glossary_terms(glossary_md)
    units = []
    for unit in parsed_units:
        unit_topics = []
        for phrase in unit.get("topic_phrases", []) or []:
            unit_topics.append({
                "code": _extract_topic_code(phrase),
                "slug": slugify(_strip_topic_code(phrase)),
                "label": _strip_topic_code(phrase),
                "aliases": _lookup_taxonomy_aliases(_strip_topic_code(phrase), glossary_terms),
                "kind": "subtopic" if "." in (_extract_topic_code(phrase) or "") else "topic",
                "unit_slug": unit["slug"],
            })
        units.append({
            "slug": unit["slug"],
            "title": unit["title"],
            "topics": _dedupe_taxonomy_topics(unit_topics),
        })
    return {"version": 1, "course_slug": slugify(_infer_course_name_from_map(course_map_md)), "units": units}


def _write_internal_content_taxonomy(root_dir: Path, taxonomy: dict) -> None:
    write_text(
        root_dir / "course" / ".content_taxonomy.json",
        json.dumps(taxonomy, ensure_ascii=False, indent=2),
    )
```

- [ ] **Step 4: Run tests to verify taxonomy generation passes**

Run: `.\.venv\Scripts\python -m pytest tests\test_file_map_unit_mapping.py -k taxonomy -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py tests/fixtures/subtopic_taxonomy_cases.py docs/superpowers/plans/2026-04-03-subtopic-first-temporal-matching.md
git commit -m "feat: add content taxonomy index for subtopic matching"
```

## Task 2: Make Entry Matching Subtopic-First

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Write the failing tests for subtopic-first matching**

```python
from src.builder.engine import _auto_map_entry_subtopic, _derive_unit_from_topic_match


def test_auto_map_entry_subtopic_prefers_specific_topic_over_unit_title():
    taxonomy = {
        "units": [
            {
                "slug": "unidade-01-metodos-formais",
                "topics": [{"slug": "provadores-de-teoremas", "label": "Provadores de Teoremas", "aliases": ["isabelle"], "unit_slug": "unidade-01-metodos-formais"}],
            },
            {
                "slug": "unidade-02-verificacao-de-programas",
                "topics": [{"slug": "logica-de-hoare", "label": "Lógica de Hoare", "aliases": ["pre e pos condicoes"], "unit_slug": "unidade-02-verificacao-de-programas"}],
            },
        ]
    }
    entry = {"title": "Prova Interativa de Teoremas - Isabelle", "category": "material-de-aula", "manual_tags": [], "auto_tags": ["ferramenta:isabelle"]}
    match = _auto_map_entry_subtopic(entry, taxonomy, "Isabelle theorem proving")
    assert match.topic_slug == "provadores-de-teoremas"
    assert _derive_unit_from_topic_match(match, taxonomy) == "unidade-01-metodos-formais"


def test_auto_map_entry_subtopic_maps_hoare_to_unit_two():
    taxonomy = {
        "units": [
            {
                "slug": "unidade-02-verificacao-de-programas",
                "topics": [{"slug": "logica-de-hoare", "label": "Lógica de Hoare", "aliases": ["pre e pos condicoes"], "unit_slug": "unidade-02-verificacao-de-programas"}],
            }
        ]
    }
    entry = {"title": "Exerciciosespecificacao", "category": "lista", "manual_tags": [], "auto_tags": ["topico:logica-de-hoare"]}
    match = _auto_map_entry_subtopic(entry, taxonomy, "Pré e pós condições\nCorreção parcial e total")
    assert match.topic_slug == "logica-de-hoare"
    assert _derive_unit_from_topic_match(match, taxonomy) == "unidade-02-verificacao-de-programas"
```

- [ ] **Step 2: Run the subtopic matching tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests\test_file_map_unit_mapping.py -k subtopic -q`
Expected: FAIL with missing helper functions

- [ ] **Step 3: Implement subtopic-first scoring**

```python
@dataclass
class TopicMatch:
    topic_slug: str = ""
    unit_slug: str = ""
    confidence: float = 0.0
    ambiguous: bool = True
    reasons: List[str] = field(default_factory=list)


def _auto_map_entry_subtopic(entry: dict, taxonomy: dict, markdown_text: str) -> TopicMatch:
    signals = _collect_entry_unit_signals(entry, markdown_text)
    candidates = []
    for unit in taxonomy.get("units", []) or []:
        for topic in unit.get("topics", []) or []:
            score = _score_entry_against_taxonomy_topic(signals, topic)
            if score > 0:
                candidates.append((topic, score))
    if not candidates:
        return TopicMatch(reasons=["sem-topico"])
    candidates.sort(key=lambda item: item[1], reverse=True)
    winner, winner_score = candidates[0]
    runner_up = candidates[1][1] if len(candidates) > 1 else 0.0
    if winner_score < 1.0 or abs(winner_score - runner_up) < 0.30:
        return TopicMatch(topic_slug=winner["slug"], unit_slug=winner["unit_slug"], confidence=winner_score, ambiguous=True, reasons=["score-baixo-ou-empate"])
    return TopicMatch(topic_slug=winner["slug"], unit_slug=winner["unit_slug"], confidence=min(1.0, winner_score / 2.5), ambiguous=False, reasons=["topico-vencedor"])


def _derive_unit_from_topic_match(match: TopicMatch, taxonomy: dict) -> str:
    return match.unit_slug if match and match.topic_slug else ""
```

- [ ] **Step 4: Wire `FILE_MAP` to derive unit from topic match before timeline matching**

```python
taxonomy = _build_content_taxonomy(teaching_plan, course_map_md, glossary_md)
topic_match = _auto_map_entry_subtopic(entry, taxonomy, markdown_text)
derived_unit_slug = _derive_unit_from_topic_match(topic_match, taxonomy)
if manual_unit_slug:
    unit_slug = manual_unit_slug
else:
    unit_slug = derived_unit_slug
```

- [ ] **Step 5: Run the focused tests**

Run: `.\.venv\Scripts\python -m pytest tests\test_file_map_unit_mapping.py -k "subtopic or manual_unit" -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: derive file map units from subtopic matches"
```

## Task 3: Annotate Timeline Blocks by Subtopic, Then Derive Unit

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/fixtures/subtopic_taxonomy_cases.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Write the failing tests for timeline block topic derivation**

```python
from datetime import datetime
from src.builder.engine import _build_timeline_index


def test_build_timeline_index_sets_primary_topic_before_unit():
    rows = [
        {"index": 1, "date_text": "06/04/2026", "date_dt": datetime(2026, 4, 6), "content": "Prova interativa de teoremas - Isabelle"},
        {"index": 2, "date_text": "08/04/2026", "date_dt": datetime(2026, 4, 8), "content": "Prova interativa de teoremas - Isabelle"},
    ]
    unit_index = [{"slug": "unidade-01-metodos-formais", "title": "Unidade 01 Métodos Formais"}]
    taxonomy = {
        "units": [
            {
                "slug": "unidade-01-metodos-formais",
                "topics": [{"slug": "provadores-de-teoremas", "label": "Provadores de Teoremas", "aliases": ["isabelle"], "unit_slug": "unidade-01-metodos-formais"}],
            }
        ]
    }
    timeline = _build_timeline_index(rows, unit_index=unit_index, taxonomy=taxonomy)
    block = timeline["blocks"][0]
    assert block["primary_topic_slug"] == "provadores-de-teoremas"
    assert block["unit_slug"] == "unidade-01-metodos-formais"
```

- [ ] **Step 2: Run the timeline block tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests\test_file_map_unit_mapping.py -k timeline_index -q`
Expected: FAIL because `_build_timeline_index` does not accept `taxonomy`

- [ ] **Step 3: Implement topic-first block annotation**

```python
def _assign_timeline_block_to_topic(block: Dict[str, object], taxonomy: dict) -> tuple[str, List[dict]]:
    block_text = _normalize_match_text(" ".join(str(row.get("content", "")) for row in block.get("rows", []) or []))
    scored = []
    for unit in taxonomy.get("units", []) or []:
        for topic in unit.get("topics", []) or []:
            score = _score_block_against_taxonomy_topic(block_text, topic)
            if score > 0:
                scored.append({
                    "topic_slug": topic["slug"],
                    "unit_slug": topic["unit_slug"],
                    "score": score,
                })
    scored.sort(key=lambda item: item["score"], reverse=True)
    primary = scored[0]["topic_slug"] if scored and scored[0]["score"] >= 1.0 else ""
    return primary, scored[:3]


def _build_timeline_index(candidate_rows: List[Dict[str, object]], unit_index: list, taxonomy: Optional[dict] = None) -> dict:
    runtime_blocks = []
    blocks = _group_rows_into_thematic_blocks(candidate_rows)
    for position, rows in enumerate(blocks, start=1):
        topics, aliases, topic_text = _extract_timeline_topics(rows)
        runtime_block = {
            "id": f"bloco-{position:02d}",
            "period_start": rows[0]["date_dt"].strftime("%Y-%m-%d") if rows[0].get("date_dt") else "",
            "period_end": rows[-1]["date_dt"].strftime("%Y-%m-%d") if rows[-1].get("date_dt") else "",
            "period_label": _timeline_period_label(rows[0].get("date_text", ""), rows[-1].get("date_text", "")),
            "topics": topics,
            "aliases": aliases,
            "topic_text": topic_text,
            "rows": rows,
        }
        primary_topic_slug, topic_candidates = _assign_timeline_block_to_topic(runtime_block, taxonomy or {"units": []})
        runtime_block["primary_topic_slug"] = primary_topic_slug
        runtime_block["topic_candidates"] = topic_candidates
        runtime_block["unit_slug"] = topic_candidates[0]["unit_slug"] if topic_candidates and topic_candidates[0]["score"] >= 1.0 else ""
        runtime_blocks.append(runtime_block)
    return {"version": 1, "blocks": runtime_blocks}
```

- [ ] **Step 4: Run the block tests**

Run: `.\.venv\Scripts\python -m pytest tests\test_file_map_unit_mapping.py -k timeline_index -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py tests/fixtures/subtopic_taxonomy_cases.py
git commit -m "feat: annotate timeline blocks with primary subtopics"
```

## Task 4: Select Period by Matching Entry Against Blocks Inside the Derived Unit

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Write the failing tests for derived-unit block selection**

```python
from src.builder.engine import _select_probable_period_for_entry


def test_select_probable_period_uses_only_blocks_inside_derived_unit():
    entry = {"title": "Exerciciosformalizacaoalgoritmosrecursao", "category": "lista", "manual_tags": [], "auto_tags": ["topico:funcoes-recursivas"]}
    unit = {"slug": "unidade-01-metodos-formais"}
    candidate_blocks = [
        {"id": "bloco-02", "unit_slug": "unidade-01-metodos-formais", "unit_confidence": 0.82, "period_label": "16/03/2026 a 25/03/2026", "topic_text": "funcoes recursivas listas arvores", "rows": [{"content": "definicoes indutivas e recursivas"}]},
        {"id": "bloco-09", "unit_slug": "unidade-02-verificacao-de-programas", "unit_confidence": 0.90, "period_label": "27/04/2026 a 04/05/2026", "topic_text": "logica de hoare", "rows": [{"content": "pre e pos condicoes"}]},
    ]
    period, confidence, ambiguous, reasons = _select_probable_period_for_entry(entry, unit, candidate_blocks, "Funções recursivas sobre árvores")
    assert period == "16/03/2026 a 25/03/2026"
    assert ambiguous is False
```

- [ ] **Step 2: Run the period selection tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests\test_file_map_unit_mapping.py -k probable_period -q`
Expected: FAIL due to cross-unit scoring

- [ ] **Step 3: Restrict temporal matching to derived unit first**

```python
def _select_probable_period_for_entry(entry: dict, unit: dict, candidate_rows: List[Dict[str, object]], markdown_text: str) -> tuple[str, float, bool, List[str]]:
    signals = _collect_entry_unit_signals(entry, markdown_text)
    blocks = list(candidate_rows)
    preferred_unit_slug = str(unit.get("slug", "") or "")
    scoped_blocks = [
        block for block in blocks
        if not preferred_unit_slug or str(block.get("unit_slug", "") or "") in ("", preferred_unit_slug)
    ]
    if preferred_unit_slug and any(str(block.get("unit_slug", "") or "") == preferred_unit_slug for block in blocks):
        blocks = [block for block in scoped_blocks if str(block.get("unit_slug", "") or "") == preferred_unit_slug]
    else:
        blocks = scoped_blocks or blocks
```

- [ ] **Step 4: Run the period tests**

Run: `.\.venv\Scripts\python -m pytest tests\test_file_map_unit_mapping.py -k probable_period -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: scope timeline matching to derived unit"
```

## Task 5: Detect Assessment vs Timeline Inconsistencies

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for assessment conflict detection**

```python
from src.builder.engine import _detect_assessment_timeline_conflicts


def test_detect_assessment_timeline_conflicts_flags_declared_unit_before_topics():
    assessments = [
        {"id": "p1", "label": "P1", "date": "2026-04-22", "declared_unit_slugs": ["unidade-01-metodos-formais", "unidade-02-verificacao-de-programas"]},
    ]
    timeline_index = {
        "blocks": [
            {"period_end": "2026-04-08", "unit_slug": "unidade-01-metodos-formais"},
            {"period_start": "2026-04-27", "period_end": "2026-05-06", "unit_slug": "unidade-02-verificacao-de-programas"},
        ]
    }
    conflicts = _detect_assessment_timeline_conflicts(assessments, timeline_index)
    assert conflicts[0]["assessment_id"] == "p1"
    assert conflicts[0]["declared_units"] == ["unidade-01-metodos-formais", "unidade-02-verificacao-de-programas"]
```

- [ ] **Step 2: Run the conflict tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k assessment_conflict -q`
Expected: FAIL because helper is missing

- [ ] **Step 3: Implement conflict detection without changing matching output**

```python
def _detect_assessment_timeline_conflicts(assessments: List[dict], timeline_index: dict) -> List[dict]:
    warnings = []
    blocks = list((timeline_index or {}).get("blocks", []) or [])
    for assessment in assessments:
        exam_date = str(assessment.get("date", "") or "")
        if not exam_date:
            continue
        covered = sorted({
            str(block.get("unit_slug", "") or "")
            for block in blocks
            if str(block.get("unit_slug", "") or "") and str(block.get("period_start", "") or "") <= exam_date
        })
        declared = list(assessment.get("declared_unit_slugs", []) or [])
        if declared and any(unit not in covered for unit in declared):
            warnings.append({
                "assessment_id": assessment.get("id", ""),
                "declared_units": declared,
                "timeline_coverage_until_exam": covered,
                "warning": "Plano de avaliação antecipa unidade sem cobertura explícita no cronograma.",
            })
    return warnings
```

- [ ] **Step 4: Surface warnings in `.timeline_index.json` and a short note in `COURSE_MAP.md`**

```python
timeline_index["assessment_conflicts"] = _detect_assessment_timeline_conflicts(assessment_index, timeline_index)
if timeline_index["assessment_conflicts"]:
    lines.append("## Alertas de consistência")
    for item in timeline_index["assessment_conflicts"]:
        lines.append(f"- `{item['assessment_id']}`: {item['warning']}")
```

- [ ] **Step 5: Run the focused tests**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k assessment_conflict -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: detect assessment and timeline inconsistencies"
```

## Task 6: Regenerate Structural Artifacts from the New Pipeline

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for structural regeneration**

```python
def test_regenerate_pedagogical_files_writes_taxonomy_and_timeline_indexes(tmp_path):
    builder = make_builder(tmp_path)
    builder._regenerate_pedagogical_files([])
    assert (tmp_path / "course" / ".content_taxonomy.json").exists()
    assert (tmp_path / "course" / ".timeline_index.json").exists()


def test_reprocess_path_recomputes_taxonomy_without_new_entries(tmp_path):
    builder = make_builder(tmp_path)
    builder.incremental_build([])
    assert (tmp_path / "course" / ".content_taxonomy.json").exists()
```

- [ ] **Step 2: Run the structural tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "taxonomy_and_timeline_indexes or recomputes_taxonomy" -q`
Expected: FAIL because `.content_taxonomy.json` is not written

- [ ] **Step 3: Wire taxonomy + timeline generation into `_regenerate_pedagogical_files(...)`**

```python
course_map_text = _low_token_course_map_md(self.root_dir, self.subject_profile, timeline_context=None)
glossary_text = _low_token_glossary_md(self.root_dir, self.subject_profile)
taxonomy = _build_content_taxonomy(
    getattr(self.subject_profile, "teaching_plan", "") or "",
    course_map_text,
    glossary_text,
)
_write_internal_content_taxonomy(self.root_dir, taxonomy)
timeline_context = _build_file_map_timeline_context(
    getattr(self.subject_profile, "syllabus", "") or "",
    getattr(self.subject_profile, "teaching_plan", "") or "",
    taxonomy=taxonomy,
)
_write_internal_timeline_index(self.root_dir, timeline_context.get("timeline_index", _empty_timeline_index()))
```

- [ ] **Step 4: Run the structural tests**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "taxonomy_and_timeline_indexes or recomputes_taxonomy" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: regenerate taxonomy and timeline indexes structurally"
```

## Task 7: Cut Over FILE_MAP and COURSE_MAP to the New Pipeline

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing end-to-end tests for FILE_MAP/COURSE_MAP**

```python
def test_file_map_uses_subtopic_derived_unit_before_period():
    file_map = render_file_map_for_formal_methods_case()
    assert "| Exerciciosformalizacaoalgoritmosrecursao |" in file_map
    assert "unidade-01-metodos-formais" in file_map
    assert "16/03/2026 a 25/03/2026" in file_map


def test_course_map_aggregates_unit_periods_from_subtopic_annotated_blocks():
    course_map = render_course_map_for_formal_methods_case()
    assert "| Unidade 01  Métodos Formais | 02/03/2026 a 25/03/2026 |" in course_map
```

- [ ] **Step 2: Run the end-to-end tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_file_map_unit_mapping.py tests/test_core.py -k "formal_methods_case or aggregates_unit_periods" -q`
Expected: FAIL with old unit-first behavior

- [ ] **Step 3: Replace the old unit-macro shortcuts in FILE_MAP and COURSE_MAP**

```python
# FILE_MAP
topic_match = _auto_map_entry_subtopic(entry, taxonomy, markdown_text)
derived_unit_slug = manual_unit_slug or topic_match.unit_slug
period, period_confidence, period_ambiguous, reasons = _select_probable_period_for_entry(
    entry,
    {"slug": derived_unit_slug},
    list(blocks_by_unit.get(derived_unit_slug, [])),
    markdown_text,
)

# COURSE_MAP
blocks_by_unit = timeline_context.get("blocks_by_unit", {})
period_map = _aggregate_unit_periods_from_blocks(blocks_by_unit)
```

- [ ] **Step 4: Keep manual overrides last-write-wins**

```python
if entry.get("manual_unit_slug"):
    derived_unit_slug = _resolve_entry_manual_unit_slug(entry, unit_index)
if entry.get("manual_timeline_block_id"):
    manual_block = _resolve_entry_manual_timeline_block(entry, timeline_context)
    if manual_block:
        period = manual_block.get("period_label", "")
```

- [ ] **Step 5: Run the full focused suite**

Run: `.\.venv\Scripts\python -m pytest tests/test_file_map_unit_mapping.py tests/test_core.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py tests/test_core.py
git commit -m "refactor: cut over mapping pipeline to subtopic-first matching"
```

## Task 8: Remove or Quarantine the Legacy Unit-Macro Path

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing regression test that legacy path is no longer primary**

```python
def test_file_map_no_longer_uses_unit_macro_period_when_subtopic_match_exists():
    file_map = render_file_map_for_formal_methods_case()
    assert "04/03/2026 a 04/05/2026" not in file_map
```

- [ ] **Step 2: Run the regression test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k unit_macro_period -q`
Expected: FAIL if any old macro shortcut still leaks

- [ ] **Step 3: Remove or quarantine legacy helpers behind narrow fallback**

```python
def _legacy_unit_macro_period(entry: dict, unit_slug: str, timeline_context: dict) -> str:
    return ""


def _match_timeline_to_units(timeline: List[dict], units: List[dict]):
    # retained only for backward-compatible COURSE_MAP fallback when no taxonomy or no candidate rows
    if not timeline or not units:
        return []
    return _match_timeline_to_units_generic(timeline, units)
```

- [ ] **Step 4: Run the regression test and the full suite**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py tests/test_file_map_unit_mapping.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py tests/test_file_map_unit_mapping.py
git commit -m "refactor: remove legacy macro-period path from file mapping"
```

## Self-Review

**Spec coverage:**
- Subtópico-first: coberto nas Tasks 1 e 2
- Unidade derivada do subtópico: coberto nas Tasks 2 e 7
- Timeline-second: coberto nas Tasks 3 e 4
- Conflito avaliação vs cronograma: coberto na Task 5
- Reprocessamento e build estrutural: coberto na Task 6
- Cutover e remoção do legado: coberto nas Tasks 7 e 8

**Placeholder scan:**
- não há `TODO`, `TBD` ou “similar a”
- cada task contém comandos e código concretos

**Type consistency:**
- taxonomia usa `unit_slug`, `topic_slug`, `aliases`
- matching usa `TopicMatch`
- override manual continua em `manual_unit_slug` e `manual_timeline_block_id`

## How It Works in Practice

### Cenário bom: `Isabelle`

1. A taxonomia oficial da disciplina contém:
   - `1.3.3 Provadores de Teoremas`
   - alias `isabelle`
2. O arquivo `Prova Interativa de Teoremas - Isabelle` gera sinais:
   - título com `isabelle`
   - markdown com `theorem proving`
   - `auto_tags` com `ferramenta:isabelle`
3. O matcher escolhe primeiro `provadores-de-teoremas`
4. A unidade é derivada automaticamente como `unidade-01-metodos-formais`
5. O cronograma é consultado só dentro dessa unidade
6. O bloco `06/04/2026 a 08/04/2026` vence
7. `FILE_MAP.md` mostra:
   - unidade 1
   - período `06/04/2026 a 08/04/2026`

### Cenário bom: `Lógica de Hoare`

1. A taxonomia oficial contém:
   - `2.1 Lógica de Hoare`
   - `2.1.1 Pré e Pós Condições`
2. O arquivo `Exerciciosespecificacao` contém:
   - markdown com `pré e pós condições`
   - `auto_tags` com `topico:logica-de-hoare`
3. O matcher escolhe o subtópico `logica-de-hoare`
4. A unidade derivada é `unidade-02-verificacao-de-programas`
5. O cronograma procura blocos só da unidade 2
6. O bloco de `27/04/2026 a 04/05/2026` vence
7. O `FILE_MAP.md` não cai mais em unidade 1 por palavras genéricas como `especificação`

### Cenário ambíguo: lista de revisão

1. A entry mistura:
   - recursão
   - indução
   - revisão
2. O matcher de subtópico encontra:
   - `funcoes-recursivas`: 1.18
   - `provadores-de-teoremas`: 1.11
3. Como a diferença é pequena, marca o conteúdo como ambíguo
4. O `FILE_MAP.md` pode:
   - manter a unidade, se ela for clara
   - deixar o período vazio
5. O backlog continua permitindo override manual

### Cenário de inconsistência: P1

1. Avaliação declara: `P1 cobre unidades 1 e 2`
2. Cronograma mostra `Lógica de Hoare` só após `22/04/2026`
3. O sistema registra um warning interno
4. O matcher não move `Hoare` artificialmente para antes da prova
5. `COURSE_MAP.md` pode expor um alerta curto, sem poluir o artefato

### Erros possíveis e por que acontecem

- **Arquivo com markdown fraco**
  - OCR ruim, headings ruins, título genérico
  - o sistema perde sinais para casar com subtópicos

- **Taxonomia oficial incompleta**
  - `teaching_plan` pobre ou mal formatado
  - o sistema pode ter poucos subtópicos explícitos

- **Cronograma genérico**
  - linhas como `Exercícios`, `Revisão`
  - o bloco temporal fica fraco e o período deve ficar vazio

- **Conteúdo transversal**
  - revisão geral, prova antiga, apostila cumulativa
  - o melhor comportamento continua sendo “não inventar precisão”

- **Plano de avaliação inconsistente**
  - o sistema detecta, alerta, mas não tenta corrigir semanticamente

## Implementation Notes

- **Não** usar `assessment_conflicts` como peso do matcher
- **Não** promover `.content_taxonomy.json` nem `.timeline_index.json` como leitura padrão do tutor
- **Não** remover `manual_unit_slug` nem `manual_timeline_block_id`
- **Não** misturar novamente `unit-first macro` com a decisão final do período

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-03-subtopic-first-temporal-matching.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
