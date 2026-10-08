# Cronograma: tipo autoritativo do SARC + tab em tabela com legenda

> Design doc. Aprovado em 2026-06-06.

## Goal

Duas frentes coesas sobre o cronograma:

1. **Backend** — usar o **tipo autoritativo do SARC** (coluna *Atividade* + cor da
   linha) para classificar blocos do cronograma, em vez de re-adivinhar tudo do
   texto livre. Consequência direta: dias de prova viram `assessment` de forma
   confiável e **não recebem unidade** (hoje o sistema tenta atribuir unidade a
   provas, confundindo o cronograma).
2. **UI** — refazer o tab *Cronograma* como **tabela plana com legenda**
   (ícone → significado), mantendo edição manual (kind/unidade) e expansão de
   arquivos por bloco.

## Contexto (estado atual)

Fluxo SARC → kind hoje (mapeado):

```
SARC HTML (dgAulas, linhas coloridas, coluna Atividade)
  -> _aspnet_row_kind() : cor -> (token legado, ignored)         helpers.py:377
  -> _parse_aspnet_schedule() : embute [Atividade] no texto       helpers.py:388
       e emite {kind=token} quando token != class                 helpers.py:406-410
  -> _build_timeline_candidate_rows() : extrai {kind=}, row.kind  index.py:415
       ignored = token in _IGNORED_KINDS                          index.py:412
  -> montagem do bloco (NENHUM kind aqui)                         index.py:~2077
  -> ensure_block_kind() -> classify_block() (texto/sessão)       index.py:2154
  -> block["kind"]                                                (única escrita)
```

Problemas confirmados:

- **A cor é descartada para o bloco.** `row.kind` (de `{kind=exam}`) nunca chega
  em `block["kind"]`; `classify_block` re-deriva do texto. O sinal do professor
  morre na montagem.
- **A coluna Atividade vira só texto.** `[Prova]` é concatenado na descrição e só
  influencia via tokens da sessão (rede de segurança adicionada em
  `2026-06-06-...` — o fix de `_session_exam_or_review`). Nunca foi campo distinto.
- **Tokens de cor são legados** (`exam`, `ps`, `g2`, `event`, `assignment`,
  `suspension`) e não batem com `BlockKind` (`assessment`, `makeup`, `suspended`,
  `academic_event`, `deliverable`). `{kind=exam}` produz string inválida no enum.
- **Atribuição de unidade roda em todos os blocos**, inclusive provas
  (`index.py:2127-2140`), antes de `ensure_block_kind` (`2154`).
- **Tab** = `src/ui/timeline_dashboard.py`: accordion de blocos + filtros +
  dropdowns de override (kind/unidade) + expansão de arquivos + seção "não
  mapeados". Não há legenda. Ícones/labels vêm de `KIND_DISPLAY`
  (`src/builder/timeline/kinds.py`, 15 kinds, fonte única).

## Decisões (do brainstorming)

- **Sinal autoritativo:** Atividade primário, **cor confirma** (não sobrepõe
  Atividade explícita).
- **Unidade:** kinds não-aula (prova/feriado/revisão/reposição/…) **não recebem
  unidade**.
- **Tab:** **tabela plana + legenda**, mantendo edição inline (kind/unidade) e
  expansão de arquivos.
- **Entrega:** spec único, **2 planos** — backend primeiro (testável sozinho),
  depois UI.
- **Abordagem backend:** hint `source_kind` autoritativo via o canal `{kind=}`
  existente (reaproveita pipeline; mínimo de campos novos).

## Arquitetura

Princípio: o tipo do SARC vira um **hint de bloco** (`source_kind`) que
`classify_block` honra com prioridade logo abaixo do override manual. Texto/sessão
continuam como fallback (cobre cronogramas não-SARC, ex.: SYLLABUS colado). Unidade
é limpa de blocos cujo kind final não é `class`.

Prioridade de kind: `manual_kind_override` > `source_kind` (SARC) > heurística
texto/sessão.

---

## PARTE A — Backend (Plano 1)

### A1. `src/utils/helpers.py` — Atividade + cor → kind canônico

- Novo dict keyword `ATIVIDADE_KIND_MAP` (normalizado, sem acento, lower):
  - `prova`, `avaliacao`, `exame`, `teste` → `"assessment"`
  - `trabalho`, `entrega` → `"deliverable"`
  - `feriado` → `"holiday"`
  - `revisao` → `"review"`
- Novo helper `_aspnet_row_canonical_kind(row) -> tuple[str, bool]`:
  1. `atividade = _aspnet_row_cell(row, "Atividade")` (normalizado).
  2. Procura keyword de `ATIVIDADE_KIND_MAP` em `atividade`. Achou →
     `(kind, False)` (Atividade vence).
  3. Senão, `color_kind, ignored = _aspnet_row_kind(row)`; se `color_kind != "class"`
     → `(color_kind, ignored)` (cor como fallback).
  4. Senão → `("class", False)`.
- `_ASPNET_COLOR_KIND_MAP`: trocar os tokens **não-ignorados** por nomes do enum:
  `"#ffa500"/"orange" -> ("assessment", False)`,
  `"#ffff00"/"yellow" -> ("deliverable", False)`.
  Os ignorados (`suspension`, `g2`, `ps`, `event`) **permanecem** com os tokens
  atuais e `ignored=True` (preservam `_IGNORED_KINDS`).
- `_parse_aspnet_schedule`: usar `_aspnet_row_canonical_kind(row)` no lugar de
  `_aspnet_row_kind(row)`; emitir `{kind=<canônico>}` quando `kind != "class"`
  (comportamento de `ignored`/`⊘` inalterado). A linha `[Atividade]` no texto
  permanece (não quebra exibição nem a rede de segurança da sessão).

### A2. `src/builder/timeline/index.py` — validação do token

- Em `_build_timeline_candidate_rows`: após extrair `kind` do `{kind=}`, validar
  contra os valores de `BlockKind`. Inválido → `kind = "class"` (defensivo).
- `ignored = kind in _IGNORED_KINDS` permanece (tokens ignorados não mudaram).

### A3. `src/builder/timeline/index.py` — `source_kind` no bloco

- Constante de prioridade (mais forte vence ao agregar linhas de um bloco):
  `["assessment", "deliverable", "review", "holiday", "makeup", "suspended",
   "academic_event", "results", "workshop", "office_hours", "planning",
   "reserved"]` (tudo menos `class`/`overview`/`unknown`).
- Na montagem do bloco: coletar os `row["kind"]` (não-`class`, válidos, não
  `ignored`) das linhas do bloco; se houver, `block["source_kind"]` = o de maior
  prioridade. Sem hint → não escreve a chave.
- Persistência: incluir `source_kind` na serialização
  (`_serialize_timeline_index`) e no schema do timeline como **campo opcional**
  (string). Confirmar em `tests/test_timeline_schema.py` que não dispara drift; se
  o validador rejeitar campos extras, adicionar `source_kind` à lista permitida
  (sem bump de versão se possível).

### A4. `src/builder/timeline/classifier.py` — honrar `source_kind`

- Em `classify_block`, logo após o bloco de `manual_kind_override` e **antes** da
  heurística de texto:
  ```python
  source = block.get("source_kind")
  if isinstance(source, str):
      try:
          return BlockKind(source)
      except ValueError:
          pass
  ```
- Mantém o fix de sessão (`_session_exam_or_review`) como fallback para
  cronogramas sem SARC.

### A5. `src/builder/timeline/index.py` — limpar unidade em não-aula

- Helper único `finalize_block(block) -> dict` (idempotente):
  1. `ensure_block_kind(block)` (mantém lógica atual).
  2. Se `block["kind"] != BlockKind.CLASS.value` **e** sem `manual_unit_slug` →
     `block["unit_slug"] = ""`, `block["unit_confidence"] = 0.0`.
- Substituir as chamadas atuais de `ensure_block_kind` no fluxo de montagem
  (`index.py:2154`) e onde a serialização re-deriva kind, por `finalize_block`.
- Override manual de unidade (`manual_unit_slug`) sempre preservado.
- Nota: revisão de conteúdo que permanece `class` (tem unidade, gated em
  `_session_exam_or_review`) mantém a unidade — só kinds finais não-`class` perdem.

### A6. Testes (TDD, `tests/`)

`tests/test_sarc_import.py` (ou novo arquivo de helpers):
- `Atividade="Prova"` → `{kind=assessment}` no markdown.
- `Atividade="Aula"` + linha laranja → `class` (Atividade vence a cor).
- `Atividade=""` + linha laranja → `assessment` (cor como fallback).
- `Atividade="Trabalho"` → `deliverable`.

`tests/test_timeline_kinds.py`:
- `classify_block({"source_kind": "assessment", "unit_slug": "u1"})` → `ASSESSMENT`
  (source vence texto/unidade).
- `manual_kind_override` vence `source_kind`.
- `source_kind` inválido → cai na heurística.

`tests/test_timeline_*` (montagem/serialização):
- Linha `{kind=assessment}` → `row.kind="assessment"`, não `ignored`; bloco recebe
  `source_kind="assessment"`.
- Linha `{kind=suspension}` → `ignored=True` (inalterado).
- Token inválido `{kind=foo}` → `class`.
- `finalize_block`: bloco assessment → `unit_slug=""`; bloco class → unidade
  mantida; `manual_unit_slug` preservado em não-aula.

Regressão:
- Re-rodar o delta dos 5 cursos reais (`Engenharia-Software-2`, `IA`,
  `Métodos-Formais`, `Sistemas-Operacionais`, `TCC`): nenhuma regressão; provas
  ficam `assessment` sem unidade. Health-gates seguem verdes.

---

## PARTE B — UI (Plano 2)

### Restrição Tk

`ttk.Treeview` não hospeda dropdowns nem expansão inline. Para manter edição +
expansão "em formato de tabela", usar um **grid de widgets**: frame rolável com
uma linha por bloco, colunas alinhadas via `grid` + cabeçalho fixo. Lê como tabela,
preserva os widgets atuais. (Não é `ttk.Treeview`.)

### B1. Legenda (topo do tab)

- Bloco de legenda derivado de `KIND_DISPLAY` (fonte única): tabela `ícone →
  significado`. Sem hardcode de ícones/labels.
- Renderizar só os kinds presentes nos blocos atuais? Não — mostrar todos (legenda
  é referência). Decisão: **todos os 15 kinds**.

### B2. Tabela plana

- Cabeçalho fixo: `Tipo | Período | Tópico | Unidade | Status | Arq.`.
- Uma linha por bloco, colunas alinhadas (`grid`):
  - **Tipo**: ícone + label (`KIND_DISPLAY`).
  - **Período**: `period_label`.
  - **Tópico**: `primary_topic_label` (ou `—`).
  - **Unidade**: dropdown de override (✎ se manual) — preservado.
  - **Status**: badge colorido — preservado.
  - **Arq.**: contagem; clique na linha expande lista de arquivos do bloco —
    preservado.
  - Dropdown de **kind** (override manual) mantido (na coluna Tipo ou ação por
    linha).
- **Filtros** por kind (checkboxes) e **seção "não mapeados"**: mantidos.
- Sem mudança de dados: consome o mesmo `.timeline_index.json` + `manifest.json`.

### B3. Testes UI

- Lógica testável extraída do widget (ex.: `build_legend_rows()` → lista
  `(icon, label)` de `KIND_DISPLAY`; `build_table_rows(blocks)` → linhas
  formatadas). Testes unitários sobre essas funções puras; o `grid` em si não é
  testado por automação (Tk).

---

## Fora de escopo

- Reconciliar `ps`/`g2`/`event`/`suspension` ignorados (segunda chamada, G2 etc.):
  permanecem ignorados como hoje.
- Separar bloco fundido revisão+prova (ex.: TCC 01/07 + 03/07) em dois blocos.
- Stopword "para" poluindo `primary_topic_label` (extração de tópico).
- Re-rodar/regerar os repos reais — o usuário regera quando quiser ver o efeito.

## Riscos

- Adicionar `source_kind` ao schema pode disparar o gate de schema — mitigado
  tratando como campo opcional permitido (A3).
- Limpar `unit_slug` de blocos não-`class` interage com `classify_block`
  (usa `has_unit`): seguro porque kinds não-`class` derivam de
  `source_kind`/keyword/sessão, não de unidade (A5, nota).
