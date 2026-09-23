# Workflow compartilhado

Ler o núcleo canônico: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/workflow.md.
Se indisponível, usar [workflow.md](workflow.md) e suas referências locais; registrar fallback.
Ler uma vez por sessão e referências somente na ação correspondente. Não carregar ambos.

Papéis: Claude Code = terminal/execução; Codex = orquestração/revisão; AGY = auditoria/pesquisa/achados.
Uma tarefa, um coordenador. Configuração e execução devem ser verificadas separadamente.

Estado por worktree: .workflow/local/active-task.md (legado: .workflow-local/), usando [template](task-state.template.md).
[HANDOFF.md](HANDOFF.md) aponta continuidade desta frente; não carregar handoff do motor para configurar CLIs.
Não transportar estado entre branches sem conferir HEAD/diff nem reiniciar contadores.
Snapshots são distribuição manual revisada; hashes em [manifest.json](manifest.json).
Novas regras nascem na fonte canônica, depois são distribuídas.
