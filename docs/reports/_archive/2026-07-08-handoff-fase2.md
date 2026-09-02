# Handoff — FASE 2 do Motor de Atribuição (sessão zerada)

date: 2026-07-08
branch: `feat/motor-atribuicao` (NÃO mergeada; decisão de merge pendente do user)
sessões anteriores: FASE 0 (2026-07-07) + FASE 1 + auditoria do gold (2026-07-08), ambas nesta branch

## 1. Estado — o que está PRONTO

- **FASE 0 entregue** (12 commits `f75d22b..fff7d47`): pacote isolado `src/builder/routing/motor/`
  (contracts, window_provider P1/P2, disambiguator IDF len-norm + session-label 1ª classe,
  anchor_engine). READ-ONLY, **NÃO integrado ao pipeline** (integração = FASE 4). Guard AST de
  imports (`tests/test_motor_import_guard.py`) proíbe os 3 símbolos condenados + star-imports.
- **FASE 1 entregue** (11 commits `2e49ceb..HEAD`): gate D4 calibrado com recall medido. Review
  final whole-branch: **Ready to merge — Yes**. Levers: desconto nome-do-curso
  (`MotorContext.course_name`), gate por token discriminante (D4 literal; neutro no corpus MF —
  proteção estrutural), `MARGIN_TAU=0.55` (grade 36 pontos). Novos: `motor/metrics.py`
  (`gate_report` puro), `scripts/fase1_recall_gate_MF.py` (harness externo READ-ONLY).
- **Auditoria do gold MF (2026-07-08, sign-off user)**: 7 rows do `ground_truth_MF.csv` tinham
  `true_block_id` STALE (drift posicional `bloco-NN` pós-reprocess — bloco-09 de hoje é a prova P1).
  Re-rotuladas por conteúdo. A "pendência de curadoria bloco-09" da FASE 0 era diagnóstico ERRADO
  (card map estava certo) — morta no tracker.

## 2. Números vigentes (régua corrigida)

| Métrica | Valor | Guard |
|---|---|---|
| Acurácia escopo-disamb MF (par-colapsada) | **82.8% (48/58)** | piso HARD 59.7% |
| Confiante-errado | **1** (`exerciciosdafny2`) | `BASELINE_CONFIANTE_ERRADO=1` (fase0) |
| Contenção-fora | **0** | `BASELINE_CONTENCAO_FORA=0` (fase0) |
| Recall do gate | **0.900 (9/10)** | `BASELINE_RECALL=9/10` (fase1, veredito composto) |
| Fila do flag | 37 (28 certos, 9 errados) | — insumo do go/no-go FASE 3 |
| Gold embutido (CI) | contenção 100% / conf-errado 0 | `tests/test_motor_golden_mf.py` |
| Suite | 1701 passed / 4 skipped | — |

Constantes: `MARGIN_TAU=0.55`, `W_SESSION_LABEL=1.0`, `W_TOPIC=0.6` (disambiguator.py).
Probes rodam EM PAR: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
— ambos PASS exit 0 hoje.

Composição dos 10 pares errados restantes (tabela completa no report): 6 = cluster indução×Isabelle
05↔06 (grão-de-semana; LLM NÃO converte essa classe — MARCO 1); 1 = exerciciosdafny2 (confiante,
candidato TIER 3); 2 = títulos 100% stem-genérico; 1 = tiposindutivos. **~7/10 fora do alcance de
scorer lexical → próximo ponto de acurácia = FASE 2/pinos, não calibração.**

## 3. Artefatos-chave

- Spec (governa tudo): `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` (§7 fases; §6 aceite)
- Report FASE 1 + adendos: `docs/reports/2026-07-07-fase1-recall-report.md`
- Planos executados: `docs/superpowers/plans/Feitos/2026-07-03-fase0-motor-atribuicao.md` e
  `Feitos/2026-07-07-fase1-gate-d4-recall.md`
- Tracker: `docs/reports/pendencias.md` (entradas FASE 0/FASE 1 + adendo auditoria)
- Ledger de execução: `.superpowers/sdd/progress.md` (git-ignored; histórico completo de decisões)
- Golds externos: `docs/reports/ground_truth_{MF,IA,SO,TCC,ES2}.csv` — TODOS existem rotulados
  (MF corrigido; os outros 4 NÃO auditados pós-reprocess)

## 4. PRÉ-FLIGHT da FASE 2 (obrigatório antes do plano)

1. **Auditar frescor de `ground_truth_SO/TCC/IA/ES2.csv` vs timeline atual dos repos-tutor**
   (mesmo método da auditoria MF: bloco true existe? é admin/prova? overlap lexical zero? par
   inconsistente? true fora da janela?). O drift posicional que escondeu 12pp no MF pode estar
   nos 4. Detector: cuidado com substring "prova" casando "provador" (falso-alarme conhecido).
   Toda re-rotulagem = sign-off do USER (gold é verdade humana).
2. Considerar migrar os CSVs pra `block_uuid` (imune a re-numeração) — decidir com o user se
   entra na FASE 2 ou fica dívida.

## 5. Próximo passo — FASE 2 (spec §7)

Providers P3 (SO data-no-nome) + P4 (TCC topic-bridge). Aceite (spec §6): P3 = data → exatamente
1 bloco (probe 9/9, 0 colisão), cobertura ~45% dos materiais SO; P4 = ≥4/5 pinos manuais
reproduzidos, cobertura >26%, resíduo NP-completude cai pro TIER 3 SEM errar confiante.
PROIBIDO week-math ordinal-linear (F-TCC). "Semana N - Tópico" do TCC: parsear o TÓPICO, nunca o N.

Depois da FASE 2: **go/no-go da FASE 3 (LLM) = decisão do USER** (sign-off condicional §9 do spec).
Nota honesta: o caso do LLM ENFRAQUECEU pós-auditoria — resíduo confiante = 1, e a maior classe
flagada (cluster 05/06) é a que o MARCO 1 provou que o voto não converte. Sem LLM, flagged = fila
humana no Dashboard (37 itens MF).

## 6. Disciplinas não-negociáveis (herdadas + novas)

- Tudo que CC roda sozinho é **READ-ONLY nos repos-tutor** (`~/Documents/GitHub/*-Tutor`).
  Mutação do vivo (reprocess, curadoria) = ação do USER na GUI.
- Lógica nova SÓ em `src/builder/routing/motor/` (e `scripts/`); NUNCA `engine.py`.
- ANCHOR-ONLY; funil (`computed`) = piso; integração só na FASE 4.
- **NÃO commitar sem pedido explícito do user.**
- Guard AST: proibido importar `block_token_weights`, `score_entry_against_timeline_block`,
  `select_probable_period_for_entry` no pacote do motor. Whitelist: concept_resolver puro,
  card_block, thresholds, entry_signals, text/*.
- UTF-8 shim em todo script novo (console Windows cp1252). PT-BR nos docs.
- MARCO 0/1 NÃO se re-rodam (provas cacheadas).
- Gold = verdade humana: re-rotulagem exige sign-off do user, caso a caso.
- Probes fase0+fase1 rodam em par (os vereditos assumem isso).
- Pre-commit hook pode imprimir UnicodeEncodeError não-fatal — verificar commit com `git log -1`.
- `.claude/settings.local.json` nunca commitar; CLAUDE.md/settings do graphify fora do escopo.

## 7. Comando de partida (colar na sessão nova)

> Leia `docs/reports/2026-07-08-handoff-fase2.md` e o spec
> `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` (inteiro). Branch
> `feat/motor-atribuicao`. Execute primeiro o PRÉ-FLIGHT §4 do handoff (auditoria de frescor dos
> golds SO/TCC/IA/ES2, READ-ONLY, com sign-off meu para qualquer re-rotulagem). Depois invoque
> `writing-plans` e escreva o plano da FASE 2 (P3 SO + P4 TCC) em `docs/superpowers/plans/`.
