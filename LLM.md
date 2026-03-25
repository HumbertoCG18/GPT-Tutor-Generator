# LLM.md — Contexto Expandido do Projeto

> Use este arquivo para dar contexto a qualquer agente de coding que precise entender o estado atual deste repositório.

Última atualização: 2026-03-25

---

## 1. Resumo do Projeto

O **Academic Tutor Repo Builder V3** é uma aplicação desktop em `Python/tkinter` que converte materiais acadêmicos em repositórios Markdown curados para estudo assistido por IA.

O produto hoje gera instruções e estrutura para:

- `Claude`
- `GPT`
- `Gemini`

Ele não deve mais ser descrito como uma ferramenta exclusiva para Claude, embora Claude continue sendo uma plataforma importante do fluxo.

---

## 2. Objetivo do Produto

O objetivo é produzir um repositório versionável por disciplina que concentre:

- materiais brutos
- extrações automáticas
- conteúdos revisados
- arquivos pedagógicos
- estado do aluno
- instruções para a IA principal

Fluxo conceitual:

```text
importar -> processar -> revisar -> organizar -> gerar instruções -> estudar
```

---

## 3. Arquitetura Atual

```text
GPT-Tutor-Generator/
├── app.py
├── run.bat
├── run.ps1
├── README.md
├── CODEX.md
├── CLAUDE.md
├── LLM.md
├── pyproject.toml
├── requirements.txt
├── src/
│   ├── __main__.py
│   ├── builder/
│   │   └── engine.py
│   ├── models/
│   │   └── core.py
│   ├── ui/
│   │   ├── app.py
│   │   ├── dialogs.py
│   │   ├── curator_studio.py
│   │   └── theme.py
│   └── utils/
│       └── helpers.py
└── tests/
    └── test_core.py
```

Observação importante:

- hoje não existe um `src/services/llm.py` ativo na arquitetura atual do código-fonte
- não documente auto-categorização por LLM como funcionalidade vigente sem verificar antes

---

## 4. Módulos Principais

### `src/builder/engine.py`

É o núcleo do sistema.

Responsabilidades:

- processar PDF, imagem, URL, código, ZIP e links GitHub
- escolher backend base e avançado
- gerar markdowns automáticos
- manter manifest
- criar arquivos pedagógicos
- executar `build()`, `incremental_build()`, `process_single()` e `unprocess()`

Pontos recentes:

- o `URL Fetcher` foi melhorado para gerar Markdown estruturado
- a seleção de conteúdo principal da página tenta evitar sidebar, menu e footer

### `src/models/core.py`

Modelos principais:

- `FileEntry`
- `DocumentProfileReport`
- `BackendRunResult`
- `PipelineDecision`
- `SubjectProfile`
- `StudentProfile`
- `SubjectStore`
- `StudentStore`

Ponto crítico:

- `SubjectProfile.queue` usa serialização customizada
- não usar `asdict()` diretamente nesse modelo

### `src/ui/app.py`

Janela principal.

Hoje inclui:

- matéria ativa
- perfil do aluno
- status do ambiente
- fila a processar
- backlog
- log
- abertura de repositório existente
- Curator Studio
- geração de instruções LLM

### `src/ui/dialogs.py`

Concentra:

- dialogs de matéria
- perfil do aluno
- edição de entry
- visualizador de markdown
- ajuda `F1`
- entrada de URL
- janela de status

### `src/ui/curator_studio.py`

Faz revisão manual dos artefatos em `manual-review/`.

Funções importantes:

- abrir fontes base/avançada/template
- salvar edição
- aprovar conteúdo para diretório final
- reprovar e devolver item para fila
- atualizar `manifest.json`

### `src/ui/theme.py`

Centraliza:

- paletas
- aplicação de tema
- `AppConfig`
- convenções de estilo para `tk` e `ttk`

---

## 5. Funcionalidades Atuais

### Perfis persistentes

- matéria com fila persistida
- aluno com preferências pedagógicas

### Importação

Tipos aceitos:

- `pdf`
- `image`
- `url`
- `github-repo`
- `code`
- `zip`

### Modos de processamento

- `auto`
- `quick`
- `high_fidelity`
- `manual_assisted`

### Perfis de documento

- `auto`
- `general`
- `math_light`
- `math_heavy`
- `layout_heavy`
- `scanned`
- `exam_pdf`

### Backends

Base:

- `pymupdf4llm`
- `pymupdf`

Avançados:

- `docling`
- `marker`

### Curadoria

- `manual-review/`
- Curator Studio
- aprovação sincronizada no manifest

### Backlog

- leitura do `manifest.json`
- edição de entry já processada
- limpeza de processamento
- reprocessamento do repositório
- geração de instruções LLM

### Instruções para IA

Arquivos gerados:

- `INSTRUCOES_CLAUDE_PROJETO.md`
- `INSTRUCOES_GPT_PROJETO.md`
- `INSTRUCOES_GEMINI_PROJETO.md`

---

## 6. Estrutura Gerada no Repositório da Disciplina

Estrutura típica:

```text
{repo-root}/
├── INSTRUCOES_CLAUDE_PROJETO.md
├── INSTRUCOES_GPT_PROJETO.md
├── INSTRUCOES_GEMINI_PROJETO.md
├── manifest.json
├── system/
├── course/
├── student/
├── content/
├── exercises/
├── exams/
├── raw/
├── staging/
├── manual-review/
└── build/
```

Diretórios-chave:

- `raw/` -> origem copiada para o repo
- `staging/` -> artefatos automáticos
- `manual-review/` -> revisão humana guiada
- `content/`, `exercises/`, `exams/` -> conteúdo aprovado
- `build/claude-knowledge/bundle.seed.json` -> bundle inicial de materiais prioritários

---

## 7. Categorias Atuais

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

Categorias com efeito estrutural:

- `provas`, `fotos-de-prova` -> exames
- `listas`, `gabaritos` -> exercícios
- `trabalhos` -> contexto de assignment
- `codigo-professor`, `codigo-aluno` -> contexto de código
- `quadro-branco` -> apoio visual/aula

---

## 8. Regras de Trabalho no Código

### UI

Novo `tk.Toplevel` deve usar:

```python
p = apply_theme_to_toplevel(self, parent)
```

Além disso:

- `tk.Frame` e `tk.Label` precisam de `bg`
- `tk.Text` precisa de `bg`, `fg`, `insertbackground`
- `tk.Canvas` precisa de `bg` e `highlightthickness=0`

### Modelos

- preserve `to_dict()` / `from_dict()`
- trate `FileEntry.from_dict()` com tolerância a campos faltantes

### Build

- mudanças em geradores pedagógicos normalmente exigem ajuste em `build()` e `incremental_build()`
- se criar novo arquivo gerado, atualize a geração e os testes

### Manifest

- trate `manifest.json` como fonte de verdade do backlog
- não quebre compatibilidade de campos sem necessidade

---

## 9. Testes

Rodar tudo:

```bash
python -m pytest tests/ -v
```

Compacto:

```bash
python -m pytest tests/ -q
```

Exemplo focado:

```bash
python -m pytest tests/test_core.py -k "UrlFetcher" -q
```

Os testes rodam headless porque `tkinter` é mockado em `tests/test_core.py`.

---

## 10. Dependências

Obrigatórias no estado atual:

- `pymupdf`
- `pymupdf4llm`
- `pdfplumber`
- `Pillow`

Opcionais:

- `docling`
- `marker-pdf`

OCR:

- `tesseract`
- `tessdata`

---

## 11. Documentos de Referência Internos

Use estes arquivos em conjunto:

- `README.md` -> visão geral para humanos
- `CODEX.md` -> guia técnico mais direto para manutenção
- `CLAUDE.md` -> contexto curto para trabalho operacional
- `LLM.md` -> contexto expandido

---

## 12. Resumo Executivo

Se um agente tiver pouco tempo, as verdades mais importantes são:

1. o núcleo está em `src/builder/engine.py`
2. o projeto hoje é multi-plataforma (`Claude`, `GPT`, `Gemini`)
3. `manifest.json` é central para backlog e curadoria
4. `Curator Studio` já faz promoção para pastas finais e sincroniza o manifest
5. `SubjectProfile.queue` não pode ser tratado com `asdict()` puro
6. a ajuda `F1`, `README.md` e `CLAUDE.md` já foram alinhados com o estado atual
