# Resposta do astra ao brief v5 — revisar a medicao dos 3 eixos com o motor completo (2026-09-12, noite)

Perfil astra, read-only. 114.674 tokens. Brief: 151 linhas.
Veredito: as contagens conferem; o ISOLAMENTO do experimento nao. Abaixo a resposta final, verbatim.

---

**As contagens conferem; a conclusão “resta só um eixo” não. O isolamento do vocabulário está incompleto.**

Reexecutei o medidor sobre RÉGUA e PRODUTO: resultados reproduzidos. NU e VOCAB conferidos nos logs, pois suas cópias foram sobrescritas. Não executei o reprocess completo nem alterei arquivos.

1. **A medição se sustenta como retrato das cópias, com três problemas de metodologia.**

   **Cache preserva efeitos do vocabulário removido.** `code_curation.json` contém resumos `determ-v3`, não resumos Gemini, nos sete cursos. Porém, o produtor determinístico usa aliases da taxonomia e do sidecar LLM; o cache considera somente o hash do texto. Retirar aliases não invalida o resumo. [Entrada dos aliases](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:565), [hash](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:134), [reutilização do cache](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:634).

   **MEDIDO:** os 42 registros de código da RÉGUA são idênticos aos do produto. Recalculando apenas seus resumos em memória com os aliases atuais, **32/42 mudam**: MF 4, IA 4, ES2 8, CG 12, FR 4. Desaparecem conceitos como `NuSMV`, `Elitismo`, `HTTP` e `Socket`, presentes no sidecar retirado. Em IA, restaurar os aliases do produto reproduz os quatro resumos salvos. Há dependência residual concreta; **o impacto nos três eixos ainda não foi medido**.

   **O veto também não equivale ao replay.** O reprocess reconstrói e sobrescreve a taxonomia depois da edição do driver. Reproduzi essa reconstrução em memória: mesmos aliases da cópia salva. Nela, **30 ocorrências** coincidem com termos vetados: MF 14, SO 4, IA 4, ES2 5, TCC 3. Podem vir legitimamente do plano, headings ou curadoria humana; coincidência não prova origem LLM. O replay elimina por texto independentemente da origem, portanto aplica outra intervenção. [Regeneração](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ops/pedagogical_regeneration.py:453), [replay](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_cru_12-09.py:32).

   **“Terminou sem exceção → zero chamadas” não é prova.** Reproduzi uma tentativa bloqueada que a camada de vocabulário captura e deixa a execução continuar. O texto “0 chamadas” do driver é fixo, sem contador. Além disso, `use_llm_voter=False` não desliga compilação, resíduo ou enriquecimento de referências. Este último pode rodar no incremental conforme a configuração. [Captura da exceção](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ops/pedagogical_regeneration.py:104), [referências](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ops/build_workflow.py:147), [mensagem fixa](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py:135).

   A acurácia total está calculada corretamente para os registros presentes: fila não remove material nem concede acerto automático. Conferi **zero IDs duplicados e zero golds avaliáveis ausentes** nas cópias atuais. Entretanto, o medidor percorre o manifest: uma futura entrada desaparecida seria omitida silenciosamente. [Contagem](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_3eixos_12-09.py:72).

2. **“Bloco passou de 90% nesta base” confere; “bloco resolvido” excede a evidência.**

   RÉGUA: **222/237 = 93,7%**. Retirando os seis materiais com pino manual: **216/231 = 93,5%**. Portanto, os pinos não explicam o resultado. A fila tampouco o infla: seus materiais continuam avaliados. E “cobertura” aqui significa ausência da fila conjunta, que também dispara por dúvida de subunidade ou conflito. [Regras da fila](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/revisar.py:53).

   A seleção da base merece atenção: CG tem **93 entradas, mas apenas 35 avaliadas em bloco**. Seu CSV contém 48 linhas; 13 foram excluídas por “seção sem bloco casado”. Isso exclui casos difíceis de rotular, sem demonstrar como o motor se sairia neles. FR não participa desse eixo. [Gold CG](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/ground_truth_CG.csv:4).

   Outro problema verificável: **os UUIDs dos 35 golds de bloco do CG não existem no índice atual**. O medidor aceita o ID posicional. Exemplo: `intro` aponta para UUID `26afa1ef…`, mas o `bloco-01` atual tem `7eda873a…`. Isso não prova classificação errada; exige validar a correspondência antes de tratar esses acertos como identidade temporal confirmada. [Gold](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/ground_truth_CG.csv:2), [índice](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/.motor3eixos/Computacao-Grafica-Tutor/course/.timeline_index.json:130).

   Finalmente, MF fica em **89,4%**. A meta agregada passa; uma meta por curso, não.

3. **“Faltam três” é aritmética correta; “só existem dez alavancas” é inferência errada.**

   `ceil(0,90 × 284) = 256`; hoje são 253. Faltam **três acertos líquidos**, contando regressões. Reproduzi: **31 erros, 28 na fila, dez corrigidos no produto, 21 errados nos dois**. [Resultado RÉGUA](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_regua_12-09.log:34).

   O produto também errar não estabelece teto do dado. Ambos podem compartilhar uma falha determinística. Os dez desacordos ajudam no diagnóstico; não delimitam o conjunto de melhorias possíveis sem API.

   Critério honesto: identificar mecanismo geral, congelar a correção e medir ganhos **e perdas** em toda a base. Escolher três IDs para cruzar 90% seria ajuste ao benchmark. Os sete cursos já examinados servem para desenvolvimento/regressão; comprovação externa exige cursos ainda não usados nas decisões. SO em **27/37 = 73,0%** impede chamar unidade de resolvida.

4. **Priorizar subunidade faz sentido; concluir que só ela precisa de LLM, não.**

   O grande ganho observado acompanha o vocabulário: **75/251 = 29,9 pontos**, não 29,8. Isso identifica a principal contribuição desta intervenção; não prova necessidade exclusiva de LLM nem impossibilidade de outra fonte lexical.

   Também não atribuiria automaticamente VOCAB → PRODUTO ao voter: a quarta coluna é um produto salvo, sem braço contemporâneo reprocessado sob condições iguais. O delta observado é válido; a atribuição causal ainda precisa desse controle.

   “Compilar vocabulário e reprocessar localmente com voter desligado” já corresponde aproximadamente ao braço VOCAB. Seus resultados ainda ficam abaixo da meta em unidade e subunidade: **255/284 e 220/251**. Além disso, aliases alimentam taxonomia, resumos e decisões anteriores: restringir seu efeito à subunidade seria uma configuração nova, ainda não medida.

   **Custo por curso: desconhecido.** O compilador faz uma chamada lógica por unidade elegível, reutiliza sidecar e pode envolver retries internos. Faltam tokens, tentativas e trabalho humano observados para calcular custo. [Compilador](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:221).

5. **Descartar agora as conclusões fortes, preservando os resultados observados.**

   Retirar: “resta um eixo”, “os dez são a única alavanca”, “zero chamadas comprovadas” e “ganho do voter isolado”. Corrigir também: cobertura de unidade no produto = **76,1%**; deltas de bloco = **+0,4 / −0,4 / +5,9 pontos**; aliases inicialmente vetados = **51–98 por curso**.

   **Próximo passo: corrigir o experimento antes do motor.** Separar snapshots por configuração; definir se a ablação remove a fonte LLM ou qualquer termo coincidente; regenerar caches dependentes dessa fonte; contar tentativas de API; incluir o quarto braço equivalente com voter ligado. Só então decidir se unidade pode sair da frente principal.
hook: Stop
hook: Stop Completed
2026-09-13T00:47:38.639370Z ERROR codex_core::session: failed to record rollout items: thread 01a09833-252d-7230-a2d0-3b9fd3e76b0b not found
tokens used
114.674
**As contagens conferem; a conclusão “resta só um eixo” não. O isolamento do vocabulário está incompleto.**

Reexecutei o medidor sobre RÉGUA e PRODUTO: resultados reproduzidos. NU e VOCAB conferidos nos logs, pois suas cópias foram sobrescritas. Não executei o reprocess completo nem alterei arquivos.

1. **A medição se sustenta como retrato das cópias, com três problemas de metodologia.**

   **Cache preserva efeitos do vocabulário removido.** `code_curation.json` contém resumos `determ-v3`, não resumos Gemini, nos sete cursos. Porém, o produtor determinístico usa aliases da taxonomia e do sidecar LLM; o cache considera somente o hash do texto. Retirar aliases não invalida o resumo. [Entrada dos aliases](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:565), [hash](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:134), [reutilização do cache](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:634).

   **MEDIDO:** os 42 registros de código da RÉGUA são idênticos aos do produto. Recalculando apenas seus resumos em memória com os aliases atuais, **32/42 mudam**: MF 4, IA 4, ES2 8, CG 12, FR 4. Desaparecem conceitos como `NuSMV`, `Elitismo`, `HTTP` e `Socket`, presentes no sidecar retirado. Em IA, restaurar os aliases do produto reproduz os quatro resumos salvos. Há dependência residual concreta; **o impacto nos três eixos ainda não foi medido**.

   **O veto também não equivale ao replay.** O reprocess reconstrói e sobrescreve a taxonomia depois da edição do driver. Reproduzi essa reconstrução em memória: mesmos aliases da cópia salva. Nela, **30 ocorrências** coincidem com termos vetados: MF 14, SO 4, IA 4, ES2 5, TCC 3. Podem vir legitimamente do plano, headings ou curadoria humana; coincidência não prova origem LLM. O replay elimina por texto independentemente da origem, portanto aplica outra intervenção. [Regeneração](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ops/pedagogical_regeneration.py:453), [replay](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_cru_12-09.py:32).

   **“Terminou sem exceção → zero chamadas” não é prova.** Reproduzi uma tentativa bloqueada que a camada de vocabulário captura e deixa a execução continuar. O texto “0 chamadas” do driver é fixo, sem contador. Além disso, `use_llm_voter=False` não desliga compilação, resíduo ou enriquecimento de referências. Este último pode rodar no incremental conforme a configuração. [Captura da exceção](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ops/pedagogical_regeneration.py:104), [referências](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ops/build_workflow.py:147), [mensagem fixa](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py:135).

   A acurácia total está calculada corretamente para os registros presentes: fila não remove material nem concede acerto automático. Conferi **zero IDs duplicados e zero golds avaliáveis ausentes** nas cópias atuais. Entretanto, o medidor percorre o manifest: uma futura entrada desaparecida seria omitida silenciosamente. [Contagem](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_3eixos_12-09.py:72).

2. **“Bloco passou de 90% nesta base” confere; “bloco resolvido” excede a evidência.**

   RÉGUA: **222/237 = 93,7%**. Retirando os seis materiais com pino manual: **216/231 = 93,5%**. Portanto, os pinos não explicam o resultado. A fila tampouco o infla: seus materiais continuam avaliados. E “cobertura” aqui significa ausência da fila conjunta, que também dispara por dúvida de subunidade ou conflito. [Regras da fila](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/revisar.py:53).

   A seleção da base merece atenção: CG tem **93 entradas, mas apenas 35 avaliadas em bloco**. Seu CSV contém 48 linhas; 13 foram excluídas por “seção sem bloco casado”. Isso exclui casos difíceis de rotular, sem demonstrar como o motor se sairia neles. FR não participa desse eixo. [Gold CG](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/ground_truth_CG.csv:4).

   Outro problema verificável: **os UUIDs dos 35 golds de bloco do CG não existem no índice atual**. O medidor aceita o ID posicional. Exemplo: `intro` aponta para UUID `26afa1ef…`, mas o `bloco-01` atual tem `7eda873a…`. Isso não prova classificação errada; exige validar a correspondência antes de tratar esses acertos como identidade temporal confirmada. [Gold](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/ground_truth_CG.csv:2), [índice](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/.motor3eixos/Computacao-Grafica-Tutor/course/.timeline_index.json:130).

   Finalmente, MF fica em **89,4%**. A meta agregada passa; uma meta por curso, não.

3. **“Faltam três” é aritmética correta; “só existem dez alavancas” é inferência errada.**

   `ceil(0,90 × 284) = 256`; hoje são 253. Faltam **três acertos líquidos**, contando regressões. Reproduzi: **31 erros, 28 na fila, dez corrigidos no produto, 21 errados nos dois**. [Resultado RÉGUA](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_regua_12-09.log:34).

   O produto também errar não estabelece teto do dado. Ambos podem compartilhar uma falha determinística. Os dez desacordos ajudam no diagnóstico; não delimitam o conjunto de melhorias possíveis sem API.

   Critério honesto: identificar mecanismo geral, congelar a correção e medir ganhos **e perdas** em toda a base. Escolher três IDs para cruzar 90% seria ajuste ao benchmark. Os sete cursos já examinados servem para desenvolvimento/regressão; comprovação externa exige cursos ainda não usados nas decisões. SO em **27/37 = 73,0%** impede chamar unidade de resolvida.

4. **Priorizar subunidade faz sentido; concluir que só ela precisa de LLM, não.**

   O grande ganho observado acompanha o vocabulário: **75/251 = 29,9 pontos**, não 29,8. Isso identifica a principal contribuição desta intervenção; não prova necessidade exclusiva de LLM nem impossibilidade de outra fonte lexical.

   Também não atribuiria automaticamente VOCAB → PRODUTO ao voter: a quarta coluna é um produto salvo, sem braço contemporâneo reprocessado sob condições iguais. O delta observado é válido; a atribuição causal ainda precisa desse controle.

   “Compilar vocabulário e reprocessar localmente com voter desligado” já corresponde aproximadamente ao braço VOCAB. Seus resultados ainda ficam abaixo da meta em unidade e subunidade: **255/284 e 220/251**. Além disso, aliases alimentam taxonomia, resumos e decisões anteriores: restringir seu efeito à subunidade seria uma configuração nova, ainda não medida.

   **Custo por curso: desconhecido.** O compilador faz uma chamada lógica por unidade elegível, reutiliza sidecar e pode envolver retries internos. Faltam tokens, tentativas e trabalho humano observados para calcular custo. [Compilador](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:221).

5. **Descartar agora as conclusões fortes, preservando os resultados observados.**

   Retirar: “resta um eixo”, “os dez são a única alavanca”, “zero chamadas comprovadas” e “ganho do voter isolado”. Corrigir também: cobertura de unidade no produto = **76,1%**; deltas de bloco = **+0,4 / −0,4 / +5,9 pontos**; aliases inicialmente vetados = **51–98 por curso**.

   **Próximo passo: corrigir o experimento antes do motor.** Separar snapshots por configuração; definir se a ablação remove a fonte LLM ou qualquer termo coincidente; regenerar caches dependentes dessa fonte; contar tentativas de API; incluir o quarto braço equivalente com voter ligado. Só então decidir se unidade pode sair da frente principal.
