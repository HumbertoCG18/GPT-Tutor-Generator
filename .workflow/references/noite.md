# Agente noturno

Ler ao coordenar trabalho noturno; não carregar preventivamente. Registro e estados: campaigns.md.

1. Tomar só tarefas `livre` de `campanhas.py listar --noite`. Nada livre: dizer no chat e parar.
   Aberto pelo agendador do Alethe: a tarefa já vem no prompt; trabalhar só nela, sem escolher outra.
2. Uma tarefa por vez, com o seu `.workflow/local/active-task.md` (`campanha`, `tarefa`, classificação).
3. Delegar com `task: <ID>` igual a `tarefa`; contratos de delegação, revisão e timeout valem (delegation.md, review.md).
4. Registrar cada resultado: `campanhas.py noite <ID> --resultado ok|aguarda-voce|falhou|parou --resumo "…" [--evidencia "…"]`.
   Abrir o `--resumo` com o estado de retomada (`retomada:`, `do zero:`, `Gate 2:`, `decisão:`, `falhou:`), tabela em resume.md.
   Execução longa grava `.workflow/local/execucao.json` com `i`, `N`, `inicio`, `teto` e `pid`, como o `replay.py`.
   Selo `✕ parado` na tarefa ativa: o processo morreu antes do teto; registrar `parou`, sem esperar o teto (#142).
5. Nunca concluir: o Gate 2 é do usuário. Não marcar `gate_2: aprovado` nem rodar `estado … concluída`. Trabalho pronto fica `status: concluido` com `gate_2: pendente` (o hook deixa a tarefa `bloqueada`, aguardando o Gate 2), recebe no registro `campanhas.py estado <ID> bloqueada --gate2 pendente` e entra no diário como `aguarda-voce` com resumo `Gate 2:`; parada numa decisão de plano também é `aguarda-voce`, com `decisão:`.
6. Toda espera por subagente tem prazo (#396): Monitor no mtime de `subagents/agent-<id>.jsonl` da sessão (o `tasks/<id>.output` fica com 0 bytes até o fim), avisando com 4 min sem escrita e teto de 30 min. Aviso de "interim" ou "waiting on its own background work" sem processo em segundo plano: ler a transcrição e a worktree, sem esperar mais. Agente retomado por SendMessage não entrega um 2º relatório: o resultado está na transcrição.
7. Achado fora da tarefa: `campanhas.py achado "título" --tipo ideia|bug|risco|divida --origem <ID>`, sem investigar; no máximo 3 por tarefa.

## Restrições (SEG-02, #53)

Valem até a correção de cada lacuna; levantar uma restrição exige decisão registrada.

1. Só worker Claude, e só com `PreToolUse` presente no settings: o Alethe parte o worker mesmo sem ele.
2. Codex como worker não roda: o Alethe liga o thread com `features.hooks=false`, então os guardas não valem.
3. Executor Codex do modo economia não roda: o guarda só confere o prefixo `codex exec` e aceita comando encadeado.
4. AGY não roda: a config do usuário não tem nenhum hook e executa comandos em modo EAGER. O sandbox de terminal está ligado e o acesso fora do workspace está negado desde 24/10 (#359).
5. Skills só de origem registrada (`deployed-skills.json` ou plugin com versão e commit); MCP ativo sem versão fixa é erro do verify.py.

## Checklist antes de sair (#313)

Seis travas da noite (~7,3 h) vieram de `ask` sem ninguém acordado.

- Heredoc com delimitador entre aspas lido por `cat`, `tee` ou `python -` já não pede por causa de `eval`/`exec` no corpo; evitar `sh <<`, `bash <<` e `eval`, que ainda pedem.
- Chamada de shell montada no Bash (`powershell -Command`/`-File`, `bash -c`, `eval`) sempre pergunta no git-lock, e à noite vira bloqueio: rodar PowerShell pela ferramenta PowerShell, sem `powershell` dentro do Bash (#396).
- Diário, relatório e arquivo novo com Write/Edit, não com heredoc ou `printf`: texto com git e commit perto de uma expansão (`printf '… git-lock … commit' "$(date)"`) pergunta, e heredoc seguido de pipe (`cat <<'E' | bash`) também.
- Texto de várias linhas entre aspas duplas com `&` (um `gh pr create --body "…"` com "A & B" numa linha do meio) agora pergunta (#396): corpo de PR e issue com `--body-file` gravado por Write.
- Commit só na forma canônica e só pelo agente principal; subagente não grava.
- Edição de teste que remove ou troca `assert` é negada pelo teste-guard em subagente (dia ou noite) e pergunta no agente principal (#313): acrescentar testes em vez de trocar asserts. O git-lock também nega em subagente o commit fora da forma canônica. O teste-guard só vê Edit/Write: edição por script passa, e a linha "Testes" do cartão do Gate 2 conta os asserts removidos no diff do PR (#396).
- Comparação nova num teste novo não pergunta mais; trocar `==` por `>=` num assert existente pergunta.
- Worktrees em `alw-wt/<issue>`; nada fora dele.
- Antes de sair: `/noite` (ou `campanhas.py noite-flag ligar`) liga o flag `.workflow/local/noite` do lab por 12 h e mostra as tarefas livres. Com ele, o `ask` do git-lock e do teste-guard vira bloqueio com motivo também no agente principal, que reescreve o comando ou acrescenta testes (#345, #347). De manhã: `/dia`.
- O gate2-pergunta também nega à noite: `git commit`/`git push` sem Gate 2 da tarefa, `gh pr merge` fora da forma `gh pr merge N [--squash|--merge|--rebase|-d|--auto|--admin]` ou sem Gate 2 do PR (`gates.py verificar --pr N`), e qualquer falha da conferência (#358).

## Limites do gate2-pergunta (#358)

O mod é um freio contra erro, não uma barreira contra agente hostil. Fora do escopo, sem pergunta garantida:

- `pwsh -c` / `cmd /c`, alias do git e merge por `gh api`.
- Comando entregue por `| bash`, `<<<` ou `bash <<EOF`.
- Registro antigo da issue N aprova um PR novo que feche N ou tenha N na branch (`verificar --pr` casa por issue).
- `verificar_pr` rodado em `dev` para um PR dev→main: a branch `dev` não traz issue, só vale o registro com `--pr`.
- `cd` montado por variável ou expansão (`X=cd; $X B`, `${X:-cd} B`), variável de ambiente com nome quebrado por aspas (`declare -x GIT_""DIR=…`), `find … -execdir git commit` e glob no `cd` (`cd wt[38]` é lido ao pé da letra, sem expandir).
- Na ferramenta PowerShell, o mod não resolve o alvo: commit, push ou `gh pr merge` sempre pergunta de dia (mostrando o registro da tarefa da sessão) e nega à noite. As palavras valem em qualquer ordem (`$p=@('push'); git @p` pergunta), mas git montado por concatenação (`'gi'+'t'`), backtick (`` g`it ``), `gcm`/`Get-Command` ou `-EncodedCommand` passa sem pergunta.
- Comentário `#` com apóstrofo antes de `'<<EOF'` e a forma `$'\''` confundem o rastreio de aspas do mod (sem parser de shell real).
- `git push` para remoto ou caminho de outro repositório (`git push ../B HEAD:main`): o mod confere o checkout de onde sai o push, não o destino.
- Script (Python ou outro) que chama `gh pr merge` ou `git push` por subprocess: o mod só vê o comando do Bash, não o que o script roda. O coordenador usava um script assim para esperar o CI e mergear; desde 24/10 o merge é chamada direta de `gh pr merge N`.

Comando em outro checkout do lab (`git -C alw-wt/N commit`, `cd alw-wt/N && …`, `--work-tree`, `--git-dir …/.git`): o mod confere o Gate 2 da tarefa daquele checkout (`gates.py verificar --checkout DIR`: `active-task.md` dele ou, sem ele, a issue da branch `<tipo>/<N>-<slug>`). O alvo só é certo em três formas: `git [-C dir]... [-c k=v]... commit|push …`, `cd <dir> && git … (&& git …)*` (um `cd`, no início) e `git … && git …` sem `cd`. O `gates.py` roda na pasta atual da sessão dada por `$.session.cwd()`; sem ela, comando sem alvo absoluto também pergunta. Qualquer outra (`;`, `||`, `|`, `&`, `#`, `pushd`, `command cd`, variável, `$( )`, dois alvos) ou alvo fora do lab (`--git-common-dir` diferente) pergunta de dia e nega à noite. Toda pergunta mostra o registro achado.
