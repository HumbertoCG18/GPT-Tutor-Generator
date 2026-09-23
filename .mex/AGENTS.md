---
name: agents
description: Identidade, invariantes e comandos do GPT Tutor
---

# GPT-Tutor-Generator

Desktop Python/Tkinter que converte materiais acadêmicos em repositórios-tutor Markdown.
Navegação: [ROUTER.md](ROUTER.md). Engenharia: [patterns/engenharia-produto.md](patterns/engenharia-produto.md).

## Invariantes

- Ler fontes antes de editar; validar APIs/flags/versões, sem adivinhar. Pular arquivos >100 KB salvo necessidade concreta.
- engine.py é fachada: lógica nova em subpacotes; imports vêm do módulo especializado.
- Gemini: google-genai, imports lazy; nunca o SDK legado google-generativeai nem a classe GenerativeModel (padrões em scripts/hooks/gemini-antipattern-guard.js).
- code_curation.json gerado é cache: podar obsoletos antes de ler, escrever atomicamente.
- Fixtures reproduzem contrato real com proveniência: [convenções](context/conventions.md) e [contratos](context/institutional.md). Ler antes de código/testes.
- Estado vivo apenas em docs/reports/pendencias.md; resultado concluído sai da fila viva e entra em Concluído. Atualizar só o escopo da tarefa.
- Plano/spec/report concluídos com todos os aceites verdes vão para Feitos/ do próprio diretório; git mv quando trackeados. Não arquivar trabalho incompleto.
- MEX guarda intenção/convenções/contratos; Graphify estrutura. Sem duplicar estado no mapa/contexto.
- Ao mudar código, atualizar o grafo; ao mudar arquitetura/pipeline/atribuição, atualizar docs/Overview-Sistema.html.
- Ao fechar tarefa, corrigir contexto obsoleto e padrão desviado; padrão novo só se necessário, com entrada em patterns/INDEX.md.
- Sem comentários óbvios nem docstrings de múltiplos parágrafos. Sem floreio/sicofantia.

## Comandos

- Suíte: python -m pytest tests -q
- Teste focado: python -m pytest tests/<arquivo>.py -q
- Aplicativo: python app.py

Issue/PR/release, Gates, delegação e comunicação seguem os núcleos pessoais/workflow;
este arquivo não os duplica. Referência histórica detalhada: [project-invariants-history.md](context/project-invariants-history.md).
