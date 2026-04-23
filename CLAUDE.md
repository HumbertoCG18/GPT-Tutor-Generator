# CLAUDE.md — GPT Tutor Generator

## Comandos essenciais

```powershell
# Rodar testes
python -m pytest tests -q

# Rodar arquivo específico
python -m pytest tests/test_datalab_image_extraction.py -q

# Rodar app
python app.py
```

## Arquitetura do projeto

```text
app.py                          # bootstrap: inicia TK e chama src/ui/app.py

src/
├── builder/
│   ├── engine.py               # façade estável — orquestra chamadas entre subsistemas
│   ├── artifacts/              # COURSE_MAP, FILE_MAP, prompts, navegação e student_state
│   │   ├── navigation.py
│   │   ├── pedagogy.py
│   │   ├── prompts.py
│   │   ├── repo.py
│   │   └── student_state.py
│   ├── core/                   # utilidades centrais (config semântica, markdown, imagens)
│   │   ├── core_utils.py
│   │   ├── image_resolution.py
│   │   ├── markdown_utils.py
│   │   ├── semantic_config.py
│   │   └── source_importers.py
│   ├── extraction/             # taxonomy, sinais de entry e markdown de imagens
│   │   ├── content_taxonomy.py
│   │   ├── entry_signals.py
│   │   ├── image_markdown.py
│   │   └── teaching_plan.py
│   ├── facade/                 # wrappers configurados expostos pelo engine
│   │   ├── file_map.py
│   │   ├── glossary.py
│   │   ├── navigation_templates.py
│   │   ├── repo_docs.py
│   │   └── teaching_timeline.py
│   ├── ops/                    # operações de ciclo de vida do build
│   │   ├── bootstrap_ops.py
│   │   ├── build_workflow.py
│   │   ├── entry_processing.py
│   │   ├── incremental_build.py
│   │   ├── lifecycle_ops.py
│   │   ├── operational_artifacts.py
│   │   ├── pedagogical_regeneration.py
│   │   ├── state_ops.py
│   │   ├── task_queue_runner.py
│   │   └── url_and_cleanup.py
│   ├── pdf/                    # pipeline PDF e assets
│   │   ├── pdf_analysis.py
│   │   ├── pdf_assets.py
│   │   ├── pdf_pipeline.py
│   │   └── pdf_scanned.py
│   ├── routing/                # matching e roteamento do FILE_MAP
│   │   └── file_map.py
│   ├── runtime/                # clientes de backends externos
│   │   ├── backend_runtime.py
│   │   └── datalab_client.py
│   ├── text/                   # sanitização e conversão URL→markdown
│   │   ├── sanitization.py
│   │   └── url_markdown.py
│   ├── timeline/               # índice e sinais do cronograma
│   │   ├── index.py
│   │   └── signals.py
│   └── vision/                 # vision e classificação visual
│       ├── card_evidence.py
│       ├── image_classifier.py
│       ├── ollama_client.py
│       └── vision_client.py
├── models/
│   ├── core.py                 # dataclasses centrais (SubjectProfile, BackendRunResult, …)
│   └── task_queue.py           # RepoTask e RepoTaskStore (fila persistida)
├── ui/
│   ├── app.py                  # janela principal e roteamento de tabs
│   ├── consolidate_unit_dialog.py  # diálogo de consolidação de unidade
│   ├── curator_studio.py       # revisão manual de entradas
│   ├── dialogs.py              # configurações, status, ajuda e demais dialogs
│   ├── image_curator.py        # curadoria de imagens e extração visual
│   ├── repo_dashboard.py       # dashboard operacional de repositórios
│   └── theme.py                # tema e preferências persistidas
└── utils/
    ├── helpers.py              # helpers gerais, autodetects, OCR/Tesseract
    └── power.py                # previne sleep durante builds longos
```

## Decisões de arquitetura

### engine.py é uma façade, não o lugar certo para nova lógica
`engine.py` foi progressivamente esvaziado. Toda lógica nova deve ir para o subpacote correto. Novos consumidores diretos devem importar dos módulos focados, não de `engine.py`.

### BackendRunResult.images_dir
O campo `images_dir: Optional[str]` em `src/models/core.py` é propagado do backend Datalab quando imagens são extraídas. Ele aparece no manifest do item e é usado pelo pipeline de curadoria de imagens.

### Imagens do Datalab
O backend Datalab salva imagens em:
```
staging/markdown-auto/datalab/<entry>/images/
```
O caminho real vem de `_save_datalab_images` em `datalab_client.py` e é retornado via `BackendRunResult.images_dir`.

### Modelos de backend PDF
- `datalab`: backend principal para `math_heavy`; requer `DATALAB_API_KEY`
- `docling` / `docling_python`: alternativas locais/GPU
- `marker`: disponível, mas em investigação — não é o caminho principal
- `pymupdf4llm` / `pymupdf`: base para todos os casos simples

### Vision pipeline
- Backend: `ollama` (local)
- Endpoint padrão: `http://localhost:11434/api/chat`
- Independente do backend PDF — pode usar Datalab para PDF e Ollama para Vision ao mesmo tempo

### Fila de tarefas
`RepoTaskStore` persiste a fila em JSON entre sessões. A fila sobrevive a reinicializações do app — não recriar manualmente.

## Convenções de código

- Sem comentários óbvios; somente WHY não-óbvio
- Sem docstrings multi-parágrafo
- `Optional[X]` com default `None` para campos opcionais em dataclasses
- Imports de subpacotes focados, não de `engine.py`
- Testes ficam em `tests/test_<módulo>.py`; fixtures em `tests/fixtures/`

## Variáveis de ambiente

```env
DATALAB_API_KEY=          # obrigatória para backend datalab
DATALAB_BASE_URL=https://www.datalab.to
OPENAI_API_KEY=           # opcional
GEMINI_API_KEY=           # opcional
```

## Arquivos críticos do repositório gerado

```text
course/COURSE_MAP.md      # mapa pedagógico — ponto de entrada para Claude
course/FILE_MAP.md        # índice de roteamento com prioridade
student/STUDENT_STATE.md  # perfil e progresso do aluno
exercises/EXERCISE_INDEX.md
build/claude-knowledge/bundle.seed.json
setup/INSTRUCOES_CLAUDE_PROJETO.md
```

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

### Nota operacional: ferramentas MCP são deferred

Todos os `mcp__code-review-graph__*` e `mcp__token-savior__*` são carregados sob demanda.
Antes de chamar qualquer um deles, use `ToolSearch` com `select:<nome>` para carregar o schema.
Chamar sem carregar falha com `InputValidationError`.

## MCP Tools: token-savior

Segundo servidor MCP disponível. Ferramentas de análise estrutural complementares ao
code-review-graph: call chains, dead code, hotspots, impacto de símbolo, dependências
entre arquivos, busca estrutural via tree-sitter.

Usar quando: rastrear call chains de uma função específica, encontrar dead code,
calcular impacto de renomear um símbolo, verificar quais testes cobrem um arquivo.

Também exige `ToolSearch select:<nome>` antes de usar.

## Problemas conhecidos / dívida técnica

1. **Patch local fora do repo** — `.venv/.../marker/services/ollama.py` tem patch manual;
   se `.venv` for recriada, o patch se perde. Não há versão commitada do patch.
2. **Marker + cloud models instável** — `qwen3-vl:235b-cloud` causa 500 errors com
   Marker; usar `qwen3-vl:8b q4_K_M` (estável no RTX 4050 6GB).
3. **LaTeX corrompido silencioso** — `pymupdf4llm` pode corromper fórmulas sem sinalizar;
   usar Marker/Datalab para `math_heavy`.
4. **Stall timeout por fase incompleto** — apenas `LLM processors running` tem override;
   outras fases usam timeout geral calculado por backend.

Detalhes completos, SubjectProfile fields, regras de tema UI e checklist de edição:
`LLM_Context/CLAUDE.md`.

## Approach
- Read existing files before writing. Don't re-read unless changed.
- Thorough in reasoning, concise in output.
- Skip files over 100KB unless required.
- No sycophantic openers or closing fluff.
- No emojis or em-dashes.
- Do not guess APIs, versions, flags, commit SHAs, or package names. Verify by reading code or docs before asserting.
