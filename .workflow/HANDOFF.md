# Retomar no Claude Code

Ler README.md e workflow.md nesta pasta. Fable executa; Astra revisa somente leitura,
com no máximo uma chamada automática por tarefa relevante. Fable corrige os achados.
Escolha explícita prevalece; gates, escopo e permissões permanecem aplicáveis.

A rodada de configuração e o piloto comparativo terminaram. Não repetir testes ou
chamadas de modelo apenas ao abrir a sessão. A lista de pendências não é uma tarefa nova aprovada;
consultar PENDING.md para os aceites ainda abertos.

Para a tarefa de produto escolhida pelo usuário, ler .mex/ROUTER.md, tracker e handoff
vivos. Conferir branch/HEAD e alterações locais antes de editar. Preservar trabalho de
outras sessões. Estado concluído em .workflow-local/active-task.md não deve ser reaberto
para renovar o limite de chamadas. Nova tarefa recebe ID próprio e escopo aprovado.

Usar contratos de agents/ inline se o papel nativo não estiver disponível. Não inferir
registro nativo a partir de arquivo instalado. Consumir o artefato final do Codex, não a
concatenação de mensagens: o piloto observou aviso do claude-mem antes do JSON final.
Não reiniciar o worker por quota. Credenciais ficam nas configurações locais, nunca no brief.

Commits desta rodada são locais; nenhum push foi solicitado. A continuação normal é
trabalhar na tarefa que o usuário escolher, não abrir outra rodada de configuração.
