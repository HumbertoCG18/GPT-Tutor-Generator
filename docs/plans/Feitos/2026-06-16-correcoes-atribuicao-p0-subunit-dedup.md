# Correções de atribuição — P0 (subunit fonte-única + dedup id) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar o "8º segundo cérebro" da subunidade (fonte única + leitura coerente entre FILE_MAP e editor), restringir a subunidade à unidade do bloco, e fechar a duplicação de id no build batch — sem regredir o golden de bloco.

**Architecture:** Três correções estruturais do subsistema de atribuição. (1) `computed_subunit_slug` vira campo first-class de `FileEntry` e o FILE_MAP passa a ler a tag gated `subunit:` (não o best-effort ungated), igualando-se ao editor. (2) o scorer de subunidade recebe a unidade resolvida da entry como restrição (`winning_unit_slug`), exigindo reordenar unit-match antes de subunit-match. (3) o dedup de id do caminho single-entry é extraído num helper e aplicado nos dois laços de build batch.

**Tech Stack:** Python 3, pytest. Sem libs novas. Comando de teste: `python -m pytest tests -q`.

**Escopo:** Este plano cobre P0.4, P0.1 e P0.2 do spec `docs/superpowers/specs/2026-06-16-correcoes-atribuicao-wave-1-2-design.md`. **P0.3/D1** (Gemini código→bloco fonte-única) é refator cross-file complexo e ganha plano próprio em seguida. P1/P2/P3 ganham plano no início de cada fase (eval-gated, dependem do baseline pós-P0).

**Constraint (toda task):** após cada task, `python -m pytest tests -q` verde. As tasks que mudam atribuição real (P0.2) são eval-gated: rodar o golden de bloco e o censo de bands de subunit no repo real antes de considerar a fase fechada (ver "Eval-gate da fase" no fim).

---

## File Structure

- `src/builder/ops/lifecycle_ops.py` — **Modify**: novo helper público `assign_dedup_id(entry, existing_ids)` ao lado do `_dedup_entry_id` existente.
- `src/builder/ops/build_workflow.py` — **Modify**: chamar `assign_dedup_id` no laço de build completo antes de `_process_entry`.
- `src/builder/ops/incremental_build.py` — **Modify**: idem no laço incremental, semeando `existing_ids` do manifest.
- `src/models/core.py` — **Modify**: declarar `computed_subunit_slug: str = ""` em `FileEntry`.
- `src/builder/artifacts/navigation.py` — **Modify**: helper `_display_subunit_slug(entry)` (manual > tag gated) e usá-lo no render do FILE_MAP.
- `src/builder/extraction/content_taxonomy.py` — **Modify**: reordenar unit-match antes de subunit-match e passar `winning_unit_slug` ao `auto_map_entry_subtopic_fn`.
- `tests/test_dedup_entry_id_batch.py` — **Create**: testa `assign_dedup_id`.
- `tests/test_fileentry_roundtrip.py` — **Modify**: cobre `computed_subunit_slug` no round-trip.
- `tests/test_filemap_subunit_display.py` — **Create**: testa `_display_subunit_slug`.
- `tests/test_resolve_unit_block_tags.py` — **Modify**: testa o wiring de `winning_unit_slug` e atualiza os stubs existentes para aceitar o kwarg.

---

## Task 1: P0.4 — Dedup de id no build batch

**Files:**
- Modify: `src/builder/ops/lifecycle_ops.py` (após `_dedup_entry_id`, linhas 15-29)
- Modify: `src/builder/ops/build_workflow.py:54-65`
- Modify: `src/builder/ops/incremental_build.py:28-46`
- Test: `tests/test_dedup_entry_id_batch.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_dedup_entry_id_batch.py`:

```python
from src.models.core import FileEntry
from src.builder.ops.lifecycle_ops import assign_dedup_id


def _entry(source_path: str, category: str) -> FileEntry:
    return FileEntry.from_dict({
        "title": source_path,
        "source_path": source_path,
        "file_type": "pdf",
        "category": category,
    })


def test_assign_dedup_id_first_use_keeps_base_id():
    existing = set()
    e = _entry("trabalhos/introducao.pdf", "trabalhos")
    assert assign_dedup_id(e, existing) == "introducao"
    assert e.id_override == ""
    assert "introducao" in existing


def test_assign_dedup_id_collision_suffixes_category():
    existing = set()
    e1 = _entry("trabalhos/introducao.pdf", "trabalhos")
    e2 = _entry("codigo/introducao.zip", "codigo-professor")
    assert assign_dedup_id(e1, existing) == "introducao"
    assert assign_dedup_id(e2, existing) == "introducao-codigo-professor"
    assert e2.id_override == "introducao-codigo-professor"
    assert e2.id() == "introducao-codigo-professor"
```

- [ ] **Step 2: Rodar o teste pra confirmar que falha**

Run: `python -m pytest tests/test_dedup_entry_id_batch.py -q`
Expected: FAIL com `ImportError: cannot import name 'assign_dedup_id'`.

- [ ] **Step 3: Implementar o helper**

Em `src/builder/ops/lifecycle_ops.py`, logo após `_dedup_entry_id` (linha 29), adicionar:

```python
def assign_dedup_id(entry, existing_ids: set) -> str:
    """Dedup de id para os laços de build BATCH (espelha o caminho single-entry).

    Se o id base do entry colide com um já presente em existing_ids, seta
    entry.id_override (sufixo de categoria / contador via _dedup_entry_id) para
    que TODO o pipeline use o id final. Registra o id final em existing_ids e o
    retorna. Sem colisão, mantém o id base e não toca id_override.
    """
    base_id = entry.id()
    final_id = base_id
    if base_id in existing_ids:
        final_id = _dedup_entry_id(base_id, entry.category, existing_ids)
        entry.id_override = final_id
    existing_ids.add(final_id)
    return final_id
```

- [ ] **Step 4: Rodar o teste pra confirmar que passa**

Run: `python -m pytest tests/test_dedup_entry_id_batch.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Ligar no build completo**

Em `src/builder/ops/build_workflow.py`, no laço que começa em `for i, entry in enumerate(active_entries):` (linha 59). Antes do laço, inicializar o set; dentro, chamar o dedup antes de `_process_entry`:

```python
    total = len(active_entries)
    existing_ids: set = set()
    for i, entry in enumerate(active_entries):
        logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
        if builder.progress_callback:
            builder.progress_callback(i, total, entry.title)
        assign_dedup_id(entry, existing_ids)
        try:
            item_result = builder._process_entry(entry)
            manifest["entries"].append(item_result)
```

Adicionar o import no topo de `build_workflow.py` (junto aos imports existentes):

```python
from src.builder.ops.lifecycle_ops import assign_dedup_id
```

- [ ] **Step 6: Ligar no incremental**

Em `src/builder/ops/incremental_build.py`, no bloco `else:` que processa `new_entries` (a partir da linha 33). Semear `existing_ids` com os ids do manifest existente e dedupar dentro do laço:

```python
        total = len(new_entries)
        existing_ids = {
            str(e.get("id") or "")
            for e in manifest.get("entries", [])
            if e.get("id")
        }
        for i, entry in enumerate(new_entries):
            logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
            if builder.progress_callback:
                builder.progress_callback(i, total, entry.title)
            assign_dedup_id(entry, existing_ids)
            try:
                item_result = builder._process_entry(entry)
                manifest["entries"].append(item_result)
```

Adicionar o import no topo de `incremental_build.py`:

```python
from src.builder.ops.lifecycle_ops import assign_dedup_id
```

- [ ] **Step 7: Rodar a suíte inteira**

Run: `python -m pytest tests -q`
Expected: PASS (suíte verde; nenhuma regressão).

- [ ] **Step 8: Commit**

```bash
git add src/builder/ops/lifecycle_ops.py src/builder/ops/build_workflow.py src/builder/ops/incremental_build.py tests/test_dedup_entry_id_batch.py
git commit -m "fix(dedup): id unico no build batch (fix c) - assign_dedup_id em build_workflow/incremental"
```

---

## Task 2: P0.1a — `computed_subunit_slug` vira campo de FileEntry

**Files:**
- Modify: `src/models/core.py:81` (bloco de campos `computed_*`)
- Test: `tests/test_fileentry_roundtrip.py` (modificar)

- [ ] **Step 1: Escrever o teste que falha**

Em `tests/test_fileentry_roundtrip.py`, adicionar `computed_subunit_slug` ao `_make_entry_dict` e à tupla de campos persistidos. Editar:

```python
_PERSISTED_ENTRY_FIELDS = (
    "manual_subunit_slug",
    "unit_match_confidence",
    "unit_match_reasons",
    "subunit_match_confidence",
    "subunit_match_reasons",
    "computed_subunit_slug",
)
```

e no `_make_entry_dict`, adicionar a chave:

```python
        "subunit_match_reasons": ["topic_overlap"],
        "computed_subunit_slug": "subunidade-02-inducao",
    }
```

- [ ] **Step 2: Rodar o teste pra confirmar que falha**

Run: `python -m pytest tests/test_fileentry_roundtrip.py::test_fileentry_roundtrip_preserves_persisted_match_fields -q`
Expected: FAIL com `campo 'computed_subunit_slug' sumiu no round-trip` (o campo não é declarado em FileEntry, então `from_dict` o descarta).

- [ ] **Step 3: Declarar o campo em FileEntry**

Em `src/models/core.py`, logo após `computed_unit_slug: str = ""` (linha 81), adicionar:

```python
    computed_unit_slug: str = ""
    # Melhor candidato de subunidade (best-effort, pode estar abaixo do gate de
    # tag). Declarado aqui para sobreviver ao round-trip from_dict -> to_dict
    # (antes era descartado, deixando subunit_match_confidence orfa). A tag
    # subunit: (gated) continua sendo a atribuicao; este campo e a sugestao.
    computed_subunit_slug: str = ""
    computed_block_id: str = ""
```

- [ ] **Step 4: Rodar o teste pra confirmar que passa**

Run: `python -m pytest tests/test_fileentry_roundtrip.py -q`
Expected: PASS.

- [ ] **Step 5: Rodar a suíte inteira**

Run: `python -m pytest tests -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/models/core.py tests/test_fileentry_roundtrip.py
git commit -m "fix(subunit): computed_subunit_slug vira campo de FileEntry (sobrevive round-trip)"
```

---

## Task 3: P0.1b — FILE_MAP lê a tag gated, não o best-effort ungated

**Files:**
- Modify: `src/builder/artifacts/navigation.py:623-626`
- Test: `tests/test_filemap_subunit_display.py` (criar)

Contexto: o editor (`dialogs.py:4154-4175`) já lê na ordem correta (manual > tag `subunit:` gated > computed best-effort rotulado "Sugestão baixa confiança"). O FILE_MAP (`navigation.py:623-626`) lê `manual > computed` direto, **pulando a tag** — exibe o best-effort ungated como se fosse atribuição. Fix: ler a tag gated, sem fallback pro computed (FILE_MAP só mostra atribuições reais).

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_filemap_subunit_display.py`:

```python
from src.builder.artifacts.navigation import _display_subunit_slug


def test_manual_subunit_wins():
    entry = {
        "manual_subunit_slug": "sub-manual",
        "auto_tags": ["subunit:sub-auto"],
        "computed_subunit_slug": "sub-computed",
    }
    assert _display_subunit_slug(entry) == "sub-manual"


def test_gated_tag_used_when_no_manual():
    entry = {
        "auto_tags": ["unit:u1", "subunit:sub-auto", "bloco:bloco-01"],
        "computed_subunit_slug": "sub-computed",
    }
    assert _display_subunit_slug(entry) == "sub-auto"


def test_ungated_computed_is_not_surfaced():
    # Sem tag subunit: (nao passou no gate) -> FILE_MAP NAO mostra o best-effort.
    entry = {
        "auto_tags": ["unit:u1"],
        "computed_subunit_slug": "sub-computed",
    }
    assert _display_subunit_slug(entry) == ""


def test_empty_when_nothing():
    assert _display_subunit_slug({}) == ""
```

- [ ] **Step 2: Rodar o teste pra confirmar que falha**

Run: `python -m pytest tests/test_filemap_subunit_display.py -q`
Expected: FAIL com `ImportError: cannot import name '_display_subunit_slug'`.

- [ ] **Step 3: Implementar o helper e usá-lo no render**

Em `src/builder/artifacts/navigation.py`, adicionar o helper (perto do topo do módulo, junto aos outros helpers de módulo):

```python
def _display_subunit_slug(entry: dict) -> str:
    """Subunidade exibida no FILE_MAP: manual > tag gated `subunit:`.

    NAO cai no computed_subunit_slug (best-effort ungated) — o FILE_MAP so
    mostra atribuicoes reais (igual ao tier 'Automatico' do editor). O
    best-effort fica so no editor, rotulado como sugestao.
    """
    manual = str(entry.get("manual_subunit_slug") or "").strip()
    if manual:
        return manual
    for tag in entry.get("auto_tags") or []:
        if tag.startswith("subunit:"):
            return tag[len("subunit:"):]
    return ""
```

Depois, no render (linhas 623-626), trocar:

```python
            preferred_topic_slug = (
                str(entry.get("manual_subunit_slug") or "").strip()
                or str(entry.get("computed_subunit_slug") or "").strip()
            )
```

por:

```python
            preferred_topic_slug = _display_subunit_slug(entry)
```

- [ ] **Step 4: Rodar o teste pra confirmar que passa**

Run: `python -m pytest tests/test_filemap_subunit_display.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Rodar a suíte inteira**

Run: `python -m pytest tests -q`
Expected: PASS. (Se algum teste de FILE_MAP esperava o computed ungated na coluna de subtópico, atualizar pra esperar a tag gated — é a correção pretendida; documentar no commit.)

- [ ] **Step 6: Commit**

```bash
git add src/builder/artifacts/navigation.py tests/test_filemap_subunit_display.py
git commit -m "fix(subunit): FILE_MAP le tag subunit: gated (nao o best-effort ungated) - coerente com editor"
```

---

## Task 4: P0.2 — Subunidade restrita à unidade do bloco (`winning_unit_slug`)

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py:1079-1118` (reordenar unit-match antes de subunit-match + passar `winning_unit_slug`)
- Test: `tests/test_resolve_unit_block_tags.py` (adicionar teste + atualizar stubs existentes)

Contexto: `auto_map_entry_subtopic` (file_map.py:166) já tem o parâmetro `winning_unit_slug` que filtra os tópicos à unidade, mas nenhum caller o passa. Hoje o caller (content_taxonomy.py:1087) roda o subunit-match ANTES do unit-match, então a unidade resolvida não está disponível. Fix: reordenar e passar.

- [ ] **Step 1: Atualizar os stubs existentes (pré-requisito — senão a mudança quebra os testes atuais)**

Em `tests/test_resolve_unit_block_tags.py`, TODOS os stubs `auto_map_entry_subtopic_fn=lambda e, t, m: ...` passam a aceitar o kwarg. Substituir cada ocorrência de:

```python
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
```

por:

```python
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
```

(usar replace-all no arquivo; aplicar a mesma transformação a qualquer variante que retorne `_stub_topic_match(...)` com argumentos).

- [ ] **Step 2: Escrever o teste que falha (wiring do winning_unit_slug)**

Adicionar ao fim de `tests/test_resolve_unit_block_tags.py`:

```python
def test_subtopic_matcher_receives_resolved_unit_as_winning_unit_slug():
    captured = {}

    def _capture_subtopic(e, t, m, winning_unit_slug=""):
        captured["winning_unit_slug"] = winning_unit_slug
        return _stub_topic_match()

    resolve_unit_block_tags(
        [_make_minimal_entry("e1", "Slides")],
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=_capture_subtopic,
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    assert captured["winning_unit_slug"] == "unidade-02"
```

- [ ] **Step 3: Rodar o teste pra confirmar que falha**

Run: `python -m pytest tests/test_resolve_unit_block_tags.py::test_subtopic_matcher_receives_resolved_unit_as_winning_unit_slug -q`
Expected: FAIL — `captured["winning_unit_slug"]` é `""` (o caller ainda não passa o kwarg), ou KeyError se o subunit-match roda antes do unit-match.

- [ ] **Step 4: Reordenar unit-match antes de subunit-match e passar o kwarg**

Em `src/builder/extraction/content_taxonomy.py`, mover o bloco `--- Unit match (manual tem precedencia) ---` (linhas 1102-1118) para ANTES do bloco `--- Topic/subunit match (manual tem precedencia) ---` (linha 1079). O bloco de unit-match não usa `preferred_topic_slug` nem nada do subunit, então a reordenação é segura. Resultado (ordem nova):

```python
        # --- Unit match (manual tem precedencia) ---
        manual_unit = _collapse_ws(str(entry.get("manual_unit_slug") or ""))
        if manual_unit:
            resolved_unit_slug = manual_unit
            unit_confidence = 1.0
            unit_ambiguous = False
            unit_reasons = ["manual"]
        else:
            _learned_boosts = build_learned_unit_boosts(_tag_profile, entry) if _tag_profile else {}
            unit_match = auto_map_entry_unit_fn(
                entry, unit_index, markdown_text, topic_index,
                learned_unit_boosts=_learned_boosts,
            )
            resolved_unit_slug = unit_match.slug
            unit_confidence = unit_match.confidence
            unit_ambiguous = unit_match.ambiguous
            unit_reasons = list(unit_match.reasons)

        # --- Topic/subunit match (manual tem precedencia) ---
        manual_subunit = _collapse_ws(str(entry.get("manual_subunit_slug") or ""))
        if manual_subunit:
            preferred_topic_slug = manual_subunit
            subunit_reasons = ["manual"]
            subunit_confidence = 1.0
            best_subunit_slug = manual_subunit
        else:
            topic_match = auto_map_entry_subtopic_fn(
                entry, content_taxonomy, subunit_markdown_text,
                winning_unit_slug=resolved_unit_slug,
            )
            preferred_topic_slug = ""
            subunit_reasons = list(getattr(topic_match, "reasons", []))
            subunit_confidence = float(getattr(topic_match, "confidence", 0.0))
            best_subunit_slug = str(getattr(topic_match, "topic_slug", "") or "")
            if (
                topic_match.topic_slug
                and not topic_match.ambiguous
                and topic_match.confidence >= T.SUBUNIT_TAG
            ):
                preferred_topic_slug = topic_match.topic_slug
```

(O bloco `--- Block match: DESACOPLADO da unidade ---` na linha 1120 fica logo depois, inalterado — ele usa `resolved_unit_slug` e `preferred_topic_slug`, ambos já definidos acima.)

- [ ] **Step 5: Rodar o teste pra confirmar que passa**

Run: `python -m pytest tests/test_resolve_unit_block_tags.py -q`
Expected: PASS (o novo teste + todos os existentes com os stubs atualizados).

- [ ] **Step 6: Rodar a suíte inteira**

Run: `python -m pytest tests -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/builder/extraction/content_taxonomy.py tests/test_resolve_unit_block_tags.py
git commit -m "fix(subunit): restringe subunidade a unidade resolvida (winning_unit_slug) - reordena unit antes de subunit"
```

---

## Eval-gate da fase (antes de considerar P0 fechado)

P0.2 (e, em menor grau, P0.1b) muda atribuição/exibição real. Rodar antes de mergear a fase:

- [ ] **Golden de bloco:** `python scripts/eval_assignments.py` (ou o harness do golden). Critério: **41/48, confiante-errado 0** mantido (P0 não deve regredir o bloco — só toca subunit/exibição/id).
- [ ] **Censo de bands de subunit no repo real:** retag/reprocesso do Metodos-Formais-Tutor e conferir a distribuição de bands de subunit antes×depois. Esperado: subunidades agora restritas à unidade do bloco (some o desalinhamento subunit↛unit); FILE_MAP deixa de exibir best-effort ungated. Registrar os números no plano-mestre (seção da auditoria).
- [ ] Se a restrição por unidade de baixa confiança piorar o censo, gatear `winning_unit_slug` por `unit_confidence` (passar só quando não-ambíguo) — follow-up eval-gated.

---

## Self-Review

**Spec coverage:** P0.4 (Task 1), P0.1a (Task 2), P0.1b (Task 3), P0.2 (Task 4) — todos os itens P0 do spec exceto P0.3/D1 (plano próprio, declarado no Escopo). ✓

**Placeholder scan:** sem TBD/TODO; todo step tem código ou comando concreto. ✓

**Type consistency:** `assign_dedup_id(entry, existing_ids)` — mesma assinatura em lifecycle_ops, build_workflow, incremental_build. `_display_subunit_slug(entry)` — mesma em navigation e teste. `winning_unit_slug` kwarg — mesmo nome no helper (file_map.py:166), no caller (content_taxonomy) e nos stubs de teste. `computed_subunit_slug` — mesmo nome em core.py, dialogs (leitor existente), navigation (não usa mais), round-trip. ✓

**Dependência de ordem:** Task 4 exige que os stubs de `test_resolve_unit_block_tags.py` aceitem `winning_unit_slug=""` (Step 1) ANTES da mudança do caller (Step 4) — capturado como primeiro step da task.
