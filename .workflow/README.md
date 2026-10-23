# Snapshot do workflow comum

Cópia do `agent-workflow-lab` (fonte canônica: `agent-workflow-lab/workflow.md`). Entrada:
[workflow.md](workflow.md); detalhes por ação em [references/](references/); papéis inline em
[agents/README.md](agents/README.md).

Arquivos com hash em [manifest.json](manifest.json) não se editam aqui: mudar no laboratório e
rodar lá `python bin/manutencao.py snapshots --aplicar`. O comando escreve no checkout principal
deste repo; levar a mudança para uma branch própria e commitar pelo Gate 2.

Do projeto, fora da cópia: este README, a fila `campanhas.json` e a caixa `achados.json` (alteradas
só por `agent-workflow-lab/bin/campanhas.py`) e `local/` (estado da tarefa ativa, não versionado).
Não há handoff: o estado vivo fica na fila.
