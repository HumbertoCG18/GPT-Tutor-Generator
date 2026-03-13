# LLM.md — Contexto Completo do Projeto GPT-Tutor-Generator

> **Use este arquivo para dar contexto a qualquer LLM de coding (Claude Code, Codex, Antigravity, etc.).**
> Última atualização: 2026-03-13

---

## 1. O Que É Este Projeto

**Academic Tutor Repo Builder V3** — uma aplicação desktop Python/tkinter que converte PDFs acadêmicos em repositórios de conhecimento curado para sistemas de tutoria baseados em LLM.

O objetivo final é criar um **template reutilizável de tutor acadêmico** para diversas disciplinas universitárias, onde cada tutor é alimentado por Markdown curado, materiais da disciplina, cronograma, listas de exercícios, provas antigas, rubricas e acompanhamento de progresso.

### Decisões Arquiteturais Já Tomadas

- **Repositório GitHub como fonte da verdade** para cada disciplina
- **Markdown como formato principal** — PDFs ficam como material bruto, conteúdo importante é convertido/curado em `.md`
- Uma pasta `build/gpt-knowledge/` com os arquivos mais importantes para anexar ao GPT
- Sistema escalável e replicável para múltiplas disciplinas
- Suporte futuro para integração via GitHub / connector / MCP / app

### Visão do Tutor

O tutor deve ser capaz de:
- Ensinar conteúdo da disciplina
- Resolver listas de exercícios
- Preparar o aluno para provas
- Acompanhar progresso
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

### Dependências

**Core** (obrigatórias):
- `pymupdf>=1.24.0` — manipulação de PDF, extração de imagens, OCR
- `pymupdf4llm>=0.0.10` — extração Markdown otimizada para LLM
- `pdfplumber>=0.10.0` — extração de tabelas

**Opcionais** (backends avançados):
- `docling` — CLI para entendimento avançado de documentos (fórmulas, layout)
- `marker-pdf` — CLI para extração semântica de documentos

---

## 3. Estrutura do Repositório

```
GPT-Tutor-Generator/
├── academic_tutor_repo_builder_v3.py   # App principal (~1788 linhas)
├── tests/
│   ├── __init__.py
│   └── test_core.py                    # Suite de testes (~348 linhas, 11 classes)
├── pyproject.toml                      # Configuração do projeto
├── requirements.txt                    # Dependências core
├── README.md                           # Documentação (português)
├── LLM.md                             # Este arquivo
├── .gitignore                          # Python padrão
└── .gitattributes                      # Normalização de line endings
```

> **Nota:** As pastas `system/`, `course/`, `content/`, `exercises/`, `exams/`, `student/`, `build/`, `scripts/`, `raw/`, `staging/`, `manual-review/` **não existem neste repo** — elas são **geradas dinamicamente** quando o usuário cria um repositório de disciplina pela GUI.

---

## 4. Organização do Código (`academic_tutor_repo_builder_v3.py`)

O arquivo principal contém toda a lógica em ~1788 linhas, organizado assim:

### 4.1 Imports e Configuração Global (linhas 1–89)

```python
# Detecção de backends disponíveis
HAS_PYMUPDF = True/False        # via try/except import pymupdf
HAS_PYMUPDF4LLM = True/False    # via try/except import pymupdf4llm
HAS_PDFPLUMBER = True/False     # via try/except import pdfplumber
DOCLING_CLI = shutil.which("docling")        # Path ou None
MARKER_CLI = shutil.which("marker_single")   # Path ou None
```

**Constantes importantes:**
```python
APP_NAME = "Academic Tutor Repo Builder V3"

DEFAULT_CATEGORIES = [
    "course-material", "exams", "exercise-lists", "rubrics", "schedule",
    "references", "photos-of-exams", "answer-keys", "other"
]

IMAGE_CATEGORIES = {"photos-of-exams", "exams", "course-material", "other"}
PROCESSING_MODES = ["auto", "quick", "high_fidelity", "manual_assisted"]
DOCUMENT_PROFILES = ["auto", "general", "math_heavy", "layout_heavy", "scanned", "exam_pdf"]
PREFERRED_BACKENDS = ["auto", "pymupdf4llm", "pymupdf", "docling", "marker"]
OCR_LANGS = ["por", "eng", "por,eng", "eng,por"]
```

### 4.2 Funções Utilitárias (linhas ~95–210)

| Função | O que faz |
|--------|-----------|
| `slugify(value)` | `"Cálculo I - 2024/1"` → `"cálculo-i-20241"` |
| `ensure_dir(path)` | Cria diretório com pais, retorna Path |
| `write_text(path, content)` | Escreve arquivo UTF-8, cria pais |
| `parse_page_range(page_range)` | `"1-3, 5"` → `[0, 1, 2, 4]` (zero-based) |
| `pages_to_marker_range(pages)` | `[0,1,2,5,7,8]` → `"0-2,5,7-8"` |
| `file_size_mb(path)` | Tamanho em MB, 0.0 se inexistente |
| `safe_rel(path, root)` | Caminho absoluto → relativo |
| `json_str(value)` | JSON-encode para embedding em YAML |
| `wrap_frontmatter(meta, body)` | Gera YAML frontmatter + corpo Markdown |
| `rows_to_markdown_table(rows)` | Lista de listas → tabela Markdown |

### 4.3 Data Classes (linhas ~213–274)

**`FileEntry`** — representa um arquivo de entrada (PDF ou imagem):
```python
@dataclass
class FileEntry:
    source_path: str              # Caminho absoluto do arquivo original
    file_type: str                # "pdf" ou "image"
    category: str                 # Uma de DEFAULT_CATEGORIES
    title: str                    # Nome para exibição
    # ... metadados (tags, notes, professor_signal, relevant_for_exam, include_in_bundle)
    # ... config V3 (processing_mode, document_profile, preferred_backend,
    #                formula_priority, preserve_pdf_images_in_markdown, force_ocr,
    #                export_page_previews, extract_images, extract_tables,
    #                page_range, ocr_language)
    def id(self) -> str           # slugify do nome do arquivo
```

**`DocumentProfileReport`** — resultado da análise de perfil de um PDF:
```python
@dataclass
class DocumentProfileReport:
    page_count: int = 0
    text_chars: int = 0
    images_count: int = 0
    table_candidates: int = 0
    text_density: float = 0.0
    suspected_scan: bool = False
    suggested_profile: str = "general"
    notes: List[str] = field(default_factory=list)
```

**`BackendRunResult`** — resultado da execução de um backend:
```python
@dataclass
class BackendRunResult:
    name: str                     # "pymupdf4llm", "docling", etc.
    layer: str                    # "base" ou "advanced"
    status: str                   # "ok" ou "error"
    markdown_path: Optional[str]
    asset_dir: Optional[str]
    metadata_path: Optional[str]
    command: Optional[List[str]]
    notes: List[str]
    error: Optional[str]
```

**`PipelineDecision`** — decisão de quais backends usar:
```python
@dataclass
class PipelineDecision:
    entry_id: str
    processing_mode: str
    effective_profile: str
    base_backend: Optional[str]
    advanced_backend: Optional[str]
    reasons: List[str]            # Trilha de auditoria das decisões
```

### 4.4 Arquitetura de Backends (linhas ~280–605)

**Hierarquia de classes:**

```
ExtractionBackend (base abstrata)
├── PyMuPDF4LLMBackend  (name="pymupdf4llm", layer="base")
├── PyMuPDFBackend       (name="pymupdf",     layer="base")
├── DoclingCLIBackend    (name="docling",      layer="advanced")
└── MarkerCLIBackend     (name="marker",       layer="advanced")
```

Cada backend implementa:
- `available() → bool` — verifica se pode rodar no ambiente
- `run(ctx: BackendContext) → BackendRunResult` — executa a extração

**`BackendContext`** — contexto passado para cada backend:
- `root_dir`, `raw_target`, `entry`, `report`

**`BackendSelector`** — lógica de seleção:
- `available_backends() → Dict[str, bool]`
- `decide(entry, report) → PipelineDecision` — aplica regras por modo/perfil

**Regras de decisão:**

| Modo | Camada Base | Camada Avançada |
|------|-------------|-----------------|
| `quick` | ✓ (pymupdf4llm → pymupdf) | ✗ |
| `high_fidelity` | ✓ | ✓ (tenta todos disponíveis) |
| `manual_assisted` | ✓ | ✓ (se perfil justifica) |
| `auto` | ✓ | ✓ (se perfil ∈ {math_heavy, layout_heavy, scanned, exam_pdf}) |

### 4.5 RepoBuilder (linhas ~611–1010)

Classe principal de orquestração. Método `build()`:

1. `_create_structure()` — cria 43 diretórios
2. `_write_root_files()` — gera COURSE_IDENTITY.md, BACKEND_ARCHITECTURE.md, etc.
3. Para cada entry: `_process_entry()` → `_process_pdf()` ou `_process_image()`
4. `_write_source_registry()` → SOURCE_REGISTRY.yaml
5. `_write_bundle_seed()` → bundle.seed.json
6. `_write_build_report()` → BUILD_REPORT.md

**Pipeline de processamento de PDF:**
```
PDF → _profile_pdf() → BackendSelector.decide()
    → Rodar base backend → staging/markdown-auto/{backend}/{id}.md
    → Rodar advanced backend (se selecionado)
    → _extract_pdf_images() → staging/assets/images/{id}/
    → _export_page_previews() → staging/assets/page-previews/{id}/
    → _extract_tables_pdfplumber() → staging/assets/tables/{id}/
    → Gerar manual review → manual-review/pdfs/{id}.md
```

### 4.6 Templates e Geradores (linhas ~1111–1427)

Funções que geram conteúdo Markdown/YAML para o repositório criado:
- `manual_pdf_review_template()` — checklist de revisão para cada PDF
- `manual_image_review_template()` — checklist para imagens
- `pdf_curation_guide()` → `system/PDF_CURATION_GUIDE.md`
- `backend_architecture_md()` → `system/BACKEND_ARCHITECTURE.md`
- `backend_policy_yaml()` → `system/BACKEND_POLICY.yaml`
- `root_readme()` → `README.md` do repositório de disciplina

### 4.7 Interface Gráfica (linhas ~1429–1776)

**`FileEntryDialog(simpledialog.Dialog)`** — formulário para configurar cada arquivo:
- Campos para todos os atributos de `FileEntry`
- Comboboxes para categoria, modo, perfil, backend, OCR language
- Checkboxes para flags booleanas

**`App(tk.Tk)`** — janela principal (1320×820):
- Campos de metadados da disciplina (nome, slug, semestre, professor, instituição)
- Seleção de diretório raiz do repositório
- Toolbar: Add PDFs, Add Images, Edit, Duplicate, Remove, Build Repo
- Treeview listando arquivos adicionados com suas configurações
- Painel de detecção do ambiente (backends disponíveis)

### 4.8 Entry Point (linhas ~1778–1788)

```python
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
```

---

## 5. Estrutura Gerada (Repositório de Disciplina)

Quando o usuário executa "Build Repo" pela GUI, o app gera esta estrutura:

```
{course-slug}/
├── README.md
├── manifest.json                          # Log completo de processamento
├── BUILD_REPORT.md                        # Backends disponíveis + regras
│
├── system/
│   ├── BACKEND_ARCHITECTURE.md
│   ├── PDF_CURATION_GUIDE.md
│   └── BACKEND_POLICY.yaml
│
├── course/
│   ├── COURSE_IDENTITY.md                 # YAML frontmatter + info da disciplina
│   └── SOURCE_REGISTRY.yaml              # Índice de todos os arquivos processados
│
├── content/                               # Para conteúdo curado (preenchido manualmente)
│   ├── units/
│   ├── concepts/
│   ├── summaries/
│   ├── references/
│   └── curated/
│
├── exercises/                             # Para exercícios (preenchido manualmente)
│   ├── lists/
│   ├── solved/
│   └── index/
│
├── exams/                                 # Para provas (preenchido manualmente)
│   ├── past-exams/
│   ├── answer-keys/
│   └── exam-index/
│
├── student/                               # Materiais do aluno (futuro)
├── scripts/                               # Scripts de automação (futuro)
│
├── raw/                                   # Arquivos originais (preservados)
│   ├── pdfs/{category}/
│   └── images/{category}/
│
├── staging/                               # Saídas automáticas (para revisão)
│   ├── markdown-auto/
│   │   ├── pymupdf4llm/
│   │   ├── pymupdf/
│   │   ├── docling/
│   │   └── marker/
│   └── assets/
│       ├── images/
│       ├── inline-images/
│       ├── page-previews/
│       ├── tables/
│       └── table-detections/
│
├── manual-review/                         # Checklists de revisão guiada
│   ├── pdfs/
│   └── images/
│
└── build/
    └── gpt-knowledge/
        └── bundle.seed.json              # Seed para curadoria do bundle GPT
```

---

## 6. Arquivos Futuros Planejados (Ainda Não Implementados)

O design original prevê estes arquivos que **ainda não são gerados** pelo app:

| Arquivo | Função Planejada |
|---------|------------------|
| `system/LLM_SYSTEM.md` | Instruções de sistema para o tutor LLM |
| `system/INSTRUCTIONS.md` | Instruções gerais de comportamento |
| `system/PEDAGOGY.md` | Política pedagógica do tutor |
| `system/MODES.md` | Modos de interação (ensino, exercício, prova, etc.) |
| `system/OUTPUT_TEMPLATES.md` | Templates de resposta do tutor |
| `system/QUALITY_RULES.md` | Regras de qualidade das respostas |
| `course/COURSE_MAP.md` | Mapa de tópicos da disciplina |
| `course/CURRICULUM.md` | Currículo e cronograma |
| `course/ASSESSMENT_BLUEPRINT.md` | Blueprint de avaliações |
| `course/SOURCE_GUIDE.md` | Guia de fontes por tópico |
| `course/GLOSSARY.md` | Glossário da disciplina |
| `exercises/EXERCISE_INDEX.md` | Índice de exercícios por tópico |
| `exams/EXAM_INDEX.md` | Índice de provas por tópico |
| `student/PROGRESS_SCHEMA.md` | Schema de acompanhamento de progresso |
| `student/TRACKING_RULES.md` | Regras de tracking automático |
| `student/REVIEW_POLICY.md` | Política de revisão espaçada |

Esses arquivos fazem parte da visão de longo prazo do sistema de tutoria e representam a separação entre:
- **Modelo do domínio** (conteúdo da disciplina)
- **Modelo do aluno** (progresso, tracking)
- **Política pedagógica** (como o tutor ensina)
- **Recuperação de conhecimento** (índices, glossário)
- **Simulados e avaliação** (exercícios, provas)

---

## 7. Testes

**Localização:** `tests/test_core.py`
**Runner:** `python -m pytest tests/ -v`

O tkinter é mockado para rodar em CI headless:
```python
sys.modules.setdefault("tkinter", mock.MagicMock())
# ... demais módulos tkinter
```

**Cobertura de testes (11 classes):**

| Classe | O que testa |
|--------|-------------|
| `TestSlugify` | Conversão de strings para slugs |
| `TestParsePageRange` | Parsing de ranges de página |
| `TestPagesToMarkerRange` | Conversão para formato Marker CLI |
| `TestFileSizeMb` | Cálculo de tamanho de arquivo |
| `TestSafeRel` | Caminhos relativos seguros |
| `TestEnsureDirAndWriteText` | Criação de diretórios e escrita de arquivos |
| `TestWrapFrontmatter` | Geração de YAML frontmatter |
| `TestRowsToMarkdownTable` | Geração de tabelas Markdown |
| `TestFileEntry` | Data class FileEntry (id, defaults) |
| `TestBackendSelector` | Lógica de seleção de backend por modo/perfil |
| `TestDocumentProfileReport` | Data class DocumentProfileReport |

---

## 8. Comandos de Desenvolvimento

```bash
# Instalar dependências
pip install -r requirements.txt

# Instalar dev (pytest)
pip install -e ".[dev]"

# Rodar a aplicação
python academic_tutor_repo_builder_v3.py

# Rodar testes
python -m pytest tests/ -v

# Backends opcionais
pip install docling       # Docling CLI
pip install marker-pdf    # Marker CLI
```

---

## 9. Princípios de Design

1. **Resiliência** — funciona mesmo sem dependências opcionais; fallback gracioso entre backends; falhas não param o processamento
2. **Preservação de integridade** — arquivos raw separados de outputs processados; múltiplas saídas de backend para comparação; revisão manual guiada
3. **Arquitetura em camadas** — base (rápido, confiável) + avançada (rico em features); seleção configurável e sobrescrevível
4. **Orientação ao usuário** — checklists de revisão por PDF; documentação de arquitetura gerada; detecção de ambiente na UI
5. **Escalabilidade** — template replicável para qualquer disciplina; design limpo para longo prazo

---

## 10. Estado Atual e Próximos Passos

### ✅ Implementado
- App GUI completa para criação de repositórios de disciplina
- Pipeline de extração com 4 backends (2 base + 2 avançados)
- Profiling automático de PDFs
- Seleção inteligente de backend por modo/perfil
- Extração de imagens, tabelas e previews
- Geração de documentação e revisão manual guiada
- Suite de testes com 60+ assertions
- manifest.json, SOURCE_REGISTRY.yaml, bundle.seed.json

### 🔲 Próximos Passos (Visão de Longo Prazo)
- Arquivos de sistema do tutor (LLM_SYSTEM.md, PEDAGOGY.md, MODES.md, etc.)
- Schema de progresso do aluno (PROGRESS_SCHEMA.md)
- Índices inteligentes (EXERCISE_INDEX.md, EXAM_INDEX.md)
- Pipeline de bundle para GPT (compilar `build/gpt-knowledge/`)
- Integração viva via GitHub / MCP / connector
- Simulados inteligentes e resolução automática de listas
- Progress tracking automático

---

## 11. Fluxo de Trabalho do Usuário

```
1. Executar: python academic_tutor_repo_builder_v3.py
2. Preencher metadados da disciplina (nome, slug, semestre, professor, instituição)
3. Selecionar diretório raiz do repositório
4. Adicionar PDFs → categorizar, configurar modo de processamento
5. Adicionar imagens (opcional)
6. Clicar "Criar repositório"
7. Revisar staging/markdown-auto/ e manual-review/
8. Comparar saídas base vs avançada
9. Promover conteúdo curado para content/, exercises/, exams/
10. Subir para GitHub
```

---

## 12. Contexto do Prompt Original

Este projeto nasceu da necessidade de criar um **GPT Tutor acadêmico reutilizável para disciplinas universitárias**. A arquitetura escolhida é **GitHub estruturado como fonte principal + Markdown curado + bundle enxuto para anexar ao GPT**.

O sistema deve suportar separação entre:
- **Modelo do domínio** — conteúdo da disciplina em Markdown
- **Modelo do aluno** — progresso, histórico
- **Política pedagógica** — como o tutor ensina, avalia, acompanha
- **Recuperação de conhecimento** — índices por tópico, glossário
- **Simulados e avaliação** — exercícios, provas, rubricas

A primeira tarefa (já implementada) foi a conversão de PDFs acadêmicos para Markdown, que é o que o app atual faz. As próximas tarefas envolvem construir o ecossistema completo do tutor.
