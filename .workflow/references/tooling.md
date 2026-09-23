# Ferramentas locais e portabilidade

Fonte das skills pessoais compartilhadas: `C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/skills`.
Claude, Codex e AGY têm destinos próprios; validar com `verify.py` nesse laboratório.
Alethe cuida das sessões. Não reimportar bundles inteiros nem deixar dois gestores
reescreverem os mesmos destinos. Skillfile permanece apenas piloto, sem sincronização automática.

Graphify é principal. CBM é fallback nas três CLIs, com auto_index=false e
 auto_watch=false. Antes do primeiro fallback da sessão, ou após mudar fontes,
executar index_repository explicitamente. Não sincronizar os bancos entre si.
No GPT Tutor, seguir também `.mex/patterns/codegraph-fallback.md`.
Antes de usar Graphify MCP em outro projeto, conferir se o graph.json configurado
pertence ao projeto atual; se não, usar a CLI local. Não consultar o grafo do GPT
Tutor como se representasse outro repositório.

RTK 0.49.0 está em `C:/Users/Humberto/.local/bin/rtk.exe`. Uso aprovado inicialmente:
`rtk pytest <argumentos>` para leitura humana da saída. Se o pytest do projeto não
estiver no PATH, preservar o ambiente nativo e executar o comando original.
Recuperar detalhes omitidos com `rtk recall <hash> --full` quando houver indicação.
Para comparação exata, JSON ou pipelines, usar saída original. Não aplicar RTK a
rg/grep, git ou todos os comandos via hook sem medição específica. Não confundir
redução de bytes com economia comprovada de quota.

Aprendizagem: ao fechar trabalho relevante, usar ECC para propor correções com
 evidência; não editar skills globais automaticamente. Tracker/handoff preservam
continuidade quando claude-mem não grava. Não reiniciar o worker por erro de quota.

Portabilidade ECC: dentro do Alethe, seguir o caminho de Orquestração abaixo.
Fora dele, usar subagente nativo quando disponível. Se a CLI não expuser
o papel, executar a etapa inline seguindo a definição em
`C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/agents/`
(tdd-guide.md ou python-reviewer.md), preservando Gates 1/2. Nunca inventar
uma chamada de subagente. Ausência do papel ECC não é gatilho para escalar a Astra.

## Alethe como Orquestração principal

Em sessões Alethe, a Orquestração é o caminho principal para executar trabalho
aprovado. Usar os nomes nativos: Planner coordena; Run agrupa uma rodada de
delegação; Worker/Job executa; Thread preserva a conversa; cwd/Worktree identifica
o local. Uma campanha pode ter várias Runs; Task do scheduler não é sinônimo de Job.

Reutilizar criação, fila de Jobs, concorrência, timeout, cancelamento, persistência
e telemetria nativos quando atenderem ao contrato. Não criar outro launcher,
registro operacional ou painel. Tracker/estado existentes continuam como fonte de
campanhas, tarefas, Gates, tentativas e revisões; referenciar seus IDs no label/spec.
O scheduler nativo não recebe outra cópia da fila por esta política.

Um Planner e um único caminho de dispatch por tarefa. Não executar o mesmo trabalho
por alethe_delegate e por CLI/subagente externo. Launchers e rotinas existentes são
preservados para uso fora do Alethe ou escolha explícita; indisponibilidade de MCP,
quota ou capacidade não autoriza fallback automático. AGY mantém seu contrato;
suporte nativo não demonstrado deve ser declarado, sem fabricar integração.

Alethe executa; o workflow autoriza e aceita resultados. Eventos SubagentStart/Stop,
status done e botões de aplicar/merge não substituem Gates. Conferir modelo/effort
observado, permissões, arquivos permitidos e retomada antes de depender deles;
askForApproval não comprova confinamento de leitura e prompt não impõe controle.
Quota/fitness são telemetria, não teto por campanha. Falta de controle exigido
bloqueia a ação; não enfraquecer o contrato para conseguir lançar.

Memória, revisão e noite mantêm contratos e contadores próprios. Não remover o
runtime noturno nem liberar scheduler/noite antes da equivalência validada e dos
preflights de #42 no projeto correspondente. Não iniciar segundo servidor standalone
para duplicar o painel. Operação: delegation.md; continuidade: resume.md.
