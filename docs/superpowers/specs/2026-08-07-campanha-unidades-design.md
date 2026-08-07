# Spec — Unidades (campanha unificação, subprojeto 2/3)

data: 2026-08-07 · aprovado pelo user nesta sessão (abordagem A — exclusividade de título na
FONTE/taxonomia; gold de unidade nos 5 cursos completos; merge `unit_index`→projeção de
`content_taxonomy` FORA, trilho próprio pós-curas). Ordem da campanha aprovada:
Índice (FECHADA) → **Unidades** → SO. Insumos primários:
`docs/reports/2026-08-06-task3-colisao-rotulo-mf.md` (causa-raiz, matriz de afinidade, DP) ·
tracker `docs/reports/pendencias.md` (fio subject_profile Tasks 2/3, item PRIORITÁRIO
u3/subject_profile) · handoff `docs/reports/2026-08-07-handoff-campanha-indice-fechada.md` §4.1.

## 1. Problema

4/5 cursos perderam unidades no `.timeline_index.json` (verificação Task 2 do fio, `as-of
f11dda7`): **MF 3→2** (falta u03-verificacao-de-modelos) · **SO 7→6** (falta u04-deadlock, unidade
do MEIO — não é truncamento de cauda) · **ES2 3→2** (falta u03-testes-de-software) · **IA 5→3**
(faltam u04-raciocinio-sob-incerteza, u05-aprendizado-de-maquina). TCC 4/4 intacto. O wiring
(`subject_profile` chegando ao `RepoBuilder`) já foi consertado (fio Task 1), mas **reprocess NÃO
cura** (provado 4×, Task 3 rollback): o defeito restante é de sinal, não de fio.

Agravantes provados:
- **Dual-source sonda/produção nos 2 sentidos** (Task 2/3): sonda `retag(persist=False)` pula
  `attach_block_summary_fields` etc. → 3 falsos alarmes de drift de `computed_block_id` + 1 falso
  positivo de unidade (sonda previu bloco-16→u03 conf 0.6; produção real deu u02 conf 0.4).
- **SO com 2 anomalias extras**: conteúdo de deadlock absorvido no `topic_text` do bloco-05
  (unidade-02 — perda de fidelidade, não só de rótulo) e ordem de unidades NÃO-monotônica nos
  blocos 10-12 (`unidade-07`→`unidade-05`→`unidade-07` — sinal de rodadas de reprocess sobrepostas,
  mecanismo não investigado).
- **Resíduo da campanha 1**: scorer do AnchorEngine sensível a rótulo rico de taxonomia em
  vizinhos topicais (aula-13-teorema-de-rice atraída por "Prova da Indecidibilidade..."), mitigado
  por pino gold-backed `91c1d2a`, SEM guard estrutural.

## 2. Causa-raiz (CONFIRMADA por reconstrução bit-a-bit, Task 3)

Dois fatores compostos, reproduzidos contra o disco real do MF:

1. **Colisão de rótulo de tópico.** O `teaching_plan` do MF tem, dentro da abertura da Unidade 01,
   o bullet-preview *"1.3.1. Verificação de Modelos (Model Checking)"*. `build_content_taxonomy`
   cria tópico pra esse bullet sob a u01, e o alias-enrichment
   (`content_taxonomy.py:502-536`) casa headings reais do material ("VERIFICAÇÃO DE MODELOS",
   "Verificação de Modelos e Lógica Temporal", "checagem de modelos") por TEXTO do rótulo, não por
   unidade → aliases conteudisticamente da u03 grudam na cópia da u01 → `_unit_tokens(u01)` ganha
   `temporal`/`modelos` → **empate 4×4** u01/u03 na afinidade do bloco-16 (tokens
   `{exercicios, ferramenta, logica, modelos, temporal, verificacao}`).
2. **DP monotônico global com tie-break "menor índice"** (`unit_matcher.py:84-88,92-98`): cauda
   sem sinal (bloco-17 "revisão", bloco-20 "devolução de provas") não recompensa avançar de
   unidade; empatado, bloco-16 fica em u02 conf 0.4. Comportamento CORRETO do algoritmo dado o
   empate — o defeito é o sinal contaminado, não o DP.

Bug genérico: qualquer plano cujo texto de abertura de unidade cite título de unidade futura.
Nota: o achado "U+FFFD no teaching_plan" foi **FALSIFICADO** (mojibake de console cp1252;
amendment 2026-08-06 no tracker) — a colisão é texto legítimo do plano, único problema real.

## 3. Objetivo e não-objetivos

**Objetivo**: índice dos 5 cursos com a contagem de unidades do plano de ensino (MF 3 · SO 7 ·
ES2 3 · IA 5 · TCC 4); bloco-16 MF → `unidade-03-verificacao-de-modelos`; sonda ≡ produção
byte-idêntico; gold de unidade como régua permanente; curas gated com gold pré/pós.

**Não-objetivos (FORA, destino registrado):**
- Merge `unit_index` → projeção de `content_taxonomy` → **trilho próprio PÓS-curas** (ruling do
  user nesta sessão; merge antes das curas contamina o diff com churn de slugs).
- Deleção física de legado → cutover FASE 5 (lista no tracker).
- Reprocess-all 5 repos → fila item 3 (pós-campanha).
- SO providers (57.9→~85) → campanha 3/3.
- Golden IA stale (`test_caracterizacao_blocos_atual[IA]`) → item [CODE] próprio, re-baseline
  gated fora daqui. Suite baseline desta campanha = 1881/4/**1** (o 1 é ele).
- R2/R3/R7/R9/R11/R12 → trilhos já registrados no tracker.
- Mexer no DP do `unit_matcher` (tie-break/pesos) → FORA explícito: mudá-lo mascara colisão em
  vez de matá-la e afeta os 5 cursos de uma vez.

## 4. Design (6 componentes)

**U1 — Exclusividade de título de unidade na taxonomia (núcleo; TDD com dados reais do MF).**
Em `build_content_taxonomy`/enriquecimento:
(a) tópico cujo rótulo normalizado casa o TÍTULO de outra unidade (caso preview 1.3.1) não
contribui tokens/aliases pra assinatura da unidade hospedeira;
(b) alias-enrichment (`content_taxonomy.py:502-536`), ao escolher `best_topic` pra um heading,
prefere tópico sob a unidade DONA do título quando o heading casa título de unidade.
Efeito esperado (calculado da matriz real da Task 3): u01 perde `modelos`+`temporal` → afinidade
do bloco-16 vira u01=2/u02=3/u03=4 → DP avança pra u03, conf 0.6 (margem 1). Detalhe fino
(re-atribuir o tópico-preview à unidade dona vs só excluí-lo da assinatura) decidido no plano com
o RED test na mão.

**U2 — Unificação de assinatura sonda/produção (padrão C2 da campanha 1).**
Sondas de unidade (`verify_units.py`, probes de recompute) obtêm block→unit pelo caminho COMPLETO
de produção (montador único `_build_file_map_timeline_context_from_course` + curation +
post-transforms + `attach_block_summary_fields`, na ordem real), nunca recomputam por atalho.
Aceite: sonda × produção byte-idêntico nos 5 cursos. Mata a classe "3 falsos alarmes + 1 falso
positivo". Regra dura herdada: número de sonda pré-U2 não vale como evidência de gate.

**U3 — Gold de unidade, 5 cursos completos (USER, one-time).**
Template CSV por curso: `block_uuid`, bloco-NN informativo, datas, `topic_text`, `unit_slug`
atual, coluna `true_unit` vazia. User rotula (~80 linhas no total; TCC incluso = régua de
regressão pro reprocess-all). Vira `tests/fixtures/eval/gold_units_<curso>.csv` +
`scripts/eval_units.py` (% blocos-aula com `unit_slug` == gold; sem colapso de par). **Keyed por
`block_uuid`**, nunca bloco-NN posicional (lição do drift do gold MF, tracker 2026-07-08).
Baseline pré-cura medido e versionado ANTES de qualquer escrita em repo-tutor.

**U4 — Curas gated, curso a curso: MF → SO → ES2 → IA (TCC sem cura).**
Por curso: snapshot tracked+gitignored com eco por arquivo + sha256 (protocolo provado 3×; glob
silencioso = rede furada) → reprocess pipeline REAL (`RepoBuilder.incremental_build()`) → gates:
(a) unidades recuperadas na contagem do plano; (b) `eval_units` pré/pós sem regressão (mudança
INTENCIONAL de unidade justificada pelo gold, caso a caso); (c) `computed_block_id` 0 mudanças
ou diff justificado; (d) réguas vivas da campanha 1 byte-idênticas (fase2-TCC 84.2 cw0 · fase4
58/58 · fase5 6/8 · MF eval 97.0 · rebuild_diff 0/5); (e) suite sem fail novo (baseline 1881/4/1).
FAIL em qualquer gate → rollback hash-verificado + investigação com report próprio (padrão "cada
camada consertada revela a próxima" — esperado). Curadoria manual (`.timeline_curation.json`) só
como fallback pontual com ruling explícito do user, nunca silenciosa.
**SO carrega 2 sub-itens**: diagnóstico da anomalia topic_text (deadlock absorvido no bloco-05) e
da ordem não-monotônica ANTES da cura; se o fix exigir re-segmentação além de atribuição de
unidade → HALT ruling.

**U5 — Herdados do review final da campanha 1.**
W1 (`pedagogical_regeneration.py:394-402`) adota `engine._build_rich_content_taxonomy` (mata
dual-source por cópia) · warning na degradação silenciosa de `build_rich_content_taxonomy`
(manifest ausente/corrupto → hoje degrada mudo pra taxonomia pobre) · `logger.warning` nos 2
early-returns mudos de unidade (`file_map.py:1500` e `:1628` — curso perde 1/3 da estrutura sem
nenhum sinal).

**U6 — Resíduo do scorer do AnchorEngine (condicional, pós-U1).**
Re-medir o caso aula-13-teorema-de-rice (TCC) em sandbox SEM o pino: se o scorer ainda atrai por
rótulo rico de vizinho topical → especificar guard C6-equivalente no caminho do scorer; se U1
matou → registrar veredito e fechar o item. Pino gold-backed `91c1d2a` segura produção enquanto
isso — U6 não bloqueia nada.

**Ordem**: U1 → U5 → U2 → U3 (USER) → U4 (MF→SO→ES2→IA) → U6.

## 5. Riscos e tratamento de erro

- **Churn de sidecar da taxonomia nos 5 repos** (U1 muda `content_taxonomy.json` persistido):
  nenhuma escrita em repo-tutor fora de U4; cada cura com snapshot+sha256 e rollback testado.
- **Empate persistente pós-fix** (colisão de outra família em SO/ES2/IA): rollback imediato,
  report, HALT ruling. Nunca forçar.
- **Falso-verde por sonda**: todo gate de U4 mede pelo caminho de produção (pós-U2).
- **Golden IA já failando**: 1 failed conhecido = baseline; 2º fail = regressão real.

## 6. Testes

- **U1**: TDD com fixture da taxonomia real do MF, proveniência registrada (regra
  `context/conventions.md`). RED: empate 4×4, bloco-16 u02 · GREEN: bloco-16 u03 conf 0.6.
  Não-regressão: plano SEM preview (TCC) → taxonomia byte-idêntica.
- **U2**: teste sonda≡produção por curso (espírito do `rebuild_diff` 0/5).
- **U4**: os gates SÃO o teste (gold pré/pós + réguas vivas).
- **U5**: manifest ausente → warning emitido, saída degradada inalterada.
- Suite completa a cada task.

## 7. Critérios de aceite da campanha

1. Índices: MF 3 · SO 7 · ES2 3 · IA 5 · TCC 4 unidades (== plano de ensino).
2. bloco-16 MF = `unidade-03-verificacao-de-modelos`; SO u04-deadlock de volta no MEIO.
3. `eval_units` 5/5 sem regressão vs gold (baseline pré-cura versionado).
4. Sonda ≡ produção byte-idêntico 5/5.
5. Réguas vivas da campanha 1 intactas; suite sem fail novo.
6. Tracker atualizado; U6 com veredito registrado (guard ou óbito).

## 8. Decisões do user nesta sessão

- Gold de unidade: **5 cursos completos** (inclui TCC como régua do reprocess-all).
- Merge das 2 fontes de unidade: **FORA** — trilho próprio pós-curas.
- Abordagem do fix: **A — fonte/taxonomia** (exclusividade de título), guard de scorer só
  condicional (U6), DP intocado.
