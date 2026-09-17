# scripts arquivados em 2026-09-04 (C0 item 9, corte 1)

Movidos de `scripts/` com `git mv` (historico: `git log --follow`). Criterio medido (04/09): nenhuma referencia em docs vivos
(handoff/tracker), em `src/`, em outro script mantido ou em teste vivo — ou referencia so de prova/migracao/one-off ja encerrada.
Ficaram 37 em `scripts/` (handoff §Ferramentas + dependencias + utilitarios com teste vivo). Testes que so testavam
scripts arquivados estao em `tests/` aqui (nao rodam na suite). Para reviver um: `git mv` de volta e o import `from scripts.X`.

| script | linhas | ultimo commit | o que era |
|---|---|---|---|
| `audit_timeline.py` | 75 | 2026-06-02 |  |
| `build_gold_xlsx.py` | 527 | 2026-07-01 | Gerador de scaffold do gold material->bloco (planilha de rotulagem CEGA). |
| `build_golden_metodos_formais.py` | 176 | 2026-06-12 | Gera o golden set real do Metodos-Formais (P0 da reforma da atribuicao). |
| `build_ground_truth.py` | 471 | 2026-07-01 | Crosswalk gold xlsx (rotulado) -> ground_truth_<curso>.csv. GENERICO por --curso. |
| `build_ground_truth_IA.py` | 251 | 2026-06-29 | Conversor gold xlsx -> ground_truth_IA.csv. HALT pos-crosswalk (read-before-commit). |
| `classify_discriminant_IA.py` | 158 | 2026-06-29 | Classifica os 33 scorable em DISCRIMINANTE vs TRIVIAL por regra GEOMETRICA fixa. |
| `crosscheck_IA.py` | 203 | 2026-06-29 | Cross-check de atribuicao: 3 sinais independentes (card / roteiro / funil) |
| `dedup_md5_IA.py` | 155 | 2026-06-25 | Scan md5 do corpus IA inteiro -> grupos de colisao de conteudo. |
| `diff_pinfix_IA.py` | 102 | 2026-06-29 | Diff before-pinfix vs manifesto-novo. Critério de LIMPO FIXADO ANTES do resultado. |
| `eval_code_block_census.py` | 64 | 2026-06-16 | Censo código->bloco: compara primary_block_id (Gemini) x computed_block_id |
| `eval_subunit_census.py` | 134 | 2026-06-17 | Censo subunit/bands: distribuicao de subunidade + calibracao de band num |
| `eval_subunit_gt.py` | 41 | 2026-09-03 | Regua OFICIAL de subunidade: computed_subunit_slug vs subunit_gt_{SO,IA,ES2,TCC}.csv. |
| `eval_subunit_health.py` | 156 | 2026-08-20 | Regua de SAUDE da subunidade — sem rotulo nenhum. |
| `explain_entry.py` | 218 | 2026-08-21 | Explica, etapa a etapa, como UM arquivo foi atribuido a bloco/unidade/subunidade. |
| `fase0_prova_motor_MF.py` | 161 | 2026-07-22 | FASE 0 — prova READ-ONLY do MOTOR real vs ground_truth_MF.csv. |
| `fase1_recall_gate_MF.py` | 150 | 2026-07-22 | FASE 1 — recall do gate D4 do MOTOR real vs ground_truth_MF.csv (READ-ONLY). |
| `fase2_prova_SO.py` | 128 | 2026-07-22 | FASE 2 — prova do provider P3 (SO data-no-nome) vs ground_truth_SO.csv (READ-ONLY). |
| `fase2_prova_TCC.py` | 146 | 2026-07-22 | FASE 2 — prova do provider P4 (TCC topic-bridge) vs ground_truth_TCC.csv (READ-ONLY). |
| `fase3_prova_LLM_MF.py` | 171 | 2026-08-05 | FASE 3 — prova do TIER 3 (voto LLM) vs ground_truth_MF.csv (READ-ONLY no repo-tutor). |
| `fase4_prova_D9.py` | 158 | 2026-07-22 | FASE 4 — prova D9: apply_anchor_engine vs manifest MF (READ-ONLY no repo). |
| `fase5_prova_tier2.py` | 115 | 2026-08-07 | FASE 5 — prova TIER-2 (janela-de-prazo): 8 rows out-of-scope do gold MF. |
| `gold_score.py` | 158 | 2026-06-25 | gold_score.py — amostragem do gold (canário). SÓ amostra; NÃO pontua. |
| `gold_units_template.py` | 79 | 2026-08-07 | Gera o template de gold de unidade (U3) a partir do indice EM DISCO |
| `gold_units_xlsx.py` | 291 | 2026-08-10 | Camada de edicao xlsx pro gold de unidades (campanha 2, Task 7). |
| `harness_balde_b.py` | 91 | 2026-08-26 | Harness do balde B (rodar com os 5 repos ABLACIONADOS via scratch ablacao.py): decisao deterministica atual vs |
| `harness_cobertura.py` | 91 | 2026-08-27 | Harness OFFLINE do eixo COBERTURA: recomputa `derive_coverage_units` por entry do gold |
| `m365_probe.py` | 265 | 2026-06-08 | Spike de viabilidade M365/OneDrive — DESCARTÁVEL, não é a feature final. |
| `make_coverage_labels.py` | 138 | 2026-08-18 | Esqueleto da regua de COBERTURA (material transversal -> N unidades). |
| `make_material_coverage_labels.py` | 180 | 2026-08-20 | Gera o template de rotulagem MULTI-LABEL para material (nao referencias). |
| `marco0_prova_deterministica.py` | 320 | 2026-07-01 | MARCO 0 — prova READ-ONLY do disambiguator deterministico + ordinal-no-nome (MF). |
| `marco1_voto_llm.py` | 185 | 2026-07-01 | MARCO 1 — voto LLM (Gemini) no conjunto FLAGGED do MARCO 0 (MF). READ-ONLY no repo. |
| `measure_flip.py` | 179 | 2026-08-17 | Medicao pre/pos-flip `use_concept_resolver` em sandbox (mecanica F4, agora |
| `measure_taxonomy_fix.py` | 107 | 2026-08-18 | Medicao do fix de perda de topicos do plano de ensino (2026-08-18) em sandbox. |
| `migrate_collided_ids.py` | 158 | 2026-06-16 | Migra ids de entry colididos para o esquema fix c v2 (sufixo por extensão). |
| `migrate_gold_uuid.py` | 89 | 2026-07-22 | Migra os gold CSVs para block_uuid (decisão user 08/07): adiciona coluna |
| `moodle_backfill_sections.py` | 64 | 2026-06-08 | Backfill de source_section via METADADOS da API Moodle (sem baixar bytes). |
| `moodle_login.py` | 42 | 2026-06-07 | Debug: cunha o wstoken a partir de matrícula/senha e grava em moddle/.env. |
| `moodle_probe.py` | 118 | 2026-06-08 | Probe READ-ONLY da Moodle Web Services API (mobile app token). |
| `postcond_reimport_IA.py` | 140 | 2026-06-25 | Pos-condicao do re-import IA (mundo-42 -> mundo-63). |
| `posting_date_probe.py` | 57 | 2026-06-18 | Probe READ-ONLY do posting_date (S0): mede, por curso, o cluster de inicio-de-semestre |
| `precheck_stash_paths_IA.py` | 125 | 2026-06-25 | Pre-check READ-ONLY (PRE-import): paths distintos dos 21 notebooks do stash. |
| `refresh_reference_coverage.py` | 70 | 2026-08-18 | Recalcula a COBERTURA das referencias de um repo gerado (so a camada de refs). |
| `trace_motor.py` | 112 | 2026-06-29 | Trace READ-ONLY do motor de atribuição proposto (WindowProvider + Disambiguator). |
| `validate_references_e2e.py` | 136 | 2026-06-04 | Validação end-to-end da pipeline de referências (rede + Gemini REAIS). |

## artefato_razao/
Gerador one-off do artefato HTML 'razao dos blocos' (dados.json, dados_artefato.py, patch_razao.py, templates).

## tests/ (arquivados junto)
- `test_crosscheck_IA.py`
- `test_golden_generator.py`
- `test_posting_date_probe.py`
- `test_tipo_of.py`
