# CLAUDE.md — Contexto de Trabalho

Contexto curto e operacional para trabalhar neste repositório.

---

## O que é este projeto

O **Academic Tutor Repo Builder V3** é uma aplicação desktop em `Python + tkinter` que converte materiais acadêmicos em repositórios Markdown estruturados para uso com:

- `Claude`
- `GPT`
- `Gemini`

O fluxo geral é:

```text
App -> importar materiais -> processar -> revisar -> gerar instruções -> conectar à IA
```

---

## Estado atual do produto

O app hoje já suporta:

- perfis persistentes de matéria e aluno
- fila persistida por matéria
- importação de PDF, imagem, link, GitHub repo, código e ZIP
- processamento individual e build completo/incremental
- backlog baseado em `manifest.json`
- Curator Studio com aprovação, reprovação e sync do manifest
- geração de:
  - `INSTRUCOES_CLAUDE_PROJETO.md`
  - `INSTRUCOES_GPT_PROJETO.md`
  - `INSTRUCOES_GEMINI_PROJETO.md`

Não assuma que o projeto ainda é “Claude only”.

---

## Estrutura relevante

```text
src/
├── __main__.py
├── builder/
│   └── engine.py
├── models/
│   └── core.py
├── ui/
│   ├── app.py
│   ├── dialogs.py
│   ├── curator_studio.py
│   └── theme.py
└── utils/
    └── helpers.py

tests/
└── test_core.py
```

Arquivos úteis:

- `README.md` -> visão geral do produto
- `CODEX.md` -> guia técnico mais detalhado
- `LLM.md` -> contexto expandido para outros agentes/LLMs

---

## Arquivos centrais

### `src/builder/engine.py`

Arquivo mais importante.

Responsável por:

- pipeline de processamento
- seleção de backend
- build completo e incremental
- processamento individual
- URL fetcher
- geração dos arquivos pedagógicos

### `src/models/core.py`

Contém:

- `FileEntry`
- `SubjectProfile`
- `StudentProfile`
- stores e serialização

Ponto crítico:

- `SubjectProfile.queue` tem serialização customizada
- não use `asdict()` diretamente em `SubjectProfile`

### `src/ui/app.py`

Tela principal.

Responsável por:

- fila a processar
- backlog
- log
- abertura de dialogs
- build e processamento em threads

### `src/ui/dialogs.py`

Centraliza dialogs e a ajuda `F1`.

### `src/ui/curator_studio.py`

Revisão manual.

Hoje ele:

- abre markdowns de `manual-review/`
- permite escolher fonte base/avançada/template
- aprova para `content/curated`, `exercises/lists` ou `exams/past-exams`
- grava `approved_markdown` / `curated_markdown` no manifest

---

## Regras práticas de manutenção

### Tema da UI

Todo novo `tk.Toplevel` deve:

1. chamar `apply_theme_to_toplevel(self, parent)` logo após `grab_set()`
2. aplicar `bg=p["bg"]` em widgets `tk.Frame` e `tk.Label`
3. aplicar `bg/fg/insertbackground` em `tk.Text`
4. aplicar `bg=p["frame_bg"]` e `highlightthickness=0` em `tk.Canvas`

### Processamento

- `incremental_build()` pode regenerar arquivos pedagógicos mesmo sem novos entries
- `process_single()` e UI pesada rodam em thread com callback via `after(...)`
- `manifest.json` é a fonte de verdade do backlog

### Categorias

Categorias atuais:

```python
[
    "material-de-aula",
    "provas",
    "listas",
    "gabaritos",
    "fotos-de-prova",
    "referencias",
    "bibliografia",
    "cronograma",
    "trabalhos",
    "codigo-professor",
    "codigo-aluno",
    "quadro-branco",
    "outros",
]
```

---

## Pontos importantes do estado atual

- `URL Fetcher` gera Markdown estruturado, não mais bloco bruto de texto
- a ajuda `F1` já foi atualizada para o estado atual do app
- `README.md` já foi atualizado para refletir as plataformas múltiplas
- `Backlog` e `Curator Studio` fazem parte do fluxo principal, não são extras
- não há `src/services/llm.py` ativo no código-fonte atual; não documente isso como parte da arquitetura vigente sem verificar primeiro

---

## Testes

```bash
python -m pytest tests/ -v
python -m pytest tests/ -q
python -m pytest tests/ -k "UrlFetcher"
```

`tkinter` é mockado em `tests/test_core.py`, então os testes rodam headless.

---

## Checklist mental antes de editar

- o comportamento existe de fato na UI atual?
- o texto/documentação menciona Claude como único alvo sem necessidade?
- o arquivo precisa sincronizar com `README.md`, `LLM.md` e `CODEX.md`?
- a mudança afeta `manifest.json`, `SubjectProfile` ou `Curator Studio`?
