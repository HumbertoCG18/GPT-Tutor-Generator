# Alavanca 0 — índice data→tópico (lessons[].text) como termo do fusor (β)

date: 2026-06-17
status: SUPERSEDED (2026-07-01) — o sinal (.lessons_index.json) virou 1ª classe no disambiguator do
motor de atribuição (D3/D5, log 2026-06-28-motor-atribuicao-decisoes.md); o termo-β no fusor velho
mira caminho que morre no cutover 3.4. Caso-alvo (card Verificação de Programas MF) herdado pelo spec
do motor como requisito de lesson-matching fino.
branch: `feat/reconciliar-unit-bloco`
relacionado: `docs/superpowers/specs/2026-06-17-signal-registry-design.md` (alavanca 0), gold travado em `tests/fixtures/eval/code_block_gold.json`

## Contexto (por quê)

O resolver erra 3-4 dos 6 casos do gold do MF dentro de UM card multi-bloco
("Verificação de Programas" = blocos 10-15). O `source_section` (alavanca 2, já no
resolver) é a janela do card inteiro — não discrimina bloco fino. O sinal que
discrimina existe e o pipeline joga fora: os **labels semanais** do Moodle trazem
`(DD/MM): tópico` por aula (`lessons[].text`), parseados por `parse_card_dates`
(formato A-C) e **dropados** em `derive_card_block_map` (`moodle_labels.py:150` usa
só `dates`). O card "Verificação de Programas" do MF tem **14 lessons** cobrindo
exatamente Dafny/Hoare/NuSMV — onde estão `exemplos-zip`, `invariantes`,
`tiposindutivos`. Resultado esperado: resolver vai de 11/17 → ~14/17 sem hardcode.

Decisão do usuário (2026-06-17): abordagem **β** — canal + termo explícito no fusor
(registry), não enriquecimento implícito do block-vec (α). Persistência decidida
neste plano (ver abaixo).

## Constatação que força a arquitetura

O `contents` cru da API Moodle (`core_course_get_contents`) **não persiste em disco**
— só existe no import (`moodle.py:393`, onde `parse_card_dates` já roda). Logo o
índice tem que ser **construído no import e serializado**; runtime-efêmero em tempo
de resolve é inviável (o dado sumiu). Só o MF tem `.card_block_map.json` hoje; os
outros 4 cursos ganham o sinal num re-import (degradação honesta até lá).

## Persistência (recomendada)

**Novo artefato course-level `course/.lessons_index.json`**, keyed por data ISO:

```json
{ "version": 1, "by_date": { "2026-05-11": "introducao a dafny",
                             "2026-05-13": "terminacao", ... } }
```

Por quê este e não estender `.card_block_map.json`:
- O `.card_block_map.json` é keyed por card e tem merge manual>labels
  (`merge_card_block_map`); misturar per-lesson lá complica a precedência manual.
- O resolver quer **course-level por data** (não por card) — `.lessons_index.json`
  é exatamente essa forma.
- Separação limpa: artefato gerado, inspecionável, fácil de reverter; ausência do
  arquivo = termo ausente (degradação honesta, sem quebra).

Alternativa considerada (estender o card_block_map) registrada e descartada acima.

## Mudanças (com âncoras de reúso)

### 1. Extrator (import) — `moodle_labels.py`
- Nova função pura `build_lesson_topic_index(contents, year) -> dict`:
  reusa o `lessons[]` que `parse_card_dates` (`:207`) já produz (formatos A-C
  populam `{date,text}` em `:63/:89/:106`); colapsa por data → `{date_iso: text}`
  normalizado. Sem datas/text → `{}` (formato D/E = skip honesto).
- Nenhuma mudança em `parse_card_dates`/`derive_card_block_map` (não-regressão).

### 2. Persistir no import — `moodle.py` (perto de `:393`)
- Onde `derive_card_block_map(parse_card_dates(contents, year), blocks)` já roda,
  chamar `build_lesson_topic_index(contents, year)` e gravar
  `course/.lessons_index.json` (mesmo `write_json`/encoding dos outros artefatos).
  Só escreve se não-vazio.

### 3. Carregar + threadar — `resolver_apply.py`
- `assemble_resolver_inputs`/`apply_concept_resolver` (`:26`/`:55`): ler
  `root/course/.lessons_index.json` (ausente → `None`) e passar `lessons_index=`
  ao resolver. Mesmo padrão com que já lê `code_curation`/timeline.

### 4. Termo novo no fusor — `concept_resolver.py`
- `resolve_material_assignment(..., lessons_index: Optional[dict] = None)` (assinatura
  `:203`, kwarg novo, default None = byte-idêntico quando ausente).
- Por bloco, dentro do loop `:268-287`:
  - `block_lesson_text` = concat de `lessons_index["by_date"][d]` para `d` em
    `[period_start, period_end]` do bloco (bounds via `_block_period_bounds`,
    `file_map.py:1025`, já existe).
  - `lesson_vec = concept_vector(block_lesson_text, weights, normalize=norm)`.
  - `lesson_overlap = sum(min(entry_vec[t], lesson_vec[t]) for t in entry_vec & lesson_vec)`.
  - `lesson_term = LESSON_CONCEPT_FRAC * lesson_overlap` — peso capado novo (constante
    perto de `SECTION_CONCEPT_FRAC`, `:48`). Calibrar por PRINCÍPIO no golden real,
    NÃO overfitar ao MF (mesma disciplina da Fase 2.2).
  - somar `lesson_term` em `fused` (`:281-287`) e expor `"lesson": round(lesson_term,4)`
    no breakdown (`:288-296`).
- Discrimina bloco-fino: cada bloco do card pega só as lessons da SUA janela; o
  material casa o tópico da aula certa. Sem `lessons_index` → termo 0 → idêntico a hoje.

### 5. Doc vivo — `docs/Overview-Sistema.html`
- §5 (sinais): mover `lessons[].text` de "descartado" para sinal ativo (atrás da flag).

## Degradação honesta (invariantes)
- `lessons_index` ausente/vazio (4 cursos sem re-import, formato D/E) → `lesson_term=0`
  → comportamento idêntico ao atual. Nunca load-bearing.
- Peso capado (`LESSON_CONCEPT_FRAC`) → anti-envenenamento por label ruim.
- Conflito bloco-unit×tópico-unit (`:326`) e band-cap 0.45 continuam valendo: label
  que briga com os outros sinais vira band baixa + flag, não erro confiante.

## Eval-gate (obrigatório, antes de cutover)
- `python -m pytest tests -q` verde (atual 1442).
- Golden PDF `python scripts/eval_assignments.py` = **5/5, confiante-errado 0** (invariante).
- Gold de código `python scripts/eval_code_block_gold.py <MF>` — **resolver_acc ≥ 64.7%
  (baseline travado) E confiante-errado ≤ 1**; alvo: subir (esperado ~14/17).
- `python scripts/rebuild_diff.py` 5 cursos — diffs explicáveis; sinal que melhora MF
  mas regride outro curso NÃO entra.
- Flag `use_concept_resolver` continua controlando o caminho (OFF = produção intacta).

## Ordem TDD
1. `build_lesson_topic_index` puro + testes (formato A com 14 lessons → 14 datas;
   formato D/E → `{}`; colisão de data → último/merge). Sintético, hermético.
2. Termo `lesson_term` no resolver + teste de unidade (com/sem `lessons_index`;
   ausente = breakdown idêntico; presente = bloco certo do card multi-bloco vence).
3. Persistência no import + load no `resolver_apply` (teste com tmp `.lessons_index.json`).
4. Calibrar `LESSON_CONCEPT_FRAC` no golden; rodar todos os gates; medir gold do MF.
5. Atualizar Overview §5.

## Pontos abertos (decidir ao codar)
- `LESSON_CONCEPT_FRAC` inicial: tracejar no golden (provável 0.5-0.7 de W_CONCEPT;
  forte o bastante p/ discriminar dentro do card, fraco p/ não dominar o voto LLM).
- Colisão de datas no índice (2 lessons mesma data): concatenar texto (não perder).
- Re-import dos outros 4 cursos: fora de escopo desta alavanca (só MF mede agora);
  os 4 degradam honestamente até serem re-importados.
- Material-date precision (casar a data do PRÓPRIO material a uma lesson) encosta na
  alavanca 3 (posting_date) — fora de escopo; o overlap de tópico já fixa os 3 erros.
