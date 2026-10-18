# Graphify com fallback estrutural

1. Localizar o símbolo; consultar Graphify com explain/path. Se suficiente, parar.
2. Se faltar cobertura, houver ambiguidade ou falha, consultar codebase-memory-mcp
   no projeto correspondente à raiz atual. Nunca consultar índices do benchmark
   como se fossem o repositório vivo. Confirmar a raiz com list_projects e atualizar
   explicitamente o índice antes do primeiro fallback da sessão ou após mudar fontes.
3. Usar search_graph/trace_path ou query_graph restrito ao símbolo/arquivo.
   Resultado vazio não prova ausência: verificar cobertura e ler o fonte relevante.
4. Em divergência, conferir o arquivo atual e a atualização dos índices. O fonte
   decide; não unir respostas contraditórias nem copiar arestas entre ferramentas.

## Atualização e exclusões

- Cada ferramenta lê os fontes e grava apenas o próprio índice. Os dois continuam
  extraindo estruturas parcialmente iguais; não há deduplicação de armazenamento.
- Graphify: manter os hooks nativos post-commit/post-checkout. Para alterações ainda
  sem commit, executar graphify update . ao finalizar o lote, antes de consultá-lo.
  Não instalar um segundo watcher ou hook para disparar ambos.
- CBM sob demanda: manter auto_watch=false e auto_index=false na configuração
  pessoal (vale para todos os projetos desse usuário). Quando o fallback for
  necessário, executar index_repository na raiz correta com persistence=false e
  sem substituir name. Aguardar sucesso antes de consultar. Reutilizar o índice
  nas consultas seguintes da sessão enquanto os fontes não mudarem; se houver
  dúvida de frescor, atualizar. Falha de atualização exige leitura direta do fonte,
  sem tratar o índice antigo como atual. Não indexar CBM ao iniciar sessão, salvar,
  fazer commit ou trocar branch; não criar hooks para esses eventos.
- .graphifyignore e .cbmignore excluem índices, caches, vendor e o harness de
  comparação. Ambos também respeitam .gitignore. Ao mudar exclusões, atualizar os
  índices existentes; a regra sozinha não demonstra remoção dos nós antigos.
- Usar o Python apontado por graphify-out/.graphify_python, alinhado ao dos hooks.
  Não recriar esse ponteiro a partir de uma instalação uv antiga.

É uma política de consulta para o agente, não um bloqueio técnico a duas chamadas.
Não habilita memória de conversas nem substitui o observer do claude-mem.
