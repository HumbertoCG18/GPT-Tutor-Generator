# Retomar o trabalho em sessão nova: workflow das três CLIs

## Objetivo atual

Resolver o aviso `Skill descriptions were shortened to fit the skills context budget`
no Codex usado pelo Alethe e no terminal, sem instalar outra stack ou remover
capacidades por suposição. O usuário confirmou que o aviso apareceu em conversa
retomada no Alethe e também no terminal; ainda não confirmou teste em conversa nova.

## Estado verificado

- Implementação autorizada nas três CLIs registrada em workflow-implantacao_15-09.md.
- Laboratório: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab.
- verify.py passou: 75 arquivos pessoais sem drift; instruções pessoais idênticas.
- Instância nova do Codex e app-server novo: 24 skills pessoais/sistema habilitadas.
- Conversa importada anterior contém catálogo de 94 descrições, inclusive recursos
  desativados. A presença no histórico não prova que esse catálogo cause o aviso novo.
- Três testes exec e uma inicialização interativa 0.154.0 não mostraram o aviso.
- Tentativa de retomar a conversa ativa no terminal foi bloqueada por sessão aberta
  em outra aplicação. Encerrada sem forçar o lock, sem enviar prompt e sem editar JSONL.
- Existem versões diferentes: executável OpenAI 0.154.0; wrapper npm 0.140.0;
  app-server de plugins 0.154.0-alpha.6.2. Não assumir que o mesmo comando usa sempre
  o mesmo binário. No teste interativo foi usado o executável OpenAI 0.154.0.

## Teste da sessão nova (15/09, 23:55 America/Sao_Paulo)

- Sessão `01a0a824-59b4-72f1-ab1b-fcf3c39bdb36`: metadata do JSONL confirma
  `originator=codex-tui`, `source=cli`, `cli_version=0.154.0`.
- Processo ancestral desta execução: PID 8812, executável
  `C:/Users/Humberto/AppData/Local/Programs/OpenAI/Codex/bin/codex.exe`.
  Consulta direta `--version`: `codex-cli 0.154.0`.
- Catálogo efetivamente recebido: 44 entradas em `### Available skills`, extraídas
  da mensagem developer no JSONL desta sessão. Não equivale às 24 entradas pessoais
  da consulta anterior de outra instância; inclui skills de plugins.
- Usuário confirmou nesta conversa: "Não apareceu". Ausência do aviso no terminal
  novo confirmada pelo usuário; causa do aviso anterior ainda não reproduzida.
- Nenhuma configuração alterada nesta retomada. Falta aceite de conversa nova
  aberta pelo Alethe; não declarar o defeito resolvido.

## Próxima ação

Abrir conversa nova pelo Alethe e registrar aviso, binário/versão e catálogo recebido;
depois rodar verify.py no laboratório. Manter a conversa antiga disponível como histórico.
Se houver aviso, reproduzir no mesmo binário e comparar catálogo/configuração efetiva.
Não concluir que Alethe regravou arquivos, que basta limpar memória ou que o defeito
foi resolvido apenas por contar o catálogo de outra instância.

## Decisões preservadas

Ponytail limita escopo; ECC conduz processo; Graphify principal; CBM fallback nas três
CLIs, com auto_index=false e auto_watch=false. RTK 0.49.0 explícito apenas para pytest.
Skillfile não promovido após falha no piloto local. claude-mem não grava por quota;
não reiniciar worker. Fontes pessoais comuns no laboratório, distribuição por hashes.
Não alterar fontes do GPT Tutor nem trabalhos de atribuição paralelos por esta tarefa.

Tracker vivo: pendencias.md. Relatório: workflow-implantacao_15-09.md.
