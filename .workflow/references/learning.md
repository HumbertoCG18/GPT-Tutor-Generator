# Aprendizado: padrões repetidos em ativos

Usar quando o pedido for aprender com sessões, transformar padrão repetido em regra, comando ou skill, ou ao encerrar campanha com atrito recorrente. Não usar para implementação comum, depuração isolada ou ferramenta externa (esta segue capabilities.md).

Inventariar antes de propor: skills, comandos e agentes ativos nas três CLIs (../deployed-skills.json), instruções pessoais, workflow.md e references, regras e skills do projeto (AGENTS.md, .claude/rules, .claude/skills). Candidato já coberto estende o dono existente; nunca criar quase-duplicata nem segundo dono para a mesma fase.

Evidência, nesta ordem: conversa atual, tracker/handoff, issues e PRs, histórico git, transcrições de sessão. Candidato forte tem duas ou mais ocorrências, entrada estável, saída clara e condição de parada. Ocorrência única não basta, salvo pedido explícito do usuário para aquele fluxo. Não usar dado pessoal ou sensível como exemplo no ativo gerado.

Pontuar cada candidato por frequência, custo (tempo, tokens, atenção), risco de execução inconsistente, estabilidade e cobertura atual. Escolher a menor forma que resolve: linha em regra ou reference existente; reference sob demanda; script, quando a sequência é determinística e dispensa LLM; comando; skill; agente. "Nada a criar" é resultado válido quando a evidência é fraca.

Script, lint ou hook só entra se o check novo falha num erro real que já aconteceu: citar o caso. Sem esse caso, a lição fica como texto (origem: pstack `correct`, SKILL.md:26).

Propor antes de mudar: achados (evidência, frequência), mudanças recomendadas com dono e forma, pulados com motivo, e o que precisa de mais evidência. A criação segue delivery.md (issue, Gates 1/2). skill-create (quando disponível) só gera arquivo depois que este filtro escolher skill; skill global nunca é editada automaticamente.
