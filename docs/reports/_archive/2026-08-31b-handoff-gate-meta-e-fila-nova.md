# Handoff 2026-08-31b — Gate de meta na subunidade e a fila nova

**Para a proxima sessao. Comecar pelo item (a); fila (a)-(g) na ordem. Nada aqui esta bloqueado**
(unico bloqueio do mapa segue sendo Lab SO <- SARC da turma 310, e e so do P3).
Leia antes: `docs/reports/pendencias.md` — secao "PENDENTE DE VERDADE (2026-08-31)" e o cabecalho ESTADO
(as-of 2026-08-31c).

## Leis da campanha (inalteradas)
Dado real antes de codigo · raiz nunca remendo · tudo pelo motor, LLM = fallback · sem regra por categoria ·
sem regra por CURSO · pinar menos · **gate entre passos**: `eval_eixos.py` (4 eixos) + `pytest -q` +
sentinela campo a campo vs `git show HEAD:manifest.json` + determinismo (2 reprocess = 0 campos em 6/6) +
`ablacao_rapida.py` nu e `--curado` · nada avanca com regua pior em QUALQUER eixo · restaurou tutor por git ->
reprocessa (derivados fora do git) · commits com trailers Co-Authored-By + Claude-Session · respostas em
portugues comecando com [Humberto].

## Estado que esta sessao deixou (2026-08-31c, tudo verificado)
- Regua curada: bloco **199/200 conf-err 0** · unidade **191/191** · cobertura **56/57 F1 0,982** ·
  subunidade **89/93** · pinos 5 · card manual 1 (TCC "Semana 12") · suite **2138**.
- Motor nu (ablacao 31/08): bloco 194/200 conf-err 2 · unidade **170/191 (89%)** — era 134, +36 pelo DP com
  desvio de janela · cobertura 54/57 F1 0,947 (trade honesto documentado no ESTADO) · pinos 0.
- Gerador `9154868`; tutores todos 0/0 com remote: MF `0850653` · TCC · IA `906e0c2` · SO · ES2 · CG
  (fase4 + duplicatas commitadas em todos).
- 6 entries `duplicate_of` (SO plano=programa; TCC 3dm e prog-inteira; CG 3 pares): confirmadas por sha256
  (3 bit a bit) e PDF-TEXTO por pagina (3 so metadados), rastreadas ao Moodle (repostagem do professor,
  ids de download distintos), conferidas NO OLHO pelo user. Secundarias fora dos indices; motor/golds
  intactos. Copias em `Desktop/duplicatas-tutores/` (descartavel).

## EXECUTADO nesta sessao (nao refazer)
P1 cobertura 55->56/57 (rota de texto p/ github-repo; aws = teto de dado) · P2a DP com desvio de janela
(IA nu 3->39/42; bonus CG bloco-5 u02->u04 confirmado pelos titulos) · P2b deterministico (EXERCISE/EXAM
INDEX: unidade real, pareamento gabarito, dedup; ruling: questoes por LLM = item futuro) · P2c (sessao
anterior) · P2d (P4 no stem6 compartilhado; disambiguator prefixo-8 e due_window ficam DE PROPOSITO) ·
P2f (glossario IA "analise exploratoria" -> subunidade 87->89/93; 3 familias diagnosticadas) ·
detector de duplicatas (4 niveis) + remedio duplicate_of.

## REFUTADOS nesta sessao (nao retentar sem dado novo)
- `ref_summary` concatenado ao texto de cobertura: aws vai a u03, eth2 cai 0,938->0,726.
- Piso global 8.0 no heading->alias da taxonomia: 729 campos em 5 cursos — a rota de overlap fraco e
  LOAD-BEARING (sustenta dezenas de aliases legitimos). Fix precisa ser cirurgico e MEDIDO.
- (Sessoes anteriores, seguem valendo: alias Cook-Levin TCC; stem6 global; fallback-cobertura=bloco.)

## FILA NOVA (ordem recomendada; a-g)
a) **Gate de meta/abrangente na SUBUNIDADE** (comecar aqui). Espelho da regra A da cobertura
   (META_CATEGORIES), que a subunidade nunca ganhou. Fecha: TCC `aula-06` (revisao multi-assunto, gold
   VAZIO, motor atribui argumento-diagonal conf 3.24 => regua 89->90/93) e SO `plano-de-ensino`/`programa`
   (subunit indevida `evolucao-historica`; golds ja estao `scorable=no` "cronograma transversal" desde
   25/08 => ganho de honestidade no manifest, SEM efeito na regua). ARMADILHAS ja mapeadas: (i) categoria
   nao basta — plano/programa sao o MESMO arquivo com categorias "cronograma" e "outros"; precisa sinal de
   conteudo (EMENTA no texto, titulo) ou nome; (ii) "revisao" da aula-06 TCC: cuidado para nao esvaziar
   subunit de aulas de revisao LEGITIMAMENTE mono-assunto (medir; so a regua diz). Gate completo.
b) **Detector de headings vira script de auditoria** (`scripts/`): regra "heading interno nomeia subunit
   irma != atribuida E a atribuida nao aparece em heading nenhum" — achou SO plano/programa e ES2 devops
   em segundos, sem LLM. Calibrar matching label<->heading nos DOIS sentidos (caso `devops`: heading
   "DevOps" mais curto que o label "Conceito de DevOps" nao casou). Rodar pos-reprocess, como o
   detecta_duplicatas.
c) **Filtro de imagens orfas no texto do scorer**: `_entry_markdown_text_for_file_map` le o .md inteiro;
   bloco `IMAGE_DESCRIPTION_ORPHANS` do TCC trabalho-t2 tem 17 descricoes de OUTRO material (DFA/PDA/
   Chomsky/brasoes USP). Cortar o bloco do TEXTO DO SCORER (nao do arquivo). Medir com a regua.
d) **Familia B cirurgica** (ES2 `web` 8.65x8.31 via alias podre "ARQUITETURA DE SISTEMAS WEB" em
   serverless): so com desenho fino (ex.: exigir contencao apenas p/ heading multi-tema com overlap de
   1 token) e medicao; o piso global ja foi refutado.
e) **P2b-LLM**: extracao de questoes de provas antigas (ruling do user 31/08: "deterministico agora, LLM
   depois"). Habilita incidencia por topico no EXAM_INDEX.
f) **Higiene import github-repo**: clone OK sobrescreve `category` da entry via STUDENT_BRANCHES
   (master/main => codigo-aluno — bibliografia viraria codigo) e importa o repo inteiro; pins `tags=main`
   errados de eth2/aws MANTIDOS de proposito ate este fix (clone falha inofensivo; texto ja vem da pagina).
g) **Decisoes antigas em aberto** (topo do tracker): `U<n>` no card como sinal de 1a classe (medir quando
   o Fund. Redes buildar) · `moodle_pull` gravar `summary` de secao (formula do G1 de SO/Lab SO mora la) ·
   `build_course --syllabus-url` (aposentar o caminho PDF do SARC).
- **GAP VIDEO** (achado do user 31/08): apresentacoes T2 = slides de explicacao em video (PDF tem ate
  screenshot de player). Registrado como limite do material ingerido; NAO iniciar sem decisao do user.
- **Familia C** (proposito vs vocabulario: ES2 roteiro5 19.3x16.4, TCC aula-08 35x4.6 — gold ja correto e
  confirmado por cronologia): teto do motor lexical, so com sinal de outro tipo. Revisitavel.

## P3 — Builds pagos (fora deste handoff; quando o user autorizar)
Inalterado desde o handoff anterior: Lab Redes PRONTO -> Fund. Redes PRONTO -> Lab SO **BLOQUEADO** (SARC
da turma 310; o link do Moodle e da 330, remap refutado 30/08). Stashes duraveis em `Desktop/Moodle/*`,
planos em `Desktop/claude-tutor/*.plano.md`, token Moodle renova sozinho (`scripts/moodle_token.py`).

## Ferramentas de medicao (todas rapidas)
- `python scripts/eval_eixos.py` — regua oficial 4 eixos (+ `--course SIGLA`).
- `python scripts/harness_cobertura.py [base|final] [--detalhe]` — cobertura offline ~15 s.
- `python scripts/ablacao_rapida.py [--curado] --repos MF,SO,IA,ES2,TCC,CG` — nu/curado em copias
  (`.ablacao/`; excecao conhecida do gate curado: IA 2 campos, ruido de voto no cache da copia).
- `python scripts/detecta_duplicatas.py [--repos ...] [--quase 0.9]` — NOVO: duplicatas em 4 niveis
  (BYTES/PDF-TEXTO/TEXTO/QUASE; pares enunciado<->gabarito excluidos).
- subunidade: comparar `computed_subunit_slug` do manifest com `docs/reports/subunit_gt_{SO,IA,ES2,TCC}.csv`
  (89/93 hoje; erros restantes: ES2 web+roteiro5, TCC aula-06+aula-08 — os 2 ultimos com gold CONFIRMADO).
- sentinela: manifest atual vs `git show HEAD:manifest.json` nos 6 (campos: temporal_block_id/method,
  computed_block_id/method, computed_unit_slug, computed_subunit_slug, confidencias, auto_tags,
  coverage_units, duplicate_of).
- reprocess: `python scripts/reprocess_assignments.py "C:/.../X-Tutor" [...]` (headless, deterministico).
