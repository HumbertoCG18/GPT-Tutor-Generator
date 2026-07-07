# Handoff — Virada de fase: medição IA → arquitetura da cascata

date: 2026-06-26
contexto: continua de `2026-06-23-handoff-sessao.md`. Branch `feat/block-stable-id`.
status: medição IA FECHADA (baseline cravado). Próximo = decidir/testar arquitetura da cascata de atribuição.

---

## 0. TL;DR pro chat novo

- Mediu-se a atribuição file→bloco do IA com rigor crescente. **Baseline cravado: 87% discriminante / 91% agregado**, FAILs nomeados, diagnóstico EARLY/LATE/FORA.
- **Virada:** parar de medir, decidir ARQUITETURA. Objetivo real = sistema de atribuição MODULAR (toda matéria, esforço mínimo, alta precisão) por **cascata de fontes**.
- **Inventário feito (read-only).** Resposta única: **a cascata EXISTE no código, mas o nível FINO está gateado OFF + a precedência está INVERTIDA. NÃO é "âncora-de-pasta é tudo".** É **tarde (religar+reordenar), não semana (construir)** — com 1 ressalva (o fino regrediu o gold antes).
- **Próximo passo decidido (não-disparado):** teste mínimo por flag-swap em `subjects.json` (`use_anchor_placement=False` + `use_concept_resolver=True`) → reprocessa → re-mede contra baseline. Se 3 FAILs caem E baseline segura → cascata é o caminho.
- **Disciplina:** NÃO commita (user separa à mão). Mutação do vivo = ação do USER na GUI (não CC). Read-only no inventário.

---

## 1. O BASELINE (a SPEC + o juiz da reconstrução)

Mundo-63 IA (42 originais + 21 notebooks importados). Denominador derivado = **33 scorable** (clean ∩ joined ∩ single-block ∩ resolved).

- **Agregado: 30/33 (91%)** — pós-fix do pin do artigo (era 29/33).
- **Discriminante (geométrico): 13/15 (87%)** — pós-fix (era 12/15).
- **Trivial: 17/18 (94%)** — inflado-monstro (bloco-05 engole 18/03–20/04).
- A pass-rate NÃO é o titular; os **FAILs nomeados** são (regra: reportar FAIL nomeado, não agregado).

**3 FAILs restantes (estruturais, não 1-linha):**
1. `exemplo-2-k-nn-IRIS` — k-NN fronteira, **band ALTA = confiante-errado** (pendência de calibração). true bloco-05, anchor bloco-04.
2. `exemplo-com-k-nn` — k-NN fronteira, mesmo mecanismo. true bloco-05, anchor bloco-04.
3. `IA-aula-29` — INTERIOR, **uncovered** (source_section=None → temporal vazio → fallback computed scorer_only band-baixa = bloco-04). true bloco-05.

**Diagnóstico do mecanismo (EARLY/LATE/FORA)** — a âncora-de-pasta erra **bidirecionalmente** (scout dos 12 straddle joined):
- **EARLY-bias** (subt-1,3,9): âncora→bloco-do-início-da-pasta.
- **LATE-bias** (subt-2): âncora→bloco-do-fim (OPOSTO).
- **FORA / off-by-MANY** (subt-11): material postado em pasta-de-tópico-errado → bloco distante (`lista1`→bloco-15, `prova-1`→bloco-08). Conflito gold-vs-postagem.
- → **não há "um conserto Semana-3"**; qualquer ajuste de end-selection cego que ajuda EARLY regride LATE. Fix bidirecional real = resolução por-tópico-per-material (concept_resolver).

---

## 2. INVENTÁRIO DA CASCATA (block placement, IA)

### Fontes + função/arquivo
| Fonte | Função / arquivo | Papel | Estado IA |
|---|---|---|---|
| SARC syllabus | `_parse_syllabus_timeline` (timeline/index.py:128) → block_identity | Define os BLOCOS (period_start + topic_tokens) = ALVOS | ATIVA (define alvos, NÃO placeia) |
| Cards/source_section | `_card_scoped_block` (content_taxonomy) + `apply_anchor_placement` (anchor_placement) | Placeia por pasta-Moodle / "Semana N - DD.MM" | ATIVA — nível GROSSO |
| Card-dates | `parse_card_dates`+`derive_card_block_map` (moodle_labels) → card_block_map | card-AULA-datas ∩ block-periods | ATIVA |
| Roteiro/lessons_index | `build_lesson_topic_index` (moodle_labels, no import) → `score_lesson_match` (concept_resolver, W_LESSON 0.5) | card-descrição-por-data casa material | GATEADA OFF |
| Conteúdo (concept/LLM) | `_card_scoped_block` LLM-vote + `apply_concept_resolver` fusão-6-termos | lê conteúdo | LLM-vote ATIVO; fusão GATEADA OFF |
| Plano-de-ensino | `parse_units_from_teaching_plan` (file_map:1493) | → UNIDADES (não blocos) | ATIVA mas pra UNIT |

### Ativo / gateado / nunca-escrito (placement)
- **ATIVO:** `_card_scoped_block`→`computed_block_id`; `apply_anchor_placement`→`temporal_block_id` (Semana-folder-week) ← âncora-de-pasta, o grosso rodando sozinho.
- **GATEADO OFF** (`use_concept_resolver=False`, `pedagogical_regeneration.py:366`): `apply_concept_resolver` — fusão 6-termos (concept W_CONCEPT=1.0 + LLM W_LLM=0.85 + date_term + seq + card + **roteiro/lesson W_LESSON=0.5**). Nível FINO per-material, DORMENTE. **Regrediu o gold (11→10)** com concepts ruidosos; revertido p/ clean-signal, segue gateado.
- **NUNCA-ESCRITO como placement-source:** SARC-tópico→data DIRETO per-material (SARC só define blocos). Plano-de-ensino só → UNIDADES.

### Precedência read-time (o que o EVAL pontua) — `resolve_temporal_block` (file_map.py:633-636)
```
1. temporal_block_id  (âncora/pasta)  ← VENCE
2. manual_timeline_block_id  (pin)
3. computed_block_id  (_card_scoped_block; OU concept_resolver se ligado)
```
**INVERTIDA:** grosso (âncora) lê ACIMA do fino (concept_resolver escreve em `computed` = fundo). Ligar use_concept_resolver não basta — fino fica abaixo, não pontuado, sem reordenar.

### Gates de placement (todos): `pedagogical_regeneration.py`
- `:57` `enable_material_residual` (Camada-2 Gemini residual)
- `:366` `use_concept_resolver` (**OFF p/ IA**)
- `:379` `use_anchor_placement` (**ON p/ IA**; feature_flags subjects.json = `{use_anchor_placement: True}`)

### Degradação
- Sem source_section → âncora não placeia → temporal VAZIO → cai pro computed (scorer fraco). Degrada, não quebra (IA-aula-29).
- Sem SARC → sem blocos → quebra.

### 2 camadas de mascaramento (por que o 80%→87% NÃO generaliza)
- Âncora mascara erro-de-computed (hierárquico: computed=bloco-07 errado, âncora=bloco-06).
- Pins mascaram erro-de-âncora (`artigo-usando-k-nn-em-texto`: pin-05 corrige âncora-04 — FÓSSIL, humano já patcheava a fraqueza Semana-3).
- **Erro BRUTO do placement-por-pasta (sem âncora, sem pins) é > 20%.** SO/MF podem não ter essas camadas.

---

## 3. PRÓXIMO PASSO (decidido, NÃO disparado)

**Teste mínimo SEM código — 2 feature_flags em `subjects.json` IA:**
```
use_anchor_placement = False   (âncora não escreve temporal)
use_concept_resolver = True    (resolver fino escreve computed)
```
→ `resolve_temporal_block` cai no `computed` = resultado do concept_resolver (fino) → **é o que o eval pontua.**
→ Reprocessar (GUI) → re-medir contra baseline 87%/91%.

Decisão:
- 3 FAILs caem E baseline segura → fino > grosso, **cascata é o caminho**, expande com confiança.
- Tanca (como o gold antes) → âncora ainda necessária; fix real = HÍBRIDO (cascata fino→grosso com fallback), aí precisa do **reorder de `resolve_temporal_block`** (pequeno código).

Regra modular na cabeça do user (não-cravada — inventário pode mudar): **SARC-data > roteiro > plano-de-ensino > estrutura-de-cards, primeira-que-resolve-vence, degrada pro próximo.** Mas SARC-data-per-material não está wired; o substituto wired é roteiro (lessons_index) no concept_resolver.

---

## 4. INSTRUMENTO DE MEDIÇÃO (reutiliza inteiro — é o juiz da reconstrução)

Todos em `scripts/` (criados nesta campanha, uncommitted):
- `postcond_reimport_IA.py` — pós-condição read-only do re-import (assert 63 + 21 notebooks).
- `dedup_md5_IA.py` — scan md5 do corpus. 3 grupos KNOWN (minimax, lista, prova), 0 NOVO no mundo-63.
- `precheck_stash_paths_IA.py` — paths distintos no stash (pré-import).
- `build_ground_truth_IA.py` — **CONVERSOR** gold xlsx → `docs/reports/ground_truth_IA.csv`. HALT pós-crosswalk. Regra borda `[início,fim)` + teste-unidade. Emite id/true_block_id/computed/temporal/pair_key/provenance/scope/scorable/discriminante.
- `classify_discriminant_IA.py` — classifica 33 em DISCRIMINANTE/TRIVIAL por regra geométrica (±1 aula-SARC muda bloco), CEGA ao resultado.
- `diff_pinfix_IA.py` — diff não-cascateamento (before vs novo), critério travado.

Eval (já existia): `scripts/eval_ground_truth.py <repo_root> <labels.csv>`. **Pontua TEMPORAL** (resolve_temporal_block), não computed.

**PROTOCOLO de conserto (cravado):** pós-mutação do vivo → **REGENERA o CSV** (`build_ground_truth_IA`) ANTES de classificar (senão CSV-stale vs vivo dá número errado — eval lê vivo, classify lê CSV). Sequência: mutação→gate-vivo→reprocess→diff_pinfix→**regen CSV**→eval+classify.

---

## 5. ESTADO DO DADO VIVO

Repo IA: `C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor` (typo "Artifical" é o nome REAL da pasta; bate com `subjects.json IA.repo_root`).

- `manifest.json` = **63 entries**, `artigo-usando-agrupamento` em **bloco-06** (pin errado deletado + reprocess; 1º conserto da campanha, validado: FAIL→PASS, não-cascateamento LIMPO).
- Backups (nomes estáveis, NÃO rotacionados pelo auto-`.bak`):
  - `manifest.json.before-pinfix.20260626.bak` (63, artigo+pin) — rede do fix.
  - `manifest.json.postpoda-42-prereimport.20260623.bak` (42).
  - `manifest.json.prepoda-55.20260623.bak` (55).
- Gold: `docs/reports/gold_templates/gold_IA_rotular.xlsx` (53 originais + 21 notebooks = 74 rows; aba Rotulagem + Gabarito Subtopicos). Backup `gold_IA_rotular.20260625.bak.xlsx`.
- `docs/reports/ground_truth_IA.csv` — CSV do conversor (pós-fix).

### Achados de dados (gold vs manifest)
- **16 gold materiais fora da manifest viva:** 13 PODADOS (poda 55→42; gold rotulado pré-poda; out-of-escopo aceito) + 3 NEVER-IMPORT: `Agentes.pdf` (FALSO ALARME — existe como `introducao-a-agentes`, mismatch-de-nome) + `P2_IA_2024` + `P2_IA_2024_02_A_turma30` (2 provas; **hipóteses DISTINTAS: phantom-no-gold vs nunca-baixada** — investigar separado, precisa checar Moodle).
- **21 straddle clean inscoráveis** (12 joined) — gold rotula em subtópico-2-sessões, pipeline placeia em bloco-1-sessão (propriedade do MÉTODO de gold). Re-entram via batch SARC (selector escolhe DATA, não bloco). Zona alta-FAIL.

---

## 6. FRENTES ABERTAS (ordem decidida)

1. **[próximo] Flag-swap test** (§3) — mede fino-sozinho vs baseline. Decide religar+reordenar vs híbrido.
2. **Layer-2 straddle** — pré-preencher data_real dos 12 joined (filename, como notebooks; revisar mushy) → medir taxa-FAIL straddle vs não-straddle SEPARADO.
3. **Fix estreito subt-3** — os 2 k-NN (EARLY-bias). Não-1-linha (anchor end-selection).
4. **never-import** — distinguir phantom vs nunca-baixada nas 2 provas (checar Moodle); fix alias do Agentes.
5. **Calibração** — IRIS confiante-errado (band alta), prioridade alta; protocolo "só reviso o flagado" é CEGO pra confiante-errado.

---

## 7. DISCIPLINA / CONSTRAINTS (não-negociável)

- **NÃO commita.** User separa à mão (há trabalho pré-sessão misturado no working-tree).
- **Mutação do vivo = ação do USER na GUI** (deletar pin, reprocessar). CC prepara/valida arquivos MORTOS; tornar-vivo é ato do user (rename/reprocess) com gate-vivo do CC antes.
- **GUI lê o disco** (`incremental_build_impl:25` json.load). Pin-edit pelo Timeline Dashboard persiste imediato (`timeline_dashboard.py:248` write_text cru, sem .bak); pelo diálogo é in-memory (precisa save). **Armadilha §5:** estado-GUI-velho sobrescreve disco — ordem blindada: fecha-GUI→rename→gate-vivo→reabre→reprocessa.
- **Aviso GUI "sem bloco atribuído" = sem PIN, não sem placement** (58-59/63 usam auto-placement, estado DESEJADO). NÃO preencher à mão — re-introduz circularidade. (Armadilha de UX, stampada.)
- Gates de medição: regra geométrica/borda FIXADA antes de ver resultado; reportar FAIL nomeado não agregado; número inflado CONTRA o sistema é tão inválido quanto a favor (n pequeno ≠ taxa).

---

## 8. PENDÊNCIAS (em `docs/reports/pendencias.md`)

Seção nova **"MEDIÇÃO IA — conversor gold→ground_truth (as-of mundo-63)"** com: straddle-gold-method, 21-straddle-batch-SARC, 16-unjoined (poda/never-import split), denominador-33, 2-mecanismos-FAIL, calibração-IRIS, pin-sweep, UX-trap-aviso-GUI, protocolo-regen-CSV, 80%-pós-2-camadas. Tudo carimbado `as-of`.

CLAUDE.md / .mex: ler `.mex/AGENTS.md` + `.mex/ROUTER.md` no início. Idioma PT-BR. Começar resposta com "[Humberto]".
