# Handoff — cardinalidade do motor: por que unidade e subunidade travam

> **SUPERADO por `docs/reports/2026-08-20-handoff-fechamento-campanha-motor.md`** (2026-08-20).
> A sessão continuou depois deste documento. Seções A–H seguem válidas (tese, os 4 consumidores,
> as 5 previsões refutadas, notas operacionais). **A seção I-7 está VENCIDA** — a DECISION de
> granularidade foi resolvida e as duplicatas foram removidas. Ler o handoff de 20/08 primeiro.

date: 2026-08-19
branch: `feat/motor-atribuicao` · gerador HEAD `419aaff` · **código na árvore, NÃO commitado**
5 repos-tutor: **limpos e NÃO reprocessados** (dois reprocess aplicados e revertidos nesta sessão)
suite: **1902 passed / 1 skipped / 0 failed**

> Sessão de INVESTIGAÇÃO E MEDIÇÃO. Tudo abaixo foi medido, não inferido. Cinco previsões minhas
> foram refutadas pelo dado — estão registradas na seção E porque o padrão de erro importa mais
> que os acertos.

## Boot da nova sessão

1. `mem-search` · `.mex/ROUTER.md` · este handoff · tracker `docs/reports/pendencias.md`
   (cabeçalho + seções `## CODE — REALIMENTACAO`, `## CODE — eixo de UNIDADE`,
   `## CODE — SUBUNIDADE`, `## CODE — o eixo N:N e ESCRITO e NUNCA LIDO`).
2. Relatório completo com todas as tabelas: `docs/reports/2026-08-18-achados-eixo-unidade.md`.
3. Handoff anterior (dois eixos, taxonomia, camada de referência):
   `2026-08-18-handoff-cobertura-taxonomia.md`.
4. Réguas: `scripts/eval_entry_unit.py` (nova) · `scripts/eval_subunit_health.py` (nova) ·
   `scripts/eval_ground_truth.py` · `scripts/eval_units.py` · `scripts/eval_coverage.py`.

---

## A. A TESE — a raiz é cardinalidade, não scorer

Três eixos, e o sistema usa a cardinalidade errada em dois:

| eixo | pergunta | cardinalidade CORRETA | o que o código faz hoje | acerto medido |
|---|---|---|---|---|
| bloco | *quando foi dado?* | **1** | 1 ✓ | **118/208 = 57%** |
| unidade | *o que cobre?* | **N** | 1 ✗ | 129/191 = 68% (teto 94%) |
| subunidade | *sobre o que é?* | **N (tags)** | 1 ✗ | **sem gold nenhum** |

**Evidência dura**: 53 arquivos avaliativos (prova, lista, gabarito, exercício, trabalho) nos 5
cursos, e **os 53 recebem exatamente uma subunidade**. A lista P1 do SO cobre escalonamento,
threads e sincronização; recebe `programas-multithreads` e ponto. Não é o scorer errando — é o
campo não comportando a resposta.

**Consequência 1 — o "colapso" da subunidade é artefato.** IA u05 com 95% em
`introducao-ao-aprendizado-de-maquina`: 40 arquivos de uma unidade de ML **são** sobre
aprendizado de máquina. O defeito é faltarem a segunda e a terceira tag. Passei três tentativas
de fix tentando fazer um vencedor melhor num lugar onde não deve haver vencedor.

**Consequência 2 — a régua não pode chegar a 100%.** Ela pergunta "qual é a unidade?" para
arquivos com duas respostas certas. Acertar a régua no `roteiro4-circuitbreaker` do ES2 exigiria
afirmar que ele não é sobre microsserviços — o que é falso.

**Consequência 3 — toda melhoria em material multi-tópico registra −1.** Tirar o arquivo de uma
unidade certa e pôr em outra unidade certa é perda na régua. É por isso que nenhum fix fecha.

---

## B. Estado verificado (as-of 2026-08-19)

### Régua entry→unidade (NOVA — o handoff anterior registrava que não existia)

Verdade sem rotular nada: `ground_truth_<C>.csv` (entry→true_block_uuid) ⨝
`gold_units_<C>.csv` (block_uuid→true_unit). **191 entries.**

```
curso    ok  EIXO  GATE  S/SINAL  ERRO   total    %
MF       51     0     3        3    10      67   76%
SO       15     6     2        1    12      36   42%
IA       40     0     1        1     1      43   93%
ES2       8     6     0        0    13      27   30%
TCC      15     0     0        0     3      18   83%
TOTAL   129    12     6        5    39     191   68%
```

- **IA (93%) e TCC (83%) estão praticamente resolvidos.** O motor funciona.
- **SO (42%) e ES2 (30%) carregam 25 dos 39 ERRO e os 12 do EIXO.**
- O detector de EIXO é **conservador** (exige o card sustentar um lado e não o outro). Os 13 ERRO
  do ES2 são `roteiro2..8` / `microsservicos2..7` — série de laboratório, divergência de eixo
  confirmada caso a caso. **O EIXO real é ~30, não 12.**
- **Teto no modelo 1:1 = 179/191 = 94%.** Contando ES2 corretamente, ~85%.

CAVEAT NÃO-NEGOCIÁVEL: a verdade é a unidade do **bloco TEMPORAL**. A régua superestima o erro em
curso com material transversal (SO, ES2).

### Outros eixos

- **bloco 118/208 = 57%** — o mais fraco, o único genuinamente 1:1, com gold pronto, e
  **ninguém mexeu nele nesta campanha**. Maior ganho disponível.
- **subunidade**: teto de acerto 133/170 = 78% (condição NECESSÁRIA — o subtópico pertence à
  unidade certa; não é acerto). Colapso em 3 unidades. Sem gold.
- **tags-espelho**: `unit:` acerta **126/168 = 75%** · `bloco:` **118/194 = 61%**.
  `topico:` e `ferramenta:` **não têm gold, nunca tiveram**.

---

## C. Código na árvore (7 arquivos, NÃO commitado, suite verde)

| mudança | arquivo | efeito medido |
|---|---|---|
| `T.UNIT_TAG` 0,65 → 0,50 | `routing/thresholds.py` | **+3** |
| termo de glossário sem `Aparece em` não é sinal; frase ubíqua podada | `routing/file_map.py` | **+1** |
| `—` e afins não viram sinônimo | `extraction/content_taxonomy.py` | (junto do anterior) |
| guard do bônus fantasma `0 >= 0` | `timeline/index.py` | **0** (corrige defeito real) |
| aprendizado ignora prefixos-espelho | `models/tag_profile.py` | **+1** |
| `auto_tags_text`/`tags_text` sem eco | `extraction/entry_signals.py` | **−2, ponto fixo** |

Isolado com harness fiel: **126 → 131 (+5), nenhum curso regride.**
Com o corte do eco: **129**, e o reprocess vira **idempotente**.

### O ganho estrutural: ponto fixo

```
reprocess rodado DUAS vezes seguidas, mesmo código:
  MF 0 · SO 0 · IA 0 · ES2 0 · TCC 0   entries mudaram
```

Antes, o mesmo scorer dava 131 com as tags velhas e 129 com as novas — **cada reprocess
deslocava 2 sem ninguém mudar nada**. As `auto_tags` eram entrada E saída.

**Isso é pré-requisito de toda medição futura.** Sem ponto fixo, comparar dois reprocess mede o
sorteio junto com a mudança — foi o que me fez perseguir fantasma por várias rodadas.

Custo explícito: **−2 acertos** (`MF/colecoes-arrays`, `MF/classes-parte2`), onde a tag `unit:`
estava certa e o eco a reelegia. Ruling do user (2026-08-19): **manter o corte.**

### Produção NÃO reprocessada — de propósito

Dois reprocess aplicados e revertidos. Resultado real das duas vezes: unidade **127 → 127**
(neutro), bloco intocado, **subunit coerente pior** (133/170 → 121/161), colapsos 3 → 6,
aliases 361 → 259 (limpeza). Uma sentinela do TCC flagra caso que exige revisão manual.

**Não reprocessar antes de trocar a cardinalidade.** O ganho não se materializa e a subunidade
piora, porque o eixo está errado, não o scorer.

---

## D. O caminho definitivo (a razão deste handoff existir)

Metade da infraestrutura **já existe e roda** — na camada de REFERÊNCIAS:

```json
"coverage_units": [
  {"unit_slug": "unidade-02-verificacao-de-programas",
   "topics": ["logica de hoare", "invariante e variante de laco", ...], "confidence": 0.5},
  {"unit_slug": "unidade-01-metodos-formais",
   "topics": ["linguagens de especificacao e logicas", ...], "confidence": 0.375}
]
```

N unidades, N tópicos cada, com confiança. E a régua N:N também existe:
`scripts/eval_coverage.py`, com precision/recall/F1 e exact-set-match.

**E o campo é ESCRITO E NUNCA LIDO.** `coverage_units` tem uma ocorrência em `src/` —
`core/reference_summary.py:135`, a escrita. Zero leituras. Quem alimenta COURSE_MAP,
BIBLIOGRAPHY e a navegação é o single-winner `computed_ref_unit`, espelho do primeiro item.

Terceira instância da classe *"código certo, dano zero, porque ninguém chega lá"* (as outras:
`known_tools`, `TOOL_TOKENS`).

### Os 4 consumidores que precisam mudar

| onde | lê hoje | precisa ler |
|---|---|---|
| `artifacts/repo.py:670-671` | `computed_ref_unit` + `computed_ref_topics` | iterar `coverage_units`, emitindo a ref sob CADA unidade |
| `core/reference_navigation.py:35,49,53` | `computed_ref_unit` (pula se vazio) | agrupar por âncora em N unidades |
| `artifacts/navigation.py:35` (FILE_MAP) | 1ª tag `subunit:` | N tags, ou primária por confiança |
| `ui/dialogs.py:4193` | 1ª tag `subunit:` | idem |

**É aqui que o valor aparece.** Escrever a lista sem trocar o leitor só cria um segundo campo
write-only.

### Sequência proposta

1. **Estender `eval_coverage.py` ao material** (hoje só lê `references_curation.json`).
   Sem régua multi-label não dá para saber se acertou.
2. **[USER] Rotular ~25 arquivos** com o conjunto de unidades/tópicos que cobrem.
   Prioridade: os 13 do ES2 e os 12 do SO — são exatamente os casos disputados, e o rótulo
   decide se são ERRO ou EIXO. É o rótulo mais fácil que existe ("essa prova cai o quê?").
3. **`coverage_units[]` no material**, mesmo formato das referências.
4. **Trocar os 4 consumidores.**
5. Otimizar GATE (6) / SEM-SINAL (5) / ERRO restante, com denominador honesto.
6. **Em paralelo: atacar o BLOCO** — 57%, gold pronto, cardinalidade correta, ninguém mexeu.
   É o único eixo onde "100%" é meta legítima.

---

## E. Cinco previsões minhas REFUTADAS pela medição

Registradas porque o padrão de erro é o achado mais reutilizável desta sessão.

1. **"`known_tools` cega o scorer de bloco em 57% das entries do MF."** Ablação: **0 flips**,
   com e sem LLM. Prova mais forte: `build_content_taxonomy` com o filtro ligado/desligado dá
   JSON **byte-idêntico** nos 5 cursos — o bypass do `topic_code` cobre 100%.
2. **"O voto do LLM compensa o dano."** Repetido com `llm_curation=None`: **0 flips**.
3. **"A auto_tag `bloco:` fecha loop no resolver."** `auto_tags_text` não entra no `content_text`
   (`concept_resolver.py:314`). Errado no lugar apontado — **mas certo um andar acima**, no
   scorer de unidade (seção C).
4. **"O ímã de aliases causa o colapso do IA u05."** Fix medido: aliases `[9,2,2,2]` → `[4,2,2,2]`,
   **colapso 95% → 95%**, régua **−4**. Rejeitado.
5. **"O gate rende +6."** Simulação omitia `learned_unit_boosts` (produção passa,
   `resolver_apply.py:225`). Inflava ~5 pontos. Real: **+3**.

**A causa comum das cinco: reconstruir o caminho à mão em vez de usar o montador canônico.**
Regra que fica: `_build_rich_content_taxonomy`, `_build_file_map_unit_index_from_course`,
`build_learned_unit_boosts`, `manual_unit_slug` — se o harness não passa por todos, o número
mente. Custou a esta sessão três medições inválidas.

---

## F. Achados abertos, por severidade

**Estruturais**
- **`coverage_units` escrito e nunca lido** (seção D).
- **`_infer_tool_candidates` é gerador de anti-tópico** (`semantic_config.py:196`): vocabulário
  auto-inferido do próprio corpus usado como filtro destrutivo. **Dano medido HOJE: zero** — o
  bypass do `topic_code` cobre 100%. Arma carregada, trava acionada.
- **Filtro de ferramenta é SUBTRATIVO** (`content_taxonomy.py:159`): ser ferramenta não deveria
  apagar tópico. Dafny é ferramenta E tópico. Definição operacional extraída do próprio código
  (`concept_resolver.py:158,218`): *ferramenta = instrumento com que a unidade inteira é
  ensinada; discrimina unidade, não discrimina bloco*.
- **Colapso de subunidade**: IA u05 95% · SO u06 100% · SO u02 89%. Causa medida: o tópico
  vencedor duplica o vocabulário da própria unidade. IDF intra-unidade implementado em duas
  variantes e **rejeitado** (dura −2/+3 errado; suave neutra).

**Médios**
- `_extract_tool_candidates` (`content_taxonomy.py:202`) ficou com substring cru enquanto o
  `:101` ganhou fronteira — duas cópias da mesma lógica.
- Segundo parser de tópico sem normalização: `- **1.1** Evolução histórica` →
  `11-evolucao-historica`. **SO: 36 tópicos, 48 tags `topico:`, 0 casando.** Consequência real
  achada pela régua nova: `MF/logicadehoare2` com subtópico `21-logica-de-hoare`, stale.
- IA: 19 tópicos na taxonomia, **0** tags de tópico (parser exige marcador; plano do IA usa
  linha solta).
- 10 de 15 constantes de `thresholds.py` **sem prova de calibração**, incluindo
  `SUBUNIT_TAG=0.60`. `UNIT_MATCH_MIN_WINNER` e `UNIT_MATCH_REL_MARGIN` provados **mortos**
  (resultado idêntico em 72 linhas de sweep).
- Uma correção humana do MF atingia **19 de 67 entries** via prefixos-espelho. Corrigido.
  Segundo registro do mesmo perfil tem `corrected_unit_slug` **vazio**, silenciosamente pulado.

**Pequenos**
- `.tag_catalog.json` git-ignored e não regenerado no rollout.
- `TOOL_TOKENS` citado em comentário (`entry_signals.py:84`) não existe — só em `.pyc` stale.
- `tests/test_taxonomy_topic_loss.py:111-112` pina `Uso de threads` e `Provas de NP-Completude`
  como ferramenta; ambos são tópico.
- Scripts de medição escrevem `last_seen` em `.block_identity.json` — "read-only" que não é.

---

## G. Decisões pendentes do user

- **[DECISION] granularidade da avaliação**: marcar a prova inteira com um conjunto de tópicos
  (barato, determinístico) ou quebrar em questões (caro, LLM, habilita incidência por tópico).
  Aberta desde o handoff anterior. O modelo N:N **adia**, não dispensa.
- **[USER] rotular os ~25 casos disputados** (passo 2 da seção D).
- **[USER] pinos e duplicatas do IA** — herdado do handoff anterior, sem ruling:
  `Cap. Algoritmos Genéticos`, as 3 cópias da P1, entry fantasma `artigo-usando-agrupamento`
  (que a régua nova voltou a flagrar: aponta markdown inexistente).
- **commitar o que está na árvore?** 7 arquivos, suite verde, +5 isolado, ponto fixo garantido.

## I. ESTADO FINAL (2026-08-19b) — a sessão avançou muito depois das seções A–H

> As seções acima descrevem o meio da sessão. Esta descreve onde parou. Onde houver
> divergência, **vale esta**.

### I-1 · A descoberta que mudou o diagnóstico

**O ES2 nunca esteve quebrado.** Contra a régua temporal marcava 8/27 (30%); contra os rótulos
de cobertura, **17/18 (94%)**. A régua é que cobrava a resposta errada.

Consequência para o plano da seção D: **o balde EIXO sumiu quando os rótulos chegaram.** Ele era
artefato da régua temporal, não do modelo 1:1. Logo a cardinalidade N **deixou de ser
pré-requisito** do passo 1 — virou melhoria de modelo, não de acurácia.

### I-2 · Números finais

| eixo | antes | agora |
|---|---|---|
| unidade 1:1 | 127/191 = 66% | **165/191 = 86%** |
| cobertura N:N | não existia | **44/58 = 76%, F1 0,79** |
| bloco | 118/208 = 57% | **118/208 — INTOCADO** |
| idempotência do reprocess | deslocava 2 | **ponto fixo (0)** |
| suite | 1898 | **1904 passed / 1 skipped / 0 falhas** |

Progressão do 1:1: 127 (baseline) → 131 (resumo do Gemini na rota de unidade) → 160 (rótulos:
a régua estava errada) → **165** (bibliografia/cronograma no eixo de unidade).

### I-3 · O que entrou em código nesta sessão

| mudança | onde | efeito medido |
|---|---|---|
| resumo do Gemini na rota de UNIDADE | `resolver_apply.py` | **+4 em produção** |
| bibliografia/cronograma entram no eixo de unidade | `resolver_apply.py` | **+6** |
| `coverage_units[]` no material, 3 regras | `routing/coverage_rules.py` (novo) | **44/58, F1 0,79** |
| eco das auto_tags cortado | `entry_signals.py` | **−2, e ponto fixo** |
| aprendizado ignora prefixos-espelho | `tag_profile.py` | +1 |
| gate `T.UNIT_TAG` 0,65 → 0,50 | `thresholds.py` | +3 |
| poda do glossário (`—`, seção de template, frase ubíqua) | `file_map.py`, `content_taxonomy.py` | +1 |
| guard do bônus fantasma `0 >= 0` | `timeline/index.py` | 0 (corrige defeito) |
| `.smv` como extensão de código | `helpers.py`, `thresholds.py` | 0 hoje, vale no próximo import |

### I-4 · As 3 regras são comportamento, não rótulo

`src/builder/routing/coverage_rules.py` — nenhuma olha nome de arquivo nem de cadeira:

```
A meta       categoria cronograma OU cita o título de >=80% das unidades
B avaliação  título casa P1/Prova2/Lista1 + categoria de avaliação -> unidades citadas
C card       card nomeia unidade/tópico -> a de MAIOR evidência (não todas)
+ fallback   a unidade 1:1 já decidida entra na cobertura
```

**Cadeira nova nasce com isso.** O que continua sendo manual por cadeira é o RÓTULO — e rótulo
serve para medir, não para funcionar.

### I-5 · Os 14 que ainda erram, por causa

```
4  bibliografia   texto depende de rede; a camada de REFERÊNCIA processa a MESMA entry
                  em paralelo e as duas coberturas não se falam. Unificar rende no
                  máximo 1 dos 4 — os outros 3 a referência também não sabe.
6  código         resumo do Gemini raso (~400 chars) para zip de Dafny/Isabelle
4  avaliação      `lista1-gab` não casa o regex · `exercicios` · ENADE
```

### I-6 · Fila revisada (atualizada 2026-08-19d)

> **O item 1 desta lista estava errado.** Eu disse que o bloco estava em 57% e era o elo fraco.
> Está em **172/200 = 86%** — eu media `computed_block_id` cru em vez de `resolve_temporal_block`.
> Os três eixos estão em 86–88%. Investigado e registrado no tracker, seção do bloco.

1. **Os 28 erros de bloco são 26% em avaliação e 43% em meta, contra 9% em material de aula.**
   Duas vias já fechadas por medição: `posting_date` (precisão 41%, é upload em lote) e janela de
   `assign_due` (4 de 37 cards têm o dado). Sem hipótese barata — o sinal que resolveria (quando a
   avaliação foi aplicada) o Moodle não dá.
2. Cachear texto de bibliografia web (4 casos + destrava a camada de referência).
3. Resumo mais rico para zip de código (6 casos).
4. O padrão "título de unidade vence tópico" — explica erros no SO, MF e TCC.
5. Cardinalidade N no resto do sistema (os 4 consumidores da seção D) — agora é melhoria de
   modelo, não pré-requisito.
6. `EXAM_INDEX.md` existe em 1 de 5 cursos, com 10 linhas — decorrência da DECISION de
   granularidade, resolvida no tracker.

### I-7 · Pendências do user

- **commitar**: 13 modificados + 16 novos, suite verde, nada commitado.
- Duplicatas: `lista1-gab` vs `lista-exercicios-p1-gabarito` (11.973 chars idênticos) no SO,
  e as 3 cópias da P1 do IA, herdadas do handoff anterior.
- `[DECISION]` granularidade da avaliação (prova inteira vs por questão) — ainda aberta.

## H. Notas operacionais

- **Heredoc do Bash corrompe conteúdo com `` ` `` e `\n`.** Terceira vez nesta campanha. Para
  markdown/LaTeX/mensagem de commit, usar Write.
- **Reverter produção é `git checkout -- .` nos 5 repos** — nada é commitado pelo reprocess, e
  `manifest.json.bak` fica ao lado.
- **`.claude/worktrees/` deixa `grep -r` lento** (>2 min). Usar a ferramenta Grep, não `grep -r`.
- Hook `code-review-graph` segue crashando com `UnicodeEncodeError` cp1252 — conhecido,
  não-bloqueante.
