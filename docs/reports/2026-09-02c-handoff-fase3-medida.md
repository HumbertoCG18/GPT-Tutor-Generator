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
Gerador `feat/motor-atribuicao` (ver `git log`; item 2 = `fe2c4fb` + docs). Tutores: MF `e39e14a` SO `9c320b0`
IA `ffd9fdb` ES2 `2212f9f` TCC `b9af3c3` (os 5 com estrutura do Moodle no manifest, 03/09) CG `19472d1` LR `0e3ab1a`
FR `64990dc` (os 3 do semestre corrente ganham os campos no rebuild do item 8; hook ja roda) (com o vocab compilado;
`.glossary_curation.llm.json` em MF/CG/LR/FR). `subjects.json`: `compile_vocabulary: true` nos 8. `raw/moodle/{sections,
contents,labels}.json` gravados nos 8 (gitignored; copia versionada em `_harness-2026-09-02/moodle_sections/` e
`moodle_contents/`). Copias `.ablacao` dos 5: puro + vocab (com os 3 campos). Suite 2250.
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
   **PROXIMO ITEM = 3 (Fase 3b, card ordenado).**
2. ~~**3a Backfill estrutural nos 5 encerrados**~~ FEITO 03/09 (tracker §FASE 3a): `backfill_moodle_structure_repo` em
   `sources/moodle.py` + hook `_run_moodle_structure_backfill` na regeneracao (antes do motor, idempotente, so se
   `raw/moodle/contents.json` existe); 3 campos em `FileEntry` (`moodle_section_index`, `moodle_module_index`,
   `moodle_week_label` = texto do label DATADO antes do modulo; "data no nome" = `moodle_label` e "secao" = `source_section`,
   ja no manifest — nao duplicados; `MotorContext` nao mudou: o entry carrega os campos e o provider de 3b le do entry).
   Casamento por secao: savename/filename -> `moodle_label` unico -> stem. Higiene: `description` manda sobre `name` (cache
   stale: ES2 name 2025/description 2026, MF "Trabalho 1 (06/05/2026):"/"Trabalho 1:"); sem data nao ancora; ano != cronograma
   e ruido. Encerrados: MF 62/63 · SO 38/39 · IA 57/57 · ES2 35/35 · TCC 25/27 entries com card casadas (4 sem match =
   renomeados no Moodle depois do stash); week_label em MF 56, ES2 30 (SO/IA/TCC: labels sem data). Gate: sentinela 0 nos 8,
   diff total = so os 3 campos, curada 199/200 · 191/191 · 55/57 · 93/93, puro 161/158/51/26, +vocab 162/167/50/79, AULA
   152/189, censo 53,2, suite 2250, determinismo 0. 12 testes em `tests/test_moodle_structure.py` (fixture real
   `tests/fixtures/moodle/contents_excerpt.json`).
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
   **Pre-requisitos do CG (resgatados do historico em 03/09):** (a) `.htm` sem L nao e classificado por
   `stash_import._classify_file_type` — cai em `skipped` e a UI so mostra a contagem; fix = extensao + listar os nomes dos
   ignorados (teste); (b) "modals" do CG — investigar o que e tecnicamente antes de dizer que sobrevive a extracao;
   (c) "em duvida 28/08" (PS/G2 como principais, cadeira sem prova, `U1 - ...`/"Laboratorio N", Lab SO sem avaliacao no plano)
   — triar so nos flagados do rebuild, nao antes.
9. Refactor corte 1 (`scripts/` 79 -> ~25; harnesses de `_harness-2026-09-02/` que viraram rotina sobem para `scripts/`,
   o resto arquiva) — sessao curta, sentinela 0.
10. **Fase 2** cronograma manda na unidade (unidade explicita na linha > ancora forte > ancora > DP so preenche), medida no
    que a estrutura nao resolveu; depois `--flags recompile_vocab` no CG.
11. **Fase 4** LLM residual so nos flagados, cacheado, contado no CRONOGRAMA_HEALTH (votos/100 e revisar/100).
12. **Travessia "depois"** = rerodar o item 1; comparar (mede so o motor, FILE_MAP intacto). Depois abre a CAMPANHA DE
    TRAVESSIA (`pendencias.md` §PROXIMA CAMPANHA: FILE_MAP completo e magro primeiro, unico com numero; grafo/vetores nao).
## CAMPANHAS DEPOIS DO MOTOR — lotes de pendencias, em ordem (definido 03/09)

**Protocolo anti-regressao (vale para TODO lote; e o que impede "arrumar um eixo e quebrar outro"):**
1. Gold antes de regra: a regua PROPRIA do lote existe e tem baseline medido antes do primeiro commit de codigo.
2. Gate de saida = todas as reguas existentes rodam e NENHUMA regride: curada (bloco 199/200 conf-err 0 · unidade 191/191 ·
   cobertura 55/57 · subunidade 93/93 + FR 14/18), AULA (`regua_aula.py`), travessia IA/FR/CG, revisar/100, sentinela 0 fora
   do campo tocado, determinismo 2x, motor puro ± vocab, ablacao, suite pytest. Numeros das 3 linhas no tracker a cada item.
3. Tutores: reprocess em COPIA (`.ablacao`) primeiro; diff de manifest (sentinela) antes de tocar originais; commit dos 8
   so no fim do lote. Nada pushed sem o user.
4. Tamanho: 4-7 itens, <= 3 sessoes. Item que crescer vira lote proprio. Nada entra num lote sem numero ou sem gold.
5. 1 handoff vivo: novo lote = novo handoff, o anterior vai para `_archive/`; tracker registra numero e commit de cada item.

**C0 — MOTOR (em curso) = itens 2-12 acima.** Gate = item 7 + item 12. Push/merge em main e decisao do user no fim de C0.
**C1 — TRAVESSIA (1 sessao).** FILE_MAP completo e magro (unico com numero: IA 9 -> 14/15): rastreabilidade -> `FILE_MAP_TRACE.md`,
   coluna "Secoes" limitada, clamp 80 KB + aviso. Gate: IA >= 14/15, FR 15/15, CG rerodado, sentinela 0 no motor. Indice por
   unidade / de termos / "quando abrir" por LLM SO se a regua pos-C1 mostrar erros dessa forma. Vai ANTES de C2/C3 porque
   esses lotes adicionam o que o tutor precisa ACHAR (referencias, provas); indice cortado esconderia o ganho.
**C2 — REFERENCIAS (4 itens).** Vetar o gold `coverage_gt_{SO,MF,IA}.csv` (9/10; MF/IA proposto-claude); decisao B (eth2/aws
   {u02} ou N:N); pino de cobertura 57/57 (mecanismo, ou 55/57 aceito como teto documentado); consumo de bibliografia
   (decisao 22/07 "caso a parte": desenho + medicao, sem estourar o Project). Gate: regua de referencias sobe de 0/9; cobertura
   curada nao cai.
**C3 — PROVAS E IMAGENS (4 itens).** Ruling da granularidade (prova inteira x questao a questao); P2b-LLM (extracao de questoes,
   cacheado, contado); EXAM_INDEX "incidencia por topico" honesto; imagens: descricao do Datalab consumida pelo tutor. Gold
   ANTES: ~10 provas + ~10 imagens rotuladas. Gate: gold medido; curada intacta.
**C4 — LIMPA PRE-WEB (refactor, 6 itens).** Cortes 2 e 4; 13 tokenizadores -> 1; 17 limiares -> `thresholds.py`;
   `concept_resolver` so apos medir os 8 consumidores de `computed_block_*`; CODE_INDEX "sem aula atribuida" (decisao H);
   `auditoria-enxame`. Gate: BYTE-IDENTICO (determinismo, sentinela 0 total, ablacao identica, suite verde) — zero mudanca de numero.
**C5 — DIVIDAS DE DADOS (dependem do user; paralelizavel).** Lab SO (SARC da turma 310); GAP VIDEO do T2; 10 suspeitos do
   `detecta_headings`; sobras do "em duvida 28/08" que o item 8 nao encostar. Gate: gold proprio por item.
**C6 — WEB.** Backlog vivo (`pendencias.md` §CAMPANHA FUTURA) + `graph.json` derivado como modelo de dados. Depois de C4.

## NAO fazer (refutado no gold em 02/09)
Serie `k -> k-esimo bloco` (+5/-10) · serie monotonica por DP (+1/-2; so-flagados 0) · prova antiga -> prep (0) · label em
decisao CONFIANTE (+3/-2) · identidade por "termo contido em titulo de material" (tira 2 ganhos do FR para 1 do MF) ·
aliases compilados so na rota de subunidade (perderia unidade +9) · rebuild dos 5 encerrados pela API (invalida golds).

## Ferramentas (todas em `docs/reports/_harness-2026-09-02/` salvo indicado)
`scripts/motor_puro.py [--com-vocab]` · `scripts/censo_motor_llm.py` · `scripts/eval_travessia.py` · `scripts/sentinela_manifests.py` ·
`calibra_revisar.py` · `mede_alavancas.py` · `mede_ordem_secoes.py` · `mede_card_ordenado.py` · `regua_aula.py` ·
`audita_gold.py` (+ `auditoria_gold.csv`) · `moodle_sections/*.json`, `moodle_contents/*.json`, `picks_*.json`.
