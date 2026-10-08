# Piloto Context7 — 16/09/2026

Autorização: validar integração existente, teto de 20 chamadas, sem contratar plano ou ampliar permissões globais. Google Workspace fora do escopo.

## Retomada com chave substituída pelo usuário

Autenticação passou no AGY 1.2.4. Permissões continuam somente no projeto isolado. Nenhuma propagação da nova chave para Claude/Codex executada.

| Pesquisa | Tentativas MCP Context7 | Resultado |
|---|---:|---|
| Python json.dumps | 2 | Útil: 3/3 fatos corretos, fontes CPython; resposta veio em bloco Markdown apesar do pedido JSON puro |
| pytest monkeypatch | 1 | Falhou: resolve-library-id enviado apenas com libraryName, sem query; nenhuma documentação útil |
| Python json.loads, ID reaproveitado | 1 | Útil: 2/2 fatos corretos; uma URL irrelevante também listada e reconhecida como ruído |

Aceite: 2/3 pesquisas úteis, 5/5 fatos corretos nas respostas úteis; não confundir esse denominador com cobertura de todos os pontos das três pesquisas. A resposta de falha atribuiu o problema a query em vez de libraryName; trajetória mostra Arguments={libraryName:pytest}, ou seja, query omitida. Falha do executor, não de autenticação. ID /python/cpython reaproveitado sem repetir resolve-library-id: uma resolução evitada por instrução explícita, sem cache automático implementado.

Orçamento conservador acumulado: 6/20 tentativas, incluindo 2 rejeições de chave anteriores e a tentativa com schema inválido. Cobrança efetiva da tentativa inválida não verificada. Uma repetição diagnóstica anterior; nenhuma repetição automática nas três pesquisas atuais. Não é necessário consumir as 14 restantes.

Três execuções atuais: 43,711 s somados conforme duração do CLI; total_tokens=143377, cache_read_tokens reportado separadamente. Nenhuma medição monetária, de saldo ou de economia de assinatura. Modelo solicitado gemini-3.8-flash-low. Uma execução por caso: não estabelece taxa geral de sucesso.

Artefatos atuais na pasta privada do piloto: python-valid-key.json, pytest.json, reuse.json, respectivos .stderr e resume-audit.json. Conversas: 77998fcf-1178-42ce-8785-98f3e4040aea, 498f3685-3297-4e1d-a9b9-9a85a58370c1, a638256f-f780-4001-abcf-a8f4d01ed3ee. Contagem obtida dos registros estruturados de chamadas nas trajetórias SQLite, excluindo leituras de schema e de saída documental.

Proteção da chave: não incluída em prompt, argumentos de shell ou saídas desta conversa. Captura do subprocesso sanitizada em memória antes de gravar. Varredura literal em 15 arquivos (saídas selecionadas, logs recentes e três bancos de trajetória): 0 ocorrências. Não é garantia sobre logs não examinados. Configuração local permanece o armazenamento autorizado. Verificação final dos 75 arquivos gerenciados: sem drift.

Limite adicional do coletor: impressão da terceira resposta falhou com UnicodeEncodeError/cp1252 depois de o JSON já estar salvo; não repetimos inferência. A resposta contém mojibake em acentos. Conteúdo técnico conferido na documentação oficial: https://docs.python.org/3/library/json.html . Registro bruto preservado.

Decisão: integração autenticada e útil para consultas delimitadas, com leitura de schema e conferência das fontes; não promover pesquisador autônomo irrestrito ou enxame. Pendências: robustez de argumentos, formato da saída e fontes irrelevantes. Piloto encerrado dentro do teto.

## Resultado

Permissão MCP resolvida no projeto isolado; pesquisa bloqueada por credencial rejeitada. Executadas 2/20 chamadas remotas Context7: 1 resolve-library-id pelo AGY e 1 repetição direta diagnóstica. Ambas retornaram `Invalid API key. Please check your API key. API keys should start with 'ctx7sk' prefix.` Zero respostas documentais úteis; nenhuma query-docs executada. Não demonstrada economia nem qualidade da pesquisa.

O cabeçalho local contém chave não vazia com prefixo ctx7sk-. A mesma chave consta na configuração Claude. A chamada direta enviou o cabeçalho configurado para https://mcp.context7.com/ e recebeu HTTP 200 com erro textual no resultado MCP; HTTP 200 não prova autenticação bem-sucedida. Causa específica da rejeição (revogação, valor incorreto etc.) não determinada. Não expor a chave nos relatórios.

## Configuração e rastreabilidade

- Projeto descartável AGY: `0d57185d-98a0-41e1-8cf0-4c6e9e0f315c`, nome `Context7 pilot 20260916`; único recurso é a pasta privada do piloto.
- Permissões criadas pelo editor nativo /permissions, escopo Project: `mcp(context7/resolve-library-id)` e `mcp(context7/query-docs)`. Nenhum wildcard, bypass ou mudança de permissões globais.
- Log `cli-20260916_011220.log`: `ApplyProjectPermissionGrants: stored 2 allow, 0 deny grants from project "Context7 pilot 20260916"`.
- Arquivo de projeto gerado pelo CLI contém permissionGrants.permissionGrants.allow; preservar formato observado, não inferir schema a partir de exemplos antigos.
- AGY atualizou automaticamente de 1.2.3 para 1.2.4 durante abertura interativa. Comparação com teste anterior não isola versão.
- `-i /permissions` foi tratado como prompt pelo modelo; interrompido. Digitar /permissions no TUI abriu o editor correto. Essa preparação teve inferência adicional, fora da métrica da pesquisa; consumo não consolidado.
- Pesquisa: gemini-3.8-flash-low solicitado; conversa `93f7bf8e-4f19-4cde-87e9-2be243b26ba5`; 10,156 s e total_tokens=30320, cache_read_tokens=61080 separados conforme JSON do CLI. Não converter em custo monetário.
- Trajetória SQLite read-only: passos de ferramenta 3/6 são view_file dos schemas; passo 9 é call_mcp_tool/context7/resolve-library-id. Leituras de schema não contam como consultas Context7. Nenhuma negação reportada nesta pesquisa.
- Resposta não cumpriu JSON puro (prosa + bloco JSON). Conteúdo corretamente declarou erro e não inventou documentação.

Evidências: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/context7-pilot-20260916/python.json, python.stderr, direct-auth.txt. O projeto do GPT Tutor existente não foi editado; a entrada descartável criada inicialmente com cwd do GPT Tutor foi renomeada e teve o recurso substituído pela pasta isolada antes da pesquisa.

## Bloqueio anterior, superado na retomada acima

Substituir a credencial Context7 por chave válida usando armazenamento local, sem colar em conversa; confirmar plano Free no dashboard. Retomar o piloto com no máximo 18 chamadas restantes, contabilizando repetições. Não gastar o saldo repetindo autenticação rejeitada.

Referência de permissões: https://antigravity.google/docs/cli/permissions/ . Plano gratuito e limite: https://context7.com/plans . Plano/saldo da conta não verificados.
