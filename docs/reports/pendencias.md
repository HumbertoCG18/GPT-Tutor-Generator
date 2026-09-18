# Pendências — tracker vivo

## [USER] Workflow de entrega e engenharia do produto (17/09)

- [#16](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/16): deltas de Karpathy aplicados na fonte e nas três instruções pessoais; quatro arquivos com SHA-256 `93ad2a58...`, `verify.py` verde (75 arquivos, zero divergências). Falta remote no `agent-workflow-lab` para PR/versionamento.
- [#10](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/10): contrato e templates recuperados da worktree antiga e preparados sobre `origin/main`; Gate 2/PR pendentes.
- [#11](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/11): baseline medido em 11 arquivos UI/27 classes/17 threads; jornadas centrais têm progresso e cancelamento, fluxos auxiliares e testes de estado permanecem incompletos. Matriz em `2026-09-18-gaps-issues-abertas.md`.
- [#12](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/12): 28 módulos importam logging; 224 chamadas usam `logger` e 2 usam `logging.error`; sem correlation/run/trace ID e sem backend. Plano local-first + Sentry opt-in registrado; nenhuma exportação configurada.
- [#13](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/13): concluída pelo PR #30; check `core` obrigatório na `main`, com suíte, cobertura por plataforma, Ruff e contrato arquitetural.
- [#14](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/14): zero artefato web de produto; gates definidos, instalação continua bloqueada até a stack C6 existir.
- [#17](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/17): três referências Agent Skills adaptadas sem plugin/dependência; Gate 2/PR pendentes.
- [#22](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/22): 12/12 registros reais concluídos; 10/12 respostas corretas e 9/12 conformes ao schema. Claude fica MCP manual/restrito via `server.bundle.mjs`, sem hook; Codex e AGY foram removidos. Relatório separado preparado; issue continua aberta pelas falhas Codex/auditoria e Codex/UI.
