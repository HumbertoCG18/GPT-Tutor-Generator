**84/251 é o placar observado; 35,5% não é fim de linha demonstrado, e 52–59% não é teto geral.** Há uma falha concreta na construção de H3. Não encontrei evidência suficiente para prometer ganho líquido ≥20.

Referências `replay_*`, `diagnostico_*` e `astra_*` abaixo pertencem a `docs/reports/_harness-2026-09-04/c1-3/`.

1. **FATO — denominador preservado; validade de H3 é mais estreita que a conclusão publicada.**

   Conferi HEAD `ce02a8f`, 251 registros, 84 acertos, 8 ausentes; todos os IDs e primários do diagnóstico correspondem aos golds permitidos. Não encontrei duplicatas de ID ou `source_path` nos manifests. Os ausentes entram antes do `continue`: não desaparecem do denominador (`replay_subunidade_21-09.py:159–174`).

   **Defeito concreto:** `score_h3` constrói `pseudo` uma vez e depois consulta apenas unidade/slug (`:78–92`). A segunda passada acrescenta aliases numa cópia da taxonomia (`resolver_apply.py:308–331`), mas H3 ignora esses aliases novos. Portanto, **88 mede essa implementação congelada**, não uma substituição fiel que preserve o aprendizado da segunda passada. Das 14 perdas, **11** tinham reasons `propagado-headings` ou `rotulo-decomposto`.

   Outra diferença: os 217 tópicos possuem label/alias equivalentes após retirar numeração; H3 os entrega ao índice, que acumula `topic_phrases` sem deduplicar (`file_map.py:99–109`). Isso altera pesos. Mantém também o piso absoluto de revisão e os limiares de confiança da rota anterior (`:232–246`): escala equivalente não demonstrada.

   **Não certifiquei ausência de vazamento:** o replay conserva tags; `entry_signals.py:112` chama `_sem_eco`, cuja definição está fora do intervalo autorizado. Fidelidade ao gravado, sozinha, não exclui circularidade. A cadeia original de mapeamento usa arquivos `herancas_*` não autorizados.

2. **FATO — “95 sem rótulo” não significa “95 sem informação”.**

   A premissa dos tokens curtos está desatualizada: siglas já entram (`diagnostico_subunidade_17-09.py:53–73`); nome de arquivo e resumo de código também (`:103–109`). Nos 95, contei **68 com markdown e 27 com resumo de código**.

   Cruzamento determinístico CSV → manifest/taxonomia, contando linhas, sem somar fontes sobrepostas:

   - **Token exato adicional:** nome de arquivo **0**; token curto não contabilizado, nos metadados examinados, **0**; seção **18**, dos quais **4** com token exclusivo na unidade; notes/image_description **0**.
   - **Prefixo comum de seis caracteres, tokens diferentes:** título **4**, Moodle label **8**, caminho raw **4**, seção **21**; união **28**. São candidatos morfológicos, não correções; incluem `socket/sockets` e `supervisionado/supervisionados`. Não reabrem a hipótese de radicais já refutada.
   - **Vizinhos confiantes:** excluindo a própria entrada, confiança ≥0,7 e sem `ambiguous`, há algum vizinho na seção em **93** casos; o conjunto contém o gold em **21**. Porém, entre **46** com previsão unânime, **0** acertam. Por bloco: **89/12/11/0**, respectivamente.
   - Código bruto: parecer anterior encontrou **2** sinais adicionais, já cobertos pela seção (`astra_revisao_regime2_17-09.md:30`); não reinspecionei os arquivos.

   **Cinco dos 95 têm gold vazio**, não rótulo lexical faltante — exemplo `diagnostico_subunidade_17-09.csv:184`.

3. **FATO — existe componente de régua; sua dimensão não autoriza trocar a métrica.**

   Nos 167 não-acertos, contei **13 pai×filho**, usando mesma unidade e prefixo hierárquico do código curricular; **5** também são aceitos-não-primários. Há **82 previsões entre irmãos**, das quais **16** aceitas-não-primárias. Total aceito-não-primário: **24**.

   **Não quantifiquei “quase sinônimos” semanticamente**: parentesco ou aceitação alternativa não prova sinonímia.

   IA concentra **34 erros com gold abstrato**: **26 preditivos + 8 descritivos**, sendo **31 ausentes + 3 genéricos** lexicalmente. Isso mede necessidade de ligar algoritmo à categoria, não necessariamente erro da régua (`subunit_gt_IA.csv:14,39`).

   Assim, **131=84+47 e 148=131+17** são somas condicionadas ao diagnóstico, não limites de todo método sem LLM. O próprio registro anterior já rejeitava essa inferência (`astra_revisao_regime2_17-09.md:22`).

4. **HIPÓTESES ranqueadas — nenhuma tem ganho esperado ≥20 sustentado.**

   **H1: aquisição explícita de relações categoria→algoritmo no material.** Maior população identificada: **34 erros IA**. A cadeia completa permanece não demonstrada (`astra_revisao_regime2_17-09.md:34`). **34 é oportunidade, não ganho esperado.** Risco: associações transitivas erradas. Medição: extrair vínculos sem gold, exigir proveniência textual e avaliar ganhos/perdas nos 251.

   **H2: H3 respeitando aliases da segunda passada.** População diretamente suspeita: **11 perdas**. Recuperá-las mantendo os demais resultados daria **99/251**, cenário condicional. Risco: aliases e duplicação também alterarem os 18 ganhos. Medição: comparação pareada, alterando somente atualização/deduplicação das pseudo-unidades.

   Mesmo um seletor-oráculo entre H2/H3/H3b existentes recupera apenas **19 erros distintos**: nenhuma combinação desses resultados sustenta +20.

5. **FATO — critérios estruturais ajudam parcialmente; separador validado, não.**

   Nas 83 linhas de `detalhe`, selecionar H3 quando ambos os rótulos existem e o novo é mais longo dá **+10/−2**; vocabulário maior dá **+10/−2**. O critério já existente de três palavras com ≥5 caracteres dá **+14/−9**. Preservar decisões marcadas como propagação/decomposição dá **+13/−3**. Nenhum separa perfeitamente os cursos.

   São seleções retrospectivas **in-sample**, não validação independente.

**Limitações:** nenhuma escrita, rede, LLM, rebuild ou reprocess. Não executei o replay completo: suas dependências e textos ultrapassam a lista autorizada. Permanecem sem verificação integral eco de tags, linhagem do mapeamento e sinais morfológicos no corpo dos materiais.