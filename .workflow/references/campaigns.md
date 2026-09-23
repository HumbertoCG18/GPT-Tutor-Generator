# Fila de campanhas

Ler ao consultar, selecionar, reservar ou atualizar campanhas; não carregar preventivamente.
Política canônica; o estado vive no tracker do projeto, em bloco delimitado `fila-campanhas`.
Sequência, prioridades e bloqueios de cada projeto ficam só no tracker, nunca aqui.
Não há daemon, monitor nem garantia técnica de obediência: a disciplina é do coordenador.

## Estrutura

- Campanha agrupa tarefas atômicas com aceite, estado, evidência e dependências.
- IDs estáveis, nunca reutilizados; origem `USER` (pedido), `CODE` (achado no código) ou `DECISION` (decisão registrada). Deduplicar por issue/resultado/escopo.
- Estados: proposta · pronta · em execução · bloqueada · reservada · concluída.
- Restantes = tarefas ainda não verificadas, incluindo bloqueadas e propostas. Escopo desconhecido ou não decomposto mostra "a definir", nunca zero.
- Goals referenciam tarefas; não duplicam contagem nem aceite.
- Campanha só fecha com 100% dos aceites cumpridos e integração aprovada, não pela emissão de relatório.
- Ideia nova entra como proposta, nunca como autoridade para execução. Gates 1/2 permanecem.

## Seleção e confirmação

- Menu nativo quando a ferramenta de escolha estiver exposta e permitida no modo; senão, menu numerado por mensagem normal.
- Confirmação: título/ID, N restantes, estimativa (não medida ou "a definir"), prioridade, janela e risco. Rótulo limitado pela UI: compactar o rótulo e manter metadados no corpo.
- Opções: executar agora · reservar · detalhar · voltar. Tarefa bloqueada só admite detalhar ou desbloquear, nunca lançar.
- Não repetir escolha já registrada no tracker.

## Estimativa, janela e reserva

- Estimativa intervalar é explicitamente NÃO medida: declarar premissas e confiança. Duração medida entra à parte. Não inventar contagem nem tempo.
- Trabalho longo, repetitivo e de aceite determinístico sugere janela noturna; risco alto, ambiguidade ou ação irreversível sugere janela assistida.
- Reservar só registra preferência: não lança, não agenda. Preflight, quota e aprovação continuam exigidos.

## Escrita

- Um coordenador por tarefa e um writer por bloco; reler o bloco antes de escrever e preservar alterações de outras sessões.
- Ler a fila no início/retomada; atualizar ao descobrir pendência e ao concluir tarefa, durante sessão ativa.
- Sessão read-only não escreve: propõe o delta ao coordenador.
