"""Planilha de rotulagem do gold AGRUPADA POR CARD (= source_section).

Uma linha por card distinto: arquivos nele + bloco candidato (com # de aula do
cronograma e datas) + `true_block_id` pre-preenchido p/ voce CONFIRMAR/corrigir
uma vez por card. Arquivos sem card viram 1 linha cada (n_files=1).

Depois de confirmar, use scripts/expand_card_gold.py p/ virar file->bloco gold.

Confianca:
- alta : card_block_map source=manual (1 bloco) — voce ja curou.
- media: card_block_map source=labels (1 bloco), OU todos os arquivos do card
         preveem o MESMO bloco (unanime).
- baixa: predicoes divergentes no card (veja 'evidence'), ou arquivo sem card.

Uso:
    python -m scripts.gold_by_card <repo_root> <out.csv>
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_NO_TIMELINE = {"referencias", "bibliografia"}

COLUMNS = [
    "card", "n_files", "candidate_block", "block_aulas", "block_dates",
    "block_topic", "confidence", "true_block_id", "evidence", "file_ids",
]


def _load(path):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def build_card_rows(repo_root: Path) -> list[dict]:
    manifest = _load(repo_root / "manifest.json")
    entries = manifest.get("entries") or []
    blocks = (_load(repo_root / "course" / ".timeline_index.json").get("blocks")) or []
    card_map = _load(repo_root / "course" / ".card_block_map.json")
    by_id = {str(b.get("id")): b for b in blocks}

    groups: dict = defaultdict(list)
    for e in entries:
        if str(e.get("category") or "").strip().lower() in _NO_TIMELINE:
            continue
        groups[str(e.get("source_section") or "").strip()].append(e)

    def _blk_cols(bid):
        b = by_id.get(bid, {})
        return (",".join(str(r) for r in (b.get("source_rows") or [])),
                str(b.get("period_label") or ""),
                str(b.get("topic_text") or b.get("primary_topic_label") or ""))

    rows = []
    for card in sorted(groups):
        group = groups[card]
        fids = [str(e.get("id") or "") for e in group]
        if not card:
            # arquivos sem card: 1 linha cada (precisam de rotulo individual)
            for e in group:
                bid = str(e.get("computed_block_id") or "")
                aulas, dates, topic = _blk_cols(bid)
                rows.append({"card": "(sem card)", "n_files": 1,
                             "candidate_block": bid, "block_aulas": aulas,
                             "block_dates": dates, "block_topic": topic,
                             "confidence": "baixa", "true_block_id": bid,
                             "evidence": "sem source_section -> predicao do funil",
                             "file_ids": str(e.get("id") or "")})
            continue
        card_entry = card_map.get(card) or {}
        bids = [str(b) for b in (card_entry.get("block_ids") or [])]
        src = str(card_entry.get("source") or "")
        if len(bids) == 1:
            cand, conf = bids[0], ("alta" if src == "manual" else "media")
            evidence = f"card_block_map (source={src})"
        else:
            preds = Counter(str(e.get("computed_block_id") or "") for e in group)
            cand, _ = preds.most_common(1)[0]
            conf = "media" if len(preds) == 1 else "baixa"
            evidence = (f"sem card-map; predicoes={dict(preds)}"
                        if len(preds) > 1 else "sem card-map; predicao unanime")
        aulas, dates, topic = _blk_cols(cand)
        rows.append({"card": card, "n_files": len(group),
                     "candidate_block": cand, "block_aulas": aulas,
                     "block_dates": dates, "block_topic": topic,
                     "confidence": conf, "true_block_id": cand,
                     "evidence": evidence, "file_ids": ";".join(fids)})
    return rows


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python -m scripts.gold_by_card <repo_root> <out.csv>")
        return 2
    repo_root, out = Path(pos[0]), Path(pos[1])
    rows = build_card_rows(repo_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    cards = [r for r in rows if r["card"] != "(sem card)"]
    nocard = [r for r in rows if r["card"] == "(sem card)"]
    by_conf = Counter(r["confidence"] for r in cards)
    print(f"{out}  cards={len(cards)} (alta={by_conf['alta']} media={by_conf['media']} "
          f"baixa={by_conf['baixa']})  arquivos_sem_card={len(nocard)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
