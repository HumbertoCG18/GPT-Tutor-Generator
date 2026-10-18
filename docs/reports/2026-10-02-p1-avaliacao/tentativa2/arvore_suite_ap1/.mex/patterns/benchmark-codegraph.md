# Comparar ferramentas de navegação de código

Usar quando avaliar substituição ou combinação de índices de código.

1. Congelar os fontes atuais (incluindo alterações locais) e guardar hashes. Definir
   perguntas e gabarito por leitura antes de consultar os índices; excluir ambos da indexação.
2. Fixar versões e arquivos incluídos. Separar índice AST de conteúdo semântico.
3. Normalizar somente o transporte: remover envelope JSON MCP, resolver nomes
   qualificados para arquivos existentes, respeitar escopos explícitos. Registrar
   truncamento e ambiguidades. Correções do harness valem para todos os braços.
4. Separar consultas fixas de agente autônomo, chamadas frias de MCP persistente,
   tokens reais de caracteres. Guardar pacotes, prompts/protocolo, saídas e hashes.
5. Pontuar símbolos/caminhos e evidências por fato; linha existente não basta.
   Reexecutar todos os hashes alterados, nunca somente respostas erradas. Testar
   remoção e adição de uma relação em cópia isolada.

Harness reproduzível: `docs/reports/_codegraph-benchmark/PROTOCOL.md`.
Medições e decisão: relatório em `docs/reports/Feitos/benchmark-codegraph_15-09.md`.
Índices maiores não provam qualidade; leitura de fonte pode equalizar resultados.
Piloto sem perguntas inéditas não demonstra superioridade geral.
