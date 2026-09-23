# Piloto de conhecimento externo — desenho (23/09/2026, regime separado, não executado)

**Status: desenho.** Autorizado só o desenho. Não autoriza baixar dados, incorporar conhecimento externo ao regime cru
nem implementar nada no produto. Cada etapa abaixo (aquisição, construção, execução) exige aprovação própria.
Sem promessa de ganho, sem nova grade de pesos, sem reabrir S, G, H2 ou R1–R4.

## 1. Pergunta e motivo

Na base v2, os 165 erros de subunidade primária se dividem em não geração 76 (F6 relação fora do índice 65, F7 relação não
encontrada 11), seleção 67, unidade 17 e identidade 5 (W-Z2). O W-U mostrou que as relações que já estão no pacote do
curso cobrem 56/106 casos de relação ausente, mas conflitam em 177/178: a existência de relação não discrimina. Sobram
casos em que o material nomeia um conceito (algoritmo, técnica) e o plano nomeia a categoria, sem nenhuma ponte no
pacote. A pergunta do piloto é esta: **um conhecimento geral de computação, independente do benchmark, gera o tópico
certo como candidato sem inflar a ambiguidade, e o seletor atual o escolhe?** As duas perguntas são medidas separadamente.

## 2. Regime

- Regime **"cru + KE"**, separado do cru. O cru publicado não muda, e o placar de cada regime é reportado lado a lado.
- Processamento local e determinístico: sem professor, sem LLM, sem rede, sem embedding. O conhecimento entra como
  arquivo local congelado (sha256), lido durante o replay.
- A aquisição do dado (download de uma versão fixada) é uma etapa anterior, com autorização própria. É o único ponto com
  rede, e fica registrada com URL, data, versão e sha256.

## 3. Fontes candidatas (a confirmar na etapa de aquisição)

| fonte | cobertura | idioma | relações úteis | licença (verificar na aquisição) |
|---|---|---|---|---|
| Wikidata (dump ou recorte por consulta fixa) | geral, com computação ampla | pt e en (rótulos e aliases) | subclasse de (P279), instância de (P31), parte de (P361), rótulos alternativos | CC0 |
| ConceptNet 5 | senso comum com termos técnicos | multilíngue, com pt | IsA, PartOf, Synonym, RelatedTo | CC BY-SA 4.0 |
| ACM Computing Classification System 2012 | taxonomia de computação | en | hierarquia de conceitos | termos de uso da ACM, a confirmar |
| WordNet / OpenWordNet-PT | léxico geral | en / pt | sinonímia, hiperonímia | licenças WordNet / OpenWordNet-PT, a confirmar |

Critérios para aceitar uma fonte: (a) independente dos materiais, da régua e das listas de erro; (b) cobertura geral de
computação, não só dos 7 cursos; (c) licença compatível com uso local e versionamento do recorte; (d) versão fixável
(release ou data de dump); (e) proveniência por relação (id do item, propriedade, versão).

## 4. Construção do léxico (sem olhar o benchmark)

- **Recorte geral por regra declarada antes**: por exemplo, fecho transitivo por "subclasse de" a partir de
  "ciência da computação"/"computação", com profundidade e tipos de relação fixos. Não semear pelos rótulos dos planos
  nem por materiais, e nunca pela lista de erros, pelo gold ou pelas famílias do W-Z2.
- **Tipos de relação distintos, sem peso novo**: cada relação guarda o tipo (sinônimo/tradução, é-um, parte-de,
  relacionado). O piloto usa **um único subconjunto declarado antes** (proposta: sinônimo/tradução e é-um), sem ajustar
  depois. "Relacionado" fica fora: é a relação que o W-U mostrou não discriminar.
- Saída: `lexico_ke_<fonte>_<versao>.json` com entidade → rótulos (pt/en) e arestas tipadas, cada uma com fonte, id,
  versão e sha256 do arquivo. Uma auditoria de vazamento lista as entradas do script de construção; nenhuma delas pode
  estar sob `tests/fixtures/eval`, na régua ou nos relatórios de erro.

## 5. Ponto de integração (um só, fixado antes)

- O KE entra **só na geração de candidatos da subunidade**: um tópico do plano vira candidato do material quando um
  termo do material (título, headings, texto, pelas mesmas funções de sinal do motor) casa com uma entidade do léxico
  ligada ao rótulo do tópico por relação do subconjunto declarado.
- O seletor não muda: mesma pontuação e mesma ordem. O candidato vindo do KE entra pelo canal de aliases já existente,
  com o mesmo tratamento de um alias do plano. Não há peso, limiar ou regra nova, nem grade de valores.
- A unidade não é tocada no braço principal (ver 6.3).

## 6. Medição separada (replay integral, mesma cadeia do W-Z2)

Cadeia `replay_bloco_21-09` → `replay_unidade_21-09`, base v2 congelada por sha256 antes de ler o gold. Três leituras
independentes, por curso e no total, com a lista de IDs:

1. **Geração de candidatos**: fração dos materiais em que o tópico-gold está entre os candidatos, cru × cru+KE (com a
   unidade prevista e com a unidade-gold como oráculo diagnóstico, sem somar). Mede também a **ambiguidade
   introduzida**: materiais que ganham 2 ou mais candidatos novos e o tamanho médio do conjunto de candidatos. Converter
   F6/F7 só conta como avanço se a ambiguidade não crescer na mesma proporção.
2. **Escolha primária**: condicionada ao gold estar entre os candidatos, a taxa de escolha do gold como primário, cru ×
   cru+KE. Separa "o KE trouxe o candidato" de "o seletor escolheu certo".
3. **Unidade**: no braço principal, o eixo de unidade tem de sair idêntico por ID (asserção). Um braço secundário
   opcional, com o KE também na rota de unidade, só roda com autorização própria e reporta mudanças de unidade por ID.

Placar dos três eixos (bloco, unidade, subunidade primária) com as mudanças por ID: ganhos, perdas e materiais movidos
sem ganho.

## 7. Aceite e limites de interpretação

- Critérios de integração inalterados: ganho positivo, zero perda de acerto atual (sem lista protegida por gold),
  nenhum curso regride, outros eixos preservados, replay integral. Precisão sobre os acertos atuais não é aceite.
- Os 7 cursos já estudados (MF, SO, IA, ES2, TCC, CG, FR) **não são holdout**. O piloto neles mede o mecanismo, não a
  generalização. Para afirmar generalização, é preciso um curso novo, com régua construída às cegas antes de rodar.
- Resultado negativo encerra a hipótese desta configuração, sem retunar tipos de relação, profundidade ou fonte sobre os
  mesmos dados.

## 8. Etapas e autorizações

1. Aprovar este desenho (fontes, recorte, subconjunto de relações, ponto de integração, métricas).
2. Autorizar a aquisição, a única etapa com rede: baixar a versão fixada, conferir a licença, registrar o sha256.
3. Construir o léxico e a auditoria de vazamento, sem o gold.
4. Autorizar a execução: replay integral e relatório com as três leituras separadas.
5. Qualquer uso no produto é decisão separada, depois do resultado.
