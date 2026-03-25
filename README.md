<div align="center">
  <h1>Academic Tutor Repo Builder V3</h1>
  <p>Aplicação desktop em Python/tkinter para transformar materiais acadêmicos em repositórios estruturados para Claude, GPT e Gemini.</p>
</div>

---

## Visão Geral

O **Academic Tutor Repo Builder V3** converte PDFs, imagens, links, repositórios GitHub, arquivos de código e ZIPs em um repositório Markdown curado para estudo assistido por IA.

O fluxo principal é:

```text
App -> importar materiais -> processar -> revisar -> gerar instruções -> conectar à IA
```

O projeto foi pensado para disciplinas reais ao longo do semestre:

- salvar perfis de matéria e aluno
- processar materiais com múltiplos backends
- revisar manualmente conteúdos críticos no Curator Studio
- manter backlog e manifest do repositório
- gerar instruções para `Claude`, `GPT` e `Gemini`

---

## Principais Funcionalidades

### 1. Perfis persistentes

- **Matérias:** nome, slug, professor, semestre, instituição, horário, cronograma, plano de ensino, pasta do repositório, URL GitHub e LLM principal.
- **Aluno:** nome, apelido e preferências de aprendizagem.
- A fila de arquivos é persistida por matéria.

### 2. Importação multicanal

O app aceita:

- PDFs
- imagens e fotos
- links web
- repositórios GitHub
- arquivos de código
- arquivos ZIP

Também é possível:

- importar cronograma a partir de HTML
- extrair plano de ensino a partir de PDF

### 3. Processamento em camadas

Modos disponíveis:

- `auto`
- `quick`
- `high_fidelity`
- `manual_assisted`

Perfis de documento:

- `auto`
- `general`
- `math_light`
- `math_heavy`
- `layout_heavy`
- `scanned`
- `exam_pdf`

### 4. Múltiplos backends

Base:

- `pymupdf4llm`
- `pymupdf`

Avançados:

- `docling`
- `marker`

O app também consegue:

- extrair tabelas
- extrair imagens
- forçar OCR
- limitar processamento por intervalo de páginas

### 5. URL Fetcher com Markdown estruturado

Ao importar links, o app:

- busca o conteúdo da página
- tenta isolar o conteúdo principal
- converte headings, listas, links, código e tabelas HTML para Markdown
- gera um `.md` mais limpo, em vez de despejar texto cru

### 6. Backlog e manifest

A aba **Backlog** lê o `manifest.json` do repositório e permite:

- atualizar a lista de itens processados
- editar metadados
- limpar processamento de uma entry
- reprocessar o repositório
- regenerar instruções LLM

### 7. Curator Studio

O **Curator Studio** revisa os arquivos em `manual-review/`.

Ele permite:

- comparar preview e markdown
- escolher entre saída base, avançada ou template
- editar e salvar
- aprovar e promover conteúdo para a pasta final correta
- reprovar e devolver o item para a fila
- restaurar templates ausentes
- aprovar todos os pendentes

### 8. Geração de instruções para IA

O projeto gera:

- `INSTRUCOES_CLAUDE_PROJETO.md`
- `INSTRUCOES_GPT_PROJETO.md`
- `INSTRUCOES_GEMINI_PROJETO.md`

Além disso, gera arquivos pedagógicos e de estado como:

- `system/TUTOR_POLICY.md`
- `system/PEDAGOGY.md`
- `system/MODES.md`
- `system/OUTPUT_TEMPLATES.md`
- `course/COURSE_MAP.md`
- `course/GLOSSARY.md`
- `content/BIBLIOGRAPHY.md`
- `student/STUDENT_STATE.md`
- `student/PROGRESS_SCHEMA.md`

---

## Estrutura do Projeto

```text
src/
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

Arquivos de apoio importantes:

- `app.py` -> bootstrap simples para rodar a aplicação
- `CODEX.md` -> guia de manutenção do projeto
- `requirements.txt` -> dependências
- `pyproject.toml` -> metadados e config de testes

---

## Requisitos

- Python `3.8+`
- Windows, Linux ou outro ambiente compatível com `tkinter`

Dependências principais:

```bash
pip install -r requirements.txt
```

`requirements.txt` inclui:

- `pymupdf`
- `pymupdf4llm`
- `pdfplumber`
- `Pillow`

Backends opcionais:

```bash
pip install docling
pip install marker-pdf
```

Para OCR com Tesseract, o executável e `tessdata` precisam estar disponíveis no ambiente.

---

## Como Rodar

### Windows

```powershell
run.ps1
```

ou

```bat
run.bat
```

### Qualquer plataforma

```bash
python app.py
```

ou

```bash
python -m src
```

---

## Fluxo Recomendado de Uso

### No app

1. Abra `📝 Gerenciar` e crie a matéria.
2. Preencha professor, semestre, cronograma, plano de ensino, URL GitHub e LLM principal.
3. Abra `👤 Aluno` e ajuste o perfil do estudante.
4. Selecione a matéria ativa.
5. Defina a pasta do repositório ou use `📂 Abrir Repo`.
6. Importe PDFs, imagens, links ou código.
7. Processe um item com `⚡ Processar` ou rode `🚀 Criar Repositório`.
8. Revise `manual-review/` no `🖌 Curator Studio`.
9. Use a aba `Backlog` para editar entries, reprocessar o repo e gerar instruções LLM.

### Fora do app

1. Faça push do repositório para o GitHub, se for usar sync.
2. Conecte o repositório à plataforma principal escolhida.
3. Use o arquivo de instruções correspondente.
4. Atualize `student/STUDENT_STATE.md` ao longo do semestre.

---

## Estrutura do Repositório Gerado

Exemplo:

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

Pontos importantes:

- `raw/` guarda os arquivos originais copiados para o repositório
- `staging/` guarda saídas automáticas intermediárias
- `manual-review/` concentra revisão humana guiada
- `content/`, `exercises/` e `exams/` recebem o conteúdo aprovado
- `build/claude-knowledge/bundle.seed.json` guarda a seleção inicial de materiais prioritários

---

## Categorias Atuais

As categorias válidas do projeto são:

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

Algumas têm efeitos especiais:

- `provas` e `fotos-de-prova` alimentam índices de exames
- `listas` e `gabaritos` alimentam índices de exercícios
- `trabalhos`, `codigo-*` e `quadro-branco` entram nas instruções e no contexto pedagógico

---

## Testes

Rodar a suíte:

```bash
python -m pytest tests/ -v
```

Saída compacta:

```bash
python -m pytest tests/ -q
```

Filtrar por nome:

```bash
python -m pytest tests/ -k "UrlFetcher"
```

Os testes são headless; `tkinter` é mockado em `tests/test_core.py`.

---

## Notas de Manutenção

- Não use `asdict()` diretamente em `SubjectProfile`; use `to_dict()` / `from_dict()`.
- `incremental_build()` pode retornar cedo sem novos arquivos, mas ainda regenerar arquivos pedagógicos.
- `parse_page_range("1-3")` converte automaticamente para base zero.
- Novos dialogs `tk.Toplevel` devem aplicar tema com `apply_theme_to_toplevel(...)`.
- O ponto central do projeto está em `src/builder/engine.py`.

Para contexto mais técnico de manutenção, consulte `CODEX.md`.

---

## Licença

MIT.
