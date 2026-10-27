# Ferramentas: detalhes e medições

Movido de [tooling.md](tooling.md) (PODA-18, #447). Ler ao citar número medido, criar glossário ou ADR, ou rever a paridade de MCPs.

## MCPs por CLI (paridade medida em 30/09/2026)

Iguais nas três: context7, claude-mem (mcp-search).
GitHub e Graphify pelas CLIs gh e graphify. Uso real antes de remover, remedido em 11/10 com
`skills/medir-uso-antes-de-remover/scripts/count_tool_use.py` até 30/09 (a contagem anterior só lia
tool_use e dava zero falso no Codex): github MCP 0/0/0 chamadas (Claude/Codex/AGY; as 28
"github" do Codex são do conector embutido codex_apps) contra gh 491/252; graphify MCP 2/0/0
contra CLI 18/82; chrome-devtools 0/0/0; perssua 0/0/0. O 1 do github no Claude e o ~1 do
graphify no AGY de 30/09 não se reproduzem (hipótese: transcripts rotacionados). Removidos: github (as três),
graphify e chrome-devtools-mcp (Claude, AGY), perssua (Claude; segue desligado no
Codex e no AGY). O chrome-devtools continua via plugin ECC no Claude e no Codex.
Codex: node_repl (MCP, sem `enabled` = ativo) e o plugin codex-app-tools seguem ativos; cua_repl
fica desligado (`enabled = false`), assim como graphify e perssua.
Readicionar: claude mcp add perssua -s user -e PERSSUA_MCP_SOURCE=... -- cmd.exe /d /s
/c npx -y @perssua/mcp; graphify MCP com graph.json do projeto como argumento.
Backups: ~/.claude.json, ~/.codex/config.toml e ~/.gemini/config/mcp_config.json com
sufixo .bak-paridade-20260930-011932 (e .bak-github-mcp-20260930-004949).

## Número medido

Número medido citado em doc ou eval vem com três marcas: N (amostras ou rodadas), faixa (min–max ou IC)
e limitador (o que não foi medido). Com N=1 a faixa escreve-se `faixa n/d (N=1)`. Contagem exata de itens observados (achados, rodadas,
sessões) dispensa faixa; mediana com mínimo e máximo vale como faixa. Sem as três, o número
é só indício: não serve de decisão.
Antes de citar, responder: rodou como roda de verdade (build, flags e cache de produção)? contou erros e falhas, não só o tempo? o trabalho aconteceu dentro da região medida (cache, lazy load, processo em background)? alternou A/B em vez de A depois B? (origem: pstack `benchmark-checklist`, perguntas 2, 4, 7 e alternância da 5).

## Glossário e ADR leve

Não por padrão. Um projeto ganha glossário só com termo sobrecarregado comprovado: o mesmo termo com dois significados que já geraram erro ou retrabalho registrado (issue, revisão, handoff). Sem esse registro, não criar.
- Onde: seção `## Glossário` no mapa de fontes do projeto (`.mex/ROUTER.md` quando existir), linkada do próprio mapa; sem arquivo novo, sem glossário global no laboratório.
- Formato mínimo: `termo: significado adotado; o que não é; fonte`. Uma linha por termo. ADR leve: só decisão que contradiz o óbvio do código, 3 linhas (contexto, decisão, gatilho de revisão), na mesma seção.
- Manutenção: termo sem consulta no período de medição sai (mesma regra de remoção de skill).
- Medição de consultas reais: contar leituras do ROUTER depois de criado o glossário, não grep do termo. `python skills/medir-uso-antes-de-remover/scripts/count_tool_use.py '\.mex/ROUTER\.md' --in-args` por projeto, antes e depois (`--until` fixa a data de corte). Consulta ao glossário = leitura do ROUTER em sessão cujo tema contém o termo; a contagem do arquivo inteiro é teto, não consulta ao glossário. Janela e limiar de remoção: definir ao criar o primeiro glossário; hoje 🔴 sem dado (nenhum glossário existe).
