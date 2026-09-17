# Handoff — roteiro pós-rollout (decisão user 2026-08-04)

**Data:** 2026-08-04 · **Branch:** `feat/motor-atribuicao` (head no push desta sessão) ·
**Par deste handoff:** `docs/reports/2026-08-04-handoff-rollout-trilha1.md` (estado por curso,
avisos operacionais, infra) — LER OS DOIS juntos; este documenta a SEQUÊNCIA decidida, aquele o
estado.

## §1 Sequência decidida pelo user (ordem obrigatória)

1. **(1) Ruling `lista2` + flip SO** — user decide o gold; com hard=0, flip SO segue o fluxo
   provado (Task 6 do plano da trilha 1: snapshot → flip → reprocess `--flags` → gate estrutural
   → fase2_SO idêntica + audit pós hard=0 → commits + registro).
2. **(2) Plano B — dívidas do motor + investigações**, nesta ordem de dependência:
   a. **Investigação do cw TCC** (`aula-01`: voter endossou com confiança resposta de funil já
      errada — computado bloco-02 vs gold bloco-01, provider=topic; 1º caso real de
      confiança-indevida do flip). Bloqueia o retry do flip TCC.
   b. **Idempotência do funil-base** (4 entries TCC recomputam `auto_tags bloco:` a cada
      reprocess, flags-OFF reproduz; converge com o minor do line-count variável dos .md —
      ambos apontam não-determinismo do pipeline; investigar juntos).
   c. **Defer-F5 do review F4**: T1b combo UI stale (migração em `AppConfig._load`) · T2b
      `load_repo_artifact` engole exceção (1 logger.debug) · T3 pend-perpétua janela-1 no probe
      fase3 · T4b lock do voter por-processo · T7a double-md5 · T7b e2e do gate via
      `regenerate_pedagogical_files` · T9a ref `None` no filtro do health · herdados F3
      (parent-dir `save_material_curation`, fold acento `source_section`, `match_window_ref`
      strip/casefold, truncamento dry-run, stopwords PT P4).
   d. **Minors-batch F5b**: filtro `fileurl` em `extract_file_dues` · gate due-vazio · imports
      function-local · hoist `mine=_stems()` · higiene `manifest.json.bak` tracked no MF-Tutor.
   e. **topics→kind no filtro D-H** — SÓ com re-medição completa (pré-requisito de flag-ON em
      curso novo sem topics).
   f. Estrutural do review final: `reprocess_assignments.py` ler `subjects.json` (mata a
      armadilha do `--flags` manual).
3. **SÓ DEPOIS: brainstorms** — (i) bibliografia (trilha 3, decisão user 2026-07-22);
   (ii) **"silver gold" via Moodle** (weak supervision; análise preliminar na conversa de
   2026-08-04: acurácia alta NÃO dispensa gold [vira sentinela de regressão]; Moodle-derived
   labels são circulares pros providers que leem Moodle → válidos só pra validar providers de
   CONTEÚDO; discordância silver×motor = fila de revisão humana; scraper desnecessário —
   `MoodleClient` API já roda headless).

Rollout IA/ES2 e cutover: aguardam gold user-side (trilha 4) e flags estáveis — fora desta
sequência, ver handoff-par §4.

## §2 Evidência pronta para o ruling do `lista2` (item 1)

- Gold SO: `lista2,lista2.pdf,true=bloco-17,computed=bloco-11,temporal=bloco-11,`
  `pair_key=lista-exercicios-p2,block-direct,clean,scorable=yes,discriminante=yes`.
- Timeline SO: bloco-17 = assessment 25/06 (P2, topics vazio); bloco-16 = office_hours 23/06;
  bloco-18 = assessment 30/06 (substituição).
- Manifest SO: `lista2` categoria `listas`, funil `bloco:bloco-11`, data_real 2026-03-10
  (postagem antecipada), sem pino.
- Conflito: semântica CONTEÚDO (bloco-11) vs ÉPOCA-DE-USO (bloco-17, preparação da P2). O
  auditor acusa ADMIN_TRUE só porque o TÍTULO "lista2" não casa `ASSESS_TITLE_RE` — o
  `pair_key=lista-exercicios-p2` identifica material de prova que a regex de título não vê.
- Precedentes a favor de manter bloco-17: gold SO já usa semântica de uso (segmentação→bloco-12
  = enunciado TP2); decisão F5b: trabalho = época de entrega.
- **Recomendação registrada (controller):** confirmar gold bloco-17 e ensinar o auditor a
  reconhecer material-de-prova também pelo `pair_key`/nome (ex.: sufixo `-p1`/`-p2`/`-prova`) —
  mudança em script de auditoria (não motor), mesmo precedente do guard-clause `_gold_check` F4
  (alinhar medição ao gold aceito, sem afrouxar piso). Re-rotular para bloco-11 melhoraria a
  acurácia medida — cheiro de re-tuning via gold; evitar sem evidência semântica nova.

## §3 Regras herdadas (seguem valendo — handoff-par §5)

Flag-OFF byte-idêntico + régua completa em mudança de motor · FAIL honesto, proibido re-tuning ·
medição só com hard=0 · D-E nunca chuta · gold só muda com evidência + autorização user · TDD por
task · reprocess headless do MF SEMPRE com `--flags` (armadilha documentada) · SO-Tutor com árvore
suja pré-campanha: snapshot antes de qualquer mexida.

## §4 Comando de partida da próxima sessão

> Leia este handoff + `2026-08-04-handoff-rollout-trilha1.md` + entradas 2026-08-04 do
> pendencias.md. Item 1: apresentar §2 ao user, colher ruling do `lista2`, executar flip SO.
> Item 2: Plano B começa por investigação (2a/2b) ANTES de escrever o plano (writing-plans) —
> dívidas 2c-2f entram como tasks mecânicas no mesmo plano.
