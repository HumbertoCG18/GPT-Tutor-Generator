---
name: delegar-codex-agy
description: Delegação headless com escopo, skills verificadas e leituras delimitadas.
triggers:
  - "segunda opiniao"
  - "revisor B"
  - "ler o corpus com o Gemini"
  - "codex exec"
  - "agy -p"
last_updated: 2026-09-17
---

# Delegar ao Codex e ao AGY

Política + template de brief: [workflow](../../.workflow/workflow.md), seção
"Delegação com contexto delimitado". Fonte: agent-workflow-lab/workflow.md.
Fable executa; Astra revisa uma vez, somente leitura; AGY pesquisa.
CLI externa não herda automaticamente skills, hooks nem contexto do Claude Code.

## Chamada e contrato

1. Fixar tipo/escopo, cwd absoluto, HEAD/diff, arquivos, evidências, testes e término.
   Persistir estado antes da chamada. Hipóteses e corpus amplo são pesquisa,
   não revisão automática de diff. Não reenviar conversa inteira.
2. Codex: quando não houver subagente nativo exposto, usar no Bash:
   `codex exec --profile astra --sandbox read-only -C "<repo-absoluto>" -o "<final.md>" - < "<brief.md>"`.
   O arquivo fecha stdin. Guardar eventos/stderr em log separado; consumir apenas
   final.md. Sem terceiro voto/santa-loop, subdelegação ou retry automático.
   Chamador controla 10 minutos; background não comprova encerramento por timeout.
3. AGY: contrato inline em `.workflow/agents/agy-researcher.md`. Para corpus:
   `agy -p "<pergunta com caminhos absolutos>" --add-dir "<diretorio-absoluto>" --model gemini-3.8-flash-medium --output-format json --json-schema '<schema-JSON>'`.
   Para texto pequeno, fornecer pergunta + dados pelo stdin, omitindo `-p`.
   Schema: `.workflow/evals/research-output.schema.json`. Consumir `structured_output`;
   validar schema, fontes e `denied_actions`. `response` pode concatenar objetos.
   `SUCCESS` sozinho não prova êxito. Quota esgotada salva estado, sem troca automática.
4. No destino, verificar skills necessárias: caminho, leitura sem truncamento e
   ação correspondente no log. Catálogo não é execução. Usar Graphify explain/path
   por ID, depois código por função/trecho. Não reinstalar nem ampliar permissões.
5. Devolver achados com arquivo:linha, evidência, limitações e ID da sessão.
   Coordenador confere; eventos intermediários ficam fora do seu contexto.

## Leitura eficiente

- `rg -n` em caminhos delimitados localiza; linhas/símbolo confirmam.
  Ler o arquivo inteiro na memória do processo não significa enviá-lo ao modelo.
- Agrupar trechos pequenos independentes; ler skills separadamente. Não repetir
  intervalos inalterados já vistos. Truncamento: recuperar apenas a parte omitida.
  Preferir função completa quando linhas soltas omitem contexto necessário.
- Contagens, filtros e joins de CSV/JSON: código determinístico local.
  AGY interpreta o recorte; preservar dados decisivos, denominadores e artefato completo.
- Python no Windows: `sys.stdout.reconfigure(encoding='utf-8')` antes de imprimir.
  Saída inicial alvo de 2.000 tokens por ferramenta, ajustável pela evidência;
  não é teto da sessão nem garantia de completude.

## Verificação e limites

Codex: `~/.codex/sessions/<AAAA/MM/DD>/rollout-*.jsonl`.
AGY: `~/.gemini/antigravity-cli/conversations/<conversation_id>.db`.
Citar o ID ao delegar. Codex registra tanto `function_call` quanto `custom_tool_call`;
contar só o primeiro perde chamadas via code mode.

Separar input acumulado, cached_input_tokens, output e contexto por turno.
Identificar janela de quota por `window_minutes`, sem presumir primary=5h.
Percentuais incluem arredondamento e podem incluir outras sessões; não são fórmula
de cobrança. Bytes removidos não provam economia de quota.

AGY print mode pode usar workspace scratch: caminhos absolutos + `--add-dir`.
Não ampliar permissões de shell. `-p` e stdin não se combinam.
Para `/quota`, preferir PowerShell: MSYS no Bash pode converter o comando em caminho.
Não executar consultas de modelo como teste de instalação.

Medição sem LLM: [auditoria 17/09](../../docs/reports/2026-09-17-auditoria-delegacao-leituras.md).
