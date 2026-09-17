# Revisão Astra do diff: remoção da exportação DeepTutor (17/09, read-only)

session id: 01a0ae19-405f-72d1-b35f-b0abc9b271f1 | codex exec --profile astra --sandbox read-only | 03:41:25→03:50:58 | rc=0 | tokens não capturados no log | árvore inalterada pela chamada.

Brief: scratchpad/brief-astra-deeptutor.md (não versionado; diff de 13 arquivos inline, patch sha256 3781162a…). Mensagem final consumida via -o, sem concatenar eventos.

Consumo pelo Fable: 1 BLOQUEIA e 3 AJUSTE verificados na fonte e aplicados; 4 NOTA registradas; correção do brief: +14, não +25.

---

1. [BLOQUEIA] B — Remover o ignore expõe o legado ao Git — Medido: os 8 tutores são repositórios Git; `.deeptutor/` existe, não está versionado e é ignorado por `.gitignore:33`. O arquivo é sobrescrito em src/builder/ops/bootstrap_ops.py:233 e src/builder/ops/pedagogical_regeneration.py:529. Inferência: após rebuild/incremental, um futuro `git add .` poderá incluir o legado; não haverá versionamento automático apenas pelo build. Nenhum teste ou contrato vivo encontrado exige essa exclusão; tests/test_core.py:3851 não a verifica — Manter `.deeptutor/` como exclusão de legado e acrescentar a asserção ao teste do `.gitignore`.

2. [AJUSTE] A — A cópia experimental passa a transportar DeepTutor — Medido por leitura: scripts/ablacao_rapida.py:31 remove a exclusão usada pelo `robocopy /E` em :51. Inferência: `sync()` passa a copiar `.deeptutor/` existente, embora o builder não o atualize — Restaurar a exclusão; desativar o exportador não exige copiar seus resíduos.

3. [AJUSTE] E — Documentação ainda anuncia exportação ativa — Medido: docs/superpowers/plans/2026-06-11-auditoria-artefatos.md:112, fora de Feitos, mantém “export externo (todo build)” e “manter”. O template editado ainda manda “colar no DeepTutor” em docs/deeptutor-soul-template.md:7 — Marcar a linha do plano como superada e adaptar a instrução do template à referência futura. A menção em docs/reports/pendencias.md:1521 pertence ao relato datado de 07/09; preservar seu caráter histórico.

4. [AJUSTE] F — BACKLOG atribui remoção indevida a MODES.md — Medido: docs/superpowers/BACKLOG.md:95 retira MODES.md da pendência e o agrupa com o módulo removido. Porém src/builder/ops/pedagogical_regeneration.py:526 continua gerando system/MODES.md, usando src/builder/artifacts/pedagogy.py:243 — Retirar da pendência apenas `_soul_md`; preservar MODES.md como consumidor existente.

5. [NOTA] A — Exportador e chamadas explícitas removidos — Medido: nenhuma definição, importação ou chamada de `write_deeptutor_export` restante em src/, scripts/, tests/, .claude/ ou .codex/, incluindo scripts/hooks/. Resta referência local não versionada em src/academic_tutor_repo_builder.egg-info/SOURCES.txt:13, sem função operacional de exportação — Nenhuma remoção adicional de código identificada; tratar o metadado na próxima regeneração normal.

6. [NOTA] C — Os testes alcançam os dois pontos removidos — Medido por leitura: tests/test_core.py:3688 chama build(), encaminhado por src/builder/engine.py:1770; tests/test_core.py:4503 chama incremental_build(), encaminhado por :2123. HEAD tinha somente essas duas chamadas diretas ao exportador. UI e scripts usam essas entradas; reject/reprocess usam também regeneração pedagógica, sem exportador próprio — Manter as duas asserções. Elas não verificam preservação de uma pasta legada preexistente nem sua exclusão do Git.

7. [NOTA] D — Poda e compactação não procuram a pasta legada — Medido por leitura: src/builder/artifacts/repo.py:594 filtra entradas do manifest e :600 limita logs; a busca de Markdown em :489 usa diretórios enumerados, sem `.deeptutor`. As podas atuam nas referências de imagens (src/builder/core/image_resolution.py:216) e em code_curation.json (src/builder/core/code_summarization.py:502). Nos 8 tutores, esses manifests/curadorias não mencionam `.deeptutor` — Preservar esse comportamento; não acrescentar limpeza do legado.

8. [NOTA] F — Dois números do brief precisam correção — Medido: diff sem PENDING = 13 arquivos, +14/−305; `git diff --check` sem erros. Excluindo somente as duas asserções, a busca Python ainda encontra o comentário em tests/test_core.py:3691 — Corrigir +25 para +14 e declarar “zero referências operacionais”, excluindo também o comentário.

VEREDITO: REPROVAR
NÃO VERIFIQUEI: execução dos builds/testes; resultados 2 failed, 3 passed e 2357 passed/4 skipped em 42 s; efeito após rebuild real; exclusões globais do Git. Revisão exclusivamente estática e comandos de leitura.