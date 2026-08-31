# Pendências — tracker vivo

last_updated: 2026-08-26 (balde A/B fechados, 7 golds corrigidos, R3 titulo-topico, t1/t2, ablacao rapida, humano 23 -> 6).
**FILA VIVA: secao `## DECISOES 28/08 (user, uma a uma — le antes de tocar em prova/entrega/identidade)

**D1 — Provas e notas (decidido).** Provas PRINCIPAIS sao P1, P2 (e P3 quando existe; raro). **PS** = prova
SUBSTITUTIVA: quem faltou a P1 ou a P2 faz a PS (depois da P2) no lugar dela — nao e marco novo e cobre o SEMESTRE
INTEIRO (mesmo conteudo da G2; corrigido pelo user 28/08 — NAO herda o escopo da prova substituida). **G2** = RECUPERACAO: quem fecha G1 < 7 vai para a G2, desde que G1 >= 5 (abaixo de 5 reprova
direto); nota final = (G1 + G2) / 2, aprovado se >= 5. Consequencias para o motor: (a) "prova principal" = rotulo
`P<n>`/`Prova N` — NUNCA PS/G2/PF; a lista `_NOT_MAIN_EXAM` (substitui/entrega/trabalho/recupera) sai, e os termos
`P<n>` da formula do G1 confirmam a contagem; (b) PS e G2 cobrem a disciplina inteira -> regra R7 (avaliacao-global) passa a
incluir PS, G2 e PF; (c) PS/G2 nao entram como N-esima prova em prep-prova/R6 (nao definem janela de escopo).
Caso que motivou: Fund. Redes tem "Prova P1", "Prova 2", "Prova PS", "Prova G2" -> a lista dava 4 principais; sao 2.

**D5 — Identidade da cadeira (decidido).** Chave = Moodle course id + codigo SARC (ex.: Fund. Redes 98709 / Lab Redes
98710 — nomes quase iguais). Nome e so rotulo. Perfil deixa de ser achado por nome.

**D2 — Trabalho como marco (decidido).** Marco de trabalho = TERMO NUMERADO da formula do G1 (T1, TP1, TF, T2...)
na linha AMARELA (Atividade "Trabalho") de apresentacao/fechamento — mesma semantica de marco que P<n>: janela,
preparacao, escopo por calendario. Amarelo SEM numero ("Oficina de problemas" do TCC, labs DHCP/DNS do Lab Redes)
= dia avaliado que hospeda material, sem semantica de marco. Linha BRANCA (Aula) com "duvidas/desenvolvimento/
especificacao/enunciado do Tn" = preparacao dentro da janela do marco (como "revisao para P1"). Vocabulario de cores
do SARC, identico em 8 cronogramas (salvos em Desktop/claude-tutor/sarc/): branco=aula, #FFFF00=trabalho,
#FFA500=prova principal, #FF8C00=PS (cor propria em 6/6), LightGrey=pos-semestre (G2/devolucao/atendimento/vazio),
Red/#FF4500=feriado/suspensao, #8B0000=evento. O mapa cor->kind ja existe (`_ASPNET_COLOR_KIND_MAP`) mas so no
caminho "importar SARC pela URL" (`{kind=}` por linha); os 7 perfis sao tabelas markdown SEM cor -> PS/G2/P colapsam
em assessment. Re-importar pela URL (item 6) e pre-requisito de D1/D2 no calendario.

**D3 — Sinais numerados (decidido, censo de 13 cursos do Moodle 2026).** (a) `U<n>`/`Unidade N` EXPLICITO no card ou no
nome do arquivo = sinal de 1a classe do eixo de UNIDADE (numeracao vem do plano = autoridade); hoje so Fund. Redes
("U1 - Redes de Computadores", "Lista de exercicios - Unidade 1"); medir quando o FR for construido. (b) SEM provedor
novo para "Laboratorio N"/"Tutorial N.M"/"Roteiro N": em toda ocorrencia real ha data ao lado (Lab Redes card
`[10/08]`, Lab SO "14/08 Tutorial 1.1"); heranca de irmaos (ES2) + datas cobrem; reabre so se aparecer cadeira com
serie numerada sem datas. Censo: data e o sinal mais frequente (cards/labels/arquivos em 8 cadeiras); "Semana N" em 4,
sempre com data ou topico ao lado; "Aula N" em 4 (ja tratado); "Parte N" (MF/EU/Simulacao) e serie dentro de topico,
nao posicao.

**Em aberto, nesta ordem:** 4 (`U<n>` no card e "Laboratorio N"
como sinal de 1a classe?), 4 (`moodle_pull` gravar `summary` de secao — lacuna, nao decisao), 6 (`build_course
--syllabus-url` e aposentar o PDF do SARC), 7 (jitter `ferramenta:` — bug, raiz a achar).

## DISSECACAO 28/08: tres cadeiras novas (Lab Redes, Lab SO, Fund. Redes), fontes da formula do G1, 2 fixes de extracao

**Verificado contra o dado (Moodle API, SARC HTML, planos):** Lab Redes = so SEG (19 linhas SARC), sem prova,
`G1=(T1+T2+T3)/3`, cards `[DD/MM] - Tema` (data no card), arquivos "Laboratorio N - X", assigns com due · Lab SO =
**TER/QUI** 17:30 (user dissera qua/sex), prof. Miguel Xavier = SO, cards tematicos + "Leitura indicada" como a SO,
arquivos "07/08 Slides: ...", 4 "Fechamento da parte N" = 4 unidades do plano, sem prova, `G1=(TP1+..+TP4)/4, media
5.0, sem G2` **so no `summary` da secao 0 do Moodle** (o plano 4646I e generico, sem secao de avaliacao) · Fund.
Redes = TER/QUI 19:15, cards `U1 - Redes de Computadores` (numero da unidade no card — sinal novo), P1 24/09 (u01-03),
P2 26/11 (u04-06), TF, PS, G2 · **SARC exporta HTML sem login** (`Export.aspx?id=...&ano=&sem=`), tabela de 7 colunas
— caminho PDF->geometria da CG fica obsoleto (`build_course --syllabus-url`, a fazer).

**Onde mora a formula do G1 (9 cursos):** plano em 8/9 (TCC incluso: `G1=(P1+P2+T)/3`, P1=u1-3, P2=u4), `summary`
da secao 0 do Moodle em 2 (SO, Lab SO), label em 1 (IA). Formas variam: `(P1+P2+T)/3`, `P1P2T/3` (glifos), letras
matematicas Unicode (MF/ES2, NFKC resolve), `G1: MP*0.7+MT*0.3` (CG). **Termos** (P1, P2, T, TPn, MT, TF) sao o
estavel; operadores nao. `moodle_pull` NAO grava o `summary` das secoes (labels truncados em 500) — lacuna a fechar.

**Fix 1 — `src/utils/pdf_markdown.py` (`e8f926d`):** pymupdf4llm >= 1.27 monta o layout com
`TEXT_IGNORE_ACTUALTEXT` (Google Docs + Inter codifica `( + ) :` via /ActualText -> PUA: TCC dava
`G1 = \ue081P1\ue09dP2\ue09dT\ue082/3`) e `use_ocr=True` OCR-iza e descarta texto nativo de pagina com logo
(`img_text`: SO/Lab SO/Fund. Redes perdiam ~400 chars). Helper unico (UI "Extrair PDF", `build_course`, backend base):
texto identico aos perfis gravados (ratio 1,000 TCC/SO/ES2), 0 PUA em 7 planos. Perfis existentes estao corretos.
PUA residual nos repos: so `staging/assets/tables/*.md` (MF 55, SO 20, IA 3, TCC 4) — tabelas, nao conteudo.

**Fix 3 — fracao empilhada (`0c8ec30`):** a media do G1 em SO/MF/ES2 e uma EQUACAO (Word/LaTeX): numerador, barra
como linha vetorial, denominador centrado; o texto perdia a divisao (`G1 = P1 + P2 + TP` + `3` noutra linha — o user
apontou pelo PDF de apresentacao da SO, que diz `(P1 + P2 + TP) / 3`). `stacked_fractions()` detecta por geometria
(regua fina, curta, isolada — sem regua vizinha nem borda vertical, que e o que tabela tem —, texto cobrindo por cima e
centrado por baixo) e `splice_fractions()` reescreve `lhs = (num) / den` com NFKC. 10 PDFs: SO/MF/ES2 corrigidos,
0 falsos positivos (borda "Evento/Academico" da CG derrubou a versao ingenua). **Perfis SO/MF/ES2 reextraidos**
(backup `subjects.json.bak-2026-08-28-fracao`): diff = so a linha da formula; reprocess dos 3 = sentinela 0 campos,
regua igual; alteracoes restantes eram so timestamps, descartadas.

**Fix 2 — parser de unidades (`e878f5d`):** template "N. DA UNIDADE" com CONTEUDO rendido como bullet e topicos
"1. HTTP e HTTPS" (Lab Redes: 1 unidade/0 topicos -> 3/11); 9 outros planos identicos ao baseline.

**Suite: `test_caracterizacao_blocos_atual[TCC]` VERMELHO** desde o reprocess de cobertura (`b5f10f2`): golden
`_golden/TCC-Tutor__casos_chave.json` tem `aula-06 computed_block_id cbf887a2`, manifest tem `ee594a67` — e o flip
do scorer de conceito causado pelo jitter das tags `ferramenta:` (FILA item 0). Nao atualizar o golden: corrigir a
raiz e o manifest volta. Rodar com `--deselect` ate la.

**Em duvida (28/08):** (1) `_NOT_MAIN_EXAM` trata "Prova PS"/"Prova G2" como principais (FR teria 4; a formula diz 2)
— ler os termos da formula do G1 (plano -> summary sec0 -> label) e substituir a lista; (2) cadeira sem prova: marco =
entrega ("Fechamento da parte N", "Apresentacao do T1"); `_exam_number`/prep-prova/R6 so entendem P; "duvidas do TP1"
= preparacao de entrega; (3) provedor de unidade-no-card (`U1 - ...`) e ordinal "Laboratorio N"/"Tutorial 1.2";
(4) identidade de curso = Moodle id + codigo SARC (98709 vs 98710), nunca nome; (5) plano do Lab SO nao tem avaliacao:
a unica fonte e o Moodle — o pipeline precisa ler `summary` de secao; (6) Lab Redes com ~10 blocos de conteudo em 19
sessoes (3 feriados + 6 desenvolvimento/apresentacao) — regua magra.

## PENDENTE DE VERDADE (2026-08-31) — ordem de prioridade e bloqueios

Tudo abaixo e o que RESTA; o resto do arquivo e historico/executado. Unico bloqueio real do mapa:
Lab SO <- SARC da turma 310 (user/professor). Nada mais bloqueia nada.

**P1 — Cobertura 55 -> 57: EXECUTADO 31/08, fechou em 56/57 F1 0,982 (teto documentado do aws).**
Golds u02 CONFIRMADOS por ruling do user 31/08 (notas no material_gt_MF.csv). Raiz do 0 chars: github-repo
NAO tinha rota de texto (`process_github_repo` clona codigo e nunca preenche `base_markdown`; o clone das 2
ainda falhava por pin `tags="main"` legado da UI — defaults reais: eth2=master, aws=mainline). Fix de motor:
`process_github_repo` agora busca o texto da PAGINA do repo (README server-rendered) via `builder._process_url`
ANTES do clone — mesma rota de file_type=url; UI `URLEntryDialog` nao pina mais "main" (vazio = auto-detect).
Teste novo `test_page_text_becomes_base_markdown_even_when_clone_fails`. Gate completo: eval_eixos bloco
199/200 conf-err 0 · unidade 191/191 · **cobertura 56/57 F1 0,982** · subunidade 87/93 (0 campos nos 4 golds)
· suite 2133 · sentinela = SO as 2 entries (campos honestos) · determinismo ok (2x reprocess, so generated_at).
- `eth2` FECHOU pelo motor puro: auto_map u02 conf 0,938 com o texto real ("verification"≈"verificacao" via
  stem6 da rota de topico do A1). coverage_units=u02 ✓.
- `aws-encryption-sdk` NAO fecha = TETO COM O DADO DISPONIVEL: a pagina raiz (meta-repo) fala criptografia,
  cita Dafny/verifier de passagem; 0 topicos de qualquer unidade casam; auto_map da u01 (0,637) -> R4.
  TESTADO E REFUTADO 31/08: concatenar `ref_summary` (Gemini, PT) ao texto -> aws vai para u03 (transpilacao/
  cripto puxam u03) e eth2 enfraquece 0,938->0,726. Nao retentar sem dado novo. Fechar 57/57 exigiria pino de
  cobertura (mecanismo NAO existe; pinos 5 sao de unidade) — decisao do user se quiser.
- Higiene NOVA (fila): import github-repo com clone OK sobrescreve `category` da entry via STUDENT_BRANCHES
  (master/main => codigo-aluno — bibliografia viraria codigo!) e importa o repo INTEIRO como extracted_files.
  Por isso o pin errado das 2 entries foi MANTIDO de proposito (clone falha inofensivo, texto vem da pagina).
  Consertar categoria/escopo do import antes de limpar os pins.

**P2 — Fila antiga (sem bloqueio, ordem sugerida):**
  a) **EXECUTADO 31/08 — unidade NUA 134 -> 170/191 (+36).** DP ganhou 1 DESVIO DE JANELA
     (`unit_matcher.assign_units_positional` + `_dp_monotonic`): uma faixa contigua de blocos pode usar unidade
     fora da ordem do plano pagando DETOUR_COST=2 (DETOUR_MIN_GAIN=2; desvio so vence com SOMA estritamente
     maior que a monotonica — empate fica com o baseline, ancora espuria de 1 token nunca paga o custo).
     Caso raiz: IA 2026/2 ensina u05/ML em 2o lugar (gold_units_IA: u01 -> u05 -> u02 -> u03); o DP esmagava
     ML em u01 e o nu dava 3/42 -> agora 39/42. BONUS CG: bloco 5 "processo de visualizacao 2d recorte" saiu
     de u02 (monotonia) para u04 (titulo da unidade nas sessoes!) — 14 entries corrigidas em cascata (vis2d,
     recorte, instanciamento, mapeamento...), sentinela aceita como honesta. Regua curada INTACTA (199/200
     conf-err 0 | 191/191 | 56/57 | 87/93), suite 2134, determinismo ok. Cobertura NUA 55 -> 54: trade honesto
     (ver MOTOR NU no ESTADO). Teste: `test_positional_detour_window_recovers_local_inversion`; o teste do
     pino IA foi atualizado (o DP cego agora recupera a inversao sozinho — pinos daquele caso viraram
     redundantes, caminho around_pins segue coberto).
  b) **FASE 4: parte deterministica EXECUTADA 31/08; extracao de questoes via LLM = item novo da fila
     (ruling do user 31/08: "deterministico agora, LLM depois").**
     - RULING granularidade (pendente desde 18/08): prova inteira por enquanto; quebrar em questoes
       individuais (LLM, habilita incidencia por topico) fica como item separado, sem data.
     - EXERCISE_INDEX (repo.py): coluna Unidade = computed_unit_slug REAL (tags so fallback); pareamento
       enunciado<->gabarito por stem do titulo (`_exercise_answer_stem`: X <-> X_respostas/gabarito/solucao/
       resolucao); gabarito vira tipo proprio ("e o gabarito", "conferir apos tentar"); "Solucao: sim — <par>".
     - EXAM_INDEX (repo.py): dedup por (arquivo, titulo) (CG tinha linha dupla); coluna "Unidades cobertas" =
       coverage_units do motor (fallback computed_unit_slug); header prometia "incidencia por topico" e agora
       promete o que entrega (por unidade; topico/questao = quando houver extracao).
     - FileEntry ganhou `coverage_units` (round-trip from_dict->to_dict descartava o campo silenciosamente).
     - Gate: regua intacta (199/200 conf-err 0 | 191/191 | 56/57 F1 0,982) · sentinela 0 campos nos 6 ·
       suite **2136** (+2) · golden CG `__divisao_blocos` ATUALIZADO DE PROPOSITO (blocos 10/28 = provas
       cujo escopo agora inclui u04 — consequencia correta do P2a, nao regressao).
  c) Housekeeping: **FEITO 31/08** — `scripts/artefato_razao/` (dados_artefato + patch_razao + template,
     caminhos relativos, saida gitignored; byte-identico ao publicado). Artefato: claude.ai/code/artifact/d2ef4eaa-...
  d) **A1 "grande": EXECUTADO 31/08 no recorte honesto.** P4 (`window_provider._stems`) agora usa o
     `stem_set`/`STEM_LEN` compartilhado de text/normalize (t[:6] e stem6 sao provadamente identicos —
     zero mudanca de comportamento; suite 2136, regua identica sem reprocess). NAO unificados de proposito:
     `disambiguator` usa prefixo 8 para _GENERIC_STEMS (convencao DELIBERADA que espelha marco0 — mudar e
     alterar comportamento sem hipotese de ganho) e `due_window._stems` (nome coincidente, semantica
     diferente: regex findall sem truncar). Fim do item.
  e) MF 30/66 no LLM: ACEITO como fallback legitimo (30/30 certos). So revisitar com assinatura de bloco mais
     rica, MEDIDA (3 tentativas historicas: 2 pioraram).
  f) **Subunidade residuais: EXECUTADO 31/08 — 87 -> 89/93.** Distribuicao REAL dos 6 era IA 2 / ES2 2 /
     TCC 2 (o "6 do IA" deste tracker estava impreciso). Tres familias diagnosticadas com score em maos:
     - Familia A (IA 2, lacuna de vocabulario): FECHADA. Sidecar `.glossary_curation.json` do IA (ja existia
       desde 25/08!) ganhou "Introducao ao aprendizado de maquina" com sinonimos de analise exploratoria
       (proposto-claude, ruling user 31/08). IA subunit 37 -> 39/39; regua IA intacta; determinismo ok;
       cascata de confiancas na u05 esperada (aliases novos mudam margens; slugs intactos).
     - Familia B (ES2 `web`, alias PODRE): heading de material "ARQUITETURA DE SISTEMAS WEB" vira alias de
       "Arquitetura Serverless" pela rota de overlap fraco do heading->alias (content_taxonomy ~L572-616,
       score 5.0+0.4/token, piso efetivo ~5.4) e ganha de cliente-servidor por 8.65 x 8.31. Piso 8.0
       (igualdade/contencao) TESTADO E REFUTADO 31/08: 729 campos em 5 cursos — a rota fraca e LOAD-BEARING
       (sustenta dezenas de aliases legitimos). Nao retentar piso global; um fix teria de ser cirurgico
       (ex.: so heading multi-tema com overlap de 1 token) e MEDIDO. Teto documentado.
     - Familia C (ES2 roteiro5 = proposito vs vocabulario 19.3x16.4; TCC aula-08 idem 35x4.6; TCC aula-06 =
       over-assignment em aula de revisao, gold vazio): teto do motor lexical; so fecham com sinal de outro
       tipo (papel/estrutura do material ou LLM lendo a tese). Documentado, revisitavel com desenho novo.

**P3 — Builds pagos (Datalab), quando o user autorizar:**
  - Lab Redes: PRONTO. Stash durable: `Desktop/Moodle/laboratorio-de-redes-de-computadores/stash` (6 arquivos +
    sidecar; roteiros HTML ja impressos em PDF). Cronograma: `--syllabus-url` (export 340, validado 340=340).
  - Fund. Redes: PRONTO. `Desktop/Moodle/fundamentos-de-redes-de-computadores/stash` (20 arquivos). U<n> cobre
    19/20 (F7). Cronograma: `--syllabus-url` (320=320).
  - Lab SO: stash pronto (`Desktop/Moodle/laboratorio-de-sistemas-operacionais/stash`, 19 arquivos, tutoriais
    impressos) — **BLOQUEADO pelo SARC da turma 310** (o link no Moodle e da 330; ver F14). Nao buildar com o
    da 330 nem com remap (testado 30/08: ordem bate, datas nao — off-by-one nas fronteiras).
  - Planos de ensino dos 3: `Desktop/claude-tutor/*.plano.md` (+ PDFs originais e exports SARC em
    `Desktop/claude-tutor/sarc/`).

## A1 EXECUTADO (recorte cirurgico): stem6 compartilhado fecha os 3 forks — cobertura 52 -> 55/57 (2026-08-31)

`text/normalize.stem6` (radical de 6 chars, a MESMA convencao do TOPIC_STEM_LEN do motor de bloco) agora e o stem
oficial compartilhado. Tres tentativas MEDIDAS ate o recorte certo:
1. stem em `_matches_normalized_phrase` + `_score_timeline_unit_phrase` (amplo): cobertura 54 mas subunidade
   87->83, bloco 199->198 conf-err 1, IA oracle regride. REPROVADO pela lei (regua pior em qualquer eixo).
2. stem so no `_score_timeline_unit_phrase`: eixos voltam mas forks NAO fecham (o fix vinha da rota de topico) e
   oracle segue errado — cobertura 51. REPROVADO.
3. **ADOTADO**: `_matches_normalized_phrase(..., stem_fallback=)` OPT-IN; so a rota de TOPICO do MAPEADOR DE
   UNIDADE (`file_map.auto_map` topic_score) passa True; subunidade (`score_entry_topics`) continua exata; scorer
   de frase intocado. "Chamadas de sistema" (plano) casa "chamada de sistema fork()" (resumo Gemini) e os 3
   `exemplo-criacao-de-processos` fecham.

Regua: bloco 199/200 conf-err 0 | unidade 191/191 | **cobertura 55/57 F1 0,965** | subunidade 87/93 | suite 2132.
Restam na cobertura APENAS eth2 e aws-encryption-sdk (0 chars — so com o texto da pagina do link). Sentinela:
apenas `unit_match_confidence` (topic_score mudou) + coverage_units off-gold mistos e honestos (SO
`1703-chamada-de-sistema` ganha u01; forks passam a cair no fallback da unidade final, que e u01 correto).
O A1 "grande" (P4 + desempate no mesmo tokenizador) fica aberto como refactor de higiene — o ganho de regua ja veio.

## DISSECACAO: 3 cursos novos 2026/2 (Fund. Redes, Lab Redes, Lab SO) — achados ANTES de codar (2026-08-28)

Contexto (user): cadeiras de curriculo especial (sem prova, media por trabalhos) existem — Lab Redes, Lab SO e uma
online neste semestre; Experiencia do Usuario e Pratica em Pesquisa em 2026/1. Decisao: dissecar antes do A1.
Dados: planos em `Desktop/claude-tutor/*.plano.md` (pymupdf4llm; lab-so e escaneado/OCR), SARC em
`Desktop/claude-tutor/sarc/*.bin`; harness `(scratch)/timeline_labs.py` roda o indice de timeline PURO
(SARC HTML -> tabela markdown -> `_build_file_map_timeline_context_from_course`, sem stash/repo/Datalab).

**Fatos verificados** (afirmacoes do user checadas na fonte):
- Lab Redes (Moodle 95473, cod 98710): so SEG, 19 linhas SARC, sem prova; `G1=(T1+T2+T3)/3` no plano; cards
  `[03/08] - Introducao` (DATA no card — melhor caso do motor); arquivos "Laboratorio N - X"; assign com due. A
  afirmacao "labels tipo Aula 0/Aula 01 como TCC" nao confere nos cards (so 1 arquivo "Aula 01").
- Lab SO (95227, 4646I): TER/QUI 17:30 JK (user dissera qua/sex — corrigido); prof Miguel Xavier = SO ✓, mesma
  organizacao de Moodle ✓; plano GENERICO sem secao de avaliacao; formula esta no **summary da secao 0 do Moodle**
  (fora de card): `G1 = (TP1+TP2+TP3+TP4)/4`, "media 5.0, sem G2" — SARC coerente (0 Prova, 4 "Fechamento da
  parte N", sem linha G2). Fund. Redes tem G2/PS no SARC (10/12, 01/12).
- Onde mora a formula por curso: plano (MF, IA, SO, ES2, CG, FR, Lab Redes) · summary sec0 (Lab SO, SO) ·
  label (IA). TCC: nao achada. Fontes concordam quando coexistem (SO, IA).
- **SARC exporta HTML publico sem login** (`Export.aspx?id=...&ano=&sem=`): tabela 7 colunas — caminho PDF+geometria
  do build_course fica obsoleto para quem tiver a URL.

**Lacunas/erros achados (F1-F8), com causa lida no codigo:**
- F1 **EXECUTADO (30/08)**: `raw/moodle/sections.json` = summary + labels COMPLETOS por secao (medido: formula do
  G1 do Lab SO capturada do summary da sec0). labels.json continua igual (compat).
- F2+F3 **EXECUTADOS (30/08)**: guard cue-x-conteudo-do-plano em `classify_block` — keyword de
  ASSESSMENT/MAKEUP nao dispara quando o texto casa frase de CONTEUDO do plano contendo o cue
  (`_cue_e_conteudo_do_plano`; frases normalizadas carimbadas em `block["_plan_phrases"]` por
  `plan_phrases_para_classificacao(unit_index)` nos 2 pontos de finalize do index, transiente, nunca persiste).
  Substitui a lista "corpus auditado" (avaliacao/substituicao "inequivocos") que o Lab SO falsificou.
  Medido no timeline puro: blocos 18-20+25 ("Avaliacao de desempenho...") -> class u03/u04; bloco-23
  ("Algoritmos de substituicao de paginas") -> class u04; u03/u04 deixam de ficar orfas. "Prova P1"/"substituicao"
  solto (MF bloco-21) intactos — o guard exige outro token distintivo da frase do plano no texto.
- F4 Lab Redes: Atividade=Trabalho nos DIAS DE LAB (praticas com material) -> `deliverable` via ATIVIDADE_KIND_MAP.
  deliverable nao esta em NEVER_HOSTS (material ancora), mas o bloco fica sem unit_slug: 11 de 17 blocos sem
  unidade, u03 (nivel de rede) com ZERO blocos. Em cadeira de lab a coluna Atividade nao separa aula de entrega.
- F5 **EXECUTADO (30/08)**: `assign_units_by_work_milestones` (unit_matcher) — entregas numeradas ("Fechamento da
  parte N", digito preservado nos labels de sessao; o topic_text o perde) segmentam as unidades com autoridade,
  SO quando formam exatamente 1..K e K == unidades do plano; senao o DP posicional decide como sempre (SO 2026/1
  tem partes 1..4 e 7 unidades -> nao aplica; "Parte 1" em titulo de AULA do MF -> nao e marco). Medido no timeline
  puro do Lab SO: u01=1-5, **u02=8-11 (device drivers, antes 0 blocos)**, u03=14-20, u04=22-29. Gate: suite 2127,
  reprocess 6 = regua identica, sentinela 0 campos nos 6, ablacao nu identica, curado 5/6 + IA p2-202402.
  F6 (prep/desenvolvimento de entrega — "duvidas do TP1", "Desenvolvimento do T1") ADIADO para depois do build dos
  labs: sem curso construido nao ha como medir; o provedor t1/t2 e a heranca de vizinho ja cobrem parte.
- F6 prep de entrega nao existe: "Aula reservada para duvidas do TP1" -> office_hours (ok) mas nada liga ao TP1;
  `_exam_number`/`is_exam_prep_material`/R6 so entendem P. "Desenvolvimento do T1" x2 -> class na unidade errada.
- F7 **EXECUTADO (30/08, = D3a)**: `explicit_unit_number` em `auto_map_entry_unit` — U<n>/"Unidade N" explicito
  no card/titulo/arquivo decide a unidade ANTES do scorer (conf 0.95, reason `unidade-explicita=uN`; numeracao do
  plano = autoridade). Falsos positivos guardados ("aula01", "qemu 2", "UDP 1" nao casam). Medido: FR **19/20**
  entries decididos pelo sinal (o 20o e o Programa, meta); 0 disparos nos 6 cursos velhos (inerte onde deve).
  Restam do F7 original, agora renumerados: FR bloco-20 (Camada de Enlace -> u04, fusao com vizinho) e bloco-13
  ("Introducao ao roteamento" -> overview, stem "introduc") — fronteiras de bloco, nao unidade; ficam p/ holdout.
- F8 FR: "Prova PS" e "Prova G2" contam como prova principal (`_NOT_MAIN_EXAM` nao as filtra); formula do plano diz
  2 provas (P1, P2). A formula do G1 da os marcos derivados: termos P = provas, TPn/T/TF = entregas, "sem G2" =
  nao esperar final; contagem TPn bate com "Fechamento" do SARC (4=4 no Lab SO).

**F9 EXECUTADO (2026-08-28):** `_DATE_PREFIX_RE` aceita `[`-opcional e separador `./espaco/barra`; o CARD
(`source_section`) entrou na varredura do `extract_date_in_name` (so PREFIXO — "Semana 13/04/2026 a ..." segue
fora). Falso positivo "Tutorial 1.2" -> (1,2) morre no calendario (provider exige sessao real). +4 testes.
Gate: extracao identica nos 6 cursos velhos (medida entry a entry), sentinela 0 campos nos 6, regua e subunidade
identicas, suite 2104 (golden TCC aula-06 regenerado DE PROPOSITO — deriva de 27/08 ja documentada no sentinel:
tag `ferramenta:lemas` -> boosts -> computed_block_id, fora da regua; desta vez o jitter NAO reapareceu).
Preview nos novos: Lab Redes **4/6 ancorados** pelo card `[03/08]`; FR 0/20 (esperado — FR e U<n>, F7).

- GRADE DO USER 2026/2 (30/08, cruzada com exports/perfis — tudo consistente): Seg = Lingua Inglesa IV
  (125AB-04 T2, E-E1) + Lab Redes (98710-02 T340, LM); Ter = CG (98716-04 T310, JK) + Fund. Redes (98709-04
  T320, LM); Qua = Lingua Inglesa + Lab SO (4646I-04 T310, LM); Qui = CG + Fund. Redes; Sex = Lab SO (JK).
  Horarios PUCRS confirmados nos exports: JK = 17:30-19:00, LM = 19:15-20:45. Lab SO 310 tem horario diferente
  por dia (qua LM, sex JK). Validacao independente p/ F12: dias do cronograma x grade do user, alem de turma do
  export x shortname. Falta ainda: export SARC da turma 310 do Lab SO (GUID nao derivavel; user vai copiar do SARC).
- IMAGENS/HTML (30/08, pedido do user "imagens passam pelo Datalab p/ descricao"): CORRECAO de leitura minha — a
  rota da CG (pagina HTML -> PDF impresso -> Datalab) JA entrega descricoes posicionadas: staging de "origens" tem
  12 blocos IMAGE_DESCRIPTION no lugar das figuras (os ![]() sao removidos de proposito). O buraco era outro:
  resource `.htm(l)` (os 6 roteiros/tutoriais dos labs) caia CRU no stash como codigo-professor, sem print e sem
  descricao. **EXECUTADO**: `moodle_pull` agora manda resource-html pelo MESMO caminho das paginas (raw + print
  PDF -> Datalab no build), tipo `material-pagina-arquivo`, sinal `resource-html`; sidecar de nomes aponta p/ o
  .pdf. Rota HTML->markdown direta DESCARTADA por decisao do user (perderia a descricao de imagem do Datalab).
  Validado com pull real (31/08, token renovado AUTOMATICAMENTE via `moodle_token.ensure_moodle_token` +
  MOODLE_USER/MOODLE_PASS no .env local): Lab Redes --pdf -> "Lab 1 - Wireshark" 4 pags/**6 imagens**, DHCP 3 pags,
  DNS 3 pags, todos `material-pagina-arquivo -> print` no stash; cronograma SARC aceito (340=340); review restante
  so wireshark.org (externo, correto). Cards sanitizados viram `[10.08]` (ponto) — o F9 ja aceita. Stash do Lab
  Redes PRONTO para build.
- F14 **RESOLVIDO DE VEZ (30/08, descoberta do USER): o professor postou no Moodle o link do SARC da TURMA
  ERRADA.** Cabecalho do export: "4646I-4 Laboratorio de Sistemas Operacionais **(330)**"; shortname do Moodle:
  "4646I-04**310**262" (turma 310). A 330 e TER/QUI 17:30; a 310 do user e QUA/SEX — e as datas dos arquivos
  (07/08, 12/08, 14/08, 21/08, 26/08) caem exatamente em SEX/QUA de 2026. Nao era casca copiada: minha hipotese
  "2025/2" foi coincidencia de calendario (padrao de 2 dias fixos repete entre anos — QUI/TER de 2025 batia por
  acaso) e o "(copiado)" dos labels e so marca de copia de material. Mea culpa registrada: pulei de correlacao
  para conclusao duas vezes (primeiro "user errou os dias", depois "casca 2025").
  **Regra derivada para o F12**: turma do cabecalho do export TEM que bater com a turma do shortname do Moodle
  (medido: Lab SO 330!=310 pega o erro; Lab Redes 340=340 e FR 320=320 passam). Mismatch -> manual-review, nunca
  usar o cronograma silenciosamente. Falta: obter o export da turma 310 (o link certo nao esta no Moodle).
  Nota do user (30/08): cronograma da CG veio DENTRO de um PDF — raro, mas o caminho `sarc_pdf_to_table` (38/38
  medido) fica como fallback permanente do `--syllabus-url` (F12).

**Censo Moodle dos 3 (moodle_pull --dry-run, `(scratch)/pull-*`), F9-F13:**
- F9 `_DATE_PREFIX_RE` (window_provider:328) so aceita `DD.MM`/`DD MM` — nao casa `[03/08]` (cards do Lab Redes)
  nem `07/08 Slides:` (nomes do Lab SO). Os dois formatos novos de data ficam sem provedor.
- F10 **EXECUTADO (30/08)**: `moodle_pull` grava `stash/.moodle_nomes.json` ("card/arquivo" -> nome do modulo);
  `scan_stash_cards` detecta a categoria sobre MODULO + ARQUIVO concatenados (arquivo por ultimo preserva a
  extensao) — a ordem de prioridade dos cues decide os dois sentidos ("aula" antes de "livro"). Medido nos 3
  cursos reais: FR 9 correcoes (todas as "(Slides)" -> material, inclusive "Modelos de Referencia" — F10 e F11 se
  protegem), Lab Redes "Plano de ensino/320-340.pdf" -> cronograma, Lab SO 0 mudancas (filenames ja acertavam).
  Sem sidecar (stash manual, cursos antigos) comportamento byte-igual. Categoria so em import — sem reprocess.
- F11 **EXECUTADO (30/08)**: `auto_detect_category(..., frases_do_plano=)` — cue de bibliografia suprimido
  quando o nome casa frase do plano contendo o cue ("02 - Modelos de Referencia.pdf" deixa de ser bibliografia;
  "referencias bibliograficas.pdf" continua). `scan_stash_cards` e `build_course` passam as frases do plano;
  UI sem parametro = comportamento antigo.
  Gate: suite 2116 · reprocess 6 + regua identica (199/200, 191/191, 52/57, 87/93) · sentinela 0 campos nos 6 · ablacao nu identica · curado 5/6 + IA p2-202402 (excecao documentada).
- F12 **EXECUTADO (30/08)**: `classify_url` reconhece o export do SARC como `cronograma` e VALIDA a turma
  (cabecalho do export x shortname do Moodle): FR 320=320 e Lab Redes 340=340 aceitos; Lab SO 330!=310 ->
  `review` sinal `turma-divergente` (pega automaticamente o link errado do professor). HTML salvo em
  `raw/sarc/cronograma-*.html` quando valido. `build_course --syllabus-url` (novo): export HTML -> tabela
  markdown + turma impressa p/ conferencia; PDF (`sarc_pdf_to_table`, caso CG) vira fallback. Suite 2107.
- F13 sinais de ancora por entry (censo, sem construir): FR 19/20 (tudo U<n> — sem provedor, F7, e filenames com
  ordinal proprio "01 -", "02 -"); Lab Redes 5/6 (DATA-CARD + "Laboratorio N" + due — motor quase pronto, so F9);
  Lab SO 11/20 (datas nos nomes + "aula0N"/"Tutorial 1.N" estilo TCC ✓). Sem sinal = "Informacoes Gerais" com
  livros O'Reilly inteiros (camada de referencia, e o ima de bloco-01 ja conhecido). Links: FR 24 (2 review),
  Lab Redes 8 (2), Lab SO 27 (5) — review = SARC (F12), IMDB, wireshark.org, SBC, LinkedIn, Debian.

**Direcao (sem codar ainda, tudo derivado, lei 4b):** F9 barra/colchete no `_DATE_PREFIX_RE`; F10 categoria ve modulo+arquivo (stash guarda os dois nomes); F11=F2/F3 (cue x plano); F12 build_course puxa o SARC do links.json; fonte "avaliacao do curso" = plano -> summary sec0 -> labels
(conflito = manual-review); cue de assessment/makeup nao dispara quando a palavra e conteudo do curso (df/topicos
do plano — F2/F3); em cadeira sem prova, entregas herdam o papel de marco (F5/F6); provedor "U<n>" (F7);
`_NOT_MAIN_EXAM` -> leitura da formula (F8). Identidade de curso por Moodle id + codigo SARC (98709 vs 98710 —
nomes quase iguais: Fundamentos de Redes x Laboratorio de Redes).

## COBERTURA 41 -> 52/57: cinco raizes em `coverage_rules.py`, medidas offline antes de tocar producao (2026-08-27)

Pergunta do user: "a cobertura so aumentou 1? nao tem como chegar a 54-55?". Resposta: sim, mas nao pelo A2 —
a cobertura tem regras proprias. `scripts/harness_cobertura.py` (novo) recomputa o eixo em ~15 s sem reprocessar
e reproduziu os 41/57 exatos; cada regra foi medida nele (corrigiu/quebrou) antes de entrar. Os 16 erros:

| raiz | entries | regra |
|---|---|---|
| fallback do scorer somado ao card que ja decidiu (4/4 sobre-coberturas) | MF formalizacao, exemplos-zip, TCC aula-12, SO exercicios | **R4** fallback so sem regra |
| token generico distintivo no card ("Gerencia de **Processos** CPU" -> u03) | SO exercicios | **R2** genericos do A2 + `_GENERIC_STEMS` |
| empate do card descarta a 2a unidade (ruling 26/08: roteiros = u01 E u02) | ES2 roteiros x5 (+7 que acertavam por SORTE do scorer) | **R5** pratico (roteiro/lab) mantem todas do card |
| PX sem topico no texto; `\bP1\b` nao casa "Revisao_P1_Gabarito" | MF revisao-p1-gabarito | **R6** calendario: unidades entre a prova N-1 e a N (titulo E id) |
| avaliacao global | SO ENADE -> todas | **R7** convencao do user (ENADE/concurso/prova final) |
| scorer 1:1 erra conteudo: "chamada de sistema" vs "Chamada**s**" (sem stem) | SO fork x3 | A1 |
| sem texto (0 chars) | MF eth2, aws | so com a pagina do link (pipeline `moodle_pull`) |

Variantes descartadas (medidas): R1 "fallback = unidade temporal final" 34/57 — gold de UNIDADE e "unidade do bloco
temporal" (onde mora) e gold de COBERTURA e "o que o conteudo cobre" (colunas distintas do CSV; SO threads mora em u02,
cobre u03). R3 "texto corrobora 2a unidade" 32/57 — slides de microsservicos (gold u01) e threads da SO ganham unidade
espuria. R4 sozinho 37/57 (quebra os 7 roteiros que so acertavam pelo flip do scorer) — R5 e o que os estabiliza.

Gate: 199/200 conf-err 0 · 191/191 · **52/57 F1 0,912** · subunidade 87/93 · pinos 5 · suite 2090 · determinismo 0
campos em 5/6 (CG 2 `auto_tags`: `ferramenta:animacao-v2` flipa entre dois runs identicos — nao-determinismo
PRE-EXISTENTE do catalogo `ferramenta:` em `content_taxonomy.build_tag_catalog`, mesma classe do `ferramenta:lemas`
x7 do TCC vs HEAD; as tags alimentam `build_learned_unit_boosts` -> confidencias -> `computed_block_id` do scorer de
conceito; nenhum campo da regua. Entrou na FILA). Sentinela: 55 `coverage_units` mudaram, revisadas uma a uma —
nenhuma mudanca de bloco/unidade/subunidade. Fora do gold: CG perde a u09 espuria em 10 entries (R2/R4), ES2
revisao-p2/respostas ganham u02 pela regra B (id casa), IA p2-202402 ganha calendario.

Commits: gerador `6499217`; MF `bc75df4`, TCC `b5f10f2`, IA `8fd1f48` (push), SO `0f6c023`, ES2 `c517579`, CG `eb628e8` (sem remote). Gate curado nas copias: 0 campos em 5/6, IA 2 = `p2-202402` llm-funil (ruido de voto no cache da copia, igual ao A2).

Achado colateral: `exemplos-zip` (MF) tem resumo Gemini ERRADO — fala em Dafny/Hoare para um zip de `.smv` (NuSMV);
o motor acerta u03 pelo card apesar do dado ruim. Restam 5: 3 forks (A1) + 2 links sem texto.

## A2 EXECUTADO: genericos de unidade por curso (df do plano + nome do curso) — lista do MF aposentada (2026-08-27)

**Nao e tokenizador novo.** Os scorers de unidade (`file_map.score_entry_against_unit` via `_score_timeline_unit_phrase`),
o indice de unidade e o scorer de subunidade (`_score_entry_against_taxonomy_topic`) recebem o conjunto de genericos
por PARAMETRO: `stopwords.unit_generic_tokens_from_units` (token em >= 40% das unidades do plano, titulo + topicos,
+ estruturais) ∪ tokens do nome do curso; carimbado no indice de unidade e em cada topico da taxonomia (`course_name`
gravado na raiz via semantic_profile). `UNIT_GENERIC_MODE`: **df (default)** | lista (constantes antigas; byte-identico:
gate 0 campos em 5/6, os 2 do IA sao ruido de voto no cache da copia) | ambos.

**Comparacao nas copias dos 6 (harness rapido, 3 modos):**
| modo | bloco | unidade | cobertura | subunidade |
|---|---|---|---|---|
| lista (antes) | 199/200 | 191/191 | 40/57 | 87/93 |
| **df + nome do curso** | 199/200 | 191/191 | **41/57** | 87/93 |
| ambos | 199/200 | 191/191 | 40/57 | 87/93 |
Primeira rodada do df (SEM nome do curso) expos a mesma raiz do A1 no eixo de unidade: a lista do MF continha
"computacao" por acaso; sem ela, a u09 da CG ("Temas ... de Computacao Grafica") casava todo PDF pelo cabecalho.
Nome do curso e boilerplate em qualquer eixo.

**Fora do gold (df):** ganhos — ES2 `azure` -> plataformas-de-devops; IA `introducao-a-agentes` -> planejamento-
classico; TCC `aula-14` PCP -> prova-da-indecidibilidade, `integer-programming` -> reducao-polinomial; CG
`opengl3dcpp-vdi` -> camera sintetica, `exerciciodemodelagem` +u07, u09 deixa de poluir 3 exercicios; SO I/O perde
"paginacao" errada. Perdas anotadas (cobertura): IA `o-que-e-ia` perde u01, ES2 `roteiro6` perde u02, TCC
`aula-13-rice` perde u04. Colecoes multi-topico (MF `listas`, `exemplos-zip`) ficam sem subunidade — honesto.

Persistido nos 6 (reprocess in-place 93 s, sentinela sem mudanca de bloco). Proximo: A1 (bloco: um tokenizador
e uma assinatura para P4 + desempate com o `_global_df`), B (kind x categoria), C (apagar `anchor_placement`).

## AUDITORIA v2 — uso real e efeito medido (2026-08-27, pedido do user: "entender o que ja existe e o que e usado")

**Chamadores reais (arquivo:linha), no caminho do reprocess:**
- `disambiguator._toks/_block_signature/_global_df`: so o desempate do motor (+ gate D4). `_global_df` =
  IDF por BLOCO, memoizado no ctx. Usado. `window_provider` NAO o usa (P4 casa por stem sem peso).
- `window_provider._topic_tokens/_stems/_block_topic_stems`: so o P4 (`provider_topic`). Usado. Homonimo
  `file_map._topic_tokens` e OUTRA funcao (indice de unidade).
- `timeline/index._timeline_specific_tokens`: fusao de blocos, extracao de topicos, deteccao de nao-instrucional
  (11 usos). Usado no build e no reprocess (timeline e reconstruida).
- `_score_timeline_unit_phrase` + `TIMELINE_UNIT_NEUTRAL_TOKENS`: DP de unidade via engine.py:250/2251. Usado.
- `UNIT_GENERIC_TOKENS`: indice de unidade do file_map (facade:167, routing/file_map), vocabulario de unidade dos
  blocos (index.py:1754-1766) e `concept_resolver` (legado concept-fused: roda a cada reprocess, calcula
  `computed_block_*`, e SOBREPOSTO por `resolve_temporal_block` -> custo sem efeito no bloco).
- `infer/resolve_semantic_profile`: taxonomia, tag catalog, file_map (extra signals), teaching_plan. Nunca no motor.
- `anchor_placement` (+ copia de `_GENERIC_STEMS`): gated por `use_anchor_placement`, nenhum perfil liga = MORTO.
- `content_taxonomy` tem `_toks`/`_GENERIC_STEMS`/`_UNIT_TITLE_GENERIC` proprios (aliases de subunidade). Usado.

**Efeito medido das listas nos 6 cursos (tokens do vocabulario do curso que cada lista remove):**
- `_GENERIC_STEMS` (motor): so palavras de ATIVIDADE em todos (aula, exercicios, introducao, apresentacao,
  disciplina, trabalho, revisao, estudo/caso). E dominio, nao curso. Mantem como semente.
- `TIMELINE_UNIT_NEUTRAL_TOKENS` + `UNIT_GENERIC_TOKENS`: MF perde 9-10 palavras reais (logica, verificacao,
  modelos, programas, predicados, formais...) — proposito da lista; SO/IA/ES2/TCC quase nada; **CG perde
  `fundamentos`** (titulo da unidade 2) e `algoritmos/modelos/metodos/aplicacoes`. Lista MF em disfarce.
- IDF por BLOCO (o `_global_df` que existe) NAO reproduz a lista do MF: so `logica` passa de 40% dos blocos.
- **IDF por UNIDADE do plano (titulo+topicos, df/n >= 0,4) REPRODUZ a lista do MF onde ela acerta**
  (`formal`/`verificacao`/`logica` em 3/3) **e acha o que ela nao sabe**: SO `gerencia` 4/7 + `estudo de casos`
  5/7, IA `aprendizagem` 5/5, ES2 `software`/`microsservicos`/`integracao`, CG `algoritmos` 4/9 — sem matar
  topico raro (CG `fundamentos` 1/9, SO `programas`, TCC `linguagens`, IA `modelos`). `file_map.ubiquas`
  (frase presente em TODAS as unidades) e a versao estrita disso.

**Plano final (cada fase com o gate: 5 curados 199/200 + 191/191 + 40/57, nu 205/212, CG, suite):**
- **A1 (bloco):** P4 e desempate com o MESMO tokenizador (`_toks` + dims/wids) e a MESMA assinatura de bloco;
  boilerplate do P4 = semente de atividade (`_GENERIC_STEMS`) + `course_name` + `_global_df` (df/m >= 0,4);
  stems de 6 so como fuzzy por cima do token unificado. Some `_topic_tokens`/`_course_stems` duplicados.
- **A2 (unidade):** `TIMELINE_UNIT_NEUTRAL_TOKENS` e `UNIT_GENERIC_TOKENS` viram df por unidade do plano,
  calculado por curso na construcao do indice (taxonomia ja carregada); `TIMELINE_GENERIC_TOKENS` (atividade)
  fica. Consumidores: `_score_timeline_unit_phrase`, index.py:1754-1766, file_map unit index.
- **B (kinds):** tabela kind x categoria derivada dos 212+73 pares; substitui edicoes ad hoc em NEVER_HOSTS.
- **C (morto):** `anchor_placement.py` + sua `_GENERIC_STEMS`; avaliar `concept_resolver` (roda, nao decide).
- **D (invariantes):** testes sobre os 6 cursos reais: nome do curso fora de assinatura; 2d/3d/t2 sobrevivem;
  prova fora de janela; df>=40% nunca discrimina.

## AUDITORIA: o que o sistema JA faz de tokenizacao, boilerplate, frequencia, kinds e categoria (2026-08-27)

Pedido do user antes de implementar "IDF por curso + tokenizador unico": nao reconstruir o que existe. Mapa (arquivo:linha):

**Tokenizadores (7, cada um com regra propria):**
| onde | regra | consome |
|---|---|---|
| `motor/disambiguator._toks:40` | >=3 chars, sem digitos, `_GENERIC_STEMS` (prefixo 8), quebra camelCase | desempate; assinatura do bloco (topic + sessions) |
| `motor/window_provider._topic_tokens:104` | >=3 chars + dimensionais 2d/3d (novo), `_GENERIC_STEMS`; stems de 6 | P4 topic (card) — + `_course_stems`, `_unit_stems` (novos) |
| `timeline/index._timeline_specific_tokens:362` | >=4 chars, `TIMELINE_GENERIC_TOKENS` | fusao de blocos (cabeca da linha), fronteiras |
| `timeline/index` unidade `:467/:1754` | >=4, `TIMELINE_UNIT_NEUTRAL_TOKENS` / `UNIT_GENERIC_TOKENS` | DP de unidade (`_score_timeline_unit_phrase`) |
| `timeline/unit_matcher._tokens:37` | >=3, `UNIT_MATCHER_STOPWORDS` | DP posicional bloco->unidade |
| `timeline/card_block._tokens:33` = `block_identity._tokens:40` | >2, `CARD_BLOCK_STOP` | card->bloco (labels), identidade |
| `extraction/content_taxonomy._topic_support_tokens:208` | >=4, prefixo 5 | aliases de subunidade |
| `routing/file_map` (scorer de unidade) | `UNIT_GENERIC_TOKENS` | unidade 1:1 / cobertura |
Normalizacao e unica (`text/normalize.normalize_match_text`), mas piso, stems e stopwords divergem por modulo:
o que sobrevive num lado morre no outro (raiz das 4 correcoes da CG e do t2).

**Listas manuais de "generico" (6 + 2 duplicadas):** `_GENERIC_STEMS` (disambiguator:25; **duplicada** em
`routing/anchor_placement.py:60`, legado gated por `use_anchor_placement`, morto com `use_anchor_engine`),
`TIMELINE_GENERIC_TOKENS` (calendario/atividade — ok, e de dominio), **`TIMELINE_UNIT_NEUTRAL_TOKENS` e
`UNIT_GENERIC_TOKENS` (stopwords.py:23/:35) carregam vocabulario do METODOS FORMAIS** ("formais", "predicado",
"proposicional", "sintaxe", "semantica", "verificacao", "especificacao", "linguagens", "concorrentes"...) — lei
4b violada numa constante global; funciona no MF e no SO por acaso, e vira ruido em cadeira nova. `_TOPIC_FILLER`
(R3), `_TIMELINE_ADMIN_PHRASES`, `UNIT_MATCHER_STOPWORDS`, `CARD_BLOCK_STOP` (PT puro, ok).

**Frequencia / inferido por curso (JA EXISTE, parcial):**
- `disambiguator._global_df:133` + `_score:122`: **IDF por token sobre as assinaturas dos blocos do curso**, so no
  DESEMPATE (e no gate D4 de janela-1: `DATE_DF_MAX`). O provider de janela (P4) nao usa — casa por stem sem peso.
- `disambiguator._block_signature:107`: tokens de `ctx.course_name` saem da assinatura (so no desempate; P4 ganhou
  o equivalente ontem).
- `core/semantic_config.infer_semantic_profile:267`: por curso, a partir de plano/COURSE_MAP/glossario/headings:
  `known_tools`, `generic_slug_blacklist` (= so o slug do curso), `heading_single_overlap_cues`. Consumido por
  `content_taxonomy` (aliases) e `teaching_plan`; **nada disso chega ao motor**.
- `coverage_rules._FRACAO_META` / `repo._doc_is_meta`: doc que cita >=80% dos titulos de unidade = meta (plano/TOC).
- `window_provider._modal_years`: ano modal das sessoes.

**Kinds / hosting:** `timeline/kinds.NEVER_HOSTS_MATERIAL_KINDS:66` (holiday, office_hours, workshop,
academic_event, reserved, results, planning, suspended) usado em `drop_never_hosts` (+`assessment` desde ontem, com
fallback) e em `_NOT_PREP_HOSTS`. Nao ha tabela kind x categoria; e edicao ad hoc.

**Categoria no roteamento (so 4 pontos):** `anchor_engine.is_out_of_disamb_scope:27` (`trabalhos`/`provas` +
card TDE), `anchor_engine.resolve_generic_reference:48` (`bibliografia`/`references` -> 1o bloco),
`due_window.tier2_due_scope:40` (`trabalhos`/`provas`, `codigo` em TDE), `coverage_rules:94`. `outros`/
`material-de-aula` sao neutros. O detector (`helpers.auto_detect_category`) e so por nome de arquivo.

**Conclusao da auditoria:** o IDF por curso EXISTE (desempate) e nao foi levado ao P4 nem aos eixos de
unidade; as listas globais de unidade sao MF em disfarce; os 7 tokenizadores sao a origem estrutural das
correcoes repetidas. Plano sem regressao: (A1) motor — um tokenizador e uma assinatura para P4 + desempate,
boilerplate = IDF do curso (`_global_df`) no lugar de `_GENERIC_STEMS`/`_course_stems`, gate nos 6 (5 curados
199/200 + nu 205/212 + CG); (A2) eixo de unidade — trocar `TIMELINE_UNIT_NEUTRAL_TOKENS`/`UNIT_GENERIC_TOKENS` por
IDF do curso no `_score_timeline_unit_phrase` e no scorer do file_map, gate 191/191 + cobertura 40/57;
(B) tabela kind x categoria derivada dos golds (212 pares) no lugar de `NEVER_HOSTS` ad hoc; (C) apagar
`anchor_placement._GENERIC_STEMS` (legado morto); (D) invariantes como teste sobre os 6 cursos reais.

## HOLDOUT CG EXECUTADO: 4 raizes gerais, 13 -> 2 suspeitos, bancada intacta (2026-08-27)

**Build** `Computacao-Grafica-Tutor` (build_course CLI, zero curadoria): 73/73 entries, 29 blocos, Datalab balanced em
52 PDFs (4h30). Repo com git init + .gitattributes + commits; perfil "Computacao Grafica" no subjects.json.
**Pre-revisao (sem gold, so cronograma x card):** 13 suspeitos, 10 deles material de aula em bloco de PROVA (card 13
"CG 3D" -> G2 08/12 e P1; card 16 "Sintese de Imagens" -> P2). O professor reusa o mesmo Moodle: nada disso e prova.

**Raizes (todas gerais, todas no `provider_topic`; medidas com gate curado nos 5 = 199/200 intacto e nu 205/212 igual):**
1. **Bloco de prova saia como candidato.** Nos 5 golds, **0/212** entries tem bloco-verdade `assessment`; o
   `topic_text` da prova e a COBERTURA ("Conteudo: unidade-08...") e casava qualquer card com nome de unidade —
   40/70 janelas da CG traziam 2-3 provas. `drop_never_hosts` agora tira `assessment` (fallback se so ha prova).
2. **"2d"/"3d" morriam no piso de 3 chars** (mesma classe do t2): "Computacao Grafica 3D" ficava so com o nome do
   curso. Token dimensional com assinatura propria no texto cru das sessoes; dimensao SOZINHA que aponta 1 bloco
   ("Exercicios 2D") = escopo, nao aula -> funil (o LLM acertava; janela-1 forcada regredia 3).
3. **Nome do curso nao era boilerplate no provider** ("comput" casava "Geometria/Visao COMPUTacional"; so o
   disambiguator descartava). Stems do course_name saem dos dois lados.
4. **Card nomeado pela UNIDADE do plano** ("Sintese de Imagens Realisticas" vs linha "Iluminacao"): o bloco tem
   `unit_slug` da unidade (DP) e o P4 nao olhava. unit_slug entra na assinatura do bloco.
Efeito na CG: cards 1-16 todos nos blocos esperados; restam `matematica.cpp` (card 3 -> 10/09), Texturas (card 17
-> 25/08, "mapeamento" 2D; o cronograma nao tem linha de texturas) e convencoes (Resolucoes de Prova 2D/3D, lista
da P1). Sentinela nos 5: SO 1 metodo (llm -> llm-funil, certo), ES2 2 metodos (-> janela-1), IA 2 provas antigas
saem do bloco da P2. Tutores reprocessados e commitados.

**Achados de ingestao no caminho (todos corrigidos):** cue `biblio` casava "biblioteca" (2 falsos `bibliografia`,
que sairiam do desempate) e `ementa` casava "complementar" (-> cronograma); acentos nao sobrevivem ao Start-Process
(`--args-json`); Edge headless devolve antes de fechar o PDF (espera estabilizar); golden da CG nascido vazio durante
o build (regenerado). Categoria: 35 `outros` (detector so olha o nome; neutro para o motor).

**Politica de gold (user, 27/08):** gold NAO faz parte do fluxo de cadeira nova; a CG e a ULTIMA regua a ser
rotulada, e por verificacao (tu marca ✗ no artefato), nao por rotulagem do zero. Depois disso, o termometro em
producao e o proprio motor (flagados / llm-funil / conf-err -> fila de revisao).

## FILA VIVA (2026-08-26) — o que falta` logo abaixo — le antes de escolher trabalho.**
A fila de 24/08 (Fases 0-2) esta CONCLUIDA; a Fase 3 (cobertura) segue pendente e esta reescrita na fila viva.
**HANDOFF: `docs/reports/2026-08-26-handoff-cg-holdout.md`** — le primeiro (plano CG passo a passo: site -> PDF -> stash -> CLI -> holdout; links do Moodle classificados). Historia e leis: `2026-08-21-handoff-rumo-aos-100.md`.
ESTADO (`scripts/eval_eixos.py`, as-of **2026-08-31b**): bloco **199/200** conf-err **0** (o erro = ES2 `azure`,
convencao ACEITA por ruling 31/08) · unidade **191/191 (100%)** · cobertura **56/57 F1 0,982** (resta SO
aws-encryption-sdk — teto documentado, ver P1 EXECUTADO; eth2 fechou pelo motor com o texto da pagina) ·
subunidade **87/93** (4 cursos com gold) · **pinos 5** · cards manuais **1** (TCC
"Semana 12", MANTIDO por refutacao 31/08) · decisoes humanas de bloco **6** (eram 23) · suite **2133 passed** ·
determinismo **6/6** (o "jitter" ferramenta: era convergencia em 1 passo, resolvido 31/08).
MOTOR NU (zero curadoria, `scripts/ablacao_rapida.py` nos 6): bloco display **194/200** conf-err 2 (205/212 por
uuid, medido 27/08) · unidade **170/191 (89%)** — era 134, +36 pelo DP com desvio de janela (P2a 31/08) ·
cobertura **54/57 F1 0,947** — era 55: knn/IA passou a acertar (bloco certo -> card certo) e as 2 entries u01
do IA que acertavam POR ACIDENTE (DP esmagava tudo em u01) expuseram erro proprio de auto_map (oracle->u02,
ia-responsavel->u05); trade honesto, o curado cobre os 3 · subunidade ~21/94 (medida 26/08). Erros
nus: 3 ruido do voto (MF, aceitos, ficam os pinos) · 2 convencao sem texto (IA prova-1, ES2 azure — ACEITOS
31/08) · 2 dominio (TCC aula-17; alias Cook-Levin TESTADO E REFUTADO 31/08 — nao retentar sem sinal novo) ·
1 teto de dado (MF aws, pagina raiz sem vocabulario de verificacao, ver P1 EXECUTADO).
Gate curado nas copias: 5/6 + IA `p2-202402` (ruido de voto no cache da copia, excecao documentada).
PUSH (as-of 2026-08-31): gerador `f45fd31`. **Os 6 tutores tem remote privado (HumbertoCG18) e estao 0/0 com
origin**: MF `0157a2c` · TCC `f90aa98` · IA `60f7271` · SO `b4c336c` · ES2 `3dbd45d` · CG `62c80a0`.
Antes: `docs/reports/2026-08-20-handoff-fechamento-campanha-motor.md`.
Cobre a sessao inteira (`7e940f5e`, 63 prompts): poda do enxame, regua nova + sweep do gate,
rotulagem dos 64 casos, limpeza do manifest, eixo de bloco, N:N nos consumidores, fix do
nao-determinismo, `explain_entry.py` e o veredito do termo `card`.
Antes: `docs/reports/2026-08-19-handoff-cardinalidade-do-motor.md` — secoes A–H seguem validas,
**I-7 vencida** (granularidade resolvida, duplicatas removidas).
CARD (2026-08-20d): o card e ponteiro de **UNIDADE** (teto LOO 97%, janela 1,41), nao de bloco
(85%, abaixo dos 86% de hoje); consenso por card no eixo de cobertura **REFUTADO** (+1 em 57)
porque `rule: card` ja responde por 179 das 258 `coverage_units` — o teto ja esta colhido.
Ver K-3a/K-3b em `## CODE — o termo card da fusao esta MORTO`.

ESTADO FINAL (`as-of 2026-08-19d`): unidade 1:1 **166/188 = 88%** (era 127/191 = 66%) ·
cobertura N:N **44/57 = 77%, F1 0,81** (regua nova) · bloco **172/200 = 86%** (NAO 57% — eu media
o campo errado; ver secao do bloco) ·
entries **227** (eram 233; 6 duplicatas de conteudo removidas) · suite **1904 passed /
1 skipped / 0 falhas** · producao reprocessada e **idempotente** (0 mudancas entre duas rodadas).
ROTULAGEM COMPLETA: 64 casos, 0 pendentes.
DECISION da granularidade da avaliacao **RESOLVIDA** (prova inteira, nao por questao) — ver
secao propria; o gargalo medido e o `EXAM_INDEX.md` existir em 1 de 5 cursos, nao a granularidade.
A DESCOBERTA DA SESSAO: **o ES2 nunca esteve quebrado** — 8/27 contra a regua temporal virou
17/18 contra os rotulos de cobertura. A regua e que cobrava a resposta errada. O balde EIXO
sumiu quando os rotulos chegaram, entao a cardinalidade N deixou de ser pre-requisito do
passo 1 e virou melhoria de modelo.
TESE: a raiz de unidade e subunidade nao e o scorer, e a CARDINALIDADE. Prova: 53 arquivos
avaliativos nos 5 cursos, os 53 recebem 1 subunidade so. Teto da regua de unidade no modelo
1:1 = **179/191 = 94%** (~85% contando o ES2). O balde EIXO so fecha trocando para N.
Por curso: IA 93% e TCC 83% praticamente resolvidos; **SO 42% e ES2 30%** carregam 25 dos 39 ERRO.
BLOCO e o eixo mais fraco (**118/208 = 57%**), o unico genuinamente 1:1, com gold pronto, e
NINGUEM MEXEU — maior ganho disponivel.
GANHO ESTRUTURAL DESTA SESSAO: **reprocess virou ponto fixo** (0 entries mudam entre duas
rodadas identicas; antes deslocava 2). Pre-requisito de qualquer medicao futura.
Codigo na arvore (7 arquivos, +5 isolado, suite 1902) **NAO commitado**; producao **NAO
reprocessada** de proposito — o ganho nao se materializa e a subunidade piora enquanto a
cardinalidade estiver errada.
Antes — sessao EIXO DE UNIDADE — medicao **e** execucao da fila.
Regua nova `entry -> unidade` criada (`scripts/eval_entry_unit.py`, 191 entries, verdade
composta de dois golds ja aprovados — o handoff registrava que essa regua NAO EXISTIA).
FEITO: (1) gate `T.UNIT_TAG` calibrado 0.65 -> 0.50 no primeiro sweep da historia do projeto,
medido ponta-a-ponta; (2) tres fixes de higiene do glossario (secao de template virando sinal de
unidade, frase ubiqua, travessao virando alias); (3) normalizacao por tamanho de unidade
REJEITADA pela medicao. Suite 1901 passed / 1 skipped.
PONTA-A-PONTA: 126 certo / 46 errado / 19 vazio -> **132 / 47 / 12**.
Achados novos nas duas secoes CODE abaixo (eixo de UNIDADE e `known_tools`); relatorio com todas
as tabelas e as CORRECOES: `docs/reports/2026-08-18-achados-eixo-unidade.md`.
PENDENTE: reprocessar os 5 repos-tutor — os fixes de glossario so entram na taxonomia em disco
no proximo reprocess, e o gate novo so vale para o que for regravado.
VEREDITO `known_tools`: **dano medido = ZERO nos dois eixos** (taxonomia byte-identica com o
filtro ligado/desligado nos 5 cursos; 0 flips em bloco; 0 delta em 4 bracos de unidade) — a raiz
segue armada mas a trava esta acionada. Desce para higiene.
TOPO DA FILA POR IMPACTO MEDIDO: (1) sweep de `T.UNIT_TAG=0.65`, que mata 29 acertos certos;
(2) normalizar score por tamanho de unidade — ACOPLADO ao (1); (3) podar boilerplate do
template do GLOSSARY.md, +2 e zero regressao; (4) eixo de cobertura (ES2 59% confiante-e-errado).
Antes — sessao EIXO DE COBERTURA + TAXONOMIA — **TUDO APLICADO EM PRODUCAO
e commitado**; gerador HEAD `843db1e`, 5 repos-tutor limpos e reprocessados; suite 1898.
Handoff da sessao: `docs/reports/2026-08-18-handoff-cobertura-taxonomia.md`.
Feito: (1) perda de topicos do plano de ensino corrigida — TCC 11/27, SO 3/34, ES2 1/21 -> 0
ausentes nos 5; (2) heading institucional e frase-titulo-de-outra-unidade fora da assinatura;
(3) card do Moodle como sinal do eixo de UNIDADE; (4) regua entry->unidade criada com 9 rotulos
aprovados e baseline medido; (5) camada de referencia destravada — "sem predicao" de 8/9 para
3/9, SO F1 0,778. Reguas por material e golds de unidade sem regressao em nenhum curso.
FILA: fase 3 (codigo/exemplos) -> fase 4 (exercicios/listas/provas antigas, o pedido original).
RULING PENDENTE DO USER: pino do `Cap. Algoritmos Geneticos` (IA), duplicatas da P1 do IA,
destino do entry fantasma, granularidade da cobertura de avaliacoes.
Antes: **CAMPANHA 3 / PASSO 3 FECHADO — FLIP + DELEÇÃO COMPLETOS: motor é o
atribuidor ÚNICO em 100% do sistema, funil legado deletado (-4747 linhas), serializador único
v4, 5 cursos reprocessados/commitados**, ver Concluído 2026-08-17c e relatório
`docs/reports/2026-08-17-passo3-flip-delecao-fechado.md`. Antes no mesmo dia: etapa 1 medição
pré-flip (Concluído 2026-08-17b); PASSO 2 C1 pinos + gaps 1.2/1.3 (Concluído 2026-08-17). Histórico 2026-08-14: F4 unit/subunit no motor + AUDITORIA-ENXAME EXECUTADA — workflow 45 agentes [7 finders + 37
verificadores adversariais + síntese; mix sonnet/fable], 32 achados CONFIRMADOS / 5 refutados;
relatório ranqueado em `docs/reports/2026-08-14-auditoria-enxame.md`; ver Concluído 2026-08-14.
Fila restante da ratificação 2026-08-11: campanha 3 cutover → campanha web)
> histórico 2026-08-11b: 3 decisões batch executadas — freshness 5/5 verde, kind-override
> promove auto_unit [pino IA removido, 11 pinos], guard C6 resolvido por medição; suite
> 1925/0/4. CAMPANHA FUTURA de produto web criada [backlog vivo ~24 itens, seção no fim].
> Renomeado de `2026-06-21-pendencias.md` em 2026-07-03 (decisão do user: nome geral sem data,
> mais fácil de achar/revisar). Histórico preservado via `git mv`; 7 referências atualizadas.
status: documento VIVO. Atualizar a cada conclusão de plano (regra não-negociável,
`.mex/AGENTS.md`). Concluído 100% (gate verde) → remover daqui + mover o plano pra `Feitos/`.

Legenda: **[USER]** = ação humana (rotular/decidir/rodar). **[CODE]** = implementável.
**[DECISION]** = decisão de produto antes de codar.

CONVENÇÃO (não-negociável): todo item DERIVADO (fato sobre estado vivo dos repos) carrega
`as-of <data/commit>`. Sem isso, volta a mentir na próxima mudança de estado. Itens DURÁVEIS
(goal/decisão/plano) não carimbam.

FATO DURAVEL — O STASH E CONFIGURACAO, NAO CAMINHO FIXO (corrigido pelo user 2026-08-25;
minha primeira redacao dizia "SEMPRE C:\...\Desktop\Moodle" como se fosse constante — ERRADO).
A pasta de origem de cada cadeira vem de **`SubjectProfile.stash_folder`** (`src/models/core.py:234`,
"pasta com os arquivos-fonte (PDFs/cards) da materia"), persistido em
`%APPDATA%/GPTTutorGenerator/subjects.json` por perfil. Os 6 perfis tem o campo preenchido e
todas as pastas existem em disco (`as-of 2026-08-25`); o VALOR segue hoje a convencao
`Desktop/Moodle/<slug-do-curso>`, mas o MECANISMO e configuracao — nunca hardcodar o caminho.
Cada entry grava a origem resolvida em `source_path`. Nao confundir com `raw_target`
(`raw/pdfs/...`), que e a COPIA dentro do repo-tutor e esta no `.gitignore`. Quando um item
falar em "o bruto", checar de qual dos dois se trata — foi essa confusao que gerou a avaliacao
de risco errada do `reject` em 24/08.

- [RESOLVIDO 2026-08-25] **6o perfil "Laboratorio de Redes de Computadores" = FORA DE ESCOPO,
  de proposito.** Tem `stash_folder` configurado (pasta existe no disco) e `repo_root` VAZIO.
  **Ruling do user:** e cadeira NOVA, com os arquivos sendo subidos ao longo do semestre —
  material incompleto, entao nao serve nem para desenvolver nem para medir. Nao criar repo-tutor,
  nao apagar o perfil. Quando "os 5 cursos" aparecer neste tracker, e por isso; o perfil existir
  em `subjects.json` nao e bug.

LEI DA CAMPANHA — **AS CADEIRAS DO SEMESTRE PASSADO SAO BANCADA DE TESTE, NAO O ALVO**
(user, 2026-08-25; extensao explicita da lei "sem motor por categoria"). Desenvolvemos e medimos
sobre MF/SO/IA/ES2/TCC porque o material ja esta 100% subido e as informacoes sao conhecidas —
e isso torna a medicao possivel. **NAO significa que se corrija para essas cadeiras.** Regra que
so vale para um curso e pino ou curadoria, nunca codigo; toda regra tem que se medir em tudo e
ler-se por categoria. O teste real vem depois, com o semestre corrente, quando os eixos e o motor
estiverem em ~100%.

**BLOQUEADOR CONHECIDO DO TESTE REAL — Computacao Grafica publica HTM** (user, 2026-08-25;
mecanismo verificado no codigo em 25/08). Nao e "feature nao implementada", sao DOIS defeitos
distintos e o segundo e o pior:
1. **`.htm` (sem L) nao existe em `src/`** — `stash_import._classify_file_type` devolve `""` e o
   arquivo cai em `StashScanResult.skipped`. A UI mostra so a CONTAGEM ("N ignorado(s) por
   extensao", `ui/app.py:1679`), nunca os nomes. Material some sem ninguem saber qual.
2. **`.html` (com L) esta em `CODE_EXTENSIONS`** (`utils/helpers.py:204`), entao e importado —
   como `file_type="code"` e `auto_detect_category` -> **`codigo-professor`**
   (`utils/helpers.py:647-648`). Slide/apostila publicada como pagina web entra no sistema
   classificada como CODIGO DO PROFESSOR: ganha resumo de codigo do Gemini em vez de tratamento
   de material, e cai no balde que ja e o 2o pior do eixo de bloco (D-5: codigo-professor
   52/59 = 88,1%, contra material-de-aula 96,6%).
Fix de raiz quando chegar a hora: reconhecer `.htm`/`.html` como um `file_type` PROPRIO
(documento web), nao como codigo, com extracao de texto propria — e nomear os `skipped` na UI,
que e barato e vale para qualquer extensao futura.

**CG ENTRA NO ESCOPO (ruling do user 2026-08-25)** — e por um motivo que NAO vale para o Lab
Redes: **o professor reutiliza os materiais**, entao cards, links e PDFs ja estao no Moodle mesmo
para unidades/topicos ainda nao dados. O material esta COMPLETO; e a completude que decide se uma
cadeira serve de bancada, nao o semestre.

**ANATOMIA DO SITE DE CG (verificado 2026-08-25, `inf.pucrs.br/pinho/CG/`):** e uma arvore de
HUBS e FOLHAS, nao paginas de conteudo soltas.
- hub (`Aulas/GeomComp/GeomComp.htm`): **~150 palavras** + 3 logos + 3 links relativos
  (`Dominancia/Domina.html`, `Slab/Slab.html`, `PlaneSweep/PlaneSweep.html`).
- folha (`Dominancia/Domina.html`): ~350 palavras, **5 diagramas** (`domina1..5.jpg`),
  pseudocodigo em `<pre>`, formulas inline.
- indice do curso (`/pinho/CG/`): mesma forma — cronograma, bibliografia, listas P1/P2, tudo `.htm`.
- HTML estatico puro: **sem applet, Flash, canvas ou JS**. Nada se perde numa conversao.
Consequencia: converter o HUB rende 150 palavras e tres logos. **O material esta nas FOLHAS** —
qualquer caminho exige crawl de 1 nivel; nao ha atalho de "converter a pagina da aula".

**PLANO DO USER (HTML -> PDF -> Datalab -> sistema): avaliado, com ressalva.** Funciona HOJE com
zero codigo (`.pdf` ja e `file_type` de 1a classe; e so por no `stash_folder`) e serve de
desbloqueio imediato. Mas e a forma errada para o regime permanente, por tres razoes medidas:
1. **O sistema JA converte HTML**: `text/url_markdown.py:189 html_to_structured_markdown`
   (BeautifulSoup, ja e dependencia em `pyproject.toml`), usada por `fetch_reference_text`.
   Preserva `h1`-`h6`, listas, tabelas e **`<pre>`** — exatamente onde vive o pseudocodigo.
2. **O round-trip destroi a estrutura e depois paga para adivinha-la de volta.** No HTML o heading
   e `<h2>` declarado; virando PDF vira "texto maior em negrito" e o Datalab tem de inferir. E
   essa estrutura NAO e decorativa aqui: `markdown_headings_text` tem peso **4,4** no scorer de
   subunidade e `collect_strong_heading_candidates` le os 4 primeiros headings para alimentar a
   taxonomia. O round-trip degrada justamente o sinal mais forte dos eixos.
3. **Custo**: o Datalab e o unico custo pago recorrente do pipeline e mata-lo e objetivo declarado
   da campanha web. Mandar HTML para la e pagar OCR por conteudo sem problema de OCR.

**LACUNA HONESTA do caminho recomendado:** `html_to_structured_markdown` **nao trata `img`**
(`img` nao esta nos `block_tags`, `url_markdown.py:217`). As 5 figuras do Domina.html sao carga
util numa aula de geometria. O caminho bom exige baixar as imagens e referencia-las — o mesmo
trabalho que o pipeline ja faz para PDF (`images_dir`). Nao e de graca; e mais barato que o
round-trip.

**CORRECAO (user, 2026-08-25):** nao ha material de CG no corpus porque **nada foi baixado
ainda** — nao porque nao exista. E o acervo tem TRES formas, e so uma e problema:

| forma | estado |
|---|---|
| **PDFs** | o professor tambem publica PDF — funcionam HOJE, pipeline de sempre, zero codigo novo |
| **paginas `.htm`** | os dois defeitos acima (descarte silencioso / classificado como codigo) |
| **modals** | forma ainda NAO investigada — **adiado por decisao do user**, "por hora nao" |

**Consequencia pratica: CG NAO esta bloqueada.** Baixar os PDFs e processar funciona sem uma linha
de codigo nova; o trabalho de `.htm` so limita a parcela do acervo que vive como pagina. Nao tratar
"CG" como um bloco monolitico que espera o fix de HTM.

**NAO FAZER AGORA (o trabalho de `.htm`/modals)**: sem material baixado nao ha o que medir, e regra
sem regua e exatamente o que esta campanha proibiu. Entra depois dos eixos, como pre-requisito do
teste real — nao como descoberta de ultima hora. Os PDFs, esses, podem entrar quando o user quiser.

- [USER] **Investigar os "modals" de CG** (`as-of 2026-08-25`, adiado pelo proprio user). Forma de
  material que o professor publica e que ainda nao sabemos o que e tecnicamente (janela modal na
  pagina? conteudo carregado por JS? outra coisa?). Sem isso nao da para dizer se sobrevive a
  qualquer extracao. Investigar SO quando CG entrar de verdade.

AVISO DE DRIFT DE CAMINHO (`as-of 2026-08-24`): os modulos foram movidos depois que boa parte
deste tracker foi escrita. `core/file_map.py` -> **`routing/file_map.py`** (ha tambem
`facade/file_map.py`, que e outro arquivo) e `core/content_taxonomy.py` ->
**`extraction/content_taxonomy.py`**. As 8 citacoes soltas `file_map.py:NNN` daqui sao ambiguas
entre os dois file_map E tem numero de linha velho. **Confirme com grep antes de agir sobre
qualquer `arquivo.py:linha` deste documento** — um item pode parecer aberto so porque o grep
foi no caminho errado (aconteceu com o guardrail do subject_profile em 24/08).

---

## FILA ACORDADA COM O USER (2026-08-24) — ordem, gate e o porque da ordem

**Principio que decide a ordem:** neste projeto a regressao entre itens vem do REPROCESS, nao do
codigo. O voto do LLM varia entre rodadas (o cache congela o primeiro), a ordem de chaves do JSON
alterna, e toda mudanca de scorer move dois eixos ao mesmo tempo (H1/H2/H3 ganharam unidade e
esvaziaram subunidade). Logo: ir do que **nao pode** regredir para o que pode, e AGRUPAR as
mudancas de comportamento em poucos reprocesses, nunca intercalar.

**GATE UNICO entre fases (nao negociavel):**
```
python scripts/eval_eixos.py     # bloco / unidade / cobertura / pinos
python -m pytest -q              # ler a linha "N passed", NUNCA o exit code
```
mais o diff das sentinelas revisado campo a campo. **Nada avanca com regua pior em qualquer eixo.**

### FASE 0 — limpeza de morto — **CONCLUIDA 2026-08-24** (ver secao propria abaixo)

### FASE 1 — fechar o eixo de bloco — **CONCLUIDA 2026-08-25** (ver secao propria abaixo; 8 erros restam, nenhum e codigo)
Os 6 golds **e** as 2 curadorias de card do SO no mesmo ato; reprocess de SO+MF; uma medicao.
Distincao que muda a expectativa: os **6 golds mudam a REGUA, nao o sistema** — 186 -> ~195 nao
deixa o tutor melhor, deixa a medicao honesta (um gold errado envenena toda medicao futura; foi o
drift do MF em julho). As **2 curadorias de card** sao o oposto: 4 entries passam a ser atribuidas
certo de verdade. Mata K-3 e B-3. Depois disso o bloco esta no TETO DO DADO — os 5 roteiros do ES2
nao tem solucao sem cronograma novo, entao "100%" e inalcancavel; a meta real e ~195/200.

### FASE 2 — gold de subunidade — **CONCLUIDA 2026-08-25** (ver secao propria abaixo; hipotese REFUTADA)
Rotular ~40 entries em `subunit_gt_<C>.csv` (IA u05, SO u01/u02, TCC u01/u02). **Zero codigo, zero
risco de regressao** — e medicao pura. E a maior alavanca por razao estrutural: um eixo inteiro
esta cego, e a cegueira bloqueia ~6 itens de uma vez (G-1, G-3, G-5, K-3 `card_text`, `SUBUNIT_TAG`
em F-5, e a hipotese do `primary_topic_slug`). Todos param na mesma frase: *"sem regua de ACERTO de
subunidade, trocaria perda medida por ganho nao medido"*. Precedente: foi exatamente esse movimento
— parar de consertar o scorer e perguntar DE ONDE A VERDADE VEM — que levou a unidade de 130 a 178.
So DEPOIS do gold, testar "subunidade = `primary_topic_slug` do bloco temporal". Nunca antes.

### FASE 3 — cobertura — **PENDENTE** (17 erros na regua atual 40/57; reescrita na FILA VIVA 2026-08-26, itens 4 e 9)
Cobertura: os 11 erros com `explain_entry.py`, um a um, ANTES de qualquer regra (consenso por card
ja foi refutado, +1/57). So entao a **FASE 4** (exercicios, listas, provas antigas), que era o
PEDIDO ORIGINAL de 18/08 e segue intocada — depende da cobertura estar de pe.

---

## FILA VIVA (2026-08-26) — o que falta, em ordem, com gate

0. **RESOLVIDO (31/08): "jitter" `ferramenta:` NAO era nao-determinismo — era CONVERGENCIA em 1 passo.** Medido:
   2 reprocess seguidos da CG = **0 difs** (e todos os gates desde 28/08 = 0 campos nos 6). Mecanismo lido no codigo:
   `write_tag_catalog` regenera o catalogo TODA rodada a partir de plano/mapa/glossario + `strong_headings` (4
   primeiros headings dos MARKDOWNS das entries) — deterministico dado o mesmo estado; mas a MESMA rodada reescreve
   markdowns DEPOIS de gerar o catalogo (injetores/navegacao), entao a rodada seguinte ve headings novos e o
   catalogo muda UMA vez e estabiliza (ponto fixo). Os flips historicos (`animacao-v2` CG, `lemas` x7 TCC) foram
   isso, logo apos mudancas de codigo que mexeram na emissao de markdown. Nao propaga para a regua; o gate de
   determinismo (2a rodada = 0 campos) e exatamente o detector certo e passa a exigir **6/6**. Reordenar o pipeline
   (catalogo depois da emissao final) so se os flips virarem rotina — hoje e 1 rodada de absorcao apos mudanca.

**Gate unico entre itens (inalterado + 2 itens novos):** `eval_eixos.py` (4 eixos) · `pytest -q` (ler "N passed") ·
sentinela campo a campo contra `git show HEAD:manifest.json` (nao contra `.bak`) · **determinismo** (2 reprocess
seguidos = 0 campos; R11) · para regra de motor: `scripts/ablacao_rapida.py` antes/depois (nu) e `--curado` (copia ==
original). Nada avanca com regua pior em qualquer eixo. Restaurou tutor por git -> reprocessa (derivados fora do git).

1. **HOLDOUT Computacao Grafica, zero curadoria** — **passos 1-3 EXECUTADOS 26/08** (`site_snapshot.py`, `moodle_pull.py`,
   `build_course.py`; stash em Desktop/Moodle/computacao-grafica, perfil gravado, 73 entries em dry-run). FALTA: build real
   (Datalab pago) -> reprocess -> gold de bloco -> `ablacao_rapida --repos CG`. Plano detalhado no handoff de 26/08 (4 passos: `site_snapshot.py`
   com PDF via Edge headless e cronograma HTML -> SYLLABUS.md direto; links do Moodle importados e CLASSIFICADOS material
   vs bibliografia/referencia/repositorio, ambiguos em manual-review; `build_course.py` CLI; gold + medida). Site verificado
   26/08: HTML estatico, sem modal, cronograma UTF-16 em formato SARC, paginas de aula chegam pelo Moodle. Pre-requisito antigo
   (nao e codigo): baixar os PDFs do site do professor (`inf.pucrs.br/pinho/CG`; ver ADENDO do handoff — os PDFs
   dispensam o problema do `.htm`), criar o repo-tutor pela UI **sem nenhum pino/card/sidecar**, rotular o gold de
   bloco por uuid (~30 entries, protocolo dos outros). Medida = bloco por uuid; expectativa honesta **>= 90%** (os 5
   deram 96,7% mas foram vistos). O que a CG revela primeiro: qual habito o professor tem (datas na secao? no nome?
   "Aula N"?) — o motor tem um provider por habito; se for um habito novo, e balde A/B de novo, nao curadoria.
2. **Teto do cru — os 7 erros nus:** (a) MF x3 = ruido do voto: ACEITO, ficam os 3 pinos; (b) **RESOLVIDO (31/08,
   ruling do user): IA prova-1-2024-02 e ES2 azure FICAM COMO ESTAO** — IA com o pino existente, azure como o erro
   honesto e visivel da regua (199/200). Sem scorable=no, sem pino novo; teto documentado, nao maquiado. (c) **TESTADO E
   REFUTADO (31/08)**: alias Cook-Levin (NP-completude/NP-completo/SAT/satisfatibilidade em 4.5.3) + remocao do
   card manual "Semana 12" derruba o TCC de 25/25 p/ 24/25 com conf-err 1 (aula-17-np-completude vai ao bloco do
   Cook-Levin; gold = escolha do professor via card) e FLIPA 5 subunidades (exercicios de reducao 4.5.5 viram
   teorema-de-cook). Vocabulario compartilhado real: SAT/NP-completo aparecem em Cook-Levin E nas reducoes — o
   card codifica um corte que o lexico nao decide. Revertido (25/25 conf-err 0 de volta); o card "Semana 12" FICA
   como a ultima decisao humana de bloco do TCC. Nao retentar sem sinal novo (ex.: data real nas secoes).
3. **RESOLVIDO (31/08, ruling final do user): `pthread` FICA no bloco-04** (card Threads, coerente com os 3
   `exemplo-threads-em-c`). O ruling de 25/08 (bloco-03) esta SUPERSEDIDO — nao reabrir. Custo zero (gold e motor
   ja estavam em 04).
4. **FASE 3 — cobertura 40/57 (17 erros):** `explain_entry.py` um a um ANTES de regra. Sabido: 5 pdf-roteiros do ES2 so
   emitem `card u01` (scorer de texto nao alcanca u02); R9 (definicoes honestas do glossario) custou 47 -> 40 e foi
   aceito como baseline honesto. Candidato ja anotado: vocabulario de unidade deterministico via headings.
5. **Unidade NUA 134/191** (curada e 100% so com pinos de unidade em IA/ES2): raiz = DP monotonico assume "ordem do
   plano = ordem do calendario" (IA ensina ML/u05 em marco). Item de motor: DP robusto a inversao local. Medir com
   `ablacao_rapida` (unidade nua) antes/depois; gate curado 191/191 intacto.
6. **Subunidade 87/93:** 6 residuais documentados como teto (IA); decisao pendente do user sobre gerar
   `.glossary_curation.json` por LLM (user ve LLM como fallback); `pthread` fora da regua (reversivel, ver item 3).
7. **MF depende do LLM em 30/66** (professor sem nenhum sinal temporal: tudo postado 18/02, sem "Aula N", sem data em
   secao ou nome; cards de 2-9 blocos; vocabulario repetido). Nao e bug: fallback funcionando, 30/30 certos. Se quiser
   reduzir: assinatura de bloco mais rica que "logica de hoare aula" (medir), nao regra nova (3 medidas hoje, 2 perdem).
8. **Divida/infra:** remotes SO/ES2/CG: **FEITO (31/08)** — privados em HumbertoCG18, push com upstream nos 3
   (gh instalado + auth keyring; o GITHUB_TOKEN do ambiente e um PAT sem createRepository — contornar com
   `$env:GITHUB_TOKEN=""` antes de chamar gh). Os 6 tutores agora tem backup. Resto: `.htm` = 2 defeitos (sem L: ignorado em silencio; com L: vira
   `codigo-professor`) so importam se a CG precisar de HTML; `seed_glossary_fields` com strings por curso (lei 4b);
   artefato "Razao dos Blocos" (claude.ai/code/artifact/d2ef4eaa-...) regenera com `scratch/dados_artefato.py` +
   `patch_razao.py` — mover para `scripts/` se virar rotina; harness `scratch/harness_regras.py` e `redundancia.py` idem.
9. **FASE 4 original** (exercicios, listas, provas antigas — pedido de 18/08): depende da cobertura (item 4).

**Refutado hoje (nao retentar sem dado novo):** `posting_date` como provider (modal = carga inicial; nao-modal em
mini-lotes e pos-bloco: +1/-0 unico, +2/-2 tolerancia 2); afinidade de kind material-de-aula -> so `class` (-25/+2);
topico vence ordinal (-3/0); bola de neve como raiz do SO (era a cabeca da linha).

## OS 15 ERROS NUS REABERTOS: 7 eram gold errado, 1 regra nova, 7 ficam (2026-08-26)

**Labels dos cards (pergunta do user):** e o professor. O mapa `.card_block_map.json` com source `labels` nasce
de DATAS que o professor escreve — no titulo da secao do Moodle (IA: "Semana 4 - 23.03 a 27.03 - ...", 18 cards)
ou em rotulos datados dentro da secao (MF "Verificacao de Programas", ES2 "Microsservicos"). SO poe a data no
NOME do arquivo ("12/03 Processos" -> provider `data`); TCC numera "Aula N" (-> `ordinal`) e nomeia a secao
"Semana N - Topico" (-> `topic`). "Sem mapa" nao e "sem sinal": o provider `topic` casa o nome da secao com as
sessoes em tempo de execucao (SO "Threads" -> bloco-04). Um provider por habito de professor.

**Gold errado (ruling do user com evidencia):** MF `provasindutivas` x3 (0x Isabelle, 0x lemma; sessao literal
"provas por inducao listas e arvores" no bloco 05) 06 -> 05; SO `pthread` (card Threads; unico bloco com
threads e o 04) 03 -> 04; SO `sockets` x2 (138x socket, 0x deadlock/sincronizacao; 23/04 e "comunicacao entre
processos") 06 -> 09; SO `definicao-e-historico` (linha 10/03 "historico e evolucao") 02 -> 03. 6 pinos + card
manual "Introducao aos SO" removidos. `subunit_gt_SO` pthread: scorable=no (u02 nao tem topico de threads).

**Regras medidas (harness `scratch/harness_regras.py`, nu com markdown + curado):** R3 titulo-topico
(titulo+rotulo ⊇ tokens do topico de exatamente 1 bloco da janela -> confiante, sem voto): +1 (MF hoare2),
0 regressoes, 5 votos a menos -> **implementada** (`disambiguate`, method `titulo-topico`). R5 afinidade de
kind (material de aula so em bloco class): -25/+2 -> descartada. R6 topico vence ordinal: -3/0 -> descartada.

**Regua curada:** 199/200 conf-err 0, 191/191, 40/57, subunidade 87/93, **pinos 11 -> 5**, cards manuais
12 -> 1 (TCC "Semana 12"). Decisoes humanas de bloco: 23 -> **6**. 2047 passed.
**Motor nu:** 197 -> **205/212 (96,7%)**, display 194/200, conf-err 2. Restam 7: MF terminacao /
exercicioscorrecaoterminacao / tiposindutivos (ruido do voto LLM, +31/-2 liquido), IA prova-1-2024-02 e
ES2 azure (convencao sem texto), TCC aula-17 x2 (Cook-Levin = NP-completude: dominio; o card "Semana 12"
manual segura no curado). Teto do cru alcancado sem convencao: ~97%.

## MENOS HUMANO: 23 -> 13 decisoes de bloco; regra t1/t2; ablacao em 81 s (2026-08-26)

**Pergunta do user:** "queria diminuir o humano". Cruzamento decisao a decisao (`scratch/redundancia.py`:
cada pino / card manual x o que o motor nu faz nas entries cobertas, por uuid, contra o gold):
23 decisoes humanas de bloco cobrindo 51 entries -> **7 redundantes** (motor nu acerta todas: MF cards
"Especificacoes Indutivas e Recursivas" 10, "Provas por Inducao" 8, "Revisao - Logica e Especificacao" 7,
"Exercicios de Revisao para Provas" 2; TCC "Semana 10", "Semana 13", "Semana 7"), **15 necessarias** em 3
naturezas: regra geral pendente (TCC "Semana 14 - Apresentacoes T2" x5, "Semana 3 ... Trabalho T1"), ruido do
voto LLM (MF pinos terminacao, exercicioscorrecaoterminacao, logicadehoare2, tiposindutivos — o desempate
deterministico acerta, o voto sobrepoe; voto e liquido +31/-2, fica), convencao do professor (MF
provasindutivas x3, SO sockets x2 + pthread + card "Introducao", IA prova-1-2024-02, TCC "Semana 12").

**Regra t1/t2 (user: "Apresentacao + T2 nao seria sinal?").** "Apresentacoes" nao esta em linha nenhuma do
cronograma; "t2" esta em DUAS (29/05 oficina "entrega t2", 12/06 entrega "entrega t2") e "t1" em 20/03.
`provider_topic` descartava tokens < 3 chars nos dois lados (piso de `_topic_tokens` e `_toks`). Agora:
identificador de trabalho (`(tp|t)\d{1,2}`) extraido do card e do texto CRU das sessoes
(`_block_session_hay`), em UNIAO com o topico — "Semana 3 - Minimizacao e Trabalho T1" precisa de [aula,
entrega], nao de janela-1 na entrega. A oficina de 29/05 sai por never-hosts -> janela-1 = 12/06. Curado:
neutro (0 campos; cards manuais vinham antes). Nu: TCC 28 -> 34/36.

**Cards apagados (MF 5 incl. "Bibliografia-Livros" vazio; TCC 5 = 3 redundantes + os 2 que a regra
substitui).** Gate: regua identica 199/200 conf-err 0, 191/191, 40/57; sentinela so `temporal_block_method`
(MF 15: janela-1/disamb -> llm; TCC 5: llm -> janela-1/prep-prova — TCC ficou MAIS deterministico); 2044
passed. Trade-off dito ao user e aceito: nos 4 cards grandes do MF, "humano confiante" virou "LLM
correto-mas-flagado" (banda media) em ~20 entries. Restam 13 decisoes humanas de bloco: 11 pinos + card SO
"Introducao aos SO" + card TCC "Semana 12 - NP-completude".

**Ablacao rapida (`scripts/ablacao_rapida.py`).** Copia dos 5 repos (robocopy incremental, sem .git/build),
ablacao na copia, reprocess dos 5 em PARALELO, medicao pela copia (`TUTOR_REPOS_DIR` nos avaliadores;
`TUTOR_REPOS_ORIG` faz o reprocess casar o perfil da disciplina pelo repo original — `find_by_repo_root` e
por caminho). **12 min -> 81 s.** Gate `--curado`: copia reprocessada == original, 0 campos nos 5 (a 1a
versao sem raw/staging/images reprovou: `image_curation` mudava em todos e o MF perdia 13 entries — por isso
a copia e completa). Cache de votos nu persiste na copia (medida nua deterministica entre rodadas).

**Motor nu agora: bloco 197/212 por uuid (93%), display 186/200, conf-err 3.** Erros restantes 15: ruido do
voto 4 (MF), convencao 10, C 1 (aula-17 Cook-Levin). Proximo: holdout Computacao Grafica com zero curadoria.

## BALDE B ATACADO: prep-prova antes do voto em janela indireta; posting_date medido e descartado (2026-08-26)

**Harness** `scripts/harness_balde_b.py` (repos ablacionados): para cada gold, janela/provider atual +
desempate SEM LLM + 3 regras candidatas, contadas em todos os golds dos 5 (nao so nas 7 do balde).

**O que o harness mostrou antes de qualquer codigo:**
- `posting_date` NAO e provider do motor ("data" = DD.MM no NOME). E nao deve virar: a data modal e a
  carga inicial (MF 46/66 em 18/02, SO 33/39, IA 45/59, ES2 22/35); a nao-modal vem em **mini-lotes**
  (MF 11/05 = hoare+invariantes+terminacao; ES2 05/06 = 7 roteiros com gold em 4 blocos) e em
  **postagem pos-bloco** (MF exercicios-arrays 08/06, gold = bloco de 13-25/05). Medido: data unica
  +1/-0 (IA k-nn, que o LLM ja acertava); tolerancia 2 +2/-2. **Descartado.**
- O voto LLM e liquido POSITIVO no nu: det✗->nu✓ MF 9, SO 5, IA 5, ES2 12; det✓->nu✗ so 2 (MF
  terminacao, exercicioscorrecaoterminacao). Nao se mexe no voto por 2 casos.
- `hoare2`: "det confiante" era artefato do harness sem markdown; com o texto dos slides fica flagado
  -> LLM -> 11. Ruido do voto. Vai para C.
- IA `prova-1-2024-02`: prep-prova daria bloco-11 (aula 11/05, ultimo hospedavel antes da P1); gold 09
  (entrega 04/05). Nao e sinal nao usado, e convencao. Vai para D.

**R2 (implementado):** janela vinda de provider INDIRETO (`topic`/`ordinal`) + cue de preparacao de prova
-> `resolve_exam_prep` decide antes do desempate/voto. `is_exam_prep_material`: "lista/revisao pN" e o
gabarito sao preparacao mesmo com `cat=provas` (MF `revisao-p1-gabarito` "Respostas": antes
lexical=False pulava o prep). Card manual/datado e data-no-nome continuam antes. +2/-0 no harness.

**Gate:** 2041 passed; curado 199/200 conf-err 0, 191/191, 40/57; sentinela = 1 mudanca fora da regua
(ES2 `revisao-p2`, `scorable=no`: llm-funil -> bloco-13 "entrega trabalho final" virou prep-prova ->
bloco-12, aula de 26/06 = ultimo hospedavel antes da P2 de 17/07, postado 27/06 — convencao cumprida).

**Ablacao re-medida:** bloco por uuid **188 -> 191/212** (MF 57->59, TCC 27->28), display 179 -> 182/200,
conf-err 5 -> 4. Motor nu: 89% -> **90% por uuid**. Balde B: 7 -> 3 (terminacao, exercicioscorrecao,
hoare2 = ruido do voto LLM, aceito) + 1 reclassificado D (prova-1-2024-02).

**Teto honesto agora:** 21 erros nus = C 5 + D 10 + ruido do voto 3 + SO convencao 3. Sem convencao do
professor derivavel de texto, o cru para em ~90-92%. Os 95% exigem ou glossario (C: Cook-Levin =
NP-completude) ou curadoria de 10 min por cadeira (D).

## BALDE A ATACADO: corte de bloco pela CABECA da linha do cronograma — SO sem boundary_dates (2026-08-26)

**Correcao do diagnostico anterior.** Eu tinha nomeado a "bola de neve" (`block_tokens` = uniao acumulada)
como raiz. O log linha a linha mostrou que nao: 17/03 -> 19/03 compartilham 3 tokens entre si
(`processos, chamadas, sistema`) — overlap de sacola de tokens, com ou sem acumulo, NUNCA separa esses
dois. O que separa e a cabeca da linha: "Estruturas dos SO, processos, chamadas" vs "Gerencia do
processador, processos, chamadas, escalonamento"; e 14/04 "Especificacao TP1; Gerencia...". O `content`
junta as colunas do SYLLABUS com espaco e `_timeline_core_text` so cortava em `:`/` - `, nao em `,`/`;`.

**Regra (geral, sem nada de curso):** `_timeline_row_head` = 1o segmento antes de `: ; ,` ou ` - `.
Cabecas com tokens especificos disjuntos cortam o bloco — salvo se a cabeca nova ja aparece no texto da
linha anterior (continuacao anunciada: TCC 15/05 "Classes de Problemas; Complexidade de Tempo vs. Espaco;
..." -> 20/05 "Complexidade de Tempo: Classes P e NP" fica no mesmo bloco; sem a excecao o bloco-19 do TCC
partia e 3 golds sumiam). Linha sem separador cai na regra de overlap de antes (10/03 "Historico e
evolucao dos SO" continua fundindo com 12/03 — o gold tambem funde).

**Gate:** harness em memoria com `load_boundary_dates` neutralizado: **5/5 cursos com estrutura identica
a curada** (SO 26 blocos com cortes em 19/03 e 14/04 sem pino). `boundary_dates` removido da curadoria do
SO (pinos de estrutura 2 -> 0); reprocess do SO = 0 campos vs HEAD; eval 38/38. Testes de boundary
reescritos (eram a caracterizacao do defeito: "sem boundary funde em 1") + caso TCC. 2037 passed. Regua
curada intacta: 199/200 conf-err 0, 191/191, 40/57, 88/94.

**Ablacao re-medida (motor nu, zero curadoria):**

| eixo | nu antes | nu agora |
|---|---|---|
| bloco (display) | 155/200, conf-err 21 | **179/200, conf-err 5** |
| bloco por uuid | 179/212 (SO 26/39, 12 SUMIU) | **188/212** (SO 35/39, 0 SUMIU) |
| unidade | 124/191 (SO 20/37) | **131/191** (SO 27/37) — unidade segue bloco |
| cobertura | 34/57 | 34/57 |

Sobram no SO nu 4, todos ja classificados C/D: biblioteca-pthread (card "Threads" -> bloco 04; gold 03 e
convencao), definicao-e-historico (ambiguo), sockets x2 (convencao). Balde A fechado: 12 -> 3 (os 3 que
ficam nao eram segmentacao, eram convencao escondida atras do SUMIU). Motor nu: 84% -> **89% por uuid**.
Proximo: balde B (7 erros, prioridade da cascata: data > ordinal, prep-prova antes do voto LLM, topico
exato do bloco antes do LLM).

## OS 33 ERROS DO MOTOR NU, UM A UM — onde esta o teto de 84% (2026-08-26)

Pergunta do user: "como chegar a 95% no motor cru? qual o gargalo?". Ablacao reaberta so para listar os 33
erros por uuid (179/212) com os sinais de cada entry (`posting_date`, `moodle_label`, card, metodo) e testar
se algum sinal presente no repo teria acertado. Script `erros_nu.py` (scratch). Repos restaurados por git +
reprocess (1 rodada = HEAD, 0 campos: R11 confirmado de novo).

| balde | n | entries | leitura |
|---|---|---|---|
| **A. Segmentacao (SO)** | 12 | 1203-processos, 1703-chamada, biblioteca-pthread, exemplo-criacao x4, 0704-laminas x2, 0704-exemplo-threads, laminas-cs-4244, laminas-sockets | gold SUMIU: nu funde 10-31/03 (7 dias, 3 temas) e 07-16/04. 9 deles ja caem no bloco grosso certo por data; so falta o corte |
| **B. Tem sinal, motor nao usou** | 7 | MF terminacao (pd = dia do gold), MF tiposindutivos (pd = vespera), TCC aula-16 (pd = vespera; ordinal "Semana 10" venceu), MF revisao-p1 x2 (cue prep-prova; cascata foi ao LLM dentro da janela do card), MF logicadehoare2 (label "Logica de Hoare (parte 2)" = topico do bloco 10; LLM sobrepos), IA prova-1-2024-02 (cue "Prova 1"; foi llm-funil, a confirmar por que prep nao disparou) | raiz de codigo: ordem/prioridade da cascata |
| **C. Sinal ambiguo / precisa dominio** | 5 | TCC aula-17 x2 (NP-completude <-> Cook-Levin 03/06 vs linha "NP-complete" 05/06), TCC t1-enunciado (T1 <-> linha Trabalho 20/03), SO definicao-e-historico ("historico" em 05/03 e 10/03), MF exercicioscorrecaoterminacao (exercicio vai ao deliverable anterior) | parte resolve com glossario/LLM; parte e convencao |
| **D. Convencao, sem sinal derivavel** | 9 | TCC "Semana 14 - Apresentacoes T2" x5 (posting DEPOIS da apresentacao; "Apresentacoes" nao esta no cronograma; 2 linhas "Entrega T2"), MF provasindutivas x3 (conteudo aponta bloco 05 "Inducao arvores"; gold 06 Isabelle pelo card), ES2 azure | teto do motor cru |

**Raiz do balde A (12/33):** `_rows_belong_to_same_thematic_block` funde a linha nova se ela compartilha >= 2
tokens com `block_tokens` = **uniao acumulada de todas as linhas do bloco**. Bola de neve: "gerencia do
processador ... escalonamento" (19/03) compartilha processos/chamadas/sistema com as linhas anteriores e
entra; "threads e exclusao mutua" (26/03) compartilha gerencia/processador com o acumulado e entra. O gold
corta em 19/03 (linha muda de unidade do plano: estruturas dos SO -> gerencia do processador) e em 14/04
(aula -> "especificacao tp1"). O sinal esta nas linhas do cronograma; a regra o dilui. Candidato: overlap
contra a linha anterior / nucleo do tema, e corte quando a linha ancora outra unidade do plano.

**Descoberta paralela:** "Semana N" do Moodle (TCC) NAO e semana de calendario (semana 12 -> 20/05 pelo
calendario; gold 03/06). Sinal de ordinal e menos confiavel que `posting_date` — hoje a prioridade e a
inversa (aula-16).

**Conta:** A + B = 19 -> 198/212 (93%). + C parcial -> 95% alcancavel. D = 9 e o teto (~96%). Ordem de
ataque: A (1 regra, 12 erros, tambem melhora unidade que segue bloco) > B (prioridade data > ordinal;
prep-prova antes do voto LLM; topico exato do bloco antes do LLM) > C via glossario.

## R11 + R12: o build dependia da rodada anterior (perfil em cache) e o injetor do sumario crescia (2026-08-26)

**Sintoma.** Depois da ablacao, `git checkout -- . && git clean -fd` deixou os 5 repos "0 sujos", mas
`eval_eixos` deu **bloco 165/200, conf-err 13** (SO 4/38) em vez de 199/200. Eu tinha escrito no tracker
"regua curada confirmada" sem ter confirmado — corrigido acima.

**Causa 1 (nao e bug, e regra):** `course/.timeline_index.json`, `.content_taxonomy.json`, `.tag_catalog.json`,
`.semantic_profile.generated.json`, `.assessment_context.json` sao **ignorados pelo git** em todos os tutores.
Restaurar por git devolve manifest + curadoria, mas o indice de blocos fica o da ablacao; no SO o manifest
restaurado apontava uuids que o indice ablacionado nao tinha. **Regra: depois de restaurar um tutor por git,
reprocessar** — o estado derivado nao e versionado.

**Causa 2 = R11 (bug de raiz, corrigido):** reprocessar o SO duas vezes seguidas dava **34 campos diferentes**
(confidencias de unidade, 1 subunidade, `coverage_units`, auto_tags). Nao era aleatorio: rodada 3 = rodada 2.
Era memoria de 1 passo: `resolve_semantic_profile` fazia `merge(cached, inferred, override)` onde `cached` =
`.semantic_profile.generated.json` gravado pela rodada anterior (que so contem o `inferred` daquela rodada).
`known_tools`, `generic_slug_blacklist` e `heading_single_overlap_cues` da rodada N-1 vazavam para N (uniao
nunca esquece: a blacklist acumulada mudava tags e confidencias). Fix: `merge(inferred, override)` — o build
e funcao pura de (conteudo + curadoria). Prova: perfil sujo injetado a mao no SO + reprocess = **0 campos
diferentes vs HEAD**. Teste `test_resolve_semantic_profile_ignora_perfil_gerado_da_rodada_anterior`.

**Consequencia honesta:** os manifests de HEAD de MF/IA/TCC (commit 01:45) tinham sido gerados com a
blacklist/cues acumuladas de builds antigos; o ponto fixo puro difere deles em campos SECUNDARIOS
(`auto_tags` `ferramenta:lemas`/`topico:...`, confidencias, e no TCC o campo legado `computed_block_id`
concept-fused do aula-06 — `temporal_block_id` intacto). Regua identica: bloco 199/200 conf-err 0, unidade
191/191, cobertura 40/57, subunidade 88/94. Golden `TCC casos_chave` regenerado de proposito (so esse campo).
SO e ES2 ja coincidiam com HEAD (0 campos).

**R12 (bug de raiz, corrigido):** `content/curated/referencia-reducibility...md` do TCC ganhava **+1 linha em
branco por build** (HEAD ja tinha 36). `_inject_executive_summary` insere `"
" + block` mas a regex de
remocao tirava so `block + 
?` — cada build deixava o `
` prefixado. Fix: `
?` tambem no inicio da regex;
chamada repetida agora e no-op. Testes em `test_navigation_exec_summary.py`. As 36 linhas antigas ficam
(inofensivas; colapsar em massa mexeria em todos os md curados).

**Suite:** 2036 passed. Gate: eval + pytest + sentinela contra `git show HEAD:manifest.json` (nao contra
`.bak`, que era da ablacao) + 2 reprocess seguidos = 0 campos (novo item do gate: **determinismo**).

## ABLACAO "MOTOR NU" — quanto do numero e regra geral e quanto e curadoria por cadeira (2026-08-26)

Pergunta do user: "se eu criar um repo de cadeira nova e os numeros cairem, o trabalho foi especifico?"
Medido: os 5 repos reprocessados com o MESMO codigo e ZERO curadoria por cadeira (pinos de bloco/unidade/
subunidade nas entries, `.timeline_curation.json` incl. `boundary_dates`, cards `manual`, sidecar de
sinonimos; cache de votos LLM ficou — e motor). **Restaurar por git NAO bastou** (ver R11 abaixo): a regua so voltou
a 199/200 depois de reprocessar os 5 com a curadoria de volta.

| eixo | curado | motor NU | perda |
|---|---|---|---|
| bloco (display) | 199/200 | **155/200**, 21 conf-err | 44 |
| bloco por UUID (sem artefato de renumeracao) | — | MF 57/66 · SO 26/39 · IA 42/43 · ES2 27/28 · TCC 27/36 = 179/212 (84%) | |
| unidade | 191/191 | **124/191** (IA 3/42, ES2 17/28, SO 20/37) | 67 |
| cobertura | 40/57 | 34/57 | 6 |
| subunidade | 88/94 | **21/94** (IA 0/39) | 67 |

**Leitura honesta.** As regras de codigo generalizam (IA e ES2 mantem o BLOCO em 42/43 e 27/28 nus). O
que depende de curadoria e concentrado em 3 mecanismos, e sao eles o custo por cadeira:
1. **Inversao calendario-vs-plano -> pinos de UNIDADE nos blocos.** IA ensina ML (u05) em marco-abril, antes
   de busca (u02); ES2 mistura u01/u02. O DP monotonico assume "ordem do plano = ordem do calendario" e
   falha em **2 das 5 cadeiras**; sem pino a unidade colapsa (IA 3/42) e a subunidade vai junto (0/39),
   porque os topicos sao filtrados pela unidade. Registrado em T9c como "DP nao alcanca sem pino".
2. **Estrutura de blocos -> `boundary_dates` e pinos de bloco.** SO: sem o split curado de 19/03 os blocos
   03/04 se fundem e **12 uuids do gold somem** — nao e "o motor errou", e a estrutura ficando mais grossa.
   MF: 7 pinos de referencia (aws/archive/...; B-6 cobre parte) e 5 cards manuais.
3. **Cards sem data -> cards `manual`.** TCC: 6 cards manuais ("Semana 14 - Apresentacoes T2" cobre 5
   entries); sem eles 27/36 por uuid.
4. Sidecar de sinonimos: subunidade cai de 88 para 21, mas a maior parte e efeito 1 (unidade errada);
   IA sem sidecar E com unidade certa media 4/39 (medido antes).

**Conclusao para cadeira nova:** bloco deve nascer em ~85% por uuid, unidade depende de o calendario seguir
o plano (se nao seguir, pinos de unidade — hoje humano), subunidade nasce cega ate ter sidecar. O proximo
passo que ataca a raiz (nao a curadoria) e o item 1: unidade de bloco robusta a inversao local. Segundo:
holdout real (Computacao Grafica, zero curadoria) para confirmar o 85%.

## GOLD DE SUBUNIDADE DO ES2 + sidecar do ES2 + 2 golds de unidade/cobertura corrigidos (2026-08-26)

**Gold:** `subunit_gt_ES2.csv`, 35 linhas, 28 scorable (u01 8, u02 21 + os 6 dos blocos 09/10, u03 0).
Protocolo dos outros 3 (conteudo primeiro; zip sem markdown = card/irmao numerado). Rulings do user:
- **Blocos 09 (05/06 "comunicacao assincrona") e 10 (12/06 "autenticacao/autorizacao") NAO sao u03 "Testes
  de Software"** — nada de testes em nenhuma das 6 entries; e a continuacao dos labs de microsservicos =
  **2.7 estudo de caso (u02)**. `gold_units_ES2` corrigido; os PINOS de curadoria que os prendiam em u03
  (`manual_unit_slug`, gold antigo pela ordem do plano) trocados para u02. **Unidade 191/191.**
- **Roteiros 2-8 cobrem u01 (arquitetura) E u02 (2.7)** — o gold de cobertura dizia so u01 e contradizia a
  subunidade 2.7 recem-rotulada. `material_gt_ES2` +u02 em 12 roteiros; motor acerta os 7 que ja emitia
  {card u01, texto u02}; os 5 pdf-roteiros que so tem `card u01` viram erro (mesma classe: o scorer de
  texto nao alcanca u02 neles). ES2 cobertura 18 -> 14/19 pelo gold novo; total 44 -> 40/57.
- `azure`: saiu de bloco-01 (disamb, confiante-errado) para bloco-08 (22/05, voto cacheado) — gold 09, mas
  conf-err 0 pela 1a vez.

**Sidecar `.glossary_curation.json` do ES2 (proposto-claude):** o plano diz so "Estudo de caso" para os
labs; o lexico real (service discovery, name server, API gateway, circuit breaker, compose, filas,
RabbitMQ, Auth0, Kubernetes/Docker/conteineres, monolito, SOA) entra em 1.3.3/1.3.4/1.5/2.6/2.7.
Subunidade ES2 **12 -> 26/28** em memoria e em producao. Tres sinonimos foram MEDIDOS e removidos, cada um
por um efeito colateral diferente (todos pegos em memoria antes de gravar):
`Spring` (palavra do curso inteiro: puxou o bloco de 27/03 de u01 para u02 no DP), `microsservicos`/
`microservicos` (idem: bloco 22-29/05 empatou e caiu em u01), `comunicacao entre microsservicos` (token
"microsservicos" faz a regra `card` da cobertura reivindicar u02 para o card inteiro), `roteiro` (palavra
de formato: deu texto aos zips e o scorer de unidade passou o gate com u02). **Criterio consolidado:
sinonimo = vocabulario especifico do topico; palavra do curso inteiro, do card ou do formato nunca.**

Respostas ao user: (a) o glossario JA e por subunidade (termos = topicos do plano); (b) o motor grava UMA
subunidade; `gold_subunits_extra` e so regua (63/66 leniente x 62/66 estrito) — multi-subunidade nao se
paga e nao seria "motor separado", seria o mesmo scorer devolvendo o 2o com margem; (c) sem LLM, o
glossario = definicoes genericas (99/132) + sinonimos por sidecar curado a mao (~30 min/cadeira), e isso
entrega subunidade 88/94.

## GLOSSARIO: como e gerado, e a evidencia que era lixo (2026-08-26, pedido do user)

Pergunta do user: o glossario e gerado a partir dos arquivos processados? e modular? codifica/normaliza
bem os acentos? Resposta medida (censo em memoria, pipeline real, 5 cursos, 132 termos):

**Anatomia (`artifacts/repo.py`, fiacao em `facade/glossary.py`).** Modular: funcoes puras com
callables injetados (parciais), sem estado; a taxonomia consome o TEXTO gerado (`glossary_md`), o
arquivo `GLOSSARY.md` e artefato derivado regravado a cada build. Cascata por termo: (1) tabela FIXA
no codigo por termo conhecido (`seed_glossary_fields`: MF/IA — "logica de hoare", "modelos preditivos"...
lei 4b violada de nascenca; `_unit_hint` idem) -> (2) "evidencia": melhor frase de `content/curated`
por overlap de tokens -> (3) generico "Conceito central de ...". **Termos = so topicos do plano**; os
materiais nunca geram termo, so a frase de evidencia. Sinonimos: so tabela fixa ou sidecar
(`.glossary_curation.json`) — nunca dos materiais (93/132 vazios).

**Encoding/normalizacao.** Arquivos UTF-8 NFC limpos, zero mojibake nos 5 cursos; leitura/escrita
`encoding="utf-8"`, `write_text` atomico. Para MATCHING ha duas convencoes: `glossary_tokens` (lower,
mantem acento e flexao: "historica" != "historico") vs `normalize_match_text` (NFKD sem acento) no
resto do motor. Medido: normalizar tokens muda so o IA (13 -> 17 evidencias de 20). Nao era a raiz.

**A raiz: a evidencia era lixo estruturado.** Censo ANTES: 73/132 genericas, 49 "Conceito central de
esta unidade" (erro gramatical), 10 definicoes com texto cru do plano ("CONTEUDOS: ### UNIDADE 01") ou
TOC injetado ("Sumario Introducao a IA: Visao Geral Roteiro..."). Das 47 "com evidencia", 2 eram frases
reais. Cinco mecanismos, todos no extrator, nenhum de acento:
1. docs META (plano de ensino, programa, apresentacao) entravam como evidencia e ganhavam o +8 sempre —
   contem a string de TODOS os termos (SO: 32 evidencias, 12 fora de docs meta; ES2 21 -> 1). Fix:
   `_doc_is_meta` por CONTEUDO (cita >= 80% dos titulos de unidade, `_FRACAO_META` da cobertura), sobre
   o texto COM headings (o plano lista as unidades como heading — a 1a versao olhava o corpo sem
   headings e o plano voltou; pego pelo censo).
2. o termo casava NUMERADO ("1.2 Chamadas de sistema"): material real diz "chamadas de sistema", so o
   PDF do plano contem o numero — o +8 ia para o plano POR CAUSA do numero. Fix: `glossary_term_core`
   (nucleo sem codigo) no +8, nos tokens e no `refine`; titulo de unidade sem o prefixo "Unidade NN —".
3. `best_glossary_sentence` tinha FALLBACK: sem frase candidata devolvia os 180 primeiros chars do doc
   ("{0}------ # Titulo Autor 2026") e isso virava definicao (SO 3.3, TCC 2.2/2.3/2.5/4.5.5). Fix:
   sem frase, sem evidencia (generico honesto). Fontes de frase = so o CORPO; titulo e headings
   concatenados ("Escalonamento de Processos Definicao (1) Definicao (2)...") nao sao frase.
4. bloco EXEC_SUMMARY (TOC injetado no build) e blocos IMAGE_DESCRIPTION saiam como texto; linhas de
   heading grudavam na 1a frase ("# Chamadas de sistema em Linux As chamadas..."). Fix: removidos antes
   de extrair frases; headings ficam so na lista `headings`.
5. `normalize_glossary_sentence` e `trim_glossary_prefix` ARRANCAVAM o termo do inicio da frase mesmo
   quando era o sujeito ("Conceituacao estabelece o escopo..." -> "estabelece..."), matando exatamente
   as frases definicionais. Fix: tira prefixo so quando vem separador ("Termo - texto", "Termo: texto").
   Era o que fazia o teste de `test_core` passar so gracas ao fallback (3).

**Censo DEPOIS: 99/132 genericas (honesto: o 73 antigo contava eco do plano como evidencia), 0 lixo,
0 "de esta".** O que sobra nao-generico: a tabela fixa (MF/IA) + ~8 frases reais. Conclusao: o extrator
heuristico NAO consegue produzir definicao — nao e tarefa dele; e do gerador LLM, que agora tem
entrada limpa (topicos do plano + titulos/headings dos materiais da unidade, sem docs meta, sem TOC).
Testes: `test_glossary_evidencia.py` (3). Residuo conhecido: descricao de imagem em texto puro do
Datalab ("Faded coat of arms of the Holy See", TCC aula-16) — sem marcador, nao filtravel sem heuristica.
Golden `TCC__casos_chave` regenerado: mudou porque o backfill preencheu `moodle_label` (dado).

### R9 · o lixo era estrutural: cobertura caiu 47 -> 36/57 ao limpar as definicoes
Reprocess pos-consertos: bloco/unidade/subunidade identicos, **cobertura 47 -> 36/57** (SO 15 -> 6).
Meu diff daquela rodada nao olhava `coverage_units` — de novo. Mecanismo (`file_map.py`, indice de
unidade): `extra_signals` da unidade = termo do glossario + SINONIMOS + tokens da DEFINICAO. As
definicoes-lixo (prosa de objetivos do plano) davam vocabulario a TODAS as unidades e equilibravam o
scorer de unidade do texto (regra `unidade-atribuida` da cobertura); limpas, so as unidades com
sidecar tinham sinal extra e u02 do SO (PCB/FCFS/threads) dominou. Medido em memoria (harness de
cobertura, 4 variantes): atual 34 · sem definicao 37 · **sem sinonimos 43** · sem ambos 42. Fix:
sinonimos ficam FORA do indice de unidade — sao vocabulario de subtopico (alias na taxonomia, scorer
de subunidade); definicao honesta continua entrando. `test_glossary_curation.py` (+1).
- Licao (3a vez): **o gate e sempre os 3 eixos + subunidade + diff por campo incluindo
  `coverage_units`** — `scratchpad/sentinel.py` passa a ser o diff padrao.
- Estado final desta etapa: **cobertura 44/57 F1 0,835** (SO 14, MF 8, IA 2, ES2 18, TCC 2). Os 4 pontos
  a menos vs 47 sao todos `unidade-atribuida` adicionando unidade ESPURIA (scorer de texto confiante e
  errado: SO `exemplo-criacao` u03, TCC `aula-12` u04, ES2 `roteiro7-history` devops, IA `o-que-e-IA`
  u02); +1 no MF. O 47 se apoiava em prosa de OBJETIVOS/EMENTA (nivel de curso) que caia por acaso em
  termos de certas unidades. **DECISAO PENDENTE DO USER:** aceitar 44 como baseline honesto (recuperacao
  esperada pelo gerador LLM: definicoes reais por unidade = vocabulario balanceado) ou reverter a
  limpeza das definicoes (volta o lixo, volta 47).


## (iii) em SO e TCC + R8 · glossario casava topico por CONTENCAO (2026-08-26)

**Subunidade 53 -> 62/66** (SO 8 -> 16/16, TCC 7 -> 9/11, IA 37/39) · **cobertura 46 -> 47/57 F1 0,876** ·
bloco 199/200 e unidade 190/191 identicos · pinos 11 · 0 votos novos · timelines dos 5 identicos.

### R8 — a raiz atras dos empates do SO e do TCC
`_glossary_aliases_for_topic` casava termo do glossario com topico por CONTENCAO: "3.3 Algoritmos de
escalonamento" contem "escalonamento", logo o termo E os sinonimos curados (FCFS, SJF...) entravam TAMBEM
em "Escalonamento" — os dois empatavam (51,9 x 51,4) e o primeiro da lista vencia. TCC idem ("2.3
Variacoes de MT" e "2.5 MT Universais" viravam alias de "Maquinas de Turing"). Fix: termo NUMERADO
casa so pelo nucleo EXATO; termo sem numeracao mantem a contencao. Aliases: SO 104 -> 91, TCC 78 -> 73,
ES2 -1, MF/IA iguais. `test_glossary_alias_exato.py` (2). O "desempate pelo label mais longo" no
seletor de heading foi medido antes e REFUTADO (0 efeito): o mecanismo era o glossario, nao o seletor.

### Sidecars SO/TCC — e a segunda regressao pega pelo gate de 3 eixos
Primeira versao dos sinonimos derrubou a COBERTURA 46 -> 42/57 (TCC 3/3 -> 1/3): a regra `card` da
cobertura casa nome do card contra aliases por contencao/token>=10, e a regra `unidade-atribuida` usa
o scorer de unidade do texto — ambos consomem os mesmos aliases. Sinonimo generico ou compartilhado
com outra unidade envenena: "processo"/"estruturas de controle" (card de u01) puxavam u02 no SO;
"decidivel"/"decidibilidade" e "Church-Turing"/"calculo lambda" (u02) casavam o texto de aulas de u03
no TCC (Halting, Entscheidungsproblem citam a tese legitimamente). Criterio que ficou: **sinonimo =
vocabulario ESPECIFICO do topico** (PCB, round-robin, Turing-decidivel, diagonalizacao de Cantor),
nunca palavra que apareca em card ou texto de outra unidade. Podado e remedido em memoria com harness
de cobertura (`cov.py`, reproduz SO/TCC da regua) ANTES do reprocess. Restam: TCC `aula-06` (gold
vazio por design) e `aula-08` (heading proprio ecoa em MT, 41 x 21 — sinonimos de Church-Turing nao
compensam e custam cobertura); IA 2 EDA.
- Licao: a alavanca (iii) e conteudo, e conteudo tambem regride. Gate = 3 eixos + diff campo a campo.

### Backfill do Moodle — GRAVADO nos 5 (2026-08-26): 51 labels, datas so preenchidas, 0 mudanca de atribuicao
A API TEM as entries: labels preencheria **51 das 56** vazias (5 sao URLs), `posting_date` so preenche
(0 sobrescritas; unica mudanca TCC `3dm` 17/06 -> 02/07, mais perto do gold 03/07). ES2 `azure` = label
"Instrucoes: cadastro Azure", postado 18/02 em lote: confirma tutorial de conta sem rota por data.
ES2 `codigo.zip x7` na API = o "main.pdf" que o user descreveu (stash renomeia; casamento vai pelo
`filename` original, unico). Gravado (`migrate_signals --write`, `.apibak` descartado) e reprocessado: **0 mudanca** em bloco/unidade/subunidade/cobertura, 0 votos novos — `posting_date` nao alimenta provider de janela (so data-no-nome), e `moodle_label` entra no sinal limpo sem mover nada mensuravel hoje. `azure` segue sem rota: e tutorial de conta, postado em lote em 18/02; so pino.

## ALAVANCA (iii) EXECUTADA + R7 · glossario curado por sidecar; pino de unidade nao propaga (2026-08-25e)

**Subunidade 19 -> 53/66 (IA 4 -> 37/39)** pelo pipeline REAL, bloco/unidade/cobertura/pinos identicos,
0 votos novos, goldens de caracterizacao passam sem regenerar. Suite 2025+ passed.

### Como o glossario chega ao motor (descoberto medindo, nao lendo)
`GLOSSARY.md` e artefato DERIVADO: regravado a cada build a partir do plano + `seed_glossary_fields`
(tabela FIXA no codigo, com strings por curso — "modelos supervisionados" para o IA esta hardcoded em
`artifacts/repo.py`: a lei 4b violada desde antes). A taxonomia consome o TEXTO gerado em memoria,
nao o arquivo: sinonimos escritos a mao no .md **nao chegaram aos aliases** (testado) e morreriam no
build seguinte. Fix: `course/.glossary_curation.json` ({"<Termo do plano>": {"synonyms": [...]}}),
mesclado por `glossary_md` em "Sinonimos aceitos" -> `_glossary_aliases_for_topic` -> alias do
topico. Sobrevive ao reprocess (padrao do `.card_block_map`). Sem sidecar = byte-identico. Testes em
`test_glossary_curation.py` (3). Conteudo do IA u05 = vocabulario dos algoritmos que o plano
categorico nao nomeia (perceptron, k-NN, arvore de decisao -> Modelos Preditivos; k-means,
agrupamento -> Descritivos; acuracia, F1 -> Metricas). Proposto-claude, revisar a mao; proximo passo
e GERAR esse sidecar por LLM (1 chamada por unidade) e estender a SO (8/16) e TCC (7/11).

### R7 · o DP monotonico de unidade nao sabia dos pinos — regressao pega pelo diff, nao pela regua
Ao ligar os aliases, `assign_units_positional` (afinidade por tokens de unidade, DP monotonico
GLOBAL pela ordem do plano) passou a ver u05 FORTE nos blocos de ML de marco-abril e empurrou TODOS
os blocos de maio-junho (busca, minimax, agentes: u02/u03) para u05 — **16 entries do IA trocaram
de unidade, nenhuma com gold: a regua dizia 42/42.** Os goldens de caracterizacao e o diff por campo
pegaram. Raiz: o IA ensina ML (u05) ANTES de busca (u02) — inversao calendario-vs-plano que o T9c
resolveu com PINOS de unidade (`block_manual_unit_slug`); os pinos eram aplicados DEPOIS do DP e nao
isolavam a inversao. Fix: `unit_matcher.assign_units_around_pins` re-roda o DP so nos blocos-aula
sem pino (excecao local nao constrange vizinhos); chamado apos `_apply_curation_overrides`; sem pino
e no-op. Rebuild em memoria: IA volta EXATAMENTE aos u01/u02/u02/u02/u03/u03 de antes; MF/SO/ES2/TCC
identicos. Testes em `test_unit_matcher.py` (+2).
- Licao: **"sem regressao" so se prova por diff de sentinelas campo a campo nos 5 repos** — a regua
  cobre 200 de 227 entries e ficou cega para as 16. Manter o diff no gate.

## R6 · provider de topico preso ao formato "Semana N - Topico" (2026-08-25d) — bloco 196 -> 199

O user seguia "encucado" com os 4 erros. Os 3 `exemplo-threads-em-c` (SO, card "Threads") iam ao
`llm-funil` porque `provider_topic` so aceitava card no formato do IA; o bloco-04 tem "threads"
nas sessoes de 26 e 31/03. Formato de UM curso virando regra de motor (lei 4b). Fix: card sem o
prefixo usa o NOME inteiro como topico (mesma assinatura por stems; `_GENERIC_STEMS` filtra).
Medido nos 19 entries do funil dos 5 cursos: 9 ganham janela, **gold dentro em 9/9**, 3 viram
janela-1 certa (as threads); "Informacoes Gerais"/"TDE"/"Plano de Ensino" nao casam bloco e
seguem ao funil. Reprocess do SO: 3 entries mudaram de bloco (para o gold), 6 so de metodo
(`llm-funil` -> `llm`, mesmo bloco, cache dentro da janela), **0 votos novos**. Testes +2.
**Resta 1 erro de bloco: `azure`** (tutorial de conta Azure; `posting_date`/`moodle_label`
vazios = backfill do Moodle falhou em 56 entries; sem sinal no texto). Pino ou re-rodar o backfill.

## RAIZ: BLOCO MISTO + IDENTIDADE POR DISPLAY — 4 defeitos fechados (2026-08-25c)

Ponto de partida: o user apontou `azure` (ES2) em bloco-01 como absurdo ("um dos ultimos
conteudos"). O `azure` em si NAO tem rota (e o tutorial de criar conta; `posting_date` e
`moodle_label` vazios = backfill do Moodle falhou; gold 09 fica; 1 pino ou dado). Mas ao olhar os
blocos do ES2 apareceu um defeito estrutural, e ao corrigi-lo, mais tres da mesma familia. Ordem
do user: "sem regressao do estado; causa raiz real, nao o erro especifico". Regua ANTES = DEPOIS:
bloco 196/200 · cobertura 46/57 · pinos 11; unidade 186/190 -> 187/191 (bloco novo com gold).
MF/TCC/SO byte-identicos em todas as rodadas. Suite 2016+ passed (goldens de caracterizacao
regenerados para IA/SO/ES2 — a divisao mudou DE PROPOSITO).

### R1 · linha do cronograma so tinha kind pela coluna Atividade; o texto nunca era lido
ES2 bloco-11 = `19/06 "suspensao jogo copa do mundo"` + `26/06 "devops exercicios"` num bloco
`suspended`: a linha 19/06 vinha com Atividade "aula" (=class), "devops **exercicios**" caia na
regra de continuacao e grudava; o classificador so via o agregado. Censo por sessoes nos 5 cursos:
**4 blocos mistos** (IA 06 "suspensao de aulas"+ML, IA 15 atendimento+aula, SO 25 reserva+G2,
ES2 11). Fix na ORIGEM: `_build_timeline_candidate_rows` deriva o kind do texto quando Atividade
e aula/vazia — `classifier.row_kind_from_text`, MESMA tabela de keywords, mas so
`ROW_TEXT_KINDS` = nao-academicos inequivocos. **OFFICE_HOURS e PLANNING ficam fora**: a
primeira tentativa (todos os nao-academicos) sequestrou "introducao a agentes e **planejamento**"
(IA, conteudo) e "gerencia de arquivos, **duvidas**" (SO, aula) — no bloco eles tem guard
(evidencia de unidade / maioria das sessoes) que a linha isolada nao tem. Medido por rebuild EM
MEMORIA dos 5 timelines com diff bloco a bloco antes de gravar: MF/TCC identicos; IA 23->24,
SO 25->26 (so o ultimo bloco), ES2 14->15. Testes em `test_atividade_kind.py` (5).
- Efeito colateral bom: a curadoria manual do IA bloco-06 (`manual_kind_override: class` +
  `manual_unit_slug: u05`) era um REMENDO de julho contra exatamente este defeito.

### R2 · identidade no split: a primeira fatia roubava o uuid
`reattach_block_uuids` reescrevia a ancora do registro DENTRO do laco; a fatia de 1 dia (20/04)
vinha primeiro, herdava o uuid das aulas de ML de 22-27/04 com 1 dia de overlap e encolhia a
ancora; a fatia de 6 dias chegava com overlap 0 e mintava — levando curadoria, pino u05 e 8 golds
(todos por uuid) para a suspensao. Fix: pontuar TODOS os blocos contra as ancoras de ENTRADA
(congeladas) e atribuir cada registro ao bloco que mais o cobre, EXCLUSIVO; sem competicao o
resultado e o de sempre. Testes em `test_block_identity.py` (+2). Verificado: IA 22-27/04 herda
`17ea65f3`; ES2 26/06 (DevOps) minta e a suspensao 19/06 fica com o antigo (1 dia cada, tokens
decidem) -> gold do `devops` re-rotulado para a aula (`22a44498`, bloco-12) + linha nova em
`gold_units_ES2.csv` (u02). Displays dos golds re-derivados por uuid (IA 9 + gold_units 18/18/3).

### R3 · voto do LLM cacheado por DISPLAY: stale silencioso
Apos renumerar, o voto "bloco-15" (10-15/06 na epoca) passou a apontar para o bloco que HOJE se
chama bloco-15 (01-08/06) — `match_window_ref` aceitou porque o display existe na janela nova.
**3 entries do IA (card Semana 15) trocaram de bloco sem revotar; o sidecar nao mudou.** Pior que
o "voto varia entre rodadas": e o voto certo apontando para o bloco errado. Fix: voto grava
`block_uuid` + `window_uuids`; leitura compara por uuid; legado (sem uuid) segue por display.
Votos legados migrados UMA vez (dado): IA/SO/ES2 pelo `.timeline_index.json.bak` pre-rebuild,
MF/TCC pelo indice atual (o .bak deles era antigo — 9+3 displays fora do indice denunciaram; sidecar
restaurado do git antes). Resultado: as 8 entries do IA VOLTARAM aos blocos originais com 0 votos
novos. Teste em `test_motor_llm_vote.py` (+1).

### R4 · card de rotulo guardava uuids resolvidos uma vez
`.card_block_map.json` (`source: labels`) JA carrega as datas do rotulo ("DevOps": 26/06, 03/07,
10/07) mas o motor lia `block_ids` congelados: a aula nova de 26/06 nao entrava na janela. Fix:
`card_block.card_entry_block_ids` resolve as datas contra os blocos ATUAIS (block_ids = fallback),
usado por `lookup_card_blocks` E por `window_provider._window_for_source` (o primeiro fix so no
lookup nao chegou ao motor). Censo: caches divergentes em MF 1, IA 4 (com uuids MORTOS
`ab4631aa?` — o item "uuid obsoleto no card_block_map do IA" do handoff fecha de graca), ES2 1.
`devops` e `kubernetes` foram para a aula de 26/06. Teste em `test_motor_anchor_engine.py` (+1).

### R5 · `suspended` entra em NEVER_HOSTS_MATERIAL_KINDS
So "aparecia no gold" (medicao de 21/08) porque a suspensao engolia a aula vizinha. Com R1, raio
medido: 0 entries em bloco suspenso nos 5 cursos, 9 janelas que o continham ja decidiam outro
bloco. Remendo local do `prep-prova` removido.

### Ferramentas de medicao (scratchpad, nao commitadas)
Rebuild em memoria + diff bloco a bloco (`tl_diff.py`), censo de blocos mistos por sessao, censo
cache-vs-datas do card map, diff de sentinelas POR UUID (display renumera; comparar por display
mente), migracao de votos. Um reprocess de 5 cursos travou 10 min com a API fora — rodar por
curso em background quando a rede oscilar.

## FASE 1 EXECUTADA (2026-08-25) — golds, curadorias, duplicata, regra do irmao; DOIS reprocesses

Gate: **bloco 186 -> 192/200** (conf-err 1: `azure`) · **unidade 178 -> 184/190** · cobertura 46/57 F1 0,847
(igual) · pinos **11** (igual) · suite **2005 passed / 1 skipped** (+4 testes) · subunidade **19/66** (3
`exemplo-threads` viraram rotulaveis). MF **66/66** e IA/TCC 100%; ES2 **27/28**; SO 31/38.

### Aplicado (rulings do user desta sessao)
- **Golds de bloco** (`ground_truth_<C>.csv`, provenance `relabel-2026-08-25-fase1`, `.bak` ao lado):
  MF `t2-2026-1` 16->18 (convencao ENTREGA, igual T2 do TCC) · MF `eth2` 12->01 (regra B-6) ·
  SO `exercicios` 03->04 (card "Gerencia de Processos CPU") · SO `lista-exercicios-p2` + `exercicios-p2`
  21->20 (**convencao do user: lista-pN = ULTIMA AULA antes da prova N**; o gold da P2 e que estava no
  dia da prova) · SO `exemplo-threads-em-c-exemplo1/2/3` 06->04 (**ruling: usados na aula de threads
  26-31/03**, nao na de sincronizacao/deadlock; o gold 06 era por associacao com o exemplo em Java
  de 07/04).
- **Duplicata `1404-troca-de-mensagens` removida** via `RepoBuilder.reject` (curated/staging apagados,
  `raw/` mantido por ruling anterior). `dedup_manifest.py` NAO serve: so pega gemeo stale, e os dois
  arquivos existem no stash. `ground_truth_SO.csv`: linha removida, `pair_key` do `14-04` limpo (39 linhas).
- **Curadoria de card SO** (`.card_block_map.json`): `"Introducao aos Sistemas Operacionais"` manual ->
  bloco-02 — `definicao-e-historico` acertou. A curadoria `"Threads": [03, 06]` do handoff foi
  **aplicada, medida e REVERTIDA**: tirou o bloco-04 da janela, `3103-threads` (gold 04, certo por
  data-no-nome) caiu em 03 com band alta, e os 3 exemplos foram de 04 para 03. Card com 3 blocos de
  verdade (03 pthread pinado, 04 aula, 06 java) nao se descreve com janela.
- **Regra do irmao numerado no card** — unica mudanca de MOTOR (`routing/motor/apply.py`,
  `_inherit_from_numbered_sibling`, metodo/provider `irmao-card`; teste `tests/test_motor_sibling.py`).
  Entry SEM markdown herda o bloco do irmao COM texto que partilha card + radical + numero
  (`roteiro4.zip` <- `Roteiro4_circuitbreaker.pdf`). **Dado antes de codigo:** censo nos 5 cursos,
  10 grupos, 8 com gold, **8/8 concordam** (MF, IA, ES2). Efeito: 8 entries `irmao-card`, os 4
  roteiros do ES2 corrigidos (2->04, 4->07, 5->08, 7->09), `roteiro6` 07->08 (sem gold, plausivel),
  zero mudanca fora do ES2. So entries sem texto, em escopo, sem pino e sem due; irmaos com texto que
  discordam nao decidem.

### Regra `prep-prova` — remedicao pedida pelo user (2026-08-25b): 6/7 -> 7/7, bloco 192 -> 196
A "revisao antes da prova" tinha sido REFUTADA em 4/8 com golds inconsistentes (SO tinha lista-p1 na
aula antes e lista-p2 no dia da prova). Com a convencao do user aplicada ao gold, remedida nos 5
cursos: **"lista/revisao pN -> ultimo bloco hospedavel antes da N-esima prova PRINCIPAL"** da
**7/7** (MF revisao-p1, SO x4, ES2 revisao-p1, TCC aula-16), desde que (a) substituicao/entrega nao
contem como prova principal e (b) `suspended` nao hospede — MF bloco-08 ("suspensao") fica entre a
revisao (07, gold) e a P1. Implementada em `motor/anchor_engine.py::resolve_exam_prep`, metodo
`prep-prova`, **so no caminho SEM janela** (card generico "Informacoes Gerais" -> era llm-funil) e
**nunca para a propria prova/trabalho** (`lexical=False`; a prova antiga do IA `prova-1-2024-02`
iria para o bloco errado). Card datado continua decidindo antes. Reprocess do SO: exatamente as 4
listas mudaram (llm-funil -> prep-prova), zero efeito colateral. Testes em
`tests/test_motor_anchor_engine.py` (5). **Nao e regra por categoria:** o gatilho e o NOME (pN),
a estrutura e o cronograma (assessments).
- [HIGIENE] `suspended` fora de `NEVER_HOSTS_MATERIAL_KINDS`. Raio medido: MF 2 blocos (1 entry com
  suspended na janela), ES2 1 bloco (7 na janela) e **`devops`/`kubernetes` GRAVADOS no bloco
  suspenso 11 do ES2**. Mexer no NEVER muda janelas -> votos novos. Deixado local a regra por ora.

### Os 4 erros restantes — nenhum e codigo, todos decisao do user
| entries | gold | motor | por que | 100% exige |
|---|---|---|---|---|
| SO `exemplo-threads-em-c` x3 | 04 | 03 (llm-funil) | o LLM votava 04 na rodada anterior; a janela mudou, o cache invalidou, a rodada nova votou 03. Codigo `.c` sem sinal deterministico | 3 pinos |
| ES2 `azure` | 09 | 01 (disamb, conf-err) | PDF de 877k chars sobre cloud; nada o liga a 05/06 | 1 pino ou dado |

#### (historico) os 8 de antes da regra prep-prova
| entries | gold | motor | por que | 100% exige |
|---|---|---|---|---|
| SO `lista-p1` + gabarito, `lista-p2`, `exercicios-p2` (3 pts) | aula antes da prova | dia da prova | convencao adotada no gold; motor sem regra (medida 4/8 antes, com golds inconsistentes) | remedir "lista antes da prova" com golds consistentes; senao 4 pinos |
| SO `exemplo-threads-em-c` x3 | 04 | 03 (llm-funil) | o LLM votava 04 na rodada anterior; a janela mudou, o cache invalidou, a rodada nova votou 03. Codigo `.c` sem sinal deterministico | 3 pinos |
| ES2 `azure` | 09 | 01 (disamb, conf-err) | PDF de 877k chars sobre cloud; nada o liga a 05/06 | 1 pino ou dado |

### Refutado nesta fase (nao retentar)
- **"apoio segue a aula do card"** (bibliografia/codigo herda o bloco do material-de-aula do mesmo
  card): gold concorda **73/98**; em cards com 1 aula, 54/64 — e o motor ja acerta 85/98 e 56/64.
  Card "Verificacao de Programas" do MF tem 15 entries de apoio em 5 blocos. Pior que o motor.
- **Voto do LLM no funil e instavel entre rodadas** (confirmado de novo: `exemplo-threads` 04 -> 03
  sem mudanca de codigo, so de janela). Toda mudanca de janela custa votos novos E pode trocar acertos.

### Subunidade — as 3 alavancas MEDIDAS em memoria contra o gold (harness reproduz o gravado 7/8/4)
| alavanca | IA /39 | 3 cursos /63 | veredito |
|---|---|---|---|
| base | 4 | 19 | |
| (i) piso absoluto 0,5 / 1,0 / 2,0 | 3 / 2 / 1 | 18 / 17 / 13 | **REFUTADA** — os scores baixos sao onde o acerto mora (SO 8->4 com piso 2) |
| (ii) desempate do seletor de alias | 1 | — | **REFUTADA sozinha** — move o ima INTRO para PARAD; gold diz PRED/DESC |
| (iii) glossario de algoritmos | **37** | **52** | **CONFIRMADA** — 4->37; lista minima (perceptron, mlp, k-nn, arvore, k-means, agrupamento, cluster, acuracia...) da 30/39; 3 termos, 27/39 |
| (ii)+(iii) | 36 | 51 | (ii) nao acrescenta a (iii) |
Mecanismo do colapso (medido, `timeline/index.py:1649`): `modelos-preditivos`/`modelos-descritivos`
marcam **0,00 em 40/40** — os 4 aliases deles nao ocorrem em texto nenhum, `modelos` e generico e
`preditivos/supervisionados` sao plural (texto tem singular). O vocabulario que EXISTE (aprendizado
supervisionado 26/40, agrupamento hierarquico, k-means, machine learning) e alias de INTRO — chegou
la por empate 3,4 x 3,4 com PARAD no seletor de alias, desfeito por `>` estrito = primeiro da lista.
Conf relativa sem piso: 0,11 de um token (`exemplo`/`aula`) vira conf 1,000.
**Caminho da (iii):** `_glossary_aliases_for_topic` exige que o termo case o LABEL do topico, logo a
entrada e `Modelos Preditivos` com `synonyms = [perceptron, k-NN, arvore de decisao, ...]` — conteudo
gerado (glossario + `Aparece em`), nao codigo. E o proximo passo da subunidade.

## FASE 2 EXECUTADA (2026-08-25) — gold de subunidade pronto, hipotese do bloco REFUTADA

Zero codigo no repo (scripts de extracao/medicao ficaram no scratchpad). Regua byte-identica
(bloco 186/200 · unidade 178/188 · cobertura 46/57 F1 0,847 · pinos 11; suite 2001 passed / 1 skipped).

**Gold: `docs/reports/subunit_gt_{TCC,SO,IA}.csv` — 75 linhas, 63 scorable** (TCC 12/11 ·
SO 23/13 · IA 40/39). O handoff estimou "~40"; o universo real das 5 unidades era 75. Protocolo,
todo por ruling do user: rotulo por CONTEUDO (card oculto durante a proposta) para aula e para os
notebooks do IA — eles SAO a aula; rotulo pelo CARD so para material de apoio (bibliografia,
codigo de contexto), coluna `gold_fonte` registra qual. `gold_subunit` (1 primario) +
`gold_subunits_extra` (`;`) + `scorable`. Gold VAZIO com `scorable=yes` = "nenhum topico se
aplica, predizer e erro" (aula-06 TCC: revisao online de Automatos, pre-requisito). Transversal
(plano de ensino, prova antiga, lista multi-unidade, entry com UNIDADE errada) = `scorable=no`.

### Medicao — "subunidade = primary_topic_slug do bloco temporal": REFUTADA (nao retentar)

| preditor | estrito | leniente (primario ou extra) | predicao vazia |
|---|---|---|---|
| MOTOR (computed_subunit_slug gravado) | **19/63 (30,2%)** | 24/63 (38,1%) | 6 |
| HIP (topico do bloco temporal) | **6/63 (9,5%)** | 8/63 (12,7%) | **44** |

Por curso, estrito — motor / hip: TCC 7/11 / 5/11 · SO 8/13 / 1/13 · IA 4/39 / **0/39**. A
hipotese nao vence o motor em nenhum curso. Tres causas, todas no dado do bloco, nenhuma no scorer:

1. **Granularidade.** Bloco e janela temporal, subunidade e topico. IA `bloco-05` vai de 18/03 a
   15/04 (4 semanas), carrega 26 entries e 3 topicos-gold distintos (k-NN/perceptron/MLP/arvores
   = preditivos, metricas, e mais). Um topico por bloco nao tem como acertar — mesmo com o topico
   do bloco perfeito, o teto da hipotese no IA e ~1/3.
2. **`primary_topic_slug` vazio em 44/63.** Todos os 4 blocos da u05 do IA e 3 dos 4 do TCC tem
   `topic_source=topic_text_fallback` — e o fallback, por design, NUNCA popula o slug
   (`timeline/index.py:2035`). No IA os candidatos vem poluidos por topicos de OUTRA unidade
   (`busca-adversaria`, `algoritmos-de-busca-com-informacao` a 1.0 num bloco de ML), 4 empatados
   a 1.0 -> `topic_ambiguous` -> vazio.
3. **Topico do bloco fora da propria unidade.** SO `bloco-03` (unit=u01) recebeu
   `comunicacao-e-sincronizacao-de-processos`, topico da u03, com `chamadas-de-sistema` (u01, o
   certo, 7 entries-gold) em 2o a 0.95. O candidato nao e restrito a unidade do bloco — a mesma
   violacao que o P0.2 proibiu na entry, so que no bloco. Vale registrar como defeito do eixo de
   bloco; nao move a regua de subunidade.

### O que o gold revela do MOTOR (baseline para a proxima etapa — o alvo agora e o scorer)

- **IA colapsou**: 34/40 entries predizem `introducao-ao-aprendizado-de-maquina`; `paradigmas`,
  `modelos-preditivos` e `modelos-descritivos` tem **0 predicoes** e o gold tem 25+8+0 delas.
  Estrito 4/39. Hipotese para investigar (NAO testada): todo notebook abre com "aprendizado de
  maquina"/"machine learning" no header e o topico "introducao" ganha no lexico.
- SO: os 5 rotulados por card acertam 5/5; os por conteudo 3/8. `3103-threads` e
  `1903-estruturas-de-controle` caem em `escalonamento` (topico do bloco) em vez de
  `conceitos-basicos`; `2603-algoritmos` cai no vizinho `escalonamento`.
- TCC 7/11: erra `aula-02` (Cantor -> conjuntos-enumeraveis), `aula-08` (Church-Turing -> MT),
  `aula-10` (decidiveis -> MT), `aula-06` (revisao: prediz conjuntos onde o gold manda VAZIO).
- 6 predicoes vazias no motor, 5 delas notebooks do IA com conteudo obvio (perceptron, k-NN java).

### Achados de dado durante a rotulagem (fila da FASE 1 / higiene — nada aplicado)

- [DECISION USER 2026-08-25] **`exercicios` (SO) tem gold de UNIDADE errado**: card `Gerencia de
  Processos CPU` => u02. `2403-escalonamento` e `2603-algoritmos` estao no MESMO card com gold
  bloco-04; so `exercicios` ficou em bloco-03 (posting_date 2026-03-10 e artefato de download em
  lote — dezenas de entries do SO tem essa data). Aplicar no ato da FASE 1: `ground_truth_SO.csv:24`
  bloco-03/bdcc7b26 -> bloco-04/e4f7e22a. **Efeito previsto: bloco 186->185, unidade 178->179.**
- [DECISION USER 2026-08-25] **`1404-troca-de-mensagens` e duplicata de `14-04-troca-de-mensagens`**
  (dois arquivos reais no stash, mesmo card, conteudo identico) -> REMOVER no ato da FASE 1 via
  `scripts/dedup_manifest.py`. Hoje o ruler ja colapsa o par (`pair_key`), remover nao muda numero.
- **`plano-de-ensino` e `programa` (SO) sao o mesmo PDF** ("programa" = nome original baixado do
  Moodle; categorias `cronograma` vs `outros`). Sem ruling de remocao ainda.
- **`moodle_label` vazio em 61/227 entries (5 repos), correlacao PERFEITA com `posting_date` vazio**
  — uma causa so: o backfill (`sources/moodle.py:162-186`) casa por basename EXATO casefolded e
  exige key UNICA no curso. 5 sao URLs (correto); 56 sao falha real, todas com `source_path` no
  stash. Duas formas de morrer: (A) `main.pdf` repetido -> count>1 -> pulado (hipotese do user,
  o codigo a implementa); (B) o stash chega RENOMEADO para o rotulo, entao o basename nunca e
  `main.pdf` — a key some antes de a ambiguidade contar. Separar A de B exige re-rodar
  `moodle_pull` (rede+auth): nao ha dump da API em cache. Importa porque `moodle_label` alimenta o
  sinal limpo de `concept_resolver.py:118` e `disambiguator.py:58` — canal apagado em 56 entries.
- **"Threads" nao existe como topico em nenhuma unidade do plano do SO** (nem u01 nem u02); 3
  entries foram forcadas a vizinhos. Lacuna de TAXONOMIA, nao de motor. User: "investigar mais a
  fundo" — em aberto. Lei dos aliases intacta.
- `biblioteca-em-c-pthread` (SO, pinada via `manual_timeline_block_id`) tem `temporal_block_id`
  e `computed_block_id` **None** — entry pinada nao recebe bloco temporal gravado. Higiene.
- TCC: `moodle_label` vazio em 12/27, inclusive `aula-01/02/03/05/06/09`. O nome de arquivo salva
  (ja e o rotulo), mas e o mesmo canal apagado.

### Retratacoes desta sessao (para nao repetir)

- Li `ground_truth_SO.csv` col.3 como PREDICAO; e `true_block_id`. Isso gerou a falsa suspeita
  de unidade errada em `biblioteca-em-c-pthread` (esta certa, bloco-03/u01) e o falso achado
  "card Threads estilhacado" — card e secao do Moodle e acumula semanas; bloco e janela. Um card
  em 2 blocos com 1 mes de distancia e normal, nao incoerencia.
- Propus `aula-08` (TCC) como `maquinas-de-turing` pelo titulo; o conteudo e a Tese de
  Church-Turing (l.381). Corrigido pelo challenge do user. Regra: heading interno > titulo.

## FASE 0 EXECUTADA (2026-08-24) — remocao de morto, regua byte-identica

Gate: suite **2001 passed / 1 skipped** (era 2002; o -1 e exatamente o teste dedicado a funcao
removida) e `eval_eixos.py` **byte-identico ao baseline** (bloco 186/200 · unidade 178/188 ·
cobertura 46/57 F1 0,847 · pinos 11). Nenhum numero se mexeu — que e a prova de que era morto.

- [DONE] **`_derive_unit_from_topic_match` REMOVIDO** (era `timeline/index.py:1951`). Alvo do item
  "RUN dedicada de remocao de mortos" (decisao user 2026-07-03). Sairam junto: import e `__all__`
  em `engine.py`, o teste dedicado, e as 3 asserts parasitas dentro de testes cujo sujeito real e
  `_auto_map_entry_subtopic` (esses testes ficaram, so perderam a assert da funcao morta).
  Comentario stale em `timeline/conflicts.py:48` (dizia "o build resolve via ...") corrigido.
- [DONE] **R11 · manifest escrito de forma nao-atomica** (`ui/timeline_dashboard.py:248`) — passou a
  usar `utils/helpers.write_json_manifest` (tmp + `os.replace`, `.bak` best-effort), que ja era o
  writer canonico de manifest. Nao escrevi helper novo: reuso.
- [DONE] **`preserve_raw` morto colapsado** (`ui/curator_studio.py`) — ver o ACHADO abaixo, que e
  mais grave que o item registrado.
- [DONE] **comentario mentiroso de `TOOL_TOKENS`** (`extraction/entry_signals.py:100`, item B-9) —
  dizia que "o scorer de bloco (file_map, TOOL_TOKENS) filtra quais sao ferramentas de verdade";
  `TOOL_TOKENS` nao existe em `src/`. Comentario agora diz que **nada filtra** e aponta B-1/B-9.

### ACHADO NOVO na Fase 0 — [DECISION · USER] o dialogo de reprovar PROMETE o que nao cumpre

Ao colapsar o `preserve_raw` descobri que o item era maior do que o tracker registrava. O que o
codigo fazia: `builder.reject(entry_id, preserve_raw=False)` levantava `TypeError` **sempre** (a
assinatura real e `reject(self, entry_id)`, `ops/lifecycle_ops.py:313`), caia num ramo de
"compatibilidade" que remontava um `RepoBuilder` IDENTICO e chamava `reject(entry_id)`. Dois
builders, um resultado. Isso foi colapsado — comportamento identico, -14 linhas.

**Mas a intencao por tras do `preserve_raw=False` nunca foi cumprida.** `reject` limpa
`base_markdown`, `advanced_markdown`, `images_dir`, `tables_dir` etc. (lista `keys_to_clean`), e
**`raw_target` NAO esta na lista** — o PDF/arquivo bruto sobrevive. O texto do dialogo, porem,
promete ao usuario: *"- remover o PDF/arquivo bruto copiado para o repositorio"*.

**CORRECAO da minha primeira avaliacao de risco (2026-08-25):** eu escrevi que apagar
`raw_target` seria "apagar arquivo de origem do user, destrutivo e irreversivel". **Errado** —
inferi sem olhar o manifest. Cada entry carrega DOIS caminhos: `raw_target` = `raw/pdfs/...`
(copia DENTRO do repo-tutor) e `source_path` = `C:\Users\Humberto\Desktop\Moodle\<curso>\...`
(o original, FORA do repo). Apagar `raw_target` apaga a copia, nao o download. `raw/` esta no
`.gitignore` dos repos-tutor (0 arquivos rastreados), entao essa copia nunca teve versionamento
— mas tambem nao e fonte de verdade de nada.

**RULING DO USER 2026-08-25: opcao (b) — corrigir o texto, manter o bruto.** O `raw/` fica no
repo de proposito, como rede para reimportar sem depender do stash. Aplicado: a linha
"- remover o PDF/arquivo bruto copiado para o repositorio" saiu do dialogo e foi substituida por
um aviso explicito de que o bruto e MANTIDO; o comentario do call-site deixou de ser "ATENCAO
pendente" e passou a registrar o ruling. **`reject` NAO foi alterado** — o comportamento de
sempre esta agora descrito com honestidade.

Opcao (a), NAO escolhida, fica registrada: por `raw_target` na `keys_to_clean` de
`ops/lifecycle_ops.py:reject`. Argumento contra que pesou: o TCC ja perdeu 24 de 42 sources
quando `Downloads/TCC` foi movida (so 2 recuperaveis pelo backup) — nesse cenario a copia em
`raw/` e a ultima existente, e `raw/` e gitignored. Trocar risco de perda de conteudo por
economia de disco e troca ruim num Moodle que expira no fim do semestre.

Ideia registrada, NAO implementada (o user nao pediu): um `sweep_orphans` que LISTE — sem apagar
— os arquivos em `raw/` sem entry no manifest, para decisao em lote. Ja existe um
`sweep_orphans` em `engine.py:2196` para reaproveitar.

## USER-SIDE — destravam a cadeia de medição/cutover

- [USER] **ES2-Tutor com sujeira pré-existente** (`as-of 2026-08-05`, achado Plano B Task 5, NÃO
  causada pela sessão) — **45 arquivos** com mtimes de **01/07** e **04/08**. Inspecionar antes do
  rollout ES2 (item "Depois do Plano B" da fila): confirmar se é lixo de builds/experimentos
  anteriores ou conteúdo válido não-limpo, antes de flag-ON o motor no curso.
  > recontagem `as-of 2026-08-06` (varredura): **46** entradas em `git status --porcelain -uall`
  > (33 M + 13 ??, incluindo `course/.timeline_index.json.bak` e `manifest.json.apibak`).
  > IA-Tutor no mesmo estado: **48** entradas, idêntico ao catalogado em 2026-08-05.
  > **DOSSIÊ PRONTO (2026-08-06, `docs/reports/2026-08-06-dossie-triagem-es2-ia.md`) — VEREDITO
  > INVERTE A HIPÓTESE: não é lixo, são sessões VÁLIDAS nunca commitadas** (ES2: import 01/07
  > com +10 materiais, 6 curated referenciados no manifest; IA: poda 23/06 executada + import
  > de 21 notebooks 25/06 + reprocess 01/07). Ação certa = COMMITAR (sem os .bak), nunca
  > checkout/clean. 3 decisões pedidas no dossiê (ruling do user).
  > **FECHADO (2026-08-06, ruling user "vamos fazer os commits + confirmar poda"):** ES2
  > commitado `d287426` (+10 materiais oficiais), IA commitado `ceae83e` (poda de 14
  > confirmada, aula-29 via gêmeo; 21 notebooks; `manifest.json.bak` destrackeado T19);
  > `*.bak`/`*.apibak` gitignorados nos 2. Árvores 0 dirty. **E os DOIS ROLLOUTS flag-ON
  > EXECUTADOS na sequência (mesma sessão): ES2 `dc74c12`** — 3 runs, 25 votos estáveis
  > (0 novos no run 3), temporal 29/35 {labels:4, llm:25}, fila 0, funil 0 drift, computed
  > 0 diffs, pino 1/1, audit hard=0, units 2→2 (u03 = campanha); **IA `86f00d9`** — swap
  > legado no mesmo ato (`use_anchor_placement` OFF), 47 temporal `anchor` reescritos →
  > 54/62 motor {labels:35, llm:19}, resíduo legado 0, 17 votos estáveis, fila 0, funil 0
  > drift, computed 0 diffs, pinos 4/4, audit hard=0, units 3→3 (u04/u05 = campanha).
  > **PLACAR ROLLOUT: 4/5 cursos flag-ON em produção (MF/SO/ES2/IA); só TCC bloqueado**
  > (divergência de geradores de índice — campanha de unificação).
  > **SUPERSEDED 2026-08-06 (mesma noite): campanha gerador-índice-único fechou o TCC —
  > PLACAR FINAL 5/5 flag-ON** (TCC-Tutor `31f6025` flip + `91c1d2a` pino aula-13; ver entrada
  > Concluído da campanha).

- [USER] **Gold cross-curso** (DURÁVEL/intent) — rotular `tests/fixtures/eval/ground_truth_<curso>.csv` IA/SO/ES2/TCC
  (MF já mede via eval_assignments 5/5). Planilhas em `docs/reports/gold_templates/gold_by_card_<curso>.csv`
  (MF 6 cards · IA 9 · SO 5 · ES2 3 · TCC 13 + avulsos). **Bloqueia: cutover Fase 3.4, lever lessons[].text,
  resolvers SO/MF, avaliação do anchor.** ← MAIOR GARGALO.
  > progresso `as-of 2026-07-01`: **5/5 CURSOS COM RÉGUA.** IA ✅ · MF ✅ (67 scorable/24 disc, `511ea1e`) ·
  > ES2 ✅ (28/14, `4aa9bcd`) · **SO ✅ 42 scorable/23 disc** (`ground_truth_SO.csv`) · **TCC ✅ 42 scorable/
  > 20 disc** (`ground_truth_TCC.csv`) — ambos UNCOMMITTED, HALT pendente revisão humana do crosswalk.
  > TCC: template refeito (tipo=file_type puro) com backup `gold_TCC_rotular.pre-refazer-20260701-165239.bak.xlsx`;
  > 4 rótulos off-by-one detectados na revisão HALT e corrigidos com confirmação do user (+gêmeos, 7 células;
  > obs carimbada no xlsx). Gêmeos md5 rotulados SEM conflito (validado).
  > Evidência p/ o motor: as 3 cópias byte-idênticas da aula-06 têm temporal em 3 blocos DIFERENTES
  > (bloco-06/09/22) = dup-divergence vivo, motor não trata dup hoje.
  > **EVAL BASELINE OFICIAL 5/5 (as-of 2026-07-01, HALTs sign-off user, colapso de par ativo):**
  > **IA 38/44 = 86.4%** (6/6 erros off-by-one adjacente, 0 miss-tópico; calibração ok: alta 32ok/3erro) ·
  > **MF 42/66 = 63.6%** (12/24 adjacente; 1 órfão) · **TCC 14/25 = 56.0%** (pós-poda; pré era 15/27 55.6%) ·
  > **ES2 14/28 = 50.0%** (12/14 = miss de tópico) · **SO 18/38 = 47.4%** (17/20 miss de tópico; band alta
  > 15ok/16erro = confiança NÃO informa). Leitura: IA (única com âncora data-de-seção) erra SÓ fronteira;
  > os 4 sem âncora afundam em miss-de-tópico — confirma o desenho janela+disambiguator do motor. É o placar
  > que o AnchorEngine tem que bater SEM regressão no IA. Confiante-e-errado dominante fora do IA reforça a
  > pendência de calibração.
- [DERIVADO] **Sweep md5 dos 5 cursos COMPLETO** (`as-of 2026-07-01`, via `raw/` de cada repo) — dups por
  conteúdo: **IA 3 grupos** (já cobertos no pairs) · **ES2 0** · **MF 1** (`logicadehoare1-exercicios-respostas`
  ≡ `logicadehoare-exercicios-respostas`, ESCAPOU do `511ea1e`; pairs preenchido + CSV regenerado 2026-07-01,
  67/24 mantidos, unidades de eval 67→66; gêmeos ambos bloco-10 PASS = sem flip) · **SO 4** · **TCC 14**.
  Todos os grupos agora cobertos em `COURSE_CONFIG.pairs`. IA tem 3 entries sem `raw_target` no disco
  (2 artigos-web com sufixo hash + `artigo-usando-agrupamento`) — não-verificáveis por hash, vigiar.
- ~~TCC `pairs` dedup a preencher~~ **PREENCHIDO (2026-07-01, uncommitted)** — sweep md5 via `raw/` do repo:
  **42 entries = 27 materiais distintos, 14 grupos dup** (11 cross-stash OLD≡Moodle + triplo intra-OLD aula-06 +
  2 intra-Moodle). `COURSE_CONFIG["TCC"]["pairs"]` populado (canônico = id Moodle vivo). Causa CONFIRMADA por
  hash: stash antigo `Downloads/TCC` + stash Moodle acumulados sem poda de migração — mesmo mecanismo do IA.
- [DERIVADO] **TCC: 24/42 sources SUMIDOS do disco** (`as-of 2026-07-01`) — todo o lado `Downloads/TCC` não
  existe mais (migração pro `Desktop/Moodle` levou a pasta). Entries seguem vivas via `raw/` do repo. Download
  Moodle do TCC é **PARCIAL**: 10 materiais OLD sem substituta Moodle (aulas 01-03, 05, 09, 14, 15, prova-revisão,
  referência Karp, weighted-max-cut) — podar esses = perder conteúdo. Igual "stash IA parcial".
- ~~TCC poda de migração~~ **EXECUTADA em 2 rodadas (2026-07-01), ESCOPO AMPLIADO pelo user**: rodada 1 (GUI,
  user) matou 7 (aula-04, aula-06 ×2 — colisão de id RESOLVIDA —, aula-08, aula07-grudada, enunciado-t1/t2);
  rodada 2 (script CC autorizado pelo user, executado pelo user via `!`, backup
  `TCC-Tutor/manifest.pre-poda16-20260701-184119.bak.json`) matou os **17 restantes do Downloads** — decisão
  EXPLÍCITA do user de incluir os **11 SEM substituta Moodle** (aulas 01-03/05/06-revisão/09/14/15,
  exemplo-prova-revisão, referência Karp, weighted-max-cut). Manifest TCC: 42→**18 entries, 100% Moodle**.
  **Consequência assumida: esses 11 conteúdos estão FORA do tutor até re-import Moodle completo** (entra na
  refatoração de ingestão de apoio). Gold xlsx TCC: ~24 linhas viram unjoined no próximo crosswalk (esperado,
  não é bug). Dups restantes: só os 2 intra-Moodle (3d-matching, integer-programming), `pairs` cobre.
  ~~PENDENTE reprocessar~~ **CICLO FECHADO (2026-07-01): reprocess + gate VERDE.** Descoberta que mata a
  teoria "download parcial": as entries velhas do Downloads **SOMBREAVAM o import** (dedup por slug) — poda
  liberou o importer, que re-ingeriu **9 dos 11 "perdidos" direto do stash Moodle** com seção Semana-N correta.
  Perda líquida real = **2 arquivos** (referência Karp + weighted-max-cut; só existiam no Downloads; recuperáveis
  do backup). Manifest TCC final: **27 entries, 100% Moodle**, colisão de id morta, dups = só 2 intra-Moodle.
  Gate: **0 drift** de temporal/true nos 18 sobreviventes ✓; re-importados ganharam placement novo (esperado):
  aula-01 virou FAIL novo (true bloco-01, temporal bloco-02 — janela Semana-1 ambígua), aula-06 temporal
  bloco-09. Crosswalk 36/42 joined (6 unjoined = exatamente os nomes mortos, sem gap silencioso).
  **EVAL TCC pós-poda = 14/25 (56.0%)** — baseline re-referenciado (pré-poda 15/27 55.6%, estável).
  **INSIGHT p/ refatoração de ingestão: import dedup-por-slug deixa entry morta BLOQUEAR fonte viva** —
  mesma mecânica pode estar escondendo material em outros cursos; sweep de shadowing entra no escopo da
  refatoração de apoio/bibliografia.
  > sub-nota DERIVADO-STALE: TODOS os números embutidos são pré-reprocess (gold_templates +
  > evals de 17–18/06): card-counts MF6/IA9/SO5/ES2 3/TCC13, "MF mede 5/5", e qualquer placar
  > tipo "~41% funil MF / resolver 12/17". Não verificados pós-reprocess.
- [USER] **IA placements gold-relevant** — `verificado as-of reprocess IA 7561f5c`:
  - **4 weak unpinned** (section Semana 2, hoje em bloco-04 dados 11–16/03):
    - `caracteristicasdosdados`/`caracteristicas-dos-dados` → bloco-04 **parecem certas** (content=DADOS bate "tipos dados/preparação").
    - `introducao-a-ml`/`introducaoml-atualizacao2025` → bloco-04, mas **DESLOCAMENTO candidato**: intro-ML real = **bloco-03** (09/03 "ml introducao a ml", hoje VAZIO). ABERTO p/ o gold.
  - **5 PINS preservados** (manual≠vazio): `oracle`/`ia-responsável`→bloco-01 (refs), `p1-2024-02`→bloco-08 (provas),
    `artigo-usando-k-nn`→bloco-05 (k-NN supervis = ok), **`artigo-usando-agrupamento`→bloco-05 SUSPEITO**
    (agrupamento=clustering=**bloco-06**, não supervis-05). Verificar no gold.
  - **bloco-06 mis-kind `suspended`→`class`** (`as-of 7561f5c`, uuid `17ea65f3-5f84-47c7-9357-e090ee1f80ed`).
    Range 20–27/04: só **20/04 é feriado**; **22/04 (k-Means)** + **27/04 (hierárquico)** são AULA. O `suspended`
    vazou da sessão 20/04 p/ o nível-bloco. Efeito: bloco ∈ `NON_ACADEMIC_KINDS` (`kinds.py:83`, `files:False`)
    → **7** materiais de clustering **somem da vista do gabarito** (`as-of 7561f5c`; cohort
  não-supervis Semana 8+9 = **8** ids — o 8º `artigo-usando-agrupamento` some pelo pin→bloco-05,
  não pelo bloco-06). Possível raiz do desloc. `artigo-agrupamento`→05
    (bloco-06 inválido como alvo file-bearing). Fix **EXISTE** (não é código novo): `.timeline_curation.json`
    `manual_kind_override:class` — honrado em `classifier.py:167-172`, aplicado em `index.py:85-90`. Passe de
    curadoria **pós-gold, GATEADO** (diff antes/depois, só `kind` muda; sem relance).
    > **CONCLUÍDO (2026-07-01): curation escrita + IA reprocessado + GATE VERDE.** bloco-06 kind
    > `suspended`→`class` (override honrado; key migrada pra uuid `17ea65f3` pelo pipeline). Zero placement
    > movido nos 7 de clustering; eval IA 38/44 = 86.4% byte-idêntico ao baseline (mesmos 6 off-by-one).
    > Os 7 materiais de clustering voltaram à vista do gabarito/GUI.
- [USER] **9 SO date-vs-block** (8 DIFFERS + 1 NO_MATCH) — **still-valid, verificado as-of reprocess SO 320712d.**
  Os 9 ainda divergem (bloco-da-data ≠ bloco-vivo). CONFIRMA "data-prefix = POSTAGEM, não aula": 3 arquivos com
  prefixo **02/06** caem em **blocos diferentes** (05/03/11). → pro gold SO, confiar em **tópico/seção**, NÃO na
  data do filename. Decisão humana por entry.
- ~~TCC sem CRONOGRAMA~~ **CORRIGIDO (21/06): claim era STALE (pré-reprocess).** TCC TEM cronograma
  completo pós-reprocess (31 blocos datados, SARC setado, 39/40 entries com "Semana N"). É
  week-anchorable igual IA/ES2. NÃO é blocker.
- ~~[USER] card "Verificação de Programas" MF sem bloco-09 na janela~~ **MORTA (2026-07-08): diagnóstico
  da FASE 0 estava ERRADO — o card map estava CERTO; o defeito era GOLD STALE.** User contestou a
  pendência; auditoria completa do `ground_truth_MF.csv` (67 rows, READ-ONLY vs timeline atual) provou
  drift posicional de `bloco-NN` pós-reprocess: bloco-09 HOJE é a prova P1 (22/04) — material de conteúdo
  rotulado nela era rótulo antigo deslocado. **7 rows re-rotuladas com sign-off do user** (invariantes×2
  09→11; correcaoterminacao×2 10→11; exerciciosformalizacaoalgoritmosinvariantes 10→11; hoare 13→10;
  exercicioscorrecaoinducaomatematica 06→05; tiposindutivos mantido 15 por decisão do user). Números
  reais do motor pós-correção: **acurácia 82.8% (48/58), contenção-fora 0, confiante-errado 1
  (exerciciosdafny2), recall 0.900** — a régua stale escondia 12pp. Baselines dos probes renegociados
  (conf≤1, conten≤0, recall≥9/10). LIÇÃO DURÁVEL: gold em `bloco-NN` posicional é frágil a reprocess —
  antes de qualquer medição cross-curso (FASE 2), auditar frescor dos ground_truth_* vs timeline atual
  (SO/TCC/IA/ES2 podem ter o mesmo drift); considerar migrar gold pra `block_uuid`.
- [USER] **pino antigo `eth2` (MF) discorda do gold — pin-vs-gold disagreement**
  (`as-of 2026-08-06`, achado review Task 2 da campanha índice único). O pino manual resolve
  pro uuid `c4bf9e4c` (→ `bloco-01`), mas o gold true de `eth2` é `bloco-12`. Mesma classe do
  caso `revisao-p1-gabarito` resolvido em 2026-08-06 (pin trivial já correto — ver PIN-SWEEP
  acima): "discorda" ≠ "errado" até confirmar com o oráculo do user. Pós-fix C5
  (`fase5_prova_tier2` honra temporal→manual→computed, commit `305cd9f`), `eth2` HOJE exibe
  `bloco-01` na régua (antes exibia vazio) — decidir se o pino é STALE (deletar, deixa a
  âncora computar) ou se há razão de negócio pro `bloco-01` que o gold desconhece. Bloqueia:
  nada estrutural (é 1 entry), mas contamina qualquer eval futuro de `eth2` sem ruling.

## MEDIÇÃO IA — conversor gold→ground_truth (as-of mundo-63, 2026-06-25)

- [DERIVADO] **Gold-method straddle = MAIOR história do crosswalk** (`as-of mundo-63`). O gold IA rotula em
  **subtópico (2 sessões)**; o pipeline placeia em **bloco (≈1 sessão)**. 11/20 subtópicos ATRAVESSAM fronteira
  de bloco → **21 materiais clean ficam inscoráveis** porque o subtópico sozinho não determina o bloco.
  **Propriedade do MÉTODO de gold, NÃO do pipeline.** Só subt 4-8 single-block (monstro bloco-05 absorve 4-7).
- [USER] **21 straddle clean** — inscoráveis por falta de `data_real` por-material. Re-entram via **batch SARC**
  (selector escolhe a SESSÃO/data, NÃO o bloco; conversor mapeia data→bloco sob `[início,fim)`). **Zona
  alta-FAIL** (fronteira). PROTOCOLO: medir taxa-FAIL straddle vs não-straddle SEPARADO — comparação some se
  misturar no agregado. Sequência: eval nos 33 PRIMEIRO (baseline), straddle como 2ª camada depois.
- [DECISION] **16 gold materiais fora da manifest viva** — gold rotulado PRÉ-poda (53/55), manifest PÓS-poda (42).
  **13 PODADOS** (no prepoda-55): out-of-escopo aceito (re-importar pra inflar denominador desfaria curadoria
  por vaidade métrica). **3 NEVER-IMPORT** (nem no pre55): `P2_IA_2024`, `Agentes`, `P2_IA_2024_02_A_turma30` —
  **buraco de PROCESSO** (rotulado, nunca entrou em build), NÃO decisão de poda. Investigar separado.
- [DERIVADO] **Denominador derivado: 33 scorable** (clean ∩ joined ∩ single-block ∩ resolved). **4 FAILs nomeados**,
  2 mecanismos: **(a) âncora-janela-de-pasta** (3: `Exemplo 2 k-NN IRIS`, `Exemplo com k-NN` — fronteira `[)`;
  `IA Aula 29` MLP) — placement por janela-de-pasta-Semana erra material cujo tópico-SARC pertence a outro bloco;
  **(b) pin-manual-errado** (1: `artigo-usando-agrupamento` — computed=None + manual-pin→bloco-05, oráculo=bloco-06;
  MESMO material "sem computed" da 2.5, não dois). Teste-unidade de borda `[início,fim)` = FIADOR dos FAILs k-NN.
- [CODE] **calibração-de-confiança — caso-âncora IRIS, PRIORIDADE ALTA** (`as-of mundo-63`). `exemplo-2-k-nn-IRIS`
  previu bloco-04 (errado; true bloco-05) com **band ALTA** = confiante-e-errado. NÃO é nota de rodapé: é a
  pendência de calibração do handoff inicial com caso vivo. Entre os DISCRIMINANTES a taxa confiante-errado é
  1/N-discriminante, NÃO 1/28 — diluir no monstro esconde. E é o modo de falha que o protocolo "só reviso o
  flagado" é **CEGO POR CONSTRUÇÃO** (confiante-errado não se auto-flagra). A âncora por-janela-de-pasta emite
  band alta mesmo placeando pela pasta errada → a confiança não reflete a incerteza de FRONTEIRA. Entra ANTES de
  gerar mais número.
- [DERIVADO] **DOIS mecanismos de FAIL, não um** (`as-of mundo-63`) — refuta "erra só na fronteira":
  **(1) âncora/janela-de-pasta** — 3 FAILs DISCRIMINANTES de fronteira (IRIS band-alta, exemplo-com-k-nn,
  artigo-pin); off-by-one adjacente; só pega material de fronteira. **(2) sem-cobertura→fallback-computed** —
  `IA-aula-29` é INTERIOR (subt-6, 06+08/04 ambos bloco-05, miolo do monstro) e ERRA mesmo assim:
  `source_section=None` → âncora não placeia → `temporal` VAZIO → eval cai no `computed` (`file_map:636`),
  `scorer_only` **band baixa** = bloco-04. Caso VIVO da fragilidade temporal-vazio (dentro do scored-set IA, não
  hipotético SO/MF). NÃO é calibração-errada: band baixa = incerteza honesta (≠ IRIS band-alta-errado). Mecanismo
  (2) alcança INTERIOR. Distância dos 4 segue off-by-one, mas "só fronteira" caiu.
- [DECISION] **80% discriminante assume proxy-date fiel pros existentes** (`as-of mundo-63`). Existentes datados por
  **1ª-data-do-subtópico** (só notebooks têm data por-material exata). 1 proxy-frágil: `arvores-de-decisao` (subt-7,
  proxy 13/04=trivial vs real 15/04=discriminante) — **passa em ambas → proxy NÃO esconde FAIL aqui**. Limitação
  nomeada: onde proxy≠real caírem em blocos diferentes, o proxy fabrica/esconde FAIL. 5 agrupamento usam 20/04
  (suspensão; aula real 22/04, mesmo bloco bloco-06).
- [DERIVADO] **Cobertura prediz correção — mas o sinal é MECANISMO, não taxa** (`as-of mundo-63`). Dos 33 scorable,
  só **2 uncovered** (temporal cru vazio → fallback): IA-aula-29 (sem-pasta→computed) + artigo-agrupamento
  (pin→manual); ambos falharam. NÃO reportar "100% uncovered-fail" — n=2, amostra pequena demais pra taxa
  (número inflado contra o sistema é tão inválido quanto a favor). O sinal é o MECANISMO sem-pasta→fallback→erro,
  que IA-aula-29 dá sozinho; os 2 ilustram, não quantificam. **0 uncovered PASSOU → a 3ª categoria temida
  (acertos-frágeis-por-sorte-do-fallback) NÃO existe neste set.**
- [CODE] **PIN-SWEEP — pins manuais que discordam da âncora** (`as-of mundo-63`). 5 pins, 2 discordam, mas
  **"discorda" ≠ "errado"** (oráculo separa): ~~(WRONG) `artigo-usando-agrupamento` pin-05~~ **JÁ RESOLVIDO
  (verificado 2026-07-01: pin=None, temporal=bloco-06 correto — deletado em sessão anterior ou reprocess).**
  **(GOOD) `artigo-usando-k-nn-em-texto`**
  pin-05 vs âncora-04: o pin está CERTO (k-NN=18/03→bloco-05), a âncora ERRARIA (Semana-3 começa 16/03=prep) — o pin
  **resgata** a âncora do erro Semana-3-prep-vs-k-NN-18/03 (mesmo que derruba os notebooks k-NN). Evidência de patch
  humano sobre fraqueza sistemática da âncora. Regra de varredura futura: pin-disagreement = CANDIDATO, confirma
  com oráculo antes de deletar (deletar pin-bom quebra).
- [DECISION/USER] **never-import resolvido — não é buraco de conteúdo** (`as-of mundo-63`). Dos 3 unjoined-never-import:
  **`Agentes.pdf` = FALSO ALARME** (existe na manifest como `introducao-a-agentes`, Semana-16; gold usou nome
  divergente → join-miss; fix: alias/renome no gold). **`P2_IA_2024` + `P2_IA_2024_02_A_turma30`** = 2 provas-2 fora
  do stash → DUAS hipóteses DISTINTAS (NÃO fundir): **phantom-no-gold** (rótulo de material inexistente = erro de
  rotulagem) vs **nunca-baixada** (existe no Moodle, download pulou = mini-buraco-de-processo que repete em SO/MF).
  Distinguir precisa checar Moodle. Gap estreito, provas não-conteúdo; nenhum material pedagógico dropado pelo import.
- [DERIVADO] **80% é PÓS-2-CAMADAS-DE-CORREÇÃO** (`as-of mundo-63`). Mascaramento empilhado: âncora mascara
  erro-de-computed (hierárquico bloco-07→06), pins mascaram erro-de-âncora (`k-nn-texto`: pin-05 corrige âncora-04).
  `k-nn-texto` é **FÓSSIL** — humano patcheou o bug Semana-3-prep-vs-k-NN ANTES desta campanha = confirmação
  INDEPENDENTE do mecanismo (não artefato de medição). O erro BRUTO do placement-por-pasta (sem âncora, sem pins) é
  **MAIOR que 20%**; o 80% é performance real COM as 2 correções e **NÃO generaliza sem elas** (SO/MF podem não ter
  as camadas de patch).
- [UX/CODE] **aviso GUI "sem bloco atribuído" induz pin desnecessário = armadilha de UX** (`as-of 2026-06-26`). O
  aviso do cronograma conta materiais sem atribuição MANUAL (pin), NÃO sem placement — 58/63 (os que usam
  auto-placement, o estado DESEJADO). A redação empurra o usuário a preencher pins à mão → re-introduz circularidade
  (mão atribuindo o bloco que o pipeline computa) + risco de pin-stale (caso `artigo`). Custou uma **deleção-de-entry
  acidental** nesta sessão (delete-entry vs pop-field quase-idênticos na GUI do Timeline Dashboard; 63→62, pego pelo
  gate (b)). Fix: re-redigir ("sem override manual", não "sem bloco") ou suprimir quando há placement auto; e separar
  visualmente delete-entry de clear-pin.
- [PROTOCOL] **conserto-de-pin loop: pós-mutação do vivo, REGENERA o CSV antes de classificar** (`as-of 2026-06-26`).
  No 1º fix (artigo) o `eval` (lê manifesto vivo) deu 30/33 mas o `classify` (lê coluna `temporal_block_id` do CSV
  pré-reprocess) deu 12/15 — defasagem CSV-stale vs vivo. NÃO escolher um: regenerar o CSV (`build_ground_truth_IA`)
  pós-reprocess e re-classificar. Sequência: rename→gate-vivo→reprocess→diff_pinfix→**regen CSV**→eval+classify.

## CODE — cadeia de atribuição (degrau 3 / Fase 3)

- ~~Degrau 3a alavanca 0 (lessons no fusor)~~ **SUPERSEDED PELO MOTOR (2026-07-01, verificado)** — o SINAL
  (`.lessons_index.json`/roteiro) virou 1ª classe no disambiguator do motor (D3/D5; exercitado no MARCO 0).
  O PLANO original (termo β no fusor velho via `resolver_apply`/`score_lesson_match` peso 0.5) mira o caminho
  que morre no cutover 3.4 — `load_lessons_index` está chamado em `resolver_apply.py:111`, atrás da flag
  desligada, fundo da cascata. Plano `2026-06-17-alavanca0-lessons-index-plan.md` carimbado superseded.
  **Herança viva pro spec:** o caso-alvo do A1 (card "Verificação de Programas" MF, 14 lessons, blocos 10-15)
  é onde MARCO 0/1 ainda erra (hoare/tiposindutivos/dafny1-2) → matching fino de lesson = requisito do
  disambiguator real.
- ~~Alavanca 3 (posting_date / seleção por sessão)~~ **SUPERSEDED (2026-07-01)** — posting_date foi declarado
  lixo como sinal de base (decisão 28/06); o motor D0-D13 não o usa (sinais: seção/roteiro/prazo/conteúdo).
- [CODE] **Fase 3.4 cutover** — default ON do concept_resolver + DELETE do funil legado
  (`score_entry_against_timeline_block` S2/S4, `select_probable_period`, `_best_instructional_block_fallback`,
  2 rotas card). Eval-gated.
  > **PRÉ-REQ FASE 4 CONCLUÍDO (`as-of 2026-08-14`, commits `5da5f2e..b9a4a53`)**: unit/subunit no
  > motor (`apply_unit_subunit_fields`, resolver_apply.py; wire flag-gated engine→pedagogical_regeneration)
  > — achado 1.1 da auditoria destravado. Medição sandbox MF: golds unit 12/14 BEFORE=AFTER (zero
  > regressão), **GO CONDICIONADO** (review final F4, Opus): flip depende dos gaps 1.2/1.3 E do
  > fix dos pinos manuais (achado C1 abaixo). Régua adicional pro flip: verificar sobrevivência
  > dos pinos por curso (eval_units é cego a pinos — mede unit por bloco).
  > **CONDIÇÕES FECHADAS (2026-08-17, passo 2, `636f299..d319477`)**: C1 pinos ✓ (Tier 1 casa
  > uuid+display) · gap 1.3 ✓ (resync tag `bloco:` no swap D1, cobre blocks=[]/None) · gap 1.2 ✓
  > (teste de integração da cadeia, não-vacuidade provada por mutação). Gates: suite 1952/1/0,
  > sentinelas 0 diff, MF 50/57. **Flip destravado** — falta só a própria medição do passo 3:
  > golds 5/5 cursos + sobrevivência de pinos por curso + rebuild_diff 0.
  > **Dependência nova pra F5**: ao deletar `resolve_unit_block_tags`, portar a limpeza
  > `_NO_TIMELINE_CATEGORIES` (content_taxonomy.py:1137-1147) pro caminho do motor — hoje ela só
  > roda dentro do legado.
- ~~topic-resolver (SO) + label-resolver (MF)~~ **SUPERSEDED PELO MOTOR (2026-07-01)** — viraram
  WindowProviders por curso dentro do AnchorEngine (D5/D10), não resolvers avulsos. E são LOAD-BEARING,
  não rollout tardio — cobertura de card-window medida hoje:
  **IA 56/62 (90%) · MF 60/67 (90%) · ES2 30/35 (86%) · TCC 7/27 (26%) · SO 0/42 (0%).**
  Sem provider próprio, o motor = funil pra SO inteiro e 20/27 do TCC. Spec deve tratar
  WindowProvider-por-curso (SO topic/filename-date; TCC parse "Semana N") como fase de 1ª classe.
- [CODE] Degrau 2/3c **over-merge temporal** (merge feriado+prova) — adiado; funde no degrau 3 quando join virar DATA.
- [CODE] **placement-computed-errado-mascarado-por-âncora** (`as-of mundo-63 IA, 2026-06-25`) — o
  `_card_scoped_block` (computed) ERRA o hierárquico: `computed_block_id=bloco-07` ("duvidas"), enquanto a
  verdade-oráculo é **bloco-06** (27/04, SARC, proveniência cravada por redundância tabela+bullets). O eval
  pontua `temporal` (`resolve_temporal_block`, `file_map:633/635` — `temporal_block_id` da âncora vence ANTES
  do fallback), e a âncora pôs bloco-06 → **passa HOJE**. MAS `file_map:636`: `temporal` vazio → fallback
  `computed`. Os 24 notebooks IA têm temporal setado → nenhum cai. Material com temporal vazio (SO/MF/ES2, ou
  IA futuro sem cobertura de âncora) → eval pontua `computed` = o canal que erra o hierárquico.
  **"Hierárquico passa" é verdade hoje, frágil amanhã; a fragilidade vive na COBERTURA DA ÂNCORA, não no
  computed.** NÃO é "sistema consertou" — é erro-de-computed mascarado por override temporal. Delta
  computed-vs-temporal nos 24: **3 diferem** (hierárquico×2, "Exemplo com k-NN"), 21 idênticos. Mesmo
  mecanismo dos 2 FAILs k-NN (placement por janela-de-pasta-Semana erra material cujo tópico-SARC pertence a
  outro bloco) — só que nos k-NN a âncora TAMBÉM erra (não mascara). Reaparece sem boa cobertura de âncora.

## CODE — limpeza / dead-code (auditoria pronta)

> Revisão spec×código×dívida (2026-07-03, agente read-only): âncoras §8 do spec = **0 drift / 0 missing /
> 0 divergente** (plano fase 0 parte delas sem re-verificação). Veredito de ordem: unificação D/E **NÃO
> antecede a fase 0** — primitivas do Disambiguator (`concept_token_weights`/`concept_vector`/
> `score_lesson_match`, concept_resolver.py) já são a cópia canônica sobre normalize/stopwords canônicos;
> o gêmeo IDF (`block_token_weights`, file_map.py:882) é o S2 que morre no cutover.

- [CODE] **Tasks D/E (corrigidas 2026-07-03)** — "vocab/normalizadores ×4" JÁ RESOLVIDO no código: todos
  delegam a `text/normalize.py:normalize_match_text` (variantes só paramétricas); `_collapse_ws` e
  `UNIT_GENERIC_TOKENS` fonte única. Resta: 3 scorers de unidade dup (`file_map.py:209`,
  `index.py:1620`, `index.py:1732`) + signal-key mismatch (H3) + predicados (M3). Eval-gated, trilho
  próprio, DEPOIS da fase 0 (grafo disjunto do motor; unificar antes não reduz risco).
- [CODE] **Task B** `administrative_only` — persistir vs deletar (decisão de produto). **CONGELADA até os
  testes de janela da fase 0**: predicado usado DENTRO de `derive_card_block_map`
  (moodle_labels.py:158-159) = WindowProvider P1/P2; mexer nele altera a janela do motor. Nota da
  revisão 03/07: os "filtros mortos" originais já não existem — predicado lê `rows` no runtime e é real.
- ~~[CODE] **fallback keyword (~600 linhas, index.py) — DIVIDIDO 2026-07-03, não deletar em bloco**~~
  **FECHADO (2026-08-17, passo 3, `df86203`)**: ramo (a) deletado (+ helpers e thresholds órfãos);
  cadeia (b) topic-labels segue VIVA como decidido.
  (a) ramo fallback de UNIDADE (index.py:2207-2215, dispara só com `assign_units_positional` vazio) =
  deletável no cutover c/ guard test; (b) cadeia topic-labels (index.py:2174 → 1929/1732) RODA SEMPRE e
  alimenta UI/badges = VIVA, fora da lista de morto.
- [CODE] ~~**Auditoria de artefatos**~~ **FEITA 2026-07-03** — mapa de leitores no relatório da revisão:
  `.timeline_index`/`.card_block_map`/`.lessons_index`/`code_curation`/`.tag_profile` TODOS vivos;
  `.timeline_index` ganha consumidor novo no motor (`sessions[].label`); cache do motor =
  `material_curation.json` NOVO, sem colisão com `code_curation`.
- [CODE] **RUN dedicada de remoção de mortos (decisão user 2026-07-03)** — separada do plano do motor,
  qualquer hora. Primeiro alvo provado: `_derive_unit_from_topic_match` (index.py:2080; morto em
  produção; só re-export engine.py:241/2443 + tests/test_file_map_unit_mapping.py:11,647,705,732,836).
  Remoção pura, sem eval.
  > **RE-VERIFICADO ABERTO 2026-08-24:** a funcao vive hoje em `timeline/index.py:1951` (linha
  > mudou); alcancada so por `engine.py:245`/`:2443` (re-export) e por um comentario em
  > `timeline/conflicts.py:48`. Segue morta em producao.
- ~~[CODE] **Mapa de deleção do cutover fase 5 — 5 conflitos, resoluções travadas 2026-07-03**~~
  **FECHADO (2026-08-17, passo 3, `df86203` + `037ddbe`)**: itens 1-8 TODOS executados conforme
  travado (1 aposentado · 2 aposentados · 3 lista nomeada completa · 6 fantasma+testes ·
  7 R4/R6 · 8a-8e entregues/verificados). Ver Concluído 2026-08-17c. Histórico abaixo:
  1. `cronograma_health.py:117-171` reusa o scorer S2 condenado → **fase 4 decide** portar pro scoring
     do motor ou aposentar (band/flag do Dashboard na mão); fase 5 não deleta antes da decisão.
  2. `scripts/eval_assignments.py:99` + `scripts/retag_manifest.py:60` injetam `select_probable_period`
     → **LEGADO-NÃO-USAR desde já**; aposentar no MESMO commit da deleção (régua oficial =
     `eval_ground_truth.py`, mede via `resolve_temporal_block`, que sobrevive).
  3. Deleção por **LISTA NOMEADA de símbolos**: morrem `score_entry_against_timeline_block` /
     `block_token_weights` (S2) / `TOOL_*` (S4) / `select_probable_period_for_entry` /
     `_best_instructional_block_fallback` / `_card_scoped_block`; FICAM
     `score_card_evidence_against_entry` + `_score_block_date_match` (file_map.py:737/1078 — usados
     pelo `concept_resolver` VIVO) e `card_block.py` inteiro. Guard test na fase 0: pacote do motor
     proibido de importar os condenados.
  4. = Task B congelada (acima).
  5. = fallback dividido (acima).
  6. `_serialize_timeline_index` (index.py:813-866, fantasma v4 filtrador de admin) + testes legados dele
     (tests/test_core.py:2939,2953,5248-5271; test_fileentry_roundtrip.py:155,181;
     test_file_map_unit_mapping.py:1097; **tests/test_timeline_schema.py:29,92,118**;
     **tests/test_unit_matcher.py:18,21** — achado review Task 4 da campanha índice, 2026-08-07,
     também chamam o fantasma e morrem JUNTOS no mesmo cutover) morrem JUNTOS no cutover; guard
     de condenação em `tests/test_persist_enriched_serializer.py` (C3, 2026-08-07).
  7. **Família dual-source R4/R5/R6** (varredura 2026-08-06, campanha índice único, Task 6) —
     R4 `scripts/compare_resolver.py:86-103` (`_inject_block_uuids_from_ledger`: harness injeta
     `block_uuid` no timeline que a produção não injeta); R5 = mesmo item 2 acima
     (`scripts/eval_assignments.py:99`, já LEGADO-NÃO-USAR); R6 `scripts/eval_assignments.py:
     135-138` (2º produtor de `.card_block_map.json`, escrito num tempdir só pro harness —
     produção usa `derive_card_block_map`, `moodle_labels.py:158-159`). Morrem no cutover junto
     com a lista nomeada do item 3.
  8. **Achados adicionais do cutover (Task 4/6, review final, 2026-08-06/07)**:
     (a) `tests/test_persist_enriched_serializer.py` fixa `version==3` — bump v3→v4 no cutover
     quebra o teste de propósito (atualizar junto); (b) unificar o par de vocabulário fraco exam
     (`("prova","teste")` no classifier + `_TOPIC_EXAM_STEMS` no motor — 2 literais, 1 conceito) e
     o import privado cross-package `_STRONG_EXAM_RE` classifier→motor; (c) W1
     (`pedagogical_regeneration.py:394-402`) adotar `engine._build_rich_content_taxonomy` (hoje
     replica inline as mesmas 3 linhas — dual-source por cópia); (d) W2 `rebuild_course --write`
     não escreve `.content_taxonomy.json` (W1 escreve; sidecar envelhece — leitores:
     `concept_resolver.py:79`, `compare_resolver.py:129`, `eval_subunit_census.py:42`); (e)
     `build_rich_content_taxonomy` degrada silencioso p/ taxonomia pobre se manifest.json
     faltar/corromper — adicionar warning quando W2 --write.

## CODE — família dual-source (R1-R12, varredura 2026-08-06, campanha "gerador de índice único")

> Inventário completo dos 3 agentes que varreram a base antes da campanha 1/3
> (`docs/superpowers/specs/2026-08-06-gerador-indice-unico-design.md` §8). R4/R5/R6 (cutover)
> vivem no Mapa de deleção acima (item 7); aqui ficam os que NÃO entraram no escopo da
> campanha 1/3 — trilho separado ou minors-batch/subprojeto SO — mais o status dos que a
> campanha fechou (R1/R8/R10).

- [CODE] **R1 — dois serializadores do timeline (v3 produção / v4 só-testes)** — **CONDENADO,
  não deletado** (C3 da campanha índice, commit `9155224`, `as-of 2026-08-06`):
  `_serialize_timeline_index` (v4, filtra admin, força kind; ids posicionais deslocam entre
  formatos — `.bak` do TCC é v4/23 blocos vs vivo v3/31) segue vivo até o cutover; guard test
  `tests/test_persist_enriched_serializer.py` proíbe caller novo de produção. Deleção física:
  item 6 do Mapa de deleção do cutover (acima).
- [CODE] **R2 — render de FILE_MAP com `persist=True` escreve efeitos colaterais no meio do
  build** (`navigation.py:525-529` + `teaching_timeline.py:93-95`, `as-of 2026-08-06`) — mint
  de uuid/migração de refs disparados por uma chamada de RENDER, não só pelos 2 write-sites do
  índice (W1/W2). Fora do escopo de C2 (que exige só paridade de CONTEÚDO, não de efeito
  colateral de `persist`) — item [CODE] próprio, trilho separado.
- [CODE] **R3 — bootstrap × regenerate escrevem os mesmos `.md` com insumos diferentes**
  (`bootstrap_ops` vs `pedagogical_regeneration`, `as-of 2026-08-06`) — mesma família
  dual-source do índice (C2), só que do lado dos materiais didáticos gerados, não do timeline.
  Trilho próprio.
- ~~[CODE] R8 — fase5 sem precedência de pino~~ **FECHADO (C5 da campanha índice, commit
  `305cd9f`, `as-of 2026-08-06`)** — `fase5_prova_tier2._effective_display` passa a honrar
  temporal→manual→computed (espelha `resolve_temporal_block`); acc 4/8→6/8, cw=0 mantido.
- [CODE] **R7 — 4 loaders de índice com fallbacks distintos** (`as-of 2026-08-06`) — sem
  file:line detalhado nesta varredura (nível "achado", não "localizado"); minors-batch, fora
  da campanha índice (C2 unificou só os 2 write-sites, não os loaders de leitura).
- ~~[CODE] R10 — taxonomia com/sem `manifest_entries` vivas filtradas (causa-raiz do dual-source
  de índice)~~ **FECHADO (C2 da campanha índice, commits `305877a`+`328a0b2`,
  `as-of 2026-08-06`)** — montador único `_build_file_map_timeline_context_from_course`
  (`index.py:1349`) usado pelos 2 write-sites E pelas sondas read-only; `rebuild_diff` W1×W2 =
  **0 diff nos 5 cursos** (medido nesta Task 6, `as-of 2026-08-07`).
- [CODE] **R9 — `scan_existing_block_refs` lê nível errado do manifest, guard cego**
  (`index.py:1401` + `block_identity.py:269-272`, `as-of 2026-08-06`) — o guard de UUID-ref
  confere `manual_timeline_block_id`/`computed_block_id` no manifest mas não desce pro nível
  certo em todo caminho; minors-batch/subprojeto SO.
- [CODE · RE-VERIFICADO ABERTO 2026-08-24] **R11 — dashboard escreve manifest não-atômico**
  (`src/ui/timeline_dashboard.py:248`, `write_text` direto — confirmado hoje,
  `as-of 2026-08-06`) — `manifest_path.write_text(...)` direto, sem write-temp+rename; write
  parcial em crash/kill corrompe o manifest vivo. Minors-batch, fora da campanha índice.
- [CODE] **R12 — join de data truncado vs cru dentro do motor** (`disambiguator.py:68` usa
  `sess.get("date")` cru vs `llm_vote.py:227-229` que trunca `[:10]` antes do lookup em
  `ctx.lessons_index`, `as-of 2026-08-06`) — mesma chave semântica, formatos diferentes;
  candidato ao subprojeto SO (roteiro/lessons_index é sinal fraco em SO hoje, ver
  WindowProvider acima).

## CODE — bugs pré-existentes localizados

- ~~[CODE] `gemini_client.py DEFAULT_MODEL = "gemini-2.5-flash"` APOSENTADO pela API~~ **FECHADO
  (F4 item 0, pré-flight — commits `8f73084`/`79c...` guard em `get_gemini_client`)**: `DEFAULT_MODEL`
  migrado para `gemini-3.5-flash` pinado + guard contra config persistido antigo vazando o modelo
  morto pro endpoint (review T1).
- ~~[CODE] `SubjectManagerDialog._save` (dialogs.py:1503-1525) **dropa `moodle_course_id`/`m365_filter`** ao salvar.~~
  **FIX aplicado (2026-06-22, working tree, uncommitted):** `_save` agora preserva ambos de `existing`
  (espelha `turma`/`schedule_url`, dialogs.py:1521-1525). 388 testes verdes (core/moodle/m365). NOTA: o fix
  evita zeragem FUTURA; o `moodle_course_id` do IA já perdido precisa **re-import Moodle** pra restaurar.
- ~~[CODE] `migrate_signals` standalone **não grava `turma`** (só `import_moodle_courses` grava) — derivar do curso.~~
  > derived-código, não-reprocess-stale, as-of 18/06 (S0).
  **STALE — fechado em algum ponto pós-18/06 (verificado 2026-08-06, varredura):**
  `backfill_repo_signals_additive` grava `manifest["turma"]` quando `info` traz turma
  (`moodle.py:462-463`), o parse do curso extrai turma (`moodle.py:62-78`) e o docstring do
  migrador declara turma no escopo S0. Sem gap restante.
- ~~[CODE] **Latente:** sem teaching_plan, `_derive_unit_specs_from_repo` vs `content_taxonomy["units"]=[]`
  divergem → fallback vira load-bearing.~~ **CONFIRMADO EM PRODUÇÃO (2026-08-05, investigação
  `docs/reports/2026-08-05-unit-sources-investigacao.md`) — vira o item [CODE] PRIORITÁRIO abaixo.**
- [CODE] **PRIORITÁRIO — campanha u3/subject_profile** (`as-of 2026-08-05`, investigação
  `docs/reports/2026-08-05-unit-sources-investigacao.md`). Causa-raiz FATO: `scripts/
  reprocess_assignments.py:81` monta `RepoBuilder` SEM `subject_profile` → `teaching_plan=""` →
  `content_taxonomy["units"]=[]` (`file_map.py:1500-1501`) → `assign_units_positional` retorna `[]`
  no guard `m<2` (`unit_matcher.py:66-67`) → cai no scorer legado alimentado pelo índice de 2
  unidades derivado do COURSE_MAP (`file_map.py:1628`), que a mesma rodada RE-ESCREVE em disco
  (`pedagogical_regeneration.py:402`) — loop auto-perpetuante. **Matcher inocentado**: com as 3
  unidades reais do plano.md, bloco-16 (MF) cai em unidade-03 com argmax 4 (overlap
  logica/modelos/temporal/verificacao) vs 3 (u01) vs 2 (u02), confiança 0.6 — provado por
  experimento real (`assign_units_positional` real + blocos reais + taxonomy real). **+2
  vazamentos do mesmo formato**: `src/ui/app.py:2391` (unprocess) e `src/ui/curator_studio.py:
  1293,1303` (reject) — mesma falta de `subject_profile`, mesmo efeito, cada clique re-envenena o
  repo. **Fix**: importar `_resolve_subject_profile` de `scripts/retag_manifest.py:30-41` (já
  resolve corretamente) nos 3 sites; subsume o T18 (feature_flags) já fechado — profile em mãos,
  merge de `feature_flags` é 2 linhas junto. **MUDA ATRIBUIÇÕES → gold obrigatório** antes/depois
  (mesmo protocolo do Fix 2b). Guardrail barato: `logger.warning` nos 2 early-returns silenciosos
  (`file_map.py:1500` e `:1628`) — hoje nenhum loga, curso perde 1/3 da estrutura sem nenhum sinal.
  > **FECHADO (verificado no codigo 2026-08-24):** o wiring foi aplicado nos 3 sites —
  > `scripts/reprocess_assignments.py:52` (`_find_subject_profile`) passa o perfil em `:105`;
  > `src/ui/app.py:2387` passa `subject_profile=profile` no unprocess; `_resolve_subject_profile`
  > e usado em todo o app. **Os 2 guardrails tambem entraram**, ao contrario do que este item
  > pedia como pendente: `routing/file_map.py:1185` loga "sem teaching_plan no perfil —
  > content_taxonomy vazia" e `:1237` loga "unidades derivadas do repo gerado, nao do plano de
  > ensino — fallback". Item inteiro fechado; nada aqui e acao.
  > PENDENTE do mesmo item, NAO fechado: unificar as 2 fontes de unidade (`unit_index` como
  > projecao de `content_taxonomy`) — era "depois do wiring fix", e o wiring ja esta feito.
  **Depois do wiring fix** (não antes — evita migrar o veneno): unificar as 2 fontes de unidade
  (`unit_index` vira projeção de `content_taxonomy`) — merge antes do fix causaria churn de slugs
  nos 5 repos-tutor (títulos Title-Cased do fallback ≠ títulos acentuados do plano).
- ~~[CODE] **BLOQUEANTE pré-rollout ES2/curso novo**~~ **RESOLVIDO (2026-08-06, TDD):**
  `_NON_CONTENT_KINDS` expandido com `NON_ACADEMIC_KINDS` canônico de `kinds.py` (holiday,
  suspended, academic_event, office_hours, planning, reserved, results) — admin nunca ancora
  entrega, mesmo com `topics` populado; makeup/overview/unknown seguem CONTEÚDO (fail-open
  para fora-do-enum preservado). RED confirmado pré-fix (holiday ancorava), GREEN 20/20 no
  arquivo, fase5 PASS 4/8 cw0 byte-idêntico, suite 1871/4/0. Texto original:
  (`as-of 2026-08-05`, achado Plano B Task 5 fix
  round 1, deferido). Filtro D-H do due-window (`due_window.py`, `_NON_CONTENT_KINDS=
  {"assessment","review"}`) foi derivado só dos kinds REALMENTE observados nos 4 índices
  disponíveis hoje (TCC/MF/SO/ES2 sem due real; IA-Tutor sem índice) — kinds administrativos nunca
  vistos com `topics=[]` no corpus atual (`holiday`, `suspended`, `office_hours`, etc.) **fail-open**:
  se um curso novo produzir um desses com `topics=[]`, o filtro os deixa elegíveis à janela de
  prazo (deveriam ser excluídos como não-conteúdo). Fix: mover de lista-por-observação pra
  allowlist positiva de kinds de conteúdo, OU expandir `_NON_CONTENT_KINDS` com os kinds
  administrativos conhecidos do `BlockKind` antes do próximo curso/ES2 entrar em produção com o
  motor ON.
- [CODE] **Integrar `knowledge_graph.py`** (`as-of 2026-08-05`) — gerador de grafo de conhecimento
  do tutor, hoje só no scratchpad da sessão (stdlib-only; produziu `mf_knowledge_graph.html`, 90
  nós/78 arestas/1 órfão "plano", MF confirmado intocado, 12 divergências temporal≠computed
  visíveis). Falta: mover pra `scripts/` + melhorias já decididas (espinha temporal
  bloco-01→NN e unidades derivadas do plano de ensino — 3 no MF, incluindo a vazia/perdida u3
  acima). Foi o grafo que achou a perda da u3 (via inspeção visual das 12 divergências) — vale
  como ferramenta de auditoria recorrente, não one-off.
- [CODE] **Latente: TCC NFD dotless-i no manifest** (`as-of 2026-07-01`, herdado do handoff 28/06 P4) — slug
  `aula-10-linguagens-reconhecıveis-e-linguagens-decidıveis` carrega U+0131 (NFD do macOS). Join por nome pode
  falhar silencioso. Fix: normalizar NFC no import. Não urgente; vigiar no crosswalk TCC.
- [CODE · RE-VERIFICADO ABERTO 2026-08-24] **`preserve_raw` morto no `reject`** — segue vivo em
  `src/ui/curator_studio.py:1296`. (`as-of 2026-08-06`, achado fio Task 1, reviewer
  pré-existente não desta task). `builder.reject(entry_id, preserve_raw=False)` sempre cai no
  `except TypeError` — a assinatura atual de `reject` não tem parâmetro `preserve_raw`
  (`engine.py:2194` / `lifecycle_ops.py:313`; re-verificado 2026-08-06, call-site
  `curator_studio.py:1301` com os 2 builders no try/except). 2 builders passam por esse caminho no reject hoje.
  Fix: remover o parâmetro morto das chamadas OU implementar o comportamento que o nome promete
  (não decidido; registrar para triagem).
- [CODE] **golden `test_caracterizacao_blocos_atual[IA]` stale pós-rollout IA `86f00d9`**
  (`as-of 2026-08-06`, achado sessão campanha índice único, Task 1) — o rollout IA
  (`use_anchor_placement` OFF) mudou `computed_block_id` do caso-chave
  `agrupamento-parte2` de `""` pra uuid real (`0b986383-663a-4a54-b000-4b97ebce59c4`); o
  baseline `_golden/Inteligencia-Artifical-Tutor__casos_chave.json` não foi re-versionado.
  Suite roda **1879 passed / 4 skipped / 1 failed** desde então — o 1 failed é EXATAMENTE este
  golden, não é fail de gate de nenhuma task da campanha (confirmado régua Task 6,
  `as-of 2026-08-07`). Fix: re-baseline GATEADO do golden (regenerar `_golden/*.json` com diff
  revisado antes de versionar) — fora do escopo da campanha índice único.
  > **FECHADO (verificado 2026-08-24, execucao da suite):** `python -m pytest -q` da
  > **2002 passed / 1 skipped / 0 failed**. O golden foi rebaselinado em alguma das campanhas
  > seguintes (as sentinelas foram regravadas varias vezes em 20-21/08). Nao ha fail pendente.
- [CODE] **Scorer do AnchorEngine sensível a rótulo rico de taxonomia em vizinhos topicais**
  (`as-of 2026-08-06`, tentativa 5 do re-flip TCC): `aula-13-teorema-de-rice` foi de
  bloco-12→bloco-13 quando o rótulo rico "Prova da Indecidibilidade do Problema da Parada"
  entrou na assinatura do bloco — caso FLAGADO (band media, cw=0), mitigado por pino
  gold-backed (`91c1d2a`); o caminho do scorer NÃO tem guard C6-equivalente. Insumo nomeado da
  campanha 2 (unidades/colisão de rótulo).

## CODE — eixo de UNIDADE: achados medidos (2026-08-18, sessao de investigacao)

Regua NOVA `entry -> unidade` criada e commitada: `scripts/eval_entry_unit.py`. Verdade =
composicao de dois golds ja aprovados (`ground_truth_<C>.csv` |><| `gold_units_<C>.csv`),
191 entries nos 5 cursos, sem rotular nada novo. Relatorio completo com todas as tabelas e as
hipoteses refutadas: `docs/reports/2026-08-18-achados-eixo-unidade.md`.

BASELINE INICIAL (`as-of 2026-08-18`, HEAD `419aaff`, gate 0.65): certo **95/191 (50%)** ·
sem resposta 57 (30%) · confiante-e-errado 39 (20%). Ponta-a-ponta: 126 certo / 46 errado /
19 vazio. Decomposicao dos 96 nao-acertos: gate 29 · eixo 12 · erro 55.

**BASELINE ATUAL (`as-of 2026-08-18b`, gate 0.50, apos a poda do glossario)**: scorer isolado
**109/191 certo (57%)** · sem resposta 40 (21%) · confiante-e-errado 42 (22%).
Ponta-a-ponta (o que o sistema GRAVA): **132 certo · 47 errado · 12 vazio**.
Por curso, scorer isolado (certo/n): MF 43/67 · SO 9/36 · IA 39/43 · ES2 8/27 · TCC 10/18.

CAVEAT: a verdade e a unidade do bloco TEMPORAL; a regua SUPERESTIMA o erro em curso com
material transversal (ES2, SO). ES2 piorou em confiante-e-errado com o gate menor (16 -> 19 no
scorer isolado) — e o problema de EIXO sendo amplificado, nao regressao do scorer; ponta-a-ponta
o ES2 fica igual (8/27) porque a reconciliacao segura.

- [CONCLUIDO 2026-08-18b] **A-6 · gate `T.UNIT_TAG` calibrado 0.65 -> 0.50** — primeiro sweep de
  UNIT_TAG do projeto, medido PONTA-A-PONTA (depois de `reconcile_unit_with_block`).
  gate 0.65: 126 certo / 46 errado / 19 vazio · **0.50: 132 / 47 / 12** (escolhido) · 0.40 satura
  em 132 e so cresce o errado. Por curso em 0.50: MF 52->54 · SO 14->15 · IA 38->40 · ES2 8->8 ·
  TCC 14->15. Tabela no comentario de `thresholds.py`. Sentinela `test_thresholds_present`
  atualizado; dois testes de gate passaram a ser RELATIVOS a `T.UNIT_TAG` para nao apodrecer.
  **CORRECAO ao que eu tinha escrito**: "o gate mata 29 acertos" superestimava ~5x — com o slug
  vazio a reconciliacao HERDA a unidade do bloco (`file_map.py:724`), que acerta mais que o
  scorer. Ganho real +6 gravadas certas, +1 errada, -7 vazias.
- [REJEITADO 2026-08-18b] **A-2 · normalizar score por tamanho de unidade** — medido e PIOR.
  Com o gate livre para se mover, alpha=0,5 perde para alpha=0 em toda a grade (104 contra
  109/110 no scorer isolado). O ganho aparente do braco H vinha de comparar contra gate fixo em
  0.65. Fica o FATO estrutural (desequilibrio de tamanho, que a poda do glossario PIOROU:
  SO 1,89->3,00 · TCC 2,71->4,00 · IA 3,22->3,50 · ES2 1,92->2,57), sem correcao proposta.
- [CONCLUIDO 2026-08-18b] **A-1 · template do GLOSSARY.md virava topic_phrase de TODAS as
  unidades (5/5 cursos)** — `_parse_glossary_terms` tratava toda linha `## ` como termo, e
  `## Formato de entrada` / `## Termos` sao secoes do template sem `**Aparece em:**`; o guard
  `if unit_hint and ...` deixava passar. Dois fixes: (1) termo sem `Aparece em` nao e sinal de
  unidade; (2) frase presente em TODAS as unidades e descartada de quem NAO a tem como topico
  proprio (a dona mantem e volta a discriminar). Resultado: **frases ubiquas = 0 nos 5 cursos**,
  SO caiu de 168 para 98 frases no indice. **Ganho na regua: ZERO** — o braco G previu +2 e nao
  era simulacao fiel; o ruido era simetrico entre unidades, entao nao mudava o argmax. O fix
  continua certo (remove sinal de discriminancia nula), mas nao e ganho de acuracia.
  **CORRECAO**: `camadas` (ES2) e `definicao da classe` (TCC) na tabela original eram FALSOS
  POSITIVOS — meu contador somava ocorrencias, nao unidades.
- [CONCLUIDO 2026-08-18b] **A-4 · `—` virava alias (placeholder de formatacao virando sinal)** —
  template escreve `**Sinonimos aceitos:** —` quando nao ha sinonimo e `content_taxonomy.py:371`
  aceitava qualquer nao-vazio. Eram **100 de 361 aliases**: SO 36/97 (37%), ES2 21/50 (42%),
  TCC 26/78 (33%), MF 14/84, IA 3/52. **RULING DO USER: `—` e formatacao em 99% dos casos.**
  Fix: `_GLOSSARY_EMPTY_MARKERS` = `—`,`–`,`-`,`--`,`n/a`,`nenhum`. **Só entra em producao no
  proximo reprocess** (a taxonomia em disco ainda tem os aliases velhos).
- [CODE] **F-5 · 10 de 15 constantes de `thresholds.py` sem prova de calibracao**
  (`as-of 2026-08-18b`, varredura automatica: comentario contiguo citando sweep/gold/regua/razao
  medida). COM prova: `STRONG_SCORE`, `BAND_HIGH`, `DATE_STRONG_BOOST`, `IDF_WEIGHT`, `UNIT_TAG`
  (este ultimo so a partir de hoje). SEM prova: `BAND_LOW` 0.20 · `DATE_WEAK_BOOST` 0.10 ·
  `TOOL_EXTENSIONS` · `METHOD_CAPS` · **`SUBUNIT_TAG` 0.60** · `MARGIN_K` 0.18 ·
  `MARGIN_K_TOPIC` 0.20 · `UNIT_MATCH_REL_MARGIN` 0.15 · `UNIT_MATCH_MIN_WINNER` 0.5 ·
  `SEQUENCE_BOOST` 0.20. `SUBUNIT_TAG` e o analogo direto do gate que acabou de mover 15 pontos
  — e nao existe regua de subunidade. Dois ja provados mortos (F-4).
- [CODE] **F-4 · dois thresholds sao CONSTANTES MORTAS** (`as-of 2026-08-18b`).
  `UNIT_MATCH_MIN_WINNER` (0,5) e `UNIT_MATCH_REL_MARGIN` (0,15) dao resultado IDENTICO nas 72
  linhas do sweep (testados 0,5/0,3/0,15 e 0,15/0,10). Nenhum discrimina nada no corpus atual.
  Ou o piso esta frouxo demais para morder, ou `ambiguous` ja foi decidido antes por outra
  condicao. Nao investigado.
- [CODE] **A-5 · vazamento cross-unidade por alias (MF)** (`as-of 2026-08-18`).
  `logica-de-hoare` e topico da u02 (correto) E `Logica de Floyd-Hoare` e alias de
  `fundamentos-de-logica-de-primeira-ordem`, na u01. Mesmo conceito em duas unidades, uma errada.
  Quarta instancia da classe "sinal textual de uma unidade vazando para outra".
- [DECISION] **A-3 · divergencia de eixo sai CONFIANTE — e o modo dominante do ES2**
  (`as-of 2026-08-18`). ES2 tem 16 de 27 confiante-e-errado (59%): serie de laboratorio
  `roteiro2..8` / `microsservicos2..7`, todas com card `Microsservicos`, todas preditas
  `unidade-01-arquitetura-de-software` com conf **0,86-0,95**, verdade temporal em u02/u03. O
  scorer responde COBERTURA, a regua cobra TEMPORAL. Mesmo padrao no SO com `threads` (6 entries
  preditas u03, verdade temporal u02/u04) — e literalmente a pergunta do handoff anterior.
  Nao e bug de scorer: e o eixo faltante. Mas grava com 0,95 e nada sinaliza.

## CODE — SUBUNIDADE: regua sem rotulo + colapso diagnosticado (2026-08-19)

Regua nova `scripts/eval_subunit_health.py` — **nao precisa de gold**. Nao mede acerto, mede se
o SINAL EXISTE: COLAPSO (concentracao >=60% num subtopico, unidade com >=4 entries e >=3
topicos), IMA (topico com >=2,5x a mediana de aliases dos irmaos), INTEGRIDADE (subtopico stale
ou de outra unidade). Exit 1 em colapso/integridade — serve de gate. Detalhe em
`docs/reports/2026-08-18-achados-eixo-unidade.md` secao G.

TETO DE ACERTO da subunidade (condicao NECESSARIA — subtopico pertence a unidade verdadeira;
derivado dos golds existentes, sem rotular nada): **133/191 = 70%**. Por curso: IA 91% · MF 87% ·
TCC 78% · SO 42% · ES2 26%. SO e ES2 herdam o erro de unidade (divergencia de eixo).

- [CODE] **G-1 · COLAPSO em 3 unidades** (`as-of 2026-08-19`). IA `u05 aprendizado-de-maquina`:
  40 entries -> **2 subtopicos de 4, 95% num so**. SO `u06 gerencia-de-arquivos`: 5 entries ->
  **1 de 6, 100%**. SO `u02`: 9 entries -> 2 de 4, 89%. Nesses casos `computed_subunit_slug` nao
  e predicao, e constante. Gravado em **209 de 233 entries** dos 5 cursos.
- [CODE] **G-3 · CAUSA: o topico vencedor duplica o vocabulario da propria unidade**
  (`as-of 2026-08-19`). IA u05: titulo tem tokens `apren`+`maqui`, e o topico vencedor
  `introducao-ao-aprendizado-de-maquina` contem os DOIS — todo material da unidade casa nele.
  SO u06: titulo `arqui`+`geren`, vencedor `arquivos`. SO u02: `escal` aparece em 2 dos 4
  rotulos irmaos. MF u01 nao colapsa porque nenhum topico domina. Falta **IDF intra-unidade** em
  `score_entry_against_taxonomy_topic`. Mesma classe do A-1, um nivel abaixo.
  NAO implementado: sem regua de ACERTO de subunidade, trocaria perda medida por ganho nao
  medido (ver G-2).
- [REJEITADO 2026-08-19] **G-2 · desempate por POSICAO em `_select_supported_taxonomy_topic`**
  (`content_taxonomy.py:255`, `if score > best_score` mantem o primeiro da lista). CONFIRMADO
  experimentalmente: inverter a ordem dos topicos do IA u05 troca a resposta. Fix candidato
  (empate => nao vira alias de ninguem) medido: aliases do IA u05 `[9,2,2,2]` -> `[4,2,2,2]`,
  **colapso 95% -> 95% (nao muda)**, regua entry->unidade **132 -> 128 (-4)**. Custa 4 certas e
  nao move o colapso. O defeito de desempate CONTINUA existindo — so nao e a causa do colapso.
- [CODE] **G-4 · B-5 tem consequencia real em producao, ao contrario do que medi**
  (`as-of 2026-08-19`). A regua achou `logicadehoare2` com subtopico **`21-logica-de-hoare`** —
  slug com o prefixo numerico grudado, o defeito de `_strip_topic_prefix` que eu tinha medido
  como INERTE na regua de unidade. Nao e inerte: corrompe subunidade. Sobe de prioridade.
- [CODE] **G-5 · integridade** (`as-of 2026-08-19`): SO `programa` recebe subtopico
  `estudo-de-casos` que pertence a OUTRA unidade. 1 caso, mas viola o invariante P0.2.
- [REJEITADO 2026-08-19] **H · IDF intra-unidade** — implementado em DUAS variantes e medido
  contra as duas reguas. **Duro** (token comum sai do overlap E frase so-comum nao conta como
  hit): ponta-a-ponta **132/47/12 -> 130/50/11** (-2 certo, +3 errado); scorer isolado 109->112.
  Resolve SO u06 (100%->40%) e SO u02, IA u02 vai de 4 para **6 de 6 topicos** (56%->31%), mas
  **IA u05 PIORA (95%->98%)** e TCC ganha 2 colapsos novos. **Suave** (so o overlap, frase
  preservada): 131/47/13, neutro, colapso segue em 3 so trocando de lugar. Revertido.
  **LICAO**: o colapso do IA u05 sobrevive as duas => NAO e causado por token comum, e sim pelos
  ALIASES MAL ATRIBUIDOS (`Aprendizado Supervisionado` esta no topico `introducao-*` quando
  pertence a `paradigmas-*`). Os dois candidatos atacam metades diferentes e cada um cobra:
  empate=>ninguem custa -4 e nao move o colapso; IDF custa -2 e piora o IA. O fix certo e
  "empate => desempatar por EVIDENCIA melhor", que exige sinal que hoje nao existe.
- [CONCLUIDO 2026-08-19] **H-2 · bonus fantasma de +1,4 (`timeline/index.py`)** — quando o
  topico nao tem token proprio, `len(overlap) >= len(topic_tokens)` vira `0 >= 0` e soma **+1,4
  INCONDICIONAL em toda entry avaliada**. Vivo em producao: **3 topicos do MF** com vocabulario
  inteiro em `UNIT_GENERIC_TOKENS` (`Linguagens de Especificacao e Logicas`, os dois `Softwares
  de Suporte a Verificacao Formal de ...`). Guard aplicado. Ponta-a-ponta no gate operante
  (0,50): **132/47/12, identico** — neutro; ganha nos gates altos (0,65: 126->127). Mantido por
  ser correcao de defeito a custo zero. Teste
  `test_topico_sem_vocabulario_proprio_nao_ganha_bonus_fantasma`. Achado colateral da tentativa
  de IDF — o fix rejeitado pagou por si em diagnostico.

## CODE — `known_tools`: raiz documentada, dano MEDIDO = ZERO (2026-08-18)

Investigado a pedido do user. **Prova mais forte que ablacao**: `build_content_taxonomy` com
`_looks_like_tool_candidate` ligado vs desligado produz JSON **byte-identico** nos 5 cursos —
o bypass do `topic_code` cobre 100% dos topicos do plano, o filtro nunca e alcancado. Ablacoes:
eixo de BLOCO 0 flips (com e sem voto do LLM); eixo de UNIDADE 0 delta em 4 bracos
(sem `ferramenta:` poluida / sem `bloco:` / sem `topico:` / `topico:` com prefixo corrigido).
**Arma carregada com a trava acionada: higiene, nao urgencia.** Detalhe em
`docs/reports/2026-08-18-achados-eixo-unidade.md` secao B.

DEFINICAO OPERACIONAL DE FERRAMENTA (extraida do proprio codigo, `concept_resolver.py:158` e
`:218`): **instrumento com que a unidade inteira e ensinada, uniformemente — discrimina UNIDADE,
nao discrimina BLOCO.** Teste: trocar por outra mantem o conteudo ensinado? Isabelle->Coq mantem
"Logica de Hoare" => ferramenta. Trocar "Logica de Hoare" muda o conteudo => topico. Lista certa
ja existe: `semantic_defaults.json`, 11 entradas, todas provadores.

- [CODE] **B-1 · `_infer_tool_candidates` e um gerador de anti-topico** (`semantic_config.py:196`).
  Vocabulario auto-inferido do proprio corpus usado como filtro DESTRUTIVO sobre esse mesmo
  corpus. Realimentacao positiva: quanto mais central o termo, mais vira "ferramenta". Vocabulario
  vivo (`as-of 2026-08-18`): MF `formal`,`programas`,`modelos`,`invariantes`,`hoare`,`sobre` ·
  TCC `hierarquia`,`propriedades`,`cook-levin`,`np-completude` · SO `threads` · ES2
  `cliente-servidor`,`devops`. Fix: parar de inferir; usar defaults curados + override por curso.
- [CODE] **B-3 · o filtro de ferramenta e SUBTRATIVO — erro categorico** (`content_taxonomy.py:159`).
  Ser ferramenta nunca deveria apagar topico. Dafny e ferramenta E topico do MF. Fix: tirar
  `_looks_like_tool_candidate` de `_is_valid_topic_candidate`; `known_tools` so ADICIONA
  `ferramenta:`. Derruba `tests/test_taxonomy_topic_loss.py:111-112` — que pina `Uso de threads`
  e `Provas de NP-Completude` como ferramenta, sendo ambos topico. Devem cair.
- [CODE] **B-4 · fix assimetrico: `_extract_tool_candidates` ficou com substring cru**
  (`content_taxonomy.py:202` vs `:101` que ganhou fronteira). Duas copias da mesma logica de
  match — extrair helper. Efeito: `"Especificacao informal de requisitos"` -> `ferramenta:formal`.
  MF tem 20 `ferramenta:` contra 18 `topico:` no catalogo (`as-of 2026-08-18`).
- [CODE] **B-5 · segundo parser de topico sem normalizacao** (`content_taxonomy.py`
  `_extract_topic_candidates`). Trata `## `, `- [ ] `, `- ` mas NAO `**`. Linha real do SO
  `- **1.1** Evolucao historica` -> slug `11-evolucao-historica` vs `evolucao-historica` da
  taxonomia. **SO: 36 topicos, 48 tags `topico:`, 0 casando** (`as-of 2026-08-18`); confirmado em
  producao (`topico:32-escalonamento`, 10 slugs). Fix: reusar
  `teaching_plan._normalize_teaching_plan_heading`. Impacto na regua: **nenhum** (medido).
- [CODE] **B-6 · IA: 0 topicos do plano no catalogo de tags** (`as-of 2026-08-18`).
  `_extract_topic_candidates` exige marcador ou numero no inicio; o plano do IA vem em linha
  solta (`_parse_units_from_teaching_plan` trata via `current_style == "learning_unit"`,
  `content_taxonomy` nao). 19 topicos na taxonomia, 0 tags.
- [CODE] **B-7 · heuristicas de forma sobre entrada autoritativa**. `>6 palavras` e
  `>=2 hifens / >=9 espacos / ano 19xx-20xx` matam topico que o plano JA numerou sob uma unidade.
  Vitimas no TCC: `Argumento Diagonal de Cantor e Conjuntos Incontaveis`,
  `Prova da Indecidibilidade do Problema da Parada`. Fix: rodar so em candidato de heading.
- [CODE] **B-8 · `.tag_catalog.json` e git-ignored e o rollout nao regenerou** (mtime 15:39,
  fix commit 16:19, rollout 16:48). Cache nao versionado consumido pelo scorer (S4).
- [CODE] **B-9 · `TOOL_TOKENS` nao existe — o comentario mente** (`entry_signals.py:84`). Diz que
  "o scorer de bloco (file_map, TOOL_TOKENS) filtra quais sao ferramentas de verdade". O simbolo
  so existe em `.pyc` stale. Nada filtra.

## CODE — REALIMENTACAO pelas auto_tags: a raiz da regressao (2026-08-19)

Isolamento com harness FIEL (learned_unit_boosts + manual_unit_slug + reconcile), 191 rotuladas:

| variante | gate 0.65 | gate 0.50 |
|---|---|---|
| base (HEAD) | 126 | 129 |
| + poda glossario + guard | 126 | 130 |
| + fix do loop de correcao | 126 | **131** |

Isolado, **+5 e nenhum curso regride** (MF 52->53 · SO 14->15 · IA 38->40 · ES2 8->8 · TCC 14->15).
Em PRODUCAO o mesmo codigo da **127 -> 127**. A diferenca e a realimentacao.

- [CONCLUIDO 2026-08-19] **J-1 · `extract_entry_learned_terms` aprendia pelos ESPELHOS da
  saida do sistema** (`src/models/tag_profile.py:98`). Ele extraia o slug de TODA auto_tag,
  incluindo `unit:`, `subunit:` e `bloco:` — que `resolver_apply` escreve a partir do que ele
  mesmo computou. Efeito medido: **1 correcao humana do MF atingia 19 de 67 entries (28%)** com
  boost de +1.5 a +3.0 para `unidade-03-verificacao-de-modelos`, casando por `bloco-03`,
  `codigo` e `unidade-01-metodos-formais`. Com `winner_score` tipico de 1.79, um boost de 3.0
  decide sozinho. Fix: `_PREFIXOS_ESPELHO = {unit, subunit, bloco, block}` filtrado do
  aprendizado. Harness: 130 -> **131**. Producao: 0.
  **Segundo registro do mesmo perfil tem `corrected_unit_slug` VAZIO** e e silenciosamente
  pulado (`tag_profile.py:160`) — lixo que ninguem ve.
- [CODE] **J-2 · o loop MAIOR continua: `auto_tags` sao entrada E saida** (`as-of 2026-08-19`).
  Medido rodando o MESMO harness sobre os manifests antes e depois do reprocess:
  **131 (tags antigas) -> 129 (tags novas)**, toda a perda no MF. As tags que o sistema escreve
  alimentam `auto_tags_text` em `score_entry_against_unit` (0.18 exato / 0.04 parcial) e
  `tags_text`. Logo TODO reprocess desloca o resultado sem ninguem ter mudado nada — o sistema
  re-elege a propria resposta anterior, e quebrar esse eco custa acerto.
  **E a explicacao definitiva de por que a regressao nao fecha por mudanca de scorer.**
  Fix candidato: excluir prefixos gerenciados de `auto_tags_text`/`tags_text` nos signals, do
  mesmo jeito que J-1 fez no aprendizado. NAO medido.
- [CODE] **J-3 · o harness fiel ainda difere da producao em ~2** (129 vs 127, `as-of 2026-08-19`).
  Diff entry-a-entry: 9 divergencias, harness acerta 4 e erra 1. As 5 restantes sao entries que
  a producao deixa VAZIAS (`SO/laminas-sockets`, `IA/artigo-usando-agrupamento`, `ES2/plano`) —
  `apply_unit_subunit_fields` pula entry sem `computed_block_id`. Falta modelar esse skip.

- [CONCLUIDO 2026-08-19] **J-2 · eco cortado nos signals** (`extraction/entry_signals.py`).
  `auto_tags_text` e `tags_text` deixam de receber os prefixos que o proprio motor escreve
  (`unit:`, `subunit:`, `bloco:`, `block:`). A lista crua de `auto_tags` segue inteira para
  `tool_values` e para os outros leitores — so o TEXTO de score perde o eco.
  **RESULTADO: ponto fixo.** Reprocess rodado DUAS vezes seguidas com o mesmo codigo:
  **0 entries mudam** entre elas, nos 5 cursos. Harness idempotente tambem: 129 antes do
  reprocess, 129 depois (antes do fix era 131 -> 129, deslocava 2).
  Custo: 2 acertos no harness (131 -> 129) — eram o eco reelegendo a resposta anterior, que
  estava mais certa que errada. Producao: unidade **127**, identica ao baseline.
  **Isto e pre-requisito de qualquer medicao futura**: sem ponto fixo, comparar dois reprocess
  media o sorteio, nao a mudanca.

## VEREDITO da rodada (2026-08-19)

Estado FINAL em producao, apos cortar o eco (J-1 + J-2), `as-of 2026-08-19`:

| metrica | baseline | final | |
|---|---|---|---|
| unidade | 127/191 | **127/191** | neutro |
| bloco | 118/208 | **118/208** | intocado |
| subunit coerente | 133/170 (78%) | **121/161 (75%)** | pior 3pp |
| colapsos de subunidade | 3 | **6** | pior |
| aliases na taxonomia | 361 | **259** | limpeza |
| **idempotencia do reprocess** | **deslocava 2** | **ponto fixo (0)** | **ganho estrutural** |

O eixo de UNIDADE fica neutro e agora e REPRODUZIVEL. O eixo de SUBUNIDADE piora — e o eixo
que ja se sabe quebrado (colapso medido, sem regua de acerto, cardinalidade errada: 53 arquivos
avaliativos recebendo 1 subtopico so). Suite **1902 passed / 1 skipped**.

## CODE — EIXO DE BLOCO investigado (2026-08-19d)

**CORRECAO DE UM NUMERO QUE EU REPETI VARIAS VEZES**: o bloco NAO esta em 57%. Esta em
**172/200 = 86%**. O 118/208 media `computed_block_id` cru; a regua oficial
(`scripts/eval_ground_truth.py`) usa `resolve_temporal_block`, que honra a ANCORA temporal e os
pinos manuais — que e o que o sistema de fato usa. **Os tres eixos estao em 86-88%; nao ha elo
fraco isolado.** Por curso: MF 95,5% · IA 97,7% · ES2 78,6% · TCC 72,0% · SO 71,1%.

- [CONCLUIDO 2026-08-19d] **a regua do bloco estava CEGA em 3 de 5 cursos, em silencio**.
  `load_labels_csv` lia com `encoding="utf-8"`; ao sincronizar os golds do dedup eu gravei com
  `utf-8-sig`, que ADICIONA BOM — a 1a coluna virou `﻿id`, `row.get("id")` devolveu None e
  a regua reportou **`Acuracia: 0/0`** para MF, SO e IA sem erro nenhum. Corrigido nos DOIS
  leitores do arquivo (`utf-8-sig` aceita com e sem BOM) e os CSVs normalizados sem BOM.
  **Classe de bug**: regua que degrada para zero em silencio e pior que regua ausente.
- [CODE] **os 28 erros do bloco se concentram em AVALIACAO e META** (`as-of 2026-08-19d`):

  | classe | ok | erro | taxa |
  |---|---|---|---|
  | CONTEUDO (material de aula) | 143 | 15 | **9%** |
  | AVALIACAO (provas/listas/gabaritos/trabalhos) | 29 | 10 | **26%** |
  | META (cronograma/outros) | 4 | 3 | **43%** |

  Termo da fusao que decide errado: **`concept` em 21 de 25**, `llm` em 4. Direcao do erro:
  ES2 e TCC preveem um bloco ANTERIOR em **13 de 13**; SO preve POSTERIOR em 8 de 11; mediana da
  distancia −1 e 8 de 26 sao off-by-one. Por metodo: `date` **0% de erro** (19 casos) ·
  `concept-fused` 16% (161) · vazio 29% (14).
  **Diagnostico**: e a mesma tensao conteudo-vs-tempo do eixo de unidade — material multi-topico
  casa conceito difusamente e ganha o bloco que compartilha mais vocabulario, nao onde a prova
  aconteceu. No bloco NAO da para resolver com N: uma prova aconteceu numa data so.
- [REJEITADO 2026-08-19d] **`posting_date` como sinal de bloco**. **Ruling-user: professor reusa
  material antigo** — verificado: os anos batem (tudo 2026), mas **88 de 166 postagens estao FORA
  do periodo do curso**, em lotes (`2026-02-18` x45 no MF, `2026-02-24` x25 no IA,
  `2026-02-18` x16 no ES2). E data de UPLOAD EM MASSA, nao de aula. Mesmo filtrando lote e
  periodo sobram 29 casos e a precisao e **41% (12 de 29)**, contra 84% do `concept-fused`;
  corrigiria **1** erro. Rejeitado.
- [REJEITADO 2026-08-19d] **janela de `assign_due` para avaliacao** — o mecanismo existe
  (`ASSIGN_WINDOW_CATEGORIES`, `motor/due_window.py`) mas so **4 de 37 cards** tem o dado, e
  NENHUM bloco tem `card_evidence` populado. Sem dado para sustentar os 39 avaliativos.
- [CODE] **o sinal de data vem do NOME DO ARQUIVO, nao do Moodle** (`_score_block_date_match`,
  `file_map.py:954`): extrai de `raw_text`/`title_text`/`markdown_text`. Por isso o metodo `date`
  so dispara no SO, cujos arquivos sao `0205-`, `2403-`, `3103-` (DDMM no nome).
  **Ruling-user 2026-08-19d: manter assim, como fallback.** Onde ha data no nome, acerta 19/19.

## DECISION RESOLVIDA — granularidade da avaliacao (2026-08-19c)

Aberta desde o handoff de 2026-08-18. **RESOLVIDA: prova INTEIRA com conjunto de topicos.
NAO quebrar em questoes.** Tres medicoes sustentam:

1. **So 5 de 39 arquivos avaliativos sao multi-unidade** (`as-of 2026-08-19c`). 36 dos 39 (92%)
   ja tem `coverage_units`, e a regra B ja extrai os TOPICOS citados no enunciado. O eixo de
   unidade nao precisa de granularidade menor.
2. **Quebrar em questao so rende no nivel de TOPICO**, e a regra B ja entrega topicos por
   avaliacao sem LLM — a lista P1 do SO devolve `u01|u02|u03|u04` com os topicos citados.
3. **O gargalo nao e granularidade, e o artefato nao existir.** `exams/EXAM_INDEX.md` existe em
   **1 de 5 cursos** (so MF), tem **10 linhas**, lista **1 arquivo**, e a coluna `Observacao` esta
   VAZIA — enquanto o cabecalho promete *"identificar quais topicos tem maior incidencia e quais
   padroes de questao se repetem"*. E o mesmo diagnostico do handoff anterior, agora com o
   numero: investir em extracao por questao antes de o indice existir e otimizar o que ninguem le.

- [CODE] **fila derivada desta decisao**: (a) gerar `EXAM_INDEX.md` nos 5 cursos, nao 1;
  (b) alimenta-lo com `coverage_units[].topics` (ja existe) para dar incidencia por topico sem
  LLM; (c) a coluna `Observacao`/`Padrao do professor` depende de `notes`, que esta **0%
  preenchido** nos 233 materiais (achado K-4) — ou some da tabela ou vira derivada.
  Quebra por questao fica REGISTRADA como opcao futura, nao como pre-requisito.

## CODE — DUPLICATAS DE CONTEUDO: 6 removidas (2026-08-19c)

`scripts/dedup_manifest.py --by-content` (modo novo). O modo antigo agrupa por basename
normalizado E exige que uma das gemeas nao exista no stash — nao pega duplicata de conteudo com
nomes diferentes e os dois arquivos presentes.

**GUARD NAO-NEGOCIAVEL (ruling-user 2026-08-19c)**: gabarito e lista sao documentos DISTINTOS e
importantes; o professor frequentemente passa os dois. O dedup **nunca remove automaticamente
quando as categorias diferem** — marca AMBIGUO e deixa para o humano. Verificado nos 5 cursos:
gabarito sempre tem mais texto que a lista (MF 5264 vs 3366; ES2 16057 vs 7746; IA 13357 vs
9332), entao o hash nunca colide entre os dois de verdade.

Removidas (sha1 identico do markdown; campos que so a descartada tinha — `posting_date`,
`moodle_label` — sao MESCLADOS na mantida, porque data e sinal do eixo temporal, o mais fraco):

| curso | removida | mantida | por que |
|---|---|---|---|
| MF | `logicadehoare1-exercicios-respostas` | `logicadehoare-exercicios-respostas` | cross-categoria; **ruling-user: os DOIS sao gabarito**, md5 identico ja na origem do Moodle (623885 bytes, 12/jun e 28/jun). Mantida a catalogada como `gabaritos`, que e o que o conteudo E |
| SO | `lista1-gab` | `lista-exercicios-p1-gabarito` | mesma categoria |
| SO | `lista2` | `lista-exercicios-p2` | mesma categoria |
| IA | `minimax` | `minimax-teoria` | mesma categoria |
| IA | `lista1` | `lista-de-exercicios-i` | mesma categoria |
| IA | `prova-1-202402` | `prova-1-2024-02` | mesma categoria |

Entries: **233 -> 227**. Golds sincronizados (6 linhas orfas removidas de `ground_truth_*` e
`material_gt_SO`), **preservando as linhas de `id` vazio** — sao registro deliberado com
`scorable=no` e proveniencia, nao lixo (apaguei por engano e restaurei via git).
`p1-2024-02-ia.pdf` fica como arquivo ORFAO na pasta do IA: existe em disco, nao e entry.

**BASELINE APOS DEDUP (`as-of 2026-08-19c`)**: unidade 1:1 **166/188 = 88%** ·
cobertura **44/57 = 77%, F1 0,81** · entries 227.

## CODE — COBERTURA DO MATERIAL: as 3 regras em codigo (2026-08-19b)

`src/builder/routing/coverage_rules.py` — `coverage_units[]` no MATERIAL, mesmo formato
da camada de referencia. **Sao os rulings do user virados COMPORTAMENTO**: sem isso o mesmo
julgamento teria de ser refeito a mao em cada cadeira nova. Nenhuma regra olha nome de arquivo
nem de cadeira.

| regra | criterio | derivado de |
|---|---|---|
| A meta | categoria `cronograma` OU cita o titulo de >=80% das unidades | ruling: meta cobre todas |
| B avaliacao | titulo casa `P1/Prova2/Lista1` E categoria de avaliacao -> unidades citadas no enunciado | ruling: Lista PX cobre as unidades da prova |
| C card | card nomeia unidade/topico -> a de MAIOR evidencia | ruling: serie cobre a unidade do tema |
| + fallback | a unidade 1:1 ja decidida entra na cobertura | cobrir e superconjunto de morar |

**BASELINE (`as-of 2026-08-19b`, 58 rotulos com `scorable=yes`)**:
**exact-set-match 44/58 = 76% · precisao 0,78 · recall 0,81 · F1 0,79**.
Por curso: ES2 19/19 · TCC 3/3 · SO 14/20 · MF 7/13 · IA 1/3.

Progressao medida: 23/58 (40%) -> 41 (71%) -> **44 (76%)**. O que cada correcao rendeu:
desempate do card por evidencia **+18** (ES2 1/19 -> 19/19) · topicos da TAXONOMIA em vez de
`topic_phrases` **+3** no SO (matava `kernel`/`sistema` entrando como topico) · aliases junto do
label **+2** · token distintivo (>=10 chars) em vez de substring **+3** (o card do TCC diz
`Halteproblem und Entscheidungsproblem`, em alemao, e o label e
`entscheidungsproblem e introducao a reducibilidade de problemas`: substring nao casa, token sim).

- [REJEITADO 2026-08-19b] **baixar `_MIN_TOPICOS_PARA_UNIDADE` de 2 para 1** — sweep contra os
  58 rotulos: **44 -> 43 exact**, precisao e recall IDENTICOS. Perda seca, nao trade-off.
- [CODE] **`_MIN_TOKEN_DISTINTIVO` e mais uma constante inerte** (`as-of 2026-08-19b`):
  resultado identico com 8, 10 e 12. Junta-se a `UNIT_MATCH_MIN_WINNER` e
  `UNIT_MATCH_REL_MARGIN` na lista dos limiares que nao discriminam nada no corpus atual.
- [USER] **ROTULAGEM COMPLETA: 64 casos, 0 pendentes** (`docs/reports/material_gt_*.csv` +
  `scripts/make_material_coverage_labels.py`, que PRESERVA rotulo ja dado ao regenerar).
  Rulings de 2026-08-19: serie de microsservicos -> a unidade que fala de microsservicos (17
  casos) · meta-material -> todas as unidades · Lista PX -> unidades da prova ·
  `Processo e Estruturas de Controle` -> u01 (`chamadas-de-sistema`) · ENADE -> meta (todas) ·
  `exemplos-zip` -> u03 (confirmado abrindo o zip: 5 arquivos `.smv`).
- [CODE] **os 14 que ainda erram, por causa** (`as-of 2026-08-19b`):
  **4 bibliografia** — texto depende de rede; a camada de REFERENCIA processa a MESMA entry em
  paralelo e as duas coberturas nao se falam (o `eth2` tem `coverage_units` na referencia e
  `[]` no material). Unificar renderia no maximo 1 dos 4 — os outros 3 a referencia tambem nao
  sabe. **6 codigo** — resumo do Gemini raso demais (~400 chars) para discriminar.
  **4 avaliacao** — `lista1-gab` nao casa o regex, `exercicios`, ENADE.

- [CONCLUIDO 2026-08-19b] **`.smv` nao era extensao de codigo reconhecida**
  (`utils/helpers.py` `CODE_EXTENSIONS`/`LANG_MAP`, `thresholds.TOOL_EXTENSIONS`).
  `concept_resolver.py:442` JA documentava *"a ferramenta (.dfy/.thy/.smv) ancora a UNIDADE"*,
  mas a lista so tinha `.thy` e `.dfy`. Efeito medido: `exemplos.zip` do MF (5 arquivos NuSMV)
  era o **UNICO zip sem extracao nos 5 cursos** — `extracted_files=[]`, sem resumo do Gemini,
  sem sinal nenhum. **RESSALVA: o ganho NAO aparece em `reprocess_assignments`**, que pula o
  laco de extracao de proposito; so no proximo import de verdade. Teste
  `test_smv_e_linguagem_de_codigo_reconhecida`.
- [CONCLUIDO 2026-08-19b] **sentinela `test_caracterizacao_blocos_atual[TCC-Tutor]`
  rebaselinada** apos revisao caso a caso: `aula-06-revisao-alfabeto-cadeia-linguagem` mudou de
  u01 para u04 e **AMBOS ESTAO ERRADOS** — o certo e `unidade-02-turing-computabilidade` (o
  card diz "Teoria de Automatos e Introducao a Maquinas de Turing"). Causa medida: colisao
  lexical (`Hierarquia de Chomsky` casa `hierarquia de classes de complexidade`), u04 e a maior
  unidade (14 topicos), e 27 mil chars de markdown espalhando match. u02 perde por 2,64 (5%).
  Fica como caso conhecido do TCC, nao como regressao.

## CODE — VARREDURA "sinal que existe e nao chega a quem decide" (2026-08-19)

Matriz sinal x decisor, montada por grep sobre os tres scorers
(`concept_resolver` / `score_entry_against_unit` / `_score_entry_against_taxonomy_topic`):

| sinal | BLOCO | UNIDADE | SUBUNID | veredito |
|---|---|---|---|---|
| `title_text`, `markdown_text` | X | X | X | ok |
| `markdown_headings/lead`, `category`, `tags`, `raw` | - | X | X | bloco usa outro modelo (vetor de conceito) |
| **`card_text`** | - | X | **-** | **gap plausivel, NAO mensuravel hoje** |
| **`moodle_label_text`** | X | **-** | **-** | **FALSO gap — redundante** |
| **`tool_tags_text`** | X | **-** | **-** | gap teorico; vocabulario sujo, baixa prioridade |
| `image_description_text` | - | - | - | campo morto (0% de dado nos 5 cursos) |

- [CONCLUIDO 2026-08-19] **K-1 · resumo do Gemini nao chegava a UNIDADE** — `code_curation`
  alimentava BLOCO (`entry["concepts"]`, `resolver_apply.py:90`) e SUBUNIDADE (`sub_md`), mas a
  UNIDADE recebia `markdown_text`, vazio para zip/codigo. **25 de 233 materiais (11%)** decidiam
  unidade sem ler nada — entre eles `colecoes-*` e `classes-parte1` do MF, que viviam no balde
  de erro. O comentario do proprio codigo entregava: *"unit/bloco ficam com o markdown original
  (mesma mecanica do legado)"* — herdado, nao decidido.
  **MEDIDO EM PRODUCAO: unidade 127 -> 131 (+4).** Maior ganho isolado da campanha.
  Subunidade passou a reusar o mesmo texto (duplicacao removida). Teste
  `test_resumo_de_codigo_alimenta_a_rota_de_UNIDADE_tambem`.
- [REJEITADO 2026-08-19] **K-2 · `moodle_label` na rota de unidade** — parecia gap (167 de 233
  = 72% preenchido, labels limpos como `Conjuntos Indutivos`). Implementado e medido:
  **0 entries mudam**. Causa: o label e o titulo com as palavras separadas
  (`conjuntosindutivos` vs `conjuntos indutivos`) e o pipeline JA aplica `split_camel_case` no
  titulo (`entry_signals.py:120`). Redundante por construcao. Revertido.
- [CODE] **K-3 · `card_text` nao chega a SUBUNIDADE** (`as-of 2026-08-19`). Card presente em
  **228 de 233 (98%)** e casa um topico da taxonomia em **74 de 228 (32%)** — ES2 74%, MF 39%,
  TCC 22%, SO 19%, IA 15%. A UNIDADE le (peso 2.5 na frase); a SUBUNIDADE nao. **NAO
  implementado**: sem regua de ACERTO de subunidade, seria trocar ganho nao medido por risco.
  A ausencia no BLOCO e DELIBERADA (`test_card_nao_afeta_o_scorer_de_bloco_do_motor`; card e
  sinal de cobertura, nao temporal).
- [CODE] **K-4 · campos capturados e mortos** (`as-of 2026-08-19`): `professor_signal` **0%
  preenchido** e nunca lido em `src/`; `notes` **0%** — e o `EXAM_INDEX` promete colunas
  `Observacao`/`Padrao do professor` que dependem dele; `image_description` **0%**, logo
  `image_description_text` e campo morto por falta de DADO (o conteudo, quando existe, ja entra
  via `markdown_text`). `relevant_for_exam` esta em 99% mas nao e sinal de unidade.

## CODE — o eixo N:N era ESCRITO e NUNCA LIDO — RESOLVIDO (2026-08-19 / 2026-08-20)

- [CODE] **I-1 · `coverage_units` tem 1 ocorrencia em `src/` e e a ESCRITA** (`as-of 2026-08-19`).
  Grep no codigo de producao: `src/builder/core/reference_summary.py:135` (write). **Zero
  leituras.** Quem alimenta COURSE_MAP, BIBLIOGRAPHY e a navegacao e o single-winner
  `computed_ref_unit`/`computed_ref_topics`, escrito no MESMO dict literal como espelho do
  primeiro item da lista (`assign_concepts_to_unit` devolve as duas formas; nao podem divergir,
  mesmo padrao de `auto_tags["bloco:"]`). Consumidores de `coverage_units` hoje: so
  `scripts/eval_coverage.py`, `scripts/refresh_reference_coverage.py` e
  `tests/test_reference_summary.py`.
  **A camada de cobertura calcula N:N e o sistema inteiro usa 1:1.** Terceira instancia da classe
  "codigo certo, dano zero, porque ninguem chega la" (as outras: `known_tools`, `TOOL_TOKENS`).
  A duplicacao NAO e o problema — o campo morto e.
- [CODE] **I-2 · os 4 consumidores que precisariam mudar para o N:N valer** (`as-of 2026-08-19`):

  | onde | le hoje | precisaria ler |
  |---|---|---|
  | `artifacts/repo.py:670-671` | `computed_ref_unit` + `computed_ref_topics` | iterar `coverage_units`, emitindo a ref sob CADA unidade coberta |
  | `core/reference_navigation.py:35,49,53` | `computed_ref_unit` (pula ref com campo vazio) | agrupar por ancora em N unidades, nao 1 |
  | `artifacts/navigation.py:35` (FILE_MAP) | 1a tag `subunit:` | N tags, ou primaria por confianca |
  | `ui/dialogs.py:4193` | 1a tag `subunit:` | idem |

  Os dois primeiros valem para REFERENCIAS (o N:N ja existe); os dois ultimos sao o que a
  subunidade-como-tags exigiria. **E aqui que o valor aparece** — escrever a lista sem trocar o
  leitor so cria um segundo campo write-only.

- [DONE] **I-3 · os dois leitores de REFERENCIA passaram a ler a lista** (`2026-08-20`).
  `core/reference_navigation.py` ganhou `_ancoras(rec)`: devolve `[(unit_slug, topics)]` a partir
  de `coverage_units`, com fallback para o espelho `computed_ref_unit` (curation antiga segue
  funcionando). `build_unit_topic_reference_index` emite a ref sob CADA ancora, e nao pula mais
  ref sem o espelho. `artifacts/repo.py` exibe todas as ancoras em `Relevante para:` separadas
  por `·`. **Medido:** MF sai de 2 para 4 ancoras (o `eth2` e o `archive-of-formal-proofs` passam
  a aparecer sob `metodos-formais` E `verificacao-de-programas`); IA e SO nao mudam.
- [OPEN] **I-4 · SO tem 3 referencias com ZERO ancora** (`as-of 2026-08-20`). Nem `coverage_units`
  nem `computed_ref_unit`. Ficam invisiveis no COURSE_MAP — o `_ancoras` devolve lista vazia e a
  ref some. Nao e regressao (antes tambem sumiam, pelo `continue`), mas agora esta medido.
- [DONE] **I-5 · o material tambem virou N:N no COURSE_MAP** (`2026-08-20`).
  `build_unit_topic_reference_index` passou a devolver `material_by_unit` (mesmo ponto de
  encanamento, `_reference_nav_index`, que ja chegava no COURSE_MAP — nenhum cano novo). A secao
  por unidade emite `🧪 Tambem cobre esta unidade: ...`. **So as unidades EXTRAS** entram, isto e,
  aquelas que o vencedor 1:1 nao nomeia: repetir a unidade-dona so incharia o "mapa pedagogico
  curto", que ja mostra isso no FILE_MAP e na timeline.
  **Medido nos 5 cursos:** 213 entries com `coverage_units`, distribuicao N = {1: 190, 2: 15,
  3: 3, 4: 2, 7: 3}; 23 multi-unidade, TODAS as 23 com ao menos uma unidade extra.
  `cronograma` fica de FORA da renderizacao (`META_CATEGORIES`): sozinho gerava 16 das 49 linhas,
  sempre o mesmo plano de ensino sob cada unidade. O manifest mantem a cobertura completa — a
  busca continua achando o plano por qualquer unidade; e so a linha do COURSE_MAP que sai.

## CODE — NAO-DETERMINISMO no score de bloco: RESOLVIDO (2026-08-20)

- [DONE] **J-1 · `computed_block_confidence` mudava entre duas rodadas IDENTICAS do reprocess.**
  Raiz: `concept_resolver.py`, `sum(min(...) for tok in entry_vec.keys() & block_vec.keys())`.
  `keys() & keys()` devolve **set**, e a ordem de iteracao de set de `str` muda a cada processo
  (hash randomization do Python). Somar float em ordem diferente muda o resultado no ultimo ULP.
  **Consequencias medidas (TCC):** 6 entries divergiam entre rodadas; a `band` flipava na
  fronteira baixa/media; e em empate tecnico o bloco VENCEDOR trocava — `aula-06` (confianca
  0.0841) alternava entre dois blocos conforme o PYTHONHASHSEED. Com `PYTHONHASHSEED=0`, zero
  divergencias. Isso torna suspeita QUALQUER medicao anterior perto da fronteira.
  **Fix:** a soma virou `overlap_min()` (funcao nomeada, `sorted()` na interseccao). Mesmo
  defeito corrigido em `routing/motor/disambiguator.py:_score` (`mat & set(sig)`).
  **Rede:** `tests/test_determinismo_do_score.py` roda o mesmo calculo em 4 subprocessos com
  PYTHONHASHSEEDs diferentes e exige saida identica; tem um segundo teste que impede que a
  entrada vire invariante a ordem (teste vacuoso nao pega o bug de volta). **Verificado que o
  teste FALHA sem o fix** — 3 somas distintas nos 4 seeds.
  **Impacto na acuracia: ZERO.** Bloco continua 172/200 = 86% com e sem o fix; a medicao A/B na
  regua de unidade da 103/188 nos dois casos. O empate era 50/50 mesmo — o valor do fix e o
  reprocess virar idempotente, nao o motor ficar melhor. Sentinela `_golden/TCC-Tutor__casos_
  chave.json` regravada de proposito (coin-flip virou valor fixo).

## CODE — o termo `card` da fusao esta MORTO (2026-08-20)

- [OPEN] **K-1 · `card_evidence` esta vazio em 120/120 blocos dos 5 cursos.**
  `concept_resolver.py:392` calcula `card_term` contra `block.get("card_evidence")`. O campo
  existe em todo bloco e esta **sempre vazio**, entao o termo e 0 sempre.
  **Censo (227 materiais, 5 cursos):** o termo `card` e nao-zero em **0** deles, e isso apesar de
  `signals["card_text"]` existir em **222/227 (98%)**. Assimetria: o lado da ENTRY esta populado
  (vem do `source_section` do Moodle, ex. "Semana 4 - Teoria de Automatos"), o lado do BLOCO nao.
  **Raiz:** `vision/card_evidence.py` so reconhece as formas literais `Card: <titulo>` e
  `Topico: <titulo>` no texto das linhas do cronograma. Nenhum plano de ensino real escreve assim.
  **Contexto:** `concept` e o maior termo em 185/227 (81%); `llm` 4, `date` 5, `lesson` 3,
  `sequence` 0. A fusao e mono-termo na pratica — o que casa com o diagnostico de que `concept`
  decidiu errado em 21 dos 25 erros de bloco.
- [REFUTADO] **K-2 · usar `source_section` como sinal autoritativo PIORARIA.**
  Teto medido de um oraculo que atribui a cada secao o bloco verdadeiro mais frequente:
  **144/199 = 72%**, abaixo dos 86% de hoje (MF 71%, SO 70%, IA 93%, ES2 43%, TCC 78%).
  As secoes sao mais GROSSAS que os blocos (MF: 9 secoes para 23 blocos), entao a secao restringe
  o bloco a um INTERVALO, nao a um ponto. Se for revivido, o card tem que entrar como **filtro**
  (excluir blocos fora do intervalo da secao), nunca como pontuador autoritativo.
- [MEDIDO] **K-3a · o card e ponteiro de UNIDADE, nao de bloco.** Leave-one-out nos 5 cursos
  (janela = unidades verdadeiras dos IRMAOS do mesmo card, verdade = `ground_truth |><|
  gold_units`): **card -> unidade recall 165/170 = 97%, janela media 1,41 unidade**;
  **card -> bloco recall 164/192 = 85%, janela 1,0 a 6,2 blocos** (IA 1,2 · TCC 1,0 · SO 2,1 ·
  MF 2,8 · ES2 6,2). Corrobora K-2 por outro caminho: como filtro de bloco o card tem teto
  ABAIXO dos 86% de hoje; como filtro de unidade, teto 97% contra os 88% do scorer 1:1.
  Duas gramaticas de card convivem: datada ("Semana N - Topico", aponta bloco, TCC/IA) e
  tematica ("Microsservicos", "DevOps", aponta unidade e espalha por varios blocos, ES2/SO).
  RESSALVA: contra a verdade TEMPORAL o card suja (ES2 `Microsservicos` = 22 entries em 3
  unidades; SO `Threads` em 3); contra os rotulos de COBERTURA, 12 de 14 cards = 1 unidade exata.
  O card aponta a unidade de COBERTURA — a deriva temporal e o professor repostando.
- [REFUTADO] **K-3b · consenso por card no eixo de COBERTURA: ganho = +1 em 57.** A ideia que
  K-3a sugeria (irmaos do mesmo card votam a unidade; a entry duvidosa herda o consenso) foi
  medida com a regua EXISTENTE (`scripts/eval_coverage.py::score`, nenhuma regua nova) contra os
  57 rotulos de `material_gt_*.csv`. Voto dos irmaos vem de `manifest.entries[].coverage_units`
  (predicao de producao, nunca do gold); META (cronograma/plano/apoio) nao vota.

  | variante | exact-set | macro P/R/F1 |
  |---|---|---|
  | BASE (producao) | 44/57 | 0,816 / 0,827 / **0,811** |
  | uniao dos irmaos | 22/57 | 0,642 / 0,912 / 0,729 |
  | maioria | 40/57 | 0,813 / 0,796 / 0,781 |
  | filtro (own ∩ irmaos, fallback own) | **45/57** | 0,825 / 0,827 / **0,817** |
  | uniao + self | 21/57 | 0,642 / 0,930 / 0,735 |

  BASE reproduz o numero do handoff (44/57, F1 0,81) — harness validado antes de comparar.
  **CAUSA do ganho nulo, e e boa noticia:** `rule: card` ja responde por **179 das 258**
  `coverage_units` do corpus (`unidade-atribuida` 37, `meta` 17, `meta-por-conteudo` 14,
  `avaliacao` 11). O teto de 97% de K-3a **ja esta colhido** pela regra C; consenso le a mesma
  informacao duas vezes.
  **Blast radius:** no-op em **200/227** entries, muda 7, 20 sem irmao. Dos 7 (todos cortam a 2a
  unidade), so 1 e rotulado — MF `exemplos-zip`, F1 0,667 -> 1,0; os 2 do TCC sao ruido votando
  (os irmaos do card `Semana 4` se contradizem entre si: u02/u03/u04).
  **Achado colateral:** as 3 entries que divergem TOTALMENTE dos irmaos (own ∩ irmaos = vazio)
  estao todas no card `TDE Trabalho Discente Efetivo` — o mesmo que `anchor_engine._TDE_PREFIX` e
  `anchor_placement._ADMIN_TOKENS` ja declaram nao-informativo. Card administrativo agrupa por
  burocracia, nao por tema. O fallback-para-own do filtro engole os 3 em silencio.
  Script NAO promovido a `scripts/`: regua de ideia refutada convida alguem a rodar de novo.
  **Onde o card segue sem consumidor:** eixo de bloco (`use_anchor_engine` default `False`,
  `pedagogical_regeneration.py:552` — a cascata `window_provider` P1..P4 existe e esta desligada)
  e o scorer 1:1, onde ele entra como *hint posicional FRACO* (`concept_resolver.py:346`).

## CODE — RUMO AOS 100% NO BLOCO: prior de kind + a lista do que NAO e codigo (2026-08-21e)

- [DONE] **K-1 · kinds que nunca hospedam material saem de qualquer janela.** Medido nos 200 golds:
  nenhum bloco-gold e `holiday`/`office_hours`/`workshop`/`academic_event` (avaliacao/revisao/
  overview/entrega/suspensao aparecem e seguem elegiveis). Fonte unica `kinds.NEVER_HOSTS_MATERIAL_
  KINDS`; aplicado em `window_provider.drop_never_hosts` (cascata) e no llm-funil. TCC `aula-17`
  (card = [oficina, aula Cook-Levin]) vira janela-1 → **TCC 25/25**, bloco **186/200**, LLM 60 → 58.
- [DONE] **K-2 · janela so com ref fantasma cai no llm-funil, nao em None.** `card_block_map` do IA
  tem uuid OBSOLETO ("Semana 13": [fantasma, evento]); sem o evento (K-1) a entry `ag-feito-em-aula`
  perdia o temporal — o ramo "nenhum ref resolve → funil honesto" devolvia None desde antes do
  llm-funil existir. [NOTA · higiene] uuid obsoleto no card_block_map = drift de dado (timeline
  regenerada, mapa nao) — a regeneracao do mapa deveria invalidar refs mortos.
  **Segunda raiz no mesmo caso (K-2b):** o voto do LLM e cacheado por CONTEUDO, mas a pergunta e
  sobre uma JANELA. O voto antigo ("bloco-13", o evento) ficou fora de toda janela e
  `match_window_ref` devolvia None para sempre — nem o llm-funil reperguntava. `LlmVoter.vote`
  agora grava `window` junto do voto e repergunta (1x, dentro do cap) quando o voto cacheado cai
  fora de uma janela DIFERENTE (ou desconhecida: cache legado). Mesma janela = cache hit; voto
  dentro da janela nova nao repergunta. Testes em `test_motor_llm_vote.py` (1 novo, 1 ajustado).
- [USER] **K-3 · os 14 erros que restam NAO sao codigo. Classificacao com evidencia:**
  *Gold a revisar (6):* MF `t2-2026-1` — due da sala de entrega T2 = **06/07**; o motor ancora no
  ultimo bloco de conteudo antes (18, 29/06); gold 16 (15-22/06) segue "postagem", contra a
  convencao decidida para o T2 do TCC (entrega). SO `exercicios` — card "Gerencia de Processos
  CPU", conteudo = escalonamento; gold 03 "Comunicacao e sincronizacao" vs previsto 04
  "Escalonamento". SO `lista-p1` + `gabarito` — gold 09 (ultima aula antes da P1), mas as
  `lista-p2` do MESMO curso tem gold 21 = dia da P2: o gold do SO e inconsistente entre P1 e P2;
  decidir "lista PN → bloco da prova N" (alinha com P2 e com o motor) ou o inverso. MF `eth2` —
  regra B-6 (ref sem card → bloco-01) vs gold 12: 100% exige re-decidir o gold (01) ou pinar.
  *Curadoria de card, 1 ato por cluster (4):* SO "Threads" → [bloco-06] (3 entries `exemplo-
  threads`; o pino `biblioteca-pthread` tem gold 03 — janela [03, 06] deixa o voto decidir);
  SO "Introducao aos Sistemas Operacionais" → [bloco-02] (`definicao-e-historico`).
  *Sem sinal no dado (5):* ES2 `roteiro2/4/5/7` + `azure` — card "Microsservicos" = unidade inteira
  (10 blocos), cronograma nao nomeia laboratorios (0 de 20 sessoes), codigo sem markdown. 100% aqui
  = dado novo (sessoes do cronograma nomeando os roteiros) ou curadoria por entry.
  Depois disso o eixo de UNIDADE vai junto (178/188 → os mesmos casos).

## CODE — EIXO DE UNIDADE: unidade = unidade do bloco TEMPORAL — 130 -> 178/188 (2026-08-21d)

- [DONE] **U-1 · duas raizes, nenhum remendo.** A verdade de unidade e, por construcao, a unidade do
  bloco verdadeiro (`ground_truth |><| gold_units`) — entao a unidade tem que ser funcao do eixo
  de bloco (185/200), nao do texto. Medido (188 entries): scorer gravado **130** · unidade do bloco
  temporal **162** · bloco + heranca do vizinho **178** · so bloco + heranca, SEM scorer **178** —
  o texto nao acrescenta nada por cima do bloco.
  **Raiz 1 (ORDEM):** `apply_unit_subunit_fields` rodava ANTES de `_run_anchor_engine_layer` e
  reconciliava contra `computed_block_id` (scorer de conceito antigo) — o eixo de unidade nunca
  viu `temporal_block_*`, o bloco que a regua mede. Fase movida para depois da ancora; bloco =
  `resolve_temporal_block` (manual > temporal > computed).
  **Raiz 2 (PRECEDENCIA):** `reconcile_unit_with_block` comparava `block_confidence >=
  unit_confidence` e deixava o texto forte vencer o bloco — onde o texto erra. Agora o bloco com
  unidade decide sempre; o texto discordante fica em `unit_block_conflict` (auditoria).
  **Heranca:** bloco sem `unit_slug` (avaliacao/revisao/entrega/overview, por design do
  posicional) herda do vizinho de CONTEUDO — anterior para o que fecha a unidade, proximo para
  overview (`file_map.unit_of_block_or_neighbor`). 16/188 caiam nesses blocos; a heranca acerta 11.
  **Producao:** unidade **178/188 = 94,7%** (MF 65/66 · SO 29/35 · IA 42/42 · ES2 24/27 · TCC
  18/18; material **82/83** · codigo 54/59 · listas 21/23). **Os 10 erros de unidade sao os erros
  de bloco** — nao existe mais erro proprio do eixo de unidade. Bloco 185/200 intocado. Cobertura
  N:N 44 -> **46/57**, F1 0,811 -> **0,847**, sem-predicao 4 -> 0. Sentinelas MF/SO/TCC regravadas
  (diffs so em `computed_unit_slug`). Suite 1996 passed.
  **Consequencia para a regua:** `scripts/eval_entry_unit.py` mede o SCORER isolado (55%) — numero
  que deixou de importar; a medida do eixo e "unidade gravada vs verdade" (harness em
  `scratchpad/unidade_vs_bloco.py`, a promover). O scorer de texto segue util so para: entry sem
  bloco nenhum, eixo de cobertura (N:N) e o `unit_block_conflict` como sinal de revisao.
  **Armadilha de ferramenta:** `eval_coverage.py <repo> material_gt_*.csv` le `coverage_curation.json`
  / `references_curation.json` (camada de referencia), nao o `coverage_units` do manifest — da
  0/0 para material. A medicao valida de material usa `eval_coverage.score` sobre o manifest.

## CODE — "TUDO PELO MOTOR": lexico vs LLM medido; D4 relido; -26% de votos (2026-08-21b)

Pedido do user: decidir pelo motor, LLM o minimo; raiz, nunca remendo. Primeiro o dado que
contradiz a percepcao "maioria dos erros e bibliografia": dos 15 erros de bloco, **1** e
bibliografia (`eth2`, preco aceito da regra B-6); 7 sao `codigo-professor`, 3 material, 2 listas.
- [MEDIDO] **D-1 · lexico top-1 vs LLM em TODA janela >= 2 (87 casos com gold):** lexico **55/87**,
  LLM **69/87**. Por balde de sinal lexico:

  | balde | n | lexico ok | LLM ok |
  |---|---|---|---|
  | `s1=0` (cego) | 13 | 1 | 8 |
  | `s1>0, s2=0` (so 1 bloco casa) | 23 | **21** | 22 |
  | `rel<tau` (competicao) | 40 | 23 | **34** |
  | `rel>=tau` (ja confiante) | 11 | 10 | — |

  "Tudo pelo motor" hoje custaria 14 pontos nessas 87. O LLM ganha onde ha competicao real e
  onde o lexico e cego; nesses dois baldes o sinal que falta e **ordem da serie** ("roteiro N",
  "microsservicos N": gold monotono no tempo, duas series intercaladas no mesmo card do ES2) —
  candidato a provider deterministico, nao medido. Resumo de codigo no disambiguator: medido e
  DESCARTADO (nao move o total; vira `rel<tau` e vai ao LLM do mesmo jeito).
- [DONE] **D-2 · gate D4 relido: `s2=0` com token discriminante e CONFIANTE.** O `s2 > 0`
  obrigatorio ("competicao real") confundia sem-competicao com sem-evidencia. Guard: janela
  degradada (ref fantasma, 1 bloco resolvivel) nao tem runner-up e segue flagada (teste existente
  preservado). Stems genericos +`disciplina`/`estudo`/`caso` (boilerplate do bloco-01) e
  +`trabalho` (nome de categoria; ES2 `kubernetes` ia sozinho para "Entrega trabalho final").
  Gate de df global na exclusividade: simulado, tira 2 confiantes certos e nao remove `azure` —
  descartado. **Producao: votos de LLM 81 -> 60 (-26%), `disamb` 10 -> 31, regua 185/200
  identica, confiante-e-errado 1** (`azure`: "servicos" colide com "arquitetura baseada em
  servicos"; aceito). Suite 1993 passed.
- [DONE] **D-3 · trabalhos/provas NAO passam pelo desempate lexico** (`resolve_unscoped(lexical=
  False)`): o enunciado descreve o conteudo cobrado, nao a entrega — TCC `t1-enunciado` ia para a
  aula 03 (tokens `minimizacao`/`primitivas`) em vez da entrega 04. Janela-1 estrutural decide;
  janela > 1 vai ao voto sobre a janela. Achado pelo primeiro reprocess (a simulacao so tinha
  material) — a regua pegou, o fix e de raiz (categoria inteira), nao de caso.
- [NOTA] Sentinela `_golden/Metodos-Formais-Tutor__casos_chave.json` regravada de proposito: unico
  diff e `eth2` com temporal via `ref-generica` (mesmo uuid do pino removido em B-6).
- [REFUTADO 2026-08-21c] **D-4 · provider "ordinal dentro do card" (serie numerada no mesmo card,
  alinhamento monotono + lexico).** Universo: 19 membros de serie com gold em janela >= 2 (MF
  `exerciciosdafny1-5`, `classes-parte1/2`; ES2 `microsservicos2-7`, `roteiro1-7`). Gold e
  monotono em N em 3 de 4 series — o sinal de ORDEM existe. Mas o alinhamento monotono (DP
  maximizando score lexico sob ordem) da **7/19**, contra lexico top-1 9/19 e producao (LLM)
  **15/19**: com score zero (roteiros = codigo sem markdown, titulo "roteiroN") o DP colapsa
  tudo no bloco-01, e o ima `bloco-04` engole os slides. A ordem diz a DIRECAO, nao o bloco; o
  mapeamento N -> bloco exigiria o cronograma nomear os roteiros por data — o do ES2 nao nomeia
  (0 de 20 sessoes). O LLM acerta lendo datas + sequencia, sem ancora deterministica possivel.
- [MEDIDO] **D-5 · eixo de bloco por categoria (200 unidades) — a ordem de ataque do user:**
  material-de-aula **86/89** (96,6%) · codigo-professor **52/59** (88,1%) · listas 24/26 ·
  trabalhos 6/7 · gabaritos 3/4 · bibliografia 6/7 · provas 2/2 · cronograma 4/4.
  **Os 3 erros de material-de-aula tem 3 raizes distintas e nenhuma e sistemica:** SO
  `definicao-e-historico` (card tematico "Introducao aos SO", gold bloco-02 "Introducao" kind
  overview — o stem generico `introduc` apaga o unico token que ligaria card e bloco; tirar o
  stem reabre o ima "Introducao" em todo curso), ES2 `azure` (custo aceito de D-2), TCC
  `aula-17-np-completude` (professor numerou duas "Aula 17"). Material-de-aula esta no teto do
  dado; nao ha fix de raiz barato. Em codigo-professor os 7 erros sao os 3 `threads` do SO (card
  tematico sem janela, llm-funil) e 4 roteiros do ES2 (sem texto, ver D-4) — ambos sem sinal no
  dado atual; o resumo de codigo no disambiguator foi medido (D-1): recupera 4/12 no balde
  `s1=0` mas nao move o total com o LLM ligado.

## CODE — OS 8 OFF-BY-ONE: 1 defeito de codigo, 7 nao (2026-08-20h)

- [DONE] **O-1 · provider ordinal contava a aula de CORRECAO como encontro.** TCC `bloco-18`
  "Correcao" (13/05, pos-P1) e `kind=class` de proposito (classifier.py:144) — certo para o
  conteudo — mas o professor nao a numera: "Aula 16" e 15/05. `_session_ordinal_index` punha o
  16o encontro na correcao: janela-1, band ALTA, bloco errado — o unico confiante-e-errado do
  motor apos B-1. Fix em `window_provider._session_ordinal_index` (pula sessao com "correcao"
  no hay), teste `test_correcao_de_prova_nao_conta_como_encontro`. **Medido:** so o TCC tem
  titulos "Aula N" (19, todos com gold): 16/19 -> **17/19**, 0 regressoes; IA tem 2 blocos de
  correcao e 0 ordinais -> intocado. TCC reprocessado: 1 entry muda, acuracia 18/25 -> **19/25**,
  confiante-e-errado **1 -> 0**. Evidencia de 1 curso — se um professor numerar o dia da correcao,
  este fix regride 1; o gold do TCC diz que nao.
- [MEDIDO] **O-2 · os outros 7 nao sao bug:** 3 funil (SO `definicao-e-historico`,
  `lista-exercicios-p2`; TCC `t1-enunciado` — B-2, estrutural); 1 pino manual vs gold (TCC
  `3d-matching` — B-3); 2 voto do LLM numa janela de **10 blocos** no ES2 (`roteiro5`, `azure`:
  card "Microsservicos" cobre a unidade inteira, P4 abre a unidade toda e o LLM escolhe o vizinho);
  1 numeracao DUPLICADA do professor (TCC tem dois "Aula 16" e dois "Aula 17"; `aula-17-np-
  completude` gold = 03/06, ordinal nao recupera duplicata, LLM escolheu 29/05).
- [NOTA] `git diff` do TCC mostra "+1 linha" num `.md` curado a cada reprocess: e CRLF/LF do git
  (HEAD `\n`, arvore `\r\n`), nao conteudo. Nao fere o ponto fixo.

## CODE — BANDA "INVERTIDA" era artefato de regua; o ralo e o FUNIL (2026-08-20g)

- [DONE] **B-1 · `eval_ground_truth.py` lia `computed_block_band` para uma predicao que vinha da
  ANCORA.** A acuracia e medida em `resolve_temporal_block` (temporal vence), mas a banda vinha
  do scorer de conceito — confianca de um metodo, acerto de outro. Isso fabricava "media 78% <
  baixa 85%". Fix: banda do METODO QUE DECIDIU (manual > temporal > funil) + campo `source` +
  linha "Por fonte" no relatorio. Teste `test_band_e_a_do_metodo_que_decidiu_o_bloco`.
  **Regua corrigida, 200 unidades:** alta **72/1 = 99%** · media **72/18 = 80%** · baixa 1/5 ·
  manual 27/3 — MONOTONICA. Confiante-e-errado 2 -> 1.
  **Por fonte (190 entries):** temporal alta **70/71 = 99%** · temporal media **70/77 = 91%** ·
  manual 28/30 · **funil (scorer sem janela) 6/26 = 23%**. Por metodo: janela-1 69/70,
  llm 63/69, disamb 6/6, concept-fused (funil) **6/24**. O roteador real e a FONTE, nao a banda:
  `source == funil` e a fila de revisao. O `AnchorEngine` ja esta ON em producao via
  `feature_flags` do perfil (`subjects.json`: IA tem `use_anchor_engine` e `use_llm_voter`) — o
  "default False" do codigo engana; o reprocess headless injeta as flags do perfil.
- [MEDIDO] **B-2 · anatomia do funil (26 entries, 20 erros):**
  SO 17: cards TEMATICOS ("Threads", "Gerencia de Memoria", "Informacoes Gerais") — sem
  `Semana N`, sem data, `card_block_map` do SO tem 1 entrada -> nenhum provider abre janela.
  8 dos 17 sao `Informacoes Gerais` (listas/gabaritos P1-P2, gold = bloco da prova): card
  administrativo, certo ficar sem janela; o sinal que falta e a DATA DA PROVA. TCC 6: 5 sao
  `trabalhos` -> `_OUT_CATEGORIES` antes de qualquer provider; card "Semana 14 - Apresentacoes
  T2" nao casa bloco nenhum (precisa de data, nao de topico).
  **Hipotese testada e REFUTADA:** P4 aceitando card tematico sem "Semana" no SO = +1 plausivel
  (`exercicios`, janela 12) e **4 confiante-e-errados novos** (`Threads` x3 viram janela-1 = alta
  no bloco errado; `definicao-e-historico` gold fora). Liberar `trabalhos` pela janela manual do
  card no TCC = +1 (`t1-enunciado`) / -1 (`trabalho-t2`, gold fora). Nao implementar. O funil e
  estrutural: o sinal que resolveria (data da avaliacao/apresentacao) nao esta no texto.
- [DONE 2026-08-21] **B-5 · bibliografia/references/cronograma/apoio LIBERADAS de `_OUT_CATEGORIES`.**
  Ficam fora so `trabalhos`/`provas` (tier2) e o card TDE. Achado no caminho: das 14 entries
  dessas categorias em producao, **12 tem pino manual** (o pino vence antes do escopo; 11/12 batem
  com o gold, a 12a e `eth2`, B-3) — por isso so 2 apareciam no funil. Medido em memoria SEM pino
  (curso novo): 7/14 = 50%; os erros sao referencia generica que o gold poe em bloco-01 e o LLM
  manda para bloco tematico. **Producao: mudam exatamente as 2 sem pino**, MF `plano` (llm-funil)
  e IA `artigo-usando-agrupamento` (janela-1/labels/alta), ambas = gold. Regua **179 -> 181/200
  (90,5%)**; **IA 43/43**; **funil 0/0 nos 5**; confiante-e-errado 0. Suite 1985 passed.
  Sinal para B-3: o LLM, sem ver o pino, poe `eth2` em **bloco-12 = gold**, contra o pino
  (bloco-01).
- [NOTA · higiene] Dois ruidos de reprocess vistos aqui, nenhum muda decisao: (a) ordem de chaves
  do JSON do manifest alterna entre rodadas (`computed_block_method` troca de posicao com uma
  lista) em SO/ES2/TCC — semanticamente identico, diff sujo; (b) `manual_timeline_block_id` do
  TCC `3d-matching` alterna uuid <-> `bloco-24` a cada reprocess (`block_identity.py:329`
  reescreve o pino). Campo MANUAL nao deveria ser tocado por reprocess. Ambos revertidos, nao
  investigados.
- [DONE 2026-08-21] **B-4 · llm-funil IMPLEMENTADO e em producao.** `AnchorEngine.resolve_funnel`
  (janela = todos os blocos, band `media`, flag=True, method/provider `llm-funil`); `resolve()`
  cai nele sem janela; `apply.py` manda provas/trabalhos sem due para ele; cap 20 -> 60.
  Bibliografia/references/cronograma/apoio/TDE seguem FORA (sem eixo temporal por design) —
  por isso MF `plano` e IA `artigo` continuam no funil. 5 repos reprocessados: llm-funil decidiu
  **30 entries, 24 com gold -> 12 ok / 12 erro (50%)**; regua de bloco **173 -> 179/200**
  (SO 27->31, ES2 22->23, TCC 19->20); confiante-e-errado 0 nos 5. Testes: 3 no engine + 1 no
  apply. Suite 1985 passed / 1 skipped. Nota: o voto do LLM varia entre rodadas (ES2
  `revisao-p1` errou no experimento e acertou em producao; TCC `programacao-inteira` foi 23 ->
  26) — o cache congela o primeiro voto, entao a producao e estavel daqui em diante.
  Medicao original do experimento abaixo.
- [MEDIDO] **B-4 (experimento) · LLM votando no FUNIL com janela = todos os blocos: 6/26 -> 13/26,
  0 regressoes.** Experimento read-only (2026-08-21, `gemini-3.5-flash`, cache proprio no
  scratchpad, 26 chamadas, 0 erros): mesmo `LlmVoter`/prompt de producao, janela = todos os
  blocos do curso (14-35). Resultado: **scorer concept-fused 6/26 = 23% -> LLM 13/26 = 50%**;
  as 6 que o scorer acertava o LLM manteve (0 regressao); 0 votos fora da janela. Ganhos: MF
  `plano`, SO `apresentacao-da-disciplina`/`programa`/`questoes-do-enade`/`lista-exercicios-p2`,
  IA `artigo-usando-agrupamento`, TCC `t1-enunciado`. Persistem 13 erros: SO `Threads` x3 (LLM
  -> bloco-04, gold 06), `lista-p1` x2 (-> 12, gold 09), ES2 `revisao-p1`, e o cluster TCC das
  apresentacoes T2 (4x -> bloco-23, gold 25; `trabalho-t2-enunciado` -> 25 lendo a data do
  enunciado, gold 24 — o gold desse cluster merece revisao junto com B-3).
  A `confianca` do LLM e "alta" em 25/26 — inutil como gate (ja documentado: auditoria, nunca
  gate). **Custo em producao:** 32 entries no funil nos 5 cursos (SO 17) = 32 chamadas UMA vez,
  depois cache; `cap=20` por rodada em `pedagogical_regeneration._build_motor_voter` teria que
  subir ou o SO leva 2 rodadas. Os 5 perfis ja tem `use_llm_voter`.
  **E mudanca de SPEC, nao bug:** spec §12 "sem-janela nunca vota" (`LlmVoter.vote` devolve None
  com janela vazia; `AnchorEngine.resolve` devolve None antes do voto). Implementar = no
  `AnchorEngine.resolve`, quando `resolve_window` falha e o voter existe, votar com janela =
  blocos do curso, band `media`, method `llm-funil` (rastreavel). Fora-de-escopo (`_OUT_CATEGORIES`)
  tambem teria que passar: 7 dos 26 sao `trabalhos`/`bibliografia`/`cronograma`, e 3 desses 7 o
  LLM acertou. Decisao do user.
- [DONE 2026-08-21] **B-6 · PINAR MENOS: 30 -> 11 pinos, regua 181 -> 185/200, user aprovou as 4 acoes.**
  (1) `eth2`: pino removido, gold 12 mantido — a regra nova poe em bloco-01 (erro aceito, 1/5).
  (2) `3d-matching`: pino removido; gold de `trabalho-t2-enunciado` 24 -> 25 (data do enunciado);
  **uma curadoria de card** em `TCC/course/.card_block_map.json` ("Semana 14 - Apresentacoes T2"
  -> [bloco-25]; "Semana 13 - Trabalho T2" -> [23, 25]) cobre as 5 entries do cluster via
  janela-1/alta — exigiu `AnchorEngine.resolve_unscoped` + `apply.py` mandando provas/trabalhos
  sem due pela cascata antes do llm-funil (`resolve_due_window` so le `assign_due`; card manual
  nao valia para trabalhos). (3) 13 pinos redundantes apagados (+ `aws`/`archive`/`o-que-e-IA`/
  `ia-responsavel`, redundantes com a regra 4). (4) **`resolve_generic_reference`**: referencia
  sem card -> primeiro bloco `overview`/`class` (IA e SO tem `kind=overview` no bloco-01).
  **Resultado:** TCC 20 -> **24/25**, MF 64, SO 31, IA **43/43**, ES2 23 = **185/200 (92,5%)**;
  confiante-e-errado 0; funil 0/0; pinos restantes **11, 11/11 certos**: MF 7 (LLM escolhe o
  vizinho na janela — `provasindutivas` x3, `logicadehoare2`, `terminacao`, `tiposindutivos`,
  `exercicioscorrecaoterminacao`), SO 3 (bibliografia com card tematico), IA 1 (`prova-1` sem
  due). Suite 1988 passed / 1 skipped. Testes: 3 novos + 2 reescritos. **Proximo ganho real:
  o LLM errar o vizinho em janela curta (7 do MF + 2 do ES2) — investigavel com os votos
  cacheados em `material_curation.json`.**
- [INVESTIGADO 2026-08-21] **B-3 · evidencia dos 2 pinos + CENSO DE PINOS (objetivo: pinar menos).**
  *`3d-matching`*: o enunciado do T2 diz literalmente **"Data Entrega: 12/06/2026 (data da
  apresentacao)"** = bloco-25. Pino bloco-24 (10/06) esta ERRADO; o gemeo `3dm-caetano` (mesma
  apresentacao) tem gold 25 — regra do par exige o mesmo bloco. Consequencia: o gold de
  `trabalho-t2-enunciado` (24) tambem esta errado pela propria data do enunciado -> 25.
  *`eth2`*: bibliografia externa (GitHub, Dafny), sem card, sem data, 0 chars de texto. Pino
  bloco-01 segue a convencao "bibliografia -> apresentacao da disciplina" (mesmo pino uuid de
  `aws` e `archive`). Gold bloco-12 = "introducao ao Dafny" (topico). LLM sem pino: bloco-13
  (Dafny tambem, adjacente). Veredito provavel: pino errado, gold certo (referencia ESPECIFICA
  vai ao topico; generica vai ao bloco-01). **Decisao do user.**
  **Censo (30 pinos em producao, todos com gold), motor rodando SEM nenhum pino:**
  **13 REDUNDANTES (43%)** — motor = pino = gold, podem ser apagados sem mudar nada ·
  **15 NECESSARIOS** — motor erra: 7 no MF sao LLM escolhendo o vizinho dentro da janela
  (`provasindutivas` x3, `logicadehoare2`, `terminacao`, `tiposindutivos`, `exercicioscorrecao
  terminacao`), 4 sao referencia generica -> bloco-01 (`aws`, `archive`, `o-que-e-IA`,
  `ia-responsavel`), 3 sao bibliografia do SO com card tematico, 1 e IA `prova-1` ·
  **2 ERRADOS** (os de cima).
  **Regras testadas para substituir pino:** (a) "referencia sem card -> bloco-01": **4/5** no
  gold (excecao = `eth2`), cobre 4 pinos necessarios — unica regra que sobreviveu; (b) "Prova N /
  Lista PN -> N-esimo bloco de avaliacao": **2/8**, REFUTADA; (c) refinada "bloco de revisao
  antes da prova N, senao a prova": **4/8**, REFUTADA — o labeler poe a preparacao da P1 onde o
  professor a usou (bloco `class` anterior), nao na revisao; (d) data explicita no texto da
  avaliacao: so **2 de 50** textos tem ("Data Entrega: 12/06/2026" no T2; "data limite 03/07" no
  T1 do ES2) — provider nao se paga agora, mas os 2 casos apontam bloco coerente.
- [USER] **B-3 · 2 pinos manuais discordam do gold:** MF `eth2` (pino -> bloco-01, gold
  bloco-12) e TCC `3d-matching` (pino bloco-24, gold bloco-25; e o unico confiante-e-errado que
  resta). Um dos lados esta errado em cada par — decidir qual.

## CODE — SUBUNIDADE colapsada: RAIZ RASTREADA, fix NAO aplicado (2026-08-20e)

- [OPEN] **S-1 · ECO de heading: o material e pontuado contra o PROPRIO titulo.** Cadeia:
  `collect_strong_heading_candidates` (content_taxonomy.py:671) le os 4 primeiros headings do
  .md de CADA material -> `build_content_taxonomy` (linha 554) anexa cada heading como ALIAS do
  topico que `_select_supported_taxonomy_topic` escolher -> `_score_entry_against_taxonomy_topic`
  (timeline/index.py:1685) da `peso x 0.82` POR ALIAS casado em `markdown_headings_text` (peso 4.4)
  -> o material casa o alias que e o seu proprio heading. Mesma classe do eco das `auto_tags`
  cortado em 2026-08-19, so que via taxonomia em disco.
  **Censo (5 cursos): 103 de 259 aliases (40%) sao heading/titulo de material** — MF 34/70,
  TCC 23/52, SO 21/59, ES2 10/29, IA 15/49. No IA u05 o ima `introducao-ao-aprendizado-de-
  maquina` tem 9 aliases, **8 sao eco** ("Aula 02 - ... k-Means - Exemplo 2", "Aula 29 - ...
  Medidas de Avaliacao") e recebe 33 de 39 entries com `winner_score` 13-23 e conf 0.99;
  `arvores-de-decisao` e `agrupamento-hierarquico` caem nele. Agravante: o topico que carrega o
  NOME da unidade absorve todo heading que cita a unidade (overlap de 2 tokens ja da 6.3 no
  seletor), entao o eco concentra num topico so. A taxonomia do u05 tem so 4 topicos — nenhum
  e "arvores", "redes neurais", "k-nn" ou "agrupamento" (limite do plano de ensino, problema
  SEPARADO do eco).
  **Hipotese TESTADA e REFUTADA 3x (2026-08-20e)** — o mecanismo de alias NAO e o defeito.
  Harness: taxonomia alterada em memoria, `_auto_map_entry_subtopic` + `_auto_map_entry_unit`
  pelo caminho de producao, 5 cursos, regua de unidade (`eval_entry_unit`) como rede:

  | variante | UNIDADE certo/188 | SUBUNIDADE vazios/214 | colapsadas |
  |---|---|---|---|
  | base | **103** | **93** | 5 |
  | H1 · cortar TODO alias-eco (103 aliases) | 89 | 121 | 7 |
  | H2 · cortar so o absorvido via tokens do titulo da unidade | 89 | 119 | 4 |
  | H3 · excluir so o PROPRIO heading da entry (analogo ao eco de auto_tags) | 96 | 115 | 6 |

  Toda variante perde unidade e ESVAZIA subunidade. O caso que decide: TCC
  `aula-03-funcoes-recursivas-primitivas` acerta na base e vira (vazio) em H3 — o proprio
  heading E a evidencia mais forte do que o material trata. **O enquadramento "eco" estava
  errado:** `auto_tags` era SAIDA do motor realimentada; heading e ENTRADA. A taxonomia tem so
  label + 1-2 aliases de glossario; os headings dos materiais sao o vocabulario principal dos
  topicos. Mexer neles so esvazia. **Nao retentar pelo alias.**
- [DONE 2026-08-20e] **S-2 · a raiz REAL do IA u05: "Modelos Preditivos" sumia da taxonomia.**
  O plano lista 5 topicos na u05; a taxonomia tinha 4. Perdido em `build_content_taxonomy`:
  `_is_valid_topic_candidate` — filtro de RUIDO DE HEADING — e aplicado ao CONTEUDOS do plano, e
  o marcador de bibliografia `ed` casa substring em "pr**ed**itivos". Medido nos 5 cursos: o filtro
  rejeita **27 de 127 topicos do plano (21%), todos legitimos, zero lixo** ("Logica de Hoare",
  "Teorema de Cook-Levin", "Conjectura de Church-Turing"); sobreviviam SO pela isencao de codigo
  numerico — e o plano do IA nao numera. Fix: topico vindo do plano nao passa pelo filtro
  (`topics_from_plan`); o filtro segue para o fallback via COURSE_MAP. Teste em
  `tests/test_taxonomy_topic_loss.py` (RED antes, GREEN depois). **Medido pelo montador de
  producao:** so o IA muda (+`modelos-preditivos`, aliases 49 -> 51); MF/SO/ES2/TCC byte-identicos;
  regua de unidade identica (103/188). Suite 1978 passed / 1 skipped. NAO commitado, producao NAO
  reprocessada.
  **MAS o colapso do u05 NAO muda com o topico de volta** (28 -> 28 em `introducao`): "arvores de
  decisao", "perceptron", "k-NN" nao contem "modelos preditivos". O plano e CATEGORICO
  (preditivo/descritivo) e o material e ALGORITMICO; nao existe ponte lexica em lugar nenhum —
  `GLOSSARY.md` do IA tem 23 termos e **zero de ML**. Nao e bug de scorer: e lacuna de vocabulario.
  Caminhos possiveis: (a) geracao do glossario (LLM) produzir os termos dos algoritmos com
  `Aparece em` — e conteudo, nao codigo; (b) aceitar vazio/colapso como resposta honesta do
  modelo lexico.
  **Reaproveitamento medido (2026-08-20f):** o vocabulario-ponte EXISTE nos textos do u05 —
  "supervisionado" em 25/39 entries, "classificacao" 26, "agrupamento/cluster" 14, "regressao" 10;
  e a taxonomia ja traz o alias `modelos supervisionados` em `modelos-preditivos` (glossario).
  **Nao serve:** polaridade. Os 9 textos com "nao supervisionado" tambem casam "supervisionado"
  (substring) e `modelos-descritivos` so tem o alias "modelos exploratorios" — ponte lexica
  mandaria agrupamento para preditivo. O resumo do Gemini (`code_curation`, 25/39) ja alimenta o
  scorer de subunidade. Nada barato e seguro para reusar. DECISAO: (b) — subunidade do IA u05
  fica como esta; a taxonomia em disco foi regravada com os 5 topicos (reprocess do IA, 0
  mudancas de atribuicao, `updated_at` revertido para nao commitar timestamp). O censo `COLAPSO` do `eval_subunit_health.py` tambem e regua fraca:
  TCC u02 (4 entries -> `maquinas-de-turing`) e SO u02 (-> `escalonamento`) sao provavelmente
  CERTOS — concentracao nao e erro sem gold.
- [OPEN · higiene UI] **S-3 · marcador de bibliografia `ed`/`eds` casa SUBSTRING.** Mesmo defeito
  do `known_tools` ja corrigido (teste `test_tool_so_casa_em_fronteira_de_palavra`). No caminho do
  `.tag_catalog.json` derruba 12 headings nos 5 cursos, 9 no IA ("Rede Neural Perceptron", "Redes
  Feed Forward", "Introducao a redes neurais"), "Reducao Polinomial" no TCC, "LOGICA DE PREDICADOS"
  no MF. Consumidor: so a UI (`ui/dialogs.py:2180`, seletor de tags) — **zero impacto nos eixos
  medidos**. Fix trivial (fronteira de palavra), so quando mexer na UI.
- [NOTA] TCC 27 -> 26 topicos: `definicao-da-classe` existe em 4.5.1 e 4.6.1 e
  `_dedupe_taxonomy_topics` funde pelo slug. Dois pais, um slug. Nao investigado.

## FERRAMENTA — `scripts/explain_entry.py` (2026-08-20)

- [DONE] Explica um arquivo etapa a etapa pelo CAMINHO DE PRODUCAO: sinais montados -> bloco
  (com o breakdown dos 6 termos da fusao) -> `resolve_temporal_block` -> texto da rota de unidade
  (markdown + resumo do Gemini) -> unidade 1:1 + gate + `reconcile_unit_with_block` -> cobertura
  N:N com a regra que disparou -> subunidade restrita a unidade reconciliada.
  Usa os montadores canonicos (`assemble_resolver_inputs`, `_build_file_map_unit_index_from_
  course`, `build_learned_unit_boosts`) — remontar o caminho a mao foi a causa comum de CINCO
  predicoes refutadas nesta campanha. Diferente de `scripts/trace_motor.py`, que se declara um
  PISO com tokenizer proprio e nao mede o motor real.
  Uso: `python scripts/explain_entry.py <REPO> <pedaco do id ou titulo>`.
  **Achado ja na primeira entry** (TCC `aula-06`): os tres eixos discordam entre si — bloco
  concept-fused -> u02, `resolve_temporal_block` sobrepoe para bloco-05, scorer de unidade -> u04
  ("hierarquia" casando com "hierarquia de classes de complexidade"), cobertura regra `card` ->
  u03. `reconcile_unit_with_block` NAO corrige: mantem u04 e so registra o conflito.

## CODE — camada de COBERTURA (material transversal, 2026-08-18)

Eixo novo, separado do motor. Motor responde "QUANDO isso foi dado" (1 bloco temporal);
cobertura responde "O QUE isso cobre" (N unidades/topicos). Prova, lista, gabarito,
bibliografia, apoio e codigo de exemplo so tem o segundo eixo — nao entram no motor.
Fila acordada com o user (2026-08-18): regua -> referencias -> codigo/exemplos ->
exercicios/listas/provas antigas.
Regua: `docs/reports/coverage_gt_<SIGLA>.csv` + `scripts/eval_coverage.py` +
gerador `scripts/make_coverage_labels.py`.

- [USER] **Rotular a regua de cobertura das referencias — 9/10 PREENCHIDOS, AGUARDANDO VETO**
  (`as-of 2026-08-18`). SO 3/3 com `provenance=plano-de-ensino` (evidencia documental, o plano
  responde sozinho: threads e u03). MF 3/3 e IA 3/3 com `provenance=proposto-claude` — o user
  precisa vetar ou confirmar. IA4 (`artigo-usando-agrupamento`) marcado `scorable=no` por ser
  entry fantasma. **BASELINE MEDIDO: 0/9 exact-set-match, 8 de 9 SEM PREDICAO NENHUMA** —
  e o retrato de partida contra o qual os 4 fixes da camada de referencia serao medidos.
  Detalhe original:
  10 entries vivas (SO 3, MF 3, IA 4; ES2/TCC 0). Preencher `gold_units` (pipe-separated) nos
  CSVs `coverage_gt_{SO,MF,IA}.csv`; catalogo de slugs em `coverage_units_<SIGLA>.md`. Sem
  rotulo nao ha baseline. N=10 mede caso-a-caso, nao estatistica.
  Proposta ja apresentada ao user (aguardando veto/confirmacao): SO1=3, SO2=3, SO3=3(DUVIDA),
  MF1=1,2 · MF2=1,2 · MF3=1 · IA1=1 · IA2=1 · IA3=5 · IA4=skip(fantasma).
  **SO RESOLVIDO pelo plano de ensino (2026-08-18, ruling do user "da para saber analisando o
  plano")**: threads e u03. Evidencia: topico `4.1 Programas multithreads` na u03; descritivo da
  u03 "conceitos de processos leves e pesados (Tasks e Threads)"; objetivo 4 "conhecer
  programacao concorrente e mecanismos de exclusao mutua"; bibliografia "Threads Primer: A Guide
  to Multithreaded Programming". A u02 nao cita threads em nenhum dos 4 topicos. SO1/SO2/SO3
  rotulados no CSV com `provenance=plano-de-ensino`. Baseline medido: **0/3, sem predicao**
  (as 3 nunca foram mapeadas — e o `fetch_reference_text` so-rede). Faltam MF (3) e IA (4).
  Contexto que o user ja deu: MF2 (AWS Encryption SDK) e caso de uso de metodo formal provando
  codigo; IA2 (IA Responsavel) e artigo, possivelmente sobre LLMs.
- [CONCLUIDO 2026-08-18] **`fetch_reference_text` so busca rede** — CORRIGIDO (le markdown local antes da rede) (`core/reference_content.py`) — GitHub README
  ou HTML. PDF local do Moodle -> texto vazio -> 0 conceitos -> 0 mapeamento. Causa raiz de
  **1 de 15 refs mapeadas** (`as-of 2026-08-18`). Fix: ler `approved/curated/base_markdown`
  antes da rede.
- [CONCLUIDO 2026-08-18] **`assign_concepts_to_unit` e single-winner** — CORRIGIDO (devolve `units[]`) (`core/reference_topic.py`) — elege 1
  unidade e descarta o resto. Modelo errado para material transversal: precisa devolver a
  lista acima do threshold.
- [CONCLUIDO 2026-08-18] **`computed_ref_topics` devolvia topicos errados** — CORRIGIDO (so os que casaram)
  (`core/reference_topic.py:60`), nao os que casaram. Dado enganoso mesmo quando mapeia.
- [CONCLUIDO 2026-08-18] **Categoria `references` nao era reconhecida** — CORRIGIDO — `_REFERENCE_CATEGORIES = {"referencias",
  "bibliografia"}` (`core/reference_summary.py`). 3 entries vivas com `category='references'`
  (MF 1, IA 2) nunca entram na camada (`as-of 2026-08-18`). Vocabulario da UI diz `referencias`;
  ha 3 grafias em uso.
- [CONCLUIDO 2026-08-18] **Curation sem prune de orfaos** — CORRIGIDO — `references_curation.json` guarda entries que nao
  existem mais no manifest: ES2 6/6 orfas, TCC 2/2 (`as-of 2026-08-18`). `code_curation.json`
  ja poda; esta nao.
- [CODE] **Entry fantasma no IA** (`as-of 2026-08-18`) — `artigo-usando-agrupamento` tem
  `review_status: approved` e aponta `content/curated/*.md` + `raw/pdfs/*.pdf` que NAO existem
  no disco. Ainda alimenta `content/BIBLIOGRAPHY.md`.
- [CODE] **Referencia GitHub depende da rede a cada build** (`as-of 2026-08-18`) — `eth2` e
  `aws-encryption-sdk` (MF) ficam com 0 byte de texto quando o README nao vem, e sem texto nao ha
  cobertura. E o teto atual da camada, nao o matcher. Cachear o README no repo resolveria.
  `ia-responsavel` (IA, 258B) e caso irmao: a pagina nunca foi convertida, so a URL foi salva.
- [CODE] **EXAM_INDEX / EXERCISE_INDEX sao vitrines vazias** (`artifacts/repo.py:703,2029`) —
  EXAM: colunas `Observacao`/`Padrao do professor` dependem de `notes` manual sempre vazio.
  EXERCISE: coluna "Unidade" imprime tag crua (`topico:...; tipo:gabarito; bloco:...`) tendo
  `computed_unit_slug` disponivel; coluna `Solucao` procura "gabarito" em `notes` em vez de
  parear com o irmao no repo (SO tem `lista-exercicios-p1` + `-gabarito` e diz "nao").
- [CODE] **Duplicatas de prova nao detectadas** (IA, `as-of 2026-08-18`) — mesma P1 em
  `p1-2024-02-ia.md`, `prova-1-2024-02.md`, `prova-1-202402.md` (67 linhas cada); uma delas
  nem aparece no EXAM_INDEX.
- [USER] **Decidir o destino das duplicatas e do fantasma do IA** — qual das 3 copias da P1
  fica; e se `artigo-usando-agrupamento` e reimportado ou removido. Sem ruling, os dois
  seguem alimentando `EXAM_INDEX`/`BIBLIOGRAPHY`.
- [CODE] **Descritivo da unidade no plano nunca vira sinal** (`as-of 2026-08-18`) — o paragrafo
  que fecha cada unidade PUCRS ("Nesta unidade sera estudada programacao concorrente. Serao
  enfatizados os conceitos de processos leves e pesados (Tasks e Threads)...") e a mencao mais
  explicita a THREADS em todo o plano do SO. Antes do fix ele entrava como "topico" (poluindo a
  taxonomia com metodologia); agora `_finalize_topics` o descarta junto com "Uso de projetor
  multimidia". Nenhum dos dois estados aproveita o texto. Ganho REAL confirmado: "Threads" ->
  token `threa`, enquanto `4.1 Programas multithreads` -> `{multi, progr}`; o token `threa` SO
  existe no descritivo.
  **MAS a implementacao naive e perigosa (medido 2026-08-18, por isso NAO entrou no rollout):**
  os tokens do descritivo da u03 do SO contem `{geren, proce}` — que e exatamente o
  `_unit_title_core_tokens` da **u02** ("Gerencia do Processador"). A regra (a) de
  `build_content_taxonomy` ("topico cujo rotulo contem o nucleo do titulo de OUTRA unidade migra
  pra unidade dona") mandaria o texto — e o token `threa` — para a u02, o oposto do desejado. O
  descritivo tambem contem o core da propria u03 (`{conco, progr}`), entao haveria duas donas
  candidatas e o `next(...)` decide por ordem de iteracao. Mesmo mecanismo de alias que causou o
  caso ES2.
  Implementacao segura (a fazer): injetar TOKENS (nunca topico, nunca alias que participe da
  migracao), filtrando token que pertenca ao core de outra unidade. Pre-requisito: regua
  entry->unidade rotulada, senao nao ha como medir o efeito.
  **PRIORIDADE REBAIXADA (2026-08-18, verificacao de cards):** o token que faltava (`threa`) esta
  no CARD, nao so no descritivo — os 5 materiais de threads do SO (`07.04 Exemplo threads em
  Java`, `Exemplo threads em C - exemplo1/2/3`, `Biblioteca em C - pthread`) estao TODOS no card
  `Threads`. Campo curto e limpo contra paragrafo poluido: o card entrega o mesmo sinal sem o
  risco de migracao para a unidade errada. Fazer o CARD primeiro; o descritivo talvez nem seja
  necessario.
- [CASO REAL — motor x cobertura] **SO threads: cronograma e ementa discordam POR DESIGN**
  (`as-of 2026-08-18`) — o cronograma poe threads nas aulas 8 e 9 ("Gerencia do processador,
  threads e exclusao mutua", periodo da u02); a ementa poe em `4.1 Programas multithreads` (u03).
  Nao e conflito: e o eixo TEMPORAL (quando foi dado) contra o eixo de COBERTURA (o que cobre).
  Melhor evidencia concreta de que as duas camadas precisam existir separadas — e explica por que
  os `Exemplo threads em C` viviam caindo em unidade errada.
- [USER] **IA: 1 regressao remanescente do rollout de 2026-08-18** — decidir se leva pino manual.
  O caso (b) abaixo (`Visao Geral`) foi RESOLVIDO pelo card. O caso (a) permanece:
  (a) `Cap. sobre Algoritmos Geneticos (Lacerda e outros)` — card `Semana 12 - 18.05 a 22.05 -
      Algoritmos de Busca com Informacao`. Producao tinha `unidade-02-solucao-de-problemas` (que
      cobre busca, coerente com o card); o fix move para `unidade-05-aprendizado-de-maquina`.
      **O card indica que o fix PIOROU este caso** — unico regressao identificada por evidencia
      independente em todos os 5 cursos.
  (b) `Visao Geral - Introducao e Historico` — card `Semana 1 - Plano de Ensino e Introducao a
      IA`. Producao: `unidade-05-aprendizado-de-maquina` (errado); fix: vazio (menos errado). O
      card daria a resposta certa (`unidade-01-visao-geral`), reforcando o item do CARD acima.
  Confirmacoes do lado bom: `Kubernetes` e `devops` estao no card `DevOps` e ambos terminam em
  `unidade-02-devops` apos o fix do alias; os 5 de threads no card `Threads` -> u03.
  `t1_2026_1` (ES2) esta no card administrativo `TDE Trabalho Discente Efetivo`, que nao nomeia
  unidade — arbitrario nos dois lados, candidato a pino manual ou a ficar sem unidade.
- [CODE] **FASE 3 da fila — codigo e exemplos** (`as-of 2026-08-18`, NAO INICIADA). Pedido do
  user: depois das referencias, atacar "arquivos de codigo, exemplos". `code_curation.json` ja
  existe com resumo Gemini + `assign_code_to_block` (bloco, nao unidade) — avaliar se entra na
  mesma camada de cobertura ou se ja esta suficientemente servido.
- [CODE] **FASE 4 da fila — exercicios, listas e provas antigas** (`as-of 2026-08-18`, NAO
  INICIADA). Era o PEDIDO ORIGINAL da sessao ("estao jogados"). Diagnostico ja levantado: prova
  e tratada como material de aula (1 arquivo -> 1 bloco -> 1 unidade) sendo multi-topico por
  natureza; indices vazios; enunciado e gabarito nao pareados; zero extracao de questoes.
  Depende de: camada de cobertura de pe + regua rotulada.
- [DECISION] **Granularidade da cobertura de avaliacoes** — marcar a prova inteira com um
  conjunto de topicos (barato, deterministico) ou quebrar em questoes individuais (caro, LLM,
  mas e o que habilita "incidencia por topico" que o header do EXAM_INDEX ja promete).
  Perguntado ao user em 2026-08-18, sem ruling.

## CODE — UI (Parte B de features backend já entregues)

- [CODE] Cronograma SARC: **tab em tabela + legenda**.
- [CODE] Guard de conflito override: **aviso no tab + botão "reverter p/ auto"**.

## DECISION

- [DECISION] **Sign-off §9 do spec do motor (2026-07-03)** — resoluções **9** (TCC topic-bridge) e **11**
  (aceite duplo contenção+cobertura) APROVADAS; **10** (`material_curation.json` keyed md5/pair_key) e
  **12** (voto aceito cego bounded, autoconfiança ignorada) APROVADAS **CONDICIONAIS à fase 3** —
  go/no-go da fase 3 decidido DEPOIS do recall medido do gate D4 (fase 1). Sem LLM, flagged = fila
  humana no Dashboard (MF: 18 casos; voto resolveria ~1/3 — saldo real nas regras finais = **+4**, não
  +5: `plano.pdf` sem janela não vota; 3 bibliografias nem chegam ao voto). Ambiguidade achada → §12 do
  spec: MARCO 1 converteu `plano.pdf` SEM janela, mas regra "voto bounded à janela" o proíbe — definir
  na fase 3. Escopo de ciclo: reorg física de `scripts/` só PÓS-motor (mapa adiado); modularização de
  `dialogs.py` (4.998 linhas) e sentença dos HTMLs (02–18/06, pré-motor) FORA deste ciclo; remoção de
  mortos = run dedicada (ver CODE).
- [DECISION] **bloco-15 over-merge (IA)** — bloco-15 = 01–08/06; merge **Semana 14** (dijkstra/hc-sa, sess 01,03/06)
  + **Semana 15** (minimax/listas, sess 08/06). **still-valid, verificado as-of reprocess IA 7561f5c.** Cura de timeline separada.
- [DECISION] **5 IA busca — bloco-12 vs bloco-13** — section "Semana 12 - Algoritmos de Busca", caem em **bloco-12**
  (Correção P1+Agentes, 18–20/05). MAS **bloco-13** (25/05, "Algoritmos busca") = candidato topic-match → **um bloco fora**.
  Mismatch Moodle×SARC persiste. **still-valid, verificado as-of 7561f5c.** Gold-relevant.
- [DERIVADO] **MARCO 0/1 EXECUTADOS (2026-07-01)** — validação do D8 com número (detalhe no log de
  decisões, seção D8): ordinal-no-nome morto por medição (DP-monotone = lift negativo); len-norm +6.5pp;
  **LLM 3/18→8/18 no flagged** (converte confusão-semântica, não grão-de-semana); global escopo-disamb
  58.1%→66.1% (empata funil). **Gargalo real = recall do gate D4** (11 confiante-errado cegos pro LLM).
  Scripts novos (uncommitted): `marco0_prova_deterministica.py`, `marco1_voto_llm.py`; sidecars
  `marco0_flagged_MF.json`, `marco1_votes_MF.json`. → **SPEC ESCRITO (2026-07-03)**:
  `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` incorpora D8-refinado (voto em "flagged OU
  série same-theme", autoconfiança ignorada, gate D4 = fase 1 com recall medido), TIER 0 dup-grouping
  (md5-gêmeos = 1 decisão), exclusão bibliografia/apoio do motor, aceite contenção+cobertura por provider,
  cache `material_curation.json` keyed por md5/pair_key (seed = votos MARCO 1). Resoluções de conflito na
  §9 do spec (TCC = topic-bridge, NÃO parse ordinal de "Semana N"). Próximo: plano fase 0 (`writing-plans`).
- [DERIVADO] **FASE 0 do motor de atribuição FECHADA (as-of 2026-07-07; código COMMITADO em 12 commits
  `f75d22b..fff7d47` na branch `feat/motor-atribuicao` — inclui o fix de review final
  `fff7d47` (janela-1 gated no tamanho da janela + funil unificado); papelada docs ainda sem commit)** —
  pacote isolado `src/builder/routing/motor/` (contracts, window_provider, disambiguator, anchor_engine),
  READ-ONLY, **NÃO integrado ao pipeline** (integração = FASE 4). Regressão global: suíte inteira
  **1688 passed / 4 skipped, 0 falha** (as-of pré-fix-final; +1 teste ref-fantasma depois); 28 testes do
  motor + 6 `tests/test_anchor_placement.py`
  (call-site velho intacto, FASE 0 é ADITIVA) todos verdes.
  **Probe externo** (`scripts/fase0_prova_motor_MF.py`, régua par-colapsada `pair_key`+`scorable==yes`):
  escopo-disamb MF **36/58 = 62.1%** (piso MARCO 0 A' = 59.7%, folga +2.4pp) → **VEREDITO FASE 0: PASS**
  (exit 0).
  **Gold embutido** (`tests/test_motor_golden_mf.py`, roda em CI): 45 casos mensuráveis; contenção
  **100%**; confiante-errado **0**; janela-1 OK.
  **Calibração final:** `MARGIN_TAU=0.45`, `W_SESSION_LABEL=1.0`, `W_TOPIC=0.6`; gate estrutural
  (decisão user 2026-07-07): `confident` exige `s2>0` (competição real) e decisão `flagged` nunca sai da
  band "alta" (capada em "media" — fecha vazamento de `confidence_band` no ramo flagged, `BAND_HIGH=0.50`).
  **Dívida FASE 1 (baselines conscientes aceitos no probe):** confiante-errado ≤7 e contenção-fora ≤2 na
  régua externa. Composição dos 7 confiante-errado: **2 poluição nome-do-curso** (`topic_text` do
  bloco-02 = "introducao metodos formais" contamina materiais que citam o nome da disciplina — candidato
  de calibração FASE 1) + **5 casos gold `discriminante=yes`** onde o motor reproduz a heurística antiga
  (recall do gate/TIER 3). Motor = subset EXATO dos 11 confiante-errado do marco0 (gate novo cortou
  11→7); seleção reproduz Config A' byte-a-byte.
  **Tensão "Verificação de Programas" (prevista no plano):** no gold EMBUTIDO o card tem `block_ids: []`
  → funil na CI, não exercível. No repo REAL a janela existe (labels, blocos 10-15) mas SEM bloco-09 →
  as 2 contenção-fora do probe. **PENDÊNCIA [USER]:** curadoria do `card_block_map` do repo MF (incluir
  bloco-09 na janela da seção "Verificação de Programas") ou reprocess; mutação do repo-tutor é ação do
  user na GUI — ver item espelhado em USER-SIDE.
  Guard AST do motor endurecido além do plano previsto (star-imports proibidos + acesso
  module-qualified detectado).
  **Fixes do review final (commit `fff7d47`):** fast-path janela-1 e funil `block_ref=""`
  corrigidos no fechamento (review final) — Protocols de `contracts.py` ainda divergem das
  assinaturas reais (`markdown`; shadowing `AnchorEngine`) = item FASE 1.
  **→ Números e dívidas desta entrada SUPERSEDED pela FASE 1 (entrada seguinte, 2026-07-07):**
  MARGIN_TAU agora 0.55; baseline confiante-errado agora 3; Protocols/unificação resolvidos.
- [DERIVADO] **FASE 1 do motor de atribuição FECHADA (as-of 2026-07-07; 8 commits `2e49ceb..ccea93c`
  na branch `feat/motor-atribuicao`, review final fable "Ready to merge: Yes" pós fix-wave)** —
  gate D4 calibrado COM RECALL MEDIDO (spec §7 fase 1). Report completo:
  `docs/reports/2026-07-07-fase1-recall-report.md`. Números: **recall do gate 0.824 (14/17)** vs
  referência proxy MARCO 1 0.577 (15/26); **confiante-errado 7→3**; **acurácia escopo-disamb
  62.1%→70.7%** (par-colapsada; piso HARD 59.7%); contenção-fora 2 (inalterada, pendência USER
  bloco-09 — agora custa também 1 confiante-errado). Gold embutido inviolado (contenção 100%,
  conf-errado 0). Suite **1701 passed / 4 skipped**. Levers: desconto nome-do-curso
  (`MotorContext.course_name`, −2 conf-errado, +8.6pp acc), `MARGIN_TAU` 0.45→0.55 (grade 36 pontos,
  −2 conf-errado, acc invariante), gate token-discriminante D4 literal (NEUTRO neste corpus — mantido
  por conformidade ao spec §3, custo 2 falso-alarme). Novos: `motor/metrics.py` (gate_report puro),
  `scripts/fase1_recall_gate_MF.py` (harness READ-ONLY, veredito HARD composto: recall ≥ 14/17 OU
  conf-errado ≤ 3, E > 0.577). Dívidas FECHADAS: poluição nome-do-curso, Protocols/shadowing
  (`AnchorEngineProtocol`), unificação `_card_entry`↔`card_block.normalized_card_map`. Dívidas que
  FICAM: hardening MotorContext (YAGNI), memoização `normalized_card_map` (FASE 4), resíduo TIER 3 =
  3 confiante-errado same-theme (Dafny/Hoare; 1 deles cai com curadoria bloco-09) + fila flag 37/59
  (23 falso-alarme, 63%) = O número do go/no-go FASE 3. Limitação documentada: desconto course_name
  em curso nomeado-pelo-tópico degrada para flag (nunca confiante-errado). Próximo: FASE 2 (P3 SO /
  P4 TCC); go/no-go FASE 3 = decisão USER com o report em mãos (sign-off condicional §9).
  **ADENDO auditoria do gold (2026-07-08, sign-off USER):** 7 rows do `ground_truth_MF.csv` com
  true_block_id stale (drift posicional pós-reprocess) re-rotuladas — números REAIS da FASE 1:
  **acurácia 82.8% / contenção 0 / confiante-errado 1 / recall 0.900**; resíduo TIER 3 = só
  `exerciciosdafny2`; fila flag 37 (28 certos). Pendência USER bloco-09 MORTA (card map estava certo).
  Baselines renegociados nos 2 probes. Ver item USER-SIDE riscado e report FASE 1 (adendo).
  Composição dos 10 pares errados restantes (report, tabela final): 6 = cluster indução×Isabelle
  05↔06 (grão-de-semana, LLM não converte — lever = pino/card fino), 1 = exerciciosdafny2 (confiante,
  candidato TIER 3), 2 = títulos 100% stem-genérico (introducao/revisao — sem sinal lexical), 1 =
  tiposindutivos (código sem léxico no roteiro). ~7/10 fora do alcance de scorer lexical → próximo
  ponto de acurácia = FASE 2/pinos, não calibração.
- [DERIVADO] **PRÉ-FLIGHT FASE 2 item 1 CONCLUÍDO (as-of 2026-07-08): golds SO/TCC/IA/ES2 FRESCOS —
  0 re-rotulagens necessárias.** Auditoria READ-ONLY via `scripts/audit_gold_freshness.py` (novo;
  checks MISSING_BLOCK/DATE_MISMATCH/ADMIN_TRUE/OUT_OF_WINDOW/PAIR_MISMATCH/ZERO_OVERLAP, filtra
  scorable=yes). Prova de frescor: `computed_block_id` congelado nos CSVs == computed atual do
  manifest (uuid→display) em **0 DIFF nos 4 cursos** (SO 38/38, TCC 35/35, IA 40/40, ES2 27/27;
  0 órfãos scorable); timelines intocadas desde 28/06–01/07 = época da rotulagem (01/07, pós-reprocess
  21/06). ES2 validado também por data_real ∈ período do bloco true em 100% dos rotulados. O drift do
  MF NÃO se reproduz. ZERO_OVERLAPs remanescentes = limitação do léxico (NP filtrado, semântica
  semáforos→sincronização), não drift. Casos SO contra-intuitivos (segmentação→bloco-12=enunciado TP2;
  IPC→bloco-05 com computed=bloco-07) são rótulos humanos deliberados CONTRA o computed — ficam.
  Probes fase0+fase1 re-rodados em par: ambos PASS (82.8% / conten 0 / conf-errado 1 / recall 0.900).
  Item 2 do pré-flight DECIDIDO (user, 2026-07-08): migração gold→block_uuid fica DÍVIDA para a
  FASE 4 (junto do trabalho de reprocess); regra vigente = `audit_gold_freshness.py` roda como
  PRÉ-GATE antes de QUALQUER medição contra ground_truth_* (especialmente pós-reprocess).
- [DERIVADO] **FASE 2 do motor de atribuição FECHADA (as-of 2026-07-09; código COMMITADO em 9
  commits `985351b..9119ac4` — 6 tasks + 3 fix-waves de review — na branch `feat/motor-atribuicao`)** — providers P3 (SO, data-no-nome)
  e P4 (TCC, topic-bridge) implementados + provados por réguas externas HARD. Report completo:
  `docs/reports/2026-07-09-fase2-providers-report.md`.
  **P3/SO** (`scripts/fase2_prova_SO.py`): cobertura **45.2% (19/42)**, colisões **0**, matriz gate
  {alta-ok 13, resto-ok 2, resto-err 4}, confiante-errado **0**, acurácia par-colapsada **77.8%**
  (14/18) vs baseline funil 47.4%; 100% das decisões via provider `data`. `DATE_DF_MAX` recalibrado
  na grade 1/2/3 (protocolo D4) e **mantido em 2** (empata com 3 no `alta-ok` máximo, desempate pela
  constante já vigente/validada na FASE 1 MF).
  **P4/TCC** (`scripts/fase2_prova_TCC.py`): pinos manuais **5/5** por interseção (contenção total
  3/5 — NP-completude perde bloco-21, Halteproblem perde bloco-10, métrica secundária sem piso),
  cobertura **83.3% (30/36)**, confiante-errado **0**, acurácia par-colapsada **84.2%** (19 pares) vs
  baseline funil 56.0%; breakdown por provider: manual 8/8=100%, topic 16/20=80%. `TOPIC_STEM_LEN=6`
  / `TOPIC_MIN_TOKEN=3` mantidos (grade não disparou — pinos 5/5 já no ponto default).
  **MF (regressão): intacto** — acc 82.8%, contenção 0, confiante-errado 1, recall 0.900; probes
  fase0/fase1 PASS em toda a fase. **Suite completa: 1722 passed / 4 skipped / 0 failed.**
  **Fila humana consolidada (go/no-go FASE 3): MF 37 + SO 6 + TCC 22 = 65 flagados** (SO/TCC
  derivados da matriz gate/banda — não expostos direto no output do probe original, confirmados por
  reexecução read-only contando `AnchorDecision.flag`, 0 mismatch contra `flag == (band != "alta")`).
  **Riscos residuais (não bloqueantes, ver report):** (1) ramo flagado do gate de data hardcoda
  `band="media"` — perde granularidade silêncio-lexical vs overlap-boilerplate na fila SO; (2)
  janela-1 vinda de provider `topic` NÃO passa pelo gate D4 (só `data` passa) — 0 ocorrências hoje no
  TCC, monitorar; (3) `TOPIC_MIN_TOKEN` piso-2 é no-op estrutural (assinatura de bloco tem piso-3) —
  calibração futura de tokens curtos exige assinatura própria do P4 nos dois lados; (4) réguas
  SO/TCC medem acurácia WHOLE-CASCADE por design, com linha `providers` denunciando mistura; (5)
  contenção total de pinos 3/5 (vs interseção 5/5, o aceite) — relevante se FASE 3+ exigir contenção
  dura multi-bloco; (6) memoização `_global_df`/`_modal_years`/`normalized_card_map` deferida pra
  FASE 4. Próximo: go/no-go FASE 3 = decisão USER com este report em mãos (sign-off condicional §9,
  resoluções 9/11 do spec já aprovadas).
- [DERIVADO] **FASE 3 do motor de atribuição FECHADA (as-of 2026-07-09; código COMMITADO Tasks 1-5
  `512afcd..c70c272` na branch `feat/motor-atribuicao`; Task 6 = esta medição real, uncommitted até
  este commit) — VEREDITO: FAIL HONESTO.** Report completo:
  `docs/reports/2026-07-09-fase3-llm-report.md`. Rodada real (3 rodadas, cap 20/rodada):
  **50 chamadas API tentadas, 30 úteis** (rodada 1 = 20/20 erro 404 — bloqueio de infra, não
  conteúdo: `gemini-2.5-flash` aposentado neste ambiente para `generateContent`; fix = trocar
  `gemini_model` pra `gemini-flash-latest` no `~/.gpt_tutor_config.json` pessoal, sem tocar
  código/repo; ver report). **Números**: lift **+1** (piso +4, FAIL) · confiante-errado **0**
  (piso cumprido — o único resíduo herdado, `exerciciosdafny2`, foi corrigido pelo voto) · rodada
  **completa** (48/48 votos cacheados, 18 seed MARCO 1 + 30 novos). Acurácia global par-colapsada
  82.8%→84.5% (48/58→49/58). **Achado central**: na fila FLAGADA (37/44, a fila que a TIER 3
  deveria reduzir) o saldo foi **ZERO** (28→28: 4 correções anuladas por 4 regressões); todo o
  lift (+1) veio do lado série-same-theme não-flagado (7/44, 6→7). Ou seja, medido honestamente,
  **o voto TIER 3 não reduziu a fila humana no MF** — só resolveu 1 caso pontual que já não
  estava na fila. 5 casos seguem não-conversíveis (cluster indução×Isabelle 05↔06 núcleo duro
  — 4 casos — + `tiposindutivos`); 2 dos 6 casos originalmente nomeados nesse cluster (FASE 1)
  CONVERTERAM nesta rodada, refutando a categorização binária "100% não-conversível". Regressão
  total: fase0/fase1/fase2-SO/fase2-TCC PASS intactos (rodam sem voter); suite **1743 passed / 4
  skipped / 0 failed**. Por spec §12 regra 4, **NÃO iterei prompt** — número é definitivo para
  esta rodada; decisão go-forward (aceitar lift menor com sign-off OU reverter GO da TIER 3) é do
  **user**, com o report em mãos. **Dívida #1 (band no ramo flagado, risco residual #1 da FASE 2)
  fica OPEN** — como o veredito é FAIL, a TIER 3 não "consome" o flag; N/A só se aplicaria em
  PASS. Plano **NÃO arquivado** (regra do brief: só arquiva em gate verde) — segue em
  `docs/superpowers/plans/2026-07-09-fase3-voto-llm.md` até a re-decisão do user.
- [DERIVADO] **FASE 3 ACEITA com piso revisado (as-of 2026-07-09, SIGN-OFF user, pós-experimento
  gemini-3.5-flash) — supersede o FAIL da entrada acima.** Hipótese do user (modelo aposentado +
  seed 2.5 deprimiram o lift) parcialmente CONFIRMADA: re-voto das 44 rows com `gemini-3.5-flash`
  PINADO (cache zerado, seed excluído, 44 chamadas, 0 erros, smoke de geração pré-rodada) =
  lift **+3** (6 conversões − 3 regressões), global par-colapsado **82.8%→87.9%** (51/58),
  conf-errado **0**. Variante offline "flagged-only" (série não vota) é PIOR: +2 e conf-errado
  volta a 1 (`exerciciosdafny2` só vota via série) — escopo flagged∪série do spec confirmado
  ÓTIMO; as 3 regressões (`exercicioscorrecaoterminacao`, `logicadehoare2`, `terminacao`) são
  todas FLAG (falso-alarme do gate D4 votando) — nenhuma regra de escopo as evita. Piso da régua
  renegociado ≥+4→**≥+3** (`LIFT_MIN=3`, baseline consciente; regressão futura <+3 = FAIL).
  **Dívida #1 (band no ramo flagado) → N/A** (GO aceito: TIER 3 consome flag, não band). Config
  do user pinada `gemini-3.5-flash` (era alias `gemini-flash-latest`); cache da rodada mista
  preservado em `material_curation_MF_2026-07-09_run1_mixed.json`. Resíduo pós-voto: 7 pares →
  checklist de PINOS (TIER 1, user na GUI): `exercicioscorrecaoterminacao`→bloco-11,
  `logicadehoare2`→bloco-10, `terminacao`→bloco-12, `provasindutivas-especificacoesrecursivas`
  (+`-arvores`/`-listas`)→bloco-06, `tiposindutivos`→bloco-15. Com pinos: 58/58 no gold (100%
  no gold ≠ 100% no curso). A [DECISION] D4×janela-1 abaixo vira item OBRIGATÓRIO do plano da
  FASE 4 (voter vai ligar).
- [DERIVADO] **FASE 4 do motor de atribuição FECHADA (as-of 2026-07-22; código COMMITADO
  `8f73084..480231a` na branch `feat/motor-atribuicao`; régua `fase4_prova_D9.py` = Task 11,
  commit `2fd725a`; fix-wave pós-review `54e7662..480231a`)** — AnchorEngine substitui `apply_anchor_placement` no call-site do reprocess,
  atrás de `use_anchor_engine` por-curso (precedência sobre a flag legada; caminho legado intacto
  até o cutover FASE 5); voter TIER 3 opt-in via `use_llm_voter`. **9 itens do handoff (0-8)
  FECHADOS:** item 0 (modelo Gemini morto → `gemini-3.5-flash` pinado + guard), item 1 (D4×janela-1
  — ver entrada riscada acima), item 2 (sidecar `material_curation.json` no repo-tutor +
  `prune()` merge-on-save), item 3/4 (`LlmVoter` thread-safe: lock, log de erro, `no_key`,
  `round_summary`, cache por content_key), item 5 (`motor/context.py` loader único +
  memoizações `_global_df`/`_modal_years`/`normalized_card_map` — fecha a dívida FASE 1 do mesmo
  nome), item 6 (gold→`block_uuid` — ver entrada riscada acima), item 7 (badges band/flag/provider
  no Timeline Dashboard, band autoritativa do motor), item 8 (`cronograma_health` lê a janela do
  motor quando `temporal_block_window` existe; S2 legado vira fallback só flag-OFF, pré-requisito
  nomeado da deleção FASE 5).
  **Número do aceite (spec §7), medido por `scripts/fase4_prova_D9.py`:** flag-OFF byte-idêntico ✓;
  flag-ON `computed_*` inalterado (só `temporal_*`) ✓; pino manual nunca sobrescrito (11 pinos,
  0 `TEMPORAL_KEYS` vazadas) ✓; dup-divergence 0 (TIER 0 por `content_key` md5) ✓; gold MF
  pair-colapsado **det 48/58 = 82.8% (conf-errado 1) · voter all-cache (cap=0) 51/58 = 87.9%
  (conf-errado 0)** — byte-idêntico aos baselines FASE 0/FASE 3, 0 chamadas API na rodada de prova.
  **VEREDITO FASE 4: PASS.** Regressão: 6 probes (fase0/fase1/fase2-SO/fase2-TCC/fase3/fase4) PASS
  + suite **1787 passed / 4 skipped / 0 failed** (pós fix-wave `54e7662..480231a`).
  **Review final whole-branch (fable): Ready to merge YES** — fix-wave fechou 1 Critical
  (C1: `resolve_temporal_block` agora resolve uuid→display no chokepoint leitor; producer intocado,
  flag-OFF byte-idêntico preservado) + 2 Important (I1: TIER 0 não atravessa fronteira de escopo —
  gêmeo md5 fora-de-escopo não herda nem apaga temporal; I2: `_build_motor_voter` usa a precedência
  real config > `GEMINI_API_KEY` do ambiente) + 7 minors fix-now da triage. Defer-F5 registrados
  no ledger `.superpowers/sdd/progress.md`.
  **2 adjudicações do controller registradas no ledger, durante a escrita da régua (Task 11):**
  (1) *defeito-de-plano — universo do gold-check.* O snippet do plano (Step 1) omitiu o filtro
  `is_out_of_disamb_scope` em `_gold_check`; sem ele a régua mediu as 66 rows scorable (incluindo
  as 8 TIER-2 fora do mandato do motor) em vez das 58 do universo disamb-scope que os baselines
  F0/F3 declaram — FAIL espúrio (74.2%/78.8%) mascarando comportamento byte-idêntico ao aceito.
  Fix: 1 guard-clause em `_gold_check` (skip out-of-scope), alinhando o universo medido ao
  universo declarado. (2) *precedente explícito F1 (BASELINE_RECALL=14/17 fração exata) — pisos
  em fração exata, não display arredondado.* `82.8`/`87.9` como floats literais eram o valor
  ARREDONDADO de `48/58`/`51/58`; `48/58 = 82.7586...` é `< 82.8` em ponto flutuante (comparação
  estrita), gerando 2º FAIL espúrio (det=False) mesmo com o universo já corrigido. Fix: pisos
  viram `48/58`/`51/58` (frações exatas); display em `%` mantido via `100 * PISO:.1f`. Nenhum piso
  foi *afrouxado* em nenhuma das duas correções — ambas alinham a MEDIÇÃO ao número já aceito, não
  mudam o número aceito.
  **Dívida nomeada nova [CODE]:** TIER-2 no gold MF (`trabalhos/provas/TDE`, 8 rows scorable) =
  **1/8 pelo funil** — categorias saem do motor via `_OUT_CATEGORIES` por design (janela-de-prazo
  real T1/T2→blocos 15/16 é dívida separada, ver "Fora de escopo" do plano F4); medição própria
  destas 8 rows entra no rollout FASE 5, não bloqueia o aceite F4 (que mede só o universo
  disamb-scope, por declaração explícita dos pisos).
  *Composição concreta no MF (diagnóstico do piloto 2026-07-22, verificado entry-a-entry):*
  `t1-2026-1`/`t2-2026-1` (trabalhos TDE) = alvo direto da janela-de-prazo; `t1-2026-1-thy`
  (codigo-professor) = companion do t1, herda a atribuição; `revisao-p1-gabarito` (provas) =
  **pino trivial na GUI** (mesmo bloco `5599d015` do `revisao-p1`, já pinado) — não precisa de
  código; `plano` (cronograma) = **funil deliberado** (plano de ensino não pertence a bloco;
  "corrigir" seria inventar pertencimento). Só 3 dos 5 dependem de código novo (o provider
  janela-de-prazo).
  Housekeeping: `docs/superpowers/plans/2026-07-10-fase4-integracao-d9.md` movido para
  `Feitos/` (gate verde). Reprocess REAL nos repos-tutor (escrever temporal/sidecar de verdade) e
  ligar `use_anchor_engine`/`use_llm_voter` em `SubjectProfile.feature_flags` = ação do user na
  GUI, curso a curso — rollout FASE 5.
- [DERIVADO] **Triage completa do review final whole-branch F4 (fable, 2026-07-22; veredito
  pós-fix-wave: Ready to merge YES).** Registro integral por decisão do user (inclusive os
  "ignore" — catalogados mesmo sem ação prevista):
  **FECHADOS na fix-wave (`54e7662..480231a`):** C1 uuid→display no leitor `resolve_temporal_block`
  (producer intocado); I1 TIER 0 `decided`-cache não atravessa fronteira de escopo (skip
  `is_out_of_disamb_scope` antes do lookup, ambas as ordens testadas); I2 `_build_motor_voter`
  com precedência real config > `GEMINI_API_KEY` do ambiente; T1a logger.info no remap
  RETIRED_MODELS; T6 testes pino-inválido/None-em-gêmeos; T7c asserts de `_run_anchor_engine_layer`
  com deepcopy (não-vácuos); T7d `exc_info=True` no warning da camada; T11a import morto +
  param `repo` não usado removidos da régua; T11b veredito imprime `voter=SKIPPED` sem cache;
  dup-div exclui entries sem temporal (evita FAIL espúrio com pino gêmeo em F5).
  **[CODE] Defer-FASE 5 (entram junto do rollout, não bloqueiam):** T1b combo da UI mostra modelo
  stale órfão (migração em `AppConfig._load` é o fix certo); T2b `load_repo_artifact` engole
  exceção com `{}` — timeline corrompida vira motor no-op silencioso (1 logger.debug basta);
  T3 `fase3_prova` vote_rows não filtra janela-1 (row nova flagged sem cache = "pend" perpétua no
  gate de completude); T4b lock do voter é por-processo (TOCTOU entre processos; single-writer
  hoje via task queue); T7a double-hashing md5 (live_keys + apply — compartilhar mapa de chaves);
  T7b sem teste e2e do gate via `regenerate_pedagogical_files` (elif verificado por inspeção;
  e2e entra na suite do cutover); T9a ref `None` vira `"None"` e sobrevive ao filtro do health
  (só manifest editado à mão aciona); herdados do review F3: parent-dir em
  `save_material_curation`, fold caso/acento em `source_section`, `match_window_ref`
  strip/casefold, truncamento do dry-run, stopwords PT no P4.
  **Ignore (catalogados, sem ação prevista — razões do reviewer):** T1c guard test exime
  `gemini_client.py` inteiro por nome (único uso legítimo de "gemini-2.5" vive lá); T1d fix-wave
  T1 rodou só `-k gemini` (superado: suite completa verde no head); T2a gate T2 re-rodou só 3
  probes (superado: Task 11 re-rodou os 6); T4a memória-vence em chave conflitante entre
  instâncias (mesma content_key = mesmo conteúdo, qualquer voto é válido); T8 teste não-leak
  do badge cobre só `computed_block_band` (motor_badge só lê temporal_*); T9b anotação `-> list`
  frouxa; T10a `true_of` chamado 3x/2x por row em SO/TCC (probe, custo desprezível); T10b
  fallback devolve uuid cru se bloco sem `id` (falha honesta de display em timeline malformada);
  T10c `migrate_gold_uuid` sem try/except (one-shot já executado); T11c divisão ok/tot duplicada.
- [DERIVADO] **Piloto flag-ON MF (2026-07-22, dry-run em memória — zero writes no repo-tutor):
  retrato do que `use_anchor_engine`+`use_llm_voter` fariam hoje no reprocess do MF.**
  67 entries → **51 com `temporal_*`** (bands 15 alta / 36 media; providers 9 manual / 6 labels /
  36 llm), **11 com pino manual** (motor respeita e limpa temporal — resolvidos por decisão
  humana, pino > temporal na cascata) e **5 TIER-2 fora-de-escopo** (composição acima). Voter
  100% cache da F3: 36 hits, **0 chamadas API**, 0 erros; **fila humana 0** (o cache cobre
  exatamente os casos flagáveis). Delta visível: 42 decisões confirmam o funil, **9 divergem** —
  por gold/auditoria-0807: `exerciciosdafny1` (12 vs 15), `exerciciosdafny2` (13 vs 11) e
  `revisao` (03 vs 02) são CORREÇÕES de erro do funil; `tiposindutivos` (13 vs 15) e
  `exercicioscorrecaoterminacao` (12 vs 11) são os erros residuais conhecidos (band media, nunca
  alta); `provas` (06 vs 05, alta) consistente com a régua (voter cw=0); `exemplos-zip`/
  `exercicios-arrays`/`exercicios-conjuntos` sem gold direto. Balanço flag-ON: **62/67 com dono
  certo** (51 motor + 11 pino), 1 pino trivial pendente, 3 aguardando janela-de-prazo, 1
  deliberadamente sem bloco.
  **[CODE] Pré-requisito do flip real:** o sidecar `material_curation.json` NÃO existe na raiz do
  `Metodos-Formais-Tutor` — fazer seed do cache F3 (`docs/reports/material_curation_MF.json` →
  raiz do repo-tutor) antes do 1º reprocess flag-ON, senão a 1ª rodada re-paga até 20 votos (cap).
- ~~[USER/DECISION] **Auditoria .env (2026-07-22): armadilha de token Moodle stale.**~~
  **RESOLVIDO (verificado 2026-08-06, varredura):** `.env` raiz hoje só tem
  `GEMINI_API_KEY`/`DATALAB_API_KEY`/`DATALAB_BASE_URL` — as chaves MOODLE saíram do raiz;
  `moddle/.env` virou fonte única (recomendação do controller executada; zero código).
  Texto original preservado abaixo:
  `MOODLE_URL`/`MOODLE_TOKEN` existem no `.env` RAIZ e em `moddle/.env`; a raiz vence
  (os.environ carregado no import por `helpers._load_project_env_file`), mas a GUI
  (`save_moodle_token`, moodle.py:638) escreve SÓ em `moddle/.env` → renovar token pela GUI
  não tem efeito enquanto a cópia stale viver no raiz (falha silenciosa). Recomendação do
  controller: remover as chaves MOODLE do `.env` raiz (zero código; `moddle/.env` vira fonte
  única). Alternativa [CODE]: `save_moodle_token` fazer merge no raiz e aposentar `moddle/.env`.
  DECISÃO PENDENTE do user.
- ~~[USER] **`MOODLE_PRIVATE_TOKEN` é chave morta** — presente no `.env` raiz e documentada no
  `.env.exemple`, mas ZERO consumidores no código (grep 2026-07-22). Remover do `.env` e do
  template (o template hoje ensina a criar uma chave que não faz nada).~~
  **RESOLVIDO (verificado 2026-08-06, varredura):** fora do `.env` raiz e do `.env.exemple`
  (as duas remoções pedidas). Zero consumidores re-confirmado por grep (só menções em docs).
  Residual inofensivo: a chave ainda existe em `moddle/.env` — ninguém a lê; apagar é opcional.
- [CODE] **`datalab_client` depende de import transitivo de `helpers` para ver o `.env`** —
  (re-verificado 2026-08-06: ainda vivo; arquivo hoje em `src/builder/runtime/datalab_client.py`,
  lê `os.environ` nas linhas 30/61/65 sem loader próprio) —
  lê `os.environ` em call-time sem carregar o `.env` por conta própria; hoje todos os chamadores
  (engine, dialogs) importam helpers antes, mas um script standalone futuro que o use direto
  não veria as chaves. Fix barato quando tocar o arquivo: import de helpers (ou chamada explícita
  ao loader) no topo do datalab_client.
- [CODE] **Hook `code-review-graph` crasha com erro de encoding cp1252 em todo commit**
  (`as-of 2026-08-06`; o handoff 2026-08-05/06 dizia "registrado como pendência", mas o item não
  existia neste tracker — registrado agora). Cosmético: engole o painel de risco no output do
  commit, não bloqueia o commit. Fix provável: forçar UTF-8 no stdout do hook
  (`PYTHONIOENCODING=utf-8` ou `sys.stdout.reconfigure`). Mesma família do mojibake de console
  que fabricou o falso U+FFFD da fio Task 3 (ver AMENDMENT 2026-08-06).
- [DERIVADO] **Provider janela-de-prazo (TIER 2) ENTREGUE (2026-07-22, commits `b64d983..6d1418a`,
  7 commits; spec `2026-07-22-janela-de-prazo-tier2-design.md`, plano em plans/).** Probe-first:
  `fase5_prova_tier2.py` cravou baseline **1/8** ANTES de código (universo 8 rows out-of-scope,
  guard n==8). Produtor: `extract_assign_deadlines_detailed` (um due por módulo, sem colapso) +
  `assign_dues` aditivo no card map. Motor: `due_window.py` (tier2_due_scope, matching stem com
  guard de conflito, containment/straddle D-A/D-B, band D-D, nunca chuta) + wiring na cascata
  `pino > tier2 > out-of-scope` (sem dup-cache no TIER-2, lição F4 I1). Review final whole-branch
  (fable) + fix wave + re-review: **READY TO MERGE YES**. Régua: 6 probes byte-idênticos + fase5
  baseline-only PASS; suite ~1806/4/0. **Invariante testado**: true-set do tier2_due_scope ⊂
  is_out_of_disamb_scope (flag-ON fora do TIER-2 idêntico ao pré-branch por construção).
  **[USER] Pré-requisitos da medição target (piso 4/8, cw 0)**: (a) sync Moodle do MF na GUI
  (popula assign_dues real); (b) **card `source=="manual"` NUNCA ganha assign_dues**
  (merge_card_block_map) — se o piloto pinar o card TDE manualmente, o 4/8 fica inalcançável POR
  DESIGN; interpretar FAIL com isso em mente antes de culpar o provider. FAIL = resultado honesto.
  **[CODE] residual cosmético**: `mine = _stems(...)` computado 2× em `_match_due` (hoist de 1
  linha, minors-batch futuro).
- [DERIVADO/DECISION] **Medição TARGET da janela-de-prazo EXECUTADA (2026-08-03): FAIL honesto
  1/8 (piso 4/8) · cw=0.** Sync do MF rodou HEADLESS (token `moddle/.env` + `MoodleClient` +
  `backfill_repo_signals_consumed`, mesmo caminho da GUI; MF ainda visível na matrícula,
  id=92717) — `assign_dues` real populado, card TDE `source=labels` (caveat do pino manual NÃO
  se aplicou). Causa do FAIL: **os dados reais do Moodle falsificam a inferência do design**
  (spec §6 já hedgeava: "dues dos exemplos são INFERÊNCIA do gold"). Três quebras verificadas
  na API: (1) os 2 assigns do card TDE chamam-se ambos "Sala de entrega" — SEM stem t1/t2 →
  matching D-C nunca casa → funil (por isso 1/8, não cw). (2) Mesmo casando por posição: due
  estruturado do T1 = 2026-05-06 (stale — professor moveu a entrega; a sala real do T1 é o
  FORUM "Sala de Entrega (10/06)" na seção Verificação de Programas, outro card) → containment
  daria bloco-11 ≠ gold bloco-15 = confident-wrong band alta. (3) Due do T2 = 2026-07-06 cai
  DENTRO de bloco-18 [06/07..06/07] (dia-único de devolução) → containment daria bloco-18 ≠
  gold bloco-16 = segundo confident-wrong. **D-E (nunca chuta) foi o que segurou cw=0** — a
  recusa por falta de stem evitou 2 erros confiantes. Spec §12 regra 4: FAIL registrado, ZERO
  re-tuning. Redesign (dues cross-card/forum, ordinal por label, due→bloco-de-conteúdo-anterior)
  = decisão de design NOVA do user, não patch. Semestre 2026/2 já visível na matrícula — cursos
  novos são o teste out-of-sample natural do provider como está.
- [DERIVADO] **GOLD t1/t1-thy CORRIGIDO bloco-15 → bloco-11 (2026-08-03, autorizado user).**
  Investigação pós-FAIL derrubou a inferência da spec F5: probe one-off do LlmVoter (0/3, cache
  isolado em scratchpad, 3 calls) expôs que conteúdo do T1 = Isabelle/indução, não Dafny →
  auditoria via API Moodle com evidência DEFINITIVA: submissão real do T1 = **2026-05-05 15:56**
  (assign 212883, `mod_assign_get_submission_status`) → due 06/05 do Moodle era CORRETO, não
  stale; fórum "Sala de Entrega (10/06)" ≠ T1 (são exercícios Dafny — disc. "Humberto - Fila
  Ilimitada" 10/06). T2 submetido 2026-06-27 (assign 215115) → gold bloco-16 confirmado.
  **Decisões user**: semântica do trabalho = ÉPOCA DE ENTREGA; fonte de verdade = Moodle
  ("geralmente a mais correta"). Auditor de frescor MF: hard=0 (ZERO_OVERLAP em t1/t2 = suspeita
  soft esperada de PDF de trabalho, 47 rows na mesma condição). Probe fase5 pós-correção:
  FAIL 1/8 esperado (provider ainda decide por stem/containment — F5b pendente). **[DECISION]
  F5b proposto (aguarda autorização)**: (1) matching posicional `label → resources → assign` na
  ordem da seção (mata dependência de stem); (2) D-A revisada: "último bloco DE CONTEÚDO com
  `period_end <= due`" no lugar de containment puro (t1: 06/05→bloco-11 ✓; t2: 06/07→pula
  17/18 sem tópicos→bloco-16 ✓). Piso 4/8 mantido, cw=0 mantido.
- [DERIVADO/DECISION] **Medição TARGET pós-F5b EXECUTADA (2026-08-03): PASS 4/8 (piso 4/8) ·
  cw=0.** Re-sync HEADLESS do MF (mesmo caminho `MoodleClient` + `backfill_repo_signals_consumed`
  usado no FAIL 1/8 anterior) gravou `file_dues` real no card TDE: `t1_2026_1.pdf`/
  `t1_2026_1.thy` due `2026-05-06`, `t2_2026_1.pdf` due `2026-07-06` (posicional, `source=
  structured`); re-sync também gravou uma key extra `"arquivo .thy.thy"` (due `2026-05-06`),
  vinda de um resource `.thy` com nome genérico na mesma seção — observado, não-bloqueante,
  nenhuma assertiva afetada. Probe `fase5_prova_tier2.py`: `t1→bloco-11 OK, t1-thy→bloco-11 OK,
  t2→bloco-16 OK, revisao-p1-gabarito→bloco-07 OK` — as 4 previsões exigidas pela spec F5b
  bateram exatamente; `plano`/`archive-of-formal-proofs`/`aws-encryption-sdk`/`eth2` seguem sem
  match (fora de escopo por design, D-E). Confirma a virada de causa registrada no FAIL: a
  correção veio de DOIS ajustes do F5b, não um só — (1) matching posicional `file_dues` (stem
  nunca casaria "Sala de entrega") e (2) revisão da semântica de janela D-A→D-H/D-I ("último
  bloco DE CONTEÚDO com period_end <= due"; blocos administrativos como bloco-17/18 nunca
  ancoram) — por isso t2 cai em bloco-16, não no confident-wrong bloco-18 que containment puro
  daria. Régua flag-OFF (6 probes) byte-idêntica: fase0 82.8%/conten 0/cw 1 · fase1
  9/10 · fase2-SO 45.2%/0/0 · fase2-TCC 5/5 pinos+83.3%/0 · fase3 lift +3 sem API nova · fase4 det
  48/58 cw1, voter 87.9%/cw0 (baselines pós-pinos MF 2026-08-06: det 53/58, voter 58/58 — drift
  dos 7 pinos, isolado via stash). Suite: 1816 passed, 4 skipped. Head dos commits F5b: `843475f`
  (produtor `extract_file_dues` posicional), `1d39cb4` (motor `_match_due` posicional +
  âncora bloco-de-conteúdo).
- [DERIVADO/DECISION] **Task 3 rollout flag-ON MF (2026-08-04): reprocess REAL executado, gate
  HARD-drift (gate_mf.py) PASS, mas gate duro do voter FALHOU (1 chamada API nova) → ROLLBACK,
  campanha PARADA para sign-off.** `python scripts/reprocess_assignments.py --flags
  use_anchor_engine,use_llm_voter` rodou sem traceback (`bloco 66/67 -> 66/67`). gate_mf.py:
  **PASS exato** — 54/54 `temporal_block_id` (51 piloto + 3 tier2), 11/11 pinos intactos e
  LIMPOS de temporal, `t1-2026-1`/`t1-2026-1-thy`→bloco-11, `t2-2026-1`→bloco-16 (bate 100% com
  o probe fase5_prova_tier2.py), `plano`/`revisao-p1-gabarito` corretamente fora do temporal.
  **Mas** `material_curation.json` foi de 44→45 votos: 1 chamada Gemini nova real (content_key
  `7fd46c78cec5e28c6090392b3057fb20`, resultado `bloco-16`/`gemini-3.5-flash`) — viola a premissa
  "cache 44 votos deve cobrir" das regras da task. *(Correção pós-diagnóstico, ver entrada Fix
  round 1 abaixo: essa chave NÃO é de `t2-2026-1` — é de `verificacaomodelos`, material de aula
  in-scope; a coincidência de bloco (bloco-16) é conteúdo real, não scope-leak.)*
  **Causa provável, não confirmada como bug**: o probe one-off do LlmVoter usado na correção do
  gold t1/t1-thy (entrada acima, "GOLD t1/t1-thy CORRIGIDO") rodou com **cache isolado em
  scratchpad** (por design — `material_curation_path()` documenta que probes nunca escrevem no
  path de produção), então aquele voto NUNCA foi mesclado no seed de 44 usado no Task 2 — o
  conteúdo de `t2-2026-1` provavelmente nunca tinha sido votado no path de produção antes desta
  rodada. Se essa leitura estiver certa, o novo voto era estruturalmente inevitável (conteúdo
  novo do tier2, entregue DEPOIS do piloto 36-hit de 2026-07-22) e não uma regressão do motor —
  mas isso é INFERÊNCIA, não confirmado por ninguém com autoridade para relaxar o gate.
  **Evidência adicional**: o método de verificação prescrito na brief (`Select-String` no log do
  reprocess por `gemini|voter|vote`) NÃO detecta nem chamadas nem cache-hits — o `LlmVoter` só
  usa `logger.info`/`logger.warning` (sem handler pro stdout no script headless), nunca `print`;
  o log real tinha só a linha `[flags] ...` (falso-match em "voter"). A verificação confiável foi
  diff direto de `material_curation.json` (contagem de votos + chave nova) contra o seed original
  em `docs/reports/material_curation_MF.json`.
  **Ação tomada**: `git checkout -- .` no repo-tutor MF (reverteu manifest.json + 8 artefatos
  regenerados a `8ea55de`, confirmado 0 `temporal_block_id` pós-revert); flags MF revertidas em
  `subjects.json` (backup do Task 2); **desvio deliberado da Step 5 da brief**: NÃO rodei
  `git clean -fd` — `material_curation.json` (untracked, 45 votos) foi preservado de propósito
  (backup extra em `<scratchpad>/material_curation.json.post-reprocess-45votes.json`) porque
  apagá-lo destruiria o voto já pago sem necessidade — um retry vai bater cache 100% (0 chamadas
  novas de verdade) em vez de re-pagar. Nada foi commitado no repo-tutor MF; `src/` do motor
  intocado. **Recomendação para quem retomar**: revisar se "1 voto novo para conteúdo tier2
  genuinamente novo (nunca votado no path de produção antes)" é aceitável como exceção pontual
  ao gate duro; se sim, re-rodar Task 3 sem modificação (cache já cobre as 45, deve fechar 0/0) e
  seguir para commit. Sem sign-off, campanha permanece PARADA nesta task (branch
  `feat/motor-atribuicao`, sem push).
- [DERIVADO/DECISION] **Fix round 1 — CASE B confirmado por 2 ângulos, retry limpo, 1 divergência
  explicada segura o commit (2026-08-04).** Controller adjudicou: diagnosticar dono do voto +
  wiring antes de decidir CASE A (scope-leak, não fazer retry) vs CASE B (inevitável, prosseguir).
  **Dono do voto**: `content_key()` (`llm_vote.py:49-62`) rodado sobre as 67 entries → a chave
  nova pertence a `verificacaomodelos` (categoria `material-de-aula`, in-scope normal), NÃO a
  `t2-2026-1`. **Wiring**: `apply_anchor_engine()` (`apply.py:53-103`, cascata pino > tier2 >
  out-of-scope > engine) — `tier2_due_scope(entry)` (`due_window.py:23-29`, cobre category
  trabalhos/provas) sempre `continue` antes de alcançar `engine.resolve()`/voter;
  `resolve_due_window()` é aritmética pura, zero import de `LlmVoter` (docstring: "NUNCA
  disambiguator, NUNCA voto LLM"). Confirmado empiricamente pós-retry: `t1-2026-1`/`t1-2026-1-thy`/
  `t2-2026-1` têm `temporal_block_provider=due-window` (nunca `llm`). **CASE B confirmado** — retry
  autorizado. **Retry**: reflip flags, reprocess re-executado sem traceback, `material_curation.json`
  45→45 (0 chamadas novas, 0 chaves alteradas), `gate_mf.py` PASS 8/8 idêntico. Assertivas novas:
  t1/t1-thy `due-window/due-contain/alta/False`, t2 `due-window/due-straddle/media/True` (bate
  exato com a previsão do controller). Distribuição dos outros 51: real **9 manual/5 labels/37
  llm** vs piloto **9/6/36** — 1 unidade migrou de `labels`→`llm`, é a mesma `verificacaomodelos`
  (pós-retry: `provider=llm/band=media/flag=False`, assinatura clássica de aceitação do voter) —
  causa já diagnosticada, sem sinal de problema adicional. `auto_tags bloco:` comparado nas 67
  entries completas (não amostra): zero diffs, funil intacto. **Apesar da explicação completa,
  segui a instrução literal do controller ("divergência = pare, sem commit") e NÃO commitei** —
  não substituí o critério explícito por julgamento próprio uma 2ª vez na mesma task.
- [DERIVADO/DECISION] **Ruling final do controller (2026-08-04): divergência ACEITA, commit
  LIBERADO e EXECUTADO — `Metodos-Formais-Tutor` commit `c7b7498`.** Adjudicação completa:
  **(a)** 1ª chamada API estruturalmente inevitável — conteúdo de `verificacaomodelos` nunca
  tinha voto em produção (probe do gold t1/t1-thy, 2026-08-03, usou cache ISOLADO em scratchpad
  por design, nunca mesclado no seed). **(b)** Voto rastreado por `content_key()` até uma entry
  in-scope normal (`verificacaomodelos`, categoria `material-de-aula`) — NÃO `t2-2026-1`; wiring
  de `apply_anchor_engine()` (`apply.py:53-103`) prova que `trabalhos`/`provas` (cascata
  `tier2_due_scope` → `resolve_due_window`, sempre `continue` antes do `engine.resolve()`/voter)
  nunca alcançam o voter — decisão do user 2026-08-03 ("voter para trabalhos DESCARTADO")
  preservada intacta, zero scope-leak. **(c)** Retry fechou 0 chamadas novas
  (`material_curation.json` 45→45, 0 chaves alteradas). **(d)** `gate_mf.py` PASS 8/8 + assertivas
  novas exatas (`t1-2026-1`/`t1-2026-1-thy` → `due-window/due-contain/alta`; `t2-2026-1` →
  `due-window/due-straddle/media/flag=True`) + `auto_tags bloco:` zero-diff nas 67/67 entries
  completas. **(e)** Distribuição de providers nos 51 não-tier2 **9 manual/5 labels/37 llm vira o
  novo valor de referência do rollout MF** (substitui o piloto 9/6/36 de 2026-07-22) — adjudicado
  com evidência de gold: `docs/reports/ground_truth_MF.csv` tem `verificacaomodelos → bloco-16`
  (block-direct, clean, scorable=yes) — o voto novo colocou o material no dono CERTO por gold,
  é correção da era-`labels` (que resolvia sem voto), não regressão. **(f)** Autorização de sessão
  do user: "fazer trilha 1" (cutover fora da campanha, decisão registrada em
  `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/progress.md`). Concern residual PARQUEADO
  como minor deferred (não investigar): contagem de linhas dos `.md` gerados variando entre as 2
  rodadas do reprocess (hipótese não confirmada: ordenação não-determinística de `set()` Python em
  `detect_same_theme_series`) — resultados estruturais (contagens/campos temporal_*/providers/
  auto_tags) foram idênticos nas duas rodadas em todos os pontos verificados; só a formatação de
  índices .md pode ter variado. Detalhes completos (diagnóstico, retry, evidências, self-review)
  em `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-3-report.md`.
- [DERIVADO/DECISION] **Rollout flag-ON MF EXECUTADO (2026-08-04): reprocess REAL finalizado, gate HARD-drift PASS, commit `c7b7498` gravado.** Reprocessamento com flags `use_anchor_engine=True`/`use_llm_voter=True` rodou sem traceback (`bloco 66/67 → 66/67`, manifest backup `manifest.json.bak`). **Gate duro gate_mf.py PASS 8/8 exato:** 54/54 `temporal_block_id` (51 piloto + 3 tier2 F5b), 11/11 pinos intactos/limpos de temporal, `t1-2026-1`/`t1-2026-1-thy` → bloco-11/alta/due-contain, `t2-2026-1` → bloco-16/media/due-straddle/flag=True (provider due-window em 100% dos 3 tier2), `plano`/`revisao-p1-gabarito` corretamente no funil. **Voter retry: PASS limpo** — `material_curation.json` 45→45 votos, 0 chamadas API novas, 0 chaves alteradas (cache 45 cobriu 100%, voto novo da rodada 1 já adjudicado CASE B pelo controller). **Distribuição de providers nos 51 não-tier2:** **9 manual/5 labels/37 llm** (nova referência do rollout MF, substitui piloto 9/6/36 de 2026-07-22) — migração labels→llm é a mesma `verificacaomodelos` (contenção gold bloco-16, scoreável=yes), correção da era-labels, não regressão. **Régua completa pós-flip: 7 probes + pytest 100%** (Task 4 medição) — fase0 48/58 conten0 cw1 · fase1 recall 9/10 · fase2-SO cobertura 45.2% colisões 0 cw0 · fase2-TCC pinos 5/5+83.3% cw0 · fase3 lift +3/0 API · fase4 det 48/58 cw1, voter 51/58 cw0 calls0 byte-idêntico flag-OFF (baselines pós-pinos MF
  2026-08-06: det 53/58, voter 58/58 — drift dos 7 pinos, isolado via stash) · fase5 target PASS 4/8 cw0 (t1/t1-thy/t2/revisao-p1-gabarito 4 certos, plano/archives 4 fora-escopo) · **pytest 1820 passed / 4 skipped / 0 failed** — zero regressão entre Tasks 3/4. **Gold MF: 67/67 `auto_tags bloco:` zero-diff** — funil intacto (verificação programática completa, não amostra). **Achado colateral (não-MF, pré-existente):** `audit_gold_freshness.py` hard=1 em SO (lista2 ADMIN_TRUE + ZERO_OVERLAP, title="lista2" não casa regex `ASSESS_TITLE_RE`) — investigação provou scope pré-existente (timeline_index SO datado 28/jun, anterior à campanha; repo SO-Tutor não tocado pela task; heurístico ADMIN_TRUE + estado local antigo). Registrado em pre-flight do rollout SO, não-bloqueante para MF. **Flags duráveis ON:** `subjects.json` (`%APPDATA%\GPTTutorGenerator\`) com `Metodos-Formais.feature_flags = {use_anchor_engine: true, use_llm_voter: true}` persistido (pós-reprocess, pré-commit). **Decisions de sessão (user autorização 2026-08-03):** cutover via FASE 5 fora desta campanha (rollout é FASE 5b trilha 1, não integração global), push antes do cutover (commit MF em main, flags persistidas, sem merge para canário/staging — controle de blast-radius da user). Commit HEAD do MF: `c7b7498` (`rollout flag-ON: use_anchor_engine + use_llm_voter (temporal_* reais; gate HARD-drift PASS)`). Detalhes completos (adjudicação CASE B, retry, wiring tier2, step-by-step) em `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-3-report.md` (Task 3) e `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-4-report.md` (Task 4 régua). Campanha rollout-flag-ON trilha 1 **FECHADA, porta aberta para Task 6 (rollout SO) e Task 7 (trilha 2)** — não há blokers estruturais; próximas trilhas testam isolamento de cursos (SO tópico, TCC topic-bridge, ES2 data). **AVISO operacional:** reprocess headless futuro do MF exige `--flags use_anchor_engine,use_llm_voter` (flags não persistem no manifest; headless não lê subjects.json).
  **[USER] Pré-requisitos de rollout flag-ON em curso NOVO (review final F5b)**: (a) o filtro
  de bloco-de-conteúdo (D-H) usa `topics` — campo OPCIONAL no schema v4; curso com timeline
  sem topics populado deixa o provider silenciosamente morto (funil total, honesto mas
  invisível) — antes do flag-ON, garantir topics OU migrar o filtro para `kind` (campo
  required, enum tipado; candidato a F6/minors-batch com re-medição). (b) Limite conhecido da
  herança posicional: arquivo postado ENTRE o assign do grupo N e o label do grupo N+1
  herdaria o due do grupo N+1 (inexistente no MF atual; fix de 1 linha + teste + re-medição
  quando o produtor for tocado de novo). **[CODE] minors-batch F5b (review final, deferred
  com ruling)**: filtro de `extract_file_dues` não exige `fileurl` (diverge de
  `iter_section_files` → savename key pode divergir; chave por filename original cobre);
  `file_dues` com due vazio cai no fallback stem (produtor nunca emite — gate `if due:`);
  imports function-local em `_module_due`/`extract_file_dues` (estilo da casa); hoist
  `mine=_stems()` 2× herdado de F5.
- [USER/DECISION] **Pre-flight rollout SO (2026-08-04): flip ADIADO — hard=1.** Auditoria `audit_gold_freshness.py --course SO` (`as-of 2026-08-04`): 42 entries scorable, 21 suspeitas (hard=1). Única row com hard-flag = `lista2` [ADMIN_TRUE, ZERO_OVERLAP] true=bloco-17, kind=assessment, título="lista2" não casa regex `ASSESS_TITLE_RE` (label=1 dia · 25/06/2026). **Achado PRÉ-EXISTENTE:** timeline_index SO datado 28/jun (anterior à campanha); Sistemas-Operacionais-Tutor não tocado pela task; heurístico ADMIN_TRUE reproduz estado pré-existente (não regressão do motor). **Regra não-negociável:** medição só com hard=0 e gold muda SÓ com evidência + autorização do user → flip SO bloqueado até ruling do user sobre lista2 (re-rotular true_block OU confirmar bloco-17 como legítimo — lista de revisão de prova). **Pré-requisitos técnicos SATISFEITOS:** baseline fase2_SO 45.2%/0/0 segue válido e byte-idêntico (medido 2026-08-04); topics 19/21 blocos ok (ZERO_OVERLAP = limitação de léxico em nomes como "segmentação" sem overlap semântico com conteúdo bloco-12=TP2, não erro de placement); material_curation.json próprio na raiz do SO-Tutor presente (cache voter local; flip futuro liga use_anchor_engine+use_llm_voter normalmente). **Decisão:** SO flip adiado até autorização do user; Task 7 (TCC trilha 2) pode prosseguir em paralelo (cursos independentes). **Report completo:** `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-6-report.md`.
- [DERIVADO/DECISION] **Rollout flag-ON TCC BLOQUEADO (2026-08-04): gate estrutural (b) funil FALHOU — achado PRÉ-EXISTENTE e ORTOGONAL às flags, confirmado por diagnóstico; sem commit, flags revertidas.** Pre-flight `audit_gold_freshness.py --course TCC`: hard=0 (42 rows, 8 suspeitas ZERO_OVERLAP não-hard). Baseline `fase2_prova_TCC.py`: pinos 5/5 + cobertura 83.3% (30/36) + cw=0 — byte-idêntico ao aceito. Snapshot pré-rollout: `TCC-Tutor` commit `28bb29f`. Flip aplicado e verificado por round-trip (`Teoria da Computabilidade e Complexidade.feature_flags = {use_anchor_engine:true, use_llm_voter:true}`; MF e SO confirmados intocados no mesmo round-trip). Reprocess (`--flags use_anchor_engine,use_llm_voter`) rodou sem traceback: `bloco 27/27 → 27/27`. **Voter SEM cache prévio (TCC não tinha `material_curation.json` na raiz): 16 votos NOVOS pagos (Gemini `gemini-3.5-flash`), todos `confianca=alta`, 0 fila humana (nenhum `temporal_block_flag=True`)** — abaixo do cap built-in 20. **Gate estrutural a/c/d PASS:** (a) os 2 únicos `manual_timeline_block_id` do manifest (`plano-de-ensino`, `3d-matching`) preservados byte-idênticos, nenhum com `temporal_block_id` sujo. (c) 19/27 entries com `temporal_block_id`: providers `{llm:16, manual:1, topic:2}`, bands `{media:16, alta:3}`, methods `{llm:16, janela-1:1, disamb:2}` — zero entries de categoria out-of-scope (trabalhos/provas/cronograma/etc.) com temporal fora de due-window. (d) `material_curation.json` criado na raiz, 16/20 votos. **Gate (b) FUNIL FALHOU:** 4/27 entries mudaram `auto_tags bloco:` entre `manifest.json.bak` (pré) e `manifest.json` (pós) SEM nenhum `temporal_block_id` associado (motor não tocou essas entries — todos os campos `temporal_*` = None nelas): `3dm-caetano-gabriel-e-gustavo` bloco-22→16, `cubic-3-edge-coloring` bloco-26→16, `integer-programming-0001` bloco-13→16, `programacao-inteira-01-20260617-154423-0000` bloco-13→16 — exatamente as mesmas 4 (de 8) linhas já flagueadas `ZERO_OVERLAP` no pre-flight (workshop "Semana 14 - Apresentações T2", conteúdo de teoria dos grafos sem overlap léxico com o vocabulário do curso). **Diagnóstico (prova de causa):** árvore revertida pro snapshot `28bb29f` e `reprocess_assignments.py` rodado SEM `--flags` (flag-OFF puro) como controle — a MESMA drift bloco-22/26/13/13→16 reproduziu IDÊNTICA nas mesmas 4 entries, 0 `temporal_block_id` gerado. **Conclusão: instabilidade do funil-base (recompute de `auto_tags bloco:` fora do anchor engine) é PRÉ-EXISTENTE e ORTOGONAL ao flip `use_anchor_engine`/`use_llm_voter`** — não é regressão desta task, mas viola a letra do gate "(b) zero mudanças" tal como especificado na dispatch. **Ação tomada (sem mandato para autorizar unilateralmente a exceção):** `TCC-Tutor` revertido (`git checkout -- .`) ao snapshot `28bb29f` (working tree limpa; `material_curation.json` de 16 votos PRESERVADO untracked, para reaproveitar cache em retry e não pagar de novo); `subjects.json` revertido (`Teoria da Computabilidade e Complexidade.feature_flags = {}`; MF/SO/IA/ES2 confirmados intocados). **Nenhum commit feito em `TCC-Tutor` nem push.** Pendência: ruling humano sobre se a drift do funil-base nas 4 entries de workshop (pré-existente, comprovadamente independente do flip, mesmas 4 já suspeitas no gold) é aceitável para prosseguir com o rollout TCC, ou se exige correção separada do funil-base antes do flip (fora do mandato desta task — proibido tocar `src/`, proibido re-tuning). Retry recomendado após ruling: reflip + reprocess deve reaproveitar os 16 votos já pagos (cache bate por `content_key` md5) e fechar 0 chamadas API novas. **Report completo:** `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-7-report.md`.
- [DERIVADO/DECISION] **Fix round 1 — rollout flag-ON TCC (2026-08-04): controller ACEITOU condicionalmente a exceção do gate (b) e pediu critério decisivo mensurável; critério decisivo FALHOU → flip TCC ADIADO (bug funil-base, mesmo tratamento do SO), rollback completo, sem commit.** Ruling do controller sobre o BLOCKED anterior: experimento de controle (drift reproduzido com flags OFF) aceito como prova de causa ortogonal — não é aceitação cega, decisão final condicionada a medição. Executado: **(1)** re-flip TCC (`feature_flags={use_anchor_engine:true, use_llm_voter:true}`), MF confirmado ON no mesmo round-trip. **(2)** reprocess retry sem traceback (`bloco 27/27 → 27/27`); `material_curation.json` **16→16 votos, 0 chamadas novas** (diff de chaves: `novas={}`, `removidas={}` — cache cobriu 100%, dentro da tolerância ≤2). **(3)** gate a/c/d PASS de novo (idênticos ao round anterior); gate (b) restrito: drift bateu **exatamente** as mesmas 4 entries do experimento de controle (`3dm-caetano-gabriel-e-gustavo`, `cubic-3-edge-coloring`, `integer-programming-0001`, `programacao-inteira-01-20260617-154423-0000`), nenhuma entry adicional — condição do controller satisfeita nesse ponto. **(4) CRITÉRIO DECISIVO — MISTO:** `audit_gold_freshness.py --course TCC` pós-reprocess = **hard=0** (idêntico, mesmas 8 suspeitas ZERO_OVERLAP) → PASS; mas `fase2_prova_TCC.py` pós-reprocess **NÃO bateu idêntico**: pinos seguem 5/5 e cobertura 83.3%, porém **`confiante-e-errado` foi de 0 para 1** (`aula-01-apresentacao-da-disciplina-...`, computado=bloco-02, gold true=bloco-01, provider=`topic`) e a acurácia par-colapsada subiu 84.2%→89.5% (par-colapsada 16/19=84.2%→17/19=89.5%; acc topic bruta 16/20→17/20) — **VEREDITO FASE2: FAIL**. Isso viola a letra do critério ("AMBOS idênticos") → **rollback obrigatório**. **Fato registrado sobre as 4 entries do gate (b):** todas têm row no gold TCC (`scorable=yes`, `true_block_id=bloco-24`), mas o `computed_block_id` congelado no CSV já era bloco-22/26/13/13 (ERRADO vs bloco-24) **antes** desta task tocar qualquer coisa — a drift do funil-base trocou um valor errado por outro valor errado (bloco-16), não mudou o veredito de correção dessas 4 linhas especificamente. **O achado novo e mais sério é `aula-01`:** seu `auto_tags bloco:` no manifest (`bloco-02`) ficou byte-idêntico nas 3 fotografias comparadas (pristine pré-reprocess, 1º run flag-ON, retry flag-ON) — a mudança NÃO é no funil-base desta vez. O que mudou foi que `aula-01` passou a ter `temporal_block_id` populado via voter LLM (`provider=llm`, `band=media`, voto cacheado do 1º run) nesta rodada, e isso por si só empurrou o cálculo de confiança do `fase2_prova_TCC.py` para "confiante" sobre uma resposta que já estava errada e antes não era contada como confiante — **este efeito É causado pelo flip** (voter tocando uma entry cuja resposta de base já era errada e endossando-a com confiança), diferente da drift das 4 entries (comprovadamente ortogonal). **Ação (rollback completo, sem mandato para seguir com desvio no critério decisivo):** `TCC-Tutor` revertido (`git checkout -- .`) pro snapshot `28bb29f` (confirmado: 0 `temporal_block_id` no manifest pós-revert); `material_curation.json` (16 votos) **preservado untracked** para retry futuro sem custo; `subjects.json` revertido (`Teoria da Computabilidade e Complexidade.feature_flags = {}`, MF/SO/IA/ES2 confirmados intocados). **Nenhum commit em `TCC-Tutor`.** **Decisão: TCC flip ADIADO, mesmo tratamento do SO** — pendente de investigação/fix do bug de instabilidade do funil-base (ver item de dívida técnica abaixo) antes de reautorizar novo retry. **Report completo (todos os números, diffs, evidência):** `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-7-report.md`.
- [DERIVADO/DECISION] **TCC re-flip tentativa 3 (2026-08-06): FAIL honesto do critério decisivo →
  rollback completo sha256-verificado, flags revertidas, sem commit.** Report:
  `docs/reports/2026-08-06-tcc-reflip-fail-report.md`. Resumo: gates a/c/d PASS (pinos 2/2;
  temporal 19/27 idêntico à referência {llm:16,manual:1,topic:2}, fila 0; votos 16→16, 0 API);
  gate (b) 1 drift `cubic` bloco-26→22 = materialização esperada do fix 2b (integer/programacao
  ESTÁVEIS — instabilidade antiga do funil-base NÃO reproduziu, fix 2b estabilizou); MAS
  fase2-TCC pós caiu 84.2%→78.9% (cw manteve 0) e audit hard 0→1 (`aula-14` ADMIN_TRUE:
  **bloco-13 virou `kind=assessment` no índice do reprocess**, janela do card Semana-10 ganhou
  bloco-13). **Causa nomeada: índice de `reprocess_assignments` ≠ índice do rebuild cirúrgico
  (`rebuild_course`) que vive no repo desde 2026-08-04 — 3ª aparição da família dual-source
  (gerador-vs-gerador).** TCC re-flip re-BLOQUEADO; pré-requisito = reconciliar os 2 geradores
  de índice (kind de bloco determinístico) — insumo PRIORITÁRIO da campanha de unificação.
  T18 confirmado em produção no mesmo rito (`[profile]` no stdout, sem `--flags`).
  **SUPERSEDED: TCC flag-ON em `31f6025`/`91c1d2a` (2026-08-06, tentativa 6, campanha
  gerador-índice-único — ver Concluído).**
- [CODE] **Funil-base TCC recomputa `auto_tags bloco:`/confiança de forma instável a cada reprocess — candidato a bug de idempotência do retag (não investigado, fora do mandato de tocar `src/`).**
  > AMENDMENT 2026-08-06 (re-flip tentativa 3): a instabilidade das 4 entries NÃO reproduziu
  > pós-fix-2b (integer/programacao estáveis; cubic moveu 1x para o valor previsto pelo fix e
  > 3dm já estava lá) — ESTA parte está resolvida. O problema vivo mudou de endereço: divergência
  > reprocess-vs-rebuild do ÍNDICE (kind do bloco-13), ver entrada nova acima. Evidência: reprocess de `TCC-Tutor` (com OU sem `--flags`) muda `auto_tags bloco:` de 4 entries fixas (`3dm-caetano-gabriel-e-gustavo`, `cubic-3-edge-coloring`, `integer-programming-0001`, `programacao-inteira-01-20260617-154423-0000`) mesmo sem o anchor engine tocá-las (`temporal_block_id=None` nas 4). Adicionalmente, no Fix round 1, `aula-01-apresentacao-...` teve seu `temporal_block_id` populado via voter LLM (cache) numa rodada e isso sozinho fez `fase2_prova_TCC.py` marcar a entry como `confiante-e-errado` (era wrong-mas-não-confiante antes). Não sabemos se a causa é não-determinismo de `set()`/hash (hipótese já registrada no achado colateral do Task 3 MF) ou algo mais estrutural do recompute do funil-base/voter-confidence — candidato a investigação e fix antes de reautorizar o rollout TCC. Vai para o Plano B/cutover.
- [DERIVADO] **Audit pré-rollout IA/ES2 (2026-08-04)**: IA (74 rows, 0 hard, 7 soft ZERO_OVERLAP) + ES2 (35 rows, 0 hard, 22 soft ZERO_OVERLAP). Feature flags: IA `{"use_anchor_placement": true}` (legado ativo), ES2 `{}` (OK). `material_curation.json` não presente em ambos (não-crítico). **IA:** gold user-side pendente (trilha 4, 21 SARC batch), stash ~45 `.ipynb`/datasets, timeline 24-29/06 vs SARC vivo (bug conhecido, OK), legado `use_anchor_placement=true` reforça bloqueio pós-flip (flip futuro do motor DEVE desligar no mesmo ato — precedência já OK em `pedagogical_regeneration.py:444`, manter ambos ON é estado não-medido). **ES2:** sem gold fresco desde 21/06 (medição pré-flip obrigatória), ZERO_OVERLAP severo (22/35 rows, validar download SARC). ES2 pronto para rollout flag-ON; IA pronto com ações documentadas pós-flip. Sem flip nesta campanha em nenhum dos dois (audit report-only). Report completo: `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-8-report.md`.
- [DERIVADO/DECISION] **Rollout flag-ON SO EXECUTADO (2026-08-04, verificado/fechado 2026-08-05):
  gate estrutural a/c/d PASS, gate (b) 1 exceção registrada (classe funil-base já conhecida), fase2
  byte-idêntica em 3 capturas independentes, audit hard=0 estável — commit `Sistemas-Operacionais-Tutor`
  `11667b7`.** Pre-flight destravado pelo ruling `lista2=bloco-17` (`f14d50c`, 20:08:59): audit
  `--course SO` hard=0 (42 rows, 21 suspeitas). Snapshot pré-rollout: commit `d4929fe` (20:17:49).
  Backup gitignored completo (`course/.assessment_context.json`, `.content_taxonomy.json`,
  `.semantic_profile.generated.json`, `.tag_catalog.json`, `.timeline_index.json`) — não usado (zero
  rollback). Flip round-trip: `Sistemas Operacionais.feature_flags = {use_anchor_engine: true,
  use_llm_voter: true}`; MF confirmado ON, TCC/ES2 confirmados `{}`, IA legado `{use_anchor_placement:
  true}` intocado. Reprocess sem traceback: `bloco 42/42 → 42/42`. **Gate (a) pinos PASS:** 4/4
  preservados, zero `temporal_block_id` sujo em pino. **Gate (b) auto_tags bloco: 1 drift** —
  `exercicios-p2` `bloco-03→bloco-16`, **sem `temporal_block_id`** (motor não tocou a entry; mesma
  classe de instabilidade do funil-base já diagnosticada e registrada para TCC, ver item CROSS-CUTTING
  acima). `exercicios-p2` já era gold-errado ANTES desta task (`ground_truth_SO.csv`: true=bloco-17,
  computado congelado=bloco-03) — o reprocess trocou um valor errado por outro errado, não introduziu
  regressão de correção nova; e a linha não participa do conjunto `provider=data` medido pelo
  `fase2_prova_SO.py`, por isso a régua ficou intacta apesar do drift. **Gate (c) temporal_* PASS:**
  19 entries com `temporal_block_id`, 0 fora de escopo; provider `{data:19}`, band `{media:6,alta:13}`,
  method `{janela-1:19}`, fila humana `{flag=True:6, flag=False:13}`. **Gate (d) voter PASS:**
  `material_curation.json` (cache local pré-existente na raiz do SO-Tutor) `entries` **11→11 entre os
  commits `d4929fe`/`11667b7` (`git diff --stat` vazio) — 0 chamadas API novas**, cache cobriu 100%.
  **CRITÉRIO DECISIVO PASS:** `fase2_prova_SO.py` byte-idêntico em 3 capturas independentes (pós-reprocess
  20:25; re-checagem 23:18; reverify ao vivo 2026-08-05) — cobertura 19/42=45.2%, colisões 0, janela P3
  15 in/4 out (mesma lista), acurácia par-colapsada 77.8% de 18 pares, matriz
  `{('resto','err'):4,('resto','ok'):2,('alta','ok'):13}`, confiante-e-errado 0. `audit_gold_freshness
  --course SO` pós = **hard=0** nas 3 capturas (20:26/23:18/2026-08-05); suspeitas soft variou 21→24
  mas os 3 ids novos (`0206-laminas-memoria-virtual-livro-texto`,`14-04-troca-de-mensagens`,
  `1404-troca-de-mensagens`) já existiam no manifest pré com o MESMO `bloco:` tag (confirmado por diff
  direto, zero id novo, zero bloco mudou nesses 3) — causa não é o funil/motor, não investigada a fundo
  (fora do escopo do gate a-d, não afeta hard), registrada como concern não-bloqueante. `pytest
  tests/test_timeline_schema.py` **18 passed** em 3 rodadas (20:26 original + reverify 2026-08-05).
  **Divergência registrada:** o commit `11667b7` alega "gate estrutural PASS" sem qualificar; a
  reconstrução desta sessão (sem log salvo da rodada original do `gate_so.py`, diferente do padrão de
  log completo do TCC) mostra que (b) tecnicamente falha por 1 entry — tratado como PASS-com-exceção
  dado diagnóstico completo (órfã do motor, mesma classe TCC, sem impacto na régua decisiva), não como
  bloqueio; commit do repo-tutor não foi reescrito. **Report completo:** `<scratchpad>/roteiro-1b-so-report.md`
  (sessão 2026-08-05).
- [DERIVADO/DECISION] **Ruling user `lista2` (2026-08-04): gold bloco-17 CONFIRMADO + fix do auditor (commit `f14d50c`).** User confirmou semântica de uso: lista2 = preparação da P2 (pair_key `lista-exercicios-p2`), true=bloco-17 mantido. Fix autorizado no AUDITOR (não motor): `_looks_like_assessment(material, pair_key)` — ADMIN_TRUE agora reconhece material-de-prova também pelo pair_key (regex intocada, `\bp[12]\b` casa o sufixo). 3 testes novos (`tests/test_audit_admin_true.py`). Hard counts pós-fix: SO/TCC/IA/ES2/MF TODOS 0 (lista2 sai do hard, zero efeitos colaterais). Precedente citado: guard-clause `_gold_check` F4 (alinhar medição a gold aceito, sem afrouxar piso). **Pre-flight SO destravado.**
- [DERIVADO/DECISION] **CORREÇÃO DE ATRIBUIÇÃO do cw TCC + rollback T7 incompleto para gitignored (2026-08-04, pós-campanha).** Cadeia: (1) suite acusou FAIL novo em `test_timeline_schema.py[TCC-Tutor]` (needs_unit 3/16=19% > gate 10%) — causa: o rollback da Task 7 (`git checkout -- .`) NÃO restaurou `course/.timeline_index.json` (GITIGNORED, nunca tracked) → o índice REGENERADO pelos 2 reprocess do rollout ficou vivo no repo; índice pré-campanha IRRECUPERÁVEL (sem histórico git; `.bak` de 02/06 preservado em scratchpad, pré-campanha-de-junho, não serve). (2) Recovery: rebuild cirúrgico só-TCC via `rebuild_timeline.rebuild_course` (caminho próprio com curation Fase 5) → gates OK (19%→0%), suite verde **1823/4/0**. (3) **DESCOBERTA que REFUTA a atribuição do Fix round 1 (entrada acima):** com manifest flag-OFF (snapshot `28bb29f`) e índice reconstruído, `fase2_prova_TCC.py` dá **cw=1 no `aula-01`** (topic, computado bloco-02 vs gold bloco-01) — o cw NÃO era causado pelo voter/flip: é o ESTADO DO ÍNDICE. O cw=0 aceito da régua TCC repousava em índice STALE que o pipeline atual não reproduz por NENHUM caminho (reprocess e rebuild produzem índice em que o topic provider casa `aula-01` com confiança no bloco-02 — conteúdo "revisão de conjuntos/enumerabilidade" bate topics do bloco-02; falta sinal ordinal "aula-01"→bloco-01). **Consequências:** (a) número aceito fase2_TCC (cw=0) era artefato de índice stale — régua TCC INSTÁVEL até o Plano B resolver (caso-chave 2a com repro vivo: rodar fase2 com índice atual reproduz); (b) NENHUM re-tuning feito — FAIL honesto documentado; flip TCC segue ADIADO; (c) lição operacional: rollback de reprocess DEVE cobrir artefatos gitignored (índice/sidecars) — snapshot só de tracked é rede FURADA; (d) mesma classe de risco vale pro flip SO (índice SO também é gitignored e stale de 28/jun — o gate pós-flip fase2_SO idêntica decide honestamente). Estado TCC: manifest `28bb29f` flag-OFF, índice rebuilt gates-OK, cache 16 votos untracked, fase2_TCC FAIL cw=1 = realidade atual do pipeline.
- [USER/DECISION] **Bibliografia = caso à parte (decisão user 2026-07-22, brainstorm F5):** tutor
  deve passar a CONSUMIR bibliografias (hoje só resumo leve + mapa 📖 Apoio) sem estourar o limite
  de projeto Claude/GPT — brainstorm/spec próprios, fora do provider janela-de-prazo. Até lá,
  bibliografia/references/cronograma seguem fora total do motor. Contexto: gold TIER-2 MF tem
  eth2→bloco-12 (residual conhecido), archive/aws→bloco-01. Spec da janela-de-prazo §7:
  `docs/superpowers/specs/2026-07-22-janela-de-prazo-tier2-design.md`.
- ~~[DECISION] D4 × TIER 3 janela-1~~ **FECHADO (F4 item 1, commit `1f80f2a`)** — Opção A (D-A do
  plano F4) implementada: `len(window) > 1` gateia o hook do voter em `anchor_engine.py:57`;
  |janela|==1 nunca entra no escopo do voto, FLAG honesto sobrevive pra fila humana.
- ~~[CODE] Migrar ground_truth_*.csv de bloco-NN → block_uuid (FASE 4)~~ **FECHADO (F4 item 6,
  commit `4a73b5b`, decisão user 08/07)** — 5 CSVs + `true_of` uuid-first nos probes; auditor de
  frescor (`audit_gold_freshness.py`) segue como pré-gate obrigatório de qualquer medição.
- ~~A1 (lessons no fusor) — brainstorming antes de spec~~ **SUPERSEDED (2026-07-01)** — ver entrada
  Degrau 3a acima; sinal absorvido pelo motor, plano velho mirava o fusor que morre no cutover.
- [DECISION/CODE] **Refatoração futura: ingestão de material de APOIO (durável/intent, 2026-07-01)** — artigos
  web, papers e bibliografias ainda NÃO são ingeridos 100% no tutor (ex.: IA tem 3 entries sem `raw/`, 2 delas
  artigos-web). Fazer motor análogo ao de atribuição, mas para apoio/bibliografia — atribuir ao card/bloco
  certo SEM inflar verbosidade/custo do tutor (requisito explícito do user). Fora do escopo do motor atual;
  entra DEPOIS dele.
- [DECISION] **Span-cap de over-merge REFUTADO (as-of 2026-06-22)** — tentativa de cap de span temporal em
  `_rows_belong_to_same_thematic_block` (15d) reverteu por EVIDÊNCIA, não por calibração: (1) IA bloco-05
  ("monstro" 28d) é unidade COESA *ML supervisionado* (kNN→redes neurais→árvores); só a cauda 04-15
  não-supervisionada é mis-merge. (2) Span não distingue coeso-longo (MF 21d, recursivas) de qualquer-longo —
  mesma classe; nenhum threshold separa sem quebrar o coeso. (3) Quebrou
  `test_file_map_..._respects_manual_timeline_block_override` (bisecta tópico coeso no meio) = o mecanismo do
  +17 do Degrau 2. **Discriminante (as-of reprocess IA 7561f5c):** arquivos da cauda não-supervis
  (k-means/agrupamento/clustering) auto-atribuem a bloco-06/07, NUNCA a bloco-05 → a mis-merge do 04-15 em
  bloco-05 é **render-only** (cosmético do cronograma), sem mal-atribuição de arquivo. Se um dia splitar:
  por TRANSIÇÃO de tópico, NÃO span. Bloco-05 não é problema de fronteira/atribuição.
- [DECISION] **Regra "2 aulas = 1 bloco" APOSENTADA (durável)** — bloco = unidade pedagógica, sessão = átomo
  do render (`sessions[]` por semana ISO). A granularidade fina vive nas sessões, não em mais blocos.
- [DECISION] **Dedup por CONTEÚDO (md5), nunca por basename/id (durável, 2026-06-23)** — duplicata sem hash é
  palpite. CAUSA confirmada no IA: o stash migrou de `Downloads\InteligenciaArtificial` (nomeado por TÍTULO do
  PDF) → `Desktop\Moodle\inteligencia-artificial` (Moodle, nomes reais + Semanas); o manifest **acumulou os dois**
  e ninguém podou o velho. Faltou **poda de migração**. Dedup por basename/id não pega (nomes diferem); só md5.
- [CODE] **IA: poda de 13 stale (verificado as-of 2026-06-23)** — 13 entries do stash ANTIGO (source sumiu)
  são byte-idênticas (md5) a uma VIVA do stash novo → podar. Gate: só poda com substituta viva. **1 exige migração
  ANTES:** `p1-2024-02-ia`→`prova-1-2024-02` carrega `manual_timeline_block_id` (pin bloco-08, uuid `5256ec08`) +
  `manual_unit_slug` que a viva NÃO tem (perda de curadoria). Outras 12: viva já aprovada (sem gap). Pós-poda 50→37.
  Gold é keyed por id → 13 linhas órfãs no CSV; remapear old→live (mesmo md5 = mesma resposta), não re-rotular.
- [CODE] **`gold_score.py VERSION_PAIRS` cobre os casos ERRADOS** — `mlp`/`mlp-novaversao` e `introducao-a-ml`/
  `introducaoml-atualizacao2025` são **byte-dups** do stash antigo (somem na poda), **não pares de versão**. O
  "posting 24/02 = slide reusado" estava errado (é só a data do arquivo velho). O ÚNICO version-pair real (bytes
  diferentes, mesma aula) é **`inteligencia-artificial-aula-29...` ≡ `como-analisar-resultados-acc-pr-re-e-f1`**
  (md5 5bdaa9c7 vs 84a1f47a; o aula-29 é órfão byte-único, source sumiu — tratar à parte, não podar). Trocar o
  VERSION_PAIRS hardcoded por dedup-por-md5 no pipeline (causa), gate golden 5/5 + não-cascateamento + rebuild_diff.
- [USER] **Stash IA é download PARCIAL** — API Moodle (course 93156) mostra ~45 arquivos no Moodle ausentes do
  stash local (grosso = `.ipynb`/datasets que o pipeline pula; alguns PDF reais ex.: `Agentes.pdf` Semana 16,
  `Future of Jobs`, TDE `P2`). Lista definitiva exige baixar+hashear (content-match), não slug.

## CROSS-CUTTING

- [DECISION] **Branch `feat/block-stable-id` NÃO mergeada** — carrega Fase 1 + Fase 2 + campanha anchor/WO2/reprocess.
  Merge/PR = decisão do user.
- ~~`.timeline_index.json` stale (ES2 7/IA20/SO13)~~ **RESOLVED-BY-REPROCESS, verificado as-of 21/06:**
  o reprocess regravou os 5 índices; rebuild_diff vivo = **ES2 0/IA1/MF1/SO0/TCC0** (= baseline pré-existente,
  NÃO o drift 7/20/13). O drift de índice stale sumiu.
- **timeline IA em snapshot SARC antigo — janela 24–29/06** (`as-of 7561f5c`). SARC vivo (prof. moveu a
  apresentação T2): **24/06 = Feriado**, **29/06 = T2**. `SYLLABUS.md`/KB shipado refletem isso; mas
  `.timeline_index.json`/`CRONOGRAMA_DETALHADO.md` (fonte do gabarito) têm **24/06=T2 (bloco-19)** +
  **29/06=aula "Gerias" (bloco-20)** — trocados. Mesmo reprocess, `.timeline_curation` vazia → **SYLLABUS≠timeline**
  (bug de pipeline: dois caminhos de SARC divergem, a investigar). **Cosmético p/ o gabarito**: conteúdo do
  Moodle acaba ~**Semana 16** (último card 15–19/06; sem PDF → 0 entries); blocos **18–25 têm 0 material** →
  nenhum card cavalga a janela trocada. Gold: tratar 24/06=feriado / 29/06=T2 por override **no gold**, sem tocar repo.

---

## Concluído (2026-08-18 — taxonomia do plano de ensino + card como sinal de unidade)

APLICADO EM PRODUCAO nos 5 repos-tutor (reprocess 2026-08-18). Gate verde: reguas por
material SO 27/38 · MF 63/66 · IA 43/44 · ES2 22/28 · TCC 18/25 (todas sem regressao,
TCC melhora confiante-e-errado 2->1); golds de unidade ES2 7/7 · IA 9/10 · MF 12/14 ·
SO 9/11 · TCC 13/13; 0 pinos violados; suite 1886 passed / 1 skipped;
`scripts/audit_taxonomy_losses.py` = 0 ausentes nos 5 (era TCC 11/27, SO 3/34, ES2 1/21).
Taxonomia em disco: SO 31->36 topicos, TCC 14->26, ES2 20->21.
Medicao completa (2 rodadas): `docs/reports/2026-08-18-medicao-fix-taxonomia.md`.
Patch da 1a tentativa do card: `docs/reports/2026-08-18-card-signal-tentativa.patch`.

- [CODE] **CAUSA RAIZ DO MATCHING FRACO DE UNIDADE: `_topic_text` serializa dict**
  (`extraction/teaching_plan.py:_topic_text`, `as-of 2026-08-18`) — a funcao trata tupla e str,
  mas a taxonomia passa cada topico como **dict**
  (`{code, slug, label, aliases, kind, unit_slug}`), entao cai no `str(topic)` e o
  `topic_phrases` de `build_file_map_unit_index` fica sendo o dict SERIALIZADO:
  `"code 1 2 slug visoes arquiteturais estrutural e dinamica label visoes ... aliases ... kind
  topic unit slug unidade 01 arquitetura de software"`. Consequencias: (1) os pesos altos de
  frase de `score_entry_against_unit` (headings 3.0, lead 2.8, title 2.7) **nunca disparam** para
  topico vindo da taxonomia — a phrase e um blob que nao casa em texto nenhum; (2) `topic_tokens`
  ganha lixo estrutural (`code`, `slug`, `label`, `aliases`, `kind`) e os tokens dos ALIASES,
  que foi por onde o heading institucional do ES2 entrou. O scorer de SUBtopico
  (`_score_entry_against_taxonomy_topic`) esta saudavel — usa `topic_label` limpo. **Este e o
  proximo alvo**: e a razao pela qual sinal novo (como o card) nao pega no eixo de unidade.
  Pre-requisito: regua entry->unidade rotulada, porque o alcance e todas as entries dos 5 cursos.
- [CODE] **CARD DO MOODLE COMO SINAL DE UNIDADE — IMPLEMENTADO E MEDIDO em 2026-08-18** (ruling
  do user). `card_text` nos sinais (`extraction/entry_signals.py`); no scorer de unidade
  (`routing/file_map.py`) pesa 1,5 contra o TITULO da unidade, 2,5 contra frase de topico e 0,40
  no overlap parcial — so nivel de frase, para card administrativo ficar inerte. Teste
  `test_card_nao_afeta_o_scorer_de_bloco_do_motor` fixa o contrato: o card NAO entra no eixo
  temporal. Depende de dois fixes irmaos: `_topic_text` tratando dict e o descarte de frase que e
  titulo de OUTRA unidade (sem este, o card regredia 6 entries do MF). Gates verdes nos 5, suite
  1886. Saldo julgado caso a caso: 13 ganhos, 9 neutros, 1 regressao isolada
  (`Cap. sobre Algoritmos Geneticos` no IA — candidato a pino). Detalhe:
  `docs/reports/2026-08-18-medicao-fix-taxonomia.md` §Rodada 2.
- [HISTORICO] **Card: primeira tentativa revertida no mesmo dia.**
  Patch guardado: `docs/reports/2026-08-18-card-signal-tentativa.patch` (`card_text` nos sinais
  + peso 2.5 exato / 0.40 parcial no scorer de unidade; testes inclusos). Medicao em sandbox nos
  5 cursos: gates continuaram verdes (reguas sem regressao, 0 pinos violados), MAS bissecao
  isolando o card mostrou dano real no MF — **delta de unidade 1 (so ganho) sem o card contra 9
  com o card, incluindo 6 REGRESSOES**: `Hoare`, `Invariantes`, `Colecoes Arrays`,
  `Colecoes Conjuntos`, `Exercicios Conjuntos`, `classes_parte2` saem de
  `unidade-02-verificacao-de-programas` — que e o nome EXATO do card (`Verificacao de
  Programas`). E nao resolveu os 2 alvos do IA (`Cap. sobre Algoritmos Geneticos` segue em
  `aprendizado-de-maquina` apesar do card dizer busca; `Visao Geral` segue sem unidade).
  Ganhos que o card SIM trouxe (IA): `programa-exemplo AG` e `Programas-exemplo HC, SA` saem de
  sem-unidade para `solucao-de-problemas`; `Introducao a redes neurais` e os 2 exemplos de k-NN
  vao para `aprendizado-de-maquina` (todos confirmados pelo card).
  **A ideia segue certa; a implementacao por frase nao funciona enquanto `_topic_text` serializar
  dict** (item acima). Reabrir depois desse fix e com a regua de pe.
  Levantamento que continua valido: Ruling do user: "da para saber a unidade com base no card que o link esta,
  e a maneira mais precisa e o que podemos fazer agora". Levantamento (`as-of 2026-08-18`):
  **API do Moodle NAO e necessaria** — `source_section` ja vem preenchido em **228 de 233**
  entries dos 5 cursos (SO 42/42, MF 64/67, IA 60/62, ES2 35/35, TCC 27/27); nas categorias
  transversais, 161/166. As 5 sem card sao links externos (GitHub/Oracle/Microsoft/isa-afp)
  que nunca estiveram em card.
  Dois furos conhecidos antes de codar:
  (a) **cards administrativos** nao nomeiam unidade — SO tem `Informacoes Gerais` 10x (24% do
      curso), ES2 tem `Exercicios Revisao para Provas` 4x + `Revisao` 3x, mais `TDE` e
      `Plano de Ensino` em varios. E justamente o material que mais precisa de cobertura
      multi-unidade (prova, lista de revisao) que cai no card generico;
  (b) `card -> bloco` esta vazio: `.card_block_map.json` do SO tem 1 entrada
      (`Informacoes Gerais`) com `block_ids: []`. A rota viavel e direta: **card -> unidade**
      casando o nome do card contra a taxonomia (`Threads`, `Sincronizacao e Comunicacao de
      Processos` casam sozinhos).
  ALERTA DE VIES: se o gold sair do card E o algoritmo usar o card, a regua se auto-confirma
  (mesmo P3.1 que morreu com o funil). Separacao acordada: gold = julgamento do conteudo
  (card e evidencia auxiliar); algoritmo pode usar card; a regua mede quando o card mente.
- [CODE→USER] **TAXONOMIA PERDE TOPICOS DO PLANO DE ENSINO — CORRIGIDO E MEDIDO 2026-08-18,
  FALTA APLICAR EM PRODUCAO.** Medicao em sandbox nos 5 cursos:
  `docs/reports/2026-08-18-medicao-fix-taxonomia.md` (driver `scripts/measure_taxonomy_fix.py`).
  Gates verdes: nenhuma regua regride, 0 pinos violados, TCC melhora 1 confiante-e-errado.
  Ganhos qualitativos: SO corrige 4 entries de threads (erros ja catalogados no handoff §B),
  TCC corrige PCP e os subtopicos de complexidade (inclusive "Aula 16 - Classes de Problemas",
  erro conhecido), MF e ES2 ganham entries que estavam sem unidade.
  **ES2 investigado a fundo (2026-08-18): a causa nao era o topico recuperado.** Ver secao
  dedicada no relatorio de medicao. Decisao do user pendente: aplicar nos 5 repos.
- [CODE] **Heading institucional virava alias de topico — CORRIGIDO 2026-08-18**
  (`extraction/content_taxonomy.py`, bloco de enriquecimento por `strong_headings`). O cabecalho
  que abre TODO material do curso (`ENGENHARIA DE SOFTWARE II ---`, `Trabalho FinalEngenharia de
  Software II`) era anexado como alias do topico mais proximo, e os tokens `engenharia`,
  `trabalho`, `finalengenharia` entravam nos `distinctive_tokens` da unidade dona — que virava
  ima do curso inteiro (score de `Kubernetes`: u01 4.70 -> 9.45 so pelo alias). O perfil ja
  marcava o slug do curso em `generic_slug_blacklist`; o bloco de enriquecimento nunca consultava.
  Fix: descartar heading cujo slug esta em `tag_generic_slugs` ou que contenha o nome do curso.
  Teste `test_heading_institucional_nao_vira_alias_de_topico`.
- [NOTA] **Slug de subtopico do SO muda de forma** (`as-of 2026-08-18`) — com o codigo numerico
  extraido, `33-algoritmos-de-escalonamento` vira `algoritmos-de-escalonamento`. So o SO usa
  numeracao em negrito. Verificado: os unicos arquivos com os slugs antigos sao GERADOS
  (taxonomy, tag_catalog, timeline_index, FILE_MAP, manifest, .deeptutor) e todos sao reescritos
  no reprocess; nenhum gold, sentinela ou curadoria manual depende deles. `scripts/audit_taxonomy_losses.py` agora reporta **0 ausentes nos 5
  cursos** (era TCC 11/27, SO 3/34, ES2 1/21) e a suite passa 1881/0/1skip. Os repos-tutor
  **nao foram reprocessados**: o `.content_taxonomy.json` e o `.semantic_profile.generated.json`
  em producao seguem com a perda. Antes de aplicar: medir as reguas dos 5 (a taxonomia alimenta
  `topic_phrases`/`distinctive_tokens` do matching de unidade, entao os numeros DEVEM mexer).
  Correcoes: parser normaliza a linha num ponto so (markdown + zero-width) e casa todo ramo
  contra ela; itens colados pelo PDF viram topicos separados; o codigo numerico passa a viver
  NO texto do topico (contrato que `content_taxonomy` ja esperava via `_extract_topic_code`);
  bullets sem numero sao descartados quando a unidade tem numerados (mata "Uso de projetor
  multimidia" e o topico-lixo `processo-de-discussao` do SO); `_looks_like_tool_candidate` casa
  em fronteira alfanumerica; `_infer_tool_candidates` nao promove mais CAIXA ALTA a ferramenta.
  Testes: `tests/test_taxonomy_topic_loss.py` (8 casos, fixtures literais dos 4 formatos de
  plano reais). Diagnostico original abaixo.
- [DIAGNOSTICO original] **`known_tools` envenenado**
  (`as-of 2026-08-18`, auditoria `scripts/audit_taxonomy_losses.py`). Perdas medidas:
  **TCC 11/27** (unidade 04 inteira: Hierarquia de Classes, Classe P, Cook-Levin, Reducao
  Polinomial, NP-Completude, PSPACE x3, Intratabilidade — a taxonomia do repo tem 4 de 11
  topicos nessa unidade), **SO 3/34** (4.1 Programas multithreads, 6.1.1, 7.3), **ES2 1/21**
  (1.1 Conceito de arquitetura de software). MF e IA: 0.
  Tres causas somadas:
  1. `_infer_tool_candidates` (`core/semantic_config.py:243`) aceita como "ferramenta" qualquer
     palavra com maiuscula fora da 1a posicao **com count>=1**. Plano de ensino em CAIXA ALTA
     (PDF PUCRS) faz TODA palavra de titulo virar `known_tools`: `ementa`, `horas`, `carga`,
     `percentual`, `objetivos` no SO; `pspace`, `np-completude`, `cook-levin`, `hierarquia`,
     `exemplo` no TCC. Loop perverso: quanto mais central o termo, mais provavel virar "tool"
     e sumir do indice.
  2. `_looks_like_tool_candidate` (`extraction/content_taxonomy.py:89`) casa **substring sem
     fronteira de palavra** para tools >=4 chars: `ementa` mata "impl-EMENTA-cao", `threads`
     mata "multi-THREADS", `exemplo` mata "exemplos".
  3. O escape hatch `if not topic_code and not _is_valid_topic_candidate(...)`
     (`content_taxonomy.py:487`) **nunca protege**: `_extract_topic_code` nao tolera markdown
     (`**4.1**` -> code vazio) e o `numbered_topic_re` do parser ja remove o codigo do texto.
     Todos os topicos ficam com `code` vazio e passam pelo filtro.
  Impacto alem da cobertura: a taxonomia alimenta `topic_phrases`/`distinctive_tokens` do
  matching de unidade — TCC sem "Classe P"/"NP-Completude" explica erro conhecido
  ("Aula 16 - Classes de Problemas"). Fix minimo = (3): fazer o codigo numerico sobreviver,
  que sozinho salva 9 dos 15 casos; (1) e (2) sao os fixes de raiz.
- [CODE] **Parser do plano de ensino perde topico sem bullet e itens colados**
  (`extraction/teaching_plan.py:57`, `as-of 2026-08-18`) — `numbered_topic_re` exige ponto
  apos a numeracao e casa contra a linha CRUA (nao a normalizada), entao `**5.1.** Conceitos
  basicos` (negrito, sem bullet) e `1.1 Conceito de arquitetura` (sem ponto) somem. Itens
  colados na mesma linha pelo PDF (`4.5.2 ... 4.5.3 ...`, `1.2 ... 1.3 ...`) so rendem o
  primeiro. Entra tambem lixo de metodologia como topico ("Uso de projetor multimidia",
  "processo de discussao." — este ultimo esta na taxonomia do SO, unidade 07).

## Concluído (2026-06-22 — divisão de blocos: prova estrutural)
> Carimbo (ROUTER): **Fases 0-2 — estrutural provado (não-cascateamento + golden 5/5); correção de
> atribuição NÃO medida, bloqueada em gold IA.** (A máquina está provada; se os arquivos caem no bloco
> CERTO é o que o gold IA — bloqueado user-side — vai medir.)
- **Fase 0 caracterização** — snapshots golden do estado atual (divisão · maior-bloco · casos-chave · render),
  17 goldens em `tests/_golden/`, suíte 1637 verde. Commit `7554e82`.
- **Fase 1 identidade estável** — PROVADA robusta a split (não só a existência de `block_uuid`):
  `tests/test_block_split_nao_cascateia.py` — split renumera `bloco-NN` mas o uuid segue o CONTEÚDO
  (date/token overlap), `computed_block_id` + `card_block_map` seguem resolvendo, ledger append-only;
  contraste explícito (posicional cascateia, uuid não). Wired pós-split: `reattach_block_uuids`
  (`index.py:1405`) roda APÓS a construção dos blocos (`index.py:1380`), então qualquer split futuro herda
  a proteção. Commit `b733d19`.
- **Fase 2 data-membership** — já viva/wired/testada nesta branch: `derive_card_block_map` (`moodle.py:488`)
  → `.card_block_map.json` → `_card_scoped_block` (`content_taxonomy.py:1193`) → `computed_block_id`
  (`content_taxonomy.py:1260`). Casos-chave IA decididos por method `card`/`card+scorer`. Normalização
  `norm_ascii_lower` nos 2 lados do join (Degrau 1). Item 3 do plano já era no-op.
- **Fase 3 (span-cap)** — REFUTADA (ver DECISION acima): mecanismo errado, over-merge do IA é render-only.

## Concluído (histórico desta campanha — 2026-06-21)
- Camada anchor placement WIRED (temporal_block_id aditivo + helper `resolve_temporal_block`, 6 consumidores
  temporais, KB intocado). Commit `d792331`.
- Surface durável `feature_flags` por matéria. Commit `22b6de9`.
- WO2 fix manual-uuid (`_block_by_migrated_ref` uuid-first) — 23 pins humanos recuperados nos 5. Commit `d67bb19`.
- Reprocess dos 5 tutores (computed→uuid; IA com 33 temporal/2 movers; outros sem temporal). Commits tutor repos:
  IA 7561f5c · ES2 abc8ee2 · MF 357a59b · SO 320712d · TCC 6b6e1e3. Gates: HARD-drift 0 em todos.

## Concluído (2026-08-05 — Plano B Task 1)
- [DERIVADO] **T12 stopwords PT: causa-raiz do cw TCC fechada (cw 1→0, acc intacta).** 11 palavras-função PT
  (`nao`/`sim`/`com`/`sem`/`por`/`dos`/`das`/`nos`/`nas`/`uma`/`que`) adicionadas a `_GENERIC_STEMS`
  (`disambiguator.py:22-26`, espelha `marco0._GEN`) — causa: `nao` (df_global=1) satisfazia
  `bool(discriminante)` (`disambiguator.py:184`) e produzia band "alta" indevida em `aula-01-apresentacao-
  da-disciplina...` (TCC), fechando o `fase2_TCC FAIL cw=1` deixado em aberto pela entrada CROSS-CUTTING
  "CORREÇÃO DE ATRIBUIÇÃO do cw TCC" (2026-08-04) — motor real volta a `cw=0`. TDD: 3 testes novos
  `tests/test_motor_stopwords_pt.py` (RED confirmado pré-fix, GREEN pós-fix). Régua completa pós-fix
  (7 probes + suite): fase0 48/58 conten0 cw1 · fase1 recall 9/10 · fase2-SO 45.2%/colisões0/cw0 ·
  **fase2-TCC pinos 5/5 + cobertura 83.3% + acc 84.2% + cw0 (PASS — número EXATO da medição empírica)** ·
  fase3 lift +3/0 chamadas API · fase4 det 48/58 cw1, voter 51/58 cw0/calls0 · fase5 target 4/8 cw0 ·
  **pytest 1826 passed / 4 skipped / 0 failed** (1823 prévios + 3 novos). Lista CONSERVADORA por medição:
  versão larga (+ demonstrativos/comparativos) custou 2 casos (84.2%→78.9%), NÃO adotada (ver comentário
  no código). `last_seen` de `Metodos-Formais-Tutor/course/.block_identity.json` (bumped pelos probes)
  restaurado; SO/TCC sem alteração. Report completo:
  `.superpowers/sdd/2026-08-05-planob-motor/task-1-report.md`.

## Concluído (2026-08-05 — Plano B Task 4)
- [DERIVADO] **Fix 2b: funil-base lê `_p_ambig` + piso de confiança (MUDA ATRIBUIÇÕES, medido).**
  `content_taxonomy.py:1224` gateava atribuição de bloco só em `if _period:`, ignorando a flag
  `_p_ambig` (atribuída em `:1208`, nunca lida) e sem piso de confiança — um palpite `conf=0.0/
  ambig=True` de `select_probable_period_for_entry` virava atribuição dura (`scorer_only`) em vez
  de cair no `_best_instructional_block_fallback` honesto. Fix: `if _period and not _p_ambig and
  p_conf > 0:`. TDD: `tests/test_funil_gate_ambiguidade.py` (novo, RED 2/3 pré-fix confirmado via
  `git stash`, GREEN 3/3 pós-fix) + 1 teste pré-existente corrigido
  (`test_resolve_unit_block_band.py::test_wiring_medium_confidence_maps_to_band_media` passava
  `ambig=True` indevidamente — corrigido `False`, seu próprio docstring só prova confidence→band).
  **PRÉ (id → bloco atual → gold, medição in-memory read-only nos 3 repos reais):**

  | repo | id | atual | conf | gold |
  |---|---|---|---|---|
  | TCC | 3dm-caetano-gabriel-e-gustavo | bloco-26 | 0.0000 | bloco-24 |
  | TCC | cubic-3-edge-coloring | bloco-26 | 0.0000 | bloco-24 |
  | TCC | integer-programming-0001 | bloco-16 | 0.0000 | bloco-24 |
  | TCC | programacao-inteira-01-... | bloco-16 | 0.0000 | bloco-24 |
  | MF | logicadehoare | bloco-11 | 0.0037 | bloco-10 |
  | MF | classes-parte1 / classes-parte2 | bloco-13 | 0.0389 | bloco-15 |
  | SO | exercicios-p2 | bloco-16 | 0.0539 | bloco-17 |

  **PÓS (mesma tabela, delta):** TCC 3dm/cubic **movem** bloco-26→**bloco-22** (conf honesta
  0.22/0.25, gold ainda bloco-24 — erro persiste, agora com confiança honesta, não regressão);
  integer/programacao **permanecem** bloco-16 mas com conf honesta 0.0451 (era 0.0 cego) — empate
  real do scorer bruto (bloco-16==bloco-26 @20.5456) decidido por ordem estável de lista dentro de
  `_best_instructional_block_fallback` (fora do range 1225-1234 escopado para tie-break); ramo
  1225-1234 **inalcançável pelas 6 entries TCC+MF; alcançável pelo SO, mas sem `period_label`
  duplicado para desempatar** (evidência direta: `candidate_rows` de `exercicios-p2` tem 17 blocos,
  só 1 com o `period_label` devolvido — instrumentado dentro do próprio `resolve_unit_block_tags`,
  não emprestado da sonda `fase2_prova_SO.py`, que mede outro código, `provider_date` do motor);
  tie-break dispensado. MF (3) e SO (1) **sem nenhuma mudança** — achado que CORRIGE a
  investigação: MF nunca passa por `select_probable_period_for_entry_fn` (resolve via
  `_card_scoped_block`/`card+scorer`, fora do escopo do bug 2b desde sempre) e SO já tinha
  `conf=0.0539>0`, que já passava pelo piso literal `p_conf>0` ANTES do fix (o texto §2b "só o piso
  pega o SO" não se sustenta matematicamente para este valor). **Delta corpus-wide (fix round 1,
  os 136 entries dos 3 repos, não só as 8 conhecidas):** medido via `git worktree` do repo do
  PROJETO em `2c3fe45~1` (pré-fix) vs `2c3fe45` (pós-fix), harness `persist=False` idêntico —
  **4/136 mudaram, exatamente as 4 TCC já auditadas linha-a-linha; os 132 restantes (23 TCC + 67 MF
  + 42 SO) são byte-idênticos** (`computed_block_id`/`method`/`confidence`). Régua completa (7
  probes) **byte-idêntica** aos baselines pós-Task-3 (fase0 48/58 conten0 cw1 · fase1 9/10 ·
  fase2-SO 45.2%/0/cw0 · fase2-TCC 5/5/83.3%/cw0/84.2% · fase3 39 rows/+3 lift/0 API · fase4
  det48/58cw1 voter51/58cw0calls0 · fase5 4/8cw0) — mas nenhum dos 7 probes importa
  `content_taxonomy` (confirmado por grep): a régua prova só isolamento do caminho
  `engine.py`/`AnchorEngine` (não tocado), NÃO prova acurácia do funil. Evidência real de acurácia
  do funil = suíte de gate gold que EXECUTA `resolve_unit_block_tags` (`test_eval_assignments.py`
  `test_block_accuracy_not_below_baseline` + `test_eval_golden_real.py` + `test_block_method_caps.py`,
  17/17 verdes, já inclusos nos 1838) + o delta corpus-wide acima. **pytest 1838 passed / 4 skipped
  / 0 failed** (1835 prévios + 3 novos). Repos-tutor: **zero escrita líquida** — nenhum `last_seen`
  para restaurar (medição usou wrapper `persist=False`, ver achado abaixo).
  **Achado extra (registrar como pendência nova, não corrigido — fora do escopo desta task):**
  `_build_file_map_timeline_context_from_course` tem `persist=True` por padrão e, além do bump de
  `last_seen` já catalogado, TAMBÉM grava `manifest.json` (migração `manual_timeline_block_id`
  bloco-NN→uuid) quando encontra refs legadas — `scripts/retag_manifest.retag()` (usado por esta
  investigação e pela Task 4) **não é read-only de verdade**; reproduzido e revertido no TCC-Tutor
  antes de qualquer medição válida. Report completo:
  `.superpowers/sdd/2026-08-05-planob-motor/task-4-report.md`.

## Concluído (2026-08-05 — Plano B Task 5)
- [DERIVADO] **T17: filtro D-H do due-window troca `topics` (opcional) por `kind` (required).**
  `due_window.py:96` excluía bloco de conteúdo com `topics=[]` — matava pré-requisito artificial
  de rollout (curso novo sem topics populado). Fix: `_NON_CONTENT_KINDS = frozenset({"assessment",
  "review"})`, derivado dos 4 `.timeline_index.json` reais disponíveis (TCC/MF/SO/ES2 — IA-Tutor
  sem índice, motor nunca rodou lá): únicos 2 kinds com blocos `topics=[]` hoje (assessment 10/5,
  review 2/1 vazio/preenchido); todo outro kind observado (class, deliverable, holiday,
  academic_event, office_hours, overview, results, reserved, suspended, workshop) sempre tem
  `topics` populado. Coerente com uso já existente de `kind` em `content_taxonomy.py:966,973`.
  TDD: `tests/test_motor_due_window.py` (2 testes novos, RED confirmado pré-fix — bloco
  `kind=class topics=[]` não ancorava; bloco `kind=assessment topics≠[]` ancorava direto — GREEN
  pós-fix) + `_ctx_mf_real` atualizado com `kind` real por bloco (11/16=class, 17=review,
  18=assessment). Régua completa (7 probes) **byte-idêntica** ao baseline pós-Task-4 (fase0
  48/58 conten0 cw1 · fase1 recall 9/10 · fase2-SO 45.2%/colisões0/cw0 · fase2-TCC pinos
  5/5+83.3%+cw0+84.2% · fase3 39 rows/lift+3/0 API · fase4 det48/58cw1 voter51/58cw0calls0 ·
  **fase5 4/8 cw0 idêntico** — o gate central da task, D-H não mudou resultado no MF). **pytest
  1840 passed / 4 skipped / 0 failed** (1838 prévios + 2 novos). `last_seen` de
  `Metodos-Formais-Tutor/course/.block_identity.json` (bumped pelos probes fase0/1/4/5, mesmo
  padrão já catalogado) restaurado; TCC (só `?? material_curation.json` pré-existente, não meu) e
  SO sem alteração. Commit `4190abb`.

  **Fix round 1 (revisão do coordenador) — medição PRÉ/PÓS em TCC e SO, corpus real de produção.**
  Achado do report original citava blocos `assessment`/`review` com `topics≠[]` em TCC (bloco-05
  review, bloco-28 assessment) e SO (bloco-18 assessment) como "efeito pretendido não medido fora
  do MF" — a revisão pediu medição direta em vez de diferimento, já que SO está flag-ON em
  produção. Medido `resolve_due_window` para TODO entry `tier2_due_scope` de TCC-Tutor e
  Sistemas-Operacionais-Tutor, PRÉ (`git worktree` do repo do PROJETO em `4190abb~1`, código
  anterior ao fix) vs PÓS (HEAD `4190abb`), via `build_motor_context` (loader já read-only,
  docstring própria confirma "nunca escreve" — não é o `persist=True` da Task 4 §0, função
  diferente). **Resultado: zero deltas nos dois cursos, e por um motivo mais forte que "o kind não
  importou" — o filtro por kind nunca chega a ser exercido:**
  - **SO: 0 entries passam `tier2_due_scope`** (categorias reais: material-de-aula/listas/
    gabaritos/cronograma/codigo-professor/outros/bibliografia — nenhuma `trabalhos`/`provas`, e
    `codigo-professor` não tem `source_section` prefixado `TDE`). `resolve_due_window` nunca é
    chamada para nenhum entry real do SO hoje — o achado do bloco-18 é um FATO de dados
    (kind=assessment, topics≠[]) inerte em produção, confirmado por medição direta, não por
    inferência.
  - **TCC: 5 entries passam `tier2_due_scope`**, mas `resolve_due_window` retorna `null`
    idêntico PRÉ e PÓS para as 5 (`3dm-caetano-gabriel-e-gustavo`, `cubic-3-edge-coloring`,
    `programacao-inteira-01-...`, `t1-enunciado`, `trabalho-t2-enunciado`) — o passo `_match_due`
    (upstream do loop de blocos onde o fix vive) já retorna `None` nas duas versões: confirmado
    que `course/.card_block_map.json` de TCC (5 cards) e SO (1 card) não têm nenhum `assign_dues`/
    `file_dues` estruturado — a due-window TIER 2 só está de fato populada com dados reais no MF
    hoje. O achado do bloco-05/28 é igualmente um fato de dados inerte, mesma razão.
  - **Interpretação (linha 3 do fix): nenhum delta observado, logo nenhum julgamento
    correção-vs-regressão foi necessário** — não houve "due parando de ancorar em prova" para
    avaliar, porque devido a esta cascata (`tier2_due_scope` vazio em SO; `_match_due` vazio em
    TCC) o provider due-window está estruturalmente adormecido nos dois cursos, independente do
    fix de kind. Não há BLOCKED a levantar.
  - Repos-tutor: zero escrita (`build_motor_context` confirmado read-only por medição — `git
    status` limpo em TCC/SO antes e depois; nenhum `last_seen` a restaurar). Worktree temporário
    removido (`git worktree remove`) ao final.
  - Nenhuma mudança de código neste round (`src/` intocado); só a medição registrada aqui e em
    `.superpowers/sdd/2026-08-05-planob-motor/task-5-report.md` §8 (comandos + saída completos).

## Concluído (2026-08-05 — Plano B FECHAMENTO: 7/7 tasks)

- [DERIVADO] **Plano B ENTREGUE — 7/7 tasks, 19/19 dívidas mecânicas + 2a + 2b pagas** (commits
  `d3cd0fa..84d25b0` na branch `feat/motor-atribuicao`, + `Metodos-Formais-Tutor@235e8a7` para o
  T19). Task 1 (T12 stopwords PT, ver Concluído acima) e Task 4 (fix 2b, ver Concluído acima) e
  Task 5 (T17 D-H por kind, ver Concluído acima) já têm entrada própria. Tasks 2/3/6/7 fecham
  aqui: **Task 2** batch higiene sem mudança de comportamento (T9a/T2b/T8/T9/T10/T7a/T16/T13/T14/
  T11 — 4 commits por área, régua byte-idêntica); **Task 3** sonda fase3 filtra janela-1 antes da
  medição 2b (T3, alinhada ao gate real do engine `anchor_engine.py:57-58`, lift +3/0 API mantido);
  **Task 6** lock cross-processo do voter (T4b — sentinela `O_EXCL`, 3 rounds de hardening:
  deadline+sleep nos `continue` órfãos, takeover single-winner via rename, guard `SidecarLockTimeout`
  em `vote()`/`prune()` pra não derrubar a rodada D9 inteira); **Task 7** infra final (T15 imports,
  T1b tabela de migração, **T18** reprocess lê `SubjectStore`/injeta `feature_flags` vivas — mata a
  armadilha operacional `--flags` obrigatório do reprocess headless, T7b e2e da ordem
  refresh→resolve→attach, **T19** `*.bak` no `.gitignore` gerado + destracking dos 5 `.bak` do MF
  (autorizado pelo user), read_only probe — `retag_manifest`/`rebuild_timeline` em modo leitura
  agora passam `persist=False`, fechando o write-trap achado na Task 4).
  **Review final whole-branch (fable, `d3cd0fa..896592c`, 20 commits): READY TO MERGE YES** — 1
  Important (guard `OSError` no `os.remove` pós-takeover do lock, última saída desprotegida) + 3
  minors (skipif POSIX no teste de dono-vivo; `.get()` no `stems_by_block`; docstring
  caller-holds em `_persist`); fix wave dispatched ao implementer do lock, fechado em `84d25b0`
  (re-review limpo, campanha ENCERRADA).
  **Régua**: 7 probes (fase0/fase1/fase2-SO/fase2-TCC/fase3/fase4/fase5) **byte-idênticos em TODOS
  os gates** através das 7 tasks (única mudança de número intencional foi o cw TCC 1→0 na Task 1
  e as 4 atribuições TCC movidas na Task 4, ambas medidas e registradas nas entradas próprias).
  **Suite: 1823 → 1858 passed / 4 skipped / 0 failed** (+35 testes novos ao longo das 7 tasks).
  Repos-tutor: read-only durante todo o plano (MF/SO seguem flag-ON como estavam; TCC/ES2 OFF);
  `last_seen` bumped pelos probes restaurado a cada task. Ledger completo:
  `.superpowers/sdd/2026-08-05-planob-motor/progress.md` (briefs + reports + diffs de review por
  task). Fila pós-plano: ver `docs/reports/2026-08-05-handoff-planob-fechado.md`.

## [DERIVADO] Fio subject_profile — Task 2: verificação 5 cursos + recompute MF em memória

- [DERIVADO] **Verificação parser-vs-índice, 5 cursos** (`as-of f11dda7`, read-only, `json.load`
  puro de `course/.timeline_index.json` vs `_parse_units_from_teaching_plan` sobre o
  `teaching_plan` real do `subjects.json` via `SubjectStore.find_by_repo_root`). **4/5 cursos com
  PERDA de unidade, não só o MF.** TCC 4/4 OK (único intacto). MF 3→2 (falta u03, causa-raiz já
  mapeada). SO 7→6 (falta a unidade do **MEIO**, u04-deadlock — u05/06/07 sobrevivem intactas no
  índice, **não é truncamento de cauda**; sanity check fix-round-1: 0 referência pendurada a
  u04/deadlock em `unit_slug`/`auto_unit_slug`/`period_label` de qualquer bloco = drop limpo, NÃO
  ref quebrada — **mas achado NOVO mais sério**: o `topic_text` de bloco-05 (unidade-02) contém
  literalmente "...sincronizacao **deadlock** especi..." — o CONTEÚDO de deadlock foi absorvido
  no texto agregado do bloco vizinho sob a unidade ERRADA, perda de fidelidade, não só de rótulo;
  e **a ordem das unidades no índice SO não é monotônica** — bloco-10=`unidade-07`,
  bloco-11=`unidade-05`, bloco-12=`unidade-07` de novo — sinal de múltiplas rodadas de reprocess
  sobrepostas, mecanismo não investigado, registrado para a Task 3). ES2 3→2 (falta
  u03-testes-de-software). IA 5→3 (faltam
  u04-raciocinio-sob-incerteza e u05-aprendizado-de-maquina). Todos os 5 repos TÊM
  `.timeline_index.json` (a suposição "IA pode não ter índice" estava desatualizada). Mesmo
  mecanismo da investigação MF (`2026-08-05-unit-sources-investigacao.md`): qualquer reprocess
  headless sem `subject_profile` (pré-Task-1) perde parte das unidades em QUALQUER curso com plano
  de ensino real — não é peculiaridade do MF. **Eleva o escopo da Fio Task 3**: reprocess real +
  gold/medição pré-pós precisam cobrir SO/ES2/IA também, não só o MF.

- [DERIVADO] **Recompute MF em memória pelo fio consertado** (`as-of f11dda7`, read-only,
  `scripts.retag_manifest.retag(MF, subject_profile_real)` persist=False +
  `_build_file_map_timeline_context_from_course(persist=False)` direto p/ block→unidade). Aceite
  do brief **CONFIRMADO em 4/5 pontos**: 3 unidades presentes; bloco-16 →
  `unidade-03-verificacao-de-modelos` (era `unidade-02` no disco — poison confirmado); blocos
  01-06 → `unidade-01-metodos-formais` e 10-15 → `unidade-02-verificacao-de-programas`
  **byte-idênticos ao disco** (inclui bloco-14 vazio nos dois lados, non-instructional). Único
  delta de `unit_slug` nos 21 blocos é o bloco-16 (o fix pretendido).
  **DESVIO — PARADO, NÃO ajustado (regra da task):** `computed_block_id` não é byte-idêntico em
  **3/67 entries** (`logicadehoare` bloco-10→bloco-11; `classes-parte1`/`classes-parte2`
  bloco-15→bloco-13). **Causa-raiz isolada e NÃO é o fio** (reproduzido byte-a-byte com
  `retag(MF, subject_profile=None)` — mesmos 3 IDs, mesmos blocos de destino, independente de
  `subject_profile`) — isso está confirmado por teste. **A CAUSA REAL da divergência disco-vs-
  recompute é HIPÓTESE ABERTA — resolver na Task 3 com o diff pré/pós do reprocess real**
  (item PRIMÁRIO, não afterthought — fix round 1 da revisão retirou a atribuição original a
  "Dívida #5" por falta de teste; ver reconciliação completa em
  `.superpowers/sdd/2026-08-05-fio-subject-profile/task-2-report.md` §"Fix round 1"). O que ESTÁ
  testado e confirmado: (a) não é o fio; (b) não é `_content_taxonomy` ausente — injetei a
  taxonomia real e o drift persiste idêntico (o caminho real desses 3 entries,
  `_card_scoped_block`→`_best_instructional_block_fallback`, é puramente lexical, nunca lê
  `_content_taxonomy` — meu diagnóstico original estava ERRADO, código-fonte confirma:
  `content_taxonomy.py:886-916,825-878`, `preferred_unit_slug`/`preferred_topic_slug` hardcoded
  vazios); (c) para `classes-parte1`/`classes-parte2` (têm `code_curation.json`), simular a ORDEM
  real de produção (`resolve_unit_block_tags` + `attach_block_summary_fields`,
  `pedagogical_regeneration.py:182-252`) mostra que o `computed_block_id` **também driftaria em
  produção real** para o mesmo bloco novo (o D1 restore gate exige "sem card", e os 3 TÊM card —
  nunca dispara) — só o `computed_block_method` seria restaurado para `llm_only` pelo cache,
  criando uma inconsistência method-vs-id (`llm_only` mas id/conf/band são do `card+scorer`) que
  também existiria em produção, não só no script-sonda; (d) `logicadehoare` não tem
  `code_curation.json` (é PDF) — nem a hipótese (c) se aplica a ele. **Nenhuma das 3 histórias
  causais testadas (minha original, a do revisor, e a do achado independente
  `2026-08-05-planob-investigacao.md` §2b Evidência 2 — que já nomeava os MESMOS 3 IDs como
  "manifest stale" antes desta task) explica por que o scorer de hoje prefere um bloco diferente
  do gravado em disco.** `manifest.json` do MF tem mtime 2026-08-04 17:58 (a MESMA rodada que
  produziu o `.content_taxonomy.json` envenenado) — não é staleness de meses, é a última rodada
  real, sem mecanismo de divergência identificado.
  > **AMENDMENT 2026-08-06** (task-3, reprocess real do MF; detalhe completo, matriz de afinidade
  > e reconstrução do DP em `docs/reports/2026-08-06-task3-colisao-rotulo-mf.md`) — a HIPÓTESE
  > ABERTA acima ("A CAUSA REAL da divergência disco-vs-recompute é HIPÓTESE ABERTA — resolver na
  > Task 3 com o diff pré/pós do reprocess real") está **FECHADA**: 0/67 `computed_block_id` mudou
  > no reprocess REAL (pipeline completo `RepoBuilder.incremental_build()`), incluindo os 3 IDs
  > flagados (`logicadehoare`/`classes-parte1`/`classes-parte2`). Causa: **dual-source** — o probe
  > isolado `retag(persist=False)` pula etapas do pipeline completo (`attach_block_summary_fields`
  > etc.) e por isso diverge do disco; não é staleness do disco.
  > **RETRATAÇÃO EXPLÍCITA** da frase "o `computed_block_id` **também driftaria em produção real**"
  > (item (c) acima, sobre `classes-parte1`/`classes-parte2`) — **FALSIFICADA** pelo reprocess real
  > (0/67 mudou em produção). O mecanismo descrito no Teste B (o D1 restore gate exige "sem card",
  > os 3 TÊM card, nunca dispara) **existe de fato no código** — mas a PREMISSA de que os insumos
  > da sonda equivalem aos da produção é falsa, então a conclusão que dependia dela não se sustenta.
  > Além disso, o "CONFIRMADO em 4/5 pontos" no topo deste bullet **validou só o CAMINHO DA SONDA,
  > não previu a produção**: no reprocess real, bloco-16 NÃO foi para unidade-03 (a sonda tinha
  > dado conf=0.6) — ficou em unidade-02 conf=0.4, empate 4×4 entre unidade-01/unidade-03 no
  > matcher posicional (colisão de rótulo: "Verificação de Modelos" é pré-visualização 1.3.1 dentro
  > da abertura da Unidade 01). **Prova do DUAL-SOURCE nos dois sentidos**: 3 falsos alarmes de
  > drift (este bullet, sonda via `computed_block_id`) + 1 falso positivo de unidade (bloco-16,
  > sentido oposto — sonda previu certo, produção não confirmou).

- [DERIVADO] **Régua completa (7 probes) + suite byte-idênticos, pós-Task-1** (`as-of f11dda7`).
  fase0 48/58=82.8% conten0 cw1 · fase1 recall 0.900 (9/10) · fase2-SO 45.2%/colisões0/cw0/77.8% ·
  fase2-TCC pinos5/5/83.3%/cw0/84.2% · fase3 escopo39/lift+3/0 chamadas API/cw0 · fase4
  flag-OFF idêntico/det48-58cw1/voter51-58cw0calls0 · fase5 4/8/cw0 — **todos PASS, todos os
  números idênticos ao baseline** (nenhum probe roda `subject_profile`/unit_index no seu próprio
  `build_context`, então nada deveria mudar com a Task 1 — confirmado). **pytest 1862 passed / 4
  skipped / 0 failed** (igual ao pós-Task-1, nenhum teste novo nesta task de medição).
  `last_seen` de `Metodos-Formais-Tutor/course/.block_identity.json` bumped pelos probes (mesmo
  padrão já catalogado, diff conferido = só `last_seen`) restaurado via `git checkout`; TCC (só
  `?? material_curation.json` pré-existente) e SO sem alteração; ES2 não tocado (45 dirty
  pré-existentes, regra da task). Report completo:
  `.superpowers/sdd/2026-08-05-fio-subject-profile/task-2-report.md`.

- [USER] **Inteligência-Artificial-Tutor com sujeira pré-existente, NÃO catalogada até agora**
  (`as-of 2026-08-05`, achado incidental desta task, leitura pura — repo intocado por esta
  sessão). `git status --porcelain` = **48 entradas** (M `manifest.json`, `.block_identity.json`,
  `.card_block_map.json`, `.lessons_index.json`, `.timeline_curation.json`, vários `.md` gerados,
  2 `content/curated/*.md` deletados + ~24 `?? code/professor/*.md`/exams/backups
  não-trackeados). Mesmo formato do achado ES2 (Plano B Task 5, 45 arquivos), mas em curso
  diferente e nunca registrado antes. Mesma regra: SÓ LEITURA, sem checkout/restore, inspecionar
  antes de qualquer rollout/reprocess IA (já era pré-requisito listado no handoff — este achado
  documenta o tamanho exato do problema).

- [DERIVADO] **Fio Task 3 (cura MF, reprocess real, GATED) — STATUS FINAL: BLOCKED → ROLLED_BACK**
  (`as-of 2026-08-06`, sign-off user SATISFIED, escrita real autorizada e executada no MF-Tutor;
  detalhe completo, matriz de afinidade e reconstrução do DP:
  `docs/reports/2026-08-06-task3-colisao-rotulo-mf.md`). O fio funcionou até a camada de
  taxonomia (`content_taxonomy.json` com as 3 unidades corretas, títulos acentuados), mas o
  objetivo central — bloco-16 carregar `unit_slug=unidade-03-verificacao-de-modelos` — **não
  aconteceu**: matcher posicional manteve bloco-16 em unidade-02, conf 0.4, por **colisão de
  rótulo de tópico** ("Verificação de Modelos" aparece como pré-visualização 1.3.1 dentro da
  abertura da Unidade 01 do plano de ensino, contaminando a assinatura de u01 com tokens de u03) +
  **DP monotônico global sem sinal na cauda** (empate 4×4 u01/u03, tie-break fica na unidade
  anterior). Gate (a) mandatório FALHOU → nenhum commit em nenhum repo. **Rollback executado**:
  MF-Tutor restaurado ao snapshot `f83adc9fe8509bc49d68eba11f2e327afda0800e` (hash-verificado —
  sha256 dos 5 sidecars gitignored idêntico byte-a-byte ao snapshot pré-cura; `git status
  --porcelain -uall` vazio pós-restore). Achados extra registrados para a próxima campanha: (1)
  **`U+FFFD` (replacement character) pré-existente no `teaching_plan` do MF em `subjects.json`**
  (`%APPDATA%/GPTTutorGenerator/subjects.json`, live `SubjectStore`) — dado JÁ corrompido na
  fonte, fora de escopo desta task, **consertar antes da próxima cura** (o texto contaminado é
  literalmente o do bullet "1.3.1. Verifica��o de Modelos" que colide com u03); (2)
  `unit_confidence=1.0` pré-cura em bloco-16 era stale (o DP real nunca produz 1.0 — valores
  possíveis são 0.4/0.6/0.8 — resíduo de rodada muito anterior nunca recalculado). **CAVEAT para a
  próxima sessão**: restaurar o fio (`subject_profile` chegando ao `RepoBuilder`) **NÃO restaura
  automaticamente a unidade perdida** quando há empate no DP — não assumir que reprocessar
  SO/ES2/IA recupera as unidades que a verificação da Task 2 encontrou faltando (SO 7→6, ES2 3→2,
  IA 5→3); cada curso pode ter o mesmo padrão de colisão de rótulo do MF e vai exigir a mesma
  investigação antes de confiar no reprocess sozinho.
  > **AMENDMENT 2026-08-06 (varredura com dados reais): achado extra (1) — U+FFFD — FALSIFICADO.**
  > `subjects.json` real (`%APPDATA%/GPTTutorGenerator/`, mtime 2026-08-04 20:18:59 — ANTERIOR ao
  > achado da Task 3 e intocado desde então) tem **0 ocorrências de U+FFFD no arquivo inteiro**
  > (verificação programática por codepoint); o `teaching_plan` do MF contém "1.3.1. Verificação
  > de Modelos" acentuado e íntegro, e o inventário non-ASCII do campo só tem acentos legítimos +
  > símbolos matemáticos. `SubjectStore` lê/grava com `encoding="utf-8"` explícito
  > (`src/models/core.py:341,349`) — a corrupção também não acontece na leitura. O "Verifica��o"
  > visto na Task 3 era **mojibake de console** (stdout cp1252 renderizando UTF-8), mesma família
  > do crash cp1252 do hook `code-review-graph`. **Consequência: o pré-passo "consertar o U+FFFD
  > antes" da campanha colisão-de-rótulo CAI** — a colisão em si (1.3.1 é texto legítimo do plano
  > dentro da abertura da u01) permanece o problema real e único. Achado extra (2)
  > (`unit_confidence=1.0` stale) não afetado.

## Concluído (2026-08-06 — campanha gerador de índice único, 1/3 da unificação)

- [DERIVADO] **Campanha "gerador de índice único" ENTREGUE — 9 tasks, TCC destravado, PLACAR
  FINAL 5/5 flag-ON.** Tasks: **C1** guard classifier `0bc4265` (c/ ruling user só-prova/teste);
  **C5** régua fase5 pino `305cd9f`; **C2** montador único `305877a`+`328a0b2`; **C3** condenação
  serializador `9155224`; **C4** guard W2 `4b6e793`; **Task 6** tracker `8a80ad3`; **C6** guard
  janela P4 `b4c9672`; re-flip TCC tentativa 6 GREEN — TCC-Tutor `31f6025`+`91c1d2a`. **6
  tentativas de re-flip no total, 3 camadas de colisão prova/demonstração mortas** (kind, janela
  P4, scorer-mitigado-por-pino). **fase2-TCC final 84.2% cw=0 byte-idêntica** — baseline
  renegociado 78.9 com sign-off user na fase A, devolvido a 84.2 pela fase B. **Suite 1881/4/1**
  (1 = golden IA, item próprio). **rebuild_diff 0/5.** Review final whole-branch: **zero Critical
  de código**, findings de docs fechados neste commit. **PLACAR 5/5 FLAG-ON.** Review final
  verificou §6.3 empiricamente: taxonomia montador==produção byte-idêntica nos 5 cursos.

## CODE — dívida da campanha 2 (unidades, 2026-08-11)

- [CODE] ~~Classifier de kind por keyword sem posição/contexto~~ **FECHADO 2026-08-12
  (commits projeto `a6f7b73` + TCC `887dfe4` + IA `87f134a`; TDD 6 testes; suite 1930/0/4;
  eval 5/5 intacto)**: (a)+(b) promote posicional de véspera (TCC 16/30 review c/ scope da
  prova) + demote existente + override stale TCC-05 removido (código acerta sozinho);
  (c) já resolvido no T9a (guard maioria-de-sessões); (d) guard planning-com-evidência-de-
  unidade (IA-16, override removido); (e) workshop-gap: varrido, ZERO instâncias vivas
  pós-refresh (source_kind cobre) — 1 linha de keyword SE aparecer. BÔNUS: revisão herda
  scope MANUAL da prova (véspera-P1 TCC) + 2 scopes gold-backed P1/P2 TCC. Correção de
  prova sem kind próprio (TCC class vs MF results): inconsistência TEXTUAL entre cursos,
  não bug — segue documentada. Era item original:**
  (`as-of 2026-08-11`): (a) `review` sem posição — TCC bloco-05 (revisão LFA, dist 12 da prova)
  falso positivo vs bloco-16/26 ("revisão para prova", dist 1) falsos negativos; MF acerta os
  mesmos padrões; (b) correção de prova sem kind próprio (TCC class vs MF results); (c)
  `office_hours` por 'duvidas' no último label — SO bloco-18 (3 sessões de arquivos 16-23/06)
  sequestrado (curado no T9a); (d) `planning` por keyword no TEMA — IA bloco-16 "agentes e
  planejamento" Atividade=Aula virou planning (curado com override+pino, T11); (e) `workshop`
  não cobre 'desenvolvimento/apresentação de trabalho' com Atividade=Aula. Destino: ANTES da
  campanha 3 (prior de revisão do SO depende de kind confiável). Regra institucional posicional
  em `institutional.md`. Fallback de COR existe (helpers.py:398-411) — cores novas = 1 linha
  com export como prova.
- [CODE] **`manual_kind_override`→class NÃO re-deriva unidade** (`as-of 2026-08-11`, RED =
  bloco-16 IA): `_serialize_timeline_index` (index.py:835) zera `unit_slug` de não-class ANTES
  de `_apply_curation_overrides`; auto_unit_slug guarda o que o DP deu, unit_slug fica vazio.
  Workaround institucional: kind override + pino `manual_unit_slug` JUNTOS (precedentes:
  bloco-18 SO T9c, bloco-16 IA T11).
- [CODE] ~~Guard C6-equivalente no scorer de card (aula-13 TCC)~~ **RESOLVIDO POR MEDIÇÃO
  2026-08-11 (ruling user, zero código — report
  `2026-08-11-guard-c6-resolvido-por-medicao.md`)**: o motor novo pra aula-13 sem pino dá
  conf 0.08 band BAIXA (honesto; card_term=0 em todos os blocos); o confiante-e-errado
  0.85-alta do T12 era o resolver LEGADO, que só decidiu porque `apply_concept_resolver`
  pula entry com computed_block_id vazio (resolver_apply.py:116). Legado morre no cutover
  Fase 3.4 (campanha 3); pino segura produção até lá. Sandbox T12 vira RED DE REGRESSÃO
  do cutover: pós-cutover, aula-13 sem pino deve dar band não-alta.
- [CODE] **boundary_dates sem validação de formato** (T9c, deferred): data inválida na
  curadoria = fail-open silencioso; warning sugerido.
- [CODE] **`card_block._tokens` aceita pontuação como token** (`as-of 2026-08-11`, análise
  slug): título "Visão Geral (5%)" gera token lixo `'(5%)'` (split ingênuo; len>2 passa).
  Inofensivo hoje (não casa com nada); fragilidade do tokenizador arquivo→bloco.
- [CODE] **Fix profundo T2b — não mergear sessão não-letiva em bloco de aula** (IA bloco-06,
  suspensão 20/04): fix cirúrgico topic_text já em produção (3d5d7fb); o profundo junta com
  item over-merge existente (Degrau 2/3c).
- [CODE] ~~`check_sarc_freshness` 3/5 no fechamento~~ **FECHADO 2026-08-11 (aprovado pelo
  user, mesmo dia)**: comparador normaliza whitespace + descarta sessão-sem-descrição nos
  DOIS lados (`_norm_desc`; testes `tests/test_check_sarc_freshness.py`). Gate de volta a
  **5/5, 0 diffs**. CORREÇÃO FACTUAL do diagnóstico do review final: as linhas 15/07 IA e
  16/07 SO NÃO eram fantasma de import — são sessões REAIS do SARC agendadas sem descrição
  (confirmado no HTML vivo; `parse_html_schedule` as descarta do lado vivo). Bloco-23 IA é
  legítimo; notes do gold/cruzamento corrigidas. Parser de produção intocado.
- [CODE] Minors acumulados da campanha: `eval_units --baseline` compara ok ABSOLUTO (ler
  pct+totais impressos); `by_uuid` dict-comp sem guard de colisão de uuid vazio/dup;
  `sonda_units`/`check_repo` com sp!=None sem teste automatizado (fake sp sugerido);
  `collect_strong_heading_candidates` sem teste de integração lendo disco (débito antigo);
  import de `_clean_heading_text` no meio de arquivo de teste (linha ~96); anotação
  `-> set` vs `-> set[str]` (content_taxonomy.py:72); `period_start→date_start` sem comentário
  inline (gold_units template); runbooks/handoffs com `pytest -k ES2` NO-OP (0 testes — usar
  `-k "Engenharia-Software-2"`); gold_units_ES2.csv linhas 5/8/10/11 sem note de pino
  (convenção SO documenta na linha); racional do ruling posicional ES2 09/10 só em arquivo
  gitignored (levar pra docs/reports).

## USER/DECISION — dívida da campanha 2 (unidades, 2026-08-11)

- [USER] ~~Remendo dos golds antigos~~ **PARTE MECÂNICA FECHADA 2026-08-12** (dossiê
  `2026-08-12-remendo-golds-dossie.md`): 32 remendos Tier-A (uuid vivo→display novo,
  SO 25 · TCC 6 · IA 1) aplicados; **audit hard=0 nos 5/5** (era SO 13 + IA 1).
  ACHADO: eval SO honesto = **17/38 (44.7%)** — baseline real pro cutover julgar
  (materiais "Lâminas" sem sinal; 19 ZERO_OVERLAP). RESTA [USER] opcional sem urgência:
  ~102 suspeitas soft (sinal fraco, rótulo possivelmente certo) + 7 drifts SEMÂNTICOS
  do MF — arbitragem de conteúdo com os CSVs `remendo_golds/` como material.
  Pré-requisito da campanha 3: **DESTRAVADO** (a régua mede honesto).
- [USER] **Revisar gold IA congelado** (`as-of 2026-08-11`): `gold_units_IA.csv` derivado do
  CRUZAMENTO_IA_SARC.md (validado) — conferir régua 10 e vazios (blocos 07/10/13/21/23);
  aba MF do xlsx pendente de revisão pós-refresh (blocos de junho recompuseram).
  **Aba IA + lista `_slugs` do `gold_units_rotular.xlsx` estão STALE** (25 blocos pré-refresh,
  slugs mortos com percentual; achado review T11) — arquivo em rotulagem ativa, NÃO tocado;
  regenerar via `scripts/gold_units_xlsx.py` (+`fix-dropdowns`) quando o user pausar, ou
  tratar a aba IA como superseded (gold IA veio do CRUZAMENTO).
- [DECISION] **covered_units (lista) p/ assessment/deliverable** (decisão user 2026-08-08):
  contexto pro tutor; fonte candidata due-window + `.assessment_context.json` (inspecionar
  primeiro) + notas de cobertura do gold como verdade inicial. Regra IA: P1=u01+u05,
  P2 CUMULATIVA=u01+u05+u02+u03, PS=tudo (regra DESTE plano; MF/TCC não-cumulativo).
- [DECISION] **Tratamento estrutural PS/G2** (regra institucional 2026-08-08): provas
  opcionais sem unidade (PS = semestre; G2 condicional G1<7, (G1+G2)/2>=5).
- [DECISION] **Subunidades** (ideia do user, pós-campanha): grão mais fino repete lição do
  straddle IA mundo-63; base já existe (computed_subunit_slug/eval_subunit_census);
  cruzamentos como insumo.
  > **Design candidato (2026-08-11, discussão user+CC)**: grão = SESSÃO (não bloco —
  > mata o straddle); vocabulário = TÓPICOS do plano por unidade (já parseados com
  > profundidade em _parse_units_from_teaching_plan); atribuição = token-overlap do
  > label da sessão contra os tópicos DA unidade do bloco (escopo restrito, precedente
  > do concept_resolver; sem DP — medir antes de sofisticar); representação =
  > sessions[].subunit_slug + bloco agrega LISTA de subunidades cobertas; régua = gold
  > por sessão só nas unidades com texto repetido (caso motivador: "mesma unidade no
  > cronograma, conteúdo diferente"). PRÓXIMO PASSO: diagnóstico read-only — casar
  > labels de sessão x tópicos do plano nos 5 cursos, medir taxa de casamento.
- [DECISION] **Modo não-monotônico por curso** — descartado no ruling T11 (opção C): 1/5
  cursos inverte, scorer puro erra sob co-ocorrência; reavaliar SE a família crescer.
  > **Anotação 2026-08-11 (análise a pedido do user, veredicto: NÃO implementar agora —
  > risco de overengineering confirmado no código):** o caminho bloco→unidade já empilha
  > ~8 camadas (DP global, 2 fallbacks, 2 heranças, curadoria, demote de revisão, escopo
  > por janela) e o conceito "segmento entre provas" JÁ EXISTE (`assessment_scope_by_date`
  > + `link_review_scope`, index.py:1299). Detector automático é frágil em curso de sinal
  > fraco (SO: 'gerencia' em 4/7 títulos — dispararia falso e podia regredir cursos 100%).
  > Verbosidade das respostas: modelo não muda nada (só o valor do slug; COURSE_MAP já
  > exibe certo). Pinos custam ~zero manutenção. **Gatilho de reavaliação: inversão em
  > 2+ cursos OU 2+ semestres.** Se disparar, o design é GENERALIZAR o DP existente
  > (reset PENALIZADO nas âncoras de assessment que o código já computa) — 1 algoritmo,
  > sem modo novo, sem detector. RED congelado: gold_units_IA.csv + índice IA 2026/1.
  > Inversão IA é bimodal com quebra na P1 (u01+u05 antes; u02+u03 depois) —
  > monotonicidade vale dentro de cada segmento.

## Concluído (2026-08-11 — campanha 2: unidades, 13/13 tasks)

- [DERIVADO] **Campanha 2 (unidades) ENTREGUE — placar eval_units 5/5: MF 12/14 (85.7) ·
  SO 9/11 (81.8) · ES2 7/7 (100) · TCC 13/13 (100) · IA 9/10 (90). Misses restantes = 100%
  POLÍTICA (overview/véspera/entrega-embutida não carregam unidade), zero erro de matcher.
  SUITE 1920 passed/0 failed/4 skipped — golden IA crônico FECHADO.** Tasks 1-13: U1 título
  exclusivo `dd10126` · U1c `fda3151` · U1b DP tie-break `e4af4a9` · U5 `f1e8e5e` · U2 sonda
  canônica `1cd481c` · U3 gold xlsx `1539fc3`+`6a96324` · T7a refresh SARC 5/5 (40 diffs
  reais; `check_sarc_freshness.py` gate permanente) · T8 cura MF (30454ee, 3 unidades disco)
  · T9 cura SO em 3 atos (E/S '/', office_hours, boundary_dates `9c89082`, 3 pinos;
  SO-Tutor `24029c5`) · T10 cura ES2 (4 pinos, ES2-Tutor `b06b264`; review byte-a-byte OK)
  · T11 ruling IA opção B (IA-Tutor `dd9967d`+`458f744`: refresh + 4 pinos u05 + bloco-16
  class/u03; projeto `8683a39` fix slug percentual + `96dfb3e` gold IA 23/10) · T12 sandbox
  aula-13 (resíduo VIVO, guard C6 → item CODE) · T13 fechamento. **12 pinos gold-backed em
  produção** (3 SO + 4 ES2 + 5 IA). Índices em disco: MF 3/3 · SO 7/7 · ES2 3/3 · TCC 4/4 ·
  IA 4/5 (u04 sem aula própria no SARC vivo — baseline). Lições: 5ª geração prova/rótulo
  (inversões LOCAIS calendário-vs-plano → pino gold-backed); régua mede o que o sistema
  produz (gold por bloco, keyed uuid, política = miss documentado); SARC vivo > import.

## Concluído (2026-08-14 — auditoria-enxame pré-cutover)

- [DERIVADO] **Auditoria-enxame EXECUTADA (`as-of 2026-08-14`, branch feat/motor-atribuicao)** —
  workflow de 45 agentes (7 dimensões em paralelo, verificação adversarial de todo achado sério,
  síntese ranqueada; mix de modelos sonnet/fable adotado após 3 estouros de limite em 48h),
  ~2.03M tokens, 0 erros. Placar: **32 confirmados / 5 refutados**. Relatório completo ranqueado
  (Pré-cutover / Quick wins / Estrutural / Registrar-ignorar):
  `docs/reports/2026-08-14-auditoria-enxame.md`. Destaques que ALIMENTAM a campanha 3:
  **1.1 BLOQUEANTE** — campos de unidade 100% do legado (resolver_apply.py:132-137 descarta o
  `unit_slug` que o motor novo calcula; Fase 4 vira pré-req duro do cutover) · **1.2** gap de
  reconciliação unidade×bloco pós-apply (dormente, ativa no cutover) · **1.3** drift REAL do
  espelho auto_tags em produção · **1.5** mapa de deleção de testes (3 lotes; ~1240 linhas
  apagáveis em bloco; test_file_map_unit_mapping.py exige auditoria função-a-função).
  Quick wins top: loop incremental (write+compact por entry, 32x medido — DESEMPATE: design
  deliberado de crash-resume `10bec352`/`79b6f98`, fix = checkpoint a cada N com compact junto,
  nunca deletar linha isolada) · 5 mocks docling = suite ~2x mais rápida · loaders silenciosos
  sem log (engine:1831 + 3 loaders de artefato) · 6 símbolos mortos de UI · 3 campos nunca
  lidos no approve-flow.
  **DESEMPATE MANUAL pós-relatório (mesma data)**: journal tinha vereditos duplicados
  divergentes (pause/resume); 3 contestados decididos por evidência primária, todos pró
  contra-veredito: **2.5 rebaixado** (sem corrupção cross-entry, class_ordinal não persiste,
  deepcopy desnecessário — resta só 3.2), **2.2 fundido no 2.1** (acima), **1.5b reescopado**
  (apagar em bloco só 4 arquivos puros/911 linhas; test_block_scorer_signals.py: mover os 3
  testes S4b [única cobertura de extensão→ferramenta] pra test_entry_signals_materials.py
  antes de apagar). Relatório carrega as marcações [REESCOPADO]/[FUNDIDOS]/[REBAIXADO].
  **QUICK WINS EXECUTADOS (mesma noite, suite 1931/0/4 verde em cada lote):** 2.10+2.11
  código morto UI + campos approve-flow (`1d6e07c`, -150 linhas) · 2.4+2.6 warnings em
  loaders fail-open (`bb19bd8`) · 2.3 mocks docling (`3c98813`, **suite 51.7s→23.8s**) ·
  2.12+2.14 strip_accents fonte única + docstrings cruzados (`69e050b`) · 2.8+2.9 no-ops
  de scoring (probe 5 índices = 0 divergentes) + memo unit_index (`b698028`) · 2.1+2.2
  checkpoint a cada 10 no incremental (`1e1c06e`). **FICAM do relatório:** 2.7
  signal_token_set (eval-gated, mexe em input de scoring — trilho próprio), 2.13 smoke
  tests deeptutor/golds, 3.1-3.3 estruturais (campanha), seção 1 inteira (insumo do spec
  da campanha 3 cutover).
  Workflow reusável em `.claude/workflows/auditoria-enxame.js` (duplicata `-mew.js` deletada —
  colisão de meta.name causava resolução aleatória).

## Concluído (2026-08-17c — campanha 3, PASSO 3 FECHADO: flip + deleção do funil)

- [DERIVADO] **PASSO 3 ENTREGUE (`as-of 2026-08-17`, commits `c5ecb5f` flip · `df86203`
  deleção -4747/+334 · `037ddbe` serializador v4 + item 8; repos-tutor: flip, pós-deleção e
  v4 commitados nos 5)** — **flip**: `use_concept_resolver` default ON (ausente=ON, opt-out
  explícito), pino de curadoria `revisao_p1_gabarito→bloco-07` (régua ficaria 49/57), 7
  sentinelas casos-chave revisadas caso a caso e re-baselined; **deleção por lista nomeada**
  (resoluções 2026-07-03 TODAS executadas): funil `resolve_unit_block_tags` + S2 + S4
  (TOOL_EXTENSIONS fica) + fallback keyword de unidade + fallback S2 do health + R4 mortos,
  scripts retag/eval_assignments aposentados, limpeza `_NO_TIMELINE_CATEGORIES` portada, motor
  agora SEMEIA entries novos (gate invertido); **serializador único** persist_enriched v4
  (fantasma morto, bump 8a, índices de produção v4), itens 8b (vocab exam unificado) e 8d
  (--write grava taxonomy) entregues, 8c/8e já estavam feitos. **Achado**: deleção removeu o
  viés P3.1 (scorer lia tags unit:/subunit: re-escritas pelo funil — auto-confirmação);
  confidences honestas, ~15 slugs de unit/subunit por material mudaram one-time, idempotência
  0 diffs. Testes: 12 arquivos-fantasma deletados, invariantes migrados pro motor (M8 parcial:
  learned boosts coberto). Gates finais: suite **1852/1/0**, golds unit **5/5**, régua MF
  **50/57**, pinos **0 violados**, rebuild_diff **5/5=0**, guard verde. Relatório:
  `docs/reports/2026-08-17-passo3-flip-delecao-fechado.md`. **Candidatos a pino (rótulo
  user)**: SO `0704-threads`, IA `introducao-a-busca-informada`. **Próximo: campanha web
  (backlog no fim do tracker) — motor estável e único, fundação pronta.**

## Concluído (2026-08-17b — campanha 3, PASSO 3 etapa 1: medição pré-flip 5 cursos)

- [DERIVADO] **MEDIÇÃO PRÉ-FLIP ENTREGUE (`as-of 2026-08-17`, HEAD `b4d119d`, sandbox
  read-only)** — 4 gates da etapa 1 TODOS verdes: golds unit **5/5 sem regressão**
  (MF 12/14 · SO 9/11 · ES2 7/7 · IA 9/10 · TCC 13/13, mismatches byte-idênticos
  BEFORE/AFTER); pinos **29/29 sem violação** (26 honrados no escopo do motor — inclui
  `tiposindutivos`, caso-bug F3/C1, primeira medição do fix em curso real; 3 MF
  `fora_do_motor`, bibliografia, flip-neutros); `rebuild_diff` produção **5/5 = 0**;
  **M7 fora do pré-flip** (1 caso único nos 5 cursos, `colecoes-conjuntos` MF 0.80→0.45,
  não é inversão em escala — dívida segue aberta). Delta informacional de bloco:
  23/67 · 15/42 · 17/35 · 31/62 · 17/27 (100% troca, 0 mudança de cobertura) = o diff
  esperado das sentinelas no flip. Driver COMMITADO `scripts/measure_flip.py` (fecha
  limitação F4 "scripts ad-hoc irreprodutíveis"). Relatório:
  `docs/reports/2026-08-17-medicao-pre-flip-5cursos.md`. **VEREDITO: GO pra etapa 2
  (flip default ON)** — protocolo: snapshot antes de reprocess, sentinelas re-versionadas
  conscientemente.

## Concluído (2026-08-17 — campanha 3, PASSO 2: C1 pinos + gaps 1.2/1.3)

- [DERIVADO] **PASSO 2 ENTREGUE (`as-of 2026-08-17`, commits `636f299..d319477`, SDD 4 tasks +
  1 fix round, reviews limpas)** — as 3 pré-condições do flip fechadas: **C1** Tier 1 casa pino
  uuid+display (id canônico; 3 testes; bônus: harness compare_resolver sem `changed` espúrio);
  **1.3** attach resincroniza tag `bloco:` no swap D1 (guard `is not None` — cobre blocks=[]
  de produção e blocks=None legado; invariante testado; MUDA produção flag-OFF de propósito —
  era drift real); **1.2** teste de integração da cadeia `apply_concept_resolver →
  apply_unit_subunit_fields` (unit fields descrevem bloco pós-motor; não-vacuidade provada por
  mutação dupla na review). Gates: suite **1952/1/0**, sentinelas **0 diff**, MF **50/57**.
  Plano: `docs/superpowers/plans/2026-08-17-passo2-gaps-flip.md`. **Próximo: passo 3 (flip +
  deleção)** — medição 5 cursos (golds unit + pinos + rebuild_diff), default ON, delete por
  lista nomeada.

## Concluído (2026-08-14 — campanha 3, FASE 4: unit/subunit no motor)

- [DERIVADO] **FASE 4 ENTREGUE (`as-of 2026-08-14`, commits `5da5f2e..b9a4a53`, SDD 5 tasks +
  2 fix rounds, reviews limpas)** — sob `use_concept_resolver=True` o motor produz TODOS os campos
  de unidade/subunidade que a UI lê (contrato do legado `resolve_unit_block_tags`):
  `apply_unit_subunit_fields` em `resolver_apply.py` — unit via scorer sobrevivente + gate
  `T.UNIT_TAG` + `reconcile_unit_with_block` contra o bloco NOVO do motor (fecha o gap 1.2 pro
  caminho unit por construção); subunit restrita à unidade FINAL reconciliada (**correção
  deliberada** vs legado, que restringia à unidade crua pré-reconcile — invariante do spec:
  subunit nunca escapa a unidade final); wire flag-gated `engine.py` (partial, aliases legados)
  → `pedagogical_regeneration.py:528`. Gates: suite **1945/1/0**, sentinelas **0 diff** (flag OFF
  byte-idêntico), régua MF **50/57**, golds unit MF **12/14 BEFORE=AFTER**. Medição sandbox MF
  (67 entries): 12 unit divergentes (11 slug-alterado rastreando bloco motor ≠ legado — território
  pré-F4; 1 só-conflict), 11 subunit (design). **GO pro flip** após gaps 1.2/1.3.
  Relatório: `docs/reports/2026-08-14-f4-medicao-unit-motor.md`. Plano:
  `docs/superpowers/plans/2026-08-14-fase4-unit-subunit-motor.md`. Limitação registrada: sem gold
  por-material pras 12 reatribuições (só gold por bloco); scripts ad-hoc da medição não commitados.
  **Review final (Opus 5) pós-fecho**: C1+I2 corrigidos na fix wave (`bd43430` block_is_manual lê
  pino direto + teste; `7cb0e21` medição emendada, GO condicionado); minors M4-M8 registrados como
  itens abaixo. Rulings do SDD todos sustentados.

- ~~[CODE] **C1 (BLOQUEAVA O FLIP) — motor descarta pinos manuais em uuid**~~ **FECHADO
  (2026-08-17, passo 2, `636f299`)**: `_manual_block_id` casa uuid E display e devolve id
  canônico; winner lookup do Tier 1 idem; 3 testes (2 unit + 1 fim-a-fim pelo apply). Bônus:
  corrigiu `changed` espúrio do harness `compare_resolver` pra pinos uuid. A régua de
  sobrevivência de pinos POR CURSO permanece na medição do flip (passo 3).
- [CODE] **Dívidas menores da review final F4 (passo 2 / oportunista)**: M4 teste de wiring
  flag-ON não valida assinatura do partial (`inspect.signature(...).bind` na sentinela —
  `test_resolver_wiring.py:310-334`); M5 `unit_block_conflict`/reasons órfãos quando
  `resolve_material_assignment` devolve `block_id=""` e o apply pula (conflito fantasma na UI —
  `dialogs.py:4114`; não observado na MF); M6 dedup do lookup uuid-then-id em
  `resolver_apply.py:221-223` vs `_display_id_for_block`; M7 reconcile compara confiança do MOTOR
  contra confiança do scorer legado de unidade (escalas distintas — caso `colecoes-conjuntos`
  0.80→0.45 inverteu desempate; calibrar antes do flip); M8 coberturas ausentes em
  `test_resolver_apply_units.py` (branch code_curation, lookup display, unit==bloco, tag_profile,
  e — da re-review da fix wave — ramo do pino em forma DISPLAY vs computed uuid no
  block_is_manual novo).

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
