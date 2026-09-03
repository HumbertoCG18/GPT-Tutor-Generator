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
Gerador `feat/motor-atribuicao` (ver `git log`; item 2 = `fe2c4fb`, item 3 = `b802a68`, item 4 = `79fc92a`, item 5 = `fdf28af`,
ancora-faixa = `b1d565a`, + docs). Tutores: MF `e39e14a` SO `603d914` IA `ca1f765` ES2 `2212f9f` TCC `b9af3c3` (os 5 com estrutura do Moodle no manifest, 03/09) CG `19472d1` LR `0e3ab1a`
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
   **PROXIMO ITEM = 8 (rebuild FR -> LR -> CG pela API; gate da Fase 3 registrado no tracker §GATE DA FASE 3).**
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
3. ~~**3b Card como documento ordenado = provider de janela**~~ FEITO 03/09 (tracker §FASE 3b): `routing/motor/card_stream.py`
   (`card_windows(entries, ctx)`: por secao, grupo de entries com o mesmo `moodle_week_label` = run de semanas; DP monotonica
   por categoria, tokens material x semana + assinatura SARC) -> `provider_card` FORA da `_CASCADE`: o `anchor_engine` so o
   consulta (a) sem janela, antes do llm-funil, e (b) em decisao ainda FLAGADA **depois do voter** (card antes do voter
   calava o LLM em janela-1 e a curada caiu 199 -> 187; medido e revertido). Janela-1 do card e gateada como data/topic;
   decisao do card sem flag sai com banda "media" (precisao medida 8/11); card que repete o bloco e a duvida nao renomeia
   o provider. 3a estendido: modulo com data no nome ("12/03 Processos") ancora os seguintes (SO week_label 0 -> 30).
   Numeros: motor puro 161 -> **173**/200 (conf-err 3 = 3), unidade 158 -> 161, +vocab 162 -> 172 · 167 -> 171 · sub 79 -> 82;
   AULA 152 -> **163**/189 (+16/-5 nos golds; REF 9 -> 8: SO laminas-sockets, bibliografia, flagada antes e depois);
   curada 199/200 · 191/191 · 55/57 · 93/93 intacta, sentinela 0, censo 53,2 (o voter ja decidia tudo que o card decide —
   o ganho e do motor puro / sem voter). 5 erros do card que ESCAPAM da fila (band media sem flag: MF revisao, arvores,
   intro, listas, terminacao) — insumo do item 7 (`calibra_revisar`).
4. ~~**3b Ordem das secoes** + **card generico -> apresentacao**~~ FEITO 03/09 (tracker §FASE 3b item 4). (a) Ordem das
   secoes: `mede_ordem_secoes.py --chain --only-flagged` agiu em **0** depois do item 3 (os +7/-1 eram flagados que o card
   ja decide) — sem numero, NAO entrou (nada de codigo). (b) Card generico: raiz e a **secao 0 do Moodle** (area geral do
   curso; `moodle_section_index == 0`), nao o nome do card (o regex `informa|geral` pegava "Busca com Informacao" no IA):
   `resolve_general_section` no `anchor_engine`, sem janela nenhuma, depois de prep-prova e card, antes do llm-funil,
   so no caminho lexical; method `secao-geral`, banda media, irma de meta/ref-generica (`_first_class_block_decision`
   extraida). Numeros: motor puro 173 -> **176**/200, unidade 161 -> 164; +vocab 172 -> 175 · 171 -> 174; AULA 164 -> **167**/189
   sem vocab, 163 -> **166** com vocab;
   curada 199/200 · 191/191 · 55/57 · 93/93 intacta; no curado SO `apresentacao-da-disciplina`, `questoes-do-enade`,
   `programa` saem do llm-funil (18 -> 15 nos 8; revisar/100 53,2 -> 52,6; votos/100 33,8 -> 32,9).
5. ~~**3c Tokens curtos consagrados pelo cronograma**~~ FEITO 03/09 (tracker §FASE 3c): `text/tokens.py::motor_tokens` = tokenizador
   unico (corte 3, strangler: `disambiguator._toks` delega, byte-identico; os outros 12 migram em C4); `course_short_vocab(ctx)`
   (2-3 chars consagrados por topic_text + labels de sessao, memoizado); `disambiguate` refaz o desempate D4 com o vocab curto
   nos DOIS lados SO quando o lexico padrao ficou flagado, adota se muda o bloco ou tira a flag, method `disamb-curto`.
   Numeros: motor puro 176 -> **180**/200 (IA k-NN x4, 0 perdas; conf-err 3), +vocab 175 -> **179**; AULA 167 -> **171** sem
   vocab, 166 -> **170** com vocab; curada 199/200 · 191/191 · 55/57 · 93/93 intacta (IA: 3 votos de LLM viram disamb-curto,
   mesmo bloco); censo llm 71 -> 68, revisar/100 52,6 -> 51,7, votos/100 32,9 -> 32,0.
   **HOLDOUT CG (pedido do user 03/09, curso do semestre NAO usado para afinar):** `_harness-2026-09-02/holdout_cg.py <GEN> <COPY>`
   (motor puro, sem voter/vocab, gold `ground_truth_CG.csv` scorable 35): codigo pre-item 2 (`b0b3b42`) **27/35** -> HEAD
   **30/35**, conf-err 1 = 1, flagados 19 -> 16. Os 3 ganhos sao do item 5 ("2d" consagrado pelas sessoes do bloco-06);
   itens 3-4 nao agem no CG porque o professor nao usa label datado nem data no nome (week_label vazio) — ausencia de
   sinal, nao overfitting. Regua nova: roda a cada item daqui em diante (baseline 30/35).
6. ~~**3d Label/titulo com token unico a 1 bloco da janela**~~ NAO ENTRA (03/09): `mede_alavancas.py` pos-item 5 = 0/0 (ja
   certo 3); H5 serie +1/-2 e H2 prova antiga 0/0 seguem refutados. Motor puro (com vocab) nos 203 golds: **182/203**, 21 erros
   = 8 confiantes (MF exerciciosdafny2/revisao/arvores/intro/listas/terminacao, ES2 azure, TCC aula-17) + 13 flagados; residual
   para o LLM 35 materiais (17/100); teto com LLM nos residuais ~195/203. **Refinamento do item 3 (mesma sessao, tracker
   §ITEM 6 + ANCORA):** modulo sem data depois de ancoras "dd/mm" recebe a FAIXA da secao (uniao das ancoras) e o texto decide;
   modulo com data propria (`extract_date_in_name`) fica no seu bloco. +4/0 (SO exemplo-criacao x4): motor puro 180 -> 183,
   unidade 168, cobertura 54, sub 30; AULA 171 -> 174 sem vocab; curada intacta, sentinela 0.
7. ~~**Gate da Fase 3**~~ REGISTRADO 03/09 (tracker §GATE DA FASE 3): AULA 152 -> **174**/189 (175 sem vocab) — batido; curada
   199/200 · 191/191 · 55/57 · 93/93 — intacta; motor puro 161/158/51/26 -> **184/168/54/30**, +vocab 162/167/50/79 ->
   **183/178/53/82**; censo votos/100 33,8 -> 32,0 — caem; holdout CG 27 -> 30 (curado 34/35). **Residual flagado em AULA
   18,5/100 (meta <= 8 NAO batida)**: as alavancas decidem mantendo a duvida honesta; o balde e o item 11.
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
