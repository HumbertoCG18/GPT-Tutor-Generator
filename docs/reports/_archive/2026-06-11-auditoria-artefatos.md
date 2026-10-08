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
