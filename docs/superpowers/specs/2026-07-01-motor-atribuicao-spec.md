# AnchorEngine — Spec do Motor de Atribuição material→bloco

date: 2026-07-03 (nome do arquivo conforme handoff de partida)
status: SPEC (consolidação final pré-plano)
supersede: `docs/superpowers/specs/2026-06-29-motor-atribuicao-design.md` (rev 2026-06-29b — pré-MARCO)
fontes: log de decisões `docs/reports/2026-06-28-motor-atribuicao-decisoes.md` (D0–D13, F-MF, F-TCC,
Restrições de Plataforma, Mapa de Providers, SÍNTESE, "Validação EXECUTADA" no D8),
handoff `docs/reports/2026-07-01-handoff-spec-motor.md` (§4 = achados medidos),
revisão de sincronização 2026-07-03 (itens 1–12, incorporados na seção "Resoluções da revisão"),
tracker `docs/reports/pendencias.md`.

> Este spec NÃO re-decide D0–D13. Consolida decisões + medições (MARCO 0/1) em requisitos
> VERIFICÁVEIS para o plano (`writing-plans`) e execução SubAgent-Driven. Cada requisito
> rastreia a decisão/medição de origem. Diferenças vs design 06-29b estão marcadas **[Δ]**.

---

## 1. Problema

Atribuir `material → bloco da timeline` em 5 cursos com sinais organizadores E fontes
heterogêneas: IA = data-de-seção (Moodle); MF = unit-card + roteiro interno (M365); TCC =
"Semana N - Tópico" sem data (Moodle); ES2 = card grosso 1x/sem (M365); SO = unit-card sem
roteiro mas com data-no-nome (Moodle). O `anchor_placement` atual é IA-only (`_SEMANA_RE`);
os outros 4 cursos caem no funil-chute (`computed`, scorer).

Regra não-negociável do user: **correção GERAL na raiz, nunca fix por cadeira** → motor
plugável mode-aware que usa o sinal DISPONÍVEL de cada curso e degrada honestamente (flag).

## 2. Régua oficial e critério de DONE  **[Δ — substitui o Eval-gate do design]**

Eval oficial = `eval_ground_truth` com **colapso de par (`pair_key`)**, gold human-confirmado
nos 5 cursos, HALTs com sign-off. Baselines as-of 2026-07-01 (o que o motor tem que bater):

| Curso | Baseline | Assinatura do erro hoje |
|---|---|---|
| IA | **86.4%** (38/44) | 6/6 off-by-one de fronteira; única com âncora ligada |
| MF | **63.6%** (42/66) | 12/24 adjacente; 1 órfão |
| TCC | **56.0%** (14/25) | pós-poda; re-referenciado |
| ES2 | **50.0%** (14/28) | 12/14 miss de tópico |
| SO | **47.4%** (18/38) | 17/20 miss de tópico; band alta = moeda ao ar |

- **DONE = sem-regressão vs gold em TODOS; IA não pode cair.** NÃO é byte-paridade com o
  anchor velho (o Disambiguator PODE melhorar).
- Réguas de DEV auxiliares (unit-level, não governam aceite): golden MF 48 casos
  (`tests/fixtures/eval/metodos_formais_golden.json`, F-MF) e sidecars do MARCO
  (`marco0_flagged_MF.json`, `marco1_votes_MF.json`).
- Pisos medidos de referência (MARCO 0/1, escopo-disamb MF): determinístico com len-norm
  **59.7%**; com voto LLM no flagged **66.1%** (empata com o funil). São PISOS de probe
  (tokenizer cru, sem concept-IDF real) — o motor real deve ≥.
- **MARCO 0/1 NÃO se repetem.** Provas executadas e cacheadas; scripts em
  `scripts/marco0_prova_deterministica.py` / `scripts/marco1_voto_llm.py` ficam como
  referência reproduzível. **[Δ item 1 da revisão — design listava MARCO 1 como pendente]**
- Troca do motor ⇒ re-baseline CONSCIENTE de `test_caracterizacao`;
  `test_anchor_placement`/`test_temporal_block_wire` substituídos pelos testes do motor (TDD).
- Fragilidade conhecida do eval: `eval_ground_truth` é keyed-por-id (colisão nova = linha
  some silenciosa). Guard-rail barato no plano: assert de unicidade de id no load.

## 3. Arquitetura — 3 contratos + tiers

### Contrato 1 — WindowProvider (CASCATA de providers; o "container")

```
WindowProvider(entry, ctx) -> list[block_ref]   # 1º provider que rende janela não-vazia; [] = sem janela
```

Tentados em ordem de CONFIABILIDADE (cada um opcional; usa o sinal que TIVER):

```
P1  card-window MANUAL (card_block_map source=manual)      -> janela           [verdade humana]
P2  card_block_map LABELS datado (parse_card_dates A–D)    -> janela           [IA; MF; ES2 grosso]
P3  DATA-no-nome do arquivo -> data SARC -> bloco          -> janela ~1        [SO forte; IA parcial]
P4  TÓPICO-do-card ↔ block.topic_text / sessions[].label   -> janela p/ tópico [TCC; SO fallback]
senão                                                      -> []  (funil-piso)
```

- `block_ref` = `bloco-NN` (display id), NÃO uuid. Resolução downstream via
  `lookup_card_blocks` (`src/builder/timeline/card_block.py`).
- Janela grossa é legítima (ES2: 1 card = 10 blocos) — Disambiguator carrega a carga (D7).
- **Invariante:** janela `[]` → motor NÃO ancora → funil-piso. Material COM janela NUNCA
  escapa dela.
- **NÃO filtra por `kind`** (D2-soft): conteúdo evita admin sozinho.
- **NÃO usa week-math ordinal-linear** (F-TCC: drifta 2-3 blocos por feriado/recesso =
  confident-wrong, pior que vazio).
- **[Δ item 5/§4.5] WindowProvider por curso é 1ª CLASSE, não rollout tardio.** Cobertura de
  card-window hoje: IA 90% · MF 90% · ES2 86% · **TCC 26%** · **SO 0%**. Sem P3/P4 próprios,
  o motor vira funil para ~62 materiais. Providers SO/TCC entram como fase própria ANTES da
  escalada LLM (ver §7 Fases).
- **[Δ item 9] TCC = P4 topic-bridge, NÃO parse ordinal.** A frase do handoff §4.5 ("TCC
  parse 'Semana N'") lê-se: parsear o TÓPICO do card "Semana N - Tópico" e casar com
  `block.topic_text` + `sessions[].label` (F-TCC: 4/5 determinístico; resíduo NP-completude
  → TIER 3). O "N" ordinal NUNCA vira janela.

### Contrato 2 — Disambiguator (escolha DENTRO da janela; COMPARTILHADO)

```
Disambiguator(entry, window, ctx) -> (block_ref, conf: float, band: str, flag: bool)
```

`band ∈ {"alta","media","baixa",""}` — reusa `confidence_band` (`thresholds.py`). Só roda se
`|window| > 1`. Cadeia por DISPONIBILIDADE (D3):

```
|window| == 1 -> coloca direto (8/8 trivial no MF)
senão, em prioridade:
  0. DATA-no-nome ∩ sessions[].date (ou period_start..end)               [determinístico forte]
  1. CONTENT ↔ SESSION-TOPIC: conteúdo ∩ sessions[].label (FINO, 1ª classe)
       + CONTENT ↔ block.topic_text (agregado, fallback GROSSO)
       + score_lesson_match(lessons_index) quando há roteiro              [MF]
  2. scorer-BOUNDED na janela (reusa primitivas concept_resolver)         [resíduo]
  3. bloco class mais cedo da janela + FLAG                               [último]
```

- **[Δ item 2/§4.1] len-norm OBRIGATÓRIO no scoring:** score de assinatura de bloco
  normalizado por `sqrt(|assinatura|)`. Medido: **+6.5pp grátis** (53.2→59.7% escopo MF);
  o "sumidouro bloco-11" era assinatura verbosa, não semântica.
- **[Δ item 13/§4.4] Ordinal-no-nome DEMOVIDO da cadeia.** MARCO 0: prior linear = lift
  ZERO; DP-monotone = lift NEGATIVO (importa erro do vizinho). NÃO implementar como sinal de
  posição. Fica fora do core; candidato a tie-break soft SÓ se sobrar tempo, nunca base.
  (Design 06-29b o tinha como passo 3 da cadeia — removido.)
- **`sessions[].label` (data→tópico do SARC) é PRIMEIRA-CLASSE**, acima de `block.topic_text`
  (agregado/grosso). Probes: rescatou TCC-S10; lever fino do ES2.
- Admin (`evento academico`/`devolucao`/`Conteúdo: unidade-XX`) perde sozinho no conteúdo;
  `kind` = desempate SOFT só no caso silencioso/fraco (D2-soft). Hard-drop só placeholder
  inequívoco.
- **[Δ §4.6] Lesson-matching FINO é requisito, não nice-to-have:** o caso-alvo herdado do A1
  — card "Verificação de Programas" MF (14 lessons, blocos 10-15; hoare, tiposindutivos,
  dafny1-2) — vira FIXTURE NOMEADA do aceite. O probe usou roteiro cru; o motor usa o
  scoring IDF real do `concept_resolver` bounded à janela.
- **Gate de margem (D4):** confiante = best supera runner-up por ≥1 token discriminante →
  band `alta`, ancora. Empate/silêncio → ancora no melhor MAS band `baixa` + FLAG. Sinais
  concordam (data-no-nome + topic) → `alta`; discordam → FLAG. Valor calibrado no gold MF (TDD).
- **[Δ item 4/§4.2] Gate D4 = LEVER DOMINANTE, fase com número próprio.** MARCO 1: proxy
  τ=0.25 pegou só 15/26 erros; **11 confiante-e-errado ficaram CEGOS pro LLM**. A fase do
  gate entrega **recall medido do gate** (fração dos erros reais que ganham FLAG), não só
  o threshold. Ver §7 fase 1 e §6 aceite.
- Teto conhecido: matching determinístico plateia ~57–65% multi-bloco; resíduo é SEMPRE
  same-theme (Dafny / NP-completude / microsserviços). Subir teto = TIER 3. Evidência, não bug.

### Contrato 3 — AnchorEngine (orquestra tiers; ANCHOR-ONLY)

```
AnchorEngine.resolve(entry, ctx) -> AnchorResult | None    # None = sem âncora -> funil
```

```
TIER 0  DUP-GROUPING [Δ item 6/§4.7]: md5-gêmeos (pair_key) = UMA decisão
          resolve 1 representante -> propaga temporal_block_id ao(s) gêmeo(s)
TIER 1  pino manual (entry.manual_timeline_block_id válido) -> bloco final, FIM   (D1)
TIER 2  roteamento por CATEGORIA (D6):
          bibliografia / references / cronograma [Δ item 7/§4.8]
            -> FORA do motor: funil-piso direto, NUNCA disambiguator, NUNCA voto LLM
               (MARCO 1: 0/3, chamada desperdiçada; classe = refatoração de ingestão futura)
          trabalho / provas / codigo-* com assign_due / seção TDE [§4.9]
            -> janela-de-prazo (blocos period_start < assign_due; ASSIGN_WINDOW_CATEGORIES,
               S5 EXISTE). Due NUNCA decide sozinho. NUNCA entram no disambiguator.
               (Prova da necessidade: T1/T2 MF têm temporal ERRADO hoje — bloco-05/02 vs
               true 15/16; a janela-de-prazo é quem resolve.)
          revisão + prova (nome casa "revis" + P1/P2/PS/...)
            -> bloco de revisão (review_list_block_for_entry; conf 0.95)
          senão
            -> WindowProvider(cascata) -> (Disambiguator se |janela|>1) -> temporal
               gate D4: band alta ancora; empate/silêncio -> ancora + FLAG
TIER 3  escalada LLM (D8-refinado) [Δ item 3/§4.3]:
          escopo = FLAGGED ∪ membro de SÉRIE SAME-THEME (não só flagged)
          voto Gemini (gemini-2.5-flash via get_gemini_client; google-genai lazy;
          background-thread; CACHEADO) -> ainda incerto -> FLAG humano
```

- `AnchorResult` reusa/estende o dataclass atual (`anchor_placement.py:77`): `block_uuid`,
  `method`, `section`, `window_start/end`, `changed` — + `band`/`flag`/`provider`.
- Dois grãos de correção manual (D1): pino por-material (conserta desambiguação/sem-janela)
  e card-window manual (conserta a janela). Corrige no grão mais COARSE que resolve. Ambos
  `source=manual` → sobrevivem reprocess. Métrica de sucesso = quão POUCOS manuais.

### Regras do voto LLM  **[Δ item 12 — regra de aceitação explícita]**

1. **Autoconfiança do LLM é IGNORADA como sinal** (MARCO 1: "alta" 18/18, acertou 8).
   Nenhum gate lê a confiança reportada.
2. **Voto BOUNDED à janela:** voto fora da janela = inválido → mantém FLAG (não ancora).
3. **Aceitação:** voto válido no escopo (flagged ∪ same-theme) SUBSTITUI a escolha
   determinística e ancora com band `media` + marca `provider=llm`. (Regra provada no
   MARCO 1: aceitar cego deu +5/18 sem novo confident-wrong dentro do escopo.)
4. Classe que o voto converte: confusão-semântica (sintaxe/semântica 4/4, isabelle2,
   plano→bloco-01). Classe que NÃO converte: grão-de-semana same-theme (Dafny1, indução
   05↔06) — essa fica FLAG → humano. Não gastar iteração tentando prompt-engineer isso.
5. **Cache:** votos de material em `material_curation.json` **[Δ item 10 — NÃO
   `code_curation.json`, que é o voto de código]**; prune stale + write atomic; reprocess
   REUSA voto, só material novo/alterado chama API. **Chave do cache = identidade de
   conteúdo (md5/pair_key), não entry-id** — gêmeos compartilham 1 voto (coerente com
   TIER 0). Votos do MARCO 1 (`marco1_votes_MF.json`) são importáveis como seed do cache.
6. Cap=20 por reprocess (orçamento existente); opt-in por flag de curso.

## 4. Invariantes ANCHOR-ONLY (não-negociáveis)

- Escreve **só `temporal_block_id`** (+ method/band/flag). NUNCA toca `computed_block_id`
  (funil = piso) nem `manual_timeline_block_id`. Cascata: `temporal > manual > computed`
  (`resolve_temporal_block`, `file_map.py:617`).
- Material sem janela → `None` → funil-piso. NUNCA scorer desbounded fora da janela.
- Disambiguator NUNCA sai da janela; sinal apontando fora = possível mis-file → FLAG.
- Lógica nova em `src/builder/routing/`, **NUNCA** `engine.py` (facade).
- LLM = `google-genai` (`from google import genai`), lazy dentro do método,
  background-thread. Proibido `google.generativeai`/`genai.GenerativeModel`.
- md5-gêmeos recebem o MESMO `temporal_block_id` (TIER 0) — dup-divergence medida (TCC
  aula-06 em 3 blocos; SO plano/programa PASS/FAIL) não pode reaparecer.
- Tudo que CC roda sozinho é READ-ONLY nos repos-tutor. Escrever temporal = reprocess =
  ação do USER na GUI. NÃO commitar sem pedido explícito.

## 5. Mapa de WindowProvider por curso (instâncias da cascata)

| Curso | Fonte | Provider PRIMÁRIO | Cobertura card-window hoje | Resíduo (→ TIER 3) |
|---|---|---|---|---|
| IA | Moodle | P2 datado (data-de-seção) | 90% | degenerado (seção≈1 bloco) |
| MF | M365 | P2 + roteiro (data→tópico) | 90% | Dafny same-theme |
| ES2 | M365 | P2 grosso + session-label | 86% | microsserviços espiral |
| TCC | Moodle | P1 (5 pinos) + **P4 tópico** | **26%** | NP-completude (Cook-Levin) |
| SO | Moodle | **P3 data-no-nome** (45% 1:1, 0 colisão) | **0%** | sem-data: categoria D6 / topic fraco |

Sinais por disponibilidade: data-de-seção=IA · roteiro-no-card=MF · data-no-nome=SO(forte)/
IA(parcial) · tópico-do-card=TCC · **session-label-SARC=TODOS** (universal, subutilizado).

## 6. Critérios de aceite (verificáveis; contenção E cobertura)  **[Δ item 11]**

O design 06-29b só media CONTENÇÃO (verdade ∈ janela). Aceite agora tem DUAS métricas por
provider — contenção sem cobertura = motor-funil disfarçado:

| Componente | Contenção (verdade ∈ janela) | Cobertura (materiais com janela) |
|---|---|---|
| P1/P2 (IA, MF, ES2) | 100% dos golds (reproduz C1) | ≥ medido hoje (IA 90 · MF 90 · ES2 86%) |
| P3 (SO data-no-nome) | data → exatamente 1 bloco (9/9 probe, 0 colisão) | ~45% dos materiais SO |
| P4 (TCC tópico) | ≥4/5 pinos manuais reproduzidos; resíduo cai pro TIER 3, NÃO erra confiante | >26% (supera o só-manual) |

| Tier / componente | Critério |
|---|---|
| Disambiguator `janela=1` | coloca o único bloco; 0 FLAG (MF 8/8) |
| Disambiguator `janela>1` | escopo-disamb MF ≥ **59.7%** (piso MARCO 0 com len-norm); `confiante-errado` (band alta + errado) = **0**; session-label ≥ block.topic_text no multi-bloco; fixture nomeada "Verificação de Programas" (blocos 10-15) melhora vs baseline |
| Gate D4 | **RECALL DO GATE medido e reportado** (fração dos erros reais flagados); meta: nenhum erro confiante escapa nos golds; calibrado no gold MF |
| TIER 0 (dup) | 0 dup-divergence: todo grupo md5/pair_key com temporal idêntico |
| TIER 1 (pino) | pino válido ⇒ bloco final, sem TIER 2/3; sobrevive reprocess |
| TIER 2 categoria | trabalho/prova/TDE+due ⇒ janela-de-prazo (T1/T2 MF: bloco 15/16 corretos); revisão ⇒ review_rule; bibliografia/apoio ⇒ funil direto, 0 chamada LLM |
| TIER 3 (LLM) | só escopo flagged∪same-theme; cap=20; voto bounded à janela; cache `material_curation.json` reusado no reprocess; autoconfiança nunca lida |
| ANCHOR-ONLY | flag-OFF ⇒ saída byte-idêntica ao atual; flag-ON ⇒ `computed` inalterado, só `temporal_*` |
| Eval final | sem-regressão vs gold 5/5 (pair_key); **IA ≥ 86.4%** |

## 7. Fases com número  **[Δ item 4 — ordem do handoff §6, substitui "Próximo passo" do design]**

Cada fase termina com métrica reportada contra a régua da §2; read-only até a fase 4.

```
FASE 0  Contratos + WindowProvider P1/P2 (card_block_map) + Disambiguator com len-norm
        e session-label 1ª classe. Provado READ-ONLY vs gold MF.
        + guard test de imports: pacote do motor PROIBIDO de importar condenados do cutover
        (block_token_weights, score_entry_against_timeline_block, select_probable_period_
        for_entry); whitelist: concept_resolver puro, card_block, thresholds, entry_signals,
        text/*. [revisão 03/07]
        Número: escopo-disamb MF ≥59.7%; contenção 100%; confiante-errado=0.
FASE 1  Gate D4 calibrado COM MEDIÇÃO DE RECALL (lever dominante).
        Número: recall do gate nos golds (referência ruim a bater: proxy 15/26).
        Decide: quanto do resíduo confiante-errado sobra pro escopo same-theme do TIER 3.
FASE 2  Providers P3 (SO) + P4 (TCC).  [promovida — era rollout tardio]
        Número: cobertura SO ~45% / TCC >26%, contenção conforme §6.
FASE 3  Escalada LLM (TIER 3). GATE DE ENTRADA [sign-off 03/07]: go/no-go do user
        pós-recall da fase 1 — LLM é opcional; sem ela, flagged = fila humana no Dashboard.
        Escopo ampliado, cache material_curation.json, seed dos votos MARCO 1.
        Número: lift ≥ +4 no flagged MF sem novo confiante-errado (era +5 no MARCO 1 cru;
        nas regras finais plano.pdf sem-janela não vota — ver §12).
        [REVISÃO 09/07, SIGN-OFF user] Piso revisado para ≥ +3 pós-medição: rodada mista
        (seed 2.5 + flash-latest) deu FAIL +1; experimento com gemini-3.5-flash PINADO
        (44 votos frescos, seed excluído) = lift +3, global 82.8%→87.9%, conf-errado 0.
        Variante flagged-only medida offline é PIOR (+2, conf-errado 1) — escopo
        flagged∪série confirmado ótimo. GO ACEITO com +3; LIFT_MIN=3 na régua.
FASE 4  Integração D9: AnchorEngine SUBSTITUI apply_anchor_placement
        (call-site pedagogical_regeneration.py:381), feature-flag por-curso, funil intacto.
        Número: flag-OFF byte-idêntico; flag-ON sem-regressão 5/5.
FASE 5  Rollout por curso (IA/MF → ES2 → SO → TCC, gold-gated) + CUTOVER FASE 3.4 do
        tracker (default ON concept_resolver + DELETE funil legado: score_entry_against_
        timeline_block S2/S4, select_probable_period, _best_instructional_block_fallback,
        2 rotas card). Deleção por LISTA NOMEADA [revisão 03/07] — sobrevivem
        score_card_evidence_against_entry + _score_block_date_match (usados pelo resolver
        vivo) e card_block.py inteiro; aposentar scripts/eval_assignments.py +
        retag_manifest.py no MESMO commit; pré-requisito: decisão cronograma_health da
        fase 4. 5 conflitos mapeados no tracker de pendências.
        Eval-gated. Re-baseline consciente de caracterização.
```

MARCO 0/1 NÃO são fases — já executados (§2).

## 8. Mapa de reúso (âncoras do design 06-29b, validadas então; plano re-verifica linhas)

REUSAR (espinha):
- WindowProvider: `derive_card_block_map:152`, `parse_card_dates:232`,
  `build_lesson_topic_index:253` (`src/builder/sources/moodle_labels.py`);
  `load_card_block_map`, `lookup_card_blocks`, `lookup_card_assign_due`
  (`src/builder/timeline/card_block.py`).
- Disambiguator scoring (PURO): `concept_token_weights:136`, `concept_vector:160`,
  `score_lesson_match:106` (`concept_resolver.py`) — **+ len-norm novo**. Session-topic:
  minerar `sessions[].label` do `.timeline_index.json` (novo consumidor, sinal presente).
- Band: `confidence_band` (`thresholds.py`). Sinais: `collect_entry_unit_signals:80`
  (`entry_signals.py`), `assemble_resolver_inputs:65` (`resolver_apply.py`). Data-no-nome:
  extrator DD.MM de title/`moodle_label`/`source_path`.
- Categoria (D6): `ASSIGN_WINDOW_CATEGORIES:29` (hoje `frozenset({"trabalhos"})`,
  extensível), `review_list_block_for_entry:949` (`content_taxonomy.py`).
- kind (D2-soft): `BlockKind` (`kinds.py:17`), `_aggregate_source_kind:258` (`index.py`).
- Cascata: `resolve_temporal_block:617` (`file_map.py`).
- Voto LLM: `run_material_residual:44` (`pedagogical_regeneration.py`) →
  `summarize_residual_materials:61` (`summary_core.py`); `get_gemini_client` (chave ✓).
- Flag por-curso: `SubjectProfile.feature_flags:244` (`core.py`).
- Base a evoluir: `resolve_placement:258`, `apply_anchor_placement:344`, `AnchorResult:77`
  (`anchor_placement.py`).

SUBSTITUIR: call-site passo 5 `pedagogical_regeneration.py:381` (gate `use_anchor_placement`).

NÃO reusar (overwrite/apply): `resolve_material_assignment:256`,
`resolver_apply.apply_concept_resolver` — aplicam/sobrescrevem unidade. Só scoring puro.

Schemas (aterram fixtures): `FileEntry` (`core.py:39` — `moodle_label` PODE FALTAR em
M365/MF/ES2); Block (`schemas/timeline_index.v4.json` — `sessions:[{date,label,…}]`);
`card_block_map` (`course/.card_block_map.json` — chave NFKD+lower+sem-acento; pode ser
vazio/grosso).

## 9. Resoluções da revisão 2026-07-03 — SIGN-OFF do user (2026-07-03): #9 e #11 APROVADAS; #10 e #12 APROVADAS CONDICIONAIS à fase 3 (go/no-go decidido pós-recall da fase 1)

| # | Conflito | Resolução adotada | Racional |
|---|---|---|---|
| 9 | handoff §4.5 "TCC parse 'Semana N'" vs F-TCC topic-bridge | **topic-bridge (P4)**; "parse" = extrair o TÓPICO do título do card | F-TCC falsificou week-math com drift medido 2-3 blocos |
| 10 | cache `code_curation.json` (D8) vs `material_curation.json` (design) | **`material_curation.json`**; chave = md5/pair_key; seed do MARCO 1 | code_curation é voto de CÓDIGO; chave por conteúdo casa com TIER 0 |
| 11 | aceite só media contenção | aceite DUPLO contenção+cobertura (§6) | TCC 26%/SO 0%: contenção 100% seria vitória falsa |
| 12 | voto LLM sem regra de aceitação | aceitar cego no escopo, band `media`, bounded à janela, autoconfiança ignorada | regra reproduz exatamente o protocolo que deu +5/18 no MARCO 1 |

## 10. Non-goals

- NÃO reescrever o funil (`computed` = piso; delete legado SÓ no cutover 3.4, eval-gated).
- Bibliografia/apoio/cronograma: FORA (funil; refatoração de ingestão futura no tracker,
  junto com sweep de shadowing).
- Ordinal-no-nome como sinal de posição: MORTO por medição (MARCO 0).
- week-math ordinal-linear como provider: PROIBIDO (F-TCC).
- Frequência de aula e granularidade de bloco: UPSTREAM.
- OpenSarc, plano de ensino (tópico→semana): fases posteriores.
- Sem hardcode de cadeira; só providers/extratores genéricos + pesos.
- UI nova: NÃO — revisão no Timeline Dashboard existente (override + badges).

## 11. Rastreio decisão/medição → requisito

| Origem | Onde no spec |
|---|---|
| D0/D5 plugável, cascata | §3 Contrato 1 |
| D1 dois grãos | §3 Contrato 3 (grãos) |
| D2 kind SOFT | §3 Contratos 1-2 |
| D3(+ajuste) cadeia, teto | §3 Contrato 2 |
| D4 gate + recall (MARCO 1) | §3 Contrato 2; §6; §7 fase 1 |
| D6 category-aware (+§4.8/4.9) | §3 TIER 2 |
| D7 tight/loose | §3 Contrato 1; §5 |
| D8-refinado (MARCO 1) | §3 TIER 3 + Regras do voto |
| D9 integração | §4; §7 fase 4; §8 |
| D10 rollout + providers (+§4.5) | §5; §7 fases 2/5 |
| D11 cross-check = anomalia-de-dado | mantido como QA report separado (`scripts/crosscheck_IA.py`); NÃO audita janela (11/11 falso-alarme) |
| D12/D13 gold | §2 (régua, modos por curso no log D13) |
| F-MF / F-TCC | §2 pisos; §3 P4/ordinal |
| MARCO 0 (len-norm, ordinal morto) | §3 Contrato 2; §10 |
| MARCO 1 (escopo, autoconfiança, recall) | §3 TIER 3; §6; §7 |
| §4.7 dup-divergence | §3 TIER 0; §4; §6 |

## 12. Decisões abertas pro plano (calibração TDD, não re-decisão)

- Valor exato do gate D4 (≥0.5 roteiro-score? band-cap?) — tracejar no gold MF.
- Pesos da fusão (concept-IDF vs session-label vs block.topic_text vs data-no-nome) —
  session-label > block.topic_text (fino > grosso).
- TCC P4: limiar do topic-match; quando cair direto no TIER 3.
- ES2: janela grossa (10 blocos) — session-label segura ou escala TIER 3 mais cedo?
- SO P3: data em bloco de range largo (grossura é UPSTREAM, mas medir).
- Serialização de `band`/`flag`/`provider` no `AnchorResult` → Dashboard.
- Detecção de "série same-theme" para o escopo do TIER 3 (prefixo comum + mesmo card?
  definir na fase 3 com os casos reais: Dafny1-5, indução, microsserviços).
- [sign-off 03/07] FLAG SEM janela × TIER 3: MARCO 1 converteu `plano.pdf` (sem janela; voto
  bloco-01 correto), mas a regra 2 do voto (bounded à janela) + invariante sem-janela→funil
  PROÍBEM esse voto. Definir na fase 3: sem-janela nunca vota (perde a classe plano) OU
  janela=timeline inteira só p/ categoria não-bibliografia.
- [revisão 03/07] cronograma_health (decidir na fase 4): portar `_top_candidate_blocks`
  (cronograma_health.py:117-171, reusa o S2 condenado) pro scoring do motor OU aposentar se
  band/flag/provider do Dashboard cobrirem. Pré-requisito da deleção S2 na fase 5.

## 13. Próximo passo

Plano de implementação (`writing-plans`): um plano por fase (fase 0 primeiro), tasks
bite-sized TDD, salvos em `docs/superpowers/plans/`. Execução SubAgent-Driven. Read-only
vs golds até a fase 4; escrever temporal = reprocess = user na GUI.
