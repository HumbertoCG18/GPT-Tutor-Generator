# Handoff 2026-09-05b — PONTO DE ENTRADA: a FILA de campanhas (C1 aberta e BLOQUEADA em LLM; C3 proxima; decisoes do user na frente)

Unico handoff vivo. Substitui `_archive/2026-09-05-handoff-fila-campanhas.md` (sessao 6, 05/09 tarde). **Leia nesta ordem:** (1) este arquivo;
(2) `pendencias.md` §CURADORIA DE UNIDADE DO CG, §GOLD DE SUBUNIDADE CG E MF, §OS 32 ERROS, §C1 ITEM 3 (numeros); (3) `.mex/context/decisions.md`
(entradas de 05/09). Rode `mem-search` para a sessao de 05/09 tarde (sessao 6).

**Regra de fila (user, 03/09):** UMA campanha aberta, UMA proxima, o resto ESTACIONADO. Campanha so fecha com 100% dos itens; item nao feito
ou e feito, ou o user o RETIRA por decisao registrada. Novo lote = novo handoff, o anterior vai para `_archive/`. Ideia no meio vai para a CAIXA.

**GEMINI: BLOQUEADO ate o user mandar.** `gemini_auto_summarize` foi DESLIGADO na UI pelo user em 05/09 (`~/.gpt_tutor_config.json`); religar so ao
liberar. **INCIDENTE 05/09 tarde: 60 chamadas nao autorizadas** — o reprocess re-resume codigo por Gemini quando o hash da entry muda; a medicao
`title := label` nas copias disparou 60 resumos (MF 19, SO 8, IA 8, ES2 8, CG 17); originais intactos. **Regra: toda medicao ou reprocess roda com o
tripwire** (`_harness-2026-09-04/c1-3/shim_b.py` para copias — client nulo; `reprocess_cg_unidade.py`/`determinismo_tripwire.py` para produto —
voter so com cache, construtor do client explode) **e termina com `check_gemini_hoje.py` = 0.** Custo medido em 04-05/09: travessia 270 chamadas
x ~11-13k tokens; voter 23 votos; rebuild do CG ~110 chamadas.

## REGUA OFICIAL A PARTIR DE AGORA: a AUTOMATICA (user, 05/09 tarde: "gold so mede; nao criar curadoria por curso")
Motor + voter com cache, sem pino, sem glossario manual, com vocab LLM (`_harness-2026-09-04/c1-3/motor_auto.py`): **bloco 193/199 = 97,0% conf-err 0 ·
unidade 185/191 = 96,9% · cobertura 53/57 · subunidade 82/93 = 88% · holdout CG 35/35** (v2: vocab tambem no holdout, cache de votos do produto; 192 era com o cache antigo da copia). Motor puro (sem voter) segue como regua de diagnostico; curada
(com pinos) e o produto de hoje, nao a meta. Pinos e glossario manual sao ANDAIME: cada um deve ter regra generica ou voto de LLM que o substitua,
medido nos 8 — ou fica registrado como residuo humano com nome. Golds novos so para MEDIR (CG/MF subunidade: aprovar uma vez, nunca curar por curso).
**Subunidade: propagacao por headings ENTROU no motor (`4a239d9`): motor puro 82 -> 87/93; o IA automatico iguala o glossario manual (39/39).**
Resto sem LLM: SO fork/exec x4 (regra humana do gold contradiz o IA) e ES2 quase-empates x2. Caminhos com LLM: vocab compilado melhor · voto de LLM para
unidade de bloco sem evidencia lexical (CG bloco-08; 1 chamada por bloco assim).
**06/09 noite — golds CG/MF aprovados (regua 233) · fila sem a camada llm (57,5 -> 33,0 por 100; `0673150`) · decomposicao de rotulos na 2a passada
(`ff3eda7`): automatica x 233 187 -> 192 (82,4%), CG 49 -> 54/82, produto 193 -> 197 (84,5%); tracker §CG SUBUNIDADE 60% e §FILA DE REVISAO — CAMADA LLM CORTADA.
Regua SEM GOLD (posicao do professor no Moodle): coerencia 188/195 = 96,4% nos 5 cursos, 7 incoerencias = defeitos do Moodle (gold da razao ao motor);
CG/LR/FR sem posicao datada (regua nao cobre). Fila: P3 (sem sub-ambigua) 30,2/100 custo 0; P4 (sem conflito) 18,7/100 perde 7 erros do CG — decisao do user.
Janela ∩ unidade da secao (`8856d89`+`b421e92`) + fila sem janela-1 flagada/funil com voto: holdout CG puro 31 -> 33/35, FR do zero fila 11 -> 10, 26,7 (93/348: duvida 71 + mudou 22; por curso MF 11, SO 10, IA 4, ES2 12, TCC 7, LR 0, FR 5, CG 44; anatomia conflito 50, sub-ambigua 13, sub-empate 8, flag disamb 3)/100; produto curada bloco 198/199 conf-err 0 · unidade 191/191 · cobertura 55/57; subunidade x 6 golds 201/233 (8.
Unidade explicita da secao vence bloco (`1b41003`): FR do zero unidade x secao 10/19 -> 19/19; 7 cursos iguais. FR run A2 fila 11/20; run B (Gemini, so FR): build 840 s + 2 reprocess; chamadas Gemini: 10 summarize_bundle no build (code_curation.json NAO gravado — a investigar).
Regra da secao S1b (`4d649c4`, +3 -0 simulado, +2 no motor): automatica x 233 196 (84,1%), CG 58/82; produto 201/233 (86,3%), primario 169; CG 58/82, SO 15/15, IA 39/39, ES2 27/28, TCC 11/11, MF 51/58; gold `intro` corrigido pelo oraculo (origens).
Regra do titulo (`34d8b19`, +2 -0): automatica x 233 194 (83,3%), CG 56/82; produto 199/233 (85,4%), primario 166; CG 56/82, ES2 27/28, MF 51/58; tracker §CG CONFIANTES ERRADOS. Teto do CG sem LLM/sem dado novo ~56-58/82.**
**Camada 3 (resumos de codigo) medida (06/09, tracker §NO MAXIMO DUAS CAMADAS):** so a subunidade a sente: 87 -> 71 sem resumo, 79/78 com substituto
deterministico (mesma rota, produtor diferente); bloco/unidade/cobertura/holdout iguais. Os 8 que so o Gemini acerta sao vocabulario de categoria que
o codigo nao contem ('classificacao', 'chamadas de sistema', 'microsservicos'). Peso: 85 resumos / 205 votos / 1 vocab por curso nos 8.

## DESCOBERTAS DA NOITE DE 06/09 (indice; detalhe nas secoes do tracker `pendencias.md`, todas datadas 06/09 noite)
1. **Tela de login** era a sync criando entry de URL e o buscador pedindo a pagina sem sessao; corrigido na sync (`6d68578`), CG reparado (`404f5f9`,
   16 paginas com texto). Custou 2 no gold do CG: paginas-indice de videos vao para o filho mais citado (classe pai x filho, 10 dos 27 residuais).
2. **Placar por material** (`placar_100.py`; todos os golds do material certos, 288): zero LLM 155 · automatica 230 · produto 245; CG automatica 56/83.
3. **Zero LLM, os 133:** 116 falham em subunidade; em 48 o nome do subtopico do gold nao aparece em fonte nenhuma (IA 27, CG 14); ima de headings na
   taxonomia (heading grudado por token do titulo da unidade; 23 aliases; IA 35 confiantes) — raiz lida, correcao nao medida.
4. **ES2 unidade sem LLM:** 'microsservicos' esta em 2 unidades do plano (5 ocorrencias); a grafia (1 s no SARC) NAO e a causa (medido); o DP de
   blocos preenche por posicao (0,4) e o scorer da entry decide confiante (11 dos 18 erros de unidade do zero sao confiantes). Candidata A.
5. **Cerca de provas** (plano AVALIACAO x data no SARC): dura quebra o MF (17); como desempate de bloco sem sinal +3/-0. Candidata B.
6. **Lei reafirmada: SARC e Moodle > gold.** ES2: 7 materiais antes da P1 (secao 1) estavam no gold na unidade 02 porque o LLM pendurou 'API gateway'
   na 2.7 — corrigidos (produto perde 7 unidades e 6 subs: erros do LLM escondidos pelo gold). MF t2 -> bloco-20. 6 outras divergencias mantidas.
7. **Decisoes:** bloco de prova hospeda entrega (inverte o T17); bloco de prova tem unidade = escopo da prova (calendario > plano, a medir).
8. **API das salas** (`mede_salas.py`, 30 salas): abertura/vencimento/fechamento/enunciado/anexos por `mod_assign_get_assignments`; duracao separa
   atividade de aula (12) x trabalho (4) onde ha abertura (IA, LR); MF/SO/ES2 so vencimento; TCC so fechamento; vencimento x SARC 10/11 coerentes.
9. **Lacuna de material:** 10 anexos de salas fora do tutor — enunciados T1/T2 da IA e TP1/TP2 do SO so existem na sala (baixados e conferidos).
10. **Achado colateral:** vencimento posicional sem fronteira (MF 30 arquivos herdam 10/06 de um forum); exposicao 0 hoje; so o MF tem file_dues.
**Proximos, na ordem acordada:** item 4 (pull/sync: anexos + enunciado das salas viram material; ligacao estruturada arquivo -> sala; fronteira de
grupo) em copia · C1/C3/C5 no motor com gate · C2 com precedencia calendario > plano · candidatas A/B do zero LLM · regra pai x filho · vocab do
CG sem 'OpenGL' (Gemini) · fila 'conflito' · zips · push.

## COMECE POR (proxima sessao) — tres decisoes do user antes de qualquer codigo
**Texto que o motor le (07/09):** approved > curated > base > advanced; CG/LR/FR leem `staging/` (MD nao aprovado). O `advanced_markdown` do **Datalab nunca foi lido pelo motor** (198/198 aprovados vieram do pymupdf4llm), mas o Datalab ENTRA pelas descricoes de imagem injetadas no texto lido (142/305). A aprovacao individual injeta um sumario com todos os headings no topo (o lote nao) — estado desigual, medido em `c1-3/simula_aprovacao.py`. Backlog do user: produtor da descricao escolhivel (Datalab | Gemini | Ollama). 'Sem API paga' = sem chamada, nao sem influencia. Detalhe no tracker §DE ONDE VEM O TEXTO.
**Consolidacao das duplicacoes (07/09, commits A1 4f60bd0 · A2 0efa29a · B 46499aa · C 35cb99c):** gate `c1-3/zero_diff.py --base` (referencia do dia) / `--check` (0 arquivos = comportamento preservado); tokenizador de card unico, leitor unico de moodle_label, legado anchor_placement removido, listas em `text/stopwords.py`, regex em `text/patterns.py`; o que fica diferente por semantica esta listado no tracker §CONSOLIDACAO. Regra: nenhum filtro/tokenizador novo; migrar call site para `motor_tokens` so com zero-diff ou medida.
**Placar por material (06/09 noite, gold do ES2 corrigido pelo oraculo):** `python docs/reports/_harness-2026-09-04/c1-3/placar_100.py` (snapshots em `c1-3/snap_placar/`; zero LLM 156/288 · automatica 231/288 · produto 246/288 com todos os golds certos; CG automatica 56/83; produto unidade 184/191, sub 193/233). Tracker §PLACAR CONSISTENTE e §LEI REAFIRMADA. **Lei: SARC e Moodle > gold** (user, 06/09 noite).
**Salas de entrega pela API (06/09 noite):** abertura/vencimento/fechamento/enunciado/anexos via `mod_assign_get_assignments`; LACUNA: anexos das salas (enunciados T1/T2 da IA) nao entram no tutor; propostas C1-C5 no tracker §SALAS DE ENTREGA PELA API.
**Decidido (06/09 noite): bloco de prova hospeda entrega.** Gold do MF `t2-2026-1` -> bloco-20; produto bloco 197/199 (o due-window ancora na aula anterior por desenho T17: candidata C no tracker). Placar: zero 155 · automatica 230 · produto 245 / 288; unidade 183/190; sub 193/233.
0. Confirme o estado: `git status --short` (so `.claude/settings.local.json`, `.codex/` e `.mex/patterns/*` de outro agente), `git log --oneline -3`,
   HEAD dos 8 tutores = "Estado ao terminar", `python scripts/censo_motor_llm.py` (revisar/100 58,3 com 'mudou' 13; votos/100 35,9; FILE_MAP 100%
   nos 8, SO 38/39 por duplicata), `python -m pytest tests -q` (2325), `python scripts/sentinela_manifests.py` (0). Nada pushed.
1. ~~APROVAR os golds de subunidade propostos~~ **FEITO 06/09: aprovados pelo user, ligados na regua (MF em `motor_puro.py`, CG em `holdout_cg.py`,
   scorer `ablacao_rapida.score_subunit`); automatica x 233 = 187 (80,3%), CG 49/82, MF 51/58; causas no tracker §GOLDS CG E MF APROVADOS.**
   (texto original:) (`docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md`, coluna `ok?`): CG 82 pontuaveis
   (produto acerta 49 com extras, 36 primario), MF 58 (51, 36); 4 rulings marcados (bundle misto pelo card; `exemplodemanipulacaodeimagens`
   label 'Classe Vetor' x conteudo; convencao Dafny = `softwares-de-suporte` com extra `verificacao-de-programas`; OpenGL = vazio). Aprovado:
   ligar `subunit_gt_{CG,MF}.csv` em `scripts/motor_puro.py` (`SUBUNIT_GOLD`): a propagacao ja entrou (medida +5/-0 nos 6 golds com os propostos);
   o gold aprovado passa a ser regua permanente de CG/MF.
2. **BUG dos zips do MF (SYNC/C5):** extracao sem subpasta colide `ex1.dfy` entre 5 zips (4 zips sem conteudo no tutor; 5 resumos de codigo errados)
   e `.smv` (NuSMV) e ignorado. Corrigir na extracao (`<id>/<membro>` + `.smv` como codigo), re-resumir quando o Gemini for liberado, reprocess do MF.
   Decisao de fila (C5 esta estacionada).
3. **Liberar ou nao o Gemini** para fechar a C1: travessia final IA/FR/CG modo LLM (~90 chamadas; alvo IA >= 14/15, FR 15/15, CG rerodado — ja medido
   apos o item 1: IA 14, FR 15, CG 10-11); depois, so se a travessia errar por indice: item 4 ou "FILE_MAP titulo = label · stem"; e o prompt do voter
   com `label do Moodle` (90/125 votados tem label != title; re-voto <= 90 chamadas). Sem Gemini a C1 nao tem item.
   **3b. 'No maximo duas camadas LLM' (user 06/09):** qual cortar. Numeros: vocab +57 sub/+10 unidade · voter +7 bloco/+4 holdout · resumos +8 sub
   (0 no resto). Recomendacao: cortar a 3 trocando o produtor de `code_curation.json` pelo deterministico v2 (`c1-3/shim_codigo.py`, -8/93 sub);
   ou, para nao perder os 8, a compilacao do vocab ver o bundle de codigo (mesma chamada; exige Gemini para medir).
4. Gate de cada item: suite verde; sentinela 0 nos 8; determinismo 8/8 (so se `src/` mudar); curada intacta (198/199); commit com numero no tracker;
   tutores so mudam por reprocess registrado com tripwire (copia `.ablacao` antes); reprocess NAO commita quando so `updated_at` muda (caixa).

## Leis
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · **gold nao e oraculo: SARC e Moodle mandam; gold e humano e se
corrige com nota `SARC/Moodle <data> (user)`** · curadoria (pino de bloco/unidade, mapa de card, glossario manual) e a camada humana da arquitetura,
fix especifico ali e legitimo; fix de raiz vai para o motor so com saldo medido nos 8 · nada regride em regua nenhuma · estrutura estreita, texto
decide, estrutura NUNCA sobrepoe decisao confiante nem preempta o voto do LLM · **sinonimo manual e vocabulario de SUBtopico: nunca renomeia
bloco** (CG 05/09: 'Morfologia' em '3.5 Segmentacao' rotulou o bloco-08 e puxou 4 materiais do bloco certo; revertido) · nada pushed sem o
user · `.claude/settings.local.json` intocado · tokens (`moddle/.env`, `.env`) nunca impressos · [Humberto] · nao corrigir conteudo do professor em
silencio (marcar para review).

## Estado ao terminar (05/09 tarde, tudo commitado, NADA pushed)
Gerador `feat/motor-atribuicao` @ `4a239d9` (codigo: higiene `e0c433c` + radical-fallback `ff21cab` + propagacao por headings `4a239d9`) + docs da sessao 6. Sessao 6 (05/09 tarde), commits: `d511357` `8d61d28`
`75b9955` `7a19208` `dc98c15` `ef4628c` `009b627` `d880f1b` `17afd2e` (docs/medicoes) · `e0c433c` (feat higiene + teste) · `ff21cab` (feat radical-fallback + teste) · `4a239d9` (feat propagacao por headings + teste). Suite 2328.
Tutores (07/09, apos o reprocess da taxonomia padronizada): **MF `1c33ca0` · SO `d0c135e` · IA `e1540df` · ES2 `5640abe` · TCC `f296ab3` · LR `3348864` · FR `eb347d2` · CG `3775b1a`** (topicos 229 -> 228, subunidade 1, unidade 0, bloco 0; reguas intactas: 197/199, 183/190, 193/233, fila 27,6). Historico — Tutores (06/09 noite, apos o reparo do CG): **MF `ed31d99` · SO `c60e2d1` · IA `d88cc53` · ES2 `0fe0f53` · TCC `79a9696` · LR `5201deb` · FR `5c9372a` · CG `404f5f9`** (reparo registrado das 16 paginas do Moodle, `c1-3/repara_paginas_cg.py`, 0 chamadas; gerador `6d68578` corrige a sync). Historico — Tutores (06/09 noite, apos fila + decomposicao): **MF `ed31d99` · SO `f513ba0` · IA `74fec68` · ES2 `0fe0f53` · TCC `082b728` · LR `d139547` · FR `4c64ed6` · CG `929cdc3`** (antes: MF `7a8707a` · SO `0921948` · IA `0075334` · ES2 `4c8011b` · TCC `621c292` · LR `d139547` · FR `fd7814f` · CG `0d2020a`) (reprocess da propagacao:
MF/IA/ES2/TCC commitados, SO/LR/FR/CG so `updated_at` e nao commitados; CG: 4 reprocess
registrados: `c566dc3` pinos 06/08/15, `ee4c276` sinonimo de morfologia — REVERTIDO em `2c5e01e`, `0d2020a` pinos 06 e 15 REMOVIDOS, fica so o 08; 0 chamadas Gemini; votos 42 = 42).
Copias `.ablacao` dos 5 + CG + LR + FR (motor puro pos-higiene). `.ablacao/CG-rebuild` (365 MB) e `CG-export-backup` (440 MB): apagar e decisao do user.
**Reguas (gold pelo oraculo, 199 pontuaveis):** curada **198/199 conf-err 0** (falta ES2 `azure`) · unidade 191/191 · cobertura 55/57 · motor puro +vocab
**186/199 conf-err 1** · unidade 183/191 · cobertura 53/57 · sub 82/93 · holdout CG puro 31/35 conf-err 0 (flagados 14) · censo revisar/100 58,3
('mudou' 13 do reprocess do CG; era 57,8) · votos/100 35,9 · FILE_MAP 345/345 · **CG unidade: produto 1/93 errada (+2 por erro de bloco); AUTOMATICA (sem pino) 22/93 -> 6/93** (morfologia x3, texturas x3) · travessia pos-C1-item-1: IA 14/15 · FR 15/15 · CG 10/15 (11 completo) com LLM; sem-llm IA 10 · FR 9 · CG 5.
Golds de subunidade APROVADOS 06/09 e na regua: `subunit_gt_CG.csv` 82 pontuaveis · `subunit_gt_MF.csv` 58 (regua = 233; automatica 187 = 80,3%). **Regua automatica (v2, pos-propagacao): bloco 193/199 (97,0%, conf-err 0) · unidade 185/191 · cobertura 53/57 · **sub 87/93 (93,5%)** · holdout 35/35 · CG unidade 6/93 erradas sem pino.** Determinismo pos-higiene **8/8, 0 arquivos nao deterministicos**; 0 resumos de codigo de hoje nos originais e nas copias.

## BALANCO da sessao 6 (05/09 tarde)
- **C1 item 3 (title := label): REFUTADO por medicao, 0 codigo.** Piso sem-llm 0 flip; motor puro bloco 186 -> 184, 2 confiantes viram flag (label
  "Respostas" apaga o assunto do nome do arquivo); stem e label sao complementares; o FILE_MAP ja mostra o label.
- **Subunidade sem LLM, medido e refutado:** card (nome 0/+ 23/-; irmao 0/+ 2/-) · IDF intra-unidade (V1 0/0, V2 +1/-5, V2s 0/0) · raiz dos 4 do IA =
  vocabulario do glossario MANUAL (camada humana). **Propagacao por headings: +5/-0 no gold, mas sem gold no CG/MF nao entra** (caixa; destrava com o
  gold aprovado).
- **CG unidade 22/93 -> 1:** raiz = vocab compilado por LLM com nomes de secao pendurados em topicos genericos de u01 + ordem do professor invertida
  (DP monotonica). Motor: 5 alavancas genericas medidas e refutadas (sem aliases 183 -> 136; radicais saldo 0; vizinho ancorado 183 -> 163; exclusividade
  relaxada 179; higiene sozinha neutra). **Entrou no motor: higiene (`e0c433c`) e radical so como fallback (`ff21cab`, +1 bloco, 0 colateral).** Pinos 06 e 15
  removidos (produto identico); fica so o 08 (morfologia: plano nao menciona, residuo para voto de LLM de unidade). CG automatico: 22 -> 6 unidades erradas. Gates: motor puro 186/199 = · holdout 31/35 = · curada 198/199 = · sentinela 0 · suite 2325.
- **Golds de subunidade CG (82) e MF (58) propostos** para aprovacao; bug dos zips do MF medido; `gemini_auto_summarize` desligado pelo user.

## FILA DE CAMPANHAS (ordem decidida 03/09, atualizada 05/09 tarde)

### 0. FECHADAS — SYNC 6/6 (04/09) · C0 MOTOR 11/11 (05/09) (historico no `_archive/2026-09-05-handoff-fila-campanhas.md` e tracker §C0 ITEM 9-12)

### 1. ABERTA — C1 TRAVESSIA — itens 1, 2 e 3 FEITOS (3 refutado por medicao); falta a travessia final (LLM) e o item 4 (condicional, LLM)
Entrada medida no item 12 da C0; item 1 = FILE_MAP completo e magro (IA 9 -> 14/15); item 2 = titulo de bloco qualificado em colisao + CRONOGRAMA_DETALHADO
em TCC/LR; item 3 = title := label REFUTADO (§C1 ITEM 3). `python scripts/eval_travessia.py {IA,FR,CG} [--sem-llm|--contexto-completo]`.
**Pronto quando:** IA >= 14/15, FR 15/15, CG rerodado, sentinela 0 no motor. **Bloqueada em LLM: decisao 3 do COMECE POR.**

### 2. PROXIMA — C3 PROVAS, LISTAS E TRABALHOS (ordem registrada em 03/09; posicao da C7 IMAGENS e decisao do user na fronteira)
Granularidade da cobertura (prova inteira x questao), P2b-LLM (extracao de questoes, cacheado, contado), EXAM_INDEX honesto, triagem "em duvida 28/08".
**Pronto quando:** gold de ~10 provas + ~10 imagens medido e curada intacta.

### 3-8. ESTACIONADAS — C2 referencias/bibliografia (decisao B; `eth2`/`aws` u02 por ruling) · C4 limpa pre-web (byte-identico; tempo de reprocess: cache da
normalizacao, `find_spec`; reprocess nao commitar so por `updated_at`) · **C5 dividas de dados (ganhou 3 itens: bug dos zips do MF; GLOSSARY.md do CG para em
7.1.2 — u07 tardio, u08 e u09 sem termo, logo sem sinonimo manual possivel; gold de unidade do CG)** · C6 web · C7 imagens (dados e refutacoes no
`_archive/2026-09-05-handoff-fila-campanhas.md` §8).

## CAIXA DE IDEIAS (fora da campanha aberta; triagem so na fronteira)
Formato: **ideia** · da para fazer? · quando? · o que resolve?
- **Voto de LLM para a UNIDADE de bloco sem evidencia lexical** (CG bloco-08 morfologia: plano nao menciona; unico caso nos 8) · 1 chamada por bloco assim · substitui o pino do bloco-08 · precisa de Gemini.
- **Prompt do voter sem o `moodle_label`** (`llm_vote.py:241`; 90/125 votados tem label != title) · 1 linha + re-voto <= 90 chamadas · C1 fechamento (LLM).
- **FILE_MAP titulo = label perde o stem** (103 linhas; 7 labels sem conteudo) · "label · stem" quando o title tem token que o label nao tem · C1 item 4, so se a travessia errar.
- **Zips extraidos sem subpasta colidem nomes** — nos 8: CG 168 nomes repetidos entre 14 zips, ES2 38, MF 10, SO 3; `.smv` ignorado · `<id>/<membro>` + `.smv` como codigo · SYNC/C5 · codigo e resumo certos por zip.
- **Paginas do Moodle (`mod/page`) capturadas como tela de login** (CG 16/16; unico tutor com paginas) · capturar com sessao autenticada no pull · SYNC/C5 · conteudo real para rotear.
- **Saude de curso novo sem gold**: revisar/100 (CG 74-76 x media 58) + fracao de blocos preenchidos por posicao + conflitos texto x bloco no CRONOGRAMA_HEALTH · sim, so leitura · C4/C6 · sinal de 'olhar este curso' sem gold.
- **GLOSSARY.md para no ultimo termo que o parser do plano entende** (CG: 7.1.2; u08/u09 sem termo) · investigar o parser do plano do CG · C5 · sinonimo manual para texturas.
- **Gold de unidade do CG** (22 erros vieram a luz pelo gold de subunidade) · proposto-claude a partir de `2026-09-05-cg-atribuicoes.md` · C5.
- Custo do Gemini (Datalab para imagens, Gemini so fallback; medir chamadas por funcao) · C7/C3. Tempo de reprocess (CG 111 s, 83% em `normalize_match_text`
  sem cache) · C4. Data de entrega (`duedate`) dos trabalhos pela API · SYNC/C3. Conferencia das 37 formulas do CG por LLM · C3. Reprocess registrado
  commita so `updated_at` · C4. Apagar `.ablacao/CG-*` (805 MB) · agora, decisao do user. Merge/push dos ~840 commits em `main` · fronteira.

## Decisoes ABERTAS do user (nao travam a campanha 1)
- ~~Aprovar os golds de subunidade CG/MF~~ (feito 06/09). ~~Fila: camada `llm`~~ (`0673150`), ~~janela-1 flagada e funil com voto~~ (`8856d89`). Resta: 'conflito' (53, 0 erros de unidade) e sub-ambigua (13, 1 erro). Corrigir a extracao dos zips (2). Gemini (3). Religar `gemini_auto_summarize` so com o Gemini liberado.
- Qual camada LLM cortar para ficar em duas (COMECE POR 3b). Apagar `.ablacao/CG-rebuild` e `CG-export-backup`. Posicao da C7 IMAGENS. Push/merge em `main`. Revisao da fila `revisar_queue.md` (45) do CG. Fila 'conflito' (50, 0 erros de unidade) e sub-ambigua (13, 1 erro). Regra pai x filho para paginas-indice (10 dos 27 residuais do CG apos o reparo; hipotese, nao medida). Recompilar o vocab do CG sem o alias 'OpenGL' (9 gold-vazio; exige Gemini). Blocos sem unidade (entrega/revisao): adiado pelo user.

## NAO fazer (refutado no gold)
**05/09 tarde (sessao 6):** `title` do manifest := `moodle_label` (piso 0; bloco 186 -> 184; 2 confiantes viram flag) · subunidade de codigo pelo card (nome 0/+
23/-; irmao 0/+ 2/-) · IDF intra-unidade no scorer de subtopico (V1 0/0, V2 +1/-5, V2s 0/0) · mapa bloco->unidade sem aliases (183 -> 136) · radicais nos
tokens do mapa (saldo 0: 'proces~processamento') · preenchimento pelo vizinho ancorado no lugar da DP (183 -> 163) · exclusividade relaxada da ancora
(179) · sinonimo manual que renomeia bloco ('Morfologia' em Segmentacao: 4 materiais mudaram de bloco).
**05/09 madrugada:** peso do label no desempate x2/x3 (50 -> 47/48) · janela do card = secao (72 -> 56; janela-1 21 -> 15) · data de postagem como decisor
(33/52) · "revisao" fora dos genericos (50 -> 50) · H9 sobre confiante (saldo 0). **Anteriores:** serie k -> k-esimo bloco · serie monotonica · prova antiga
-> prep · H7 ordem das secoes · H6 label unico · label em decisao confiante · card ANTES do voter · regex de nome para card generico · imprimir HTML em PDF
para o Datalab · rastrear `Aulas/` do site do professor · `unit_block_conflict` como alavanca de banda.

## Artefatos publicados (06/09 noite; + Matriz de Atribuicao em 07/09)
- Matriz de Atribuicao (348 materiais x 5 regimes x 3 eixos + professor e gold como referencia): https://claude.ai/code/artifact/4ddad807-e2fe-4ede-a3ca-c175916f7ca6
- Placar do Motor de Atribuicao (consolidado da sessao 6): https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de
- Razao dos Blocos (estado curado dos 8, regenerado pelo gerador `_archive/scripts-2026-09-04/artefato_razao/`, gerador d079604): https://claude.ai/code/artifact/d2ef4eaa-3483-412a-9dc8-110b1f9ccacb
- Gold x Moodle x SARC (auditoria regenerada: `_harness-2026-09-02/audita_gold.py` sobre motor puro + vocab de 06/09; 188 AULA, 148 concorda, 3 divergem, 37 sem posicao): https://claude.ai/code/artifact/f53542b1-9061-4034-a1f3-e86ce001a81f
- Anatomia do Bloco (leitura de 01/09 + faixa de atualizacao 06/09): https://claude.ai/code/artifact/ba1de7bf-a802-49fc-b88b-6be358d4b796
- Raio-X da Atribuicao (leitura de 02/09 + faixa de atualizacao 06/09; HTML-fonte reescrito, o original nao estava mais em disco): https://claude.ai/code/artifact/399626ee-682b-43f8-9987-09c344f6c60f

## Ferramentas
`scripts/` (37): `sync_moodle.py` · `motor_puro.py [--com-vocab]` · `censo_motor_llm.py` · `sentinela_manifests.py` · `eval_eixos.py` · `reprocess_assignments.py` ·
`moodle_pull.py` · `eval_travessia.py` · `_harness-2026-09-02/{regua_aula,holdout_cg,calibra_revisar,mede_alavancas,determinismo}.py`.
**Sessao 6 (`_harness-2026-09-04/c1-3/`, README la):** `shim_b.py` (tripwire para copias) · `check_gemini_hoje.py` · `snapshot.py`/`diff_b.py` · `medicao_a_piso.py` ·
`leitores_title.py` · `simula_sub_card.py` · `simula_idf_sub.py` · `simula_propaga_headings{,_weak,_semgold}.py` · `simula_unidade_sem_alias.py` ·
`simula_raiz_unidade.py` · `gera_gold_subunidade.py` · `reprocess_cg_unidade.py` (tripwire de produto) · `determinismo_tripwire.py`.
Relatorio das atribuicoes do CG: `docs/reports/2026-09-05-cg-atribuicoes.md`. Padrao: `.mex/patterns/medir-alavanca-ablacao.md`.
