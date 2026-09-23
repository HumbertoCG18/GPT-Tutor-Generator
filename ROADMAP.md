# Roadmap — GPT Tutor / AlexandrIA

Atualizado em 23/09/2026. Índice por horizonte, uma linha por item.
Estado vivo e prioridade das campanhas: bloco `fila-campanhas` de [`docs/reports/pendencias.md`](docs/reports/pendencias.md).
Detalhe das ideias de produto: seção **CAMPANHA FUTURA (produto) [BACKLOG VIVO]** do mesmo tracker, que é a caixa de entrada.
Ideia nova entra primeiro na caixa; aqui só entra depois de triada. Ferramentas avaliadas e não adotadas: [`.workflow/pendencias_workflow.md`](.workflow/pendencias_workflow.md).

## Agora

- **Motor >90% por eixo** (subunidade primária, unidade e bloco, separadamente), sem LLM no regime cru. Campanhas CRU-02..04; issues #47–#52.
- **Agente noturno** (#42): execução noturna de campanhas com sandbox, preflight, quota e Gate 2 humano. Bloqueado na autenticação da sandbox.

## Próximo — campanha web C6 (AlexandrIA, painel web local)

Motor segue headless e intocado; a web troca a vitrine. Contrato de qualidade na #14 (branch `docs/14-c6-quality`); gates na #41.

- **Painel fase A (read-only):** "minha semana" entre cursos, avaliações com escopo, estado dos materiais, freshness do SARC, `.ics`.
- **Dashboard como home:** entregas, próximas aulas com sala/laboratório (SARC e OpenSarc), uso/quota das LLMs.
- **Página de health:** bridge/LLM offline, dependências, freshness por curso, último build.
- **Grafo na web:** unidades/subunidades/blocos/materiais/provas navegáveis (Cytoscape.js ou force-graph sobre os índices).
- **Upload pela web** com extração defensiva (zip-slip/zip-bomb, sufixos, limites) → staging → motor.
- **Settings — um control plane:** providers, quotas, fontes e flags por curso numa config só; pré-requisito da distribuição.
- **Painel fase B:** curadoria na web (pinos, overrides, reprocess com preview); aposenta a GUI Tkinter depois de paridade e Gate 1 próprio.
- **Tutor como CLI agent-native:** consulta ao acervo com saída JSON/NDJSON para outros agentes.
- **Citação por página** nos artefatos, como extensão da proveniência atual.

## Depois — camada LLM por conta (assinatura, não API)

- **Bridge local → CLI autenticado**, um provider primeiro: chat tutor sobre os índices e extração de PDF.
- **Extração PDF → Markdown:** bake-off MinerU × Docling × CLI multimodal × Datalab (Datalab vira último fallback); extração local com torch CUDA na GPU para quem não tem Datalab. Absorve os antigos itens MinerU e Marker-API.
- **Imagens como conhecimento de primeira classe:** `image_id` estável, render no chat, pergunta sobre a imagem.
- **Question Banks** por unidade/subunidade; **Living Books**; **memória em camadas com proveniência**; **workspaces por disciplina** com instruções persistentes.
- **Modo Projects por provedor** (repo-tutor como KB) e **coleta Moodle assistida** (read-only, sessão logada).
- **Agenda:** sync com Google Agenda além do `.ics`.
- **Modo Exercícios / Practice:** feedback de código do aluno ([plano](plans/exercises-mode-code-correction.md)); depende do refactor material-agnostic.

## Distribuição

- **PyPI e/ou Docker** (web + CLI sem clone); exige o control plane e nenhum dado pessoal no pacote.
- **Instalador Windows (Setup.exe)** para usuários sem ambiente de desenvolvimento.

## Estacionados (reabrir com gatilho)

- **Frameworks RAG / embeddings:** adiados; gatilho = busca lexical do painel medir mal em sinônimos, e então embedding local pontual.
- **NotebookLM / Notebooks do Gemini:** sem demanda desde junho; o Modo Projects cobre o uso de revisão pré-prova.
- **Export Obsidian/Notion:** rebaixado a bônus (o grafo fica na web); ~1 script sobre o JSON dos índices.
- **Vídeos Manim**, **Mastery Path** e roteamento de modelo por tarefa na bridge.
- **Limpeza de campos do manifest/índice:** só com auditoria de consumo campo a campo, pós-cutover.

## Descartados

Multi-usuário/auth, canais de IM, marketplace de skills/personas, loja de MCP: peso de produto público para um caso de uso local de um usuário.

## Concluído

- **Cronograma visual / dashboard da timeline** — 12/05/2026 (`docs/superpowers/plans/Feitos/2026-05-12-timeline-dashboard-plan.md`).
- **Student State v2** — 16/04/2026, com import manual em 22/04.
- **Sinal de data no nome do arquivo (`DD.MM`)** — no motor (`src/builder/routing/dates.py`).
- **Code Summarization via Gemini** — 02/06/2026; pattern `.mex/patterns/gemini-code-summarization.md`.
- **Exportação DeepTutor** removida em 17/09; volta como implementação futura depois do ambiente web.

A versão detalhada anterior (junho/2026) está em [`docs/reports/_archive/2026-06-roadmap-v3.md`](docs/reports/_archive/2026-06-roadmap-v3.md).
