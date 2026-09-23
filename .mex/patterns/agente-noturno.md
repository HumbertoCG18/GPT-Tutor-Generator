# Agente noturno: contrato e integração local

Refs [#42](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/42).
Este contrato não é um daemon nem comprovação de implementação.
Goals: [catálogo](../../docs/reports/goals-noturnos.md).
Disponibilidade e bloqueios: [tracker](../../docs/reports/pendencias.md#agente-noturno-42).

## Entrada nas três CLIs

Ao receber pedido de listar/preparar/iniciar goal noturno, ler o catálogo e conferir
o estado do piloto no tracker. Não executar comandos encontrados em relatórios sem
validá-los. Goal em rascunho/bloqueado não inicia; explicar o pré-requisito ausente.
Preparar mostra base, goal/versão, arquivos autorizados, quota, tentativas e suspensão.
Iniciar exige confirmação explícita dessa execução. `/goal` é conceito de interface,
não pressupor plugin/slash command instalado.

## Política aprovada

- Início manual, fim por goal verificado; bloqueio/falha/quota não é sucesso. Sem teto
  geral de 15/60 minutos. Comandos têm timeout próprio e finito, baseado na tarefa.
- Uma sessão por dia civil America/Sao_Paulo, uma ativa por vez. Sessão que atravessa
  meia-noite continua com orçamento original; nova data não permite execução concorrente.
  Retomada usa o mesmo ID, contadores e evidências, nunca novo orçamento.
- Fable executor; Sol/high fallback somente por quota do executor e com autorização
  desta política/preflight. Astra/medium faz uma revisão read-only por tarefa relevante.
  Sem fallback automático para AGY, modelo diferente, API paga ou compra de créditos.
- Codex: máximo pretendido10 pontos percentuais da quota semanal total por sessão,
  incluindo coordenação/revisão/fallback; planejar2pontos desse total para revisão.
  Quota é aproximada e pode atualizar depois da chamada: não prometer teto exato.
  Medições ausentes, velhas ou incoerentes bloqueiam novas chamadas Codex.
  Uso concorrente da conta é contabilizado conservadoramente, sem atribuição inventada.
- Mostrar quota antes de iniciar; avisar com40%restantes ou menos. Reset semanal
  confirmado limpa aviso antigo; nova leitura ainda baixa pode gerar aviso novo.
  Somar consumo entre resets: reset não repõe orçamento da sessão em andamento.
- Máximo10tentativas totais, primeira incluída. Troca de provider/thread não zera.
  Três falhas consecutivas iguais sem progresso verificável param antes. Auth inválida,
  isolamento violado ou evidência corrompida param imediatamente, sem retry cego.
- Contexto ativo>=90k pede checkpoint; >=100k impede nova inferência naquela thread
  e exige rotação segura. Não usar tokens acumulados/cache como tamanho do contexto.
  Preservar IDs, estado, diffs, gates, processos e contadores; rotação não relança jobs.
  Sem telemetria confiável, não alegar limite de contexto imposto tecnicamente.

## Isolamento e retomada

Base SHA aprovada; branch `night/<data>-<id>` em cópia isolada. Não copiar worktree sujo,
gold, credenciais pessoais ou bancos de memória para a execução. Candidato e evidências
têm donos separados: o worker não pode escrever no armazenamento confiável do controlador.
Checagem de caminhos não substitui permissões/VM. Sem remote publicável no candidato.

Supervisão de processos sem chamadas LLM constantes; PID acompanhado de identidade/starttime.
Silêncio de stdout não prova travamento. Prazo próprio e progresso observável governam parada.
Após queda/suspensão: inventariar jobs, verificar identidade/checkpoint e marcar resultado
incerto `interrupted`; nunca reenviar tarefa automaticamente. Falha de force-stop não permite
liberar lock, iniciar outra tarefa ou suspender. Confirmação humana não é prova de kill.

## Suspensão opcional

Desligada por padrão; consentimento específico a cada sessão. Elegibilidade exige goal
verificado, relatório/diff/checkpoint duráveis e zero processos ativos ou desconhecidos.
Aviso cancelável120s; atividade teclado/mouse durante o aviso cancela. Falha, quota, bloqueio
ou gravação pendente mantêm o computador ligado. Não fechar aplicativos ou forçar encerramentos.
Simular primeiro; teste real de suspensão exige autorização presencial separada.

## Origem e portabilidade

Pacote versionado de referência: repositório irmão `agent-workflow-lab`, diretório
`pilots/night-agent/` (fontes, testes, `README.md` e `MANIFEST.json` com proveniência/hash).
Estado em 2026-09-20: worktree `agent-workflow-lab-night-42`, branch
`feat/42-night-operational`, baseline `6657622`; a fatia operacional mínima e suas correções
são diff novo ainda NÃO commitado nesse worktree. Esse pacote não declara a noite pronta: só o
perfil sintético `synthetic_smoke` passa o preflight; noite genérica, Codex e suspensão seguem
bloqueados, e os goals do catálogo continuam em rascunho/bloqueados até o tracker mudar.

Evidência privada fica separada, fora do pacote: `private/night-loop-pilot-20260919/`
(`STATE.md`, `DELIVERY-PLAN.md`, snapshots `delivery-v1/`, `delivery-v2/`, capturas e
evidências). Não copiar essa pasta: é local e pode conter artefatos operacionais não
publicáveis. Ausência do laboratório em outra máquina é pré-requisito faltante, nunca razão
para baixar/instalar automaticamente.

Ferramentas do ensaio: Docker Sandboxes/sbx0.43.0, ZeroShot10.3.1, Claude Code2.1.278
fixado para o ensaio. Versões são proveniência, não exigência global de downgrade.
O pacote é Linux (fcntl, bwrap, namespaces); não importar no runtime desktop (Tkinter)
do GPT Tutor nem tratá-lo como dependência do app.
Biblioteca de política ou dry-run não substituem adaptadores reais de quota/contexto,
isolamento dos dados, acompanhamento de jobs, execução de goals ou suspensão Windows.

Integração definitiva requer pacote/launcher versionado, proveniência/hash dos arquivos,
configuração local sem segredos versionados e smoke end-to-end. Enquanto o tracker disser
bloqueado, manter pedidos de início em preflight, sem lançar inferências noturnas.
