# Build Metrics no BUILD_REPORT — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Anexar ao `BUILD_REPORT.md` uma seção "Custos e qualidade do build" com páginas processadas via Datalab (proxy de custo), parse_quality médio e % de PDFs escaneados, via um módulo modular de collectors.

**Architecture:** Módulo puro novo `src/builder/artifacts/build_metrics.py` com collectors isolados (`collect_scan_stats` manifest-only; `collect_datalab_metrics` lê cada sidecar Datalab 1x), um orquestrador `collect_build_metrics` e um renderer `render_build_metrics_md`. `write_build_report` (`src/builder/artifacts/repo.py`) chama collect+render e anexa as linhas. Métricas novas no futuro = novo collector + linha no render, sem tocar o existente.

**Tech Stack:** Python 3.13, dataclasses, pytest. Sem libs novas.

**Spec:** `docs/superpowers/specs/2026-06-11-build-metrics-design.md`

---

## Contexto de codebase (leia antes de começar)

- `src/builder/artifacts/repo.py:441` define `write_build_report(root_dir, manifest, *, preferred_platform, ...)`. Monta uma lista `report` de strings e ao fim faz `write_text_fn(root_dir / "BUILD_REPORT.md", "\n".join(report) + "\n")`. A última coisa que ele anexa hoje é o bloco "## Regras práticas de curadoria" (~linha 489-496).
- `manifest` é um dict com chave `"entries"` (lista de dicts). Cada entry de PDF tem:
  - `entry["file_type"]` == `"pdf"`.
  - `entry["document_report"]` (dict) com `page_count` (int) e `suspected_scan` (bool). **Pode faltar** em entries não-PDF ou PDFs sem profiling — sempre use `.get(...)`.
  - `entry["advanced_backend"]` == `"datalab"` quando o backend avançado foi Datalab.
  - `entry["advanced_metadata_path"]` (str, caminho relativo a `root_dir`) apontando para `staging/markdown-auto/datalab/<id>/datalab-run.json`.
- O sidecar `datalab-run.json` é um JSON com (entre outras) as chaves: `selected_pages_count` (int), `page_count` (int), `parse_quality_score` (float ou `null`).
- Convenção do projeto: módulos em `src/...`, testes em `tests/test_<nome>.py`, `from __future__ import annotations` no topo, type hints. Os testes rodam com `pytest` a partir da raiz do repo.
- Os ~1179 testes atuais passam. Não quebrar nenhum.

## File Structure

- **Create** `src/builder/artifacts/build_metrics.py` — módulo puro: dataclasses `ScanStats`, `DatalabMetrics`, `BuildMetrics`; funções `collect_scan_stats`, `collect_datalab_metrics`, `collect_build_metrics`, `render_build_metrics_md`. Responsabilidade única: derivar e renderizar métricas a partir do manifest + sidecars. Nenhuma escrita em disco.
- **Modify** `src/builder/artifacts/repo.py` — `write_build_report` passa a importar e chamar `collect_build_metrics` + `render_build_metrics_md`, anexando as linhas ao `report`.
- **Create** `tests/test_build_metrics.py` — testes unitários dos collectors e do renderer.
- **Modify** `tests/test_build_metrics.py` (Task 4) — teste de integração que chama `write_build_report` real e checa a seção no texto.

---

### Task 1: `collect_scan_stats` + `ScanStats`

**Files:**
- Create: `src/builder/artifacts/build_metrics.py`
- Test: `tests/test_build_metrics.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build_metrics.py
from src.builder.artifacts.build_metrics import collect_scan_stats, ScanStats


def test_collect_scan_stats_counts_scanned_pdfs_and_pages():
    entries = [
        {"file_type": "pdf", "document_report": {"page_count": 10, "suspected_scan": True}},
        {"file_type": "pdf", "document_report": {"page_count": 20, "suspected_scan": False}},
        {"file_type": "pdf", "document_report": {"page_count": 30, "suspected_scan": True}},
        {"file_type": "image", "document_report": {"page_count": 1, "suspected_scan": True}},  # ignorado (não-PDF)
        {"file_type": "pdf"},  # sem document_report → conta como pdf, 0 páginas, não-escaneado
    ]
    stats = collect_scan_stats(entries)
    assert stats == ScanStats(pdf_total=4, scanned_count=2, total_pages=60, scanned_pages=40)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_metrics.py::test_collect_scan_stats_counts_scanned_pdfs_and_pages -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.builder.artifacts.build_metrics'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/builder/artifacts/build_metrics.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ScanStats:
    pdf_total: int
    scanned_count: int
    total_pages: int
    scanned_pages: int


def collect_scan_stats(entries: List[dict]) -> ScanStats:
    """Conta PDFs escaneados e páginas a partir de entry['document_report'].
    Entries não-PDF são ignorados. document_report ausente => 0 páginas,
    não-escaneado."""
    pdf_total = 0
    scanned_count = 0
    total_pages = 0
    scanned_pages = 0
    for entry in entries:
        if (entry or {}).get("file_type") != "pdf":
            continue
        pdf_total += 1
        report = entry.get("document_report") or {}
        pages = int(report.get("page_count") or 0)
        total_pages += pages
        if bool(report.get("suspected_scan")):
            scanned_count += 1
            scanned_pages += pages
    return ScanStats(
        pdf_total=pdf_total,
        scanned_count=scanned_count,
        total_pages=total_pages,
        scanned_pages=scanned_pages,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_build_metrics.py::test_collect_scan_stats_counts_scanned_pdfs_and_pages -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/build_metrics.py tests/test_build_metrics.py
git commit -m "feat(metrics): collect_scan_stats para % PDFs escaneados"
```

---

### Task 2: `collect_datalab_metrics` + `DatalabMetrics`

**Files:**
- Modify: `src/builder/artifacts/build_metrics.py`
- Test: `tests/test_build_metrics.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_build_metrics.py  (adicionar imports no topo do arquivo)
import json
from pathlib import Path
from src.builder.artifacts.build_metrics import collect_datalab_metrics, DatalabMetrics


def _write_sidecar(root: Path, rel: str, payload: dict) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def test_collect_datalab_metrics_sums_pages_and_averages_quality(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"selected_pages_count": 5, "page_count": 5, "parse_quality_score": 0.8})
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/b/datalab-run.json",
                   {"selected_pages_count": 3, "page_count": 10, "parse_quality_score": 0.9})
    entries = [
        {"advanced_backend": "datalab", "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"},
        {"advanced_backend": "datalab", "advanced_metadata_path": "staging/markdown-auto/datalab/b/datalab-run.json"},
        {"advanced_backend": "marker", "advanced_metadata_path": "x"},  # ignorado (não-datalab)
        {"advanced_backend": "datalab"},  # ignorado (sem metadata_path)
    ]
    m = collect_datalab_metrics(entries, tmp_path)
    assert m.entry_count == 2
    assert m.processed_pages == 8  # 5 + 3 (usa selected_pages_count)
    assert m.avg_parse_quality == 0.85


def test_collect_datalab_metrics_uses_page_count_fallback(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"page_count": 7, "parse_quality_score": None})
    entries = [{"advanced_backend": "datalab",
                "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"}]
    m = collect_datalab_metrics(entries, tmp_path)
    assert m.processed_pages == 7  # sem selected_pages_count → cai em page_count
    assert m.avg_parse_quality is None  # nenhum score válido


def test_collect_datalab_metrics_skips_broken_sidecar(tmp_path):
    (tmp_path / "staging/markdown-auto/datalab/a").mkdir(parents=True)
    (tmp_path / "staging/markdown-auto/datalab/a/datalab-run.json").write_text("{not json", encoding="utf-8")
    entries = [
        {"advanced_backend": "datalab", "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"},
        {"advanced_backend": "datalab", "advanced_metadata_path": "staging/markdown-auto/datalab/missing/datalab-run.json"},
    ]
    m = collect_datalab_metrics(entries, tmp_path)  # não levanta exceção
    assert m == DatalabMetrics(entry_count=0, processed_pages=0, avg_parse_quality=None)


def test_collect_datalab_metrics_empty():
    m = collect_datalab_metrics([], Path("."))
    assert m == DatalabMetrics(entry_count=0, processed_pages=0, avg_parse_quality=None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_build_metrics.py -k datalab -v`
Expected: FAIL com `ImportError: cannot import name 'collect_datalab_metrics'`

- [ ] **Step 3: Write the implementation**

Adicione ao topo de `src/builder/artifacts/build_metrics.py` os imports faltantes (`json`, `Path`):

```python
# src/builder/artifacts/build_metrics.py — atualizar bloco de imports do topo
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
```

Adicione a dataclass e a função (após `collect_scan_stats`):

```python
@dataclass(frozen=True)
class DatalabMetrics:
    entry_count: int
    processed_pages: int
    avg_parse_quality: Optional[float]


def collect_datalab_metrics(entries: List[dict], root_dir: Path) -> DatalabMetrics:
    """Lê cada sidecar datalab-run.json 1x. Soma páginas processadas
    (selected_pages_count, fallback page_count) e calcula a média dos
    parse_quality_score válidos. Sidecar ausente/inválido => entry pulado."""
    entry_count = 0
    processed_pages = 0
    quality_scores: List[float] = []
    for entry in entries:
        entry = entry or {}
        if entry.get("advanced_backend") != "datalab":
            continue
        rel = entry.get("advanced_metadata_path")
        if not rel:
            continue
        try:
            payload = json.loads((Path(root_dir) / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        entry_count += 1
        pages = payload.get("selected_pages_count")
        if pages is None:
            pages = payload.get("page_count")
        processed_pages += int(pages or 0)
        score = payload.get("parse_quality_score")
        if score is not None:
            try:
                quality_scores.append(float(score))
            except (TypeError, ValueError):
                pass
    avg_parse_quality = (
        round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None
    )
    return DatalabMetrics(
        entry_count=entry_count,
        processed_pages=processed_pages,
        avg_parse_quality=avg_parse_quality,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_build_metrics.py -k datalab -v`
Expected: PASS (4 testes)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/build_metrics.py tests/test_build_metrics.py
git commit -m "feat(metrics): collect_datalab_metrics (paginas processadas + parse_quality)"
```

---

### Task 3: `collect_build_metrics` + `render_build_metrics_md` + `BuildMetrics`

**Files:**
- Modify: `src/builder/artifacts/build_metrics.py`
- Test: `tests/test_build_metrics.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_build_metrics.py  (adicionar import)
from src.builder.artifacts.build_metrics import (
    collect_build_metrics, render_build_metrics_md, BuildMetrics,
)


def test_collect_build_metrics_orchestrates(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"selected_pages_count": 4, "parse_quality_score": 0.9})
    manifest = {"entries": [
        {"file_type": "pdf", "document_report": {"page_count": 4, "suspected_scan": True},
         "advanced_backend": "datalab",
         "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"},
        {"file_type": "pdf", "document_report": {"page_count": 6, "suspected_scan": False}},
    ]}
    m = collect_build_metrics(manifest, tmp_path)
    assert m.scan.pdf_total == 2
    assert m.scan.scanned_count == 1
    assert m.datalab.entry_count == 1
    assert m.datalab.processed_pages == 4


def test_collect_build_metrics_missing_entries_key(tmp_path):
    m = collect_build_metrics({}, tmp_path)  # sem "entries"
    assert m.scan.pdf_total == 0
    assert m.datalab.entry_count == 0


def test_render_build_metrics_md_with_data():
    metrics = BuildMetrics(
        scan=ScanStats(pdf_total=7, scanned_count=2, total_pages=350, scanned_pages=80),
        datalab=DatalabMetrics(entry_count=3, processed_pages=42, avg_parse_quality=0.91),
    )
    lines = render_build_metrics_md(metrics)
    text = "\n".join(lines)
    assert "## Custos e qualidade do build" in text
    assert "páginas processadas via Datalab: 42 (em 3 arquivo(s))" in text
    assert "parse_quality médio (Datalab): 0.91" in text
    assert "PDFs escaneados: 2 de 7 (29%) · 80 de 350 páginas" in text


def test_render_build_metrics_md_empty():
    metrics = BuildMetrics(
        scan=ScanStats(pdf_total=0, scanned_count=0, total_pages=0, scanned_pages=0),
        datalab=DatalabMetrics(entry_count=0, processed_pages=0, avg_parse_quality=None),
    )
    text = "\n".join(render_build_metrics_md(metrics))
    assert "## Custos e qualidade do build" in text
    assert "nenhum arquivo via Datalab" in text
    assert "parse_quality médio (Datalab): —" in text
    assert "PDFs escaneados: 0 de 0" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_build_metrics.py -k "build_metrics or render" -v`
Expected: FAIL com `ImportError: cannot import name 'collect_build_metrics'`

- [ ] **Step 3: Write the implementation**

Adicione ao final de `src/builder/artifacts/build_metrics.py`:

```python
@dataclass(frozen=True)
class BuildMetrics:
    scan: ScanStats
    datalab: DatalabMetrics


def collect_build_metrics(manifest: dict, root_dir: Path) -> BuildMetrics:
    """Orquestra os collectors a partir do manifest."""
    entries = (manifest or {}).get("entries") or []
    return BuildMetrics(
        scan=collect_scan_stats(entries),
        datalab=collect_datalab_metrics(entries, root_dir),
    )


def _pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def render_build_metrics_md(metrics: BuildMetrics) -> List[str]:
    """Renderiza a seção markdown 'Custos e qualidade do build'.
    Sempre retorna a seção; usa '—' / textos de vazio quando não há dado."""
    dl = metrics.datalab
    scan = metrics.scan

    if dl.entry_count:
        pages_line = (
            f"- páginas processadas via Datalab: {dl.processed_pages} "
            f"(em {dl.entry_count} arquivo(s)) — proxy de custo (Datalab bilha por página)"
        )
    else:
        pages_line = "- páginas processadas via Datalab: — (nenhum arquivo via Datalab)"

    quality = f"{dl.avg_parse_quality:.2f}" if dl.avg_parse_quality is not None else "—"

    scan_line = (
        f"- PDFs escaneados: {scan.scanned_count} de {scan.pdf_total} "
        f"({_pct(scan.scanned_count, scan.pdf_total)}%) · "
        f"{scan.scanned_pages} de {scan.total_pages} páginas"
    )

    return [
        "",
        "## Custos e qualidade do build",
        pages_line,
        f"- parse_quality médio (Datalab): {quality}",
        scan_line,
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_build_metrics.py -v`
Expected: PASS (todos os testes do arquivo)

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/build_metrics.py tests/test_build_metrics.py
git commit -m "feat(metrics): collect_build_metrics + render_build_metrics_md"
```

---

### Task 4: Integrar em `write_build_report`

**Files:**
- Modify: `src/builder/artifacts/repo.py:441-497`
- Test: `tests/test_build_metrics.py`

- [ ] **Step 1: Write the failing integration test**

```python
# tests/test_build_metrics.py
from src.builder.artifacts.repo import write_build_report


def test_write_build_report_includes_metrics_section(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"selected_pages_count": 5, "parse_quality_score": 0.88})
    manifest = {
        "generated_at": "2026-06-11T00:00:00",
        "entries": [
            {"file_type": "pdf", "document_report": {"page_count": 5, "suspected_scan": False},
             "advanced_backend": "datalab",
             "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"},
        ],
    }
    captured = {}

    def fake_write_text(path, text):
        captured["path"] = path
        captured["text"] = text

    write_build_report(
        tmp_path,
        manifest,
        preferred_platform="claude",
        has_pymupdf=True,
        has_pymupdf4llm=True,
        has_pdfplumber=True,
        has_datalab_api_key_fn=lambda: True,
        docling_cli=None,
        has_docling_python_api_fn=lambda: False,
        marker_cli=None,
        write_text_fn=fake_write_text,
    )

    assert "## Custos e qualidade do build" in captured["text"]
    assert "páginas processadas via Datalab: 5 (em 1 arquivo(s))" in captured["text"]
    assert "parse_quality médio (Datalab): 0.88" in captured["text"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_metrics.py::test_write_build_report_includes_metrics_section -v`
Expected: FAIL — `assert "## Custos e qualidade do build" in captured["text"]` (seção ainda não anexada)

- [ ] **Step 3: Add the import near the top of `src/builder/artifacts/repo.py`**

Localize o bloco de imports no topo do arquivo (já há `from pathlib import Path` etc.) e acrescente:

```python
from src.builder.artifacts.build_metrics import (
    collect_build_metrics,
    render_build_metrics_md,
)
```

- [ ] **Step 4: Anexar a seção em `write_build_report`**

Em `src/builder/artifacts/repo.py`, dentro de `write_build_report`, o bloco atual é:

```python
    report.extend([
        "",
        "## Regras práticas de curadoria",
        "- PDFs simples: camada base costuma bastar.",
        "- PDFs com fórmulas, scans, layout complexo ou provas: camada avançada + revisão manual.",
        "- O conhecimento final do tutor deve sair de `manual-review/` e depois ser promovido.",
        "- Atualizar `student/STUDENT_STATE.md` após cada sessão de estudo.",
    ])
    write_text_fn(root_dir / "BUILD_REPORT.md", "\n".join(report) + "\n")
```

Insira a chamada às métricas entre o `report.extend([...])` das regras e a linha `write_text_fn(...)`:

```python
    report.extend([
        "",
        "## Regras práticas de curadoria",
        "- PDFs simples: camada base costuma bastar.",
        "- PDFs com fórmulas, scans, layout complexo ou provas: camada avançada + revisão manual.",
        "- O conhecimento final do tutor deve sair de `manual-review/` e depois ser promovido.",
        "- Atualizar `student/STUDENT_STATE.md` após cada sessão de estudo.",
    ])
    report.extend(render_build_metrics_md(collect_build_metrics(manifest, root_dir)))
    write_text_fn(root_dir / "BUILD_REPORT.md", "\n".join(report) + "\n")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_build_metrics.py::test_write_build_report_includes_metrics_section -v`
Expected: PASS

- [ ] **Step 6: Run the full build_metrics suite + a sanity check on the broader suite**

Run: `pytest tests/test_build_metrics.py -v`
Expected: PASS (todos)

Run: `pytest tests/test_core.py -q`
Expected: PASS (nenhuma regressão; `write_build_report` é tipicamente stubbado no build, mas o import novo não pode quebrar a importação do módulo)

- [ ] **Step 7: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_build_metrics.py
git commit -m "feat(metrics): anexa secao de custos/qualidade ao BUILD_REPORT"
```

---

## Pós-implementação

Após todas as tasks e a revisão final:
- Rodar a suíte completa: `pytest -q`. Esperado: todos passam (1179 + novos).
- Atualizar `docs/reports/2026-06-09-relatorio-sistema.html`: marcar #5 como ✅ FEITO no roadmap (item 5, ~linha 412) e na priorização (linha "2,3,4,5"). Descrever a versão entregue (proxy de custo por páginas Datalab, % escaneados, parse_quality; cost-dict e imagens rejeitadas como slots futuros).

## Self-Review (preenchido pelo autor do plano)

1. **Spec coverage:** Páginas Datalab (proxy de custo) → Task 2. parse_quality médio → Task 2. % escaneados → Task 1. Render da seção → Task 3. Integração no BUILD_REPORT → Task 4. Tratamento de erro de sidecar → Task 2 (test + impl). Não-objetivos (cost-dict, imagens) não viram task — correto. ✔
2. **Placeholder scan:** Sem TBD/TODO; todo passo tem código completo e comando com saída esperada. ✔
3. **Type consistency:** `ScanStats`/`DatalabMetrics`/`BuildMetrics` e assinaturas `collect_scan_stats(entries)`, `collect_datalab_metrics(entries, root_dir)`, `collect_build_metrics(manifest, root_dir)`, `render_build_metrics_md(metrics)` idênticas entre Tasks 1-4. ✔
