**≥95% sem LLM não foi demonstrado nem refutado. O brief confunde melhor placar observado com teto de informação.**

Parecer do Astra, confrontado com código local e recontagem dos manifests. Reconfirmei **V = 134/251 primário, 175/251 aceito**; não reexecutei o motor. Nenhum arquivo alterado.

### 1. Causa real: três problemas, com uma relação semântica ausente no centro da subunidade

**Concordo parcialmente com a suspeita de remendos.** Não há evidência de uma causa única para os três eixos:

- **Bloco:** colocação temporal do material.
- **Unidade:** pertencimento curricular versus colocação temporal.
- **Subunidade:** reconhecimento do assunto e escolha do principal.

Na unidade, o brief omite uma exceção importante: **unidade explícita já pode vencer o bloco**. Nos conflitos restantes, o bloco sempre decide. Isso mistura “quando foi usado” com “a que conteúdo pertence”. [file_map.py:785](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:785)

Na subunidade, a hipótese **“plano nomeia categoria; material nomeia técnica”** tem sustentação experimental: fornecer a relação lexical corrigiu 34 primários sem alterar os outros eixos. Reordenar precedências não fornece essa relação; acrescentar vocabulário fornece.

Mas **“o problema é apenas selecionar os tópicos” não foi demonstrado**. V escolheu os tópicos olhando os erros **e importou as relações de um sidecar de LLM**. Provou efeito da relação fornecida; não provou aquisição automática elegível. [motor_3eixos_12-09.py:186](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py:186)

Há defeitos adicionais verificados:

- `moodle_label_text` chega ao coletor, mas o scorer de subunidade não o consome. [entry_signals.py:173](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/entry_signals.py:173), [index.py:1835](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/timeline/index.py:1835)
- A doação promove heading a alias após associação inferida pelo próprio sistema. Essa associação volta como evidência lexical, reforçando inclusive erros. [content_taxonomy.py:603](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:603)
- O bônus `+0,04` existe, mas **seu impacto no placar não foi isolado**. Não tratá-lo como causa principal.

Recontagem do CSV: **87 dos 109 erros aceitos de subunidade têm unidade correta; nove têm unidade errada; 13 não têm régua de unidade**. Portanto, resolver unidade não resolve a maior parte da subunidade. [CSV dos erros](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/erros_subunidade_cru_honesto_13-09.csv)

### 2. Alcançabilidade: déficit conhecido; teto determinístico desconhecido

| Eixo | Cru registrado | Mínimo ≥95% | Ganho líquido necessário |
|---|---:|---:|---:|
| Bloco | 222/237 | 226/237 | +4 |
| Unidade | 253/284 | 270/284 | +17 |
| Subunidade primário | 100/251 | 239/251 | +139 |

Fonte: [baseline registrado:149](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/sem_curadoria_benchmark_13-09.log:149). V ainda precisa de **105 primários líquidos**; produto, **53**.

**Não existe teto determinístico medido nesses dados.** Também não existe prova de que uma arquitetura nova alcance 95%. Os experimentos refutam regras específicas; não esgotam os algoritmos possíveis.

Somar os 17 erros de unidade adjudicados e anunciar 95,1% também não demonstra solução: pressupõe selecionar exatamente os erros sem perder acertos. O próprio log chama esse contrafactual de “teto medido”. [braco_V_13-09.log:39](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/braco_V_13-09.log:39)

**Onde a informação pode acabar:** identificar “árvore de decisão” não determina sozinho qual categoria e qual prioridade aquele professor adotou. Para remover essa indeterminação, uma fonte teria que declarar uma relação como:

| Fonte | Informação necessária |
|---|---|
| Plano | Técnica/subtema subordinado ao código curricular |
| Moodle | ID do recurso associado ao código do tópico principal |
| SARC | Aula associada ao tópico curricular e aos recursos utilizados |

São **contratos propostos**, não campos cuja existência atual esteja comprovada. Nem todos precisam existir: uma ligação inequívoca pode bastar.

Outra limitação: o “cru honesto” parte de cópia do produto e mantém curadoria humana; retirar termos selecionados pelo benchmark não certifica criação integral apenas com fontes do professor. [motor_3eixos_12-09.py:66](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py:66)

### 3. Arquitetura: generalizar evidência e rastreabilidade, não três cascatas arbitrárias

**Desenho proposto, ganho ainda não medido:**

```text
Fontes do professor
  → extração com origem e vínculo entre objetos
  → relações curriculares comprovadas
  → candidatos por eixo
  → decisão com método + evidência + conflitos
```

Reaproveitar os métodos existentes. Cada método deve declarar **quando se aplica, qual candidato propõe e qual trecho/vínculo sustenta a proposta**.

Bloco temporal e unidade curricular precisam conservar decisões separadas. O bloco pode ajudar a unidade; não deve redefinir automaticamente seu significado. Isso **não implica “texto sempre vence”**, regra já refutada.

Para vocabulário, distinguir **sinônimo** de **técnica pertencente a uma categoria**. “Árvore de decisão” não é sinônimo de “modelo preditivo”; é uma relação de pertencimento. Guardar essa relação evita transformar toda menção em equivalência.

Adaptar convenções observáveis: código curricular explícito, data no nome, seção temática, vínculo recurso→aula. Evitar exceções por professor escolhidas depois de olhar seus erros.

Método novo entra primeiro em comparação, preservando a decisão atual. Promoção exige ganho e ausência de regressão no recorte congelado, além de validação em professor não usado no desenvolvimento. **Sete cursos verdes comprovam compatibilidade nesses sete; não garantem generalização.**

### 4. Vocabulário: antes de selecionar “carentes”, extrair relações para todos

**Não há seletor validado. Isso não prova inexistência de sinal.**

A primeira tentativa sem LLM deve aproveitar relações explícitas em **todos os tópicos**: hierarquia do plano, seção vinculada a código, cabeçalho que declara categoria e técnicas. Sem chamadas pagas, selecionar apenas K tópicos pode ser uma otimização desnecessária.

O requisito central é **âncora independente**. “O motor colocou o arquivo neste tópico; logo seus headings enriquecem este tópico” reproduz a circularidade atual.

Poucos aliases, margem baixa e coocorrência podem localizar incerteza; não comprovam a relação correta. Se nenhuma fonte declarar ou permitir inferir essa relação com qualidade suficiente, o extrator não a inventará.

Curadoria pelo aluno violaria o caminho feliz pedido. Nesse cenário, resta melhorar o contrato das fontes ou reduzir a promessa de automação. **Uma interface de curadoria não satisfaz o requisito original.**

### 5. Primário: há problemas diferentes escondidos nos 42 casos

**142 − 100 = 42 materiais; diferença de 16,73 pontos.** Isso prova apenas que o motor escolheu um extra aceito.

Os exemplos locais mostram causas distintas:

- **MF:** lógica proposicional tem nota explícita de ausência de tópico próprio na taxonomia. É problema de representação. [subunit_gt_MF.csv:11](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/subunit_gt_MF.csv:11)
- **IA:** MLP com GridSearchCV recebe modelo preditivo como principal e métricas como extra, conforme decisão registrada do usuário. É política de prioridade. [subunit_gt_IA.csv:27](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/subunit_gt_IA.csv:27)

Não dá para chamar os 42 de desempate, nem de ambiguidade irredutível. É necessário distinguir assunto dominante, relação pai/filho, taxonomia incompleta e convenção de anotação.

**Mesmo corrigindo os 42, chegaríamos a 142/251 primários.** Ainda faltariam **97 correções entre os materiais hoje fora do aceito**, preservando todos os acertos.

### 6. Ordem e critérios de parada

1. **Certificar o baseline de criação.** Partir dos arquivos e fontes autorizadas, com política explícita de primário. Encerrar quando toda entrada usada tiver proveniência e o resultado puder ser reproduzido sem artefatos derivados de LLM ou curadoria por material.
2. **Medir sinais disponíveis que não chegam ao decisor.** Moodle label e conteúdo de ZIP em braços separados. Não promover braço sem ganho líquido ou com regressões; não estimar ganho pela contagem de arquivos afetados.
3. **Testar aquisição de relações explícitas para todos os tópicos.** Congelar o extrator antes da avaliação. Encerrar a hipótese se não produzir relações válidas e ganho fora dos cursos usados para desenvolvê-lo.
4. **Modularizar somente a decisão necessária às evidências aprovadas.** Preservar fallback e testar criação versus resync. Não promover método que dependa de exceções escolhidas pelo placar.
5. **Cobrar a meta no processo completo.** Exigir os três mínimos da tabela, sem excluir abstenções para melhorar a taxa, e validar em professor novo. FR continua sem avaliação de bloco/unidade nesse recorte; o agregado não certifica todos os cursos.

**Não fazer:** reescrita geral agora; outra regra global de precedência; novo seletor baseado apenas em incerteza; bundle já refutado; curadoria dirigida disfarçada de aquisição; promessa de precisão por modularização.

### 7. Medição decisiva que falta

Produzir, por material, a cadeia:

**disponível na fonte → extraído → consumido → relação curricular sustentada → principal escolhido.**

Congelar o procedimento antes de consultar os erros. Isso separa perda de entrada, falha semântica e falha de prioridade sem transformar classificação manual de erros em “teto”.

Para o primário, dois avaliadores devem julgar usando exclusivamente as fontes permitidas, sem ver a predição. Divergências precisam indicar qual informação ou convenção falta; desacordo humano, sozinho, também não estabelece teto matemático.

**Próximo passo: certificar a criação crua e localizar onde essa cadeia rompe. O braço V já demonstrou que fornecer a relação certa funciona; falta demonstrar que o sistema consegue obtê-la nas condições exigidas.**
