# Handoff 2026-09-03 — PONTO DE ENTRADA: campanha SYNC (Moodle -> tutor), depois C1 travessia

Unico handoff vivo. O anterior (`_archive/2026-09-02c-handoff-fase3-medida.md`) fechou a rodada do motor (C0, itens 2-7);
NAO reabrir a fila dele. **Leia nesta ordem:** (1) este arquivo; (2) `pendencias.md` §SEQUENCIA ACORDADA e §GATE DA FASE 3
(numeros); (3) `.mex/context/decisions.md` (as 6 decisoes de 03/09 estao la). Rode `mem-search` para as sessoes de 03/09.

## Leis (inalteradas)
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · gold nao e oraculo (Moodle/SARC sao a verdade
estrutural) · nada regride em regua nenhuma · estrutura estreita, texto decide, estrutura NUNCA sobrepoe decisao confiante
(e NUNCA preempta o voto do LLM — medido 03/09: card antes do voter derrubou a curada 199 -> 187) · nada pushed sem o user ·
`.claude/settings.local.json` intocado · token do Moodle (`moddle/.env`) nunca impresso · [Humberto].

## Estado ao comecar (tudo commitado, NADA pushed)
Gerador `feat/motor-atribuicao`: itens 2-7 do C0 = `fe2c4fb` (3a) · `b802a68` (3b card) · `79fc92a` (secao 0) · `fdf28af` (3c tokens
curtos + holdout CG) · `b1d565a` (ancora como faixa) · `a1bcc25` (casamento por stem) + commits de docs. Tutores: MF `e39e14a`
SO `603d914` IA `ca1f765` ES2 `2212f9f` TCC `b9af3c3` (5 encerrados com estrutura do Moodle no manifest) · CG `19472d1` LR `0e3ab1a`
FR `64990dc` (semestre corrente: SEM os campos; entram na sync). Suite 2277. Copias `.ablacao` dos 5 + CG.
**Reguas (5 golds):** curada 199/200 conf-err 0 · 191/191 · 55/57 · 93/93 · motor+vocab 183/178/53/82 · motor sem vocab
184/168/54/30 · AULA 174/189 (175 sem vocab) · REF 8/10 · holdout CG puro 30/35, curado 34/35 · censo revisar/100 51,7,
votos/100 32,0. Residual flagado em AULA 18,5/100 (meta <= 8 nao batida; balde do item 11).

## Decisoes de 03/09 (detalhe em `decisions.md`)
- Card ordenado age so sem janela ou em decisao ainda flagada DEPOIS do voter; janela-1 do card gateada; banda "media".
- Secao 0 do Moodle = area geral -> apresentacao. Tokens curtos so no retry flagado. Ancora "dd/mm" = faixa da secao.
- Holdout CG (`_harness-2026-09-02/holdout_cg.py <GEN> <COPY> [--curado]`) e regua fixa: puro 30/35, curado 34/35.
- **SYNC (user, 03/09):** modulo removido no Moodle SOME do tutor (flag por curso `sync_prune_removed`, default ligada; desligada =
  fica marcado e fora dos indices); decisao antiga que se moveu por material novo entra na fila como **"mudou, confira"**;
  arquivo alterado (`timemodified` > `posting_date`) re-extrai AUTOMATICO com contagem e cap; links/videos entram como
  entries de referencia (so import; atribuicao e C2); CG = primeira sync como REBUILD LIMPO (ids novos, gold re-chaveado
  por `true_block_uuid`, historico git preservado).
- **Ordem das campanhas (user, 03/09):** materiais de aula -> listas/trabalhos/provas -> bibliografia por ultimo. Logo C3 antes
  de C2. Registrado o contraponto: nos 5 encerrados os 3 eixos ja estao em ~100% na curada; o "100%" que falta e nos cursos
  do semestre (sem gold) e na travessia (IA 9 -> 14/15 medido).

## O que o item 8 mostrou (dry-runs de 03/09; nenhum tutor tocado)
Estrutura identica a 02/09 nos 3. **FR:** mesmos 20 arquivos (nomes originais no repo; o pull grava pelo titulo do modulo) — ids
0/20 mas bytes iguais; faltam 2 videos + cronograma como referencia. **LR:** 3 labs sao `.html` impressos em PDF (casamento por
stem corrigido em `a1bcc25`, 6/6); **Lab 4 (HTTP, 31/08) nunca entrou** — ninguem sincronizou. **CG:** repo veio do EXPORT (37/69
arquivos sem par por nome; ids 14/69); pull da API = 40 arquivos + 15 paginas Moodle + 15 snapshots + 23 videos/indices.
Conclusao: "rebuild" e um caso particular de **sincronizar**; sem sync o tutor envelhece toda semana.

## FILA — CAMPANHA SYNC (1a a executar; 4-6 itens; TDD com os `contents.json`/`sections.json`/`links.json` REAIS dos 3 dry-runs de
   03/09, versionados em `_harness-2026-09-03/pulls/{FR,LR,CG}/`)
S1. ~~**Diff estrutural**~~ FEITO 03/09 (`2491596`): `src/builder/sources/moodle_sync.py::sync_diff` (novos/alterados/sumidos/iguais/links/fora);
    casador UNICO extraido do backfill (`moodle.match_module_entries` + `iter_sections`, byte-identico nos 5 encerrados);
    `scripts/sync_moodle.py <nome|slug> --dry-run` (pull da estrutura em raiz temporaria, sem downloads). 6 testes com a fixture
    LR real (secoes 4 e 7, `timemodified`). **Baseline:** LR {novos 1 = Lab 4 HTTP, 0, 0; iguais 6; links 2} · FR {0, 0, 0; iguais 20;
    links 4} · CG {novos 19 = 15 paginas Moodle de videos + 4 arquivos (zip, 2 xlsx...); alterados 0; sumidos 26 = entries do EXPORT
    sem par por nome; iguais 47; links 27}. Modulos `page` contam como material no diff; o S2 usa a classificacao do pull
    (`links.json`: print x indice-videos) para decidir imprimir ou referenciar.
S2. ~~**Import do delta**~~ FEITO 03/09 (`619488c`): `moodle_sync.plan_import(diff, contents, scan, links, entries, nomes=, defaults=,
    prune_removed=)` -> `SyncPlan{add, readd, prune, mark, links, review, ignorados}` (puro; casa os itens do stash aos modulos
    novos/alterados com o MESMO casador; links `acao == referencia` -> entries url `references` com card, sem duplicar URL;
    `review` fica no manual-review; `ignorados` = stash.skipped por nome, dotfiles fora). `scripts/sync_moodle.py <slug> --apply
    [--repo <copia>] [--no-prune]`: `moodle_pull --pdf` na raiz do curso (baixa/imprime SO o que nao existe), `scan_stash_cards`,
    plano, `unprocess` dos alterados/sumidos (ou marca `moodle_missing_since` + `include_in_bundle=False`), copia `raw/moodle`
    para o repo, `incremental_build` com novos + links. 5 testes (fixture LR + `links.json` real do FR).
S3. ~~**Regeneracao + diff de decisoes**~~ FEITO 03/09: `snapshot_decisions` (bloco/unidade/subunidade/flag; pino vale como
    bloco) antes do build; `decision_diff` (moved/added/removed) depois; `mark_sync_changes` grava `sync_changed`
    ("bloco: X -> Y (sync AAAA-MM-DD)", campo novo do `FileEntry`) e recalcula `revisar`; estado novo **`mudou`** em
    `routing/revisar.py` (duvida > mudou > llm > ok; censo conta mudou em revisar/100); `course/SYNC_REPORT.md` com 8 secoes.
    6 testes. **Medido na COPIA do LR:** 1a sync = Lab 4 entra (`lab-4-http`, bloco-05 data/janela-1 sem flag, unidade-01), as 6
    antigas so ganham os 3 campos de estrutura, 0 decisoes movidas, 0 falhas; 2a sync (sem delta) = manifest byte-identico
    fora `updated_at`, relatorio "nenhum" em tudo. Gate do S3 batido.
S4. **Primeira sync real = LR** (Lab 4, regua magra): commit do LR; subunidade/travessia nao mudam.
S5. **FR = controle** (diff vazio; entram os 3 campos de estrutura + 2 videos como referencia); `subunit_gt_FR` 14/18 e
    `travessia_gt_FR` 15/15 intactos; commit.
S6. **CG = rebuild limpo pela API** (`--pdf`: 40 downloads, 30 impressoes/snapshots, Datalab); zero curadoria, summaries ON,
    vocab compilado, voter ON com cap; `ground_truth_CG.csv` re-chaveado por `true_block_uuid` (35 scorable) e holdout rerodado;
    o user revisa a fila `revisar` (cada correcao = override + gold-por-fenomeno). "Em duvida 28/08" e "modals" triados so aqui.
Gate da campanha: curada intacta; holdout CG >= 30/35 puro, 34/35 curado; sentinela 0 nos 5 encerrados; determinismo; suite.
Script: `scripts/sync_moodle.py <curso> [--dry-run]` (headless, como o reprocess); botao na UI so com a secao de revisao.

## DEPOIS DA SYNC (ordem decidida 03/09)
- **C0 restante:** 9 (refactor corte 1: `scripts/` 79 -> ~25 + podar a escada stale da `regua_aula.py`), 10 (Fase 2 unidade),
  11 (Fase 4 LLM so nos flagados — decidir a ordem motor <-> LLM: hoje o card so age depois do voter), 12 (travessia "depois").
- **C1 — TRAVESSIA (1 sessao, recomendacao: logo apos a sync).** FILE_MAP completo e magro (IA 9 -> 14/15 medido).
- **C3 — LISTAS/TRABALHOS/PROVAS e imagens** (antes de C2 por decisao do user): granularidade da cobertura (prova inteira x
  questao), P2b-LLM, EXAM_INDEX honesto, imagens do Datalab. Gold ANTES: ~10 provas + ~10 imagens.
- **C2 — REFERENCIAS/BIBLIOGRAFIA (por ultimo):** decisao B (eth2/aws), `coverage_gt` vetado, pino de cobertura, consumo de bibliografia.
- **C4 limpa pre-web** (byte-identico) · **C5 dividas de dados** (Lab SO SARC 310, GAP VIDEO T2, headings) · **C6 web**.
Protocolo anti-regressao de todo lote: `_archive/2026-09-02c-handoff-fase3-medida.md` §CAMPANHAS (gold antes de regra; todas
as reguas rodam e nenhuma regride; copia antes dos originais; 4-7 itens; 1 handoff vivo).

## Decisoes ABERTAS (do user)
- Regua por item: motor COM vocab + curada + holdout, ablacao sem vocab so em gate de fase? (proposto 03/09; `motor_puro.py`
  passaria a rodar com vocab por default). Hoje rodam as 3 linhas.
- Decisao B (eth2/aws) · golds proposto-claude (`travessia_gt_*`, `subunit_gt_FR`, `ground_truth_CG`) · push/merge em main.

## NAO fazer (refutado no gold)
Serie k -> k-esimo bloco · serie monotonica (+1/-2) · prova antiga -> prep (0) · H7 ordem das secoes pos-item 3 (0/0) · H6 label
unico (0/0) · label em decisao confiante · card ANTES do voter · regex de nome para card generico (secao 0 e o sinal).

## Ferramentas
`scripts/motor_puro.py [--com-vocab]` · `scripts/censo_motor_llm.py` · `scripts/sentinela_manifests.py` · `scripts/eval_eixos.py` ·
`scripts/reprocess_assignments.py` · `scripts/moodle_pull.py --course N --root R [--dry-run|--pdf]` ·
`_harness-2026-09-02/{regua_aula,holdout_cg,calibra_revisar,mede_alavancas,determinismo}.py`.
