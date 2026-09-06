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
Motor + voter com cache, sem pino, sem glossario manual, com vocab LLM (`_harness-2026-09-04/c1-3/motor_auto.py`): **bloco 192/199 = 96,5% conf-err 0 ·
unidade 185/191 = 96,9% · cobertura 53/57 · subunidade 82/93 = 88% · holdout CG 35/35**. Motor puro (sem voter) segue como regua de diagnostico; curada
(com pinos) e o produto de hoje, nao a meta. Pinos e glossario manual sao ANDAIME: cada um deve ter regra generica ou voto de LLM que o substitua,
medido nos 8 — ou fica registrado como residuo humano com nome. Golds novos so para MEDIR (CG/MF subunidade: aprovar uma vez, nunca curar por curso).
**Abaixo de 95% so a subunidade (vocabulario). Caminhos genericos:** vocab compilado melhor (LLM; hoje nao emite 'perceptron'/'MLP' para o IA) ·
propagacao por headings (+5/-0 no gold, valida com o gold CG/MF) · voto de LLM para unidade de bloco sem evidencia lexical (CG bloco-08; 1 chamada por bloco assim).

## COMECE POR (proxima sessao) — tres decisoes do user antes de qualquer codigo
0. Confirme o estado: `git status --short` (so `.claude/settings.local.json`, `.codex/` e `.mex/patterns/*` de outro agente), `git log --oneline -3`,
   HEAD dos 8 tutores = "Estado ao terminar", `python scripts/censo_motor_llm.py` (revisar/100 58,3 com 'mudou' 13; votos/100 35,9; FILE_MAP 100%
   nos 8, SO 38/39 por duplicata), `python -m pytest tests -q` (2325), `python scripts/sentinela_manifests.py` (0). Nada pushed.
1. **APROVAR os golds de subunidade propostos** (`docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md`, coluna `ok?`): CG 82 pontuaveis
   (produto acerta 49 com extras, 36 primario), MF 58 (51, 36); 4 rulings marcados (bundle misto pelo card; `exemplodemanipulacaodeimagens`
   label 'Classe Vetor' x conteudo; convencao Dafny = `softwares-de-suporte` com extra `verificacao-de-programas`; OpenGL = vazio). Aprovado:
   ligar `subunit_gt_{CG,MF}.csv` em `scripts/motor_puro.py` (`SUBUNIT_GOLD`) e REMEDIR a propagacao de vocabulario por headings nos 8
   (`c1-3/simula_propaga_headings*.py`: +5/-0 no gold de 93, mas MF 6 / CG 9 mudancas sem gold — o gold novo e o que decide).
2. **BUG dos zips do MF (SYNC/C5):** extracao sem subpasta colide `ex1.dfy` entre 5 zips (4 zips sem conteudo no tutor; 5 resumos de codigo errados)
   e `.smv` (NuSMV) e ignorado. Corrigir na extracao (`<id>/<membro>` + `.smv` como codigo), re-resumir quando o Gemini for liberado, reprocess do MF.
   Decisao de fila (C5 esta estacionada).
3. **Liberar ou nao o Gemini** para fechar a C1: travessia final IA/FR/CG modo LLM (~90 chamadas; alvo IA >= 14/15, FR 15/15, CG rerodado — ja medido
   apos o item 1: IA 14, FR 15, CG 10-11); depois, so se a travessia errar por indice: item 4 ou "FILE_MAP titulo = label · stem"; e o prompt do voter
   com `label do Moodle` (90/125 votados tem label != title; re-voto <= 90 chamadas). Sem Gemini a C1 nao tem item.
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
Gerador `feat/motor-atribuicao` @ `e0c433c` (codigo: higiene do glossario) + docs da sessao 6. Sessao 6 (05/09 tarde), commits: `d511357` `8d61d28`
`75b9955` `7a19208` `dc98c15` `ef4628c` `009b627` `d880f1b` `17afd2e` (docs/medicoes) · `e0c433c` (feat higiene + teste). Suite 2325.
Tutores: MF `afb83cb` · SO `0921948` · IA `d7d81ed` · ES2 `ba7d2c8` · TCC `13ced08` · LR `d139547` · FR `fd7814f` · **CG `2c5e01e`** (3 reprocess
registrados: `c566dc3` pinos de unidade 06/08/15, `ee4c276` sinonimo de morfologia — REVERTIDO em `2c5e01e`; 0 chamadas Gemini; votos 42 = 42).
Copias `.ablacao` dos 5 + CG + LR + FR (motor puro pos-higiene). `.ablacao/CG-rebuild` (365 MB) e `CG-export-backup` (440 MB): apagar e decisao do user.
**Reguas (gold pelo oraculo, 199 pontuaveis):** curada **198/199 conf-err 0** (falta ES2 `azure`) · unidade 191/191 · cobertura 55/57 · motor puro +vocab
**186/199 conf-err 1** · unidade 183/191 · cobertura 53/57 · sub 82/93 · holdout CG puro 31/35 conf-err 0 (flagados 14) · censo revisar/100 58,3
('mudou' 13 do reprocess do CG; era 57,8) · votos/100 35,9 · FILE_MAP 345/345 · **CG unidade: 22/93 erradas -> 1** (`texturas-v3`) + 2 por erro de bloco
(texturas no bloco-06, flagadas) · travessia pos-C1-item-1: IA 14/15 · FR 15/15 · CG 10/15 (11 completo) com LLM; sem-llm IA 10 · FR 9 · CG 5.
Golds propostos (NAO na regua): `subunit_gt_CG.csv` 82 pontuaveis · `subunit_gt_MF.csv` 58. **Regua automatica: bloco 192/199 · unidade 185/191 · sub 82/93 · holdout 35/35.** Determinismo pos-higiene **8/8, 0 arquivos nao deterministicos**; 0 resumos de codigo de hoje nos originais e nas copias.

## BALANCO da sessao 6 (05/09 tarde)
- **C1 item 3 (title := label): REFUTADO por medicao, 0 codigo.** Piso sem-llm 0 flip; motor puro bloco 186 -> 184, 2 confiantes viram flag (label
  "Respostas" apaga o assunto do nome do arquivo); stem e label sao complementares; o FILE_MAP ja mostra o label.
- **Subunidade sem LLM, medido e refutado:** card (nome 0/+ 23/-; irmao 0/+ 2/-) · IDF intra-unidade (V1 0/0, V2 +1/-5, V2s 0/0) · raiz dos 4 do IA =
  vocabulario do glossario MANUAL (camada humana). **Propagacao por headings: +5/-0 no gold, mas sem gold no CG/MF nao entra** (caixa; destrava com o
  gold aprovado).
- **CG unidade 22/93 -> 1:** raiz = vocab compilado por LLM com nomes de secao pendurados em topicos genericos de u01 + ordem do professor invertida
  (DP monotonica). Motor: 5 alavancas genericas medidas e refutadas (sem aliases 183 -> 136; radicais saldo 0; vizinho ancorado 183 -> 163; exclusividade
  relaxada 179; higiene sozinha neutra; radical so como fallback: +1 bloco, 0 colateral, unica unificacao que sobrevive, caixa). Solucao = higiene generica (codigo, `e0c433c`) + pinos de unidade nos blocos 06 (u04, nome do SARC), 08 (u03),
  15 (u07) — o mesmo mecanismo dos outros 7 tutores (13 pinos). Gates: motor puro 186/199 = · holdout 31/35 = · curada 198/199 = · sentinela 0 · suite 2325.
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
- **Propagacao de vocabulario por headings para a subunidade (sem LLM)** · +5/-0 no gold de 93 (conf >= 0,7, token em >= 2 confiantes, df <= 25%, so nos
  nao-confiantes), curada intacta; MF 6 / CG 9 mudancas sem gold com erros a olho · sim, ~40 linhas em `apply_unit_subunit_fields` · **depois do gold CG/MF aprovado**.
- **Voto de LLM para a UNIDADE de bloco sem evidencia lexical** (CG bloco-08 morfologia: plano nao menciona; unico caso nos 8) · 1 chamada por bloco assim · substitui o pino do bloco-08 · precisa de Gemini.
- **Radical (6 chars) so como fallback no mapa bloco->unidade** (tokens exatos decidem; sem ancora exata, ancora por radical exclusivo) · 1 bloco muda
  nos 8 (CG bloco-15 = pino), 0 colateral, unidade 183 = 183 · ~15 linhas em `assign_units_positional` · ganho hoje 0 (pino), valor = proximo curso sem pino · C4/C5.
- **Prompt do voter sem o `moodle_label`** (`llm_vote.py:241`; 90/125 votados tem label != title) · 1 linha + re-voto <= 90 chamadas · C1 fechamento (LLM).
- **FILE_MAP titulo = label perde o stem** (103 linhas; 7 labels sem conteudo) · "label · stem" quando o title tem token que o label nao tem · C1 item 4, so se a travessia errar.
- **Zips extraidos sem subpasta colidem nomes** (MF 5 zips x `ex1.dfy`; `.smv` ignorado) · `<id>/<membro>` + `.smv` como codigo · SYNC/C5.
- **GLOSSARY.md para no ultimo termo que o parser do plano entende** (CG: 7.1.2; u08/u09 sem termo) · investigar o parser do plano do CG · C5 · sinonimo manual para texturas.
- **Gold de unidade do CG** (22 erros vieram a luz pelo gold de subunidade) · proposto-claude a partir de `2026-09-05-cg-atribuicoes.md` · C5.
- Custo do Gemini (Datalab para imagens, Gemini so fallback; medir chamadas por funcao) · C7/C3. Tempo de reprocess (CG 111 s, 83% em `normalize_match_text`
  sem cache) · C4. Data de entrega (`duedate`) dos trabalhos pela API · SYNC/C3. Conferencia das 37 formulas do CG por LLM · C3. Reprocess registrado
  commita so `updated_at` · C4. Apagar `.ablacao/CG-*` (805 MB) · agora, decisao do user. Merge/push dos ~840 commits em `main` · fronteira.

## Decisoes ABERTAS do user (nao travam a campanha 1)
- Aprovar os golds de subunidade CG/MF (COMECE POR 1). Corrigir a extracao dos zips (2). Gemini (3). Religar `gemini_auto_summarize` so com o Gemini liberado.
- Apagar `.ablacao/CG-rebuild` e `CG-export-backup`. Posicao da C7 IMAGENS. Push/merge em `main`. Revisao da fila `revisar_queue.md` (45) do CG.

## NAO fazer (refutado no gold)
**05/09 tarde (sessao 6):** `title` do manifest := `moodle_label` (piso 0; bloco 186 -> 184; 2 confiantes viram flag) · subunidade de codigo pelo card (nome 0/+
23/-; irmao 0/+ 2/-) · IDF intra-unidade no scorer de subtopico (V1 0/0, V2 +1/-5, V2s 0/0) · mapa bloco->unidade sem aliases (183 -> 136) · radicais nos
tokens do mapa (saldo 0: 'proces~processamento') · preenchimento pelo vizinho ancorado no lugar da DP (183 -> 163) · exclusividade relaxada da ancora
(179) · sinonimo manual que renomeia bloco ('Morfologia' em Segmentacao: 4 materiais mudaram de bloco).
**05/09 madrugada:** peso do label no desempate x2/x3 (50 -> 47/48) · janela do card = secao (72 -> 56; janela-1 21 -> 15) · data de postagem como decisor
(33/52) · "revisao" fora dos genericos (50 -> 50) · H9 sobre confiante (saldo 0). **Anteriores:** serie k -> k-esimo bloco · serie monotonica · prova antiga
-> prep · H7 ordem das secoes · H6 label unico · label em decisao confiante · card ANTES do voter · regex de nome para card generico · imprimir HTML em PDF
para o Datalab · rastrear `Aulas/` do site do professor · `unit_block_conflict` como alavanca de banda.

## Ferramentas
`scripts/` (37): `sync_moodle.py` · `motor_puro.py [--com-vocab]` · `censo_motor_llm.py` · `sentinela_manifests.py` · `eval_eixos.py` · `reprocess_assignments.py` ·
`moodle_pull.py` · `eval_travessia.py` · `_harness-2026-09-02/{regua_aula,holdout_cg,calibra_revisar,mede_alavancas,determinismo}.py`.
**Sessao 6 (`_harness-2026-09-04/c1-3/`, README la):** `shim_b.py` (tripwire para copias) · `check_gemini_hoje.py` · `snapshot.py`/`diff_b.py` · `medicao_a_piso.py` ·
`leitores_title.py` · `simula_sub_card.py` · `simula_idf_sub.py` · `simula_propaga_headings{,_weak,_semgold}.py` · `simula_unidade_sem_alias.py` ·
`simula_raiz_unidade.py` · `gera_gold_subunidade.py` · `reprocess_cg_unidade.py` (tripwire de produto) · `determinismo_tripwire.py`.
Relatorio das atribuicoes do CG: `docs/reports/2026-09-05-cg-atribuicoes.md`. Padrao: `.mex/patterns/medir-alavanca-ablacao.md`.
