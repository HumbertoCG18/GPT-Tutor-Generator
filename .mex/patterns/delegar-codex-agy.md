---
name: delegar-codex-agy
description: Como o Claude Code chama Codex (revisor) e Antigravity/agy (leitor) em modo headless, sem abrir chat neles. Medido em 2026-09-10.
triggers:
  - "segunda opiniao"
  - "revisor B"
  - "ler o corpus com o Gemini"
  - "codex exec"
  - "agy -p"
last_updated: 2026-09-10
---

# Delegar ao Codex e ao agy

## Context

Uma fase, um dono: Claude Code escreve; Codex (ChatGPT Plus) revisa diff; agy (Google AI Pro)
le corpus grande. Os dois rodam como subprocesso do `Bash`, em background quando for paralelo.
Nenhum deles escreve no repo.

## Steps

1. Revisor (Codex, `gpt-5.6-terra`/medium por padrao no config.toml global do Codex (pasta ~/.codex)):
   `codex exec --sandbox read-only --skip-git-repo-check -C "<repo>" - < prompt.md`
   ou `codex review --uncommitted` / `--base main` (nativo, resolve o diff sozinho).
   Terceiro voto caro, so quando Claude e revisor discordarem: `--profile astra`
   (arquivo astra.config.toml na pasta ~/.codex, gpt-6-astra/high).
2. Leitor (agy, Gemini 3.8 Flash):
   - conteudo pequeno: pergunta + texto pelo stdin, sem `-p`:
     `{ echo "<pergunta>"; cat arquivo; } | agy --model gemini-3.8-flash-low --output-format json`
   - corpus: `agy -p "<pergunta com caminho ABSOLUTO>" --add-dir "<abs>/docs" --model gemini-3.8-flash-medium --output-format json`
   Resposta em `.response`; tokens em `.usage.total_tokens`.
3. Revisao dupla pronta: `ecc:santa-loop` (Claude + Codex, `--sandbox read-only`).

## Gotchas

- agy em print mode nao tem workspace (default: pasta antigravity-cli/scratch dentro de ~/.gemini): caminho relativo
  faz o modelo varrer `C:\` com `pwsh`, que e negado. Sempre absoluto, no prompt e no `--add-dir`.
- `-p` e stdin sao exclusivos: com `-p "<texto>"` o stdin e ignorado; `--print` sem valor quebra o parse.
- O settings.json do agy (pasta ~/.gemini) tem `permissions.allow: ["read_file(*)"]`; a leitura usa `view_file`
  nativo. Nao liberar `command(pwsh)`.
- Cada chamada do agy custa ~20k tokens de contexto fixo (skills + system prompt) antes do conteudo.
- `codex exec` trava sem saida quando a cota do Codex acabou; foi assim com `gpt-6-astra`/high.
- `santa-loop` pedia `-m gpt-5.4` (fora do catalogo); trocado na copia de cache do ECC; update desfaz.

## Verify

- `codex exec ... "responda ok"` devolve `ok` e a linha `tokens used`.
- agy devolve `status: SUCCESS`, `denied_actions: []` e `response` nao vazio.
