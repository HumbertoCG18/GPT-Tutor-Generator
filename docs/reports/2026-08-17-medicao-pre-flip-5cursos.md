# Medição pré-flip `use_concept_resolver` — 5 cursos (passo 3, etapa 1)

as-of: 2026-08-17 · HEAD `b4d119d` · sandbox read-only · produção intocada

## Método

Mecânica da F4 (`docs/reports/2026-08-14-f4-medicao-unit-motor.md`), agora com driver
COMMITADO (`scripts/measure_flip.py` — fecha a limitação "scripts ad-hoc irreprodutíveis"
registrada na F4). Por curso (MF/SO/ES2/IA/TCC):

1. `robocopy <repo-tutor produção> <scratchpad>/sandbox-<SIGLA> /E /XD .git`
2. **BEFORE** (flag OFF): `reprocess(sandbox, [], store=FixedStore(perfil real))` →
   snapshots `manifest_before.json` / `timeline_index_before.json`. `FixedStore` devolve o
   perfil real do `subjects.json` (leitura pura; produção nunca escrita; `root_dir` = sandbox).
3. **AFTER** (flag ON): `reprocess(sandbox, ["use_concept_resolver"], store=...)` → snapshots
   `_after`.
4. Análise: `eval_units.score_course` contra os 2 índices · sobrevivência de pinos
   (`manual_timeline_block_id` vs `computed_block_id` pós-apply, pino resolvido a uuid
   canônico via índice) · delta `computed_block_id`/`computed_unit_slug`/`computed_subunit_slug`
   por entry (keyed `entry.id`) · candidatos M7 (mesmo bloco, unit muda).
5. `scripts/rebuild_diff.py` em produção (dry-run, read-only), separado.

Reports JSON por curso ficaram no scratchpad da sessão (reproduzíveis com o driver commitado).

## Placar (gates da etapa 1)

| curso | eval gold BEFORE→AFTER | mismatches | pinos (violados) | delta bloco | unit | subunit | M7 |
|---|---|---|---|---|---|---|---|
| MF  | 12/14 → 12/14 | bloco-07, bloco-11 (idênticos, política) | 17 (**0**) | 23/67 | 10 | 12 | 1 |
| SO  | 9/11 → 9/11   | bloco-01, bloco-02 (idênticos)           | 4 (**0**)  | 15/42 | 10 | 11 | 0 |
| ES2 | 7/7 → 7/7     | —                                        | 1 (**0**)  | 17/35 | 7  | 14 | 0 |
| IA  | 9/10 → 9/10   | bloco-01 (idêntico)                      | 4 (**0**)  | 31/62 | 7  | 16 | 0 |
| TCC | 13/13 → 13/13 | —                                        | 3 (**0**)  | 17/27 | 8  | 7  | 0 |

- **Gate golds unit 5/5: PASS.** Zero regressão, zero novo erro; listas de mismatch
  byte-idênticas BEFORE/AFTER nos 5 cursos.
- **Gate pinos 100%: PASS.** 29 pinos totais, 0 violados/perdidos. 26 no escopo do motor
  honrados (`computed_block_id` == uuid canônico do pino) — **inclui `tiposindutivos` (MF), o
  caso do bug F3/C1: pino agora HONRADO em curso real (primeira medição do fix `636f299`)**.
  3 pinos MF `fora_do_motor` (bibliografia/references — `github-repo`/`url`, computed vazio nos
  DOIS lados, idêntico à produção atual): flip-neutros, comportamento pré-existente.
- **Gate `rebuild_diff` produção: PASS.** 5/5 cursos com 0 blocos mudados (HEAD atual não
  drifta os índices gravados; warnings "heading skip" de md curado ausente = ruído conhecido).
- **M7 (calibração cross-escala): NÃO entra no pré-flip.** 1 único caso nos 5 cursos
  (MF `colecoes-conjuntos`, conf 0.80→0.45, mesmo caso da F4) — não é inversão "em escala"
  (condição do handoff pra exigir cap/normalização antes do flip). Dívida M7 permanece aberta
  no tracker como estava.

## Delta de atribuição (informacional — o que as sentinelas vão mostrar no flip)

`computed_block_id` muda em: MF 23/67 · SO 15/42 · ES2 17/35 · IA 31/62 · TCC 17/27 —
**100% troca de bloco** (0 ganho/0 perda de cobertura em todos; cobertura `bloco:` idêntica
BEFORE/AFTER, ex. MF 66/67, SO 42/42). É o território motor≠funil já conhecido (F3/F4);
sem gold por-material, as trocas não são prováveis caso a caso — o gate mensurável (gold por
bloco) empata e os pinos seguram os casos curados à mão.

Coerência com a medição F4 (MF): unit **10** vs 11 da F4 — `tiposindutivos` SAIU da lista de
unit divergente (pino honrado pós-C1, era o caso-bug); subunit **12** vs 11 da F4 — mesmos 11 +
`Tiposindutivos` (consequência direta do pino honrado: subunit agora restrita à unidade final
do bloco pinado). As duas diferenças rastreiam exatamente o fix C1 — sem surpresa nova.

## Veredito

**GO pra etapa 2 do passo 3 (flip default ON).** Todos os gates da etapa 1 verdes. Protocolo
do flip (handoff): snapshot antes de reprocess em produção, sentinelas vão diffar — revisar
caso a caso e re-versionar conscientemente.
