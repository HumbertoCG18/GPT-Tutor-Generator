# Auditoria de uso de capacidades nas três CLIs

Issue: [#23](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/23)
Data da medição: 2026-09-18
Escopo: Claude Code, Codex e AGY; leitura de configuração e transcripts; nenhuma configuração alterada.

## Resultado executivo

Não há base para uma remoção em massa. A auditoria separou chamadas estruturadas de menções textuais e encontrou quatro grupos:

| Decisão | Capacidades | Evidência |
|---|---|---|
| Manter | Context7, claude-mem, CBM como fallback, Graphify como skill/CLI, ECC e Ponytail | uso observado ou papel explícito no workflow |
| Pilotar desativação | Perssua MCP, Chrome DevTools MCP, GitHub MCP externo, Graphify MCP em Claude/AGY | uso ausente ou alternativa já disponível; ainda exige jornada fixa e rollback |
| Deduplicar em piloto | cópias de `heredoc-git-bash-windows` e `mex-check-falso-positivo` | dois pares byte a byte idênticos aparecem duas vezes no catálogo ativo do Codex |
| Não decidir por falta de telemetria | MCPs aninhados no `functions.exec` do Codex e ativação de skills no AGY | o transcript registra o invólucro, não prova toda chamada interna/ativação |

Próxima instalação continua bloqueada até existir gap concreto, candidato auditado, piloto isolado, issue própria e Gates 1/2. `find-skills` permanece instalado e desativado por padrão.

## Método e cobertura

O script [`audit_usage.py`](_capability-usage-audit/audit_usage.py) lê apenas os campos estruturados de chamadas. Texto de prompts, definições de ferramentas e nomes encontrados em documentação não contam como uso. Os argumentos servem somente para reconhecer leitura de `SKILL.md`, invocação `gh` e a ferramenta filha do invólucro; nenhum argumento ou segredo entra no resultado.

| Fonte | Arquivos | Linhas JSON válidas | Inválidas | Intervalo | Chamadas estruturadas |
|---|---:|---:|---:|---|---:|
| Claude Code | 1.000 | 145.009 | 0 | 2026-08-11 a 2026-09-18 | 14.045 |
| Codex atual | 243 | 42.111 | 0 | 2026-05-04 a 2026-09-18 | 3.675 |
| Codex arquivado | 80 | 364.542 | 0 | 2026-03-25 a 2026-06-22 | 63.454 |
| AGY, somente `transcript_full.jsonl` canônico | 91 | 1.004 | 0 | 2026-09-10 a 2026-09-16 | 276 |

Validação positiva do parser: Claude registrou `Bash=10.418`, `Read=922`, `Write=862`; Codex atual registrou `exec=2.822`; AGY registrou `view_file=98` e `run_command=61`. O autoteste também prova que uma definição textual de ferramenta não vira chamada, que `Write`/`echo` não viram leitura de skill e que comandos `gh` isolados ou compostos são reconhecidos.

Limites:

- `gh_command_matches` reconhece comandos em argumentos de shell; é evidência operacional, não uma API de telemetria do `gh`.
- O Codex atual registra `functions.exec` como chamada de topo. Nomes `tools.*` dentro do JavaScript são referências aninhadas e ficam fora da contagem de chamadas.
- O AGY não expõe de forma uniforme a ativação de skills; zero nesse campo não significa desuso.
- Ausência de chamada no intervalo não prova ausência de necessidade futura. Cada desativação precisa de piloto da jornada que a capacidade deveria cobrir.

## MCPs e alternativas

| Capacidade | Claude | Codex | AGY | Decisão |
|---|---:|---:|---:|---|
| Context7 | 4 | não observável no invólucro atual | 9 | manter |
| claude-mem | 34 | skill ativa; MCP interno não observável neste formato | 1 | manter |
| Codebase Memory | 0 | não observável no invólucro atual | 1 | manter como fallback de baixa frequência |
| GitHub MCP externo | 1 | 0 direto; conector GitHub arquivado 2 | 0 | pilotar contra `gh` e conector nativo |
| Chrome DevTools MCP | 0 | 0 direto | 0 | pilotar contra navegador nativo/Playwright na mesma jornada |
| Graphify MCP | 0 | já desativado | 0 | preservar skill/CLI; pilotar retirada só das entradas MCP de Claude/AGY |
| Perssua MCP | 0 | 0 direto | 0 | primeiro candidato de desativação, após smoke test de identidade e rollback |
| Node REPL MCP | não configurado | habilitado; uso interno não separável | não configurado | manter; lacuna de observabilidade |

O Graphify não está sem uso: foram observadas 2 leituras de skill no Claude e 31 no Codex atual. O dado sustenta consolidar a interface, não remover a capacidade.

GitHub também não está sem uso: houve 117 correspondências de comandos `gh` no Claude, 82 no Codex atual e 1 no Codex arquivado. O piloto deve comparar a mesma tarefa com `gh`, MCP externo e conector nativo, medindo sucesso, chamadas, tempo, bytes de transcript e permissões. Só então uma interface pode virar dona.

`perssua` foi identificado como o pacote `@perssua/mcp`; nenhum dos transcripts medidos contém chamada estruturada ao servidor. Isso o torna o candidato mais forte, mas ainda falta provar que nenhum hook ou fluxo externo depende dele.

## Skills e plugins

O catálogo vivo do Codex contém 77 skills: 26 ativas, 51 desativadas e 8.146 caracteres de descrição ativa. A lista `skills.config` possui 478 overrides desativados; ela não representa o catálogo efetivo. `find-skills` está desativada no catálogo vivo, como definido pela política.

Uso observado confirma os donos principais: Graphify teve 31 leituras no Codex atual e 2 no Claude; `troglodita`, 11 e 1; `medir-uso-antes-de-remover`, 2 no Codex; `eval-harness`, 9; Ponytail, 9. No Claude, a ferramenta `Skill` invocou `claude-mem:mem-search` 8 vezes e `ecc:orch-fix-defect` 2 vezes.

Dois pares ativos no Codex são redundância comprovada:

- `~/.agents/skills/heredoc-git-bash-windows/SKILL.md` e a cópia em `skills/learned/`: SHA-256 `A07998B1...BD147` em ambas.
- `~/.agents/skills/mex-check-falso-positivo/SKILL.md` e a cópia em `skills/learned/`: SHA-256 `D74CA338...0728F` em ambas.

A deduplicação deve manter o path canônico usado pelo laboratório, executar `verify.py`, abrir sessão nova nas três CLIs e comprovar que nome, descrição e invocação continuam disponíveis. Não remover nesta issue.

Plugins habilitados não foram classificados como desperdício só por baixa invocação. Plugins do runtime usam descoberta progressiva; medir custo de início e catálogo visível é pré-condição. Duplicatas já desativadas — `claude-mem@thedotmack` e `codex@openai-codex` no Codex — permanecem desativadas.

## Fila de pilotos

1. Perssua: mapear função/dependentes, executar smoke test, desativar nas três CLIs, abrir sessão nova e restaurar se qualquer fluxo falhar.
2. Duplicatas de skills: escolher fonte canônica, remover só as duas cópias idênticas em worktree isolado e validar o catálogo das três CLIs.
3. GitHub: executar a mesma jornada de issue + branch + PR com `gh`, MCP externo e conector nativo; manter uma interface por CLI quando o benchmark demonstrar cobertura.
4. Chrome: medir uma jornada web fixa com Chrome DevTools MCP e a alternativa já instalada; preservar a opção que cobrir inspeção, console e automação.
5. Graphify MCP: comparar `explain` e `path` via MCP e CLI local com o mesmo `graph.json`; retirar apenas entradas redundantes, nunca a skill nem o fallback documentado.

Cada item vira issue própria. Gate 1 aprova desenho e rollback; Gate 2 aprova o diff. Configurações atuais ficam intactas até esses pilotos.

## Follow-up executado — issue #27

Gate 1 foi autorizado em 2026-09-18. O piloto aplicou a escolha explícita de `gh` como dono do GitHub e preservou rollback local em `~/.config-backups/capability-cleanup-27-20260918-021024`.

| Item | Antes | Depois | Verificação |
|---|---|---|---|
| GitHub MCP externo | configurado nas três CLIs; no Claude faltava `GITHUB_TOKEN` | removido das três CLIs | `gh` 2.98.0 autenticado; leitura pós-mudança passou; comentário na issue #27 comprovou escrita |
| Perssua | configurado nas três; zero chamada estruturada no baseline | removido do escopo user do Claude; `disabled` no Codex e AGY | estados confirmados; busca em hooks, scripts e workflow retornou zero dependência |
| Skills duplicadas | catálogo Codex 77 total/26 ativas; duas entradas ativas para cada nome e duas cópias antigas desativadas | catálogo 73 total/24 ativas; uma entrada ativa por nome | app-server novo, zero erro de catálogo |
| Graphify no Codex | MCP desativado | mantido desativado; skill/CLI preservada | `explain AnchorEngine` passou; `AnchorEngine -> MotorContext` retornou caminho de 1 hop |

As cópias canônicas continuam em `~/.agents/skills/learned/`, gerenciadas por `agent-workflow-lab/deployed-skills.json`. Foram removidas duas cópias raiz byte a byte idênticas e duas cópias antigas do Codex com frontmatter divergente. Saíram quatro entradas de override: duas globais e duas da configuração local do GPT Tutor. `verify.py` foi ajustado de 54 para 52 paths e passou com `managed_skill_files=75`, sem erros. O dry-run de `repor-podas.py` indicou zero remoções/reposições e não gerencia essas quatro pastas.

Graphify permanece sem MCP no Codex porque o histórico registrou reescrita inválida do comando pelo Alethe. O caminho CLI não depende dessa entrada e passou no grafo atual. Claude e AGY ainda mantêm seus MCPs Graphify ativos.

O Claude Code só oferece o toggle de MCP por projeto; para desativar Perssua globalmente sem depender de cada checkout, a entrada user foi removida e preservada no backup. A restauração copia os quatro arquivos de configuração, as quatro pastas e `agent-workflow-lab-verify.py` do backup para seus caminhos originais; depois roda o `verify.py` restaurado e abre sessões novas nas três CLIs. Referência: [Claude Code — Disable a server without removing it](https://code.claude.com/docs/en/mcp#disable-a-server-without-removing-it).
