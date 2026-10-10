# Roteamento por tarefa

Aplicar sem exigir pedido explícito de delegação. Ler uma vez por tarefa; escolha do usuário prevalece.

- Pergunta/status/documentação pequena: agente ativo.
- Código: Claude Code executa conforme nível investigado abaixo.
- Arquitetura, múltiplos componentes ou aceite ambíguo: Codex planeja/orquestra; Claude Code implementa.
- Código relevante pronto: revisão independente do revisor, uma tentativa conforme review.md (em T3, mais uma após NOT APPROVED).
- Auditoria/corpus/pesquisa/achados: AGY (papel principal), fontes e arquivos de saída delimitados.

## Investigador e níveis (aprovado em 21/09/2026)

Investigador é quem conduz a investigação, não outro agente obrigatório. O agente ativo
faz a triagem read-only; se já há investigação delegada, seu dono classifica e devolve
a decisão. Não chamar modelo só para classificar. O investigador decide; o coordenador
registra e aplica, esclarecendo contradições de escopo/permissão. Escolha do usuário prevalece.

Antes de implementar/delegar, registrar nível, risco, ambiguidade, alcance, evidência
arquivo:linha, confiança (alta/média/baixa), aceite e modelo/effort por fase. Usar o maior
nível sustentado pelos critérios, não soma nem número de tokens/arquivos.

| Nível | Critério | Executor Claude | Planejador Codex se necessário | Auditor AGY padrão se necessário |
|---|---|---|---|---|
| T0 | Determinístico: consulta, contagem, check mecânico | ferramenta, sem nova chamada | agente ativo | sem nova chamada |
| T1 | Baixo risco, causa/escopo locais, aceite objetivo | claude-sonnet-5-5 / medium | gpt-6.1-sol / medium | claude-sonnet-5-5-medium |
| T2 | Integração entre componentes, hipóteses concorrentes, regressão relevante | claude-opus-5-5 / high | gpt-6.1-sol / high | claude-opus-5-5-high |
| T3 | Segurança/permissões sensíveis, perda de dados/irreversibilidade, arquitetura ou incerteza sistêmica | claude-fable-5-1 / high | gpt-6-astra / high | claude-opus-5-5-high |

Modelos em uso (conferidos em 30/09/2026): Claude Code prioriza claude-sonnet-5-5 e
claude-opus-5-5, mais claude-fable-5-1; Codex usa gpt-6.1-sol, gpt-6-astra, gpt-6-sol e
gpt-6-luna. Linhas anteriores (claude-*-5, gpt-5.6-*) saem da seleção.

Incerteza não investigada não vira T1: manter classificação provisória e investigar
antes de executar. Para investigação delegada, a triagem propõe nível provisório e o
investigador confirma/revisa antes da próxima fase. Reclassificar com evidência/motivo,
nunca como fallback por quota/recusa. Tarefa pequena pode ser T3; longa pode ser T1.
Pergunta/status/docs simples ficam no agente ativo, sem migração de sessão.

## Leitura no plano da OpenAI (fase 3 da #5, aprovada em 10/10/2026)

Trabalho só de leitura vai para o Codex: verificar a issue contra o código antes de implementar,
investigação delimitada e triagem do registro de campanhas ou de achados. Fora do Alethe, ferramenta
codex_read do Mod astra-review; no Alethe, alethe_delegate com readOnly. A implementação fica no
Claude Code, inclusive T1. O coordenador confere a resposta no código antes de agir e registra no
estado o caminho e o que confirmou ou refutou. Limites: Codex nunca implementa automaticamente;
pergunta sem segredos; effort pelo nível (medium T1/T2, high T3).

## AGY: pesquisador e orquestrador de último recurso

Papel principal do AGY: pesquisador e derivados (pesquisa, auditoria, corpus, achados),
só leitura com saída delimitada. Padrão inicial, não medido: Sonnet 5.5
(claude-sonnet-5-5-medium) para pesquisa de rotina; Opus 5.5 (claude-opus-5-5-high) para
auditoria ou pesquisa ampla. Workers AGY na Orquestração do Alethe (campanha AGY, ainda não
implementado) seguem esse papel; código fica com os executores Claude/Codex.
Orquestradores, prioridade fixa: Claude Code, Codex, AGY (o último). AGY orquestra só por
escolha explícita, nunca como fallback automático; então planejador e revisor Opus 5.5
(medium em T1/T2, high em T3). Revisão segue review.md (revisor independente).

## Perfis adicionais AGY

- gemini-3.1-pro-high: candidato T3 para contexto amplo, dependências e arquitetura.
- claude-sonnet-5-5-{low,medium,high}: candidato T1/T2 de código/documentação.
- claude-opus-5-5-{low,medium,high}: candidato T2/T3 de código, orquestração e revisão.
- Investigador pode escolher esses perfis aprovados com justificativa; superioridade
  ainda não medida. Não chamar vários para a mesma auditoria sem avaliação delimitada
  e autorizada. Não substituem a revisão do revisor.
- Gemini, Sonnet 5.5 e Opus 5.5: escolher o ID da variante (o esforço vem no ID), sem
  inventar variantes nem repassar --effort. Não transferir parâmetros ou supor mesma
  assinatura/quota do Claude Code.
- Modelos do AGY (agy models, AGY 1.2.16, 04/10/2026): gemini-3.8/3.7/3.6-flash-{low,medium,high},
  gemini-3.1-pro-{low,high}, claude-opus-5-5-{low,medium,high},
  claude-sonnet-5-5-{low,medium,high} e gpt-oss-120b-medium.
- Pendente para o worker AGY no Alethe: o CLI aceita --effort low|medium|high|xhigh|max, mas
  nem todo modelo muda de esforço. Gemini Flash, Sonnet 5.5 e Opus 5.5 têm low/medium/high no
  ID; Gemini 3.1 Pro só low/high; GPT-OSS 120B (Medium) tem esforço fixo.
  O papel/worker AGY só deve oferecer os esforços de cada modelo e não repassar
  --effort aos fixos; medir antes se o CLI recusa ou ignora --effort nesses casos.

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
