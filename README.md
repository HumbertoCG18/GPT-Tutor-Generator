# GPT Tutor Generator

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](#requisitos)
[![UI](https://img.shields.io/badge/UI-Tkinter-1f6feb)](#arquitetura)
[![PDF](https://img.shields.io/badge/PDF-Datalab%20%C2%B7%20Marker%20%C2%B7%20Docling-0f766e)](#backends-de-extração)
[![Vision](https://img.shields.io/badge/Vision-Ollama-000000)](#image-curator-e-vision)
[![LLM](https://img.shields.io/badge/Resumos-Gemini-4285F4?logo=google&logoColor=white)](#resumos-via-gemini-opcional)
[![Tests](https://img.shields.io/badge/Testes-1100%2B-4ade80)](#testes)
[![License](https://img.shields.io/badge/Licença-MIT-green)](#licença)

Aplicação desktop (Windows) que transforma os materiais reais de uma disciplina — PDFs, slides, código, links, Moodle — em um **repositório Markdown estruturado, curado e pronto para uso com tutores baseados em LLM** (Claude, GPT, Gemini).

O diferencial: o repositório gerado não é só uma pilha de markdowns. Ele carrega **contexto pedagógico** — cronograma da disciplina, mapeamento arquivo→aula, escopo de provas, estado do aluno — para que o tutor saiba *onde* o aluno está no semestre e *o que* importa agora.

---

## Sumário

- [Principais Recursos](#principais-recursos)
- [Como Funciona](#como-funciona)
- [Início Rápido](#início-rápido)
- [Arquitetura](#arquitetura)
- [Pipeline de Processamento](#pipeline-de-processamento)
- [Backends de Extração](#backends-de-extração)
- [Perfis de Processamento](#perfis-de-processamento)
- [Cronograma e Mapeamento Automático](#cronograma-e-mapeamento-automático)
- [Importação Moodle / M365](#importação-moodle--m365)
- [Curadoria](#curadoria)
- [Image Curator e Vision](#image-curator-e-vision)
- [Resumos via Gemini (opcional)](#resumos-via-gemini-opcional)
- [Arquitetura Low-Token](#arquitetura-low-token)
- [Repositório Gerado](#repositório-gerado)
- [Configuração](#configuração)
- [Testes](#testes)
- [Roadmap](#roadmap)
- [Licença](#licença)

---

## Principais Recursos

| | Recurso | Descrição |
|---|---|---|
| 📥 | **Importação multiformato** | PDFs, imagens, código (`.py`, `.ipynb`, `.dfy`…), ZIPs, repositórios GitHub, URLs e import direto do Moodle (incluindo OneDrive/M365) |
| 🧠 | **Extração híbrida de PDF** | Seleção automática de backend por perfil do documento: PyMuPDF para texto simples, Datalab/Marker/Docling para material matemático ou escaneado |
| 📅 | **Cronograma inteligente** | Parse do cronograma institucional, classificação de blocos (aula, prova, revisão, feriado), escopo automático de avaliações e mapeamento arquivo→aula com score de confiança |
| 🏷️ | **Mapeamento com aprendizado** | Correções manuais alimentam um perfil de tags por matéria que melhora os mapeamentos futuros |
| 🖼️ | **Curadoria visual** | Image Curator com descrições via Ollama ou captions do Datalab; Curator Studio para revisão de extrações difíceis |
| 🤖 | **Enriquecimento via Gemini** | Resumos de código e referências bibliográficas com cache por hash (reprocessar não custa tokens) |
| 🎓 | **Estado do aluno** | Perfil, personalidade e progresso por tópico (`STUDENT_STATE.md`) consumidos pelo tutor para calibrar profundidade |
| ⚙️ | **Operação resiliente** | Fila de tasks persistente, builds retomáveis, arquivos ausentes não abortam o build, limpeza automática de curadoria órfã |

---

## Como Funciona

```text
Importar materiais (PDF, código, links, Moodle)
   → classificar e configurar entries na fila
   → processar: extração + sanitização + assets
   → mapear cada arquivo para unidade/bloco do cronograma
   → revisar casos difíceis (manual-review, curadores)
   → enriquecer: resumos Gemini, descrições de imagem
   → gerar repositório: índices, mapas, instruções por plataforma
```

Fluxo típico no app:

1. Criar ou selecionar uma **matéria** (cronograma + plano de ensino + pasta do repositório).
2. Importar arquivos, links ou puxar direto do **Moodle**.
3. **Processar a fila** (ou enfileirar como task de repositório).
4. Revisar saídas problemáticas em `manual-review/` e nos curadores.
5. Ajustar mapeamentos na aba **Cronograma** ou no editor de **Backlog**.
6. **Build/Reprocessar** — regenera todos os artefatos pedagógicos com o código atual, sem reextrair PDFs.

A fila é persistente entre sessões; builds e reprocessamentos podem ser retomados.

---

## Início Rápido

```powershell
git clone <URL_DO_REPOSITORIO>
cd GPT-Tutor-Generator
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -e .[dev]

# backends avançados de PDF (opcionais)
pip install docling marker-pdf

python app.py
```

Validação do ambiente: no app, abra **Status** e confira `Datalab API`, `docling CLI`, `marker CLI`, `TESSDATA` e `Vision`.

### Requisitos

- Windows 10/11, Python **3.11+** com `tkinter`
- Dependências principais: `pymupdf`, `pymupdf4llm`, `pdfplumber`, `Pillow`, `requests`, `beautifulsoup4`
- Opcionais: **Ollama** (vision local), **Tesseract** (OCR), **Datalab** (PDF cloud), **Gemini** (resumos), `docling`/`marker-pdf` (backends locais avançados)

---

## Arquitetura

```text
app.py                      # bootstrap

src/
├── builder/
│   ├── engine.py           # façade — ponto único de entrada; backends e BackendSelector
│   ├── ops/                # orquestração: build completo, incremental, regeneração, fila
│   ├── core/               # importers (código/zip/github), resumos LLM, resolução de imagens
│   ├── timeline/           # índice do cronograma, classificador de blocos, escopo de provas
│   ├── extraction/         # taxonomia de conteúdo, sinais de entry, tags automáticas
│   ├── artifacts/          # geradores de markdown: mapas, índices, instruções, health
│   ├── routing/            # scoring arquivo × unidade/bloco (FILE_MAP)
│   ├── pdf/                # perfil de documento, pipeline PDF, assets
│   ├── runtime/            # clientes externos: Datalab, Gemini, Marker/Docling config
│   ├── sources/            # Moodle e Microsoft 365
│   ├── text/               # normalização e sanitização
│   ├── vision/             # cliente Ollama, classificação visual, evidência de cards
│   └── facade/             # wiring de aliases usado pela façade
├── models/                 # FileEntry, perfis, RepoTask (fila persistida)
├── ui/                     # janela principal, 8 abas, dialogs, curadores
└── utils/                  # helpers, parse de cronograma HTML, OCR, power management
```

**Camadas:** a UI conversa com o builder exclusivamente via `engine.py` (façade estável). O engine orquestra `ops` → domínio (`timeline`, `extraction`, `artifacts`, `routing`) → base (`text`, `models`, `utils`).

**Abas da UI:** Fila a Processar · Tasks de Repositório · Backlog · Dashboard · Cronograma · Códigos · Manutenção · Log.

---

## Pipeline de Processamento

```text
① ENTRADA      process_entry() roteia por tipo e copia o bruto para raw/
② PERFIL       _profile_pdf() → densidade de texto, scan suspeito, tabelas
               BackendSelector decide base + avançado conforme o perfil
③ EXTRAÇÃO     base (PyMuPDF/PyMuPDF4LLM) e/ou avançada (Datalab, Marker, Docling)
               → staging/markdown-auto/  (com chunking e fallback automático)
④ SANITIZAÇÃO  detecção de corrupção LaTeX, híbrido marker+base,
               normalização matemática, extração de imagens com filtro de ruído
⑤ ROTEAMENTO   manual → card Moodle → léxico → conteúdo (scoring com confiança)
               resultado no manifest: unidade, bloco, banda, razões
⑥ LLM (opc.)   resumos de código e referências via Gemini (cache por hash)
⑦ TIMELINE     classificação de blocos, escopo de avaliações, taxonomia, tags
⑧ ARTEFATOS    87+ arquivos: mapas, índices, instruções, relatórios, export
```

### Resiliência

- **Arquivo-fonte ausente** não aborta o build: entry vai para `failed_entries` com `error_type=missing_source` e a UI lista os ausentes ao final.
- **Curadoria órfã** é podada automaticamente no reprocessamento (`prune_stale_image_curation`): descrições de imagens deletadas são removidas, páginas vazias são limpas.
- **Fallback de backend**: timeout no Marker dispara retry com chunking; indisponibilidade cai para o próximo backend do perfil.

---

## Backends de Extração

| Backend | Tipo | Quando usar |
|---|---|---|
| `pymupdf4llm` / `pymupdf` | base, local | texto digital simples — rápido e grátis |
| `datalab` | avançado, cloud | **melhor opção para `math_heavy`** — fórmulas, layout complexo (requer `DATALAB_API_KEY`; cobrança por página) |
| `marker` | avançado, local | alternativa local com suporte a LLM auxiliar; chunking e fallback automáticos |
| `docling` / `docling_python` | avançado, local | comparação e processamento local |

A opção **Pular backends base** (Configurações → Processamento) força ir direto ao backend avançado, útil quando a extração base nunca é aproveitada para um perfil de material.

Saídas do Datalab ficam em `staging/markdown-auto/datalab/<entry>/` com markdown, imagens extraídas e `datalab-run.json` (metadados, custo, qualidade do parse).

---

## Perfis de Processamento

Perfis nomeados unificam **modo de processamento + backend preferido + modo Datalab + perfil de documento** num seletor único (toolbar e por entry). O mapeamento perfil→backend usado pelo roteamento automático é **derivado dos próprios perfis** — fonte única de configuração, sem tabelas paralelas.

- Modos: `auto`, `quick`, `high_fidelity`, `manual_assisted`
- Perfis de documento: `auto`, `math_heavy`, `diagram_heavy`, `scanned`
- Modos Datalab: `fast`, `balanced`, `accurate`

Perfis são gerenciáveis em **Gerenciar Matérias → Gerenciar perfis** e podem ser definidos por matéria e sobrescritos por entry.

---

## Cronograma e Mapeamento Automático

### Importação do cronograma (PUCRS)

O app converte a tabela de aulas do portal acadêmico da PUCRS (ASPNET, tabela `dgAulas`) diretamente em markdown estruturado:

1. Portal → matéria → **Cronograma de Aulas** → DevTools (`F12`)
2. Copiar o `outerHTML` da `<table id="dgAulas">`
3. No app: **Importar Cronograma (HTML)** → colar → **Importar para Markdown**

O parser reconhece automaticamente suspensões (linha vermelha → `{kind=suspension} ⊘`), feriados (amarela), provas (azul → `{kind=exam}`) e recursos de sala (`@Laboratório…`). Dias marcados com `⊘` são ignorados no mapeamento de arquivos.

> Outras instituições: o app funciona normalmente, mas o campo **Cronograma** da matéria é preenchido manualmente. Para adaptar o parser: `src/utils/helpers.py` → `parse_html_schedule()`.

### Classificação de blocos

O índice do cronograma (`course/.timeline_index.json`) classifica cada bloco como aula, avaliação, revisão, feriado ou reservado, com regras como:

- Sessões de revisão só permanecem como REVIEW se **precedem uma avaliação**; revisões de conteúdo no meio do semestre viram aula normal e herdam a unidade vizinha.
- Avaliações ganham **escopo automático**: as unidades cobertas são derivadas da janela cronológica desde a última avaliação.
- Overrides manuais (tipo, unidade, tópico) são preservados entre rebuilds.

### Scoring e aprendizado

O mapeamento arquivo→unidade/bloco usa precedência **manual → card Moodle → léxico → conteúdo**, com confiança relativa (margem entre o vencedor e o segundo colocado, threshold de aceite ≥ 0.65 e não-ambíguo). Correções manuais alimentam `course/.tag_profile.json` — boosts por matéria que reduzem erros recorrentes. O perfil é isolado por matéria e os tooltips da UI mostram as razões de cada sugestão.

### Aba Cronograma

Visualização da alocação por bloco: accordion com data/título, badges de confiança, marcador `✎` para overrides, seção de não-mapeados e **reatribuição manual via dropdown** (grava `manual_timeline_block_id` no manifest na hora; o botão 🔄 Reprocessar aplica nos artefatos).

---

## Importação Moodle / M365

Pelo diálogo **Aluno → Conectar e escolher cursos**:

- Login no Moodle institucional (a senha nunca é persistida — apenas o token de sessão)
- Seleção de cursos com download automático de PDFs
- Suporte a arquivos hospedados no **OneDrive/M365** via device-code flow
- Cards do Moodle viram evidência de mapeamento (`source_section`), usada na atribuição de bloco

---

## Curadoria

| Ferramenta | Função |
|---|---|
| **Backlog (aba)** | Editar entries já processados: título, categoria, tags, unidade/subunidade manual. Mostra valores automáticos, sugestões de baixa confiança e a seção de origem do Moodle |
| **Curator Studio** | Revisão de extrações difíceis em `manual-review/`: preview do PDF com zoom, comparação base × avançada × template, editor markdown, aprovar/reprovar |
| **Image Curator** | Curadoria de imagens extraídas (ver abaixo) |
| **Códigos (aba)** | Gerenciar `code_curation.json`: gerar resumos Gemini, editar, atribuir aula |
| **Manutenção (aba)** | Detectar e limpar resíduos: curadorias órfãs, sidecars desatualizados |
| **Student State Curator** | Importar registro de sessão do tutor e atualizar progresso por tópico em `student/batteries/` |

---

## Image Curator e Vision

Opera sobre as imagens extraídas dos PDFs: agrupamento por página, preview do PDF, captura manual de regiões, classificação heurística (diagrama, tabela, fórmula, código, decorativa…), descrição acadêmica e extração de texto+matemática em Markdown/LaTeX.

Dois modos, controlados por `Fonte de descrição de imagens` nas Configurações:

- **Ollama** (padrão): vision local descreve cada imagem sob demanda (`qwen3-vl` recomendado)
- **Datalab**: descrições vêm das captions extraídas durante o processamento do PDF — sem custo adicional de vision

```powershell
ollama serve
ollama pull qwen3-vl:8b            # local
ollama pull qwen3-vl:235b-cloud    # cloud via Ollama
```

Validação: **Status → Vision → Validar Vision**.

---

## Resumos via Gemini (opcional)

Com `pip install google-genai` e uma chave em **Configurações → Gemini**, o app enriquece:

- **Código**: título inferido, linguagem, papel pedagógico, conceitos, resumo e vinculação automática ao bloco do cronograma — persistido em `course/code_curation.json` com cache por hash (re-executar sem mudanças = 0 chamadas)
- **Referências bibliográficas**: conceitos e relevância por unidade — `course/.reference_curation.json`

Aparece no cabeçalho de cada código, no `CODE_INDEX.md` agrupado por aula, no `CRONOGRAMA_DETALHADO.md` e no `CODE_HEALTH.md` (cobertura e órfãos). Custo típico: ~$0.03 por matéria com `gemini-2.5-flash`. Sem chave, tudo funciona com fallback byte-equal.

---

## Arquitetura Low-Token

Os artefatos são desenhados para **baixo custo de contexto** em LLMs web (map-first):

1. Começar por `course/COURSE_MAP.md` (mapa pedagógico curto)
2. Consultar `student/STUDENT_STATE.md` para calibrar profundidade
3. Usar `course/FILE_MAP.md` como índice de roteamento
4. Abrir markdowns longos só quando os artefatos curtos não bastarem

Descrições de imagem são injetadas de forma compacta e `bundle.seed.json` fica seletivo, focado em metadados de alto sinal.

---

## Repositório Gerado

```text
{repo-root}/
├── manifest.json        # índice master de entries
├── course/              # COURSE_MAP, FILE_MAP, GLOSSARY, CRONOGRAMA_DETALHADO,
│                        # índices internos (.timeline_index, .tag_profile, code_curation…)
├── content/             # markdown consolidado + images/
├── code/                # códigos com resumos, agrupados por origem
├── exercises/ exams/    # índices e materiais por categoria
├── assignments/
├── student/             # STUDENT_STATE, perfil, batteries por unidade
├── setup/               # instruções prontas para Claude, GPT e Gemini
├── system/              # política do tutor, pedagogia, modos
├── build/               # BUILD_REPORT, bundles, guias de curadoria
├── manual-review/       # revisão humana guiada
├── staging/             # saídas intermediárias dos backends
└── raw/                 # cópias dos arquivos originais
```

---

## Configuração

### `.env` (raiz do projeto)

```env
DATALAB_API_KEY=                          # necessária para o backend datalab
DATALAB_BASE_URL=https://www.datalab.to
```

### Configuração persistida do app

`~/.gpt_tutor_config.json` — gerenciada pela UI (Configurações). Campos relevantes: tema, modo/OCR/backend padrão, perfis de processamento, `skip_base_backends`, timeouts e opções do Marker, vision (`vision_model`, `ollama_base_url`, `image_description_source`), Gemini (`gemini_api_key`, `gemini_model`, `gemini_auto_summarize`), `prevent_sleep_during_build`.

Configuração **por matéria** (modo, backend, OCR, perfil, pastas) vive no gerenciador de matérias e tem precedência sobre o padrão global.

### PATH

| Executável | Obrigatório | Função |
|---|---|---|
| `python` | sim | rodar o app |
| `ollama` | para vision local | descrições de imagem |
| `tesseract` | não | OCR local |
| `docling` / `marker_single` | não | backends PDF locais avançados |

Se a autodetecção do Tesseract falhar:

```powershell
[Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", "C:\Program Files\Tesseract-OCR\tessdata", "User")
```

---

## Testes

```powershell
pytest tests -q          # suíte completa (1.100+ testes)
```

---

## Roadmap

Roadmap completo em [`ROADMAP.md`](ROADMAP.md). Próximos focos:

| Tema | Descrição |
|---|---|
| **Cronograma editável** | Tabela com edição inline de tipo/unidade e escopo manual de avaliações (spec em `docs/superpowers/specs/`) |
| **Tutor proativo** | Contexto de "semana atual" nas instruções, prontidão pré-prova (escopo × progresso do aluno) |
| **Desempenho** | Paralelização de chunks do Datalab, retry com backoff nas integrações |
| **Novos destinos** | Export NotebookLM além de Claude/GPT/Gemini |

---

## Licença

MIT
