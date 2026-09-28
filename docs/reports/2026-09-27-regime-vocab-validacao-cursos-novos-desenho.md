# Regime VOCAB — validação em cursos novos: desenho e decisões pendentes (27/09/2026)

**Estado: PROPOSTA. Nada executado.** Decisão do usuário de 27/09: preparar a validação em cursos novos até o Gate de
rede/LLM. Este documento vira pré-registro só depois das decisões da §6 e de um Gate 1 próprio.

## 1. Pergunta

O compilador de vocabulário atual, congelado como na rodada VOCAB_LIMPO, melhora a subunidade primária em cursos que
não participaram de nenhum desenvolvimento, sem regredir bloco e unidade?

É a única medição que responde à generalização. Os sete cursos atuais (MF, SO, IA, ES2, TCC, CG, FR) estão
contaminados: o prompt foi calibrado neles, o gold deles foi visto em duas avaliações, e o diagnóstico de 27/09 formou
hipóteses olhando suas perdas.

## 2. Candidatos disponíveis hoje (inventário de 27/09)

| curso | situação | serve como curso novo? |
|---|---|---|
| MF, SO, IA, ES2, TCC, CG, FR | gold completo, usados no desenvolvimento | não |
| LR (Laboratório de Redes) | tutor no disco com 7 entradas (4 "outros", 2 materiais de aula, 1 cronograma); sem gold de bloco, unidade ou subunidade; sem pacote congelado; tem sidecar LLM histórico; entrou em medições de 8 cursos do motor | só como complemento: amostra pequena demais para decidir |
| outros cursos | nenhum tutor no disco | exigem novos tutores fornecidos pelo usuário |

**Consequência:** a validação depende de cursos novos que o usuário tenha, construídos pelo aplicativo e rotulados pelo
próprio usuário. Não há como montar o conjunto só com o que está no disco.

## 3. Protocolo proposto (etapas e Gates)

1. **Escolha dos cursos (usuário).** Disciplinas nunca processadas pelo motor, com plano de ensino e materiais. Meta de
   tamanho a decidir na §6.
2. **Construção dos tutores (usuário, pelo aplicativo).** Build normal do produto, sem mudança em `src/`. O compilador
   de vocabulário fica DESLIGADO no build, para o CRU nascer sem vocabulário: flag de curso `compile_vocabulary`
   desligada (é opt-in) e `TUTOR_NO_VOCAB_COMPILE=1` como trava (`pedagogical_regeneration.py`).
3. **Pacote congelado por curso.** Manifest, markdowns, timeline e taxonomia copiados para `.frzero/`, com árvore de
   hashes, antes de qualquer rótulo ou geração.
4. **Gold cego (usuário).** Rótulos de bloco, unidade, subunidade primária e aceita, nos formatos atuais
   (`ground_truth_*`, `material_gt_*`, `subunit_gt_*`), feitos sobre o pacote congelado SEM ver predições do motor.
   Congelados por blob git antes da geração. Denominadores por curso declarados no congelamento.
5. **Pré-registro e congelamento do compilador.** Reusa o normativo da rodada limpa (congelamento `62b45e38…`):
   - mesmo código (`vocabulary_compile.py` `60c83080…`, `gemini_client.py` `9635f6aa…`), mesmo prompt de sistema
     (`99221b05…`) e schema (`49e06e9e…`);
   - modelo `gemini-3.5-flash` (alias; `model_version` registrado por resposta, sem garantia de versão imutável);
   - staging a partir do CRU do curso novo, ensaio sem rede com inventário de chamadas, uma geração oficial.
6. **Gate de rede/LLM (usuário).** Autoriza a geração única com o inventário exato de chamadas.
7. **Braços e capturas sem gold.** CRU, VOCAB, controle "maior" e três aleatórios (sementes 1, 2, 3), pelo harness da
   rodada limpa adaptado só nos cursos e caminhos (diff revisável).
8. **Gate de avaliação (usuário).** Espelho da régua por blob, avaliador congelado, uma execução de conferência.

## 4. Veredictos a pré-registrar (proposta, mesmos critérios da rodada limpa)

- **A_novo:** VOCAB > CRU, controle "maior" e cada aleatório na primária total dos cursos novos.
- **B_novo:** ganho de primária, zero perda nos três eixos oficiais, nenhum curso regredindo.
- **C_novo:** > 90% estrito por contagem (acertos × 10 > 9 × n) por eixo e curso avaliado.
- Relatório por curso, com transições por ID e precisão sobre todas as alteradas, como na rodada limpa.

## 5. O que muda no código (só harness, fora de `src/`)

- Lista de cursos, caminhos dos pacotes e denominadores (hoje fixos em `comum.py` e `captura.py` da rodada).
- Referência do CRU: nos cursos novos não há placar publicado. O CRU passa a ser medido na própria avaliação, e o
  controle de integridade vira "CRU reexecutado = captura CRU por ID".
- Nenhuma mudança em métricas, sorteio dos controles, pontuador ou avaliador além dos nomes.

## 6. Decisões pendentes do usuário (bloqueiam o Gate 1)

1. **Quais cursos novos** e quantos. Referência: os sete atuais somam 251 materiais com gold de subunidade; abaixo de
   ~100 o resultado fica muito instável por curso.
2. **Se o LR entra** como curso complementar, sabendo que tem 7 entradas e já apareceu em medições do motor.
3. **Quem rotula e quando:** o gold precisa ser feito antes da geração e sem ver predições.
4. **Se o diagnóstico de 27/09 pode orientar alguma mudança antes da validação.** Recomendação: não. Qualquer ajuste
   (piso da 1ª passada, diluição da cobertura, aliases genéricos, propagação) mudaria o objeto e exigiria nova rodada
   limpa; a validação em cursos novos deve medir o compilador congelado de hoje.

## 7. Riscos conhecidos

- **Alias do modelo:** `gemini-3.5-flash` pode apontar para outra versão na data da geração. Registrar `model_version`
  e declarar a diferença, sem trocar de modelo.
- **Build do produto:** se o build dos cursos novos exigir mudança em `src/`, a validação para até outro Gate.
- **Mecanismos do motor:** o diagnóstico mostrou perdas vindas da regra de seção e da propagação da 2ª passada. Elas
  devem reaparecer nos cursos novos; isso faz parte da medição, não é motivo para ajustar antes.
