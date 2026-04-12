# GPT Tutor Generator

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](#requisitos)
[![UI](https://img.shields.io/badge/UI-Tkinter-1f6feb)](#arquitetura)
[![Vision](https://img.shields.io/badge/Vision-Ollama-000000)](#image-curator-e-vision)
[![Backend](https://img.shields.io/badge/PDF-Datalab-0f766e)](#backend-datalab)
[![License](https://img.shields.io/badge/Licenca-MIT-green)](#licenca)

Aplicação desktop em Python para transformar materiais acadêmicos em um repositório Markdown estruturado, curado e pronto para uso com tutores baseados em LLM.

## Sumário

- [Visão Geral](#visao-geral)
- [Como o App Funciona](#como-o-app-funciona)
- [Arquitetura](#arquitetura)
- [Processamento de Arquivos](#processamento-de-arquivos)
- [Backend Datalab](#backend-datalab)
- [Arquitetura Low-Token](#arquitetura-low-token)
- [Image Curator e Vision](#image-curator-e-vision)
- [Estrutura do Repositório Gerado](#estrutura-do-repositorio-gerado)
- [Requisitos](#requisitos)
- [Instalação](#instalacao)
- [Configuração](#configuracao)
- [Execução](#execucao)
- [Testes](#testes)
- [Notas de Manutenção](#notas-de-manutencao)
- [Licença](#licenca)

## Visão Geral

O **GPT Tutor Generator** organiza materiais reais de uma disciplina ao longo do semestre e os converte em um repositório navegável por IA.

O app combina:

- importação multiformato
- processamento automático de PDFs, links, imagens e código
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
2. Definir a pasta do repositório.
3. Importar arquivos e links.
4. Processar a fila.
5. Revisar saídas em `manual-review/` quando necessário.
6. Abrir o **Image Curator** para imagens extraídas de PDFs ou fotos.
7. Construir ou atualizar o repositório final.
8. Usar **Reprocessar Repositório** para reaplicar a arquitetura atual em repositórios já existentes.
9. Usar a aba **Tasks de Repositório** para enfileirar builds, reprocessamentos e processamentos individuais.
10. Abrir a aba **Dashboard** para acompanhar o estado operacional dos repositórios.

Observação operacional: a fila é persistente entre sessões do app, então builds e reprocessamentos podem ser retomados sem recriar toda a fila manualmente.

## Arquitetura

```text
app.py
  -> bootstrap da aplicação

src/
|-- builder/
|   |-- engine.py            # pipeline principal de processamento e build
|   |-- datalab_client.py    # integração com a API do Datalab
|   |-- image_classifier.py  # heurísticas para imagens
|   |-- ollama_client.py     # integração Vision via Ollama /api/chat
|   `-- vision_client.py     # fábrica do cliente de vision
|-- models/
|   `-- core.py              # dataclasses e modelos persistidos
|-- ui/
|   |-- app.py               # janela principal
|   |-- dialogs.py           # configurações, status, ajuda e dialogs
|   |-- curator_studio.py    # revisão manual e curadoria
|   |-- image_curator.py     # curadoria de imagens e extração visual
|   `-- theme.py             # tema e configuração persistente
`-- utils/
    |-- helpers.py           # helpers, autodetects, OCR/Tesseract e utilidades
    `-- power.py             # prevenção de sleep durante builds longos
```

### Decisões Atuais de Arquitetura

- Backend de vision ativo: `ollama`
- Endpoint usado para vision: `/api/chat`
- O pipeline PDF é híbrido e seleciona backends conforme o perfil e a disponibilidade local/cloud
- Para `math_heavy`, o **Datalab** é hoje a alternativa mais previsível quando a API key está configurada
- `marker` continua disponível, mas não é o caminho principal recomendado no estado atual do projeto
- A arquitetura de contexto para Claude Web é **map-first**:
  - começar por `course/COURSE_MAP.md`
  - consultar `student/STUDENT_STATE.md` para calibrar profundidade e evitar repetição
  - usar `course/FILE_MAP.md` para localizar o material certo
  - abrir markdowns longos só quando os artefatos curtos não bastarem

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
math_heavy
diagram_heavy
scanned
```

### Backends de extração

Base:

- `pymupdf4llm`
- `pymupdf`

Avançados:

- `datalab`
- `docling`
- `docling_python`
- `marker`

### Observação prática sobre backends

No estado atual do projeto:

- `datalab` é a melhor aposta para PDFs `math_heavy`
- `docling` e `docling_python` continuam úteis para comparação e processamento local
- `marker` continua disponível, mas está em fase de investigação/refino e não é a rota principal recomendada agora

O sistema também consegue:

- extrair imagens
- extrair tabelas
- forçar OCR
- preservar imagens do PDF no markdown
- limitar páginas por faixa
- consolidar saídas intermediárias
- regenerar artefatos derivados sem reprocessar tudo do zero

## Backend Datalab

O projeto agora suporta **Datalab** como backend avançado de processamento de PDF.

Ele é especialmente útil para:

- materiais `math_heavy`
- PDFs com fórmulas e layout complexo
- casos em que o pipeline local não está entregando a qualidade esperada

### Como o backend é usado

- Se `DATALAB_API_KEY` estiver definida, o app pode preferir `datalab` automaticamente em `math_heavy`
- Também é possível selecionar `Backend preferido = datalab` manualmente por entry
- Quando `datalab` é escolhido, o item passa a ter um seletor `Modelo` com:
  - `fast`
  - `balanced`
  - `accurate`

### Modos do Datalab

- `fast`: menor custo e maior velocidade
- `balanced`: equilíbrio entre custo e qualidade
- `accurate`: maior qualidade, especialmente útil para material matemático

### Saída do Datalab

As saídas são gravadas em:

```text
staging/markdown-auto/datalab/<entry>/
```

Com artefatos como:

- markdown retornado pela API
- imagens extraídas
- `datalab-run.json` com metadados da execução

### Configuração mínima

No arquivo `.env`:

```env
DATALAB_API_KEY=
DATALAB_BASE_URL=https://www.datalab.to
```

Sem `DATALAB_API_KEY`, o backend continua indisponível.

### Observação de custo

O Datalab é um serviço externo com cobrança por página. Antes de adotar como backend principal, verifique:

- o custo por volume de páginas
- a necessidade de enviar documentos para serviço externo
- requisitos de privacidade do seu material

Documentação oficial:

- https://documentation.datalab.to/

## Arquitetura Low-Token

O projeto gera artefatos pensados para **baixo custo de contexto** em LLMs web, especialmente no Claude.

Princípios:

- começar por arquivos curtos e roteadores
- usar `STUDENT_STATE.md` antes de repetir conteúdo ou subir demais a profundidade
- abrir markdowns longos apenas como último recurso
- promover para o bundle só metadados e materiais de alto sinal
- compactar descrições de imagem antes de injetar no markdown final
- reduzir repetição visual de slides e PDFs exportados

Arquivos-chave dessa arquitetura:

```text
course/COURSE_MAP.md
course/FILE_MAP.md
exercises/EXERCISE_INDEX.md
build/claude-knowledge/bundle.seed.json
INSTRUCOES_CLAUDE_PROJETO.md
```

### O que muda na prática

- `COURSE_MAP.md` funciona como mapa pedagógico curto
- `STUDENT_STATE.md` entra no fluxo antes dos materiais longos
- `FILE_MAP.md` vira índice de roteamento com prioridade e contexto
- `EXERCISE_INDEX.md` vira roteador de prática por unidade
- `bundle.seed.json` fica seletivo e focado em metadados

### Como aplicar isso em repositórios antigos

Use a ação **Reprocessar Repositório** no backlog para reaplicar a arquitetura atual.

Essa ação:

- não reextrai PDFs crus por padrão
- reutiliza o `manifest.json`
- regenera os artefatos pedagógicos com o código atual
- reaplica `COURSE_MAP`, `FILE_MAP`, bundle e instruções atualizados

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
formula
codigo
generico
decorativa
extracao-latex
```

### Runtime atual de Vision

```text
Backend:  ollama
Endpoint: http://localhost:11434/api/chat
```

O pipeline de vision do **Image Curator** é independente do backend PDF principal. Ou seja:

- você pode usar `datalab` para PDFs
- e continuar usando `ollama` no curator de imagens

### Setup do Ollama

Exemplo:

```powershell
ollama signin
ollama pull qwen3-vl:235b-cloud
ollama pull qwen3-vl:8b
```

Opcionalmente, se quiser apenas testar o fallback local:

```powershell
ollama pull qwen3-vl:8b
```

### Validação no app

Na interface:

1. abra `Status`
2. localize a seção `Vision`
3. clique em `Validar Vision`

O app verifica:

- Ollama acessível
- modelo configurado disponível
- fallback disponível

## Estrutura do Repositório Gerado

```text
{repo-root}/
|-- INSTRUCOES_CLAUDE_PROJETO.md
|-- INSTRUCOES_GPT_PROJETO.md
|-- INSTRUCOES_GEMINI_PROJETO.md
|-- manifest.json
|-- build/
|-- content/
|-- course/
|-- exercises/
|-- exams/
|-- manual-review/
|-- raw/
|-- staging/
|-- student/
`-- system/
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
- Ollama instalado para o fluxo de vision
- Ollama acessível em `http://localhost:11434`

Dependências Python principais:

- `pymupdf`
- `pymupdf4llm`
- `pdfplumber`
- `Pillow`
- `requests`
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

Se for usar OCR local:

- instale o Tesseract
- garanta `tessdata` configurado corretamente

## Configuração

### `.env`

Hoje, o `.env` pode incluir tanto chaves externas quanto a chave do Datalab:

```env
DATALAB_API_KEY=
DATALAB_BASE_URL=https://www.datalab.to
OPENAI_API_KEY=
GEMINI_API_KEY=
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
  "ollama_base_url": "http://localhost:11434",
  "prevent_sleep_during_build": true
}
```

### O que realmente precisa para cada fluxo

Para usar o **Image Curator** com Vision:

```powershell
ollama signin
ollama pull qwen3-vl:235b-cloud
ollama pull qwen3-vl:8b
```

Para usar o **Datalab**:

- preencher `DATALAB_API_KEY` no `.env`

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

- O pipeline de vision do curator continua sendo `Ollama`
- O pipeline PDF agora pode usar `datalab`, `docling`, `docling_python` e `marker`
- Para `math_heavy`, o Datalab é a principal alternativa prática no estado atual do projeto
- `marker` continua no projeto, mas está em investigação e refinamento
- O ponto de verdade do fluxo atual está em:
  - [src/builder/engine.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/engine.py)
  - [src/builder/datalab_client.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/datalab_client.py)
  - [src/builder/ollama_client.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ollama_client.py)
  - [src/ui/image_curator.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/ui/image_curator.py)
  - [src/ui/dialogs.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/ui/dialogs.py)
- Documentos em `docs/superpowers/` podem descrever versões históricas da implementação

## Licença

MIT
