# Plano-mestre — Reforma do sistema de atribuição

date: 2026-06-11 (atualizado 2026-06-12 pós-M365)
base: `docs/reports/2026-06-11-diagnostico-atribuicao.md` (diagnóstico com dados reais)
revisão: `docs/reports/2026-06-11-reanalise-atribuicao.md` (re-análise independente +
causa raiz M365 provada)
objetivo do projeto: **auto é o caminho principal**; manual é correção de exceção.
Cada fase = ciclo próprio (brainstorm → spec → plano → subagents → eval → relatório).

## Atualização 2026-06-12 — o que mudou desde o diagnóstico

- **Causa raiz a montante encontrada e CORRIGIDA (M365).** A re-análise provou que a
  classe dominante de erro nascia ANTES do matcher: o download M365 colocava o
  arquivo no card errado por chute léxico (pasta-tópico do OneDrive → seção Moodle
  por afinidade de tokens), contaminando `source_section`. A feature M365
  (spec/plano `2026-06-11-m365-card-mapping`, 7 commits, suíte verde) trocou isso
  por índice basename→seção REAL da API Moodle; fallback honesto, nunca léxico.
  **Para imports NOVOS, a origem do sinal está limpa.**
- **Implicação para este plano:** o P1 muda de papel. Não é mais "resgatar a seção
  que se perde" — a seção agora vem certa da API no import. P1 vira a **2ª linha de
  defesa** (degradação visível quando a seção falta mesmo assim) + reparo dos DADOS
  já contaminados (manifests/stash existentes ainda têm `source_section` errado e
  `source_path` quebrados — reparo é trabalho à parte, fora do funil).
- **Correções de rota da re-análise:** B2 (card bonus 2×) **refutado** — sai do P3.
  IDF de raridade **já existe** no scorer de UNIDADE (`token_weights = 1/freq`,
  file_map.py); P4 reusa esse mecanismo no scorer de BLOCO em vez de criar do zero.
  CamelCase **confirmado** (fix na tokenização do título, não no `normalize` global).
- **Sequência inalterada:** P0 (medir) continua sendo o primeiro — sem harness,
  nenhuma fase prova melhora.

## Norte

1. **Precisão**: atribuição automática certa por padrão (meta: ≥95% no golden set com seção; ≥80% sem).
2. **Honestidade**: confiança baixa ⇔ chance real de erro; "confiante e errado" vira raro.
3. **Degradação visível**: sinal faltando (seção) ⇒ confiança cai e a UI avisa — nunca falha silenciosa.

## Arquitetura-alvo: funil único com precedência explícita

```
Estágio 0  manual (bloco/unidade/subunidade)        conf 1.0, vence tudo
Estágio 1  PRIOR   seção→gabarito (card_block_map)  restringe 21 blocos → 1-3
Estágio 2  RANK    scorer léxico                    ranqueia DENTRO do conjunto restrito
Estágio 3  VOTO    Gemini (código)                  consenso ⇒ sobe confiança
Saída      computed_block_id + method (qual estágio decidiu) + confiança calibrada
```

Não são cérebros rivais: o prior restringe, o scorer desempata, o LLM vota. O defeito
atual não é a arquitetura — é (a) o estágio 1 desligar em silêncio quando `source_section`
falta, e (b) a confiança não refletir QUEM decidiu. `computed_block_method` (já existe
pra código) generaliza para todas as entries: `manual | card | card+scorer | scorer_only |
consensus | review_rule`.

## Estado atual (medido, repo Metodos-Formais)

| Fato | Número |
|---|---|
| Erro geral | 8/49 (16.3%) |
| Erro COM seção (gabarito ativo) | 0/22 |
| Erro SEM seção (scorer solto) | 8/27 (29.6%) |
| Scorer puro sem gabarito | 59.2% acerto |
| Erros com conf 1.0 "alta" | 7/8 |
| Entries com conf=1.0 | 46/54 (clamp estourado — conf não calibra) |

## Fases

### P0 — Medição primeiro (pré-requisito de tudo)

**Por quê primeiro:** sem harness funcional, nenhuma fase posterior prova melhora.
O `scripts/eval_assignments.py` colapsa com o índice persistido (bug B3: espera `rows`,
índice tem `sessions`/`source_rows` → 49/49 "erradas" espúrias).

- Corrigir B3 (adaptador `sessions`→`rows` ou aceitar ambos em `select_probable_period_for_entry`).
- **Golden set versionado**: as 49 entries do Metodos-Formais com bloco esperado
  (da avaliação do diagnóstico) viram fixture de regressão (`tests/golden/` ou
  `scripts/golden/metodos-formais.json`). Rodável com 1 comando.
- Métrica-padrão impressa: acurácia geral / com-seção / sem-seção / % confiante-e-errado.
- Critério de aceite: harness reproduz os 8 erros conhecidos do manifest real.

Esforço: baixo. Risco: baixo. Dependências: nenhuma.

### P1 — Seção automática (2ª linha de defesa + reparo dos dados)

**REVISADO pós-M365.** A premissa original ("a seção existe no stash e se perde por
basename") estava parcialmente errada: a re-análise mostrou que a seção se perdia
porque o download M365 CHUTAVA o card por léxico. Isso foi corrigido na origem
(feature M365). P1 deixa de ser o conserto principal e passa a cobrir os resíduos:

- **2ª linha de defesa**: entries que mesmo assim cheguem sem `source_section`
  (import direto de arquivo solto, raw/pdfs por categoria, Moodle offline no import)
  tentam resgate por basename contra o índice da API quando disponível.
- **card_block_map AUTOMÁTICO via labels de semana (descoberta 12/06)**: nesta
  cadeira, TODO card de conteúdo tem labels "Semana DD/MM a DD/MM: (DD/MM): aula"
  — parseável da API (`mod.description` dos labels). Card→datas→blocos vira
  derivação automática com cobertura total, matando o card_block_map manual
  (hoje 5/9 seções e com erro comprovado — revisão P1 apontava bloco-06, real
  bloco-07). Formato varia entre cadeiras → parser tolerante + fallback manual.
  Bônus do mesmo sinal: detecta segmentação ruim da timeline (ex.: "Introdução
  ao Dafny" atravessa blocos 12-13).
- **Reparo dos dados já contaminados** (trabalho à parte, pode virar sub-fase): o
  manifest real do Metodos-Formais tem `source_section` errado (chute léxico antigo)
  e `source_path` quebrados (pasta `dafny\` extinta + arquivos movidos). Re-rodar
  import M365 corrigido + retag reconcilia; precisa de passo de reconciliação de
  caminhos.
- Todo caminho de import preenche seção quando derivável (stash_import já faz;
  raw/pdfs e import direto ganham o resgate).
- **Degradação visível**: seção vazia após resgate ⇒ method `scorer_only`, teto de
  confiança (ver P3) e aviso no editor ("sem seção — atribuição só léxica, revise").
- Ambiguidade de basename (mesmo nome em 2 seções) registrada, não chutada.
- Critério de aceite (golden set): erro sem-seção 29.6% → <10%; os 4 PDFs do caso
  real (LogicaDeHoare etc.) ganham seção e caem nos blocos do gabarito.

Esforço: médio. Risco: baixo (aditivo). Dependências: P0 (pra medir).

### P2 — Calibrar confiança + method em todas as entries

(antigo P3 — promovido: barato e destrava a triagem; o scorer melhor vem depois)

- `margin_confidence` recebe scores grandes (~4-8) e clampa em 1.0 → 46/54 entries
  com conf 1.0. Trocar por margem **relativa** (ex.: `(best−runner)/best` + termo de
  força absoluta) ou normalizar scores antes da margem. Manter bands (alta/média/baixa)
  com cutoffs recalibrados no golden set.
- `computed_block_method` generalizado: gravar qual estágio decidiu para TODA entry
  (hoje só código tem). Editor mostra (campo "Match do bloco" já existe — passa a
  valer pra tudo).
- Teto de confiança por método: `scorer_only` nunca passa de ~0.7 (não há como ter
  certeza só com léxico); `card` single-block 0.85; `manual`/`review_rule` ~1.0;
  `consensus` sobe.
- Critério de aceite: % confiante-e-errado (conf≥0.5 e errado) no golden set cai de
  87.5% dos erros para <20%; distribuição de conf deixa de ser 85% em 1.0.

Esforço: baixo-médio. Risco: médio (mexe em número que outros leem — verificar
consumidores de computed_block_confidence/band). Dependências: P0.

### P3 — Higiene (bugs B1, B2, B4, B5)

- B1: `_NO_TIMELINE_CATEGORIES` ganha equivalentes EN (`references`) ou normalização
  de categoria antes do filtro.
- ~~B2: card bonus somado 2×~~ — **REFUTADO** na re-análise: file_map.py:795 e :874
  são caminhos mutuamente exclusivos, sem dupla soma. Removido do escopo.
- B4: re-rodar retag no repo real pós-F1 e confirmar que `formalizacaoalgoritmos-recursao`
  (unit u02 + bloco u01) reconcilia ou flagra conflito.
- B5: colisão de ids no manifest (`t1-2026-1`, `introducao` 2×) — id ganha sufixo de
  categoria ou dedup no import; auditar efeitos no code_curation.
- Critério de aceite: suíte verde + golden set não regride.

Esforço: baixo. Risco: baixo. Dependências: P0 (B4 usa o harness).

### P4 — Scorer melhor (sobe o piso dos casos sem prior)

**Sinal novo aprovado (12/06, design corrigido por demo real): janela de
trabalho via assign.** A API expõe `dates` estruturado nos módulos `assign`
(`duedate`, e `allowsubmissionsfromdate` quando configurado — confirmado no T1
real de MF: duedate 06/05/2026 23:59). Para entries de trabalho (convenção B =
conteúdo): o duedate é PRIOR/RESTRIÇÃO — só blocos de aula que começam antes do
vencimento são candidatos — e o SCORER ranqueia dentro pelo conteúdo (mesma
forma do card map: prior restringe, scorer decide, confiança honesta). NOTA de
projeto: a heurística "último bloco de aula antes do duedate" foi testada e
REPROVADA no caso real (escolheria bloco-10/Hoare; o certo é bloco-06 pelo
conteúdo Isabelle do T1) — o duedate não decide sozinho. Com o sinal de
ferramenta do P4, T1 → bloco-06; exemplo abre 19/06 / vence 10/07 → restrição
até 08/07 + conteúdo model-checking → bloco-16. `allowsubmissionsfromdate`
(quando existir) pode apertar a janela como boost.

Fontes do deadline em CASCATA (varia por professor — confirmado nos dados
reais, 12/06): (1) `assign.dates[duedate]` estruturado (MF TDE: 06/05);
(2) regex de data no NOME do módulo de entrega — forums usados como sala
(MF: forum "Sala de Entrega (10/06)"); (3) data no label do card (MF:
"Trabalho 1 (06/05/2026):"; ES2: "Trabalho Final (03/07/2026):" — o parser
de labels do P1 já captura como data avulsa). Sem fonte → sem restrição,
scorer puro com confiança honesta, como sempre.

Maior esforço, deixado por último de propósito: depois de P1, o scorer decide MENOS
casos (só os sem seção resgatável); depois de P2, quando decide, a confiança é honesta.

- **Raridade de token (IDF simples)**: peso do token ∝ 1/nº de blocos que o contêm.
  "hoare" (1 bloco) passa a valer ≫ "logica" (muitos blocos). Resolve o mecanismo
  central dos erros LogicaDeHoare. NOTA: o scorer de UNIDADE já tem isso
  (`token_weights = 1/freq`, file_map.py:136-140) — reusar o mesmo mecanismo no
  scorer temporal/bloco (`entry_signals.py`, hoje pesos fixos), não criar do zero.
- **Sinal de ferramenta**: extensão/conteúdo (.thy=Isabelle, .dfy/Dafny) vs ferramenta
  do bloco (tokens "isabelle"/"dafny" nos topics) — boost/penalidade forte. Resolve
  intro.thy→bloco Dafny.
- **Tokenizar CamelCase** no título ("LogicaDeHoare" → logica+de+hoare) antes de
  normalizar. Resolve o match exato de frase perdido.
- Avaliar: penalizar topic_text concatenado verboso (superfície inflada) via
  normalização por tamanho do bloco.
- Critério de aceite: scorer puro (sem gabarito) no golden set 59% → ≥80%; zero
  regressão nos casos com gabarito.

Esforço: médio-alto. Risco: médio (mexe no coração do matcher; golden set é a rede).
Dependências: P0 (medir), idealmente após P1/P2.

## Sequência e porquê

```
P0 medir → P1 seção (mata 100% dos erros observados) → P2 confiança honesta
        → P3 higiene → P4 scorer (último: decide menos casos e com rede de medição)
```

Após CADA fase: rodar golden set, registrar números no relatório da fase, atualizar
este plano-mestre (tabela abaixo).

## Placar (atualizar por fase)

| Fase | Status | Acurácia geral | Sem seção | Confiante-e-errado |
|---|---|---|---|---|
| baseline (diagnóstico, rótulos LLM) | — | 83.7% | 70.4% | 7/8 erros |
| P0 — golden v1 (ground truth ancorado) | **fechado 12/06** | **56.5% (26/46)** | n/a (todos com seção física) | **7** |
| P0 — golden v1.1 (rótulos confirmados + card map revisão-P1 corrigido) | — | 58.7% (27/46) | n/a | 6 |
| P1 — card map via labels (+ fix B3 2º call site) | **fechado 12/06** | **78.3% (36/46)** | n/a | 9 (alvo do P2) |
| P2 — margem relativa + tetos + method universal | **fechado 12/06** | 78.3% (36/46, mantida) | n/a | **0** (meta ≤2 batida; banda alta: 28 ok / 0 erro) |
| P3 — higiene B1/B5/B4 | **fechado 12/06** | 78.3% (inalterada — higiene) | n/a | 0 |
| P4 | **FECHADO 12/06** (Fase 0 limpeza + S1-S5 + S4b) | **85.4% (41/48)** | n/a | **0** (banda alta: 28 ok / 0 erro) |

**Fechamento P4 (12/06, golden v2 = 48 casos):** progressão por sinal —
36/48 (baseline pós-P3) → S1 CamelCase → S2 IDF **40/48** → S3 (medido
redundante/danoso, NÃO implementado) → S4 ferramenta → S5 janela de assign →
**S4b ferramenta por extensão (.thy/.dfy) → 41/48 (85.4%)**, confiante-e-errado
**0**, suíte 1318 verde. Commit final `cbfb6bd`.

**Teto principiado do scorer (por que 41 e não os ≥43 da meta):** os 7 erros
restantes são TODOS band baixa/media (review-flag honesto, 0 na banda alta).
Dois deles (`t1`, `provas` → bloco-06) só seriam alcançáveis revivendo a
heurística "último bloco antes do prazo" — **reprovada na própria spec**: `t1`
é `.pdf` (sem extensão de ferramenta) e seu ground-truth é o julgamento "opção B"
do usuário (trabalho pertence ao fim do arco que exercita); `provas`.thy recebe
o boost isabelle em bloco-06 mas o surface "inducao arvores" de bloco-05 domina
por 4.4 — fechar isso exigiria overpeso de ferramenta que regrediria outros
casos (overfit a 1 cadeira, risco documentado na spec). Os outros 5
(`logicadehoare2`, `exerciciosdafny1`, `exercicios-conjuntos`, `terminacao`,
boundary de segmentação) são fronteiras reais de timeline entre blocos
adjacentes — confiança baixa é a resposta correta, não um defeito. **Meta
primária (confiante-e-errado = 0) batida; a acurácia bruta cede à honestidade
da confiança, que era o objetivo do programa todo.**

**Retag do repo real (Metodos-Formais-Tutor, 12/06):** 56 entries, 6
computed_block_id corrigidos (5 dafny exercises 15→13/11, `introducao` 11→12).
Distribuição de bands: 33 alta / 8 media / 12 baixa / 3 sem. As 12 baixas (spec
esperava 2-4) são honestas: exercícios Dafny entre blocos Dafny adjacentes
(11/13/15) e Lógica de Hoare parte 1/2 têm margem relativa genuinamente baixa →
review-flag correto. Backup em `manifest.json.retag.bak`.

**Decisão P4 (12/06, pós-ciclo P1-P3):** dos 10 erros restantes do golden, ~8 têm
mecanismo P4 identificado: 5 exercícios Dafny caem no bloco-15 em vez do 13
(topic_text do 15 verboso vence — normalização por tamanho/IDF); `logicadehoare2`
(CamelCase: título vira 1 token); `provas`.thy (sinal de ferramenta Isabelle —
os outros 4 .thy o prior+scorer já acertam); 2× especificação (desempate fino
02/03). Escopo do P4 confirmado: IDF/normalização no scorer de bloco (reusar
token_weights da unidade), tokenizar CamelCase no título, sinal de ferramenta.
Potencial: 78.3% → ~93%. B4 verificado: F1 flagrou `unit_block_conflict` na
entry real (`formalizacaoalgoritmos-recursao`, unit u02 × bloco u01) — contrato
cumprido. Force-reprocess corrigido para resolver old_id por source_path
(review final; commit 09625b2).

**Dívidas registradas do ciclo (review final 12/06), pro P4 ou limpeza:**
- Portões `>= 0.5` do FILE_MAP (navigation.py:662,678) não recalibrados para a
  fórmula relativa — confiança menor ⇒ menos linhas ganham período no artefato
  FILE_MAP.md (mais conservador; fora do alcance do golden). Medir no artefato
  e recalibrar ou aceitar explicitamente.
- Spec P2.2 listava `consensus → min(0.95, conf)`; decisão final: métodos de
  código (consensus/llm_only) ficam FORA do METHOD_CAPS (confiança deles vive em
  computed_block_match_confidence) — documentado em thresholds.py, spec ficou
  desatualizada nesse ponto.
- `reconcile_unit_with_block` recebe block_confidence CRUA (pré-cap) — decidir
  se passa o valor capado (consistência exibição×decisão).
- Formato D dormindo: import não passa `week_anchor` (cadeiras tipo Teoria
  degradam pra E). Derivar âncora do cronograma da matéria.
- `METHOD_CAPS.get(method, 1.0)`: default permissivo — method novo futuro
  passaria sem teto.
- FILE_MAP corrigido pra fonte única (commit 94c17b3, 12/06 — a coluna Período
  lê computed_block_id; o roteamento próprio do artefato morreu). ~~Follow-up
  (a) coluna UNIDADE~~ — RESOLVIDO na Fase 0 do P4 (8141a12). (b) leitura crua
  de computed_block_id sem o fallback auto_tags["bloco:"] de manifests legados
  (unificar com resolve_effective_block) — segue dívida.

**Fase 0 do P4 fechada (12/06, commits 94bce21..8141a12):** 4 mortos deletados
(flag processing_profiles_seeded_v2 PULADA — é guard de idempotência ativo, não
morta; MATERIAL_COVERAGE_MIN tinha consumidor e foi inline), 6 unificações,
normalize_match_text unificado com `keep="+-./"` parametrizado (51/211 textos
reais divergiam — datas/outline justificam), 3 segundos cérebros mortos (coluna
UNIDADE do FILE_MAP, scorer reimplementado da UI com pesos divergentes, parser
regex de FILE_MAP renderizado; −469/+123 linhas). Golden IDÊNTICO em toda a
fase: 36/48, confiante-e-errado 0, mesmos 12 erros. Suíte 1291.
Dívidas de fluxo registradas (não atacadas): cronograma_health top-N roda o
scorer com markdown vazio; retag sem `_content_taxonomy` (inputs degradados vs
pipeline completo); índices (assignment/whiteboard/code_health) imprimem
`e.tags` legado em vez de computed_unit_slug.
- ~~Golden: 2 pendentes (`t1-2026-1` ×2)~~ — RESOLVIDO 12/06: usuário decidiu
  opção conteúdo (bloco-06, Isabelle/fim do arco; deadline rejeitado). Golden
  completo: 48 casos contados, 0 pendentes. Placar final do ciclo com
  denominador novo: **36/48 (75.0%)**, confiante-e-errado 0 — os 2 casos do T1
  erram hoje (scorer→bloco-05, band baixa) e são alvos do P4 (ferramenta).

## Investigação subunidade conf-0.0 (12/06, pós-P4)

Disparada pelo censo de bands de SUBUNIDADE no repo real (56 entries):
**23 alta / 11 media / 20 baixa / 2 sem** — e dentro das 20 baixas, um cluster
de **12 entries com `subunit_match_confidence = 0.0` exato, TODAS
`codigo-professor`** (`t1-2026-1`(code), `introducao`, `intro`, `classes-parte1`,
`colecoes-arrays`, `colecoes-conjuntos`, `colecoes-sequences`,
`exercicios-conjuntos`, `hoare`, `invariantes`, `terminacao`, `tiposindutivos`).

**Nota de escala:** a confiança de subunidade vem de OUTRA fórmula que a de
bloco — `auto_map_entry_subtopic` (file_map.py:161-213) usa rel_margin puro
`(winner−runner)/winner`, sem escala de força; empate exato ⇒ conf 0.0.

**Causas-raiz (3, verificadas por reprodução headless):**

1. **Empate exato ⇒ slug ARBITRÁRIO surfaçado.** Com rel_margin = 0 a conf vai
   a 0.0, mas `auto_map_entry_subtopic` retorna `scored[0]` mesmo assim — e o
   sort estável faz o vencedor ser o tópico de MENOR índice na taxonomia entre
   os empatados. Resultado: `linguagens-de-especificacao-e-logicas` (índice 1)
   "vence" repetidamente. Verificado: `hoare` empata 3-way em 0.603;
   `intro` empata 2-way em 0.936. O slug exibido no editor é ruído com cara de
   atribuição.
2. **Zips de código têm sinal de markdown ZERO.** 10 das 12 entries são
   `file_type=zip` com `md_path` ausente E `image_description` ausente —
   `_entry_markdown_text_for_file_map` (navigation.py:67-78) retorna `""`.
   Sobram título + auto_tags (pesos 3.8 / 0.22) ⇒ scores fracos que empatam no
   nível do ruído. As 2 restantes (type=code) têm markdown mas empatam mesmo
   assim.
3. **Persistência incondicional do slug.** content_taxonomy.py:1272 grava
   `computed_subunit_slug` mesmo quando conf = 0.0/ambíguo — o slug arbitrário
   do item 1 chega à UI como se fosse atribuição.

**Achado-chave (8º "segundo cérebro"):** `code_curation.json` do repo real tem,
por código, resumo Gemini rico — `inferred_title` ("Verificação de Correção de
Programa Simples com Tripla de Hoare"), `concepts` (6 itens: "Tripla de Hoare",
"Pré-condição"…), `summary` em prosa, `language`. O matcher de BLOCO de código
consome isso (consensus); o scorer de SUBUNIDADE nunca lê. Mesmo padrão dos 7
segundos cérebros já mortos: sinal forte existe, caminho que decide ignora.

**Achados secundários:**
- Manifest real tem ids DUPLICADOS: `introducao` ×2 e `t1-2026-1` ×2 (pdf
  trabalhos + zip codigo-professor compartilham id). Mascarou o diagnóstico
  (probe achava o pdf conf 0.85, manifest mostrava o zip conf 0.0).
- ~~Dívida #5 confirmada VIVA~~ — **RESOLVIDA 16/06 (432b64a, fix (d))**:
  `retag_manifest.py` passava só `{"_repo_root": …}` ⇒ taxonomia vazia no retag;
  um retag de subunidade LIMPARIA os slugs. Mascarado porque o reprocesso completo
  do app reescrevia tudo depois. Fix: fallback de disco em `resolve_unit_block_tags`.

**Correções candidatas (decisão 12/06: (a) agora, (b) depois — ambas FEITAS):**
- (a) ~~Mínima~~ — **FEITO 12/06 (62da0d2)**: empate exato ou
  `winner_score <= 0` ⇒ slug vazio + reason (`empate-exato Nx score=…` /
  `sem-sinal`). Replay no repo real: 9/12 viram vazio honesto, 3 ganham
  vencedor real por margem mínima (ambiguous, banda baixa). Golden intacto
  41/48, confiante-errado 0, suíte 1320.
- (b) ~~Sinal real~~ — **FEITO 13/06 (1c787fb)**: `code_curation_signal_text`
  (em `code_summarization.py`) reaproveita o resumo Gemini já existente
  (`inferred_title` como heading peso 4.4, `concepts`/`summary`/`language` no
  corpo) como sinal léxico. Em `resolve_unit_block_tags` é injetado SÓ no input
  do scorer de subunidade (markdown de bloco/unidade intacto → golden de bloco
  preservado). **Geral**: qualquer cadeira com `code_curation.json` se beneficia,
  sem hardcode de MF. Replay no repo real: 10/12 entries que davam empate-vazio
  agora ganham subunidade real (hoare→logica-de-hoare, introducao→sistemas-formais,
  exercicios-conjuntos→pre-e-pos-condicoes…); 2 seguem empate honesto. Golden de
  bloco intacto 41/48, confiante-errado 0, suíte 1330.
- (c) Higiene: unicidade de id no manifest (dedupe ou sufixo por categoria).
  **Causa-raiz diagnosticada na auditoria 16/06 (P0-4):** `_dedup_entry_id` só roda no
  caminho single-entry (`lifecycle_ops.process_single_impl`); os builds batch
  (`build_workflow.py:64`, `incremental_build.py:48`) NÃO deduplicam → ids duplicados
  (reintroduz B5: dirs de assets compartilhados). Fix: extrair o dedup p/ helper e
  chamar nos 2 laços batch antes de `_process_entry`.
  **fix c v2 (16/06):** o sufixo do dedup muda de categoria → **extensão** (cascata
  ext→pasta→contador): `introducao-zip`, `exemplos-zip`. A categoria não desambigua colisão
  mesma-categoria (`exemplos.thy` vs `exemplos.zip`) e o id `x-codigo-professor` confunde com
  categoria. Id segue determinístico/no-import (Gemini NÃO define id; só o título de display,
  via `inferred_title` na aba códigos).
- (d) ~~Dívida #5~~ — **FEITO 16/06 (432b64a)**: `load_internal_content_taxonomy`
  lê `course/.content_taxonomy.json` do `_repo_root` como fallback quando
  `_content_taxonomy` não vem em memória. Antes, `resolve_unit_block_tags` lia a
  taxonomia só de `course_meta["_content_taxonomy"]`; o retag passa apenas
  `{"_repo_root": …}` → taxonomia vazia → um retag LIMPARIA todos os
  `computed_subunit_slug` (footgun latente, mascarado só porque o reprocesso
  completo do app reescrevia tudo depois). In-memory mantém precedência (pipeline
  completo intacto). Replay no repo real: retag agora **preserva** os slugs
  (42→52 não-vazios; antes iria a ~0). Golden de bloco intacto 41/48,
  confiante-errado 0, suíte 1332.

**Modularidade (confirmado 13/06):** lógica é geral, não específica de MF.
- `code_curation.json` é artefato genérico — qualquer cadeira com código o gera.
- `code_curation_signal_text` lê campos genéricos (`inferred_title`, `concepts`,
  `summary`, `language`); zero string hardcoded de MF.
- Injeção por chave de entry (`_code_curation_entries.get(entry["id"])`): entry sem
  resumo de código mantém `markdown_text` intacto; cadeira sem código nenhum = dict
  vazio, efeito nulo.
- Distinção chave: a **lógica** é modular; só a **calibração dos pesos** foi validada
  em 1 cadeira (MF). Risco de calibração coberto abaixo (2º golden set).

## Auditoria completa do sistema de atribuição (16/06, wave 1+2)

Investigação read-only pedida pelo usuário ("conflitos, duplicação, mortos, ruído").
9 clusters cobertos por subagentes paralelos em 2 ondas. Categorias: **CONFLITO** (um
passo desfaz/sobrescreve outro), **DUPLICAÇÃO** (mesma lógica em 2+ lugares), **MORTO**
(sem caller / campo nunca lido / ramo inalcançável), **RUÍDO** (sinal que atrapalha mais
que ajuda). Cobertura: todo o pipeline (import → card/`source_section` → scorer file→block
→ Gemini código→bloco → matcher posicional de unidade → scorer subunit → tags → bandas/caps
→ conflicts → consumidores). Fora de escopo (não-core): `image_resolution.py`,
`semantic_config.py`. Espelhada na aba 6 de `docs/Overview-Sistema.html`.

### P0 — corrompe atribuição (alta confiança, cross-validado)

1. **8º "segundo cérebro" = SUBUNIDADE.** `computed_subunit_slug` gravado SEMPRE/ungated
   (content_taxonomy.py:1316) vs tag `subunit:` gravada só após o gate (:1278-1279). Lidos
   em precedência divergente: `navigation.py:623-625` (FILE_MAP) usa o ungated e ignora a
   tag; `dialogs.py:4154-4166` (editor) prefere a tag gated → mesma entry atribuída no
   FILE_MAP e "sugestão baixa confiança" no editor. PIOR: `computed_subunit_slug` NÃO é
   campo declarado de `FileEntry` (core.py:75-76 só tem `subunit_match_confidence/reasons`)
   → round-trip `from_dict→to_dict` (fila/SubjectProfile) descarta o slug e mantém a
   confiança (confiança órfã).
2. **Gemini código→bloco PARALELO ao funil determinístico.** `primary_block_id` (Gemini)
   governa CODE_INDEX.md / CRONOGRAMA_DETALHADO.md / contagem CODE_HEALTH
   (repo.py:837/913/994); `computed_block_id` (funil) governa todo o resto (file_map.py:613,
   `resolve_effective_block`). Nunca reconciliam → mesma entry de código mostra bloco
   diferente conforme o .md. **→ decisão D1.**
3. **`winning_unit_slug` parâmetro morto** (file_map.py:173-174): nenhum caller o passa → o
   scorer de subunidade escolhe sobre TODOS os tópicos de TODAS as unidades, sem restringir
   à unidade do bloco. Causa-raiz do desalinhamento subunit↛unit (hoje só avisado em
   dialogs.py:4143, nunca corrigido; nada reconcilia subunit↔unidade-do-bloco).
4. **Fix (c) — dedup de id ausente no batch** (ver item (c) acima): `build_workflow.py:64`,
   `incremental_build.py:48` não dedupam → `introducao`×2 / `t1-2026-1`×2 (B5).

### P1 — código/contrato morto

5. **`administrative_only` contrato 100% quebrado:** `_timeline_block_is_administrative_only`
   nunca grava a chave no payload (index.py:888 só faz `continue`) → 4 filtros consumidores
   são no-op permanentes: content_taxonomy.py:1144 (PIOR — caminho material→bloco real,
   blocos admin entram como candidatos), file_map.py:537, cronograma_health.py:124,
   moodle_labels.py:131. **→ decisão D2.**
6. **Piso 0.72 anulado pelo cap:** `max(conf,0.72)` (file_map.py:1354) sempre rebaixado por
   `min(conf, METHOD_CAPS["scorer_only"]=0.70)` (content_taxonomy.py:1244). Piso calibrado morto.
7. **`BLOCO_TAG=0.50` morto** (thresholds.py:139): nunca lido; a tag `bloco:` é emitida sempre
   que há `computed_block_id`, sem gate de banda. Morto OU gate faltante.
8. **Fallback keyword ~600 linhas** (index.py:2205-2213): `_assign_timeline_block_to_unit` +
   `_vote_unit_from_topic_candidates` + `_score_timeline_row_against_unit` só rodam quando
   `assign_units_positional` retorna [] (<2 unidades / 0 blocos / afinidade-zero). Scorer-keyword
   subsumido sobrevivendo como fallback de borda.
9. **`auto_suggested_unit` gate obsoleto** (conflicts.py:31-44): ramo topic-derive (gate 0.65)
   inalcançável porque `assign_units_positional` sempre grava `auto_unit_slug`. Docstring mente.
10. **Mortos menores:** branch `consensus` B quase-inalcançável (code_summarization.py:271);
    method `auto_concept` efêmero (tooltip dialogs.py:2329 mente); `process_reference_entry`
    sem caller (reference_summary.py:56).

### P2 — duplicação (manutenção; unificações eval-gated)

11. **Família de 6 scorers** (maior fonte de duplicação): 3 ponderados (index.py:1618,
    file_map.py:236, index.py:1730) + 3 de overlap leve com 3 fórmulas de confiança
    diferentes (`assign_code_to_block`, `assign_concepts_to_unit`, `assign_concepts_to_block`).
12. **2º sistema código→bloco:** `assign_code_to_block`+`_consolidate_assignment` (A-E,
    code_summarization.py:164-289) duplica o funil determinístico (content_taxonomy.py:1120-1227).
13. **3× basename→source_section:** stash_backfill.py:16, moodle.py:156, m365.py:271.
14. **2 rotas card→bloco:** `resolve_card_to_block` (léxico só-nome, card_block.py:62) vs
    `derive_card_block_map` (datas, autoritativo).
15. **Predicados de kind duplicados** index vs classifier.py com vocabulário DIVERGENTE
    (index aceita "prova 1/2"/"teste"; classifier exige "prova N") — meio conflito.
16. **Menores:** `is_exercise_entry` (lista repetida 3-4×), `entry_norm` duplicado, filtro
    "token significativo len≥4" (~5 sites), 3 tokenizadores divergentes.

### P3 — ruído (eval-gated; golden de bloco 41/48 é a rede)

17. auto_tags realimenta o scorer de subunit/unidade (auto-confirmação em retag; index.py:1755,1801).
18. `llm_only` confiança hardcoded 0.6 = banda alta sem corroboração léxica.
19. m365 sobrescreve `source_section` da API Moodle por ordem de execução (inverte autoridade).
20. keyword "trabalho" sozinha → DELIVERABLE, zera unidade de aula (classifier.py:77-82).
21. canal de data duplo (file_map.py:1297+1311); herança bidirecional soft-continuation
    (index.py:2218, quebra monotonicidade do DP); substring em fontes fracas (file_map.py:700);
    pisos de confiança hardcoded fora de thresholds.py.

### Não-problemas confirmados
- Referências (Approach C) NÃO contaminam a atribuição principal (isolamento em 3 níveis:
  seleção disjunta, persistência separada, leitura sem mutação).
- `margin_confidence` vs `relative_margin_confidence`: escopos disjuntos, intencional.
- METHOD_CAPS não tornam banda alta inalcançável.
- Os 3 "segundos cérebros" do FILE_MAP já mortos NÃO ressurgiram.

### 2 decisões de arquitetura pendentes (discutir antes de corrigir)
- **D1 — Gemini código→bloco:** o caminho deve existir (votar/subir confiança) ou
  CODE_INDEX/CRONOGRAMA/CODE_HEALTH passam a ler `resolve_effective_block` (fonte única)? Se
  fonte única, todo o ramo de DECISÃO de bloco em `_consolidate_assignment` (A-E) é redundante
  com o funil; mantém-se do Gemini só os sinais que não duplicam (já alimentam o scorer de subunit).
- **D2 — `administrative_only`:** ligar o campo (gravar no payload + runtime, religando os 4
  filtros) OU deletar os 4 no-ops? Risco de deletar sem ligar: content_taxonomy.py:1144 opera
  sobre runtime que ainda inclui blocos admin.

### Sequência de fixes recomendada
1. P0-4 (fix c) — barato, fecha B5.
2. P0-1 + P0-3 juntos — fonte-única de subunidade (declarar `computed_subunit_slug` em
   `FileEntry`, leitores na mesma ordem, ligar `winning_unit_slug`).
3. D1/D2 (decisão) → então o P1 derivado.
4. P1 morto barato (BLOCO_TAG, piso 0.72, auto_suggested_unit, mortos menores).
5. P2 unificações + P3 ruído, cada um atrás do golden.

## Riscos transversais

- **Golden set de 1 disciplina só**: Metodos-Formais pode enviesar (muito código
  Isabelle/Dafny). Mitigação: quando outra matéria tiver cronograma rico, adicionar
  segundo golden set (IA, SO…).
- **Manifests existentes**: mudanças de confiança/method só se materializam após
  retag/reprocesso — comunicar na UI ("reprocesse para aplicar").
- **F1 na branch**: este plano continua a branch `feat/reconciliar-unit-bloco` ou
  nova por fase — decidir no início de cada fase; merges pequenos e frequentes
  preferíveis a uma branch gigante.

## Fora de escopo (decidido)

- Trocar o scorer por LLM para tudo (custo/latência; o funil com prior já entrega).
- Remover o gabarito ou o scorer (dados provam que ambos são necessários: 0/22 com
  prior; 59% sem).
- Reescrever timeline_index (estrutura fiel ao cronograma; só o topic_text concatenado
  entra como item do P4).
