# Baseline do resolver (P2 Fase 2.3) — corpus real MF

date: 2026-06-17
harness: `scripts/compare_resolver.py` (read-only, nao escreve no repo, nao chama API)
repo: `Metodos-Formais-Tutor` (reprocessado 17/06)

## Como rodar

```
python scripts/compare_resolver.py "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor"
python scripts/compare_resolver.py        # roda os 5 cursos default, skip limpo nos ausentes
```

O `signals` e montado pelo MESMO caminho que o **BLOCK scorer da producao**:
`collect_entry_unit_signals(entry, markdown_text)` com
`markdown_text = _entry_markdown_text_for_file_map(root, entry)` — o markdown
CRU. Para codigo/zip sem `.md` convertido o markdown cai **vazio**, IGUAL ao
funil: NAO injetamos o surrogate `code_curation_signal_text` (o funil so o usa
na rota de subunit/topico, NUNCA no scorer de bloco) e NAO mesclamos
`known_tools` do `.semantic_profile` em `tool_tags_text` (a producao nunca
injeta — `tool_tags_text` vem so de `auto_tags ferramenta:` + extensao).

**Comparacao NAO like-for-like:** o resolver le os `concepts` do Gemini
(injetados em `entry["concepts"]`, canal LLM-first-class por design) + o voto
LLM (`summary` da curation: `primary_block_id`/`secondary_block_ids`/
`block_match_confidence`). O funil (oraculo = `entry["computed_block_id"]` JA no
manifest, nao recomputado) NAO le esses concepts no scorer de bloco. Logo a
comparacao e "resolver-COM-concepts-do-LLM vs funil-SEM" — esperado divergir
exatamente onde o sinal semantico do LLM e o unico discriminante de code/zip.

## Tabela MF (57 materiais, 21 blocos, 3 unidades)

Numeros CORRIGIDOS apos remover o surrogate de markdown + a mescla de
`known_tools` (harness fiel a producao). Blocos mudados (resolver != funil):
**28** (era 32 com o surrogate). Conflitos flagados: **9** (era 7).

| id | funil | resolver | mudou | funil_unit | resolver_unit | conflito | band f->r |
|---|---|---|---|---|---|---|---|
| arvores | bloco-06 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | media->alta |
| classes-parte1 | bloco-16 | bloco-15 | SIM | unidade-03-verificacao-de-modelos | unidade-02-verificacao-de-programas | - | media->alta |
| exemplos | bloco-06 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exemplos-zip | bloco-12 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | - | alta->media |
| exercicioscorrecaoinducaomatematica | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| exerciciosdafny1 | bloco-15 | bloco-11 | SIM | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | baixa->alta |
| exerciciosdafny5 | bloco-15 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | - | baixa->media |
| formalizacaoalgoritmos-recursao | bloco-04 | bloco-11 | SIM | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->alta |
| hoare | bloco-10 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | - | alta->alta |
| intro | bloco-06 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | baixa->media |
| introducao | bloco-11 | bloco-16 | SIM | unidade-02-verificacao-de-programas | unidade-03-verificacao-de-modelos | SIM | media->media |
| invariantes | bloco-11 | bloco-04 | SIM | unidade-02-verificacao-de-programas | unidade-01-metodos-formais | - | alta->media |
| listas | bloco-06 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| logicadehoare | bloco-10 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | SIM | baixa->media |
| logicapredicados-semantica | bloco-03 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| logicapredicados-sintaxe | bloco-03 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| logicaproposicional-semantica | bloco-03 | bloco-06 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |
| logicaproposicional-sintaxe | bloco-03 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | media->media |
| provas | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | media->media |
| provasindutivas-especificacoesrecursivas | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |
| provasindutivas-especificacoesrecursivas-arvores | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| provasindutivas-especificacoesrecursivas-listas | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| revisao | bloco-02 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | - | baixa->alta |
| revisao-p1-gabarito | bloco-07 | bloco-04 | SIM | unidade-02-verificacao-de-programas | unidade-01-metodos-formais | - | alta->alta |
| t1-2026-1 | bloco-05 | bloco-06 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |
| t1-2026-1-thy | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | baixa->media |
| terminacao | bloco-11 | bloco-12 | SIM | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->media |
| verificacaomodelos | bloco-16 | bloco-11 | SIM | unidade-03-verificacao-de-modelos | unidade-02-verificacao-de-programas | - | alta->media |
| colecoes-arrays | bloco-13 | bloco-13 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | SIM | alta->media |
| colecoes-conjuntos | bloco-13 | bloco-13 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | SIM | alta->media |
| colecoes-sequences | bloco-13 | bloco-13 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->media |
| conjuntosindutivos | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |
| correcaoterminacao | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->alta |
| exercicios-conjuntos | bloco-13 | bloco-13 | - | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | SIM | alta->media |
| exerciciosconjuntosindutivos | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exercicioscorrecaoterminacao | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | media->alta |
| exerciciosdafny2 | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | baixa->alta |
| exerciciosdafny3 | bloco-13 | bloco-13 | - | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | SIM | baixa->media |
| exerciciosdafny4 | bloco-13 | bloco-13 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | SIM | baixa->media |
| exerciciosespecificacao | bloco-03 | bloco-03 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosespecificacao-respostas | bloco-03 | bloco-03 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosformalizacaoalgoritmosinvariantes | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->alta |
| exerciciosformalizacaoalgoritmosrecursao | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosformalizacaoalgoritmosrecursao-respostas | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosformalizacaoalgoritmosrecursao2 | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosformalizacaoalgoritmosrecursao3 | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosisabelle | bloco-06 | bloco-06 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosisabelle2 | bloco-06 | bloco-06 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exercicioslogicatemporal | bloco-16 | bloco-16 | - | unidade-03-verificacao-de-modelos | unidade-03-verificacao-de-modelos | SIM | alta->media |
| exerciciosnusmv | bloco-16 | bloco-16 | - | unidade-03-verificacao-de-modelos | unidade-03-verificacao-de-modelos | SIM | media->media |
| formalizacaoalgoritmos-invarianteslaco | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->alta |
| formalizacaoalgoritmos-recursao2 | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |
| formalizacaoalgoritmos-recursao3 | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| introducao-zip | bloco-12 | bloco-12 | - | unidade-03-verificacao-de-modelos | unidade-02-verificacao-de-programas | - | media->media |
| logicadehoare2 | bloco-10 | bloco-10 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| revisao-p1 | bloco-06 | bloco-06 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| tiposindutivos | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |

### O que MUDOU ao remover o surrogate (vs baseline anterior, com surrogate)

Remover o `code_curation_signal_text` como markdown de bloco e a mescla de
`known_tools` reduziu a divergencia de 32 -> 28 e CORRIGIU dois non-regress:
`colecoes-conjuntos` e `colecoes-sequences` agora FICAM em bloco-13 (antes
caiam em bloco-04 puxados pelo surrogate). `terminacao` mudou de `11->04` para
`11->12` (ainda diverge, mas o destino mudou). `t1-2026-1` mudou de `->04`
para `->06`. As demais linhas estao estaveis. Conflitos subiram 7 -> 9
(`colecoes-conjuntos` e `logicadehoare` agora flagam block-unit != topic-unit).

## Checagem dos alvos da Fase 2

**4 que DEVEM mudar (funil errado -> resolver certo):**
- arvores: bloco-06 -> bloco-05 (esperado 05) — **OK**
- intro: bloco-06 -> bloco-05 (esperado 04) — **DIVERGE** (caiu em 05, nao 04)
- listas: bloco-06 -> bloco-05 (esperado 05) — **OK**
- classes-parte1: bloco-16 -> bloco-15 (esperado 15) — **OK**

3/4 confirmados. `intro` diverge (ver leitura abaixo).

**6+ que NAO podem regredir:**
- colecoes-arrays: 13 inalterado — **OK** (mas ver caveat: o voto ATUAL do
  `code_curation` para `colecoes-arrays` e bloco-04 — o resolver elegeu 13 por
  outra via, nao por concordancia de voto; logo NAO e um non-regress limpo
  vote-consistente, so ficou em 13 porque o resolver o escolheu)
- exercicios-conjuntos: 13 inalterado — **OK** (UNICO non-regress genuinamente
  vote-consistente: o voto do `code_curation` tambem e 13, 13==13)
- colecoes-conjuntos: 13 inalterado — **OK** (corrigido apos remover o surrogate;
  antes caia em 04. Voto atual do Gemini ainda e bloco-04 -> ficou em 13 por
  escolha do resolver, NAO por concordancia de voto)
- colecoes-sequences: 13 inalterado — **OK** (idem: voto atual = bloco-04, mas
  com secondary=bloco-13; ficou em 13 por escolha do resolver)
- invariantes: 11 -> 04 — **DIVERGE** (voto atual = bloco-04, conf 0.75)
- terminacao: 11 -> 12 — **DIVERGE** (voto atual = bloco-04; o resolver elegeu
  bloco-12 — nem o voto nem o funil; destino mudou de 04 p/ 12 apos remover o
  surrogate, conduzido por concept-overlap agora que o markdown cai vazio)
- hoare: 10 -> 11 — **DIVERGE** (voto atual = bloco-11)

4/7 confirmados (era 2/7 com o surrogate); 3 divergem (invariantes, terminacao,
hoare). **Caveat de leitura:** dos 4 "OK" de non-regress, so
`exercicios-conjuntos` e vote-consistente (voto atual = 13 == 13).
`colecoes-arrays` (voto atual = bloco-04), `colecoes-conjuntos` e
`colecoes-sequences` (votos atuais = bloco-04) ficaram em 13 por ESCOLHA do
resolver, nao por concordancia com o voto ATUAL do Gemini — nao sao non-regress
"limpos" no sentido de voto==resultado.

## Leitura (3 paragrafos) — por que diverge e por que NAO se calibra

**1. A causa raiz e DRIFT DE INPUT (lineage), nao peso do resolver.** O
`computed_block_id` do manifest (oraculo de comparacao) das entries que
"regridem" carrega uma RODADA ANTERIOR da curadoria Gemini. **Correcao de
fato:** a staleness NAO esta na idade do arquivo — `manifest.json` (mtime
2026-06-17) e na verdade MAIS NOVO que `code_curation.json` (mtime 2026-06-16).
A staleness esta na LINEAGE do valor de block-assignment congelado: o
`manifest.generated_at` e **2026-03-23**, ou seja o `computed_block_id` foi
escrito por uma rodada de marco e nunca recomputado, enquanto o
`code_curation.json` carrega os votos Gemini de junho. Esses votos atuais sao:
`colecoes-conjuntos`/`colecoes-sequences`/`invariantes`/`terminacao` =
`primary_block_id=bloco-04`, `hoare`=`bloco-11`, `exercicios-conjuntos`=`bloco-13`,
`colecoes-arrays`=`bloco-04`. O funil e o resolver estao lendo OPINIOES
DIFERENTES do mesmo Gemini (o funil congelou a antiga no manifest via
`generated_at`=marco; o resolver le a `code_curation.json` de junho). A conclusao
de drift/lineage permanece — so a redacao "manifest mais velho que curation"
estava invertida pela mtime do arquivo.

**2. Os concepts reais sao genericos e nao discriminam.** As entries de codigo/zip
do MF tem concepts Gemini do tipo "datatype / tipo indutivo / predicado / verificacao
de tipo" — vocabulario comum a Dafny/Isabelle que casa FORTE com `bloco-04`
("Especificacao de Conjuntos Indutivos") qualquer que seja o bloco verdadeiro.
**Atualizacao apos remover o surrogate:** com o markdown caindo vazio (fiel a
producao), o concept-overlap agora vem so de `title_text`+`concepts` em vez do
texto inflado do surrogate; isso fez `colecoes-conjuntos`/`colecoes-sequences`
PARAREM em bloco-13 (nao mais 04) e moveu `terminacao` p/ bloco-12. Ou seja: o
surrogate estava ARTIFICIALMENTE empurrando essas entries para 04. O ponto de
fundo permanece — `invariantes` ainda cai em 04 (voto + concept genericos
concordam la). O oraculo 2.2 (sintetico) alimentou concepts hand-crafted que
discriminavam (ex. "colecoes arrays sequencias") + um voto LLM deliberadamente
errado, montando o cenario "concept forte vence LLM errado"; esse cenario NAO
ocorre naturalmente nessas entries reais. Para `intro`, o `intro.thy` foi
convertido em `.md` real cujos concepts trazem "inducao" (token de peso 1.0) que
casa `bloco-05` ("Inducao arvores"), enquanto o LLM vota 04 ("Conjuntos
Indutivos") — ambos sao blocos de inducao plausiveis, divergencia genuinamente
ambigua sem rotulo humano.

**3. Por que NAO calibrar (decisao registrada para a Fase 3).** Ajustar pesos para
forcar `bloco-13/11/10` seria overfit a um baseline STALE que contradiz tanto o voto
ATUAL do proprio Gemini quanto o overlap de conceito — exatamente o que o brief proibe.
A divergencia exige decisao de produto: (a) qual rodada de curadoria e o ground-truth
(o manifest congelado ou o `code_curation.json` reprocessado?), e (b) um conjunto de
rotulos humanos para code/zip, ja que os concepts genericos do Gemini nao discriminam
bloco. **Recomendacoes para a Fase 3:** (i) reconciliar manifest x code_curation (re-rodar
`attach_block_summary_fields`/`regenerate_pedagogical_files` ANTES de comparar, para que
funil e resolver leiam a MESMA opiniao); (ii) construir um gold rotulado por humano para
as ~12 entries de codigo (o eval atual e so 5 PDFs); (iii) so entao decidir se o resolver
precisa de um sinal posicional/data extra para code/zip sem source_section (hoje todos
caem em concept+LLM puro). O resolver permanece NAO wired (Fase 3); o golden 5/5 e a
suite 1420 seguem intactos.

## Caveats da comparacao / o que a Fase 3 precisa

Tres ressalvas que limitam o que este baseline pode concluir hoje — todas viram
acao na Fase 3, NENHUMA justifica calibrar peso agora:

1. **Reconciliar manifest x code_curation antes de julgar o resolver.** O oraculo
   (funil `computed_block_id`, `generated_at`=2026-03-23) e o input do resolver
   (`code_curation.json` de junho) leem opinioes Gemini DIFERENTES. Antes de
   medir "resolver vs funil" e preciso re-rodar
   `attach_block_summary_fields`/`regenerate_pedagogical_files` (ou congelar a
   curadoria) para que ambos leiam o MESMO voto. Sem isso, parte da "divergencia"
   e drift de lineage, nao erro do resolver.

2. **A comparacao NAO e like-for-like.** O resolver le os `concepts` do Gemini
   (`entry["concepts"]`, canal LLM-first-class por design) + o voto LLM; o funil
   (scorer de bloco) IGNORA esses concepts. Logo divergencias onde o LLM e o
   unico sinal discriminante de code/zip sao ESPERADAS por construcao — nao sao,
   por si so, evidencia de que o resolver esteja errado. O harness agora declara
   esse caveat explicitamente na saida ("resolver-COM-concepts-do-LLM vs
   funil-SEM").

3. **Falta gold rotulado por humano para as ~12 entries de code/zip.** O eval
   atual (`scripts/eval_assignments.py`) cobre **so 5 PDFs**. Os concepts Gemini
   de code/zip sao genericos ("datatype/tipo indutivo/predicado") e nao
   discriminam bloco; sem rotulos humanos nao da pra dizer se 13/12/04/11 e o
   bloco CERTO para `colecoes-*`/`terminacao`/`invariantes`/`hoare`. A Fase 3
   precisa construir esse gold ANTES de qualquer decisao de tuning.

## Cross-course (skip limpo dos campos faltantes)

Os 5 cursos default tem manifest. Resumo (alvos da Fase 2 sao MF-only):
- Engenharia-Software-2: 33 materiais, 12 blocos, 0 unidades; 20 mudados. O resolver
  colapsa quase tudo em `bloco-02` (bloco "Spring/microservices" de altissimo overlap
  lexico) — MESMO padrao: vocabulario compartilhado domina quando a entry nao tem sinal
  discriminante, e o funil (tambem llm_only) discorda. Sem unidades na taxonomia -> sem
  conflito flagavel.
- Inteligencia-Artificial: 16 materiais, 18 blocos, 0 unidades; 9 mudados.
- Sistemas-Operacionais / TCC: rodam pelo harness (ver saida completa de
  `python scripts/compare_resolver.py`); sem alvos definidos.

Conclusao cross-course: o resolver generaliza mecanicamente (le os sinais certos em
todos os repos), mas a QUALIDADE da atribuicao em code/zip depende de concepts Gemini
discriminantes — onde faltam, ele segue concept+LLM e diverge do funil. Confirma a
recomendacao: a Fase 3 precisa de gold rotulado, nao de calibracao de peso.
