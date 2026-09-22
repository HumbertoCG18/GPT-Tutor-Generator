# Organizacao do workflow — piloto de versionamento

Refs #44: https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/44

## Escopo e isolamento

Gate 1 autorizado em 22/09/2026. Entrega parcial: tornar versionaveis os recursos compartilhados das CLIs e registrar consumidores. Sem mover/remover arquivos, alterar src/, executar hooks ou iniciar agentes. Branch chore/44-workflow-layout-pilot, base 410592d. Gate 2 pendente.

O inventario descreve o checkout principal observado em 22/09, incluindo alteracoes ainda nao commitadas. O worktree do piloto parte do commit: nao representa as configuracoes ativas nao commitadas da raiz. Nenhuma configuracao antiga desta branch foi executada ou copiada de volta.

## Donos e consumidores atuais

| Caminho | Dono/consumidor | Tratamento neste lote |
|---|---|---|
| AGENTS.md, CLAUDE.md, GEMINI.md | Entradas de instrucoes das CLIs | Preservados; detalhes comuns continuam nas fontes existentes |
| .workflow/ | Snapshot do agent-workflow-lab, manifest e referencias | Preservado; nao criar segunda fonte nem redistribuir snapshot antigo |
| .mex/ | Identidade, mapa e convencoes do produto | Preservado |
| .workflow-local/ | Estado e Gates de cada worktree | Estado proprio neste worktree; motor intocado |
| .claude/settings.json | Claude: PreToolUse e plugins | Permitir versionamento; bytes ativos preservados |
| .claude/settings.local.json | Permissoes e MCP pessoais | Continuar ignorado |
| .claude/skills, rules, agents | Recursos de projeto descobertos pelo Claude | Permitir versionamento; nao criar pastas vazias |
| .codex/config.toml | Codex; 476 entradas de skills, 7 habilitadas no inventario; MCP e hooks | Preservar; nao remover bloqueios nem alterar precedencia |
| .agents/skills e .agents/rules | Descoberta de skills Codex e regras AGY conforme versao | Permitir versionamento, sem instalar conteudo |
| .agents/hooks.json | Registro atual dos guardas para AGY | Excecao existente preservada; carregamento nao retestado |
| scripts/hooks/engine-facade-guard.js | Referenciado por Claude, Codex e adaptador AGY | Implementacao unica preservada |
| scripts/hooks/gemini-antipattern-guard.js | Referenciado pelas tres CLIs; possui caminho proprio na lista de isencoes | Preservado; mover exige atualizar todos os consumidores |
| scripts/hooks/agy-adapter.js | Registro .agents/hooks.json | Preservado; cwd efetivo requer teste antes de migrar |
| scripts/hooks/repor-podas.py | Manutencao de plugins compartilhados; documentado em .mex/patterns/atualizar-claude-mem-e-codex.md | Preservado; opera configuracao pessoal, nao e motivo para copiar plugins ao projeto |
| .alethe/worktrees/ | Alethe e Git, 10 worktrees registradas no inventario | Preservadas inclusive regras de ignore, conforme decisao anterior |
| .claude/workflows/auditoria-enxame.js | Launcher legado com raiz absoluta e contexto antigo | Continua local/ignorado; consumidor e uso precisam ser confirmados |

## Material para lotes posteriores

- plans/: 6 arquivos. ROADMAP.md ainda referencia code-summarization-gemini.md e material-agnostic-refactor.md. Checkboxes e estados discordam; verificar tracker/aceites antes de mover para Feitos/.
- docs/superpowers/plans/: 13 arquivos no topo e 54 em Feitos/. specs/: 9 no topo e 46 em Feitos/. Preservar links; eventual mudanca de nome em lote proprio.
- .superpowers/: 260 arquivos, 5.286.480 bytes no inventario, 7 rastreados. Separar provas SDD de estado operacional de brainstorm; nao apagar em bloco.
- .claude/: 3 backups locais; .claude/skills e .claude/worktrees vazias no inventario. Nenhuma pasta artificial criada.
- %SystemDrive%/: 4 arquivos de cache Windows; origem ainda nao confirmada. Relatorio com caminho malformado na raiz tambem exige triagem.
- .worktrees/auditoria-enxame-codex-skill e demais worktrees externas: verificar dono, mudancas e integracao antes de qualquer movimento/remocao.
- .codex/hooks.json esta excluido no checkout principal por outra frente; este piloto nao restaura nem incorpora essa exclusao.

Nao criar .agy/: a documentacao atual usa .agents/; validar compatibilidade da versao instalada antes de mudar recursos AGY. Skills pessoais continuam na fonte do laboratorio e nos destinos administrados, sem duplicacao por projeto. Remocao de capacidade exige medicao de invocacoes reais; este inventario nao constitui essa medicao.

## Mudanca e aceite

O ignore generico de .claude/ e .agents/ escondia novos recursos compartilhados. Foram adicionadas excecoes estreitas para os caminhos nativos, preservando settings.local.json, backups, worktrees e workflows legados. Nenhuma mudanca no catalogo, MCP, permissao ou execucao de hooks.

Validar com git check-ignore --no-index sobre caminhos sinteticos (sem criar skills), git diff --check e hashes dos arquivos ativos. Confirmar que .alethe continua com o mesmo resultado de ignore. A verificacao de descoberta em sessoes novas fica para quando houver conteudo realmente migrado.

Rollback: reverter somente o bloco adicionado em .gitignore; este relatorio pode permanecer como evidencia. Nao restaurar configuracoes nem estados a partir deste worktree.

## Fontes consultadas em 22/09/2026

- Claude settings: https://code.claude.com/docs/en/settings
- Claude skills/rules/agents: https://code.claude.com/docs/en/skills ; https://code.claude.com/docs/en/memory ; https://code.claude.com/docs/en/sub-agents
- Codex: https://learn.chatgpt.com/docs/build-skills ; https://learn.chatgpt.com/docs/config-file/config-basic
- AGY: https://www.antigravity.google/docs/rules-workflows/
- Git worktrees: https://git-scm.com/docs/git-worktree

## Resultado medido

- 23 verificacoes de ignore passaram (recursos compartilhados visiveis; estado pessoal e backups ignorados).
- git diff --check: passou.
- 145 arquivos da raiz conferidos por SHA256, incluindo src/ (exceto __pycache__), configuracoes ativas, scripts/hooks/, estado do motor e .gitignore: nenhum alterado entre baseline e verificacao.
- src/ e scripts/hooks/ do worktree: zero diff.
- Nenhuma migracao de pasta, commit, push, worker ou revisao Astra executados.
