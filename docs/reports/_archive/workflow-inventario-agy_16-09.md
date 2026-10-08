# Inventário e proposta AGY — 16/09/2026

Escopo: inspeção local e pesquisa; nenhuma instalação, mudança de configuração ou teste de inferência. Prioridade informada: Claude Code, Codex, AGY.

## Verificado localmente

- `python C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/verify.py`: ok=true, 75 arquivos gerenciados, errors=[].
- `agy --version`: 1.2.3. `agy -p /skills --output-format json`: 38 entradas na resposta; descoberta não prova execução.
- Claude e AGY: seis MCPs globais configurados sem flag de desativação: perssua, chrome-devtools-mcp, context7, github, graphify, codebase-memory-mcp. Transporte não retestado nesta rodada.
- Codex: os mesmos nomes; Graphify MCP desabilitado, uso local pela skill; node_repl adicional na configuração. Plugins/conectores de aplicação são outra superfície.
- ECC, ponytail e claude-mem presentes nas três configurações. AGY descobre orch-*, eval-harness, parallel-execution-optimizer, living-docs-governance, cost-aware-llm-pipeline e seis skills pessoais comuns.
- AGY tem 68 arquivos de agentes ECC em ~/.gemini/config/plugins/ecc/agents. Não comprovada sua execução nativa. docs-lookup/doc-updater declaram model: haiku; planner: opus; tdd-guide: sonnet. Ferramentas usam nomes do Claude.
- doc-updater propõe docs/CODEMAPS e ferramentas TypeScript; adaptar ao Graphify/MEX antes de usar neste projeto.
- `claude agents` exigiu TTY; `claude agents --json` retornou sessões de agentes, não catálogo de definições. Não usar essa saída para contar papéis instalados.
- DOCX/PDF/PPTX/XLSX e Google Workspace não aparecem nas 38 skills descobertas pelo AGY. `gws` não encontrado no PATH.

## Pesquisa e limites

- AGY documenta subagentes nativos, modelos inherit/flash/pro e ferramentas próprias: https://antigravity.google/docs/subagents . Divergência com importação ECC é indício de incompatibilidade; falha de execução ainda não reproduzida.
- Skills de documentos candidatas: https://github.com/anthropics/skills . DOCX/PDF/PPTX/XLSX são source-available, não Apache-2.0 como parte das outras skills; verificar licença/dependências e execução antes de portar.
- Google Workspace candidato: https://github.com/googleworkspace/cli . CLI com skills; README declara não ser produto oficialmente suportado pelo Google. Não assumir suporte MCP por referências antigas.
- A documentação web de plugins cita ~/.gemini/antigravity-cli; o guia embutido e a descoberta local usam ~/.gemini/config. Priorizar evidência do binário instalado.

## Proposta, ainda não implementada

Claude como entrada principal e executor; Codex como revisão independente e executor de tarefas delimitadas; AGY para pesquisa com fontes, leitura de corpus, preparação de documentação e tarefas verificáveis. Modelo forte sobe por ambiguidade, não por extensão do arquivo.

Antes de adicionar ferramentas: validar docs-lookup e doc-updater adaptados em cópia isolada, preservando contratos MEX. Comparar fontes corretas, omissões, alterações fora do escopo, tempo e consumo. Documentação arquitetural não é automaticamente tarefa simples. Instalar equivalente documental somente quando houver formato/alvo concreto.
