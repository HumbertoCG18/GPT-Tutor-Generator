# Alethe: Orquestração e build

Movido de [tooling.md](tooling.md) (PODA-18, #447). Ler em sessão Alethe, ao delegar pela Orquestração, ou ao rodar cargo, `tauri build` ou atualizar o Alethe Dev.

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
preservados para uso fora do Alethe ou escolha explícita. Quota/recusa nunca autorizam
fallback fora da reserva de routing.md › Camadas; falta do transporte de revisão admite só o caminho já definido em review.md,
antes da primeira chamada, preservando contador, escopo e permissões. AGY mantém seu contrato;
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
Briefs de subagente que rodam cargo citam essas pastas; o coordenador também as usa (cargo sem
`CARGO_TARGET_DIR` numa worktree cria um `src-tauri\target` local).
Verificação enxuta (aprovada pelo dono em 11/10/2026, medida: tarefas de 12 a 64 min e 93k a 414k
tokens por subagente): durante a iteração, só os testes focados; suíte completa uma vez no fim;
repetir a suíte (3×) só em T3 ou para investigar instabilidade. Uma tarefa com cargo por vez e
rebuild do Alethe Dev fora dessa janela: competem pela CPU, e a carga já gerou falso vermelho
(ACH-0022 no Alethe).
Atualizar o Alethe Dev sem desinstalar: `bin/alethe-dev/alethe-dev.ps1 update -ExpectedCommit <SHA completo>`.
O SHA é o commit validado/autorizado, não uma branch móvel. `build` recusa worktree suja ou de
outro repositório, preserva WIP e grava `D:\cargo-target\alethe\alethe-build.json` com commit,
caminho e SHA256. `verify -ExpectedCommit <SHA>` confere sem executar; `install` exige esse
mesmo SHA e manifesto (`-Manifest <caminho>` opcional), nunca escolhe o exe mais recente.
Os comandos que compartilham a saída usam uma trava; ela não substitui autorização.
Instala por cima com `/P /UPDATE` e reabre pelo Explorer; `build` e `install` separados.
Instalação requer autorização própria do dono. Espera o usuário sair
pelo app; nunca fecha o Alethe Dev. Antes de dizer que o Alethe Dev está aberto ou fechado, ou de
pedir ao usuário que o feche, conferir o processo (`alethe.exe` com caminho em `\Alethe Dev\`); não
supor pelo histórico da conversa.
Antes de merge com mudança em Rust: `cargo check --bins --lib` (o `orchestrator_core.rs` também
entra no binário `alethe-orchestrator-mcp`; `cargo test --lib` não compila os binários, #58→#59).
