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


## 4ª resposta do Astra (22/09, após W-P1/W-P2'/W-S e #49; enviada pelo usuário)

Humberto, eu descartaria a opção 1 como requisito do produto, seguiria com a CRU-03 e não trataria a opção 3 como uma obrigação de aceitar 33,5%. A conclusão correta, por enquanto, é que as estratégias medidas saturaram — não que todas as soluções possíveis foram esgotadas.

Também preciso revisar minha recomendação anterior: a declaração mínima do professor era uma hipótese de intervenção barata. O resultado que você trouxe enfraquece essa hipótese: 76 perguntas com muitas respostas “depende”, ou 261 intervenções para chegar a 84,9%, não atendem ao fluxo de uma plataforma que o aluno deve conseguir usar sozinho.

Não faz sentido transformar esse custo em responsabilidade do professor — nem simplesmente transferir as mesmas perguntas para o aluno.

1. A CRU-03 é o próximo passo certo, mas precisamos separar seus dois benefícios

Com os números do relatório, a unidade está em 246/284 e precisa de mais dez acertos para ultrapassar 90%.

Portanto, investigar os 17 bloqueios tem um objetivo relevante por si só: melhorar a unidade e remover restrições que impedem a subunidade correta de sequer ser considerada.

Entretanto, é importante não misturar os resultados:

Resultado investigado    O que representa
Corrigir a unidade    Um ganho real no segundo eixo.
Liberar a subunidade correta como candidata    Remoção de um bloqueio, não garantia de escolha correta.
Escolher automaticamente essa subunidade    Um ganho adicional que precisa ser medido.

Não podemos partir dos 213/251 do W-S e somar os bloqueios corrigidos como previsão do produto automático. Aqueles 213 dependem das intervenções humanas que você rejeitou.

A comparação principal da CRU-03 deve partir do cru atual, com 84/251, mantendo a declaração desligada. Em uma conta apenas de efeitos diretos, recuperar os 17 materiais levaria a 101/251; efeitos sobre outros materiais precisariam aparecer no replay integral.

Isso não diminui a importância da CRU-03. Apenas deixa claro que corrigir unidade é uma etapa necessária de saneamento, não a solução inteira da subunidade.

2. O fracasso dos aliases está dizendo algo importante sobre a representação

O dado mais interessante da CRU-02 não é apenas o teto de 118/251. É este:

65–70% das perguntas por expressão resultam em “depende”, e o alias desloca materiais de subtópicos irmãos.

Minha interpretação — hipótese, não conclusão demonstrada — é que o motor pode estar tentando representar uma relação contextual como uma associação fixa.

A regra:

“A expressão X pertence ao subtópico Y.”

pode estar tentando substituir uma pergunta diferente:

“Neste material, X está sendo ensinado como assunto principal, usado como exemplo, mencionado como pré-requisito ou comparado com outra coisa?”

Isso é compatível com uma limitação conhecida das representações baseadas apenas em ocorrências de palavras: elas não preservam, por si, a estrutura e as relações do texto. A documentação do scikit-learn explicita essa limitação para representações bag of words. Isso não prova que seja a causa dos seus erros, mas ajuda a formular o teste correto.

O W-S já testou guarda de escopo. Portanto, dizer apenas “vamos adicionar contexto” seria repetir o que vocês fizeram.

A diferença que ainda vale esclarecer é:

O sistema consegue obter automaticamente, dos documentos existentes, a relação que no W-S precisou receber da pessoa?

Essa é uma questão diferente de melhorar o formulário ou aumentar o vocabulário.

3. A investigação seguinte deveria procurar relações documentadas, não outra combinação de pesos

Há uma distinção decisiva dentro dos 106 casos de “relação ausente”:

Situação A: a relação não está representada no vocabulário que o motor usa.

Situação B: a relação não aparece em nenhum dos sinais disponíveis, nem no material, nem no plano, nem em outro documento do pacote.

Essas situações não autorizam a mesma conclusão. Na primeira, pode haver informação não aproveitada. Na segunda, precisamos discutir de onde viria a informação adicional.

Um exemplo do que procurar

Considere este exemplo hipotético, usando os termos do seu brief. Um documento do curso apresenta a estrutura:

Modelos Preditivos
    Redes neurais
        Perceptron

Outro material tem o título “Implementação do perceptron”.

O primeiro documento pode fornecer uma relação explícita que falta ao segundo. Não seria necessário saber antecipadamente o que é perceptron, nem consultar uma LLM: a ligação estaria documentada no próprio pacote.

A proposta seria preservar algo como:

Expressão → relação explícita → tópico → documento e trecho que justificam a ligação.

Extrair determinadas relações de textos por padrões lexicais e estruturais é uma abordagem estabelecida; o trabalho de Hearst, por exemplo, trata da aquisição de relações de inclusão semântica a partir de padrões textuais. A existência dessa técnica não demonstra cobertura suficiente nos seus cursos.

Também não basta encontrar uma ligação para decidir o assunto principal. Um material pode comparar dois algoritmos ou mencionar um deles como pré-requisito. Por isso, a relação deveria permanecer vinculada ao trecho e ao contexto, em vez de virar imediatamente um alias global.

Isso não é o consenso de vizinhos já refutado. Estar na mesma seção não constitui a relação. Tampouco é aprender todos os tokens de um documento previamente classificado com confiança.

Essa via já apareceu no parecer anterior. Não estou apresentando-a como descoberta nova ou ganho garantido. O resumo da CRU-02 não estabelece se essa obtenção automática de relações foi medida. Antes de abrir outra implementação, eu verificaria a sobreposição com os experimentos existentes.

O primeiro resultado útil seria uma contagem: quantos erros têm uma relação explícita recuperável no pacote e quantos realmente não têm? Sem essa cobertura, não há justificativa para construir um mecanismo maior.

4. “Sem professor” não precisa significar “sem nenhuma fonte de conhecimento”

Existe ainda uma separação de requisitos que a lista de três opções esconde.

Você quer uma plataforma que o aluno consiga usar sem depender do professor. Também quer execução barata, determinística e sem obrigatoriedade de LLM ou rede. Esses requisitos não são idênticos a exigir que todo conhecimento de domínio venha exclusivamente do plano e dos arquivos daquele curso.

Caso as relações realmente estejam ausentes do pacote, existe uma alternativa de produto: conhecimento geral embarcado, mantido pela plataforma, e não declarado por cada professor.

Por exemplo, há estruturas curriculares públicas de Computação, como o CS2023 da ACM/IEEE-CS/AAAI, organizadas em áreas, unidades e tópicos. Elas poderiam ser fontes candidatas para estudar uma camada de conhecimento geral — não um mapeamento pronto para a taxonomia particular de cada disciplina.

Isso estaria fora do cru estrito atual. Precisaria de um regime separado, avaliação própria e atenção a manutenção, licenciamento, cobertura e ambiguidades. Não estou sugerindo embutir uma lista de exceções dos sete cursos, nem chamar um vocabulário externo de “cru”.

Também não prometeria 90%: o próprio ensaio de vocabulário que vocês relataram mostra que acrescentar conhecimento não resolve automaticamente todos os erros de seleção.

Mas essa alternativa importa porque não obriga a escolher entre professor rotulando arquivos e produto permanentemente limitado a 33,5%. Ela muda uma restrição técnica sem abandonar a autonomia do aluno.

5. A decisão que eu passaria ao agente

A opção 1 está descartada como requisito do produto. A plataforma deve funcionar para o aluno sem depender de rotulação pelo professor, e esse trabalho não será simplesmente transferido ao aluno.

Prosseguir com a CRU-03, medindo as correções de unidade e seus efeitos reais na subunidade a partir do cru atual, sem declaração. Os resultados do W-S permanecem como diagnóstico, não como previsão do desempenho automático.

Não encerrar a pesquisa de subunidade nem declarar 33,5% como teto geral. Após a CRU-03, esclarecer se “relação ausente” significa ausência no vocabulário atual ou ausência em todo o pacote disponível. Verificar se a extração automática de relações explícitas já foi testada; se não, propor primeiro um experimento de cobertura, antes de implementação.

Manter denominadores, critérios de preservação e avaliação por LOCO. Nenhum curso conhecido será tratado como holdout novo. Qualquer proposta com conhecimento externo deverá ser identificada como outro regime e submetida a uma decisão separada.

Você não precisa aceitar um número baixo como destino. Mas continuar a pesquisa precisa significar testar uma hipótese diferente, não repetir a mesma família de soluções esperando outro resultado. Neste momento, eu manteria a meta e mudaria a pergunta: de “como conseguir mais aliases?” para “qual relação falta, onde ela pode ser obtida automaticamente e como preservá-la sem transformar contexto em regra global?”

## 5ª resposta do Astra (22/09, após W-T e W-U; colada pelo usuário)

Humberto, eu avançaria com a importação offline, mas não aprovaria o critério de "precisão > 50% nos 84 certos" como autorização para mudar o motor. Também resolveria as inconsistências da régua antes de usar os próximos resultados para declarar um teto.

Os novos resultados mudam a investigação: W-T reprova as alternativas medidas de precedência da unidade; W-U mostra que encontrar relações não basta para escolher a subunidade. A proposta de relações explícitas que eu sugeri não se confirmou como solução autossuficiente. Isso precisa ser reconhecido, sem transformar a reprovação dessa hipótese em prova de que todo o problema terminou.

### 1. Importação offline: favorável ao Gate 1, com o ganho explicado por material

É a prioridade mais concreta. Porém, o resumo deixa uma conta que precisa ser esclarecida: há 13 ausentes — 12 links e um PDF —, mas atribui +13 à importação dos 12 links. Isso pode ter uma explicação, como a recuperação adicional do PDF ou um efeito sobre outro material; o handoff não a apresenta.

Partindo de 246/284, as contas são:

| Recuperação direta | Resultado possível, sem perdas |
|---|---|
| Os 12 materiais correspondentes aos links | 258/284 — 90,8% |
| Os 12 links e o PDF ausente | 259/284 — 91,2% |

Ambos ultrapassam a meta. Portanto, não é necessário apoiar a decisão naquele décimo terceiro ganho ainda não explicado.

Eu aprovaria um escopo específico: importar os materiais ou snapshots já disponíveis localmente, preservar identidade e metadados de origem e reproduzir o pipeline completo, sem rede ou LLM no cru. O relatório de aceite deve mostrar quais materiais passaram de erro para acerto e qualquer efeito nos outros eixos.

A disponibilização da entrada não equivale, por si, à classificação correta. O resultado precisa continuar sendo confirmado pelo replay, não inferido apenas da quantidade de ausentes.

### 2. A régua precisa de uma correção auditável, não de uma flexibilização

O handoff registra quatro materiais de SO com unidade e subunidade de gold incompatíveis, um slug repetido entre unidades e um gold vazio em TCC. Essas inconsistências impedem interpretar parte dos erros como falha exclusiva do motor.

O procedimento adequado é manter a régua histórica congelada e produzir uma versão corrigida, sustentada pelos materiais e pela taxonomia — não pela resposta que o motor deu. Os materiais e denominadores permanecem; as diferenças decorrentes de anotação ficam separadas dos ganhos de algoritmo.

Também esclareceria dois pontos nos artefatos antes de consolidar as conclusões:

A cobertura de W-U: 56 + 53 + 70 = 179, enquanto o total citado é 178. Pode haver sobreposição ou diferença de população; os identificadores precisam explicar isso. Não estou presumindo que o experimento esteja errado.

Os quatro "custos da #48": é necessário dizer se são efetivamente quatro transições acerto→erro provocadas pelo commit ou erros remanescentes atribuídos àquela lógica. Se forem regressões reais, existe uma incompatibilidade com o critério registrado de zero perdas, que precisa ser explicitada — não absorvida pelo saldo positivo.

Essas verificações não servem para elevar artificialmente o placar. Servem para não exigir do motor respostas simultaneamente incompatíveis nem interpretar ganhos com populações diferentes.

### 3. W-U não significa 177 classificações erradas — mas o gate proposto é insuficiente

O índice foi construído sem gold e sem saídas do motor. Segundo o relatório, quase todos os materiais cobertos também possuem relações com tópicos incorretos, com 5–19 concorrentes. Isso demonstra que a existência de uma relação é um sinal pouco seletivo. Não demonstra, sozinha, que nenhum critério conseguiria ordenar os candidatos corretamente.

A separação necessária é:

Gerar candidatos: colocar o tópico correto entre as opções.

Selecionar: escolher o tópico correto sem ser desviado pelas relações concorrentes.

Entretanto, superar 50% nos 84 materiais atualmente corretos não atende ao aceite do projeto. Nesse subconjunto, o motor atual já acerta todos, por definição. Um novo seletor poderia ultrapassar 50% e ainda destruir dezenas de acertos.

Esse limiar pode, no máximo, funcionar como uma triagem exploratória. Para justificar integração, o teste precisa demonstrar:

Preservação dos acertos atuais, sem usar uma lista desses materiais para protegê-los durante a execução.
Correções no residual, com precisão calculada sobre todas as decisões novas ou alteradas, incluindo abstenção→erro.
Acionamento baseado apenas nos sinais disponíveis, com parâmetros escolhidos por LOCO e replay integral dos três eixos.

"Sem gold" deve qualificar a construção do índice e a inferência. Para medir precisão, a comparação com o gold é justamente a avaliação permitida. Além disso, como W-U cobre 70 dos 84 acertos, o relatório precisa distinguir precisão sobre decisões emitidas de desempenho sobre o denominador completo.

Eu admitiria um experimento delimitado de seleção, não uma implementação antecipada nem uma busca indefinida por pesos. Ele precisa explicitar qual evidência distingue uma relação principal de uma menção incidental e medir o que isso acrescenta às variantes já reprovadas.

### 4. Os 40 casos sem relação tornam a próxima pergunta mais precisa

O handoff classifica 40 casos como "B puros", que exigiriam fonte externa. Essa é a conclusão registrada para o pacote e a análise examinados.

Há uma consequência matemática importante:

Se esses 40 materiais continuarem errados, mesmo acertando todos os demais, o máximo será 211/251 — 84,1%.

Para chegar a 226, seria necessário recuperar pelo menos 15 desses 40, mesmo no cenário ideal em que todos os outros materiais fossem resolvidos. Havendo outros erros residuais, seria necessário recuperar mais.

Esse 211 é uma conta condicional nova, baseada nos 40 casos. Não é a validação do antigo teto de W-S, que utilizava os 17 bloqueios posteriormente revisados para dez.

Mas eu repetiria essa análise depois da importação offline. A importação altera o pacote disponível: os documentos recuperados podem conter relações úteis para outros materiais. Isso é uma possibilidade a medir, não um ganho que já podemos contabilizar.

Assim, a próxima comparação deveria mostrar quantos dos 40 continuam sem relação após a entrada ser completada. Se permanecerem, um seletor restrito ao índice atual não terá demonstrado como resolver a lacuna.

Nesse ponto, discutir conhecimento externo embarcado seria uma mudança explícita de regime, sem professor e sem necessariamente exigir rede durante a execução. Não seria legítimo chamá-lo de cru atual, mas também não seria equivalente a desistir da autonomia do aluno. Essa decisão continua separada, como vocês já registraram.

### 5. CRU-04: manter a investigação, mas com o alvo por curso correto

O bloco já ultrapassou 90% no total, mas MF permanece em 56/66. Para ultrapassar 90% nesse curso, precisa chegar a 60/66: mais quatro acertos.

Os seis desempates residuais listados no handoff não são seis casos de MF: são três de MF, um de IA e dois de CG. Portanto, corrigir apenas os três desempates de MF levaria a 59/66 — 89,4%, ainda abaixo da meta.

Isso orienta o esforço: não concentrar toda a frente em desempates esperando que eles, sozinhos, fechem MF. A importação e as outras famílias de erro também precisam entrar nessa conta.

O documento registra que V4 corrigiria exerciciosdafny2, mas isso não substitui o aceite integral para eventual adoção. E "indistinguível" precisa sempre indicar em quais sinais ou representação os candidatos são indistinguíveis. Se a evidência disponível à regra é a mesma, trocar pesos não cria a informação que falta.

### 6. Meu parecer sobre as decisões solicitadas

Gate 1 da importação offline: favorável, com escopo local, rastreabilidade das transições e avaliação dos três eixos.

CRU-04: favorável à investigação focalizada, sem presumir que os seis desempates pertencem a MF ou que outra variante de score fechará o curso.

Subunidade: favorável apenas a um experimento de seleção bem definido, preferencialmente depois de completar a entrada e resolver as inconsistências da régua. O limiar de 50% não serve como aceite de integração.

Gate 2 documental: favorável ao registro dos oito artefatos e do parecer correspondente, deixando as ressalvas explícitas. Esse commit registra experimentos, inclusive hipóteses reprovadas; não aprova uma nova regra. A autorização efetiva continua sendo sua, sem incluir push, PR ou merge. O handoff identifica esses arquivos como pendentes e separa essas autorizações.

A direção agora não é aceitar 33,5% nem continuar tentando qualquer heurística. É completar a entrada, tornar a avaliação consistente e separar os erros que ainda têm evidência selecionável daqueles que exigem informação adicional. Isso mantém a meta, mas exige que cada próxima frente explique concretamente de onde virão os novos acertos.

### Conferência do coordenador (22/09, por ID)

- "+13 com 12 links": os 13 ausentes do W-T são 12 links (MF `eth2`, `aws-encryption-sdk`, `archive-of-formal-proofs-355fb8`; IA `o-que-é-inteligência-artificial…`, `ia-responsável…`; CG 7 vídeos) + 1 PDF (MF `t1-2026-1`). 246 + 12 = 258 (90,8 %) já cruza; + o PDF = 259. O handoff-49 escrevia "12 links (+13)" por imprecisão; corrigido.
- W-U: 56 + 53 + 70 = 179 cobertos; A puro 1 + 1 + 0 = 2; A-conflitante 55 + 52 + 70 = 177. O correto é "177 dos 179 cobertos"; as três populações (106/53/84) são disjuntas por construção. Corrigido no tracker e no handoff-49.
- "4 custos da #48": não são regressões. `aceite_v4_48_22-09.json`: `perdas_novas_vs_47.unidade = []` e `cursos_que_regridem_vs_47 = []`. Dos 4 `texto_vence_errado` (CG), 2 mudaram de unidade sob a #48 por `texto-vence-vizinho` (`openglbasico` u02→u03, `texturas-v3` u02→u01), erro→erro; 2 (`morfologiamatematicapptx`, `pagina-com-videos-sobre-morfologia-matematica-06265a`) não têm razão da #48 (texto > bloco por score). Rótulo correto: "texto vence errado 4, 0 regressões da #48". O critério de zero perdas está preservado.
