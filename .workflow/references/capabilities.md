# Descoberta, adoção e remoção de capacidades

Buscar capacidade nova somente após registrar um gap concreto e conferir recursos nativos,
conectores, MCPs, skills e padrões já disponíveis. `find-skills` permanece desabilitada no
catálogo padrão. Quando o gap justificar busca externa, usar sob demanda
`DO_NOT_TRACK=1 npx skills find "<capacidade específica>"`; nunca executar busca vazia,
`add` ou `update` automaticamente.

Resultado de busca é candidato, não recomendação. Fixar repositório, caminho, commit e
licença; auditar `SKILL.md`, scripts, referências, hooks, MCPs, rede, telemetria, permissões e
tratamento de segredos. Comparar com o dono atual usando fixture e critérios prévios. Só
instalar após issue própria, piloto isolado, ganho verificável e Gates 1/2. Manter a solução
atual até o candidato superar o baseline; popularidade, estrelas e bytes não provam qualidade,
segurança ou economia de tokens.

Antes de remover skill, MCP, plugin ou conector, medir invocações reais nos transcripts e
separar definições de ferramenta de chamadas executadas. Distinguir homônimos por prefixo e
origem, mapear dependências e confirmar o substituto já usado. Zero uso sem cobertura de
transcript vira lacuna de observabilidade, não autorização de remoção. Preferir desabilitação
reversível; cada lote de remoção usa issue, diff, rollback e Gates próprios.
