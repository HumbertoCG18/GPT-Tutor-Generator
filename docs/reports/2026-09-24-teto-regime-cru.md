# Teto do regime cru do motor de atribuição, por curso (24/09/2026)

Regime cru: 0 LLM, 0 rede, 0 embedding; gold só avalia; nada por curso, arquivo ou ID. Meta do marco motor→web (usuário,
21/09): mais de 90 % em bloco, unidade e subunidade primária, separadamente, por curso e no total. Este relatório publica
onde o motor está, até onde o cru chega com o que já foi medido e o que falta para cada família de erro. Não é previsão.

Base: `feat/motor-atribuicao` em `eebc698c` (inclui o M1 de 24/09), régua v2 final + 13 materiais presentes. FR não tem
régua de bloco nem de unidade.

## 1. Placar atual e meta

| curso | bloco | unidade | sub primária | sub aceita | mínimo >90 % (bloco / unidade / sub) |
|---|---:|---:|---:|---:|---|
| MF | 60/66 | 63/66 | 25/58 | 29 | 60 / 60 / 53 |
| SO | 36/39 | 30/37 | 7/15 | 8 | 36 / 34 / 14 |
| IA | 41/42 | 39/42 | 4/39 | 5 | 38 / 38 / 36 |
| ES2 | 27/28 | 26/28 | 7/28 | 8 | 26 / 26 / 26 |
| TCC | 26/27 | 17/18 | 7/11 | 9 | 25 / 17 / 10 |
| CG | 33/35 | 74/93 | 30/82 | 43 | 32 / 84 / 74 |
| FR | — | — | 6/18 | 7 | — / — / 17 |
| **total** | **223/237 (94,1 %)** | **249/284 (87,7 %)** | **86/251 (34,3 %)** | 109 | 214 / 256 / 226 |

- **Bloco:** cumpre em todos os cursos; o MF está exatamente no mínimo.
- **Unidade:** faltam 7 no total; por curso, CG +10 e SO +4.
- **Subunidade primária:** faltam 140 no total; todos os cursos estão abaixo da meta.

## 2. Tetos do cru

**Unidade.** Sobre a base de 23/09, os caminhos admissíveis somam **253/284 (89,1 %)**. Foram medidos 250: M1 +1 e M2 +1,
com 0 perda. Está implementado 249 (M1). O CG chega no máximo a 74 (meta 84) e o SO a 30 (meta 34).
Fontes: `c1-3/unidade_caminhos_24-09.json` e `c1-3/wab_unidade_fallback_fronteiras_24-09.json`.

**Subunidade primária.** O teto estrutural (W-Z2 §3.7) é um limite ideal: cada candidato gerado seria escolhido certo.

| curso | mínimo | teto com a unidade atual | teto com unidade perfeita |
|---|---:|---:|---:|
| MF | 53 | 55 | 55 |
| SO | 14 | **10** | 14 (exige 100 % do endereçável) |
| IA | 36 | 39 | 39 (exige converter 30 de 30 F6) |
| ES2 | 26 | **25** | 28 |
| TCC | 10 | 11 | 11 |
| CG | 74 | **60** | **69** |
| FR | 17 | 18 | 18 |
| total | 226 | **218 (86,9 %)** | 234 (93,2 %) |

Mesmo o limite ideal fica abaixo da meta no total e em SO, ES2 e CG. Nenhum mecanismo medido chega perto do ideal: os
melhores mudaram a subunidade em −3 (S), −9 (conhecimento externo) e −10 (G).

## 3. Famílias de erro da subunidade e o que cada uma exigiria

Anatomia dos 165 erros (W-Z2 §3.2; cada material conta uma vez):

| família | n | causa | tentativas medidas | o que exigiria |
|---|---:|---|---|---|
| F6 relação fora do índice | 65 | o gold tem pontuação zero; outra fonte do pacote liga o material ao tópico, mas de forma ambígua | W-U (177/179 relações conflitantes); G, W-AA (86 → 76) | relação exclusiva entre vocabulário do material e rótulo do plano, que o pacote não traz |
| F4b escolha errada | 33 | o gold é candidato e perde a seleção | S, W-AA (86 → 83); sinais P1, P2, P4 e P5 (W-AC, nenhum passa) | sinal que distinga o assunto principal do assunto de fundo |
| F8 vários assuntos | 23 | material com vários assuntos; o primário perde | idem F4b; pai × filho fechado em 13–14/09 | idem |
| F2 unidade errada | 17 | a unidade prevista exclui o gold | unidade R1–R4 reprovada (W-Z); M1/M2 não alcançam esses casos | unidade certa; o oráculo de unidade dá só +6 líquido |
| F7 relação não encontrada | 11 | nenhuma fonte do pacote liga o material ao tópico | ConceptNet (86 → 77) | conhecimento externo; já reprovado neste formato |
| F4a abstenção | 8 | o motor não decide | P1 só na abstenção: +4/−1 (exploratório) | — |
| F1 régua do CG | 5 | subunidade-gold vazia sob a unidade v2 u05 | — | decisão do usuário sobre a régua (versão separada) |
| F5 alterada depois | 3 | a 2ª passada troca uma decisão certa | propagação +11/−4 hoje | restringir doadores: teto de +4 |

Causa comum às maiores famílias: os tópicos do plano de ensino são categorias ("modelos preditivos", "transformações
geométricas"), e os materiais falam de algoritmos, ferramentas e termos em inglês (k-NN, OpenGL, circuit breaker). O pacote
do professor não traz a relação entre os dois níveis. Onde a relação aparece, ela aponta cinco tópicos ou mais.

## 4. Varredura final de sinais nunca testados (W-AC, 24/09)

Só leitura sobre a base congelada, previsões congeladas antes do gold
(`c1-3/wac_varredura_sinais_subunidade_24-09.json`). Portão: precisão > 50 % nos 86 acertos e saldo potencial > 0.

| sinal | dispara em acertos | precisão nos acertos | erros em que aponta o gold | saldo potencial | portão |
|---|---:|---:|---:|---:|---|
| P1 posição da aula na unidade × ordem dos tópicos | 80 | 21 % | 60 | −3 | não |
| P2 posição na seção do Moodle × ordem dos tópicos | 74 | 13 % | 33 | −31 | não |
| P4 referência cruzada a outro material | 0 | — | 0 | 0 | não |
| P5 tópico primário da aula (`primary_topic_slug`) | 34 | 65 % | 6 | −6 | não |

Exploração posterior ao resultado, só indício: P1 restrito às abstenções dá +4/−1; restrito a decisões com confiança
abaixo de 0,7 dá +11/−8. Nenhuma variante cumpre "0 perda".

## 5. Mecanismos reprovados ou fechados (não reabrir sem sinal novo)

- Precedência bloco × texto na unidade: R1–R4 (W-Z, 22–23/09); "seção sozinha" (W-H, 21/09, dominada pela seção
  corroborada da #47).
- Seleção por papel da seção (S) e geração por subordinação local (G) (W-AA, 23/09).
- Conhecimento externo com ConceptNet 5.7.0 (piloto de 23/09).
- Pai × filho na subunidade (13–14/09); localização em título/heading (H2).
- Sinais posicionais e de referência da W-AC (24/09).
- Rotulação pelo professor: fora do produto, por decisão do usuário.

## 6. Leitura para decisão

- **No cru, a meta de subunidade não é alcançável** com os insumos do pacote: o limite ideal (218) já fica abaixo de 226, e
  todos os mecanismos medidos pioram ou não mudam o placar. A de unidade também não fecha no CG nem no SO.
- **O que mudaria o teto** é sempre um sinal que o pacote não contém: relação vocabulário → tópico com proveniência (regime
  separado, com decisão própria e guarda contra ajuste ao benchmark), ou um plano de ensino mais granular. Rotulação pelo
  professor segue excluída.
- **Publicar o cru como está** exige mostrar o placar por curso e regime, com abstenções e ausentes no denominador, sem
  trocar acerto total por precisão só dos confiantes.
