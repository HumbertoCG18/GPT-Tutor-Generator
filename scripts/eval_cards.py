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
    from src.builder.engine import _build_file_map_unit_index_from_course
    from src.models.core import SubjectStore

    # Carrega o SubjectProfile cujo repo_root casa com este repo (tem o teaching_plan).
    subject_profile = None
    try:
        store = SubjectStore()
        target = str(repo_root).replace("\\", "/").rstrip("/").casefold()
        for name in store.names():
            sp = store.get(name)
            rr = str(getattr(sp, "repo_root", "") or "").replace("\\", "/").rstrip("/").casefold()
            if rr and rr == target:
                subject_profile = sp
                break
    except Exception:
        subject_profile = None

    card_map = load_card_block_map(repo_root / "course")
    try:
        units = _build_file_map_unit_index_from_course({"_repo_root": str(repo_root)}, subject_profile)
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
            print(f"  - {str(c['id']):<28} card={c['card']:<28} previu={c['block'] or '(orfao)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
