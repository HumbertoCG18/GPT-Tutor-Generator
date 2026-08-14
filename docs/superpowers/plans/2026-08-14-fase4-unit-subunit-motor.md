# Fase 4 — unit/subunit no motor novo (campanha 3 cutover) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sob `use_concept_resolver=True`, o caminho do motor passa a produzir TODOS os campos de unidade/subunidade que a UI lê (hoje 100% do legado `resolve_unit_block_tags`), reconciliados contra o bloco NOVO do motor — destravando o flip (Fase 3.4) e a deleção do funil (F5).

**Architecture:** Nova função `apply_unit_subunit_fields` em `src/builder/routing/resolver_apply.py`, mesma mecânica de injeção de dependências do legado (engine monta `partial` com os aliases já wireados; scorers de unidade/subunidade SOBREVIVEM ao cutover — só a orquestração muda de dono). Chamada em `pedagogical_regeneration` imediatamente após `apply_concept_resolver`, sob a MESMA flag. Reconciliação roda contra o bloco que o motor acabou de gravar — o achado 1.2 (gap de reconciliação) fica consertado por construção no caminho unit.

**Tech Stack:** Python 3, pytest. Sem dependências novas.

**Spec:** `docs/reports/2026-08-14-auditoria-enxame.md` §1 (achados 1.1/1.2, contrato + file:line) + `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` §7-8 + `docs/reports/2026-08-14-handoff-campanha3-cutover.md` (ordem da campanha).

## Global Constraints

- `engine.py` é façade: lógica nova vai em subpacote (routing); engine só WIREIA (partial), como já faz em `engine.py:2147-2157`.
- Imports vêm de submódulos focados, nunca de `engine.py`.
- Flag `use_concept_resolver` está OFF em produção: com flag OFF o build DEVE permanecer byte-idêntico (gate da fase).
- A tag `bloco:` permanece DISPLAY (`bloco-NN`), nunca uuid (`file_map.py:506` parseia `bloco-(\d+)`). Tags `unit:`/`subunit:` seguem os gates do legado: `unit:` conf ≥ `T.UNIT_TAG` (0.65) e não-ambíguo; `subunit:` conf ≥ `T.SUBUNIT_TAG` (0.60) e não-ambíguo, restrita à unidade vencedora.
- `manual_unit_slug`/`manual_subunit_slug`/bloco manual têm precedência absoluta (conf 1.0), como no legado.
- Não tocar: `resolve_unit_block_tags` (morre só na F5), `attach_block_summary_fields` (achado 1.3 = passo 2 da campanha, fora deste plano), símbolos condenados da lista nomeada.
- Gates da fase (handoff): suite verde + régua MF ≥ 50/57 + sentinelas casos-chave com diff ZERO (flag OFF — nada pode mudar) + `rebuild_diff` 0.
- Comandos: `python -m pytest tests -q` (suite), `python scripts/eval_ground_truth.py ..\Metodos-Formais-Tutor tests\fixtures\eval\ground_truth_MF.csv` (régua MF).

## Contrato a reproduzir (fonte: `content_taxonomy.py:1336-1429`, leitores da UI)

Campos por entry que o motor passa a escrever (leitores entre parênteses):
- `computed_unit_slug` — gated + reconciliado (navigation.py:643, dialogs.py:2487/3336/4108)
- `unit_match_reasons` — lista + sufixos do reconcile `unidade_do_bloco_manual` / `herdada_do_bloco=<id>` / `reconciliada_do_bloco=<id>` (dialogs.py:3348/4113)
- `unit_match_confidence` (timeline_dashboard.py:828, dialogs.py:3349)
- `unit_block_conflict` — `{}` ou `{unit, block_unit, block_id}` (dialogs.py:4114)
- `computed_subunit_slug` — best-effort SEM gate + `subunit_match_reasons` + `subunit_match_confidence`
- `auto_tags`: espelhos `unit:<slug>` / `subunit:<slug>` (gated), preservando tags de outros prefixos

---

### Task 1: `apply_unit_subunit_fields` — caminho de UNIDADE + reconcile

**Files:**
- Modify: `src/builder/routing/resolver_apply.py` (nova função ao fim do arquivo)
- Test: `tests/test_resolver_apply_units.py` (novo)

**Interfaces:**
- Produces: `apply_unit_subunit_fields(entries, blocks, course_meta, subject_profile, root, code_curation, *, auto_map_entry_unit_fn, auto_map_entry_subtopic_fn, build_file_map_unit_index_from_course_fn, iter_content_taxonomy_topics_fn, entry_markdown_text_for_file_map_fn) -> list` — muta entries in-place (mesma convenção de `apply_concept_resolver`), devolve a lista.
- Consumes: `reconcile_unit_with_block` (`file_map.py:651`, kwargs-only), `T.UNIT_TAG` (`thresholds.py:137`), `load_tag_profile`/`build_learned_unit_boosts` (`src/models/tag_profile.py`), `_is_material` (já em resolver_apply.py:39).

- [x] **Step 1: Escrever o teste que falha** — `tests/test_resolver_apply_units.py`. Fixtures mínimas no padrão de `tests/test_reconcile_unit_block.py` (dicts crus). Stub de `auto_map_entry_unit_fn` devolve um objeto com `.slug/.confidence/.ambiguous/.reasons` (usar `types.SimpleNamespace`).

```python
from types import SimpleNamespace

from src.builder.routing.resolver_apply import apply_unit_subunit_fields

BLOCKS = [
    {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1"},
    {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "u2"},
]

def _entry(**kw):
    e = {"id": "e1", "file_type": "pdf", "computed_block_id": "u-2",
         "computed_block_confidence": 0.8, "computed_block_method": "concept-fused",
         "auto_tags": ["unit:velha", "outra:tag"]}
    e.update(kw)
    return e

def _fns(unit_match):
    return dict(
        auto_map_entry_unit_fn=lambda e, ui, md, ti, learned_unit_boosts=None: unit_match,
        auto_map_entry_subtopic_fn=lambda e, tax, md, winning_unit_slug="": SimpleNamespace(
            topic_slug="", topic_label="", unit_slug="", confidence=0.0, ambiguous=True, reasons=[]),
        build_file_map_unit_index_from_course_fn=lambda cm, sp: [{"slug": "u1"}, {"slug": "u2"}],
        iter_content_taxonomy_topics_fn=lambda tax: [],
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

def test_unit_reconciliada_contra_bloco_do_motor():
    # unidade auto (u1, conf 0.6) discorda do bloco NOVO (u-2 -> u2) com block_conf 0.8
    # >= unit_conf: reconcilia pro bloco, reason "reconciliada_do_bloco=u-2".
    e = _entry()
    m = SimpleNamespace(slug="u1", confidence=0.6, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"
    assert "reconciliada_do_bloco=u-2" in out[0]["unit_match_reasons"]
    assert out[0]["unit_block_conflict"] == {}
    assert out[0]["unit_match_confidence"] == 0.6

def test_unit_forte_vence_e_flaga_conflito():
    e = _entry(computed_block_confidence=0.5)
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u1"
    assert out[0]["unit_block_conflict"] == {"unit": "u1", "block_unit": "u2", "block_id": "u-2"}

def test_gate_unit_tag_e_espelho_de_tags():
    # conf < T.UNIT_TAG (0.65) -> slug gated vazio -> herda a do bloco; tag unit: espelha o resultado
    e = _entry()
    m = SimpleNamespace(slug="u1", confidence=0.5, ambiguous=False, reasons=["fraca"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"          # herdada_do_bloco
    assert "unit:u2" in out[0]["auto_tags"]
    assert "unit:velha" not in out[0]["auto_tags"]
    assert "outra:tag" in out[0]["auto_tags"]            # prefixo não-gerenciado preservado

def test_manual_unit_tem_precedencia():
    e = _entry(manual_unit_slug="uman")
    m = SimpleNamespace(slug="u1", confidence=0.2, ambiguous=True, reasons=[])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "uman"
    assert out[0]["unit_match_reasons"] == ["manual"]
    assert out[0]["unit_match_confidence"] == 1.0

def test_nao_material_e_sem_bloco_ficam_intocados():
    sem_bloco = {"id": "e2", "file_type": "pdf", "computed_block_id": "", "auto_tags": []}
    nao_material = {"id": "e3", "file_type": "url", "auto_tags": []}
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=[])
    out = apply_unit_subunit_fields([sem_bloco, nao_material], BLOCKS, {}, None, None, {}, **_fns(m))
    assert "computed_unit_slug" not in out[0]
    assert "computed_unit_slug" not in out[1]
```

- [x] **Step 2: Rodar e ver falhar** — `python -m pytest tests/test_resolver_apply_units.py -q`. Esperado: `ImportError: cannot import name 'apply_unit_subunit_fields'`.

- [x] **Step 3: Implementação mínima** em `resolver_apply.py` (após `apply_concept_resolver`). Copiar o import do `T` exatamente como está no header de `content_taxonomy.py` (símbolo `T` de `src.builder.routing.thresholds`) e o `_collapse_ws` de onde `content_taxonomy` importa.

```python
def apply_unit_subunit_fields(
    entries: list,
    blocks: List[dict],
    course_meta: dict,
    subject_profile,
    root: Optional[Path],
    code_curation: dict,
    *,
    auto_map_entry_unit_fn,
    auto_map_entry_subtopic_fn,
    build_file_map_unit_index_from_course_fn,
    iter_content_taxonomy_topics_fn,
    entry_markdown_text_for_file_map_fn,
) -> list:
    """Fase 4 do cutover: unit/subunit no caminho do motor.

    Roda DEPOIS de apply_concept_resolver, sob a mesma flag: recomputa a
    unidade com o scorer sobrevivente e reconcilia contra o bloco que o
    motor acabou de gravar (fecha o gap 1.2 para os campos de unidade).
    Só toca entries que o motor decidiu (material + computed_block_id).
    """
    from src.builder.routing.file_map import reconcile_unit_with_block
    from src.builder.routing.thresholds import T
    from src.models.tag_profile import build_learned_unit_boosts, load_tag_profile
    from src.utils.helpers import collapse_ws as _collapse_ws

    unit_index = build_file_map_unit_index_from_course_fn(course_meta, subject_profile)
    content_taxonomy = (
        course_meta.get("_content_taxonomy")
        or course_meta.get("_content_taxonomy_for_tests")
        or {}
    )
    if not content_taxonomy and course_meta.get("_repo_root"):
        from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
        content_taxonomy = load_internal_content_taxonomy(course_meta["_repo_root"])
    topic_index = iter_content_taxonomy_topics_fn(content_taxonomy)

    tag_profile = None
    if root:
        try:
            tag_profile = load_tag_profile(Path(root) / "course")
        except Exception:
            tag_profile = None

    for entry in entries:
        if not _is_material(entry):
            continue
        block_id = str(entry.get("computed_block_id") or "").strip()
        if not block_id:
            continue

        markdown_text = entry_markdown_text_for_file_map_fn(root, entry) if root is not None else ""

        manual_unit = _collapse_ws(str(entry.get("manual_unit_slug") or ""))
        if manual_unit:
            resolved_unit_slug, unit_confidence = manual_unit, 1.0
            unit_ambiguous, unit_reasons = False, ["manual"]
        else:
            learned = build_learned_unit_boosts(tag_profile, entry) if tag_profile else {}
            match = auto_map_entry_unit_fn(
                entry, unit_index, markdown_text, topic_index,
                learned_unit_boosts=learned,
            )
            resolved_unit_slug = match.slug
            unit_confidence = match.confidence
            unit_ambiguous = match.ambiguous
            unit_reasons = list(match.reasons)

        gated_unit = resolved_unit_slug if (not unit_ambiguous and unit_confidence >= T.UNIT_TAG) else ""

        blk = next((b for b in blocks if str(b.get("block_uuid") or "") == block_id), None)
        if blk is None:
            blk = next((b for b in blocks if str(b.get("id") or "") == block_id), None)
        block_unit = str((blk or {}).get("unit_slug") or "").strip()

        reconciled, suffix, conflict = reconcile_unit_with_block(
            computed_unit_slug=gated_unit,
            unit_confidence=float(unit_confidence),
            computed_block_id=block_id,
            block_confidence=float(entry.get("computed_block_confidence") or 0.0),
            block_unit_slug=block_unit,
            block_is_manual=str(entry.get("computed_block_method") or "") == "manual",
            has_manual_unit=bool(manual_unit),
        )
        if suffix:
            unit_reasons = list(unit_reasons) + suffix

        entry["computed_unit_slug"] = reconciled
        entry["unit_match_reasons"] = unit_reasons
        entry["unit_match_confidence"] = unit_confidence
        entry["unit_block_conflict"] = conflict

        tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("unit:")]
        if reconciled:
            tags.append(f"unit:{reconciled}")
        entry["auto_tags"] = tags

    return entries
```

- [x] **Step 4: Rodar o teste** — `python -m pytest tests/test_resolver_apply_units.py -q`. Esperado: PASS (os stubs de subunit da Task 2 ainda não são exercitados aqui).

- [x] **Step 5: Commit**

```bash
git add tests/test_resolver_apply_units.py src/builder/routing/resolver_apply.py
git commit -m "feat(routing): apply_unit_subunit_fields — unidade do motor reconciliada (F4 cutover, achado 1.1)"
```

---

### Task 2: caminho de SUBUNIDADE (manual > topic-route restrito à unidade reconciliada)

**Files:**
- Modify: `src/builder/routing/resolver_apply.py` (dentro de `apply_unit_subunit_fields`, após o bloco de unit)
- Test: `tests/test_resolver_apply_units.py` (acrescentar)

**Interfaces:**
- Consumes: `auto_map_entry_subtopic_fn(entry, taxonomy, markdown, winning_unit_slug=...)` → objeto com `.topic_slug/.confidence/.ambiguous/.reasons`; `code_curation_signal_text` (`src/builder/core/code_summarization.py:292`); `T.SUBUNIT_TAG`.
- Produces: `computed_subunit_slug` (best-effort SEM gate), `subunit_match_reasons`, `subunit_match_confidence`, tag `subunit:` gated.

- [x] **Step 1: Testes que falham** (acrescentar ao arquivo da Task 1):

```python
def test_subunit_gated_e_best_effort():
    e = _entry()
    m = SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[])
    fns = _fns(m)
    fns["auto_map_entry_subtopic_fn"] = lambda e_, tax, md, winning_unit_slug="": SimpleNamespace(
        topic_slug="t-fraco", topic_label="", unit_slug="u2",
        confidence=0.30, ambiguous=False, reasons=["topico"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **fns)
    assert out[0]["computed_subunit_slug"] == "t-fraco"          # best-effort persiste
    assert not any(t.startswith("subunit:") for t in out[0]["auto_tags"])  # gate 0.60 segura a tag

def test_subunit_restrita_a_unidade_reconciliada():
    seen = {}
    e = _entry()
    m = SimpleNamespace(slug="u1", confidence=0.5, ambiguous=False, reasons=[])  # gated vazio -> herda u2
    fns = _fns(m)
    def _sub(e_, tax, md, winning_unit_slug=""):
        seen["unit"] = winning_unit_slug
        return SimpleNamespace(topic_slug="t1", topic_label="", unit_slug="u2",
                               confidence=0.9, ambiguous=False, reasons=[])
    fns["auto_map_entry_subtopic_fn"] = _sub
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **fns)
    assert seen["unit"] == "u2"                                   # restrição usa a unidade FINAL
    assert "subunit:t1" in out[0]["auto_tags"]

def test_manual_subunit_tem_precedencia():
    e = _entry(manual_subunit_slug="sman")
    m = SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_subunit_slug"] == "sman"
    assert out[0]["subunit_match_confidence"] == 1.0
    assert "subunit:sman" in out[0]["auto_tags"]
```

- [x] **Step 2: Rodar e ver falhar** — `python -m pytest tests/test_resolver_apply_units.py -q`. Esperado: FAIL (`computed_subunit_slug` ausente).

- [x] **Step 3: Implementação** — dentro do loop, após gravar os campos de unit:

```python
        # --- Subunit (rota de tópico, restrita à unidade FINAL reconciliada) ---
        manual_subunit = _collapse_ws(str(entry.get("manual_subunit_slug") or ""))
        if manual_subunit:
            preferred_topic_slug = manual_subunit
            best_subunit_slug = manual_subunit
            subunit_reasons = ["manual"]
            subunit_confidence = 1.0
        else:
            # Texto enriquecido: zips/código sem .md só têm sinal via resumo curado
            # (mesma mecânica do legado; unit/bloco ficam com o markdown original).
            sub_md = markdown_text
            rec = (code_curation.get("entries") or {}).get(str(entry.get("id") or "")) or {}
            if rec:
                from src.builder.core.code_summarization import code_curation_signal_text
                extra = code_curation_signal_text(rec)
                if extra:
                    sub_md = f"{markdown_text}\n\n{extra}" if markdown_text else extra
            topic_match = auto_map_entry_subtopic_fn(
                entry, content_taxonomy, sub_md, winning_unit_slug=reconciled,
            )
            best_subunit_slug = str(getattr(topic_match, "topic_slug", "") or "")
            subunit_reasons = list(getattr(topic_match, "reasons", []))
            subunit_confidence = float(getattr(topic_match, "confidence", 0.0))
            preferred_topic_slug = ""
            if (
                topic_match.topic_slug
                and not topic_match.ambiguous
                and topic_match.confidence >= T.SUBUNIT_TAG
            ):
                preferred_topic_slug = topic_match.topic_slug

        entry["computed_subunit_slug"] = best_subunit_slug
        entry["subunit_match_reasons"] = subunit_reasons
        entry["subunit_match_confidence"] = subunit_confidence

        tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
        if preferred_topic_slug:
            tags.append(f"subunit:{preferred_topic_slug}")
        entry["auto_tags"] = tags
```

- [x] **Step 4: Rodar TODOS os testes do arquivo** — `python -m pytest tests/test_resolver_apply_units.py -q`. Esperado: PASS em todos (inclusive os da Task 1 — o espelho de tags roda em dois passos, verificar que unit: não é perdida pelo passo de subunit).

- [x] **Step 5: Commit**

```bash
git add tests/test_resolver_apply_units.py src/builder/routing/resolver_apply.py
git commit -m "feat(routing): subunit no caminho do motor — topic-route restrita a unidade reconciliada (F4)"
```

---

### Task 3: wiring — engine partial + chamada flag-gated em pedagogical_regeneration

**Files:**
- Modify: `src/builder/engine.py:2147-2157` (vizinhança — acrescentar um partial novo no mesmo bloco de kwargs)
- Modify: `src/builder/ops/pedagogical_regeneration.py:359` (assinatura) e `:518-526` (chamada)
- Test: `tests/test_resolver_wiring.py` (acrescentar caso)

**Interfaces:**
- Produces: kwarg `apply_unit_subunit_fn` em `regenerate_pedagogical_files`; engine monta `partial(apply_unit_subunit_fields, auto_map_entry_unit_fn=_auto_map_entry_unit, auto_map_entry_subtopic_fn=_auto_map_entry_subtopic, build_file_map_unit_index_from_course_fn=_build_file_map_unit_index_from_course, iter_content_taxonomy_topics_fn=_iter_content_taxonomy_topics, entry_markdown_text_for_file_map_fn=_entry_markdown_text_for_file_map)` — os MESMOS aliases já usados no partial do legado (`engine.py:2149-2156`).

- [x] **Step 1: Teste de wiring que falha** — em `tests/test_resolver_wiring.py`, seguir o padrão dos casos existentes do arquivo (que já testam a chamada flag-gated de `apply_concept_resolver`): flag ON ⇒ entries saem com `computed_unit_slug`/`computed_subunit_slug` presentes; flag OFF ⇒ `apply_unit_subunit_fields` NÃO é chamado (monkeypatch com sentinela que explode se invocado).

- [x] **Step 2: Rodar e ver falhar** — `python -m pytest tests/test_resolver_wiring.py -q`.

- [x] **Step 3: Implementar o wiring.** Em `pedagogical_regeneration.py`, dentro do gate existente (`:518`), logo após `apply_concept_resolver`:

```python
    if bool(builder.options.get("use_concept_resolver", False)):
        from src.builder.routing.resolver_apply import apply_concept_resolver
        live_manifest_entries = apply_concept_resolver(
            live_manifest_entries,
            enriched_timeline_index.get("blocks") or [],
            content_taxonomy.get("units") or [],
            _code_curation,
            builder.root_dir,
        )
        # F4: unit/subunit do motor, reconciliados contra o bloco recém-gravado.
        live_manifest_entries = apply_unit_subunit_fn(
            live_manifest_entries,
            enriched_timeline_index.get("blocks") or [],
            runtime_course_meta,
            builder.subject_profile,
            builder.root_dir,
            _code_curation,
        )
```

No engine, no mesmo bloco de kwargs de `:2147`:

```python
            apply_unit_subunit_fn=partial(
                _apply_unit_subunit_fields,
                auto_map_entry_unit_fn=_auto_map_entry_unit,
                auto_map_entry_subtopic_fn=_auto_map_entry_subtopic,
                build_file_map_unit_index_from_course_fn=_build_file_map_unit_index_from_course,
                iter_content_taxonomy_topics_fn=_iter_content_taxonomy_topics,
                entry_markdown_text_for_file_map_fn=_entry_markdown_text_for_file_map,
            ),
```

com `_apply_unit_subunit_fields` importado no topo do engine junto dos demais re-exports de routing (seguir o padrão de import do módulo; NÃO importar engine a partir de routing).

- [x] **Step 4: Rodar wiring + arquivo de units + suite rápida de routing** — `python -m pytest tests/test_resolver_wiring.py tests/test_resolver_apply_units.py -q`. Esperado: PASS.

- [x] **Step 5: Commit**

```bash
git add src/builder/engine.py src/builder/ops/pedagogical_regeneration.py tests/test_resolver_wiring.py
git commit -m "feat(engine): wire apply_unit_subunit_fields sob use_concept_resolver (F4)"
```

---

### Task 4: gates da fase — flag OFF byte-idêntico + suite + régua

- [x] **Step 1: Suite completa** — `python -m pytest tests -q`. Esperado: ≥1934 passed / 1 skipped / 0 failed (baseline do handoff; os novos testes somam).

- [x] **Step 2: Sentinelas** — `python -m pytest tests/test_caracterizacao_blocos_atual.py -q`. Esperado: PASS com ZERO diff de snapshot (flag OFF em produção — Fase 4 não pode mover atribuição).

- [x] **Step 3: Régua MF** — `python scripts/eval_ground_truth.py ..\Metodos-Formais-Tutor tests\fixtures\eval\ground_truth_MF.csv`. Esperado: ≥ 50/57 (igual ao baseline 87.7%).

- [x] **Step 4: Commit de fecho da fase (se algo mudou em docs/testes durante os gates)** e reportar os três números no resumo da sessão.

---

### Task 5: medição de prontidão pro flip (read-only, sandbox)

**Files:**
- Create: relatório curto `docs/reports/2026-08-XX-f4-medicao-unit-motor.md` (números, sem prosa longa)
- Modify: `docs/reports/pendencias.md` (registrar F4 concluída + números na seção Concluído; remover o pré-requisito do item 1.1 da fila)

- [x] **Step 1:** Rodar build sandbox flag-ON num curso com gold (MF) SEM escrever no repo-tutor de produção (cópia em scratchpad, mesma mecânica do sandbox T12 do handoff da campanha 2), comparando os campos unit legado×motor: contar entries com `computed_unit_slug` divergente e listar os reasons.
- [x] **Step 2:** `python scripts/eval_units.py` com `tests/fixtures/eval/gold_units_MF.csv` na cópia flag-ON. Esperado pro go do flip: 5/5 dos golds unit (gate do handoff) — se <5/5, registrar os casos e PARAR (decisão de calibração antes do passo 2 da campanha).
- [x] **Step 3:** Escrever o relatório + atualizar tracker (Scaffold Growth do `.mex/AGENTS.md`: mover estado pro tracker, rodar `graphify update .`).
- [x] **Step 4: Commit**

```bash
git add docs/reports/ docs/superpowers/plans/2026-08-14-fase4-unit-subunit-motor.md
git commit -m "docs(f4): medicao unit motor flag-ON + fecho da fase 4"
```

---

## Notas de escopo (não fazer aqui)

- **1.2 bloco→reconcile pós-`attach_block_summary_fields`** e **1.3 resync `auto_tags`**: passo 2 da campanha, plano próprio. A F4 fecha o gap 1.2 apenas para o caminho de unidade sob a flag.
- **Limpeza `_NO_TIMELINE_CATEGORIES`** (`content_taxonomy.py:1137-1147`): permanece responsabilidade do legado até a F5; na F5, portar esse pedaço junto (registrado no mapa de deleção como dependência nova — adicionar linha no tracker ao fechar a F4).
- **Cobertura**: o motor só sobrepõe entries com `computed_block_id`; entries sem bloco continuam com os campos do legado até o flip. A medição da Task 5 quantifica esse resíduo.

## Self-review (feita na escrita)

- Contrato da UI coberto: 6 campos + 2 tags ↔ Tasks 1-2. Reconcile contra bloco NOVO ↔ Task 1 Step 3. Gates do handoff ↔ Task 4. Go/no-go do flip ↔ Task 5.
- Tipos consistentes: `apply_unit_subunit_fields` mesma assinatura nas Tasks 1-3; stubs dos testes casam com `UnitMatchResult`/`TopicMatchResult` via SimpleNamespace (atributos idênticos aos lidos em `content_taxonomy.py:1176-1205`).
- Sem placeholders: todo step tem código ou comando concreto.
