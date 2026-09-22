# Alethe como interface — correções locais

Refs #44. Gate1 aprovado pelo usuário; Gate2 pendente,sem commit. Configuração assistida T2,coordenador Codex; nenhum worker/revisor/inferência iniciado. Estado do motor e contadores existentes preservados.

## Aplicado e verificado

- Ponte MCP ativa gerada pelo Alethe: parâmetro padrão Invoke-WebRequest:UseBasicParsing=true. Antes,teste não interativo sem JSON-RPC; depois initialize0.235s e tools/list0.234s,9ferramentas,exit0/stderr0. Não aumentado startup_timeout_sec. Chamadas somente de protocolo,não execução de ferramentas.
- Dois guards PreToolUse migrados integralmente de .codex/hooks.json para .codex/config.toml,fora dos marcadores gerenciados pelo Alethe. JSON redundante removido após backup. Comparação por parser confirmou igualdade de todas as definições,SubagentStart/Stop preservados e restante do TOML inalterado. Não inferir hooks executados pela validade do arquivo.
- Codex Companion1.0.6: somente timeout SessionEnd5→3; comparação JSON confirmou ausência de outras mudanças. Não desabilitado nem removido.
- Ponte de governança na fonte agent-workflow-lab/references/tooling.md e snapshot idêntico,hash atualizado no manifesto. Sem segunda fila,memória,roteador ou servidor. Core do workflow não copiado para objetivo do planner.

## Uso

No Alethe,abrir GPT-Tutor-Generator no modo Terminal com Claude Code ou Codex; instruções do projeto continuam sendo a entrada. Para planner futuro,objetivo curto: "Leia .workflow/README.md; consulte a fila-campanhas de docs/reports/pendencias.md e o estado da tarefa escolhida. Siga seus Gates; não lance workers até validar esta integração."

Modo Orquestração não homologado: v1.7.0 não expõe modelo/effort por delegate e launcher Claude usa bypassPermissions. Não promover prompt a controle técnico. Preservar AGY/memória/agente noturno. Um dispatch por task_id; eventos nativos apenas mostram atividade. Não usar botões de commit/merge como aprovação implícita.

## Limites e próximos checks

Correção MCP é LOCAL à ponte ativa em Temp: Alethe1.7.0 pode recriá-la ao abrir outra sessão. Correção definitiva pertence ao gerador src-tauri/src/agent_events.rs (Invoke-WebRequest sem UseBasicParsing); não alterado binário,não compilado fork,não instalado daemon. Nova sessão exige reconferir ponte; não declarar persistência entre sessões validada. Edição no cache Companion também pode ser substituída por atualização; compatibilidade deve chegar à fonte do plugin.

Carregamento em sessão nova e confiança /hooks ainda pendentes; a sessão atual não foi reiniciada. Migração altera origem/hash dos guards: conferir/trust em /hooks antes de contar com execução. Nenhum teste E2E de workers,nenhum ganho de tokens/quota medido.

Backup local privado: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/alethe-interface-20260921/. Inclui project-config.before.toml,project-hooks.before.json,companion-hooks.before.json,bridge.before.ps1. Ponte contém autenticação local: não publicar/copiar para brief. Restaurar seletivamente após conferir drift; nunca sobrescrever configuração nova com backup antigo automaticamente.

OpenAI Docs orientou consolidar uma representação de hooks por camada e respeitar máximo3s em SessionEnd. Diagnóstico diferencial isolou o parser PowerShell; não aumentou timeout para mascarar falha.

## Identidade e continuidade: nomenclatura nativa do Alethe

Conferência documental solicitada pelo usuário em 21/09, vinculada a #44. Fonte: checkout local `agent-workflow-lab/private/alethe-upstream-usebasicparsing-20260921`, HEAD `dd87c97639adf712929e55f62e625921cf7b7014`. Evidência de código, não teste da instalação atual. Os registros anteriores descrevem a sessão de configuração; não são inventário dos workers atuais. Claude permanece coordenando o motor; nenhum job foi criado, retomado ou cancelado nesta conferência.

| Nome no Alethe | Campo nativo | Uso no workflow existente |
| --- | --- | --- |
| Planner | `id`, `label`, `agent`; vínculo do job: `plannerId` | Terminal/agente que coordena a execução. Referenciar seu ID no estado existente; não criar cadastro paralelo de coordenadores. |
| Run | `runId`, `runLabel` | Uma rodada de delegação; uma chamada de `alethe_delegate` gera uma Run. Usar `label` para identificar campanha/tarefa do tracker. Campanha pode abranger várias Runs. |
| Worker / Job | `id` no resultado, `jobId` nos comandos; `agent`, `spec`, `status` | Unidade executada pelo Alethe. Associar ao `task_id` existente pelo brief e pelo registro do coordenador. Não substituir o ID da tarefa pelo ID do Job. |
| Thread | `threadId` | Conversa do worker usada na continuidade. Não confundir com Planner, Run ou tarefa do tracker. |
| Diretório / Worktree | `cwd`, `worktree` | Reutilizar os caminhos retornados pelo Alethe. Conferir branch/HEAD no Git; esses valores não constam como campos próprios do Job consultado. |

Fontes no checkout citado: `src/lib/tauri/orchestrator.ts` (tipos e comandos), `src/lib/orchestratorRuns.ts` (agrupamento das Runs), `src-tauri/src/orchestrator_core.rs` (`Planner`, `Job::snapshot`, `Job::record`, `Job::from_record`, `persist` e `tools`).

### Uso sem nova estrutura

- Antes de delegar, consultar `alethe_status` e o estado existente da tarefa para localizar Job já associado; não emitir outro `alethe_delegate` para trabalho em andamento. Essa conferência é disciplina do Planner, não deduplicação automática por `task_id` comprovada.
- No `label` da Run, incluir os IDs existentes, por exemplo `CRU-03 | <task_id> | replay de unidade`. No texto de `tasks`, referenciar tracker/estado, escopo aprovado, cwd/branch/HEAD e aceite. São valores dos campos nativos, não uma nova fila.
- Após dispatch autorizado, o coordenador registra `plannerId`, `runId`, `jobId` e `threadId` nos campos de chamada/evidência do estado existente. Os IDs devem vir da resposta do Alethe; não fabricar valores nem escrever diretamente no armazenamento interno.
- `alethe_status` consulta; `alethe_check` recolhe resultados; `alethe_steer` orienta o turno em andamento; `alethe_send` envia novo trabalho na Thread existente e pode iniciar execução. `alethe_delegate` cria novos workers e executa. Retomada exige a autorização da tarefa, não apenas a existência de `threadId`.
- O armazenamento nativo preserva Jobs, Planners, IDs, caminhos, resumo e tokens registrados. Ao restaurar, Jobs `running`/`queued` viram `interrupted`; isso não equivale a retomada automática. A gravação ocorre em transições, não em todo evento de tokens, e `quota` não é persistida nesse registro.

### Limites que continuam no workflow

Gates, contadores de revisão, tentativas, dependências entre tarefas e identificação estável da campanha continuam no tracker/estado existentes. `done` não significa Gate 2 aprovado; `blocked`/`pendingApproval` do Alethe não substituem os Gates do projeto. O scheduler tem uma entidade `Task` e lê `.planning/task.md` (`src-tauri/src/scheduler.rs`); não importar a fila-campanhas para ali nem tratar Task e Job como sinônimos sem integração própria.

Resultado desta etapa: mapeamento de nomes e procedimento de vínculo, sem código novo, sem renomear arquivos/campos do workflow, sem mudar perfis, quota, scheduler ou estado do motor. Retomada real e deduplicação técnica permanecem não validadas por esta conferência.

## Plano de consolidação solicitado em 21/09, 20h — Gate 1 pendente

Pedido: Alethe como Orquestração principal, corrigir sobreposições sem remover funcionalidades e recuperar MCP Codex. Integração T3/C3, confiança média: mecanismos nativos identificados, equivalência de controles ainda não demonstrada. Refs #44 e #42; MCP upstream #199 já possui patch e revisão consumida. Este plano não altera o estado do motor, os seus Gates ou os seus workers.

1. Consolidar o caminho principal na fonte canônica do laboratório: `references/tooling.md`, `references/delegation.md` e `references/resume.md`. Em sessão Alethe, Planner usa seus Jobs/Runs/Threads; launchers diretos ficam preservados para uso externo explicitamente escolhido, sem dispatch simultâneo ou fallback automático. Distribuir somente os snapshots correspondentes em `.workflow/references/` e atualizar o manifesto após conferir drift. Não modificar roteamento de modelos nem renomear os IDs do tracker.
2. Preservar contratos existentes de Gates, revisão, tentativas, modelo observado, corpus/arquivos permitidos e aplicação/verificação de resultados. Capacidade nativa sem equivalência comprovada mantém a tarefa bloqueada; `askForApproval` não prova confinamento de leitura. Não criar outra fila, registro de Jobs, painel, launcher ou contador básico de tokens. Orçamento por campanha segue lacuna separada, não funcionalidade já entregue.
3. Validar a integração em worktree descartável com uma tarefa assistida delimitada: um dispatch, IDs registrados, resultado conferido, encerramento por timeout/cancelamento confirmado e continuidade sem Job duplicado. O teste não toca o motor/corpus e precisa de limite explícito antes de lançar; autorização deste plano não renova tentativas/revisões antigas. Implementação nova pelo executor T3 `claude-fable-5-1/high`; revisão de eventual novo diff relevante por Astra/high, uma tentativa registrada antes da chamada. Se MCP/modelo/permissões não atenderem ao contrato, não lançar por outro caminho.
4. Só depois mapear #42 para os mecanismos validados. Manter o runtime noturno, testes e controles atuais enquanto a equivalência não passar; nenhuma exclusão ou liberação noturna nesta fatia. Qualquer adaptação executável em `agent-workflow-lab-night-42/pilots/night-agent/` exige allowlist de arquivos e Gate 1 próprio após o teste assistido. Fonte e worktree do laboratório ficam fora da raiz gravável desta sessão: escrita dependerá da permissão do ambiente.
5. MCP: reaproveitar o patch existente no gerador `src-tauri/src/agent_events.rs`, sem repetir implementação/revisão upstream. Correção durável exige build/release validado e instalação autorizada; não instalar fork nem criar monitor que reescreva Temp. Aceite durável: duas sessões novas geram ponte corrigida e expõem as nove ferramentas, sem workers. Gate 2/commit/merge/deploy permanecem separados.

### Diagnóstico e mitigação do MCP nesta retomada

Configuração atual apontava para `alethe-codex-mcp-bridge-9123-_fxUT9oDHlUZEDe2n4RB2.ps1`, novamente sem `UseBasicParsing`. Sob o pedido de correção, acrescentado apenas o parâmetro padrão, com backup byte-idêntico em Temp (`.before-basicparsing-20260921-203040-636713.bak`); corpo original preservado. Backup contém autenticação e não deve ser publicado.

O teste antes e depois retornou zero respostas MCP, mesmo com exit 0 e stderr vazio. Repetição read-only fora da sandbox também sem respostas. Diagnóstico HTTP direto, usando os mesmos headers em memória sem exibir segredos: `ConnectionRefusedError`, Windows `10061`. Consulta não encontrou listener na porta 9123 nem processo com nome Alethe. Portanto: mitigação do script aplicada; MCP NÃO recuperado nesta retomada. É necessário abrir o Alethe e conferir a ponte que ele gerar antes de repetir initialize/tools/list. Nenhuma tools/call, worker, restart ou alteração do binário foi executada.

### Consolidação das referências concluída após aprovação do usuário

Gate 1 aprovado explicitamente para as três referências e seus snapshots, deixando Alethe como principal. Alteradas na fonte canônica `agent-workflow-lab/references/{tooling,delegation,resume}.md`; distribuídas somente as três cópias em `.workflow/references/`, com atualização das respectivas entradas de `.workflow/manifest.json`. Antes da escrita: 3/3 cópias byte-idênticas e hashes anteriores válidos. Depois: 3/3 cópias byte-idênticas, manifesto 23/23 válido e diff-check do manifesto limpo. Launchers, runtime noturno, modelos, perfis, skills globais e estado do motor não foram alterados; nenhum worker lançado ou cancelado. Gate 2 permanece pendente, sem commit.

Verificação `python verify.py` no laboratório: 81 arquivos de skills gerenciados; exit 1 por um único erro, `Codex Companion reenabled inside Codex`, divergência já conhecida e fora deste escopo. Não desabilitado o plugin para tornar a verificação verde. Backup das três referências e do manifesto anterior: diretório privado Temp `alethe-workflow-consolidation-gkvbibra`.

Diagnóstico da instalação: `AppData/Local/Alethe/alethe.exe` existe e informa ProductVersion/FileVersion 1.7.0; executável MCP também presente. Consulta Win32_Process fora da sandbox não retornou `alethe.exe`; nenhuma escuta na porta 9123. `last_session.json` registra versão 1.7.0 e `clean_exit: false`: indica última sessão não registrada como encerramento limpo, sem determinar causa. Evidência não demonstra má instalação. Bloqueios identificados: ponte gerada sem UseBasicParsing (defeito já reproduzido no template upstream) e listener ausente com aplicativo parado. Não reinstalado nem iniciado o aplicativo; recuperação E2E do MCP ainda depende de abrir Alethe e testar a ponte vigente. Integridade integral do pacote não foi certificada por esta inspeção.
