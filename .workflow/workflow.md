# Roteamento operacional das três CLIs

Claude Code é a entrada principal: esclarece o pedido, conduz ECC e implementa ou delega. Codex executa tarefas delimitadas e revisa em sessão separada. AGY pesquisa documentação pública e prepara documentação a partir de evidências verificadas. A CLI escolhida não substitui os critérios de aceite.

1. Claude define escopo, arquivos e verificações; Gate 1 humano antes de implementação quando houver plano novo. Uma tarefa, um coordenador.
2. AGY usa agents/agy-researcher.md como contrato inline quando pesquisa for necessária. Consultas Context7 exigem biblioteca + pergunta completas; IDs e evidências são compartilhados para evitar repetição. Documentação do projeto usa MEX/Graphify, sem gerar CODEMAPS concorrentes.
3. Executor recebe contrato e evidências. Cada arquivo tem um dono. Sem biblioteca nova para tarefa coberta pela stdlib. Defeito começa por teste vermelho.
4. Revisão proporcional ao risco: documentação simples recebe conferência local; código relevante recebe revisão independente do diff fixado, critérios e resultados, normalmente no Codex. Mudanças críticas exigem análise aprofundada. O revisor não faz merge.
5. Gate 2 humano antes de commit. Tracker recebe resultado e pendências; não declarar sucesso por exit code/SUCCESS sem artefato e verificações.

## Escolha do executor e escalada automática

Política aprovada em 16/09/2026. Fable é o executor padrão no Claude Code; a escolha explícita do usuário prevalece. Não mudar o modelo global nem a sessão atual silenciosamente. Sol continua disponível por escolha explícita. A comparação Fable/Astra aguarda o reset do limite Fable.

O coordenador pode delegar a Astra uma vez por tarefa aprovada, sem nova pergunta, quando registrar uma necessidade concreta: bloqueio reproduzido após tentativa dirigida do Fable, ou decisão de alto impacto com alternativas e incerteza ainda não resolvidas. Quantidade de arquivos, quota esgotada e o comando continuar não são gatilhos suficientes. Se o usuário restringir a Fable, não escalar. Anunciar brevemente a escalada e seu motivo.

Antes da chamada, persistir estado seguindo task-state.template.md: tarefa/escopo aprovados, executor atual, restrições explícitas, Gate 1/2, evidência do bloqueio, arquivos permitidos, critério de término, escaladas=1 e status=delegando. Só o coordenador escreve esse estado. Uma tarefa preserva seu ID entre sessões; não criar novo ID para renovar a franquia. Se houver outra sessão coordenando, não delegar em paralelo.

Astra recebe brief autocontido e delimitado, sem segredos: problema, tentativas, diff, testes, arquivos autorizados e critério de término. Sem delegação recursiva, commit ou merge pelo delegado. Preferir subagente nativo com modelo gpt-6-astra quando disponível. Caso contrário usar codex exec --profile astra, validando primeiro o arquivo ~/.codex/astra.config.toml. Revisão usa --sandbox read-only; implementação usa --sandbox workspace-write -C <worktree-isolado> e prompt por stdin. Preservar permissões nativas; não usar bypass. O chamador aplica timeout de 10 minutos, encerra a chamada ao atingir o limite e não repete automaticamente. Isso limita tentativas/tempo, não garante limite de tokens ou quota.

Ao terminar, registrar ID da sessão, resultado, diff e testes, então integrar e revisar. Se falhar, retornar diagnóstico e preservar estado; falha, timeout ou quota também consomem a única tentativa automática. Astra como executor explicitamente escolhido pelo usuário não é uma escalada automática.

## Retomada e limites

Estado local por worktree em .workflow-local/active-task.md, excluído do Git; usar o template distribuído. Tracker/handoff versionado guarda apenas resultado e pendências sem dados sensíveis. Em projeto sem este pacote, usar o handoff existente com os mesmos campos.

Ao receber continuar, ler estado + tracker/handoff e conferir branch, HEAD, diff, testes e situação da chamada anterior. Se status=delegando, verificar a sessão registrada antes de decidir que foi interrompida; não lançar segunda chamada. Retomar a próxima etapa pendente, sem refazer trabalho concluído, reabrir tarefa encerrada ou ultrapassar Gate 1/2. Estado ausente, contraditório ou múltiplas tarefas plausíveis exige esclarecer a ambiguidade. Continuar não é autorização de commit nem de novo escopo.

Quando houver quota esgotada, salvar estado e aguardar orientação; não trocar de provedor nem repetir chamadas recusadas automaticamente. Data e saldo de reset não são presumidos. AGY e Context7 entram somente quando pesquisa for necessária.

Automação conduzida pelo agente enquanto a sessão está ativa, com autorização persistente nas instruções. Não há daemon, monitor de reset ou scheduler. Hooks existentes mantêm verificações mecânicas; não disparam LLM. O limite de uma escalada depende do coordenador seguir o estado, não de bloqueio técnico no servidor. Gates ECC permanecem aplicáveis; autorização explícita de commit dada pelo usuário no escopo prevalece, depois de preparar e verificar o diff.

## Enxame experimental

Somente tarefas independentes, até três trabalhadores, sem recursão. Uma cópia por escritor ou arquivos disjuntos; integração serial pelo coordenador. Usar o mesmo modelo e esforço nos braços individual/enxame para avaliar concorrência; trocar por modelo mais barato é outro experimento. Comparar aceite, regressões, tempo de parede e uso reportado. Uma execução por braço não prova confiabilidade geral nem economia de assinatura.

## Context7 e segredos

Configuração nativa por CLI. Chave somente nos arquivos locais autorizados, nunca em prompts, relatórios, git ou argumentos de shell. Escopo de permissão restrito às consultas resolve-library-id e query-docs quando o cliente exigir. Plano pago não autorizado. Limite atual do piloto e consumo ficam no tracker do projeto, sem duplicar números aqui.

Catálogo instalado, descoberta, chamada executada e resposta correta são quatro evidências distintas. Configurar uma chave não atualiza necessariamente uma sessão já aberta.

No AGY, enviar o schema de saída com --json-schema e consumir structured_output do envelope JSON. response pode concatenar objetos; não usar como JSON puro. Conferir também denied_actions e fatos/fontes. Contrato de saída do piloto: evals/research-output.schema.json.
