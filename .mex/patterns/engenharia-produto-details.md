# Contrato de engenharia: desktop atual e campanha C6 web

Padrão para qualquer agente/modelo/CLI. Fluxo GitHub na seção "Issues, PRs e releases"
de `.workflow/workflow.md`, cuja fonte é `agent-workflow-lab/workflow.md`.
Este arquivo define requisitos; não afirma que já foram implementados.

## Fluxo de entrega

Criar/reutilizar issue antes de alterar o projeto; branch por escopo e PR relacionado.
Preencher `.github/ISSUE_TEMPLATE/task.md` e `.github/pull_request_template.md`.
Manter URL no estado local/handoff e tracker. Não duplicar o backlog inteiro em issues
sem triagem: criar cada tarefa ao aceitar seu escopo. As frentes solicitadas em 17/09
estão nas issues #10–#14. Gates 1/2 permanecem; sem commit, merge ou deploy implícitos.

O produto atual é Python/Tkinter. C6, no tracker, prevê web local: primeiro painel
de leitura, depois curadoria; preservar o motor e seus contratos. Next.js aparece
na ideia de distribuição, mas versões, framework final e infraestrutura exigem Gate 1.
Não antecipar a migração nem instalar ferramentas web no runtime Python.

## UI: todos os estados, movimento com propósito

Usar [design-motion-principles](https://github.com/kylezantos/design-motion-principles/tree/4a9ca879f24a361f4dca4174fe2da0f67b5ddee3/skills/design-motion-principles)
de Kyle Zantos, revisão fixada `4a9ca879f24a361f4dca4174fe2da0f67b5ddee3`.
Carregar SKILL.md e somente workflow/referências exigidos pela tarefa, sob demanda;
não importar o repositório inteiro para o catálogo automático de skills.
Para o painel de produtividade: priorizar contenção/velocidade e acabamento discreto.
Telas de estudo podem ter critérios próprios, definidos antes de gerar componentes.

- Cada jornada assíncrona cobre idle, loading, empty, success e error; operações
  longas mostram etapa, progresso e cancelamento quando suportado. Não inventar
  percentuais: denominador conhecido = progresso medido; desconhecido = indeterminado.
- Skeleton onde há conteúdo remoto/assíncrono com estrutura previsível; não aplicar
  artificialmente a elementos instantâneos. Reservar espaço para evitar saltos.
- Lazy loading para recursos pesados não críticos. Conteúdo inicial essencial e
  controles necessários ao usuário não devem depender de carregamento tardio.
- Entrada/saída suaves quando comunicam mudança. Interações frequentes/teclado
  não devem ganhar atrasos. Sem exigir animação em todos os widgets.
- Web: `prefers-reduced-motion`, foco, teclado, nomes acessíveis e feedback de
  estado. Desktop: alternativa equivalente de movimento reduzido; não copiar CSS
  para Tkinter. Ações devem funcionar com animação desligada.
- Evitar bloqueio da UI, submissão duplicada e resultados obsoletos após cancelar.
  Testar sucesso, falha, lentidão, vazio e cancelamento; anexar evidência visual.

## Ferramentas por responsabilidade e stack

| Capacidade | Python/Tkinter atual | Web futura / decisão necessária |
|---|---|---|
| Logs, erros, métricas e traces | Inventariar logging; IDs de operação, duração e status; avaliar SDK Python | OpenTelemetry para instrumentação; backend escolhido por necessidade |
| Monitoramento | Avaliar Sentry, Datadog ou New Relic com orçamento e coleta definidos | Não contratar os três por padrão; evitar telemetria duplicada |
| Lint e formato | Ruff já declarado; ampliar regras com baseline | Biome para linguagens suportadas, se compatível com a stack |
| Fronteiras arquiteturais | Contratos/testes Python compatíveis com módulos existentes | ArchContract é candidato para TypeScript |
| Código/dependências sem uso | Auditoria de consumidores e ferramenta Python compatível | Knip para JS/TS; sem remoção automática sem confirmar usos dinâmicos |
| Commits | Conventional Commits; validar mensagem/título conforme estratégia de merge | commitlint é candidato; não adicionar Node ao runtime Python só por isso |
| Unitários e integração | pytest + pytest-cov já declarados; dados reais de contrato | Runner da stack escolhida; cobrir integração com o motor |
| E2E | Estratégia de automação Tkinter + smoke das jornadas nativas | Playwright para browser; não controla widgets Tkinter |
| Cobertura | Relatório local primeiro; baseline e metas incrementais | Codecov é serviço de cobertura, não runner; definir upload/configuração |
| Mutação | Avaliar ferramenta Python apenas com necessidade concreta | Stryker em componentes compatíveis; começar por regras críticas |

Interpretação provisória dos nomes do pedido: Datahog → Datadog, comilint → commitlint,
stryke → Stryker. Confirmar antes da adoção se eram outros projetos. Ferramenta
homônima não deve ser instalada por suposição.

## Observabilidade e aceite

Seguir também [Agent Skills: referências adaptadas](agent-skills-adapted.md): definir de duas
a quatro perguntas operacionais antes dos sinais; cada sinal deve responder uma delas.
Instrumentar fronteiras úteis: importação, extração, build, exportação e chamadas
externas. Correlation/run ID, operação, duração, resultado e versão; sem conteúdo
acadêmico bruto, credenciais ou prompts integrais em telemetria. Preservar modo
local/offline; exportação externa exige destino e configuração explícitos.

Aceite inclui erro reproduzível que apareça no destino configurado, correlação de
uma operação e comportamento quando o coletor está indisponível. Definir retenção,
amostragem, orçamento e alertas acionáveis. Instalar SDK não comprova observabilidade.

Antes do merge: checks aplicáveis verdes, regressão da mudança, contratos preservados
e riscos documentados. Cobertura não prova qualidade sozinha; evitar meta arbitrária
de 100%. Baseline precede limite; ratchet bloqueia regressão. Não reduzir a barra no mesmo
diff para obter verde. Para release: artefato/commit identificados, smoke test e rollback executável.
CI deve usar permissões mínimas e dados sintéticos/revisados, sem material privado.

## Fila e fontes

- [#10 — governança](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/10): instruções e templates nesta entrega.
- [#11 — UI](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/11): inventário de jornadas e plano de adequação.
- [#12 — observabilidade](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/12): desenho e escolha de backend.
- [#13 — qualidade Python](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/13): baseline e CI incremental.
- [#14 — qualidade web](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/14): contrato documental em [qualidade C6](../../docs/reports/2026-09-19-contrato-qualidade-c6.md); ativação dos checks na primeira fatia pela [#41](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/41).

Fontes oficiais: [OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/),
[ArchContract](https://github.com/leofmarciano/arch-contract), [Biome](https://biomejs.dev/),
[Knip](https://knip.dev/), [commitlint](https://commitlint.js.org/),
[Stryker](https://stryker-mutator.io/), [Playwright](https://playwright.dev/python/docs/intro),
[Codecov](https://docs.codecov.com/docs/about-code-coverage).
