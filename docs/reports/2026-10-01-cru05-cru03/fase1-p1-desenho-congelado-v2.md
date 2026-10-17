# Fase 1: desenho congelado do P1 (frases compartilhadas entre tópicos concorrentes). Versão 2, 02/10/2026

**Versão 2.** Substitui a v1 (`fase1-p1-desenho-congelado.md`, sha256 `b10b3361…`, mantida sem alteração e somente
leitura), com duas precisões do usuário de 02/10. A regra não muda.

1. **F_top ≥ 1 não vale para toda chave.**
   - Uma palavra única com menos de 4 caracteres, como "cpu", não casa nem consigo mesma pelo matcher (o token mínimo é
     de 4), então F_top = 0.
   - **A divisão ocorre somente nos acertos de frase**; não se pré-calculam recíprocos de todas as chaves.
   - Uma chave com F_top = 0 nunca produz acerto, então continua sem contribuição de frase.
   - A componente de tokens fica intacta (`short_vocab`).
   - Exemplo novo: E4b.
2. **E7 reforçado:** uma taxonomia enriquecida em que um alias novo faz um divisor passar de 1 para 2. Assim o teste
   detecta a reutilização indevida dos divisores da 1ª passada.

**Autorização do usuário (01/10):** Fase 1 **somente com P1**, como desenho congelado, com um candidato. P2 fica
suspenso, sem redesenho.

**Em 02/10 (com a v2):** implementação restrita autorizada:

- implementação, testes sintéticos e suíte local;
- P1 **desligado por padrão, por parâmetro explícito**;
- **sem avaliação nos cursos, gold, integração ou commit**;
- com P1 desligado, comparar com o braço correspondente (base sem acentos, ou A com acentos), para não atribuir ao P1
  uma diferença da normalização.

Base: `relatorio-fase0-pontuador.md` (sensibilidade demonstrada; benefício ainda desconhecido) e
`proposta-pontuador-termos-pouco-discriminantes.md`. Este documento é selado por sha256 e só muda com nova versão
explícita.

## 1. Hipótese

Frases de rótulo, alias ou slug compartilhadas por vários tópicos concorrentes somam peso cheio para cada tópico que as
contém. Assim, um tópico de rótulo curto ganha vantagem sobre os tópicos que nomeiam a mesma coisa de forma mais
específica.

O exemplo é "Máquinas de Turing" contido em "Variações de Máquinas de Turing" e em "Máquinas de Turing Universais".

**Hipótese:** reduzir essa vantagem, preservando o peso das frases específicas, reduz uma fragilidade do seletor.

**Não é** caminho demonstrado para os +140 da subunidade primária.

## 2. Escopo

- **Dentro:** o seletor da subunidade, `routing/file_map.auto_map_entry_subtopic` (`file_map.py:199`), em todas as suas
  chamadas: 1ª passada e repontuação da 2ª passada (`resolver_apply.propagar_vocabulario_por_headings`).
- **Fora, inalterados:**
  - a rota de unidade (`file_map.py:539`, `stem_fallback=True`);
  - a pontuação bloco × tópico da timeline (`timeline/index.py:1998`);
  - a regra de seção;
  - a guarda do título;
  - a propagação (aliases e partes de rótulo);
  - os limiares e `generic_tokens`;
  - a componente de tokens (sobreposição e cobertura).
- **Só a componente de frases** da pontuação muda. A contagem `exact_hits` e, portanto, as penalidades não mudam.

## 3. Regra (fixa, sem parâmetro livre)

**Tópicos concorrentes:** C = o `topic_index` que o seletor usa naquela chamada. São os tópicos da unidade vencedora,
ou todos os tópicos se não houver unidade, como hoje.

**Divisor de uma frase:** para cada tópico t ∈ C, cada chave de frase k de t (rótulo, alias ou slug, normalizada e
deduplicada como hoje no pontuador) recebe

> **F_top(k, C)** = número de tópicos t' ∈ C com alguma chave q tal que `_matches_normalized_phrase(q, k, False)` é
> verdadeiro.

- O casamento é o do próprio pontuador: frase de várias palavras por substring; palavra única por token de ≥ 4
  caracteres.
- O próprio t conta. Por isso **F_top ≥ 1 vale para toda chave que tem acerto**.
  - Um acerto de frase de várias palavras implica que a chave contém a si mesma.
  - Um acerto de palavra única implica que ela tem ≥ 4 caracteres e, portanto, casa consigo mesma.
- Uma palavra única com < 4 caracteres tem F_top = 0 e nunca acerta (v2).
- **A divisão é aplicada só no acerto.** As contagens podem ser calculadas antes, mas não há recíproco pré-calculado nem
  divisão em chave sem acerto.

**Contribuição de cada acerto de frase**, por campo:

- hoje: `peso_do_campo × fator`;
- **com P1:** `peso_do_campo × fator / F_top(k, C)`.

Quando F_top = 1 (frase específica), a contribuição é idêntica à de hoje.

**Ordem de soma:** a mesma de hoje (campos por fora, frases por dentro). P1 desligado tem de ser **idêntico byte a
byte** ao comportamento atual.

**Liga e desliga:**

- P1 precisa de um seletor explícito para os braços da avaliação, desligado por padrão até a decisão de integração.
- A forma (flag de matéria ou parâmetro do seletor) fica para o Gate de implementação. A regra acima não muda com ela.

## 4. Exemplos sintéticos (contrato; calculados à mão pela regra)

Valem para todos os exemplos:

- os tópicos têm `kind = "topic"`, nenhum alias e `generic_tokens = ["zzzz"]` (controle; evita o conjunto padrão);
- o slug é o rótulo slugificado, e por isso é deduplicado na chave do rótulo;
- os sinais têm só os campos citados, **já normalizados** como os produz `collect_entry_unit_signals`; os demais ficam
  vazios.

**Conferência:** a coluna "hoje" de E1, E2 e E4 foi conferida com o pontuador real de `bf46d51f`, chamado sobre esses
tópicos e sinais sintéticos (`confere_exemplos_p1.py`, nesta pasta, 02/10). Os resultados são iguais aos da tabela. A
coluna P1 é aritmética da regra, sem implementação.

**Unidade U1:** A "Máquinas de Turing"; B "Variações de Máquinas de Turing"; C "Máquinas de Turing Universais".
Divisores: F_top("maquinas de turing") = 3; os rótulos de B e de C têm F_top = 1.

| exemplo | sinais | hoje (A / B / C) → decisão | P1 (A / B / C) → decisão | propriedade |
|---|---|---|---|---|
| **E1** | título "Máquinas de Turing" | 5,64 / 0,9072 / 0,9072 → **A decidido** (margem rel. 0,839) | 3,1067 / 0,9072 / 0,9072 → **A decidido** (0,708) | frase compartilhada sozinha ainda decide; não esvazia |
| **E2** | título "Máquinas de Turing"; heading "Variações de Máquinas de Turing" | 10,04 / 6,46 / 0,9072 → **A decidido** (0,357) | 4,5733 / 6,46 / 0,9072 → **B decidido** (0,292) | a frase específica deixa de perder para a compartilhada contida nela |

Conta do E2:

- **A, hoje:** frase em título (3,8) e heading (4,4, por substring) = 8,2, mais cobertura 2/2 = 1,84.
- **A com P1:** 8,2 / 3 + 1,84.
- **B:** frase no heading = 4,4, mais cobertura 3/3 = 2,06.
- **C:** sem frase; cobertura 2/3 = 1,26, × 0,72 (sem acerto exato).

**E3, identidade.** Unidade com "Swapping", "Memória Virtual" e "Paginação", sem frase contida em outra. Todas as
pontuações com P1 ligado são **idênticas** às de hoje, para qualquer sinal.

**E4, palavra única.** X "Escalonamento" e Y "Algoritmos de Escalonamento"; F_top("escalonamento") = 2.

- Heading "Escalonamento": X fica com 4,4 / 2 + 0,9 = 3,1 (hoje 5,3).
- Y fica com 0,25 × 0,72 × 0,68 = 0,1224 nos dois casos.
- X decide nos dois.

**E4b, palavra única curta (v2).** Tópicos X "CPU" e Y "Memória", com `short_vocab = ["cpu"]`; heading "CPU".

- "cpu" não casa nem consigo mesma: F_top = 0 e nenhum acerto de frase.
- X = 0,9 (token curto em campo forte) × 0,72 × 0,68 = **0,4406**, com P1 ligado e desligado.
- Y = 0.
- **Nenhuma divisão e nenhum erro.** P1 é idêntico a hoje.

**E5, penalidades.** No E1, o acerto de frase de A continua contando como `exact_hits`, então a penalidade × 0,72 não se
aplica. P1 não altera `exact_hits`.

**E6, escopo.** Com P1 ligado, a rota de unidade e a pontuação bloco × tópico dão resultados idênticos aos de hoje,
porque não recebem divisor.

**E7, 2ª passada (reforçado na v2).** Os divisores são calculados sobre a taxonomia **recebida em cada chamada**
(estendida na 2ª passada).

- **T1 (original):** A "Swapping" e B "Paginação"; heading "Paginação". F_top("paginacao") = 1, e B = 4,4 + 0,9 =
  **5,3**, com P1 ligado e desligado.
- **T2 (enriquecida):** A ganha o alias "Paginação sob demanda", que contém o token "paginacao". F_top("paginacao")
  passa de **1 para 2**.
  - Com P1 ligado: B = 4,4 / 2 + 0,9 = **3,1**.
  - Com P1 desligado: 5,3.
  - A = 0,1224 nos dois casos (o alias de A não acerta o heading).
- Uma implementação que reaproveitasse os divisores de T1 daria 5,3 para B com P1 ligado em T2. O teste detecta isso.
- Complemento (v1): um alias de palavra única "maquina" não está contido em "maquinas" por token, então tem F_top = 1.

**Conferência v2:** a coluna "hoje" de E4b, T1 e T2 foi conferida com o pontuador real de `bf46d51f`: E4b [0,4406;
0,0], T1 [0,0; 5,3], T2 [0,1224; 5,3]. O matcher confirma que 'cpu' não casa 'cpu' e que 'paginacao sob demanda' casa
'paginacao' (`confere_exemplos_p1.py`, 02/10).

**Observação do rastro existente (não é alvo).** No candidato do #89, o vencedor ambíguo da aula-10 na 1ª passada é
`maquinas-de-turing-universais`, de rótulo específico (F_top = 1). P1 **não** reduziria esse vencedor e poderia até
aumentar a margem dele. P1 não é desenhado para recuperar a aula-10. Não haverá ajuste para esse caso.

## 5. Avaliação futura (exige Gate próprio; congelada aqui)

1. **Pré-condições:**
   - os exemplos E1–E7 e E4b passam como testes;
   - P1 desligado → suíte e replay idênticos por ID ao **braço correspondente**: base (`e024d396…`) numa árvore sem os
     acentos, ou A numa árvore com os acentos (v2).
2. **Braços:**
   - base (`replay_base.json`, `e024d396…`, que o braço base tem de reproduzir por ID);
   - A = acentos (#89);
   - **P1**;
   - **A+P1**.

   P1 é comparado com a base, e A+P1 com a base e com A. Assim os efeitos ficam separados.
3. **Replay integral offline** nos 7 cursos, comparado por ID nos três eixos.
   - **Garantia de escopo:** com P1, bloco e unidade são idênticos por ID ao braço sem P1 correspondente. Qualquer
     diferença é falha de escopo.
4. **Relato separado por grupo:**
   - desenvolvimento (MF, SO, IA, ES2, TCC);
   - CG/FR: descritivo, com exposição declarada, não independente;
   - teste independente: só cursos novos elegíveis (hoje nenhum).

   Passar nos 7 cursos **não** demonstra generalização.
5. **Aceite de integração** (critério vigente da campanha), para P1 e para A+P1:
   - ganho positivo na subunidade primária;
   - **zero perda por ID** em cada eixo;
   - nenhum curso regride;
   - suíte sem regressão nova contra a base comparável.
6. **Sem ajuste:** uma avaliação. Se o aceite falhar, registrar e parar; não há variante de divisor, limiar ou escopo.
   Gold só na pontuação da avaliação autorizada, nunca no desenho.

## 6. Fora deste desenho

- P2 (frequência entre materiais), suspenso.
- Mudanças em tokens ou cobertura.
- Recuperação de casos específicos.
- Os +140.
