# FASE 3 — voto LLM TIER 3: report de fechamento

date: 2026-07-09
branch: feat/motor-atribuicao
commits: `512afcd..c70c272` (Tasks 1-5: cache, série same-theme, `LlmVoter`, hook no `AnchorEngine`,
régua HARD `fase3_prova_LLM_MF.py`) + esta rodada (Task 6, medição real)

## Veredito

**FAIL honesto** (lift +1, piso +4). Confiante-errado = 0 (piso cumprido). Rodada completa
(0 pendências de cap). Por regra do plano (spec §12 regra 4), **NÃO iterei o prompt** — o resultado
abaixo é a medição real, sem tentativa de prompt-engineering. Decisão go-forward é do user (ver
"Recomendação" no fim).

| Critério (spec §7) | Piso | Medido | OK |
|---|---|---|---|
| Lift no escopo do voto (flagged ∪ série) | ≥ +4 | **+1** (34/44 → 35/44) | ❌ |
| Confiante-errado novo (band alta, global) | 0 | **0** | ✅ |
| Rodada completa (sem pendência de cap) | sim | **sim** (48/48 votos cacheados) | ✅ |

## Bloqueio de infraestrutura encontrado e corrigido

A 1ª rodada real (20/20 chamadas) retornou **erro em 100% dos casos** — não é a classe
"grão-de-semana" prevista no plano, é infraestrutura: o modelo `gemini-2.5-flash` (hardcoded no
plano/`DEFAULT_MODEL` de `gemini_client.py` e no campo `gemini_model` do
`~/.gpt_tutor_config.json`) responde `404 NOT_FOUND` ("This model ... is no longer available")
neste ambiente — aposentado para `generateContent` (ainda aparece em `models.list()`, mas não serve
mais requests). Diagnosticado com uma chamada direta fora do harness (reproduziu o 404
byte-a-byte); testei os aliases correntes e `gemini-flash-latest` respondeu OK.

**Fix aplicado**: editado `gemini_model` em `~/.gpt_tutor_config.json` de `gemini-2.5-flash` →
`gemini-flash-latest` (alias estável do Google pro modelo flash corrente; mesma classe/preço).
Arquivo pessoal fora do repo, não versionado — nenhum código do projeto foi tocado. Como erros de
API **não são cacheados** (`llm_vote.py:221-223`), a 1ª rodada não sujou o cache (0 votos gravados
com erro); as rodadas seguintes re-tentaram os mesmos 30 itens do zero, já com o modelo corrigido.
**Atenção FASE 4 / próxima medição**: o plano (`docs/superpowers/plans/2026-07-09-fase3-voto-llm.md`)
e o código ainda citam `gemini-2.5-flash` como padrão — se o `gemini_model` do config for resetado,
o mesmo 404 volta.

## Números finais

- **Chamadas API por rodada**: rodada 1 = 20 (20 erros 404, 0 sucesso, 0 cacheado) · rodada 2 = 20
  (0 erros, 20 cacheados) · rodada 3 = 10 (0 erros, 10 cacheados) → **total de chamadas tentadas: 50**;
  **chamadas úteis/cacheadas: 30** (+ 18 seed MARCO 1 = 48 votos no cache final).
- **Custo estimado**: as 20 chamadas da rodada 1 falharam no cliente antes de gerar conteúdo (404
  imediato, sem geração) — custo ≈ 0. As 30 chamadas bem-sucedidas usam prompt truncado em
  `MD_PROMPT_CAP=3500` chars (~900-1300 tokens de entrada com o bloco de candidatos) + saída
  estruturada curta (schema `Voto`, ~100-150 tokens). Volume total ≈ 40-50k tokens no tier
  flash. **Estimativa: bem abaixo de US$0,05** (não verificado contra dashboard de billing — é
  estimativa por volume de token, não fatura real; segue folgado dentro do teto de US$1
  autorizado).
- **Confiante-e-errado (band alta, global)**: **0** — o único resíduo herdado de FASE 0/1/2
  (`exerciciosdafny2`, banda alta, errado desde o MARCO 0) foi **resolvido pelo voto** (LLM acertou
  bloco-13; aceitação cega rebaixa a banda pra `media`/`provider=llm`, então some da contagem de
  confiante-errado). É o único ganho líquido do lift.
- **Acurácia global escopo-disamb par-colapsada**: **antes** (sem voto, medido por
  `fase0_prova_motor_MF.py` na mesma rodada) = 48/58 = 82.8%. **Depois** (com voto TIER 3,
  medido pelo próprio `fase3_prova_LLM_MF.py`) = **49/58 = 84.5%** (+1 par, +1.7pp).

### Por que o lift ficou tão abaixo do piso — achado central desta fase

O escopo do voto (44 rows) tem duas origens distintas, e elas se comportam **de forma oposta**:

| Sub-escopo | n | det ok | llm ok | lift |
|---|---|---|---|---|
| **Flagged** (band ≠ alta — a fila humana que a TIER 3 deveria reduzir) | 37 | 28 | 28 | **0** |
| **Série same-theme não-flagada** (band alta, entrou só por ser série ordinal) | 7 | 6 | 7 | **+1** |
| **Total** | 44 | 34 | 35 | **+1** |

O lift inteiro veio do lado da série (a correção pontual de `exerciciosdafny2`). **No lado que
importa — a fila flagada — o voto LLM teve saldo líquido ZERO**: 4 acertos novos anularam
exatamente 4 erros novos (ver tabela completa abaixo). Isso contrasta com o MARCO 1 original
(prompt mais específico, gold pré-correção): lá o flagged (18 casos, baseline muito pior, 15/18
errado) foi de 3/18 → 8/18 (+5 líquido). Duas explicações não-excludentes: (a) o piso +4 foi
calibrado sobre um baseline determinístico que a FASE 0/1 já melhorou bastante (82.8% par-colapsado
hoje vs muito pior no MARCO 1 cru) — sobrou menos "gordura" fácil pro LLM converter; (b) o prompt
generalizado (`build_vote_prompt`, cross-curso) pode não ser tão eficaz no MF quanto o prompt
mais específico do MARCO 1 — não testei essa hipótese (proibido iterar prompt por spec §12 regra 4),
fica registrada para decisão do user.

## Tabela det vs LLM — as 44 rows do escopo do voto (rodada completa)

`ok`/`X` = acerto/erro contra `true_block_id`. Todas resolvidas via `method=llm` (voto aceito cego
no escopo, spec §12 regra 3) — mesmo quando o voto confirma o valor determinístico.

| id | det | ok? | llm | ok? | true | obs |
|---|---|---|---|---|---|---|
| correcaoterminacao | bloco-11 | ok | bloco-11 | ok | bloco-11 | — |
| exercicioscorrecaoinducaomatematica | bloco-05 | ok | bloco-05 | ok | bloco-05 | — |
| exercicioscorrecaoterminacao | bloco-11 | ok | bloco-12 | **X** | bloco-11 | regressão (flagged) |
| exerciciosdafny1 | bloco-12 | ok | bloco-13 | **X** | bloco-12 | regressão (flagged + série) |
| exerciciosdafny2 | bloco-11 | X | **bloco-13** | **ok** | bloco-13 | correção — resíduo confiante-errado FASE 0/1 resolvido |
| exerciciosdafny3 | bloco-13 | ok | bloco-13 | ok | bloco-13 | — |
| exerciciosdafny4 | bloco-13 | ok | bloco-13 | ok | bloco-13 | — |
| exerciciosdafny5 | bloco-15 | ok | bloco-15 | ok | bloco-15 | — |
| exerciciosespecificacao | bloco-03 | ok | bloco-03 | ok | bloco-03 | — |
| exerciciosespecificacao-respostas | bloco-03 | ok | bloco-03 | ok | bloco-03 | — |
| exerciciosformalizacaoalgoritmosinvariantes | bloco-11 | ok | bloco-11 | ok | bloco-11 | — |
| exerciciosformalizacaoalgoritmosrecursao2 | bloco-04 | ok | bloco-04 | ok | bloco-04 | — |
| exerciciosformalizacaoalgoritmosrecursao3 | bloco-04 | ok | bloco-04 | ok | bloco-04 | — |
| exerciciosisabelle2 | bloco-05 | X | **bloco-06** | **ok** | bloco-06 | correção (cluster indução×Isabelle) |
| exercicioslogicatemporal | bloco-16 | ok | bloco-16 | ok | bloco-16 | — |
| formalizacaoalgoritmos-recursao2 | bloco-04 | ok | bloco-04 | ok | bloco-04 | — |
| formalizacaoalgoritmos-recursao3 | bloco-04 | ok | bloco-04 | ok | bloco-04 | — |
| introducao | bloco-01 | X | **bloco-02** | **ok** | bloco-02 | correção |
| logicadehoare | bloco-10 | ok | bloco-10 | ok | bloco-10 | — |
| logicadehoare2 | bloco-10 | ok | bloco-11 | **X** | bloco-10 | regressão (flagged) |
| logicapredicados-semantica | bloco-03 | ok | bloco-03 | ok | bloco-03 | — |
| logicapredicados-sintaxe | bloco-03 | ok | bloco-03 | ok | bloco-03 | — |
| logicaproposicional-semantica | bloco-03 | ok | bloco-03 | ok | bloco-03 | — |
| logicaproposicional-sintaxe | bloco-03 | ok | bloco-03 | ok | bloco-03 | — |
| provasindutivas-especificacoesrecursivas | bloco-05 | X | bloco-05 | X | bloco-06 | grão-de-semana (não converteu) |
| provasindutivas-especificacoesrecursivas-arvores | bloco-05 | X | bloco-05 | X | bloco-06 | grão-de-semana (não converteu) |
| provasindutivas-especificacoesrecursivas-listas | bloco-05 | X | bloco-05 | X | bloco-06 | grão-de-semana (não converteu) |
| revisao | bloco-02 | X | **bloco-03** | **ok** | bloco-03 | correção |
| arvores | bloco-05 | X | bloco-05 | X | bloco-06 | grão-de-semana (não converteu) |
| classes-parte1 | bloco-15 | ok | bloco-15 | ok | bloco-15 | — |
| classes-parte2 | bloco-15 | ok | bloco-15 | ok | bloco-15 | — |
| colecoes-arrays | bloco-13 | ok | bloco-13 | ok | bloco-13 | — |
| colecoes-conjuntos | bloco-13 | ok | bloco-13 | ok | bloco-13 | — |
| colecoes-sequences | bloco-13 | ok | bloco-13 | ok | bloco-13 | — |
| exemplos | bloco-06 | ok | bloco-06 | ok | bloco-06 | — |
| exemplos-zip | bloco-16 | ok | bloco-16 | ok | bloco-16 | — |
| exercicios-arrays | bloco-13 | ok | bloco-13 | ok | bloco-13 | — |
| exercicios-conjuntos | bloco-13 | ok | bloco-13 | ok | bloco-13 | — |
| intro | bloco-06 | ok | bloco-06 | ok | bloco-06 | — |
| introducao-zip | bloco-12 | ok | bloco-12 | ok | bloco-12 | — |
| invariantes | bloco-11 | ok | bloco-11 | ok | bloco-11 | — |
| listas | bloco-05 | X | **bloco-06** | **ok** | bloco-06 | correção (cluster indução×Isabelle) |
| terminacao | bloco-12 | ok | bloco-11 | **X** | bloco-12 | regressão (flagged) |
| tiposindutivos | bloco-10 | X | bloco-13 | X | bloco-15 | não converteu (código sem léxico no roteiro) |

**Resumo**: 5 correções (`exerciciosdafny2`, `exerciciosisabelle2`, `introducao`, `revisao`, `listas`)
− 4 regressões (`exercicioscorrecaoterminacao`, `exerciciosdafny1`, `logicadehoare2`, `terminacao`)
= **+1 líquido**. 5 casos seguem errados nos dois lados (o núcleo do cluster indução×Isabelle
05↔06 — 4 casos — mais `tiposindutivos`, que é um caso à parte, sem léxico no roteiro do professor).
Nota: 2 dos 6 casos do cluster indução×Isabelle citados no relatório FASE 1 (`exerciciosisabelle2` e
`listas`) **converteram** nesta rodada — a categorização "grão-de-semana = 100% não-conversível" do
relatório FASE 1 era otimista; o núcleo duro (`provasindutivas-*` ×3 + `arvores`) continua resistente.

## Decisões de calibração mantidas (herdadas do spec §12, reconfirmadas nesta medição)

- **Sem-janela não vota**: confirmado programaticamente — `plano` (plano.pdf) é
  `is_out_of_disamb_scope=True` → `AnchorEngine.resolve` retorna `None` → nunca entra em
  `scope_rows`/`vote_rows`, nunca chama o voter. Classe **plano.pdf permanece perdida** por
  desenho (funil-piso responde), como documentado no spec e no plano; nenhuma mudança nesta fase.
- **Autoconfiança do LLM ignorada por gate**: campo `confianca` gravado no cache só para auditoria
  (48/48 votos têm o campo preenchido); nenhum código de decisão o lê — confirmado por inspeção do
  hook (`AnchorEngine`/`LlmVoter.vote`), sem teste novo necessário (comportamento herdado da Task 4).
- **Aceitação cega no escopo**: todo voto válido (dentro da janela) substituiu a escolha
  determinística, inclusive quando pior — é o mecanismo por trás das 4 regressões acima. Não é bug;
  é a regra aprovada no sign-off §9/§12. O número desta fase é exatamente a medição dessa regra em
  produção-simulada.
- **Cache por identidade de conteúdo (md5)**: 48 votos cacheados, nenhuma colisão de chave
  observada; write atômico (`tmp` + `os.replace`) não gerou nenhum arquivo `.tmp` órfão ao final.

## Riscos residuais (com dono)

1. **[DECISION/USER] Prompt generalizado entrega saldo zero na fila flagada** — achado central
   desta fase (ver seção acima): 37 rows flagados, 28→28 (lift 0). O ganho total (+1) veio de fora
   da fila flagada (série `exerciciosdafny2`). Se o objetivo de produto da TIER 3 é reduzir a fila
   humana de 65 flagados (MF 37 + SO 6 + TCC 22, `pendencias.md`), **esta medição não sustenta
   esse objetivo no MF**. Decisão do user: aceitar o resultado como está (lift menor, revisão de
   piso com sign-off) ou reverter o GO (flags voltam 100% pra fila humana).
2. **[CODE] Série same-theme votando sobre banda alta — risco NÃO materializado nesta medição**
   (citado como risco a monitorar no plano/FASE 2). Medido: 7 rows série-não-flagados, 6→7,
   **0 novo confiante-errado**. Nesta amostra pequena (n=7) o mecanismo ajudou (corrigiu
   `exerciciosdafny2`); segue como risco a re-medir com mais dados (SO/TCC na FASE 4), não como
   fato estabelecido — n=7 é amostra frágil para generalizar.
3. **[CODE] Modelo hardcoded `gemini-2.5-flash` está aposentado** — ver seção "Bloqueio de
   infraestrutura" acima. Fix aplicado só no config pessoal (`~/.gpt_tutor_config.json`); o
   `DEFAULT_MODEL` em `src/builder/runtime/gemini_client.py` e a menção no plano
   `2026-07-09-fase3-voto-llm.md` continuam citando o modelo aposentado. Sem dono definido para
   corrigir o código-fonte — registrar para quem tocar `gemini_client.py` de novo (fora do escopo
   desta task, que só roda/mede).
4. **[CODE] Cluster indução×Isabelle (05↔06) parcialmente convertível** — 2/6 casos do cluster
   nomeado na FASE 1 converteram nesta rodada (ver nota na tabela). Contradiz a categorização
   binária "grão-de-semana = não-conversível" — o comportamento é mais parecido com "conversão
   instável/dependente do prompt exato" do que "impossível por desenho". Não é motivo para
   iterar o prompt agora (regra §12.4), mas é sinal para quem decidir a FASE 4 do voto.

## O que fica para FASE 4 (fora do escopo desta task)

- **Sidecar `material_curation.json` no repo-tutor via reprocess** — hoje o cache vive só em
  `docs/reports/material_curation_MF.json` (medição, READ-ONLY no repo-tutor); produção precisa do
  sidecar gravado no repo real via pipeline de reprocess.
- **Background-thread na GUI** para não bloquear a UI durante chamadas de voto.
- **Prune de chaves órfãs** no cache (conteúdo que saiu do manifest) — adiado desde a Task 1
  (auto-review do plano, item de risco #(c)).
- **Cap/opt-in por curso via `SubjectProfile.feature_flags`** — hoje o cap é global
  (`DEFAULT_CAP=20`) e o voter é chamado incondicionalmente pelo harness; produção precisa de
  opt-in por curso.
- **Decisão sobre o achado desta fase** (prompt generalizado com saldo zero na fila flagada) —
  se a FASE 4 for adiante, vale reavaliar se o voto TIER 3 deve ser condicionado a alguma
  característica do flag (ex.: só rodar em bandas muito baixas, ou só em séries) em vez de
  "todo flagged ∪ série" uniformemente — mas isso é code novo/prompt novo, fora do escopo desta
  medição (spec §12.4 proíbe iterar agora).

## Regressão total (Step 5)

```
python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py && \
python scripts/fase2_prova_SO.py && python scripts/fase2_prova_TCC.py && \
python scripts/fase3_prova_LLM_MF.py && python -m pytest -q
```

| Probe | Veredito | Números-chave |
|---|---|---|
| FASE 0 (`fase0_prova_motor_MF.py`) | **PASS** | escopo-disamb 48/58=82.8%, contenção-fora 0, confiante-errado 1 (baseline consciente, SEM voter) |
| FASE 1 (`fase1_recall_gate_MF.py`) | **PASS** | acc/recall dentro do piso (SEM voter, números intactos) |
| FASE 2/P3 SO (`fase2_prova_SO.py`) | **PASS** | cobertura 45.2%, colisões 0, confiante-errado 0 |
| FASE 2/P4 TCC (`fase2_prova_TCC.py`) | **PASS** | cobertura 83.3%, pinos 5/5, confiante-errado 0 |
| FASE 3 (`fase3_prova_LLM_MF.py`, re-rodado 100% cache, 0 chamadas novas) | **FAIL** (honesto) | lift=+1 confErrado0=True completo=True |
| `pytest -q` | **0 failed** | 1743 passed, 4 skipped |

fase0-2 rodaram sem o voter (por construção não usam `LlmVoter`) — números idênticos aos das fases
anteriores, confirmando 0 regressão cruzada. FASE 3 re-rodada aqui é 100% cache hit (0 chamadas
novas), reconfirmando o veredito FAIL sem gastar API de novo.

## Recomendação ao user (decisão go-forward)

O número real é **lift +1** (piso +4), com **0 confiante-errado** e rodada **completa**. Não
iterei o prompt (regra §12.4 — grão-de-semana/prompt já é o que é, medido). Duas opções, ambas
compatíveis com os dados:

1. **Aceitar o resultado e revisar o piso com sign-off** — o ganho real (fechar o único
   confiante-errado residual, +1.7pp global) tem valor mesmo sem bater +4; mas note que isso não
   sustenta o objetivo original de reduzir a fila flagada (saldo 0 lá).
2. **Reverter o GO da TIER 3** — flagged volta 100% pra fila humana no Dashboard; dívida #1
   (granularidade de band no ramo flagado, `pendencias.md` risco residual #1 da FASE 2) fica
   **aberta**, sem N/A — nada na TIER 3 resolveu isso, já que ela não mexe em band, só substitui a
   escolha por aceitação cega.

Dívida #1 (band no ramo flagado): como o veredito é **FAIL**, ela **permanece aberta**, apontando
para a re-decisão do user (não é N/A — N/A só se aplicaria em caso de PASS, quando a TIER 3
"consome" o flag e tornaria a granularidade de band irrelevante para essa fila).
