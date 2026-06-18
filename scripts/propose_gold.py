"""Draft de gabarito (true_block_id) para o gold file->bloco, com EVIDENCIA.

NAO e gold final: e um pre-preenchimento por sinais OBJETIVOS/curados, para o
humano VERIFICAR (evita rotular do zero). Confianca por linha:
- alta  : card_block_map source=manual com 1 bloco (voce ja curou) OU data de
          card/sessao caindo 1:1 num bloco.
- media : card_block_map source=labels com 1 bloco; ou predicao == sugestao por data.
- baixa : sem card nem data -> cai na predicao do funil (NEEDS REVIEW).

Usar o draft como gold SEM revisar e circular (maquina avaliando maquina). As
linhas 'alta' (card manual) sao as mais seguras; revise as 'baixa'/'media'.

Uso:
    python -m scripts.propose_gold <repo_root> <out.csv>
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_NO_TIMELINE = {"referencias", "bibliografia"}
_DATE_RE = re.compile(r"\b(\d{1,2})[/.](\d{1,2})\b")

COLUMNS = [
    "id", "title", "category", "source_section", "moodle_label", "posting_date",
    "predicted_block_id", "proposed_true_block_id", "block_aulas", "block_dates",
    "block_topic", "confidence", "method", "needs_review", "evidence",
]


def _load(path):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _block_contains(block, month, day) -> bool:
    """True se a data (mes/dia, ano-agnostico) cai no [period_start, period_end]."""
    ps, pe = str(block.get("period_start") or ""), str(block.get("period_end") or "")
    if not ps:
        return False
    pe = pe or ps
    try:
        sm, sd = int(ps[5:7]), int(ps[8:10])
        em, ed = int(pe[5:7]), int(pe[8:10])
    except (ValueError, IndexError):
        return False
    return (sm, sd) <= (month, day) <= (em, ed)


def propose_rows(repo_root: Path) -> list[dict]:
    manifest = _load(repo_root / "manifest.json")
    entries = manifest.get("entries") or []
    blocks = (_load(repo_root / "course" / ".timeline_index.json").get("blocks")) or []
    card_map = _load(repo_root / "course" / ".card_block_map.json")
    by_id = {str(b.get("id")): b for b in blocks}

    rows = []
    for e in entries:
        category = str(e.get("category") or "").strip().lower()
        if category in _NO_TIMELINE:
            continue
        section = str(e.get("source_section") or "").strip()
        title = str(e.get("title") or "")
        predicted = str(e.get("computed_block_id") or "")

        proposed, conf, method, evidence = predicted, "baixa", "prediction", "sem card/data -> predicao do funil"

        # (1) card_block_map curado pelo usuario (manual) ou derivado (labels)
        card = card_map.get(section) if section else None
        if card and card.get("block_ids"):
            bids = [str(b) for b in card["block_ids"]]
            src = str(card.get("source") or "")
            if len(bids) == 1:
                proposed = bids[0]
                conf = "alta" if src == "manual" else "media"
                method = f"card-{src or 'map'}"
                evidence = f"card_block_map['{section}']={bids} (source={src})"
            else:
                method = "card-multi"
                evidence = f"card_block_map['{section}']={bids} (varios -> revisar)"

        # (2) data explicita no titulo/secao -> bloco por periodo (so se card nao decidiu)
        if conf == "baixa":
            m = _DATE_RE.search(title) or (_DATE_RE.search(section) if section else None)
            if m:
                day, month = int(m.group(1)), int(m.group(2))
                hits = [str(b.get("id")) for b in blocks if _block_contains(b, month, day)]
                if len(hits) == 1:
                    proposed, conf, method = hits[0], "media", "date"
                    evidence = f"data {day:02d}/{month:02d} no nome -> bloco unico {hits[0]}"

        blk = by_id.get(proposed, {})
        _src_rows = blk.get("source_rows") or []
        rows.append({
            "id": str(e.get("id") or ""),
            "title": title,
            "category": category,
            "source_section": section,
            "moodle_label": str(e.get("moodle_label") or ""),
            "posting_date": str(e.get("posting_date") or ""),
            "predicted_block_id": predicted,
            "proposed_true_block_id": proposed,
            "block_aulas": ",".join(str(r) for r in _src_rows),   # # do cronograma cobertas pelo bloco
            "block_dates": str(blk.get("period_label") or ""),
            "block_topic": str(blk.get("topic_text") or blk.get("primary_topic_label") or ""),
            "confidence": conf,
            "method": method,
            "needs_review": "SIM" if conf != "alta" else "",
            "evidence": evidence,
        })
    return rows


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python -m scripts.propose_gold <repo_root> <out.csv>")
        return 2
    repo_root, out = Path(pos[0]), Path(pos[1])
    rows = propose_rows(repo_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    by_conf = {"alta": 0, "media": 0, "baixa": 0}
    for r in rows:
        by_conf[r["confidence"]] = by_conf.get(r["confidence"], 0) + 1
    print(f"{out}  ({len(rows)} materiais)  alta={by_conf['alta']} "
          f"media={by_conf['media']} baixa={by_conf['baixa']} (revisar media+baixa)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
