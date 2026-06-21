# Pendências — tracker vivo

last_updated: 2026-06-21
status: documento VIVO. Atualizar a cada conclusão de plano (regra não-negociável,
`.mex/AGENTS.md`). Concluído 100% (gate verde) → remover daqui + mover o plano pra `Feitos/`.

Legenda: **[USER]** = ação humana (rotular/decidir/rodar). **[CODE]** = implementável.
**[DECISION]** = decisão de produto antes de codar.

CONVENÇÃO (não-negociável): todo item DERIVADO (fato sobre estado vivo dos repos) carrega
`as-of <data/commit>`. Sem isso, volta a mentir na próxima mudança de estado. Itens DURÁVEIS
(goal/decisão/plano) não carimbam.

---

## USER-SIDE — destravam a cadeia de medição/cutover

- [USER] **Gold cross-curso** (DURÁVEL/intent) — rotular `tests/fixtures/eval/ground_truth_<curso>.csv` IA/SO/ES2/TCC
  (MF já mede via eval_assignments 5/5). Planilhas em `docs/reports/gold_templates/gold_by_card_<curso>.csv`
  (MF 6 cards · IA 9 · SO 5 · ES2 3 · TCC 13 + avulsos). **Bloqueia: cutover Fase 3.4, lever lessons[].text,
  resolvers SO/MF, avaliação do anchor.** ← MAIOR GARGALO.
  > sub-nota DERIVADO-STALE: TODOS os números embutidos são pré-reprocess (gold_templates +
  > evals de 17–18/06): card-counts MF6/IA9/SO5/ES2 3/TCC13, "MF mede 5/5", e qualquer placar
  > tipo "~41% funil MF / resolver 12/17". Não verificados pós-reprocess.
- [USER] **4 IA manual-pins suspeitos** — `caracteristicasdosdados`/`caracteristicas-dos-dados`
  (conteúdo=DADOS, talvez bloco-05 ≠ Semana 2) + `introducao-a-ml`/`introducaoml-2025`. Conferir antes de pinar.
  > **STALE — não verificado pós-reprocess (origem: investigação 20/06).**
- [USER] **8 SO DIFFERS** (data-postagem vs data-aula) + **1 SO NO_MATCH** (02/05 cai no gap entre blocos).
  > **STALE — não verificado pós-reprocess (origem: investigação 20/06).**
- ~~TCC sem CRONOGRAMA~~ **CORRIGIDO (21/06): claim era STALE (pré-reprocess).** TCC TEM cronograma
  completo pós-reprocess (31 blocos datados, SARC setado, 39/40 entries com "Semana N"). É
  week-anchorable igual IA/ES2. NÃO é blocker.

## CODE — cadeia de atribuição (degrau 3 / Fase 3)

- [CODE] Degrau 3a **alavanca 0** (lessons[].text → índice data→tópico no fusor) — plano escrito, não
  executado; `load_lessons_index` dormente. Eval-gate (precisa gold). Refazer com identidade limpa do label
  (a versão anterior regrediu o gold com concepts ruidosos).
- [CODE] **Alavanca 3** (posting_date / seleção por sessão) — não implementada.
- [CODE] **Fase 3.4 cutover** — default ON do concept_resolver + DELETE do funil legado
  (`score_entry_against_timeline_block` S2/S4, `select_probable_period`, `_best_instructional_block_fallback`,
  2 rotas card). Eval-gated.
- [CODE] **topic-resolver (SO)** + **label-resolver (MF)** — próximos resolvers de âncora (reusam
  `anchor_placement`/`resolve_temporal_block`); cada um TDD + canário próprio.
- [CODE] Degrau 2/3c **over-merge temporal** (merge feriado+prova) — adiado; funde no degrau 3 quando join virar DATA.

## CODE — limpeza / dead-code (auditoria pronta)

- [CODE] **Tasks D/E** — unificar 3 scorers de unidade dup + vocab/normalizadores ×4. Eval-gated.
- [CODE] **Task B** `administrative_only` — persistir vs deletar filtros mortos (decisão de produto).
- [CODE] **fallback keyword** (~600 linhas, index.py) — deletar junto da unificação P2 (fold dos sinais que
  o frágil tem: "Unidade N" explícita, frases/âncoras) + guard test.
- [CODE] **Auditoria de artefatos** — mapear quem lê `.timeline_index`/`.card_block_map`/`.lessons_index`/
  `code_curation`/`.tag_profile`/etc. → morto/vivo/redundante → fundir, cada fusão eval-gated.

## CODE — bugs pré-existentes localizados

- [CODE] `SubjectManagerDialog._save` (dialogs.py:1503-1525) **dropa `moodle_course_id`/`m365_filter`** ao salvar.
  > derived-código, não-reprocess-stale, as-of 18/06 (S0). Baixa urgência; carrega proveniência.
- [CODE] `migrate_signals` standalone **não grava `turma`** (só `import_moodle_courses` grava) — derivar do curso.
  > derived-código, não-reprocess-stale, as-of 18/06 (S0).
- [CODE] **Latente:** sem teaching_plan, `_derive_unit_specs_from_repo` vs `content_taxonomy["units"]=[]` divergem
  → fallback vira load-bearing. Remover ou dar mesmo fallback à taxonomy.
  > derived-código, não-reprocess-stale, as-of 17/06.

## CODE — UI (Parte B de features backend já entregues)

- [CODE] Cronograma SARC: **tab em tabela + legenda**.
- [CODE] Guard de conflito override: **aviso no tab + botão "reverter p/ auto"**.

## DECISION

- [DECISION] **bloco-15 over-merge (IA)** — dijkstra + hc-sa caem em bloco-15 pela Semana 14, minimax pela 15.
  Over-merge ou correto? (cura de timeline separada).
  > **STALE — não verificado pós-reprocess (origem: stageA 21/06, canary em manifest pré-reprocess).**
  > Relance não conta; re-confirmar contra timeline_index vivo na Fase 1.
- [DECISION] **5 IA topic-mismatch Semana 12** ("Algoritmos de Busca" seção vs sessão "Correção P1 + Agentes")
  = discrepância Moodle×SARC → cura de timeline separada (não inflar anchor).
  > **STALE — não verificado pós-reprocess (origem: investigação 20/06).**
- [DECISION] **A1 (lessons no fusor)** — chamar brainstorming antes de spec.

## CROSS-CUTTING

- [DECISION] **Branch `feat/block-stable-id` NÃO mergeada** — carrega Fase 1 + Fase 2 + campanha anchor/WO2/reprocess.
  Merge/PR = decisão do user.
- [CODE] **`.timeline_index.json` stale** (drift pré-existente ES2 7/IA 20/SO 13) — o reprocess desta sessão
  regravou os índices dos 5; RE-MEDIR rebuild_diff baseline pra confirmar se está resolvido.
  > **STALE — não verificado pós-reprocess (origem: 17/06; reprocess 21/06 regravou índices →
  > provavelmente já resolvido, RE-MEDIR).**

---

## Concluído (histórico desta campanha — 2026-06-21)
- Camada anchor placement WIRED (temporal_block_id aditivo + helper `resolve_temporal_block`, 6 consumidores
  temporais, KB intocado). Commit `d792331`.
- Surface durável `feature_flags` por matéria. Commit `22b6de9`.
- WO2 fix manual-uuid (`_block_by_migrated_ref` uuid-first) — 23 pins humanos recuperados nos 5. Commit `d67bb19`.
- Reprocess dos 5 tutores (computed→uuid; IA com 33 temporal/2 movers; outros sem temporal). Commits tutor repos:
  IA 7561f5c · ES2 abc8ee2 · MF 357a59b · SO 320712d · TCC 6b6e1e3. Gates: HARD-drift 0 em todos.
