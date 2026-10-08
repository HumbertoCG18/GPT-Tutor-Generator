# Piloto da noite — handoff (03/10/2026)

Campanha PILOTO, janela noite, worktree GPT-Tutor-Generator-noite (noite/piloto, da dev 163f779d).
Objetivo: observar o ciclo noturno e adiantar MOTOR-00 e VOCAB-01. Sem commit. Tarefas independentes entre si.
LAB = C:/Users/Humberto/Documents/GitHub/agent-workflow-lab · PRINCIPAL = C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator
CRU05 = C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-cru05

## Regras comuns
- Regras da noite: LAB/references/noite.md.
- Registro, diário e achados só via `python LAB/bin/campanhas.py`; não ler nem editar o
  .workflow/campanhas.json desta worktree (cópia defasada).
- Estado: .workflow/local/active-task.md desta worktree (modelo .workflow/task-state.template.md). Se existir
  um de outra tarefa, renomear para active-task-<ID>.md antes de criar o novo.
- Escrita só nesta worktree, em docs/reports/2026-10-03-piloto-noite/<NN>-*/ (a PILOTO-02 grava também a
  cópia da referência). Fora dela, só o que o CLI e os hooks gravam e os temporários das ferramentas.
- Proibido: git add/commit/push/merge/stash (trava até 04/10 08:00), rede, instalar, imprimir env/tokens ou
  conteúdo sensível, rebuild de tutores, LLM do produto, gold como insumo, editar src/ ou tests/.
- Fim: active-task `status: concluido`, `gate_2: pendente`; `campanhas.py noite <ID> --resultado aguarda-voce
  --resumo "…" --evidencia "<pasta>"`. Sem como seguir: `--resultado parou|falhou` com a causa.
  Nunca `estado … concluída`.
- Todo relatório termina com "Observação do piloto": hora de início e fim, permissões negadas
  (comando + mensagem), onde travou, desvios deste handoff.
- Achado fora da tarefa: `campanhas.py achado … --origem <ID>`, até 3, sem investigar.

## PILOTO-01 — Calibração: suíte na worktree
- Objetivo: provar o ciclo (estado → execução → relatório → diário → aguarda você).
- Entradas: tests/. Base documentada em bf46d51f (src/ e tests/ idênticos à dev 163f779d): 2447 passed,
  2 failed, 4 skipped. Falhas da base:
  test_caracterizacao_blocos_atual.py::test_divisao_de_blocos_atual[Fundamentos-de-Redes-Tutor] e
  test_pdf_markdown.py::test_respect_actualtext_tira_a_flag_e_restaura.
- Passos: 1) `git status --porcelain` (antes); 2) `python -m pytest tests -q`, gravando início, fim, as últimas
  40 linhas e o exit code em 01-calibracao/suite.txt; 3) relatorio.md com contagens e comparação com a base;
  4) `git status --porcelain` (depois).
- Aceite: suite.txt com linha-resumo e exit; cada falha classificada "da base" ou "nova"; o status depois só
  acrescenta docs/reports/2026-10-03-piloto-noite/.
- Evidência: 01-calibracao/{suite.txt,relatorio.md}.
- Não fazer: corrigir teste, rodar de novo para "limpar" falha, mexer em src/ ou tests/.

## PILOTO-02 — MOTOR-00: preparar a referência e024d396 para versionar
- Objetivo: replay_base.json nesta worktree, verificado byte a byte; commit no Gate 2. Destrava MOTOR-00
  (e, por ela, REPLAY-01 e LIMPEZA-03).
- Entradas: CRU05/docs/reports/2026-10-01-cru05-cru03/replay_base.json (64 KB, sha256 e024d396bf1cc84c…).
  A CRU05 é só leitura: nada é escrito nela.
- Passos: 1) sha256 da origem; se não começar por e024d396bf1cc84c, `parou`; 2) `git -C CRU05 status
  --porcelain` (antes); 3) `cp` (binário) para docs/reports/2026-10-01-cru05-cru03/replay_base.json desta
  worktree; 4) sha256 e bytes do destino; 5) `git check-ignore -v` no destino; 6) `gitleaks dir <destino>
  --no-banner --redact` (só exit e contagem); 7) status da CRU05 (depois); 8) verificacao.md com tudo e o
  comando sugerido para o Gate 2, sem executar.
- Aceite: sha256 destino = origem = e024d396bf1cc84c…; mesmo tamanho; não ignorado; gitleaks 0 (se houver,
  só a contagem, e aguarda você); status da CRU05 idêntico.
- Evidência: 02-motor-00/verificacao.md + a cópia.
- Não fazer: copiar outros arquivos de cru05-cru03, abrir o JSON em editor, reformatar, escrever na CRU05,
  rodar replay.

## PILOTO-03 — VOCAB-01: manifesto dos relatórios de validação externa de 29/09
- Objetivo: inventário verificável do que versionar na PRINCIPAL; `git add` no Gate 2. Destrava VOCAB-01
  (e, por ela, LIMPEZA-03).
- Entradas (não versionadas na PRINCIPAL): docs/reports/_harness-2026-09-04/c1-3/validacao_externa*_29-09/
  (5 pastas, 251 arquivos) e docs/reports/2026-09-29-regime-vocab-validacao-externa-preregistro.md.
- Passos: 1) `git -C PRINCIPAL status --porcelain -uall` (antes); 2) candidatos = entradas `??` que casam com
  os dois padrões; os demais `??` vão para "fora do escopo", só a pasta; 3) manifesto.tsv com caminho, bytes e
  sha256 por candidato; 4) `git check-ignore` por pasta; 5) `gitleaks dir <pasta> --no-banner --redact` por
  pasta e no pré-registro (só exit e contagem); 6) status (depois); 7) manifesto.md com totais por pasta,
  gitleaks, ignorados, fora do escopo e `git add` sugerido, sem executar.
- Aceite: linhas do manifesto.tsv = candidatos (esperado 252); sha256 com 64 hex; status da PRINCIPAL igual
  antes e depois (fora .workflow/; diferença → registrar e aguardar você); nenhum conteúdo copiado.
- Evidência: 03-vocab-01/{manifesto.tsv,manifesto.md}.
- Não fazer: copiar os relatórios para esta worktree, escrever na PRINCIPAL, executar scripts do harness,
  decidir D1–D9 (VOCAB-02).
