# Audit Fixes + FILE_MAP + First Session Protocol — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 7 audit issues found in pedagogical generators, add `FILE_MAP.md` generation, and refactor the tutor system prompt to include a First Session protocol so the tutor knows how to initialize when the student opens the chat.

**Architecture:** The fixes are isolated changes in `engine.py` (generators) and `llm.py` (prompt). The new `file_map_md()` generator reads manifest entries and produces a Markdown table. The system prompt gets a new "Protocolo de Primeira Sessão" section with a checklist for the tutor. All changes are backward-compatible.

**Tech Stack:** Python, regex, existing `FileEntry`/`SubjectProfile` data classes, pytest.

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/builder/engine.py` | Modify | Add `file_map_md()`, fix system prompt, fix conditional index refs, fix `_regenerate_pedagogical_files` |
| `src/services/llm.py` | Modify | Fix hardcoded categories, increase syllabus truncation limit |
| `tests/test_core.py` | Modify | Add tests for `file_map_md()`, categories in LLM prompt, system prompt sections |

---

### Task 1: Fix hardcoded categories in LLM prompt (Issue #1)

**Files:**
- Modify: `src/services/llm.py:115-117`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write failing test — LLM prompt includes all DEFAULT_CATEGORIES**

```python
class TestLLMPromptCategories:
    """Verifica que o prompt do LLM inclui todas as categorias válidas."""

    def test_prompt_includes_all_categories(self):
        from src.services.llm import LLMCategorizer
        from src.utils.helpers import DEFAULT_CATEGORIES
        llm = LLMCategorizer("openai", "", "")
        # Access the prompt building logic by calling classify_pdf
        # with a mock that captures the prompt
        from unittest.mock import patch
        captured = {}
        def mock_openai(self_inner, prompt, max_tokens=50):
            captured["prompt"] = prompt
            return '{"category": "outros", "unit": "", "exam_ref": ""}'
        with patch.object(LLMCategorizer, "_call_openai", mock_openai):
            llm.openai_key = "fake"
            llm.classify_pdf("Test", "", "", "test text")
        prompt = captured["prompt"]
        for cat in DEFAULT_CATEGORIES:
            assert cat in prompt, f"Category '{cat}' missing from LLM prompt"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py::TestLLMPromptCategories -v`
Expected: FAIL — "trabalhos", "codigo-professor", "codigo-aluno", "quadro-branco" missing from prompt

- [ ] **Step 3: Fix — derive category list from DEFAULT_CATEGORIES**

In `src/services/llm.py`, replace the hardcoded category string (lines 115-117):

```python
# OLD:
# - "category": tipo do arquivo. Escolha UM dentre:
#   material-de-aula, provas, listas, gabaritos, fotos-de-prova,
#   referencias, bibliografia, cronograma, outros

# NEW — derive from DEFAULT_CATEGORIES:
        categories_str = ", ".join(DEFAULT_CATEGORIES)
        # ... in the prompt f-string:
        f'- "category": tipo do arquivo. Escolha UM dentre:\n  {categories_str}'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core.py::TestLLMPromptCategories -v`
Expected: PASS

- [ ] **Step 5: Also increase syllabus truncation (Issue #4)**

In `src/services/llm.py:111`, change `syllabus[:1000]` to `syllabus[:4000]`:

```python
# OLD:
{syllabus[:1000]}

# NEW:
{syllabus[:4000]}
```

- [ ] **Step 6: Run all tests**

Run: `python -m pytest tests/test_core.py -v`
Expected: All pass

---

### Task 2: Fix system prompt — conditional file references (Issue #3)

**Files:**
- Modify: `src/builder/engine.py:1694-1712` (inside `generate_claude_project_instructions()`)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write failing test — system prompt only references files that exist**

```python
class TestSystemPromptFileReferences:
    """Verifica que o system prompt não referencia arquivos que podem não existir."""

    def test_no_assignments_reference_without_entries(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(
            {"course_name": "Test", "professor": "P", "institution": "I", "semester": "S"},
        )
        # Without entries, conditional dirs should NOT appear in the file table
        assert "assignments/" not in result
        assert "code/professor/" not in result
        assert "whiteboard/" not in result

    def test_file_map_referenced(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(
            {"course_name": "Test", "professor": "P", "institution": "I", "semester": "S"},
        )
        assert "FILE_MAP.md" in result
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — current prompt always includes `assignments/`, `code/professor/`, `whiteboard/`; `FILE_MAP.md` is missing.

- [ ] **Step 3: Refactor file reference table to be dynamic**

Add `has_code`, `has_assignments`, `has_whiteboard` parameters to `generate_claude_project_instructions()`. Build the table rows conditionally. Add `FILE_MAP.md` row always.

```python
def generate_claude_project_instructions(
    course_meta: dict,
    student_profile=None,
    subject_profile=None,
    has_assignments: bool = False,
    has_code: bool = False,
    has_whiteboard: bool = False,
) -> str:
```

In the table section:
```python
    file_rows = [
        "| `system/TUTOR_POLICY.md` | Sempre — regras de comportamento |",
        "| `system/PEDAGOGY.md` | Ao explicar qualquer conceito |",
        "| `system/MODES.md` | Para identificar o modo da sessão |",
        "| `system/OUTPUT_TEMPLATES.md` | Para formatar respostas |",
        "| `course/COURSE_IDENTITY.md` | Dados gerais da disciplina |",
        "| `course/COURSE_MAP.md` | Ordem dos tópicos e dependências |",
        "| `course/SYLLABUS.md` | Cronograma e datas |",
        "| `course/GLOSSARY.md` | Terminologia da disciplina |",
        "| `course/FILE_MAP.md` | Mapeamento arquivo→unidade — **consulte para rastreabilidade** |",
        "| `student/STUDENT_STATE.md` | Estado atual do aluno — SEMPRE consulte |",
        "| `student/STUDENT_PROFILE.md` | Perfil e estilo do aluno |",
        "| `content/BIBLIOGRAPHY.md` | Referências bibliográficas |",
        "| `content/` | Material de aula curado |",
        "| `exercises/` | Listas de exercícios |",
        "| `exams/` | Provas anteriores e gabaritos |",
    ]
    if has_assignments:
        file_rows.append("| `assignments/` | Enunciados de trabalhos — consulte antes de guiar |")
    if has_code:
        file_rows.append("| `code/professor/` | Código do professor — exemplos e implementações |")
    if has_whiteboard:
        file_rows.append("| `whiteboard/` | Explicações do professor no quadro |")

    file_table = "\n".join(file_rows)
```

- [ ] **Step 4: Update callers to pass the flags**

In `_write_root_files()` and `_regenerate_pedagogical_files()`, compute the flags from entries:

```python
has_assignments = any(e.category in ASSIGNMENT_CATEGORIES for e in entries_for_check)
has_code = any(e.category in CODE_CATEGORIES for e in entries_for_check)
has_whiteboard = any(e.category in WHITEBOARD_CATEGORIES for e in entries_for_check)
```

Pass them to `generate_claude_project_instructions(meta, student_p, subj_p, has_assignments, has_code, has_whiteboard)`.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_core.py -v`
Expected: All pass

---

### Task 3: Add `file_map_md()` generator (Issue #2 — core feature)

**Files:**
- Modify: `src/builder/engine.py` — add new function
- Test: `tests/test_core.py`

- [ ] **Step 1: Write failing tests**

```python
class TestFileMapMd:
    COURSE_META = {"course_name": "Métodos Formais", "course_slug": "metodos-formais"}

    def test_empty_entries(self):
        from src.builder.engine import file_map_md
        result = file_map_md(self.COURSE_META, [])
        assert "FILE_MAP" in result
        assert "pending_review" in result
        assert "Nenhum arquivo" in result

    def test_with_entries(self):
        from src.builder.engine import file_map_md
        entries = [
            {"id": "aula-01", "title": "Aula 01 - Introdução",
             "category": "material-de-aula", "tags": "",
             "base_markdown": "staging/markdown-auto/pymupdf4llm/aula-01.md",
             "raw_target": "raw/pdfs/material-de-aula/aula-01.pdf"},
            {"id": "prova-p1", "title": "Prova P1 2025",
             "category": "provas", "tags": "unidade-01-métodos-formais",
             "base_markdown": "staging/markdown-auto/pymupdf4llm/prova-p1.md",
             "raw_target": "raw/pdfs/provas/prova-p1.pdf"},
        ]
        result = file_map_md(self.COURSE_META, entries)
        assert "Aula 01 - Introdução" in result
        assert "material-de-aula" in result
        assert "staging/markdown-auto/pymupdf4llm/aula-01.md" in result
        assert "raw/pdfs/material-de-aula/aula-01.pdf" in result
        # Entry with existing tag should show it
        assert "unidade-01-métodos-formais" in result

    def test_cronograma_marked_curso_inteiro(self):
        from src.builder.engine import file_map_md
        entries = [
            {"id": "cronograma", "title": "Cronograma",
             "category": "cronograma", "tags": "",
             "base_markdown": "", "raw_target": "raw/pdfs/cronograma/cronograma.pdf"},
        ]
        result = file_map_md(self.COURSE_META, entries)
        assert "curso-inteiro" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_core.py::TestFileMapMd -v`
Expected: FAIL — `file_map_md` does not exist

- [ ] **Step 3: Implement `file_map_md()`**

Add to `engine.py` after `glossary_md()`:

```python
_NO_UNIT_CATEGORIES = {"cronograma", "bibliografia", "referencias"}

def file_map_md(course_meta: dict, manifest_entries: list) -> str:
    """Gera FILE_MAP.md a partir das entries do manifest.

    Cada entry é um dict vindo do manifest.json (não FileEntry).
    Campos usados: id, title, category, tags, base_markdown, raw_target.
    """
    course_name = course_meta.get("course_name", "Curso")
    lines = [
        "---",
        f"course: {course_name}",
        "status: pending_review",
        "---",
        "",
        f"# FILE_MAP — {course_name}",
        "",
        "> **Status:** ⏳ Aguardando mapeamento de unidades pelo tutor.",
        "> Na primeira sessão, o tutor lerá cada arquivo e preencherá as colunas",
        "> **Unidade** e **Tags** cruzando com `course/COURSE_MAP.md` e `course/SYLLABUS.md`.",
        "",
        "## Arquivos do repositório",
        "",
    ]

    if not manifest_entries:
        lines.append("Nenhum arquivo processado ainda.")
        return "\n".join(lines)

    lines += [
        "| # | Título | Categoria | Markdown | Raw | Unidade | Tags |",
        "|---|---|---|---|---|---|---|",
    ]

    for i, entry in enumerate(manifest_entries, 1):
        title = entry.get("title", "")
        category = entry.get("category", "")
        tags = entry.get("tags", "")
        md_path = entry.get("base_markdown") or entry.get("advanced_markdown") or ""
        raw_path = entry.get("raw_target") or ""

        # Categories that cover the whole course get auto-tagged
        if category in _NO_UNIT_CATEGORIES and not tags:
            unit = "curso-inteiro"
        else:
            unit = ""

        md_cell = f"`{md_path}`" if md_path else "—"
        raw_cell = f"`{raw_path}`" if raw_path else "—"
        unit_cell = unit or ""
        tags_cell = tags or ""

        lines.append(f"| {i} | {title} | {category} | {md_cell} | {raw_cell} | {unit_cell} | {tags_cell} |")

    lines += [
        "",
        "## Legenda",
        "",
        "- **Unidade**: slug da unidade do COURSE_MAP (ex: `unidade-01-métodos-formais`)",
        "- **Tags**: informações adicionais (ex: `pré-P1`, `Dafny`, `exercício-lab`)",
        "- **Categoria**: tipo do arquivo — **não** deve ser alterada pelo tutor",
        "",
    ]

    return "\n".join(lines)
```

- [ ] **Step 4: Export from engine.py and import in test_core.py**

Add `file_map_md` to the imports in `test_core.py`:
```python
from src.builder.engine import (
    ...,
    file_map_md,
)
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_core.py::TestFileMapMd -v`
Expected: All 3 pass

---

### Task 4: Wire `file_map_md()` into build pipeline

**Files:**
- Modify: `src/builder/engine.py` — `_write_root_files()` and `_regenerate_pedagogical_files()`

- [ ] **Step 1: Add FILE_MAP.md generation in `_write_root_files()`**

After the existing index generation (after line ~696), add:

```python
        # ── FILE_MAP — generated AFTER all entries are processed ──
        # Note: this is called from build() after the entry loop,
        # not from _write_root_files() which runs before entries.
```

Actually, `_write_root_files()` runs BEFORE entries are processed (line 496). FILE_MAP needs manifest data AFTER processing. So add it in `build()` after the entry loop, around line 535:

```python
        # FILE_MAP — needs manifest entries, so generated after processing
        write_text(self.root_dir / "course" / "FILE_MAP.md",
                   file_map_md(self.course_meta, manifest["entries"]))
```

- [ ] **Step 2: Add FILE_MAP.md regeneration in `_regenerate_pedagogical_files()`**

After the existing index regeneration (around line 1529), add:

```python
        # FILE_MAP
        write_text(self.root_dir / "course" / "FILE_MAP.md",
                   file_map_md(self.course_meta, manifest.get("entries", [])))
```

- [ ] **Step 3: Run all tests**

Run: `python -m pytest tests/test_core.py -v`
Expected: All pass

---

### Task 5: Add First Session Protocol to system prompt (Issue #2 — protocol)

**Files:**
- Modify: `src/builder/engine.py` — `generate_claude_project_instructions()`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write failing test**

```python
class TestFirstSessionProtocol:
    def test_first_session_section_present(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(
            {"course_name": "Test", "professor": "P", "institution": "I", "semester": "S"},
        )
        assert "Primeira Sessão" in result or "Primeira sessão" in result
        assert "FILE_MAP" in result
        assert "COURSE_MAP" in result
        assert "GLOSSARY" in result

    def test_first_session_has_checklist(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(
            {"course_name": "Test", "professor": "P", "institution": "I", "semester": "S"},
        )
        # Should have numbered steps or checklist items
        assert "1." in result
        assert "FILE_MAP" in result
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — no "Primeira Sessão" section in current system prompt

- [ ] **Step 3: Add First Session Protocol section**

Add after the "Captura de conteúdo novo" section (before the closing `"""`), a new section:

```python
## Protocolo de Primeira Sessão

Quando o aluno abrir o **primeiro chat** deste Projeto, execute este protocolo antes de qualquer outra coisa:

**Mensagem de boas-vindas:**
> "Olá {nick}! Sou seu tutor de {course_name}. Antes de começarmos a estudar, preciso organizar seus materiais. Vou analisar cada arquivo e mapear para a unidade correspondente do curso. Isso vai levar um momento."

**Checklist de inicialização:**

1. **Mapear arquivos → unidades**: Leia `course/FILE_MAP.md`. Para cada arquivo com a coluna "Unidade" vazia:
   - Abra o arquivo Markdown referenciado na coluna "Markdown"
   - Leia o conteúdo e identifique o(s) tópico(s) abordado(s)
   - Cruze com as unidades em `course/COURSE_MAP.md`
   - Se necessário, use `course/SYLLABUS.md` para identificar o período
   - Preencha a coluna "Unidade" com o slug correto (ex: `unidade-01-métodos-formais`)
   - Preencha "Tags" com informações adicionais relevantes (ex: `pré-P1`, `Dafny`, `laboratório`)

2. **Preencher alta incidência em provas**: Se existirem provas em `exams/`, analise-as e preencha a seção "Tópicos de alta incidência em prova" em `course/COURSE_MAP.md`

3. **Semear glossário**: Leia `course/GLOSSARY.md`. Para cada termo com `[a preencher]`, escreva uma definição baseada no material disponível

4. **Apresentar resultado**: Mostre o FILE_MAP preenchido ao aluno em formato de tabela e peça confirmação

5. **Instruir o commit**:
```
git add course/FILE_MAP.md course/COURSE_MAP.md course/GLOSSARY.md
git commit -m "init: mapeamento de arquivos e glossário pelo tutor"
git push
```

**Após a primeira sessão**, nas sessões seguintes, consulte `course/FILE_MAP.md` para saber qual arquivo pertence a qual unidade antes de responder qualquer pergunta.
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_core.py -v`
Expected: All pass

---

### Task 6: Fix `_regenerate_pedagogical_files` — add student files (Issue #7)

**Files:**
- Modify: `src/builder/engine.py:1465-1530`

- [ ] **Step 1: Add student profile regeneration**

After the bibliography section in `_regenerate_pedagogical_files()`, add:

```python
        # Student profile (may have changed since initial build)
        if self.student_profile:
            write_text(self.root_dir / "student" / "STUDENT_PROFILE.md",
                       student_profile_md(self.student_profile))
```

Note: do NOT regenerate `STUDENT_STATE.md` — it evolves during sessions and should not be overwritten.

- [ ] **Step 2: Run all tests**

Run: `python -m pytest tests/test_core.py -v`
Expected: All pass

---

### Task 7: Fix COURSE_MAP and GLOSSARY placeholder instructions (Issues #5, #6)

**Files:**
- Modify: `src/builder/engine.py` — `course_map_md()` and `glossary_md()`

- [ ] **Step 1: Update COURSE_MAP "alta incidência" section**

Change the placeholder from a generic `[a preencher]` to a tutor instruction:

```python
    lines += [
        "## Tópicos de alta incidência em prova",
        "",
        "<!-- Preenchido pelo tutor na Primeira Sessão após analisar exams/ -->",
        "",
        "| Tópico | Unidade | Incidência |",
        "|---|---|---|",
        "| ⏳ Aguardando análise do tutor | | |",
        "",
        "## Notas do professor",
        "",
        "<!-- Preenchido pelo tutor após análise das provas e materiais -->",
        "- ⏳ Aguardando análise do tutor",
    ]
```

- [ ] **Step 2: Update GLOSSARY placeholder text**

In `glossary_md()`, change the placeholder definitions to signal the tutor:

```python
        for term, unit_title in candidates:
            lines += [
                f"## {term}",
                "**Definição:** ⏳ Aguardando preenchimento pelo tutor na Primeira Sessão",
                "**Sinônimos aceitos:** —",
                "**Não confundir com:** —",
                f"**Aparece em:** {unit_title}",
                "",
            ]
```

- [ ] **Step 3: Run all tests**

Run: `python -m pytest tests/test_core.py -v`
Expected: All pass (check that existing tests don't assert on the old placeholder text)

---

### Task 8: Final integration test + verification

**Files:**
- Test: `tests/test_core.py`

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/test_core.py -v`
Expected: All tests pass (100+ tests)

- [ ] **Step 2: Verify no regressions in existing functionality**

Run: `python -m pytest tests/test_core.py -v --tb=short 2>&1 | tail -20`

- [ ] **Step 3: Review all changes**

```bash
git diff --stat
git diff src/builder/engine.py
git diff src/services/llm.py
git diff tests/test_core.py
```

Verify:
- `file_map_md()` is exported and callable
- System prompt references `FILE_MAP.md` in the file table
- System prompt has "Primeira Sessão" protocol
- LLM prompt includes all 13 categories
- Syllabus truncation is 4000 chars
- `_regenerate_pedagogical_files` includes student profile
- Conditional file references in system prompt
- COURSE_MAP and GLOSSARY have tutor-directed placeholders
