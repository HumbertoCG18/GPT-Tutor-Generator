# Handoff — pós-F5b (rollout flag-ON + cutover + bibliografia)

**Data:** 2026-08-03 · **Branch:** `feat/motor-atribuicao` (head `b99e380`, ~15 commits à frente
do origin, NÃO pushado) · **Contexto:** semestre 2026/2 começou; repos atuais são de 2026/1.

## §1 Estado: F5 + F5b FECHADAS — janela-de-prazo PROVADA no alvo

- **Probe target PASS: 4/8 (piso exato) · cw=0** (`scripts/fase5_prova_tier2.py`, modo target).
  t1→bloco-11 (alta) · t1-thy→bloco-11 (alta) · t2→bloco-16 (media+FLAG) · revisao-p1→bloco-07 (funil).
- Campanha F5b `62acd26..b99e380` (10 commits): FAIL honesto 1/8 registrado → gold t1/t1-thy
  CORRIGIDO bloco-15→bloco-11 com evidência de submissão da API Moodle (submetido 2026-05-05;
  fórum "10/06" refutado como entrega do T1 — eram exercícios Dafny) → spec adendo D-F..D-I →
  matching posicional `file_dues` (produtor + motor, stem = fallback) + âncora só em bloco DE
  CONTEÚDO (`topics` não-vazio) → re-sync headless → medição.
- Review final whole-branch (fable): **READY TO MERGE YES**, 0 Critical. Régua: 6 probes
  flag-OFF byte-idênticos, zero drift. Suite 1816/4 verde.
- Decisões user desta campanha: semântica do trabalho = **ÉPOCA DE ENTREGA**; fonte de verdade
  = **Moodle**; voter para trabalhos DESCARTADO (probe one-off 0/3 — vota por conteúdo).
- Sync Moodle roda HEADLESS (token `moddle/.env` + `MoodleClient` + `backfill_repo_signals_consumed`
  — mesmo caminho da GUI). MF ainda visível na matrícula (id=92717); cursos 2026/2 já aparecem.

## §2 Pré-requisitos de rollout registrados (review final F5b — pendencias.md)

- **Flag-ON em curso NOVO exige `topics` populado** no timeline index: o filtro de
  bloco-de-conteúdo (D-H) usa campo OPCIONAL do schema v4; sem topics o provider fica
  silenciosamente morto (funil total). Alternativa futura: migrar filtro para `kind`
  (required, enum) — exige re-medição.
- **Limite do posicional**: arquivo entre o assign do grupo N e o label do N+1 herdaria o due
  errado (inexistente no MF atual; fix 1 linha + teste quando tocar o produtor).
- Card `source=="manual"` NUNCA ganha `assign_dues`/`file_dues` (merge protege) — interpretar
  medições com isso em mente.

## §3 O que falta (por prioridade — lista curada 2026-08-03)

**Trilha 1 — motor (próximo grosso):**
1. **Rollout flag-ON do MF**: seed cache F3 (`docs/reports/material_curation_MF.json` → raiz do
   Metodos-Formais-Tutor), flip `use_anchor_engine`+`use_llm_voter`, reprocess GUI, gate
   HARD-drift 0. Piloto dry-run já passou (2026-07-22).
2. **Push da branch** (user decide quando; merge → main só no fim).
3. **Rollout SO/TCC/IA/ES2** — golds frescos (pré-flight F2); medição por curso antes de cada flip.
4. **Cutover fase 5** (matar funil legado) — SÓ com flags ON estáveis: mapa de deleção (5
   conflitos travados 2026-07-03), RUN dedicada de mortos, fallback keyword ~600 linhas
   (dividido), Task B `administrative_only` (congelada até rollouts).
5. **Dívidas do motor**: defer-F5 do review F4 (T1b/T2b/T3/T4b/T7a/b/T9a) + minors-batch F5b
   (filtro `fileurl`, topics→`kind` c/ re-medição, fronteira de label, hoist stems).

**Trilha 2 — semestre 2026/2 (paralelo):**
6. Importar cursos novos quando professores postarem (out-of-sample real; nascem flag-OFF;
   flag-ON exige §2).

**Trilha 3 — caso à parte:**
7. **Bibliografia**: tutor consumir bibliografias sem estourar limite de projeto Claude/GPT —
   brainstorm próprio, não iniciado (decisão user 2026-07-22).

**Trilha 4 — gold/medição USER-SIDE (bloqueiam medições finas, não o rollout):**
8. Rotulagem cross-curso: IA placements · 9 SO date-vs-block · 21 straddle (batch SARC) ·
   16 materiais fora da manifest viva (decisão).
9. **Caso IRIS** — calibração de confiança (PRIORIDADE ALTA no tracker).
10. PIN-SWEEP: 2 pins manuais discordando da âncora.

**Trilha 5 — limpeza/menor:**
11. `.env`: `MOODLE_PRIVATE_TOKEN` morto · armadilha token stale · `datalab_client` import transitivo.
12. Latentes: `migrate_signals` sem `turma` · divergência sem teaching_plan · TCC NFD dotless-i.
13. UI parte B: tab cronograma SARC · guard conflito override · aviso "sem bloco" (UX-trap de pin).
14. Stashes: IA ~45 arquivos faltando · TCC 24/42 sources sumidos do disco.

## §4 Regras não-negociáveis (herdadas, seguem valendo)

- Flag-OFF byte-idêntico; régua completa (7 probes) antes/depois de qualquer mudança do motor.
- FAIL = resultado honesto; PROIBIDO re-tuning pra passar régua. Pisos em fração exata.
- Medição só com `audit_gold_freshness.py` hard=0 (pre-gate).
- D-E: provider nunca chuta (0-match/empate → funil). Gold muda SÓ com evidência + autorização user.
- TDD por task; fixture ajustável (timezone), implementação nunca.

## §5 Infra (estado 2026-08-03)

- Token Moodle vivo em `moddle/.env`; Gemini em `.env` raiz (`GEMINI_API_KEY`). Cache do voter
  F3/F4 intacto (probe one-off usou cache isolado em scratchpad, descartado).
- Card map do MF re-sincado 2× nesta sessão (assign_dues + file_dues reais gravados; key extra
  `"arquivo .thy.thy"` observada, não-bloqueante).
- Workspace SDD da F5b deletado (histórico = git + pendencias). Hook de commit segue com
  UnicodeEncodeError cp1252 cosmético.

## §6 Arquivos-fonte desta continuação

- `docs/reports/pendencias.md` — tracker vivo (entradas 2026-08-03: FAIL, gold fix, PASS,
  pré-requisitos de rollout, minors-batch).
- `docs/superpowers/specs/2026-08-03-janela-de-prazo-f5b-adendo.md` (+ spec-base 2026-07-22
  com nota de gold no topo).
- `docs/superpowers/plans/2026-08-03-janela-de-prazo-f5b.md` — plano executado (3 tasks).
- `scripts/fase5_prova_tier2.py` — probe da janela (modos baseline-only/target auto).

## §7 Comando de partida da próxima sessão

> Leia `docs/reports/2026-08-03-handoff-pos-f5b.md` + entradas 2026-08-03 do pendencias.md.
> Depois: **rollout flag-ON do MF** (trilha 1 item 1 — seed cache F3, flip flags, reprocess
> GUI, gate HARD-drift 0, re-rodar régua completa) OU **brainstorm da bibliografia** (trilha 3,
> superpowers:brainstorming) — user escolhe a campanha.
