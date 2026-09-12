# Resposta do astra ao brief v3 — "como aumentar o numero do cru?" (2026-09-12, noite)

Comando: codex exec --profile astra --sandbox read-only --skip-git-repo-check -C <repo> - < brief_codex_astra_cru_como_subir.md
Perfil astra, read-only. 75.748 tokens. Brief: 377 linhas, com os 77 erros confiantes um a um.
Abaixo a RESPOSTA FINAL, verbatim. O transcript de execucao fica fora do repo (ecoa o .mex/AGENTS.md e
dispara o guard de anti-padrao Gemini no staged).

---

**Para aumentar o cru: corrigir a fila que ignora abstenções e recuperar evidência que distingue os tópicos. “Entrega confiável” sozinha também permite melhorar o placar chutando.**

Conferi código e logs; recontei o CSV: **77 erros, 63 corrigidos pelo produto, 14 persistentes, 53 na primeira passada e 24 na segunda**. Não executei o motor. Os contrafactuais da seção 4 são resultados reportados no brief, não reproduzidos nesta revisão. [CSV:1](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/lista_erros_confiantes_cru_12-09.csv:1)

**1. A métrica: manter entrega confiável, mas subordinada a um limite de erro.**

Defina `C = confiantes certos`, `E = confiantes errados`, `Q = fila`. Então:

`entrega = C/251`; `precisão = C/(C+E)`; `cobertura = (C+E)/251`.

A brecha: **retirar os 61 materiais da fila, mantendo suas previsões, aumenta a entrega de 113/251 para 147/251**, mas aumenta os erros confiantes de **77 para 104**. Erro não soma ao numerador, porém também não penaliza. Portanto, entregar tudo maximiza essa métrica para previsões fixas. Cálculo sobre o [log:4](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_cru_12-09.log:4).

Minha escolha: **maximizar entrega sob precisão mínima**, mostrando fila e resultado por curso. Isso preserva a decisão do Gate 1 de priorizar precisão ACEITA.

Alvos distintos:

- **Resultado imediato calculável:** encaminhar os três vazios errados → `C=113`, `E=74`, `Q=64`, precisão **60,4%**, entrega **45,0%**. É projeção aritmética; a correção ainda precisa ser validada.
- **Marco de pesquisa proposto:** precisão **≥80%**, preservando pelo menos **113 entregas certas**; depois buscar **126/251 = 50,2%** de entrega. São critérios propostos, **não desempenho previsto pelos dados**. Com exatamente 126 certas, 80% exige no máximo 31 erros.
- **70,9% do produto:** referência comparativa, não promessa para o cru.

**Os 64% não limitam a entrega confiável.** São alcance do **primário**, em outra base, por fontes e detector específicos. O script consulta o gold e aceita a união das fontes que o alcançam; não demonstra que o motor consegue escolher a fonte correta quando elas discordam. Também não exclui soluções por combinação de sinais ou outro vocabulário. É alcance observado desse instrumento, não teto geral de informação. [Instrumento:131](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fontes_do_professor.py:131)

**2. “Quanto menos erros confiantes, melhor”: vale mantendo a entrega útil ou explicitando seu custo.**

Com `C` preservado, reduzir `E` melhora inequivocamente. Quando ambos caem, existe uma escolha de produto.

Para congelar a troca antes dos próximos experimentos, proponho **um erro confiante custar quatro entregas certas**, usando:

`saldo = ΔC − 4 × ΔE`

Evitar um erro pode compensar perder até quatro entregas certas; igualdade é empate, sem ganho. **Esse peso é uma preferência operacional proposta, não algo estimado pelo gold.** O piso de entrega impede que “abster de tudo” vire candidato aceitável.

Não use a confiança gravada como probabilidade: o código calcula margem relativa. `1,000` significa vantagem relativa máxima nessa disputa, não 100% de chance de acerto. [file_map.py:203](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:203)

**3. IA: principalmente ausência de vocabulário discriminante; amplificação pela taxonomia e pela segunda passada.**

As hipóteses já foram separadas pelos contrafactuais reportados:

**(a) Captura:** não sustentada. O plano não numera; inventar números não recupera informação ausente.

**(b) Tópico aspirador:** contribui, mas removê-lo compra apenas **+2**.

**(c) Vocabulário:** maior explicação disponível, com **+31** ao restituí-lo. Contudo, “ausência total” exagera: o gold tem score zero em **30/34**, não em todos.

**(d) Amplificação:** headings associados pelo próprio motor viram aliases e voltam como evidência. O código confirma essa doação. Uma correspondência exata com um alias assim produzido pode repetir o erro original, sem confirmação independente. [Brief:194](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_cru_como_subir.md:194), [content_taxonomy.py:642](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:642)

**Não repetiria essa separação.** Mediria agora quanto do ganho pode vir de **SARC com vínculos congelados e evidência independente**, sem usar o gold para construir os vínculos. Restituir os termos dos três tópicos conhecidos prova sensibilidade ao vocabulário; ainda não prova aquisição automática nem transferência.

Ressalva de escopo: este “cru” conserva unidade do manifest e lê `code_curation`. A ablação remove aliases por igualdade textual com o sidecar LLM; não reconstrói toda a cadeia sem LLM. Logo, os números descrevem **essa ablação de subunidade**, não um gerador integralmente cru. [Replay:129](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py:129), [Ablação:32](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_cru_12-09.py:32)

**4. Os 14 persistentes: não há evidência para classificá-los como teto. Permanecem no denominador.**

“O produto também erra” demonstra que **o vocabulário atual não basta**. Não distingue extração insuficiente, vínculo errado, scorer, propagação ou gold inadequado.

A adjudicação precisa comparar, por material: conteúdo efetivamente consumido, contexto do professor, destinos aceitos e origem da decisão. Para os dois com gold vazio, verificar se vazio significa **“nenhum tópico aplicável”**, uma resposta válida, ou **“ainda não adjudicado”**.

Só excluir quando houver motivo de inelegibilidade independente do resultado, aplicado igualmente a todos os regimes. Dificuldade do caso não justifica exclusão.

Duplicatas continuam no benchmark congelado; acrescentar resultado por documento distinto. **251 entradas não equivalem automaticamente a 251 evidências independentes.** O próprio brief registra duplicação na seleção das regras. [Brief:240](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_cru_como_subir.md:240)

**5. Segunda passada: não desligar inteira com base nos 24 erros.**

**24 é atribuição pela razão final, não quantidade de erros causados incrementalmente.** A comparação completa reportada compra **+6 confiantes certos e +3 erros confiantes** frente a desligá-la. Com o custo proposto, saldo `6 − 4×3 = −6`: justifica investigar restrição, não identifica qual restrição ganha. [Brief:252](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_cru_como_subir.md:252)

Headings isolados pioram o cru, mas **“só headings” não mede “tudo menos headings”**. Há interações entre regras. A decisão exige esse contrafactual completo, transições pareadas e controle no produto.

Minha hipótese prioritária: **não liberar automaticamente uma abstenção quando a nova evidência deriva apenas das próprias previsões que alimentaram a propagação**. Preservar a previsão candidata permite revisão sem jogá-la fora.

Não basta concatenar razões antigas: isso pode manter dúvida mesmo após uma resolução legítima. Separar histórico da decisão de seu estado final. Hoje o código substitui as razões, mas essa substituição, sozinha, não demonstra que toda resolução seja inválida. [resolver_apply.py:339](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/resolver_apply.py:339)

**6. A ordem muda: reparar a abstenção existente primeiro; recuperar acurácia logo depois.**

1. **Alinhar matcher e fila.** Cobrir abstenções explícitas ainda não resolvidas, preservando “não aplicável” legítimo. O matcher marca `ambiguous=True` em `sem-sinal`; a fila só reconhece duas strings. “Zero regressões observadas nesta base” é defensável; “custo zero, sem risco” não. [Matcher:208](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:208), [Fila:39](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/revisar.py:39)
2. **Medir a liberação de abstenções pela segunda passada**, distinguindo evidência independente de evidência produzida pelo próprio motor.
3. **Executar controle limpo + SARC no IA**, com vínculos congelados, contando entregas certas, erros e fila.
4. **Avaliar aquisição de vocabulário independente do gold**, reservando curso ainda não usado na escolha das regras. Os sete atuais já são desenvolvimento.
5. **Comparar base × advanced nos erros residuais**, somente quando houver diferença relevante no texto efetivamente consumido.

**7. Descartar agora, sem nova rodada.**

Numerar artificialmente IA; desligar toda a segunda passada por contagem bruta; limpar tokens de mídia para melhorar este placar; excluir os 14 difíceis; tratar 64% como teto; repetir pisos globais com outro nome.

Também **não promover `exact_hits == 0` porque ganhou em PRIMÁRIO**: a régua decisória congelada é ACEITO. Custo menor justifica considerá-la como candidata, não trocar a régua depois do resultado. E `exact_hits > 0` não certifica evidência independente, como mostra a doação de headings.

O **67,3%** reportado é o melhor resultado entre as regras de abstenção examinadas, **não teto de toda abstenção possível**. A amostra já usada para escolher cerca de vinte regras tampouco serve como holdout dessas regras. [Brief:235](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_cru_como_subir.md:235)
hook: Stop
hook: Stop Completed
tokens used
75.748
**Para aumentar o cru: corrigir a fila que ignora abstenções e recuperar evidência que distingue os tópicos. “Entrega confiável” sozinha também permite melhorar o placar chutando.**

Conferi código e logs; recontei o CSV: **77 erros, 63 corrigidos pelo produto, 14 persistentes, 53 na primeira passada e 24 na segunda**. Não executei o motor. Os contrafactuais da seção 4 são resultados reportados no brief, não reproduzidos nesta revisão. [CSV:1](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/lista_erros_confiantes_cru_12-09.csv:1)

**1. A métrica: manter entrega confiável, mas subordinada a um limite de erro.**

Defina `C = confiantes certos`, `E = confiantes errados`, `Q = fila`. Então:

`entrega = C/251`; `precisão = C/(C+E)`; `cobertura = (C+E)/251`.

A brecha: **retirar os 61 materiais da fila, mantendo suas previsões, aumenta a entrega de 113/251 para 147/251**, mas aumenta os erros confiantes de **77 para 104**. Erro não soma ao numerador, porém também não penaliza. Portanto, entregar tudo maximiza essa métrica para previsões fixas. Cálculo sobre o [log:4](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_cru_12-09.log:4).

Minha escolha: **maximizar entrega sob precisão mínima**, mostrando fila e resultado por curso. Isso preserva a decisão do Gate 1 de priorizar precisão ACEITA.

Alvos distintos:

- **Resultado imediato calculável:** encaminhar os três vazios errados → `C=113`, `E=74`, `Q=64`, precisão **60,4%**, entrega **45,0%**. É projeção aritmética; a correção ainda precisa ser validada.
- **Marco de pesquisa proposto:** precisão **≥80%**, preservando pelo menos **113 entregas certas**; depois buscar **126/251 = 50,2%** de entrega. São critérios propostos, **não desempenho previsto pelos dados**. Com exatamente 126 certas, 80% exige no máximo 31 erros.
- **70,9% do produto:** referência comparativa, não promessa para o cru.

**Os 64% não limitam a entrega confiável.** São alcance do **primário**, em outra base, por fontes e detector específicos. O script consulta o gold e aceita a união das fontes que o alcançam; não demonstra que o motor consegue escolher a fonte correta quando elas discordam. Também não exclui soluções por combinação de sinais ou outro vocabulário. É alcance observado desse instrumento, não teto geral de informação. [Instrumento:131](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fontes_do_professor.py:131)

**2. “Quanto menos erros confiantes, melhor”: vale mantendo a entrega útil ou explicitando seu custo.**

Com `C` preservado, reduzir `E` melhora inequivocamente. Quando ambos caem, existe uma escolha de produto.

Para congelar a troca antes dos próximos experimentos, proponho **um erro confiante custar quatro entregas certas**, usando:

`saldo = ΔC − 4 × ΔE`

Evitar um erro pode compensar perder até quatro entregas certas; igualdade é empate, sem ganho. **Esse peso é uma preferência operacional proposta, não algo estimado pelo gold.** O piso de entrega impede que “abster de tudo” vire candidato aceitável.

Não use a confiança gravada como probabilidade: o código calcula margem relativa. `1,000` significa vantagem relativa máxima nessa disputa, não 100% de chance de acerto. [file_map.py:203](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:203)

**3. IA: principalmente ausência de vocabulário discriminante; amplificação pela taxonomia e pela segunda passada.**

As hipóteses já foram separadas pelos contrafactuais reportados:

**(a) Captura:** não sustentada. O plano não numera; inventar números não recupera informação ausente.

**(b) Tópico aspirador:** contribui, mas removê-lo compra apenas **+2**.

**(c) Vocabulário:** maior explicação disponível, com **+31** ao restituí-lo. Contudo, “ausência total” exagera: o gold tem score zero em **30/34**, não em todos.

**(d) Amplificação:** headings associados pelo próprio motor viram aliases e voltam como evidência. O código confirma essa doação. Uma correspondência exata com um alias assim produzido pode repetir o erro original, sem confirmação independente. [Brief:194](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_cru_como_subir.md:194), [content_taxonomy.py:642](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:642)

**Não repetiria essa separação.** Mediria agora quanto do ganho pode vir de **SARC com vínculos congelados e evidência independente**, sem usar o gold para construir os vínculos. Restituir os termos dos três tópicos conhecidos prova sensibilidade ao vocabulário; ainda não prova aquisição automática nem transferência.

Ressalva de escopo: este “cru” conserva unidade do manifest e lê `code_curation`. A ablação remove aliases por igualdade textual com o sidecar LLM; não reconstrói toda a cadeia sem LLM. Logo, os números descrevem **essa ablação de subunidade**, não um gerador integralmente cru. [Replay:129](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py:129), [Ablação:32](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_cru_12-09.py:32)

**4. Os 14 persistentes: não há evidência para classificá-los como teto. Permanecem no denominador.**

“O produto também erra” demonstra que **o vocabulário atual não basta**. Não distingue extração insuficiente, vínculo errado, scorer, propagação ou gold inadequado.

A adjudicação precisa comparar, por material: conteúdo efetivamente consumido, contexto do professor, destinos aceitos e origem da decisão. Para os dois com gold vazio, verificar se vazio significa **“nenhum tópico aplicável”**, uma resposta válida, ou **“ainda não adjudicado”**.

Só excluir quando houver motivo de inelegibilidade independente do resultado, aplicado igualmente a todos os regimes. Dificuldade do caso não justifica exclusão.

Duplicatas continuam no benchmark congelado; acrescentar resultado por documento distinto. **251 entradas não equivalem automaticamente a 251 evidências independentes.** O próprio brief registra duplicação na seleção das regras. [Brief:240](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_cru_como_subir.md:240)

**5. Segunda passada: não desligar inteira com base nos 24 erros.**

**24 é atribuição pela razão final, não quantidade de erros causados incrementalmente.** A comparação completa reportada compra **+6 confiantes certos e +3 erros confiantes** frente a desligá-la. Com o custo proposto, saldo `6 − 4×3 = −6`: justifica investigar restrição, não identifica qual restrição ganha. [Brief:252](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_cru_como_subir.md:252)

Headings isolados pioram o cru, mas **“só headings” não mede “tudo menos headings”**. Há interações entre regras. A decisão exige esse contrafactual completo, transições pareadas e controle no produto.

Minha hipótese prioritária: **não liberar automaticamente uma abstenção quando a nova evidência deriva apenas das próprias previsões que alimentaram a propagação**. Preservar a previsão candidata permite revisão sem jogá-la fora.

Não basta concatenar razões antigas: isso pode manter dúvida mesmo após uma resolução legítima. Separar histórico da decisão de seu estado final. Hoje o código substitui as razões, mas essa substituição, sozinha, não demonstra que toda resolução seja inválida. [resolver_apply.py:339](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/resolver_apply.py:339)

**6. A ordem muda: reparar a abstenção existente primeiro; recuperar acurácia logo depois.**

1. **Alinhar matcher e fila.** Cobrir abstenções explícitas ainda não resolvidas, preservando “não aplicável” legítimo. O matcher marca `ambiguous=True` em `sem-sinal`; a fila só reconhece duas strings. “Zero regressões observadas nesta base” é defensável; “custo zero, sem risco” não. [Matcher:208](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:208), [Fila:39](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/revisar.py:39)
2. **Medir a liberação de abstenções pela segunda passada**, distinguindo evidência independente de evidência produzida pelo próprio motor.
3. **Executar controle limpo + SARC no IA**, com vínculos congelados, contando entregas certas, erros e fila.
4. **Avaliar aquisição de vocabulário independente do gold**, reservando curso ainda não usado na escolha das regras. Os sete atuais já são desenvolvimento.
5. **Comparar base × advanced nos erros residuais**, somente quando houver diferença relevante no texto efetivamente consumido.

**7. Descartar agora, sem nova rodada.**

Numerar artificialmente IA; desligar toda a segunda passada por contagem bruta; limpar tokens de mídia para melhorar este placar; excluir os 14 difíceis; tratar 64% como teto; repetir pisos globais com outro nome.

Também **não promover `exact_hits == 0` porque ganhou em PRIMÁRIO**: a régua decisória congelada é ACEITO. Custo menor justifica considerá-la como candidata, não trocar a régua depois do resultado. E `exact_hits > 0` não certifica evidência independente, como mostra a doação de headings.

O **67,3%** reportado é o melhor resultado entre as regras de abstenção examinadas, **não teto de toda abstenção possível**. A amostra já usada para escolher cerca de vinte regras tampouco serve como holdout dessas regras. [Brief:235](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_cru_como_subir.md:235)
