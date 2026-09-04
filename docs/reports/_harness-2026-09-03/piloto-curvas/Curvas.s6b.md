# Curvas

## Conteúdo Extraído
**Computação Gráfica**

**Curvas Paramétricas**

[Prof.Dr. Márcio Sarroglia Pinho](https://www.inf.pucrs.br/pinho)

***Introdução***

A forma mais comum de representação de curvas é aquela em que uma das coordenadas é obtida em função da outra. Ou seja, y = F(x) ou x = F(y)

Esta forma de representação, porém possui alguns inconvenientes quando estamos trabalhando com modelagem geométrica. Entre estes inconvenientes estão:

- é difícil definir a equação de uma curva através de seus pontos e de suas derivadas neste pontos (o que é bastante útil em modelagem geométrica);

![Figura: Diagrama que ilustra o conceito do cálculo de variações, mostrando um caminho real (linha contínua) e um caminho variado (linha tracejada) que ligam os pontos P1 e P2.](content/images/curvas-image003.gif)

- é impossível criar curvas com laços;

- é bastante difícil obter uma curva suave que passe por um conjunto de pontos.

![Figura: Gráfico que ilustra uma curva suave de interpolação conectando quatro pontos azuis dispostos sobre um fundo preto.](content/images/curvas-interpola.gif)

***Curvas paramétricas***

A primeira classe de curvas paramétricas é aquela em que o comportamento da curva, ao longo do tempo, em relação a cada um dos eixos é definida por uma equação independente. A forma geral destas curvas pode ser expressa por :

x = F(u) y = F(u)

Exemplos do uso desta formulação podem ser:

- Cálculo da trajetória de um projétil

A posição vertical(y) é independente da posição horizontal(x). Ambas são funções da variável "tempo".

- a equação paramétrica do círculo de raio 1 com centro na origem, para t entre 0o e 360o

x = cos(t) y = sin(t)

- a equação paramétrica do círculo de raio R com centro em (CX,CY), para t entre 0o e 360o

x = cos(t) * R + CX y = sin(t) * R + CY

- a curva

x = sen(t) y = t * t

O uso deste tipo de técnica para a criação de curvas paramétricas é bastante útil em um processo de modelagem. Porém, não soluciona dois dos problemas levantados para as curvas da forma Y = F(X):

- criação de curvas a partir dos pontos por onde ela deve passar;

- criação de curvas dados os pontos e as derivadas da curva nestes pontos.

***Composições ponderadas***

Às técnicas de obtenção de equações de curvas dados seus pontos e suas derivadas, chama-se, normalmente, **interpolação**, **aproximação** ou **composição ponderada**. Destas técnicas destacam-se 3 formulações: **curvas Bèzier, curvas Hermite e curvas Spline**.

***Curvas BÉZIER***

Analisando a equação paramétrica da reta entre os ponto P0 e P1 chega-se a conclusão de que trata-se de uma média ponderada, ou de um balanço, entre P0 e P1 onde o peso de cada ponto é definido de forma que quanto mais um deles pese no resultado, menos o outro influencie no mesmo.

![Figura: Um segmento de reta que conecta dois pontos rotulados como P0 e P1.](content/images/curvas-reta.gif)

Para obter esta ponderação os pesos de P0 e de P1 podem ser expressos pela funções (para o parâmetro ponderador "t" entre 0 e 1):

Peso de P0 = 1 - T Peso de P1 = T

Com isto a equação paramétrica da reta fica: P(t) = (1-t) * P0 + t * P1

Curvas Bèzier por 3 pontos

Caso seja preciso ponderar 3 pontos (P0, P1 e P2) gerando uma curva, a formulação é bastante semelhante:

Considerando duas retas R1 e R2, respectivamente, entre P0 e P1 e entre P1 e P2, representadas na forma paramétrica apresentada acima, é possível obter uma curva P0-P1-P2 fazendo simplesmente a ponderação entre R1 e R2 usando para isto os pesos "T" e "1 - T".

O desenvolvimento analítico desta idéia é o seguinte:

Sejam R1 e R2 as referidas retas definidas parametricamente por,

R1: (1-t) * P0 + t * P1

R2: (1-t) * P1 + t * P2

![Figura: Um diagrama mostrando uma curva C1 e seus pontos de controle P0, P1 e P2. A curva começa em P0, atinge o pico e termina em P2, com P1 atuando como ponto de controle acima do arco.](content/images/curvas-bezier3pontos.gif)

**Exemplo de curva Bèzier por 3 pontos**

Reaplicando novamente a idéia de ponderação tem-se a curva C1 definida pela seguinte equação:

**C1 : (1-t) * R1 + t * R2**

que ao ser desenvolvida dá origem a

**C1(t) = (1-t)2 * P0 + 2 * (1-t) * t * P1 + t2 * P2**

para t entre 0 e 1.

Curvas Bèzier por 4 pontos

A obtenção das curvas Bèzier para 4 pontos (P0-P1-P2-P3) segue o mesmo raciocínio, desta feita, ponderando duas curvas, **C1**->(P0-P1-P2) e **C2**->(P1-P2-P3). O desenvolvimento desta idéia é o seguinte, com base na figura abaixo:

![Figura: Um diagrama mostrando uma curva C1 e um caminho linear por partes C2 conectando os pontos P0, P1, P2 e P3.](content/images/curvas-DuasBz3Ptos.gif)

Dadas as curvas C1 e C2, definidas parametricamente, em função de "t", a curva C3 pode ser expressa por:

**C3 = (1-t) * C1 + t * C2**

cujo desenvolvimento resulta em

**C3(t) = (1-t)3 * P0 + 3 * t * (1-t)2 * P1 + 3 * t2 * (1-t) * P2 + t3 * P3**

![Figura: Um gráfico mostrando uma curva azul sobre um fundo preto com quatro pontos de controle vermelhos. A curva começa no canto inferior esquerdo, sobe até um pico, cai até um vale e depois sobe novamente. Os pontos de controle estão localizados no início e no fim da curva, e dois pontos adicionais estão posicionados acima e abaixo da trajetória da curva.](content/images/curvas-bezier4pontos.gif) **Exemplo de curva Bèzier por 4 pontos**

Formas alternativas de traçado de uma Bèzier

![Figura: Um diagrama mostrando um caminho de P0 a P1 a P2. O segmento de P0 a P1 é verde, e o segmento de P1 a P2 é cinza. P0 é um ponto preto preenchido, P1 é um ponto verde e P2 é um círculo aberto. O rótulo t=0 está posicionado abaixo do caminho.](content/images/curvas-image001.gif)![Figura: Um diagrama mostrando uma sequência de pontos P0, P1, P2 e P3 conectados por segmentos de reta coloridos. P0 é um ponto preto, P1 é um ponto azul, P2 é um ponto verde e P3 é um círculo vazado. O segmento P0-P1 é azul, P1-P2 é verde e P2-P3 é cinza. O rótulo t=0 está posicionado abaixo do segmento P1-P2.](content/images/curvas-image002.gif)

https://en.wikipedia.org/wiki/B%C3%A9zier_curve

Exemplos:

- Curvas Bezier e os fontes TrueType: https://jdhao.github.io/2018/11/27/font_shape_mathematics_bezier_curves/
- Editor: http://math.hws.edu/eck/cs424/notes2013/canvas/bezier.html

***Curvas HERMITE***

Tentando solucionar o problema de definição de uma curva dados seus pontos extremos e as derivadas nestes pontos surgiu a formulação de HERMITE. O desenvolvimento desta formulação vem a seguir.

Uma curva de grau 3 genérica pode ser expressa por

**P(t) = a * t3 + b * t2 + c * t + d (1)**

Se for necessário criar uma curva P(t), para t entre 0 e 1, que tenha os extremos nos pontos P0 e P3 e tenha como derivadas, nestes pontos, os vetores V0 e V3 respectivamente, tem-se como verdadeiras as seguintes definições:

**P(****0) = P0 P(1) = P3 (2)**

**P'(0) = V0 P'(1) = V3 (3)**

**P'(t) = 3 * a * t2 + 2 * b * t + c (4)**

Colocando as equações (1) e (4) na forma matricial(a fim de facilitar os cálculos) teremos:

Equação (1):

$$P(t) = \begin{bmatrix} t^3 & t^2 & t & 1 \end{bmatrix} \begin{bmatrix} a \\ b \\ c \\ d \end{bmatrix}$$
<sub>fonte: [Image1.gif](content/images/curvas-Image1.gif)</sub>

Equação (4):

$$P'(t) = \begin{bmatrix} 3t^3 & 2t^2 & t & 0 \end{bmatrix} \begin{bmatrix} a \\ b \\ c \\ d \end{bmatrix}$$
<sub>fonte: [Image2.gif](content/images/curvas-Image2.gif)</sub>

Objetivo agora é obter os valores das entradas da matriz-coluna, a qual dá-se o nome de matriz de coeficientes.

Para isto, substitui-se, nesta forma de representação, as afirmativas de (2) e (3) obtendo-se 4 equações.

$$P(1) = \begin{bmatrix} 1 & 1 & 1 & 1 \end{bmatrix} \begin{bmatrix} a \\ b \\ c \\ d \end{bmatrix}$$
<sub>fonte: [Image3.gif](content/images/curvas-Image3.gif)</sub>

 

$$P(0) = \begin{bmatrix} 0 & 0 & 0 & 0 \end{bmatrix} \begin{bmatrix} a \\ b \\ c \\ d \end{bmatrix}$$
<sub>fonte: [Image4.gif](content/images/curvas-Image4.gif)</sub>

$$p'(0) = \begin{bmatrix} 0 & 0 & 1 & 0 \end{bmatrix} \begin{bmatrix} a \\ b \\ c \\ d \end{bmatrix}$$
<sub>fonte: [Image5.gif](content/images/curvas-Image5.gif)</sub>

 

$$P'(1) = \begin{bmatrix} 3 & 2 & 1 & 0 \end{bmatrix} \begin{bmatrix} a \\ b \\ c \\ d \end{bmatrix}$$
<sub>fonte: [Image6.gif](content/images/curvas-Image6.gif)</sub>

Como queremos obter os valores de 4 incógnitas (a,b,c,d) podemos colocar as 4 equações numa notação matricial:

Isolando a matriz de coeficientes(que é o objetivo deste processo) temos a seguinte equação matricial:

$$\begin{bmatrix} a \\ b \\ c \\ d \end{bmatrix} = \begin{bmatrix} 2 & -2 & 1 & 1 \\ -3 & 3 & -2 & -1 \\ 0 & 0 & 1 & 0 \\ 1 & 0 & 0 & 0 \end{bmatrix} \begin{bmatrix} p(0) \\ p(1) \\ p'(0) \\ p'(1) \end{bmatrix}$$
<sub>fonte: [Image7.gif](content/images/curvas-Image7.gif)</sub>

À matriz-coluna, de pontos e de derivadas dá-se o nome de matriz geometria de Hermite(MGh), e à matriz 4x4, matriz de Hermite(Mh).

Logo a equação (1)

$$P(t) = \begin{bmatrix} t^3 & t^2 & t & 1 \end{bmatrix} \begin{bmatrix} a \\ b \\ c \\ d \end{bmatrix}$$
<sub>fonte: [Image8.gif](content/images/curvas-Image8.gif)</sub>

pode ser reescrita como:

$$P(t) = \begin{bmatrix} t^3 & t^2 & t & 1 \end{bmatrix} \mathbf{M}_h \quad \mathbf{M}_G h$$
<sub>fonte: [Image9.gif](content/images/curvas-Image9.gif)</sub>

Esta equação, que ao ser desenvolvida gera:

$$P(t) =$$

$$P(0) * (2t^3 - 3t^2 + 1) +$$

$$P(1) * (-2t^3 + 3t^2) +$$

$$P'(0) * (t^3 - 2t^2 + t) +$$

$$P'(1) * (t^3 - t^2)$$
<sub>fonte: [EquacaoHermite.png](content/images/curvas-EquacaoHermite.png)</sub>

A especificação das derivadas em P0 e P3 deve ser feita através de vetores, conforme a figura abaixo.

![Figura: Animação gráfica que ilustra a determinação da distância entre dois pontos no plano cartesiano por meio do Teorema de Pitágoras.](content/images/curvas-vetor.gif)

A influência destes vetores no comportamento da curva se dá pela determinação de como a curva sai do ponto inicial e chega ao ponto final.

![Figura: Diagrama 1: Uma curva vermelha conectando o nó 1 ao nó 3, com linhas pretas verticais nos nós 1 e 3. Diagrama 2: Uma curva vermelha conectando o nó 1 ao nó 3, com linhas pretas verticais nos nós 1 e 3. Diagrama 3: Uma curva vermelha conectando o nó 1 ao nó 3, com uma linha diagonal no nó 1 e uma linha horizontal no nó 3. Diagrama 4: Uma curva vermelha conectando o nó 1 ao nó 3, com uma linha horizontal no nó 1 e uma linha diagonal no nó 3.](content/images/curvas-image004.png)

**Exemplos de Curvas Hermite**

Exemplo: https://codepen.io/liorda/pen/KrvBwr

***Curvas SPLINE***

$$p(t) = \frac{1}{6} [P_0 * (-t^3 + 3t^2 - 3t + 1) + P_1 * (3t^3 - 6t^2 + 4) + P_2 * (-3t^3 + 3t^2 + 3t + 1) + P_3 * (t^3)]$$
<sub>fonte: [Image11.gif](content/images/curvas-Image11.gif)</sub>

![Figura: Diagrama de um retângulo com vértices rotulados de 1, 2, 3, 4 e um arco vermelho conectando os cantos superior esquerdo e superior direito. Diagrama de uma forma em V com vértices rotulados de 1, 2, 3, 4 e um arco vermelho conectando os cantos superior esquerdo e superior direito. Diagrama de um retângulo com vértices rotulados de 1, 2, 3, 4 e um arco vermelho conectando os cantos superior esquerdo e superior direito. Diagrama de uma forma complexa com vértices rotulados de 1 a 12 e um arco vermelho conectando os cantos superior esquerdo e superior direito.](content/images/curvas-image005.png)

**Exemplos de Curvas Spline**

***CATMULL - ROM***

Montada a partir de uma sequência de curvas Hermite. O cálculo das tangentes de forma automática a partir dos quatro pontos fornecidos pelo usuário.

Para gerar a curva, traça-se uma Hermite entre cada par de pontos.

A curva passa pelos pontos definidos pelo usuário (menos o primeiro e o último).

![Figura: Um diagrama geométrico que mostra um caminho através dos pontos 1, 2, 3, 4, 5 e 6. Ele inclui segmentos de reta pretos conectando 1-2, 2-3, 3-4, 4-5 e 5-6. Uma curva vermelha conecta os pontos 2, 3, 4 e 5. Segmentos de reta azuis são tangentes à curva vermelha nos pontos 2, 3 e 5.](content/images/curvas-image006.png)

**Exemplo de Curva Catmull-Rom**

A tangente em cada ponto é dada por:

$$p_i = \frac{(p_i - p_{i-1}) + (p_{i+1} - p_i)}{2}$$
<sub>fonte: [image007.png](content/images/curvas-image007.png)</sub>

Vantagens

- Continuidade garantida de forma automática
- Possui a propriedade do controle local nos pontos de controle
- A curva passa pelos pontos de controle (menos o primeiro e o último)

Exemplo: https://qroph.github.io/2018/07/30/smooth-paths-using-catmull-rom-splines.html

**FIM.**
