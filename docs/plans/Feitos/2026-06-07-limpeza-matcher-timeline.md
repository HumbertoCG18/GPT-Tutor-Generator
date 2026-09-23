# Limpeza do subsistema matcher/timeline (dead code + unificação) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax. Cada task é independente e testável; rodar a suíte completa após cada uma. As tasks H3/H4/M1/M3 mudam comportamento de scoring → SÓ executar com o eval harness confiável (gate de regressão via `scripts/rebuild_diff.py` + `scripts/eval_assignments.py`).

**Goal:** Reduzir dívida técnica no subsistema arquivo→bloco / bloco→unidade / cronograma (mapeado por auditoria em 2026-06-06): remover código morto, unificar duplicações, consolidar normalizadores/vocabulários, sem regressão.

**Architecture:** Mudanças em ordem de risco crescente. Removeções puras primeiro (zero comportamento), consolidações value-identical depois, unificações de scoring (comportamentais) por último e atrás de eval.

**Tech Stack:** Python 3.11/3.13, pytest. Guards: `scripts/rebuild_diff.py` (deltas unit/kind nos 5 cursos), `scripts/eval_assignments.py` (gold arquivo→bloco), suíte completa.

**Fonte:** auditoria read-only de 2026-06-06 (resultado no histórico da sessão). Itens referenciados por ID (H=high, M=med, L=low).

---

## Sequência recomendada (da auditoria)
1. **H2** (decidir contrato `administrative_only`) — gate semântico de M3.
2. **H1** (deletar matcher morto) — remoção pura, ~180 linhas + testes.
3. **M2 + M4 + L1** (vocab/helpers/normalizadores) — mecânico, value-identical.
4. **H3** (signal-key mismatch) — atrás de eval.
5. **H4 + M1 + M3** (unificar scorers/predicados) — maior superfície; só com eval confiável.

---

## Task A (H1): deletar o matcher morto `_match_timeline_to_units_generic`

**Files:** `src/builder/timeline/index.py` (~250-427), `src/builder/facade/teaching_timeline.py`, `src/builder/engine.py` (`__all__` + aliases), `tests/test_core.py` (~2900-3025, 3329).

**Evidência:** `_match_timeline_to_units_generic`/`_match_timeline_to_units` só têm callers em `tests/test_core.py`; nenhum em `src/`. Superseded por `_build_timeline_index` → matcher posicional.

- [ ] **Step 1:** Confirmar zero callers de produção: `grep -rn "_match_timeline_to_units" src/ --include=*.py` (esperado: só definição + facade/engine re-export, nenhum call-site real).
- [ ] **Step 2:** Remover `_match_timeline_to_units_generic` (e helpers aninhados só usados por ele: `_normalize_token_text`, `_tokenize_signal`, e a 2ª inferência de date-keys ~264-273 — L2). Remover os aliases em `facade/teaching_timeline.py` e as entradas em `engine.__all__`/wiring.
- [ ] **Step 3:** Remover o bloco de testes correspondente em `tests/test_core.py` (os testes do caminho morto).
- [ ] **Step 4:** `python -m pytest -q` (verde; contagem cai pelos testes removidos do caminho morto).
- [ ] **Step 5:** Commit `refactor(timeline): remove dead _match_timeline_to_units_generic matcher`.

---

## Task B (H2): resolver o contrato `administrative_only`

**Files:** `src/builder/routing/file_map.py:~505`, `src/builder/extraction/content_taxonomy.py:~975`, `src/builder/artifacts/cronograma_health.py:~124`, `src/builder/timeline/index.py` (`_serialize_timeline_index` ~1099-1147).

**Problema:** `administrative_only` é LIDO em 3 lugares mas NUNCA escrito — o serializer DROPA blocos administrativos em vez de marcá-los. Os 3 filtros são no-ops; contrato inconsistente (risco se um dia blocos admin forem mantidos no índice).

- [ ] **Step 1 (decisão):** escolher contrato:
  - (a) persistir `administrative_only: True` no serializer (parar de dropar) → os 3 leitores viram reais; OU
  - (b) deletar os 3 filtros mortos e documentar que a serialização dropa.
  Recomendado: **(b)** (menor superfície) a menos que a UI precise exibir blocos admin.
- [ ] **Step 2:** TDD do contrato escolhido (teste afirmando o comportamento). 
- [ ] **Step 3:** Implementar; `python -m pytest -q` verde.
- [ ] **Step 4:** Commit `refactor(timeline): settle administrative_only contract (<a|b>)`.

---

## Task C (M2+M4+L1): consolidar vocabulários, helpers e normalizadores

**Files:** novo `src/builder/text/tokens.py` (ou usar `text/normalize.py` existente) + call-sites.

**Itens:**
- **M2:** `_UNIT_GENERIC_TOKENS` (index.py:~607) == `UNIT_GENERIC_TOKENS` (file_map.py:~24) — idênticos. Unificar num módulo, importar nos dois.
- **M4:** `_collapse_ws` ×4 (index.py, content_taxonomy.py, core/semantic_config.py, core/reference_content.py) idênticos → 1 canônico. `_normalize_unit_slug` em index.py:113 == teaching_plan.py:191 → index importa de teaching_plan (como `conflicts.py` já faz). `_signal_token_set` ×2.
- **L1:** `classifier._norm` e `signals._normalize_match_text` não aplicam o fix "propocional→proposicional" que o canônico `text/normalize.normalize_match_text` aplica → mesma pipeline, 2 tokenizações. Fazer ambos delegarem ao canônico (manter a variante non-stripping de signals onde necessária).

- [ ] **Step 1:** Mover `_collapse_ws` + `UNIT_GENERIC_TOKENS` p/ módulo canônico; testes de paridade (mesma saída).
- [ ] **Step 2:** Substituir as cópias por imports; `python -m pytest -q` verde após cada substituição.
- [ ] **Step 3:** `index._normalize_unit_slug` → import de teaching_plan; remover a cópia.
- [ ] **Step 4:** `classifier._norm`/`signals._normalize_match_text` delegam ao canônico (cuidado: muda tokenização do classifier — rodar `rebuild_diff.py` e conferir deltas de kind; aceitar só se coerente).
- [ ] **Step 5:** Commits separados por item (`refactor(text): unify <x>`).

---

## Task D (H3): corrigir o signal-key mismatch do scorer bloco→tópico

**Files:** `src/builder/timeline/index.py` (`_build_timeline_block_topic_signals` ~1843, `_score_entry_against_taxonomy_topic` ~1738).

**Problema:** o builder emite `tags_text` (aliases do bloco) que o scorer NÃO lê; e o scorer lê `markdown_headings_text`/`markdown_lead_text`/`manual_tags_text` (pesos altos 4.4/2.8/3.0) que o builder NUNCA seta para blocos → matching bloco→tópico roda num subconjunto degradado. (Nota: o matcher posicional novo reduz a dependência disto, mas o scorer ainda alimenta `topic_candidates`/labels.)

- [ ] **Step 1:** Alinhar as chaves: mapear aliases do bloco → `manual_tags_text` (ou adicionar canal de alias ao scorer). Teste de paridade de chaves (contrato).
- [ ] **Step 2:** **GATE EVAL:** rodar `scripts/eval_assignments.py` + `scripts/rebuild_diff.py` antes/depois; aceitar só se melhora/neutro.
- [ ] **Step 3:** Commit `fix(timeline): align block->topic scorer signal keys`.

---

## Task E (H4+M1+M3): unificar scorers e predicados (maior risco — só com eval)

**Files:** `index.py`, `routing/file_map.py`, `classifier.py`, `extraction/content_taxonomy.py`.

**Itens (NÃO fazer num passo só; cada um atrás de eval):**
- **H4:** 3 cópias do "score text vs unit descriptor" (`_score_entry_against_taxonomy_topic`, `score_entry_against_unit`, `_score_timeline_row_against_unit`) com constantes que divergiram → extrair 1 `score_text_against_unit_descriptor(...)` paramétrico; as 3 delegam. Canônico base = `score_entry_against_unit` (mais rico).
- **M1:** unificar a cadeia de unit-assignment (`_derive_unit_from_topic_match` + `_assign_timeline_block_to_unit` + `_vote_unit_from_topic_candidates`) num `assign_block_unit(...) -> (slug, conf, source)`. NOTA: o matcher posicional já é o primário; o fallback usa `_assign`/`_vote`. `_derive_unit_from_topic_match` provavelmente está MORTO agora (verificar callers) → candidato a remoção.
- **M3:** rotear os predicados `_timeline_block_is_noninstructional/administrative_only` por `classify_block` + `NON_ACADEMIC_KINDS`; consolidar as listas de keyword/phrase duplicadas (`_TIMELINE_ADMIN_PHRASES`, lista inline em ~686, `content_taxonomy._is_exam_review_signal`) na fonte única do classifier.

- [ ] **Step 1:** Verificar se `_derive_unit_from_topic_match` virou dead code pós-Plano-2 (`grep -rn`); se sim, remover (commit separado, puro).
- [ ] **Step 2..N:** Cada unificação como task TDD própria, **gate eval** (`eval_assignments.py` + `rebuild_diff.py`) antes/depois. Não agrupar.
- [ ] Commits separados por item.

---

## Notas de execução
- **Ordem importa:** A→B→C antes de D→E (D/E são comportamentais e precisam de eval estável).
- Guard de regressão obrigatório nas tasks comportamentais (D/E/C-step4): `python scripts/rebuild_diff.py` (revisar deltas) + `python scripts/eval_assignments.py`.
- Hook `code-review-graph.exe` imprime `UnicodeEncodeError` cosmético; commit passa.
- Trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- NÃO regravar índices dos cursos reais como efeito colateral — só via reprocess decidido pelo usuário.
