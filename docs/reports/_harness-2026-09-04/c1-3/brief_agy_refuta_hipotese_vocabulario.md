# REFUTE esta hipótese — motor de atribuição curricular, 2026-09-13

Você é um refutador independente. **Seu trabalho é DERRUBAR a hipótese abaixo, não confirmá-la.** Se ela sobreviver,
diga o que sobreviveu e o que continua sem evidência. Separe MEDIDO de JULGAMENTO. Não invente número.

## O sistema, em 5 linhas

Um motor atribui cada material didático de um curso a três eixos: **bloco** (qual semana/aula), **unidade** (qual
unidade do plano de ensino) e **subunidade** (qual subtópico dentro da unidade). O motor tem uma camada de
vocabulário: um sidecar por curso que mapeia termos dos materiais para tópicos do plano
(`"Modelos Preditivos": {"synonyms": ["perceptron", "k-NN", "Árvores de Decisão"]}`).
Há dois regimes: **cru** (sem o sidecar compilado por LLM) e **produto** (com ele, mais um voter de LLM em runtime).
A meta posta pelo dono do projeto é **90% de acurácia total nos três eixos, no regime cru**.

## Os números MEDIDOS (motor completo, rede bloqueada, 0 chamadas)

| eixo | cru | produto | meta 90% |
|---|---|---|---|
| bloco (237 materiais) | 93,7% | 99,2% | ✅ já bate |
| unidade (284) | 89,1% | 92,6% | faltam 3 materiais |
| **subunidade (251)** | **142 = 56,6%** | 224 = 89,2% | **faltam 84 materiais** |

O vocabulário compilado por LLM sozinho vale **+29,4 pontos na subunidade** (e só +0,7 na unidade, −0,4 no bloco).
Por isso o vocabulário vinha sendo tratado como a alavanca principal.

## O diagnóstico que gerou a hipótese

Os 109 erros de subunidade do regime cru foram classificados material a material, com o *bundle* que um adquiridor de
vocabulário receberia (título + label do Moodle + até 24 headings) e o catálogo completo de tópicos do curso:

| classe | definição | n |
|---|---|---|
| C | competição: a evidência do tópico certo já está no texto e já pontua, mas outro candidato vence | **38** |
| B | a expressão de domínio está no material, falta a relação termo→tópico | **32** |
| A | nenhuma expressão do material liga ao tópico certo | **23** |
| D | gold vazio, cronograma, assunto sem subtópico correspondente | **16** |

Distribuição de B por curso: **IA 29** · CG 1 · ES2 1 · SO 1 · MF 0 · FR 0 · TCC 0.

E um recorte: em **23 dos 109** a evidência decisiva existe no arquivo mas **não chega ao bundle** — CG 11 (o corte em
24 headings esconde um arquivo que é o 26º de 43), MF 5 (`language: "isabelle"` está no frontmatter, campo que o
bundle não lê), FR 4 (os zips dizem `socket` de 2 a 5 vezes por arquivo, mas o bundle só expõe nome de zip), ES2 3
(`@FeignClient`, `@EnableEurekaServer` estão dentro dos `.java`).

**Como isso foi produzido:** 7 agentes de LLM diagnosticaram (um por curso) e 6 refutadores atacaram só a classe B,
derrubando 13 alegações. **É julgamento por leitura, com refutação adversarial. NÃO é ganho medido no motor.**

## A HIPÓTESE QUE VOCÊ DEVE DERRUBAR

> **"Parar de tratar vocabulário como a alavanca principal da subunidade. A aquisição de vocabulário entrega no
> máximo 32 dos 84 materiais que faltam, e 29 desses 32 são um curso só (IA). Somando a classe C (38, competição)
> com os 23 de bundle, há mais material nas alavancas de engenharia determinística — que não precisam de LLM — do
> que na aquisição de vocabulário."**

## Ataque a hipótese por estes vetores, e acrescente os que eu não listei

1. **A soma 38 + 23 é legítima?** As duas classes se sobrepõem? Um material pode ser C e também ter evidência fora do
   bundle? Se sim, a comparação "61 contra 32" é inflada e por quanto?
2. **"Teto de 32" é teto mesmo?** O teto foi medido sobre os erros ATUAIS. Se uma alavanca de engenharia corrigir 20
   materiais, os erros restantes mudam de natureza — e o teto da aquisição sobre o conjunto NOVO pode ser outro. A
   ordem de ataque muda o tamanho do prêmio de cada alavanca?
3. **O argumento "91% do teto é um curso" se vira contra a própria hipótese?** Se os erros se concentram no IA, e o
   IA é 34 dos 109, a conclusão correta não seria "resolver o IA" em vez de "abandonar o vocabulário"?
4. **Classe C é mesmo tratável sem vocabulário?** "A evidência já pontua e perde" pode significar que ela pontua
   POUCO justamente porque falta vocabulário que a reforce. Separar C de B por leitura é confiável?
5. **O viés do instrumento:** os diagnosticadores viram o gold. A instrução dizia "use o gold só como referência de
   avaliação, não invente ligação porque o gold diz que o alvo é aquele". Isso basta? Como esse viés empurraria a
   contagem — para mais B ou para mais C?
6. **O custo omitido:** engenharia de bundle mexe no pipeline de extração, que alimenta os TRÊS eixos. Vocabulário
   mexe num sidecar isolado. O risco de regressão nos eixos que já batem a meta (bloco 93,7%) foi considerado?
7. **A aritmética final:** 142 + 32 = 174/251 = 69,3%. Mesmo somando 61 de engenharia, 142 + 61 = 203/251 = 80,9%.
   **Nenhuma das duas chega a 90%.** A hipótese resolve o problema do dono do projeto, ou só troca de alavanca?

## O que devolver

1. **Veredito:** a hipótese cai, sobrevive parcialmente, ou sobrevive? Uma frase.
2. **Os vetores em que ela cai**, com o raciocínio, e o que a versão corrigida da hipótese deveria dizer.
3. **O teste decisivo** que separaria as duas teorias (vocabulário × engenharia) com o menor esforço — e que não
   dependa de julgamento de LLM.
4. **O que você NÃO consegue avaliar** com o que está neste documento.
