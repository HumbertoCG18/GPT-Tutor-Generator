# Roteamento por tarefa

Ler uma vez ao iniciar tarefa substantiva; não recarregar por mensagem.
Núcleo e permissões: ../workflow.md. Uma tarefa mantém um coordenador.

## Classificação

| Pedido | Dono e saída |
|---|---|
| Pergunta/status ou ajuste documental/local pequeno | Agente ativo, resposta/verificação local |
| Implementação pequena e bem delimitada | Claude Code pelo nível em routing.md, teste e diff |
| Mudança complexa, múltiplos componentes, arquitetura ou aceite ambíguo | Codex planeja/orquestra; plano e aceites delimitados; Claude Code implementa pelo nível investigado |
| Código relevante pronto para revisão | Astra em sessão independente, read-only, uma tentativa registrada |
| Auditoria, pesquisa/corpus ou redação de achados | AGY, fontes verificáveis e relatório; arquivos de saída explicitamente permitidos |

Classificação, matriz e perfis: routing.md é a fonte canônica; investigador decide e coordenador registra.
Contratos inline: ../agents/codex-planner.md e ../agents/agy-auditor.md; carregar apenas o papel escolhido.
O usuário não precisa pedir "delegue". Classificar é parte da tarefa; chamadas respeitam
Gates e contrato [delegation.md](delegation.md). Escolha explícita do usuário prevalece.
Ler [review.md](review.md) antes de chamar revisor; não usar planejamento para renovar revisão.
Se o host já é Codex, planejar nele; não chamar outro Codex para repetir orquestração.
Se o host é Claude, conservar o terminal como interface; receber o plano e conduzir sua execução.
Se o host é AGY, limitar-se à auditoria/pesquisa/achados; devolver implementação ao coordenador.
Documentação/configuração simples pode ser concluída pelo agente ativo conforme escolha explícita.
Não delegar de volta ao chamador nem criar cadeia recursiva. Sem troca por quota.

## Goals e agente noturno

Quando solicitado listar goals, consultar o catálogo do projeto atual e mostrar ID, estado,
aceite restante e bloqueio; se ausente, declarar ausência. No GPT Tutor a fonte prevista é
docs/reports/goals-noturnos.md da frente #42; a fila persistente é #43.
Não confundir /goal nativo com catálogo do projeto. Selecionar/reservar não executa.
Antes de continuar, localizar tarefa existente em .workflow/local/active-task.md (legado: .workflow-local/) e conferir
branch/HEAD; preservar contador e chamada ativa. Nunca importar estado de outro worktree por suposição.
O supervisor noturno mantém seu próprio contrato executável, preflight e estado; esta rota
não o libera nem substitui seus controles. A integração futura deve transmitir o ID do goal
e papel explicitamente, pois subprocessos com safe-mode podem não carregar hooks.

## Hooks e validação

Hooks apenas injetam um lembrete desta rota, sem inferência, escrita de estado ou scheduler.
Claude/Codex: UserPromptSubmit; AGY: PreInvocation. Configuração é local e preserva hooks existentes.
Codex requer confiança da definição em /hooks; não escrever hashes de confiança nem usar bypass.
Modelo configurado não atesta modelo observado. Após abrir sessão nova, validar uma tarefa real
e registrar sessão/roteamento/saída antes de declarar delegação E2E.
Fontes: https://code.claude.com/docs/en/hooks e https://learn.chatgpt.com/docs/hooks;
AGY: https://antigravity.google/docs/hooks?tab=ide documenta também a CLI; formato conferido
com hooks.json e ponytail-inject.js instalados, sem presumir API de Gemini CLI.
