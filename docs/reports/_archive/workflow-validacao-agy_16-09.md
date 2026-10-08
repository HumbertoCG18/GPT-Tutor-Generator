# Validação dos papéis AGY — 16/09/2026

Autorizado: testar pesquisa com fontes e atualização documental isolada. Google Docs/Sheets/Drive excluídos. Nenhuma configuração global alterada.

## Medido

AGY 1.2.3; modelo solicitado gemini-3.8-flash-low, listado por agy models. Log do controle registra resolução e propagação desse modelo; não é auditoria do modelo servido pelo provedor em cada chamada.

| Caso | Resultado | Segundos reportados | total_tokens reportados |
|---|---|---:|---:|
| Seleção --agent docs-lookup | AGENT_READY; carregamento da definição não comprovado | 2,615 | 21553 |
| Pesquisa Context7 | Reprovado: MCP negado, resposta vazia, apesar de status SUCCESS | 1,615 | 21722 |
| Síntese com fonte inline | 3/3 fatos corretos, 3 URLs, limitação explícita | 2,911 | 21872 |
| Edição de cópia do README | Um parágrafo alterado; restante byte a byte preservado | 11,080 | 35571 |

Quatro chamadas; soma de total_tokens=100718. A edição também reporta cache_read_tokens=57011 separadamente; não somar nem converter em custo monetário sem conhecer a semântica de cobrança. Durações são as reportadas pelo CLI, não tempo total de shell. Uma execução por caso, sem comparação entre modelos nem prova de economia de quota.

Pesquisa: json.dumps, tipo str, ensure_ascii=True, allow_nan=False produz ValueError para NaN. Coordenador conferiu https://docs.python.org/3/library/json.html. Na tentativa autônoma, denied_actions=[{action:mcp,display_name:CallMcpTool}]. O fallback recebeu trecho fornecido, usou zero ferramentas e declarou não ter pesquisado autonomamente.

Documentação: cópia real do README do agent-workflow-lab, evidência dos testes locais. Papel inline adaptado: atualizar documento existente, sem CODEMAPS. Execução --mode accept-edits com --add-dir apontando somente a cópia. Validação por Python confirmou prefixo/sufixo byte-idênticos fora do parágrafo, README original com mesmo hash, workspace com apenas README.md/evidence.txt. Nenhuma negação reportada nesse caso. A presença de dois arquivos verifica o workspace observado, não constitui sandbox completo do filesystem.

Verificador final: ok=true, managed_skill_files=75, errors=[].

## Portabilidade e conclusão

agy agents retornou vazio. --agent docs-lookup foi aceito e respondeu, mas esse controle não comprova que a definição ECC foi carregada. Não declarar aliases haiku/sonnet/opus compatíveis nem incompatíveis a partir disso. Subagentes nativos e enxame não testados; fallback inline foi o mecanismo validado para edição.

Aceite limitado: síntese de fonte fornecida e edição documental delimitada aprovadas nesses dois casos. Pesquisa autônoma headless via Context7 bloqueada por permissão MCP. Próxima validação requer permissão específica na superfície de execução, preservando o escopo; não usar bypass global.

## Evidências locais

Diretório: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/agy-docs-validation-20260916.

- agent-selection.json: conversa 7170746e-78de-4f98-8329-0f6c0a7c0589.
- research.json/.stderr: dc734421-b416-47a2-b2da-2684b9e0a96c.
- research-inline.json/.stderr: e7b68255-ba0f-4bda-95b0-4b855593c12b.
- doc-edit.json/.stderr: 131f077d-2885-4150-b7e6-eafc8c37e6d3.
- README.before.md e workspace/README.md: comparação reproduzível do parágrafo AGY, delimitado pelo próximo item Codex.

Decisão proposta: usar AGY como sintetizador e editor documental supervisionado; manter coleta MCP e roteamento nativo como pendências antes do enxame. Não instalar skills adicionais para contornar uma negação de permissão.
