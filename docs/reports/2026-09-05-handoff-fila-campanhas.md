# Handoff 2026-09-05 — PONTO DE ENTRADA: a FILA de campanhas (C1 aberta, C3 proxima, o resto estacionado)

Unico handoff vivo. Substitui `_archive/2026-09-04-handoff-fila-campanhas.md` (C0 FECHADA 11/11 em 05/09; C1 itens 1-3 feitos, o 3 refutado por medicao). **Leia nesta
ordem:** (1) este arquivo; (2) `pendencias.md` §C1 ITEM 3, §GOLD PELO ORACULO, §C1 ITEM 1-2, §C0 ITEM 12 (numeros); (3) `.mex/context/decisions.md`
(decisoes de 04-05/09). Rode `mem-search` para a sessao de 04-05/09.

**Regra de fila (user, 03/09):** UMA campanha aberta, UMA proxima, o resto ESTACIONADO. **Campanha so fecha com 100% dos itens**; item nao
feito ou e feito, ou o user o RETIRA por decisao registrada. Novo lote = novo handoff, o anterior vai para `_archive/`. Ideia que surge no meio
vai para a CAIXA DE IDEIAS (da para fazer? · quando? · o que resolve?).

**GEMINI (user, 05/09 manha): credito recarregado, mas NAO USAR ate o user mandar.** Tudo que segue e medicao/codigo sem LLM. O que
depende de LLM e fica na fila: travessia pos-itens 1-3 da C1 (so modo LLM, 1 rodada por item, ~45-105 chamadas) e re-voto do voter onde um
pino nao resolver. Custo medido da sessao 04-05/09: travessia 270 chamadas x ~11-13k tokens; voter 23 votos novos; rebuild do CG ~110 chamadas.
**INCIDENTE 05/09 tarde (sessao 6): 60 chamadas Gemini NAO autorizadas.** O reprocess re-resume codigo por Gemini quando o hash da entry muda
(config da UI `gemini_auto_summarize=True` + chave; sem interruptor de ambiente); a medicao title := label nas copias disparou 60 resumos (MF 19,
SO 8, IA 8, ES2 8, CG 17). Originais intactos; referencias com cache intacto. Tripwire em `_harness-2026-09-04/c1-3/shim_b.py` + pos-check
`check_gemini_hoje.py`. **Regra nova: toda medicao ou reprocess que mude `title`/conteudo de codigo roda com tripwire, ou com
`gemini_auto_summarize` desligado na UI** (decisao do user, abaixo). Detalhe no tracker §C1 ITEM 3 (INCIDENTE).

## COMECE POR (proxima sessao) — C1 TRAVESSIA: itens 1-3 FEITOS (3 por medicao); o que falta e LLM (decisao do user: liberar Gemini)
0. Confirme o estado: `git status --short` (so `.claude/settings.local.json`, `.codex/` e `.mex/patterns/*` de outro agente podem aparecer),
   `git log --oneline -3`, HEAD dos 8 tutores iguais aos de "Estado ao comecar", `python scripts/censo_motor_llm.py` (revisar/100 57,8; votos/100
   35,9; FILE_MAP 100% nos 8, SO 38/39 por duplicata), `python -m pytest tests -q` (2324). Nada pushed.
1. **Item 3 FEITO por medicao (05/09 tarde, §C1 ITEM 3 no tracker): REFUTADO, 0 codigo.** Piso sem-llm com title := label: 0 flip nos 3 cursos;
   motor puro bloco 186 -> 184/199 (MF, label "Respostas" perde `conjuntos`/`arrays`), 2 confiantes viram flag; sub/unidade/holdout iguais (remedido
   LIMPO apos o incidente Gemini, ver acima).
   Nome do arquivo e label sao COMPLEMENTARES (103 entries tem token so no title); o motor ja soma os dois; o FILE_MAP ja mostra o label (item 1).
2. **Com Gemini liberado (decisao do user), nesta ordem, 1 rodada cada:** (a) travessia final IA/FR/CG modo LLM (~90 chamadas; alvo IA >= 14/15,
   FR 15/15, CG rerodado; ja medido apos o item 1: IA 14, FR 15, CG 10-11) — fecha a C1 se bater; (b) so se a travessia errar por indice: item 4
   (indice por unidade/termos) ou "FILE_MAP titulo = label · stem" (103 linhas); (c) prompt do voter com `label do Moodle` (90/125 votados tem
   label != title; re-voto <= 90 chamadas; entra so se conf-err cai sem regua regredir).
3. **Sem Gemini:** a C1 nao tem item sem LLM. Opcoes do user: liberar Gemini; ou adiantar da caixa um item byte-identico (reprocess nao commitar
   quando so `updated_at` muda; cache da normalizacao; `find_spec` no `write_build_report`) — e decisao de fila (C4 esta estacionada).
4. Gate de cada item: suite verde; sentinela 0 nos 8; determinismo 8/8 (so se `src/` mudar); curada intacta (198/199); commit com numero no
   tracker; tutores so mudam por reprocess registrado (copia `.ablacao` antes); reprocess NAO commita quando so `updated_at` muda (caixa).

## Leis
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · **gold nao e oraculo: SARC e Moodle mandam; gold e humano e se
corrige com nota `SARC/Moodle <data> (user)`** · curadoria (pino, mapa de card) e a camada humana da arquitetura, fix especifico ali e legitimo;
fix de raiz vai para o motor so com saldo medido nos 8 · nada regride em regua nenhuma · estrutura estreita, texto decide, estrutura NUNCA
sobrepoe decisao confiante nem preempta o voto do LLM · nada pushed sem o user · `.claude/settings.local.json` intocado · tokens (Moodle
`moddle/.env`, Datalab/Gemini `.env`) nunca impressos · [Humberto] · nao corrigir conteudo do professor em silencio (marcar para review).

## Estado ao comecar (05/09 manha, tudo commitado, NADA pushed)
Gerador `feat/motor-atribuicao` @ `7c76a00` + docs do item 3 (sessao 6, 05/09 tarde), 871+ commits a frente de `main`. Sessao 5 (03-05/09), commits de codigo: `728c0f1` (11a)
`86dab7e` (11b) `4a14d8b` (10) `557be23` `1284b26` (9) `0ff832a` `4db9a6c` `df0e34f` `6afdcff` `d5d7629` (C1 item 1) `333d635` `09415da` (C1 item 2)
`734ca8b` (gold pelo oraculo + regua honra `scorable`). Suite 2324.
Tutores: MF `afb83cb` · SO `0921948` · IA `d7d81ed` · ES2 `ba7d2c8` · TCC `13ced08` · LR `d139547` · FR `fd7814f` · CG `0986874` (CG = `e3d02ed`
rebuild pela API + complemento + reprocess 11a/11b/10/C1; 93 entries; stash `Desktop/Moodle/computacao-grafica/stash/`). Copias `.ablacao` dos 5 +
CG + LR + FR (estado motor puro pos-item 10). `.ablacao/CG-rebuild` (365 MB) e `CG-export-backup` (440 MB): apagar e decisao do user.
**Reguas (gold pelo oraculo, 199 pontuaveis):** curada **198/199 conf-err 0** (falta ES2 `azure`, imagem sem texto) · unidade 191/191 · cobertura
55/57 · motor puro +vocab **186/199 conf-err 1** · unidade 183/191 · cobertura 53/57 · sub 82/93 · AULA 174/189 (flagados no puro 45/189) · REF 8/10 ·
holdout CG puro 31/35 conf-err 0 (flagados 14) · curado 35/35 · censo revisar/100 57,8 · votos/100 35,9 (remedido 05/09 tarde; 2 pinos MF) · FILE_MAP 345/345 materiais nos 8 ·
travessia pos-C1-item-1: IA 14/15 · FR 15/15 · CG 10/15 (completo 11) com LLM; sem-llm IA 10 · FR 9 · CG 5.

## BALANCO em 05/09
- **SYNC — 6/6, FECHADA (04/09).** CG rebuild pela API promovido; formulas 37/37 aprovadas pelo user.
- **C0 MOTOR — 11/11, FECHADA (05/09).** 11a exclusivo 2+ tokens · 11b voter so em flagada/serie/prazo/funil + votos no CRONOGRAMA_HEALTH · 10 ancora
  lexical exclusiva no mapa bloco->unidade · 9 scripts 81 -> 37 + regua AULA podada · 12 travessia "depois" (limite era o FILE_MAP, nao o motor).
- **C1 TRAVESSIA — ABERTA; itens 1, 2 e 3 FEITOS.** FILE_MAP completo e magro (80 KB, TRACE, titulo = label, Secoes 3/80) · titulo de bloco qualificado
  so em colisao de aula (16) + CRONOGRAMA_DETALHADO em TCC e LR · item 3 medido e REFUTADO (title := label regride o motor puro 186 -> 184; piso 0).
  Falta: travessia final (LLM), item 4 (condicional, LLM).
- **Gold pelo oraculo (05/09):** TCC aula-17 -> 19, MF arvores/listas -> 05, IA prova antiga fora; curadoria: pinos MF + card TCC; regua de bloco honra
  `scorable`. 4 alavancas estruturais para o motor puro medidas e REFUTADAS (ver NAO fazer).

## FILA DE CAMPANHAS (ordem decidida 03/09, atualizada 05/09)

### 0. FECHADA 05/09 — C0 MOTOR 11/11 (historico dos itens abaixo; detalhe no tracker §C0 ITEM 9-12)
9. **FEITO 04/09 noite (`557be23`, `599ff10`, `1284b26`; §C0 ITEM 9).** `scripts/` 81 -> 37 por grafo de dependencias medido (44 + artefato_razao
   arquivados em `_archive/scripts-2026-09-04/` com README; 4 testes foram junto, suite 2337 -> 2312); escada stale da `regua_aula.py` podada.
   src/ intocado = byte-identico por construcao; sentinela 0/8.
10. **FEITO 04/09 noite (`4a14d8b`; §C0 ITEM 10).** Medido: 10/12 erros = mapa bloco->unidade da DP sem pinos. Alavanca com numero: ancora
   lexical exclusiva (>= 2 tokens + token so da unidade), 3 blocos nos 8, unidade 179 -> 183/191, 0 regressao. Resto sem alavanca estrutural.
11. **FEITO 04/09 noite (11a `728c0f1` + 11b `86dab7e`; §C0 ITEM 11a/11b no tracker).** Fase 4: LLM so nos flagados (ja era o desenho; serie
   confiante fica, paga 1 conf-err), contado no CRONOGRAMA_HEALTH (36,5/100); ordem motor -> LLM -> card fica (199 -> 187 em 03/09); residual
   flagado AULA 7,9/100 (gate <= 8 atendido). Regua por item (com vocab + curada + holdout; ablacao so em gate) = decisao aberta do user.
   **11a (primeiro, medido 04/09 em `_harness-2026-09-03/s6f/mede_exclusivo.py`):** regra `exclusivo` do disamb (s2=0 -> alta) com UM
   token: 22 decisoes nos 6 golds, 5 erradas (77%; 2+ tokens e margem dao 94%) -> 1 token vira banda media + flag; medir motor_puro
   +vocab, eval_eixos, regua_aula, holdout CG (gold re-chaveado). Entra so se conf-err cai sem AULA/curada regredir. **FEITO 04/09 noite
   (`728c0f1`): entrou — conf-err 3 -> 2 (puro), holdout puro conf-err 2 -> 0, curado 35/35, nenhuma regua regrediu; custo votos/100 29,9 -> 36,5.**
12. **FEITO 05/09 (§C0 ITEM 12).** Travessia "depois" = "antes" no IA e no FR (material); CG limitado pelo FILE_MAP (26/93), bloco melhorou.
**C0 FECHOU em 05/09: 11/11 feitos, cada um com numero no tracker.**

### 1. ABERTA (05/09) — C1 TRAVESSIA (FILE_MAP completo e magro) — itens 1, 2 e 3 FEITOS (3 refutado por medicao, §C1 ITEM 3); falta a travessia final (LLM) e o 4 (condicional, LLM) — so com liberacao do user
Entrada medida no item 12 da C0: CG FILE_MAP 26/93 e 8/8 erros da travessia fora do corte; linha do FILE_MAP imprime `title` (nome de arquivo)
e nao `moodle_label`; label de bloco duplicado no cronograma do FR (bloco-06/20).
Unico item com numero de PRODUTO grande ja medido: IA 9 -> 14/15 com o indice completo (o corte de 12 KB esconde 40/59 materiais).
Itens: rastreabilidade (`FILE_MAP_TRACE.md`), coluna "Secoes" limitada, clamp 80 KB + aviso; indice por unidade/termos so se a
regua pos-C1 mostrar erro dessa forma. `python scripts/eval_travessia.py {IA,FR,CG} [--sem-llm|--contexto-completo]`.
**Pronto quando:** IA >= 14/15, FR 15/15, CG rerodado, sentinela 0 no motor. 1 sessao.

### 2. PROXIMA — C3 PROVAS, LISTAS E TRABALHOS (ordem registrada em 03/09; a posicao da C7 IMAGENS e decisao do user na fronteira)
Granularidade da cobertura (prova inteira x questao a questao — decisao aberta desde 18/08), P2b-LLM (extracao de questoes,
cacheado, contado), EXAM_INDEX "incidencia por topico" honesto, triagem "em duvida
28/08" (PS/G2 como principais, cadeira sem prova, `U1 - ...`/"Laboratorio N"). **Pronto quando:** gold de ~10 provas + ~10
imagens medido e curada intacta.

### 4. ESTACIONADA — C2 REFERENCIAS E BIBLIOGRAFIA (por ultimo, ordem do user)
Decisao B (eth2/aws {u02} ou N:N); vetar `coverage_gt_{SO,MF,IA}.csv` (9/10, baseline 0/9); pino de cobertura 57/57 ou 55/57
documentado; consumo de bibliografia (decisao 22/07 "caso a parte"); os videos do FR e 23 links do CG (hoje llm-funil/duvida).
**Pronto quando:** regua de referencias sobe de 0/9 e cobertura curada nao cai.

### 5. ESTACIONADA — C4 LIMPA PRE-WEB (byte-identico)
Cortes 2 e 4, 13 tokenizadores -> `text/tokens.py`,
17 limiares -> `thresholds.py`, `concept_resolver` so apos medir os 8 consumidores, CODE_INDEX "sem aula atribuida" (decisao H),
`auditoria-enxame`. **Pronto quando:** determinismo 0, sentinela 0 total, ablacao identica, suite verde — zero mudanca de numero.

### 6. ESTACIONADA — C5 DIVIDAS DE DADOS (dependem do user; paralelizavel)
Lab SO (SARC da turma 310), GAP VIDEO do T2, 10 suspeitos do `detecta_headings`, `content/` sem markdown de material no LR
(consolidacao e etapa da UI). **Pronto quando:** cada item tem gold proprio ou ruling.

### 7. ESTACIONADA — C6 WEB
Backlog vivo em `pendencias.md` §CAMPANHA FUTURA; `graph.json` derivado como modelo de dados. Depois de C4.

### 8. ESTACIONADA — C7 IMAGENS (decisao do user 04/09: campanha propria; posicao na fila a decidir na fronteira)
Objetivo do user: nenhuma imagem captada 2 ou mais vezes, e logos/imagens de template fora do tutor. Dado medido 04/09 (CG, 977 imagens):
3 familias por PDF (`page-NNN-img` do pymupdf, `-datalab-<md5>_img`, `<arquivo>.pdf-NNNN-NN`), 359 orfas (213+146) nunca citadas; 299 logos
(296 curados pelo user em `content/images/logos/` + 3 achados por dHash<=8, conferidos na imagem; galeria PARCIAL, "tem mais"), 0 citados em
markdown, entram pelo bloco de `resolve_content_images` que copia toda imagem extraida para o Image Curator; 39 logos nos bundles do stash
(0 lidos); 7 alts de logo virando texto (CG 2 `PUCRS logo`, TCC 5 `watermark of the USP crest`); mesma pagina do Moodle em 2 secoes = 2
entries (Resolucao de Prova 2D, modulos 3770178/3770183). Galeria dHash<=8 nos 8 tutores: CG 3, TCC 25, SO 2, IA 1, outros 0; 0 citados.
**REFUTADO:** cluster dHash automatico sem galeria (flagaria 191 fora do dir, 84 citadas, GIFs de formula das Curvas); md5 exato pega so
203/296 (logo com numero de slide queimado); "169 refs a template no CG" (03/09) nao se reproduz: 0 grupos template entre as 322 citadas.
Itens: (1) medir duplicacao entre as 3 familias (md5 + dHash) e decidir UMA fonte por PDF; (2) galeria `data/image_templates/` (42
representantes dHash<=4, 1 MB, seed = `logos/` do user) + `is_template_image` (md5 ou dHash<=8, PIL, sem lib nova) na copia para
`content/images`, na ref `![]`/descricao Gemini e em `save_material`; (3) pagina repetida -> 1 entry (md5 do html sem ids de player);
(4) imagens do Datalab consumidas pelo tutor (era C3); (5) limpar os 8 tutores rodando so a etapa de imagens, copia `.ablacao` antes.
Gate: curada, holdout, sentinela e determinismo identicos; por tutor contar `content/images` (esperado CG -299, TCC -25, SO -2, IA -1),
refs md alteradas (esperado so os 7 alts), stash CG -39. **Pronto quando:** 0 duplicata por md5 em `content/images` dos 8 e 0 hit de galeria.

## CAIXA DE IDEIAS (fora da campanha aberta; triagem so na fronteira)
Formato: **ideia** · da para fazer? · quando (campanha)? · o que resolve no sistema?
- **Prompt do voter sem o `moodle_label`** (`llm_vote.py:241` mostra so `titulo`; 90/125 votados tem label != title: CG 31, MF 31, ES2 16 — o voter ve "Vis3d")
  · sim, 1 linha no prompt + re-voto <= 90 chamadas · C1 fechamento (LLM) · voto com o nome humano; entra so se conf-err cai sem regua regredir.
- **FILE_MAP titulo = label perde o stem** (103 linhas com token so no title; 7 com label sem conteudo: MF "Respostas" x6, CG `vis2d` "Introducao")
  · sim: "label · stem" quando o title tem token que o label nao tem · C1 item 4 (so se a travessia LLM errar dessa forma) · roteador com os dois sinais.
- Conferencia das 37 formulas do CG por LLM (Gemini ve a imagem e compara com a transcricao do Datalab; ~37 chamadas) · sim · C3 · segunda opiniao
  depois da aprovacao humana de 04/09; so lista divergencias, nao corrige.
- **Custo do Gemini (user 05/09: R$43 em poucos dias para um fallback):** imagens dos materiais deveriam passar pelo Datalab (descricao ja vem no
  markdown do arquivo) e o Gemini ficar so como fallback; travessia so no modo LLM e uma rodada por item; medir chamadas por funcao antes de mexer
  · sim · discutir com a C7 IMAGENS · menos API por rebuild. Dado desta sessao: travessia 165 chamadas x ~11-13k tokens; voter 23 votos (cache 205).
- **Tempo de reprocess (user 05/09: "vale auditoria"; medido com cProfile nas copias):** CG 111 s, dos quais 92,5 s (83%) em
  `apply_unit_subunit_fields` -> `_score_entry_against_taxonomy_topic` -> `normalize_match_text` (85,6 s: normalizacao refeita por par
  entry x topico x frase, sem cache); LR 11,6 s, dos quais 8,8 s em `write_build_report` -> `load_docling_python_api` (importa o docling so
  para dizer se existe). Determinismo = 16 reprocess sequenciais (~10 min); reprocess dos 8 sequencial. Correcoes byte-identicas: cache da
  normalizacao (lru), determinismo com 1 rodada comparada ao original commitado, paralelismo por tutor (`ablacao_rapida.reprocess_parallel`),
  `find_spec` no lugar do import · sim · campanha futura (C4) · determinismo ~10 -> ~1-2 min, reprocess dos 8 ~8 -> ~2 min.
- Janela do card = secao inteira: REFUTADA 05/09 com numero (todos os materiais da secao 72 -> 56; so janela-1 por card 21 -> 15, 25/27 flagados). A
  janela-1 pelo label do card e a melhor aposta estrutural; o resto e voto cacheado ou humano. Nao repetir sem sinal novo (ex.: data por material no Moodle).
- **Data de entrega dos trabalhos (user 05/09: postagem + entrega como alavanca de T1/T2):** nenhum manifest tem `duedate`; capturar `dates` de assign/quiz
  no pull da API e persistir por entry, depois medir contra o gold (hoje prazo vem do SARC: 7/9) · sim · SYNC/C3 · trabalhos sem chute.
- Peso do label do Moodle no desempate: REFUTADO 05/09 (50 -> 47/48 em 58 disamb; quebra k-NN do IA). Nao repetir.
- Matcher bloco->topico absorvido por aliases genericos da taxonomia (FR: topico "Modelos OSI e TCP/IP" herda os nomes de todas as camadas e pontua 1,0 para
  qualquer aula "camada X"; o topico certo fica em 0,14) · corrigir exige GOLD DE TOPICO por bloco (nao existe) · campanha futura · labels de bloco certos, menos colisao.
- Reprocess registrado commita quando so o `updated_at` do manifest muda (7 commits de ruido em 05/09) · sim: comparar sem `updated_at` antes de commitar · C4 · historico limpo.
- Watchdog de formula transcrita x texto ao redor (erro do professor vs OCR) · sim, heuristica fraca · C3 · so listaria suspeitas; a
  lista de formulas para review (S6c) ja da o caminho humano.
- Regua por item so com vocab (ablacao sem vocab em gate de fase) · sim, 1 flag · C0 item 11 · corta 2,5 min por item.
- Merge/push dos 805 commits em `main` · sim · fronteira SYNC -> C0 · tira o risco de branch longa.
- Bold aninhado do Word vira `**P(****0) = P0**` no conversor (Curvas.htm) · sim, conversor · C4 limpa (ou S6f se atrapalhar o tutor) · legibilidade do material HTML.
- Imagem http do MESMO host da pagina -> arquivo do mirror do snapshot (hoje "nao capturada": 12 refs em 20 paginas do CG) · sim · S6d · menos "nao capturada".
- FILE_MAP nao lista o html novo (clamp 12 KB; nem o PDF irmao aparece) · ja e o item da C1 · C1 · indice completo.
- Imagem do mesmo host numa pagina do Moodle SOLTA (`Window1.png`, 2 refs) · sim: pagina do Moodle como bundle quando tem `<img>` externo · S6 futuro/C3 · menos "nao capturada".
- Regra `exclusivo` do disamb (s2=0 -> alta) com UM token: 22 decisoes nos 6 golds, 5 erradas (77% x ~98% prometido pela banda alta; 2+ tokens e margem dao 94%) · sim: 1 token -> banda media + flag, medir motor_puro + eval_eixos + holdout · C0 item 11 · -5 conf-err no puro, 17 certas viram duvida (+~22 votos); `unit_block_conflict` nao separa (2/7 x 5/51). `s6f/mede_exclusivo.py`, `s6f/mede_conflito.py`.
- Imagem de prova (texto OCR) vira `![Figura: <texto>]` longo em vez de bloco de texto · sim · C3 provas · legibilidade das resolucoes de prova.
- Migrar os 4 labs `.htm` do LR de PDF impresso para html (regra (a) do S6d) · sim: readd dos 4 · fronteira C0 -> C1 · fidelidade das imagens dos roteiros.
- Sobras `.ablacao/CG-rebuild` (365 MB) e `CG-export-backup` (440 MB) · apagar quando o user confirmar o CG novo (gate-html e rebuild-holdout ja foram) · agora · disco.
- `sync_diff` lista como NOVO modulo cujos arquivos sao todos de extensao ignorada (2 xlsx do CG) · sim: classificar como ignorado · fronteira C0 -> C1 · relatorio sem ruido.
- Imagens-template, logos e duplicatas -> virou campanha propria **C7 IMAGENS** (fila, item 8); dados e refutacoes estao la.

## Decisoes ABERTAS do user (nao travam a campanha 1)
- **Desligar `gemini_auto_summarize` na UI enquanto o Gemini estiver bloqueado** (incidente de 60 chamadas em 05/09 tarde; sem isso qualquer
  reprocess que mude hash de codigo chama a API). O tripwire cobre so as medicoes com o shim.
- **Gemini:** credito recarregado 05/09; liberar uso (travessia final da C1 e re-votos) e decisao sua. Ate la, so medicao sem LLM.
- **Apagar** `.ablacao/CG-rebuild` (365 MB) e `.ablacao/CG-export-backup` (440 MB). **Posicao da C7 IMAGENS** na fila (hoje 8a). IA `prova-1-2024-02`
  ficou com `manual_unit_slug` (unidade pinada); pino de bloco removido.
- **Push/merge em `main`:** ~825 commits verdes na branch; a fronteira SYNC -> C0 chegou. Proposta: merge/push agora.
- Revisao humana do CG novo: **formulas 37/37 APROVADAS pelo user (04/09)** (`s6f/formulas_index.md`; `Image2.gif` da Curvas mantem o erro
  do professor nos expoentes, fonte nao corrigida). Falta o veredito da fila `revisar_queue.md` (45) — nao trava o C0.
- Regua por item com vocab (campanha 5) · decisao B (campanha 4) · golds proposto-claude — revisao sua, quando quiser.

## NAO fazer (refutado no gold)
**Medido e refutado em 05/09 (motor puro, copias):** subunidade de codigo de apoio pelo card — nome do card (0 '+', 23 '-') e irmao principal do card (0 '+', 2 '-')
(§OS 32 ERROS; o scorer de subtopico nao le o card e nao deve) · IDF intra-unidade no scorer de subtopico (V1 0/0, V2 +1/-5, V2s 0/0; a raiz dos 4
do IA e vocabulario do glossario MANUAL, camada humana) · `title` do manifest := `moodle_label` (C1 item 3: piso 0; bloco 186 -> 184, 2 confiantes
viram flag, sub/unidade iguais; label generico como "Respostas" apaga o assunto que o nome do arquivo carrega — stem e label sao complementares, o motor ja soma os dois) ·
peso do label do Moodle no desempate x2/x3 (50 -> 47/48 em 58) · janela do card = secao inteira,
todos os materiais (72 -> 56, 45 flagados) e so janela-1 por card (21 -> 15, 25/27 flagados) · data de postagem como decisor (33/52 = 63%; flagados 4/9)
· "revisao" fora dos stems genericos (50 -> 50) · H9 sobre decisao confiante que contradiz o card ordenado (2 casos, saldo 0). A janela-1 pelo label do
card e a melhor aposta estrutural (21/27); o que sobra no motor puro e voto cacheado ou pino. Nao repetir sem dado NOVO do Moodle (data/`duedate` por material).
Serie k -> k-esimo bloco · serie monotonica (+1/-2) · prova antiga -> prep (0) · H7 ordem das secoes pos-item 3 (0/0) · H6 label
unico (0/0) · label em decisao confiante · card ANTES do voter · regex de nome para card generico (secao 0 e o sinal) · imprimir
pagina HTML em PDF para o Datalab (texto ja e texto; so as imagens vao ao Datalab) · rastrear o indice `Aulas/` do site do
professor (entra so o que um card do Moodle aponta). · `unit_block_conflict` como alavanca de banda (erradas 2/7 x certas 5/51,
04/09).

## Ferramentas
`scripts/` tem 37 (corte 1 em 04/09; arquivo em `_archive/scripts-2026-09-04/README.md`): `scripts/sync_moodle.py` · `scripts/motor_puro.py [--com-vocab]` · `scripts/censo_motor_llm.py` · `scripts/sentinela_manifests.py` ·
`scripts/eval_eixos.py` · `scripts/reprocess_assignments.py` · `scripts/moodle_pull.py --course N --root R [--dry-run|--pdf]` ·
`scripts/eval_travessia.py` · `_harness-2026-09-02/{regua_aula,holdout_cg,calibra_revisar,mede_alavancas,determinismo}.py` ·
pulls reais em `_harness-2026-09-03/pulls/{FR,LR,CG}/` · piloto Curvas versionado em `_harness-2026-09-03/piloto-curvas/` (Curvas.htm, 27 imagens, gold Datalab, `gate_s6b_curvas.py` = Curvas de ponta a ponta numa copia do CG, `Curvas.s6b.md` = saida do S6b).
