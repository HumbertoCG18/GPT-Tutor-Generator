# Executor selecionado e revisor Astra

O investigador seleciona executor Claude/effort conforme routing.md; Astra revisa (medium T1/T2, high T3). Escolha explícita do usuário prevalece. Astra não assume implementação automaticamente. Sol ou Astra como executores exigem escolha explícita. Não mudar o modelo global nem a sessão atual silenciosamente.

O coordenador pode chamar Astra para uma revisão por tarefa aprovada, sem nova pergunta, quando o diff delimitado e as verificações estiverem prontos. Código relevante exige revisão independente; documentação simples recebe conferência local. Essa revisão substitui a chamada Terra/santa-loop padrão, evitando dois revisores pagos para a mesma etapa. Bloqueio do executor não autoriza transferir a implementação a Astra; registrar diagnóstico e solicitar orientação quando necessário.

Antes da chamada, persistir estado seguindo ../task-state.template.md: tarefa/escopo aprovados, executor/modelo selecionado, revisor=Astra, restrições explícitas, Gates 1/2, diff fixado, testes, arquivos permitidos e critério de término. O campo legado escaladas_automaticas contabiliza chamadas automáticas Astra, agora somente de revisão: marcar 1 e status=delegando antes da chamada. Não zerar a contagem de uma tarefa existente. Só o coordenador escreve estado; sem duas sessões coordenando a mesma tarefa.

Astra recebe brief autocontido, sem segredos: contrato, diff, testes, riscos e arquivos permitidos. Somente leitura; sem implementação, subdelegação, commit ou merge. Usar subagente nativo gpt-6-astra com instrução read-only quando exposto; senão codex exec --profile astra --sandbox read-only, validando ~/.codex/astra.config.toml e fornecendo prompt por stdin. Preservar permissões nativas, sem bypass. Exigir do chamador timeout de 10 minutos; sem retries automáticos. O limite de tempo não equivale a limite de tokens/assinatura.

Consumir a mensagem final da CLI, sem concatenar eventos intermediários: o piloto detectou aviso do claude-mem antes do JSON final. Registrar sessão, achados e evidências da revisão. O executor selecionado corrige os achados e roda as verificações; nova revisão LLM exige autorização explícita. Falha, timeout ou quota consomem a única tentativa automática; preservar estado e reportar revisão incompleta. Pedido de continuar não renova essa tentativa.

O piloto comparativo passou nas duas tarefas para ambos os modelos, mas não mediu superioridade de Astra como revisor nem execução autônoma desta política. A divisão dos papéis é a preferência aprovada pelo usuário.
