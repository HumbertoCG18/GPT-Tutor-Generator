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
| P4 | **APROVADO pelos números** (12/06) | alvo ~93% | — | — |

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
