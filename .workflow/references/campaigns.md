# Fila de campanhas

Ler ao consultar, selecionar, reservar ou atualizar campanhas; não carregar preventivamente.
Política canônica; o estado vive em `.workflow/campanhas.json` do checkout principal do projeto
(o mesmo arquivo em qualquer worktree). Não há daemon nem garantia técnica de obediência: a disciplina é do coordenador.

## Registro

- Ferramenta: `bin/campanhas.py` — `listar [--noite] [--curto] [--arquivo]`, `arquivar [--dias N]`, `validar`, `estado ID NOVO [--evidencia T] [--resultado T]`, `tarefa`, `janela`, `passo`, `ativa`, `noite`, `noite-flag`, `achado`, `achados`, `triar`, `limpar-achados`, `sobreposicao`. `--registro CAMINHO` substitui o local. O hook SessionStart (hooks/README.md) injeta `listar --curto`.
- Movido para [campaigns-details.md › Registro: caminhos raros](campaigns-details.md#registro-caminhos-raros): arquivo (`arquivar`), diário da noite, vetos (`vetos.json`) e gabarito do painel do Alethe.
- Campanha: `id`, `titulo`, `prioridade`, `janela`, `depende_de`, `worktrees`, `handoff`, `atualizado_em`, `decomposta`, `tarefas`.
- Tarefa, campo opcional `worktree` (texto, pasta da worktree): `campanhas.py estado <id> <novo> --worktree <pasta>`; `validar` exige texto. `manutencao.py` lista em `tarefas_concluidas` a worktree cuja tarefa está `concluída`, candidata a retirar (o estado do git continua decidindo).
- Tarefa, campo opcional `gate_2` (`pendente` ou `aprovado`): `campanhas.py estado <id> <novo> --gate2 pendente|aprovado`; `validar` recusa outro valor. `pendente` = trabalho pronto aguardando o Gate 2 do dono; `aprovado` só depois da aprovação dele.
- Tarefa: `id`, `titulo`, `nivel`, `estado`, `depende_de`, `janela`, `eixo`, `nota`, `motivo`, `origem`, `evidencia`, `resultado`, `recorrente`, `passos` (`[{texto, feito}]`; o atual é o primeiro não feito).
- Estados: proposta · pronta · em execução · bloqueada · reservada · concluída · descartada (fechada sem entrega: fora do percentual, vale de qualquer estado, inclusive concluída). `estado … concluída` é recusado com passo aberto. Janelas: assistida · noite · qualquer. `depende_de` aceita IDs de tarefa ou de campanha.
- Mudar estado só por `estado`: grava escrita atômica e atualiza `atualizado_em`. Narrativa longa vai ao arquivo `handoff` da campanha, não ao registro. Rodar `validar` após edição manual.
- Criar tarefa só por `tarefa CAMPANHA "título" [--nivel] [--estado proposta|pronta] [--depende ID ...] [--origem USER|CODE|DECISION]`: imprime o id novo `<CAMPANHA>-NN` (maior sufixo numérico da campanha + 1, mín. 2 dígitos, nunca reusa; colisão no registro incrementa). A Todo List do Alethe usa a mesma regra, o mesmo lock e a mesma escrita atômica.
- IDs estáveis, nunca reutilizados; `origem` USER, CODE ou DECISION. Deduplicar por issue/resultado/escopo.
- `decomposta: false` mostra `+?` no total: escopo desconhecido é "a definir", nunca zero.
- Goals referenciam tarefas; não duplicam contagem nem aceite.
- Campanha só fecha com 100% dos aceites cumpridos e integração aprovada, não pela emissão de relatório.

## Elo com a tarefa ativa

Em todo repo o tronco é a `dev`; a `main` é backup e só recebe a `dev` por PR de promoção
quando uma campanha fecha com a suíte inteira verde e a revisão de fim de campanha aprovada
(review.md). O PR sai de `sync/promocao-<campanha>`, criada
no commit validado da `dev`, com `--base main` (o registry-guard só isenta `sync/*`). A `main` segue como branch padrão do
GitHub (vitrine estável), então todo PR de trabalho leva `--base dev`.
Unidade de integração: campanha acoplada (tarefas só funcionam juntas, como no GPT Tutor) usa
uma worktree de desenvolvimento criada da `dev` atual conferida e entra na `dev` só ao terminar;
as tarefas compartilham essa worktree e seus checkpoints, e uma campanha nova recebe outra
worktree a partir da `dev` já integrada. Campanha de tarefas independentes (padrão do lab):
uma worktree e um PR para `dev` por tarefa.
`git worktree add -b <branch-da-campanha> <pasta> dev` cria o checkout; registrar base/HEAD,
campanha e tarefa no estado local. Não herdar estado operacional da campanha anterior.

Ao terminar: checks aplicáveis verdes, revisão independente e aceites cumpridos;
Gate 2 antes de commit e autorização própria para push/merge. Integrar por PR para `dev`,
verificar o commit integrado e só então retirar a worktree. Verde não autoriza merge.
Não acumular worktrees antigas só para preservar o snapshot do workflow.

Antes de remover: inventariar diff/index/untracked/ignorados, commits exclusivos, PRs,
PTYs/workers/spawns pendentes e symlinks/junctions. HEAD antigo ou integrado não prova
que o WIP foi entregue. Evidência local útil vai para backup com hashes; código não
integrado e sessões ativas impedem remoção, assim como a pasta citada em `worktrees` ou no
`handoff` de campanha com tarefa não concluída no registro: concluir ou atualizar a tarefa antes. Usar `git worktree remove` sem `--force`;
não apagar branches remotas nem integrar WIP como efeito colateral da limpeza.
Worktrees legadas com código pendente são exceções preservadas até integrar ou arquivar
explicitamente esse código. Não propagá-las só para ocultar drift no verificador.
Arquivar = commit `wip: arquivado` na branch, push e `git worktree remove`; a branch local fica.
Enquanto não estiver no tronco, o hook de início a lista, e antes de uma implementação nova o
agente oferece retomar, integrar por PR, descartar (`git branch -d` só depois de integrada; a
remota fica) ou adiar.

1. Escolher a tarefa do registro (criar com `tarefa` se faltar).
2. Gravar `campanha` e `tarefa` em `.workflow/local/active-task.md`; ao passar a `status: executando`, o hook sincroniza-tarefa.py põe `em execução` no registro.
3. Delegar com `task: <ID>` igual a `tarefa`. Com registro, o delegate-gate.py bloqueia delegação, revisão ou validação sem tarefa aberta e dá o comando de criação.
4. Revisar; o Gate 2 é do usuário (`gate_2: aprovado…`).
5. `concluido` com Gate 2 aprovado e `evidencia_de_aceite` preenchida vira `concluída` (o hook espelha; o Stop fecha-tarefa.py cobra se faltar). Sem Gate 2 ou sem evidência, fica `bloqueada` com o motivo em `resultado`; `concluída` nunca reabre sozinha.

## Passos de aceite

- Ao iniciar uma tarefa, o coordenador dela (o agente que executa, inclusive o da noite) define de 3 a 7 passos de aceite com `passo TAREFA --definir "…" "…"` e marca cada um com `--feito N` assim que estiver verificavelmente feito (`--desfazer N` volta atrás; `passo TAREFA` sem opção imprime `feitos/total · passo atual`).
- Os passos são o progresso da tarefa que o dono vê no Alethe (linha, detalhe e título do terminal) e, no Claude Code, acima do prompt (mod `tarefa-ativa`, via `campanhas.py ativa`: a `tarefa` do `active-task.md` do checkout; sem ele, nada aparece). Revisor e sessão read-only não escrevem passos: propõem o delta ao coordenador.
- `passo` não muda o estado da tarefa; o Gate 2 do dono não muda. Tarefa concluída recusa; `--definir` sobre passo já feito exige `--forcar`.

## Seleção e confirmação

- Menu nativo quando a ferramenta de escolha estiver exposta e permitida no modo; senão, menu numerado por mensagem normal.
- Confirmação: título/ID, N restantes, estimativa (não medida ou "a definir"), prioridade, janela e risco.
- Opções: executar agora · reservar · detalhar · voltar. Tarefa bloqueada só admite detalhar ou desbloquear, nunca lançar.
- Não repetir escolha já registrada no registro.
- Uma sessão por campanha (aprovado pelo dono em 23/10/2026, #339): trabalho fora de campanha conta como frente própria. Ao trocar de campanha ou de frente, o estado vai para o registro, o `active-task.md` e o work_state, e a próxima começa com `/clear` ou sessão nova. Motivo: na sessão 9d476570, que juntou seis frentes, `/context` deu 323.3k de 400k, com as mensagens em 293.9k e o custo fixo da sessão em ~29k.

## Estimativa, janela e reserva

- Estimativa intervalar é NÃO medida: declarar premissas e confiança. Não inventar contagem nem tempo.
- Trabalho longo, repetitivo e de aceite determinístico sugere janela noturna; risco alto, ambiguidade ou ação irreversível sugere janela assistida.
- Trabalho noturno: só tarefas de janela efetiva noite (a da tarefa, senão a da campanha) cujas dependências estão concluídas; `listar --noite` mostra livres e em espera. Coordenação: references/noite.md.
  Marcar: `campanhas.py janela <ID> noite` (tarefa aberta) ou `tarefa … --janela noite` na criação.
- Reservar só registra preferência: não lança, não agenda. Preflight, quota e aprovação continuam exigidos.

## Escrita

Movido para [campaigns-details.md › Escrita](campaigns-details.md#escrita): um coordenador e um writer por registro, registro só no checkout principal (registry-guard) e conflitos de snapshot.

## Achados

Movido para [campaigns-details.md › Achados](campaigns-details.md#achados): caixa `achados.json`, limite de 3 por tarefa, triagem e `limpar-achados`.
