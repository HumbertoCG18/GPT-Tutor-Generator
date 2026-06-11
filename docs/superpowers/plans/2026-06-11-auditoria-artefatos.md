# Auditoria e limpeza de artefatos (#18) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Registrar um documento de auditoria de artefatos de build (contrato-referência) e remover completamente o artefato morto `build/PROGRESS_SCHEMA.md`.

**Architecture:** Duas entregas independentes. Task 1 cria um doc Markdown de auditoria (sem código). Task 2 remove a geração de `PROGRESS_SCHEMA.md` threading por 6 arquivos na ordem consumidor→produtor, mais um teste de regressão e adição ao stale-delete para limpar repos existentes.

**Tech Stack:** Python 3.13, pytest. Sem libs novas.

**Spec:** `docs/superpowers/specs/2026-06-11-auditoria-artefatos-design.md`

---

## Contexto de codebase (leia antes de começar)

- O projeto gera um repositório de tutor LLM. ~70-90 artefatos por build, escritos por `src/builder/ops/*` e `src/builder/artifacts/*`.
- `PROGRESS_SCHEMA.md` é um doc estático (schema do `STUDENT_STATE.md`). É **morto**: 0 referências fora dos write-sites, ausente de `prompts.py`, não lido por nada. Confirmado por investigação.
- Os 3 "impls" de build recebem geradores como kwargs vindos de `engine.py`. Remover o artefato exige remover o gerador, o alias do facade, o alias/kwargs do engine, e o param+write de cada impl.
- A suíte tem ~1191 testes verdes. Nenhum referencia `PROGRESS_SCHEMA` (verificado). Não quebrar nada.
- Hook pre-commit `code-review-graph` imprime um `UnicodeEncodeError` inofensivo no Windows; o commit conclui mesmo assim — verificar com `git log -1 --oneline`.

## File Structure

- **Create** `docs/reports/2026-06-11-auditoria-artefatos.md` — doc de auditoria (Task 1). Tabela de inventário + nota de manutenção + registro da ação.
- **Modify (Task 2):**
  - `src/builder/artifacts/repo.py` — remover gerador `progress_schema_md`.
  - `src/builder/facade/repo_docs.py` — remover alias + entrada no dict.
  - `src/builder/engine.py` — remover alias, entrada na lista, 3 kwargs.
  - `src/builder/ops/bootstrap_ops.py` — remover param + write.
  - `src/builder/ops/incremental_build.py` — remover param + write condicional.
  - `src/builder/ops/pedagogical_regeneration.py` — remover param + write condicional; adicionar build/ ao stale-delete.
- **Test (Task 2):** `tests/test_artifact_cleanup.py` (novo) — regressão.

---

### Task 1: Documento de auditoria de artefatos

**Files:**
- Create: `docs/reports/2026-06-11-auditoria-artefatos.md`

Não há teste de código (é um documento). A validação é revisão humana.

- [ ] **Step 1: Criar o documento com o conteúdo abaixo (exato)**

Crie `docs/reports/2026-06-11-auditoria-artefatos.md` com este conteúdo:

```markdown
# Auditoria de artefatos de build

date: 2026-06-11
roadmap: #18

## Como usar este documento

Contrato-referência dos artefatos que um build gera no repositório do tutor.
**Princípio de manutenção:** a cada novo artefato adicionado a um build,
acrescente uma linha na tabela com sua classe e consumidor. A cada adição de
feature, revise se algum artefato virou redundante.

Classes:
- **código-lê** — lido de volta por builder/UI/testes.
- **tutor-facing** — referenciado nas instruções do tutor (`prompts.py`) ou em
  outro artefato que o tutor lê.
- **diagnóstico-humano** — não lido por código, mas é referência/diagnóstico que
  uma pessoa abre no repo gerado.
- **morto** — ninguém lê e sem valor humano → candidato a remoção.

## Inventário

| Artefato | Gerador (file:line) | Consumidor | Classe | Verdito |
|---|---|---|---|---|
| `manifest.json` | build_workflow.py:123 | builder/UI (re-import) | código-lê | manter |
| `course/COURSE_MAP.md` | bootstrap_ops.py:144 | prompts.py (todas variantes) | tutor-facing | manter |
| `course/FILE_MAP.md` | build_workflow.py:105 | prompts.py | tutor-facing | manter |
| `course/GLOSSARY.md` | bootstrap_ops.py:145 | prompts.py | tutor-facing | manter |
| `course/SYLLABUS.md` | bootstrap_ops.py:168 | prompts.py (condicional) | tutor-facing | manter |
| `course/COURSE_IDENTITY.md` | bootstrap_ops.py:109 | — | diagnóstico-humano | manter |
| `course/SOURCE_REGISTRY.yaml` | repo.py:389 | — | diagnóstico-humano | manter |
| `course/CODE_HEALTH.md` | repo.py:1026 | — (UI não expõe ao vivo) | diagnóstico-humano | manter |
| `course/CODE_INDEX.md` | pedagogical_regeneration.py:352 | pedagogy.py (modo code_review) | tutor-facing | manter |
| `course/CRONOGRAMA_DETALHADO.md` | pedagogical_regeneration.py:364 | MODES.md (tutor) | tutor-facing | manter |
| `course/CRONOGRAMA_HEALTH.md` | cronograma_health.py:161 | — (UI não expõe ao vivo) | diagnóstico-humano | manter |
| `course/.assessment_context.json` | repo.py:164 | routing/file_map | código-lê | manter |
| `course/.content_taxonomy.json` | content_taxonomy.py:519 | routing | código-lê | manter |
| `course/.timeline_index.json` | pedagogical_regeneration.py:212 | file_map/UI | código-lê | manter |
| `course/.tag_catalog.json` | content_taxonomy.py:759 | routing semântico | código-lê | manter |
| `course/.semantic_profile.generated.json` | semantic_config.py:360 | routing | código-lê | manter |
| `system/TUTOR_POLICY.md` | bootstrap_ops.py:135 | prompts.py | tutor-facing | manter |
| `system/PEDAGOGY.md` | bootstrap_ops.py:136 | prompts.py | tutor-facing | manter |
| `system/MODES.md` | bootstrap_ops.py:137 | prompts.py | tutor-facing | manter |
| `system/OUTPUT_TEMPLATES.md` | bootstrap_ops.py:138 | prompts.py + testes | tutor-facing | manter |
| `student/STUDENT_STATE.md` | bootstrap_ops.py:155 | prompts.py (parse YAML) | tutor-facing | manter |
| `student/STUDENT_PROFILE.md` | bootstrap_ops.py:165 | prompts.py (condicional) | tutor-facing | manter |
| `student/batteries/<unit>/<topic>.md` | student_state.py:257 | tutor (histórico) | tutor-facing | manter |
| `build/PROGRESS_SCHEMA.md` | repo.py:42 | — (0 refs; STUDENT_STATE é auto-descritivo) | morto | **REMOVIDO (11/06)** |
| `build/BACKEND_POLICY.yaml` | bootstrap_ops.py:142 | extração PDF | código-lê | manter |
| `build/PDF_CURATION_GUIDE.md` | bootstrap_ops.py:140 | — | diagnóstico-humano | manter |
| `build/BACKEND_ARCHITECTURE.md` | bootstrap_ops.py:141 | — | diagnóstico-humano | manter |
| `build/claude-knowledge/bundle.seed.json` | repo.py:440 | testes/UI/export | código-lê | manter |
| `BUILD_REPORT.md` | repo.py:502 | — (+ build_metrics 11/06) | diagnóstico-humano | manter |
| `setup/INSTRUCOES_CLAUDE_PROJETO.md` | prompts.py:478 | é a instrução do tutor | tutor-facing | manter |
| `setup/INSTRUCOES_GPT_PROJETO.md` | prompts.py:498 | idem | tutor-facing | manter |
| `setup/INSTRUCOES_GEMINI_PROJETO.md` | prompts.py (gemini) | idem | tutor-facing | manter |
| `setup/CONTEXTO_TEMPORAL.md` | pedagogical_regeneration.py:388 | prompts.py | tutor-facing | manter |
| `content/BIBLIOGRAPHY.md` | bootstrap_ops.py:171 | prompts.py | tutor-facing | manter |
| `content/images/*` | image_resolution.py:248 | tutor (refs em md) | tutor-facing | manter |
| `exercises/EXERCISE_INDEX.md` | pedagogical_regeneration.py:326 | prompts.py | tutor-facing | manter |
| `exams/EXAM_INDEX.md` | pedagogical_regeneration.py:321 | tutor | tutor-facing | manter |
| `assignments/ASSIGNMENT_INDEX.md` | pedagogical_regeneration.py:343 | tutor | tutor-facing | manter |
| `whiteboard/WHITEBOARD_INDEX.md` | pedagogical_regeneration.py:404 | tutor | tutor-facing | manter |
| `.deeptutor/*` (SOUL, README, knowledge/*) | deeptutor.py:266 | export externo (todo build) | código-lê | manter |
| `staging/*`, `raw/*`, `manual-review/*` | engine.py / importers | intermediários de processamento | código-lê | manter |

## Ação desta passada (11/06/2026)

Removido `build/PROGRESS_SCHEMA.md` (artefato morto): doc estático do schema do
STUDENT_STATE, sem nenhum consumidor e ausente das instruções do tutor; o
próprio `STUDENT_STATE.md` é auto-descritivo. Geração removida; path adicionado
ao stale-delete para limpar repos já construídos no próximo build.

## Decisões de "manter" que parecem candidatas mas não são

- **CODE_HEALTH.md / CRONOGRAMA_HEALTH.md** — write-only pelo código, mas são o
  ÚNICO lugar do diagnóstico (cobertura, bandas de confiança, conflitos). A UI
  não expõe isso ao vivo. Remover perderia informação.
- **COURSE_IDENTITY.md / SOURCE_REGISTRY.yaml** — metadados/traceability para
  humano. Baratos, sem redundância.
- **Índices por categoria / 3 INSTRUCOES_* / health reports** — consolidar seria
  alto risco e baixo valor; mantidos separados por design.
```

- [ ] **Step 2: Commit**

```bash
git add docs/reports/2026-06-11-auditoria-artefatos.md
git commit -m "docs(audit): inventario de artefatos de build (#18)"
```
Verifique: `git log -1 --oneline` (o hook pode imprimir UnicodeEncodeError inofensivo).

---

### Task 2: Remover `PROGRESS_SCHEMA.md` completamente

**Files:**
- Test: `tests/test_artifact_cleanup.py` (criar)
- Modify: `src/builder/ops/bootstrap_ops.py`, `src/builder/ops/incremental_build.py`, `src/builder/ops/pedagogical_regeneration.py`, `src/builder/engine.py`, `src/builder/facade/repo_docs.py`, `src/builder/artifacts/repo.py`

- [ ] **Step 1: Write the failing regression test**

Crie `tests/test_artifact_cleanup.py`:

```python
def test_progress_schema_generator_removed():
    """O gerador morto progress_schema_md não deve mais existir."""
    import src.builder.artifacts.repo as repo
    assert not hasattr(repo, "progress_schema_md")


def test_build_progress_schema_in_stale_delete(tmp_path):
    """build/PROGRESS_SCHEMA.md deve ser limpo em repos existentes:
    o path precisa estar na lista de stale-delete da regeneração."""
    import inspect
    import src.builder.ops.pedagogical_regeneration as pr
    src = inspect.getsource(pr.regenerate_pedagogical_files)
    assert '"build"' in src and 'PROGRESS_SCHEMA.md' in src
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_artifact_cleanup.py -v`
Expected: `test_progress_schema_generator_removed` FAILS (symbol still exists). The second test may pass or fail depending on current source; both must pass at the end.

- [ ] **Step 3: Remove the write-site + param in `bootstrap_ops.py`**

In `src/builder/ops/bootstrap_ops.py`, remove the parameter `progress_schema_md_fn,` from the `write_root_files` signature (line ~86) and remove the write line (line ~156):
```python
    write_text(builder.root_dir / "build" / "PROGRESS_SCHEMA.md", progress_schema_md_fn())
```
Delete that entire line. And delete the `progress_schema_md_fn,` entry from the function's parameter list.

- [ ] **Step 4: Remove the write-site + param in `incremental_build.py`**

In `src/builder/ops/incremental_build.py`:
- Change the signature (line ~15) from
  ```python
  def incremental_build_impl(builder, *, student_state_md_fn, progress_schema_md_fn) -> None:
  ```
  to
  ```python
  def incremental_build_impl(builder, *, student_state_md_fn) -> None:
  ```
- Delete the conditional write block (lines ~105-107):
  ```python
      progress_path = builder.root_dir / "build" / "PROGRESS_SCHEMA.md"
      if not progress_path.exists():
          write_text(progress_path, progress_schema_md_fn())
  ```

- [ ] **Step 5: Remove the write-site + param + add stale-delete in `pedagogical_regeneration.py`**

In `src/builder/ops/pedagogical_regeneration.py`:
- Remove the parameter `progress_schema_md_fn,` from the `regenerate_pedagogical_files` signature (line ~166).
- Delete the conditional write block (lines ~416-418):
  ```python
      progress_path = builder.root_dir / "build" / "PROGRESS_SCHEMA.md"
      if not progress_path.exists():
          write_text(progress_path, progress_schema_md_fn())
  ```
- Add `build/PROGRESS_SCHEMA.md` to the `stale_files` list (lines ~176-181) so existing repos get it removed. The list becomes:
  ```python
      stale_files = [
          builder.root_dir / "system" / "PDF_CURATION_GUIDE.md",
          builder.root_dir / "system" / "BACKEND_ARCHITECTURE.md",
          builder.root_dir / "system" / "BACKEND_POLICY.yaml",
          builder.root_dir / "student" / "PROGRESS_SCHEMA.md",
          builder.root_dir / "build" / "PROGRESS_SCHEMA.md",
      ]
  ```

- [ ] **Step 6: Remove the engine alias, list entry, and 3 kwargs in `engine.py`**

In `src/builder/engine.py`:
- Delete the kwarg `progress_schema_md_fn=progress_schema_md,` at line ~1789 (inside the `write_root_files` call).
- Delete the kwarg `progress_schema_md_fn=progress_schema_md,` at line ~2104 (inside the `_incremental_build_impl` call).
- Delete the kwarg `progress_schema_md_fn=progress_schema_md,` at line ~2164 (inside the pedagogical regeneration call).
- Delete the alias line `progress_schema_md = _repo_doc_aliases["progress_schema_md"]` (line ~2331).
- Delete the entry `"progress_schema_md",` from the names list (line ~2423).

- [ ] **Step 7: Remove the facade alias + dict entry in `repo_docs.py`**

In `src/builder/facade/repo_docs.py`:
- Delete line ~18: `progress_schema_md = repo_artifacts_module.progress_schema_md`
- Delete the dict entry `"progress_schema_md": progress_schema_md,` (line ~43).

- [ ] **Step 8: Remove the generator in `repo.py`**

In `src/builder/artifacts/repo.py`, delete the entire function `progress_schema_md()` (lines ~42-92). Remove any now-stranded blank lines.

- [ ] **Step 9: Run the regression test + grep verification**

Run: `pytest tests/test_artifact_cleanup.py -v`
Expected: both tests PASS.

Run grep to confirm the symbol is gone everywhere:
```bash
git grep -n "progress_schema_md" -- src/ tests/
```
Expected: NO matches (the symbol is fully removed).

```bash
git grep -n "PROGRESS_SCHEMA" -- src/
```
Expected: only the two `stale_files` path strings in `pedagogical_regeneration.py` (`student/PROGRESS_SCHEMA.md` and `build/PROGRESS_SCHEMA.md`).

- [ ] **Step 10: Run the full suite (no regressions)**

Run: `pytest -q`
Expected: all pass (was 1191; now 1191 + 2 new = 1193, minus any test that asserted PROGRESS_SCHEMA existence — none expected).

- [ ] **Step 11: Commit**

```bash
git add src/builder/artifacts/repo.py src/builder/facade/repo_docs.py src/builder/engine.py src/builder/ops/bootstrap_ops.py src/builder/ops/incremental_build.py src/builder/ops/pedagogical_regeneration.py tests/test_artifact_cleanup.py
git commit -m "refactor(artifacts): remove PROGRESS_SCHEMA.md morto (#18)"
```
Verifique `git log -1 --oneline` (hook UnicodeEncodeError inofensivo).

---

## Pós-implementação

Após as duas tasks + review final:
- `pytest -q` verde.
- Atualizar `docs/reports/2026-06-09-relatorio-sistema.html`: marcar #18 como ✅ FEITO (roadmap item 18, ~linha 433, e priorização linha 447). Descrever: doc de auditoria criado + PROGRESS_SCHEMA removido; conjunto confirmado bem curado (sem outros mortos); health/identity/registry mantidos com justificativa.

## Self-Review (autor do plano)

1. **Spec coverage:** Entregável 1 (doc auditoria) → Task 1. Entregável 2 (remover PROGRESS_SCHEMA: gerador, facade, engine alias+lista+3 kwargs, 3 impls param+write, stale-delete) → Task 2 steps 3-8. Validação (grep + suíte) → Task 2 steps 9-10. Ordem consumidor→produtor da spec → steps 3-8 seguem write-sites/impls (3-5), engine (6), facade (7), gerador (8). ✔
2. **Placeholder scan:** Sem TBD/TODO; cada step tem o trecho exato a remover/alterar e comando com saída esperada. Linhas marcadas "~" porque edições anteriores no mesmo arquivo deslocam números — o trecho de código citado é a âncora exata. ✔
3. **Type consistency:** Nome do símbolo `progress_schema_md` / kwarg `progress_schema_md_fn` usado de forma idêntica em todos os steps. Teste `tests/test_artifact_cleanup.py` consistente entre steps 1 e 9. ✔
