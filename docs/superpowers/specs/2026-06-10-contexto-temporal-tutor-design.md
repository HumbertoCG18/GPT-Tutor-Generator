# Contexto Temporal + Prontidão Pré-Prova — Design

> Roadmap #12 (contexto temporal / semana atual) + #13 (prontidão pré-prova).

**Data:** 2026-06-10
**Branch:** new-features

## Objetivo

O tutor LLM deve abrir cada sessão sabendo onde o aluno está no semestre
(tópico da semana vigente), qual a próxima avaliação e seu escopo, e quão
preparado o aluno está para ela — **tudo autocalculado pelo tutor a cada
sessão** a partir de um artefato compacto gerado no build. Sem staleness,
sem reprocessar a matéria.

## Princípio de automação

Dado **estável** (cronograma) é gerado no build; lógica **dinâmica**
("hoje", prontidão) é delegada ao tutor em runtime via regras de instrução.

```
BUILD (ocasional)                          SESSÃO DO TUTOR (toda vez)
─────────────────                          ──────────────────────────
.timeline_index.json (já tem               1. lê setup/CONTEXTO_TEMPORAL.md
  period_start/end ISO, kind,              2. acha linha onde hoje ∈ [início,fim]
  unit_slug, primary_topic_label,             → "semana atual" + tópico
  scope_unit_slugs)                        3. acha 1ª prova com início ≥ hoje
        │                                      → próxima avaliação + escopo
        ▼                                   4. p/ cada unidade do escopo:
  temporal_context.py (novo)                   cruza COURSE_MAP × STUDENT_STATE
        │  gera                                × batteries/ → prontidão (lacunas)
        ▼
  setup/CONTEXTO_TEMPORAL.md  ◄── instruções (prompts.py) ensinam as regras 2-4
```

- **#12** = passos 1-3 (semana atual + próxima prova).
- **#13** = passo 4 (prontidão: escopo × baterias × estado).
- O artefato carrega só dado **estável** (cronograma). Prontidão usa
  artefatos que o tutor já tem (`COURSE_MAP.md`, `STUDENT_STATE.md`,
  `student/batteries/`) — sem duplicar estado mutável no artefato.

## Artefato: `setup/CONTEXTO_TEMPORAL.md`

```markdown
# CONTEXTO TEMPORAL — Cálculo I
> Cronograma compacto. Você (tutor) calcula a semana atual e a prontidão
> pré-prova A CADA sessão comparando com a data de hoje. Datas ISO YYYY-MM-DD.

## Unidades
- **U1** = `unidade-01-limites` — Limites
- **U2** = `unidade-02-derivadas` — Derivadas

## Cronograma
| bloco | inicio | fim | tipo | unidade | topico | escopo |
|-------|--------|-----|------|---------|--------|--------|
| bloco-01 | 2026-03-03 | 2026-03-10 | aula | U1 | Definição de limite; Limites laterais | — |
| bloco-07 | 2026-04-21 | 2026-04-21 | revisão | — | — | U1 |
| bloco-09 | 2026-04-28 | 2026-04-28 | prova P1 | — | — | U1 |
```

Regras de conteúdo:

- **Coluna `unidade` e `escopo` usam rótulo curto `U1`/`U2`** (legível). A
  seção `## Unidades` mapeia cada rótulo ao **slug canônico** + nome — é por
  ela que o tutor resolve `U1 → unidade-01-limites` para juntar com
  `student/batteries/<slug>/` e `COURSE_MAP`. Rótulo curto via
  `unit_short_label` (extraído pra módulo base; ver Unidades de código). Slug
  que não casa o padrão `unidade-NN` cai pro próprio slug.
- A legenda lista **só as unidades que aparecem** na tabela (em aula ou escopo),
  ordenadas por número. Nome da unidade: derivado do slug (parte após
  `unidade-NN-`, com `-`→espaço, capitalizado) — não há fonte de nome melhor
  disponível no bloco; YAGNI.
- Coluna `tipo`: `aula` (CLASS), `prova <código>` (ASSESSMENT, ex.: `prova P1`),
  `revisão` (REVIEW), `feriado` (HOLIDAY), `exame` (EXAM). Código de prova via
  `_exam_code_from_block` (`content_taxonomy.py`).
- Coluna `topico`: **lista completa `topics`** do bloco, juntada por `; `
  (cobre mais que só o tópico primário). Vazia → `—`.
- Célula vazia → `—`. Múltiplos rótulos no escopo → separados por `, `.
- Bloco **sem data válida** (sem `period_start`) → **omitido** da tabela
  (não há como localizá-lo no tempo).
- **Cronograma vazio** (nenhum bloco com data) → artefato emitido com nota
  `_Cronograma indisponível._` no lugar da tabela e da legenda.

## Lógica de instrução (em `prompts.py`)

Helper único `_temporal_context_instructions() -> str` (DRY), injetado nos
três geradores (Claude/GPT/Gemini). Texto fixo (sem interpolação por curso):

```markdown
## Contexto temporal — calcule no início de cada sessão
Abra `setup/CONTEXTO_TEMPORAL.md`. Com a data de HOJE:
1. **Semana atual**: linha onde hoje ∈ [inicio, fim]. Diga unidade + tópico vigente.
   Se hoje for depois do último bloco, o semestre acabou; se antes do 1º, ainda não começou.
2. **Próxima avaliação**: 1ª linha tipo=prova/exame com inicio ≥ hoje. Diga qual, a data,
   dias restantes e o escopo (unidades).
3. **Prontidão pré-prova** (só se houver prova futura): pra cada unidade do escopo →
   tópicos no `COURSE_MAP.md` → status em `STUDENT_STATE.md` / `student/batteries/<unidade>/`.
   Liste tópicos sem registro ou pendentes. Priorize se a prova ≤ 7 dias.
Se `CONTEXTO_TEMPORAL.md` não existir ou estiver vazio, pule este bloco.
```

Caminho relativo serve aos três (a instrução GPT já explica o acesso raw
GitHub genericamente). A seção entra junto ao contrato de artefatos existente.

## Unidades de código

### Extração: `src/builder/timeline/unit_labels.py` (novo, base)

`_unit_short_label` hoje vive em `src/ui/timeline_dashboard.py` (camada UI). O
builder **não pode importar a UI**. Extrair para módulo base compartilhado:

- `unit_short_label(slug: str) -> str` — `unidade-01-... → U1`; fallback ao slug.
- `unit_name_from_slug(slug: str) -> str` — parte após `unidade-NN-`,
  `-`→espaço, capitalizado; vazio → slug.
- Move o regex `_UNIT_NUM_RE` para cá.

`src/ui/timeline_dashboard.py` passa a importar `unit_short_label` deste módulo
(mantém o alias `_unit_short_label = unit_short_label` para não quebrar os
testes existentes que importam o nome privado).

### Novo módulo `src/builder/artifacts/temporal_context.py`

- `build_temporal_context_rows(timeline_blocks: list[dict]) -> list[dict]`
  Puro. Mapeia cada bloco com `period_start` em
  `{"id", "inicio", "fim", "tipo", "unidade", "unidade_slug", "topico", "escopo", "escopo_slugs"}`.
  - `inicio`/`fim`: `period_start`/`period_end` (string ISO; `fim` cai pra
    `inicio` se ausente).
  - `tipo`: rótulo derivado de `kind` + código de prova (`_exam_code_from_block`).
  - `unidade`: rótulo curto (`unit_short_label(unit_slug)`); `unidade_slug`: slug cru.
  - `topico`: `topics` (lista completa) juntada por `; `; cai pra
    `primary_topic_label` se `topics` vazio; senão `""`.
  - `escopo`: lista de rótulos curtos dos `scope_unit_slugs`; `escopo_slugs`:
    slugs crus (para a legenda). Vazia para aula/feriado.
  - Blocos sem `period_start` → omitidos.

- `build_unit_legend(rows: list[dict]) -> list[dict]`
  Puro. Coleta todos os slugs que aparecem em `unidade_slug` + `escopo_slugs`,
  dedup, ordena por número da unidade, retorna
  `[{"label": "U1", "slug": "unidade-01-limites", "nome": "Limites"}]`.
  Nome: parte após `unidade-NN-` com `-`→espaço, capitalizado; vazio → slug.

- `temporal_context_md(course_meta: dict, timeline_blocks: list[dict]) -> str`
  Renderiza cabeçalho + nota + seção `## Unidades` (legenda) + seção
  `## Cronograma` (tabela). Vazio → nota de indisponível (sem legenda/tabela).
  Célula vazia vira `—`; escopo vira `, `.join(rótulos)` ou `—`.

- `current_block_for_date(rows: list[dict], ref_date: date) -> dict | None`
  Localiza o bloco vigente (`inicio <= ref_date <= fim`). Retorna o row ou
  `None`. Util testável — **não** ligado à UI nesta entrega (YAGNI), mas
  disponível para um indicador de "semana atual" futuro.

### `src/builder/artifacts/prompts.py`

- `_temporal_context_instructions() -> str` (helper único).
- Injetar a seção retornada nos três geradores: `_low_token_generate_claude_project_instructions`,
  `generate_gpt_instructions`, `generate_gemini_instructions`.

### Wire no build — `src/builder/ops/bootstrap_ops.py`

Em `write_root_files`, junto ao bloco que já grava `CRONOGRAMA_DETALHADO.md`
(quando `_timeline_blocks` presente), gravar também:

```python
write_text(
    builder.root_dir / "setup" / "CONTEXTO_TEMPORAL.md",
    temporal_context_md(builder.course_meta, _timeline_blocks),
)
```

`write_text` já é atômico. `temporal_context_md` passa como novo parâmetro
`temporal_context_md_fn` na assinatura de `write_root_files` (mesmo padrão dos
demais `*_fn`), e `engine._write_root_files` passa a função real importada de
`artifacts.temporal_context`.

## Tratamento de erros / casos de borda

- Cronograma vazio ou ausente → artefato com nota; instrução manda o tutor pular.
- Blocos sem data → omitidos da tabela (não quebram o render).
- Datas malformadas → tratadas como ausentes (omitidas).
- `current_block_for_date` com data fora de qualquer janela → `None`.

## Testes

Novo `tests/test_unit_labels.py`:

- `unit_short_label`: `unidade-01-limites → U1`; `unidade-10-x → U10`;
  slug fora do padrão → ele mesmo; vazio → `""`.
- `unit_name_from_slug`: `unidade-01-limites → Limites`;
  `unidade-02-derivadas-parciais → Derivadas parciais`; sem sufixo → slug.

Novo `tests/test_temporal_context.py`:

- `build_temporal_context_rows`: aula com `topics` (lista juntada por `; `);
  aula só com `primary_topic_label` (fallback); prova com escopo + código
  `P1`; revisão com escopo; feriado; bloco sem data (omitido); escopo
  multi-unidade (rótulos curtos).
- `build_unit_legend`: coleta slugs de unidade + escopo, dedup, ordenado por
  número; nome derivado; lista só unidades presentes.
- `temporal_context_md`: contém `## Unidades` + `## Cronograma`, datas ISO,
  rótulo `U1` na tabela, slug na legenda; vazio → nota `Cronograma indisponível`
  sem tabela/legenda.
- `current_block_for_date`: acerta bloco vigente; `None` fora de janela;
  borda inclusiva (`inicio` e `fim`).

Estender `tests/test_prompts*` (ou novo): cada gerador inclui a seção
"Contexto temporal".

Reuso do regex na UI: garantir que `tests/test_timeline_sort.py` (que importa
`_unit_short_label` da UI) segue verde após a extração (alias mantido).

## Fora de escopo (YAGNI)

- Indicador de "semana atual" na UI (a util existe, mas não é ligada agora).
- Prontidão pré-computada/persistida no build (delegada ao tutor).
- Regeneração agendada (#15) e instruções adaptativas (#16) — itens próprios.
