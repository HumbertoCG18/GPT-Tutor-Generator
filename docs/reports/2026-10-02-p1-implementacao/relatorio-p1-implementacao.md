# P1 (#90): implementação restrita, 02/10/2026

**Estado: implementado e verificado, desligado por padrão. Sem avaliação nos cursos, sem gold, sem integração, sem
commit.** Contrato: `GPT-Tutor-Generator-cru05/docs/reports/2026-10-01-cru05-cru03/fase1-p1-desenho-congelado-v2.md`
(sha256 `d30980a3…`).

## Onde

- **Worktree** `GPT-Tutor-Generator-p1`, branch local `feat/cru-p1-frases-compartilhadas`, a partir de `bf46d51f`.
  Fica **sem** a correção dos acentos (#89), que segue na worktree `cru05`. Assim os braços podem ser montados
  separados.
- **Diff de produto:** 2 arquivos, +48/−22 (`diff_p1_vs_bf46d51f.diff`).
- **Teste novo:** `tests/test_p1_frases_compartilhadas.py`, não rastreado e fora do diff.

## O que mudou

**`src/builder/timeline/index.py`:**

- `_frases_do_topico(label, aliases, topic_slug)`: o bloco de deduplicação de frases do pontuador, extraído sem mudança,
  com o mesmo comentário.
- `_divisores_de_frase(topicos)`: devolve as contagens F_top pelo matcher do pontuador. Uma palavra única com menos de 4
  caracteres fica com 0.
- `_score_entry_against_taxonomy_topic(..., divisores_frase=None)`:
  - com `None`, a expressão de soma é a de hoje;
  - com divisores, divide **só no acerto**;
  - `exact_hits` não muda.

**`src/builder/routing/file_map.py`:**

- `auto_map_entry_subtopic(..., divisores_de_frase=None)`. Quando o parâmetro é passado, os divisores são calculados
  sobre o `topic_index` **da própria chamada**, na 1ª ou na 2ª passada.
- **Nenhum chamador de produção passa o parâmetro** (conferido por grep): o P1 fica desligado em todo o produto.
- A rota de unidade, a pontuação bloco × tópico, os tokens e as penalidades ficam intocados.

## Verificação

| verificação | resultado | registro |
|---|---|---|
| testes do contrato (E1–E7, E4b, divisores, padrão desligado) antes da implementação | **vermelho**: `ImportError` de `_divisores_de_frase` | `registros/teste_vermelho.txt` |
| os mesmos testes depois | **10/10 verdes** | `registros/teste_verde.txt` |
| suíte completa (CPython 3.11.9) | 2457 aprovados, 4 pulados, 2 falhas; a base `bf46d51f` tinha 2447 e as **mesmas 2 falhas por ID**; os +10 são os testes novos. **Sem regressão nova** | `registros/suite_p1.txt`; base em `cru05/.../registros/suite_base.txt` |
| replay integral offline com P1 **desligado** × braço correspondente (base sem acentos, `replay_base.json` `e024d396…`), por ID, **sem gold** | **350/350 idênticos**; nenhum módulo `src` de fora da worktree | `replay_p1_desligado.json`, `registros/replay_p1_desligado.txt` (`replay_identidade.py`) |

Os testes cobrem o contrato v2:

- E1: frase compartilhada sozinha ainda decide, sem penalidade;
- E2: frase específica vence a compartilhada, com a confiança esperada;
- E3: identidade bit a bit quando não há frase compartilhada;
- E4: palavra única com divisor 2;
- E4b: "cpu" tem divisor 0, nenhum acerto e nenhum erro;
- E6: padrão desligado idêntico, inclusive com `stem_fallback`;
- E7: divisor de 1 para 2 na taxonomia enriquecida, com chamadas em sequência e sem reaproveitar divisores.

## Hashes

- `index.py` `28894d0a…`;
- `file_map.py` `6ad4f70b…`;
- teste `10f3188f…`;
- `replay_identidade.py` `5c223221…`.

## Fora desta autorização

- P1 **ligado** nos cursos.
- Os braços A, P1 e A+P1.
- Gold e placar.
- Integração e commit.

A avaliação exige Gate próprio, pelo §5 do contrato.

## Revisão independente e reforço dos testes (02/10)

**Revisão:** `job-30` (`run-15`), papel `reviewer`, somente leitura, uma tentativa.

- **Parecer: SEM BLOQUEADOR.** Nenhum achado CRITICAL ou MAJOR; dois MINOR de cobertura de teste.
- O revisor conferiu os 6 hashes do conjunto.
- Ele não conseguiu rodar o pytest no próprio ambiente ("No usable temporary directory found"). A limitação fica
  documentada e não exige nova revisão (decisão do usuário).
- Parecer integral: `registros/revisao_job-30.md`.

**Reforço** (decisão do usuário: só testes; replay só se o produto, o runner ou os insumos mudassem). Quatro testes
novos, um por lacuna:

| lacuna do revisor | teste |
|---|---|
| duas chaves do mesmo tópico contendo k | `test_varias_chaves_do_mesmo_topico_contam_o_topico_uma_vez`: rótulo + alias distinto + alias repetido + alias que normaliza para vazio + slug igual ao rótulo. F_top = 2 tópicos, não 3 chaves |
| filtro da unidade vencedora | `test_divisores_respeitam_o_filtro_da_unidade_vencedora`: divisores entre os concorrentes de u1 (2) × sem filtro (3), conferidos pela confiança |
| isolamento das rotas de unidade e bloco | `test_rotas_de_unidade_e_bloco_nao_recebem_divisores_com_o_p1_ligado`: com o seletor da subunidade ligado, um espião confirma que a rota de unidade só recebe `stem_fallback=True` e que a de bloco não recebe argumento extra |
| propagação real | `test_propagacao_real_recalcula_divisores_na_taxonomia_enriquecida`: `propagar_vocabulario_por_headings` real com dados sintéticos. O seletor ligado recebe a taxonomia **enriquecida** (alias "perceptron" propagado), o receptor é decidido, e a taxonomia original fica intocada |

**Resultados:**

- **Testes do P1:** 14/14 verdes, os 10 anteriores e os 4 novos.
- **Mutação em memória** (`mutacao_conta_chaves.py`): `_divisores_de_frase` contando chaves em vez de tópicos.
  - O teste novo **falha** sob a mutação; o antigo de divisores passava, confirmando a lacuna apontada pelo revisor.
  - Registro: `registros/mutacao_conta_chaves.txt`.
- **Suíte final:** 2461 aprovados (2447 da base + 14 do P1), 4 pulados e as mesmas 2 falhas da base por ID. Sem
  regressão nova. Registro: `registros/suite_p1_reforco.txt`.
- **Hashes:** produto inalterado (`index.py` `28894d0a…`, `file_map.py` `6ad4f70b…`). O runner do replay
  (`5c223221…`) e a referência (`e024d396…`) também ficaram iguais. Só o teste mudou: `10f3188f…` → `90746e83…`.
  - **A evidência do replay com P1 desligado (350/350) continua válida, sem repetição.**
- Nenhum defeito de produto foi encontrado. Não houve mudança de produto nem de contrato, nova revisão LLM ou avaliação
  dos braços.
