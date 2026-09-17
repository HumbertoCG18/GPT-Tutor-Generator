# Plano — Identidade estável de bloco (Fase 1)

spec: `docs/superpowers/specs/2026-06-20-block-stable-id-design.md`
branch: `feat/block-stable-id`
base: `1422443` (docs checkpoint: spec + baseline congelado)
modo: subagent-driven + TDD. Ledger durável: `.git/sdd/progress.md`.

## Global Constraints (verbatim — atenção do reviewer)
- INVARIANTE não-comportamental. Portão (falha = REVERT, NUNCA calibração):
  - `eval_assignments` 5/5 cw0 (idêntico ao baseline).
  - `eval_code_block_gold <MF>` resolver_acc >= 70.6%, confiante-errado <= 1.
  - `rebuild_diff` sem drift NOVO vs **ES2 0 / IA 1 / MF 1 / SO 0 / TCC 0** (baseline real).
  - `python -m pytest tests -q` verde.
  - flag `use_concept_resolver` OFF = produção byte-idêntica.
- **NÃO hash de conteúdo.** Re-attach = best-overlap de datas (`period_start..period_end`)
  + desempate por overlap de `topic_tokens`.
- `bloco-NN` permanece como **display** (`file_map.py:506` ordinal intacto). uuid = join interno.
- **Verdade humana irresolúvel → FLAG (lista explícita), NUNCA dropa em silêncio nem chuta.**
  Superfícies humanas: `manual_timeline_block_id`, `.timeline_curation.json`, gold
  `true_block_id`/`expected_block_id`.
- Migração lazy retrocompatível: lê `bloco-NN`/índice `N` E uuid; resolve posicional→uuid
  via índice corrente enquanto válido; reescreve uuid.
- Determinismo de teste: uuid via injeção/seed nos testes (não `uuid4` cru não-determinístico
  nas asserts).

## Task 1 — Ledger de identidade + block_uuid + re-attach + refuse-guard
NÚCLEO. Novo módulo `src/builder/timeline/block_identity.py` (puro; I/O só load/save do ledger).

API:
- `load_identity_ledger(course_dir) -> list[dict]` (lê `.block_identity.json`; [] se ausente).
- `save_identity_ledger(course_dir, records) -> None` (escrita atômica).
- `reattach_block_uuids(runtime_blocks, ledger, *, has_existing_refs: bool, mint=uuid4) -> tuple[list[dict], list[dict], list[str]]`
  retorna (blocks_com_block_uuid, ledger_atualizado, flags). Lógica:
  - best-overlap de datas vs `record["anchor"]`; desempate topic_tokens; herda uuid.
  - overlap zero → cunha (mint) + append record.
  - **near-tie** (2 topos próximos, margem < ε) E record com ref humana → adiciona a `flags`.
  - empate exato sem desempate / sem data → cunha + loga em `flags`.
  - **REFUSE-GUARD:** se `ledger==[]` E `has_existing_refs` → `raise BlockIdentityError`
    (NUNCA re-cunha tudo). `ledger==[]` E `not has_existing_refs` → cunha à vontade.
  - registro: `{uuid, anchor:{period_start,period_end,topic_tokens}, display_id_last, first_seen, last_seen}`.
    append-only (nunca deleta); refresh de anchor/last_seen no match.
- `scan_existing_block_refs(course_dir, manifest) -> bool` (True se qualquer
  computed_block_id/manual_timeline_block_id/card_block_map.block_ids/curation/gold não-vazio).

Wire em `_build_timeline_index` (`index.py`, após `runtime_blocks` montado ~:2109,
antes da serialização): cada bloco recebe `block_uuid`. Serializer/schema persistem `block_uuid`.
`id` (`bloco-NN`) intacto.

Testes (TDD red primeiro):
- **T2** re-sync muda data: ledger tem record anchor D1..D4; rebuild com bloco deslocado p/ D2..D5
  → herda mesmo uuid (maior overlap consigo), não cunha.
- **T3** empate/sem-data: 2 blocos mesma janela → desempate topic_tokens determinístico;
  bloco sem data → cunha novo + flag, nunca adivinha.
- **T4** refuse-guard: ledger=[] + has_existing_refs=True → raise; ledger=[] + refs=False → cunha ok.
- ledger round-trip (load/save atômico).

## Task 2 — Migração lazy das referências re-deriváveis
Migra p/ uuid (lê ambos formatos, resolve posicional→uuid via índice corrente, reescreve):
`card_block_map.block_ids` (`card_block.py`/`moodle.py`), `computed_block_id`
(`content_taxonomy.py:1248/1319`, `resolver_apply.py:113`), `secondary_block_ids`
(`code_summarization.py:417`, `codes_panel.py`). Helper comum `resolve_block_ref(raw, index) -> uuid|""`
(aceita `bloco-NN`, índice `N`, uuid passthrough).

Teste **T1** (core, prova-de-fogo): índice com block_uuid-A cobrindo D1..D4;
`card_block_map[card]=[uuid-A]`; entries de A com computed_block_id=uuid-A. Split de A
em A'(D1..D2)+novo(D3..D4) → A' herda uuid-A. ASSERT: `lookup_card_blocks(card)` ainda
resolve uuid-A; computed_block_id das entries de A' inalterado; display renumera, uuid não.
Contraste: MESMO cenário com id posicional QUEBRA (prova a regressão).

## Task 3 — Verdade humana: migração com trava FLAG
`manual_timeline_block_id` (manifest, aceita `bloco-NN` OU índice `N`) +
`.timeline_curation.json` (keyed `bloco-NN`, `curation.py`) migram p/ uuid.
Irresolúvel/ambíguo → acumula em lista de FLAG (log + retorno estruturado), NUNCA dropa nem chuta.

Teste **T5**: override (manual_timeline_block_id e curation) que resolve → vira uuid;
que NÃO resolve → aparece na lista de FLAG, NÃO é dropado nem mapeado no chute.

## Task 4 — Camada de medição migra junto (anti auto-revert)
- Gold `true_block_id` (CSVs ground_truth) + `expected_block_id` (golden `assignments_gold.json`)
  migram p/ uuid. **Verdade humana → FLAG no irresolúvel.**
- `eval_assignments.py:164` e `eval_ground_truth.py:91` comparam uuid==uuid (igualdade preservada).
- Golden sintético define blocos inline: atribui `block_uuid` determinístico aos blocos da
  fixture + reescreve `expected_block_id` (ou normaliza posicional→uuid no load do harness).
- `gold_by_card`/`expand_card_gold`/`propose_gold` emitem uuid (= pré-condição do Plano A).

Teste **T6**: pós-migração, `eval_assignments` dá os MESMOS números (5/5 cw0). Prova que a
troca de formato é não-comportamental na própria medição.

## ORDEM DOS PORTÕES (coordenação — crítico)
- Task 1 é **aditiva**: adiciona `block_uuid` + ledger; `computed_block_id` continua
  `bloco-NN`. eval_assignments segue 5/5 (comparação bloco-NN==bloco-NN intacta).
- Task 2 flipa `computed_block_id`→uuid. **A PARTIR DAQUI o eval_assignments fica RED
  (0/5) POR DESIGN** até a Task 4 migrar o gold + dar block_uuid aos blocos da fixture.
  **NÃO reverter o flip pra "consertar" o eval — é esperado.** O portão eval só é
  válido DEPOIS da Task 4 (T6). Entre Task 2 e 4, validar via testes unitários (T1/T5)
  + suíte, não via eval_assignments.
- Sequência obrigatória: 1 → 2 → 3 → 4 → portão final.

## Portão final (após 4 tasks)
Rodar os 3 evals + suíte; comparar com `docs/reports/2026-06-20-baseline-congelado.md`.
Sem drift novo → review whole-branch (opus) → commit final → ledger → PARAR e reportar.
