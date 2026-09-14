# PROMPT CONGELADO — braço C (LLM como fornecedor do mapa categoria → tópico), 14/09

**Congelado antes de qualquer execução.** Provedor: agy (conta Google do usuário). Modelo: `gemini-3.8-flash-high`.
Execução: um lote por chamada, ordem fixa (curso, lote), **a primeira resposta vale** — sem nova tentativa por placar.
Resposta inválida ou fora do schema = categorias do lote sem correspondência. Nenhuma ferramenta: o lote vai inline.

---

Você recebe, logo abaixo, os TÓPICOS do plano de ensino de uma disciplina (código e rótulo) e uma lista numerada de
CATEGORIAS que o professor usou nos materiais da disciplina, cada uma com os termos que ele listou sob ela e um trecho.

Para CADA categoria, responda o código do ÚNICO tópico do plano ao qual os termos listados sob essa categoria pertencem.

Regras:
1. Use somente códigos que aparecem na lista de tópicos. Não invente código, tópico ou termo.
2. Se nenhum tópico corresponde, ou se a categoria é genérica (exemplo, exercícios, referências, agenda, avaliação,
   bibliografia, sumário, objetivo), responda "SEM".
3. Se a categoria corresponde a mais de um tópico com a mesma força, responda "SEM".
4. Não use nenhuma ferramenta. Não explique. Responda apenas o JSON do schema, com uma entrada para cada id da lista.
