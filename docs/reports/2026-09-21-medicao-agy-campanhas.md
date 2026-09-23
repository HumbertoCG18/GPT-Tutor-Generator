# Medição AGY e fila de campanhas — 21/09/2026

## Resultado
12/12 chamadas concluídas, exit0/SUCCESS; quatro perfis acertaram A/B e não reportaram defeito em C. Zero achados extras na conferência do coordenador. Nenhuma repetição ou fallback. Aceite desta medição cumprido; não encerra #42 nem libera execução noturna.

| Perfil solicitado | Acertos | Tempo médio de parede | Input total | Output total | Cache read total |
|---|---:|---:|---:|---:|---:|
| gemini-3.8-flash-high | 3/3 | 45.07s | 81595 | 41073 | 34136 |
| gemini-3.1-pro-high | 3/3 | 14.69s | 43711 | 3145 | 16242 |
| claude-sonnet-4-6 | 3/3 | 21.51s | 75276 | 2361 | 38515 |
| claude-opus-4-6-thinking | 3/3 | 33.74s | 80117 | 3718 | 57805 |

Totais por perfil somam três chamadas. Não somar thinking novamente ao output; categorias reportadas pelo AGY não equivalem necessariamente entre providers. Claude reportou thinking0, o que não prova ausência de raciocínio. Input inclui harness/contexto; não são somente tokens dos casos. Cache variou e ordem rotacionada não elimina aquecimento. Sem medição de fatura, quota ou economia de assinatura.

## Método e evidência
Três casos sintéticos congelados antes das chamadas: A limite off-by-one; B cache sem isolamento por projeto; C reserva correta, controle negativo. Gabaritos executados deterministicamente. Mesmo prompt por caso, schema, cwd, permissões; chamadas sequenciais com ordem rotacionada. Limites120s CLI/150s externo, parada global em erro, sem retries. Skill parallel-execution-optimizer orientou separar inventário e medição sem concorrência entre inferências, evitando disputa de recursos.

Artefatos privados: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/agy-benchmark-20260921/{cases.json,results.json,STATE.md}.
SHA256 cases.json: 589724008cad29020fe9796475cb4b1bca578b5ac62ff2fc9e6dc9e83fe76eac.
results.json preserva envelopes, IDs de sessão, tempos e uso. Transcripts em ~/.gemini/antigravity-cli/brain/<session>/.system_generated/logs/transcript.jsonl. Inventário dos12transcripts: somente USER_INPUT,PLANNER_RESPONSE,GENERIC,EPHEMERAL_MESSAGE; nenhum evento ERROR ou evento separado de ferramenta observado. Não equivale a auditoria independente de efeitos externos; não foi necessário ampliar grants.

Pontuação usa structured_output, não response textual: CLI finaliza schema e algumas respostas livres tinham fences/campos extras. Formato estruturado validado não demonstra aderência JSON da resposta livre. AGY apresentou modelo solicitado/configurado, sem atestação independente do modelo efetivo.

| Caso | Perfil | Parede s | Sessão |
|---|---|---:|---|
| A | gemini-3.8-flash-high | 33.015 | 9974486d-73d0-4535-8b68-b8513d0441ac |
| A | gemini-3.1-pro-high | 16.656 | 0780d00e-8f4d-4674-b047-09aff5a142d8 |
| A | claude-sonnet-4-6 | 13.688 | c0e35f2a-b476-46a2-8606-edbfb8361889 |
| A | claude-opus-4-6-thinking | 24.484 | 0813b8e9-be6a-47e5-92c3-22b4a19a8057 |
| B | gemini-3.1-pro-high | 12.813 | e6b38dba-09c4-49f6-a8a5-ec42a35279ae |
| B | claude-sonnet-4-6 | 19.078 | ea5204da-47b8-42db-879f-03515a62ac6d |
| B | claude-opus-4-6-thinking | 40.844 | 47035578-feab-4802-bf83-f60a927a7b87 |
| B | gemini-3.8-flash-high | 77.578 | f1c3d900-4d21-40fc-9a35-80745367a1f2 |
| C | claude-sonnet-4-6 | 31.765 | 2fe0fa42-e253-4602-b596-ce4fa0cce964 |
| C | claude-opus-4-6-thinking | 35.891 | f9a1f561-3c5e-406e-86e3-63cad1cc5b3e |
| C | gemini-3.8-flash-high | 24.609 | b9666527-0676-4d89-9a19-8d7974152590 |
| C | gemini-3.1-pro-high | 14.594 | 8e7cdfbd-f831-46b5-9284-ef4bd513efd4 |

## Decisão limitada à amostra
Pro3.1high teve menor tempo médio; Sonnet4.6 menor output agregado. Flash3.8high consumiu mais output/tempo, sobretudo no cache. OpusThinking não trouxe ganho de acerto nesses casos. São três casos pequenos, uma execução por combinação, sem significância estatística: não demonstram superioridade em arquitetura/corpus/repositório real, nem validam Flash low/medium.

Manter matriz aprovada sem promoção global. Para próximo piloto assistido de auditoria delimitada, Pro3.1high é candidato justificado por este resultado; Sonnet4.6 é alternativa a selecionar antes da chamada, não fallback automático. Investigador registra nível, critério e limites. Não chamar todos novamente em tarefa real. Nenhum default alterado.

## Fila e fechamento noturno
Inventário: [pendencias.md](pendencias.md), bloco fila-campanhas:26tarefas únicas/11campanhas, níveis T0–T3 e classes C1–C3. Fonte GitHub consultada nesta rodada:9issues abertas (#11,#12,#14,#41–46),3PRs (#9,#39,#40). Estados classificados pelo investigador; níveis de escopo indefinido permanecem provisórios. Labels locais, não criados no GitHub. Histórico fora do bloco preservado; tarefas tecnicamente prontas ainda entram quando Gate2/integração pendem.

#42 continua bloqueada: causa de unexpected_model/unrecognized não estabelecida; diagnóstico sintético instrumentado de1chamada exige autorização específica; preflight/base/recursos e E2E continuam pendentes. Suspensão Windows real não implementada, generic_night negado; não prometer uma noite autônoma. Uma revisão já consumida não é renovada.

Próxima sequência: diagnóstico assistido e contido; correção só após causa/evidência; E2E com aceite determinístico e Gate2; então piloto PREWEB-01[T2], read-only, relatório de reconciliação. Não iniciar corpus CRU bloqueado. Aprovação desta medição não autoriza inferência noturna, merge, commit ou fechamento de issues.

