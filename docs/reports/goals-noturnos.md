# Catálogo de goals noturnos

Refs [#42](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/42).
Contrato de operação: [agente-noturno](../../.mex/patterns/agente-noturno.md).
Estado do piloto: [pendências](pendencias.md#agente-noturno-42).

## Seleção e estados

Pedido ao agente: `Preparar o goal CRU-01 para a próxima sessão noturna`.
Isso seleciona o goal; não inicia processos nem autoriza inferência ou suspensão.
Não existe, por enquanto, um slash command `/night` ou `/goal` instalado por esta entrega.

Estados: `rascunho`, `pronto`, `em execução`, `concluído`, `bloqueado`.
Somente `pronto` pode iniciar, após preflight e confirmação do resumo pelo operador.
Cada execução congela versão do goal, issue, base SHA, comandos verificadores,
hashes das fontes, tolerâncias e arquivos permitidos. Alterar critérios durante a
execução invalida a aprovação e exige novo Gate 1. Retomar não reinicia contadores.
Resultado sem ganho não é sucesso do goal de melhoria: relatório inconclusivo e parada.

| ID / versão | Resultado | Dependências | Estado |
|---|---|---|---|
| CRU-01 / 1 | Baseline reproduzível dos eixos crus | Piloto validado, base e corpus aprovados | bloqueado |
| CRU-02 / 1 | Uma melhoria delimitada de subunidade | CRU-01, hipótese e meta pré-registradas | rascunho |
| CRU-03 / 1 | Uma melhoria delimitada de unidade | CRU-01, hipótese e meta pré-registradas | rascunho |
| CRU-04 / 1 | Uma melhoria delimitada de bloco | CRU-01, hipótese e meta pré-registradas | rascunho |
| PREWEB-01 / 1 | Triagem verificável das pendências pré-web | Inventário de branches, PRs e tracker | rascunho |

## Contrato comum dos goals CRU

Fable/Sol podem implementar código, mas o motor, aquisição e medições não chamam LLM.
Reutilizar extrações Datalab existentes. Nova extração paga exige orçamento específico.
Gold somente em avaliação final cega, executada separadamente do worker: não montar
gold nem diagnósticos derivados dele na cópia de desenvolvimento. Histórico já lido
por agentes não vira holdout novo; declarar essa limitação e não alegar cegamento retroativo.
Congelar candidato antes da avaliação; não devolver erros individuais ao executor para
uma segunda otimização sobre o mesmo teste. Sem mudanças em tutores-produto ou evidência
histórica; saídas em diretório novo, nunca sobrescrever baseline.

### CRU-01 — Baseline reproduzível

- Objetivo: fixar a referência para comparar candidatos na mesma base e nos mesmos dados.
- Entrada: SHA aprovado de `feat/motor-atribuicao`, manifesto de fontes/extrações existentes,
  configuração do regime cru, comandos verificados localmente e protocolo de avaliação.
- Escrita: somente diretório novo de evidências e cópias sintéticas/de medição autorizadas;
  não editar `src/`, `tests/`, `.ablacao/` ou tutores-produto. Corpus privado não vai ao GitHub.
- Aceite: registrar versões, hashes, denominadores/ausentes, resultados por eixo/curso,
  duração e erros; repetir a medição determinística e comparar previsões/hashes, justificando
  campos voláteis. Demonstrar zero chamadas LLM/rede no trecho de medição, não inferir pelo nome.
- Verificação: relatório + JSON saneado + comandos/exit codes + comparação das duas execuções.
- Parar: fonte ausente, dependência paga, contaminação por gold/LLM ou divergência não explicada.
- Pendente: escolher corpus/base atuais e comandos; placar de 17/09 é histórico, não baseline novo.

### CRU-02 — Subunidade

- Objetivo: testar uma hipótese generalizável para melhorar subunidade primária, sem regras
  específicas por curso/arquivo/rótulo gold. Seleção da hipótese por contratos e fontes sem gold.
- Entrada: CRU-01, hipótese escrita, escopo de funções/testes e meta/tolerância aprovados.
- Escrita: apenas allowlist de código/testes definida no preflight e diretório novo de evidências.
- Aceite: regressão sintética reproduzível quando aplicável, suíte pertinente verde, diff revisado,
  aumento mínimo e tolerâncias por eixo/curso aprovados ANTES da avaliação final cega.
- Verificação: mesmo protocolo do baseline; ganhos e perdas separados, denominadores fixados.
- Parar: quota/tentativas, três falhas iguais sem progresso, necessidade de gold no desenvolvimento
  ou hipótese que exija outro escopo. Sem ganho final: inconclusivo, não promover.

### CRU-03 — Unidade

Mesmo contrato de CRU-02, eixo alvo unidade. Congelar hipótese/allowlist/meta próprias,
preservar bloco e subunidade dentro de tolerâncias aprovadas. Não executar em paralelo
na mesma cópia de CRU-02. Revalidar baseline se a base mudar após integrar outro goal.

### CRU-04 — Bloco

Mesmo contrato de CRU-02, eixo alvo bloco. Congelar hipótese/allowlist/meta próprias,
preservar unidade e subunidade dentro de tolerâncias aprovadas. Não reutilizar o baseline
de outra revisão de código como se fosse a base atual.

### PREWEB-01 — Triagem pré-web

- Objetivo: distinguir entrega existente, merge pendente, medição faltante e capacidade ausente.
- Entradas: tracker, handoff, branches/PRs e issues #11, #12, #14 e #41; issue aberta não prova
  implementação ausente, nem arquivo local prova integração na branch motor.
- Escrita: relatório de triagem e deltas propostos do tracker; não modificar produto/CI/web.
- Aceite: cada pendência com evidência atual, dependência, resultado verificável e proposta de
  goal pequeno; não duplicar tarefas já entregues nem instalar antecipadamente a stack web.
- Verificação: URLs/SHAs/paths conferidos e revisão documental; novas implementações exigem
  goal e Gate 1 próprios. Não fechar issues automaticamente.

## Relatório obrigatório

ID/versão do goal, sessão/thread/run IDs, issue, branch/base, hash do patch recuperável,
resumo, testes baseline/final, medições, ganhos/perdas, tentativas, falhas, modelos/esforços,
tokens input/output/cache separados, quota observada e limitações, achados/revisão,
decisão humana pendente. Tokens e preço de tabela não equivalem à quota da assinatura.
Sem commit/push/merge automático. Rejeição preserva evidências; reversão após merge exige
aprovação específica. O objetivo e a aprovação não migram silenciosamente para outra base.
