# Motor de atribuição material→bloco — design (evolução do anchor_placement)

date: 2026-06-29
status: design (pré-implementação)
rev: 2026-06-29b — incorpora probes read-only dos 5 cursos (F-TCC, restrições de plataforma, mapa de WindowProvider). Mudanças load-bearing: Contrato 1 vira CASCATA de providers (card_block_map não é universal); Disambiguator ganha SESSION-LABEL como sinal de primeira-classe.
relacionado: log de decisões `docs/reports/2026-06-28-motor-atribuicao-decisoes.md` (D0–D12, F-MF, F-TCC, Restrições de Plataforma, Mapa de Providers, SÍNTESE — FONTE-DE-VERDADE), handoff `docs/reports/2026-06-29-handoff-motor-atribuicao-impl.md`, signal-registry `docs/superpowers/specs/2026-06-17-signal-registry-design.md`

> Este spec NÃO re-decide nada. Consolida D0–D12 + SÍNTESE + os probes em requisitos
> VERIFICÁVEIS (contratos, invariantes, critérios de aceite por tier) para o plano de
> implementação e a execução SubAgent-Driven. Cada requisito rastreia a decisão de origem.

## Problema

Atribuir `material → bloco da timeline` em **5 cursos com sinais organizadores E fontes
heterogêneas**: IA = data-de-seção (Moodle); MF = unit-card + roteiro interno (M365); TCC =
"Semana N" ordinal sem data (Moodle); ES2 = card grosso 1x/sem (M365); SO = unit-card sem
roteiro mas com data-no-nome (Moodle). O motor que resolve o IA hoje (`anchor_placement`) é
**IA-only e estreito** — `resolve_placement` parseia só o formato "Semana N" (`_SEMANA_RE`),
não generaliza. Os outros 4 caem inteiros no funil-chute (`computed`, scorer). Só IA/MF têm gold.

Regra do usuário (não-negociável): **correção GERAL na raiz, nunca fix por cadeira**. A solução
é um motor plugável, mode-aware, que aproveita o sinal organizador DISPONÍVEL de cada curso,
degradando honestamente (flag) quando ele falta.

## Constatação central: o SARC é a verdade; nenhum sinal único é universal

Três provas read-only fecham o design:

1. **O backbone (SARC) é a verdade e existe CEDO.** O cronograma SARC dá **1 data por aula +
   tópico + `kind`**, completo desde o início do semestre. "Semana" é agrupamento do professor
   no Moodle, não do SARC. → blocos/datas/tópicos existem antes do material; o motor coloca
   incremental conforme o Moodle/M365 enche (D12). "Semana N" sem data NÃO é datável por
   week-math (drift — ver F-TCC); a ponte é tópico/data-real, não ordinal-linear.
2. **A janela contém a verdade ONDE o card_block_map popula (C1 = 100%):** 47/47 IA e 46/46 MF
   ∈ janela. MAS o card_block_map **não é universal** (probes): vazio no SO, grosso-inútil no
   ES2 (1 card = 10 blocos), só-manual no TCC. → a janela vem de uma **CASCATA de providers por
   sinal disponível**, não só card_block_map.
3. **O scoring já existe e é reusável (puro):** `concept_token_weights`/`concept_vector`/
   `score_lesson_match` (`concept_resolver.py`) — primitivas IDF sem efeito colateral. O motor
   REUSA o scoring bounded à janela — **não reinventa**.

**Portanto este design é EVOLUÇÃO, não reescrita.** O `anchor_placement` já é "feature-flagged,
additive, temporal-only" (`apply_anchor_placement:344` escreve só `temporal_block_id`, nunca
toca `computed`/`manual`). O motor generaliza `anchor-que-cospe-bloco` para
`WindowProvider(cascata) + Disambiguator(compartilhado)`.

> Greenfield: NÃO existem ainda `AnchorEngine`/`WindowProvider`/`Disambiguator` em
> `src/builder/routing/`. São classes novas; o resto é reuso.

## Restrições de PLATAFORMA (confirmadas; aterram o design)

- **SARC = data por aula** (1 linha = data + tópico + `kind`), completo no início. **Moodle =
  incremental** (material postado ao longo do tempo). Exceção (arquivo do semestre passado /
  upload-total) = ANOMALIA-DE-DADO (D11), não rotina.
- **Fonte do arquivo varia:** MF e ES2 = **M365** (API Moodle não pega) → `moodle_label`/
  instancename pode FALTAR, `source_section` vem da PASTA (M365/Desktop dump). IA/TCC/SO =
  Moodle (têm `moodle_label`). → os sinais disponíveis mudam por curso.
- **`sessions[].label` do SARC (data→tópico) existe em TODOS** — é o sinal fino universal
  (vem do SARC). Subutilizado hoje.
- **OpenSarc** (reserva de sala/lab) = IGNORAR por hora.

## Arquitetura — 3 contratos + tiers

### Contrato 1 — WindowProvider (CASCATA de providers; o "container")
```
WindowProvider(entry, ctx) -> list[block_ref]    # 1º provider que rende janela não-vazia; [] = sem janela
```
Tentados em ordem de CONFIABILIDADE (cada um opcional; usa o sinal que TIVER):
```
P1  card-window MANUAL (card_block_map source=manual)       -> janela          [verdade humana]
P2  card_block_map LABELS datado (parse_card_dates A–D)      -> janela          [IA; MF]
P3  DATA-no-nome do arquivo -> data SARC -> bloco            -> janela ~1       [SO forte; IA parcial]
P4  TÓPICO-do-card ↔ block.topic_text / sessions[].label    -> janela p/ tópico [TCC]
senão                                                        -> []  (funil-piso)
```
- **`block_ref` = `bloco-NN` (display id)**, NÃO uuid. Resolução p/ `block_uuid` é downstream
  via `lookup_card_blocks` (`src/builder/timeline/card_block.py`) — mesmo caminho do pipeline.
- **Janela grossa é legítima** (ES2: card "Microsserviços" = 10 blocos) — o Disambiguator
  carrega a carga. Janela tight (IA week-card) → pouca desambiguação. (D7)
- **Invariante:** janela `[]` → o motor NÃO ancora → funil-piso (`computed`). Material COM
  janela NUNCA escapa dela.
- **NÃO filtra por `kind`** (D2-soft): o conteúdo evita admin sozinho no Disambiguator.
- **NÃO usa week-math ordinal-linear** (F-TCC: drifta 2-3 blocos por feriado/recesso). Ordinal
  é sinal SOFT do Disambiguator, nunca provider de janela.

### Contrato 2 — Disambiguator (escolha DENTRO da janela; COMPARTILHADO)
```
Disambiguator(entry, window, ctx) -> (block_ref, conf: float, band: str, flag: bool)
```
`band ∈ {"alta","media","baixa",""}` — REUSA `computed_block_band` via
`thresholds.confidence_band`, não inventa rótulo. Só roda se `|window| > 1`. Cadeia por
DISPONIBILIDADE (D3):
```
|window| == 1  -> coloca direto (8/8 trivial no MF)
senão, em prioridade:
  0. DATA-no-nome ∩ sessions[].date (ou period_start..end)              [determinístico forte]
  1. CONTENT ↔ SESSION-TOPIC: conteúdo ∩ sessions[].label (data→tópico SARC, FINO)  <-- 1ª classe
       + CONTENT ↔ block.topic_text (SARC, agregado/GROSSO)             [fallback coarse]
       + score_lesson_match(lessons_index) quando há roteiro             [MF]
  2. scorer-BOUNDED na janela (reusa primitivas)                        [resíduo]
  3. ordinal-no-nome (Aula NN)                                          [desempate SOFT, TCC/ES2]
  4. bloco class mais cedo da janela + FLAG                             [último]
```
- **`sessions[].label` (data→tópico do SARC) é PRIMEIRA-CLASSE**, acima de `block.topic_text`
  (que é agregado/grosso). Probes: rescatou TCC-S10 (topic_text="para" genérico, session-label
  "revisao para prova p1" casou) e é o lever fino do ES2 (microsserviços espiral). Schema:
  `sessions` carrega `label`/descrição além de `date`.
- Admin (`evento academico`/`devolucao`/`Conteúdo: unidade-XX`) **perde sozinho** no conteúdo;
  `kind` = desempate SOFT só no caso silencioso/fraco (D2-soft).
- **Gate de margem (D4):** confiante = best supera runner-up por ≥1 token discriminante → band
  `alta`, ancora. Empate/silêncio → ancora no melhor MAS band `baixa` + **FLAG**. Sinais que
  concordam (data-no-nome + topic) → `alta`; discordam → FLAG. Valor calibrado no golden MF (TDD).
- **Teto conhecido:** matching determinístico por token **plateia ~57–65%** no multi-bloco; o
  resíduo é SEMPRE **same-theme** (Dafny / NP-completude / microsserviços espiral). Subir o teto
  = TIER 3 LLM. Isto é EVIDÊNCIA, não bug.

### Contrato 3 — AnchorEngine (orquestra tiers; ANCHOR-ONLY)
```
AnchorEngine.resolve(entry, ctx) -> AnchorResult | None      # None = sem âncora -> funil
```
```
TIER 1  pino manual (entry.manual_timeline_block_id válido)  -> bloco final, FIM   (D1)
TIER 2  roteamento por CATEGORIA (D6):
          trabalho / codigo-* com assign_due
            -> janela-de-prazo (blocos period_start < assign_due; ASSIGN_WINDOW_CATEGORIES)
          revisão + prova (nome casa "revis" + P1/P2/PS/...)
            -> bloco de revisão (review_list_block_for_entry; conf 0.95)
          senão
            -> WindowProvider(cascata) -> (Disambiguator se |janela|>1) -> temporal (ANCHOR-ONLY)
               gate D4: band alta ancora; empate/silêncio -> ancora + FLAG
TIER 3  se FLAGGED -> voto LLM (Gemini, cacheado) -> ainda incerto -> FLAG humano   (D8)
```
- O due NUNCA decide sozinho (janela-de-prazo é conjunto, não escolha).
- Categoria (D6) corta resíduo: no SO, parte dos ~55% sem-data são trabalho/revisão/plano →
  roteados por categoria, não falha de disambiguação.
- `AnchorResult` reusa/estende o dataclass atual (`anchor_placement.py:77`): `block_uuid`,
  `method`, `section`, `window_start/end`, `changed` — + `band`/`flag`/`provider` para D4.

### Dois grãos de correção manual (D1; escotilha rara, durável)
```
1. pino por-material (manual_timeline_block_id) -> conserta DESAMBIGUAÇÃO ou SEM-janela  [cirúrgico]
2. card-window MANUAL (card_block_map source=manual) -> conserta a JANELA (container)    [coarse]
```
Corrige no grão mais COARSE que resolve o erro. Ambos `source=manual` → sobrevivem reprocess.
Métrica de sucesso = **quão POUCOS** manuais são precisos.

## Mapa de WindowProvider por curso (instâncias concretas da cascata)

| Curso | Fonte | Provider PRIMÁRIO | card_block_map | Resíduo (→ D8) |
|---|---|---|---|---|
| IA | Moodle | P2 card_block_map datado (data-de-seção) | popula | seção≈1 bloco (degenerado) |
| MF | M365 | P2 + roteiro (data→tópico) | popula | Dafny same-theme |
| TCC | Moodle | P1 (5 pinos) + **P4 tópico** (labels vazia) | só manual | NP-completude (Cook-Levin) |
| ES2 | M365 | P2 grosso (1 card=10 blocos) + **session-label** | popula grosso | microsserviços espiral |
| SO | Moodle | **P3 data-no-nome** (45%, 1:1, 0 colisão) | VAZIA | sem-data: categoria D6 / topic fraco |

## Invariantes ANCHOR-ONLY (não-negociáveis)

- Escreve **só `temporal_block_id`** (+ method/band/flag). NUNCA toca `computed_block_id`
  (funil = piso) nem `manual_timeline_block_id` (D0/D9).
- Cascata efetiva: **`temporal > manual > computed`** (`resolve_temporal_block`,
  `file_map.py:617`).
- Material sem janela → `None` → funil-piso. **Nunca** scorer desbounded fora da janela.
- Disambiguator NUNCA sai da janela. Sinal apontando FORA da janela = possível mis-file → FLAG.
- Lógica nova em `src/builder/routing/`, **NUNCA** em `engine.py` (facade). Imports focados.
- LLM (TIER 3) = `google-genai` (`from google import genai`), **lazy dentro do método**,
  background-thread. Proibido: `google.generativeai` / `genai.GenerativeModel`.
- Tudo que CC roda sozinho é **READ-ONLY**. Escrever temporal = reprocess = ação do USER na GUI.
  **NÃO commitar.**

## Critérios de aceite POR TIER (verificáveis)

| Tier / componente | Critério de aceite (verificável) |
|---|---|
| WindowProvider P1/P2 (IA, MF) | `WindowProvider(entry) ⊇ {bloco-verdade}` em **100%** dos golds (reproduz C1). Janela vazia ⇒ `[]`. |
| WindowProvider P3 (SO date-in-name) | Cada material datado → data → **exatamente 1 bloco** (probe: 9/9 sem colisão). Cobre ~45% dos materiais SO. |
| WindowProvider P4 (TCC tópico) | Reproduz ≥4/5 pinos manuais via topic-match (probe); o resíduo (NP-completude) cai pro D8, NÃO erra confiante. NUNCA usa week-math (F-TCC). |
| Disambiguator `|janela|==1` | Coloca o único bloco; 0 FLAG. (MF: 8/8.) |
| Disambiguator `|janela|>1` | Sem-regressão vs gold MF: `multi CERTO ≥ baseline` (fusão completa = 22/38). `confiante-errado` (band alta + errado) = **0** (C2). Session-label deve ≥ block.topic_text no multi-bloco. |
| Gate D4 | Todo caso errado/empate → band baixa + FLAG (nenhum erro confiante escapa). Calibrado no golden MF. |
| TIER 1 (pino) | `manual_timeline_block_id` válido ⇒ bloco final, sem TIER 2/3. Sobrevive reprocess. |
| TIER 2 categoria | trabalho/codigo+due ⇒ janela-de-prazo; revisão+prova ⇒ `review_rule` (0.95). Reusa S5/review. |
| TIER 3 (LLM) | Só no conjunto FLAGGED. Cap=20. Voto cacheado em `material_curation.json`; reprocess REUSA. |
| ANCHOR-ONLY | Flag-OFF ⇒ saída byte-idêntica ao funil atual. Flag-ON ⇒ `computed` inalterado; só `temporal_*`. |

## Eval-gate

- **Sem-regressão** vs gold — NÃO byte-paridade com o anchor velho (o Disambiguator PODE
  MELHORAR). Golds reais: IA `docs/reports/ground_truth_IA.csv`, MF
  `tests/fixtures/eval/metodos_formais_golden.json`.
- Troca do motor ⇒ **re-baseline consciente** de `test_caracterizacao`. `test_anchor_placement`/
  `test_temporal_block_wire` substituídos pelos do motor novo (TDD).
- `pytest -q` verde; golden/eval sem drift inexplicado.
- **MARCO 1 (gate-0, ANTES de construir o motor inteiro):** rodar Gemini no conjunto FLAGGED do
  MF (≤20 chamadas) e **medir o lift** sobre o teto determinístico ~65%. Se o voto resolve a
  série same-theme (ExerciciosDafny OO → bloco-15), D8 segura. Senão, repensar TIER 3. Barato e
  decisivo. (O mesmo padrão same-theme aparece em TCC NP-completude e ES2 microsserviços → o
  lift do MF generaliza.)

## Mapa de reúso (âncoras CONFIRMADAS)

REUSAR (espinha):
- WindowProvider: `derive_card_block_map:152`, `parse_card_dates:232`,
  `build_lesson_topic_index:253` (`src/builder/sources/moodle_labels.py`);
  `load_card_block_map`, `lookup_card_blocks`, `lookup_card_assign_due`
  (`src/builder/timeline/card_block.py`).
- Disambiguator scoring (PURO): `concept_token_weights:136`, `concept_vector:160`,
  `score_lesson_match:106` (`concept_resolver.py`). **Session-topic:** minerar `sessions[].label`
  do `.timeline_index.json` (data→tópico) — novo consumidor, sinal já presente.
- Band/threshold: `confidence_band` (`thresholds.py`) — `alta/media/baixa`.
- Sinais: `collect_entry_unit_signals:80` (`entry_signals.py`), `assemble_resolver_inputs:65`
  (`resolver_apply.py`). **Data-no-nome:** extrator DD.MM do title/`moodle_label`/`source_path`
  (forte no SO).
- Categoria (D6): `ASSIGN_WINDOW_CATEGORIES:29`, `review_list_block_for_entry:949`
  (`content_taxonomy.py`); `lookup_card_assign_due:189` (`card_block.py`).
- kind (D2-soft): `BlockKind` (`kinds.py:17`), `_aggregate_source_kind:258` (`index.py`).
- Cascata: `resolve_temporal_block:617` (`file_map.py`).
- Voto LLM (TIER 3): `run_material_residual:44` (`pedagogical_regeneration.py`) →
  `summarize_residual_materials:61` (`summary_core.py`).
- Flag por-curso: `SubjectProfile.feature_flags:244` (`core.py`).
- Base a evoluir: `resolve_placement:258`, `apply_anchor_placement:344`, `AnchorResult:77`
  (`anchor_placement.py`).

SUBSTITUIR: call-site passo 5 `pedagogical_regeneration.py:381` (gate `use_anchor_placement`).

NÃO reusar (overwrite/apply): `resolve_material_assignment:256` e
`resolver_apply.apply_concept_resolver` — aplicam/sobrescrevem unidade. Reusar SÓ scoring puro;
o motor escreve temporal.

### Correções de precisão ao handoff
1. Cache do voto-material = **`material_curation.json`** (não `code_curation.json`; esse é o
   voto de código). TIER 3 usa o de material.
2. Anchor atual parseia só "Semana N" (`_SEMANA_RE`) → o motor generaliza para a cascata.
3. `ASSIGN_WINDOW_CATEGORIES` hoje = `frozenset({"trabalhos"})` (+ `codigo-*` com assign_due).
   Extensível; sem hardcode de cadeira.

### Schemas confirmados (aterram contratos + fixtures de TDD)
- **Entry** (`FileEntry`, `core.py:39`): lê `source_section`, `category`, `title`,
  `manual_timeline_block_id`, sinais (`moodle_label` — **pode faltar em M365/MF/ES2**, markdown);
  escreve só `temporal_block_id`/`temporal_block_method`. `computed_*` = piso.
- **Block** (`schemas/timeline_index.v4.json`): `id` (`bloco-NN`) + `block_uuid`; `topic_text`
  (SARC "Atividade", agregado), `period_start`/`period_end`, **`sessions:[{date, label, …}]`**
  (label = data→tópico, FINO — corrige leitura anterior que via só `{date}`), `kind` (15),
  `primary_topic_label`.
- **card_block_map** (`course/.card_block_map.json`): `{source_section_normalizado:
  {block_ids:[bloco-NN], source: manual|labels|inferred, format?, dates?, assign_due?}}`. Chave
  normalizada NFKD+lower+sem-acento. **Pode ser vazio (SO) ou grosso (ES2).**

## Rollout (D10) — ajustado pelos probes

1. **IA + MF** (P2 card-window + gold) — provam o core. IA é o caso degenerado; MF exercita
   roteiro + same-theme (Dafny) → primeiro teste do D8.
2. **SO** (P3 data-no-nome + categoria D6) — determinístico forte (45% 1:1), topic-fallback
   fraco; precisa de gold antes de confiar (provider novo).
3. **TCC** (P4 topic-bridge) — wiring do provider de tópico; ordinal só soft. Resíduo
   NP-completude → D8.
4. **ES2** (P2 grosso + session-label) — disambiguação mais pesada (janela enorme + same-theme);
   maior dependência de D8.

Feature-flag por-curso (`SubjectProfile.feature_flags`). UI de revisão = Timeline Dashboard
EXISTENTE (override + badges); sem UI nova. Reprocess re-renderiza artefatos; atualizar
`docs/Overview-Sistema.html` + `pendencias.md`.

## Cross-check = detector de ANOMALIA-DE-DADO (D11; não audita janela)

Auditar janela = 11/11 falso-alarme (C1=100%). O cross-check (`scripts/crosscheck_IA.py`,
read-only) só vale no SEM-janela: placement que discorda de sinal independente = duplicata/
mis-file/arquivo-stale-do-semestre-passado. Alimenta correção de DADO do humano, NÃO flag de
rotina. Valor LIMITADO; leve. Rotina ≠ cross-check (rotina = D4 → D8 → pino).

## Non-goals

- NÃO reescrever o funil (`computed` = piso para sem-janela).
- **Frequência de aula** = UPSTREAM (duplica o sinal de data). Em ES2 (1x/sem) o ordinal ≈
  semana 1:1, mas isso é sinal soft, não core.
- **Granularidade de bloco** = UPSTREAM (block-splitting); o motor herda a grossura.
- **week-math ordinal-linear** = PROIBIDO como provider (F-TCC drift).
- Sem hardcode de cadeira. Só providers/extratores genéricos + pesos.
- OpenSarc, plano de ensino (tópico→semana), ordinal-extração refinada = fases posteriores.

## Decisões abertas (pro implementador; calibração no TDD)

- **Gate D4** (≥0.5 roteiro-score? band-cap?) — tracejar no golden MF.
- **Pesos da fusão** (concept-IDF vs session-label vs block.topic_text vs date-no-nome) —
  session-label deve pesar mais que block.topic_text (fino > grosso); fixtures reais.
- **TCC P4:** limiar do topic-match; quando cair direto no D8 (NP-completude-like).
- **ES2:** janela grossa (10 blocos) — confiar no session-label ou escalar D8 mais cedo?
- **SO P3:** granularidade — data cai em bloco de range largo (1 dia vs semana); risco de
  bloco grosso (UPSTREAM).
- Onde mora `band`/`flag`/`provider` no `AnchorResult` e como serializam pro Dashboard.

## Rastreio D0–D12 → requisito do spec

| Decisão | Onde no spec |
|---|---|
| D0 plugável mode-aware | Constatação central; Contratos 1–3; Mapa de Providers |
| D1 dois grãos de manual | "Dois grãos"; TIER 1; WindowProvider P1 |
| D2 kind SOFT | Contrato 1 (não filtra); Contrato 2 (admin perde sozinho) |
| D3 cadeia por disponibilidade | Contrato 2 (cadeia 0–4); Contrato 1 (cascata P1–P4) |
| D3-ajuste teto ~65% | Contrato 2 ("teto"); Eval-gate MARCO 1 |
| D4 gate de margem | Contrato 2; critério "Gate D4" |
| D5 window-source | Constatação central; Contrato 1 (cascata — refina "card_block_map universal") |
| D6 category-aware | Contrato 3 TIER 2; critério categoria |
| D7 estilo por-professor | Contrato 1 (tight/loose); Mapa de Providers |
| D8 escalada por custo / LLM | Contrato 3 TIER 3; MARCO 1; resíduo same-theme universal |
| D9 integração ANCHOR-ONLY | Invariantes; Mapa de reúso; Eval-gate |
| D10 rollout + providers | Mapa de Providers; seção Rollout |
| D11 cross-check | seção Cross-check |
| D12 estratégia de gold | Eval-gate; Rollout; Restrições de Plataforma (SARC cedo) |

### Refinamentos pós-probe (2026-06-29) — ver log de decisões
- **F-TCC:** week-math ordinal-linear DRIFTA → TCC usa P4 topic-bridge (refina D5/D10).
- **Restrições de plataforma:** SARC cedo+por-aula; Moodle incremental; M365 sourcing (refina D12).
- **Mapa de Providers:** card_block_map não é universal → WindowProvider = cascata (refina D5).
- **Session-label first-class:** sinal universal subutilizado (refina D3).

## Próximo passo

Spec → **plano de implementação** (skill `writing-plans`, fases TDD): (0) MARCO 1 prova-LLM →
(1) WindowProvider cascata (P1/P2) + Disambiguator (session-label first-class) read-only vs gold
MF → (2) gate D4 calibrado → (3) escalada LLM D8 wiring+cache → (4) integração D9 (substitui
`apply_anchor_placement`, funil intacto) → (5) rollout D10 (IA/MF → SO → TCC → ES2). Depois:
execução SubAgent-Driven.
