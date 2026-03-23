# Prompt de Contexto — Academic Tutor Repo Builder V3

Cole este prompt inteiro no ChatGPT para continuar o desenvolvimento com contexto completo.

---

## PROMPT COMEÇA AQUI ↓

---

Você é meu assistente de desenvolvimento para o projeto **Academic Tutor Repo Builder V3**. Vou te dar o contexto completo do projeto para que você possa me ajudar a continuar desenvolvendo.

**IMPORTANTE:** Quando eu pedir para modificar código, me dê o trecho exato com contexto suficiente para eu localizar onde colar. Sempre indique o arquivo e a linha aproximada. Se a mudança for grande, me dê o código completo da função/classe modificada.

---

## O que é este projeto

Aplicação desktop **Python 3.11 / tkinter** que converte PDFs acadêmicos em repositórios de conhecimento curado, conectados a um **Projeto no Claude.ai** como tutor acadêmico personalizado.

**Fluxo do usuário:**
```
App → adicionar PDFs → build → push GitHub → Claude Project → estudar
```

**Stack:** Python 3.11, tkinter, pymupdf, pymupdf4llm, pdfplumber, Pillow, python-dotenv.
Backends opcionais: docling, marker-pdf (CLI externos).
**OS:** Windows 11. Repositório em `C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator`

---

## Estrutura de arquivos (com contagem de linhas)

```
src/
├── builder/engine.py      # 3577 linhas — Motor principal, ARQUIVO MAIS IMPORTANTE
├── models/core.py         # 198 linhas — DataClasses de domínio
├── services/              # (vazio, reservado)
├── utils/helpers.py       # 384 linhas — Utilitários puros
└── ui/
    ├── app.py             # 1180 linhas — Janela principal
    ├── dialogs.py         # 1824 linhas — Todos os diálogos modais
    ├── curator_studio.py  # 537 linhas — Editor de revisão manual de Markdown
    └── theme.py           # 267 linhas — ThemeManager + AppConfig
tests/test_core.py         # 821 linhas — 101 testes, todos passando
```

---

## Arquitetura do Engine (src/builder/engine.py)

### Backends de extração
```
ExtractionBackend (base abstrata)
├── PyMuPDF4LLMBackend  layer="base"    — padrão, rápido
├── PyMuPDFBackend       layer="base"    — fallback
├── DoclingCLIBackend    layer="advanced" — fórmulas, OCR
└── MarkerCLIBackend     layer="advanced" — equações, layout
```

### RepoBuilder — métodos públicos
| Método | Quando chamar |
|--------|---------------|
| `build()` | Build do zero |
| `incremental_build()` | Adicionar arquivos a repo existente; regenera arquivos pedagógicos |
| `process_single(entry)` | Botão "⚡ Processar" — processa item a item |
| `unprocess(entry_id)` | Botão "🗑 Limpar" — remove arquivos e retira do manifest |
| `_regenerate_pedagogical_files(manifest)` | Regenera TODOS os arquivos pedagógicos sem reprocessar PDFs |
| `_resolve_content_images()` | Pós-build: copia imagens referenciadas nos MDs para content/images/ com paths relativos |

### Geradores pedagógicos (funções livres em engine.py)
| Função | Arquivo gerado |
|--------|---------------|
| `generate_claude_project_instructions()` | `INSTRUCOES_CLAUDE_PROJETO.md` (system prompt do tutor) |
| `course_map_md()` | `course/COURSE_MAP.md` |
| `glossary_md()` | `course/GLOSSARY.md` |
| `file_map_md()` | `course/FILE_MAP.md` (mapeamento arquivos→unidades, preenchido pelo tutor) |
| `bibliography_md()` | `content/BIBLIOGRAPHY.md` |
| `exam_index_md()` | `exams/EXAM_INDEX.md` |
| `exercise_index_md()` | `exercises/EXERCISE_INDEX.md` |
| `tutor_policy_md()` | `system/TUTOR_POLICY.md` |
| `pedagogy_md()` | `system/PEDAGOGY.md` |
| `modes_md()` | `system/MODES.md` |
| `output_templates_md()` | `system/OUTPUT_TEMPLATES.md` |
| `student_state_md()` | `student/STUDENT_STATE.md` |
| `progress_schema_md()` | `student/PROGRESS_SCHEMA.md` |
| `student_profile_md()` | `student/STUDENT_PROFILE.md` |

### First Session Protocol
O `INSTRUCOES_CLAUDE_PROJETO.md` contém um protocolo que instrui o tutor Claude a, na primeira sessão de chat:
1. Ler o `FILE_MAP.md` (que tem `status: pending_review`)
2. Atribuir tags de unidade a cada arquivo
3. Cruzar provas com unidades para preencher incidência
4. Semear definições no glossário
5. Confirmar com o aluno para sincronizar via git

Isso substitui a antiga abordagem de auto-categorização via LLM (OpenAI/Gemini), que foi **completamente removida**.

---

## DataClasses (src/models/core.py)

### FileEntry — arquivo na fila
Campos: `source_path`, `file_type` (pdf/image/url/code/zip/repo), `category`, `title`, `tags`, `professor_signal`, `processing_mode`, `document_profile`, `preferred_backend`, `formula_priority`, `preserve_pdf_images_in_markdown`, `force_ocr`, `extract_images`, `extract_tables`, `page_range`, `ocr_language`, `enabled`.
**Nota:** `export_page_previews` foi REMOVIDO (previews agora são renderizados on-the-fly pelo Curator).

### SubjectProfile — perfil de matéria
Campos: `name`, `slug`, `professor`, `syllabus`, `teaching_plan`, `queue: List[FileEntry]`, `repo_root` (caminho COMPLETO do repo).
**NUNCA usar `asdict()` diretamente** — usar `sp.to_dict()` (queue tem serialização customizada).

### StudentProfile — perfil do aluno (único)
Campos: `full_name`, `nickname`, `personality`.

---

## UI (src/ui/)

### app.py — janela principal
- **Toolbar:** ➕PDFs, 🖼Imagens, 🔗Link, 💻Código, ⚡Processar, 📂Abrir Repo, ⚙Config, ?Ajuda, 🖌Curator, 🚀Criar Repo
- **3 abas:** Fila de Processamento | 📁 Backlog (Já Processados) | 📋 Log
- **Backlog tab toolbar:** 🔄Atualizar | ✏Editar | 🗑Limpar | 🔄Reprocessar Repositório
- Double-click no backlog → `BacklogEntryEditDialog` (com abas Editar + Visualização MD)
- `_reprocess_repo()` — chama `incremental_build()` sem entries novos, regenera todos os arquivos pedagógicos
- `_repo_dir()` retorna `Path(var_repo_root)` direto (repo_root armazena caminho completo)

### dialogs.py — diálogos
- `BacklogEntryEditDialog(tk.Toplevel)` — 2 abas:
  - **Editar:** título, categoria, tags, camada, notas, checkboxes (bundle, prova)
  - **Visualização MD:** viewer com syntax highlighting, seletor de fonte (base/avançado/revisão), botão "Ver PDF Original" (abre no visualizador do sistema)
  - Usa tema dark do ThemeManager (não mais simpledialog.Dialog)
- `FileEntryDialog` — edita FileEntry antes de processar
- `SubjectManagerDialog` — CRUD de matérias
- `StudentProfileDialog` — perfil do aluno
- `SettingsDialog` — 2 abas: Aparência, Processamento (aba IA foi removida)
- `MarkdownPreviewWindow` — visualizador standalone (não mais usado, mas classe ainda existe)

### curator_studio.py — editor de revisão
- Painel esquerdo: lista de arquivos em `manual-review/`
- Painel central: preview do PDF renderizado on-the-fly via PyMuPDF (sem PNGs pré-gerados)
- Painel direito: editor de markdown + seletor de fonte
- `_load_previews(fm)` — renderiza PDF usando `source_pdf` do frontmatter, com fallback para `_lookup_raw_target()` que busca no manifest.json

### theme.py — AppConfig
- `DEFAULTS` dict com todos os valores padrão
- Tema dark aplicado via `ThemeManager.palette()` → dict de cores

---

## .gitignore dos repos gerados
```
# Não essencial para o Tutor
staging/          # Cache de build (2465+ assets)
raw/              # PDFs originais (tutor lê os markdowns)
build/            # Artefatos de build
manual-review/    # Workspace humano
scripts/          # Utilitários locais
# Sistema
__pycache__/ *.pyc .DS_Store Thumbs.db
```

---

## Categorias válidas
```python
DEFAULT_CATEGORIES = [
    "material-de-aula", "provas", "listas", "gabaritos",
    "fotos-de-prova", "referencias", "bibliografia", "cronograma", "outros"
]
```
`_NO_UNIT_CATEGORIES = {"cronograma", "bibliografia", "referencias"}` → auto-tagged "curso-inteiro" no FILE_MAP.

---

## Commits recentes (mais novo primeiro)
```
6a874ec fix: BacklogEntryEditDialog com tema dark consistente
3c89a15 fix: _active_subject() não existia no _reprocess_repo
ec11d8b feat: melhoria UX do backlog — visualização MD inline + reprocessar repo
b0453a0 fix: Curator Studio PDF preview não encontrava source_pdf
29a4f77 refactor: remove page preview pre-generation, render PDF on-the-fly
500c28f feat: resolve imagens referenciadas + .gitignore para repos gerados
0c1088c refactor: repo_root stores full repo path instead of parent dir
e420bf3 refactor: remove LLM auto-categorization (replaced by tutor first-session protocol)
92731d7 fix: prevent STUDENT_STATE.md overwrite on process_single
22cebb6 fix(system-prompt): remove git commands from First Session Protocol
05f5358 Add FILE_MAP, First Session protocol & fixes
```

---

## O que foi feito recentemente (sessões com Claude Code)

1. **FILE_MAP.md + First Session Protocol** — sistema de mapeamento arquivo→unidade preenchido pelo tutor na primeira sessão
2. **Remoção completa do LLM auto-categorization** — removido `src/services/llm.py`, botão auto-categorizar, CategorizationReviewDialog, aba IA do Settings, chaves OpenAI/Gemini
3. **Refactor repo_root** — agora armazena caminho completo (ex: `C:\...\Metodos-Formais-Tutor`) em vez de diretório pai + slug
4. **Resolução de imagens** — `_resolve_content_images()` copia apenas imagens referenciadas nos MDs para `content/images/` com paths relativos (evita 2465 assets no Claude Projects)
5. **Remoção de page previews** — Curator Studio renderiza PDF on-the-fly via PyMuPDF em vez de PNGs pré-gerados
6. **Melhoria UX do backlog** — dialog com abas (Editar + Visualização MD), botão Ver PDF, botão Reprocessar Repositório
7. **Tema dark consistente** — BacklogEntryEditDialog convertido de simpledialog.Dialog para tk.Toplevel com ThemeManager

---

## Armadilhas conhecidas

- **Nunca usar `asdict()` no SubjectProfile** — usar `sp.to_dict()`
- **`process_single` reseta `self.logs = []`** após escrever no manifest — intencional
- **`incremental_build` sem entries novos** ainda regenera arquivos pedagógicos — correto
- **`parse_page_range`** converte base-1 → base-0 automaticamente
- **`_TEACHING_PLAN_SECTION_STOP`** para ao encontrar PROCEDIMENTOS|AVALIAÇÃO|BIBLIOGRAFIA|METODOLOGIA
- **Claude Projects tem limite de ~200 arquivos** — por isso staging/ e raw/ ficam no .gitignore
- **Toda operação pesada na UI** roda em `threading.Thread(daemon=True)` + `self.after(0, callback)`

---

## Testes

```bash
python -m pytest tests/test_core.py -q    # 101 testes, todos devem passar
```
tkinter é mockado no topo de `test_core.py` — testes rodam headless.

---

## Como contribuir código

1. Sempre rodar `python -m pytest tests/test_core.py -q` após mudanças
2. Manter compatibilidade com Python 3.8+ (sem `match/case`, sem `X | Y` em type hints)
3. Seguir padrão existente: funções livres para geradores, métodos em RepoBuilder para pipeline
4. Toda UI pesada em thread separada + `self.after(0, callback)`
5. Tema dark: usar `ThemeManager.palette()` para cores, nunca hardcodar branco
6. Preferir `tk.Frame`/`tk.Label`/`tk.Text` com cores manuais em vez de `ttk` sem tema para evitar partes brancas

---

Agora estou pronto para continuar. Me diga o que quer fazer a seguir e eu te ajudo com o código.
