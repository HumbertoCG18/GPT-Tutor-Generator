# Cronograma: Sessão-como-Átomo + Projeções — Design

last_updated: 2026-06-19
status: design aprovado (brainstorming), pendente revisão final do spec
escopo: dentro do refactor de atribuição A1-A7

## Problema

Investigação dos 5 cursos (MF, IA, SO, ES2, TCC) revelou que **as datas e dias-da-semana
do cronograma já estão 100% corretos** (zero anomalias após re-import SARC). O que o usuário
percebe como "cronograma inconsistente / arquivos espalhados" são três defeitos distintos,
todos a montante do que o re-import resolve:

1. **Over-merge de blocos.** O agrupamento temático (`_rows_belong_to_same_thematic_block`)
   cola N sessões num bloco só. Resultado: blocos variam de 1 dia a 29 dias (IA bloco-05:
   9 sessões, 29 dias). Granularidade desigual entre matérias. Já catalogado e adiado no
   `.mex/ROUTER.md` como "separar blocos merged" (P2).
2. **Render que esconde os dias.** `cronograma_detalhado_md` (`src/builder/artifacts/repo.py`)
   renderiza `period_label` ("## 15 dias · 11/03 a 25/03") e **ignora** o array `sessions`
   que já existe em cada bloco. O dado por-dia existe; o render não o mostra.
3. **Espalhamento de material.** Atribuição material→bloco usa `source_section` →
   `resolve_card_to_block` (match difuso de token) ou scorer. No MF real, 28% das entries
   têm `source_section` vazio → caem no scorer → espalham; e a chave de join tem bug de
   normalização (`.strip()` sem casefold em `content_taxonomy.py:890`).

A causa-raiz comum: o sistema trata um **agrupamento heurístico** (bloco-temático) como
unidade primária e enterra o **átomo real** (a sessão de aula) dentro dele. Heurística como
primária = tuning recorrente a cada curso. Esta spec inverte isso.

## Objetivo

Inverter o núcleo da timeline: **a sessão de aula (1 linha do cronograma SARC) é a unidade
persistida (átomo)**. Tudo o mais — semana, bloco-temático, unidade, escopo de prova,
progressão — passa a ser **projeção determinística** sobre sessões. Material atribui por join
explícito (card → slug canônico → sessões). Render mostra dia-a-dia.

Princípio de modularidade: **nenhuma suposição de cadência** (semana = semana ISO sobre o que
existir; funciona para 1x, 2x, 3x por semana sem código novo). O átomo é o invariante presente
em todo curso (toda matéria tem export SARC com uma linha por aula).

## Fronteira com a Spec B (ingestão)

Esta spec é o **consumidor**. Ela assume um stash organizado e o cronograma SARC parseado.
Ela **não** cobre como o stash é baixado/organizado — isso é a Spec B
(`2026-06-19-ingestao-stash-sarc-skeleton-design.md`).

Contrato de dados compartilhado (B produz, A consome):
- **`_CRONOGRAMA.json`** na raiz do stash: lista de sessões SARC (data, kind, topic, unit).
- **`_CARD.json`** em cada pasta-card: declara `topic_slug`, `topic_label`, `unit_slug`
  (ou lista de unidades), `session_dates`, `source` ("sarc"|"manual"), `confirmed` (bool).

A consome um stash organizado **à mão** igual a um organizado pela B. A automação da B é
ortogonal à correção da A.

## Arquitetura

### 1. Átomo — Sessão

Unidade persistida, 1:1 com uma linha do cronograma SARC. Substitui o bloco como primário no
`.timeline_index.json`.

```json
{
  "id": "s-2026-03-11",
  "date": "2026-03-11",
  "weekday": "qua",
  "kind": "class",
  "unit_slug": "unidade-01",
  "topic_slug": "especificacao-conjuntos-indutivos",
  "topic_label": "Especificação de Conjuntos Indutivos",
  "signals": ["..."],
  "source_row": 7,
  "materials": ["ConjuntosIndutivos.pdf", "..."]
}
```

- `kind` vem do SARC (Atividade + cor) **por linha** — sem `_aggregate_source_kind`. Cada
  sessão já carrega seu kind na origem. Reusa os 15 valores de `BlockKind`
  (`src/builder/timeline/kinds.py`).
- `materials` é populado pela atribuição (seção 3), não pelo parse SARC.

### 2. Projeções — funções puras sobre sessões (nada persistido como primário)

- `weekly(sessions) -> [Week]`: agrupa por semana ISO via `date.isocalendar()`. `Week{iso_year,
  iso_week, mon, sun, sessions[]}`. Determinístico, sem suposição de cadência.
- `thematic(sessions) -> [TopicGroup]`: agrupa por `topic_slug` (e por `unit_slug`). O "bloco"
  vira grupo derivado por igualdade de slug — **substitui** `_rows_belong_to_same_thematic_block`
  (mata o over-merge: agrupa por tag igual, não por overlap difuso).
- `assessment_scope(sessions) -> {assessment_session_id: [in_scope_session_id]}`: janela por
  data. Para cada sessão `kind=assessment`, inclui sessões `class` com `date <= assessment.date`
  e `> data da prova anterior` (P1: início→P1; PN: P(N-1)→PN; PS/G2: semestre inteiro). Re-aloja
  a lógica já implementada (`assessment_scope_by_date`), agora **sobre sessões** → precisão de
  subunidade de graça (inclui sessões taught até a data, exclui as depois), sem campo de subunidade.
- `progression(sessions)`: sessões ordenadas por data. A progressão "primeiro X, depois Y" é
  emergente da ordem; não requer hierarquia de subunidade.

### 3. Atribuição de material (peça nuclear do A1-A7)

Join explícito, determinístico:

```
arquivo → card (pasta) → _CARD.json{topic_slug|unit_slug} → sessões com esse slug → datas
```

- O slug do card e o slug da sessão vêm da **mesma taxonomia canônica** (derivada do plano de
  ensino / SARC) → join é identidade, não inferência. Aposenta `resolve_card_to_block` difuso e
  o bug de normalização.
- **Uma atribuição por material** (nunca N entries — proíbe o bug de duplicata já corrigido por
  `scripts/dedup_manifest.py`). Persistido como `computed_session_ids` (lista) OU
  `computed_topic_slug` no manifest; o render expande. Substitui `computed_block_id`.
- **Manual override:** `manual_session_ids` / `manual_topic_slug` substitui
  `manual_timeline_block_id`, com migração retro-compatível.
- **Política de render para tópico multi-sessão** (decisão em aberto, ver Riscos): material de um
  tópico ensinado em N sessões aparece (a) repetido em cada sessão, ou (b) uma vez sob o
  cabeçalho do tópico, demais sessões marcam "continuação". Default proposto: **(a) repetir**,
  porque o usuário quer "o que estudar para esta aula" e a aula dura ~1h30.
- **Subunidade: opcional e cosmética.** Quando o `_CARD.json` declara `subunit_slug` (ou o stash
  tem subpasta de subunidade), vira rótulo de display. Nenhuma das dores operacionais
  (progressão, escopo) depende dela — ambas saem das datas. Curso sem subunidade funciona; com,
  ganha rótulo mais fino. **Nada quebra se faltar.**

### 4. Render

- **Dia-a-dia (fatia imediata — ver seção 6):** lista cada sessão sob sua data, com dia-semana.
  Agrupado por semana ISO.

```markdown
## Semana 3 · 09/03 – 13/03 — unidade-01
### Seg 09/03 — Lógica de Predicados
   • logicaPredicados_semantica.pdf
### Qua 11/03 — Especificação de Conjuntos Indutivos
   • ConjuntosIndutivos.pdf · ExerciciosConjuntosIndutivos.pdf · FormalizacaoAlgoritmos_Recursao2.pdf
```

- **Escopo de prova no display:** "P1 (22/04) cobre até: Provas Interativas / Isabelle" —
  derivado do `topic_label` da última sessão no escopo.
- Dashboard (`src/ui/timeline_dashboard.py`): consome sessões (não só `period_start/end`).

### 5. Migração

- Inverter primazia bloco↔sessão no `.timeline_index.json` (bump de versão).
- `computed_block_id` → `computed_session_ids`/`computed_topic_slug`; leitura retro-compatível
  do schema antigo durante transição.
- `manual_timeline_block_id` → `manual_session_ids`/`manual_topic_slug` (migração).
- Re-alojar `source_kind` (por-sessão, sem agregação) e `assessment_scope_by_date` (sobre
  sessões).
- Depreciar `_rows_belong_to_same_thematic_block` (substituído por `thematic()`).
- Preservar eval-gate / gold / rebuild_diff do A1-A7: a inversão entra atrás do gate, com
  comparação contra gold por curso antes do cutover.

### 6. Fatia imediata (ortogonal, segura de shippar antes da inversão)

Render dia-a-dia que **lê o `sessions[]` que já existe** nos blocos atuais e o lista por data,
agrupado por semana ISO. Não toca atribuição nem schema. É forward-compatível: quando a sessão
virar o átomo, este render é o render natural. Entrega o maior valor imediato (visualizar cada
aula) sem depender do refactor.

## Invariantes (não-negociáveis)

- Nenhuma suposição de cadência (semana = ISO sobre as sessões existentes).
- Uma atribuição por material (sem duplicatas no manifest).
- SARC read-only (OpenSARC nunca é escrito).
- Projeções são funções puras/determinísticas (testáveis isoladas, mesmo input → mesmo output).
- Subunidade é opcional; ausência não quebra nada.
- LLM nunca é autoridade de runtime na atribuição (só sugestor congelado, se usado — ver Spec B).

## Testes

- **Projeções (unit, fixtures de sessão):**
  - `weekly`: semana cruzando virada de ano; curso só-sexta (1 sessão/semana ISO); semana de
    feriado (0 sessões `class`); tópico atravessando 2 semanas ISO.
  - `thematic`: tópicos distintos não colam (caso que hoje over-merge cola); mesmo slug em
    sessões não-contíguas agrupa.
  - `assessment_scope`: P1 (início→P1), PN (P(N-1)→PN exclusivo/inclusivo), PS/G2 (semestre
    inteiro); prova cobre até a última sessão antes da data, exclui a seguinte (precisão
    subunidade sem campo).
- **Render:** snapshot do `CRONOGRAMA_DETALHADO.md` (dia-a-dia por semana) contra fixture.
- **Migração:** manifest antigo com `computed_block_id` lê corretamente sob o schema novo.

## Riscos / decisões em aberto

1. **Política de render multi-sessão** (repetir vs 1×-sob-tópico). Default proposto (a) repetir.
   Decidir antes da implementação do render. Pesa no caso card grosso (MF "Verificação de
   Programas" = 2 unidades, ~10 sessões → muita repetição sob (a)).
2. **Grão do card grosso.** Card multi-unidade joga material em muitas sessões (grão-unidade).
   Resolvido pela Spec B (rachar card no grão-tópico SARC); aqui, degradação graciosa: precisão
   = `min(grão-do-card, estrutura-disponível)`.
3. **Estabilidade do slug canônico.** Card e SARC têm que referenciar os mesmos slugs do plano de
   ensino. Risco da divergência latente `unit_index` vs `content_taxonomy` (já marcado no
   `.mex/ROUTER.md`). Esquema de slug estável é pré-requisito; tratar no A1-A7.
