# Roteamento operacional das três CLIs

Claude Code é a entrada principal: esclarece o pedido, conduz ECC e implementa ou delega. Fable executa; Astra revisa em sessão separada no Codex. AGY pesquisa documentação pública e prepara documentação a partir de evidências verificadas. A CLI escolhida não substitui os critérios de aceite.

1. Claude define escopo, arquivos e verificações; Gate 1 humano antes de implementação quando houver plano novo. Uma tarefa, um coordenador.
2. AGY usa agents/agy-researcher.md como contrato inline quando pesquisa for necessária. Consultas Context7 exigem biblioteca + pergunta completas; IDs e evidências são compartilhados para evitar repetição. Documentação do projeto usa MEX/Graphify, sem gerar CODEMAPS concorrentes.
3. Executor recebe contrato e evidências. Cada arquivo tem um dono. Sem biblioteca nova para tarefa coberta pela stdlib. Defeito começa por teste vermelho.
4. Revisão proporcional ao risco: documentação simples recebe conferência local; código relevante recebe revisão independente do diff fixado, critérios e resultados, com Astra no Codex, em modo somente leitura. Mudanças críticas exigem análise aprofundada. O revisor não faz merge.
5. Gate 2 humano antes de commit. Tracker recebe resultado e pendências; não declarar sucesso por exit code/SUCCESS sem artefato e verificações.

## Issues, PRs e releases

Toda tarefa de correção, melhoria ou nova função, incluindo documentação/CI que altere o projeto, começa por issue no GitHub do repositório correto. Pesquisar duplicatas; reutilizar issue aberta com o mesmo escopo. Uma issue por resultado verificável, não por chamada de ferramenta. Perguntas e diagnóstico exploratório sem mudança não exigem issue. Abrir a issue não aprova implementação nem antecipa campanha futura.

Antes de editar, registrar issue/URL, problema, escopo, critérios de aceite e validação. Trabalhar em branch própria ou worktree isolado quando houver trabalho concorrente; não misturar mudanças de outra tarefa. Se GitHub estiver indisponível, registrar o bloqueio e preparar diagnóstico/rascunho local, sem declarar issue criada.

Entregar por PR para a base correta. A descrição deve mencionar a issue: `Closes #N` quando a entrega completa a resolve, `Refs #N` em entrega parcial. Incluir comportamento alterado, verificações realmente executadas, limitações, riscos e rollback; evidência visual para UI. Usar draft enquanto houver pendências. Issues relacionadas à tarefa são autorizadas por este padrão; Gates 1/2, autorização de commit e critérios de merge permanecem vigentes. Não fechar issue manualmente antes do aceite da entrega.

Release/deploy deve ser rastreável ao PR aprovado e ao commit validado. Definir alvo (desktop, pacote, container, web local ou ambiente remoto), checks, smoke test e rollback antes de publicar. PR não dispara produção por si só; merge, publicação e deploy seguem as autorizações e o pipeline do projeto. Não publicar builds de branch não revisada nem habilitar serviços pagos silenciosamente.

Mudanças de UI, observabilidade e qualidade seguem o contrato de engenharia do projeto e a stack daquela fase. Selecionar ferramentas por capacidade/compatibilidade, não instalar todos os nomes de uma lista. Medir baseline antes de criar gates de cobertura/performance e separar política documentada de check realmente imposto por CI.

## Executor Fable e revisor Astra

Fable é o executor padrão no Claude Code; Astra é o revisor independente. Escolha explícita do usuário prevalece. Astra não assume implementação automaticamente. Sol ou Astra como executores exigem escolha explícita. Não mudar o modelo global nem a sessão atual silenciosamente.

O coordenador pode chamar Astra para uma revisão por tarefa aprovada, sem nova pergunta, quando o diff delimitado e as verificações estiverem prontos. Código relevante exige revisão independente; documentação simples recebe conferência local. Essa revisão substitui a chamada Terra/santa-loop padrão, evitando dois revisores pagos para a mesma etapa. Bloqueio do executor não autoriza transferir a implementação a Astra; registrar diagnóstico e solicitar orientação quando necessário.

Antes da chamada, persistir estado seguindo task-state.template.md: tarefa/escopo aprovados, executor=Fable, revisor=Astra, restrições explícitas, Gates 1/2, diff fixado, testes, arquivos permitidos e critério de término. O campo legado escaladas_automaticas contabiliza chamadas automáticas Astra, agora somente de revisão: marcar 1 e status=delegando antes da chamada. Não zerar a contagem de uma tarefa existente. Só o coordenador escreve estado; sem duas sessões coordenando a mesma tarefa.

Astra recebe brief autocontido, sem segredos: contrato, diff, testes, riscos e arquivos permitidos. Somente leitura; sem implementação, subdelegação, commit ou merge. Usar subagente nativo gpt-6-astra com instrução read-only quando exposto; senão codex exec --profile astra --sandbox read-only, validando ~/.codex/astra.config.toml e fornecendo prompt por stdin. Preservar permissões nativas, sem bypass. Exigir do chamador timeout de 10 minutos; sem retries automáticos. O limite de tempo não equivale a limite de tokens/assinatura.

Consumir a mensagem final da CLI, sem concatenar eventos intermediários: o piloto detectou aviso do claude-mem antes do JSON final. Registrar sessão, achados e evidências da revisão. Fable corrige os achados e roda as verificações; nova revisão LLM exige autorização explícita. Falha, timeout ou quota consomem a única tentativa automática; preservar estado e reportar revisão incompleta. Pedido de continuar não renova essa tentativa.

O piloto comparativo passou nas duas tarefas para ambos os modelos, mas não mediu superioridade de Astra como revisor nem execução autônoma desta política. A divisão dos papéis é a preferência aprovada pelo usuário.

## Delegação com contexto delimitado

Uma CLI externa inicia sua própria sessão: não presumir herança do catálogo, hooks, skills carregadas ou contexto do coordenador. Não reinstalar skills para corrigir uma chamada. Usar este contrato nas três CLIs, preservando as instruções obrigatórias do destino.

1. Classificar o pedido como revisão de diff, pesquisa ou implementação. A revisão automática Astra responde ao checklist do diff fixado; hipótese nova, varredura de corpus e experimento são pesquisa, não extensão silenciosa da revisão. Registrar lacunas e encerrar ao satisfazer o critério, sem buscar melhorias fora do escopo.
2. Enviar brief curto e autocontido: objetivo, tipo, cwd absoluto, branch/HEAD e identificação do diff, arquivos permitidos, restrições, critérios de término, testes já executados e dúvidas concretas. Anexar só evidência decisiva com arquivo:linha; logs completos ficam em arquivo. Não copiar histórico, catálogos ou manuais inteiros. Não resumir conjuntos/dados cuja diferença decide o achado.
3. Indicar somente skills necessárias, com caminho resolvido e motivo. No destino, distinguir instalada, descoberta, lida sem truncamento e aplicada com resultado verificável. Ler a skill selecionada separadamente; usar referências específicas e trechos consecutivos se necessário. Caminho ausente ou ferramenta não exposta exige registrar limitação e seguir o fallback documentado, sem inventar chamada nativa. A leitura do SKILL.md sozinha não prova aplicação.
4. Localizar com rg em arquivos/diretórios delimitados; para estrutura, usar Graphify explain e path com símbolos/IDs exatos antes de query aberta, conferindo o projeto do grafo. Depois ler função/bloco relevante, com arquivo:linha, e confirmar no código. Grafo orienta navegação, não substitui fonte; ausência de caminho não prova ausência de relação. Não repetir trecho inalterado já presente no contexto. Após compactação ou mudança do arquivo, recuperar apenas o necessário.
5. Agrupar leituras independentes pequenas, sem esconder skills em um lote grande. Mirar até 2.000 tokens de saída por ferramenta; ajustar explicitamente quando a evidência exigir. Limite de saída não garante completude: detectado truncamento, restringir a consulta e recuperar só a parte omitida, sem repetir o lote inteiro nem concluir sobre conteúdo invisível. JSON/CSV: selecionar colunas e linhas por código determinístico, guardando totais e dados decisivos. Python no Windows: configurar stdout UTF-8 antes de imprimir texto Unicode.

Antes de iniciar, preencher no brief:

```text
tipo / objetivo / criterio_de_termino:
cwd / branch / HEAD / diff_fixado:
arquivos_permitidos / restricoes:
evidencias_decisivas / testes_ja_executados:
skills_necessarias: caminho -> acao verificavel (ou nenhuma)
perguntas_delimitadas:
saida: achados com arquivo:linha, evidencias, limitacoes; sem repetir o brief
```

Retornar apenas resultado final ao coordenador; manter eventos completos no log local. Registrar ID da sessão, skills realmente aplicadas e lacunas. Medir chamadas, input total/cache/output separados, crescimento do contexto e tempo. Bytes removidos e tokens em cache não equivalem a economia comprovada de quota; comparar tarefas equivalentes antes de concluir.

O timeout de 10 minutos continua obrigatório no chamador. Uma ferramenta retornar um ID de background não prova que encerrará o processo nesse prazo: conferir o mecanismo do chamador e registrar timeout real ou limitação. Esta política não instala um supervisor nem impõe teto técnico de tokens.

## Descoberta, adoção e remoção de capacidades

Buscar capacidade nova somente após registrar um gap concreto e conferir recursos nativos,
conectores, MCPs, skills e padrões já disponíveis. `find-skills` permanece desabilitada no
catálogo padrão. Quando o gap justificar busca externa, usar sob demanda
`DO_NOT_TRACK=1 npx skills find "<capacidade específica>"`; nunca executar busca vazia,
`add` ou `update` automaticamente.

Resultado de busca é candidato, não recomendação. Fixar repositório, caminho, commit e
licença; auditar `SKILL.md`, scripts, referências, hooks, MCPs, rede, telemetria, permissões e
tratamento de segredos. Comparar com o dono atual usando fixture e critérios prévios. Só
instalar após issue própria, piloto isolado, ganho verificável e Gates 1/2. Manter a solução
atual até o candidato superar o baseline; popularidade, estrelas e bytes não provam qualidade,
segurança ou economia de tokens.

Antes de remover skill, MCP, plugin ou conector, medir invocações reais nos transcripts e
separar definições de ferramenta de chamadas executadas. Distinguir homônimos por prefixo e
origem, mapear dependências e confirmar o substituto já usado. Zero uso sem cobertura de
transcript vira lacuna de observabilidade, não autorização de remoção. Preferir desabilitação
reversível; cada lote de remoção usa issue, diff, rollback e Gates próprios.

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
