# Handoff — pronto para CAMPANHA 3 (cutover do funil legado)

date: 2026-08-14
branch: `feat/motor-atribuicao` (HEAD `11402b2`)
sessão anterior: auditoria-enxame executada + desempates + quick wins + sentinelas

## Boot da nova sessão (ordem)

1. `mem-search` (regra global) · ler `.mex/ROUTER.md` · ler este handoff · tracker `docs/reports/pendencias.md` (header + "Mapa de deleção do cutover").
2. Insumo PRINCIPAL da campanha: `docs/reports/2026-08-14-auditoria-enxame.md` **seção 1 (Pré-cutover)** — 6 achados verificados adversarialmente, com file:line.
3. Spec de referência da família índice: `docs/superpowers/specs/2026-08-06-gerador-indice-unico-design.md` §8.

## Estado verificado (as-of 2026-08-14, HEAD 11402b2)

- Suite: **1934 passed / 1 skipped / 0 failed em ~23s** (2x mais rápida pós quick win 2.3; o 1 skip é ES2 sem casos-chave nomeados — documentado no próprio teste).
- Rollout: **5/5 cursos flag-ON** (MF/SO/ES2/IA/TCC); flags por curso em `subjects.json` (`%APPDATA%/GPTTutorGenerator/`).
- Régua MF VIVA: **50/57 = 87.7%** (`python scripts/eval_ground_truth.py ..\Metodos-Formais-Tutor tests\fixtures\eval\ground_truth_MF.csv`). Só MF tem ground_truth em fixtures; ES2/SO/TCC/IA nunca chegaram (HALT 2026-07-01).
- Sentinelas: `tests/test_caracterizacao_blocos_atual.py::CASOS_CHAVE` agora cobre IA+MF+SO+TCC (12 casos, baselines em `tests/_golden/*__casos_chave.json`). **Cutover DEVE mudar vários desses snapshots — diff é o sinal de correção, revisar e re-versionar, não temer.**
- Working tree: 1 arquivo modificado PRÉ-sessão, não tocar sem ruling: `docs/reports/gold_templates/gold_units_rotular.xlsx`.

## Commits da sessão anterior (contexto rápido)

`d097669` docs auditoria+desempates · `1d6e07c` -150 linhas UI morta · `bb19bd8` warnings loaders fail-open · `3c98813` mocks docling (suite 51.7→23.8s) · `69e050b` strip_accents fonte única · `b698028` no-ops scoring (probe 5 índices=0 diff) · `1e1c06e` checkpoint-10 incremental · `af7ba93` tracker · `11402b2` sentinelas casos-chave.

## CAMPANHA 3 — ordem imposta pelos achados (não negociável)

**1º — Fase 4 (unit/subunit no motor novo) é PRÉ-REQUISITO DURO do cutover** (achado 1.1, BLOQUEANTE): o motor novo calcula `Assignment.unit_slug` (concept_resolver.py:178) e DESCARTA (resolver_apply.py:132-137 só lê block); todos os campos de unidade que a UI lê (navigation.py:643, dialogs.py:2487/3336, timeline_dashboard.py:828) vêm do legado `resolve_unit_block_tags`. Desligar o legado antes da Fase 4 = UI sem unidade, fallback silencioso pra vazio.

**2º — consertar os 2 gaps dormentes que ATIVAM no flip** (fazem parte do cutover, não são opcionais):
- 1.2: `apply_concept_resolver` sobrescreve `computed_block_id` sem re-rodar `reconcile_unit_with_block` (content_taxonomy.py:1354-1363 vs resolver_apply.py:132-146) — re-rodar pós-apply ou mover pra dentro.
- 1.3: espelho `auto_tags` com drift REAL já hoje (attach_block_summary_fields troca computed DEPOIS do resolve sem resync da tag `bloco:` — pedagogical_regeneration.py:242) — teste de invariante + resync ANTES do flip.

**3º — flip + deleção** (Fase 3.4/5 do tracker): default ON do concept_resolver + DELETE por LISTA NOMEADA (tracker, "Mapa de deleção do cutover", itens 1-8 — símbolos que morrem, símbolos que FICAM, 5 conflitos com resolução travada). Junto:
- 1.4: aposentar `scripts/retag_manifest.py` + `scripts/eval_assignments.py` (injetam funil condenado) no MESMO commit.
- 1.6: cronograma_health fallback S2 — portar ou aposentar (decisão de fase 4/5, item 1 do mapa).
- Testes (1.5 REESCOPADO no desempate): apagar em bloco SÓ os 4 puros (911 linhas: test_resolve_unit_block_tags, test_funil_gate_ambiguidade, test_resolve_unit_block_band, test_card_block_assignment); **antes** de apagar `test_block_scorer_signals.py`, MOVER os 3 testes S4b (linhas ~273-301, única cobertura extensão→ferramenta) pra `test_entry_signals_materials.py`; `test_file_map_unit_mapping.py` (2032 linhas) = auditoria função-a-função.

**Gates de cada fase**: suite verde + régua MF ≥ 50/57 + sentinelas (diff revisado) + golds unit 5/5 (`scripts/eval_units.py` com `tests/fixtures/eval/gold_units_*.csv`) + `rebuild_diff` 0 nos 5 cursos. Protocolo do projeto: mudança que MOVE atribuição → medir antes/depois, snapshot antes de reprocess.

## Fora do escopo da campanha (não misturar)

- 2.7 signal_token_set (mexe em input de scoring — trilho eval-gated próprio).
- 2.13 smoke tests deeptutor/golds · 3.1 cache tokenização (pós-cutover) · 3.2 class_ordinal subconjunto · 3.3 unificação tokenização com multiplicidade.
- Campanha web (depois da 3; backlog no fim do tracker).

## Lições operacionais (economia de tokens/custo)

- Workflows de enxame: **`model: 'sonnet'` nos agentes de varredura/verify, Fable SÓ na síntese** — o workflow `.claude/workflows/auditoria-enxame.js` já está assim; replicar o padrão em qualquer workflow novo. Motivo: 3 estouros de limite em 48h com tudo em Fable; com mix, 45 agentes/2M tokens sem estourar.
- Cuidado com launch por NOME de workflow: dois arquivos com o mesmo `meta.name` = resolução aleatória (foi bug real; duplicata deletada). Um nome = um arquivo.
- Vereditos de verify duplicados (pause/resume) podem DIVERGIR — desempatar por evidência primária antes de agir (3/3 desta sessão caíram pró contra-veredito).
