# Pendências — tracker vivo

last_updated: 2026-07-07
> Renomeado de `2026-06-21-pendencias.md` em 2026-07-03 (decisão do user: nome geral sem data,
> mais fácil de achar/revisar). Histórico preservado via `git mv`; 7 referências atualizadas.
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
  > progresso `as-of 2026-07-01`: **5/5 CURSOS COM RÉGUA.** IA ✅ · MF ✅ (67 scorable/24 disc, `511ea1e`) ·
  > ES2 ✅ (28/14, `4aa9bcd`) · **SO ✅ 42 scorable/23 disc** (`ground_truth_SO.csv`) · **TCC ✅ 42 scorable/
  > 20 disc** (`ground_truth_TCC.csv`) — ambos UNCOMMITTED, HALT pendente revisão humana do crosswalk.
  > TCC: template refeito (tipo=file_type puro) com backup `gold_TCC_rotular.pre-refazer-20260701-165239.bak.xlsx`;
  > 4 rótulos off-by-one detectados na revisão HALT e corrigidos com confirmação do user (+gêmeos, 7 células;
  > obs carimbada no xlsx). Gêmeos md5 rotulados SEM conflito (validado).
  > Evidência p/ o motor: as 3 cópias byte-idênticas da aula-06 têm temporal em 3 blocos DIFERENTES
  > (bloco-06/09/22) = dup-divergence vivo, motor não trata dup hoje.
  > **EVAL BASELINE OFICIAL 5/5 (as-of 2026-07-01, HALTs sign-off user, colapso de par ativo):**
  > **IA 38/44 = 86.4%** (6/6 erros off-by-one adjacente, 0 miss-tópico; calibração ok: alta 32ok/3erro) ·
  > **MF 42/66 = 63.6%** (12/24 adjacente; 1 órfão) · **TCC 14/25 = 56.0%** (pós-poda; pré era 15/27 55.6%) ·
  > **ES2 14/28 = 50.0%** (12/14 = miss de tópico) · **SO 18/38 = 47.4%** (17/20 miss de tópico; band alta
  > 15ok/16erro = confiança NÃO informa). Leitura: IA (única com âncora data-de-seção) erra SÓ fronteira;
  > os 4 sem âncora afundam em miss-de-tópico — confirma o desenho janela+disambiguator do motor. É o placar
  > que o AnchorEngine tem que bater SEM regressão no IA. Confiante-e-errado dominante fora do IA reforça a
  > pendência de calibração.
- [DERIVADO] **Sweep md5 dos 5 cursos COMPLETO** (`as-of 2026-07-01`, via `raw/` de cada repo) — dups por
  conteúdo: **IA 3 grupos** (já cobertos no pairs) · **ES2 0** · **MF 1** (`logicadehoare1-exercicios-respostas`
  ≡ `logicadehoare-exercicios-respostas`, ESCAPOU do `511ea1e`; pairs preenchido + CSV regenerado 2026-07-01,
  67/24 mantidos, unidades de eval 67→66; gêmeos ambos bloco-10 PASS = sem flip) · **SO 4** · **TCC 14**.
  Todos os grupos agora cobertos em `COURSE_CONFIG.pairs`. IA tem 3 entries sem `raw_target` no disco
  (2 artigos-web com sufixo hash + `artigo-usando-agrupamento`) — não-verificáveis por hash, vigiar.
- ~~TCC `pairs` dedup a preencher~~ **PREENCHIDO (2026-07-01, uncommitted)** — sweep md5 via `raw/` do repo:
  **42 entries = 27 materiais distintos, 14 grupos dup** (11 cross-stash OLD≡Moodle + triplo intra-OLD aula-06 +
  2 intra-Moodle). `COURSE_CONFIG["TCC"]["pairs"]` populado (canônico = id Moodle vivo). Causa CONFIRMADA por
  hash: stash antigo `Downloads/TCC` + stash Moodle acumulados sem poda de migração — mesmo mecanismo do IA.
- [DERIVADO] **TCC: 24/42 sources SUMIDOS do disco** (`as-of 2026-07-01`) — todo o lado `Downloads/TCC` não
  existe mais (migração pro `Desktop/Moodle` levou a pasta). Entries seguem vivas via `raw/` do repo. Download
  Moodle do TCC é **PARCIAL**: 10 materiais OLD sem substituta Moodle (aulas 01-03, 05, 09, 14, 15, prova-revisão,
  referência Karp, weighted-max-cut) — podar esses = perder conteúdo. Igual "stash IA parcial".
- ~~TCC poda de migração~~ **EXECUTADA em 2 rodadas (2026-07-01), ESCOPO AMPLIADO pelo user**: rodada 1 (GUI,
  user) matou 7 (aula-04, aula-06 ×2 — colisão de id RESOLVIDA —, aula-08, aula07-grudada, enunciado-t1/t2);
  rodada 2 (script CC autorizado pelo user, executado pelo user via `!`, backup
  `TCC-Tutor/manifest.pre-poda16-20260701-184119.bak.json`) matou os **17 restantes do Downloads** — decisão
  EXPLÍCITA do user de incluir os **11 SEM substituta Moodle** (aulas 01-03/05/06-revisão/09/14/15,
  exemplo-prova-revisão, referência Karp, weighted-max-cut). Manifest TCC: 42→**18 entries, 100% Moodle**.
  **Consequência assumida: esses 11 conteúdos estão FORA do tutor até re-import Moodle completo** (entra na
  refatoração de ingestão de apoio). Gold xlsx TCC: ~24 linhas viram unjoined no próximo crosswalk (esperado,
  não é bug). Dups restantes: só os 2 intra-Moodle (3d-matching, integer-programming), `pairs` cobre.
  ~~PENDENTE reprocessar~~ **CICLO FECHADO (2026-07-01): reprocess + gate VERDE.** Descoberta que mata a
  teoria "download parcial": as entries velhas do Downloads **SOMBREAVAM o import** (dedup por slug) — poda
  liberou o importer, que re-ingeriu **9 dos 11 "perdidos" direto do stash Moodle** com seção Semana-N correta.
  Perda líquida real = **2 arquivos** (referência Karp + weighted-max-cut; só existiam no Downloads; recuperáveis
  do backup). Manifest TCC final: **27 entries, 100% Moodle**, colisão de id morta, dups = só 2 intra-Moodle.
  Gate: **0 drift** de temporal/true nos 18 sobreviventes ✓; re-importados ganharam placement novo (esperado):
  aula-01 virou FAIL novo (true bloco-01, temporal bloco-02 — janela Semana-1 ambígua), aula-06 temporal
  bloco-09. Crosswalk 36/42 joined (6 unjoined = exatamente os nomes mortos, sem gap silencioso).
  **EVAL TCC pós-poda = 14/25 (56.0%)** — baseline re-referenciado (pré-poda 15/27 55.6%, estável).
  **INSIGHT p/ refatoração de ingestão: import dedup-por-slug deixa entry morta BLOQUEAR fonte viva** —
  mesma mecânica pode estar escondendo material em outros cursos; sweep de shadowing entra no escopo da
  refatoração de apoio/bibliografia.
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
    > **CONCLUÍDO (2026-07-01): curation escrita + IA reprocessado + GATE VERDE.** bloco-06 kind
    > `suspended`→`class` (override honrado; key migrada pra uuid `17ea65f3` pelo pipeline). Zero placement
    > movido nos 7 de clustering; eval IA 38/44 = 86.4% byte-idêntico ao baseline (mesmos 6 off-by-one).
    > Os 7 materiais de clustering voltaram à vista do gabarito/GUI.
- [USER] **9 SO date-vs-block** (8 DIFFERS + 1 NO_MATCH) — **still-valid, verificado as-of reprocess SO 320712d.**
  Os 9 ainda divergem (bloco-da-data ≠ bloco-vivo). CONFIRMA "data-prefix = POSTAGEM, não aula": 3 arquivos com
  prefixo **02/06** caem em **blocos diferentes** (05/03/11). → pro gold SO, confiar em **tópico/seção**, NÃO na
  data do filename. Decisão humana por entry.
- ~~TCC sem CRONOGRAMA~~ **CORRIGIDO (21/06): claim era STALE (pré-reprocess).** TCC TEM cronograma
  completo pós-reprocess (31 blocos datados, SARC setado, 39/40 entries com "Semana N"). É
  week-anchorable igual IA/ES2. NÃO é blocker.
- ~~[USER] card "Verificação de Programas" MF sem bloco-09 na janela~~ **MORTA (2026-07-08): diagnóstico
  da FASE 0 estava ERRADO — o card map estava CERTO; o defeito era GOLD STALE.** User contestou a
  pendência; auditoria completa do `ground_truth_MF.csv` (67 rows, READ-ONLY vs timeline atual) provou
  drift posicional de `bloco-NN` pós-reprocess: bloco-09 HOJE é a prova P1 (22/04) — material de conteúdo
  rotulado nela era rótulo antigo deslocado. **7 rows re-rotuladas com sign-off do user** (invariantes×2
  09→11; correcaoterminacao×2 10→11; exerciciosformalizacaoalgoritmosinvariantes 10→11; hoare 13→10;
  exercicioscorrecaoinducaomatematica 06→05; tiposindutivos mantido 15 por decisão do user). Números
  reais do motor pós-correção: **acurácia 82.8% (48/58), contenção-fora 0, confiante-errado 1
  (exerciciosdafny2), recall 0.900** — a régua stale escondia 12pp. Baselines dos probes renegociados
  (conf≤1, conten≤0, recall≥9/10). LIÇÃO DURÁVEL: gold em `bloco-NN` posicional é frágil a reprocess —
  antes de qualquer medição cross-curso (FASE 2), auditar frescor dos ground_truth_* vs timeline atual
  (SO/TCC/IA/ES2 podem ter o mesmo drift); considerar migrar gold pra `block_uuid`.

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
  **"discorda" ≠ "errado"** (oráculo separa): ~~(WRONG) `artigo-usando-agrupamento` pin-05~~ **JÁ RESOLVIDO
  (verificado 2026-07-01: pin=None, temporal=bloco-06 correto — deletado em sessão anterior ou reprocess).**
  **(GOOD) `artigo-usando-k-nn-em-texto`**
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

- ~~Degrau 3a alavanca 0 (lessons no fusor)~~ **SUPERSEDED PELO MOTOR (2026-07-01, verificado)** — o SINAL
  (`.lessons_index.json`/roteiro) virou 1ª classe no disambiguator do motor (D3/D5; exercitado no MARCO 0).
  O PLANO original (termo β no fusor velho via `resolver_apply`/`score_lesson_match` peso 0.5) mira o caminho
  que morre no cutover 3.4 — `load_lessons_index` está chamado em `resolver_apply.py:111`, atrás da flag
  desligada, fundo da cascata. Plano `2026-06-17-alavanca0-lessons-index-plan.md` carimbado superseded.
  **Herança viva pro spec:** o caso-alvo do A1 (card "Verificação de Programas" MF, 14 lessons, blocos 10-15)
  é onde MARCO 0/1 ainda erra (hoare/tiposindutivos/dafny1-2) → matching fino de lesson = requisito do
  disambiguator real.
- ~~Alavanca 3 (posting_date / seleção por sessão)~~ **SUPERSEDED (2026-07-01)** — posting_date foi declarado
  lixo como sinal de base (decisão 28/06); o motor D0-D13 não o usa (sinais: seção/roteiro/prazo/conteúdo).
- [CODE] **Fase 3.4 cutover** — default ON do concept_resolver + DELETE do funil legado
  (`score_entry_against_timeline_block` S2/S4, `select_probable_period`, `_best_instructional_block_fallback`,
  2 rotas card). Eval-gated.
- ~~topic-resolver (SO) + label-resolver (MF)~~ **SUPERSEDED PELO MOTOR (2026-07-01)** — viraram
  WindowProviders por curso dentro do AnchorEngine (D5/D10), não resolvers avulsos. E são LOAD-BEARING,
  não rollout tardio — cobertura de card-window medida hoje:
  **IA 56/62 (90%) · MF 60/67 (90%) · ES2 30/35 (86%) · TCC 7/27 (26%) · SO 0/42 (0%).**
  Sem provider próprio, o motor = funil pra SO inteiro e 20/27 do TCC. Spec deve tratar
  WindowProvider-por-curso (SO topic/filename-date; TCC parse "Semana N") como fase de 1ª classe.
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

> Revisão spec×código×dívida (2026-07-03, agente read-only): âncoras §8 do spec = **0 drift / 0 missing /
> 0 divergente** (plano fase 0 parte delas sem re-verificação). Veredito de ordem: unificação D/E **NÃO
> antecede a fase 0** — primitivas do Disambiguator (`concept_token_weights`/`concept_vector`/
> `score_lesson_match`, concept_resolver.py) já são a cópia canônica sobre normalize/stopwords canônicos;
> o gêmeo IDF (`block_token_weights`, file_map.py:882) é o S2 que morre no cutover.

- [CODE] **Tasks D/E (corrigidas 2026-07-03)** — "vocab/normalizadores ×4" JÁ RESOLVIDO no código: todos
  delegam a `text/normalize.py:normalize_match_text` (variantes só paramétricas); `_collapse_ws` e
  `UNIT_GENERIC_TOKENS` fonte única. Resta: 3 scorers de unidade dup (`file_map.py:209`,
  `index.py:1620`, `index.py:1732`) + signal-key mismatch (H3) + predicados (M3). Eval-gated, trilho
  próprio, DEPOIS da fase 0 (grafo disjunto do motor; unificar antes não reduz risco).
- [CODE] **Task B** `administrative_only` — persistir vs deletar (decisão de produto). **CONGELADA até os
  testes de janela da fase 0**: predicado usado DENTRO de `derive_card_block_map`
  (moodle_labels.py:158-159) = WindowProvider P1/P2; mexer nele altera a janela do motor. Nota da
  revisão 03/07: os "filtros mortos" originais já não existem — predicado lê `rows` no runtime e é real.
- [CODE] **fallback keyword (~600 linhas, index.py) — DIVIDIDO 2026-07-03, não deletar em bloco**:
  (a) ramo fallback de UNIDADE (index.py:2207-2215, dispara só com `assign_units_positional` vazio) =
  deletável no cutover c/ guard test; (b) cadeia topic-labels (index.py:2174 → 1929/1732) RODA SEMPRE e
  alimenta UI/badges = VIVA, fora da lista de morto.
- [CODE] ~~**Auditoria de artefatos**~~ **FEITA 2026-07-03** — mapa de leitores no relatório da revisão:
  `.timeline_index`/`.card_block_map`/`.lessons_index`/`code_curation`/`.tag_profile` TODOS vivos;
  `.timeline_index` ganha consumidor novo no motor (`sessions[].label`); cache do motor =
  `material_curation.json` NOVO, sem colisão com `code_curation`.
- [CODE] **RUN dedicada de remoção de mortos (decisão user 2026-07-03)** — separada do plano do motor,
  qualquer hora. Primeiro alvo provado: `_derive_unit_from_topic_match` (index.py:2080; morto em
  produção; só re-export engine.py:241/2443 + tests/test_file_map_unit_mapping.py:11,647,705,732,836).
  Remoção pura, sem eval.
- [CODE] **Mapa de deleção do cutover fase 5 — 5 conflitos, resoluções travadas 2026-07-03**:
  1. `cronograma_health.py:117-171` reusa o scorer S2 condenado → **fase 4 decide** portar pro scoring
     do motor ou aposentar (band/flag do Dashboard na mão); fase 5 não deleta antes da decisão.
  2. `scripts/eval_assignments.py:99` + `scripts/retag_manifest.py:60` injetam `select_probable_period`
     → **LEGADO-NÃO-USAR desde já**; aposentar no MESMO commit da deleção (régua oficial =
     `eval_ground_truth.py`, mede via `resolve_temporal_block`, que sobrevive).
  3. Deleção por **LISTA NOMEADA de símbolos**: morrem `score_entry_against_timeline_block` /
     `block_token_weights` (S2) / `TOOL_*` (S4) / `select_probable_period_for_entry` /
     `_best_instructional_block_fallback` / `_card_scoped_block`; FICAM
     `score_card_evidence_against_entry` + `_score_block_date_match` (file_map.py:737/1078 — usados
     pelo `concept_resolver` VIVO) e `card_block.py` inteiro. Guard test na fase 0: pacote do motor
     proibido de importar os condenados.
  4. = Task B congelada (acima).
  5. = fallback dividido (acima).

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
- [CODE] **Latente: TCC NFD dotless-i no manifest** (`as-of 2026-07-01`, herdado do handoff 28/06 P4) — slug
  `aula-10-linguagens-reconhecıveis-e-linguagens-decidıveis` carrega U+0131 (NFD do macOS). Join por nome pode
  falhar silencioso. Fix: normalizar NFC no import. Não urgente; vigiar no crosswalk TCC.

## CODE — UI (Parte B de features backend já entregues)

- [CODE] Cronograma SARC: **tab em tabela + legenda**.
- [CODE] Guard de conflito override: **aviso no tab + botão "reverter p/ auto"**.

## DECISION

- [DECISION] **Sign-off §9 do spec do motor (2026-07-03)** — resoluções **9** (TCC topic-bridge) e **11**
  (aceite duplo contenção+cobertura) APROVADAS; **10** (`material_curation.json` keyed md5/pair_key) e
  **12** (voto aceito cego bounded, autoconfiança ignorada) APROVADAS **CONDICIONAIS à fase 3** —
  go/no-go da fase 3 decidido DEPOIS do recall medido do gate D4 (fase 1). Sem LLM, flagged = fila
  humana no Dashboard (MF: 18 casos; voto resolveria ~1/3 — saldo real nas regras finais = **+4**, não
  +5: `plano.pdf` sem janela não vota; 3 bibliografias nem chegam ao voto). Ambiguidade achada → §12 do
  spec: MARCO 1 converteu `plano.pdf` SEM janela, mas regra "voto bounded à janela" o proíbe — definir
  na fase 3. Escopo de ciclo: reorg física de `scripts/` só PÓS-motor (mapa adiado); modularização de
  `dialogs.py` (4.998 linhas) e sentença dos HTMLs (02–18/06, pré-motor) FORA deste ciclo; remoção de
  mortos = run dedicada (ver CODE).
- [DECISION] **bloco-15 over-merge (IA)** — bloco-15 = 01–08/06; merge **Semana 14** (dijkstra/hc-sa, sess 01,03/06)
  + **Semana 15** (minimax/listas, sess 08/06). **still-valid, verificado as-of reprocess IA 7561f5c.** Cura de timeline separada.
- [DECISION] **5 IA busca — bloco-12 vs bloco-13** — section "Semana 12 - Algoritmos de Busca", caem em **bloco-12**
  (Correção P1+Agentes, 18–20/05). MAS **bloco-13** (25/05, "Algoritmos busca") = candidato topic-match → **um bloco fora**.
  Mismatch Moodle×SARC persiste. **still-valid, verificado as-of 7561f5c.** Gold-relevant.
- [DERIVADO] **MARCO 0/1 EXECUTADOS (2026-07-01)** — validação do D8 com número (detalhe no log de
  decisões, seção D8): ordinal-no-nome morto por medição (DP-monotone = lift negativo); len-norm +6.5pp;
  **LLM 3/18→8/18 no flagged** (converte confusão-semântica, não grão-de-semana); global escopo-disamb
  58.1%→66.1% (empata funil). **Gargalo real = recall do gate D4** (11 confiante-errado cegos pro LLM).
  Scripts novos (uncommitted): `marco0_prova_deterministica.py`, `marco1_voto_llm.py`; sidecars
  `marco0_flagged_MF.json`, `marco1_votes_MF.json`. → **SPEC ESCRITO (2026-07-03)**:
  `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` incorpora D8-refinado (voto em "flagged OU
  série same-theme", autoconfiança ignorada, gate D4 = fase 1 com recall medido), TIER 0 dup-grouping
  (md5-gêmeos = 1 decisão), exclusão bibliografia/apoio do motor, aceite contenção+cobertura por provider,
  cache `material_curation.json` keyed por md5/pair_key (seed = votos MARCO 1). Resoluções de conflito na
  §9 do spec (TCC = topic-bridge, NÃO parse ordinal de "Semana N"). Próximo: plano fase 0 (`writing-plans`).
- [DERIVADO] **FASE 0 do motor de atribuição FECHADA (as-of 2026-07-07; código COMMITADO em 12 commits
  `f75d22b..fff7d47` na branch `feat/motor-atribuicao` — inclui o fix de review final
  `fff7d47` (janela-1 gated no tamanho da janela + funil unificado); papelada docs ainda sem commit)** —
  pacote isolado `src/builder/routing/motor/` (contracts, window_provider, disambiguator, anchor_engine),
  READ-ONLY, **NÃO integrado ao pipeline** (integração = FASE 4). Regressão global: suíte inteira
  **1688 passed / 4 skipped, 0 falha** (as-of pré-fix-final; +1 teste ref-fantasma depois); 28 testes do
  motor + 6 `tests/test_anchor_placement.py`
  (call-site velho intacto, FASE 0 é ADITIVA) todos verdes.
  **Probe externo** (`scripts/fase0_prova_motor_MF.py`, régua par-colapsada `pair_key`+`scorable==yes`):
  escopo-disamb MF **36/58 = 62.1%** (piso MARCO 0 A' = 59.7%, folga +2.4pp) → **VEREDITO FASE 0: PASS**
  (exit 0).
  **Gold embutido** (`tests/test_motor_golden_mf.py`, roda em CI): 45 casos mensuráveis; contenção
  **100%**; confiante-errado **0**; janela-1 OK.
  **Calibração final:** `MARGIN_TAU=0.45`, `W_SESSION_LABEL=1.0`, `W_TOPIC=0.6`; gate estrutural
  (decisão user 2026-07-07): `confident` exige `s2>0` (competição real) e decisão `flagged` nunca sai da
  band "alta" (capada em "media" — fecha vazamento de `confidence_band` no ramo flagged, `BAND_HIGH=0.50`).
  **Dívida FASE 1 (baselines conscientes aceitos no probe):** confiante-errado ≤7 e contenção-fora ≤2 na
  régua externa. Composição dos 7 confiante-errado: **2 poluição nome-do-curso** (`topic_text` do
  bloco-02 = "introducao metodos formais" contamina materiais que citam o nome da disciplina — candidato
  de calibração FASE 1) + **5 casos gold `discriminante=yes`** onde o motor reproduz a heurística antiga
  (recall do gate/TIER 3). Motor = subset EXATO dos 11 confiante-errado do marco0 (gate novo cortou
  11→7); seleção reproduz Config A' byte-a-byte.
  **Tensão "Verificação de Programas" (prevista no plano):** no gold EMBUTIDO o card tem `block_ids: []`
  → funil na CI, não exercível. No repo REAL a janela existe (labels, blocos 10-15) mas SEM bloco-09 →
  as 2 contenção-fora do probe. **PENDÊNCIA [USER]:** curadoria do `card_block_map` do repo MF (incluir
  bloco-09 na janela da seção "Verificação de Programas") ou reprocess; mutação do repo-tutor é ação do
  user na GUI — ver item espelhado em USER-SIDE.
  Guard AST do motor endurecido além do plano previsto (star-imports proibidos + acesso
  module-qualified detectado).
  **Fixes do review final (commit `fff7d47`):** fast-path janela-1 e funil `block_ref=""`
  corrigidos no fechamento (review final) — Protocols de `contracts.py` ainda divergem das
  assinaturas reais (`markdown`; shadowing `AnchorEngine`) = item FASE 1.
  **→ Números e dívidas desta entrada SUPERSEDED pela FASE 1 (entrada seguinte, 2026-07-07):**
  MARGIN_TAU agora 0.55; baseline confiante-errado agora 3; Protocols/unificação resolvidos.
- [DERIVADO] **FASE 1 do motor de atribuição FECHADA (as-of 2026-07-07; 8 commits `2e49ceb..ccea93c`
  na branch `feat/motor-atribuicao`, review final fable "Ready to merge: Yes" pós fix-wave)** —
  gate D4 calibrado COM RECALL MEDIDO (spec §7 fase 1). Report completo:
  `docs/reports/2026-07-07-fase1-recall-report.md`. Números: **recall do gate 0.824 (14/17)** vs
  referência proxy MARCO 1 0.577 (15/26); **confiante-errado 7→3**; **acurácia escopo-disamb
  62.1%→70.7%** (par-colapsada; piso HARD 59.7%); contenção-fora 2 (inalterada, pendência USER
  bloco-09 — agora custa também 1 confiante-errado). Gold embutido inviolado (contenção 100%,
  conf-errado 0). Suite **1701 passed / 4 skipped**. Levers: desconto nome-do-curso
  (`MotorContext.course_name`, −2 conf-errado, +8.6pp acc), `MARGIN_TAU` 0.45→0.55 (grade 36 pontos,
  −2 conf-errado, acc invariante), gate token-discriminante D4 literal (NEUTRO neste corpus — mantido
  por conformidade ao spec §3, custo 2 falso-alarme). Novos: `motor/metrics.py` (gate_report puro),
  `scripts/fase1_recall_gate_MF.py` (harness READ-ONLY, veredito HARD composto: recall ≥ 14/17 OU
  conf-errado ≤ 3, E > 0.577). Dívidas FECHADAS: poluição nome-do-curso, Protocols/shadowing
  (`AnchorEngineProtocol`), unificação `_card_entry`↔`card_block.normalized_card_map`. Dívidas que
  FICAM: hardening MotorContext (YAGNI), memoização `normalized_card_map` (FASE 4), resíduo TIER 3 =
  3 confiante-errado same-theme (Dafny/Hoare; 1 deles cai com curadoria bloco-09) + fila flag 37/59
  (23 falso-alarme, 63%) = O número do go/no-go FASE 3. Limitação documentada: desconto course_name
  em curso nomeado-pelo-tópico degrada para flag (nunca confiante-errado). Próximo: FASE 2 (P3 SO /
  P4 TCC); go/no-go FASE 3 = decisão USER com o report em mãos (sign-off condicional §9).
  **ADENDO auditoria do gold (2026-07-08, sign-off USER):** 7 rows do `ground_truth_MF.csv` com
  true_block_id stale (drift posicional pós-reprocess) re-rotuladas — números REAIS da FASE 1:
  **acurácia 82.8% / contenção 0 / confiante-errado 1 / recall 0.900**; resíduo TIER 3 = só
  `exerciciosdafny2`; fila flag 37 (28 certos). Pendência USER bloco-09 MORTA (card map estava certo).
  Baselines renegociados nos 2 probes. Ver item USER-SIDE riscado e report FASE 1 (adendo).
  Composição dos 10 pares errados restantes (report, tabela final): 6 = cluster indução×Isabelle
  05↔06 (grão-de-semana, LLM não converte — lever = pino/card fino), 1 = exerciciosdafny2 (confiante,
  candidato TIER 3), 2 = títulos 100% stem-genérico (introducao/revisao — sem sinal lexical), 1 =
  tiposindutivos (código sem léxico no roteiro). ~7/10 fora do alcance de scorer lexical → próximo
  ponto de acurácia = FASE 2/pinos, não calibração.
- [DERIVADO] **PRÉ-FLIGHT FASE 2 item 1 CONCLUÍDO (as-of 2026-07-08): golds SO/TCC/IA/ES2 FRESCOS —
  0 re-rotulagens necessárias.** Auditoria READ-ONLY via `scripts/audit_gold_freshness.py` (novo;
  checks MISSING_BLOCK/DATE_MISMATCH/ADMIN_TRUE/OUT_OF_WINDOW/PAIR_MISMATCH/ZERO_OVERLAP, filtra
  scorable=yes). Prova de frescor: `computed_block_id` congelado nos CSVs == computed atual do
  manifest (uuid→display) em **0 DIFF nos 4 cursos** (SO 38/38, TCC 35/35, IA 40/40, ES2 27/27;
  0 órfãos scorable); timelines intocadas desde 28/06–01/07 = época da rotulagem (01/07, pós-reprocess
  21/06). ES2 validado também por data_real ∈ período do bloco true em 100% dos rotulados. O drift do
  MF NÃO se reproduz. ZERO_OVERLAPs remanescentes = limitação do léxico (NP filtrado, semântica
  semáforos→sincronização), não drift. Casos SO contra-intuitivos (segmentação→bloco-12=enunciado TP2;
  IPC→bloco-05 com computed=bloco-07) são rótulos humanos deliberados CONTRA o computed — ficam.
  Probes fase0+fase1 re-rodados em par: ambos PASS (82.8% / conten 0 / conf-errado 1 / recall 0.900).
  Item 2 do pré-flight DECIDIDO (user, 2026-07-08): migração gold→block_uuid fica DÍVIDA para a
  FASE 4 (junto do trabalho de reprocess); regra vigente = `audit_gold_freshness.py` roda como
  PRÉ-GATE antes de QUALQUER medição contra ground_truth_* (especialmente pós-reprocess).
- [CODE] **Migrar ground_truth_*.csv de bloco-NN → block_uuid (FASE 4)** — decisão user 2026-07-08
  (pré-flight FASE 2 item 2). Inclui: 5 CSVs + eval_ground_truth + harnesses fase0/fase1 resolvendo
  uuid→display. Até lá, auditor de frescor é pré-gate obrigatório de medição.
- ~~A1 (lessons no fusor) — brainstorming antes de spec~~ **SUPERSEDED (2026-07-01)** — ver entrada
  Degrau 3a acima; sinal absorvido pelo motor, plano velho mirava o fusor que morre no cutover.
- [DECISION/CODE] **Refatoração futura: ingestão de material de APOIO (durável/intent, 2026-07-01)** — artigos
  web, papers e bibliografias ainda NÃO são ingeridos 100% no tutor (ex.: IA tem 3 entries sem `raw/`, 2 delas
  artigos-web). Fazer motor análogo ao de atribuição, mas para apoio/bibliografia — atribuir ao card/bloco
  certo SEM inflar verbosidade/custo do tutor (requisito explícito do user). Fora do escopo do motor atual;
  entra DEPOIS dele.
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
