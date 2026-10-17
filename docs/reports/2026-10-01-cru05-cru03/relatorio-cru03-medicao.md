# CRU-03: medição de sinal nos blocos de afinidade zero (01/10/2026)

**Resultado: 0/80 para o detector pré-definido.** Nenhum dos 80 materiais dos blocos de afinidade zero tem
`section_slug`, o detector de seção do Moodle do #47, fixado no pré-registro antes da execução.

- Isso **encerra esta medição**, sem proposta de regra.
- **Não prova** que as seções não tenham nenhuma informação útil: só o detector pré-definido foi medido.
- Os aliases EN/PT continuam **não medidos**.

*Precisão do usuário, 01/10.*

## Execução

- **Pré-registro:** `preregistro-cru03-medicao.md`, sha256 `36eed38b…`, selado às 18:3x, antes da execução
  (`registros/preregistro-cru03.sha256`).
- **Script:** `mede_cru03.py` (`13228662…`). Usa `src` da base, sem a correção do CRU-05 (worktree da noite,
  `bf46d51f`), as decisões de `replay_base.json` e o rastro de `diag_rastro_base.json` (fidelidade integral). Roda sem
  gold e sem replay, em cerca de 4 s.
- **Saída:** `medicao_cru03.json` (tabela selada `24a95cd6…`) e `registros/medicao_cru03.txt`.

## Reconciliação

| | W-Z2 (23/09) | agora |
|---|---|---|
| candidatos do DP | 125 | 125 |
| afinidade zero (`sem_sinal`) | 50 | 50 |
| blocos não fiéis ao DP | — | 0 |

## Universo (50 blocos de afinidade zero)

- **Por posição:**
  - 33 interior;
  - 11 fronteira;
  - 6 borda.
- **Por curso:**
  - CG 9;
  - IA 8;
  - MF 8;
  - ES2 7;
  - SO 7;
  - FR 6;
  - TCC 5.
- **Materiais:**
  - 34 dos 50 blocos **não têm nenhum material**: só influenciam a sequência do DP e os vizinhos;
  - os outros 16 têm 80 materiais.
- **Motivo da unidade desses 80 materiais**, no replay da base:
  - 37 pela própria pontuação de texto (`topic_score`);
  - 15 herdada do bloco;
  - 12 reconciliada com o bloco;
  - 11 herdada do vizinho;
  - 4 texto-vence-vizinho;
  - 1 unidade explícita.

  Só cerca de metade depende da unidade do bloco.
- **Sinal da seção do Moodle:**
  - **0 dos 80** materiais têm `section_slug`, nos três estratos. Cardinalidade das unidades compatíveis = 0 nos 50
    blocos; concordância "ausente" em todos;
  - o sinal existe em outros materiais (61 de 350: CG 28, TCC 12, IA 10, SO 9, ES2 2, MF 0, FR 0). O instrumento
    funciona: o sinal é que está ausente nesse universo;
  - as seções cruas desses materiais nomeiam atividade ou semana, não unidade. Exemplos: "Provas por Indução",
    "Exercícios de Revisão para Provas", "Informações Gerais", "Semana 1 - 02.03 a 06.03 - Plano de Ensino…".
- **Aliases EN/PT:** não medidos (lacuna declarada no pré-registro, por falta de fonte bilíngue independente).

## Leitura e limites

- Para o detector pré-definido (`section_slug`), a frente "afinidade zero em fronteiras e janelas pela seção do Moodle"
  **não tem sinal** na base atual: 0/80. Isso não descarta outra leitura das seções, que seria hipótese nova.
- Uma comparação de seção mais solta (sem vencedor único, ou por nome de semana) seria uma variante nova. Ela ficou de
  fora pelo pré-registro, porque seria uma grade de combinações.
- Os +7 de unidade pedem **hipótese nova**, antes de outra rodada, como recomendou a revisão.
- O universo é o dos 7 cursos já vistos. A medição é descritiva, sem gold e sem placar.
