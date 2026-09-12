# Achados — eixo de UNIDADE medido (sessão de investigação, sem alteração de código)

date: 2026-08-18
branch: `feat/motor-atribuicao` · HEAD `419aaff` · working tree limpa
escopo: investigação do `known_tools` a pedido do user, e do item "ES2 e SO no scorer de unidade"
natureza: **relatório de medição**. Nenhum arquivo de produção alterado nesta sessão.

> Regra desta sessão: nada afirmado sem medição. Três hipóteses minhas foram
> REFUTADAS pelo dado e estão registradas como tal na seção C.

## Régua nova: `entry → unidade` (não existia)

O handoff anterior registra: *"Nenhuma régua atual mede `entry → unidade`"*. Construída aqui,
sem rotular nada novo — composição de dois golds **já aprovados**:

```
ground_truth_<C>.csv  (entry -> true_block_uuid)
        |><|  gold_units_<C>.csv  (block_uuid -> true_unit)
        =>    entry -> true_unit          191 entries nos 5 cursos
```

Predição pelo caminho de produção (`resolver_apply.py:225` → `_auto_map_entry_unit`), perfil
resolvido por `find_by_repo_root` com abort explícito se falhar (lição da sessão anterior).

**CAVEAT NÃO-NEGOCIÁVEL**: a verdade é a unidade do **bloco TEMPORAL**. Para material
multi-tópico os dois eixos divergem por design — é a tese central do handoff. Logo esta régua
**superestima o erro** em cursos com material transversal (SO, ES2). Quantificado em A-3.

### Baseline (as-of 2026-08-18, HEAD `419aaff`)

| curso | n | bruto | após gate 0.65 | produção grava | confiante-e-errado |
|---|---|---|---|---|---|
| MF | 67 | 53 (79%) | 40 (60%) | 54 (81%) | 7 |
| SO | 36 | 12 (33%) | 6 (17%) | 14 (39%) | **16 (44%)** |
| IA | 43 | 41 (95%) | 35 (81%) | 37 (86%) | 0 |
| ES2 | 27 | 8 (30%) | 7 (26%) | 8 (30%) | **16 (59%)** |
| TCC | 18 | 10 (56%) | 7 (39%) | 14 (78%) | 0 |
| **total** | **191** | **124 (65%)** | **95 (50%)** | **127 (66%)** | **39 (20%)** |

Distribuição pós-gate: **certo 95 (50%) · sem resposta 57 (30%) · confiante-e-errado 39 (20%)**.
`reconcile_unit_with_block` recupera de 50% para 66% — o scorer sozinho acerta metade.

### Decomposição dos 96 não-acertos

| balde | n | % | o que é |
|---|---|---|---|
| perdido no gate | 29 | 15% | predição CERTA, morta por `T.UNIT_TAG = 0.65` |
| divergência de eixo | 12 | 6% | card sustenta o predito e não a verdade temporal |
| erro real | 55 | 29% | resto |

O balde de eixo é conservador (exige card sustentando um lado e não o outro); o número real é
maior — ver A-3.

---

## A. Achados NOVOS desta sessão

### A-1 · Template do GLOSSARY.md vira topic_phrase de TODAS as unidades — 5/5 cursos
**severidade: alta · medido**

`_parse_glossary_terms` (`content_taxonomy.py:362`) trata **toda** linha `## ` do GLOSSARY.md
como termo. O template tem `## Formato de entrada` e `## Termos` como seções estruturais. Sem
`**Aparece em:**`, o `unit_hint` fica vazio, e o guard `if unit_hint and ...` (linha 404) **não
filtra nada** — o termo cola em TODA unidade.

Frases presentes em todas as unidades (as-of 2026-08-18):

| curso | frases ubíquas |
|---|---|
| MF | `formato de entrada`, `termos`, `usadas` |
| IA | `formato de entrada`, `termos` |
| SO | as duas + `conceito`, `central`, `unidade`, `reconhecido`, `usado`, `corretamente`, `respostas`, `revisoes` |
| ES2 | idem SO, mais `camadas` |
| TCC | idem SO, mais `definicao da classe` |

As oito extras vêm da **definição boilerplate auto-gerada**: *"Conceito central de esta unidade
que deve ser reconhecido e usado corretamente nas respostas e revisões."* A frase-modelo virou
vocabulário de todas as unidades.

Efeito medido (braço G — poda do boilerplate): **95 → 97 acertos pós-gate (+2, todo no TCC)**,
zero regressão, 8 a 10 frases-lixo a menos por unidade.

### A-2 · Score de unidade não é normalizado pelo tamanho — a maior unidade vence por default
**severidade: alta · medido**

`score_entry_against_unit` soma sobre `topic_phrases`. Os índices são muito desiguais:

| curso | frases min → max | razão |
|---|---|---|
| IA | 18 → 58 | 3,2× |
| TCC | 21 → 57 | 2,7× |
| ES2 | 24 → 46 | 1,9× |
| SO | 18 → 34 | 1,9× |
| MF | 38 → 47 | 1,2× |

Evidência direta: ES2 `unidade-01-arquitetura-de-software` tem 46 frases e é o predito em
**26 de 27** entries rotuladas. No SO, `unidade-06-gerencia-de-arquivos` (34 frases) é o dreno do
material administrativo — `plano-de-ensino` (conf 0,20), `programa` (0,20), `questoes-do-enade`
(0,10), `apresentacao-da-disciplina` (0,40).

Braço H (score ÷ √n_frases): **bruto 124 → 130 (+6)**, o melhor ranking de todos os braços,
TCC 10 → 14. **Mas pós-gate 95 → 86 (−9)**: a confiança deriva do score absoluto, então
normalizar derruba todo mundo abaixo de 0,65. Correção real exige recalibrar o gate junto.

### A-3 · Divergência de eixo é o modo dominante no ES2 — e sai confiante
**severidade: alta · medido**

ES2 tem **16 de 27 confiante-e-errado (59%)**. O padrão é uma série de laboratório:
`roteiro2..roteiro8`, `microsservicos2..7`, todos com card `Microsserviços`, todos preditos
`unidade-01-arquitetura-de-software` com confiança **0,86–0,95**, e verdade temporal em u02
(DevOps) ou u03 (Testes).

O scorer está respondendo **cobertura** (a série é sobre microsserviços, tópico da u01); a verdade
da régua é **temporal** (foram entregues ao longo do semestre). Não é bug de scorer — é o eixo
faltante. Mas o sistema grava com 0,95 de confiança uma unidade que discorda do cronograma, e
nada sinaliza.

Mesmo padrão no SO com `threads`: 6 entries (`3103-threads`, `biblioteca-em-c-pthread`,
`exemplo-threads-em-c-*`) preditas `unidade-03-programacao-concorrente`, verdade temporal
`unidade-02-gerencia-do-processador` ou `unidade-04-deadlock`. É literalmente a pergunta que o
handoff anterior deixou aberta.

### A-4 · `—` como alias: placeholder de formatação virando sinal
**severidade: média · medido · causa raiz confirmada**

O template escreve `**Sinônimos aceitos:** —` quando não há sinônimos. O parser
(`content_taxonomy.py:371`) faz `re.split(r"[,;/|]", ...)` e aceita qualquer não-vazio: o
travessão sobrevive como sinônimo e vira alias do tópico.

Aliases `—`/vazio na taxonomia em disco (as-of 2026-08-18): **100 de 361** —
SO 36/97 (37%) · ES2 21/50 (42%) · TCC 26/78 (33%) · MF 14/84 · IA 3/52.

Ruling do user: `—` é formatação em 99% dos casos. Correção: tratar `—`, `–`, `-`, vazio e `n/a`
como ausência de valor no parser do glossário.

### A-5 · Vazamento cross-unidade por alias (MF)
**severidade: média · medido**

`logica-de-hoare` é tópico de `unidade-02-verificacao-de-programas` (correto). Ao mesmo tempo
`Lógica de Floyd-Hoare` é **alias** de `fundamentos-de-logica-de-primeira-ordem`, na
`unidade-01`. Mesmo conceito ancorado em duas unidades, uma errada.

Quarta instância da classe "sinal textual de uma unidade vazando para outra" registrada no
handoff anterior — desta vez pela via de alias de glossário, não de heading.

### A-6 · O gate `T.UNIT_TAG = 0.65` mata 29 acertos (15% do total)
**severidade: alta · medido**

29 das 191 entries têm a unidade CERTA e são suprimidas pelo gate. Casos por 0,01:
`2403-escalonamento-de-processos` (SO) com 0,64. Outros: `lista-exercicios-p1` (0,46),
`1703-chamada-de-sistema` (0,51), `plano` do ES2 (0,54), três aulas do TCC empatadas em 0,63.

Nunca houve sweep de `UNIT_TAG` contra uma régua entry→unidade, porque a régua não existia.

---

## B. Achados da investigação do `known_tools`

### B-1 · A raiz: vocabulário auto-inferido do próprio corpus usado como filtro destrutivo
**severidade: estrutural · dano MEDIDO hoje: zero (ver B-2)**

`_infer_tool_candidates` (`semantic_config.py:196`) monta `known_tools` a partir do plano, course
map, glossário e headings do próprio curso — e o resultado é usado para **descartar tópicos desse
mesmo curso**. Realimentação positiva: quanto mais central o termo, mais repete em heading, mais
chance de virar "ferramenta", mais conteúdo apaga.

A perda histórica precisou de TRÊS camadas simultâneas:

1. o parser casava unidade contra `normalized_line` e tópico contra `line` cru, e **descartava o
   código numérico** (`m.group(1)`);
2. `content_taxonomy.py:488` — o guard `if not topic_code and not _is_valid_topic_candidate(...)`
   era a escotilha de escape para tópico numerado do plano; produtor e consumidor discordavam
   sobre o código morar no texto, nada assertava o contrato, **a escotilha nunca abriu**;
3. `_looks_like_tool_candidate` casava substring cru (`ementa` dentro de "implEMENTAção").

O fix `8495926` corrigiu (1), pôs fronteira de palavra em (3) e tirou CAIXA ALTA da promoção.
**Não removeu o loop.**

Vocabulário em produção (as-of 2026-08-18) — ainda contém o núcleo das disciplinas:
MF `formal`, `programas`, `modelos`, `invariantes`, `hoare`, `sobre`, `ferramentas` ·
TCC `hierarquia`, `propriedades`, `cook-levin`, `np-completude` · SO `threads` ·
ES2 `cliente-servidor`, `devops`.

### B-2 · MEDIDO: o filtro é INERTE hoje, nos dois eixos

**Prova mais forte que ablação**: `build_content_taxonomy` com `_looks_like_tool_candidate`
ligado vs desligado produz JSON **byte-idêntico** nos 5 cursos. O bypass do `topic_code` cobre
100% dos tópicos do plano — o filtro nunca é alcançado.

Eixo de BLOCO (191 entries, com e sem voto do LLM): **0 flips**.
Eixo de UNIDADE:

| braço | afeta | bruto | pós-gate | delta |
|---|---|---|---|---|
| base | — | 124 | 95 | — |
| sem `ferramenta:` poluída | 70 entries | 124 | 95 | +0 |
| sem `bloco:` (espelho) | 177 entries | 124 | 95 | +0 |
| sem `topico:` | 80 entries | 124 | 95 | +0 |
| `topico:` com prefixo numérico corrigido | 10 slugs | 124 | 95 | +0 |

Conclusão: **arma carregada com a trava acionada**. Higiene, não urgência.

### B-3 · O filtro de ferramenta é subtrativo — erro categórico

Ser ferramenta nunca deveria apagar tópico. Dafny é ferramenta **e** tópico do MF; threads é
ferramenta **e** tópico do SO. A definição operacional está no próprio código, em dois lugares:

- `concept_resolver.py:158` — token de ferramenta vale `_BLOCK_TOOL_FLOOR = 0.0` no escopo de
  BLOCO (não discrimina bloco dentro da unidade);
- `concept_resolver.py:218` `_tool_unit` — mas ancora a UNIDADE (*"um Dafny não cabe numa unidade
  Isabelle"*).

> **Ferramenta = instrumento com que a unidade inteira é ensinada, uniformemente. Discrimina
> unidade, não discrimina bloco.**
> Teste: trocar a coisa por outra mantém o conteúdo ensinado? Isabelle→Coq mantém "Lógica de
> Hoare" ⇒ ferramenta. Trocar "Lógica de Hoare" muda o conteúdo ⇒ tópico.

A lista certa já existe: `semantic_defaults.json`, 11 entradas, todas provadores.

### B-4 · Fix assimétrico: `_extract_tool_candidates` ficou com substring cru

`content_taxonomy.py:101` ganhou fronteira de palavra; `content_taxonomy.py:202` **não**. Causa:
duas cópias da mesma lógica de match. Efeito medido: `"Especificação informal de requisitos"` →
`ferramenta:formal`. Catálogos de produção: MF tem 20 `ferramenta:` contra 18 `topico:`.

### B-5 · Segundo parser de tópico sem normalização — divergência total de slug

`_extract_topic_candidates` trata `## `, `- [ ] `, `- `, mas **não `**`**. Linha real do plano do
SO: `- **1.1** Evolução histórica` → slug `11-evolucao-historica`, contra `evolucao-historica` da
taxonomia. **SO: 36 tópicos na taxonomia, 48 tags `topico:`, 0 casando.** Confirmado em produção
(`topico:32-escalonamento`, 10 slugs). O fix `8495926` criou o ponto único de normalização só em
`teaching_plan.py`. Impacto na régua: **nenhum** (braço F, +0).

### B-6 · IA: 0 tópicos do plano no catálogo de tags

`_extract_topic_candidates` exige linha começando com marcador ou número; o plano do IA vem em
linha solta. `_parse_units_from_teaching_plan` trata (`current_style == "learning_unit"`),
`content_taxonomy` não. 19 tópicos na taxonomia, 0 tags.

### B-7 · Heurísticas de forma rodando sobre entrada autoritativa

`_looks_like_weak_heading_candidate` mata tópico com mais de 6 palavras;
`_looks_like_bibliography_candidate` mata com 2+ hífens, 9+ espaços ou qualquer ano `19xx/20xx`.
Aplicados a tópico que o plano já numerou sob uma unidade. Vítimas no TCC:
`Argumento Diagonal de Cantor e Conjuntos Incontáveis`,
`Prova da Indecidibilidade do Problema da Parada`.

### B-8 · `.tag_catalog.json` é git-ignored e o rollout não regenerou

mtime 15:39 · fix commit 16:19 · rollout 16:48. Cache não versionado consumido pelo scorer.

### B-9 · `TOOL_TOKENS` não existe — o comentário mente

`entry_signals.py:84` diz *"o scorer de bloco (file_map, TOOL_TOKENS) filtra quais são ferramentas
de verdade"*. O símbolo só existe em `.pyc` stale. Nada filtra.

### B-10 · O teste do próprio fix congela o defeito

`tests/test_taxonomy_topic_loss.py:111-112` pina `Uso de threads` e `Provas de NP-Completude`
como ferramenta. Ambos são tópico. Caem quando B-3 for corrigido — devem cair.

---

## C. Hipóteses minhas REFUTADAS pela medição

Registradas porque as três eram convincentes e nenhuma sobreviveu ao número. Mesma classe do
achado #4 do handoff anterior.

1. **"`known_tools` cega o scorer de bloco em 57% das entries do MF."** Inferido de
   `_BLOCK_TOOL_FLOOR = 0.0`. Ablação: **0 flips** em 5 cursos, com e sem voto do LLM. O piso
   dispara de fato (`hoare` 1,0 → 0,0), mas o vetor de conceito da entry tem tokens demais para
   um token zerado mudar o argmax.
2. **"O voto do LLM está compensando o dano."** Repetido com `llm_curation=None`: **0 flips**
   também.
3. **"A auto_tag `bloco:` fecha um loop de realimentação no resolver."** `auto_tags_text` não
   entra no `content_text` do resolver (`concept_resolver.py:314`); é espelho de
   `computed_block_id` escrito por `resolver_apply.py:158`. Ablação: **0 flips**.

---

## D. Fila revisada, ordenada por impacto MEDIDO

| # | item | ganho medido | achado |
|---|---|---|---|
| 1 | sweep de `T.UNIT_TAG` contra esta régua | até +29 acertos | A-6 |
| 2 | normalizar score por tamanho de unidade **e recalibrar o gate junto** | +6 bruto, −9 pós-gate isolado | A-2 |
| 3 | podar boilerplate do template no parser do glossário | +2 pós-gate, 0 regressão | A-1, A-4 |
| 4 | eixo de cobertura para material transversal | destrava ES2 (59% conf-errado) e o threads do SO | A-3 |
| 5 | alias cross-unidade | dano estrutural provado, impacto não isolado | A-5 |
| 6 | `known_tools` e parsers duplicados | **zero** hoje | B-1..B-10 |

Itens 1 e 2 são acoplados: mexer no score sem recalibrar o gate piora o resultado gravado.

## F. Execução da fila (2026-08-18b) — resultados e CORREÇÕES ao que está acima

### F-1 · Item 3 (poda do glossário) — IMPLEMENTADO, ganho medido ZERO

Três fixes, todos com teste que falha antes:

| fix | arquivo | o que mudou |
|---|---|---|
| A-4 | `content_taxonomy.py` `_GLOSSARY_EMPTY_MARKERS` | `—`/`–`/`-`/`n/a`/`nenhum` deixam de virar sinônimo |
| A-1 | `file_map.py:~1280` | termo de glossário **sem `Aparece em`** não é sinal de unidade nenhuma |
| A-1/A-2 | `file_map.build_file_map_unit_index` | frase presente em TODAS as unidades é descartada de quem **não a tem como tópico próprio** |

Efeito estrutural (as-of 2026-08-18b): frases ubíquas **0 em todos os 5 cursos**; SO caiu de
168 para 98 frases no índice.
Efeito na régua: **+0**. Suite 1901 passed / 1 skipped.

> **Correção ao A-1**: o braço G previu **+2** e o fix entrega **+0**. O braço G não era
> simulação fiel (podava lista própria, sem recomputar `token_weights`). Quarta previsão minha
> refutada nesta campanha. O ruído era **simétrico** entre unidades — some do score de todas
> igualmente, então o argmax não muda. O fix continua certo (remove sinal de discriminância
> provadamente nula), mas não é ganho de acurácia.

> **Correção ao A-1 (tabela de frases ubíquas)**: `camadas` (ES2) e `definicao da classe` (TCC)
> eram **falsos positivos**. Meu contador somava OCORRÊNCIAS, não unidades — `camadas` aparece
> 3× dentro da u01 do ES2, e o curso tem 3 unidades. As demais entradas da tabela seguem válidas
> (verificadas por leitura do template e do guard, não pelo contador).

> **Correção ao A-2**: a razão de tamanho **PIOROU** com a poda, porque o boilerplate inflava as
> unidades pequenas: SO 1,89 → **3,00** · TCC 2,71 → **4,00** · IA 3,22 → **3,50** ·
> ES2 1,92 → **2,57** · MF 1,24 → 1,26.

### F-2 · Item 1 (gate) — CALIBRADO, `T.UNIT_TAG` 0.65 → 0.50

Primeiro sweep de `UNIT_TAG` da história do projeto (a régua não existia). **Medido
ponta-a-ponta, depois de `reconcile_unit_with_block`** — e essa distinção muda a conclusão:

| gate | GRAVA certo | errado | vazio |
|---|---|---|---|
| 0.65 | 126 | 46 | 19 |
| 0.60 | 127 | 46 | 18 |
| 0.55 | 129 | 47 | 15 |
| **0.50** | **132** | **47** | **12** |
| 0.45 | 132 | 48 | 11 |
| 0.40 | 132 | 49 | 10 |
| 0.00 | 132 | 52 | 7 |

Por curso em 0.50: MF 52→54 · SO 14→15 · IA 38→40 · ES2 8→8 · TCC 14→15.

> **Correção ao A-6**: eu disse "o gate mata 29 acertos". Ponta-a-ponta o ganho recuperável é
> **+6, não +29** — `file_map.py:724` faz `if not computed_unit_slug: return block_unit_slug`,
> ou seja, o gate suprimindo **herda a unidade do bloco**, que acerta mais que o scorer. Medir só
> o scorer inflava o ganho em ~5×. Quinta previsão corrigida pelo dado.

### F-3 · Item 2 (normalização por tamanho) — REJEITADO pela medição

Com o gate livre para se mover, α=0,5 é **pior que α=0 em toda a grade** (104 contra 109/110 no
scorer isolado). O ganho que o braço H aparentava vinha de comparar contra um gate fixo em 0.65.
Item removido da fila.

### F-4 · Achado NOVO · dois thresholds são constantes MORTAS

`UNIT_MATCH_MIN_WINNER` (0,5) e `UNIT_MATCH_REL_MARGIN` (0,15) produzem **resultado idêntico**
em todas as 72 linhas do sweep (valores testados: 0,5/0,3/0,15 e 0,15/0,10). Nenhum dos dois
discrimina nada no corpus atual. Ou o piso está frouxo demais para morder, ou o caminho de
`ambiguous` está sendo decidido antes por outra condição. Não investigado.

### F-5 · Baseline novo (as-of 2026-08-18b, `T.UNIT_TAG = 0.50`)

Ponta-a-ponta: **132 certo · 47 errado · 12 vazio** (era 126 · 46 · 19).

## G. Subunidade (2026-08-19) — régua sem rótulo + diagnóstico do colapso

### G-1 · `scripts/eval_subunit_health.py` — régua que não precisa de gold

Não mede acerto (não existe gold de subunidade). Mede se o **sinal existe**. Três checagens
derivadas do próprio artefato: **COLAPSO** (concentração ≥60% num subtópico, em unidade com ≥4
entries e ≥3 tópicos), **ÍMÃ** (tópico com ≥2,5× a mediana de aliases dos irmãos),
**INTEGRIDADE** (subtópico stale ou de outra unidade). Exit 1 se houver colapso ou integridade.

Achados na primeira execução (as-of 2026-08-19):

| curso | achado |
|---|---|
| IA | COLAPSO `u05 aprendizado-de-maquina`: 40 entries → **2** subtópicos de 4, **95%** num só |
| SO | COLAPSO `u06 gerencia-de-arquivos`: 5 entries → **1** subtópico de 6, **100%** |
| SO | COLAPSO `u02 gerencia-do-processador`: 9 entries → 2 de 4, **89%** |
| MF | STALE `logicadehoare2` → subtópico **`21-logica-de-hoare`**, que não existe na taxonomia |
| SO | FORA `programa` → `estudo-de-casos`, de outra unidade |
| MF·SO·IA·TCC | ÍMÃ em 5 tópicos (IA intro 9 aliases contra mediana 2 dos irmãos) |

> **O STALE do MF é o achado B-5 com consequência real.** `21-logica-de-hoare` é o slug com o
> prefixo numérico grudado — o mesmo defeito de `_strip_topic_prefix` que eu tinha medido como
> **inerte** na régua de unidade. Não é inerte: corrompe subunidade em produção.

### G-2 · Causa do colapso: NÃO é o ímã de aliases (medido)

Hipótese inicial: `_select_supported_taxonomy_topic` (`content_taxonomy.py:255`) usa
`if score > best_score` — empate mantém o **primeiro da lista**. Confirmado experimentalmente:
inverter a ordem dos tópicos do IA u05 troca `Aprendizado Supervisionado` de
`introducao-ao-aprendizado-de-maquina` para `paradigmas-de-aprendizado`. Desempate por
**posição**, não por evidência.

Fix candidato medido (empate ⇒ não vira alias de ninguém):

| efeito | resultado |
|---|---|
| aliases do IA u05 | `[9,2,2,2]` → `[4,2,2,2]` — ímã cortado pela metade |
| **colapso do IA u05** | **95% → 95%** — não muda nada |
| régua entry→unidade | **132 → 128 (−4)** |

**Rejeitado**: custa 4 atribuições certas e não move o colapso. Os aliases extras, mesmo no
tópico errado, alimentavam positivamente o scorer de UNIDADE.

### G-3 · Causa real: o tópico vencedor duplica o vocabulário da própria unidade

| unidade | título (tokens) | vencedor | ∩ título |
|---|---|---|---|
| IA u05 | `apren`,`maqui` | `introducao-ao-aprendizado-de-maquina` | **`apren`,`maqui`** (o título inteiro) |
| SO u06 | `arqui`,`geren` | `arquivos` | **`arqui`** |
| SO u02 | `geren`,`proce` | `escalonamento` | ∅ — mas `escal` está em **2 dos 4** rótulos irmãos |
| MF u01 (sem colapso) | `forma`,`metod` | — | nenhum tópico domina |

Regra unificada: **vence o tópico cujos tokens são os mais frequentes dentro do vocabulário da
própria unidade** — herdados do título (IA, SO u06) ou repetidos entre irmãos (SO u02). Um
rótulo curto feito do token mais comum da unidade é imbatível.

É a mesma lição do achado A-1, um nível abaixo: **token presente em vários irmãos não discrimina
entre eles.** Falta IDF intra-unidade em `score_entry_against_taxonomy_topic`.

Não implementado: sem régua de acerto de subunidade, trocaria perda medida por ganho não
medido — exatamente o erro que G-2 acabou de mostrar.

## H. IDF intra-unidade (2026-08-19) — implementado, medido, REJEITADO

Duas variantes implementadas e medidas contra as duas réguas. Nenhuma paga.

**Variante dura** — token comum aos irmãos sai do overlap **e** frase feita só de tokens comuns
não conta como hit exato:

| métrica | antes | com IDF duro |
|---|---|---|
| entry→unidade, ponta-a-ponta (gate 0,50) | **132 certo / 47 errado / 12 vazio** | **130 / 50 / 11** |
| entry→unidade, scorer isolado | 109 certo | 112 (+3) |
| SO u06 gerencia-de-arquivos | 100% num subtópico | **40%**, 3 de 6 |
| SO u02 | 89% | resolvido (sai da lista) |
| IA u02 solucao-de-problemas | 4 de 6 tópicos, 56% | **6 de 6**, 31% |
| **IA u05 aprendizado-de-maquina** | 95% | **98% — piorou** |
| TCC u01 e u04 | ok | **2 colapsos novos** (60% e 67%) |

**Variante suave** — IDF só no overlap de tokens, match de frase exata preservado:
**131 / 47 / 13**. Praticamente neutra; o colapso continua em 3, só troca de lugar
(IA u05 98%, SO u06 80%, TCC u02 90%).

**Rejeitadas as duas.** A dura custa 2 atribuições certas e 3 erros a mais; a suave é neutra e
não resolve nada. Revertido.

### H-1 · O que a medição ensinou sobre o IA u05

O colapso do IA u05 **sobrevive às duas variantes** (95% → 98%). Logo **não é causado por token
comum**. É causado pelos **aliases mal atribuídos**: `Aprendizado Supervisionado`,
`Aprendizado Não Supervisionado`, `Aula 02 - ...` estão em
`introducao-ao-aprendizado-de-maquina` quando pertencem a `paradigmas-de-aprendizado`.

Os dois fixes candidatos atacam metades diferentes e cada um cobra:

| fix | o que corrige | custo na régua de unidade | efeito no IA u05 |
|---|---|---|---|
| empate ⇒ ninguém (G-2) | a atribuição do alias | **−4** | nenhum |
| IDF intra-unidade (H) | o peso do token comum | **−2** | piora |

O fix certo é **empate ⇒ desempatar por evidência melhor** (mandar o alias para o tópico certo,
não para lugar nenhum) — e isso exige um sinal que hoje não existe.

### H-2 · Achado colateral APLICADO: bônus fantasma de +1,4

Implementando o IDF, o guard `if not topic_tokens` expôs um defeito no código atual:
`len(overlap) >= len(topic_tokens)` vira `0 >= 0` quando o tópico não tem token próprio, e soma
**+1,4 incondicional em toda entry avaliada**.

Vivo em produção: **3 tópicos do MF** cujo vocabulário inteiro está em `UNIT_GENERIC_TOKENS` —
`Linguagens de Especificação e Lógicas` e os dois `Softwares de Suporte à Verificação Formal
de ...`.

Guard aplicado. Ponta-a-ponta no gate operante (0,50): **132/47/12, idêntico** — neutro. Ganha
nos gates altos (0,65: 126→127 · 0,60: 127→128). Mantido por ser correção de defeito a custo
zero. Teste: `test_topico_sem_vocabulario_proprio_nao_ganha_bonus_fantasma`.

## E. Reprodução

- Régua: `scripts/eval_entry_unit.py`.
- Ablações e diagnósticos desta sessão (descartáveis, fora do repo): `ablate_tools.py`,
  `measure_unit_axis.py`, `measure_topico.py`, `diag_es2_so.py`, `buckets.py`, `fix_arms.py`,
  `conf_errado.py`.
