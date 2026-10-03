# Agente noturno

Ler ao coordenar trabalho noturno; não carregar preventivamente. Registro e estados: campaigns.md.

1. Tomar só tarefas `livre` de `campanhas.py listar --noite`. Nada livre: registrar no diário e parar.
   Aberto pelo agendador do Alethe: a tarefa já vem no prompt; trabalhar só nela, sem escolher outra.
2. Uma tarefa por vez, com o seu `.workflow/local/active-task.md` (`campanha`, `tarefa`, classificação).
3. Delegar com `task: <ID>` igual a `tarefa`; contratos de delegação, revisão e timeout valem (delegation.md, review.md).
4. Registrar cada resultado: `campanhas.py noite <ID> --resultado ok|aguarda-voce|falhou|parou --resumo "…" [--evidencia "…"]`.
5. Nunca concluir: o Gate 2 é do usuário. Não preencher `gate_2` nem rodar `estado … concluída`. Trabalho pronto fica `status: concluido` com `gate_2: pendente` (o hook deixa a tarefa `bloqueada`, aguardando o Gate 2) e entra no diário como `aguarda-voce`.
6. Achado fora da tarefa: `campanhas.py achado "título" --tipo ideia|bug|risco|divida --origem <ID>`, sem investigar; no máximo 3 por tarefa.
