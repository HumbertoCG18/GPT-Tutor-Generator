# Delegação com contexto delimitado

Uma CLI externa inicia sua própria sessão: não presumir herança do catálogo, hooks, skills carregadas ou contexto do coordenador. Não reinstalar skills para corrigir uma chamada. Usar este contrato nas três CLIs, preservando as instruções obrigatórias do destino.

1. Classificar o pedido como planejamento, auditoria, revisão de diff, pesquisa ou implementação. Planejamento Codex produz plano/aceites; auditoria AGY produz achados com evidência, sem assumir implementação. A revisão automática do revisor responde ao checklist do diff fixado; hipótese nova, varredura de corpus e experimento são pesquisa, não extensão silenciosa da revisão. Registrar lacunas e encerrar ao satisfazer o critério, sem buscar melhorias fora do escopo.
2. Enviar brief curto e autocontido: objetivo, tipo, cwd absoluto, branch/HEAD e identificação do diff, arquivos permitidos, restrições, critérios de término, testes já executados e dúvidas concretas. Anexar só evidência decisiva com arquivo:linha; logs completos ficam em arquivo. Não copiar histórico, catálogos ou manuais inteiros. Não resumir conjuntos/dados cuja diferença decide o achado.
3. Indicar somente skills necessárias, com caminho resolvido e motivo. No destino, distinguir instalada, descoberta, lida sem truncamento e aplicada com resultado verificável. Ler a skill selecionada separadamente; usar referências específicas e trechos consecutivos se necessário. Caminho ausente ou ferramenta não exposta exige registrar limitação e seguir o fallback documentado, sem inventar chamada nativa. A leitura do SKILL.md sozinha não prova aplicação.
4. Localizar com rg em arquivos/diretórios delimitados; para estrutura, usar Graphify explain e path com símbolos/IDs exatos antes de query aberta, conferindo o projeto do grafo. Depois ler função/bloco relevante, com arquivo:linha, e confirmar no código. Grafo orienta navegação, não substitui fonte; ausência de caminho não prova ausência de relação. Não repetir trecho inalterado já presente no contexto. Após compactação ou mudança do arquivo, recuperar apenas o necessário.
5. Agrupar leituras independentes pequenas, sem esconder skills em um lote grande. Mirar até 2.000 tokens de saída por ferramenta; ajustar explicitamente quando a evidência exigir. Limite de saída não garante completude: detectado truncamento, restringir a consulta e recuperar só a parte omitida, sem repetir o lote inteiro nem concluir sobre conteúdo invisível. JSON/CSV: selecionar colunas e linhas por código determinístico, guardando totais e dados decisivos. Python no Windows: configurar stdout UTF-8 antes de imprimir texto Unicode.

Antes de iniciar, preencher no brief:

```text
tipo / objetivo / criterio_de_termino:
cwd / branch / HEAD / diff_fixado:
arquivos_permitidos / restricoes:
evidencias_decisivas / testes_ja_executados:
skills_necessarias: caminho -> acao verificavel (ou nenhuma)
perguntas_delimitadas:
saida: achados com arquivo:linha, evidencias, limitacoes; sem repetir o brief
```

Retornar apenas resultado final ao coordenador; manter eventos completos no log local. Registrar ID da sessão, skills realmente aplicadas e lacunas. Medir chamadas, input total/cache/output separados, crescimento do contexto e tempo. Bytes removidos e tokens em cache não equivalem a economia comprovada de quota; comparar tarefas equivalentes antes de concluir.

O timeout de 10 minutos continua obrigatório no chamador. Uma ferramenta retornar um ID de background não prova que encerrará o processo nesse prazo: conferir o mecanismo do chamador e registrar timeout real ou limitação. Esta política não instala um supervisor nem impõe teto técnico de tokens.

Dimensionar cada tarefa para o teto: o Alethe informa o orçamento no início do brief (responder até 70%) e, no timeout, entrega o que o worker escreveu até ali; o que ele só leu se perde. Não mandar aviso no meio do turno: o Codex só o lê depois de terminar o texto em curso, em geral a própria resposta, e gasta outra rodada respondendo (30/09: 3 de 6 respostas prontas viraram timeout). Uma tarefa é um entregável; mirar conclusão em até 70% do teto. Dividir quando o brief juntar decisões ou perguntas com fontes próprias, e cada parte leva só as suas fontes. Em leitura pesada, pedir a saída escrita antes do aprofundamento. Medido em 18 briefs reais do Alethe (29-30/09): as 9 tarefas de pesquisa/planejamento concluídas levaram 263-541 s e 3 estouraram 600 s, uma delas com 3 arquivos citados, portanto contagem de arquivos não prevê estouro. Caso que motivou a regra: 15 arquivos numa tarefa, timeout com 1.734 tokens de saída; a outra metade, com 4 arquivos, concluiu em 495 s. delegate-gate.py recusa tarefa que cite mais de 8 arquivos (maior brief concluído da amostra), exceto revisão de diff ou brief_grande_autorizado: é piso mecânico para o caso grosseiro, não o dimensionamento. Rever os números com novas medições.

## Dispatch pela Orquestração do Alethe

- Em sessão Alethe, consultar alethe_status e o estado da tarefa antes de lançar;
  localizar Job já associado, inclusive queued/running/blocked/interrupted. Dúvida
  sobre chamada existente bloqueia novo dispatch; não duplicar execução.
- Usar alethe_delegate para trabalho aprovado e visível na Orquestração. label
  referencia campanha/tarefa; tasks contém o brief acima. Uma chamada gera uma Run.
  Registrar os IDs retornados plannerId/runId/jobId/threadId no estado existente,
  sem substituir task_id nem escrever diretamente no armazenamento do Alethe.
- alethe_delegate inicia execução; não usá-lo para cadastrar rascunhos. Conferir
  agent, cwd, isolamento, permissões e timeoutSeconds (máximo 600 neste contrato;
  exceção aprovada em 01/10: o papel validador-externo usa 1800).
  Limite de concorrência não autoriza paralelismo nem dois escritores no mesmo alvo.
- Modelo e permissão vêm de papel configurado em Preferências > Orquestração, não do
  padrão da CLI: alethe_status lista os papéis e o que cada um resolve; delegar com
  role, sem agent/model/effort/readOnly/timeoutSeconds (o Alethe recusa a mistura).
  Papéis esperados: reviewer (T1/T2) e reviewer-high (T3), ambos readOnly; planner-t1,
  planner-t2, planner-t3 readOnly para planejamento Codex; executor-t1, executor-t2,
  executor-t3 (Claude, modelo/effort do nível) para implementação delegada;
  validador-externo (Codex gpt-6-astra, high, readOnly, 1800 s) para a validação externa de
  um pacote congelado, até 2 rodadas automáticas antes da rodada final do usuário no app. Papel
  ausente: model/effort e readOnly explícitos pelo nível em routing.md, registrando a
  limitação. Claude aceita model e effort, mas recusa readOnly: trabalho somente
  leitura vai para Codex ou fica no agente ativo. Conferir role/model/effort/readOnly
  no retorno antes de depender deles.
- Implementação fica no agente ativo por padrão. Delegar a executor-tN só quando o
  investigador decidir (unidades independentes ou nível diferente do da sessão), com
  isolate=true: o worker Claude roda sem canal de aprovação (bypassPermissions) e só
  escreve na própria worktree. O diff volta por alethe_diff e passa pela revisão e pelo
  Gate 2 antes de qualquer integração; nunca dois escritores no mesmo alvo.
- Codex e derivados (codex exec, codex:rescue, codex-companion) em sessão Alethe vão
  por alethe_delegate, para aparecerem na Orquestração. Sem model/effort/readOnly no
  schema, registrar a limitação e seguir o caminho documentado da ação.
- alethe_check recolhe resultados; alethe_diff fornece o diff disponível. Conferir
  artefatos/testes antes do aceite. alethe_steer orienta turno ativo; alethe_send
  envia trabalho na Thread existente e pode iniciar turno: ambos respeitam escopo,
  orçamento e autorização. alethe_cancel exige alvo exato e verificação de parada.
- Reutilizar esses mecanismos sem presumir equivalência com isolamento, modelo
  observado, encerramento completo ou Gates. Capacidade ausente é bloqueio explícito;
  não recorrer a CLI externa silenciosamente nem renovar tentativa/revisão.
