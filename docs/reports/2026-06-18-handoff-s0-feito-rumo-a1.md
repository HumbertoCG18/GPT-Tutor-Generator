# Handoff — S0 feito (merge-ready) + rumo A1 (lessons[].text no fusor)

date: 2026-06-18
branch: `feat/reconciliar-unit-bloco`
estado: **S0 código completo e merge-ready** · suíte **1483 verde** · golden PDF **5/5, confiante-errado 0** · resolver de bloco ainda **atrás da flag `use_concept_resolver` (default OFF — produção = funil)**.

## Como retomar (ler nesta ordem, NÃO reler a conversa antiga)
1. `.mex/ROUTER.md` + `.mex/AGENTS.md` (bootstrap + não-negociáveis). `.mex/context/institutional.md` (PUCRS/SARC/Moodle/Plano).
2. **Este handoff.**
3. Spec do S0: `docs/superpowers/specs/2026-06-18-s0-substrato-medicao-cross-curso-design.md` (tem o **mapa de precedência** + o achado empírico do probe).
4. Overview vivo: `docs/Overview-Sistema.html` — aba 6 (Pendências, bloco **🔴 PRECEDÊNCIA**) + aba 8 (Concluído, seção **S0**) + §0 sinais.
5. Direção geral: `docs/reports/2026-06-17-handoff-signal-registry.md` (alavancas A1–A3/A5, cutover A4, calibração A6, limpeza A7).
6. Ledger SDD (local, não commitado): `.git/sdd/progress.md` — seção S0 + follow-ups.
7. **Prefixar TODA resposta com `[Humberto]`** (CLAUDE.md). Commits terminam com `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. **Caveman mode** ativo (terse; código/commits normais).

## Objetivo macro (do usuário)
Atribuição (arquivo→bloco→unidade→subunidade + código) a ~100% **modular** (qualquer cadeira, não fix-MF). **Evitar loop de refatoração.** NÃO há rewrite: a arquitetura é sólida; o resíduo é (1) sinais limpos dropados e (2) o resolver de 70% atrás de flag OFF (produção roda funil de 41%). Caminho = EXTENSÃO do fusor + cutover (delete do funil), não reescrita.

Fila de sub-projetos: **S0 (feito)** → S0b → **A1 (próximo)** → A2 → A3 → A5 → A4 (cutover) → A6 → A7 (limpeza). Cada um: spec→plano→eval-gate cross-curso.

## Mapa de PRECEDÊNCIA (verificado por leitura — crítico, não mexer às cegas)
Vários sistemas decidem, em **pilha determinística (maior vence)**:
- **BLOCO** (`resolve_unit_block_tags`, content_taxonomy.py:1137-1236): `manual` (1.0) > `review_rule` (0.95) > `card`/`card+scorer` (`source_section`→`lookup_card_blocks`, 0.85/0.80) > `scorer_only` (`score_entry_against_timeline_block`, gate 0.95, 0.70). + janela S5 `assign_due`. + **[resolver, flag ON]** `apply_concept_resolver` (resolver_apply.py:111) pós-processa e SOBREPÕE `computed_block_id` — **OFF em produção**.
- **UNIDADE:** `manual_unit_slug` (1.0) > auto scorer + `tag_profile` boosts > `reconcile_unit_with_block` (bloco define unidade se `block_confidence ≥ unit_confidence`).
- **SUBUNIDADE:** `manual_subunit_slug` (1.0) > subtopic scorer (gated `SUBUNIT_TAG`), **input enriquecido com resumo Gemini de código** (`code_curation`).

GOLDEN intocáveis: `assign_units_positional` (unit_matcher.py:52), `_build_timeline_index` (timeline/index.py:2026), `finalize_block`, review rule, flag-OFF, golden PDF 5/5.

## O que o S0 entregou (commits e7d4e61..HEAD, ~18 commits)
Captura **aditiva** (não muda atribuição; verificado: rebuild_diff = drift pré-existente, não do S0):
- `SectionFile.timemodified/timecreated` + `iter_section_files`; `backfill_posting_date_from_api`/`posting_date_iso`; `FileEntry.posting_date(+_created)` ISO.
- `parse_moodle_course.turma`; `SubjectProfile.turma/schedule_url`; `parse_sarc_turma_key`; persistência do `schedule_url` pela UI (`HTMLImportDialog`→`SubjectManagerDialog._save`).
- Split DRY `backfill_repo_signals_additive` × `_consumed` (moodle.py); `import_moodle_courses` usa os dois.
- `scripts/migrate_signals.py` (additive, dry-run+`.apibak`, `--year` auto-derivado), `scripts/posting_date_probe.py`, gate `load_predictions_from_gold`+`check_baseline` (eval_ground_truth.py).
- Fixes: `make_ground_truth_template` standalone (`bc2cbcc`); `sanitize_folder_name` preserva datas `18/06→18.06` (`e6d7fa1`).
- Rotulagem de gold: `scripts/propose_gold.py`, `scripts/gold_by_card.py`, `scripts/expand_card_gold.py`.

**Migração `--write` JÁ aplicada nos 5 repos** (com `.apibak`): capturados posting_date/moodle_label/lessons_index. Cursos 2026/1 (repo : moodle_course_id):
`Metodos-Formais-Tutor:92717` · `Inteligencia-Artifical-Tutor:93156` · `Sistemas-Operacionais-Tutor:92854` · `Engenharia-Software-2-Tutor:92714` · `TCC-Tutor:93728`. (Repos em `C:\Users\Humberto\Documents\GitHub\*-Tutor`.)

## Pendência do usuário (gold cross-curso — destrava o eval-gate de A1)
1. Rotular `docs/reports/gold_templates/gold_by_card_<curso>.csv` (1 linha por card: confirmar `true_block_id` usando `block_aulas`=# do cronograma + `block_dates`; linhas `(sem card)` = por arquivo). Cards: MF 6, IA 9, SO 5, ES2 3, TCC 13 (+ avulsos).
2. `python -m scripts.expand_card_gold "<repo>" "docs/reports/gold_templates/gold_by_card_<curso>.csv" "tests/fixtures/eval/ground_truth_<curso>.csv"`.
3. Medir + travar baseline: `evaluate_ground_truth(load_predictions_from_gold(csv), load_labels_csv(csv), {})` → gravar `block_accuracy`/`confident_wrong` num teste de gate (mirror de `tests/test_eval_code_block_gold.py`).

## A1 — próximo sub-projeto (consumir `lessons[].text` no fusor)
**Tese:** o resumo-da-semana (mapa data→tópico do PRÓPRIO professor) é o sinal mais limpo/autoral; resolve subunidades finas sem curadoria manual. **Dado live confirmado (ano 2026): MF 32, IA 31, ES2 15 datas; SO/TCC 0** → modular em 3/5, degrada honesto onde o prof não posta.
- Captura PRONTA: `build_lesson_topic_index` → `course/.lessons_index.json` (já gravado pela migração). `load_lessons_index` (resolver_apply.py) existe como infra.
- **Lição da reversão anterior (alavanca 0):** consumir a lesson casando contra os `concepts` do Gemini (ruidosos) REGREDIU o gold 11→10. **A chave (agora possível):** casar a lesson contra a identidade LIMPA = `moodle_label` (capturado na alavanca 1, já ativo no resolver) e/ou contra `topic_text` do bloco por DATA, não contra concepts opacos.
- Ponto de entrada do sinal: `collect_entry_unit_signals` (entry_signals.py) → novo canal (ex.: `lesson_term`) → termo pesado no fusor `concept_resolver` (concept_resolver.py:289-306). Eval-gate: `eval_code_block_gold.py` (MF) + os novos golds cross-curso; sem regredir golden 5/5.
- Começar por **brainstorming** (skill) → spec → plano → subagent-driven (mesmo fluxo do S0).

## Recursos disponíveis (automatização)
- **Moodle API:** token mobile em `moddle/.env` (`MOODLE_URL`/`MOODLE_TOKEN`). `scripts/moodle_probe.py` (read-only, `--dump <id>` despeja JSON cru), `scripts/moodle_pull.py`, `scripts/migrate_signals.py`. `core_course_get_contents` traz tudo (label, timemodified, contents, summary, description, dates).
- **Microsoft 365 / Graph:** `m365.py` (DriveItem `lastModifiedDateTime`/`createdDateTime`/`description` — sub-usado). Fonte só de `source_section` hoje.
- **OpenSARC (ASP.NET):** cronograma via `Export.aspx?id=<GUID-turma>&ano=&sem=` → `fetch_schedule_html` (GET) → `_parse_aspnet_schedule` (DataGrid `dgAulas`). **Aluno é READ-ONLY — nunca escrever no SARC.** Campos sub-usados no export: recursos/sala, horário, dia-da-semana.

## Eval-gates / comandos
- Suíte: `python -m pytest tests -q` (1483).
- Golden PDF: `python scripts/eval_assignments.py` (5/5, cw 0).
- Gold de código (MF): `python scripts/eval_code_block_gold.py "<repo>"`.
- Gold file→bloco (cross-curso): `python scripts/eval_ground_truth.py "<repo>" "<labels.csv>"`.
- Rebuild-diff 5 cursos: `python scripts/rebuild_diff.py` (mostra drift pré-existente ES2 7/IA 20/SO 13 — dívida A7, NÃO regressão).
- Probe posting_date: `python -m scripts.posting_date_probe --course <id> --year 2026`.

## Follow-ups abertos (não-bloqueantes)
- Migrador **standalone** (`migrate_signals`) não grava `turma` (só `import_moodle_courses` grava) — derivar do curso como faz `_resolve_year`.
- `SubjectManagerDialog._save` (dialogs.py:1503-1525) dropa `moodle_course_id`/`m365_filter` ao salvar matéria (bug PRÉ-EXISTENTE; Task 5b preservou só schedule_url/turma).
- **A7:** 4/5 `.timeline_index.json` STALE (ES2 7/IA 20/SO 13/MF 1 blocos) — regravar num momento controlado, DEPOIS do cutover A4.
- **Refazer abas 1-5 (diagramas) do Overview** após o refactor de atribuição (registrado na aba 6).

## Gotchas
- Hook `code-review-graph` PostCommit cospe traceback **cp1252** no Windows — inofensivo, commit passa. `LF→CRLF` idem.
- Flag `use_concept_resolver` default OFF: produção = funil. O resolver (e o consumo de A1) só roda com flag ON; o cutover (A4) liga e deleta o funil legado.
- Gold `media`/`baixa` no gabarito = revisar (predições divergem); circularidade: gold feito por máquina avaliando máquina não prova precisão — a verificação humana é o que torna gold confiável.
