# Pedido do usuário, 23/09 (manhã) — registro literal

Recebido na sessão 843a75cb como texto colado, sem outro texto do usuário no turno; tratado como pedido do
usuário (o texto só restringe escopo: leitura, consolidação e medições isoladas; nada em src/, régua, commit).
Contexto: o usuário disse na noite anterior que enviaria o relatório/conclusão do W-Z ao GPT-6 Pro.

---

Li o parecer final do W-Z. Ele responde a uma parte importante do diagnóstico solicitado: há evidência de problemas na origem da unidade do bloco e na suposição de herança homogênea, enquanto a precedência bloco > texto preserva muitos acertos.

Quero que a próxima entrega PARTA DESSES ACHADOS, sem refazer o W-Z e sem abrir uma R5.

O objetivo agora é completar o diagnóstico causal dos três eixos e apresentar uma direção fundamentada para avançarmos rumo a mais de 90%, com prioridade real na subunidade.

Não quero uma promessa de atingir a meta. Quero saber quais causas estão demonstradas, quais continuam incertas, quanto cada frente poderia resolver e o que ainda falta explicar.

1. ESCOPO E LIMITES

Autorizo leitura de código, fontes, tracker e artefatos; consolidação do diagnóstico; e medições isoladas estritamente necessárias para responder às lacunas abaixo.

Não autorizo:
- Alterar src/, testes de produção, régua ou declarações congeladas.
- Implementar novas regras ou iniciar reescrita.
- Commit, push, PR ou merge.
- Outra grade de limiares equivalente às variantes reprovadas.
- Rotulação pelo professor ou transferência dessa curadoria para o aluno.

Mantenha os contratos:
- Mais de 90% em cada eixo, separadamente, por curso e no total.
- Denominadores preservados; ausentes e abstenções continuam como erro.
- Subunidade aceita é auxiliar, não substitui a primária.
- Cru: zero LLM, embedding ou rede durante o processamento.
- Gold apenas para avaliação e diagnóstico offline, nunca para decisões de produção.
- Nada por curso, arquivo, ID ou lista dos erros conhecidos.
- Parâmetros por LOCO; cursos estudados não são holdout novo.
- Aceite de implementação continua exigindo ganho positivo, zero perda dos acertos atuais, nenhum curso regredindo e preservação dos demais eixos por replay integral.

Não incorpore conhecimento externo. Se necessário, apresente essa possibilidade como regime separado, sujeito a decisão própria.

2. TRATE O W-Z COMO RESULTADO CONSOLIDADO

Use os artefatos conferidos e o congelamento do W-Z como ponto de partida:
bloco 223/237, unidade 248/284, subunidade primária 86/251, aceita 109/251.

Não relance as 25 execuções para redescobrir que R1–R4 falham.

Reutilize as decisões congeladas e --reavaliar quando isso for suficiente. Se um contrafactual alterar uma etapa anterior, recompute os componentes dependentes necessários; não simule o resultado apenas trocando a saída final.

Antes de qualquer medição adicional, registre:
qual pergunta ainda não foi respondida, por que os artefatos existentes não bastam e qual decisão o resultado poderá mudar.

Respeite o protocolo de execução e revisão acordado e registre eventuais desvios. Não substitua revisão de evidências por uma nova execução longa sem necessidade.

3. FECHE AS AMBIGUIDADES DO PRÓPRIO PARECER

O W-Z apresenta:
- “origem 9, homogeneidade 6, empate 3”;
- depois, “origem 9, homogeneidade 9”.

Reconcilie isso por ID, indicando a evidência que sustentou qualquer mudança de classificação. Se três casos permanecerem indeterminados, mantenha-os assim.

Delimite também o alcance das conclusões:
- “Nenhuma regra de texto” deve se referir às regras efetivamente examinadas.
- Os potenciais +4 e +2 das hipóteses finais não são ganhos implantáveis nem garantidos.
- Quando o parecer usa “maioria dos materiais”, esclareça se isso foi constatado pelo gold ou por evidência independente disponível ao motor.

O gold pode sustentar o diagnóstico de que um bloco contém materiais de unidades diferentes. Não pode virar um mecanismo de produção que reconstrói a unidade pelo voto das respostas corretas.

Não altere a régua durante este diagnóstico.

4. COMPLETE A EXPLICAÇÃO CAUSAL DA UNIDADE

Não repita apenas a anatomia dos 18 casos. Use-a para explicar os mecanismos gerais.

A. Origem da unidade do bloco

Mostre onde assign_units_positional:
- dispõe de evidência positiva para uma unidade;
- está completando uma lacuna pela ordem;
- é influenciado por cabeçalhos, janelas, âncoras ou restrições de sequência.

Explique quando essa inferência posicional funciona, usando acertos como controles, e quando falha.

Afinidade zero não deve, sozinha, virar uma nova regra: precisamos saber quantos acertos dependem desse preenchimento e o que diferencia os erros.

B. Herança e homogeneidade

Explique qual significado unit_slug tem hoje:
unidade obrigatória de todos os materiais, unidade predominante do bloco ou contexto usado como aproximação?

Verifique se esse significado corresponde ao contrato do produto e às fontes.

Nos blocos com materiais de unidades diferentes, esclareça o que o modelo atual consegue representar e o que perde. Não presuma antecipadamente que precisamos de uma reescrita ou de um novo campo.

“Decisão por material” deve significar uma decisão AUTOMÁTICA do motor. A alternativa de pedir rótulos a uma pessoa está descartada.

C. Uso das seções e do próprio corpus

Se considerar evidência dos materiais para estimar a unidade do bloco, identifique riscos de circularidade:
bloco define unidade do material → unidade do material retorna como prova da unidade do bloco.

A evidência deve ter proveniência e não depender da conclusão que pretende justificar.

Aliases EN/PT só podem ser tratados como informação do cru quando sustentados pelos insumos permitidos. Tradução ou relação semântica acrescentada pelo conhecimento do desenvolvedor/modelo é conhecimento externo e deve ser explicitada.

D. Restante dos erros

Integre os 11 erros dependentes de bloco e os sete em que o texto vence errado, reutilizando os diagnósticos existentes. Não limite o plano de unidade aos 18 casos.

Separe a meta geral da meta por curso:
faltam oito acertos no total, mas CG precisa de +11 e SO de +4. As hipóteses devem ser avaliadas também por essa distribuição.

5. PRIORIDADE: DIAGNÓSTICO ATUALIZADO DA SUBUNIDADE

Subunidade primária permanece em 86/251: são 165 não acertos e faltam 140 correções líquidas para ultrapassar 90%.

A entrega não estará completa se detalhar como melhorar unidade e deixar a subunidade apenas como “falta vocabulário”.

Atualize sua anatomia na MESMA base v2, com os 13 materiais presentes. Reutilize resultados válidos, mas não transplante automaticamente as contagens antigas do W-P1/W-U.

Para cada família de erro, diferencie:
- Problema de identidade ou taxonomia.
- Subunidade correta excluída pela unidade.
- Subunidade existente, mas não gerada como candidata.
- Candidata correta disponível, mas seleção errada ou abstenção.
- Decisão correta alterada posteriormente.
- Relação necessária não representada no índice atual.
- Relação não encontrada nos insumos disponíveis, dentro do alcance efetivamente inspecionado.
- Vários assuntos presentes, sem distinção suficiente entre principal, revisão, exemplo, comparação ou pré-requisito.

Registre sobreposições sem somar o mesmo material várias vezes. Se não houver evidência para atribuir uma causa, marque como indeterminada.

Explique o que “subunidade primária” significa operacionalmente e quais sinais disponíveis permitem reconhecê-la. Não substitua a tarefa por multirrótulo para aumentar o placar.

Permitir múltiplas unidades ou tópicos como candidatos internos pode ser investigado como representação; isso não altera a obrigação de avaliar a saída primária pela métrica atual.

6. QUANTIFIQUE QUANTO OS ERROS ANTERIORES EXPLICAM DA SUBUNIDADE

Use os artefatos existentes ou isolamentos mínimos para responder:

- Quanto da subunidade seria recuperado se a unidade correta fosse fornecida como oráculo diagnóstico, mantendo o resolver real e recomputando as dependências?
- Quantos erros persistem mesmo com a unidade correta?
- Em quantos casos a resposta correta já está entre os candidatos?
- Quanto das mudanças de subunidade é efeito direto do material e quanto vem da segunda passada?
- Que relações ou evidências já disponíveis são descartadas antes da seleção?

Use oráculos somente onde houver gold coerente disponível. Não invente rótulos ausentes nem retire esses materiais do denominador.

Separe claramente:
efeito diagnóstico de uma intervenção ideal;
cobertura de candidatos;
ganho de uma regra realmente executável sem gold.

Não apresente um oráculo como solução ou como teto universal. Não some efeitos de intervenções sobrepostas.

Na segunda passada, distinga dependências legítimas, sustentadas por evidência, de circularidade ou propagação sem suporte. Não trate toda influência entre materiais como defeito.

7. PROPOSTA DE DIREÇÃO: NO MÁXIMO TRÊS FRENTES

Depois do diagnóstico, proponha até três frentes, ordenadas por evidência, alcance e risco.

Cada frente precisa informar:
- Causa que pretende corrigir.
- Evidência favorável e contrária.
- Mecanismo geral proposto.
- Diferença real em relação ao que já foi reprovado.
- Materiais e cursos potencialmente atingidos, com sobreposições.
- Alcance separado em bloco, unidade e subunidade.
- Acertos atuais ameaçados.
- Dependências e custos de execução/manutenção.
- Menor experimento que decide se vale implementar.
- Critérios de aprovação, refutação e encerramento.

Não faça uma seleção de exceções pelos IDs recuperáveis. Não invente faixas de ganho. Onde não houver base, declare “não estimável ainda” e a medição necessária.

Uma das conclusões deve tratar explicitamente do grande residual de subunidade: qual frente o enfrenta e qual parcela permanece sem caminho demonstrado.

Se as frentes justificadas não fecharem a distância até 90%, mostre a lacuna restante. Isso não autoriza encerrar a pesquisa, mas impede apresentar melhorias pequenas como solução integral.

Conhecimento externo, se discutido, deve ficar em alternativa separada: qual informação falta, por que não foi obtida do pacote e qual custo teria fornecê-la pela plataforma, sem professor. Nada disso está autorizado para implementação.

8. ENTREGA

Produza um relatório principal com tabelas auditáveis em anexo, não uma coleção de documentos desconectados.

Abra com respostas claras:
1. O que o W-Z já demonstrou?
2. O que agora sabemos sobre onde os erros nascem?
3. O que explica a maior parte dos erros de subunidade?
4. Quais hipóteses continuam sem comprovação?
5. Qual é a próxima frente recomendada e por quê?
6. Quanto da distância até a meta ela pode abordar e o que permanece descoberto?

Inclua um mapa enxuto das dependências relevantes, poucos exemplos completos de fonte → decisão → erro → propagação e controles atualmente corretos.

Toda afirmação sobre implementação deve apontar código real. Toda medição deve apontar artefato e versão. Identifique inferências e desconhecidos.

Termine com uma proposta concreta para o próximo Gate 1, sem implementar nem commitar.

Não quero refazer o diagnóstico que o W-Z já entregou. Quero completar o que falta e transformar os resultados em uma decisão de engenharia fundamentada.
