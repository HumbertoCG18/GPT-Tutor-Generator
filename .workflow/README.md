# Workflow compartilhado

Ler [workflow.md](workflow.md) antes de executar ou continuar uma tarefa. Essa política
substitui as regras antigas que exigiam pedido explícito para toda chamada Astra ou
fixavam Claude como único escritor. Restrições explícitas do usuário prevalecem.

Snapshot da fonte agent-workflow-lab, aprovado em 16/09/2026; hashes em manifest.json.
Atualização manual revisada, mesma cópia nas branches. Não editar snapshots isoladamente.
Os contratos de agents/ são inline; não pressupõem um subagente nativo instalado.

Copiar task-state.template.md para .workflow-local/active-task.md ao iniciar trabalho
multietapa. A pasta local é ignorada pelo Git; não transportar tarefa ativa entre branches
sem conferir HEAD/diff. O coordenador registra estado antes de delegar e em cada etapa.

Configurações pessoais e Context7 são locais à máquina e já valem entre branches.
Credenciais, backups e permissões pessoais não fazem parte deste pacote. Hooks existentes
não lançam LLM; a escalada autorizada é executada pelo agente ativo. Não há bloqueio técnico
de quota/contagem nem execução quando a sessão está encerrada.

Aceites ainda abertos: [PENDING.md](PENDING.md).
