# Piloto Context Mode por MCP isolado — 18/09/2026

Issue: [#18](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/18).
Resultado: **gate MCP aprovado; hooks ainda não avaliados nem ativados**.

## Escopo e isolamento

Fonte fixada: `mksglu/context-mode@c127f2fe8496fefc36e0ebef36ded92d4fa8f570`,
versão `1.0.169`, licença Elastic-2.0. O piloto executou `server.bundle.mjs` diretamente.
Não usou `start.mjs`: esse entrypoint contém autocorreções de plugin e instalações em
background, incompatíveis com o isolamento exigido.

HOME, DATA_DIR, PROJECT_DIR, configuração Claude e TEMP apontaram para o sandbox do piloto.
Dependências foram instaladas com `--ignore-scripts` apenas no clone privado. Nenhuma configuração
de Claude, Codex ou AGY mudou; nenhum pacote global, skill ou hook foi instalado.

Contrato: [`_context-mode-pilot/contract.json`](_context-mode-pilot/contract.json).
Harness: [`_context-mode-pilot/run_pilot.py`](_context-mode-pilot/run_pilot.py).
Resultado estruturado: [`_context-mode-pilot/result.json`](_context-mode-pilot/result.json).
Revisão independente: [`_context-mode-pilot/astra-review.md`](_context-mode-pilot/astra-review.md).

## Resultado medido

| Fixture/check | Resultado | Evidência |
|---|---|---|
| Superfície MCP | passou | 11 tools; `ctx_execute`, `ctx_execute_file` e `ctx_search` presentes |
| Erro | passou | `isError=true`; exit code `7`, stdout e stderr preservados na resposta |
| Unicode direto | passou | `ação|漢字|🎉|é` retornou sem `U+FFFD` na execução final |
| JSON | passou | payload parseado e igual ao objeto esperado |
| Segredo sintético | passou | conteúdo processado por hash; zero ocorrência em resposta, stderr e sandbox fora da fixture |
| Truncamento/indexação | passou | 14.280 bytes determinísticos → resposta de 1.705 bytes, marcada como indexada |
| Recuperação por `ctx_search` | passou | 120/120 linhas recompostas; SHA-256 igual ao original |
| Exit do servidor | passou | `0` após EOF do stdio |
| Isolamento | passou | quatro configs globais e bundle com hashes pré/pós idênticos; ambiente filho allowlisted |

A execução de calibração sem `intent` não cruzou o limiar de indexação com 14 KB; a fixture final
acionou explicitamente o caminho documentado usando `intent`. O stream final usou LF explícito por
`sys.stdout.buffer.write`. Uma execução intermediária mostrou `U+FFFD` em snippets ASCII; as duas
execuções finais não reproduziram isso. O achado não sustenta bloqueio, mas deve ser repetido.

## Recuperação bruta

O primeiro harness exigia o bruto inteiro contíguo em uma única resposta e inferia capacidades por
nome de tool; a revisão Astra reprovou esse desenho. A correção definiu recomposição verificável:
120 queries por marcadores únicos, agrupadas em seis chamadas, extração apenas de linhas completas,
ordenação por índice e comparação byte a byte.

Resultado final: 120/120 linhas, SHA-256 recomposto e esperado
`3a93f24df4a49a07aab472322b90440dd673d4e1d6c21e736298565b0d3c5ba5`.
Isso prova a rota ensaiada com dados marcados; não prova recuperação prática de qualquer blob sem
termos pesquisáveis. O custo foi seis chamadas MCP após a indexação.

## Decisão

O MCP fica elegível para a próxima avaliação. Não registrar Context Mode nas três CLIs ainda:
compatibilidade, duplicidade, latência, segurança e rollback dos hooks exigem issue/plano próprios.
Nenhum hook foi executado nesta etapa. A recuperação marcada deve ser comparada com payloads reais
antes de concluir economia de tokens ou substituir as ferramentas atuais. Próxima etapa:
[#19](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/19).
