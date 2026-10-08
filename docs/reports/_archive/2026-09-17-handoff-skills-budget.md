# Handoff — orçamento de skills, 17/09/2026

Pedido: corrigir `Exceeded skills context budget` sem quebrar o workflow.

## Medido

- Sessão importada ativa: `01a0a6f9-cb20-7032-8d68-40716ad3ca6e`, origem
  Claude Code/source=vscode. Em 17/09 19:07:15.778Z recebeu catálogo com 314
  entradas sem descrições, das quais 293 ECC. O aviso informado excluía mais 35.
- Catálogo atual do Codex 0.154.0 e do plugin app-server: 77 entradas,
  26 habilitadas, 51 desabilitadas, nenhum erro. O catálogo habilitado inclui
  os três orch, orch-pipeline, contract-first, eval-harness, git-workflow,
  tdd-workflow, Graphify, troglodita, ponytail e mem-search.
- Poda existente em simulação: zero remoções/reposições. A sessão carregada
  diverge do disco; só contar arquivos não detectava esse caso. Não foi reproduzida
  a sequência exata que expandiu o catálogo da sessão importada.
- Sessão efêmera de diagnóstico `01a0b0e3-0dd5-7351-99df-5245b3b77710`, sem
  turn/start nem inferência: início sem warning notificado/stderr. Isso verifica
  inicialização no app-server, não prova recarga do terminal já aberto.
- Schema local `SkillsConfigWriteParams` aceita seletor por nome. Teste em memória
  com `skills.config=[{name="ecc:orch-pipeline",enabled=false}]` desabilitou
  a entrada; nome sem prefixo `orch-pipeline` não desabilitou. Nenhuma inferência.

## Correção aplicada

Config global `~/.codex/config.toml` e config deste worktree `.codex/config.toml`:
424 seletores nativos por nome, derivados de skillOverrides do Claude e dos
aliases source-command. Os 54 ajustes anteriores por caminho foram preservados;
exceções explicitamente habilitadas do projeto não entram na exclusão.

O filtro por nome independe da versão no caminho do plugin e reduz a dependência
da poda SessionStart para skills já conhecidas. Não houve aumento de orçamento,
desinstalação ou mudança dos modelos/hooks. A poda antiga continua complementar.

`agent-workflow-lab/verify.py` agora também compara a política por nome com a seleção
do Claude. Passou com 75 arquivos gerenciados. Teste negativo em memória retirou
`ecc:accessibility` e confirmou falha do verificador, sem alterar disco.
Os dois catálogos após a mudança mantêm exatamente 26 habilitadas/zero erros.

Backup anterior à edição:
`agent-workflow-lab/private/skills-name-policy-20260917T194525Z/`.
Não restaurar config inteira sobre alterações posteriores; revisar o diff primeiro.

## Retomada e limites

Iniciar sessão nova e usar este handoff + workflow vigente; não retomar o JSONL
antigo como teste de catálogo novo. Não editar o histórico ativo. O contexto já
injetado nesta conversa não foi reescrito pela alteração de configuração.

Rodar `python verify.py`, `python catalog.py` e `python catalog_appserver.py` no
agent-workflow-lab após updates ou mudança de seleção. Os dois últimos não chamam
modelo. Se a política divergir, sincronizar seletores antes de usar a nova sessão.

Outros worktrees/projetos com arrays próprios de skills substituem a seleção global
e precisam receber os mesmos seletores. A config deste worktree está marcada
skip-worktree no índice; o diff comum não mostra sua alteração local. Essa marca
foi preservada. Revalidar ao trocar de worktree/projeto. Não houve commit nesta tarefa.
Novas skills ou mudanças do runtime podem exigir manutenção. Não prometer ausência
perpétua de warnings: a proteção cobre os nomes atuais e o verificador detecta drift
da seleção do Claude, não todo comportamento interno do runtime.
