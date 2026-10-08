# Piloto dos hooks do Context Mode — issue #19

**Decisão:** não ativar o conjunto completo de hooks em Claude Code, Codex ou AGY.

O MCP isolado da #18 continua aprovado. Este resultado limita apenas os hooks da versão
`1.0.169`, commit upstream `c127f2fe8496fefc36e0ebef36ded92d4fa8f570`.

## Método

- Entry points reais executados com Node 24.13.0 em homes, storage, temporários e projetos isolados.
- Versões locais: Claude Code 2.1.276, Codex CLI 0.154.0 e AGY 1.2.5.
- Eventos: seis em Claude/Codex; três em AGY. Quinze subprocessos `PreToolUse` por plataforma para p50/p95.
- Fixture de segredo com formato de chave sintética em prompt, resposta final, saída de ferramenta e arquivos de instrução.
- Hashes de seis configs reais antes/depois; nenhum hook ou MCP registrado globalmente.
- Volume observado = bytes agregados de stdout, incluindo envelopes que o host pode não inserir no contexto. `ceil(bytes/3)` é só estimativa heurística, sem garantia de teto ou equivalência a tokens faturados.

## Resultado por CLI

| CLI | Suporte exercitado | Latência `PreToolUse` p50/p95 | Stdout agregado | Sobreposição declarada | Resultado |
|---|---:|---:|---:|---|---|
| Claude Code | 6/6 eventos, exit 0 | 68,269 / 89,439 ms | 5.575 bytes; heurística 1.859 tokens | `PreToolUse` do RTK + `SessionStart` do reparo de podas | Rejeitar |
| Codex | 6/6 eventos, exit 0 | 88,598 / 101,294 ms | 5.073 bytes; heurística 1.691 tokens | `PreToolUse` do Graphify + `SessionStart` do reparo de podas | Rejeitar |
| AGY | 3/3 eventos, exit 0 | 87,240 / 99,281 ms | 655 bytes; heurística 219 tokens | ECC e claude-mem importados; payload parcialmente empírico | Rejeitar |

`pytest -q` recebeu orientação para `ctx_execute` em Claude/Codex e foi negado no AGY. Isso altera o caminho aprovado `rtk pytest` e impede ativação do matcher upstream sem adaptação.

## Checks

| Check | Resultado |
|---|---|
| Upstream fixado | passou |
| Eventos normais encerram com exit 0 | passou |
| Configs globais inalteradas | passou |
| Segredo ausente das respostas dos hooks | passou |
| Segredo ausente da persistência | **falhou** |
| Nenhuma duplicata pela chave `sessão+tipo+categoria+dados` | passou |
| Nenhum stderr | **falhou** |
| Entrada malformada falha aberta | **falhou** |
| Timeout de 1 ms imposto pelo harness | passou |
| Backup/restauração sintética byte a byte | passou |

Total: **7/10**.

## Bloqueios medidos

1. Claude e Codex persistiram o segredo sintético no banco de sessão. As origens foram `UserPromptSubmit`, `Stop` e captura de regras do projeto (`SessionStart` no Claude; `PostToolUse` no Codex). AGY não persistiu o segredo nesta fixture.
2. Node emitiu `ExperimentalWarning` de SQLite no stderr: cinco eventos de Claude, cinco de Codex e dois de AGY. O conteúdo do segredo não apareceu no aviso, mas stderr pode ser tratado como falha pelo host.
3. `PreToolUse` do Codex recebeu JSON malformado e encerrou com exit 1 + stack trace. Claude e AGY falharam abertos no mesmo caso.
4. O matcher upstream intercepta `pytest`. No AGY, a decisão foi `deny`; em Claude/Codex houve contexto adicional orientando outro executor.

## Evidência complementar

- Vitest local correto: **127 passed, 2 skipped**, cinco arquivos de hooks. A tentativa inicial com `bun test` foi inválida: Bun não suporta `better-sqlite3` nesse runner e não implementou `vi.importActual`; seus sete failures não foram tratados como defeitos do produto.
- `agy plugin validate` passou no bundle `configs/antigravity-cli`: uma skill, um MCP e um conjunto de hooks processados.
- Smoke de `context-mode upgrade` em homes isolados: Codex e AGY geraram somente configs isoladas; Claude falhou em home vazio porque não criou o diretório pai de `settings.json`. O comando também clona o GitHub, portanto não serve como instalador offline determinístico.
- Nenhum grupo duplicado foi encontrado pela chave consultada. Hooks existentes não foram executados junto com Context Mode; coexistência e duplicidade entre gestores permanecem não avaliadas. O timeout comprova apenas imposição pelo harness, sem provar limpeza de descendentes ou continuidade do host. O procedimento sintético restaurou cópias das seis configs byte a byte; rollback operacional do produto permanece não avaliado.

## Condição para repetir

Reavaliar somente após: redigir/filtrar prompt, resposta final e regras antes da persistência; eliminar stderr no Node suportado; fazer o dispatcher Codex falhar aberto em JSON inválido; permitir matcher que exclua `pytest` e preserve RTK/Graphify. A nova rodada deve usar a mesma fixture e comparar os mesmos dez checks.
