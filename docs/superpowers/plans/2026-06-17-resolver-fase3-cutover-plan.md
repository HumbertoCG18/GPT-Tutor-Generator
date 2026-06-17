# Resolver de conceito — Fase 3: pré-cutover + cutover do BLOCO (plano)

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA: `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans`. Passos com checkbox (`- [ ]`).

**Goal:** Trocar o caminho de produção de `computed_block_id` (material→bloco) do funil léxico (S2/S4/scorers/2 rotas de card) para o resolver de conceito (`concept_resolver.resolve_material_assignment`) — só DEPOIS de provar, num eval honesto, que o resolver ≥ funil.

**Architecture:** A Fase 2 entregou o resolver atrás de flag (não-wired). O baseline da Fase 2 (`docs/reports/2026-06-17-resolver-baseline.md`) revelou que NÃO dá pra julgar o resolver hoje: (1) o `computed_block_id` do funil está stale (linhagem `generated_at` 03/2026) vs os votos atuais do `code_curation` (16/06) → comparação confundida; (2) o eval é só 5 PDFs — as ~12 entries de código/zip (onde o resolver mais difere) não têm gold. Logo a Fase 3 começa CONSTRUINDO o eval (3.1 reconciliar inputs, 3.2 gold de código), só então faz o cutover gated (3.3 atrás de flag, 3.4 default + delete do legado).

**Tech Stack:** Python 3.13, pytest. Sem libs novas. `google-genai` lazy. Reusa `concept_resolver` (Fase 2) + `text/normalize`+`text/stopwords` (Fase 1).

**Specs:** design `docs/superpowers/specs/2026-06-17-resolver-atribuicao-conceito-design.md`; plano-mãe `docs/superpowers/plans/2026-06-17-resolver-atribuicao-conceito-plan.md` (Fase 3 era milestone — este plano a detalha); baseline `docs/reports/2026-06-17-resolver-baseline.md`.

## Global Constraints

- Lógica nova NUNCA em `engine.py` (facade). Imports de submódulos.
- Sem libs novas. `google-genai` lazy dentro de método (nunca top-level; nesta fase NÃO chamar API — só ler `code_curation.json`).
- **Flag de resolver:** o caminho do resolver entra atrás de uma config (default **OFF**) na 3.3; só vira **default ON** na 3.4, após o gate. Enquanto OFF, produção = funil atual (zero mudança).
- **Eval-gates de toda fase que muda atribuição:** `python scripts/eval_assignments.py` = **5/5, confiante-errado 0** (golden de PDF, nunca regride); `python -m pytest tests -q` verde; censo código→bloco (`scripts/eval_code_block_census.py`) e subunit (`scripts/eval_subunit_census.py`) sem piora; `python scripts/rebuild_diff.py` (diffs explicáveis nos 5 cursos); a partir da 3.2, **gold de código** (resolver ≥ funil, confiante-errado ≤ funil).
- Censo reflete repo gerado → reprocessar (app reiniciado OU `scripts/reprocess_assignments.py`) ANTES de medir.
- NÃO tocar rota SARC (`source_kind`/kind) nem o P3.4. Curadoria manual sempre vence.
- Sem comentário óbvio; só WHY não-óbvio. Sem docstring multi-parágrafo.

---

## Fase 3.1 — Reconciliar manifest ↔ code_curation (baseline honesto)

Objetivo: eliminar o drift de input. O `computed_block_id` armazenado no manifest precisa refletir os VOTOS ATUAIS do `code_curation` (não a linhagem 03/2026), pra que funil e resolver sejam comparados sobre os MESMOS insumos. Não muda o algoritmo do funil — só re-roda a atribuição sobre o estado atual.

### Task 3.1.1: Reconciliação determinística + diagnóstico

**Files:**
- Reusar: `scripts/reprocess_assignments.py` (headless `regenerate_pedagogical_files`) e/ou `scripts/retag_manifest.py`.
- Criar (se preciso): `scripts/diagnose_block_lineage.py` — read-only, reporta por entry: `manifest.computed_block_id` vs `code_curation.summary.primary_block_id` vs `computed_block_method`, e a `generated_at` da linhagem do bloco.

- [ ] **Step 1:** Rodar o diagnóstico no MF: quantas entries têm `computed_block_id` divergente do voto atual do `code_curation` e qual o método (`llm_only`/`consensus`/`card`). Salvar a tabela.
- [ ] **Step 2:** Reprocessar o MF (`python scripts/reprocess_assignments.py "…/Metodos-Formais-Tutor"`) — re-roda `regenerate_pedagogical_files` → `attach_block_summary_fields` lê o `code_curation` atual. Backup `.bak` automático.
- [ ] **Step 3:** Re-rodar o diagnóstico → confirmar que o `computed_block_id` agora bate com a regra D1 sobre os votos atuais (divergência stale = 0; o que sobrar é divergência legítima funil-léxico × LLM, não staleness).
- [ ] **Step 4:** Eval-gate: `python scripts/eval_assignments.py` = 5/5; `python -m pytest tests -q` verde. Commit (script de diagnóstico + nenhum código de produção mudado).

**Gate de saída 3.1:** o baseline (`compare_resolver`) passa a comparar funil-fresh × resolver-fresh sobre os mesmos votos. Re-rodar `scripts/compare_resolver.py` no MF e atualizar o baseline report — a divergência agora é só o sinal real (concept vs léxico), sem ruído de staleness.

---

## Fase 3.2 — Gold de código (cobertura de eval onde o resolver importa)

Objetivo: hoje o único ground truth é 5 PDFs. As ~12 entries de código/zip (onde o resolver diverge do funil) não têm rótulo → impossível cravar quem acerta. Esta fase cria o gold de código. **Tem passo USER-SIDE (rótulo humano).**

### Task 3.2.1: Esqueleto do gold de código (assistido)

**Files:**
- Criar: `scripts/make_code_gold_template.py` (gera um CSV/JSON pré-preenchido com a predição atual, pro humano corrigir) — espelhar `scripts/make_ground_truth_template.py`.
- Criar (dados): `tests/fixtures/eval/code_block_gold.json` (saída rotulada).

- [ ] **Step 1:** Gerar o template no MF: por entry de código/zip — `id`, `inferred_title`, `concepts`, `funil_block`, `gemini_primary`, `resolver_block` (rodando o resolver), coluna vazia `true_block_id`.
- [ ] **Step 2 (USER-SIDE):** O humano preenche `true_block_id` por entry (decisão pedagógica: a qual bloco do cronograma o material realmente pertence). **Bloqueia aqui até o usuário entregar os rótulos** — não inventar gold.
- [ ] **Step 3:** Validar o gold (todos os `true_block_id` existem no timeline index; sem vazios não-justificados). Commit do template + do gold rotulado.

### Task 3.2.2: Harness de eval contra o gold de código

**Files:**
- Criar: `scripts/eval_code_block_gold.py` — read-only, mede funil E resolver contra `code_block_gold.json`: acurácia + **confiante-errado** (band alta + bloco ≠ gold) por método, lado a lado.

- [ ] **Step 1:** Implementar; rodar no MF → placar funil vs resolver vs gold. Salvar relatório.
- [ ] **Step 2:** Guard de regressão em `tests/` (baseline no fixture, igual ao `test_eval_assignments`).
- [ ] **Step 3:** Eval-gate (golden PDF 5/5 + suíte verde). Commit.

**Gate de saída 3.2:** existe um número honesto "resolver vs funil vs gold de código". Decisão de produto: o resolver só segue pro cutover se **≥ funil em acurácia E confiante-errado ≤ funil** no gold de código (e PDF golden 5/5 intacto). Se o resolver perder, voltar à calibração (Fase 2.2 §9) com o gold como alvo — não cutover.

---

## Fase 3.3 — Wire do resolver atrás de flag (caminho do BLOCO)

Objetivo: rotear `computed_block_id` pelo resolver quando a flag está ON, mantendo o funil como default OFF. Permite A/B no repo real sem comprometer produção.

### Task 3.3.1: Config flag + ponto de wire

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py` (onde `computed_block_id`/`period_block_id` é decidido, ~:1180-1248) — sob flag, chamar `resolve_material_assignment` em vez do funil; montar `signals`/`blocks`/`units`/`llm_curation` (reusar a montagem fiel já validada no `scripts/compare_resolver.py`).
- Modify: config/DEFAULTS — flag `use_concept_resolver` default `False`.
- Test: `tests/test_resolver_wiring.py` — com flag OFF, saída idêntica ao funil (byte-idêntico no golden); com flag ON, usa o resolver (testar num caso controlado).

- [ ] **Step 1:** Test: flag OFF → `resolve_unit_block_tags` produz EXATAMENTE o de hoje (golden 5/5 inalterado). RED se o wire vazar com flag OFF.
- [ ] **Step 2:** Implementar o wire gated; extrair a montagem de signals pra um helper compartilhado (DRY com o harness).
- [ ] **Step 3:** Flag OFF: golden 5/5 + suíte verde (zero mudança). Flag ON: rodar `eval_code_block_gold` + censos + `rebuild_diff` nos 5 cursos.
- [ ] **Step 4:** Commit. **Gate:** com flag ON, resolver ≥ funil no gold de código + golden PDF 5/5 + rebuild-diff explicável.

---

## Fase 3.4 — Cutover default + delete do legado (milestone)

> Detalhe bite-sized ao chegar, contra o `rebuild_diff` e o gold; só após o gate da 3.3.

- Flip da flag pra default **ON** (resolver = caminho de produção do bloco).
- Deletar o legado do funil de BLOCO: `file_map.score_entry_against_timeline_block` + S2 (`block_token_weights`) + S4 (`TOOL_BOOST`/`TOOL_PENALTY`/`TOOL_TOKENS`) + `select_probable_period_for_entry` + `_best_instructional_block_fallback` + as 2 rotas card→bloco (consolidar no tier de card do resolver).
- **Gate:** suíte verde, golden PDF 5/5, gold de código (resolver ≥ funil, confiante-errado 0/≤), censos sem piora, `rebuild_diff` nos 5 cursos explicável. A unidade + fold do fallback ~600 linhas continua na Fase 4 (plano próprio).

---

## Eval-gates (resumo)
- PDF golden `eval_assignments.py` = 5/5, confiante-errado 0 — invariante de TODA fase.
- Gold de código (novo, 3.2) — resolver ≥ funil, confiante-errado ≤ funil — gate do cutover.
- Censos código→bloco + subunit — sem piora.
- `rebuild_diff` nos 5 cursos — diffs explicáveis.
- Suíte `pytest tests -q` verde.

## Self-Review (checklist do autor)
- **Achados cobertos:** drift de input → Fase 3.1 (reconciliação); sem gold de código → Fase 3.2 (gold + harness). Ambos ANTES do cutover (3.3/3.4) — o cutover é gated pelo gold.
- **Sem placeholders nas fases prontas:** 3.1/3.2/3.3 têm tasks/passos/files; 3.2.2 USER-SIDE explícito (bloqueia até rótulo). 3.4 é milestone POR DESIGN (delete exato contra rebuild-diff em runtime; plano bite-sized ao chegar) — não fabricar a lista de linhas a deletar agora.
- **Dependências:** 3.1 → 3.2 (gold sobre dados reconciliados) → 3.3 (A/B gated pelo gold) → 3.4 (cutover). Humano no loop em 3.2.2.
- **Risco/altitude:** flag default OFF até o gate; funil intacto até 3.4; rota SARC e P3.4 nunca tocados.
