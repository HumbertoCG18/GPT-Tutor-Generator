# Fila de campanhas

Ler ao consultar, selecionar, reservar ou atualizar campanhas; não carregar preventivamente.
Política canônica; o estado vive em `.workflow/campanhas.json` do checkout principal do projeto
(o mesmo arquivo em qualquer worktree). Não há daemon nem garantia técnica de obediência: a disciplina é do coordenador.

## Registro

- Ferramenta: `bin/campanhas.py` — `listar [--noite] [--curto]`, `validar`, `estado ID NOVO [--evidencia T] [--resultado T]`. `--registro CAMINHO` substitui o local. O hook SessionStart (hooks/README.md) injeta `listar --curto`.
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

## Seleção e confirmação

- Menu nativo quando a ferramenta de escolha estiver exposta e permitida no modo; senão, menu numerado por mensagem normal.
- Confirmação: título/ID, N restantes, estimativa (não medida ou "a definir"), prioridade, janela e risco.
- Opções: executar agora · reservar · detalhar · voltar. Tarefa bloqueada só admite detalhar ou desbloquear, nunca lançar.
- Não repetir escolha já registrada no registro.

## Estimativa, janela e reserva

- Estimativa intervalar é NÃO medida: declarar premissas e confiança. Não inventar contagem nem tempo.
- Trabalho longo, repetitivo e de aceite determinístico sugere janela noturna; risco alto, ambiguidade ou ação irreversível sugere janela assistida.
- Trabalho noturno: só tarefas de janela efetiva noite (a da tarefa, senão a da campanha) cujas dependências estão concluídas; `listar --noite` mostra livres e em espera.
- Reservar só registra preferência: não lança, não agenda. Preflight, quota e aprovação continuam exigidos.

## Escrita

- Um coordenador por tarefa e um writer por registro; `estado` relê o arquivo antes de gravar.
- Ler a fila no início/retomada; atualizar ao descobrir pendência e ao concluir tarefa, durante sessão ativa.
- Sessão read-only não escreve: propõe o delta ao coordenador.
- Ideia nova entra como `proposta`, nunca como autoridade para execução. Gates 1/2 permanecem.
