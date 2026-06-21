# Degrau 3a — Alavanca 0: sinal `lessons[].text` (data→tópico) no fusor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar um termo de fusão `lesson_term` ao `concept_resolver` que casa a identidade LIMPA do material (`moodle_label` + título) contra o tópico da aula daquele dia (`lessons[].text`, o "resumo da semana" do professor, indexado por data) — re-introduzindo o sinal data→tópico que foi revertido, agora que o `moodle_label` (Alavanca 1) está ativo e dá a identidade limpa que faltava.

**Architecture:** O índice `.lessons_index.json` (`{version, by_date:{ISO_date: tópico}}`) já é capturado no import (`build_lesson_topic_index`, `moodle_labels.py:254`) e carregado por `load_lessons_index` (`resolver_apply.py:27`) — hoje DORMENTE (definido, não chamado). Esta alavanca: (1) `apply_concept_resolver` carrega o índice e o passa ao resolver; (2) `resolve_material_assignment` ganha um termo `lesson_term` CAPADO que, por bloco candidato, casa os tokens do sinal limpo do material (`moodle_label_text` + `title_text`, **NÃO** markdown/concepts ruidosos — essa foi a causa do revert anterior) contra os tokens do tópico das sessões daquele bloco (via `by_date[session.date]`). Tudo atrás da flag `use_concept_resolver` (default OFF) → produção byte-idêntica.

**Tech Stack:** Python 3.13, pytest. Módulos: `src/builder/routing/concept_resolver.py`, `src/builder/routing/resolver_apply.py`. Gate: `scripts/eval_assignments.py`, `scripts/eval_code_block_gold.py`, `scripts/compare_resolver.py`, `scripts/rebuild_diff.py`.

## Global Constraints

- **Flag-OFF byte-idêntico** — toda a mudança vive no caminho do `concept_resolver` (`use_concept_resolver`, default OFF). Com a flag OFF, produção inalterada. Invariante verificável: golden 5/5 cw0 com flag OFF.
- **Casar só o sinal LIMPO** — `lesson_term` casa `moodle_label_text` + `title_text` contra o tópico da lesson. **NUNCA** markdown nem `concepts` do Gemini (o termo anterior foi revertido justamente por casar contra concepts ruidosos → regrediu gold 11→10). Esta é a diferença que torna a re-introdução viável.
- **Teto de peso (anti-envenenamento)** — `lesson_term` tem `W_LESSON` e um cap de overlap; um sinal de lesson ruim nunca domina o conceito/LLM, só desempata/reforça. Spec signal-registry §"Contrato de degradação honesta".
- **Degradação honesta** — `.lessons_index.json` ausente/`by_date` vazio → `lesson_term = 0.0` para todo bloco (skip honesto). Curso sem resumo-da-semana funciona, sem o reforço.
- **Não tocar GOLDEN nem o funil** — `assign_units_positional`, `_build_timeline_index`, review rule intocados; o funil legado NÃO é alterado (será deletado na Fase 3.4 pós-gate).
- **Eval-gate cross-curso obrigatório** (spec signal-registry §Eval-gate): golden PDF 5/5 cw0; gold de código resolver ≥ funil e cw ≤ funil; `rebuild_diff` explicável (pista que melhora MF mas regride outro curso NÃO entra); suíte verde.
- **`by_date` chaveia por data ISO `YYYY-MM-DD`**; `block.sessions[].date` é ISO (`_extract_block_sessions`). Match por igualdade de data.

---

### Task 1: `lesson_term` capado no fusor + wire do índice

**Files:**
- Modify: `src/builder/routing/concept_resolver.py` (constantes `W_LESSON`/`LESSON_OVERLAP_CAP`; função `score_lesson_match`; parâmetro `lessons_index` em `resolve_material_assignment`; termo no `fused` e no breakdown)
- Modify: `src/builder/routing/resolver_apply.py` (`apply_concept_resolver` carrega `load_lessons_index(root)` e passa ao resolver)
- Test: `tests/test_lesson_signal.py` (criar)

**Interfaces:**
- Consumes: `_concept_tokens(text, normalize) -> set` (`concept_resolver.py:90`); `signals` dict com `moodle_label_text` e `title_text` (de `collect_entry_unit_signals`); `lessons_index = {"version":int, "by_date":{date_iso: topic_str}}` (de `build_lesson_topic_index`/`load_lessons_index`); `block.sessions[]` com `date` ISO.
- Produces: `score_lesson_match(signals, block, lessons_index, normalize) -> float`; `resolve_material_assignment(entry, blocks, units, *, signals, llm_curation=None, lessons_index=None) -> Assignment` (novo kwarg opcional `lessons_index`, default None → termo 0.0; assinatura retro-compatível).

Contexto (a fórmula de fusão atual, `concept_resolver.py:300-315`):
```python
        fused = (
            W_CONCEPT * overlap
            + W_LLM * llm_term
            + date_term
            + seq_term
            + card_term
        )
        scored.append((block, fused, {
            "concept": round(overlap, 4),
            "llm": round(llm_term, 4),
            "date": round(date_term, 4),
            "sequence": round(seq_term, 4),
            "card": round(card_term, 4),
            "fused": round(fused, 4),
            "authoritative_card": card_term >= CARD_AUTHORITATIVE,
        }))
```

- [ ] **Step 1: Escrever os testes que falham**

Crie `tests/test_lesson_signal.py`:

```python
from src.builder.routing.concept_resolver import (
    score_lesson_match,
    resolve_material_assignment,
    W_LESSON,
)
from src.builder.text.normalize import normalize_match_text


_LESSONS = {"version": 1, "by_date": {
    "2026-04-27": "Lógica de Hoare",
    "2026-04-29": "Lógica de Hoare",
    "2026-05-13": "Programas em Dafny",
}}


def _block(bid, unit, dates):
    return {
        "id": bid, "unit_slug": unit, "primary_topic_label": "", "topics": [],
        "sessions": [{"id": f"{bid}-{d}", "date": d, "kind": "class", "label": "", "signals": []} for d in dates],
        "card_evidence": [],
    }


def test_lesson_match_uses_clean_label_against_block_lesson_topics():
    block = _block("bloco-10", "u-verif", ["2026-04-27", "2026-04-29"])
    # sinal LIMPO do material casa o tópico da aula daquele bloco
    signals = {"moodle_label_text": "logica de hoare parte 2", "title_text": "LogicaDeHoare2"}
    score = score_lesson_match(signals, block, _LESSONS, normalize_match_text)
    assert score > 0.0


def test_lesson_match_ignores_markdown_and_concepts():
    block = _block("bloco-10", "u-verif", ["2026-04-27"])
    # sem label/título limpos; só markdown ruidoso não deve casar a lesson
    signals = {"moodle_label_text": "", "title_text": "", "markdown_text": "logica de hoare hoare hoare"}
    assert score_lesson_match(signals, block, _LESSONS, normalize_match_text) == 0.0


def test_lesson_match_capped():
    # muitas datas com o mesmo tópico não estouram o teto
    block = _block("bloco-10", "u-verif", ["2026-04-27", "2026-04-29"])
    signals = {"moodle_label_text": "logica de hoare", "title_text": "hoare"}
    score = score_lesson_match(signals, block, _LESSONS, normalize_match_text)
    assert score <= W_LESSON * 3  # cap de overlap aplicado


def test_lesson_index_absent_scores_zero():
    block = _block("bloco-10", "u-verif", ["2026-04-27"])
    signals = {"moodle_label_text": "logica de hoare", "title_text": "hoare"}
    assert score_lesson_match(signals, block, None, normalize_match_text) == 0.0
    assert score_lesson_match(signals, block, {"by_date": {}}, normalize_match_text) == 0.0


def test_resolver_lesson_term_breaks_tie_toward_lesson_block():
    # 2 blocos sem outro sinal discriminante; a lesson + label limpo decide
    b_hoare = _block("bloco-10", "u-verif", ["2026-04-27", "2026-04-29"])
    b_dafny = _block("bloco-13", "u-verif", ["2026-05-13"])
    entry = {"id": "e1", "file_type": "pdf"}
    signals = {"moodle_label_text": "logica de hoare parte 2", "title_text": "LogicaDeHoare2"}
    a = resolve_material_assignment(entry, [b_dafny, b_hoare], [], signals=signals, lessons_index=_LESSONS)
    assert a["block_id"] == "bloco-10"
    assert a["signals"].get("lesson", 0.0) > 0.0


def test_resolver_without_lessons_index_unchanged_default():
    # lessons_index default None → termo lesson ausente, comportamento atual
    b = _block("bloco-10", "u-verif", ["2026-04-27"])
    entry = {"id": "e1", "file_type": "pdf"}
    a = resolve_material_assignment(entry, [b], [], signals={"title_text": "x"})
    assert a["signals"].get("lesson", 0.0) == 0.0
```

- [ ] **Step 2: Rodar os testes para ver falhar**

Run: `python -m pytest tests/test_lesson_signal.py -v`
Expected: FAIL no import de `score_lesson_match`/`W_LESSON` (não existem) → todos falham no import. RED.

- [ ] **Step 3: Adicionar constantes + `score_lesson_match`**

Em `src/builder/routing/concept_resolver.py`, após a constante `SECTION_CONCEPT_FRAC` (linha 48), adicione:

```python
# Alavanca 0 (lessons[].text): tópico da aula daquele DIA (resumo-da-semana do
# professor, indexado por data) reforça o bloco cujas sessões cobrem essa data.
# Casa SÓ o sinal LIMPO do material (moodle_label + título) — casar contra
# markdown/concepts do Gemini regredia o gold (revert anterior). Capado p/ não
# dominar conceito/LLM (anti-envenenamento).
W_LESSON: float = 0.5
LESSON_OVERLAP_CAP: int = 3
```

E após `_concept_tokens` (linha 95), adicione:

```python
def score_lesson_match(
    signals: dict,
    block: dict,
    lessons_index: Optional[dict],
    normalize: Callable[[str], str],
) -> float:
    """Reforço data→tópico: tokens do tópico das aulas DESTE bloco (via
    lessons_index[session.date]) ∩ tokens do sinal LIMPO do material
    (moodle_label + título). Capado. 0.0 quando o índice falta ou não casa."""
    by_date = (lessons_index or {}).get("by_date") or {}
    if not by_date:
        return 0.0
    lesson_tokens: set = set()
    for session in block.get("sessions") or []:
        topic = by_date.get(str(session.get("date") or ""))
        if topic:
            lesson_tokens |= _concept_tokens(str(topic), normalize)
    if not lesson_tokens:
        return 0.0
    clean = " ".join(p for p in (
        str(signals.get("moodle_label_text", "") or ""),
        str(signals.get("title_text", "") or ""),
    ) if p)
    clean_tokens = _concept_tokens(clean, normalize)
    overlap = len(clean_tokens & lesson_tokens)
    if overlap <= 0:
        return 0.0
    return W_LESSON * float(min(overlap, LESSON_OVERLAP_CAP))
```

- [ ] **Step 4: Adicionar o parâmetro `lessons_index` e o termo na fusão**

Em `resolve_material_assignment` (`concept_resolver.py:218`), altere a assinatura para incluir `lessons_index`:

```python
def resolve_material_assignment(
    entry: dict,
    blocks: List[dict],
    units: List[dict],
    *,
    signals: dict,
    llm_curation: Optional[dict] = None,
    lessons_index: Optional[dict] = None,
) -> Assignment:
```

No loop de scoring, ANTES de `fused = (`, adicione o termo:
```python
        lesson_term = score_lesson_match(signals, block, lessons_index, norm)
```
Inclua-o na soma e no breakdown:
```python
        fused = (
            W_CONCEPT * overlap
            + W_LLM * llm_term
            + date_term
            + seq_term
            + card_term
            + lesson_term
        )
        scored.append((block, fused, {
            "concept": round(overlap, 4),
            "llm": round(llm_term, 4),
            "date": round(date_term, 4),
            "sequence": round(seq_term, 4),
            "card": round(card_term, 4),
            "lesson": round(lesson_term, 4),
            "fused": round(fused, 4),
            "authoritative_card": card_term >= CARD_AUTHORITATIVE,
        }))
```

- [ ] **Step 5: Wire do índice em `apply_concept_resolver`**

Em `src/builder/routing/resolver_apply.py`, em `apply_concept_resolver` (linha 77), após `blocks = annotate_class_ordinals(copy.deepcopy(blocks))` (linha 93), carregue o índice uma vez:
```python
    lessons_index = load_lessons_index(root)
```
E na chamada `resolve_material_assignment(...)` (linha 102), passe o kwarg:
```python
        assignment = resolve_material_assignment(
            entry_for_resolver,
            blocks,
            units,
            signals=signals,
            llm_curation=summary or None,
            lessons_index=lessons_index,
        )
```

- [ ] **Step 6: Rodar os testes para ver passar**

Run: `python -m pytest tests/test_lesson_signal.py -v`
Expected: PASS nos 6 casos.

- [ ] **Step 7: Rodar a suíte do resolver para não-regressão**

Run: `python -m pytest tests/test_resolver_wiring.py -v` (e qualquer `tests/test_*resolver*.py`)
Expected: PASS — o novo kwarg é opcional (default None → termo 0.0); chamadas existentes inalteradas.

- [ ] **Step 8: Commit**

```bash
git add src/builder/routing/concept_resolver.py src/builder/routing/resolver_apply.py tests/test_lesson_signal.py
git commit -m "feat(resolver): alavanca 0 — lesson_term capado (data->topico vs label limpo)"
```

---

### Task 2: Eval-gate cross-curso + calibração de `W_LESSON` (decisiva)

**Files:**
- Possível ajuste: `src/builder/routing/concept_resolver.py` (só `W_LESSON`/`LESSON_OVERLAP_CAP` se a calibração exigir; sem mudança estrutural)
- Sem novo arquivo de produção.

**Interfaces:**
- Consumes: estado pós-Task 1. Gate: `scripts/eval_assignments.py` (golden 5 PDFs MF), `scripts/eval_code_block_gold.py` (gold de código MF), `scripts/compare_resolver.py` (harness), `scripts/rebuild_diff.py` (5 cursos).
- Produces: confirmação de que a alavanca 0 NÃO regride (a tentativa anterior regrediu 11→10; agora com `moodle_label` ativo deve manter/melhorar) e veredito de calibração.

- [ ] **Step 1: Golden PDF (invariante)**

Run: `python scripts/eval_assignments.py` (use a mesma invocação registrada no ledger `.git/sdd/progress.md`; com `--help` se necessário).
Expected: **5/5, confiante-errado 0.** Se regredir → STOP, BLOCKED (o termo ou o teto regridem o golden; reduzir `W_LESSON` ou restringir tokens). Lembrar: o termo lesson SÓ atua no caminho do resolver; o golden roda com a flag conforme o harness — registre qual caminho mede.

- [ ] **Step 2: Gold de código (resolver ≥ funil)**

Run: `python scripts/eval_code_block_gold.py` (mesma invocação do ledger).
Expected: resolver acerta **≥** o funil e confiante-errado **≤** funil. Baseline registrado no ledger: "funil 7/17, resolver 11/17 cw1, subset alta resolver 9/13". A alavanca 0 deve manter ≥11 (idealmente subir — o ledger previu que invariantes/tiposindutivos/exemplos-zip melhoram com o label limpo casando a lesson). Registre o novo placar.

- [ ] **Step 3: Harness compare_resolver + rebuild_diff cross-curso**

Run: `python scripts/compare_resolver.py` e `python scripts/rebuild_diff.py`
Expected: diffs explicáveis; **nenhuma pista que melhora MF mas regride outro curso.** Registre o drift por curso. IA/SO/ES2/TCC sem gold rotulado → confirmar que o drift é explicável (lesson casando label limpo), não ruído. Se um curso regride de forma inexplicável → STOP, BLOCKED.

- [ ] **Step 4: Calibração (se necessário)**

Se o golden passa mas o gold de código não melhora (ou regride no subset alta), ajuste `W_LESSON` (ex.: 0.5→0.35) ou `LESSON_OVERLAP_CAP`, re-rodando Steps 1-3. **Tracejar com as fixtures do golden real, NÃO overfitar ao MF** (mesma disciplina da Fase 2.2). Se nenhum peso passa o gate sem regredir → STOP, BLOCKED (a pista não generaliza ainda; reportar p/ revisão de design).

- [ ] **Step 5: Registrar o resultado do gate**

Anexe a `.git/sdd/task-2-report-d3a.md`: comandos, golden (esperado 5/5), gold de código (placar antes/depois), rebuild_diff por curso, e `W_LESSON`/`cap` finais. Sem commit se não houve ajuste de peso; se houve, commit `tune(resolver): calibra W_LESSON da alavanca 0 (eval-gate)`.

---

## Self-Review

**1. Cobertura (spec signal-registry):**
- "Alavanca 0 — lessons[].text: parser pronto, só falta o consumidor" → Task 1 wira `load_lessons_index` (dormente) + `score_lesson_match`. ✅
- Plug point #2 "novo termo no fusor com TETO de peso" → `W_LESSON*min(overlap, LESSON_OVERLAP_CAP)`, somado ao `fused`. ✅
- "casar contra concepts ruidosos regredia o gold; consumir quando moodle_label der identidade limpa" (`resolver_apply.py:30-34` + revert) → `score_lesson_match` casa SÓ `moodle_label_text`+`title_text`, nunca markdown/concepts. ✅ (testado em `test_lesson_match_ignores_markdown_and_concepts`).
- "degradação honesta: sinal ausente → termo ausente" → índice None/vazio → 0.0. ✅ (`test_lesson_index_absent_scores_zero`).
- Eval-gate cross-curso obrigatório → Task 2 (golden 5/5, gold código resolver≥funil, rebuild_diff explicável). ✅
- Flag-OFF byte-idêntico → toda a mudança no caminho do resolver; kwarg opcional default None. ✅

**2. Placeholder scan:** Task 1 tem código real + 6 testes verbatim. Task 2 nomeia os 4 scripts reais; invocação exata delegada a `--help`/ledger (ferramentas existentes documentadas), com critérios numéricos de aceite explícitos. Sem TODO.

**3. Type consistency:** `score_lesson_match(signals, block, lessons_index, normalize) -> float`; `W_LESSON: float`, `LESSON_OVERLAP_CAP: int`; novo kwarg `lessons_index: Optional[dict] = None`. `_concept_tokens` reusado. Breakdown ganha chave `"lesson"`. Consistente entre Task 1 (define) e os testes (consomem `a["signals"]["lesson"]`).

**Nota empírica (honesta):** a tentativa anterior do termo lesson regrediu o gold (11→10). A diferença agora é casar o sinal LIMPO (`moodle_label`, ativo desde a Alavanca 1) em vez dos concepts ruidosos. Se o eval-gate (Task 2) ainda regredir com qualquer peso, a alavanca NÃO entra (spec: "pista que regride NÃO entra") — Task 2 é a árbitra, não Task 1.
