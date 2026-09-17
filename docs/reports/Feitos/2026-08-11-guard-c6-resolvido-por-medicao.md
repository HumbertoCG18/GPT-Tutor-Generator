# Guard C6 (aula-13 TCC) — RESOLVIDO POR MEDIÇÃO: motor novo já é honesto; vilão é o legado condenado

as-of: 2026-08-11 · follow-up do T12 (`2026-08-11-t12-sandbox-aula13-tcc.md`) · ruling user: aceitar veredicto

## Medição (sandbox TCC sem pino, mesmos inputs de produção)

Replicação do scoring com as funções públicas do `concept_resolver` + chamada real de
`resolve_material_assignment` (inputs via `assemble_resolver_inputs`, code_curation e
lessons_index do repo):

| Caminho | Resultado pra aula-13 sem pino | Caráter |
|---|---|---|
| **Motor novo** (concept_resolver, flag-ON TCC) | bloco-09, conf **0.08**, band **BAIXA**, method concept-fused; `card_term=0` em TODOS os blocos | Errado mas HUMILDE — sem dano |
| **Legado** (resolve_unit_block_tags) | bloco-13, conf **0.85** (`CARD_SINGLE_CONF`), band **ALTA** | Confiante-e-errado — o resíduo do T12 |
| Produção | pino `manual_timeline_block_id` → bloco-12, conf 1.0 | Correta |

## Por que o legado decidiu no sandbox

`apply_concept_resolver` PULA entry com `computed_block_id` vazio (`resolver_apply.py:116`)
— o sandbox zerou o campo ao remover o pino, o motor novo pulou, o legado preencheu com
card 0.85. Em produção esse cenário exige pino caído + computed zerado simultâneos.

## Veredicto (ruling user 2026-08-11)

**Nenhum guard implementado — de propósito:**
1. Motor novo NÃO precisa (degrada honestamente; os guards de coerência existentes —
   unit-vs-topic 0.45 e tool-unit — seguem cobrindo as classes de conflito reais).
2. Guard no legado = investir em código condenado ao cutover Fase 3.4 (campanha 3),
   com réguas fase2/4/5 sensíveis ao redor. Anti-overengineering.
3. Pino gold-backed segura produção até o cutover; o cutover mata o caminho vilão.

Item [CODE] "guard C6" do tracker encerrado com esta referência. O sandbox T12 permanece
como RED de REGRESSÃO do cutover: pós-cutover, aula-13 sem pino DEVE dar band não-alta
(motor novo) — se voltar a 0.85-alta, o caminho legado renasceu.
