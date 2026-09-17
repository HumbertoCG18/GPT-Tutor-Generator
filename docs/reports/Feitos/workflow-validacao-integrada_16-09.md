# Workflow integrado e Context7 — 16/09/2026

## Resultado

Quatro passos executados em laboratório isolado. Claude planejou, AGY pesquisou, Sol implementou e uma sessão independente Codex Terra revisou. Roteamento supervisionado documentado em agent-workflow-lab/workflow.md; não foi criado um orquestrador automático entre CLIs. Enxame testado, não promovido. Nenhum código de produção do GPT Tutor alterado por esta tarefa; sem commit.

## Configuração e pesquisa

Chave válida do AGY sincronizada nos registros Context7 existentes de Claude e Codex. Igualdade das três credenciais verificada sem imprimir valores. Claude novo executou duas consultas Context7; Codex novo executou uma. Sessões já abertas podem exigir reabertura. Sem mudança de modelo global, plano pago ou ampliação global de permissões.

Contrato reutilizável: agent-workflow-lab/agents/agy-researcher.md. Resolver exige libraryName e query; query-docs exige libraryId e query. Limite de duas consultas por pesquisa; reutilizar ID conhecido. AGY recebe evals/research-output.schema.json por --json-schema; consumir structured_output, pois response pode concatenar objetos. Definição nativa de agente AGY continua não comprovada; contrato aplicado inline.

Regressão pytest passou: dois argumentos obrigatórios presentes, fato sobre monkeypatch.context com fonte pertinente. Holdout Python json.skipkeys passou reutilizando /python/cpython em uma consulta. Dois casos úteis nesta rodada; amostra insuficiente para afirmar confiabilidade geral. Auditoria dos tool calls reais: Claude 2 + Codex 1 + AGY 3 = 6. Acumulado conservador do piloto: 12/20 tentativas, restam 8. Não é o saldo oficial da conta.

## Fluxo e revisão

Claude Fable 5.1 produziu plano com contrato e fontes. Duas tentativas auxiliares de Read/Bash foram negadas pelo escopo restrito; plano entregue sem ampliar permissões. AGY Gemini 3.8 Flash low forneceu evidência. Executor recebeu plano e evidência comuns nos dois braços. Codex Terra medium revisou pacote fixado, sem ferramentas nem edição.

Baseline vermelho: 6 métodos de teste, 30 erros em subcasos. Ambos os braços passaram nos 6 métodos iniciais. Revisor encontrou falha média comum: fence JSON com CRLF rejeitado no Windows. Dois novos subcasos reproduziram dois erros em cada braço; correção mínima nos delimitadores da expressão regular. Resultado final: 6/6 métodos verdes em cada braço, incluindo os dois subcasos CRLF. Correção posterior não integra os tempos abaixo; versões anteriores preservadas.

## Solo versus enxame

| Braço | Agentes | Tempo de sessão | Tokens totais reportados | Entrada em cache |
|---|---:|---:|---:|---:|
| Solo | 1 | 48,979 s | 158.971 | 152.320 |
| Enxame | 3 | 59,407 s | 375.516 | 359.296 |

Mesmo modelo efetivo gpt-5.6-sol, esforço low, confirmado nos turn_context. O plano previa medium quando suportado; o launcher nativo herdou low igualmente nos dois braços. Tempo obtido dos timestamps das sessões: início do primeiro agente até término do último. Inclui escalonamento dos três lançamentos; exclui planejamento, pesquisa e revisão compartilhados. Três módulos independentes, nenhum arquivo compartilhado entre escritores; apenas resolver.py, context.py e response.py alterados em cada cópia.

Enxame 21,29% mais lento e 2,36 vezes os tokens reportados. Uma execução por braço, tarefa pequena, ordem fixa e cache não controlado. Tokens em cache não equivalem a cobrança ou quota. Não houve comparação entre modelos baratos/caros nem validação de produção. Decisão: execução solo como padrão; enxame continua experimental, até três trabalhadores e sem recursão.

## Verificações e proveniência

verify.py: ok=true, 75 arquivos gerenciados, nenhum erro. Auditoria literal da chave: zero ocorrências em 40 arquivos de saída, contrato e trajetórias selecionados; configurações e backups privados de configuração excluídos intencionalmente. Não equivale a auditoria de todos os logs do computador.

Artefatos locais: agent-workflow-lab/private/workflow-four-steps-20260916/. comparison.json e agent-usage.json contêm métricas; mcp-call-audit.json contém chamadas; codex-review.jsonl contém revisão; *-crlf-red.log e *-final-green.log preservam regressão e correção. Backups de configuração são privados e não devem ser publicados. Não publicar o diretório privado como pacote de evidências.

Aprendizagem proposta: manter caso CRLF no verificador e exigir chamada com schema + saída estruturada no contrato AGY. Sem edição automática de skills globais. Google Docs, Sheets e Drive excluídos.
