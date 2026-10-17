# Parecer do S10: job-29 (run-14), papel validador-externo, 01/10/2026

Texto final entregue pelo worker via `alethe_check` (outcome `succeeded`), transcrito integralmente. Os links do
original foram mantidos como caminhos.

---

APROVÁVEL COM AJUSTES

Não identifiquei violação funcional de R1–R6 nos caminhos examinados, nem achado CRITICAL/MAJOR. Este parecer não é Gate.

`ART` abaixo significa `docs/reports/2026-10-01-correcao-moodle-v1/`.

1. **MINOR — o teste de saldo exato não prova ausência de sondagem do framing.**
   Evidência: tests/test_moodle.py:832 e oráculo:1011 (tests/test_moodle.py:1011).
   **Cenário medido:** ao registro de C03, acrescentei em memória leituras do CRLF, chunk zero e terminador, mantendo `OrcamentoExcedido` e os 2 bytes contabilizados → `_confere_caso` devolveu `[]`. Portanto, esse teste aceitaria sondagem que o relatório afirma impedir. O código atual respeita a ordem correta.
   **Correção mínima:** verificar explicitamente que não existe operação posterior ao payload que esgota o saldo em C03/A31.

2. **MINOR — “principal inalterada” excede o alcance da fiscalização do S7.**
   Evidência: runner:24 (ART/runner_s7_adquire_v5.py:24), runner:104 e relatório:245 (ART/relatorio.md:245).
   **Cenário por inspeção:** alteração em arquivo já marcado `M`, fora das três subárvores fotografadas → pode preservar o mesmo `git status` e produzir `principal_alterada=[]`. Além disso, `--saida` apontando para a principal escreve nela **depois** da fotografia final, sem invalidar `resultado="ok"`. Não executei esse cenário destrutivo.
   **Correção mínima:** validar destinos resolvidos de `--saida`/`--basetemp` fora da principal e limitar a afirmação às áreas verificadas; garantia integral exige proteção de escrita. Não encontrei evidência de alteração ocorrida: os dois fontes da principal ainda coincidem com o delta congelado.

3. **MINOR — a proposta de REL deixa uma regra incompatível com R4.**
   Evidência: proposta:263 (ART/relatorio.md:263) e REL:295 (GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa3_correcoes_29-09/relatorio_correcoes_etapa3.md:295).
   **Cenário:** `Transfer-Encoding: chunked`, `Content-Length: 999`, saldo 3, payload `[]` → V1 lê 2 bytes e aceita, conforme M2c. Aplicar somente as substituições propostas preserva “Um Content-Length acima do orçamento restante não é lido”, contradizendo esse comportamento.
   **Correção mínima:** qualificar essa frase com “em respostas não chunked”; substituir também a associação irrestrita entre `None` e “comportamento anterior” por “sem limite de bytes”. O adendo proposto para ISS A6 já explicita corretamente as mudanças deliberadas.

4. **MINOR — descrição incorreta do intervalo de versões.**
   Evidência: relatório:219 (ART/relatorio.md:219) versus pyproject.toml:6.
   **Cenário:** Python 3.12 → satisfaz `>=3.11`, embora o §8 diga que a restrição “não cobre 3.12”.
   **Correção mínima:** escrever “3.12 está no suporte declarado, mas não foi testado”, como o próprio §7 já informa.

5. **MINOR — manifesto final citado não está no conjunto disponível.**
   Evidência: relatório:54 (ART/relatorio.md:54).
   **Cenário:** seguir a referência `hashes_finais.txt` → arquivo inexistente. O manifesto S10 disponível contém sete entradas, sem os resultados individuais.
   **Correção mínima:** marcar o manifesto final como pendente ou corrigir a referência e declarar seu alcance parcial.

A verificação sustenta a correção principal: os sete hashes S10 conferem; os JSONs registram 64/64 casos aprovados, com resultados idênticos nos três runtimes; as funções privadas relevantes têm AST idêntica. Reexecutei **em memória**, no 3.11.9, os 63 casos parametrizados e sondas adicionais sem `read1`, incluindo leitura curta, `IncompleteRead.partial` e timeout: passaram.

A instrumentação não apresentou leitura silenciosamente ignorada nos caminhos examinados: `readinto` falha explicitamente; a stdlib utilizada segue por `read`, `read1` e `readline`. Os oito controles vermelhos do delta falham somente por causa encadeada. `TIMEOUT-PAYLOAD` está corretamente classificado como novo: seu modelo entrega zero bytes ao `read` do delta, portanto não demonstra perda de fragmento previamente entregue nesse caso.

A identidade do cliente no S7 é válida para os imports e testes examinados: os testes usam `A.M.MoodleClient`, com o módulo da worktree preservado. Os registros sustentam os **40 aprovados** e, na suíte completa candidata, **2522 aprovados, duas falhas preexistentes e quatro pulos**.

Não conferi execução em 3.12, suíte completa em 3.13/3.14 nem reexecutei pytest/S7, pois escrevem arquivos. Não consigo atestar ausência absoluta de alterações na principal a partir das fotografias limitadas. Nenhum arquivo foi editado; não houve rede, motor ou abertura das áreas proibidas.
