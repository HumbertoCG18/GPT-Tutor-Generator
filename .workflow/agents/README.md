# Papéis usados inline

Estes arquivos são contratos de execução, não prova de registro ou disponibilidade de subagentes nativos. Quando o papel nativo não estiver exposto, ler sua definição e executar a etapa inline na sessão atual.

O frontmatter `model`/`tools` dos papéis importados do ECC preserva metadados de origem Claude. No uso inline, ignorar esses campos: usar somente as ferramentas realmente expostas pela CLI e o executor definido em [workflow.md](../workflow.md). Fable/Astra seguem esse roteamento; ler um papel não troca o modelo da sessão nem autoriza uma chamada adicional.

- [tdd-guide.md](tdd-guide.md): implementação seguindo o contrato e verificações do projeto.
- [python-reviewer.md](python-reviewer.md): revisão do diff Python delimitado.
- [agy-researcher.md](agy-researcher.md): pesquisa documental com fontes e orçamento de consultas.
- [agy-doc-updater.md](agy-doc-updater.md): edição documental restrita aos alvos aprovados, com fontes MEX/Graphify.

As instruções do projeto e os Gates 1/2 continuam aplicáveis. Não inventar chamadas de subagente ou substituir ferramentas por nomes de outra CLI. Se faltar uma capacidade necessária, registrar o bloqueio e o próximo passo no handoff.
