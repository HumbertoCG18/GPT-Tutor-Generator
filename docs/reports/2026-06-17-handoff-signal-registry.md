# Handoff — Resolver Fase 3 concluída + direção signal-registry

date: 2026-06-17 (fim de sessão longa)
branch: `feat/reconciliar-unit-bloco`
estado: working tree com gold + docs commitados; suíte **1438 verde**; golden PDF **5/5, confiante-errado 0**; resolver de bloco **wired ATRÁS DE FLAG `use_concept_resolver` (default OFF — produção = funil, intacta)**.

## Atualização — sessão 2 (2026-06-17): alavanca 2 fechada, alavanca 0 captação, pivot p/ alavanca 1

Commits (branch `feat/reconciliar-unit-bloco`):
- `dab6781` test(gold): baseline-lock real (11/17, cw≤1) — `eval_code_block_gold.py` virou gate (`check_baseline`, exit 1 em regressão; antes só sintético).
- `d9aaef3` docs: plano alavanca 0 (`docs/superpowers/plans/2026-06-17-alavanca0-lessons-index-plan.md`) + backlog de artefatos (seção abaixo).
- `60c4eb1` feat: captação do resumo-da-semana — `build_lesson_topic_index` (moodle_labels) → `course/.lessons_index.json` no import + `load_lessons_index` (resolver_apply). CONSUMO no fusor REVERTIDO (abaixo).
- `013da0b` fix: captação robusta a resumo **year-less dentro do card** (formato A year-less + parens-opcional + semana-dentro; `_LESSON_SHORT` paren-opcional). Captava só 2/5 layouts → 5/5. MF inalterado (full-year).

**ALAVANCA 2 (source_section):** JÁ estava implementada (consumida em `concept_resolver:259/81` + backfill nos 5 manifests). Não era greenfield. Baseline travado em 11/17.

**ALAVANCA 0 (lessons[].text):** captação FEITA + robusta; **CONSUMO (lesson_term) REVERTIDO** — regrediu gold 11→10. Root cause (probe): lessons alinham PERFEITO ao bloco por data, mas casar contra os `concepts` do Gemini (ruidosos: hoare=[dafny,hoare,indutivos,terminacao]; listas=[inducao,isabelle] sem "listas"→flipa 05→06; exemplos-zip=[hoare,terminacao] errado p/ NuSMV) amplifica concept errado. **Alavancas 0 e 1 SÃO ACOPLADAS:** a lesson precisa da IDENTIDADE LIMPA do material (moodle_label), não dos concepts. `load_lessons_index` fica como infra pronta.

**PRÓXIMO — ALAVANCA 1 (moodle_label):** capturar `mod.get("name")` (`moodle.py:130`, o `<span instancename>`, ex. "Exemplos (Lógica de Floyd-Hoare)") num campo NOVO `moodle_label` (NUNCA sobrescrever `title`) ANTES do redirect SharePoint que o destrói. Canal `moodle_label_text` em `collect_entry_unit_signals`. Reativar `lesson_term` casando `moodle_label × lesson`. Medir no MF.

**BACKLOG NOVO:** `rebuild_diff` mostra 4/5 `.timeline_index.json` gravados STALE vs código atual (ES2 7, IA 20, SO 13 blocos divergem unit/kind) — drift PRÉ-EXISTENTE, NÃO da sessão 2 (verificado por stash). Reprocessar/regravar índices num momento controlado.

**Artefato:** `…\Metodos-Formais-Tutor\course\.lessons_index.json` (28 datas, montado do resumo REAL do usuário p/ medir a alavanca 1; um re-import real regenera).

## Como retomar (nova sessão — ler nesta ordem, NÃO reler a conversa antiga)
1. `.mex/ROUTER.md` + `.mex/AGENTS.md` (bootstrap + não-negociáveis). `.mex/context/institutional.md` (PUCRS/SARC/Moodle/Plano — atualizado com labels/resumo-da-semana).
2. **Este handoff.**
3. **Spec da direção nova:** `docs/superpowers/specs/2026-06-17-signal-registry-design.md` (signal-registry como EXTENSÃO do fusor; alavancas 0-3).
4. Plano Fase 3 (cutover do bloco): `docs/superpowers/plans/2026-06-17-resolver-fase3-cutover-plan.md`.
5. Design do resolver: `docs/superpowers/specs/2026-06-17-resolver-atribuicao-conceito-design.md`.
6. Overview vivo: `docs/Overview-Sistema.html` (§5 agora lista os sinais descartados).
7. Ledger SDD (local, `.git/sdd/progress.md` — não commitado): marca FEITO; briefs/reports em `.git/sdd/task-*.md`.
8. Prefixar TODA resposta com `[Humberto]` (CLAUDE.md). Commits terminam com `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

## Feito nesta sessão (Fase 3 quase completa)
- **3.1 Reconciliar manifest↔code_curation:** MEDIDO, **drift=0** nos 5 cursos (census weak-changed=0; manifest mais novo que code_curation). Reprocess era NO-OP. O `generated_at:2026-03-23` da raiz do manifest é red herring. Sem mutação de repo.
- **3.2.1 `make_code_gold_template.py`** (`1dc61e8..9126989`, review limpo): gerador read-only do template de rótulo (entries code/zip, funil/gemini/resolver lado a lado, `true_block_id` vazio).
- **3.2.2 gold + harness** (`b65e99c`, review limpo): `scripts/eval_code_block_gold.py` (funil vs resolver vs gold, acurácia + confiante-errado, subset por confiança) + `tests/test_eval_code_block_gold.py` (5 sintéticos). Gold em `tests/fixtures/eval/code_block_gold.json`.
- **3.2.2 gold ROTULADO por proveniência + moodle_labels do usuário** (commit desta sessão): 17 entries do MF rotuladas via pasta-card (`source_path`) + extensão real dos zips (.thy=Isabelle/u1, .dfy=Dafny/u2, .smv=NuSMV/u3) + o `<span instancename>` que o usuário forneceu (15/17 com label). Correção via label: hoare 11→10 ("Floyd-Hoare"=bloco-10). PROVISÓRIO nos 4 `media` sem label forte.
- **3.3.1 wire rota (b) atrás de flag** (`b65e99c..1d742b9`, review OPUS limpo, zero Critical/Important): novo `src/builder/routing/resolver_apply.py` (`assemble_resolver_inputs` + `apply_concept_resolver` BLOCK-only) + wire gated em `pedagogical_regeneration.py:359` (flag default OFF; import function-local → módulo nem carrega com OFF; `attach_block_summary_fields` incondicional) + refactor DRY de `compare_resolver` (output inalterado) + `tests/test_resolver_wiring.py` (5). Suíte 1438, golden 5/5, harness 28/9, gold 6vs12 — todos inalterados (flag OFF = byte-idêntico).
- **Investigação de arquitetura whole-system** (3 Explore agents + Overview): mapa de reúso/legado/golden. Spec do signal-registry + update do Overview §5 (sinais descartados).

## PLACAR do gold (label-grounded, 17 code entries MF)
| | acurácia | confiante-errado |
|---|---|---|
| funil | 7/17 (41%) | 5 |
| Gemini | 10/17 (59%) | — |
| **resolver** | **11/17 (64%)** | **1** (só hoare) |
| subset alta (13) | funil 7/13 | **resolver 9/13** |

Gate (resolver_acc ≥ funil E cw ≤ funil): **PASSA**. Resolver ganha até no subset alta-confiança (sólido). Único cw do resolver = `hoare` (dá 11, gold 10; blocos Hoare adjacentes).
Os 6 erros do resolver: invariantes(04→11), tiposindutivos(04→13), exemplos-zip(11→16 NuSMV), hoare(11→10), intro(05→04), provas(04→06). **3 deles (invariantes/tiposindutivos/exemplos-zip) somem com o `moodle_label`** → resolver iria a ~14/17.

## DOIS caminhos a seguir (decisão do usuário)

### Caminho A — Fechar a Fase 3 (cutover do bloco)
1. **Gold sign-off (USER):** restam 3 `media` provisórios (`intro`→04, `tiposindutivos`→12ou13, `t1`→04) + a miss `invariantes`. (`terminacao`=bloco-12 RESOLVIDO/alta: gold é material→bloco, o .dfy rodou na sessão Dafny; resumo-da-semana põe o tópico em 06/05/bloco-11 mas Dafny só entra 11/05.) `tests/fixtures/eval/code_block_gold.json` tem `evidence`+`confidence`+`moodle_label` por entry.
2. **Fixar baseline** no gold (`baseline.resolver_block_accuracy`) + guard de regressão real (hoje o guard é sintético).
3. **A/B no repo real:** reprocessar MF com `use_concept_resolver=True` nas options → census. MUTA o repo (com `.bak`) → decisão do usuário.
4. **3.4 cutover:** flip flag default ON + **DELETAR** (não refatorar) o funil de bloco legado: `score_entry_against_timeline_block` S2 (`block_token_weights`), S4 (`TOOL_BOOST/PENALTY/TOOL_TOKENS`), `select_probable_period_for_entry`, `_best_instructional_block_fallback`, 2 rotas card→bloco. Gate: golden 5/5 + gold + rebuild_diff 5 cursos.

### Caminho B — Signal-registry (precisão geral, maior ROI a longo prazo)
Spec: `docs/superpowers/specs/2026-06-17-signal-registry-design.md`. Alavancas como instâncias do registry, eval-gated cross-curso, cada uma = extrator + chave em `collect_entry_unit_signals` + termo no fusor `concept_resolver`:
- **Alavanca 2** (source_section dos zips) — menor risco, `_section_from_source_path` já existe (commit 8d8915a), só backfill p/ repos antigos.
- **Alavanca 0** (`lessons[].text` resumo-da-semana → índice data→tópico) — MAIOR ROI, parser pronto (`moodle_labels.py` formatos A-E), `derive_card_block_map` dropa o `text` hoje.
- **Alavanca 1** (`moodle_label` = `mod.get("name")`, `moodle.py:130`) — campo NOVO (NUNCA sobrescrever `title`) + canal `moodle_label_text`. Conserta ~4 erros.
- **Alavanca 3 / posting_date** — seleção por sessão (`rows`/`sessions` já têm data+Descrição) + Moodle `timemodified` (já no payload, dropado em `iter_section_files`); Graph/Drive só fallback OneDrive-only.

## Constatação central (anti-refatoração-em-círculo)
O fusor já existe (`concept_resolver`) e já degrada honestamente. O signal-registry é **EXTENSÃO** (adicionar extratores+pesos), não reescrita. O funil legado é **DELETADO** na 3.4, não refatorado. Coexistência 2-caminhos-atrás-de-flag = sem big-bang. NÃO tocar GOLDEN (`assign_units_positional`, `_build_timeline_index`, review rule, flag-OFF).

## Backlog pós-refatoração — auditoria/unificação de artefatos (registrado 2026-06-17)
Depois de fechar o signal-registry (alavancas) E o cutover 3.4, fazer UMA rodada de
auditoria dos **artefatos de dados em disco**: provavelmente há artefatos mortos,
redundantes ou duplicados que podem ser fundidos num só. NÃO executar antes do cutover
— o funil legado ainda lê parte deles.
- Candidatos observados (`course/` + raiz, por curso): `manifest.json`, `code_curation.json`,
  `.timeline_index.json`, `.timeline_curation.json`, `.card_block_map.json`, `.content_taxonomy.json`,
  `.semantic_profile.generated.json`, `.tag_profile.json`, `.tag_catalog.json`, `.assessment_context.json`,
  `references_curation.json` + (novo) `.lessons_index.json`. Suspeitas a confirmar: `tag_profile`×`tag_catalog`;
  sobreposição de mapa data/bloco entre `card_block_map`×`lessons_index`×`timeline_index`; curations dispersas.
- Método: primeiro AUDITAR quem LÊ cada artefato (grep dos load points) → marcar morto/vivo/redundante;
  só então propor fusão. Correção na RAIZ (não por curso). Cada fusão = eval-gate (golden 5/5 + suíte +
  rebuild_diff 5 cursos) + doc-vivo atualizado.
- Distinto do FOLD de CÓDIGO já listado na spec (signal-registry §"Mapa de reúso"): aquilo é dedup de
  FUNÇÕES; este é dedup de ARTEFATOS de dados.

## Eval-gates / comandos
- Suíte: `python -m pytest tests -q` (1438).
- Golden PDF: `python scripts/eval_assignments.py` (5/5, confiante-errado 0).
- Gold de código: `python scripts/eval_code_block_gold.py "<repo>"` (funil vs resolver vs gold).
- Census código→bloco: `python scripts/eval_code_block_census.py "<repo>"`.
- Harness resolver: `python scripts/compare_resolver.py "<repo>"` (28 mudados / 9 conflitos no MF).
- Template gold: `python scripts/make_code_gold_template.py "<repo>" out.csv`.
- Rebuild-diff 5 cursos: `python scripts/rebuild_diff.py`.
- 5 cursos sob `C:\Users\Humberto\Documents\GitHub\*-Tutor`.

## Gotchas
- Hook `code-review-graph` PostCommit cospe traceback **cp1252** no Windows — inofensivo, commit passa. `LF will be replaced by CRLF` idem.
- `claude-mem` PreToolUse pode bloquear Read se o worker estiver down — workaround via PowerShell.
- Flag `use_concept_resolver` default OFF: produção = funil. Wire só roda com flag ON; com OFF o módulo `resolver_apply` nem é importado.
- Gold `media` PROVISÓRIO (3 restantes: intro/tiposindutivos/t1): viés possível pró-resolver nos `.thy` sem label. Os `.dfy`/`.smv` (proveniência+extensão+label) são sólidos. Subset alta (14): resolver 10/14 vs funil 7/14.
- `classes-parte2` tem label mas NÃO está nas 17 entries → possível material não importado no MF (checar).
- Artefato `docs/reports/code_gold_template_MF.csv` é gerado (template em branco), NÃO commitar.

## Regras do usuário (manter)
- Correções gerais na raiz, nunca fix por arquivo/cadeira. Mudança que altera atribuição = eval-gate (golden + suíte + rebuild_diff 5 cursos; census/gold user-side).
- Doc vivo `docs/Overview-Sistema.html` sempre atualizado (AGENTS non-negotiable).
- Reprocessar cursos com app reiniciado (ou `reprocess_assignments.py`) antes de medir census.
