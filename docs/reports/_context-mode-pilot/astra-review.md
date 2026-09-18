# Revisão Astra — Context Mode MCP

Revisão única, somente leitura, antes do resultado final.

## Achados aplicados

1. **BLOQUEIA:** não inferir capacidade por nome de tool. Conclusão limitada à rota ensaiada.
2. **BLOQUEIA:** saída e recomposição precisavam ser byte-determinísticas. Fixture mudou para
   `stdout.buffer` com LF; busca passou a recompor linhas completas e comparar SHA-256.
3. **AJUSTE:** preservar resultado integral e proveniência. Harness agora exige diretórios novos,
   grava resultado privado integral e artefato público sanitizado com versões/hash do bundle.
4. **AJUSTE:** scan do segredo precisava incluir wire, falhar em erro de leitura e aguardar threads.
5. **AJUSTE:** isolamento precisava ser medido. Ambiente filho virou allowlist; quatro configs e
   bundle recebem hash antes/depois.

Após as correções, a execução final passou 10/10 checks. Não houve segunda chamada Astra.

