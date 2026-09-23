# Retomada e limites

Estado local por worktree em .workflow/local/active-task.md, excluído do Git (/.workflow/local/ no .gitignore). Worktree ainda não migrada: ler .workflow-local/ (legado) e mover ao retomar, conferindo hashes, sem copiar estado entre worktrees; usar o template distribuído. Tracker/handoff versionado guarda apenas resultado e pendências sem dados sensíveis. Em projeto sem este pacote, usar o handoff existente com os mesmos campos.

Ao receber continuar, ler estado + tracker/handoff e conferir branch, HEAD, diff, testes e situação da chamada anterior. Se status=delegando, verificar a sessão registrada antes de decidir que foi interrompida; não lançar segunda chamada. Retomar a próxima etapa pendente, sem refazer trabalho concluído, reabrir tarefa encerrada ou ultrapassar Gate 1/2. Estado ausente, contraditório ou múltiplas tarefas plausíveis exige esclarecer a ambiguidade. Continuar não é autorização de commit nem de novo escopo.

Quando houver quota esgotada, salvar estado e aguardar orientação; não trocar de provedor nem repetir chamadas recusadas automaticamente. Data e saldo de reset não são presumidos. AGY e Context7 entram somente quando pesquisa for necessária.

Automação conduzida pelo agente enquanto a sessão está ativa, com autorização persistente nas instruções. Esta política não instala daemon, monitor de reset ou scheduler. O scheduler
nativo do Alethe não libera automaticamente execução noturna. Hooks existentes mantêm verificações mecânicas; não disparam LLM. O limite de uma revisão automática depende do coordenador seguir o estado, não de bloqueio técnico no servidor. Gates ECC permanecem aplicáveis; autorização explícita de commit dada pelo usuário no escopo prevalece, depois de preparar e verificar o diff.

## Continuidade no Alethe

Consultar o Planner e seus Jobs/Runs com alethe_status; cruzar os IDs com o estado
existente, cwd/Worktree e branch/HEAD do Git. O armazenamento nativo preserva a
identidade operacional; tracker/estado preservam aceite, Gates, tentativas e revisões.
Não criar outro cadastro de Jobs nem copiar a fila para o scheduler.

Na implementação consultada, restaurar o Alethe converte running/queued em
interrupted; Thread persistida não prova processo ativo ou retomada autorizada.
Confirmar o estado real antes de alethe_send; não usar alethe_delegate para recriar
uma tarefa interrompida sem decisão explícita. done não é aprovação de integração;
pendingApproval/blocked não é Gate 1 ou Gate 2. Preservar contadores entre Threads,
Runs e troca explícita de Planner, com apenas um coordenador por tarefa.

Tokens registrados podem ser anteriores ao último evento; quota não é persistida
no registro de Job consultado. Reconsultar quota/reset antes de retomar e preservar
o consumo já atribuído à campanha. Sem telemetria exigida, não presumir saldo nem
liberar novas chamadas. Continuar após corte de orçamento exige autorização própria.
