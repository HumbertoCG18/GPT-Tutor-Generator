# Handoff — Identidade estável de bloco (uuid) + Camada de placement por âncora

date: 2026-06-21
branch: `feat/block-stable-id`
HEAD: `fab3803`
estado: **Fase 1 (uuid) COMPLETA e merge-ready (não mergeada). Fase 2 (anchor placement) Phase 1 commitada. Wire Stage A (plano) entregue, aguardando OK do Humberto pra Stage B.**

## Como retomar (ler nesta ordem, NÃO reler a conversa)
1. `.mex/ROUTER.md` + `.mex/AGENTS.md` (bootstrap + não-negociáveis). **Prefixar TODA resposta com `[Humberto]`**; debate-partner; commits terminam com `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; **caveman mode** no chat (código/commits/spec normais).
2. **Este handoff.**
3. **Ledger durável (fonte de verdade):** `.git/sdd/progress.md` — seções "Fase 1" e "Fase 2".
4. **Spec/plano Fase 1:** `docs/superpowers/specs/2026-06-20-block-stable-id-design.md` + `docs/superpowers/plans/2026-06-20-block-stable-id-plan.md` + baseline `docs/reports/2026-06-20-baseline-congelado.md`.
5. **Investigação file→card (relatórios visíveis):** `docs/reports/2026-06-20-investigacao-file-to-card/` (7 .md + json).
6. **Plano do wire (próximo passo):** `.git/sdd/wire-stageA-plan.md`.

## NÃO-NEGOCIÁVEIS desta campanha
- **uuid é a identidade de bloco** (não posicional). `bloco-NN` = só display. Join interno por `block_uuid` (ledger `.block_identity.json`).
- **persist-gate:** medição (eval/rebuild_diff) é READ-ONLY. Só build/reprocess real escreve. Flag OFF = byte-idêntico ao baseline.
- **Verdade humana nunca sobrescrita** (manual_timeline_block_id, .timeline_curation.json, gold true_block_id). Irresolúvel → FLAG, nunca dropa/chuta.
- **NÃO re-conflacie temporal vs KB.** computed_block_id alimenta DOIS consumidores: KB (file→card/unit) e TEMPORAL (cronograma). O wire do anchor alimenta SÓ o temporal.
- **NÃO calibra pra fazer diff inesperado passar.** Regressão em portão = REVERT.
- **Read-only nos 5 repos-tutor** salvo reprocess autorizado explicitamente pelo Humberto.

## FASE 1 — Identidade estável de bloco (uuid) — COMPLETA, merge-ready
commits `1422443..8eaf5b6` (5 tasks + PASSO 0). Review whole-branch opus: READY, 0 Critical/Important.
- Ledger `.block_identity.json` (append-only, trackeado): uuid por bloco, re-attach por best-overlap de DATAS (não hash), refuse-guard anti-orfanamento.
- 6 consumidores migrados pra uuid (lazy retrocompat): card_block_map, computed_block_id, secondary_block_ids + 3 verdades humanas (manual_timeline_block_id, curation, gold) com trava FLAG.
- Gate `persist` (Task 5): medição read-only. `migrate_human_truth` + reattach só escrevem com persist=True.
- Camada de medição migrada (Task 4): gold tools emitem uuid = pré-condição do Plano A.
- **Portão verde** (verificado): eval_assignments 5/5 cw0 · eval_code_block_gold funil 7/17 resolver 12/17 cw1 · rebuild_diff sem drift novo (ES2 0/IA1/MF1/SO0/TCC0) · pytest 1589.
- PENDENTE USER-SIDE: rebuild REAL do MF (persist=True, via `python -m scripts.retag_manifest <MF> --write` OU GUI Reprocessar) — MAS ver gotcha do retag abaixo. + reprocess controlado dos 5 repos.

## INVESTIGAÇÃO file→card (entre Fase 1 e Fase 2) — achados que MUDAM o entendimento
Relatórios em `docs/reports/2026-06-20-investigacao-file-to-card/`.
1. **"Regressão" exercicios-conjuntos (bloco-13→03) = ARTEFATO do probe léxico.** Entries de CÓDIGO (.zip) são atribuídas em produção pelo **D1/`attach_block_summary_fields` (llm_only)**, NÃO pelo funil léxico (`resolve_unit_block_tags`). O probe rodou o léxico → bloco errado. Produção (D1) dá bloco-13 (= gold).
2. **`retag_manifest` tem o MESMO furo:** roda o funil léxico SEM o D1 → `retag --write` REGREDIRIA code entries. Pro rebuild real do MF, usar build COMPLETO (com D1), não retag.
3. **SO 8 DIFFERS = data de POSTAGEM, não sessão.** Date-membership CEGO misplaceia (o DD.MM do filename pode ser upload/seção, não dia de aula). Validar contra cronograma é obrigatório.
4. **A medição de cobertura M2 estava FURADA (3 undercounts):** keyou em `.card_block_map.json` em vez do campo autoritativo real. Corrigido:
   - MF: `moodle_label` 57/60 + `lessons_index` (resumo semanal data→tópico) — não 20%.
   - TCC: `source_section` 39/40 (seções "Semana N - Topic") + `.timeline_index.json` datado — TEM cronograma, não 0%.
   - SO: `source_section` 36/36 (seções de tópico "Gerência de X") + 17 filename-dates — não 0%.
   - **Âncora autoritativa real = `source_section` (seção Moodle) > `moodle_label`+`lessons_index` (resumo) > filename-date validada.** Todos os 5 têm âncora forte; SO é o único "fraco" (tópico-section + date sujeita a postagem).

## FASE 2 — Camada de placement por âncora (estratificada) — Phase 1 commitada
spec/brief: `.git/sdd/anchor-placement-brief.md`. Módulo: `src/builder/routing/anchor_placement.py` (commit `fab3803`).
- Precedência por entry: **manual > anchor (cronograma-validado) > scorer**. uuid-keyed. `placement_method`. ADITIVO (não-wired).
- Anchor week-resolver: seção "Semana N - DD.MM a DD.MM - Tópico" → janela de datas → bloco, **válido SÓ se** (a) tópico não-admin, (b) bloco tem sessão real na janela, (c) overlap de tópico MEANINGFUL (filtro `_GENERIC_STEMS`: introduc/continua/exercici/revisao/etc não-distintivos não validam → scorer). Plugável por tipo (semana feito; tópico/label = próximas fases).
- **Canário IA (in-memory, read-only): 33 anchor / 5 manual / 12 scorer.** 33 = 11 (≥2 meaningful) + 22 (1 meaningful supervis/dados). Autoritativo = 38/50, → 42/50 após os 4 pins.
- pytest 1595, 6 testes não-vacuos. IA intacto (read-only provado).

## WIRE — Stage A (plano entregue, AGUARDA OK) — `.git/sdd/wire-stageA-plan.md`
Objetivo: wirar anchor_placement no caminho de produção, genérico mas efeito escopado ao IA via flag per-repo `builder.options["use_anchor_placement"]` (default OFF, padrão do `use_concept_resolver`).
- **6 consumidores TEMPORAIS** (devem ler bloco resolvido): timeline_dashboard:225/807, dialogs:4219, navigation:652, repo:926, cronograma_health:248.
- **8 KB** (NÃO mudam): content_taxonomy (produtor), file_map:540/556/602 (incl. `reconcile_unit_with_block`→unit), resolver_apply, D1, scan_guard.
- **FURO ACHADO:** wirar no write compartilhado de `computed_block_id` (proposta inicial do subagent) RE-CONFLACIA temporal+KB (o `resolve_effective_block` file_map:556 é compartilhado; mudar o bloco muda a unidade via reconcile_unit_with_block). **Viola "não re-conflacie".**
- **Wire correto = temporal-only.** Opção A (recomendada): novo campo `temporal_block_id` (anchor-resolvido, flag-gated) escrito ao lado; os 6 temporais leem ele (fallback computed_block_id); KB byte-idêntico. → wire = 1 produtor + 6 redirects. Opção B: split do resolve_effective_block (mais invasivo).
- **Diff IA previsto (flag ON, só temporal):** 5 manual NO-DIFF (consumer já honra manual, content_taxonomy:1143), 33 anchor MUDA (temporal scorer→anchor), 12 scorer NO-DIFF. KB inalterado nos 50.
- **DECISÃO PENDENTE DO HUMBERTO:** Opção A vs B; e aprovar o diff dos 33 entry-por-entry antes do Stage B. Stage B = TDD seam+flag, gate de aceitação (flag OFF byte-idêntico TODOS; flag ON só IA = exatamente o diff previsto; outros 4 zero diff; pytest≥1595), commit (UMA fase = seam+flag+IA ON; sem pins, sem resolvers SO/MF, sem cura dos 5 mismatch).

## PENDÊNCIAS (não desta fase, pra compor)
- **4 IA manual-pin (decisão humana):** `introducao-a-ml`, `introducaoml-atualizacao2025`, `caracteristicasdosdados`, `caracteristicas-dos-dados` → bloco Semana 2 (intro 09/03). Os 2 "caracteristicas dos dados" são suspeitos (conteúdo=DADOS, pode ser bloco-05) — conferir antes de pinar. Pin vira tier manual, flui pelo resolve. Pin-antes-ou-depois do wire tanto faz.
- **5 IA topic-mismatch Semana 12** ("Algoritmos de Busca" seção vs sessão "Correção P1 + Agentes") = discrepância real Moodle×SARC → cura de timeline separada (NÃO inflar anchor).
- **Resolvers próximos:** topic-resolver (SO: seção-tópico + filename-date validada) + label-resolver (MF: moodle_label+lessons). Cada um = fase própria, TDD, canário, audita o filtro de stem genérico (ATENÇÃO: "revisao" é bloco de ensino REAL no ES2 — não tratar como genérico lá). NÃO ligar ES2/TCC junto do IA; cada um precisa de canário próprio.
- **Working tree dos 5 repos-tutor:** sujo de propósito (reprocess controlado do user pendente). Fase 1 já trackeou+commitou ledger+manifest+curation nos 5 (commits 5f3fcd2/5fc4560/e684c2f/39bdd56/b47422a) — verdade humana preservada em uuid. Resto (MDs/system/content/syllabus) = dirt pré-existente.

## Gotchas
- **claude-mem worker** caiu mid-sessão e bloqueou o tool Read no thread principal (PreToolUse). Subagents NÃO são afetados. Fix: `node ".../claude-mem/<ver>/scripts/worker-cli.js" restart` (ou reload de plugins). Nesta sessão contornou-se via subagents+Bash.
- **Hook code-review-graph PostCommit** cospe traceback cp1252 no commit — inofensivo, commit passa.
- **Console Windows cp1252:** `??` na saída é display, não corrupção.
- **`.git/sdd/`** é scratch (dentro de `.git`, oculto em explorer). Relatórios pra revisão humana copiados pra `docs/reports/2026-06-20-investigacao-file-to-card/` (untracked).
- **MCPs token-savior/code-review-graph** só via hook nesta máquina (não como tools) → usar Read/Grep direcionado.
