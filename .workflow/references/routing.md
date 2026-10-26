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
| T0 | Determinístico: consulta, contagem, check mecânico | ferramenta, sem nova chamada | agente ativo | sem nova chamada |
| T1 | Baixo risco, causa/escopo locais, aceite objetivo | claude-haiku-5-5 / high, escalar a claude-sonnet-5-5 / medium | gpt-6-astra / medium; implementa na reserva | claude-sonnet-5-5-medium / claude-sonnet-5-5-medium |
| T2 | Integração entre componentes, hipóteses concorrentes, regressão relevante | claude-sonnet-5-5 / high, escalar a claude-opus-5-5 / high | gpt-6-astra / high; implementa na reserva | claude-sonnet-5-5-high, escalar a claude-opus-5-5-high / claude-sonnet-5-5-medium |
| T3 | Segurança/permissões sensíveis, perda de dados/irreversibilidade, arquitetura ou incerteza sistêmica | claude-opus-5-5 / high | gpt-6-astra / high; não implementa | não implementa (fica no Claude Code) / claude-sonnet-5-5-high |

Modelos em uso (revistos em 10/10/2026; evidência em ../evals/modelos-2026-10-10.md):
Claude Code usa claude-sonnet-5-5 e claude-opus-5-5. claude-fable-5-1 saiu do T3. Codex usa
gpt-6-astra (leitura, escrita e reserva do executor); gpt-6.1-sol e gpt-6-sol ficam fora da seleção
por falta de dado público suficiente. Linhas anteriores (claude-*-5, gpt-5.6-*) saem da seleção.
Números e fontes: [routing-details.md](routing-details.md) › Modelos em uso.

IDs só aqui (agent-workflow-lab#43). No Claude Code, settings, frontmatter de agentes e delegações
usam alias (opus, sonnet, haiku, fable, opusplan, inherit; [1m] aceito); verify.py confere settings
e frontmatter (lab e ~/.claude/agents) e falha com ID fixo. Alias → ID medido: routing-details.md ›
Modelos em uso. Precedência do subagente: model da chamada > model do
frontmatter > CLAUDE_CODE_SUBAGENT_MODEL > modelo da sessão. O menu /model ainda oferece linhas
antigas (Sonnet 5) e Enter salva como padrão: escolher pelo alias ou usar s (só na sessão).

T2 no Sonnet e T1 no Haiku (ROTA-04, aprovado pelo dono em 15/10/2026): escalar ao Opus quando o
Sonnet travar, falhar no aceite ou a revisão achar P1 que ele não corrige; T1 sobe do Haiku ao
Sonnet nas mesmas condições. Evidência: ../evals/rota-03-2026-10-15.md.

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
| 3 | AGY | Só por escolha explícita (cota do plano PRO baixa), só com arquivos (sem comandos): implementa T1/T2 ou escreve | Claude do AGY, depois gpt-oss-120b, depois Gemini 3.8 Flash; Gemini 4 Argon só como reserva (seção AGY) |

- Implementação: camada 1. Com a cota do Claude apertada (aviso de limite ou escolha do dono), o
  coordenador registra a troca no estado e passa T1/T2 ao Codex: `codex exec -m gpt-6-astra -c
  model_reasoning_effort=<medium T1, high T2> -s workspace-write`, numa worktree própria. T3 fica
  na camada 1: sem cota, espera. Erro ou recusa não é troca: parar.
- Codex implementando roda sem os hooks do workflow (`features.hooks=false`, SEG-02): só o sandbox
  protege. Nunca com `--dangerously-bypass-approvals-and-sandbox`, `--yolo` ou `danger-full-access`;
  brief sem segredos; proibido no noturno (noite.md).
- Revisão (#332, aprovado pelo dono em 22/10/2026): o revisor é independente do implementador, não do
  orquestrador. Todo código é revisado por claude-opus-5-5 (medium em T1/T2, high em T3), em contexto
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

## AGY: por escolha explícita, orquestrador de último recurso

Desde a ROTA-06 (16/10/2026) o AGY entra só por escolha explícita: a cota do plano PRO é baixa, e
reserva, escrita e auditoria foram para o Codex. Quando escolhido, vale o que segue. Aprovado pelo
dono em 10/10/2026; prioridade de fornecedor dentro do AGY em 11/10/2026: Anthropic, depois OpenAI,
depois Google. Claude do AGY implementa T1/T2 com a cota do AGY (claude-sonnet-5-5-medium em T1,
claude-sonnet-5-5-high em T2, claude-opus-5-5-high como escalonamento) e escreve docs, changelog e
relatórios (claude-sonnet-5-5-medium; high em T3). T3 não implementa no AGY. Em 2º lugar,
gpt-oss-120b-medium (esforço fixo, contexto de 128k). Em 3º, Gemini 3.8 Flash; por ter alta taxa de
alucinação e poucos bugs achados, seus achados passam pelo Codex (codex_read) ou pelo Claude antes de
virar issue ou ação. gemini-4-argon-high fica como reserva, por escolha explícita na tarefa (#151,
18/10/2026): a qualidade foi a dos outros braços, mas 3 PRs gastaram ~46% da cota semanal do Argon.
Medições: routing-details.md › Medições AGY; ../evals/rota-06-argon-2026-10-18.md.
Cota (#151): ler o `/usage` do agy antes e depois de cada uso e anotar no eval ou no estado da tarefa. Replay no AGY só por escolha explícita, 1 PR por rodada (`bin/replay.py` recusa mais). Sondas de capacidade (flags, sandbox, ferramentas) no Gemini 3.8 Flash. No Alethe o app não troca de modelo dentro do AGY sozinho. Worker AGY (AGY-04): sem comandos (só lê, busca e edita arquivos), sem hooks globais nem GEMINI.md do dono, sempre em worktree própria; git, testes e builds ficam com o coordenador; mesma revisão independente (review.md).
Orquestradores, prioridade fixa: Claude Code, Codex, AGY (o último). AGY orquestra só por
escolha explícita, nunca como fallback automático; então planejador e revisor Opus 5.5
(medium em T1/T2, high em T3). Revisão segue review.md (revisor independente).

## Perfis adicionais AGY

- Fora da seleção automática: gemini-4-argon-low/medium (só o high foi medido). gemini-3.7/3.6-flash e gemini-3.1-pro saíram do AGY.
- Investigador pode escolher outro perfil do AGY com justificativa registrada. Não chamar vários para a mesma auditoria sem avaliação delimitada e autorizada; não substituem o revisor.
- ID da variante (o esforço vem no ID) ou família com --effort, nunca os dois (o agy recusa na partida). Não inventar variantes, não transferir parâmetros nem supor mesma assinatura/quota do Claude Code.
- O worker AGY do Alethe oferece só: Sonnet 5.5 e Gemini 3.8 Flash medium/high pela família, claude-opus-5-5-high e gpt-oss-120b-medium (esforço fixo) pelo ID. Lista de modelos: routing-details.md.

## Haiku (ROTA-04, aprovado pelo dono em 15/10/2026)

Haiku recebe tarefas inteiras, repetitivas e já especificadas; evidência em
../evals/rota-03-2026-10-15.md. O coordenador confere o resultado antes de usá-lo.

- Executor T1 (tabela de níveis), com escalada ao Sonnet.
- Busca ampla de arquivos: Explore com model haiku (tabela em [Investigador e níveis](#leitura-dono)).
- Tarefa operacional: subagente haiku-ops (../agents/haiku-ops.md) para rascunho de commit/PR,
  comandos do registro de campanhas, resumo de log ou relatório, inventário e contagem, renomear
  lista aprovada e edição pequena exata. Ele devolve a tarefa quando falta insumo.
- Dentro de tarefa de código não há delegação forçada: o Opus gastou ~1/4 do custo em leitura
  nas 12 rodadas da ROTA-03, abaixo do limiar de 1/3.
- Nunca: revisão, adjudicação, verificação, gates, classificação de nível, T2/T3, refatoração
  multiarquivo, depuração entre dependências e loops autônomos longos.

## Campanhas e limites

C1: resultado independente; C2: tarefas/dependências encadeadas; C3: integração sensível
ou irreversível com checkpoints assistidos. Investigador classifica campanha e tarefas
separadamente; classe não fixa modelo para todas. Janela noturna é eixo independente:
exige preflight, dependências cumpridas e opt-in; tarefa bloqueada não executa.

Matriz governa próximas chamadas autorizadas, não troca sessão/default global silenciosamente.
Código relevante mantém uma revisão read-only do revisor: medium T1/T2, high T3; correção pelo
executor selecionado. Não abrir chamada só para preencher coluna. Luna fica fora da seleção
automática até avaliação; Haiku só nos papéis da seção Haiku; xhigh/max exigem justificativa/aprovação específica;
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
