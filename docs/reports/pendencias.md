# Pendências — tracker vivo

last_updated: 2026-09-02 noite (rodada do motor: Fase 0 e 1b feitas; Fase 3 reescrita pelo dado; decisao C fechada = API-first para cursos em andamento (CG/LR/FR) e backfill nos 5 encerrados; regua de AULA 152/189 e regua de travessia criadas; ponto de entrada = handoff 2026-09-02c). 03/09 madrugada: as 6 medicoes
fecharam (§REGUA DE TRAVESSIA, bloco MEDICOES FECHADAS); watchdog do censo casa por nome de arquivo; 1b adiado para a campanha
de travessia. 03/09 sessao 4: **item 2 (Fase 3a) FEITO** (gerador `fe2c4fb`, 5 tutores reprocessados; §FASE 3a);
item 3 (Fase 3b, card ordenado) FEITO na mesma sessao (§FASE 3b; AULA 152 -> 163, curada intacta);
**proximo = item 4 (Fase 3b, ordem das secoes + card generico -> apresentacao)**. Tracker CORTADO em 03/09: historico (MOTOR PURO ate campanhas 1-3, 4.8k linhas)
em `_archive/pendencias-historico-ate-2026-09-02.md`; aqui so o vivo. Documentos vivos = este + handoff 2026-09-02c + plano
2026-09-02 (desenho/decisoes, carimbado).

## SEQUENCIA ACORDADA (02/09 noite) — a lista, em ordem (detalhes no handoff 2026-09-02c)

**Rodada atual = fechar o motor de MATERIAL DE AULA (189/203 golds; regua `_harness-2026-09-02/regua_aula.py`, hoje 152/189).**
Gate por fase: AULA sobe, curada intacta (199/200 · 191/191 · 93/93), residual flagado <= 8/100, sentinela 0, motor puro
± vocab. Teto medido sem LLM ~92%; "100%" = LLM contado no residuo ou professor explicito — gate numerico, nao "100%".

Do user: revisar os golds proposto-claude (`travessia_gt_{IA,FR,CG}.csv`, `subunit_gt_FR.csv`, `ground_truth_CG.csv`);
decisao B (gold eth2/aws) quando quiser; push.
1. ~~Baseline de travessia~~ FEITO 02-03/09: IA/FR/CG x sem-llm/LLM/contexto completo (§REGUA DE TRAVESSIA). E o "antes".
1b. ~~FILE_MAP completo~~ MOVIDO para a CAMPANHA DE TRAVESSIA (decisao do user 03/09: terminar o motor primeiro; assim o
   item 12 mede o efeito do motor sozinho). Detalhe e candidatos em §PROXIMA CAMPANHA abaixo.
2. ~~Fase 3a — backfill estrutural nos 5 ENCERRADOS~~ FEITO 03/09 (`fe2c4fb`; §FASE 3a): 3 campos no manifest a cada
   regeneracao; encerrados 217/221 entries com card casadas; todas as reguas identicas; sentinela 0.
3. ~~Fase 3b — card como documento ordenado = provider de janela~~ FEITO 03/09 (§FASE 3b): AULA 152 -> 163/189, motor puro
   161 -> 173/200, curada intacta; card so depois do voter (antes dele regrediu a curada e foi revertido).
4. Fase 3b — ordem das secoes para cards sem data (+7/-1) e card generico -> apresentacao (+3/0).
5. Fase 3c — tokens curtos do cronograma no desempate (+4/-2), como strangler do tokenizador so no disambiguator.
6. Fase 3d — label unico nos flagados (+2/0).
7. Gate da Fase 3: AULA 152 -> ~174/189; residual <= 8/100; curada intacta; motor puro ± vocab; calibra_revisar; censo.
8. Rebuild pela API dos 3 do SEMESTRE CORRENTE (FR -> LR -> CG; diff de ids antes; protocolo do run real; user revisa
   `revisar`). Os 5 encerrados NAO se rebuildam (regua de regressao).
9. Refactor corte 1 (scripts 79 -> ~25), sessao curta.
10. Fase 2 — cronograma manda na unidade, no que sobrou; depois `recompile_vocab` no CG.
11. Fase 4 — LLM residual so nos flagados, contado.
12. Travessia "depois"; so aqui grafo renderizado / vetores, se a regua mostrar perguntas fora do alcance dos indices.
Depois do motor: LOTES C1..C6 com protocolo anti-regressao — handoff 2026-09-02c §CAMPANHAS DEPOIS DO MOTOR (C1 travessia
FILE_MAP -> C2 referencias -> C3 provas e imagens -> C4 limpa pre-web -> C5 dividas de dados -> C6 web). Cada pendencia deste
arquivo tem dono la; nada entra num lote sem gold e numero.

**PROXIMA CAMPANHA — TRAVESSIA (adiada 03/09; abre depois do item 12).** Runtime = Claude Project; FR (48k tokens) cabe na
janela, CG (206k) e IA (729k) estouram e dependem do retrieval do Project + indices. A regua (`eval_travessia.py`) mede so
indices = piso. Candidatos, por custo, so o 1o com numero:
1. **FILE_MAP completo e magro** (medido: IA 9 -> 14/15): rastreabilidade -> `course/FILE_MAP_TRACE.md` (45% dos bytes);
   coluna "Secoes" e lixo em slide ("Roteiro A conversa com voce ChatGPT Copilot icon Copilot"), limitar ou tirar; clamp so
   rede de seguranca (80 KB) com aviso no BUILD_REPORT. Gate: IA >= 14/15, FR 15/15, CG rerodado, sentinela 0 no motor.
2. Indice por unidade (2 saltos) — so se 80 KB pesar. Nao medido.
3. Indice de termos -> arquivo, renderizado do vocabulario compilado (`.glossary_curation.llm.json`, ja existe) — ataca
   "acuracia/precisao/recall" nao achar o deck de metricas. Nao medido; 1 tarde na regua.
4. Coluna "Quando abrir" por LLM 1x cacheada (hoje heuristica; e a coluna que o tutor cita) — ataca deck x notebook. Nao medido.
NAO: vetores proprios (o Project ja faz; o problema medido nao e semantica) e grafo para o tutor (manifest ja e o grafo;
FILE_MAP/COURSE_MAP sao projecoes; grafo visual e fase web). Limite da regua: nao mede o retrieval do Project.

**Decisao C (fechada 02/09 noite):** criterio nao e "novo x antigo", e "semestre em andamento x encerrado". API-first
(`moodle_pull`) para todo curso em andamento — e o unico caminho que acompanha o semestre (pull incremental com estrutura);
export so fallback sem estrutura. Encerrados: backfill.

**Refactor — quanto e quando (medido 02/09 noite):** `scripts/` 79 .py (+14 harnesses versionados) · motor/roteamento
8.739 linhas em 13 modulos (`timeline/index.py` 2.243, `file_map.py` 1.440, `content_taxonomy.py` 1.027) · **13 definicoes
de tokenizador** (eram 10; o bug do k-NN vive em uma delas e nao nas outras) · 17 limiares soltos fora de `thresholds.py` ·
`concept_resolver.py` 487 linhas com **8 consumidores** de `computed_block_*` fora do resolver — decisao H nao pode ser
"apagar" sem medir consumo. Antes da limpa so entra o que a Fase 3 encosta (corte 3 no disambiguator); corte 1 quando
incomodar; cortes 2 e 4 e o concept_resolver na limpa pre-web.

**Vetores / grafos / nodos (ideia do user, 02/09):** ADIADO ate a regua de travessia dar numero. Contra vetores no MOTOR: resumo
semantico na rota temporal foi REFUTADO (199 -> 194); o vocab compilado ja faz a ponte semantica barato e deterministico.
Grafo explicito (semana/card/material/bloco/unidade/topico) e a forma natural do dado que a Fase 3 importa — vale como MODELO
DE DADOS e visualizacao da fase web, nao como regra do motor. Regua de travessia: `scripts/eval_travessia.py` (feita).

## FASE 3a — ESTRUTURA DO MOODLE NO MANIFEST (03/09 sessao 4, item 2, FEITO)

**Entregue (gerador `fe2c4fb`; tutores MF `e39e14a` SO `9c320b0` IA `ffd9fdb` ES2 `2212f9f` TCC `b9af3c3`):**
`backfill_moodle_structure_from_api` + `backfill_moodle_structure_repo` (`src/builder/sources/moodle.py`), hook
`_run_moodle_structure_backfill` na regeneracao (antes do motor; so se `raw/moodle/contents.json` existe; idempotente: limpa e
refaz), 3 campos em `FileEntry`: `moodle_section_index` (= `section` da API), `moodle_module_index` (posicao na lista de
modulos da secao, labels contam), `moodle_week_label` (texto do label DATADO mais proximo antes do modulo; consecutivos
= ` || `). 12 testes (`tests/test_moodle_structure.py`, fixture real `tests/fixtures/moodle/contents_excerpt.json`).
Contrato em `.mex/context/institutional.md` §Moodle; decisao em `decisions.md`.
**Desvios do handoff, registrados:** (a) week_label guarda SO o label — "data no nome" ja e `moodle_label` e "secao" ja e
`source_section`, nao se duplica; (b) `MotorContext` nao mudou: o entry carrega os campos e o provider de 3b le do entry
(so `sections.json` nao foi lido: tudo que ele tem esta em `contents.json`); (c) texto do label = `description` sem HTML,
nao `name` — o `name` e cache stale (ES2 name "Semana 18/08/2025" com description "Semana 23/03/2026"; MF name "Trabalho 1
(06/05/2026):" com description "Trabalho 1:", que portanto NAO ancora).
**Casamento (entries com card):** MF 62/63 · SO 38/39 · IA 57/57 · ES2 35/35 · TCC 25/27 = **217/221**; 4 sem match = arquivo
renomeado/trocado no Moodle depois do stash (MF `logicadehoare-exercicios-respostas` -> hoje "respostas 1/2"; SO
`plano-de-ensino` -> hoje "Programa"; TCC `cubic-3-edge-coloring` -> "3-Edge Coloring", `3d-matching` -> "3-Dimensional
Matching") — sem estrutura, contados, sem fuzzy. week_label: MF 56, ES2 30, SO/IA/TCC 0 (labels sem data: SO tem a data no
nome do modulo = `moodle_label`; IA/TCC nem isso). Informativo p/ item 8 (hook ja roda, campos entram no rebuild): CG 48/73,
LR 3/6 (labs), FR 20/20.
**Gate (copia `.ablacao` primeiro, depois originais):** diff das copias e dos originais vs HEAD = SO os 3 campos (+ `updated_at`,
`last_seen`, `updated:`); sentinela 0 nos 8; curada 199/200 conf-err 0 · 191/191 · 55/57 · 93/93; motor puro 161/158/51/26;
+vocab 162/167/50/79 (subunidade 79/93); AULA 152/189 (151 sem vocab); censo revisar/100 53,2, votos/100 33,8;
suite 2250; determinismo 0/8 arquivos. Estrutura sozinha nao muda decisao — e o esperado do item 2.

## FASE 3b (item 3) — CARD COMO DOCUMENTO ORDENADO (03/09 sessao 4, FEITO)

**Entregue (gerador `b802a68`; tutor SO `5809cca`, os outros 4 byte-identicos):** `src/builder/routing/motor/card_stream.py` (`card_windows(entries, ctx)` -> {id: janela}; por secao, entries
consecutivas com o mesmo `moodle_week_label` = grupo alinhado ao run de semanas "W1 || W2"; DP monotonica por FLUXO
(categoria), score = tokens(moodle_label + titulo) x tokens(texto da semana + assinatura SARC dos blocos); semana dd/mm/aaaa
-> blocos hospedeiros com sessao no intervalo; "dd/mm Topico" -> ano modal); `MotorContext._card_windows_cache` preenchido
em `apply_anchor_engine`; `provider_card` FORA da `_CASCADE` (window_provider); `anchor_engine.resolve_unscoped` consulta o
card (a) sem janela, depois de prep-prova e antes do llm-funil, (b) em decisao ainda FLAGADA depois do voter. Janela-1 do
card gateada como data/topic (`_gated_window1_decision`); decisao do card sem flag = banda "media"; card que repete bloco e
flag nao renomeia o provider. 3a estendido: modulo com data no nome e ancora dos seguintes (`_DATE_PREFIX` no backfill).
14 testes em `tests/test_card_stream.py` + 2 em `test_moodle_structure.py`. Contrato/decisao em `.mex`.
**Medido (copias `.ablacao`, golds de bloco):** +16/-5, err->err 6 (3 ganhos vieram do irmao-card em cascata: ES2 roteiro1/2/4).
Motor puro sem vocab 161 -> 173/200, conf-err 3 -> 3 (foi a 15 com janela-1 incondicional e a 8 com gate; a banda "media"
fecha), unidade 158 -> 161, cobertura 51 = 51, subunidade 26 = 26. +vocab 162 -> 172 · 167 -> 171 · 50 = 50 · 79 -> 82.
AULA 152 -> 163/189 (sem vocab 151 -> 164); REF 9 -> 8 (SO `laminas-sockets-material-alternativo`, bibliografia, flagada antes
e depois: topic/disamb janela 5 -> card janela-1 07, gold 09); BASE 4/4. Perdas: MF exerciciosformalizacao-res (04 -> 03),
intro (06 -> 05), introducao-zip (12 -> 10, flagada), terminacao (12 -> 11), SO laminas-sockets — 4 delas = "gold DEPOIS da
postagem" (material postado na semana anterior a aula; padrao ja medido no `audita_gold`). Precisao das decisoes do card SEM
flag: 8/11 (73%) — por isso banda "media" (alta ~98%). Escapam da fila (errados, band media, sem flag): MF revisao, arvores,
intro, listas, terminacao — insumo do item 7 (`calibra_revisar .ablacao` hoje: 41,6/100, 6 erros de bloco em "ok").
**Curada (originais, voter ON):** 199/200 conf-err 0 · 191/191 · 55/57 · 93/93 — INTACTA; sentinela 0 nos 8; censo 53,2 e
votos/100 33,8 iguais. Leitura honesta: o voter ja decidia (certo) tudo que o card decide — o card so age onde nao ha voto.
Com o card ANTES do voter (1a versao): curada 199 -> 187, 191 -> 185, 55 -> 52, 93 -> 89 (janela-1 do card calava o LLM que
acertava: MF arvores/intro/listas/provas, SO exemplo-criacao x4). Revertido para "card depois do voter"; regra nova.
**Tutores:** so o SO muda no manifest (`moodle_week_label` 0 -> 30 pelas ancoras "dd/mm"; nenhum campo do motor); MF/IA/ES2/
TCC byte-identicos (revertido o `updated_at`). Determinismo (8 tutores, 2x, codigo final): 0 arquivos. Suite 2265.

## REGUA DE TRAVESSIA — baseline "antes" (02/09 noite)

Gold proposto-claude (revisar): `travessia_gt_IA.csv` e `travessia_gt_FR.csv`, 15 perguntas cada em 3 estilos (5 estruturadas,
5 ambiguas, 5 malformadas — o aluno cansado pergunta pior). Cardapios: `travessia_cardapio_{IA,FR}.txt`. Harness
`scripts/eval_travessia.py` (LLM so para medir, cache em `_travessia_cache/`; casamento da escolha por linha do FILE_MAP,
"linha N" e tokens — o tutor cita a descricao da linha, nao o Titulo).

Tabela fechada 03/09 madrugada (3 cursos x 3 modos; "contexto completo" = README + TUTOR_POLICY + os 4 indices por tipo alem
dos 4 de navegacao; matcher entende linha do FILE_MAP, "linha N" e titulo-resumo do CODE_INDEX — IA/FR rerodados do cache):

| curso | modo | hit@1 | hit@3 | bloco | estruturada | ambigua | malformada |
|---|---|---|---|---|---|---|---|
| FR (20 mat., FILE_MAP 20/20) | sem-llm | 9/15 | 11/15 | 5/6 | 4/5 | 2/5 | 3/5 |
| FR | **LLM** | **15/15** | 15/15 | 6/6 | 5/5 | 5/5 | 5/5 |
| FR | LLM + contexto completo | 15/15 | 15/15 | 6/6 | 5/5 | 5/5 | 5/5 |
| IA (59 mat., FILE_MAP 19/59) | sem-llm | 10/15 | 12/15 | 6/8 | 4/5 | 1/5 | 5/5 |
| IA | **LLM** | **9/15** | 10/15 | 8/8 | 3/5 | 2/5 | 4/5 |
| IA | LLM + contexto completo | 10/15 | 10/15 | 8/8 | 3/5 | 2/5 | 5/5 |
| IA | LLM + **FILE_MAP completo** (59 linhas, experimento em copia) | **14/15** | 15/15 | 8/8 | 5/5 | 4/5 | 5/5 |
| CG (73 mat., FILE_MAP 20/73) | sem-llm | 10/15 | 11/15 | 8/11 | 4/5 | 3/5 | 3/5 |
| CG | **LLM** | **8/15** | 8/15 | 7/11 | 2/5 | 3/5 | 3/5 |
| CG | LLM + contexto completo | 10/15 | 10/15 | 7/11 | 2/5 | 4/5 | 4/5 |

Leitura: com 20 materiais os indices bastam (15/15). Com 59 e 73, o LLM lendo indices e PIOR que o piso por tokens (IA 9 x 10,
CG 8 x 10) e o contexto completo so devolve o empate (10 x 10): os indices por tipo fazem o tutor citar CODIGO, nao achar o deck.
IA: (a) prefere notebook a deck quando pergunta "como funciona" e deck a notebook quando pede "exemplo pratico"/"codigo";
(b) nao acha o deck de metricas por "acuracia/precisao/recall" (escolhe pelo periodo "abordagem supervisionada"); (c) "o que
cai na P2?" responde com o CRONOGRAMA/SYLLABUS — nao e material; o gold tem que dizer se vale. CG: nos 7 erros com LLM o alvo
do gold esta FORA do FILE_MAP cortado (posicoes 32-57 do manifest: recorte, vis2d, fundamentosmatematicos, colisao, os 2
exercicios, transformacoes-geometricas-em-opengl) e a escolha errada esta DENTRO (`segmentacaopptx` pos. 2, `opengl3dcpp`
pos. 14, o pacote "Praticas 2D/3D"). Bloco: 8/8, 6/6, 7/11 — o "quando" o tutor acerta quando o material existe no indice.
**RAIZ DA PERDA COM O TAMANHO (medida 02/09 noite): o FILE_MAP e CORTADO em 12 KB** (`clamp_navigation_artifact(max_chars=12000)`,
`navigation.budgeted_file_map_md`, de abril/2026, "compacto e roteavel", sem medicao). O renderer emite TODOS os materiais
(1 linha + 1 linha de rastreabilidade, ~570 B cada); o clamp corta o TEXTO em 12 KB pela cauda, sem relevancia — sobrevivem
as ~20 primeiras linhas na ordem do manifest (IA posicoes 2-20, MF 3-22, CG 0-19). Cobertura (watchdog `cobertura_indices`
do censo, 03/09; casa por raw, nome de arquivo e id delimitado): FILE_MAP MF 20/66, SO 22/39, IA 19/59, ES2 21/35, TCC 18/27,
CG 20/73; so LR 6/6 e FR 20/20 cabem. Em indice NENHUM (nem FILE_MAP nem CODE/EXAM/EXERCISE/ASSIGNMENT_INDEX): MF 24, SO 13,
IA 12, ES2 11, TCC 9, CG 25 — e material-de-aula/"outros"/listas/provas: os indices por tipo cobrem so codigo, prova,
exercicio e trabalho, entao slide fora do corte fica invisivel. No IA faltam os 28 notebooks (so no CODE_INDEX, que o tutor e
mandado ler apenas "ao revisar codigo do aluno") e 12 materiais em indice NENHUM (deck de k-NN, metricas, redes neurais,
perceptron/reta, P1/P2, lista I, gabarito, agentes). **Experimento** (copia do IA,
FILE_MAP completo = 59 linhas / 33,7 KB; `_harness-2026-09-02/filemap_sem_clamp{,2}.py`): LLM **9/15 -> 14/15 hit@1, 10 -> 15/15
hit@3**; ambiguas 2 -> 4/5, malformadas 3 -> 5/5. A perda nao era do LLM nem do tamanho: era do indice incompleto. O piso
sem-llm nao muda (le o manifest, nao o FILE_MAP). Conserto candidato (medir na regua): FILE_MAP COMPLETO sempre (~570 B por
material; CG 73 -> ~42 KB), com a linha de rastreabilidade (~45% dos bytes; raw/tags/markdown-base, uso humano) movida para
`FILE_MAP_TRACE.md`, e clamp so como rede de seguranca alta (ex.: 80 KB) com aviso no BUILD_REPORT.
Consequencia para a fase web/grafo: o problema de travessia medido NAO e "achar por semantica"; com o indice completo o
LLM acha 14/15 lendo Markdown. Rerodar depois da Fase 3 = o "depois".

**MEDICOES FECHADAS 02-03/09 (os 6 itens, "faz na sua ordem, todos entram"):**
1. Subunidade FR (sidecar compilado por LLM, producao; gold `subunit_gt_FR.csv` proposto-claude): **14/18**. Erros = codigos de
   socket (udp-example-c/java -> `paradigmas-clienteservidor-e-p2p`; tcp-chat-c/tcp-example vazio). Total 5 cursos 107/111.
2. Gold de bloco do CG por ESTRUTURA (`ground_truth_CG.csv`; secao numerada do Moodle <-> topico do SARC, `gold_cg_estrutura.py`):
   61 materiais, **35 scorable** (26 a revisar: secoes 2, 5, 8, 10, 13, 16, 17 sem bloco unico); motor curado+LLM **34/35**, conf-err 1.
3. Travessia com contexto completo: tabela acima (IA 9 -> 10, FR 15, CG 8 -> 10). Nao substitui o FILE_MAP completo (14/15).
4. Travessia CG (`travessia_gt_CG.csv`, cardapio, 15 perguntas): tabela acima; 3o curso, mesmo padrao do IA.
5. Determinismo (8 tutores, 2x reprocess em copia, `_harness-2026-09-02/determinismo.py`): **0 arquivos** nao deterministicos
   (SO: so o `updated:` do STUDENT_STATE, rodada cruzou a meia-noite). A reordenacao do COURSE_MAP do ES2 (divida de 02/09) NAO
   reproduziu — fica como divida sem repro, nao como bug confirmado.
6. Watchdog de cobertura dos indices no censo (`cobertura_indices`): numeros acima. Divida achada: `code/CODE_INDEX.md` do IA
   diz "⚠ Sem aula atribuida (requer atribuicao manual)" em codigo que TEM bloco temporal — consumidor de campo antigo
   (`computed_block_id`, decisao H) desatualizado; entra no corte 1 do refactor.
Resultados versionados: `travessia_result_{IA,FR,CG}_{sem-llm,llm,llm-completo}.json` + `_travessia_cache/`.

## FASE 1b — vocabulario compilado por LLM + MEDICAO "o que falta para 200" (2026-09-02, sessao 3, parte 2)

**Entregue (`86fc9b3`):** `src/builder/core/vocabulary_compile.py` (`compile_course_vocabulary`, 1 chamada por unidade COM
material, prompt v2 medido, schema pydantic, client fake nos 25 testes de `tests/test_vocabulary_compile.py`). Sidecar
`course/.glossary_curation.llm.json` (formato do loader, chave "<codigo> <label>", `_provenance`, `_raw`); loader funde manual +
llm; flags de curso `compile_vocabulary` (ligada nos 8 perfis), `recompile_vocab`, `refilter_vocab`; kill switch
`TUTOR_NO_VOCAB_COMPILE=1` nos harnesses; `motor_puro.py --com-vocab` = 3a linha da regua.
**Desvios do plano, registrados:** arquivo SEPARADO do manual (o motor puro apaga curadoria e mantem o compilado; recompilar
nunca sobrescreve trabalho humano); chave COM codigo (o glossario chaveia "1.2 Modelos OSI" — sem isso 68 termos gravaram 0
aliases no FR; e sem codigo "3.1 Conceitos basicos" colidia com "5.1", quebrando R8 no SO); filtro de IDENTIDADE (termo igual
ou contido em nome de OUTRA unidade/topico sai — a aula 1 do CG enumera as unidades e 48 materiais foram sugados para u01).
**Limite descoberto:** o compile herda a unidade que o MOTOR deu (CG: Octrees/CSG viraram termos de u02 porque o motor pos
modelagem em u02) — recompilar apos a Fase 2 (cronograma manda) e a saida; `refilter_vocab` reaplica filtros sem chamar.

| regua (02/09) | bloco | unidade | cobertura | subunidade | revisar/100 |
|---|---|---|---|---|---|
| curada + LLM (originais COM vocab, 8) | 199/200 | 191/191 | **55/57** (eth2) | 93/93 | 53,2 (era 55,7) |
| motor puro (sem vocab) | 161/200 | 158/191 | 51/57 | 26/93 · 21 prim. | 54,0 |
| **puro + vocab compilado** | 162/200 | **167/191** | 50/57 | **79/93 · 75 prim.** (IA 35/39, ES2 24/28, TCC 11/11, SO 9/15) | — |

Sidecars compilados: MF 77 termos, CG 77, LR 8, FR 53 (os 4 manuais intactos, 0 campos). CG subunidade taggada 55 -> 63, FR 12 -> 16.
**REGRESSAO (lei: nada regride) — pendente do user:** cobertura 56 -> 55/57: MF `eth2` (referencia GitHub do Eth2.0 em Dafny,
gold u02). A aula 1 cita "Eth2.0 spec" como exemplo de aplicacao -> termo de "1.4 Exemplos de Aplicacoes" (u01), correto pelo
texto; o scorer de unidade empata u01/u02 (0.925 -> 0.483 < gate 0.5) -> cobertura cai no bloco (u01). Mesma excecao ja aceita
no eixo BLOCO ("referencia especifica de Dafny, preco aceito para nao pinar"). Opcoes: teto documentado (como `aws`) ou aliases
compilados so na rota de subunidade. Efeito colateral no FR (sem gold): `tcp-chat-c` u03 -> u05 (card diz U2; o bloco manda; a
janela por topico mudou e o LLM votou enlace — erro estrutural pre-existente, o vocab trocou o erro). **Tutores: 8 sujos com o
vocab aplicado, NAO commitados; 2 snapshots de caracterizacao (FR divisao, MF casos-chave) mudam com o estado sujo.**

**MEDICAO "o que falta para chegar perto de 200"** (artifact "Raio-X da Atribuicao",
https://claude.ai/code/artifact/399626ee-682b-43f8-9987-09c344f6c60f; harness `_harness-2026-09-02/mede_alavancas.py`,
`mede_ordem_secoes.py`, `calibra_revisar.py`):
- 38 erros de bloco no motor puro: **29 tem o bloco certo DENTRO da janela** (o desempate erra, nao a janela); 5 sem janela;
  3 irmaos herdam erro; 1 janela-1 errada. Acerto por metodo: janela-1 96% (102/106), disamb confiante 92% (22/24),
  **disamb flagado 51% (28/55)** = todo o gap. Por fonte: data no arquivo 100%, ordinal 94%, card datado 83%, card sem data 70%.
- SARC repetido (mesmo texto em 2+ blocos da janela): 12/55 flagados (7 erram). 39 tem texto distinto e 20 erram assim mesmo.
- Hipoteses REFUTADAS no gold: serie k -> k-esimo bloco (+5/-10); serie monotonica via DP (+1/-2; so-flagados 0); prova antiga
  -> prep (0; gold b09, prep daria b11); label 1a classe em TODOS (+3/-2).
- Alavancas que ENTRAM (Fase 3, medidas nos 203 golds, so agem onde o desempate esta flagado):
  1. card generico ("Informacoes Gerais") sem janela -> bloco de apresentacao/1a aula, regra irma da meta-generica: **+3/0**.
  2. **ORDEM DAS SECOES do Moodle** (dado coletado: `moodle_pull --dry-run` nos 8, `raw/moodle/sections.json` gravado nos 8
     repos + `_harness-2026-09-02/moodle_sections/`): premissa "secoes seguem o semestre" vale em 44/46 golds de cards sem
     data. Ancoras = cards de CONTEUDO com janela datada (utilitarios — TDE, Informacoes Gerais, Plano, Exercicios de Revisao —
     fora); material sem data herda a faixa do proprio card (irmaos datados) ou fica entre ancoras, encadeado com os outros
     cards sem data: **+7/-1** (SO exemplo-criacao x4, exercicios; MF logica proposicional x2; perde SO laminas-sockets-
     alternativo, gold fora da faixa dos irmaos).
  3. label/titulo com token unico a 1 bloco da janela decide, so flagados: **+2/0**.
  4. **tokens curtos consagrados pelo cronograma no desempate** (`short_vocab_from_topic_labels` sobre labels de sessao +
     topic_text, aplicado a `_toks` do disambiguator nos DOIS lados): a linha do SARC da IA diz "abordagem supervisionada
     k-NN" e `_toks` descarta "k"/"nn" (< 3 chars) — o unico token que separa a semana era invisivel; k-NN caia em b04 por
     "dados/machine/learning" e `exemplo-com-k-nn` dava 0x0. Medido: **+4/-2** (IA k-NN x4, 3 viram CONFIANTES; perde 2
     flagados do ES2 via "api"). Mesma familia da campanha tcp/ip do FR, agora na rota de bloco.
  5. **card do Moodle como documento ordenado** (`contents.json` da API; o export apaga): semana = faixa de blocos com sessao
     no intervalo do label "Semana dd/mm a dd/mm", materiais alinhados as semanas por ordem (monotonico, por fluxo/categoria)
     + tokens, desempate de producao dentro da semana. Medido so nos flagados: **+12/-5** (a tudo: +13/-10 — estrutura nunca
     sobrepoe decisao confiante). Perdas = professor fora de ordem (zips sob a semana errada, enunciado sob label de semana).
     Requisito de produto: importar pela API (`moodle_pull`), nao pelo export. Harness `mede_card_ordenado.py`.
- **REGUA DE MATERIAIS DE AULA (decisao do user 02/09: foco = material de aula 100% sem LLM; referencia e contexto).**
  189 dos 203 golds sao AULA (material-de-aula 88, codigo-professor 59, listas 26, trabalhos 7, gabaritos 4, provas 2, outros 3);
  REF 10; BASE 4 (100%). Escada em AULA, so estrutura + lexico (`_harness-2026-09-02/regua_aula.py`):
  152/189 (80%) -> card generico 155 -> ordem das secoes 162 -> card ordenado 167 -> tokens curtos **171/189 (90,5%)**;
  +3 zips do ES2 que seguem o irmao consertado -> ~174 (92%). Ficam ~15: (a) posicao do professor != gold (MF zips de
  "Provas por Indução" x4 postados sob a semana 1, gold semana 2; ES2 roteiro1-introducao; MF t2) — estrutura NAO sabe
  sem data por material; (b) trabalhos/provas antigas (IA prova-1-2024-02, TCC t1-enunciado, MF t2); (c) janela de 2
  blocos sem sinal (IA analise-exploratoria-ex1, MF introducao b01/b02, MF recursao-respostas); (d) azure, aula-17,
  dafny2, revisao. Flagados/sem bloco em AULA depois da escada: 12 (6/100), 3 errados; erros confiantes 15.
  **Pergunta de definicao que decide os ~5 de (a): o gold de material de aula e "onde o professor postou" (estrutura)
  ou "a aula em que foi usado"? Se e a posicao, (a) deixa de ser erro e a regua sobe para ~95%.**
- **AUDITORIA DO GOLD (pergunta do user: "o gold pode estar errado; Moodle/SARC sao a verdade").** Lado a lado
  posicao do professor (label de semana / data no nome / secao-semana, do `contents.json`) x SARC x gold x motor, nos 189
  golds de AULA (`_harness-2026-09-02/audita_gold.py` -> `auditoria_gold.csv`; artifact "Gold x Moodle x SARC"):
  **concorda 148/148 onde ha posicao datada**; 38 sem posicao datada (SO cards sem data, TCC "Semana N"); **3 divergencias,
  todas defeitos do MOODLE que o gold pegou**: ES2 `roteiro1`/`roteiro1-introducao` sob label "Semana 18/08/2025" (curso
  clonado de 2025, a semana 23-27/03 ficou sem label) e MF `t2-2026-1` sob "Trabalho 1 (06/05/2026)" (label "Trabalho 2:"
  sem data). Nao ha padrao de erro do gold em material de aula. Consequencias: (i) label com ano != ano do curso e ruido
  estrutural detectavel — o leitor do card deve ignora-lo; (ii) onde o Moodle nao opina (38), o gold continua sendo a
  unica verdade alem do texto.
  - Datas em que a cadeira acontece: ja usadas (sessoes do SARC); ordem de postagem NAO segue a ordem das aulas em semanas de
    2 aulas (IA Semana 3, SO Processo): so o topico da linha do SARC separa — dai a alavanca 4.
- **Escada: 165 -> 168 -> 174 -> 176/203; residual 43 flagados (21/100, era 23) -> LLM 69/70 -> ~192; os 3 zips roteiro1/2/4
  seguem o irmao -> ~195/203.** Ficam: dafny2 (confiante em b11, label diria b13), azure (nao dedutivel), aula-17 (numeracao do
  professor != calendario), recursao x2 e arvores/listas (janela de 2-3 blocos sem sinal: so data), e o erro do LLM (~1/70).
- Captura faltante no produto: o import por stash (export do Moodle) nao traz a ordem das secoes; `moodle_pull` traz
  (`sections.json`). Fase 3 precisa persistir o indice da secao (manifest ou `raw/moodle/sections.json`) e o motor ler isso
  como prior de janela.

## FASE 0 — regua oficial + fila `revisar` (2026-09-02, sessao 3)

Plano `2026-09-02-plano-fechar-o-motor.md` Fase 0, os 3 itens feitos. Suite 2201 (+23) · sentinela nos 8 =
so o campo novo `revisar` · regua curada intacta (199/200 · 191/191 · 56/57 · 93/93) · motor puro reproduzido.

**1. Promovidos** (`docs/reports/_harness-2026-09-02/` -> `scripts/`, paths por `__file__`, `main()`):
`scripts/motor_puro.py` (regua oficial do produto: copias nu + voter OFF + 3 eixos + subunidade, 135 s) e
`scripts/censo_motor_llm.py` (motor x LLM por eixo + **revisar por 100** + anatomia dos gatilhos; aceita
`TUTOR_REPOS_DIR` para medir nas copias). Harness novo versionado: `_harness-2026-09-02/calibra_revisar.py`
(gatilho x erro no gold, precisao/recall por eixo — rodar a cada fase, e a regua da fila).

**2. `revisar`** = `src/builder/routing/revisar.py` (`revisar_de`, `motivos_de`; puro, 21 testes em
`tests/test_revisar.py`), gravado por `apply_unit_subunit_fields` em TODO material (inclusive os sem bloco,
que o loop de unidade pula), campo `FileEntry.revisar` (round-trip), vigiado pela sentinela. Decisao B como
especificada: `duvida` = sem bloco em escopo (nao conta bibliografia/referencias/cronograma nem secao TDE) OU
`temporal_block_flag` (inclui llm-funil) OU `unit_block_conflict` OU subunidade `ambiguous`/`empate-exato`
(sem-sinal e revisao-sem-assunto NAO sao duvida — decisao 4) · `llm` = `temporal_block_method == "llm"` ·
`ok` = resto. Pino manual = bloco (o motor limpa os temporal_*).

**3. Baseline oficial (02/09):**

| regua | bloco | unidade | cobertura | subunidade | revisar/100 | votos/100 |
|---|---|---|---|---|---|---|
| curada + LLM (8 cursos, 325 mat.) | 199/200 | 191/191 | 56/57 | 93/93 | **55.7** (duvida 113 + llm 68) | 33.5 |
| motor puro (5 c/ gold, 226 mat.) | 161/200 conf-err 3 | 158/191 | 51/57 F1 0,895 | 26/93 · 21/93 prim. | **54.0** (duvida 122 + llm 0) | 0 |

Por curso (curada): MF 62 · SO 59 · IA 34 · ES2 66 · TCC 41 · CG 66 · LR 67 · FR 55. Anatomia da duvida nos 8
(um material pode ter >1): conflito 61 · sub-empate 31 · flag:janela-1 24 · flag:llm-funil 18 · sub-ambigua 16 ·
sem-bloco 0 · flag:due-straddle 1. Motor puro 161 = 158 do 01/09d + meta-generica (4 nas copias).

**Calibracao dos gatilhos (motor puro, gold dos 5) — o dado que valida a decisao B:**

| gatilho | n | erro real | precisao | bloco/unid/sub errados |
|---|---|---|---|---|
| sem-bloco | 5 | 5 | **100%** | 4/3/1 |
| flag:disamb | 57 | 36 | **63%** | 28/16/21 |
| sub-empate | 14 | 8 | 57% | 2/1/6 |
| conflito | 39 | 22 | **56%** | 3/10/13 |
| flag:janela-1 | 11 | 3 | 27% | 0/3/0 |
| sub-ambigua | 9 | 2 | 22% | 2/0/0 |
| flag:due-straddle | 1 | 0 | 0% | — |

Recall (erro real -> camada): bloco 32/39 em duvida, **7 escapam como ok** (`exerciciosdafny2`, IA `prova-1-
2024-02` = prova antiga, ES2 `roteiro1/2/4` + `azure` = serie numerada, TCC `aula-17`) — todos alvos ja
listados da Fase 3 · unidade 27/33 (6 escapam, os mesmos do ES2) · **subunidade 35/67: 32 escapam** (IA
perceptron/mlp/k-means/agrupamento…: confiante-errado ou sem-sinal por falta de vocabulario = Fase 1b).
Na regua CURADA a calibracao e cega (1 erro de bloco, 0 de unidade/subunidade): conflito 34 -> 1 erro. Ou
seja, conflito e sinal REAL so enquanto o bloco erra; quando a Fase 3 subir o bloco, a precisao do conflito
cai e ele vira ruido de 20% da fila — remedir entao, nao agora.
`flag:janela-1` (27%) e `sub-ambigua` (22%) sao os gatilhos fracos; janela-1 NUNCA vota (D4), entao a flag
dele nao tem quem a limpe — candidato a sair da fila quando houver dado da run real do FR.

**Bug de raiz achado no caminho:** `SubjectStore.find_by_repo_root` comparava string — `reprocess_assignments.py
../X-Tutor` nao achava o perfil, o plano parseava 0 unidades e `UnitsShrinkError` abortava a rodada (o MF
ficou com manifest parcial; restaurado do HEAD). Fix: `Path.resolve` nos dois lados (`_norm_repo_root`,
`tests/test_subject_store_repo_root.py`).

**Divida achada (nao mexida):** no reprocess dos 8 com manifest IDENTICO (sentinela 0 fora de `revisar`), o `course/COURSE_MAP.md` do ES2 reordenou a lista "Tambem cobre esta unidade" (`Roteiro2_nameserver` (+12) -> `roteiro2` (+13); `Roteiro1_introducao` perdeu o (+1)) — nao-determinismo do RENDERER (ordem de empate/set), nao do motor. Entra no corte 1 do refactor: ordenar por chave estavel e cobrir com teste de determinismo.

**Proximo:** Fase 1b (`compile_course_vocabulary`) — handoff `_archive/2026-09-02-handoff-executar-plano.md` §Fase 1b.

## PENDENCIAS ANTIGAS AINDA ABERTAS (triagem 03/09; detalhe no historico `_archive/pendencias-historico-ate-2026-09-02.md`)

Do "RESUMO 01/09b — DECISOES DO USER", o que NAO fechou: (1) P2b-LLM (extracao de questoes de provas; ruling "deterministico
agora, LLM depois") — entra em "imagens e provas" depois da fila do motor; (2) Lab SO BLOQUEADO (SARC da turma 310) + triagem
dos achados de P3; (3) GAP VIDEO do T2; (4) triagem dos 10 suspeitos SEM-GOLD do `detecta_headings`; (5) pino de cobertura
p/ 57/57 (mecanismo nao existe; ligado a decisao B eth2/aws); (7) merge em main / push (nada pushed desde 01/09).
FECHOU: (6) gold de bloco do CG — `ground_truth_CG.csv` 03/09 (35 scorable, motor 34/35).

**Resgatadas do historico em 03/09 (varredura por [USER]/[DECISION]/BLOQUEADO/aguardando; so o que ainda vale), por dono na fila:**
- **Item 8 (rebuild CG/LR/FR pela API) — pre-requisitos do CG:** (a) **CG publica `.htm` (sem L)** e `stash_import._classify_file_type`
  nao conhece a extensao: arquivo cai em `skipped` e a UI mostra so a CONTAGEM ("N ignorado(s) por extensao"), nunca os
  nomes — material some sem ninguem saber qual (user 25/08; **ainda sem `htm` no codigo em 03/09**). Fix = extensao + listar
  nomes. (b) **"modals" do CG** — forma de material que nao sabemos o que e tecnicamente (janela modal? conteudo por JS?);
  investigar so quando CG entrar de verdade (adiado pelo user 25/08). (c) **"Em duvida 28/08" das 3 cadeiras novas, nunca
  triado:** `_NOT_MAIN_EXAM` trata "Prova PS"/"Prova G2" como principais (FR teria 4; a formula do G1 diz 2 — ler os termos
  do plano); cadeira sem prova: marco = entrega ("Fechamento da parte N", "Apresentacao do T1"), `_exam_number`/prep-prova/R6
  so entendem P; provedor de unidade-no-card (`U1 - ...`) e ordinal "Laboratorio N"/"Tutorial 1.2" (a Fase 3b encosta nisso);
  identidade de curso = Moodle id + codigo SARC (98709 vs 98710), nunca nome; plano do Lab SO sem avaliacao: unica fonte e o
  `summary` de secao do Moodle (a Fase 3a passa a ler `sections.json`); Lab Redes ~10 blocos de conteudo em 19 sessoes = regua magra.
- **"Depois: referencias" — gold JA EXISTE, aguardando veto:** `coverage_gt_{SO,MF,IA}.csv`, 9/10 preenchidos (SO 3/3 pelo
  plano de ensino; MF 3/3 e IA 3/3 `proposto-claude`: MF1=1,2 · MF2=1,2 · MF3=1 · IA1=1 · IA2=1 · IA3=5; IA4 fantasma = skip).
  Baseline medido em 18/08: 0/9 exact-set, 8/9 sem predicao nenhuma. Junto com a decisao 22/07 "bibliografia = caso a parte"
  e a decisao B (eth2/aws).
- **"Depois: imagens e provas":** alem de P2b-LLM, a [DECISION] **granularidade da cobertura de avaliacoes** (prova inteira
  com um conjunto de topicos, barato e deterministico, x questao a questao, caro/LLM, que e o que o header do EXAM_INDEX ja
  promete "incidencia por topico") — perguntada 18/08, sem ruling.
- **Residual de bloco na curada (para a Fase 4, LLM contado):** ES2 27/28 (1 off-by-one nao confiante; `azure`, PDF de 877k
  chars sobre cloud, hoje metodo `llm`); SO `exemplo-threads` x3 e IA `Cap. Algoritmos Geneticos` FECHARAM (SO 38/38, IA 43/43 em 03/09).
FECHADOS na varredura (nao voltam): sujeira pre-existente em ES2/IA (0 entradas sujas em 03/09; decisao A commitou os 8);
branch `feat/block-stable-id` (ja mergeada em HEAD); subunidade IA "6 residuais teto" (Fase 1b, 93/93); card_block_map do MF
"Verificacao de Programas" (morta 08/07); bloco-15/bloco-12x13 do IA (junho; IA 43/43 hoje); gold IA congelado / xlsx stale /
102 suspeitas soft (superados pela auditoria gold x Moodle x SARC de 02/09, 148/148); rollout flag-ON TCC/SO (cutover 17/08).
**Decisoes DURAVEIS que estavam so no historico e nao em `.mex/context/decisions.md`** (mover quando quiser, nao e pendencia):
dedup por CONTEUDO (md5), nunca por basename/id (23/06); regra "2 aulas = 1 bloco" aposentada (bloco = unidade pedagogica);
bibliografia = caso a parte (22/07); `covered_units` lista p/ avaliacao/entrega (08/08); tratamento estrutural PS/G2 (08/08);
modo nao-monotonico por curso descartado (ruling T11); span-cap de over-merge refutado (22/06).
Tudo o mais abaixo de FASE 0 no arquivo antigo (MOTOR PURO, TOKENS CURTOS, DISSECACOES, campanhas 1-3, Plano B, auditorias)
esta executado ou superado pela SEQUENCIA ACORDADA; le o historico so para "por que" de uma regra.

## CAMPANHA FUTURA (produto) — web local + camada LLM por conta [BACKLOG VIVO]

Decisão do user 2026-08-11: campanha própria, DEPOIS da campanha 3 (cutover — motor
estável antes de produto). Backlog ABERTO: o user vai adicionando ideias com o tempo
(minerar DeepTutor e spec "Nexo" do amigo como referências). Princípio acordado nas
discussões: manter o motor de compreensão (compile-time, medido) e trocar só
VITRINE e CUSTO — nada de migrar pra catalogação+LLM-runtime.

- [DECISION] **Painel web local** (substitui a GUI Python como cara do sistema; motor
  já é headless, zero mudança nele). Fase A read-only: "minha semana" cross-curso
  agregando os 5 `.timeline_index.json`, avaliações cronológicas com escopo
  (covered_units quando existir), materiais com estado lido/catalogado/não-extraído,
  badge de freshness (`check_sarc_freshness` como status), download `.ics` (assessments
  já têm data+escopo nos índices). Fase B: curadoria na web (pinos, overrides,
  reprocess gated com preview) — aposenta a GUI Python de vez.
- [DECISION] **Camada LLM por conta (não API)**: bridge HTTP local → CLI autenticado
  (padrão Nexo/Codex, mas provider-agnóstico). COMEÇAR COM 1 provider (YAGNI no
  multi). DOIS usos: (a) chat tutor lendo os artefatos/índices locais; (b) **EXTRAÇÃO
  PDF→markdown multimodal** — transcreve LaTeX de verdade e DESCREVE figuras (dor real
  do user com Marker offline), one-shot por material, revisável, gate de qualidade
  barato (headings/fórmulas contadas + diff). **Mata o Datalab** (único custo pago
  recorrente do pipeline). Teto do design: quota da assinatura compartilhada entre
  extração e chat.
- [DECISION] **Modo Projects por provedor**: repo-tutor como KB de Claude Projects
  (GitHub linkado) / GPT custom — já é o padrão atual com ChatGPT; custo ~zero, é
  apontar o Project pro repo. Item = documentar/otimizar artefatos pro formato de KB
  de cada provedor (tamanho, granularidade).
- [DECISION] **Coleta Moodle assistida** (API local sobre a sessão logada, "como o
  usuário clicando", estilo Nexo) como fonte UPSTREAM de ingestão: material novo →
  staging → motor atribui como sempre. Read-only estrito. Riscos registrados:
  fragilidade de seletores a cada mudança de layout, termos de uso institucionais.
  Complementa (não substitui) o SARC público já automatizado.
- [USER] **Backlog aberto de ideias de produto** — user adiciona aqui conforme surgir
  (DeepTutor: UI de estudo + KB local; Nexo: .ics, estados de leitura, status de sync
  por fonte — os dois já parcialmente absorvidos nos itens acima).
  Ideias adicionadas 2026-08-11:
  - **Visão de grafo estilo Obsidian**: unidades/subunidades/blocos/materiais/provas
    como grafo navegável, atualização em tempo real. Base já existe: os índices são
    relacionais (bloco→unidade, material→bloco, prova→escopo) e
    `computed_subunit_slug` é a semente de subunidades (item DECISION próprio).
  - **Question Banks**: junção de exercícios + trabalhos + provas por
    unidade/subunidade. Base: assessments/exercises já catalogados nos manifests;
    liga com covered_units (escopo por prova).
  - **Memória em camadas com proveniência** (DeepTutor: "L1 traces, L2 surface
    summaries, L3 synthesis" + Memory Graph): personalização visível e EDITÁVEL,
    cada claim rastreável à evidência — casa com nossa disciplina de
    gold/proveniência (URLs de origem, bands, notes).
  - **Grouped Workspaces com instruções persistentes por grupo** (DeepTutor):
    workspace por disciplina/tema com custom instructions próprias.
  - **Living Books** (DeepTutor): "livro vivo" gerado dos materiais do curso,
    reorganizado por unidade/subunidade, atualizado quando material novo chega.
  - **Settings — one control plane**: config única (providers LLM, quotas, fontes,
    flags por curso) — hoje espalhado em subjects.json/feature_flags/scripts.
  - **ManimCat / vídeos Manim**: geração de visuais matemáticos (dual-mode AI
    workspace) — candidato natural pra MF/TCC (LaTeX/provas formais).
  - **Dashboard como home**: atividades a entregar, próximas aulas com horário e
    SALA/LABORATÓRIO (fonte: SARC e **OpenSarc** — registrar OpenSarc como fonte
    nova a integrar), relógio/dia/data em tempo real, uso/quota das LLMs.
  - **Agenda da semana sincronizada com Google Agenda**: além do .ics estático —
    sync (push) do calendário acadêmico.
  Ideias adicionadas 2026-08-11 (2ª leva):
  - **Página de health**: status úteis em um lugar — LLM/bridge offline, dependência
    faltando (Node, CLI, pacotes), freshness por curso, quota/uso, último build por
    repo. Herda os gates CLI (verify_units, check_sarc_freshness) como widgets.
  - **Upload de arquivos pela web**: ingestão de material direto na UI local
    (drag-and-drop → staging → motor processa gated como sempre) — substitui o fluxo
    manual de copiar arquivo pra pasta.
  - **Limpeza/simplificação dos dados por arquivo** [CODE, pós-cutover]: auditoria de
    CONSUMO real dos campos de manifest/índice (quem lê o quê — grep de consumidores
    por campo) e poda do que ninguém usa; junta com a poda de artefatos .md por repo
    (COURSE_MAP/FILE_MAP/GLOSSARY/...) já nomeada como gordura na discussão de
    overengineering. Regra: podar SÓ com auditoria de consumo, campo a campo.
  - **Distribuição: PyPI e/ou Docker** (modelo DeepTutor): `pip install` → web app
    completa + CLI sem clone (`tutor start` spawna o Next.js standalone; requer
    Python 3.11–3.13 + Node 20+ no PATH) e/ou container único com imagens no GHCR.
  Ideias da leitura do repo DeepTutor (HKUDS, 2026-08-11 — CC leu features/arquitetura):
  - **Bake-off de engines de parsing** (refina o item extração): DeepTutor pluga
    MinerU/Docling/markitdown/PyMuPDF4LLM — MinerU e Docling são locais, open-source
    e fortes em fórmula→LaTeX e layout acadêmico (a dor real do user com Marker).
    Bake-off nos 164 PDFs: MinerU vs Docling vs CLI-multimodal-por-conta vs Datalab;
    medir taxa de LaTeX correto + descrição de imagem. Datalab vira último fallback.
  - **Export vault Obsidian** — REBAIXADO a bônus opcional (ruling user 2026-08-11:
    grafo tem que ser NA WEB, pra quem não usa Obsidian). Item grafo atualizado:
    página de grafo no PAINEL com lib pronta (Cytoscape.js/force-graph — commodity,
    1 componente lendo o JSON relacional dos índices); interatividade rica (filtros,
    painéis, tempo real) incremental depois. Vault Obsidian = ~1 script sobre o mesmo
    JSON, se sobrar vontade.
  - **Citação por página** (padrão PageIndex): resumos/artefatos do tutor citarem
    página exata do PDF de origem — extensão natural da nossa disciplina de
    proveniência (URLs, bands, notes).
  - **Segurança no upload web** (anexo ao item upload): herdar os gates do DeepTutor
    — extração defensiva (zip-slip/zip-bomb), whitelist de sufixos, limites de
    tamanho configuráveis.
  - **Índice versionado leve** (padrão version-N imutável): formalizar o protocolo de
    snapshot das campanhas como versionamento do reprocess (re-index nunca destrói o
    índice ativo; rollback = trocar ponteiro). Nossos snapshots+git cobrem 90% —
    item só formaliza.
  - **Tutor como CLI agent-native**: expor consulta ao acervo como comando com saída
    JSON/NDJSON e session_id — outros agentes (Claude Code etc.) consultam o motor
    como ferramenta. Barato: os dados já são JSON.
  - Notas menores: thinking-model routing por tarefa na bridge (modelo barato pra
    extração, forte pra síntese); bounded caches/hot-reload quando o painel existir;
    Mastery Path (aprendizado adaptativo) como ideia distante de produto.
  - **DESCARTADOS de propósito** (peso de produto público, caso nosso é 1 usuário
    local): multi-user/auth, 15 canais IM, skill hubs/marketplace, partners/personas,
    MCP services store.
  - [DECISION] **Frameworks RAG (LlamaIndex/LightRAG/GraphRAG/PageIndex) — AVALIADOS
    E ADIADOS (2026-08-11)**: retrieval do chat já resolvido 2x (Projects = RAG do
    provedor; bridge CLI = retrieval agentic sobre índices estruturados); o motor JÁ
    é retrieval especializado com régua (chunking vetorial achataria a estrutura
    temporal/curricular; GraphRAG reconstruiria por LLM, sem régua, o grafo que temos
    determinístico); custo = subsistema novo (vector store+embeddings+versão).
    GATILHO de reavaliação: busca lexical acento-insensível do painel medir MAL em
    sinônimos ("onde vi isso?" cross-curso) → adotar embedding local PONTUAL
    (ollama/BM25+expansão), nunca o framework inteiro.
    PRÉ-REQUISITO técnico: separar CÓDIGO de DADOS/CONFIG — hoje paths dos
    repos-tutor/subjects.json são locais e acoplados; empacotar exige o "Settings —
    one control plane" (config única apontando pros dados do usuário) e garantir que
    NENHUM dado pessoal/material de curso vai dentro do pacote/imagem.
