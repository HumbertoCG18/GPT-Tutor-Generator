# Proposta #65 — D9 cru como padrão de matéria nova (23/09/2026, não implementada)

**Status: proposta.** Este documento e o commit que o versiona não aprovam implementação, mudança de default nem
migração de perfis. O D9 fica separado dos recursos opcionais (votador, vocabulário, LLM, rede): ligar um não liga os
outros.

Pedido do usuário (23/09): matérias novas usam o D9 no regime cru, sem votador, vocabulário externo, LLM ou rede;
preservar as escolhas explícitas dos perfis existentes e o comportamento dos pinos e fallbacks. Autorização: só elaborar
a proposta; implementar exige Gate 1 próprio. Não depende das #63/#64, mas pressupõe a #63 (sem ela, o primeiro save de
uma matéria existente apagaria as flags de novo).

## Mudança mínima (3 pontos, dado explícito no perfil, sem mudar default de código)

1. `src/models/core.py`: constante `NEW_SUBJECT_FEATURE_FLAGS = {"use_anchor_engine": True}`. Votador, vocabulário e
   resíduo ficam ausentes, e ausente = desligado (`FLAG_DEFAULTS` em `src/builder/ops/assignment_run.py`).
2. `src/ui/dialogs.py` `_save`: matéria nova (`existing is None`) grava `dict(NEW_SUBJECT_FEATURE_FLAGS)`; matéria
   existente continua copiando `existing.feature_flags` como está (#63).
3. `src/builder/sources/moodle.py:707` (`import_moodle_courses`, ramo "created"): a matéria criada pelo import recebe a
   mesma constante. Os ramos "updated"/"linked" (perfil existente) não tocam nas flags.

**Não muda:** o default de código `use_anchor_engine=False` (senão os perfis com `{}` migrariam em silêncio); pinos
(`_valid_manual_pin` limpa o temporal e o manual vence); fallback `resolve_temporal_block` → `resolve_effective_block`
(manual > `computed_block_id`); `use_concept_resolver` segue ligado por default; nenhuma flag exposta na UI.

**Fora, decisão separada:** `scripts/build_course.py:148` tem default `--flags use_anchor_engine,use_llm_voter` (liga o
votador em matéria criada pelo script) e em `:181` substitui as flags do perfil a cada execução, inclusive valores falsos
explícitos. Alinhar exige decisão própria, porque é o contrato de uma ferramenta de desenvolvimento.

## Testes propostos (vermelhos antes)

1. Diálogo, matéria nova → `feature_flags == {"use_anchor_engine": True}` exatamente (sem `use_llm_voter`,
   `compile_vocabulary`, `enable_material_residual`).
2. Diálogo, matéria existente com `{}` → continua `{}`; com `{"use_anchor_engine": False}` → continua `False`
   (sem migração, sem falso virar verdadeiro).
3. Import do Moodle: curso novo recebe exatamente a constante; curso casado por id ou slug mantém as flags que tinha.
4. Opções de matéria nova: `_build_options_from_config(subject=nova)` tem `use_anchor_engine=True` e não tem chave de
   votador, vocabulário ou resíduo; `new_run(opts)["effective"]` tem os três em `False`.
5. Pinos e fallback: sem teste novo, porque o código não muda (cobertos por `tests/test_motor_apply.py` e pelos testes de
   `resolve_temporal_block`). O registro da #64 (`block_source`) mostra pino, D9 e `computed_block_id` por execução.

## Validação

- Reprodutor isolado `c1-3/waa_iso_d9_fluxo_real_23-09.py`, caso 1 (matéria criada pela UI): esperado D9 com 1 chamada
  e 26/27 materiais com bloco temporal (hoje 0 chamadas e 0/27), `assignment_run.executed.use_llm_voter=false`, sem
  tentativa de rede (tripwires do reprodutor). Hoje o caso 2 já mostra esse resultado com a flag gravada à mão.
- Suíte completa antes e depois.
- Replay integral dos 3 eixos: os 8 cursos medidos têm flags explícitas e não mudam, e o harness já mede o D9. O
  critério da #65 ("replay se o padrão de execução mudar") pede decisão do usuário: dispensar ou rodar como conferência.

## Riscos

- Matéria nova sem cronograma: o D9 retorna sem decidir (`apply_anchor_engine`, `if not ctx.blocks`); unidade e bloco
  seguem pelo resolvedor antigo, como hoje. O `assignment_run` registra 0 em `temporal_block_id`.
- Exceção no D9: a camada é pulada (política atual, inalterada) e o `assignment_run` registra `fallback.use_anchor_engine`.
- Acurácia: nenhuma mudança de acerto é atribuída a esta proposta. Configuração não é ganho de acurácia; 86/251 continua
  sendo o resultado observado da base de subunidade.
