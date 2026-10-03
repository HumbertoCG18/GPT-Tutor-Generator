# Fila de campanhas

Ler ao consultar, selecionar, reservar ou atualizar campanhas; não carregar preventivamente.
Política canônica; o estado vive em `.workflow/campanhas.json` do checkout principal do projeto
(o mesmo arquivo em qualquer worktree). Não há daemon nem garantia técnica de obediência: a disciplina é do coordenador.

## Registro

- Ferramenta: `bin/campanhas.py` — `listar [--noite] [--curto]`, `validar`, `estado ID NOVO [--evidencia T] [--resultado T]`, `tarefa`, `noite`, `achado`, `achados`, `triar`. `--registro CAMINHO` substitui o local. O hook SessionStart (hooks/README.md) injeta `listar --curto`.
- Diário da noite: `noite TAREFA --resultado ok|aguarda-voce|falhou|parou --resumo T [--evidencia T]` acrescenta uma entrada em `.workflow/local/noites/<AAAA-MM-DD>.json` do checkout principal (data em que a noite começou: antes de 12:00, ontem); resumo até 120 caracteres; não muda o estado da tarefa. `listar --curto` resume o diário mais recente em "Noite de DD/MM: …".
- Campanha: `id`, `titulo`, `prioridade`, `janela`, `depende_de`, `worktrees`, `handoff`, `atualizado_em`, `decomposta`, `tarefas`.
- Tarefa: `id`, `titulo`, `nivel`, `estado`, `depende_de`, `janela`, `eixo`, `nota`, `motivo`, `origem`, `evidencia`, `resultado`, `recorrente`.
- Estados: proposta · pronta · em execução · bloqueada · reservada · concluída. Janelas: assistida · noite · qualquer. `depende_de` aceita IDs de tarefa ou de campanha.
- Mudar estado só por `estado`: grava escrita atômica e atualiza `atualizado_em`. Narrativa longa vai ao arquivo `handoff` da campanha, não ao registro. Rodar `validar` após edição manual.
- Criar tarefa só por `tarefa CAMPANHA "título" [--nivel] [--estado proposta|pronta] [--depende ID ...] [--origem USER|CODE|DECISION]`: imprime o id novo `<CAMPANHA>-NN` (maior sufixo numérico da campanha + 1, mín. 2 dígitos, nunca reusa; colisão no registro incrementa). A Todo List do Alethe usa a mesma regra, o mesmo lock e a mesma escrita atômica.
- IDs estáveis, nunca reutilizados; `origem` USER, CODE ou DECISION. Deduplicar por issue/resultado/escopo.
- `decomposta: false` mostra `+?` no total: escopo desconhecido é "a definir", nunca zero.
- Goals referenciam tarefas; não duplicam contagem nem aceite.
- Campanha só fecha com 100% dos aceites cumpridos e integração aprovada, não pela emissão de relatório.
- Gabarito: o painel do Alethe reimplementa progresso e situação em TS. Ao mudar uma regra, regenerar `bin/fixtures/campanhas.gabarito.json` com `listar --json --registro bin/fixtures/campanhas.exemplo.json` e copiar os dois arquivos para o teste do Alethe; percentual arredonda meio para cima nos dois.

## Elo com a tarefa ativa

1. Escolher a tarefa do registro (criar com `tarefa` se faltar).
2. Gravar `campanha` e `tarefa` em `.workflow/local/active-task.md`; ao passar a `status: executando`, o hook sincroniza-tarefa.py põe `em execução` no registro.
3. Delegar com `task: <ID>` igual a `tarefa`. Com registro, o delegate-gate.py bloqueia delegação, revisão ou validação sem tarefa aberta e dá o comando de criação.
4. Revisar; o Gate 2 é do usuário (`gate_2: aprovado…`).
5. `concluido` com Gate 2 aprovado e `evidencia_de_aceite` preenchida vira `concluída` (o hook espelha; o Stop fecha-tarefa.py cobra se faltar). Sem Gate 2 ou sem evidência, fica `bloqueada` com o motivo em `resultado`; `concluída` nunca reabre sozinha.

## Seleção e confirmação

- Menu nativo quando a ferramenta de escolha estiver exposta e permitida no modo; senão, menu numerado por mensagem normal.
- Confirmação: título/ID, N restantes, estimativa (não medida ou "a definir"), prioridade, janela e risco.
- Opções: executar agora · reservar · detalhar · voltar. Tarefa bloqueada só admite detalhar ou desbloquear, nunca lançar.
- Não repetir escolha já registrada no registro.

## Estimativa, janela e reserva

- Estimativa intervalar é NÃO medida: declarar premissas e confiança. Não inventar contagem nem tempo.
- Trabalho longo, repetitivo e de aceite determinístico sugere janela noturna; risco alto, ambiguidade ou ação irreversível sugere janela assistida.
- Trabalho noturno: só tarefas de janela efetiva noite (a da tarefa, senão a da campanha) cujas dependências estão concluídas; `listar --noite` mostra livres e em espera. Coordenação: references/noite.md.
  Marcar: `campanhas.py janela <ID> noite` (tarefa aberta) ou `tarefa … --janela noite` na criação.
- Reservar só registra preferência: não lança, não agenda. Preflight, quota e aprovação continuam exigidos.

## Escrita

- Um coordenador por tarefa e um writer por registro; `estado` relê o arquivo antes de gravar.
- Ler a fila no início/retomada; atualizar ao descobrir pendência e ao concluir tarefa, durante sessão ativa.
- Sessão read-only não escreve: propõe o delta ao coordenador.
- Ideia nova entra como `proposta`, nunca como autoridade para execução. Gates 1/2 permanecem.

## Achados

- Caixa: `.workflow/achados.json` do checkout principal (versionada, mesma trava e escrita atômica do registro). Achado fora da tarefa atual vira uma linha `achado "título" --tipo ideia|bug|risco|divida [--origem TAREFA] [--detalhe T]`, que imprime `ACH-NNNN`; o agente não investiga e segue a tarefa.
- No máximo 3 achados novos por tarefa (`--origem`); título até 100 caracteres, sem duplicar achado não descartado.
- Triagem só quando o usuário pedir ("triar achados"): listar com `achados --novos`, o usuário decide cada um, então `triar ACH-NNNN --virar CAMPANHA [--titulo T] [--nivel Tn]` (cria tarefa `proposta`, origem CODE) ou `--descartar "motivo"`.
- `listar --curto` só informa a contagem de achados novos, nunca os títulos.
