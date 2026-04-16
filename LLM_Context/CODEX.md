## O que é este projeto

Aplicação desktop **Python/tkinter** que converte PDFs acadêmicos em repositórios de conhecimento curado conectados a um **Projeto no Claude.ai** como tutor acadêmico personalizado.

**Fluxo do usuário:**
```
App → adicionar PDFs → build → push GitHub → Claude Project → estudar
```

**Stack:** Python 3.8+, tkinter, pymupdf, pymupdf4llm, pdfplumber, Pillow, python-dotenv.
Backends opcionais: docling, marker-pdf (CLI externos).

---

## Estrutura de arquivos

```
src/
├── builder/engine.py     # Motor principal — ARQUIVO MAIS IMPORTANTE
├── models/core.py        # DataClasses de domínio
├── services/             # (reservado para serviços futuros)
├── utils/helpers.py      # Utilitários puros (sem estado)
└── ui/
    ├── app.py            # Janela principal
    ├── dialogs.py        # Todos os diálogos modais
    ├── curator_studio.py # Editor de revisão manual de Markdown
    └── theme.py          # ThemeManager + AppConfig
tests/test_core.py        # 61 testes, todos devem passar
```

---

## Data classes (`src/models/core.py`)

### `FileEntry` — arquivo na fila
Campos críticos: `source_path`, `file_type` (pdf/image/url), `category`, `title`,  
`professor_signal` (padrões do professor), `processing_mode`, `document_profile`,  
`preferred_backend`, `formula_priority`, `page_range`, `ocr_language`.  
Serialização via `to_dict()` / `from_dict()`.

### `SubjectProfile` — perfil de matéria
Campos críticos: `name`, `slug`, `professor`, `syllabus` (cronograma em Markdown),  
`teaching_plan` (plano de ensino extraído do PDF — campo mais rico, usado para auto-extração),  
`queue: List[FileEntry]` (fila persistida por matéria), `repo_root` (caminho completo do repo, ex: `C:\Users\...\Metodos-Formais-Tutor`).  
**Atenção:** `queue` tem serialização manual em `to_dict()`/`from_dict()` — não usar `asdict()` diretamente no SubjectProfile.

### `StudentProfile` — perfil do aluno (único no sistema)
Campos: `full_name`, `nickname`, `personality` (campo mais impactante para o tutor).

### `DocumentProfileReport` — resultado da análise do PDF
Campos: `page_count`, `text_chars`, `images_count`, `suspected_scan`, `suggested_profile`.

### `PipelineDecision` — decisão de backends
Campos: `base_backend`, `advanced_backend`, `reasons` (trilha de auditoria).

---

## Motor principal (`src/builder/engine.py`)

### Hierarquia de backends
```
ExtractionBackend (base abstrata)
├── PyMuPDF4LLMBackend  layer="base"    — padrão, rápido
├── PyMuPDFBackend       layer="base"    — fallback
├── DoclingCLIBackend    layer="advanced" — fórmulas, OCR
└── MarkerCLIBackend     layer="advanced" — equações, layout
```
Seleção automática via `BackendSelector.decide(entry, report)`.

### `RepoBuilder` — métodos públicos
| Método | Quando chamar |
|--------|---------------|
| `build()` | Build do zero |
| `incremental_build()` | Adicionar arquivos a repo existente; regenera arquivos pedagógicos |
| `process_single(entry)` | Botão "⚡ Processar" — processa item a item |
| `unprocess(entry_id)` | Botão "🗑 Limpar" — remove arquivos e retira do manifest |

### Geradores pedagógicos — funções livres
Todas recebem `course_meta: dict` e opcionalmente `subject_profile` / `student_profile`.

| Função | Arquivo gerado | Nota |
|--------|---------------|------|
| `generate_claude_project_instructions()` | `INSTRUCOES_CLAUDE_PROJETO.md` | System prompt do Projeto |
| `course_map_md()` | `course/COURSE_MAP.md` | Extrai unidades do `teaching_plan` |
| `glossary_md()` | `course/GLOSSARY.md` | Semeia termos dos tópicos extraídos |
| `bibliography_md()` | `content/BIBLIOGRAPHY.md` | Extrai refs do `teaching_plan` |
| `exam_index_md()` | `exams/EXAM_INDEX.md` | Só gerado quando há provas |
| `exercise_index_md()` | `exercises/EXERCISE_INDEX.md` | Só gerado quando há listas |
| `tutor_policy_md()` | `system/TUTOR_POLICY.md` | |
| `pedagogy_md()` | `system/PEDAGOGY.md` | |
| `modes_md()` | `system/MODES.md` | |
| `output_templates_md()` | `system/OUTPUT_TEMPLATES.md` | |
| `student_state_md()` | `student/STUDENT_STATE.md` | |
| `progress_schema_md()` | `student/PROGRESS_SCHEMA.md` | |

### Funções auxiliares de extração (regex, sem LLM)

**`_parse_units_from_teaching_plan(text) -> List[(title, topics)]`**  
Suporta dois formatos:
- **PUCRS:** `N°. DA UNIDADE: N` + `CONTEÚDO: Título` + tópicos `1.1.`
- **Genérico:** `### Unidade N — Título` + marcadores (`-`, `•`)  
Para ao encontrar `PROCEDIMENTOS`, `AVALIAÇÃO`, `BIBLIOGRAFIA`, `METODOLOGIA`.

**`_parse_bibliography_from_teaching_plan(text) -> {"basica": [...], "complementar": [...]}`**  
Busca seção `BIBLIOGRAFIA` com sub-seções `BÁSICA:` e `COMPLEMENTAR:`.  
Referências numeradas: `1. AUTOR, A. Título...`

**Regra de ouro:** sempre envolva chamadas de extração em `try/except` e degrade para template vazio.

---

## Helpers (`src/utils/helpers.py`)

Funções puras sem estado — seguras para importar em qualquer contexto.

| Função | O que faz |
|--------|-----------|
| `slugify(value)` | `"Cálculo I"` → `"cálculo-i"` |
| `parse_page_range("1-3,5")` | → `[0,1,2,4]` (converte para base-0 automaticamente se não houver zero) |
| `pages_to_marker_range([0,1,2])` | → `"0-2"` (formato para CLI do marker) |
| `parse_html_schedule(html)` | HTML de tabela → Markdown (requer beautifulsoup4) |
| `auto_detect_category(filename)` | Detecta categoria por palavras-chave no nome do arquivo |
| `write_text(path, content)` | Cria diretórios pais automaticamente |
| `safe_rel(path, root)` | Caminho relativo seguro, retorna `None` se `path` for `None` |
| `get_app_data_dir()` | `~/.config/gpt_tutor_generator/` no Linux, `%APPDATA%/GPTTutorGenerator` no Windows |

**Flags de disponibilidade:** `HAS_PYMUPDF`, `HAS_PYMUPDF4LLM`, `HAS_PDFPLUMBER`, `DOCLING_CLI`, `MARKER_CLI` — cheque antes de usar os respectivos recursos.

---

## UI (`src/ui/`)

### `app.py` — janela principal
- `_save_current_queue()` — persiste `self.entries` no `SubjectProfile.queue` ativo. Chamar sempre que a fila mudar.
- `_on_subject_selected()` — restaura fila salva ao selecionar matéria.
- `_refresh_backlog()` — lê `manifest.json` e popula a aba Backlog.
- `process_selected_single()` / `_on_single_processed_success()` — processamento item a item em thread separada.
- Toda operação pesada roda em `threading.Thread(daemon=True)` + `self.after(0, callback)` para atualizar a UI.

### `dialogs.py` — todos os diálogos
- `SubjectManagerDialog` — cria/edita perfis de matéria. Contém `_syllabus_text` e `_teaching_plan_text` como widgets `tk.Text`.
- `StudentProfileDialog` — edita perfil único do aluno.
- `FileEntryDialog(simpledialog.Dialog)` — edita um `FileEntry`. Campos condicionais para PDF vs imagem.
- `HelpWindow` — janela F1 com `HELP_SECTIONS: List[(título, texto)]`. Para adicionar seção nova, só appender nessa lista.
- `SettingsDialog` — 3 abas: Aparência, Processamento, IA.

### `theme.py` — AppConfig
`DEFAULTS` contém todos os valores padrão de configuração. **Sempre adicionar nova chave aqui** antes de usar `config.get()`.  
API keys são salvas separadamente no `.env` local (não no JSON de config).

---

## Categorias válidas

```python
DEFAULT_CATEGORIES = [
    "material-de-aula", "provas", "listas", "gabaritos",
    "fotos-de-prova", "referencias", "bibliografia", "cronograma", "outros"
]
```

`EXAM_INDEX.md` é gerado quando há entries em `("provas", "fotos-de-prova")`.  
`EXERCISE_INDEX.md` é gerado quando há entries em `("listas", "gabaritos")`.

---

## Como adicionar um novo gerador pedagógico

1. Criar função livre `novo_arquivo_md(course_meta, ...) -> str` em `engine.py`
2. Chamar em `_write_root_files()` do `RepoBuilder`
3. Chamar também em `incremental_build()` (evitar desatualização após rebuild parcial)
4. Adicionar entrada na tabela de arquivos em `generate_claude_project_instructions()`
5. Adicionar testes em `tests/test_core.py`

## Como adicionar um novo campo ao SubjectProfile

1. Adicionar campo com valor padrão em `SubjectProfile` (dataclass em `core.py`)
2. Verificar que `to_dict()` / `from_dict()` funcionam (campos simples são automáticos via `asdict`)
3. Expor no formulário em `SubjectManagerDialog._build_ui()` e `_on_select()` / `_save()`
4. Propagar para os geradores pedagógicos que precisam do campo

---

## Testes

```bash
python -m pytest tests/ -v        # deve passar 61 testes
python -m pytest tests/ -q        # saída compacta
python -m pytest tests/ -k "Units" # filtrar por nome
```

`tkinter` é mockado no topo de `test_core.py` — os testes rodam headless.  
Ao adicionar testes para geradores pedagógicos, instanciar `SubjectProfile` e `StudentProfile` diretamente.

---

## Comandos úteis

```bash
python app.py                          # rodar o app
python -m pytest tests/ -v             # testes
git log --oneline -10                  # histórico recente
grep -n "def " src/builder/engine.py   # funções do engine
```

---

## Convenção de tema em novos Dialogs (obrigatório)

Todo `tk.Toplevel` novo DEVE:

1. Chamar `p = apply_theme_to_toplevel(self, parent)` no `__init__`,
   logo após `self.grab_set()`
2. Usar `bg=p["bg"]` em todos os widgets `tk.Frame`, `tk.Label`
3. `tk.Text` sempre precisa de:
   `bg=p["input_bg"], fg=p["fg"], insertbackground=p["fg"]`
4. `tk.Canvas` sempre precisa de:
   `bg=p["frame_bg"], highlightthickness=0`
5. Widgets `ttk.*` herdam o tema automaticamente — não precisam de bg/fg
6. Nunca usar `tk.Frame` como container raiz sem `bg=p["bg"]`

---

## Armadilhas conhecidas

- **Nunca usar `asdict()` diretamente no `SubjectProfile`** — a `queue` tem serialização customizada. Usar `sp.to_dict()`.
- **`process_single` reseta `self.logs = []`** após escrever no manifest — comportamento intencional para evitar logs duplicados em chamadas consecutivas.
- **`incremental_build` retorna cedo** se não há novos entries, mas **ainda regenera arquivos pedagógicos** se `subject_profile` estiver presente — isso é correto.
- **`parse_page_range`** converte automaticamente de base-1 para base-0 se não houver zero na entrada. Intervalo `"1-3"` → `[0,1,2]`.
- **`_TEACHING_PLAN_SECTION_STOP`** para o parser de unidades ao encontrar `PROCEDIMENTOS|AVALIAÇÃO|BIBLIOGRAFIA|METODOLOGIA`. Se o plano de ensino tiver uma dessas palavras como título de unidade, as unidades seguintes serão ignoradas.
- **`exam_index_md` e `exercise_index_md`** recebem `List[FileEntry]` mas também são chamados em `incremental_build` com entries reconstruídos via `FileEntry.from_dict(e)` do manifest — garantir que `from_dict` seja tolerante a campos ausentes.