# Auditoria visual de skills e workflows — snapshot 17/09, atualização 19/09/2026

Origem: [#15](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/15). Atualização: [#35](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/35). Abrir o [painel interativo offline](2026-09-17-auditoria-skills-workflows.html) ou os [dados estruturados](2026-09-17-auditoria-skills-workflows.json).

## Resultado

O núcleo do workflow já tem cobertura documental ampla. #16/#22/#33 e a prova de retomada estão fechadas; falta entregar a reconciliação no PR #36. O loop noturno mantém severidade P0, mas é a última entrega por decisão de sequência. Instalar outra suite inteira não demonstra resolver esses gaps.

**Atualização — issue #16:** Karpathy Skills foi adotado parcialmente como regras nas instruções compartilhadas, sem instalar plugin. Quatro deltas: premissas materiais, estilo local, órfãos da própria mudança e verificação por etapa. Adição de 16 linhas/1027 bytes; fonte e três cópias idênticas, verify.py aprovado com 75 arquivos e zero divergências. Comportamento/consumo ainda não medidos. A issue foi fechada com a limitação de o laboratório não ter remote. O inventário permanece o snapshot de 17/09; esta atualização não é nova varredura do catálogo.

**Atualização — issue #17:** três referências do Agent Skills foram adaptadas em um pattern local: piso de qualidade com baseline/ratchet, checkpoint de contexto e observabilidade orientada a perguntas. O bloco de qualidade agora é imposto pelo gate Python `core` da #13; nenhum plugin/hook upstream foi instalado. Fable/Astra, MEX/Graphify e Gates 1/2 permanecem.

**Atualização — issues #18/#19/#22:** o MCP isolado passou 10/10, mas os hooks foram rejeitados (7/10; persistência de segredo sintético e stderr). Em 12 execuções reais, 10/12 respostas foram corretas e 9/12 conformes ao schema. Em 19/09, a decisão foi não adotar: registros e dados ativos foram removidos das três CLIs, com backup recuperável.

1. **Context Mode:** não adotado; removido das três CLIs. Codex falhou nas duas tarefas ON; AGY ficou mais lento/verboso; zero uso interativo foi medido no Claude. Não generalizar economia de contexto.
2. **Agent-pd:** candidato a observabilidade do agente, condicionado à privacidade dos logs. Não bloqueia ações; armazena inputs completos e pode guardar segredos em texto puro.
3. **UI:** reutilizar as fontes ECC e design-motion-principles já referenciada. Comparar Impeccable com um único guia atual quando houver uma tela web da C6.
4. **MarkItDown:** benchmark de conversão com fixtures, já relacionado à caixa de ideias. Sem substituir o pipeline atual antes de medir fidelidade.
5. **Suites e nomes ambíguos:** GStack/agências são referências seletivas; Graft (trailhq), Archify (tt-a1i) e Agent Skills (addyosmani) tiveram URLs confirmadas pelo usuário; Manifest e outros homônimos ainda exigem confirmação.

## Medido

| Escopo | Entradas | O que isso prova |
|---|---:|---|
| Claude | 340 | Arquivos em skills pessoais/plugins selecionados e política local |
| Codex | 77 | skills/list novo, por duas rotas de app-server |
| Codex habilitadas | 26 | 24 nomes únicos; não prova aplicação |
| AGY | 33 | Arquivos e configuração, sem inventário efetivo de sessão nova |
| Fonte ECC | 286 | Reserva disponível no marketplace; não significa ativação |

`verify.py`: ok=true, 75 arquivos gerenciados, errors=[]. Claude: 266 user-invocable-only; 21 off; 16 em plugins desabilitados; 37 sem override explícito. AGY: 27 entradas em plugins habilitados e 6 pessoais. Duplicatas habilitadas Codex: heredoc-git-bash-windows e mex-check-falso-positivo. Nenhuma removida.

A sessão anuncia caminhos de skill-stocktake e agent-architecture-audit ausentes no cache Codex. Os critérios dessas skills foram lidos na fonte Claude do marketplace. Isso evidencia divergência entre a lista desta sessão e os arquivos presentes; o catálogo novo não reescreve o contexto já carregado.

## Camadas

| Camada | Baseline existente | Gap principal |
|---|---|---|
| 01 · Governança e seleção | ponytail · troglodita · verify.py · overrides | Validar sessão nova por CLI; evitar dois gestores de skills. |
| 02 · Contexto e navegação | MEX · Graphify · CBM fallback · contrato de leitura | Recuperar saída bruta sob demanda e medir contexto por tarefa. |
| 03 · Memória e continuidade | tracker · handoff · claude-mem · estado local | Distinguir memória do produto, memória do agente e continuidade do job. |
| 04 · Pesquisa e ingestão | AGY inline · Context7 · padrões PDF | Benchmark de conversão; evitar cookies e serviços externos sem necessidade. |
| 05 · Planejamento e delegação | ECC orch-* · Fable executor · Astra read-only | Supervisor externo, timeout real, teto de tentativas e sessão nova. |
| 06 · Implementação | ECC tdd-guide inline · Python · stdlib primeiro | Selecionar skill de stack por tarefa; não carregar todas as linguagens. |
| 07 · Qualidade e revisão | pytest · Ruff · arquitetura · cobertura · revisão delimitada | Web #14 aguarda stack C6; E2E desktop continua sem matriz completa. |
| 08 · Segurança e limites | permissões nativas · contratos · corpus protegido | Negação técnica, isolamento de credenciais e logs sem segredos para o loop. |
| 09 · Design e acessibilidade | ECC motion/taste na fonte · contrato #11 | Escolher um guia visual; medir estados assíncronos e redução de movimento. |
| 10 · Browser e jornadas | E2E no contrato · ferramentas de browser da sessão | Fixtures e teste reproduzível; comparar Playwright CLI com MCP. |
| 11 · Entrega e observabilidade | issue → PR → release · templates · #10/#12 | Release/deploy e telemetria de produto continuam sem implementação comprovada. |

As 736 entradas são classificadas por camada predominante usando o nome da skill. É uma heurística para navegação, não avaliação semântica integral de cada arquivo. O painel permite buscar a descrição e inspecionar caminho, origem, configuração e evidência de runtime.

## Candidatos — decisão individual

| Candidato | Natureza | Decisão | Fonte fixada |
|---|---|---|---|
| Agent Skills | Coleção de engenharia | Adotado parcialmente | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/blob/a120596f6d7ff9b967a3f5e0331ea911376ee5ef/README.md) |
| Karpathy Skills | Regras incorporadas ao contrato | Adotado parcialmente | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/skills/karpathy-guidelines/SKILL.md) |
| GStack | Suite de workflow e ferramentas | Referência seletiva | [garrytan/gstack](https://github.com/garrytan/gstack/blob/a6b3a57512ca6d5c6aa5b68f74f736195021f96e/README.md) |
| ui-ux-pro-max | Skill + dados e scripts | Comparar na C6 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/15de38fb70bc80ae9276fa7703b48ae861a672e6/README.md) |
| taste-skill | Coleção de direção visual | Reutilizar o atual | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/blob/e79ca9ec7e071eb3a3b623c4fb752e853fc3ed58/README.md) |
| impeccable | Skill, comandos e detectores | Piloto condicionado | [pbakaus/impeccable](https://github.com/pbakaus/impeccable/blob/f2c7051853848826aac2f4646581d62a732155ad/README.md) |
| playwright-mcp | Servidor MCP | Comparar na C6 | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp/blob/ea43eee0d95196ab31f7619b26f78d7b9c664286/README.md) |
| anthropic-skills | Coleção oficial de skills | Referência seletiva | [anthropics/skills](https://github.com/anthropics/skills/blob/34040c9c568585f6929bedeaad110ad08f079624/README.md) |
| markitdown | Biblioteca Python / CLI | Benchmark pontual | [microsoft/markitdown](https://github.com/microsoft/markitdown/blob/945314a45ddbe02935f2fd287b797dc0ba4a01e4/README.md) |
| frontend-slides | Skill de apresentações HTML | Reutilizar o atual | [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides/blob/9906a34d640d2111f724544cbc50f7f130569ae1/README.md) |
| claude-seo | Suite SEO + agentes | Adiar por escopo | [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo/blob/92795530b4cc92c6bf7a2435b82c15b003e71181/README.md) |
| apify | Skills e plataforma / MCP separado | Adiar por escopo | [apify/agent-skills](https://github.com/apify/agent-skills/blob/8449f30c746b8c1741348ef208f678cfef6bf626/README.md) |
| agent-reach | CLI e adaptadores de fontes | Adiar por escopo | [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach/blob/a19a171fa980a0785849596492e0af4db800c82f/README.md) |
| mem0 | Infraestrutura de memória | Adiar por escopo | [mem0ai/mem0](https://github.com/mem0ai/mem0/blob/f135cb994979170401d4e62d37fd043ed01ac5f8/README.md) |
| agency-agents | Catálogo de papéis | Referência seletiva | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents/blob/ad9264e309bd5e5422c04784372d7841b1e5d604/README.md) |
| awesome-claude-skills | Catálogo + componentes de integração | Somente descoberta | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills/blob/be2a406907dbc61b73e6827ded415c96139d13a2/README.md) |
| wshobson agents | Marketplace de agentes e skills | Referência seletiva | [wshobson/agents](https://github.com/wshobson/agents/blob/4236bb91f8395b0435f1d8b8baf9e8e4c69a8620/README.md) |
| prompt-master | Skill de escrita de prompts | Reutilizar o atual | [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master/blob/2bd92518e26bf659e21e3d9ab90573fcf3ddeccb/README.md) |
| security sweep | Skill de revisão de segurança | Reutilizar o atual | [Onome-AJ/security-sweep-plugin](https://github.com/Onome-AJ/security-sweep-plugin/blob/6ca48b6ef582b5c6050e717202b3e35fa575449c/README.md) |
| context mode | MCP + armazenamento + hooks | Não adotado; removido das três CLIs | [mksglu/context-mode](https://github.com/mksglu/context-mode/blob/c127f2fe8496fefc36e0ebef36ded92d4fa8f570/README.md) |
| claude-video | Skill + scripts de vídeo | Adiar por escopo | [bradautomates/claude-video](https://github.com/bradautomates/claude-video/blob/83da59fa78c3eee9e20f515fe75c438bb5166efd/README.md) |
| manifest | Gateway de modelos | Adiar por conflito | [mnfst/manifest](https://github.com/mnfst/llm-gateway/blob/b8022df157a7b3bca8d8e86b78631fb718415a82/README.md) |
| skill-bus | Hooks de composição de skills | Referência seletiva | [joeymnguyen/skill-bus](https://github.com/joeymnguyen/skill-bus/blob/77fd804aa4fa1d4d7081725d41da511cfcd3de1f/README.md) |
| design-principals | Skill de motion e auditoria | Já referenciada | [kylezantos/design-motion-principles](https://github.com/kylezantos/design-motion-principles/blob/4a9ca879f24a361f4dca4174fe2da0f67b5ddee3/README.md) |
| Strix | Agentes de pentest | Adiar por escopo | [usestrix/strix](https://github.com/usestrix/strix/blob/4c1f00d1ee5bac0880e66e325ba50ed18a0b182b/README.md) |
| Graft | Grafo de código/contexto + CLI/MCP/hooks | Benchmark pontual | [trailhq/Graft](https://github.com/trailhq/Graft/blob/33d805905b01761e2bc83c043610689386f31927/README.md) |
| Archify | JSON tipado → diagramas HTML/SVG | Piloto condicionado | [tt-a1i/archify](https://github.com/tt-a1i/archify/blob/72c750bb070d95171dbb2244e5b62b1b7da69c12/README.md) |
| agent-pd | Hook de log + detectores | Piloto condicionado | [varmabudharaju/agent-pd](https://github.com/varmabudharaju/agent-pd/blob/9f68a6b5067123bef87877d2ad09c035d83cd978/README.md) |

Cada ficha no HTML/JSON inclui função, sobreposição, risco, custo qualitativo, compatibilidade, licença, critério de piloto e confiança na identidade. Nomes sem URL foram associados a correspondências prováveis, sem presumir confirmação do usuário.

## Workflows

| Etapa | Dono | Estado observado |
|---|---|---|
| 01 · Entrada | MEX / coordenador | Documentado — Bootstrap não deve recarregar todo o histórico. Sessão antiga pode reter catálogo anterior. |
| 02 · Escopo | issue + ponytail + ECC | Documentado — Issue não aprova código. Os gates são instruções, não uma barreira técnica universal. |
| 03 · Contexto | Graphify / MEX / AGY | Contrato definido — Catálogo instalado não prova que a skill foi lida/aplicada; saída truncada ainda pode perder evidência. |
| 04 · Implementação | Fable + tdd-guide | Contrato definido — Subagentes nativos variam por CLI. Contratos inline preservam o papel, não criam ferramenta. |
| 05 · Verificação | executor / CI | Gate Python imposto — Tkinter não tem matriz E2E completa; gates web permanecem bloqueados até existir stack C6. |
| 06 · Revisão | Astra read-only | Política; não supervisor — O próprio contrato declara não impor quota/contagem/timeout por servidor. Revisão nativa adicional pode duplicar custo se roteada sem critério. |
| 07 · Entrega | humano + GitHub | Contrato entregue — Templates e branch protection existem; release/deploy ainda dependem do alvo e de autorização própria. |
| 08 · Continuidade | coordenador / futuro loop | Última entrega planejada — Não há daemon/supervisor nesta política. Compact não é checkpoint nem contenção. O loop só avança após o fechamento dos gaps anteriores. |

Além de validate-timeline.yml, a #13 adicionou o workflow Python `core`: suíte pytest, cobertura por plataforma, Ruff e contrato arquitetural. A proteção da `main` exige `core` atualizado e conversas resolvidas; PRs #31/#32 passaram e foram mesclados. O plano noturno está em .workflow/PENDING.md, sem implementação afirmada aqui. O contrato explicita ausência de daemon e de limite técnico global de quota/contagem.

## Fontes que mudam a decisão

- [Playwright MCP](https://github.com/microsoft/playwright-mcp/blob/ea43eee0d95196ab31f7619b26f78d7b9c664286/README.md): o README recomenda considerar CLI + skills para coding agents.
- [Context Mode](https://github.com/mksglu/context-mode/blob/c127f2fe8496fefc36e0ebef36ded92d4fa8f570/README.md): MCP isolado aprovado na #18; hooks rejeitados na #19; medição real e decisão por CLI na #22/PR #32. [Licença ELv2](https://github.com/mksglu/context-mode/blob/c127f2fe8496fefc36e0ebef36ded92d4fa8f570/LICENSE).
- [Agent-pd SECURITY.md](https://github.com/varmabudharaju/agent-pd/blob/9f68a6b5067123bef87877d2ad09c035d83cd978/SECURITY.md): logging-only, inputs completos, plaintext, sem bloqueio.
- [Skill Bus](https://github.com/joeymnguyen/skill-bus/blob/77fd804aa4fa1d4d7081725d41da511cfcd3de1f/README.md): composição por hooks; conclusão é sinal sintético e o encadeamento é experimental.
- [Graft confirmado: trailhq/Graft](https://github.com/trailhq/Graft/blob/33d805905b01761e2bc83c043610689386f31927/README.md): avaliar navegação e contexto contra o baseline atual. [Telemetria](https://github.com/trailhq/Graft/blob/33d805905b01761e2bc83c043610689386f31927/TELEMETRY.md) inclui background/postinstall; condicionar o piloto à desativação prévia.
- [Archify confirmado: tt-a1i/archify](https://github.com/tt-a1i/archify/blob/72c750bb070d95171dbb2244e5b62b1b7da69c12/README.md): candidato a piloto visual; a validação é sobre fatos fornecidos, não prova de cobertura do código.
- [Agent Skills confirmado: addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/blob/a120596f6d7ff9b967a3f5e0331ea911376ee5ef/README.md): três deltas adotados na #17; o bloco de qualidade usa o gate próprio da #13.

## Método e limites

Leitura local de políticas, metadados de skills, configuração selecionada e catálogo Codex. Upstreams: README fixado por SHA, metadados GitHub, árvore de arquivos e trechos de entrypoints/manifests/licenças dirigidos aos riscos relevantes. Contagens upstream de SKILL.md incluem cópias/fixtures; não são contagens de skills únicas. Não se auditou todo o código executável nem cada dependência transitiva.

Sem LLMs auxiliares/subagentes; o próprio assistente fez a análise. Sem instalação ou mudança de seleção de skills; as instruções pessoais receberam o delta documentado na #16, o projeto recebeu o pattern da #17 e o Context Mode foi medido nas #18/#19/#22. Houve 12 sessões novas no experimento #22; isso não equivale a benchmark geral de quota. Sem reinício de worker, pentest ou deploy. Custos/ganhos dos demais candidatos continuam qualitativos; tamanhos de arquivo não equivalem a tokens.

Coleta reproduzível e evidência bruta local: `agent-workflow-lab/private/skills-audit-20260917/` (collect_sources.py, inventory.py, build_report.py, sources/, upstreams.json). Dados públicos do relatório não incluem valores de credenciais nem conteúdo de configurações completas.

## Verificação do artefato

node --check e o validador estático passaram: JSON embutido idêntico à fonte, IDs únicos, zero recurso remoto automático, 28 candidatos, 736 entradas, 11 camadas e oito etapas. Assertions confirmam o gate Python, os PRs #31/#32 e a decisão Context Mode. A inspeção visual via HTTP local confirmou as cinco abas, as contagens principais e o layout desktop sem quebra visível. Viewport móvel, impressão e download permanecem sem teste nesta atualização.
