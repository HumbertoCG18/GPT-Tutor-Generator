# Ferramentas locais e portabilidade

Fonte das skills pessoais compartilhadas: `C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/skills`.
Claude, Codex e AGY têm destinos próprios; validar com `verify.py` nesse laboratório.
Alethe cuida das sessões. Não reimportar bundles inteiros nem deixar dois gestores
reescreverem os mesmos destinos. Skillfile permanece apenas piloto, sem sincronização automática.

Graphify é principal. CBM é fallback nas três CLIs, com auto_index=false e
 auto_watch=false. Antes do primeiro fallback da sessão, ou após mudar fontes,
executar index_repository explicitamente. Não sincronizar os bancos entre si.
No GPT Tutor, seguir também `.mex/patterns/codegraph-fallback.md`.
Graphify roda pela CLI local nas três (graphify query/explain/path no projeto atual);
o MCP saiu porque servia um graph.json fixo do GPT Tutor em qualquer projeto.

## MCPs por CLI (paridade medida em 30/09/2026)

Iguais nas três: context7, claude-mem (mcp-search) e codebase-memory-mcp (fallback).
GitHub e Graphify pelas CLIs gh e graphify. Uso real medido (tool_use) antes de remover:
github 1/0/0 chamadas (Claude/Codex/AGY) contra gh 491/252; graphify MCP 2/0/~1 contra
CLI 18/82; chrome-devtools 0/0/0; perssua 0/0/0. Removidos: github (as três),
graphify e chrome-devtools-mcp (Claude, AGY), perssua (Claude; segue desligado no
Codex e no AGY). O chrome-devtools continua via plugin ECC no Claude e no Codex.
Codex mantém as ferramentas do app (cua_repl, node_repl, codex_app).
Readicionar: claude mcp add perssua -s user -e PERSSUA_MCP_SOURCE=... -- cmd.exe /d /s
/c npx -y @perssua/mcp; graphify MCP com graph.json do projeto como argumento.
Backups: ~/.claude.json, ~/.codex/config.toml e ~/.gemini/config/mcp_config.json com
sufixo .bak-paridade-20260930-011932 (e .bak-github-mcp-20260930-004949).

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
uma chamada de subagente. Ausência do papel ECC não é gatilho para escalar ao revisor.

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

## Build do Alethe (pastas de saída do cargo)

Teste Rust (`cargo test`, debug): `CARGO_TARGET_DIR=D:\cargo-target\alethe-test`, cache único
compartilhado por sessões, worktrees e subagentes. Instalador (`tauri build`, release):
`D:\cargo-target\alethe`. Não criar pasta de saída por tarefa (cada uma custa 6 GB). `cargo fmt`
no crate inteiro é proibido; usar `rustfmt --check --edition 2021` só nos arquivos tocados.
Briefs de subagente que rodam cargo citam essas pastas.
Atualizar o Alethe Dev sem desinstalar: `bin/alethe-dev/alethe-dev.ps1 update` (build de origin/dev
+ instalação por cima com `/P /UPDATE /R`); `build` e `install` separados. Espera o usuário sair
pelo app; nunca fecha o Alethe Dev. Antes de dizer que o Alethe Dev está aberto ou fechado, ou de
pedir ao usuário que o feche, conferir o processo (`alethe.exe` com caminho em `\Alethe Dev\`); não
supor pelo histórico da conversa.
Antes de merge com mudança em Rust: `cargo check --bins --lib` (o `orchestrator_core.rs` também
entra no binário `alethe-orchestrator-mcp`; `cargo test --lib` não compila os binários, #58→#59).
