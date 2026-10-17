# Fase 0: medição descritiva dos termos pouco discriminantes no pontuador da subunidade (01/10/2026)

**Resultado interpretativo: sensibilidade demonstrada; benefício ainda desconhecido.** (Leitura fixada pelo usuário em
01/10.)

O critério indicativo pré-registrado marcou "ganha força". Essa saída fica preservada como histórica, com duas
ressalvas:

- a razão 68/158 mistura populações (ver "Detalhamento");
- os contrafactuais R_* removem termos inteiros e **não** medem os candidatos P1 e P2.

O detalhamento mostra que a sensibilidade vem de outro lugar que o esperado:

- **frases:** os termos pouco discriminantes quase não pesam no vencedor, salvo em 2 dos 5 cursos;
- **tokens:** a pontuação concentra-se em tokens frequentes nos materiais. Retirá-los deixa a maioria das decisões
  afetadas **sem sinal**, em vez de trocar o tópico.

É medição descritiva: sem gold, sem placar e sem regra. Nenhuma mudança é "acerto" ou "erro".

## Execução

- **Pré-registro:** `preregistro-fase0-pontuador.md`, sha256 `68ff436f…`, selado às 23:05, antes da execução.
- **Runner:** `fase0_pontuador.py` (`cb1405f1…`). Uma execução, 23:08–23:11 (181 s).
  - Cursos MF, SO, IA, ES2 e TCC; CG e FR não executados.
  - `src` da base, sem a correção do CRU-05, contra `replay_base.json` (`e024d396…`).
- **Saída:** `fase0_pontuador.json` e `registros/fase0_pontuador.txt`.
- **Fidelidade: integral.**
  - Decisões finais idênticas à referência: 0 divergências.
  - Nenhum `src` carregado de fora da worktree.
  - Decomposição: reproduz a pontuação real em **1536/1536** pares (material, tópico), com diferença máxima 0,0.
  - Vencedor e estado recalculados iguais aos devolvidos em **231/231** chamadas.
  - Matcher em cache igual ao real em **27.968/27.968** avaliações.

## Resultados pré-registrados

Universo: 231 materiais na 1ª passada, dos quais **158 com vencedor**.

| curso | 1ª passada | com vencedor | vencedor só por tokens | argmax muda R_top | R_mat | R_both | fração de frases pouco discriminantes no vencedor: mediana (fração > 0) |
|---|---|---|---|---|---|---|---|
| MF | 69 | 45 | 30 | 1 | 6 | 7 | 0,0 (0 %) |
| SO | 39 | 22 | 7 | 11 | 7 | 15 | **1,0 (53 %)** |
| IA | 63 | 49 | 27 | 1 | 23 | 23 | 0,0 (0 %) |
| ES2 | 34 | 20 | 17 | 5 | 13 | 14 | 0,0 (0 %) |
| TCC | 26 | 22 | 11 | 3 | 7 | 9 | 0,0 (18 %) |
| **total** | **231** | **158** | **92** | **21** | **56** | **68** | **0,0** (n = 66 vencedores com frase) |

**Critério indicativo** (pré-registrado):

- mediana da fração de frases = 0,0, abaixo de 10 %;
- argmax muda em R_both em 68/158 = **43 %**, acima de 25 %.

Pela regra pré-registrada, o resultado é **"ganha força"**.

## Detalhamento (feito depois, da mesma execução, sem rodar de novo)

**1. Tipo de mudança do argmax:**

| versão | decidido → vazio | vazio → decidido | troca de tópico |
|---|---|---|---|
| R_top | 10 | 4 | 7 |
| R_mat | 39 | 9 | 8 |
| R_both | **47** | 11 | **10** |

- O critério pré-registrado contou "vazio" como mudança de argmax. Foi uma falha do desenho, só percebida depois.
- **A razão 68/158 mistura populações** (correção do usuário). As 11 mudanças "vazio → decidido" vêm de materiais **fora**
  dos 158 que tinham vencedor; eles estão entre os 73 sem vencedor.
  - **Entre os 158 com vencedor**, R_both muda o argmax em **57/158 = 36,1 %**: 47 esvaziamentos (29,7 %) e **10
    trocas de tópico (6,3 %)**.
  - Pelo mesmo recorte: R_top muda 17/158 (10 esvaziamentos e 7 trocas); R_mat muda 47/158 (39 e 8).
  - As colunas "argmax muda" da tabela por curso, acima, usam a contagem mista.
- Retirar os tokens com F_mat > 0,25 esvazia 39 decisões. Isso mostra que **o sinal de muitas decisões está todo em
  tokens frequentes nos materiais**: é o tema transversal da disciplina. Sem gold, não se sabe se esses tokens
  enganam ou acertam.

**2. Inventário de frases pouco discriminantes:**

- são poucas: 0 a 2 por curso com F_top ≥ 2, e 0 a 2 com F_mat > 0,25;
- **só em 2 cursos** entram na pontuação de vencedores:
  - SO: "escalonamento" em 12 vencedores, "arquivos" em 11;
  - TCC: "maquinas de turing" em 10.
- No MF, na IA e no ES2, nenhuma frase pouco discriminante pesa em vencedor.

**3. Vencedores sem acerto de frase:** 92 dos 158 vencem só pela sobreposição de tokens. A frase exata não é a via
dominante da 1ª passada nesses cursos.

## Leitura para a Fase 1 (decisão do usuário, 01/10)

- **R_top não é P1.** R_top remove frases e tokens compartilhados; P1 reduz o peso das frases compartilhadas e preserva
  as mais específicas. As 7 trocas e os 10 esvaziamentos de R_top **não** são efeitos medidos de P1: mostram
  sensibilidade a uma remoção mais abrangente.
- **P1 segue para a Fase 1 como desenho congelado.** A hipótese é delimitada: reduzir a vantagem de frases
  compartilhadas pelos tópicos concorrentes, preservando o sinal específico.
  - As frases pouco discriminantes só pesam em vencedores do SO e do TCC (cerca de 23).
  - O alcance pequeno não torna o P1 inútil para corrigir fragilidades, mas impede apresentá-lo como caminho
    demonstrado para os +140.
- **P2 fica suspenso, sem redesenho.** Ele confunde frequência no corpus com falta de utilidade para distinguir
  tópicos. Os 39 esvaziamentos mostram o risco da remoção, embora não provem piora de acurácia.
- **Os +140 da subunidade primária:** nada aqui indica um caminho para eles.

## Limites

- 5 cursos de desenvolvimento, com gold já visto em outras rodadas; esta medição não leu gold.
- As versões R_* são contrafactuais de sensibilidade, não regras: retiram termos inteiros.
- O critério indicativo contou "vazio" como mudança de argmax. Isso está registrado como falha do pré-registro e não
  foi reinterpretado: o resultado formal continua "ganha força", com o detalhamento acima.
- Não houve segunda execução nem variação de limiar.
