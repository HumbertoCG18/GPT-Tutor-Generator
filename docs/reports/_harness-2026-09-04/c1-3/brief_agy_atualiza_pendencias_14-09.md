# Tarefa (leitura e redação; NÃO invente número): escreva o bloco de ESTADO que abre o `pendencias.md`

Você não pode editar arquivo. **Devolva só o bloco em markdown**, pronto para ser colado logo abaixo da linha `last_updated` do
tracker. Eu colo verbatim, depois de conferir cada número contra as fontes.

## Fontes (caminhos ABSOLUTOS — leia só estas)

1. `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md` — **leia das seções
   `## 28.` até o fim (`## 39.`)**. É onde está tudo o que foi medido de 13 a 14/09.
2. `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/pendencias.md` — **só as primeiras 40 linhas**, para ver o
   formato e a linha `last_updated`.
3. `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/resposta_codex_astra_relacao_termo_topico.md`
   — a seção **"4. Mapa de consolidação"**.

## O bloco que eu quero, nesta ordem (no máximo ~90 linhas)

### A) `## ESTADO DA FRENTE "REGIME CRU" EM 14/09 — o que está medido e o que está fechado`

1. **Placar do cru honesto** (tabela: bloco, unidade, subunidade aceito, subunidade primário) e, ao lado, o do **produto** e o do
   braço **VOCAB** (vocabulário por LLM, sem voter). Tire os números da §29 e da §33.
2. **O que funcionou** (1 linha cada, com o número): o braço V (§32); o FR construído do zero com e sem vocabulário (§33.4).
3. **O que foi FECHADO por medição** — uma tabela `alavanca | resultado medido | §`. Inclua todas as das §28 a §39: precedência
   bloco×texto (as duas), título, SARC, abstenção, limpar mídia, Datalab, seletor de tópicos carentes, engenharia de bundle,
   `moodle_label`, propagação de headings (`sempropag`), singular×plural, pai×filho, e o extrator de relações explícitas.
4. **As decisões do usuário, que não se reabrem**: LLM opcional (nenhum eixo se sustenta em LLM ou API); nada se sustenta em
   gold; motor modular por professor; resync; o aluno só processa o arquivo; **embedding conta como LLM**; **o motor tem que rodar
   em máquina fraca**.
5. **As correções de afirmações do Claude** registradas nessas seções (ex.: "teto de 32" era piso; "15 zips sem texto" estava
   errado; "singular×plural 5 de 12" virou 0). Uma linha cada.

### B) `## MAPA DE CONSOLIDAÇÃO — 4 camadas (astra, 14/09): MAPEAR, NÃO FUNDIR AGORA`

Comece com este texto, **literal**:

> Para a fusão que o usuário quer fazer depois, o astra separou 4 camadas, sem mexer em nada agora:
> - **aquisição de vocabulário**: de onde vêm os termos;
> - **vocabulário do curso**: o que o motor lê;
> - **evidência do material**: título, headings e corpo, que são o mesmo documento e não confirmações independentes;
> - **estrutura e decisão**: datas, SARC, seção, heranças e correções humanas. Isto não é vocabulário e não deve virar um peso único.

Depois, uma tabela `camada | o que reunir (mecanismos atuais, com arquivo) | o que precisa sobreviver à fusão`, tirada da §38.5 e
da resposta do astra. E a lista de **candidatos a sair** da §38.5, com a regra: *cada retirada com ablação individual*.

### C) `## DECISÃO EM ABERTO (14/09)`

As 3 opções da §39.7 para o elo "nome do professor → rótulo do plano" — (a) correspondência lexical fraca, (b) declaração humana
única por curso, (c) LLM opcional —, **e que a meta (≥ 95% nos 3 eixos, primário, no cru) está sendo revista pelo astra antes de
medir as 3**.

## Regras

- **Todo número vem das fontes, com o § ao lado.** Se não achar, escreva "não encontrado" — não estime.
- Português com acentos. Sem introdução nem conclusão fora do bloco.
