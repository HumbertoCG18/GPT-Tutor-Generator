# Auditoria dos diretórios dos coding agents

Data: 22/09/2026. Refs [#44](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/44).
Escopo: auditar organização, consumidores e proposta de consolidação. Sem migração, remoção, alteração em src/, execução de workers ou mudança de configurações ativas. O piloto de .gitignore anterior continua isolado e com Gate 2 pendente.

## Parecer

Organizar por responsabilidade e pelos caminhos nativos de cada cliente. Manter .claude/ para Claude, .codex/ para Codex e .agents/ para a superfície compartilhada Codex/AGY e hooks AGY. Não criar .agy/ sem um consumidor comprovado. Não mover o workflow comum para dentro de uma CLI.

A fonte pessoal continua no agent-workflow-lab; o projeto recebe apenas regras específicas e snapshots revisados. Alethe mantém a execução e as worktrees; tracker e estado local mantêm aceites, Gates e revisão. Diretórios arrumados não comprovam que workers carregam as regras corretas.

## Evidência atual

- Versões executadas via --version: Claude Code 2.1.280; Codex 0.155.1; AGY 1.2.8.
- Instruções pessoais ~/.claude/CLAUDE.md, ~/.codex/AGENTS.md e ~/.gemini/GEMINI.md: 4.314 bytes cada e SHA256 idêntico. Já existe uma distribuição consistente; preservar.
- verify.py do laboratório: 81 arquivos gerenciados; resultado ok=false, único erro `Codex Companion reenabled inside Codex`. Não desabilitar o plugin só para tornar o relatório verde; confirmar dono/intenção em tarefa separada. Nenhum outro erro foi reportado pelo verificador, o que não equivale a teste de runtime de todas as CLIs.
- Inventário de SKILL.md fora dos caches de plugins: 21 em ~/.claude/skills, 11 em ~/.codex/skills, 37 em ~/.agents/skills, 6 em ~/.gemini/config/skills. Não são contagens de skills habilitadas/carregadas.
- Em ~/.agents/skills há dois pares de SKILL.md byte a byte iguais: heredoc-git-bash-windows/SKILL.md e learned/heredoc-git-bash-windows/SKILL.md; mex-check-falso-positivo/SKILL.md e learned/mex-check-falso-positivo/SKILL.md. A comparação não cobre todo o bundle nem comprova desuso. Não removidos.
- Configuração Codex do projeto: 476 entradas de skills, 7 habilitadas; 52 entradas com caminhos absolutos. Parte da lista expressa bloqueios, não duplicação descartável. verify.py verifica a seleção e a relação com as políticas Claude.
- No principal, .workflow/README.md, .claude/settings.json e AGENTS.md diferem dos arquivos da worktree Alethe job-01. Isso comprova diferenças em disco, não qual conteúdo a sessão carregou. Um worker novo não deve ser presumido equivalente ao principal.
- Os contratos em .workflow/agents são instruções/papéis documentais; não presumir cadastro de agentes nativos. Não foram encontrados diretórios pessoais ~/.claude/agents ou ~/.codex/agents no inventário.

## Estrutura de destino proposta

Árvore lógica; itens opcionais não serão criados vazios. A migração documental depende da classificação por aceite e de correção dos links.

```text
GPT-Tutor-Generator/
├── AGENTS.md                    # entrada comum/Codex, curta
├── CLAUDE.md                    # entrada Claude atual; pode permanecer curta
├── GEMINI.md                    # entrada AGY atual, com referências comuns
├── .mcp.json                    # posição nativa Claude; hoje local/ignorada
├── .claude/
│   ├── settings.json            # configuração compartilhada
│   ├── settings.local.json      # pessoal, ignorada
│   ├── skills/                  # recursos específicos do projeto, se necessários
│   ├── rules/                   # instruções condicionais, sem copiar todo o workflow
│   ├── agents/                  # agentes Markdown realmente necessários
│   └── workflows/               # scripts nativos Claude; execução explicitamente roteada
├── .codex/
│   ├── config.toml              # configuração do projeto; seleção/MCP/hooks atuais
│   ├── agents/                  # agentes TOML, se houver uso autorizado
│   └── rules/                   # regras nativas de execução, quando aplicáveis
├── .agents/
│   ├── skills/                  # bundles compatíveis Codex/AGY
│   ├── rules/                   # regras AGY; não confundir com regras de execução Codex
│   └── hooks.json               # registro AGY já existente
├── .workflow/                   # snapshot e contratos compartilhados
├── .workflow-local/             # estado por worktree, ignorado
├── .alethe/worktrees/           # propriedade do Alethe, preservada
├── .mex/                        # mapa e invariantes do produto, preservados
├── scripts/hooks/              # uma implementação dos guardas para as três CLIs
└── docs/
    ├── plans/                   # destino futuro dos planos hoje dispersos
    │   └── Feitos/
    ├── specs/                   # destino futuro das especificações
    │   └── Feitos/
    └── reports/                 # auditorias, evidências e handoffs existentes
```

CLAUDE.md também pode morar em .claude/CLAUDE.md, conforme documentação, mas manter o arquivo curto na raiz evita alterar consumidores só para esconder um arquivo. Não manter duas cópias autoritativas. AGENTS.md continua na raiz. GEMINI.md continua no caminho atual até validar sua descoberta na versão AGY instalada.

A documentação Codex atual admite .codex/agents/*.toml; o formato não é o Markdown dos agentes Claude. .codex/rules não é substituto de .claude/rules: regras de execução e instruções em linguagem natural possuem contratos distintos. A existência de uma pasta hooks/ não registra hooks; a configuração do cliente precisa apontar para os scripts.

## Global versus projeto

| Superfície | Global/pessoal: preservar no home | Projeto: somente o necessário |
|---|---|---|
| Claude | ~/.claude/CLAUDE.md, settings, skills/plugins, hooks pessoais, memória e histórico; ~/.claude.json gerenciado | .claude/settings.json, skills/rules/agents/workflows; entrada de instruções e .mcp.json nos caminhos nativos |
| Codex | ~/.codex/config.toml, AGENTS.md, rules, plugins, bancos e sessões; ~/.agents/skills e caminhos já gerenciados | .codex/config.toml, agentes TOML quando usados; .agents/skills; AGENTS.md |
| AGY | ~/.gemini/GEMINI.md e configuração/estado atuais em ~/.gemini/config e ~/.gemini/antigravity-cli | .agents/hooks.json, rules e skills compatíveis; GEMINI.md atual |
| Alethe | Dados e preferências administrados pelo aplicativo | .alethe/worktrees e integrações geradas pelo aplicativo |

A documentação AGY distingue caminhos globais de CLI e IDE. O ambiente atual tem recursos gerenciados em ~/.gemini/config/skills; não migrá-los só para refletir a documentação mais recente sem comprovar onde AGY 1.2.8 os carrega.

Não copiar plugins/caches do home ao repositório. Não mover bancos, auth, memórias ou transcripts para dentro do projeto. Não criar .worktreeinclude com .env ou credenciais por padrão: o exemplo documental é ilustrativo, não uma necessidade deste workflow.

## O que juntar, manter ou investigar

| Origem | Proposta | Condição antes de executar |
|---|---|---|
| plans/ + docs/superpowers/plans/ | Consolidar em docs/plans/, preservando Feitos/ | Mapear referências e conflitos de nome; verificar conclusão real, não idade/checklist isolado |
| docs/superpowers/specs/ | Consolidar em docs/specs/, preservando Feitos/ | Corrigir links relativos e referências do tracker/handoffs |
| docs/superpowers/BACKLOG.md | Reconciliar pendências com o tracker existente; preservar história no arquivo de decisões/relatórios | Não copiar indiscriminadamente para a fila-campanhas nem perder decisões antigas |
| .superpowers/brainstorm e sdd | Classificar estado temporário, evidência concluída e trabalho aberto; arquivar apenas evidência concluída no local documental escolhido | Conferir referências e conclusão; sessões abertas ficam no lugar; não apagar todo o diretório |
| .claude/workflows/auditoria-enxame.js | Manter na localização nativa; revisar portabilidade e rota operacional | Caminho ROOT absoluto na linha 11; chamadas agent/pipeline/parallel nas linhas 66–90. Não executar nesta auditoria |
| scripts/hooks/ | Manter compartilhado | Mover para .claude/hooks duplicaria propriedade; os três registros já apontam para estes scripts |
| .workflow/agents/ | Manter contratos; criar adaptadores nativos apenas para papéis realmente usados | Formatos e permissões diferem; criação não deve habilitar um segundo coordenador |
| Instruções pessoais distribuídas | Manter fonte do laboratório e destinos verificados | São idênticas e têm verificação existente; não substituir por três conjuntos editados à mão |
| Pares de skills em ~/.agents/skills | Candidatos a consolidação | Conferir bundles completos, invocações reais, caminhos cadastrados e mecanismo que os recria |
| .cursorrules, .windsurfrules, .kiro/steering | Auditar uso das ferramentas e alinhar referências se ativas | Contêm code-review-graph obrigatório; fonte atual usa Graphify principal/CBM fallback. Ausência de uso não foi medida |
| GEMINI.md | Enxugar bloco histórico de code-review-graph após preservar sua finalidade | Já declara precedência das fontes atuais; é ruído e risco de conflito, não prova de falha atual |
| .claude/*.bak*, %SystemDrive%/ e arquivo com nome malformado | Triagem separada com lista exata | Origem, consumidores e retenção confirmados antes de remoção |
| .alethe/worktrees, .worktrees e worktrees externas | Não juntar sob uma CLI | Donos, metadados Git e referências persistentes do Alethe devem ser preservados |

## Correção da classificação anterior

.claude/workflows/*.js é um recurso nativo confirmado na documentação oficial; Claude 2.1.280 está instalado. Não há base para chamar o diretório de obsoleto. O conteúdo específico de auditoria-enxame.js é candidato a revisão por caminhos absolutos e contexto antigo. Seu uso atual não foi medido.

O piloto de .gitignore anterior é uma allowlist mínima, não o catálogo completo Claude. Ele continua excluindo workflows, commands, output-styles e agent-memory. Isso é aceitável enquanto nenhum recurso desses for selecionado para compartilhamento, mas não deve ser apresentado como prova de desuso. Não liberar o diretório inteiro sem classificar seu conteúdo. commands segue suportado; preferir skills para material novo.

## Integração com Alethe: critério operacional

1. Uma tarefa tem um coordenador. Perfis combinados representam papéis sequenciais, não dois despachantes independentes.
2. Em sessão Alethe, o dispatch e o acompanhamento seguem a rota Alethe já aprovada. Workflow dinâmico Claude que lança subagentes é uma alternativa explícita; não presumir que seus filhos aparecem como Worker Jobs do Alethe.
3. Cada worker precisa de cwd/worktree, commit e conjunto de instruções identificados. A diferença medida entre principal e job-01 impede presumir equivalência automática.
4. Distribuir apenas arquivos aprovados e compartilháveis, por mecanismo existente e verificável. Não sobrescrever worktrees ativas, não transplantar active-task.md do motor e não copiar credenciais para fazer um smoke passar.
5. Preservar Gates, contador único de revisão e fila-campanhas. Sucesso de Job não é aceite; pastas e prompts não impõem limites de quota. Limites de tokens/modelo/permissões precisam de validação própria.

Não foi executado smoke de worker, nem confirmada uma correção upstream do MCP. A futura validação deve usar um teste pequeno, explicitamente autorizado, sem trabalho de produto, preservando os limites anteriores.

## Plano mínimo e aceites antes de migrar

- Lote A: aprovar/entregar o piloto existente; conferir o que deve ser compartilhado além da allowlist inicial. Gate 2 continua pendente.
- Lote B: reconciliar instruções conflitantes e mover planos/specs com tabela arquivo-origem/destino, atualização de links e Feitos/ preservado. src/ fora do escopo.
- Lote C: consolidar somente bundles comprovadamente duplicados e recursos pessoais mal posicionados. Medição de uso antes de remoção; testar descoberta nas versões instaladas.
- Lote D: validar bootstrap de uma worktree nova e integração com Alethe. Comparar skills/instruções/hooks antes e depois; 0 alterações em src/, 0 segredo copiado, 0 reset de Gates/revisão e 0 dispatch duplicado.
- Worktrees antigas e caches ficam para lote de limpeza próprio, após confirmação de dono, resultados e estado Git. Não confundir reorganização com purga de sessões.

Sem novo framework, gerenciador de sincronização, fila ou árvore de diretórios vazia. Não há economia de tokens medida nesta auditoria: fonte única, menos regras sempre carregadas e ausência de dispatch duplicado são hipóteses a validar.

## Fontes oficiais consultadas

- Índice Claude: https://code.claude.com/docs/llms.txt
- Diretório Claude: material integral fornecido pelo usuário; referência https://code.claude.com/docs/en/claude-directory
- Workflows Claude: https://code.claude.com/docs/en/workflows
- Skills Claude: https://code.claude.com/docs/en/skills
- Skills Codex: https://learn.chatgpt.com/docs/build-skills
- Agentes Codex: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Instruções Codex: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Skills AGY: https://antigravity.google/docs/skills
- Hooks AGY: https://antigravity.google/docs/hooks
- Settings AGY: https://antigravity.google/docs/settings?tab=cli

Limites: inventário por arquivos e configuração, hashes e ajuda/versionamento das CLIs. Não mede invocações de todos os recursos, carga real de cada sessão, custo de tokens ou paridade de comportamento após migração. Nenhuma migração foi aplicada.
