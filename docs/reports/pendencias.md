# Pendências — tracker vivo

last_updated: 2026-09-05 tarde (sessao 6; REGUA AUTOMATICA = oficial: bloco 192/199, unidade 185/191, holdout CG 35/35, sub 82/93; CG unidade automatica 6/93 erradas; radical-fallback no motor; propagacao por headings no motor: sub puro 82 -> 87/93; C1 itens 1-3 FEITOS; gold pelo oraculo; Gemini com credito mas NAO usar ate o user mandar). **Ponto de entrada = handoff `2026-09-05b-handoff-fila-campanhas.md`** (sessao 6; o de 05/09 manha esta em `_archive/`) (regra
de fila do user: UMA campanha aberta, UMA proxima, o resto estacionado com "pronto quando"; anteriores em `_archive/`).
**Criterio estrito (user, 03/09 tarde): campanha so fecha com 100% dos itens.** Balanco: **C0 MOTOR 11/11 FECHADA em 05/09** (§C0 ITEM 12, 9, 10, 11a, 11b);
**SYNC 6/6 FECHADA em 04/09** (S6f promovido + complemento: CG `e3d02ed`, 93 entries; holdout puro 31/35, curado 33/35 aceito pelo user com causa medida; §SYNC S6f).
**FILA:** 1 ABERTA = **C1 TRAVESSIA** (FILE_MAP completo e magro; entrada = §C0 ITEM 12) · 2 PROXIMA = C3 provas/listas (ordem registrada; posicao da C7 e decisao do user na fronteira) · estacionadas: C7 imagens ·
C2 bibliografia · C4 limpa · C5 dividas de dados · C6 web. Ideias novas vao para a CAIXA DE IDEIAS do handoff.
Numeros vivos: §GATE DA FASE 3, §HOLDOUT, §REGUA DE TRAVESSIA. Tracker CORTADO em 03/09: historico (MOTOR PURO ate campanhas 1-3,
4.8k linhas) em `_archive/pendencias-historico-ate-2026-09-02.md`; aqui so o vivo. Documentos vivos = este + handoff 2026-09-03b +
plano 2026-09-02 (desenho/decisoes, carimbado).

## DE ONDE VEM O TEXTO QUE O MOTOR LE — STAGING x APROVADO, ONDE O DATALAB ENTRA, SUMARIO INJETADO (07/09; user: "automatizar a curadoria; o produto nao pode se moldar a uma API paga; medir com os aprovados antes do passo 1")
**Precedencia (medida, `navigation._entry_markdown_path_for_file_map:71`):** `approved_markdown` > `curated_markdown` > `base_markdown` >
`advanced_markdown`. Estado nos 8 (`c1-3/fonte_do_texto.log`): MF le approved 51 + base 2 · SO 38 approved · IA 55 · ES2 27 · TCC 27 ·
**CG le base 76+5 · LR base 7 · FR base 17** (staging = MD nao aprovado no Curator Studio). 305 de 348 materiais tem texto.
**O `advanced_markdown` DO DATALAB NUNCA FOI LIDO PELO MOTOR (achado que corrige a premissa):** os 198 textos aprovados vieram, todos, do `base_markdown`
(**pymupdf4llm**, biblioteca livre) — jaccard de linhas >= 0,9 contra o base e < 0,9 contra o advanced, em 198/198. O Datalab gerou
`advanced_markdown` em 163 entries (MF 34 + marker 9, SO 31, IA 28, ES2 27, TCC 27, CG 21, LR 7, FR 15) e **nenhum desses arquivos entrou no
caminho de atribuicao**. **POREM o Datalab ENTRA no texto do motor por outra porta (correcao 07/09, lembrete do user):** as DESCRICOES DE
IMAGEM sao geradas pelo Datalab (`image_curation.pages[].images[].source == "datalab"`, 2011 imagens nos 8; 3 sem marca no MF) e sao
INJETADAS no markdown lido (`<!-- IMAGE_DESCRIPTION -->`), em ingles. Entao o texto-base e livre (pymupdf4llm) mas 142/305 materiais carregam
prosa do Datalab que pontua no scorer. Trocar o backend muda ESSAS descricoes — medida em `c1-3/ablate_descricoes.py` (remove os blocos e
remede).
**A aprovacao MUDA o texto (dois caminhos divergentes — inconsistencia a decidir):** `_approve_current` (aprovar UM) normaliza refs de imagem,
grava a fonte escolhida, copia e entao aplica `_clean_extraction_noise` (tira numero de pagina, separadores, linhas em branco) +
`_inject_executive_summary` (**insere no TOPO um bloco "## Sumario" com TODOS os headings do documento**). `_approve_all_pending` (aprovar
TODOS) so copia e injeta descricoes de imagem — **nao limpa e nao injeta sumario**. Por isso o estado e desigual: textos lidos com sumario
MF 19/53 · SO 28/38 · IA 25/55 · ES2 24/27 · TCC 26/27 · **CG 0/81 · LR 0/7 · FR 0/17**. Efeito esperado no motor: o lead e capado em 2600
chars (`extract_markdown_lead_text`) e pesa 1,6 por token / 2,8 por frase exata, headings 1,8 / 3,0; o sumario DUPLICA os headings dentro do
lead e pode empurrar o conteudo real para fora dele — mexe em score e, sobretudo, em MARGEM (o gate de `ambiguous` e 0,12 na subunidade e
0,15 na unidade). **Medido (`c1-3/simula_aprovacao.py`, copias em `.ablacao/aprovado/`, tripwire, 0 chamadas):** produto ANTES 245/288 (bloco 235/237, unidade 183/190, sub 193/233, fila 91, conf-err 19) -> DEPOIS **identico** em todos os eixos; so a fila sobe 3 (MF +1, CG +2). O estado do texto (staging x aprovado) NAO explica o holdout do CG: nao e preciso aprovar nada antes das alavancas.
**"ZERO LLM/SEM API PAGA" E SEM CHAMADA, NAO SEM INFLUENCIA:** o texto que o motor le contem **descricoes de imagem do Datalab** (bloco
`<!-- IMAGE_DESCRIPTION: ... -->`) em 142 de 305 materiais, em TODOS os cursos: MF 11/53 (186 chars medios) · SO 27/38 (552) · IA 23/55
(1634) · ES2 24/27 (474) · TCC 26/27 (420) · CG 18/81 (760) · LR 3/7 (240) · FR 10/17 (604). O motor nao chama LLM nem Datalab em nenhum regime,
mas o insumo desses materiais ja passou pelo Datalab. Etiqueta honesta: "sem chamada na atribuicao". O regime "sem servico externo em lugar
nenhum" e o de `ablate_descricoes.py`.
**MEDIDO — REMOVER AS DESCRICOES DO DATALAB MELHORA O MOTOR (`c1-3/ablate_descricoes.log`, copias em `.ablacao/sem-descricao/`, tripwire):**
produto com descricoes (hoje) 100% certo **245/288** · bloco 235/237 · unidade 183/190 · sub 193/233 · fila 91 · conf-err 19; **sem** as
descricoes **247/288** · bloco 235/237 · unidade 183/190 · **sub 195/233** · fila 89 · **conf-err 18** (CG 57 -> 59, sub 56 -> 58, conf-err
10 -> 9; TCC fila 7 -> 6; SO 10 -> 9; MF/IA/ES2 iguais). Removidos ~390 mil chars de prosa em ingles. Leitura: a descricao generica do
Datalab ("Three images illustrating smart home appliances") e RUIDO para a atribuicao. **Conclusao de arquitetura (nao "apagar descricao"):**
a descricao serve ao ALUNO (texto do tutor), nao ao scorer — o motor deve pontuar o texto SEM os blocos `IMAGE_DESCRIPTION`, mantendo-os no
markdown entregue. Alavanca barata: filtrar o bloco no `entry_signals` antes de pontuar (a medir com gate).
**Backlog de arquitetura (pedido do user, 07/09):** o produtor da descricao de imagem deve ser ESCOLHIVEL (Datalab | Gemini | Ollama local),
como ja e o backend de extracao; hoje esta fixo no Datalab. Ordem: motor primeiro, depois backends (Marker correto, MinerU) e o seletor de
descricao, com re-medicao nos aprovados.
**Consequencia para as reguas:** a comparacao in-sample (5 cursos) x holdout (CG) confunde DUAS variaveis — "afinado x nao afinado" e
"texto pos-aprovacao x texto cru". So depois de igualar o estado do texto o 67% do CG e comparavel com o 94-100% dos outros.
**Ordem acordada com o user (07/09):** igualar o texto (este experimento) -> passo 1 (ima de headings) -> demais passos. Backlog do user:
automatizar a curadoria de MD e trocar o backend de extracao (Marker correto, MinerU) DEPOIS do motor, com teste nos aprovados.

## CONSOLIDACAO DAS DUPLICACOES DO MOTOR (07/09; user: "vamos antes resolver essas duplicacoes"; inventario em `c1-3/inventario_motor_2026-09-07.md`)
**Metodo:** refactor SEM mudanca de comportamento, um grupo por commit. Gate por commit: suite verde + **zero-diff nos 8 tutores**
(`c1-3/zero_diff.py --base|--check`: copia com `staging/`, 1 reprocess com tripwire, snapshot de 1017 artefatos derivados sem build/, raw/,
BUILD_REPORT, STUDENT_STATE, updated_at, last_seen; compara com a referencia do mesmo dia). Achado no caminho: o `determinismo.py` de
02/09 ignorava `staging/` e reprocessava LR/CG/FR/MF SEM o texto dos materiais (base_markdown em staging) — valia como determinismo, nao
como fidelidade; a referencia contra o original dava 56 arquivos por isso + datas. Auto-consistencia do gate novo: 0/1017.
**Adendo do user (07/09):** os arquivos estao em `staging/` porque NAO passaram pelo Curator Studio (aprovacao do MD; aprovar move para
`content/curated/` e grava `approved_markdown`). Estado medido no manifest: LR 7/7 em staging · CG 76/93 (5 aprovados, 12 sem MD) · FR 17/22
· MF 2/66 (51 aprovados) · SO/IA/ES2/TCC 100% aprovados. Implicacao: o motor le `base_markdown` onde estiver, entao os numeros de CG/LR/FR
(holdout, placar, fila) sao sobre MD nao aprovado; a aprovacao pode editar o texto e mover o motor — remedir esses cursos apos a curadoria.
O gate zero-diff e o determinismo tem de copiar `staging/` para reproduzir o que o motor ve hoje (feito no zero_diff.py).
**Commits (gerador, nada pushed): A1 4f60bd0 · A2 0efa29a · B 46499aa · C 35cb99c.**
- **A1** tokenizador de card/bloco unico (`text.tokens.card_stop_tokens`; `_tokens` era byte-identico em `timeline/card_block` e
  `timeline/block_identity`) · regex de numero de unidade so em `file_map` (`window_provider` importa) · leitor unico de `moodle_label`
  (`models.core.moodle_label_text`; 6 copias: disambiguator, window_provider, sources/moodle, resolver_apply, artifacts/navigation,
  core/vocabulary_compile). Suite 2341 · zero-diff 0.
- **A2** removido o caminho legado `routing/anchor_placement.py` (412 linhas atras de `use_anchor_placement`, default False, nunca ligado em
  produto) + `tests/test_anchor_placement.py` + ramo da flag em `ops/pedagogical_regeneration.py`; comentarios em `models/core.py` e
  `file_map.py`. Suite 2335 · zero-diff 0.
- **B** listas de genericos/stopwords centralizadas em `text/stopwords.py` com conteudo identico (bloco recortado, nao retipado) e alias no
  modulo de origem: `UNIT_MATCHER_GENERIC` (unit_matcher), `UNIT_TITLE_GENERIC` (content_taxonomy), `SEMANTIC_TOKEN_STOPWORDS`
  (semantic_config), `LABEL_PART_STOP` e `TOPIC_FALLBACK_STOPWORDS` (index), `MOTOR_GENERIC_STEMS` (disambiguator; coverage_rules e
  resolver_apply importam o canonico), `TOPIC_SUPPORT_STOP` (content_taxonomy inline), `FILE_MAP_TITLE_ANCHOR_STOP` e
  `FILE_MAP_TOPIC_ANCHOR_STOP` (file_map inline). Guard de identidade em `tests/test_stopwords_consolidation.py`. Suite 2336 · zero-diff 0.
- **C (mecanico)** regex identicas viram uma so em `text/patterns.py`: `SECTION_NUM_PREFIX_RE` (window_provider = resolver_apply) e
  `DATE_DMY_RE` (sources/moodle = motor/card_stream). Suite 2336 · zero-diff 0.
**Ficam DOCUMENTADAS, nao unificadas (semantica diferente; unificar = mudar comportamento = medir antes):**
- tokenizadores: `text.tokens.motor_tokens` (normalize_match_text, camelCase, digitos fora, stems genericos, short_vocab) x
  `unit_matcher._tokens` (norm_ascii_lower + `[a-z]+` >= 3 + UNIT_MATCHER_STOPWORDS) x `content_taxonomy._topic_support_tokens` (stem-5,
  >= 4) x `index._specific_tokens`/`_timeline_specific_tokens` x `resolver_apply._tokens_headings`/`_toks` x `concept_resolver._concept_tokens`.
  Regra daqui em diante: quem tocar um deles migra ESSE call site para `motor_tokens` parametrizado, com zero-diff ou medida.
- "data no nome": `window_provider._DATE_PREFIX_RE` (dd/mm prefixo, `\b`) x `moodle._DATE_PREFIX` (aceita ano) x `card_stream._DATE_DM`
  (lookahead negativo) — tres contratos.
- "nome do curso e boilerplate": `window_provider._course_stems` (stems de _topic_tokens) x `disambiguator drop = _toks(course_name)` x
  `content_taxonomy course_norm` x `stopwords.resolve_unit_generic_tokens`.
- IDF/raridade x3 (file_map 1/df entre unidades; concept_resolver 1/freq entre blocos; stopwords df >= 0,4) e "token exclusivo" x3
  (unit_matcher, file_map distinctive, resolver_apply subtopico): eixos diferentes, formulas parecidas — candidatos a um helper quando um
  passo do plano os tocar.
- "a secao nomeia X" x2 (`window_provider.unit_named_by_section`, `resolver_apply._secao_nomeia_subtopico`): mesma forma, eixos diferentes;
  o passo 4 do plano (topico do bloco como ultimo recurso da subunidade) e o momento de unificar a forma.
- heranca de unidade por vizinho x2 (`file_map.unit_of_block_or_neighbor`, `index` soft-continuation): entry x bloco.
- codigo morto que FICA de proposito: `file_map.timeline_block_matches_preferred_topic` (passo 4 religa) e o parametro `block_confidence`
  de `reconcile_unit_with_block` (passo 2 religa).

## FILA DE REVISAO DO REGIME ZERO (SEM LLM) — ANATOMIA E RAIZES (07/09 madrugada; user: "um motor, camada LLM on/off; teto do puro; fila menor pela raiz")
**Regua (`c1-3/fila_zero.py zero`, snapshots de 06/09, 6 cursos, 319 materiais):** fila **137 (42,9/100)** vs automatica (LLM em cache) 90 (28,2).
Motivos: conflito 57 · flag:disamb 53 · '?' 11 · sub-empate 10 · sem-bloco 10 · sub-ambigua 6 · disamb-curto 4 · due-straddle 1. Rendimento:
fila&erra 64 · fila&certo (aviso vazio) 58 · sem gold 15. **ERROS CONFIANTES (fora da fila) 69: sub 65 (IA 29, ES2 13, CG 11, MF 7), bloco 4
(MF), unidade 4.** Os 11 '?' sao 'mudou' do CG herdado do produto no snapshot (artefato): fila real do zero = **126 (39,5/100)**.
**Por motivo (`fila_zero_motivos.log`):** conflito 57 -> erra 28 (unidade 5, sub 21, bloco 3), certo 22 · flag:disamb 53 -> erra 21 (bloco 8, unidade 3,
sub 15), certo 28 · sub-empate 10 -> erra 8 · sem-bloco 10 -> erra 4 (4 sem gold) · disamb-curto 4 -> erra 4 · due-straddle 1 -> erra 1 (MF t2, C1 resolve).
**Raiz 1 — 'conflito' (`fila_zero_conflito*.log`):** 40/57 tem bloco ancorado (>= 0,6); erro de unidade em 5/57 (SO 4 no bloco-06 cujo SARC diz
"gerencia do processador, sincronizacao E deadlock" = duas unidades; IA 1 em bloco de conf 0). Politica raiz simulada: conflito so e duvida se o
bloco e fill (< 0,6) OU o label do SARC do bloco toca >= 2 unidades (tokens exclusivos): **saem 26, ficam 31 com os 5 erros; 0 erro escondido**.
**Raiz 2 — duvidas de bloco x posicao do professor (`posicao_duvidas_zero.py`, 68 itens):** sem posicao 35 (CG 34: Moodle sem data) · posicao
com 2-4 blocos 31 (MF/IA: label "Semana X a Y" cobre 2 aulas; contem o gold 25/31; estreita a janela atual em so 5: o provider 'labels' ja usa)
· posicao unica 2 (1 != gold). Os 4 erros confiantes de bloco (MF) tambem estao em posicao multipla. => O que resta de duvida de bloco e escolher
entre as 2-4 aulas da mesma semana/secao: o unico sinal deterministico nao usado e a ORDEM dos modulos dentro do label/secao (alavanca medida em
02/09: +7/-1 e +12/-5, fora do motor). No CG, sem datas, a ordem das secoes x ordem do SARC.
**Raiz 3 — subunidade:** 20 duvidas (empate 10, ambigua 6, curto 4; erram 15) e 65 erros confiantes: ima de headings (IA 29), pai x filho (CG 10),
'OpenGL' (CG 9, vocab), 48 sem o nome em fonte nenhuma. Sinais deterministicos para desempate: sessao do SARC do bloco nomeia o subtopico
(9 inteiros / 36 parciais), secao (S1b ja entrou), titulo (ja entrou).
**Tensao a decidir:** as correcoes de raiz para erro confiante (ima, token compartilhado) AUMENTAM a fila (viram duvida) antes de diminui-la; as
que diminuem sem esconder erro sao: politica do conflito (-26), cerca (+3 acertos), C1 (-1), artefato 'mudou' (-11), ordem dos modulos (a medir).

## MEDICAO DAS SALAS NOS 8 CURSOS (06/09 noite; user: "concordo com os 5; medir para fundar e ver se replica") — `c1-3/mede_salas.py`, log `mede_salas.log`
**Cobertura:** 30 salas em 6 cursos (IA 18, SO 3, TCC 3, LR 3, MF 2, ES2 1; CG e FR 0 visiveis — 87 modulos "sem acesso" na conta do aluno).
**C3 (duracao abertura -> vencimento) replica onde o professor define abertura:** IA e LR definem (21 salas): atividade de aula (<= 26 h) 12 ·
curta (1-5 dias) 6 · trabalho (>= 7 dias) 4 (IA T1 672 h, T2 645 h, 3b, video do T2). MF, SO e ES2 so definem vencimento (4 + 1 curta): o
classificador precisa de fallback por nome ("T1", "Trabalho", "TP") e secao (TDE, "Informacoes Gerais"). **TCC so define FECHAMENTO** (cutoffdate:
20/03, 25/06, 08/07) — sem duedate; fallback para cutoffdate.
**C5 (vencimento x SARC) replica: 10 de 11 trabalhos coerentes sem gold.** MF T1 06/05 -> bloco-11 deliverable · MF T2 06/07 -> bloco-20 "prova
p2, entrega do t2" · SO TP1 14/05 -> bloco-14 "apresentacao tp1" · SO TP2 02/07 -> bloco-23 "apresentacao tp2" · IA T1 04/05 -> bloco-09
"apresentacao do t1" · IA T2 29/06 -> bloco-19 "apresentacao t2" · ES2 Trabalho Final 06/07 -> bloco-13 "prova p2, entrega trabalho final" ·
LR 3 salas -> blocos deliverable do proprio dia · TCC T1 fechamento 20/03 -> bloco-04 "t1 em aula". Unico desvio: TCC T2 fecha 25/06 e o SARC
entrega em 12/06 (fechamento e posterior a apresentacao). Vencimento por kind do bloco: deliverable 10 · class 11 (atividades de aula) ·
assessment 2 (C1: MF T2, ES2 TF) · office_hours 2 (IA atividades 8/9 em "duvidas para t1") · holiday 1 (IA "integrantes", 26/06 suspensao).
**C1 replica:** 2 de 11 trabalhos vencem dentro do bloco da prova (MF T2, ES2 TF); hoje o due-window os manda para a aula anterior (T17).
**C2:** escopo da prova por data ja existe (`scope_unit_slugs`); o plano declara em MF/TCC/ES2/FR; conflito com o calendario em MF (U2 depois da
P1) e no FR do zero (IP/ICMP antes da P1 com U4). Precedencia proposta: calendario (SARC) > plano.
**C4 — LACUNA CONFIRMADA e maior que a IA:** 10 anexos de salas, 10 fora do tutor. IA: `T1_IA_2026_01_t32.pdf` (3 pag, "T1 - Tic Tac Toe com
ML") e `T2_AlgoritmosDeBusca_2026_01.pdf` (2 pag, "T2 - Algoritmos de Busca: Olimpiada") baixados pela API e conferidos (scratchpad, fora do
tutor); mais dados da Atividade 1 (19 MB), `cardio_v2.csv`, A* v2, casos de teste. **SO: `TP1_20261.pdf` e `TP2_20261.pdf` (enunciados dos
trabalhos) tambem so existem como anexo da sala** + o codigo do "Somatorio em Java". Os tutores de IA e SO nao tem os enunciados dos trabalhos.
Correcao na sync/pull: baixar `introattachments` (fileurl + token) e o `intro` de cada sala como material (categoria trabalhos/exercicios por C3).
**Achado colateral APURADO (`file_dues_exposicao.log`):** causa = o card "Verificacao de Programas" do MF termina num FORUM "Sala de Entrega (10/06)";
`_module_due` (moodle_labels.py) aceita assign/forum com "entrega" + "(DD/MM)" no nome como vencimento 'named', e `extract_file_dues` e posicional
SEM fronteira de grupo: cada arquivo herda o vencimento do PROXIMO modulo-com-due da secao. Como o forum e o ultimo modulo, os 30 arquivos
(54 chaves = filename + savename) de 27/04 a 12/06 herdam 10/06. Exposicao hoje: ZERO (nenhum entry desse card esta no escopo do due-window;
os 3 entries em escopo do MF sao do TDE, fonte 'structured'). Nos 8 cursos so o MF tem `file_dues`; SO e IA tem `assign_due` por card mas nenhum
arquivo ligado (TP1/TP2 do SO e atividades da IA sao ANEXOS da sala, que a sync nao traz); ES2/TCC nada; LR/CG/FR sem card_block_map (sync
antiga). Conclusao: a ligacao arquivo -> vencimento hoje so existe por acidente de layout (recurso antes do assign na mesma secao). Correcao
(dentro do item 4): ligar anexos e arquivos do MESMO grupo de label ao assign (estruturado) e limitar a heranca posicional ao grupo; forum
nomeado so vale para o grupo dele. Os "31 sem entry" da primeira apuracao eram savenames duplicados, nao lacuna.

## SALAS DE ENTREGA PELA API — ABERTURA / VENCIMENTO / FECHAMENTO, ATIVIDADE DE AULA x TRABALHO, ANEXOS AUSENTES (06/09 noite; perguntas do user)
**API (medido ao vivo, token do aluno, 0 chamadas Gemini):** `mod_assign_get_assignments(courseids)` devolve por sala `allowsubmissionsfromdate`
(abertura), `duedate` (vencimento), `cutoffdate` (fechamento), `gradingduedate`, `timemodified`, `intro` (enunciado HTML) e `introattachments`
(arquivos do enunciado); 29 modulos vieram como "sem acesso" (ocultos ao aluno). `core_course_get_contents.dates` ja traz "Aberto:" e
"Vencimento:" (IA 18, LR 3, ES2 1; MF e SO so vencimento; TCC/CG/FR nada). Fechamento: so 1 sala da IA (Atividade 1); MF nenhum.
**IA (18 salas) — o catch do user, separavel pela duracao abertura -> vencimento:** <= 26 h = ATIVIDADE DE AULA (10: Atividades 1, 3a, 4, 5, 6, 7,
10, 11, 12 e Casos de Teste; vencem 21:50-22:30 do dia da aula) · 3-5 dias (4: Atividades 2, 8, 9 e "integrantes") · >= 7 dias = TRABALHO (T1 672 h,
06/04 -> 04/05; T2 645 h, 03/06 -> 29/06; Atividade 3b 168 h; video do T2 189 h). Nome ("T1", "Atividade de Aula N") e secao (TDE) confirmam.
Coerencia com o SARC sem gold: T1 vence 04/05 = "apresentacao do T1" 04/05-06/05 (blocos 09/10); T2 vence 29/06 = "apresentacao T2" 29/06 (bloco 19).
Para o bloco, a regra "bloco que contem o vencimento hospeda" serve aos dois casos: atividade de aula vence no dia da aula -> bloco-aula do dia;
trabalho vence na entrega -> bloco da entrega (deliverable ou prova). O catch e de CATEGORIA (exercicio de aula x trabalho da media), nao de bloco.
**LACUNA (medida):** os `introattachments` nao entram no pull nem no tutor: IA `T1_IA_2026_01_t32.pdf`, `T2_AlgoritmosDeBusca_2026_01.pdf`,
`Atividade_Dados2026.zip`, `AlgoritmoAStar_v2.zip`, `casoDeTeste32.zip` ausentes; manifest da IA tem 0 entries 'trabalhos'. O aluno nao tem os
enunciados dos trabalhos da IA no tutor (`cardio_v2.csv` existe por outro caminho). Sync/pull: trazer anexos e `intro` das salas.
**Bloco de prova com unidade (pergunta do user):** faz sentido = escopo da prova. O motor ja calcula `scope_unit_slugs` por data
(`apply_assessment_review_scope`); o plano declara o escopo em MF/TCC/ES2/FR (AVALIACAO). Conflito real: MF plano "P2 = unidade 3" x calendario
(unidade 2 ensinada depois da P1: escopo por data = U2+U3). Precedencia a decidir: calendario (SARC) > plano.
**Conclusoes para o motor (propostas; so C1 decidida; nada medido):** C1 vencimento dentro de bloco de prova hospeda (inverte T17). C2 bloco de prova
recebe `unit_slugs` = escopo, e material hospedado escolhe a unidade DENTRO do escopo pelo conteudo (unit DP restrito). C3 sala com span <= 1 dia =
atividade de aula -> bloco-aula do dia, categoria exercicios; span >= 7 dias ou TDE/"T<n>" = trabalho -> bloco do vencimento. C4 sync traz
`introattachments` + `intro` como material e descricao do professor (texto deterministico para bloco/subunidade). C5 regua sem gold: vencimento x
sessao "apresentacao/entrega" do SARC. Gate: motor puro + suite; gold so mede.

## BLOCO DE PROVA HOSPEDA ENTREGA (decisao do user 06/09 noite) — GOLD DO T2 DO MF -> BLOCO 20; DATAS DE ENTREGA JA ESTAO NO PULL
**Gold (docs):** `ground_truth_MF.csv` t2-2026-1 true_block bloco-18 -> **bloco-20** ("prova P2, entrega do T2", 06/07, kind assessment; Moodle
'Sala de entrega' vencimento 06/07/2026 23:59). Bloco de prova nao tem unidade (gold_units 'FORA DA REGUA'): o T2 sai da regua de unidade
(191 -> 190). **Remedido:** produto bloco 198 -> **197/199** (o motor ancora o T2 em bloco-18 por desenho, abaixo), unidade 183/190, sub 193/233;
placar por material zero 156 -> 155 · automatica 231 -> 230 · produto 246 -> 245 (`placar_100_gold_mf.log`).
**Datas de entrega pela API (pergunta do user):** SIM, e ja estao no pull: `core_course_get_contents` devolve, em cada modulo `assign` ("Sala de
entrega"), `dates: [{label: 'Vencimento:', dataid: 'duedate', timestamp}]`. Nos pulls de 06/09: IA 18/18 assigns com vencimento · LR 3/3 · MF 2/2
(06/05 e 06/07) · SO 2/3 · ES2 1/1 (Trabalho Final 06/07) · TCC 0/3 (salas sem prazo) · CG 0 · FR 0. `mod_assign_get_assignments` daria ainda
allowsubmissionsfromdate/cutoffdate/intro; nao e necessario para a data de entrega.
**O motor ja usa a data (tier 2 `motor/due_window.py`, spec 2026-07-22 + F5b):** casa arquivo -> vencimento por filename/stem e, por desenho
(T17, 2026-08-06), **so bloco de CONTEUDO ancora**: vencimento dentro de prova/revisao -> "ultimo bloco de conteudo anterior", confianca media +
FLAG (method `due-straddle`). Foi exatamente isso no T2: vencimento 06/07 dentro do bloco-20 (P2) -> bloco-18 (29/06). **Candidata C (a
decisao do user inverte o T17):** vencimento contido em bloco `assessment` ancora nele (review/feriado seguem excluidos). Alcance estatico: MF T2;
ES2 Trabalho Final (vencimento 06/07 dentro do bloco-13 "prova P2, entrega trabalho final"); TCC sem prazo nas salas. Gate: motor puro + suite.

## LEI REAFIRMADA: SARC E MOODLE > GOLD — GOLD DO ES2 CORRIGIDO PELO ORACULO E CRIVO DAS 7 DIVERGENCIAS (06/09 noite, sessao 6; user: "se o gold estiver diferente do SARC/Moodle, e mais provavel que eu tenha errado o gold")
**Correcao (docs, gold so mede):** `tests/fixtures/eval/gold_units_ES2.csv` bloco-04 (10/04-24/04: discovery, api gateway, exercicios de revisao
para P1) true_unit unidade-02 -> **unidade-01-arquitetura-de-software** (7 materiais: revisao-p1, roteiro2, roteiro3, microsservicos2,
microsservicos3, roteiro2-nameserver, roteiro3-gateway). `docs/reports/subunit_gt_ES2.csv`: os 6 pontuaveis 2.7 -> **1.5
`estudo-de-caso-arquitetura-orientada-a-microsservicos`** (revisao-p1 segue scorable=no). Evidencia do professor: plano "P1 contempla a secao 1",
P1 no SARC em 08/05, label do Moodle de 24/04 "exercicios de revisao para P1". Bloco-07 (circuit breaker, 15/05, apos a P1) fica na 2.7.
**Remedido (`placar_100_gold_es2.log`, snapshots de 06/09; produto `eval_eixos`):**

| regime | 100% certo / 288 | 3 golds certos / 146 | bloco | unidade | subunidade |
|---|---|---|---|---|---|
| zero LLM | 155 -> **156** | 65 | 222/237 | 173 -> **180/191** | 117/233 |
| vocab (5 cursos, 205) | 173 -> 166 | 125 -> 119 | 188/202 | 183 -> 176/191 | 138 -> 132/151 |
| automatica | 238 -> **231** | 131 -> 125 | 231/237 | 185 -> 178/191 | 193 -> 187/233 |
| produto | 253 -> **246** | 138 -> 132 | 236/237 | 191 -> **184/191** | 199 -> 193/233 |

ES2: zero 6 -> 7/31 (unidade 18 -> 25/28) · automatica 28 -> 21 (unidade 28 -> 21, sub 26 -> 20) · produto 29 -> 22 (unidade 28 -> 21, sub 27 -> 21).
Leitura: o produto e a automatica seguiam o alias 'API gateway'/'discovery' que o vocab LLM pendurou na 2.7; o gold, feito junto com a curadoria,
concordava (in-sample). O oraculo discorda dos dois: **7 erros de unidade e 6 de subunidade do LLM estavam escondidos pelo gold**; o motor puro
sem vocab, que preenche por posicao, estava certo. Nos 93 dos 4 cursos afinados o produto passa de 93/93 para 86/93 e a automatica de 87 para 81.
**Crivo das outras 7 divergencias gold x posicao no Moodle (`coerencia_moodle.log` / `auditoria_gold.csv`), pela mesma lei:**
- ES2 roteiro1, roteiro1-introducao (Moodle -> bloco-01; gold bloco-02): MANTIDO. Na secao 'Microsservicos' o Roteiro 1 esta entre o label
  "Semana 30/03 a 03/04: feriado" e o label "10/04: discovery"; a auditoria pulou o label do feriado (sem bloco-aula) ate o de 20/03. O
  professor o pos logo apos a aula de 27/03 "microsservicos no Spring (introducao)" = bloco-02. Artefato da heuristica, nao do professor.
- TCC 3dm-caetano..., programacao-inteira-01-20260617 (Moodle 'secao' -> bloco-22/23; gold bloco-25): MANTIDO. Secao "Semana 14 - Apresentacoes
  T2" sem data; SARC "oficina de problemas, entrega T2" em 12/06 = bloco-25.
- SO laminas-cs-4244-sockets, laminas-sockets-alternativo (Moodle 'faixa de irmaos' -> bloco-06/07; gold bloco-09): MANTIDO. No card, o label
  "Sockets" vem depois de "14/04 IPC (pipes, fifo)"; o SARC de 23/04 (bloco-09) e "comunicacao entre processos, pipes, filas". A 'faixa' e o
  intervalo dos irmaos datados, nao uma afirmacao sobre sockets.
- MF t2-2026-1 (Moodle label "Trabalho 1 (06/05)" -> bloco-11; gold bloco-18): a posicao do Moodle e artefato (o label "Trabalho 2:" nao tem
  data e a auditoria herdou o do T1). Mas o gold bloco-18 (aula "verificacao de modelos, ferramenta", 29/06; relabel de 25/08) nao tem
  evidencia do professor: o SARC diz "prova P2, entrega do T2" em **06/07 = bloco-20 (kind assessment)**, e o texto do T2 cita Dafny 3x (nao
  cita NuSMV/Kripke). Nenhum gold dos 6 cursos aponta para bloco de prova (kinds no gold: class, deliverable, review, overview). **ABERTO
  (decisao do user):** gold -> bloco-20 (bloco de prova passa a hospedar entrega) ou scorable=no.

## ES2 UNIDADE SEM LLM — 'MICROSSERVICOS' EM DUAS UNIDADES, CERCA DE PROVAS E GOLD SUSPEITO (06/09 noite, sessao 6; user: "como arrumar esse tipo de erro? o plano tem 3 entradas?")
**Plano de ES2 (fonte `subjects.json`):** 5 ocorrencias de 'microsservicos' (sempre com dois s): 3 topicos (1.3.4 Orientada a Microsservicos e 1.5
Estudo de caso, na unidade 01; 2.7 Estudo de Caso: integracao e implantacao, na unidade 02), 1 na ementa, 1 na bibliografia. Token presente em
duas unidades nao e evidencia: o DP de blocos ja o trata assim (fill 0,4), mas o scorer de unidade da ENTRY nao — as 10 unidades erradas do ES2 no
zero sao CONFIANTES (uconf 0,77-0,98, winner_score 15-58) porque a unidade 01 tem mais aliases contendo a palavra (1.3.4 + 1.5). Dos 18 erros de
unidade no zero, 11 confiantes e 7 na fila. Candidata A (nao medida): token compartilhado por >= 2 unidades vale 0 tambem na entry -> vira duvida.
**Moodle de ES2:** secoes sem nome; labels com 'secao' = 'Revisao' / 'Microsservicos' (20/03 a 12/06, tudo) / 'DevOps' (22/06+). Nao separa 1.5 de 2.7.
**Cerca de provas (`c1-3/simula_cerca_provas.py`, estatico, snapshots zero + FR do zero):** o plano diz o escopo (MF P1 = U1+U2, P2 = U3; TCC
P1 = U1-3, P2 = U4; ES2 P1 = secao 1, P2 = 2 e 3; FR P1 = U01-03, P2 = U04-06; IA 'ate a data'; SO/LR/CG nada) e o SARC da a data. Como regra
DURA: MF blocos 10/12/13/15 (Hoare, Dafny; U2, conf 0,6-0,8) ficam entre P1 e P2 e o gold confirma U2 em 17/17 -> quebraria 17; TCC bloco-18
'correcao prova p1' (U3 apos P1, 0 gold); FR do zero blocos 07-09 (IP, ICMP; U4 antes da P1, 0 gold); ES2 bloco-07 (circuit breaker, fill 0,4,
apos P1) -> U2/U3, gold 3/3 concorda. Como DESEMPATE so de bloco sem sinal proprio (conf 0,4): +3 (ES2 bloco-07), 0 perdas nos 101 golds dos 4
cursos. Candidata B, gate pendente (motor puro sem vocab).
**GOLD SUSPEITO (decisao do user):** ES2 bloco-04 (10/04 discovery, 17/04 api gateway, 24/04 'exercicios de revisao para P1' no label do Moodle)
vem ANTES da P1 de 08/05, que pelo plano contempla so a secao 1. O gold de unidade poe os 7 materiais desse bloco (revisao-p1, roteiro2, roteiro3,
microsservicos2, microsservicos3, roteiro2-nameserver, roteiro3-gateway) na unidade 02 (sub 2.7). Pelo oraculo (plano AVALIACAO + SARC + label do
Moodle), sao unidade 01, subtopico 1.5 'Estudo de caso: arquitetura orientada a microsservicos'; circuit breaker (15/05) e implantacao (22/05)
ficam na 2.7. Se o gold mudar: zero +7 unidade; produto/automatica (que seguem os aliases LLM 'API gateway' da 2.7) -7. 'revisao-p1' na unidade 02
com a P1 cobrindo a secao 1 e o sinal mais claro de que o gold esta errado ali.

## ZERO LLM — DIAGNOSTICO DOS 133 QUE NAO ESTAO 100% (06/09 noite, sessao 6; user: "como aumentar o 100% no zero LLM?")
**Decomposicao (`c1-3/diag_zero.py zero`, snapshot `snap_placar/zero`, log `diag_zero.log`):** so sub 102 · unidade+sub 9 · bloco+sub 5 · so unidade 7 ·
so bloco 8 · bloco+unidade 2. Sub: 97 erradas, 10 vazias, 9 gold-vazio, 8 empates. Unidade 18: ES2 10 (blocos 04/07 sem sinal proprio), SO 5 (so o
voter resolve), IA 3. Bloco 15: 10 flagados (o voter resolve), 5 confiantes; 6 com o gold fora da janela, 2 sem bloco.
**Onde o nome do subtopico do gold aparece (`diag_zero_texto.log`, 107 erros com gold nao vazio):** em fonte NENHUMA 48 (IA 27, CG 14, SO 4, MF 3)
— irredutivel sem ponte de conceito (vocab LLM, glossario humano, ou dicionario de dominio compilado uma vez e reaproveitado; hipotese); em alguma
fonte 59: texto do material (rotulo inteiro) 26, sessao do SARC 9 inteiros / 36 parciais, secao 6 / 33, titulo 4 / 15.
**Ima de headings na taxonomia (raiz lida em `content_taxonomy.py`, laco `for heading in heading_sources`):** heading do Moodle e grudado no
topico com maior sobreposicao de tokens (5,0 + 0,4 por token), e a sobreposicao pode ser um unico token que e do titulo da unidade
('aprendizado'); empate vai para o primeiro da lista. IA: 'Introducao ao aprendizado de maquina' recebe 'Aprendizado Supervisionado', 'Aula 02 -
... k-Means', ... e vira ima: 35 erros confiantes (score ate 90). Estatico nos 6 (aliases nao-LLM grudados so por token da unidade): MF 8, TCC 7,
IA 6, SO 1, ES2 1, CG 0 = 23. Correcao candidata: sobreposicao sem tokens do titulo da unidade, sem grudar em empate. NAO MEDIDA (gate: motor
puro sem vocab nos 6, 0 chamadas). Expectativa: IA 35 confiantes viram vazio/empate (fila), 8 com 'Modelos Preditivos' no texto podem acertar.
**ES2 unidade — 'microservicos' (SARC) x 'microsserviços' (plano), pergunta do user:** o normalizador faz o que o user disse (microsserviços ->
microsservicos); o SARC escreve 'microservicos' (um s) em 3 de 4 sessoes e um s de diferenca nao casa por token exato. MAS nao e a causa da unidade
errada: medido com `assign_units_positional` sem vocab LLM e o SARC reescrito na grafia do plano, os blocos 04 e 07 continuam na unidade 01 com
conf 0,4 (fill posicional), porque 'microsservicos' esta nas DUAS unidades (1.3.4/1.5 e 2.7) e token em duas unidades nao decide; o bloco 02, que
ja usa a grafia do plano, prova (unidade 01, 0,4, nos dois regimes). O que decide com vocab sao os aliases LLM de 2.7 ('API gateway', 'discovery').
Sem LLM, as palavras do SARC dessas sessoes (spring, discovery, gateway, circuit breaker) nao existem no plano. Casamento tolerante (ss ~ s) e
barato mas rende 0 aqui.
**Ressalva:** o regime zero le o GLOSSARY.md do tutor (sinonimos escritos no build original); o unico build zero de verdade e o FR do zero run A.

## PLACAR CONSISTENTE POR MATERIAL x REGIME + TELA DE LOGIN (raiz e correcao) + REPARO DO CG (06/09 noite, sessao 6; user: "quantos arquivos estao 100%? qual versao do motor deu qual resultado?")
**Tela de login — raiz medida (nao e timeout nem desconexao):** a sync (`moodle_sync.plan_import`) criava, para cada pagina do Moodle
(`mod/page`), uma entry `url` -> `moodle.pucrs.br/mod/page/view.php?id=N`; o conversor de URL (`url_fetcher`) busca sem sessao e o Moodle
devolve a tela de login. O pull ja salvava o HTML real (com token) em `<pull>/raw/moodle/pages/<N>-<slug>.html` e a sync nao o usava.
**Correcao definitiva na sync (`6d68578`):** `plan_import(root=...)` prefere o HTML salvo (entry `html`, MESMO id via `id_override`) e so cai
para URL quando nao ha HTML; teste `test_pagina_do_moodle_com_html_salvo_vira_entry_html_com_o_mesmo_id`. Curso novo: a pagina nasce com texto.
**Reparo registrado do CG (`c1-3/repara_paginas_cg.py`, CG `404f5f9`, tripwire, 0 chamadas):** 16 entries url -> html com o texto real
(275-2281 chars, login=nao), ids/golds/curadoria intactos; bloco 0 mudancas; build incremental local + reprocess.
**Efeito do reparo no gold de subunidade do CG (82):** produto 58 -> 56 (+3 -5) · automatica 58 -> 55 · holdout puro 47 -> 45. Ganhou 3
(deteccao de colisao, introducao ao processamento, morfologia: paginas antes vazias). **Perdeu 5 paginas-INDICE de videos** (curvas
parametricas -> hermite 4,84; manipulacao de imagens -> segmentacao 4,46; modelagem geometrica -> csg 8,58; visualizacao 3d -> paralela 12,40;
mapeamento -> empate exato 4x): o texto real lista videos de varios filhos do topico, o vocabulario puxa o filho mais citado, e o gold (= a
secao do Moodle) e o topico-pai. Antes, com o texto de login, o titulo sozinho caia no pai por acaso (winner_score 0,12-0,94). E a classe
"pai x filho" ja diagnosticada (5): agora 10 dos 27 residuais. **Candidata (hipotese, nao medi):** texto que cobre >= N irmaos com forca
comparavel -> subtopico-pai / o que a secao nomeia (S1 "sempre" foi medida em 06/09 e perdia; esta e mais estreita). Fila: 93 -> 96 (+3
sub-empate/ambigua nas paginas com texto) = **27,6/100** (CG 47 = duvida 25 + mudou 22 · MF 11 · SO 10 · IA 4 · ES2 12 · TCC 7 · LR 0 · FR 5).
**Placar consistente (`c1-3/placar_100_runs.py` + `placar_100.py`; snapshots `snap_placar/{zero,vocab,auto}/`, produto = originais; tripwire, 0
chamadas; CG apos o reparo):** 288 materiais com algum gold nos 6 cursos (bloco 237, unidade 191, subunidade 233); 146 com os TRES golds
(so nos 5 cursos: o CG nao tem gold de unidade). "100% certo" = acerta todos os eixos em que tem gold.

| regime (o que usa de LLM) | 100% certo / 288 | 3 golds certos / 146 | bloco | unidade | subunidade |
|---|---|---|---|---|---|
| zero LLM: sem vocab, sem voter, sem curadoria | **155 (53,8%)** | 65 (44,5%) | 222/237 | 173/191 | 117/233 |
| vocab (1 chamada por curso), so os 5 cursos | 173/205 (84,4%) | 125 (85,6%) | 188/202 | 183/191 | 138/151 |
| automatica = vocab + voter com cache (tutor novo) | **238 (82,6%)** | 131 (89,7%) | 231/237 | 185/191 | 193/233 |
| produto = + curadoria humana | **253 (87,8%)** | 138 (94,5%) | 236/237 | 191/191 | 199/233 |

Por curso (100% certo / com gold), zero -> automatica -> produto: MF 50 -> 56 -> 59 /66 · SO 27 -> 32 -> 39 /39 · IA 3 -> 39 -> 42 /42 ·
ES2 6 -> 28 -> 29 /31 · TCC 23 -> 27 -> 27 /27 · **CG 46 -> 56 -> 57 /83**. Leitura: sem vocab a subunidade e 50% e a IA vai a 4/39 (o plano
nomeia categorias, o material nomeia algoritmos; ES2 unidade 18/28 sem vocab, 28/28 com); o vocab (1 chamada) leva os 5 cursos afinados a 85%
por material; o voter paga bloco (+7 nos 5: 189 -> 196/202; CG 33 -> 35) e nada de subunidade; a curadoria paga 15 materiais. **O numero para planejar um tutor
novo e o do CG automatica: 56/83 = 67% dos materiais com bloco E subunidade certos (bloco 35/35, sub 55/82); sem LLM nenhum, 46/83 = 55%.**
Os 4 cursos afinados dao 94-100% no produto porque a curadoria nasceu com o gold (in-sample).
**Sem gold (FR do zero, 20 materiais, sandbox):** run A (0 chamadas) unidade 19/19 pela secao do professor; concorda com o FR curado em bloco
13/20, sub 11/20; fila 10/20. Run B (Gemini ~22 chamadas) concorda 19/20, 20/20, 17/20; fila 6/20.
**O que falta para o tutor 100% automatico (medido, nao opiniao):** (1) a ponte de vocabulario categoria -> algoritmo, unica coisa que hoje so o
LLM da (+57 sub/+10 unidade nos 93; sem ela IA 4/39); fontes deterministicas ja tentadas e refutadas: IDF/similaridade/card/stem; (2) posicao
datada no Moodle (labels "Semana dd/mm"): existe em 5 cursos, nao em CG/LR/FR, e e o que faz o bloco sem voter (CG puro 33/35); (3) ordem dos
modulos na secao (API do Moodle, ja no pull): alavancas medidas em 02/09 (+7/-1 e +12/-5) e ainda fora do motor; (4) regra pai x filho acima.
Gold: so mede; o aluno nunca cria gold.

## CAUSA RAIZ DAS DUVIDAS DE BLOCO — JANELA ∩ UNIDADE DA SECAO + FILA SEM CERIMONIA (06/09, sessao 6; user: "encontrar o real motivo")
**Anatomia medida (produto, 8 cursos, 38 duvidas de bloco; gold de bloco onde existe):** janela-1 flagada 21 ("sinal indireto" por desenho; janela de
1 bloco por data no nome 9 / topico da secao 12) **14/14 certos** · funil com voto 16 (flag mantida por desenho apos o LLM decidir) **1/1 (+5/5 em
05/09)** · due-straddle 1 (1/1). **37 avisos por 0 erros de bloco = cerimonia**, como a camada llm. Nas copias automaticas: identico (14/14, 1/1).
**FR do zero (A2), 10 duvidas de bloco, causa ESTRUTURAL:** 8 vem do provider 'topic': os tokens do nome da secao ('camada', 'aplicacao') casam sessoes
do SARC de setembro a novembro -> janela de 6 blocos em 4 unidades com rotulos repetidos -> desempate flagado. O motor ja sabia a unidade (secao
'U2' = blocos 03 e 05) e nao a usava na janela. 2 sao sem janela nenhuma (poster png sem texto; lista da U1).
**Alavanca ENTROU (`8856d89` + fix `b421e92`, `window_provider.narrow_window_by_unit` no `anchor_engine.resolve_unscoped` logo apos
`resolve_window`; `MotorContext.units` carregado de `.content_taxonomy.json`):** janela ∩ blocos da unidade que a secao nomeia ('U<n>' via
`explicit_unit_number`, ou secao contida no/igual ao titulo da unidade). Nunca esvazia; **bloco SEM unidade (entrega/revisao/prova) fica na
janela** — a 1a versao o descartava e o MF `exercicioscorrecaoterminacao` perdeu a entrega bloco-11 (gold) da janela e virou erro confiante
(conf-err 0 -> 1 na automatica): corrigido, 4 testes (`tests/test_window_unit.py`). Alcance estatico: FR do zero 8 janelas, CG 23, SO 1, FR 10; gold
de bloco dentro da janela encolhida 16/16.
**Fila (`revisar.motivos_de`, `8856d89`):** janela-1 flagada e llm-funil com voto deixam de ser pendencia (a flag fica gravada como informacao).
Censo antes do reprocess: 57,5 -> 26,7 por 100 (duvida 71 + mudou 22). Testes adaptados (`test_revisar`, `test_moodle_sync`). Suite 2339.
**Gates (copias, tripwire, 0 chamadas; `janela2_*.log`):** motor puro +vocab 186/199 conf-err 1 · 183/191 · 53/57 · sub 138/151 · **holdout CG puro
bloco 31 -> 33/35** · CG sub puro 47 · automatica 193 conf-err 0 · 185 · 53 · 138 · holdout 35/35 · CG sub 58/82. Determinismo 8/8, 0 arquivos nao deterministicos.
**FR do zero A4 (`rebuild_fr_a4.log`, 0 chamadas):** fila 11 -> 10/20 · concordancia com o produto bloco 11 -> 13/20, unidade 20/20, sub 11/20 ·
todos os materiais de U2 caem em blocos 03/05 (a janela encolhida). O que resta: 7 desempates 03 x 05 flagados (13/08 x 27/08: o SARC nao separa
"protocolos de aplicacao" de "desenvolvimento de aplicacoes" no texto de um zip de sockets) · 2 sem janela (poster png; lista da U1) · 1 empate de
subunidade. Candidata: sem janela + unidade nomeada -> janela = blocos da unidade (poster/lista da U1 -> [01, 02]).
**Reprocess registrado dos 8 (`c1-3/reprocess_8_janela.py`):** bloco mudou so no FR (3 zips de sockets: bloco-22 11/10 -> bloco-05 27/08, a aula de desenvolvimento de aplicacoes); unidade 0; subunidade 0; revisar mudou 26; fila 110 -> 93; HEADs SO c60e2d1, TCC 79a9696, LR 5201deb, FR 5c9372a, CG 3c2c932 (MF/IA/ES2 so updated_at). **Produto:** curada bloco 198/199 conf-err 0 · unidade 191/191 · cobertura 55/57; subunidade x 6 golds 201/233 (86,3%) igual; sentinela 0. **Fila 26,7 (93/348: duvida 71 + mudou 22; por curso MF 11, SO 10, IA 4, ES2 12, TCC 7, LR 0, FR 5, CG 44; anatomia conflito 50, sub-ambigua 13, sub-empate 8, flag disamb 3) por 100.**

## FR DO ZERO — RUN A (06/09, sessao 6; user: "faca FR em sandbox, numeros de precisao, sem gold")
**Como (`c1-3/rebuild_fr.py --fresh`, 771 s):** stash do Moodle do FR (20 arquivos: 15 pdf, 1 png, 4 tar.gz; os 2 links do youtube nao entram pelo stash)
-> mesmo caminho da UI (scan_stash_cards -> build_stash_entries -> RepoBuilder.build), perfil real do FR, pymupdf4llm (o FR atual ja era pymupdf4llm),
em `.ablacao/FR-rebuild/`. **Zero chamada externa** (tripwire de Gemini e de Datalab: 0 tentativas), vocab NAO compilado, sem votos, sem resumos, sem
pino, sem gold. O FR atual (produto) fica como comparacao: ele tem vocab LLM (53 sinonimos), 13 votos e 4 resumos.
**Numeros crus (20 materiais):** fila 11/20 (duvida: conflito 9, flag disamb 8, sub-empate 3, sem bloco 2) · concordancia com o produto: bloco 11/20,
unidade 11/20, subunidade 7/20 · **regua sem gold que existe no FR: a SECAO do Moodle nomeia a UNIDADE ("U1 - Redes de Computadores", "U2 - Camada de
Aplicacao"): rebuild 10/19, produto 16/19** (os 3 zips de sockets do produto estao em u05 enlace; a secao diz u02). Os 9 erros de unidade do rebuild
(poster e unidade1-exercicios sem bloco -> u04; 4 zips -> u03 transporte; unidade2-exercicios dhcp/dns/http -> u03/u04) estao TODOS na fila: a fila
funciona, o motor nao. Bloco: sem o voter, unidade2-exercicios-dns/http caem em blocos de setembro/outubro (bloco-07/20) por texto; o produto os tem em
bloco-03 por voto.
**Leitura:** sem nenhuma chamada, num curso sem data no Moodle, o motor puro entrega unidade 10/19 pela regua do professor e 11 avisos em 20; com as
duas camadas de LLM (produto) 16/19 e 8 avisos. **Alavanca deterministica que a regua revela:** a secao que NOMEIA a unidade ("U<n> - ..." ou titulo da
unidade) e estrutura do professor e o motor nao a usa para a unidade (so para a janela de bloco): corrigiria os 9 do rebuild e os 3 do produto. Medir
nos 5 golds de unidade + CG + FR-oraculo antes de entrar (risco: secao = unidade x bloco de outra unidade; hoje 'bloco decide').
**Alavanca ENTROU (`1b41003`, `file_map.reconcile_unit_with_block(unit_is_explicit=...)`):** o motor JA detectava a unidade explicita da secao
(`unidade-explicita=u2`, conf 0,95, `explicit_unit_number`) e a reconciliacao a sobrepunha pelo bloco — inclusive bloco FLAGADO ou herdado do
vizinho. Agora a explicita vence e o conflito fica registrado (`explicita-vence-bloco=<id>`). So o FR tem secoes 'U<n>'; nos outros 7 a secao
nomeia a unidade por titulo em 60 materiais (MF 29, CG 23, SO 6, ES2 2) e em todos a unidade final ja era a da secao (0 diferem): a regra por
titulo seria no-op hoje, fica como candidata. Teste `test_unidade_explicita_da_secao_vence_bloco_discordante`. Suite 2335.
**Run A2 do FR (`rebuild_fr.py --fresh`, 888 s, 0 chamadas):** unidade x secao do professor **10/19 -> 19/19** · concordancia com o produto
bloco 11/20, unidade 11 -> 17/20, subunidade 7 -> 10/20 · fila 11/20 (conflito 9 — agora 'explicita-vence-bloco' — flag disamb 8, sem bloco 2,
sub-empate 2). **Gates (copias, tripwire):** 5 cursos e holdout CG identicos (186/183/53/138 · 193/185/53/138 · 31/35 · 35/35 · CG sub 58/82).
**Reprocess registrado dos 8 (`c1-3/reprocess_8_explicita.py`):** so o FR mudou: 3 zips de sockets u05 -> u02 (unidade) e subunidade preenchida (sockets / cliente-servidor); bloco 0; fila 110 = 110; FR HEAD 1cad69d, demais so updated_at. Fila 31,6 (110/348)/100. Determinismo 8/8, 0 arquivos nao deterministicos.
**Run B do FR (`rebuild_fr_b.py --fresh`, Gemini liberado pelo user so para o FR, contado; Datalab bloqueado):** build 840 s + 2 reprocess; chamadas Gemini: 10 summarize_bundle no build (code_curation.json NAO gravado — a investigar) + 2 na compilacao do vocab (68 sinonimos) + 10 votos gravados em material_curation.json (voter usa outro metodo, nao contado pelo interceptor) ~= 22; resultado: unidade x secao do professor 19/19, concordancia com o produto bloco 19/20 · unidade 20/20 · subunidade 17/20, sub vazias 2/20, fila 6/20 (2 flag llm-funil + 4 conflito 'explicita-vence-bloco' nos zips). Run A2 (0 chamadas): unidade 19/19, fila 11/20 = 8 blocos flagados por texto + 2 sem bloco + 1 empate — nenhuma politica de fila os toca; e o voter que os resolve
Sandboxes: `.ablacao/FR-rebuild/` (A2) e `.ablacao/FR-rebuild-B/` (B); o FR original nao foi apagado.

## GOLD DE SUBUNIDADE DO CG x MOODLE (oraculo) E REGRA DA SECAO (06/09, sessao 6; pedido do user)
**Comparacao (`c1-3` inline, 93 linhas do gold do CG):** onde a SECAO do Moodle nomeia um subtopico do plano, gold = secao em 27, gold != secao em 2
(`intro`: secao "Origens", gold "Conceitos" -> **gold corrigido pelo user: primario `origens`, conceitos/areas-relacionadas viram extras**;
`exemplozbuffer`: secao nomeia o pai, gold o filho z-buffer: fica); "Biblioteca OpenGL" 5 com gold vazio (ruling mantido: o plano nao tem OpenGL;
o 'conceitos' do motor vem do alias do vocab LLM); 48 a secao e a unidade inteira ou assunto fora do plano (Morfologia); 11 fora do gold. Nos 6 golds a
secao nomeia exatamente o subtopico do gold em 94 materiais: motor certo 86, errado 8.
**Regra da secao simulada (`c1-3/simula_secao_sub.py`, rota real: 1a + 2a passada REAL + regra; base reproduz o gravado 194/233):**
S1 (1a passada nao confiante: secao que nomeia exatamente UM subtopico decide, sobrepondo a 2a passada) **+5 -3** (perde SO threads x1 e IA k-nn x2:
a secao "Threads"/"Semana 3 ..." casa aliases errados) · **S1b (so se DEPOIS da 2a passada a subunidade ainda esta vazia ou ambigua) +3 -0** (MF
exemplos-zip, CG intro, CG curvasparametricas; 197/233) · S2 (tambem sobre decisao confiante) **+5 -13: REFUTADA** (a secao nomeia o pai quando o gold e o
filho: z-buffer, k-nn, escalonamento). **ENTROU (`4d649c4`, `resolver_apply._secao_nomeia_subtopico` no fim da 2a passada; reason `secao-nomeia-subtopico`; a 2a passada perdeu o
retorno antecipado `if not extra` para a regra do titulo e a da secao valerem sempre; teste `test_secao_do_moodle_decide_so_onde_nada_decidiu`).
**Gates (copias, tripwire, 0 chamadas; `secao_*.log`):** motor puro +vocab 186/199 · 183/191 · 53/57 · sub 5 cursos 138/151 (117) · holdout CG puro 31/35 ·
CG sub puro (sem vocab) 45 -> 47/82 · automatica 193 · 185 · 53 · 138/151 · holdout 35/35 · **CG sub automatica 56 -> 58/82 (45 primario)** ·
**automatica x 233: 194 -> 196 (84,1%)** · suite 2334 · determinismo 8/8, 0 arquivos nao deterministicos · sentinela 0. (O +1 do MF `exemplos-zip` da simulacao nao se
reproduziu no motor: o filtro de genericos do motor e o do curso, nao a lista da simulacao.)
**Reprocess registrado dos 8 (`c1-3/reprocess_8_secao.py`):** subunidade mudou 7 (SO 1: laminas-sockets -> comunicacao-e-sincronizacao; IA 3: outros-operadores, programa-exemplo-ag, lista-de-exercicios-i -> algoritmos-de-busca-com-informacao; CG 3: intro -> origens, curvasparametricas -> representacao-de-curvas-parametricas, slab -> algoritmos-de-geometria-computacional), bloco 0, unidade 0, fila 115 -> 110; HEADs SO db71737, IA d88cc53, CG 73ab72e, demais so updated_at. **Produto x 6 golds: 201/233 (86,3%), primario 169; CG 58/82, SO 15/15, IA 39/39, ES2 27/28, TCC 11/11, MF 51/58.** Fila 31,6 (110/348) por 100.

## O MOTOR SEM GOLD — REGUA PELA POSICAO DO PROFESSOR NO MOODLE (06/09, sessao 6; pergunta do user "o motor se sustenta sem os golds?")
**Regua sem gold (`c1-3/coerencia_moodle.py`, read-only, 0 chamadas):** para cada material, a POSICAO DO PROFESSOR no Moodle (label datado, data no
nome do modulo, secao-semana, faixa dos irmaos datados — a mesma logica da auditoria de 02/09, `contents.json` da API) vira o conjunto de blocos
admissiveis; o bloco do produto e "coerente" se esta nele. Nos 8 tutores (348 materiais): **posicao existe em 195 (56%)**, todos nos 5 cursos com gold;
**CG, LR e FR: 0 posicoes** (o professor nao data labels nem secoes) — a regua nao cobre esses cursos. **Coerencia: 188/195 = 96,4%.** Calibracao
contra o gold onde ambos existem: coerente-e-certo 170, coerente-e-errado 1, **incoerente-e-certo 7, incoerente-e-errado 0** — as 7 incoerencias sao
defeitos do proprio Moodle ja conhecidos (MF t2 sob label do Trabalho 1; ES2 roteiro1 x2 sob label de 2025; SO laminas de sockets x2 fora da faixa do
card; TCC 2 sob secao-semana errada). **Leitura:** onde o professor deixa data, o motor coincide com ele em 100% dos casos em que o Moodle nao esta
quebrado; para BLOCO, o motor se sustenta sem gold nesses cursos. Para unidade e subunidade nao existe oraculo sem gold (o professor nao as declara):
sobra o sinal de duvida do motor (pega ~metade dos erros). Num curso novo, a regua so funciona se o professor datar labels/secoes; sem isso, so o
teste com gold pelo SARC (protocolo do curso novo).
**Rebate do user ("nao estamos usando o SARC para obter as posicoes datadas?") — checado:** o SARC data as AULAS (todo bloco tem periodo e sessoes) e
e a metade que converte uma data em bloco; a data do MATERIAL so existe do lado do Moodle (label datado, data no nome, secao-semana) — e o motor ja
usa essas mesmas datas como providers de janela, por isso o SARC nao pode ser a regua das decisoes que ele mesmo alimenta. **Quarta marca medida:
data de upload (`timecreated` no `contents.json`).** Existe nos 8, mas: CG 93 modulos, so 2 uploads dentro do semestre (33 em 28/07 antes do inicio +
arquivos clonados de 2020-2025); FR 24/24 em 04/08 (upload em bloco); LR 7/9 progressivos; MF 42/116 (57 em 18/02), SO 38/40, IA 29/87, ES2 18/44,
TCC 32/37. Onde o upload cai no semestre e casa com um gold (25 materiais, MF/ES2/TCC): a aula do gold esta a <= 21 dias do upload em 25/25, <= 7 dias
em 18/25 (72%), no mesmo bloco em 12/25 (48%) — regua FROUXA (janela de ~3 semanas), nao de bloco. Para CG e FR, justamente os cursos sem as outras
marcas, o upload e em bloco: nenhuma posicao datada de material existe. Conclusao mantida: a regua sem gold de bloco existe quando o professor deixa
data no Moodle (label, nome, secao ou upload progressivo); CG e FR nao deixaram.
**Fila de revisao no estado atual (`fila_rendimento.py`, 35 materiais errados em algum eixo nos golds):** gatilhos: conflito 53 na fila / 42 com gold /
9 errados (21%; unidade 0, todos subunidade) · flag janela-1 21/19/5 (26%) · llm-funil 16/5/2 · sub-ambigua 15/13/1 (8%) · sub-empate 12/8/4 (50%) ·
due-straddle 1/1/0. Contrafactual: **P1 atual 115 (33,0/100) pega 23** · P3 = P1 sem sub-ambigua e due-straddle **105 (30,2) pega 23** (custo 0) · P2 = sem
conflito 76 (21,8) pega 16 · **P4 = sem conflito e sem sub-ambigua 65 (18,7) pega 16** (perde 7: subunidade do CG) · P5 = P4 + gatilho sub-vazia 85 (24,4)
pega 20. **Sem LLM, a fila cai por politica (o que conta como duvida), nao pelo motor:** as duvidas restantes sao blocos flagados (37: territorio do
voter/estrutura do Moodle) e empates reais da subunidade (12). Decisao do user: P3 (gratis) e/ou P4 (−50 itens, −7 erros pegos, todos do CG).

## CG CONFIANTES ERRADOS — TITULO NOMEIA OUTRO SUBTOPICO (06/09, sessao 6, FEITO; gerador `34d8b19`; user: "vamos medir essa alavanca")
**Regra (2a passada, `resolver_apply._subtopico_nomeado_no_titulo`):** decisao CONFIANTE da 1a passada cai quando o titulo + label do Moodle do
material contem uma parte de rotulo (decomposicao) de OUTRO subtopico Y da mesma unidade, Y e unico, e NENHUMA frase (rotulo/aliases) do vencedor
esta no titulo. Reason `titulo-nomeia-subtopico`. Caso: CG "Exercicios de geometria computacional" ia para `entidades-geometricas` (7,74, por
'Vetor/Pontos/Retas' no corpo) com o gold `algoritmos-de-geometria-computacional` em 0,96.
**Simulado (`c1-3/simula_titulo_confiante.py`, rota real: 1a passada + 2a passada REAL + regra por cima; base reproduz o gravado 192/233, 0 divergencias):**
T1 (parte no titulo, vencedor ausente do titulo) **+2 -0** · T1b (T1 e Y > 0 no corpo) +2 -0 · T2 (T1 so com margem pequena, 2o >= 50% do 1o) 0/0
— a margem nao separa (7,74 x 0,96). Entrou T1 (mais simples; T1b exigiria re-pontuar). Os outros 5 confiantes errados do CG NAO tem parte de rotulo
no titulo (exercicios-sobre-curvas x2 "Exercicios sobre curvas" com hermite 4,92 x catmull-rom 4,27 ambos no texto; vis2d x2; basico3d-py) e
seguem: sao escolha entre dois assuntos presentes, sem sinal generico.
**Gates (copias, tripwire, 0 chamadas; `titulo_*.log`):** motor puro +vocab 186/199 conf-err 1 · 183/191 · 53/57 · sub 5 cursos 138/151 (117) · holdout CG
puro 31/35 · CG sub puro 45/82 · automatica 193 conf-err 0 · 185 · 53 · 138/151 · holdout 35/35 · **CG sub automatica 54 -> 56/82 (42 primario)** ·
**automatica x 233: 192 -> 194 (83,3%)** · suite 2333 · determinismo 8/8, 0 arquivos nao deterministicos · sentinela 0.
**Reprocess registrado dos 8 (`c1-3/reprocess_8_titulo.py`, tripwire de produto):** subunidade mudou 2 (CG: exercicios-de-geometria-computacional, domina), bloco 0, unidade 0, revisar 0; CG HEAD e598a3c, demais so updated_at. **Produto x 6 golds: 199/233 (85,4%), primario 166; CG 56/82, ES2 27/28, MF 51/58.** Fila 33,0 (115/348) por 100.
**CG, o que resta (26/82):** 9 gold-vazio (5 pelo alias 'OpenGL' do vocab LLM em `conceitos`: Gemini) · 5 paginas de LOGIN (SYNC) · 3 morfologia (unidade a
montante) · 5 confiantes entre dois assuntos presentes · curvasparametricas (empate hermite = b-spline, gold e o pai) · 3 vazias sem alias no texto
(intro, exercicio-com-animacao, aula-gravada). Sem LLM e sem dado novo, o teto do CG na automatica e ~56-58/82.

## CG SUBUNIDADE 60% — DIAGNOSTICO DOS 33 E DECOMPOSICAO DE ROTULOS NO MOTOR (06/09, sessao 6, FEITO; gerador `ff3eda7`)
**Pedido do user:** "vamos resolver o problema de subunidades de CG; o que mais me preocupa e o 60%". **Diagnostico pela rota real
(`c1-3/diag_cg_sub.py CG`, copia na regua automatica, 0 chamadas) — os 33 erros por familia:** (a) **gold vazio, motor preencheu 9**: OpenGL x5 vao
para u01/`conceitos` porque o vocab LLM pendurou 'OpenGL'/'OpenGL 3D' como sinonimo de "Conceitos" (secao 'Biblioteca OpenGL'); transformacoes/
instanciamento x4 em u04 sem subtopico no plano · (b) **vazia 12** (3 sao paginas do Moodle capturadas como LOGIN, sem texto): bezier x4 (rotulo
"Bezier e Algoritmo de Casteljau" so casa a FRASE inteira; 'bezier' sozinho valia 0,12), curvasparametricas (empate hermite = b-spline 6,44), intro,
exercicio-com-animacao, exercicioduascores, aula-gravada (UNIDADE errada a montante: morfologia u06 x gold u03) · (c) **confiante 9**: morfologia x2
(unidade errada a montante + colisao 'matematica' com "A matematica das projecoes"), geometria computacional x2 (titulo diz "geometria computacional",
rotulo e "Algoritmos de Geometria Computacional": frase nao casa; `entidades-geometricas` ganha por 'Vetor/Pontos/Retas'), exercicios-sobre-curvas
x2 (hermite 4,92 x catmull-rom 4,27, ambos no texto), exercicios-teoricos-vis2d x2, basico3d-py (perspectiva 8,98 x camera 4,46) · (d) ambigua 2,
fraca 1. **Raiz generica:** o plano nomeia por FRASE COMPOSTA e o material nomeia a PARTE.
**Alavancas simuladas (`c1-3/simula_cg_sub_levers.py`, 1a passada em memoria, 6 golds = 233):** H2 = higiene estendida (sinonimo LLM que e SUBFRASE
de nome de secao sai; 'OpenGL' <- 'Biblioteca OpenGL'): **+0 -2 (SO threads perdem 'Processos'): REFUTADA**. D = decomposicao de rotulos
(partes de 'A e B'/'A ou B'/'A: B'/'A (B)'/'A / B' + rotulo com cabeca generica no curso 'Algoritmos de X' -> 'X'): **+9 -1 (CG 49 -> 57)**.
**Codigo (`ff3eda7`):** `timeline.index._label_parts` + `resolver_apply._partes_de_rotulo`, 2a FONTE de aliases da 2a passada
(`propagar_vocabulario_por_headings`), com as salvaguardas da propagacao: teto de df 25% dos materiais, exclusividade no CURSO INTEIRO (parte
contida no rotulo/aliases de outro topico ou no titulo de uma unidade nao entra — sem isso 'saida' de "Dispositivos de entrada e saida" no SO custava
1 cobertura e 'Internet' do rotulo-aspirador do FR derrubava o teste do holdout FR), e so onde a 1a passada nao decidiu. Reason `rotulo-decomposto`.
Primeira versao (na taxonomia, 1a passada, sem df): CG 57 mas cobertura SO 19 -> 18 e teste do FR vermelho — por isso foi para a 2a passada.
Testes `tests/test_label_decomposition.py` (4). Suite 2332.
**Gates (copias, tripwire, 0 chamadas; `decomp2_*.log`):** motor puro +vocab bloco 186/199 conf-err 1 · unidade 183/191 · cobertura 53/57 · sub 5 cursos
138/151 (117 primario, era 118) · holdout CG puro 31/35 · **CG sub puro (sem vocab) 39 -> 45/82** · automatica bloco 193 conf-err 0 · 185 · 53 · 138/151 ·
holdout 35/35 · **CG sub automatica 49 -> 54/82 (40 primario)** · **automatica x 233: 187 -> 192 (82,4%)** · determinismo 8/8, 0 arquivos nao deterministicos · sentinela 0.
**Reprocess registrado dos 8 (`c1-3/reprocess_8_decomp.py`, tripwire de produto):** subunidade mudou 15 (CG 10: bezier x4, basico3d-cpp,
programabasico3d, img, listadeexercicios, resolucao-de-prova, exercicioduascores · IA 3 · MF 1 `intro` · ES2 1 `devops`), bloco 0, unidade 0.
**Produto x 6 golds: 193 -> 197/233 (84,5%; primario 164)**: CG 49 -> 54, **ES2 28 -> 27** (`devops`: era ambiguo em `conceito-de-devops`; a parte
"Integracao continua" do rotulo "Integracao continua (CI)" — que nunca casava como frase por causa do '(CI)' — esta no texto da aula de DevOps; o gold
diz conceito). MF 51, SO 15, IA 39, TCC 11. Curada bloco 198/199 · 191/191 · 55/57 (intacta). HEADs: MF `ed31d99` · IA `74fec68` · ES2 `0fe0f53` ·
CG `929cdc3` (SO/TCC/LR/FR so `updated_at`).
**O que resta no CG (28/82):** 9 gold-vazio (5 pelo alias 'OpenGL' do vocab LLM em `conceitos` — a higiene estendida perde 2 no SO; caminho e recompilar
o vocab com o Gemini ou regra de 'ferramenta' sem subtopico) · 3 morfologia (unidade errada a montante, residuo conhecido) · 5 paginas de LOGIN
(dado, SYNC) · confiantes errados (geometria computacional x2, exercicios-sobre-curvas x2, vis2d x2, basico3d-py): a 2a passada nao toca decisao
confiante por desenho; alavanca candidata = "confiante com margem pequena e parte do rotulo no TITULO" (medir).

## FILA DE REVISAO — CAMADA LLM CORTADA (06/09, sessao 6, FEITO; gerador `0673150`; decisao do user "diminuir os arquivos para revisar")
`routing/revisar.py`: voto de LLM na janela nao e mais pendencia (era 79 dos 200 itens por 2 erros; bloco por voto 75/76 no gold). Teste ajustado
(`test_llm_na_janela_nao_e_pendencia`). **Reprocess registrado dos 8 (`c1-3/reprocess_8_revisar.py`):** revisar mudou 80, fila 200 -> 120, bloco/
unidade/subunidade 0 mudancas; commits MF `00539d2` SO `f513ba0` IA `d67cd58` ES2 `0f92ae5` TCC `082b728` FR `4c64ed6` CG `f920f21` (LR so `updated_at`).
Apos a decomposicao: **fila 115/348 = 33,0 por 100** (duvida 102 + mudou 13; sub-empate 20 -> 12, sub-ambigua 17 -> 15). A UI segue lendo
`temporal_block_method == "llm"` como informacao. 'conflito' (53, 0 erros de unidade) fica ate a subunidade do CG melhorar.

## FILA DE REVISAO (`revisar`/100 = 57,5) — RENDIMENTO MEDIDO CONTRA OS GOLDS (06/09, sessao 6; pergunta do user "da para diminuir?")
**O que e:** campo derivado `revisar` (`routing/revisar.py`, decisao B 02/09) = lista que o tutor mostra para conferir. Tres camadas: **duvida** (o
motor se acusou: sem bloco, bloco flagado, conflito unidade x bloco, subunidade empate/ambigua) · **mudou** (uma sync moveu decisao confiante) ·
**llm** (bloco decidido por voto de LLM, "confira"). Metrica = (duvida + llm + mudou) por 100 materiais. Hoje: 200/348 = 57,5 (duvida 108, llm 79, mudou 13).
**Rendimento (produto, 8 tutores x golds de bloco 234 / unidade 191 / subunidade 233; `c1-3/fila_rendimento.py`, 0 chamadas):** 41 materiais
errados em algum eixo (bloco 1, unidade 0, subunidade 40). Camada **duvida** 108 na fila, 79 com gold, 27 errados (34%) · **mudou** 13, 3 errados ·
**llm** 79 na fila, 71 com gold, **2 errados (3%)** — os blocos decididos por LLM acertam 75/76 no gold; os 2 sao erros de subunidade por acaso ·
**ok** (fora da fila) 148, 125 com gold, 9 errados (7%; todos subunidade confiante sem sinal: MF invariantes/terminacao/tiposindutivos/exemplos/AFP,
CG domina/exercicios-teoricos/pagina-instanciamento/aula-gravada).
**Por gatilho da duvida:** conflito 53 na fila, 13 errados (unidade 0! bloco 1, sub 12 por coincidencia) 31% · flag:janela-1 21 -> 5 (26%) · sub-empate
20 -> 9 (**69%**, o melhor) · sub-ambigua 17 -> 2 (14%) · flag:llm-funil 16 -> 3 (60%) · due-straddle 1 -> 0.
**Contrafactual (tamanho da fila x erros pegos, dos 41):** P0 atual 200 (57,5) pega 32 · **P1 sem a camada llm 121 (34,8) pega 30** · P2 P1 sem
'conflito' 85 (24,4) pega 23 · P1 + gatilho novo sub-vazia 134 (38,5) pega 31 · P1 + sub-vazia + sub-fraca(score<1) 150 (43,1) pega 32 · P2 + vazia +
fraca 129 (37,1) pega 31. Por curso sob P1: CG 76 -> 59, MF 58 -> 15, ES2 66 -> 34.
**Leitura:** a fila e 40% cerimonia: a camada llm (79) existe para "conferir o voto", mas o voto acerta 75/76. Cortar a camada llm da metrica tira 79
itens e perde 2 erros. 'conflito' e o maior gatilho da duvida e tem rendimento ZERO no eixo que ele vigia (unidade 191/191): os 13 que pega sao erros
de subunidade dos mesmos materiais. O que sobra fora da fila (9) e erro confiante de subunidade = vocabulario, sem sinal para gatilho.
**Proposta (decisao do user; muda metrica de produto):** P1 = camada llm vira "ok" na metrica e na fila (conservar o campo `temporal_block_method`
para a UI mostrar "decidido por LLM" como informacao, nao como pendencia). Opcional: gatilho `sub-vazia` (+13 itens, +1 erro). Nao tocar 'conflito'
ate a subunidade do CG melhorar (ele e hoje o unico que pega 7 dos erros de sub do CG sem gold).

## GOLDS CG E MF APROVADOS — REGUA DE SUBUNIDADE PASSA A 233; REMEDIDO (06/09, sessao 6; user: "Eu aprovo o gold de MF e CG")
**Ligacao:** `scripts/ablacao_rapida.score_subunit` (scorer compartilhado) · MF em `scripts/motor_puro.py` (`SUBUNIT_GOLD`) · CG no fim de
`_harness-2026-09-02/holdout_cg.py` (imprime `SUBUNIDADE CG`). Proposta marcada como aprovada (4 rulings como propostos). Suite 2328.
**Remedido (copias, tripwire, 0 chamadas; `c1-3/regua_tripwire.py {puro|holdout}` + `motor_auto.py {puro5|holdout}`, logs `gold6_*.log`):**
| regua | bloco (199) | unidade (191) | cobertura (57) | subunidade 5 cursos (151) | CG bloco (35) | CG subunidade (82) |
|---|---|---|---|---|---|---|
| motor puro + vocab (holdout CG sem vocab por definicao) | 186 conf-err 1 | 183 | 53 | **138 (91,4%) · 118 primario** | 31 | **39 (48%) · 27** |
| automatica v2 | 193 conf-err 0 | 185 | 53 | 138 · 118 | 35 | **49 (60%) · 36** |
| produto | 198 | 191 | 55 | 144 (93 + MF 51) | 35 | 49 · 36 |
**Automatica x 6 golds (233): 187 (80,3%) · primario 154. Produto: 193 (83%) · 162.** Por curso (automatica): SO 11/15 · IA 39/39 · ES2 26/28 ·
TCC 11/11 · MF 51/58 · CG 49/82. **Causa dos 46 erros da automatica:** SO 4 confiantes (fork/exec, regra humana) · ES2 1 ambigua + 1 confiante ·
MF 5 confiantes + 1 fraca + 1 vazia · **CG 11 vazias + 10 confiantes + 9 em que o GOLD E VAZIO e o motor preencheu (OpenGL/transformacoes sem
subtopico) + 2 ambiguas + 1 fraca.** Sem vocab (holdout puro) o CG cai para 39: o vocab vale 10 no CG.
**Numeros sem gold (censo do produto 06/09, `scripts/censo_motor_llm.py` + sinais do scorer):** subunidade vazia 44/348 (CG 17, SO 7, FR 6) ·
empate 20 (CG 10, IA 5) · ambigua 17 · score < 1: 40 (CG 22) · propagadas 25 · subtopicos no plano 229 (CG 59, SO 36, FR 33) = 1,3 material por
subtopico. **Duvida do motor x erro no gold (produto, 233):** 40 errados, 47 com sinal de duvida, 20 errados-e-com-duvida, 20 errados confiantes
(CG 15 de 33), 27 alarmes falsos: o sinal aponta o CURSO (revisar/100 CG 76, FR 59) e filtra revisao; nao mede acerto.
**Relatorio consolidado (artefato, pedido do user "todos os numeros, facil de entender"):** https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de

## NO MAXIMO DUAS CAMADAS LLM — CAMADA 3 (RESUMOS DE CODIGO) MEDIDA: ABLACAO E SUBSTITUTO DETERMINISTICO (06/09, sessao 6; DECISAO DO USER)
**Pedido do user:** "quero o motor o mais automatico possivel, LLM para 3 camadas fica pesado, queria deixar no maximo duas"; "nao quero ficar criando
novas rotas para o motor". **Peso medido no produto (8 tutores):** vocab = 1 compilacao por curso · resumos de codigo = 85 (1 por arquivo/zip, cache por
hash, so re-roda se o arquivo mudar) · votos = 205 (1 por material incerto, cache). Curso novo do tamanho do CG: 1 + 17 + 42.
**Ablacao da camada 3 (`c1-3/shim_codigo.py {sem|determ} {puro|holdout}`, copias, tripwire, 0 chamadas; motor puro + vocab + propagacao):**
| regime | bloco (199) | unidade (191) | cobertura (57) | subunidade (93) | holdout CG (35) |
|---|---|---|---|---|---|
| COM resumos do Gemini (referencia, `b_prop_*.log`) | 186 | 183 | 53 | **87** (83 primario) | 31 |
| SEM resumos (`code_curation.json` vazio, `codigo_sem_*.log`) | 186 | 183 | 53 | **71** (67) | 31 |
| substituto deterministico v1: zip/ipynb crus (`codigo_determ_*.log`) | 186 | 183 | 53 | 79 (75) | 31 |
| substituto deterministico v2: os `.md` que o motor JA gera para codigo/zip = o mesmo bundle que o Gemini recebe (`codigo_determ2_*.log`) | 186 | 183 | 53 | 78 (74) | 31 |
**Leitura:** a camada 3 so sustenta a SUBUNIDADE (+16 sobre nada, +8 sobre o melhor substituto); bloco, unidade, cobertura e holdout nao a sentem.
Os 8 que SO o resumo do Gemini acerta (listados na copia, `winner_score`/`empate`): SO threads x3 (empate exato 0,11: 'pthread' esta no vocab mas
empata; o Gemini injeta 'gerenciamento de processos'/'programacao concorrente') · IA perceptron x4 + mlp-xor (na copia 'perceptron' NAO e alias de
`modelos-preditivos`, so 'MultiLayer Perceptron'; o notebook tem 'Generalizacao', alias de `introducao`; o Gemini injeta 'Perceptron'/'Classificacao')
· ES2 roteiro1 (zip Spring: o codigo so tem 'currency/exchange'; o Gemini injeta 'Microsservicos'). Ou seja: o resumo vale pelo VOCABULARIO DE
CATEGORIA que o codigo nao contem — e um remendo da camada 2 (vocab), nao sinal proprio do codigo. Os outros 6 erros sao os mesmos com ou sem Gemini.
**Decisao do user (aberta): qual camada cortar.** Recomendacao com numero: cortar a 3 (menor ganho das tres: +8 sub; vocab vale +57 sub/+10 unidade;
voter vale +7 bloco/+4 holdout) e trocar o PRODUTOR de `code_curation.json` pelo deterministico v2 — mesma rota (`code_curation_signal_text` +
`entry["concepts"]`), produtor diferente, 0 rotas novas; custo -8/93 na subunidade, 0 no resto. Para nao perder os 8 mantendo duas camadas: a
compilacao do vocab (camada 2) passar a ver o bundle de codigo (`vocabulary_compile` le `_entry_markdown_text_for_file_map`, que para zip devolve
vazio) — mesma chamada, mais insumo; exige Gemini para remedir -> decisao 3 do handoff.
**"% de similaridade vocab x nome do material" (pergunta do user; `c1-3/simula_similaridade_nome.py`, 93 pontuaveis, 0 chamadas):** Jaccard de tokens
do nome (title + label) x label do plano (sem LLM): limiar 0,5 -> 9 certos 0 errados 84 sem atribuicao; 0,2 -> 16/1/76. x label + aliases do vocab LLM:
0,5 -> 27/0/66; 0,3 -> 46/3/44; 0,2 -> 63/6/24. `difflib` 0,3 -> 46 certos 41 errados. O scorer do motor (mesma ideia, texto inteiro + pesos): 87 com
vocab, 30 sem. **Leitura:** faz sentido e JA E o que o scorer faz (sobreposicao de tokens material x vocab, por topico); um indice explicito nao
acrescenta informacao — o teto e o vocabulario, nao a funcao de similaridade. Nenhuma rota nova proposta.

## CONTRIBUICAO POR CAMADA (06/09, pedido do user: "os numeros obtidos sem LLM" antes de uma materia 100% nova)
| camada (copias, tripwire, 0 chamadas) | bloco (199) | unidade (191) | cobertura (57) | subunidade (93) | holdout CG (35) |
|---|---|---|---|---|---|
| 100% sem LLM: motor puro SEM vocab compilado, SEM propagacao (`b_semvocab_semprop_puro.log`) | 187 conf-err 1 | 173 (ES2 18/28) | 54 | **30 (32%)** | 31 |
| idem COM propagacao por headings (`b_semvocab_puro.log`) | 187 | 173 | 54 | 26 — **regride 4**: sem vocab as sementes 'confiantes' erram e a propagacao amplifica | 31 |
| + vocab compilado por LLM (cache; ~1 chamada por unidade) | 186 | 183 | 53 | **87** | 31 |
| + voter com cache (~35% dos materiais votados) = AUTOMATICA v2 | **193 conf-err 0** | **185** | 53 | 87 | **35** |
| + curadoria (pinos, glossario manual) = produto | 198 | 191 | 55 | (IA 39/39) | 35 |
**Leitura:** a propagacao PRESSUPOE o vocab compilado (com ele +5, sem ele -4): se um dia o pipeline rodar sem a camada 2, desligar a 2a passada.
O vocabulario compilado e a camada que sustenta a SUBUNIDADE (30 -> 87) e boa parte da UNIDADE (173 -> 183; ES2 18 -> 28): sem ele o plano
nao tem os nomes dos algoritmos. O voter sustenta o BLOCO (186 -> 193, conf-err 1 -> 0; holdout 31 -> 35). A curadoria vale 5 blocos (MF 6 pinos) e 6
unidades (SO 3 + IA 3). Para uma materia nova, o custo de LLM medido no rebuild do CG (93 materiais): vocab ~9 (1/unidade) + resumos de codigo 17
(1/zip ou arquivo) + voter ~40 (flagados/serie/funil) ~= 66 chamadas; travessia (opcional, medicao) +45.

## SUBUNIDADE SEM LLM — PROPAGACAO DE VOCABULARIO POR HEADINGS NO MOTOR (05/09 noite, sessao 6, FEITO; gerador `4a239d9`)
**Pedido do user:** arrumar as subunidades de maneira automatica, sem LLM. **Raiz:** o plano nomeia categorias e o material nomeia algoritmos; o vocab
compilado por LLM nao emitiu 'perceptron'/'rede neural'/'MLP' para o IA e o remendo era o glossario MANUAL (curadoria).
**Regra (`resolver_apply.propagar_vocabulario_por_headings`, 2a passada):** token EXCLUSIVO dos headings/titulo dos materiais que a 1a passada atribuiu
com confianca (>= 0,7) a um subtopico vira alias desse subtopico; so materiais vazios/ambiguos/fracos sao repontuados; decisao confiante nunca e
sobreposta. Salvaguardas medidas, cada uma: sem stems genericos do motor ('exemplo'/'respostas' viravam alias: CG `slab` e MF `respostas` caiam) · df
<= 25% dos materiais ('sumario'/'aula' do TCC) · >= 2 confiantes · exclusivo de UM subtopico · so nos nao-confiantes (o CG perdia 8 confiantes sem isso).
Limiares em `thresholds.T` (SUBUNIT_PROPAG_CONF 0,7 · MIN_ENTRIES 2 · DF_MAX 0,25; grade de 8 pontos em `c1-3/simula_propaga_grid_df025.log`).
Teste `tests/test_subunit_propagacao.py` (2). Suite 2328. Reason gravada: `propagado-headings`.
**Medido antes de entrar (`c1-3/simula_propaga_headings_6golds.py`, 6 golds = 233, CG/MF propostos):** 182 -> 187, **+5 -0**, 4 mudancas erro->erro;
FR/LR 0 mudancas. Alias = label de sessao do SARC (`simula_alias_sessao_sub.py`): 0 efeito nos 93.
**Gates (tripwire, 0 chamadas):** motor puro +vocab bloco 186/199 · unidade 183/191 · cobertura 53/57 · **sub 82 -> 87/93 (83 primario)** · automatica bloco 193/199 (97,0%, conf-err 0) · unidade 185/191 · cobertura 53/57 · **sub 87/93 (93,5%)**
· holdout CG puro 31/35 · automatico 35/35 · CG sub automatico 49/82 (1 propagado) · curada bloco 198/199 · 191/191 · 55/57 · produto x 6 golds de
subunidade 193/233 com extras (igual; primario 162) · sentinela 0 · censo revisar/100 57,5 (sub-empate 24 -> 20, sub-ambigua 19 -> 17) · determinismo 8/8, 0 arquivos.
**Reprocess registrado dos 8 (`c1-3/reprocess_8_propagacao.py`, tripwire de produto; NAO commita quando so `updated_at` muda — caixa aplicada):**
MF `7a8707a` (sub mudou 4: t1-thy, hoare, invariantes, terminacao -> verificacao-de-programas; os zips com resumo colidido) · IA `0075334` (2: lista-de-
exercicios-i, p2-202401 -> busca-adversaria) · ES2 `4c8011b` (6, todos dentro dos extras do gold) · TCC `621c292` (1: aula-16 -> prova-da-indecidibilidade) ·
SO/LR/FR/CG so `updated_at`, sem commit. Bloco 0 · unidade 0 · flagadas iguais · propagados 26 nos 8.
**O que sobra na subunidade do motor puro (6/93):** SO fork/exec x4 (gold pela regra humana 'apoio rotula pelo card', que o IA contradiz: sem regra
generica), ES2 `devops`/`kubernetes` (quase-empate). No IA o automatico agora iguala o glossario manual (39/39) — o remendo humano deixou de ser necessario.

## CG UNIDADE SEM LLM E SEM PINO — RADICAL-FALLBACK NO MOTOR + 2 PINOS REMOVIDOS (05/09 tarde, sessao 6, FEITO; gerador `ff21cab`, CG `0d2020a`)
**Pedido do user:** o maior numero possivel sem LLM, sem curadoria por curso. **Medido antes (`c1-3/simula_cg_unidade_generico.py`, nos 8):** radical so como
fallback (RF) +1 bloco (CG 15 -> u07), 0 colateral, unidade 183 = 183 · generico por radical entre unidades (SG) 183 -> 172, SO 32 -> 21: REFUTADO · heranca
por afinidade zero (Z0) 0 efeito (o bloco-08 tem afinidade 1 via 'matematica' no label de u06) · alias boilerplate ('OpenGL' em > 25% dos materiais) 0
efeito no mapa · bloco flagado nao impoe unidade: texto certo 3 x bloco certo 4 (puro), 0 x 4 (produto): REFUTADO · gate por confianca do texto
(>= 0,6 a 0,95): saldo -17 a -2 em toda a varredura: REFUTADO (o 'bloco decide' de 21/08 segue certo).
**Codigo (`ff21cab`, `assign_units_positional`):** bloco sem ancora exata possivel (aff < 2) ancora por radical de 6 chars com as mesmas exigencias
(>= 2, margem >= 1, radical exclusivo de UMA unidade), conf 0,6. Teste `test_positional_radical_so_como_fallback_ancora_bloco_sem_token_exato`.
No codigo real muda so o bloco-15 do CG nos 8. Suite 2326.
**Curadoria do CG:** pinos dos blocos 06 e 15 REMOVIDOS (`0d2020a`; a mensagem do commit repete a anterior — e a remocao); fica so o bloco-08
(morfologia -> u03), residuo com nome. Reprocess registrado (tripwire): unidade mudou 0, bloco 0, sub 0, votos 42 = 42, 0 resumo: o produto
ficou identico sem os 2 pinos.
**Gates:** motor puro +vocab 186/199 conf-err 1 · 183/191 · 53/57 · sub 82/93 (iguais) · holdout CG puro 31/35 (igual) · curada 198/199 · 191/191 ·
55/57 (igual) · sentinela 0 · censo 58,3/35,9 · determinismo 8/8, 0 arquivos nao deterministicos.
**Regua automatica remedida (`motor_auto.py` v2: COM vocab tambem no holdout e cache de votos DO PRODUTO copiado para a copia — a copia acumulava
votos antigos, CG 2/42 diferentes, e o holdout puro roda SEM vocab por definicao, o que fazia o bloco-02 ficar sem unidade):** 5 cursos bloco 193/199 (97,0%, conf-err 0) · unidade 185/191 · cobertura 53/57 · sub 82/93 (0 votos pulados; era 192 com o cache antigo da copia) ·
holdout CG 35/35 · **CG unidade automatica: 22/93 -> 6/93 erradas** = morfologia x3 (bloco-08 -> u06; plano nao menciona morfologia) + texturas x3
(`maptextures` e pagina de videos no bloco-06 por colisao 'mapeamento'; `texturas-v3` u01 por conteudo). A primeira medicao (11/93) estava
contaminada pela falta do vocab na copia: corrigida.
**Residuo sem LLM (com nome):** 3 de morfologia (so voto de LLM de unidade ou pino) + 3 de texturas (2 erro de bloco flagado -> voter; 1 conteudo).

## REGUA AUTOMATICA (05/09 tarde, sessao 6; decisao do user: "gold so mede; nao criar curadoria por curso") — MEDIDA, VIRA A OFICIAL
**Definicao:** motor + voter com CACHE de votos, SEM pinos (bloco/unidade/sub), SEM glossario manual, COM vocab compilado por LLM; copias `.ablacao`;
tripwire (cache miss = voto pulado e contado; 0 pulados nesta rodada; 0 chamadas). Ferramenta: `_harness-2026-09-04/c1-3/motor_auto.py {puro5|holdout}`.
| regua | motor puro | **AUTOMATICA** | curada (produto) |
|---|---|---|---|
| bloco (199) | 186 conf-err 1 | **192 = 96,5%, conf-err 0** | 198 |
| unidade (191) | 183 | **185 = 96,9%** | 191 |
| cobertura (57) | 53 | 53 | 55 |
| subunidade (93) | 82 | **82 = 88%** | (sem regua curada; IA 39/39 com glossario manual) |
| holdout CG (35) | 31 | **35 = 100%** | 35 |
**Leitura:** o pipeline automatico ja passa de 95% em bloco, unidade e no curso nao usado para afinar; o que falta para a curada e o territorio dos
pinos (MF 6 de bloco: arvores/listas e cia.; SO 3 + IA 3 de unidade) — o voter resolve os flagados de bloco (holdout 31 -> 35) mas NAO existe voto de
UNIDADE para bloco sem evidencia lexical. **Onde esta abaixo de 95%: subunidade (88%) = vocabulario** (o plano nomeia categorias, o material nomeia
algoritmos; o vocab compilado por LLM nao emitiu 'perceptron'/'rede neural'/'MLP' para o IA; o glossario manual foi o remendo humano).
**Regras genericas x pinos do CG (medido nos 8, `c1-3/simula_radical_fallback.py` + combo em memoria):** bloco-06 (u04) ja nao precisa de pino
(a higiene resolveu; base = u04) · bloco-15 (u07) e coberto por RADICAL SO COMO FALLBACK (1 bloco muda nos 8, 0 colateral, unidade 183 = 183) ·
bloco-08 (morfologia -> u03) NAO tem sinal lexical generico possivel: o plano nao menciona morfologia e o unico token que casa e 'matematica' no
label do topico u06 'A matematica das projecoes'; higiene por titulo/secao no mapa, heranca por afinidade zero (Z0) e exclusividade relaxada (XR)
nao o alcancam (0 efeito nos 8). Caminho generico para esse residuo = LLM decidindo a UNIDADE de bloco sem evidencia lexical (1 chamada por bloco
assim; CG tem 1) — precisa de Gemini. Ate la o pino do bloco-08 e andaime, nao arquitetura.

## CURADORIA DE UNIDADE DO CG + HIGIENE DO VOCAB (05/09 tarde, sessao 6, FEITO; CG `2c5e01e`, gerador `e0c433c`)
**Codigo (`e0c433c`, `load_glossary_curation`):** sinonimo COMPILADO por LLM igual a nome de secao do Moodle (sem numeracao) nao vira alias; manual fica.
Teste `tests/test_glossary_curation.py::test_sinonimo_compilado_igual_a_secao_do_moodle_nao_entra`. Remove exatamente os 3 do CG; 0 nos outros.
**Curadoria (CG `.timeline_curation.json`, pelo oraculo):** pinos de unidade bloco-06 -> u04 (SARC 7-8 e secao 6 'Processo de Visualizacao 2D'),
bloco-08 -> u03 (SARC 12 entre processamento de imagens e exercicios), bloco-15 -> u07 (SARC 21 entre curvas e visualizacao 3D). Glossario manual do CG
so com `_nota`: o sinonimo 'Morfologia Matematica' em '3.5 Segmentacao' (`ee4c276`) rotulou o bloco-08 como Segmentacao e moveu 4 materiais de
segmentacao do bloco-07 (aula certa, 01-03/09) para o 08 — REVERTIDO em `2c5e01e` (lei nova: sinonimo manual nunca renomeia bloco).
**Reprocess registrado (`c1-3/reprocess_cg_unidade.py`, tripwire de produto: voter so com cache):** unidade mudou 9 (morfologia x3 -> u03, modelagem x6 ->
u07), bloco 0, flagadas 15 = 15, votos 42 = 42, 0 resumo de codigo; subunidade mudou 10 (csg -> geometria-solida-construtiva-csg, exercicio de
modelagem -> tecnicas-de-modelagem-3d ...). **CG unidade: 22/93 erradas -> 1** (`texturas-v3`: sem bloco, u01 por conteudo; u08 sem termo no GLOSSARY.md,
que para em 7.1.2) + 2 por erro de BLOCO (maptextures e pagina de videos no bloco-06 pela colisao 'mapeamento'; flagadas, voter decide). Os 10 do
bloco-06 sao u04 pelo oraculo (o plano poe transformacoes/instanciamento em u05: gold de subunidade vazio para 5, mapeamento -> sistema-de-coordenadas).
**Gates (todos com tripwire, 0 chamadas):** motor puro +vocab 186/199 conf-err 1 · 183/191 · 53/57 · sub 82/93 (iguais) · holdout CG 31/35 conf-err 0
flag 14 (igual) · curada 198/199 conf-err 0 · 191/191 · 55/57 (igual) · sentinela 0/8 · suite 2325 · censo revisar/100 58,3 ('mudou' 13) votos 35,9 ·
determinismo pos-higiene: **8/8, 0 arquivos nao deterministicos** (`c1-3/determinismo_higiene.log`, tripwire; 0 chamadas nos originais e nas copias).
**Gold de subunidade v2 (proposto, aguarda aprovacao):** CG 93 materiais, **82 pontuaveis** (1 unidade errada + 2 bloco errado + 8 meta), produto acerta
49/82 com extras (36 primario); MF 66, 58 pontuaveis, 51/58 (36). Revisao: `gold_subunidade_CG_MF_proposta_2026-09-05.md`; atribuicoes do CG por entry:
`2026-09-05-cg-atribuicoes.md`. Alavancas genericas no motor para a unidade: 5 medidas e refutadas (ver §CG 22/93 abaixo e NAO fazer do handoff).

## GOLD DE SUBUNIDADE CG E MF — PROPOSTO-CLAUDE (05/09 tarde, sessao 6; **APROVADO PELO USER EM 06/09**, ver secao acima) + BUG: ZIPS DO MF COLIDEM
**Arquivos:** `docs/reports/subunit_gt_CG.csv` (93 materiais, **63 pontuaveis**, 22 com UNIDADE computada errada -> `scorable=no` com a unidade
verdadeira na nota) e `subunit_gt_MF.csv` (66, **58 pontuaveis**, 5 unidade errada); revisao humana em
`docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md` (coluna `ok?`). Gerador: `_harness-2026-09-04/c1-3/gera_gold_subunidade.py`
(regras no docstring). **Ainda NAO entra em `motor_puro.py` (SUBUNIT_GOLD) nem na regua:** gold e humano; entra apos aprovacao.
**Contra o PRODUTO (originais), com a proposta como esta:** CG com-extras 42/63 (primario 30/63) · MF 51/58 (36/58). Rulings pendentes marcados na
nota: (a) bundle de codigo misto rotula pelo card (CG `opengl3dcpp`, `-vdi`)? (b) CG `exemplodemanipulacaodeimagens`: label 'Classe Vetor' x conteudo
processamento de imagens; (c) convencao Dafny: listas 'Programacao e Verificacao com Dafny (X)' = `softwares-de-suporte...` com extra
`verificacao-de-programas`; (d) OpenGL (ferramenta) = subtopico vazio.
**Achado de UNIDADE no CG (22/93, sem gold de unidade):** o card '6 - Processo de Visualizacao 2D' mistura u04 (recorte) e u05 (instanciamento,
mapeamento, transformacoes) e o motor poe tudo em u04 (8 entries); modelagem (csg, modelagem3d, exercicio de extrusao, basico3d x2, pagina de
videos) em u06 em vez de u07 (6); texturas (maptextures, texturas-v3, pagina de videos) em u04/u01 em vez de u08 (3); morfologia (slides, aula
gravada, pagina) em u01 em vez de u03 (3); animacao-v2 e transformacoes em u04 em vez de u05. Candidato a gold de unidade do CG (C5).
**CG 22/93 UNIDADES ERRADAS — DISSECADO (05/09 tarde, `c1-3/simula_unidade_sem_alias.py`):** 3 blocos explicam 19: bloco-06 'Recorte' u04 (10 entries
que o PLANO poe em u05: instanciamento/mapeamento/transformacoes — o SARC chama tudo de 'Processo de Visualizacao 2D' = nome de u04: RULING),
bloco-15 'Modelagem geometrica' u06 (6; verdade u07; ancora falha: 1 token exclusivo 'modelagem', aff 1 < 2), bloco-08 rotulado 'Areas relacionadas'
conf 1,0 u01 (3; verdade u03); + 3 de texturas (2 no bloco-06 por colisao do token 'mapeamento' com a sessao 'processo de visualizacao 2d mapeamento';
1 por conteudo). **RAIZ = DADO: o vocab compilado por LLM do CG (`.glossary_curation.llm.json`) poe 'Morfologia Matematica' e 'Manipulacao de Imagens'
como sinonimos de 'Areas relacionadas' (u01) e 'Mapeamento de Texturas', 'OpenGL', 'OpenGL 3D' de 'Conceitos' (u01)** — envenena `_unit_tokens`
(ancora), o scorer de unidade (texturas-v3 -> u01) e o rotulador de bloco (bloco-08). Censo nos 8: so o CG tem esse padrao (topicos genericos
com titulos de material de OUTRA unidade). **Alavancas genericas no motor, medidas e REFUTADAS:** unidade sem aliases no mapa bloco->unidade
(183 -> 136/191, pinos 12 -> 5/13: IA e ES2 dependem dos sinonimos) · radicais (6 chars) nos dois lados (183 = 183; CG bloco-15 -> u07 +4, mas
bloco-06 -> u03 por 'proces~processamento' -4; saldo 0). **Simulado o conserto de DADO (veto dos 5 + sinonimos: u07 tecnicas-de-modelagem-3d <-
'Modelagem Geometrica/de Solidos/Extrusao', u08 mapeamento-de-textura <- 'Mapeamento de Texturas/Texturas', u03 segmentacao <- 'Morfologia
Matematica/Dilatacao/Erosao'):** bloco-08 -> u03 e bloco-15 -> u07 (9 entries), mas bloco-06 cai para u02 (DP monotonica: u04 antes de u03 e
inversao; ancora bloqueada porque 'instanciamento' e exclusivo de u07) -> precisa de PINO de unidade no bloco-06 (u04, ou u05 por ruling).
Falta no loader do glossario um VETO (manual so ADICIONA sinonimos): feature de ~5 linhas em `load_glossary_curation` (chave `exclude`).
**O QUE O ORACULO DIZ (SARC = cronograma no SYLLABUS; Moodle = secoes):** sessoes 7-8 'Processo de Visualizacao 2D - Instanciamento' e '... - Recorte e
mapeamento' + secao 6 'Processo de Visualizacao 2D' (13 modulos) -> o professor chama TUDO de u04 (o plano poe mapeamento/transformacoes em u05);
sessao 12 'Morfologia Matematica' entre 'Processamento de Imagens' (9-10) e exercicios + secao 11 entre 10-Segmentacao e 12-Modelagem -> u03 (plano
sem topico; vizinho = segmentacao); sessao 21 'Modelagem Geometrica' entre Curvas (19-20, u07) e Visualizacao 3D (24-25, u06) + secoes 12 e 14 -> u07;
texturas: sem sessao no SARC, secao 17, plano u08/mapeamento-de-textura. **Raiz dos sinonimos envenenados:** o compilador de vocabulario (LLM, Fase 1b)
recebeu NOMES DE SECAO do Moodle como termos e, sem topico que casasse, pendurou-os nos topicos genericos de u01 — 3 no CG ('Mapeamento de
Texturas' -> Conceitos; 'Manipulacao de Imagens', 'Morfologia Matematica' -> Areas relacionadas), 0 nos outros 3 tutores com vocab LLM (censo com
numeracao removida; MF tem 4 sinonimos = titulo de material, mas CORRETOS e uteis).
**Raiz sem LLM, medida em memoria nos 8 (`c1-3/simula_raiz_unidade.py`):** H = higiene (sinonimo compilado que e nome de secao do Moodle nao vira
alias): unidade 183 = 183/191, pinos 12/13 =, remove exatamente os 3 do CG; bloco-08 perde o u01 errado mas cai em u06 (plano sem topico de
morfologia) — neutro na regua, limpa o rotulo do bloco e o scorer. V = preencher pelo vizinho ancorado em vez da DP monotonica: **REFUTADO**
(183 -> 163/191; CG 71 -> 41/93: Origens/Conceitos herdam u02); VX (exclusividade relaxada): 179/191, CG 47 — REFUTADO. **Conclusao:** a DP monotonica
e o melhor prior estrutural; a inversao de ordem do CG (u04 -> u07 -> u03 -> u07 -> u06 -> u07) so se resolve pela camada humana = PINOS DE UNIDADE nos
blocos 06 (u04, pelo nome do SARC), 08 (u03) e 15 (u07) — o mesmo mecanismo que os outros 7 tutores ja usam (13 pinos) — + higiene generica no codigo +
sinonimos manuais no CG (u08 <- 'Texturas'/'Mapeamento de Texturas'; u03/segmentacao <- 'Morfologia Matematica').
**UNIFICAR ALAVANCAS? (pergunta do user 05/09 tarde: 'uma acerta, a outra remede e erra') — medido:** (1) Unidade, conflito texto x bloco
(`unit_block_conflict`, gold de 191): motor puro 33 conflitos -> bloco certo 27, texto certo 3 (SO sockets x2 bibliografia, IA visao-geral), nenhum 3;
produto 25 -> bloco 25, texto 0. Gate 'texto vence quando bloco conf <= 0,4': +1 (IA) -1 (MF) = saldo 0. A decisao de 21/08 ('bloco decide, texto vira
registro de conflito') segue certa: 9:1. (2) Higiene de aliases por label de SESSAO/titulo de material: IA tem 5 aliases 'Aula NN - ...' (aspirador
do topico de busca), mas os aliases = titulo sao UTEIS (MF 8: 'Conjuntos Indutivos', 'Inducao Estrutural...'; IA 'MLP', 'arvores de decisao'; ES2
'Kubernetes', 'DEVOPS') -> nao generalizar. (3) **Radical (6 chars) SO como fallback no mapa bloco->unidade** (tokens exatos decidem; bloco sem
ancora exata possivel, aff < 2, ganha ancora por radical com >= 2, margem >= 1, radical exclusivo de UMA unidade): nos 8, **1 bloco muda (CG
bloco-15 Modelagem -> u07, = pino), 0 colateral**, pinos 12 -> 13 (sem contar o pino novo do CG), unidade 183 = 183/191. E a unica unificacao que
sobrevive: cobre sem pino o caso que hoje o pino cobre. Candidato (caixa): ~15 linhas em `assign_units_positional`, ganho atual 0 (pino ja
resolve), valor = proximo curso sem pino. `c1-3/simula_radical_fallback.py`.
**MATERIA NOVA (pergunta do user 05/09 tarde) — evidencia e bugs de dado medidos nos 8:** o unico teste de generalizacao e o holdout CG (curso nao
usado para afinar): bloco automatico 35/35, mas unidade 22/93 erradas (so vistas ao montar o gold de subunidade) e subunidade ~49/82 no gold proposto.
O censo ja sinalizava: CG revisar/100 = 74-76 (maior dos 8; media 58) — um curso novo com revisar/100 alto e o sinal para olhar, sem gold. Dados que
uma materia nova traz quebrados: (1) **paginas do Moodle (`mod/page`) capturadas como TELA DE LOGIN**: CG 16/16 (unico tutor com paginas; o tutor so
roteia essas 16 pelo titulo); (2) **colisao de nomes de membro ENTRE zips** na extracao plana: CG 168 nomes repetidos em 14 zips (projetos OpenGL
com os mesmos arquivos), ES2 38 em 8, MF 10 em 13, SO 3 — o codigo do tutor e o resumo de codigo desses zips estao trocados/incompletos.
Tag [CODE] SYNC/C5. Condicoes para o automatico funcionar: SARC com sessoes datadas, Moodle com secoes e labels (FR tem 0 labels), plano
parseavel ate o fim (CG para em 7.1.2), Gemini para voter/vocab/resumos (~100-150 chamadas por curso de 90 materiais); professor sem sinal
temporal (MF: tudo postado em 18/02) empurra 30/66 para o LLM.
**BUG (medido): zips do MF extraidos SEM subpasta -> colisao de nomes.** `raw/code/professor/` e plano (36 arquivos): `colecoes_arrays/ex1.dfy`,
`colecoes_sequences/ex1.dfy`, `invariantes/ex1.dfy`, `terminacao/ex1.dfy` e `tiposindutivos/ex1.dfy` viram UM `ex1.dfy` (o ultimo vence:
`code/professor/ex1.md` tem 'datatype Cor' = tiposindutivos; 'new nat[5]' dos arrays nao existe em lugar nenhum). Resultado: 4 zips (20 .dfy)
perderam o conteudo no tutor e os 5 resumos de codigo dizem 'datatype Cor'; `exemplos.zip` (5 `.smv` do NuSMV) nao gera markdown (extensao
ignorada) e o resumo diz 'Dafny'. Efeito na atribuicao: os flips de bloco do item 3 (`exercicios-conjuntos`, `-arrays`) e os 6 'exemplos' do MF
decidem com texto de OUTRO zip. Correcao: extrair zip preservando `<zip>/<membro>` (ou prefixar pelo id) + aceitar `.smv`; depois re-resumir
(Gemini, quando liberado) e reprocessar o MF. Tag [CODE] · campanha: SYNC/C5 (dado) — decisao do user.

## OS 32 ERROS DO MOTOR PURO POR REGUA, SEM LLM (05/09 tarde, sessao 6; pergunta do user "da para subir bloco/unidade/subunidade sem LLM?")
**Bloco 13/199:** 1 conf-err (MF `exerciciosdafny2`, voto acerta no produto) · 9 flagados (duvida legitima: voter no produto, pino na curada) · 3 media
sem flag: MF `revisao` 04 -> 03 ("revisao" fora dos genericos: refutado 50 -> 50), MF `intro` 05 -> 06 (.thy: so o TIPO DE ARQUIVO aponta Isabelle = regra
por categoria, vetada), TCC `t1-enunciado` sem bloco (unico caso do `duedate`; manifests sem modname/dates; 8 `trabalhos` nos 8 tutores, so este erra
no gold). Frente fechada com 5 alavancas refutadas em 05/09 + title := label hoje.
**Unidade 8/191 (os mesmos do §C0 ITEM 10):** SO bloco-06 x3 + sockets x2 · IA blocos 01-02 x3 (`visao-geral-introducao-e-historico` e 2 links sem card:
conteudo aponta u01, a reconciliacao impoe a unidade do bloco). Registrado como sem alavanca estrutural; a curada resolve por pino (191/191).
**Subunidade 11/93 = 3 familias:** SO fork/exec x4 (`estudo-de-casos` por "Unix/Linux" no texto; gold `chamadas-de-sistema` pela regra humana "apoio rotula
pelo card") + SO `exemplo-threads-em-c-exemplo3` (empate-exato 3x 0,11, texto curto) · IA notebooks x4 (perceptron x3, mlp-xor: score 2,3-2,7 `ambiguous`,
caem no topico que duplica o vocabulario da unidade — causa G-3 de 19/08, "falta IDF intra-unidade", NAO implementada: `grep -i idf` em
`timeline/index.py` = 0) · ES2 `devops`/`kubernetes` (quase-empate 0,04/0,26; "Conceito de DevOps" so casa por alias 0,82). **Simuladas em memoria e
REFUTADAS (`c1-3/simula_sub_card.py`):** (A) codigo herda subunidade pelo NOME do card: 0 '+', 23 '-' (IA "Semana N - ML Aprendizado Supervisionado" casa
`introducao-ao-aprendizado-de-maquina`); (B) codigo herda do irmao principal do card: 0 '+', 2 '-'; o SO fork x4 nao muda em nenhuma (card nao nomeia o
topico; irmaos tambem em `estudo-de-casos`). O scorer de subunidade (`_score_entry_against_taxonomy_topic`) nao le o card — e por medida, nao deve.
**IDF intra-unidade MEDIDO (05/09 tarde, `c1-3/simula_idf_sub.py`: em memoria pela rota real `auto_map_entry_subtopic`, 0 chamadas; base
reproduz 92/93 do snapshot):** V1 (tokens do titulo da unidade + tokens em >= 2 irmaos viram genericos) **0 flip** · V2 (V1 + alias repetido ou so
de tokens genericos sai) **+1 -5** (+ ES2 `devops` -> `gerenciamento-da-configuracao`, extra do gold; - IA k-means/agrupamento caem em introducao:
`Agrupamento` e compartilhado com os aliases-sessao do topico de introducao) · V2s (so alias repetido verbatim em >= 2 irmaos) **0/0**. **REFUTADO.**
**Raiz dos 4 do IA e VOCABULARIO, nao scorer:** na copia (motor puro +vocab) `modelos-preditivos` nao tem `perceptron`, `rede neural`, `MLP`, `kNN` —
esses termos so existem no glossario MANUAL `.glossary_curation.json` (curadoria 25/08, "o plano nomeia CATEGORIAS; o material nomeia ALGORITMOS"),
que a ablacao remove; o vocab compilado por LLM tem "MultiLayer Perceptron" (frase) e nao o token. Teto da subunidade no motor puro = vocabulario
(camada humana, ou re-compilacao por LLM quando liberado).
**PROPAGACAO DE VOCABULARIO POR HEADINGS (sem LLM, 05/09 tarde; `c1-3/simula_propaga_headings*.py`, em memoria pela rota real):** tokens
EXCLUSIVOS dos headings/titulo dos materiais que o motor ja atribuiu com confianca a um subtopico viram aliases desse subtopico (2 passadas;
token em > 25% dos materiais do curso = generico; 2a passada so onde a 1a nao decidiu com confianca). **Gold (93): 82 -> 87/93, +5 -0**
(IA perceptron x3 + mlp-xor via `rede`/`nearest`/`neighbors`; SO `exemplo3`) no ponto (conf >= 0,7; token em >= 2 confiantes; df <= 25%);
curada 93/93 intacta. Grade df 0,25 (8 pontos): (0,5;2) +5/-3 · (0,5;3) +3/0 · (0,6;2) +5/-3 · **(0,7;2) +5/0** · (0,7;3) +4/0 · (0,8;2) +5/-1 ·
(0,9;2) 0/0 · (0,9;3) 0/0; sem o teto de df, (0,9;2) dava -20 (poucos confiantes = exclusividade vazia). **MAS nos 4 cursos SEM gold de
subunidade (weak-only, `simula_propaga_semgold_weak.log`): MF 6 mudancas, CG 9, FR 0, LR 0 — varias visivelmente erradas** (CG
`transformacoesgeometricas` -> recorte, `aula-gravada` da Morfologia -> a-matematica-das-projecoes, `slab` geometria-comp -> operacoes-com-
vetores; MF `hoare` logica-de-hoare -> verificacao-de-programas). Sem rescore dos confiantes o CG ainda perdia 8 decisoes confiantes (19 mudancas).
**Nao entra no motor: saldo nos 8 desconhecido sem gold.** Caminho sem LLM = humano: gold de subunidade do CG (e MF) proposto-claude para
aprovacao do user (formato de 25/08), depois remedir nos 8 (C5, "gold proprio ou ruling"); ou pino/glossario manual para os 4 do IA (curadoria).
Fora disso, o que sobra e voto (LLM) ou pino (camada humana), por desenho.

## C1 ITEM 3 — `title` DO MANIFEST = `moodle_label` (05/09 tarde, sessao 6, MEDIDO sem LLM; **FECHADO POR MEDICAO: REFUTADO, 0 codigo**)
**Premissa do handoff:** o rebuild grava `title` = nome do arquivo e o piso sem-llm do CG caiu 10 -> 5; "medir title := label (fallback nome); se 0, fecha".
**Lido antes de medir:** o piso (`eval_travessia.escolher_sem_llm`) e o `entry_tokens` do disamb somam title + label num CONJUNTO; title := label
nao ACRESCENTA token, so REMOVE os que vinham do nome do arquivo. Leitores do `title` sozinho no motor: 9 (`leitores_title.py`); em 211/348
entries reescriviveis, mudam de saida: ordinal 0 · `_exam_number` 0 · prep 0 · stems do due 0 · datas 0 · numero de unidade 0 · `_REVISAO_RE` 2 (ES2
`servicos`/`web`, label "revisao de conceitos") · `split_camel_case(title)` no texto combinado 133 · `entry_tokens` 103 (token so do title perdido).
**Medicao A — piso sem-llm, title := label em memoria (0 chamadas):** IA (14 titles) 10/15 -> 10/15, hit@3 12 -> 12, bloco 6/8 -> 6/8 · FR (0
titles: sem label) 9 -> 9 · CG (67 titles) 5 -> 5, hit@3 6 -> 6, bloco 10/11 -> 10/11. **0 flip.** A queda 10 -> 5 do CG foi medida entre manifests
diferentes (export 73 x rebuild 93, gold re-chaveado) e NAO e o title.
**Medicao B — motor puro +vocab nas copias (baseline reproduzido 186/199 conf-err 1 · 183/191 · 53/57 · sub 82/93; holdout CG 31/35 conf-err 0 flagados 14):**
| regua | antes | title := label (143 titles nos 5; 67 no CG) |
|---|---|---|
| bloco | 186/199, conf-err 1 | **184/199**, conf-err 1 — MF `exercicios-conjuntos`, `exercicios-arrays` 13 -> 12 (gold 13; label "Respostas" perde `conjuntos`/`arrays`) |
| confiantes | — | MF `colecoes-arrays`, `colecoes-sequences` alta -> media + flag (label "Exemplos (Arrays)" perde `colecoes`) |
| unidade · cobertura | 183/191 · 53/57 | iguais |
| subunidade | 82/93 | **82/93** (a 1a rodada deu 81: era resumo de codigo NOVO do Gemini, nao o title — ver INCIDENTE abaixo) |
| holdout CG | 31/35, conf-err 0, flag 14 | iguais; 2 mudancas sem gold (`intro` sub, `fundamentosmatematicos` metodo); as outras 8 da 1a rodada eram resumo novo |
**0 flip positivo em regua nenhuma.** O nome do arquivo e o label do Moodle sao sinais COMPLEMENTARES: o label e generico onde o professor nomeia o
modulo pela funcao ("Respostas", "Exemplos (Arrays)", "Introducao"); o stem carrega o assunto. Nos 8: 103 entries tem token no title que o label nao
tem (MF 35, CG 34, ES2 23); 7 tem label sem token de conteudo e title com (MF 6 "Respostas", CG `vis2d` "Introducao").
**INCIDENTE (05/09 tarde): 60 chamadas Gemini NAO autorizadas.** O reprocess (`incremental_build` -> `_run_auto_code_summarization`) re-resume por
Gemini todo material de codigo cujo `content_hash` (bundle inclui o `title`) muda, quando a config da UI tem `gemini_auto_summarize=True` + chave
(estava: modelo `gemini-3.5-flash`; nao ha interruptor de ambiente). title := label mudou o hash de 60 entries de codigo nas copias (MF 19, SO 8,
IA 8, ES2 8, CG 17; 11:45-11:54) e a 1a rodada da B mediu com resumos NOVOS — dai SO sub 81 e as 10 mudancas do CG. Referencias: cache intacto (0
diferentes). Originais intactos (0 resumo de hoje). Correcao: tripwire em `c1-3/shim_b.py` (`get_gemini_client` -> None, `GeminiClient.__init__`
explode) + `c1-3/check_gemini_hoje.py` como pos-check; B REFEITA LIMPA (0 chamadas, `diff_b2.log`): bloco 184/199 e os 2 confiantes iguais, sub 82 = 82,
unidade/cobertura/holdout iguais. **Regra:** todo reprocess (registrado ou de medicao) que mude `title` ou conteudo de codigo chama Gemini com essa
config — medir SEMPRE com tripwire, ou desligar `gemini_auto_summarize` na UI enquanto o Gemini estiver bloqueado (decisao do user).
**Decisao (registrada em decisions.md):** `title` do manifest FICA o stem; o label e coluna (FILE_MAP, item 1), nao substituto. Item 3 fecha por medicao,
sem codigo; entra em NAO fazer. Achados para a fila LLM (so com Gemini liberado): (a) prompt do voter (`llm_vote.py:241`) mostra so `titulo`: 90/125
materiais votados tem label != title (CG 31, MF 31, ES2 16, SO 7, IA 5) — o voter ve "Vis3d", nao "Visualizacao 3D - Projecao"; adicionar linha `label
do Moodle` ao prompt e re-votar (<= 90 chamadas) e a alavanca com numero; (b) FILE_MAP titulo = label perde o stem em 103 linhas (7 sem token de
conteudo): "label · stem quando o title tem token que o label nao tem" so se a travessia LLM errar dessa forma.
**Censo remedido nesta sessao (originais):** revisar/100 **57,8** (handoff 58,0) · votos/100 **35,9** (36,5): MF pinos 4 -> 6 (arvores, listas, gold pelo
oraculo) = 2 votos a menos (2/348 = 0,6) — consistente, nao isolado. FILE_MAP 100% nos 8 (SO 38/39 duplicata). Suite 2324 · `src/` intocado.
Harness: `_harness-2026-09-04/c1-3/` (medicao A, shim da B, snapshot/diff, leitores, logs).

## GOLD PELO ORACULO (05/09 ~04h30, decisao do user: SARC e Moodle mandam; gold e humano)
**Mudancas no gold (nota `SARC/Moodle 05/09 (user)` na coluna provenance):** TCC `aula-17-np-completude-pdf` bloco-22 -> **bloco-19** (SARC: sessao
"complexidade de tempo np complete" no 19; postado 22/05); MF `arvores` e `listas` bloco-06 -> **bloco-05** (SARC: "provas por inducao listas e arvores");
`intro`, `exemplos`, `provas` ficam no 06 (Isabelle). IA `prova-1-2024-02` -> `scorable=no` (prova antiga 2024/2). **Regua de bloco passou a honrar
`scorable`** (`load_labels_csv`; a de unidade ja honrava) — denominador 200 -> 199; teste novo.
**Reguas remedidas (mesmos manifests, so o gold mudou):**
| regua | antes | depois |
|---|---|---|
| motor puro +vocab (copias) | 183/200 (91,5%), conf-err 2 | **186/199 (93,5%), conf-err 1** |
| curada (originais) | 199/200 (99,5%), conf-err 0 | **195/199 (98,0%), conf-err 1** — MF 64/66 (arvores, listas: produto respondeu 06 por voto), TCC 24/25 (22, agora conf-err) |
| unidade · cobertura | 183/191 · 53/57 (puro); 191/191 · 55/57 (curada) | iguais |
**Curadoria aplicada (user 05/09 ~05h):** MF pinos `arvores`/`listas` -> bloco-05 (MF `afb83cb`); TCC card "Semana 12 - NP-completude" no
`.card_block_map.json` de [21, 22] -> [bloco-19] (TCC `13ced08`; o produto vinha por janela-1 desse card curado, nao por voto). Reprocess sem LLM (votos
cacheados; sem chamada nova). **Curada 195 -> 198/199 (99,5%), conf-err 0**; o 1 que falta e ES2 `azure` (imagem sem texto -> C7). Sentinela 0/8.
Natureza: fixes ESPECIFICOS por desenho — pino e mapa de card sao a camada humana da arquitetura; a raiz aqui era humana (card curado errado; voto sem
sinal estrutural). Fixes de raiz desta sessao ficaram no motor (11a, item 10) e no roteador (C1 itens 1-2).

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
**Alavanca 'janela do card = secao inteira' medida e REFUTADA (05/09 ~03h, copias motor puro, MF+ES2 = os 2 cursos com `moodle_week_label`):**
(a) janela = blocos entre a semana da secao e a da proxima, desempate lexical dentro dela, para TODOS os materiais da secao: 72 -> 56 acertos (-16),
45 flagados — perde card datado/ordinal/titulo-topico que hoje acertam; e a semana da secao nao delimita ("Provas por Inducao" comeca 30/03 e tem 8
materiais no bloco-04 de 11/03). (b) so onde o motor decide por card com janela-1 (27 casos com gold), janela = blocos dos irmaos confiantes da
secao: 21 -> 15 acertos, 25/27 flagados; `.thy` se dividem (`intro`/`provas` -> 06 certo, `arvores`/`listas` ficam no 05). **A janela-1 pelo label do
card e, com numero, a melhor aposta estrutural (21/27); o resto e voto (cacheado) ou humano.** Sai da caixa.
**Alavanca 'data de postagem -> ultimo bloco-aula ate a data' medida e REFUTADA (05/09 ~03h30):** so 52 materiais com gold tem data real (a modal e a
data de montagem do curso: MF 46/66 em 18/02, IA 45/59, SO 33/39; CG sem datas); acerta 33/52 (63%): SO 4/4, IA 7/7, ES2 5/7, TCC 11/19, MF 6/15; nos
flagados 4/9 (conserta MF `introducao-zip` e `terminacao`, erra 5). Como decisor criaria confiantes errados; como desempate dentro da janela nao
alcanca os 2 (gold fora da janela). Nao entra.
**Sinais por erro (medido):** H9 contem o gold em 5 dos 14 erros de AULA (revisao, introducao, exerciciosformalizacao, dafny2, terminacao) mas 2 deles
sao confiantes (revisao, dafny2) e o card nao sobrepoe confianca (medido 02/09: a tudo +13/-10). Nos 5 `.thy` nenhum sinal estrutural aponta o 06.
**Perguntas do user (05/09 ~04h) medidas:** (1) trabalhos por postagem+entrega: nenhum manifest tem `duedate` (export nao traz; pull da API do CG nao tem
modulos assign/dates) — a janela de prazo hoje vem do SARC e acerta 7/9 trabalhos/provas do gold; **dado a capturar na SYNC** (`dates` de assign/quiz do
`core_course_get_contents`) antes de virar alavanca. (2) `revisao` fora dos stems genericos: 50 -> 50, nada muda; o titulo do card ja e a janela [03, 04].
(3) H9 sobre decisao confiante que contradiz o card ordenado: 2 casos — `dafny2` vira flag (voter acerta) e `exemplos` quebra (06 -> 05): saldo 0.
(4) `.thy`: o titulo do card "Provas por Inducao" e a sessao do SARC do bloco-05 ("provas por inducao listas e arvores") sao o que manda para o 05;
so o tipo de arquivo (.thy = Isabelle) aponta o 06, e a janela e de 1 bloco. Vocab compilado ja esta ligado no motor puro +vocab.
**Fecho da frente 'corrigir os erros do motor puro' (user 05/09):** 4 alavancas medidas, 4 refutadas com numero (label x2/x3; janela = secao, 2 formas;
data de postagem). O que sobra e voto cacheado (produto: curada 199/199) ou pino humano. Sem sinal novo do Moodle, nao ha o que codar.
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
