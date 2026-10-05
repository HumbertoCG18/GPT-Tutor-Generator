# Integração e ativação conjunta A+P1 (#89, #90) — relatório para o Gate 2

04/10/2026, sessão Claude Code `bafdef33`. Executa os 5 passos de
`p1/docs/reports/2026-10-02-p1-avaliacao/plano-integracao-acentos-p1.md`, com Gate de integração concedido pelo usuário
na retomada de 04/10. **Sem commit, merge ou push.** Avaliação congelada de 02/10 não reaberta; nenhuma revisão LLM nova.

## Resultado

| árvore | callback de subunidade | decisões × referência (350 IDs, sem gold) | bloco | unidade | sub primária | sub aceita |
|---|---|---|---:|---:|---:|---:|
| integrada (`feat/motor-integracao-ap1`) | com `divisores_de_frase` | 0 mudanças × candidato 87 `6299edfd` | 223/237 | 249/284 | **87/251** | 110 |
| revertida (= `dev` 6a55857c) | sem | 0 mudanças × referência 86 `e024d396` | 223/237 | 249/284 | 86/251 | 109 |

O replay usou o callback real da produção (`src.builder.engine._auto_map_entry_subtopic`, o mesmo objeto que
`resolver_apply` leva à 1a passada e à 2a), sem `partial` experimental. Gold só depois das decisões fixadas por sha256;
`src` fora da worktree: nenhum nas duas execuções.

## O que mudou (diff contra `dev` 6a55857c)

| arquivo | origem | sha256 |
|---|---|---|
| `src/builder/text/normalize.py` | A, cópia byte a byte da `cru05` | `f5b9581a` (= avaliado) |
| `src/builder/timeline/index.py` | P1, cópia da `p1` | `28894d0a` (= avaliado) |
| `src/builder/routing/file_map.py` | P1, cópia da `p1` | `6ad4f70b` (= avaliado) |
| `src/builder/facade/file_map.py` | **novo vínculo**: import de `_divisores_de_frase` do módulo especializado + `divisores_de_frase=` no `partial` | `6a673406` |
| `tests/test_text_normalize.py` | A, 7 casos de acentos | `961105b8` |
| `tests/test_p1_frases_compartilhadas.py` | 14 testes P1 + 2 da integração (1a e 2a passada pelo callback de produção) | `fbcb77b8` |
| `.gitattributes` | `-text` para os JSON deste diretório (bytes fixos, como a referência 86) | — |
| `docs/Overview-Sistema.html` | precedência da subunidade: P1 e diacríticos espaçadores | — |

A base da P1/cru05 (`bf46d51f`) e a `dev` têm `src/` idêntico (conferido); por isso a cópia integral equivale a
aplicar os hunks. Nada de Moodle, `.codex/` ou hooks foi transportado (ACH-0006 não se aplica a esta árvore).

## Verificações executadas

1. **TDD da ativação.** Os 2 testes novos falharam antes do vínculo (vencedor `maquinas-de-turing` nas duas passadas)
   e passaram depois (`variacoes-de-maquinas-de-turing`); focado: 30/30.
2. **Suíte**, `TUTOR_REPOS=C:\Users\Humberto\Documents\GitHub`, mesmo ambiente:
   - base (`dev` destacada, worktree `GPT-Tutor-Generator-ap1-base`): 2448 aprovados, 4 pulados, 1 falha;
   - integrada: 2471 aprovados, 4 pulados, 1 falha;
   - falha nas duas: `test_caracterizacao_blocos_atual.py::test_divisao_de_blocos_atual[Fundamentos-de-Redes-Tutor]`
     (preexistente). `test_respect_actualtext…` passou nas duas (ACH-0002);
   - coleta: 2453 → 2476 IDs, nenhum ausente, 23 novos (16 P1, 7 acentos).
3. **Replay integral** com `verifica_integracao.py` (derivado de `tentativa2/replay_t2.py`; um processo por árvore,
   sem a barreira cuja guarda de ABORT estava pendente; aborta antes do gold em src fora ou decisão divergente).
4. **Reversão conjunta.** `git apply integracao.patch` na worktree base reproduz os 6 hashes da árvore integrada;
   `git apply -R` devolve a árvore sem diff contra a `dev` (o teste novo some junto). O replay dessa árvore é a linha
   "revertida" acima. Desligar só o P1 deixaria A (85/251) e não é reversão válida.

## Referências preservadas

- 86: `docs/reports/2026-10-01-cru05-cru03/replay_base.json` (`e024d396`, já versionada na `dev` pela MOTOR-00).
- 87: `referencia87_replay_ap1.json` neste diretório (`6299edfd`, cópia de `p1/.../tentativa2/replay_ap1.json`).
- Replays desta verificação: `replay_integrada.json` (`b4f92a79`), `replay_revertida.json` (`ac064fe7`).
  Promover a 87 a referência vigente só depois do Gate 2; a 86 continua identificada.

## Limites

Ganho de 1 material de desenvolvimento (TCC aula-09), sem curso independente nem generalização demonstrada.
Faltam +7 em unidade e +139 na primária para passar de 90%. A verificação prova que o pacote integrado reproduz por ID
o que foi avaliado; não é nova avaliação.

## Pendente (do usuário)

1. **Gate 2** deste diff. Commit proposto na branch `feat/motor-integracao-ap1`, com os 8 arquivos acima e este
   diretório (sem `coleta_*.txt` se preferir enxugar): `feat(motor): liga frases compartilhadas (P1) e corrige
   diacríticos espaçadores na subunidade`, `Closes #89`, `Closes #90`.
2. Revisão independente do vínculo (2 linhas de produção + 2 testes): só se pedida.
3. PR para `dev`, merge e push: autorizações próprias. Após o merge: replay integral na `dev`, regra da campanha.
4. Grafo: o `graphify-out/` vive na principal; atualizar depois do merge.
5. Remover a worktree temporária `GPT-Tutor-Generator-ap1-base` quando não for mais útil.
