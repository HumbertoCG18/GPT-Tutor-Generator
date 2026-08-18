# Handoff — pós-cutover: sinais de atribuição (o que falta implementar)

date: 2026-08-18
branch: `feat/motor-atribuicao` (HEAD `f61db40`)
sessão anterior: campanha 3 PASSO 3 (flip + deleção do funil) **FECHADA** + 3 melhorias de sinal
working tree: **limpa** · 5 repos-tutor: **limpos**, todos em "indice v4"

> Este handoff é de LEITURA/PLANEJAMENTO. Nada aqui está em execução; a seção
> "O que falta" é a fila para decidir, não para rodar direto.

## Boot da nova sessão

1. `mem-search` · `.mex/ROUTER.md` · este handoff · tracker `docs/reports/pendencias.md`
   (header + Concluído 2026-08-17c).
2. Fecho do cutover: `docs/reports/2026-08-17-passo3-flip-delecao-fechado.md`
   (flip, deleção, serializador v4, achado do viés P3.1).
3. Medição pré-flip: `docs/reports/2026-08-17-medicao-pre-flip-5cursos.md`.

## Estado verificado (as-of 2026-08-18, HEAD `f61db40`)

- Suite: **1873 passed / 1 skipped / 0 failed**.
- Motor é o atribuidor ÚNICO (funil legado deletado, -4747 linhas). Serializador
  de índice único (v4). `use_concept_resolver` default ON.
- Réguas por material (`scripts/eval_ground_truth.py` + `docs/reports/ground_truth_<curso>.csv`):

| curso | régua | confiante-e-errado |
|---|---|---|
| MF | 63/66 (95,5%) | 1 |
| IA | 43/44 (97,7%) | 0 |
| ES2 | 22/28 (78,6%) | 0 |
| SO | **27/38 (71,1%)** | 0 |
| TCC | 18/25 (72,0%) | 2 |

- Golds por bloco (`scripts/eval_units.py`): ES2 7/7 · IA 9/10 · MF 12/14 · SO 9/11 · TCC 13/13.
- `rebuild_diff`: 5/5 cursos = 0. Pinos: 0 violados.

## Commits desta sessão (gerador)

| commit | conteúdo |
|---|---|
| `b56815f` | medição pré-flip 5 cursos (4 gates verdes) + `scripts/measure_flip.py` |
| `c5ecb5f` | flip: `use_concept_resolver` default ON |
| `df86203` | **deleção do funil legado** (-4747/+334), motor semeia entries novos |
| `037ddbe` | serializador único v4 + itens 8b/8d |
| `864a61c` | relatório de fecho do passo 3 + tracker |
| `9b6ab28` | tier de DATA NO NOME + re-rótulo do gold SO (10 linhas) |
| `24a25f2` | ordinal mira o ENCONTRO + `provider_ordinal` (P3b) no motor de âncora |
| `f61db40` | remove `professor_signal` (campo morto) |

Repos-tutor: flip, reprocess pós-deleção e índice v4 commitados nos 5.

## Achados que mudam como se raciocina sobre o sistema

1. **A régua mede `resolve_temporal_block`** (âncora > pino manual > computed).
   Melhoria em `computed_block_id` NÃO aparece na régua quando a entry já tem
   âncora — foi por isso que o tier de data pareceu "neutro" no SO. Quem move a
   régua é o **provider de âncora**; `computed_block_id` alimenta unit/subunit.
2. **O gold pode estar errado.** SO subiu 18/38 → 27/38 só com re-rótulo pela
   evidência de data no nome. Antes de caçar bug, conferir o gold.
3. **Viés P3.1 morreu com o funil**: o scorer lia as tags `unit:`/`subunit:` que
   o próprio funil reescrevia (auto-confirmação). Confidences agora honestas.
4. **Datas do Moodle são inúteis como sinal** (verificado em Computação Gráfica,
   67 arquivos): `timecreated` = bulk upload do dia 1 (34 arquivos em 28/07, 31
   sem valor); `timemodified` = 2020-2022 (reuso de material). `posting_date`
   fica cego POR DESIGN — não reabrir.

## O QUE FALTA IMPLEMENTAR (fila para decidir)

### A. Aplicar em produção o que já está no código — PENDENTE
O date-tier e o `provider_ordinal` estão commitados e medidos em SANDBOX, mas os
5 repos-tutor **não foram reprocessados** com eles. Falta:
- reprocess dos 5 (`scripts/reprocess_assignments.py`);
- revisar sentinelas caso-a-caso e re-baselinar (`tests/_golden/*__casos_chave.json`);
- commitar por repo.
Impacto medido em sandbox: SO 91 campos alterados (11 blocos), TCC 12 (13 entries
passam a ancorar por `ordinal` em vez de voto LLM). Réguas: neutras ou melhores.

### B. Erros restantes do SO (11 de 38) — material SEM data e SEM ordinal
`plano-de-ensino` · `apresentacao-da-disciplina` · `definicao-e-historico` ·
`exercicios` · `lista-exercicios-p1` (+`-gabarito`) · `lista-exercicios-p2` ·
`questoes-do-enade-sobre-sisop` · `exemplo-threads-em-c-exemplo1/2/3`.
Padrão: sem sinal de nome, sobra só conceito — e vários são material de apoio que
o professor não datou. Hipóteses a avaliar (nenhuma implementada):
- `source_section` do card Moodle como janela (já existe `provider_topic`, mas só
  casa "Semana N - Tópico"; os cards do SO podem ter outro shape);
- séries: `exemplo-threads-em-c-exemplo1/2/3` são gêmeos temáticos — decidir juntos;
- pino manual (2-3 pinos resolveriam metade).

### C. Erros restantes do TCC (7 de 25)
- "Aula 17" aparece 2× em blocos diferentes (professor repetiu o número) — o
  ordinal não distingue; candidato a pino.
- "Aula 16 - Classes de Problemas": ordinal→bloco-18, gold quer bloco-19
  (fronteira de bloco).
- Demais: listas/provas sem ordinal.

### D. Data no meio do título — IMPLEMENTADO, mas só no `computed`
`extract_dates(..., dm_two_digit_only=True)` casa "07.04" em qualquer posição do
título cru. **Porém** o `provider_date` do motor de âncora ainda lê só o PREFIXO
(`_DATE_PREFIX_RE`, `window_provider.py:251`). Unificar os dois (o provider
passar a usar o mesmo extrator com guarda de 2 dígitos) é trabalho pequeno e
levaria o ganho pra régua — não foi feito.

### E. Canais ainda cegos (auditoria 2026-08-17)
- `relevant_for_exam`: flag manual sem uso no scoring. Usar seria especulativo
  (viés pró-bloco-de-prova). Recomendação: deixar como está.
- `manual_review` / `review_status` / `file_count` / `language`: operacionais,
  corretamente fora do scoring.
- `posting_date`: ver achado 4 acima — fechado, não reabrir.
- ~~`professor_signal`~~ removido nesta sessão.

### F. Dívidas do tracker que seguem abertas
- **M7** (calibração cross-escala de confiança motor × scorer de unidade) — 1 caso
  conhecido (`colecoes-conjuntos` MF, 0.80→0.45).
- **M4/M5/M6** e resto do **M8** — oportunistas.
- 2.7 `signal_token_set` · 2.13 smoke tests · 3.1-3.3 estruturais.
- **Campanha web** (backlog no fim do tracker) — era o próximo da fila ratificada
  em 2026-08-11, agora desbloqueada (motor estável e único).

## Notas operacionais

- Sandboxes de medição: `robocopy <repo> <scratch>/sandbox-<SIGLA> /E /XD .git`,
  depois `scripts/measure_flip.py <SIGLA> <scratch>` (driver commitado).
- Réguas oficiais vivem em `docs/reports/ground_truth_<curso>.csv` (NÃO em
  `tests/fixtures/eval/`, onde só há os golds por bloco).
- `.bak` do gold SO pré-rótulo: `docs/reports/ground_truth_SO.csv.bak`.
- Hook `code-review-graph` crasha com `UnicodeEncodeError` cp1252 em todo commit —
  conhecido, não-bloqueante.
- PowerShell: `Remove-Item` em variável que contém `/E` (arg do robocopy) dispara
  bloqueio de path protegido — separar limpeza e cópia em comandos distintos.
