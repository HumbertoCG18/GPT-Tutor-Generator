**Meta proposta para o tracker: “Motor local sem modelos nem APIs obrigatórios; buscar ≥95% de precisão nas atribuições automáticas, com ≥80% de cobertura por eixo, em cursos inéditos; declaração do professor e LLM serão regimes opcionais, avaliados separadamente.”**

Isso **reduz a exigência original de acurácia total**. É uma meta proposta, ainda não demonstrada. Hoje, nenhum resultado autoriza prometer esses números.

1. **Veredito: a meta original não está demonstrada; os experimentos não provaram impossibilidade.**

   **MEDIDO anteriormente, conferido nos registros; não reexecutado nesta revisão:** o produto com LLM ainda precisa de **7 acertos de unidade e 53 primários** para alcançar 95%. O FR criado do zero entrega **6/18 primários** sem LLM e **16/18** com vocabulário compilado. Isso demonstra distância e efeito do enriquecimento naquele curso; não estabelece teto. [Handoff §33:2043](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:2043), [FR:2089](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:2089).

   Duas correções no enquadramento:

   - **“Cru honesto” não significa “criação automática só com fontes”.** Mantém o ruling humano sobre OpenGL. Retirando-o, o registro cai de **253→248 unidades e 100→95 primários**. Além disso, o driver copia o produto existente; retirar sidecars não certifica a origem de todos os derivados. [§29:1705](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:1705), [driver:67](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py:67).
   - **“Nenhuma alavanca sobrevivente” vale para as versões e os recortes testados.** Não fecha toda técnica determinística possível. O próprio handoff registra que um “teto” por classificação de erros caiu quando o braço V foi executado. [§32:1983](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:1983).

   **Inferência:** sem uma política observável de primário, duas pessoas podem fornecer entradas idênticas e esperar prioridades diferentes. O motor não consegue distinguir essas intenções ausentes. Isso impede uma promessa irrestrita sobre qualquer professor; **não prova que 95% seja inalcançável numa população delimitada**.

   Portanto: **retirar a promessa universal; manter 95% total como objetivo de pesquisa.** Não há hoje caminho validado que permita transformá-lo em compromisso de entrega.

2. **Meta revista: separar autonomia, qualidade e trabalho humano.**

   Recomendo três regimes, com a mesma régua de qualidade:

   | Regime | Insumo adicional permitido | Compromisso pretendido |
   |---|---|---|
   | **Cru automático** | Apenas fontes originais e regras gerais congeladas | Aluno processa e sincroniza sem curadoria ou modelo |
   | **Cru com declaração** | Mapa curricular fornecido pelo professor responsável | Aluno recebe a configuração pronta; declaração versionada |
   | **LLM opcional** | Relações produzidas por modelo, com origem registrada | Ganho separado; desligar o recurso preserva o funcionamento cru |

   **Critério proposto para chamar um eixo de automático:** precisão ≥95% entre decisões liberadas **e cobertura ≥80% dos materiais elegíveis**. O piso de 80% é uma proposta de produto: aceita até 20 encaminhamentos por 100 materiais naquele eixo. **Não é um resultado observado nem uma previsão de viabilidade.**

   Publicar sempre, por eixo e regime:

   **Acurácia total** = acertos / todos os elegíveis; abstenção não conta como acerto.  
   **Precisão automática** = acertos liberados / decisões liberadas.  
   **Cobertura automática** = decisões liberadas / todos os elegíveis.  
   **Fila e erros liberados** = contagens por 100 materiais.

   Para subunidade, **primário continua sendo a métrica principal**. “Aceito” fica como diagnóstico secundário; não substitui o principal. Material sem tópico representável ou sem evidência suficiente permanece visível como falha de cobertura da tarefa. A elegibilidade não pode ser escolhida depois de ver a saída.

   Não reduziria o padrão de qualidade de um eixo por estar pior. Mudaria a prioridade de trabalho: bloco está próximo no registro existente; unidade exige respeitar a política curricular; subunidade exige aquisição e prioridade. **Os 17 erros de desenho continuam erros.** O usuário já decidiu que o plano deve prevalecer conceitualmente; removê-los do denominador contradiz essa decisão. [§26:1360](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:1360).

   Publicar também **acerto conjunto e fila por material**: três eixos com 95% individualmente não significam 95% dos materiais inteiramente corretos.

   O contrato funcional pode exigir execução local, proveniência e reprodução entre criação/resync. **O contrato numérico só poderá ser anunciado depois da validação**, com população, cobertura e incerteza declaradas. O rótulo atual de confiança não fica certificado por essa troca de meta.

3. **Congelar uma comparação que realmente isole o elo faltante.**

   **Primeiro, corrigir o desenho do inventário.** As “25 candidatas” da §39 são emitidas **depois** de a categoria casar exatamente com um tópico: `matched = anchors.get(norm(category), [])`. Não representam todas as relações locais encontradas antes da ancoragem. [Extrator:169](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/extrator_relacoes_14-09.py:169).

   O futuro harness deve salvar **categoria → termo → trecho → documento:linha antes desse filtro**. Reaproveitar `scan` e os filtros congelados; mudar apenas o mecanismo que liga categoria ao tópico. [Extrator:61](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/extrator_relacoes_14-09.py:61).

   **Congelamento comum:** commit, fontes e hashes, taxonomia, política de primário, população elegível, extrator, filtros, consumo das relações, seletor de confiança, parâmetros e critérios de aprovação. Congelar também a máquina de referência e os limites de memória/tempo antes da execução. “Máquina fraca” ainda não define um limite verificável.

   As fontes devem ser reconstruídas desde os originais. Excluir gold, análises de erro, predições, sidecars antigos, resumos e descrições de imagens por LLM. A origem de taxonomia, cronograma e metadados derivados também precisa ser comprovada. No cru, bloquear a rede durante **toda a execução**, não apenas no reprocessamento.

   Rodar quatro braços independentes: **base estrita, base+A, base+B, base+C**. Mesmos candidatos, tópicos, filtros e consumidor. Nenhum braço herda relações produzidas por outro. Os sete cursos conhecidos servem para desenvolvimento e regressão; nenhum resultado neles será chamado de validação inédita.

   **A — correspondência lexical fraca. Regra proposta, congelável:**

   Normalizar com `norm` existente. Tentar primeiro a igualdade de `anchor_names`; correspondência exata ambígua é rejeitada. Sem igualdade, comparar tokens após remover somente:

   `a o as os de da do das dos e em para por com um uma modelo modelos tarefa tarefas`

   Um token casa por igualdade ou por **prefixo comum de pelo menos 7 caracteres**. Todo token restante do rótulo precisa casar com algum token da categoria; rótulo sem tokens é rejeitado. Aceitar somente **um tópico candidato em todo o curso**. Não desempatar por score do motor, unidade predita ou frequência dos erros. Não acrescentar sinônimos, traduções ou exceções por curso.

   Isso admite `tarefa preditiva → modelos preditivos`. Também pode admitir indevidamente `estatística descritiva → modelos descritivos`: **esse risco faz parte da hipótese**. Não remover o caso depois para salvar o braço. `Tarefas Supervisionadas` não vira `Modelos Preditivos` por essa regra. Resultado negativo encerrará essa versão lexical, sem afirmar que encerrou toda correspondência determinística.

   **B — declaração humana única.**

   Quem declara: **professor responsável pela organização curricular**, ou quem cria a matéria com autoridade curricular delegada. O simples fato de alguém clicar em “criar matéria” não lhe dá esse conhecimento.

   Entregar um pacote com plano, categorias, termos e trechos originais, sem predições nem gabarito. Para cada categoria, registrar tópico ou “sem correspondência”, escopo da declaração, autoria e versão das fontes. Permitir categorias homônimas com escopos diferentes; proibir classificação de arquivos individuais e seleção de categorias pela lista de erros.

   Proponho **uma sessão de até 30 minutos por curso**, sem segunda rodada após feedback. É orçamento experimental proposto. Registrar tempo, categorias examinadas e pendentes; incompletude conta no resultado.

   Para simular sem professor disponível, usar especialista que **não tenha acompanhado estes cursos, briefings ou gold**, em contexto e diretório isolados. Outro avaliador produzirá o gabarito. Alguém que já conhece os erros não recupera cegamento apenas deixando de abrir o CSV. Essa simulação mede declaração por especialista; não comprova adesão ou tempo do professor real.

   **“Uma vez” significa uma vez por versão curricular.** Um resync idêntico reutiliza a declaração; alteração de rótulos ou escopo exige detectar a desatualização. Não prometer configuração eterna.

   **C — LLM opcional.**

   A comparação principal deve ser **LLM como fornecedor do mapa categoria→tópico**, com o mesmo pacote de B. Não ligar voter, resumo de código, descrição de imagem nem enriquecimento adicional. O modelo pode inferir a correspondência semântica, mas só pode escolher tópicos e categorias existentes; não inventar termos.

   Congelar provedor, identificador exato do modelo, prompt, parâmetros, schema e divisão dos lotes antes do reservado. Processar todas as categorias em ordem fixa; usar a primeira resposta, sem escolher a melhor tentativa pelo placar. Resposta inválida vira correspondência ausente. Guardar pedido, resposta, custos, tentativas e relações rejeitadas.

   Gerar esse artefato uma vez; depois rodar o motor offline. **Continua sendo regime LLM**, mesmo que a classificação posterior não faça chamadas. O comparador histórico mais próximo é **VOCAB sem voter**, mas esse novo braço restrito ao elo não é uma reprodução daquele compilador. O PRODUTO completo não isola essa pergunta. [§19:876](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:876).

4. **Validar prospectivamente e separar ganho de cumprimento da meta.**

   Proponho um lote final de **6 cursos de professores ainda não usados, com pelo menos 300 materiais elegíveis**, como orçamento operacional, não como tamanho estatístico mágico. Usar um curso novo para ensaiar o procedimento o transforma em desenvolvimento; ele sai do reservado.

   Dois avaliadores independentes, sem acesso às saídas dos braços, anotam bloco, unidade curricular, primário, alternativas e sustentação. Resolver divergências antes de abrir as predições. **Gold pode avaliar o motor; não pode alimentar a aquisição ou selecionar a configuração vencedora no reservado.** Ausência de gold na entrada e ausência de gold na avaliação são exigências diferentes. [§28:1622](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:1622).

   Em cada braço, executar criação do zero, resync sem mudança e resync com um lote de materiais separado previamente. No resync idêntico, exigir as mesmas atribuições; com materiais novos, comparar o resultado com uma criação limpa usando as mesmas fontes finais e os mesmos artefatos autorizados.

   Medir **relações corretas e incorretas**, termos efetivamente consumidos, ganhos e perdas por material em cada eixo, métricas da meta, tempo humano, tempo computacional, memória e chamadas. Auditar relações sem mostrar seu efeito no placar; não corrigir o mapa depois dessa auditoria na mesma rodada.

   Separar duas leituras: resultado completo usando todas as fontes disponíveis e transferência para documentos que não doaram a relação, agrupando duplicatas/versões. **Autodoação não é automaticamente contaminação por gold:** o próprio documento é uma entrada legítima. O +1 da §39 pode ser um acerto local válido; não demonstra benefício transferível. [Comparação registrada:18](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/compara_bracoR_x_C_14-09.log:18).

   **Critério de parada:** encerrar a versão ao terminar o lote congelado. Vazamento, baseline divergente ou chamada proibida invalidam a corrida. Não prolongar a amostra nem ajustar regra até aparecer aprovação.

   **Critério para a opção sobreviver como mecanismo:** ganho líquido de primário em documentos não doadores, observado em pelo menos dois cursos novos, sem perdas nos demais eixos avaliados. Listar todas as perdas; saldo positivo isolado não apaga regressão.

   **Critério para cumprir a meta:** precisão automática ≥95% e cobertura ≥80% em cada eixo, por curso; publicar também agregados, pior curso e intervalos de incerteza. Resultado pontual insuficiente para sustentar o limite inferior de precisão fica **inconclusivo para promessa**, mesmo passando o placar. Considerar correlação por professor/curso; 300 arquivos não são 300 experiências independentes de generalização.

   Uma opção pode demonstrar aquisição útil e continuar longe da meta. Isso autoriza reconhecer o mecanismo, não anunciar o produto como ≥95%.

5. **O que não fazer.**

   Não rebatizar artefato LLM como cru; não trocar primário por aceito; não retirar os 17 erros de desenho; não elevar confiança por decreto; não usar a declaração como gabarito disfarçado.

   Não exigir que B ou C “provem literalmente” uma equivalência ausente das fontes: a contribuição deles é justamente acrescentar interpretação curricular. Registrar essa origem semântica explicitamente.

   Não transformar as três opções numa competição de sistemas diferentes. Se C receber voter e documentos extras, ou B puder corrigir arquivos após ver erros, o resultado deixa de responder qual mecanismo fecha o elo.

   Não reescrever o motor antes de validar aquisição. O canal experimental de injeção já existe; o driver atual serve para regressão histórica, mas **não certifica criação limpa nem implementa o cegamento descrito aqui**. [Injeção:232](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py:232).

   **Nenhum experimento executado; nenhum arquivo alterado.**
