# Handoff — Plano B FECHADO, campanha encerrada (2026-08-05)

**Branch:** `feat/motor-atribuicao` · head `84d25b0` · **Este é o handoff de fechamento** do Plano B
(sucede `docs/reports/Feitos/2026-08-05-handoff-planob-pronto.md`, que era o handoff de partida —
"7 tasks, NENHUMA executada"). Agora: 7/7 executadas, review final READY TO MERGE, campanha
encerrada.

## §1 Estado

1. **Plano B: ENTREGUE.** 7/7 tasks, 19/19 dívidas mecânicas mapeadas na investigação + 2a
   (stopword-fantasma) + 2b (gate `_p_ambig`) — todas pagas. Commits `d3cd0fa..84d25b0` na branch
   (+ `Metodos-Formais-Tutor@235e8a7` para o T19, único commit em repo-tutor do plano inteiro).
2. **Régua**: 7 probes byte-idênticos em todos os gates ao longo das 7 tasks, exceto as 2 mudanças
   de comportamento DELIBERADAS e medidas (Task 1: cw TCC 1→0; Task 4: 4 atribuições TCC movidas
   pra confiança honesta). Suite **1823 → 1858 passed / 4 skipped / 0 failed**.
3. **Review final whole-branch (fable):** READY TO MERGE YES, pós fix-wave. Ver §3.
4. **Rollout MF+SO segue como estava** (read-only neste plano, por constraint global) — TCC/ES2
   OFF. Nenhum reprocess real, nenhum flip de flag.
5. **Achado paralelo da sessão** (fora do escopo do plano, autorizado pelo user): investigação
   completa da perda da unidade-03 do MF — causa-raiz FATO, promovida a
   `docs/reports/2026-08-05-unit-sources-investigacao.md`. Vira a PRÓXIMA prioridade [CODE] em
   `pendencias.md`. Ver §4.

## §2 O que mudou, por task

| # | Task | Commits | O quê |
|---|------|---------|-------|
| 1 | T12 stopwords PT | `83540ce` (+ base `d3cd0fa`) | 11 palavras-função PT em `_GENERIC_STEMS` (`disambiguator.py:22-26`) — fecha cw TCC 1→0, acc 84.2% intacta (número EXATO da medição empírica, lista NÃO estendida). |
| 2 | Batch higiene (10 itens) | `e810303`, `1d6f52b`, `353b1c9`, `0ca0250` | T9a/T2b (apply/context), T8/T9/T10/T7a (llm_vote — mkdir, fold, casefold, memoize md5), T16/T14/T13 (providers — hoist stems, gate due-vazio, filtro fileurl), T11 (probe fase3 sem truncamento). Régua byte-idêntica (higiene pura). |
| 3 | T3 sonda fase3 janela-1 | `5c2b862`, `7b6539e` | `fase3_prova_LLM_MF.py` só conta rows elegíveis ao voto (`flag and len(window)>1) or série`), alinhado ao gate real `anchor_engine.py:57-58`. Lift +3/0 API MANTIDO — o viés era só de contagem da sonda. |
| 4 | Fix 2b | `2c3fe45`, `3b8267f` | `content_taxonomy.py:1224` passa a ler `_p_ambig` + exigir `p_conf>0` — palpite cego nunca mais vira atribuição dura. MUDA atribuições: 4 TCC medidas pré/pós, régua corpus-wide 4/136 (só as 4 conhecidas; resto byte-idêntico). Achado extra: `persist=True` do `retag_manifest.retag()` grava `manifest.json` mesmo em "leitura" — ver §4. |
| 5 | T17 D-H por kind | `4190abb`, `b5af54f` | `due_window.py`: filtro `topics` (opcional) → `kind` (required), `_NON_CONTENT_KINDS={assessment,review}` derivado dos 4 índices reais. Mata pré-requisito artificial de curso novo. Fix round: medição PRÉ/PÓS direta em TCC/SO confirmou zero deltas (provider due-window estruturalmente adormecido nos dois, independente do fix). |
| 6 | T4b lock do voter | `dfee9c5`, `7467187`, `793952b` | Lock cross-processo por sentinela `O_EXCL` em `_persist`/`prune` (`llm_vote.py`). 3 rounds de hardening: deadline+sleep em todo `continue` órfão (Windows dono-vivo-lento), takeover single-winner via `rename` atômico, guard `SidecarLockTimeout` em `vote()` E `prune()` (prune roda ANTES do apply na mesma rodada D9 — timeout ali abortaria a rodada inteira antes de qualquer material). |
| 7 | Infra final | `500a116`, `963924e`, `481697d`, `a29ca57`, `7c750f3`, `896592c` | T15 (imports no topo sem ciclo), T1b (`_MODEL_MIGRATIONS` como tabela), **T18** (reprocess lê `SubjectStore`/injeta `feature_flags` vivas — mata a armadilha `--flags` obrigatório), T7b (e2e da ordem refresh→resolve→attach), **T19** (`*.bak` no `.gitignore` gerado + destrack dos 5 `.bak` do MF, autorizado pelo user), read_only probe (`retag_manifest`/`rebuild_timeline` em modo leitura ganham `persist=False`). |

## §3 Review final — veredito + fix wave

**Whole-branch (fable, `d3cd0fa..896592c`, 20 commits): READY TO MERGE YES.**

- **1 Important** — `os.remove(stale_name)` pós-rename do takeover do lock era a última saída sem
  proteção (`OSError` transiente Windows AV/indexer escapava do contextmanager; os guards de
  `vote()`/`prune()` só capturam `SidecarLockTimeout`, não fechavam esse invariante).
- **3 minors** — `skipif(win32)` no teste de dono-vivo (rename de fd aberto só sucede em POSIX);
  `window_provider._block_topic_stems` `stems_by_block[id(b)]` → `.get(id(b), set())` (achado
  emprestado da mesma área do lock, via `AnchorEngine`); docstring em `_persist()` documentando o
  invariante "chamador segura `self._lock`".
- **Fix wave**: dispatched ao implementer do lock, commit `84d25b0` — 4/4 ADDRESSED, re-review
  limpo. **Campanha ENCERRADA.**
- Cross-task: memoize+lock não interagem; gate 2b e filtro kind ficam em camadas disjuntas; scripts
  `persist=False` nunca instanciam `LlmVoter`. Aritmética da suite (1823→1858) fecha exata
  cross-reports. Triage do deferred: tudo ride pra próxima campanha, exceto o fail-open de kinds
  admin (Task 5), promovido a item BLOQUEANTE do checklist pré-rollout ES2/curso novo (ver
  `pendencias.md`).

## §4 Achados da sessão (fora do escopo do plano)

- **u3 causa-raiz — FATO, não hipótese.** `scripts/reprocess_assignments.py:81` monta
  `RepoBuilder` sem `subject_profile` → `teaching_plan=""` → `content_taxonomy["units"]=[]`
  (`file_map.py:1500-1501`) → `assign_units_positional` recusa por `m<2` (`unit_matcher.py:66-67`)
  → cai no scorer legado com o índice de 2 unidades derivado do `COURSE_MAP.md`
  (`file_map.py:1628`), que a mesma rodada RE-ESCREVE (`pedagogical_regeneration.py:402`) — loop
  auto-perpetuante. Matcher **inocentado**: com as 3 unidades reais, bloco-16 do MF cai em
  unidade-03 (argmax 4, experimento real). +2 vazamentos idênticos: `app.py:2391` (unprocess) e
  `curator_studio.py:1293/1303` (reject). Investigação completa promovida:
  `docs/reports/2026-08-05-unit-sources-investigacao.md`. Vira campanha própria — ver §5.
- **`persist=True` write-trap fechado para os scripts read-only.** Achado na Task 4
  (`_build_file_map_timeline_context_from_course` grava `manifest.json` — migração
  `manual_timeline_block_id` bloco-NN→uuid — mesmo em contexto de "leitura", não só o bump de
  `last_seen` já catalogado). A Task 7 fechou o buraco nos dois callers de leitura
  (`retag_manifest`/`rebuild_timeline` agora passam `persist=False` explícito). O `retag()` de
  produção (mutação intencional) continua `persist=True` por design — o fix é só nos caminhos que
  se anunciavam como read-only e não eram.
- **ES2-Tutor sujo.** 45 arquivos de sujeira pré-existente (mtimes 01/07 e 04/08, não causada por
  esta sessão) — achado incidental da Task 5, registrado em `pendencias.md` como bloqueio
  USER-SIDE antes do rollout ES2.
- **Grafo de conhecimento entregue.** `knowledge_graph.py` (stdlib-only, paralelo ao plano, decisão
  do user) produziu `mf_knowledge_graph.html` — 90 nós/78 arestas/1 órfão ("plano"), MF confirmado
  intocado, **12 divergências temporal≠computed visíveis**. Foi essa inspeção visual que achou a
  perda da u3 (§4 acima) — o grafo funcionou como ferramenta de auditoria, não só visualização.
  Integração em `scripts/` ainda pendente (item CODE em `pendencias.md`).

## §5 Fila pós-plano (ordem)

1. **Campanha u3/subject_profile** — wiring fix nos 3 sites (`reprocess_assignments.py:81`,
   `app.py:2391`, `curator_studio.py:1293/1303`) via `_resolve_subject_profile` de
   `retag_manifest.py:30-41`; MUDA atribuições → gold obrigatório; depois (não antes) merge das 2
   fontes de unidade.
2. **Integração do grafo de conhecimento** — mover `knowledge_graph.py` pra `scripts/` +
   melhorias decididas (espinha temporal bloco-01→NN, unidades derivadas do plano de ensino).
3. **Brainstorms represados** — bibliografia (decisão 2026-07-22); "silver gold" via Moodle (weak
   supervision, sem scraper — análise preliminar no handoff roteiro §1.3).
4. **Rollout IA/ES2** — gold user-side + pré-requisitos (IA: gold trilha 4, stash parcial, janela
   SARC 24-29/06, desligar flag legado no flip; ES2: gold de 21/06 + limpar a sujeira do §4 + medir
   pré-flip).
5. **TCC re-flip** — **agora desbloqueado**: PB Task 1 (cw TCC zerado) + Task 4 (funil medido) são
   exatamente os dois pré-requisitos que o handoff de partida citava como condição pra
   re-autorizar. Re-rodar o fluxo de flip com gate (cache de 16 votos untracked preservado no
   TCC-Tutor).
6. **Cutover** — último de todos (5 flags ON estáveis; mapa de deleção do funil legado já travado
   em `pendencias.md`, seção "CODE — limpeza/dead-code").

## §6 Armadilha morta (e a que sobrevive)

**T18 matou** a obrigação de passar `--flags use_anchor_engine,use_llm_voter` manualmente em todo
reprocess headless do MF/SO — `reprocess_assignments.py` agora lê `SubjectStore` e injeta
`feature_flags` vivas do perfil (CLI `--flags` continua vencendo se passado; sem perfil, mesmo
comportamento de antes). Essa era a armadilha operacional nomeada no handoff de rollout
(`docs/reports/2026-08-04-handoff-rollout-trilha1.md:83`).

**O que T18 NÃO matou** (escopo era intencionalmente estreito, "too narrow" — texto da própria
investigação u3): o `subject_profile` **ainda não é injetado** no mesmo call site. Flags vivas
resolvem a durabilidade de config; a perda da unidade-03 do MF é um problema diferente — falta de
`teaching_plan`, não de `feature_flags`. É exatamente a campanha u3 do §5 item 1 que fecha essa
lacuna (e, por reaproveitar a mesma função `_resolve_subject_profile`, subsome o T18 se algum dia
a mesma trilha for revisitada — mas T18 em si já está fechado e não depende da campanha u3 para
funcionar).
