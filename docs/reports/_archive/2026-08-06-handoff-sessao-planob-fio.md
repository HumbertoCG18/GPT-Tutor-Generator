# Handoff — sessão 2026-08-05/06: Plano B entregue + campanha fio (3/4 tasks) + dual-source confirmado

**Branch:** `feat/motor-atribuicao` · head `69c59f1`. Sucede
`docs/reports/2026-08-05-handoff-planob-fechado.md` (fechamento do Plano B). Este handoff cobre a
campanha fio subject_profile que rodou na sequência, na mesma sessão lógica.

## §1 Estado

Plano B: **7/7 ENTREGUE** (commits `d3cd0fa..84d25b0` + `Metodos-Formais-Tutor@235e8a7` para o T19),
review final whole-branch READY TO MERGE, suite 1823 → 1858 passed/4 skipped/0 failed, menu de merge
ABERTO (`new-features`). Campanha fio subject_profile: tasks **1/2/4 ENTREGUES** (commits
`b9cf02f..69c59f1`, suite 1858 → 1869 passed/4 skipped/0 failed), review final **WITH FIXES** — as
correções são exatamente o amendment do registro durável feito nesta sessão (ver COMMIT 2). Task 3
(cura do MF): **BLOCKED → ROLLED_BACK**, MF-Tutor de volta ao snapshot `f83adc9` (hash-verificado,
sha256 dos 5 sidecars gitignored idêntico ao pré-cura). Grafo de conhecimento do projeto entregue
(scratchpad, servido em `localhost:8765`). Motor MF real, medido no gold de 58 casos auditados: gate
determinístico 82.8% (cw 1) / voter 87.9% (cw 0).

## §2 A cadeia de descobertas da sessão (o valor real)

O grafo de conhecimento revelou que a unidade-03 do Plano de Ensino do MF (`u3`) estava ausente do
índice de timeline em produção. Investigação apontou a causa como FATO, não hipótese: o reprocess
headless montava o `RepoBuilder` sem `subject_profile`, então `teaching_plan` chegava vazio e
`content_taxonomy["units"]` ficava `[]`. O fio (`subject_profile` chegando ao `RepoBuilder` via
`SubjectStore.find_by_repo_root`) foi consertado nos 3 sites furados. A verificação pós-fio, porém,
revelou que a perda não era peculiaridade do MF: **4/5 cursos perderam unidades** — TCC 4/4 intacto
(único são); MF 3→2 (falta u03); SO 7→6 (falta a unidade do **meio**, u04-deadlock); ES2 3→2 (falta
u03-testes-de-software); IA 5→3 (faltam u04-raciocínio-sob-incerteza e u05-aprendizado-de-máquina).
Isso motivou prevenção antes de qualquer cura: `UnitsShrinkError` + `verify_units.py` acoplado à
régua + fallback barulhento no lugar do silêncio anterior.

Com a vigia ligada, a cura do MF (Task 3) rodou — e ficou **BLOQUEADA por um empate 4×4**: o plano
de ensino lista "Verificação de Modelos" como pré-visualização (subtópico 1.3.1) dentro da abertura
da Unidade 01, então o enriquecimento de aliases por texto (não por unidade) faz a assinatura da
Unidade 01 absorver tokens da Unidade 03. O DP monotônico global do matcher posicional não avança em
empate — o tie-break prefere ficar na unidade anterior. O recompute em memória da Task 2 tinha dado
`u3 conf=0.6` (vitória limpa) para o mesmo bloco; a produção real, com os insumos reais do disco pós-
reprocess, deu `u2 conf=0.4` (empate 4×4). Essa divergência é **dual-source confirmado nos dois
sentidos**: (a) 3 falsos alarmes de drift na Task 2 (`logicadehoare`/`classes-parte1`/`classes-
parte2`) eram artefato do probe isolado `retag(persist=False)`, que pula `attach_block_summary_fields`
e outras etapas — a produção real reproduziu esses 3 `computed_block_id` byte-a-byte; e (b) 1 falso
positivo no sentido oposto — bloco-16 do MF, que a sonda previu como u3 confiante, virou empate 4×4
inconclusivo assim que rodou pelo pipeline de produção completo. Ou seja: nem toda divergência
sonda-vs-disco é sinal de staleness do disco, e nem toda previsão da sonda se confirma em produção —
os dois caminhos montam assinaturas diferentes e precisam ser unificados antes da próxima cura.
Diante do empate, a decisão foi rollback limpo do MF-Tutor para o snapshot pré-cura, deixando a
investigação de causa-raiz (colisão de rótulo + unificação de fontes) para a próxima campanha.

## §3 Fatos fechados

**0/67 `computed_block_id` mudou no reprocess real** — a pergunta dos 3 drifts aberta desde a Task 2
está FECHADA: o drift observado era artefato da sonda isolada (`retag()`), o disco nunca esteve
stale, e a produção real (`RepoBuilder.incremental_build()` completo) reproduz exatamente o valor
gravado. O fio testado com T18 (reprocess lendo `SubjectStore`/`feature_flags` vivas) **sem
`--flags`** passou no fire test: `[profile]` apareceu no stdout, confirmando que o perfil e as flags
chegam sem a armadilha operacional antiga. O guard `UnitsShrinkError` **nunca disparou** em fluxo
legítimo (o índice do MF continuou com 2 slugs, não caiu para 0/1) — ficou quieto exatamente como
deveria.

## §4 Fila da próxima sessão, EM ORDEM (decisões do user)

1. **VARREDURA de `pendencias.md` com dados reais** (mandato do user: começar por aqui).
2. **Campanha colisão-de-rótulo + unificação das fontes de unidade** (insumo: report promovido no
   amendment desta sessão — consertar o `U+FFFD` do `teaching_plan` do MF em `subjects.json` ANTES).
3. **Cura do SO no mesmo rito**, com as 2 anomalias já registradas (deadlock absorvido no `topic_text`
   do bloco-05; ordem não-monotônica bloco-10=u07/bloco-11=u05/bloco-12=u07).
4. **Inspeção do USER da sujeira ES2 (45 arquivos) / IA (48 arquivos)** antes de qualquer rollout.
5. **TCC re-flip** (destravado).
6. **Rollouts IA/ES2** (gold user-side).
7. **Cutover** (mapa 2026-07-03).
8. **Integração do grafo em `scripts/`** (+ espinha temporal, unidades do plano).
9. **Pós-motor**: brainstorm de bibliografia + Computação Gráfica HTML→PDF sem perda (materiais do
   professor em HTML; Datalab possivelmente não suporta; converter preservando estrutura).

## §5 Armadilhas/notas

- Notação **"fix round N/5"** = round N de um teto de 5, não um checklist a esgotar; "0 open" =
  loop encerrado.
- O hook `code-review-graph` crasha com erro de encoding cp1252 em todo commit — cosmético, engole
  o painel de risco no output; registrado como pendência.
- `preserve_raw` está morto no `reject`: `builder.reject(entry_id, preserve_raw=False)` sempre cai
  no `except TypeError` porque a assinatura atual de `reject` não tem `preserve_raw`
  (`engine.py:2194` / `lifecycle_ops.py:307`) — 2 builders passam por esse caminho no reject.
- O servidor local do grafo (`localhost:8765`) morre junto com a sessão — não persiste entre
  reinícios.
- O menu de merge do Plano B + fio está **aberto**: um único merge de `new-features` cobre os dois
  (nenhuma ação de merge foi tomada nesta sessão).
