# Pendências — tracker vivo

last_updated: 2026-06-22
status: documento VIVO. Atualizar a cada conclusão de plano (regra não-negociável,
`.mex/AGENTS.md`). Concluído 100% (gate verde) → remover daqui + mover o plano pra `Feitos/`.

Legenda: **[USER]** = ação humana (rotular/decidir/rodar). **[CODE]** = implementável.
**[DECISION]** = decisão de produto antes de codar.

CONVENÇÃO (não-negociável): todo item DERIVADO (fato sobre estado vivo dos repos) carrega
`as-of <data/commit>`. Sem isso, volta a mentir na próxima mudança de estado. Itens DURÁVEIS
(goal/decisão/plano) não carimbam.

---

## USER-SIDE — destravam a cadeia de medição/cutover

- [USER] **Gold cross-curso** (DURÁVEL/intent) — rotular `tests/fixtures/eval/ground_truth_<curso>.csv` IA/SO/ES2/TCC
  (MF já mede via eval_assignments 5/5). Planilhas em `docs/reports/gold_templates/gold_by_card_<curso>.csv`
  (MF 6 cards · IA 9 · SO 5 · ES2 3 · TCC 13 + avulsos). **Bloqueia: cutover Fase 3.4, lever lessons[].text,
  resolvers SO/MF, avaliação do anchor.** ← MAIOR GARGALO.
  > sub-nota DERIVADO-STALE: TODOS os números embutidos são pré-reprocess (gold_templates +
  > evals de 17–18/06): card-counts MF6/IA9/SO5/ES2 3/TCC13, "MF mede 5/5", e qualquer placar
  > tipo "~41% funil MF / resolver 12/17". Não verificados pós-reprocess.
- [USER] **IA placements gold-relevant** — `verificado as-of reprocess IA 7561f5c`:
  - **4 weak unpinned** (section Semana 2, hoje em bloco-04 dados 11–16/03):
    - `caracteristicasdosdados`/`caracteristicas-dos-dados` → bloco-04 **parecem certas** (content=DADOS bate "tipos dados/preparação").
    - `introducao-a-ml`/`introducaoml-atualizacao2025` → bloco-04, mas **DESLOCAMENTO candidato**: intro-ML real = **bloco-03** (09/03 "ml introducao a ml", hoje VAZIO). ABERTO p/ o gold.
  - **5 PINS preservados** (manual≠vazio): `oracle`/`ia-responsável`→bloco-01 (refs), `p1-2024-02`→bloco-08 (provas),
    `artigo-usando-k-nn`→bloco-05 (k-NN supervis = ok), **`artigo-usando-agrupamento`→bloco-05 SUSPEITO**
    (agrupamento=clustering=**bloco-06**, não supervis-05). Verificar no gold.
  - **bloco-06 mis-kind `suspended`→`class`** (`as-of 7561f5c`, uuid `17ea65f3-5f84-47c7-9357-e090ee1f80ed`).
    Range 20–27/04: só **20/04 é feriado**; **22/04 (k-Means)** + **27/04 (hierárquico)** são AULA. O `suspended`
    vazou da sessão 20/04 p/ o nível-bloco. Efeito: bloco ∈ `NON_ACADEMIC_KINDS` (`kinds.py:83`, `files:False`)
    → **7** materiais de clustering **somem da vista do gabarito** (`as-of 7561f5c`; cohort
  não-supervis Semana 8+9 = **8** ids — o 8º `artigo-usando-agrupamento` some pelo pin→bloco-05,
  não pelo bloco-06). Possível raiz do desloc. `artigo-agrupamento`→05
    (bloco-06 inválido como alvo file-bearing). Fix **EXISTE** (não é código novo): `.timeline_curation.json`
    `manual_kind_override:class` — honrado em `classifier.py:167-172`, aplicado em `index.py:85-90`. Passe de
    curadoria **pós-gold, GATEADO** (diff antes/depois, só `kind` muda; sem relance).
- [USER] **9 SO date-vs-block** (8 DIFFERS + 1 NO_MATCH) — **still-valid, verificado as-of reprocess SO 320712d.**
  Os 9 ainda divergem (bloco-da-data ≠ bloco-vivo). CONFIRMA "data-prefix = POSTAGEM, não aula": 3 arquivos com
  prefixo **02/06** caem em **blocos diferentes** (05/03/11). → pro gold SO, confiar em **tópico/seção**, NÃO na
  data do filename. Decisão humana por entry.
- ~~TCC sem CRONOGRAMA~~ **CORRIGIDO (21/06): claim era STALE (pré-reprocess).** TCC TEM cronograma
  completo pós-reprocess (31 blocos datados, SARC setado, 39/40 entries com "Semana N"). É
  week-anchorable igual IA/ES2. NÃO é blocker.

## MEDIÇÃO IA — conversor gold→ground_truth (as-of mundo-63, 2026-06-25)

- [DERIVADO] **Gold-method straddle = MAIOR história do crosswalk** (`as-of mundo-63`). O gold IA rotula em
  **subtópico (2 sessões)**; o pipeline placeia em **bloco (≈1 sessão)**. 11/20 subtópicos ATRAVESSAM fronteira
  de bloco → **21 materiais clean ficam inscoráveis** porque o subtópico sozinho não determina o bloco.
  **Propriedade do MÉTODO de gold, NÃO do pipeline.** Só subt 4-8 single-block (monstro bloco-05 absorve 4-7).
- [USER] **21 straddle clean** — inscoráveis por falta de `data_real` por-material. Re-entram via **batch SARC**
  (selector escolhe a SESSÃO/data, NÃO o bloco; conversor mapeia data→bloco sob `[início,fim)`). **Zona
  alta-FAIL** (fronteira). PROTOCOLO: medir taxa-FAIL straddle vs não-straddle SEPARADO — comparação some se
  misturar no agregado. Sequência: eval nos 33 PRIMEIRO (baseline), straddle como 2ª camada depois.
- [DECISION] **16 gold materiais fora da manifest viva** — gold rotulado PRÉ-poda (53/55), manifest PÓS-poda (42).
  **13 PODADOS** (no prepoda-55): out-of-escopo aceito (re-importar pra inflar denominador desfaria curadoria
  por vaidade métrica). **3 NEVER-IMPORT** (nem no pre55): `P2_IA_2024`, `Agentes`, `P2_IA_2024_02_A_turma30` —
  **buraco de PROCESSO** (rotulado, nunca entrou em build), NÃO decisão de poda. Investigar separado.
- [DERIVADO] **Denominador derivado: 33 scorable** (clean ∩ joined ∩ single-block ∩ resolved). **4 FAILs nomeados**,
  2 mecanismos: **(a) âncora-janela-de-pasta** (3: `Exemplo 2 k-NN IRIS`, `Exemplo com k-NN` — fronteira `[)`;
  `IA Aula 29` MLP) — placement por janela-de-pasta-Semana erra material cujo tópico-SARC pertence a outro bloco;
  **(b) pin-manual-errado** (1: `artigo-usando-agrupamento` — computed=None + manual-pin→bloco-05, oráculo=bloco-06;
  MESMO material "sem computed" da 2.5, não dois). Teste-unidade de borda `[início,fim)` = FIADOR dos FAILs k-NN.
- [CODE] **calibração-de-confiança — caso-âncora IRIS, PRIORIDADE ALTA** (`as-of mundo-63`). `exemplo-2-k-nn-IRIS`
  previu bloco-04 (errado; true bloco-05) com **band ALTA** = confiante-e-errado. NÃO é nota de rodapé: é a
  pendência de calibração do handoff inicial com caso vivo. Entre os DISCRIMINANTES a taxa confiante-errado é
  1/N-discriminante, NÃO 1/28 — diluir no monstro esconde. E é o modo de falha que o protocolo "só reviso o
  flagado" é **CEGO POR CONSTRUÇÃO** (confiante-errado não se auto-flagra). A âncora por-janela-de-pasta emite
  band alta mesmo placeando pela pasta errada → a confiança não reflete a incerteza de FRONTEIRA. Entra ANTES de
  gerar mais número.
- [DERIVADO] **DOIS mecanismos de FAIL, não um** (`as-of mundo-63`) — refuta "erra só na fronteira":
  **(1) âncora/janela-de-pasta** — 3 FAILs DISCRIMINANTES de fronteira (IRIS band-alta, exemplo-com-k-nn,
  artigo-pin); off-by-one adjacente; só pega material de fronteira. **(2) sem-cobertura→fallback-computed** —
  `IA-aula-29` é INTERIOR (subt-6, 06+08/04 ambos bloco-05, miolo do monstro) e ERRA mesmo assim:
  `source_section=None` → âncora não placeia → `temporal` VAZIO → eval cai no `computed` (`file_map:636`),
  `scorer_only` **band baixa** = bloco-04. Caso VIVO da fragilidade temporal-vazio (dentro do scored-set IA, não
  hipotético SO/MF). NÃO é calibração-errada: band baixa = incerteza honesta (≠ IRIS band-alta-errado). Mecanismo
  (2) alcança INTERIOR. Distância dos 4 segue off-by-one, mas "só fronteira" caiu.
- [DECISION] **80% discriminante assume proxy-date fiel pros existentes** (`as-of mundo-63`). Existentes datados por
  **1ª-data-do-subtópico** (só notebooks têm data por-material exata). 1 proxy-frágil: `arvores-de-decisao` (subt-7,
  proxy 13/04=trivial vs real 15/04=discriminante) — **passa em ambas → proxy NÃO esconde FAIL aqui**. Limitação
  nomeada: onde proxy≠real caírem em blocos diferentes, o proxy fabrica/esconde FAIL. 5 agrupamento usam 20/04
  (suspensão; aula real 22/04, mesmo bloco bloco-06).
- [DERIVADO] **Cobertura prediz correção — mas o sinal é MECANISMO, não taxa** (`as-of mundo-63`). Dos 33 scorable,
  só **2 uncovered** (temporal cru vazio → fallback): IA-aula-29 (sem-pasta→computed) + artigo-agrupamento
  (pin→manual); ambos falharam. NÃO reportar "100% uncovered-fail" — n=2, amostra pequena demais pra taxa
  (número inflado contra o sistema é tão inválido quanto a favor). O sinal é o MECANISMO sem-pasta→fallback→erro,
  que IA-aula-29 dá sozinho; os 2 ilustram, não quantificam. **0 uncovered PASSOU → a 3ª categoria temida
  (acertos-frágeis-por-sorte-do-fallback) NÃO existe neste set.**
- [CODE] **PIN-SWEEP — pins manuais que discordam da âncora** (`as-of mundo-63`). 5 pins, 2 discordam, mas
  **"discorda" ≠ "errado"** (oráculo separa): **(WRONG) `artigo-usando-agrupamento`** pin-05 vs âncora/oráculo-06 →
  **TOPO da fila, fix-de-1-linha: deleta o pin**, âncora-bloco-06 correta emerge. **(GOOD) `artigo-usando-k-nn-em-texto`**
  pin-05 vs âncora-04: o pin está CERTO (k-NN=18/03→bloco-05), a âncora ERRARIA (Semana-3 começa 16/03=prep) — o pin
  **resgata** a âncora do erro Semana-3-prep-vs-k-NN-18/03 (mesmo que derruba os notebooks k-NN). Evidência de patch
  humano sobre fraqueza sistemática da âncora. Regra de varredura futura: pin-disagreement = CANDIDATO, confirma
  com oráculo antes de deletar (deletar pin-bom quebra).
- [DECISION/USER] **never-import resolvido — não é buraco de conteúdo** (`as-of mundo-63`). Dos 3 unjoined-never-import:
  **`Agentes.pdf` = FALSO ALARME** (existe na manifest como `introducao-a-agentes`, Semana-16; gold usou nome
  divergente → join-miss; fix: alias/renome no gold). **`P2_IA_2024` + `P2_IA_2024_02_A_turma30`** = 2 provas-2 fora
  do stash → DUAS hipóteses DISTINTAS (NÃO fundir): **phantom-no-gold** (rótulo de material inexistente = erro de
  rotulagem) vs **nunca-baixada** (existe no Moodle, download pulou = mini-buraco-de-processo que repete em SO/MF).
  Distinguir precisa checar Moodle. Gap estreito, provas não-conteúdo; nenhum material pedagógico dropado pelo import.
- [DERIVADO] **80% é PÓS-2-CAMADAS-DE-CORREÇÃO** (`as-of mundo-63`). Mascaramento empilhado: âncora mascara
  erro-de-computed (hierárquico bloco-07→06), pins mascaram erro-de-âncora (`k-nn-texto`: pin-05 corrige âncora-04).
  `k-nn-texto` é **FÓSSIL** — humano patcheou o bug Semana-3-prep-vs-k-NN ANTES desta campanha = confirmação
  INDEPENDENTE do mecanismo (não artefato de medição). O erro BRUTO do placement-por-pasta (sem âncora, sem pins) é
  **MAIOR que 20%**; o 80% é performance real COM as 2 correções e **NÃO generaliza sem elas** (SO/MF podem não ter
  as camadas de patch).
- [UX/CODE] **aviso GUI "sem bloco atribuído" induz pin desnecessário = armadilha de UX** (`as-of 2026-06-26`). O
  aviso do cronograma conta materiais sem atribuição MANUAL (pin), NÃO sem placement — 58/63 (os que usam
  auto-placement, o estado DESEJADO). A redação empurra o usuário a preencher pins à mão → re-introduz circularidade
  (mão atribuindo o bloco que o pipeline computa) + risco de pin-stale (caso `artigo`). Custou uma **deleção-de-entry
  acidental** nesta sessão (delete-entry vs pop-field quase-idênticos na GUI do Timeline Dashboard; 63→62, pego pelo
  gate (b)). Fix: re-redigir ("sem override manual", não "sem bloco") ou suprimir quando há placement auto; e separar
  visualmente delete-entry de clear-pin.
- [PROTOCOL] **conserto-de-pin loop: pós-mutação do vivo, REGENERA o CSV antes de classificar** (`as-of 2026-06-26`).
  No 1º fix (artigo) o `eval` (lê manifesto vivo) deu 30/33 mas o `classify` (lê coluna `temporal_block_id` do CSV
  pré-reprocess) deu 12/15 — defasagem CSV-stale vs vivo. NÃO escolher um: regenerar o CSV (`build_ground_truth_IA`)
  pós-reprocess e re-classificar. Sequência: rename→gate-vivo→reprocess→diff_pinfix→**regen CSV**→eval+classify.

## CODE — cadeia de atribuição (degrau 3 / Fase 3)

- [CODE] Degrau 3a **alavanca 0** (lessons[].text → índice data→tópico no fusor) — plano escrito, não
  executado; `load_lessons_index` dormente. Eval-gate (precisa gold). Refazer com identidade limpa do label
  (a versão anterior regrediu o gold com concepts ruidosos).
- [CODE] **Alavanca 3** (posting_date / seleção por sessão) — não implementada.
- [CODE] **Fase 3.4 cutover** — default ON do concept_resolver + DELETE do funil legado
  (`score_entry_against_timeline_block` S2/S4, `select_probable_period`, `_best_instructional_block_fallback`,
  2 rotas card). Eval-gated.
- [CODE] **topic-resolver (SO)** + **label-resolver (MF)** — próximos resolvers de âncora (reusam
  `anchor_placement`/`resolve_temporal_block`); cada um TDD + canário próprio.
- [CODE] Degrau 2/3c **over-merge temporal** (merge feriado+prova) — adiado; funde no degrau 3 quando join virar DATA.
- [CODE] **placement-computed-errado-mascarado-por-âncora** (`as-of mundo-63 IA, 2026-06-25`) — o
  `_card_scoped_block` (computed) ERRA o hierárquico: `computed_block_id=bloco-07` ("duvidas"), enquanto a
  verdade-oráculo é **bloco-06** (27/04, SARC, proveniência cravada por redundância tabela+bullets). O eval
  pontua `temporal` (`resolve_temporal_block`, `file_map:633/635` — `temporal_block_id` da âncora vence ANTES
  do fallback), e a âncora pôs bloco-06 → **passa HOJE**. MAS `file_map:636`: `temporal` vazio → fallback
  `computed`. Os 24 notebooks IA têm temporal setado → nenhum cai. Material com temporal vazio (SO/MF/ES2, ou
  IA futuro sem cobertura de âncora) → eval pontua `computed` = o canal que erra o hierárquico.
  **"Hierárquico passa" é verdade hoje, frágil amanhã; a fragilidade vive na COBERTURA DA ÂNCORA, não no
  computed.** NÃO é "sistema consertou" — é erro-de-computed mascarado por override temporal. Delta
  computed-vs-temporal nos 24: **3 diferem** (hierárquico×2, "Exemplo com k-NN"), 21 idênticos. Mesmo
  mecanismo dos 2 FAILs k-NN (placement por janela-de-pasta-Semana erra material cujo tópico-SARC pertence a
  outro bloco) — só que nos k-NN a âncora TAMBÉM erra (não mascara). Reaparece sem boa cobertura de âncora.

## CODE — limpeza / dead-code (auditoria pronta)

- [CODE] **Tasks D/E** — unificar 3 scorers de unidade dup + vocab/normalizadores ×4. Eval-gated.
- [CODE] **Task B** `administrative_only` — persistir vs deletar filtros mortos (decisão de produto).
- [CODE] **fallback keyword** (~600 linhas, index.py) — deletar junto da unificação P2 (fold dos sinais que
  o frágil tem: "Unidade N" explícita, frases/âncoras) + guard test.
- [CODE] **Auditoria de artefatos** — mapear quem lê `.timeline_index`/`.card_block_map`/`.lessons_index`/
  `code_curation`/`.tag_profile`/etc. → morto/vivo/redundante → fundir, cada fusão eval-gated.

## CODE — bugs pré-existentes localizados

- ~~[CODE] `SubjectManagerDialog._save` (dialogs.py:1503-1525) **dropa `moodle_course_id`/`m365_filter`** ao salvar.~~
  **FIX aplicado (2026-06-22, working tree, uncommitted):** `_save` agora preserva ambos de `existing`
  (espelha `turma`/`schedule_url`, dialogs.py:1521-1525). 388 testes verdes (core/moodle/m365). NOTA: o fix
  evita zeragem FUTURA; o `moodle_course_id` do IA já perdido precisa **re-import Moodle** pra restaurar.
- [CODE] `migrate_signals` standalone **não grava `turma`** (só `import_moodle_courses` grava) — derivar do curso.
  > derived-código, não-reprocess-stale, as-of 18/06 (S0).
- [CODE] **Latente:** sem teaching_plan, `_derive_unit_specs_from_repo` vs `content_taxonomy["units"]=[]` divergem
  → fallback vira load-bearing. Remover ou dar mesmo fallback à taxonomy.
  > derived-código, não-reprocess-stale, as-of 17/06.

## CODE — UI (Parte B de features backend já entregues)

- [CODE] Cronograma SARC: **tab em tabela + legenda**.
- [CODE] Guard de conflito override: **aviso no tab + botão "reverter p/ auto"**.

## DECISION

- [DECISION] **bloco-15 over-merge (IA)** — bloco-15 = 01–08/06; merge **Semana 14** (dijkstra/hc-sa, sess 01,03/06)
  + **Semana 15** (minimax/listas, sess 08/06). **still-valid, verificado as-of reprocess IA 7561f5c.** Cura de timeline separada.
- [DECISION] **5 IA busca — bloco-12 vs bloco-13** — section "Semana 12 - Algoritmos de Busca", caem em **bloco-12**
  (Correção P1+Agentes, 18–20/05). MAS **bloco-13** (25/05, "Algoritmos busca") = candidato topic-match → **um bloco fora**.
  Mismatch Moodle×SARC persiste. **still-valid, verificado as-of 7561f5c.** Gold-relevant.
- [DECISION] **A1 (lessons no fusor)** — chamar brainstorming antes de spec.
- [DECISION] **Span-cap de over-merge REFUTADO (as-of 2026-06-22)** — tentativa de cap de span temporal em
  `_rows_belong_to_same_thematic_block` (15d) reverteu por EVIDÊNCIA, não por calibração: (1) IA bloco-05
  ("monstro" 28d) é unidade COESA *ML supervisionado* (kNN→redes neurais→árvores); só a cauda 04-15
  não-supervisionada é mis-merge. (2) Span não distingue coeso-longo (MF 21d, recursivas) de qualquer-longo —
  mesma classe; nenhum threshold separa sem quebrar o coeso. (3) Quebrou
  `test_file_map_..._respects_manual_timeline_block_override` (bisecta tópico coeso no meio) = o mecanismo do
  +17 do Degrau 2. **Discriminante (as-of reprocess IA 7561f5c):** arquivos da cauda não-supervis
  (k-means/agrupamento/clustering) auto-atribuem a bloco-06/07, NUNCA a bloco-05 → a mis-merge do 04-15 em
  bloco-05 é **render-only** (cosmético do cronograma), sem mal-atribuição de arquivo. Se um dia splitar:
  por TRANSIÇÃO de tópico, NÃO span. Bloco-05 não é problema de fronteira/atribuição.
- [DECISION] **Regra "2 aulas = 1 bloco" APOSENTADA (durável)** — bloco = unidade pedagógica, sessão = átomo
  do render (`sessions[]` por semana ISO). A granularidade fina vive nas sessões, não em mais blocos.
- [DECISION] **Dedup por CONTEÚDO (md5), nunca por basename/id (durável, 2026-06-23)** — duplicata sem hash é
  palpite. CAUSA confirmada no IA: o stash migrou de `Downloads\InteligenciaArtificial` (nomeado por TÍTULO do
  PDF) → `Desktop\Moodle\inteligencia-artificial` (Moodle, nomes reais + Semanas); o manifest **acumulou os dois**
  e ninguém podou o velho. Faltou **poda de migração**. Dedup por basename/id não pega (nomes diferem); só md5.
- [CODE] **IA: poda de 13 stale (verificado as-of 2026-06-23)** — 13 entries do stash ANTIGO (source sumiu)
  são byte-idênticas (md5) a uma VIVA do stash novo → podar. Gate: só poda com substituta viva. **1 exige migração
  ANTES:** `p1-2024-02-ia`→`prova-1-2024-02` carrega `manual_timeline_block_id` (pin bloco-08, uuid `5256ec08`) +
  `manual_unit_slug` que a viva NÃO tem (perda de curadoria). Outras 12: viva já aprovada (sem gap). Pós-poda 50→37.
  Gold é keyed por id → 13 linhas órfãs no CSV; remapear old→live (mesmo md5 = mesma resposta), não re-rotular.
- [CODE] **`gold_score.py VERSION_PAIRS` cobre os casos ERRADOS** — `mlp`/`mlp-novaversao` e `introducao-a-ml`/
  `introducaoml-atualizacao2025` são **byte-dups** do stash antigo (somem na poda), **não pares de versão**. O
  "posting 24/02 = slide reusado" estava errado (é só a data do arquivo velho). O ÚNICO version-pair real (bytes
  diferentes, mesma aula) é **`inteligencia-artificial-aula-29...` ≡ `como-analisar-resultados-acc-pr-re-e-f1`**
  (md5 5bdaa9c7 vs 84a1f47a; o aula-29 é órfão byte-único, source sumiu — tratar à parte, não podar). Trocar o
  VERSION_PAIRS hardcoded por dedup-por-md5 no pipeline (causa), gate golden 5/5 + não-cascateamento + rebuild_diff.
- [USER] **Stash IA é download PARCIAL** — API Moodle (course 93156) mostra ~45 arquivos no Moodle ausentes do
  stash local (grosso = `.ipynb`/datasets que o pipeline pula; alguns PDF reais ex.: `Agentes.pdf` Semana 16,
  `Future of Jobs`, TDE `P2`). Lista definitiva exige baixar+hashear (content-match), não slug.

## CROSS-CUTTING

- [DECISION] **Branch `feat/block-stable-id` NÃO mergeada** — carrega Fase 1 + Fase 2 + campanha anchor/WO2/reprocess.
  Merge/PR = decisão do user.
- ~~`.timeline_index.json` stale (ES2 7/IA20/SO13)~~ **RESOLVED-BY-REPROCESS, verificado as-of 21/06:**
  o reprocess regravou os 5 índices; rebuild_diff vivo = **ES2 0/IA1/MF1/SO0/TCC0** (= baseline pré-existente,
  NÃO o drift 7/20/13). O drift de índice stale sumiu.
- **timeline IA em snapshot SARC antigo — janela 24–29/06** (`as-of 7561f5c`). SARC vivo (prof. moveu a
  apresentação T2): **24/06 = Feriado**, **29/06 = T2**. `SYLLABUS.md`/KB shipado refletem isso; mas
  `.timeline_index.json`/`CRONOGRAMA_DETALHADO.md` (fonte do gabarito) têm **24/06=T2 (bloco-19)** +
  **29/06=aula "Gerias" (bloco-20)** — trocados. Mesmo reprocess, `.timeline_curation` vazia → **SYLLABUS≠timeline**
  (bug de pipeline: dois caminhos de SARC divergem, a investigar). **Cosmético p/ o gabarito**: conteúdo do
  Moodle acaba ~**Semana 16** (último card 15–19/06; sem PDF → 0 entries); blocos **18–25 têm 0 material** →
  nenhum card cavalga a janela trocada. Gold: tratar 24/06=feriado / 29/06=T2 por override **no gold**, sem tocar repo.

---

## Concluído (2026-06-22 — divisão de blocos: prova estrutural)
> Carimbo (ROUTER): **Fases 0-2 — estrutural provado (não-cascateamento + golden 5/5); correção de
> atribuição NÃO medida, bloqueada em gold IA.** (A máquina está provada; se os arquivos caem no bloco
> CERTO é o que o gold IA — bloqueado user-side — vai medir.)
- **Fase 0 caracterização** — snapshots golden do estado atual (divisão · maior-bloco · casos-chave · render),
  17 goldens em `tests/_golden/`, suíte 1637 verde. Commit `7554e82`.
- **Fase 1 identidade estável** — PROVADA robusta a split (não só a existência de `block_uuid`):
  `tests/test_block_split_nao_cascateia.py` — split renumera `bloco-NN` mas o uuid segue o CONTEÚDO
  (date/token overlap), `computed_block_id` + `card_block_map` seguem resolvendo, ledger append-only;
  contraste explícito (posicional cascateia, uuid não). Wired pós-split: `reattach_block_uuids`
  (`index.py:1405`) roda APÓS a construção dos blocos (`index.py:1380`), então qualquer split futuro herda
  a proteção. Commit `b733d19`.
- **Fase 2 data-membership** — já viva/wired/testada nesta branch: `derive_card_block_map` (`moodle.py:488`)
  → `.card_block_map.json` → `_card_scoped_block` (`content_taxonomy.py:1193`) → `computed_block_id`
  (`content_taxonomy.py:1260`). Casos-chave IA decididos por method `card`/`card+scorer`. Normalização
  `norm_ascii_lower` nos 2 lados do join (Degrau 1). Item 3 do plano já era no-op.
- **Fase 3 (span-cap)** — REFUTADA (ver DECISION acima): mecanismo errado, over-merge do IA é render-only.

## Concluído (histórico desta campanha — 2026-06-21)
- Camada anchor placement WIRED (temporal_block_id aditivo + helper `resolve_temporal_block`, 6 consumidores
  temporais, KB intocado). Commit `d792331`.
- Surface durável `feature_flags` por matéria. Commit `22b6de9`.
- WO2 fix manual-uuid (`_block_by_migrated_ref` uuid-first) — 23 pins humanos recuperados nos 5. Commit `d67bb19`.
- Reprocess dos 5 tutores (computed→uuid; IA com 33 temporal/2 movers; outros sem temporal). Commits tutor repos:
  IA 7561f5c · ES2 abc8ee2 · MF 357a59b · SO 320712d · TCC 6b6e1e3. Gates: HARD-drift 0 em todos.
