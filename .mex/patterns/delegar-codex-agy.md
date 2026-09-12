---
name: delegar-codex-agy
description: Como o Claude Code chama Codex (revisor) e Antigravity/agy (leitor) em modo headless, sem abrir chat neles. Medido em 2026-09-10.
triggers:
  - "segunda opiniao"
  - "revisor B"
  - "ler o corpus com o Gemini"
  - "codex exec"
  - "agy -p"
last_updated: 2026-09-11
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
   Terceiro voto caro (Astra): so a pedido explicito do user, nunca por decisao do agente:
   `--profile astra`
   (arquivo astra.config.toml na pasta ~/.codex, gpt-6-astra/high, `tool_output_token_limit = 4000`).
   O astra julga, nao explora: recebe no brief a tabela pronta de um script reproduzivel
   (p.ex. `docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py`) e responde em 2 ou 3 turnos. Replay e experimento
   rodam sem LLM, a custo zero de cota.
   Regras do brief, para qualquer perfil (custo da cota = contexto x turnos, ver Gotchas):
   - Trecho, nao arquivo: `rg -n`, `sed -n a,b`, `tail`. Arquivo inteiro so se couber em ~200
     linhas. Cada byte lido volta ao modelo em todos os turnos seguintes.
   - Leituras agrupadas: varios trechos num comando so. Trocar arquivo inteiro por cinco `sed`
     em cinco turnos nao economiza; cada turno reenvia o contexto todo.
   - Brief autocontido: `git diff`, logs relevantes e o mapa do graphify vao dentro do brief.
     O astra de 2026-09-11 gastou os 3 primeiros turnos lendo isso sozinho.
   - Dado que decide vai bruto: o astra achou o erro do SO porque viu os conjuntos, nao a soma.
2. Leitor (agy, Gemini 3.8 Flash):
   - conteudo pequeno: pergunta + texto pelo stdin, sem `-p`:
     `{ echo "<pergunta>"; cat arquivo; } | agy --model gemini-3.8-flash-low --output-format json`
   - corpus: `agy -p "<pergunta com caminho ABSOLUTO>" --add-dir "<abs>/docs" --model gemini-3.8-flash-medium --output-format json`
   Resposta em `.response`; tokens em `.usage.total_tokens`.
   - com escolha automatica de modelo pela cota: `pwsh scripts/agy-cota.ps1 <mesmos args>`;
     `-SoEscolher` so imprime o modelo. Cadeia e limiar (`AGY_COTA_MINIMO`, padrao 0.10) no topo.
   Papel do agy na delegacao: mapa (onde esta o que, arquivo:linha) e digestao de log grande em
   tabela por item. Nao resume o dado que decide; esse vai bruto, por trecho, para o Codex.
3. Revisao dupla pronta: `ecc:santa-loop` (Claude + Codex, `--sandbox read-only`).

## Gotchas

- agy em print mode nao tem workspace (default: pasta antigravity-cli/scratch dentro de ~/.gemini): caminho relativo
  faz o modelo varrer `C:\` com `pwsh`, que e negado. Sempre absoluto, no prompt e no `--add-dir`.
- `-p` e stdin sao exclusivos: com `-p "<texto>"` o stdin e ignorado; `--print` sem valor quebra o parse.
- O settings.json do agy (pasta ~/.gemini) tem `permissions.allow: ["read_file(*)"]`; a leitura usa `view_file`
  nativo. Nao liberar `command(pwsh)`.
- Cada chamada do agy custa ~20k tokens de contexto fixo (skills + system prompt) antes do conteudo.
- A cota do agy e por grupo, nao por modelo (`/quota`, 11/09): Gemini (Flash 3.6-3.8 + Pro 3.1)
  e "Claude and GPT" (Opus, Sonnet, GPT-OSS) tem cada um sua janela de 5h e semanal, consumidas
  em proporcao ao custo do token. Trocar Flash por Pro nao traz cota e esvazia o balde mais
  rapido; trocar de grupo traz. Nao ha fallback nativo; o retry por rate limit e no mesmo modelo.
- `agy -p "/quota"` (tambem `/usage`, `/credits`, `/model`, `/help`) responde em print mode sem
  turno e com 0 tokens, em JSON com `command.data.groups[].buckets[]` (`remaining_fraction`,
  `reset_time`). So via PowerShell: pelo Bash tool o MSYS antepoe a pasta do Git ao `/quota`
  (o agy recebe "C:/Program Files/Git/quota", promptLength=26 no cli.log) e vira um turno de
  modelo. Medido em
  11/09: 4 tentativas, ~72k tokens. No bash, `MSYS_NO_PATHCONV=1` evita a conversao.
- `codex exec` trava sem saida quando a cota do Codex acabou; foi assim com `gpt-6-astra`/high.
- A cota do ChatGPT pesa o contexto em cache, nao so o input novo: no rollout do astra de
  2026-09-11, turnos com 400 tokens novos custaram 1 ponto e, acima de 120k de contexto, 2 pontos
  cada. Custo = contexto x turnos. Aquela sessao: 39 turnos, contexto de 27k a 165k, 4,7M tokens
  reenviados (96% cache), 68 pontos da janela de 5h (2% -> 70%) e 10 da semanal. Cada `codex exec`
  do terra com 2 turnos: 1 ponto.
- Saida de ferramenta entra no contexto com ate 10k tokens por chamada (`truncation_policy` no
  catalogo, `codex debug models`, sem gastar cota). `tool_output_token_limit` no config ou em
  `-c tool_output_token_limit=N` sobrescreve; medido com N=500: o modelo viu 2348 chars e o
  marcador `…4413 tokens truncated…`. Nao existe limite por bytes.
- `model_auto_compact_token_limit` existe no binario 0.154; efeito na cota nao medido. So se o
  resto nao bastar.
- `santa-loop` pedia `-m gpt-5.4` (fora do catalogo); trocado na copia de cache do ECC; update desfaz.

## Verify

Rastro fora do transcript do Claude, para o user conferir que a chamada aconteceu:
- Codex: cada `codex exec` cria `~/.codex/sessions/<AAAA/MM/DD>/rollout-*.jsonl` com
  `"originator":"codex_exec"` e `"model":"..."`; `codex resume` lista essas sessoes.
- agy: cada `agy -p` cria `~/.gemini/antigravity-cli/conversations/<conversation_id>.db`;
  `agy --conversation <id>` reabre a conversa inteira.
- Ao delegar, o Claude cita na resposta o nome do rollout ou o `conversation_id`.

- `codex exec ... "responda ok"` devolve `ok` e a linha `tokens used`.
- Cota gasta por sessao: no rollout, cada evento `token_count` traz `rate_limits.primary`
  (janela de 5h) e `.secondary` (semanal) com `used_percent`; a diferenca entre o primeiro e o
  ultimo evento e o custo da sessao. `last_token_usage.input_tokens` e o contexto do turno.
- agy devolve `status: SUCCESS`, `denied_actions: []` e `response` nao vazio.
