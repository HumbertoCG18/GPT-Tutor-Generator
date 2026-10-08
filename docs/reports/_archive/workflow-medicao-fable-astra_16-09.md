# Piloto Fable × Astra — 16/09/2026

## Resultado e decisão

Ambos passaram nas duas tarefas na primeira resposta. Parser: 23/23 casos por modelo;
roteamento: 12/12 decisões por modelo. Nenhum turno de reparo. Manter Fable padrão e
Astra por necessidade concreta: este piloto não mostrou ganho funcional que justifique
Astra obrigatório. Não determina qual modelo é melhor em tarefas difíceis.

| Braço | Aceite funcional | Tempo de parede | Tokens reportados, incluindo cache |
|---|---:|---:|---:|
| Fable / CRLF | 23/23 | 26,563 s | 14.330 |
| Astra / CRLF | 23/23 | 26,859 s | 25.902 |
| Astra / roteamento | 12/12 | 17,547 s | 26.228 |
| Fable / roteamento | 12/12 | 13,859 s | 15.216 |

Totais: Fable 40,422 s e 29.546 tokens reportados; Astra 44,406 s e 52.130.
Esses volumes não medem economia financeira nem quota da assinatura. Contextos de
sistema, ferramentas expostas, contabilidade e cache diferem entre as CLIs.

## Protocolo fixado antes das chamadas

Quatro invocações principais de CLI; ordem Fable/CRLF, Astra/CRLF, Astra/roteamento,
Fable/roteamento. Mesmos prompts por tarefa, sem ferramentas ou fontes externas nos
braços. Uma resposta por braço; sem retries; timeout configurado de 180 segundos por
invocação. Nenhum timeout ocorreu; encerramento por timeout não foi exercitado.
Modelos solicitados: claude-fable-5-1 e gpt-6-astra; esforço medium solicitado em ambos.
Medium não tem necessariamente o mesmo significado entre provedores. O Astra deste
piloto não usa high do perfil de escalada habitual.

Claude: --tools vazio, --strict-mcp-config, permission-mode dontAsk; uma rodada por
resposta, nenhuma negativa de ferramenta ou erro. modelUsage registrou Fable mais
Haiku auxiliar nas duas invocações. Portanto, quatro invocações principais não equivalem
a somente quatro requisições internas de modelo; o total Fable inclui o auxiliar.
Codex: read-only e instrução explícita sem ferramentas; zero tool items nas saídas.
Nenhuma chamada Context7 realizada; o piloto Context7 permanece em 12/20 tentativas.

Tarefa CRLF: defeito real preservado do piloto anterior; baseline 20/23, com três
falhas em CRLF, antes de avaliar candidatos. Baseline, casos e enunciado iguais; código
retornado inspecionado antes da execução local. Testes cobrem Unicode, preservação de
CRLF dentro de strings, fences LF/CRLF, não-objetos e entradas inválidas. Não é prova
exaustiva de conformidade JSON. Fable acrescentou tratamento redundante de ValueError
e tolerância a espaços nas cercas; Astra acrescentou rejeição de constantes não finitas.
Essas diferenças adicionais não foram pontuadas como ganho no conjunto predefinido.

Tarefa roteamento: 12 cenários sintéticos com precedência explícita derivada da política,
incluindo quota, escolha explícita, limite de uma escalada, sessão em andamento e gates.
Acertar a classificação não comprova que a CLI realmente delegue ou retome uma tarefa.

## Formato e interferência do ambiente

Os quatro artefatos finais são JSON válidos. Fable produziu uma única resposta JSON em
2/2 casos. Codex/Astra produziu dois eventos agent_message em 2/2 casos: aviso obrigatório
do claude-mem seguido do JSON final. Assim, a resposta completa não cumpre JSON único,
embora o último artefato seja válido e passe nos testes. Isso é interferência observada
das instruções injetadas no ambiente, não evidência de deficiência de raciocínio.

O consumidor deve obter a mensagem final pelo mecanismo da CLI, não concatenar todos
os eventos. Nenhuma alteração global de hooks foi feita com base nessa observação.

## Proveniência e limites

Execução em 16/09/2026, 23:37–23:38 America/Sao_Paulo; diretório usa data UTC 17/09:
C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/fable-astra-20260917/.
protocol.json fixa ordem, limites e hashes dos prompts; baseline-red.json guarda o teste
vermelho; results.json e summary.json guardam métricas; grade.py é o verificador.
Prompts, respostas brutas, stderr, módulos candidatos e metadados permanecem nesse diretório.

Uma execução por tarefa/modelo, somente duas tarefas pequenas e contextos de CLI distintos.
Não é experimento causal puro entre modelos, validação de código de produção, medição
financeira nem avaliação de delegação autônoma. Disponibilidade do Fable confirmada pelas
duas respostas sem erro de quota; saldo restante e reset exato não foram medidos.

Pendentes: primeira escalada/retomada real e aceite Alethe. Não aumentar a amostra nem
mudar roteamento automaticamente. Trabalho do motor e organização de relatórios de
outra sessão preservados; nenhuma inferência do produto, commit ou push nesta medição.
