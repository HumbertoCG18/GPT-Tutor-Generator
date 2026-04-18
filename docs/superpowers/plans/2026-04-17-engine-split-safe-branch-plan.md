# Engine Split Safe Branch Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modularizar `src/builder/engine.py` com segurança, usando branch dedicada, preservando a API pública atual e finalizando com um PR de merge para `main`.

**Architecture:** O split será incremental, com `engine.py` funcionando como facade estável durante toda a fase 1. Cada cluster funcional é movido para um módulo focado, depois reexportado por `engine.py`, e só então a duplicação antiga é removida. O trabalho inteiro acontece em uma branch dedicada de refatoração, com commits curtos por batch e validação por suíte focada.

**Tech Stack:** Python 3.11, tkinter, pytest, Git, ripgrep, PowerShell, GitHub remote.

---

## File Structure

### Arquivos já existentes que serão o centro do split

- Modify: `src/builder/engine.py`
  - Mantém `RepoBuilder`, orchestration e a facade pública durante a fase 1.
- Modify: `src/builder/content_taxonomy.py`
  - Consolidar o cluster de taxonomia/tagging já iniciado.
- Modify: `src/builder/timeline_index.py`
  - Consolidar parse/core/scoring temporal.
- Modify: `src/builder/navigation_artifacts.py`
  - Centralizar `FILE_MAP`, `COURSE_MAP` e helpers RAG de artefatos.
- Modify: `src/builder/prompt_generation.py`
  - Manter instruções Claude/GPT/Gemini e helpers de prompt fora do engine.
- Modify: `src/builder/student_state.py`
  - Manter STUDENT_STATE v2, batteries, refresh e consolidação fora do engine.
- Modify: `src/builder/image_markdown.py`
  - Manter a injeção de descrições e helpers puros de markdown/imagem.

### Arquivos de validação

- Modify: `tests/test_core.py`
- Modify: `tests/test_file_map_unit_mapping.py`
- Modify: `tests/test_rag_enrichment.py`
- Modify: `tests/test_code_review_profiles.py`
- Modify: `tests/test_image_curation.py`
- Modify: `tests/test_semantic_profile.py`

### Arquivos de documentação/coordenação

- Modify: `LLM_Context/CLAUDE_HANDOFF.md`
  - Atualizar o mapa real dos módulos do builder.
- Modify: `ROADMAP.md`
  - Opcional ao final, se o split virar marco concluído.

---

## Regras Operacionais

- O split **não** acontece em `main`.
- O split **não** acontece na branch atual de trabalho do usuário.
- O split usa branch dedicada obrigatória: `refactor/engine-modularization`.
- `engine.py` continua exportando os nomes antigos até o fim da fase 1.
- Nenhum batch pode misturar refatoração estrutural com mudança comportamental nova.
- Cada batch fecha com:
  - rewire via facade
  - remoção da duplicação antiga daquele cluster
  - testes focados
  - commit

---

## Critérios de Segurança

- Se um patch exigir mover mais de ~250 linhas com dependências cruzadas, quebrar o batch.
- Se um símbolo ainda for importado diretamente de `src/builder/engine.py` por testes ou UI, manter wrapper.
- Se um módulo novo depender de helpers ainda no engine, preferir:
  - wrapper temporário em `engine.py`, ou
  - injeção explícita de dependência
  - e **não** criar import circular.
- Não tocar primeiro em:
  - `process_single`
  - orchestration pesada de build
  - backend adapters `marker` / `docling` / `datalab`

---

## Task 1: Criar baseline seguro no Git

**Files:**
- Modify: working tree inteira

- [ ] **Step 1: Verificar estado local antes de iniciar a refatoração**

Run: `git status --short`
Expected: entender claramente se há mudanças locais pendentes que precisam entrar no commit de backup.

- [ ] **Step 2: Criar um commit de backup na branch atual**

Run:

```bash
git add -A
git commit -m "chore: backup before engine modularization split"
```

Expected: commit criado com o estado de partida estável.

- [ ] **Step 3: Criar a branch dedicada do split**

Run:

```bash
git switch -c refactor/engine-modularization
```

Expected: HEAD na branch nova.

- [ ] **Step 4: Confirmar que a branch ativa é a dedicada**

Run: `git branch --show-current`
Expected: `refactor/engine-modularization`

- [ ] **Step 5: Commit de checkpoint operacional**

Run:

```bash
git commit --allow-empty -m "chore: start engine modularization branch"
```

Expected: ponto de início explícito da branch de refatoração.

---

## Task 2: Congelar a API pública mínima do engine

**Files:**
- Modify: `tests/test_core.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Garantir um smoke test da API pública que não pode quebrar**

Adicionar ou ajustar em `tests/test_core.py` algo neste formato:

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

- [ ] **Step 2: Rodar o teste para fixar o contrato**

Run: `python -m pytest tests/test_core.py::test_engine_public_api_smoke_import -q`
Expected: `1 passed`

- [ ] **Step 3: Marcar `engine.py` explicitamente como facade**

Adicionar no topo de `src/builder/engine.py` um comentário curto:

```python
# Public facade for builder functionality during modularization.
# Keep stable exports here while moving implementations into focused modules.
```

- [ ] **Step 4: Rodar regressão curta de artefatos e prompts**

Run: `python -m pytest tests/test_core.py -k "PromptArchitectureAlignment or engine_public_api_smoke_import" -q`
Expected: PASS

- [ ] **Step 5: Commit**

Run:

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "test: lock engine facade api before modularization"
```

---

## Task 3: Fechar o split do cluster de taxonomia/semântica

**Files:**
- Modify: `src/builder/content_taxonomy.py`
- Modify: `src/builder/semantic_config.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_semantic_profile.py`
- Test: `tests/test_file_map_unit_mapping.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Validar o estado atual do cluster já iniciado**

Ler e confirmar em `engine.py` e `content_taxonomy.py`:
- `_build_tag_catalog`
- `_build_content_taxonomy`
- `_write_internal_content_taxonomy`
- `_collect_strong_heading_candidates`
- `_extract_markdown_lead_text`
- `_infer_entry_auto_tags`
- `_write_tag_catalog`
- `_refresh_manifest_auto_tags`

Objetivo: identificar o que ainda está duplicado entre `engine.py` e `content_taxonomy.py`.

- [ ] **Step 2: Rewire `engine.py` para delegar ao módulo novo**

Manter nomes antigos em `engine.py`, mas transformar as implementações em wrappers finos, por exemplo:

```python
def _build_tag_catalog(...):
    return build_tag_catalog(...)
```

Para `_build_content_taxonomy(...)`, passar explicitamente:
- `_parse_units_from_teaching_plan`
- `_topic_text`
- `_normalize_unit_slug`

- [ ] **Step 3: Remover as implementações duplicadas antigas do engine**

Critério:
- a implementação real mora em `content_taxonomy.py`
- `engine.py` só reexporta/delega
- nenhum símbolo duplicado do cluster permanece no engine

- [ ] **Step 4: Rodar os testes focados do cluster**

Run:

```bash
python -m pytest tests/test_semantic_profile.py -q
python -m pytest tests/test_file_map_unit_mapping.py -q
python -m pytest tests/test_core.py -k "engine_public_api_smoke_import or file_map_prefers_cached_content_taxonomy_and_timeline_context or course_map_prefers_cached_timeline_and_assessment_context" -q
```

Expected: PASS

- [ ] **Step 5: Commit**

Run:

```bash
git add src/builder/engine.py src/builder/content_taxonomy.py src/builder/semantic_config.py tests/test_semantic_profile.py tests/test_file_map_unit_mapping.py tests/test_core.py
git commit -m "refactor: finish extracting content taxonomy facade"
```

---

## Task 4: Fechar o split do cluster de timeline

**Files:**
- Modify: `src/builder/timeline_index.py`
- Modify: `src/builder/timeline_signals.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Mapear o que ainda é timeline no engine**

Localizar em `src/builder/engine.py`:
- parse de cronograma
- normalização de datas/períodos
- block building
- scoring temporal
- escrita de `.timeline_index.json`
- resolução de `manual_timeline_block_id`

- [ ] **Step 2: Definir o corte seguro do batch**

Mover para `timeline_index.py` tudo que for:
- parser
- normalizador
- scorer
- serializer

Mas manter em `engine.py` apenas wrappers e qualquer pedaço que ainda esteja diretamente acoplado ao `RepoBuilder`.

- [ ] **Step 3: Rewire via facade**

Em `engine.py`, reexportar/delegar pelo menos:
- `_build_timeline_index`
- `_serialize_timeline_index`
- `_write_internal_timeline_index`
- helpers temporais ainda usados por testes

- [ ] **Step 4: Remover duplicação antiga do cluster**

Critério:
- parse/core/scoring timeline não ficam duplicados entre os dois módulos

- [ ] **Step 5: Rodar regressão focada**

Run:

```bash
python -m pytest tests/test_file_map_unit_mapping.py -q
python -m pytest tests/test_core.py -k "timeline or course_map_prefers_cached_timeline_and_assessment_context or engine_public_api_smoke_import" -q
```

Expected: PASS

- [ ] **Step 6: Commit**

Run:

```bash
git add src/builder/engine.py src/builder/timeline_index.py src/builder/timeline_signals.py tests/test_file_map_unit_mapping.py tests/test_core.py
git commit -m "refactor: extract timeline core behind engine facade"
```

---

## Task 5: Fechar o split de prompt generation

**Files:**
- Modify: `src/builder/prompt_generation.py`
- Modify: `src/builder/pedagogical_prompts.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`
- Test: `tests/test_code_review_profiles.py`

- [ ] **Step 1: Revisar a divisão atual entre `prompt_generation.py` e `pedagogical_prompts.py`**

Confirmar onde moram:
- `generate_claude_project_instructions`
- `generate_gpt_instructions`
- `generate_gemini_instructions`
- `tutor_policy_md`
- `modes_md`
- `output_templates_md`
- helpers de `code_review`

- [ ] **Step 2: Consolidar o cluster em módulos de prompt, não no engine**

Objetivo:
- implementação real fica fora do engine
- `engine.py` apenas reexporta os geradores e helpers públicos

- [ ] **Step 3: Remover duplicação residual no engine**

Critério:
- `engine.py` não mantém cópias antigas desses geradores

- [ ] **Step 4: Rodar testes focados**

Run:

```bash
python -m pytest tests/test_code_review_profiles.py -q
python -m pytest tests/test_core.py -k "PromptArchitectureAlignment or SystemPromptFileReferences or engine_public_api_smoke_import" -q
```

Expected: PASS

- [ ] **Step 5: Commit**

Run:

```bash
git add src/builder/engine.py src/builder/prompt_generation.py src/builder/pedagogical_prompts.py tests/test_core.py tests/test_code_review_profiles.py
git commit -m "refactor: keep prompt generation outside engine"
```

---

## Task 6: Fechar o split de navigation artifacts e RAG helpers

**Files:**
- Modify: `src/builder/navigation_artifacts.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_rag_enrichment.py`
- Test: `tests/test_file_map_unit_mapping.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Confirmar o contrato atual de `navigation_artifacts.py`**

Verificar onde estão:
- `course_map_md`
- `file_map_md`
- variantes low-token/budgeted
- `_extract_section_headers`
- `_inject_executive_summary`
- `_clean_extraction_noise`
- `_get_entry_sections`
- `_infer_unit_confidence`

- [ ] **Step 2: Deixar o engine apenas como facade desses artefatos**

Garantir que qualquer import antigo de `src.builder.engine` continue válido.

- [ ] **Step 3: Remover sobra duplicada do engine**

Critério:
- nenhuma implementação real desse cluster fica duplicada no engine

- [ ] **Step 4: Rodar regressão focada**

Run:

```bash
python -m pytest tests/test_rag_enrichment.py -q
python -m pytest tests/test_file_map_unit_mapping.py -q
python -m pytest tests/test_core.py -k "FileMap or CourseMap or engine_public_api_smoke_import" -q
```

Expected: PASS

- [ ] **Step 5: Commit**

Run:

```bash
git add src/builder/engine.py src/builder/navigation_artifacts.py tests/test_rag_enrichment.py tests/test_file_map_unit_mapping.py tests/test_core.py
git commit -m "refactor: move navigation artifacts behind engine facade"
```

---

## Task 7: Fechar o split de STUDENT_STATE / batteries

**Files:**
- Modify: `src/builder/student_state.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`
- Test: `tests/test_student_state_v2.py` (se existir)
- Test: `tests/test_consolidate_unit.py` (se existir)

- [ ] **Step 1: Revisar o que ainda está no engine**

Localizar no engine qualquer implementação restante ligada a:
- geração do `STUDENT_STATE.md`
- batteries
- refresh de `active_unit_progress`
- consolidação de unidade
- migração v1→v2

- [ ] **Step 2: Consolidar em `student_state.py`**

Mover ou manter lá a implementação real, deixando no engine apenas wrappers.

- [ ] **Step 3: Garantir que o contrato map-first e STUDENT_STATE v2 não mudam**

Não alterar:
- formato YAML
- `student/batteries/...`
- fluxo de consolidação

- [ ] **Step 4: Rodar regressão focada**

Run:

```bash
python -m pytest tests/test_core.py -k "student_state or engine_public_api_smoke_import" -q
```

Se houver testes específicos:

```bash
python -m pytest tests/test_student_state_v2.py -q
python -m pytest tests/test_consolidate_unit.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

Run:

```bash
git add src/builder/engine.py src/builder/student_state.py tests/test_core.py
git commit -m "refactor: keep student state subsystem outside engine"
```

---

## Task 8: Fechar o split de image markdown helpers

**Files:**
- Modify: `src/builder/image_markdown.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_image_curation.py`

- [ ] **Step 1: Confirmar que a API do `RepoBuilder` continua estável**

Critério mínimo:
- `RepoBuilder.inject_image_descriptions(...)` continua existindo
- delega para `image_markdown.py`

- [ ] **Step 2: Remover qualquer duplicação residual no engine**

Se ainda houver helpers antigos de markdown/imagem duplicados, remover após confirmar o wrapper.

- [ ] **Step 3: Rodar regressão focada**

Run:

```bash
python -m pytest tests/test_image_curation.py -q
python -m pytest tests/test_core.py -k "engine_public_api_smoke_import" -q
```

Expected: PASS

- [ ] **Step 4: Commit**

Run:

```bash
git add src/builder/engine.py src/builder/image_markdown.py tests/test_image_curation.py tests/test_core.py
git commit -m "refactor: keep image markdown helpers outside engine"
```

---

## Task 9: Reduzir o engine ao papel de facade + orchestration

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `LLM_Context/CLAUDE_HANDOFF.md`
- Test: `tests/test_core.py`

- [ ] **Step 1: Revisar o topo do engine**

Objetivo:
- imports claros por subsistema
- comentário curto explicando:
  - facade pública
  - orchestration
  - `RepoBuilder`

- [ ] **Step 2: Garantir que `engine.py` não mantém implementações duplicadas dos clusters já extraídos**

Checklist:
- prompts
- timeline
- taxonomy
- navigation artifacts
- image markdown
- student state

- [ ] **Step 3: Atualizar o handoff técnico**

Adicionar em `LLM_Context/CLAUDE_HANDOFF.md` uma seção curta como:

```markdown
## Builder modules
- `engine.py`: facade pública + RepoBuilder + orchestration
- `content_taxonomy.py`: tags, taxonomy e auto-tagging
- `timeline_index.py`: parse/scoring/serialization de timeline
- `navigation_artifacts.py`: FILE_MAP, COURSE_MAP e helpers RAG
- `prompt_generation.py`: instruções Claude/GPT/Gemini
- `student_state.py`: STUDENT_STATE v2, batteries e consolidação
- `image_markdown.py`: injeção de descrições de imagem
```

- [ ] **Step 4: Rodar regressão ampla do core**

Run:

```bash
python -m pytest tests/test_core.py -q
```

Expected: PASS

- [ ] **Step 5: Medir o tamanho final do engine**

Run:

```bash
python -c "from pathlib import Path; print(len(Path('src/builder/engine.py').read_text(encoding='utf-8').splitlines()))"
```

Expected: redução perceptível em relação ao baseline inicial.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/builder/engine.py LLM_Context/CLAUDE_HANDOFF.md tests/test_core.py
git commit -m "refactor: reduce engine to facade and orchestration"
```

---

## Task 10: Regressão final e preparação para PR

**Files:**
- Modify: branch inteira

- [ ] **Step 1: Rodar a suíte focada completa do builder**

Run:

```bash
python -m pytest tests/test_core.py -q
python -m pytest tests/test_file_map_unit_mapping.py -q
python -m pytest tests/test_rag_enrichment.py -q
python -m pytest tests/test_code_review_profiles.py -q
python -m pytest tests/test_image_curation.py -q
python -m pytest tests/test_semantic_profile.py -q
```

Expected: PASS

- [ ] **Step 2: Rodar a suíte completa do projeto**

Run: `python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 3: Revisar diff final da branch**

Run:

```bash
git status --short
git diff --stat main...HEAD
```

Expected:
- working tree limpa
- diff coerente com refatoração estrutural

- [ ] **Step 4: Publicar a branch no remoto**

Run:

```bash
git push -u origin refactor/engine-modularization
```

Expected: branch publicada.

- [ ] **Step 5: Criar o Pull Request para `main`**

Se GitHub CLI estiver autenticado:

```bash
gh pr create --base main --head refactor/engine-modularization --title "refactor: modularize builder engine safely" --body "## Summary
- split engine.py by subsystem behind a stable facade
- preserved public builder API during phase 1
- validated focused and full pytest suites

## Main modules
- content_taxonomy.py
- timeline_index.py
- navigation_artifacts.py
- prompt_generation.py
- student_state.py
- image_markdown.py

## Validation
- pytest tests/ -q
"
```

Expected: PR aberto contra `main`.

- [ ] **Step 6: Commit final de housekeeping, se necessário**

Só se houver ajuste final pequeno pós-regressão:

```bash
git add -A
git commit -m "chore: final cleanup after engine modularization"
git push
```

---

## Self-Review

### Cobertura do objetivo

- Branch dedicada obrigatória: coberta em Task 1
- Split seguro por batches: Tasks 2–9
- Preservar arquitetura atual do projeto: refletido em facade + módulos já existentes
- PR final para `main`: Task 10

### Riscos reais cobertos

- Quebra de import público: mitigada por wrappers/reexports em `engine.py`
- Import circular: mitigado por cortes por cluster e injeção explícita quando necessário
- Refatoração misturada com mudança de comportamento: proibida nas regras operacionais
- Regressão silenciosa: mitigada por testes focados por cluster + suíte final

### O que este plano evita de propósito

- Não tenta modularizar `RepoBuilder` inteiro de uma vez
- Não tenta separar backends pesados cedo
- Não força mudança de assinatura pública durante o split

