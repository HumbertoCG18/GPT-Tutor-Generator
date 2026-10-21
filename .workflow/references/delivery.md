# Issues, PRs e releases

Aceite é evidência por critério, não só contagem de testes: registrar commit/diff, comando,
resultado e pendência em `evidencia_de_aceite`. Para desktop, separar verificação automática,
build, instalação autorizada e validação nativa. A instalação necessária ao teste visual
pode ocorrer com autorização do dono antes do aceite visual; marcar esse aceite pendente.
Não exigir que o usuário valide uma atualização ainda não instalada.
Registrar manifesto/commit/SHA256 em `artefato_instalado` e cenário/resultado/captura em
`validacao_nativa`; quando houver regressão de desempenho, medir RAM/CPU no cenário real.
Ausência de ferramenta nativa é limitação registrada, nunca "UI validada" por teste de componente.
CI deve cobrir a base real do PR (`dev` quando adotada), mantendo os checks existentes;
job ausente não equivale a job verde. Snapshot do workflow é promovido junto da campanha,
sem sobrescrever worktrees com WIP; `verify.py --projects-only` mostra drift por checkout.

Toda tarefa de correção, melhoria ou nova função, incluindo documentação/CI que altere o projeto, começa por issue no GitHub do repositório correto. Pesquisar duplicatas; reutilizar issue aberta com o mesmo escopo. Uma issue por resultado verificável, não por chamada de ferramenta. Perguntas e diagnóstico exploratório sem mudança não exigem issue. Abrir a issue não aprova implementação nem antecipa campanha futura.

Em arquitetura, refatoração ou feature, ler o mapa do projeto e apenas o estado/handoff do domínio antes do plano. Antes de editar, registrar issue/URL, problema, escopo, fora de escopo, suposições em aberto, critérios de aceite e validação. Manter a mudança no escopo aprovado e no estilo local; premissa que mude arquitetura ou aceite é declarada e resolvida por evidência. Em refatoração, comparar baseline e depois, separando falhas anteriores. Remover órfãos criados pela própria alteração depois de conferir os consumidores; órfão de legado alheio vira pendência. Trabalhar em branch própria ou worktree isolado quando houver trabalho concorrente; não misturar mudanças de outra tarefa. Antes de publicar uma branch derivada, conferir `git log origin/<base>..HEAD`: não publicar commits de outra frente sem autorização; rebasear sobre a base publicada quando necessário. Se GitHub estiver indisponível, registrar o bloqueio e preparar diagnóstico/rascunho local, sem declarar issue criada.

Entregar por PR para a base correta. A descrição deve mencionar a issue: `Closes #N` quando a entrega completa a resolve, `Refs #N` em entrega parcial. Incluir comportamento alterado, verificações realmente executadas, limitações, riscos e rollback; evidência visual para UI. Usar draft enquanto houver pendências. Issues relacionadas à tarefa são autorizadas por este padrão; Gates 1/2, autorização de commit e critérios de merge permanecem vigentes. Não fechar issue manualmente antes do aceite da entrega.

Contrato pós-PR (babysit): depois de abrir o PR, tratar três pendências por rodada: conflito de merge (rebasear sobre a base e resolver), CI vermelho (corrigir a causa) e comentário de review (responder ou corrigir). Máximo de 3 rodadas; se restar pendência, devolver ao dono com o estado (checks, comentários abertos, conflito). Não editar teste para passar: falha de teste se corrige no código, ou o teste só muda com evidência de que estava errado, registrada no PR. Também não afrouxar regra, gate ou configuração para passar; mudança de configuração exige aprovação do dono. Falha de CI se investiga só lendo (log, diff, workflow). Teste local verde não prova o CI remoto. Investigar não autoriza push, rerun nem merge.

Release/deploy deve ser rastreável ao PR aprovado e ao commit validado. Definir alvo (desktop, pacote, container, web local ou ambiente remoto), checks, smoke test e rollback antes de publicar. PR não dispara produção por si só; merge, publicação e deploy seguem as autorizações e o pipeline do projeto. Não publicar builds de branch não revisada nem habilitar serviços pagos silenciosamente.

Mudanças de UI, observabilidade e qualidade seguem o contrato de engenharia do projeto e a stack daquela fase. Selecionar ferramentas por capacidade/compatibilidade, não instalar todos os nomes de uma lista. Medir baseline antes de criar gates de cobertura/performance e separar política documentada de check realmente imposto por CI.
