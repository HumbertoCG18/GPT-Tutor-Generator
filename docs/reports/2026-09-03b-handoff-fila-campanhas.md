# Handoff 2026-09-03b — PONTO DE ENTRADA: a FILA de campanhas (uma aberta, uma proxima, o resto estacionado)

Unico handoff vivo. Substitui `_archive/2026-09-03-handoff-sync.md` (SYNC: 5/6 feitos, continua ABERTA aqui) e `_archive/2026-09-02c-handoff-fase3-medida.md`
(C0 motor: 6/11 feitos, e a PROXIMA aqui). **Leia nesta ordem:** (1) este arquivo; (2) `pendencias.md` §GATE DA FASE 3 e §HOLDOUT (numeros);
(3) `.mex/context/decisions.md` (decisoes de 03/09). Rode `mem-search` para as sessoes de 03/09.

**Regra de fila (user, 03/09, contra o acumulo de frentes):** UMA campanha aberta, UMA proxima, o resto ESTACIONADO. **Campanha
so fecha quando 100% dos itens dela foram feitos** (criterio estrito, user 03/09 tarde): item nao feito nao "muda de dono" por
conta propria — ou e feito, ou o user o RETIRA da campanha por decisao explicita registrada aqui. Novo lote = novo handoff, o
anterior vai para `_archive/`. Tracker registra numero e commit de cada item.
**Caixa de IDEIAS (secao no fim):** o que surge no meio do caminho ("da para fazer X?") NAO entra na campanha aberta: vai para a
caixa com 3 campos — da para fazer? · quando (qual campanha)? · o que resolve no sistema? — e e triado so na fronteira entre campanhas.

## Leis (inalteradas)
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · gold nao e oraculo (Moodle/SARC sao a verdade
estrutural) · nada regride em regua nenhuma · estrutura estreita, texto decide, estrutura NUNCA sobrepoe decisao confiante nem
preempta o voto do LLM · nada pushed sem o user · `.claude/settings.local.json` intocado · tokens (Moodle `moddle/.env`,
Datalab/Gemini `.env`) nunca impressos · [Humberto] · nao corrigir conteudo do professor em silencio (marcar para review).

## Estado ao comecar (dados de 03/09, tudo commitado, NADA pushed)
Gerador `feat/motor-atribuicao`, **805 commits a frente de `main`** (4 atras). Rodada do motor: `fe2c4fb` `b802a68` `79fc92a` `fdf28af`
`b1d565a` `a1bcc25`; SYNC: `2491596` `619488c` `91867b7` `e593ee7` + docs. Suite 2298.
Tutores: MF `e39e14a` · SO `603d914` · IA `ca1f765` · ES2 `2212f9f` · TCC `b9af3c3` (encerrados, estrutura do Moodle no manifest) ·
LR `040b2dd` (sincronizado: Lab 4 entrou) · FR `89db35d` (sincronizado: 2 videos como referencia) · CG `19472d1` (EXPORT; e o
alvo da campanha aberta). Copias `.ablacao` dos 5 + CG + LR + FR.
**Reguas (5 golds):** curada 199/200 conf-err 0 · 191/191 · 55/57 · 93/93 · motor+vocab 183/178/53/82 · motor sem vocab 184/168/54/30 ·
AULA 174/189 (175 sem vocab) · REF 8/10 · holdout CG puro 30/35, curado 34/35 · censo revisar/100 51,7 · votos/100 32,0 ·
`subunit_gt_FR` 14/18. Residual flagado em AULA 18,5/100 (meta <= 8 nao batida; balde de "LLM no residuo").

## BALANCO em 03/09 (criterio estrito: nada fechou; o que foi feito e o que falta, por campanha)
- **C0 MOTOR — 6/11 feitos, ABERTA.** Feitos: 2 (3a estrutura no manifest), 3 (3b card ordenado, so depois do voter), 4 (secao 0 ->
  apresentacao; ordem das secoes nao entrou, 0/0), 5 (3c tokens curtos + tokenizador unico), 6 (nao entra, medido 0/0), 7 (gate
  registrado: motor puro 161 -> 184, AULA 152 -> 174, curada intacta, holdout 27 -> 30; meta residual <= 8/100 NAO batida, 18,5).
  Faltam: 9 (refactor corte 1: `scripts/` 79 -> ~25 + podar a escada stale da `regua_aula.py`), 10 (Fase 2 unidade — SEM numero
  medido; fazer a medicao ou o user retira), 11 (Fase 4: LLM so nos flagados, contado — e o balde do residual 18,5), 12 (travessia
  "depois" = rerodar o item 1 e comparar).
- **SYNC — 5/6 feitos, ABERTA.** Feitos: S1 diff, S2 import do delta, S3 regeneracao + diff de decisoes + `mudou` + SYNC_REPORT,
  S4 LR sincronizado (Lab 4), S5 FR controle (2 videos). Falta: S6 (CG rebuild pela API), que DEPENDE de tratar HTML como
  material — por isso a "PAGINAS+CG" nao e campanha: e a sub-etapa S6a-S6f dentro da SYNC (abaixo).

## FILA DE CAMPANHAS (ordem decidida 03/09)

### 1. ABERTA — SYNC, item S6: CG pela API, com HTML como material (sub-etapas S6a-S6f)
Por que: o CG e o unico tutor ainda vindo do EXPORT (37/69 arquivos sem par por nome; 30 paginas HTML do Moodle e do site do
professor; formulas em GIF). Piloto Curvas (03/09): 24 imagens -> Datalab cru a 1 centavo cada; 12 formulas em LaTeX fieis
(conferidas contra o GIF; `Image2.gif` tem erro do PROFESSOR — expoentes da derivada), 9 figuras com legenda em ingles, 3 GIFs sem
texto voltam vazios. GIF cru funciona (sem PNG/upscale). Decisoes do user: legendas traduzidas pelo Gemini; vazias descritas pelo
Gemini; formula -> bloco `$$...$$` + `<sub>fonte: [x.gif](images/x.gif)</sub>`; snapshots do site entram como material; `.xlsx` (2)
ficam ignorados e listados; **toda formula transcrita vai para `manual-review/formulas/` para o user conferir com o professor**.
- S6a (=H1). Conversor `text/url_markdown.py`: refs `![alt](src)` inline e em bloco (FEITO 03/09, `src` sem aspas coberto); teto de 15 000
  chars vira parametro (arquivo local sem teto).
- S6b (=H2). Tipo `html`/`htm` em `stash_import._classify_file_type` + `_process_html` (HTML salvo -> conversor -> `base_markdown`); imagens
  da pagina: logos deduplicados por md5 e descartados; cada imagem -> Datalab CRU com cache por md5 e cap por build (400);
  `$$` -> bloco + fonte; legenda -> Gemini PT-BR -> `![Figura: ...](images/x.gif)`; vazia -> Gemini descreve; falha -> `![x.gif — nao
  capturada](images/x.gif)`; imagens copiadas para `content/images/`.
- S6c (=H3). `manual-review/formulas/<id>.md`: cada formula (LaTeX + link da imagem-fonte + caixa "conferir com o professor") e as nao
  capturadas; indice no `SYNC_REPORT`. Sem detector de erro: a lista e para o user.
- S6d (=H4). Pull: paginas do Moodle e snapshots do site entram no stash como `.html` (nao impressos); indices de video idem, categoria
  `references`; snapshot segue so links na SUBARVORE da pagina (hoje `same_site` = mesmo host: vazaria `Aulas/` e outras cadeiras).
- S6e (=H5). Fixtures: `Curvas.htm` real + cache do piloto como gold (12 formulas); clientes Datalab/Gemini falsos nos testes; suite verde.
- S6f. CG = primeira sync como REBUILD LIMPO pela API: Datalab so nos 21 PDFs reais + ~250 imagens (~US$ 3); Gemini nos 18 codigos +
  traducoes; zero curadoria, summaries ON, vocab, voter com cap; `ground_truth_CG.csv` re-chaveado por `true_block_uuid`; copia
  antes do original. "Em duvida 28/08" e "modals" triados aqui.
**SYNC fecha quando:** CG sincronizado com paginas como markdown; holdout CG re-chaveado >= 30/35 puro e 34/35 curado; curada dos 5
intacta; sentinela 0; determinismo; user revisou a fila `revisar` e a lista de formulas. Estimativa: 2 sessoes.

### 2. PROXIMA — C0 MOTOR, itens 9-12 (o que falta para fechar a rodada do motor)
9. Refactor corte 1: `scripts/` 79 -> ~25 (harnesses que viraram rotina sobem, o resto arquiva); podar a escada stale da
   `regua_aula.py` (picks H9/H7). Gate: byte-identico (determinismo, sentinela 0, suite).
10. Fase 2 unidade: ANTES de codigo, medir o que a estrutura nao resolveu na unidade (motor+vocab 178/191: 13 erros, quais e por
   que). Se a medicao nao der alavanca com numero, o user retira o item.
11. Fase 4: LLM so nos flagados, cacheado, contado no CRONOGRAMA_HEALTH; decidir a ordem motor <-> LLM (hoje o card so age depois
   do voter) e a regua por item (com vocab + curada + holdout; ablacao so em gate). Gate: residual flagado em AULA <= 8/100.
12. Travessia "depois": rerodar `eval_travessia.py {IA,FR,CG}` e comparar com o "antes" (tracker, REGUA DE TRAVESSIA).
**C0 fecha quando:** 9-12 feitos ou retirados pelo user, com numero no tracker.

### 3. ESTACIONADA — C1 TRAVESSIA (FILE_MAP completo e magro)
Unico item com numero de PRODUTO grande ja medido: IA 9 -> 14/15 com o indice completo (o corte de 12 KB esconde 40/59 materiais).
Itens: rastreabilidade (`FILE_MAP_TRACE.md`), coluna "Secoes" limitada, clamp 80 KB + aviso; indice por unidade/termos so se a
regua pos-C1 mostrar erro dessa forma. `python scripts/eval_travessia.py {IA,FR,CG} [--sem-llm|--contexto-completo]`.
**Pronto quando:** IA >= 14/15, FR 15/15, CG rerodado, sentinela 0 no motor. 1 sessao.

### 4. ESTACIONADA — C3 PROVAS, LISTAS, TRABALHOS E IMAGENS (antes de C2, ordem do user)
Granularidade da cobertura (prova inteira x questao a questao — decisao aberta desde 18/08), P2b-LLM (extracao de questoes,
cacheado, contado), EXAM_INDEX "incidencia por topico" honesto, imagens do Datalab consumidas pelo tutor, triagem "em duvida
28/08" (PS/G2 como principais, cadeira sem prova, `U1 - ...`/"Laboratorio N"). **Pronto quando:** gold de ~10 provas + ~10
imagens medido e curada intacta.

### 5. ESTACIONADA — C2 REFERENCIAS E BIBLIOGRAFIA (por ultimo, ordem do user)
Decisao B (eth2/aws {u02} ou N:N); vetar `coverage_gt_{SO,MF,IA}.csv` (9/10, baseline 0/9); pino de cobertura 57/57 ou 55/57
documentado; consumo de bibliografia (decisao 22/07 "caso a parte"); os videos do FR e 23 links do CG (hoje llm-funil/duvida).
**Pronto quando:** regua de referencias sobe de 0/9 e cobertura curada nao cai.

### 6. ESTACIONADA — C4 LIMPA PRE-WEB (byte-identico)
Cortes 2 e 4, 13 tokenizadores -> `text/tokens.py`,
17 limiares -> `thresholds.py`, `concept_resolver` so apos medir os 8 consumidores, CODE_INDEX "sem aula atribuida" (decisao H),
`auditoria-enxame`. **Pronto quando:** determinismo 0, sentinela 0 total, ablacao identica, suite verde — zero mudanca de numero.

### 7. ESTACIONADA — C5 DIVIDAS DE DADOS (dependem do user; paralelizavel)
Lab SO (SARC da turma 310), GAP VIDEO do T2, 10 suspeitos do `detecta_headings`, `content/` sem markdown de material no LR
(consolidacao e etapa da UI). **Pronto quando:** cada item tem gold proprio ou ruling.

### 8. ESTACIONADA — C6 WEB
Backlog vivo em `pendencias.md` §CAMPANHA FUTURA; `graph.json` derivado como modelo de dados. Depois de C4.

## CAIXA DE IDEIAS (fora da campanha aberta; triagem so na fronteira)
Formato: **ideia** · da para fazer? · quando (campanha)? · o que resolve no sistema?
- Watchdog de formula transcrita x texto ao redor (erro do professor vs OCR) · sim, heuristica fraca · C3 · so listaria suspeitas; a
  lista de formulas para review (S6c) ja da o caminho humano.
- Regua por item so com vocab (ablacao sem vocab em gate de fase) · sim, 1 flag · C0 item 11 · corta 2,5 min por item.
- Merge/push dos 805 commits em `main` · sim · fronteira SYNC -> C0 · tira o risco de branch longa.

## Decisoes ABERTAS do user (nao travam a campanha 1)
- **Push/merge em `main`:** 805 commits verdes na branch. Proposta: merge ao fechar a campanha 1.
- Regua por item com vocab (campanha 5) · decisao B (campanha 4) · golds proposto-claude (`travessia_gt_*`, `subunit_gt_FR`,
  `ground_truth_CG`) — revisao sua, quando quiser.

## NAO fazer (refutado no gold)
Serie k -> k-esimo bloco · serie monotonica (+1/-2) · prova antiga -> prep (0) · H7 ordem das secoes pos-item 3 (0/0) · H6 label
unico (0/0) · label em decisao confiante · card ANTES do voter · regex de nome para card generico (secao 0 e o sinal) · imprimir
pagina HTML em PDF para o Datalab (texto ja e texto; so as imagens vao ao Datalab) · rastrear o indice `Aulas/` do site do
professor (entra so o que um card do Moodle aponta).

## Ferramentas
`scripts/sync_moodle.py` · `scripts/motor_puro.py [--com-vocab]` · `scripts/censo_motor_llm.py` · `scripts/sentinela_manifests.py` ·
`scripts/eval_eixos.py` · `scripts/reprocess_assignments.py` · `scripts/moodle_pull.py --course N --root R [--dry-run|--pdf]` ·
`scripts/eval_travessia.py` · `_harness-2026-09-02/{regua_aula,holdout_cg,calibra_revisar,mede_alavancas,determinismo}.py` ·
pulls reais em `_harness-2026-09-03/pulls/{FR,LR,CG}/` · piloto Curvas no scratchpad de 03/09 (cache Datalab com as 12 formulas).
