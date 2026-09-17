# Roteamento operacional das três CLIs

Claude Code é a entrada principal: esclarece o pedido, conduz ECC e implementa ou delega. Fable executa; Astra revisa em sessão separada no Codex. AGY pesquisa documentação pública e prepara documentação a partir de evidências verificadas. A CLI escolhida não substitui os critérios de aceite.

1. Claude define escopo, arquivos e verificações; Gate 1 humano antes de implementação quando houver plano novo. Uma tarefa, um coordenador.
2. AGY usa agents/agy-researcher.md como contrato inline quando pesquisa for necessária. Consultas Context7 exigem biblioteca + pergunta completas; IDs e evidências são compartilhados para evitar repetição. Documentação do projeto usa MEX/Graphify, sem gerar CODEMAPS concorrentes.
3. Executor recebe contrato e evidências. Cada arquivo tem um dono. Sem biblioteca nova para tarefa coberta pela stdlib. Defeito começa por teste vermelho.
4. Revisão proporcional ao risco: documentação simples recebe conferência local; código relevante recebe revisão independente do diff fixado, critérios e resultados, com Astra no Codex, em modo somente leitura. Mudanças críticas exigem análise aprofundada. O revisor não faz merge.
5. Gate 2 humano antes de commit. Tracker recebe resultado e pendências; não declarar sucesso por exit code/SUCCESS sem artefato e verificações.

## Executor Fable e revisor Astra

Fable é o executor padrão no Claude Code; Astra é o revisor independente. Escolha explícita do usuário prevalece. Astra não assume implementação automaticamente. Sol ou Astra como executores exigem escolha explícita. Não mudar o modelo global nem a sessão atual silenciosamente.

O coordenador pode chamar Astra para uma revisão por tarefa aprovada, sem nova pergunta, quando o diff delimitado e as verificações estiverem prontos. Código relevante exige revisão independente; documentação simples recebe conferência local. Essa revisão substitui a chamada Terra/santa-loop padrão, evitando dois revisores pagos para a mesma etapa. Bloqueio do executor não autoriza transferir a implementação a Astra; registrar diagnóstico e solicitar orientação quando necessário.

Antes da chamada, persistir estado seguindo task-state.template.md: tarefa/escopo aprovados, executor=Fable, revisor=Astra, restrições explícitas, Gates 1/2, diff fixado, testes, arquivos permitidos e critério de término. O campo legado escaladas_automaticas contabiliza chamadas automáticas Astra, agora somente de revisão: marcar 1 e status=delegando antes da chamada. Não zerar a contagem de uma tarefa existente. Só o coordenador escreve estado; sem duas sessões coordenando a mesma tarefa.

Astra recebe brief autocontido, sem segredos: contrato, diff, testes, riscos e arquivos permitidos. Somente leitura; sem implementação, subdelegação, commit ou merge. Usar subagente nativo gpt-6-astra com instrução read-only quando exposto; senão codex exec --profile astra --sandbox read-only, validando ~/.codex/astra.config.toml e fornecendo prompt por stdin. Preservar permissões nativas, sem bypass. Exigir do chamador timeout de 10 minutos; sem retries automáticos. O limite de tempo não equivale a limite de tokens/assinatura.

Consumir a mensagem final da CLI, sem concatenar eventos intermediários: o piloto detectou aviso do claude-mem antes do JSON final. Registrar sessão, achados e evidências da revisão. Fable corrige os achados e roda as verificações; nova revisão LLM exige autorização explícita. Falha, timeout ou quota consomem a única tentativa automática; preservar estado e reportar revisão incompleta. Pedido de continuar não renova essa tentativa.

O piloto comparativo passou nas duas tarefas para ambos os modelos, mas não mediu superioridade de Astra como revisor nem execução autônoma desta política. A divisão dos papéis é a preferência aprovada pelo usuário.

## Retomada e limites

Estado local por worktree em .workflow-local/active-task.md, excluído do Git; usar o template distribuído. Tracker/handoff versionado guarda apenas resultado e pendências sem dados sensíveis. Em projeto sem este pacote, usar o handoff existente com os mesmos campos.

Ao receber continuar, ler estado + tracker/handoff e conferir branch, HEAD, diff, testes e situação da chamada anterior. Se status=delegando, verificar a sessão registrada antes de decidir que foi interrompida; não lançar segunda chamada. Retomar a próxima etapa pendente, sem refazer trabalho concluído, reabrir tarefa encerrada ou ultrapassar Gate 1/2. Estado ausente, contraditório ou múltiplas tarefas plausíveis exige esclarecer a ambiguidade. Continuar não é autorização de commit nem de novo escopo.

Quando houver quota esgotada, salvar estado e aguardar orientação; não trocar de provedor nem repetir chamadas recusadas automaticamente. Data e saldo de reset não são presumidos. AGY e Context7 entram somente quando pesquisa for necessária.

Automação conduzida pelo agente enquanto a sessão está ativa, com autorização persistente nas instruções. Não há daemon, monitor de reset ou scheduler. Hooks existentes mantêm verificações mecânicas; não disparam LLM. O limite de uma revisão automática depende do coordenador seguir o estado, não de bloqueio técnico no servidor. Gates ECC permanecem aplicáveis; autorização explícita de commit dada pelo usuário no escopo prevalece, depois de preparar e verificar o diff.

## Enxame experimental

Somente tarefas independentes, até três trabalhadores, sem recursão. Uma cópia por escritor ou arquivos disjuntos; integração serial pelo coordenador. Usar o mesmo modelo e esforço nos braços individual/enxame para avaliar concorrência; trocar por modelo mais barato é outro experimento. Comparar aceite, regressões, tempo de parede e uso reportado. Uma execução por braço não prova confiabilidade geral nem economia de assinatura.

## Context7 e segredos

Configuração nativa por CLI. Chave somente nos arquivos locais autorizados, nunca em prompts, relatórios, git ou argumentos de shell. Escopo de permissão restrito às consultas resolve-library-id e query-docs quando o cliente exigir. Plano pago não autorizado. Limite atual do piloto e consumo ficam no tracker do projeto, sem duplicar números aqui.

Catálogo instalado, descoberta, chamada executada e resposta correta são quatro evidências distintas. Configurar uma chave não atualiza necessariamente uma sessão já aberta.

No AGY, enviar o schema de saída com --json-schema e consumir structured_output do envelope JSON. response pode concatenar objetos; não usar como JSON puro. Conferir também denied_actions e fatos/fontes. Contrato de saída do piloto: evals/research-output.schema.json.
