# FASE 2 — Providers P3 (SO) + P4 (TCC): report de fechamento

date: 2026-07-09
branch: feat/motor-atribuicao
commits: `985351b..9119ac4` (Tasks 1-6, FASE 2 completa)

## Aceite (spec §6) vs medido

| Critério | Spec | Medido | PASS |
|---|---|---|---|
| P3 contenção (colisão) | data → exatamente 1 bloco, 0 colisão | SO: 0 colisões em 19 datas resolvidas | ✅ |
| P3 cobertura | ~45% materiais SO | SO: 45.2% (19/42) | ✅ |
| P4 pinos | ≥4/5 reproduzidos (interseção) | TCC: 5/5 (contenção total 3/5, métrica secundária) | ✅ |
| P4 cobertura | >26% | TCC: 83.3% (30/36) | ✅ |
| Confiante-errado novo | 0 | SO: 0 · TCC: 0 | ✅ |
| Regressão MF | fase0+fase1 PASS | MF intacto: acc 82.8%, contenção 0, confiante-errado 1, recall 0.900 — fase0/fase1 PASS em toda a FASE 2 (Tasks 5 e 6) | ✅ |

Suite completa: **1722 passed / 4 skipped / 0 failed** (`python -m pytest tests -q`, medido na Task 6 após fix do teste de contrato desatualizado herdado da Task 3).

## Constantes calibradas

### `DATE_DF_MAX` (gate D4 de concordância, janela-1 do provider `data`/P3)

Grade testada na régua externa SO (protocolo D4), edição/reversão transiente sem diff residual:

| `DATE_DF_MAX` | cobertura | colisões | matriz gate (resto-err, resto-ok, alta-ok) | confiante-errado | veredito |
|---|---|---|---|---|---|
| 1 | 45.2% (19/42) | 0 | (4, 7, 8) | 0 | PASS |
| **2 (vigente)** | 45.2% (19/42) | 0 | (4, 2, 13) | 0 | PASS |
| 3 | 45.2% (19/42) | 0 | (4, 2, 13) | 0 | PASS |

Cobertura/colisões/contenção da janela P3 são invariantes a `DATE_DF_MAX` — o parâmetro só afeta
o gate D4 pós-janela. `alta-ok` empata entre 2 e 3 (13, máximo da grade); `1` estrangula o gate
(8, mais decisões empurradas pra "resto"/flag). Critério do protocolo (maximizar `alta-ok` com
confiante-errado 0) escolhe {2, 3}; desempate pela constante já vigente (validada também na régua
MF da FASE 1) → **mantido `DATE_DF_MAX=2`**. Nenhuma mudança funcional; comentário do código
atualizado (`src/builder/routing/motor/disambiguator.py`, linhas 82-87) documentando a grade.

### `TOPIC_STEM_LEN` / `TOPIC_MIN_TOKEN` (provider `topic`/P4)

**Mantidas em `TOPIC_STEM_LEN=6`, `TOPIC_MIN_TOKEN=3`** (fixadas na Task 4 + fix de review `54c14aa`).
Grade de calibração do Step 2 do brief **não disparou** — o probe TCC passou 5/5 pinos (≥4/5, piso
já atingido) na primeira rodada, sem necessidade funcional de mudança. O stem-prefix-6 já leva
"NP-completude" a casar por stem "comple" (era o 5º pino que falhava no dry-run cru da Task 4).
`TOPIC_MIN_TOKEN` piso-2 permanece **no-op estrutural**: a assinatura de bloco tem piso-3 nos dois
lados, então baixar o piso do provider sozinho não muda nada — ver risco residual #3 abaixo.

## Composição do resíduo (insumo go/no-go FASE 3)

### SO (P3 — data-no-nome)

Escopo: 42 rows gold. Cobertura P3 (janela via `provider_date`): **19/42 = 45.2%**. Dos 19 com
janela resolvida, a cascata completa produziu decisão em **19/19** (100% via provider `data` —
`providers das decisões: {'data': 19}`, sem contaminação de manual/labels/topic). Matriz gate:

- **alta (não-flag), 13/19** — todas corretas (confiante-errado = 0).
- **resto (flag), 6/19** — 4 erradas + 2 corretas por acaso (band baixa não garante erro; só não é
  confiante).

Acurácia motor par-colapsada (com-janela): **77.8% de 18 pares** vs baseline funil **47.4%**.
Os 4 "resto-err" batem exatamente com os 4 "out" da contenção de janela (`0206-laminas-gerencia-de-
i-o-livro-texto`, `0206-laminas-mecanismos-de-interrupcao`, `2306-laminas-gerencia-de-arquivos`,
`2306-laminas-laminas-armazenamento-em-massa`) — o gate D4 corretamente não os marca `alta`, daí
confiante-e-errado = 0. Os 23/42 rows restantes ficam fora do escopo P3 (sem data-no-nome
resolvível) ou fora de escopo de disambiguação — vão pro funil/outros providers do motor
(fora do recorte deste probe).

### TCC (P4 — topic-bridge)

Escopo: 36 rows gold. Cobertura P4 (janela via `provider_topic`): **30/36 = 83.3%**. Pinos manuais
(`.card_block_map` `source=manual`) reproduzidos por interseção da janela P4: **5/5** (piso 4/5);
contenção total (janela P4 ⊇ todos os blocos do pino) mais estrita: **3/5** — "NP-completude" perde
bloco-21 (interseção só em bloco-22) e "Halteproblem" perde bloco-10 (interseção só em bloco-11);
métrica secundária, sem piso no aceite.

Na cascata completa (36 rows − fora-de-escopo), **28 decisões**: `providers das decisões:
{'topic': 20, 'manual': 8}`. Breakdown por provider (por caso, não par-colapsada):
- **manual: 8/8 = 100%** (0 erro)
- **topic: 16/20 = 80%** (4 erros — nenhum confiante-errado, todos caem na fila de flag)

Acurácia motor par-colapsada (com-janela): **84.2% de 19 pares** vs baseline funil **56.0%**.
O headline par-colapsada é agregação de manual (perfeito) + topic (80%) — a linha de breakdown por
provider existe exatamente para não esconder essa mistura (fix de review, commit `9119ac4`).

## Riscos residuais (achados de review da FASE 2)

1. **[Task 3, Important-registro]** O ramo flagado do gate de concordância de data hardcoda
   `band="media"`: silêncio lexical total e overlap-boilerplate caem na mesma band — perda de
   granularidade de triagem da fila de flag do SO. Não é bug; documentado para não confundir na
   FASE 3/5 (a fila de flag do SO não distingue "sem sinal nenhum" de "sinal fraco/ambíguo").
2. ~~**[Task 6, Minor]** Janela-1 vinda de provider `"topic"` não passa pelo gate D4~~ **RESOLVIDO
   (2026-07-09, pós-review-final, autorização do user):** gate estendido a `provider in ("data",
   "topic")` (`_gated_window1_decision`, ex-`_date_window1_decision`). Motivo: o review final provou
   que o shape existe hoje (Halteproblem → `p4=['bloco-11']`, mascarado pelo pino manual P1 — drift
   de pino viraria alta-cega silenciosa). Mudança estruturalmente segura (só rebaixa alta→flag, nunca
   cria confiante-errado). Regressão: suite 1724 passed/0 failed (+2 testes), 4 probes PASS com
   números idênticos.
3. **[Task 4]** `TOPIC_MIN_TOKEN` piso-2 é **no-op estrutural** — a assinatura de bloco (usada pelos
   dois lados do match) já tem piso-3, então baixar o piso do provider sozinho não abre tokens
   curtos. Se calibração futura exigir tokens curtos (ex.: `np`, `t2`), o caminho correto é dar ao
   P4 assinatura própria nos DOIS lados (material e bloco), não só ajustar a constante do provider.
4. **Réguas SO/TCC medem acurácia WHOLE-CASCADE por design** (mesmo padrão FASE 0/1, não
   isolado-por-provider) — cada probe expõe uma linha `providers das decisões` que denuncia mistura
   de manual/labels/data/topic no headline, prevenindo leitura enganosa da acurácia agregada.
5. **Contenção total de pinos 3/5** (interseção 5/5 é o critério de aceite) — relevante se a FASE 3+
   exigir contenção dura de pinos multi-bloco; hoje janelas P4 largas (até 8 blocos, pino "Revisão
   para P1") seguram sem confiante-errado, mas a fila de flag tende a crescer.
6. **Defer FASE 4:** memoização de `_global_df` / `_modal_years` / `normalized_card_map` — todos
   recomputados por chamada hoje; sem impacto de correção, só de custo, adiado até a integração real
   ao pipeline.

## Fila humana consolidada (MF + SO + TCC)

| Curso | Decisões na cascata | Flag=True (fila humana) | Flag=False (banda alta) | Como foi obtido |
|---|---|---|---|---|
| MF | 65 (37+28) | **37** | 28 | `scripts/fase1_recall_gate_MF.py` — "fila do flag: 37 flagados, 28 certos" (output direto do report FASE 1) |
| SO | 19 | **6** | 13 | Derivado da matriz gate do report da Task 5 (`resto-err`=4 + `resto-ok`=2 = 6 flagados; `alta-ok`=13 = 13 não-flagados). Confirmado por re-execução read-only do probe instrumentado com contagem direta de `d.flag` (`AnchorDecision.flag`): flag=True 6, flag=False 13, 0 mismatch contra a regra `flag == (band != "alta")` que o código de `disambiguate()`/`_date_window1_decision()` garante estruturalmente (decisão flagada nunca sai da band alta). |
| TCC | 28 | **22** | 6 | O report da Task 6 não expõe banda/flag diretamente (só providers+accuracy). Derivado por re-execução read-only do probe instrumentado (`AnchorEngine.resolve` sobre as 36 rows do gold, mesma cascata do `fase2_prova_TCC.py`): `band_count={'media': 14, 'baixa': 8, 'alta': 6}` → flag=True (media+baixa) = 22, flag=False (alta) = 6; 0 mismatch contra a regra `flag == (band != "alta")`. |

**Fila humana consolidada (go/no-go FASE 3): 37 + 6 + 22 = 65 flagados.**

Nota de método: a régua `flag == (band != "alta")` não é suposição — é garantida estruturalmente
pelo código (`_date_window1_decision`: `band="alta"` só quando `flag=False` e vice-versa;
`disambiguate`: `flag=not confident` e `confident` é a única condição que produz `band="alta"`,
com o comentário explícito "decisão flagada NUNCA carrega band alta"). A re-execução confirmou
mismatch=0 nos dois cursos, então a derivação por matriz/band é equivalente a contar `flag=True`
diretamente.

## Referências

- `docs/superpowers/sdd/task-5-report.md` — probe SO + calibração `DATE_DF_MAX`.
- `docs/superpowers/sdd/task-6-report.md` — probe TCC + fix de contrato + breakdown de providers.
- `scripts/fase2_prova_SO.py`, `scripts/fase2_prova_TCC.py` — réguas HARD permanentes (exit 0/1),
  parte da infraestrutura de regressão do motor, re-executadas a cada fase futura.
- `docs/reports/2026-07-07-fase1-recall-report.md` — baseline MF (recall do gate, fila de flag 37).
