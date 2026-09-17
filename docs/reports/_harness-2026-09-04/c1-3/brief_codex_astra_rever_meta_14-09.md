# Brief 13 para o astra (read-only): REVER A META — antes de medir as 3 opções — 2026-09-14

## 0. A ordem do usuário

> *"...vamos usar o resto do limite do astra hoje, para rever a meta, e depois de revermos a meta, meça os 3."*

Os "3" são as opções da §39.7 do handoff (`docs/reports/2026-09-12-handoff-regime-cru.md`) para o elo que falta. **Você não mede
nada: revê a meta e desenha como eu vou medir as 3**, de forma que o resultado responda à meta revista. Use o esforço que for
preciso — é o resto do seu limite de hoje. MEDIDO × HIPÓTESE, `arquivo:linha`.

## 1. A meta atual, literal (13/09)

> *"A ideia é que o motor fique preciso o suficiente (3 eixos e primário > 95%), mas de maneira crua — o aluno consegue apenas
> processar o arquivo, e com base nas informações que o sistema coleta quando é criada uma matéria (SARC, Plano de Ensino, Cards
> moodle) consiga categorizar tudo; e quando o repo sofre resync, a mesma coisa acontece. O uso de LLM ou APIs externas tem que ser
> totalmente opcional, nenhum eixo ou precisão pode se sustentar com LLM ou APIs... as informações e eixos não podem se sustentar
> nos gold... o motor tem que ser modular. Busco bloco, unidade e subunidade >= 95%, depois disso é apenas polimento."*

**Decisões acrescentadas em 14/09:** embedding conta como LLM; o motor tem que rodar em máquina fraca (modelo local não é
pré-requisito). Ideia futura dele, fora do escopo agora: OAuth da conta do próprio usuário no provedor de LLM, em vez de chave de API.

## 2. O que está medido (motor completo, rede bloqueada; detalhe nas §§ citadas)

| configuração | bloco (237) | unidade (284) | subunidade aceito (251) | subunidade PRIMÁRIO (251) |
|---|---|---|---|---|
| **95% exige** | **226** | **270** | — | **239** |
| **cru honesto** (§29) | 222 = 93,7% | 253 = 89,1% | 142 = 56,6% | **100 = 39,8%** |
| VOCAB — vocabulário compilado por LLM, sem voter (§19) | 221 = 93,2% | 255 = 89,8% | 220 = 87,6% | 184 = 73,3% |
| PRODUTO — vocab + voter LLM (§19) | 235 = 99,2% | 263 = 92,6% | 224 = 89,2% | 186 = 74,1% |
| cru + vocabulário DIRIGIDO de 2 tópicos do IA (braço V, §32) | 222 | 253 | 175 = 69,7% | 134 = 53,4% |

- **FR construído do zero** (único curso só com fontes do professor, 0 chamadas, §33.4): subunidade primário **6/18** cru; **16/18**
  com vocabulário compilado por LLM.
- **Unidade no cru**: 31 erros, dos quais **17 são divergência de DESENHO** (a precedência bloco→unidade contra a adjudicação do
  usuário, §26); mudar a precedência por regra perdeu fora da amostra (LOCO, §27).
- **Primário × aceito**: 42 materiais em que o motor acerta um tópico aceito mas não o principal (§33.7); parte é taxonomia
  incompleta (MF), parte é política de prioridade decidida pelo usuário (IA).

**Fechado por medição, sem nenhuma alavanca sobrevivente** (§§25-39): precedência (2 versões), título, SARC posicional, abstenção,
limpar mídia, Datalab, seletor de tópicos carentes, engenharia de bundle, `moodle_label`, propagação de headings, singular×plural,
pai×filho, e o **extrator de relações explícitas** (§39: 25 candidatas, 3 novas, 0 no IA; no motor, +1 primário que é autodoação).

**O diagnóstico convergente (§37, §39.7):** o texto do material tem a evidência; o plano não tem o termo; e **a evidência explícita
do professor termina antes do rótulo do plano** — ele escreve "Tarefas Supervisionadas", o plano diz "Modelos Preditivos".

## 3. As 3 opções para o elo que falta (§39.7)

- **(a) correspondência lexical fraca** — radical compartilhado (`preditiv`); você alertou falso positivo ("estatística descritiva").
- **(b) declaração humana única por curso** — alguém liga a categoria do professor ao rótulo do plano, uma vez; você disse que
  curadoria pelo ALUNO viola o caminho feliz. (Quem mais poderia fazer? O professor? Quem cria a matéria?)
- **(c) LLM opcional** — fora do regime cru; é o único caminho que já provou fechar o elo.

## 4. O que eu quero

1. **A meta atual é alcançável sob as restrições?** Veredito com evidência. Não "impossível" sem prova; não "possível" sem caminho.
2. **A meta revista, formulada com precisão** — o que o usuário pode prometer e cobrar. Considere, e decida o que faz sentido:
   - separar **regimes** com metas próprias (ex.: *cru garantido* / *cru + declaração humana única* / *com LLM opcional*), em vez de
     um número único;
   - **qual métrica**: primário ou aceito; acurácia total ou precisão do confiante + fila (o motor que avisa quando não sabe);
   - **metas diferentes por eixo** (bloco já está em 93,7% no cru; unidade tem 17 erros que são decisão de desenho);
   - **como validar** sem os 7 cursos já examinados (curso construído do zero, reservado).
3. **O protocolo para eu medir as 3 opções**, de modo que cada uma responda à meta revista: o que exatamente rodar, o que congelar
   antes, o critério de parada, e **como evitar contaminação por gold** — em especial na (b): quem escreve a declaração e como
   simular isso sem que quem escreve veja o gabarito; na (a): a regra lexical exata, congelada; na (c): qual configuração conta.
4. **O que NÃO fazer.**

Resposta direta. Se a conclusão for que a meta deve mudar, diga para o quê, em uma frase que caiba no topo do tracker.
