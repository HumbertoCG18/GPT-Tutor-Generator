# Diagnóstico sessão-vs-bloco (gold de unidades) — 2026-08-08

Pergunta do user: "gold por sessão não seria melhor? e há discrepância SARC × blocos?"
Método: READ-ONLY, 5 cursos; SYLLABUS.md (SARC importado) × sessões do índice data a data;
argmax de unidade POR SESSÃO (tokens do label × assinatura U1-limpa) × unidade do bloco.
Script: `diagnostico_sessoes.py` (scratchpad da sessão).

## A) Integridade SARC × índice: PERFEITA nos 5 cursos

| Curso | Linhas SYLLABUS | Numeradas (`#`) | Sem `#` | Sessões no índice | Datas divergentes |
|---|---|---|---|---|---|
| MF | 40 | 37 (max #37) | 3 (suspensão 20/04, devolução 13/07, G2 15/07) | 40 | **0** |
| SO | 40 | 35 | 5 (3 feriados, G2, 16/07 vazia) | 40 | **0** |
| ES2 | 20 | 17 | 3 (2 feriados, G2) | 20 | **0** |
| IA | 40 | 37 | 3 (suspensão, G2, 15/07 vazia) | 40 | **0** |
| TCC | 40 | 36 | 4 (2 feriados, atendimento, G2) | 40 | **0** |

**A dúvida "SARC vai até 37, gold só tem 17" resolvida por completo**: o `#` do SARC NÃO
numera suspensões/feriados/G2/devolução — MF tem 37 numeradas + 3 sem número = 40 linhas, e o
índice tem EXATAMENTE as mesmas 40 datas (zero faltando, zero sobrando, zero duplicada, nos 5
cursos). Nenhuma aula foi perdida em curso nenhum. O gold tem menos LINHAS porque 1 linha = 1
bloco (agregado por assunto), e provas ficam fora por design.

## B) Straddle medido (sessão cujo sinal aponta unidade ≠ vizinhas do mesmo bloco)

- **SO bloco-03 = o ÚNICO straddle REAL dos 82 blocos**: 10-17/03 → u01 (scores 3-5, margens
  3-4 = sinal FORTE) e 19-31/03 → u02 (scores 2-4). Troca de unidade no meio de bloco de 7
  sessões. Exatamente o caso que o user apontou preenchendo o gold.
- MF (3 flags) e ES2 (1 flag): TODOS artefatos de score 1 / margem 1 — o token genérico
  `exercicios` casando assinatura de outra unidade. Sessões "Exercícios" pertencem ao conteúdo
  que as cerca; o grão-bloco absorve esse ruído automaticamente. (Mesma família do lever A
  descartado na spec-review: `exercicios` como sinal é migalha.)
- IA e TCC: **0 straddle**.

## C) Por que gold POR SESSÃO perde (provas concretas)

1. **Cobertura: ganho ZERO.** (A) prova que nenhuma sessão está faltando no grão-bloco — os
   180 rows de sessão já estão TODOS dentro dos 82+21 blocos.
2. **Sessão não tem output do sistema pra comparar.** Schema real da sessão:
   `['date', 'id', 'kind', 'label', 'signals']` — SEM `unit_slug`. O motor atribui unidade
   por BLOCO (`assign_units_positional`). Gold por sessão mediria uma camada que o sistema
   não produz; pra ser medível exigiria construir atribuição por sessão só pra régua
   (inverte a relação régua↔sistema). Lição já paga: gold IA em grão-subtópico ≠ grão do
   pipeline → 21 materiais inscoráveis (tracker, mundo-63).
3. **Custo 2.2× pra consertar 1/82.** ~180 linhas de rotulagem em vez de 82, sendo que o
   único caso real que o grão-bloco não expressa (SO bloco-03) já está coberto pelo
   protocolo de notes (corte por data), que é EXATAMENTE o insumo que a re-segmentação da
   cura SO precisa.
4. **Por sessão FORÇARIA decisão onde o sinal é mais fraco.** As 16 "discordâncias" de sessão
   medidas são majoritariamente sessões "Exercícios" (score 1) — no grão-sessão o rotulador
   teria que decidir unidade para cada uma delas isoladamente; no grão-bloco elas herdam o
   contexto. O bloco é a unidade pedagógica certa: professor agrupa por assunto.
5. **Estabilidade de chave é equivalente na prática.** `block_uuid` sobrevive a reprocess;
   re-segmentação (SO, T9) órfã apenas os blocos re-cortados — cujas verdades por data já
   estão nas notes. Migrar tudo pra chave-data por causa disso é pagar o custo total por um
   benefício que as notes dão de graça.

## Veredito

Gold **por bloco confirmado com dados**. Único débito real do grão: SO bloco-03 (straddle
verdadeiro) → protocolo notes com corte por data (acordado 2026-08-08) + re-segmentação na
cura SO (T9, já prevista com HALT). Nada a mudar no tooling da campanha.
