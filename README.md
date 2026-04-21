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
- [Roadmap](#roadmap)
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
|   |-- engine.py            # facade principal e orquestração do build
|   |-- artifacts/           # COURSE_MAP, FILE_MAP, prompts e índices
|   |-- core/                # config semântica e utilidades centrais
|   |-- extraction/          # taxonomy, sinais e helpers de extração
|   |-- facade/              # wiring configurado usado pela facade
|   |-- ops/                 # operações de build, regen e fila
|   |-- pdf/                 # pipeline PDF e assets
|   |-- routing/             # matching e roteamento do FILE_MAP
|   |-- runtime/             # integrações com backends externos
|   |-- text/                # sanitização textual e URL -> markdown
|   |-- timeline/            # índice e sinais do cronograma
|   `-- vision/              # clientes de vision e classificação visual
|-- models/
|   |-- core.py              # dataclasses e modelos persistidos
|   `-- task_queue.py        # RepoTask e RepoTaskStore (fila persistida)
|-- ui/
|   |-- app.py                       # janela principal
|   |-- consolidate_unit_dialog.py   # diálogo de consolidação de unidade
|   |-- curator_studio.py            # revisão manual e curadoria
|   |-- dialogs.py                   # configurações, status, ajuda e dialogs
|   |-- image_curator.py             # curadoria de imagens e extração visual
|   |-- repo_dashboard.py            # dashboard operacional de repositórios
|   `-- theme.py                     # tema e configuração persistente
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

### Extração de imagens pelo Datalab

Quando o Datalab processa um PDF, as imagens são salvas automaticamente em:

```text
staging/markdown-auto/datalab/<entry>/images/
```

O caminho é propagado via `BackendRunResult.images_dir` até o manifest do item e fica disponível para o **Image Curator** sem processamento adicional.

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
setup/INSTRUCOES_CLAUDE_PROJETO.md
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
|-- manifest.json
|-- build/
|-- content/
|-- course/
|-- exercises/
|-- exams/
|-- manual-review/
|-- raw/
|-- setup/
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

- Windows 10/11
- Python `3.11` recomendado
- `tkinter` habilitado na instalacao do Python
- Git
- Ollama local para o fluxo de Vision

Dependencias Python usadas de fato pelo app:

- `pymupdf`
- `pymupdf4llm`
- `pdfplumber`
- `Pillow`
- `requests`
- `beautifulsoup4`
- `pytest` para desenvolvimento

Ferramentas externas opcionais, mas importantes:

- `tesseract` para OCR local
- `docling` CLI
- `marker_single` via `marker-pdf`

Servicos externos opcionais:

- Datalab para PDFs `math_heavy`
- Ollama para Vision no Image Curator
- OpenAI / Gemini so se voce usar essas integracoes fora do fluxo local principal

### Stack operacional

Hoje, o stack pratico do projeto e:

- UI desktop: `Tkinter`
- processamento PDF base: `PyMuPDF`, `PyMuPDF4LLM`, `pdfplumber`
- HTTP / integracoes cloud: `requests`
- parsing HTML de URLs: `beautifulsoup4`
- imagens na UI: `Pillow`
- vision local: `Ollama`
- OCR local opcional: `Tesseract`
- PDF cloud opcional: `Datalab`

## Instalacao

### Windows / PowerShell

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -e .[dev]
```

### Bootstrap completo em maquina nova

```powershell
git clone <URL_DO_REPOSITORIO>
cd GPT-Tutor-Generator
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -e .[dev]
pip install docling marker-pdf
```

### CLIs opcionais

```powershell
pip install docling
pip install marker-pdf
```

### Tesseract OCR

Se voce usar OCR local, instale o Tesseract e deixe o executavel no `PATH`. Veja detalhes de configuração de `TESSDATA_PREFIX` na seção [Configuração](#configuracao).

### Ollama

O Image Curator usa Ollama. O minimo e ter o servidor local ativo:

```powershell
ollama serve
```

Modelos uteis:

```powershell
ollama pull qwen3-vl:8b
ollama pull qwen3-vl:235b-cloud
```

Se o servidor nao estiver em `http://localhost:11434`, ajuste isso nas configuracoes do app.

### Validacao rapida do ambiente

No app, abra `Status` e confira:

- `Datalab API`
- `docling CLI`
- `marker CLI`
- `TESSDATA`
- `Vision`

Essa e a forma mais rapida de validar o outro computador.

## Configuracao

### Variáveis de sistema (PATH)

O app depende que os executáveis abaixo estejam disponíveis no `PATH` do sistema:

| Executável | Obrigatório | Função |
|---|---|---|
| `python` | sim | rodar o app |
| `ollama` | sim, para Vision | servidor de vision local |
| `tesseract` | não | OCR local (fallback) |
| `docling` | não | backend PDF alternativo |
| `marker_single` | não | backend PDF alternativo (em investigação) |

Se a autodetecção do `TESSDATA_PREFIX` falhar, defina manualmente:

```powershell
# Temporário (sessão atual)
$env:TESSDATA_PREFIX = "C:\Program Files\Tesseract-OCR\tessdata"

# Permanente
[Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", "C:\Program Files\Tesseract-OCR\tessdata", "User")
```

### `.env`

O projeto carrega automaticamente o arquivo `.env` na raiz, sem sobrescrever variáveis já existentes no sistema.

Variáveis atualmente em uso:

```env
DATALAB_API_KEY=          # necessária para o backend datalab
DATALAB_BASE_URL=https://www.datalab.to
```

- `DATALAB_API_KEY` é a única chave necessária no fluxo principal atual
- `DATALAB_BASE_URL` pode ficar no padrão

### Configuracao persistida do app

As opcoes da UI ficam fora do repositorio, no diretorio de dados do usuario.

No Windows, o app usa:

```text
%APPDATA%\GPTTutorGenerator
```

Em geral, vale copiar isso apenas se voce quiser reaproveitar preferencias de interface e modelos configurados.

Campos relevantes:

- `vision_backend`
- `vision_model`
- `vision_model_quantization`
- `ollama_base_url`
- `prevent_sleep_during_build`

## Execucao

### Rodar com o venv ativado

```powershell
& .\.venv\Scripts\Activate.ps1
python app.py
```

### Script PowerShell

```powershell
.\run.ps1
```

### Script batch

```bat
run.bat
```

### Comandos uteis de desenvolvimento

```powershell
python -m pytest tests -q
python -m pytest tests\test_image_curation.py -q
```

### Execucao direta

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

## Roadmap

O roadmap completo está em [`ROADMAP.md`](ROADMAP.md).

Itens planejados em ordem de prioridade:

| # | Feature | Esforço | Ganho |
|---|---|---|---|
| 1 | **Student State** — painel de captura de sessão para eliminar cold start | médio | alto |
| 2 | **Sinalizador DD.MM** — data no nome do arquivo como boost de mapeamento | baixo | médio |
| 3 | **Cronograma visual** — timeline bloco × arquivo no app | médio | alto |
| 4 | **NotebookLM** — export como destino adicional além de Claude/GPT/Gemini | médio | alto |
| 5 | **MinerU** — backend PDF open-source com foco em equações | alto | alto |
| 6 | **Marker-API** — versão cloud do Marker sem dependência de GPU local | médio | médio |
| 7 | **Obsidian / Notion** — compatibilidade de saída com segundos cérebros | alto | médio |
| 8 | **Instalador Windows** — Setup.exe com wizard, publicado nas Releases do GitHub | alto | alto |

## Notas de Manutenção

- O pipeline de vision do curator continua sendo `Ollama`
- O pipeline PDF agora pode usar `datalab`, `docling`, `docling_python` e `marker`
- Para `math_heavy`, o Datalab é a principal alternativa prática no estado atual do projeto
- `marker` continua no projeto, mas está em investigação e refinamento
- O ponto de verdade do fluxo atual está em:
  - [src/builder/engine.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/engine.py)
  - [src/builder/runtime/datalab_client.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/runtime/datalab_client.py)
  - [src/builder/vision/ollama_client.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/vision/ollama_client.py)
  - [src/ui/image_curator.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/ui/image_curator.py)
  - [src/ui/dialogs.py](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/ui/dialogs.py)
- Documentos em `docs/superpowers/` podem descrever versões históricas da implementação

## Licença

MIT
