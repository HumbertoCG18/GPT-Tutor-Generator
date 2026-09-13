**Vocabulário é a principal alavanca demonstrada; aquisição sozinha ainda não sustenta a promessa de 90%.** O desenho deve aprender relações entre técnicas e tópicos, controlar a publicação de aliases e validar transferência em cursos novos.

**MEDIDO nesta sessão:** recontagem dos manifests → cru **146/251**, produto **224/251**; inspeção dos sidecars e do código. Os demais resultados abaixo vêm dos logs existentes. Não reexecutei o motor, não alterei arquivos nem fiz chamadas de rede.

1. **Análise: o enquadramento acerta a direção, mas exagera três conclusões.**

   **“Só o CG tem termos de domínio”: falso.** ES2 contém `circuitbreaker`, `fanout`, `nameserver`; IA contém `crossover`, `geneticos`, `implementacaominimax`. Isso não garante que estejam associados ao tópico certo, mas impede chamar todo o restante de ruído. Evidência: [sidecar ES2:8](C:/Users/Humberto/Documents/GitHub/Engenharia-Software-2-Tutor/course/.glossary_curation.json:8), [sidecar IA:11](C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor/course/.glossary_curation.json:11).

   **“O sidecar manual não é humano”: também é generalização.** Hoje ele mistura geração automática, decisões humanas e intervenções avaliadas no benchmark. O CG registra curadoria humana; ES2 registra `gateway` acrescentado após ganho medido. A nota geral de geração automática não descreve todas as entradas atuais. Evidência: [CG:2](C:/Users/Humberto/Documents/GitHub/Computacao-Grafica-Tutor/course/.glossary_curation.json:2), [ES2:97](C:/Users/Humberto/Documents/GitHub/Engenharia-Software-2-Tutor/course/.glossary_curation.json:97).

   **“Mesmo corpus, diferença apenas na seleção”: parcialmente correto.** Os dois usam materiais do curso, mas não recebem a mesma representação. O determinístico exige seção/SARC que já nomeie um tópico, extrai tokens e usa até **8 headings**; o LLM recebe expressões, até **24 headings**, nomes de membros de ZIP e os tópicos da unidade. O filtro de comprimento mínimo **4** já prejudica siglas curtas. Evidência: `gera_sidecar_professor.py:103–150`; [vocabulary_compile.py:173](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:173).

   O problema principal é **reconhecer a expressão e resolver sua relação curricular**. `Perceptron` não é sinônimo de “Modelos Preditivos”: é uma técnica dessa categoria. `Chiara`, quando aparece como autoria, não expressa essa relação. Frequência e concentração não distinguem necessariamente os dois; um nome de autor pode ser mais exclusivo que uma técnica.

   Esse separador **é computável sem LLM quando há evidência explícita ou conhecimento externo estruturado**: marcação de autoria, definição textual, ontologia técnica ou curadoria humana. **Não há separador geral demonstrado usando apenas os sinais lexicais disponíveis.** O LLM acrescenta conhecimento semântico aprendido, mesmo quando copia todas as expressões do curso. At estar 552/560 expressões não prova que suas associações aos tópicos sejam corretas.

   Portanto: **não demonstramos que LLM seja indispensável; tampouco demonstramos aquisição automática suficiente sem ele.** O número atual sem sidecar LLM e sem voter é **58,2%**. A campanha anterior com aquisição determinística registrou **146/233 = 62,7%**, em outra base; não é teto nem previsão para os 251 atuais.

2. **Desenho executável: classificar relações; publicar um vocabulário compacto.**

   **HIPÓTESE de projeto**, a congelar antes de medir ganho:

   | Etapa | Operação | Critério de parada |
   |---|---|---|
   | Preparar | Congelar plano, títulos, labels, headings e nomes de membros dos arquivos | Todo material representado ou marcado como sem insumo; nenhum truncamento silencioso |
   | Classificar | Associar expressões atestadas aos tópicos, considerando o catálogo completo do curso | Cada proposta tem fonte, relação curricular e destino válido; ambiguidades permanecem pendentes |
   | Selecionar | Remover redundância e limitar publicação por tópico | Nenhuma proposta restante acrescenta cobertura literal dentro do orçamento |
   | Materializar | Gravar sidecar e decisões auditáveis; executar atribuição determinística | Resultado reproduzível com os mesmos artefatos e zero chamadas durante a atribuição |
   | Validar | Comparar política congelada em cursos novos | Uma avaliação final; falha encerra a versão, sem reajuste no conjunto de teste |

   **Fontes.** Reutilizar os leitores existentes. Não usar previsões, confiança, fila, gold, glossário enriquecido nem resumos de código derivados do próprio vocabulário como evidência de pertencimento. Seção Moodle e SARC entram como contexto, sem transformar posição em verdade semântica.

   **Escopo.** Todos os tópicos do plano são candidatos, inclusive os de outras unidades. A unidade calculada pode organizar os lotes, mas não restringir destinos. Hoje essa restrição existe em `vocabulary_compile.py:240–261`: um material mal colocado pode nunca mostrar ao compilador seu tópico correto.

   **Contrato de termo.** Exigir expressão literal, identificação do material/campo/trecho e relação explícita: técnica, algoritmo, protocolo, conceito ou ferramenta ensinada naquele tópico. Uma menção bibliográfica ou enumeração de assuntos não basta. Nome próprio não recebe veto universal: isso também eliminaria termos técnicos legítimos.

   **Seleção de tópico.** Não construir outro ranking de “carência” agora. Examinar todos; publicar apenas onde existam relações aprovadas. O orçamento limita aliases, sem pressupor que os primeiros K tópicos sejam os melhores.

   **Seleção dentro do tópico.** Agrupar variantes do mesmo conceito. Priorizar a expressão que cobre mais materiais ainda não cobertos por outra expressão aprovada daquele tópico; desempate por ordem normalizada. Acrescentar variante somente se alcançar material adicional. Isso mede **cobertura textual**, não acurácia.

   **Orçamento proposto:** máximo de **8 conceitos por tópico**, até **3 variantes por conceito**. São limites operacionais, sem alegação de optimalidade; devem permanecer fixos durante a avaliação. Não escolher esses limites varrendo os sete cursos.

   **Não fazer:** aumentar K até melhorar o placar; usar `score > 0` como evidência; excluir termo porque aparece em outra unidade; preencher tópico sem evidência; tratar todas as ocorrências de uma expressão como aulas daquele assunto.

   **Autoenvenenamento:** acrescentar o sidecar não remove aliases errados já doados pelos headings. Essa doação existe em [content_taxonomy.py:603](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:603). Comparar, como ablação previamente definida, **adição** versus **substituição dos aliases adquiridos automaticamente**, preservando plano e decisões humanas. Não presumir que desligar a doação melhora o resultado.

3. **Contrato mínimo de LLM, cache e dependência do gold.**

   **Hoje:** uma chamada por unidade com materiais; nenhuma quando existe arquivo manual; cache pela existência do `.llm.json`, sem validação de mudança do corpus nessa decisão. Um curso sem unidades calculadas não compila. Evidência: [vocabulary_compile.py:221](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:221).

   **Proposta:** empacotar os registros antes de chamar, com catálogo completo de tópicos em cada pacote e limite de **24.000 caracteres por entrada completa**, sem cortar materiais pela metade. O empacotamento determina **B chamadas por curso antes da primeira chamada**. Não existe número constante honesto para cursos de tamanhos diferentes. Pacote que exceda o limite precisa de divisão explícita; catálogo que sozinho exceda o limite interrompe esta versão do contrato.

   Fixar também **4.096 tokens de saída por chamada**, sem tentativas adicionais automáticas. Falha, JSON inválido ou saída truncada permanece falha registrada; não autoriza uma campanha ilimitada de reparos. Orçamento: **B tentativas**, até **24.000 × B caracteres de entrada** e **4.096 × B tokens de saída**. Valor monetário depende do modelo/preço escolhido; não foi calculado.

   Manter `course/.glossary_curation.llm.json`, compatível com o loader. Acrescentar metadados para hash das entradas, prompt, modelo/configuração, resposta original, evidências, rejeições e seleção publicada. O cache precisa identificar esses componentes; “arquivo existe” não garante atualidade.

   O humano pode produzir o mesmo contrato sem chamada, usando `course/.glossary_curation.json`. O loader já funde ambos e aceita vetos manuais; **os tratamentos não são perfeitamente iguais**, pois há filtro adicional para termos do arquivo LLM. Evidência: [repo.py:1728](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/repo.py:1728). A presença de um arquivo manual parcial deve deixar de bloquear o curso inteiro; preservar decisões humanas por entrada.

   **Curso novo:** extrair materiais e plano → compilar vocabulário sem depender das unidades previstas → atribuir com voter desligado. Sem serviço e sem curador, executar a base disponível e registrar aquisição pendente. Não prometer 90%.

   **Definição do cru:** atribuição determinística usando vocabulário previamente compilado por LLM é possível. Porém, no experimento atual, isso corresponde ao braço **VOCAB**, não à RÉGUA. Se “cru” proíbe LLM em toda a cadeia, a alternativa é curador/ontologia; ainda não existe resultado que assegure 90% nessa condição.

   **Gold do prompt v2:** voltar ao v1 no IA mede sensibilidade ao prompt, não elimina retrospectivamente o ajuste ao IA. Uma compilação por versão também mistura efeito do prompt e variação de geração. Esse teste é diagnóstico, não validação de transferência.

   A dependência não se limita ao prompt: há curadorias posteriores medidas no benchmark, como `gateway`; e igualdade `_raw` versus filtrado em K=5/K=40 não prova inocuidade dos filtros em toda configuração.

   **Como quebrar o ciclo:** congelar prompt, seleção, orçamento e tratamentos de legado agora; avaliar em novos cursos. Para comparar v1/v2, gerar ambos do mesmo corpus novo, com orçamento e condições pareados, antes de abrir rótulos. Declarar antecipadamente o candidato principal; escolher o vencedor após ver o teste exige outro conjunto de confirmação.

4. **Validação: sem gold na aquisição; com referência independente para medir acurácia.**

   **Não existe validação de “90% correto” sem alguma verdade de referência.** Sem adjudicação, podemos verificar procedência, cobertura, estabilidade e colisões. Nenhuma dessas medidas substitui acurácia.

   **LR:** contei **7 entradas**, incluindo **1 cronograma**. Já existe sidecar LLM, portanto não é um teste de partida sem artefatos. Evidência: [manifest LR:45](C:/Users/Humberto/Documents/GitHub/Laboratorio-de-Redes-Tutor/manifest.json:45), [sidecar LR:2](C:/Users/Humberto/Documents/GitHub/Laboratorio-de-Redes-Tutor/course/.glossary_curation.llm.json:2).

   Adjudicar **as 7 entradas**: elegibilidade, unidade curricular, subunidade primária, alternativas aceitáveis e ausência legítima de subunidade, sempre com evidência. Resolver apresentação/cronograma pelo contrato previamente escrito. Dois avaliadores sem acesso às previsões; desacordos resolvidos antes de abrir resultados. Reconstruir os braços a partir das fontes, sem herdar o sidecar existente.

   LR serve para verificar o procedimento. Mesmo **6/6** acertos dariam limite inferior binomial unilateral de 95% de apenas **60,7%**, sob independência. Não certificam transferência.

   **Orçamento de validação proposto:** além do LR, **300 materiais em 6 cursos novos, 50 por curso**, sorteados com regra fixada antes da avaliação e controle de duplicatas. É um compromisso operacional, não tamanho mágico. Reportar resultado agregado, por curso e ganhos/perdas pareados.

   Sob independência, **279/300 = 93%** ultrapassa o teste unilateral de 5% contra 90%; **270/300** apenas atinge a meta pontual. Materiais do mesmo curso são correlacionados: não usar esse cálculo isolado como certificado de generalização.

   Comparar com **RÉGUA**, aquisição determinística do professor, compilação atual sem seletor, **maior unidade** e seleção aleatória. Nos rankings, igualar tópicos/aliases publicados; na comparação operacional, reportar também chamadas e volume processado. Comparar orçamento igual, não apenas K igual.

   Os sete cursos atuais continuam úteis para regressão e diagnóstico. LOCO neles pode refutar outra hipótese; não restaura sua condição de teste independente após tantas decisões informadas pelos resultados. Se a versão falhar nos novos cursos, eles passam a desenvolvimento.

5. **Erros residuais, unidade e meta realista.**

   **Os 25 erros comuns não são todos de aquisição.** Recontagem: **24** estão na unidade considerada correta, **6** têm gold vazio e **16** são do CG. Nos cinco vazios do CG, as notas do gold registram assunto sem subtopico correspondente dentro da unidade exigida. Acrescentar um alias positivo não representa essa ausência. Exemplo: [subunit_gt_CG.csv:36](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/subunit_gt_CG.csv:36).

   Os demais precisam de diagnóstico individual: expressão ausente, associação errada, competição apesar de evidência ou conteúdo insuficiente. `microsservicos2`, por exemplo, recebe do produto um tópico semanticamente próximo, mas diferente do gold; não basta chamar isso de falta de palavra.

   **Dos 14 vazios do cru, o produto acerta 11; 3 também pertencem aos 25 erros comuns.** São conjuntos sobrepostos. Os 11 são candidatos à investigação da aquisição, mas o produto inclui voter: o ganho ainda precisa ser decomposto. Evidência recontada em [erros_subunidade_motor_12-09.csv:12](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/erros_subunidade_motor_12-09.csv:12).

   **Unidade:** faltam **3 acertos líquidos**, de **253 para 256/284**. O vocabulário atual entrega **255/284**, apenas **+2 líquidos**; o voter acrescenta **+8**, chegando a 263. Portanto, os 10 materiais exclusivos do produto não demonstram recuperação integral pela mesma aquisição. Evidência: [motor_3eixos_v2_12-09.log:133](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_v2_12-09.log:133), [motor_3eixos_produto_12-09.log:34](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_produto_12-09.log:34).

   A aquisição global pode corrigir associações e a unidade dos blocos. Porém, quando o texto já aponta a unidade correta e perde para o bloco, mais vocabulário no material não resolve necessariamente: a precedência permanece em [file_map.py:789](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:789). **Não proporia peça nova de unidade antes de decompor esses 10 nos três braços.**

   **Subunidade:** 90% exige **226/251**. O VOCAB completo demonstra **220**, faltam **6 líquidos**. Os **222** escolhidos com gold pertencem a outro procedimento e não constituem teto matemático; faltam **4** naquele experimento. O produto fica em **224**.

   Meta honesta em três entregas: **aquisição auditável e independente das previsões → ganho transferível medido → tratamento dos resíduos que aquisição não representa**. A faixa **87,6–88,4%** é referência histórica de capacidade observada com vocabulário, não previsão para curso novo. **Não há evidência para prometer 90% em um número fixo de passos, com ou sem LLM.**

   Próximo passo concreto: congelar esse contrato de aquisição e o protocolo de adjudicação das **7 entradas do LR**, antes de implementar ou recompilar.
