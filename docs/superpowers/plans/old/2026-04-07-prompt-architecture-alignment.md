# Prompt Architecture Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the Claude, GPT, and Gemini prompt generators with the current app-managed repository architecture so the tutor treats `COURSE_MAP.md` and `FILE_MAP.md` as structural artifacts, routes fixes through `Reprocessar Repositório` and backlog overrides, and never falls back to manual map maintenance as the default workflow.

**Architecture:** Keep prompt generation inside `src/builder/engine.py`, but replace the current mix of legacy text and string-replacement hacks with shared helper builders that define one canonical structural-artifact contract. Lock the behavior with focused prompt tests in `tests/test_core.py`, including first-session protocol, economic reading order, repo drift handling, and generated `INSTRUCOES_CLAUDE_PROJETO.md` output.

**Tech Stack:** Python, pytest, existing builder pipeline in `src/builder/engine.py`

---

## File Structure

- `src/builder/engine.py`
  - Continue to host the prompt generators.
  - Add shared helper functions for structural-artifact policy, first-session protocol, economic reading order, and repo-drift handling.
  - Remove or quarantine legacy prompt bodies that still instruct manual `FILE_MAP.md` / `COURSE_MAP.md` filling.
- `tests/test_core.py`
  - Extend the prompt contract tests already present here.
  - Add coverage for Claude, GPT, and Gemini prompt output, plus generated Claude instruction artifact output.

## Implementation Notes

- The tutor should consume:
  - `course/COURSE_MAP.md`
  - `course/FILE_MAP.md`
  - `course/GLOSSARY.md`
  - `student/STUDENT_STATE.md`
  - `exercises/EXERCISE_INDEX.md` for practical routing
- The tutor should **not** be instructed to consume internal app infrastructure directly:
  - `course/.timeline_index.json`
  - `course/.content_taxonomy.json`
  - `course/.tag_catalog.json`
  - `course/.assessment_context.json`
- The tutor should treat repository structure maintenance as an app flow:
  - `Reprocessar Repositório`
  - override manual no backlog
  - never “return updated FILE_MAP/COURSE_MAP ready to paste” as the default path

---

### Task 1: Lock the new prompt contract with failing tests

**Files:**
- Modify: `tests/test_core.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Add failing tests for the structural-artifact contract**

Insert a new test group near the existing prompt tests in `tests/test_core.py`:

```python
class TestPromptArchitectureAlignment:
    META = {
        "course_name": "Metodos Formais",
        "repo_url": "https://github.com/example/metodos-formais-tutor",
        "branch": "main",
    }

    def test_claude_prompt_treats_maps_as_generated_artifacts(self):
        from src.builder.engine import generate_claude_project_instructions

        text = generate_claude_project_instructions(self.META)

        assert "artefatos estruturais gerados pelo app" in text
        assert "Reprocessar Repositório" in text
        assert "backlog" in text

    def test_claude_prompt_no_longer_requests_manual_file_map_fill(self):
        from src.builder.engine import generate_claude_project_instructions

        text = generate_claude_project_instructions(self.META)

        assert "preencha a coluna **Unidade** dos itens vazios" not in text
        assert "retorne o `FILE_MAP.md` e o `COURSE_MAP.md` atualizados" not in text

    def test_gpt_prompt_uses_same_structural_contract(self):
        from src.builder.engine import generate_gpt_instructions

        text = generate_gpt_instructions(self.META)

        assert "artefatos estruturais gerados pelo app" in text
        assert "não reescreva `FILE_MAP.md`/`COURSE_MAP.md` manualmente" in text

    def test_gemini_prompt_uses_same_structural_contract(self):
        from src.builder.engine import generate_gemini_instructions

        text = generate_gemini_instructions(self.META)

        assert "artefatos estruturais gerados pelo app" in text
        assert "não reescreva `FILE_MAP.md`/`COURSE_MAP.md` manualmente" in text

    def test_prompts_do_not_surface_internal_json_indexes(self):
        from src.builder.engine import (
            generate_claude_project_instructions,
            generate_gemini_instructions,
            generate_gpt_instructions,
        )

        texts = [
            generate_claude_project_instructions(self.META),
            generate_gpt_instructions(self.META),
            generate_gemini_instructions(self.META),
        ]

        for text in texts:
            assert ".timeline_index.json" not in text
            assert ".content_taxonomy.json" not in text
            assert ".tag_catalog.json" not in text
            assert ".assessment_context.json" not in text
```

- [ ] **Step 2: Run the focused prompt tests and verify the failure**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_core.py -k "PromptArchitectureAlignment or claude_instructions_no_longer_ask_tutor_to_fill_file_map_manually" -q
```

Expected:

```text
FAIL: test_claude_prompt_no_longer_requests_manual_file_map_fill
FAIL: test_prompts_do_not_surface_internal_json_indexes
```

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_core.py
git commit -m "test: lock prompt architecture alignment contract"
```

---

### Task 2: Add shared prompt-policy helpers in `engine.py`

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Add shared helper builders for prompt policy**

Insert helper functions above the prompt generator section in `src/builder/engine.py`:

```python
def _prompt_structural_artifact_contract_lines() -> list[str]:
    return [
        "1. Leia `course/COURSE_MAP.md`, `course/FILE_MAP.md`, `course/GLOSSARY.md` e `student/STUDENT_STATE.md`.",
        "2. Trate `FILE_MAP.md` e `COURSE_MAP.md` como artefatos estruturais gerados pelo app.",
        "3. Se algo parecer desatualizado, proponha `Reprocessar Repositório` ou ajuste manual no backlog.",
        "4. Não reescreva `FILE_MAP.md`/`COURSE_MAP.md` manualmente como fluxo padrão.",
    ]


def _prompt_repo_drift_lines() -> list[str]:
    return [
        "Antes de sessões futuras, releia `student/STUDENT_STATE.md` e `course/FILE_MAP.md`.",
        "Se surgirem novos materiais ainda não refletidos nesses artefatos, avise o aluno antes de continuar.",
        "Encaminhe a correção pelo app: `Reprocessar Repositório` para recalcular a estrutura ou override no backlog para casos específicos.",
    ]


def _prompt_economic_reading_order_lines() -> list[str]:
    return [
        "1. Comece por `course/COURSE_MAP.md` para identificar unidade, ordem e pré-requisitos.",
        "2. Use `course/GLOSSARY.md` para terminologia oficial.",
        "3. Use `course/FILE_MAP.md` para localizar o material certo.",
        "4. Se a tarefa for prática, consulte `exercises/EXERCISE_INDEX.md` antes de abrir listas ou provas longas.",
        "5. Só então abra um markdown em `content/`, `exercises/` ou `exams/`.",
        "6. Use o PDF bruto apenas quando o markdown não trouxer detalhe suficiente.",
    ]
```

- [ ] **Step 2: Add a helper for the first-session protocol**

Still in `src/builder/engine.py`, add:

```python
def _prompt_first_session_protocol_lines() -> list[str]:
    return [
        "Quando o aluno abrir o primeiro chat deste Projeto, ou quando `course/FILE_MAP.md` estiver com `status: pending_review`:",
        "1. Consulte os artefatos estruturais gerados pelo app.",
        "2. Assuma que `FILE_MAP.md` e `COURSE_MAP.md` são a base estrutural atual do repositório.",
        "3. Se eles não bastarem para responder, abra apenas o material mínimo necessário.",
        "4. Se detectar drift estrutural, proponha `Reprocessar Repositório` ou ajuste manual de override no backlog.",
        "5. Não trate esses arquivos como formulários a preencher manualmente.",
    ]
```

- [ ] **Step 3: Run the focused prompt tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_core.py -k "PromptArchitectureAlignment" -q
```

Expected:

```text
FAIL
```

The helper code alone should not pass yet because the generators still use legacy bodies.

- [ ] **Step 4: Commit the helper scaffolding**

```bash
git add src/builder/engine.py
git commit -m "refactor: add shared prompt policy helpers"
```

---

### Task 3: Collapse the Claude path onto one canonical architecture

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Replace the legacy low-token Claude replacement hack with direct composition**

Refactor the active Claude builder in `src/builder/engine.py` so the canonical output is assembled from helpers instead of post-hoc string replacement:

```python
def _build_claude_prompt_body(
    course_meta: dict,
    *,
    raw_base: str | None = None,
) -> str:
    structural = "\n".join(_prompt_structural_artifact_contract_lines())
    first_session = "\n".join(_prompt_first_session_protocol_lines())
    reading_order = "\n".join(_prompt_economic_reading_order_lines())
    repo_drift = "\n".join(_prompt_repo_drift_lines())

    return f"""
## Protocolo da Primeira Sessão
{first_session}

## Contrato Estrutural do Repositório
{structural}

## Ordem de Leitura Econômica
{reading_order}

## Drift do Repositório
{repo_drift}
""".strip()


def _low_token_generate_claude_project_instructions(
    course_meta: dict,
    *,
    raw_base: str | None = None,
) -> str:
    body = _build_claude_prompt_body(course_meta, raw_base=raw_base)
    return body


generate_claude_project_instructions = _low_token_generate_claude_project_instructions
```

- [ ] **Step 2: Convert the old public Claude generator into a compatibility wrapper**

Replace the old `generate_claude_project_instructions(...)` body near the legacy section with:

```python
def generate_claude_project_instructions(
    course_meta: dict,
    *,
    raw_base: str | None = None,
) -> str:
    return _low_token_generate_claude_project_instructions(
        course_meta,
        raw_base=raw_base,
    )
```

This keeps the public name stable while preventing any legacy body from emitting stale guidance.

- [ ] **Step 3: Run the focused Claude prompt tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_core.py -k "PromptArchitectureAlignment or SystemPrompt" -q
```

Expected:

```text
PASS
```

- [ ] **Step 4: Commit the Claude prompt cutover**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "refactor: cut over claude prompt to structural artifact contract"
```

---

### Task 4: Align GPT and Gemini with the same contract

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Make GPT reuse the shared policy helpers**

Refactor `generate_gpt_instructions(...)` in `src/builder/engine.py` so its structural guidance is composed from the shared helpers:

```python
def generate_gpt_instructions(course_meta: dict, *, raw_base: str | None = None) -> str:
    structural = "\n".join(_prompt_structural_artifact_contract_lines())
    reading_order = "\n".join(_prompt_economic_reading_order_lines())
    repo_drift = "\n".join(_prompt_repo_drift_lines())

    return f"""
Você é um tutor acadêmico.

## Protocolo Estrutural
{structural}

## Ordem de Leitura Econômica
{reading_order}

## Drift do Repositório
{repo_drift}
""".strip()
```

- [ ] **Step 2: Make Gemini reuse the same shared policy helpers**

Refactor `generate_gemini_instructions(...)` in `src/builder/engine.py` similarly:

```python
def generate_gemini_instructions(course_meta: dict, *, raw_base: str | None = None) -> str:
    structural = "\n".join(_prompt_structural_artifact_contract_lines())
    reading_order = "\n".join(_prompt_economic_reading_order_lines())
    repo_drift = "\n".join(_prompt_repo_drift_lines())

    return f"""
Você é um tutor de apoio à disciplina.

## Contrato Estrutural
{structural}

## Ordem de Leitura Econômica
{reading_order}

## Drift do Repositório
{repo_drift}
""".strip()
```

- [ ] **Step 3: Run the multi-model prompt contract tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_core.py -k "PromptArchitectureAlignment" -q
```

Expected:

```text
PASS
```

- [ ] **Step 4: Commit the GPT/Gemini alignment**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "refactor: align gpt and gemini prompts with structural artifact contract"
```

---

### Task 5: Verify the generated Claude instruction artifact

**Files:**
- Modify: `tests/test_core.py`
- Test: `src/builder/engine.py`

- [ ] **Step 1: Add a build-level regression test for `INSTRUCOES_CLAUDE_PROJETO.md`**

Extend the existing repository-generation tests in `tests/test_core.py`:

```python
def test_generated_claude_instruction_file_reflects_new_prompt_architecture(tmp_path):
    from src.builder.engine import Builder
    from src.models.core import SubjectProfile

    repo = tmp_path / "repo"
    repo.mkdir()

    subject = SubjectProfile(
        name="Metodos Formais",
        repo_root=str(repo),
        preferred_llm="claude",
        teaching_plan="Unidade 1: Métodos Formais",
        syllabus="04/03/2026 - Introdução",
    )

    builder = Builder(subject)
    builder._regenerate_pedagogical_files()

    instructions = (repo / "INSTRUCOES_CLAUDE_PROJETO.md").read_text(encoding="utf-8")

    assert "artefatos estruturais gerados pelo app" in instructions
    assert "Reprocessar Repositório" in instructions
    assert "backlog" in instructions
    assert "preencha a coluna **Unidade** dos itens vazios" not in instructions
    assert ".timeline_index.json" not in instructions
```

- [ ] **Step 2: Run the artifact-level regression**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_core.py -k "generated_claude_instruction_file_reflects_new_prompt_architecture" -q
```

Expected:

```text
PASS
```

- [ ] **Step 3: Commit the artifact regression coverage**

```bash
git add tests/test_core.py
git commit -m "test: verify generated claude instruction artifact uses new contract"
```

---

### Task 6: Quarantine leftover legacy prompt fragments and run regression

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Remove or neutralize leftover legacy phrases**

Search in `src/builder/engine.py` for stale prompt phrases and remove them from executable paths:

```powershell
rg -n "preencha a coluna \\*\\*Unidade\\*\\* dos itens vazios|retorne o `FILE_MAP.md` e o `COURSE_MAP.md` atualizados|arquivos → unidades|prontos para colar" src\builder\engine.py
```

For any remaining executable prompt path, either:
- delete the stale block, or
- replace it with a thin wrapper to the new canonical helper path

Use this compatibility pattern when deletion would be risky:

```python
def _deprecated_prompt_wrapper(*args, **kwargs):
    return _low_token_generate_claude_project_instructions(*args, **kwargs)
```

- [ ] **Step 2: Add one final test to guard against the main legacy phrases**

Append this regression to `tests/test_core.py`:

```python
def test_claude_prompt_contains_no_legacy_manual_mapping_phrases():
    from src.builder.engine import generate_claude_project_instructions

    text = generate_claude_project_instructions(
        {"course_name": "Metodos Formais", "repo_url": "", "branch": "main"}
    )

    forbidden = [
        "preencha a coluna **Unidade** dos itens vazios",
        "retorne o `FILE_MAP.md` e o `COURSE_MAP.md` atualizados",
        "prontos para colar",
    ]

    for phrase in forbidden:
        assert phrase not in text
```

- [ ] **Step 3: Run the full prompt regression suite**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_core.py -k "PromptArchitectureAlignment or SystemPrompt or generated_claude_instruction_file_reflects_new_prompt_architecture" -q
```

Expected:

```text
PASS
```

- [ ] **Step 4: Run the broader regression touched by builder prompt generation**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_core.py tests\test_file_map_unit_mapping.py tests\test_tag_catalog.py -q
```

Expected:

```text
PASS
```

- [ ] **Step 5: Commit the prompt alignment cleanup**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "refactor: remove legacy prompt mapping workflow"
```

---

## Out of Scope

- Broad dead-code cleanup across the whole app
- `.gitignore` cleanup for generated repos
- New UI for prompt inspection
- Changes to the pedagogical matching algorithm itself

## Self-Review Notes

- Spec coverage: Claude/GPT/Gemini prompt generators, generated Claude artifact, legacy removal, and regression coverage are all represented by explicit tasks.
- Placeholder scan: no `TODO`, `TBD`, or “similar to previous task” shortcuts remain.
- Type consistency: all helper names referenced in later tasks are introduced in Task 2 before being used by Tasks 3-6.
