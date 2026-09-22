# Estado da tarefa — copiar para .workflow/local/active-task.md

- task_id: <ID estável>
- campanha_task_e_goal: <IDs do bloco fila-campanhas do tracker | nenhuma>
- reserva_e_janela: <nenhuma | reservada: assistida/noturna; reservar não lança>
- estimativa_nao_medida_e_duracao_medida:
- evidencia_de_aceite:
- issue_url:
- pr_url_e_base:
- alvo_de_release_e_rollback:
- objetivo_e_escopo_aprovados:
- branch_e_head:
- coordenador_e_sessao:
- investigador_e_sessao:
- classificacao: <T0..T3; C1..C3 ou nenhuma; provisória/confirmada>
- risco_ambiguidade_alcance_e_evidencias:
- confianca_e_motivo_reclassificacao:
- modelo_effort_por_fase_e_justificativa:
- modelo_observado_e_uso: <não atestado até evidência; input/cache_create/cache_read/output/tempo>
- executor: <Claude/modelo conforme routing.md ou escolha explícita>
- revisor: Astra (somente leitura)
- restricoes_explicitas:
- gate_1: pendente
- gate_2: pendente
- etapa_atual:
- proxima_acao:
- arquivos_permitidos:
- tipo_de_delegacao: <planejamento | auditoria | revisao_de_diff | pesquisa | implementacao | nenhuma>
- skills_necessarias_e_evidencia_de_uso:
- criterio_de_termino:
- evidencias_e_tentativas:
- diff_e_testes:
- escaladas_automaticas: 0
- status: planejando
- sessao_delegada:
- inicio_e_timeout:
- resultado_e_pendencias:

Atualizar antes de delegar e ao fechar cada etapa. Estados: planejando, executando,
delegando, bloqueado, revisando, concluido. Nunca guardar chaves ou saídas sensíveis.
