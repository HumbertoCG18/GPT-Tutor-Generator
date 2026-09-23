# Verificação do piloto noturno — 20/09/2026

Refs [#42](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/42).
Contrato: [agente-noturno](../../.mex/patterns/agente-noturno.md).
Este relatório registra evidências; disponibilidade atual fica no [tracker](pendencias.md#agente-noturno-42).

## Proveniência e isolamento

Atualização operacional posterior: pacote `agent-workflow-lab/pilots/night-agent/`,
worktree `agent-workflow-lab-night-42`, baseline local `6657622`; integração ainda sem commit.
Snapshot `operational-v4`: coordenador reproduziu333testesLinux em32,552s,62testes de política
Windows em5,418s; Ruff crítico e15hashes do manifesto verdes. Uma revisão Astra/high,
quatro achados corrigidos por Fable; não houve segunda revisão LLM. Cobertura92,5% refere-se
à v3, não foi remedida após o último ajuste. Histórico abaixo preserva medições anteriores.

Smoke real limitado a uma chamada: `02c8fa8d-8661-4333-8016-1878da9dc86b`,1,486s,
`unexpected_model`, identidade sanitizada `unrecognized`; parada confirmada, diff vazio,
zero edições/verificadores, goal não concluído. Artefatos privados preservados em
`operational-smoke-live-42/` e `OPERATIONAL-VERIFY.md` no laboratório. Não repetir nem zerar
contadores. Autenticação OAuth configurada no Docker, mas CLI informa login ausente;
isso não identifica sozinho a causa nem prova expiração. Nova captura diagnóstica precisa
preservar proteção de modelo/segredos e autorização específica. Noite genérica, adaptador
Codex e suspensão Windows continuam indisponíveis; campanha42 não encerrada.

Laboratório local irmão `agent-workflow-lab/private/night-loop-pilot-20260919/`.
Snapshot `delivery-v1`: primeira implementação e `ASTRA-REVIEW.md`, quatro bloqueadores.
Snapshot `delivery-v2`: correções do Fable preservadas sem sobrescrever v1.
Sessão Fable v2: `7cdd587e-407e-4f07-9b8b-98ecd6151e14`; 531517ms,35turnos.
Uso reportado: input62/output47531/cache creation109595/cache read2135939;
USD5.10305475 em preço de tabela, não cobrança nem consumo de assinatura comprovados.

Branch de integração documental `feat/42-night-goals`, base
`ce02a8f47285c30c16f12b131bdf86c46dcba64e`, worktree irmão
`GPT-Tutor-Generator-night-42`. Principal `feat/motor-atribuicao` preservado com29entradas
locais no status; nenhum delta transportado automaticamente. Sem commit/merge/push.

## Verificação reproduzida pelo coordenador

No Linux, cwd `/tmp/night-delivery`, executado:

```text
python3 -m unittest test_night_session test_fix_regressions test_zeroshot_glue -q
Ran 51 tests in 2.736s — OK
```

Essa execução verificou regressões de paths, concorrência entre processos, falha de
relatório, saneamento de GIT_* e vinculação de decisão ao patch. Não equivale a testar
hostile worker com acesso ao diretório de evidência: essa escrita deve ser impedida por
isolamento real, não por checagens de path.

Cobertura v2 registrada pelo executor, não repetida pelo coordenador: trace533/560linhas,
95.2%; branches e processos-filho fora da instrumentação. Script e lista de gaps em
`delivery-v2/evidence/fix-coverage.txt`. Não chamar isso cobertura do runner completo.

## Testes mecânicos ZeroShot preservados

- Timeout: `01a0bce4-c6ce-7781-b0ce-3f73389aac36`, motivo exato `expected_timeout`,
  8.05s no ensaio, zero sobreviventes registrados após5s.
- Force-stop: `01a0bce4-b964-7702-9853-7844973ea1bd`, motivo `force_stopped`;
  filhos vivos antes/depois de desconectar o observador, zero sobreviventes após parada.
- Identidade PID+starttime gravada; desconectar/reconectar observador não é recuperar
  controlador morto. Um run admitido por caso, sem chamadas de modelo nesses dois ensaios.
- Evidências inspecionadas: `delivery-v2/evidence/fix-mechanical/{timeout,force-stop}.json`.
  Não repetir ensaios automaticamente nem alegar nova prova de kill pelo simples status terminal.

## Lacuna encontrada na integração

O sucesso real `01a0bccb-07fa-7342-967b-a7c04ca80390` contém
`terminalResult={status:succeeded,output:null}`. O parser v2 só aceitava status/reason.
Reprodução na fase seguinte: `NightError: terminalResult com campos inesperados`.
Correção delegada: tolerar e descartar output, manter contrato dos campos relevantes,
preservar cache separado e não liberar a tarefa se force-stop não confirmar parada.
Relatórios a partir de runs já terminais não demonstram polling de job ativo.

## Integração de término e política mínima

Snapshot `delivery-v3` congelado. Coordenador executou100testes Linux, todos verdes
em5.454s, incluindo12regressões adicionais de integração de término. A consulta do
binário real a três runs terminais gerou relatórios `completed`, `timeout` e `cancelled`,
com hash do patch, relatório atual e contagens desconhecidas preservadas como nulas.
Isso não valida o conteúdo do goal nem a execução de um novo trabalho no motor.

Política nova:37testes completos no Windows verdes em2.018s, incluindo lock entre
processos. CLI `self-check` declara honestamente `real_nightly_run_possible=false`;
o campo `platform_tested` é estático, não reflete esta execução posterior no Windows.
Compilação Python e lint crítico Ruff(E9,F63,F7,F82) executados na fase de verificação.

Astra/medium revisou somente a política nova, uma vez:2HIGH+1MEDIUM reproduzidos,
apesar dos testes verdes. Parada de segurança ignorada em unknown/succeeded; quota
persistida malformada aceita; contexto não invalidado após review. Correções delegadas
ao Fable, sem segunda revisão automática. Não transferir o status desses testes para
adaptadores reais ainda ausentes. Sessão Fable anterior terminou exit1 sem envelope
final; causa não determinada, artefatos recuperados e reexecutados pelo coordenador.

## Resultado das correções revisadas

Snapshot final desta etapa: `delivery-v4`, preservando v1/v2/v3. Fable corretivo
`e2043db9-899a-49ee-8fb8-39590a5696cf`, exit0, 164384ms, 16 turnos.
Input28/output15166/cache creation52640/cache read526976; USD1.943124 em preço
de tabela, não cobrança comprovada. Evidências novas `policy-review-red.txt` e
`policy-review-green.txt`; RED47testes/54falhas de subcasos antes das correções.

Coordenador reproduziu após correção:

| Verificação | Resultado | Limite |
|---|---|---|
| Linux, cinco módulos unittest selecionados | 110 testes OK, 4.058s | Sem relançar ZeroShot/modelo |
| Windows, test_night_policy | 47 testes OK, 2.396s | Política, não host sleep |
| trace antes dos imports, Linux | entrega565/589=95,9%; política453/505=89,7% | Linhas, não branches; subprocessos não rastreados |
| py_compile dos dois módulos | OK | Não verifica tipos |
| Ruff E9/F63/F7/F82 | OK | Lint crítico, não todas as regras |
| Links dos três MDs novos + git diff --check | OK | Sem merge/commit |

Pyright não encontrado; nenhuma ferramenta instalada para suprir essa lacuna.
Falha de segurança prevalece sobre outcome, quota persistida rejeita dados inválidos,
review invalida observação anterior e sessão/rotação novas começam com contexto desconhecido.
Uma medição explícita é exigida antes de inferência. Não foi feita segunda revisão LLM.

SHA256 dos fontes congelados:

```text
night_session.py 56a976faad5cdb23de6b2d15e25f7a121033b0bfbd616b07c158f35184830a15
night_policy.py  c8968f8c0867614d6db609bd83368c64fd72ae086a92e1d45c48eb236b398cb0
```

Entrada técnica segura, executada a partir do snapshot local: `python night_policy.py self-check`.
Não existe comando de execução noturna real nesse módulo. Importação no produto limitada
a documentação/roteamento; não adicionar dependência Linux ao runtime Python/Tkinter.

## Host e itens não demonstrados

### Adaptador real de quota (revisão em correção)

Snapshot `quota-v1` no laboratório, executor Fable
`79a8b3cc-f808-4305-a68a-7df9ae2487be`; 420970ms/20turnos.
Input36/output36574/cache creation95958/cache read1376743; USD4.09240575 list,
não consumo percentual da assinatura. `night_session.py` permaneceu byte-idêntico.
Novos `night_quota.py`/testes e integração `Policy.refresh_and_record`.

Coordenador reproduziu149testes Linux(4.810s),62testes de política Windows(3.400s),
compilação e lint crítico. Trace reexecutado: quota213/232=91,8%; política531/572=92,8%.
São linhas, não branches nem cobertura dos filhos. Transporte de quota limitado ao Linux.

Duas consultas reais via app-server, sem inferência Codex: bucket `codex`, janela
semanal10080min no slot `primary`,21%usados/79%restantes; outras janelas ausentes.
Isso é um retrato das consultas, não saldo atual garantido. Credenciais geridas pelo CLI;
sem leitura/cópia de auth.json, sem compra/resgate de créditos. Fonte oficial:
[app-server](https://developers.openai.com/pt-BR/docs/app-server).

Falha de leitura invalida autorização mesmo com observação anterior ainda fresca;
reset não estorna consumo e troca entre fonte simulada/real é bloqueada.
Percentual agregado inclui uso concorrente; lacunas entre leitura e reset não são
mensuráveis. Nenhuma garantia de teto rígido de10pontos durante inferência em voo.

Revisão Astra medium, uma chamada:1P2 reproduzido. `_reap` encerrava apenas o líder
e podia deixar filho ignorando SIGTERM vivo. Correção Fable em andamento, sem nova
revisão automática nem probes. Snapshot v1/evidências anteriores preservados.

Atualização 20/09,02:55: correção concluída por Fable na sessão
`b0c257ee-e96b-4e6f-a8fb-ce94ae601aa0`,142862ms/14turnos, snapshot `quota-v2`.
Coordenador reproduziu161testes em8.476s:159 aprovados/2 skips (ZeroShot opt-in),
compilação e Ruff E9/F63/F7/F82 verdes; nenhum worker órfão no ps final.
Cleanup sinaliza grupo próprio antes de colher líder e confirma término com espera
limitada; falha vira `cleanup_unconfirmed`. Policy/session byte-idênticos.
Trace do executor: quota248/264=93,9%; política531/572=92,8%, linhas somente.
Filhos que escapam do grupo via setsid não são contidos: supervisor/isolamento pendentes.
Astra permanece uma revisão consumida; nenhuma segunda revisão LLM.
Após reboot anterior por LSASS/RPCRT4, SFC reparou Appx.psd1; nexo causal indeterminado.
Nesta rodada não houve reboot nem evento LSASS/RPCRT4 entre02:52 e02:55:44;
isso não comprova estabilidade prolongada. Sem novo probe Codex, commit ou noite real.

`powercfg /a` confirmou suspensão S3 e hibernação disponíveis. Nenhuma suspensão real
executada. Após autorização, Codex 0.155.1 instalado na sandbox pelo pacote oficial.
Device login concluído; `codex login status` retornou `Logged in using ChatGPT`.
Nenhum token do host copiado; nenhuma inferência Codex usada nessa verificação.

Permanecem verificações de integração: quota/contexto reais, orçamento entre resets,
executor/fallback/revisor, dados protegidos do worker, recuperação após crash/suspensão,
comando de início, relatório final e aviso120s com cancelamento por atividade.
Sem modelo/runtime novo ou credencial importada silenciosamente. Não ativar noite real
com base somente nos testes do módulo de entrega ou da política simulada.

## Supervisor sintético: entrega parcial, bloqueada por isolamento

Gate1 específico aprovado; Fable implementou `night_supervisor.py` e testes na sandbox.
Namespace Linux user/PID contém filhos mesmo com setsid; deadline independente do
stdout, checkpoint antes do go, recuperação interrupted sem reenvio automático.
Quota/policy/session permaneceram byte-idênticos. Nenhuma integração real foi liberada.

Primeira chamada37922 terminou1 sem envelope após RED30testes; chamada85557 concluiu0,
sessão3e651e71-f232-4c89-a16c-8a69e98a137b,422902ms/17turnos. Input28/output34558,
cache creation59831/cache read569340; USD3.067135 list, não quota da assinatura.
Coordenador reproduziu191testes17.037s(189OK/2skip), compile/lint crítico verdes.
Trace parent-only368/517=71,2%; subprocessos não rastreados, cobertura total desconhecida.

Revisão Astra medium única:2HIGH+1MEDIUM. Worker compartilha UID/filesystem e consegue
escrever no armazenamento confiável; identidade ilegível era tomada por processo morto;
destrutor de Popen podia colher worker antes do waitpid e perder exit code.
Fable corrigiu os dois últimos, adicionou cleanup de handles após recuperação confirmada
e8regressões. Chamada8619 terminou1 sem envelope final, artefatos recuperados/verificados.
Snapshot supervisor-v2 SHAe00bf6b510d6eec30e7e07f256aa564a3ede11870d5cb00d10dd8f5668c94fed.
Coordenador199testes18.840s:197OK/2skip; compile/lint crítico verdes. ResourceWarnings
persistem no teste de encerramento não confirmado; não declarar resolvidos por serem testes.

HIGH de escrita nos checkpoints permanece aberto: precisa isolamento efetivo de
filesystem/permissões no próximo Gate1. Apenas worker sintético confiável neste estágio.
Sem cgroup CPU/memória, sem suspensão/loop/commit. Nenhuma segunda revisão Astra.

## Isolamento de filesystem: recorte verificado

Gate1 seguinte aprovado. Reutilizado bubblewrap0.11.1 já instalado, sem instalação ou
elevação. Política: raiz mínima, runtime `/usr` RO, workspace explicitamente validado RW,
proc/dev/tmp privados e rede desligada. Nenhuma montagem de credenciais, sockets do host
ou armazenamento confiável. A política é responsabilidade do chamador, como descreve
a [documentação oficial do bubblewrap](https://github.com/containers/bubblewrap#sandbox-security).

Primeira chamada Fable82701 terminou0 após266300ms, sem implementação; relatório do
executor alegou540s incorretamente. Registrado no STATE. Probe nested travado não se
reproduziu em dois comandos do coordenador (<1s cada). Retomada8484 terminou0,
373942ms/47turnos, sessão9a577bc1-84c9-4c89-a948-ace6fb3f6a18. Snapshot isolation-v1:
211testes20.007s,209OK/2skip, compile/lint verdes, ainda3ResourceWarnings.

Revisão Astra medium deste novo escopo, única:2HIGH reproduzidos. Variáveis do worker
atingiam loader do bwrap antes da contenção; mount aninhado podia expor checkpoint.
Fable corrigiu bootstrap com ambiente confiável vazio, transportando env como dados e
aplicando-o só no worker; rejeitou mounts por ID do kernel, não só dispositivo/caminho.
Coordenador identificou exceção residual em ancestral montado; continuação delimitada
fechou o mesmo achado exigindo workspace no mount da raiz `/`. Sem segunda revisão LLM.
Fixture foi corrigida para a instância dona dos handles também finalizar sua recuperação;
asserções de bloqueio e recuperação entre instâncias preservadas.

Snapshot final `isolation-v2`: supervisor
SHA256 `e2ffc0fb2b25309198bd0937cc53f7da9424fd50a71ec971e0e01ae27d6e9d43`.
Coordenador reproduziu220testes20.889s: **218OK/2skip**, zero ResourceWarnings,
py_compile e Ruff E9/F63/F7/F82 verdes. Quota/policy/session mantiveram hashes anteriores.
Evidência RED comprovou adulteração de lock/sentinel, bootstrap loader e alias ancestral;
GREEN comprovou negação com estado preservado e escrita permitida no workspace.

Limites: mount da raiz do controlador é confiável; workspaces em mounts separados,
inclusive `/tmp` dedicado, são recusados. Ator privilegiado do host alterando mounts
concorrentemente fica fora da fronteira. Sem cobertura total de subprocessos medida,
sem cgroupCPU/RAM, integração real de provider/contexto/corpus e suspensão pendentes.
Rede desligada deste worker sintético não constitui adaptação pronta para CLIs online.
Sem commit/merge/noite real; catálogos continuam bloqueados até preflight e integração.
