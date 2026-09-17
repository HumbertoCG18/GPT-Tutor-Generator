CURSO: TCC

TOPICOS DO PLANO (use somente estes codigos):
- `1.1` Conjuntos Enumeráveis
- `1.2` Argumento Diagonal de Cantor e Conjuntos Incontáveis
- `1.3` Funções Recursivas Primitivas e Funções Recursivas Parciais
- `2.1` Máquinas de Turing
- `2.2` Linguagens Reconhecíveis e Decidíveis
- `2.3` Variações de Máquinas de Turing
- `2.4` Conjectura de Church-Turing
- `2.5` Máquinas de Turing Universais
- `3.1` Prova da Indecidibilidade do Problema da Parada
- `3.2` Entscheidungsproblem e Introdução à Reducibilidade de Problemas
- `3.3` Decidibilidade de Teorias Lógicas
- `3.4` Teoremas de Gödel
- `4.1` Tipos de Problemas Computacionais
- `4.2` Complexidade de Tempo e de Espaço
- `4.3` Hierarquia de Classes de Complexidade de Problemas
- `4.4` Classe P e exemplos de Problemas em P
- `4.5` Classe NP
- `4.6` Classe PSPACE
- `4.7` Intratabilidade

CATEGORIAS (lote 2):
[121] categoria: HALT | termos: x) : M \text{ para na entrada } x\}$ | trecho: - **HALT**: $\{(M, x) : M \text{ para na entrada } x\}$
[122] categoria: Funcionamento | termos: 1 Cursor inicia no estado  $q0$; A base sempre está “na frente” do topo | trecho: #### Funcionamento - 1 Cursor inicia no estado $q_0$
[123] categoria: $q0$ | termos: estado inicial; procura 0 para marcar | trecho: - $q_0$ : estado inicial, $F = \{q_2\}$
[124] categoria: $q1$ | termos: último símbolo foi 0; $q2$ : últimos símbolos foram 01; movendo à direita; procurando 1 | trecho: - $q_1$ : último símbolo foi 0, $q_2$ : últimos símbolos foram 01
[125] categoria: Uma linguagem é regular se é reconhecida por algum DFA | termos: equivalentemente; por algum NDFAs | trecho: Uma linguagem é **regular** se é reconhecida por algum DFA (equivalentemente, por algum NDFAs).
[126] categoria: Transição  $q0 \rightarrow q1$ | termos: ao ler o primeiro 1; muda para fase de comparação | trecho: - **Transição $q_0 \rightarrow q_1$ :** ao ler o primeiro 1, muda para fase de comparação
[127] categoria: Transições principais | termos: $(q0, 1, X) \rightarrow (q1, \varepsilon)$; $(q1, 1, X) \rightarrow (q1, \varepsilon)$; $(q1, \varepsilon, Z0) \rightarrow (qf, Z0)$ | trecho: #### Transições principais - $(q_0, 1, X) \rightarrow (q_1, \varepsilon)$
[128] categoria: Outro Exemplo de PDA | termos: b\}^\}$ | trecho: #### Outro Exemplo de PDA: $L = \{wcw^R : w \in \{a, b\}^*\}$
[129] categoria: Observação | termos: Cada nível adiciona “memória”; AFD: memória finita (estados); AP: memória de pilha (LIFO); ALL: memória linear no tamanho da entrada | trecho: #### Observação - Cada nível adiciona “memória”
[130] categoria: Tipo 3: Regulares | termos: $\{w : w \text{ contém } 01 \text{ como subcadeia}; $\{w : |w| \text{ é par}\}$; Qualquer linguagem finita | trecho: #### Tipo 3: Regulares - $\{w : w \text{ contém } 01 \text{ como subcadeia}\}$
[131] categoria: Tipo 2: Livres de Contexto | termos: $\{0^n 1^n : n \geq 0\}$; $\{ww^R : w \in \{a, b\}^\}$ , palíndromos pares; Expressões aritméticas bem formadas | trecho: #### Tipo 2: Livres de Contexto - $\{0^n 1^n : n \geq 0\}$
[132] categoria: $\{ww^R | termos: w \in \{a; b\}^\}$; palíndromos pares | trecho: - $\{ww^R : w \in \{a, b\}^*\}$ , palíndromos pares
[133] categoria: Tipo 1: Sensíveis ao Contexto | termos: $\{ww : w \in \{a, b\}^\}$ , cópias | trecho: #### Tipo 1: Sensíveis ao Contexto - $\{ww : w \in \{a, b\}^*\}$ , cópias
[134] categoria: $\{ww | termos: w \in \{a; b\}^\}$; cópias | trecho: - $\{ww : w \in \{a, b\}^*\}$ , cópias
[135] categoria: Características | termos: Reconhecidas por Máquinas de Turing; Nenhuma restrição nas regras de produção; Crescimento mais rápido que qualquer polinômio | trecho: #### Características - Reconhecidas por Máquinas de Turing
[136] categoria: Exercício 4: Autômatos Finitos | termos: 2 Construa um N DFA para | trecho: ### Exercício 4: Autômatos Finitos - 2 Construa um N DFA para
[137] categoria: 4  $L = \{ww | termos: w \in \{a; b\}^\}$ | trecho: - 4 $L = \{ww : w \in \{a, b\}^*\}$
[138] categoria: 3  $\{w | termos: assumo o alfabeto  $\{a; b\}$ | trecho: - 3 $\{w : w \text{ tem igual número de as e bs}\}$ , assumo o alfabeto $\{a, b\}$
[139] categoria: 4  $\{ww^R | termos: w \in \{a; b\}^\}$ | trecho: - 4 $\{ww^R : w \in \{a, b\}^*\}$
[140] categoria: 2 Projete um PDA para  $L = \{wcw^R | termos: w \in \{a; b\}^\}$ | trecho: - 2 Projete um PDA para $L = \{wcw^R : w \in \{a, b\}^*\}$ .
[141] categoria: 2  $\{ww | termos: w \in \{a; b\}^\}$ | trecho: - 2 $\{ww : w \in \{a, b\}^*\}$
[142] categoria: Componentes de uma Máquina de Turing | termos: 1 Fita: memória infinita dividida em células; 3 Controle: estados que determinam o comportamento | trecho: ## Componentes de uma Máquina de Turing - 1 Fita:** memória infinita dividida em células
[143] categoria: 2 Cabeçote | termos: lê e escreve na fita; move-se | trecho: - 2 Cabeçote:** lê e escreve na fita, move-se
[144] categoria: $\delta | termos: R\}$; função de transição; S\}^k$$; R\})$$ | trecho: - $\delta : Q \times \Gamma \rightarrow Q \times \Gamma \times \{L, R\}$ , **função de transição**
[145] categoria: Convenções | termos: $\sqcup$  é o símbolo branco (blank); Estado inicial: seta entrando; Estado de aceitação: círculo duplo; Transições: setas rotuladas  $a \rightarrow b, D$ | trecho: ### Convenções - $\sqcup$ é o símbolo **branco** (blank)
[146] categoria: “Se está em  $q1$  lendo  $a$ | termos: escreve  $b$; move à direita; vai para  $q2$ ” | trecho: “Se está em $q_1$ lendo $a$ : escreve $b$ , move à direita, vai para $q_2$ ”
[147] categoria: Transições | termos: setas rotuladas  $a \rightarrow b; D$ | trecho: - Transições: setas rotuladas $a \rightarrow b, D$
[148] categoria: q<sub>0</sub> | termos: Estado inicial | trecho: - q<sub>0</sub>**: Estado inicial, representado por um círculo simples com uma seta rotulada "start" apontando para ele.
[149] categoria: q<sub>1</sub> | termos: Estado intermediário; representado por um círculo simples | trecho: - q<sub>1</sub>**: Estado intermediário, representado por um círculo simples.
[150] categoria: q<sub>acc</sub> | termos: Estado de aceitação; representado por um círculo duplo | trecho: - q<sub>acc</sub>**: Estado de aceitação, representado por um círculo duplo.
[151] categoria: De q<sub>0</sub> para q<sub>1</sub> | termos: Uma seta rotulada  $a \rightarrow X; R$ | trecho: - De **q<sub>0</sub>** para **q<sub>1</sub>**: Uma seta rotulada $a \rightarrow X, R$ .
[152] categoria: De q<sub>1</sub> para q<sub>acc</sub> | termos: Uma seta rotulada  $\sqcup \rightarrow \sqcup; L$ | trecho: - De **q<sub>1</sub>** para **q<sub>acc</sub>**: Uma seta rotulada $\sqcup \rightarrow \sqcup, L$ .
[153] categoria: Transição  $a \rightarrow X, R$ | termos: lendo  $a$; escreve  $X$; move à direita | trecho: Transição $a \rightarrow X, R$ : lendo $a$ , escreve $X$ , move à direita.
[154] categoria: MT para  $L = \{0^n 1^n | termos: n \geq 0\}$; com entrada  $w$ : | trecho: MT para $L = \{0^n 1^n : n \geq 0\}$ , com entrada $w$ :
[155] categoria: Estados | termos: $q0$ : estado inicial, procura 0 para marcar; $q1$ : movendo à direita, procurando 1; $q2$ : movendo à esquerda, voltando ao início; $q{acc}$ : aceita | trecho: ### Estados - $q_0$ : estado inicial, procura 0 para marcar
[156] categoria: $q2$ | termos: movendo à esquerda; voltando ao início | trecho: - $q_2$ : movendo à esquerda, voltando ao início
[157] categoria: Exemplo 2 | termos: b\}^\}$ | trecho: ##### Exemplo 2: $L = \{ww : w \in \{a, b\}^*\}$
[158] categoria: Decisor | termos: sempre para; com resposta correta | trecho: Decisor: sempre para, com resposta correta.
[159] categoria: União | termos: se  $L1; então  $L1 \cup L2$  é r.e | trecho: - União: se $L_1, L_2$ são r.e., então $L_1 \cup L_2$ é r.e.
[160] categoria: Interseção | termos: se  $L1; então  $L1 \cap L2$  é r.e | trecho: - Interseção: se $L_1, L_2$ são r.e., então $L_1 \cap L_2$ é r.e.
[161] categoria: Concatenação | termos: se  $L1; então  $L1 \cdot L2$  é r.e | trecho: - Concatenação: se $L_1, L_2$ são r.e., então $L_1 \cdot L_2$ é r.e.
[162] categoria: Fecho de Kleene | termos: se  $L$  é r.e; então  $L^$  é r.e | trecho: - Fecho de Kleene: se $L$ é r.e., então $L^*$ é r.e.
[163] categoria: Fatos Importantes | termos: Decidível  $\subset$  Reconhecível  $\subset$  Tod; Reconhecível  $\neq$  co-Reconhecível | trecho: ## Fatos Importantes - Decidível $\subset$ Reconhecível $\subset$ Todas
[164] categoria: 1 Trace a execução para as entradas | termos: $aabb$; $abab$; $aaaa$ | trecho: - 1 Trace a execução para as entradas: $aabb$ , $abab$ , $aaaa$
[165] categoria: 3  $L = \{w\#w | termos: w \in \{0 | trecho: - 3 $L = \{w\#w : w \in \{0, 1\}^*\}$ (verificar se duas cadeias são iguais)
[166] categoria: Especificação | termos: Saída:  $1^{m \times n}$  na fita | trecho: ### Especificação - Saída: $1^{m \times n}$ na fita
[167] categoria: MT como Reconhecedor de Linguagens | termos: Entrada: cadeia  $w$; Saída: Aceita ou Rejeita (ou loop); Decide se  $w \in L$ | trecho: ## MT como Reconhecedor de Linguagens - Entrada: cadeia $w$
[168] categoria: MT como Computador de Funções | termos: Entrada: valor  $x$  (codificado como cadeia); Saída: valor  $f(x)$  na fita (ou loop) | trecho: ## MT como Computador de Funções - Entrada: valor $x$ (codificado como cadeia)
[169] categoria: Uma função parcial  $f | termos: para toda entrada  $w$ : | trecho: Uma função parcial $f : \Sigma^* \rightarrow \Sigma^*$ é **Turing-computável** se existe uma MT $M$ tal que, para toda entrada $w$ :
[170] categoria: Entrada | termos: \dots; $\langle Me; y \rangle$; Uma codificação  $\langle M | trecho: - Entrada: $(n_1, \dots, n_k)$ codificado como $\text{bin}(n_1)\# \dots \# \text{bin}(n_k)$
[171] categoria: Saída | termos: \dots; nk)$  na mesma codificação; y)$ | trecho: - Saída: $f(n_1, \dots, n_k)$ na mesma codificação
[172] categoria: MT | termos: remove 1s de dois em dois; se sobrar 1; loop infinito | trecho: MT: remove 1s de dois em dois; se sobrar 1, loop infinito.
[173] categoria: Correspondência com MTs | termos: Função total  $\leftrightarrow$  MT que sempre par | trecho: ### Correspondência com MTs - Função total $\leftrightarrow$ MT que sempre para
[174] categoria: Se  $f | termos: então  $g \circ f$  também é | trecho: Se $f : \Sigma^* \rightarrow \Sigma^*$ e $g : \Sigma^* \rightarrow \Sigma^*$ são Turing-computáveis, então $g \circ f$ também é.
[175] categoria: Para computar  $f | termos: \mathbb{N}^k \rightarrow \mathbb{N}$; \dots; nk)$  como uma única cadeia | trecho: Para computar $f : \mathbb{N}^k \rightarrow \mathbb{N}$ , precisamos codificar $(n_1, \dots, n_k)$ como uma única cadeia.
[176] categoria: 3 Função de pareamento | termos: usar  $\langle n1; n2 \rangle$  recursivamente | trecho: - 3 **Função de pareamento:** usar $\langle n_1, n_2 \rangle$ recursivamente
[177] categoria: Finitos estados | termos: enumere como  $q0; q1; \dots; qn$ | trecho: - Finitos estados: enumere como $q_0, q_1, \dots, q_n$
[178] categoria: Finitas transições | termos: D)$ | trecho: - Finitas transições: liste cada $\delta(q_i, a) = (q_j, b, D)$
[179] categoria: $\langle M, w \rangle$  = codificação do par | termos: MT  $M$; entrada  $w$ | trecho: $\langle M, w \rangle$ = codificação do par (MT $M$ , entrada $w$ ).
[180] categoria: Podemos listar | termos: $M0; M1; M2; \dots$ | trecho: Podemos listar: $M_0, M_1, M_2, \dots$
[181] categoria: Estrutura de $U$ (3 fitas) | termos: Fita 1: Descrição de  $M$  (transições); Fita 3: Estado atual de  $M$ | trecho: #### Estrutura de $U$ (3 fitas) - **Fita 1:** Descrição de $M$ (transições)
[182] categoria: Simulação de um Passo | termos: 3 Encontre a transição aplicável | trecho: #### Simulação de um Passo - 3 Encontre a transição aplicável
[183] categoria: 4 Atualize | termos: símbolo na Fita 2; posição; estado na Fita 3 | trecho: - 4 Atualize: símbolo na Fita 2, posição, estado na Fita 3
[184] categoria: ( $\mu$ -recursiva $\Rightarrow$ Turing-computável) | termos: Composição: execute MTs em sequência; Recursão primitiva: use loop com contador; Minimização: busca sequencial (while) | trecho: #### **( $\mu$ -recursiva $\Rightarrow$ Turing-computável)** - Composição: execute MTs em sequência
[185] categoria: (Turing-computável $\Rightarrow$ $\mu$ -recursiva) | termos: Codifique configurações de MT como números; A função “próxima configuração” é recursiva primit; Use minimização para encontrar configuração de par | trecho: #### **(Turing-computável $\Rightarrow$ $\mu$ -recursiva)** - Codifique configurações de MT como números
[186] categoria: A noção informal de “função efetivamente computável” coincide com a noção formal de “funçã | termos: equivalentemente; $\mu$ -recursiva | trecho: A noção informal de “função efetivamente computável” coincide com a noção formal de “função Turing-computável” (equivalentemente, $\mu$ -recursiva).
[187] categoria: Evidências | termos: Máquinas de Turing; Funções  $\mu$ -recursivas; Cálculo Lambda; Máquinas de Post | trecho: #### Evidências - Máquinas de Turing
[188] categoria: Termos | termos: variáveis; $\lambda x.M$; $(M N)$ | trecho: - Termos: variáveis, $\lambda x.M$ , $(M N)$
[189] categoria: Base para linguagens funcionais | termos: Lisp; Haskell | trecho: - Base para linguagens funcionais (Lisp, Haskell)
[190] categoria: Instruções | termos: INC; DEC; JZ (jump if zero); Identifique corretamente as questões na folha de r | trecho: - Instruções: INC, DEC, JZ (jump if zero)
[191] categoria: Aritmética | termos: $\times$; primos; gcd | trecho: - Aritmética: $+$ , $\times$ , $!$ , primos, gcd
[192] categoria: Funções Computáveis (exemplos) | termos: Strings: concatenação, reverso, palíndromo; Ackermann: total mas cresce muito rápido | trecho: #### Funções Computáveis (exemplos) - Strings: concatenação, reverso, palíndromo
[193] categoria: Strings | termos: concatenação; reverso; palíndromo | trecho: - Strings: concatenação, reverso, palíndromo
[194] categoria: Busy Beaver parcial | termos: indefinida caso contrário | trecho: - Busy Beaver parcial: $BB'(n) = BB(n)$ se $n \leq 4$ , indefinida caso contrário
[195] categoria: Função de Parada | termos: 0 caso contrário | trecho: - Função de Parada: $h(e, x) = 1$ se $\varphi_e(x) \downarrow$ , 0 caso contrário
[196] categoria: Diagram showing the equivalence between four computational models | termos: Máquinas de Turing; Funções $\mu$-recursivas; Cálculo Lambda | trecho: Diagram showing the equivalence between four computational models: Máquinas de Turing, Funções $\mu$-recursivas, Cálculo Lambda, and Gramáticas Tipo 0. All four models are intercon
[197] categoria: 1 Se  $f | termos: \mathbb{N} \rightarrow \mathbb{N}$  é computável t | trecho: - 1 Se $f : \mathbb{N} \rightarrow \mathbb{N}$ é computável total, mostre que o conjunto $\{(x, f(x)) : x \in \mathbb{N}\}$ (o grafo de $f$ ) é decidível.
[198] categoria: Análise | termos: A árvore tem profundidade  $\leq t(n)$ | trecho: ### Análise - A árvore tem profundidade $\leq t(n)$
[199] categoria: Consequência para Complexidade | termos: Para computabilidade:  $\text{MTN} \equiv \text{MT | trecho: ### Consequência para Complexidade - Para computabilidade: $\text{MTN} \equiv \text{MTD}$
[200] categoria: Classe NP | termos: Linguagens decidíveis por MTN em tempo polinomial | trecho: ### Classe NP - Linguagens decidíveis por MTN em tempo polinomial.
[201] categoria: Demonstração de Equivalência | termos: Utilize duas fitas; Uma para posições  $\geq 0$; Versão alternativa: use uma fita "intercalada" | trecho: ### Demonstração de Equivalência - Utilize duas fitas
[202] categoria: Pode simplificar certos algoritmos, como verificar palíndromos | termos: um cabeçote no início | trecho: Pode simplificar certos algoritmos, como verificar palíndromos (um cabeçote no início, outro no fim).
[203] categoria: Resultados | termos: Existem MTs universais pequenas; Rogozhin (1996): várias combinações pequenas; Neary & Woods (2009): 2 estados e 18 símbolos | trecho: #### Resultados - Existem MTs universais pequenas
[204] categoria: Aceitação | termos: MT aceita  $w$  com probabilidade  $p$ | trecho: #### Aceitação - MT aceita $w$ com probabilidade $p$
[205] categoria: Classes de Complexidade | termos: BPP: tempo polinomial com erro bilateral; RP: tempo polinomial com erro unilateral | trecho: ### Classes de Complexidade - BPP: tempo polinomial com erro bilateral
[206] categoria: Poder Computacional | termos: Possivelmente mais eficiente para certos problemas; Algoritmo de Shor: fatoração em tempo polinomial q; Algoritmo de Grover: busca com speedup quadrático | trecho: ### Poder Computacional - Possivelmente mais **eficiente** para certos problemas
[207] categoria: Variações Equivalentes à MT Padrão | termos: MT com  $k$  fitas; MT com fita duplamente infinita; MT com fita bidimensional; MT com múltiplos cabeçotes | trecho: ### Variações Equivalentes à MT Padrão - MT com $k$ fitas
[208] categoria: Para Complexidade | termos: Multifita:  $O(t^2)$  slowdown | trecho: ### Para Complexidade - Multifita: $O(t^2)$ slowdown
[209] categoria: Exercício 2: Simulação de Multifita | termos: Como uma transição é simulada | trecho: ### Exercício 2: Simulação de Multifita - Como uma transição é simulada
[210] categoria: Decidível | termos: simule  $D$  em  $w$; sempre para em  $|w|$  passos; rejeite; senão | trecho: - Decidível: simule $D$ em $w$ , sempre para em $|w|$ passos.
[211] categoria: Linguagens Livres de Contexto | termos: Decidível: use algoritmo CYK (programação dinâmica | trecho: ### Linguagens Livres de Contexto - Decidível: use algoritmo CYK (programação dinâmica).
[212] categoria: $\{n | termos: n \text{ é primo}\}$; teste de primalidade (AKS) | trecho: - $\{n : n \text{ é primo}\}$ , teste de primalidade (AKS)
[213] categoria: Para toda  $w$ | termos: então  $M$  sempre para | trecho: - Para toda $w$ : ou $w \in L$ ou $w \in \bar{L}$ , então $M$ sempre para.
[214] categoria: Estrutura (3 fitas) | termos: 3 Fita 3: Estado atual de  $M$ | trecho: ### Estrutura (3 fitas) - 3 **Fita 3:** Estado atual de $M$
[215] categoria: 2 Inicialize | termos: copie  $w$  para Fita 2; $q0$  para Fita 3 | trecho: - 2 Inicialize: copie $w$ para Fita 2, $q_0$ para Fita 3
[216] categoria: Algoritmo | termos: 3 Repita:; Busque transição para (estado, símbolo) na Fita 1 | trecho: ### Algoritmo - 3 Repita:
[217] categoria: Atualize | termos: símbolo na Fita 2; posição; estado na Fita 3 | trecho: - Atualize: símbolo na Fita 2, posição, estado na Fita 3
[218] categoria: Interpretadores e Compiladores | termos: Interpretador: implementação direta de MT Universa; Recebe código-fonte + entrada, executa passo a pas | trecho: ### Interpretadores e Compiladores - **Interpretador:** implementação direta de MT Universal
[219] categoria: Caso 1: $D$ para em $\langle D \rangle$ | termos: Então  $D$  entra em loop infinito (pela construçã | trecho: #### Caso 1: $D$ para em $\langle D \rangle$ - Então $D$ entra em loop infinito (pela construção)
[220] categoria: Suponha que  $A{TM}$  seja decidível com decisor  $A$ . Construa decisor  $H'$  para  $HAL | termos: na entrada  $\langle M; w \rangle$ : | trecho: Suponha que $A_{TM}$ seja decidível com decisor $A$ . Construa decisor $H'$ para $HALT$ : na entrada $\langle M, w \rangle$ :
[221] categoria: Contrapositiva | termos: Se  $A$  é indecidível e  $A \leqm B$; então  $B$  é indecidível | trecho: Contrapositiva: Se $A$ é indecidível e $A \leq_m B$ , então $B$ é indecidível.
[222] categoria: Construa redução  $f$ | termos: dado  $\langle M; w \rangle$; produza  $\langle M' \rangle$  onde  $M'$; na entrada  $x$ : | trecho: Construa redução $f$ : dado $\langle M, w \rangle$ , produza $\langle M' \rangle$ onde $M'$ , na entrada $x$ :
[223] categoria: O diagrama ilustra a hierarquia dos problemas de decisão. Um grande oval preto, rotulado ' | termos: mas fora da interseção | trecho: O diagrama ilustra a hierarquia dos problemas de decisão. Um grande oval preto, rotulado 'Todas as Linguagens', contém dois ovais menores que se sobrepõem: um azul rotulado 'R.E.' 
[224] categoria: Decidíveis | termos: $A{DFA}$; $E{DFA}$; $A{CFG}$; primalidade | trecho: - **Decidíveis:** $A_{DFA}$ , $E_{DFA}$ , $A_{CFG}$ , primalidade
[225] categoria: Conceitos Principais | termos: MT Universal: simula qualquer outra MT; Existem problemas indecidíveis (HALT,  $A{TM}$ ); Diagonalização: técnica fundamental para provas de; Reduções: técnica para transferir indecidibilidade | trecho: ## Conceitos Principais - MT Universal: simula qualquer **outra** MT
[226] categoria: Existem problemas indecidíveis | termos: HALT; $A{TM}$; Halting; Entscheidungsproblem | trecho: - Existem problemas indecidíveis (HALT, $A_{TM}$ )
[227] categoria: Importância | termos: Verificação de software: garantir que programas te; Compiladores: otimizações dependem de análise de t; Depuração: detectar loops infinitos automaticament | trecho: ### Importância - Verificação de software: garantir que programas terminam
[228] categoria: $\Gamma$ | termos: \sqcup \in \Gamma$ ) | trecho: - $\Gamma$ : alfabeto da fita ( $\Sigma \subseteq \Gamma, \sqcup \in \Gamma$ )
[229] categoria: $q0, q{accept}, q{reject} \in Q$ | termos: estados inicial; de aceitação e rejeição | trecho: - $q_0, q_{accept}, q_{reject} \in Q$ : estados inicial, de aceitação e rejeição
[230] categoria: Qualquer MT  $M$  pode ser codificada como uma string  $\langle M \rangle$  sobre um alfab | termos: ex:  $\{0 | trecho: Qualquer MT $M$ pode ser codificada como uma string $\langle M \rangle$ sobre um alfabeto fixo (ex: $\{0, 1\}$ ).
[231] categoria: Método: Prova por Contradição + Diagonalização | termos: 2 Construir uma nova MT  $D$  usando  $H$; 3 Mostrar que  $D$  leva a uma contradição | trecho: ### Método: Prova por Contradição + Diagonalização - 2 Construir uma nova MT $D$ usando $H$
[232] categoria: Diagram illustrating the construction of machine D. An input  enters a dashed box labeled  | termos: one labeled 'se aceita' leading to 'loop $\infty$'; and another labeled 'se rejeita' leading to 'para' | trecho: Diagram illustrating the construction of machine D. An input enters a dashed box labeled D. Inside D is a box labeled H. From the output of H, two paths emerge: one labeled 'se ace
[233] categoria: 1 Entrada | termos: $\langle M; w \rangle$ | trecho: - 1 Entrada: $\langle M, w \rangle$
[234] categoria: Então | termos: w \rangle \in A{TM}$ | trecho: Então: $M$ para em $w \iff M'$ aceita $w \iff \langle M', w \rangle \in A_{TM}$
[235] categoria: Podem requerer anotações do programador | termos: invariantes; variantes | trecho: - Podem requerer **anotações** do programador (invariantes, variantes)
[236] categoria: Exemplos Reais | termos: Analisadores estáticos: falsos positivos/negativos | trecho: ## Exemplos Reais - **Analisadores estáticos:** falsos positivos/negativos
[237] categoria: Exercício 5: Aplicações Práticas | termos: 2 Considere o seguinte código: | trecho: ### Exercício 5: Aplicações Práticas - 2 Considere o seguinte código:
[238] categoria: [2] Alonzo Church. “An Unsolvable Problem of Elementary Number Theory”. Em | termos: American Journal of Mathematics 58:2 (1936); pp. 345–363; American Journal of Mathematics 58.2 (1936) | trecho: - [2] Alonzo Church. “An Unsolvable Problem of Elementary Number Theory”. Em: *American Journal of Mathematics* 58:2 (1936), pp. 345–363.
[239] categoria: [5] Marvin L. Minsky. Computation | termos: Finite and Infinite Machines. Prentice-Hall | trecho: - [5] Marvin L. Minsky. *Computation: Finite and Infinite Machines*. Prentice-Hall, 1967.
[240] categoria: [8] Alan M. Turing. “On Computable Numbers, with an Application to the Entscheidungsproble | termos: pp. 230–265 | trecho: - [8] Alan M. Turing. “On Computable Numbers, with an Application to the Entscheidungsproblem”. Em: *Proceedings of the London Mathematical Society* 42.1 (1936), pp. 230–265.
