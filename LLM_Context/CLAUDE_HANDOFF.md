# Claude Code Handoff

Voce esta assumindo o projeto GPT-Tutor-Generator no seguinte estado local:

Repo:
- `C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator`

Working tree no momento deste handoff:
- ha mudancas locais nao commitadas em:
  - `src/builder/datalab_client.py`
  - `src/builder/engine.py`
  - `src/ui/app.py`
  - `src/ui/curator_studio.py`
  - `tests/test_core.py`
  - `tests/test_image_curation.py`

Objetivo geral recente:
- melhorar robustez do pipeline de processamento
- separar markdown/LaTeX de extracao de imagens
- consolidar perfis de documento
- tornar fila/backlog/curadoria mais consistentes
- integrar o backend cloud do Datalab para PDFs complexos
- manter Marker como opcao de LaTeX, mas sem depender dele para imagens

## Resumo arquitetural atual

### 1. Perfis de documento consolidados
Perfis ativos:
- `auto`
- `math_heavy`
- `diagram_heavy`
- `scanned`

Compatibilidade legada:
- `general -> auto`
- `math_light -> math_heavy`
- `layout_heavy -> diagram_heavy`
- `exam_pdf -> diagram_heavy`

Arquivos principais:
- `src/utils/helpers.py`
- `src/models/core.py`
- `src/builder/engine.py`
- `src/ui/dialogs.py`

### 2. Pipeline geral de PDF
- backend base continua sendo `pymupdf4llm` ou `pymupdf`
- backend avancado pode ser `datalab`, `docling`, `docling_python` ou `marker`
- `preferred_backend` manual continua respeitado
- selecao automatica depende do perfil efetivo e dos backends disponiveis

### 3. Regra atual de selecao automatica
Estado real do codigo hoje:
- `math_heavy`: prioriza `datalab`, depois `marker`, depois `docling`
- `diagram_heavy`: prioriza `docling`, depois `marker`
- `scanned`: prioriza backends avancados locais (`docling`/`marker`)
- `auto` e perfis comuns: tende a ficar so com backend base

Arquivo principal:
- `src/builder/engine.py`

### 4. Estrategia atual para imagens
- a extracao de imagens nao deve depender exclusivamente do markdown do Marker
- a curadoria de imagens e feita app-side
- o objetivo atual e:
  - backend avancado cuida de markdown/LaTeX
  - imagens entram por pipeline propria e Image Curator

### 5. Fonte de verdade operacional
- `manifest.json` e a fonte de verdade para entries processadas
- fila, backlog, dashboard e retomada de sessao devem ser reconciliados com o manifest
- "processado" nao significa "curado" nem "aprovado"

## Mudancas grandes ja implementadas

### A. Marker: chunking, timeout e LLM opcional
- marker chunking tem modo configuravel:
  - `off`
  - `fallback`
  - `always`
- default atual: `fallback`
- comportamento:
  - tenta documento inteiro primeiro
  - so entra em chunks se houver timeout/stall real
- chunk size:
  - 10 paginas para workloads pesados
  - 20 paginas para os demais
- timeout e logs do Marker ficaram mais explicitos

Configuracao importante:
- `marker_use_llm`
- `marker_llm_model`
- `marker_chunking_mode`
- `ollama_base_url`
- `marker_torch_device`

Arquivos:
- `src/builder/engine.py`
- `src/ui/theme.py`
- `src/ui/dialogs.py`
- `tests/test_core.py`

### B. Marker + Ollama
- integracao opcional via configuracao
- Marker nao herda mais `vision_model`
- se `marker_use_llm=true` mas `marker_llm_model` estiver vazio, o LLM do Marker e pulado
- flags relevantes suportadas hoje:
  - `--use_llm`
  - `--llm_service`
  - `--OllamaService_ollama_base_url`
  - `--OllamaService_ollama_model`
  - `--redo_inline_math`
- Marker nao usa mais language flag de OCR
- `marker-run.json` registra metadados de LLM quando aplicavel

Constante importante:
- `MARKER_OLLAMA_SERVICE = marker.services.ollama.OllamaService`

Arquivos:
- `src/builder/engine.py`
- `src/utils/helpers.py`
- `src/ui/theme.py`
- `src/ui/dialogs.py`
- `src/ui/app.py`
- `tests/test_core.py`

### C. Patch local no Marker instalado na `.venv`
Foi aplicado patch direto em:
- `.venv/Lib/site-packages/marker/services/ollama.py`

Esse patch local faz:
1. `flatten_schema`
- resolve `$defs / $ref` antes de enviar `format` para o Ollama
- corrige `invalid JSON schema in format`

2. fallback `response -> thinking`
- ajuda com modelos que devolvem conteudo em `thinking`

3. tentativa de recuperar JSON embutido em texto

Importante:
- isso esta fora do repo versionado
- se a `.venv` for recriada, esse patch pode ser perdido

### D. Backend Datalab integrado
O Datalab hoje e uma parte central da arquitetura para PDFs complexos, especialmente `math_heavy`.

Estado atual:
- backend avancado `datalab` implementado
- `math_heavy` pode preferir `datalab` automaticamente quando a API key existe
- tambem e possivel escolher `preferred_backend = datalab` manualmente por entry
- quando `datalab` e selecionado para um PDF, o dialogo da entry mostra seletor `Modelo` com:
  - `fast`
  - `balanced`
  - `accurate`

Comportamento importante:
- o app envia:
  - `disable_image_extraction = true`
  - `disable_image_captions = true`
- ou seja:
  - o Datalab hoje cuida da conversao para markdown
  - imagens e descricoes sinteticas do Datalab foram desativadas intencionalmente
  - a curadoria de imagens permanece app-side

Artefatos gerados:
- `staging/markdown-auto/datalab/<entry>/`
- `datalab-run.json`

Arquivos:
- `src/builder/datalab_client.py`
- `src/builder/engine.py`
- `src/ui/dialogs.py`
- `src/ui/app.py`
- `README.md`
- `tests/test_core.py`

### E. Datalab para documentos longos
Foi implementada politica especifica para documentos longos no backend Datalab.

Estado atual:
- existe logica de chunking para documentos longos
- `math_heavy` usa chunk size de 20 paginas
- documentos pequenos ou faixas pequenas selecionadas usam execucao unica
- chunks sao consolidados em markdown final unico
- `datalab-run.json` grava:
  - `chunked`
  - `chunk_size`
  - lista de `chunks`

Importante:
- isso foi feito para reduzir risco/custo em PDFs grandes sem quebrar a saida final
- ainda assim o app trata o Datalab como pipeline de markdown, nao de imagem

Arquivos:
- `src/builder/engine.py`
- `tests/test_core.py`

### F. Extração de imagens paralela ao backend avancado
- houve mudanca estrutural para pipeline de imagem paralela
- ideia atual:
  - Marker/Datalab/Docling cuidam do markdown
  - imagens entram e sao curadas fora desse markdown
- isso reduz a dependencia da qualidade de extracao de imagem do Marker

Arquivos:
- `src/builder/engine.py`
- `src/ui/image_curator.py`
- `src/ui/dialogs.py`
- `tests/test_core.py`
- `tests/test_image_curation.py`

### G. Injeção de descricao de imagem
- corrigido problema em que imagens nao-`scanned` perdiam descricao porque o nome mudava apos rewrite para `content/images`
- injecao agora resolve aliases do nome da imagem
- stale description blocks tambem foram tratados

Arquivos:
- `src/builder/engine.py`
- `tests/test_image_curation.py`

### H. Queue / backlog / manifest / dashboard
- fila ativa agora e reconciliada contra `manifest.json`
- item processado sai da fila real quando o manifest indica que ele ja entrou como entry
- backlog diferencia melhor os estados de processamento
- dashboard usa contagem reconciliada, nao snapshot bruto
- sessao retomada usa manifest como fonte de verdade

Arquivos:
- `src/ui/app.py`
- `src/ui/repo_dashboard.py`
- `src/ui/dialogs.py`
- `src/builder/engine.py`
- `tests/test_core.py`
- `tests/test_repo_dashboard.py`

### I. Curator Studio e Image Curator

Curator Studio:
- ignora `manual-review` que nao pertence ao fluxo de curadoria
- URL fetcher foi movido para `manual-review/web`
- reviews legados de URL em `manual-review/pdfs` sao migrados para `manual-review/web`
- zoom do PDF foi implementado
- preview de PDF grande foi limitado
- loading parcial/truncado foi tratado
- recorte de regiao no preview foi implementado
- recorte salva em `content/images/manual-crops/`

Mudanca muito importante recente:
- referencias de imagem de manual crop agora sao normalizadas para caminhos repo-relative estaveis:
  - `content/images/manual-crops/...`
- antes o Curator Studio inseria caminhos relativos ao markdown atual, por exemplo:
  - `../../../content/images/manual-crops/...`
- isso quebrava quando o markdown mudava de pasta entre `staging/`, `manual-review/` e `content/curated/`
- agora:
  - `_markdown_image_reference()` prefere caminho repo-relative
  - `_normalize_repo_image_references()` reescreve referencias locais antigas ao salvar e ao aprovar

Image Curator:
- resolucao do PDF da entry ficou deterministica
- usa `raw_target/source_path`
- nao depende mais de buscas amplas e ambiguas para achar o PDF da entry

Arquivos:
- `src/ui/curator_studio.py`
- `src/ui/image_curator.py`
- `src/ui/dialogs.py`
- `src/builder/engine.py`
- `tests/test_image_curation.py`
- `tests/test_ui_queue_dashboard.py`
- `tests/test_repo_dashboard.py`

### J. URL Fetcher
- manual review de URL agora vai para:
  - `manual-review/web`
- nao deve mais poluir `manual-review/pdfs`
- Curator Studio nao deve mais tratar URL fetcher como PDF normal

Arquivos:
- `src/builder/engine.py`
- `src/ui/curator_studio.py`
- `tests/test_core.py`

### K. Sleep prevention
- build/processamento pode impedir suspensao do Windows
- config:
  - `prevent_sleep_during_build = true` por padrao

Arquivos:
- `src/utils/power.py`
- `src/ui/theme.py`
- `src/ui/dialogs.py`
- `src/ui/app.py`
- `src/builder/engine.py`
- `tests/test_power_management.py`
- `tests/test_core.py`

### L. UI: backlog e tasks de repositorio ficaram mais limpos
Mudancas recentes de UI:

Backlog:
- toolbar foi compactada
- a lista ficou mais alta por padrao
- acoes secundarias de repositorio foram agrupadas em um menu curto `Repo`
- botoes redundantes removidos do backlog:
  - `Abrir Dashboard`
  - `Enfileirar Build`
  - `Enfileirar Reprocessamento`

Tasks de Repositorio:
- acoes de enfileiramento foram agrupadas em menu:
  - `➕ Enfileirar`
- acoes de remocao/limpeza foram agrupadas em menu:
  - `🧹 Limpeza`
- acoes de execucao continuam visiveis:
  - `Executar`
  - `Pausar`
  - `Cancelar`

Arquivo principal:
- `src/ui/app.py`

## Problemas atuais / dores em aberto

### 1. Marker + Ollama continua instavel com alguns modelos
Problemas observados:
- `qwen3-vl:235b-cloud`
  - respostas pseudo-JSON
  - `500 Internal Server Error`
  - comportamento inconsistente
- `gemma4:e4b`
  - melhor velocidade
  - pior precisao matematica
  - em alguns casos gerou blocos `html` para matematica
- `llama3.1`
  - inadequado para esse fluxo

Hipoteses:
- incompatibilidade do modelo com o contrato structured output do Marker
- backend cloud do Ollama menos previsivel
- limitacoes upstream do Marker + Ollama

### 2. Stall timeout ainda pode matar processo saudavel
Cenario:
- Marker ou Docling podem continuar trabalhando internamente sem emitir log novo
- watchdog do app mata por silencio em `stdout/stderr`
- isso afeta principalmente:
  - Marker com LLM ativo
  - Docling/VLM pesado

### 3. Force OCR no Marker
- quando LLM e desligado e `force_ocr` e ativado, o resultado geral de matematica ficou melhor
- porem acentos pioram
- causa provavel:
  - o Marker atual nao expoe mais language flag publica de OCR

### 4. Docling Python continua experimental
Estado atual:
- `page_range` ja foi corrigido
- Standard GPU ja foi ligado
- VLM/Ollama para Docling nao foi implementado

Risco:
- mudancas no pacote Docling ou no ambiente Python podem alterar comportamento

### 5. Datalab tem custo e depende de rede/API externa
Estado atual:
- Datalab hoje e a opcao mais previsivel para `math_heavy`
- porem:
  - e servico pago por pagina
  - depende de API key
  - ainda precisa ser monitorado em documentos longos

Observacao importante:
- imagens/captions do Datalab estao desligadas de proposito
- se alguem vir isso como "faltando feature", precisa entender que foi uma decisao arquitetural para manter Image Curator app-side

## Bugs conhecidos do sistema

### A. Bugs ativos ou parcialmente ativos

#### 1. Marker + Ollama nao e confiavel com certos modelos
Visibilidade:
- aparece em logs
- pode degradar a qualidade do markdown final

Sintomas observados:
- `Expecting value: line 1 column 1 (char 0)`
- `Expecting property name enclosed in double quotes`
- `Extra data`
- `500 Server Error: Internal Server Error for url: http://localhost:11434/api/generate`

#### 2. Stall timeout por silencio de log
Visibilidade:
- visivel no log como "Sem output por Xs"
- as vezes o usuario percebe como travamento

#### 3. `force_ocr` melhora matematica, mas piora acentuacao
Visibilidade:
- visivel no markdown final

#### 4. `docling_python` ainda e experimental
Visibilidade:
- performance e qualidade ainda precisam de validacao em PDFs reais

### B. Problemas visiveis ao usuario que ja aconteceram e precisam ficar em memoria

Ja aconteceram e foram corrigidos, mas sao regressions importantes:

#### 1. Descricoes de imagem repetidas muitas vezes
Estado:
- corrigido

#### 2. Descricoes de imagem so funcionavam corretamente em `scanned`
Estado:
- corrigido

#### 3. Curator Studio mostrava itens errados
Sintomas historicos:
- `manual-review/code` aparecia como se fosse item do Curator Studio
- URL fetcher aparecia como PDF

Estado:
- corrigido

#### 4. Curator Studio travava em markdown/PDF grande
Estado:
- mitigado com preview limitado e loading parcial

#### 5. Seletor de perfil da fila sumiu da UI
Estado:
- corrigido

#### 6. Zoom do PDF no Curator Studio nao funcionava
Estado:
- corrigido

#### 7. Recorte de regiao no Curator Studio nao existia
Estado:
- implementado

#### 8. Manual crop gerava caminho instavel
Sintoma historico:
- recorte ia para o markdown com caminho relativo como `../../../content/images/manual-crops/...`
- depois quebrava quando o arquivo era salvo/aprovado em outra pasta

Estado:
- corrigido com normalizacao para `content/images/manual-crops/...`

#### 9. Fila/backlog nao diminuia visualmente
Estado:
- corrigido com reconciliacao via manifest

#### 10. Botao de processar uma unica entry gerava erro de layout Tkinter
Estado:
- corrigido

### C. Problemas internos / nao visiveis diretamente

#### 1. Patch local fora do repo
Dependencia critica nao versionada:
- `.venv/Lib/site-packages/marker/services/ollama.py`

#### 2. Artefatos antigos podem sugerir configuracao errada
Exemplos:
- `marker-run.json` antigo sem bloco `llm`
- artefatos antigos mencionando `language_flag`
- markdowns antigos sem normalizacao de image refs do Curator Studio

#### 3. Mistura entre bugs do app e bugs upstream
O projeto depende de:
- Marker
- Docling
- Ollama
- Datalab

Nem todo erro visto pelo usuario e bug local do app.

## Hardware / ambiente conhecido
- notebook com RTX 4050 6 GB VRAM
- recomendacao anterior para Ollama local:
  - melhor aposta: `qwen3-vl:8b` com quantizacao `q4_K_M`
  - fallback leve: `qwen3-vl:4b`
- `qwen3-vl:235b-cloud` foi problematico

## Validacoes recentes conhecidas
- `python -m pytest tests\\test_image_curation.py -q`
  - passou: `54 passed`
- `python -m py_compile src\\ui\\app.py`
  - passou

Tambem ha testes focados para:
- Datalab chunking e configuracao
- Curator Studio image refs
- queue/backlog reconciliation
- repo dashboard

Nao assumir que a suite inteira foi rerodada apos toda mudanca recente sem checar.

## Planos criados no repo
- `docs/superpowers/plans/2026-04-07-marker-latex-and-parallel-image-pipeline.md`
- `docs/superpowers/plans/2026-04-08-document-profile-consolidation.md`

## Arquivos mais importantes para orientar futuras mudancas
- `src/builder/engine.py`
- `src/builder/datalab_client.py`
- `src/utils/helpers.py`
- `src/ui/dialogs.py`
- `src/ui/app.py`
- `src/ui/curator_studio.py`
- `src/ui/image_curator.py`
- `src/ui/repo_dashboard.py`
- `src/models/core.py`
- `README.md`
- `tests/test_core.py`
- `tests/test_image_curation.py`
- `tests/test_repo_dashboard.py`
- `tests/test_ui_queue_dashboard.py`

## O que eu quero que voce faca a partir daqui
1. Entenda este estado como baseline atual do projeto.
2. Nao reverta mudancas recentes sem confirmar intencao.
3. Considere que existe patch local fora do repo em:
- `.venv/Lib/site-packages/marker/services/ollama.py`
4. Se for investigar Marker + Ollama, trate os problemas como:
- parcialmente upstream
- parcialmente especificos do modelo usado
- nao apenas "flag mal configurada"
5. Se for mexer no Datalab:
- preserve a decisao atual de deixar imagens/captions desativadas na API
- mantenha Image Curator como fluxo app-side
- preserve a politica de chunking para documentos longos, a menos que haja motivo forte para mudar
6. Se for mexer em Docling:
- preserve o Standard GPU ja adicionado
- nao confundir com VLM pipeline via Ollama
7. Se for mexer em fila/backlog/curadoria:
- mantenha manifest como fonte de verdade
- nao trate "processado" como "curado/aprovado"
8. Se for mexer no Curator Studio:
- preserve a normalizacao repo-relative de imagens locais
- cuidado para nao reintroduzir caminhos relativos instaveis

## Estado desejado no curto prazo
- continuar usando Datalab como opcao pratica para `math_heavy`
- manter Marker como opcao de LaTeX, mas sem depender dele para imagens
- continuar melhorando qualidade matematica sem sacrificar tanto acentuacao
- reduzir falsos stall timeouts em fases silenciosas
- manter backlog/tasks/fila com UI mais limpa e menos redundante

## Prioridade de investigacao

### Prioridade 1: qualidade matematica util em PDFs reais
Foco:
- comparar `datalab`
- comparar `marker` sem LLM + `force_ocr`
- comparar `marker` com LLM em modelos viaveis
- comparar `docling_python` Standard GPU em `math_heavy`

Objetivo:
- achar melhor equilibrio entre:
  - LaTeX
  - acentuacao
  - tabelas
  - velocidade

### Prioridade 2: reduzir falsos travamentos
Foco:
- revisar watchdog por silencio
- considerar timeout adaptativo por fase
- observar especialmente:
  - `LLM processors` do Marker
  - VLM/transformers do Docling

### Prioridade 3: decidir estrategia definitiva para LLM no Marker
Foco:
- validar se existe algum modelo Ollama realmente estavel para o Marker nesse hardware
- avaliar se vale insistir em `qwen3-vl`
- decidir se o patch local do Marker e so paliativo ou parte de um processo mais formal

### Prioridade 4: monitorar regressoes de curadoria e UI
Foco:
- Curator Studio
- Image Curator
- backlog/fila/manifest
- layout das toolbars e menus recentes

### Prioridade 5: avaliar evolucao futura do Datalab
Foco:
- custo por pagina
- chunking de documentos longos
- qualidade real em materiais `math_heavy`
- decidir depois se vale reativar alguma feature da API do Datalab ou manter tudo de imagem app-side
