# Handoff — Resolver de conceito (P2): retomar na Fase 3

date: 2026-06-17 (fim de sessão longa)
branch: `feat/reconciliar-unit-bloco`
estado: **working tree limpo**; suíte **1420 verde**; golden de bloco **5/5, confiante-errado 0**; resolver de conceito construído **ATRÁS DE FLAG (não-wired — produção intacta)**.

## Como retomar (nova sessão — ler nesta ordem, NÃO reler a conversa antiga)
1. `.mex/ROUTER.md` + `.mex/AGENTS.md` (bootstrap + não-negociáveis). `.mex/context/institutional.md` (PUCRS/SARC/Moodle/Plano).
2. **Este handoff.**
3. Spec do resolver: `docs/superpowers/specs/2026-06-17-resolver-atribuicao-conceito-design.md`.
4. **Plano da Fase 3 (o que executar):** `docs/superpowers/plans/2026-06-17-resolver-fase3-cutover-plan.md`.
5. Baseline da Fase 2: `docs/reports/2026-06-17-resolver-baseline.md`.
6. Ledger subagent-driven (local, em `.git/`, não commitado): `.git/sdd/progress.md` — marca o que está FEITO; briefs/reports das tasks em `.git/sdd/task-*.md`.
7. Prefixar TODA resposta com `[Humberto]` (CLAUDE.md). Commits terminam com `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

## Feito nesta sessão (15 commits, da base `b98ae29`)
- **P3.4** `trabalho`→DELIVERABLE **unit-aware** (`7016222` fix, `6108b5d` docs). Token nu saiu de `KIND_KEYWORDS[DELIVERABLE]` → regra gated 3c em `classify_block` (`_has_unit_evidence`). Bundle G2/PS no `_STRONG_EXAM_RE`. Descoberta: a "FP de trabalho" não existia — eram apresentações de TP (DELIVERABLE correto); 2 merged (apresentação+prova) viram ASSESSMENT.
- **Censo subunit** (`7eb4c1a`): `scripts/eval_subunit_census.py` (gate P0.2). Achou **7 subunit fora da unidade** = divergência SARC×Plano (Hoare/correção/etc. agendados na u1, plano lista u2/u3). Registrado em institutional.md + spec.
- **Spec + plano P2** (`b36ef9a`, `84020b9`): resolver único em espaço de conceito.
- **Fase 1 — consolidação** (`a4947e6` guard, `173568a` normalize, `4c6d194` stopwords, `b12ced8` docs): base única `src/builder/text/normalize.py` (params `keep`/`em_dash_to_hyphen`/`fix_typos`) + fonte única `src/builder/text/stopwords.py`. **Não-comportamental** (guards byte-idênticos + 5 set-guards). Review final opus: equivalência por execução.
- **Fase 2 — resolver atrás de flag** (`742562a` 2.1, `02f3f42` 2.2, `9fc2acf`+`03fa9c2` 2.3, `2bffd0a` docs):
  - `src/builder/routing/concept_resolver.py`: `concept_token_weights`(scope-aware: ferramenta/formato → peso ~0 no escopo BLOCO, mantém no escopo UNIDADE → mata o viés Isabelle→bloco-06) + `concept_vector` + `resolve_material_assignment` (fusão `1.0*concept + 0.85*llm + date/seq/card`, tiers `manual>card>concept>posicional`, conflito flagado quando bloco-unit≠tópico-unit, `subunit_slug` sempre "" por ora, `relative_margin_confidence`).
  - `scripts/compare_resolver.py`: harness read-only funil×resolver.
  - oracle 18/18 (4 corrige: arvores→05/intro→04/listas→05/classes→15; 6 não-regride: colecoes→13, invariantes/terminacao→11, hoare→10, exercicios-conjuntos→13). **Não-wired.**
- **Plano Fase 3** (`f4ef85e`).

## PRÓXIMO PASSO: executar a Fase 3 (cutover do BLOCO) — gated
Plano detalhado em `docs/superpowers/plans/2026-06-17-resolver-fase3-cutover-plan.md`. Resumo do que falta:
- **3.1 Reconciliar `manifest`↔`code_curation`** (mata o DRIFT DE INPUT). O `computed_block_id` do funil tem linhagem stale (`generated_at` 03/2026) vs votos atuais do `code_curation` (16/06) → comparação confundida. Reprocessar (`python scripts/reprocess_assignments.py "<repo>"`) + diagnóstico. Concreto, sem humano.
- **3.2 Gold de código** (o eval só tem 5 PDFs; as ~12 entries de código/zip não têm rótulo). Scaffold do template (`make_code_gold_template.py`) → **USER rotula `true_block_id`** (HUMANO NO LOOP — trava aqui) → harness `eval_code_block_gold.py` (funil vs resolver vs gold).
- **3.3 Wire** do resolver atrás de flag `use_concept_resolver` (default OFF) em `content_taxonomy.py` (~:1180-1248). A/B no repo real. **Gate:** resolver ≥ funil no gold + golden PDF 5/5 + rebuild-diff.
- **3.4 Cutover** default ON + delete do legado (`score_entry_against_timeline_block`, S2 `block_token_weights`, S4 `TOOL_BOOST/PENALTY/TOOL_TOKENS`, `select_probable_period_for_entry`, `_best_instructional_block_fallback`, 2 rotas card→bloco).

Execução: subagent-driven (a sessão estava usando essa skill; ledger em `.git/sdd/progress.md`). Dá pra fazer 3.1 + scaffold 3.2.1 sozinho; 3.2.2 trava no rótulo do usuário.

## DEPOIS da Fase 3 (Fases 4-5, milestones — plano-mãe)
- **Fase 4:** cutover da UNIDADE + **fold do fallback keyword ~600 linhas** (`index.py:2205`) + deletar `_derive_unit_specs_from_repo` (divergência latente). Reconciliação bloco×plano resolve os 7 subunit-fora-da-unidade.
- **Fase 5:** limpeza (gate D1 `attach_block_summary_fields` substituído pelo sinal LLM fundido; normalizadores/predicados duplicados restantes).

## Eval-gates / comandos
- Suíte: `python -m pytest tests -q` (1420).
- Golden PDF: `python scripts/eval_assignments.py` (5/5, confiante-errado 0).
- Censo código→bloco: `python scripts/eval_code_block_census.py "<repo>"`.
- Censo subunit/bands: `python scripts/eval_subunit_census.py "<repo>"`.
- Harness resolver: `python scripts/compare_resolver.py "<repo>"`.
- Reprocessar: `python scripts/reprocess_assignments.py "<repo>"` (ou app reiniciado).
- 5 cursos sob `C:\Users\Humberto\Documents\GitHub\*-Tutor` (MF reprocessado; outros podem faltar → skip).

## Gotchas
- Hook `code-review-graph` PostCommit cospe traceback **cp1252** no Windows — inofensivo, commit passa.
- `claude-mem`: o PreToolUse `file-context` pode **bloquear o tool Read** quando o worker está down (aconteceu nesta sessão). Se Read falhar com "worker unreachable", subir o worker do claude-mem ou desligar o hook; workaround = ler/editar via PowerShell.
- `LF will be replaced by CRLF` no commit — autocrlf, inofensivo.
- Minors abertos (logados no `.git/sdd/progress.md`, triagem no review final whole-branch): docstrings borderline; `FORMAT_TOKENS` resolvido na 2.2; `winner_breakdown.card` ordenado por fused; `NOREGRESS_TARGETS` do harness usa expectativa stale (re-derivar na 3.1).
- Resolver está **NÃO-WIRED**: nada em produção o chama (só testes + `compare_resolver.py`). Golden/suíte verdes garantem isso.

## Regras do usuário (manter)
- Correções gerais na raiz, nunca fix específico por arquivo/cadeira. Mudança que altera atribuição = eval-gate (golden + suíte; censo é user-side).
- Doc vivo `docs/Overview-Sistema.html` sempre atualizado (AGENTS non-negotiable).
- Pendência USER-SIDE recorrente: reprocessar os cursos com app reiniciado antes de medir censos.
