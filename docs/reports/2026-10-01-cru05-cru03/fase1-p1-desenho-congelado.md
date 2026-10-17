# Fase 1: desenho congelado do P1 (frases compartilhadas entre tópicos concorrentes), 01/10/2026

**Autorização do usuário (01/10):** Fase 1 **somente com P1**, como desenho congelado, com um candidato. **Sem
implementação e sem avaliação nesta autorização.** P2 fica suspenso, sem redesenho.

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
- O próprio t conta, então F_top ≥ 1.

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

**E5, penalidades.** No E1, o acerto de frase de A continua contando como `exact_hits`, então a penalidade × 0,72 não se
aplica. P1 não altera `exact_hits`.

**E6, escopo.** Com P1 ligado, a rota de unidade e a pontuação bloco × tópico dão resultados idênticos aos de hoje,
porque não recebem divisor.

**E7, 2ª passada.** Os divisores são calculados sobre a taxonomia recebida na chamada (estendida na 2ª passada).
Exemplo: um alias novo "maquina" (palavra única) em A não está contido em "maquinas" por token, então tem F_top = 1 e
peso cheio.

**Observação do rastro existente (não é alvo).** No candidato do #89, o vencedor ambíguo da aula-10 na 1ª passada é
`maquinas-de-turing-universais`, de rótulo específico (F_top = 1). P1 **não** reduziria esse vencedor e poderia até
aumentar a margem dele. P1 não é desenhado para recuperar a aula-10. Não haverá ajuste para esse caso.

## 5. Avaliação futura (exige Gate próprio; congelada aqui)

1. **Pré-condições:**
   - os exemplos E1–E7 passam como testes;
   - P1 desligado → suíte e replay idênticos à base.
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
