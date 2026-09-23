# GPT-Tutor-Generator

Desktop Python/Tkinter que converte materiais acadêmicos em repositórios-tutor Markdown.
Fonte única das instruções do projeto para Codex, Claude Code e AGY.

## Onde procurar (ler só o pertinente à tarefa)

- Localizar a fonte de um domínio (motor, PDF, saída, decisões, contratos): `.mex/ROUTER.md`.
- Issue, PR, release, UI, observabilidade e qualidade: `.mex/patterns/engenharia-produto.md`.
- Delegar, retomar tarefa, Gates, revisão ou quota: `.workflow/README.md`; estado em `.workflow/local/active-task.md`.
- Campanhas: bloco `fila-campanhas` de `docs/reports/pendencias.md`; política em `.workflow/references/campaigns.md`.
- Estrutura e callers: Graphify explain/path; fallback em `.mex/patterns/codegraph-fallback.md`.
- Goals ou agente noturno: `.mex/patterns/agente-noturno.md` e `docs/reports/goals-noturnos.md`; conferir bloqueios no tracker antes de iniciar.

## Invariantes

- Ler fontes antes de editar; validar APIs/flags/versões, sem adivinhar. Pular arquivos >100 KB salvo necessidade concreta.
- engine.py é fachada: lógica nova em subpacotes; imports vêm do módulo especializado.
- Gemini: google-genai, imports lazy; nunca o SDK legado google-generativeai nem a classe GenerativeModel (padrões em scripts/hooks/gemini-antipattern-guard.js).
- code_curation.json gerado é cache: podar obsoletos antes de ler, escrever atomicamente.
- Fixtures reproduzem contrato real com proveniência: [convenções](.mex/context/conventions.md) e [contratos](.mex/context/institutional.md). Ler antes de código/testes.
- Estado vivo apenas em docs/reports/pendencias.md; resultado concluído sai da fila viva e entra em Concluído. Atualizar só o escopo da tarefa.
- Plano/spec/report concluídos com todos os aceites verdes vão para Feitos/ do próprio diretório; git mv quando trackeados. Não arquivar trabalho incompleto.
- MEX guarda intenção/convenções/contratos; Graphify estrutura. Sem duplicar estado no mapa/contexto.
- Ao mudar código, atualizar o grafo; ao mudar arquitetura/pipeline/atribuição, atualizar docs/Overview-Sistema.html.
- Ao fechar tarefa, corrigir contexto obsoleto e padrão desviado; padrão novo só se necessário, com entrada em .mex/patterns/INDEX.md.
- Sem comentários óbvios nem docstrings de múltiplos parágrafos. Sem floreio/sicofantia.

## Comandos

- Suíte: python -m pytest tests -q
- Teste focado: python -m pytest tests/<arquivo>.py -q
- Aplicativo: python app.py

A suíte local não tem acesso de produção: rode-a, corrija falhas causadas pela mudança
pedida e rode de novo os testes afetados sem pedir aprovação a cada passo. Isso não inclui
rebuild de tutores, rede, LLM ou uso do gold como insumo.

Issue/PR/release, Gates, delegação e comunicação seguem o workflow compartilhado; este arquivo
não os duplica. Histórico detalhado: `.mex/context/project-invariants-history.md`.
