---
name: debug-graphify-mcp
description: Diagnose Graphify stdio startup and handshake failures in Codex
triggers:
  - "graphify MCP"
  - "MCP startup incomplete"
  - "handshaking with MCP server failed"
  - "Alethe reescreveu o config.toml"
edges:
  - target: "context/setup.md"
    condition: "when the Python environment or dependency installation is suspect"
last_updated: 2026-09-10
---

# Debug Graphify MCP

## Context

The MCP process must write only JSON-RPC messages to stdout. Use the interpreter recorded in
`graphify-out/.graphify_python` and the existing `graphify-out/graph.json`.

## Steps

1. Inspect the effective entry with `codex mcp get graphify --json`.
2. Run an MCP client probe against that exact command and call `initialize` plus `list_tools`.
3. If the entry runs `graphify <repo> --mcp`, replace it with the direct server entry point:
   `python -m graphify.serve <absolute graph.json>`.
4. Restart the Codex client so it reloads the project-scoped config.

## Gotchas

- `graphify <repo> --mcp` may enter extraction before serving, polluting stdout and failing on
  semantic-backend requirements.
- A PATH lookup may select a different Graphify installation. Pin the verified interpreter.
- O Alethe (`AppData\Local\Alethe`, app Tauri) reescreve `[mcp_servers.graphify]` no
  `.codex/config.toml` do projeto a cada lancamento do Codex, sempre como
  `graphify <cwd> --mcp`, comando que nao existe no graphify 0.9.42-0.9.57. Grava mesmo com
  os toggles de Graphify desligados (medido 2026-09-10, 11:59, 12:20, 18:44, 18:49); nao
  aparece no gerenciador de MCP dele porque e o recurso "Graphify", nao uma entrada de MCP.
  Interruptor que sobrevive: `enabled = false` em `[mcp_servers.graphify]` do
  config.toml global do Codex (pasta ~/.codex); o merge e por chave e o projeto nao apaga essa chave.
  `codex mcp list` mostra `disabled`; a skill `$graphify-windows` segue funcionando.
  Religar so quando o Alethe corrigir o comando (deveria ser `graphify-mcp <graph.json>`).

## Verify

- `initialize` reports the expected Graphify version.
- `list_tools` returns the Graphify tool set.
- `codex mcp get graphify --json` shows the pinned interpreter and absolute graph path
  (lancado pelo Alethe: mostra a forma dele e `enabled: false`; e o esperado).

## Debug

If initialization still closes, capture server stderr and verify that `mcp` imports in the pinned
interpreter before changing timeouts.

Medido em 2026-09-10: `mcp` 2.1.1 importa `pywintypes` no Windows e morre sem responder ao
`initialize` quando `pywin32` falta. `python -m pip check` acusa; `pip install pywin32` resolve.

## Update Scaffold

- [ ] Update setup context only when the supported installation contract changes.
- [ ] Record unresolved follow-up work in `docs/reports/pendencias.md`.
