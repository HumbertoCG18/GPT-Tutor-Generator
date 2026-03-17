# LLM.md — Contexto Completo do Projeto GPT-Tutor-Generator

> **Use este arquivo para dar contexto a qualquer LLM de coding (Claude Code, Codex, etc.).**
> Última atualização: 2026-03-16

---

## 1. O Que É Este Projeto

**Academic Tutor Repo Builder V3** — aplicação desktop Python/tkinter que converte PDFs acadêmicos em repositórios de conhecimento curado para sistemas de tutoria baseados em LLM.

O objetivo final é criar um **template reutilizável de tutor acadêmico** para diversas disciplinas universitárias. Cada repositório de disciplina é conectado a um **Projeto no Claude.ai**, onde o Claude atua como tutor com política pedagógica estruturada.

### Decisões Arquiteturais

- **Plataforma alvo:** Claude Projects (claude.ai) — substituiu o ChatGPT Custom GPT
- **Repositório GitHub como fonte da verdade** para cada disciplina
- **Markdown como formato principal** — PDFs ficam como material bruto, conteúdo curado vai para `.md`
- A pasta `build/claude-knowledge/` contém os arquivos para conectar ao Claude Project
- Sistema escalável e replicável para múltiplas disciplinas

### Visão do Tutor

O tutor no Claude deve ser capaz de:
- Ensinar conteúdo da disciplina (modo `study`)
- Resolver listas de exercícios sem entregar a resposta (modo `assignment`)
- Preparar para provas com foco em incidência e padrões (modo `exam_prep`)
- Acompanhar o aluno durante a aula (modo `class_companion`)
- Acompanhar progresso via `student/STUDENT_STATE.md`
- Usar cronograma e provas como parte da lógica pedagógica

---

## 2. Stack Técnica

| Item | Valor |
|------|-------|
| Linguagem | Python 3.8+ |
| UI | tkinter (desktop GUI) |
| Versão | 3.0.0 |
| Licença | MIT |
| Gerenciamento | pyproject.toml (PEP 517) |
| Testes | pytest |
| Launcher Windows | `run.bat` / `run.ps1` |

### Dependências

**Core** (obrigatórias):
- `pymupdf>=1.24.0` — manipulação de PDF, extração de imagens
- `pymupdf4llm>=0.0.10` — extração Markdown otimizada para LLM
- `pdfplumber>=0.10.0` — extração de tabelas
- `Pillow>=10.0.0` — processamento de imagens
- `python-dotenv` — gerenciamento de variáveis de ambiente

**Opcionais** (backends avançados):
- `docling` — CLI para fórmulas, layout complexo, OCR avançado
- `marker-pdf` — CLI para extração semântica

**Opcionais** (auto-categorização por LLM):
- `openai` — categorização via GPT-4o-mini
- `google-genai` — categorização via Gemini 1.5 Flash

---

## 3. Estrutura do Repositório (código-fonte)

```
GPT-Tutor-Generator/
├── app.py                              # Entry point (thin wrapper)
├── run.bat                             # Launcher Windows (CMD)
├── run.ps1                             # Launcher Windows (PowerShell)
├── src/
│   ├── __main__.py                     # Inicialização e logging
│   ├── builder/
│   │   └── engine.py                   # Pipeline de extração + geradores pedagógicos
│   ├── models/
│   │   └── core.py                     # DataClasses: FileEntry, SubjectProfile, etc.
│   ├── services/
│   │   └── llm.py                      # LLMCategorizer (OpenAI / Gemini)
│   └── ui/
│       ├── app.py                      # Janela principal (App)
│       ├── curator_studio.py           # Editor de revisão manual
│       ├── dialogs.py                  # Todos os diálogos modais
│       └── theme.py                    # ThemeManager + AppConfig
├── tests/
│   ├── __init__.py
│   └── test_core.py                    # Suite de testes (11 classes, 60+ assertions)
├── pyproject.toml
├── requirements.txt
├── LLM.md                              # Este arquivo
└── README.md
```

---

## 4. Organização do Código

### 4.1 `src/models/core.py` — Data Classes

| Classe | Função |
|--------|--------|
| `FileEntry` | Representa um arquivo de entrada (PDF, imagem, URL). Tem `to_dict()`/`from_dict()` para serialização |
| `DocumentProfileReport` | Resultado da análise de perfil de um PDF |
| `BackendRunResult` | Resultado da execução de um backend |
| `PipelineDecision` | Decisão de quais backends usar (com trilha de auditoria) |
| `SubjectProfile` | Perfil de uma matéria, inclui `queue: List[FileEntry]` persistida |
| `StudentProfile` | Perfil do aluno exportado nos repositórios |
| `SubjectStore` | Persistência de perfis em `~/.config/gpt_tutor_generator/subjects.json` |
| `StudentStore` | Persistência do perfil do aluno em `student.json` |

**Importante:** `SubjectProfile.queue` persiste a fila de arquivos pendentes por matéria. Ao selecionar uma matéria na UI, a fila é restaurada automaticamente.

### 4.2 `src/builder/engine.py` — Motor principal

**Backends de extração:**

```
ExtractionBackend (base abstrata)
├── PyMuPDF4LLMBackend  (layer="base")
├── PyMuPDFBackend       (layer="base")
├── DoclingCLIBackend    (layer="advanced")
└── MarkerCLIBackend     (layer="advanced")
```

**Classe `RepoBuilder` — métodos principais:**

| Método | Função |
|--------|--------|
| `build()` | Build completo do zero |
| `incremental_build()` | Adiciona novos entries sem recriar |
| `process_single(entry)` | Processa um único arquivo e adiciona ao manifest |
| `unprocess(entry_id)` | Remove todos os arquivos gerados de um entry e o retira do manifest |

**Geradores de arquivos pedagógicos (funções livres):**

| Função | Arquivo gerado |
|--------|---------------|
| `generate_claude_project_instructions()` | `INSTRUCOES_CLAUDE_PROJETO.md` |
| `tutor_policy_md()` | `system/TUTOR_POLICY.md` |
| `pedagogy_md()` | `system/PEDAGOGY.md` |
| `modes_md()` | `system/MODES.md` |
| `output_templates_md()` | `system/OUTPUT_TEMPLATES.md` |
| `course_map_md()` | `course/COURSE_MAP.md` |
| `glossary_md()` | `course/GLOSSARY.md` |
| `student_state_md()` | `student/STUDENT_STATE.md` |
| `progress_schema_md()` | `student/PROGRESS_SCHEMA.md` |
| `bibliography_md()` | `content/BIBLIOGRAPHY.md` |

### 4.3 `src/ui/app.py` — Interface principal

**Funcionalidades-chave:**
- Fila de arquivos salva automaticamente por matéria (`_save_current_queue()`)
- Processamento individual via botão "⚡ Processar" (`process_selected_single()`)
- Remoção de processamento via "🗑 Limpar Processamento" (`remove_processed_single()`)
- Importação rápida sem diálogo (`⚡ Importação rápida`)
- Auto-categorização por LLM antes do build
- Build incremental (detecta repositório existente e pergunta)
- Backlog tab mostra arquivos já processados via `manifest.json`

### 4.4 `src/services/llm.py` — Auto-categorização

`LLMCategorizer` usa OpenAI (gpt-4o-mini) ou Gemini (1.5-flash) para classificar PDFs automaticamente em categorias/unidades do plano de ensino.

---

## 5. Estrutura Gerada (Repositório de Disciplina)

```
{course-slug}/
├── INSTRUCOES_CLAUDE_PROJETO.md       # System prompt para Claude Projects ← NOVO
├── README.md
├── manifest.json
├── BUILD_REPORT.md
│
├── system/                            # Política pedagógica do tutor ← NOVO
│   ├── TUTOR_POLICY.md
│   ├── PEDAGOGY.md
│   ├── MODES.md
│   ├── OUTPUT_TEMPLATES.md
│   ├── BACKEND_ARCHITECTURE.md
│   ├── PDF_CURATION_GUIDE.md
│   └── BACKEND_POLICY.yaml
│
├── course/
│   ├── COURSE_IDENTITY.md
│   ├── COURSE_MAP.md                  # Mapa pedagógico ← NOVO
│   ├── GLOSSARY.md                    # Terminologia ← NOVO
│   ├── SYLLABUS.md                    # Cronograma (se preenchido)
│   └── SOURCE_REGISTRY.yaml
│
├── content/
│   ├── BIBLIOGRAPHY.md               # Referências bibliográficas ← NOVO
│   ├── units/
│   ├── concepts/
│   ├── summaries/
│   ├── references/
│   └── curated/
│
├── exercises/
│   ├── lists/
│   ├── solved/
│   └── index/
│
├── exams/
│   ├── past-exams/
│   ├── answer-keys/
│   └── exam-index/
│
├── student/
│   ├── STUDENT_STATE.md              # Progresso do aluno ← NOVO
│   ├── STUDENT_PROFILE.md
│   └── PROGRESS_SCHEMA.md            # Schema de tracking ← NOVO
│
├── scripts/
├── raw/pdfs/{category}/
├── raw/images/{category}/
├── staging/markdown-auto/{backend}/
├── staging/assets/
├── manual-review/
└── build/claude-knowledge/
    └── bundle.seed.json
```

---

## 6. Integração com Claude Projects

### Fluxo completo

```
1. Abrir app → selecionar matéria → adicionar PDFs
2. Clicar "🚀 Criar Repositório" → gera estrutura + arquivos pedagógicos
3. Revisar staging/markdown-auto/ e manual-review/
4. Promover conteúdo curado para content/, exercises/, exams/
5. Preencher COURSE_MAP.md e GLOSSARY.md manualmente
6. Push para GitHub
7. No Claude.ai → criar Projeto → Settings → conectar repositório GitHub
8. Colar conteúdo de INSTRUCOES_CLAUDE_PROJETO.md no campo "Instructions"
9. Estudar → ao final de cada sessão: Claude sugere update do STUDENT_STATE.md → commit → push
```

### Lógica de escopo das provas (embutida nos arquivos pedagógicos)

As provas são cumulativas com peso progressivo:
- **P1** → 100% conteúdo pré-P1
- **P2** → ~70% conteúdo entre P1-P2, ~30% conteúdo pré-P1
- **P3** → ~70% conteúdo entre P2-P3, ~20% P1→P2, ~10% pré-P1

---

## 7. Testes

```bash
python -m pytest tests/ -v
```

O tkinter é mockado para CI headless. 11 classes de teste, 60+ assertions cobrindo utilidades, backends e data classes.

---

## 8. Comandos de Desenvolvimento

```bash
# Instalar dependências
pip install -r requirements.txt

# Instalar dev
pip install -e ".[dev]"

# Rodar o app
python app.py
# ou no Windows:
run.bat

# Rodar testes
python -m pytest tests/ -v
```

---

## 9. Princípios de Design

1. **Separar comportamento de conteúdo** — system prompt ≠ material da matéria
2. **Separar disciplina de aluno** — conteúdo do curso ≠ estado do estudante
3. **PDF é material bruto** — Markdown curado é conhecimento operacional
4. **GitHub é a fonte da verdade** — tudo versionável, não depende de um chat
5. **Claude como camada pedagógica** — não como depósito de tudo

---

## 10. Estado Atual

### ✅ Implementado
- GUI completa com fila persistente por matéria
- Pipeline de extração com 4 backends (2 base + 2 avançados)
- Processamento individual (`process_single`) e remoção (`unprocess`)
- Build incremental e build completo
- Auto-categorização por LLM (OpenAI / Gemini)
- Curator Studio para revisão manual
- Geração completa de arquivos pedagógicos para Claude Projects
- `INSTRUCOES_CLAUDE_PROJETO.md` como system prompt do Projeto
- `STUDENT_STATE.md` para tracking de progresso
- Lógica de escopo de provas (cumulativo com peso progressivo)
- Integração GitHub (via Claude Project Settings)

### ✅ Tudo implementado
- GUI completa com fila persistente por matéria
- Pipeline de extração com 4 backends (2 base + 2 avançados)
- Processamento individual (`process_single`) e remoção (`unprocess`)
- Build completo e incremental
- Auto-categorização por LLM (OpenAI / Gemini)
- Curator Studio para revisão manual
- Todos os arquivos pedagógicos para Claude Projects
- `INSTRUCOES_CLAUDE_PROJETO.md` como system prompt do Projeto
- `STUDENT_STATE.md` para tracking de progresso
- Lógica de escopo de provas (cumulativo com peso progressivo)
- Extração automática de unidades do `teaching_plan` → `COURSE_MAP.md`
- Extração automática de referências → `BIBLIOGRAPHY.md`
- Seeding de termos → `GLOSSARY.md`
- `EXAM_INDEX.md` gerado condicionalmente (só quando há provas na fila)
- `EXERCISE_INDEX.md` gerado condicionalmente (só quando há listas na fila)
- `incremental_build` regenera todos os arquivos pedagógicos
- 61 testes passando

### 🔲 Melhorias futuras (não críticas)
- Extração de datas de prova do `syllabus` para popular `EXAM_INDEX`
- Campo de escopo de prova configurável por matéria no `SubjectManagerDialog`
- `today-context.md` gerado automaticamente antes da aula