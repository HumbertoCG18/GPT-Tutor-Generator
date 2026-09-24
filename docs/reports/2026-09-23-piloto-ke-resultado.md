# Piloto de conhecimento externo (regime experimental separado) — resultado, 23/09/2026

**Resultado experimental, não uma melhoria aprovada.** O candidato derruba a subunidade primária de 86 para 77/251,
com 16 perdas de acertos atuais e três cursos regredindo (MF, ES2, FR); bloco e unidade não mudam.
**Recomendação: encerrar este mecanismo** (léxico geral do ConceptNet injetado pelo canal de alias). Nenhuma variante
foi iniciada. Não houve mudança em `src/`, na régua ou no regime cru.

Artefatos: `c1-3/piloto_ke_declaracao_23-09.md` (pré-registro), `piloto_ke_lexico_23-09.{py,json}`,
`piloto_ke_execucao_23-09.py`, `piloto_ke_congelamento_23-09.json`, `piloto_ke_resultado_23-09.json`. O dump, o léxico,
a tabela de aliases e as capturas ficam em `.frzero/ke_piloto_23-09/`, fora do git, porque o ConceptNet é CC BY-SA e o
léxico derivado não é redistribuído.

## 1. Fontes e congelamento

| item | valor |
|---|---|
| fonte usada | ConceptNet 5.7.0 (`conceptnet-assertions-5.7.0.csv.gz`, S3 oficial), 497.963.447 bytes, sha256 `accd65fe…af7e`, baixada em 2026-09-24T01:26–01:27Z. Única etapa com rede |
| licença | CC BY-SA 4.0, com atribuição: ConceptNet 5, Commonsense Computing Initiative (Speer, Chin e Havasi, 2017), conceptnet.io |
| não usadas | ACM CCS 2012: pendência de termos, que dizem só "educational and research purposes" sem licença formal. Wikidata: CC0, mas um recorte geral não cabe no piloto |
| recorte | todas as arestas `/r/IsA` e `/r/Synonym` com as duas pontas em en/pt, sem filtro de domínio: 621.197 arestas; léxico sha256 `91043b4b…` |
| regras | pré-registradas **antes** da aquisição (declaração sha256 `16fa60b7…`): casamento de rótulo, aliases e partes do rótulo com conceitos; +1 salto de sinônimo; +1 salto de hipônimo, direcional (hipônimo → categoria); higiene mínima |
| aliases KE | CG 1139 (21 tópicos), FR 1168 (12), SO 384 (19), MF 271 (6), ES2 252 (6), IA 60 (7), TCC 2 (1); tabela sha256 `76dd66e9…` |
| integração | taxonomia estendida entregue **só** ao mapeador de subtópico, na 1ª e na 2ª passada, com peso 0,82 como qualquer alias do plano |
| congelamento | capturas base `f64af429…` e KE `b141aa83…`, junto com aliases, léxico, declaração e scripts, em 2026-09-23T22:49:22, antes de ler o gold |

**Observação feita antes do gold.** Ao conferir a tabela de aliases, sem gold, apareceu o efeito da polissemia. Partes de
rótulo que são palavras gerais ("locais", "funções", "perspectiva", "ambiente", "exemplos") casam com conceitos gerais.
O ConceptNet mistura sentidos nos sinônimos ("servidor" ↔ "servant"), e os hipônimos desses sentidos entram como alias
("admiralty", "accountancy"). A regra pré-registrada **não foi alterada**.

**Mudança depois do congelamento.** A avaliação ganhou quatro contadores descritivos: gold nos candidatos da base,
escolhido ou não, e acertos sem o gold entre os candidatos. Mecanismo, capturas e aliases foram conferidos por sha256
antes da reavaliação.

## 2. Execução

- Base: reproduziu por ID a captura congelada da base v2 (`f941ac33…`).
- Os dois braços rodaram locais e determinísticos, sem LLM nem embedding, com tripwires de rede e do cliente Gemini:
  **0 tentativas**.
- Tempo e memória, cada braço em processo próprio: base 319,8 s e 183,5 MB de pico; KE **647,6 s** (2× mais, pelo
  número de frases de alias) e 185,4 MB.

## 3. Comparação (denominadores históricos; régua v2 congelada)

| eixo | base | KE |
|---|---:|---:|
| bloco | 223/237 | 223/237 (0 divergência por ID) |
| unidade | 248/284 | 248/284 (0 divergência por ID) |
| subunidade primária | **86/251** | **77/251** |
| subunidade aceita | 109/251 | 103/251 |

| curso | sub primária base → KE | gold entre os candidatos base → KE | ganhos | perdas | erro → outro erro |
|---|---|---|---:|---:|---:|
| MF | 25 → 19 / 58 | 41 → 43 | 5 | 11 | 14 |
| SO | 7 → 7 / 15 | 4 → 4 | 0 | 0 | 2 |
| IA | 4 → 4 / 39 | 8 → 8 | 0 | 0 | 0 |
| ES2 | 7 → 6 / 28 | 11 → 16 | 0 | 1 | 6 |
| TCC | 7 → 7 / 11 | 10 → 10 | 0 | 0 | 0 |
| CG | 30 → 30 / 82 | 45 → 46 | 2 | 2 | 7 |
| FR | 6 → 4 / 18 | 17 → 18 | 0 | 2 | 2 |
| **total** | **86 → 77** | **136 → 145** | **7** | **16** | **31** |

- **Candidatos:** o gold entra no conjunto em 9 materiais a mais (MF 2, ES2 5, CG 1, FR 1). O conjunto médio sobe de
  4,12 para 4,28 tópicos, e 2 materiais ganharam 2 ou mais candidatos novos. Maior cobertura de candidatos não é aceite.
- **Abstenções:** das decisões antes vazias, 4 passam a certas e 15 a erradas; 5 decisões viram abstenção.
- **Precisão das decisões novas ou alteradas:** 7 certas em 49 (14 %).
- **Os 5 casos da régua CG:** nenhum mudou; continuam no denominador.

## 4. Correções e perdas

Das 54 mudanças, 20 têm um alias KE do novo tópico presente no material, **29 não têm nenhum** e 5 viraram abstenção. As
29 sem alias são efeito indireto: a 1ª passada de outros materiais mudou e isso alterou doadores e confiança na 2ª
passada.

- **Ganhos (7):**
  - 3 são geração, com o gold entrando nos candidatos só com o KE: MF `logicaproposicional-sintaxe` e
    `logicaproposicional-semantica` (alias `logica`, forma singular da parte "Lógicas" do rótulo) e CG `remocaoderuido`
    (`filtro` → "filter", Wiktionary);
  - 4 são mudança de seleção entre candidatos que já existiam: MF `exercicioscorrecaoterminacao`, `invariantes` e
    `terminacao`, e CG `vis3d` (`projecao`/"exibição").
- **Perdas (16), todas com o gold já entre os candidatos:**
  - MF, 11:
    - 7 foram atraídas para "linguagens de especificação e lógicas": `logicapredicados-sintaxe`, `introducao` e
      `formalizacaoalgoritmos-recursao` com o alias `logica` presente; as 3 `provasindutivas-especificacoesrecursivas*`
      e `exerciciosformalizacaoalgoritmosrecursao2` pela 2ª passada, sem alias presente;
    - `exerciciosformalizacaoalgoritmosrecursao3` foi para "exemplos de aplicações" (`original`, hipônimo de "model");
    - `logicadehoare` foi para "correção parcial e total" (`total` → "number" → "divisor"/"inteiro");
    - 2 respostas de recursão viraram abstenção;
  - FR, 2: `rede` → "internet" puxou `02-modelos-de-referencia`; `unidade2-exercicios-dns` mudou pela 2ª passada;
  - CG, 2: `programabasico3d` foi atraído por hipônimos de "position" (`back`, `front`, `left`); `exemplozbuffer` mudou
    por efeito indireto;
  - ES2, 1: `roteiro5-conteiners`, efeito indireto.

## 5. Conhecimento acrescentado × capacidade de selecionar

| | gold entre os candidatos | escolhido quando está | acertos por outra via (2ª passada/seção) |
|---|---:|---:|---:|
| base | 136 | 77 (56,6 %) | 9 |
| KE | 145 | 72 (49,7 %) | 5 |

- **O conhecimento acrescentado quase não alcança a geração que falta.** O gold continua fora dos candidatos em 106
  materiais, contra 115 na base. No IA, o caso que motivou o piloto (o plano nomeia a categoria, o material nomeia o
  algoritmo), o KE não trouxe nenhuma geração nova: pela regra declarada, `modelos-preditivos` e `modelos-descritivos`
  não receberam nenhum alias, e "introdução ao aprendizado de máquina" recebeu 6 (entre eles "neural network"). O TCC só
  ganhou alias em 1 tópico.
- **O KE piora a seleção.** Os aliases gerais e polissêmicos somam evidência a tópicos concorrentes, e a escolha do gold
  quando ele é candidato cai de 56,6 % para 49,7 %. Pelo canal de alias, esse ruído também chega à 2ª passada.
- **Mesmo com geração perfeita, a seleção atual seria o limite.** Hoje o gold está nos candidatos em 136 a 145 materiais
  e é escolhido em cerca de metade deles. Os 226 acertos de subunidade exigem as duas coisas.

## 6. Recomendação

**Encerrar este mecanismo** (ConceptNet geral via canal de alias do subtópico), pelos seguintes motivos:
- saldo −9 na subunidade primária;
- 16 perdas de acertos atuais, quando o aceite exige zero;
- três cursos regredindo;
- precisão de 14 % nas decisões alteradas;
- geração +9, sem alcançar as relações de categoria → algoritmo que motivaram o piloto;
- custo de tempo dobrado.

Se o usuário quiser manter a direção de conhecimento externo, a premissa específica a revisar, com decisão própria e sem
variante automática, é a de que **um léxico geral e sem sentido desambiguado pode entrar pelo canal de seleção**. Uma
revisão teria de:
1. usar uma fonte de domínio com sentidos explícitos e licença clara (hoje a ACM CCS está em pendência de termos);
2. medir primeiro só a geração de candidatos, sem alimentar a seleção nem a 2ª passada.

Mesmo assim, o gargalo medido aqui é a seleção, que o conhecimento externo não resolve.
