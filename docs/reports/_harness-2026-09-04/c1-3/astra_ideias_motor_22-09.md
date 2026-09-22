# Parecer GPT-6 Astra — ideias de solução para o motor (22/09/2026)

Origem: resposta ao brief `brief_astra_motor_90_22-09.md`, enviada manualmente pelo usuário e colada
na sessão Claude Code 634847b0 em 22/09. Cópia literal; a validação do coordenador está no tracker
(`docs/reports/pendencias.md`, bloco "Validado: parecer Astra de ideias (22/09)").

---

Minha prioridade seria reduzir a declaração necessária do professor, não substituir novamente o scorer. Faltam 142 acertos de subunidade. Os 95 casos sem rótulo não provam impossibilidade no cru: pode existir uma relação explícita em outro material. Mas, quando duas atribuições diferentes são compatíveis com todos os sinais disponíveis, o motor não tem como garantir qual convenção o professor pretendia. O teto diagnóstico de 52–59% limita as hipóteses examinadas, não todos os algoritmos possíveis.

Protocolo comum: reproduzir primeiro a baseline com a regra já aprovada; depois, replay integral, incluindo segunda passada e efeitos entre materiais. Escolher parâmetros por LOCO aninhado, sem tratar esses cursos como holdout novo. Exigir os critérios de aceite informados e registrar separadamente acerto→erro, erro→acerto e precisão de todas as decisões novas. A ordem abaixo é qualitativa de ganho/risco; as faixas exploratórias não são medições nem devem ser somadas.

Regime 2 — Microdeclarações de relações, escolhidas por cobertura, em vez de pedir um glossário completo.
Premissa: poucos vínculos entre nomes concretos e categorias do plano explicam muitos materiais; IA demonstra essa possibilidade, não sua universalidade.
Mecanismo: extrair expressões de títulos, nomes, rótulos e headings; apresentar ao professor: "Neste curso, esta expressão pertence a qual subunidade?". Mostrar ocorrências e permitir "depende".
Priorizar expressões que cobrem mais materiais ainda sem relação conhecida, sem consultar erros do gold; agrupar apenas variantes lexicais, não presumidos sinônimos semânticos.
Registrar associação escopada à unidade; uma expressão compartilhada exige condição adicional, não um alias global.
Ganho condicionado: reproduzir o efeito do vocabulário compilado levaria aproximadamente a 183–186/251, deixando 40–43 correções até 226; não há evidência de que vocabulário sozinho feche isso.
Por curso: IA tem evidência específica de +33 no ensaio 5→38, cujo comparador difere do 4/39 da base. Para MF/SO/ES2/TCC/CG/FR, os agregados permitem apenas limites de recuperação de 0–33/0–8/0–21/0–4/0–54/0–12, não previsões informadas.
Pedido adicional, se necessário: uma declaração de primazia para materiais multitópicos — extensão explícita do regime 2, além de vocabulário.
Custo hipotético: 20–60 segundos por associação com exemplos já apresentados; 18 associações seriam 6–18 minutos, sem contar ambiguidades. O número mínimo depende da cobertura real.
Riscos: aliases polissêmicos e preferência do professor divergente do gold primário; ambos podem derrubar acertos atuais.
Medição/refutação: professor sem acesso ao gold; curva acertos × associações × tempo, por curso, sob LOCO. Refuta a promessa de intervenção pequena se os ganhos exigirem decisões praticamente arquivo a arquivo.

Cru — Relações explícitas entre documentos, sem consenso de seção nem pseudo-rótulos como prova.
Premissa: parte dos 95 materiais sem rótulo possui, em outro documento, uma ligação textual verificável à taxonomia.
Mecanismo: procurar relações como "Y inclui X", listas de exemplos sob um heading que nomeia Y, ou referência a um arquivo identificável dentro desse escopo.
Usar plano, Markdown, headings, nomes e referências já presentes; aceitar somente relação direta, destino único e contexto instrucional, não bibliografia ou mera comparação.
A ligação nasce do texto, não da unidade atribuída ao documento doador; isso evita reproduzir a dependência problemática da segunda passada. A promoção atual por exclusividade de tokens de títulos/headings é um mecanismo diferente.
Ganho exploratório: 0–12 acertos de subunidade; investigar primeiro materiais de código em IA/CG/SO, sem presumir que contenham essas relações. Aplicabilidade nos demais cursos depende das ocorrências.
Risco: exemplo secundário virar assunto principal; links sob headings amplos; relações ambíguas. Não transformar todos os tokens do documento em aliases.
Medição: inventariar cobertura antes de pontuar; guardar trecho e relação justificadora de cada decisão; comparar com a propagação atual no replay completo e LOCO.
Refutação: ausência de relações explícitas nos casos relevantes, relações predominantemente incidentais ou qualquer perda atual. Sem relação encontrada, a hipótese não autoriza inferência por proximidade.

Cru — Resolver primazia pelo papel do trecho, não por mais peso no título.
Premissa: alguns erros contêm o tópico correto, mas referências, pré-requisitos ou revisão estão sendo tratados como conteúdo principal.
Mecanismo: quando um subtópico aparece explicitamente no objetivo/conteúdo da aula e o concorrente aparece somente em trechos marcados como revisão, pré-requisitos ou referências, preferir o primeiro.
Usar a árvore de headings e expressões estruturais do Markdown; sem marcação explícita de papel, manter a decisão atual. Não é outra ponderação genérica de campos.
Aplicar dentro da unidade vigente; descrições geradas só podem ser separadas quando seus delimitadores forem reconhecíveis — inglês não é indicador suficiente.
Ganho exploratório: 0–6 acertos de subunidade, entre os 47 casos com discriminante presente; o brief não permite distribuí-los por curso.
Risco: documentos de revisão cujo assunto principal é justamente o tópico revisado; objetivos amplos cobrindo várias subunidades.
Medição: ablação "mesmos tokens, com/sem papéis estruturais", mantendo os pesos; LOCO dos padrões e gates; informar sobreposição com os 19 erros recuperáveis pelas variantes anteriores.
Refutação: inexistência dessa assimetria estrutural, nenhum ganho adicional ou perdas nos materiais em que revisão é o objetivo principal. Não usar o conjunto "aceito" para redefinir o alvo primário.

Cru — Corrigir unidade por evidências explícitas de subtópicos, pesquisadas antes da restrição à unidade herdada.
Premissa: a unidade errada fecha a busca de subunidade antes que uma evidência suficientemente específica possa contradizê-la.
Mecanismo: consultar a taxonomia inteira e procurar dois subtópicos distintos, explicitamente desenvolvidos no material, pertencentes unicamente à mesma unidade alternativa.
Exigir frases do plano em escopo instrucional; título repetido no heading não conta como duas evidências. Não usar aliases aprendidos, seção ou bloco para produzir essas testemunhas.
Quando houver esse certificado, corrigir apenas a unidade; não transformar um vencedor léxico comum em autoridade sobre o bloco nem alterar o bloco automaticamente.
Ganho exploratório: 0–8 dos aproximadamente 25 erros de unidade derivados do bloco; triagem em CG/SO pela concentração de erros na base, sem afirmar a distribuição do residual atual.
Riscos: materiais interdisciplinares, revisões e trabalhos abrangentes; a mudança de unidade também pode alterar subunidades de outros materiais pela segunda passada.
Medição: comparar certificado contra override textual simples; medir cobertura e precisão por curso em LOCO; aceitar somente após replay integral preservar bloco e subunidade, não após um teste com esses efeitos congelados.
Refutação: certificados ausentes no residual, presentes também em acertos que seriam perdidos, ou correções limitadas aos casos já cobertos pela regra seção+texto. Não há base para prometer os dez acertos necessários.

Cru — Desempate temporal por evidência contrastiva, sem vantagem decorrente apenas do tamanho da assinatura.
Premissa verificável: parte dos quatro erros do MF decorre de termos compartilhados ou normalização por comprimento, não de evidência exclusiva do bloco errado. Hoje o disamb agrega título/rótulo/Markdown e divide o score pela raiz do tamanho da assinatura.
Mecanismo: entre candidatos da janela, separar termos comuns dos exclusivos; mudar a escolha somente quando um candidato tiver evidência instrucional distintiva contra cada concorrente, sem evidência instrucional conflitante.
Termos incidentais de revisão/referência não sustentam o desempate; na ausência desse certificado, conservar a decisão atual. Aplicar pela configuração da evidência, nunca pelo nome do método anterior.
Sinais: mesmos textos do material e assinaturas dos blocos já disponíveis; nenhuma data inventada e nenhuma expansão automática da janela.
Ganho exploratório: 0–2 dos quatro erros do MF; não projetaria benefício nos outros cursos antes de inventariar os casos elegíveis.
Riscos: perder desempates corretos favorecidos pela normalização atual ou confundir uma menção legítima com referência incidental.
Medição: replay de todas as janelas multicandidatas, LOCO e teste contrafactual de adicionar termos sem correspondência às assinaturas; verificar se a mudança responde à evidência ou só ao comprimento.
Refutação: bloco correto ausente da janela, candidatos indistinguíveis pelos sinais contrastivos, nenhuma recuperação ou qualquer perda entre os desempates corretos.

Para refinar a primeira ideia, precisaria ver a matriz expressão→materiais→campo/trecho, a taxonomia exata, a cobertura das associações do vocabulário já ensaiado e as transições de acerto por curso desse ensaio, com comparadores alinhados. Também precisaria da contagem residual separando ausência de relação semântica, unidade errada, primazia ambígua e entrada ausente. Isso permitiria estimar quantas declarações realmente compram cobertura — e distinguir um formulário pequeno de uma curadoria extensa disfarçada

---

## Réplica do Astra à validação do coordenador (22/09, colada pelo usuário)

Essa validação sustenta uma decisão prática: continuar a frente regime2-declaracao-20260917, agora medindo o menor esforço de declaração que produz ganho real, em vez de abrir outra frente de scorers.

Eu manteria a conclusão registrada como "nenhuma alavanca grande demonstrada no cru", não como impossibilidade geral. E separaria dois objetivos: reduzir bastante o trabalho do professor e alcançar 226/251. O primeiro ainda não garante o segundo.

1. Reconciliar a população antes de dimensionar o formulário

As faixas do meu parecer continuam sendo hipóteses exploratórias, não estimativas validadas pelo fato de a aritmética estar correta. Além disso, os possíveis ganhos de unidade e bloco não entram na conta dos 142 acertos faltantes de subunidade.

Há uma diferença que merece fechamento: 95 + 17 + 47 = 159, enquanto 251 − 84 = 167 não acertos. Portanto, precisamos identificar os oito restantes e alinhar as versões dos diagnósticos. Não presumiria que sejam ausentes, gold vazio ou alguma categoria específica.

A base dessa medição deve ser uma relação dos 251 materiais, cada qual com seu estado na baseline escolhida. As classes já existentes entram como diagnóstico; não substituem esse inventário completo. Isso impede que o formulário pareça cobrir quase todo o problema quando, na verdade, cobre apenas o subconjunto anteriormente analisado.

2. Produzir a matriz de evidências sem transformá-la em seleção pelo gold

A matriz pendente é a primeira peça que eu priorizaria. Cada ocorrência precisa relacionar:

Expressão → material → campo e trecho literal → unidade sugerida → relações já conhecidas → possíveis conflitos.

Ela deve incluir também os materiais atualmente corretos: uma expressão candidata pode ajudar cinco documentos e atingir outros três nos quais seria prejudicial. Olhar apenas os indecisos esconderia esse risco.

A seleção das perguntas pode privilegiar cobertura marginal: quantos materiais adicionais aquela expressão alcança, descontando os já cobertos pelas perguntas anteriores. Essa cobertura é de ocorrências, não de erros recuperáveis, e não consulta o gold.

O professor escolheria o destino na taxonomia e poderia responder "depende" ou "não associar". A unidade inferida seria uma sugestão, não uma restrição: limitá-lo à unidade herdada do bloco poderia incorporar o erro atual à própria declaração.

O registro seria uma relação contextual de pertencimento, não um sinônimo universal. Conflitos com a unidade vigente seriam registrados separadamente, sem autorizar sua alteração automática.

3. Medir uma única declaração, com vários orçamentos simulados no replay

Para respeitar "o professor declara uma vez", proporia uma sessão de preenchimento com perguntas ordenadas por uma política definida sem acesso ao gold. Depois, o harness reproduziria prefixos dessa mesma declaração: primeiras 5, 10, 20 associações, por exemplo.

Assim, não seria necessário perguntar novamente ao professor para construir a curva. Também não se escolheriam retrospectivamente "as dez associações que mais acertaram": isso mediria um seletor-oráculo, não o formulário proposto.

Para cada orçamento, registraria acertos/251, correções, perdas, decisões novas erradas e tempo acumulado do professor, sempre por curso e no total. A precisão das decisões alteradas precisa incluir abstenção→erro; aumentar cobertura sozinho não é sucesso.

Cada prefixo deve reconstruir o estado derivado correspondente, incluindo a segunda passada e caches relevantes. Reaproveitar aliases produzidos com uma declaração maior contaminaria a medição do formulário menor.

Parâmetros e gates continuam sob LOCO; os sete cursos continuam sendo desenvolvimento, não holdout novo. O vocabulário do braço V serve como referência diagnóstica, mas não substitui respostas reais do professor nem mede seu esforço.

4. Usar o residual para descobrir o que vocabulário não resolve

Eu refinaria as quatro classes para evitar chamar toda falha restante de "falta de vocabulário":

| Classe | Critério diagnóstico |
|---|---|
| Entrada indisponível | O pipeline não dispõe de uma entrada utilizável para produzir a atribuição. Markdown ausente, sozinho, não basta se os metadados permitem decidir. |
| Bloqueio pela unidade | A unidade vigente exclui a subunidade correta do conjunto de candidatos. |
| Relação semântica ausente | Há entrada e unidade adequada, mas falta uma ligação utilizável entre a expressão do material e o tópico do plano. |
| Falha de seleção | A relação está disponível, mas o motor escolhe outro candidato ou se abstém. Separar aqui primazia ambígua de erro do scorer. |

Essas classes são diagnósticos de avaliação, não condições de roteamento alimentadas pelo gold. Um material pode ter mais de um problema; registrar sobreposições evita somar recuperações incompatíveis.

Há também um teste de teto simples: 226/251 permite, no máximo, 25 não acertos. Enquanto a busca ficar restrita à unidade atribuída, se a união entre entradas indisponíveis e materiais bloqueados por unidade errada ultrapassar 25, vocabulário sozinho não poderá atingir a meta, mesmo resolvendo perfeitamente os demais casos. Essa contagem precisa ser feita nos 251 materiais; não pode ser importada do denominador de unidade, que é 284.

A próxima entrega analítica, portanto, seria a matriz de evidências acompanhada da reconciliação dos oito casos. Com isso, será possível definir perguntas por cobertura sem consultar o gold. Depois das declarações e do replay, a curva mostrará se existe um formulário realmente pequeno ou se a lacuna exige uma curadoria maior — e qual parte dela sequer responde a vocabulário.

---

## Terceira resposta do Astra (22/09, colada pelo usuário) — aprova a etapa analítica, com cuidados

Sim, faz sentido como plano de experimento — não como comprovação de que uma declaração pequena chegará a 90%. (…) Eu aprovaria essa próxima etapa analítica, não ainda uma mudança no motor.

Cuidados que passam a fazer parte do protocolo do W-P:
1. Reconciliar os 8 por IDENTIFICADOR e estado, não por contagem; alinhar versões dos diagnósticos.
2. Cobertura é critério de prioridade entre expressões que possam sustentar relação contextual, não previsão de ganho nem autoridade para criar a relação; "depende" continua legítimo; nunca selecionar perguntas pelo gold.
3. Custo = perguntas EXAMINADAS (aprovadas + rejeitadas + "depende") e tempo total, não só associações utilizáveis. Cada prefixo usa somente o estado (respostas, aliases, caches) existente naquele orçamento — sem revisão retroativa nem vazamento de etapas posteriores. Materiais do curso são entrada permitida; gold e seleção baseada nele ficam fora.
4. Teto de 25: contar cada material uma vez; "sem Markdown" não é bloqueio se os metadados decidem; unidade errada é bloqueio enquanto a busca ficar restrita à unidade. ≤ 25 torna a meta possível, não a demonstra.
5. LOCO aninhado: seleção e avaliação separadas; zero perdas no replay é exigência a registrar, não garantia para cursos futuros; o formulário passa pelo replay integral com a 2ª passada.

Pergunta decisiva: "Quanto trabalho real do professor é necessário para obter quantas correções, sem perdas, e quais erros continuam fora do alcance dessa intervenção?"
