# Spec — Unidades (campanha unificação, subprojeto 2/3)

data: 2026-08-07 · v2 (pós spec-review com dados reais,
`docs/reports/2026-08-07-spec-review-unidades.md` — TODA afirmação de mecanismo abaixo foi
verificada executavelmente, READ-ONLY, contra taxonomia recomputada em memória + índices reais).
Aprovado pelo user nesta sessão (abordagem A — exclusividade de título na FONTE/taxonomia; gold
de unidade nos 5 cursos completos; merge `unit_index`→projeção de `content_taxonomy` FORA,
trilho próprio pós-curas). Ordem da campanha aprovada: Índice (FECHADA) → **Unidades** → SO.
Insumos primários: `docs/reports/2026-08-06-task3-colisao-rotulo-mf.md` · spec-review acima ·
tracker `docs/reports/pendencias.md` · handoff `2026-08-07-handoff-campanha-indice-fechada.md` §4.1.

## 1. Problema

4/5 cursos perderam unidades no `.timeline_index.json` (verificado de novo nesta revisão, índice
vs parser do plano): **MF 3→2** (falta u03-verificacao-de-modelos) · **SO 7→6** (falta
u04-deadlock, unidade do MEIO) · **ES2 3→2** (falta u03-testes-de-software) · **IA 5→3** (faltam
u04-raciocinio-sob-incerteza, u05-aprendizado-de-maquina). TCC 4/4 intacto. O wiring
(`subject_profile` no `RepoBuilder`) já foi consertado (fio Task 1); **reprocess NÃO cura**
(provado 4×): o defeito restante é de sinal — e a revisão provou que é UM defeito por curso, não
um genérico (ver §2).

Agravantes provados:
- **Dual-source sonda/produção nos 2 sentidos** (Task 2/3) + prova nova da revisão: sonda
  DP-pura diverge do disco nos blocos que `finalize_block` limpa depois (`unit_slug=""` em
  revisão/suspensão/evento). Gate que não mede produção mente.
- **SO com 2 anomalias extras** (ambas re-confirmadas no disco): deadlock absorvido no
  `topic_text` do bloco-05 (sob unidade-02 — perda de fidelidade) e ordem NÃO-monotônica
  blocos 10-12 (u07→u05→u07 — camadas stale de rodadas sobrepostas; o DP atual nunca produziria
  isso, e o recompute de cura muda bloco-12 u07→u05).
- **Resíduo da campanha 1**: scorer do AnchorEngine sensível a rótulo rico em vizinhos topicais
  (aula-13 TCC), mitigado por pino `91c1d2a`, sem guard estrutural.

## 2. Causa-raiz POR CURSO (verificada, não especulada)

**MF — colisão de rótulo (DUPLA) + empate de caminho no DP.**
1. A abertura da Unidade 01 do plano contém DOIS bullets-preview de unidades futuras: *"1.3.1.
   Verificação de Modelos (Model Checking)"* (título da u03) e *"1.3.2. Verificação de
   Programas"* (título da u02). `build_content_taxonomy` cria tópicos pra eles SOB a u01, e o
   alias-enrichment (`content_taxonomy.py:502-536`) casa headings reais por TEXTO do rótulo, não
   por unidade → aliases da u03 ("Verificação de Modelos e Lógica Temporal" → `temporal`) e da
   u02 (família Dafny) grudam na u01 → empate 4×4 u01/u03 no bloco-16 (aff real `[4,3,4]`).
2. Morta a colisão, o empate REAPARECE no nível de caminho do DP: avançar pra u03 = 4+0+0; ficar
   em u02 = 3+1+0 (migalha `exercicios` do bloco-17-revisão) → tie-break "menor índice"
   (`unit_matcher.py:84-88`) mantém u02@0.4. **Por isso U1 sozinho NÃO move o bloco-16**
   (falsificado por simulação — spec v1 previa o contrário; corrigido).

**Definição operacional de "casa o título"**: pelo NÚCLEO do título, definido por TOKENS —
tokens do título menos genéricos/numerais (mecanismo `_UNIT_GENERIC`/stopwords já existente no
matcher), NÃO por regex de prefixo. Os 5 cursos atuais seguem 2 padrões ("Unidade NN —" ×4 ·
"Unidade de Aprendizagem N —" IA · "UNIDADE" maiúsculo TCC), mas NADA garante o padrão em curso
futuro ("Módulo 1", "Parte I", título sem prefixo) — e o lado do HEADING (texto livre dos
arquivos de material) não tem padrão nenhum (ruling do user 2026-08-07). Degradação graciosa:
sem prefixo → núcleo = título inteiro. Guard anti-falso-positivo pra núcleo curto/genérico
(ex.: "Testes"): calibrar no plano com os 5 corpora reais + fixture de título sem padrão.
Match ingênuo por título completo = no-op provado.

**SO — absorção de conteúdo, NÃO colisão** (0 colisões na varredura): o conteúdo de deadlock
(u04) foi absorvido no texto agregado do bloco vizinho sob u02; nenhum bloco carrega sinal de
u04 → DP pula a unidade do meio. Cura = investigação de absorção/segmentação.

**ES2 — sinal ausente, NÃO colisão** (0 colisões): u03-testes-de-software nunca vence bloco
nenhum no recompute limpo. Investigar assinatura da u03 vs tokens dos blocos finais.

**IA — violação da premissa monotônica** (0 colisões): o curso ensinou u05 (ML) no INÍCIO
(dados/k-NN/clustering, semanas 2-9) e u03/agentes no fim (Semana-16). `assign_units_positional`
exige índice não-decrescente na ordem cronológica → u04/u05 podem ser IRRECUPERÁVEIS por DP
monotônico. Cura IA começa com HALT de diagnóstico + ruling de produto.

**TCC — saudável**: 4/4 unidades, 0 colisões, recompute == disco nos blocos de produção.

## 3. Objetivo e não-objetivos

**Objetivo**: índice dos 5 cursos com a contagem de unidades do plano ONDE VIÁVEL (MF 3 · SO 7 ·
ES2 3 · TCC 4; IA condicionado ao ruling §4-U4); bloco-16 MF → `unidade-03-verificacao-de-modelos`;
sonda ≡ produção byte-idêntico; gold de unidade como régua permanente; curas gated.

**Não-objetivos (FORA, destino registrado):**
- Merge `unit_index` → projeção de `content_taxonomy` → trilho próprio PÓS-curas (ruling user).
- Deleção física de legado → cutover FASE 5. · Reprocess-all → fila 3. · SO providers →
  campanha 3/3. · Golden IA stale → item próprio (suite baseline = 1881/4/1).
- R2/R3/R7/R9/R11/R12 → trilhos já registrados no tracker.
- **Pesos/estrutura do DP intocados.** AMENDADO na revisão: refinamento de TIE-BREAK em empate
  EXATO é o U1b (abaixo) — provado que só dispara em empate (0 diffs SO/ES2/TCC) e resolve o
  caso-alvo. Mexer em pesos/afinidade/monotonicidade segue FORA (IA é ruling, não gambiarra).

## 4. Design (7 componentes)

**U1 — Exclusividade de NÚCLEO de título na taxonomia (TDD, dados reais MF).**
Em `build_content_taxonomy`: (a) tópico cujo rótulo casa núcleo de título de OUTRA unidade não
contribui tokens/aliases pra hospedeira (decisão fina excluir vs re-atribuir no plano; simulação
mostrou ambos equivalentes pro DP do MF; re-atribuir enriquece a dona — preferência default);
(b) alias-enrichment prefere tópico da unidade dona quando heading casa núcleo de título.
Efeito PROVADO: mata as 2 colisões do MF; aff bloco-16 `[4,3,4]`→`[2,3,4]`; **NÃO move bloco-16
sozinho** (empate de caminho, §2). No-op provado em SO/ES2/IA/TCC (0 colisões hoje) — guard
genérico pra planos futuros com preview.

**U1b — Desempate por sinal concentrado no DP (gated por curso).**
Tie-break lexicográfico: empate na soma de afinidade do caminho → vence o caminho com maior
Σaff² (sinal concentrado > migalhas). PROVADO por simulação 5 cursos sobre U1: MF bloco-16 →
**u03@0.6** com ZERO outro diff de produção (bloco-17/20 mudam no DP mas `finalize_block` limpa
ambos — disco confirma `unit_slug=""` neles) · SO/ES2/TCC **0 diffs** · **IA 14 diffs (colapso
pra u05) → alavanca NÃO entra em IA antes do diagnóstico U4-IA**; gate por curso obrigatório.
Alternativa testada e DESCARTADA: `exercicios` genérico (regride bloco-10 u02→u01 + 4 colaterais).

**U2 — Unificação de assinatura sonda/produção (padrão C2).**
Sondas de unidade obtêm block→unit pelo caminho COMPLETO de produção (montador único
`index.py:1349` + curation + post-transforms + `finalize_block`), nunca DP avulso. Aceite: sonda
× produção byte-idêntico nos 5 cursos. Pré-requisito dos gates de U4.

**U3 — Gold de unidade, 5 cursos completos (USER, one-time).**
Template CSV por curso: `block_uuid` (presença verificada 21/21·21/21·14/14·25/25·31/31),
bloco-NN informativo, datas, `topic_text`, `unit_slug` atual, `true_unit` vazia. **82 linhas no
total** (contado). Vira `tests/fixtures/eval/gold_units_<curso>.csv` + `scripts/eval_units.py`.
Baseline pré-cura medido e versionado ANTES de qualquer escrita.

**U4 — Curas gated, curso a curso: MF → SO → ES2 → IA (TCC sem cura).**
Por curso: snapshot+sha256 (protocolo provado 3×) → reprocess pipeline REAL → gates: (a)
unidades na contagem do plano; (b) `eval_units` pré/pós sem regressão; (c) `computed_block_id` 0
mudanças ou diff justificado; (d) réguas vivas campanha 1 byte-idênticas; (e) suite sem fail
novo. FAIL → rollback + report + HALT se mecanismo novo.
- **MF**: U1+U1b devem bastar (provado em simulação; cura confirma em produção).
- **SO**: diagnóstico da absorção do deadlock + ordem não-monotônica ANTES da cura; recompute
  muda bloco-12 u07→u05 (esperado, camada stale — gold decide o certo); re-segmentação além de
  unidade → HALT ruling.
- **ES2**: investigar por que u03-testes nunca vence (assinatura vs blocos); fix próprio + gold.
- **IA**: HALT-primeiro — diagnóstico da violação monotônica com ruling de produto (aceitar
  limitação documentada, modo não-monotônico por curso, ou outra via). U1b só entra em IA com
  aprovação pós-diagnóstico.
Curadoria manual (`.timeline_curation.json`) só como fallback pontual com ruling explícito.

**U5 — Herdados do review final da campanha 1.**
W1 (`pedagogical_regeneration.py:394-404`) adota `engine._build_rich_content_taxonomy`
(dual-source por cópia de `taxonomy_inputs.py:16-32`, verificado) · warning na degradação
silenciosa (`taxonomy_inputs.py:26-30`: manifest ausente/corrupto → `entries=[]` mudo) ·
`logger.warning` nos 2 early-returns mudos (`file_map.py:1500-1501` e `:1629-1634`, verificados
sem log). Nota: guard `_guard_units_not_silently_lost` (encolhimento de índice) JÁ existe
(`pedagogical_regeneration.py:275`) — U5 cobre as camadas que ele não vê.

**U6 — Resíduo do scorer do AnchorEngine (condicional, pós-U1).**
Re-medir aula-13 TCC em sandbox sem pino: persiste → guard C6-equivalente; morreu → registrar
óbito. Não bloqueia (pino segura produção).

**Ordem**: U1 → U1b → U5 → U2 → U3 (USER) → U4 (MF→SO→ES2→IA) → U6.

## 5. Riscos e tratamento de erro

- **Churn de sidecar** (U1/U1b mudam taxonomia/índice persistidos): escrita só em U4, com
  snapshot+sha256 e rollback testado.
- **Mecanismo novo por curso**: esperado (SO/ES2/IA já têm mecanismos próprios nomeados);
  rollback + report + HALT ruling.
- **Falso-verde por sonda**: gates medem produção (pós-U2). Regra dura.
- **Golden IA já failando**: 1 fail = baseline; 2º fail = regressão real.
- **IA pode não ter cura sob DP monotônico**: aceite condicionado a ruling — falha honesta
  documentada > número forçado.

## 6. Testes

- **U1**: TDD fixture da taxonomia real MF (proveniência registrada). RED: 2 tópicos-preview sob
  u01, aff bloco-16 `[4,3,4]` · GREEN: colisões mortas, aff `[2,3,4]`. Não-regressão: TCC
  byte-idêntico (0 colisões → no-op). + casos do núcleo por tokens: título SEM prefixo padrão
  casa; núcleo curto/genérico NÃO dispara falso positivo.
- **U1b**: TDD no `unit_matcher`: caso empate-de-caminho real do MF (RED: u02@0.4 · GREEN:
  u03@0.6); caso sem-empate → saída idêntica à atual (SO/ES2/TCC como fixtures de não-regressão).
- **U2**: teste sonda≡produção por curso.
- **U4**: gates são o teste (gold pré/pós + réguas vivas).
- **U5**: manifest ausente → warning emitido, saída inalterada.
- Suite completa a cada task (baseline 1881/4/1).

## 7. Critérios de aceite da campanha

1. Índices: MF 3 · SO 7 · ES2 3 · TCC 4 unidades; **IA**: u04/u05 recuperadas OU ruling de
   viabilidade documentado (decisão de produto na cura IA).
2. bloco-16 MF = `unidade-03-verificacao-de-modelos` (caminho provado: U1+U1b).
3. `eval_units` sem regressão vs gold nos cursos curados (baseline pré-cura versionado).
4. Sonda ≡ produção byte-idêntico 5/5.
5. Réguas vivas da campanha 1 intactas; suite sem fail novo.
6. Tracker atualizado; U6 com veredito registrado.

## 8. Decisões do user + trilha da revisão

- Gold de unidade: 5 cursos completos. · Merge das 2 fontes: FORA (pós-curas). · Abordagem A
  (fonte/taxonomia).
- Spec-review delegado ao CC (2026-08-07): 9 claims verificados, 6 achados (A1-A6), 1 previsão
  falsificada (V5 — U1 sozinho não move bloco-16) → U1b criado, IA re-classificado como ruling.
  Evidência completa: `docs/reports/2026-08-07-spec-review-unidades.md`.
