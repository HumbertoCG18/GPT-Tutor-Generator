# T12 (U6) — Sandbox aula-13 TCC: resíduo do scorer VIVO, guard C6 vira item [CODE]

as-of: 2026-08-11 · campanha 2 (unidades) · Task 12

## Método

Cópia integral do TCC-Tutor pro scratchpad (sem .git); pino `manual_timeline_block_id`
removido da entry `aula-13-teorema-de-rice-pdf` na CÓPIA (derivados `computed_*`
zerados); reprocess pelo caminho de produção (`RepoBuilder.incremental_build`, perfil
real com `repo_root` trocado, flags vivas `use_anchor_engine`+`use_llm_voter`).
Produção intocada (pino segue em `91c1d2a`, método `manual`, conf 1.0 → bloco-12).

## Resultado

Sem pino, a aula-13 volta EXATAMENTE pro erro pré-ruling:

| Campo | Valor sem pino | Correto |
|---|---|---|
| computed_block_id | `027d4024` = **bloco-13** (problema da correspondência de Post, 24/04) | `0cd0390b` = bloco-12 (teorema de Rice, 22/04) |
| computed_block_method | `card` | — |
| computed_block_confidence / band | **0.85 / alta** | — |
| reasons | `winner_score=48.76 · topic_score=8.83 · herdada_do_bloco=027d4024` | — |

## Veredito (Step 3 do plano)

**U1 NÃO matou o resíduo.** O caminho `card` (herança de bloco via card_evidence do
rótulo rico do bloco-13) segue atraindo o material com banda ALTA — classe
confiante-e-errado, a pior. Conforme o plano: **especificar guard C6-equivalente no
caminho do scorer como item [CODE], com este sandbox como RED pronto** (reproduzir:
remover pino na cópia + reprocess ⇒ esperado bloco-12, obtido bloco-13@0.85-alta).
Implementação SÓ com aprovação do user (follow-up; o pino gold-backed segura produção
indefinidamente). Vai pro tracker na T13.

Sinal específico pro futuro guard: `topic_score=8.83` é BAIXO relativo ao
`winner_score=48.76` — o vencedor vence por evidência de card, não por afinidade de
tópico; um C6-equivalente pode exigir coerência tópico-vs-card antes de conceder
banda alta a herança de bloco.
