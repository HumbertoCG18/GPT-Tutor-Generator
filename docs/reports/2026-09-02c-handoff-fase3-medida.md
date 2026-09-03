# Handoff 2026-09-02c — PONTO DE ENTRADA da proxima sessao: fechar a rodada do motor (Fase 3 revisada)

Unico handoff vivo desta rodada; os dois anteriores de 02/09 estao em `_archive/` (contexto; NAO reabrir a fila deles). **Leia nesta ordem:** (1) este arquivo; (2) `pendencias.md` §"SEQUENCIA ACORDADA" (a lista numerada) e
§"FASE 1b … MEDICAO" (numeros); (3) `2026-09-02-plano-fechar-o-motor.md` §"REVISAO 02/09 (noite)".
Artifacts: "Raio-X da Atribuicao" (https://claude.ai/code/artifact/399626ee-682b-43f8-9987-09c344f6c60f) e
"Gold x Moodle x SARC" (https://claude.ai/code/artifact/f53542b1-9061-4034-a1f3-e86ce001a81f).

## Leis (inalteradas) + o que o dado de 02/09 acrescentou
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · gate = eixos + subunit_gt + pytest + sentinela +
determinismo + ablacao nu/curado + motor puro (+ `--com-vocab`) · **nada regride na regua de AULA nem na curada** · commits
com trailers · [Humberto]. Acrescentado: (a) **estrutura estreita, texto decide, estrutura NUNCA sobrepoe decisao confiante**
(medido: a tudo +13/-10; so flagados +12/-5); (b) a verdade estrutural esta no Moodle pela API (labels de semana, ordem dos
modulos, ordem das secoes) — o export a apaga; (c) foco = material de AULA (189/203 golds); referencia e contexto (watchdog).

## Documentos (arrumados 03/09 — "1 -> 2 -> 3")
Vivos: este handoff (fila + estado) · `pendencias.md` (tracker, ~400 linhas: SEQUENCIA, REGUA DE TRAVESSIA, FASE 1b, FASE 0,
PENDENCIAS ANTIGAS AINDA ABERTAS, CAMPANHA FUTURA web) · `2026-09-02-plano-fechar-o-motor.md` (desenho das fases e decisoes;
secoes ESTADO/REVISAO carimbadas como historico). Historico: `_archive/` (35 handoffs + `pendencias-historico-ate-2026-09-02.md`,
4.8k linhas cortadas do tracker). Os 4 worktrees de junho em `.claude/worktrees/` foram removidos (commits ja na `main` ou
equivalentes; branches `worktree-*` mantidos). Regra: 1 handoff vivo; novo handoff = o anterior vai para `_archive/`.

## Estado ao comecar (tudo commitado, NADA pushed)
Gerador `feat/motor-atribuicao` (ver `git log`; ultimo desta sessao = docs consolidados). Tutores: MF `61a9104` SO `c81527f`
IA `002c169` ES2 `09e3739` TCC `84670e4` CG `19472d1` LR `0e3ab1a` FR `64990dc` (com o vocab compilado;
`.glossary_curation.llm.json` em MF/CG/LR/FR). `subjects.json`: `compile_vocabulary: true` nos 8. `raw/moodle/{sections,
contents,labels}.json` gravados nos 8 (gitignored; copia versionada em `_harness-2026-09-02/moodle_sections/` e
`moodle_contents/`). Copias `.ablacao` dos 5: puro + vocab. Suite 2232.
Reguas: curada 199/200 · 191/191 · 55/57 (eth2 = referencia, watchdog) · 93/93 · revisar 53,2/100 · motor puro 161/158/51/26 ·
puro+vocab 162/167/50/79 · **AULA 152/189**.

## Decisoes
- A (tutores com vocab) — FEITA. B (gold de cobertura eth2/aws: {u02} ou N:N) — pendente, nao trava.
- **C — FECHADA (02/09 noite): API-first para todo curso com semestre EM ANDAMENTO (CG/LR/FR agora, todos os futuros);
  backfill da estrutura para os 5 ENCERRADOS (MF/SO/IA/ES2/TCC = regua de regressao, ids/golds intocados); export so
  fallback sem estrutura.**

## FILA (ordem; cada item do motor = TDD + regua de AULA + curada intacta + sentinela 0 + commit + tracker)
**Do user:** revisar os golds proposto-claude (`travessia_gt_{IA,FR,CG}.csv`, `subunit_gt_FR.csv`, `ground_truth_CG.csv`).
Push quando quiser.
1. ~~**Baseline de travessia ("antes")**~~ FEITO 02-03/09 (IA/FR/CG x sem-llm/LLM/`--contexto-completo`; resultados em
   `travessia_result_*.json`, tabela + as 6 medicoes em `pendencias.md` §REGUA DE TRAVESSIA). Resumo: FR 15/15; IA 9/15 e
   CG 8/15 com LLM (abaixo do piso por tokens, 10/15) porque o alvo esta fora do FILE_MAP cortado; IA 14/15 com FILE_MAP completo.
   Rerodar = `python scripts/eval_travessia.py {IA,FR,CG} [--sem-llm|--contexto-completo]` (cache: 0 chamadas se o contexto nao mudou).
1b. ~~FILE_MAP completo~~ MOVIDO para a campanha de travessia (user, 03/09: "terminar a campanha do motor"; assim o item 12
   mede so o motor). Watchdog de cobertura ja esta no censo. Candidatos em `pendencias.md` §PROXIMA CAMPANHA — TRAVESSIA.
   **PROXIMO ITEM = 2 (Fase 3a).**
2. **3a Backfill estrutural nos 5 encerrados** (reprocess, nao rebuild): ler `raw/moodle/contents.json` + `sections.json`;
   casar modulo <-> entry (nome do arquivo primeiro, depois `moodle_label` se unico na secao, depois stem — ver
   `_harness-2026-09-02/audita_gold.py`, que casou 151/189 golds de aula); gravar no manifest `moodle_section_index`,
   `moodle_module_index`, `moodle_week_label` (texto do label datado mais proximo antes do modulo / data no nome / secao-semana)
   e `FileEntry` correspondente; `build_motor_context` le. Higiene medida: label com ano != ano do curso e ruido (ES2 2025);
   label sem data nao ancora (MF "Trabalho 2:"). Gate: sentinela = SO os campos novos; entry sem match = sem estrutura, contado.
3. **3b Card como documento ordenado = provider de janela** (posicao na `_CASCADE` a MEDIR: entre `labels` e `data`?):
   semana do label -> faixa de blocos hospedaveis com sessao no intervalo; materiais alinhados as semanas por ordem
   (monotonico, por fluxo = categoria) + tokens; `disambiguate` de producao dentro da semana; so age onde a decisao atual e
   flagada. Regra e harness: `mede_card_ordenado.py --stream --only-flagged` (+12/-5).
4. **3b Ordem das secoes** como prior para cards sem data (`mede_ordem_secoes.py --chain --only-flagged`, +7/-1: ancoras so de
   cards de conteudo com janela datada; faixa do proprio card > vizinhos + encadeamento) e **card generico sem janela ->
   bloco de apresentacao** (irma da `resolve_generic_reference`, +3/0).
5. **3c Tokens curtos consagrados pelo cronograma** em `disambiguator._toks` nos DOIS lados (`short_vocab_from_topic_labels`
   sobre labels de sessao + topic_text; +4/-2, IA k-NN x4) — implementar como corte 3 do refactor (tokenizador unico como
   strangler SO no disambiguator, byte-identico primeiro, sentinela 0, depois o vocab curto).
6. **3d Label/titulo com token unico a 1 bloco da janela** decide, so flagados (+2/0).
7. **Gate da Fase 3**: AULA 152 -> ~174/189; residual flagado <= 8/100 em AULA; curada 199/191/93 intacta; `motor_puro.py` e
   `--com-vocab`; `calibra_revisar.py .ablacao`; censo (votos/100 caem). Registrar as 3 linhas da regua no tracker.
8. **Rebuild dos 3 do semestre corrente pela API**, comecando pelo FR (menor, SARC com cores): antes, pull do FR em pasta
   temporaria e DIFF DE IDS contra o repo atual; se batem, troca limpa; se nao, build novo (sem gold, sem custo). Protocolo
   do run real: zero curadoria, summaries ON, vocab compilado, voter ON com cap e contagem, watchdogs; o user revisa a fila
   `revisar`; cada correcao = override + gold-por-fenomeno. Depois LR, depois CG.
9. Refactor corte 1 (`scripts/` 79 -> ~25; harnesses de `_harness-2026-09-02/` que viraram rotina sobem para `scripts/`,
   o resto arquiva) — sessao curta, sentinela 0.
10. **Fase 2** cronograma manda na unidade (unidade explicita na linha > ancora forte > ancora > DP so preenche), medida no
    que a estrutura nao resolveu; depois `--flags recompile_vocab` no CG.
11. **Fase 4** LLM residual so nos flagados, cacheado, contado no CRONOGRAMA_HEALTH (votos/100 e revisar/100).
12. **Travessia "depois"** = rerodar o item 1; comparar (mede so o motor, FILE_MAP intacto). Depois abre a CAMPANHA DE
    TRAVESSIA (`pendencias.md` §PROXIMA CAMPANHA: FILE_MAP completo e magro primeiro, unico com numero; grafo/vetores nao).
Depois da fila do motor (sequencia acordada): referencias (regua propria, 10 golds) -> imagens e provas (criar gold antes de
regra) -> limpa pre-web (`auditoria-enxame`, cortes 2 e 4, `concept_resolver` so apos medir os 8 consumidores) -> `graph.json`
derivado como modelo de dados da fase web.

## NAO fazer (refutado no gold em 02/09)
Serie `k -> k-esimo bloco` (+5/-10) · serie monotonica por DP (+1/-2; so-flagados 0) · prova antiga -> prep (0) · label em
decisao CONFIANTE (+3/-2) · identidade por "termo contido em titulo de material" (tira 2 ganhos do FR para 1 do MF) ·
aliases compilados so na rota de subunidade (perderia unidade +9) · rebuild dos 5 encerrados pela API (invalida golds).

## Ferramentas (todas em `docs/reports/_harness-2026-09-02/` salvo indicado)
`scripts/motor_puro.py [--com-vocab]` · `scripts/censo_motor_llm.py` · `scripts/eval_travessia.py` · `scripts/sentinela_manifests.py` ·
`calibra_revisar.py` · `mede_alavancas.py` · `mede_ordem_secoes.py` · `mede_card_ordenado.py` · `regua_aula.py` ·
`audita_gold.py` (+ `auditoria_gold.csv`) · `moodle_sections/*.json`, `moodle_contents/*.json`, `picks_*.json`.
