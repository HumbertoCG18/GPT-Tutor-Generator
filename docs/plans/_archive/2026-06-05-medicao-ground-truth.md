# Medição de Correção com Ground-Truth — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tooling que mede a correção real da atribuição file→bloco contra um repo gerado real + rótulos de verdade (CSV), reportando acurácia, confusão, `confident_wrong` e calibração por band — sem re-rodar o scorer.

**Architecture:** Dois scripts em `scripts/` (lógica em funções puras, CLIs finas), mirror do padrão de `scripts/eval_assignments.py` (testes importam `from scripts.X import ...`). Lê predições de `manifest.json` e bloco→período de `course/.timeline_index.json`.

**Tech Stack:** Python, pytest, csv/json stdlib. Sem disco real nos testes (usa `tmp_path`).

**Base:** 906 testes verdes.

---

### Task 1: `eval_ground_truth.py` — loaders

**Files:**
- Create: `scripts/eval_ground_truth.py`
- Test: `tests/test_eval_ground_truth.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
import csv
import json
from pathlib import Path

from scripts.eval_ground_truth import (
    load_predictions, load_block_period_map, load_labels_csv,
)


def _make_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    manifest = {
        "entries": [
            {"id": "m-ok", "title": "Aula 1", "category": "material-de-aula",
             "computed_block_id": "bloco-01", "computed_block_band": "alta",
             "computed_block_confidence": 0.9, "markdown_path": "content/curated/m-ok.md"},
            {"id": "m-confwrong", "title": "Aula 2", "category": "material-de-aula",
             "computed_block_id": "bloco-02", "computed_block_band": "alta",
             "computed_block_confidence": 0.88, "markdown_path": "content/curated/m2.md"},
            # entry órfão: sem computed_block_id/band (to_dict omitiu defaults)
            {"id": "m-orfao", "title": "Aula 3", "category": "material-de-aula",
             "markdown_path": "content/curated/m3.md"},
        ]
    }
    (repo / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    timeline = {"version": 4, "blocks": [
        {"id": "bloco-01", "period_label": "Semana 1"},
        {"id": "bloco-02", "period_label": "Semana 2"},
        {"id": "bloco-03", "period_label": "Semana 3"},
    ]}
    (repo / "course" / ".timeline_index.json").write_text(json.dumps(timeline), encoding="utf-8")
    return repo


def test_load_predictions_reads_fields_with_defaults(tmp_path):
    repo = _make_repo(tmp_path)
    preds = load_predictions(repo)
    assert preds["m-ok"]["block_id"] == "bloco-01"
    assert preds["m-ok"]["band"] == "alta"
    assert preds["m-orfao"]["block_id"] == ""   # default ausente
    assert preds["m-orfao"]["band"] == ""
    assert preds["m-ok"]["markdown_path"] == "content/curated/m-ok.md"


def test_load_block_period_map(tmp_path):
    repo = _make_repo(tmp_path)
    m = load_block_period_map(repo)
    assert m["bloco-01"] == "Semana 1"
    assert m["bloco-03"] == "Semana 3"


def test_load_labels_csv_skips_empty_true(tmp_path):
    p = tmp_path / "labels.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "true_block_id"])
        w.writerow(["m-ok", "bloco-01"])
        w.writerow(["m-skip", ""])
    labels = load_labels_csv(p)
    assert labels == {"m-ok": "bloco-01"}
```

- [ ] **Step 2: Rodar — verificar que falham**

Run: `python -m pytest tests/test_eval_ground_truth.py -v`
Expected: FAIL — ImportError (módulo não existe).

- [ ] **Step 3: Implementar `scripts/eval_ground_truth.py` (loaders)**

```python
"""Harness de medicao de correcao file->bloco contra um repo gerado real.

Le predicoes do manifest.json + bloco->periodo do course/.timeline_index.json
e compara com rotulos de verdade (CSV). Reporta acuracia, confusao,
confiante-e-errado e calibracao por band. Nao re-roda o scorer.

Uso:
    python scripts/eval_ground_truth.py <repo_root> <labels.csv>
    python scripts/eval_ground_truth.py <repo_root> <labels.csv> --json
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def load_predictions(repo_root: Path) -> dict:
    manifest = json.loads((Path(repo_root) / "manifest.json").read_text(encoding="utf-8"))
    preds = {}
    for e in manifest.get("entries", []):
        eid = str(e.get("id", ""))
        if not eid:
            continue
        preds[eid] = {
            "block_id": str(e.get("computed_block_id", "")),
            "band": str(e.get("computed_block_band", "")),
            "confidence": float(e.get("computed_block_confidence", 0.0) or 0.0),
            "title": str(e.get("title", "")),
            "category": str(e.get("category", "")),
            "markdown_path": str(e.get("markdown_path", "") or e.get("base_markdown", "")),
        }
    return preds


def load_block_period_map(repo_root: Path) -> dict:
    path = Path(repo_root) / "course" / ".timeline_index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(b.get("id", "")): str(b.get("period_label", "")) for b in data.get("blocks", [])}


def load_labels_csv(path: Path) -> dict:
    labels = {}
    with Path(path).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            eid = str(row.get("id", "")).strip()
            true_block = str(row.get("true_block_id", "")).strip()
            if eid and true_block:
                labels[eid] = true_block
    return labels
```

- [ ] **Step 4: Rodar — verificar que passam**

Run: `python -m pytest tests/test_eval_ground_truth.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/eval_ground_truth.py tests/test_eval_ground_truth.py
git commit -m "feat(eval): ground-truth loaders (manifest predictions + timeline + labels CSV)"
```

---

### Task 2: `evaluate_ground_truth` — métricas

**Files:**
- Modify: `scripts/eval_ground_truth.py`
- Test: `tests/test_eval_ground_truth.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
from scripts.eval_ground_truth import evaluate_ground_truth


def test_evaluate_metrics(tmp_path):
    repo = _make_repo(tmp_path)
    preds = load_predictions(repo)
    block_map = load_block_period_map(repo)
    labels = {
        "m-ok": "bloco-01",        # predito bloco-01 band alta -> correto
        "m-confwrong": "bloco-03", # predito bloco-02 band alta -> confiante-e-errado
        "m-orfao": "bloco-03",     # predito "" -> missed
    }
    r = evaluate_ground_truth(preds, labels, block_map)
    assert r["total"] == 3
    assert r["correct"] == 1
    assert r["wrong"] == 2
    assert abs(r["block_accuracy"] - 1/3) < 1e-9
    assert r["confident_wrong"] == 1     # m-confwrong
    assert r["orphans"] == 1             # m-orfao previu ""
    assert r["missed"] == 1             # m-orfao tinha verdade mas previu ""
    band_total = sum(b["correct"] + b["wrong"] for b in r["bands"].values())
    assert band_total == r["total"]
    assert r["confusion"]["bloco-03->(orfao)"] == 1


def test_evaluate_only_labeled_entries(tmp_path):
    repo = _make_repo(tmp_path)
    preds = load_predictions(repo)
    block_map = load_block_period_map(repo)
    labels = {"m-ok": "bloco-01"}  # só 1 rotulado
    r = evaluate_ground_truth(preds, labels, block_map)
    assert r["total"] == 1
    assert r["correct"] == 1
```

- [ ] **Step 2: Rodar — verificar que falham**

Run: `python -m pytest tests/test_eval_ground_truth.py::test_evaluate_metrics tests/test_eval_ground_truth.py::test_evaluate_only_labeled_entries -v`
Expected: FAIL — `evaluate_ground_truth` não existe.

- [ ] **Step 3: Implementar — adicionar a `eval_ground_truth.py`**

```python
def evaluate_ground_truth(predictions: dict, labels: dict, block_map: dict) -> dict:
    bands = {"alta": {"correct": 0, "wrong": 0}, "media": {"correct": 0, "wrong": 0},
             "baixa": {"correct": 0, "wrong": 0}, "": {"correct": 0, "wrong": 0}}
    confusion: dict = {}
    rows = []
    correct = orphans = missed = confident_wrong = 0

    for eid, true_block in labels.items():
        pred = predictions.get(eid, {})
        predicted = str(pred.get("block_id", ""))
        band = str(pred.get("band", ""))
        is_correct = predicted == true_block
        if is_correct:
            correct += 1
        if predicted == "":
            orphans += 1
            if true_block:
                missed += 1
        if band == "alta" and not is_correct:
            confident_wrong += 1
        bands.setdefault(band, {"correct": 0, "wrong": 0})
        bands[band]["correct" if is_correct else "wrong"] += 1
        key = f"{true_block}->{predicted or '(orfao)'}"
        confusion[key] = confusion.get(key, 0) + 1
        rows.append({"id": eid, "true": true_block, "predicted": predicted,
                     "band": band, "correct": is_correct,
                     "title": str(pred.get("title", ""))})

    total = len(labels)
    return {
        "total": total, "correct": correct, "wrong": total - correct,
        "block_accuracy": (correct / total) if total else 0.0,
        "orphans": orphans, "missed": missed, "confident_wrong": confident_wrong,
        "bands": bands, "confusion": confusion, "cases": rows,
    }
```

- [ ] **Step 4: Rodar — verificar que passam**

Run: `python -m pytest tests/test_eval_ground_truth.py -v`
Expected: PASS (5 testes acumulados).

- [ ] **Step 5: Commit**

```bash
git add scripts/eval_ground_truth.py tests/test_eval_ground_truth.py
git commit -m "feat(eval): ground-truth metrics (accuracy, confident_wrong, confusion, missed)"
```

---

### Task 3: `format_report` + `main` (CLI)

**Files:**
- Modify: `scripts/eval_ground_truth.py`
- Test: `tests/test_eval_ground_truth.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
from scripts.eval_ground_truth import format_report


def test_format_report_mentions_key_metrics(tmp_path):
    repo = _make_repo(tmp_path)
    preds = load_predictions(repo)
    block_map = load_block_period_map(repo)
    labels = {"m-ok": "bloco-01", "m-confwrong": "bloco-03"}
    r = evaluate_ground_truth(preds, labels, block_map)
    text = format_report(r, block_map)
    assert "Acuracia" in text or "Acurácia" in text
    assert "Confiante e ERRADO" in text or "confiante" in text.lower()
```

- [ ] **Step 2: Rodar — verificar que falha**

Run: `python -m pytest tests/test_eval_ground_truth.py::test_format_report_mentions_key_metrics -v`
Expected: FAIL — `format_report` não existe.

- [ ] **Step 3: Implementar — adicionar a `eval_ground_truth.py`**

```python
def format_report(report: dict, block_map: dict) -> str:
    lines = ["=== Eval ground-truth: atribuicao file -> bloco ==="]
    acc = report["block_accuracy"]
    lines.append(f"Acuracia: {report['correct']}/{report['total']} ({acc * 100:.1f}%)")
    lines.append(f"Orfaos (previu vazio): {report['orphans']}   Missed (verdade tinha bloco): {report['missed']}")
    lines.append(f"Confiante e ERRADO (band alta, bloco errado): {report['confident_wrong']}")
    lines.append("")
    lines.append("Calibracao por band (correto / errado):")
    for band in ("alta", "media", "baixa", ""):
        b = report["bands"].get(band, {"correct": 0, "wrong": 0})
        lines.append(f"  {(band or '(vazio)'):<8} {b['correct']:>3} ok / {b['wrong']:>3} erro")
    wrong = [c for c in report["cases"] if not c["correct"]]
    lines.append("")
    if wrong:
        lines.append("Erros:")
        for c in wrong:
            tp = block_map.get(c["true"], c["true"])
            pp = block_map.get(c["predicted"], c["predicted"] or "(orfao)")
            lines.append(f"  - {c['id']:<24} verdade={c['true'] or '-'} ({tp}) "
                         f"previu={c['predicted'] or '(orfao)'} ({pp}) band={c['band'] or '-'}")
    else:
        lines.append("Sem erros.")
    return "\n".join(lines)


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    as_json = "--json" in argv
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python scripts/eval_ground_truth.py <repo_root> <labels.csv> [--json]")
        return 2
    repo_root, labels_path = Path(pos[0]), Path(pos[1])
    preds = load_predictions(repo_root)
    block_map = load_block_period_map(repo_root)
    labels = load_labels_csv(labels_path)
    report = evaluate_ground_truth(preds, labels, block_map)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report, block_map))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Rodar — verificar que passa**

Run: `python -m pytest tests/test_eval_ground_truth.py -v`
Expected: PASS (6 testes).

- [ ] **Step 5: Commit**

```bash
git add scripts/eval_ground_truth.py tests/test_eval_ground_truth.py
git commit -m "feat(eval): ground-truth report formatter + CLI"
```

---

### Task 4: `make_ground_truth_template.py` — gerador de esqueleto

**Files:**
- Create: `scripts/make_ground_truth_template.py`
- Test: `tests/test_eval_ground_truth.py` (reusa o `_make_repo`)

- [ ] **Step 1: Escrever os testes que falham**

```python
from scripts.make_ground_truth_template import build_template_rows


def test_build_template_rows_prefills_true_with_predicted(tmp_path):
    repo = _make_repo(tmp_path)
    rows = build_template_rows(repo)
    by_id = {r["id"]: r for r in rows}
    assert len(rows) == 3
    assert by_id["m-ok"]["true_block_id"] == "bloco-01"        # pré-preenchido = predito
    assert by_id["m-ok"]["predicted_period"] == "Semana 1"
    assert by_id["m-orfao"]["predicted_block_id"] == ""        # órfão
    assert by_id["m-orfao"]["true_block_id"] == ""             # pré-preenchido = predito (vazio)
    for col in ("id", "title", "category", "markdown_path",
                "predicted_block_id", "predicted_period", "predicted_band", "true_block_id"):
        assert col in rows[0]
```

- [ ] **Step 2: Rodar — verificar que falha**

Run: `python -m pytest tests/test_eval_ground_truth.py::test_build_template_rows_prefills_true_with_predicted -v`
Expected: FAIL — módulo não existe.

- [ ] **Step 3: Implementar `scripts/make_ground_truth_template.py`**

```python
"""Gera um CSV esqueleto de rotulos ground-truth a partir de um repo gerado.

Uma linha por material do manifest, com a predicao atual; a coluna
`true_block_id` ja vem pre-preenchida com o bloco predito (o usuario so
confirma/corrige). Imprime no stdout a referencia de blocos validos.

Uso:
    python scripts/make_ground_truth_template.py <repo_root> <out.csv>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from scripts.eval_ground_truth import load_predictions, load_block_period_map

COLUMNS = ["id", "title", "category", "markdown_path",
           "predicted_block_id", "predicted_period", "predicted_band", "true_block_id"]


def build_template_rows(repo_root: Path) -> list:
    preds = load_predictions(repo_root)
    block_map = load_block_period_map(repo_root)
    rows = []
    for eid, p in preds.items():
        block_id = p.get("block_id", "")
        rows.append({
            "id": eid,
            "title": p.get("title", ""),
            "category": p.get("category", ""),
            "markdown_path": p.get("markdown_path", ""),
            "predicted_block_id": block_id,
            "predicted_period": block_map.get(block_id, ""),
            "predicted_band": p.get("band", ""),
            "true_block_id": block_id,  # pre-preenchido = predito
        })
    return rows


def write_template_csv(rows: list, out_path: Path) -> None:
    with Path(out_path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python scripts/make_ground_truth_template.py <repo_root> <out.csv>")
        return 2
    repo_root, out_path = Path(pos[0]), Path(pos[1])
    rows = build_template_rows(repo_root)
    write_template_csv(rows, out_path)
    block_map = load_block_period_map(repo_root)
    print(f"Esqueleto escrito: {out_path}  ({len(rows)} materiais)")
    print("Blocos validos (id -> periodo):")
    for bid, period in block_map.items():
        print(f"  {bid:<16} {period}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Rodar — verificar que passa**

Run: `python -m pytest tests/test_eval_ground_truth.py -v`
Expected: PASS (7 testes).

- [ ] **Step 5: Commit**

```bash
git add scripts/make_ground_truth_template.py tests/test_eval_ground_truth.py
git commit -m "feat(eval): ground-truth label template generator (prefilled with predictions)"
```

---

### Task 5: Verificação + backlog/ROUTER

**Files:**
- Modify: `docs/superpowers/BACKLOG.md`, `.mex/ROUTER.md`

- [ ] **Step 1: Rodar a suíte completa**

Run: `python -m pytest -q`
Expected: PASS, 0 failures.

- [ ] **Step 2: Atualizar backlog**

Em `docs/superpowers/BACKLOG.md`, item "Medição de correção com ground-truth":
marcar o TOOLING como ENTREGUE (2 scripts + testes), com o fluxo de uso (gerar
esqueleto → rotular assistido → eval). Deixar explícito que os RÓTULOS reais
ainda dependem do usuário apontar um repo + preencher (assistido pelo agente).

- [ ] **Step 3: Atualizar ROUTER**

Em `.mex/ROUTER.md`, seção "Working", linha curta sobre o harness ground-truth
(`scripts/eval_ground_truth.py` + `scripts/make_ground_truth_template.py`):
mede correção real file→bloco contra repo real + CSV de rótulos; métrica-chave
`confident_wrong`; lê manifest + `.timeline_index.json`, não re-roda scorer.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/BACKLOG.md .mex/ROUTER.md
git commit -m "docs: mark ground-truth eval tooling delivered"
```

---

## Self-Review

**Cobertura do spec:** loaders→Task 1; métricas→Task 2; report/CLI→Task 3;
template gen→Task 4; verificação/docs→Task 5. Fluxo de uso documentado no spec +
backlog. ✔

**Placeholders:** todos os Steps têm código completo (scripts + testes). ✔

**Consistência de tipos:** `load_predictions` retorna `dict[id]->{block_id, band,
confidence, title, category, markdown_path}`; `evaluate_ground_truth` consome
essas chaves; `build_template_rows` reusa os loaders e usa `block_id` p/
`predicted_period`. CSV COLUMNS batem com as chaves usadas no teste. Testes
importam exatamente os nomes definidos. ✔

**Risco residual:** nenhum acoplamento com o pipeline real (tudo lê arquivos);
os testes usam `tmp_path`, determinísticos. O `markdown_path` pode estar ausente
no manifest (campo omitido) → `load_predictions` cai pra `base_markdown` e depois
`""`; a rotulação assistida lida com isso lendo o que existir.
