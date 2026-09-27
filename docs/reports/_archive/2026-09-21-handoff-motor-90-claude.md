# Retomada Claude Code: motor >90% e diagnóstico #42

## Pedido vigente e limites

Usuário21/09: priorizar motor,subunidade/unidade/bloco com precisão estritamente>90%; buscar evidência existente antes de medir,medir antes de afirmar; depois migrar para web. Codex autorizado excepcionalmente a preparar captura diagnóstica. Próxima interface: Claude Code. Uma tarefa/um coordenador; nenhuma chamada ativa desta frente.

Usar acerto total nos denominadores históricos como régua inicial,sem substituí-lo por precisão só dos confiantes. Registrar cobertura/abstenções separadas. Subunidade primária é métrica principal; aceito não a substitui. Meta>90%por eixo,não média dos três. Publicar também por curso; regra de aprovação por curso e demais eixos de "etc" ainda exigem delimitação,não inventar resultados. Meta não é garantia de viabilidade nem aprovação de implementação ampla.

Regimes separados: cru automático sem LLM em toda cadeia; declaração do professor opcional; LLM opcional. Gold somente avaliação,não insumo de implementação. Não excluir ausentes do denominador silenciosamente,nem usar curso já estudado como holdout novo. Não redefinir a métrica para declarar sucesso. Não remover GUI até contrato/paridade web/Gate1 próprios.

## Números conferidos nesta sessão

Recomputação determinística dos JSONs existentes,SEM rebuild/LLM/rede no cálculo. MF/IA: verificacao_pacote_categoria_MF_IA_17-09.json; demais: verificacao_pacote_7cursos_15-09.json. Base dos artefatos em docs/reports/_harness-2026-09-04/c1-3/. São resultados históricos15/17-09, não baseline atual renovado.

| Eixo | Acertos/total | Percentual | Mínimo inteiro para >90% | Diferença aritmética |
|---|---:|---:|---:|---:|
| Bloco |213/237|89,873%|214|1|
| Unidade |239/284|84,155%|256|17|
| Subunidade primária |84/251|33,466%|226|142|
| Subunidade aceita,auxiliar |108/251|43,028%|226|118|

Diferença não estima ganho alcançável. Mínimo calculado por floor(0.9*n)+1,denominador fixo.

| Curso | Bloco | Unidade | Sub primária | Sub aceita |
|---|---:|---:|---:|---:|
| MF |53/66|61/66|25/58|29/58|
| SO |36/39|27/37|7/15|8/15|
| IA |38/42|39/42|4/39|5/39|
| ES2 |27/28|25/28|7/28|8/28|
| TCC |26/27|17/18|7/11|9/11|
| CG |33/35|70/93|28/82|42/82|
| FR |n/d|n/d|6/18|7/18|

diagnostico_subunidade_17-09.json confirma:251entradas,84acertos,8ausentes;159erros classificados,95rótulo ausente/17genérico/47presente discriminante na unidade. Não interpretar47como ganho garantido nem95como prova de necessidade universal de declaração. Review anterior retirou essas conclusões. Não misturar com antigo cru herdado/produto+voter/vocabulário LLM.

SHA256 dos artefatos conferidos:
- verificacao_pacote_7cursos_15-09.json: ca4947e41b2b06863259026a4f4911ceb8abbd9c7ada670fe7924f23bb0a6239
- verificacao_pacote_categoria_MF_IA_17-09.json: cd24c34284679b314d015898192b20064a780a8fdc3baf3b783ff8f77e416feb
- diagnostico_subunidade_17-09.json: cfbc2a59dd83fac138994e011e0108275f09ab78157d0dc9089854e10a089092

## Estado existente: não refazer

Checkout C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator,feat/motor-atribuicao,HEADce02a8f conferido na preparação. Worktree sujo; preservar alterações alheias. .workflow-local/active-task.md pertence ao regime2-declaracao-20260917; não sobrescrito. Review Astra já consumida: NÃO SUSTENTA declaração sempre necessária; script/formulários aguardam Gate1. Categoria prova matemática já concluída,2382passed/4skipped históricos,não testes rerodados hoje. Handoff17/09 precede parte dessas conclusões; tracker/active-task prevalecem.

Fila em pendencias.md bloco fila-campanhas:26tarefas/11campanhas,MOTOR/CRU prioritários. MOTOR-9 reconcilia PR9/base antes de congelar CRU; CRU-01 baseline; CRU-02subunidade; CRU-03unidade; CRU-04bloco. Níveis provisórios não liberam execução. Diagnóstico do motor não depende de inventar automação noturna pronta. CRU-01 noturno continua bloqueado pelos preflights/base/corpus,sem autorizar acesso novo ao corpus.

## Fable: duas falhas distintas

1. Implementador Windows,exec41331,fable/high,tools vazias,safe-mode,JSON final: TimeoutExpired300s,sem envelope recuperado. Chamada encerrada,não repetida. --version2.1.278 respondeu0.031s; auth status posterior loggedIn=true/authMethod=claude.ai. Não localizados registros da chamada em debug/telemetry/metrics/session-data; --no-session-persistence estava ativo. Causa interna NÃO DETERMINADA; não afirmar quota,re­de,autenticação ou lentidão de inferência. Instrumentação do chamador era insuficiente para localizar a fase: output só no fim e exceção não preservou diagnóstico parcial. Próxima chamada autorizada deve preservar eventos sanitizados/tempos antes de aumentar timeout; não autorizar retry por este handoff.
2. Sandbox: UMA chamada diagnóstica autorizada114ef8f9-e3b6-4ef4-83fe-b8e428bf8bbc,0.609s,unexpected_model,exit-9,kill_confirmed=true. Init anunciou claude-fable-5-1; assistant trouxe <synthetic>,zero tokens no evento,categoria fixa auth. Auth status posterior loggedIn=false/authMethod=none/firstParty,apesar de arquivo de credencial existir. Variáveis de autenticação consultadas ausentes no ambiente e provider. Evidência sustenta falha de autenticação reconhecida pela CLI da sandbox,não prova expiração nem origem exata. <synthetic> é evento interno,não adicionar à allowlist nem tratá-lo como modelo alternativo aprovado. Falha antiga02c8fa8d não tem ID original retido; nova tentativa reproduziu o sintoma com causa observável,sem provar retrospectivamente o conteúdo antigo.

Captura privada: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/night-loop-pilot-20260919/diagnostic-20260921/{diagnostic.py,test_diagnostic.py,RESULT.json,brief.md}. Subclass temporária observa metadados antes da normalização e preserva guard/cleanup. Runtime de produção inalterado. TDD:4RED→4GREEN Linux;5testes existentes containment/env/argv verdes. Cobertura não medida; primeiro import Windows falhou por fcntl e não contou como RED. Skill tdd-workflow orientou sanitização/guard antes do live; systematic-debugging separou evidência de hipótese. Sem commits(checkpoints dependem Gate2),sem segunda revisão.

Sandbox night-fable-20260919 parada ao fim,estado preservado. Orçamento diagnóstico1CONSUMIDO,sem retry. #42permanece aberta: auth,limites agregados (memory.max=max,cpu.max=max100000),preflight/E2E e demais aceites pendentes. Generic night negado,suspensão não autorizada,review1preservada. Não copiar credenciais do host nem alterar login automaticamente.

## Próxima sessão Claude Code

1. Ler este handoff,.workflow/README.md e estado do motor; conferir HEAD/diff atual. Assumir coordenação só após encerrar esta sessão; não iniciar outro coordenador em paralelo.
2. Conferir fontes citadas antes de propor medição nova; preservar distinção histórico/recalculado/reexecutado. Delimitar plano de baseline e meta>90%,com dados/base/comandos,0LLM no motor e avaliação separada. Não reconstruir tudo sem necessidade.
3. Priorizar hipótese generalizável de subunidade e reconciliar regime2 opcional; apresentar Gate1 mínimo com critério de ganho/perdas,sem reabrir revisão consumida. Unidade/bloco depois,com baseline revalidado após integração.
4. Autenticação sandbox exige orientação/interação do usuário; novo live exige autorização específica pois tentativa consumida. Não bloquear investigação assistida do motor esperando capacidades noturnas fora de escopo.
5. Antes da web,exigir evidência de aceite do motor e contrato independente de Tkinter; migração/remoção da GUI em escopo próprio. Sem commit/merge/deploy autorizado nesta sessão.
