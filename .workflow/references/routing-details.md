# Roteamento por tarefa

Ler uma vez ao iniciar tarefa substantiva; não recarregar por mensagem.
Núcleo e permissões: ../workflow.md. Uma tarefa mantém um coordenador.

## Classificação

| Pedido | Dono e saída |
|---|---|
| Pergunta/status ou ajuste documental/local pequeno | Agente ativo, resposta/verificação local |
| Implementação pequena e bem delimitada | Claude Code pelo nível em routing.md, teste e diff |
| Mudança complexa, múltiplos componentes, arquitetura ou aceite ambíguo | Codex planeja/orquestra; plano e aceites delimitados; Claude Code implementa pelo nível investigado |
| Código relevante pronto para revisão | Revisor em sessão independente, read-only, uma tentativa registrada |
| Auditoria, corpus ou busca de código | Codex leitor, fontes verificáveis e achados; relatório só no caminho permitido |
| Documentação, pesquisa ou redação de achados | Escritor no Codex (AGY por escolha), arquivos de saída explicitamente permitidos |

Classificação, matriz e perfis: routing.md é a fonte canônica; investigador decide e coordenador registra.
Contratos inline: ../agents/codex-leitor.md e ../agents/escritor.md; carregar apenas o papel escolhido.
O usuário não precisa pedir "delegue". Classificar é parte da tarefa; chamadas respeitam
Gates e contrato [delegation.md](delegation.md). Escolha explícita do usuário prevalece.
Ler [review.md](review.md) antes de chamar revisor; não usar planejamento para renovar revisão.
Se o host já é Codex, planejar nele; não chamar outro Codex para repetir orquestração.
Se o host é Claude, conservar o terminal como interface; receber o plano e conduzir sua execução.
Se o host é AGY, só orquestrar quando escolhido (último na prioridade, routing.md › Orquestradores),
com planejador e revisor Opus 5.5; senão, limitar-se à escrita escolhida.
Documentação/configuração simples pode ser concluída pelo agente ativo conforme escolha explícita.
Não delegar de volta ao chamador nem criar cadeia recursiva. Troca por quota só pela reserva de routing.md › Camadas.

## Goals e agente noturno

Quando solicitado listar goals, consultar o catálogo do projeto atual e mostrar ID, estado,
aceite restante e bloqueio; se ausente, declarar ausência. No GPT Tutor a fonte prevista é
docs/reports/goals-noturnos.md da frente GPT #42; a fila persistente é GPT #43.
Não confundir /goal nativo com catálogo do projeto. Selecionar/reservar não executa.
Antes de continuar, localizar tarefa existente em .workflow/local/active-task.md (legado: .workflow-local/) e conferir
branch/HEAD; preservar contador e chamada ativa. Nunca importar estado de outro worktree por suposição.
O supervisor noturno mantém seu próprio contrato executável, preflight e estado; esta rota
não o libera nem substitui seus controles. A integração futura deve transmitir o ID do goal
e papel explicitamente, pois subprocessos com safe-mode podem não carregar hooks.

## Hooks e validação

O lembrete desta rota (implementação, refatoração, defeito ou git) fica em `personal-instructions.md`
(uma vez por sessão nos três CLIs, #180), sem
hook de prompt; no AGY a regra `always_on` guarda só o papel da CLI (../hooks/README.md).
Hooks que restarem não fazem inferência, escrita de estado nem scheduler; o Codex requer confiança
da definição em /hooks, sem hashes de confiança nem bypass.
Modelo configurado não atesta modelo observado. Após abrir sessão nova, validar uma tarefa real
e registrar sessão/roteamento/saída antes de declarar delegação E2E.
Fontes: https://code.claude.com/docs/en/hooks e https://learn.chatgpt.com/docs/hooks;
AGY: https://antigravity.google/docs/hooks?tab=ide documenta também a CLI; no AGY, PreInvocation
roda a cada chamada ao modelo, então texto fixo vai para regras (#18).

## Modelos em uso

Revisão de 10/10/2026 com dados públicos de benchlm.ai, Artificial Analysis e Arena, e com as
medições internas de 09–10/10 (evidência em ../evals/modelos-2026-10-10.md). claude-fable-5-1 saiu
do T3: ficou abaixo do Opus 5.5 em FrontierSWE v2 (56,3 × 62,3), DeepSWE (67,4 × 74,2) e SWE-bench
Pro (81,2 × 89,9), e as T3 de 09/10 foram feitas pelo Opus.

Alias → ID medido em 15/10/2026 (Claude Code 2.1.299): opus → claude-opus-5-5, sonnet →
claude-sonnet-5-5, haiku → claude-haiku-5-5, fable → claude-fable-5-1.

## Medições ROTA-04 e ROTA-06

T2 no Sonnet (ROTA-04, 15/10/2026): no replay de 3 PRs, em 3 rodadas, o Sonnet teve 10 P1 contra 11
do Opus, com os mesmos testes ocultos (78/108) e ~1/3 do custo de execução (US$ 2,70 × 7,85);
evidência em ../evals/rota-03-2026-10-15.md. T1 no Haiku pelo mesmo replay: 10 P1 em 3 rodadas, como
o Sonnet, com 76/108 ocultos (Sonnet 78/108) e US$ 0,62 de execução.

Reserva no Codex (ROTA-06, 16/10/2026): no replay da ROTA-05 o Codex (gpt-6-astra / high) teve 4 P1 e
26/36 ocultos, dentro da faixa dos braços Claude (2 a 5 P1, 26/36), sem US$ e mais lento (32 min,
Sonnet 12 a 19); evidência em ../evals/rota-05-2026-10-16.md.

## Medições AGY

- gpt-oss-120b-medium (2º lugar): esforço fixo, contexto de 128k, AA Agentic 6,2; medido em 11/10 como
  worker (escreveu o arquivo, não rodou comando, 5,5k tokens, 6 s; uma amostra trivial).
- Gemini 3.8 Flash (3º): 55,2% de alucinação (AA-Omniscience) e poucos bugs achados (Bug Hunt 18);
  por isso seus achados passam pelo Codex (codex_read) ou pelo Claude antes de virar issue ou ação.
- gemini-4-argon-high (reserva, #151, 18/10/2026): no replay deu a qualidade dos outros braços (5 P1,
  ocultos 27/36), mas 3 PRs gastaram ~46% da cota semanal do Argon
  (../evals/rota-06-argon-2026-10-18.md).

## Modelos do AGY

agy models, AGY 1.4.2 em 18/10/2026; o CLI se atualiza sozinho:
gemini-4-argon-{low,medium,high}, gemini-3.8-flash-{low,medium,high}, claude-opus-5-5-{low,medium,high},
claude-sonnet-5-5-{low,medium,high} e gpt-oss-120b-medium.

## AGY: cota e worker

Cota (#151): ler o `/usage` do agy antes e depois de cada uso e anotar no eval ou no estado da tarefa;
replay no AGY só por escolha explícita e com 1 PR por rodada (`bin/replay.py` recusa mais); sondas
de capacidade (flags, sandbox, ferramentas) no Gemini 3.8 Flash. A ordem vale pela escolha do papel: no Alethe o fallback desce um nível e a cota do
AGY é lida por fornecedor, então o app não troca de modelo dentro do AGY sozinho.
Desde AGY-04 (alethe-agents #158) o worker AGY roda como agente gerenciado `alethe-worker`, sem
comandos (só lê, busca e edita arquivos), sem os hooks globais e o GEMINI.md do dono, sempre numa
worktree própria; git, testes e builds ficam com o coordenador depois do turno. Código de worker AGY
recebe a mesma revisão independente (review.md).

## Perfis adicionais AGY

- Fora da seleção automática até medição no nosso uso: gemini-4-argon-low e gemini-4-argon-medium
  (só o high foi medido). gemini-3.7/3.6-flash e gemini-3.1-pro saíram do AGY na 1.4.2.
- Investigador pode escolher outro perfil do AGY com justificativa registrada; a superioridade no
  nosso uso ainda não foi medida. Não chamar vários para a mesma auditoria sem avaliação delimitada
  e autorizada. Não substituem a revisão do revisor.
- Gemini, Sonnet 5.5 e Opus 5.5: ID da variante (o esforço vem no ID) ou família com --effort,
  nunca os dois (medido na 1.3.3: o agy recusa na partida); sem inventar variantes. Não transferir
  parâmetros ou supor mesma assinatura/quota do Claude Code.
- Lista de modelos do AGY (agy models, 1.4.2 em 18/10/2026): routing-details.md › Modelos do AGY.
- Esforço: o CLI aceita --effort low|medium|high|xhigh|max, mas nem todo modelo muda de esforço.
  Gemini Argon, Gemini Flash, Sonnet 5.5 e Opus 5.5 têm low/medium/high no ID;
  GPT-OSS 120B (Medium) tem esforço fixo. O worker AGY do Alethe oferece só os aprovados: Sonnet
  5.5 e Gemini 3.8 Flash medium/high pela família, Opus 5.5 pelo ID claude-opus-5-5-high e
  gpt-oss-120b-medium pelo ID (esforço fixo).
