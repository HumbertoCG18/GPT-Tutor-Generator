# MOTOR-9-01 — diagnóstico de integração da PR #9 e plano (24/09/2026)

Sessão Claude Code na nuvem, noturna, sem supervisão. Só diagnóstico e plano: nenhum conflito foi
resolvido, nenhum código de produção mudou, nada foi commitado em `feat/motor-atribuicao`, `main` ou
na PR #9. Toda simulação rodou em árvore descartável na área de rascunho da sessão, a partir de
`git merge-tree --write-tree`. Este arquivo também é o handoff da sessão (§10).

Objetivo: determinar como integrar as entregas de `feat/motor-atribuicao` à `main` preservando os
comportamentos aprovados dos dois lados. Não repete o diagnóstico de acurácia do motor.

## 0. Resumo executivo

1. A divergência real é pequena em código e grande em documentos. A `main` traz 12 arquivos de
   código/CI (+814/−33) que o git aplica sozinho sobre o motor sem nenhum conflito de código. Os
   9 conflitos são todos de configuração e documentação.
2. Sobre a árvore mesclada simulada, a suíte no Linux da nuvem tem exatamente o mesmo conjunto de
   falhas da ponta do motor (26 falhas e 2 erros de coleta, todos preexistentes e de ambiente) e
   ganha 25 execuções de teste (21 funções novas da `main`, algumas parametrizadas, mais o teste antes deselecionado), todas verdes. Nenhuma regressão de teste detectável aqui.
3. Bloqueio real para a integração: o check obrigatório `core` da `main` reprovaria a árvore
   mesclada no ratchet do Ruff (61 impressões digitais acima do baseline; 97 achados), porque o
   baseline foi tirado em 18/09 sem o código do motor. É preciso regerar o baseline no mesmo
   commit da integração ou limpar os achados (decisão D3).
4. Risco de segurança fora da PR, mas que a integração propagaria: a `main` versiona
   `moddle/.m365_token.json` com um `refresh_token` (commit `40cfa28e`, 09/06), além de
   `.superpowers/brainstorm/**` e `motion-audits/*.html`, todos listados no `.gitignore`. O motor
   nunca teve o token. Recomendação: PR de higiene na `main` antes da integração (D4).
5. Estratégia recomendada: merge da `main` no motor preparado em branch temporária a partir da
   ponta do motor, resolvido e validado, e publicado por fast-forward em `feat/motor-atribuicao`;
   depois a PR #9 entra na `main` por merge commit (não squash). Detalhe em §6 e §7.
6. O escopo da PR #9 é a campanha inteira desde 06/2026 (1112 commits, 2567 arquivos, +985 mil
   linhas, das quais a quase totalidade é dado de harness em `docs/reports/`). A descrição da PR
   cobre só as entregas de 21 a 23/09 e omite a #49, que está no branch. Proposta de revisão por
   grupos em §5.4.

## 1. Base fixada

| Referência | SHA | Data | Conferido |
|---|---|---|---|
| `origin/main` | `77a043f58d487e85850f8d2660d97da8ab8fd7d9` | 23/09 (merge #62) | igual ao informado pelo usuário |
| `origin/feat/motor-atribuicao` | `76e4357b8ecf9c1ca92762bd58d76b622ad0ad54` | 24/09 (ROUTER) | igual |
| ancestral comum (`git merge-base`) | `8f1081927ecac16d658641fb39a8ab974c17238c` | 04/06 | igual |
| árvore do `merge-tree main ← motor` | `5e7805a5c9383a665100227015af594aaad04ea5` | — | gerada nesta sessão |

- O clone chegou raso (`is-shallow-repository = true`) e com o HEAD local em `875f97fc`, ancestral
  da ponta do motor. Foi feito `git fetch --unshallow origin` e `git fetch origin main
  feat/motor-atribuicao` antes de qualquer cálculo. Git 2.43.0.
- Divergência: 62 commits só na `main` (24 no first-parent, todos merges de PR ou commits diretos
  listados em §3.1) e 1112 só no motor.
- Arquivos mudados desde o ancestral: `main` 239 (157 A, 3 D, 18 M, 61 R); motor 2567 (2344 A,
  21 D, 135 M, 67 R). Caminhos tocados pelos dois lados: 265, dos quais 61 são as mesmas
  renomeações (`docs/superpowers/{plans,specs}/* → docs/{plans,specs}/Feitos/*`, `plans/* →
  docs/plans/*`) feitas de forma idêntica nos dois históricos.
- `git merge-tree --write-tree` nas duas direções: 9 arquivos em conflito, os mesmos.
- PR #9: aberta, não rascunho, `mergeable_state = dirty`, 0 check runs no head (com conflito o
  GitHub não gera a ref de merge, logo o workflow `python-quality.yml` da `main` nunca rodou para
  ela). Base registrada na API: `208af96e` (obsoleta; a `main` avançou).

## 2. Ambiente e método

- Primeira ação da §1 do guia da nuvem: `pydantic` 2.13.5 e `pytest` 9.1.1 presentes; hook
  `.git/hooks/pre-commit` ausente, instalado com `cp` + `chmod +x` (sem `gitleaks`, o hook só
  avisa); `/tmp/setup-nuvem.log` lido (script roda como root fora do clone, `tkinter` ausente).
- Simulação: `git archive <árvore do merge-tree>` extraído no rascunho da sessão; os 9 arquivos
  em conflito ficam com marcadores. Para rodar Ruff e pytest, só o `pyproject.toml` recebeu, na
  cópia descartável, a resolução proposta em §4 (união dos dois lados com `target-version =
  "py311"`). Nenhum outro conflito foi tocado.
- Comando de testes do `setup.md` (Linux), com `TUTOR_COURSES_DIR` apontando para diretório
  inexistente, como na CI. Limitações da nuvem: sem `tkinter`, sem tutores locais, sem
  `google-genai`; 21 testes dependem de caminho Windows (#68) e o mock de `tkinter` vaza (#69).

## 3. Inventário das entregas

### 3.1 Exclusivas da `main` (62 commits)

Código e CI (12 arquivos, +814/−33; tudo auto-mesclável):

| Entrega | Commits | Arquivos | Comportamento aprovado |
|---|---|---|---|
| #39 / issue #12 — observabilidade local privada | `5ef21dfd`, `78751044` | `src/observability.py` (novo, 149 linhas), `src/__main__.py`, `src/builder/engine.py` (método `_operation_scope` e envelope em `build`, `incremental_build`, `process_single`), `tests/test_observability.py` | eventos JSONL locais rotativos, correlação por UUID, `entry_point` estável, status `partial` quando `failed_entries` cresce; offline, sem SDK |
| #40 / issue #11 — progresso nativo e movimento reduzido | `a29fc941`, `6aefdade` | `src/ui/app.py` (4 funções puras + `_set_progress_paused`, `_apply_reduce_motion_preference`; remove `_tick_fake_indeterminate`), `src/ui/dialogs.py` (checkbox em `SettingsDialog`, `_start_busy_progress` no importador Moodle), `src/ui/theme.py` (`reduce_motion: False` nos defaults), `tests/test_ui_queue_dashboard.py` (+151) | barra ttk nativa determinada/indeterminada; preferência persistida vale na operação ativa e sobrevive à prévia de tema |
| #30 / issue #13 — ratchets de qualidade | `a0a2bd30` | `.github/workflows/python-quality.yml`, `.github/python-quality-baseline.json`, `scripts/verify_python_quality.py`, `tests/test_verify_python_quality.py`, `pyproject.toml` (`pydantic>=2.0` declarado, extras `pytest-cov`/`ruff`, `[tool.ruff] py38`, `[tool.coverage.run]`), `tests/test_core.py` (`os.name` via `SimpleNamespace`) | check `core` obrigatório: suíte + cobertura por plataforma (Linux 79,62 %, Windows 79,69 %) + Ruff por arquivo/código + contrato arquitetural (`src` fora de `ui` não importa `src.ui`, exceção única em `build_workflow.py`) |
| #62 / issue #14 — contrato de qualidade C6 | `1304c132`, `acbc7075`, `89937c9b` | `docs/reports/2026-09-19-contrato-qualidade-c6.md`, `.mex/patterns/engenharia-produto-details.md`, `docs/reports/pendencias.md` (versão de 2,6 KB da `main`), handoff do workflow | só documentação |
| Workflow e contexto (#20, #21, #25, #26, #28, #29, #31, #32, #34, #36, #38, #55, #58, #61) | vários | `.workflow/**`, `.mex/patterns/**`, `.github/{ISSUE_TEMPLATE,pull_request_template}.md`, `.claude/settings.json`, `.codex/config.toml`, `scripts/hooks/{pre-commit.sh,repor-podas.py}`, `docs/plans|specs/Feitos` | contratos, templates e reorganização; os três "propagar-main" espelham commits do motor (§3.3) |
| README (`208af96e`, 09/06) | 1 | `README.md` reescrito | descreve o sistema atual (badge Python 3.11+) |

Arquivos versionados na `main` apesar do `.gitignore` (nenhum existe no motor):
`moddle/.m365_token.json` (chave `refresh_token`; `40cfa28e`, 09/06), 12 arquivos em
`.superpowers/brainstorm/**` (`40cfa28e`), `motion-audits/academic-tutor-repo-builder-2026-09-19.html`
(`a29fc941`), `.claude/settings.local.json` e `.token-savior-cache.json` (existiam no ancestral; o
motor os removeu, a `main` não os alterou, logo o merge os remove sem conflito). O merge manteria
os três primeiros na árvore integrada.

### 3.2 Exclusivas do motor (1112 commits: 496 docs, 262 feat, 184 fix, 39 chore, 35 test, 33 refactor, outros)

| Grupo | Conteúdo | Evidência |
|---|---|---|
| Motor de atribuição (regime cru) | `src/builder/routing/motor/`, `src/builder/ops/assignment_run.py`, D9 (`temporal_*`), gate D4, providers, desempate, `due_window`, identidade estável de bloco (`933485d8`) | `src` 96 arquivos +12.339/−3.500; `tests` 226 arquivos +26.702/−2.070; `scripts` 53 arquivos |
| Cutover e limpeza | `df862033` deleção do funil legado (remove `scripts/{eval_assignments,eval_cards,retag_manifest,backfill_source_section}.py`, `tests/test_resolve_unit_block_*.py`, `test_card_block_assignment.py`, `test_date_prefix_signal.py`, `test_ddmm_timeline_boost.py`, `test_eval_*.py`, `test_retag_manifest.py`); `fd0747a0` remove exportação DeepTutor (`src/builder/artifacts/deeptutor.py`); consolidações A1/A2/B (`4f60bd0b`, `0efa29ad`, `46499aae`, com zero-diff nos 8 tutores) | a `main` não alterou nenhum desses arquivos: o merge os apaga sem conflito |
| #47 seção corroborada vence bloco (CRU-03) | `9220a578` (21/09): `routing/file_map.py`, `resolver_apply.py`, `facade/file_map.py`, `ui/dialogs.py`; testes `test_reconcile_unit_block.py`, `test_resolver_apply_units.py`, `test_file_map_unit_mapping.py`, `test_core.py` | issue: 239 → 244/284, 0 perda |
| #48 prova hospeda entrega, TDE, vizinho (CRU-03/04) | `b726d4cd` (22/09): `motor/due_window.py`, `motor/apply.py`, `file_map.py`, `resolver_apply.py`, `ui/dialogs.py`; `test_motor_due_window.py`, `test_motor_apply.py` e os de unidade | bloco 213 → 214/237, unidade 244 → 246/284 |
| #49 `_score` sem `sqrt(len(sig))` (CRU-04) | `410592d8` (22/09) "fix(motor): _score do desempate deixa de dividir por sqrt(len(sig))": `motor/disambiguator.py` (14 linhas; docstring cita a #49) e `tests/test_motor_disambiguator.py` (+65: `test_score_ignora_termos_da_assinatura_que_nao_casam`, `test_desempate_prefere_mais_evidencia_a_assinatura_curta`, `test_empate_positivo_margem_zero_e_flag_independem_do_comprimento`, mais 2); harness `aceite_v1_49_22-09.*`. O divisor entrou em `c8a28007` (07/07) | está no branch e no código publicado; o título do commit não traz `#49`, a PR não a lista. Não reaplicar |
| #50 "Prova N" → P<N>, seção de avaliação, unidades sem bloco | `493119e1` (22/09): `extraction/content_taxonomy.py`, `timeline/index.py`, `ui/timeline_dashboard.py`; `tests/test_assessment_label_and_plan_section.py` (novo), `test_review_list_block.py`, `test_timeline_sort.py` | publicada; a continuação (data da prova, `EXAM_INDEX.md`) só existe no worktree local (§3.5) |
| #63 preservar `feature_flags` ao salvar matéria | `7d90debd` (23/09): `ui/dialogs.py` (2 linhas), `tests/test_subject_dialog_save.py` | |
| #64 registro da execução da atribuição | `36b00ab9` (23/09): `ops/assignment_run.py` (novo; `FLAG_DEFAULTS`, `manifest["assignment_run"]`), `ops/pedagogical_regeneration.py`, `ui/app.py` (`_build_options_from_config` com `subject`), `scripts/reprocess_assignments.py`, `docs/Overview-Sistema.html`; `tests/test_assignment_run_record.py`, `test_reprocess_flags.py` | |
| #65 D9 cru para matérias novas | `f312267d` (proposta), `844c61b7` (`models/core.py` `NEW_SUBJECT_FEATURE_FLAGS = {"use_anchor_engine": True}`, `sources/moodle.py`, `ui/dialogs.py`; `tests/test_new_subject_d9_default.py`), `fc4a9466` (validação: replay de preservação idêntico) | |
| Régua v2, medições e handoffs | `9cfdf2c7`, `14f0e08d`, `1a968a2e`, `64463780` (tracker com bloco `fila-campanhas` e handoffs 21–23/09), `76e4357b` (ROUTER) | `docs/reports/` 1982 arquivos |
| Contexto e guardas | `.mex/context/{sessao-nuvem,architecture,decisions,conventions,institutional,setup,...}.md`, `scripts/hooks/{agy-adapter,engine-facade-guard,gemini-antipattern-guard}.js` (a `main` referencia o guarda Gemini no `pre-commit.sh`, mas não tem o arquivo), PRs #59, #60, #66, #73 mescladas no motor | |

### 3.3 Equivalentes ou duplicadas por históricos diferentes

- Reorganização de planos e specs (`docs/superpowers → docs/{plans,specs}/Feitos`, `plans/ →
  docs/plans`): idêntica nos dois lados; o git a reconhece e não conflita.
- Propagações `chore/44-propagar-main` (#55), `chore/56-propagar-main` (#58) e
  `chore/59-propagar-main` (#61) reproduzem na `main` os commits `7b8705cd`, `61017256`,
  `2067d8d5` do motor. Resíduo após o merge: só os 2 conflitos documentais de §4 (itens 4 e 5).
  `.claude/settings.json`, `.codex/config.toml`, templates de issue/PR, `.gitleaks.toml`,
  `CLAUDE.md`, `GEMINI.md`, `ROADMAP.md` e `validate-timeline.yml` são byte-idênticos.
- `scripts/hooks/pre-commit.sh`: o mesmo fix do guarda Gemini entrou como `b5b59429` (main) e
  `0ef03ee5` (motor); o motor acrescentou `6d778f39` (chmod e dica de instalação fora do Windows).
- `tests/test_core.py`: o fix da `main` (`SimpleNamespace(name="nt")`) resolve a queda global do
  pytest no Linux descrita em `sessao-nuvem.md` §12; o motor não o tem. Na árvore mesclada a suíte
  rodou sem o `--deselect` do `setup.md`.
- Extras `pytest-cov`/`ruff` no `pyproject.toml`: idênticos nos dois lados (fora do conflito).

### 3.4 Conflitantes ou parcialmente sobrepostas

Nove arquivos (§4). Mais seis arquivos de código que o git mescla sozinho, mas cujas interações
foram examinadas em §5: `src/builder/engine.py`, `src/ui/app.py`, `src/ui/dialogs.py`,
`src/ui/theme.py`, `tests/test_core.py`, `tests/test_ui_queue_dashboard.py`.

### 3.5 Trabalho só no worktree local (dado do usuário; não reproduzível aqui)

| Item | Estado local | Verificado na nuvem | Risco de integração |
|---|---|---|---|
| Continuação da #50, sem commit, 5 arquivos (+93/−7): `src/builder/ops/bootstrap_ops.py`, `src/builder/ops/pedagogical_regeneration.py`, `src/builder/timeline/index.py`, `tests/test_assessment_label_and_plan_section.py`, `tests/test_pedagogical_regeneration_order.py` | Gate 2 pendente desde 22/09 (handoff de 23/09 §4.4; comentário de 22/09 na #50: data da prova prefere a linha da prova; `EXAM_INDEX.md` sempre regenerado) | a `main` não alterou nenhum dos três arquivos de código desde o ancestral (diff vazio); os dois testes não existem na `main`; `test_pedagogical_regeneration_order.py` também não existe no motor publicado | o merge da `main` não toca esses arquivos, logo o git não o bloqueia por causa deles. Porém `36b00ab9` (#64, 23/09) alterou `pedagogical_regeneration.py` depois de o diff local nascer; se o worktree já contém `36b00ab9` (esperado, pois o mesmo worktree o commitou), o diff é relativo a ele. **Só confirmável localmente**: `git status --short src tests` e `git diff --stat` devem mostrar os 5 arquivos sobre HEAD ≥ `36b00ab9` |
| 4 artefatos não versionados de 17/09 em `docs/reports/_harness-2026-09-04/c1-3/`: `astra_revisao_regime2_17-09.md`, `diagnostico_subunidade_17-09.{csv,json,py}` | untracked (o `.gitignore` não os ignora; nunca foram adicionados) | ausentes na ponta do motor; **scripts versionados dependem deles**: `replay_subunidade_21-09.py:38` e `wp1_inventario_matriz_22-09.py:66` carregam `diagnostico_subunidade_17-09.py`; o handoff de 21/09 registra o sha256 do `.json`; `astra_pesquisa_subunidade_21-09.md` e o tracker os citam | nenhum risco no merge; risco de reprodutibilidade (harness publicado não roda a partir do clone). Decisão D11 |
| Tracker `docs/reports/pendencias.md` | pode ter edições locais sem commit (guia §6) | a ponta do motor já traz o bloco `fila-campanhas` (`64463780`) | **bloqueia o merge local**: `pendencias.md` é um dos 9 conflitos; `git merge` recusa sobrescrever arquivo com alteração local não commitada. Commitar ou guardar (stash) antes |

## 4. Mapa de conflitos (9 arquivos)

Legenda: "ours" = `main`, "theirs" = motor, na simulação `main ← motor`.

| # | Arquivo | Tipo | O que a `main` mudou | O que o motor mudou | Comportamento a preservar | Resolução proposta | Evidência | Teste que demonstra | Decisão pendente |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `pyproject.toml` | conteúdo | `pydantic>=2.0` em `dependencies` (auto-mesclado), `[tool.ruff] target-version = "py38"`, `[tool.coverage.run] omit = [src/__main__.py, src/ui/*]` | `[tool.ruff] target-version = "py311"` com comentário; sem coverage; sem pydantic | CI `core` (cobertura ignora UI; pydantic instalado por `pip install -e .[dev]`); código do motor exige ≥ 3.9 (`with (...)` parentizado em `tests/test_resolver_wiring.py`, 5 ocorrências) e a CI roda 3.11 | União: `pydantic` + `[tool.ruff] line-length = 100, target-version = "py311"` + `[tool.ruff.lint] select = ["E9","F","B"]` (idêntico nos dois) + `[tool.coverage.run]` da `main` | com `py38` o Ruff reprova por sintaxe (5 `invalid-syntax`); com `py311` passam a valer 12 achados `B905` (`zip` sem `strict`) em 3 arquivos, que entram no baseline (D3) | `python scripts/verify_python_quality.py --coverage coverage.json` verde na árvore integrada; `tests/test_verify_python_quality.py` (passou na simulação) | D2: manter `requires-python = ">=3.8"` (obsoleto; README da `main` diz 3.11+) ou subir para `>=3.11` |
| 2 | `.gitignore` | conteúdo (mesma região) | +42 linhas (propagação da organização `.workflow/local/`) | as mesmas linhas + `/.alethe/` e `/%SystemDrive%/` | ignorar os dois conjuntos | União (versão do motor, superconjunto) | diff `main → motor` = só as 4 linhas do motor | `git check-ignore -v .alethe %SystemDrive% .workflow/local` | nenhuma |
| 3 | `scripts/hooks/pre-commit.sh` | add/add | criado em `b5b59429` (guarda Gemini + gitleaks) | criado em `0ef03ee5` (mesmo conteúdo) + `6d778f39` (comentário sobre `chmod +x`, dica de instalação fora do Windows) | hook funcional no Windows e no Linux | Versão do motor (superconjunto; diferença de 3 linhas, só texto) | diff `main → motor` = 3 linhas | `git hook run pre-commit` após instalar; commit deste relatório usou o hook | nenhuma |
| 4 | `.workflow/pendencias_workflow.md` | add/add | inclui parágrafo "Context Mode não adotado… plugins mantidos intencionalmente" (`aefaa0b8`, 23/09) | mesmo arquivo sem esse parágrafo (`61017256`, `2067d8d5`) | registro de decisão (#22 fechada; plugins não são pendência) | Versão da `main` (superconjunto: 4 linhas a mais) | `git log -S` mostra o parágrafo só na `main` | leitura | D6 (confirmar que o parágrafo continua válido) |
| 5 | `.mex/patterns/engenharia-produto-details.md` | add/add | linha da #14 aponta o contrato C6 e a #41 (`1304c132`, PR #62) | linha antiga "gates da campanha C6" | ponteiro atual do contrato C6 | Versão da `main` (diferença de 1 linha) | diff `main → motor` = 1 linha | links relativos resolvem (`docs/reports/2026-09-19-contrato-qualidade-c6.md` existe nos dois lados) | nenhuma |
| 6 | `AGENTS.md` | conteúdo | consolidado (#59 propagado) | + linha "Sessão na nuvem … `sessao-nuvem.md`" | ambas | Versão do motor (superconjunto; 1 linha) | diff = 1 linha | leitura | nenhuma |
| 7 | `.mex/ROUTER.md` | conteúdo (tabela) | linha "Motor/produto" aponta `2026-09-17-handoff-regime-cru.md`; linha "Estrutura/callers" sem fallback | aponta `2026-09-23-handoff-motor-wz-waa-claude.md` (+anteriores), acrescenta linha "Sessão na nuvem" e o fallback `context/architecture.md` | rotas atuais | Versão do motor (superconjunto e mais recente) | diff = 5 linhas | leitura; arquivos apontados existem no motor | nenhuma |
| 8 | `README.md` | conteúdo | reescrita completa (`208af96e`, 09/06): 364 linhas, Python 3.11+, seções atuais | 1 linha no bloco "Notas de Manutenção" (`docs/superpowers/` → `docs/plans/ e docs/specs/`), bloco que a `main` removeu | README da `main` | Versão da `main` inteira (o motor só ajustou um caminho num bloco que não existe mais) | `git diff MB..motor -- README.md` = 1 linha; conflito é remoção × edição do mesmo bloco | leitura | nenhuma; opcional: README passar a citar o motor D9 (fora deste escopo) |
| 9 | `docs/reports/pendencias.md` | add/add | tracker de 2,6 KB criado na `main`: #14 e #41 abertas; Concluído: #11, #12, #10, #13, #17, #16, #22, #33, prova de retomada | tracker de 610 KB do motor (360 commits): bloco `fila-campanhas` (MOTOR-9-01 "bloqueada"), campanhas CRU, histórico | estado vivo único; nenhum item perdido | Base = versão do motor; incorporar as entradas da `main` num bloco "Workflow de entrega (main, 17–23/09)" e mover #11/#12/#14 para Concluído conforme já estão na `main`; deduplicar com UI-11/OBS-12/WEB-14 do bloco `fila-campanhas` (que os marcam "bloqueada", mas #39 e #40 já mergearam em 23/09) | conteúdo lido nos dois lados nesta sessão | `grep -c '<!-- fila-campanhas-start -->'` = 1; IDs únicos | D5: resolver só na máquina do usuário (arquivo tem edições locais); exige reler UI-11-01 e OBS-12-01 (estão desatualizados) |

Resoluções globais "ours"/"theirs" não servem: itens 1 e 9 exigem união; 4 e 5 são `main`; 2, 3,
6, 7 são motor; 8 é `main`.

## 5. Interações de comportamento que o git não detecta

### 5.1 Seis arquivos de código auto-mesclados (verificados na árvore simulada)

| Arquivo | Hunks da `main` | Onde caem no motor | Verificação |
|---|---|---|---|
| `src/builder/engine.py` | import `operation_scope`; método `_operation_scope`; envelopes em `build`, `incremental_build`, `process_single` | os três métodos e `_sleep_guard` existem no motor (linhas 1759–2193 da ponta); `failed_entries` existe (`1746`) | compila; `_operation_scope` é método, não `def` de nível superior, logo o guarda `engine-facade-guard.js` (conta `^def `) não bloqueia; `_emit` só chama `logging.getLogger("...").info`, sem configuração vira no-op: scripts headless do motor (`build_course.py`, `reprocess_assignments.py`) não passam a gravar arquivo |
| `src/ui/app.py` | 4 funções puras de progresso, `_set_progress_paused` em 8 pontos, remoção de `_tick_fake_indeterminate` | regiões distintas de `_build_options_from_config` (#64) e do restante do motor | compila; 40 testes direcionados da `main` passam sobre o código do motor (`test_ui_queue_dashboard.py` inclui asserts de texto-fonte sobre `app.py`/`dialogs.py`) |
| `src/ui/dialogs.py` | `SettingsDialog` (checkbox, `reduce_motion` kwarg, `_apply_reduce_motion_preference` no `_save`), `MoodleCourseSelectDialog._busy` | `SubjectManagerDialog._save` (#63/#65) e os ajustes de #47/#48 ficam em classes diferentes | `Optional` já importado; compila |
| `src/ui/theme.py` | `reduce_motion: False` em `DEFAULTS` | motor mudou 17 linhas noutra região | uma única chave `reduce_motion` no dict mesclado |
| `tests/test_core.py` | `SimpleNamespace` no teste do marker | motor mudou 913 linhas (testes de #47/#48 e outros) | suíte mesclada roda sem `--deselect`; `TestCliResolution` verde |
| `tests/test_ui_queue_dashboard.py` | +151 (progresso, movimento reduzido, HELP) | motor +25 (workspace de curadoria unificado) | 40 direcionados verdes |

### 5.2 Configuração, flags, manifest, fallback, cronograma, chamadas do motor

- `feature_flags`, `FLAG_DEFAULTS` (`assignment_run.py`), `manifest["assignment_run"]`,
  `manifest["options"]`, `NEW_SUBJECT_FEATURE_FLAGS`, pino manual, `temporal_*` e o fallback
  `computed_block_id`: a `main` não toca nenhum desses caminhos (seu diff em `src/` é observabilidade,
  UI de progresso e o wrapper do engine). O invariante "flag desligada é byte-idêntica" não é
  afetado porque os envelopes de observabilidade só emitem log; a saída do build não muda.
- Cronograma, timeline, `content_taxonomy`: só o motor mudou. Sem interação.
- `src/__main__.py`: a `main` chama `configure_local_observability(default_log_dir())` no
  lançamento da UI; `app.py` do motor delega a `src.__main__.main`, logo o comportamento da `main`
  entra pela UI e não pelos scripts. Diretório de log fora do repositório (`%LOCALAPPDATA%` ou
  `~/.gpt-tutor-generator/logs`).
- Contrato arquitetural da CI (`src` fora de `ui` não importa `src.ui`): a árvore mesclada tem
  exatamente a exceção do baseline (`build_workflow.py → src.ui.theme`). Verde.
- Arquivos que a `main` mantém e o motor apagou (§3.2 "cutover"): o merge os remove; nada na
  `main` os importa (o baseline do Ruff cita `tests/test_eval_assignments.py` e
  `tests/test_resolve_unit_block_decoupled.py`, mas contagem menor que o baseline não reprova).

### 5.3 CI `core` sobre a árvore mesclada (simulação na nuvem)

| Verificação | Resultado | Consequência |
|---|---|---|
| Ruff (`select E9,F,B`, `py311`) contra `.github/python-quality-baseline.json` | 155 achados; 61 impressões digitais acima do baseline, 97 achados excedentes: `tests` 50, `src` 32, `scripts` 15. Por código: F401 59, B905 12, B023 11, B007 7, F841 4, B904 1, B008 1, F541 1, F811 1. Em `src/`: 18 fingerprints (`engine.py`, `content_taxonomy.py`, `lifecycle_ops.py`, `file_map.py`, `motor/disambiguator.py`, `motor/llm_vote.py`, `resolver_apply.py`, `sources/moodle.py`, `moodle_sync.py`, `text/stopwords.py`, `timeline/{block_identity,card_block,index,unit_matcher}.py`, `ui/codes_panel.py`, `utils/pdf_markdown.py`) | **`core` reprova** até regerar o baseline ou corrigir; lista completa no anexo A |
| Mesmo Ruff com `py38` (config da `main`) | 55 fingerprints excedentes, incluindo 5 `invalid-syntax` em `tests/test_resolver_wiring.py` | confirma D2: `py311` |
| Contrato arquitetural | 1 violação = baseline | verde |
| Cobertura (Linux, sem `tkinter`, sem tutores) | 84,19 % (baseline Linux 79,62 %) | indicativo; a CI mede em ubuntu com `tkinter` |
| Suíte completa (§5.4) | mesmo conjunto de falhas da ponta do motor | ver abaixo |

### 5.4 Suíte na nuvem (Linux) — ponta do motor × árvore mesclada

| | motor `76e4357b` | mesclada `5e7805a5` |
|---|---|---|
| passed | 2347 | 2372 (+25: 21 funções novas da `main` e o teste antes deselecionado) |
| failed | 26 | 26 (conjunto idêntico) |
| skipped | 30 | 30 |
| deselected | 1 (`test_marker_cli_prefers_project_venv`) | 0 (fix da `main` dispensa o deselect) |
| erros de coleta | 2 (`test_assessment_label_and_plan_section.py`, `test_codes_panel_label.py`, sem `tkinter`) | 2 (os mesmos) |
| tempo | 26,6 s | 46,3 s (com `--cov`) |

As 26 falhas são as do piloto 2 de 24/09 (§3 do handoff do piloto: `google-genai` 1, `robocopy`
1, caminho `C:\` 18 em `test_moodle_structure.py`/`test_moodle_sync.py`, barra invertida 2, mock
de `tkinter` em `test_reprocess_flags.py` 1) mais os 3 testes de `tests/test_subject_dialog_save.py`
(#63/#65; dependem de `tkinter` real e do vazamento #69). Nenhuma delas é atribuível ao merge.
Direcionados sobre a árvore mesclada: `test_observability.py`, `test_verify_python_quality.py`,
`test_ui_queue_dashboard.py`, `test_core.py::TestCliResolution` → 40 passed. Os testes de
#63/#65 (`test_subject_dialog_save.py`, `test_new_subject_d9_default.py`) e o de #50 só rodam com
`tkinter`: ficam para a máquina do usuário (referência Windows da PR: 2443 passed, 4 skipped, 1
falha preexistente do golden do FR).

### 5.5 Escopo da PR #9 além da descrição

A descrição cobre #47, #48, #50, #63–#65 e as medições de 21–24/09. O branch também carrega: #49
(`410592d8`), o cutover do funil legado (`df862033`), a remoção do DeepTutor (`fd0747a0`), as
consolidações A1/A2/B, a identidade estável de bloco, o registro `assignment_run`, a régua v2, ~1980
arquivos de harness (um só JSON, `wp1_inventario_matriz_22-09.json`, tem 301 mil linhas), o guia da
nuvem e os guardas em `scripts/hooks/*.js`. Proposta de revisão em grupos, sem reescrever a PR:

1. `src/` (96 arquivos): revisar por módulo com o handoff e o tracker como evidência de Gate 2
   já dado por commit (#47, #48, #49, #50, #63–#65 tiveram revisão Astra registrada).
2. `tests/` (226) e `scripts/` (53): conferir que a suíte é a fonte de aceite; sem revisão
   linha a linha.
3. `docs/reports/_harness-*` e `tests/_golden`: aceitar como dado (derivação dos números
   publicados; `.gitignore` do motor versiona logs de harness por decisão).
4. `.mex/`, `.workflow/`, `docs/plans|specs`: já propagados em parte; revisar só o resíduo de §3.3.
Atualizar o corpo da PR #9 para listar a #49 e esses grupos (D8).

## 6. Estratégia de integração

| Estratégia | Como | Prós | Contras | Veredito |
|---|---|---|---|---|
| A. Atualizar o branch com a `main` por merge commit, preparado em branch temporária e publicado por fast-forward | branch `integracao/2026-09-xx-main-no-motor` criada da ponta do motor; `git merge --no-ff origin/main`; resolver os 9 conflitos (§4); regerar baseline do Ruff; validar (§8); `git push origin integracao/…:feat/motor-atribuicao` (fast-forward, sem force) | preserva os 1112 commits e as referências de SHA em issues/tracker; satisfaz "branch atualizada" e faz a CI `core` rodar na PR #9; um único ponto de resolução; não exige mexer no worktree sujo do usuário (o branch da PR fica em outro worktree/clone) | um merge commit a mais no branch; a resolução de `pendencias.md` precisa do estado local | **recomendada** |
| B. Branch de integração a partir da `main`, com merge do motor, nova PR | `git checkout -b integracao main; git merge feat/motor-atribuicao`; nova PR; fechar #9 | isola o branch do motor | mesmos 9 conflitos; perde a PR #9 (histórico, comentários, referência no tracker/issues); a proteção da `main` exige o branch atualizado de qualquer forma; duas PRs para reconciliar | alternativa se o usuário não quiser tocar `feat/motor-atribuicao` |
| C. Rebase ou cherry-picks do motor sobre a `main` | — | — | branch publicado com 1112 commits; proibido pelo guia (§3); cherry-picks isolados quebram dependências (ex.: #48 depende de #47; #65 de #63/#64; cutover de consolidações) | descartada |
| D. Cherry-pick das 3 entregas da `main` para o motor sem merge | — | — | não atualiza a PR (continua `dirty`); duplica commits; a `main` continua sem o motor | descartada |
| E. Squash ao mergear a PR #9 | — | árvore da `main` simples | apaga SHAs citados em #47–#65, tracker, handoffs, harness (`aceite_*`), e a proveniência dos dados | descartada; merge commit (D7) |

Dependências e riscos da estratégia A: (i) D4 antes, para o merge não trazer o token ao branch
(se a higiene ficar depois, o branch integrado passa a conter o arquivo até o próximo merge);
(ii) `pendencias.md` local commitado ou guardado; (iii) baseline do Ruff regerado no commit do merge
(sem isso a PR fica vermelha e "não mergear" vira permanente); (iv) replay/zero-diff locais antes
do Gate 2 (o merge não altera o motor, mas o Gate 2 da integração exige a prova).

## 7. Sequência de resolução (executável, para aprovação)

Pré-condições: decisões D1–D5 e D7 tomadas; máquina do usuário (tutores, `tkinter`, Windows).

1. **Local, no worktree do usuário**: `git status --short`; commitar a continuação da #50 (Gate 2
   pendente) ou `git stash push -m "50-continuacao"`; commitar ou guardar as edições do tracker.
   Registrar o SHA resultante.
2. **Higiene na `main` (PR pequena, separada)**: `git rm --cached moddle/.m365_token.json
   .superpowers/brainstorm -r motion-audits/…html`; revogar o refresh token no M365; commitar com o
   hook; PR para a `main`; merge. Reescrita de histórico é decisão à parte (D4).
3. **Preparar o merge** (novo worktree ou clone limpo; nunca `git add -A`):
   `git fetch origin main feat/motor-atribuicao` → `git switch -c integracao/2026-09-xx-main-no-motor
   origin/feat/motor-atribuicao` → `git merge --no-ff origin/main`.
4. **Resolver os 9 conflitos** conforme §4: `git checkout --theirs` para itens 2, 3, 6, 7
   (motor), `--ours` para 4, 5, 8 (`main`), edição manual para 1 e 9; `git diff --check`.
5. **Regerar o baseline do Ruff** (`.github/python-quality-baseline.json`, chave `ruff`) sobre a
   árvore integrada com a mesma função de impressão digital de `scripts/verify_python_quality.py`;
   manter `coverage_percent` e `architecture`. Registrar no commit o motivo (baseline de 18/09
   anterior ao motor). Alternativa D3.
6. **Validar** (§8, passos 1–4) e só então `git commit` do merge (mensagem: "merge(main): integra
   #30/#39/#40/#62 em feat/motor-atribuicao; resolve 9 conflitos; regera baseline do Ruff").
7. **Publicar**: `git push origin integracao/…:feat/motor-atribuicao` (fast-forward; se recusar,
   parar: alguém avançou o branch). A PR #9 sai de `dirty`, a CI `core` roda. Atualizar o corpo da
   PR (#49, grupos de revisão, remover "Não mergear" quando o Gate 2 for dado).
8. **Gate 2 da integração** e merge da PR #9 na `main` por merge commit. Depois: fechar #63/#64/#65
   (texto da PR) e decidir #47/#48/#49/#50 (D10); atualizar `sessao-nuvem.md` §3 (regra de base),
   `.mex/ROUTER.md`, `docs/Overview-Sistema.html` se a arquitetura publicada mudar; tracker.
9. **Reaplicar o trabalho local** (passo 1) sobre o branch integrado; Gate 2 próprio; PR.

## 8. Validação planejada (definir; sem replay nesta sessão)

| Etapa | O quê | Onde | Já existe |
|---|---|---|---|
| 1. Baselines | `main` `77a043f5`: check `core` verde (PRs #39/#40/#62 reportaram `core SUCCESS`; conferir no último push). Motor `76e4357b`: Windows 2443 passed / 4 skipped / 1 falha preexistente (golden FR); Linux nuvem 26 F / 2347 P / 30 S / 2 E (esta sessão) | GitHub; máquina do usuário; este relatório | sim (PR #9, comentário da #65, piloto 2, §5.4) |
| 2. Preservação dos dois lados | `main`: `tests/test_observability.py`, `tests/test_ui_queue_dashboard.py`, `tests/test_verify_python_quality.py`, `tests/test_core.py::TestCliResolution` → 40 passed na simulação; repetir com `tkinter` no Windows. Motor: suíte completa com o mesmo conjunto de falhas ou menor; nenhum teste do motor some (2347 → 2372, só acréscimos da `main` e o teste antes deselecionado) | nuvem (feito) + Windows | parcial |
| 3. #63/#64/#65 | `tests/test_subject_dialog_save.py` (3), `tests/test_new_subject_d9_default.py`, `tests/test_assignment_run_record.py`, `tests/test_reprocess_flags.py`; reprodutor isolado `c1-3/waa_iso_d9_fluxo_real_23-09.py` casos 1–3 (flags preservadas; D9 1 chamada; `assignment_run` gravado) | Windows (`tkinter`, APPDATA temporário) | sim (23/09), repetir sobre a árvore integrada |
| 4. Pinos, D9 e recursos opcionais | pino manual vence (`test_temporal_block_wire.py`, `test_persist_gate.py`), D9 só grava `temporal_*`, votador/vocabulário/rede desligados com D9 ligado (`test_new_subject_d9_default.py` inclui ausência de rede), camada opcional não derruba regeneração | suíte | sim |
| 5. Replay integral dos três eixos | `c1-3/preservacao_base_v2_65_23-09.py` (7 cursos, 350 materiais, régua v2 congelada, mesma configuração efetiva) sobre a árvore integrada: captura idêntica à congelada, zero divergências por ID e por curso; `replay_bloco_21-09` → `replay_unidade_21-09` se a captura divergir. Como a `main` não toca o motor, divergência aqui é sintoma de erro de merge, não de regra: diagnosticar, não compensar | máquina do usuário (tutores, `.frzero/`) | referência de 23/09 |
| 6. Zero-diff | `docs/reports/_harness-2026-09-04/c1-3/zero_diff.py --check` nos 8 tutores | máquina do usuário | referência das consolidações |
| 7. CI | push do branch integrado → `core` (suíte + cobertura ≥ baseline por plataforma + Ruff + arquitetura) e `validate-timeline` | GitHub | — |
| 8. Classificação de falhas | preexistente = está na lista de §5.4 ou no golden FR; regressão = falha nova ausente nos dois baselines; ambiente = `tkinter`, caminho Windows, `robocopy`, `google-genai` (#68/#69) | — | — |

Não reexecutar W-Z, W-AA nem o piloto externo. Não ajustar gold, scorers, régua ou defaults. Se a
simulação de merge revelar divergência de decisão do motor, diagnosticar (§8.5) e parar.

## 9. Decisões pendentes do usuário

- **D1** Estratégia: A (recomendada) ou B.
- **D2** `pyproject.toml`: `target-version = "py311"` (recomendado; `py38` reprova a sintaxe do
  motor) e se `requires-python` sobe para `>=3.11` (coerente com a CI e com o README da `main`).
- **D3** Ratchet do Ruff: regerar o baseline no commit do merge (recomendado; honra "bloquear
  erros novos sem limpar o legado") ou corrigir os 97 achados antes (toca 18 arquivos de `src/` do
  motor → exige zero-diff; vira issue própria).
- **D4** Token e arquivos ignorados versionados na `main`: remover em PR de higiene antes da
  integração (recomendado) e revogar o refresh token; reescrever histórico é decisão separada.
- **D5** `docs/reports/pendencias.md`: resolver localmente com a versão do motor como base e as
  entradas da `main` incorporadas; atualizar UI-11-01 e OBS-12-01, que ainda dizem "bloqueada".
- **D6** `.workflow/pendencias_workflow.md`: manter o parágrafo da `main` sobre Context Mode e
  plugins (recomendado).
- **D7** Método de merge da PR #9: merge commit (recomendado) versus squash.
- **D8** Corpo da PR #9: incluir a #49 e os grupos de revisão de §5.5; manter "não mergear" até o
  Gate 2 da integração.
- **D9** Continuação local da #50: commitar antes da integração (entra na PR #9) ou depois (PR
  própria). Recomendado: antes, após conferir o diff sobre `36b00ab9`.
- **D10** Pós-merge: encerrar `feat/motor-atribuicao` e abrir branches por issue a partir da
  `main` (exige atualizar `sessao-nuvem.md` §3); fechar #47/#48/#49/#50 além de #63/#64/#65.
- **D11** Versionar os 4 artefatos de 17/09 (`diagnostico_subunidade_17-09.*`,
  `astra_revisao_regime2_17-09.md`): scripts versionados dependem deles; a decisão de 23/09 os
  deixou fora.

## 10. Handoff (campos da §9 do guia da nuvem)

- **Pedido**: MOTOR-9-01, diagnóstico de integração da PR #9 e plano; sem resolver conflitos,
  sem código, sem commit no branch da PR.
- **Issue/PR**: PR #9 (`Refs #9`); issues rastreadas #47, #48, #49, #50, #63, #64, #65; entregas da
  `main` #39, #40, #62, #30 (CI).
- **Base e SHA**: `feat/motor-atribuicao` @ `76e4357b8ecf9c1ca92762bd58d76b622ad0ad54`.
- **Branch**: `nuvem/2026-09-24-motor-9-01-plano-integracao`.
- **Arquivos mudados**: só este relatório.
- **Testes** (Linux nuvem, `TUTOR_COURSES_DIR` inexistente, `-p no:cacheprovider
  --continue-on-collection-errors`): ponta do motor 26 failed / 2347 passed / 30 skipped / 1
  deselected / 2 errors; árvore mesclada (com `--cov=src`) 26 failed / 2372 passed / 30 skipped /
  2 errors; conjuntos de falha idênticos (todos preexistentes: §5.4). Direcionados da `main` sobre
  a árvore mesclada: 40 passed. Ruff/arquitetura/cobertura: §5.3.
- **Não validado**: Windows; `tkinter`; testes de #50/#63/#65 que exigem `tkinter`; replay integral;
  zero-diff; reprodutor D9; CI real no GitHub; conteúdo local do worktree do usuário.
- **Ambiente**: hook do pre-commit instalado com `chmod +x`; clone desraso; HEAD local estava atrás
  da ponta do motor.
- **Delta proposto ao tracker** (não aplicado): no bloco `fila-campanhas`, MOTOR-9-01 → estado
  "concluída tecnicamente; Gate 1 do plano pendente", evidência este relatório; novas tarefas:
  MOTOR-9-02 [T2] preparar merge da `main` no motor em branch temporária, resolver 9 conflitos,
  regerar baseline do Ruff (dep: D1–D5, D7; §7 passos 3–5); MOTOR-9-03 [T2] validação local
  (§8 passos 2–6; dep: MOTOR-9-02); MOTOR-9-04 [T1] higiene da `main` (token e arquivos ignorados
  versionados; independente); MOTOR-9-05 [T1] Gate 2, fast-forward, CI, merge da PR #9, fechamento
  de issues, atualização de `sessao-nuvem.md` §3/ROUTER/Overview (dep: MOTOR-9-03). Atualizar
  UI-11-01 e OBS-12-01 para "concluída" (PRs #40 e #39 mergeadas em 23/09) e WEB-14-01 (PR #62
  mergeada). Fora deste delta: CRU-02..05.
- **Decisões que ficam para o usuário**: D1–D11 (§9).

## Anexo A — impressões digitais do Ruff acima do baseline (árvore mesclada, `py311`)

Formato `arquivo|código: excesso`. `src/`: `engine.py|F401: 3`, `extraction/content_taxonomy.py|F401: 5`,
`ops/lifecycle_ops.py|F401: 1`, `routing/file_map.py|F401: 2`, `routing/motor/disambiguator.py|F401: 1`,
`routing/motor/llm_vote.py|B904: 1`, `routing/resolver_apply.py|B007: 4`, `sources/moodle.py|F401: 1`,
`sources/moodle.py|F841: 1`, `sources/moodle_sync.py|F401: 2`, `text/stopwords.py|F401: 1`,
`timeline/block_identity.py|F401: 1`, `timeline/card_block.py|F401: 1`, `timeline/index.py|B905`,
`timeline/unit_matcher.py|B905`, `ui/codes_panel.py|B905` (12 B905 somados), `utils/pdf_markdown.py|B023: 2`,
`utils/pdf_markdown.py|F841: 1`. `scripts/`: `audit_taxonomy_losses.py|B023: 2`, `build_course.py|B023: 5`,
`dedup_manifest.py|B007: 3`, `erros_motor_nu.py|B023: 2`, `motor_puro.py|F401: 2`, `site_snapshot.py|F401: 1`.
`tests/` (50 achados, quase todos F401 em 35 arquivos; além de `test_eval_code_block_gold.py|F541`,
`test_motor_anchor_engine.py|F811`, `test_persist_gate.py|F841`, `test_subject_dialog_save.py|B008`,
`test_unit_matcher.py|F841`). Com `py38`: 55 fingerprints, incluindo `tests/test_resolver_wiring.py|invalid-syntax: 5`.

## Anexo B — arquivos que o merge remove ou adiciona sem conflito

Removidos (apagados no motor, intocados na `main`): `scripts/{backfill_source_section,eval_assignments,eval_cards,retag_manifest}.py`,
`src/builder/artifacts/deeptutor.py`, `tests/{test_card_block_assignment,test_date_prefix_signal,test_ddmm_timeline_boost,test_eval_assignments,test_eval_cards,test_resolve_unit_block_band,test_resolve_unit_block_decoupled,test_resolve_unit_block_tags,test_retag_manifest}.py`,
`docs/eval/metodos-file-block.csv`, `docs/sistema-atribuicao.html`, `.claude/settings.local.json`, `.token-savior-cache.json`.
Adicionados pela `main` ao motor: `src/observability.py`, `scripts/verify_python_quality.py`, `.github/workflows/python-quality.yml`,
`.github/python-quality-baseline.json`, `tests/{test_observability,test_verify_python_quality}.py`, `docs/reports/2026-09-19-contrato-qualidade-c6.md`
e, sem que se queira, `moddle/.m365_token.json`, `.superpowers/brainstorm/**`, `motion-audits/*.html`.
