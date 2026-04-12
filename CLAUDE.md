# CLAUDE.md — Contexto de Trabalho

Contexto operacional para trabalhar neste repositório.

---

## O que é este projeto

O **Academic Tutor Repo Builder V3** é uma aplicação desktop `Python + tkinter`
que converte materiais acadêmicos em repositórios Markdown estruturados para uso
com Claude, GPT e Gemini como tutores acadêmicos.

Fluxo geral:

```
App → importar materiais → processar → revisar (Curator Studio)
    → gerar instruções → conectar à IA (Claude/GPT/Gemini)
```

---

## Estado atual do produto

O app suporta:

- Perfis persistentes de matéria (`SubjectProfile`) e aluno (`StudentProfile`)
- Fila persistida por matéria com serialização customizada
- Importação de PDF, imagem, link, GitHub repo, código e ZIP
- Processamento individual e build completo/incremental
- Backlog baseado em `manifest.json` (fonte de verdade)
- Curator Studio com aprovação, reprovação e sync do manifest
- Image Curator com curadoria de imagens por entry
- Repo Dashboard com status de processamento
- Geração de instruções para três plataformas:
  - `INSTRUCOES_CLAUDE_PROJETO.md`
  - `INSTRUCOES_GPT_PROJETO.md`
  - `INSTRUCOES_GEMINI_PROJETO.md`
- Sleep prevention durante build (Windows)
- Backlog e tasks com UI compacta

**Não assuma que o projeto é Claude-only.**

---

## Estrutura de arquivos

```
src/
├── __main__.py
├── builder/
│   ├── engine.py          ← arquivo mais importante
│   └── datalab_client.py  ← cliente HTTP do Datalab API
├── models/
│   └── core.py
├── ui/
│   ├── app.py
│   ├── dialogs.py
│   ├── curator_studio.py
│   ├── image_curator.py   ← curadoria de imagens por entry
│   ├── repo_dashboard.py  ← dashboard de status do repositório
│   └── theme.py
└── utils/
    ├── helpers.py
    └── power.py           ← sleep prevention (Windows)

tests/
├── test_core.py
├── test_image_curation.py
├── test_repo_dashboard.py
├── test_ui_queue_dashboard.py
└── test_power_management.py
```

Arquivos de documentação:

- `README.md` — visão geral do produto
- `CODEX.md` — guia técnico detalhado
- `LLM.md` — contexto expandido para agentes/LLMs

---

## Arquivos centrais

### `src/builder/engine.py`

Arquivo mais importante. Responsável por:

- pipeline de processamento (backends base e avançados)
- seleção automática de backend por perfil de documento
- build completo e incremental
- processamento individual (`process_single`)
- URL fetcher
- geração de todos os arquivos pedagógicos
- geração do FILE_MAP (roteador operacional)
- geração do COURSE_MAP (mapa pedagógico)
- lógica de timeline e mapeamento de unidades

### `src/builder/datalab_client.py`

Cliente para o Datalab API. Cuida de:

- autenticação e envio de PDFs
- polling de status
- chunking para documentos longos (chunk size: 20 págs para math_heavy)
- consolidação de chunks em markdown único
- `disable_image_extraction = true` e `disable_image_captions = true`
  são passados sempre — imagens ficam no pipeline app-side (Image Curator)

### `src/models/core.py`

Contém: `FileEntry`, `SubjectProfile`, `StudentProfile`, stores e serialização.

**Ponto crítico:**
- `SubjectProfile.queue` tem serialização customizada — não use `asdict()` direto
- `SubjectProfile` tem campos novos: `github_url`, `preferred_llm`
- `FileEntry` tem campos: `manual_unit_slug`, `manual_timeline_block_id`

### `src/ui/app.py`

Tela principal. Responsável por fila, backlog, log, threads e build.
Ações secundárias de repositório agrupadas em menu `Repo`.

### `src/ui/dialogs.py`

Centraliza dialogs e ajuda F1. Inclui `BacklogEntryEditDialog` com abas:
Configurar, Visualização MD, Imagens.

### `src/ui/curator_studio.py`

Revisão manual. Hoje:

- abre markdowns de `manual-review/`
- escolha de fonte: base, avançada ou template
- aprova para `content/curated/`, `exercises/lists/` ou `exams/past-exams/`
- grava `approved_markdown` / `curated_markdown` no manifest
- normaliza referências de imagem para caminhos repo-relative estáveis:
  `content/images/manual-crops/...` (não caminhos relativos instáveis)
- URL fetcher vai para `manual-review/web/` (não `manual-review/pdfs/`)
- zoom e recorte de região implementados

### `src/ui/image_curator.py`

Curadoria de imagens por entry. Resolve PDF via `raw_target/source_path`
(determinístico). Imagens ficam em pipeline separado do markdown.

---

## Backends de extração

### Perfis de documento

| Perfil | Descrição | Backend preferido |
|---|---|---|
| `auto` | padrão | pymupdf4llm |
| `math_heavy` | fórmulas, LaTeX, lógica formal | datalab → marker → docling |
| `diagram_heavy` | tabelas complexas, layouts | docling → marker |
| `scanned` | PDFs escaneados, OCR | docling / marker com force_ocr |

Compatibilidade legada: `general→auto`, `math_light→math_heavy`,
`layout_heavy→diagram_heavy`, `exam_pdf→diagram_heavy`

### Backends disponíveis

**Base:**
- `pymupdf4llm` — padrão, rápido, PDFs digitais simples
- `pymupdf` — fallback básico

**Avançados:**
- `datalab` — melhor para math_heavy; requer DATALAB_API_KEY; cobra por página
- `docling` — CLI externo; excelente para tabelas; Standard GPU habilitado
- `docling_python` — via Python; experimental
- `marker` — CLI externo; excelente para LaTeX/equações

### Marker — configurações relevantes

```python
marker_use_llm: bool          # usar LLM opcional
marker_llm_model: str         # ex: "qwen3-vl:8b" via Ollama
marker_chunking_mode: str     # "off" | "fallback" | "always" (default: "fallback")
marker_torch_device: str      # "cpu" | "cuda" | "mps"
ollama_base_url: str          # ex: "http://localhost:11434"
```

**Chunking:** tenta documento inteiro primeiro; entra em chunks só em timeout real.
Chunk size: 10 págs (workloads pesados), 20 págs (demais).

**⚠ Patch local crítico fora do repo:**
`.venv/Lib/site-packages/marker/services/ollama.py` tem patch que:
1. `flatten_schema` — resolve `$defs/$ref` antes de enviar ao Ollama
2. Fallback `response → thinking`
3. Recuperação de JSON embutido em texto

Se a `.venv` for recriada, esse patch pode ser perdido.

**Modelos Ollama:** `qwen3-vl:8b q4_K_M` (melhor para RTX 4050 6GB),
`qwen3-vl:4b` (fallback). `qwen3-vl:235b-cloud` é problemático.

---

## Arquitetura map-first do repositório gerado

O tutor usa esta ordem de navegação:

```
COURSE_MAP → STUDENT_STATE → GLOSSARY → FILE_MAP → conteúdo
```

**COURSE_MAP.md** — mapa pedagógico curto, gerado pelo app a partir do plano de
ensino. Cruza timeline com unidades. Versão enxuta corta placeholders vazios.

**FILE_MAP.md** — índice operacional de roteamento. Colunas atuais: Quando abrir,
Prioridade, Markdown, Unidade, Período. Colunas novas (próximo incremento):
Seções principais, Confiança.

**SYLLABUS.md** — fonte de datas e cronograma.

**`.timeline_index.json`** — índice interno. Liga blocos do cronograma com
unidades e períodos. Não é para o tutor usar diretamente.

**Correção de mapeamento incorreto:** usar `manual_unit_slug` e
`manual_timeline_block_id` no backlog entry + "Reprocessar Repositório".
Não editar FILE_MAP ou COURSE_MAP manualmente como fluxo padrão.

---

## SubjectProfile — campos relevantes

```python
name: str
slug: str
professor: str
institution: str
semester: str
schedule: str
syllabus: str           # cronograma multilinea
teaching_plan: str      # plano de ensino
default_mode: str       # auto | math_heavy | diagram_heavy | scanned
repo_root: str          # caminho local do repositório gerado
github_url: str         # URL do repositório no GitHub
preferred_llm: str      # "claude" | "gpt" | "gemini"
queue: List[FileEntry]  # serialização customizada
```

---

## Categorias ativas

```python
[
    "material-de-aula", "provas", "listas", "gabaritos",
    "fotos-de-prova", "referencias", "bibliografia", "cronograma",
    "trabalhos", "codigo-professor", "codigo-aluno", "quadro-branco",
    "outros",
]
```

Categorias sem unidade (não entram no mapeamento de timeline):
`cronograma`, `bibliografia`, `referencias`.

---

## Funções previstas no próximo incremento (RAG enrichment)

Serão adicionadas em `engine.py`:

```python
_extract_section_headers(md_content: str) -> list[dict]
# Extrai headers ## e ### do markdown (ignora blocos de código e sumário existente)

_inject_executive_summary(md_path: Path) -> bool
# Injeta bloco <!-- EXEC_SUMMARY_START/END --> no topo de cada arquivo curado
# Idempotente — pode ser chamada múltiplas vezes sem duplicar

_clean_extraction_noise(content: str) -> str
# Remove ruído de extração: números de página, separadores, headers duplicados
# Preserva: blocos de código, LaTeX, tabelas, imagens

_get_entry_sections(md_path: Path, max_sections: int = 4) -> str
# Retorna string "Seção 1 · Seção 2 · ..." para coluna FILE_MAP

_infer_unit_confidence(entry: dict) -> str
# Retorna "Alta" | "Média" | "Baixa ⚠" baseado nos sinais de inferência
```

`student_state_md()` será atualizado para incluir tabela de histórico de sessões.

---

## Regras práticas de manutenção

### Tema da UI

Todo novo `tk.Toplevel` DEVE:

1. Chamar `p = apply_theme_to_toplevel(self, parent)` logo após `grab_set()`
2. Aplicar `bg=p["bg"]` em todos `tk.Frame` e `tk.Label`
3. Aplicar `bg=p["input_bg"]`, `fg=p["fg"]`, `insertbackground=p["fg"]`
   em `tk.Text`
4. Aplicar `bg=p["frame_bg"]`, `highlightthickness=0` em `tk.Canvas`
5. Widgets `ttk.*` herdam o tema automaticamente — não precisam de bg/fg

Nunca usar `tk.Frame` como container raiz sem `bg=p["bg"]`.

### Processamento e threads

- `incremental_build()` pode regenerar arquivos pedagógicos mesmo sem novos entries
- `process_single()` e UI pesada rodam em thread com callback via `after(...)`
- `manifest.json` é a fonte de verdade do backlog
- "processado" ≠ "curado/aprovado" — Curator Studio controla a promoção

### Imagens

- Imagens ficam em pipeline separado do markdown (Image Curator app-side)
- Datalab não gera imagens/captions (desabilitado intencionalmente)
- Referências do Curator Studio normalizadas para `content/images/manual-crops/...`
- `content/images/` contém apenas imagens referenciadas nos markdowns

### Datalab

- Preservar `disable_image_extraction = true` e `disable_image_captions = true`
- Preservar política de chunking para documentos longos
- Não reativar features de imagem da API sem decisão explícita

### Manifest como fonte de verdade

- Fila ativa reconciliada contra `manifest.json`
- Item processado sai da fila quando manifest confirma entry
- Dashboard usa contagem reconciliada, não snapshot bruto

---

## Problemas conhecidos / dívida técnica

1. **Patch local fora do repo** — `.venv/.../marker/services/ollama.py`
2. **Stall timeout pode matar processo saudável** — watchdog mata por silêncio;
   afeta Marker com LLM e Docling VLM
3. **Marker + Ollama instável** — `qwen3-vl:235b-cloud` causa 500 errors
4. **LaTeX corrompido é silencioso** — pymupdf4llm pode corromper fórmulas;
   usar Marker/Datalab para math_heavy

---

## Testes

```bash
python -m pytest tests/ -v
python -m pytest tests/ -q
python -m pytest tests/ -k "image_curation"
python -m pytest tests/ -k "dashboard"
```

`tkinter` é mockado — testes rodam headless.

---

## Checklist mental antes de editar

- O comportamento existe de fato na UI atual?
- A mudança afeta `manifest.json`, `SubjectProfile` ou `Curator Studio`?
- O arquivo precisa sincronizar com `README.md`, `LLM.md` e `CODEX.md`?
- Widgets `tk.*` novos aplicam o tema via `apply_theme_to_toplevel()`?
- O texto menciona Claude como único alvo sem necessidade?
- A mudança toca em Datalab? Preservar decisão de imagens app-side.
- A mudança toca em referências de imagem? Preservar normalização repo-relative.