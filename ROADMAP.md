# Roadmap

Features planejadas para o Academic Tutor Repo Builder V3.

---

## 1. Suporte ao NotebookLM / Notebooks do Gemini

Gerar um quarto destino de export além de Claude Projects, Custom GPT e Gemini
Gem: os **Notebooks** da nova seção do Gemini (NotebookLM embutido).

### Motivação

Notebooks oferecem *grounding* muito mais forte que Gems: as respostas ficam
ancoradas nas fontes com citação por trecho. Combina com as regras "nunca
invente" e "cite a fonte". Útil especialmente em modos de revisão (prova
chegando) sobre subconjuntos específicos de arquivos.

### Escopo

- Novo gerador `generate_notebooklm_instructions()` em
  `src/builder/prompt_generation.py`, adaptado ao formato de instrução custom
  do Notebook (mais raso que Gem — foco em persona + rastreabilidade, menos em
  modos de operação).
- Novo arquivo `setup/INSTRUCOES_NOTEBOOKLM.md`.
- Novo valor `"notebooklm"` em `SubjectProfile.preferred_llm` e no
  `platform_map` do engine/app.
- Empacotar um **bundle enxuto** de fontes para o Notebook:
  - Priorizar `content/curated/`, `exercises/lists/`, `exams/past-exams/`
  - Excluir `setup/`, `manifest.json`, `staging/`, `raw/`
  - Exportar em `build/notebooklm-bundle/` para upload manual.
- Suporte a **Notebook pontual por unidade** (ex.: "revisão P1"): seletor de
  unidades no app para gerar bundle restrito.

### Considerações

- Notebook não executa ciclo `ditar → git push` do STUDENT_STATE de forma
  natural. Instruções devem assumir Notebook como **leitor** e orientar o aluno
  a voltar ao Gem/Claude para atualizar estado.
- Limite de fontes por Notebook (atualmente ~50 — confirmar antes de implementar).

---

## 2. Cronograma visual com blocos temporais × arquivos

Mostrar no app, numa aba dedicada, o cronograma da disciplina como uma
timeline com os **blocos temporais** (semanas/aulas do SYLLABUS) e os
**arquivos ligados a cada bloco** ao lado.

### Motivação

Hoje o mapeamento bloco-arquivo vive espalhado entre `timeline_index.py`,
`navigation_artifacts.py` (FILE_MAP) e `manual_timeline_block_id` no backlog.
Não existe visão única. Quando o usuário suspeita de erro de mapeamento, ele
precisa abrir `course/FILE_MAP.md`, cruzar com `course/SYLLABUS.md` e adivinhar
qual `manual_timeline_block_id` usar.

### Escopo

- Nova janela `TimelineDashboard` em `src/ui/`:
  - Coluna esquerda: blocos do `timeline_index` (data, rótulo, unidade, kind)
  - Coluna direita: arquivos mapeados naquele bloco (com confiança e overrides)
  - Linhas ignoradas (`⊘` / `{kind=holiday|prova|revisao}`) visualmente atenuadas
  - Blocos sem arquivos destacados (gap de material)
  - Arquivos sem bloco atribuído listados à parte
- Drag-and-drop de arquivo → bloco para gravar `manual_timeline_block_id`
  direto no manifest (sem abrir o backlog).
- Botão "Reprocessar repositório" embutido após mudança.
- Ponto de entrada no menu `Repo → Timeline`.

### Considerações

- Reaproveitar `_build_file_map_timeline_context_from_course()` já existente
  no engine — não reinventar scoring.
- UI precisa aplicar tema via `apply_theme_to_toplevel()` (convenção da UI atual).
- Exportar o mesmo mapeamento como `course/TIMELINE_MAP.md` (artefato
  adicional lido pelo tutor) — decidir se vale a pena ou se `FILE_MAP.md`
  já basta.

---

## 3. Compatibilidade correta com Obsidian e Notion

Fazer os repositórios gerados abrirem bem em Obsidian e Notion sem perda de
estrutura, links ou imagens.

### Motivação

O aluno pode querer estudar fora do tutor LLM — abrir os markdowns curados num
segundo cérebro pessoal. Hoje a compatibilidade é parcial:

- Obsidian: links `[[wikilink]]` não são gerados; links relativos funcionam mas
  sem preview de grafo. Imagens com caminhos `content/images/manual-crops/...`
  renderizam, mas tags frontmatter poderiam virar tags clicáveis.
- Notion: não entende frontmatter YAML, não entende LaTeX `$$...$$`,
  importer quebra links relativos, imagens precisam estar numa URL acessível.

### Escopo

**Obsidian**
- Gerar (opcionalmente) `.obsidian/` com config básica recomendada (atalhos,
  plugin de grafo).
- Canonical tags frontmatter: garantir formato `tags: [tag1, tag2]` que o
  Obsidian entende.
- Adicionar links wiki-style `[[arquivo]]` ao lado dos links relativos em
  `FILE_MAP.md` e `COURSE_MAP.md` (modo dual).
- Verificar renderização do LaTeX dos curados no MathJax do Obsidian.

**Notion**
- Comando "Exportar para Notion-friendly" no menu `Repo`:
  - Converter frontmatter YAML em cabeçalho markdown (`> **Curso:** X`)
  - Substituir `$$...$$` por blocos de código com linguagem `latex`
    (Notion renderiza equações via `/equation`, então também oferecer modo
    de conversão para blocos nativos)
  - Flatten de links relativos para URLs `raw.githubusercontent.com`
  - Imagens referenciadas ficam apontando para GitHub raw
- Exportar `build/notion-import/` com a variante adaptada (não substituir o
  repo principal).

### Considerações

- Não quebrar compatibilidade com Claude/GPT/Gemini: a transformação para
  Notion deve ser **derivada**, não destrutiva.
- Verificar comportamento do Obsidian com frontmatter estendido que o app já
  escreve (`status:`, `mode:`, etc.).
- Decidir escopo do import de Notion — importer oficial vs. API.

---

## 4. Painel Student State — captura de sessão de estudo

Substituir o botão **File Map** (atualmente inutilizável) por um botão **Student State**
que abre um painel de captura de sessão, similar ao Curator Studio, onde o aluno
registra o que aprendeu durante uma aula ou sessão de estudo.

### Motivação

Dois problemas estruturais das LLMs no fluxo atual:

**Cold start** — cada sessão começa do zero. O tutor não sabe o que foi discutido ontem,
quais convenções foram acordadas, o que travou ou o que já foi bem dominado.

**Context flooding** — a compensação instintiva é empurrar tudo para o `STUDENT_STATE.md`,
inflando o contexto com informação histórica de baixa relevância atual, queimando tokens
e degradando atenção do modelo para o que realmente importa.

A solução é um arquivo de estado compacto e datado por sessão, que o tutor lê no
início de cada conversa como um "diário de bordo": sabe exatamente de onde parar,
sem reconstruir o estado a partir do zero e sem receber um dump histórico completo.

### Convenção de nomeação

```text
student/batteries/<unidade>/bloco<N>_<tema>_<DD-MM-YY>_<HH-MM>.md
```

Exemplo:

```text
student/batteries/unidade-2/bloco3_derivadas-implicitas_15-04-26_19-30.md
```

- `bloco<N>`: número sequencial dentro da unidade (incrementado automaticamente)
- `<tema>`: slug derivado do tema preenchido pelo aluno (normalizado: lowercase, hífens)
- `<DD-MM-YY>`: data da sessão (não usa `/` porque não é válido em nome de arquivo)
- `<HH-MM>`: hora de início da sessão (não usa `:` pelo mesmo motivo)

### Estrutura do arquivo gerado

```markdown
---
unidade: "2 — Derivadas"
bloco: 3
tema: "Derivadas implícitas"
data: 2026-04-15
hora: 19:30
duracao_min: 90
---

## O que eu entendi

...

## O que ainda está confuso

...

## Perguntas em aberto

...

## Próximo passo combinado com o tutor

...
```

### Fluxo de uso

1. Aluno clica em **Student State** na barra de ferramentas do app.
2. App abre painel lateral, similar ao Curator Studio, com:
   - Seletor de unidade (deriva do `COURSE_MAP`)
   - Campo de tema (texto livre → normalizado para slug)
   - Data/hora pré-preenchida com `datetime.now()`
   - Duração estimada da sessão
   - Quatro campos de texto livre (entendeu / confuso / perguntas / próximo passo)
3. Ao salvar, o app:
   - Cria o arquivo com o nome canônico em `student/batteries/<unidade>/`
   - **Não passa pelo pipeline**: nenhum processamento, nenhuma extração, nenhuma fila
   - Abre o explorador de arquivos no arquivo criado (opcional)
4. O aluno faz o commit manualmente (ou via botão "Commitar sessão" que chama `git add` + `git commit`)
5. Na próxima sessão, o tutor lê o arquivo mais recente de `student/batteries/` e retoma sem cold start

### Integração com a arquitetura atual

- **`src/ui/`**: novo `student_state_panel.py` (padrão do projeto — um arquivo por widget complexo)
- **`src/builder/artifacts/student_state.py`**: adicionar `next_bloco_number(repo_path, unit)` para resolver o incremento
- **`src/models/core.py`**: sem mudança — o arquivo de sessão é texto puro, não passa por `BackendRunResult`
- **`student/STUDENT_STATE.md`**: não é alterado pelo painel; continua sendo o estado consolidado de longo prazo
- **`RepoTaskStore`**: não envolve fila — criação síncrona e direta

### O que NÃO muda

- O `STUDENT_STATE.md` existente continua sendo o estado de longo prazo (perfil, progresso, metas)
- O fluxo de consolidação via `Repo → Consolidar unidade` continua como está
- O pipeline de build não é afetado

---

## 5. Sinalizador de data em nome de arquivo (`DD.MM nome.pdf`)

Adicionar reconhecimento do padrão `DD.MM` no início do nome do arquivo como
sinal auxiliar de mapeamento para blocos do cronograma.

### Motivação

Muitos alunos nomeiam materiais com a data da aula no início:

```text
12.03 Processos.pdf
05.05 Gerência de Memória — slides.pdf
```

O ponto (`.`) é usado como separador porque `/` não é válido em nome de arquivo no Windows.
Esse padrão já carrega a data exata da aula — informação preciosa para confirmar a qual
bloco temporal o arquivo pertence.

### Comportamento esperado

- O sinal **não substitui** o scoring por conteúdo — é um **boost** adicional
- Se a data `DD.MM` extraída do nome bate com a data de um bloco do `timeline_index`,
  o score daquele bloco sobe (ex.: +0.25 sobre o score base)
- Se não bate com nenhum bloco, o sinal é ignorado silenciosamente
- O campo `manual_timeline_block_id` continua tendo precedência absoluta

### Integração com a arquitetura atual

- **`src/builder/extraction/entry_signals.py`**: nova função `extract_date_prefix_signal(filename) -> Optional[date]`
- **`src/builder/routing/file_map.py`**: `score_entry_against_timeline_block()` recebe o sinal de data e aplica o boost
- Regex proposta: `^(\d{1,2})\.(\d{2})\s+` (captura `DD.MM` seguido de espaço no início do nome)
- Ano inferido como o ano letivo corrente da disciplina (já disponível no `SubjectProfile`)

---

## 6. Backend MinerU

Adicionar **MinerU** como backend avançado de extração de PDF, com foco em documentos
acadêmicos com fórmulas, tabelas e layouts complexos.

### Motivação

MinerU é um extrator open-source com suporte a:
- Fórmulas LaTeX via modelo de visão
- Detecção de layout (colunas, cabeçalhos, rodapés)
- Tabelas como markdown
- Execução local sem API key

Abre uma alternativa ao Datalab para quem quer qualidade `math_heavy` sem custo por
página e sem enviar documentos para serviço externo.

### Escopo

- Novo `src/builder/runtime/mineru_client.py` — wraper de chamada ao CLI/API local do MinerU
- Novo valor `"mineru"` no enum de backends em `src/builder/runtime/backend_runtime.py`
- Seletor no app para `math_heavy` com MinerU como opção ao lado de Datalab e docling
- Saída gravada em `staging/markdown-auto/mineru/<entry>/` (padrão dos backends avançados)
- Suporte a `images_dir` via `BackendRunResult.images_dir` (já existe o campo)

### Considerações

- MinerU exige GPU ou é lento em CPU — documentar requisitos mínimos
- Investigar compatibilidade com Windows (projeto principal usa Win 11)
- Avaliar se o output LaTeX do MinerU é compatível com a injeção atual de descrições de imagem

---

## 7. Marker-API (backend cloud do Marker)

Adicionar suporte ao **Marker-API** — versão cloud do Marker com API key — como
alternativa ao uso local do `marker_single` CLI.

### Motivação

O Marker local está em investigação e não é o caminho principal recomendado atualmente.
A Marker-API resolve os problemas do Marker local:
- Sem dependência de GPU local
- Sem problemas de instalação de dependências pesadas
- Qualidade consistente entre máquinas
- Cobrança por uso, sem setup

### Escopo

- Novo `src/builder/runtime/marker_api_client.py`
- Novo valor `"marker_api"` separado de `"marker"` (local CLI)
- Campo `MARKER_API_KEY` nas variáveis de ambiente e no `.env`
- Seletor no app exibido apenas quando `MARKER_API_KEY` estiver configurada
- Saída em `staging/markdown-auto/marker-api/<entry>/`
- Reaproveitamento da lógica de `_save_datalab_images` adaptada para o formato de resposta da Marker-API

### Considerações

- Verificar limites de tamanho de arquivo e custo por página da Marker-API
- Manter `"marker"` (CLI local) e `"marker_api"` como opções independentes — não fundir

---

## 8. Instalador Windows (Setup.exe)

Distribuir o app como um instalador nativo para Windows, publicado na seção
**Releases** do GitHub, que configura tudo do zero sem exigir conhecimento de
terminal, Python ou virtualenvs.

### Motivação

O fluxo de instalação atual exige:

- instalar Python manualmente com a opção `Add to PATH`
- criar e ativar um virtualenv
- rodar `pip install -e .[dev]`
- instalar Ollama, Tesseract e CLIs opcionais separadamente
- configurar variáveis de sistema manualmente

Para um aluno que só quer usar o app — não desenvolver nele — esse processo é
uma barreira alta. Um `Setup.exe` elimina esse atrito e abre o projeto para
usuários sem background técnico.

### Escopo

**Wizard de instalação**

- Tela de boas-vindas com versão e licença
- Seleção de pasta de instalação (padrão: `%LOCALAPPDATA%\GPTTutorGenerator`)
- Detecção automática do que já está instalado (Python, Ollama, Tesseract, Git)
- Checkbox por componente opcional (Tesseract OCR, docling, marker-pdf)
- Configuração do `.env` pelo wizard (campo para `DATALAB_API_KEY`)
- Seletor de modelos Ollama para baixar durante a instalação:
  - `qwen3-vl:8b` — leve, roda em GPU com 8 GB de VRAM
  - `qwen3-vl:235b-cloud` — qualidade máxima via Ollama Cloud
  - `(nenhum por enquanto)` — instalar depois pelo app
- Opção de criar atalho na Área de Trabalho e no Menu Iniciar
- Opção de associar extensão `.env` ao Bloco de Notas para edição rápida

**O que o instalador configura automaticamente**

- Copia os arquivos do app para a pasta de instalação
- Cria e popula o virtualenv interno (`<install_dir>\.venv`)
- Define `TESSDATA_PREFIX` no perfil do usuário se Tesseract for instalado
- Adiciona Ollama ao `PATH` se não estiver
- Cria `run.bat` e atalhos apontando para `python app.py` dentro do venv

**Releases no GitHub**

- Artefato publicado em `github.com/HumbertoCG18/GPT-Tutor-Generator/releases`
- Nome canônico: `GPTTutorGenerator-Setup-v<versao>.exe`
- Changelog resumido no corpo da release (gerado do `git log`)
- Asset adicional: `GPTTutorGenerator-portable-v<versao>.zip` (extração direta, sem wizard)

### Toolchain sugerida

| Opção | Prós | Contras |
|---|---|---|
| **NSIS** (Nullsoft) | maduro, scriptável, output leve | sintaxe de script datada |
| **Inno Setup** | UI moderna, Pascal script, gratuito | menos usado em projetos Python |
| **PyInstaller + NSIS** | empacota o Python junto, sem dependência de instalação do Python | executável maior (~50–80 MB) |
| **uv + NSIS** | usa `uv` para resolver deps rapidamente, venv leve | exige `uv` instalado ou embarcado |

Recomendação inicial: **Inno Setup** para o wizard + **PyInstaller** para empacotar
o Python e o app num único executável, evitando dependência de Python instalado no
sistema do usuário.

### Considerações

- O app usa Tkinter — PyInstaller lida bem com isso no Windows
- Ollama precisa ser baixado separadamente (instalador próprio); o wizard pode
  abrir o instalador do Ollama automaticamente ou redirecionar para o site
- `git` também pode não estar presente — o wizard deve verificar e orientar
- O fluxo de atualização (reinstalar sobre versão anterior) deve ser testado
- CI/CD: criar GitHub Action que gera o `Setup.exe` automaticamente em cada tag `v*`

---

## Priorização sugerida

| Ordem | Item | Esforço | Ganho |
|---|---|---|---|
| 1 | Student State (painel de sessão) | médio | alto — resolve cold start e context flooding |
| 2 | Sinalizador DD.MM em nomes de arquivo | baixo | médio — melhora mapeamento automático |
| 3 | Cronograma visual | médio | alto — resolve dor atual de diagnóstico de mapeamento |
| 4 | NotebookLM | médio | alto — destrava caso de uso de revisão pré-prova |
| 5 | MinerU | alto | alto — alternativa local de qualidade ao Datalab |
| 6 | Marker-API | médio | médio — destravar Marker sem dependência de GPU local |
| 7 | Obsidian/Notion | alto | médio — nicho, mas abre uso fora do tutor LLM |
| 8 | Instalador Windows (Setup.exe) | alto | alto — remove barreira de entrada para usuários finais |

Student State e DD.MM vêm primeiro por custo-benefício: menor esforço, resolvem
problemas que afetam todo ciclo de uso. Cronograma visual e NotebookLM vêm em
seguida porque já têm o contexto arquitetural claro. MinerU e Marker-API dependem
de investigação de ambiente antes de comprometer escopo. O instalador vem por
último no esforço técnico, mas é o que abre o projeto para usuários sem background
de desenvolvimento.

---

## Concluído

### STUDENT_STATE v2 — 2026-04-16

- YAML puro no `STUDENT_STATE.md` (~150–300 tokens)
- Histórico em `student/batteries/<unit>/<topic>.md` com summary consolidado
- Consolidação manual via `Repo → Consolidar unidade` com backup reversível
- Migração automática de repos v1 na primeira abertura
- Spec: `docs/superpowers/specs/2026-04-16-student-state-batteries-design.md`
- Plano: `docs/superpowers/plans/2026-04-16-student-state-batteries.md`
