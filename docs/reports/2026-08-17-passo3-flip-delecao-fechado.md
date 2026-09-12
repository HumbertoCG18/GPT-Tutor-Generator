# PASSO 3 FECHADO — flip default ON + deleção do funil legado (campanha 3, cutover)

as-of: 2026-08-17 · branch `feat/motor-atribuicao` · sessão única (medição → flip → deleção)

**Estado final: 100% da atribuição (bloco/unit/subunit) roda no motor
(`concept_resolver` + `apply_unit_subunit_fields`). Funil legado DELETADO.
Serializador de índice ÚNICO (v4). 5 cursos de produção reprocessados e
commitados. Suite 1852 passed / 1 skipped / 0 failed.**

## Etapa 1 — Medição pré-flip (relatório próprio)

`docs/reports/2026-08-17-medicao-pre-flip-5cursos.md` — 4 gates verdes
(golds unit 5/5 sem regressão, pinos 29/29, rebuild_diff 5/5 = 0, M7 caso
único). Driver commitado: `scripts/measure_flip.py`.

## Etapa 2 — Flip (default ON)

- Código: `pedagogical_regeneration.py` — `use_concept_resolver` default
  `False → True` (site único de leitura). Opt-out por curso =
  `feature_flags {"use_concept_resolver": false}`. Commit `c5ecb5f`.
- Sentinela re-versionada: flag AUSENTE = motor ON; teste novo de opt-out
  explícito.
- Curadoria pré-flip: pino `revisao_p1_gabarito → bloco-07` (gêmeo do pino
  `revisao_p1`; motor concept-fused puxava pro bloco-04 de conteúdo — régua
  teria caído 50→49/57; MF `9f7972c`).
- Rollout: 5 repos reprocessados e commitados (MF `9785b56` · SO `168abc0` ·
  ES2 `276cfb7` · IA `f4ca5e1` · TCC `b3fa20d`), todos os gates verdes
  (golds idênticos ao sandbox, régua MF 50/57, pinos 0 violados,
  rebuild_diff 0).
- Sentinelas casos-chave: 7 casos diffaram (esperado), revisados um a um e
  re-baselined. Neutros/melhora: MF `introducao`/`t1-2026-1` (erros de régua
  pré-existentes nos DOIS lados), TCC `aula-01`/`aula-06` (revisão de base →
  u01, plausível correção). **Candidatos a pino de curadoria (rótulo do
  user)**: SO `0704-threads` (u02→u01, parecia certo antes) e IA
  `introducao-a-busca-informada` (→bloco-01 band baixa) — sem gold
  por-material, não bloquearam gate nenhum.

## Etapa 3 — Deleção por lista nomeada (commit `df86203`, -4747/+334)

Tudo conforme resoluções travadas 2026-07-03 (tracker, Mapa de deleção):

- **Mortos**: `resolve_unit_block_tags` · `_best_instructional_block_fallback`
  · `_card_scoped_block` · `score_entry_against_timeline_block` ·
  `block_token_weights` · `select_probable_period_for_entry` ·
  `TOOL_TOKENS/BOOST/PENALTY` (S4; `TOOL_EXTENSIONS` FICA — entry_signals) ·
  ramo fallback keyword de unidade do index (`_assign_timeline_block_to_unit`,
  `_vote_unit_from_topic_candidates`, `_score_timeline_row_against_unit`,
  `T.BLOCK_UNIT_*`/`T.VOTE_*`) · fallback S2 do `cronograma_health`
  (aposentado; sem janela → `[]`, material segue acionável) · R4
  (`_inject_block_uuids_from_ledger`).
- **Scripts aposentados no mesmo commit**: `retag_manifest.py`,
  `eval_assignments.py`.
- **Portes no mesmo commit**: limpeza `_NO_TIMELINE_CATEGORIES` (B1) →
  `apply_concept_resolver`; gate "só re-resolve quem tinha bloco" INVERTIDO —
  **o motor agora SEMEIA entries novos** (teste
  `test_motor_semeia_entry_sem_computed`).
- **Testes**: 12 arquivos-fantasma deletados; 3 S4b movidos pra
  `test_entry_signals_materials`; invariantes migrados pro motor
  (no-timeline, tag `bloco:` display, learned boosts do tag_profile —
  fecha parte do M8, ordem do pipeline); fixtures re-versionadas pra rota
  posicional (planos com ≥2 unidades, produção-like); guard do motor verde
  o tempo todo.

### Achado da deleção: remoção do viés P3.1 (eco de auto-confirmação)

O gate de neutralidade (reprocess de cópia da produção com código
pós-deleção) mostrou **zero diff em bloco/pinos/índice**, mas mudanças em
massa de `unit_match_confidence`/`subunit_match_confidence` e ~15 slugs de
unit/subunit por material. Causa: `refresh_manifest_auto_tags` reconstrói
`auto_tags` do zero e era o FUNIL quem re-escrevia `unit:`/`subunit:` antes
do apply — o scorer de unidade lia essas tags como sinal (**P3.1,
"auto-confirmação", catalogado como ruído no plano mestre 2026-06-11**).
Sem o funil, o eco morre e as confidences ficam honestas. Idempotência
verificada: 2º reprocess = **0 diffs**. Golds/régua/pinos inalterados.
Produção assentada no commit por curso ("reprocess pos-delecao").

## Serializador único + item 8 (commit `037ddbe`)

- **Item 6**: `_serialize_timeline_index` (fantasma v4 só-testes, filtrava
  admin) DELETADO; único = `core_utils.persist_enriched_timeline_index`;
  testes fantasma migrados; guard anti-reintroducão.
- **Item 8a**: bump v3→v4 no persist — versão unificada com o schema
  (`validate_timeline`, const 4). Índices de produção gravados em v4
  (commits "indice v4" nos 5 repos).
- **Item 8b**: vocabulário exam unificado no classifier
  (`STRONG_EXAM_RE`/`WEAK_EXAM_TOKENS` públicos); motor sem import privado.
- **Item 8d**: `rebuild_timeline --write` atualiza `.content_taxonomy.json`.
- **Itens 8c/8e**: já entregues em campanhas anteriores (montador único +
  warning de degradação) — verificado, nada a fazer.

## Gates finais (produção, as-of fechamento)

| gate | resultado |
|---|---|
| suite | 1852 passed / 1 skipped / 0 failed |
| golds unit | ES2 7/7 · IA 9/10 · MF 12/14 · SO 9/11 · TCC 13/13 (= baseline) |
| régua MF (ground-truth) | 50/57 (87.7%) |
| pinos | 30 totais, 0 violados |
| rebuild_diff | 5/5 cursos, 0 blocos mudados |
| índice | v4 nos 5 cursos |
| guard motor | verde |

## Dívidas que SEGUEM abertas (tracker)

- M7 (calibração cross-escala de confiança) — 1 caso único conhecido.
- M4/M5/M6 e resto do M8 — oportunistas.
- Curadoria potencial: pinos SO `0704-threads` e IA `busca-informada`
  (aguardam rótulo do user).
- 2.7 signal_token_set · 2.13 smoke · 3.1-3.3 estruturais · campanha web.
