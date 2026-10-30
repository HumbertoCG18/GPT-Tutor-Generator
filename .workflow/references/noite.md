# Agente noturno

Ler ao coordenar trabalho noturno; não carregar preventivamente. Registro e estados: campaigns.md.

1. Tomar só tarefas `livre` de `campanhas.py listar --noite`. Nada livre: dizer no chat e parar.
   Aberto pelo agendador do Alethe: a tarefa já vem no prompt; trabalhar só nela, sem escolher outra.
2. Uma tarefa por vez, com o seu `.workflow/local/active-task.md` (`campanha`, `tarefa`, classificação).
   Cada tarefa num subagente de contexto novo; só o pai (o coordenador da noite) grava o diário (`campanhas.py noite`).
3. Delegar com `task: <ID>` igual a `tarefa`; contratos de delegação, revisão e timeout valem (delegation.md, review.md).
4. Registrar cada resultado: `campanhas.py noite <ID> --resultado ok|aguarda-voce|falhou|parou --resumo "…" [--evidencia "…"]`.
   Abrir o `--resumo` com o estado de retomada (`retomada:`, `do zero:`, `Gate 2:`, `decisão:`, `falhou:`), tabela em resume.md.
   Execução longa grava `.workflow/local/execucao.json` com `i`, `N`, `inicio`, `teto` e `pid`, como o `replay.py`.
   Selo `✕ parado` na tarefa ativa: o processo morreu antes do teto; registrar `parou`, sem esperar o teto (#142).
5. Gate 2 automático (#486), só T1/T2 e fora das guardas: na worktree, antes do commit, `gates.py gate2 --tarefa ID --aprovador noite-auto`. Ele grava só com a última rodada de revisão Codex (`astra_review.py run`) APPROVED neste HEAD e neste conteúdo (tarefa que precisa de revisão Claude fica `aguarda-voce`), nível T1/T2 no registro de campanhas e Gate 1 do dono (`gate1-aprovado`) com a issue da branch, a noite ligada no flag real (o `CAMPANHAS_NOITE_FLAG` dos testes não conta e o git-lock o nega em chamada ao `gates.py` ou ao `campanhas.py`), diff só em `arquivos_permitidos` e fora de `hooks/`, `githooks/`, `plugins/gate2-pergunta/`, `plugins/astra-review/`, `bin/gates.py`, `bin/campanhas.py`, `workflow.md`, `references/noite.md` e settings, nenhum assert removido e a suíte do CI verde (o `gates.py` roda). Com ele, `git add` numa chamada própria, depois `git commit`, `git push origin <branch>` e `gh pr create --draft` passam; editar a worktree depois invalida o Gate 2, e índice diferente da worktree aprovada também; de dia o `noite-auto` não vale, o Gate 2 volta ao dono. À noite o git-lock nega escrita em `.workflow/campanhas.json` fora do `campanhas.py`. Recusa: a tarefa fica `aguarda-voce` com o motivo. Merge nunca (Gate 3 do dono).
   Sem `noite-auto`, nunca concluir: o Gate 2 é do usuário. Não marcar `gate_2: aprovado` nem rodar `estado … concluída`. Trabalho pronto fica `status: concluido` com `gate_2: pendente` (o hook deixa a tarefa `bloqueada`, aguardando o Gate 2), recebe no registro `campanhas.py estado <ID> bloqueada --gate2 pendente` e entra no diário como `aguarda-voce` com resumo `Gate 2:`; parada numa decisão de plano também é `aguarda-voce`, com `decisão:`.
6. Toda espera por subagente tem prazo (#396): Monitor no mtime de `subagents/agent-<id>.jsonl` da sessão (o `tasks/<id>.output` fica com 0 bytes até o fim), avisando com 4 min sem escrita e teto de 30 min. Aviso de "interim" ou "waiting on its own background work" sem processo em segundo plano: ler a transcrição e a worktree, sem esperar mais. Agente retomado por SendMessage não entrega um 2º relatório: o resultado está na transcrição.
7. Achado fora da tarefa: `campanhas.py achado "título" --tipo ideia|bug|risco|divida --origem <ID>`, sem investigar; no máximo 3 por tarefa.

## Rodada antes da noite

1. O agente roda `campanhas.py listar --rodada` (T1/T2 prontas, sem dependência aberta; a `janela` não filtra).
2. Grilling das escolhidas por pergunta nativa, até 4 por chamada, recomendada em 1º.
3. Por tarefa aprovada: `gates.py gate1-aprovado --tarefa ID --issue N --citacao "<palavras do dono>"`, com N a issue da branch da tarefa (`<tipo>/<N>-<slug>`). Só essas ficam `livre` em `listar --noite`.
4. O dono liga a noite com `/noite`. A aprovação vale 12 h; mais velha, no futuro ou seguida de `gate1-reprovado`, não vale.

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
- Antes de sair: o dono roda `/noite` (o git-lock bloqueia o agente que tenta `campanhas.py noite-flag ligar` ou `desligar`, #463), que liga o flag `.workflow/local/noite` do lab por 12 h e mostra as tarefas livres. Com ele, o `ask` do git-lock e do teste-guard vira bloqueio com motivo também no agente principal, que reescreve o comando ou acrescenta testes (#345, #347). De manhã: `/dia`.
- O gate2-pergunta também nega à noite: `git commit`/`git push` sem Gate 2 da tarefa, `gh pr merge` fora da forma `gh pr merge N [--squash|--merge|--rebase|-d|--auto|--admin]` ou sem Gate 2 do PR (`gates.py verificar --pr N`), e qualquer falha da conferência (#358).
- Merge à noite nunca: o Gate 3 (merge na `dev`) é do dono. `gates.py verificar --pr N` responde 1 com a noite ligada e o git-lock nega `gh pr merge`, mesmo com Gate 2 válido (#486).
- À noite o gate2-pergunta só deixa `git commit`, `git push` e `gh pr create` com Gate 2 `noite-auto` válido; o PR só em rascunho (`--draft`) e nesta pasta; o push nomeia a branch de destino e nunca vai para `dev`, `main` ou `master` (destino não lido também é negado). O pre-push `pre-push-tronco` recusa o tronco à noite em qualquer worktree, pelo que o próprio git envia; vale depois que o dono roda `gates.py instalar` de novo. O git-lock nega escrita em `.workflow/local/astra-reviews` (só `astra_review.py` grava) e o cartão do Gate 3 mostra a linha `Gate 2 · noite-auto` (#486).

## Limites do gate2-pergunta (#358)

O mod é um freio contra erro, não uma barreira contra agente hostil. Fora do escopo, sem pergunta garantida:

- `pwsh -c` / `cmd /c`, alias do git e merge por `gh api`.
- Comando entregue por `| bash`, `<<<` ou `bash <<EOF` (`echo "git push" | bash`): o texto entregue é dado, não comando vigiado, e passa sem recusa nem pergunta.
- Comentário `#` com `;` ou `|` depois de um commit/push vigiado (`git push origin b # ; x`) é recusado como composição: o mod não lê comentários.
- Na mesma pasta, o formato aceita `git -C A switch B && git -C A push …` e preparação mutável antes do push (`git -C A reset --hard x && git -C A push …`): a conferência é a tarefa do checkout A, não a branch que o `switch` deixa (#556).
- `gh pr create` não é comando vigiado: composto com ele não é recusado pelo formato; à noite segue a regra do rascunho.
- Registro antigo da issue N aprova um PR novo que feche N ou tenha N na branch (`verificar --pr` casa por issue).
- `verificar_pr` rodado em `dev` para um PR dev→main: a branch `dev` não traz issue, só vale o registro com `--pr`.
- `cd` montado por variável ou expansão (`X=cd; $X B`, `${X:-cd} B`), variável de ambiente com nome quebrado por aspas (`declare -x GIT_""DIR=…`), `find … -execdir git commit` e glob no `cd` (`cd wt[38]` é lido ao pé da letra, sem expandir).
- Na ferramenta PowerShell, o mod não resolve o alvo: commit, push ou `gh pr merge` sempre pergunta de dia (mostrando o registro da tarefa da sessão) e nega à noite. As palavras valem em qualquer ordem (`$p=@('push'); git @p` pergunta), mas git montado por concatenação (`'gi'+'t'`), backtick (`` g`it ``), `gcm`/`Get-Command` ou `-EncodedCommand` passa sem pergunta.
- Comentário `#` com apóstrofo antes de `'<<EOF'` e a forma `$'\''` confundem o rastreio de aspas do mod (sem parser de shell real).
- `git push` para remoto ou caminho de outro repositório (`git push ../B HEAD:main`): o mod confere o checkout de onde sai o push, não o destino.
- Script (Python ou outro) que chama `gh pr merge` ou `git push` por subprocess: o mod só vê o comando do Bash, não o que o script roda. O coordenador usava um script assim para esperar o CI e mergear; desde 24/10 o merge é chamada direta de `gh pr merge N`.

Comando em outro checkout do lab (`git -C alw-wt/N commit`, `cd alw-wt/N && …`, `--work-tree`, `--git-dir …/.git`): o mod confere o Gate 2 da tarefa daquele checkout (`gates.py verificar --checkout DIR`: `active-task.md` dele ou, sem ele, a issue da branch `<tipo>/<N>-<slug>`). O alvo só é certo em três formas: `git [-C dir]... [-c k=v]... commit|push …`, `cd <dir> && git … (&& git …)*` (um `cd`, no início) e `git … && git …` sem `cd`. O `gates.py` roda na pasta atual da sessão dada por `$.session.cwd()`; sem ela, comando sem alvo absoluto também pergunta. Toda pergunta mostra o registro achado.

Recusa de formato (#556), antes de qualquer conferência, de dia e de noite, sem card, sem `gates.py` e sem ler a noite: commit, push ou `gh pr merge` com outro comando anexado (`;`, quebra de linha, `||`, `&` sozinho), pipe no meio ou para fora do filtro final (`| tee`, `| xargs`, `| bash`), redirecionamento (`>`, `<`, `<<<`, `N>&M` no meio) ou commit/push em dois checkouts ou com dois `cd`. A negação traz o código (`pipeline-seguido`, `pipeline`, `composicao`, `segundo-plano`, `redirecionamento`, `multiplos-alvos`), a coluna e a forma a reenviar; nada é executado nem cortado. Texto entre aspas, mensagem canônica, `-F arquivo` e corpo de heredoc são dados e não contam. Continuam incerteza (pergunta de dia, nega à noite), com o código no motivo: `$VAR`, `$( )`, crase, `~` ou `{}` no alvo (`checkout-dinamico`) e forma fora da allowlist (`sintaxe`: `pushd`, `command cd`, `#`, `( )`), além de alvo fora do lab (`--git-common-dir` diferente).

Noite em três estados (#556): `campanhas.py noite-flag estado` com exit 0 e `noite ligada…` é noite; exit 1 e `noite desligada` é dia; qualquer outra saída (sem python, timeout, traceback) é desconhecida e nega como a noite, sem card: "Estado da noite não confirmado (codigo noite-desconhecida)". O card de dia mostra a branch do checkout alvo (`git -C <alvo> rev-parse --abbrev-ref HEAD`; `HEAD destacado`; falha vira `não resolvido`), nunca a da sessão para outro checkout.
