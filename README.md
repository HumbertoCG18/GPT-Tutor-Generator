# GPT Tutor Generator

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](#requisitos)
[![UI](https://img.shields.io/badge/UI-Tkinter-1f6feb)](#arquitetura)
[![Vision](https://img.shields.io/badge/Vision-Ollama-000000)](#image-curator-e-vision)
[![Modelo](https://img.shields.io/badge/Modelo%20padr%C3%A3o-qwen3--vl%3A235b--cloud-6f42c1)](#image-curator-e-vision)
[![License](https://img.shields.io/badge/Licen%C3%A7a-MIT-green)](#licen%C3%A7a)

Aplicação desktop em Python para transformar materiais acadêmicos em um repositório Markdown estruturado, curado e pronto para uso com tutores baseados em LLM.

## Sumário

- [Visão Geral](#visão-geral)
- [Como o App Funciona](#como-o-app-funciona)
- [Arquitetura](#arquitetura)
- [Arquivos e Fontes Suportadas](#arquivos-e-fontes-suportadas)
- [Processamento de Arquivos](#processamento-de-arquivos)
- [Arquitetura Low-Token](#arquitetura-low-token)
- [Image Curator e Vision](#image-curator-e-vision)
- [Estrutura do Repositório Gerado](#estrutura-do-repositório-gerado)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [Testes](#testes)
- [Notas de Manutenção](#notas-de-manutenção)
- [Licença](#licença)

## Visão Geral

O **GPT Tutor Generator** foi projetado para organizar materiais de estudo reais de uma disciplina ao longo do semestre e convertê-los em um repositório navegável por IA.

Ele combina:

- importação multiformato
- processamento automático de PDFs e documentos
- revisão manual dos casos difíceis
- curadoria de imagens acadêmicas
- geração de instruções e artefatos para Claude, GPT e Gemini

O sistema mantém contexto de:

- disciplina
- professor
- semestre
- cronograma
- perfil do aluno
- progresso de processamento

## Como o App Funciona

Fluxo de alto nível:

```text
Importar materiais
  -> classificar e configurar entries
  -> processar PDFs / links / código / imagens
  -> revisar saídas problemáticas
  -> curar imagens e extrair descrições
  -> consolidar conteúdo em markdown
  -> gerar arquivos de instrução e estrutura pedagógica
```

Fluxo típico no app:

1. Criar ou selecionar uma matéria.
2. Definir pasta do repositório.
3. Importar arquivos e links.
4. Processar a fila.
5. Revisar saídas em `manual-review/` quando necessário.
6. Abrir o **Image Curator** para imagens extraídas de PDFs ou fotos.
7. Gerar descrições e extrações em LaTeX.
8. Construir ou atualizar o repositório final.
9. Usar **Reprocessar Repositório** para reaplicar a arquitetura atual em repositórios já existentes.

## Arquitetura

```text
app.py
  -> bootstrap da aplicação

src/
├── builder/
│   ├── engine.py            # pipeline principal de processamento e build
│   ├── image_classifier.py  # heurísticas para imagens
│   ├── ollama_client.py     # integração Vision via Ollama /api/chat
│   └── vision_client.py     # fábrica do cliente de vision
├── models/
│   └── core.py             # dataclasses e modelos persistidos
├── ui/
│   ├── app.py              # janela principal
│   ├── dialogs.py          # configurações, status, ajuda, dialogs utilitários
│   ├── image_curator.py    # curadoria de imagens e extração visual
│   └── theme.py            # tema e configuração persistente
└── utils/
    └── helpers.py          # helpers, autodetects, OCR/Tesseract e utilidades
```

### Decisões Atuais de Arquitetura

- Backend de vision ativo: `ollama`
- Endpoint usado para vision: `/api/chat`
- Modelo padrão: `qwen3-vl:235b-cloud`
- Mesmo modelo para:
  - descrição de imagens
  - extração fiel de texto/matemática com prompt de LaTeX
- Diferença entre os modos: apenas o prompt
- A arquitetura de contexto para Claude Web é **map-first**:
  - comece por `course/COURSE_MAP.md`
  - consulte `student/STUDENT_STATE.md` para calibrar profundidade e evitar repetição
  - use `course/FILE_MAP.md` para localizar o material certo
  - abra markdowns longos só quando os artefatos curtos não bastarem

## Arquitetura Low-Token

O projeto agora gera artefatos pensados para **baixo custo de contexto** em LLMs web, especialmente no Claude.

Princípios:

- começar por arquivos curtos e roteadores
- usar `STUDENT_STATE.md` antes de repetir conteúdo ou subir demais a profundidade
- abrir markdowns longos apenas como último recurso, não como padrão
- promover para o bundle só metadados e materiais de alto sinal
- compactar descrições de imagem antes de injetar no markdown final
- reduzir repetição visual de slides/PDFs exportados de PPTX

Arquivos-chave dessa arquitetura:

```text
course/COURSE_MAP.md
course/FILE_MAP.md
build/claude-knowledge/bundle.seed.json
INSTRUCOES_CLAUDE_PROJETO.md
```

### O que mudou na prática

- `COURSE_MAP.md` ficou mais curto e funciona como mapa pedagógico
- `STUDENT_STATE.md` passou a entrar no fluxo de leitura antes dos materiais longos
- `FILE_MAP.md` virou índice de roteamento com `quando abrir` e `prioridade`
- `bundle.seed.json` agora é seletivo, focado em metadados e registra o motivo de inclusão de cada item
- descrições de imagem no markdown final entram em versão compacta
- duplicatas exatas entre páginas vizinhas podem virar referência curta, em vez de repetir o bloco inteiro

### Como aplicar isso em repositórios antigos

Use a ação **Reprocessar Repositório** no backlog.

Essa ação:

- não reextrai PDFs crus por padrão
- reutiliza o `manifest.json`
- regenera os artefatos pedagógicos com o código atual
- reaplica `COURSE_MAP`, `FILE_MAP`, bundle e instruções atualizados
- mantém o fluxo `map-first` com `STUDENT_STATE.md` antes de abrir markdowns longos
- reinjeta descrições de imagem com a lógica mais nova

Isso é o caminho recomendado para atualizar repositórios que já estavam prontos antes dessas mudanças.

## Arquivos e Fontes Suportadas

O app suporta entradas dos seguintes tipos:

```text
pdf
image
url
github-repo
code
zip
```

### Exemplos práticos

- PDFs de aula
- provas e listas escaneadas
- fotos de quadro
- screenshots de material
- páginas web e bibliografias online
- repositórios GitHub
- arquivos `.py`, `.js`, `.java`, `.cpp` e outros
- ZIPs com material compactado

### Categorias acadêmicas disponíveis

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

## Processamento de Arquivos

O pipeline usa múltiplas camadas e heurísticas.

### Modos de processamento

```text
auto
quick
high_fidelity
manual_assisted
```

### Perfis de documento

```text
auto
general
math_light
math_heavy
layout_heavy
scanned
exam_pdf
```

### Backends de extração

Base:

- `pymupdf4llm`
- `pymupdf`

Avançados:

- `docling`
- `marker`

O sistema também consegue:

- extrair imagens
- extrair tabelas
- forçar OCR
- preservar imagens do PDF no markdown
- limitar páginas por faixa
- consolidar saídas intermediárias
- regenerar artefatos derivados sem reprocessar tudo do zero

## Image Curator e Vision

O **Image Curator** é a camada de curadoria visual do projeto.

Ele opera sobre `content/images/` e faz:

- agrupamento por página
- preview de imagens
- preview da página do PDF
- captura manual de regiões
- classificação heurística
- descrição acadêmica de imagens
- extração de texto + matemática com saída em Markdown/LaTeX
- sinalização de duplicatas exatas entre páginas
- injeção compacta de descrições no markdown final

### Tipos visuais usados no curator

```text
diagrama
tabela
fórmula
código
genérico
decorativa
extração-latex
```

### Runtime atual de Vision

```text
Backend:  ollama
Modelo:   qwen3-vl:235b-cloud
Fallback: qwen3-vl:8b
Endpoint: http://localhost:11434/api/chat
```

### Setup do Ollama

```powershell
ollama signin
ollama pull qwen3-vl:235b-cloud
ollama pull qwen3-vl:8b
```

Opcionalmente, se quiser apenas testar o fallback local:

```powershell
ollama pull qwen3-vl:8b
```

### Validação no App

Na interface:

1. abra `📊 Status`
2. localize a seção `Vision — Descrição de Imagens`
3. clique em `Validar Vision`

O app verifica automaticamente:

- Ollama acessível
- modelo configurado disponível
- fallback disponível
- readiness de cloud quando o modelo termina com `-cloud`

### Otimização de contexto visual

As descrições de imagem usadas no conteúdo final não são mais injetadas de forma verbosa por padrão.

Regras atuais:

- priorizar uma descrição curta e útil
- evitar repetir raciocínio do modelo
- reduzir duplicatas visuais entre páginas consecutivas
- manter rastreabilidade por comentário `IMAGE_DESCRIPTION`

### Observações importantes

- `qwen3-vl:235b-cloud` exige `ollama signin`
- o uso pode ser limitado pelo plano da conta Ollama
- documentos sensíveis deixam de ser estritamente locais ao usar cloud models

## Estrutura do Repositório Gerado

```text
{repo-root}/
├── INSTRUCOES_CLAUDE_PROJETO.md
├── INSTRUCOES_GPT_PROJETO.md
├── INSTRUCOES_GEMINI_PROJETO.md
├── manifest.json
├── build/
├── content/
├── course/
├── exercises/
├── exams/
├── manual-review/
├── raw/
├── staging/
├── student/
└── system/
```

### Pastas importantes

- `raw/`: cópias dos arquivos originais
- `staging/`: saídas intermediárias e automáticas
- `manual-review/`: revisão manual guiada
- `content/`: conteúdo textual consolidado
- `exercises/`: materiais de exercício
- `exams/`: materiais de prova
- `build/`: artefatos de build e bundles

## Requisitos

- Python `3.8+`
- ambiente com `tkinter`
- Ollama instalado
- Ollama acessível em `http://localhost:11434`

Dependências Python principais:

- `pymupdf`
- `pymupdf4llm`
- `pdfplumber`
- `Pillow`
- `pytest` para desenvolvimento

Ferramentas opcionais:

- `docling`
- `marker-pdf`
- `tesseract`

## Instalação

### Windows / PowerShell

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .[dev]
```

Backends opcionais:

```powershell
pip install docling
pip install marker-pdf
```

Se for usar OCR:

- instale o Tesseract
- garanta `tessdata` configurado corretamente

## Configuração

### `.env`

Hoje, **não é necessário adicionar nada novo no `.env` para o pipeline de vision com Ollama**.

Seu `.env` atual pode continuar só com as chaves de LLMs externas já usadas em outros fluxos do projeto:

```env
OPENAI_API_KEY=''
GEMINI_API_KEY=''
```

### Configuração persistida do app

As opções do app ficam em:

```text
~/.gpt_tutor_config.json
```

Exemplo:

```json
{
  "vision_backend": "ollama",
  "vision_model": "qwen3-vl:235b-cloud",
  "vision_model_quantization": "default",
  "ollama_base_url": "http://localhost:11434"
}
```

### O que realmente precisa para Vision funcionar

```powershell
ollama signin
ollama pull qwen3-vl:235b-cloud
ollama pull qwen3-vl:8b
```

## Execução

### Script PowerShell

```powershell
.\run.ps1
```

### Script batch

```bat
run.bat
```

### Execução direta

```powershell
python app.py
```

## Testes

Rodar a suíte principal:

```powershell
pytest tests -q
```

Rodar apenas os testes do Image Curator / Vision:

```powershell
pytest tests\test_image_curation.py -q
```

## Notas de Manutenção

- O pipeline de vision ativo é Ollama-only
- O ponto de verdade do fluxo atual está em:
  - `src/builder/ollama_client.py`
  - `src/builder/vision_client.py`
  - `src/ui/image_curator.py`
  - `src/ui/dialogs.py`
- Documentos em `docs/superpowers/` podem descrever versões históricas da implementação
- O modelo padrão de maior qualidade hoje é `qwen3-vl:235b-cloud`

## Licença

MIT
