# Pendências do workflow

- [USER] Confirmar conversa nova no Alethe sem aviso de orçamento de skills; sessão direta já aceita.
- [CODE] Na próxima tarefa real, verificar uma revisão Astra read-only e a retomada pelo estado salvo. Classificar cenários no piloto não prova delegação em execução.
- [DESIGN] Piloto de continuação noturna nas três CLIs. Gatilho explícito equivalente a
  "vou dormir, pode continuar desenvolvendo" deve iniciar um controlador externo em
  worktree isolado; não ampliar permissões da sessão nem trocar provider automaticamente.
  Exigir contrato aprovado, paths/comandos permitidos, bloqueio de rede/push/merge/deploy,
  snapshot/hash de arquivos protegidos, limites de tempo/tentativas/diff, validação externa,
  ledger append-only, kill switch e Gate 2 humano. Rotacionar a sessão antes de 100k tokens:
  persistir estado/handoff compacto, encerrar a sessão antiga e iniciar outra; autocompact
  nativo é otimização, não fonte de continuidade. Avaliar ZeroShot como referência/benchmark;
  não instalar enquanto não suportar AGY/Antigravity e a política de uma revisão Astra.
  Roteamento aprovado: Opus desenvolve e testa a infraestrutura do loop; Fable permanece
  reservado ao desenvolvimento do GPT-Tutor-Generator. O loop não troca modelos por quota.

Comparação Fable/Astra concluída: ambos 23/23 no parser e 12/12 no roteamento, sem retries.
Relatório: ../docs/reports/Feitos/workflow-medicao-fable-astra_16-09.md. Amostra pequena,
contextos distintos; não comprova economia de quota ou superioridade de Astra na revisão.
Fable executa; Astra revisa por preferência aprovada, uma chamada automática por tarefa
relevante. Fable corrige os achados. Nenhuma troca automática de executor por quota.

AGY usa contratos inline; registro de agentes nativos permanece não comprovado.
Context7 autenticado nas três CLIs; piloto conservador 12/20 tentativas, sem novas consultas.

Context Mode não adotado: removido das três CLIs; #22 fechada. Dados ativos preservados em backup recuperável.
Plugins Claude.ai Desktop Commander, PDF Viewer, Engineering, Design e `cowork-plugin-management`
mantidos intencionalmente na conta para possível uso futuro; não são pendência de limpeza.

## Candidatos avaliados, não adotados (22/09)

Critério: `.workflow/references/capabilities.md` (lacuna concreta antes de adotar). Reabrir só com o gatilho indicado.

- opensrc (vercel-labs, Apache-2.0): código-fonte de pacotes npm/PyPI/crates/GitHub em cache local. Complementa o Context7 (código x documentação), mas no stack Python o fonte das dependências já está em site-packages e o `gh` busca repositórios com tag fixa. Gatilho: campanha web C6 (npm não instalado localmente); piloto contra Context7 + `gh` em perguntas reais de API.
- ai-memory (akitaonrails, MIT, v2.4.0): memória de longo prazo e handoff tipado entre CLIs (Claude, Codex e AGY suportados), fonte em markdown versionado, captura por hooks sem LLM. Sobrepõe claude-mem, `.workflow/local/active-task.md` e os handoffs; Windows nativo é experimental; AGY sem SessionEnd automático; mais uma camada de hooks nas três CLIs junto de claude-mem, Alethe e guardas. Gatilho: substituir o claude-mem (não somar), ou handoff entre CLIs falhar de forma medida (#45). Piloto em WSL2 isolado.
- repowise: terceiro índice de código ao lado de Graphify e CBM; ganhos publicados medidos fora deste projeto; `init` reescreve config do Claude. Gatilho: substituir Graphify ou CBM após comparação com perguntas reais do motor.
- tron-claude-config: sem licença, foco frontend; aproveitada só a ideia do pre-commit com gitleaks (#54), reimplementada.

## Próxima frente depois do agente noturno (#42)

- Retomar a auditoria-enxame como skill do Codex. Plano e spec de 03/09 arquivados em
  `docs/reports/_archive/2026-09-03-auditoria-enxame-codex-skill*.md`; branch
  `feat/auditoria-enxame-codex-skill` e worktree `.worktrees/auditoria-enxame-codex-skill`
  preservadas (parada em 16/09, 1 de 25 itens). A versão Claude (`.claude/workflows/auditoria-enxame.js`)
  segue em uso. Decisão do usuário em 23/09: terminar depois do #42.
