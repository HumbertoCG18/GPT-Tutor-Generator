# Observabilidade local — issue #12

Data: 2026-09-19. Escopo: primeira camada operacional do produto Python, sem serviço,
SDK ou exportação externa.

## Resultado

`src/observability.py` grava `operations.jsonl` no diretório local da aplicação. Cada
operação emite início e término com estes campos permitidos: `timestamp`, `run_id` UUID,
`operation`, `status`, `duration_ms`, `version` e, em falha, `error_type`. Mensagem da
exceção, traceback, caminho, URL, credencial, prompt e conteúdo acadêmico não entram nesse
arquivo.

Fronteiras instrumentadas: `RepoBuilder.build`, `incremental_build` e `process_single`.
`InterruptedError` vira `cancelled`; demais exceções viram `error`; a exceção original é
relançada. O logging diagnóstico preexistente continua responsável pelo traceback local.

As perguntas operacionais respondidas são:

1. Qual entrada pública iniciou e qual foi seu resultado?
2. Qual `run_id`, versão e duração pertencem à operação completa?
3. A operação terminou com sucesso, cancelamento ou tipo de erro conhecido?
4. O produto continua iniciando quando o destino local de logs está indisponível?

## Política operacional

- retenção: arquivo ativo de 2 MiB + cinco backups de 2 MiB; limite aproximado de 12 MiB;
- amostragem: 100% das três fronteiras, dois eventos por operação; dados de usuário ficam fora;
- cardinalidade: `operation`, `status`, `version` e `error_type` são conjuntos pequenos;
  `run_id` serve só para correlação, nunca como label de métrica agregada;
- modo offline: padrão e único modo implementado; falha ao abrir/configurar o arquivo gera aviso
  e não impede a UI;
- alertas locais: nenhum pager, pois desktop sem plantão não tem destinatário acionável;
- alertas futuros: após baseline e runbook, Sentry opt-in pode notificar o mantenedor sobre novo
  tipo de erro por versão e aumento sustentado da taxa de erro; limiar não será inventado antes
  da medição.

Contagens por `status` e distribuição de `duration_ms` fornecem o baseline de métricas. Os pares
`started`/terminal com o mesmo `run_id` formam o trace local mínimo. OpenTelemetry fica adiado:
não existe coletor nem consumidor que justifique SDK, custo de operação ou telemetria duplicada.

## Backend

Sentry permanece o candidato futuro para erros opt-in. O produto local precisa primeiro de conta,
consentimento, retenção, orçamento e destino de alerta aprovados. Datadog e New Relic ficam fora
desta fase: agentes/APM e exportação contínua não resolvem um gap atual do desktop. Nenhuma conta,
chave, contratação ou endpoint foi criado.

## Evidência

- RED: `python -m pytest tests/test_observability.py -q` falhou com
  `ModuleNotFoundError: src.observability`;
- GREEN: `8 passed`; `src.observability` com 92% de cobertura;
- privacidade: fixture com token, caminho e conteúdo bruto ausentes do JSONL;
- falha rastreável: teste induz `RuntimeError`, preserva o mesmo `run_id`, registra
  `status=error` + `error_type=RuntimeError` e relança a mesma instância;
- rotação: teste força `operations.jsonl.1` com limite reduzido;
- regressão: `1127 passed, 1 deselected`; o único teste excluído falha também em
  `origin/main@be0b195` por estado do corpus externo `Metodos-Formais-Tutor`;
- lint: Ruff verde em `observability.py`, `__main__.py` e nos testes; `engine.py` mantém
  um F841 preexistente em `out_path`, confirmado na base.

Rollback: reverter o PR remove o handler e os três wrappers. Arquivos JSONL locais já criados
podem permanecer até a rotação ou remoção manual; não contêm payload acadêmico pelo contrato.

Limite conhecido: `RotatingFileHandler` coordena threads de um processo, não duas instâncias
simultâneas do aplicativo. Suporte multiprocesso exige medição e handler próprio antes de ser
declarado.
