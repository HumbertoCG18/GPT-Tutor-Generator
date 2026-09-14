---
name: atualizar-claude-mem-e-codex
description: Atualizacao manual do claude-mem (Claude + Codex) e do Codex CLI sem o erro de porta do worker; auto-update do claude-mem desligado de proposito. Medido em 2026-09-13.
triggers:
  - "atualizar claude-mem"
  - "worker do claude-mem"
  - "stale worker port"
  - "atualizar o codex"
  - "codex update"
last_updated: 2026-09-13
---

# Atualizar claude-mem e Codex

## Context

O marketplace thedotmack (claude-mem) roda com autoUpdate desligado desde 2026-09-13
(known_marketplaces.json na pasta ~/.claude/plugins). Motivo medido: 10 versoes instaladas em
~20h (13.24.6 em 10/09 21:29 ate 13.24.23 em 11/09 16:57); o erro "Stale worker port still open
after SIGKILL" apareceu so nesses dias (38 em 10/09, 23 em 11/09) e zerou sem troca de versao
(0 em 12 e 13/09). Correlacao, nao reproduzida.

Um worker unico (porta 38790) atende Claude e Codex. O Codex usa o marketplace local
claude-mem-local, que le a pasta do marketplace do Claude; roda 13.24.7 e grava sessoes
normalmente (sdk_sessions com platform_source=codex todo dia de 10 a 13/09).

## Steps

Criterio: so atualizar quando a versao nova estiver parada ha 1-2 dias. Tudo em terminal comum,
com TODAS as sessoes do Claude e do Codex fechadas: hook de sessao aberta sobe o worker velho de
novo (log "Worker not running — lazy-spawning").

claude-mem:
1. `claude plugin marketplace update thedotmack` e comparar a versao do catalogo com a instalada
   (installed_plugins.json na pasta ~/.claude/plugins).
2. `claude plugin update claude-mem@thedotmack` (so copia a versao nova para o cache).
3. Parar o worker da versao EM EXECUCAO (a antiga): bun worker-service.cjs stop, com o script da
   pasta ~/.claude/plugins/cache/thedotmack/claude-mem/VERSAO_ANTIGA/scripts.
4. Abrir o Claude Code: o hook sobe o worker novo.
5. Codex, so se ele parar de gravar sessoes: `codex plugin remove claude-mem@claude-mem-local`,
   `codex plugin add claude-mem@claude-mem-local` e reaprovar em /hooks.
6. agy: nao mexer. Usa so a skill mem-search, e `agy plugin import` reimporta o ECC inteiro.

Codex CLI:
1. `codex update`. Nao apaga as releases antigas: ficam na pasta
   ~/.codex/packages/standalone/releases, e a junction current aponta para a em uso. Apagar as
   outras a mao (em 2026-09-13 eram 7 versoes, ~2,3 GB).
2. `codex plugin marketplace upgrade` para ECC e ponytail (marketplaces Git). O claude-mem-local
   nao entra: marketplace local.
3. Reaprovar em /hooks depois de qualquer update de plugin (o hash dos hooks muda).

## Gotchas

- Update do ECC recopia tudo e desfaz a poda. `scripts/hooks/repor-podas.py` com --aplicar refaz
  a partir do skillOverrides do Claude; roda no SessionStart do Claude e do Codex (no Codex, so
  depois de aprovado em /hooks).
- `claude plugin marketplace update` nao religa o autoUpdate (conferido em 2026-09-13).
- O clone do marketplace thedotmack e raso (rev-parse --is-shallow-repository = true): git log nao
  mostra a cadencia de versoes. Usar a data de criacao das pastas de versao no cache.
- "NOT NULL constraint failed: session_summaries.memory_session_id" (11/09) e bug do gerador de
  sumario, nao do worker.

## Verify

- bun worker-service.cjs status (script da versao nova) mostra a Version nova e o PID.
- Log do dia na pasta ~/.claude-mem/logs sem "Stale worker port" nem "Worker not available".
- `codex --version` responde e `codex plugin list` mostra ecc@ecc installed, enabled.
- `python scripts/hooks/repor-podas.py` (simulacao) com remove 0 e repoe 0 nos dois alvos.
