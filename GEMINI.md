# GPT-Tutor-Generator

Read `AGENTS.md`, `.mex/ROUTER.md` and `.mex/patterns/engenharia-produto.md` before work.
Follow the current shared workflow for issues, PRs, release, UI, observability and quality.

Campanhas: estado no bloco `fila-campanhas` de `docs/reports/pendencias.md`; política em
`references/campaigns.md` da fonte compartilhada, fallback `.workflow/references/campaigns.md`.
Ler só ao consultar, selecionar, reservar ou atualizar campanhas.

## Navegação estrutural

Graphify é o grafo principal deste projeto (`graphify-out/graph.json`). Para
estrutura, callers e dependências: Graphify explain/path com o símbolo exato;
query aberta só com budget. Sem cobertura, ambiguidade ou falha: codebase-memory-mcp
como fallback, conforme `.mex/patterns/codegraph-fallback.md`. O grafo orienta a
navegação; confirmar no código-fonte antes de concluir ou editar.
code-review-graph foi removido: não usar suas ferramentas.
