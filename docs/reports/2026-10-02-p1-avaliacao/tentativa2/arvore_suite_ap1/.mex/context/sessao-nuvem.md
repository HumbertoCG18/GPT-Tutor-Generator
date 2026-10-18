---
name: sessao-nuvem
description: Guia para sessão do Claude Code na nuvem, ou qualquer agente sem o contexto local — o que falta, o que não tocar, arquitetura, regras e frentes
triggers:
  - nuvem
  - cloud
  - sessão remota
  - claude.ai/code
  - agente noturno
edges:
  - target: context/architecture.md
    condition: mapa de pacotes, pipeline e motor
  - target: context/setup.md
    condition: instalar e testar no Linux
  - target: context/decisions.md
    condition: porquê de uma decisão, antes de propor mudança
last_updated: 2026-09-24
---

# Sessão na nuvem — ler antes de agir

Este guia existe para a sessão remota não adivinhar, não sujar e não quebrar o que já existe.
Ele resume e aponta; não substitui a fonte. Precedência: código > tracker
(`docs/reports/pendencias.md`) > handoff mais recente > este guia. Se algo aqui contradisser o
código ou o tracker, siga a fonte e registre a divergência no handoff da sessão (§9).

## 1. Parar antes de começar

Pare e escreva só um diagnóstico, sem código, se qualquer item abaixo for verdade:

- O pedido não traz escopo e aceite explícitos. Pedido vago não é Gate 1 (§6).
- A tarefa depende de prioridade ou estado de campanha e o tracker do clone não tem o bloco
  `<!-- fila-campanhas-start -->`. Em 24/09 esse bloco e os handoffs de 21 a 23/09 existiam só na
  máquina local, sem commit; o clone estaria atrás. Tarefa presa a uma issue, com escopo e aceite
  no pedido, não depende do tracker e pode seguir.
- A tarefa exige algo da §2 que a nuvem não tem (tutores, gold como insumo, rede no produto).
- A tarefa pertence a uma campanha marcada como bloqueada no tracker.

Primeira ação de toda sessão, antes do pedido: conferir o ambiente com
`python3 -c "import pydantic, pytest"` e `ls "$(git rev-parse --git-common-dir)/hooks/pre-commit"`;
ler `/tmp/setup-nuvem.log`, se existir. Se faltar dependência ou hook, rodar os comandos Linux de
[setup.md](setup.md) e registrar no handoff. Medido no piloto 3 de 24/09: o script do ambiente roda
como root em `/home/user`, fora do clone; instala as dependências pip; o `tkinter` fica ausente (PPA
bloqueado) e o hook é sempre instalado pela sessão, com `chmod +x`.

## 2. O que a nuvem não tem

| Ausente | Consequência | Conduta |
|---|---|---|
| Instruções pessoais do usuário e o laboratório `agent-workflow-lab` (fonte canônica, caminho Windows) | O README do workflow aponta para um caminho Windows | Usar os snapshots de `.workflow/` e registrar o fallback, como o README permite |
| graphify-out/ (ignorado) e o MCP do Graphify | Sem explain/path | `rg` e leitura direta; mapa em [architecture.md](architecture.md). Não gerar grafo |
| Repositórios-tutor irmãos (../*-Tutor), subjects.json do usuário, moddle/, PDFs (`*.pdf` é ignorado), `.env` | Replay, zero-diff, harness do motor e rebuild não rodam; testes de dados reais dão skip | Não recriar dados nem inventar fixture sem proveniência |
| .workflow/local/active-task.md (ignorado) | Sem estado de tarefa em curso | Estado vai no handoff commitado (§9) |
| Codex, AGY, Astra (revisor), Alethe, claude-mem | Sem delegação nem revisão Astra | A revisão é o PR em rascunho mais o Gate 2 humano |
| Pre-commit do git (.git/hooks) e gitleaks | Commit sem guarda de segredo | Instalar o hook na primeira ação (acima), se ausente; sem gitleaks ele só avisa. Nunca commitar segredo |
| Commits locais sem push e trabalho não commitado | A nuvem só vê o GitHub | Não presumir que o clone é igual à máquina do usuário |

## 3. Branch — escolher antes de tudo

- O padrão do remoto é `main`. O motor vive em feat/motor-atribuicao (PR #9 aberto, em
  conflito). As duas divergiram em 06/2026: em 24/09 eram cerca de 60 commits só na `main` e 1100
  só no motor.
- Só no motor: `src/builder/routing/motor/`, `src/builder/ops/assignment_run.py`, cerca de 200
  testes, réguas e relatórios do motor.
- Só na `main`: src/observability.py, movimento reduzido na UI, `pydantic` declarado no
  `pyproject.toml` e a CI python-quality.yml (check obrigatório `core`).
- Motor, atribuição, timeline → base feat/motor-atribuicao. UI, observabilidade, web C6 → base
  `main`. Na dúvida, perguntar; não escolher pela conveniência.
- Trabalhar sempre numa branch própria nuvem/<AAAA-MM-DD>-<tema> criada da base.
- Nunca: commit direto na base, merge, force-push, rebase de branch publicada, fechar issue,
  integrar o PR #9, `git add -A`.

## 4. Arquitetura em uma tela

Detalhe em [architecture.md](architecture.md). Resumo:

- Desktop Python 3.11/Tkinter. Entrada pela UI (`app.py` → `src/ui/app.py`) ou por `scripts/`.
- `src/builder/engine.py` é fachada: `RepoBuilder` delega a src/builder/ops/*. Lógica nova vai no
  subpacote certo; um hook bloqueia `def` novo de nível superior em `src/builder/engine.py`.
- Pipeline: entrada (Moodle/M365, SARC, plano de ensino, stash, URL) → extração (PyMuPDF base;
  Datalab, Marker, Docling avançados) → pós-build → motor de atribuição → artefatos → repositório-
  tutor Markdown ([repo-output.md](repo-output.md)).
- Motor: taxonomia do plano; cronograma e bloco → unidade por DP posicional;
  `apply_concept_resolver` grava `computed_*`; a camada D9 grava só `temporal_*`, por flag. Leitura
  do bloco efetivo: `temporal_block_id` > pino manual > `computed_*`.

## 5. Vocabulário do motor

- **Bloco**: sessão do cronograma. `bloco-NN` é posicional; a referência durável é `block_uuid`.
- **Unidade / subunidade**: vêm do plano de ensino. A subunidade **primária** é o eixo medido; a
  aceita é auxiliar.
- **D9**: motor de âncora temporal (`use_anchor_engine` → `temporal_block_id`). Ligar o D9 não liga
  votador, vocabulário nem LLM.
- **Regime cru**: 0 LLM, 0 rede, 0 embedding, roda em máquina fraca. Embedding conta como LLM.
- **Gold / régua**: tests/fixtures/eval/gold_units_*.csv, docs/reports/*_gt_*.csv,
  ground_truth_*.csv. Só avaliam; nunca viram insumo, nem por curso, arquivo ou ID. A régua
  vigente é a v2 de 22/09 e fica congelada durante medições.
- **`feature_flags`** (padrões em `src/builder/ops/assignment_run.py`): só `use_concept_resolver` ligado.
  Flag desligada deve dar saída byte-idêntica. `manifest["assignment_run"]` registra o pedido e o
  executado de cada camada.
- **Meta**: acima de 90% em cada eixo (bloco, unidade, subunidade primária), por curso e no total.
  Âncora de 23/09, não baseline: bloco 223/237, unidade 248/284, subunidade primária 86/251.

## 6. Regras de trabalho

- **Gate 1**: plano aprovado antes de implementar. Na nuvem, o pedido que abre a sessão só é Gate 1
  se trouxer escopo e aceite explícitos; senão, entregar plano ou diagnóstico.
- **Gate 2**: diff aprovado antes de integrar. Na nuvem o usuário não está presente: commitar só
  na branch nuvem/*, abrir PR em **rascunho**, e o Gate 2 passa a ser a revisão do PR. Nada sai da
  branch própria sem ele.
- **Issue antes de editar**: toda mudança de código, doc ou CI parte de uma issue existente (buscar
  duplicata). Criar issue nova só se o pedido autorizar.
- **PR**: template `.github/pull_request_template.md`; `Closes #N` só para entrega completa,
  `Refs #N` para parcial. Na `main`, o check `core` é obrigatório, a branch precisa estar
  atualizada e as conversas resolvidas.
- **Testes**: rodar a suíte e corrigir falhas causadas pela mudança, sem pedir licença a cada passo
  (`AGENTS.md`). Separar falha preexistente de falha nova, comparando com a base. Como instalar e
  rodar no Linux: [setup.md](setup.md).
- **Commits**: pequenos, só dos arquivos da tarefa (`git add <arquivos>`), mensagem no padrão do
  histórico.
- **Tracker**: não editar `docs/reports/pendencias.md` na nuvem, porque o arquivo costuma ter
  alterações locais sem commit e conflitaria. Propor o delta no handoff (§9).
- **Segredos**: nenhum no código, no git, em argumento de shell, no handoff ou no PR.

## 7. Invariantes que quebram fácil

1. `src/builder/engine.py` é fachada (hook `scripts/hooks/engine-facade-guard.js`).
2. Gemini só com `google-genai` e import lazy; nunca o SDK legado nem `GenerativeModel` (hook
   `scripts/hooks/gemini-antipattern-guard.js` e pre-commit).
3. Escrita de manifest, índices e caches sempre atômica (`src/utils/helpers.py`: `write_text`,
   `write_json_manifest`).
4. Fixtures copiam o contrato real com proveniência ([conventions.md](conventions.md),
   [institutional.md](institutional.md)). Tudo em disco é UTF-8.
5. Motor: flag desligada é byte-idêntica; D9 escreve só `temporal_*`; o pino manual vence; camada
   opcional nunca derruba a regeneração; sem rede síncrona no caminho padrão.
6. Refatoração do motor exige zero-diff nos 8 tutores (`docs/reports/_harness-2026-09-04/c1-3/zero_diff.py`).
   Na nuvem isso é impossível, logo refatoração do motor não roda aqui.
7. Não mover dados de docs/reports/_harness-*: testes os leem, alguns já na coleta.
8. Arquivos acima de 100 KB (ex.: `src/ui/dialogs.py`, `src/builder/engine.py`, o tracker): ler só
   o trecho necessário.
9. Mudou arquitetura, pipeline ou atribuição: atualizar `docs/Overview-Sistema.html` e
   [architecture.md](architecture.md).

## 8. O que a nuvem pode e não pode fazer

**Pode**, dentro de issue e com Gate 1 no pedido:

- correção de defeito com teste vermelho primeiro, fora das regras de atribuição;
- teste novo para comportamento existente;
- refatoração com comportamento preservado fora do motor, com a suíte verde antes e depois;
- documentação e contexto MEX, sem duplicar estado;
- lint sem aumentar a contagem da base do Ruff;
- diagnóstico e plano escritos.

**Não pode**:

- medir ou mudar regra de atribuição, réguas, gold, defaults ou `feature_flags`;
- replay, zero-diff, rebuild de tutores ou qualquer coisa que dependa dos repositórios-tutor;
- LLM ou rede dentro do produto; dependência nova sem Gate 1;
- editar `.claude/settings.json`, hooks, `.codex/config.toml`, `.workflow/` ou `AGENTS.md` sem
  pedido explícito;
- reabrir decisão da §10;
- lançar campanha bloqueada, inclusive o agente noturno (#42).

## 9. Encerrar a sessão

1. Escrever docs/reports/AAAA-MM-DD-handoff-nuvem-<tema>.md com: pedido, issue, base e SHA,
   branch, arquivos mudados, testes (comando e resultado, separando falhas preexistentes), o que não
   foi validado, delta proposto ao tracker, decisões que ficam para o usuário.
2. Commitar só os arquivos da tarefa e o handoff; conferir `git log origin/<base>..HEAD`.
3. Push da branch nuvem/* e PR em rascunho para a base, com o template preenchido. Sem merge.

## 10. Frentes e decisões fechadas

Estado vivo e prioridades ficam no tracker. Em 21/09 o usuário aprovou a ordem: diagnóstico do
agente noturno (#42) → motor/CRU → preparação web → migração. A GUI Tkinter só sai com contrato,
paridade web e Gate 1 próprios.

Não reabrir sem o usuário:

- LLM e API são opcionais; nada se sustenta no gold; o motor é modular por professor.
- Rotulação pelo professor não volta como requisito; conhecimento externo só como regime separado.
- Famílias fechadas: precedência bloco × texto (R1–R4), pai × filho, H2, S/G/G+S, singular × plural.
- Régua v2 vigente; casos do CG ficam em u05; não decidir régua por oráculo; não mudar régua durante
  medição.
- SARC e Moodle valem mais que o gold; bloco de prova hospeda entrega; aula de dúvidas antes de
  prova é review e herda o escopo.
- Um só motor, com a camada LLM ligada ou desligada; consolidar antes de criar alavanca nova; FAIL de
  gate é rollback, não reajuste.
- Web: o motor fica intocado; a web consome transporte versionado; RAG adiado com gatilho.
- Campanha só fecha com 100% dos itens.

Fontes: [decisions.md](decisions.md), tracker, handoffs do motor em `docs/reports/`.

## 11. Ideias e roadmap

`ROADMAP.md` organiza por horizonte: **Agora** (motor acima de 90% por eixo; agente noturno);
**Próximo** (campanha web C6 "AlexandrIA": painel local só de leitura, depois curadoria na web);
**Depois** (bridge para CLI autenticada, bake-off de extração de PDF, modos novos);
**Estacionados** com gatilho e **Descartados**. A caixa de ideias viva fica no tracker. Ideia nova
entra como proposta; rótulo não inicia trabalho.

## 12. Lacunas conhecidas (24/09; não corrigir sem issue)

- `pydantic` é importado no topo de 5 módulos (`src/builder/engine.py` puxa um deles) e não está declarado no
  `pyproject.toml` do motor; instalação limpa precisa dele à parte (45 erros de coleta sem ele).
- code_curation.json é gravado com `path.write_text` direto em `src/builder/core/code_summarization.py`,
  sem escrita atômica, contrariando o `AGENTS.md`.
- `docs/Overview-Sistema.html` está parcialmente defasado (resumo de código ainda aparece como
  Gemini; é determinístico desde 11/09).
- `tests/test_caracterizacao_blocos_atual.py` gera o baseline em `tests/_golden/` na primeira
  execução com tutores presentes; na nuvem não commitar baseline gerado ali.
- Suíte no Linux (piloto de 24/09): um teste derruba o pytest (`os.name` global em
  `tests/test_core.py`), 21 dependem de caminho Windows, `robocopy` ou barra invertida, e o mock de
  `tkinter` vaza entre módulos. Base conhecida e comandos em [setup.md](setup.md).
