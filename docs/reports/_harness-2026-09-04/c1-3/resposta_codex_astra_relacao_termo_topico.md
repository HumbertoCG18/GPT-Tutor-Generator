**Existe técnica sem LLM para extrair essas relações. O acervo contém evidências úteis, mas ainda não sustenta uma solução automática completa para “perceptron → Modelos Preditivos”. Recomendo ampliar a aquisição de vocabulário por curso, preservando um único consumidor no motor.**

Auditoria somente leitura, com verificação do acervo delegada ao Astra (`/root/astra_acervo`). Nenhum arquivo alterado. Contagens reproduzidas nos manifests; taxas históricas conferidas nos logs, sem reexecutar o motor completo.

### 1. Auditoria do inventário

As contagens de bloco e unidade da §2 conferem nos **341 materiais de `.motor3eixos`**. A cópia `.ablacao` contém resultados com LLM e não representa esse mesmo regime.

Também conferi o braço C: **142/251 aceitos e 100/251 primários**; braço V: **175/251 e 134/251**. O V demonstra que fornecer aquelas relações melhora a atribuição. **Não demonstra como descobri-las sem LLM.** [Braço C:151](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/sem_curadoria_benchmark_13-09.log:151), [braço V:36](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/braco_V_13-09.log:36).

| Nº / mecanismo | Relação que realmente produz | Parecer |
|---|---|---|
| **1. Glossário** | Transporta relações fornecidas por outras fontes; transforma tudo em alias. Não descobre pertencimento. | **Manter o canal.** `GLOSSARY.md` é derivado; editar nele não sobrevive ao build. A persistência está nos sidecars. [repo.py:1713](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/repo.py:1713) |
| **2. Seed fixo** | Definições, equivalências e associações escritas manualmente. | **Conhecimento de domínio em `src/`: candidato a sair para dados por curso.** Contagem corrigida: **28 condicionais principais + 8 no auxiliar de contexto**, não 36 regras termo→tópico. [repo.py:1464](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/repo.py:1464) |
| **3. Evidência do glossário** | Recupera trechos para definir termos já enumerados pelo plano. | **Útil para definições; não resolve aquisição de relações novas.** A definição extraída não vira automaticamente vocabulário do tópico. [repo.py:1399](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/repo.py:1399) |
| **4. Sidecar do professor** | Infere associação curricular pela seção/sessão; doa tokens. | **Protótipo de aquisição, com ruído e dependência do motor.** Escolhe a unidade dominante usando `computed_unit_slug`; portanto, a relação não vem exclusivamente da estrutura original do professor. [gera_sidecar_professor.py:103](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/gera_sidecar_professor.py:103) |
| **5. Compilador LLM** | Classifica termos nos tópicos, mas grava pertencimento como `synonyms`. | **Funciona como aquisição opcional.** Deve permanecer identificável e excluível do cru. O próprio esquema descreve termos “que pertencem” ao tópico. [vocabulary_compile.py:61](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:61) |
| **6. Doação de headings** | Inferência por semelhança lexical com o rótulo; não prova sinonímia nem pertencimento. | **Candidata a perder autoridade autônoma.** Mesma estrutura responsável por selecionar o tópico acrescenta o heading aos aliases. [content_taxonomy.py:603](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:603) |
| **7. Segunda passada** | Mistura associação aprendida das próprias previsões, decomposição legítima do rótulo e decisões por título/seção. | **Não é uma peça única.** Preservar a distinção: retirar propagação e retirar partes do rótulo têm efeitos diferentes. [resolver_apply.py:262](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/resolver_apply.py:262) |
| **8. Correções aprendidas** | Relação supervisionada por humano: termos do material → unidade corrigida. | **Manter como evidência humana.** O registro admite subunidade, mas `build_learned_unit_boosts` só usa a unidade. [tag_profile.py:159](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/models/tag_profile.py:159) |
| **9. Perfil semântico** | Filtra ferramentas e orienta suporte lexical. Não descobre termo→tópico. | `domain_cues` e `tool_aliases`: **placeholders sem consumidor de decisão localizado em `src`**. Os cues fixos de MF são candidatos à externalização. [semantic_config.py:21](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/semantic_config.py:21), [content_taxonomy.py:258](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:258) |
| **10. Co-heading** | Infere associação pela estrutura do documento. | **Experimento insuficiente, não refutação universal da técnica.** Usa título, label e dois primeiros headings como possíveis âncoras; avalia com unidade fixada. Comparar 31/93 diretamente com 37/39 mistura universos. [coheading.py:77](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-02/coheading.py:77) |
| **11. Resumo de código** | Extrai identificadores/texto e reconhece aliases existentes. Não descobre a categoria deles. | **Manter como extração**, com ressalva de proveniência e cache descrita abaixo. [code_summarization.py:565](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:565) |
| **12. Siglas do plano** | Permite reconhecer tokens curtos já presentes nos rótulos. | **Manter.** Normalização lexical por curso; não constitui aquisição semântica nova. [stopwords.py:131](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/text/stopwords.py:131) |

O produto tem **14 aliases armazenados** para Modelos Preditivos, mas um deles é o próprio rótulo. No cru são dois itens armazenados: o rótulo e **um alias adicional**, `modelos supervisionados`. A diferença alegada está correta quando descontamos o próprio nome.

**Achados adicionais relevantes:**

- **Transporte com perda, reproduzido:** `["TCP/IP"]` → serialização do glossário → `["IP", "TCP"]`. O parser divide em `/`, além de outros delimitadores. Não prova perda de acurácia nesse caso; prova que o canal não preserva qualquer expressão. [content_taxonomy.py:407](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:407).
- **`determ-v3` não garante independência de LLM:** `course_aliases` lê explicitamente `.glossary_curation.llm.json`. O produtor é determinístico, mas seus insumos podem ter origem LLM.
- **Cache de vocabulário desatualizado, reproduzido em memória:** no material real `tcp-chat-c`, mudar os aliases muda o resumo recém-calculado; o cache continua devolvendo o anterior porque sua chave considera o bundle, não o vocabulário. **Impacto no placar não medido.** [code_summarization.py:134](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:134), [cache:647](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:647).
- **“Não lê `moodle_label`” precisa de escopo:** o scorer não lê esse campo diretamente. Para zips, o sintetizador pode incorporá-lo ao título que chega ao scorer. [code_summarization.py:629](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/code_summarization.py:629).

Outra correção: **36/38 não mede “quando tem token, acerta”**. Mede presença de token distintivo entre os casos em que o filho acertou. Também há token nos cinco erros do filho e em oito acertos do pai. A associação existe; a interpretação causal mais forte não está demonstrada. [Handoff:2445](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:2445).

### 2. O que já existe fora do projeto — e o que o acervo sustenta

Astra examinou **32 PDFs originais de IA, 1.354 páginas**, e **15 de FR, 258 páginas**, com extração nativa de texto, sem usar gold.

Na busca literal por PDF, `modelos preditivos` e `modelos descritivos` tiveram **zero ocorrências no IA**. Os radicais `preditiv` e `descritiv` apareceram em três e cinco documentos. **Isso não prova ausência semântica**: figuras, quebras de linha e outras formulações escapam; “estatística descritiva” também produz ocorrência sem representar o tópico desejado.

| Técnica | O que oferece sem LLM | Sustentação neste acervo |
|---|---|---|
| **Padrões Hearst** | Extrai relações direcionadas de formulações como “Y, incluindo X”. Técnica estabelecida; métodos baseados em padrões continuam competitivos em avaliações de hiperonímia. [Hearst](https://aclanthology.org/C92-2082/), [Roller et al.](https://aclanthology.org/P18-2057/) | **Parcial.** FR contém exemplificação explícita de protocolos. A expressão testada “é um tipo de” não ocorreu nos PDFs examinados. Não sustenta prometer resolver IA com uma regex desse padrão. |
| **Estrutura local do professor** | Usa listas, subtítulos, tabelas e seções para extrair associação curricular. | **Melhor evidência encontrada.** Perceptron e MLP aparecem sob tarefas supervisionadas. Precisa preservar a hierarquia local; estar no mesmo arquivo é insuficiente. |
| **Extração de definição** | Recupera categoria e função declaradas em frases definidoras. | **Há ponte parcial:** supervisionado → tarefa preditiva; não supervisionado → tarefas descritivas. Ainda falta ancorar essas expressões nos rótulos exatos do plano. |
| **Tesauro/ontologia externa** | Fornece relações explícitas previamente construídas. WordNet distingue sinonímia e hiperonímia; CSO organiza tópicos de computação. [WordNet](https://wordnet.princeton.edu/), [CSO](https://cso.kmi.open.ac.uk/about) | **Não validado para estes rótulos.** Pode trazer conhecimento ausente, mas exige correspondência demonstrável com a organização curricular do professor. Não verifiquei uma cadeia externa que resolva este caso específico. |
| **Coocorrência, TF-IDF/LSA, embeddings** | Recupera proximidade de contexto; pode gerar candidatos. SBERT, por exemplo, produz embeddings comparáveis por similaridade. [SBERT](https://aclanthology.org/D19-1410/) | **Nenhum ganho medido aqui.** Similaridade não determina direção, categoria ou granularidade curricular. |

As relações encontradas são concretas:

**Perceptron/MLP → tarefas supervisionadas:** `Rede Perceptron.pdf`, página 4, apresenta “Redes Feed Forward”, “Tarefas Supervisionadas: classificação … e regressão”, “Perceptron” e “MultiLayer Perceptron”. O trecho também aparece em `MLP.pdf`. As transcrições correspondentes foram confrontadas com os PDFs: [rede-perceptron.md:188](C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor/content/curated/rede-perceptron.md:188), [mlp.md:137](C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor/content/curated/mlp.md:137).

**Supervisionado → tarefa preditiva:** `Introdução a ML.pdf`, página 21, define a tarefa como encontrar uma função/modelo para prever rótulo ou valor. Na página 27, não supervisionado executa tarefas descritivas e inclui agrupamento. [introducao-a-ml.md:713](C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor/content/curated/introducao-a-ml.md:713), [página correspondente:935](C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor/content/curated/introducao-a-ml.md:935).

**FR já enumera várias relações no plano:** DNS/DHCP/SNMP/NAT → infraestrutura; HTTP/HTTPS/SMTP/POP3/IMAP → protocolos do usuário. Portanto, para esses termos, adquirir conhecimento externo não resolve necessariamente o problema: a relação já está disponível. [COURSE_MAP.md:21](C:/Users/Humberto/Documents/GitHub/Fundamentos-de-Redes-Tutor/course/COURSE_MAP.md:21).

**Fronteira dos embeddings:** “local” informa onde roda, não que modelo é. TF-IDF/LSA não exigem modelo de linguagem pré-treinado; word2vec é aprendizado estatístico; SBERT usa um modelo de linguagem pré-treinado; embeddings também podem vir de LLMs. Se a restrição significa **nenhum conhecimento aprendido em modelo de linguagem**, SBERT fica fora. Se significa **nenhuma chamada a LLM generativo**, pode haver espaço. **A escolha é sua; o primeiro experimento proposto dispensa todos eles.**

### 3. Onde entra, sem multiplicar decisões

**Na sua definição de eixo, um extrator novo é, sim, uma nova fonte de sinal.** O que podemos evitar é acrescentar outro voto, peso especial ou fallback ao resolvedor.

Recomendação: **mesmo canal de vocabulário por curso, relações distintas dentro dele**.

- `synonyms`: nomes equivalentes do conceito.
- `topic_terms`: técnicas/conceitos associados ao tópico naquele curso, com trecho e origem que sustentam a relação.

Isso não exige um grafo genérico ou um novo classificador. O scorer existente pode consumir as expressões admitidas como evidência textual, preservando a distinção no dado e na explicação. **Não publicar k-NN como sinônimo de Modelos Preditivos.**

Também não chamaria toda associação curricular de hiperonímia: “abordado neste tópico” é uma afirmação mais limitada que “é um subtipo de”. SKOS já separa rótulos alternativos, relações hierárquicas e relações associativas; serve de referência conceitual, sem precisar adotar RDF. [SKOS](https://www.w3.org/TR/skos-reference/).

Para o resync, cada relação automática precisa identificar **fonte, localização e versão/hash do insumo**. Fonte alterada → relação reavaliada. Correção humana permanece distinguível. O teste de cache mostra por que registrar somente o produtor não basta.

### 4. Mapa de consolidação — sem executar

Sua leitura está **majoritariamente correta**: nºs 1, 2, 4, 5, 6 e parte do 7 convergem para vocabulário do tópico. Mas misturam **armazenamento, aquisição e decisão**.

| Camada possível | O que reunir | Distinção que precisa sobreviver |
|---|---|---|
| **Aquisição de vocabulário** | Seed externalizado, extração do professor, compilação LLM e candidatos de headings | Origem, tipo de relação e evidência. Uma origem não deve validar outra circularmente. |
| **Vocabulário por curso** | Canal do glossário e aliases hoje espalhados | Sinônimo, associação curricular e parte literal do rótulo. Deduplicar expressão sem apagar proveniência. |
| **Evidência do material** | Título, headings, corpo, label e resumo de código | São representações do mesmo documento; não necessariamente confirmações independentes. |
| **Estrutura e arbitragem** | Datas/SARC, seção, card, heranças, correções manuais e precedências | Tempo, pertencimento estrutural e autoridade humana não são vocabulário. Não os fundir num único peso. |

A segunda passada exige cuidado especial: **decompor rótulo é aquisição lexical; título/seção sobrescreverem uma decisão é arbitragem**. Colocar tudo numa função de vocabulário apenas esconderia a cascata.

**Candidatos a sair:** regras específicas de MF/IA de `src/`; placeholders sem consumidor; doação autônoma de headings sem evidência rastreável; propagação apoiada somente na confiança da própria previsão. A retirada comportamental precisa de ablação individual: saldo agregado zero já escondeu perdas por curso.

### 5. Primeiro experimento falsificável

**Hipótese:** enumerações explicitamente ancoradas nas fontes acrescentam relações úteis ao vocabulário existente, sem alterar regras de decisão.

1. **Congelar o protocolo antes da régua.** Usar plano, estrutura original Moodle/SARC e texto nativo dos materiais. Excluir glossário compilado, descrições LLM e aliases derivados de previsões. Fixar versões, hashes e regras de extração.

2. **Extrair somente relações locais explícitas.** Começar com `categoria: itens`, `categoria (itens)` e exemplificações delimitadas. A categoria deve casar com rótulo ou equivalência documental admissível no cru. Não inserir silenciosamente `supervisionado = preditivo`. Preservar negações e registrar arquivo, página/linha e trecho.

3. **Auditar os candidatos sem consultar gold.** Separar relações novas de duplicatas do plano. Uma relação sem âncora suficiente não entra. **Zero relação nova admissível → encerrar esse extrator**, sem afrouxar regras depois de olhar os erros.

4. **Comparar no motor completo.** Baseline reproduzido, mesmos insumos, apenas o vocabulário extraído como diferença. Avaliar FR do zero e sete cursos, por material, em bloco, unidade, subunidade aceita e primária. Recalcular dependências de vocabulário para evitar o cache antigo demonstrado nesta auditoria.

5. **Aplicar o corte previamente declarado.** Eu continuaria com **≥5 novos acertos primários e ≥5 aceitos nos sete cursos**, sem perder nenhum item anteriormente correto em qualquer eixo avaliado. No FR do zero: preservar pelo menos **6/18 primários e 7/18 aceitos**, também sem trocas escondidas.

Esse mínimo é **critério de investimento, não significância estatística**. Não exigiria ganho no FR para provar uma aquisição voltada à lacuna do IA: FR funciona como controle de regressão. Se permanecer igual, o experimento **não demonstrou melhoria em curso construído do zero**.

Os sete cursos e o FR já foram examinados repetidamente. Congelar o extrator antes do gold evita escolher termos pelo placar, mas não transforma esses cursos em holdout novo. Generalização exigirá posteriormente outro curso.

**Limite esperado:** o extrator estrito pode recuperar relações já conhecidas no FR e nenhuma ponte completa no IA. Esse resultado seria útil: mostraria exatamente onde termina a evidência explícita e começa a necessidade de correspondência semântica adicional.

### 6. O que não fazer

- Acrescentar `perceptron`, `k-NN` ou `supervisionado → preditivo` como regras especiais no motor.
- Doar todos os termos de um documento porque ele recebeu classificação confiante.
- Tratar proximidade vetorial, coocorrência ou mesma aula como prova de sinonímia.
- Declarar regime sem LLM apenas por registrar zero chamadas ou `model: determ-v3`.
- Fundir os métodos agora, ajustar o extrator olhando gold ou chamar ganho concentrado no IA de solução geral para ≥95%.
