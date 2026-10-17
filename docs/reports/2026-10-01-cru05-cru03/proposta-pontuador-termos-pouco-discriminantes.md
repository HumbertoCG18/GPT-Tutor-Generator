# Proposta: termos pouco discriminantes no pontuador da subunidade (01/10/2026)

**Estado: proposta para decisão. Não é Gate e não há implementação.**

- **Autorizado pelo usuário em 01/10:** "sim para uma proposta; implementação ainda não".
- **Restrições do usuário:**
  - investigar termos pouco discriminantes **entre tópicos** e **entre materiais**, distinguindo as duas frequências;
  - nenhuma exceção para "máquina" ou para o TCC;
  - a correção dos acentos (#89) pode acompanhar o candidato, com os efeitos separados na avaliação;
  - desenvolver nos cinco cursos;
  - CG e FR não viram teste limpo.

## 1. Problema e hipótese

- **Hipótese, não causa demonstrada.** Termos e frases de rótulo pouco discriminantes pesam na decisão da subunidade:
  - **entre tópicos:** frases compartilhadas por vários rótulos da mesma unidade;
  - **entre materiais:** termos presentes em grande parte do corpus do curso.

  O diagnóstico do CRU-05 (`diagnostico-mecanismo-cru05.md`) torna a hipótese plausível, mas não a isola. A contribuição
  da 2ª passada também segue aberta.
- **Caso que motivou** (só ilustra; não é alvo de ajuste). No TCC, a frase "Máquinas de Turing" está no rótulo de 3 dos 5
  tópicos da unidade 02:
  - `maquinas-de-turing`;
  - `variacoes-de-maquinas-de-turing`;
  - `maquinas-de-turing-universais`.

  Com a palavra inteira (#89), a 1ª passada da aula-10 passa a ter `maquinas-de-turing-universais` 5,96 ×
  `maquinas-de-turing` 5,74 × o tópico certo 2,28 (pontuação exata, que é a usada pelo seletor). Na pontuação por
  radical o certo ainda lideraria (18,11 × 17,17), mas essa pontuação não decide a subunidade (`diag_rastro_*.json`).
- **Família já documentada.** Os mecanismos A e B das perdas do VOCAB (`diagnostico_perdas_vl.md`, 27/09) são da mesma
  família:
  - A: migalha de um token decide contra a regra de seção;
  - B: aliases acumulados no vizinho e diluição do bônus de cobertura.

## 2. O que o código já faz (reaproveitar antes de criar)

- **`_score_entry_against_taxonomy_topic`** (`src/builder/timeline/index.py:1820`) tem duas componentes:
  1. **frases exatas** (rótulo 1,0; alias 0,82; slug 0,65) multiplicadas pelo peso do campo: headings 4,4, título 3,8,
     lead 2,8, tags manuais 3,0, corpo 1,1, bruto 0,9;
  2. **sobreposição de tokens** com bônus de cobertura: até 1,4 + 0,22·n quando cobre todos os tokens do tópico.

  As frases dominam a escala. Hoje nenhuma das duas componentes leva em conta a frequência da frase entre tópicos ou
  entre materiais.
- **`generic_tokens` por curso** (A2, `stopwords.unit_generic_tokens_from_units`, `share=0.4`) remove da componente de
  tokens os termos presentes em ≥ 40 % das **unidades**, mais o nome do curso. É uma frequência entre unidades: não pega
  frase compartilhada por tópicos **dentro** da unidade nem termo frequente nos **materiais**, e não age sobre as frases
  exatas.
- **A propagação** (`resolver_apply.py`) já usa uma frequência entre materiais (`df_max` 0,25), mas só para aceitar
  aliases novos. Não age na 1ª passada.
- **O seletor** (`file_map.auto_map_entry_subtopic`, `:174`) decide por vencedor, margem e confiança sobre essa
  pontuação.

## 3. As duas frequências, definidas antes de medir

Calculadas por curso, só a partir do plano e do corpus de materiais (sem gold):

- **F_top(x, u):** número de tópicos da unidade *u* cujo rótulo ou alias contém a frase ou o token *x*, com a mesma
  normalização do pontuador. Frase contida em outra conta para as duas: "Máquinas de Turing" ⊂ "Máquinas de Turing
  Universais".
- **F_mat(x, c, campo):** fração dos materiais do curso *c* em que *x* aparece no campo (headings, título, corpo), pelo
  mesmo casamento que o pontuador usa. É calculada sobre os materiais do próprio build, sem rótulo de ninguém.

As duas são medidas separadamente, e cada uma pode ser alta sem a outra:

- termo de **todos os tópicos e poucos materiais**: o nome do curso já é tratado;
- termo **específico de um tópico e presente em muitos materiais**: tema transversal da disciplina.

## 4. Fases (cada uma com Gate próprio do usuário)

### Fase 0: medição descritiva, sem regra e sem gold

Instrumentar o pontuador **em memória** (wrapper, como em `diag_cru05_mecanismo.py`) para decompor a pontuação do
vencedor e do segundo colocado de cada material na 1ª passada. A contribuição de cada frase e de cada token é anotada
com F_top e F_mat.

- **Cursos:** MF, SO, IA, ES2 e TCC (desenvolvimento), sobre a referência vigente (`replay_base.json`, `e024d396…`).
  - CG e FR não entram nesta fase, para não ampliar a exposição.
- **Saída:**
  - distribuição, por curso, da fração da pontuação do vencedor e da margem que vem de termos com F_top ≥ 2 ou F_mat
    alto;
  - quantos materiais mudariam de ordem entre vencedor e segundo colocado se essa parte fosse retirada. É contagem de
    sensibilidade, **não placar**: sem gold não se sabe se a mudança acerta.
- **Fidelidade:** decisões idênticas à referência em todos os IDs.
- **Parada:** se a fração for pequena e as inversões raras, a hipótese perde força. Registrar e parar.

### Fase 1: desenho congelado, sem avaliação

No máximo **dois** candidatos, com parâmetros fixados por princípio, sem grade. Os limiares já usados no código são
reaproveitados: 0,25 de `df_max` e 0,40 de `share`.

- **(P1) frequência entre tópicos:** uma frase com F_top ≥ 2 numa unidade contribui com peso dividido pelo número de
  tópicos que a contêm. A frase mais específica que a contém (rótulo inteiro) mantém o peso cheio.
- **(P2) frequência entre materiais:** frases e tokens com F_mat acima do limiar no campo deixam de contar na
  componente em que estão.

Tudo fica congelado antes da avaliação, com pré-registro selado:

- regra;
- limiares;
- escopo (só o seletor da subunidade, ou também a rota de unidade, que usa a mesma função com `stem_fallback`);
- braços;
- aceite.

Nenhum ID, curso ou termo nomeado na regra. Casos sintéticos do contrato precedem a avaliação.

### Fase 2: avaliação

- **Braços:**
  - base (`e024d396…`);
  - **A** = só acentos (#89, já medido: −1);
  - **P** = só pontuador;
  - **A+P**.

  Assim, os efeitos dos acentos e do pontuador ficam separados.
- **Replay integral offline** nos três eixos, sobre a referência e comparado por ID. A função é compartilhada, então
  a unidade e o bloco são medidos também.
- **Relato separado por grupo:**
  - **desenvolvimento** (MF, SO, IA, ES2, TCC);
  - **CG/FR:** avaliação adicional, descritiva, com exposição declarada. O gold do CG já foi usado no ciclo VOCAB e na
    adjudicação da régua; o FR teve exposição ao placar e curadoria;
  - **teste independente de generalização:** só cursos novos elegíveis, pelo pré-registro do VOCAB (linha 25). Hoje não
    há nenhum; as 8 N0 são candidatas sujeitas à elegibilidade e aos mínimos.
- **Aceite de integração** (critério vigente da campanha):
  - ganho positivo;
  - zero perda por ID em cada eixo;
  - nenhum curso regride;
  - suíte sem regressão nova contra a base comparável.

  Se o candidato passar nos 7 cursos, isso **não** demonstra generalização. A alegação de generalização fica pendente
  do teste independente.

## 5. Riscos

- **A função é compartilhada.** Mudar o peso de frases pode mexer na unidade (rota com radical) e, por consequência,
  na propagação. Por isso os três eixos são medidos.
- **Tema transversal legítimo.** Em cursos estreitos, o termo frequente é justamente o assunto, como "redes" no FR.
  P2 pode tirar sinal certo. A Fase 0 mostra o tamanho disso antes de desenhar.
- **Exposição.** A hipótese nasceu de um caso do TCC, que é curso de desenvolvimento. Para não encaixar a regra no TCC:
  - candidatos em forma geral;
  - limiares herdados;
  - decisão congelada antes da avaliação.
- **Teto.** A frente mira perdas e fragilidades. Não há caminho demonstrado para os +140 da subunidade primária.

## 6. Decisões pedidas ao usuário

1. **Gate da Fase 0** (medição descritiva, instrumentação só em memória, 5 cursos, sem gold).
2. Depois da Fase 0: escolher P1, P2 ou nenhum, e o escopo (só subunidade, ou também unidade), para o Gate de
   implementação.
3. **Revisão independente** do desenho antes da implementação, se quiser.
