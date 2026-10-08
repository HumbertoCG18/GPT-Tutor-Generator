# Probe resolver-fino vs funil — RECUPERADO (mem-off gap)

date: 2026-06-28
contexto: claude-mem ficou OFF Jun 21–28 (bug, issues abertas no repo do claude-mem).
Os "probes" que o Claude Web citou (`probe-1 net 0`, `probe-2 net −24`, `instancename
heterogêneo`, `SARC drift`) NÃO foram gravados — nem em memória nem em report. Este doc
re-deriva o que dá pra re-derivar READ-ONLY e marca o que não dá.

método: `scripts/compare_resolver.py` (read-only; NÃO escreve no repo, NÃO chama API;
roda o `concept_resolver` in-memory sobre o manifest VIVO e conta blocos que mudariam
vs o funil `computed_block_id`). Caveat do próprio instrumento: comparação NÃO
like-for-like — resolver-COM-concepts-do-LLM vs funil-SEM.

---

## 1. NÚMEROS RECUPERADOS (estado vivo, as-of 2026-06-28)

| Curso | Materiais | Blocos mudados | % churn | Conflitos block-unit≠topic-unit |
|---|---|---|---|---|
| Engenharia-Software-2 | 24 | 12 | 50% | 3 |
| Inteligencia-Artifical | 59 | 34 | **58%** | **32** |
| Metodos-Formais | 57 | 31 | 54% | 15 |
| Sistemas-Operacionais | 32 | 9 | **28%** | 13 |
| TCC | — | (sem saída) | — | — |

> TCC não emitiu seção (provável "sem blocos em .timeline_index.json" ou manifest
> ausente no path default) — investigar à parte.

**Leitura:** ligar o resolver-fino re-rotularia a MAIORIA dos materiais em IA/MF/ES2
(50–58%), com 32 conflitos em IA. NÃO é mudança cosmética — é churn massivo, e sem gold
fora do IA não há prova de que melhora.

## 2. DIREÇÃO DA MUDANÇA EM IA (o "net negativo" qualitativo)

Das 34 mudanças IA, o padrão dominante de banda é **rebaixamento de confiança**
(`alta→baixa`, `alta→media`) — o resolver mexe E fica MENOS confiante. Exemplos vivos:

- `algoritmo-de-classificacao-k-nn`: alta→**baixa**
- `exemplo-com-k-nn`: media→**baixa**
- `k-nn-para-classificacao-exemplo-cardio`: alta→**baixa**
- `survey-on-clustering`, `visao-geral-introducao-e-historico`: → conflito + rebaixa

**Os 2 FAILs k-NN do baseline NÃO são consertados limpos:** o resolver só TROCA
`exemplo-2-k-nn-IRIS` e `exemplo-com-k-nn` de bloco com banda BAIXA — relabel incerto,
não resolução de fronteira. Bate com o histórico: o resolver **regrediu o gold IA
(11→10)** antes (handoff cascata §2).

## 3. MAPEAMENTO p/ os rótulos do Claude Web — com limites honestos

- **`probe-1 net 0`** = alavanca-0 / sinal-lesson (efeito MARGINAL de adicionar
  `lessons_index` ao fusor). Era **efficacy-neutral** — memória #1727 ("Resolver Holds
  Baseline at 12/17, 70%") + #1752 (code review Opus: "Degrau 3a APPROVED — Efficacy-
  Neutral"). NÃO re-derivado nesta corrida (exigiria diff lesson-ON vs lesson-OFF;
  o compare_resolver atual já roda COM lessons_index). **Atestado por memória, não por
  re-run.**
- **`probe-2 net −24`** = resolver-fino substituindo o funil → churn negativo grande.
  **Re-derivado em ESPÍRITO, não no inteiro literal:** IA 34/59 mudados + 32 conflitos +
  colapso de confiança; frota = 86 mudanças totais (ES2 12 + IA 34 + MF 31 + SO 9); sem
  gold fora do IA, e IA já regrediu. **O `−24` exato NÃO é reproduzível read-only**
  porque (a) compare_resolver conta MUDANÇAS, não net-julgado-por-gold; (b) só IA tem
  gold pra julgar net, e net −24 num gold de 33 é implausível (30/33→6/33); (c) a config
  exata do probe-2 do CC anterior não foi gravada.

## 4. IMPLICAÇÃO

A recuperação **CONFIRMA a direção** que refutou a recomendação B (religar a cascata):
o fino, ligado, causa churn enorme, conflito-pesado, confiança-em-queda, sem suporte de
gold fora do IA. Consistente com o Claude Web absorvendo o B.

NÃO confirma o inteiro `−24` — esse veio de um cálculo do CC anterior que não sobreviveu
ao mem-off. Pra cravar o `−24`: ou você cola as notas do probe daquele chat, ou
re-aplica o flag-swap + eval (reprocess = **ação tua na GUI**, e só mede net em IA, que
tem gold).
