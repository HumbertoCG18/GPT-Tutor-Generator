# Context7 e segredos

Configuração nativa por CLI. Chave somente nos arquivos locais autorizados, nunca em prompts, relatórios, git ou argumentos de shell. Escopo de permissão restrito às consultas resolve-library-id e query-docs quando o cliente exigir. Plano pago não autorizado. Limite atual do piloto e consumo ficam no tracker do projeto, sem duplicar números aqui.

Catálogo instalado, descoberta, chamada executada e resposta correta são quatro evidências distintas. Configurar uma chave não atualiza necessariamente uma sessão já aberta.

No AGY, enviar o schema de saída com --json-schema e consumir structured_output do envelope JSON. response pode concatenar objetos; não usar como JSON puro. Conferir também denied_actions e fatos/fontes. Contrato de saída do piloto: ../evals/research-output.schema.json.
