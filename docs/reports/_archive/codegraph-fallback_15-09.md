# Graphify primeiro, CBM como fallback — 15/09/2026

Desenho aprovado: cada índice lê os fontes; nenhuma sincronização grafo→grafo.
O roteamento é instrução ao agente, não um hook que bloqueia consultas duplicadas.
Continua existindo sobreposição de processamento e armazenamento entre índices.

## Ajuste posterior: atualização sob demanda

Após aprovação do usuário, auto_watch=false aplicado e auto_index=false confirmado
por config list. Configuração pessoal: afeta todos os projetos que usam esse CBM.
Atualizar explicitamente antes do primeiro fallback da sessão e após mudar fontes;
reutilizar nas consultas seguintes enquanto os fontes permanecerem iguais.
Graphify mantém os hooks. Bancos existentes preservados; não elimina a sobreposição
em disco, mas desabilita a atualização contínua do segundo índice.
As medições abaixo descrevem a configuração anterior com watcher ligado.

## Aplicado inicialmente

- ROUTER aponta para a política em .mex/patterns/codegraph-fallback.md.
  Graphify explain/path primeiro; CBM somente para lacuna, ambiguidade ou falha.
  Divergência resolvida por fonte atual, não por votação entre ferramentas.
- .graphifyignore e .cbmignore excluem vendor, minificados, graphify-out,
  .codebase-memory, .cache, __pycache__ e docs/reports/_codegraph-benchmark.
  .gitignore também exclui o artefato compartilhável .codebase-memory.
- Hooks Graphify post-commit/post-checkout preservados. Nenhum hook/watch novo.
  Ponteiro local de Python alinhado ao Python311 dos hooks (Graphify 0.9.42);
  valor anterior preservado em graphify-out/.graphify_python.before-cbm.
- CBM 0.10.8 permanece no Codex. auto_watch=true e auto_index=false preservados.
  Índice vivo criado com nome canônico e persistence=false. Nenhum artefato
  comprimido duplicado no repositório; banco local continua no cache nativo.

## Validação

Harness: docs/reports/_codegraph-benchmark/check_native_sync.py.
Cópia isolada do arquivo real src/builder/timeline/unit_labels.py; SHA256 registrado.
Git próprio, cópias dos dois hooks existentes e sessão MCP persistente com roots.
Sem commits, checkout ou mudanças em src do projeto vivo.

1. Renomear função e chamada, commit: Graphify e CBM refletem nome novo sem antigo.
2. Excluir arquivo, commit: ambos removem os símbolos.
3. Trocar para branch que conserva o arquivo: ambos restauram os símbolos.

Os três eventos passaram sem refresh explícito entre mutação e consulta.
Polling do teste: 2 s. Tempos são de uma cópia pequena após retorno do Git;
não representam latência garantida no projeto completo.
Evidência final: native-sync-results.json e resultado individual em native-sync/.

Sentinelas nos seis diretórios excluídos ausentes nos dois índices iniciais.
Após atualização do Graphify vivo: zero nós com fonte no novo benchmark.
CBM vivo: search_graph com filtro de arquivo do benchmark retorna total=0.
Logs: live-graphify-update.log, live-cbm-index.json, live-cbm-exclusions.json.

## Limites encontrados

O alias passado em index_repository.name criou índice consultável, mas sem
atualização automática durante 100 s. Oferecer roots não corrigiu o alias.
Usar o nome canônico resolveu; o watcher nativo registra o projeto derivado da
raiz da sessão. Evidência negativa inicial em native-sync-no-roots.json.
Fonte oficial: [registro do watcher v0.10.8](https://github.com/DeusData/codebase-memory-mcp/blob/v0.10.8/src/daemon/application.c).

Graphify: mudanças não commitadas exigem graphify update . antes da consulta;
os hooks não acompanham cada salvamento. Documentos semânticos não são
reprocessados pelo refresh AST. A atualização viva avisou 183 arquivos sem nós.
CBM: depende de sessão MCP ativa na raiz correta. O índice vivo reportou quatro
arquivos parcialmente analisados e nenhum skipped; não é garantia de completude.
Falhas/parcialidade pedem leitura do fonte, como definido na política.

Nenhuma API/LLM usada nesta integração. claude-mem permanece fora deste mecanismo.
