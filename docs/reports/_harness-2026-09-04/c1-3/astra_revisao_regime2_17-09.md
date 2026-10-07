# Revisão Astra: "a declaração do professor é necessária SEMPRE no caminho sem LLM" (17/09, read-only)

session id: 01a0b0be-fa38-70d1-8f47-2f54f430ce3c | codex exec --profile astra --sandbox read-only | 16:01:40→16:12:36 | rc=0 | árvore inalterada pela chamada. Pedido explícito do usuário ("Coloque o astra para revisar isso, não sei se a tua afirmação de fazermos isso sempre se sustenta").

Brief: scratchpad/brief-astra-regime2.md (não versionado): afirmação literal, evidência de 17/09, decisões do usuário, 5 hipóteses contrárias.

VEREDITO: NÃO SUSTENTA. Consumo pelo Fable, verificado na fonte antes de aceitar:

- A (afirmação): aceito. "83% sem palavra do tópico" misturava "sem token exclusivo no curso" com "sem palavra"; e a exclusividade era calculada no curso inteiro, embora a unidade esteja certa em 148/159. Harness corrigido (siglas do rótulo contam, como `index.py:1849` short_vocab; exclusividade também por unidade) e rerodado: rótulo ausente 95 (60%) · genérico só 17 (11%) por unidade · presente 47 (30%) por unidade (28 no curso). Gold sem token exclusivo: 40 no curso → 8 na unidade. Siglas mudaram 2 linhas. Retirados: "teto ≈ 40%", "nenhuma fonte fornece", "sempre".
- H1: aceito como medição da Astra (não reproduzi SARC): seção exclusiva 10/159, SARC 20/159, união sobre os 132 ausentes/genéricos = 9, com projeção lexical de 25 corretos/100 decisões (perde 15 acertos). Pequeno e arriscado; não reabre alavancas fechadas.
- H2: aceito e medido (acima). `definition`/`not_confuse` não entram nos aliases (`content_taxonomy.py:459`, lido). Ganho de consumir melhor a evidência presente: não medido.
- H3: aceito: necessidade varia por curso (TCC 7/11 com 3 "presente"; IA 4/39 com 31 "ausente"); sem preditor validado.
- H4: verificado: `vocabulary_compile.py:227` não compila se o manual existe, sem olhar conteúdo; `repo.py:1732` funde manual + `.llm.json` preexistente. Presença do manual não certifica regime sem LLM; medição limpa exige remover `.llm.json` na cópia.
- H5: verificado: filtro de nome de seção só no compilado (`repo.py:1749`); chave sem código vira chave morta sem aviso (`repo.py:1747`); resync regenera taxonomia (`incremental_build.py:109`). Custo 3–10 termos × 59 tópicos (CG) não medido. "Uma vez por curso" não cobre mudança de plano.

---

1. **[NÃO SUSTENTA] A — O diagnóstico não estabelece teto nem necessidade universal.**  
   **Medido:** recontagem das 251 linhas: **84 acertos, 159 erros com fonte e 8 ausentes**. Dos 159, **95 não têm token do gold; 37 têm token compartilhado; 27 têm token exclusivo**. Portanto, `132/159 = 83,0%` significa **“sem token exclusivo segundo esse diagnóstico”**, não “nenhuma palavra que nomeia o tópico”. Fonte: contagem no [diagnostico_subunidade_17-09.csv](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/diagnostico_subunidade_17-09.csv:1). As previsões das 243 entradas presentes coincidem com os manifests dos builds.

   `100/251` pertence à baseline anterior, com heranças; o resultado desde as fontes é `84/251`. Essa diferença está explicitada em [pendencias.md:53](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/pendencias.md:53).  
   **Inferência:** ausência lexical nessa representação não demonstra ausência de informação no acervo; resultado observado não demonstra limite de todos os métodos admissíveis. O braço V demonstra utilidade da relação fornecida, não necessidade de fornecimento pelo professor.  
   **Consequência para a proposta:** retirar **“teto ≈40%”**, **“nenhuma fonte fornece”** e **“necessária sempre”**. Sustenta-se: há um gargalo importante de correspondência entre material e tópico; declaração é uma alternativa ainda por avaliar.

2. **[PARCIAL] H1 — Existem fontes aproveitáveis; alcance amplo e seguro não demonstrado.**  
   **Medido nesta revisão:** cruzamento do CSV com `manifest.json`, `.content_taxonomy.json` e `.timeline_index.json` nos dois conjuntos `.frzero` indicados, mantendo tokens e exclusividade do diagnóstico:
   
   Seção/card contém token exclusivo do gold em **10/159 erros**; rótulos das sessões SARC do bloco atribuído, em **20/159**. Entre os **132 ausentes/genéricos**, seção alcança **3**, SARC **7**, união **9**, sem dupla contagem. Minha contagem cobre todos os 159 erros presentes; não reproduz o recorte avulso de 150.

   A inspeção dos **63 materiais de código errados**, incluindo conteúdo textual dos arquivos e arquivos compactados, encontrou token exclusivo adicional em **2**: `basico3d-cpp` e `basico3d-py-zip`, ambos `modelagem`. Já pertencem aos candidatos da seção; **não aumentam a união de 9**. Fontes: [CSV:166](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/diagnostico_subunidade_17-09.csv:166) e respectivos `raw_target` no build CG.

   **Risco quantificado:** numa projeção lexical simples, escolher um tópico somente quando a seção contém tokens exclusivos de um único candidato produz **25 primários corretos/100 decisões**, recupera **8 erros** e perde **15 acertos**. Com SARC: **32/96**, recupera **13** e perde **10**. São sondas em memória sobre os mesmos materiais, **não resultados de execução do motor**.

   Há também relações textuais concretas no IA: aprendizado supervisionado → tarefa preditiva; não supervisionado → tarefas descritivas → agrupamento, em [introducao-a-ml.md:491](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/.frzero/pacote_categoria_17-09/Inteligencia-Artifical-Tutor/staging/markdown-auto/pymupdf4llm/introducao-a-ml.md:491) e [:621](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/.frzero/pacote_categoria_17-09/Inteligencia-Artifical-Tutor/staging/markdown-auto/pymupdf4llm/introducao-a-ml.md:621). Falta demonstrar aquisição segura da cadeia completa até o tópico curricular.

   O experimento anterior estrito registra **+2 primários, zero perdas**, incluindo **+1 transferível**: [log:3](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/compara_braco_estrito_x_C_14-09.log:3), [pendencias.md:434](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/pendencias.md:434).  
   **Inferência:** “nenhuma fonte” é excessivo. Os **9/132** são candidatos encontrados por esta inspeção, não teto nem correções garantidas. Datas, seção e ordem podem associar conteúdos distintos; o sinal precisa preservar escopo e conflitos.  
   **Consequência para a proposta:** declaração pode complementar relações não adquiridas com segurança. Não torná-la obrigatória nem reabrir as alavancas fechadas com base nessas contagens.

3. **[PARCIAL] H2 — O diagnóstico tem limitações de representação; isso não invalida o gold inteiro.**  
   **Medido:** o harness exige tokens com **≥4 caracteres** e calcula exclusividade entre slugs do curso inteiro ([diagnóstico:49](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/diagnostico_subunidade_17-09.py:49)). O scorer real admite siglas curtas consagradas pelo plano ([index.py:1850](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/timeline/index.py:1850)). Exemplo: `05-protocolo-dns` contém `DNS`, descartado pelo diagnóstico e presente no tópico do plano; ficou “genérico” ([CSV:241](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/diagnostico_subunidade_17-09.csv:241)).

   Dos **40 erros sem token exclusivo global**, **32** passam a ter algum token exclusivo quando a comparação fica restrita à unidade gold; em **9**, esse token aparece no material, sendo **7** com unidade já correta. Contagem no CSV cruzado com as taxonomias. Isso não garante discriminação útil: alguns tokens são `caso` e `nível`.

   `definition` e `not_confuse` existem, mas a montagem dos aliases utiliza termo e sinônimos, não esses campos ([content_taxonomy.py:459](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:459)). O seed já contém “modelos supervisionados” e uma definição de modelos descritivos com “agrupamentos” ([repo.py:1612](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/repo.py:1612)). Subtópicos numerados já são representados ([content_taxonomy.py:548](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:548)).  
   **Inferência:** os 40 não são comprovadamente indecidíveis. Consumir melhor contexto, relações e representação pode alterar o resultado sem declaração; **ganho não medido**. Herdar os mesmos termos da unidade para todos os irmãos não resolve sua distinção. Usar `not_confuse` como alias positivo inverteria sua finalidade. O seed é conhecimento codificado no produto, não aquisição independente do professor.  
   **Consequência para a proposta:** manter a régua; não transformar os **24 aceitos-não-primários** em acertos para elevar o placar. Separar ambiguidade curricular, perda de representação e falha de decisão antes de atribuir necessidade à declaração.

4. **[PARCIAL] H3 — A necessidade depende do curso e da relação faltante; não há preditor validado.**  
   **Medido:** TCC tem **7/11 primários**, com seus quatro erros distribuídos em **3 “presente” e 1 “genérico”**; IA tem **4/39**, com **31 “ausente”, 3 “genérico” e 1 “presente”**. Contagem por curso no [CSV](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/diagnostico_subunidade_17-09.csv:1).  
   **Inferência:** o problema não é uniforme. TCC enfraquece a generalização por curso, mas **7/11 não comprova dispensa de declaração para uma meta alta**. Também não está demonstrado que somente planos abstratos precisam de informação adicional: materiais multitópicos podem exigir convenção de prioridade mesmo com rótulos concretos.

   Um critério mensurável, sem gold na operação, seria a proporção de materiais com **vínculo explícito e não conflitante até um tópico**, acompanhada das colisões entre tópicos e da proveniência desse vínculo. Ainda falta calibrar sua capacidade de prever precisão em professores inéditos.  
   **Consequência para a proposta:** oferecer declaração para lacunas identificadas; não exigir preenchimento integral por curso nem prometer dispensa por um limiar lexical ainda não validado.

5. **[PARCIAL] H4 — LLM opcional é alternativa demonstrada, mas revisão humana não foi validada como solução completa.**  
   **Medido anteriormente, conforme registro:** VOCAB atinge **184/251**, produto com voter **186/251**, FR do zero **6→16/18** ([pendencias.md:448](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/pendencias.md:448)). Não demonstram cumprimento geral da meta em discussão.

   **Verificado no código:** qualquer arquivo manual existente bloqueia compilação, recompilação e refiltragem, antes de verificar seu conteúdo ([vocabulary_compile.py:225](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:225)). Entretanto, o loader continua fundindo o manual com um `.llm.json` preexistente ([repo.py:1732](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/repo.py:1732)).  
   **Inferência:** manual parcial, vazio ou contendo apenas veto pode congelar a atualização automática. Sua presença também **não certifica regime sem LLM**.  
   **Consequência para a proposta:** manter os regimes opcionais separados por proveniência. LLM com revisão pode reduzir trabalho manual, mas os dados não autorizam torná-lo requisito nem declarar resolvido o caso geral.

6. **[SUSTENTA] H5 — Canal reutilizável; formato precisa de garantias além da sintaxe.**  
   **Medido/verificado:** omitir o código normalmente cria **outra chave sem efeito**, não redireciona automaticamente ao tópico errado; o código documenta esse silêncio ([repo.py:1747](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/repo.py:1747)). O vínculo usa consulta pela chave exata ([course_vocabulary.py:25](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/course_vocabulary.py:25)). O veto remove termos da fusão dos sidecars, mas não é veto geral sobre label, seed ou demais sinais. O filtro contra nomes de seção aplica-se ao compilado, **não ao manual** ([repo.py:1749](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/repo.py:1749)).

   O precedente SO registra mudança do bloco para outra unidade por doações de “Pipes” e “Comunicação entre Processos” ([pendencias.md:806](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/pendencias.md:806)). Portanto, validação de duplicatas não garante ausência de regressão.

   Contagem das taxonomias: **IA 20 tópicos; CG 59**. Exigir **3–10 termos por tópico** implica **60–200** e **177–590 associações**, respectivamente; tempo e qualidade do preenchimento não foram medidos. No resync, a regeneração volta a montar a taxonomia ([incremental_build.py:109](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ops/incremental_build.py:109)).  
   **Inferência:** a declaração pode ser reutilizada enquanto plano e vocabulário permanecerem compatíveis. “Uma vez por curso” não cobre novos assuntos, renumeração ou mudança de rótulos.  
   **Consequência para a proposta:** formulário opcional, campos dispensáveis, chave preservada do plano e validação do vínculo efetivamente consumido. Distinguir “termos associados” de sinônimos na interface; preservar veto e proveniência. Antes de adoção, medir preenchimento real e efeito nos três eixos, incluindo arquivo novo no resync.

**VEREDITO SOBRE A AFIRMAÇÃO "SEMPRE": NÃO SUSTENTA**

**NÃO VERIFIQUEI:** novos builds/replays, ganho de regras propostas, aquisição por sumários integrais de livros, preenchimento por professor independente, precisão após revisão humana, generalização para cursos inéditos ou resync executado com o formulário. Revisão em `feat/motor-atribuicao`, HEAD `ce02a8f`; somente leitura, sem alterações, delegação ou chamadas adicionais de LLM.
