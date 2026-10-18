# Alterar skills, MCPs e hooks nas três CLIs

Separar arquivo instalado, recurso descoberto e chamada executada. Um resultado
não prova os outros. AGY é Antigravity CLI, não Gemini CLI.

1. Inventariar catálogo/configuração e medir invocações reais antes de retirar recursos.
2. Definir um dono por responsabilidade e destino; fazer backup fora do Git.
3. Validar esquema nativo por CLI. No Codex, arrays de projeto substituem os globais.
4. Conferir frontmatter YAML estrito e hashes após distribuir skills; o AGY pode
   rejeitar descrições sem aspas contendo dois-pontos, mesmo quando outra CLI as aceita.
   Claude pode expor o nome da pasta, não o name do metadata; preferir skills pessoais
   diretamente sob .claude/skills, validando a descoberta em vez de presumir recursão.
5. Testar inicialização, transporte MCP e comportamento com permissões normais;
   conferir novamente após Alethe abrir as sessões. Preservar saída bruta nos pilotos.

Nesta máquina, fontes comuns e verificador ficam em
`C:/Users/Humberto/Documents/GitHub/agent-workflow-lab`.
Estado e aceites pendentes ficam no tracker. Não criar hooks para sincronizar índices.

Roteamento operacional aprovado em 16/09: seguir `workflow.md` no laboratório:
A escolha do executor e a revisão proporcional ao risco seguem a seção Escolha do executor
nesse arquivo; não fixar modelo nos hooks. AGY pesquisa e prepara documentação verificável. Papéis inline ficam em `agents/`; não reimportar bundles para corrigir contratos.
Enxame permanece experimental até comparação com execução individual e aceite registrados.

AGY 1.2.4: `--json-schema` fornece `structured_output`; consumir esse campo, não concatenar
objetos de `response`. Verificar `denied_actions`, fontes e resultado. `SUCCESS` isolado não basta.
Permissões por projeto devem ser conferidas no log de ApplyProjectPermissionGrants.
