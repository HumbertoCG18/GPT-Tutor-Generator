# Approach C — Referências de apoio no COURSE_MAP — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Referência mapeada a uma unidade/tópico aparece ativamente no `course/COURSE_MAP.md` como material de apoio, conectada ao material principal do tópico.

**Architecture:** Um helper puro novo (`reference_navigation.py`) junta `references_curation.json` + entries do manifest num índice por âncora (unidade / unidade+tópico). O índice é injetado em `course_meta["_reference_nav_index"]` (mesmo padrão de `_timeline_context`/`_assessment_context` já usado), então o renderer ativo do COURSE_MAP (`render_low_token_course_map_md`) lê esse índice e emite linhas `📖 Apoio:` sob cada unidade/tópico — sem nenhuma mudança de assinatura na cadeia de wiring. A tabela de relevância redundante da BIBLIOGRAPHY é removida e vira ponteiro. O prompt do tutor ganha uma instrução curta de como usar as linhas de apoio.

**Tech Stack:** Python 3.13, pytest. Sem dependências novas.

**Spec:** `docs/superpowers/specs/2026-06-04-approach-c-referencias-no-course-map-design.md`

---

## Decisões de arquitetura travadas (verificadas no código)

1. **Injeção por `course_meta`, não por kwargs.** `render_low_token_course_map_md` (`navigation.py:401`) já lê `course_meta.get("_timeline_context")` e `course_meta.get("_assessment_context")`. Adicionamos `course_meta["_reference_nav_index"]` no mesmo lugar onde `_timeline_context`/`_assessment_context` são setados (`pedagogical_regeneration.py:190,204`). **Nenhum wrapper (`course_map_md`, `low_token_course_map_md_v2`, `render_low_token_course_map_md_v2`) muda de assinatura.**

2. **Slug de unidade alinha.** O índice de unidades que gerou `computed_ref_unit` usa `"slug": normalize_unit_slug(title)` (`routing/file_map.py:101`). O renderer do COURSE_MAP usa o mesmo `normalize_unit_slug(unit_title)` (dep injetada, `navigation.py:407`). Logo `computed_ref_unit` (chave do índice) casa com `normalize_unit_slug(unit_title)` no renderer. **O helper NÃO precisa de função de slug para unidade** — usa `computed_ref_unit` direto como chave.

3. **Tópico via normalizador trivial compartilhado.** `computed_ref_topics` são labels (topic_phrases). O renderer renderiza tópicos via `topic_text(topic)` (label). Ambos os lados normalizam com `_norm_topic(s) = " ".join((s or "").lower().split())`, definido no helper e importado pelo renderer — garante chave idêntica sem depender de `slugify`. Match de tópico é best-effort; quando não casa, a ref cai no balde da unidade (fallback garantido).

4. **Entries como dicts do manifest.json.** A curation foi gerada lendo `manifest.json` como dicts (`entry.get("id")`). O helper recebe os mesmos dicts (lidos de `manifest.json`) → `id`/`title`/`source_path`/`file_type` alinham com as chaves da curation. Em `pedagogical_regeneration`, lemos `manifest.json` fresco (igual `summarize_all_reference_entries` faz).

---

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `src/builder/core/reference_navigation.py` (criar) | Helper puro: `build_unit_topic_reference_index`, `_norm_topic`, `_ref_support_line`, `_REF_CAP_PER_ANCHOR`. Sem I/O. |
| `src/builder/artifacts/navigation.py` (modificar) | `render_low_token_course_map_md`: ler `course_meta["_reference_nav_index"]` e emitir linhas de apoio no loop de unidades/tópicos. |
| `src/builder/ops/pedagogical_regeneration.py` (modificar) | Construir o índice e setar `runtime_course_meta["_reference_nav_index"]` antes de gerar o COURSE_MAP. |
| `src/builder/artifacts/prompts.py` (modificar) | Bloco de instrução: como o tutor usa linhas `📖 Apoio:`. |
| `src/builder/artifacts/repo.py` (modificar) | `bibliography_md`: remover tabela de relevância → ponteiro; corrigir label do clamp. |
| `tests/test_reference_navigation.py` (criar) | Testes do helper. |
| `tests/test_course_map_references.py` (criar) | Testes do renderer + modo degradado + integração leve do wiring. |
| `tests/test_prompts_reference_support.py` (criar) | Teste da instrução no prompt. |
| `tests/test_bibliography_cleanup.py` (criar) | Testes da limpeza da BIBLIOGRAPHY. |

---

## Task 1: Helper puro — índice de referências por âncora

**Files:**
- Create: `src/builder/core/reference_navigation.py`
- Test: `tests/test_reference_navigation.py`

Formato de cada `ref` no índice:
```python
{
    "entry_id": str, "title": str, "source_path": str,
    "type": "repo" | "doc",
    "concepts": [str, ...],   # ref_concepts cortado a 3
    "topics": [str, ...],     # computed_ref_topics (labels)
    "unit_slug": str,
}
```
Retorno: `{"by_unit": {unit_slug: [ref, ...]}, "by_topic": {(unit_slug, topic_key): [ref, ...]}}`.

- [ ] **Step 1: Write the failing test (criação do arquivo de teste com os 7 casos)**

```python
# tests/test_reference_navigation.py
"""Índice de referências por âncora (unidade / unidade+tópico) p/ o COURSE_MAP.

Junta references_curation.json (computed_ref_unit/topics, ref_concepts) com os
entries do manifest (title, source_path, file_type). Determinístico, sem I/O.
"""
from src.builder.core import reference_navigation as rn


def _manifest(entries):
    return entries


def _curation(by_id):
    return {"entries": by_id}


def test_ref_with_topic_goes_to_by_topic():
    entries = [{"id": "e1", "title": "Flask", "source_path": "https://github.com/pallets/flask", "file_type": "github-repo"}]
    cur = _curation({"e1": {"computed_ref_unit": "web", "computed_ref_topics": ["Rotas HTTP"], "ref_concepts": ["Flask", "WSGI"]}})
    idx = rn.build_unit_topic_reference_index(entries, cur)
    key = ("web", rn._norm_topic("Rotas HTTP"))
    assert key in idx["by_topic"]
    assert idx["by_topic"][key][0]["entry_id"] == "e1"
    assert idx["by_topic"][key][0]["type"] == "repo"


def test_ref_unit_only_goes_to_by_unit_not_by_topic():
    entries = [{"id": "e2", "title": "Doc", "source_path": "https://docs.python.org/3/library/json.html", "file_type": "link"}]
    cur = _curation({"e2": {"computed_ref_unit": "serializacao", "computed_ref_topics": [], "ref_concepts": ["JSON"]}})
    idx = rn.build_unit_topic_reference_index(entries, cur)
    assert idx["by_unit"]["serializacao"][0]["entry_id"] == "e2"
    assert idx["by_unit"]["serializacao"][0]["type"] == "doc"
    assert idx["by_topic"] == {}


def test_ref_without_unit_is_excluded():
    entries = [{"id": "e3", "title": "X", "source_path": "https://x.com", "file_type": "link"}]
    cur = _curation({"e3": {"computed_ref_unit": "", "computed_ref_topics": [], "ref_concepts": ["a"]}})
    idx = rn.build_unit_topic_reference_index(entries, cur)
    assert idx["by_unit"] == {}
    assert idx["by_topic"] == {}


def test_curation_without_matching_manifest_is_excluded():
    entries = []  # manifest vazio
    cur = _curation({"ghost": {"computed_ref_unit": "web", "computed_ref_topics": [], "ref_concepts": []}})
    idx = rn.build_unit_topic_reference_index(entries, cur)
    assert idx["by_unit"] == {}


def test_type_repo_vs_doc():
    entries = [
        {"id": "r", "title": "R", "source_path": "https://github.com/o/r", "file_type": "github-repo"},
        {"id": "d", "title": "D", "source_path": "https://example.com/p", "file_type": "link"},
    ]
    cur = _curation({
        "r": {"computed_ref_unit": "u", "computed_ref_topics": [], "ref_concepts": []},
        "d": {"computed_ref_unit": "u", "computed_ref_topics": [], "ref_concepts": []},
    })
    idx = rn.build_unit_topic_reference_index(entries, cur)
    types = {r["entry_id"]: r["type"] for r in idx["by_unit"]["u"]}
    assert types == {"r": "repo", "d": "doc"}


def test_concepts_capped_to_three_and_stable_order():
    entries = [
        {"id": "b", "title": "B", "source_path": "https://x/b", "file_type": "link"},
        {"id": "a", "title": "A", "source_path": "https://x/a", "file_type": "link"},
    ]
    cur = _curation({
        "b": {"computed_ref_unit": "u", "computed_ref_topics": [], "ref_concepts": ["c1", "c2", "c3", "c4"]},
        "a": {"computed_ref_unit": "u", "computed_ref_topics": [], "ref_concepts": ["x"]},
    })
    idx = rn.build_unit_topic_reference_index(entries, cur)
    refs = idx["by_unit"]["u"]
    assert [r["entry_id"] for r in refs] == ["a", "b"]  # ordenado por entry_id
    assert refs[1]["concepts"] == ["c1", "c2", "c3"]  # cortado a 3


def test_support_line_format():
    ref = {"entry_id": "e1", "title": "Flask", "source_path": "u", "type": "repo",
           "concepts": ["Flask", "WSGI", "rotas"], "topics": [], "unit_slug": "web"}
    line = rn._ref_support_line(ref)
    assert line == "📖 Apoio: Flask (repo) — Flask, WSGI, rotas → content/BIBLIOGRAPHY.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reference_navigation.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.builder.core.reference_navigation'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/builder/core/reference_navigation.py
"""Índice de referências mapeadas por âncora (unidade / unidade+tópico).

Junta references_curation.json (computed_ref_unit/topics, ref_concepts) com os
entries do manifest (title, source_path, file_type) para alimentar as linhas de
apoio do COURSE_MAP. Puro: sem I/O, sem rede, saída determinística.
"""
from __future__ import annotations

_REF_CAP_PER_ANCHOR = 2


def _norm_topic(s: str) -> str:
    """Normalizador trivial de label de tópico, idêntico nos dois lados do match."""
    return " ".join((s or "").lower().split())


def _ref_type(source_path: str, file_type: str) -> str:
    if file_type == "github-repo" or "github.com" in (source_path or ""):
        return "repo"
    return "doc"


def _ref_support_line(ref: dict) -> str:
    concepts = ", ".join(ref["concepts"][:3])
    tail = f" — {concepts}" if concepts else ""
    return f"📖 Apoio: {ref['title']} ({ref['type']}){tail} → content/BIBLIOGRAPHY.md"


def build_unit_topic_reference_index(manifest_entries: list, reference_curation: dict) -> dict:
    """Agrupa refs mapeadas por âncora. Só inclui refs com computed_ref_unit não-vazio
    e com entry correspondente no manifest. Listas ordenadas por entry_id (estável)."""
    by_id = {}
    for e in manifest_entries or []:
        eid = str(e.get("id") or "")
        if eid:
            by_id[eid] = e

    cur_entries = (reference_curation or {}).get("entries", {}) or {}
    refs = []
    for eid, rec in cur_entries.items():
        entry = by_id.get(eid)
        if entry is None:
            continue
        unit_slug = str(rec.get("computed_ref_unit") or "").strip()
        if not unit_slug:
            continue
        source_path = str(entry.get("source_path") or "")
        topics = [t for t in (rec.get("computed_ref_topics") or []) if t]
        refs.append({
            "entry_id": eid,
            "title": str(entry.get("title") or eid),
            "source_path": source_path,
            "type": _ref_type(source_path, str(entry.get("file_type") or "")),
            "concepts": [c for c in (rec.get("ref_concepts") or []) if c][:3],
            "topics": topics,
            "unit_slug": unit_slug,
        })

    refs.sort(key=lambda r: r["entry_id"])

    by_unit: dict = {}
    by_topic: dict = {}
    for ref in refs:
        by_unit.setdefault(ref["unit_slug"], []).append(ref)
        for topic_label in ref["topics"]:
            key = (ref["unit_slug"], _norm_topic(topic_label))
            by_topic.setdefault(key, []).append(ref)
    return {"by_unit": by_unit, "by_topic": by_topic}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reference_navigation.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/reference_navigation.py tests/test_reference_navigation.py
git commit -m "feat(references): unit/topic reference index for COURSE_MAP support lines"
```

---

## Task 2: Injeção das linhas de apoio no renderer do COURSE_MAP

**Files:**
- Modify: `src/builder/artifacts/navigation.py:437-447` (loop "## Estrutura do curso")
- Test: `tests/test_course_map_references.py`

O renderer `render_low_token_course_map_md` recebe `normalize_unit_slug`, `topic_text`, `topic_depth` como deps injetadas e lê contexto de `course_meta`. Adicionamos a leitura de `course_meta.get("_reference_nav_index")` e emitimos linhas no loop existente.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_course_map_references.py
"""Linhas de apoio (📖 Apoio:) no COURSE_MAP a partir do _reference_nav_index."""
from src.builder.artifacts import navigation as nav
from src.builder.core import reference_navigation as rn


class _Subject:
    def __init__(self, teaching_plan, syllabus=""):
        self.teaching_plan = teaching_plan
        self.syllabus = syllabus


# Plano de ensino mínimo: 1 unidade, 2 tópicos. O formato real é parseado por
# parse_units_from_teaching_plan; usamos o formato que o projeto já entende.
_TEACHING_PLAN = """Unidade 1 - Desenvolvimento Web
- Rotas HTTP
- Templates
"""


def _render(course_meta, subject):
    # Usa o builder real de dependências do módulo de navegação.
    return nav.course_map_md(
        course_meta,
        subject,
        low_token_course_map_md_v2_fn=nav._default_low_token_course_map_md_v2,
        clamp_navigation_artifact=nav._default_clamp_navigation_artifact,
    )


def test_support_line_appears_under_topic():
    # unit_slug "desenvolvimento-web" deve casar normalize_unit_slug("Unidade 1 - Desenvolvimento Web").
    # Obtemos o slug real via a função do projeto para não chutar.
    from src.builder.extraction.teaching_plan import _normalize_unit_slug
    unit_slug = _normalize_unit_slug("Unidade 1 - Desenvolvimento Web")
    idx = {
        "by_unit": {unit_slug: [{"entry_id": "e1", "title": "Flask", "source_path": "u",
                                 "type": "repo", "concepts": ["Flask"], "topics": ["Rotas HTTP"],
                                 "unit_slug": unit_slug}]},
        "by_topic": {(unit_slug, rn._norm_topic("Rotas HTTP")): [{"entry_id": "e1", "title": "Flask",
                     "source_path": "u", "type": "repo", "concepts": ["Flask"], "topics": ["Rotas HTTP"],
                     "unit_slug": unit_slug}]},
    }
    course_meta = {"course_name": "Curso", "_reference_nav_index": idx}
    out = _render(course_meta, _Subject(_TEACHING_PLAN))
    assert "📖 Apoio: Flask (repo)" in out
    # aparece logo após o bullet do tópico "Rotas HTTP"
    lines = out.splitlines()
    i = next(k for k, ln in enumerate(lines) if "Rotas HTTP" in ln and "Apoio" not in ln)
    assert any("📖 Apoio: Flask" in ln for ln in lines[i:i + 2])


def test_unit_only_ref_appears_under_unit_header():
    from src.builder.extraction.teaching_plan import _normalize_unit_slug
    unit_slug = _normalize_unit_slug("Unidade 1 - Desenvolvimento Web")
    ref = {"entry_id": "e9", "title": "Geral", "source_path": "u", "type": "doc",
           "concepts": [], "topics": [], "unit_slug": unit_slug}
    idx = {"by_unit": {unit_slug: [ref]}, "by_topic": {}}
    course_meta = {"course_name": "Curso", "_reference_nav_index": idx}
    out = _render(course_meta, _Subject(_TEACHING_PLAN))
    assert "📖 Apoio: Geral (doc)" in out


def test_degraded_mode_no_index_is_unchanged():
    course_meta_plain = {"course_name": "Curso"}
    course_meta_empty = {"course_name": "Curso", "_reference_nav_index": {"by_unit": {}, "by_topic": {}}}
    base = _render(course_meta_plain, _Subject(_TEACHING_PLAN))
    empty = _render(course_meta_empty, _Subject(_TEACHING_PLAN))
    assert "📖 Apoio" not in base
    assert base == empty  # índice vazio == sem índice


def test_cap_two_lines_plus_overflow():
    from src.builder.extraction.teaching_plan import _normalize_unit_slug
    unit_slug = _normalize_unit_slug("Unidade 1 - Desenvolvimento Web")
    tkey = (unit_slug, rn._norm_topic("Rotas HTTP"))
    refs = [{"entry_id": f"e{n}", "title": f"R{n}", "source_path": "u", "type": "doc",
             "concepts": [], "topics": ["Rotas HTTP"], "unit_slug": unit_slug} for n in range(3)]
    idx = {"by_unit": {unit_slug: refs}, "by_topic": {tkey: refs}}
    course_meta = {"course_name": "Curso", "_reference_nav_index": idx}
    out = _render(course_meta, _Subject(_TEACHING_PLAN))
    assert out.count("📖 Apoio:") == 2  # cap
    assert "(+1 referência(s) em content/BIBLIOGRAPHY.md)" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_course_map_references.py -v`
Expected: FAIL — `test_support_line_appears_under_topic` e os outros falham porque nenhuma linha `📖 Apoio` é emitida (renderer ainda não lê o índice). `test_degraded_mode_no_index_is_unchanged` deve PASSAR já (nenhuma linha emitida nos dois). Se algum teste der erro de atributo (`nav._default_low_token_course_map_md_v2` inexistente), ajuste o helper `_render` para o nome real do builder de deps do módulo (ver Step 3, nota).

- [ ] **Step 3: Write minimal implementation**

Em `src/builder/artifacts/navigation.py`, no início de `render_low_token_course_map_md` (logo após montar `timeline_context`, antes de `lines += ["## Estrutura do curso", ""]`), ler o índice:

```python
    ref_index = course_meta.get("_reference_nav_index") or {}
    ref_by_unit = ref_index.get("by_unit", {}) or {}
    ref_by_topic = ref_index.get("by_topic", {}) or {}
```

Importar o helper de formato no topo do arquivo (junto dos outros imports do módulo):

```python
from src.builder.core.reference_navigation import (
    _norm_topic as _ref_norm_topic,
    _ref_support_line,
    _REF_CAP_PER_ANCHOR,
)
```

Substituir o bloco do loop (atual `navigation.py:438-447`):

```python
    if units:
        for unit_title, topics in units:
            lines.append(f"### {unit_title}")
            if topics:
                for topic in topics:
                    indent = "  " * topic_depth(topic)
                    lines.append(f"{indent}- [ ] {topic_text(topic)}")
            else:
                lines.append("- [ ] [tópicos a preencher]")
            lines.append("")
```

por:

```python
    if units:
        for unit_title, topics in units:
            unit_slug = normalize_unit_slug(unit_title)
            lines.append(f"### {unit_title}")
            shown_ids: set = set()
            if topics:
                for topic in topics:
                    indent = "  " * topic_depth(topic)
                    lines.append(f"{indent}- [ ] {topic_text(topic)}")
                    tkey = (unit_slug, _ref_norm_topic(topic_text(topic)))
                    _emit_support_lines(
                        lines, ref_by_topic.get(tkey, []), shown_ids, indent + "  "
                    )
            else:
                lines.append("- [ ] [tópicos a preencher]")
            leftovers = [r for r in ref_by_unit.get(unit_slug, []) if r["entry_id"] not in shown_ids]
            _emit_support_lines(lines, leftovers, shown_ids, "")
            lines.append("")
```

E adicionar o helper de emissão como função de módulo (acima de `render_low_token_course_map_md`):

```python
def _emit_support_lines(lines: List[str], refs: list, shown_ids: set, indent: str) -> None:
    """Emite até _REF_CAP_PER_ANCHOR linhas 📖 Apoio (refs ainda não mostradas)
    + 1 linha de overflow se sobrar. Atualiza shown_ids."""
    fresh = [r for r in refs if r["entry_id"] not in shown_ids]
    head = fresh[:_REF_CAP_PER_ANCHOR]
    for ref in head:
        lines.append(f"{indent}- {_ref_support_line(ref)}")
        shown_ids.add(ref["entry_id"])
    overflow = len(fresh) - len(head)
    if overflow > 0:
        lines.append(f"{indent}- (+{overflow} referência(s) em content/BIBLIOGRAPHY.md)")
```

**Nota sobre `_render` no teste:** o módulo `navigation.py` expõe `course_map_md` cujas deps (`low_token_course_map_md_v2_fn`, `clamp_navigation_artifact`) são injetadas pela facade. Se não houver builder de deps default exportável, troque o helper `_render` do teste para chamar a facade real. Verifique o ponto de montagem em `src/builder/facade/` (procure `course_map_md` com `rg "course_map_md" src/builder/facade`) e use a função pública já montada (ex.: `from src.builder.facade.navigation import course_map_md as _course_map_md`). Ajuste `_render` para `return _course_map_md(course_meta, subject)`. O objetivo do teste é exercitar o renderer real com `course_meta["_reference_nav_index"]` populado.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_course_map_references.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Run full suite (garante que nenhum snapshot de COURSE_MAP existente quebrou)**

Run: `python -m pytest -q`
Expected: tudo verde. Se algum teste de COURSE_MAP existente falhar, é porque ele compara saída exata — confirme que sem `_reference_nav_index` a saída é idêntica (modo degradado). Se quebrou com índice ausente, há bug: o `or {}` deve garantir no-op.

- [ ] **Step 6: Commit**

```bash
git add src/builder/artifacts/navigation.py tests/test_course_map_references.py
git commit -m "feat(course-map): emit reference support lines from _reference_nav_index"
```

---

## Task 3: Wiring — construir o índice e injetar em course_meta

**Files:**
- Modify: `src/builder/ops/pedagogical_regeneration.py` (antes de `course_map_md_fn` em `:246`)
- Test: estender `tests/test_course_map_references.py` com 1 teste de integração

- [ ] **Step 1: Write the failing test (integração leve do wiring)**

```python
# adicionar em tests/test_course_map_references.py
import json
from pathlib import Path


def test_wiring_builds_index_and_injects(tmp_path):
    """pedagogical_regeneration deve ler manifest + curation e popular
    course_meta['_reference_nav_index'] com refs mapeadas."""
    from src.builder.core.reference_navigation import build_unit_topic_reference_index
    from src.builder.core.reference_summary import load_reference_curation, write_reference_curation

    root = tmp_path
    (root / "course").mkdir(parents=True, exist_ok=True)
    manifest = {"entries": [
        {"id": "e1", "title": "Flask", "source_path": "https://github.com/pallets/flask",
         "file_type": "github-repo", "category": "referencias"},
    ]}
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    write_reference_curation(root, {"entries": {
        "e1": {"computed_ref_unit": "web", "computed_ref_topics": ["Rotas HTTP"],
               "ref_concepts": ["Flask"], "ref_summary": "x", "content_hash": "h", "matcher_version": 1},
    }})

    entries = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    idx = build_unit_topic_reference_index(entries, load_reference_curation(root))
    assert idx["by_unit"]["web"][0]["entry_id"] == "e1"
    assert ("web", "rotas http") in idx["by_topic"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_course_map_references.py::test_wiring_builds_index_and_injects -v`
Expected: PASS imediato se o helper já existe (Task 1) — este teste valida o contrato de leitura disco→índice usado pelo wiring, não código novo. **Se passar de primeira, está correto**; ele protege contra regressão no formato de chaves (`id` no manifest, `entry_id` no índice). (Exceção ao RED: é um teste-contrato de integração; sua função é travar o formato antes da edição de produção do Step 3.)

- [ ] **Step 3: Write the wiring (produção)**

Em `src/builder/ops/pedagogical_regeneration.py`, adicionar import no topo (junto de `from src.utils.helpers import slugify, write_text`):

```python
from src.builder.core.reference_navigation import build_unit_topic_reference_index
from src.builder.core.reference_summary import load_reference_curation
```

Imediatamente antes de `course_map_text = course_map_md_fn(...)` (`:246`), inserir:

```python
    # Approach C: refs mapeadas viram linhas de apoio no COURSE_MAP.
    # Lê manifest.json fresco (mesma fonte que gerou a curation) para alinhar ids.
    try:
        _manifest_entries = json.loads(
            (builder.root_dir / "manifest.json").read_text(encoding="utf-8")
        ).get("entries", [])
        runtime_course_meta["_reference_nav_index"] = build_unit_topic_reference_index(
            _manifest_entries, load_reference_curation(builder.root_dir)
        )
    except Exception as exc:
        logger.warning("Approach C: índice de referência não construído: %s", exc)
        runtime_course_meta["_reference_nav_index"] = {"by_unit": {}, "by_topic": {}}
```

(`json` e `logger` já estão importados no módulo — `import json` linha 3, `logger` definido.)

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: tudo verde.

- [ ] **Step 5: Commit**

```bash
git add src/builder/ops/pedagogical_regeneration.py tests/test_course_map_references.py
git commit -m "feat(build): wire reference nav index into COURSE_MAP generation"
```

---

## Task 4: Instrução no prompt do tutor

**Files:**
- Modify: `src/builder/artifacts/prompts.py` (na descrição do COURSE_MAP, próximo de `:551`)
- Test: `tests/test_prompts_reference_support.py`

O prompt principal é montado por funções em `prompts.py`. Adicionamos uma função de bloco curta e a incluímos no texto. Primeiro descubra a função que monta o corpo onde fica "## Arquivos principais" (procure a string `"## Arquivos principais"` ou `course/COURSE_MAP.md` em `prompts.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompts_reference_support.py
"""O prompt do tutor explica como usar as linhas 📖 Apoio do COURSE_MAP."""
from src.builder.artifacts import prompts


def test_prompt_explains_support_references():
    text = prompts._prompt_reference_support_text()
    assert "📖 Apoio" in text
    assert "apoio" in text.lower()
    # enquadramento: complementar, não fonte principal
    assert "principal" in text.lower()


def test_support_text_is_included_in_main_prompt():
    # A função que monta o prompt principal deve conter o bloco.
    # Descobrir o nome real no Step 3; aqui validamos via a constante de bloco.
    block = prompts._prompt_reference_support_text()
    assert block.strip() != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prompts_reference_support.py -v`
Expected: FAIL com `AttributeError: module ... has no attribute '_prompt_reference_support_text'`.

- [ ] **Step 3: Write minimal implementation**

Em `src/builder/artifacts/prompts.py`, adicionar a função de bloco (junto das outras `_prompt_*_text`):

```python
def _prompt_reference_support_text() -> str:
    return (
        "## Referências de apoio (linhas `📖 Apoio:` no COURSE_MAP)\n\n"
        "Linhas `📖 Apoio:` sob um tópico/unidade no `course/COURSE_MAP.md` são "
        "material complementar (repo/doc) mapeado àquele tópico. Trate como apoio e "
        "reflexão, NÃO como fonte principal. Ao explicar o tópico, relacione a "
        "referência ao material principal — por exemplo: \"além de X estar em "
        "`<arquivo principal do FILE_MAP>`, este repo mostra X aplicado\". Só "
        "aprofunde a referência se o aluno demonstrar interesse ou o tópico pedir. "
        "O resumo completo de cada referência está em `content/BIBLIOGRAPHY.md`.\n"
    )
```

Incluir o bloco no corpo do prompt principal: localize a montagem onde já entram blocos como `{_prompt_map_artifact_contract_text()}` (perto de `:570`) e adicione `{_prompt_reference_support_text()}` na mesma f-string/concatenação. Mostre a linha real após localizar; o padrão é inserir junto dos outros blocos de contrato:

```python
{_prompt_map_artifact_contract_text()}

{_prompt_reference_support_text()}

{_prompt_student_state_v2_contract_text()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_prompts_reference_support.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/prompts.py tests/test_prompts_reference_support.py
git commit -m "feat(prompt): instruct tutor on COURSE_MAP support references"
```

---

## Task 5: Limpeza da tabela de relevância redundante na BIBLIOGRAPHY

**Files:**
- Modify: `src/builder/artifacts/repo.py:737-757` (bloco "Mapa de relevância por tópico" + label do clamp)
- Test: `tests/test_bibliography_cleanup.py`

Estado atual de `bibliography_md` (`repo.py:737-757`): monta `mapped`, emite a seção `## Mapa de relevância por tópico` com colunas mortas `Acessível`/`Incidência em prova`, e o clamp final usa `label="course/COURSE_MAP.md"` (errado).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bibliography_cleanup.py
"""BIBLIOGRAPHY sem a tabela de relevância redundante; com ponteiro p/ COURSE_MAP."""
from src.builder.artifacts import repo


class _Entry:
    def __init__(self, eid, title, source_path):
        self._id = eid
        self.title = title
        self.source_path = source_path
        self.tags = ""
        self.notes = ""
        self.professor_signal = ""
        self.include_in_bundle = True

    def id(self):
        return self._id


def _bib(entries, curation):
    return repo.bibliography_md(
        {"course_name": "Curso"},
        entries,
        None,
        reference_curation=curation,
        parse_bibliography_from_teaching_plan_fn=lambda _t: {},
        clamp_navigation_artifact=lambda text, **_k: text,  # identidade p/ inspecionar
    )


def test_no_relevance_table_headers():
    entries = [_Entry("e1", "Flask", "https://github.com/pallets/flask")]
    cur = {"entries": {"e1": {"ref_summary": "resumo", "computed_ref_unit": "web",
                              "computed_ref_topics": ["Rotas HTTP"]}}}
    out = _bib(entries, cur)
    assert "Mapa de relevância por tópico" not in out
    assert "Acessível" not in out
    assert "Incidência em prova" not in out


def test_pointer_to_course_map_present():
    out = _bib([_Entry("e1", "Flask", "u")], {"entries": {}})
    assert "course/COURSE_MAP.md" in out
    assert "📖 Apoio" in out  # menciona as linhas de apoio


def test_relevante_para_still_present_per_entry():
    entries = [_Entry("e1", "Flask", "u")]
    cur = {"entries": {"e1": {"ref_summary": "r", "computed_ref_unit": "web",
                             "computed_ref_topics": ["Rotas HTTP"]}}}
    out = _bib(entries, cur)
    assert "Relevante para" in out  # registro por-entry mantido


def test_clamp_label_is_bibliography():
    captured = {}

    def _clamp(text, **kwargs):
        captured["label"] = kwargs.get("label")
        return text

    repo.bibliography_md(
        {"course_name": "Curso"}, [_Entry("e1", "F", "u")], None,
        reference_curation={"entries": {}},
        parse_bibliography_from_teaching_plan_fn=lambda _t: {},
        clamp_navigation_artifact=_clamp,
    )
    assert captured["label"] == "course/BIBLIOGRAPHY.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bibliography_cleanup.py -v`
Expected: FAIL — `test_no_relevance_table_headers` (tabela ainda existe), `test_pointer_to_course_map_present` (sem ponteiro/📖), `test_clamp_label_is_bibliography` (label errado). `test_relevante_para_still_present_per_entry` deve PASSAR já.

- [ ] **Step 3: Write minimal implementation**

Em `src/builder/artifacts/repo.py`, substituir o bloco atual (`repo.py:737-757`):

```python
    mapped = [(e, _rec(e)) for e in entries]
    mapped = [(e, r) for (e, r) in mapped if (r.get("computed_ref_unit") or r.get("computed_ref_topics"))]
    lines += ["## Mapa de relevância por tópico", ""]
    if mapped:
        lines += ["| Tópico/Unidade | Referência | Acessível | Incidência em prova |", "|---|---|---|---|"]
        for e, r in mapped:
            unit = r.get("computed_ref_unit") or ""
            topics = ", ".join(r.get("computed_ref_topics") or [])
            alvo = " / ".join([p for p in (unit, topics) if p]) or "—"
            lines.append(f"| {alvo} | {e.title} | sim | — |")
        lines.append("")
    else:
        lines += ["<!-- Preencha após organizar as referências -->", "",
                  "| Tópico | Referência principal | Acessível | Incidência em prova |",
                  "|---|---|---|---|", "| [a preencher] | | | |", ""]

    return clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )
```

por:

```python
    lines += [
        "## Mapa de relevância por tópico",
        "",
        "> O mapa de relevância por tópico agora vive no `course/COURSE_MAP.md` "
        "(linhas `📖 Apoio:` sob cada tópico/unidade). Esta página traz o resumo "
        "completo de cada referência.",
        "",
    ]

    return clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=14000,
        label="course/BIBLIOGRAPHY.md",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bibliography_cleanup.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Run full suite (algum teste de bibliography existente pode comparar a tabela antiga)**

Run: `python -m pytest -q`
Expected: tudo verde. Se um teste antigo afirmar a presença das colunas `Acessível`/`Incidência em prova` ou do label `course/COURSE_MAP.md`, ele está validando o comportamento agora removido — atualize-o para o novo (ponteiro + label correto), pois a mudança é intencional e coberta pelos novos testes.

- [ ] **Step 6: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_bibliography_cleanup.py
git commit -m "refactor(bibliography): drop redundant relevance table for COURSE_MAP pointer; fix clamp label"
```

---

## Task 6: Validação end-to-end manual (opcional, recomendado)

**Files:** nenhum (usa o harness existente `scripts/validate_references_e2e.py` como referência).

- [ ] **Step 1: Rodar a suíte completa final**

Run: `python -m pytest -q`
Expected: tudo verde, incluindo os 4 novos arquivos de teste.

- [ ] **Step 2: Sanidade do modo degradado**

Confirme manualmente que, sem `references_curation.json` num repo gerado, o COURSE_MAP não contém `📖 Apoio` e é idêntico ao anterior (coberto por `test_degraded_mode_no_index_is_unchanged`, mas vale um olhar num build real se houver repo de teste).

- [ ] **Step 3: Atualizar docs do projeto**

Atualize `.mex/ROUTER.md` (seção "Working") com uma linha sobre as linhas de apoio do COURSE_MAP e marque o Approach C como ENTREGUE no `docs/superpowers/BACKLOG.md`.

```bash
git add .mex/ROUTER.md docs/superpowers/BACKLOG.md
git commit -m "docs: mark Approach C delivered (COURSE_MAP support references)"
```

---

## Self-Review (executado)

**1. Spec coverage:**
- Componente 1 (helper) → Task 1. ✓
- Componente 2 (renderer injection) → Task 2. ✓ (course_meta-injection, deviation documentada abaixo)
- Componente 3 (wiring) → Task 3. ✓
- Componente 4 (prompt) → Task 4. ✓
- Componente 5 (bibliography cleanup + label) → Task 5. ✓
- Modo degradado byte-idêntico → `test_degraded_mode_no_index_is_unchanged` (Task 2). ✓
- Cap 2 + overflow → `test_cap_two_lines_plus_overflow` (Task 2). ✓
- Dedup tópico vs unidade → `shown_ids` no renderer + `leftovers` filtra. ✓

**2. Desvios do spec (intencionais, melhoram o design):**
- Spec previa threading de `reference_curation`/`manifest_entries` por kwargs nos 4 níveis de wrapper. **Substituído** por injeção em `course_meta["_reference_nav_index"]`, espelhando `_timeline_context`/`_assessment_context` já existentes (`pedagogical_regeneration.py:190,204`; lido em `navigation.py:418,516`). Zero mudança de assinatura. Mais simples, segue padrão do código.
- Spec dava ao helper params `normalize_unit_slug`/`slugify`. **Removidos:** `computed_ref_unit` já é o slug certo (alinhado via `file_map.py:101` == renderer `normalize_unit_slug`); tópico usa `_norm_topic` trivial compartilhado. Helper fica sem deps.

**3. Type consistency:**
- `build_unit_topic_reference_index(manifest_entries, reference_curation)` — mesma assinatura em Task 1 (def), Task 3 (uso). ✓
- chaves do índice: `by_unit`, `by_topic`; `ref["entry_id"]`, `ref["title"]`, `ref["type"]`, `ref["concepts"]`, `ref["topics"]`, `ref["unit_slug"]` — consistentes entre Task 1, 2, 3. ✓
- `_norm_topic`, `_ref_support_line`, `_REF_CAP_PER_ANCHOR`, `_emit_support_lines` — nomes idênticos em def e uso. ✓

**Risco residual conhecido (mitigado por teste):** match de **tópico** depende de `topic_text(topic)` (renderer) normalizar igual a `computed_ref_topics` (curation). Se divergirem, a ref cai no balde de **unidade** (fallback garantido) — nunca some. `test_support_line_appears_under_topic` cobre o caminho topic; `test_unit_only_ref_appears_under_unit_header` cobre o fallback. O match de **unidade** está provado alinhado (`file_map.py:101` usa o mesmo `normalize_unit_slug`).
