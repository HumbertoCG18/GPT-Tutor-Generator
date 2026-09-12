# Handoff — pós-FASE 2: decisão go/no-go FASE 3 + dívidas (sessão zerada)

date: 2026-07-09
branch: `feat/motor-atribuicao` (NÃO mergeada; review final whole-branch F2 = **Ready to merge: Yes** —
decisão de merge pendente do user desde a FASE 0)
sessões anteriores: FASE 0 (07/07) + FASE 1 + auditoria gold MF (08/07) + FASE 2 (08-09/07), nesta branch

## 1. Estado — o que está PRONTO

- **FASES 0+1+2 entregues.** FASE 2 (14 commits `3ce409d..247fdb5` + pós-review `e043c96`):
  providers P3 (SO data-no-nome DD.MM→sessão→bloco) e P4 (TCC topic-bridge "Semana N - Tópico",
  stem-prefix-6, o N NUNCA vira janela) na cascata `manual → labels → data → topic`
  (`src/builder/routing/motor/window_provider.py`); gate D4 de concordância para janela-1 de sinal
  INDIRETO (`data` E `topic` — estendido pós-review com autorização do user, commit `e043c96`,
  `_gated_window1_decision`, `DATE_DF_MAX=2`).
- **Réguas HARD novas** (exit 0/1): `scripts/fase2_prova_SO.py` e `scripts/fase2_prova_TCC.py` —
  whole-cascade por design, linha `providers das decisões` denuncia mistura no headline.
- **Pré-gate de medição** (decisão user 08/07): `scripts/audit_gold_freshness.py` roda ANTES de
  qualquer medição contra ground_truth_* (especialmente pós-reprocess). Golds 4/4 auditados FRESCOS
  em 08/07; falso-alarme conhecido: SO `lista2` ADMIN_TRUE (gêmea da Lista P2, rótulo correto).
- Report de fechamento: `docs/reports/2026-07-09-fase2-providers-report.md` (aceite §6 lado a lado,
  constantes calibradas com grades, riscos residuais com dono, fila humana consolidada).

## 2. Números vigentes (verificados por review independente, 09/07)

| Régua | Números | Guard |
|---|---|---|
| MF (fase0+fase1, em PAR) | acc 82.8% (48/58) · contenção 0 · conf-errado 1 · recall 0.900 | baselines HARD nos probes |
| SO (fase2_prova_SO) | cobertura 45.2% (19/42) · colisões 0 · conf-errado 0 · acc 77.8% (funil era 47.4%) | PASS HARD |
| TCC (fase2_prova_TCC) | pinos 5/5 · cobertura 83.3% (30/36) · conf-errado 0 · acc 84.2% (funil era 56.0%) | PASS HARD |
| Suite | **1724 passed / 4 skipped / 0 failed** | — |
| Fila humana consolidada | **65 flags** = MF 37 + SO 6 + TCC 22 | insumo do go/no-go |

Constantes: `MARGIN_TAU=0.55`, `W_SESSION_LABEL=1.0`, `W_TOPIC=0.6`, `DATE_DF_MAX=2`,
`TOPIC_STEM_LEN=6`, `TOPIC_MIN_TOKEN=3` (piso-2 é no-op estrutural — ver report F2 risco #3).
Os 4 probes rodam em conjunto como regressão: fase0 && fase1 && fase2_SO && fase2_TCC.

## 3. DECISÃO PENDENTE #1 — go/no-go FASE 3 (LLM; sign-off condicional spec §9)

Dados honestos para a decisão:
- **Contra (caso enfraqueceu):** confiante-errado TOTAL nos 3 cursos medidos = **1**
  (`exerciciosdafny2` MF). A maior classe flagada do MF (cluster indução×Isabelle 05↔06, 6 pares,
  grão-de-semana) é a que o MARCO 1 PROVOU que o voto NÃO converte. Falso-alarme da fila MF: 28/37.
- **A favor:** classe que o voto converte = confusão-semântica (MARCO 1: +5/18 sem novo
  confiante-errado); parte dos 9 flags-errados MF + 4 SO + 4 TCC pode ser dessa classe (não medido
  por classe fora do MF). Cap=20/reprocess, cache em `material_curation.json`, seed dos votos MARCO 1.
- **Sem LLM:** 65 flags viram fila de curadoria humana no Timeline Dashboard (badges band/flag —
  serialização `AnchorResult`→Dashboard é decisão aberta do plano da FASE 4).
- Regras do voto (se GO) já estão fechadas no spec §3 TIER 3 + §12: escopo flagged∪same-theme,
  voto bounded à janela, autoconfiança IGNORADA, aceitar-cego band `media`, sem-janela NÃO vota
  (classe plano.pdf perdida — OU janela=timeline p/ categoria não-bibliografia, decidir na fase).

## 4. Dívidas em aberto (com dono/trigger)

1. **Granularidade de band no ramo flagado do gate** (`band="media"` hardcoded; silêncio ≠
   boilerplate) — ACOPLADA à decisão #1: se NO-GO, aplicar fix (~3 linhas: silêncio→`baixa`) para a
   fila humana priorizar; se GO, irrelevante (TIER 3 consome `flag`, não band). Report F2 risco #1.
2. **Stopwords PT no P4** (`_topic_tokens` deixa conectivos 3+ chars) — trigger: fila flag TCC
   crescer OU janelas P4 sistematicamente >8 blocos. Fix limpo: reusar `src/builder/text/stopwords.py`
   (whitelist text/* permite). NÃO mexer sem dor: matcher está verde e recalibra tudo.
3. **Memoizações** (`_global_df`, `_modal_years`, `normalized_card_map`) — FASE 4 (motor entra no
   reprocess; campo lazy no `MotorContext`; `motor/context.py` previsto desde a F0).
4. **Gold → `block_uuid`** — FASE 4 (decisão user 08/07); até lá o pré-gate auditor cobre.
5. **Auditor de frescor:** flag `--strict` (exit 1 em hard) SÓ se entrar em automação; teste
   dd-inválido-em-prefixo-válido não isolado (ex. "32.05") — primeiro toque nos testes do extrator.

## 5. DECISÃO PENDENTE #2 — merge da branch

Review final whole-branch (fable, `07f54a0..7e16798` + retoques): **Ready to merge: Yes**, 0
Critical/Important. Branch acumula F0+F1+F2. Merge = decisão do user (pendente desde a F0).

## 6. Disciplinas não-negociáveis (herdadas + novas)

- Tudo que CC roda sozinho é **READ-ONLY nos repos-tutor**; mutação do vivo = user na GUI.
- Lógica nova SÓ em `src/builder/routing/motor/` (e `scripts/`); NUNCA `engine.py`.
- ANCHOR-ONLY; funil (`computed`) = piso; integração só na FASE 4.
- **NÃO commitar sem pedido explícito do user** (na FASE 2 o user autorizou commit-por-task para a
  execução subagent — autorização por sessão, re-perguntar).
- Guard AST: proibido importar `block_token_weights`, `score_entry_against_timeline_block`,
  `select_probable_period_for_entry` no pacote do motor.
- **PRÉ-GATE:** `audit_gold_freshness.py` antes de QUALQUER medição contra golds.
- **Regressão = 4 probes em conjunto** (fase0, fase1, fase2_SO, fase2_TCC) + suite.
- UTF-8 shim em script novo; PT-BR nos docs; MARCO 0/1 não se re-rodam; gold = verdade humana
  (re-rotulagem só com sign-off, caso a caso).
- Pre-commit hook pode imprimir UnicodeEncodeError não-fatal — verificar com `git log -1`.
- `.claude/settings.local.json` nunca commitar; CLAUDE.md/settings do graphify fora do escopo.
- Plano 100% executado (gate verde) → `git mv` para `Feitos/` + tracker atualizado.

## 7. Comando de partida (colar na sessão nova)

> Leia `docs/reports/2026-07-09-handoff-fase3.md` e o spec
> `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` (§3 TIER 3, §7 FASE 3, §12).
> Branch `feat/motor-atribuicao`. Primeiro me apresente a decisão go/no-go da FASE 3 (§3 deste
> handoff) com os dados e aguarde meu sign-off. Se GO: invoque `writing-plans` e escreva o plano da
> FASE 3 em `docs/superpowers/plans/` (escopo flagged∪same-theme, cache material_curation.json,
> seed MARCO 1, regras de voto §12). Se NO-GO: aplique a dívida #1 (band granularidade, TDD +
> regressão dos 4 probes) e depois escreva o plano da FASE 4 (integração D9, spec §7).
