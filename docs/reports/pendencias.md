# Pendências — tracker vivo

last_updated: 2026-09-05 (sessao 5, madrugada; C0 FECHADA 11/11; C1 itens 1 e 2 FEITOS; Gemini sem credito). **Ponto de entrada = handoff `2026-09-04-handoff-fila-campanhas.md`** (regra
de fila do user: UMA campanha aberta, UMA proxima, o resto estacionado com "pronto quando"; anteriores em `_archive/`).
**Criterio estrito (user, 03/09 tarde): campanha so fecha com 100% dos itens.** Balanco: **C0 MOTOR 11/11 FECHADA em 05/09** (§C0 ITEM 12, 9, 10, 11a, 11b);
**SYNC 6/6 FECHADA em 04/09** (S6f promovido + complemento: CG `e3d02ed`, 93 entries; holdout puro 31/35, curado 33/35 aceito pelo user com causa medida; §SYNC S6f).
**FILA:** 1 ABERTA = **C1 TRAVESSIA** (FILE_MAP completo e magro; entrada = §C0 ITEM 12) · 2 PROXIMA = C3 provas/listas (ordem registrada; posicao da C7 e decisao do user na fronteira) · estacionadas: C7 imagens ·
C2 bibliografia · C4 limpa · C5 dividas de dados · C6 web. Ideias novas vao para a CAIXA DE IDEIAS do handoff.
Numeros vivos: §GATE DA FASE 3, §HOLDOUT, §REGUA DE TRAVESSIA. Tracker CORTADO em 03/09: historico (MOTOR PURO ate campanhas 1-3,
4.8k linhas) em `_archive/pendencias-historico-ate-2026-09-02.md`; aqui so o vivo. Documentos vivos = este + handoff 2026-09-03b +
plano 2026-09-02 (desenho/decisoes, carimbado).

## AUDITORIA GOLD x MOODLE/SARC (05/09 madrugada, sem LLM; regra do user: SARC e Moodle sao o oraculo, gold e humano)
**Metodo:** para cada linha pontuavel dos 5 golds, o bloco do gold cai na `moodle_week_label` do card? 203 linhas, 82 com semana (MF, ES2; SO/IA/TCC
sem o campo), **27 "fora" — todas explicadas: a semana e da SECAO, nao do material**, e as secoes abrangem varias semanas (MF "Verificacao de Programas"
24 materiais nos blocos 11-15; MF "Provas por Inducao" blocos 04-06; ES2 "Microsservicos" blocos 07-10). Nenhuma contradicao gold x Moodle.
**Retratacao (minha leitura de 05/09 ~02h):** eu disse que os `.thy` do MF eram do bloco-05 pela "semana 30/03-03/04"; essa semana e da secao inteira,
que abrange 3 blocos. O gold (bloco-06, aula de Isabelle) fica. O erro do motor nesses 5 e a JANELA DO CARD = 1 sessao casada pelo label, quando a
secao cobre 3 blocos — alavanca ja na caixa, agora com dado: 3 secoes multi-semana concentram 24+11+9 materiais e 8 dos 17 erros do motor puro.
**Casos decididos (user 05/09):** IA `prova-1-2024-02` = prova antiga 2024/2 -> gold `scorable=no`, pino manual removido do original, reprocess
(IA `d7d81ed`; sem credito o voter nao votou e ficou sem bloco — com credito voltaria a votar como prova/trabalho sem prazo: registrar se o user quer
"prova antiga nunca vota"). MF `exerciciosdafny2`: gold 13 CONFIRMADO pelo SARC (sessao "colecoes dafny arrays" = label do Moodle "arrays no Dafny");
bloco-11 nao tem Dafny. MF `revisao`: gold 03 consistente com a sessao "revisao de logica de predicados". TCC `aula-17-np-completude`: SARC tem
"np complete" no bloco-19 (motor) e Cook-Levin no 22 (gold); postado 22/05 — ambiguo, gold mantido, decisao do user. ES2 `azure`: imagens (C7).
**Alavanca medida e REFUTADA:** peso do label do Moodle no desempate lexical (tokens de titulo+label x2/x3): 58 entries disamb com gold, acerto
50 -> 47 (x2) / 48 (x3) — conserta `dafny2` e `analise-exploratoria` mas quebra 4 exemplos k-NN do IA. Nao entra.

## MEDICAO — OS 17 ERROS DO MOTOR PURO (183/200) E O 1 DA CURADA (05/09 madrugada, sem LLM; pergunta do user "como chegar a 200?")
**200 = tamanho do gold pontuavel** (MF 66, SO 38, IA 43, ES2 28, TCC 25; pares colapsados), nao o total de materiais (226 nos 5 cursos). 200/200 e 100% do gold,
e o gold e amostra humana, nao oraculo. Os 17 do motor puro: 7 flagados (duvida honesta; no produto o voter resolve), 2 sem bloco (prova/trabalho sem
prazo casado), 6 confiantes errados, 2 fora de AULA (REF 8/10). Dissecados (`c1-2/`, read-only):
- **MF `revisao`** (card "Revisao - Logica e Especificacao", janela [03, 04]): texto casa {conjuntos, especificacao} so no 04; gold 03. Revisao que cobre os
  dois blocos e o gold escolhe o primeiro — sem regra sem virar categoria.
- **MF `exerciciosdafny2`** (janela 5 por labels): texto casa {correcao, invariantes, laco, total} no bloco-11 (teoria) x {arrays, dafny} no 13 (gold). O
  vocabulario do exercicio e o da teoria, nao o da aula em que foi dado; o voter acerta (serie, 11b). Serie monotonica ja refutada no gold.
- **MF `arvores`, `intro`, `listas`** (`.thy` = Isabelle; card "Provas por Inducao", janela-1 = bloco-05 porque o label do card casa a sessao "provas por
  inducao aula"): gold bloco-06 "prova interativa de teoremas isabelle". O card NAO esta no `card_block_map` e abrange 3 blocos pelo gold (04: 8 materiais,
  05: 4, 06: 7). Alavanca candidata, nao medida em codigo: token de ferramenta pela extensao (`.thy` -> isabelle, `.dfy` -> dafny) + janela do card = blocos
  das sessoes que o label casa E os seguintes ate o proximo card — exige desenho; **caixa (C0-2)**.
- **TCC `aula-17-np-completude`** (ordinal "aula 17" -> 17o bloco = 19; gold 22 "Cook-Levin"): o numero da aula do professor deriva do calendario
  (feriados/adiamentos). Card "Semana 12": semana do card == semana do bloco gold em **17/26** materiais do TCC (65%; deslocamentos +2) — "Semana N" sem
  data nao e sinal confiavel; IA tem "Semana N" com datas (54/54) e ja usa o card datado.
- **ES2 `azure`** (o 1 erro da curada; card "Microsservicos" -> janela-1 bloco-08, gold 09): o markdown do deck e so hash de imagem, sem texto — o
  motor nao tem sinal e o LLM chutou igual. **Causa = imagens sem descricao -> C7 IMAGENS (Datalab para imagens).**
**Conclusao:** nenhuma alavanca estrutural com numero hoje; 200 no motor puro nao e meta (teto estrutura+texto ~190-193). Metas honestas: conf-err 0 no
puro (hoje 2, ambos lexico), flagados pequenos (45/189 puro, 15/189 produto), curada 200 (falta 1 = imagens).

## C1 ITEM 2 — LABEL DE BLOCO DUPLICADO NO CRONOGRAMA (05/09 madrugada, MEDIDO sem LLM; **FEITO: as 2 propostas entraram**)
**Medido nos 8 (`c1-2/`):** 6 cursos tem blocos-AULA com o mesmo `primary_topic_label`: 7 labels, 16 blocos, **33 materiais** ancorados neles
(MF 5 "Verificacao de modelos" x2 · SO 6 "Paginacao" x2 · ES2 17 "Estudo de caso: integracao..." x4 · FR 5 "Modelos OSI e TCP/IP" x2 + "Enderecamento" x2 ·
TCC "Correcao" x2 e LR "Desenvolvimento" x2 sem materiais). Em 5 das 7 colisoes o `topic_text`/sessoes diferem (qualificador disponivel); em SO/TCC/LR
o texto e igual e so a data distingue. **O que o tutor le para o "quando"** e o `CRONOGRAMA_DETALHADO.md` (`## <periodo> — <label>`): titulos repetidos
de conteudo em MF 1, SO 1, ES2 1, FR 2 (alem de feriado/duvidas/trabalho/evento, repeticoes legitimas). Foi isso que fez o flip "osi tcp ip" do item 12
(bloco-20 em vez de 02) — sumiu no item 1 com o FILE_MAP completo, por sorte do LLM, nao por estrutura.
**Raiz da colisao do FR (medida):** a taxonomia do plano da ao topico "Modelos OSI e TCP/IP" os aliases de TODAS as camadas ("Camada de Transporte",
"Camada de Enlace", "Camada Fisica"...; sub-itens do 1.2). Bloco-06 (`topic_text` "camada transporte", sessoes "camada de transporte udp tcp") pontua
1,0 nesse topico e so 0,14 em "Funcoes e caracteristicas do nivel de transporte" (unidade 3); bloco-22 ("camada fisica sockets") idem; bloco-20 (enlace)
cai em "Enderecamento" 1,0 x "Protocolos de enlace (Ethernet)" 0,13. O matcher bloco->topico (`_score_entry_against_taxonomy_topic`) e absorvido por
aliases genericos — corrigir exige gold de topico (nao existe): **caixa**, com esta evidencia.
**Achado colateral (bug):** `CRONOGRAMA_DETALHADO.md` so e gravado dentro de `if code_entries:` (`pedagogical_regeneration.py`) — **TCC e LR nao tem o
artefato** (35 e 17 blocos com data, 0 code entries na lista). O "quando" desses cursos so existe na coluna Periodo do FILE_MAP.
**Propostas (sem codigo ainda; a regua do "quando" exige LLM, creditos esgotados):** (a) qualificar o titulo do bloco no CRONOGRAMA_DETALHADO so em
colisao, com o `topic_text` humanizado ou a 1a sessao ("Modelos OSI e TCP/IP · camada transporte"), deterministico, 16 blocos em 6 cursos, byte-identico
no resto; (b) mover a escrita do CRONOGRAMA_DETALHADO para fora do `if code_entries` (TCC e LR ganham o artefato). Gate: suite, sentinela 0, determinismo;
efeito no "quando" medido na travessia quando houver credito.
**FEITO (gerador `333d635`, reprocess registrado `c1-2/reprocess_c1_2.py`):** MF `62a73ea` · SO `0921948` · IA `3f549bf` · ES2 `ba7d2c8` · TCC `d9126af` · LR `d139547` · FR `fd7814f` · CG `0986874`. CRONOGRAMA_DETALHADO por tutor: MF 23 blocos, 2 qualificados · SO 27 blocos, 2 qualificados · IA 24 blocos, 0 qualificados · ES2 15 blocos, 4 qualificados · TCC 35 blocos, 2 qualificados · LR 17 blocos, 2 qualificados · FR 30 blocos, 4 qualificados · CG 29 blocos, 0 qualificados. Manifest intocado; sentinela 0/8; determinismo 8/8 (0 arquivos nao deterministicos); suite 2322 (2 testes RED/GREEN). Medicao do "quando" na travessia: pendente de credito Gemini.

## C1 ITEM 1 — FILE_MAP COMPLETO E MAGRO (05/09 madrugada, FEITO E REGISTRADO NOS 8)
Gerador `0ff832a` (renderer) · `4db9a6c` (harness da travessia) · `df0e34f` (watchdog do censo) · `6afdcff` (titulo com `|`). **Medido antes
(passo 1, `c1-1/simula_filemap_c1.py`):** cada material ocupava 2 linhas (tabela ~250 chars + "↳ rastreabilidade" ~230); com o clamp de 12 KB
cabiam 20-30 (CG 26/93, IA 22/59, MF 31/66); sem clamp o formato antigo ia de 5,5 KB (LR) a 42,5 KB (CG); "magro" projetado 3-21 KB. Das 157
Secoes renderizadas, 62 passavam de 80 chars (max 321). `moodle_label` preenchido em 288/348 (FR 0/22); `title` = nome de arquivo em MF 57,
ES2 35, CG 69 — titulo = label muda 211/348 linhas.
**Regra (TDD, 7 testes novos + 3 antigos movidos):** teto 12 KB -> 80 KB (`FILE_MAP_MAX_CHARS`, aviso do clamp mantido) · rastreabilidade
(raw, tags, markdown-base, pinos) sai para `course/FILE_MAP_TRACE.md`, mesma numeracao, sem clamp · titulo = `moodle_label` (fallback `title`;
`inferred_title` da curadoria de codigo continua acima) · Secoes <= 3 headers / 80 chars · `|` no titulo vira `/` (IA "O que e IA? | Oracle
Brasil" deslocava 10 colunas). Escritores (`build_workflow`, `pedagogical_regeneration`) gravam o TRACE; README do tutor lista o arquivo.
**Originais (reprocess registrado `c1-1/reprocess_c1.py`):** MF `acbfdc2` · SO `7c91082` · IA `1c2869a` · ES2 `ac3862c` · TCC `6d04f4e` · LR `42cdb8a` · FR `ca7f9fd` · CG `0136790`. Manifest intocado (0 flags, 0 blocos): MF 66 linhas 18.6 KB (+ TRACE 11.3 KB) · SO 38 linhas 12.2 KB (+ TRACE 7.1 KB) · IA 59 linhas 20.5 KB (+ TRACE 12.2 KB) · ES2 35 linhas 11.9 KB (+ TRACE 6.1 KB) · TCC 25 linhas 10.4 KB (+ TRACE 6.1 KB) · LR 7 linhas 3.6 KB (+ TRACE 2.1 KB) · FR 22 linhas 7.3 KB (+ TRACE 5.1 KB) · CG 93 linhas 21.3 KB (+ TRACE 21.8 KB). Watchdog
`cobertura_indices` (censo): FILE_MAP MF 66/66 · SO 38/39 (`programa` = duplicata excluida) · IA 59/59 · ES2 35/35 · TCC 27/27 · CG 93/93 · LR 7/7 · FR 22/22.
Sentinela 0/8 · determinismo 8/8 (0 arquivos nao deterministicos) · suite 2319. Reprocess final com a correcao do `|`: so o IA mudou (2 linhas); os outros 7 commits
sao `updated_at` do manifest (ruido de timestamp — caixa: reprocess registrado nao commitar quando so o updated_at muda). Medicao que dependia da linha "↳": harness `filemap_rows` e watchdog passaram a ler o TRACE pelo numero e o label.
**Regua da C1 — travessia antes (item 12, 05/09) -> depois (FILE_MAP completo), mesma regua, ~90 chamadas Gemini:**

curso modo          | hit@1 antes->depois    hit@3          bloco        | estrut  ambig  malf   | chamadas
FR    sem-llm       |  9/15 ->  9/15          11 -> 11       5/6 -> 5/6   | 4->4   2->2   3->3   | 0
FR    llm           | 15/15 -> 15/15          15 -> 15       6/6 -> 6/6   | 5->5   5->5   5->5   | 15
FR    llm-completo  | 15/15 -> 15/15          15 -> 15       5/6 -> 6/6   | 5->5   5->5   5->5   | 15
IA    sem-llm       | 10/15 -> 10/15          12 -> 12       6/8 -> 6/8   | 4->4   1->1   5->5   | 0
IA    llm           |  9/15 -> 14/15          10 -> 14       8/8 -> 8/8   | 3->5   2->4   4->5   | 15
IA    llm-completo  | 10/15 -> 13/15          10 -> 15       8/8 -> 8/8   | 3->5   2->3   5->5   | 15
CG    sem-llm       |  5/15 ->  5/15           6 ->  6     10/11 -> 10/11  | 4->4   0->0   1->1   | 0
CG    llm           |  7/15 -> 10/15           7 -> 13      8/11 -> 9/11  | 2->3   3->5   2->2   | 15
CG    llm-completo  |  7/15 -> 11/15           8 -> 14      7/11 -> 9/11  | 2->3   3->5   2->3   | 15

Flips por pergunta:
flip + [estruturada] 'Como funciona o algoritmo k-NN para classificação e como e' esperado=['algoritmo-de-classificacao-k-nn'] antes=['exemplo-2-k-nn-com-iriscsv-mais-completo', 'exemplo-com-k-nn'] depois=['algoritmo-de-classificacao-k-nn', 'exemplo-com-k-nn']
flip + [estruturada] 'Qual a diferença entre acurácia, precisão, recall e F1, e ' esperado=['como-analisar-resultados-acc-pr-re-e-f1'] antes=['arvores-de-decisao', 'mlp'] depois=['como-analisar-resultados-acc-pr-re-e-f1']
flip + [ambigua] 'tem algum código de rede neural pra eu me basear?' esperado=['mlp-classificacao-iris-atualizado', 'mlp-regressao-cardio', 'mlp-xoripynb', 'rede-perceptron-exemplo-atualizado', 'xor-backpropagation-em-python'] antes=['exercicio-2-solucao-com-rede-perceptron-atualizado', 'mlp'] depois=['mlp-classificacao-iris-atualizado', 'exercicio-2-solucao-com-rede-perceptron-atualizado']
flip + [ambigua] 'o que cai na P2?' esperado=['lista-de-exercicios-i', 'p2-202401', 'p2-202402'] antes=[] depois=['p2-202402', 'p2-202401']
flip + [malformada] 'perceptron letras' esperado=['rede-perceptron-reconhecendo-letras'] antes=['exercicio-2-solucao-com-rede-perceptron-atualizado', 'rede-perceptron-reconhecendo-letras'] depois=['rede-perceptron-reconhecendo-letras']
flip + [estruturada] 'Como funciona o algoritmo k-NN para classificação e como e' esperado=['algoritmo-de-classificacao-k-nn'] antes=['exemplo-com-k-nn', 'exemplo-2-k-nn-com-iriscsv-mais-completo'] depois=['algoritmo-de-classificacao-k-nn', 'exemplo-com-k-nn']
flip + [estruturada] 'Qual a diferença entre acurácia, precisão, recall e F1, e ' esperado=['como-analisar-resultados-acc-pr-re-e-f1'] antes=['arvores-de-decisao'] depois=['como-analisar-resultados-acc-pr-re-e-f1']
flip + [ambigua] 'o que cai na P2?' esperado=['lista-de-exercicios-i', 'p2-202401', 'p2-202402'] antes=[] depois=['p2-202402', 'p2-202401']
flip + [estruturada] 'Como funciona o algoritmo de recorte de retas de Cohen-Sut' esperado=['pagina-com-videos-sobre-recorte-e257d3', 'recorte', 'video-sobre-o-algoritmo-de-recorte-por-subdivisao-binaria-db7e2e', 'vis2d'] antes=['maptextures'] depois=['pagina-com-videos-sobre-recorte-e257d3']
flip + [estruturada] 'Como detectar colisão entre dois objetos usando envelopes ' esperado=['colisao', 'videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84'] antes=['opengl-cpp', 'opengl3dcpp-vdi'] depois=['colisao', 'videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84']
flip - [estruturada] 'Como funciona o algoritmo Z-Buffer para remoção de element' esperado=['elemoculto', 'exemplozbuffer'] antes=['elemoculto', 'exemplozbuffer'] depois=['colisao', 'exemplozbuffer']
flip + [ambigua] 'tem exercício de imagem?' esperado=['exercicios-de-processamento-de-imagens', 'floodfill', 'remocaoderuido'] antes=['exercicios'] depois=['exercicios-de-processamento-de-imagens', 'exercicioduascores']
flip + [ambigua] 'o que cai na P1?' esperado=['cronograma2026-2', 'planodeensino-4645z-04-fundamentos-de-computacao-grafica', 'resolucao-de-prova-de-computacao-grafica-2d', 'resolucao-de-prova-de-computacao-grafica-2d-html'] antes=[] depois=['cronograma2026-2', 'planodeensino-4645z-04-fundamentos-de-computacao-grafica']
flip - [malformada] 'segmentacao imagem' esperado=['segmentacaodetexturas', 'segmentacaopptx'] antes=['segmentacaopptx', 'segmentacaodetexturas'] depois=['pagina-com-videos-sobre-segmentacao-de-imagens-d0627f', 'pagina-com-videos-sobre-segmentacao-por-texturas-e03566']
flip + [malformada] 'transformacoes opengl codigo' esperado=['transformacoesgeometricas', 'transformacoesgl'] antes=['basico3d-py', 'opengl-py'] depois=['transformacoesgeometricas', 'transformacoesgl']
flip + [estruturada] 'Como funciona o algoritmo de recorte de retas de Cohen-Sut' esperado=['pagina-com-videos-sobre-recorte-e257d3', 'recorte', 'video-sobre-o-algoritmo-de-recorte-por-subdivisao-binaria-db7e2e', 'vis2d'] antes=['maptextures', 'exercicios-teoricos-sobre-processo-de-visualizacao-2d'] depois=['pagina-com-videos-sobre-recorte-e257d3', 'exercicios-teoricos-sobre-processo-de-visualizacao-2d']
flip + [estruturada] 'Como detectar colisão entre dois objetos usando envelopes ' esperado=['colisao', 'videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84'] antes=['opengl-cpp', 'opengl3dcpp-vdi'] depois=['colisao', 'videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84']
flip - [estruturada] 'Como funciona o algoritmo Z-Buffer para remoção de element' esperado=['elemoculto', 'exemplozbuffer'] antes=['elemoculto', 'exemplozbuffer'] depois=['colisao', 'exemplozbuffer']
flip + [ambigua] 'tem exercício de imagem?' esperado=['exercicios-de-processamento-de-imagens', 'floodfill', 'remocaoderuido'] antes=[] depois=['exercicios-de-processamento-de-imagens', 'floodfill']
flip + [ambigua] 'o que cai na P1?' esperado=['cronograma2026-2', 'planodeensino-4645z-04-fundamentos-de-computacao-grafica', 'resolucao-de-prova-de-computacao-grafica-2d', 'resolucao-de-prova-de-computacao-grafica-2d-html'] antes=[] depois=['cronograma2026-2', 'planodeensino-4645z-04-fundamentos-de-computacao-grafica']
flip + [malformada] 'transformacoes opengl codigo' esperado=['transformacoesgeometricas', 'transformacoesgl'] antes=['basico3d-py', 'basico3d-cpp'] depois=['transformacoesgeometricas', 'transformacoesgl']
**Leitura:** alvo do handoff ATINGIDO — IA com LLM 9 -> **14/15** (hit@3 10 -> 14), FR 15/15 nos dois modos com LLM (bloco 6/6, o flip do item 12
sumiu), CG com LLM 7 -> **10/15** (hit@3 7 -> 13) e com contexto completo 7 -> **11/15** (hit@3 8 -> 14); bloco do CG 8 -> 9/11. Flips negativos:
CG `zbuffer` (escolheu `colisao`, 2a escolha certa) e `segmentacao imagem` (escolheu a pagina de videos sobre segmentacao, irma do alvo) —
2 perdas contra 5-6 ganhos por modo. **Ressalva medida:** a celula IA + contexto completo (13/15, hit@3 15) e da rodada sobre o FILE_MAP anterior
a correcao do `|` (1 celula de titulo); a rerodada falhou com Gemini 429 `prepayment credits are depleted` — creditos da API esgotados em
05/09 00:45; as outras 8 celulas estao no FILE_MAP final. Custo desta regua: 105 chamadas (IA 45, FR 30, CG 30). CG sem-llm nao move (5/15): o piso por tokens le title/label/
subtopico/secoes do MANIFEST, nao o FILE_MAP; o `title` = nome de arquivo do rebuild e a causa (entrada para a SYNC/C1 item 2: title do
material html = label do Moodle no manifest).

## C0 ITEM 12 — TRAVESSIA "DEPOIS" (05/09 madrugada, FEITO; **C0 FECHADA 11/11**)
Mesma regua de 02-03/09 (`scripts/eval_travessia.py`, 3 cursos x 3 modos; LLM so para medir, cache por hash do contexto). Gold do CG
re-chaveado para o rebuild (10 alvos de ids do export para ids novos, `esperado` so; export em `_archive/travessia_gt_CG.export.csv`).
Chamadas Gemini novas: 60 (FR 30 + CG 30; IA 0 = indices do IA nao mudaram desde 03/09, o cache bateu nos 3 modos).

| curso | modo | hit@1 antes -> depois | hit@3 | bloco | estruturada | ambigua | malformada |
|---|---|---|---|---|---|---|---|
| FR (22 mat., FILE_MAP 20/22) | sem-llm | 9/15 -> 9/15 | 11 -> 11 | 5/6 -> 5/6 | 4 -> 4 | 2 -> 2 | 3 -> 3 |
| FR | LLM | 15/15 -> 15/15 | 15 -> 15 | 6/6 -> 6/6 | 5 -> 5 | 5 -> 5 | 5 -> 5 |
| FR | LLM + contexto completo | 15/15 -> 15/15 | 15 -> 15 | 6/6 -> **5/6** | 5 -> 5 | 5 -> 5 | 5 -> 5 |
| IA (59 mat., FILE_MAP 19/59) | sem-llm | 10/15 -> 10/15 | 12 -> 12 | 6/8 -> 6/8 | 4 -> 4 | 1 -> 1 | 5 -> 5 |
| IA | LLM | 9/15 -> 9/15 | 10 -> 10 | 8/8 -> 8/8 | 3 -> 3 | 2 -> 2 | 4 -> 4 |
| IA | LLM + contexto completo | 10/15 -> 10/15 | 10 -> 10 | 8/8 -> 8/8 | 3 -> 3 | 2 -> 2 | 5 -> 5 |
| CG (export 73 -> **rebuild 93 mat.**, FILE_MAP 26/93) | sem-llm | 10/15 -> **5/15** | 11 -> 6 | 8/11 -> **10/11** | 4 -> 4 | 3 -> 0 | 3 -> 1 |
| CG | LLM | 8/15 -> 7/15 | 8 -> 7 | 7/11 -> **8/11** | 2 -> 2 | 3 -> 3 | 3 -> 2 |
| CG | LLM + contexto completo | 10/15 -> 7/15 | 10 -> 8 | 7/11 -> 7/11 | 2 -> 2 | 4 -> 3 | 4 -> 2 |

**Leitura (medida, por pergunta — `_harness-2026-09-04/c0-12/`):**
- **IA identico** nos 3 modos com 0 chamadas: os itens 2-11 nao mexeram no FILE_MAP do IA (blocos/unidades iguais). FR: material 15/15 nos dois
  modos com LLM; **1 flip de bloco** no contexto completo ("osi tcp ip diferenca": material certo `02-modelos-de-referencia`, bloco respondido
  bloco-20 em vez de bloco-02 — o cronograma do FR tem DOIS blocos rotulados "Modelos OSI e TCP/IP", set e nov, e o FILE_MAP do FR mudou no 11a
  (os `udp-example` migraram para o bloco-20 pelo voter). Achado para a C1: label de bloco duplicado no cronograma confunde o "quando".
- **CG com LLM: 7 acertos, TODOS com alvo dentro do FILE_MAP; 8 erros, TODOS com alvo FORA do corte** (FILE_MAP.md 11 964 chars = clamp 12 KB;
  cita 26/93 materiais). Mesmo diagnostico de 03/09 (era 20/73), agora no rebuild: recorte, colisao, fundamentosmatematicos, transformacoesgl,
  planesweep, exercicios-de-processamento-de-imagens, cronograma/plano ("o que cai na P1?") — nenhum esta no indice que o tutor le.
- **CG sem-llm 10 -> 5:** o piso por tokens casa a pergunta com o `title`, e no rebuild o `title` e o nome do arquivo ("Vis3d", "PlaneSweep",
  "FundamentosMatematicos"); o `moodle_label` humano existe no manifest ("Visualizacao 3D - Projecao", "Pagina sobre Geometria Computacional",
  "Slides sobre Deteccao de Colisao") e **o FILE_MAP imprime o `title`, nao o label**. Achado para a C1: linha do FILE_MAP com o label do Moodle.
- **Bloco ("quando") MELHOROU no CG** onde o material existe: sem-llm 8/11 -> 10/11, LLM 7/11 -> 8/11 — essa e a parte do motor (C0) na travessia.
**Conclusao do item:** nada regrediu por causa do motor; a travessia e limitada pelo indice, nao pela atribuicao. **C0 fecha 11/11.** Entradas
numeradas para a C1: (1) FILE_MAP completo (clamp 12 KB -> 80 KB + aviso; CG 26/93, IA 19/59, MF 20/66, SO 22/39, ES2 21/35, TCC 18/27);
(2) linha do FILE_MAP com `moodle_label` (piso CG 5 -> medir); (3) label de bloco duplicado no cronograma (FR bloco-06/20). Alvo da C1 ja
medido em copia (03/09): IA 9 -> 14/15 com o indice completo.

## C0 ITEM 9 — REFACTOR CORTE 1: scripts/ 81 -> 37 + ESCADA DA REGUA AULA PODADA (04/09 sessao 5 noite, FEITO)
Gerador `557be23` (corte) · `599ff10` (baseline CG do teste de caracterizacao apos o item 10) · `1284b26` (regua). **Criterio medido, nao gosto:**
grafo completo de dependencias entre scripts (`import X`, `from scripts.X import`, subprocess por caminho) + citacao em `src/`, testes vivos e
docs vivos (handoff/tracker). O primeiro scan (so `import X`) errou 5 dependencias reais (`compare_resolver` <- 2 ferramentas de gold,
`erros_motor_nu` <- ablacao por subprocess, `eval_units` <- check_sarc_freshness, `migrate_signals` <- moodle_pull, `expand_card_gold` <- gold_by_card);
o scan completo pegou. Ficam **37** (o plano dizia ~25; a diferenca e o acoplamento por teste e por import, listado no commit): 8 do handoff
§Ferramentas, 5 dependencias, 13 utilitarios de produto com teste, 6 de gold/auditoria com teste, 5 dependencias do scan. Arquivados **44 +
`artefato_razao/`** em `docs/reports/_archive/scripts-2026-09-04/` por `git mv` (historico com `--follow`), README com 1 linha por script (linhas,
ultimo commit, docstring); 4 arquivos de teste que so testavam scripts arquivados foram junto (`tests/` do archive; `testpaths=tests` nao os
coleta): **suite 2337 -> 2312**. `true_of` (gold por uuid) subiu de `fase0_prova_motor_MF` para `eval_ground_truth`; `.gitignore` acompanhou 2 saidas do
`artefato_razao`. `src/` intocado: tutores byte-identicos por construcao; py_compile 37/37; sentinela 0/8; determinismo nao rodou (nada em `src/`).
**Achado no caminho:** `tests/test_caracterizacao_blocos_atual.py` compara a divisao de blocos dos tutores REAIS com `tests/_golden/`; o reprocess do
item 10 mudou o CG (blocos 08/13) DEPOIS da suite do item 10 -> baseline regenerado e commitado (`599ff10`), mudanca esperada. Licao: a suite do
gate roda DEPOIS do reprocess registrado, nao antes.
**Regua AULA podada:** saem H1 e H7 (refutados no gold), H9 e H8 (ja producao desde a Fase 3) e os picks velhos de `moodle_sections/`; fica a linha
"motor puro hoje" (TODOS/AULA/REF/BASE), o RESTO por categoria x metodo e os flagados do motor puro. Antes: escada stale imprimia 170/189 e
"16 (8/100) depois da escada"; agora: motor puro hoje TODOS 186/203 · AULA 174/189 · REF 8/10 · BASE 4/4; flagados no motor puro 45/189 = 23,8/100 (errados 9), erros confiantes 6. Imports de `disambiguator`/`navigation`/`stopwords` sairam da regua (era recalculo de H8).

## C0 ITEM 10 — UNIDADE: ANCORA LEXICAL EXCLUSIVA NO MAPA BLOCO->UNIDADE (04/09 sessao 5 noite, FEITO E REGISTRADO NOS 8)
Gerador `4a14d8b`. **Medido ANTES do codigo (`c0-10/disseca_unidade_10.py`):** dos 12 erros de unidade do motor puro +vocab (179/191), 10 tinham
BLOCO CERTO e unidade errada: o mapa bloco->unidade da DP posicional (`unit_matcher.assign_units_positional`, monotonica na ordem do plano, 1 desvio)
erra onde o professor sai da ordem, e a curada corrige com PINO MANUAL de unidade no bloco (14 pinos nos 8 tutores; o auto erra em 3, todos do SO:
bloco-06 -> 04 deadlock, bloco-12 prova, bloco-20 "Arquivos" -> 06); no IA os blocos 01-03 deslocam sem os pinos. Os outros 2 eram bloco errado
(SO sockets; o voto resolve na curada). O texto do material acertaria a verdade em 5/12 — a reconciliacao impoe a unidade do bloco.
**Simulacao (`c0-10/simula_ancora_unidade_10.py`, DP atual reproduzida 133/133):** 8 variantes. DP segmentada por ancoras (C/D) chega a 185/191
mas muda 12-14 blocos e perde 1 pino do IA — fora. Ancora so no proprio bloco, com afinidade >= 2 tokens e token exclusivo da unidade (F/H): muda 3
blocos e da 183/191, 0 flip negativo; com afinidade 1 mudaria TCC 33 ("prova") e CG 15 — fora. Bloco com token exclusivo de DUAS unidades e ambiguo
e fica com o otimo global da DP (2 testes existentes protegem isso).
**Regra (1 constante + 8 linhas):** apos a DP (com desvio), bloco com >= `ANCHOR_MIN_AFF`=2 tokens na unidade argmax, margem >= `ANCHOR_MIN_MARGIN`=1
e um token que SO essa unidade tem no plano recebe o argmax; so ele, a DP dos vizinhos fica. Funcao antiga x nova nos 8 (mesmos blocos e taxonomia):
**3 blocos** — SO bloco-20 Arquivos 07 -> 06 (pino manual confirma; 4 entries do gold), CG bloco-08 Morfologia 06 -> 01 e CG bloco-13 Curvas 06 -> 07
(secoes do Moodle "11 - Morfologia" e "7 - Curvas" confirmam; 12 materiais), conf 0,4 -> 0,6. Teste novo; fixture do teste de otimo global movida
para 1 token (a fronteira da "ancora espuria" passou a ser 1 token, mesma leitura do 11a).
**Copias:** bloco 183/200 conf-err 2 = · **unidade 179 -> 183/191 (95,8%)** (SO 28 -> 32/37) · cobertura 53/57 = · subunidade 82/93 = · AULA 174/189 =
· holdout CG puro 31/35 conf-err 0 = · curado 35/35 =. Suite 2337.
**Originais (reprocess registrado `c0-10/reprocess_10.py`):** MF `7f17ccf` · SO `9c0b1bb` · IA `270975d` · ES2 `d5f96a5` · TCC `a438a52` · LR `c0df4a6` · FR `a6f3db0` · CG `2efddcb`. flagadas 38 -> 38 (+0) | blocos mudados 0 | unidades mudadas 12; unidades mudadas por tutor: nenhuma. Gate: curada 199/200 conf-err 0 · 191/191 · 55/57 intacta ·
sentinela 0/8 · determinismo 8/8 (0 arquivos nao deterministicos) · censo revisar/100 58,3 -> 58,0 · votos/100 36,5 =.
**Fica sem alavanca estrutural (registrado, nao vira regra):** SO bloco-06 (3 entries: o texto diz "gerencia do processador", o pino diz deadlock —
juizo humano) · IA blocos 01-02 (3 entries: a DP sem ancora desloca a introducao para a unidade 05) · SO sockets (2 entries: erro de bloco).

## C0 ITEM 11b — LLM SO NOS FLAGADOS + VOTOS CONTADOS NO CRONOGRAMA_HEALTH (04/09 sessao 5 noite, FEITO E REGISTRADO NOS 8)
Gerador `86dab7e`. **Dado ANTES do codigo:** o voter (`anchor_engine.py:252-259, 268-269`, `resolve_funnel`) JA vota so em decisao
FLAGADA ∪ membro de serie same-theme (mesmo confiante) ∪ prova/trabalho sem due (`lexical=False`) ∪ funil sem janela; janela-1 nunca vota.
Votos hoje nos 8 originais: **127** = flag 88 · serie flagada 5 · serie com motor confiante 17 (recomputo sem voter — a leitura por
`computed_block_band` engana: e o scorer legado concept-fused, nao o motor) · funil 16 · prazo 1; acerto no gold 78/79.
**Passo 1 (`c0-11b/mede_serie_11b.py`, read-only):** dos 22 votos de serie, 17 caem onde o motor ja decidia sem flag; motor 15/16 no gold,
voto 16/16. O caso: MF `exerciciosdafny2` (motor alta bloco-11 por margem — um dos 2 conf-err do motor puro; voto = gold bloco-13). Cortar
a via "serie confiante" poupa 17 votos (13%) e cria 1 conf-err na curada (MF 66 -> 65/66): **nao entra** (nada regride). "LLM so nos
flagados" ja e o desenho — item fecha SEM mexer no motor.
**Codigo:** `cronograma_health.llm_vote_summary(entries)` (pura) + secao "Votos de LLM (motor TIER 3)": decisoes por `llm`/`llm-funil` e
flagados, por 100 entries — mesma regua do censo. Teste RED/GREEN; suite 2336. Previa nos 8 = censo: 127/348 = 36,5/100 · flagados 38 =
10,9/100 (MF 50,0 · ES2 48,6 · FR 54,5 · CG 43,0 · SO 23,1 · IA 23,7 · LR 14,3 · TCC 3,7). Reprocess registrado (variante 11b de
`c0-11a/reprocess_11a.py`): MF `8eda277` · SO `33d7b4a` · IA `89ee427` · ES2 `b47ba76` · TCC `417c4a8` · LR `fdc4f8b` · FR `b6e68cd` · CG `b4dee75`. Resultado: flagadas 38 -> 38 (+0) | blocos mudados 0. Gate: determinismo 8/8 (0 arquivos nao deterministicos) · sentinela 0/8 · curada/holdout intactos (relatorio derivado; motor nao mudou).
**Decisoes do item, registradas sem re-medir:** ordem motor -> LLM -> card FICA (card antes do voter derrubou a curada 199 -> 187, 03/09).
Gate "residual flagado em AULA <= 8/100": produto apos 11a = 15/189 = **7,9/100**, os 15 sao janela-1 (SO 8, TCC 5), due-straddle (MF 1) e
llm-funil (SO 1) — sem 2o candidato para votar; atendido (o "18,5" do plano era o motor puro sem LLM). Regua por item: proposta = com-vocab
+ curada + holdout a cada item, ablacao so em gate — **decisao aberta do user** (ja listada no handoff).

## C0 ITEM 11a — `exclusivo` DO DISAMB EXIGE 2+ TOKENS (04/09 sessao 5 noite, FEITO E REGISTRADO NOS 8)
Gerador `728c0f1` (1 linha em `routing/motor/disambiguator.py:264` + 2 testes; suite 2335). Dado ANTES do codigo (`s6f/mede_exclusivo.py`):
22 decisoes "disamb alta" apoiadas em UM token de contato nos 6 golds, 5 erradas (77%); com 2+ tokens ou margem, 94%. Regra: `exclusivo`
(s1>0, s2=0) so e confiante com `len(discriminante) >= 2`; 1 token -> banda media + flag (o best fica; voter e card agem). Vocab curto sozinho
e indicio, e o segundo token que decide (teste de `test_motor_tokens.py` ajustado + teste novo).
**Copias `.ablacao`, antes -> depois na MESMA base (`c0-11a/flags_antes_depois_11a.log`):** bloco 183/200 = · conf-err 3 -> 2 · unidade 178 -> 179/191
· cobertura 53/57 = · subunidade 82/93 = · flags 40 -> 48 (5 cursos, 226 entries). AULA 174/189 = · REF 8/10 = (`regua_aula`, linha "motor puro
hoje"; residual pos-escada 35 -> 16 porque H9 so age em flagados — nao e ganho da regra). `mede_exclusivo` depois: excl1 = 0 em todos; restam 2
conf-err (MF `revisao` com 2 tokens, MF `exerciciosdafny2` por margem). Holdout CG puro 31/35 = com conf-err 2 -> 0 (flagados 9 -> 14); curado
33 -> **35/35** (conf-err 0, flagado 1).
**Originais (reprocess registrado, `c0-11a/reprocess_11a.py`, commits "reprocess: exclusivo com 1 so token vira flag ... (gerador 728c0f1, C0 11a)"):**
MF `fa85ce0` · SO `393f135` · IA `f00c53e` · ES2 `4ef7ead` · TCC `56faba3` · LR `1d7bafe` · FR `d876645` · CG `0bc78a4`. Flagadas 38 -> 38 (o
voter resolveu todas; 23 votos novos: MF 2, IA 3, FR 2, CG 16). 5 blocos mudaram: CG `matematica` e `transformacoesgl` (os 2 erros do gold — CG
original agora **35/35**), CG `pagina-com-videos-sintese-realistica` (proc. imagens -> iluminacao), FR `udp-example-c` (transporte bloco-06 ->
sockets bloco-22, com `unit_block_conflict`) e `udp-example-java` (-> aplicacao bloco-05): **os gemeos foram separados pelo voter, sem gold —
olhar na C1 (travessia FR).** Gate nos originais: curada 199/200 conf-err 0 · 191/191 · 55/57 = · sentinela 0/8 · determinismo 8/8 (0 arquivos nao deterministicos) · censo revisar/100
54,0 -> 58,3 · votos/100 29,9 -> 36,5 (custo declarado no plano: ~22 votos; medido 23). Harness: `_harness-2026-09-04/c0-11a/`.
**Divida de higiene achada no caminho (nao mexida):** `tests/test_unit_matcher.py` (~linhas 168-199) monta a timeline dos tutores REAIS
(`GitHub/Sistemas-Operacionais-Tutor`, `Metodos-Formais-Tutor`) e grava `course/.block_identity.json` do MF original (`last_seen`) a cada
suite — medido arquivo a arquivo (unico que reescreve; 04/09 20:34). Teste de unidade escrevendo em repo de producao: corrigir com copia para
tmp ou `TUTOR_COURSES_DIR` obrigatorio (1 linha) — C4, ou antes se incomodar.

## AUDITORIA DAS REGUAS (04/09 sessao 5, a pedido do user, antes do C0)

Tudo remedido em 04/09 (gerador `09feaca`+): curada dos 5 (`eval_eixos`, N=200) **199/200 conf-err 0 · 191/191 · 55/57**; motor puro
+vocab (`motor_puro`, N=200) **183/200 conf-err 3 · 178/191 · 53/57 · sub 82/93** (78 primario); AULA (`regua_aula` linha "motor puro hoje",
N=189) **174/189** = 92,1%, residual flagados 35 (18,5/100), erros flagados 7, erros nao flagados 8 (banda alta 3); REF 8/10 (flagados 3);
BASE 4/4; por escopo do motor no PRODUTO dos 6 golds (N=238): material 211/214 (conf-err 2 = CG `exclusivo`, flagados 16) · prazo 10/10
(flagados 5) · referencia 10/10 · meta 4/4; por tipo: pdf 152/153 · code 38/39 · zip 30/30 · html 10/11 · url 3/3 · github 2/2;
holdout CG puro 31/35 (flag 9) · curado 33/35 (flag 1), conf-err 2; unidade CG 33/35; censo revisar/100 54,0 · votos/100 29,9 (348);
sentinela 0/8; **determinismo 8/8 = 0 arquivos**. Tudo igual ao gate de 03/09: nenhuma regua regrediu com S6a-S6f.
**Defeitos de regua/gold achados e tratados:** (1) `regua_aula` aplica a escada stale (H9 `picks_card.json` de 02/09 "agiu em 54") e
imprime 170/189 no fim — so a linha "motor puro hoje" vale; podar no C0 item 9. (2) Gold do TCC tinha 9 ids duplicados (pares de PDFs
iguais do export com nome quase igual, mesmo bloco): 42 -> 33 linhas, 27 scorable unicos (o "36" nunca foi medido; `eval_eixos` conta
25 = 27 menos 2 pares colapsados por `pair_key`); reguas identicas antes/depois (TCC 25/25 · 18/18 · 3/3). (3) IA tem 17 linhas sem id,
todas scorable=no (materiais nao rotulados) — ok. MF/SO/ES2 e os golds de subunidade/material/cobertura: sem duplicata. (4) N difere
entre reguas para os mesmos golds (200 / 203 / 238): todo numero carrega sua regua e seu N.
**Deixado para tras e fechado antes do C0 (04/09):** o dry-run da sync no CG novo marcava as 4 folhas como SUMIDO (o casador parava no
basename do hub e nao chegava ao label): `match_module_entries` agora une o casamento por label unico ao do basename — dry-run: sumidos
0 · iguais 93 · novos 2 (os xlsx, por desenho); motor puro dos 5 identico (183/178/53/82, conf-err 3); suite 2333. Temporarios
`.determinismo`, `.ablacao/CG-gate-html`, `CG-rebuild-holdout` apagados; ficam `CG-rebuild` (365 MB) e `CG-export-backup` (440 MB) ate o user liberar.

## SYNC S6f — REBUILD LIMPO DO CG PELA API (04/09 sessao 5, FEITO NA COPIA; decisao do user pendente)

Pull real (`moodle_pull --pdf`, raiz `Desktop/Moodle/computacao-grafica`, export intacto): 93 links -> 40 download, 15 html, 15 snapshot,
23 referencia, 0 review, 0 erro; stash 218 arquivos (21 PDF, 14 zip, 3 cpp, 2 xlsx ignorados, 15 html do Moodle, 13 bundles de pagina
com 146 imagens, 0 `.orig`). Fix no caminho: pagina `index.*` leva o nome do diretorio da URL (`d7b2f87`; 4 links colapsavam).
Build na COPIA `.ablacao/CG-rebuild/Computacao-Grafica-Tutor` (`_harness-2026-09-03/s6f/rebuild_cg.py`, mesmo caminho da UI, perfil
real, zero curadoria): 2052 s, 0 falhas, 66 entries (28 html, 21 pdf, 14 zip, 3 code); Datalab 115 chamadas = 229 paginas de PDF
(~0,33 c/pagina) + 94 imagens (1 c) ~ US$ 1,70; Gemini 72 textos (legendas/descricoes) + 41 bundles. Imagens das paginas: 136 ->
37 formulas (37 reviews em `manual-review/formulas/`), 84 figuras, 5 descritas, 10 nao capturadas (8 do `cs.uic.edu` na Iluminacao,
2 `Window1.png` do mesmo host numa pagina do Moodle solta — caixa de ideias). revisar: duvida 38 · ok 21 · llm 7 (68/100).
Gold re-chaveado (`s6f/rekey_gold_cg.py` -> `s6f/ground_truth_CG.rebuild.csv`, NAO substitui o versionado): blocos 29 = 29 com a
mesma numeracao e datas; 61 linhas -> 48, **35/35 scorable** (4 aliases: paginas do site impressas no export -> bundle html;
ambiguidade resolvida pela secao original). Revisao do user: `s6f/formulas_index.md` (37) e `s6f/revisar_queue.md` (45).
**Reguas:** holdout **puro 30/35** (gate >= 30 batido), conf-err 2 (baseline 1); holdout **curado+LLM 33/35** (gate 34/35 NAO
batido), conf-err 2 · curada dos 5 199/200 · 191/191 · 55/57 intacta · sentinela 0/8 · determinismo do rebuild 0 arquivos (2 rodadas).
**Achado (raiz do 33, reproduzido em `_harness-2026-09-03/s6f/disseca_transformacoes.py`):** `transformacoesgl` (pagina "Transformacoes
Geometricas em OpenGL", secao 6 do Moodle, gold bloco-06) toca UMA assinatura de bloco no curso inteiro: o token "geometrica" de
bloco-15 ("modelagem geometrica") — coincidencia lexical, nao topico. Na janela de 9 blocos s2=0, e a regra `exclusivo` do
`_lexical_decision` (D4 relido 21/08: s1>0 com s2=0 = "evidencia mais exclusiva possivel", 21/23 nos 5 cursos) da banda ALTA sem
flag -> o voter nao vota e o card da secao 6 nao age (estrutura so em decisao flagada). No export a MESMA pagina ficava flagada
(margem 0,29 < 0,55) porque o texto impresso trazia o boilerplate do gerador ("Descricoes preservadas para imagens detectadas..."):
o token "imagens" pontuava bloco-07 — RUIDO, nao evidencia (a hipotese anterior do "2d" no nome de arquivo estava errada: "2dfa6ac3"
e um token so). O 34/35 do baseline dependia desse ruido; o motor honesto da 33/35. Balde: C0 item 11 (calibracao: `exclusivo`
por 1 token generico; `unit_block_conflict` ja registra unidade-05 x bloco de unidade-06 com 0,95 e nao rebaixa a banda).
**Medido nos 6 golds (motor puro, `s6f/mede_exclusivo.py` e `s6f/mede_conflito.py`, 04/09):** decisoes `disamb` ALTA com gold = 58:
exclusivo por 1 token 22 (5 erradas = 77%: MF `terminacao`, ES2 `azure` "servicos", CG `matematica` x2 versoes, CG `transformacoesgl`)
· exclusivo por 2+ tokens 18 (1 errada, 94%) · margem >= 0,55 18 (1 errada, 94%); a banda alta promete ~98% — o furo e SO o balde de
1 token. `unit_block_conflict` NAO separa (erradas com conflito 2/7; certas com conflito 5/51): nao e alavanca. `matematica` e caso
de JANELA (bloco-03 fora dos 9 blocos), nao de banda. Candidato para o C0 item 11, a medir antes de entrar: exclusivo por 1 token ->
banda media + flag (voter e card agem): no puro -5 conf-err e 17 certas viram duvida (revisar/100 e votos/100 sobem, ~+22 votos nos
6 cursos); no curado o LLM decide (22/23 no balde parecido, medido em 21/08). Sem regra por curso; nada entra sem esse numero.
**Decisao final do user (04/09): 33/35 ACEITO com causa medida e o rebuild PROMOVIDO** (nao fazia sentido ficar com o export velho).
Tutor CG `a16051b` (66 entries), perfil `stash_folder` -> `computacao-grafica/stash`, `ground_truth_CG.csv` = re-chaveado (export em
`_archive/`), `course/SYNC_REPORT.md` com as 37 formulas. Reguas no CG novo (`.ablacao` re-sincronizado): holdout **puro 31/35 (conf-err 2, flagados 9) · curado
33/35 (conf-err 2, flagados 1)** · sentinela 0/8 · censo revisar/100 51,8 -> 54,0 (321 -> 348 materiais), votos/100 32,3 -> 29,9. Export antigo em `.ablacao/CG-export-backup`.
Revisao humana: `formulas_index.md` 37/37 APROVADAS pelo user (04/09; conferencia por LLM na caixa, C3). Pendente (nao trava): `revisar_queue.md` (45); o antigo pendente (3) a copia virar o original
**Complemento do rebuild (04/09, achado pela pergunta "73 -> 66, por que?"):** 3 paginas sairam por regra (nao apontadas por card:
OpenGL.html, Navega, ImageClass); 4 folhas da subarvore (Slab, Dominancia, PlaneSweep, ExercicioDuasCores) ficavam so no mirror —
bug do S6d corrigido em `1d14353` (folha vira bundle no modulo do hub); 23 referencias (7 videos + 16 indices de video) nao entram
pelo caminho de build, so pela sync. Dry-run da sync no rebuild expos 19 "sumidos"/19 "novos" num repo recem-construido: tres raizes
corrigidas em `bff1fa4` (moodle_label no build; `sync_diff` casa materiais de modulo url/page; stem so com extensao compativel —
o anexo .cpp de uma pagina roubava o .zip de outro modulo). `s6f/sync_complete_cg.py` leva folhas + referencias + labels ao repo:
CG final 93 entries, tutor `e3d02ed`; sumidos 0, novos 18 por desenho (16 indices ja referencias + 2 xlsx).
 (`Computacao-Grafica-Tutor`, commit no
tutor) e o perfil apontar `stash_folder` para `computacao-grafica/stash`. Ate la o CG original NAO muda.

## SYNC S6a-S6e — HTML COMO MATERIAL (03/09 sessao 5, FEITOS)

S6c `12990ed`: `formula_index` + secao "Formulas transcritas (conferir com o professor)" no SYNC_REPORT (por entry html: n formulas,
n nao capturadas, arquivos de review). Na copia do gate: curvas 12 · 0 · 12 reviews. Suite 2318.

Commits: S6a `6111b46` (conversor: `truncate_markdown_blocks(max_chars=None)`, Comment/Declaration nao vazam, cabecalho web so
com URL) · S6b `0a8ae2e` (`core/html_material.process_html`, tipo `html` antes de code, `GeminiClient.generate_text`, resolver conta
link para content/images) · fix `a10a6ca` (referencia url sem cabecalho web: hash estavel, sem re-sumarizar a cada regeneracao).
Decisao: `decisions.md` §"HTML salvo e material". Testes: `test_url_markdown.py`, `test_html_material.py`, `test_gemini_generate_text.py`.
**Dado antes de codigo** (51 paginas reais do CG = 20 do site + 31 do Moodle): 0/51 passam de 15 000 chars (Vis3d 14 183); VML
vazava em 4; 3 paginas do Moodle ("resolucao de prova") com 20 PNGs `data:` inline (0,6-2 MB de markdown); 139 imagens no mirror,
0 duplicadas por md5, 0 logos sobrevivem ao conversor (todos em `<td>`) — regra "logos descartados por md5" NAO entrou; gold do
Datalab: 12/12 formulas com `$$`, 0/9 legendas (legendas tem `$C_1$` inline). Custo real estimado do CG: ~160 imagens ≈ US$ 1,60.
**Gate:** suite 2316 · Curvas.htm na copia `.ablacao/CG-gate-html` (layout real do mirror, cache semeado do gold): 24 imagens ->
12 formulas + 9 legendas + 3 descritas, 0 nao capturadas, 24 copias em content/images, 12 reviews em manual-review/formulas,
0 Datalab, 12 Gemini; unprocess + re-add = 0 chamadas, markdown byte-identico, mesmo bloco (bloco-15 por janela-1, igual ao irmao
`computacao-grafica-curvas-parametricas`; o irmao `curvasparametricas` esta em bloco-13 — ambiguidade pre-existente do CG, C0) ·
curada 199/200 conf-err 0 · 191/191 · 55/57 · motor puro +vocab 183/178/53/82 · sentinela 0/8 · determinismo 8/8 (FR estava com 4
arquivos por causa pre-existente do S5: referencia url re-sumarizada toda rodada; corrigida em `a10a6ca`; FR original re-sumariza
UMA vez na proxima sync). Tutores: nenhum muda neste passe.
Achados no gate: (1) `resolve_content_images` apagava as 12 GIFs de formula (fonte e link `[..]`, nao `![..]`) — raiz corrigida;
(2) FILE_MAP nao lista `curvas` — clamp de 12 KB (nem o PDF irmao aparece): C1, nao S6.
S6d `5799035`: pull grava `stash/<card>/<nome>.html` (resource .htm(l) e mod_page; acao `html`, antes `print`), snapshot vira
bundle `stash/<card>/<Stem>/` (pagina + imagens do mesmo host, do dir da pagina no caminho relativo e de fora pelo basename; nunca
`.orig`) e segue links so na SUBARVORE da pagina (`in_subtree`; `same_site` vazava `Aulas/`, `CGII/`, `~manssour/`, `CG-PPGCC/`);
**regra (a) do user:** onde ja existe `<stem>.pdf` impresso (LR, 4 labs) o PDF fica e o `.html` nao entra (`pdf-existente`), migracao
na fronteira; scan trata o bundle como 1 item html (imagens nao viram entries); URL absoluta do mesmo host resolve pelo basename no
dir da pagina (4 refs no CG). Nenhuma pagina e mais impressa em PDF. Dry-run real do CG (93 links): 15 paginas do Moodle -> html,
15 snapshot, 23 referencia, 40 download, 0 gravado. Suite 2326.
S6e (fixtures) FEITO por construcao no TDD de S6a-S6d: `test_url_markdown.py` (Curvas.htm real), `test_html_material.py` (gold Datalab
do piloto + clientes falsos), `test_site_snapshot.py` (mirror real), `test_moodle_pull.py`, `test_moodle_sync.py`, `test_stash_import.py`.
**Falta no S6:** S6f = CG rebuild limpo pela API (gasto real: Datalab 21 PDFs + ~160 imagens ~ US$ 3,60; Gemini 18 codigos +
traducoes + voter com cap): `moodle_pull --pdf` na raiz do perfil (stash novo em `computacao-grafica/stash/`, o export fica),
`build_course.py` numa COPIA (zero curadoria, summaries ON, vocab, voter com cap), gold `ground_truth_CG.csv` re-chaveado (ids novos
vem do nome do modulo; `true_block_uuid` como chave de bloco), holdout >= 30/35 puro e 34/35 curado, curada dos 5 intacta,
sentinela 0, user revisa `revisar` e a lista de formulas do SYNC_REPORT; so entao a copia vira o original. Evidencia versionada:
`_harness-2026-09-03/piloto-curvas/{gate_s6b_curvas.py,Curvas.s6b.md}`.

## SEQUENCIA ACORDADA (02/09 noite) — HISTORICO: C0 e SYNC encerradas em 03/09 (fila viva no handoff 2026-09-03b)

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
4. ~~Fase 3b — ordem das secoes para cards sem data (+7/-1) e card generico -> apresentacao (+3/0)~~ FEITO 03/09 (§FASE 3b
   item 4): ordem das secoes agiu em 0 pos-item 3 (nao entrou); secao 0 do Moodle sem janela -> apresentacao (+3/0, AULA 167).
5. ~~Fase 3c — tokens curtos do cronograma no desempate (+4/-2), como strangler do tokenizador so no disambiguator~~ FEITO
   03/09 (§FASE 3c): +4/0 (IA k-NN x4), AULA 171 sem vocab / 170 com vocab; `text/tokens.py` = tokenizador unico (corte 3).
6. ~~Fase 3d — label unico nos flagados (+2/0)~~ NAO ENTRA (03/09): `mede_alavancas.py` pos-item 5 = conserta 0, quebra 0
   (ja certo 3: os +2/0 foram absorvidos pelos itens 3-5). Sem numero, sem codigo. H5 serie monotonica +1/-2 e H2 prova
   antiga 0/0 continuam refutados.
7. ~~Gate da Fase 3~~ REGISTRADO 03/09 (§GATE DA FASE 3): AULA 152 -> 174/189 (meta ~174 batida); curada intacta; motor puro 161/158/51/26 -> 184/168/54/30, +vocab 162/167/50/79 -> 183/178/53/82; censo votos/100 33,8 -> 32,0; **residual flagado em AULA 18,5/100 (meta <= 8/100 NAO batida: 35 flagados, 7 errados)** — e o balde do item 11.
8. ~~Rebuild pela API dos 3 do SEMESTRE CORRENTE~~ VIROU A CAMPANHA SYNC (03/09; handoff 2026-09-03-sync §FILA): S1 diff
   estrutural -> S2 import do delta -> S3 regeneracao + diff de decisoes + SYNC_REPORT -> S4 LR (Lab 4) -> S5 FR (controle) ->
   S6 CG (rebuild limpo, gold re-chaveado). Decisoes do user: sumido some (flag), "mudou, confira", alterado re-extrai
   automatico com cap, links entram como referencia. Os 5 encerrados NAO se rebuildam (regua de regressao).
9. Refactor corte 1 (scripts 79 -> ~25), sessao curta.
10. Fase 2 — cronograma manda na unidade, no que sobrou; depois `recompile_vocab` no CG.
11. Fase 4 — LLM residual so nos flagados, contado.
12. Travessia "depois"; so aqui grafo renderizado / vetores, se a regua mostrar perguntas fora do alcance dos indices.
Depois do motor: SYNC -> C1 travessia -> **C3 provas/listas/trabalhos** -> **C2 bibliografia (por ultimo, user 03/09)** -> C4 limpa
pre-web -> C5 dividas de dados -> C6 web (protocolo anti-regressao em `_archive/2026-09-02c-...` §CAMPANHAS). Cada pendencia
deste arquivo tem dono la; nada entra num lote sem gold e numero.

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

**Item 4 (mesma sessao; gerador `79fc92a`, tutor SO `603d914`, os outros 4 byte-identicos).** (a) Ordem das secoes como prior (H7): `mede_ordem_secoes.py --chain --only-flagged` nas copias
pos-item 3 = **GANHO 0 PERDA 0** (21 golds em cards sem data, todos "sem efeito": os +7/-1 de 02/09 eram flagados que o card
ordenado ja decide). Sem numero, nao entrou — nenhum codigo. (b) Card generico -> apresentacao (H1, +3/0: SO
`apresentacao-da-disciplina`, `questoes-do-enade-sobre-sisop`, `programa`, todos SEM-BLOCO no puro e llm-funil no curado).
Raiz: os 3 estao na **secao 0 do Moodle** = area geral do curso (`moodle_section_index == 0`, Fase 3a); o regex de nome
`informa|geral|aviso` do harness casava "Semana 12 ... Busca com Informacao" no IA (9 entries, falso positivo). Regra:
`resolve_general_section` — secao 0, sem janela de provider nenhum (nem card), so caminho lexical, depois de prep-prova
(listas P1/P2 do mesmo card continuam prep-prova) e antes do llm-funil; method/provider `secao-geral`, banda media;
`_first_class_block_decision` extraida de `resolve_generic_reference` (byte-identico). 3 testes em `test_card_stream.py`.
Numeros: motor puro sem vocab 173 -> **176**/200 (conf-err 3), unidade 161 -> **164** (herdam do bloco), cobertura 51,
sub 26; +vocab 172 -> **175** · 171 -> **174** · 50 · 82; AULA 164 -> **167**/189 sem vocab, 163 -> **166** com vocab; curada 199/200 · 191/191 · 55/57 · 93/93 intacta; sentinela: so SO (3 entries
llm-funil -> secao-geral, flag True -> False); censo nos 8: llm-funil 18 -> 15, revisar/100 53,2 -> 52,6, votos/100
33,8 -> 32,9. Divida achada: a escada da `regua_aula.py` (H1/H7/H9 via picks) esta STALE — os picks H9 do harness
"desflagam" entries que a producao ja decide e inflam "erros CONFIANTES" (12 -> 16 sem erro novo); a linha limpa e
"motor puro hoje". Podar no item 9 (refactor).

## FASE 3c (item 5) — TOKENS CURTOS DO CRONOGRAMA + TOKENIZADOR UNICO (03/09 sessao 4, FEITO)

**Entregue (gerador `fdf28af`; tutor IA `ca1f765`, os outros 4 byte-identicos):** `src/builder/text/tokens.py::motor_tokens(text, generic_stems, short_vocab, min_len=3)` — tokenizador UNICO do
motor (corte 3 do refactor, strangler: `disambiguator._toks` delega byte-identico; os outros 12 tokenizadores migram um a um
em C4 com sentinela 0). `disambiguator.course_short_vocab(ctx)` (tokens de 2-3 chars consagrados por topic_text +
primary_topic_label + labels de sessao via `short_vocab_from_topic_labels`, memoizado em `MotorContext._short_vocab_cache`).
`disambiguate`: desempate D4 (`_lexical_decision`) com tokens padrao; se FLAGADO e o curso tem vocab curto, refaz com o vocab
curto nos DOIS lados (material e assinatura) e adota se muda o bloco ou tira a flag, method `disamb-curto` (regua vigia em
separado); janela-1 e titulo-topico intocados. 6 testes em `tests/test_motor_tokens.py`. `regua_aula.py`: monkeypatch H8
adaptado a assinatura nova (H8 agora e producao; agiu em 0 na escada).
**Medido (copias):** motor puro sem vocab 176 -> **180**/200 (IA 37 -> 41: `algoritmo-de-classificacao-k-nn`, `exemplo-de-programa-
com-k-nn-em-java`, `exemplo-2-k-nn-com-iriscsv`, `exemplo-com-k-nn` — "nn" de "k-NN" -> "k nn", consagrado pelo cronograma; vocab curto do IA = es, g1, g2, ia, ml, nn, p1, p2, ps, t1, t2), conf-err 3, unidade
164, cobertura 51, sub 26; +vocab 175 -> **179** · 174 · 50 · 82. AULA 167 -> **171** sem vocab, 166 -> **170** com vocab; REF 8/10;
BASE 4/4. 0 perdas. Acumulado dos itens 2-5 vs snapshot pre-item 3: GANHO 23 · PERDA 5 · err->err 6.
**Curada:** 199/200 conf-err 0 · 191/191 · 55/57 · 93/93 intacta; sentinela so IA (3 entries `llm` -> `disamb-curto`, mesmo
bloco, banda alta, revisar llm -> ok); censo nos 8: llm 71 -> 68, llm-funil 15, revisar/100 52,6 -> **51,7**, votos/100
32,9 -> **32,0**. Aqui o texto curto preempta o voto e acerta — e o primeiro item que reduz votos no curado.

## ITEM 6 (nao entra) + ANCORA COMO FAIXA DA SECAO (refinamento do item 3; 03/09 sessao 4, "buscar o maior numero no motor puro")

**Item 6 (H6 label unico):** `mede_alavancas.py` pos-item 5 = conserta 0, quebra 0 (ja certo 3). Nao entra. H5 serie +1/-2 e H2
prova antiga 0/0 seguem refutados. Motor puro (com vocab) nos 203 golds antes deste refinamento: 182/203, 21 erros = 8
confiantes + 13 flagados; residual para o LLM 35 (17/100); teto com LLM ~195/203.
**Ancora como faixa (medido antes de codar, +4/0, 2 err->err, 0 perdas):** os 4 `exemplo-criacao-de-processos` do SO (pasta
sem data postada DEPOIS de "19/03 Estruturas de Controle") caiam na janela-1 da ultima ancora (bloco-04); o texto ("processos")
aponta o bloco-03. Regra (em `card_stream.card_windows`): modulo DATADO ("dd/mm Topico") fica no proprio bloco; modulo SEM data
da mesma secao recebe a FAIXA da secao (uniao dos blocos de todas as ancoras da secao, em ordem) e o desempate D4 decide —
"estrutura estreita, texto decide". Data PROPRIA = `extract_date_in_name` (titulo/moodle_label/card/basename), o mesmo sinal
do provider_date: a 1a versao olhava so o `moodle_label` e `14-04-troca-de-mensagens` (M365, label vazio) caiu na faixa
[06, 07] — curada 199 -> 198, corrigido no mesmo passe (teste `own_date`). Caveat: os 4 ganhos sao 1 pasta = 1 decisao;
o holdout CG nao tem ancoras (30/35 igual); FR/LR validam no item 8.
**Numeros (copias):** motor puro sem vocab 180 -> **183**/200 (SO 32 -> 35; conf-err 3), unidade 164 -> **168**, cobertura 51 ->
**54** (os exemplos passam a cobrir "processos"), subunidade 26 -> **30**; AULA 171 -> **175**/189 sem vocab (TODOS 187/203);
com vocab 179 -> **183** · 174 -> **178** · 50 -> **53** · 82, AULA 170 -> **174**/189 (TODOS 186/203). Gerador `b1d565a`. Curada 199/200 conf-err 0 · 191/191 · 55/57 · 93/93; sentinela 0 nos 8 (nenhum tutor muda: no curado o
voter ja decidia os 4). Suite 2276.

## GATE DA FASE 3 (item 7) — REGISTRADO 03/09 sessao 4 (gerador `b1d565a` + docs)

As 3 linhas da regua (5 cursos com gold; "antes" = handoff 2026-09-02c, "depois" = HEAD):

| linha | bloco | conf-err | unidade | cobertura | subunidade | AULA (189) | TODOS (203) |
|---|---|---|---|---|---|---|---|
| motor puro sem vocab | 161 -> **184**/200 | 3 -> 3 | 158 -> **168** | 51 -> **54** | 26 -> **30** | 151 -> **175** | — -> 187 |
| motor puro + vocab (= o motor do produto) | 162 -> **183** | 3 -> 3 | 167 -> **178** | 50 -> **53** | 79 -> **82** | 152 -> **174** | — -> 186 |
| curada + LLM (originais) | 199 -> 199 | 0 -> 0 | 191 -> 191 | 55 -> 55 | 93 -> 93 | — | — |

Holdout CG (curso do semestre, gold 35): puro 27 -> 30, curado+LLM 34 = 34, conf-err 1 = 1. Censo nos 8 (originais): revisar/100
53,2 -> **51,7**, votos/100 33,8 -> **32,0**, llm-funil 18 -> 15, llm-na-janela 92 -> 89. `calibra_revisar .ablacao`: 39,4/100.
Criterios do gate: AULA ~174 **batido** (174 com vocab, 175 sem); curada intacta **batido**; motor puro ± vocab sem regressao
**batido** (REF 9 -> 8/10: 1 bibliografia do SO, flagada antes e depois); censo votos/100 caem **batido**; **residual flagado
em AULA <= 8/100 NAO batido: 35/189 = 18,5/100 (7 errados) + 8 errados nao flagados** — a meta supunha que as alavancas
desflagariam; elas decidiram e mantiveram a duvida honesta (janela-1 do card gateada, banda media). O balde e o do item 11
(LLM so nos flagados, contado). Perdas acumuladas dos itens 2-6 (6, todas MF/SO, 4 = "gold DEPOIS da postagem"):
MF exerciciosformalizacao-res, intro, introducao-zip, provas, terminacao; SO laminas-sockets-material-alternativo (bibliografia).
Ganhos 27, err->err 2. Erros confiantes fora do alcance do LLM (8): MF exerciciosdafny2, revisao, arvores, intro, listas,
terminacao, ES2 azure, TCC aula-17. Tutores: nenhum muda neste passe (sentinela 0 nos 8). Determinismo 0/8. Suite 2276.
Divida: escada da `regua_aula.py` stale (picks H9) — podar no item 9.

## HOLDOUT — CG, curso do semestre corrente (pedido do user 03/09: "ver se nao estamos fazendo overfitting")

Regua nova, roda a cada item: `_harness-2026-09-02/holdout_cg.py <GEN> <COPY_DIR> [--no-sync]` = motor puro (sem curadoria,
sem voter, sem vocab) numa copia do CG, gold `ground_truth_CG.csv` scorable=yes (35). Baseline com o gerador PRE-item 2
(`b0b3b42`, worktree temporario): **27/35**, conf-err 1, flagados/sem bloco 19. Com o HEAD (itens 2-5): **30/35**, conf-err 1,
flagados 16. Ganhos = `animacao-v2`, `instanciamento`, `transformacoesgeometricas` (janela por topico de 9 blocos; "2d"
consagrado pelas sessoes do bloco-06 "processo de visualizacao 2d ..." — item 5, `disamb-curto`). Itens 3-4 NAO agem no CG:
o professor nao usa label datado nem data no nome (week_label vazio em 73/73) e nao ha material na secao 0 — ausencia de
sinal, nao overfitting; para testar 3-4 fora dos 5 e preciso um curso do semestre com labels datados (FR/LR: medir o Moodle
antes). Sobram: `matematica` (08 x 03, confiante-errado pre-existente), `transformacoes-geometricas-em-opengl` (15 x 06,
flagada, sem "2d" no texto), `modelagem-de-solidos`/`basico3d-cpp`/`basico3d-py-zip` (05 x 15, flagadas, janela de 2: "3d"
nao esta na assinatura de nenhum dos dois blocos). Precisao por faixa (HEAD, puro): confiantes 18/19 = 94,7%, flagadas 12/16 = 75%.
**CURADO + LLM** (`--curado`: sem ablacao, voter com cache, copia): **34/35 = 97,1%**, conf-err 1 (`matematica`), flagados 5,
metodos llm 15 · llm-funil 9 · disamb-curto 2 — igual ao 34/35 medido 03/09 madrugada com o codigo antigo; a linha do produto
nao mudou, o ganho dos itens 2-5 esta no piso sem LLM (27 -> 30).

## REGUA DE TRAVESSIA — baseline "antes" (02/09 noite) — **"depois" da C0 medido em 05/09: §C0 ITEM 12 (IA identico; FR 15/15; CG limitado pelo FILE_MAP 26/93)**

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
