# Pendências — tracker vivo

last_updated: 2026-08-05
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

- ~~[CODE] `gemini_client.py DEFAULT_MODEL = "gemini-2.5-flash"` APOSENTADO pela API~~ **FECHADO
  (F4 item 0, pré-flight — commits `8f73084`/`79c...` guard em `get_gemini_client`)**: `DEFAULT_MODEL`
  migrado para `gemini-3.5-flash` pinado + guard contra config persistido antigo vazando o modelo
  morto pro endpoint (review T1).
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
- [DERIVADO] **FASE 2 do motor de atribuição FECHADA (as-of 2026-07-09; código COMMITADO em 9
  commits `985351b..9119ac4` — 6 tasks + 3 fix-waves de review — na branch `feat/motor-atribuicao`)** — providers P3 (SO, data-no-nome)
  e P4 (TCC, topic-bridge) implementados + provados por réguas externas HARD. Report completo:
  `docs/reports/2026-07-09-fase2-providers-report.md`.
  **P3/SO** (`scripts/fase2_prova_SO.py`): cobertura **45.2% (19/42)**, colisões **0**, matriz gate
  {alta-ok 13, resto-ok 2, resto-err 4}, confiante-errado **0**, acurácia par-colapsada **77.8%**
  (14/18) vs baseline funil 47.4%; 100% das decisões via provider `data`. `DATE_DF_MAX` recalibrado
  na grade 1/2/3 (protocolo D4) e **mantido em 2** (empata com 3 no `alta-ok` máximo, desempate pela
  constante já vigente/validada na FASE 1 MF).
  **P4/TCC** (`scripts/fase2_prova_TCC.py`): pinos manuais **5/5** por interseção (contenção total
  3/5 — NP-completude perde bloco-21, Halteproblem perde bloco-10, métrica secundária sem piso),
  cobertura **83.3% (30/36)**, confiante-errado **0**, acurácia par-colapsada **84.2%** (19 pares) vs
  baseline funil 56.0%; breakdown por provider: manual 8/8=100%, topic 16/20=80%. `TOPIC_STEM_LEN=6`
  / `TOPIC_MIN_TOKEN=3` mantidos (grade não disparou — pinos 5/5 já no ponto default).
  **MF (regressão): intacto** — acc 82.8%, contenção 0, confiante-errado 1, recall 0.900; probes
  fase0/fase1 PASS em toda a fase. **Suite completa: 1722 passed / 4 skipped / 0 failed.**
  **Fila humana consolidada (go/no-go FASE 3): MF 37 + SO 6 + TCC 22 = 65 flagados** (SO/TCC
  derivados da matriz gate/banda — não expostos direto no output do probe original, confirmados por
  reexecução read-only contando `AnchorDecision.flag`, 0 mismatch contra `flag == (band != "alta")`).
  **Riscos residuais (não bloqueantes, ver report):** (1) ramo flagado do gate de data hardcoda
  `band="media"` — perde granularidade silêncio-lexical vs overlap-boilerplate na fila SO; (2)
  janela-1 vinda de provider `topic` NÃO passa pelo gate D4 (só `data` passa) — 0 ocorrências hoje no
  TCC, monitorar; (3) `TOPIC_MIN_TOKEN` piso-2 é no-op estrutural (assinatura de bloco tem piso-3) —
  calibração futura de tokens curtos exige assinatura própria do P4 nos dois lados; (4) réguas
  SO/TCC medem acurácia WHOLE-CASCADE por design, com linha `providers` denunciando mistura; (5)
  contenção total de pinos 3/5 (vs interseção 5/5, o aceite) — relevante se FASE 3+ exigir contenção
  dura multi-bloco; (6) memoização `_global_df`/`_modal_years`/`normalized_card_map` deferida pra
  FASE 4. Próximo: go/no-go FASE 3 = decisão USER com este report em mãos (sign-off condicional §9,
  resoluções 9/11 do spec já aprovadas).
- [DERIVADO] **FASE 3 do motor de atribuição FECHADA (as-of 2026-07-09; código COMMITADO Tasks 1-5
  `512afcd..c70c272` na branch `feat/motor-atribuicao`; Task 6 = esta medição real, uncommitted até
  este commit) — VEREDITO: FAIL HONESTO.** Report completo:
  `docs/reports/2026-07-09-fase3-llm-report.md`. Rodada real (3 rodadas, cap 20/rodada):
  **50 chamadas API tentadas, 30 úteis** (rodada 1 = 20/20 erro 404 — bloqueio de infra, não
  conteúdo: `gemini-2.5-flash` aposentado neste ambiente para `generateContent`; fix = trocar
  `gemini_model` pra `gemini-flash-latest` no `~/.gpt_tutor_config.json` pessoal, sem tocar
  código/repo; ver report). **Números**: lift **+1** (piso +4, FAIL) · confiante-errado **0**
  (piso cumprido — o único resíduo herdado, `exerciciosdafny2`, foi corrigido pelo voto) · rodada
  **completa** (48/48 votos cacheados, 18 seed MARCO 1 + 30 novos). Acurácia global par-colapsada
  82.8%→84.5% (48/58→49/58). **Achado central**: na fila FLAGADA (37/44, a fila que a TIER 3
  deveria reduzir) o saldo foi **ZERO** (28→28: 4 correções anuladas por 4 regressões); todo o
  lift (+1) veio do lado série-same-theme não-flagado (7/44, 6→7). Ou seja, medido honestamente,
  **o voto TIER 3 não reduziu a fila humana no MF** — só resolveu 1 caso pontual que já não
  estava na fila. 5 casos seguem não-conversíveis (cluster indução×Isabelle 05↔06 núcleo duro
  — 4 casos — + `tiposindutivos`); 2 dos 6 casos originalmente nomeados nesse cluster (FASE 1)
  CONVERTERAM nesta rodada, refutando a categorização binária "100% não-conversível". Regressão
  total: fase0/fase1/fase2-SO/fase2-TCC PASS intactos (rodam sem voter); suite **1743 passed / 4
  skipped / 0 failed**. Por spec §12 regra 4, **NÃO iterei prompt** — número é definitivo para
  esta rodada; decisão go-forward (aceitar lift menor com sign-off OU reverter GO da TIER 3) é do
  **user**, com o report em mãos. **Dívida #1 (band no ramo flagado, risco residual #1 da FASE 2)
  fica OPEN** — como o veredito é FAIL, a TIER 3 não "consome" o flag; N/A só se aplicaria em
  PASS. Plano **NÃO arquivado** (regra do brief: só arquiva em gate verde) — segue em
  `docs/superpowers/plans/2026-07-09-fase3-voto-llm.md` até a re-decisão do user.
- [DERIVADO] **FASE 3 ACEITA com piso revisado (as-of 2026-07-09, SIGN-OFF user, pós-experimento
  gemini-3.5-flash) — supersede o FAIL da entrada acima.** Hipótese do user (modelo aposentado +
  seed 2.5 deprimiram o lift) parcialmente CONFIRMADA: re-voto das 44 rows com `gemini-3.5-flash`
  PINADO (cache zerado, seed excluído, 44 chamadas, 0 erros, smoke de geração pré-rodada) =
  lift **+3** (6 conversões − 3 regressões), global par-colapsado **82.8%→87.9%** (51/58),
  conf-errado **0**. Variante offline "flagged-only" (série não vota) é PIOR: +2 e conf-errado
  volta a 1 (`exerciciosdafny2` só vota via série) — escopo flagged∪série do spec confirmado
  ÓTIMO; as 3 regressões (`exercicioscorrecaoterminacao`, `logicadehoare2`, `terminacao`) são
  todas FLAG (falso-alarme do gate D4 votando) — nenhuma regra de escopo as evita. Piso da régua
  renegociado ≥+4→**≥+3** (`LIFT_MIN=3`, baseline consciente; regressão futura <+3 = FAIL).
  **Dívida #1 (band no ramo flagado) → N/A** (GO aceito: TIER 3 consome flag, não band). Config
  do user pinada `gemini-3.5-flash` (era alias `gemini-flash-latest`); cache da rodada mista
  preservado em `material_curation_MF_2026-07-09_run1_mixed.json`. Resíduo pós-voto: 7 pares →
  checklist de PINOS (TIER 1, user na GUI): `exercicioscorrecaoterminacao`→bloco-11,
  `logicadehoare2`→bloco-10, `terminacao`→bloco-12, `provasindutivas-especificacoesrecursivas`
  (+`-arvores`/`-listas`)→bloco-06, `tiposindutivos`→bloco-15. Com pinos: 58/58 no gold (100%
  no gold ≠ 100% no curso). A [DECISION] D4×janela-1 abaixo vira item OBRIGATÓRIO do plano da
  FASE 4 (voter vai ligar).
- [DERIVADO] **FASE 4 do motor de atribuição FECHADA (as-of 2026-07-22; código COMMITADO
  `8f73084..480231a` na branch `feat/motor-atribuicao`; régua `fase4_prova_D9.py` = Task 11,
  commit `2fd725a`; fix-wave pós-review `54e7662..480231a`)** — AnchorEngine substitui `apply_anchor_placement` no call-site do reprocess,
  atrás de `use_anchor_engine` por-curso (precedência sobre a flag legada; caminho legado intacto
  até o cutover FASE 5); voter TIER 3 opt-in via `use_llm_voter`. **9 itens do handoff (0-8)
  FECHADOS:** item 0 (modelo Gemini morto → `gemini-3.5-flash` pinado + guard), item 1 (D4×janela-1
  — ver entrada riscada acima), item 2 (sidecar `material_curation.json` no repo-tutor +
  `prune()` merge-on-save), item 3/4 (`LlmVoter` thread-safe: lock, log de erro, `no_key`,
  `round_summary`, cache por content_key), item 5 (`motor/context.py` loader único +
  memoizações `_global_df`/`_modal_years`/`normalized_card_map` — fecha a dívida FASE 1 do mesmo
  nome), item 6 (gold→`block_uuid` — ver entrada riscada acima), item 7 (badges band/flag/provider
  no Timeline Dashboard, band autoritativa do motor), item 8 (`cronograma_health` lê a janela do
  motor quando `temporal_block_window` existe; S2 legado vira fallback só flag-OFF, pré-requisito
  nomeado da deleção FASE 5).
  **Número do aceite (spec §7), medido por `scripts/fase4_prova_D9.py`:** flag-OFF byte-idêntico ✓;
  flag-ON `computed_*` inalterado (só `temporal_*`) ✓; pino manual nunca sobrescrito (11 pinos,
  0 `TEMPORAL_KEYS` vazadas) ✓; dup-divergence 0 (TIER 0 por `content_key` md5) ✓; gold MF
  pair-colapsado **det 48/58 = 82.8% (conf-errado 1) · voter all-cache (cap=0) 51/58 = 87.9%
  (conf-errado 0)** — byte-idêntico aos baselines FASE 0/FASE 3, 0 chamadas API na rodada de prova.
  **VEREDITO FASE 4: PASS.** Regressão: 6 probes (fase0/fase1/fase2-SO/fase2-TCC/fase3/fase4) PASS
  + suite **1787 passed / 4 skipped / 0 failed** (pós fix-wave `54e7662..480231a`).
  **Review final whole-branch (fable): Ready to merge YES** — fix-wave fechou 1 Critical
  (C1: `resolve_temporal_block` agora resolve uuid→display no chokepoint leitor; producer intocado,
  flag-OFF byte-idêntico preservado) + 2 Important (I1: TIER 0 não atravessa fronteira de escopo —
  gêmeo md5 fora-de-escopo não herda nem apaga temporal; I2: `_build_motor_voter` usa a precedência
  real config > `GEMINI_API_KEY` do ambiente) + 7 minors fix-now da triage. Defer-F5 registrados
  no ledger `.superpowers/sdd/progress.md`.
  **2 adjudicações do controller registradas no ledger, durante a escrita da régua (Task 11):**
  (1) *defeito-de-plano — universo do gold-check.* O snippet do plano (Step 1) omitiu o filtro
  `is_out_of_disamb_scope` em `_gold_check`; sem ele a régua mediu as 66 rows scorable (incluindo
  as 8 TIER-2 fora do mandato do motor) em vez das 58 do universo disamb-scope que os baselines
  F0/F3 declaram — FAIL espúrio (74.2%/78.8%) mascarando comportamento byte-idêntico ao aceito.
  Fix: 1 guard-clause em `_gold_check` (skip out-of-scope), alinhando o universo medido ao
  universo declarado. (2) *precedente explícito F1 (BASELINE_RECALL=14/17 fração exata) — pisos
  em fração exata, não display arredondado.* `82.8`/`87.9` como floats literais eram o valor
  ARREDONDADO de `48/58`/`51/58`; `48/58 = 82.7586...` é `< 82.8` em ponto flutuante (comparação
  estrita), gerando 2º FAIL espúrio (det=False) mesmo com o universo já corrigido. Fix: pisos
  viram `48/58`/`51/58` (frações exatas); display em `%` mantido via `100 * PISO:.1f`. Nenhum piso
  foi *afrouxado* em nenhuma das duas correções — ambas alinham a MEDIÇÃO ao número já aceito, não
  mudam o número aceito.
  **Dívida nomeada nova [CODE]:** TIER-2 no gold MF (`trabalhos/provas/TDE`, 8 rows scorable) =
  **1/8 pelo funil** — categorias saem do motor via `_OUT_CATEGORIES` por design (janela-de-prazo
  real T1/T2→blocos 15/16 é dívida separada, ver "Fora de escopo" do plano F4); medição própria
  destas 8 rows entra no rollout FASE 5, não bloqueia o aceite F4 (que mede só o universo
  disamb-scope, por declaração explícita dos pisos).
  *Composição concreta no MF (diagnóstico do piloto 2026-07-22, verificado entry-a-entry):*
  `t1-2026-1`/`t2-2026-1` (trabalhos TDE) = alvo direto da janela-de-prazo; `t1-2026-1-thy`
  (codigo-professor) = companion do t1, herda a atribuição; `revisao-p1-gabarito` (provas) =
  **pino trivial na GUI** (mesmo bloco `5599d015` do `revisao-p1`, já pinado) — não precisa de
  código; `plano` (cronograma) = **funil deliberado** (plano de ensino não pertence a bloco;
  "corrigir" seria inventar pertencimento). Só 3 dos 5 dependem de código novo (o provider
  janela-de-prazo).
  Housekeeping: `docs/superpowers/plans/2026-07-10-fase4-integracao-d9.md` movido para
  `Feitos/` (gate verde). Reprocess REAL nos repos-tutor (escrever temporal/sidecar de verdade) e
  ligar `use_anchor_engine`/`use_llm_voter` em `SubjectProfile.feature_flags` = ação do user na
  GUI, curso a curso — rollout FASE 5.
- [DERIVADO] **Triage completa do review final whole-branch F4 (fable, 2026-07-22; veredito
  pós-fix-wave: Ready to merge YES).** Registro integral por decisão do user (inclusive os
  "ignore" — catalogados mesmo sem ação prevista):
  **FECHADOS na fix-wave (`54e7662..480231a`):** C1 uuid→display no leitor `resolve_temporal_block`
  (producer intocado); I1 TIER 0 `decided`-cache não atravessa fronteira de escopo (skip
  `is_out_of_disamb_scope` antes do lookup, ambas as ordens testadas); I2 `_build_motor_voter`
  com precedência real config > `GEMINI_API_KEY` do ambiente; T1a logger.info no remap
  RETIRED_MODELS; T6 testes pino-inválido/None-em-gêmeos; T7c asserts de `_run_anchor_engine_layer`
  com deepcopy (não-vácuos); T7d `exc_info=True` no warning da camada; T11a import morto +
  param `repo` não usado removidos da régua; T11b veredito imprime `voter=SKIPPED` sem cache;
  dup-div exclui entries sem temporal (evita FAIL espúrio com pino gêmeo em F5).
  **[CODE] Defer-FASE 5 (entram junto do rollout, não bloqueiam):** T1b combo da UI mostra modelo
  stale órfão (migração em `AppConfig._load` é o fix certo); T2b `load_repo_artifact` engole
  exceção com `{}` — timeline corrompida vira motor no-op silencioso (1 logger.debug basta);
  T3 `fase3_prova` vote_rows não filtra janela-1 (row nova flagged sem cache = "pend" perpétua no
  gate de completude); T4b lock do voter é por-processo (TOCTOU entre processos; single-writer
  hoje via task queue); T7a double-hashing md5 (live_keys + apply — compartilhar mapa de chaves);
  T7b sem teste e2e do gate via `regenerate_pedagogical_files` (elif verificado por inspeção;
  e2e entra na suite do cutover); T9a ref `None` vira `"None"` e sobrevive ao filtro do health
  (só manifest editado à mão aciona); herdados do review F3: parent-dir em
  `save_material_curation`, fold caso/acento em `source_section`, `match_window_ref`
  strip/casefold, truncamento do dry-run, stopwords PT no P4.
  **Ignore (catalogados, sem ação prevista — razões do reviewer):** T1c guard test exime
  `gemini_client.py` inteiro por nome (único uso legítimo de "gemini-2.5" vive lá); T1d fix-wave
  T1 rodou só `-k gemini` (superado: suite completa verde no head); T2a gate T2 re-rodou só 3
  probes (superado: Task 11 re-rodou os 6); T4a memória-vence em chave conflitante entre
  instâncias (mesma content_key = mesmo conteúdo, qualquer voto é válido); T8 teste não-leak
  do badge cobre só `computed_block_band` (motor_badge só lê temporal_*); T9b anotação `-> list`
  frouxa; T10a `true_of` chamado 3x/2x por row em SO/TCC (probe, custo desprezível); T10b
  fallback devolve uuid cru se bloco sem `id` (falha honesta de display em timeline malformada);
  T10c `migrate_gold_uuid` sem try/except (one-shot já executado); T11c divisão ok/tot duplicada.
- [DERIVADO] **Piloto flag-ON MF (2026-07-22, dry-run em memória — zero writes no repo-tutor):
  retrato do que `use_anchor_engine`+`use_llm_voter` fariam hoje no reprocess do MF.**
  67 entries → **51 com `temporal_*`** (bands 15 alta / 36 media; providers 9 manual / 6 labels /
  36 llm), **11 com pino manual** (motor respeita e limpa temporal — resolvidos por decisão
  humana, pino > temporal na cascata) e **5 TIER-2 fora-de-escopo** (composição acima). Voter
  100% cache da F3: 36 hits, **0 chamadas API**, 0 erros; **fila humana 0** (o cache cobre
  exatamente os casos flagáveis). Delta visível: 42 decisões confirmam o funil, **9 divergem** —
  por gold/auditoria-0807: `exerciciosdafny1` (12 vs 15), `exerciciosdafny2` (13 vs 11) e
  `revisao` (03 vs 02) são CORREÇÕES de erro do funil; `tiposindutivos` (13 vs 15) e
  `exercicioscorrecaoterminacao` (12 vs 11) são os erros residuais conhecidos (band media, nunca
  alta); `provas` (06 vs 05, alta) consistente com a régua (voter cw=0); `exemplos-zip`/
  `exercicios-arrays`/`exercicios-conjuntos` sem gold direto. Balanço flag-ON: **62/67 com dono
  certo** (51 motor + 11 pino), 1 pino trivial pendente, 3 aguardando janela-de-prazo, 1
  deliberadamente sem bloco.
  **[CODE] Pré-requisito do flip real:** o sidecar `material_curation.json` NÃO existe na raiz do
  `Metodos-Formais-Tutor` — fazer seed do cache F3 (`docs/reports/material_curation_MF.json` →
  raiz do repo-tutor) antes do 1º reprocess flag-ON, senão a 1ª rodada re-paga até 20 votos (cap).
- [USER/DECISION] **Auditoria .env (2026-07-22): armadilha de token Moodle stale.**
  `MOODLE_URL`/`MOODLE_TOKEN` existem no `.env` RAIZ e em `moddle/.env`; a raiz vence
  (os.environ carregado no import por `helpers._load_project_env_file`), mas a GUI
  (`save_moodle_token`, moodle.py:638) escreve SÓ em `moddle/.env` → renovar token pela GUI
  não tem efeito enquanto a cópia stale viver no raiz (falha silenciosa). Recomendação do
  controller: remover as chaves MOODLE do `.env` raiz (zero código; `moddle/.env` vira fonte
  única). Alternativa [CODE]: `save_moodle_token` fazer merge no raiz e aposentar `moddle/.env`.
  DECISÃO PENDENTE do user.
- [USER] **`MOODLE_PRIVATE_TOKEN` é chave morta** — presente no `.env` raiz e documentada no
  `.env.exemple`, mas ZERO consumidores no código (grep 2026-07-22). Remover do `.env` e do
  template (o template hoje ensina a criar uma chave que não faz nada).
- [CODE] **`datalab_client` depende de import transitivo de `helpers` para ver o `.env`** —
  lê `os.environ` em call-time sem carregar o `.env` por conta própria; hoje todos os chamadores
  (engine, dialogs) importam helpers antes, mas um script standalone futuro que o use direto
  não veria as chaves. Fix barato quando tocar o arquivo: import de helpers (ou chamada explícita
  ao loader) no topo do datalab_client.
- [DERIVADO] **Provider janela-de-prazo (TIER 2) ENTREGUE (2026-07-22, commits `b64d983..6d1418a`,
  7 commits; spec `2026-07-22-janela-de-prazo-tier2-design.md`, plano em plans/).** Probe-first:
  `fase5_prova_tier2.py` cravou baseline **1/8** ANTES de código (universo 8 rows out-of-scope,
  guard n==8). Produtor: `extract_assign_deadlines_detailed` (um due por módulo, sem colapso) +
  `assign_dues` aditivo no card map. Motor: `due_window.py` (tier2_due_scope, matching stem com
  guard de conflito, containment/straddle D-A/D-B, band D-D, nunca chuta) + wiring na cascata
  `pino > tier2 > out-of-scope` (sem dup-cache no TIER-2, lição F4 I1). Review final whole-branch
  (fable) + fix wave + re-review: **READY TO MERGE YES**. Régua: 6 probes byte-idênticos + fase5
  baseline-only PASS; suite ~1806/4/0. **Invariante testado**: true-set do tier2_due_scope ⊂
  is_out_of_disamb_scope (flag-ON fora do TIER-2 idêntico ao pré-branch por construção).
  **[USER] Pré-requisitos da medição target (piso 4/8, cw 0)**: (a) sync Moodle do MF na GUI
  (popula assign_dues real); (b) **card `source=="manual"` NUNCA ganha assign_dues**
  (merge_card_block_map) — se o piloto pinar o card TDE manualmente, o 4/8 fica inalcançável POR
  DESIGN; interpretar FAIL com isso em mente antes de culpar o provider. FAIL = resultado honesto.
  **[CODE] residual cosmético**: `mine = _stems(...)` computado 2× em `_match_due` (hoist de 1
  linha, minors-batch futuro).
- [DERIVADO/DECISION] **Medição TARGET da janela-de-prazo EXECUTADA (2026-08-03): FAIL honesto
  1/8 (piso 4/8) · cw=0.** Sync do MF rodou HEADLESS (token `moddle/.env` + `MoodleClient` +
  `backfill_repo_signals_consumed`, mesmo caminho da GUI; MF ainda visível na matrícula,
  id=92717) — `assign_dues` real populado, card TDE `source=labels` (caveat do pino manual NÃO
  se aplicou). Causa do FAIL: **os dados reais do Moodle falsificam a inferência do design**
  (spec §6 já hedgeava: "dues dos exemplos são INFERÊNCIA do gold"). Três quebras verificadas
  na API: (1) os 2 assigns do card TDE chamam-se ambos "Sala de entrega" — SEM stem t1/t2 →
  matching D-C nunca casa → funil (por isso 1/8, não cw). (2) Mesmo casando por posição: due
  estruturado do T1 = 2026-05-06 (stale — professor moveu a entrega; a sala real do T1 é o
  FORUM "Sala de Entrega (10/06)" na seção Verificação de Programas, outro card) → containment
  daria bloco-11 ≠ gold bloco-15 = confident-wrong band alta. (3) Due do T2 = 2026-07-06 cai
  DENTRO de bloco-18 [06/07..06/07] (dia-único de devolução) → containment daria bloco-18 ≠
  gold bloco-16 = segundo confident-wrong. **D-E (nunca chuta) foi o que segurou cw=0** — a
  recusa por falta de stem evitou 2 erros confiantes. Spec §12 regra 4: FAIL registrado, ZERO
  re-tuning. Redesign (dues cross-card/forum, ordinal por label, due→bloco-de-conteúdo-anterior)
  = decisão de design NOVA do user, não patch. Semestre 2026/2 já visível na matrícula — cursos
  novos são o teste out-of-sample natural do provider como está.
- [DERIVADO] **GOLD t1/t1-thy CORRIGIDO bloco-15 → bloco-11 (2026-08-03, autorizado user).**
  Investigação pós-FAIL derrubou a inferência da spec F5: probe one-off do LlmVoter (0/3, cache
  isolado em scratchpad, 3 calls) expôs que conteúdo do T1 = Isabelle/indução, não Dafny →
  auditoria via API Moodle com evidência DEFINITIVA: submissão real do T1 = **2026-05-05 15:56**
  (assign 212883, `mod_assign_get_submission_status`) → due 06/05 do Moodle era CORRETO, não
  stale; fórum "Sala de Entrega (10/06)" ≠ T1 (são exercícios Dafny — disc. "Humberto - Fila
  Ilimitada" 10/06). T2 submetido 2026-06-27 (assign 215115) → gold bloco-16 confirmado.
  **Decisões user**: semântica do trabalho = ÉPOCA DE ENTREGA; fonte de verdade = Moodle
  ("geralmente a mais correta"). Auditor de frescor MF: hard=0 (ZERO_OVERLAP em t1/t2 = suspeita
  soft esperada de PDF de trabalho, 47 rows na mesma condição). Probe fase5 pós-correção:
  FAIL 1/8 esperado (provider ainda decide por stem/containment — F5b pendente). **[DECISION]
  F5b proposto (aguarda autorização)**: (1) matching posicional `label → resources → assign` na
  ordem da seção (mata dependência de stem); (2) D-A revisada: "último bloco DE CONTEÚDO com
  `period_end <= due`" no lugar de containment puro (t1: 06/05→bloco-11 ✓; t2: 06/07→pula
  17/18 sem tópicos→bloco-16 ✓). Piso 4/8 mantido, cw=0 mantido.
- [DERIVADO/DECISION] **Medição TARGET pós-F5b EXECUTADA (2026-08-03): PASS 4/8 (piso 4/8) ·
  cw=0.** Re-sync HEADLESS do MF (mesmo caminho `MoodleClient` + `backfill_repo_signals_consumed`
  usado no FAIL 1/8 anterior) gravou `file_dues` real no card TDE: `t1_2026_1.pdf`/
  `t1_2026_1.thy` due `2026-05-06`, `t2_2026_1.pdf` due `2026-07-06` (posicional, `source=
  structured`); re-sync também gravou uma key extra `"arquivo .thy.thy"` (due `2026-05-06`),
  vinda de um resource `.thy` com nome genérico na mesma seção — observado, não-bloqueante,
  nenhuma assertiva afetada. Probe `fase5_prova_tier2.py`: `t1→bloco-11 OK, t1-thy→bloco-11 OK,
  t2→bloco-16 OK, revisao-p1-gabarito→bloco-07 OK` — as 4 previsões exigidas pela spec F5b
  bateram exatamente; `plano`/`archive-of-formal-proofs`/`aws-encryption-sdk`/`eth2` seguem sem
  match (fora de escopo por design, D-E). Confirma a virada de causa registrada no FAIL: a
  correção veio de DOIS ajustes do F5b, não um só — (1) matching posicional `file_dues` (stem
  nunca casaria "Sala de entrega") e (2) revisão da semântica de janela D-A→D-H/D-I ("último
  bloco DE CONTEÚDO com period_end <= due"; blocos administrativos como bloco-17/18 nunca
  ancoram) — por isso t2 cai em bloco-16, não no confident-wrong bloco-18 que containment puro
  daria. Régua flag-OFF (6 probes) byte-idêntica: fase0 82.8%/conten 0/cw 1 · fase1
  9/10 · fase2-SO 45.2%/0/0 · fase2-TCC 5/5 pinos+83.3%/0 · fase3 lift +3 sem API nova · fase4 det
  48/58 cw1, voter 87.9%/cw0. Suite: 1816 passed, 4 skipped. Head dos commits F5b: `843475f`
  (produtor `extract_file_dues` posicional), `1d39cb4` (motor `_match_due` posicional +
  âncora bloco-de-conteúdo).
- [DERIVADO/DECISION] **Task 3 rollout flag-ON MF (2026-08-04): reprocess REAL executado, gate
  HARD-drift (gate_mf.py) PASS, mas gate duro do voter FALHOU (1 chamada API nova) → ROLLBACK,
  campanha PARADA para sign-off.** `python scripts/reprocess_assignments.py --flags
  use_anchor_engine,use_llm_voter` rodou sem traceback (`bloco 66/67 -> 66/67`). gate_mf.py:
  **PASS exato** — 54/54 `temporal_block_id` (51 piloto + 3 tier2), 11/11 pinos intactos e
  LIMPOS de temporal, `t1-2026-1`/`t1-2026-1-thy`→bloco-11, `t2-2026-1`→bloco-16 (bate 100% com
  o probe fase5_prova_tier2.py), `plano`/`revisao-p1-gabarito` corretamente fora do temporal.
  **Mas** `material_curation.json` foi de 44→45 votos: 1 chamada Gemini nova real (content_key
  `7fd46c78cec5e28c6090392b3057fb20`, resultado `bloco-16`/`gemini-3.5-flash`) — viola a premissa
  "cache 44 votos deve cobrir" das regras da task. *(Correção pós-diagnóstico, ver entrada Fix
  round 1 abaixo: essa chave NÃO é de `t2-2026-1` — é de `verificacaomodelos`, material de aula
  in-scope; a coincidência de bloco (bloco-16) é conteúdo real, não scope-leak.)*
  **Causa provável, não confirmada como bug**: o probe one-off do LlmVoter usado na correção do
  gold t1/t1-thy (entrada acima, "GOLD t1/t1-thy CORRIGIDO") rodou com **cache isolado em
  scratchpad** (por design — `material_curation_path()` documenta que probes nunca escrevem no
  path de produção), então aquele voto NUNCA foi mesclado no seed de 44 usado no Task 2 — o
  conteúdo de `t2-2026-1` provavelmente nunca tinha sido votado no path de produção antes desta
  rodada. Se essa leitura estiver certa, o novo voto era estruturalmente inevitável (conteúdo
  novo do tier2, entregue DEPOIS do piloto 36-hit de 2026-07-22) e não uma regressão do motor —
  mas isso é INFERÊNCIA, não confirmado por ninguém com autoridade para relaxar o gate.
  **Evidência adicional**: o método de verificação prescrito na brief (`Select-String` no log do
  reprocess por `gemini|voter|vote`) NÃO detecta nem chamadas nem cache-hits — o `LlmVoter` só
  usa `logger.info`/`logger.warning` (sem handler pro stdout no script headless), nunca `print`;
  o log real tinha só a linha `[flags] ...` (falso-match em "voter"). A verificação confiável foi
  diff direto de `material_curation.json` (contagem de votos + chave nova) contra o seed original
  em `docs/reports/material_curation_MF.json`.
  **Ação tomada**: `git checkout -- .` no repo-tutor MF (reverteu manifest.json + 8 artefatos
  regenerados a `8ea55de`, confirmado 0 `temporal_block_id` pós-revert); flags MF revertidas em
  `subjects.json` (backup do Task 2); **desvio deliberado da Step 5 da brief**: NÃO rodei
  `git clean -fd` — `material_curation.json` (untracked, 45 votos) foi preservado de propósito
  (backup extra em `<scratchpad>/material_curation.json.post-reprocess-45votes.json`) porque
  apagá-lo destruiria o voto já pago sem necessidade — um retry vai bater cache 100% (0 chamadas
  novas de verdade) em vez de re-pagar. Nada foi commitado no repo-tutor MF; `src/` do motor
  intocado. **Recomendação para quem retomar**: revisar se "1 voto novo para conteúdo tier2
  genuinamente novo (nunca votado no path de produção antes)" é aceitável como exceção pontual
  ao gate duro; se sim, re-rodar Task 3 sem modificação (cache já cobre as 45, deve fechar 0/0) e
  seguir para commit. Sem sign-off, campanha permanece PARADA nesta task (branch
  `feat/motor-atribuicao`, sem push).
- [DERIVADO/DECISION] **Fix round 1 — CASE B confirmado por 2 ângulos, retry limpo, 1 divergência
  explicada segura o commit (2026-08-04).** Controller adjudicou: diagnosticar dono do voto +
  wiring antes de decidir CASE A (scope-leak, não fazer retry) vs CASE B (inevitável, prosseguir).
  **Dono do voto**: `content_key()` (`llm_vote.py:49-62`) rodado sobre as 67 entries → a chave
  nova pertence a `verificacaomodelos` (categoria `material-de-aula`, in-scope normal), NÃO a
  `t2-2026-1`. **Wiring**: `apply_anchor_engine()` (`apply.py:53-103`, cascata pino > tier2 >
  out-of-scope > engine) — `tier2_due_scope(entry)` (`due_window.py:23-29`, cobre category
  trabalhos/provas) sempre `continue` antes de alcançar `engine.resolve()`/voter;
  `resolve_due_window()` é aritmética pura, zero import de `LlmVoter` (docstring: "NUNCA
  disambiguator, NUNCA voto LLM"). Confirmado empiricamente pós-retry: `t1-2026-1`/`t1-2026-1-thy`/
  `t2-2026-1` têm `temporal_block_provider=due-window` (nunca `llm`). **CASE B confirmado** — retry
  autorizado. **Retry**: reflip flags, reprocess re-executado sem traceback, `material_curation.json`
  45→45 (0 chamadas novas, 0 chaves alteradas), `gate_mf.py` PASS 8/8 idêntico. Assertivas novas:
  t1/t1-thy `due-window/due-contain/alta/False`, t2 `due-window/due-straddle/media/True` (bate
  exato com a previsão do controller). Distribuição dos outros 51: real **9 manual/5 labels/37
  llm** vs piloto **9/6/36** — 1 unidade migrou de `labels`→`llm`, é a mesma `verificacaomodelos`
  (pós-retry: `provider=llm/band=media/flag=False`, assinatura clássica de aceitação do voter) —
  causa já diagnosticada, sem sinal de problema adicional. `auto_tags bloco:` comparado nas 67
  entries completas (não amostra): zero diffs, funil intacto. **Apesar da explicação completa,
  segui a instrução literal do controller ("divergência = pare, sem commit") e NÃO commitei** —
  não substituí o critério explícito por julgamento próprio uma 2ª vez na mesma task.
- [DERIVADO/DECISION] **Ruling final do controller (2026-08-04): divergência ACEITA, commit
  LIBERADO e EXECUTADO — `Metodos-Formais-Tutor` commit `c7b7498`.** Adjudicação completa:
  **(a)** 1ª chamada API estruturalmente inevitável — conteúdo de `verificacaomodelos` nunca
  tinha voto em produção (probe do gold t1/t1-thy, 2026-08-03, usou cache ISOLADO em scratchpad
  por design, nunca mesclado no seed). **(b)** Voto rastreado por `content_key()` até uma entry
  in-scope normal (`verificacaomodelos`, categoria `material-de-aula`) — NÃO `t2-2026-1`; wiring
  de `apply_anchor_engine()` (`apply.py:53-103`) prova que `trabalhos`/`provas` (cascata
  `tier2_due_scope` → `resolve_due_window`, sempre `continue` antes do `engine.resolve()`/voter)
  nunca alcançam o voter — decisão do user 2026-08-03 ("voter para trabalhos DESCARTADO")
  preservada intacta, zero scope-leak. **(c)** Retry fechou 0 chamadas novas
  (`material_curation.json` 45→45, 0 chaves alteradas). **(d)** `gate_mf.py` PASS 8/8 + assertivas
  novas exatas (`t1-2026-1`/`t1-2026-1-thy` → `due-window/due-contain/alta`; `t2-2026-1` →
  `due-window/due-straddle/media/flag=True`) + `auto_tags bloco:` zero-diff nas 67/67 entries
  completas. **(e)** Distribuição de providers nos 51 não-tier2 **9 manual/5 labels/37 llm vira o
  novo valor de referência do rollout MF** (substitui o piloto 9/6/36 de 2026-07-22) — adjudicado
  com evidência de gold: `docs/reports/ground_truth_MF.csv` tem `verificacaomodelos → bloco-16`
  (block-direct, clean, scorable=yes) — o voto novo colocou o material no dono CERTO por gold,
  é correção da era-`labels` (que resolvia sem voto), não regressão. **(f)** Autorização de sessão
  do user: "fazer trilha 1" (cutover fora da campanha, decisão registrada em
  `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/progress.md`). Concern residual PARQUEADO
  como minor deferred (não investigar): contagem de linhas dos `.md` gerados variando entre as 2
  rodadas do reprocess (hipótese não confirmada: ordenação não-determinística de `set()` Python em
  `detect_same_theme_series`) — resultados estruturais (contagens/campos temporal_*/providers/
  auto_tags) foram idênticos nas duas rodadas em todos os pontos verificados; só a formatação de
  índices .md pode ter variado. Detalhes completos (diagnóstico, retry, evidências, self-review)
  em `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-3-report.md`.
- [DERIVADO/DECISION] **Rollout flag-ON MF EXECUTADO (2026-08-04): reprocess REAL finalizado, gate HARD-drift PASS, commit `c7b7498` gravado.** Reprocessamento com flags `use_anchor_engine=True`/`use_llm_voter=True` rodou sem traceback (`bloco 66/67 → 66/67`, manifest backup `manifest.json.bak`). **Gate duro gate_mf.py PASS 8/8 exato:** 54/54 `temporal_block_id` (51 piloto + 3 tier2 F5b), 11/11 pinos intactos/limpos de temporal, `t1-2026-1`/`t1-2026-1-thy` → bloco-11/alta/due-contain, `t2-2026-1` → bloco-16/media/due-straddle/flag=True (provider due-window em 100% dos 3 tier2), `plano`/`revisao-p1-gabarito` corretamente no funil. **Voter retry: PASS limpo** — `material_curation.json` 45→45 votos, 0 chamadas API novas, 0 chaves alteradas (cache 45 cobriu 100%, voto novo da rodada 1 já adjudicado CASE B pelo controller). **Distribuição de providers nos 51 não-tier2:** **9 manual/5 labels/37 llm** (nova referência do rollout MF, substitui piloto 9/6/36 de 2026-07-22) — migração labels→llm é a mesma `verificacaomodelos` (contenção gold bloco-16, scoreável=yes), correção da era-labels, não regressão. **Régua completa pós-flip: 7 probes + pytest 100%** (Task 4 medição) — fase0 48/58 conten0 cw1 · fase1 recall 9/10 · fase2-SO cobertura 45.2% colisões 0 cw0 · fase2-TCC pinos 5/5+83.3% cw0 · fase3 lift +3/0 API · fase4 det 48/58 cw1, voter 51/58 cw0 calls0 byte-idêntico flag-OFF · fase5 target PASS 4/8 cw0 (t1/t1-thy/t2/revisao-p1-gabarito 4 certos, plano/archives 4 fora-escopo) · **pytest 1820 passed / 4 skipped / 0 failed** — zero regressão entre Tasks 3/4. **Gold MF: 67/67 `auto_tags bloco:` zero-diff** — funil intacto (verificação programática completa, não amostra). **Achado colateral (não-MF, pré-existente):** `audit_gold_freshness.py` hard=1 em SO (lista2 ADMIN_TRUE + ZERO_OVERLAP, title="lista2" não casa regex `ASSESS_TITLE_RE`) — investigação provou scope pré-existente (timeline_index SO datado 28/jun, anterior à campanha; repo SO-Tutor não tocado pela task; heurístico ADMIN_TRUE + estado local antigo). Registrado em pre-flight do rollout SO, não-bloqueante para MF. **Flags duráveis ON:** `subjects.json` (`%APPDATA%\GPTTutorGenerator\`) com `Metodos-Formais.feature_flags = {use_anchor_engine: true, use_llm_voter: true}` persistido (pós-reprocess, pré-commit). **Decisions de sessão (user autorização 2026-08-03):** cutover via FASE 5 fora desta campanha (rollout é FASE 5b trilha 1, não integração global), push antes do cutover (commit MF em main, flags persistidas, sem merge para canário/staging — controle de blast-radius da user). Commit HEAD do MF: `c7b7498` (`rollout flag-ON: use_anchor_engine + use_llm_voter (temporal_* reais; gate HARD-drift PASS)`). Detalhes completos (adjudicação CASE B, retry, wiring tier2, step-by-step) em `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-3-report.md` (Task 3) e `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-4-report.md` (Task 4 régua). Campanha rollout-flag-ON trilha 1 **FECHADA, porta aberta para Task 6 (rollout SO) e Task 7 (trilha 2)** — não há blokers estruturais; próximas trilhas testam isolamento de cursos (SO tópico, TCC topic-bridge, ES2 data). **AVISO operacional:** reprocess headless futuro do MF exige `--flags use_anchor_engine,use_llm_voter` (flags não persistem no manifest; headless não lê subjects.json).
  **[USER] Pré-requisitos de rollout flag-ON em curso NOVO (review final F5b)**: (a) o filtro
  de bloco-de-conteúdo (D-H) usa `topics` — campo OPCIONAL no schema v4; curso com timeline
  sem topics populado deixa o provider silenciosamente morto (funil total, honesto mas
  invisível) — antes do flag-ON, garantir topics OU migrar o filtro para `kind` (campo
  required, enum tipado; candidato a F6/minors-batch com re-medição). (b) Limite conhecido da
  herança posicional: arquivo postado ENTRE o assign do grupo N e o label do grupo N+1
  herdaria o due do grupo N+1 (inexistente no MF atual; fix de 1 linha + teste + re-medição
  quando o produtor for tocado de novo). **[CODE] minors-batch F5b (review final, deferred
  com ruling)**: filtro de `extract_file_dues` não exige `fileurl` (diverge de
  `iter_section_files` → savename key pode divergir; chave por filename original cobre);
  `file_dues` com due vazio cai no fallback stem (produtor nunca emite — gate `if due:`);
  imports function-local em `_module_due`/`extract_file_dues` (estilo da casa); hoist
  `mine=_stems()` 2× herdado de F5.
- [USER/DECISION] **Pre-flight rollout SO (2026-08-04): flip ADIADO — hard=1.** Auditoria `audit_gold_freshness.py --course SO` (`as-of 2026-08-04`): 42 entries scorable, 21 suspeitas (hard=1). Única row com hard-flag = `lista2` [ADMIN_TRUE, ZERO_OVERLAP] true=bloco-17, kind=assessment, título="lista2" não casa regex `ASSESS_TITLE_RE` (label=1 dia · 25/06/2026). **Achado PRÉ-EXISTENTE:** timeline_index SO datado 28/jun (anterior à campanha); Sistemas-Operacionais-Tutor não tocado pela task; heurístico ADMIN_TRUE reproduz estado pré-existente (não regressão do motor). **Regra não-negociável:** medição só com hard=0 e gold muda SÓ com evidência + autorização do user → flip SO bloqueado até ruling do user sobre lista2 (re-rotular true_block OU confirmar bloco-17 como legítimo — lista de revisão de prova). **Pré-requisitos técnicos SATISFEITOS:** baseline fase2_SO 45.2%/0/0 segue válido e byte-idêntico (medido 2026-08-04); topics 19/21 blocos ok (ZERO_OVERLAP = limitação de léxico em nomes como "segmentação" sem overlap semântico com conteúdo bloco-12=TP2, não erro de placement); material_curation.json próprio na raiz do SO-Tutor presente (cache voter local; flip futuro liga use_anchor_engine+use_llm_voter normalmente). **Decisão:** SO flip adiado até autorização do user; Task 7 (TCC trilha 2) pode prosseguir em paralelo (cursos independentes). **Report completo:** `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-6-report.md`.
- [DERIVADO/DECISION] **Rollout flag-ON TCC BLOQUEADO (2026-08-04): gate estrutural (b) funil FALHOU — achado PRÉ-EXISTENTE e ORTOGONAL às flags, confirmado por diagnóstico; sem commit, flags revertidas.** Pre-flight `audit_gold_freshness.py --course TCC`: hard=0 (42 rows, 8 suspeitas ZERO_OVERLAP não-hard). Baseline `fase2_prova_TCC.py`: pinos 5/5 + cobertura 83.3% (30/36) + cw=0 — byte-idêntico ao aceito. Snapshot pré-rollout: `TCC-Tutor` commit `28bb29f`. Flip aplicado e verificado por round-trip (`Teoria da Computabilidade e Complexidade.feature_flags = {use_anchor_engine:true, use_llm_voter:true}`; MF e SO confirmados intocados no mesmo round-trip). Reprocess (`--flags use_anchor_engine,use_llm_voter`) rodou sem traceback: `bloco 27/27 → 27/27`. **Voter SEM cache prévio (TCC não tinha `material_curation.json` na raiz): 16 votos NOVOS pagos (Gemini `gemini-3.5-flash`), todos `confianca=alta`, 0 fila humana (nenhum `temporal_block_flag=True`)** — abaixo do cap built-in 20. **Gate estrutural a/c/d PASS:** (a) os 2 únicos `manual_timeline_block_id` do manifest (`plano-de-ensino`, `3d-matching`) preservados byte-idênticos, nenhum com `temporal_block_id` sujo. (c) 19/27 entries com `temporal_block_id`: providers `{llm:16, manual:1, topic:2}`, bands `{media:16, alta:3}`, methods `{llm:16, janela-1:1, disamb:2}` — zero entries de categoria out-of-scope (trabalhos/provas/cronograma/etc.) com temporal fora de due-window. (d) `material_curation.json` criado na raiz, 16/20 votos. **Gate (b) FUNIL FALHOU:** 4/27 entries mudaram `auto_tags bloco:` entre `manifest.json.bak` (pré) e `manifest.json` (pós) SEM nenhum `temporal_block_id` associado (motor não tocou essas entries — todos os campos `temporal_*` = None nelas): `3dm-caetano-gabriel-e-gustavo` bloco-22→16, `cubic-3-edge-coloring` bloco-26→16, `integer-programming-0001` bloco-13→16, `programacao-inteira-01-20260617-154423-0000` bloco-13→16 — exatamente as mesmas 4 (de 8) linhas já flagueadas `ZERO_OVERLAP` no pre-flight (workshop "Semana 14 - Apresentações T2", conteúdo de teoria dos grafos sem overlap léxico com o vocabulário do curso). **Diagnóstico (prova de causa):** árvore revertida pro snapshot `28bb29f` e `reprocess_assignments.py` rodado SEM `--flags` (flag-OFF puro) como controle — a MESMA drift bloco-22/26/13/13→16 reproduziu IDÊNTICA nas mesmas 4 entries, 0 `temporal_block_id` gerado. **Conclusão: instabilidade do funil-base (recompute de `auto_tags bloco:` fora do anchor engine) é PRÉ-EXISTENTE e ORTOGONAL ao flip `use_anchor_engine`/`use_llm_voter`** — não é regressão desta task, mas viola a letra do gate "(b) zero mudanças" tal como especificado na dispatch. **Ação tomada (sem mandato para autorizar unilateralmente a exceção):** `TCC-Tutor` revertido (`git checkout -- .`) ao snapshot `28bb29f` (working tree limpa; `material_curation.json` de 16 votos PRESERVADO untracked, para reaproveitar cache em retry e não pagar de novo); `subjects.json` revertido (`Teoria da Computabilidade e Complexidade.feature_flags = {}`; MF/SO/IA/ES2 confirmados intocados). **Nenhum commit feito em `TCC-Tutor` nem push.** Pendência: ruling humano sobre se a drift do funil-base nas 4 entries de workshop (pré-existente, comprovadamente independente do flip, mesmas 4 já suspeitas no gold) é aceitável para prosseguir com o rollout TCC, ou se exige correção separada do funil-base antes do flip (fora do mandato desta task — proibido tocar `src/`, proibido re-tuning). Retry recomendado após ruling: reflip + reprocess deve reaproveitar os 16 votos já pagos (cache bate por `content_key` md5) e fechar 0 chamadas API novas. **Report completo:** `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-7-report.md`.
- [DERIVADO/DECISION] **Fix round 1 — rollout flag-ON TCC (2026-08-04): controller ACEITOU condicionalmente a exceção do gate (b) e pediu critério decisivo mensurável; critério decisivo FALHOU → flip TCC ADIADO (bug funil-base, mesmo tratamento do SO), rollback completo, sem commit.** Ruling do controller sobre o BLOCKED anterior: experimento de controle (drift reproduzido com flags OFF) aceito como prova de causa ortogonal — não é aceitação cega, decisão final condicionada a medição. Executado: **(1)** re-flip TCC (`feature_flags={use_anchor_engine:true, use_llm_voter:true}`), MF confirmado ON no mesmo round-trip. **(2)** reprocess retry sem traceback (`bloco 27/27 → 27/27`); `material_curation.json` **16→16 votos, 0 chamadas novas** (diff de chaves: `novas={}`, `removidas={}` — cache cobriu 100%, dentro da tolerância ≤2). **(3)** gate a/c/d PASS de novo (idênticos ao round anterior); gate (b) restrito: drift bateu **exatamente** as mesmas 4 entries do experimento de controle (`3dm-caetano-gabriel-e-gustavo`, `cubic-3-edge-coloring`, `integer-programming-0001`, `programacao-inteira-01-20260617-154423-0000`), nenhuma entry adicional — condição do controller satisfeita nesse ponto. **(4) CRITÉRIO DECISIVO — MISTO:** `audit_gold_freshness.py --course TCC` pós-reprocess = **hard=0** (idêntico, mesmas 8 suspeitas ZERO_OVERLAP) → PASS; mas `fase2_prova_TCC.py` pós-reprocess **NÃO bateu idêntico**: pinos seguem 5/5 e cobertura 83.3%, porém **`confiante-e-errado` foi de 0 para 1** (`aula-01-apresentacao-da-disciplina-...`, computado=bloco-02, gold true=bloco-01, provider=`topic`) e a acurácia par-colapsada subiu 84.2%→89.5% (par-colapsada 16/19=84.2%→17/19=89.5%; acc topic bruta 16/20→17/20) — **VEREDITO FASE2: FAIL**. Isso viola a letra do critério ("AMBOS idênticos") → **rollback obrigatório**. **Fato registrado sobre as 4 entries do gate (b):** todas têm row no gold TCC (`scorable=yes`, `true_block_id=bloco-24`), mas o `computed_block_id` congelado no CSV já era bloco-22/26/13/13 (ERRADO vs bloco-24) **antes** desta task tocar qualquer coisa — a drift do funil-base trocou um valor errado por outro valor errado (bloco-16), não mudou o veredito de correção dessas 4 linhas especificamente. **O achado novo e mais sério é `aula-01`:** seu `auto_tags bloco:` no manifest (`bloco-02`) ficou byte-idêntico nas 3 fotografias comparadas (pristine pré-reprocess, 1º run flag-ON, retry flag-ON) — a mudança NÃO é no funil-base desta vez. O que mudou foi que `aula-01` passou a ter `temporal_block_id` populado via voter LLM (`provider=llm`, `band=media`, voto cacheado do 1º run) nesta rodada, e isso por si só empurrou o cálculo de confiança do `fase2_prova_TCC.py` para "confiante" sobre uma resposta que já estava errada e antes não era contada como confiante — **este efeito É causado pelo flip** (voter tocando uma entry cuja resposta de base já era errada e endossando-a com confiança), diferente da drift das 4 entries (comprovadamente ortogonal). **Ação (rollback completo, sem mandato para seguir com desvio no critério decisivo):** `TCC-Tutor` revertido (`git checkout -- .`) pro snapshot `28bb29f` (confirmado: 0 `temporal_block_id` no manifest pós-revert); `material_curation.json` (16 votos) **preservado untracked** para retry futuro sem custo; `subjects.json` revertido (`Teoria da Computabilidade e Complexidade.feature_flags = {}`, MF/SO/IA/ES2 confirmados intocados). **Nenhum commit em `TCC-Tutor`.** **Decisão: TCC flip ADIADO, mesmo tratamento do SO** — pendente de investigação/fix do bug de instabilidade do funil-base (ver item de dívida técnica abaixo) antes de reautorizar novo retry. **Report completo (todos os números, diffs, evidência):** `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-7-report.md`.
- [CODE] **Funil-base TCC recomputa `auto_tags bloco:`/confiança de forma instável a cada reprocess — candidato a bug de idempotência do retag (não investigado, fora do mandato de tocar `src/`).** Evidência: reprocess de `TCC-Tutor` (com OU sem `--flags`) muda `auto_tags bloco:` de 4 entries fixas (`3dm-caetano-gabriel-e-gustavo`, `cubic-3-edge-coloring`, `integer-programming-0001`, `programacao-inteira-01-20260617-154423-0000`) mesmo sem o anchor engine tocá-las (`temporal_block_id=None` nas 4). Adicionalmente, no Fix round 1, `aula-01-apresentacao-...` teve seu `temporal_block_id` populado via voter LLM (cache) numa rodada e isso sozinho fez `fase2_prova_TCC.py` marcar a entry como `confiante-e-errado` (era wrong-mas-não-confiante antes). Não sabemos se a causa é não-determinismo de `set()`/hash (hipótese já registrada no achado colateral do Task 3 MF) ou algo mais estrutural do recompute do funil-base/voter-confidence — candidato a investigação e fix antes de reautorizar o rollout TCC. Vai para o Plano B/cutover.
- [DERIVADO] **Audit pré-rollout IA/ES2 (2026-08-04)**: IA (74 rows, 0 hard, 7 soft ZERO_OVERLAP) + ES2 (35 rows, 0 hard, 22 soft ZERO_OVERLAP). Feature flags: IA `{"use_anchor_placement": true}` (legado ativo), ES2 `{}` (OK). `material_curation.json` não presente em ambos (não-crítico). **IA:** gold user-side pendente (trilha 4, 21 SARC batch), stash ~45 `.ipynb`/datasets, timeline 24-29/06 vs SARC vivo (bug conhecido, OK), legado `use_anchor_placement=true` reforça bloqueio pós-flip (flip futuro do motor DEVE desligar no mesmo ato — precedência já OK em `pedagogical_regeneration.py:444`, manter ambos ON é estado não-medido). **ES2:** sem gold fresco desde 21/06 (medição pré-flip obrigatória), ZERO_OVERLAP severo (22/35 rows, validar download SARC). ES2 pronto para rollout flag-ON; IA pronto com ações documentadas pós-flip. Sem flip nesta campanha em nenhum dos dois (audit report-only). Report completo: `.superpowers/sdd/2026-08-03-rollout-flagon-trilha1/task-8-report.md`.
- [DERIVADO/DECISION] **Rollout flag-ON SO EXECUTADO (2026-08-04, verificado/fechado 2026-08-05):
  gate estrutural a/c/d PASS, gate (b) 1 exceção registrada (classe funil-base já conhecida), fase2
  byte-idêntica em 3 capturas independentes, audit hard=0 estável — commit `Sistemas-Operacionais-Tutor`
  `11667b7`.** Pre-flight destravado pelo ruling `lista2=bloco-17` (`f14d50c`, 20:08:59): audit
  `--course SO` hard=0 (42 rows, 21 suspeitas). Snapshot pré-rollout: commit `d4929fe` (20:17:49).
  Backup gitignored completo (`course/.assessment_context.json`, `.content_taxonomy.json`,
  `.semantic_profile.generated.json`, `.tag_catalog.json`, `.timeline_index.json`) — não usado (zero
  rollback). Flip round-trip: `Sistemas Operacionais.feature_flags = {use_anchor_engine: true,
  use_llm_voter: true}`; MF confirmado ON, TCC/ES2 confirmados `{}`, IA legado `{use_anchor_placement:
  true}` intocado. Reprocess sem traceback: `bloco 42/42 → 42/42`. **Gate (a) pinos PASS:** 4/4
  preservados, zero `temporal_block_id` sujo em pino. **Gate (b) auto_tags bloco: 1 drift** —
  `exercicios-p2` `bloco-03→bloco-16`, **sem `temporal_block_id`** (motor não tocou a entry; mesma
  classe de instabilidade do funil-base já diagnosticada e registrada para TCC, ver item CROSS-CUTTING
  acima). `exercicios-p2` já era gold-errado ANTES desta task (`ground_truth_SO.csv`: true=bloco-17,
  computado congelado=bloco-03) — o reprocess trocou um valor errado por outro errado, não introduziu
  regressão de correção nova; e a linha não participa do conjunto `provider=data` medido pelo
  `fase2_prova_SO.py`, por isso a régua ficou intacta apesar do drift. **Gate (c) temporal_* PASS:**
  19 entries com `temporal_block_id`, 0 fora de escopo; provider `{data:19}`, band `{media:6,alta:13}`,
  method `{janela-1:19}`, fila humana `{flag=True:6, flag=False:13}`. **Gate (d) voter PASS:**
  `material_curation.json` (cache local pré-existente na raiz do SO-Tutor) `entries` **11→11 entre os
  commits `d4929fe`/`11667b7` (`git diff --stat` vazio) — 0 chamadas API novas**, cache cobriu 100%.
  **CRITÉRIO DECISIVO PASS:** `fase2_prova_SO.py` byte-idêntico em 3 capturas independentes (pós-reprocess
  20:25; re-checagem 23:18; reverify ao vivo 2026-08-05) — cobertura 19/42=45.2%, colisões 0, janela P3
  15 in/4 out (mesma lista), acurácia par-colapsada 77.8% de 18 pares, matriz
  `{('resto','err'):4,('resto','ok'):2,('alta','ok'):13}`, confiante-e-errado 0. `audit_gold_freshness
  --course SO` pós = **hard=0** nas 3 capturas (20:26/23:18/2026-08-05); suspeitas soft variou 21→24
  mas os 3 ids novos (`0206-laminas-memoria-virtual-livro-texto`,`14-04-troca-de-mensagens`,
  `1404-troca-de-mensagens`) já existiam no manifest pré com o MESMO `bloco:` tag (confirmado por diff
  direto, zero id novo, zero bloco mudou nesses 3) — causa não é o funil/motor, não investigada a fundo
  (fora do escopo do gate a-d, não afeta hard), registrada como concern não-bloqueante. `pytest
  tests/test_timeline_schema.py` **18 passed** em 3 rodadas (20:26 original + reverify 2026-08-05).
  **Divergência registrada:** o commit `11667b7` alega "gate estrutural PASS" sem qualificar; a
  reconstrução desta sessão (sem log salvo da rodada original do `gate_so.py`, diferente do padrão de
  log completo do TCC) mostra que (b) tecnicamente falha por 1 entry — tratado como PASS-com-exceção
  dado diagnóstico completo (órfã do motor, mesma classe TCC, sem impacto na régua decisiva), não como
  bloqueio; commit do repo-tutor não foi reescrito. **Report completo:** `<scratchpad>/roteiro-1b-so-report.md`
  (sessão 2026-08-05).
- [DERIVADO/DECISION] **Ruling user `lista2` (2026-08-04): gold bloco-17 CONFIRMADO + fix do auditor (commit `f14d50c`).** User confirmou semântica de uso: lista2 = preparação da P2 (pair_key `lista-exercicios-p2`), true=bloco-17 mantido. Fix autorizado no AUDITOR (não motor): `_looks_like_assessment(material, pair_key)` — ADMIN_TRUE agora reconhece material-de-prova também pelo pair_key (regex intocada, `\bp[12]\b` casa o sufixo). 3 testes novos (`tests/test_audit_admin_true.py`). Hard counts pós-fix: SO/TCC/IA/ES2/MF TODOS 0 (lista2 sai do hard, zero efeitos colaterais). Precedente citado: guard-clause `_gold_check` F4 (alinhar medição a gold aceito, sem afrouxar piso). **Pre-flight SO destravado.**
- [DERIVADO/DECISION] **CORREÇÃO DE ATRIBUIÇÃO do cw TCC + rollback T7 incompleto para gitignored (2026-08-04, pós-campanha).** Cadeia: (1) suite acusou FAIL novo em `test_timeline_schema.py[TCC-Tutor]` (needs_unit 3/16=19% > gate 10%) — causa: o rollback da Task 7 (`git checkout -- .`) NÃO restaurou `course/.timeline_index.json` (GITIGNORED, nunca tracked) → o índice REGENERADO pelos 2 reprocess do rollout ficou vivo no repo; índice pré-campanha IRRECUPERÁVEL (sem histórico git; `.bak` de 02/06 preservado em scratchpad, pré-campanha-de-junho, não serve). (2) Recovery: rebuild cirúrgico só-TCC via `rebuild_timeline.rebuild_course` (caminho próprio com curation Fase 5) → gates OK (19%→0%), suite verde **1823/4/0**. (3) **DESCOBERTA que REFUTA a atribuição do Fix round 1 (entrada acima):** com manifest flag-OFF (snapshot `28bb29f`) e índice reconstruído, `fase2_prova_TCC.py` dá **cw=1 no `aula-01`** (topic, computado bloco-02 vs gold bloco-01) — o cw NÃO era causado pelo voter/flip: é o ESTADO DO ÍNDICE. O cw=0 aceito da régua TCC repousava em índice STALE que o pipeline atual não reproduz por NENHUM caminho (reprocess e rebuild produzem índice em que o topic provider casa `aula-01` com confiança no bloco-02 — conteúdo "revisão de conjuntos/enumerabilidade" bate topics do bloco-02; falta sinal ordinal "aula-01"→bloco-01). **Consequências:** (a) número aceito fase2_TCC (cw=0) era artefato de índice stale — régua TCC INSTÁVEL até o Plano B resolver (caso-chave 2a com repro vivo: rodar fase2 com índice atual reproduz); (b) NENHUM re-tuning feito — FAIL honesto documentado; flip TCC segue ADIADO; (c) lição operacional: rollback de reprocess DEVE cobrir artefatos gitignored (índice/sidecars) — snapshot só de tracked é rede FURADA; (d) mesma classe de risco vale pro flip SO (índice SO também é gitignored e stale de 28/jun — o gate pós-flip fase2_SO idêntica decide honestamente). Estado TCC: manifest `28bb29f` flag-OFF, índice rebuilt gates-OK, cache 16 votos untracked, fase2_TCC FAIL cw=1 = realidade atual do pipeline.
- [USER/DECISION] **Bibliografia = caso à parte (decisão user 2026-07-22, brainstorm F5):** tutor
  deve passar a CONSUMIR bibliografias (hoje só resumo leve + mapa 📖 Apoio) sem estourar o limite
  de projeto Claude/GPT — brainstorm/spec próprios, fora do provider janela-de-prazo. Até lá,
  bibliografia/references/cronograma seguem fora total do motor. Contexto: gold TIER-2 MF tem
  eth2→bloco-12 (residual conhecido), archive/aws→bloco-01. Spec da janela-de-prazo §7:
  `docs/superpowers/specs/2026-07-22-janela-de-prazo-tier2-design.md`.
- ~~[DECISION] D4 × TIER 3 janela-1~~ **FECHADO (F4 item 1, commit `1f80f2a`)** — Opção A (D-A do
  plano F4) implementada: `len(window) > 1` gateia o hook do voter em `anchor_engine.py:57`;
  |janela|==1 nunca entra no escopo do voto, FLAG honesto sobrevive pra fila humana.
- ~~[CODE] Migrar ground_truth_*.csv de bloco-NN → block_uuid (FASE 4)~~ **FECHADO (F4 item 6,
  commit `4a73b5b`, decisão user 08/07)** — 5 CSVs + `true_of` uuid-first nos probes; auditor de
  frescor (`audit_gold_freshness.py`) segue como pré-gate obrigatório de qualquer medição.
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

## Concluído (2026-08-05 — Plano B Task 1)
- [DERIVADO] **T12 stopwords PT: causa-raiz do cw TCC fechada (cw 1→0, acc intacta).** 11 palavras-função PT
  (`nao`/`sim`/`com`/`sem`/`por`/`dos`/`das`/`nos`/`nas`/`uma`/`que`) adicionadas a `_GENERIC_STEMS`
  (`disambiguator.py:22-26`, espelha `marco0._GEN`) — causa: `nao` (df_global=1) satisfazia
  `bool(discriminante)` (`disambiguator.py:184`) e produzia band "alta" indevida em `aula-01-apresentacao-
  da-disciplina...` (TCC), fechando o `fase2_TCC FAIL cw=1` deixado em aberto pela entrada CROSS-CUTTING
  "CORREÇÃO DE ATRIBUIÇÃO do cw TCC" (2026-08-04) — motor real volta a `cw=0`. TDD: 3 testes novos
  `tests/test_motor_stopwords_pt.py` (RED confirmado pré-fix, GREEN pós-fix). Régua completa pós-fix
  (7 probes + suite): fase0 48/58 conten0 cw1 · fase1 recall 9/10 · fase2-SO 45.2%/colisões0/cw0 ·
  **fase2-TCC pinos 5/5 + cobertura 83.3% + acc 84.2% + cw0 (PASS — número EXATO da medição empírica)** ·
  fase3 lift +3/0 chamadas API · fase4 det 48/58 cw1, voter 51/58 cw0/calls0 · fase5 target 4/8 cw0 ·
  **pytest 1826 passed / 4 skipped / 0 failed** (1823 prévios + 3 novos). Lista CONSERVADORA por medição:
  versão larga (+ demonstrativos/comparativos) custou 2 casos (84.2%→78.9%), NÃO adotada (ver comentário
  no código). `last_seen` de `Metodos-Formais-Tutor/course/.block_identity.json` (bumped pelos probes)
  restaurado; SO/TCC sem alteração. Report completo:
  `.superpowers/sdd/2026-08-05-planob-motor/task-1-report.md`.

## Concluído (2026-08-05 — Plano B Task 4)
- [DERIVADO] **Fix 2b: funil-base lê `_p_ambig` + piso de confiança (MUDA ATRIBUIÇÕES, medido).**
  `content_taxonomy.py:1224` gateava atribuição de bloco só em `if _period:`, ignorando a flag
  `_p_ambig` (atribuída em `:1208`, nunca lida) e sem piso de confiança — um palpite `conf=0.0/
  ambig=True` de `select_probable_period_for_entry` virava atribuição dura (`scorer_only`) em vez
  de cair no `_best_instructional_block_fallback` honesto. Fix: `if _period and not _p_ambig and
  p_conf > 0:`. TDD: `tests/test_funil_gate_ambiguidade.py` (novo, RED 2/3 pré-fix confirmado via
  `git stash`, GREEN 3/3 pós-fix) + 1 teste pré-existente corrigido
  (`test_resolve_unit_block_band.py::test_wiring_medium_confidence_maps_to_band_media` passava
  `ambig=True` indevidamente — corrigido `False`, seu próprio docstring só prova confidence→band).
  **PRÉ (id → bloco atual → gold, medição in-memory read-only nos 3 repos reais):**

  | repo | id | atual | conf | gold |
  |---|---|---|---|---|
  | TCC | 3dm-caetano-gabriel-e-gustavo | bloco-26 | 0.0000 | bloco-24 |
  | TCC | cubic-3-edge-coloring | bloco-26 | 0.0000 | bloco-24 |
  | TCC | integer-programming-0001 | bloco-16 | 0.0000 | bloco-24 |
  | TCC | programacao-inteira-01-... | bloco-16 | 0.0000 | bloco-24 |
  | MF | logicadehoare | bloco-11 | 0.0037 | bloco-10 |
  | MF | classes-parte1 / classes-parte2 | bloco-13 | 0.0389 | bloco-15 |
  | SO | exercicios-p2 | bloco-16 | 0.0539 | bloco-17 |

  **PÓS (mesma tabela, delta):** TCC 3dm/cubic **movem** bloco-26→**bloco-22** (conf honesta
  0.22/0.25, gold ainda bloco-24 — erro persiste, agora com confiança honesta, não regressão);
  integer/programacao **permanecem** bloco-16 mas com conf honesta 0.0451 (era 0.0 cego) — empate
  real do scorer bruto (bloco-16==bloco-26 @20.5456) decidido por ordem estável de lista dentro de
  `_best_instructional_block_fallback` (fora do range 1225-1234 escopado para tie-break); ramo
  1225-1234 **inalcançável pelas 6 entries TCC+MF; alcançável pelo SO, mas sem `period_label`
  duplicado para desempatar** (evidência direta: `candidate_rows` de `exercicios-p2` tem 17 blocos,
  só 1 com o `period_label` devolvido — instrumentado dentro do próprio `resolve_unit_block_tags`,
  não emprestado da sonda `fase2_prova_SO.py`, que mede outro código, `provider_date` do motor);
  tie-break dispensado. MF (3) e SO (1) **sem nenhuma mudança** — achado que CORRIGE a
  investigação: MF nunca passa por `select_probable_period_for_entry_fn` (resolve via
  `_card_scoped_block`/`card+scorer`, fora do escopo do bug 2b desde sempre) e SO já tinha
  `conf=0.0539>0`, que já passava pelo piso literal `p_conf>0` ANTES do fix (o texto §2b "só o piso
  pega o SO" não se sustenta matematicamente para este valor). **Delta corpus-wide (fix round 1,
  os 136 entries dos 3 repos, não só as 8 conhecidas):** medido via `git worktree` do repo do
  PROJETO em `2c3fe45~1` (pré-fix) vs `2c3fe45` (pós-fix), harness `persist=False` idêntico —
  **4/136 mudaram, exatamente as 4 TCC já auditadas linha-a-linha; os 132 restantes (23 TCC + 67 MF
  + 42 SO) são byte-idênticos** (`computed_block_id`/`method`/`confidence`). Régua completa (7
  probes) **byte-idêntica** aos baselines pós-Task-3 (fase0 48/58 conten0 cw1 · fase1 9/10 ·
  fase2-SO 45.2%/0/cw0 · fase2-TCC 5/5/83.3%/cw0/84.2% · fase3 39 rows/+3 lift/0 API · fase4
  det48/58cw1 voter51/58cw0calls0 · fase5 4/8cw0) — mas nenhum dos 7 probes importa
  `content_taxonomy` (confirmado por grep): a régua prova só isolamento do caminho
  `engine.py`/`AnchorEngine` (não tocado), NÃO prova acurácia do funil. Evidência real de acurácia
  do funil = suíte de gate gold que EXECUTA `resolve_unit_block_tags` (`test_eval_assignments.py`
  `test_block_accuracy_not_below_baseline` + `test_eval_golden_real.py` + `test_block_method_caps.py`,
  17/17 verdes, já inclusos nos 1838) + o delta corpus-wide acima. **pytest 1838 passed / 4 skipped
  / 0 failed** (1835 prévios + 3 novos). Repos-tutor: **zero escrita líquida** — nenhum `last_seen`
  para restaurar (medição usou wrapper `persist=False`, ver achado abaixo).
  **Achado extra (registrar como pendência nova, não corrigido — fora do escopo desta task):**
  `_build_file_map_timeline_context_from_course` tem `persist=True` por padrão e, além do bump de
  `last_seen` já catalogado, TAMBÉM grava `manifest.json` (migração `manual_timeline_block_id`
  bloco-NN→uuid) quando encontra refs legadas — `scripts/retag_manifest.retag()` (usado por esta
  investigação e pela Task 4) **não é read-only de verdade**; reproduzido e revertido no TCC-Tutor
  antes de qualquer medição válida. Report completo:
  `.superpowers/sdd/2026-08-05-planob-motor/task-4-report.md`.

## Concluído (2026-08-05 — Plano B Task 5)
- [DERIVADO] **T17: filtro D-H do due-window troca `topics` (opcional) por `kind` (required).**
  `due_window.py:96` excluía bloco de conteúdo com `topics=[]` — matava pré-requisito artificial
  de rollout (curso novo sem topics populado). Fix: `_NON_CONTENT_KINDS = frozenset({"assessment",
  "review"})`, derivado dos 4 `.timeline_index.json` reais disponíveis (TCC/MF/SO/ES2 — IA-Tutor
  sem índice, motor nunca rodou lá): únicos 2 kinds com blocos `topics=[]` hoje (assessment 10/5,
  review 2/1 vazio/preenchido); todo outro kind observado (class, deliverable, holiday,
  academic_event, office_hours, overview, results, reserved, suspended, workshop) sempre tem
  `topics` populado. Coerente com uso já existente de `kind` em `content_taxonomy.py:966,973`.
  TDD: `tests/test_motor_due_window.py` (2 testes novos, RED confirmado pré-fix — bloco
  `kind=class topics=[]` não ancorava; bloco `kind=assessment topics≠[]` ancorava direto — GREEN
  pós-fix) + `_ctx_mf_real` atualizado com `kind` real por bloco (11/16=class, 17=review,
  18=assessment). Régua completa (7 probes) **byte-idêntica** ao baseline pós-Task-4 (fase0
  48/58 conten0 cw1 · fase1 recall 9/10 · fase2-SO 45.2%/colisões0/cw0 · fase2-TCC pinos
  5/5+83.3%+cw0+84.2% · fase3 39 rows/lift+3/0 API · fase4 det48/58cw1 voter51/58cw0calls0 ·
  **fase5 4/8 cw0 idêntico** — o gate central da task, D-H não mudou resultado no MF). **pytest
  1840 passed / 4 skipped / 0 failed** (1838 prévios + 2 novos). `last_seen` de
  `Metodos-Formais-Tutor/course/.block_identity.json` (bumped pelos probes fase0/1/4/5, mesmo
  padrão já catalogado) restaurado; TCC (só `?? material_curation.json` pré-existente, não meu) e
  SO sem alteração. Commit `4190abb`.

  **Fix round 1 (revisão do coordenador) — medição PRÉ/PÓS em TCC e SO, corpus real de produção.**
  Achado do report original citava blocos `assessment`/`review` com `topics≠[]` em TCC (bloco-05
  review, bloco-28 assessment) e SO (bloco-18 assessment) como "efeito pretendido não medido fora
  do MF" — a revisão pediu medição direta em vez de diferimento, já que SO está flag-ON em
  produção. Medido `resolve_due_window` para TODO entry `tier2_due_scope` de TCC-Tutor e
  Sistemas-Operacionais-Tutor, PRÉ (`git worktree` do repo do PROJETO em `4190abb~1`, código
  anterior ao fix) vs PÓS (HEAD `4190abb`), via `build_motor_context` (loader já read-only,
  docstring própria confirma "nunca escreve" — não é o `persist=True` da Task 4 §0, função
  diferente). **Resultado: zero deltas nos dois cursos, e por um motivo mais forte que "o kind não
  importou" — o filtro por kind nunca chega a ser exercido:**
  - **SO: 0 entries passam `tier2_due_scope`** (categorias reais: material-de-aula/listas/
    gabaritos/cronograma/codigo-professor/outros/bibliografia — nenhuma `trabalhos`/`provas`, e
    `codigo-professor` não tem `source_section` prefixado `TDE`). `resolve_due_window` nunca é
    chamada para nenhum entry real do SO hoje — o achado do bloco-18 é um FATO de dados
    (kind=assessment, topics≠[]) inerte em produção, confirmado por medição direta, não por
    inferência.
  - **TCC: 5 entries passam `tier2_due_scope`**, mas `resolve_due_window` retorna `null`
    idêntico PRÉ e PÓS para as 5 (`3dm-caetano-gabriel-e-gustavo`, `cubic-3-edge-coloring`,
    `programacao-inteira-01-...`, `t1-enunciado`, `trabalho-t2-enunciado`) — o passo `_match_due`
    (upstream do loop de blocos onde o fix vive) já retorna `None` nas duas versões: confirmado
    que `course/.card_block_map.json` de TCC (5 cards) e SO (1 card) não têm nenhum `assign_dues`/
    `file_dues` estruturado — a due-window TIER 2 só está de fato populada com dados reais no MF
    hoje. O achado do bloco-05/28 é igualmente um fato de dados inerte, mesma razão.
  - **Interpretação (linha 3 do fix): nenhum delta observado, logo nenhum julgamento
    correção-vs-regressão foi necessário** — não houve "due parando de ancorar em prova" para
    avaliar, porque devido a esta cascata (`tier2_due_scope` vazio em SO; `_match_due` vazio em
    TCC) o provider due-window está estruturalmente adormecido nos dois cursos, independente do
    fix de kind. Não há BLOCKED a levantar.
  - Repos-tutor: zero escrita (`build_motor_context` confirmado read-only por medição — `git
    status` limpo em TCC/SO antes e depois; nenhum `last_seen` a restaurar). Worktree temporário
    removido (`git worktree remove`) ao final.
  - Nenhuma mudança de código neste round (`src/` intocado); só a medição registrada aqui e em
    `.superpowers/sdd/2026-08-05-planob-motor/task-5-report.md` §8 (comandos + saída completos).
