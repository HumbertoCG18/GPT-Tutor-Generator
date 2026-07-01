# Spec — Identidade estável de bloco (uuid + ledger durável)

date: 2026-06-20
branch: `feat/block-stable-id`
base: `8fb4bd2` (pós-degrau-3a)
status: **SPEC PARA REVISÃO — nenhuma linha de código antes do OK do Humberto.**

## Problema

`block_id` é POSICIONAL: `index.py:2066` emite `f"bloco-{position:02d}"`, onde
`position` = índice do `enumerate` sobre os blocos agrupados. Qualquer mudança de
fronteira (split, merge, encurtamento) RENUMERA todos os blocos seguintes em
cascata e desalinha tudo que persistiu o id. Lição do degrau 2 revertido
(`a2acc22`): cap temporal dava golden MF 5/5 mas IA +17 blocos = id-shift, não
regrouping. Enquanto o join depender de id posicional, não dá pra mexer em
fronteira (degraus 3c/5 travados).

### Inventário COMPLETO de consumidores persistidos (grep exaustivo — D1 cond. 3)
| Consumidor | Site | Classe |
|---|---|---|
| Geração | `index.py:2066` | fonte |
| `card_block_map.block_ids` | escrito `moodle.py:488`, lido `card_block.py:143` | referência re-derivável |
| `computed_block_id` (+ `period_block_id` interno) | `models/core.py:87`, escrito `content_taxonomy.py:1319` / `resolver_apply.py:113` | referência re-derivável |
| **`manual_timeline_block_id`** | `models/core.py:50`, UI `dialogs.py`/`timeline_dashboard.py:244` | **VERDADE HUMANA** (aceita `bloco-NN` OU índice nu `N`) |
| `secondary_block_ids` | code_curation, `codes_panel.py:391` / `code_summarization.py:417` | referência re-derivável |
| **`.timeline_curation.json`** (keyed `"bloco-03"`) | `curation.py:11` | **VERDADE HUMANA** |
| **gold `true_block_id` / `expected_block_id`** | CSVs `docs/.../gold_*`, golden `assignments_gold.json:96` | **VERDADE HUMANA** (camada de medição) |
| **comparação dos evals** | `eval_assignments.py:164` (`predicted==expected`), `eval_ground_truth.py:91` (`predicted==true_block`) | igualdade de string crua |
| tag `bloco:` / ordinal | `file_map.py:506` parseia `bloco-(\d+)` | **só display** |

TRÊS superfícies de **verdade humana irrecuperável** (`manual_timeline_block_id`
+ `.timeline_curation.json` + gold `true_block_id`/`expected_block_id`): o sistema
re-deriva todo o resto; override/rótulo humano não — teria que perguntar de novo.
São as primeiras a apodrecer e as que mais doem. Recebem a trava mais conservadora
(ver §3.6).

**Auto-reversão sem a camada de medição:** os dois evals comparam
`computed_block_id` (predicted) com o gold (`bloco-NN`) por **igualdade de string
crua**. Migrar só o `computed_block_id`→uuid (§3.5) deixando o gold em `bloco-NN`
→ igualdade falsa em 100% → `eval_assignments` 0/5 → portão "sagrado" FALHA →
REVERT. A Fase 1 se auto-reverteria no primeiro portão. Os dois lados da igualdade
têm que falar uuid juntos (§3.9 + T6).

## Objetivo (Fase 1, fundação — NÃO é alavanca)

Cada bloco ganha um **uuid persistido**, re-anexado a cada rebuild por **matching
EXPLÍCITO** (NÃO hash de conteúdo — hash quebra no split, justo a operação a
proteger). `bloco-NN` vira **rótulo de display**; o join interno usa uuid.

INVARIANTE: estritamente não-comportamental nos 5 cursos atuais. `eval_assignments`
5/5 cw0; `rebuild_diff` sem drift novo vs baseline (ES2 7 / IA 20 / SO 13 / MF 1 /
TCC 0); suíte verde; flag `use_concept_resolver` OFF. Regressão em portão = REVERT,
nunca calibração.

## Design

### 3.1 Ledger de identidade `.block_identity.json` (D2 = B, decisão travada)
Arquivo PEQUENO, **trackeado no git** do repo gerado, **append-only**. Fonte de
verdade da identidade. Cada registro:
```
{ "uuid": "<uuid4>", "anchor": {"period_start": "YYYY-MM-DD",
  "period_end": "YYYY-MM-DD", "topic_tokens": [...]},
  "display_id_last": "bloco-NN", "first_seen": "...", "last_seen": "..." }
```
Por que ledger e não o índice: `.timeline_index.json` é gitignored **como
"regenerável"** (gitignore:17, 86KB reescrito todo rebuild). Pôr a identidade lá
tornaria a classificação mentira E o uuid irrecuperável num clone novo. Mover a
identidade pro ledger pequeno **restaura a verdade** de que o índice é regenerável.
Append-only: bloco que some mantém o registro → bloco que volta re-anexa.

### 3.2 Runtime: `block_uuid` no índice (consumo, não persistência de verdade)
Cada runtime_block (`index.py:2065`) recebe `block_uuid` (vindo do ledger) pro
join interno. Serializado no `.timeline_index.json` regenerável (continua
gitignored). `id` (`bloco-NN`) permanece como display/ordinal; `file_map.py`
segue parseando o ordinal dele.

### 3.3 Re-attach por best-overlap de datas (D1/D4, travado)
No rebuild, carrega o ledger e re-anexa:
- **Chave = sobreposição de datas** (`period_start..period_end` novo vs registros
  do ledger). Cada bloco novo herda o uuid do registro de maior overlap.
  **Desempate**: overlap de `topic_tokens`. **Sem data / empate sem desempate**:
  cunha uuid novo (não adivinha) e loga.
  - **Near-tie (radar, impl T2):** dois topos PRÓXIMOS sem empatar exato (ex.: 0.51
    vs 0.49 num re-sync que desloca bastante a data) escolhem o maior em silêncio.
    Quando o registro tem referência humana apontando (override/gold), flagar o
    near-tie (não só o empate exato) — fecha o último mis-attach silencioso.
- Bloco novo sem match (overlap zero) → cunha `uuid4`, append ao ledger.
- **Split**: dos 2 fragmentos, o de maior overlap herda; o outro cunha.
  **Merge**: o fundido herda o uuid do registro de maior overlap.
- Tolerante por design (best-overlap fuzzy, não exato): re-sync que CORRIGE uma
  data NÃO re-cunha — o bloco com data deslocada ainda tem maior overlap consigo.

### 3.4 REFUSE-GUARD anti-orfanamento (trava D2, load-bearing)
Antes de cunhar, o re-attach DETECTA o cenário catastrófico:
- **SE** o ledger está ausente/vazio **E** existem referências apontando pra
  blocos (qualquer `computed_block_id` / `manual_timeline_block_id` /
  `card_block_map.block_ids` / `.timeline_curation.json` / gold `true_block_id`
  não-vazio) **ENTÃO ABORTA** com erro claro — NUNCA re-cunha tudo do zero.
- Build inicial (ledger vazio **E** zero referências) → cunha à vontade.
- Garante segurança mesmo se o git falhar (clone sem ledger, ledger corrompido):
  aborta em vez de orfanar tudo silenciosamente. É a rede; o git-tracking do
  ledger é a recuperação.

### 3.5 Migração lazy retrocompatível (referências re-deriváveis)
Roda enquanto o id posicional AINDA é válido (antes de qualquer mudança de
fronteira). Lê ambos os formatos (uuid direto OU `bloco-NN`/índice `N` legado),
resolve posicional→uuid via o índice corrente, reescreve uuid:
- `card_block_map.block_ids`, `computed_block_id`, `secondary_block_ids`.

### 3.6 Verdade humana: migra com trava conservadora (D3, travado)
As TRÊS superfícies humanas migram pra uuid: `manual_timeline_block_id` (manifest),
`.timeline_curation.json`, E o gold `true_block_id`/`expected_block_id` (§3.9).
**Id que a migração não resolve com confiança → FLAG pro Humberto (lista
explícita), NUNCA dropa em silêncio nem mapeia no chute.** Um rótulo perdido =
trabalho humano jogado fora; um rótulo mal-mapeado faz a correção/medição corromper
outro bloco. `manual_timeline_block_id` aceita índice nu `N` → a resolução trata
`N` e `bloco-NN`; ambíguo/irresolúvel → FLAG.

### 3.7 Git hygiene (repos gerados)
- `.block_identity.json` (ledger), `.card_block_map.json`, `.timeline_curation.json`
  → devem estar **TRACKEADOS** (ledger + referências + verdade humana). Hoje
  card_block_map/curation existem mas não-commitados; ledger é novo.
- `.timeline_index.json` → permanece **gitignored** (agora honestamente regenerável).
- Override por-entry (`manual_timeline_block_id`) já vive no manifest trackeado.

### 3.8 Display inalterado
Cronograma, FILE_MAP, tags `bloco:` seguem mostrando `bloco-NN`. Só o JOIN interno
passa a uuid. Nenhum MD de tutor muda de byte (verificado por golden).

### 3.9 Camada de medição migra JUNTO (sem ela, auto-revert no portão)
Os dois lados de cada igualdade de eval têm que falar uuid na MESMA Fase, enquanto
o posicional ainda é válido:
- **Predicted:** `computed_block_id` já vira uuid (§3.5).
- **Expected/true:** gold `expected_block_id` (golden `assignments_gold.json`) e
  `true_block_id` (CSVs de ground truth) migram pra uuid. **São verdade humana →
  trava §3.6: irresolúvel → FLAG, nunca chuta.**
- Os comparadores `eval_assignments.py:164` e `eval_ground_truth.py:91` passam a
  comparar uuid==uuid (igualdade de string preservada; só muda o formato do id).
- O golden sintético `assignments_gold.json` define blocos inline (`id: bloco-NN`):
  ou recebe `block_uuid` determinístico nos blocos da fixture + reescreve
  `expected_block_id`, ou o harness sintético normaliza posicional→uuid no load.
  Decisão de impl na fase TDD; T6 trava o resultado.
- `gold_by_card` / `expand_card_gold` / `propose_gold` passam a emitir uuid.
  **Isso É a pré-condição do Plano A** (gold dos outros 4 cursos nasceria em
  `bloco-NN` e apodreceria no 1º renumber). Resolver aqui mata os dois coelhos.

## Teste-prova (TDD, red primeiro)
- **T1 (core):** split de bloco NÃO quebra `lookup_card_blocks` NEM reembaralha
  `computed_block_id`. Contraste: o MESMO cenário com id posicional QUEBRA (prova
  a regressão).
- **T2 (re-sync muda data — D1 cond. 1):** rebuild onde a data de um bloco muda
  (correção de fonte) → uuid re-anexa por best-overlap, NÃO re-cunha.
- **T3 (empate de datas — D1 cond. 2):** 2 blocos na mesma janela → desempate
  determinístico por topic-token; sem data/empate irresolúvel → cunha novo + loga,
  nunca adivinha.
- **T4 (refuse-guard):** ledger ausente + referências existentes → ABORTA (não
  re-cunha). Contraste: ledger ausente + zero referências → cunha ok.
- **T5 (verdade humana):** override (`manual_timeline_block_id` e curation)
  irresolúvel → FLAG, não dropa nem chuta.
- **T6 (medição não-comportamental):** depois de migrar gold + evals pra uuid,
  `eval_assignments` dá os MESMOS números de antes (5/5 cw0). Prova que a troca de
  formato de id é não-comportamental na própria medição (não é o uuid quebrando o
  golden — é o gold que não pode ficar pra trás no formato antigo).

## Decisões (TRAVADAS pelo Humberto, 2026-06-20)
- **D1 — re-attach:** best-overlap de datas + desempate topic-token. ✅
- **D2 — persistência:** ledger pequeno append-only `.block_identity.json`
  trackeado (NÃO no índice gitignored). ✅
- **D3 — verdade humana:** `manual_timeline_block_id` + `.timeline_curation.json`
  migram; irresolúvel → FLAG, nunca silent drop / chute. ✅
- **D4 — split/merge:** maior overlap herda, perdedores cunham. ✅

## Execução (após OK, na ordem — ritual SDD)
0. **PASSO 0** — congelar baselines dos 5 repos (`eval_assignments`,
   `eval_code_block_gold`, `rebuild_diff`) em
   `docs/reports/2026-06-20-baseline-congelado.md`. Read-only, não muda comportamento.
1. Testes red (T1–T6).
2. Impl green (ledger + re-attach + refuse-guard + migração lazy + trava humana +
   camada de medição §3.9: gold CSVs + golden JSON + gold tools + os 2 evals).
3. Review (spec + qualidade).
4. Portão: `eval_assignments` 5/5 cw0 · `pytest -q` verde · `rebuild_diff` sem
   drift novo vs baseline. Falhou → REVERT.
5. Commit (trailer Co-Authored-By) + ledger `.git/sdd/progress.md`.

## Saída conhecida (se o ledger der churn no futuro)
Já estamos no ledger append-only (a "saída" do D2-A). Próximo upgrade possível:
âncora mais rica (datas + 1ª sessão isolada) se best-overlap ainda churnar. Não é
beco sem saída.

## Forward note — Fase 2 (NÃO agora)
`rebuild_diff.py:33` pareia o índice antigo por `b["id"]` (`bloco-NN`). Na Fase 1
está correto (não mudamos fronteira → bloco-NN↔bloco-NN compara unit/kind intactos,
uuid invisível). Na **Fase 2**, quando o join por data começar a splitar/mover
fronteira, parear por `bloco-NN` vai acusar **drift espúrio de renumeração** — aí
o `rebuild_diff` terá que passar a parear por `block_uuid`. Não mexer agora; só
pra não confundir renumeração com regressão quando a Fase 2 chegar.
