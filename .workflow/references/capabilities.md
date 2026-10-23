# Descoberta, adoção e remoção de capacidades

Buscar capacidade nova somente após registrar um gap concreto e conferir recursos nativos,
conectores, MCPs, skills e padrões já disponíveis. `find-skills` permanece desabilitada no
catálogo padrão. Quando o gap justificar busca externa, usar sob demanda
`DO_NOT_TRACK=1 npx skills find "<capacidade específica>"`; nunca executar busca vazia,
`add` ou `update` automaticamente.

Resultado de busca é candidato, não recomendação. Fixar repositório, caminho, commit e
licença; auditar `SKILL.md`, scripts, referências, hooks, MCPs, rede, telemetria, permissões e
tratamento de segredos. Comparar com o dono atual na mesma fixture e entrada, com critérios fixados antes de editar;
uma comparação por rodada, e outra só com falha específica pendente. Uma execução bem-sucedida
é fumaça, não taxa de confiabilidade. Só
instalar após issue própria, piloto isolado, ganho verificável e Gates 1/2. Manter a solução
atual até o candidato superar o baseline; popularidade, estrelas e bytes não provam qualidade,
segurança ou economia de tokens. Lição adotada registra evidência, escopo, data e gatilho de
invalidação. Sem candidato aprovado, registrar o estado bloqueado com causa e condição de
retomada (`bloqueio_causa_e_condicao` em task-state.template.md), não adoção parcial.

Antes de remover skill, MCP, plugin ou conector, medir invocações reais nos transcripts e
separar definições de ferramenta de chamadas executadas. Distinguir homônimos por prefixo e
origem, mapear dependências e confirmar o substituto já usado. Zero uso sem cobertura de
transcript vira lacuna de observabilidade, não autorização de remoção. Preferir desabilitação
reversível; cada lote de remoção usa issue, diff, rollback e Gates próprios.

Ao instalar ou alterar nas três CLIs, arquivo instalado, recurso descoberto e chamada executada
são provas distintas; uma não prova as outras. No Codex, arrays de configuração do projeto
substituem os globais: o projeto declara a seleção completa, não só acréscimos. O AGY rejeita
descrição YAML sem aspas que contenha dois-pontos, mesmo quando outra CLI a aceita. O Claude Code
pode expor o nome da pasta da skill, não o `name` do frontmatter: conferir a descoberta na CLI.
