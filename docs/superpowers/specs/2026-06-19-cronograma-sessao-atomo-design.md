# Cronograma: Sessão-como-Átomo + Projeções — Design

last_updated: 2026-06-19
status: design revisado (revisão adversarial 2026-06-19 aplicada), pendente revisão final do user
escopo: dentro do refactor de atribuição A1-A7
revisão: pivô chave-de-join slug→DATA; slug vira projeção de display; inversão v5 = destino (não
  pré-req); escopo honesto da fatia render; fallback sem-SARC; guarda dura de slug; pré-req unit_index
  reduzido a normalização. Correções factuais: v3-em-disco já tem sessions[]; M365 já implementado.

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
determinístico pela **DATA** (card → intervalo-de-datas-do-card ∩ `session.date`); o slug
canônico é **projeção de display**, NÃO a chave de junção. Render mostra dia-a-dia.

> **Decisão de chave de join (revisão adversarial 2026-06-19):** a chave de atribuição é a
> **data**, não o slug. Motivo: a data é o invariante real do SARC (toda linha tem data — é a
> condição de existência da linha) e já existe na sessão e em `.card_block_map.json{dates}`; o
> mecanismo de interseção de datas já está implementado (`derive_card_block_map`). O slug, ao
> contrário, **não** existe por sessão hoje (vive no bloco, vindo do scorer difuso) — usá-lo como
> chave reintroduziria o matching difuso que esta spec quer aposentar e exigiria manter dois slugs
> (card e sessão) sincronizados. Com a data como chave, o slug vira rótulo derivado e o scorer
> deixa de ser carga-crítica da atribuição.

Princípio de modularidade: **nenhuma suposição de cadência** (semana = semana ISO sobre o que
existir; funciona para 1x, 2x, 3x por semana sem código novo). O átomo é o invariante presente
em todo curso (toda matéria tem export SARC com uma linha por aula).

## Fronteira com a Spec B (ingestão)

Esta spec é o **consumidor**. Ela assume um stash organizado e o cronograma SARC parseado.
Ela **não** cobre como o stash é baixado/organizado — isso é a Spec B
(`2026-06-19-ingestao-stash-sarc-skeleton-design.md`).

Contrato de dados — **REUSA artefatos existentes, NÃO cria novos** (inventário 2026-06-19;
decisão: gabarito repo-side):
- **`.card_block_map.json`** (`course/`, já existe): gabarito card→destino, auto-derivado de
  labels Moodle (`derive_card_block_map`/`merge_card_block_map`, source:"labels") + override
  manual (source:"manual"). Já carrega `dates` por card — **a atribuição usa `dates` como chave de
  join** (interseção com `session.date`). Pode opcionalmente carregar `topic_slugs` como rótulo,
  mas o slug NÃO é a chave. O padrão auto-sugere+congela JÁ EXISTE aqui. A pasta-card (nome = chave
  de lookup, normalizada) é o gabarito; organizar o stash É autorar.
- **`.content_taxonomy.json`** (`course/`, já existe): autoridade do slug canônico
  (units→topics→subtopics com `slug`+`code`, ex. "1.1"). Card, SARC e plano referenciam ESTES slugs.
- **Sessões** vivem no `.timeline_index.json` (já têm `blocks[].sessions[]`); a inversão as
  promove a primárias (seção 1). **Sem `_CRONOGRAMA.json` novo** — o esqueleto da Spec B lê o
  parse SARC direto (que hoje já é transiente, não persistido).

A consome um stash organizado **à mão** igual a um organizado pela B. A automação da B é
ortogonal à correção da A.

## Arquitetura

### 1. Átomo — Sessão

Unidade persistida, 1:1 com uma linha do cronograma SARC. **Estado real em disco:** os artefatos
são `v3` e **já carregam** `blocks[].sessions[]` (com `id/date/kind/label/signals`) — verificado
em todos os 5 cursos. O upgrade lazy `v3→v4` (que só adiciona `kind`) já roda na leitura
(`_backfill_timeline_index`). A inversão promove a sessão a primária e renumera para `v5`, com
leitura retro-compatível. O bump de versão é cosmético para a fatia render (o campo já existe).

```json
{
  "id": "s-2026-03-11",
  "date": "2026-03-11",
  "weekday": "qua",
  "kind": "class",
  "label": "Especificação de Conjuntos Indutivos",
  "signals": ["..."],
  "source_row": 7,

  "_projecao_display": {
    "unit_slug": "unidade-01",
    "topic_slug": "especificacao-conjuntos-indutivos",
    "topic_label": "Especificação de Conjuntos Indutivos"
  },
  "_projecao_atribuicao": {
    "materials": ["ConjuntosIndutivos.pdf", "..."]
  }
}
```

- **Núcleo persistido** (do SARC, por linha): `id`, `date`, `weekday`, `kind`, `label` (texto-livre
  do SARC), `signals`, `source_row`. É o que de fato existe hoje na sessão.
- `kind` vem do SARC (Atividade + cor) **por linha** — sem `_aggregate_source_kind`. Cada
  sessão já carrega seu kind na origem. Reusa os 15 valores de `BlockKind`
  (`src/builder/timeline/kinds.py`).
- **`unit_slug`/`topic_slug`/`topic_label` NÃO existem por sessão hoje** — vivem no bloco, vindos
  do scorer difuso (`_assign_timeline_block_to_unit`). Aqui são **projeção de display**: a sessão
  herda o slug do seu bloco/scorer para rótulo. **Degradação graciosa:** bloco `topic_ambiguous`
  ou `unit_slug` vazio → rótulo vazio, sem quebrar nada (não são chave de join — a chave é a data).
- `materials` é **projeção da atribuição** (seção 3, join por data), não parse SARC.

### 2. Projeções — funções puras sobre sessões (nada persistido como primário)

- `weekly(sessions) -> [Week]`: agrupa por semana ISO via `date.isocalendar()`. `Week{iso_year,
  iso_week, mon, sun, sessions[]}`. Determinístico, sem suposição de cadência.
- `thematic(sessions) -> [TopicGroup]`: agrupa por `topic_slug`/`unit_slug` projetado, **quando
  disponível**. Como o slug por-sessão é projeção do bloco (pode faltar — ver seção 1), esta
  projeção NÃO é o que mata o over-merge sozinha. **Fix do over-merge (interino, independente de
  slug):** adicionar um teto temporal (mesma-semana-ISO ou gap-de-dias-máx) à condição de
  `_rows_belong_to_same_thematic_block` (`index.py:699-700`) — `date_dt` já está disponível na
  call-site. Resolve a granularidade desigual (IA bloco-05 de 29 dias) sem depender de slug
  canônico pronto. Substituir por agrupamento puro-por-slug fica como refinamento posterior.
- `assessment_scope(sessions) -> {assessment_id: [in_scope_session_id]}`: janela por data.
  **Âncora = blocos/sessões `kind=assessment` que carregam `date`** (no MF real existem 4 blocos
  `kind=assessment` com `period_start` válido, do parse SARC). NÃO depende de `assessments[]` do
  `.assessment_context.json` (vazio no MF) nem de `unit_periods` (texto livre). Para cada prova,
  inclui sessões `class` com `date <= prova` e `> prova anterior` (P1: início→P1; PN: P(N-1)→PN;
  PS/G2: semestre inteiro). **Re-aloja `assessment_scope_by_date` PRESERVANDO o `seen` set
  anti-poluição** (evita que aula atrasada de U1 depois da P1 polua o escopo da P2 — lógica
  não-trivial já implementada). Ganho real ao descer para sessão = **precisão temporal por data**
  (que já existe no grão-bloco) + granularidade de tópico **condicional** ao slug-por-sessão
  existir. **Sem slug fino, retorna no grão-unidade** (degradação graciosa). Não há "precisão de
  subunidade de graça" — corrigido.
- `progression(sessions)`: sessões ordenadas por data. A progressão "primeiro X, depois Y" é
  emergente da ordem; não requer hierarquia de subunidade.

### 3. Atribuição de material (peça nuclear do A1-A7)

Join determinístico **pela data** (não por slug):

```
arquivo → card (pasta) → .card_block_map.json{dates: [conjunto discreto]} → sessões cujo date ∈ dates
```

- **Semântica de `dates` = conjunto discreto (membership):** `session.date ∈ card.dates` (igualdade
  exata por data ISO), NÃO intervalo `min..max`. Motivo: membership é preciso (zero over-atribuição
  em dia de gap, zero bug de tópico não-contíguo, zero ambiguidade de overlap entre cards) e
  determinístico (casa o invariante de projeção pura). A completude de `card.dates` é
  responsabilidade da **ingestão** (Spec B: cross-check SARC enumera as sessões do tópico → as datas
  exatas), não do consumo.
- **Fallback de intervalo (explícito e logado):** quando a Spec B não consegue enumerar as sessões
  (cross-check SARC falha), o card cai para `min(dates)..max(dates)` **com log `span fallback`** e
  `confirmed:false`. Nunca silencioso — a UI da Spec B sinaliza sessões sem material para placement
  manual em vez de mascarar com material do vizinho.
- A chave de join é a **data** — não o nome-do-card (string) nem o slug. Aposenta
  `resolve_card_to_block` difuso E o bug de normalização de chave (que some por construção: a
  chave deixa de ser string sensível a caixa/acento e passa a ser data).
- **Por que data e não slug:** o `.card_block_map.json` já carrega `dates` (interseção de datas já
  implementada em `derive_card_block_map`), e a sessão já carrega `date`. O slug **não** existe por
  sessão de forma confiável (vem do scorer no bloco) — usá-lo como chave reintroduziria o difuso e
  exigiria sincronizar dois slugs. Com a data, ambos os lados já estão coerentes (a SARC é a fonte
  única de datas).
- **Slug = projeção de display** sobre a sessão: **reusa** `computed_unit_slug`/`computed_subunit_slug`
  do manifest (NÃO criar `computed_topic_slug`/`computed_session_ids`). `computed_block_id` é
  **rebaixado** de fonte primária a projeção derivada (não removido; leitura retro-compatível —
  `resolve_effective_block` em `file_map.py:556` e `repo.py:913` continuam lendo o valor
  materializado).
- **Uma atribuição por material** (nunca N entries — proíbe o bug de duplicata já corrigido por
  `scripts/dedup_manifest.py`). As sessões do material são **projeção** do intervalo de datas, não
  lista persistida duplicada.
- **Manual override:** reusa `manual_unit_slug` (e `manual_timeline_block_id` durante a
  transição). Sem campo manual novo paralelo.
- **Card grosso = grão-unidade, aceito explicitamente.** Card multi-tópico (MF "Verificação de
  Programas", ~10 sessões) tem um intervalo de datas largo → o material cai em todas as ~10 sessões.
  A data **não** compra precisão de subtópico, e **não** vamos desempatar por nome-de-arquivo: isso
  reintroduziria a heurística difusa que a spec elimina. Precisão fina = rachar o card em seções
  mais finas na ingestão (Spec B), não inferência no consumo. Degradação graciosa:
  precisão = `min(grão-do-card, estrutura-disponível)`.
- **Render para tópico multi-sessão:** material aparece **(a) repetido em cada sessão** do intervalo
  (decisão fechada — o usuário quer "o que estudar para esta aula" e a aula dura ~1h30). Sob card
  grosso isso gera repetição; aceita como custo do grão-unidade até a Spec B rachar o card.
- **Subunidade: opcional e cosmética.** O `.content_taxonomy.json` já carrega `subtopics` com
  `code` (ex. "1.1"); quando presente, vira rótulo de display. Nenhuma das dores operacionais
  (progressão, escopo) depende dela — ambas saem das datas. Curso sem subunidade funciona; com,
  ganha rótulo mais fino. **Nada quebra se faltar.**

### 4. Render

- **Dia-a-dia (fatia imediata — ver seção 6):** lista cada sessão sob sua data, com dia-semana,
  agrupado por semana ISO. **A fatia imediata entrega data + rótulo por dia (lê `sessions[]` que já
  existe) — SEM materiais por dia.** As linhas de material (`•`) dependem da atribuição por data
  (seção 3) e só aparecem depois dela.

```markdown
## Semana 3 · 09/03 – 13/03 — unidade-01
### Seg 09/03 — Lógica de Predicados
   • logicaPredicados_semantica.pdf          ← (depende da seção 3; NÃO está na fatia imediata)
### Qua 11/03 — Especificação de Conjuntos Indutivos
   • ConjuntosIndutivos.pdf · ExerciciosConjuntosIndutivos.pdf   ← (idem)
```

- **Escopo de prova no display:** "P1 (22/04) cobre até: Provas Interativas / Isabelle" —
  derivado do `topic_label` da última sessão no escopo.
- Dashboard (`src/ui/timeline_dashboard.py`): consome sessões (não só `period_start/end`).

### 5. Migração

**A inversão (bump v5 + primazia da sessão) é o DESTINO, não pré-requisito.** Nenhum dos 3
defeitos a exige: a fatia render lê `sessions[]` do v3 atual, o over-merge tem fix temporal local,
o bug de chave é o normalizador. Faseamento abaixo (a inversão entra só quando uma dor a exigir):

- **Fatia render + fix de normalização** (degrau imediato, sem schema novo). Ver seção 6.
- **Fix temporal do over-merge** em `_rows_belong_to_same_thematic_block` (`index.py:699-700`),
  atrás do eval-gate. NÃO depreciar a função ainda — só restringir por janela temporal.
- **Atribuição por data** (seção 3): `.card_block_map.json` **mantém `block_ids`/`dates`**; a
  atribuição passa a usar `dates` como chave e o slug vira projeção. NÃO migrar valores de
  `block_ids → slug` (o slug não é mais a chave). `computed_block_id` rebaixado a projeção derivada,
  leitura retro-compatível; `resolve_effective_block` (`file_map.py:556`) e `repo.py:913`
  continuam lendo o valor materializado. Teste de migração: manifest antigo lê sob schema novo.
- **`manual_unit_slug` / `manual_timeline_block_id` mantidos**; sem campo manual novo.
- **Inversão v5** (sessão primária, `source_kind` por-sessão, `assessment_scope_by_date` sobre
  sessões preservando o `seen` set): só quando uma dor a exigir (ex.: cadência que quebre o
  agrupamento). Atrás do eval-gate / gold / rebuild_diff, comparação contra gold por curso antes
  do cutover.
- **Guarda dura de slug:** validar `computed_unit_slug`/`computed_subunit_slug ∈ .content_taxonomy.json`
  para **toda** origem (auto E manual/congelado) — build falha, não warning. Pegaria o órfão real
  `21-logica-de-hoare` (override manual sem validação em `content_taxonomy.py:1098-1103`).

### 6. Fatia imediata (ortogonal, segura de shippar antes da inversão)

Render dia-a-dia que **lê o `sessions[]` que já existe** nos blocos atuais (v3) e o lista por data,
agrupado por semana ISO. Reescreve o corpo de `cronograma_detalhado_md` (`repo.py:927-970`, que hoje
itera blocos e ignora `sessions[]`). Não toca atribuição nem schema. Forward-compatível: quando a
sessão virar o átomo, este é o render natural.

- **Escopo honesto:** entrega **datas + rótulo do dia por semana ISO**, NÃO materiais por dia
  (materiais dependem da atribuição da seção 3). Mata ~60-70% da queixa real (render esconde os
  dias), que é o defeito mais visível.
- **Junto, no mesmo degrau:** fix do bug de normalização de chave — aplicar `norm_ascii_lower`
  (já existe em `helpers`, já usado pelo scorer difuso) nos dois lados do join exato
  (`lookup_card_blocks` em `card_block.py:131`; `_card_scoped_block` em `content_taxonomy.py:890`,
  hoje só `.strip()`) + nas chaves do `.card_block_map.json` no load. PR isolado, testável.
- Dashboard (`src/ui/timeline_dashboard.py`): consome sessões (não só `period_start/end`).

## Invariantes (não-negociáveis)

- **Chave de join da atribuição = data, por membership** (`session.date ∈ card.dates`, conjunto
  discreto — não intervalo). Não slug, não nome-de-card-string. O slug é projeção de display, nunca
  chave. Fallback de intervalo só explícito e logado (`span fallback`).
- Nenhuma suposição de **cadência** (semana = ISO sobre as sessões existentes). **Mas há uma
  suposição de FONTE assumida:** existe uma fonte com 1 linha datada por sessão (SARC hoje). Curso
  sem essa fonte cai no modo de degradação definido nos Riscos (não gera artefato vazio).
- Uma atribuição por material (sem duplicatas no manifest).
- SARC read-only (OpenSARC nunca é escrito).
- Projeções são funções puras/determinísticas (testáveis isoladas, mesmo input → mesmo output).
- Subunidade é opcional; ausência não quebra nada (precisão = grão disponível).
- `computed_*_slug` sempre ∈ `.content_taxonomy.json` (guarda dura, toda origem).
- LLM nunca é autoridade de runtime na atribuição (só sugestor congelado, se usado — ver Spec B).
- Reusar artefatos existentes (`.card_block_map.json`, `.content_taxonomy.json`, campos
  `computed_unit_slug`/`computed_subunit_slug` do manifest, `sessions[]` do `.timeline_index.json`,
  `.assessment_context.json`); **não criar arquivos nem campos novos paralelos**.

## Testes

- **Projeções (unit, fixtures de sessão):**
  - `weekly`: semana cruzando virada de ano; curso só-sexta (1 sessão/semana ISO); semana de
    feriado (0 sessões `class`); tópico atravessando 2 semanas ISO.
  - `thematic`: tópicos distintos não colam (caso que hoje over-merge cola); mesmo slug em
    sessões não-contíguas agrupa.
  - `assessment_scope`: P1 (início→P1), PN (P(N-1)→PN exclusivo/inclusivo), PS/G2 (semestre
    inteiro); prova cobre até a última sessão antes da data, exclui a seguinte (precisão
    subunidade sem campo).
- **Atribuição por data (membership):**
  - `session.date ∈ card.dates` → material atribuído; data fora → não atribuído.
  - tópico não-contíguo: `card.dates=[11/03, 06/05]` → sessão 01/04 NÃO recebe (membership não engole
    o gap, ao contrário do intervalo).
  - fallback span: card sem enumeração → `min..max` com `span_fallback:true`, logado.
  - card grosso: material em todas as datas do conjunto (grão-unidade), sem incluir gap fora do set.
- **Render:** snapshot do `CRONOGRAMA_DETALHADO.md` (dia-a-dia por semana) contra fixture.
- **Migração:** manifest antigo com `computed_block_id` lê corretamente sob o schema novo.

## Riscos / decisões em aberto

1. ~~Política de render multi-sessão~~ **FECHADA:** (a) repetir em cada sessão. Sob card grosso
   gera repetição — custo aceito do grão-unidade até a Spec B rachar o card.
2. **Grão do card grosso.** Card multi-tópico joga material em todas as sessões do intervalo de
   datas (grão-unidade). Resolvido na **ingestão** (Spec B: rachar card em seções mais finas), NÃO
   no consumo (desempate por arquivo reintroduziria difuso). Degradação graciosa: precisão
   = `min(grão-do-card, estrutura-disponível)`.
3. **Normalização de slug (pré-req real, menor que o escrito antes).** NÃO há duas autoridades de
   slug: `unit_index` (`file_map.py`) e `content_taxonomy` derivam **ambos** de
   `parse_units_from_teaching_plan` + o mesmo `normalize_unit_slug` (verificado). A divergência é de
   **normalização em pontos de entrada** (`.strip()` sem casefold em `timeline/index.py:95` e
   `content_taxonomy.py:890`). Pré-req = **normalizar `unit_slug` consistente em todo ponto (auto,
   manual, comparação) + teste** — não re-arquitetar autoridade. Como a chave de join virou a data,
   isso deixa de ser bloqueador da atribuição (vira robustez do rótulo).
4. **Curso sem fonte datada (fallback — hoje indefinido).** As projeções são puras sobre `sessions`;
   sem SARC (ou curso só-projeto / cronograma em prosa sem datas por linha), `sessions[]` sai vazio
   e TODAS as projeções saem vazias (artefato vazio, não degrada). Definir modo **"sem timeline"**:
   render por unidade/entrega em vez de por dia. Sem isso, o primeiro curso futuro sem SARC quebra
   o invariante. (O parser descarta linha sem `Data` em `helpers.py:485` — datas são condição de
   existência da sessão.)
