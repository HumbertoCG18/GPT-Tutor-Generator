# Claude Code Handoff

Você está assumindo o projeto GPT-Tutor-Generator no seguinte estado local:

Repo:
- `C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator`

Objetivo geral recente:
- melhorar robustez do pipeline de processamento
- separar melhor texto/LaTeX de extração de imagens
- consolidar perfis de documento
- tornar a fila/backlog/curadoria mais consistentes
- experimentar Docling Python API para PDFs matemáticos
- integrar Marker com Ollama de forma opcional e rastreável

## Resumo arquitetural atual

### 1. Perfis de documento foram consolidados para apenas:
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
- backend avançado pode ser `docling`, `docling_python` ou `marker`
- seleção automática depende do perfil efetivo
- `preferred_backend` manual continua respeitado

### 3. Regra atual de seleção automática
- `math_heavy`: prioriza `marker` ou `docling`
- `diagram_heavy`: prioriza `docling` ou `marker`
- `scanned`: também ativa backend avançado
- `auto`/documento comum: tende a ficar só com backend base

### 4. Marker agora é tratado principalmente como backend de markdown/LaTeX
- extração de imagens não depende mais só do markdown do Marker
- existe trilha paralela para imagens baseada em PyMuPDF/manifest/fontes de imagem

## Mudanças grandes já implementadas

### A. Resiliência do Marker e timeout
- marker chunking agora tem modo configurável:
  - `off`
  - `fallback`
  - `always`
- default atual: `fallback`
- comportamento:
  - tenta inteiro primeiro
  - só entra em chunks se houver stall timeout real
- chunk size:
  - 10 páginas para workloads pesados
  - 20 para os demais
- timeout do Marker escala por workload
- logs do Marker ficaram mais explícitos sobre:
  - stall timeout efetivo
  - chunking mode
  - fase detectada
  - fase concluída sem itens, como `Detecting bboxes: 0it`

Arquivos:
- `src/builder/engine.py`
- `src/ui/theme.py`
- `src/ui/dialogs.py`
- `tests/test_core.py`

### B. Marker + Ollama
- integração opcional via config:
  - `marker_use_llm`
  - `marker_llm_model`
  - `ollama_base_url`
- Marker não herda mais `vision_model`
- se `marker_use_llm=true` mas `marker_llm_model` estiver vazio, o LLM do Marker é pulado
- flags suportadas atualmente:
  - `--use_llm`
  - `--llm_service`
  - `--OllamaService_ollama_base_url`
  - `--OllamaService_ollama_model`
  - `--redo_inline_math`
- Marker não usa mais language flag
- capability detection foi tornada mais tolerante:
  - ajuda por `--help` ainda existe, mas não deve mais bloquear o uso das flags reais
- `marker-run.json` agora registra bloco `llm` com:
  - `enabled`
  - `service`
  - `model`
  - `base_url`
  - `redo_inline_math`

Arquivos:
- `src/builder/engine.py`
- `src/utils/helpers.py`
- `src/ui/theme.py`
- `src/ui/dialogs.py`
- `src/ui/app.py`
- `tests/test_core.py`

Constante importante:
- `MARKER_OLLAMA_SERVICE = marker.services.ollama.OllamaService`

### C. Patch local no Marker instalado na `.venv`
Foi aplicado patch direto em:
- `.venv/Lib/site-packages/marker/services/ollama.py`

Esse patch local faz 3 coisas:
1. `flatten_schema`
- resolve `$defs / $ref` antes de enviar `format` para o Ollama
- corrige casos de `invalid JSON schema in format`

2. fallback `response -> thinking`
- corrige casos em que modelos como `qwen3-vl` devolvem conteúdo em `thinking`

3. extração de JSON embutido em texto
- tenta recuperar JSON mesmo quando o modelo devolve texto com JSON dentro

Importante:
- isso está fora do repo versionado
- se a `.venv` for recriada ou o pacote Marker for reinstalado, esse patch pode ser perdido

### D. Extração de imagens paralela ao Marker
- houve mudança para pipeline paralela de imagem
- a ideia é:
  - Marker cuida de markdown/LaTeX
  - extração de imagens é trilha separada
- políticas de extração por perfil foram melhoradas
- imagens válidas em `math_heavy`/`scanned`/`diagram_heavy` são preservadas com mais recall
- paths/fontes de imagem foram unificados para a UI

Arquivos:
- `src/builder/engine.py`
- `src/ui/dialogs.py`
- `src/ui/image_curator.py`
- `tests/test_core.py`
- `tests/test_image_curation.py`

### E. Injeção de descrição de imagem
- corrigido problema em que imagens não-`scanned` perdiam descrição porque o nome mudava após rewrite para `content/images`
- injeção agora resolve aliases do nome da imagem
- stale description blocks também foram corrigidos
- arquivos antigos precisam ser reprocessados/reinjetados para refletir isso

Arquivos:
- `src/builder/engine.py`
- `tests/test_image_curation.py`

### F. Queue/backlog/manifests
- fila ativa agora é reconciliada com `manifest.json`
- item processado some da fila mesmo durante processamento
- backlog distingue:
  - `Processado (só staging)`
  - `Processado (sem markdown)`
  - `Curado/final`
  - `Aprovado/final`
- sessão retomada usa manifest como fonte de verdade
- dashboard mostra fila remanescente real, não snapshot bruto

Arquivos:
- `src/ui/app.py`
- `src/ui/repo_dashboard.py`
- `src/ui/dialogs.py`
- `src/builder/engine.py`
- `tests/test_core.py`
- `tests/test_repo_dashboard.py`

### G. Sleep prevention
- build/processamento pode impedir suspensão do Windows
- config:
  - `prevent_sleep_during_build = true` por padrão

Arquivos:
- `src/utils/power.py`
- `src/ui/theme.py`
- `src/ui/dialogs.py`
- `src/ui/app.py`
- `src/builder/engine.py`
- `tests/test_power_management.py`
- `tests/test_core.py`

### H. Curator Studio e Image Curator

Curator Studio:
- agora ignora `manual-review` que não pertence ao fluxo de curadoria
- URL fetcher foi movido para `manual-review/web`
- reviews legados de URL em `manual-review/pdfs` são migrados para `manual-review/web`
- zoom do PDF foi implementado
- preview de PDF grande foi limitado para não travar tanto
- loading parcial/truncado foi tratado
- recorte de região no preview foi implementado
- recorte salva em `content/images/manual-crops/`
- recorte pode ser inserido no markdown atual com caminho relativo correto

Image Curator:
- resolução do PDF da entry ficou determinística
- não depende mais de `rglob` amplo
- usa `raw_target/source_path` corretos

Arquivos:
- `src/ui/curator_studio.py`
- `src/ui/image_curator.py`
- `src/ui/dialogs.py`
- `src/builder/engine.py`
- `tests/test_image_curation.py`
- `tests/test_ui_queue_dashboard.py`
- `tests/test_repo_dashboard.py`

### I. URL Fetcher
- manual review de URL agora vai para:
  - `manual-review/web`
- não deve mais poluir `manual-review/pdfs` nem Curator Studio
- migração de legados já existe

Arquivos:
- `src/builder/engine.py`
- `src/ui/curator_studio.py`
- `tests/test_core.py`

### J. Encoding/sanitização
- houve limpeza de vários textos de UI e conteúdo gerado
- backend do Marker passou a sanitizar markdown externo para tentar reparar mojibake comum
- vários testes de encoding/strings foram atualizados

Arquivos:
- `src/builder/engine.py`
- `src/ui/dialogs.py`
- `tests/test_core.py`
- `tests/test_file_map_unit_mapping.py`

### K. Backend experimental `docling_python`
- foi implementado backend novo:
  - `docling_python`
- usa API Python do Docling
- instalado na `.venv` com `pip install docling`
- atualmente:
  - usa formula enrichment para `math_heavy`/`formula_priority`
  - respeita `page_range` recortando PDF antes da conversão
  - grava `docling-python-run.json`
- standard GPU foi ligado:
  - `ThreadedPdfPipelineOptions`
  - `AcceleratorOptions(device=CUDA)`
  - `RapidOcrOptions(backend="torch")`
  - `ocr_batch_size=8`
  - `layout_batch_size=8`
  - `table_batch_size=4`
  - `settings.perf.page_batch_size >= 8`
- o metadata grava `gpu_standard` com a configuração efetiva

Importante:
- `docling_python` Standard GPU está ativo
- VLM pipeline com Ollama ainda **não** foi implementado no Docling
- Ollama no projeto hoje está só no Marker, não no Docling

Arquivos:
- `src/builder/engine.py`
- `src/utils/helpers.py`
- `src/ui/dialogs.py`
- `tests/test_core.py`

## Problemas atuais / dores em aberto

### 1. Marker + Ollama ainda é instável com alguns modelos
Problemas observados:
- `qwen3-vl:235b-cloud`
  - `500 Internal Server Error` no `/api/generate`
  - pseudo-JSON
  - response vazia
  - conteúdo inconsistente
- `gemma4:e4b`
  - melhor velocidade
  - pior precisão
  - em alguns casos gerou blocos ````html` para matemática
- `llama3.1`
  - inadequado para esse fluxo
  - não vision / ruim para structured multimodal output

Hipóteses:
- incompatibilidade do modelo com o contrato rígido do Marker
- backend cloud do Ollama menos previsível
- JSON schema/output estruturado ainda frágil mesmo com patch
- etapas de `LLM processors` podem ficar silenciosas por longos períodos

### 2. Stall timeout ainda pode matar processo saudável
Cenário:
- Marker ou Docling podem continuar trabalhando internamente sem emitir nova linha por tempo demais
- watchdog do app mata por silêncio em `stdout/stderr`
- isso afeta especialmente:
  - Marker com LLM ativo
  - Docling com VLM/transformers pesado

Hipóteses:
- processo não está travado de verdade, só silencioso
- modelo/backend fica muito tempo em uma única inferência
- cloud/local model responde lentamente ou com gargalo de VRAM

### 3. Force OCR no Marker
- quando LLM é desligado e `force_ocr` é ativado, o resultado geral de matemática ficou melhor
- porém acentos pioram
- causa provável:
  - Marker atual não expõe mais language flag pública
  - OCR reinterpreta texto que antes já existia no PDF

### 4. Docling Python ainda precisa observação real
Estado atual:
- `page_range` já foi corrigido
- Standard GPU já foi ligado
- profiling recente do `standard_pdf_pipeline` parece bom
- VLM/Ollama para Docling não foi implementado ainda

### 5. Alguns artefatos antigos podem não refletir o código novo
- `marker-run.json` antigos podem não ter bloco `llm` novo
- antigos ainda podem mencionar `language_flag`
- markdowns antigos não recebem fixes novos até reprocessar

## Bugs conhecidos do sistema

Esta seção separa:
- bugs ainda ativos / relevantes
- sintomas visíveis ao usuário
- problemas mais internos/não visíveis
- regressões históricas já corrigidas, porque elas podem reaparecer

### A. Bugs ativos ou parcialmente ativos

#### 1. Marker + Ollama ainda não é confiável com certos modelos
Visibilidade:
- parcialmente visível
- aparece em logs e, às vezes, como piora de qualidade no markdown final

Sintomas já observados:
- `Ollama inference failed: Expecting value: line 1 column 1 (char 0)`
- `Expecting property name enclosed in double quotes`
- `Extra data`
- `500 Server Error: Internal Server Error for url: http://localhost:11434/api/generate`
- processamento continua em alguns casos, mas com qualidade degradada

Causas prováveis:
- resposta do modelo fora do JSON estrito esperado pelo Marker
- incompatibilidade parcial do modelo com o contrato structured multimodal do Marker
- instabilidade de variantes cloud, especialmente `qwen3-vl:235b-cloud`
- limitações upstream do Marker + Ollama

#### 2. Stall timeout ainda pode abortar processos saudáveis
Visibilidade:
- visível no log
- às vezes percebido pelo usuário como “travou”

Sintomas já observados:
- Marker ou Docling são mortos por “Sem output por Xs”
- isso pode acontecer mesmo quando o processo estava avançando internamente

Causas prováveis:
- watchdog baseado em silêncio de `stdout/stderr`
- fases longas e silenciosas em:
  - `LLM processors`
  - VLM/transformers do Docling
- suspensão do Windows ou atraso do modelo/backend

#### 3. `force_ocr` no Marker melhora matemática, mas piora acentuação
Visibilidade:
- visível no markdown final

Sintomas:
- fórmulas/estrutura podem ficar melhores
- acentos em português podem ser perdidos ou degradados

Causa provável:
- a CLI atual do Marker não expõe mais language flag de OCR
- OCR substitui texto digital correto por texto refeito via OCR

#### 4. `docling_python` ainda é experimental
Visibilidade:
- parcialmente visível
- performance, qualidade e comportamento ainda precisam ser avaliados em PDFs reais

Estado:
- page_range já foi corrigido
- Standard GPU já foi ligado
- VLM remoto via Ollama ainda não foi implementado

Risco:
- mudanças no pacote Docling ou no ambiente Python podem alterar comportamento/performance

### B. Problemas visíveis ao usuário que já aconteceram e precisam ficar em memória

Estes problemas já foram relatados pelo usuário e corrigidos, mas são importantes para futuras investigações e para detectar regressão.

#### 1. Descrições de imagem repetidas muitas vezes no markdown
Sintoma:
- múltiplos blocos `[Descrição de imagem]` repetidos para a mesma imagem

Raiz identificada:
- stale blocks não eram removidos corretamente em alguns casos
- reinjeção acumulava descrições antigas

Estado:
- corrigido
- risco de regressão existe se a lógica de limpeza/injeção mudar novamente

#### 2. Descrições de imagem só eram injetadas corretamente em `scanned`
Sintoma:
- em outros perfis aparecia apenas o caminho da imagem

Raiz identificada:
- o nome da imagem mudava após rewrite para `content/images`
- o lookup da curadoria usava nome original

Estado:
- corrigido com resolução por aliases

#### 3. Curator Studio mostrava itens errados
Sintomas:
- `manual-review/code` aparecia como se fosse item do Curator Studio
- URL fetcher aparecia como `pdfs/titulo-da-pagina`

Raiz identificada:
- filtros de `manual-review` estavam amplos demais
- URL review legado estava indo para `manual-review/pdfs`

Estado:
- corrigido
- hoje URL review correto vai para `manual-review/web`

#### 4. Curator Studio travava em markdown/PDF grande
Sintoma:
- ao abrir arquivo grande, o Curator Studio congelava ou ficava impraticável

Raiz identificada:
- carregamento integral do markdown
- preview de PDF renderizando demais

Estado:
- mitigado com preview limitado, loading parcial e bloqueio de save/approve quando a fonte foi truncada
- ainda é um ponto sensível para arquivos grandes

#### 5. Seletor de perfil da fila sumiu da UI
Sintoma:
- a legenda aparecia, mas o combobox não

Raiz identificada:
- regressão de layout/grid no diálogo de edição de item

Estado:
- corrigido

#### 6. Zoom do PDF no Curator Studio não funcionava
Estado:
- corrigido

#### 7. Recorte de região no Curator Studio não existia
Estado:
- implementado

#### 8. Fila/backlog não diminuíam visualmente
Sintoma:
- entries já processadas continuavam parecendo “na fila”

Raiz identificada:
- contagem e snapshot não eram reconciliados com `manifest.json`

Estado:
- corrigido

#### 9. Botão de processar uma única entry gerava erro de layout Tkinter
Sintoma:
- erro envolvendo `pack`/`grid` do botão de pause

Estado:
- corrigido

### C. Problemas internos / não visíveis diretamente

#### 1. Patch local fora do repo
Existe uma dependência crítica não versionada:
- `.venv/Lib/site-packages/marker/services/ollama.py`

Isso é perigoso porque:
- o comportamento pode mudar se a `.venv` for recriada
- alguém pode olhar o repo e não entender por que localmente “funciona diferente”

#### 2. `marker-run.json` e outros artefatos podem ser antigos
Impacto:
- a inspeção de um artefato antigo pode sugerir configuração errada mesmo quando o código atual já mudou

Exemplo:
- presença de `language_flag`
- ausência do bloco `llm`

#### 3. Mistura entre bugs do app e bugs upstream
O projeto hoje depende de comportamento externo de:
- Marker
- Docling
- Ollama

Então alguns erros vistos pelo usuário não são necessariamente bugs do app local, mas o app precisa tratá-los bem:
- respostas não-JSON
- schema rejeitado pelo Ollama
- cloud model instável
- inferência silenciosa longa

### D. Regressões históricas importantes já corrigidas

Se alguma reaparecer, tratar como regressão confirmada:

- repetição massiva de descrição de imagem
- injeção de descrição falhando fora de `scanned`
- Curator Studio carregando `manual-review/code`
- URL fetcher aparecendo como PDF no manual review
- Curator Studio abrindo PDF errado da entry
- Curator Studio sem zoom
- Curator Studio sem recorte de região
- selector de perfil desaparecendo na fila
- contagem de fila/backlog desatualizada
- `docling_python` ignorando `page_range` e processando o documento inteiro
- `marker_use_llm` sendo desativado por falso negativo de capability detection
- backend do Marker ainda tentando usar language flag removida

### E. O que é bug visível vs não visível, na prática

#### Visível para o usuário
- markdown com acentuação ruim
- LaTeX ruim ou em formato incorreto
- descrição de imagem faltando ou duplicada
- arquivo errado no Curator Studio/Image Curator
- fila/backlog com números incorretos
- Curator Studio travando ou ficando impraticável
- seletor/controles sumindo da UI

#### Não visível diretamente, mas crítico
- timeout falso por silêncio de log
- capability detection errada do Marker
- patch local na `.venv` sendo perdido
- `manual-review`/`manifest` inconsistentes internamente
- backend experimental processando documento inteiro sem respeitar `page_range`
- modelo Ollama respondendo pseudo-JSON e degradando silenciosamente o pipeline

## Hardware / ambiente conhecido
- notebook com RTX 4050 6 GB VRAM
- recomendação anterior para modelos Ollama locais:
  - melhor aposta: `qwen3-vl:8b` com quantização `q4_K_M`
  - fallback leve: `qwen3-vl:4b`
- `qwen3-vl:235b-cloud` foi problemático

## Validações já feitas
- muitos testes focados foram adicionados e passaram
- recentemente:
  - pytest focado em `docling_python` / GPU / `page_range` passou
  - `compileall` passou
- houve também uma rodada anterior em que a suíte completa passou, mas desde então o código continuou mudando
- não assumir que toda a suíte foi rerodada depois das mudanças mais recentes sem checar

## Planos criados no repo
- `docs/superpowers/plans/2026-04-07-marker-latex-and-parallel-image-pipeline.md`
- `docs/superpowers/plans/2026-04-08-document-profile-consolidation.md`

## Arquivos mais importantes para orientar futuras mudanças
- `src/builder/engine.py`
- `src/utils/helpers.py`
- `src/ui/dialogs.py`
- `src/ui/app.py`
- `src/ui/curator_studio.py`
- `src/ui/image_curator.py`
- `src/ui/repo_dashboard.py`
- `src/models/core.py`
- `tests/test_core.py`
- `tests/test_image_curation.py`
- `tests/test_repo_dashboard.py`
- `tests/test_ui_queue_dashboard.py`

## O que eu quero que você faça a partir daqui
1. Entenda esse estado atual como baseline.
2. Não reverta mudanças recentes sem confirmar intenção.
3. Considere que existe patch local fora do repo em:
- `.venv/Lib/site-packages/marker/services/ollama.py`
4. Se for investigar Marker + Ollama, trate os problemas como:
- parcialmente upstream
- parcialmente específicos do modelo usado
- não apenas “flag mal configurada”
5. Se for mexer em Docling:
- preserve o Standard GPU recém-adicionado
- não confundir com VLM pipeline via Ollama
- se implementar VLM do Docling, faça como etapa separada
6. Se for mexer em fila/backlog/curadoria:
- mantenha manifest como fonte de verdade
- não trate “processado” como “curado/aprovado”

## Estado desejado no curto prazo
- avaliar se `docling_python` Standard GPU dá resultado melhor para `math_heavy`
- eventualmente testar um VLM pipeline do Docling separado do Marker
- continuar melhorando qualidade matemática sem sacrificar tanto acentuação
- reduzir falsos stall timeouts em fases silenciosas

## Prioridade de investigação

### Prioridade 1: qualidade matemática útil em PDFs reais
Foco:
- comparar `marker` sem LLM + `force_ocr`
- comparar `marker` com LLM em modelos viáveis
- comparar `docling_python` Standard GPU em `math_heavy`

Objetivo:
- descobrir qual pipeline entrega melhor equilíbrio entre:
  - LaTeX
  - acentuação
  - tabelas
  - velocidade

### Prioridade 2: reduzir falsos travamentos
Foco:
- revisar watchdog por silêncio
- considerar timeout adaptativo por fase
- observar especialmente:
  - `LLM processors` do Marker
  - VLM/transformers do Docling

Objetivo:
- não matar processo saudável só porque a fase atual ficou silenciosa

### Prioridade 3: decidir estratégia definitiva para LLM no Marker
Foco:
- validar se existe algum modelo Ollama realmente estável para o Marker nesse hardware
- avaliar se vale insistir em `qwen3-vl`
- decidir se o patch local do Marker é solução temporária ou se deve virar processo formal

Objetivo:
- parar de gastar tempo em combinações claramente incompatíveis

### Prioridade 4: avaliar se o Docling deve ganhar VLM pipeline separado
Foco:
- só depois de validar o Standard GPU
- não misturar essa etapa com o pipeline atual do Marker

Objetivo:
- testar VLM/Ollama no Docling como experimento controlado, não como mudança implícita

### Prioridade 5: monitorar regressões de UI/curadoria
Foco:
- Curator Studio
- Image Curator
- backlog/fila/manifest

Objetivo:
- garantir que bugs já corrigidos não reapareçam durante novas mudanças no pipeline
