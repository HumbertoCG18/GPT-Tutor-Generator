# Resolver único de atribuição em espaço de conceito — Plano de Execução (P2)

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` pra implementar task-a-task. Os passos usam checkbox (`- [ ]`).

**Goal:** Substituir a família de scorers léxicos + 2 rotas card→bloco + gate D1 (LLM band-restrito) + fallback keyword por UM resolver de atribuição (material→bloco/unidade) em espaço de conceito, eval-gated, sem regredir o gabarito.

**Architecture:** Migração faseada atrás de gates. Fase 1 consolida normalizadores/stopwords (não-comportamental, guard byte-idêntico). Fase 2 implementa o resolver em paralelo, atrás de flag, comparado por censo+rebuild-diff. Fases 3-5 fazem cutover (bloco → unidade+fold do fallback → limpeza), cada uma só após o resolver provar ≥ atual.

**Tech Stack:** Python 3.13, pytest. Sem libs novas. Gemini via `google-genai` (lazy, dentro de método). Concepts já vêm do `code_curation.json`.

**Spec:** `docs/superpowers/specs/2026-06-17-resolver-atribuicao-conceito-design.md` (ler antes).

## Global Constraints

- Lógica nova NUNCA em `engine.py` (facade). Imports de submódulos focados.
- Sem libs novas. `google-genai` lazy dentro de método (nunca top-level).
- Eval-gates de TODA fase que muda atribuição: `python scripts/eval_assignments.py` = **5/5, confiante-errado 0**; `python -m pytest tests -q` verde; `python scripts/eval_code_block_census.py <repo>` (confiante-errado não sobe); `python scripts/eval_subunit_census.py <repo>` (subunit-fora-da-unidade não sobe); `python scripts/rebuild_diff.py` (diffs explicáveis nos 5 cursos).
- Censo reflete repo gerado → reprocessar (app reiniciado OU `scripts/reprocess_assignments.py`) ANTES de medir.
- Não tocar a rota autoritativa do SARC (`source_kind`/kind) nem o P3.4.
- Sem comentário óbvio; só WHY não-óbvio. Sem docstring multi-parágrafo.

---

## Fase 1 — Consolidação de normalizadores/stopwords (não-comportamental)

Objetivo: uma base única de normalização + stopwords, com guard byte-idêntico. ZERO mudança de saída. Funda a fundação do resolver sem risco. É o degrau seguro e é o que destrava medir o resto.

Divergências conhecidas a reconciliar (mapeadas por grep, 17/06):
- `src/builder/extraction/content_taxonomy.py:32` `_normalize_match_text` (paths/slugs como tokens — keep especial).
- `src/builder/text/normalize.py:8` `normalize_match_text(text, *, keep="")`.
- `src/builder/timeline/classifier.py:20` `_norm` (NFKD + só `[a-z0-9 ]`).
- `src/builder/timeline/index.py:300` `_TIMELINE_GENERIC_TOKENS` (+ `:367` `_TIMELINE_UNIT_NEUTRAL_TOKENS`).
- `src/builder/routing/file_map.py` `UNIT_GENERIC_TOKENS` (import).
- `src/builder/timeline/unit_matcher.py:22` `_STOPWORDS`.
- `src/builder/timeline/card_block.py:19` `_STOP`.

### Task 1.1: Inventário e guard byte-idêntico dos normalizadores

**Files:**
- Test: `tests/test_normalize_consolidation.py` (criar)

- [ ] **Step 1: Ler as 4 implementações** (`content_taxonomy._normalize_match_text`, `text/normalize.normalize_match_text`, `classifier._norm`, e qualquer `_normalize*` em `index.py`) e tabular as diferenças reais (keep, NFKD, faixa de chars, colapso de espaço). Registrar a tabela no topo do arquivo de teste como comentário.

- [ ] **Step 2: Escrever o guard byte-idêntico** — corpus de strings reais (títulos/topics/labels dos 5 cursos + acentos + slugs + paths + hífens). Para cada normalizador, snapshot do output atual:

```python
import pytest
from src.builder.extraction.content_taxonomy import _normalize_match_text
from src.builder.text.normalize import normalize_match_text
from src.builder.timeline.classifier import _norm

CORPUS = [
    "Lógica de Hoare", "Especificação de Conjuntos Indutivos",
    "pre-condicao/pos-condicao", "C:/Moodle/Métodos Formais/intro.thy",
    "P1 — Prova", "Verificação de Programas", "TDE Trabalho",
]

@pytest.mark.parametrize("s", CORPUS)
def test_snapshot_normalizers(s, snapshot):
    # snapshot = baseline do comportamento ATUAL de cada normalizador.
    assert {"taxonomy": _normalize_match_text(s),
            "text": normalize_match_text(s),
            "classifier": _norm(s)} == snapshot
```
(Se não houver fixture de snapshot no projeto, materializar os valores esperados inline — rodar uma vez, colar a saída como `expected`.)

- [ ] **Step 3: Rodar — verde** (baseline capturado). Run: `python -m pytest tests/test_normalize_consolidation.py -q`. Expected: PASS.

- [ ] **Step 4: Commit.** `git add tests/test_normalize_consolidation.py && git commit -m "test: guard byte-identico dos normalizadores (pre-consolidacao P2)"`

### Task 1.2: Base única de normalização

**Files:**
- Modify/Create: `src/builder/text/normalize.py` (base canônica — já é o módulo de texto)
- Modify: os 3 call-sites pra delegar à base, preservando o `keep`/modo de cada um via parâmetro.

**Interfaces:**
- Produces: `normalize_match_text(text, *, keep="", nfkd=True)` cobre os 3 modos (taxonomy usa `keep` para paths/slugs; classifier usa modo estrito). Os wrappers locais (`_normalize_match_text`, `_norm`) viram finos delegadores com o `keep`/modo certo, mantendo a assinatura pública.

- [ ] **Step 1:** Estender `normalize_match_text` pra cobrir os 3 modos por parâmetro (sem mudar default). Reescrever `_normalize_match_text`/`_norm` como delegadores.
- [ ] **Step 2:** Rodar o guard da Task 1.1 — deve seguir **byte-idêntico** (PASS). Se quebrar, a base não cobre um modo → ajustar até idêntico.
- [ ] **Step 3:** Rodar suíte completa: `python -m pytest tests -q` — verde.
- [ ] **Step 4: Eval-gate** (sem reprocess; só código): `python scripts/eval_assignments.py` = 5/5. Commit.

### Task 1.3: Stopwords unificadas (com escopos preservados)

Consolidar `_TIMELINE_GENERIC_TOKENS` / `UNIT_GENERIC_TOKENS` / `unit_matcher._STOPWORDS` / `card_block._STOP` numa fonte única — **preservando o conceito de escopo** já existente (`_TIMELINE_UNIT_NEUTRAL_TOKENS` = neutro-pra-unidade ≠ genérico-geral). NÃO fundir escopos diferentes num set só.

- [ ] **Step 1:** Escrever guard: para cada consumidor, snapshot do set efetivo atual (teste de igualdade de conjunto).
- [ ] **Step 2:** Mover os sets pra um módulo único (`src/builder/text/stopwords.py`), re-exportar nos locais antigos (sem mudar membros).
- [ ] **Step 3:** Guard verde (sets idênticos) + suíte verde + golden 5/5. Commit.

**Gate de saída da Fase 1:** suíte verde, golden 5/5, guards byte-idênticos verdes, censo código→bloco e subunit **inalterados** vs baseline (17/06). Nenhuma mudança de comportamento.

---

## Fase 2 — Resolver de conceito atrás de flag + harness de comparação

Objetivo: o resolver novo roda em PARALELO ao funil, sem cutover, e a gente mede a diferença. É onde a calibração (questão aberta da spec §9) é resolvida empiricamente.

### Task 2.1: Esqueleto do resolver + representação de conceito

**Files:**
- Create: `src/builder/routing/concept_resolver.py`
- Test: `tests/test_concept_resolver.py`

**Interfaces:**
- Produces:
  `resolve_material_assignment(entry, blocks, units, *, signals, llm_curation=None) -> Assignment`
  `Assignment = {block_id: str, unit_slug: str, confidence: float, band: str, method: str, signals: dict, conflict: dict|None}`
  `concept_vector(text_or_block, *, scope) -> dict[str, float]` (tokens normalizados × peso de discriminância no escopo).

- [ ] **Step 1:** Test de representação — `concept_vector` dropa ferramenta uniforme na unidade. Caso: bloco "Indução árvores" (u1) e "teoremas Isabelle" (u1) ambos contêm "isabelle" → peso de "isabelle" ≈ 0 no escopo da unidade-01; "arvores"/"teoremas" mantêm peso. (Usa os blocos reais do MF como fixture mínima.)
- [ ] **Step 2:** Rodar — FAIL (módulo não existe).
- [ ] **Step 3:** Implementar `concept_vector` com IDF no escopo (princípio B'/spec §4.2): `df` sobre os blocos DA UNIDADE pra escolha de bloco; sobre as unidades pra escolha de unidade. Reusa `known_tools` do `semantic_profile` + extensões como conjunto de ferramenta/formato.
- [ ] **Step 4:** PASS. Commit.

### Task 2.2: Fusão de sinais + tiers + confiança/conflito

- [ ] **Step 1:** Tests (casos reais MF do censo):
  - arvores → bloco-05 (não 06); intro → 04; listas → 05; classes-parte1 → 15/unidade-02.
  - NÃO regredir: colecoes-* → 13; invariantes/terminacao → 11; hoare → 10.
  - conflito flagado quando bloco-unit ≠ tópico-unit (os 7 subunit MF) — subunit restrita à unidade vencedora.
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** Implementar fusão (spec §4.3-4.5): overlap de conceito + voto LLM ponderado + data + sequência + card-evidence; tiers (manual > card/data > concept-match > posicional); `relative_margin_confidence`; conflito quando fontes fortes discordam.
- [ ] **Step 4:** PASS + suíte verde. Commit.

### Task 2.3: Harness de comparação resolver × funil

**Files:**
- Create: `scripts/compare_resolver.py` (read-only; roda os dois caminhos sobre um repo gerado e diffa bloco/unidade/subunit/band, reusando os carregadores dos censos existentes).

- [ ] **Step 1:** Implementar: para cada material, `(funil_atual)` vs `resolve_material_assignment(...)`, imprimir diffs + contadores (mudou bloco/unit/subunit; conflitos novos).
- [ ] **Step 2:** Rodar nos 5 cursos (reprocessados). Registrar o resultado num relatório `docs/reports/2026-06-NN-resolver-baseline.md`.
- [ ] **Step 3:** Calibrar os pesos de fusão (§9) até: corrige os 4 casos, não regride os 6, golden 5/5, confiante-errado não sobe. Iterar com o harness. Commit a cada calibração estável.

**Gate de saída da Fase 2:** resolver ≥ funil no gabarito + censo (corrige ≥4, regride 0), atrás de flag, SEM cutover. Relatório de baseline commitado.

---

## Fase 3 — Cutover do BLOCO (milestone)

> Detalhamento bite-sized escrito ao chegar aqui (depende do baseline da Fase 2).

- Trocar o caminho de `computed_block_id` (`content_taxonomy`/`file_map`) pra usar o resolver.
- Deletar S2/S4 (`block_token_weights`/`TOOL_BOOST`/`TOOL_PENALTY`), `score_entry_against_timeline_block` legado, `select_probable_period_for_entry`, `_best_instructional_block_fallback`, 2 rotas card→bloco.
- **Gate:** golden 5/5, censo código→bloco (os 4 corrigidos, confiante-errado 0), rebuild-diff nos 5 cursos explicável, suíte verde.

## Fase 4 — Cutover da UNIDADE + fold do fallback (milestone)

> Detalhamento bite-sized ao chegar aqui.

- Mover `computed_unit_slug` pro resolver; reconciliação bloco×plano com conflito flagado (resolve os 7 subunit-fora-da-unidade do censo MF).
- Deletar fallback keyword ~600 linhas (`index.py:2205` else + `_assign_timeline_block_to_unit`/`_vote_unit_from_topic_candidates`/`_score_timeline_row_against_unit`) com **fold** dos sinais que ele tinha e o posicional não (nº explícito "Unidade N", frases/âncoras).
- Deletar `_derive_unit_specs_from_repo` se confirmado nunca-hit (resolve a divergência latente `unit_index`×`content_taxonomy`).
- **Gate:** golden 5/5, censo subunit (0 subunit-fora-da-unidade silencioso; conflitos flagados), guard "posicional nunca [] no golden", suíte verde.

## Fase 5 — Limpeza (milestone)

> Detalhamento ao chegar aqui.

- Remover normalizadores/predicados duplicados restantes; gate D1 (`attach_block_summary_fields` band-restrito) substituído pelo sinal LLM fundido.
- **Gate:** suíte verde, golden 5/5, doc vivo (Overview) atualizado.

---

## Self-Review (checklist do autor)

- **Cobertura da spec:** §3 princípios A–F → Tasks 1.x (consolidação/escopo) + 2.1 (B/B') + 2.2 (C/D/E); §4 arquitetura → 2.1/2.2; §5 deletes → Fases 3-5; §6 gates → Global Constraints + gate de cada fase; §7 migração → as 5 fases; §8 riscos → gates faseados; §9 abertas → 2.3 (calibração) + 4 (divergência timeline×plano).
- **Placeholders:** Fases 3-5 são milestone-level POR DESIGN (dependem do baseline da Fase 2; código exato seria fabricação agora) — cada uma ganha plano bite-sized próprio ao ser alcançada. Fases 1-2 têm tasks/passos/tests concretos.
- **Consistência de tipos:** `Assignment` (2.1) usado em 2.2/2.3; `resolve_material_assignment`/`concept_vector` nomes estáveis.
