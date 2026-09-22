# Continuidade do workflow

21/09, decisão seguinte: matriz T0..T3/C1..C3 aprovada; investigador decide classificação,
coordenador registra. Fonte operacional: references/routing.md; Sonnet/Opus/Fable por nível,
perfis AGY Pro3.1/Sonnet4.6/Opus4.6Thinking opcionais, sem superioridade medida.
Fluxo diurno Claude→AGY já validado para auditoria (estado routing-daytime-44.md no checkout principal).
Nova matriz é política documental; seleção de cada perfil ainda não validada E2E. Noite não liberada.

21/09: reconciliação #43/#44 distribuída; política sob demanda em references/campaigns.md,
fila viva em docs/reports/pendencias.md. Evidências e baseline: laboratório/private/campaign-43-reconcile-20260921/.
Histórico tracker preservado byte a byte; Gate 2 pendente, sem commit. Estado #43 no worktree próprio.
Próximo: validar fluxo diurno; depois apresentar diagnóstico #42 delimitado para autorização específica.

Frente atual: [#44](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/44).
Consolidação em agent-workflow-lab-context-44 e GPT-Tutor-Generator-context-44.
Fonte instalada: agent-workflow-lab/workflow.md; detalhes por ação em references/.

Estado da #44: .workflow/local/active-task.md (legado: .workflow-local/) do worktree correspondente; não reutilizar estado do motor.

Night-agent: #42, pacote em agent-workflow-lab-night-42/pilots/night-agent.
Fila compartilhada: #43, worktree GPT-Tutor-Generator-campaign-43; inspecionar antes de estender.
Smoke noturno anterior falhou por unexpected_model; generic_night/Codex executor/suspensão bloqueados.
Não reiniciar claude-mem por quota nem repetir revisão consumida. Commit/merge seguem seus Gates.

22/09: frente do motor — bloco 214/237 (>90 %) com #47 commitada (9220a57) e #48 implementada sem commit (Gate 2 pendente); CRU-02 (subunidade) iniciada com protocolo do Astra, workers W-P1/W-Q interrompidos. Handoff: docs/reports/2026-09-22-handoff-motor-cru02-claude.md; estado em .workflow/local/active-task.md.

22/09 (tarde), frente do motor: #48 (b726d4c) e #49 (410592d) commitadas; bloco 217/237 (91,6 %), unidade 246/284,
subunidade cru 84/251. CRU-02 medida ate o teto da declaracao (W-P1, W-P2, W-S: alias por expressao 118/251;
guarda + pergunta por material 213/251 com custo 261). Handoff: docs/reports/2026-09-22-handoff-motor-49-claude.md.
Proximo: decisao do usuario sobre o rumo da CRU-02; nenhum Gate 1 aberto.
22/09 13:40: W-T (unidade: regras reprovadas; 12 links offline = unico caminho para 90 %) e W-U (relacoes explicitas cobrem 56/106 mas nao discriminam) conferidos; adendo no handoff de 22/09; decisoes (a)/(b)/(c) pendentes do usuario.
