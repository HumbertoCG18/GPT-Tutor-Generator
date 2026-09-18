# Auditoria visual de skills e workflows — atualizada em 18/09/2026

Issue: [#15](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/15). Abrir o [painel interativo offline](2026-09-17-auditoria-skills-workflows.html) ou os [dados estruturados](2026-09-17-auditoria-skills-workflows.json).

## Resultado

O workflow já cobre seleção, contexto, implementação, revisão e entrega. A atualização pós-#27 reduziu o catálogo Codex de 77/26 para 73/24 e eliminou as duas duplicatas habilitadas. Não há gap que justifique instalar outra suíte agora.

`find-skills` foi adicionada à auditoria como capacidade instalada e desabilitada. Serve somente para busca após gap comprovado; cada candidato continua sujeito a origem/licença fixadas, auditoria, piloto isolado, issue e Gates 1/2.

O Context Mode ficou dividido: MCP aprovado no sandbox (#18), hooks rejeitados após 7/10 checks (#19) e medição real ainda aberta na #22.

## Medido

| Escopo | Entradas | Estado |
|---|---:|---|
| Claude | 340 | arquivos/configuração selecionados; catálogo novo não aferido |
| Codex | 73 | app-server novo; 24 habilitadas, 49 desabilitadas, 24 nomes únicos |
| AGY | 33 | arquivos/configuração; aplicação por skill não observável |
| Fonte ECC | 286 | reserva disponível; não implica ativação |

`verify.py`: ok=true, 75 arquivos gerenciados, errors=[]. Issue #27/PR #28: GitHub MCP removido, Perssua removido/desabilitado, quatro cópias redundantes removidas e Graphify CLI preservado.

## Camadas

| Camada | Baseline | Gap principal |
|---|---|---|
| 01 · Governança e seleção | ponytail · troglodita · verify.py · descoberta sob demanda | Medir descoberta e aplicação em sessão nova no Claude e AGY. |
| 02 · Contexto e navegação | MEX · Graphify/CLI · CBM fallback · contrato de leitura | Executar #22 antes de registrar o MCP; saída bruta e tokens por tarefa. |
| 03 · Memória e continuidade | tracker · handoff · claude-mem · estado local | Distinguir memória do produto, memória do agente e continuidade do job. |
| 04 · Pesquisa e ingestão | AGY inline · Context7 · padrões PDF | Benchmark de conversão; evitar cookies e serviços externos sem necessidade. |
| 05 · Planejamento e delegação | ECC orch-* · Fable executor · Astra read-only | Supervisor externo, timeout real, teto de tentativas e sessão nova. |
| 06 · Implementação | ECC tdd-guide inline · Python · stdlib primeiro | Selecionar skill de stack por tarefa; não carregar todas as linguagens. |
| 07 · Qualidade e revisão | pytest · Ruff no contrato · revisão delimitada | Checks amplos e baseline de cobertura ainda são tarefas #13/#14. |
| 08 · Segurança e limites | permissões nativas · contratos · corpus protegido | Negação técnica, isolamento de credenciais e logs sem segredos para o loop. |
| 09 · Design e acessibilidade | ECC motion/taste na fonte · contrato #11 | Escolher um guia visual; medir estados assíncronos e redução de movimento. |
| 10 · Browser e jornadas | E2E no contrato · ferramentas de browser da sessão | Fixtures e teste reproduzível; comparar Playwright CLI com MCP. |
| 11 · Entrega e observabilidade | issue → PR → release · templates · #10/#12 | CI geral, proteção de branch, release e telemetria ainda não impostos. |

## Candidatos — decisão individual

| Candidato | Natureza | Decisão | Fonte |
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
| context mode | MCP + armazenamento + hooks | MCP aprovado; hooks rejeitados | [mksglu/context-mode](https://github.com/mksglu/context-mode/blob/c127f2fe8496fefc36e0ebef36ded92d4fa8f570/README.md) |
| claude-video | Skill + scripts de vídeo | Adiar por escopo | [bradautomates/claude-video](https://github.com/bradautomates/claude-video/blob/83da59fa78c3eee9e20f515fe75c438bb5166efd/README.md) |
| manifest | Gateway de modelos | Adiar por conflito | [mnfst/manifest](https://github.com/mnfst/llm-gateway/blob/b8022df157a7b3bca8d8e86b78631fb718415a82/README.md) |
| skill-bus | Hooks de composição de skills | Referência seletiva | [joeymnguyen/skill-bus](https://github.com/joeymnguyen/skill-bus/blob/77fd804aa4fa1d4d7081725d41da511cfcd3de1f/README.md) |
| design-principals | Skill de motion e auditoria | Já referenciada | [kylezantos/design-motion-principles](https://github.com/kylezantos/design-motion-principles/blob/4a9ca879f24a361f4dca4174fe2da0f67b5ddee3/README.md) |
| Strix | Agentes de pentest | Adiar por escopo | [usestrix/strix](https://github.com/usestrix/strix/blob/4c1f00d1ee5bac0880e66e325ba50ed18a0b182b/README.md) |
| Graft | Grafo de código/contexto + CLI/MCP/hooks | Benchmark pontual | [trailhq/Graft](https://github.com/trailhq/Graft/blob/33d805905b01761e2bc83c043610689386f31927/README.md) |
| Archify | JSON tipado → diagramas HTML/SVG | Piloto condicionado | [tt-a1i/archify](https://github.com/tt-a1i/archify/blob/72c750bb070d95171dbb2244e5b62b1b7da69c12/README.md) |
| agent-pd | Hook de log + detectores | Piloto condicionado | [varmabudharaju/agent-pd](https://github.com/varmabudharaju/agent-pd/blob/9f68a6b5067123bef87877d2ad09c035d83cd978/README.md) |
| find-skills | Skill + CLI de descoberta | Governada; desabilitada por padrão | [vercel-labs/skills](https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/skills/find-skills/SKILL.md) |

## Workflow

| Etapa | Dono | Estado e lacuna |
|---|---|---|
| 01 · Entrada | MEX / coordenador | Documentado — Codex teve sessão nova sem warning após a deduplicação; Claude e AGY ainda precisam do mesmo smoke de catálogo. |
| 02 · Escopo | issue + ponytail + ECC | Documentado — Issue não aprova código. Os gates são instruções, não uma barreira técnica universal. |
| 03 · Contexto | Graphify / MEX / AGY | Contrato + pilotos isolados — Graphify CLI passou; Context Mode MCP ainda não tem evidência em tarefa real. Hooks foram rejeitados. |
| 04 · Implementação | Fable + tdd-guide | Contrato definido — Subagentes nativos variam por CLI. Contratos inline preservam o papel, não criam ferramenta. |
| 05 · Verificação | executor / CI | Parcial no CI — O único YAML encontrado em .github/workflows não cobre a suite/lint/E2E geral. Branch protection não auditada. |
| 06 · Revisão | Astra read-only | Política observada — Astra revisou #27 uma vez e o diff foi corrigido; timeout/contagem continuam responsabilidade do chamador. |
| 07 · Entrega | humano + GitHub | Prática validada; enforcement parcial — Issues #24/#23/#27 passaram por branch e PR; branch protection e pipeline geral não foram verificados. |
| 08 · Continuidade | coordenador / futuro loop | Loop ainda planejado — Não há daemon/supervisor nesta política. Compact não é checkpoint nem contenção. |

## Fila atual

| Prioridade | Item | Estado | Próximo passo |
|---|---|---|---|
| P0 | Controlador do loop noturno | Sem implementação | Issue própria no agent-workflow-lab + fixture de ação proibida. |
| P1 | Context Mode MCP | #22 aberta | 12 tarefas reais; hooks continuam rejeitados. |
| P1 | Qualidade/CI/observabilidade | #10/#12/#13/#14 abertas | Baselines antes de adicionar ferramentas. |
| P2 | UI e motion | #11 aberta | Auditar jornadas reais; web somente quando C6 existir. |
| Sob demanda | Novas skills/MCPs | Sem gap novo | Usar find-skills só após gap comprovado; não instalar agora. |

## O que adicionar agora

Nenhuma nova skill ou MCP. Os gaps restantes são: contenção do loop, experimento real do Context Mode, CI/qualidade/observabilidade e auditoria de jornadas da UI. Adicionar catálogo antes dessas medições recriaria o problema de orçamento e sobreposição.

## Método e limites

Inventário local refeito em 18/09; app-server Codex consultado com `forceReload`. Upstreams mantidos nos SHAs do relatório original; `find-skills`: origem e hash da pasta instalados conferidos no lockfile; o commit Git exato da instalação não está registrado. O HEAD upstream `7407f3` foi consultado apenas como referência atual. Classificação por camada usa heurística de nome.

O relatório de uso da issue #23 mede chamadas estruturadas; o invólucro Codex não expõe todas as chamadas filhas e o AGY não expõe ativação uniforme de skills. Ausência de telemetria não prova desuso. Bytes não equivalem a tokens.

## Verificação do artefato

Passou: JSON externo = JSON embutido; 29 candidatos; 732 entradas; Codex 73/24 com 24 nomes únicos; HTML offline; IDs únicos; JavaScript válido; filtros `find-skills` (1/29) e Codex habilitadas (24/24) conferidos no Chrome. Layout desktop inspecionado. O breakpoint móvel foi validado estaticamente no CSS, sem emulação de viewport nesta sessão.
