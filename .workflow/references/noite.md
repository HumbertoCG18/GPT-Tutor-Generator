# Agente noturno

Ler ao coordenar trabalho noturno; não carregar preventivamente. Registro e estados: campaigns.md.

1. Tomar só tarefas `livre` de `campanhas.py listar --noite`. Nada livre: registrar no diário e parar.
   Aberto pelo agendador do Alethe: a tarefa já vem no prompt; trabalhar só nela, sem escolher outra.
2. Uma tarefa por vez, com o seu `.workflow/local/active-task.md` (`campanha`, `tarefa`, classificação).
3. Delegar com `task: <ID>` igual a `tarefa`; contratos de delegação, revisão e timeout valem (delegation.md, review.md).
4. Registrar cada resultado: `campanhas.py noite <ID> --resultado ok|aguarda-voce|falhou|parou --resumo "…" [--evidencia "…"]`.
   Execução longa grava `.workflow/local/execucao.json` com `i`, `N`, `inicio`, `teto` e `pid`, como o `replay.py`.
   Selo `✕ parado` na tarefa ativa: o processo morreu antes do teto; registrar `parou`, sem esperar o teto (#142).
5. Nunca concluir: o Gate 2 é do usuário. Não preencher `gate_2` nem rodar `estado … concluída`. Trabalho pronto fica `status: concluido` com `gate_2: pendente` (o hook deixa a tarefa `bloqueada`, aguardando o Gate 2) e entra no diário como `aguarda-voce`.
6. Achado fora da tarefa: `campanhas.py achado "título" --tipo ideia|bug|risco|divida --origem <ID>`, sem investigar; no máximo 3 por tarefa.

## Restrições (SEG-02, #53)

Valem até a correção de cada lacuna; levantar uma restrição exige decisão registrada.

1. Só worker Claude, e só com `PreToolUse` presente no settings: o Alethe parte o worker mesmo sem ele.
2. Codex como worker não roda: o Alethe liga o thread com `features.hooks=false`, então os guardas não valem.
3. Executor Codex do modo economia não roda: o guarda só confere o prefixo `codex exec` e aceita comando encadeado.
4. AGY não roda: a config do usuário tem sandbox de terminal desligado, acesso fora do workspace liberado e nenhum hook.
5. Skills só de origem registrada (`deployed-skills.json` ou plugin com versão e commit); MCP ativo sem versão fixa é erro do verify.py.
