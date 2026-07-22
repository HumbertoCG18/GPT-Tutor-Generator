# Janela-de-prazo (TIER 2) — provider due-window do motor de atribuição

Data: 2026-07-22 · Status: DESIGN aprovado em brainstorm (decisões do user registradas) ·
Spec-mãe: `2026-07-01-motor-atribuicao-spec.md` (§3 TIER 2, §4.9) · Fase: F5 (rollout)

## §1 Problema e número de partida

As 8 rows TIER-2 fora-de-escopo do gold MF medem **1/8 pelo funil** (só `revisao-p1-gabarito`).
Alvo real = 3 rows dependentes de código: `t1-2026-1` (gold bloco-15), `t2-2026-1` (gold
bloco-16), `t1-2026-1-thy` (companion, gold bloco-15). Funil hoje: bloco-05/02/05 — errados.

Diagnóstico verificado (2026-07-22, dados reais do repo-tutor MF):

- `extract_assign_deadlines` (moodle_labels.py:195) colapsa a seção num único due — card
  `TDE Trabalho Discente Efetivo` ficou com `assign_due=2026-05-06` (aponta bloco-11; não
  serve nem pro t1 nem pro t2). A granularidade por-assignment EXISTE na API Moodle
  (`dates[dataid=duedate]` por módulo assign); a extração é que perde.
- O PDF do trabalho NÃO contém o due ("até a data limite indicada no Moodle") — parse de
  conteúdo é caminho morto. Materiais de aula nunca têm due (não são entregues) — decisão
  user: escopo por categoria, nunca por conteúdo.
- Semântica confirmada pelo gold: bloco cuja janela CONTÉM o due. Card 'Verificação de
  Programas' tem `assign_due=2026-06-10` ∈ bloco-15 `[2026-06-01, 2026-06-10]` = gold do t1.
- Legado `period_start < assign_due` (content_taxonomy.py:1165) é janela de MATERIAL — não
  contém os blocos true; NÃO é a semântica deste provider. Fica intacto (flag-OFF).

## §2 Decisões de design (fechadas com o user)

| # | Decisão | Escolha |
|---|---|---|
| D-A | Semântica | Bloco cujo `[period_start, period_end]` contém o due. |
| D-B | Straddle (due em gap/fora de bloco) | **Opção A**: bloco anterior mais próximo, band `media` + FLAG. Racional user: professores postam a sala de entrega em momentos inconsistentes — sinal de postagem é podre, só duedate estruturado vale. |
| D-C | Matching entry↔due | **Opção A — produtor burro, motor esperto**: extração emite lista sem colapsar; matching por stem/token vive no provider do motor (testável na régua, corrigível sem re-sync). |
| D-D | Band | `alta` = due estruturado + containment exato; `media` = due de parse-de-nome OU straddle (straddle sempre FLAG). |
| D-E | Sem due casado | `None` → funil byte-idêntico ao hoje. Due NUNCA decide fora do escopo TIER-2; provider nunca chuta. |

## §3 Produtor (aditivo, zero mudança de atribuição)

`src/builder/sources/moodle_labels.py`:

- Nova `extract_assign_deadlines_detailed(contents, year) -> {seção: [{name, due, source}]}`
  — mesma cascata da atual (1: `dates[dataid=duedate]` estruturado, `source="structured"`;
  2: data `(DD/MM[/AAAA])` no NAME de assign/forum com "entrega", `source="named"`), mas
  UM item por módulo, sem colapsar. Seção sem fonte fica fora (nunca inventa).
- `backfill_repo_signals_consumed` (moodle.py) grava a lista como `assign_dues` no entry do
  card map (merge aditivo). `assign_due` legado intacto — zero consumidores mudam.
- Ninguém lê `assign_dues` até o motor: flag-OFF permanece byte-idêntico.

## §4 Consumidor (motor, provider novo)

`src/builder/routing/motor/due_window.py` (pacote motor — regra "lógica nova SÓ no motor").

Roteamento em `apply.py` (cascata): pino manual > TIER-0 dup > **`tier2_due_scope(entry)`**
> `is_out_of_disamb_scope` > cascata normal.

- `tier2_due_scope(entry)`: categoria `trabalhos` OU `provas` OU (`codigo-*` E seção
  TDE-prefix). Split do `_OUT_CATEGORIES` atual: bibliografia/references/cronograma/apoio
  seguem FORA TOTAL (funil direto); trabalhos/provas/TDE tentam o provider.
- Provider: casa entry↔módulo por `norm_ascii_lower(título|id)` × `name` do módulo em
  `assign_dues` do card da entry; stem numérico `\bt(\d+)\b` tem prioridade (t1 ↔
  "Entrega T1"). 0-match ou empate → `None` → funil (preserva `revisao-p1-gabarito`).
- Due casado → bloco por containment (D-A) ou straddle (D-B) → `AnchorDecision`
  `provider="due-window"`, band por D-D. NUNCA disambiguator, NUNCA voto LLM (spec-mãe §3).
- Companion cai de graça: `t1-2026-1-thy` (codigo-professor, seção TDE, título "T1 2026 1")
  casa "Entrega T1" pelo mesmo matching — sem regra especial.

## §5 Régua e aceite (probe ANTES de código)

`scripts/fase5_prova_tier2.py` (7º probe da régua):

1. Pré-gate `audit_gold_freshness.py` (exit 0).
2. Universo declarado: 8 rows out-of-scope do gold MF; campo medido = atribuição EFETIVA
   via `resolve_temporal_block` (motor flag-ON não escreve temporal em fora-de-escopo;
   `temporal_block_id` antigo no CSV é ruído da era anchor_placement — não é o campo).
3. **Passo 1 (antes de qualquer código): medir e cravar baseline = 1/8.**
4. Pisos pós-implementação, FRAÇÃO EXATA (precedente F1): **4/8** · **confident-wrong 0**
   nas 8 · 6 probes existentes com números IDÊNTICOS (fase0/1/2-SO/2-TCC/3/4).
5. Unit tests determinísticos do matching/straddle com fixture sintética (sem rede).
6. Sem `assign_dues` no card map: probe imprime `assign_dues AUSENTE → baseline-only` e
   NÃO conta como PASS do alvo.

Medição FAIL = resultado honesto (spec-mãe §12 regra 4). Proibido re-tuning de piso.

## §6 Rollout, dependências e riscos

- Medição real do alvo exige **1 sync Moodle do MF** (ação user, GUI) pra popular
  `assign_dues` — entra na ordem do rollout F5 junto do seed do cache F3.
- **Risco nomeado**: se o Moodle não tiver `duedate` estruturado nos assigns do TDE nem
  data no nome do módulo → t1/t2 ficam no funil e o piso 4/8 FALHA honesto. Contingência
  fora da régua (decisão user na hora): pino manual (TIER 1) ou card-window manual.
- Os dues 2026-06-10 (t1) / 2026-06-29 (t2) usados nos exemplos são INFERÊNCIA do gold —
  valor real só pós-sync.

## §7 Fora de escopo (dívidas nomeadas)

- **Bibliografia = caso à parte (decisão user 2026-07-22)**: tutor deve passar a CONSUMIR
  bibliografias sem estourar o limite de projeto Claude/GPT — brainstorm/spec próprios,
  não neste provider. Até lá: bibliografia/references/cronograma seguem fora total do motor.
- `plano` = funil deliberado (plano de ensino não pertence a bloco).
- `eth2` → bloco-12 = erro residual conhecido; caminho é pino manual ou a refatoração de
  ingestão de referências (dívida já nomeada na spec-mãe).
- `revisao-p1-gabarito`: pino trivial opcional na GUI (funil já acerta; não depende disto).

## §8 Regras herdadas que valem aqui

READ-ONLY nos repos-tutor (exceto reprocess autorizado do rollout) · gold só ganha coluna ·
lógica nova só motor/scripts, nunca engine.py (guard AST) · google-genai lazy · UTF-8 shim
em scripts novos · flag-OFF byte-idêntico como invariante de qualquer mudança.
