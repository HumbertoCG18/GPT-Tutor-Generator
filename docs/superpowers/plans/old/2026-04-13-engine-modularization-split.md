# Engine Modularization Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dividir `src/builder/engine.py` em módulos menores e mais legíveis sem quebrar imports públicos, comportamento do app ou cobertura de testes.

**Architecture:** O split será incremental e guiado por fachada. `src/builder/engine.py` continua existindo como ponto de entrada estável, concentrando `RepoBuilder` e re-exportando funções públicas movidas para módulos novos. A ordem de extração prioriza funções puras e áreas com boa cobertura (`prompts` e `timeline`) antes de tocar nas partes mais acopladas de processamento PDF e manipulação de imagens.

**Tech Stack:** Python 3.11, Tkinter, pytest, ripgrep, Git

---

## File Map

- Modify: `src/builder/engine.py`
  - Virar fachada/orquestrador: manter `RepoBuilder`, imports estáveis e re-exports públicos.
- Create: `src/builder/prompt_generation.py`
  - Mover geradores de instruções Claude/GPT/Gemini e helpers `_prompt_*`.
- Create: `src/builder/timeline_index.py`
  - Mover parsing, scoring e serialização do timeline index.
- Create: `src/builder/navigation_artifacts.py`
  - Mover `course_map_md`, `file_map_md`, variantes low-token e helpers de enriquecimento RAG ligados a esses artefatos.
- Create: `src/builder/image_markdown.py`
  - Mover injeção de descrições de imagem e helpers de markdown/imagem puros.
- Modify: `src/ui/app.py`
  - Manter comportamento; só ajustar imports se algum acoplamento precisar sair de `engine.py` em fase posterior.
- Modify: `src/ui/dialogs.py`
  - Mesmo critério: só ajustar imports se necessário, mantendo compatibilidade.
- Test: `tests/test_core.py`
  - Continuar cobrindo prompts, FILE_MAP, COURSE_MAP, timeline e orquestração básica.
- Test: `tests/test_file_map_unit_mapping.py`
  - Proteger o contrato do timeline index e do roteamento por unidade/bloco.
- Test: `tests/test_code_review_profiles.py`
  - Proteger `modes_md()` e `output_templates_md()` quando forem movidos.
- Test: `tests/test_image_curation.py`
  - Proteger a injeção de descrições e utilitários estáticos do `RepoBuilder`.

## Non-Goals

- Não trocar o contrato público de `RepoBuilder`.
- Não mudar o formato de `manifest.json`, `FILE_MAP.md`, `COURSE_MAP.md` ou dos prompts neste split.
- Não mover primeiro os backends pesados (`marker`, `docling`, `datalab`) nem o coração do processamento de PDF.
- Não refatorar a UI junto com a modularização além do estritamente necessário para imports.

## Sequência recomendada

1. Congelar o contrato público de `engine.py` com testes.
2. Extrair `prompt_generation.py` em subfases pequenas.
3. Extrair `timeline_index.py` em subfases pequenas.
4. Extrair `navigation_artifacts.py` em subfases pequenas.
5. Extrair `image_markdown.py` em subfases pequenas.
6. Só depois avaliar se vale separar `RepoBuilder` por mixins ou módulos de pipeline.

## Batching obrigatório

Como `engine.py` é grande demais para cortes longos seguros, a execução deve ser feita em batches curtos. Cada batch deve:

1. mover um cluster pequeno e coeso
2. manter `engine.py` como fachada estável
3. rodar um subconjunto curto de testes
4. só então avançar para o próximo batch

**Regra operacional:** se um patch exigir mover mais de ~200-300 linhas de uma vez, ele deve ser quebrado em mais batches.

### Batch 2A — Prompts públicos

- mover apenas:
  - `generate_claude_project_instructions`
  - `generate_gpt_instructions`
  - `generate_gemini_instructions`
  - `_low_token_generate_claude_project_instructions`
  - `_prompt_map_artifact_contract_text`
  - `_prompt_student_state_update_text`
  - `_prompt_first_session_protocol_text`
  - `_prompt_first_session_protocol_lines`
  - `_prompt_structural_artifact_contract_lines`
  - `_prompt_economic_reading_order_lines`
- manter em `engine.py` por enquanto:
  - `tutor_policy_md`
  - `pedagogy_md`
  - `modes_md`
  - `output_templates_md`
  - `_code_review_profile`
- testes:
  - `pytest tests/test_core.py -k "PromptArchitectureAlignment or SystemPromptFileReferences or engine_public_api_smoke_import" -q`

### Batch 2B — Arquivos pedagógicos de prompt

- mover:
  - `tutor_policy_md`
  - `pedagogy_md`
  - `modes_md`
  - `output_templates_md`
  - `_code_review_profile`
  - `_FORMAL_CODE_REVIEW_KEYWORDS`
- testes:
  - `pytest tests/test_code_review_profiles.py -q`
  - `pytest tests/test_core.py -k "PromptArchitectureAlignment" -q`

### Batch 2C — Limpeza do legado de prompt

- remover de `engine.py` as implementações antigas já substituídas por re-export
- critério:
  - nenhum símbolo de prompt duplicado permanece em `engine.py`
- testes:
  - `pytest tests/test_core.py -k "PromptArchitectureAlignment or engine_public_api_smoke_import" -q`

### Batch 3A — Timeline parse/core

- mover apenas:
  - `_parse_syllabus_timeline`
  - `_infer_timeline_keys`
  - `_parse_timeline_date_value`
  - `_parse_timeline_period_bounds`
  - `_build_timeline_candidate_rows`
  - `_empty_timeline_index`
  - `_timeline_specific_tokens`
  - `_timeline_core_text`
  - `_timeline_period_label`
  - `_timeline_row_is_review_or_assessment`
  - `_timeline_row_is_unit_anchor_only`
  - `_timeline_text_is_administrative`
- manter em `engine.py` neste batch:
  - `_match_timeline_to_units`
  - `_match_timeline_to_units_generic`
- rationale:
  - este primeiro corte de timeline fica restrito a parsing, datas e normalização
  - matching cronograma ↔ unidades continua no `engine.py` por enquanto para não puxar
    consumidores de `course_map_md` cedo demais
- testes:
  - `pytest tests/test_core.py -k "parse_syllabus_timeline or engine_timeline_exports_still_work_after_split" -q`
  - `pytest tests/test_file_map_unit_mapping.py -k "timeline" -q`

### Batch 3B — Timeline block building/serialization

- mover:
  - `_timeline_unit_number_from_text`
  - `_timeline_unit_number_from_unit`
  - `_score_timeline_unit_phrase`
  - `_extract_timeline_topics`
  - `_row_looks_like_continuation`
  - `_rows_belong_to_same_thematic_block`
  - `_timeline_block_is_soft_continuation`
  - `_timeline_block_is_noninstructional`
  - `_timeline_block_is_administrative_only`
  - `_assign_timeline_block_to_unit`
  - `_serialize_timeline_index`
  - `_write_internal_timeline_index`
  - `_score_timeline_row_against_unit`
- manter em `engine.py` neste batch:
  - `_build_timeline_index`
- rationale:
  - `_build_timeline_index` ainda depende de assignment por taxonomy/topic e de
    consumidores posteriores; mover agora aumentaria o acoplamento do módulo
- testes:
  - `pytest tests/test_core.py -k "build_timeline_index or timeline_index or timeline_unit_scoring" -q`
  - `pytest tests/test_file_map_unit_mapping.py -k "timeline" -q`

### Batch 3C — Timeline consumers que ainda ficam no engine

- **não mover ainda**:
  - consumers de assessment context
  - assessment context
  - FILE_MAP routing temporal
- objetivo:
  - confirmar que `timeline_index.py` já concentra parse/core, scoring e taxonomy
    do timeline, sem puxar consumidores de `FILE_MAP.md` e assessment

### Batch 4A — Artefatos de navegação

- mover:
  - `course_map_md`
  - `_low_token_course_map_md`
  - `_low_token_course_map_md_v2`
- testes:
  - `pytest tests/test_core.py -k "CourseMap" -q`

### Batch 4B — FILE_MAP

- mover:
  - `file_map_md`
  - `_low_token_file_map_md`
  - `_budgeted_file_map_md`
- deixar helpers mais acoplados no mesmo módulo novo
- status atual:
  - concluído o corte dos helpers puros de FILE_MAP:
    `_entry_priority_label`, `_entry_usage_hint`,
    `_entry_markdown_path_for_file_map`, `_entry_markdown_text_for_file_map`,
    `_infer_unit_confidence`, `_file_map_markdown_cell`
- testes:
  - `pytest tests/test_core.py -k "FileMap" -q`
  - `pytest tests/test_file_map_unit_mapping.py -q`

### Batch 4C — Enriquecimento RAG dos artefatos

- mover:
  - `_extract_section_headers`
  - `_inject_executive_summary`
  - `_clean_extraction_noise`
  - `_get_entry_sections`
  - `_infer_unit_confidence`
- status atual:
  - concluído em `navigation_artifacts.py`, com `engine.py` mantendo reexports
    estáveis para testes, `curator_studio.py` e demais consumidores
- testes:
  - `pytest tests/test_rag_enrichment.py -q`

### Batch 5A — Image markdown helpers

- mover:
  - `_low_token_inject_image_descriptions`
  - helpers puros usados por ele
- manter `RepoBuilder.inject_image_descriptions = staticmethod(...)` em `engine.py`
- status atual:
  - concluído o primeiro corte seguro com helpers puros:
    `_compact_image_description_text`,
    `_build_image_description_lookup`,
    `_resolve_image_description_record`
  - concluído também o corte do wrapper `_low_token_inject_image_descriptions`
    para `image_markdown.py`
  - `RepoBuilder.inject_image_descriptions()` agora só delega para o módulo novo
- testes:
  - `pytest tests/test_image_curation.py -q`

## Task 1: Congelar a API pública de `engine.py`

**Files:**
- Modify: `tests/test_core.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Escrever um teste de smoke import para os símbolos públicos que não podem quebrar**

```python
def test_engine_public_api_smoke_import():
    from src.builder.engine import (
        RepoBuilder,
        generate_claude_project_instructions,
        generate_gpt_instructions,
        generate_gemini_instructions,
        course_map_md,
        file_map_md,
        _build_timeline_index,
    )

    assert RepoBuilder is not None
    assert callable(generate_claude_project_instructions)
    assert callable(generate_gpt_instructions)
    assert callable(generate_gemini_instructions)
    assert callable(course_map_md)
    assert callable(file_map_md)
    assert callable(_build_timeline_index)
```

- [ ] **Step 2: Rodar o teste para fixar o contrato atual**

Run: `pytest tests/test_core.py::test_engine_public_api_smoke_import -q`
Expected: `1 passed`

- [ ] **Step 3: Adicionar um comentário curto em `engine.py` documentando o papel de fachada**

```python
# engine.py acts as the public facade for builder functionality.
# During modularization, keep public imports stable and move implementations
# into focused modules behind these exports.
```

- [ ] **Step 4: Rodar a suíte mínima de artefatos e prompts**

Run: `pytest tests/test_core.py -k "PromptArchitectureAlignment or CourseMapTimeline or FileMap" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "test: lock engine public api before split"
```

## Task 2: Extrair prompts para `prompt_generation.py`

**Files:**
- Create: `src/builder/prompt_generation.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`
- Test: `tests/test_code_review_profiles.py`

- [ ] **Step 1: Criar um teste que prove que os prompts continuam vindo por `engine.py`**

```python
def test_engine_prompt_exports_still_work_after_module_split():
    from src.builder.engine import generate_claude_project_instructions

    text = generate_claude_project_instructions({"course_name": "Teste"})
    assert "course/FILE_MAP.md" in text
    assert "artefatos gerados" in text or "artefatos estruturais gerados pelo app" in text
```

- [ ] **Step 2: Criar `src/builder/prompt_generation.py` com o bloco de prompts**

```python
from __future__ import annotations

def generate_claude_project_instructions(...): ...
def generate_gpt_instructions(...): ...
def generate_gemini_instructions(...): ...
def tutor_policy_md(...): ...
def modes_md(...): ...
def output_templates_md(...): ...
```

Mover junto:
- `generate_claude_project_instructions`
- `generate_gpt_instructions`
- `generate_gemini_instructions`
- `_low_token_generate_claude_project_instructions`
- `_prompt_map_artifact_contract_text`
- `_prompt_student_state_update_text`
- `_prompt_first_session_protocol_text`
- `_prompt_first_session_protocol_lines`
- `_prompt_structural_artifact_contract_lines`
- `_prompt_economic_reading_order_lines`
- `tutor_policy_md`
- `pedagogy_md`
- `modes_md`
- `output_templates_md`

- [ ] **Step 3: Transformar `engine.py` em re-export explícito desses símbolos**

```python
from src.builder.prompt_generation import (
    generate_claude_project_instructions,
    generate_gpt_instructions,
    generate_gemini_instructions,
    tutor_policy_md,
    pedagogy_md,
    modes_md,
    output_templates_md,
)
```

- [ ] **Step 4: Rodar os testes de prompts**

Run: `pytest tests/test_core.py -k "PromptArchitectureAlignment or SystemPromptFileReferences" -q`
Expected: PASS

- [ ] **Step 5: Rodar os testes de perfis de code review**

Run: `pytest tests/test_code_review_profiles.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py src/builder/prompt_generation.py tests/test_core.py tests/test_code_review_profiles.py
git commit -m "refactor: extract prompt generation module"
```

## Task 3: Extrair timeline para `timeline_index.py`

**Files:**
- Create: `src/builder/timeline_index.py`
- Modify: `src/builder/engine.py`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_core.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Criar um teste de import smoke para o timeline**

```python
def test_engine_timeline_exports_still_work_after_split():
    from src.builder.engine import _build_timeline_index

    assert callable(_build_timeline_index)
```

- [ ] **Step 2: Criar `src/builder/timeline_index.py` e mover o cluster coeso de helpers**

Mover como bloco único, sem reescrever a lógica:
- `_TIMELINE_*`
- `_timeline_text_is_administrative`
- `_timeline_row_is_review_or_assessment`
- `_timeline_specific_tokens`
- `_timeline_period_label`
- `_build_timeline_candidate_rows`
- `_build_timeline_index`
- `_serialize_timeline_index`
- `_write_internal_timeline_index`
- scoring de unidade/tópico/bloco
- helpers de parsing/agrupamento do cronograma

```python
def _build_timeline_index(candidate_rows, unit_index, content_taxonomy=None) -> dict:
    ...
```

- [ ] **Step 3: Re-exportar em `engine.py`**

```python
from src.builder.timeline_index import (
    _build_timeline_candidate_rows,
    _build_timeline_index,
    _serialize_timeline_index,
)
```

- [ ] **Step 4: Ajustar `dialogs.py` só se algum helper temporal ainda vier de `engine.py` por acidente**

Critério:
- preferir continuar importando por `engine.py` nesta fase
- importar direto de `timeline_index.py` apenas se isso reduzir acoplamento sem espalhar churn

- [ ] **Step 5: Rodar os testes de timeline e mapeamento**

Run: `pytest tests/test_core.py -k "TimelineIndex or CourseMapTimeline" -q`
Expected: PASS

Run: `pytest tests/test_file_map_unit_mapping.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py src/builder/timeline_index.py src/ui/dialogs.py tests/test_core.py tests/test_file_map_unit_mapping.py
git commit -m "refactor: extract timeline index module"
```

## Task 4: Extrair `COURSE_MAP` / `FILE_MAP` para `navigation_artifacts.py`

**Files:**
- Create: `src/builder/navigation_artifacts.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`
- Test: `tests/test_rag_enrichment.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Criar teste que garante que `course_map_md` e `file_map_md` continuam importáveis por `engine.py`**

```python
def test_engine_navigation_exports_still_work_after_split():
    from src.builder.engine import course_map_md, file_map_md

    assert callable(course_map_md)
    assert callable(file_map_md)
```

- [ ] **Step 2: Criar `navigation_artifacts.py` com os geradores e helpers relacionados**

Mover juntos:
- `course_map_md`
- `file_map_md`
- `_low_token_course_map_md`
- `_low_token_course_map_md_v2`
- `_low_token_file_map_md`
- `_budgeted_file_map_md`
- `_extract_section_headers`
- `_inject_executive_summary`
- `_clean_extraction_noise`
- `_get_entry_sections`
- `_infer_unit_confidence`

```python
course_map_md = lambda course_meta, subject_profile=None: _clamp_navigation_artifact(...)
file_map_md = _budgeted_file_map_md
```

- [ ] **Step 3: Re-exportar em `engine.py` sem mudar a assinatura**

```python
from src.builder.navigation_artifacts import (
    course_map_md,
    file_map_md,
    _extract_section_headers,
    _inject_executive_summary,
    _clean_extraction_noise,
)
```

- [ ] **Step 4: Rodar os testes de FILE_MAP / COURSE_MAP / RAG enrichment**

Run: `pytest tests/test_core.py -k "FileMap or CourseMap" -q`
Expected: PASS

Run: `pytest tests/test_rag_enrichment.py -q`
Expected: PASS

Run: `pytest tests/test_file_map_unit_mapping.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py src/builder/navigation_artifacts.py tests/test_core.py tests/test_rag_enrichment.py tests/test_file_map_unit_mapping.py
git commit -m "refactor: extract navigation artifact generation"
```

## Task 5: Extrair markdown de imagens para `image_markdown.py`

**Files:**
- Create: `src/builder/image_markdown.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_image_curation.py`

- [ ] **Step 1: Criar teste de fumaça para `RepoBuilder.inject_image_descriptions`**

```python
def test_repo_builder_image_injection_static_api_still_works():
    from src.builder.engine import RepoBuilder

    result = RepoBuilder.inject_image_descriptions("texto", {"pages": {}})
    assert isinstance(result, str)
```

- [ ] **Step 2: Mover helpers puros de markdown/imagem para `image_markdown.py`**

Mover:
- `_low_token_inject_image_descriptions`
- helpers de heading/descrição usados por essa rotina
- qualquer regex/helper que não dependa de estado do `RepoBuilder`

```python
def inject_image_descriptions(markdown: str, curation: dict) -> str:
    ...
```

- [ ] **Step 3: Reatribuir o método estático em `engine.py`**

```python
from src.builder.image_markdown import inject_image_descriptions as _inject_image_descriptions
RepoBuilder.inject_image_descriptions = staticmethod(_inject_image_descriptions)
```

- [ ] **Step 4: Rodar a suíte de image curation**

Run: `pytest tests/test_image_curation.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py src/builder/image_markdown.py tests/test_image_curation.py
git commit -m "refactor: extract image markdown utilities"
```

## Task 6: Fechar a fase 1 do split e medir redução de risco

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `docs/CLAUDE_HANDOFF.md`
- Test: `tests/test_core.py`
- Test: `tests/test_image_curation.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Revisar `engine.py` para deixar apenas fachada, `RepoBuilder` e orquestração**

Critério de aceite:
- símbolos públicos continuam em `engine.py`
- implementações movidas não ficam duplicadas
- comentários curtos explicam onde mora cada subsistema

Exemplo de topo do arquivo:

```python
from src.builder.prompt_generation import ...
from src.builder.timeline_index import ...
from src.builder.navigation_artifacts import ...
from src.builder.image_markdown import ...
```

- [ ] **Step 2: Atualizar o handoff técnico com a nova distribuição**

Adicionar seção curta:

```markdown
## Builder modules
- `engine.py`: facade + RepoBuilder orchestration
- `prompt_generation.py`: Claude/GPT/Gemini instructions
- `timeline_index.py`: schedule matching and serialization
- `navigation_artifacts.py`: COURSE_MAP / FILE_MAP / glossary helpers
- `image_markdown.py`: image description injection helpers
```

- [ ] **Step 3: Rodar a suíte completa**

Run: `pytest tests/ -q`
Expected: PASS

- [ ] **Step 4: Medir a redução de tamanho do `engine.py`**

Run: `python -c "from pathlib import Path; print(len(Path('src/builder/engine.py').read_text(encoding='utf-8').splitlines()))"`
Expected: redução perceptível em relação ao baseline atual, sem perda funcional.

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py src/builder/prompt_generation.py src/builder/timeline_index.py src/builder/navigation_artifacts.py src/builder/image_markdown.py docs/CLAUDE_HANDOFF.md
git commit -m "refactor: split engine into focused builder modules"
```

## Risks and Mitigations

- **Risco:** quebrar imports existentes em UI e testes.
  - **Mitigação:** `engine.py` continua re-exportando os mesmos símbolos até o final da fase 1.

- **Risco:** mover helpers de timeline ou FILE_MAP com dependências implícitas e criar ciclos.
  - **Mitigação:** mover clusters coesos inteiros e usar imports explícitos no novo módulo.

- **Risco:** tentar extrair `RepoBuilder` cedo demais.
  - **Mitigação:** manter `RepoBuilder` no `engine.py` nesta fase; só extrair funções puras ou quase puras.

- **Risco:** espalhar alterações de import pela UI sem necessidade.
  - **Mitigação:** fase 1 usa fachada; a UI continua importando de `engine.py`.

## Exit Criteria

- `engine.py` deixa de concentrar prompts, timeline, maps pedagógicos e helpers puros de imagem.
- O app continua funcionando sem mudar o ponto de entrada público do builder.
- Toda a suíte `tests/` continua verde.
- Os agentes conseguem editar áreas menores sem carregar um arquivo de ~11k linhas em contexto.
