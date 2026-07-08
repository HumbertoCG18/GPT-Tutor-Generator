# FASE 1 — Report de fechamento: Gate D4 com recall medido

date: 2026-07-07
branch: `feat/motor-atribuicao` (8 commits `2e49ceb..ccea93c`, base `5fde274`)
plano: `docs/superpowers/plans/2026-07-07-fase1-gate-d4-recall.md`
spec: `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` §6/§7 (FASE 1)
régua externa: `scripts/fase1_recall_gate_MF.py` vs `docs/reports/ground_truth_MF.csv` (repo MF READ-ONLY)

## Números finais (vs referências)

| Métrica | FASE 0 | FASE 1 | Referência |
|---|---|---|---|
| **Recall do gate** (erros flagados / erros ancorados) | 0.682 (15/22) | **0.824 (14/17)** | > 0.577 (proxy MARCO 1 = 15/26) ✅ |
| Confiante-errado (band alta + errado) | 7 | **3** | meta espírito-do-spec = 0; resíduo = decisão TIER 3 (abaixo) |
| Acurácia escopo-disamb (par-colapsada) | 62.1% (36/58) | **70.7% (41/58)** | piso HARD 59.7% ✅ (+8.6pp vs FASE 0) |
| Contenção-fora | 2 | 2 | lacuna do card_block_map real (bloco-09) — pendência USER, não é do gate |
| Gold embutido (CI) | contenção 100% / conf-errado 0 | idem (inviolado) | ✅ |
| Suite | 1689/4 | **1701 passed / 4 skipped** | ✅ |

Vereditos: `fase0_prova_motor_MF.py` **PASS** exit 0 · `fase1_recall_gate_MF.py` **PASS** exit 0.
Review final whole-branch (fable): **With fixes** → fix wave `ccea93c` aplicado e re-verificado.

## O que moveu os números (atribuição honesta por lever)

1. **Desconto nome-do-curso** (Task 3, `MotorContext.course_name`): −2 confiante-errado (os 2 casos
   `logicaproposicional-sintaxe/semantica`, poluição do `topic_text` do bloco-02 "introducao metodos
   formais") **e** +8.6pp de acurácia (o desconto muda TODAS as comparações de janela — flags/média
   errados viraram acertos; população mais ampla que a dos 2 casos confiantes).
2. **Calibração `MARGIN_TAU` 0.45→0.55** (Task 5, grade 36 pontos): −2 confiante-errado
   (`correcaoterminacao`, `provasindutivas-especificacoesrecursivas` rebaixados para flag), recall
   0.706→0.824. Acurácia INVARIANTE em todos os 36 pontos da grade — o gate não toca a seleção.
3. **Gate por token discriminante** (Task 4, D4 literal do spec §3): **neutro neste corpus** — os 5
   confiante-errado da época já carregavam token discriminante; custo medido: 2 decisões corretas
   rebaixadas de "alta" para flag. Mantido por conformidade com o spec (proteção estrutural contra
   vitória só-por-peso), não por ganho medido. Calibrar expectativa disso na FASE 2.

Constantes finais: `MARGIN_TAU=0.55`, `W_SESSION_LABEL=1.0`, `W_TOPIC=0.6`. Baselines renegociados:
probe fase0 `BASELINE_CONFIANTE_ERRADO=3` (era 7); harness fase1 `BASELINE_RECALL=14/17` (fração
exata, evita FAIL espúrio de float) com veredito composto (curadoria que conserta erros FLAGADOS
derruba a razão sem regressão — o guard absoluto é confiante-errado ≤ 3).

## Composição do resíduo (insumo do go/no-go FASE 3 — sign-off condicional §9 do spec)

**(a) Confiante-errado restante (3)** — o gate NÃO pega; todos same-theme (Dafny/verificação/Hoare),
todos gold `discriminante=yes`:

| id | pred | true | nota |
|---|---|---|---|
| exerciciosdafny2 | bloco-11 | bloco-13 | token discriminante presente mas aponta pro bloco errado |
| formalizacaoalgoritmos-invarianteslaco | bloco-11 | bloco-09 | true NEM ESTÁ na janela (é 1 das 2 contenções-fora — curadoria USER bloco-09 resolve a janela; o gate não pode conter o que a janela não contém) |
| hoare | bloco-10 | bloco-13 | mesmo padrão de exerciciosdafny2 |

É exatamente a classe que o spec §3 prevê como não-resolvível por léxico/IDF puro ("resíduo é SEMPRE
same-theme — evidência, não bug") e que o MARCO 1 mediu como a classe que o voto LLM **não** converte
bem (grão-de-semana same-theme → FLAG humano). Expectativa honesta para a FASE 3: desses 3, o LLM
provavelmente converte pouco; a curadoria do bloco-09 resolve 1 deles pela raiz (janela).

**(b) Flagged errados (14)** — candidatos a conversão TIER 3/fila humana: correcaoterminacao,
exercicioscorrecaoinducaomatematica, exercicioscorrecaoterminacao,
exerciciosformalizacaoalgoritmosinvariantes, exerciciosisabelle2, introducao,
provasindutivas-especificacoesrecursivas (+ variantes -arvores/-listas), revisao, arvores,
invariantes, listas, tiposindutivos. A classe "confusão-semântica" dessa lista é a que o MARCO 1
converteu bem (8/18 no flagged cru).

**(c) Flagged certos (23)** — custo de fila (falso-alarme): 37 flagados no total sobre 59 decisões
ancoradas (63% de fila). Trade-off aceito pelo critério lexicográfico do plano (recall/conf-errado
antes de tamanho de fila). **Este é O número a pesar no go/no-go da FASE 3**: sem LLM, são 37 itens
de fila humana no Dashboard; com LLM (cap 20/reprocess), o voto reduz a fila mas gasta API.

**(d) Erros janela-1: 0.** Sem pendência de curadoria nessa dimensão.

## Limitação documentada (para FASE 2/4)

Desconto `course_name` em curso nomeado pelo TÓPICO (ex.: curso "Lógica" com bloco de lógica
proposicional): a remoção é simétrica em todos os blocos, pior caso degrada para vitória com s2=0 →
**flagada, nunca confiante-errado** (blast radius contido, verificado no review final). Registrar no
wiring multi-curso.

## Dívidas que saíram / ficaram

- ✅ Poluição nome-do-curso (resolvida, Task 3). ✅ Protocols/shadowing (Task 6). ✅ Unificação
  `_card_entry`↔`card_block` (Task 7). ✅ Baseline consciente 7→3.
- Fica: hardening MotorContext (YAGNI, sem crash conhecido); memoização de `normalized_card_map`
  no MotorContext (adiar para FASE 4, escala de integração); pendência **[USER]** curadoria
  bloco-09 no card_block_map do repo MF (resolve 1 contenção-fora E 1 confiante-errado).

## Próximo

FASE 2 (providers P3 SO / P4 TCC) é a próxima fase do spec §7. Go/no-go da FASE 3 (LLM) é decisão
do USER com este report em mãos (condição do sign-off §9); sem LLM, flagged = fila humana no
Dashboard (37 itens no MF hoje).
