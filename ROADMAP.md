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

## Priorização sugerida

| Ordem | Item | Esforço | Ganho |
|---|---|---|---|
| 1 | Cronograma visual | médio | alto — resolve dor atual de diagnóstico de mapeamento |
| 2 | NotebookLM | médio | alto — destrava caso de uso de revisão pré-prova |
| 3 | Obsidian/Notion | alto | médio — nicho, mas abre uso fora do tutor LLM |

Obsidian vem antes de Notion dentro do item 3: Obsidian usa os mesmos markdowns
com pouca adaptação; Notion exige pipeline de conversão dedicado.
