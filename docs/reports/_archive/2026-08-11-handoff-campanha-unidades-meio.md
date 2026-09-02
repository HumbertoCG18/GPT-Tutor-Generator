# Handoff — sessão 2026-08-07/08: campanha 2 (Unidades) a ~80%; fila = review T10 → ruling IA → fechamento

**Branch:** `feat/motor-atribuicao`. Sucede `docs/reports/2026-08-07-handoff-campanha-indice-fechada.md`.
**Fonte de estado fino desta campanha: o LEDGER SDD** `.superpowers/sdd/2026-08-07-campanha-unidades/progress.md`
(gitignored; linha "PAUSA DO USER" marca o ponto exato). Spec/plano:
`docs/superpowers/specs/2026-08-07-campanha-unidades-design.md` (v2) ·
`docs/superpowers/plans/2026-08-07-campanha-unidades.md`. **ATENÇÃO: o tracker
`pendencias.md` NÃO foi atualizado nesta sessão — dívida explícita da T13.**

## §1 Estado

Tasks 1-10 + T7a FECHADAS (reviews clean; T10 com review PENDENTE — ver fila). Suite
**1916 passed / 1 failed / 4 skipped** (1 = golden IA stale conhecido, item próprio).
**Placar eval_units (régua NOVA de unidades, gold do user congelado 4/5):**
MF 12/14=85.7 · SO 9/11=81.8 · ES2 7/7=100 · TCC 13/13=100 · IA aguarda ruling.
Misses restantes MF/SO = POLÍTICA (overview/deliverable/véspera não carregam unidade), não erro.
**Índices em disco:** MF 3/3 unidades (bloco-16→u03 ✓) · SO 7/7 (u04-deadlock NASCEU via
split+pino) · ES2 3/3 (4 pinos) · TCC 4/4 · IA intocado (lock até ruling).
Commits-chave projeto: `dd10126..e3d9f25` (U1/U1c/U1b/U5/U2/gold/curas). Repos-tutor:
MF `30454ee` · SO `24029c5` · ES2 `b06b264` · TCC `76e6038` (refresh) · IA nenhum.

## §2 O que esta sessão fechou (além das tasks)

**Refresh de cronograma 5/5 (T7a, ruling user "opção A")**: descoberta do user via gold →
os 5 SARC importados estavam STALE (40 diffs reais; Copa em junho, TP1 SO remarcado, agentes
IA empurrados). Perfis re-sincronizados (syllabus = TABELA do vivo; bullets NÃO parseiam —
armadilha documentada no ledger), 4 repos reprocessados gated, goldens re-baselined.
Ferramenta permanente: `scripts/check_sarc_freshness.py` (gate exit-1).
**Gold de unidades**: xlsx com dropdown (`scripts/gold_units_xlsx.py` build/export/fix-dropdowns),
82→86 blocos-régua, rotulagem user 4/5 congelada em `tests/fixtures/eval/gold_units_*.csv`,
baseline `docs/reports/2026-08-08-eval-units-baseline.json`. IA: rotulagem substituída por
`CRUZAMENTO_IA_SARC.md` (validável, insumo do ruling).
**Curas**: MF (refresh já aplicou U1/U1b) · SO em 3 atos (9a sinal: E/S "/" invisível +
office_hours sequestrando aulas + higiene topic_text; 9b investigação; 9c splits por
`boundary_dates` na curadoria + 3 pinos) · ES2 (4 pinos gold-backed, ruling user mantendo
u03 posicional).

## §3 Lições técnicas

1. **5ª geração da família prova/rótulo**: cada camada consertada revelou a próxima —
   exclusividade de título (U1) → empate de CAMINHO no DP (U1b) → co-ocorrência afoga
   deadlock → **inversões LOCAIS calendário-vs-plano** (deadlock antes de concorrente; E/S
   antes de arquivos) que o DP monotônico não expressa → resolvidas por PINO GOLD-BACKED
   (precedente aula-13; agora 3 no SO + 4 no ES2). M1/M2 (dedup título/boost core) MEDIDOS
   e descartados: 0 ganho, matrizes no report 9c.
2. **Régua mede o que o sistema produz**: gold por BLOCO (não sessão — 1 straddle real em
   82; não subunidade — lição mundo-63), keyed por `block_uuid`, política unit:False vira
   miss DOCUMENTADO, não rótulo forçado.
3. **SARC vivo > import**: freshness é gate permanente; `#` do SARC não numera
   suspensão/devolução/G2 (37≠40 explicado).

## §4 Fila da próxima sessão, EM ORDEM

1. **Review da T10** (pendente; pacote `review-f28d8e1..e3d9f25.diff` no workspace). Atenção:
   golden ES2 `divisao_blocos` foi editado À MÃO (1 linha, bloqueio de comando) — verificar
   vs índice vivo + `pytest -k ES2`.
2. **T11 — ruling IA (HALT, decisão do user)**: insumos prontos — `CRUZAMENTO_IA_SARC.md`
   (inversão provada linha a linha; u04 sem aula própria; regra de provas CUMULATIVA do
   plano IA), sonda pós-refresh dá 3 unidades (era 2). Opções a apresentar: aceitar
   limitação documentada / pinos gold-backed em massa / modo não-monotônico por curso.
   Depois do ruling: refresh+cura IA gated (perfil já tem syllabus vivo; repo intocado).
3. **T12** — sandbox aula-13 TCC (U6: re-medir scorer sem pino; veredito guard-ou-óbito).
4. **T13 — fechamento**: review final whole-branch (com lista de minors do ledger) · tracker
   pendencias.md (dívida ACUMULADA: campanha inteira + itens novos: classifier
   review-posicional/workshop/correção [RED pronto], PS/G2 estrutural, covered_units,
   remendo golds antigos ~60 linhas com SO hard=13, subunidades candidato, boundary_dates
   sem validação de data, golden IA re-baseline) · spec/plano → Feitos/ · handoff campanha 3.

## §5 Armadilhas/notas

- **Snapshots de rollback** copiados do scratchpad (morre com a sessão) para
  `.superpowers/sdd/2026-08-07-campanha-unidades/snapshots/` (sidecars gitignored dos
  repos + backups do subjects.json com SHA256SUMS).
- **NÃO reprocessar cursos pela GUI** — IA especialmente (algoritmo novo no código mudaria
  unidades sem gate; sonda IA=3 unidades vs disco 3, mas com conteúdo diferente).
- xlsx: save do Excel derruba os dropdowns na gravação openpyxl seguinte —
  `python scripts/gold_units_xlsx.py fix-dropdowns` após QUALQUER gravação minha.
- `sha256sum *` NÃO pega dotfiles — usar `.[!.]* *` (furo achado e corrigido 2×).
- Golden IA (`test_atribuicao_dos_casos_chave_atual[IA]`) segue o ÚNICO fail esperado da
  suite; segundo fail = regressão real.
- mem-search segue fora do ar; contexto = este handoff + ledger SDD + reports da campanha
  em `docs/reports/2026-08-0*.md` e `.superpowers/sdd/2026-08-07-campanha-unidades/`.
