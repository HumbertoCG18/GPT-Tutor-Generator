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
