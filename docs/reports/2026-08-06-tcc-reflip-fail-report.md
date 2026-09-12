# TCC re-flip (tentativa 3) — FAIL honesto do critério decisivo + rollback verificado

data: 2026-08-06 · sessão varredura/rollout · autorização: user aprovou ordem
TCC→D-H→inspeção→ES2/IA nesta sessão. Sem commit em nenhum repo. Zero re-tuning (spec §12).

## Rito executado

1. **Pré-flight**: baseline `fase2_prova_TCC.py` PASS (pinos 5/5 · cobertura 83.3% · acc
   par-colapsada 84.2% · cw=0 · providers {topic:20, manual:8}); `audit_gold_freshness --course
   TCC` hard=0 (42 rows / 8 soft); unidades 4/4 no índice; backup COMPLETO pré-flip (manifest +
   `material_curation.json` + 9 sidecars gitignored de `course/`) — lição do rollback furado
   de 2026-08-04 aplicada.
2. **Flip**: `feature_flags = {use_anchor_engine: true, use_llm_voter: true}` via `SubjectStore`
   (mesmo caminho da GUI), round-trip 5/5 verificado.
3. **Reprocess**: `python scripts/reprocess_assignments.py <TCC-Tutor>` SEM `--flags` — linha
   `[profile] ... feature_flags={use_anchor_engine: True, use_llm_voter: True}` no stdout
   (T18 confirmado em produção: armadilha `--flags` morta). `bloco 27/27 -> 27/27`, exit 0.

## Gates estruturais (a/c/d PASS, b = exceção explicada)

- (a) pinos 2/2 (`plano-de-ensino`, `3d-matching`) preservados, zero temporal sujo.
- (c) temporal 19/27 · providers {llm:16, manual:1, topic:2} · bands {media:16, alta:3} ·
  methods {llm:16, janela-1:1, disamb:2} · fila humana 0 — distribuição IDÊNTICA à referência
  do round de 2026-08-04. Zero out-of-scope.
- (d) votos 16→16, 0 chamadas API, 0 chaves alteradas (cache 100%).
- (b) 1 drift: `cubic-3-edge-coloring` bloco-26→bloco-22, conf honesta 0.2604 `scorer_only`,
  temporal None — **materialização esperada do fix 2b** (Plano B Task 4 mediu exatamente esse
  movimento; manifest em disco era pré-fix). `3dm` já estava em bloco-22; `integer`/`programacao`
  ESTÁVEIS em bloco-13 — a instabilidade antiga (flip a cada reprocess) NÃO reproduziu: fix 2b
  estabilizou o funil-base. `computed_block_id` diff = só o mesmo cubic (mesma causa).

## Critério decisivo — FALHOU (2 de 2)

- `fase2_prova_TCC.py` pós ≠ baseline: acc par-colapsada **84.2% → 78.9%** (topic 16/20 → 14/20);
  janela P4 do card "Semana 10 - Revisão para P1 e Prova P1" GANHOU bloco-13; cw manteve 0.
- `audit_gold_freshness` pós: **hard=1** (era 0) — `aula-14-problema-da-correspondencia-de-post`
  (true=bloco-13) caiu em ADMIN_TRUE porque **bloco-13 virou `kind=assessment`** ("1 dia ·
  24/04/2026") no índice regenerado. Unidades seguiram 4/4 (guard quieto, correto).

## Causa (evidência direta, investigação pendente)

O `.timeline_index.json` que `reprocess_assignments` regenera DIVERGE do índice produzido pelo
rebuild cirúrgico (`rebuild_timeline.rebuild_course`) que vivia no repo desde 2026-08-04:
bloco-13 muda de `kind` (class→assessment) entre os dois geradores, o que muda a janela do card
Semana-10 e derruba a acurácia topic. **3ª aparição da família dual-source** (1ª sonda-vs-
produção `retag`; 2ª assinatura de unidade; agora gerador-vs-gerador de índice). A régua TCC só
é estável sob o índice do rebuild — o reprocess não reproduz esse índice.

## Rollback (verificado)

`git checkout -- .` (tracked, incl. `manifest.json.bak` que é tracked neste snapshot) + restore
dos 9 sidecars gitignored do backup — **sha256 9/9 idêntico** + `material_curation.json`
restaurado + flags TCC `{}` (round-trip: MF/SO ON, IA legado, ES2 `{}` intocados). Re-verificação:
fase2 **byte-idêntica ao baseline** PASS, audit hard=0, árvore = só `?? material_curation.json`.
Estado final == estado pré-flip exato. HEAD `28bb29f` inalterado.

## Consequências

1. **TCC re-flip re-BLOQUEADO** — "destravado" era premissa falsa: os fixes do Plano B mataram
   o cw e a instabilidade do funil, mas NÃO a divergência entre geradores de índice.
2. **Pré-requisito novo e nomeado**: reconciliar `reprocess_assignments` × `rebuild_course`
   (kind de bloco determinístico entre caminhos) — entra na campanha de unificação de fontes,
   que sobe de prioridade (agora bloqueia TCC além de MF-u3).
3. Ordem aprovada segue válida no resto: fix D-H admin-kinds (independente) → inspeção ES2/IA
   com o user → flips ES2/IA (agora também condicionados à reconciliação de índice? decidir na
   campanha — ES2/IA nunca tiveram rebuild cirúrgico, podem não ter o conflito).

Evidência bruta (scratchpad da sessão, efêmero): `fase2_TCC_pre_reflip.txt`,
`fase2_TCC_pos_reflip.txt`, `fase2_TCC_pos_rollback.txt`, `audit_TCC_pos_reflip.txt`,
`reprocess_TCC_reflip.log`, `tcc-reflip-backup/` (sha256 verificado). Números-chave copiados
integralmente neste report.
