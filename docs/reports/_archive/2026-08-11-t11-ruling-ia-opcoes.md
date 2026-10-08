# T11 — Ruling IA: relatório de opções (HALT do user)

as-of: 2026-08-11 · campanha 2 (unidades) · Task 11 Step 2

## Diagnóstico (Step 1, confirmado com dados)

Sonda canônica read-only (`course_probe.compute_production_index`, persist=False, perfil IA
já com syllabus vivo, repo IA intocado) — 23 blocos pós-refresh:

| Blocos (sonda) | Datas | Conteúdo (SARC vivo) | Sonda dá | Verdade (cruzamento) |
|---|---|---|---|---|
| 01-02 | 02-04/03 | plano + visão geral | u01 | u01 ✓ |
| 03, 04, 05, 06 | 09/03..27/04 | **arco ML completo** (dados, k-NN, redes, árvores, k-means) | **u01** | **u05** ✗ |
| 10 | 11/05 | exercícios gerais | u01 | — (véspera P1, política) |
| 12, 14, 15 | 18/05..15/06 | algoritmos de busca | u02 | u02 ✓ |
| 16 | 17-22/06 | agentes e planejamento | u03 | u03 ✓ |
| — | — | u04 sem aula própria no SARC | ausente | ausente ✓ |

**Violação monotônica confirmada nos dados:** calendário ensina u01 → u05 → u02 → u03;
o DP monotônico não pode "saltar" pra u05 e voltar — então rotula todo o ML como u01.
Resultado: **4 blocos de aula errados**, e u05 (maior arco do semestre, ~9 semanas) invisível.
"Sonda dá 3 unidades" = u01/u02/u03 — número igual ao disco, conteúdo diferente.

## Opções

### (a) Aceitar limitação documentada
Refresh IA gated + reprocess; índice fica como a sonda (ML=u01). Gold registra os 4 misses
como limitação estrutural documentada.
- Custo: zero código.
- Risco/consequência: tutor IA responde com unidade ERRADA no conteúdo mais extenso do
  curso. Não é miss de política (véspera/prova) — é rótulo positivo errado em aula.

### (b) Pinos gold-backed (recomendada)
Refresh IA gated primeiro (blocos recompõem, uuids novos) → 4 pinos `manual_unit_slug`
u05 nos blocos ML → gates completos → gold IA congelado a partir do cruzamento validado.
- Custo: ~4 pinos + curadoria. Mecanismo JÁ em produção (3 SO + 4 ES2, 7 pinos vivos).
- Risco: baixo; zero colateral (pino é por curso/uuid). `check_sarc_freshness` vigia
  remarcação futura; pino sobrevive enquanto o bloco sobreviver (precedente: 35/35
  preservados no refresh TCC).
- Precedente de adjudicação: aula-13 TCC, bloco-18 SO, 4 pinos ES2 — inversão LOCAL
  calendário-vs-plano é exatamente a classe que o pino resolve.

### (c) Modo não-monotônico por curso (flag no matcher)
TDD estilo Tasks 1-3; flag por curso desliga a restrição monotônica do DP pro IA.
- Custo: maior (código + testes + gating por curso).
- Risco: sem a monotonicidade, o scorer puro decide sozinho — e a campanha provou que ele
  erra sob co-ocorrência (SO: slice deadlock pontuava u02 por 'gerencia'; M1/M2 medidos =
  0 ganho). No IA o matcher de tópico já confunde ("ML - Introdução" casa com "agentes em
  ambientes determinísticos" no primary_topic_label). Ganho estrutural real só se mais
  cursos inverterem — hoje é 1 em 5 (YAGNI).

## Recomendação

**(b)**. 4 pinos gold-backed com cruzamento validado como oráculo; (c) fica anotado como
candidato se a família crescer (tracker T13). Sequência pós-ruling: snapshot IA-Tutor →
refresh/reprocess [profile] gated → pinos nos uuids novos → verify_units/órfãos/
rebuild_diff/suite → golden IA re-baseline (fecha o único fail esperado da suite) →
gold IA congelado (xlsx/CSV) a partir do cruzamento.

## Regra de provas (já registrada, entra no gold/covered_units)

P1 = u01+u05 · P2 CUMULATIVA = u01+u05+u02+u03 · PS = tudo (regra DESTE plano; MF/TCC
não-cumulativo). Fonte: `docs/reports/gold_templates/CRUZAMENTO_IA_SARC.md`.
