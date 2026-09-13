> SEGUNDA CORRIDA do mesmo brief (`brief_codex_astra_aquisicao_vocabulario.md`), acidental: o primeiro processo nao
> tinha morrido e as duas terminaram. As duas respostas sao independentes e **convergem nas quatro correcoes** — e
> divergem nos numeros de ORCAMENTO (que ambas marcam como decisao, nao como parametro medido). A corrida 1 esta em
> `resposta_codex_astra_aquisicao_vocabulario.md`.

**Vocabulário é a melhor alavanca demonstrada. Ainda não há evidência de que aquisição, sozinha, entregue 90%. O desenho precisa selecionar relações termo→tópico e controlar aliases concorrentes.**

Conferi código, sidecars e contagens dos CSVs. Não reexecutei o motor nem fiz chamadas de rede. Os resultados dos braços abaixo vêm dos logs existentes. `c1-3/` refere-se a `docs/reports/_harness-2026-09-04/c1-3/`.

### 1. Análise: o enquadramento precisa de quatro correções

**“Só os 5 termos do CG são de domínio” está errado.** Recontagem confirma 66 termos, mas IA contém `crossover`; ES2 contém `circuitbreaker`, `nameserver` e `gateway`. Reconhecer um termo técnico não basta: ele precisa apontar para o tópico adequado. Evidência: `../Inteligencia-Artifical-Tutor/course/.glossary_curation.json:11`, `../Engenharia-Software-2-Tutor/course/.glossary_curation.json:8`.

**O sidecar preservado hoje tem proveniência mista.** A nota geral “gerado automaticamente sem gold” não descreve todas as entradas:

- ES2 `gateway`: acrescentado após replay, com ganho e perdas registrados.
- CG curvas: curadoria de 12/09, também medida em replay.
- SO: veto manual posterior à geração.

Isso não prova quanto dessas intervenções entrou em cada snapshot histórico. Prova que **o arquivo atual não pode ser tratado integralmente como geração cega de 07/09**. A afirmação “só sobra dependência de gold no prompt” precisa dessa ressalva. Evidência: ES2 linha 97, `../Computacao-Grafica-Tutor/course/.glossary_curation.json:13`, `../Sistemas-Operacionais-Tutor/course/.glossary_curation.json:71`.

**Os dois adquiridores não recebem exatamente a mesma entrada.** Compartilham o acervo, mas:

| Aspecto | Determinístico | LLM |
|---|---|---|
| Porta de entrada | Seção/SARC precisa nomear um tópico | Unidade prevista com materiais |
| Representação | Tokens isolados; mínimo de 4 caracteres | Expressões, siglas e variantes |
| Headings | Até 8 por material | Até 24, limitados a 60 caracteres |
| Associação | Herda o tópico da seção/SARC | Classifica semanticamente nos tópicos |

Evidência: `c1-3/gera_sidecar_professor.py:103`, `:113`, `:135`; `src/builder/core/vocabulary_compile.py:173`, `:239`.

Portanto, **a hipótese forte é seleção semântica + associação**, mas o experimento não isolou apenas o classificador. Também variam cobertura, recorte e representação. Os 552/560 termos atestados, registrados no handoff, demonstram disponibilidade textual; não demonstram igualdade dos bundles efetivamente apresentados.

**O que separa `perceptron` de `chiara`:** função no contexto e relação com a taxonomia. Um designa técnica; o outro pode aparecer como autoria. Frequência, concentração e posição em heading não estabelecem essa diferença. Sobrenomes também nomeiam técnicas: banir nomes próprios derrubaria termos válidos.

O separador é computável sem LLM **quando existe conhecimento adicional**: definição explícita no texto, glossário técnico com relações categoria→técnica ou curador humano. Um dicionário que apenas reconhece palavras técnicas ainda não resolve `perceptron → Modelos Preditivos`.

**Não há evidência de que as heurísticas locais atuais resolvam essa associação. Também não há prova de impossibilidade sem LLM.**

### 2. Desenho executável da aquisição

Proponho uma primeira versão conservadora. **Os limites abaixo são decisões de orçamento, não parâmetros comprovados pelo benchmark.**

**Fonte:** plano como taxonomia; título, label Moodle e headings originais como evidência. SARC/seção fornecem contexto. Não usar previsões de subunidade, aliases propagados ou gold como justificativa de associação.

A unidade prevista serve para organizar lotes, **não para excluir destinos**: cada chamada recebe o índice dos tópicos do curso inteiro. Isso evita obrigar um material já mal agrupado a doar vocabulário dentro da unidade errada.

**Unidade de aquisição:** relação contextual, não palavra solta:

```json
{
  "term": "k-NN",
  "topic_key": "<código e rótulo existentes no plano>",
  "relation": "tecnica",
  "evidence": [{
    "entry_id": "<material>",
    "field": "heading",
    "quote": "<trecho literal>"
  }]
}
```

Isso é mais precisamente um **indicador de tópico**: `k-NN` não é sinônimo de “Modelos Preditivos”.

**Admissão:** exigir ocorrência verificável no bundle, tópico existente e associação semanticamente sustentada. Autor, boilerplate, menção incidental e associação ambígua ficam fora da publicação automática. Termo compartilhado entre tópicos não ganha exclusividade artificial: permanece pendente.

**Seleção de tópicos:** abandonar o ranking “carente” como proposta superior. Ordenar lotes pela quantidade de materiais, desempate pelo código curricular. É o baseline simples já competitivo. Examinar todos os tópicos do lote; publicar apenas aqueles com relações admissíveis.

Dentro de cada tópico, ordenar termos pela cobertura adicional de materiais com ocorrência literal. Admitir até três; variantes redundantes não ocupam vagas. Essa cobertura é critério de economia, **não estimativa de ganho de acurácia**.

| Limite inicial | Orçamento |
|---|---:|
| Chamadas | Até 8 por curso |
| Entrada | Até 24.000 caracteres por chamada |
| Saída | Até 2.000 tokens por chamada |
| Publicação | Até 3 termos/tópico e 24 relações/lote |

Uma chamada por lote; lote de materiais sem unidade também consome orçamento. No snapshot atual, as unidades elegíveis são MF 3, SO 6, IA 4, ES2 2, TCC 4, CG 7, FR 2 e LR 1. Os números mudam se houver divisão por tamanho.

Distribuir o espaço entre materiais; não truncar silenciosamente os últimos. Registrar omissões. Esgotado o orçamento, parar com cobertura parcial explícita. Sem retries invisíveis; qualquer tentativa adicional consome o teto.

**Gravação:** reutilizar `course/.glossary_curation.llm.json` para relações aprovadas, com o formato `synonyms` que o loader já consome. Guardar evidências e decisões em metadados. Preservar `course/.glossary_curation.json` para intervenção humana.

**Não fazer:** repetir doação de tokens por concentração; ampliar listas para preencher orçamento; usar `score > 0` como evidência; promover headings pela própria previsão; escolher K depois de ver o placar.

A propagação atual pode recriar aliases errados após a aquisição (`src/builder/extraction/content_taxonomy.py:603`). O experimento deve separar **adicionar vocabulário** de **substituir aliases automáticos sem associação validada**. Caso contrário, não saberemos qual mudança causou o resultado.

### 3. Contrato mínimo de LLM e curso novo

Hoje já existe compilação por unidade, mas faltam garantias importantes:

- Qualquer arquivo “manual” bloqueia toda compilação, mesmo parcial ou automático: `vocabulary_compile.py:227`.
- Cache depende da existência do arquivo, sem chave de conteúdo: `:230`.
- Sem unidades previstas, não compila; espera outro reprocessamento: `:245`.
- `_raw` guarda termos, mas não conserva bundle, citações e versão do prompt: `:197`.

**Contrato proposto:** uma versão publicada do vocabulário por snapshot de entrada. Cache identificado por hash da taxonomia, materiais efetivamente apresentados, prompt, schema e modelo. Conservar entrada exata, resposta bruta, relações aprovadas/rejeitadas, motivo, tentativas e consumo.

Curso novo: extrair o acervo local, montar taxonomia, executar atribuição inicial sem aquisição e compilar os lotes. A unidade inicial continua sendo hipótese. Sem material, não inventar termos; sem modelo/cache, executar com a base disponível e registrar aquisição ausente. Falha ou JSON inválido preserva o vocabulário anterior.

A existência do arquivo manual deve proteger decisões humanas, não significar “curso inteiro já coberto”. Essa alteração é necessária para aquisição incremental.

**Curador humano pode substituir a chamada.** Recebe os mesmos materiais, tópicos e contrato de evidência. Pode publicar no arquivo manual existente. Entretanto, copiar cegamente `.llm.json` para `.json` não garante comportamento idêntico: o loader filtra nomes de seção apenas no arquivo LLM. Evidência: `src/builder/artifacts/repo.py:1732`, `:1753`.

**LLM necessário?** Não necessariamente. Necessária é alguma fonte de competência semântica. O LLM é a alternativa automatizada com sinal positivo disponível.

**Número sem aquisição LLM:** braço cru documentado = **146/251, 58,2%**. A campanha antiga do professor = **146/233, 62,7%**, em outra base e configuração; não substitui o número atual. Não existe medição que autorize afirmar um teto para curadoria humana, glossário externo ou novo classificador determinístico. Também não demonstramos ausência de LLM em toda a produção dos insumos.

Se o usuário aceita LLM na compilação e exige atribuição posterior offline, o contrato é viável. Se exige **nenhum conhecimento adquirido por LLM**, devolver o sidecar atual não satisfaz essa definição de cru.

### 4. Validação: sem gold na aquisição, com referência independente na avaliação

**Não existe caminho para comprovar 90% de acurácia sem alguma verdade de referência.** Ocorrência literal, consistência e estabilidade verificam o artefato; não verificam a classificação correta.

Os sete cursos conhecidos servem para desenvolvimento e regressão. LOCO executado agora pode revelar falhas, mas não apaga decisões anteriores tomadas olhando todos eles.

**LR: adjudicar os seis materiais instrucionais existentes.** O manifest tem sete entradas; uma é cronograma. Incluir apresentação e introdução, permitindo “nenhum tópico” quando apropriado. Não excluí-las depois de ver a previsão. Todos os seis estão atualmente na mesma unidade, e o curso já possui `.glossary_curation.llm.json`.

Para cada material, dois julgamentos independentes, sem acesso às previsões: unidade, tópico primário, alternativas aceitáveis, ausência válida e trecho/página de sustentação. Divergências adjudicadas. Aquisição e previsões devem estar congeladas antes de abrir esses rótulos.

**Seis materiais não validam transferência ampla.** Mesmo 6/6 resulta em limite inferior unilateral de 95% de aproximadamente 60,7%, sob hipótese binomial independente. A concentração em uma unidade limita ainda mais a generalização entre cursos.

Proponho orçamento adicional de **200 materiais de pelo menos quatro cursos/turmas ainda não examinados**, selecionados antes dos resultados. Duzentos é orçamento de avaliação, não garantia estatística. Publicar acurácia total, por curso, intervalos e diferenças pareadas; não interpretar materiais do mesmo curso como réplicas independentes de transferência.

Comparações obrigatórias, no mesmo snapshot:

| Braço | Pergunta |
|---|---|
| Base congelada | Qual o ganho líquido? |
| Compilador v2 existente | O novo contrato supera o disponível? |
| Maior unidade | O seletor acrescenta algo? |
| Aleatório, mesmas vagas e sementes fixadas | Há vantagem sobre alocação casual? |
| Todos os termos admissíveis | A seleção esparsa evita dano? |

Compartilhar candidatos e orçamento nas comparações de seleção. Contabilizar aquisição separadamente. Abstenções permanecem no denominador.

**Prompt v2:** congelá-lo e testar prospectivamente já permite medir transferência do v2. Não torna seu desenvolvimento independente do benchmark.

Para medir o efeito da escolha v1→v2, recuperar o v1 exato do histórico; compilar ambos com corpus, modelo e orçamento equivalentes em cursos novos; congelar as saídas; depois abrir a adjudicação. Uma comparação predefinida, sem escolher prompt por curso. Recompilar IA mede sensibilidade dentro da amostra, não transferência. Se v1 não for recuperável, a diferença histórica não pode ser isolada honestamente.

### 5. Erros restantes, unidade e critérios de parada

**Recontagem dos CSVs:**

| Recorte | Resultado | Implicação |
|---|---:|---|
| Erros compartilhados cru/produto | 25; 24 na unidade certa | Predomina problema dentro da unidade |
| Desses, gold vazio | 6 | Adquirir mais termos não é a correção direta |
| Predição vazia no cru | 14; produto resolve 11 | Parte é recuperável; mecanismo ainda precisa ser separado |
| Erros totais do produto | 27 | Os 25 compartilhados não incluem 2 regressões |

Os outros 19 erros compartilhados exigem diagnóstico por material: relação ausente, termo existente que perde, alias concorrente ou informação insuficiente. A lista sozinha não decide isso. Exemplos: `c1-3/erros_subunidade_motor_12-09.csv:2`, `:36`, `:58`, `:90`.

Os três tópicos com algum suporte por frase **não estão automaticamente resolvidos no vocabulário**: suporte em outro material do tópico não prova suporte no material errado. Classificar como competição somente quando a evidência relevante aparece naquele material e perde para outro candidato.

**Unidade: os 10 não estão demonstrados como ganho de vocabulário.** O controle existente diz:

- RÉGUA → VOCAB: **253→255**, ganho líquido de 2.
- VOCAB → PRODUTO: **255→263**, ganho líquido de 8.
- SO permanece **27/37** entre RÉGUA e VOCAB; chega a **29/37** com produto.

Logo, os exemplos de sockets não sustentam a atribuição causal feita no brief. Evidência: `c1-3/motor_3eixos_v2_12-09.log:84`, `:91`, `:133`; `c1-3/motor_3eixos_produto_12-09.log`.

A mesma aquisição pode contribuir, mas um alias de subunidade não ultrapassa necessariamente a reconciliação que entrega a unidade do bloco. Não reabrir precedência: medir o trajeto completo do alias até a unidade final. A regra está em `src/builder/routing/file_map.py:788`.

**Meta:** 90% exige **226/251** na subunidade e **256/284** na unidade. O vocabulário atual entrega **220/251**; a seleção dirigida por gold citada entrega **222/251**. Esta última é um resultado de uma seleção, não um teto matemático. Faltam respectivamente 6 e 4 acertos líquidos. Nenhum dado demonstra que o desenho proposto os entregará.

Executar em cinco passos, com parada explícita:

1. **Congelar proveniência e denominadores.** Parar se baseline não reproduzir ou houver artefato sem origem identificável.
2. **Produzir candidatos com o orçamento fixo.** Parar ao esgotá-lo; publicar apenas relações com evidência válida.
3. **Medir no motor completo dos sete cursos.** Separar aquisição de retirada de aliases; registrar ganhos e perdas nos três eixos. Não chamar isso de transferência.
4. **Avaliar prospectivamente.** LR como teste inicial; cursos novos como teste de transferência. Abrir os rótulos uma vez.
5. **Decidir pelo resultado.** Abaixo de 226/251 ou 256/284, a meta histórica não foi atingida. Se os resíduos forem competição, ausência válida ou falta de conteúdo, encerrar aquisição como explicação suficiente e tratar a classe demonstrada.

**Próximo passo: congelar os sidecars por entrada e proveniência. O snapshot atual já contradiz a premissa “todo o preservado veio do professor, sem seleção pelo benchmark”.**
