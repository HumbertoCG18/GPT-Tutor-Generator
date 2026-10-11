# Roteamento por tarefa

Aplicar sem exigir pedido explícito de delegação. Ler uma vez por tarefa; escolha do usuário prevalece.

- Pergunta/status/documentação pequena: agente ativo.
- Código: modelos Claude implementam conforme nível investigado abaixo (Claude Code; em T1/T2 também o worker AGY do Alethe; ver Camadas).
- Arquitetura, múltiplos componentes ou aceite ambíguo: Codex planeja/orquestra; Claude Code implementa.
- Código relevante pronto: revisão independente do revisor, uma tentativa conforme review.md (em T3, mais uma após NOT APPROVED).
- Escrita, auditoria em volume, corpus e pesquisa: AGY por prioridade de fornecedor (Claude Sonnet 5.5,
  depois gpt-oss-120b, depois Gemini 3.8 Flash), fontes e arquivos de saída delimitados.

## Investigador e níveis (aprovado em 21/09/2026)

Investigador é quem conduz a investigação, não outro agente obrigatório. O agente ativo
faz a triagem read-only; se já há investigação delegada, seu dono classifica e devolve
a decisão. Não chamar modelo só para classificar. O investigador decide; o coordenador
registra e aplica, esclarecendo contradições de escopo/permissão. Escolha do usuário prevalece.

Antes de implementar/delegar, registrar nível, risco, ambiguidade, alcance, evidência
arquivo:linha, confiança (alta/média/baixa), aceite e modelo/effort por fase. Usar o maior
nível sustentado pelos critérios, não soma nem número de tokens/arquivos.

| Nível | Critério | Executor Claude | Planejador Codex se necessário | Worker AGY: implementação / escrita e auditoria |
|---|---|---|---|---|
| T0 | Determinístico: consulta, contagem, check mecânico | ferramenta, sem nova chamada | agente ativo | sem nova chamada |
| T1 | Baixo risco, causa/escopo locais, aceite objetivo | claude-sonnet-5-5 / medium | gpt-6-astra / medium | claude-sonnet-5-5-medium / claude-sonnet-5-5-medium |
| T2 | Integração entre componentes, hipóteses concorrentes, regressão relevante | claude-opus-5-5 / high | gpt-6-astra / high | claude-sonnet-5-5-high, escalar a claude-opus-5-5-high / claude-sonnet-5-5-medium |
| T3 | Segurança/permissões sensíveis, perda de dados/irreversibilidade, arquitetura ou incerteza sistêmica | claude-opus-5-5 / high | gpt-6-astra / high | não implementa (fica no Claude Code) / claude-sonnet-5-5-high |

Modelos em uso (revistos em 10/10/2026 com dados públicos de benchlm.ai, Artificial Analysis e
Arena, e com as medições internas de 09–10/10; evidência em ../evals/modelos-2026-10-10.md):
Claude Code usa claude-sonnet-5-5 e claude-opus-5-5. claude-fable-5-1 saiu do T3: ficou abaixo do
Opus 5.5 em FrontierSWE v2 (56,3 × 62,3), DeepSWE (67,4 × 74,2) e SWE-bench Pro (81,2 × 89,9),
e as T3 de 09/10 foram feitas pelo Opus. Codex usa gpt-6-astra (revisão, leitura e planejamento);
gpt-6.1-sol e gpt-6-sol ficam fora da seleção por falta de dado público suficiente. Linhas anteriores
(claude-*-5, gpt-5.6-*) saem da seleção.

Incerteza não investigada não vira T1: manter classificação provisória e investigar
antes de executar. Para investigação delegada, a triagem propõe nível provisório e o
investigador confirma/revisa antes da próxima fase. Reclassificar com evidência/motivo,
nunca como fallback por quota/recusa. Tarefa pequena pode ser T3; longa pode ser T1.
Pergunta/status/docs simples ficam no agente ativo, sem migração de sessão.

## Camadas (aprovado pelo dono em 11/10/2026)

| Camada | Ferramenta | Faz | Modelos |
|---|---|---|---|
| 1 | Claude Code | Orquestra (padrão) e implementa | Executor Claude da tabela de níveis |
| 2 | Codex | Só leitura: planeja se necessário, revisa, investiga, valida | gpt-6-astra, effort pelo nível |
| 3 | AGY | Capacidade extra, só com arquivos (sem comandos): implementa T1/T2 quando a cota da camada 1 aperta ou por escolha; escreve e audita | Claude do AGY, depois gpt-oss-120b, depois Gemini 3.8 Flash (seção AGY) |

- Implementação: camada 1, caindo para a 3; nunca para a 2. T3 fica na camada 1: sem cota, espera.
- Leitura e revisão: camada 2. O revisor é independente do implementador (Claude), não do
  orquestrador; sem cota do Codex, a revisão espera e nunca passa ao fornecedor do implementador.
- Escrita: camada 3.
- Cota: a passagem da camada 1 para a 3 é o fallback de papel configurado no Alethe (provedor acima
  de 80%, um nível, só se o outro tem folga). Fora dele vale "Permissão/quota/recusa: parar".
- Orquestrador Codex (escolha explícita): não edita arquivos; toda edição vai aos papéis executor-t*.
  Os papéis "Qualquer" servem aos dois orquestradores; os planejadores Codex ficam redundantes,
  sem precisar mudar.
- Papéis no Alethe (AGY-03): executor-t1 ↔ executor-t1-agy (Sonnet 5.5 medium), executor-t2 ↔
  executor-t2-agy (Opus 5.5 high, o mesmo modelo do principal), executor-t3 sem fallback,
  escritor-agy (Claude Sonnet 5.5 medium). Revisores, planejadores e validador: gpt-6-astra, somente
  leitura e sem fallback (somente leitura só cai para somente leitura, e só o Codex roda assim).

## Leitura no plano da OpenAI (fase 3 da #5, aprovada em 10/10/2026)

Trabalho só de leitura vai para o Codex: verificar a issue contra o código antes de implementar,
investigação delimitada e triagem do registro de campanhas ou de achados. Fora do Alethe, ferramenta
codex_read do Mod astra-review; no Alethe, alethe_delegate com readOnly. A implementação fica com
modelos Claude (Claude Code ou worker AGY), inclusive T1. O coordenador confere a resposta no código antes de agir e registra no
estado o caminho e o que confirmou ou refutou. Limites: Codex nunca implementa automaticamente;
pergunta sem segredos; effort pelo nível (medium T1/T2, high T3).

## AGY: workers de implementação e escrita, orquestrador de último recurso

Aprovado pelo dono em 10/10/2026; prioridade de fornecedor dentro do AGY em 11/10/2026: Anthropic,
depois OpenAI, depois Google. Claude do AGY implementa T1/T2 com a cota do AGY
(claude-sonnet-5-5-medium em T1, claude-sonnet-5-5-high em T2, claude-opus-5-5-high como
escalonamento) e escreve docs, changelog e relatórios (claude-sonnet-5-5-medium; high em T3). T3 não
implementa no AGY. Em 2º lugar, gpt-oss-120b-medium (esforço fixo, contexto de 128k, AA Agentic
6,2): medido em 11/10 como worker (escreveu o arquivo, não rodou comando, 5,5k tokens, 6 s; uma
amostra trivial). Em 3º, Gemini 3.8 Flash; por ter 55,2% de alucinação (AA-Omniscience) e poucos
bugs achados (Bug Hunt 18), seus achados passam pelo Codex (codex_read) ou pelo Claude antes de virar
issue ou ação. A ordem vale pela escolha do papel: no Alethe o fallback desce um nível e a cota do
AGY é lida por fornecedor, então o app não troca de modelo dentro do AGY sozinho.
Desde AGY-04 (alethe-agents #158) o worker AGY roda como agente gerenciado `alethe-worker`, sem
comandos (só lê, busca e edita arquivos), sem os hooks globais e o GEMINI.md do dono, sempre numa
worktree própria; git, testes e builds ficam com o coordenador depois do turno. Código de worker AGY
recebe a mesma revisão independente (review.md).
Orquestradores, prioridade fixa: Claude Code, Codex, AGY (o último). AGY orquestra só por
escolha explícita, nunca como fallback automático; então planejador e revisor Opus 5.5
(medium em T1/T2, high em T3). Revisão segue review.md (revisor independente).

## Perfis adicionais AGY

- Fora da seleção automática até medição no nosso uso: gemini-3.7-flash e gemini-3.6-flash
  (abaixo do 3.8 em DeepSWE, Terminal-Bench e AA Coding), gemini-3.1-pro (AA Intelligence 30 × 41
  do 3.8 Flash, custo parecido).
- Investigador pode escolher outro perfil do AGY com justificativa registrada; a superioridade no
  nosso uso ainda não foi medida. Não chamar vários para a mesma auditoria sem avaliação delimitada
  e autorizada. Não substituem a revisão do revisor.
- Gemini, Sonnet 5.5 e Opus 5.5: ID da variante (o esforço vem no ID) ou família com --effort,
  nunca os dois (medido na 1.3.3: o agy recusa na partida); sem inventar variantes. Não transferir
  parâmetros ou supor mesma assinatura/quota do Claude Code.
- Modelos do AGY (agy models, AGY 1.3.2 em 10/10/2026, sem mudança desde a 1.2.16; o CLI se atualiza sozinho, 1.3.3 no mesmo dia): gemini-3.8/3.7/3.6-flash-{low,medium,high},
  gemini-3.1-pro-{low,high}, claude-opus-5-5-{low,medium,high},
  claude-sonnet-5-5-{low,medium,high} e gpt-oss-120b-medium.
- Esforço: o CLI aceita --effort low|medium|high|xhigh|max, mas nem todo modelo muda de esforço.
  Gemini Flash, Sonnet 5.5 e Opus 5.5 têm low/medium/high no ID; Gemini 3.1 Pro só low/high;
  GPT-OSS 120B (Medium) tem esforço fixo. O worker AGY do Alethe oferece só os aprovados: Sonnet
  5.5 e Gemini 3.8 Flash medium/high pela família, Opus 5.5 pelo ID claude-opus-5-5-high e
  gpt-oss-120b-medium pelo ID (esforço fixo).

## Campanhas e limites

C1: resultado independente; C2: tarefas/dependências encadeadas; C3: integração sensível
ou irreversível com checkpoints assistidos. Investigador classifica campanha e tarefas
separadamente; classe não fixa modelo para todas. Janela noturna é eixo independente:
exige preflight, dependências cumpridas e opt-in; tarefa bloqueada não executa.

Matriz governa próximas chamadas autorizadas, não troca sessão/default global silenciosamente.
Código relevante mantém uma revisão read-only do revisor: medium T1/T2, high T3; correção pelo
executor selecionado. Não abrir chamada só para preencher coluna. Haiku/Luna ficam fora
da seleção automática até avaliação; xhigh/max exigem justificativa/aprovação específica;
ultra/ultracode não habilitados (orquestração adicional). Permissão/quota/recusa: parar.
Ausência de transporte admite somente a alternativa já prevista em review.md, antes da
primeira tentativa, com o mesmo escopo e limite; nunca repetir uma revisão que falhou.
Registrar modelo observado separado do solicitado; ausente = não atestado. Medir qualidade,
input/cache_create/cache_read/output e tempo antes de promover vencedor. Preço de API
não comprova economia de assinatura. Sem novo orçamento de revisão por reclassificação.

Uma tarefa mantém um coordenador; sem recursão, autodelegação redundante ou troca por quota.
Chamada exige delegation.md + estado persistido; não repetir chamada em andamento.
Goals: listar catálogo do projeto com estados/bloqueios; ausência explícita. Reservar não executa.
A noite mantém preflight/estado próprios (#42); fila em #43. Hook não libera execução noturna.
Detalhes operacionais e validação: [routing-details.md](routing-details.md), somente ao configurar
hooks, integrar noite ou resolver dúvida de papéis. Núcleo: ../workflow.md.
