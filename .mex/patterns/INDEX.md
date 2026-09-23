# Pattern Index

last_updated: 2026-09-17

Lookup table for all pattern files in this directory. Check here before starting any task — if a pattern exists, follow it.

| Pattern | Use when |
|---------|----------|
| [engenharia-produto.md](engenharia-produto.md) | Toda mudança: issues/PRs/releases, estados da UI, observabilidade e qualidade por stack (desktop e C6 web) |
| [engenharia-produto-details.md](engenharia-produto-details.md) | Detalhe sob demanda do padrão de engenharia: seção pertinente ao tipo de mudança (entrega, UI, ferramentas, observabilidade, fila) |
| [agent-skills-adapted.md](agent-skills-adapted.md) | Aplicar baseline/ratchet, checkpoint de contexto ou observabilidade orientada a perguntas sem instalar a coleção Agent Skills |
| [propagar-workflow.md](propagar-workflow.md) | Levar o pacote do workflow (.workflow, .mex, instruções, hooks) de uma branch integrada para as outras, sem perder conteúdo do destino |
| [workflow-tres-clis.md](workflow-tres-clis.md) | Alterar skills, MCPs e hooks em Claude Code, Codex e AGY, com validação de descoberta e drift |
| [agente-noturno.md](agente-noturno.md) | Selecionar goals, conferir preflight, quota, isolamento, retomada e suspensão opcional |
| [benchmark-codegraph.md](benchmark-codegraph.md) | Comparar índices de código com corpus congelado, gabarito independente e custos medidos |
| [codegraph-fallback.md](codegraph-fallback.md) | Consultar Graphify primeiro e CBM como fallback, sem sincronização entre índices |
| [add-build-artifact.md](add-build-artifact.md) | Adding a new generated file to the output repository |
| [add-builder-submodule.md](add-builder-submodule.md) | Adding new processing logic to any `src/builder/` subpackage |
| [add-ui-feature.md](add-ui-feature.md) | Adding dialogs, tabs, dashboard widgets, or new entry controls to the Tkinter UI |
| [debug-build-failure.md](debug-build-failure.md) | Diagnosing failures during repository builds — manifest errors, conversion errors, stalls |
| [delegar-codex-agy.md](delegar-codex-agy.md) | Claude chama Codex (revisor) e agy (leitor) em modo headless; receitas e gotchas medidos |
| [atualizar-claude-mem-e-codex.md](atualizar-claude-mem-e-codex.md) | Atualizar claude-mem ou Codex a mao sem erro de porta do worker; limpar releases antigas do Codex |
| [debug-graphify-mcp.md](debug-graphify-mcp.md) | Diagnosing Graphify MCP startup, stdio, and initialize handshake failures; Alethe rewriting `.codex/config.toml` |
| [pdf-backend-integration.md#task-add-a-new-backend](pdf-backend-integration.md#task-add-a-new-backend) | Adding a new PDF conversion backend |
| [pdf-backend-integration.md#task-modify-existing-backend-behavior](pdf-backend-integration.md#task-modify-existing-backend-behavior) | Modifying Marker, Docling, Datalab, or PyMuPDF behavior |
| [ollama-vision.md#task-add-or-modify-vision-behavior](ollama-vision.md#task-add-or-modify-vision-behavior) | Adding image types, prompt changes, or heuristic classifier tweaks |
| [ollama-vision.md#task-debug-vision-failures](ollama-vision.md#task-debug-vision-failures) | Diagnosing Ollama connection failures, empty responses, or missing images in the curator |
| [gemini-code-summarization.md](gemini-code-summarization.md) | Adding a Gemini-backed batch job with hash cache (follow this for future material types: PDFs, exercises) |
| [medir-alavanca-ablacao.md](medir-alavanca-ablacao.md) | Medir alavanca do motor nas copias .ablacao (shim + snapshot + diff por entry) ANTES de codigo em src/ |
