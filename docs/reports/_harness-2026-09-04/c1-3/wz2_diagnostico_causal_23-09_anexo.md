# W-Z2 — anexo de tabelas geradas (diagnóstico causal, 23/09)

Declaração `2a448326e925453a…`; base congelada `f941ac331a5e676d…`; DP `fb8dc86378af6a91…`; índice documental `b7e5c26959fc33a3…`. Fidelidade: base = W-Z por ID; índice W-U reproduzido {'sha_reproduzido': 'c17786ef89c2e59ab0ee3e786bb03e8d8713e27c8affc9289e39a609aafb3d0e', 'relacoes': 11663, 'igual_ao_wu': True}. DP recomputado = gravado: {'MF': [17, 17], 'SO': [17, 17], 'IA': [15, 15], 'ES2': [11, 11], 'TCC': [22, 22], 'CG': [22, 22], 'FR': [21, 21]}. Tempo 7.7 s.

## A1. Placar dos 3 modos (bloco, unidade, sub primária/aceita)

| modo | curso | bloco | unidade | sub prim | sub aceita |
|---|---|---|---|---|---|
| base | MF | 60/66 | 63/66 | 25/58 | 29/58 |
| base | SO | 36/39 | 30/37 | 7/15 | 8/15 |
| base | IA | 41/42 | 39/42 | 4/39 | 5/39 |
| base | ES2 | 27/28 | 26/28 | 7/28 | 8/28 |
| base | TCC | 26/27 | 17/18 | 7/11 | 9/11 |
| base | CG | 33/35 | 73/93 | 30/82 | 43/82 |
| base | FR | 0/0 | 0/0 | 6/18 | 7/18 |
| base | TOTAL | 223/237 | 248/284 | 86/251 | 109/251 |
| oraculo_unidade | MF | 60/66 | 66/66 | 25/58 | 29/58 |
| oraculo_unidade | SO | 36/39 | 37/37 | 7/15 | 8/15 |
| oraculo_unidade | IA | 41/42 | 42/42 | 4/39 | 5/39 |
| oraculo_unidade | ES2 | 27/28 | 28/28 | 9/28 | 9/28 |
| oraculo_unidade | TCC | 26/27 | 18/18 | 7/11 | 9/11 |
| oraculo_unidade | CG | 33/35 | 92/93 | 34/82 | 49/82 |
| oraculo_unidade | FR | 0/0 | 0/0 | 6/18 | 7/18 |
| oraculo_unidade | TOTAL | 223/237 | 283/284 | 92/251 | 116/251 |
| oraculo_bloco | MF | 60/66 | 63/66 | 25/58 | 29/58 |
| oraculo_bloco | SO | 36/39 | 30/37 | 7/15 | 8/15 |
| oraculo_bloco | IA | 41/42 | 41/42 | 4/39 | 5/39 |
| oraculo_bloco | ES2 | 27/28 | 27/28 | 9/28 | 9/28 |
| oraculo_bloco | TCC | 26/27 | 18/18 | 7/11 | 9/11 |
| oraculo_bloco | CG | 33/35 | 73/93 | 30/82 | 43/82 |
| oraculo_bloco | FR | 0/0 | 0/0 | 6/18 | 7/18 |
| oraculo_bloco | TOTAL | 223/237 | 252/284 | 88/251 | 110/251 |

Mudanças por ID contra a base:

- oraculo_unidade · unidade: +35 / −0; perdas []
- oraculo_unidade · sub_primaria: +8 / −2; perdas ['CG|bezier-py', 'CG|bezier-python']
- oraculo_unidade · sub_aceita: +9 / −2; perdas ['CG|bezier-python', 'ES2|revisaoarquiteturapadroes']
- oraculo_bloco · unidade: +4 / −0; perdas []
- oraculo_bloco · sub_primaria: +2 / −0; perdas []
- oraculo_bloco · sub_aceita: +2 / −1; perdas ['ES2|revisaoarquiteturapadroes']

## A2. Erros de bloco (motor temporal)

| curso | id | previsto → gold | método | banda | flag | provedor | gold na janela |
|---|---|---|---|---|---|---|---|
| MF | `revisao` | bloco-04 → bloco-03 | disamb | alta | False | labels | False |
| MF | `introducao` | bloco-01 → bloco-02 | disamb | baixa | True | labels | False |
| MF | `intro` | bloco-05 → bloco-06 | janela-1 | media | False | card | False |
| MF | `exerciciosdafny2` | bloco-11 → bloco-13 | disamb | alta | False | labels | False |
| MF | `introducao-zip` | bloco-10 → bloco-12 | janela-1 | media | True | card | False |
| MF | `terminacao` | bloco-11 → bloco-12 | disamb | baixa | True | labels | False |
| SO | `definicao-e-historico` |  → bloco-03 | None | None | None | None | False |
| SO | `laminas-cs-4244-internet-programming-sockets-programming` | bloco-06 → bloco-09 | disamb | baixa | True | card | False |
| SO | `laminas-sockets-material-alternativo-em-pt` | bloco-06 → bloco-09 | disamb | baixa | True | card | False |
| IA | `analise-exploratoria-de-dados-exemplo-1` | bloco-05 → bloco-04 | disamb | media | True | labels | False |
| ES2 | `azure` | bloco-08 → bloco-09 | janela-1 | media | True | card | False |
| TCC | `t1-enunciado` |  → bloco-04 | None | None | None | None | False |
| CG | `basico3d-cpp` | bloco-05 → bloco-15 | disamb | baixa | True | topic | True |
| CG | `basico3d-py-zip` | bloco-05 → bloco-15 | disamb | baixa | True | topic | True |

## A3. Blocos do DP posicional (classe × mecanismo × gold por bloco)

| curso | bloco | classe | mecanismo | cabeçalho | posição | DP | gold do bloco | correto | rótulo |
|---|---|---|---|---|---|---|---|---|---|
| MF | bloco-01 | sem_sinal | dp_puro | False | borda | ade-01-metodos-formais | ade-01-metodos-formais | True | apresentacao da disciplina aula |
| MF | bloco-02 | sinal_proprio_unico | dp_puro | True | interior | ade-01-metodos-formais | ade-01-metodos-formais | True | introducao a metodos formais aula |
| MF | bloco-03 | sinal_proprio_empatado | dp_puro | False | interior | ade-01-metodos-formais | ade-01-metodos-formais | True | revisao de logica de predicados exercicios aula |
| MF | bloco-04 | sinal_proprio_unico | dp_puro | False | interior | ade-01-metodos-formais | ade-01-metodos-formais | True | conjuntos indutivos e equacoes recursivas aula / exercicios  |
| MF | bloco-05 | sem_sinal | dp_puro | False | interior | ade-01-metodos-formais | ade-01-metodos-formais | True | provas por inducao aula / provas por inducao listas e arvore |
| MF | bloco-06 | sinal_proprio_unico | dp_puro | False | interior | ade-01-metodos-formais | ade-01-metodos-formais | True | prova interativa de teoremas isabelle aula / prova interativ |
| MF | bloco-07 | sem_sinal | dp_puro | False | interior | ade-01-metodos-formais | ade-01-metodos-formais | True | exercicios de revisao aula |
| MF | bloco-08 | sem_sinal | dp_puro | False | fronteira | ade-01-metodos-formais | — | None | suspensao de aulas aula |
| MF | bloco-10 | sinal_proprio_unico | dp_puro | False | fronteira | rificacao-de-programas | rificacao-de-programas | True | logica de hoare aula / logica de hoare aula / exercicios aul |
| MF | bloco-12 | sem_sinal | dp_puro | False | interior | rificacao-de-programas | rificacao-de-programas | True | terminacao introducao ao dafny aula |
| MF | bloco-13 | sinal_proprio_empatado | dp_puro | True | interior | rificacao-de-programas | rificacao-de-programas | True | logica de programas introducao ao dafny aula / logica de pro |
| MF | bloco-14 | sem_sinal | dp_puro | False | interior | rificacao-de-programas | — | None | se day evento academico |
| MF | bloco-15 | sinal_proprio_unico | dp_puro | False | fronteira | rificacao-de-programas | rificacao-de-programas | True | logica de programas orientacao a objetos dafny ghosts autoco |
| MF | bloco-16 | sinal_proprio_unico | dp_puro | False | fronteira | verificacao-de-modelos | verificacao-de-modelos | True | verificacao de modelos logica temporal aula / verificacao de |
| MF | bloco-17 | sem_sinal | dp_puro | False | interior | verificacao-de-modelos | — | None | suspensao jogo copa do mundo aula |
| MF | bloco-18 | sinal_proprio_unico | dp_puro | True | interior | verificacao-de-modelos | verificacao-de-modelos | True | verificacao de modelos ferramenta aula |
| MF | bloco-19 | sem_sinal | dp_puro | False | borda | verificacao-de-modelos | — | None | exercicios de revisao aula |
| SO | bloco-01 | sem_sinal | dp_puro | False | borda | -sistemas-operacionais | -sistemas-operacionais | True | apresentacao da disciplina e introducao aula |
| SO | bloco-02 | sem_sinal | dp_puro | False | interior | -sistemas-operacionais | -sistemas-operacionais | True | introducao aula |
| SO | bloco-03 | sinal_proprio_unico | dp_puro | False | fronteira | -sistemas-operacionais | -sistemas-operacionais | True | historico e evolucao dos sistemas operacionais aula / estrut |
| SO | bloco-04 | sinal_proprio_unico | dp_puro | True | fronteira | erencia-do-processador | erencia-do-processador | True | gerencia do processador processos chamadas de sistema escalo |
| SO | bloco-05 | sem_sinal | dp_puro | False | interior | erencia-do-processador | — | None | feriado aula |
| SO | bloco-06 | sinal_proprio_unico | dp_puro | True | interior | erencia-do-processador | unidade-04-deadlock | False | gerencia do processador sincronizacao e deadlock aula / gere |
| SO | bloco-07 | sinal_proprio_unico | dp_puro | True | interior | erencia-do-processador | — | None | especificacao tp1 / especificacao tp1 |
| SO | bloco-08 | sem_sinal | dp_puro | False | fronteira | erencia-do-processador | — | None | feriado aula |
| SO | bloco-09 | sinal_proprio_unico | dp_puro | False | fronteira | rogramacao-concorrente | rogramacao-concorrente | True | comunicacao entre processos pipes filas aula / exercicios au |
| SO | bloco-10 | sem_sinal | dp_puro | False | interior | rogramacao-concorrente | — | None | duvidas prova aula |
| SO | bloco-11 | sem_sinal | dp_puro | False | fronteira | rogramacao-concorrente | — | None | duvidas tp1 duvidas p1 aula |
| SO | bloco-13 | sinal_proprio_unico | dp_puro | False | fronteira | 05-gerencia-de-memoria | 05-gerencia-de-memoria | True | gerencia de memoria memoria virtual paginacao aula |
| SO | bloco-16 | sinal_proprio_unico | dp_puro | False | interior | 05-gerencia-de-memoria | 05-gerencia-de-memoria | True | gerencia de memoria memoria virtual paginacao aula / gerenci |
| SO | bloco-17 | sem_sinal | dp_puro | False | fronteira | 05-gerencia-de-memoria | — | None | feriado aula |
| SO | bloco-18 | sinal_proprio_unico | dp_puro | True | fronteira | cia-de-entrada-e-saida | cia-de-entrada-e-saida | True | gerencia de e s |
| SO | bloco-19 | sinal_proprio_unico | dp_puro | True | fronteira | cia-de-entrada-e-saida | cia-de-entrada-e-saida | True | gerencia de e s aula |
| SO | bloco-20 | sinal_proprio_unico | ancora | True | borda | 6-gerencia-de-arquivos | 6-gerencia-de-arquivos | True | gerencia de arquivos aula / gerencia de arquivos aula / gere |
| IA | bloco-01 | sinal_proprio_empatado | desvio | False | borda | aprendizado-de-maquina | dizagem-01-visao-geral | False | plano de ensino conteudo programatico cronograma forma e dat |
| IA | bloco-02 | sem_sinal | desvio | False | interior | aprendizado-de-maquina | dizagem-01-visao-geral | False | visao geral da ia aula |
| IA | bloco-03 | sem_sinal | desvio | False | interior | aprendizado-de-maquina | aprendizado-de-maquina | True | ml introducao a ml aula |
| IA | bloco-04 | sinal_proprio_unico | desvio | False | interior | aprendizado-de-maquina | aprendizado-de-maquina | True | ml tipos de dados e preparacao de dados aula / ml preparacao |
| IA | bloco-05 | sem_sinal | desvio | False | interior | aprendizado-de-maquina | aprendizado-de-maquina | True | ml abordagem supervisionada k nn aula / ml abordagem supervi |
| IA | bloco-06 | sem_sinal | desvio | False | interior | aprendizado-de-maquina | aprendizado-de-maquina | True | suspensao de aulas aula |
| IA | bloco-07 | sinal_proprio_unico | desvio | False | fronteira | aprendizado-de-maquina | aprendizado-de-maquina | True | ml abordagem nao supervisionada k means exercicios aula / ml |
| IA | bloco-08 | sem_sinal | dp_puro | False | fronteira | dizagem-01-visao-geral | — | None | duvidas para t1 aula |
| IA | bloco-11 | sem_sinal | dp_puro | False | fronteira | dizagem-01-visao-geral | — | None | exercicios gerais aula |
| IA | bloco-13 | sinal_proprio_unico | dp_puro | False | fronteira | 2-solucao-de-problemas | 2-solucao-de-problemas | True | correcao p1 e algoritmos de busca aula / algoritmos de busca |
| IA | bloco-14 | sem_sinal | dp_puro | False | interior | 2-solucao-de-problemas | — | None | es day evento academico |
| IA | bloco-15 | sinal_proprio_unico | dp_puro | False | interior | 2-solucao-de-problemas | 2-solucao-de-problemas | True | algoritmos de busca aula / algoritmos de busca aula / algori |
| IA | bloco-16 | sinal_proprio_unico | dp_puro | False | fronteira | 2-solucao-de-problemas | 2-solucao-de-problemas | True | correcao da p1 duvidas t2 aula / algoritmos de busca exercic |
| IA | bloco-17 | sinal_proprio_unico | dp_puro | False | fronteira | ntacao-de-conhecimento | ntacao-de-conhecimento | True | introducao a agentes e planejamento aula / introducao a agen |
| IA | bloco-18 | sem_sinal | dp_puro | False | borda | ntacao-de-conhecimento | — | None | suspensao de atividades feriado |
| ES2 | bloco-01 | sinal_proprio_unico | dp_puro | False | borda | rquitetura-de-software | rquitetura-de-software | True | apresentacao da disciplina revisao de conceitos aula / arqui |
| ES2 | bloco-02 | sinal_proprio_empatado | dp_puro | False | interior | rquitetura-de-software | rquitetura-de-software | True | microsservicos no spring introducao aula |
| ES2 | bloco-03 | sem_sinal | dp_puro | False | interior | rquitetura-de-software | — | None | feriado aula |
| ES2 | bloco-04 | sem_sinal | dp_puro | False | interior | rquitetura-de-software | rquitetura-de-software | True | microservicos no spring discovery aula / microservicos no sp |
| ES2 | bloco-05 | sem_sinal | dp_puro | False | interior | rquitetura-de-software | — | None | feriado aula |
| ES2 | bloco-07 | sem_sinal | dp_puro | False | fronteira | rquitetura-de-software | ento-e-operacao-devops | False | microservicos no spring circuit breaker aula |
| ES2 | bloco-08 | sinal_proprio_unico | dp_puro | False | fronteira | ento-e-operacao-devops | ento-e-operacao-devops | True | implantacao de microservicos conteineres aula / implantacao  |
| ES2 | bloco-09 | sem_sinal | dp_puro | False | interior | ento-e-operacao-devops | ento-e-operacao-devops | True | comunicacao assincrona aula |
| ES2 | bloco-10 | sem_sinal | dp_puro | False | interior | ento-e-operacao-devops | ento-e-operacao-devops | True | autenticacao e autorizacao aula |
| ES2 | bloco-11 | sem_sinal | dp_puro | False | interior | ento-e-operacao-devops | — | None | suspensao jogo copa do mundo aula |
| ES2 | bloco-12 | sinal_proprio_unico | dp_puro | True | borda | ento-e-operacao-devops | ento-e-operacao-devops | True | devops exercicios aula |
| TCC | bloco-01 | sinal_proprio_unico | dp_puro | True | borda | s-e-funcoes-recursivas | s-e-funcoes-recursivas | True | apresentacao |
| TCC | bloco-02 | sinal_proprio_unico | dp_puro | False | interior | s-e-funcoes-recursivas | s-e-funcoes-recursivas | True | conjuntos enumeraveis e nao enumeraveis |
| TCC | bloco-03 | sinal_proprio_unico | dp_puro | False | interior | s-e-funcoes-recursivas | s-e-funcoes-recursivas | True | funcoes recursivas primitivas / funcoes recursivas parciais  |
| TCC | bloco-05 | contra_argmax | dp_puro | False | fronteira | s-e-funcoes-recursivas | — | None | revisao alfabeto cadeia linguagem hierarquia de chomsky lema |
| TCC | bloco-06 | sinal_proprio_unico | dp_puro | False | fronteira | turing-computabilidade | turing-computabilidade | True | maquinas de turing e linguagens recursivamente enumeraveis a |
| TCC | bloco-07 | sem_sinal | dp_puro | False | interior | turing-computabilidade | — | None | feriado aula |
| TCC | bloco-08 | sinal_proprio_unico | dp_puro | False | interior | turing-computabilidade | turing-computabilidade | True | variacoes de maquias de turing aula |
| TCC | bloco-09 | sinal_proprio_unico | dp_puro | False | interior | turing-computabilidade | turing-computabilidade | True | linguagens reconheciveis e linguagens decidiveis |
| TCC | bloco-10 | sem_sinal | dp_puro | False | fronteira | turing-computabilidade | problemas-indecidiveis | False | halting problem aula |
| TCC | bloco-11 | sinal_proprio_unico | dp_puro | False | fronteira | problemas-indecidiveis | problemas-indecidiveis | True | entscheidungsproblem aula |
| TCC | bloco-12 | sem_sinal | dp_puro | False | interior | problemas-indecidiveis | problemas-indecidiveis | True | theorema de rice aula |
| TCC | bloco-13 | sinal_proprio_unico | dp_puro | False | interior | problemas-indecidiveis | problemas-indecidiveis | True | problema da correspondencia de post aula |
| TCC | bloco-14 | sinal_proprio_unico | dp_puro | False | interior | problemas-indecidiveis | problemas-indecidiveis | True | teoremas de godel aula |
| TCC | bloco-15 | sem_sinal | dp_puro | False | interior | problemas-indecidiveis | — | None | feriado aula |
| TCC | bloco-16 | sinal_proprio_unico | dp_puro | False | interior | problemas-indecidiveis | — | None | revisao para prova p1 aula |
| TCC | bloco-18 | sinal_proprio_unico | dp_puro | False | fronteira | problemas-indecidiveis | — | None | correcao prova p1 aula |
| TCC | bloco-19 | sinal_proprio_unico | dp_puro | False | fronteira | oblemas-computacionais | oblemas-computacionais | True | classes de problemas / complexidade de tempo classes p e np  |
| TCC | bloco-20 | sem_sinal | dp_puro | False | interior | oblemas-computacionais | — | None | se day evento academico |
| TCC | bloco-21 | sinal_proprio_empatado | dp_puro | True | interior | oblemas-computacionais | — | None | oficina de problemas entrega t2 aula |
| TCC | bloco-22 | sinal_proprio_unico | dp_puro | False | interior | oblemas-computacionais | oblemas-computacionais | True | theorema de cook levin aula |
| TCC | bloco-30 | contra_argmax | dp_puro | False | interior | oblemas-computacionais | — | None | revisao para prova p2 aula |
| TCC | bloco-33 | contra_argmax | dp_puro | False | borda | oblemas-computacionais | — | None | correcao da prova p2 e prova ps aula |
| CG | bloco-01 | sinal_proprio_unico | dp_puro | False | borda | -processamento-grafico | — | None | apresentacao da disciplina e origens da cg aula |
| CG | bloco-02 | sem_sinal | dp_puro | False | fronteira | -processamento-grafico | — | None | introducao a opengl aula |
| CG | bloco-03 | sinal_proprio_unico | dp_puro | True | fronteira | undamentos-matematicos | — | None | fundamentos matematicos para cg pi aula / fundamentos matema |
| CG | bloco-04 | sinal_proprio_unico | dp_puro | False | interior | undamentos-matematicos | — | None | algoritmos de deteccao de colisao aula |
| CG | bloco-05 | sinal_proprio_unico | dp_puro | False | fronteira | undamentos-matematicos | — | None | geometria computacional aula |
| CG | bloco-06 | sinal_proprio_unico | desvio | True | fronteira | sso-de-visualizacao-2d | — | None | processo de visualizacao 2d instanciamento aula / processo d |
| CG | bloco-07 | sinal_proprio_unico | dp_puro | True | fronteira | -e-visao-computacional | — | None | processamento de imagens e visao computacional aula / proces |
| CG | bloco-08 | sinal_proprio_unico | dp_puro | False | fronteira | sso-de-visualizacao-3d | — | None | morfologia matematica aula / aula de exercicios aula / aula  |
| CG | bloco-09 | sem_sinal | dp_puro | False | interior | sso-de-visualizacao-3d | — | None | aula de duvidas aula |
| CG | bloco-11 | sem_sinal | dp_puro | False | fronteira | sso-de-visualizacao-3d | — | None | aula de duvidas aula |
| CG | bloco-13 | sinal_proprio_unico | ancora | False | fronteira | e-modelagem-de-objetos | — | None | curvas parametricas aula / curvas parametricas aula |
| CG | bloco-15 | sinal_proprio_unico | ancora | True | fronteira | e-modelagem-de-objetos | — | None | modelagem geometrica aula |
| CG | bloco-16 | sem_sinal | dp_puro | False | fronteira | sso-de-visualizacao-3d | — | None | semana academica evento academico |
| CG | bloco-17 | sem_sinal | dp_puro | False | interior | sso-de-visualizacao-3d | — | None | semana academica evento academico |
| CG | bloco-18 | sinal_proprio_empatado | dp_puro | True | interior | sso-de-visualizacao-3d | — | None | visualizacao 3d projecao aula |
| CG | bloco-19 | sinal_proprio_empatado | dp_puro | True | interior | sso-de-visualizacao-3d | — | None | visualizacao 3d observador aula |
| CG | bloco-20 | sinal_proprio_unico | dp_puro | False | fronteira | sso-de-visualizacao-3d | — | None | remocao de elementos ocultos aula / remocao de elementos ocu |
| CG | bloco-21 | sinal_proprio_unico | dp_puro | False | fronteira | de-imagens-realisticas | — | None | iluminacao aula / aula de exercicios aula |
| CG | bloco-22 | sem_sinal | dp_puro | False | interior | de-imagens-realisticas | — | None | aula de duvidas aula |
| CG | bloco-25 | sem_sinal | dp_puro | False | interior | de-imagens-realisticas | — | None | aula de duvidas aula |
| CG | bloco-27 | sem_sinal | dp_puro | False | interior | de-imagens-realisticas | — | None | aula de duvidas aula |
| CG | bloco-29 | sem_sinal | dp_puro | False | borda | de-imagens-realisticas | — | None | aula |
| FR | bloco-01 | sem_sinal | dp_puro | False | borda | -redes-de-computadores | — | None | apresentacao da disciplina aula |
| FR | bloco-02 | sinal_proprio_empatado | dp_puro | False | fronteira | -redes-de-computadores | — | None | arquitetura de protocolos modelos de referencia osi e tcp ip |
| FR | bloco-03 | sinal_proprio_unico | dp_puro | False | fronteira | -02-nivel-de-aplicacao | — | None | protocolos de aplicacao dhcp aula / protocolos de aplicacao  |
| FR | bloco-04 | sem_sinal | dp_puro | False | interior | -02-nivel-de-aplicacao | — | None | aula magna da escola politecnica evento academico |
| FR | bloco-05 | sinal_proprio_unico | dp_puro | False | fronteira | -02-nivel-de-aplicacao | — | None | protocolos de aplicacao dns aula / protocolos de aplicacao s |
| FR | bloco-06 | sinal_proprio_unico | dp_puro | False | fronteira | 03-nivel-de-transporte | — | None | camada de transporte udp tcp aula / camada de transporte udp |
| FR | bloco-07 | sinal_proprio_unico | dp_puro | False | fronteira | idade-04-nivel-de-rede | — | None | camada de rede enderecamento ip aula |
| FR | bloco-08 | sinal_proprio_unico | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | protocolo ipv4 aula |
| FR | bloco-09 | sinal_proprio_unico | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | icmpv4 aula |
| FR | bloco-10 | sem_sinal | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | duvidas da p1 aula |
| FR | bloco-12 | sinal_proprio_unico | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | protocolos ipv6 e icmpv6 aula |
| FR | bloco-13 | sinal_proprio_unico | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | introducao ao roteamento ip aula |
| FR | bloco-14 | sinal_proprio_unico | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | tabela de roteamento aula |
| FR | bloco-15 | sinal_proprio_unico | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | algoritmos de roteamento aula |
| FR | bloco-16 | sem_sinal | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | feriado aula |
| FR | bloco-17 | sinal_proprio_unico | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | protocolos de roteamento aula |
| FR | bloco-18 | sem_sinal | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | semana academica da pucrs evento academico |
| FR | bloco-19 | sem_sinal | dp_puro | False | interior | idade-04-nivel-de-rede | — | None | semana academica da pucrs evento academico |
| FR | bloco-20 | sinal_proprio_empatado | dp_puro | False | fronteira | idade-04-nivel-de-rede | — | None | camada de enlace servicos e enquadramento aula / camada de e |
| FR | bloco-21 | sinal_proprio_unico | dp_puro | False | fronteira | ade-05-nivel-de-enlace | — | None | ethernet comutada stp vlan lacp etc aula |
| FR | bloco-22 | contra_argmax | dp_puro | False | borda | ade-05-nivel-de-enlace | — | None | camada fisica e raw sockets aula / exercicios aula |

## A4. Erros de unidade (36) com mecanismo, fonte da unidade do bloco e proveniência do gold

| curso | id | gold → previsto | classe | mecanismo | fonte da unidade do bloco | bloco (gold de bloco) | proveniência | bruto | seção |
|---|---|---|---|---|---|---|---|---|---|
| CG | `animacao-v2` | macoes-geometricas → de-visualizacao-2d | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sinal_proprio_unico | bloco-06 (—) | material_gt:ruling_usuario | cessamento-grafico gated |  |
| CG | `exemplodemanipulacaodeimagens` | isao-computacional → mentos-matematicos | herdada_do_bloco_certo_mas_gold_diverge | herdada | sinal_proprio_unico | bloco-03 (—) | material_gt:ruling_usuario | macoes-geometricas |  |
| CG | `instanciamento` | macoes-geometricas → de-visualizacao-2d | herdada_do_bloco_certo_mas_gold_diverge | herdada | sinal_proprio_unico | bloco-06 (—) | material_gt:ruling_usuario | macoes-geometricas =gold |  |
| CG | `pagina-com-videos-sobre-instanciamento` | macoes-geometricas → de-visualizacao-2d | herdada_do_bloco_certo_mas_gold_diverge | herdada | sinal_proprio_unico | bloco-06 (—) | material_gt:ruling_usuario | de-visualizacao-2d |  |
| CG | `transformacoesgeometricas` | macoes-geometricas → de-visualizacao-2d | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sinal_proprio_unico | bloco-06 (—) | material_gt:ruling_usuario | cessamento-grafico gated |  |
| CG | `transformacoesgl` | macoes-geometricas → de-visualizacao-2d | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sinal_proprio_unico | bloco-06 (—) | material_gt:ruling_usuario | macoes-geometricas gated =gold |  |
| CG | `aula-gravada-975b85` | isao-computacional → de-visualizacao-3d | herdada_do_bloco_errado | herdada | sinal_proprio_unico | bloco-08 (—) | material_gt:secao_moodle | cessamento-grafico |  |
| CG | `basico3d-cpp` | delagem-de-objetos → mentos-matematicos | herdada_do_bloco_errado | reconciliada | sinal_proprio_unico | bloco-05 (—) | material_gt:secao_moodle | de-visualizacao-2d gated |  |
| CG | `basico3d-py-zip` | delagem-de-objetos → mentos-matematicos | herdada_do_bloco_errado | reconciliada | sinal_proprio_unico | bloco-05 (—) | material_gt:secao_moodle | cessamento-grafico gated |  |
| CG | `exercicios` | cessamento-grafico → mentos-matematicos | herdada_do_bloco_errado | vizinho | vizinho:sinal_proprio_unico | bloco-02 (—) | material_gt:ruling_usuario | isao-computacional |  |
| CG | `exercicios-sobre-curvas-html` | delagem-de-objetos → mentos-matematicos | herdada_do_bloco_errado | reconciliada | sem_bloco |  (—) | material_gt:conteudo | delagem-de-objetos gated =gold |  |
| CG | `resolucao-de-prova-de-computacao-grafica-2d` | de-visualizacao-2d → cessamento-grafico | herdada_do_bloco_errado | herdada | sem_bloco |  (—) | material_gt:ruling_usuario | cessamento-grafico |  |
| CG | `resolucao-de-prova-de-computacao-grafica-2d-html` | de-visualizacao-2d → cessamento-grafico | herdada_do_bloco_errado | herdada | sem_bloco |  (—) | material_gt:ruling_usuario | cessamento-grafico |  |
| CG | `resolucao-de-prova-de-computacao-grafica-3d` | de-visualizacao-3d|delagem-de-objetos|magens-realisticas → cessamento-grafico | herdada_do_bloco_errado | herdada | sem_bloco |  (—) | material_gt:ruling_usuario | cessamento-grafico |  |
| CG | `video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758` | cessamento-grafico → mentos-matematicos | herdada_do_bloco_errado | vizinho | vizinho:sinal_proprio_unico | bloco-02 (—) | material_gt:ruling_usuario | cessamento-grafico =gold |  |
| CG | `morfologiamatematicapptx` | isao-computacional → de-visualizacao-3d | texto_vence_errado | concorda_ou_sem_bloco | sinal_proprio_unico | bloco-08 (—) | material_gt:secao_moodle | de-visualizacao-3d gated |  |
| CG | `openglbasico` | cessamento-grafico → isao-computacional | texto_vence_errado | texto_vence_vizinho | vizinho:sinal_proprio_unico | bloco-02 (—) | material_gt:ruling_usuario | isao-computacional gated |  |
| CG | `pagina-com-videos-sobre-morfologia-matematica-06265a` | isao-computacional → de-visualizacao-3d | texto_vence_errado | concorda_ou_sem_bloco | sinal_proprio_unico | bloco-08 (—) | material_gt:secao_moodle | de-visualizacao-3d gated |  |
| CG | `texturas-v3` | magens-realisticas → cessamento-grafico | texto_vence_errado | texto_vence_vizinho | vizinho:sinal_proprio_unico | bloco-02 (—) | material_gt:conteudo | cessamento-grafico gated |  |
| CG | `video-sobre-prechimento-de-areas-duracao-330-defae7` | isao-computacional → cessamento-grafico | texto_vence_errado | concorda_ou_sem_bloco | sinal_proprio_unico | bloco-01 (—) | material_gt:secao_moodle | cessamento-grafico gated |  |
| ES2 | `microsservicos4` | -e-operacao-devops → tetura-de-software | herdada_do_bloco_certo_mas_gold_diverge | herdada | sem_sinal | bloco-07 (-e-operacao-devops) | material_gt:ruling_usuario | tetura-de-software |  |
| ES2 | `azure` | tetura-de-software → -e-operacao-devops | herdada_do_bloco_errado | herdada | sinal_proprio_unico | bloco-08 (-e-operacao-devops) | material_gt:ruling_usuario | tetura-de-software =gold |  |
| IA | `ia-responsável-7c4626` | gem-01-visao-geral → ndizado-de-maquina | herdada_do_bloco_certo_mas_gold_diverge | vizinho | vizinho:sem_sinal | bloco-01 (gem-01-visao-geral) | material_gt:proposto | gem-01-visao-geral =gold |  |
| IA | `visao-geral-introducao-e-historico` | gem-01-visao-geral → ndizado-de-maquina | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sem_sinal | bloco-02 (gem-01-visao-geral) | bloco_gold | gem-01-visao-geral gated =gold |  |
| IA | `o-que-é-inteligência-artificial-ia-oracle-brasil-43437f` | gem-01-visao-geral → lucao-de-problemas | texto_vence_errado | texto_vence_vizinho | vizinho:sem_sinal | bloco-01 (gem-01-visao-geral) | material_gt:proposto | lucao-de-problemas gated |  |
| MF | `eth2` | cacao-de-programas → 01-metodos-formais | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sem_sinal | bloco-01 (01-metodos-formais) | material_gt:ruling_usuario | cacao-de-programas gated =gold |  |
| MF | `t1-2026-1-thy` | 01-metodos-formais → cacao-de-programas | herdada_do_bloco_certo_mas_gold_diverge | vizinho | vizinho:sinal_proprio_unico | bloco-11 (cacao-de-programas) | material_gt:proposto | cacao-de-programas gated |  |
| MF | `aws-encryption-sdk` | cacao-de-programas → 01-metodos-formais | texto_vence_errado | concorda_ou_sem_bloco | sem_sinal | bloco-01 (01-metodos-formais) | material_gt:ruling_usuario | 01-metodos-formais gated |  |
| SO | `0704-exemplo-threads-em-java` | amacao-concorrente → cia-do-processador | herdada_do_bloco_certo_mas_gold_diverge | herdada | sinal_proprio_unico | bloco-06 (nidade-04-deadlock) | material_gt:proposto | cia-do-processador |  |
| SO | `3103-threads` | amacao-concorrente → cia-do-processador | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sinal_proprio_unico | bloco-04 (cia-do-processador) | material_gt:proposto | amacao-concorrente gated =gold |  |
| SO | `biblioteca-em-c-pthread` | amacao-concorrente → cia-do-processador | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sinal_proprio_unico | bloco-04 (cia-do-processador) | material_gt:proposto | amacao-concorrente gated =gold |  |
| SO | `exemplo-threads-em-c-exemplo1` | amacao-concorrente → cia-do-processador | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sinal_proprio_unico | bloco-04 (cia-do-processador) | material_gt:proposto | de-entrada-e-saida gated |  |
| SO | `exemplo-threads-em-c-exemplo2` | amacao-concorrente → cia-do-processador | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sinal_proprio_unico | bloco-04 (cia-do-processador) | material_gt:proposto | de-entrada-e-saida gated |  |
| SO | `exemplo-threads-em-c-exemplo3` | amacao-concorrente → cia-do-processador | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sinal_proprio_unico | bloco-04 (cia-do-processador) | material_gt:proposto | de-entrada-e-saida gated |  |
| SO | `laminas-sockets-material-alternativo-em-pt` | amacao-concorrente → cia-do-processador | herdada_do_bloco_errado | herdada | sinal_proprio_unico | bloco-06 (nidade-04-deadlock) | material_gt:proposto | amacao-concorrente =gold | amacao-concorrente =gold |
| TCC | `aula-11-o-problema-da-parada-halting-problem-halteproblem-pdf` | lemas-indecidiveis → ng-computabilidade | herdada_do_bloco_certo_mas_gold_diverge | reconciliada | sem_sinal | bloco-10 (lemas-indecidiveis) | material_gt:proposto | lemas-indecidiveis gated =gold |  |

## A5. Reconciliação dos 18 pelo gold POR BLOCO

| curso | id | bloco | unidade do bloco | gold do bloco | gold do material | proveniência | W-Z | gold de bloco |
|---|---|---|---|---|---|---|---|---|
| MF | `eth2` | bloco-01 | ade-01-metodos-formais | ade-01-metodos-formais | cacao-de-programas | material_gt:ruling_usuario | empate | homogeneidade |
| MF | `t1-2026-1-thy` | bloco-11 | rificacao-de-programas | rificacao-de-programas | 01-metodos-formais | material_gt:proposto | empate | homogeneidade |
| SO | `0704-exemplo-threads-em-java` | bloco-06 | erencia-do-processador | unidade-04-deadlock | amacao-concorrente | material_gt:proposto | origem | origem |
| SO | `3103-threads` | bloco-04 | erencia-do-processador | erencia-do-processador | amacao-concorrente | material_gt:proposto | origem | homogeneidade |
| SO | `biblioteca-em-c-pthread` | bloco-04 | erencia-do-processador | erencia-do-processador | amacao-concorrente | material_gt:proposto | origem | homogeneidade |
| SO | `exemplo-threads-em-c-exemplo1` | bloco-04 | erencia-do-processador | erencia-do-processador | amacao-concorrente | material_gt:proposto | origem | homogeneidade |
| SO | `exemplo-threads-em-c-exemplo2` | bloco-04 | erencia-do-processador | erencia-do-processador | amacao-concorrente | material_gt:proposto | origem | homogeneidade |
| SO | `exemplo-threads-em-c-exemplo3` | bloco-04 | erencia-do-processador | erencia-do-processador | amacao-concorrente | material_gt:proposto | origem | homogeneidade |
| IA | `ia-responsável-7c4626` | bloco-01 | aprendizado-de-maquina | dizagem-01-visao-geral | gem-01-visao-geral | material_gt:proposto | empate | origem |
| IA | `visao-geral-introducao-e-historico` | bloco-02 | aprendizado-de-maquina | dizagem-01-visao-geral | gem-01-visao-geral | bloco_gold | origem | origem |
| ES2 | `microsservicos4` | bloco-07 | rquitetura-de-software | ento-e-operacao-devops | -e-operacao-devops | material_gt:ruling_usuario | origem | origem |
| TCC | `aula-11-o-problema-da-parada-halting-problem-halteproblem-pdf` | bloco-10 | turing-computabilidade | problemas-indecidiveis | lemas-indecidiveis | material_gt:proposto | origem | origem |
| CG | `exemplodemanipulacaodeimagens` | bloco-03 | undamentos-matematicos | — | isao-computacional | material_gt:ruling_usuario | homogeneidade | indeterminado_sem_gold_de_bloco |
| CG | `animacao-v2` | bloco-06 | sso-de-visualizacao-2d | — | macoes-geometricas | material_gt:ruling_usuario | homogeneidade | indeterminado_sem_gold_de_bloco |
| CG | `instanciamento` | bloco-06 | sso-de-visualizacao-2d | — | macoes-geometricas | material_gt:ruling_usuario | homogeneidade | indeterminado_sem_gold_de_bloco |
| CG | `pagina-com-videos-sobre-instanciamento` | bloco-06 | sso-de-visualizacao-2d | — | macoes-geometricas | material_gt:ruling_usuario | homogeneidade | indeterminado_sem_gold_de_bloco |
| CG | `transformacoesgeometricas` | bloco-06 | sso-de-visualizacao-2d | — | macoes-geometricas | material_gt:ruling_usuario | homogeneidade | indeterminado_sem_gold_de_bloco |
| CG | `transformacoesgl` | bloco-06 | sso-de-visualizacao-2d | — | macoes-geometricas | material_gt:ruling_usuario | homogeneidade | indeterminado_sem_gold_de_bloco |

## A6. Subunidade primária — famílias (base)

| família | CG | ES2 | FR | IA | MF | SO | TCC | total |
|---|---|---|---|---|---|---|---|---|
| F1_identidade | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| F2_unidade | 10 | 3 | 0 | 0 | 0 | 4 | 0 | 17 |
| F4a_abstencao | 3 | 0 | 2 | 0 | 2 | 0 | 1 | 8 |
| F4b_escolha_errada | 6 | 7 | 6 | 4 | 10 | 0 | 0 | 33 |
| F5_alterada_depois | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 3 |
| F6_relacao_fora_do_indice | 8 | 10 | 1 | 30 | 14 | 2 | 0 | 65 |
| F7_relacao_nao_encontrada | 7 | 0 | 0 | 0 | 3 | 1 | 0 | 11 |
| F8_varios_assuntos | 13 | 1 | 1 | 1 | 4 | 1 | 2 | 23 |
| acerto | 30 | 7 | 6 | 4 | 25 | 7 | 7 | 86 |

## A6. Subunidade primária — famílias (oraculo_unidade)

| família | CG | ES2 | FR | IA | MF | SO | TCC | total |
|---|---|---|---|---|---|---|---|---|
| F1_identidade | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| F4a_abstencao | 4 | 1 | 2 | 0 | 2 | 0 | 1 | 10 |
| F4b_escolha_errada | 7 | 7 | 6 | 4 | 10 | 1 | 0 | 35 |
| F5_alterada_depois | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 3 |
| F6_relacao_fora_do_indice | 9 | 11 | 1 | 30 | 14 | 5 | 0 | 70 |
| F7_relacao_nao_encontrada | 9 | 0 | 0 | 0 | 3 | 1 | 0 | 13 |
| F8_varios_assuntos | 15 | 0 | 1 | 1 | 4 | 1 | 2 | 24 |
| acerto | 34 | 9 | 6 | 4 | 25 | 7 | 7 | 92 |

## A7. Subunidade — materiais em erro na base (família, candidatos, alcance)

| curso | id | gold | u^ / s^ (1a) | família | pont gold (unid/qualquer/radical) | rank / n cand | alcance fora do índice | oráculo acerta? |
|---|---|---|---|---|---|---|---|---|
| CG | `animacao-v2` | ∅ | -visualizacao-2d / desenho-de-linhas (desenho-de-linhas) | F1_identidade | 0.0/0.0/0.0 | None/4 | — | False |
| CG | `instanciamento` | ∅ | -visualizacao-2d / sistema-de-coordenadas-cartesianas (sistema-de-coordenadas-cartesianas) | F1_identidade | 0.0/0.0/0.0 | None/5 | — | False |
| CG | `pagina-com-videos-sobre-instanciamento` | ∅ | -visualizacao-2d / desenho-de-linhas (desenho-de-linhas) | F1_identidade | 0.0/0.0/0.0 | None/4 | — | True |
| CG | `transformacoesgeometricas` | ∅ | -visualizacao-2d / recorte (∅) | F1_identidade | 0.0/0.0/0.0 | None/4 | — | False |
| CG | `transformacoesgl` | ∅ | -visualizacao-2d / sistema-de-coordenadas-cartesianas (sistema-de-coordenadas-cartesianas) | F1_identidade | 0.0/0.0/0.0 | None/5 | — | False |
| CG | `aula-gravada-975b85` | segmentacao | -visualizacao-3d / a-matematica-das-projecoes-planares (∅) | F2_unidade | 0.0/0.0/0.0 | None/7 | documental | True |
| CG | `basico3d-cpp` | tecnicas-de-modelagem-3d | ntos-matematicos / algoritmos-de-poligonos (algoritmos-de-poligonos) | F2_unidade | 0.0/0.1077/0.1077 | None/2 | radical | False |
| CG | `basico3d-py-zip` | tecnicas-de-modelagem-3d | ntos-matematicos / operacoes-com-vetores (∅) | F2_unidade | 0.0/0.1077/0.1077 | None/0 | radical | True |
| CG | `exercicios` | aplicacoes | ntos-matematicos / ∅ (∅) | F2_unidade | 0.0/0.0/0.0 | None/0 | — | False |
| CG | `exercicios-sobre-curvas-html` | catmull-rom | ntos-matematicos / ∅ (∅) | F2_unidade | 0.0/4.27/4.27 | None/2 | radical,documental | False |
| CG | `morfologiamatematicapptx` | segmentacao | -visualizacao-3d / a-matematica-das-projecoes-planares (a-matematica-das-projecoes-planares) | F2_unidade | 0.0/0.0/0.0 | None/7 | documental | True |
| CG | `openglbasico` | aplicacoes | ao-computacional / introducao-e-exemplos-de-aplicacoes (introducao-e-exemplos-de-aplicacoes) | F2_unidade | 0.0/2.0/2.0 | None/3 | radical | True |
| CG | `pagina-com-videos-sobre-morfologia-matematica-06265a` | segmentacao | -visualizacao-3d / a-matematica-das-projecoes-planares (a-matematica-das-projecoes-planares) | F2_unidade | 0.0/0.0/0.0 | None/7 | documental | True |
| CG | `video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758` | aplicacoes | ntos-matematicos / ∅ (∅) | F2_unidade | 0.0/0.0/0.0 | None/0 | — | False |
| CG | `video-sobre-prechimento-de-areas-duracao-330-defae7` | segmentacao | ssamento-grafico / areas-relacionadas (areas-relacionadas) | F2_unidade | 0.0/0.0/0.0 | None/1 | documental | False |
| CG | `opengl3d` | conceito-de-camera-sintetica | -visualizacao-3d / ∅ (∅) | F4a_abstencao | 0.9072/0.9072/0.9072 | 4/9 | radical,documental | False |
| CG | `pagina-com-videos-sobre-visualizacao-3d-35a833` | pipeline-de-visualizacao-3d | -visualizacao-3d / ∅ (∅) | F4a_abstencao | 0.9072/0.9072/0.9072 | 4/10 | radical,bloco,documental | False |
| CG | `vis3d` | projecoes | -visualizacao-3d / ∅ (∅) | F4a_abstencao | 9.42/9.42/9.42 | 3/10 | radical,documental | False |
| CG | `exercicios-sobre-curvas` | catmull-rom | lagem-de-objetos / hermite (hermite) | F4b_escolha_errada | 4.27/4.27/4.27 | 2/13 | radical,documental | False |
| CG | `mapeamento` | sistema-de-coordenadas-cartesianas | -visualizacao-2d / recorte (recorte) | F4b_escolha_errada | 0.9072/0.9072/3.262 | 2/5 | radical,documental | False |
| CG | `opengl-cpp` | aplicacoes | ssamento-grafico / conceitos (∅) | F4b_escolha_errada | 4.8/4.8/4.8 | 2/2 | radical | False |
| CG | `pagina-com-videos-sobre-curvas-parametricas-63d902` | representacao-de-curvas-parametricas | lagem-de-objetos / hermite (hermite) | F4b_escolha_errada | 0.936/0.936/0.936 | 3/13 | radical,secao,bloco,documental | False |
| CG | `pagina-com-videos-sobre-sintese-de-imagens-realisticas-a6d9ea` | modelos-de-iluminacao-luz-pontual-direcional-spot | gens-realisticas / mapeamento-de-textura (modelos-de-reflexao-ambiente-difusa-especular) | F4b_escolha_errada | 0.9072/0.9072/0.9072 | 2/5 | radical | False |
| CG | `paginas-com-videos-sobre-modelagem-geometrica-f2614a` | tecnicas-de-modelagem-3d | lagem-de-objetos / geometria-solida-construtiva-csg (instanciamento-de-primitivas) | F4b_escolha_errada | 0.9072/0.9072/8.358 | 6/15 | radical,documental | False |
| CG | `exercicios-teoricos-sobre-processo-de-visualizacao-2d` | sistema-de-coordenadas-cartesianas | -visualizacao-2d / desenho-de-linhas (desenho-de-linhas) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/4 | documental | False |
| CG | `exercicios-teoricos-sobre-processo-de-visualizacao-2d-html` | sistema-de-coordenadas-cartesianas | -visualizacao-2d / desenho-de-linhas (desenho-de-linhas) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/4 | documental | False |
| CG | `floodfill` | segmentacao | ao-computacional / cores-e-tipos-de-imagens (cores-e-tipos-de-imagens) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| CG | `matematica` | operacoes-com-vetores | ntos-matematicos / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/0 | documental | False |
| CG | `pagina-com-videos-sobre-fundamentos-matematicos-para-computacao-grafica-d1d4a9` | entidades-geometricas | ntos-matematicos / algoritmos-de-poligonos (algoritmos-de-poligonos) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/3 | documental | False |
| CG | `remocaoderuido` | filtros | ao-computacional / cores-e-tipos-de-imagens (cores-e-tipos-de-imagens) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| CG | `video-sobre-prechimento-de-areas-duracao-1300-d87e5f` | segmentacao | ao-computacional / cores-e-tipos-de-imagens (cores-e-tipos-de-imagens) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| CG | `videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84` | algoritmos-de-deteccao-e-calculo-de-interseccao | ntos-matematicos / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/0 | documental | False |
| CG | `atividade` | conceito-de-camera-sintetica | -visualizacao-3d / ∅ (∅) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/7 | — | False |
| CG | `exercicio-com-animacao` | operacoes-com-vetores | ntos-matematicos / algoritmos-de-poligonos (algoritmos-de-poligonos) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/1 | — | False |
| CG | `opengl-py` | aplicacoes | ssamento-grafico / conceitos (conceitos) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/1 | — | False |
| CG | `opengl3dcpp` | conceito-de-camera-sintetica | -visualizacao-3d / algoritmo-z-buffer (algoritmo-z-buffer) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/8 | — | False |
| CG | `opengl3dcpp-vdi` | conceito-de-camera-sintetica | -visualizacao-3d / algoritmo-z-buffer (algoritmo-z-buffer) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/8 | — | False |
| CG | `pagina-com-videos-sobre-mapeamento-9f410e` | sistema-de-coordenadas-cartesianas | -visualizacao-2d / recorte (∅) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/4 | — | False |
| CG | `video-sobre-mapeamento-em-opengl-1dad3c` | sistema-de-coordenadas-cartesianas | -visualizacao-2d / recorte (∅) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/4 | — | False |
| CG | `basico3d-py` | conceito-de-camera-sintetica | -visualizacao-3d / pipeline-de-visualizacao-3d (pipeline-de-visualizacao-3d) | F8_varios_assuntos | 0.0/0.0/0.0 | None/8 | — | False |
| CG | `curvas` | representacao-de-curvas-parametricas | lagem-de-objetos / hermite (hermite) | F8_varios_assuntos | 1.512/1.512/9.198 | 2/15 | radical,secao,bloco,documental | False |
| CG | `elemoculto` | algoritmos-de-remocao-de-elementos-ocultos | -visualizacao-3d / algoritmo-z-buffer (algoritmo-z-buffer) | F8_varios_assuntos | 1.4832/1.4832/17.166 | 6/11 | radical,secao,bloco,documental | False |
| CG | `exercicio-de-animacao-foguete` | operacoes-com-vetores | ntos-matematicos / algoritmos-de-poligonos (algoritmos-de-poligonos) | F8_varios_assuntos | 0.0/0.0/0.0 | None/1 | — | False |
| CG | `exerciciodemodelagem` | varredura | lagem-de-objetos / tecnicas-de-modelagem-3d (tecnicas-de-modelagem-3d) | F8_varios_assuntos | 0.0172/0.0172/0.0172 | 12/14 | radical,documental | False |
| CG | `exercicioduascores` | algoritmos-de-quantizacao-e-amostragem | ao-computacional / cores-e-tipos-de-imagens (cores-e-tipos-de-imagens) | F8_varios_assuntos | 0.0/0.0/0.0 | None/1 | documental | False |
| CG | `exercicios-de-processamento-de-imagens` | algoritmos-de-quantizacao-e-amostragem | ao-computacional / cores-e-tipos-de-imagens (cores-e-tipos-de-imagens) | F8_varios_assuntos | 0.0/0.0/0.0 | None/1 | documental | False |
| CG | `exerciciosfundamentosmatematicos` | algoritmos-de-poligonos | ntos-matematicos / operacoes-com-vetores (operacoes-com-vetores) | F8_varios_assuntos | 0.0/0.0/0.0 | None/1 | documental | False |
| CG | `fundamentosmatematicos` | entidades-geometricas | ntos-matematicos / operacoes-com-vetores (operacoes-com-vetores) | F8_varios_assuntos | 0.0/0.0/0.0 | None/3 | documental | False |
| CG | `iluminacao` | modelos-de-iluminacao-luz-pontual-direcional-spot | gens-realisticas / modelos-de-reflexao-ambiente-difusa-especular (modelos-de-reflexao-ambiente-difusa-especular) | F8_varios_assuntos | 0.9072/0.9072/0.9072 | 3/4 | radical,documental | False |
| CG | `modelagem3d` | formas-de-representacao | lagem-de-objetos / representacao-aramada (representacao-aramada) | F8_varios_assuntos | 1.3248/1.3248/8.938 | 6/15 | radical,documental | False |
| CG | `pagina-com-videos-sobre-introducao-ao-processamento-de-imagens-61f156` | introducao-e-exemplos-de-aplicacoes | ao-computacional / filtros (filtros) | F8_varios_assuntos | 0.9072/0.9072/8.358 | 2/3 | radical | False |
| CG | `vis2d` | sistema-de-coordenadas-cartesianas | -visualizacao-2d / recorte (recorte) | F8_varios_assuntos | 0.9072/0.9072/0.9072 | 3/5 | radical,documental | False |
| ES2 | `microsservicos4` | estudo-de-caso-integracao-e-implantacao-de-microsservicos | tura-de-software / estilos-e-padroes-arquiteturais (estilos-e-padroes-arquiteturais) | F2_unidade | 0.0/0.0/0.0 | None/7 | secao,documental | True |
| ES2 | `roteiro4` | estudo-de-caso-integracao-e-implantacao-de-microsservicos | tura-de-software / ∅ (∅) | F2_unidade | 0.0/0.0/0.0 | None/5 | secao | True |
| ES2 | `roteiro4-circuitbreaker` | estudo-de-caso-integracao-e-implantacao-de-microsservicos | tura-de-software / estilos-e-padroes-arquiteturais (conceito-de-arquitetura-de-software) | F2_unidade | 0.0/0.0/0.0 | None/8 | secao,documental | False |
| ES2 | `devops` | conceito-de-devops | -operacao-devops / integracao-continua-ci (integracao-continua-ci) | F4b_escolha_errada | 0.4406/0.4406/0.4406 | 6/7 | radical,secao,documental | False |
| ES2 | `microsservicos` | orientada-a-microsservicos | tura-de-software / estilos-e-padroes-arquiteturais (estilos-e-padroes-arquiteturais) | F4b_escolha_errada | 0.0196/0.0196/10.05 | 10/10 | radical,secao,documental | False |
| ES2 | `microsservicos2` | estudo-de-caso-arquitetura-orientada-a-microsservicos | tura-de-software / estilos-e-padroes-arquiteturais (cliente-servidor) | F4b_escolha_errada | 0.1224/0.1224/0.1224 | 8/10 | radical,secao,documental | False |
| ES2 | `microsservicos5` | plataformas-de-devops | -operacao-devops / entrega-continua-cd (gerenciamento-da-configuracao) | F4b_escolha_errada | 0.1224/0.1224/0.1224 | 6/6 | radical,documental | False |
| ES2 | `roteiro1-introducao` | estudo-de-caso-arquitetura-orientada-a-microsservicos | tura-de-software / estilos-e-padroes-arquiteturais (cliente-servidor) | F4b_escolha_errada | 0.1224/0.1224/0.1224 | 6/8 | radical,secao,documental | False |
| ES2 | `roteiro2-nameserver` | estudo-de-caso-arquitetura-orientada-a-microsservicos | tura-de-software / estilos-e-padroes-arquiteturais (cliente-servidor) | F4b_escolha_errada | 0.1224/0.1224/0.1224 | 6/8 | radical,secao,documental | False |
| ES2 | `roteiro3-gateway` | estudo-de-caso-arquitetura-orientada-a-microsservicos | tura-de-software / cliente-servidor (cliente-servidor) | F4b_escolha_errada | 0.1224/0.1224/0.1224 | 6/8 | radical,secao,documental | False |
| ES2 | `kubernetes` | plataformas-de-devops | -operacao-devops / estudo-de-caso-integracao-e-implantacao-de-microsservicos (estudo-de-caso-integracao-e-implantacao-de-microsservicos) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/4 | secao | False |
| ES2 | `microsservicos3` | estudo-de-caso-arquitetura-orientada-a-microsservicos | tura-de-software / estilos-e-padroes-arquiteturais (estilos-e-padroes-arquiteturais) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/7 | secao,documental | False |
| ES2 | `microsservicos6` | estudo-de-caso-integracao-e-implantacao-de-microsservicos | -operacao-devops / gerenciamento-da-configuracao (gerenciamento-da-configuracao) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | secao,documental | False |
| ES2 | `microsservicos7` | estudo-de-caso-integracao-e-implantacao-de-microsservicos | -operacao-devops / gerenciamento-da-configuracao (gerenciamento-da-configuracao) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | secao,documental | False |
| ES2 | `roteiro1` | estudo-de-caso-arquitetura-orientada-a-microsservicos | tura-de-software / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao | False |
| ES2 | `roteiro2` | estudo-de-caso-arquitetura-orientada-a-microsservicos | tura-de-software / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao | False |
| ES2 | `roteiro3` | estudo-de-caso-arquitetura-orientada-a-microsservicos | tura-de-software / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao | False |
| ES2 | `roteiro6-conteiners-composicao` | estudo-de-caso-integracao-e-implantacao-de-microsservicos | -operacao-devops / gerenciamento-da-configuracao (gerenciamento-da-configuracao) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | secao,bloco,documental | False |
| ES2 | `roteiro7-filas` | estudo-de-caso-integracao-e-implantacao-de-microsservicos | -operacao-devops / gerenciamento-da-configuracao (gerenciamento-da-configuracao) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/2 | secao,documental | False |
| ES2 | `roteiro8-autenticacao-autorizacao` | estudo-de-caso-integracao-e-implantacao-de-microsservicos | -operacao-devops / gerenciamento-da-configuracao (gerenciamento-da-configuracao) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | secao,documental | False |
| ES2 | `revisaoarquiteturapadroes` | conceito-de-arquitetura-de-software | tura-de-software / estilos-e-padroes-arquiteturais (∅) | F8_varios_assuntos | 0.4406/0.4406/2.902 | 10/10 | radical,bloco,documental | False |
| FR | `08-desenvolvimento-de-aplicacoes` | implementacao-de-sockets | vel-de-aplicacao / ∅ (∅) | F4a_abstencao | 0.1249/0.1249/10.3 | 5/5 | radical,bloco,documental | False |
| FR | `unidade1-exercicios` | modelos-osi-e-tcpip | -de-computadores / ∅ (∅) | F4a_abstencao | 0.1422/0.1422/0.1422 | 2/2 | radical | False |
| FR | `04-camada-de-aplicacao` | funcoes-e-caracteristicas-do-nivel-de-aplicacao | vel-de-aplicacao / protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap (protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap) | F4b_escolha_errada | 0.3878/0.3878/0.3878 | 4/5 | radical,bloco,documental | False |
| FR | `05-protocolo-dns` | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | vel-de-aplicacao / protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap (protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap) | F4b_escolha_errada | 1.0368/1.0368/1.0368 | 2/5 | radical,bloco,documental | False |
| FR | `tcp-chat-c` | implementacao-de-sockets | vel-de-aplicacao / paradigmas-clienteservidor-e-p2p (paradigmas-clienteservidor-e-p2p) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 2/2 | radical,bloco,documental | False |
| FR | `tcp-example` | implementacao-de-sockets | vel-de-aplicacao / paradigmas-clienteservidor-e-p2p (paradigmas-clienteservidor-e-p2p) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 2/2 | radical,bloco,documental | False |
| FR | `udp-example-c` | implementacao-de-sockets | vel-de-aplicacao / paradigmas-clienteservidor-e-p2p (paradigmas-clienteservidor-e-p2p) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 2/2 | radical,bloco,documental | False |
| FR | `udp-example-java` | implementacao-de-sockets | vel-de-aplicacao / paradigmas-clienteservidor-e-p2p (paradigmas-clienteservidor-e-p2p) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 2/2 | radical,bloco,documental | False |
| FR | `04-protocolo-http` | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | vel-de-aplicacao / paradigmas-clienteservidor-e-p2p (protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap) | F5_alterada_depois | 1.296/1.296/1.296 | 1/5 | radical,bloco,documental | False |
| FR | `unidade2-exercicios-http` | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | vel-de-aplicacao / paradigmas-clienteservidor-e-p2p (protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap) | F5_alterada_depois | 1.3536/1.3536/1.3536 | 1/5 | radical,bloco,documental | False |
| FR | `01-protocolos-de-rede` | conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | -de-computadores / modelos-osi-e-tcpip (modelos-osi-e-tcpip) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| FR | `lista-de-exercicios-1-camada-de-aplicacao` | funcoes-e-caracteristicas-do-nivel-de-aplicacao | vel-de-aplicacao / paradigmas-clienteservidor-e-p2p (∅) | F8_varios_assuntos | 0.4222/0.4222/0.4222 | 4/5 | radical,bloco | False |
| IA | `artigo-usando-k-nn-em-texto` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F4b_escolha_errada | 0.1224/0.1224/1.152 | 3/4 | radical,documental | False |
| IA | `arvores-de-decisao` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F4b_escolha_errada | 0.1077/0.1077/10.956 | 3/5 | radical,documental | False |
| IA | `como-analisar-resultados-acc-pr-re-e-f1` | metricas-de-avaliacao | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F4b_escolha_errada | 0.9072/0.9072/0.9072 | 2/2 | radical,documental | False |
| IA | `mlp` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F4b_escolha_errada | 0.1224/0.1224/1.152 | 3/4 | radical,documental | False |
| IA | `agrupamento-hierarquico-exemplo-1` | modelos-descritivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/3 | documental | False |
| IA | `agrupamento-hierarquico-exemplo-2-use-o-dataset-da-planta-iris` | modelos-descritivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/3 | documental | False |
| IA | `agrupamento-usando-k-means-exemplo-1-ipynb` | modelos-descritivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/3 | documental | False |
| IA | `agrupamento-usando-k-means-exemplo-2-ipynb` | modelos-descritivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/2 | documental | False |
| IA | `algoritmo-de-classificacao-k-nn` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/2.002 | None/2 | radical,documental | False |
| IA | `artigo-usando-agrupamento` | modelos-descritivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/3 | documental | False |
| IA | `aula-sobre-agrupamento-parte-1-particional` | modelos-descritivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/7.098 | None/3 | radical,documental | False |
| IA | `aula-sobre-agrupamento-parte-2-hierarquico` | modelos-descritivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/7.098 | None/2 | radical,documental | False |
| IA | `exemplo-1-arvores-de-decisao-classificacao-planta-iris` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/6.806 | None/3 | radical,documental | False |
| IA | `exemplo-2-arvores-de-decisao-regressao-diabetes` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/6.806 | None/3 | radical,documental | False |
| IA | `exemplo-2-k-nn-com-iriscsv-mais-completo` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| IA | `exemplo-com-k-nn` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| IA | `exemplo-de-programa-com-k-nn-em-java` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| IA | `exercicio-2-solucao-com-rede-perceptron-atualizado` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/0 | documental | False |
| IA | `introducao-a-redes-neurais` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/2 | documental | False |
| IA | `k-nn-para-classificacao-exemplo-cardio` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| IA | `k-nn-para-regressao-exemplo-imc` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/1.1 | None/1 | radical,documental | False |
| IA | `mlp-classificacao-inadimplencia-normalizacao-e-gridsearchcv` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/2 | documental | False |
| IA | `mlp-classificacao-iris-atualizado` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/2 | documental | False |
| IA | `mlp-regressao-cardio` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/1.1 | None/1 | radical,documental | False |
| IA | `mlp-xoripynb` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| IA | `rede-perceptron` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.902 | None/3 | radical,documental | False |
| IA | `rede-perceptron-classificacao-de-cliente` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/0 | documental | False |
| IA | `rede-perceptron-classificacao-planta-iris` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| IA | `rede-perceptron-e-equacao-de-reta` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| IA | `rede-perceptron-exemplo-atualizado` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/2 | documental | False |
| IA | `rede-perceptron-or-em-python` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/0 | documental | False |
| IA | `rede-perceptron-reconhecendo-letras` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/0 | documental | False |
| IA | `survey-on-clustering` | modelos-descritivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (introducao-ao-aprendizado-de-maquina) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/1 | documental | False |
| IA | `xor-backpropagation-em-python` | modelos-preditivos | izado-de-maquina / introducao-ao-aprendizado-de-maquina (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/2 | documental | False |
| IA | `exemplo-complementar-classificacao-com-arvores-de-decisao` | modelos-preditivos | izado-de-maquina / metricas-de-avaliacao (metricas-de-avaliacao) | F8_varios_assuntos | 0.0/0.0/3.9 | None/2 | radical,documental | False |
| MF | `exerciciosnusmv` | softwares-de-suporte-a-verificacao-formal-de-modelos | cacao-de-modelos / ∅ (∅) | F4a_abstencao | 0.4222/0.4222/0.4222 | 4/8 | radical,secao,bloco | False |
| MF | `terminacao` | correcao-parcial-e-total | cao-de-programas / ∅ (∅) | F4a_abstencao | 0.0172/0.0172/0.0172 | 2/5 | radical,bloco,documental | False |
| MF | `archive-of-formal-proofs-355fb8` | provadores-de-teoremas | -metodos-formais / abordagens-para-verificacao-formal (sistemas-formais) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 6/6 | radical,bloco,documental | False |
| MF | `arvores` | provadores-de-teoremas | -metodos-formais / abordagens-para-verificacao-formal (abordagens-para-verificacao-formal) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 5/5 | radical,bloco,documental | False |
| MF | `classes-parte1` | pre-e-pos-condicoes | cao-de-programas / invariante-e-variante-de-laco (invariante-e-variante-de-laco) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 2/5 | radical,documental | False |
| MF | `exemplos` | provadores-de-teoremas | -metodos-formais / exemplos-de-aplicacoes (exemplos-de-aplicacoes) | F4b_escolha_errada | 0.1249/0.1249/0.1249 | 2/6 | radical,bloco,documental | False |
| MF | `hoare` | logica-de-hoare | cao-de-programas / correcao-parcial-e-total (correcao-parcial-e-total) | F4b_escolha_errada | 0.1077/0.1077/0.1077 | 2/6 | radical,bloco,documental | False |
| MF | `intro` | provadores-de-teoremas | -metodos-formais / abordagens-para-verificacao-formal (abordagens-para-verificacao-formal) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 5/5 | radical,bloco | False |
| MF | `invariantes` | invariante-e-variante-de-laco | cao-de-programas / sistema-de-prova (sistema-de-prova) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 4/5 | radical,bloco,documental | False |
| MF | `listas` | provadores-de-teoremas | -metodos-formais / abordagens-para-verificacao-formal (abordagens-para-verificacao-formal) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 5/5 | radical,bloco,documental | False |
| MF | `logicapredicados-semantica` | fundamentos-de-logica-de-primeira-ordem | -metodos-formais / especificacao-de-funcoes-recursivas (especificacao-de-funcoes-recursivas) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 2/4 | radical,documental | False |
| MF | `provas` | provadores-de-teoremas | -metodos-formais / abordagens-para-verificacao-formal (abordagens-para-verificacao-formal) | F4b_escolha_errada | 0.0172/0.0172/0.0172 | 5/5 | radical,bloco,documental | False |
| MF | `colecoes-arrays` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `colecoes-conjuntos` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `colecoes-sequences` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `exemplos-zip` | softwares-de-suporte-a-verificacao-formal-de-modelos | cacao-de-modelos / maquinas-de-estado (maquinas-de-estado) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `exercicios-arrays` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / sistema-de-prova (sistema-de-prova) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `exercicios-conjuntos` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `exerciciosdafny1` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / correcao-parcial-e-total (correcao-parcial-e-total) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao | False |
| MF | `exerciciosdafny2` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / pre-e-pos-condicoes (pre-e-pos-condicoes) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `exerciciosdafny3` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `exerciciosdafny4` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / correcao-parcial-e-total (correcao-parcial-e-total) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `exerciciosdafny5` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / correcao-parcial-e-total (correcao-parcial-e-total) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `exercicioslogicatemporal` | fundamentos-de-logicas-temporais | cacao-de-modelos / modelos-de-kripke (modelos-de-kripke) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/7 | documental | False |
| MF | `introducao-zip` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao | False |
| MF | `tiposindutivos` | softwares-de-suporte-a-verificacao-formal-de-programas | cao-de-programas / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/5 | secao,bloco | False |
| MF | `logicaproposicional-semantica` | linguagens-de-especificacao-e-logicas | -metodos-formais / ∅ (∅) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/4 | — | False |
| MF | `logicaproposicional-sintaxe` | linguagens-de-especificacao-e-logicas | -metodos-formais / ∅ (∅) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/4 | — | False |
| MF | `revisao` | sistemas-formais | -metodos-formais / ∅ (∅) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/5 | — | False |
| MF | `classes-parte2` | verificacao-de-programas | cao-de-programas / invariante-e-variante-de-laco (invariante-e-variante-de-laco) | F8_varios_assuntos | 0.0172/0.0172/0.0172 | 5/5 | radical,secao,bloco | False |
| MF | `exercicioscorrecaoterminacao` | correcao-parcial-e-total | cao-de-programas / invariante-e-variante-de-laco (invariante-e-variante-de-laco) | F8_varios_assuntos | 0.1594/0.1594/0.1594 | 2/5 | radical,bloco,documental | False |
| MF | `exerciciosisabelle2` | provadores-de-teoremas | -metodos-formais / especificacao-de-funcoes-recursivas (∅) | F8_varios_assuntos | 0.1594/0.1594/0.1594 | 2/5 | radical,bloco,documental | False |
| MF | `logicadehoare2` | logica-de-hoare | cao-de-programas / invariante-e-variante-de-laco (invariante-e-variante-de-laco) | F8_varios_assuntos | 4.27/4.27/22.6724 | 2/6 | radical,bloco,documental | False |
| SO | `3103-threads` | programas-multithreads | a-do-processador / escalonamento (escalonamento) | F2_unidade | 0.0/0.1224/15.356 | None/2 | radical,documental | False |
| SO | `exemplo-threads-em-c-exemplo1` | programas-multithreads | a-do-processador / ∅ (∅) | F2_unidade | 0.0/0.0/0.0 | None/0 | documental | False |
| SO | `exemplo-threads-em-c-exemplo2` | programas-multithreads | a-do-processador / ∅ (∅) | F2_unidade | 0.0/0.0/0.0 | None/0 | documental | False |
| SO | `exemplo-threads-em-c-exemplo3` | programas-multithreads | a-do-processador / ∅ (∅) | F2_unidade | 0.0/0.0/0.0 | None/0 | documental | False |
| SO | `1903-estruturas-de-controle` | conceitos-basicos | a-do-processador / escalonamento (escalonamento) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/2 | documental | False |
| SO | `exemplo-criacao-de-processos-no-unix-linux-filho` | chamadas-de-sistema | mas-operacionais / ∅ (∅) | F6_relacao_fora_do_indice | 0.0/0.0/0.0 | None/0 | bloco,documental | False |
| SO | `exercicios` | algoritmos-de-escalonamento | a-do-processador / ∅ (∅) | F7_relacao_nao_encontrada | 0.0/0.0/0.0 | None/0 | — | False |
| SO | `definicao-e-historico` | evolucao-historica | mas-operacionais / servicos-dos-sistemas-operacionais (servicos-dos-sistemas-operacionais) | F8_varios_assuntos | 0.0/0.0/0.0 | None/2 | documental | False |
| TCC | `aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-conjuntos-e-enumerabilidade` | conjuntos-enumeraveis | ncoes-recursivas / ∅ (∅) | F4a_abstencao | 0.1077/0.1077/15.902 | 2/3 | radical,documental | False |
| TCC | `aula-09-variacoes-de-maquinas-de-turing` | variacoes-de-maquinas-de-turing | -computabilidade / maquinas-de-turing (variacoes-de-maquinas-de-turing) | F5_alterada_depois | 10.88/10.88/18.1124 | 1/5 | radical,secao,bloco,documental | False |
| TCC | `aula-02-conjuntos-enumeraveis-e-nao-enumeraveis-argumento-da-diagonalizacao-de-cantor` | argumento-diagonal-de-cantor-e-conjuntos-incontaveis | ncoes-recursivas / conjuntos-enumeraveis (conjuntos-enumeraveis) | F8_varios_assuntos | 1.1664/1.1664/3.622 | 2/2 | radical,bloco,documental | False |
| TCC | `aula-08-maquinas-de-turing-como-processadoras-de-funcoes` | conjectura-de-church-turing | -computabilidade / maquinas-de-turing (maquinas-de-turing) | F8_varios_assuntos | 0.9072/0.9072/0.9072 | 3/5 | radical,documental | False |
