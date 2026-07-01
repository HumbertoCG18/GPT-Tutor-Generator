# Handoff — Cronograma sessão-átomo: Specs A+B revisadas, degrau 1 shipado, degrau 2 adiado, degrau 3a planejado

date: 2026-06-19
branch: `feat/reconciliar-unit-bloco`
HEAD: `a79f5de`
estado: **2 specs revisadas (workflow adversarial) + degrau 1 IMPLEMENTADO e revisado (merge-ready) + degrau 2 ADIADO (revertido, com aprendizado) + degrau 3a (alavanca 0) PLANEJADO, não executado.** Suíte de tocados verde; golden PDF 5/5 cw0 (intacto); flag `use_concept_resolver` OFF (produção = funil).

## Como retomar (ler nesta ordem, NÃO reler a conversa antiga)
1. `.mex/ROUTER.md` + `.mex/AGENTS.md` (bootstrap + não-negociáveis). **Prefixar TODA resposta com `[Humberto]`**; debate-partner (questionar, não concordar cego); commits terminam com `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; **caveman mode** ativo (terse; código/commits/spec normais).
2. **Este handoff.**
3. **Ledger durável (fonte de verdade do progresso):** `.git/sdd/progress.md` — tem o detalhe task-a-task de TODAS as fases (S0/S0b/resolver Fase 1-3 + degraus 1-3a desta sessão). Após qualquer compactação, confie no ledger + `git log`, não na memória.
4. **Specs (revisadas hoje):** `docs/superpowers/specs/2026-06-19-cronograma-sessao-atomo-design.md` (A, consumidor) + `docs/superpowers/specs/2026-06-19-ingestao-stash-download-automap-design.md` (B, produtor).
5. **Plano do próximo passo:** `docs/superpowers/plans/2026-06-19-degrau3a-alavanca0-lesson-signal.md`.
6. Design do resolver/signal-registry (degrau 3 se apoia nele): `docs/superpowers/specs/2026-06-17-signal-registry-design.md` + handoff `docs/reports/2026-06-17-handoff-signal-registry.md`.

## A tese (Specs A+B, pós-revisão adversarial)
- **Chave de join da atribuição = DATA, por membership** (`session.date ∈ card.dates`, conjunto discreto; fallback intervalo `min..max` só explícito e logado). Slug = projeção de display, NUNCA chave. (Pivô do slug→data: o slug não existe por sessão; usá-lo reintroduziria o difuso.)
- **Resolução 2-níveis:** label do arquivo (`moodle_label`) → tópico/sessão → datas; senão herda `card.dates`. Precisão grão-sessão para arquivos com label.
- **Atribuição automática + revisão por `rebuild_diff`** (sem confirmar card-a-card). Fila de exceção só pro que deveria ter data e não tem sinal.
- **Ingestão = 3 trilhas:** material datado→cronograma; bibliografia/links (url/github-repo)→bloco de referências (não o dia-a-dia, não a fila); fila só do signalless. No MF: 14/17 `source_section` vazio têm `moodle_label`→auto; 3/17 são links→referências. "Espalhamento" era classificação, não atribuição.
- **Correções factuais:** módulo M365 (`m365.py`) JÁ existe (device-code read-only); `unit_index` e `content_taxonomy` partilham `normalize_unit_slug` (não são 2 autoridades — pré-req é normalização, não re-arquitetura); v3-em-disco já tem `sessions[]`.
- **Futuro (pós A+B, fora de escopo):** tutor consumir bibliografia de forma otimizada; garantir captura de todos os links no import.

## Roadmap (degraus) e estado
`1 render+normalização (FEITO) → 2 over-merge temporal (ADIADO→funde no 3) → 3 atribuição = signal-registry (EM CURSO) → 4 ingestão Spec B → 5 inversão sessão-átomo`.
**Cross-degrau (lembrete do usuário):** ao fim de TODOS os degraus, **reprocessar os repos** pra aplicar a arquitetura nova.

### Degrau 1 — FEITO, merge-ready (commits `cbd657e`, `e07c55c`, `2a70a53`)
- **Fix normalização:** `lookup_card_blocks`/`lookup_card_assign_due` (`card_block.py`) casam a chave do card por `norm_ascii_lower` (caixa/acento), via `_normalized_card_map`. Chaves do mapa intactas.
- **Render dia-a-dia:** `cronograma_detalhado_md` (`repo.py`) ganhou `### Sessões` por bloco (data+dia-semana+label+⏱ prova), lendo `blocks[].sessions[]` do v3. Não-regressivo (listagem de código + 2 testes existentes intactos). SEM material por dia (isso é degrau 3/5).
- Review final (opus): 0 Critical/Important. Minor deferido: `_normalized_card_map` reconstrói por chamada (negligível, 6-9 cards/curso; fix violaria a constraint do brief).

### Degrau 2 — ADIADO (guard `f912116` REVERTIDO em `a2acc22`)
- Tentou cap de span temporal (`MAX_THEMATIC_BLOCK_SPAN_DAYS=21`) em `_rows_belong_to_same_thematic_block`. Gate: golden MF 5/5 PASS, mas **IA +17 blocos**. Causa: **`block_id` é POSICIONAL** (`bloco-{NN}`, `index.py:2066`) → split renumera os seguintes em cascata e **desalinha o `.card_block_map.json`** (referencia ids posicionais) + `computed_block_id` persistidos.
- **Decisão:** over-merge migra pro **degrau 3** (agrupamento por slug + join por data → id posicional deixa de ser carga-crítica → split deixa de quebrar card_block_map). Degrau 1 já mostra os dias, então a dor visível já estava resolvida. Aprendizado travado: tratar estabilidade de block_id ANTES de mudar fronteiras.

### Degrau 3 — atribuição = signal-registry (EM CURSO)
**Achado central:** degrau 3 (atribuição por data) ≡ a extensão **signal-registry** do `concept_resolver` (fusor já existente, wired atrás de `use_concept_resolver` OFF). Construir caminho paralelo em `content_taxonomy` duplicaria o fusor. Decisão do usuário: **integrar no resolver.**
- **Alavanca 2** (source_section) e **Alavanca 1** (moodle_label) JÁ estão no fusor (`concept_resolver.py:275` section_vec, `:267` moodle_label_text).
- **Alavanca 0** (lessons[].text data→tópico) é a **única aberta** → **PLANEJADA** (`a79f5de`). `lessons_index`/`load_lessons_index` capturados mas dormentes (`resolver_apply.py:27`, não chamado).
  - O termo lesson foi **tentado e REVERTIDO** (casava o tópico da aula contra os `concepts` ruidosos do Gemini → gold 11→10). O plano re-introduz casando **SÓ o sinal LIMPO** (`moodle_label`+título, agora ativo), capado (`W_LESSON*min(overlap,cap)`), atrás da flag. **Task 2 (eval-gate) é a árbitra empírica:** se regredir com qualquer peso, a pista NÃO entra.

## Próximo passo (sessão fresca)
Executar `docs/superpowers/plans/2026-06-19-degrau3a-alavanca0-lesson-signal.md` via **subagent-driven**:
1. Task 1: `score_lesson_match` capado + parâmetro `lessons_index` no resolver + wire em `apply_concept_resolver`. TDD (6 testes no plano).
2. Review (spec + qualidade).
3. Task 2: eval-gate decisivo (golden 5/5, gold de código resolver≥funil, `rebuild_diff`) + calibração de `W_LESSON`. Se BLOCKED, a alavanca 0 não entra — reavaliar.
4. Depois: alavanca 3/posting_date; então degrau 3c (thematic-by-slug, mata o over-merge agora com join por data); degrau 4 (Spec B); degrau 5 (inversão); reprocess final.

## Dependências (user-side)
- **Gold cross-curso:** medir IA/SO/ES2/TCC precisa de `tests/fixtures/eval/ground_truth_<curso>.csv` rotulados (pendente). **MF já mede** (`eval_assignments` 5/5 + `eval_code_block_gold`). Rotular: `gold_by_card` → confirmar `true_block_id` → `expand_card_gold` → `eval_ground_truth`.
- **Re-sync por fonte (Task 4 do S0b, deferida):** reprocessar TCC/IA/SO (Moodle) + MF/ES2 (M365) pra limpar label/seção. = parte da "Alavanca 2 = só backfill" (código já existe). Destrava o gold dos 4 + é o "reprocess" cross-degrau.

## Eval-gates / comandos
- Suíte: `python -m pytest tests -q`.
- Golden PDF: `python scripts/eval_assignments.py` (5/5, cw0 — invariante).
- Gold de código: `python scripts/eval_code_block_gold.py` (resolver≥funil; baseline funil 7/17, resolver 11/17 cw1, subset alta resolver 9/13).
- Harness resolver: `python scripts/compare_resolver.py`.
- Rebuild-diff 5 cursos: `python scripts/rebuild_diff.py` (drift pré-existente baseline ES2 7/IA 20/SO 13/MF 1/TCC 0 = dívida, não regressão).

## Gotchas
- **Ledger `.git/sdd/progress.md`** = progresso durável; tarefas marcadas complete NÃO re-executar.
- Hook `code-review-graph` PostCommit cospe traceback cp1252 no commit — **inofensivo, commit passa**.
- Console Windows cp1252: imprimir UTF-8 cru quebra; `??` na saída é display, não corrupção.
- Flag `use_concept_resolver` OFF = produção byte-idêntica (funil). Mudanças no resolver não afetam produção até cutover (Fase 3.4).
- block_id é posicional → qualquer mudança de fronteira de bloco renumera e desalinha card_block_map (lição do degrau 2). Só mexer em fronteiras quando o join não depender mais de block_id (degrau 3c/5).
- Token Moodle em `moddle/.env`; token M365 em `moddle/.m365_token.json` (gerenciado por `m365.py`).
- MCPs token-savior/code-review-graph NÃO disponíveis como tools nesta máquina (só hook) → usar Read/Grep direcionado.
