# Modelos, níveis de tarefa/campanha e diagnóstico noturno

Estado prevalente21/09: matriz ativada após aprovação; benchmark posteriormente autorizado e concluído12/12chamadas,quatro perfis3/3acertos. [Resultado e limitações](2026-09-21-medicao-agy-campanhas.md). Proposta/não executado abaixo descrevem o momento original. Diagnóstico #42 continua não executado e depende de autorização específica; Gate2 pendente.

Atualização21/09 após aprovação: matriz aprovada pelo usuário, com classificação decidida
pelo investigador e perfis adicionais AGY Pro3.1/Sonnet4.6/Opus4.6Thinking. Política vigente
na fonte canônica agent-workflow-lab/references/routing.md (snapshot .workflow/references/routing.md).
Este relatório preserva a proposta original abaixo como histórico, não uma segunda regra.
Nenhum benchmark ou diagnóstico live foi autorizado por essa aprovação de matriz.

Avaliação proposta, ainda não executada: congelar3casos sanitizados (erro local com solução
conhecida, dependência entre módulos, caso correto sem achado) e respectivos critérios/gabarito
antes de chamar modelos; comparar Flash3.8high,Pro3.1high,Sonnet4.6Thinking,Opus4.6Thinking
com mesmo conteúdo/limites/permissões.12chamadas no máximo,sem retries,em campanha separada
com orçamento previamente aprovado. Medir acerto/omissão crítica,falso positivo,evidência
arquivo:linha,violações de escopo,tempo e input/cache/output. Falha de autorização/formato
não equivale a auditoria correta. Não escolher vencedor só por velocidade ou texto convincente;
ranking por domínio,3casos são piloto sem significância estatística. Preferir evidência
determinística/gabarito congelado; não adicionar outro revisor pago para pontuar opinião.

Data: 21/09/2026. Frente #44 (inventário/proposta) e #42 (diagnóstico). Status: inventário consultado; matriz PROPOSTA, não ativada. Gate2 pendente. Não muda defaults, allowlists do supervisor, hooks ou contadores de revisão. Ler sob demanda, não no bootstrap.

## 1. O que significa disponível

Listagem é descoberta de capacidade, não prova de inferência, quota, cobrança ou autorização operacional. Catálogo da API não equivale ao seletor da assinatura. Este registro cobre todas as entradas devolvidas pelas consultas abaixo, não qualquer ID legado que a CLI aceite como texto. Atualizar antes de adoção se o catálogo mudar.

Métodos sem geração de resposta de modelo:

- Claude Code2.1.278: seletor /model da conta Claude Max e resposta control initialize/models em safe-mode; sessão de inspeção4252a010-ed6d-42a2-ae4e-bc6f887628e4 encerrada sem selecionar modelo. Safe-mode exclui customizações; não testa overrides/plugins. Controle retornou5entradas,4famílias; Default duplica Opus. O menu visual indicava duas entradas fora da janela, mas o catálogo de controle completo abaixo retornou5; não inventar modelos adicionais.
- Codex CLI0.155.1: app-server stdio initialize + model/list(limit100,includeHidden=true);7entradas,nextCursor=null; nenhuma thread/turn de inferência criada.
- AGY: agy models consultado ao vivo;14entradas. --help anuncia --effort low/medium/high; variantes abaixo já codificam esforço. Compatibilidade de cada override não testada por inferência.

### Claude Code

| Família | Entrada do seletor/ID resolvido | Efforts anunciados pelo controle |
|---|---|---|
| Opus5 | default e opus[1m] → claude-opus-5[1m] | low,medium,high,xhigh,max |
| Fable5.1 | claude-fable-5-1[1m] → claude-fable-5-1 | low,medium,high,xhigh,max |
| Sonnet5 | sonnet → claude-sonnet-5 | low,medium,high,xhigh,max |
| Haiku4.5 | haiku → claude-haiku-4-5-20251001 | nenhum effort anunciado; não passar low por suposição |

Fable foi observado em execuções anteriores deste workflow; as demais entradas desta tabela foram descobertas, não exercitadas neste inventário. Defaults globais não alterados. Ultracode não é modelo nem effort simples: inclui orquestração própria, portanto não habilitar junto ao nosso coordenador sem desenho/aceite explícito. Os nomes de effort não equivalem a unidades comparáveis entre modelos.

Fontes: [configuração Claude Code](https://code.claude.com/docs/en/model-config), [IDs atuais e capacidades](https://platform.claude.com/docs/en/models/overview). O controle local é a evidência da tabela; não extrapolar documentação de API para direito de uso na assinatura.

### Codex

| ID exato | Visibilidade | Efforts retornados | Padrão retornado |
|---|---|---|---|
| gpt-6-astra | visível | low,medium,high,xhigh,max,ultra | medium |
| gpt-5.6-sol | visível | low,medium,high,xhigh,max,ultra | low |
| gpt-5.6-terra | visível | low,medium,high,xhigh,max,ultra | medium |
| gpt-5.6-luna | visível | low,medium,high,xhigh,max | medium |
| gpt-5.5 | visível | low,medium,high,xhigh | medium |
| gpt-reserve | oculto | low,medium,high,xhigh,max | medium |
| codex-auto-review | oculto | low,medium,high,xhigh,max | medium |

Ocultos ficam inventariados, fora do roteamento proposto. Descoberta não autoriza uso nem contorna políticas. Ultra foi descrito pelo catálogo como raciocínio com delegação automática: manter desativado na proposta para evitar outro coordenador/recursão. Nenhum modelo configurado no app-server atesta qual modelo o provider efetivamente respondeu; o bloqueio do adapter noturno Codex permanece.

Fonte do método: [model/list do app-server](https://learn.chatgpt.com/docs/app-server). Lista e efforts são da consulta local de21/09, incluindo ocultos, não de uma tabela genérica de API.

### AGY

| ID exato retornado | Variante anunciada |
|---|---|
| gemini-3.8-flash-high | Gemini3.8Flash High |
| gemini-3.8-flash-medium | Gemini3.8Flash Medium |
| gemini-3.8-flash-low | Gemini3.8Flash Low |
| gemini-3.7-flash-high | Gemini3.7Flash High |
| gemini-3.7-flash-medium | Gemini3.7Flash Medium |
| gemini-3.7-flash-low | Gemini3.7Flash Low |
| gemini-3.6-flash-high | Gemini3.6Flash High |
| gemini-3.6-flash-medium | Gemini3.6Flash Medium |
| gemini-3.6-flash-low | Gemini3.6Flash Low |
| gemini-3.1-pro-high | Gemini3.1Pro High |
| gemini-3.1-pro-low | Gemini3.1Pro Low |
| claude-sonnet-4-6 | ClaudeSonnet4.6 Thinking; esforço individual não informado |
| claude-opus-4-6-thinking | ClaudeOpus4.6 Thinking; esforço individual não informado |
| gpt-oss-120b-medium | GPT-OSS120B Medium |

Fonte: saída agy models,14entradas. Não criar variantes pro-medium ou claude-*-high ausentes. Preferir Gemini no papel AGY para manter diversidade; modelos Claude no AGY não significam uso da assinatura Claude. Consumo e direitos pertencem ao produto que faz a chamada. Modelo efetivo AGY continua não atestado pelo envelope de resultados que observamos.

## 2. Matriz proposta — precisa de aprovação antes de ativar

Escolher nível ANTES da chamada por risco, ambiguidade, alcance e qualidade do aceite; quantidade de tokens/arquivos é indício, não classificador único. Primeiro tentar ferramenta determinística. Não chamar três CLIs apenas para preencher três papéis.

| Nível | Critério | Implementação Claude | Planejamento Codex, somente se necessário | Auditoria AGY, somente se necessária |
|---|---|---|---|---|
| T0 determinístico | consulta de estado, contagem, checks mecânicos | sem nova chamada LLM | agente ativo/ferramenta | sem nova chamada LLM |
| T1 delimitado | escopo local, baixo risco, aceite objetivo | Sonnet5 medium | Terra medium | Flash3.8 low |
| T2 composto | múltiplos componentes/dependências, regressão relevante | Opus5 high | Sol high | Flash3.8 medium |
| T3 crítico/ambíguo | arquitetura, dados sensíveis, migração irreversível, diagnóstico difícil | Fable5.1 high | Astra high | Flash3.8 high; Pro3.1 high apenas por necessidade demonstrada |

Haiku4.5 (sem effort) e Luna medium: candidatos a triagens mecânicas com linguagem natural, apenas após avaliação fixa; nenhuma chamada para repetir decisão já resolvida por regra. Não começar criando enxame. xhigh/max: exceção justificada por task_id e limite antes da chamada, não promoção automática ao falhar.

Revisão mantém dono e orçamento atuais: uma Astra read-only para código relevante, medium no normal, high no crítico. Nunca reduzir checks/revisão para caber num nível; planejamento não renova a tentativa de revisão. Pergunta/status/docs simples continuam no agente ativo. Não trocar a sessão atual ou modelo escolhido explicitamente pelo usuário de forma invisível: o nível determina a próxima chamada autorizada, não migra histórico sozinho.

Esta matriz ALTERARIA o padrão atual Fable executor em T1/T2: é proposta econômica para aprovação, não política já vigente. Alternativa conservadora: manter Fable medium/high nessas faixas e medir antes de trocar a família. Não há benchmark local que prove economia líquida ou qualidade equivalente de Sonnet/Opus neste projeto. A skill cost-aware orientou separação por complexidade e medição; não adotamos seus retries genéricos nem preços exemplificativos.

## 3. Campanhas: classe de coordenação, não um modelo único

- C1 local: um resultado independente; tarefas mantêm T0..T3; um dono.
- C2 encadeada: várias tarefas/dependências; plano delimitado, marcos e retomada persistentes; não elevar todas as tarefas ao maior modelo.
- C3 sensível: risco sistêmico, integração incerta ou ação irreversível; supervisão assistida e checkpoints humanos. Exemplo proposto: NIGHT-42 permanece C3 e bloqueada.
- Janela é eixo separado (assistida/noturna), não sinônimo de tamanho/custo. Campanha longa pode conter T1; campanha curta pode ser T3. Noite exige runtime validado, recursos/quota, aceite determinístico, dependências cumpridas e opt-in; nunca só um rótulo.
- Futuro estado mínimo: task_level,campaign_class,role,requested_model,requested_effort,selection_reason,observed_model,usage,gate. Reutilizar active-task/template existentes; não criar outro banco/roteador.
- Registrar input/cache_create/cache_read/output, tempo e resultado por chamada. Assinatura não gera desconto na mensalidade ao reduzir tokens; benefício esperado é quota/latência. Custo de lista não é fatura. Sem fallback por quota/recusa, sem repetir revisão consumida.

## 4. Diagnóstico noturno #42 — delimitado, ainda não executado

Evidência existente: smoke02c8fa8d,uma tentativa,unexpected_model/unrecognized,3eventos,stdout1867bytes,kill confirmado,sem edição. Código night_model_control.py normaliza qualquer ID fora de KNOWN_IDS para unrecognized antes de registrar. Logo, o relatório perdeu o ID original; não permite concluir OAuth expirado, fallback ou versão nova. Não adicionar wildcard/ID desconhecido à allowlist para fazer o teste passar.

Ambiente encontrado: sbx0.43.0; `docker sandbox` foi removido. `sbx ls --json` localizou night-fable-20260919 (a57d767b-4ac8-4d0d-8718-e7a872b3cd4c) e night-pilot-20260919,ambas paradas. Não recriadas/iniciadas nesta consulta. sbx exec inicia uma sandbox parada; registrar essa ação antes de executar. [Referência sbx exec](https://docs.docker.com/reference/cli/sbx/exec/).

Plano para autorização específica:

1. Reabrir somente night-fable-20260919 existente; conferir binário Linux2.1.278, versão/hash e condições do provider_env sem imprimir credenciais. Não migrar runtime para Windows nem alterar autenticação.
2. Uma chamada diagnóstica NOVA, fora do loop de goals: mesmo alias fable/effort high/safe-mode,tools vazias,MCP desligado,permission-mode dontAsk,switchModelsOnFlag=false,max-turns1,no-session-persistence. Prompt sintético: responder DIAGNOSTIC_OK,sem arquivos/corpus. Nenhum prompt recusado é reenviado.
3. Capturar apenas metadados sanitizados necessários antes da normalização: tipo/subtipo,ID de modelo delimitado/validado,flags de erro/fallback,uso e término. Não salvar stdout completo,credenciais,código ou texto livre do provider. Manter guard: ID inesperado/recusa/fallback encerra imediatamente; nenhuma chamada após isso.
4. Deadline120s,orçamento1tentativa,grace de kill10s e teto externo150s; isolamento e confirmação de árvore de processos obrigatórios. Se não puder garantir contenção no ambiente encontrado, não iniciar a inferência. Sem tools do modelo,sem alterações de produto,sem suspensão,sem retry/reset de #42. Instrumentação mínima preparada por Fable sob escopo aprovado; nenhuma segunda revisão Astra automática.
5. Explicar causa com evento/metadado, ou declarar indeterminada. Correção do runner e novo E2E são etapas posteriores; diagnóstico não conclui goal nem libera uma noite.

O plano não foi executado: zero chamadas de inferência neste inventário. Consulta de modelos/menus não substitui diagnóstico live. Contador de review #42 continua1 consumido, Gate2 do diff operacional pendente.
