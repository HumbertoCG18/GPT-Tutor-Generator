"""Harness de avaliacao da atribuicao arquivo->bloco temporal.

Roda cada material rotulado do gold set pelo SCORER REAL (via
content_taxonomy.resolve_unit_block_tags, o mesmo caminho que escreve o
manifest), le computed_block_id/computed_block_band e compara com o bloco
esperado. Reporta acuracia, matriz de confusao e calibracao de band.

Sem disco, sem Datalab, sem Gemini. Deterministico.

Uso:
    python scripts/eval_assignments.py [tests/fixtures/eval/assignments_gold.json]
    python scripts/eval_assignments.py --json   # so o dump de metricas
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.engine import _select_probable_period_for_entry  # noqa: E402
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags  # noqa: E402


def load_gold(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _stub_unit_match(slug: str, confidence: float, ambiguous: bool):
    """Duck-type do UnitMatch real (cf. tests/test_resolve_unit_block_band.py)."""
    class M:
        pass
    m = M()
    m.slug = slug
    m.confidence = float(confidence)
    m.ambiguous = bool(ambiguous)
    m.reasons = []
    return m


def _stub_topic_match():
    """Duck-type do TopicMatch real (cf. tests/test_resolve_unit_block_band.py linhas 49-59)."""
    class M:
        pass
    m = M()
    m.topic_slug = ""
    m.topic_label = ""
    m.unit_slug = ""
    m.confidence = 0.0
    m.ambiguous = True
    m.reasons = []
    return m


def _entry_from_case(case: dict) -> dict:
    return {
        "id": str(case.get("id", "")),
        "title": str(case.get("title", "")),
        "category": str(case.get("category", "material-de-aula")),
        "file_type": "pdf",
        "source_path": str(case.get("raw_target", "")),
        "raw_target": str(case.get("raw_target", "")),
        "tags": str(case.get("tags", "")),
        "manual_tags": [],
        "auto_tags": [],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
        "manual_subunit_slug": "",
    }


def predict_block(case: dict, blocks: list) -> tuple[str, str]:
    """Retorna (computed_block_id, computed_block_band) do scorer real."""
    guess = case.get("unit_guess") or {}
    unit_stub = _stub_unit_match(
        guess.get("slug", ""),
        guess.get("confidence", 0.0),
        guess.get("ambiguous", True),
    )
    markdown = str(case.get("markdown", ""))

    out = resolve_unit_block_tags(
        [_entry_from_case(case)],
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": list(blocks)},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: unit_stub,
        select_probable_period_for_entry_fn=_select_probable_period_for_entry,
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: markdown,
    )[0]
    return str(out.get("computed_block_id", "")), str(out.get("computed_block_band", ""))


def evaluate(gold: dict) -> dict:
    blocks = gold["timeline"]["blocks"]
    cases = gold["cases"]

    case_rows = []
    confusion: dict = {}
    bands = {
        "alta": {"correct": 0, "wrong": 0},
        "media": {"correct": 0, "wrong": 0},
        "baixa": {"correct": 0, "wrong": 0},
        "": {"correct": 0, "wrong": 0},  # orfao (sem band)
    }
    correct = 0
    orphans = 0

    for case in cases:
        expected = str(case.get("expected_block_id", ""))
        predicted, band = predict_block(case, blocks)
        is_correct = predicted == expected
        if is_correct:
            correct += 1
        if predicted == "":
            orphans += 1
        bands.setdefault(band, {"correct": 0, "wrong": 0})
        bands[band]["correct" if is_correct else "wrong"] += 1
        key = f"{expected}->{predicted or '(orfao)'}"
        confusion[key] = confusion.get(key, 0) + 1
        case_rows.append({
            "id": str(case.get("id", "")),
            "expected": expected,
            "predicted": predicted,
            "band": band,
            "correct": is_correct,
            "note": str(case.get("note", "")),
        })

    total = len(cases)
    return {
        "total": total,
        "correct": correct,
        "wrong": total - correct,
        "orphans": orphans,
        "block_accuracy": (correct / total) if total else 0.0,
        # confiante e ERRADO = pior falha (band alta mas bloco errado)
        "confident_wrong": bands["alta"]["wrong"],
        "bands": bands,
        "confusion": confusion,
        "cases": case_rows,
    }


def format_report(report: dict, gold: dict) -> str:
    lines = []
    acc = report["block_accuracy"]
    lines.append("=== Eval: atribuicao arquivo -> bloco ===")
    lines.append(
        f"Acuracia de bloco: {report['correct']}/{report['total']} "
        f"({acc * 100:.1f}%)   orfaos: {report['orphans']}"
    )
    lines.append(f"Confiante e ERRADO (band alta, bloco errado): {report['confident_wrong']}")
    lines.append("")
    lines.append("Calibracao por band (correto / errado):")
    for band in ("alta", "media", "baixa", ""):
        b = report["bands"].get(band, {"correct": 0, "wrong": 0})
        label = band or "(orfao)"
        lines.append(f"  {label:<8} {b['correct']:>3} ok / {b['wrong']:>3} erro")
    lines.append("")
    wrong = [c for c in report["cases"] if not c["correct"]]
    if wrong:
        lines.append("Erros:")
        for c in wrong:
            lines.append(
                f"  - {c['id']:<16} esperado={c['expected'] or '(orfao)'} "
                f"previu={c['predicted'] or '(orfao)'} band={c['band'] or '-'}"
                + (f"  [{c['note']}]" if c["note"] else "")
            )
    else:
        lines.append("Sem erros.")
    baseline = float((gold.get("baseline") or {}).get("block_accuracy", 0.0))
    lines.append("")
    lines.append(f"Baseline registrado: {baseline * 100:.1f}%")
    if acc + 1e-9 < baseline:
        lines.append(f"REGRESSAO: {acc * 100:.1f}% < baseline {baseline * 100:.1f}%")
    return "\n".join(lines)


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    as_json = "--json" in argv
    paths = [a for a in argv if not a.startswith("-")]
    gold_path = Path(paths[0]) if paths else Path(
        "tests/fixtures/eval/assignments_gold.json"
    )
    gold = load_gold(gold_path)
    report = evaluate(gold)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report, gold))
    baseline = float((gold.get("baseline") or {}).get("block_accuracy", 0.0))
    return 1 if report["block_accuracy"] + 1e-9 < baseline else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
