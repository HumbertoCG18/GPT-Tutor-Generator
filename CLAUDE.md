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
