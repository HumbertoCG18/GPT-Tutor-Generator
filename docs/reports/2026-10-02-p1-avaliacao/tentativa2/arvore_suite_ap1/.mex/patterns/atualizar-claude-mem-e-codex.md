---
name: atualizar-claude-mem-e-codex
description: Atualizacao manual do claude-mem (Claude + Codex) e do Codex CLI sem o erro de porta do worker; auto-update do claude-mem desligado de proposito. Medido em 2026-09-13/14.
triggers:
  - "atualizar claude-mem"
  - "worker do claude-mem"
  - "stale worker port"
  - "atualizar o codex"
  - "codex update"
last_updated: 2026-09-14
---

# Atualizar claude-mem e Codex

## Context

O marketplace thedotmack (claude-mem) roda com autoUpdate desligado desde 2026-09-13
(known_marketplaces.json na pasta ~/.claude/plugins). Motivo medido: 10 versoes instaladas em
~20h (13.24.6 em 10/09 21:29 ate 13.24.23 em 11/09 16:57); o erro "Stale worker port still open
after SIGKILL" apareceu so nesses dias (38 em 10/09, 23 em 11/09) e zerou sem troca de versao
(0 em 12 e 13/09). Correlacao, nao reproduzida.

Um worker unico (porta 38790) atende Claude e Codex. O Codex usa o marketplace local
claude-mem-local, que le a pasta do marketplace do Claude, mas materializa a copia SEM
node_modules: os hooks do plugin morrem com "Cannot find module 'zod/v3'" e o Codex para de gravar
sessoes (medido em 2026-09-14: 0 sessoes Codex de 13/09 16:03 ate a correcao; a 13.24.23 apareceu
no cache do Codex em 13/09 23:16 sem reinstall manual). `scripts/hooks/repor-podas.py` liga uma
junction node_modules para o cache do Claude da mesma versao a cada SessionStart.

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
5. Codex: nao reinstalar. Abrir uma sessao do Claude ou do Codex para o repor-podas religar
   node_modules e podar as skills; reaprovar em /hooks se o Codex pedir. Requisito: a mesma versao
   precisa existir no cache do Claude (passo 2 antes), senao o script imprime "deps FALTA".
6. agy: nao mexer. Usa so a skill mem-search, e `agy plugin import` reimporta o ECC inteiro.

Codex CLI:
1. `codex update`. Nao apaga as releases antigas: ficam na pasta
   ~/.codex/packages/standalone/releases, e a junction current aponta para a em uso. Apagar as
   outras a mao (em 2026-09-13 eram 7 versoes, ~2,3 GB).
2. `codex plugin marketplace upgrade` para ECC e ponytail (marketplaces Git). O claude-mem-local
   nao entra: marketplace local.
3. Reaprovar em /hooks depois de qualquer update de plugin (o hash dos hooks muda).

## Gotchas

- Desde 17/09, as configs global e deste projeto também usam seletores nativos
  `[[skills.config]] name = "ecc:<nome>"`, `enabled = false`, derivados de
  `skillOverrides`. Incluem aliases `ecc:source-command-<nome>` dos comandos.
  Esses seletores sobrevivem à troca do caminho versionado do plugin e filtram
  antes da poda SessionStart. Não aumentar orçamento para carregar o ECC inteiro.
  Rodar `python verify.py` no agent-workflow-lab: compara a seleção por nome com
  Claude e preserva exceções explícitas do projeto. Mudou a seleção, sincronizar
  as configs global/projeto; arrays de projeto substituem os globais.
  Outros worktrees/projetos com config própria precisam da mesma sincronização.
- Sessão retomada pode conservar catálogo anterior: a sessão importada examinada
  em 17/09 tinha 314 entradas sem descrições, enquanto CLI/app-server novos
  listavam 26 habilitadas. Não editar o JSONL ativo. Para eliminar a lista já
  injetada, iniciar sessão nova com handoff; retomar a antiga não prova recarga.
- Update do ECC recopia tudo e desfaz a poda. `scripts/hooks/repor-podas.py` com --aplicar refaz
  a partir do skillOverrides do Claude; roda no SessionStart do Claude e do Codex (no Codex, so
  depois de aprovado em /hooks).
- `claude plugin marketplace update` nao religa o autoUpdate (conferido em 2026-09-13).
- O clone do marketplace thedotmack e raso (rev-parse --is-shallow-repository = true): git log nao
  mostra a cadencia de versoes. Usar a data de criacao das pastas de versao no cache.
- "NOT NULL constraint failed: session_summaries.memory_session_id" (11/09) e bug do gerador de
  sumario, nao do worker.
- O Codex converte commands em skills na pasta .codex-plugin/migrated-command-skills do cache do
  plugin. O repor-podas poda ali tambem, mas nao repoe: command promovido depois so volta
  reinstalando o plugin no Codex.
- Orcamento do catalogo de skills no Codex: skills.max_context_tokens, padrao 2% da janela (272k no
  gpt-5.6-terra, ~5,4k tok), teto 10000. Acima disso o Codex encurta descricoes e avisa "Skill
  descriptions were shortened". Em 2026-09-14: 115 skills com descricoes cortadas, 59 inteiras
  depois da poda.
- Falha de hook no Codex so aparece como "hook: EVENTO Failed" no stderr, sem mensagem. Reproduzir
  rodando o commandWindows do codex-hooks.json do plugin com PLUGIN_ROOT apontando para o cache do
  Codex.
- `codex exec` chamado de shell sem TTY espera stdin ("Reading additional input from stdin...") ate
  o timeout; fechar com < /dev/null.

## Verify

- bun worker-service.cjs status (script da versao nova) mostra a Version nova e o PID.
- Log do dia na pasta ~/.claude-mem/logs sem "Stale worker port" nem "Worker not available".
- `codex --version` responde e `codex plugin list` mostra ecc@ecc installed, enabled.
- `python scripts/hooks/repor-podas.py` (simulacao) com remove 0 e repoe 0 nos tres alvos
  (codex/ecc, agy/ecc, codex/claude-mem) e sem linha deps.
- `codex exec --sandbox read-only --skip-git-repo-check -C . "responda apenas: ok" < /dev/null`:
  stderr so com "hook: ... Completed", nenhum Failed, e sdk_sessions ganha linha com
  platform_source=codex.
