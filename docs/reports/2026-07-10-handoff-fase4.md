# Handoff — FASE 4: integração D9 (AnchorEngine no reprocess) — sessão zerada

date: 2026-07-10
branch: `feat/motor-atribuicao` (NÃO mergeada; acumula F0+F1+F2+F3; review whole-branch F3 =
**Ready to merge: Yes** — decisão de merge pendente do user desde a FASE 0)
sessões anteriores: F0 (07/07) + F1 + auditoria gold (08/07) + F2 (08-09/07) + F3 (09/07, GO →
FAIL honesto → experimento 3.5-flash → **ACEITA com sign-off**), tudo nesta branch

## 1. Estado — o que está PRONTO

- **FASES 0+1+2+3 entregues.** FASE 3 (10 commits `512afcd..57fe6b8`): TIER 3 completo —
  `src/builder/routing/motor/llm_vote.py` (cache por identidade de conteúdo md5, seed,
  série same-theme, `LlmVoter` bounded/cap/erro-não-cacheado), hook no `AnchorEngine`
  (`voter=None` ⇒ byte-idêntico F2), régua `scripts/fase3_prova_LLM_MF.py`.
- **História do aceite F3 (importante pro contexto):** rodada mista deu FAIL +1 com confound
  de infra (`gemini-2.5-flash` APOSENTADO pela API mid-medição, 404 em 20/20 chamadas — erro
  não cacheia, zero votos sujos; + 18 seeds do modelo antigo). Experimento com
  `gemini-3.5-flash` PINADO (44 votos frescos): **lift +3, global 82.8%→87.9%, conf-errado 0**.
  Variante flagged-only medida offline e DESCARTADA (+2, conf-errado 1) — escopo
  flagged∪série do spec confirmado ótimo. Piso renegociado ≥+4→**≥+3** (`LIFT_MIN=3`,
  sign-off user 09/07). Dívida band-no-ramo-flagado → N/A. Adendo completo:
  `docs/reports/2026-07-09-fase3-llm-report.md`.
- **Config do user pinado `gemini-3.5-flash`** (`~/.gpt_tutor_config.json`, não-alias,
  reprodutibilidade). O CÓDIGO ainda referencia o modelo morto — item 0 abaixo.

## 2. Números vigentes (régua = REGRESSÃO DE 5 PROBES agora)

| Régua | Números | Guard |
|---|---|---|
| MF fase0+fase1 (determinístico) | acc 82.8% · contenção 0 · conf-errado 1 · recall 0.900 | PASS HARD |
| MF fase3 (com voto 3.5) | lift +3 (34→37/44) · global 87.9% (51/58) · conf-errado 0 | PASS HARD (`LIFT_MIN=3`) |
| SO (fase2_prova_SO) | cobertura 45.2% · colisões 0 · conf-errado 0 · acc 77.8% | PASS HARD |
| TCC (fase2_prova_TCC) | pinos 5/5 · cobertura 83.3% · conf-errado 0 · acc 84.2% | PASS HARD |
| Suite | **1743 passed / 4 skipped / 0 failed** | — |

Regressão completa: `fase0 && fase1 && fase2_SO && fase2_TCC && fase3` + suite. fase3 re-roda
em all-cache (0 chamadas API) se o cache `docs/reports/material_curation_MF.json` estiver
intacto. Backup da rodada mista: `material_curation_MF_2026-07-09_run1_mixed.json`.

## 3. Escopo da FASE 4 (spec §7 — número do aceite)

**AnchorEngine SUBSTITUI `apply_anchor_placement`** no reprocess, feature-flag por-curso,
funil intacto. Número: **flag-OFF ⇒ saída byte-idêntica ao atual; flag-ON ⇒ sem-regressão
5/5 no gold (pair_key), `computed_*` inalterado, só `temporal_*`**.

Âncoras de reúso (spec §8 — o plano RE-VERIFICA linhas): call-site
`pedagogical_regeneration.py:381` (gate `use_anchor_placement`); base a evoluir
`apply_anchor_placement:344` + `AnchorResult:77` (`anchor_placement.py`); flag por-curso
`SubjectProfile.feature_flags:244` (`core.py`); cascata `resolve_temporal_block:617`
(`file_map.py`).

## 4. Itens OBRIGATÓRIOS do plano FASE 4 (acumulados, com origem)

0. **Pré-flight modelo (PRIMEIRO item, antes de qualquer chamada Gemini):**
   `DEFAULT_MODEL = "gemini-2.5-flash"` em `gemini_client.py:11` está MORTO na API (404 em
   generateContent; metadados ainda respondem — aposentadoria de endpoint). Atualizar +
   os 2 hardcodes da UI (`dialogs.py:441` combo values E `:430` fallback do get). Sem isso,
   qualquer usuário sem o config pessoal ajustado repete o 404.
1. **[DECISION] D4 × janela-1 degenerada** (tracker): decisão D4-flagada de janela-1 entra
   no voto com UM candidato — LLM confirma e desflaga sem informação nova. Antes de ligar
   voter no reprocess: excluir |janela|==1 do escopo OU opção "nenhum destes" no prompt.
2. **Sidecar `material_curation.json` NO repo-tutor** (spec §12): reprocess escreve via
   GUI (aí deixa de ser READ-ONLY — é ação do user); chave = conteúdo; prune de chaves
   órfãs; write atômico já existe. Cache do probe em docs/reports/ segue separado.
3. **Voter na GUI = background-thread** + concorrência do cache (hoje lost-update:
   last-writer-wins; review final F3). Cap=20/reprocess; **opt-in por flag de curso**
   (`SubjectProfile.feature_flags`).
4. **Observabilidade do voter:** exceção engolida (só conta `errors` — o 404 só foi visto
   reproduzindo por fora) + caminho sem-chave silencioso (probe atribui a cap/erro).
5. **`motor/context.py`** (previsto desde F0): memoizações `_global_df`, `_modal_years`,
   `normalized_card_map`; loader dos probes migra pra cá.
6. **Gold → `block_uuid`** (decisão user 08/07): 5 CSVs + harnesses resolvendo
   uuid→display. Até lá, `audit_gold_freshness.py` é pré-gate obrigatório.
7. **Serialização `AnchorResult` → Timeline Dashboard** (badges band/flag — decisão aberta
   do plano F4 desde a F2). Consumidor lê `band` como autoritativo, NÃO `conf` (decisão
   votada mantém conf determinístico residual — minor do review F3).
8. **Decisão `cronograma_health`** — pré-requisito nomeado do cutover FASE 5.

Dívidas menores defer-F4 (review final F3, não-bloqueantes): parent dir em
`save_material_curation`; fold caso/acento em `source_section` na série; `match_window_ref`
exato (strip/casefold barato); truncamento do dry-run; stopwords PT no P4 (trigger: fila
TCC crescer). Ignorados com registro: ver ledger `.superpowers/sdd/progress.md`.

## 5. Fila humana MF — checklist de PINOS (opcional, user na GUI, TIER 1)

Resíduo pós-voto = 7 pares. Pinos que fecham 58/58 no gold (100% no gold ≠ 100% no curso):
`exercicioscorrecaoterminacao`→bloco-11 · `logicadehoare2`→bloco-10 · `terminacao`→bloco-12 ·
`provasindutivas-especificacoesrecursivas` (+`-arvores`/`-listas`)→bloco-06 (mesmo card ⇒
1 correção de card-window pode resolver o trio) · `tiposindutivos`→bloco-15.

## 6. DECISÃO PENDENTE — merge da branch

Pendente desde a F0. Review whole-branch F3 (fable): **Ready to merge Yes**, fix wave
`b0caa51` verificado. Branch com F0+F1+F2+F3. Merge = decisão do user.

## 7. Disciplinas não-negociáveis (herdadas + atualizadas)

- Tudo que CC roda sozinho é **READ-ONLY nos repos-tutor**; mutação do vivo = user na GUI.
  (Na F4 o reprocess PASSA a escrever temporal/sidecar — mas reprocess é ação do user.)
- Lógica nova SÓ em `src/builder/routing/motor/` (e `scripts/`); NUNCA `engine.py`.
- ANCHOR-ONLY; funil (`computed`) = piso; escreve só `temporal_*`.
- **NÃO commitar sem autorização de sessão** (re-perguntar; não transfere entre sessões).
- Guard AST: proibido importar `block_token_weights`, `score_entry_against_timeline_block`,
  `select_probable_period_for_entry` no pacote do motor.
- LLM = `google-genai` lazy dentro de método; PROIBIDO `google.generativeai`/
  `genai.GenerativeModel`. Modelo: pinar explícito (lição 404 — alias mascara mudança).
- **PRÉ-GATE:** `audit_gold_freshness.py` antes de QUALQUER medição contra golds
  (falso-alarme conhecido: SO `lista2` ADMIN_TRUE).
- **Regressão = 5 probes em conjunto** + suite. Autoconfiança do LLM NUNCA lida por gate.
- Voto não se re-roda por capricho: FAIL de medição = resultado honesto → decisão do user
  (spec §12 regra 4 — sem prompt-engineering do grão-de-semana).
- UTF-8 shim em script novo; PT-BR nos docs; MARCO 0/1 não se re-rodam; gold = verdade
  humana (re-rotulagem só com sign-off).
- Pre-commit hook pode imprimir UnicodeEncodeError não-fatal — verificar com `git log -1`.
- `.claude/settings.local.json` nunca commitar; CLAUDE.md/settings do graphify fora do escopo.
- Plano 100% executado (gate verde) → mover para `Feitos/` + tracker atualizado.
- `graphify update .` após mudanças de código.

## 8. Comando de partida (colar na sessão nova)

> Leia `docs/reports/2026-07-10-handoff-fase4.md` e o spec
> `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` (§3 Contrato 3, §4, §7 FASE 4,
> §8 âncoras). Branch `feat/motor-atribuicao`. Invoque `writing-plans` e escreva o plano da
> FASE 4 em `docs/superpowers/plans/` cobrindo os 9 itens obrigatórios do §4 deste handoff
> (item 0 = pré-flight modelo; item 1 = decisão D4×janela-1 que EU decido no plano-review).
> Execução subagent-driven; commit-por-task só com minha autorização explícita nesta sessão.
> Antes de codar: re-verificar as âncoras de linha do spec §8 (drift check) e rodar a
> regressão dos 5 probes + suite como baseline da sessão.
