# Pedido do usuário, 23/09 — reformular o W-AA antes da execução (registro literal)

Recebido na sessão 843a75cb como texto colado, sem outro texto do usuário no turno; tratado como pedido do usuário.
Resposta: `docs/reports/2026-09-23-waa-desenho.md`.

---

O diagnóstico permite encerrar uma dúvida importante: corrigir unidade não é a principal solução da subunidade. Não quero outro diagnóstico geral nem voltar às variantes de precedência reprovadas.

Quero reformular o W-AA antes da execução.

1. Direção principal

Priorizar geração de candidatos e seleção de subunidade. As duas classes concentram 143 dos 165 erros.

Corrigir apenas os 67 erros de seleção, mesmo sem perdas, levaria a 153/251. Portanto, essa frente não pode ser apresentada como caminho suficiente até 226/251.

Precisamos medir também como aproveitar as relações já existentes no pacote nos casos em que o tópico correto recebe pontuação zero, sem transformar essas relações em aliases globais indiscriminados.

2. Novidade em relação ao que já foi medido

Antes de executar, explique a diferença entre W-AA e o H2 de ponderação por campo, além das outras variantes pertinentes.

Testar novamente título/heading/corpo pode ser uma reavaliação na base atual, mas não deve ser apresentado como mecanismo novo sem diferença concreta.

Diferencie localização da ocorrência de função da ocorrência: assunto principal, pré-requisito, revisão, exemplo ou comparação. Não presuma que heading significa assunto principal.

Se a proposta for equivalente a uma hipótese já examinada, registre a equivalência e não abra outra grade de limiares.

3. Desenho do experimento

Compare, se os artefatos disponíveis permitirem:

A. Candidatos atuais + critério de seleção proposto.
B. Candidatos atuais acrescidos das relações existentes no pacote + o mesmo critério de seleção.

O objetivo é separar melhoria de seleção de melhoria de geração de candidatos.

Preserve a proveniência das relações: fonte, trecho, material relacionado e tópico candidato. Não use gold, IDs dos erros ou saídas do motor para criar ligações que se justificam circularmente.

A regra deve ser aplicada pela mesma política aos materiais elegíveis, não apenas aos 65 ou 67 casos identificados pela avaliação.

Declare previamente o mecanismo. Se houver parâmetros, escolha por LOCO. Reutilize dados congelados e evite execuções duplicadas.

4. Critério de avaliação

“Precisão acima de 50% nos 86 acertos atuais” não é aceite de integração.

Separe teste exploratório de sinal de avaliação de uma política completa de decisão.

Reporte nos 251 materiais:
- Acertos totais e por curso.
- Correções e perdas por ID.
- Abstenções convertidas em decisões corretas e erradas.
- Precisão das decisões novas ou alteradas.
- Efeito nos demais eixos.

Os subconjuntos servem para explicar os resultados, não para restringir artificialmente a avaliação ou o acionamento.

Qualquer integração continua exigindo os critérios vigentes de preservação e replay integral. Não é permitido proteger os 86 por uma lista extraída do gold.

5. Conferências pontuais do relatório atual

Sem repetir o diagnóstico completo:

- Mostre as transições do oráculo 86 → 92: correções, perdas e eventual efeito da segunda passada. Não trate ganho líquido como número bruto de casos recuperados.
- Apresente a fórmula, os IDs e as condições do teto de 84,1% de CG. Distinga teto do índice/intervenção de limitação da informação disponível.
- Explique como os cinco casos de régua incoerente participam dessa conta, sem alterar a régua nesta etapa.
- Confirme no fluxo real de criação de uma disciplina, em ambiente isolado, a flag efetiva do D9 e o resolvedor utilizado. Não basta ler o valor padrão de uma função se houver configuração posterior.
- Não remova o fallback antigo nem altere defaults sem proposta e replay próprios.

6. Limites e entrega

Esta etapa não autoriza mudanças em src/, régua, defaults, remoção de legado, commit, push ou incorporação de conhecimento externo.

Entregue primeiro o desenho delimitado do W-AA, suas diferenças em relação aos experimentos anteriores e as conferências pontuais acima.

A conclusão precisa dizer se existe uma hipótese nova capaz de atuar sobre geração e seleção, qual parcela do residual ela pode alcançar e qual evidência a refutaria.

Não quero outra sequência indefinida de ajustes de pesos. Quero um experimento que permita decidir uma direção.
