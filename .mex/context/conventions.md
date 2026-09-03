---
name: conventions
description: Code patterns, naming, file organization, and verification rules
triggers:
  - convention
  - naming
  - code style
  - verify
  - review
  - file organization
edges:
  - target: context/architecture.md
    condition: when deciding where new logic should live
  - target: context/decisions.md
    condition: when a convention comes from an architectural decision
last_updated: 2026-08-06
---

# Conventions

## Naming

Tests: `tests/test_<topic>.py`. Use existing topic names when adding tests (discover with
`Glob tests/test_*.py`). Do not introduce a new naming scheme without a specific reason.
Layout/inventário de diretórios: ver `graphify` (dieta MEX 2026-08-06 — contagens envelheciam).

## Fixtures Copiam Contrato Real (NÃO-NEGOCIÁVEL, 2026-08-06)

Toda fixture/dado sintético de teste copia o contrato REAL da fonte que simula — nome
exato do campo (casing incluso), tipo real, formato de armazenamento real (epoch int vs
string ISO, lista vs dict, PT acentuado vs slug ASCII), encoding — e declara PROVENIÊNCIA
(arquivo real conferido, payload real da API, ou linha de código que faz o parse).
Dicionário campo-a-campo por fonte: `context/institutional.md` §Contratos de dados.

- Nunca inventar nome/formato "genérico" — dado inventado enviesa o teste (caso F5b:
  spec assumiu assigns "Entrega T1" com stem; Moodle real tinha ambos "Sala de entrega" →
  matching nunca casou, FAIL 1/8 em produção).
- Padrão de carimbo: docstring/comentário citando a conferência, como `_ctx_mf_real`
  ("kind conferido em disco") em `tests/test_motor_due_window.py`.
- Conjuntos duplicados da fonte em teste: iterar a fonte real (mata drift) E manter um
  teste de contrato com o literal esperado (mata mudança acidental) — os dois modos de
  falha são diferentes e cada um pega o que o outro deixa passar.

## Behavioral Patterns

The README flow establishes these project patterns:

- Imports are configured as entries before processing.
- Processing is queue-based.
- Difficult outputs are routed through the generated repository's manual review area.
- Image processing is handled in the `Imagens` tab of the unified Curadoria workspace.
- Repository builds and reprocesses are available as repository tasks.
- Dashboard state reflects repository task progress.
- Cronograma state exposes file-to-block allocation and manual timeline overrides.
- Reference/bibliography entries can become tutor context through BIBLIOGRAPHY and COURSE_MAP support lines.
- Timeline/unit/tag metadata is regenerated into manifest `auto_tags` and internal course dotfiles.
- Moodle/SARC-derived signals remain separate metadata fields (`source_section`, `moodle_label`, `posting_date`, `turma`, `schedule_url`) and should not overwrite display titles.
- Stash/card imports use the immediate folder name as `source_section`; ambiguous basename backfills should remain manual.
- Timeline block references prefer stable `block_uuid`; positional `bloco-NN` ids are compatibility fallbacks, not new durable truth.
- The concept resolver is feature-flagged; default routing behavior should not change unless the flag/cutover work is explicit.
- Motor de atribuição (AnchorEngine + LlmVoter) roda por curso atrás de `use_anchor_engine`/`use_llm_voter` (precedência sobre o legado `use_anchor_placement`); escreve SÓ campos `temporal_*` (nunca `computed_*`), pino manual sempre vence, funil legado intacto até o cutover F5.
- Generated output is Markdown plus LLM instruction artifacts.

## Documentation Discipline

- Use manifest data exactly: `pyproject.toml`, project name `academic-tutor-repo-builder`, version `3.0.0`, and the declared dependencies/extras.
- If scripts, linter, formatter, build-system table, or package metadata are not declared, document them as not declared instead of guessing.
- Prefer precise paths from the brief.
- Do not assert source module internals unless they were read for the task.

## Verify Checklist

Run this checklist after code or scaffold changes:

- [ ] Manifest facts match the brief or the actual manifest that was read.
- [ ] Fixture nova copia contrato real da fonte (nome/tipo/formato/encoding) e cita proveniência (ver §Fixtures acima + `institutional.md` §Contratos).
- [ ] No undeclared dependency, script, linter, formatter, build backend, or package manager was invented.
- [ ] Entry points and paths match repository spelling and separators.
- [ ] New tests follow the `tests/test_<topic>.py` convention.
- [ ] Generated-repository behavior remains compatible with the README flow.
- [ ] If changing tag behavior, update or add coverage near `tests/test_tag_catalog.py` and relevant unit/timeline scoring tests.
- [ ] If changing timeline allocation behavior, update or add coverage near `tests/test_unit_matcher.py`, `tests/test_cronograma_health.py`, and relevant timeline scoring tests.
- [ ] If changing Moodle/SARC signal capture or consumed attribution signals, update or add coverage near `tests/test_moodle.py`, `tests/test_moodle_labels.py`, and `tests/test_migrate_signals.py`.
- [ ] If changing concept-resolver behavior, update or add coverage near `tests/test_concept_resolver.py`, `tests/test_resolver_fusion.py`, and `tests/test_resolver_wiring.py`.
- [ ] If changing stable block identity, UUID migration, or dry-run persistence behavior, update or add coverage near `tests/test_block_identity.py`, `tests/test_task2_uuid_migration.py`, `tests/test_task3_human_truth_migration.py`, `tests/test_task4_eval_uuid.py`, and `tests/test_persist_gate.py`.
- [ ] If changing anchor placement or temporal block behavior, update or add coverage near `tests/test_anchor_placement.py` and `tests/test_temporal_block_wire.py`.
- [ ] If changing stash/card import behavior, update or add coverage near `tests/test_stash_import.py` and `tests/test_stash_backfill.py`.

## Fila de campanhas (user, 2026-09-03)

UMA campanha aberta, UMA proxima, o resto ESTACIONADO com uma linha "pronto quando" no handoff vivo. **Campanha so fecha
quando 100% dos itens dela foram feitos**; item nao feito nao muda de campanha sozinho — ou e feito, ou o user o retira por
decisao registrada. Ideia que surge no meio ("da para fazer X?") vai para a CAIXA DE IDEIAS do handoff (da para fazer? · quando?
· o que resolve?) e so e triada na fronteira entre campanhas. Novo lote = novo handoff, o anterior vai para
`docs/reports/_archive/`. Motivo: sete frentes "quase fechadas" ao mesmo tempo (03/09) — nenhuma fechava.
