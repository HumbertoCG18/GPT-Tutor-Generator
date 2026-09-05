# Handoff 2026-09-04 — PONTO DE ENTRADA: a FILA de campanhas (C0 aberta, C1 proxima, o resto estacionado)

Unico handoff vivo. Substitui `_archive/2026-09-03b-handoff-fila-campanhas.md` (SYNC FECHADA em 04/09). **Leia nesta ordem:**
(1) este arquivo; (2) `pendencias.md` §GATE DA FASE 3, §HOLDOUT e §SYNC S6f (numeros); (3) `.mex/context/decisions.md` (decisoes de
03-04/09). Rode `mem-search` para as sessoes de 03-04/09.

**Regra de fila (user, 03/09):** UMA campanha aberta, UMA proxima, o resto ESTACIONADO. **Campanha so fecha com 100% dos itens**
(criterio estrito); item nao feito nao muda de dono sozinho — ou e feito, ou o user o RETIRA por decisao registrada. Novo lote = novo
handoff, o anterior vai para `_archive/`. Ideia que surge no meio vai para a CAIXA DE IDEIAS (da para fazer? · quando? · o que resolve?).

## COMECE POR (proxima sessao) — C1 TRAVESSIA, item 3: title do material html = moodle_label no MANIFEST (medir antes; piso sem-llm do CG 5/15 le o manifest). Itens 1 e 2 FEITOS 05/09. **Gemini sem credito desde 05/09 00:45: so medicao sem LLM ate a recarga; a travessia pos-itens 1-3 roda quando houver credito, so no modo LLM.**
0. Confirme o estado: `git status --short` (so `.claude/settings.local.json` e `.codex/` podem aparecer), `git log --oneline -3`, HEAD dos 8
   tutores iguais aos de "Estado ao comecar" (CG agora e `2efddcb`), `python scripts/censo_motor_llm.py` (revisar/100 58,0). Suite 2312 (25 testes de scripts arquivados sairam com eles).
1. **11a FEITO** (`728c0f1`, §C0 ITEM 11a no tracker): `exclusivo` exige 2+ tokens; 1 token = banda media + flag. Copias: conf-err 3 -> 2,
   unidade 178 -> 179, resto igual; holdout puro conf-err 2 -> 0, curado 33 -> 35/35; originais reprocessados e commitados (8 HEADs abaixo);
   custo medido: votos/100 29,9 -> 36,5 (23 votos). Observar na C1: FR `udp-example-c/java` separados pelo voter (sem gold).
2. **11b FEITO** (`86dab7e`, §C0 ITEM 11b): voter ja votava so em flagada/serie/prazo/funil; serie confiante paga (17 votos evitam 1 conf-err,
   MF `exerciciosdafny2`) e fica; CRONOGRAMA_HEALTH ganhou "Votos de LLM" (36,5/100 = censo); ordem motor -> LLM -> card fica (199 -> 187
   medido 03/09); residual flagado AULA = 7,9/100 (gate <= 8 atendido). Regua por item = decisao sua (aberta).
3. **10 FEITO** (`4a14d8b`, §C0 ITEM 10): 10 dos 12 erros eram o mapa bloco->unidade da DP sem pinos; ancora lexical exclusiva (>= 2 tokens,
   token so da unidade) muda 3 blocos nos 8 (SO 20, CG 08, CG 13, todos confirmados) — unidade 179 -> 183/191, resto igual. Sem alavanca: SO
   bloco-06 (juizo humano), IA 01-02, SO sockets (bloco).
4. **9 FEITO** (`557be23` + `599ff10` + `1284b26`, §C0 ITEM 9): scripts/ 81 -> 37 (44 + artefato_razao arquivados com README e 4 testes), true_of
   subiu para eval_ground_truth, regua AULA sem escada stale (so "motor puro hoje"). src/ intocado; suite 2312; sentinela 0/8.
5. **12 FEITO (05/09; §C0 ITEM 12) — C0 FECHADA.** Travessia "depois": IA identico (0 chamadas), FR 15/15 (1 flip de bloco por label duplicado no
   cronograma), CG com LLM 7/15 = exatamente os alvos dentro do FILE_MAP (26/93; 8/8 erros fora do corte de 12 KB); bloco melhorou (8 -> 10/11).
   Nada regrediu pelo motor. Entradas da C1: FILE_MAP completo (clamp 12 -> 80 KB); linha com `moodle_label` (piso CG 10 -> 5 por `title` = nome
   de arquivo); label de bloco duplicado (FR bloco-06/20).
6. **C1 item 1 FEITO** (`0ff832a` + `4db9a6c` + `df0e34f` + `6afdcff`; §C1 ITEM 1): FILE_MAP completo (80 KB, aviso), TRACE separado, titulo = label,
   Secoes 3/80; 8 tutores reprocessados (manifest intocado); travessia: ver tabela no tracker.
7. **C1 item 2 FEITO** (`333d635`; §C1 ITEM 2): titulo de bloco repetido qualificado so em colisao (topic_text/sessao); CRONOGRAMA_DETALHADO fora do
   `if code_entries` (TCC e LR ganharam o artefato). Raiz do FR (aliases de camadas no topico) na caixa. Proximos: (3) title do material html
   = moodle_label no MANIFEST (piso sem-llm do CG 5/15 le o manifest) — medir antes; (4) indice por unidade/termos so se a regua mostrar erro
   dessa forma. Fronteira: triagem da CAIXA (C7 IMAGENS, posicao = decisao do user).
4. Gate de cada item: suite verde; sentinela 0 nos 8; determinismo 8/8; curada intacta; commit com o numero no tracker; tutores so
   mudam por reprocess registrado (copia `.ablacao` antes).

## Leis (inalteradas)
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · gold nao e oraculo (Moodle/SARC sao a verdade
estrutural) · nada regride em regua nenhuma · estrutura estreita, texto decide, estrutura NUNCA sobrepoe decisao confiante nem
preempta o voto do LLM · nada pushed sem o user · `.claude/settings.local.json` intocado · tokens (Moodle `moddle/.env`,
Datalab/Gemini `.env`) nunca impressos · [Humberto] · nao corrigir conteudo do professor em silencio (marcar para review).

## Estado ao comecar (04/09, tudo commitado, NADA pushed)
Gerador `feat/motor-atribuicao`, ~825 commits a frente de `main`. Sessao 5 (03-04/09): `6111b46` `0a8ae2e` `a10a6ca` `12990ed`
`5799035` `d7b2f87` `1d14353` `bff1fa4` + docs; noite: `728c0f1` (C0 11a), `86dab7e` (C0 11b), `4a14d8b` (C0 10), `557be23` `599ff10` `1284b26` (C0 9), `0ff832a` `4db9a6c` `df0e34f` `6afdcff` (C1 item 1). Suite 2319.
Tutores (reprocess C1 item 1, 05/09): MF `acbfdc2` · SO `7c91082` · IA `1c2869a` · ES2 `ac3862c` · TCC `6d04f4e` · LR `42cdb8a` · FR `ca7f9fd` · CG `0136790` (CG = `e3d02ed` rebuild pela API + complemento + reprocess 11a/11b/10/C1) (93 entries: 66 do build + 4 folhas + 23 referencias; stash novo `Desktop/Moodle/computacao-grafica/
stash/`, perfil ja aponta; export antigo em `.ablacao/CG-export-backup`). Copias `.ablacao` dos 5 + CG (re-sincronizada) + LR + FR.
**Reguas (pos-11a):** curada 199/200 conf-err 0 · 191/191 · 55/57 · motor puro +vocab 183/183/53/82 conf-err 2 · AULA 174/189 · REF 8/10 ·
holdout CG (gold re-chaveado `ground_truth_CG.csv`, 35 scorable) **puro 31/35 (conf-err 0, flagados 14) · curado 35/35 (conf-err 0, flagado 1)** · censo revisar/100 58,3 · votos/100
36,5 (348 materiais). Gold do CG anterior (export) em `_archive/ground_truth_CG.export.csv`.

## BALANCO em 04/09
- **SYNC — 6/6, FECHADA.** S1-S5 (03/09), S6a-S6f (03-04/09). S6f: rebuild do CG pela API promovido a original com holdout curado
  33/35 **aceito pelo user com causa medida** (o 34 do baseline dependia do token de boilerplate "imagens"; regra `exclusivo` por 1 token
  e o balde — C0 item 11a). Detalhe: `pendencias.md` §SYNC S6f e §SYNC S6a-S6e.
- **C0 MOTOR — 11/11, FECHADA em 05/09.** Feitos 2-7 (03/09), 11a `728c0f1`, 11b `86dab7e`, 10 `4a14d8b`, 9 `557be23`/`1284b26`, 12 (medicao; §C0 ITEM 12).
- **C1 TRAVESSIA — ABERTA em 05/09; item 1 FEITO.** FILE_MAP completo nos 8 (345/345 materiais; 3,7-21,8 KB); travessia: tabela no tracker §C1 ITEM 1.

## FILA DE CAMPANHAS (ordem decidida 03/09, atualizada 04/09)

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

### 1. ABERTA (05/09) — C1 TRAVESSIA (FILE_MAP completo e magro)
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
- Janela do card generico + token de ferramenta pela extensao (`.thy` isabelle, `.dfy` dafny): MF "Provas por Inducao" abrange 3 blocos (gold 8/4/7)
  mas o label casa 1 sessao e da janela-1 no bloco-05; 5 `.thy` sao do bloco-06 Isabelle. 3 conf-err do motor puro · desenho necessario · C0-2 · motor puro +3.
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
- **Push/merge em `main`:** ~825 commits verdes na branch; a fronteira SYNC -> C0 chegou. Proposta: merge/push agora.
- Revisao humana do CG novo: **formulas 37/37 APROVADAS pelo user (04/09)** (`s6f/formulas_index.md`; `Image2.gif` da Curvas mantem o erro
  do professor nos expoentes, fonte nao corrigida). Falta o veredito da fila `revisar_queue.md` (45) — nao trava o C0.
- Regua por item com vocab (campanha 5) · decisao B (campanha 4) · golds proposto-claude — revisao sua, quando quiser.

## NAO fazer (refutado no gold)
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
