# Roteamento por tarefa

Aplicar sem exigir pedido explícito de delegação. Ler uma vez por tarefa; escolha do usuário prevalece.

- Pergunta/status/documentação pequena: agente ativo.
- Código: Claude Code executa conforme nível investigado abaixo.
- Arquitetura, múltiplos componentes ou aceite ambíguo: Codex planeja/orquestra; Claude Code implementa.
- Código relevante pronto: revisão Astra independente, uma tentativa conforme review.md.
- Auditoria/corpus/pesquisa/achados: AGY, fontes e arquivos de saída delimitados.

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
| T1 | Baixo risco, causa/escopo locais, aceite objetivo | claude-sonnet-5 / medium | gpt-5.6-terra / medium | gemini-3.8-flash-low |
| T2 | Integração entre componentes, hipóteses concorrentes, regressão relevante | claude-opus-5 / high | gpt-5.6-sol / high | gemini-3.8-flash-medium |
| T3 | Segurança/permissões sensíveis, perda de dados/irreversibilidade, arquitetura ou incerteza sistêmica | claude-fable-5-1 / high | gpt-6-astra / high | gemini-3.8-flash-high |

Incerteza não investigada não vira T1: manter classificação provisória e investigar
antes de executar. Para investigação delegada, a triagem propõe nível provisório e o
investigador confirma/revisa antes da próxima fase. Reclassificar com evidência/motivo,
nunca como fallback por quota/recusa. Tarefa pequena pode ser T3; longa pode ser T1.
Pergunta/status/docs simples ficam no agente ativo, sem migração de sessão.

## Perfis adicionais AGY

- gemini-3.1-pro-high: candidato T3 para contexto amplo, dependências e arquitetura.
- claude-sonnet-4-6: candidato T1/T2 de código/documentação, variante Thinking.
- claude-opus-4-6-thinking: candidato T3 de código, variante Thinking.
- Investigador pode escolher esses perfis aprovados com justificativa; superioridade
  ainda não medida. Não chamar vários para a mesma auditoria sem avaliação delimitada
  e autorizada. Não substituem a revisão Astra.
- Gemini: escolher ID da variante, sem inventar variantes. Sonnet/Opus Thinking no AGY:
  esforço individual não anunciado; omitir --effort e registrar não informado. Não
  transferir parâmetros ou supor mesma assinatura/quota do Claude Code.

## Campanhas e limites

C1: resultado independente; C2: tarefas/dependências encadeadas; C3: integração sensível
ou irreversível com checkpoints assistidos. Investigador classifica campanha e tarefas
separadamente; classe não fixa modelo para todas. Janela noturna é eixo independente:
exige preflight, dependências cumpridas e opt-in; tarefa bloqueada não executa.

Matriz governa próximas chamadas autorizadas, não troca sessão/default global silenciosamente.
Código relevante mantém uma revisão Astra read-only: medium T1/T2, high T3; correção pelo
executor selecionado. Não abrir chamada só para preencher coluna. Haiku/Luna ficam fora
da seleção automática até avaliação; xhigh/max exigem justificativa/aprovação específica;
ultra/ultracode não habilitados (orquestração adicional). Ausência/permissão/quota: parar.
Registrar modelo observado separado do solicitado; ausente = não atestado. Medir qualidade,
input/cache_create/cache_read/output e tempo antes de promover vencedor. Preço de API
não comprova economia de assinatura. Sem novo orçamento de revisão por reclassificação.

Uma tarefa mantém um coordenador; sem recursão, autodelegação redundante ou troca por quota.
Chamada exige delegation.md + estado persistido; não repetir chamada em andamento.
Goals: listar catálogo do projeto com estados/bloqueios; ausência explícita. Reservar não executa.
A noite mantém preflight/estado próprios (#42); fila em #43. Hook não libera execução noturna.
Detalhes operacionais e validação: [routing-details.md](routing-details.md), somente ao configurar
hooks, integrar noite ou resolver dúvida de papéis. Núcleo: ../workflow.md.
