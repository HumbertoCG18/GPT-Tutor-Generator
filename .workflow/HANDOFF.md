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

22/09: frente do motor — bloco 214/237 (>90 %) com #47 commitada (9220a57) e #48 implementada sem commit (Gate 2 pendente); CRU-02 (subunidade) iniciada com protocolo do Astra, workers W-P1/W-Q interrompidos. Handoff: docs/reports/_archive/2026-09-22-handoff-motor-cru02-claude.md; estado em .workflow/local/active-task.md.

22/09 (tarde), frente do motor: #48 (b726d4c) e #49 (410592d) commitadas; bloco 217/237 (91,6 %), unidade 246/284,
subunidade cru 84/251. CRU-02 medida ate o teto da declaracao (W-P1, W-P2, W-S: alias por expressao 118/251;
guarda + pergunta por material 213/251 com custo 261). Handoff: docs/reports/_archive/2026-09-22-handoff-motor-49-claude.md.
Proximo: decisao do usuario sobre o rumo da CRU-02; nenhum Gate 1 aberto.
22/09 13:40: W-T (unidade: regras reprovadas; 12 links offline = unico caminho para 90 %) e W-U (relacoes explicitas cobrem 56/106 mas nao discriminam) conferidos; adendo no handoff de 22/09; decisoes (a)/(b)/(c) pendentes do usuario.

26/09, frente regime VOCAB (sessão ee4dd19b): Fase 1 avaliada e encerrada (válida com ressalvas; A verdadeiro, B não
atendido, C só no IA; errata final). Rodada VOCAB_LIMPO: recompilação limpa única (26 chamadas, congelamento 62b45e38…)
e seis braços capturados sem gold (congelamento 6a0f9652…). Aguardando revisão do GPT e Gate de avaliação. Nada
commitado; 14 renames da limpeza de docs/reports staged. Handoff: docs/reports/2026-09-26-handoff-regime-vocab-claude.md.
27/09: rodada VOCAB_LIMPO avaliada (primária 174/251; A_limpo verdadeiro, B_limpo e C_limpo não atendidos; relatório
c1-3/vocab_limpo_avaliacao_26-09/relatorio_avaliacao_vl.md). Gate 2 documental: artefatos da frente commitados localmente,
sem push. Feitos em 27/09: diagnóstico das 13 perdas (c1-3/vocab_limpo_diag_perdas_27-09/) e desenho da validação em
cursos novos (docs/reports/2026-09-27-regime-vocab-validacao-cursos-novos-desenho.md). Próximo: decisões do usuário na §6
do desenho; rede/LLM e gold novo não autorizados.
