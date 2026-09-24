# Piloto de conhecimento externo — declaração pré-registrada (23/09/2026)

Escrita **antes** da aquisição e antes de qualquer contato do candidato com o gold. Segue
`docs/plans/piloto-conhecimento-externo-desenho.md` (fc4a9466). Regime experimental separado; o cru não muda; nada em
`src/`.

## Base fixada

- Código: HEAD `fc4a9466` + o fix da #50 do worktree (5 arquivos, `git diff -- src tests` sha256 `c80d309b…`). É a mesma
  árvore em que o replay de preservação reproduziu a captura congelada da base v2 (`f941ac33…`).
- Insumos: raízes da base v2 (as mesmas do W-Z2), régua v2 congelada, denominadores históricos (bloco 237, unidade 284,
  subunidade primária 251). Os 5 casos do CG seguem no denominador; serão só identificados.
- Nenhuma correção simultânea (frases_topico, normalização de acentos, propagação, régua, configuração).

## Fontes

| fonte | decisão | origem / versão | condições |
|---|---|---|---|
| ConceptNet 5.7.0 | **usar** | `https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz`, 497.963.447 bytes, Last-Modified 2019-07-03, ETag `9728310bd5184a3045f1b7bacdb936ce-29` | CC BY-SA 4.0 (wiki oficial "Copying and sharing ConceptNet"): atribuição obrigatória; share-alike ao compartilhar dados derivados. As partes WordNet e Open Multilingual WordNet já vêm com licenças permissivas próprias. Uso local no experimento é compatível. O léxico derivado **não é redistribuído**: fica em `.frzero/` (ignorado pelo git); o repositório guarda só hashes e proveniência |
| ACM CCS 2012 | **não usar (pendência)** | dl.acm.org/ccs (SKOS) | só "freely available for educational and research purposes", sem licença formal; além disso é só em inglês e classifica áreas de pesquisa. Pendência: termos de uso explícitos para este fim |
| Wikidata | **não usar** | dumps / SPARQL | CC0, mas um recorte geral não cabe no piloto: o dump tem centenas de GB e o fecho de "subclasse de" pelo SPARQL público estoura o tempo limite. Recortar pelos rótulos dos planos violaria a regra de recorte geral |

Cobertura do ConceptNet: grafo geral multilíngue (senso comum e léxico: Wiktionary, WordNet, OMW, DBpedia etc.), não
específico de computação nem dos cursos.

## Recorte (geral, sem olhar o benchmark)

Do dump inteiro, ficam as arestas com relação `/r/IsA` ou `/r/Synonym` cujas duas pontas estão em `/c/en/` ou
`/c/pt/`. Não há filtro por domínio, curso, material ou erro. Cada aresta guarda a proveniência: URI, relação, pontas,
dataset e licença do campo JSON. O peso das arestas é ignorado.

## Regras de transformação (fixas)

1. Texto do conceito = 3º segmento da URI (`/c/<língua>/<termo>/…`), com `_` → espaço.
2. Chave de comparação: NFKD sem acentos, minúsculas, espaços colapsados.
3. Frases do tópico: rótulo, aliases do plano e partes do rótulo (`timeline.index._label_parts(rótulo, set())`). Cada
   frase casa com o conceito de chave igual (en ou pt). Variante adicional só do lado do tópico: singular do português
   por regra geral, palavra a palavra (-ões/-ães→-ão, -ais→-al, -eis→-el, -óis→-ol, -ns→-m, vogal+s→vogal).
4. Expansão a partir dos conceitos casados M(T):
   - S(T) = M(T) ∪ vizinhos por `Synonym` (1 salto, os dois sentidos; inclui tradução en↔pt);
   - H(T) = {x : `IsA`(x, s), s ∈ S(T)}, 1 salto, só hipônimos.
5. Aliases KE de T = textos de S(T) ∪ H(T) que ainda não são frases do tópico. Higiene: ≥ 4 caracteres, não numérico, e
   token único não pode ser stem genérico do motor (`MOTOR_GENERIC_STEMS`). Nada é ajustado depois.

**Por que hipônimo vira alias da categoria (e não o contrário).** O plano nomeia a categoria e o material nomeia o caso
específico (W-Z2: F6/F7 = relação ausente). O alias é evidência **direcional**: quando o material cita o hipônimo, isso
conta para o tópico-categoria. Hiperônimos não viram alias (seria o sentido inverso), e `RelatedTo` e as demais relações
associativas ficam fora. Cada alias guarda a aresta de origem; nenhuma relação vira sinônimo universal.

## Integração (ponto único do desenho)

- A taxonomia estendida (plano + aliases KE, peso de alias 0,82 igual ao do plano) é entregue **só ao mapeador de
  subtópico** (`auto_sub`), na 1ª e na 2ª passada. Na 2ª passada ela se funde com a taxonomia que a própria 2ª passada
  estende.
- Não tocados: rota de unidade, bloco, vocabulário da propagação (`vocab_unit`), partes de rótulo, `frases_topico` e
  genéricos, que dependem só dos rótulos.
- Asserção: bloco e unidade idênticos por ID à baseline. Se falhar, a divergência é reportada e não conta como aceite.
- Parâmetros ajustados: nenhum, portanto LOCO não se aplica. Cursos estudados = desenvolvimento, não holdout.

## Execução e congelamento

1. Aquisição (única etapa com rede), com sha256 do arquivo baixado.
2. Construção do léxico e da tabela de aliases por (curso, unidade, tópico), com sha256. Nenhuma entrada vem do gold, de
   previsões, de IDs de materiais nem de conhecimento do agente.
3. Replays locais com tripwires de rede (`connect`, `connect_ex`, `create_connection`, `getaddrinfo`, cliente Gemini):
   baseline (sem KE) e candidato (com KE), mesma instrumentação. A baseline tem de reproduzir a captura congelada
   `f941ac33…` por ID. As decisões dos dois braços são congeladas por sha256 **antes** de ler o gold.

## Medidas (por curso e total, denominadores históricos)

- Inclusão do tópico-gold entre os candidatos (score exato > 0 na unidade prevista, 1ª passada), baseline × candidato,
  e o tamanho do conjunto de candidatos (ambiguidade).
- Escolha final da subunidade primária; correções e perdas por ID.
- Abstenções convertidas em decisão certa ou errada.
- Precisão das decisões novas ou alteradas.
- Preservação de bloco e unidade por ID.
- Tempo e memória de pico (RSS) de cada braço.

Maior cobertura de candidatos não é aceite de integração. Aceite de integração, se um dia for proposto: ganho positivo,
zero perda dos acertos atuais, nenhum curso regride, demais eixos preservados e replay integral.

Atribuição: ConceptNet 5, Commonsense Computing Initiative (Speer, Chin e Havasi, 2017), http://conceptnet.io, CC BY-SA
4.0.
