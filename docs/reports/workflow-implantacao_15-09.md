# Implantação do workflow comum — 15/09/2026

Escopo autorizado: Claude Code, Codex e AGY; skills pessoais, seleção do catálogo,
CBM e piloto RTK. Sem alteração de fontes do GPT Tutor, commit ou API paga nova.
Aceite via Alethe ainda pendente; não declarar validação completa da aplicação.

## Aplicado

| Superfície | Resultado |
|---|---|
| Skills pessoais | Seis fontes comuns; 75 arquivos distribuídos e conferidos por hash nos três destinos |
| Graphify | Preservadas as correções PowerShell da cópia Claude; variante Codex redundante desabilitada. Claude expõe /graphify pela pasta; Codex/AGY usam graphify-windows do metadata |
| Skills aprendidas | Correções de caminhos/nome claude-mem preservadas; YAML das três descrições corrigido para o parser estrito do AGY |
| Codex | 24 habilitadas no catálogo pessoal final, sem nomes ativos duplicados; Companion desabilitado apenas no Codex |
| GPT Tutor | Sete extras de domínio declarados na seleção completa do projeto; arrays não herdam os itens globais |
| Claude | Companion preservado; helpers de processo concorrentes retirados do acionamento; papéis ECC nativos tdd-guide/python-reviewer confirmados |
| AGY | Seis skills pessoais descobertas uma vez cada em .gemini/config/skills; referências externas em skills.json não funcionaram neste teste |
| MCP CBM | Registrado nas três CLIs; auto_watch=false e auto_index=false confirmados |
| RTK | 0.49.0 em ~/.local/bin/rtk.exe, checksum do release verificado; uso explícito com pytest |
| Instruções | Três arquivos pessoais idênticos, com política de RTK, fallback e papéis ECC inline quando não houver subagente nativo |

O catálogo Codex via skills/list reflete a seleção pessoal; config/read com cwd
confirma a seleção do projeto. Não confundir os dois nem somar as cópias em cache.
Apps/conectores da aplicação podem acrescentar skills fora desse catálogo local.
No Claude, as skills aprendidas foram colocadas diretamente em .claude/skills:
a descoberta real não expôs as cópias aninhadas em learned/. Originais arquivados.

## Verificação executada

- Três sessões diretas Codex: WORKFLOW_OK, sem aviso de descrições reduzidas e sem
  clamping SessionEnd. Uma nova sessão dentro do Alethe ainda depende de confirmação.
- Claude: inicialização real e conexão CBM. AGY: descoberta via /skills sem inferência.
- CBM: initialize, tools/list e list_projects responderam nas configurações das
  três CLIs; versão 0.10.8, 15 ferramentas. Nenhuma indexação nessa verificação.
- AGY pelo agente headless: tentou codebase-memory-mcp/list_projects, mas a permissão
  MCP foi negada por impossibilidade de perguntar. Permissões preservadas; o teste
  direto de transporte passou. Não equivale a execução irrestrita pelo agente.
- Verificador: zero drift em 75 arquivos. Controle negativo alterou uma fonte no
  laboratório, detectou drift e restaurou o arquivo; controle final passou.

## RTK: medições e limite de adoção

Três repetições por braço/comando. Bytes incluem stdout+stderr; não são tokens,
faturamento, quota economizada ou avaliação de diagnóstico por agente autônomo.

| Caso | Redução mediana | Exit code | Fatos verificados |
|---|---:|---|---|
| pytest: 40 aprovados sintéticos | 99,52% | Preservado | Contagem de aprovados |
| pytest: uma falha sintética | 75,94% | Preservado | Nome do teste, esperado, obtido e contagem de falhas |
| git status | 1,86% | Preservado | Não avaliados integralmente; não promovido |
| git diff --stat | 66,68% | Preservado | Não avaliados integralmente; não promovido |
| rtk grep versus rg | Incomparável: falhou | Divergiu | Dependência grep ausente; não promovido |

Recall da falha recuperou a saída completa. rtk rg existe e executou, mas não recebeu
o mesmo aceite comparativo. Nenhum hook de reescrita geral instalado. Em ambiente
sem pytest no PATH, manter o runner original do projeto.

## Skillfile: piloto não promovido

Release 1.9.1, checksum verificado. Duas skills e três destinos descartáveis:
validate e duas instalações passaram. Ao corrigir fonte local e instalar novamente,
a cópia já existente no AGY ficou antiga; diffs de entradas locais não são suportados.
Portanto, não depender de Skillfile para atualização automática dessas fontes.
Teste de conflito/patch remoto não foi executado: o caso local já falhou no requisito.

Fonte comum e distribuição manual conferida por hash ficaram como fallback do plano.
Skillfile permanece somente no laboratório; Kasetto, Headroom, Hermes, DeerFlow,
OmniRoute, Doberman, TruthProbe e observador adicional não foram instalados.
ClaudeHUD/MemoryTrim continuam opcionais, sem necessidade demonstrada.

## Artefatos e reprodução

Laboratório: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab.
Repositório Git inicializado, sem commit/remoto. README contém operação/rollback.

- verify.py: integridade das skills, instruções, CBM, seleção e RTK; sem inferência.
- catalog.py: catálogo Codex e configuração efetiva; dados privados ficam em private/.
- probe_mcp.py: teste local das três configurações MCP; sem modelo/indexação.
- validation.json, mcp-check.json, rtk-benchmark.json: resultados estruturados.
- deployed-skills.json: fontes, destinos e hashes dos arquivos pessoais.
- private/<timestamp>/: backups, changes.json e entradas antigas arquivadas;
  nunca versionar essa pasta. O arquivo .claude.json contém estado mutável:
  restaurar seletivamente, não sobrescrever sessões posteriores.

Estado vivo/pendências: tracker. Plano permanece na raiz até concluir aceite Alethe.
