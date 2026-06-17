# Baseline do resolver (P2 Fase 2.3) — corpus real MF

date: 2026-06-17
harness: `scripts/compare_resolver.py` (read-only, nao escreve no repo, nao chama API)
repo: `Metodos-Formais-Tutor` (reprocessado 17/06)

## Como rodar

```
python scripts/compare_resolver.py "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor"
python scripts/compare_resolver.py        # roda os 5 cursos default, skip limpo nos ausentes
```

O `signals` e montado pelo MESMO caminho da producao:
`collect_entry_unit_signals(entry, markdown_text)` com
`markdown_text = _entry_markdown_text_for_file_map(root, entry)`; para
codigo/zip sem `.md` convertido, o markdown cai em `code_curation_signal_text`
(o surrogate de conteudo que o funil tambem usa). `tool_tags_text` recebe a
uniao com `known_tools` do `.semantic_profile.generated.json` (down-weight de
bloco da 2.1). O voto do LLM e o `summary` da curation (carrega
`primary_block_id`/`secondary_block_ids`/`block_match_confidence`/`concepts`); o
`concepts` da entry vem de `summary.concepts`. O funil (oraculo de comparacao) e
`entry["computed_block_id"]` JA no manifest (nao recomputado).

## Tabela MF (57 materiais, 21 blocos, 3 unidades)

Blocos mudados (resolver != funil): 32. Conflitos flagados: 7.

| id | funil | resolver | mudou | funil_unit | resolver_unit | conflito | band f->r |
|---|---|---|---|---|---|---|---|
| arvores | bloco-06 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | media->alta |
| classes-parte1 | bloco-16 | bloco-15 | SIM | unidade-03-verificacao-de-modelos | unidade-02-verificacao-de-programas | - | media->media |
| colecoes-conjuntos | bloco-13 | bloco-04 | SIM | unidade-02-verificacao-de-programas | unidade-01-metodos-formais | - | alta->media |
| colecoes-sequences | bloco-13 | bloco-04 | SIM | unidade-02-verificacao-de-programas | unidade-01-metodos-formais | - | alta->baixa |
| exemplos | bloco-06 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exemplos-zip | bloco-12 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | - | alta->media |
| exercicioscorrecaoinducaomatematica | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| exerciciosdafny1 | bloco-15 | bloco-11 | SIM | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | baixa->alta |
| exerciciosdafny5 | bloco-15 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | - | baixa->media |
| exerciciosespecificacao | bloco-03 | bloco-01 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| exerciciosespecificacao-respostas | bloco-03 | bloco-01 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| formalizacaoalgoritmos-recursao | bloco-04 | bloco-11 | SIM | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->media |
| hoare | bloco-10 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | - | alta->alta |
| intro | bloco-06 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | baixa->media |
| introducao | bloco-11 | bloco-16 | SIM | unidade-02-verificacao-de-programas | unidade-03-verificacao-de-modelos | SIM | media->media |
| invariantes | bloco-11 | bloco-04 | SIM | unidade-02-verificacao-de-programas | unidade-01-metodos-formais | - | alta->media |
| listas | bloco-06 | bloco-05 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| logicadehoare | bloco-10 | bloco-11 | SIM | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | - | baixa->media |
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
| t1-2026-1 | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->baixa |
| t1-2026-1-thy | bloco-05 | bloco-04 | SIM | unidade-01-metodos-formais | unidade-01-metodos-formais | - | baixa->media |
| terminacao | bloco-11 | bloco-04 | SIM | unidade-02-verificacao-de-programas | unidade-01-metodos-formais | - | alta->media |
| verificacaomodelos | bloco-16 | bloco-11 | SIM | unidade-03-verificacao-de-modelos | unidade-02-verificacao-de-programas | - | alta->baixa |
| colecoes-arrays | bloco-13 | bloco-13 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | SIM | alta->media |
| conjuntosindutivos | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |
| correcaoterminacao | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->alta |
| exercicios-conjuntos | bloco-13 | bloco-13 | - | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | SIM | alta->media |
| exerciciosconjuntosindutivos | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exercicioscorrecaoterminacao | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | media->alta |
| exerciciosdafny2 | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | baixa->alta |
| exerciciosdafny3 | bloco-13 | bloco-13 | - | unidade-01-metodos-formais | unidade-02-verificacao-de-programas | SIM | baixa->media |
| exerciciosdafny4 | bloco-13 | bloco-13 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | SIM | baixa->media |
| exerciciosformalizacaoalgoritmosinvariantes | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->alta |
| exerciciosformalizacaoalgoritmosrecursao | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosformalizacaoalgoritmosrecursao-respostas | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosformalizacaoalgoritmosrecursao2 | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosformalizacaoalgoritmosrecursao3 | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosisabelle | bloco-06 | bloco-06 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exerciciosisabelle2 | bloco-06 | bloco-06 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| exercicioslogicatemporal | bloco-16 | bloco-16 | - | unidade-03-verificacao-de-modelos | unidade-03-verificacao-de-modelos | SIM | alta->media |
| exerciciosnusmv | bloco-16 | bloco-16 | - | unidade-03-verificacao-de-modelos | unidade-03-verificacao-de-modelos | SIM | media->media |
| formalizacaoalgoritmos-invarianteslaco | bloco-11 | bloco-11 | - | unidade-02-verificacao-de-programas | unidade-02-verificacao-de-programas | - | alta->media |
| formalizacaoalgoritmos-recursao2 | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |
| formalizacaoalgoritmos-recursao3 | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| introducao-zip | bloco-12 | bloco-12 | - | unidade-03-verificacao-de-modelos | unidade-02-verificacao-de-programas | - | media->baixa |
| logicadehoare2 | bloco-10 | bloco-10 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| revisao-p1 | bloco-06 | bloco-06 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->alta |
| tiposindutivos | bloco-04 | bloco-04 | - | unidade-01-metodos-formais | unidade-01-metodos-formais | - | alta->media |

## Checagem dos alvos da Fase 2

**4 que DEVEM mudar (funil errado -> resolver certo):**
- arvores: bloco-06 -> bloco-05 (esperado 05) — **OK**
- intro: bloco-06 -> bloco-05 (esperado 04) — **DIVERGE** (caiu em 05, nao 04)
- listas: bloco-06 -> bloco-05 (esperado 05) — **OK**
- classes-parte1: bloco-16 -> bloco-15 (esperado 15) — **OK**

3/4 confirmados. `intro` diverge (ver leitura abaixo).

**6+ que NAO podem regredir:**
- colecoes-arrays: 13 inalterado — **OK**
- exercicios-conjuntos: 13 inalterado — **OK**
- colecoes-conjuntos: 13 -> 04 — **DIVERGE**
- colecoes-sequences: 13 -> 04 — **DIVERGE**
- invariantes: 11 -> 04 — **DIVERGE**
- terminacao: 11 -> 04 — **DIVERGE**
- hoare: 10 -> 11 — **DIVERGE**

2/7 confirmados; 5 divergem.

## Leitura (3 paragrafos) — por que diverge e por que NAO se calibra

**1. A causa raiz e DRIFT DE INPUT, nao peso do resolver.** O `computed_block_id`
do manifest (oraculo de comparacao) das 5 entries que "regridem" foi escrito por
`method=llm_only`/`consensus` — ou seja, por uma RODADA ANTERIOR da curadoria
Gemini. O `code_curation.json` atual (reprocessado 16/06 21:1x) MUDOU esses votos:
`colecoes-conjuntos`/`colecoes-sequences`/`invariantes`/`terminacao` agora tem
`primary_block_id=bloco-04`, e `hoare` tem `primary_block_id=bloco-11` — exatamente
os blocos que o resolver elege. O funil e o resolver estao lendo OPINIOES DIFERENTES
do mesmo Gemini (o funil congelou a antiga no manifest; o resolver le a nova). O
breakdown confirma: invariantes fused(04)=concept 1.0 + llm 0.75 = 1.64 (concept E
LLM concordam em 04); colecoes-conjuntos concept(04)=1.5 + llm 0.6. Nao ha "voto LLM
errado vs concept certo" como no oraculo 2.2 — ambos os sinais reais apontam 04.

**2. Os concepts reais sao genericos e nao discriminam.** As entries de codigo/zip
do MF tem concepts Gemini do tipo "datatype / tipo indutivo / predicado / verificacao
de tipo" — vocabulario comum a Dafny/Isabelle que casa FORTE com `bloco-04`
("Especificacao de Conjuntos Indutivos") qualquer que seja o bloco verdadeiro. O
oraculo 2.2 (sintetico) alimentou concepts hand-crafted que discriminavam (ex.
"colecoes arrays sequencias") + um voto LLM deliberadamente errado, montando o cenario
"concept forte vence LLM errado". Esse cenario NAO ocorre naturalmente nessas entries
no corpus reprocessado. Para `intro`, o `intro.thy` foi convertido em `.md` real cujos
concepts trazem "inducao" (token de peso 1.0) que casa `bloco-05` ("Inducao arvores"),
enquanto o LLM vota 04 ("Conjuntos Indutivos") — ambos sao blocos de inducao plausiveis,
divergencia genuinamente ambigua sem rotulo humano.

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
