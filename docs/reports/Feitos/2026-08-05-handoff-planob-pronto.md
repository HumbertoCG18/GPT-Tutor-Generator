# Handoff — Plano B PRONTO, execução NÃO iniciada (2026-08-05)

**Branch:** `feat/motor-atribuicao` · head `50787b1` (pushado) · **Este é o handoff de partida da
próxima sessão** — os anteriores (`2026-08-04-handoff-rollout-trilha1.md`,
`2026-08-04-handoff-roteiro-pos-rollout.md`) seguem válidos como histórico; este consolida ONDE
ESTAMOS.

## §1 Onde estamos (mapa em 6 linhas)

1. **Rollout trilha 1: FEITO.** MF flag-ON (`Metodos-Formais-Tutor` @ `c7b7498`) e SO flag-ON
   (`Sistemas-Operacionais-Tutor` @ `11667b7`) — motor em produção em 2 cursos. TCC/ES2 OFF;
   IA OFF (flag legado `use_anchor_placement` ainda true).
2. **Ruling lista2: FEITO** (user: gold bloco-17 confirmado; auditor corrigido `f14d50c`;
   hard=0 nos 5 cursos).
3. **Investigação Plano B: FEITA** (`docs/reports/2026-08-05-planob-investigacao.md` — leitura
   OBRIGATÓRIA antes de executar): 2a = stopword "nao" vira discriminante fantasma (fix
   validado empiricamente); 2b = funil aceita palpite conf=0/ambíguo (fix de 1 linha, muda
   atribuições, exige medição); 19 dívidas mecânicas com file:line.
4. **Plano B: ESCRITO e commitado** (`docs/superpowers/plans/2026-08-05-planob-motor.md`,
   7 tasks) — **NENHUMA task executada**. Workspace SDD criado:
   `.superpowers/sdd/2026-08-05-planob-motor/` (ledger + task-1-brief prontos).
5. **Régua atual:** tudo verde EXCETO `fase2_prova_TCC` (FAIL, cw=1 `aula-01` — causa conhecida,
   PB Task 1 zera). Suite `pytest`: 1823 passed / 4 skipped / 0 failed.
6. **Depois do Plano B** (ordem decidida pelo user 2026-08-04): brainstorms (bibliografia;
   "silver gold" via Moodle) → rollout IA/ES2 (gold user-side) → cutover (só com 5 flags
   estáveis).

## §2 Plano B — as 7 tasks (execução via superpowers:subagent-driven-development)

| # | Task | O quê | Gate |
|---|------|-------|------|
| 1 | **T12 stopwords PT** | +11 palavras-função em `_GENERIC_STEMS` (`disambiguator.py:22-26`) — fecha o cw do TCC | fase2_TCC PASS cw=0 acc 84.2% EXATA + régua completa |
| 2 | **Batch higiene** (10 itens) | T9a ref "None" · T2b logger · T8 mkdir · T9 fold · T10 casefold · T7a memoize md5 · T16 hoist stems · T13 fileurl · T14 due-vazio · T11 truncamento probe | régua BYTE-IDÊNTICA (higiene pura) |
| 3 | **T3 sonda fase3** | filtro `len(window)>1` na sonda (instrumentação) — ANTES de medir 2b | fase3 re-medido honesto |
| 4 | **Fix 2b** | `content_taxonomy.py:1224` → `if _period and not _p_ambig and p_conf > 0:` (+tie-break opcional) — MUDA atribuições (4 TCC + 3 MF + SO exercicios-p2) | medição gold pré/pós row-a-row; cw não sobe, acc não cai |
| 5 | **T17 topics→kind** | filtro D-H (`due_window.py:85`) por `kind` (required) — mata pré-requisito "topics" de curso novo | fase5 4/8 cw0 byte-idêntico; isolado do 2b |
| 6 | **T4b lock voter** | lock cross-processo (sentinela O_EXCL) em `_persist`/`prune` | sozinho; régua flag-OFF |
| 7 | **Infra final** | T15 imports · T1b tabela migração · T18 reprocess ler subjects.json (mata armadilha --flags) · T7b e2e ordem · T19 .bak (**EXIGE confirmação user — destrutivo em repo-tutor**) · read_only no probe path (probes hoje bumpam `last_seen` — achado §extra da investigação) | régua final + handoff + push |

Regras da execução (Global Constraints do plano): régua completa após cada task de motor/funil ·
proibido re-tuning · mudança de comportamento = medição gold registrada · TDD · repos-tutor
READ-ONLY neste plano · restaurar `last_seen` pós-probes.

## §3 Pendências fora do Plano B (não esquecer)

- **IA/ES2 rollout:** audit hard=0 já; bloqueios user-side (IA: gold trilha 4, stash parcial,
  timeline 24-29/06, desligar flag legado no ato do flip; ES2: gold de 21/06, medir pré-flip).
- **TCC flip:** re-autorizar SÓ depois do PB Task 1 (cw) + Task 4 (funil) medidos — aí re-rodar
  o fluxo de flip com gate (cache 16 votos untracked preservado no TCC-Tutor).
- **Fila humana SO:** 6 entries flagged (band media) aguardando curadoria do user na GUI.
- **Brainstorms:** bibliografia (decisão 2026-07-22) · silver gold via Moodle (análise preliminar
  no handoff roteiro §1.3 — weak supervision, sem scraper, valida providers de conteúdo).
- **Cutover:** último de todos (5 flags ON estáveis; mapa de deleção 2026-07-03).
- **Armadilhas operacionais vivas** (handoff rollout §5): reprocess headless do MF/SO SEMPRE com
  `--flags use_anchor_engine,use_llm_voter` (até o PB T18 resolver); rollback de reprocess deve
  cobrir artefatos GITIGNORED (índice, sidecars — lição TCC).

## §4 Infra (estado 2026-08-05)

- subjects.json: MF ON · SO ON · TCC `{}` · ES2 `{}` · IA `{use_anchor_placement: true}`.
- Repos-tutor: MF/SO limpos nos commits de rollout; TCC @ snapshot `28bb29f` + índice rebuilt
  (gates OK) + `material_curation.json` 16 votos untracked.
- Token Moodle: `moddle/.env` · Gemini: `.env` raiz.
- Suite: 1823/4/0. Probes: só fase2_TCC FAIL (esperado até PB Task 1).

## §5 Comando de partida da próxima sessão

> Leia este handoff + `docs/reports/2026-08-05-planob-investigacao.md` (spec-companion).
> Execute `docs/superpowers/plans/2026-08-05-planob-motor.md` task a task via
> superpowers:subagent-driven-development — workspace/ledger já em
> `.superpowers/sdd/2026-08-05-planob-motor/` (Task 1 brief pronto; retomar do ledger).
> Ordem é obrigatória (1→7); T19 pede confirmação do user antes.
