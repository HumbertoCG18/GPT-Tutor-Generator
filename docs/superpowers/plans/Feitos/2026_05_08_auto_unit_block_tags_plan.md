# Auto-Tags de Unidade/Subunidade/Bloco — Plano de Implementação

> **Para agentic workers:** Use `superpowers:executing-plans` para executar task-by-task.
> Steps usam sintaxe checkbox (`- [ ]`) para rastreamento.

**Feature branch:** `new-features`
**Arquivo de spec relacionado:** `docs/features/2026-05-07-unit-subunit-assignment-fix.md`

---

## Contexto

O pipeline já faz scoring de unidade e bloco temporal durante a geração do
`FILE_MAP.md`, mas **descarta os resultados após o render**. Isso impede:

1. Feedback loop — `score_entry_against_unit()` usa `auto_tags_text` como sinal,
   mas nunca escreve `unit:slug` de volta nesse campo.
2. Navegação por tag — o tutor não consegue consultar "arquivos da unidade 2"
   via tag; só via a coluna Unidade do FILE_MAP (não-queryável).
3. Estabilidade — assignment é recalculado do zero em cada regeneração, sem
   memória das atribuições anteriores.

**Solução:** nova função `resolve_unit_block_tags()` que roda após
`refresh_manifest_auto_tags()` e escreve tags gerenciadas nos namespaces
`unit:`, `subunit:` e `bloco:` dentro de `auto_tags` de cada entry no manifest.

Adicionalmente: sinal `DD.MM` no nome de arquivo como boost no scoring de
bloco temporal (Roadmap item 5, custo baixo).

---

## Contratos

### Tags geradas (namespaces gerenciados)

| Tag | Threshold | Exemplo |
|---|---|---|
| `unit:slug` | confidence ≥ 0.65 AND não ambíguo | `unit:unidade-02-derivadas` |
| `subunit:slug` | confidence ≥ 0.60 AND não ambíguo | `subunit:regra-da-cadeia` |
| `bloco:id` | confidence ≥ 0.50 AND não ambíguo | `bloco:bloco-04` |

### Regras de não-regressão

- `manual_tags` nunca são tocadas.
- `manual_unit_slug` e `manual_timeline_block_id` têm precedência absoluta
  (confidence = 1.0 quando presentes).
- Categorias `cronograma`, `bibliografia`, `referencias` são puladas.
- Tags com outros prefixos em `auto_tags` são preservadas sem alteração.
- Se confidence não atingir threshold, a tag simplesmente não é adicionada
  (sem tag falsa, sem penalidade).

---

## Task 1 — Sinal DD.MM em `entry_signals.py`

**Arquivo:** `src/builder/extraction/entry_signals.py`

- [ ] **Step 1: Escrever o teste falhante**

Criar `tests/test_date_prefix_signal.py`:

```python
from datetime import date
from src.builder.extraction.entry_signals import extract_date_prefix_signal


def test_extract_date_prefix_signal_parses_dd_mm():
    result = extract_date_prefix_signal("12.03 Processos.pdf", year=2026)
    assert result == date(2026, 3, 12)


def test_extract_date_prefix_signal_parses_single_digit_day():
    result = extract_date_prefix_signal("5.09 Slides aula.pdf", year=2026)
    assert result == date(2026, 9, 5)


def test_extract_date_prefix_signal_returns_none_when_no_pattern():
    assert extract_date_prefix_signal("Processos.pdf", year=2026) is None
    assert extract_date_prefix_signal("cap01-introducao.pdf", year=2026) is None


def test_extract_date_prefix_signal_returns_none_on_invalid_date():
    assert extract_date_prefix_signal("32.13 arquivo.pdf", year=2026) is None


def test_extract_date_prefix_signal_uses_stem_not_full_name():
    # extensão não deve atrapalhar
    result = extract_date_prefix_signal("15.04 Listas.pdf", year=2026)
    assert result == date(2026, 4, 15)
```

- [ ] **Step 2: Rodar e confirmar FAIL**

```bash
python -m pytest tests/test_date_prefix_signal.py -q
```

Esperado: `ImportError` ou `AttributeError` em `extract_date_prefix_signal`.

- [ ] **Step 3: Implementar em `entry_signals.py`**

Adicionar ao final do arquivo (sem tocar no que existe):

```python
import re as _re
from datetime import date as _date
from pathlib import Path as _Path
from typing import Optional as _Optional

_DATE_PREFIX_RE = _re.compile(r"^(\d{1,2})\.(\d{2})\s+")


def extract_date_prefix_signal(filename: str, year: int) -> _Optional[_date]:
    """Extrai sinal de data DD.MM do início do nome do arquivo.

    Padrão esperado: '12.03 Processos.pdf' → date(year, 3, 12)
    O ponto é usado como separador porque '/' não é válido em nomes de
    arquivo no Windows. Retorna None se o padrão não casar ou a data
    for inválida.
    """
    stem = _Path(filename).stem
    m = _DATE_PREFIX_RE.match(stem)
    if not m:
        return None
    try:
        return _date(year, int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None
```

- [ ] **Step 4: Rodar e confirmar PASS**

```bash
python -m pytest tests/test_date_prefix_signal.py -q
```

Esperado: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_date_prefix_signal.py src/builder/extraction/entry_signals.py
git commit -m "feat(signals): add extract_date_prefix_signal for DD.MM filename pattern"
```

---

## Task 2 — Boost DD.MM em `score_entry_against_timeline_block`

**Arquivo:** `src/builder/routing/file_map.py`

- [ ] **Step 1: Escrever o teste falhante**

Criar `tests/test_ddmm_timeline_boost.py`:

```python
from src.builder.routing.file_map import score_entry_against_timeline_block
from src.builder.extraction.entry_signals import normalize_match_text


def _make_signals(title: str, raw_target: str = "") -> dict:
    return {
        "title_text": normalize_match_text(title),
        "markdown_headings_text": "",
        "markdown_lead_text": "",
        "markdown_text": "",
        "category_text": "",
        "manual_tags_text": "",
        "auto_tags_text": "",
        "legacy_tags_text": "",
        "tags_text": "",
        "raw_text": normalize_match_text(raw_target),
    }


def _make_block(date_text: str, content: str = "Aula generica") -> dict:
    return {
        "id": "bloco-01",
        "rows": [{"content": content, "date_text": date_text, "ignored": False}],
        "unit_slug": "",
        "unit_confidence": 0.0,
        "primary_topic_slug": "",
        "primary_topic_confidence": 0.0,
        "topic_ambiguous": True,
        "topic_candidates": [],
        "topic_text": "",
        "topics": [],
        "aliases": [],
        "card_evidence": [],
        "sessions": [],
        "period_label": date_text,
        "scores": [0.0],
    }


def _call_score(signals, block):
    from src.builder.extraction.entry_signals import (
        normalize_match_text,
        score_text_against_row,
    )
    from src.builder.routing.file_map import score_card_evidence_against_entry

    def _score_card(s, items):
        return score_card_evidence_against_entry(
            s, items, normalize_match_text=normalize_match_text
        )

    return score_entry_against_timeline_block(
        signals,
        block,
        normalize_match_text=normalize_match_text,
        score_text_against_row=score_text_against_row,
        score_card_evidence_against_entry_fn=_score_card,
    )


def test_ddmm_boost_applied_when_filename_date_matches_block_date():
    signals = _make_signals("Processos", raw_target="12.03 processos")
    block = _make_block(date_text="12/03/2026")
    score_with_match = _call_score(signals, block)

    signals_no_date = _make_signals("Processos", raw_target="processos")
    score_without = _call_score(signals_no_date, block)

    assert score_with_match > score_without


def test_ddmm_boost_not_applied_when_date_mismatches():
    signals_mismatch = _make_signals("Processos", raw_target="15.04 processos")
    signals_match = _make_signals("Processos", raw_target="12.03 processos")
    block = _make_block(date_text="12/03/2026")

    score_mismatch = _call_score(signals_mismatch, block)
    score_match = _call_score(signals_match, block)

    assert score_match > score_mismatch


def test_ddmm_boost_not_applied_when_no_date_prefix():
    signals = _make_signals("Processos", raw_target="processos sem data")
    block = _make_block(date_text="12/03/2026")
    # deve funcionar sem erro
    score = _call_score(signals, block)
    assert isinstance(score, float)
```

- [ ] **Step 2: Rodar e confirmar FAIL**

```bash
python -m pytest tests/test_ddmm_timeline_boost.py -q
```

Esperado: os dois primeiros testes falham (boost não existe ainda).

- [ ] **Step 3: Implementar o boost em `score_entry_against_timeline_block`**

Localizar em `src/builder/routing/file_map.py` o final da função
`score_entry_against_timeline_block`, **antes do último `return score`**.

Inserir o bloco:

```python
    # Boost DD.MM: se o raw_target começa com DD.MM e a data casa com alguma
    # row do bloco, aplica boost pequeno e determinístico (+0.30).
    raw_target_text = signals.get("raw_text", "")
    if raw_target_text:
        import re as _boost_re
        _dd_mm = _boost_re.match(r"^(\d{1,2})\.(\d{2})\s+", raw_target_text)
        if _dd_mm:
            _day = int(_dd_mm.group(1))
            _month = int(_dd_mm.group(2))
            _file_date_str = f"{_day:02d}/{_month:02d}"
            for _row in (block.get("rows") or []):
                _row_date = str(_row.get("date_text", "") or "")
                if _row_date.startswith(_file_date_str):
                    score += 0.30
                    break
```

- [ ] **Step 4: Rodar e confirmar PASS**

```bash
python -m pytest tests/test_ddmm_timeline_boost.py -q
```

Esperado: 3 passed.

- [ ] **Step 5: Rodar suite completa para garantir não-regressão**

```bash
python -m pytest tests/ -q
```

Esperado: sem falhas novas.

- [ ] **Step 6: Commit**

```bash
git add tests/test_ddmm_timeline_boost.py src/builder/routing/file_map.py
git commit -m "feat(routing): boost timeline block score for DD.MM filename date pattern"
```

---

## Task 3 — `resolve_unit_block_tags()` em `content_taxonomy.py`

**Arquivo:** `src/builder/extraction/content_taxonomy.py`

- [ ] **Step 1: Escrever os testes falhantes**

Criar `tests/test_resolve_unit_block_tags.py`:

```python
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags


def _make_minimal_entry(entry_id: str, title: str, category: str = "material-de-aula") -> dict:
    return {
        "id": entry_id,
        "title": title,
        "category": category,
        "file_type": "pdf",
        "source_path": f"/tmp/{entry_id}.pdf",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
    }


def _stub_unit_match(slug, confidence, ambiguous=False):
    class M:
        pass
    m = M()
    m.slug = slug
    m.confidence = confidence
    m.ambiguous = ambiguous
    m.reasons = []
    return m


def _stub_topic_match(slug="", confidence=0.0, ambiguous=True):
    class M:
        pass
    m = M()
    m.topic_slug = slug
    m.topic_label = slug
    m.unit_slug = ""
    m.confidence = confidence
    m.ambiguous = ambiguous
    m.reasons = []
    return m


def test_resolve_unit_block_tags_adds_unit_tag_when_high_confidence():
    entries = [_make_minimal_entry("e1", "Slides Unidade 2")]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "unit:unidade-02" in tags


def test_resolve_unit_block_tags_skips_unit_tag_when_low_confidence():
    entries = [_make_minimal_entry("e1", "Slides")]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-02", confidence=0.40, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert not any(t.startswith("unit:") for t in tags)


def test_resolve_unit_block_tags_skips_unit_tag_when_ambiguous():
    entries = [_make_minimal_entry("e1", "Slides")]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=True
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert not any(t.startswith("unit:") for t in tags)


def test_resolve_unit_block_tags_adds_subunit_tag():
    entries = [_make_minimal_entry("e1", "Regra da Cadeia")]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(
            slug="regra-da-cadeia", confidence=0.75, ambiguous=False
        ),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "subunit:regra-da-cadeia" in tags


def test_resolve_unit_block_tags_adds_bloco_tag_via_manual_override():
    entries = [_make_minimal_entry("e1", "Lista")]
    entries[0]["manual_timeline_block_id"] = "bloco-03"

    fake_block = {"id": "bloco-03", "period_label": "10/04/2026"}

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match("", 0.0, True),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: fake_block,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "bloco:bloco-03" in tags


def test_resolve_unit_block_tags_skips_special_categories():
    entries = [
        _make_minimal_entry("e1", "Cronograma", category="cronograma"),
        _make_minimal_entry("e2", "Bibliografia", category="bibliografia"),
        _make_minimal_entry("e3", "Referências", category="referencias"),
    ]

    call_count = {"n": 0}

    def counting_unit_fn(e, u, m, ti):
        call_count["n"] += 1
        return _stub_unit_match("unidade-01", 0.90, False)

    resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=counting_unit_fn,
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    assert call_count["n"] == 0, "Categorias especiais não devem chamar o unit matcher"


def test_resolve_unit_block_tags_preserves_existing_non_managed_auto_tags():
    entries = [_make_minimal_entry("e1", "Slides")]
    entries[0]["auto_tags"] = ["topico:calculo-diferencial", "tipo:material-base"]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match("", 0.0, True),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "topico:calculo-diferencial" in tags
    assert "tipo:material-base" in tags


def test_resolve_unit_block_tags_manual_unit_slug_takes_precedence():
    """manual_unit_slug deve ser usado como unit:slug mesmo sem scoring."""
    entries = [_make_minimal_entry("e1", "Slides")]
    entries[0]["manual_unit_slug"] = "unidade-99-manual"

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        # unit matcher retorna slug diferente — não deve ser usado
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-01", 0.90, False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "unit:unidade-99-manual" in tags
    assert "unit:unidade-01" not in tags
```

- [ ] **Step 2: Rodar e confirmar FAIL**

```bash
python -m pytest tests/test_resolve_unit_block_tags.py -q
```

Esperado: `ImportError` — `resolve_unit_block_tags` não existe ainda.

- [ ] **Step 3: Implementar `resolve_unit_block_tags` em `content_taxonomy.py`**

Adicionar ao **final** do arquivo `src/builder/extraction/content_taxonomy.py`,
sem alterar nenhuma função existente:

```python
def resolve_unit_block_tags(
    manifest_entries: List[dict],
    course_meta: dict,
    subject_profile=None,
    *,
    build_file_map_unit_index_from_course_fn,
    build_file_map_timeline_context_from_course_fn,
    iter_content_taxonomy_topics_fn,
    auto_map_entry_subtopic_fn,
    auto_map_entry_unit_fn,
    select_probable_period_for_entry_fn,
    resolve_entry_manual_timeline_block_fn,
    entry_markdown_text_for_file_map_fn,
) -> List[dict]:
    """Adiciona tags gerenciadas unit:, subunit: e bloco: ao auto_tags de cada
    entry no manifest.

    Thresholds:
    - unit:   confidence >= 0.65 AND não ambíguo
    - subunit: confidence >= 0.60 AND não ambíguo
    - bloco:  confidence >= 0.50 AND não ambíguo (ou manual_timeline_block_id)

    manual_tags nunca são tocadas. Tags com outros prefixos em auto_tags são
    preservadas. manual_unit_slug e manual_timeline_block_id têm precedência
    absoluta (confidence = 1.0).
    """
    _NO_TIMELINE_CATEGORIES = {"cronograma", "bibliografia", "referencias"}
    _UNIT_PREFIX = "unit:"
    _SUBUNIT_PREFIX = "subunit:"
    _BLOCO_PREFIX = "bloco:"
    _MANAGED = (_UNIT_PREFIX, _SUBUNIT_PREFIX, _BLOCO_PREFIX)

    unit_index = build_file_map_unit_index_from_course_fn(course_meta, subject_profile)
    timeline_context = build_file_map_timeline_context_from_course_fn(
        course_meta, subject_profile
    )
    content_taxonomy = (
        course_meta.get("_content_taxonomy")
        or course_meta.get("_content_taxonomy_for_tests")
        or {}
    )
    topic_index = iter_content_taxonomy_topics_fn(content_taxonomy)
    blocks_by_unit = dict(timeline_context.get("blocks_by_unit") or {})
    unassigned_blocks = list(timeline_context.get("unassigned_blocks") or [])
    repo_root = course_meta.get("_repo_root")

    updated: List[dict] = []
    for entry in manifest_entries or []:
        category = _collapse_ws(str(entry.get("category") or "")).lower()
        if category in _NO_TIMELINE_CATEGORIES:
            updated.append(entry)
            continue

        markdown_text = entry_markdown_text_for_file_map_fn(repo_root, entry)

        # --- Topic/subunit match ---
        topic_match = auto_map_entry_subtopic_fn(entry, content_taxonomy, markdown_text)
        preferred_topic_slug = ""
        if (
            topic_match.topic_slug
            and not topic_match.ambiguous
            and topic_match.confidence >= 0.60
        ):
            preferred_topic_slug = topic_match.topic_slug

        # --- Unit match (manual tem precedência) ---
        manual_unit = _collapse_ws(str(entry.get("manual_unit_slug") or ""))
        if manual_unit:
            resolved_unit_slug = manual_unit
            unit_confidence = 1.0
            unit_ambiguous = False
        else:
            unit_match = auto_map_entry_unit_fn(
                entry, unit_index, markdown_text, topic_index
            )
            resolved_unit_slug = unit_match.slug
            unit_confidence = unit_match.confidence
            unit_ambiguous = unit_match.ambiguous

        # --- Block match (manual tem precedência) ---
        period_block_id = ""
        manual_block = resolve_entry_manual_timeline_block_fn(entry, timeline_context)
        if manual_block:
            period_block_id = _collapse_ws(str(manual_block.get("id") or ""))
        elif resolved_unit_slug and not unit_ambiguous and unit_confidence >= 0.55:
            candidate_rows = list(blocks_by_unit.get(resolved_unit_slug) or [])
            if not candidate_rows:
                candidate_rows = unassigned_blocks
            if candidate_rows:
                unit_obj = next(
                    (u for u in unit_index if u.get("slug") == resolved_unit_slug), {}
                )
                _period, p_conf, p_ambig, _ = select_probable_period_for_entry_fn(
                    entry=entry,
                    unit=unit_obj,
                    candidate_rows=candidate_rows,
                    markdown_text=markdown_text,
                    preferred_topic_slug=preferred_topic_slug,
                )
                if _period and not p_ambig and p_conf >= 0.50:
                    for block in candidate_rows:
                        if str(block.get("period_label") or "") == _period:
                            period_block_id = _collapse_ws(str(block.get("id") or ""))
                            break

        # --- Monta novo auto_tags ---
        existing_auto = list(entry.get("auto_tags") or [])
        kept = [t for t in existing_auto if not any(t.startswith(p) for p in _MANAGED)]

        if resolved_unit_slug and not unit_ambiguous and unit_confidence >= 0.65:
            kept.append(f"{_UNIT_PREFIX}{resolved_unit_slug}")

        if preferred_topic_slug:
            kept.append(f"{_SUBUNIT_PREFIX}{preferred_topic_slug}")

        if period_block_id:
            kept.append(f"{_BLOCO_PREFIX}{period_block_id}")

        new_entry = dict(entry)
        new_entry["auto_tags"] = kept
        updated.append(new_entry)

    return updated
```

- [ ] **Step 4: Rodar e confirmar PASS**

```bash
python -m pytest tests/test_resolve_unit_block_tags.py -q
```

Esperado: 8 passed.

- [ ] **Step 5: Rodar suite completa**

```bash
python -m pytest tests/ -q
```

Esperado: sem falhas novas.

- [ ] **Step 6: Commit**

```bash
git add tests/test_resolve_unit_block_tags.py src/builder/extraction/content_taxonomy.py
git commit -m "feat(taxonomy): add resolve_unit_block_tags for unit/subunit/block auto-tagging"
```

---

## Task 4 — Wiring em `engine.py` e `pedagogical_regeneration.py`

**Arquivos:** `src/builder/ops/pedagogical_regeneration.py` e `src/builder/engine.py`

- [ ] **Step 1: Adicionar parâmetro `resolve_unit_block_tags_fn` em `regenerate_pedagogical_files`**

Em `src/builder/ops/pedagogical_regeneration.py`, na assinatura de
`regenerate_pedagogical_files`, adicionar o novo parâmetro **depois** de
`refresh_manifest_auto_tags_fn`:

```python
    refresh_manifest_auto_tags_fn,
    resolve_unit_block_tags_fn,       # <-- novo
```

- [ ] **Step 2: Chamar a nova função no corpo de `regenerate_pedagogical_files`**

Localizar a linha:

```python
    live_manifest_entries = refresh_manifest_auto_tags_fn(builder.root_dir, live_manifest_entries, tag_catalog)
    manifest["entries"] = live_manifest_entries
```

Substituir por:

```python
    live_manifest_entries = refresh_manifest_auto_tags_fn(builder.root_dir, live_manifest_entries, tag_catalog)

    # Resolve tags de unidade/subunidade/bloco e persiste em auto_tags
    live_manifest_entries = resolve_unit_block_tags_fn(
        live_manifest_entries,
        runtime_course_meta,
        builder.subject_profile,
    )

    manifest["entries"] = live_manifest_entries
```

- [ ] **Step 3: Importar e wired em `engine.py`**

Adicionar o import (junto aos outros imports de `content_taxonomy`):

```python
from src.builder.extraction.content_taxonomy import (
    # ... imports existentes ...
    resolve_unit_block_tags as _resolve_unit_block_tags,
)
```

Localizar o método `_regenerate_pedagogical_files` em `RepoBuilder`
(que chama `_pedagogical_regeneration_regenerate_pedagogical_files`).
Adicionar o argumento `resolve_unit_block_tags_fn` à chamada:

```python
            resolve_unit_block_tags_fn=partial(
                _resolve_unit_block_tags,
                build_file_map_unit_index_from_course_fn=_build_file_map_unit_index_from_course,
                build_file_map_timeline_context_from_course_fn=_build_file_map_timeline_context_from_course,
                iter_content_taxonomy_topics_fn=_iter_content_taxonomy_topics,
                auto_map_entry_subtopic_fn=_auto_map_entry_subtopic,
                auto_map_entry_unit_fn=_auto_map_entry_unit,
                select_probable_period_for_entry_fn=_select_probable_period_for_entry,
                resolve_entry_manual_timeline_block_fn=_resolve_entry_manual_timeline_block,
                entry_markdown_text_for_file_map_fn=_entry_markdown_text_for_file_map,
            ),
```

- [ ] **Step 4: Verificar que `_resolve_unit_block_tags` está no `__all__` de `engine.py`**

Adicionar se não estiver:

```python
    "_resolve_unit_block_tags",
```

- [ ] **Step 5: Rodar suite completa**

```bash
python -m pytest tests/ -q
```

Esperado: sem falhas.

- [ ] **Step 6: Smoke test manual (opcional mas recomendado)**

```bash
python -c "
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags
print('import OK')
"
```

- [ ] **Step 7: Commit**

```bash
git add src/builder/ops/pedagogical_regeneration.py src/builder/engine.py
git commit -m "feat(engine): wire resolve_unit_block_tags into pedagogical regeneration pipeline"
```

---

## Task 5 — Verificação end-to-end e atualização de scaffold

- [ ] **Step 1: Rodar suite completa limpa**

```bash
python -m pytest tests/ -q
```

Esperado: verde, sem falhas novas.

- [ ] **Step 2: Verificar checklist de convenções**

Seguindo `context/conventions.md`:

- [ ] Nova lógica em subpackage correto (`extraction/content_taxonomy.py`), não em `engine.py`
- [ ] `engine.py` recebe a função via `partial` — sem lógica nova
- [ ] `logger = logging.getLogger(__name__)` presente nos módulos modificados
- [ ] Campos opcionais com `= None` onde aplicável
- [ ] Sem comentários óbvios; apenas WHY quando não óbvio
- [ ] Sem docstrings multi-parágrafo

- [ ] **Step 3: Atualizar `ROUTER.md`**

Em `.mex/ROUTER.md`, seção `Working`, adicionar:

```
- Auto-tags de unidade/subunidade/bloco geradas em `resolve_unit_block_tags()`:
  tags `unit:`, `subunit:`, `bloco:` persistidas em `auto_tags` do manifest após
  cada regeneração pedagógica.
- Sinal DD.MM: arquivo `12.03 Processos.pdf` recebe boost +0.30 no bloco do
  cronograma correspondente em `score_entry_against_timeline_block()`.
```

- [ ] **Step 4: Atualizar `patterns/INDEX.md`**

Adicionar linha para o novo padrão se relevante para tarefas futuras.

- [ ] **Step 5: Commit final de scaffold**

```bash
git add .mex/ROUTER.md .mex/patterns/INDEX.md
git commit -m "docs(scaffold): update ROUTER with unit/block auto-tag pipeline"
```

---

## Resumo de arquivos modificados

| Arquivo | Tipo | O que muda |
|---|---|---|
| `src/builder/extraction/entry_signals.py` | Adição | Nova função `extract_date_prefix_signal()` |
| `src/builder/routing/file_map.py` | Modificação cirúrgica | Boost DD.MM no final de `score_entry_against_timeline_block()` |
| `src/builder/extraction/content_taxonomy.py` | Adição | Nova função `resolve_unit_block_tags()` |
| `src/builder/ops/pedagogical_regeneration.py` | Modificação cirúrgica | Novo parâmetro + 4 linhas de chamada |
| `src/builder/engine.py` | Modificação cirúrgica | Import + `partial` wiring do novo parâmetro |
| `tests/test_date_prefix_signal.py` | Novo | 5 testes para `extract_date_prefix_signal` |
| `tests/test_ddmm_timeline_boost.py` | Novo | 3 testes para boost DD.MM |
| `tests/test_resolve_unit_block_tags.py` | Novo | 8 testes para `resolve_unit_block_tags` |
| `.mex/ROUTER.md` | Atualização | Current Project State |

**Nenhuma assinatura de função existente é alterada.**
**Nenhum campo novo no manifest** (`auto_tags` já existe).
**Todos os testes existentes continuam passando.**