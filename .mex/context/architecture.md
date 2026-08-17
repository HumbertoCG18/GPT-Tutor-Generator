---
name: architecture
description: APOSENTADO (2026-08-06) — estrutura do código vive no graphify; este stub só preserva os edges do MEX
last_updated: 2026-08-14
---

# Architecture — aposentado

Conteúdo removido na dieta MEX de 2026-08-06 (era inventário estrutural de junho:
componentes, contagens de arquivos, entry-points — tudo coberto melhor e sempre-fresco
pelo grafo de código).

- **Estrutura** (quem chama quem, onde símbolo vive, mapa de módulos): `graphify query
  "<pergunta>"`, `graphify path "<A>" "<B>"`, `graphify explain "<conceito>"`; visão ampla
  em `graphify-out/GRAPH_REPORT.md`.
- **Invariantes e porquês** de arquitetura: `context/decisions.md` + non-negotiables em
  `.mex/AGENTS.md` (ex.: `engine.py` é façade — lógica nova vai no subpacote correto).
- **Fluxo do produto** (import→process→curadoria→build): `README.md` do projeto.
