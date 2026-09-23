# Block-match para PDFs / imagens / exercícios — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer PDFs, imagens e exercícios ganharem atribuição de bloco do cronograma de forma confiável (hoje só código ganha), medindo cobertura via `CRONOGRAMA_HEALTH.md`.

**Architecture:** Híbrido em 3 camadas — (C1) reforço de sinal determinístico, (C2) resumo Gemini só no resíduo (cap+cache), (C3) curadoria manual já existente. Precedido por uma Fase 0 de consolidação (thresholds, fórmula de confidence, normalize único, núcleo de summarização compartilhado) para não compor dívida.

**Tech Stack:** Python 3.11, pytest, jsonschema; Gemini opcional (extra `code-summarization`) reusando a infra de `code_summarization.py`.

**Spec:** `docs/superpowers/specs/2026-06-03-block-match-materiais-design.md`

---

## Convenções

- Rodar testes: `python -m pytest <path> -q`. Baseline atual: **4 falhas pré-existentes** (`test_low_color_math_image_is_kept_by_permissive_policy`, `test_parallel_image_extraction_runs_while_marker_remains_advanced_backend`, `test_ignores_accidental_estado_match_in_logic_file`, `test_auto_map_entry_unit_matches_exercise_to_recursive_definitions`) — env `pymupdf` + matcher legado. NÃO são regressão; ignorar.
- Commits: mensagem normal (não-caveman). Não pular hooks.
- Branch: `new-features` (já ativa). Não commitar em `main`.

---

## Estrutura de arquivos

**Criar:**
- `src/builder/text/__init__.py` — pacote.
- `src/builder/text/normalize.py` — fonte única de `normalize_match_text`.
- `src/builder/routing/thresholds.py` — constantes de limiar + `margin_confidence`.
- `src/builder/core/summary_core.py` — núcleo de summarização (client+cache+assign) reusável por código e material.
- `src/builder/artifacts/cronograma_health.py` — métrica de cobertura + `cronograma_health_md`.
- `scripts/validate_materials.py` — métrica/gate de cobertura (espelha `validate_timeline.py`).
- Testes: `tests/test_text_normalize.py`, `tests/test_routing_thresholds.py`, `tests/test_entry_signals_materials.py`, `tests/test_material_residual.py`, `tests/test_cronograma_health.py`.

**Modificar:**
- `src/builder/extraction/entry_signals.py` — nova fonte `image_description_text`; re-exporta normalize do módulo compartilhado.
- `src/builder/artifacts/navigation.py` — fallback de markdown p/ descrição de imagem.
- `src/builder/routing/file_map.py` — consome novo sinal; usa thresholds centralizados.
- `src/builder/timeline/index.py` — usa `margin_confidence` + thresholds.
- `src/builder/extraction/content_taxonomy.py` — usa normalize compartilhado.
- `src/builder/ops/pedagogical_regeneration.py` — chama summarizer residual + escreve HEALTH.
- Arquivos com `normalize_match_text` duplicada (`artifacts/pedagogy.py`, `timeline/signals.py`, `vision/card_evidence.py`, `extraction/image_markdown.py`) — re-importar do compartilhado.

---

# FASE 0 — Consolidação (base limpa)

## Task 0.1: Módulo de normalização único

**Files:**
- Create: `src/builder/text/__init__.py`
- Create: `src/builder/text/normalize.py`
- Test: `tests/test_text_normalize.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_text_normalize.py
from src.builder.text.normalize import normalize_match_text


def test_strips_accents_and_lowercases():
    assert normalize_match_text("Lógica de Predicados") == "logica de predicados"


def test_collapses_whitespace_and_symbols():
    assert normalize_match_text("P1 - Prova!!  final") == "p1 prova final"


def test_typo_fix_propocional():
    assert normalize_match_text("propocional") == "proposicional"


def test_empty_and_none():
    assert normalize_match_text("") == ""
    assert normalize_match_text(None) == ""
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_text_normalize.py -q`
Expected: FAIL (ModuleNotFoundError: src.builder.text.normalize)

- [ ] **Step 3: Criar o pacote + módulo**

```python
# src/builder/text/__init__.py
```

```python
# src/builder/text/normalize.py
from __future__ import annotations

import re
import unicodedata


def normalize_match_text(text: str) -> str:
    """NFKD + remove acentos + lower + so [a-z0-9 ]. Fonte unica do projeto.

    Antes duplicada em ~6 modulos; agora todos re-importam daqui.
    """
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("propocional", "proposicional")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()
```

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_text_normalize.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/text/__init__.py src/builder/text/normalize.py tests/test_text_normalize.py
git commit -m "refactor(text): normalize_match_text como fonte unica"
```

## Task 0.2: Re-apontar `entry_signals.normalize_match_text` p/ o compartilhado

**Files:**
- Modify: `src/builder/extraction/entry_signals.py:12-18`
- Test: `tests/test_text_normalize.py` (adiciona equivalência)

- [ ] **Step 1: Teste de equivalência (garante zero mudança de comportamento)**

```python
# anexar em tests/test_text_normalize.py
def test_entry_signals_reexports_same_normalize():
    from src.builder.extraction.entry_signals import normalize_match_text as es_norm
    from src.builder.text.normalize import normalize_match_text as canon
    for s in ["Lógica", "P1 - Prova", "Máquina de Turing", "propocional", ""]:
        assert es_norm(s) == canon(s)
```

- [ ] **Step 2: Rodar p/ falhar/passar parcial**

Run: `python -m pytest tests/test_text_normalize.py::test_entry_signals_reexports_same_normalize -q`
Expected: PASS (já é idêntica; o teste trava regressão antes do refactor)

- [ ] **Step 3: Substituir a definição local por re-import**

Em `src/builder/extraction/entry_signals.py`, remover as linhas 12-18 (a `def normalize_match_text`) e, logo após os imports do topo, adicionar:

```python
from src.builder.text.normalize import normalize_match_text  # noqa: F401  (re-export)
```

(Manter o `import re` e `import unicodedata` apenas se ainda usados no arquivo — `re` continua usado em `_extract_markdown_headings`/`_DATE_PREFIX_RE`; `unicodedata` pode sair se não houver outro uso.)

- [ ] **Step 4: Rodar suite ampla p/ garantir sem regressão**

Run: `python -m pytest tests/ -q`
Expected: 4 failed (baseline), demais passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/extraction/entry_signals.py tests/test_text_normalize.py
git commit -m "refactor(text): entry_signals reusa normalize compartilhado"
```

## Task 0.3: Re-apontar os demais módulos com normalize duplicada

**Files:**
- Modify: `src/builder/artifacts/pedagogy.py`, `src/builder/timeline/signals.py`, `src/builder/vision/card_evidence.py`, `src/builder/extraction/image_markdown.py`, `src/builder/timeline/index.py` (`_normalize_match_text`), `src/builder/extraction/content_taxonomy.py` (variante divergente — ver R4)

- [ ] **Step 1: Teste de equivalência por módulo (trava antes de mexer)**

```python
# tests/test_text_normalize.py (anexar)
import importlib
import pytest

@pytest.mark.parametrize("mod,attr", [
    ("src.builder.artifacts.pedagogy", "normalize_match_text"),
    ("src.builder.timeline.signals", "normalize_match_text"),
    ("src.builder.vision.card_evidence", "normalize_match_text"),
    ("src.builder.extraction.image_markdown", "normalize_match_text"),
    ("src.builder.timeline.index", "_normalize_match_text"),
])
def test_modules_match_canonical(mod, attr):
    from src.builder.text.normalize import normalize_match_text as canon
    m = importlib.import_module(mod)
    fn = getattr(m, attr)
    for s in ["Lógica de Predicados", "P1 - Prova!!", "Hierarquia de Chomsky", ""]:
        assert fn(s) == canon(s), f"{mod}.{attr} diverge em {s!r}"
```

- [ ] **Step 2: Rodar p/ ver quais divergem**

Run: `python -m pytest tests/test_text_normalize.py::test_modules_match_canonical -q`
Expected: a maioria PASS; `content_taxonomy` (variante com `-`) pode falhar — por isso NÃO está no parametrize acima. Anotar quais batem exatamente.

- [ ] **Step 3: Substituir cada def idêntica por re-import**

Para cada módulo cujo teste passou, remover a `def` local e adicionar no topo:

```python
from src.builder.text.normalize import normalize_match_text
```

Em `src/builder/timeline/index.py`, a função privada é `_normalize_match_text`. Manter o nome privado como alias:

```python
from src.builder.text.normalize import normalize_match_text as _normalize_match_text
```

**`content_taxonomy.py` (variante divergente):** NÃO consolidar nesta task. A variante normaliza `-` diferente; mudar pode alterar matching de tag. Deixar como está e abrir nota no commit (consolidação dela exige regressão dedicada — fora do escopo de 0.3).

- [ ] **Step 4: Rodar suite ampla**

Run: `python -m pytest tests/ -q`
Expected: 4 failed (baseline), demais passed

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(text): consolida normalize_match_text (exceto variante de content_taxonomy)"
```

## Task 0.4: Módulo de thresholds + `margin_confidence`

**Files:**
- Create: `src/builder/routing/thresholds.py`
- Test: `tests/test_routing_thresholds.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_routing_thresholds.py
from src.builder.routing.thresholds import margin_confidence, T


def test_margin_confidence_formula():
    # (winner - runner) + winner*k, clamp 0..1
    assert margin_confidence(2.0, 1.0, k=0.18) == 1.0  # 1.0 + 0.36 -> clamp 1.0
    assert round(margin_confidence(1.2, 1.0, k=0.18), 3) == round((0.2) + 1.2 * 0.18, 3)
    assert margin_confidence(0.0, 0.0, k=0.18) == 0.0


def test_thresholds_present():
    # limiares nomeados centralizados
    assert T.UNIT_TAG == 0.65
    assert T.SUBUNIT_TAG == 0.60
    assert T.BLOCO_TAG == 0.50
    assert T.BLOCK_UNIT_MIN_WINNER == 1.0
    assert T.BLOCK_UNIT_MIN_GAP == 0.35
    assert T.VOTE_DOMINANCE == 0.60
    assert T.MATERIAL_COVERAGE_MIN == 0.70  # gate de cobertura (Fase 4)
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_routing_thresholds.py -q`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Criar o módulo**

```python
# src/builder/routing/thresholds.py
from __future__ import annotations

from dataclasses import dataclass


def margin_confidence(winner: float, runner_up: float, *, k: float) -> float:
    """Confidence por margem: (winner - runner) + winner*k, clamp [0,1].

    Consolida a formula antes duplicada 4x (K=0.18 em 3 lugares, 0.20 em 1).
    """
    raw = (float(winner) - float(runner_up)) + (float(winner) * float(k))
    return min(1.0, max(0.0, raw))


@dataclass(frozen=True)
class _Thresholds:
    # tags gerenciadas (content_taxonomy.resolve_unit_block_tags)
    UNIT_TAG: float = 0.65
    SUBUNIT_TAG: float = 0.60
    BLOCO_TAG: float = 0.50
    # bloco -> unidade (timeline._assign_timeline_block_to_unit)
    BLOCK_UNIT_MIN_WINNER: float = 1.0
    BLOCK_UNIT_MIN_GAP: float = 0.35
    # voto de unidade (timeline._vote_unit_from_topic_candidates)
    VOTE_DOMINANCE: float = 0.60
    VOTE_MIN_SCORE: float = 0.10
    # K da formula de margem (padrao). Topico usa 0.20 historicamente.
    MARGIN_K: float = 0.18
    MARGIN_K_TOPIC: float = 0.20
    # cobertura de material (Fase 4, gate opcional)
    MATERIAL_COVERAGE_MIN: float = 0.70


T = _Thresholds()
```

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_routing_thresholds.py -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/thresholds.py tests/test_routing_thresholds.py
git commit -m "feat(routing): thresholds centralizados + margin_confidence"
```

## Task 0.5: Usar `margin_confidence` em `_assign_timeline_block_to_unit`

**Files:**
- Modify: `src/builder/timeline/index.py:1041-1042` (a linha do `confidence = min(1.0, max(0.0, (winner_score - runner_up_score) + (winner_score * 0.18)))`)
- Test: `tests/test_timeline_kinds.py` (já cobre vote; adicionar verificação de paridade)

- [ ] **Step 1: Teste de paridade (resultado idêntico antes/depois)**

```python
# tests/test_routing_thresholds.py (anexar)
def test_margin_matches_old_inline_018():
    # reproduz a formula inline antiga p/ K=0.18
    winner, runner = 1.5, 0.9
    old = min(1.0, max(0.0, (winner - runner) + (winner * 0.18)))
    from src.builder.routing.thresholds import margin_confidence
    assert margin_confidence(winner, runner, k=0.18) == old
```

- [ ] **Step 2: Rodar p/ passar (trava equivalência)**

Run: `python -m pytest tests/test_routing_thresholds.py::test_margin_matches_old_inline_018 -q`
Expected: PASS

- [ ] **Step 3: Substituir o inline pela helper**

Em `src/builder/timeline/index.py`, no topo importar:

```python
from src.builder.routing.thresholds import margin_confidence, T
```

Trocar a linha 1041-1042:

```python
    confidence = margin_confidence(winner_score, runner_up_score, k=T.MARGIN_K)
    return winner.get("slug", ""), confidence
```

E o guard logo acima (linha ~1038) trocar literais por constantes:

```python
    if winner_score < T.BLOCK_UNIT_MIN_WINNER or abs(winner_score - runner_up_score) < T.BLOCK_UNIT_MIN_GAP:
        return "", 0.0
```

- [ ] **Step 4: Rodar testes de timeline**

Run: `python -m pytest tests/test_timeline_kinds.py tests/test_file_map_unit_mapping.py -q`
Expected: mesmo resultado de antes (1 falha pré-existente em file_map; timeline passa)

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py tests/test_routing_thresholds.py
git commit -m "refactor(timeline): _assign_timeline_block_to_unit usa margin_confidence + thresholds"
```

## Task 0.6: Núcleo de summarização compartilhado (esqueleto)

**Files:**
- Create: `src/builder/core/summary_core.py`
- Test: `tests/test_material_residual.py`

> Objetivo: extrair o padrão "client Gemini + cache JSON + assign-to-block" para ser reusado por código (existente) e material (Fase 4). Nesta task só criamos o núcleo genérico de cache + assign determinístico (sem mover o code_summarization ainda — evita refactor arriscado num passo só).

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_material_residual.py
import json
from src.builder.core.summary_core import (
    load_summary_cache, write_summary_cache, assign_concepts_to_block,
)


def test_cache_roundtrip(tmp_path):
    write_summary_cache(tmp_path, "material_curation.json", {"version": 1, "entries": {"e1": {"x": 1}}})
    data = load_summary_cache(tmp_path, "material_curation.json")
    assert data["entries"]["e1"]["x"] == 1


def test_cache_missing_returns_empty(tmp_path):
    assert load_summary_cache(tmp_path, "material_curation.json") == {"version": 1, "entries": {}}


def test_assign_concepts_picks_best_block():
    blocks = [
        {"id": "bloco-01", "topic_text": "logica de predicados", "primary_topic_label": "Logica"},
        {"id": "bloco-02", "topic_text": "maquina de turing", "primary_topic_label": "Turing"},
    ]
    bid, conf = assign_concepts_to_block(["maquina", "turing"], blocks)
    assert bid == "bloco-02"
    assert conf > 0
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_material_residual.py -q`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Criar o núcleo**

```python
# src/builder/core/summary_core.py
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from src.builder.text.normalize import normalize_match_text


def load_summary_cache(repo_dir: Path, filename: str) -> dict:
    path = Path(repo_dir) / filename
    if not path.exists():
        return {"version": 1, "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("entries", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "entries": {}}


def write_summary_cache(repo_dir: Path, filename: str, data: dict) -> None:
    path = Path(repo_dir) / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def assign_concepts_to_block(concepts: List[str], blocks: list) -> Tuple[str, float]:
    """Casa conceitos (tokens normalizados) contra blocos por overlap. Deterministico.

    Retorna (block_id, confidence). ("", 0.0) se nada relevante.
    """
    concept_tokens = set()
    for c in concepts or []:
        concept_tokens.update(t for t in normalize_match_text(str(c)).split() if len(t) >= 4)
    if not concept_tokens:
        return "", 0.0

    scored = []
    for blk in blocks or []:
        hay = normalize_match_text(
            f"{blk.get('topic_text','')} {blk.get('primary_topic_label','')} "
            + " ".join(str(t) for t in (blk.get('topics') or []))
        )
        btoks = set(t for t in hay.split() if len(t) >= 4)
        overlap = len(concept_tokens & btoks)
        if overlap:
            scored.append((blk.get("id", ""), overlap))
    if not scored:
        return "", 0.0
    scored.sort(key=lambda x: x[1], reverse=True)
    winner_id, winner_n = scored[0]
    runner_n = scored[1][1] if len(scored) > 1 else 0
    total = sum(n for _, n in scored)
    conf = min(0.6, max(0.0, (winner_n - runner_n + 1) / (total + 1)))
    return winner_id, round(conf, 3)
```

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_material_residual.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/summary_core.py tests/test_material_residual.py
git commit -m "feat(core): summary_core (cache + assign deterministico) reusavel"
```

## Task 0.7: Documentar a distinção `manual_unit_slug` (entry vs bloco)

**Files:**
- Modify: `src/builder/timeline/curation.py` (docstring do módulo)

> A auditoria achou colisão de nome: `manual_unit_slug` existe no *entry*
> (arquivo→unidade, `manifest.json`) E no *bloco* (`.timeline_curation.json`,
> bloco→unidade). NÃO renomear (quebraria os `.timeline_curation.json` já
> escritos nos 5 cursos). Só documentar.

- [ ] **Step 1: Adicionar nota no docstring do módulo**

No topo de `src/builder/timeline/curation.py`, acrescentar ao docstring:

```
NOTA: `manual_unit_slug` aqui e BLOCK-level (bloco -> unidade). Nao confundir
com `FileEntry.manual_unit_slug` (arquivo -> unidade, em manifest.json). Mesmo
nome, escopos diferentes; aplicados em contextos distintos (bloco vs entry).
```

- [ ] **Step 2: Commit**

```bash
git add src/builder/timeline/curation.py
git commit -m "docs(curation): documenta distincao manual_unit_slug (entry vs bloco)"
```

---

# FASE 1 — Métrica primeiro (baseline antes de mexer)

## Task 1.1: Cobertura de material por curso

**Files:**
- Create: `src/builder/artifacts/cronograma_health.py`
- Test: `tests/test_cronograma_health.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_cronograma_health.py
from src.builder.artifacts.cronograma_health import material_coverage


def _entry(eid, auto_tags=None, ftype="pdf"):
    return {"id": eid, "auto_tags": auto_tags or [], "file_type": ftype, "category": "material-de-aula"}


def test_coverage_counts_blocked_vs_orphan():
    entries = [
        _entry("a", ["bloco:bloco-01"]),
        _entry("b", ["unit:u1"]),          # sem bloco -> orfao
        _entry("c", ["bloco:bloco-02"], ftype="image"),
    ]
    rep = material_coverage(entries)
    assert rep["total"] == 3
    assert rep["with_block"] == 2
    assert rep["orphans"] == 1
    assert round(rep["coverage"], 2) == 0.67
    assert rep["by_type"]["pdf"]["with_block"] == 1
    assert rep["by_type"]["image"]["with_block"] == 1


def test_coverage_manual_block_counts():
    entries = [{"id": "m", "manual_timeline_block_id": "bloco-03", "auto_tags": [], "file_type": "pdf"}]
    rep = material_coverage(entries)
    assert rep["with_block"] == 1
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_cronograma_health.py -q`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implementar coverage**

```python
# src/builder/artifacts/cronograma_health.py
from __future__ import annotations

from collections import defaultdict
from typing import Iterable


_NON_MATERIAL_CATEGORIES = {"cronograma", "bibliografia", "referencias"}


def _entry_block_id(entry: dict) -> str:
    manual = str(entry.get("manual_timeline_block_id") or "").strip()
    if manual:
        return manual
    for tag in entry.get("auto_tags") or []:
        t = str(tag)
        if t.startswith("bloco:"):
            return t[len("bloco:"):]
    return ""


def material_coverage(entries: Iterable[dict]) -> dict:
    """% de materiais com bloco, orfaos, por tipo. Read-only."""
    entries = [
        e for e in (entries or [])
        if str(e.get("category") or "").lower() not in _NON_MATERIAL_CATEGORIES
    ]
    total = len(entries)
    with_block = 0
    by_type: dict = defaultdict(lambda: {"total": 0, "with_block": 0})
    for e in entries:
        ftype = str(e.get("file_type") or "pdf").lower()
        by_type[ftype]["total"] += 1
        if _entry_block_id(e):
            with_block += 1
            by_type[ftype]["with_block"] += 1
    return {
        "total": total,
        "with_block": with_block,
        "orphans": total - with_block,
        "coverage": (with_block / total) if total else 0.0,
        "by_type": {k: dict(v) for k, v in by_type.items()},
    }
```

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_cronograma_health.py -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/cronograma_health.py tests/test_cronograma_health.py
git commit -m "feat(health): material_coverage (cobertura/orfaos/por tipo)"
```

## Task 1.2: Renderer `cronograma_health_md`

**Files:**
- Modify: `src/builder/artifacts/cronograma_health.py`
- Test: `tests/test_cronograma_health.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# anexar em tests/test_cronograma_health.py
from src.builder.artifacts.cronograma_health import cronograma_health_md


def test_health_md_renders_metrics():
    entries = [
        {"id": "a", "auto_tags": ["bloco:bloco-01"], "file_type": "pdf", "category": "material-de-aula"},
        {"id": "b", "auto_tags": [], "file_type": "image", "category": "material-de-aula"},
    ]
    blocks = [{"id": "bloco-01"}, {"id": "bloco-02"}]
    md = cronograma_health_md({"name": "X"}, entries, blocks)
    assert "Cobertura" in md
    assert "50%" in md
    assert "bloco-02" in md  # bloco pobre (0 materiais) listado
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_cronograma_health.py::test_health_md_renders_metrics -q`
Expected: FAIL (ImportError: cronograma_health_md)

- [ ] **Step 3: Implementar o renderer**

```python
# anexar em src/builder/artifacts/cronograma_health.py
def _blocks_by_material_count(entries, blocks) -> dict:
    counts = {b.get("id"): 0 for b in (blocks or []) if b.get("id")}
    for e in entries or []:
        bid = _entry_block_id(e)
        if bid in counts:
            counts[bid] += 1
    return counts


def cronograma_health_md(course_meta: dict, entries: list, blocks: list) -> str:
    rep = material_coverage(entries)
    name = str((course_meta or {}).get("name") or "Curso")
    lines = [
        f"# CRONOGRAMA_HEALTH — {name}",
        "",
        f"- **Cobertura de material**: {rep['coverage']:.0%} "
        f"({rep['with_block']}/{rep['total']} com bloco)",
        f"- **Órfãos** (sem bloco): {rep['orphans']}",
        "",
        "## Por tipo",
        "",
        "| Tipo | Com bloco | Total |",
        "|---|---|---|",
    ]
    for ftype, v in sorted(rep["by_type"].items()):
        lines.append(f"| {ftype} | {v['with_block']} | {v['total']} |")

    counts = _blocks_by_material_count(entries, blocks)
    poor = [bid for bid, n in counts.items() if n == 0]
    rich = sorted(((n, bid) for bid, n in counts.items()), reverse=True)[:5]
    lines += [
        "",
        "## Blocos pobres (0 materiais)",
        "",
        (", ".join(poor) if poor else "_nenhum_"),
        "",
        "## Blocos mais ricos",
        "",
    ]
    for n, bid in rich:
        lines.append(f"- {bid}: {n} material(is)")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_cronograma_health.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/cronograma_health.py tests/test_cronograma_health.py
git commit -m "feat(health): cronograma_health_md renderer"
```

## Task 1.3: Escrever HEALTH no build + baseline

**Files:**
- Modify: `src/builder/ops/pedagogical_regeneration.py` (após o bloco de CODE_HEALTH, ~linha 238-248)

- [ ] **Step 1: Adicionar a escrita do HEALTH**

Em `regenerate_pedagogical_files`, logo após o `write_text(... "CODE_HEALTH.md" ...)`, inserir:

```python
    from src.builder.artifacts.cronograma_health import cronograma_health_md as _cronograma_health_md
    write_text(
        builder.root_dir / "course" / "CRONOGRAMA_HEALTH.md",
        _cronograma_health_md(
            builder.course_meta,
            live_manifest_entries,
            builder._load_timeline_blocks(),
        ),
    )
```

- [ ] **Step 2: Gerar baseline manual (sem build pesado)**

Run:
```bash
python -c "import json,glob,re; from pathlib import Path; from src.builder.artifacts.cronograma_health import material_coverage;
for p in glob.glob('C:/Users/Humberto/Documents/GitHub/*-Tutor/manifest.json'):
    c=re.split(r'[\\/]+',p)[-2]; d=json.load(open(p,encoding='utf-8'));
    r=material_coverage(d.get('entries',[]));
    print(c, f\"cobertura={r['coverage']:.0%} orfaos={r['orphans']}/{r['total']}\")"
```
Expected: imprime cobertura atual por curso (baseline pré-feature). Anotar os números no commit.

- [ ] **Step 3: Rodar suite ampla**

Run: `python -m pytest tests/ -q`
Expected: 4 failed (baseline), demais passed

- [ ] **Step 4: Commit**

```bash
git add src/builder/ops/pedagogical_regeneration.py
git commit -m "feat(health): build escreve CRONOGRAMA_HEALTH.md + baseline de cobertura"
```

---

# FASE 2 — Camada 1: sinal determinístico

## Task 2.1: Sinal de descrição de imagem em `collect_entry_unit_signals`

**Files:**
- Modify: `src/builder/extraction/entry_signals.py:88-113`
- Test: `tests/test_entry_signals_materials.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_entry_signals_materials.py
from src.builder.extraction.entry_signals import collect_entry_unit_signals


def test_image_description_feeds_signal():
    entry = {
        "title": "diagram.png",
        "file_type": "image",
        "image_description": "Máquina de Turing com fita infinita e cabeçote",
        "auto_tags": [],
    }
    sig = collect_entry_unit_signals(entry, markdown_text="")
    assert "maquina de turing" in sig["image_description_text"]
    # descricao tambem entra no markdown_text efetivo p/ o scorer
    assert "turing" in sig["markdown_text"]


def test_no_image_description_is_empty():
    sig = collect_entry_unit_signals({"title": "x.pdf"}, markdown_text="conteudo")
    assert sig["image_description_text"] == ""
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_entry_signals_materials.py -q`
Expected: FAIL (KeyError: image_description_text)

- [ ] **Step 3: Adicionar a fonte de sinal**

Em `collect_entry_unit_signals`, antes do `return`, montar a descrição e fundir no markdown efetivo:

```python
    image_description = str(entry.get("image_description", "") or "")
    effective_markdown = markdown_text or ""
    if image_description and image_description not in effective_markdown:
        effective_markdown = f"{effective_markdown}\n{image_description}".strip()
```

E no dict de retorno, trocar a linha do `"markdown_text"` e adicionar a nova chave:

```python
        "image_description_text": normalize_match_text(image_description),
        "markdown_text": normalize_match_text(effective_markdown),
```

(As demais chaves que derivam de `markdown_text` — `markdown_headings_text`, `markdown_lead_text` — continuam usando o `markdown_text` original do parâmetro; a descrição entra via `markdown_text` efetivo, que é o de peso 1.0 no scorer.)

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_entry_signals_materials.py -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/extraction/entry_signals.py tests/test_entry_signals_materials.py
git commit -m "feat(signal): descricao de imagem alimenta o score (markdown efetivo + image_description_text)"
```

## Task 2.2: Fallback de markdown p/ descrição em `navigation.py`

**Files:**
- Modify: `src/builder/artifacts/navigation.py:61-70`
- Test: `tests/test_entry_signals_materials.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# anexar em tests/test_entry_signals_materials.py
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map


def test_markdown_fallback_uses_image_description(tmp_path):
    entry = {"id": "img1", "file_type": "image",
             "image_description": "Hierarquia de Chomsky e automatos"}
    # sem .md no disco -> deve cair na descricao de imagem
    txt = _entry_markdown_text_for_file_map(tmp_path, entry)
    assert "Chomsky" in txt


def test_markdown_real_md_takes_precedence(tmp_path):
    md = tmp_path / "x.md"
    md.write_text("conteudo real", encoding="utf-8")
    entry = {"id": "e", "base_markdown": "x.md", "image_description": "ignorar"}
    txt = _entry_markdown_text_for_file_map(tmp_path, entry)
    assert "conteudo real" in txt
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_entry_signals_materials.py::test_markdown_fallback_uses_image_description -q`
Expected: FAIL (retorna "" em vez da descrição)

- [ ] **Step 3: Adicionar fallback**

Em `_entry_markdown_text_for_file_map`, trocar o trecho `if not md_path: return ""`:

```python
    md_path = _entry_markdown_path_for_file_map(root_dir, entry)
    if not md_path:
        # Fallback: material sem .md convertido (imagem/PDF) usa descricao injetada
        desc = str(entry.get("image_description", "") or "").strip()
        return desc
```

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_entry_signals_materials.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/navigation.py tests/test_entry_signals_materials.py
git commit -m "feat(signal): markdown fallback p/ descricao de imagem quando nao ha .md"
```

## Task 2.3: Conteúdo de exercício no sinal + re-medir cobertura

**Files:**
- Modify: `src/builder/extraction/entry_signals.py` (garantir que `category` de exercício e notas entrem)
- Test: `tests/test_entry_signals_materials.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# anexar em tests/test_entry_signals_materials.py
def test_exercise_notes_feed_signal():
    entry = {"title": "Lista 3.pdf", "category": "lista-de-exercicios",
             "notes": "exercicios sobre maquina de turing e decidibilidade",
             "auto_tags": []}
    sig = collect_entry_unit_signals(entry, markdown_text="")
    assert "decidibilidade" in sig["markdown_text"]
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_entry_signals_materials.py::test_exercise_notes_feed_signal -q`
Expected: FAIL (notes não entram)

- [ ] **Step 3: Fundir `notes` no markdown efetivo**

Em `collect_entry_unit_signals`, no cálculo de `effective_markdown` (da Task 2.1), incluir também `notes`:

```python
    extra_parts = [markdown_text or ""]
    notes = str(entry.get("notes", "") or "")
    if notes:
        extra_parts.append(notes)
    if image_description and image_description not in " ".join(extra_parts):
        extra_parts.append(image_description)
    effective_markdown = "\n".join(p for p in extra_parts if p).strip()
```

(Substitui o cálculo de `effective_markdown` da Task 2.1.)

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_entry_signals_materials.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Re-medir cobertura (corpus real)**

Run: o mesmo one-liner da Task 1.3 Step 2.
Expected: cobertura **igual ou maior** que o baseline (C1 só adiciona sinal). Anotar no commit.

- [ ] **Step 6: Commit**

```bash
git add src/builder/extraction/entry_signals.py tests/test_entry_signals_materials.py
git commit -m "feat(signal): notes de exercicio alimentam o score; re-mede cobertura"
```

---

# FASE 3 — Camada 2: resumo Gemini residual

## Task 3.1: Summarizer residual de material (client mockável)

**Files:**
- Create: (já existe) usar `src/builder/core/summary_core.py`; adicionar `summarize_residual_materials`
- Test: `tests/test_material_residual.py`

- [ ] **Step 1: Escrever o teste que falha (extract_concepts mockável)**

> Interface mínima: `extract_concepts: Callable[[str], list[str]]`. Em teste é uma
> função com contador; em produção (Task 3.2) é um adapter sobre o client Gemini.

```python
# anexar em tests/test_material_residual.py
from src.builder.core.summary_core import summarize_residual_materials


class _Counter:
    """extract_concepts callable com contador de chamadas."""
    def __init__(self, concepts):
        self.concepts = concepts
        self.calls = 0
    def __call__(self, text):
        self.calls += 1
        return list(self.concepts)


def test_residual_assigns_block_and_caches(tmp_path):
    blocks = [{"id": "bloco-02", "topic_text": "maquina de turing", "primary_topic_label": "Turing"}]
    orphans = [{"id": "e1", "_text": "slides sobre turing machine"}]
    extract = _Counter(["maquina", "turing"])
    result = summarize_residual_materials(tmp_path, orphans, blocks, extract, cap=5)
    assert result["e1"]["primary_block_id"] == "bloco-02"
    from src.builder.core.summary_core import load_summary_cache
    cached = load_summary_cache(tmp_path, "material_curation.json")
    assert "e1" in cached["entries"]


def test_residual_respects_cap(tmp_path):
    orphans = [{"id": f"e{i}", "_text": "turing"} for i in range(10)]
    blocks = [{"id": "bloco-02", "topic_text": "turing"}]
    extract = _Counter(["turing"])
    summarize_residual_materials(tmp_path, orphans, blocks, extract, cap=3)
    assert extract.calls == 3


def test_residual_cache_hit_skips_client(tmp_path):
    from src.builder.core.summary_core import write_summary_cache
    write_summary_cache(tmp_path, "material_curation.json",
                        {"version": 1, "entries": {"e1": {"primary_block_id": "bloco-02", "concepts": ["x"]}}})
    extract = _Counter(["t"])
    summarize_residual_materials(tmp_path, [{"id": "e1", "_text": "t"}], [{"id": "bloco-02"}], extract, cap=5)
    assert extract.calls == 0  # cache hit
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_material_residual.py -q`
Expected: FAIL (ImportError: summarize_residual_materials)

- [ ] **Step 3: Implementar (reusa cache + assign do núcleo)**

```python
# anexar em src/builder/core/summary_core.py
from typing import Callable


def summarize_residual_materials(repo_dir, orphans, blocks,
                                 extract_concepts: Callable[[str], list], *,
                                 cap: int = 20,
                                 cache_filename: str = "material_curation.json") -> dict:
    """Resume materiais orfaos (cada um com chave '_text'), casa em bloco e cacheia.

    `extract_concepts(text) -> list[str]`: callable que extrai conceitos/keywords.
    Em producao e um adapter sobre o client Gemini (Task 3.2). Cap limita chamadas;
    cache evita re-chamada. Retorna {entry_id: {concepts, primary_block_id, confidence, method}}.
    """
    cache = load_summary_cache(repo_dir, cache_filename)
    entries_map = cache.setdefault("entries", {})
    out: dict = {}
    calls = 0
    for entry in orphans or []:
        eid = str(entry.get("id") or "")
        if not eid:
            continue
        if eid in entries_map and entries_map[eid].get("primary_block_id"):
            out[eid] = entries_map[eid]
            continue
        if calls >= cap:
            break
        text = str(entry.get("_text", "") or "")
        if not text.strip():
            continue
        concepts = extract_concepts(text) or []
        calls += 1
        bid, conf = assign_concepts_to_block(concepts, blocks)
        rec = {"concepts": concepts, "primary_block_id": bid,
               "confidence": conf, "method": "gemini_residual"}
        entries_map[eid] = rec
        out[eid] = rec
    write_summary_cache(repo_dir, cache_filename, cache)
    return out
```

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_material_residual.py -q`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/summary_core.py tests/test_material_residual.py
git commit -m "feat(core): summarize_residual_materials (cap + cache, client mockavel)"
```

## Task 3.2: Wiring do residual no build (opt-in) + injeta `bloco:` resolvido

**Files:**
- Modify: `src/builder/ops/pedagogical_regeneration.py` (após `resolve_unit_block_tags_fn`, ~linha 170-176)

- [ ] **Step 1: Confirmar como o code_summarization obtém o client**

Ler `summarize_all_code_entries` (`src/builder/core/code_summarization.py:391`) e a chamada em `engine.py`/`pedagogical_regeneration.py` que passa o `client`. Identificar: (a) o atributo/variável do client no `builder`, (b) o método de chamada (`client.summarize_bundle(bundle_text, schema, system_instruction)`). O adapter `extract_concepts` espelha essa chamada com um schema mínimo de keywords.

- [ ] **Step 2: Adicionar o passo residual (guardado por client presente)**

Logo após `live_manifest_entries = resolve_unit_block_tags_fn(...)`, inserir:

```python
    # Camada 2: resíduo via Gemini (opt-in). So materiais ainda sem bloco.
    # NOTA: trocar `_resolve_gemini_client(builder)` pelo acesso real ao client
    # confirmado no Step 1 (mesmo client de summarize_all_code_entries).
    gemini_client = _resolve_gemini_client(builder)
    if gemini_client is not None:
        from src.builder.artifacts.cronograma_health import _entry_block_id
        from src.builder.core.summary_core import summarize_residual_materials
        from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map

        def _extract_concepts(text: str) -> list:
            # Adapter: reusa a chamada do code_summarization (client.summarize_bundle)
            # com um prompt curto de keywords. Em caso de erro, retorna [] (degrada).
            try:
                res = gemini_client.summarize_bundle(
                    bundle_text=text[:6000],
                    schema=None,
                    system_instruction="Liste 3-8 palavras-chave tecnicas do material, separadas por virgula.",
                )
                raw = getattr(res, "text", None) or str(res)
                return [w.strip() for w in str(raw).replace("\n", ",").split(",") if w.strip()]
            except Exception:
                return []

        _blocks = builder._load_timeline_blocks()
        orphans = []
        for e in live_manifest_entries:
            if _entry_block_id(e):
                continue
            txt = _entry_markdown_text_for_file_map(builder.root_dir, e) or str(e.get("title") or "")
            orphans.append({"id": e.get("id"), "_text": txt})
        if orphans and _blocks:
            resolved = summarize_residual_materials(
                builder.root_dir, orphans, _blocks, _extract_concepts, cap=20,
            )
            by_id = {e.get("id"): e for e in live_manifest_entries}
            for eid, rec in resolved.items():
                bid = rec.get("primary_block_id")
                if bid and by_id.get(eid) is not None:
                    tags = [t for t in (by_id[eid].get("auto_tags") or []) if not str(t).startswith("bloco:")]
                    tags.append(f"bloco:{bid}")
                    by_id[eid]["auto_tags"] = tags
```

Definir o helper `_resolve_gemini_client` no topo do módulo, usando o mesmo caminho de obtenção de client confirmado no Step 1 (retorna `None` se o extra `code-summarization` não estiver instalado / sem API key — o caminho inteiro degrada para no-op):

```python
def _resolve_gemini_client(builder):
    try:
        from src.builder.core.code_summarization import _make_gemini_client  # confirmar nome no Step 1
        return _make_gemini_client(builder)
    except Exception:
        return None
```

- [ ] **Step 3: Rodar suite ampla (sem client → caminho não roda)**

Run: `python -m pytest tests/ -q`
Expected: 4 failed (baseline), demais passed (o bloco é guardado por `gemini_client is not None`)

- [ ] **Step 4: Commit**

```bash
git add src/builder/ops/pedagogical_regeneration.py
git commit -m "feat(build): residual Gemini injeta bloco: nos materiais orfaos (opt-in)"
```

---

# FASE 4 — Gate de cobertura + validação

## Task 4.1: `scripts/validate_materials.py`

**Files:**
- Create: `scripts/validate_materials.py`
- Test: `tests/test_cronograma_health.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# anexar em tests/test_cronograma_health.py
import json
from scripts.validate_materials import coverage_gate_failures


def test_gate_flags_low_coverage():
    entries = [{"id": "a", "auto_tags": [], "file_type": "pdf", "category": "material-de-aula"}]
    fails = coverage_gate_failures(entries)
    assert any("cobertura" in f for f in fails)


def test_gate_passes_high_coverage():
    entries = [{"id": "a", "auto_tags": ["bloco:bloco-01"], "file_type": "pdf", "category": "material-de-aula"}]
    assert coverage_gate_failures(entries) == []
```

- [ ] **Step 2: Rodar p/ falhar**

Run: `python -m pytest tests/test_cronograma_health.py::test_gate_flags_low_coverage -q`
Expected: FAIL (ModuleNotFoundError: scripts.validate_materials)

- [ ] **Step 3: Implementar o script**

```python
# scripts/validate_materials.py
"""Gate de cobertura de material (espelha validate_timeline.py).

Uso: python scripts/validate_materials.py [manifest_globs...]
Sem args: valida fixtures (se houver). Saida != 0 se cobertura < MATERIAL_COVERAGE_MIN.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.artifacts.cronograma_health import material_coverage  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402


def coverage_gate_failures(entries: list) -> list:
    rep = material_coverage(entries)
    fails = []
    if rep["total"] and rep["coverage"] < T.MATERIAL_COVERAGE_MIN:
        fails.append(
            f"cobertura {rep['coverage']:.0%} < {T.MATERIAL_COVERAGE_MIN:.0%} "
            f"({rep['orphans']} orfaos de {rep['total']})"
        )
    return fails


def main(argv: list) -> int:
    patterns = argv or []
    paths = []
    for pat in patterns:
        paths.extend(glob.glob(pat))
    if not paths:
        print("nenhum manifest informado")
        return 0
    ok = True
    for p in paths:
        try:
            entries = json.loads(Path(p).read_text(encoding="utf-8")).get("entries", [])
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[FAIL] {p}: {exc}")
            ok = False
            continue
        fails = coverage_gate_failures(entries)
        rep = material_coverage(entries)
        marker = "OK " if not fails else "FAIL"
        print(f"[{marker}] {p}  cobertura={rep['coverage']:.0%} orfaos={rep['orphans']}/{rep['total']}")
        for f in fails:
            print(f"        {f}")
        ok = ok and not fails
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Rodar p/ passar**

Run: `python -m pytest tests/test_cronograma_health.py -q`
Expected: PASS (todos)

- [ ] **Step 5: Medir gate no corpus real (informativo, não trava)**

Run: `python scripts/validate_materials.py "C:/Users/Humberto/Documents/GitHub/*-Tutor/manifest.json"`
Expected: imprime cobertura por curso; alguns podem estar abaixo de 70% (resíduo → curadoria). Anotar.

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_materials.py tests/test_cronograma_health.py
git commit -m "feat(ci): validate_materials gate de cobertura"
```

## Task 4.2: Wire do gate no workflow de CI (opcional, não-bloqueante por ora)

**Files:**
- Modify: `.github/workflows/validate-timeline.yml`

- [ ] **Step 1: Adicionar step informativo**

No final do job `validate`, adicionar:

```yaml
      - name: Cobertura de material (informativo)
        run: python scripts/validate_materials.py tests/fixtures/timeline/*.json || true
```

(Informativo por ora — `|| true` não falha o build. Vira bloqueante quando houver fixture de manifest com cobertura controlada.)

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/validate-timeline.yml
git commit -m "ci: roda validate_materials (informativo)"
```

---

# FASE 5 — Handshake

## Task 5.1: Marcar pré-req concluído no plano pai

**Files:**
- Modify: `plans/material-agnostic-refactor.md` (seção Pré-requisitos)

- [ ] **Step 1: Atualizar o checkbox**

Trocar a linha `- [ ] PDFs/imagens/exercícios precisam de mecanismo análogo ao concept-match...` por:

```markdown
- [x] PDFs/imagens/exercícios ganham bloco via reforço de sinal (descrição de imagem, notes de exercício, fallback de markdown) + resíduo Gemini opt-in + curadoria. Cobertura medida em `CRONOGRAMA_HEALTH.md` / `scripts/validate_materials.py`. Ver `plans/2026-06-03-block-match-materiais.md`.
```

- [ ] **Step 2: Rodar suite final completa**

Run: `python -m pytest tests/ -q`
Expected: 4 failed (baseline), demais passed

- [ ] **Step 3: Commit**

```bash
git add plans/material-agnostic-refactor.md
git commit -m "docs: pre-req de block-match de materiais concluido (handshake)"
```

---

## Verificação final (após todas as fases)

- [ ] `python -m pytest tests/ -q` → só as 4 falhas pré-existentes.
- [ ] `python scripts/validate_materials.py "C:/Users/Humberto/Documents/GitHub/*-Tutor/manifest.json"` → cobertura ≥ baseline em todos; órfãos restantes documentados como curadoria.
- [ ] `CRONOGRAMA_HEALTH.md` gerado em pelo menos 1 curso após rebuild.
- [ ] Nenhum `material_summarization.py` paralelo criado (núcleo único em `summary_core.py`).
- [ ] Facade/DI NÃO tocado (dívida separada preservada).

---

## Riscos (do spec) e onde são tratados

- **R1** (PDF lazy): Task 2.2 só *lê* markdown/descrição; nunca força re-extração.
- **R2** (custo Gemini): Task 3.1 cap + cache; Task 3.2 opt-in por client presente.
- **R3** (falso-positivo): threshold mantido; HEALTH expõe blocos ricos demais (Task 1.2).
- **R4** (consolidação muda match): Tasks 0.2/0.3/0.5 têm testes de paridade antes de trocar; `content_taxonomy` variante NÃO consolidada.
