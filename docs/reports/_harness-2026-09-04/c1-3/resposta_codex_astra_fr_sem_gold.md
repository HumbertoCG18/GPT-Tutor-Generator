**A leitura sustenta ganhos locais; não sustenta “unidade não depende de nada” nem “vocab piora a acurácia de bloco”.** MEDIDO abaixo = resultados fornecidos ou inspeção do avaliador; não reexecutei runs.

1. **Contribuições: separar efeito observado de generalização.**

   | Componente | MEDIDO no FR | Limite da conclusão |
   |---|---|---|
   | Extração | 7→8/18 sem vocab; 18→18 com vocab | +1 acerto líquido nesse contraste; não benefício geral do Datalab |
   | Vocab | +11 com pymupdf4llm; +10 com Datalab; erros confiantes 5→0 | Ganho condicionado ao curso, ao vocabulário e à régua |
   | Voter vivo | Fila 10→1; concordância de bloco 10→19; subunidade 18→18 | Reduz abstensão; não acrescenta acertos de subunidade nessa amostra |
   | Unidade | 19/19 em todas as variantes | Insensibilidade às intervenções testadas, com seção explícita disponível |

   **Evidência:** brief §2, respectivas linhas. **HIPÓTESE:** efeitos não são aditivos nem transportáveis aos outros cursos; faltam, entre outros, voter sem vocab e pymupdf4llm + vocab + voter vivo.

2. **Unidade: medida de reprodução da seção, circular como validação semântica.** **MEDIDO:** a régua extrai `U<n>` de `source_section`; o motor recebe essa mesma informação (brief §4, contexto de 06/09; [avaliador:42](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fr_sem_gold.py:42)). Isso verifica preservação do sinal explícito. Produto concordante não acrescenta independência; bloco sem gold tampouco. **HIPÓTESE:** conteúdo adjudicado contra o plano, sem consultar previsões, permitiria validação independente. CG/SO sem `U<n>` continuam desconhecidos; FR com seção mascarada mede dependência desse sinal, mas não substitui avaliá-los.

3. **Bloco: regressão de concordância, ainda sem prova de defeito.** **MEDIDO:** 15→10 acordos com produto após vocab; inexistência de gold FR (brief §§2, 4b). **HIPÓTESE:** aliases podem melhorar ou prejudicar a atribuição temporal. “O voter existe” não justifica eventual regressão: o caminho sem voter foi solicitado e executado. Medição proposta, zero chamadas: mesmos snapshots dos oito tutores, vocab desligado/ligado, voter desligado e votos removidos em ambos; pontuar contra gold disponível nos cinco + CG. Reportar transições certo→errado, errado→certo, erros confiantes e fila por tutor. Comparar blocos por identidade semântica, não UUID.

4. **Texto: não inverter prioridade com evidência apenas de PDFs FR.** **MEDIDO:** promover Datalab a `base_markdown` produz +1 sem vocab e zero com vocab; o produto guarda advanced sem pontuá-lo nesse caminho (brief §§2, 4a). **HIPÓTESE:** isso revela uma decisão de seleção a validar; não demonstra que advanced seja sempre superior. Nos oito tutores, comparar base versus advanced disponível, mantendo approved/curated prioritários, vocab fixo e voter desligado. Usar os mesmos materiais e gold; separar PDF, HTML e vídeo, cobertura de advanced e transições de erro. Os 163 disponíveis são amostra selecionada; FR não explica sozinho os 62%/57% da C5.

5. **Cache: preservar validade contextual; não trocar por conteúdo apenas.** **MEDIDO:** a janela invalida votos apesar de coincidência do conteúdo (brief §4c). **HIPÓTESE:** correto quando os candidatos mudam; perda evitável de reaproveitamento quando apenas UUIDs mudam. Migrar exigiria equivalência dos candidatos e do contexto relevante, com remapeamento validado. Evidência atual não basta para mudar a chave.

6. **Riscos concretos das tabelas.** **MEDIDO:**

   | Achado | Evidência | Consequência |
   |---|---|---|
   | `18/18` aceita qualquer alternativa gold; coluna impressa é ordenada e truncada | [avaliador:33](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fr_sem_gold.py:33), linha 53; [gold:6](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/subunit_gt_FR.csv:6), linhas 7 e 12 | Resolve as aparentes contradições; não significa 18 acertos do rótulo primário |
   | Cache: fila 11; só vocab: fila 10 | Brief §2 | “Todos miss → resultado igual” não está demonstrado |
   | “Motor puro, 0 chamadas” é rótulo fixo | [avaliador:62](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fr_sem_gold.py:62) | Legenda da run viva é falsa |
   | Produto é pontuado no conjunto do sandbox; status ausente vira `ok` | Avaliador:38–51 | Separar 20/22, denominadores por eixo e status faltantes |

   **HIPÓTESE:** gold desenvolvido junto ao produto pode favorecer suas escolhas; não prova vazamento (§5.6). Perfil forçado precisa equivaler ao da UI; reprocessamento precisa controlar estado residual (§§1, 4d). Dez chamadas, onze votos e treze votos armazenados não são unidades comparáveis. “Zero chamadas” mede execução atual, não custo histórico de Datalab/vocab (§1).
