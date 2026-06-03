# Design — Estender block-match para PDFs / imagens / exercícios

**Data:** 2026-06-03
**Status:** aprovado (brainstorming) → próximo passo: writing-plans
**Contexto:** último pré-requisito de `plans/material-agnostic-refactor.md`. Depende do schema robusto de cronograma (já concluído, Fases 0–8).

---

## 1. Problema

O mecanismo de atribuir um material a um **bloco** do cronograma já existe:
`select_probable_period_for_entry` pontua o entry contra os blocos e, se
`confidence ≥ 0.50` e não-ambíguo, injeta a tag `bloco:bloco-NN` em
`entry.auto_tags` (`content_taxonomy.py:resolve_unit_block_tags`).

O gargalo **não é o mecanismo, é o sinal**. O score do entry vem de
(`score_entry_against_timeline_row`, file_map.py): título (1.25), markdown
(1.0), filename/raw (0.65), tags (0.35), categoria (0.2). Materiais pobres em
sinal falham:

- **PDF sem markdown convertido** → `markdown_text = ""` → perde o sinal de
  peso 1.0; sobra título + filename. Filename genérico ("Aula 5.pdf") → score
  abaixo de 0.50 → sem bloco.
- **Imagem standalone** → não injeta texto de descrição nos sinais → score ~0.
- **Exercício** → ganha bônus quando o bloco menciona "lista/exercício", mas
  ainda precisa de conteúdo; `EXERCISE_INDEX` só linka unidade, não bloco.
- **Código funciona** porque ganha concept-match rico via Gemini
  (`code_summarization.py` → `code_curation.json`).

## 2. Critério de sucesso

Mensurável via novo `CRONOGRAMA_HEALTH.md` (por curso):

- `% de materiais com bloco` (cobertura), `# órfãos`, `blocos ricos vs pobres`
  (nº de materiais por bloco), quebra por tipo (pdf/imagem/exercício/código).
- Gate opcional no CI (espelha o de timeline): cobertura mínima por curso /
  órfãos sinalizados — **não** falha por material genuinamente ambíguo
  (esses vão pra curadoria).

Meta: **cobertura alta automática + curadoria fecha o resíduo** (mesma
filosofia da Fase 5 do schema robusto: determinístico + dado, zero refactor
por cadeira).

## 3. Arquitetura (3 camadas + medição)

### Camada 1 — Garantia de sinal determinístico (zero LLM novo)
- **PDF**: garantir markdown disponível no momento do match. Se não houver
  `.md` convertido, usar o texto já disponível antes de cair em `""`
  (sem forçar re-extração custosa — ver risco R1).
- **Imagem**: alimentar a descrição já injetada (ollama/datalab/vision) nos
  sinais do entry (`collect_entry_unit_signals`). Hoje a descrição vive no
  markdown da página, mas a imagem *standalone* não contribui pro score.
- **Exercício**: incluir o conteúdo do exercício no sinal e reaproveitar o
  bônus de termo de bloco que já existe.

### Camada 2 — Resumo Gemini só no resíduo (limitado + cacheado)
- Só pros materiais que **ainda** ficam abaixo de `0.50` após a Camada 1.
- **Generalizar** `code_summarization.summarize_code_entry` para qualquer
  material (ver Fase 0.d) — **não** criar um módulo paralelo gêmeo.
- Gera keywords/conceitos → reforça o sinal → re-score.
- **Cap** (top-N por build, órfãos primeiro) + **cache** (persiste o resumo;
  rebuild não re-chama). Opt-in (extra `code-summarization` já existe).

### Camada 3 — Curadoria do resíduo (já existe)
- `manual_timeline_block_id` no dashboard fecha o que sobra (precedência
  absoluta; a tag `bloco:` é derivada dele). Garantir que os órfãos fiquem
  visíveis (a seção "Sem bloco atribuído" já existe).

### Medição — `CRONOGRAMA_HEALTH.md`
- Gerado no build (`pedagogical_regeneration.py`): cobertura, órfãos, blocos
  ricos/pobres, por tipo. Fonte da métrica de sucesso.

### Fluxo de dados
```
entry → garante markdown/descrição (C1)
      → collect_entry_unit_signals (título + markdown+descrição + tags + filename)
      → score vs blocos (select_probable_period_for_entry)
      → conf ≥ 0.50 e não-ambíguo?  ── sim → tag bloco:bloco-NN
                                     └ não → resíduo (C2): summary Gemini → re-score
                                              ── passou → tag bloco:
                                              └ ainda abaixo → órfão → curadoria (C3)
build → CRONOGRAMA_HEALTH.md (cobertura por curso/tipo)
```

## 4. Fase 0 — Consolidação (dobrada da auditoria de arquitetura)

A auditoria do pipeline de atribuição revelou dívida que **será composta** se
adicionarmos cobertura sem consolidar. Itens pequenos, baixo risco, alto
retorno — feitos ANTES da feature:

- **0.a — Centralizar thresholds.** Os limiares estão hardcoded inline
  (`0.50/0.55/0.60/0.65/0.35/1.0/1.85·1.75·1.35/0.10/0.18/0.20`) espalhados em
  `file_map.py` e `timeline/index.py`. Extrair para um módulo de constantes
  nomeadas (ex.: `src/builder/routing/thresholds.py` ou
  `timeline/thresholds.py`), importado por todos. A cobertura de material
  adiciona seu próprio limiar lá.
- **0.b — Helper da fórmula de confidence.** `(winner − runner) + (winner·K)`
  está duplicada 4× (K=0.18 em 3 lugares, K=0.20 em 1 — provável inconsistência
  não-intencional). Extrair `margin_confidence(winner, runner, k)` e padronizar
  o K (decisão registrada no plano).
- **0.c — `normalize_match_text` único.** Duplicada em ~6 arquivos (1 variante
  diverge em `content_taxonomy.py`). Consolidar numa fonte
  (`src/builder/text/normalize.py`) e re-importar. Cuidado: validar que a
  variante divergente não muda resultados de match (teste de regressão).
- **0.d — Generalizar `code_summarization`.** Em vez de `material_summarization.py`
  paralelo, extrair o núcleo de summarização (Gemini client + cache + cap) para
  reuso por código E materiais. A Camada 2 consome essa base.

**Fora de escopo (dívida separada, NÃO tocar agora):**
- Facade `teaching_timeline.py` + re-alias no `engine.py` (5 camadas de
  indireção, 5 wrappers passthrough, `regenerate_pedagogical_files` com 36
  params `*_fn`). Pervasivo e arriscado — vira um plano próprio de refactor.
- Os 4 "serializadores" de timeline index (`_serialize_timeline_index`,
  `persist_enriched_timeline_index`, `_write_internal_timeline_index`,
  `core_utils`) com limpeza sobreposta.
- `ASSESSMENT/REVIEW/NON_ACAD` duplicados em `audit_timeline.py` vs
  `classifier.py` (script de dev, baixo risco).

**Nota de naming (documentar, não renomear):** existe `manual_unit_slug` no
*entry* (arquivo→unidade, em `manifest.json`) E no *bloco*
(`.timeline_curation.json`, bloco→unidade). Mesmo nome, escopos diferentes.
**Não renomear** o do bloco (quebraria os `.timeline_curation.json` já
escritos nos 5 cursos). Documentar a distinção no docstring de `curation.py`.

## 5. Componentes e arquivos

| Componente | Arquivo | Mudança |
|---|---|---|
| Sinal de imagem/exercício | `extraction/entry_signals.py` | nova fonte `image_description_text` (~peso 1.0) + conteúdo de exercício |
| Fallback de markdown | `artifacts/navigation.py` | antes de retornar `""`, buscar descrição/texto convertido |
| Wiring de score | `routing/file_map.py` | consumir o novo sinal; usar thresholds centralizados |
| Summarizer residual | `core/code_summarization.py` (generalizado) | núcleo reusável; materiais órfãos pós-C1, com cap+cache |
| Health renderer | `artifacts/repo.py` | `cronograma_health_md()` |
| Build wiring | `ops/pedagogical_regeneration.py` | chama summarizer residual + escreve HEALTH |
| Validação | `scripts/validate_materials.py` (novo) | métrica de cobertura + gate opcional |
| Thresholds | módulo novo (0.a) | constantes nomeadas |
| Normalize | `text/normalize.py` (novo, 0.c) | fonte única |

## 6. Testes

Determinístico, **sem chamar Gemini real** (client mockado):

- **C1**: `collect_entry_unit_signals` com imagem (descrição vira sinal),
  exercício (conteúdo vira sinal), PDF sem `.md` (fallback). Em fixture, o
  score de bloco sobe acima de 0.50.
- **C2**: `summarize_*` com client mockado; cache hit não re-chama; cap
  respeitado; órfão pós-C1 vira `bloco:` após summary.
- **Health**: `cronograma_health_md` em fixture → cobertura/órfãos corretos.
- **Fase 0**: `margin_confidence` (0.b) com casos conhecidos; `normalize_match_text`
  consolidado bate com as 6 versões antigas (regressão); thresholds importados.
- **Regressão**: corpus dos 5 cursos reais — cobertura sobe, zero crash.

## 7. Ordem de fases (incremental, cada uma entrega valor)

0. **Fase 0** — Consolidação (0.a–0.d). Base limpa.
1. **Fase 1** — Métrica primeiro: `cronograma_health_md` + baseline de
   cobertura atual (mede ANTES de mexer no sinal).
2. **Fase 2** — C1 determinístico (imagem/exercício/PDF). Re-mede cobertura.
3. **Fase 3** — C2 Gemini residual (cap + cache, opt-in).
4. **Fase 4** — Gate/validação de cobertura + curadoria de órfãos visível.
5. **Fase 5** — Handshake: marca o pré-req do `material-agnostic-refactor.md`
   concluído.

## 8. Riscos / mitigação

- **R1 — Conversão PDF lazy/acoplada ao pipeline pesado.** A Fase 2 isola só a
  *leitura* do markdown; se faltar, fallback de sinal (não força re-extração
  custosa). Não regredir o build.
- **R2 — Custo Gemini.** Cap + cache + opt-in; órfãos primeiro.
- **R3 — Falso-positivo de bloco** (material casa bloco errado). Mantém
  threshold 0.50 + curadoria corrige; HEALTH expõe blocos "ricos demais".
- **R4 — Consolidação muda resultado de match** (0.b/0.c). Testes de regressão
  no corpus real travam isso antes de seguir.

## 9. Não-objetivos

- Renderer `CRONOGRAMA_DETALHADO.md`, aba na UI, novo formato de output
  (ficam no `material-agnostic-refactor.md`, agora desbloqueado).
- Refactor de facade/DI e dos serializadores (dívida separada).
- Inferir bloco via LLM como caminho primário (Gemini é só fallback do resíduo).
