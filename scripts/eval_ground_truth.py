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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_BLOCO_RE = re.compile(r"bloco-(\d+)")


def _ordinal(ref: str):
    """Ordem posicional do display bloco-NN (None se não for bloco-NN)."""
    m = _BLOCO_RE.fullmatch(str(ref or "").strip())
    return int(m.group(1)) if m else None


def _load_blocks(repo_root: Path) -> list:
    """Blocos do timeline com block_uuid injetado do ledger (uuid<->bloco-NN)."""
    tl_path = Path(repo_root) / "course" / ".timeline_index.json"
    if not tl_path.exists():
        return []
    data = json.loads(tl_path.read_text(encoding="utf-8"))
    blocks = data if isinstance(data, list) else data.get("blocks", [])
    led_path = Path(repo_root) / "course" / ".block_identity.json"
    ledger_map = {}
    if led_path.exists():
        led = json.loads(led_path.read_text(encoding="utf-8"))
        recs = led if isinstance(led, list) else led.get("blocks", [])
        ledger_map = {str(r.get("display_id_last") or ""): str(r.get("uuid") or "") for r in recs}
    out = []
    for b in blocks:
        bc = dict(b)
        if not bc.get("block_uuid"):
            bc["block_uuid"] = ledger_map.get(str(bc.get("id") or ""), str(bc.get("id") or ""))
        out.append(bc)
    return out


def _uuid_to_display(blocks: list) -> dict:
    m = {}
    for b in blocks:
        u, d = str(b.get("block_uuid") or ""), str(b.get("id") or "")
        if u and d:
            m[u] = d
    return m


def _canon(ref: str, u2d: dict) -> str:
    """Canonicaliza para display bloco-NN: uuid -> bloco-NN; bloco-NN/'' -> as-is."""
    ref = str(ref or "").strip()
    return u2d.get(ref, ref)


def load_predictions(repo_root: Path) -> dict:
    # Mede contra o bloco TEMPORAL (resolve_temporal_block: temporal_block_id da âncora
    # vence; fallback resolve_effective_block honra manual>computed), canonicalizado para
    # display bloco-NN. Credita os movers da âncora; permite rotular gold em bloco-NN.
    from src.builder.routing.file_map import resolve_temporal_block
    manifest = json.loads((Path(repo_root) / "manifest.json").read_text(encoding="utf-8"))
    blocks = _load_blocks(repo_root)
    u2d = _uuid_to_display(blocks)
    preds = {}
    for e in manifest.get("entries", []):
        eid = str(e.get("id", ""))
        if not eid:
            continue
        preds[eid] = {
            "block_id": _canon(resolve_temporal_block(e, blocks), u2d),
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
    # utf-8-sig: o CSV pode vir com BOM (Excel/Windows gravam assim). Com
    # `utf-8` puro a 1a coluna vira "﻿id", `row.get("id")` devolve None e a
    # regua reporta 0/0 EM SILENCIO — aconteceu com 3 de 5 cursos em 2026-08-19c.
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            eid = str(row.get("id", "")).strip()
            true_block = str(row.get("true_block_id", "")).strip()
            if eid and true_block:
                labels[eid] = true_block
    return labels


def load_pair_keys(path: Path) -> dict:
    """{id: pair_key} das linhas com `pair_key` não-vazio (membros de version-pair).

    `pair_key` = id canônico (Moodle original), gancho ESTRUTURADO do colapso de par.
    Definido por conteúdo na folha (gold_score.VERSION_PAIRS), nunca por bloco computado."""
    out = {}
    # utf-8-sig: o CSV pode vir com BOM (Excel/Windows gravam assim). Com
    # `utf-8` puro a 1a coluna vira "﻿id", `row.get("id")` devolve None e a
    # regua reporta 0/0 EM SILENCIO — aconteceu com 3 de 5 cursos em 2026-08-19c.
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            eid = str(row.get("id", "")).strip()
            pk = str(row.get("pair_key", "")).strip()
            if eid and pk:
                out[eid] = pk
    return out


def load_predictions_from_gold(csv_path) -> dict:
    """Predicoes auto-contidas do CSV rotulado (snapshot), sem repo live."""
    preds = {}
    with Path(csv_path).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            eid = str(row.get("id", "")).strip()
            if eid:
                preds[eid] = {"block_id": str(row.get("predicted_block_id", "")),
                              "band": str(row.get("predicted_band", "")),
                              "title": str(row.get("title", ""))}
    return preds


def check_baseline(report: dict, baseline: dict) -> int:
    """0 = ok, 1 = regressao. Baseline vazio nunca regride."""
    if not baseline:
        return 0
    acc_min = float(baseline.get("block_accuracy_min", 0.0))
    cw_max = baseline.get("confident_wrong_max")
    if report.get("block_accuracy", 0.0) + 1e-9 < acc_min:
        return 1
    if cw_max is not None and report.get("confident_wrong", 0) > int(cw_max):
        return 1
    return 0


def _scoring_units(predictions: dict, labels: dict, pair_keys: dict) -> list:
    """Unidades de pontuação: avulsos 1:1; version-pairs colapsados em 1 unidade.

    Regra do par (c) — par-certo-só-se-ambos: o par só acerta se TODOS os membros
    rotulados foram preditos no MESMO bloco correto; qualquer divergência (predição OU
    rótulo) = par errado. É a propriedade "mesma aula → mesmo bloco" que o canário vigia.
    `pair_keys` vem do conteúdo (id canônico Moodle), nunca de computed_block_id.
    """
    pair_keys = pair_keys or {}
    groups: dict = {}
    units = []
    for eid, true_block in labels.items():
        pred = predictions.get(eid, {})
        rec = {"id": eid, "true": true_block, "predicted": str(pred.get("block_id", "")),
               "band": str(pred.get("band", "")), "title": str(pred.get("title", ""))}
        pk = pair_keys.get(eid, "")
        if pk:
            groups.setdefault(pk, []).append(rec)
        else:
            units.append({**rec, "is_correct": rec["predicted"] == rec["true"], "pair": False})
    for pk, members in groups.items():
        trues = {m["true"] for m in members}
        all_pred_ok = all(m["predicted"] == m["true"] for m in members)
        is_correct = len(trues) == 1 and all_pred_ok  # regra (c)
        canon = next((m for m in members if m["id"] == pk), members[0])
        if is_correct:
            predicted = canon["true"]
        else:
            # mostra a falha real: 1ª predição != seu rótulo; senão é divergência de rótulo
            predicted = next((m["predicted"] for m in members if m["predicted"] != m["true"]),
                             "(divergente)")
        band = "alta" if any(m["band"] == "alta" for m in members) else canon["band"]
        units.append({"id": pk, "true": canon["true"], "predicted": predicted,
                      "band": band, "title": canon["title"], "is_correct": is_correct,
                      "pair": True})
    return units


def evaluate_ground_truth(predictions: dict, labels: dict, block_map: dict,
                          pair_keys: dict = None) -> dict:
    bands = {"alta": {"correct": 0, "wrong": 0}, "media": {"correct": 0, "wrong": 0},
             "baixa": {"correct": 0, "wrong": 0}, "": {"correct": 0, "wrong": 0}}
    confusion: dict = {}
    rows = []
    correct = orphans = missed = confident_wrong = off_by_one = 0

    units = _scoring_units(predictions, labels, pair_keys)
    for u in units:
        true_block = u["true"]
        predicted = u["predicted"]
        band = u["band"]
        is_correct = u["is_correct"]
        if is_correct:
            correct += 1
        if predicted == "":
            orphans += 1
            if true_block:
                missed += 1
        if band == "alta" and not is_correct:
            confident_wrong += 1
        # off-by-one: erro entre blocos posicionalmente adjacentes (erro de fronteira,
        # não de tópico). Ambos os lados já estão canonicalizados em bloco-NN.
        ov, op = _ordinal(true_block), _ordinal(predicted)
        adjacente = (not is_correct) and ov is not None and op is not None and abs(ov - op) == 1
        if adjacente:
            off_by_one += 1
        bands.setdefault(band, {"correct": 0, "wrong": 0})
        bands[band]["correct" if is_correct else "wrong"] += 1
        key = f"{true_block}->{predicted or '(orfao)'}"
        confusion[key] = confusion.get(key, 0) + 1
        rows.append({"id": u["id"], "true": true_block, "predicted": predicted,
                     "band": band, "correct": is_correct, "adjacente": adjacente,
                     "title": u["title"], "pair": u.get("pair", False)})

    total = len(units)
    return {
        "total": total, "correct": correct, "wrong": total - correct,
        "block_accuracy": (correct / total) if total else 0.0,
        "orphans": orphans, "missed": missed, "confident_wrong": confident_wrong,
        "off_by_one": off_by_one,
        "bands": bands, "confusion": confusion, "cases": rows,
    }


def format_report(report: dict, block_map: dict) -> str:
    lines = ["=== Eval ground-truth: atribuicao file -> bloco ==="]
    acc = report["block_accuracy"]
    lines.append(f"Acuracia: {report['correct']}/{report['total']} ({acc * 100:.1f}%)")
    lines.append(f"Orfaos (previu vazio): {report['orphans']}   Missed (verdade tinha bloco): {report['missed']}")
    wrong_n = report["wrong"]
    obo = report.get("off_by_one", 0)
    lines.append(f"Dos {wrong_n} erros: off-by-one (fronteira adjacente): {obo}   miss de topico: {wrong_n - obo}")
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
            tags = ([t for t in ("par",) if c.get("pair")]
                    + [t for t in ("adjacente",) if c.get("adjacente")])
            tag = (" [" + ", ".join(tags) + "]") if tags else ""
            lines.append(f"  - {c['id']:<24} verdade={c['true'] or '-'} ({tp}) "
                         f"previu={c['predicted'] or '(orfao)'} ({pp}) band={c['band'] or '-'}{tag}")
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
    # Canonicaliza o lado `true` para display bloco-NN (mesmo map do predicted):
    # rótulo humano em bloco-NN bate contra computed/temporal migrado pra uuid.
    _u2d = _uuid_to_display(_load_blocks(repo_root))
    labels = {eid: _canon(tb, _u2d) for eid, tb in load_labels_csv(labels_path).items()}
    # version-pairs (mesma aula, 2 arquivos) colapsam em 1 unidade: regra (c)
    # par-certo-só-se-ambos. Gancho = coluna `pair_key` da folha (conteúdo, não computado).
    pair_keys = load_pair_keys(labels_path)
    report = evaluate_ground_truth(preds, labels, block_map, pair_keys)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report, block_map))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
