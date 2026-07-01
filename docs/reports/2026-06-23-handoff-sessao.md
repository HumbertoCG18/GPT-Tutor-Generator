# Handoff — Sessão 2026-06-22/23

last_updated: 2026-06-23
escopo: tudo feito/discutido/descoberto na sessão. Branch `feat/block-stable-id`.
status: trabalho em andamento; muitas mudanças NÃO-commitadas (lista na seção 6).

---

## 0. TL;DR

- **Fases 0-2 da divisão de blocos: já estavam feitas** na branch (o plano de 22/06 estava stale). Provei a Fase 1 de verdade (não-cascateamento). **Fase 3 (span-cap) REFUTADA** por evidência.
- **Gold tooling**: `gold_score.py` (amostrador cego completo) + off-by-one e colapso de version-pair (regra c) no `eval_ground_truth.py`. Correção: os "version-pairs" eram **byte-dups**, não versões.
- **Bug `moodle_course_id` zerado nos 5 perfis** — achado, consertado (`dialogs.py`), e os 5 restaurados via API Moodle.
- **Causa-raiz das duplicatas do IA**: stash migrou `Downloads`→`Desktop\Moodle`; manifest acumulou os dois; faltou poda de migração. **Poda executada**: 13 stale removidas, manifest IA 55→42, pin do p1 preservado.
- **Stash IA era download parcial**: 21 notebooks baixados via API (faltam re-importar).

---

## 1. Divisão de blocos (Fases 0-3)

**Estado real (verificado contra dado vivo, não suposição):**
- **Fase 1 (identidade estável)**: FEITA. `block_uuid` 100% nos 5 repos; `reattach_block_uuids` (`index.py:1405`) roda APÓS construir blocos (`index.py:1380`). PROVADA robusta a split: `tests/test_block_split_nao_cascateia.py` (commit `b733d19`) — split renumera `bloco-NN` mas uuid segue conteúdo; `computed_block_id`+`card_block_map` seguem resolvendo; ledger append-only.
- **Fase 0 (caracterização)**: FEITA, `tests/test_caracterizacao_blocos_atual.py` + 17 goldens em `tests/_golden/` (commit `7554e82`).
- **Fase 2 (data-membership)**: viva/wired/testada — `derive_card_block_map` (`moodle.py:488`) → `.card_block_map.json` → `_card_scoped_block` (`content_taxonomy.py:1193`) → `computed_block_id` (`:1260`). Casos-chave por method `card`/`card+scorer`.
- **Fase 3 (span-cap): REFUTADA.** O "monstro" IA `bloco-05` é unidade COESA (ML supervisionado, kNN→redes→árvores), não over-merge. Span não distingue coeso-longo (MF 21d) de qualquer-longo. Cap de 15d quebrou `test_file_map_..._respects_manual_timeline_block_override` (bisecta tópico coeso) = o mecanismo do +17 do Degrau 2. **Discriminante**: arquivos da cauda não-supervis caem em bloco-06/07, NUNCA bloco-05 → a mis-merge do 04-15 é render-only, sem mal-atribuição. Cap revertido.
- Carimbo ROUTER: **"Fases 0-2 — estrutural provado (não-cascateamento + golden 5/5); correção de atribuição NÃO medida, bloqueada em gold IA."**
- Regra durável: **"2 aulas = 1 bloco" APOSENTADA** — bloco = unidade pedagógica, sessão = átomo do render.

## 2. Gold tooling

- **`scripts/gold_score.py`** (NOVO, untracked): amostrador cego. Reescrito de "score" (que duplicava+quebrava o `eval_ground_truth`) para **só `build_sample`** = folha COMPLETA (50 entries), colunas `id`/`true_block_id` alinhadas ao eval, SEM vazar `computed_block_id`, coluna `pair_key` (gancho do colapso de par, content-derived, nunca computado).
- **`scripts/eval_ground_truth.py`** (modificado): adicionado **off-by-one** (adjacência bloco-NN) + **colapso de version-pair** regra (c) (`_scoring_units` + `load_pair_keys`): par certo SÓ se ambos membros = mesmo bloco correto; denominador conta 1 por par. Backward-compat (18 testes verdes).
- **Correção factual**: os "version-pairs" `mlp`/`mlp-novaversao` e `introducao-a-ml`/`introducaoml-atualizacao2025` são **byte-idênticos** (md5), NÃO versões. O "posting 24/02 = slide reusado" estava errado. O único version-pair real (bytes diferentes, mesma aula) é `aula-29 ≡ como-analisar-acc-pr-re-e-f1`.

## 3. Moodle / subjects

- **Bug `SubjectManagerDialog._save` (`dialogs.py:1503-1525`)**: não passava `moodle_course_id`/`m365_filter` ao construir `SubjectProfile` → todo save zerava. **Atingiu os 5 perfis.** Fix aplicado (preserva de `existing`, espelha `turma`/`schedule_url`). 388 testes verdes. Working tree, não-commitado.
- **Restaurados via API** (`core_enrol_get_users_courses`): MF=92717, IA=93156, TCC=93728, SO=92854, ES2=92714 (todos 2026/1). subjects.json (app data) editado + `.bak`. NOTA: só fica se o app rodar o código com o fix (rebuild/restart) — senão próximo save in-app re-zera.
- Token Moodle existe (`moddle\.env`, `https://moodle.pucrs.br`, userid 289064) — a "API fora" que afirmei antes estava ERRADA.

## 4. Stale-dup / poda de migração (o problema central do fim da sessão)

- **Causa**: stash migrou de `Downloads\InteligenciaArtificial` (nomes = TÍTULO do PDF) para `Desktop\Moodle\inteligencia-artificial` (Moodle, nomes reais + Semanas). Manifest acumulou os dois; pipeline faz upsert por id (filename) → nomes diferentes = ids diferentes = velhos persistiram. Dedup era por basename/id, não pega.
- **Regra durável**: dedup por **CONTEÚDO (md5)**, nunca basename/id. Duplicata sem hash = palpite.
- **Diagnóstico IA**: 16 stale (source sumiu), 15 grupos dup-md5 (13 ANTIGO≡NOVO + 2 NOVO≡NOVO).
- **Poda executada (2026-06-23)**: gate = stale + byte-dup de live. **13 podados** (manifest 55→42, backup `manifest.json.bak`). **Pin do `p1-2024-02-ia` migrado** para `prova-1-2024-02` (`manual_timeline_block_id=5256ec08` + manual_unit) ANTES de deletar — sem perda de curadoria humana. Os 12/13 outros: live já aprovada (sem gap).
- **MANTIDOS (gate protegeu)**: `aula-29` (byte-único, source sumiu — variante órfã, decisão manual depois) + 2 refs (`oracle`, `ia-responsavel`, sem raw).
- **Reprocess NÃO resolve**: recomputa existentes, não poda stale nem re-scaneia stash novo.

## 5. Estado do gold IA

- `docs/reports/gold_templates/gold_IA_rotular.xlsx` (no repo, user atualizou): **51/53 rotulados**, keyed por NOME do material + subtópico (01-18, aba 'Gabarito Subtopicos'). Working copy do user estava em `OneDrive\Documentos\gold_IA_rotular (1).xlsx`.
- **Dedup vs rótulos**: 13 pares consistentes; **2 conflitos resolvidos pelo user**: `CaracteristicasDosDados`→**02**, `lista1`/`Lista de Exercicios I`→**11**.
- **Bloqueio do eval**: `ground_truth_IA.csv` não existe e NÃO há conversor xlsx(subtópico)→eval(`id`+`bloco-NN`). Precisa script novo: material→entry-id + subtópico→bloco-NN (via datas da aba Gabarito Subtopicos).

## 6. Mudanças NÃO-commitadas (working tree)

Repo principal (`feat/block-stable-id`):
- COMMITADO: `7554e82` (Fase 0 + 17 goldens), `b733d19` (não-cascateamento).
- `src/ui/dialogs.py` — fix moodle_course_id/m365_filter.
- `scripts/gold_score.py` (novo) — amostrador + pair_key.
- `scripts/eval_ground_truth.py` — off-by-one + colapso de par.
- `docs/reports/2026-06-21-pendencias.md` — várias edições (regra dedup-md5, span-cap refutado, "2 aulas" aposentada, poda IA, correção mlp/introducao, fix moodle_course_id, +mais teu trabalho pré-sessão misturado).
- `docs/reports/gold_templates/gold_IA_rotular.xlsx` — user rotulou 51/53.
- `docs/reports/2026-06-23-handoff-sessao.md` — este arquivo.

Fora do git principal:
- IA repo `manifest.json` — podado 55→42 (+`manifest.json.bak`).
- IA stash (`Desktop\Moodle`) — +21 notebooks baixados.
- subjects.json (app data) — moodle_course_id dos 5 restaurado (+`.bak`).

## 7. Próximos passos (abertos)

1. **Option-1 dedup-de-conteúdo** (3 grupos NOVO≡NOVO restantes pós-poda): `minimax-teoria≡minimax`, `lista1≡lista-de-exercicios-i`, `prova-1-2024-02≡prova-1-202402` — ambos vivos, escolher 1 de cada (não stale-prune).
2. **Substituir `VERSION_PAIRS` hardcoded por dedup-por-md5 no pipeline** (causa, não os casos). Gate: golden 5/5 + não-cascateamento + rebuild_diff.
3. **Re-importar os 21 notebooks** do stash (fila → processa → código→Gemini) — reprocess não pega arquivo novo.
4. **Conversor xlsx→`ground_truth_IA.csv`** + rodar `eval_ground_truth.py` = primeiro número honesto.
5. **`aula-29` órfã**: decidir (variante byte-única, source sumiu).
6. **Decisão de merge/PR** da branch `feat/block-stable-id` (carrega toda a campanha).
7. Commit das mudanças (user separa à mão — tem trabalho pré-sessão misturado).
