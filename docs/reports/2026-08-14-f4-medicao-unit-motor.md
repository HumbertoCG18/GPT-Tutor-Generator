# F4 Task 5 — Medição de prontidão pro flip `use_concept_resolver` (unit/subunit, MF)

as-of: 2026-08-14 · sandbox read-only · produção intocada

## Método

Cópia integral do `Metodos-Formais-Tutor` pro scratchpad (sem `.git`, robocopy `/E /XD .git`).
Reprocessado headless 2x via `scripts/reprocess_assignments.reprocess()` (mesmo motor do botão
"Reprocessar Repositorio"), com **perfil real da MF** (`SubjectStore().get("Metodos-Formais")`,
leitura read-only do `subjects.json` de produção — sem gravação) e `root_dir` trocado pro sandbox
(precedente T12, `docs/reports/2026-08-11-t12-sandbox-aula13-tcc.md`):

1. **BEFORE** (flag OFF, código atual): `reprocess(sandbox, [], store=<store que sempre devolve
   o perfil real>)` → `manifest.json` + `course/.timeline_index.json` copiados pra
   `manifest_before.json` / `timeline_index_before.json`.
2. **AFTER** (flag ON): `reprocess(sandbox, ["use_concept_resolver"], store=...)` → mesmos
   arquivos copiados pra `manifest_after.json` / `timeline_index_after.json`.

Rodar o BEFORE pelo mesmo caminho de código do AFTER (em vez de usar o manifest de produção
como "antes") isola o diff no flip da flag — não mistura drift de código entre o último build real
e o HEAD atual.

Produção NUNCA escrita: `SubjectStore()` só foi `.get()` (leitura); nenhuma chamada `.add()`/
`.save()`. O `root_dir` passado ao `RepoBuilder` é sempre o path do sandbox. Scripts do driver
ad-hoc (`run_sandbox.py`, `diff_manifest.py`, `eval_sandbox.py`, `diff_block_context.py`) ficaram
no scratchpad da sessão, não commitados.

Comandos (equivalentes; script inline no scratchpad reusa `reprocess_assignments.reprocess` e
`eval_units.score_course` diretamente):

```bash
robocopy "<repo-tutor MF producao>" "<scratchpad>/mf-sandbox" /E /XD .git
python <scratchpad>/run_sandbox.py baseline   # BEFORE: reprocess(sandbox, [])
python <scratchpad>/run_sandbox.py flagon     # AFTER:  reprocess(sandbox, ["use_concept_resolver"])
python <scratchpad>/diff_manifest.py          # diff campos unit/subunit por entry
python <scratchpad>/eval_sandbox.py           # eval_units.score_course contra os 2 indices
```

## Números

- **Cobertura de bloco**: 66/67 em ambos os lados (idêntica). O 1 residual (`plano cronograma`,
  categoria de cronograma, não é material de aula) não muda com a flag — não é afetado pelo motor
  em nenhum dos dois lados. Confirma a nota de escopo do plano: motor só sobrepõe entries com
  `computed_block_id`.
- **`computed_unit_slug` efetivamente alterado**: **11/67** entries. Mais 1 entry
  (`revisao-p1-gabarito`) com slug IDÊNTICO antes/depois (unidade-02 → unidade-02) e só
  `unit_block_conflict` passando de `{}` pra preenchido — entra na tabela UNIT abaixo por
  completude (campo mudou, slug não), não conta pro total de slug alterado. **12 linhas na tabela
  UNIT (11 slug-alterado + 1 só-conflict)**.
- **`computed_subunit_slug` divergente**: **11/67** entries.
- **Tags `unit:`/`subunit:` em `auto_tags`**: a métrica bruta original (script ad-hoc
  `diff_manifest.py`) não bate com a aritmética das duas listas caso-a-caso abaixo e o script não
  sobrevive à limpeza do sandbox (não commitado; ver Limitações) — descartada. Fonte de verdade:
  as listas UNIT (12 linhas) + SUBUNIT (11) abaixo, 3 em overlap (`exercicios-arrays`,
  `formalizacaoalgoritmos-recursao`, `hoare`) → **20 entries únicas** com algum campo unit/subunit
  alterado.
- **`unit_block_conflict` passa a não-vazio** em 6 das 12 linhas UNIT (era `{}` no BEFORE em
  todas as 12).

## Placar golds (`scripts/eval_units.py` / `gold_units_MF.csv`)

`gold_units_MF.csv` existe (`tests/fixtures/eval/gold_units_MF.csv`, 14 linhas com `true_unit`
preenchido). Rodado via `eval_units.score_course` contra os 2 índices do sandbox:

| | BEFORE (flag OFF) | AFTER (flag ON) |
|---|---|---|
| Placar | **12/14 (85.7%)** | **12/14 (85.7%)** |
| Mismatches | bloco-07, bloco-11 | bloco-07, bloco-11 (idênticos) |

**Empate exato, zero regressão, zero novo erro.** Os 2 misses são pré-existentes e de **política**,
não de matcher (conforme já registrado no CSV e no placar oficial da campanha 2,
`docs/reports/pendencias.md` linha ~1546, "Misses restantes = 100% POLÍTICA"):
- `bloco-07` (review véspera de P1): regra é "unidade da prova", índice zera por ser `kind=review`.
- `bloco-11` (deliverable com aula de conteúdo embutida): índice zera por política de
  `kind=deliverable`, rótulo gold é a verdade de conteúdo.

O gate histórico da campanha 2 (`docs/reports/pendencias.md`, "placar eval_units 5/5: MF 12/14
(85.7)...") é sobre 5 **cursos** batendo cada um a própria baseline — não 5 linhas de gold da MF.
Este Task 5 mede só MF (escopo do brief); MF bate a própria baseline (12/14) com a flag ON,
byte-idêntica ao placar flag-OFF já homologado.

## Lista de divergências com veredito

### UNIT (`computed_unit_slug`) — o sinal a escrutinar

Cruzado com `computed_block_id` antes/depois (script `diff_block_context.py`) para separar
"unit mudou porque o bloco motor é outro" (propagação esperada de trabalho já homologado em
campanhas anteriores, fora do escopo desta Fase 4) de "unit mudou com o bloco igual" (candidato a
bug novo do wiring desta fase):

| entry | unit antes → depois | bloco antes → depois | veredito |
|---|---|---|---|
| `arvores` | unidade-01 → unidade-03 | bloco mudou (5599d0.. → 7a5e29..) | propagação do bloco motor |
| `colecoes-conjuntos` | unidade-02 → unidade-01 | **mesmo bloco** (de7d1b7.., conf 0.80→0.45) | ver nota abaixo |
| `exercicios-arrays` | unidade-02 → `""` | bloco mudou (95d7c9.. → c9f5f7..) | propagação do bloco motor |
| `exercicios-conjuntos` | unidade-02 → unidade-01 | bloco mudou (95d7c9.. → de7d1b..) | propagação do bloco motor |
| `formalizacaoalgoritmos-recursao` | unidade-01 → `""` | bloco mudou (7ccdaf.. → c9f5f7..) | propagação do bloco motor |
| `hoare` | unidade-02 → `""` | bloco mudou (171a1a.. → c9f5f7..) | propagação do bloco motor |
| `listas` | unidade-01 → unidade-03 | bloco mudou (5599d0.. → 7a5e29..) | propagação do bloco motor |
| `revisao-p1-gabarito` | unidade-02 → unidade-02 (**slug IDÊNTICO**, conflict novo) | bloco mudou (1dd6f1.. → 7ccdaf..) | não conta como unit alterada — só ganha `unit_block_conflict` |
| `t1-2026-1-thy` | unidade-01 → unidade-02 | bloco mudou (7a5e29.. → 7ccdaf..) | propagação do bloco motor |
| `t2-2026-1` | unidade-01 → `""` | bloco mudou (1e7362.. → c9f5f7..) | propagação do bloco motor |
| `tiposindutivos` | unidade-02 → unidade-01 | bloco mudou (95d7c9.. → 7ccdaf..) | pino manual descartado pelo motor (bug F3: concept_resolver.py:250-255 casa display, pino é uuid) — NÃO é propagação benigna |
| `verificacaomodelos` | unidade-03 → `""` | bloco mudou (a6ac04.. → c9f5f7..) | propagação do bloco motor |

(NB: os dois "11/12" a seguir são eixos independentes que coincidem em contagem —
`computed_block_id` mudou em 11 das 12 linhas [todas exceto `colecoes-conjuntos`], enquanto o
slug de unidade mudou em 11 das 12 linhas [todas exceto `revisao-p1-gabarito`]. Não é o mesmo
conjunto de 11.)

**11/12** têm `computed_block_id` diferente entre BEFORE/AFTER — a mudança de unidade é
consequência direta e coerente de `reconcile_unit_with_block` (função ÚNICA, reusada sem
alteração — `src/builder/routing/file_map.py:651`, com teste próprio em
`tests/test_reconcile_unit_block.py`) receber um bloco vencedor diferente. O bloco em si é
produto do resolver de bloco (`concept_resolver`), já homologado em campanhas anteriores à Fase 4
(fora do escopo desta task) — não é código novo desta fase.

**1/12** (`colecoes-conjuntos`) mantém o **mesmo** `computed_block_id`, mas
`computed_block_confidence` cai de 0.80 (funil) pra 0.45 (motor) para esse mesmo bloco — o que
inverte o desempate em `reconcile_unit_with_block` (`block_confidence >= unit_confidence`): no
BEFORE o match bruto de unidade tinha confiança baixa/vazia e herdou do bloco
(`herdada_do_bloco`); no AFTER o match bruto teve confiança alta (0.886) e o bloco (agora com
confiança menor) perdeu o desempate, gerando `unit_block_conflict`. A diferença de origem é a
**confiança de bloco** calculada pelo motor vs funil pro mesmo bloco vencedor — também território
do resolver de bloco (pré-Fase 4), não do wiring novo de unit/subunit.

**Nenhuma das 12 linhas da tabela UNIT (11 com slug alterado + 1 só-conflict) é atribuível a um
bug no código NOVO desta fase** (`apply_unit_subunit_fields`/wiring do reconcile) — todas
rastreiam a um input diferente (bloco ou confiança de bloco) vindo do resolver de bloco. A raiz é
da F3 (`_manual_block_id`, `concept_resolver.py:250-255`), mas **NÃO era conhecida nem homologada**
— é bug descoberto por esta review (caso `tiposindutivos`, pino uuid descartado). **Ressalva
honesta**: não existe gold MATERIAL-a-material pra MF (só gold por BLOCO, `gold_units_MF.csv`),
então não dá pra afirmar que as 11 reatribuições de slug estão CORRETAS em verdade-terreno — só
que são coerentes e explicáveis pela mecânica, e que não regridem o único gate mensurável hoje
(bloco, 12/14 idêntico).

### SUBUNIT (`computed_subunit_slug`) — correção esperada por design

Confirmado por leitura de código, não só por interpretação: o legado
(`content_taxonomy.py:1163-1191`) casa subunidade **ANTES** de reconciliar unidade×bloco
(usa `winning_unit_slug=resolved_unit_slug`, o match BRUTO pré-reconcile; o reconcile só roda
depois, `:1354`). O motor (`resolver_apply.py:204-266`) reconcilia **PRIMEIRO** (`:226`) e casa
subunidade depois usando `winning_unit_slug=reconciled` (`:266`, unidade FINAL pós-reconcile).

Isso bate exatamente com a interpretação do brief: quando a unidade bruta pré-reconcile diverge
da unidade final reconciliada, o legado busca o tópico de subunidade no pool ERRADO (unidade
bruta) e o motor busca no pool CERTO (unidade final). Exemplo concreto: `classes-parte1` —
unit final igual nos dois lados (`unidade-02-verificacao-de-programas`), mas subunit
BEFORE = `softwares-de-suporte-a-verificacao-formal-de-modelos` (tópico da unidade-**03**,
pool errado) → AFTER = `verificacao-de-programas` (tópico da unidade-**02**, pool certo).

11 diffs, todos no mesmo padrão (3 têm unit também divergente — `exercicios-arrays`,
`formalizacaoalgoritmos-recursao`, `hoare` — e para esses o pool mudou porque a unidade final
mudou; os outros 8 têm unit final igual e só o pool de busca do subunit mudou pela ordem):
`classes-parte1`, `classes-parte2`, `colecoes-arrays`, `colecoes-sequences`, `exercicios-arrays`,
`exercicioscorrecaoinducaomatematica`, `exerciciosespecificacao`,
`exerciciosespecificacao-respostas`, `formalizacaoalgoritmos-recursao`, `hoare`,
`introducao-zip`.

**Veredito: correção esperada (design), não regressão.** Consistente com a nota de escopo do
plano (1.2 bloco→reconcile pós-`attach_block_summary_fields` fecha só o caminho de unidade;
resync de `auto_tags` é passo 2 da campanha, fora desta task).

## Limitações

- **Scripts ad-hoc da medição não commitados** (`run_sandbox.py`, `diff_manifest.py`,
  `eval_sandbox.py`, `diff_block_context.py`, todos no scratchpad da sessão): irreprodutíveis sem
  re-rodar o sandbox (já removido, conforme instrução de limpeza). A métrica de tags
  `unit:`/`subunit:` descartada acima é o exemplo concreto — o número original não bate com a
  aritmética das listas caso-a-caso e não há como recomputar sem repetir o processo do zero.
- Sem gold MATERIAL-a-material pra MF: as divergências caso-a-caso (11 unit-slug + 11 subunit,
  3 em overlap) são coerentes/explicadas pela mecânica, não provadas individualmente contra
  verdade-terreno.
- A medição não verificou a sobrevivência dos 17 pinos manuais (`manual_timeline_block_id`) da MF
  nem rodou o diff global de `computed_block_id` por entry — `eval_units` mede unit por BLOCO,
  cego a pinos manuais (o caso `tiposindutivos` só apareceu por inspeção caso-a-caso da tabela
  UNIT, não por um gate dedicado a pino).

## Veredito go/no-go

**GO CONDICIONADO** — não GO puro. No gate mensurável definido pelo handoff (placar
`eval_units.py`/`gold_units_MF.csv`, nível de BLOCO): MF empata a própria baseline **12/14
(85.7%)** com a flag ON, zero regressão, zero novo erro, mesmos 2 misses de política. O resíduo
de cobertura (1/67, categoria de cronograma) é idêntico nos dois lados. Mas esse gate é cego a
pino manual (ver Limitações) e a review encontrou 1 caso concreto de pino descartado
(`tiposindutivos`). **Condicionado a**: gaps 1.2/1.3 do plano + o motor honrar pinos manuais em
uuid (fix em `_manual_block_id`, passo 2 da campanha).

**Ressalva não-bloqueante**: as 11 reatribuições de unidade a nível de MATERIAL (entry, slug
efetivamente alterado — + 1 caso `revisao-p1-gabarito` com slug idêntico e só conflict novo) não
têm gold próprio pra verificação individual — são coerentes com a mecânica (bloco motor diferente,
já homologado fora desta fase) mas não есtão provadas caso-a-caso contra verdade-terreno. Se o
controlador quiser fechar esse gap antes do flip real de produção, é trabalho de gold
MATERIAL-a-material (fora do escopo desta Task 5, que mediu contra o gold de BLOCO existente).
As 11 divergências de subunit são correção esperada por design (ordem pré vs pós-reconcile),
confirmada por leitura de código.
