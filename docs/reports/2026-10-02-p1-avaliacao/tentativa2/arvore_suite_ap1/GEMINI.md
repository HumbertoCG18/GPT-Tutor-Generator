# GPT-Tutor-Generator

Leia `AGENTS.md`: identidade, invariantes, comandos e onde procurar cada fonte.

## Navegação estrutural

Graphify é o grafo principal deste projeto (`graphify-out/graph.json`). Para
estrutura, callers e dependências: Graphify explain/path com o símbolo exato;
query aberta só com budget. Sem cobertura, ambiguidade ou falha: codebase-memory-mcp
como fallback, conforme `.mex/patterns/codegraph-fallback.md`. O grafo orienta a
navegação; confirmar no código-fonte antes de concluir ou editar.
code-review-graph foi removido: não usar suas ferramentas.
