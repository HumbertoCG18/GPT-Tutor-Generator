---
name: debug-graphify-mcp
description: Diagnose Graphify stdio startup and handshake failures in Codex
triggers:
  - "graphify MCP"
  - "MCP startup incomplete"
  - "handshaking with MCP server failed"
edges:
  - target: "context/setup.md"
    condition: "when the Python environment or dependency installation is suspect"
last_updated: 2026-09-04
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

## Verify

- `initialize` reports the expected Graphify version.
- `list_tools` returns the Graphify tool set.
- `codex mcp get graphify --json` shows the pinned interpreter and absolute graph path.

## Debug

If initialization still closes, capture server stderr and verify that `mcp` imports in the pinned
interpreter before changing timeouts.

## Update Scaffold

- [ ] Update setup context only when the supported installation contract changes.
- [ ] Record unresolved follow-up work in `docs/reports/pendencias.md`.
