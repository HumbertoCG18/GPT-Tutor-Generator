# Handoff — sessão 2026-08-06/07: campanha índice FECHADA, 5/5 flag-ON; fila = campanha 2 (Unidades)

**Branch:** `feat/motor-atribuicao` · head `2f9a070`. Sucede
`docs/reports/2026-08-06-handoff-sessao-planob-fio.md`. Tracker
(`docs/reports/pendencias.md`, last_updated 2026-08-07) é a fonte de estado — este handoff só
ordena a fila e aponta os arquivos.

## §1 Estado

**Rollout: 5/5 cursos flag-ON em produção** (MF `c7b7498`+pinos `ddd9800`/`751955f` · SO
`11667b7` · ES2 `dc74c12` · IA `86f00d9` · **TCC `31f6025`+`91c1d2a`** — fechado nesta sessão,
tentativa 6). **Campanha 1/3 (gerador de índice único) FECHADA**: 9 tasks via SDD, review final
whole-branch zero Critical, spec/plano em `Feitos/`, entrada Concluído no tracker. Suite
**1881 passed / 4 skipped / 1 failed** (o 1 = golden IA stale pós-rollout, item [CODE] próprio).
Réguas vivas: fase2-TCC 84.2%/cw0 byte-idêntica · fase4 det 53/58 voter 58/58 (pós-pinos) ·
fase5 6/8 cw0 · MF eval 64/66=97.0% cw0 · rebuild_diff 0/5 · audit hard=0 5/5.
Evals pós-rollout (régua oficial): IA 95.5 · MF 97.0 · ES2 78.6 · SO 57.9.

## §2 O que esta sessão fechou (além da campanha)

Varredura do tracker com dados reais (U+FFFD falsificado — era mojibake de console; 4 itens
stale mortos) · dieta MEX (ROUTER 424→76, contratos de dados reais em `institutional.md`,
regra de fixture com proveniência) · fix D-H admin-kinds `0f27fec` · dossiê + commits ES2/IA
(poda confirmada) · rollouts ES2/IA · 7 pinos MF (inclui regra institucional nova: **revisão =
última aula antes da prova**, registrada no MEX com caso provado) · TCC re-flip: 3 tentativas
nesta sessão (4ª FAIL janela P4 → guard C6 · 5ª FAIL scorer → ruling aceitar+pino · 6ª GREEN).

## §3 A lição técnica da campanha (para as próximas)

A colisão "prova = demonstração (plano de ensino) vs exame" apareceu em **3 camadas**:
(1) kind do bloco (keyword do classifier) — morta pelo guard C1 `0bc4265`;
(2) membership de janela P4 (token de rótulo rico) — morta pelo guard C6 `b4c9672`;
(3) scorer do AnchorEngine (vizinhos topicais: aula-13-teorema-de-rice atraída pelo rótulo
"Prova da Indecidibilidade") — MITIGADA por pino gold-backed, SEM guard estrutural. Item
[CODE] registrado; **insumo nomeado da campanha 2**. Padrão: cada camada consertada revela a
próxima — esperar o mesmo nas unidades.

## §4 Fila da próxima sessão, EM ORDEM

1. **Campanha 2/3 — Unidades** (rito brainstorm→spec→plano; ordem aprovada Índice→Unidades→SO).
   Escopo já desenhado: (a) fix colisão de rótulo de unidade (exclusividade de título na
   assinatura — caso MF u01 absorve "Verificação de Modelos" 1.3.1; agora + o resíduo do scorer
   §3.3); (b) unificação de assinatura sonda/produção (dual-source provado nos 2 sentidos);
   (c) curas gated por curso: **MF u03 · SO u04-deadlock (+2 anomalias: deadlock absorvido no
   topic_text bloco-05; ordem não-monotônica blocos 10-12) · ES2 u03-testes · IA u04/u05** —
   reprocess NÃO cura (provado 4×), cada curso com gold pré/pós; (d) herdados do review final:
   W1 adotar `_build_rich_content_taxonomy` (dual-source por cópia) + warning na degradação
   silenciosa do montador. Não existe gold de UNIDADE ainda — criar (one-time, user-side leve).
2. **Campanha 3/3 — SO providers** (57.9%→~85: janela-tópico, data-como-janela ±1, prior de
   revisão — regra institucional já registrada —, corroboração de band; mata os 10 cw band alta).
3. **Reprocess-all 5 repos** (fase final da unificação: prova de idempotência + curas aplicadas).
4. **Cutover FASE 5** — lista de deleção agora com 8 itens nomeados no tracker (inclui os 5
   novos do review final: version==3 no teste, vocabulário duplicado + import cross-package,
   W1→montador, W2 não escreve .content_taxonomy.json, degradação silenciosa).
5. Pendências menores paralelas: golden IA re-baseline gated · pino eth2 vs gold (oráculo do
   user) · minors mecânicos (preserve_raw, NFD TCC, hook cp1252, datalab_client).
6. Pós-motor: grafo em `scripts/` · bibliografia + Computação Gráfica HTML→PDF · gold rows dos
   +10 ES2/21 IA (opcional, user) · decisão de MERGE (`feat/motor-atribuicao`→`new-features`→
   `main`) — do user, branch READY.

## §5 Armadilhas/notas

- Workspace SDD da campanha 1 PRESERVADO em `.superpowers/sdd/2026-08-06-gerador-indice-unico/`
  (ledger + 9 task-reports; gitignored). Ledger = mapa completo de rulings/fix-rounds.
- Baselines que MUDARAM nesta sessão (não usar as antigas): fase4 53/58-58/58; fase5 6/8;
  fase2-TCC segue 84.2 mas com pino aula-13 embutido; MF eval 97.0.
- Reprocess headless agora lê flags vivas (T18) — sem `--flags`; linha `[profile]` no stdout
  é a confirmação.
- Rollback de repo-tutor: SEMPRE backup tracked+gitignored com eco por arquivo + sha256
  (provado 3× nesta sessão; glob silencioso = rede furada).
- Hook `code-review-graph` crasha cp1252 em todo commit — cosmético, item no tracker.
- mem-search continua fora do ar ("Worker API: fetch failed") — contexto vem de
  handoff+tracker+ledger.
