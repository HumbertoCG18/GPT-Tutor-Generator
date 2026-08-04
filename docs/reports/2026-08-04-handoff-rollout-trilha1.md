# Handoff — rollout flag-ON trilha 1 (MF completo · SO/TCC adiados · audit IA/ES2)

**Data:** 2026-08-04 · **Branch:** `feat/motor-atribuicao` · **Contexto:** campanha trilha 1 do
plano pós-F5b (`docs/superpowers/plans/2026-08-03-rollout-flagon-trilha1.md`), 9 tasks.

## §1 Estado por curso

- **MF — flag-ON COMPLETO.** Snapshot `8ea55de` (seed cache F3) → rollout `c7b7498`
  (`use_anchor_engine=true` + `use_llm_voter=true` persistidos em `subjects.json`). Gate
  HARD-drift PASS 8/8: 54/54 `temporal_block_id` (51 piloto + 3 tier2 F5b), 11/11 pinos
  intactos. Distribuição de providers nos 51 não-tier2: **9 manual/5 labels/37 llm** (nova
  referência do rollout, substitui piloto 9/6/36 — migração labels→llm é a mesma
  `verificacaomodelos`, contenção gold bloco-16, correção da era-labels, não regressão). Voter
  retry: **0 chamadas API novas** (cache 45→45 cobriu 100%; 1 voto Gemini pago na rodada 1 — 44→45, adjudicado CASE B: conteúdo verificacaomodelos nunca votado em produção). Régua completa pós-flip: **7 probes
  + pytest 100%**, fase5 target PASS 4/8 cw=0, **pytest 1820 passed / 4 skipped / 0 failed**.
  Gold MF: 67/67 `auto_tags bloco:` zero-diff.
- **SO — flip ADIADO.** Pré-flight `audit_gold_freshness.py --course SO`: hard=1, única row
  `lista2` [ADMIN_TRUE, ZERO_OVERLAP] — achado PRÉ-EXISTENTE (timeline_index SO datado 28/jun,
  anterior à campanha; SO-Tutor não tocado pela task). Pré-requisitos técnicos SATISFEITOS
  (baseline fase2_SO 45.2%/0/0 byte-idêntico, `material_curation.json` próprio presente). Flip
  bloqueado até ruling do user sobre `lista2` (re-rotular `true_block` OU confirmar bloco-17
  como legítimo).
- **TCC — flip ADIADO (FAIL honesto).** Pré-flight hard=0. Gate estrutural (b) do funil falhou
  na 1ª rodada (4 entries mudam `auto_tags bloco:` sem `temporal_block_id` associado) —
  diagnóstico com controle flag-OFF confirmou causa **pré-existente e ortogonal** ao flip. Fix
  round 1 (critério decisivo pedido pelo controller): `audit_gold_freshness` PASS, mas
  `fase2_prova_TCC.py` **NÃO** bateu idêntico — `aula-01-apresentacao` foi de
  wrong-mas-não-confiante para **confiante-e-errado** (computado bloco-02 vs gold bloco-01,
  provider=`topic`), efeito causado pelo flip (voter endossando com confiança uma resposta de
  base já errada). Veredito FASE2: FAIL → rollback completo (`TCC-Tutor` de volta a `28bb29f`,
  `subjects.json` revertido). **16 votos Gemini pagos** ficam em `material_curation.json`
  untracked no `TCC-Tutor` (cache para retry futuro sem re-pagar). Dívida de idempotência do
  funil-base nomeada em pendencias.md (candidata a bug, fora do mandato desta campanha).
- **IA/ES2 — audit hard=0, sem flip nesta campanha.** IA: 74 rows scorable, 0 hard, 7 soft
  ZERO_OVERLAP; flag legado `use_anchor_placement=true` ATIVA em `subjects.json` (precedência OK
  em `pedagogical_regeneration.py:444`, mas flip futuro do motor DEVE desligá-la no mesmo ato —
  manter ambos ON é estado não-medido). Bloqueio real é gold user-side (trilha 4: placements em
  stash, ~45 arquivos do Moodle ausentes, timeline 24-29/06 vs SARC vivo). ES2: 35 rows
  scorable, 0 hard, 22 soft ZERO_OVERLAP; flags `{}` (OK); bloqueio é gold sem atualização desde
  21/06 (medição pré-flip obrigatória antes de liberar).

## §2 Código novo desta campanha

- `--flags` no `reprocess_assignments.py` (injeção de `use_anchor_engine`/`use_llm_voter` no
  reprocess headless, que antes não tinha caminho para passar flags ao `manifest.json` do
  repo-tutor). Commit `68ca870`, 4 testes novos, suite 1820/4 (era 1816/4).

## §3 Decisões do user nesta campanha

- Push antes de mexer em qualquer coisa — feito (`a876d1c`, autorizado 2026-08-03).
- Cutover (matar funil legado) fica FORA desta campanha — espera flags estáveis nos 5 cursos.
- SO e TCC adiados por gate (SO: gold hard=1 pré-existente; TCC: FAIL honesto no critério
  decisivo) — nenhum dos dois é bloqueio do motor, ambos aguardam ação humana/investigação.
- Ideia em aberto, não desenvolvida: **"silver gold" via Moodle** (weak supervision — usar
  sinais estruturais do Moodle como gold aproximado onde a rotulagem humana é o gargalo).
  Brainstorm futuro; discutida na conversa de 2026-08-04, sem spec.

## §4 O que falta (próxima sessão)

1. **Ruling do user sobre `lista2` (SO)** — destrava o flip SO assim que resolvido.
2. **Investigação da dívida de idempotência do funil-base (TCC)** + a instabilidade do
   `auto_tags bloco:` nomeada em pendencias.md — vai para o Plano B (dívidas defer-F5 +
   minors-batch F5b), proibido re-tuning fora desse plano.
3. **Rollout IA/ES2** — aguarda gold user-side (trilha 4 para IA; medição pré-flip fresca para
   ES2); IA também exige desligar `use_anchor_placement` no ato do flip.
4. **Cutover** — só com as 5 flags estáveis (MF já está; os outros 4 ainda não).
5. **Brainstorms pendentes** — bibliografia (trilha 3, decisão user 2026-07-22, não iniciado);
   "silver gold" via Moodle (§3, não iniciado).

## §5 Regras herdadas (do handoff pós-F5b §4, seguem valendo)

- Flag-OFF byte-idêntico; régua completa (7 probes + suite) antes/depois de qualquer mudança do
  motor.
- FAIL = resultado honesto; PROIBIDO re-tuning pra passar régua. Pisos em fração exata.
- Medição só com `audit_gold_freshness.py` hard=0 (pre-gate).
- D-E: provider nunca chuta (0-match/empate → funil). Gold muda SÓ com evidência + autorização
  user.
- TDD por task; fixture ajustável (timezone), implementação nunca.

**Infra (estado 2026-08-04):**

**AVISO — Importantes para operação headless futura:**
- **ARMADILHA (review final):** reprocess headless futuro do MF SEMPRE com `--flags use_anchor_engine,use_llm_voter`. As flags NÃO persistem nas options do manifest e `reprocess_assignments.py` NÃO lê subjects.json — rodada sem --flags pula a camada temporal inteira e o efeito sobre os 54 temporal_* existentes (strip vs stale) nunca foi medido. Durabilidade das flags vale só pro caminho GUI. Fix estrutural (script ler subjects.json) = Plano B.
- **SO-Tutor** está com ~21 arquivos modificados UNCOMMITTED desde 28/jun (pré-campanha). NÃO rodar git checkout/clean nele sem snapshot antes — o fluxo de flip (Task 6 do plano) já prevê snapshot; fora dele, não tocar.

- Flags atuais persistidas em `subjects.json`: **só MF ON** (`use_anchor_engine`+
  `use_llm_voter`). SO/TCC/ES2 = `{}`. IA = `{"use_anchor_placement": true}` (legado).
- Token Moodle vivo em `moddle/.env`; Gemini em `.env` raiz (`GEMINI_API_KEY`).
- Cache do voter TCC: **16 votos untracked** em `material_curation.json` na raiz do
  `TCC-Tutor` (preservado do rollback, para retry sem re-pagar).

## §6 Comando de partida da próxima sessão

> Leia `docs/reports/2026-08-04-handoff-rollout-trilha1.md` + entradas 2026-08-04 do
> `docs/reports/pendencias.md`. Depois: **ruling do user sobre `lista2` (SO)** OU
> **investigação da dívida de idempotência do funil-base (TCC, Plano B)** OU **brainstorm**
> (bibliografia ou "silver gold") — user escolhe a campanha.
