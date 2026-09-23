# Engenharia do GPT Tutor

Fluxo canônico: agent-workflow-lab/workflow.md, rota "Issues, PRs e releases".
Issue antes de alteração, branch por escopo, PR relacionado; Gates 1/2 preservados.
Release exige commit rastreável, verificações, smoke e rollback. Configurar ferramenta não prova aceite.

## Rotas por mudança

Ler o detalhe pertinente em [engenharia-produto-details.md](engenharia-produto-details.md):

| Mudança | Seção |
|---|---|
| Issue/PR/release | Fluxo de entrega |
| UI desktop/web | UI: todos os estados, movimento com propósito |
| Escolha de ferramenta/stack | Ferramentas por responsabilidade e stack |
| Logs, métricas, erros ou qualidade | Observabilidade e aceite |
| Campanhas #10–#14 | Fila e fontes |

Produto atual: Python/Tkinter; C6 web requer escopo próprio. Não instalar ferramentas web
no runtime Python por antecipação. Não adotar todos os candidatos de uma lista.
Preservar offline e dados privados; exportação externa exige destino/configuração explícitos.
Checks proporcionais antes do merge; baseline precede metas de cobertura/performance.
