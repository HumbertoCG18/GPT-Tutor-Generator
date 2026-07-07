# Handoff — Revisão pré-plano FECHADA: partida do plano da FASE 0

date: 2026-07-03
branch: `feat/motor-atribuicao` (nada commitado nesta sessão — ver §2)
contexto: continua de `2026-07-01-handoff-spec-motor.md`. Spec consolidado + revisão final + sign-off do user.
status: spec FECHADO com sign-off. Próximo passo = **plano da fase 0** (`writing-plans`) → execução subagent-driven.

---

## 0. TL;DR pro chat novo

- **Spec fechado com sign-off do user (2026-07-03)**: `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md`.
  Resoluções §9: #9 e #11 APROVADAS; #10 e #12 APROVADAS CONDICIONAIS à fase 3 (go/no-go pós-recall da fase 1).
- **Revisão final spec×código×dívida executada** (agente read-only): 28 âncoras do §8 = **0 drift / 0 missing /
  0 divergente** — o plano parte delas sem re-verificação. Mapa de deleção do cutover com **5 conflitos
  resolvidos** (registrados no tracker). Veredito de ordem: **unificação de scorers (Tasks D/E) NÃO antecede a
  fase 0** — primitivas do Disambiguator já são a cópia canônica.
- **Tracker renomeado**: `docs/reports/pendencias.md` (sem data no nome, decisão do user; `git mv`, 7 referências
  atualizadas, zero link quebrado).
- **Nenhum bloqueio restante.** Falta só o plano da fase 0.

## 1. Disciplina (não negociável — persiste)

- **NÃO commita sem pedido explícito.** Working tree desta sessão está INTEIRO sem commit (ver §2).
- Mutação do vivo = ação do USER na GUI (reprocessar, deletar). Probes/scripts de CC = READ-ONLY nos repos-tutor.
- Lógica nova em `src/builder/routing/`, NUNCA `engine.py`. Gemini = `google-genai` lazy (`from google import genai`).
- ANCHOR-ONLY: motor escreve `temporal_block_id`; funil (`computed`) = piso intacto. Cascata `temporal>manual>computed`.
- Tracker `docs/reports/pendencias.md` (NOME NOVO) sempre atualizado; concluído vai pra `Feitos/`.
- PT-BR; UTF-8 shim em todo script novo (console cp1252).

## 2. Git — estado exato (as-of fim da sessão 2026-07-03)

Nada commitado. Working tree:

- **RM (staged pelo `git mv`)**: `docs/reports/2026-06-21-pendencias.md` → `docs/reports/pendencias.md`
  (+ edições de conteúdo da sessão: seção CODE-limpeza reescrita, DECISION sign-off, header).
- **?? (untracked)**: `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` (spec inteiro, nunca commitado)
  e este handoff.
- **M**: 5 handoffs (23/26/28/29-06 e 01-07) + `.mex/AGENTS.md` — só troca de path do tracker.
- **M**: `.claude/settings.local.json` — local, NÃO commitar.

Sugestão de separação de commits (user decide): (1) rename tracker + refs; (2) conteúdo tracker + spec + handoff.

## 3. O que esta sessão decidiu (sign-off + escopo)

1. **§9 do spec**: #9 TCC topic-bridge ✓; #11 aceite duplo contenção+cobertura ✓; #10 cache
   `material_curation.json` (md5/pair_key) e #12 voto-aceito-cego = **condicionais à fase 3**. LLM é opcional:
   go/no-go SÓ depois do recall medido do gate D4 (fase 1). Sem LLM, flagged = fila humana no Dashboard
   (MF: 18 casos; voto resolveria ~1/3 — saldo real nas regras finais = **+4**, não +5).
2. **Run dedicada de remoção de mortos** (separada do plano do motor, qualquer hora). Primeiro alvo provado:
   `_derive_unit_from_topic_match` (index.py:2080; só re-export engine.py:241/2443 + testes). Sem eval.
3. **Escopo de ciclo**: reorg física de `scripts/` (43 arquivos) só PÓS-motor; modularização de
   `src/ui/dialogs.py` (4.998 linhas) e sentença dos HTMLs (02–18/06, todos pré-motor) FORA deste ciclo.
4. **Ambiguidade nova → §12 do spec**: MARCO 1 converteu `plano.pdf` SEM janela, mas regra "voto bounded à
   janela" proíbe — definir na fase 3 (sem-janela nunca vota OU janela=timeline p/ não-bibliografia).

## 4. O que a revisão final entregou (entradas NOVAS pro plano; detalhes no tracker)

1. **Âncoras §8: 0 drift.** Única nota cosmética: `FileEntry:39` = decorator (classe :40). `get_gemini_client`
   em `src/builder/runtime/gemini_client.py:97`.
2. **Guard test de imports = requisito da FASE 0** (já no spec §7): pacote do motor PROIBIDO de importar
   condenados do cutover (`block_token_weights`, `score_entry_against_timeline_block`,
   `select_probable_period_for_entry`); whitelist: concept_resolver puro, card_block, thresholds,
   entry_signals, text/*.
3. **5 conflitos do cutover, resoluções travadas** (lista completa no tracker, seção CODE):
   cronograma_health decide-se na FASE 4 (portar ou aposentar); `eval_assignments.py`/`retag_manifest.py` =
   legado-não-usar, aposentar no MESMO commit da deleção; deleção da fase 5 por LISTA NOMEADA (sobrevivem
   `score_card_evidence_against_entry` + `_score_block_date_match` + `card_block.py` inteiro); Task B
   congelada até os testes de janela da fase 0; fallback keyword dividido (ramo unidade deletável; cadeia
   topic-labels VIVA, alimenta UI).
4. **Tasks D/E corrigidas no tracker**: "normalizadores ×4" JÁ resolvido no código (todos delegam ao canônico
   `text/normalize.py`); restam 3 scorers de unidade — trilho próprio, DEPOIS da fase 0 (grafo disjunto do motor).

## 5. Fontes de verdade (ler nesta ordem antes do plano)

1. `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` — spec FECHADO (contratos, tiers, fases com
   número, aceite §6, ambiguidades pro plano na §12).
2. `docs/reports/pendencias.md` — tracker vivo (baselines 5/5, conflitos do cutover, decisões da sessão).
3. `docs/reports/2026-06-28-motor-atribuicao-decisoes.md` — log D0–D13 (o spec NÃO re-decide; consulta de racional).
4. `docs/reports/2026-07-01-handoff-spec-motor.md` §4 — achados medidos (MARCO 0/1).
5. Régua: `scripts/eval_ground_truth.py` (pair_key) + golden MF `tests/fixtures/eval/metodos_formais_golden.json`.

## 6. Próximo passo (o que a nova sessão faz)

1. (Se o user pedir) commitar a papelada de §2.
2. **Invocar skill `writing-plans`** e escrever o plano da FASE 0 em `docs/superpowers/plans/`:
   contratos WindowProvider/Disambiguator/AnchorEngine + P1/P2 (card_block_map) + Disambiguator com len-norm
   (`sqrt(|sig|)`) e `sessions[].label` 1ª classe + guard test de imports. Tasks bite-sized TDD.
   READ-ONLY vs gold MF. Número de aceite: escopo-disamb MF ≥59.7%; contenção 100%; confiante-errado=0.
3. Execução subagent-driven (`subagent-driven-development`), review checkpoints.
4. NÃO re-rodar MARCO 0/1 (provas cacheadas). NÃO re-verificar âncoras §8 (0 drift as-of hoje).
5. Run de mortos: paralela/quando o user pedir — NÃO entra no plano da fase 0.

## 7. Comando de partida da nova sessão

> Leia `docs/reports/2026-07-03-handoff-plano-fase0.md` e o spec
> `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` (inteiro). Branch `feat/motor-atribuicao`.
> Invoque `writing-plans` e escreva o plano da FASE 0 em `docs/superpowers/plans/`.
