# Medição das issues abertas de workflow e produto

Data: 2026-09-18. Base medida: `origin/main` em `2ba355f`. Diagnóstico sem alterar o
runtime, instalar dependências, ativar telemetria ou antecipar a campanha C6.

## Resultado por issue

| Issue | Estado medido | Evidência | Gap restante |
|---|---|---|---|
| #10 | Implementação local, ausente da `main` | templates, contrato e ponteiros estavam staged em worktree antiga | versionar por PR e validar links/hashes |
| #11 | Parcial no produto; auditoria ausente | jornadas centrais têm threads, progresso e cancelamento | matriz, cobertura dos fluxos auxiliares e política de movimento reduzido |
| #12 | Parcial | 28 módulos importam logging; 224 chamadas usam `logger` e 2 usam `logging.error` | `run_id`, eventos estruturados, duração, política de dados e backend opcional |
| #14 | Não iniciada por decisão correta | zero artefato web de produto fora de docs/Graphify | ativar gates somente quando a stack C6 existir |
| #16 | Aplicada localmente, sem versionamento remoto | fonte + três destinos iguais; `verify.py` verde | laboratório não tem remote para PR |
| #17 | Implementação local, ausente da `main` | referência curta de três blocos, sem plugin/dependência | versionar e vincular aos contratos atuais |
| #22 | Medição concluída; aceite falhou | 12/12 registros, 10/12 respostas corretas | manter Claude restrito; Codex/AGY removidos; corrigir incompatibilidades antes de repetir |

#11, #12 e #14 são frentes de auditoria/planejamento. Esta entrega registra o baseline e
os gates; não reforma Tkinter nem instala a stack web.

## #11 — jornadas assíncronas do desktop

Medição AST e leitura dirigida: 11 arquivos em `src/ui`, 27 classes, 17 criações de
`Thread`, 59 chamadas `after` e duas `Progressbar`. Os 73 arquivos `test_*.py` contêm
66 imports de `src.ui`, mas não formam uma matriz de idle/loading/empty/success/error,
lentidão e cancelamento por jornada.

| Jornada | Idle/loading | Progresso | Success/error | Cancelamento | Gap |
|---|---|---|---|---|---|
| Build e fila de repositórios | explícito | determinado por item; indeterminado manual quando total desconhecido | ambos | cancelar + pausar/retomar | testar estados e impedir callback tardio após cancelamento |
| Processar/reprocessar item | explícito | indeterminado manual | ambos | cancelar + pausar/retomar | usar modo indeterminado nativo e testar retomada |
| Importar Moodle/M365 | status + barra | determinado quando total existe | ambos | ausente | definir cancelamento cooperativo ou declarar operação não cancelável |
| Buscar/importar HTML e plano PDF | mensagem de execução | ausente | ambos | ausente | feedback persistente e prevenção de submit duplicado |
| Gerar resumos de código | status textual | `idx/total` textual | erro + conclusão | ausente | cancelamento cooperativo e teste de falha parcial |
| Descrever/extrair imagens | status textual | lote sem barra comum | ambos | ausente | progresso por lote, cancelamento e resultado obsoleto |
| Manutenção/sweep | log textual | ausente | ambos | ausente | estado ocupado e bloqueio de execução duplicada |
| Preview de imagens | “Carregando…” reservado | ausente/não aplicável | imagem ou erro | ausente | é o único placeholder equivalente a skeleton; manter lazy load local |

Decisão: Tkinter é transitório. Corrigir defeitos funcionais das jornadas centrais, sem
campanha visual ampla. Para web, exigir skeleton apenas em conteúdo assíncrono previsível,
lazy loading de recurso pesado não crítico, transições funcionais e
`prefers-reduced-motion`. Nenhuma animação deve atrasar teclado ou ação frequente.

## #12 — observabilidade

Baseline em 98 arquivos Python de `src`: 28 módulos importam logging, 224 chamadas usam a
variável `logger`, duas chamam `logging.error` diretamente e há um `print`. `src/__main__.py`
configura texto local; `_UILogHandler` espelha eventos para a
interface. Não há `correlation_id`, `trace_id`, `run_id`, OpenTelemetry, Sentry, Datadog,
New Relic ou spans. Logo existente ajuda diagnóstico local, mas não correlaciona uma operação.

Perguntas operacionais que autorizam sinais:

1. Qual operação falhou, em qual etapa, versão e entrada sanitizada?
2. Quanto durou importação, extração e build; onde ficou o maior tempo?
3. Uma falha externa afetou um item ou encerrou a execução inteira?
4. O resultado terminou em sucesso, sucesso parcial, cancelamento ou erro?

Plano mínimo:

- primeiro, `run_id` UUID por operação e `LoggerAdapter`/`extra` com operação, etapa,
  duração, resultado e versão; armazenamento local e rotação;
- proibir conteúdo acadêmico, prompt, URL completa, email, segredo e texto bruto em campos;
  cardinalidade alta fica no log local, não em label/métrica;
- depois, OpenTelemetry para traces e métricas nas fronteiras do motor quando existir
  consumidor real; em Python, traces e métricas estão estáveis, logs seguem em desenvolvimento;
- backend escolhido: **Sentry**, somente como captura de erro opt-in quando houver conta,
  retenção e consentimento definidos. Datadog/New Relic ficam fora: o produto local não
  justifica três agentes/APMs nem exportação contínua;
- exportação desativada por padrão; coletor indisponível não pode impedir build. Demonstrar
  uma falha sintética local e, antes de ativar Sentry, repetir a prova no projeto configurado.

Fontes: [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/),
[Sentry Python](https://docs.sentry.io/platforms/python/),
[Datadog Python tracing](https://docs.datadoghq.com/tracing/trace_collection/dd_libraries/python/)
e [New Relic Python](https://docs.newrelic.com/docs/apm/agents/python-agent/).

## #14 — gates da campanha web C6

Medição: zero `package.json`, lockfile, TypeScript/JavaScript de produto, configuração
Playwright, Biome, Knip, commitlint, Stryker ou Codecov fora de documentação e artefatos do
Graphify. Instalar agora criaria infraestrutura sem aplicação.

Ativar nesta ordem quando a stack web for aprovada:

1. fixar runtime, gerenciador e lockfile; contrato Python↔web + unitários/integração;
2. Biome para lint/format e teste arquitetural; avaliar ArchContract somente após módulos TS;
3. Playwright nas jornadas críticas: loading, sucesso, erro, cancelamento e movimento reduzido;
4. Knip após rotas/build estabilizarem; Codecov após política de upload; Stryker apenas em
   regras críticas com suíte rápida; commitlint somente se commits individuais forem produto;
5. CI com permissões mínimas, artefato por commit, smoke test e rollback antes de deploy.

O check Python `core` continua obrigatório e separado. Cobertura web ganha baseline/ratchet;
100% não é meta. Falha de infraestrutura é inconclusiva, nunca aprovação.

## Ordem dos gaps

1. Publicar #10/#17: contratos já preparados e sem dependência de produto.
2. Implementar a primeira fatia local de #12 (`run_id` + eventos estruturados) em issue própria;
   não instalar backend no mesmo diff.
3. Corrigir somente jornadas Tkinter críticas da #11 quando houver defeito ou mudança real.
4. Manter #22 aberta: o relatório separado registra a falha Codex/UI e o launcher Claude
   corrigido; não usar bytes como proxy de tokens.
5. Manter #14 aguardando a stack C6; os gates acima são condição de entrada.
