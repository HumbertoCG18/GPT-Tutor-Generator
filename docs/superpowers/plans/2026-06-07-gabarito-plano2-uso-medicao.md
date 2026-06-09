# Gabarito Plano 2 — Uso do card na atribuição + medição Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans para implementar task-by-task. Steps usam checkbox (`- [ ]`).

**Goal:** Usar `source_section` (o card) como sinal autoritativo na atribuição file→bloco — card vence o lexical; card largo escolhe sub-bloco via scorer restrito aos blocos do card — e medir o ganho contra a baseline (62,5%/11 confident-wrong).

**Architecture:** Camada de ponte (backfill de `source_section` nos já-processados + filtro de backlog no import) deixa os dados prontos sem re-extrair. `resolve_card_to_block` (puro) resolve card→bloco(s) por nome/data; um mapa persistido (`course/.card_block_map.json`) guarda confirmações manuais. O resolver de produção (`resolve_unit_block_tags`) ganha o degrau card→bloco entre o override manual e o scorer lexical. A reatribuição usa o op existente `run_pedagogical_regeneration` (não re-extrai). Medição via script novo que usa o card como verdade.

**Tech Stack:** Python 3.11/3.13, pytest, dataclasses.

**Fonte:** `docs/superpowers/specs/2026-06-07-gabarito-cards-pasta-design.md` (componentes 3-6) + investigação de 2026-06-07 (paths/assinaturas reais abaixo).

**Pré-requisito:** Plano 1 entregue (`FileEntry.source_section`, `scan_stash_cards`, `build_stash_entries`).

---

## Contexto técnico verificado (não re-investigar)

- Resolver de produção: `resolve_unit_block_tags` em `src/builder/extraction/content_taxonomy.py:853`. Ordem de bloco hoje: `manual_timeline_block_id` (conf 1.0, linha 962-965) → scorer `select_probable_period_for_entry_fn` (gate best>=0.95, 980-1003) → fallback `_best_instructional_block_fallback` (argmax sobre TODOS instrucionais, 1005-1014). Dentro do `else` (linha 966+) já existem `unit_index` (885), `timeline_context` (886), `repo_root` (897). Carrega `tag_profile` de `Path(repo_root)/"course"` (899-905) — espelhar pra carregar o card_map.
- `_best_instructional_block_fallback(entry, markdown_text, instructional_blocks, preferred_unit_slug, preferred_topic_slug)` (`content_taxonomy.py:797`) — argmax via scorer real sobre a lista passada. Restringir a lista = restringir ao card.
- Bloco (timeline_index): `{"id","period_start","period_end","period_label","unit_slug","unit_confidence","primary_topic_label","topics","aliases","administrative_only?"}`.
- Unidade (unit_index): `{"slug","title","topics","topic_phrases","distinctive_tokens"}`.
- Reatribuição sobre manifest existente = op `run_pedagogical_regeneration` (`src/builder/ops/pedagogical_regeneration.py:281`) — carrega manifest, chama `resolve_unit_block_tags`, grava; NÃO re-extrai markdown.
- Medição read-only: `scripts/eval_ground_truth.py` lê `computed_block_id` do manifest (não re-roda scorer). `load_predictions`, `load_block_period_map` reusáveis.
- Import do stash: `import_from_stash` em `src/ui/app.py` dedup só contra `self.entries` (fila), NÃO contra o backlog/manifest. Backlog: `_get_backlog_sources()` retorna set de basenames já processados (`src/ui/app.py:~1500`).
- Helpers públicos: `norm_ascii_lower`, `collapse_ws` em `src/utils/helpers.py`.

---

## File Structure

- `src/builder/core/stash_import.py` — adiciona `filter_already_processed(scan, backlog_basenames)` (puro).
- `src/ui/app.py` — `import_from_stash` passa a filtrar por backlog (1 linha + chamada).
- `src/builder/timeline/card_block.py` (NOVO) — `resolve_card_to_block`, `CardBlockResolution`, `load_card_block_map`, `save_card_block_map`, `lookup_card_blocks`. Puro/IO mínimo.
- `src/builder/core/stash_backfill.py` (NOVO) — `match_entries_to_cards(manifest_entries, scan)` (puro).
- `scripts/backfill_source_section.py` (NOVO) — CLI dry-run/--write.
- `src/builder/extraction/content_taxonomy.py` — degrau card→bloco em `resolve_unit_block_tags`.
- `scripts/eval_cards.py` (NOVO) — medição card-as-truth.
- Testes: `tests/test_stash_import.py`, `tests/test_card_block.py` (NOVO), `tests/test_stash_backfill.py` (NOVO), `tests/test_card_block_assignment.py` (NOVO).

---

## Task 1: Filtro de backlog no import do stash

**Files:**
- Modify: `src/builder/core/stash_import.py`
- Modify: `src/ui/app.py` (`import_from_stash`)
- Test: `tests/test_stash_import.py`

- [ ] **Step 1: Teste que falha**

Adicionar a `tests/test_stash_import.py`:

```python
from src.builder.core.stash_import import filter_already_processed


def test_filter_already_processed_drops_known_basenames(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    filtered = filter_already_processed(scan, {"hoare.pdf", "slides.pdf"})
    names = {Path(i.source_path).name for i in filtered.items}
    assert "hoare.pdf" not in names
    assert "slides.pdf" not in names
    assert "hoare.zip" in names          # não estava no backlog
    assert filtered.skipped == scan.skipped  # skipped preservado


def test_filter_already_processed_empty_backlog_is_noop(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    filtered = filter_already_processed(scan, set())
    assert len(filtered.items) == len(scan.items)
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_stash_import.py -k filter_already_processed -v`
Expected: FAIL — `ImportError: cannot import name 'filter_already_processed'`

- [ ] **Step 3: Implementar (em `stash_import.py`, após `build_stash_entries`)**

```python
def filter_already_processed(scan: StashScanResult, backlog_basenames) -> StashScanResult:
    """Remove do scan os itens cujo basename já está no backlog (já processados).
    Casamento por nome de arquivo — o source_path do stash difere do source_path
    original no manifest, então dedup por path não pega. Preserva `skipped`.
    """
    known = {str(n).strip() for n in (backlog_basenames or set())}
    kept = [i for i in scan.items if Path(i.source_path).name not in known]
    return StashScanResult(items=kept, skipped=list(scan.skipped))
```

- [ ] **Step 4: Ver passar**

Run: `python -m pytest tests/test_stash_import.py -v`
Expected: PASS (todos, incluindo os 2 novos)

- [ ] **Step 5: Wire na UI**

Em `src/ui/app.py`, dentro de `import_from_stash`, logo após `scan = scan_stash_cards(stash)` e o guard de `scan.items`, inserir o filtro antes de montar `existing`:

```python
        from src.builder.core.stash_import import filter_already_processed
        scan = filter_already_processed(scan, self._get_backlog_sources())
        if not scan.items:
            messagebox.showinfo(APP_NAME, "Todos os arquivos do stash já foram processados (backlog).")
            return
```

(O `from ... import scan_stash_cards, build_stash_entries` já existe no método — acrescentar `filter_already_processed` ali ou no import inline acima.)

- [ ] **Step 6: Smoke + suíte**

Run: `python -c "import src.ui.app"` (sem erro)
Run: `python -m pytest -q` (verde)

- [ ] **Step 7: Commit**

```bash
git add src/builder/core/stash_import.py src/ui/app.py tests/test_stash_import.py
git commit -m "feat(stash): skip already-processed files on stash import

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Backfill de `source_section` nos já-processados

**Files:**
- Create: `src/builder/core/stash_backfill.py`
- Create: `scripts/backfill_source_section.py`
- Test: `tests/test_stash_backfill.py`

**Contrato:** casa entries do manifest com itens do stash por basename. Retorna `(assignments, unmatched, ambiguous)`: `assignments` = `{entry_id_or_basename: card_name}` para basenames únicos no stash; `ambiguous` = basenames que aparecem em >1 card (não atribui); `unmatched` = entries sem arquivo no stash.

- [ ] **Step 1: Teste que falha**

Criar `tests/test_stash_backfill.py`:

```python
from pathlib import Path
from src.builder.core.stash_import import scan_stash_cards
from src.builder.core.stash_backfill import match_entries_to_cards


def _make_tree(root: Path):
    (root / "Verificacao de Programas").mkdir(parents=True)
    (root / "Verificacao de Programas" / "hoare.pdf").write_text("x", encoding="utf-8")
    (root / "Introducao").mkdir()
    (root / "Introducao" / "slides.pdf").write_text("x", encoding="utf-8")
    (root / "Bibliografia").mkdir()
    (root / "Bibliografia" / "hoare.pdf").write_text("x", encoding="utf-8")  # dup basename


def test_match_assigns_unique_basenames(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    entries = [
        {"id": "slides", "source_path": "C:/old/slides.pdf"},
        {"id": "hoare", "source_path": "D:/whatever/hoare.pdf"},
        {"id": "ghost", "source_path": "X:/none/ghost.pdf"},
    ]
    assignments, unmatched, ambiguous = match_entries_to_cards(entries, scan)
    assert assignments["slides"] == "Introducao"
    assert "hoare" in ambiguous          # dup em 2 cards
    assert "hoare" not in assignments
    assert "ghost" in unmatched
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_stash_backfill.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.core.stash_backfill'`

- [ ] **Step 3: Implementar `src/builder/core/stash_backfill.py`**

```python
"""Backfill de source_section em entries já processados (manifest existente).

Casa por basename: o source_path do stash difere do original no manifest, então
o nome do arquivo é a ponte. Basename que aparece em >1 card é ambíguo (não
atribui — vai pra confirmação manual).
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from src.builder.core.stash_import import StashScanResult


def match_entries_to_cards(manifest_entries, scan: StashScanResult) -> Tuple[Dict[str, str], List[str], List[str]]:
    by_basename: Dict[str, set] = {}
    for item in scan.items:
        by_basename.setdefault(Path(item.source_path).name, set()).add(item.card_name)
    counts = Counter({name: len(cards) for name, cards in by_basename.items()})

    assignments: Dict[str, str] = {}
    unmatched: List[str] = []
    ambiguous: List[str] = []
    for entry in manifest_entries or []:
        eid = str(entry.get("id") or "")
        base = Path(str(entry.get("source_path") or "")).name
        if base not in by_basename:
            unmatched.append(eid or base)
            continue
        if counts[base] > 1:
            ambiguous.append(eid or base)
            continue
        assignments[eid or base] = next(iter(by_basename[base]))
    return assignments, unmatched, ambiguous
```

- [ ] **Step 4: Ver passar**

Run: `python -m pytest tests/test_stash_backfill.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Script CLI `scripts/backfill_source_section.py`**

```python
"""Carimba source_section em entries já no manifest, casando com o stash por nome.

Uso:
    python -m scripts.backfill_source_section <repo_root> <stash_folder>          # dry-run
    python -m scripts.backfill_source_section <repo_root> <stash_folder> --write  # grava
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.builder.core.stash_import import scan_stash_cards
from src.builder.core.stash_backfill import match_entries_to_cards


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    write = "--write" in argv
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python -m scripts.backfill_source_section <repo_root> <stash_folder> [--write]")
        return 2
    repo_root, stash = Path(pos[0]), Path(pos[1])
    manifest_path = repo_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    scan = scan_stash_cards(stash)
    assignments, unmatched, ambiguous = match_entries_to_cards(entries, scan)

    print(f"Stash: {len(scan.items)} arquivos. Manifest: {len(entries)} entries.")
    print(f"Casados (vão receber source_section): {len(assignments)}")
    print(f"Ambíguos (basename em >1 card, pulados): {len(ambiguous)} -> {ambiguous}")
    print(f"Sem arquivo no stash (pulados): {len(unmatched)} -> {unmatched}")

    if not write:
        print("\nDry-run. Use --write para gravar.")
        return 0

    changed = 0
    for entry in entries:
        eid = str(entry.get("id") or "") or Path(str(entry.get("source_path") or "")).name
        if eid in assignments:
            entry["source_section"] = assignments[eid]
            changed += 1
    backup = manifest_path.with_suffix(".json.bak")
    backup.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGravado: {changed} entries atualizados. Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 6: Smoke do script (dry-run, sem gravar)**

Run: `python -m scripts.backfill_source_section "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" "C:/Users/Humberto/Downloads/Metodos-Formais"`
Expected: imprime contagem casados/ambíguos/unmatched; NÃO grava (sem `--write`).

- [ ] **Step 7: Commit**

```bash
git add src/builder/core/stash_backfill.py scripts/backfill_source_section.py tests/test_stash_backfill.py
git commit -m "feat(stash): backfill source_section onto processed manifest by basename

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: `resolve_card_to_block` (puro)

**Files:**
- Create: `src/builder/timeline/card_block.py`
- Test: `tests/test_card_block.py`

**Contrato:** `resolve_card_to_block(card_name, unit_index, blocks) -> CardBlockResolution(block_ids, confidence, reason)`. Estratégia: (1) nome do card casa título/tópicos/aliases de uma unidade por overlap de tokens → blocos dessa unidade; (2) "Semana N"/data DD/MM no nome → bloco cujo período cobre; (3) sem match → `([], 0.0, "needs-confirmation")`.

- [ ] **Step 1: Teste que falha**

Criar `tests/test_card_block.py`:

```python
from src.builder.timeline.card_block import resolve_card_to_block, CardBlockResolution

UNITS = [
    {"slug": "u-intro", "title": "Introdução a Métodos Formais", "topics": ["motivação"], "distinctive_tokens": []},
    {"slug": "u-verif", "title": "Verificação de Programas", "topics": ["hoare", "dafny"], "distinctive_tokens": []},
]
BLOCKS = [
    {"id": "bloco-01", "unit_slug": "u-intro", "period_start": "2026-03-02", "period_end": "2026-03-02"},
    {"id": "bloco-10", "unit_slug": "u-verif", "period_start": "2026-04-27", "period_end": "2026-05-04"},
    {"id": "bloco-11", "unit_slug": "u-verif", "period_start": "2026-05-06", "period_end": "2026-05-06"},
]


def test_card_name_matches_unit_returns_its_blocks():
    r = resolve_card_to_block("Verificação de Programas", UNITS, BLOCKS)
    assert set(r.block_ids) == {"bloco-10", "bloco-11"}
    assert r.confidence > 0.0
    assert r.reason.startswith("unit:")


def test_card_partial_name_still_matches_unit():
    r = resolve_card_to_block("Verificacao de Programas (Hoare/Dafny)", UNITS, BLOCKS)
    assert set(r.block_ids) == {"bloco-10", "bloco-11"}


def test_card_with_date_maps_to_covering_block():
    r = resolve_card_to_block("Aula 06/05", UNITS, BLOCKS)
    assert r.block_ids == ["bloco-11"]
    assert r.reason.startswith("date:")


def test_unmatched_card_needs_confirmation():
    r = resolve_card_to_block("Bibliografia-Livros", UNITS, BLOCKS)
    assert r.block_ids == []
    assert r.confidence == 0.0
    assert r.reason == "needs-confirmation"
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_card_block.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.timeline.card_block'`

- [ ] **Step 3: Implementar `src/builder/timeline/card_block.py`**

```python
"""Resolve um card (subpasta do stash) a um ou mais blocos do cronograma.

Fonte autoritativa do gabarito-cards: o card (seção do Moodle) é mapeado por
NOME a uma unidade (→ blocos dela) ou por DATA/semana a um bloco específico.
Puro: sem I/O além do load/save do mapa persistido.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from src.utils.helpers import norm_ascii_lower

_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
_WEEK_RE = re.compile(r"\bsemana\s+(\d+)\b", re.IGNORECASE)
_STOP = {"de", "da", "do", "e", "a", "o", "para", "por", "em", "the", "of"}


@dataclass
class CardBlockResolution:
    block_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reason: str = "needs-confirmation"


def _tokens(text: str) -> set:
    return {t for t in norm_ascii_lower(text).split() if t and t not in _STOP and len(t) > 2}


def _unit_tokens(unit: dict) -> set:
    parts = [str(unit.get("title") or "")]
    parts += [str(x) for x in (unit.get("topics") or [])]
    parts += [str(x) for x in (unit.get("topic_phrases") or [])]
    parts += [str(x) for x in (unit.get("distinctive_tokens") or [])]
    return _tokens(" ".join(parts))


def resolve_card_to_block(card_name, unit_index, blocks) -> CardBlockResolution:
    card_tokens = _tokens(str(card_name or ""))

    # (2) data explícita no nome -> bloco que cobre a data (mês/dia).
    m = _DATE_RE.search(str(card_name or ""))
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        for b in blocks:
            start, end = str(b.get("period_start") or ""), str(b.get("period_end") or "")
            if _date_in_range(month, day, start, end):
                return CardBlockResolution([str(b.get("id"))], 0.9, f"date:{day:02d}/{month:02d}")

    # (1) nome -> unidade por overlap de tokens.
    best_unit, best_overlap = None, 0
    for unit in unit_index or []:
        overlap = len(card_tokens & _unit_tokens(unit))
        if overlap > best_overlap:
            best_unit, best_overlap = unit, overlap
    if best_unit is not None and best_overlap >= 2:
        slug = str(best_unit.get("slug"))
        ids = [str(b.get("id")) for b in blocks if str(b.get("unit_slug") or "") == slug]
        if ids:
            conf = min(0.95, 0.5 + 0.15 * best_overlap)
            return CardBlockResolution(ids, conf, f"unit:{slug}")

    return CardBlockResolution([], 0.0, "needs-confirmation")


def _date_in_range(month: int, day: int, start_iso: str, end_iso: str) -> bool:
    def md(iso: str):
        parts = iso.split("-")
        return (int(parts[1]), int(parts[2])) if len(parts) == 3 else None
    s, e = md(start_iso), md(end_iso)
    if not s or not e:
        return False
    return s <= (month, day) <= e
```

- [ ] **Step 4: Ver passar**

Run: `python -m pytest tests/test_card_block.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/card_block.py tests/test_card_block.py
git commit -m "feat(cards): resolve_card_to_block (name/date -> block ids)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Mapa persistido `course/.card_block_map.json`

**Files:**
- Modify: `src/builder/timeline/card_block.py`
- Test: `tests/test_card_block.py`

**Contrato:** `load_card_block_map(course_dir) -> dict`, `save_card_block_map(course_dir, mapping)`, `lookup_card_blocks(card_name, card_map, unit_index, blocks) -> List[str]`. O mapa: `{card_name: {"block_ids": [...], "source": "manual"|"auto"}}`. `lookup_card_blocks`: mapa manual vence; senão resolve on-the-fly via `resolve_card_to_block` (não persiste — leitura).

- [ ] **Step 1: Teste que falha**

Adicionar a `tests/test_card_block.py`:

```python
from src.builder.timeline.card_block import (
    load_card_block_map, save_card_block_map, lookup_card_blocks,
)


def test_card_map_roundtrip(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    mapping = {"Meu Card": {"block_ids": ["bloco-07"], "source": "manual"}}
    save_card_block_map(course, mapping)
    assert load_card_block_map(course) == mapping


def test_load_missing_map_returns_empty(tmp_path):
    assert load_card_block_map(tmp_path / "course") == {}


def test_lookup_prefers_manual_map_over_auto():
    card_map = {"Verificação de Programas": {"block_ids": ["bloco-99"], "source": "manual"}}
    ids = lookup_card_blocks("Verificação de Programas", card_map, UNITS, BLOCKS)
    assert ids == ["bloco-99"]   # mapa manual vence o auto (que daria bloco-10/11)


def test_lookup_falls_back_to_auto_resolution():
    ids = lookup_card_blocks("Verificação de Programas", {}, UNITS, BLOCKS)
    assert set(ids) == {"bloco-10", "bloco-11"}
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_card_block.py -k "map or lookup" -v`
Expected: FAIL — `ImportError: cannot import name 'load_card_block_map'`

- [ ] **Step 3: Implementar (em `card_block.py`)**

Adicionar `import json` e `from pathlib import Path` ao topo, e ao fim:

```python
_CARD_MAP_NAME = ".card_block_map.json"


def load_card_block_map(course_dir) -> Dict[str, dict]:
    path = Path(course_dir) / _CARD_MAP_NAME
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_card_block_map(course_dir, mapping) -> None:
    course = Path(course_dir)
    course.mkdir(parents=True, exist_ok=True)
    (course / _CARD_MAP_NAME).write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def lookup_card_blocks(card_name, card_map, unit_index, blocks) -> List[str]:
    entry = (card_map or {}).get(str(card_name or ""))
    if entry and entry.get("block_ids"):
        return [str(b) for b in entry["block_ids"]]
    return list(resolve_card_to_block(card_name, unit_index, blocks).block_ids)
```

- [ ] **Step 4: Ver passar**

Run: `python -m pytest tests/test_card_block.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/card_block.py tests/test_card_block.py
git commit -m "feat(cards): persist + lookup card_block_map (manual over auto)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Degrau card→bloco em `resolve_unit_block_tags`

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py` (`resolve_unit_block_tags`, ~960-1014)
- Test: `tests/test_card_block_assignment.py`

**Contrato:** precedência de bloco: `manual_timeline_block_id` > **card→bloco** > scorer lexical. Card mapeia a 1 bloco → esse bloco (band alta). Card mapeia a vários → `_best_instructional_block_fallback` restrito aos blocos do card. Card vazio/sem match → caminho lexical atual (sem regressão).

- [ ] **Step 1: Teste que falha (unit test do degrau, sem rodar pipeline inteira)**

Criar `tests/test_card_block_assignment.py`. Testa a função helper nova `_card_scoped_block` que o resolver usará (isola a lógica testável):

```python
from src.builder.extraction.content_taxonomy import _card_scoped_block

UNITS = [{"slug": "u-verif", "title": "Verificação de Programas", "topics": ["hoare"], "distinctive_tokens": []}]
BLOCKS = [
    {"id": "bloco-10", "unit_slug": "u-verif", "period_start": "2026-04-27", "period_end": "2026-05-04"},
    {"id": "bloco-11", "unit_slug": "u-verif", "period_start": "2026-05-06", "period_end": "2026-05-06"},
    {"id": "bloco-01", "unit_slug": "u-intro", "period_start": "2026-03-02", "period_end": "2026-03-02"},
]


def _score_stub(entry, md, scoped, unit_slug, topic_slug):
    # devolve o último bloco do escopo, conf 0.7 (simula sub-bloco escolhido)
    return scoped[-1], 0.7


def test_card_single_block_is_chosen_with_high_conf():
    entry = {"source_section": "Introdução"}
    units = [{"slug": "u-intro", "title": "Introdução", "topics": [], "distinctive_tokens": []}]
    bid, conf = _card_scoped_block(entry, "", units, BLOCKS, {}, _score_stub)
    assert bid == "bloco-01"
    assert conf >= 0.8


def test_card_wide_uses_scorer_restricted_to_card_blocks():
    entry = {"source_section": "Verificação de Programas"}
    bid, conf = _card_scoped_block(entry, "", UNITS, BLOCKS, {}, _score_stub)
    assert bid == "bloco-11"          # _score_stub escolheu o último do escopo {10,11}
    assert conf == 0.7


def test_no_card_returns_none():
    bid, conf = _card_scoped_block({"source_section": ""}, "", UNITS, BLOCKS, {}, _score_stub)
    assert bid == "" and conf == 0.0


def test_card_with_no_matching_blocks_returns_none():
    bid, conf = _card_scoped_block({"source_section": "Card Fantasma"}, "", UNITS, BLOCKS, {}, _score_stub)
    assert bid == "" and conf == 0.0
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_card_block_assignment.py -v`
Expected: FAIL — `ImportError: cannot import name '_card_scoped_block'`

- [ ] **Step 3: Implementar o helper + wiring**

Em `src/builder/extraction/content_taxonomy.py`, adicionar a função (perto de `_best_instructional_block_fallback`, ~linha 851). `CARD_SINGLE_CONF = 0.85` (band alta via `confidence_band`):

```python
CARD_SINGLE_CONF = 0.85


def _card_scoped_block(entry, markdown_text, unit_index, instructional_blocks,
                       card_map, score_fallback_fn):
    """Degrau card->bloco. Retorna (block_id, confidence) ou ("", 0.0).

    score_fallback_fn(entry, markdown_text, scoped_blocks, unit_slug, topic_slug)
    -> (block, conf): o scorer real restrito aos blocos do card (sub-bloco).
    """
    from src.builder.timeline.card_block import lookup_card_blocks
    card = str(entry.get("source_section") or "").strip()
    if not card:
        return "", 0.0
    ids = set(lookup_card_blocks(card, card_map, unit_index, instructional_blocks))
    if not ids:
        return "", 0.0
    scoped = [b for b in instructional_blocks if str(b.get("id") or "") in ids]
    if not scoped:
        return "", 0.0
    if len(scoped) == 1:
        return str(scoped[0].get("id") or ""), CARD_SINGLE_CONF
    block, conf = score_fallback_fn(entry, markdown_text, scoped, "", "")
    if block is None:
        return "", 0.0
    # piso: dentro do card, confiança nunca abaixo da de card único forte
    return str(block.get("id") or ""), max(float(conf), CARD_SINGLE_CONF)
```

Depois, no `else` de `resolve_unit_block_tags` (após `manual_block` falhar, antes do scorer lexical — inserir entre a linha 966 `else:` e a montagem de `instructional_blocks`/scorer existente). Reestruturar assim:

```python
        else:
            instructional_blocks = [
                block
                for block in (timeline_context.get("timeline_index") or {}).get("blocks", [])
                or []
                if not bool(block.get("administrative_only"))
            ]
            # --- Degrau card->bloco (gabarito-cards): vence o lexical ---
            _card_map = {}
            if repo_root:
                try:
                    from src.builder.timeline.card_block import load_card_block_map
                    _card_map = load_card_block_map(Path(repo_root) / "course")
                except Exception:
                    _card_map = {}
            _card_bid, _card_conf = _card_scoped_block(
                entry, markdown_text, unit_index, instructional_blocks, _card_map,
                lambda e, md, scoped, us, ts: _best_instructional_block_fallback(e, md, scoped, us, ts),
            )
            if _card_bid:
                period_block_id = _card_bid
                block_confidence = _card_conf
            elif instructional_blocks:
                # ... (scorer lexical atual: select_probable_period_for_entry_fn + fallback) ...
```

O bloco do scorer lexical existente (linhas 973-1014) passa a ser o corpo do `elif instructional_blocks:` (apenas re-indentado; nenhuma lógica alterada). NÃO duplicar — mover o existente para dentro do `elif`.

- [ ] **Step 4: Ver passar (unit do helper)**

Run: `python -m pytest tests/test_card_block_assignment.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Suíte completa (sem regressão no caminho lexical)**

Run: `python -m pytest -q`
Expected: verde. Entries sem `source_section` seguem idênticos (degrau retorna cedo).

- [ ] **Step 6: Commit**

```bash
git add src/builder/extraction/content_taxonomy.py tests/test_card_block_assignment.py
git commit -m "feat(cards): card->block step in resolve_unit_block_tags (beats lexical)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Medição card-as-truth

**Files:**
- Create: `scripts/eval_cards.py`
- Test: `tests/test_eval_cards.py`

**Contrato:** para cada entry com `source_section`, blocos esperados = `lookup_card_blocks(card, card_map, units, blocks)`; acerto = `computed_block_id ∈ esperados`. Reporta acurácia, confident-wrong (band alta & fora do card), cobertura (quantos têm card). Função de cálculo é pura/testável; o script só lê manifest + timeline + card_map.

- [ ] **Step 1: Teste que falha**

Criar `tests/test_eval_cards.py`:

```python
from scripts.eval_cards import evaluate_cards


def test_evaluate_cards_counts_in_card_as_correct():
    entries = [
        {"id": "a", "source_section": "Verif", "computed_block_id": "bloco-10", "computed_block_band": "alta"},
        {"id": "b", "source_section": "Verif", "computed_block_id": "bloco-99", "computed_block_band": "alta"},
        {"id": "c", "source_section": "", "computed_block_id": "bloco-01", "computed_block_band": "media"},
    ]
    expected = {"Verif": ["bloco-10", "bloco-11"]}  # card -> blocos
    rep = evaluate_cards(entries, expected)
    assert rep["with_card"] == 2
    assert rep["correct"] == 1            # a dentro, b fora
    assert rep["confident_wrong"] == 1    # b: band alta e fora do card
    assert abs(rep["accuracy"] - 0.5) < 1e-9
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_eval_cards.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.eval_cards'`

- [ ] **Step 3: Implementar `scripts/eval_cards.py`**

```python
"""Medição file->bloco usando o CARD como verdade (gabarito automático).

Para cada material com source_section, compara computed_block_id ao(s) bloco(s)
do card. Sem rótulo manual. Reporta acurácia, confiante-e-errado, cobertura.

Uso:
    python -m scripts.eval_cards <repo_root>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def evaluate_cards(entries, expected_by_card) -> dict:
    with_card = correct = confident_wrong = 0
    cases = []
    for e in entries or []:
        card = str(e.get("source_section") or "").strip()
        if not card:
            continue
        expected = set(expected_by_card.get(card, []))
        if not expected:
            continue
        with_card += 1
        bid = str(e.get("computed_block_id") or "")
        ok = bid in expected
        if ok:
            correct += 1
        elif str(e.get("computed_block_band") or "") == "alta":
            confident_wrong += 1
        cases.append({"id": e.get("id"), "card": card, "block": bid, "ok": ok})
    return {
        "with_card": with_card,
        "correct": correct,
        "confident_wrong": confident_wrong,
        "accuracy": (correct / with_card) if with_card else 0.0,
        "cases": cases,
    }


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    pos = [a for a in argv if not a.startswith("-")]
    if not pos:
        print("uso: python -m scripts.eval_cards <repo_root>")
        return 2
    repo_root = Path(pos[0])
    manifest = json.loads((repo_root / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    tl = json.loads((repo_root / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
    blocks = tl.get("blocks", [])

    from src.builder.timeline.card_block import load_card_block_map, lookup_card_blocks
    from src.builder.facade.teaching_timeline import build_file_map_unit_index_from_course

    card_map = load_card_block_map(repo_root / "course")
    # unit_index: reconstroi do course_meta minimal (repo_root basta p/ ler COURSE_MAP/teaching_plan)
    try:
        units = build_file_map_unit_index_from_course({"_repo_root": str(repo_root)}, None)
    except Exception:
        units = []

    cards = {str(e.get("source_section") or "").strip() for e in entries if e.get("source_section")}
    expected_by_card = {c: lookup_card_blocks(c, card_map, units, blocks) for c in cards if c}

    rep = evaluate_cards(entries, expected_by_card)
    print("=== Eval cards (card como verdade) ===")
    print(f"Materiais com card: {rep['with_card']}")
    print(f"Dentro do card (correto): {rep['correct']}  ({rep['accuracy']*100:.1f}%)")
    print(f"Confiante e FORA do card (band alta): {rep['confident_wrong']}")
    print("Baseline lexical (hand CSV): 62,5% / 11 confident-wrong")
    wrong = [c for c in rep["cases"] if not c["ok"]]
    if wrong:
        print("\nFora do card:")
        for c in wrong:
            print(f"  - {c['id']:<28} card={c['card']:<28} previu={c['block'] or '(orfao)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Ver passar**

Run: `python -m pytest tests/test_eval_cards.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/eval_cards.py tests/test_eval_cards.py
git commit -m "feat(eval): card-as-truth file->block measurement

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Validação end-to-end (manual, após as 6 tasks — não é commit)

Ordem pra testar no Métodos (o controller executa e reporta números; NÃO automatizar como task):
1. `python -m scripts.backfill_source_section "<repo>" "<stash>" --write` — carimba os 32 casados.
2. App: matéria Métodos ativa → **📥 Importar do stash** → enfileira só os ~23 inéditos → processa.
3. App: rodar **regeneração pedagógica** (op `run_pedagogical_regeneration`) → re-roda `resolve_unit_block_tags` com o degrau card.
4. `python -m scripts.eval_cards "<repo>"` — acurácia card-as-truth.
5. `python -m scripts.eval_ground_truth "<repo>" docs/eval/metodos-file-block.csv` — comparar à baseline 62,5%/11.

**Gate de aceite:** acurácia card-as-truth > baseline lexical e confident-wrong em queda. Se regressão, investigar antes de seguir.

---

## Fora de escopo (deste plano)

- **Telinha de confirmação de cards** (UI Tkinter pra editar `.card_block_map.json` nos `needs-confirmation`) — Plano 2b. O auto-resolve (`resolve_card_to_block`) já cobre os cards que casam por nome; a UI só agrega os ambíguos/sem-match.
- Scraper Moodle; desync timeline×manifest; refator visual do Cronograma.

## Notas de execução

- Hook `code-review-graph.exe` imprime `UnicodeEncodeError` cosmético no commit — passa; ignorar.
- Trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- NÃO gravar índices/manifests dos cursos reais como efeito de teste automatizado — só na validação manual acima, decidida pelo usuário.
