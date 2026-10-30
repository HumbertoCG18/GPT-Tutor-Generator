# Roteamento por tarefa

Aplicar sem exigir pedido explícito de delegação. Ler uma vez por tarefa; escolha do usuário prevalece.

- Pergunta/status/documentação pequena: agente ativo.
- Código: modelos Claude implementam conforme nível investigado abaixo (Claude Code); com a cota do Claude apertada, T1/T2 vão ao Codex (ver Camadas).
- Arquitetura, múltiplos componentes ou aceite ambíguo: Codex planeja/orquestra; Claude Code implementa.
- Código relevante pronto: revisão independente do revisor, uma tentativa conforme review.md (em T3, mais uma após NOT APPROVED).
- Auditoria, corpus e busca de código: Codex (../agents/codex-leitor.md). Escrita e pesquisa: Codex
  (../agents/escritor.md). Fontes e arquivos de saída delimitados; AGY só por escolha explícita.

## Investigador e níveis (aprovado em 21/09/2026)

Investigador é quem conduz a investigação, não outro agente obrigatório. O agente ativo
faz a triagem read-only; se já há investigação delegada, seu dono classifica e devolve
a decisão. Não chamar modelo só para classificar. O investigador decide; o coordenador
registra e aplica, esclarecendo contradições de escopo/permissão. Escolha do usuário prevalece.

Antes de implementar/delegar, registrar nível, risco, ambiguidade, alcance, evidência
arquivo:linha, confiança (alta/média/baixa), aceite e modelo/effort por fase. Usar o maior
nível sustentado pelos critérios, não soma nem número de tokens/arquivos.

| Nível | Critério | Executor Claude | Codex: leitura, escrita e reserva do executor | AGY por escolha: implementação / escrita |
|---|---|---|---|---|
| T0 | Determinístico: consulta, contagem, check mecânico | ver Matriz executável | agente ativo | sem nova chamada |
| T1 | Baixo risco, causa/escopo locais, aceite objetivo | ver Matriz executável | gpt-6-astra / medium; implementa na reserva | claude-sonnet-5-5-medium / claude-sonnet-5-5-medium |
| T2 | Integração entre componentes, hipóteses concorrentes, regressão relevante | ver Matriz executável | gpt-6-astra / high; implementa na reserva | claude-sonnet-5-5-high, escalar a claude-opus-5-5-high / claude-sonnet-5-5-medium |
| T3 | Segurança/permissões sensíveis, perda de dados/irreversibilidade, arquitetura ou incerteza sistêmica | ver Matriz executável | gpt-6-astra / high; não implementa | não implementa (fica no Claude Code) / claude-sonnet-5-5-high |

Matriz executável gerada de rotas.json por `bin/rotas.py --escrever`; o Mod rota aplica (ROTA-08). Não editar à mão.

<!-- rotas:inicio -->
| Papel | T0 | T1 | T2 | T3 |
|---|---|---|---|---|
| principal planejamento | sonnet/high | sonnet/high | opus/high | opus/high |
| principal coordenação | sonnet/high | sonnet/high | sonnet/high | opus/high |
| worker | — | haiku/high | sonnet/high | — |
| worker escalada | — | sonnet/medium | opus/high | — |
| revisor | — | opus/medium | opus/medium | opus/high |
| Plan | sonnet/high | sonnet/high | opus/high | opus/high |
| haiku-ops | haiku/low | haiku/low | haiku/low | haiku/low |
| investigador | sonnet/high | sonnet/high | sonnet/high | sonnet/high |
| Explore | haiku | haiku | haiku | haiku |
| general-purpose | sonnet/high | sonnet/high | sonnet/high | sonnet/high |

Cota (leitura válida por 30 min; vale a janela 5 h ou 7 d mais alta): reserva do executor acima de 80%, fallback do revisor acima de 80%, reserva de coordenação acima de 90% (volta até 80%).
<!-- rotas:fim -->

Movido para [routing-details.md › Modelos em uso: texto da revisão de 10/10/2026](routing-details.md#modelos-em-uso-texto-da-revisão-de-10102026): revisão de 10/10 (fable fora do T3, gpt-6.1-sol/gpt-6-sol fora da seleção) e fontes.

IDs só aqui (agent-workflow-lab#43). No Claude Code, settings, frontmatter de agentes e delegações
usam alias (opus, sonnet, haiku, fable, opusplan, inherit; [1m] aceito); verify.py confere settings
e frontmatter (lab e ~/.claude/agents) e falha com ID fixo. Alias → ID medido: routing-details.md ›
Modelos em uso. Precedência do subagente: hook `agent.spawn` de Mod (rota, em modo auto) > model da
chamada > model do frontmatter > CLAUDE_CODE_SUBAGENT_MODEL > modelo da sessão (doc oficial de
sub-agents; desde a 2.1.251 o env deixou de vir primeiro). Effort: CLAUDE_CODE_EFFORT_LEVEL >
effort da chamada > frontmatter > sessão; o Mod rota aplica o effort no `turn.step` do subagente. O menu /model ainda oferece linhas
antigas (Sonnet 5) e Enter salva como padrão: escolher pelo alias ou usar s (só na sessão).

T2 no Sonnet e T1 no Haiku (ROTA-04, aprovado pelo dono em 15/10/2026): escalar ao Opus quando o
Sonnet travar, falhar no aceite ou a revisão achar P1 que ele não corrige; T1 sobe do Haiku ao
Sonnet nas mesmas condições. Evidência: ../evals/rota-03-2026-10-15.md. Cada subida soma 1 em
`escalada_executor` no estado, separado de `escaladas_automaticas` (revisão); escalar não muda o nível
nem renova revisão.

Principal (ROTA-07, aprovado pelo dono em 29/10/2026; substitui o opus/high fixo da ROTA-04, #50):
sonnet/high coordena T0–T2; opus/high no planejamento T2/T3 e em toda tarefa T3 (linhas "principal" da
Matriz executável). Fase pelo `status` do active-task.md (planejando = planejamento; executando,
delegando, revisando, bloqueado = coordenação). Sem tarefa ativa, fica o modelo da sessão. O Mod rota só
troca no início de um turno, depois de mudar tarefa, nível ou fase: trocar de modelo refaz o cache do
contexto inteiro. Escolha do dono: `/rota manual <modelo> [effort]`, válida até a tarefa mudar.
Motivo da troca: em 22–28/10 a thread principal gerou 930M de cache_read em Opus (~73% do output total
era Opus); critério de validação na ROTA-12 (#554).

Subagente Claude para implementar T1/T2: worker (../agents/worker.md, sem Skill nem Agent, mantém
o CLAUDE.md), no lugar de general-purpose. O frontmatter é sonnet (T2 e escalada do T1); em T1
passar `model: haiku` na chamada, que vale mais que o frontmatter. 21/10, general-purpose gastou mediana
33.964 tokens na 1ª chamada e 0 Skill em 24 subagentes; haiku-ops (tools explícito) gastou 9.293.

<a id="leitura-dono"></a>
Trabalho só de leitura: um dono por tipo (#360).

| Tipo de leitura | Dono |
|---|---|
| Investigação, auditoria, verificar issue contra o código, triagem do registro | Codex via `codex_read` (padrão; ver Leitura no plano da OpenAI) |
| Precisa gravar arquivos de sonda ou rodar comandos fora do sandbox read-only do Codex (ex.: enviar payload a hooks) | Subagente `investigador` (../agents/investigador.md) |
| Busca ampla de arquivos | Explore com `model: haiku` |

Reserva no Codex (ROTA-06, aprovado pelo dono em 16/10/2026): uma rodada só. A cota do AGY (plano
PRO) é baixa, então reserva, escrita e auditoria saem do AGY. Evidência:
../evals/rota-05-2026-10-16.md. Números das duas medições: routing-details.md › Medições ROTA-04 e ROTA-06.

Incerteza não investigada não vira T1: manter classificação provisória e investigar
antes de executar. Para investigação delegada, a triagem propõe nível provisório e o
investigador confirma/revisa antes da próxima fase. Reclassificar com evidência/motivo,
nunca como fallback por quota/recusa. Tarefa pequena pode ser T3; longa pode ser T1.
Pergunta/status/docs simples ficam no agente ativo, sem migração de sessão.

## Camadas (aprovado pelo dono em 11/10/2026)

| Camada | Ferramenta | Faz | Modelos |
|---|---|---|---|
| 1 | Claude Code | Orquestra (padrão) e implementa | Executor Claude da tabela de níveis |
| 2 | Codex | Lê (planeja, revisa, investiga, valida, audita, busca código), escreve docs e pesquisa, e implementa T1/T2 na reserva | gpt-6-astra, effort pelo nível |
| 3 | AGY | Só por escolha explícita (cota do plano PRO baixa), só com arquivos (sem comandos): implementa T1/T2 ou escreve | Claude do AGY, depois gpt-oss-120b, depois Gemini 3.8 Flash; Gemini 4 Argon só como reserva ([routing-details.md › AGY](routing-details.md#agy-por-escolha-explícita-orquestrador-de-último-recurso)) |

- Implementação: camada 1. Com a cota do Claude apertada (aviso de limite ou escolha do dono), o
  coordenador registra a troca no estado e passa T1/T2 ao Codex: `codex exec -m gpt-6-astra -c
  model_reasoning_effort=<medium T1, high T2> -s workspace-write`, numa worktree própria. T3 fica
  na camada 1: sem cota, espera. Erro ou recusa não é troca: parar.
- Gatilho (#62): antes de delegar T1/T2, o coordenador lê a última linha de
  `<raiz>/.workflow/local/cota-historico.jsonl` (o mod `cota-alerta` grava `t`, `five_hour`, `seven_day` a
  cada turno do dono). Qualquer janela acima de 80% com `t` de até 30 min: T1/T2 vão à reserva Codex,
  registrado no estado. Sem linha, sem nenhuma das janelas `five_hour`/`seven_day` (uma só basta: o
  mod grava as que a API devolve), com `t` no futuro ou mais velho que 30 min: cota
  desconhecida, fica no Claude, sem troca silenciosa, e o estado diz "cota desconhecida". 30 min: o mod
  só mede ao fim de cada turno do dono (sem timer), então turno longo ou sessão parada deixa o dado velho.
- Codex implementando roda sem os hooks do workflow (`features.hooks=false`, SEG-02): só o sandbox
  protege. Nunca com `--dangerously-bypass-approvals-and-sandbox`, `--yolo` ou `danger-full-access`;
  brief sem segredos; proibido no noturno (noite.md).
- Reserva de coordenação (ROTA-10, aprovada pelo dono em 29/10/2026; ainda não implementada): com a
  cota do Claude estritamente acima de 90% em qualquer janela (5 h ou 7 d), leitura de até 30 min, o
  Codex coordena a próxima tarefa, trocando só entre tarefas e com um coordenador por vez. Ele planeja e
  implementa T1/T2 na worktree; T3 espera; sem commit, push ou merge; a revisão do código dele espera o
  Claude. Volta ao Claude com as duas janelas até 80% em leitura válida. Nunca à noite. O Claude Code
  segue como interface. Limiar próprio: não muda os 80% da reserva do executor nem do fallback do revisor.
- Revisão (#332, aprovado pelo dono em 22/10/2026; ordem atualizada em 29/10/2026, review.md): o revisor
  é independente do implementador, não do orquestrador. Em T1/T2 de código do Claude a 1ª rodada é do
  Codex (`astra_review`); as rodadas Claude usam claude-opus-5-5 medium. Em T3 e em código do Codex, o
  revisor é claude-opus-5-5 (high em T3), em contexto
  novo: só o brief, nunca fork da sessão que implementou. Em T3 o revisor pode ser o mesmo modelo do
  implementador. Fallback: com a cota do Claude acima de 80% (mod `cota-alerta`; no Alethe, o limiar
  do app), código do Claude vai ao revisor Codex (gpt-6-astra). Código do Codex não tem fallback: sem
  cota do Claude, a revisão espera, porque nunca passa ao fornecedor do implementador.
- Leitura, auditoria e busca: camada 2 (../agents/codex-leitor.md), somente leitura. Escrita e
  pesquisa: camada 2 (../agents/escritor.md), com `-s workspace-write` limitado aos alvos do brief.
- Alethe: o fallback de papel (provedor acima de 80%, um nível, só se o outro tem folga) é medido por
  agente, não por modelo; o workflow não depende dele.
- Orquestrador Codex (escolha explícita): não edita arquivos; toda edição vai aos papéis executor-t*.
  Os papéis "Qualquer" servem aos dois orquestradores; os planejadores Codex ficam redundantes,
  sem precisar mudar.
- Papéis no Alethe (#332, substitui AGY-03): executor-t1 (haiku high) ↔ executor-t1-astra
  (gpt-6-astra medium), executor-t2 (sonnet high) ↔ executor-t2-astra (gpt-6-astra high),
  executor-t3 (opus high) sem fallback, escritor-agy sem fallback. reviewer (opus medium) e
  reviewer-high (opus high), somente leitura, com fallback para um papel Codex gpt-6-astra somente
  leitura; somente leitura só cai para somente leitura. O Claude roda somente leitura (Read, Grep,
  Glob) desde alethe-agents#207, no build com o commit 05b882c. Planejadores e validador: gpt-6-astra,
  somente leitura e sem fallback. O dono aplica os papéis em Preferências > Orquestração.

## Leitura no plano da OpenAI (fase 3 da #5, aprovada em 10/10/2026)

Dono por tipo de leitura: tabela em [Investigador e níveis](#leitura-dono). Codex (../agents/codex-leitor.md): fora do Alethe, ferramenta codex_read do Mod astra-review; no Alethe,
alethe_delegate com readOnly. A implementação fica com modelos Claude, inclusive T1; o Codex só
implementa na reserva (Camadas). O coordenador confere a resposta no código antes de agir e registra no
estado o caminho e o que confirmou ou refutou. Limites: Codex nunca implementa sem troca registrada;
pergunta sem segredos; effort pelo nível (medium T1/T2, high T3).

## AGY e perfis do AGY

Movido para [routing-details.md › AGY: por escolha explícita, orquestrador de último recurso](routing-details.md#agy-por-escolha-explícita-orquestrador-de-último-recurso): modelos por nível no AGY, ordem de fornecedor, cota e worker AGY.

Movido para [routing-details.md › Perfis adicionais AGY: regras de routing.md](routing-details.md#perfis-adicionais-agy-regras-de-routingmd): perfis fora da seleção, ID da variante e lista do worker do Alethe.

## Orquestradores

Orquestradores, prioridade fixa: Claude Code, Codex, AGY (o último). AGY orquestra só por
escolha explícita, nunca como fallback automático; então planejador e revisor Opus 5.5
(medium em T1/T2, high em T3). Revisão segue review.md (revisor independente).

## Haiku

Movido para [routing-details.md › Haiku (ROTA-04, aprovado pelo dono em 15/10/2026)](routing-details.md#haiku-rota-04-aprovado-pelo-dono-em-15102026): papéis do Haiku (executor T1, Explore, haiku-ops) e a lista "Nunca".

## Campanhas e limites

C1: resultado independente; C2: tarefas/dependências encadeadas; C3: integração sensível
ou irreversível com checkpoints assistidos. Investigador classifica campanha e tarefas
separadamente; classe não fixa modelo para todas. Janela noturna é eixo independente:
exige preflight, dependências cumpridas e opt-in; tarefa bloqueada não executa.

Matriz governa próximas chamadas autorizadas, não troca sessão/default global silenciosamente; a troca
por turno do Mod rota (modo auto) aparece no `/rota` e em `.workflow/local/rotas.jsonl`, e o
default do settings não muda.
Código relevante mantém uma revisão read-only do revisor: medium T1/T2, high T3; correção pelo
executor selecionado. Não abrir chamada só para preencher coluna. Luna fica fora da seleção
automática até avaliação; Haiku só nos papéis da seção Haiku (routing-details.md); xhigh/max exigem justificativa/aprovação específica;
ultra/ultracode não habilitados (orquestração adicional). Permissão/quota/recusa: parar, exceto a reserva T1/T2 de Camadas.
Ausência de transporte admite somente a alternativa já prevista em review.md, antes da
primeira tentativa, com o mesmo escopo e limite; nunca repetir uma revisão que falhou.
Registrar modelo observado separado do solicitado; ausente = não atestado. Medir qualidade,
input/cache_create/cache_read/output e tempo antes de promover vencedor. Preço de API
não comprova economia de assinatura. Sem novo orçamento de revisão por reclassificação.

Uma tarefa mantém um coordenador; sem recursão, autodelegação redundante ou troca por quota fora da reserva de Camadas.
Chamada exige delegation.md + estado persistido; não repetir chamada em andamento.
Goals: listar catálogo do projeto com estados/bloqueios; ausência explícita. Reservar não executa.
A noite mantém preflight/estado próprios (GPT #42); fila em GPT #43. Hook não libera execução noturna.
Medições, histórico e lista de modelos do AGY (sem regra nova): [routing-details.md](routing-details.md). Núcleo: ../workflow.md.
