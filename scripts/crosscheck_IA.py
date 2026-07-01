"""Cross-check de atribuicao: 3 sinais independentes (card / roteiro / funil)
comparados 2-a-2. Bandeira read-only para revisao humana — NAO muta manifest.

Detecta anomalias de dado (ex.: duplicata de nome corrompido sem card cujo
funil chuta bloco errado, enquanto o roteiro aponta o certo).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.builder.routing.concept_resolver import score_lesson_match
from src.builder.text.normalize import normalize_match_text

# Abaixo disto, o funil esta "chutando" (scorer_only tipicamente <0.5).
LOW_CONF: float = 0.5


@dataclass
class CrossCheck:
    flagged: bool = False
    severity: str = ""  # "grave" | "aviso" | ""
    reasons: List[str] = field(default_factory=list)


def classify_crosscheck(card_blocks, roteiro_block, placement_block, anchored: bool,
                        computed_conf, low_conf: float = LOW_CONF) -> CrossCheck:
    """Compara roteiro/card contra o PLACEMENT EFETIVO (temporal>manual>computed).
    GRAVE so quando o placement NAO esta ancorado (veio do computed cru) E tem
    conf baixa E o roteiro o contradiz = assinatura aula-29. Ancora (temporal/
    manual) -> confiavel -> no maximo AVISO."""
    reasons: List[str] = []
    card_set = {b for b in (card_blocks or []) if b}
    if roteiro_block and placement_block and roteiro_block != placement_block:
        if (not anchored) and computed_conf < low_conf:
            reasons.append("roteiro!=placement:lowconf")
        else:
            reasons.append("roteiro!=placement")
    if card_set and roteiro_block and roteiro_block not in card_set:
        reasons.append("card!=roteiro")
    severity = "grave" if any(r.endswith(":lowconf") for r in reasons) else (
        "aviso" if reasons else "")
    return CrossCheck(flagged=bool(reasons), severity=severity, reasons=reasons)


def roteiro_block_for(signals: dict, blocks, lessons_index,
                      normalize: Optional[Callable[[str], str]] = None) -> str:
    """Bloco que o ROTEIRO sugere: argmax de score_lesson_match sobre os blocos.
    '' quando nenhum bloco casa o topico das suas sessoes (sem sinal)."""
    norm = normalize or normalize_match_text
    best_id, best = "", 0.0
    for b in blocks or []:
        s = score_lesson_match(signals, b, lessons_index, norm)
        if s > best:
            best = s
            best_id = str(b.get("id") or b.get("block_uuid") or "")
    return best_id


def _resolve_display(bid, u2d: dict) -> str:
    s = str(bid or "").strip()
    return u2d.get(s, s)


def _moodle_label_text(entry: dict) -> str:
    ml = entry.get("moodle_label")
    if isinstance(ml, dict):
        return " ".join(str(ml.get(k) or "")
                        for k in ("text", "label", "name", "instancename"))
    return str(ml or "")


def _build_signals(entry: dict) -> dict:
    return {"title_text": str(entry.get("title") or ""),
            "moodle_label_text": _moodle_label_text(entry)}


def _card_blocks_for(entry: dict, card_map: dict, u2d: dict) -> List[str]:
    card = str(entry.get("source_section") or "").strip()
    if not card:
        return []
    ce = card_map.get(card) or {}
    return [_resolve_display(b, u2d) for b in (ce.get("block_ids") or [])]


_SEV_ORDER = {"grave": 0, "aviso": 1, "": 2}


def crosscheck_rows(entries, blocks, card_map, lessons_index, u2d) -> List[dict]:
    """Compara os 3 sinais por material; devolve so os DISCORDANTES, ordenados
    por severidade (grave primeiro). Pura — recebe dados ja carregados."""
    rows: List[dict] = []
    for e in entries or []:
        signals = _build_signals(e)
        roteiro = roteiro_block_for(signals, blocks, lessons_index)
        card_set = _card_blocks_for(e, card_map, u2d)
        computed = _resolve_display(e.get("computed_block_id"), u2d)
        # Placement EFETIVO = temporal > manual > computed (espelha o gold/eval).
        temporal = str(e.get("temporal_block_id") or "").strip()
        manual = str(e.get("manual_timeline_block_id") or "").strip()
        anchored = bool(temporal or manual)
        placement = _resolve_display(temporal or manual or e.get("computed_block_id"), u2d)
        try:
            conf = float(e.get("computed_block_confidence") or 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        v = classify_crosscheck(card_set, roteiro, placement, anchored, conf)
        if not v.flagged:
            continue
        rows.append({
            "id": str(e.get("id") or ""),
            "title": str(e.get("title") or ""),
            "card": ",".join(card_set),
            "roteiro": roteiro,
            "placement": placement,
            "anchored": anchored,
            "computed": computed,
            "conf": round(conf, 3),
            "severity": v.severity,
            "reasons": v.reasons,
        })
    rows.sort(key=lambda r: (_SEV_ORDER.get(r["severity"], 9), r["id"]))
    return rows


# --- I/O wrapper (read-only; nao muta manifest) -------------------------------

DEFAULT_REPO = r"C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor"
DEFAULT_OUT = r"C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/crosscheck_IA.csv"
COLUMNS = ["id", "title", "card", "roteiro", "placement", "anchored", "computed",
           "conf", "severity", "reasons"]


def _load(path) -> dict:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def main(argv: list) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    pos = [a for a in argv if not a.startswith("-")]
    repo = Path(pos[0]) if pos else Path(DEFAULT_REPO)
    out = Path(pos[1]) if len(pos) > 1 else Path(DEFAULT_OUT)

    manifest = _load(repo / "manifest.json")
    entries = manifest.get("entries") or []
    tl = _load(repo / "course" / ".timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    card_map = _load(repo / "course" / ".card_block_map.json")
    lessons_index = _load(repo / "course" / ".lessons_index.json")
    bi = _load(repo / "course" / ".block_identity.json")
    u2d = {str(b.get("uuid")): str(b.get("display_id_last")) for b in (bi or [])}

    if not lessons_index.get("by_date"):
        print(f"AVISO: {repo.name} sem lessons_index (roteiro) — cross-check degrada "
              f"para card-vs-computed apenas.")

    rows = crosscheck_rows(entries, blocks, card_map, lessons_index, u2d)

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "reasons": ";".join(r["reasons"])})

    bar = "=" * 72
    by_sev = Counter(r["severity"] for r in rows)
    print(bar)
    print(f"CROSS-CHECK {repo.name}  ({len(entries)} materiais)")
    print(bar)
    print(f"  bandeiras: {len(rows)}  (grave={by_sev['grave']} aviso={by_sev['aviso']})")
    def _show(r):
        anc = "ancora" if r["anchored"] else "chute"
        print(f"    {r['id'][:42]:42} card={r['card'] or '-':10} "
              f"roteiro={r['roteiro'] or '-':9} placement={r['placement'] or '-':9}"
              f"({anc}) conf={r['conf']} | {';'.join(r['reasons'])}")
    graves = [r for r in rows if r["severity"] == "grave"]
    if graves:
        print("\n  GRAVE (placement sem ancora, conf baixa, roteiro contradiz):")
        for r in graves:
            _show(r)
    avisos = [r for r in rows if r["severity"] == "aviso"]
    if avisos:
        print("\n  AVISO (sinais de base discordam — qual e o certo?):")
        for r in avisos:
            _show(r)
    print("\n" + bar)
    print(f"CSV escrito (NAO commitado): {out}")
    print(bar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
