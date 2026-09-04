# Handoff 2026-09-04 — PONTO DE ENTRADA: a FILA de campanhas (C0 aberta, C1 proxima, o resto estacionado)

Unico handoff vivo. Substitui `_archive/2026-09-03b-handoff-fila-campanhas.md` (SYNC FECHADA em 04/09). **Leia nesta ordem:**
(1) este arquivo; (2) `pendencias.md` §GATE DA FASE 3, §HOLDOUT e §SYNC S6f (numeros); (3) `.mex/context/decisions.md` (decisoes de
03-04/09). Rode `mem-search` para as sessoes de 03-04/09.

**Regra de fila (user, 03/09):** UMA campanha aberta, UMA proxima, o resto ESTACIONADO. **Campanha so fecha com 100% dos itens**
(criterio estrito); item nao feito nao muda de dono sozinho — ou e feito, ou o user o RETIRA por decisao registrada. Novo lote = novo
handoff, o anterior vai para `_archive/`. Ideia que surge no meio vai para a CAIXA DE IDEIAS (da para fazer? · quando? · o que resolve?).

## COMECE POR (proxima sessao) — C0 item 11a: calibracao da regra `exclusivo` do disambiguator (TDD + medida antes de entrar)
0. Confirme o estado: `git status --short` (so `.claude/settings.local.json` e `.codex/` podem aparecer), `git log --oneline -3`, HEAD dos 8
   tutores iguais aos de "Estado ao comecar" (CG agora e `e3d02ed`), `python scripts/censo_motor_llm.py` (revisar/100 54,0). Suite 2332.
1. **11a**: em `routing/motor/disambiguator.py::_lexical_decision`, `exclusivo` (s1>0, s2=0) com UM token de contato deixa de ser alta:
   banda media + flag (voter e card agem). Teste RED com os 5 casos errados do dado (MF `terminacao`, ES2 `azure`, CG `matematica`,
   CG `transformacoesgl`) e os 17 certos (nao podem mudar de bloco). Regua: `motor_puro.py --com-vocab` (baseline 183/178/53/82,
   conf-err 3), `eval_eixos.py` (curada 199/200 · 191/191 · 55/57), `_harness-2026-09-02/regua_aula.py` (AULA 174/189), `holdout_cg.py
   <GEN> <GEN>/.ablacao` puro (baseline 31/35 (conf-err 2, flagados 9)) e `--curado` (33/35 (conf-err 2, flagados 1)). Custo declarado: votos/100 sobe (~22 votos a mais nos 6 cursos).
2. **11b**: LLM so nos flagados, cacheado, contado no CRONOGRAMA_HEALTH; ordem motor <-> LLM <-> card com numero. Gate: residual flagado
   em AULA <= 8/100 (hoje 18,5).
3. Depois: 10 (medir os 13 erros de unidade antes de codigo), 9 (refactor corte 1, byte-identico), 12 (travessia "depois").
4. Gate de cada item: suite verde; sentinela 0 nos 8; determinismo 8/8; curada intacta; commit com o numero no tracker; tutores so
   mudam por reprocess registrado (copia `.ablacao` antes).

## Leis (inalteradas)
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · gold nao e oraculo (Moodle/SARC sao a verdade
estrutural) · nada regride em regua nenhuma · estrutura estreita, texto decide, estrutura NUNCA sobrepoe decisao confiante nem
preempta o voto do LLM · nada pushed sem o user · `.claude/settings.local.json` intocado · tokens (Moodle `moddle/.env`,
Datalab/Gemini `.env`) nunca impressos · [Humberto] · nao corrigir conteudo do professor em silencio (marcar para review).

## Estado ao comecar (04/09, tudo commitado, NADA pushed)
Gerador `feat/motor-atribuicao`, ~825 commits a frente de `main`. Sessao 5 (03-04/09): `6111b46` `0a8ae2e` `a10a6ca` `12990ed`
`5799035` `d7b2f87` `1d14353` `bff1fa4` + docs. Suite 2332.
Tutores: MF `e39e14a` · SO `603d914` · IA `ca1f765` · ES2 `2212f9f` · TCC `b9af3c3` (encerrados) · LR `040b2dd` · FR `89db35d` ·
**CG `e3d02ed` = rebuild limpo pela API + complemento** (93 entries: 66 do build + 4 folhas + 23 referencias; stash novo `Desktop/Moodle/computacao-grafica/
stash/`, perfil ja aponta; export antigo em `.ablacao/CG-export-backup`). Copias `.ablacao` dos 5 + CG (re-sincronizada) + LR + FR.
**Reguas:** curada 199/200 conf-err 0 · 191/191 · 55/57 · motor puro +vocab 183/178/53/82 · AULA 174/189 (residual flagado 18,5/100) ·
holdout CG (gold re-chaveado `ground_truth_CG.csv`, 35 scorable) **puro 31/35 (conf-err 2, flagados 9) · curado 33/35 (conf-err 2, flagados 1)** · censo revisar/100 54,0 · votos/100
29,9 (348 materiais). Gold do CG anterior (export) em `_archive/ground_truth_CG.export.csv`.

## BALANCO em 04/09
- **SYNC — 6/6, FECHADA.** S1-S5 (03/09), S6a-S6f (03-04/09). S6f: rebuild do CG pela API promovido a original com holdout curado
  33/35 **aceito pelo user com causa medida** (o 34 do baseline dependia do token de boilerplate "imagens"; regra `exclusivo` por 1 token
  e o balde — C0 item 11a). Detalhe: `pendencias.md` §SYNC S6f e §SYNC S6a-S6e.
- **C0 MOTOR — 6/11, ABERTA.** Feitos 2-7; faltam 9, 10, 11, 12 (ordem proposta 11 -> 10 -> 9 -> 12).

## FILA DE CAMPANHAS (ordem decidida 03/09, atualizada 04/09)

### 1. ABERTA — C0 MOTOR, itens 9-12 (o que falta para fechar a rodada do motor)
9. Refactor corte 1: `scripts/` 79 -> ~25 (harnesses que viraram rotina sobem, o resto arquiva); podar a escada stale da
   `regua_aula.py` (picks H9/H7). Gate: byte-identico (determinismo, sentinela 0, suite).
10. Fase 2 unidade: ANTES de codigo, medir o que a estrutura nao resolveu na unidade (motor+vocab 178/191: 13 erros, quais e por
   que). Se a medicao nao der alavanca com numero, o user retira o item.
11. Fase 4: LLM so nos flagados, cacheado, contado no CRONOGRAMA_HEALTH; decidir a ordem motor <-> LLM (hoje o card so age depois
   do voter) e a regua por item (com vocab + curada + holdout; ablacao so em gate). Gate: residual flagado em AULA <= 8/100.
   **11a (primeiro, medido 04/09 em `_harness-2026-09-03/s6f/mede_exclusivo.py`):** regra `exclusivo` do disamb (s2=0 -> alta) com UM
   token: 22 decisoes nos 6 golds, 5 erradas (77%; 2+ tokens e margem dao 94%) -> 1 token vira banda media + flag; medir motor_puro
   +vocab, eval_eixos, regua_aula, holdout CG (gold re-chaveado). Entra so se conf-err cai sem AULA/curada regredir.
12. Travessia "depois": rerodar `eval_travessia.py {IA,FR,CG}` e comparar com o "antes" (tracker, REGUA DE TRAVESSIA).
**C0 fecha quando:** 9-12 feitos ou retirados pelo user, com numero no tracker.

### 2. PROXIMA — C1 TRAVESSIA (FILE_MAP completo e magro)
Unico item com numero de PRODUTO grande ja medido: IA 9 -> 14/15 com o indice completo (o corte de 12 KB esconde 40/59 materiais).
Itens: rastreabilidade (`FILE_MAP_TRACE.md`), coluna "Secoes" limitada, clamp 80 KB + aviso; indice por unidade/termos so se a
regua pos-C1 mostrar erro dessa forma. `python scripts/eval_travessia.py {IA,FR,CG} [--sem-llm|--contexto-completo]`.
**Pronto quando:** IA >= 14/15, FR 15/15, CG rerodado, sentinela 0 no motor. 1 sessao.

### 3. ESTACIONADA — C3 PROVAS, LISTAS E TRABALHOS (antes de C2, ordem do user)
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
`scripts/sync_moodle.py` · `scripts/motor_puro.py [--com-vocab]` · `scripts/censo_motor_llm.py` · `scripts/sentinela_manifests.py` ·
`scripts/eval_eixos.py` · `scripts/reprocess_assignments.py` · `scripts/moodle_pull.py --course N --root R [--dry-run|--pdf]` ·
`scripts/eval_travessia.py` · `_harness-2026-09-02/{regua_aula,holdout_cg,calibra_revisar,mede_alavancas,determinismo}.py` ·
pulls reais em `_harness-2026-09-03/pulls/{FR,LR,CG}/` · piloto Curvas versionado em `_harness-2026-09-03/piloto-curvas/` (Curvas.htm, 27 imagens, gold Datalab, `gate_s6b_curvas.py` = Curvas de ponta a ponta numa copia do CG, `Curvas.s6b.md` = saida do S6b).
