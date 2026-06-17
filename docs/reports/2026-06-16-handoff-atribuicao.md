# Handoff — sessão de correções do sistema de atribuição

date: 2026-06-16
branch: `feat/reconciliar-unit-bloco`
estado: **working tree limpo**; suíte **1366 verde**; golden de bloco (`scripts/eval_assignments.py`) **5/5, confiante-errado 0**.

## Como retomar (nova sessão)
1. Ler `.mex/ROUTER.md` + `.mex/AGENTS.md` (bootstrap + não-negociáveis do projeto).
2. Ler este handoff + `docs/Overview-Sistema.html` (aba 6 **Pendências** / aba 8 **Concluído** — doc vivo) + `docs/reports/2026-06-11-plano-mestre-atribuicao.md` (seção "Auditoria completa wave 1+2").
3. Prefixar TODA resposta com `[Humberto]` (CLAUDE.md, não-negociável). Caveman mode pode estar ativo. Commits terminam com `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
4. `claude-mem` worker pode estar offline (hook ruidoso) — ambiental, ignorar.

## Contexto
Auditoria read-only do sistema de atribuição (arquivo→bloco→unidade/subunidade) achou 21 itens (P0-P3) + 2 decisões de arquitetura (D1/D2). Spec: `docs/superpowers/specs/2026-06-16-correcoes-atribuicao-wave-1-2-design.md`. Planos: `docs/superpowers/plans/2026-06-16-*`. Regra do usuário: **correções gerais na raiz, nunca fix específico por arquivo**.

## Feito nesta sessão (commits)
- **P0**: subunit fonte-única (`e1e2c62` campo FileEntry, `093adcd` FILE_MAP lê tag gated), winning_unit_slug (`4f9a277`, `115d912`), dedup id batch (`45b4841`, `a42316c`).
- **fix c v2** (dedup por EXTENSÃO, cascata ext→pasta→contador) + **P0.5** (aba códigos inferred_title): `1773bbb`.
- **Migração de ids legados**: `scripts/migrate_collided_ids.py` (`35a72b7`) — aplicado no MF (introducao-zip, exemplos-zip, t1-2026-1-thy).
- **UI**: cronograma mostra nome do arquivo (`c3f8997`); aba códigos checkbox id↔arquivo (`2bb3c4b`).
- **unprocess** limpa filhos de zip (`3bf81ea`).
- **idea 1** unit relative_margin (`26615f1`); **D1** código→bloco band-gated (`3e4f18e`, `0774f6f`, `f0c2b27`, `9a85ac3`); **idea 3** source_section por pasta no import (`8d8915a`).
- **P1 Lote A** (mortos inequívocos): BLOCO_TAG + process_reference_entry (`f45e466`).
- Docs/Overview: `3cdbc5d`, `f1dfbc9`, `62f7389`, `0db3047`, `bd71cd3`.

## PRÓXIMO PASSO: D2, depois resto do Lote B (P1 eval-gated/decisão)
Ordem recomendada:
1. **D2 — `administrative_only`**: usar o predicado real `_timeline_block_is_administrative_only` (`timeline/index.py:821`, funciona) em `content_taxonomy.py:1147` (o vazamento REAL — esse site lê o índice **runtime**, que inclui blocos admin sem a chave). Os outros 3 sites (`file_map.py:539`, `cronograma_health.py:124`, `moodle_labels.py:131`) leem o **serializado** (admin já removido no `_serialize`) = dead filters inócuos → deletar. **EVAL-GATE** (candidate set encolhe → pode mudar/melhorar atribuição).
2. **auto_suggested_unit** (`timeline/conflicts.py:21-44`): investigar reachability REAL do ramo topic-derive (bloco serializado SEM `auto_unit_slug` mas COM `topic_candidates` ocorre em prod?). Tem testes em `tests/test_curation_conflicts.py:29,196`. Morto→remover+testes; vivo→manter. (É conflict-detection/health, não atribuição → golden-safe de qualquer forma.)
3. **piso 0.72** (`file_map.py:~1356` `max(confidence,0.72)` vs cap `scorer_only=0.70` em `content_taxonomy.py:~1247`): **NÃO é no-op** — com piso a conf session-first vira flat 0.70; sem piso vira `min(real,0.70)` (cai pra <0.70). **DECISÃO**: remover o piso (conf honesta) vs subir o cap p/ 0.72. **EVAL-GATE** (muda band).
4. **fallback keyword ~600 linhas** (`timeline/index.py:2205` else + `_assign_timeline_block_to_unit:841`, `_vote_unit_from_topic_candidates:2026`, `_score_timeline_row_against_unit:1618`): só alcançável quando `assign_units_positional` (timeline/unit_matcher.py) retorna `[]`. Deletar + **guard test** provando que nunca retorna [] nos cursos do golden. **EVAL-GATE forte.**

Depois do P1: **P2** (duplicação — família de 6 scorers; 3× basename→source_section em stash_backfill/moodle/m365; 2 rotas card→bloco; predicados de kind index vs classifier; menores) e **P3** (ruído — auto_tags self-confirmation, llm_only 0.6, m365 vs moodle source_section, "trabalho"→DELIVERABLE, canal de data duplo, herança bidirecional soft-continuation, substring fontes fracas, pisos hardcoded). Todos eval-gated.

NÃO mexer (já verificado vivo): `_consolidate_assignment` / `consensus` B / `auto_concept` — o D1 não os matou; seguem alcançáveis.

## Eval-gates / validação
- Suíte: `python -m pytest tests -q`.
- Golden de bloco: `python scripts/eval_assignments.py` → 5/5, confiante-errado 0.
- Censo código→bloco (repo real): `python scripts/eval_code_block_census.py <repo>`.
- Censo subunit/bands: retag/reprocesso + comparar distribuição (manual).

## Pendência USER-SIDE (não-código)
**Reprocessar o MF** (`C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor`) com o **APP REINICIADO** → aplica P0 + idea1 + D1 + idea3 (subunit↛unit, FILE_MAP coerente, unit honesto, código→bloco band-gated, source_section por pasta). NÃO re-extrai nem mexe em id (já feitos via migração). Depois rodar o censo: `exemplos-zip` deve ir pra `bloco-12`; zips de "Verificação de Programas" recuperam o card (blocos 10-15). `extracted_files=0` dos zips só repopula com re-add (não-crítico; resumos Gemini em cache).

## Gotchas
- MCPs `token-savior`/`code-review-graph` podem estar desconectados → cair pro Grep/Read.
- Hook `code-review-graph` PostCommit imprime traceback cp1252 no Windows — inofensivo, commit funciona.
- `Overview-Sistema.html` é o doc vivo (AGENTS.md: manter atualizado quando arquitetura/pipeline/atribuição muda). Server: `python -m http.server 8753 --directory docs` → http://localhost:8753/Overview-Sistema.html.
