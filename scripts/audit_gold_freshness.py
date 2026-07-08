#!/usr/bin/env python3
"""PRÉ-FLIGHT FASE 2 — auditoria de frescor dos ground_truth_*.csv (READ-ONLY).

Detecta drift posicional de `bloco-NN` pós-reprocess (a classe de defeito que
escondeu 12pp no MF): para cada row do gold, checa contra a timeline ATUAL do
repo-tutor:
  MISSING_BLOCK  true_block_id não existe na timeline atual
  DATE_MISMATCH  data_real do gold fora do período do bloco true (drift forte)
  ADMIN_TRUE     bloco true é não-instrucional (prova/evento/feriado) mas o
                 material não parece material de prova/revisão
  OUT_OF_WINDOW  true fora da janela do card do material (card_block_map)
  PAIR_MISMATCH  md5-gêmeos (pair_key) com true divergente
  ZERO_OVERLAP   0 tokens compartilhados material×assinatura do bloco (fraco)
  ORPHAN_ENTRY   id do gold não existe mais no manifest (informativo)

Rows scorable != yes são puladas (não-rotuladas por design).

NÃO muta nada. Re-rotulagem = decisão humana (sign-off do user, caso a caso).
Uso:
  python scripts/audit_gold_freshness.py [--course SO TCC IA ES2 MF]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
GH = Path.home() / "Documents" / "GitHub"

COURSES = {
    "SO": GH / "Sistemas-Operacionais-Tutor",
    "TCC": GH / "TCC-Tutor",
    "IA": GH / "Inteligencia-Artifical-Tutor",
    "ES2": GH / "Engenharia-Software-2-Tutor",
    "MF": GH / "Metodos-Formais-Tutor",
}

NON_INSTRUCTIONAL = {"assessment", "review", "event", "holiday", "suspension", "admin"}
# \brevis (não "revis"): "previsão" contém a substring "revis"
ASSESS_TITLE_RE = re.compile(
    r"\bprova\b|\bp[12]\b|\bps\b|\bg2\b|\bpf\b|\brevis|gabarito|simulad|enade|apresenta"
)
STOP = {
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "um", "uma",
    "ao", "aos", "com", "por", "para", "sobre", "que", "the", "and", "pdf",
    "aula", "aulas", "laminas", "lamina", "parte", "material", "alternativo",
    "livro", "texto", "geral", "gerais",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def tokens(s: str) -> set:
    out = set()
    for t in re.findall(r"[a-z0-9]+", norm(s)):
        if t in STOP or (t.isdigit() and len(t) <= 4):
            continue
        if len(t) < 3 and not any(c.isdigit() for c in t):
            continue
        out.add(t[:-1] if len(t) > 4 and t.endswith("s") else t)  # stem plural leve
    return out


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def block_signature(b: dict) -> str:
    parts = [str(b.get("topic_text") or ""), " ".join(b.get("aliases") or [])]
    parts += [str(s.get("label") or "") for s in b.get("sessions") or []]
    parts += [str(t) for t in b.get("topic_candidates") or []]
    return " ".join(parts)


def audit_course(code: str, repo: Path, gold_csv: Path) -> list[dict]:
    tl = load_json(repo / "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    by_display = {str(b.get("id")): b for b in blocks}
    by_uuid = {str(b.get("block_uuid")): b for b in blocks if b.get("block_uuid")}

    def resolve_ref(ref: str) -> dict | None:
        return by_display.get(ref) or by_uuid.get(ref)

    cbm = load_json(repo / "course/.card_block_map.json")
    card_windows = {}
    for key, val in (cbm or {}).items():
        ids = [str(x) for x in (val.get("block_ids") or [])]
        display = [str((resolve_ref(x) or {}).get("id") or x) for x in ids]
        card_windows[norm(key)] = display

    manifest = load_json(repo / "manifest.json")
    entries = {str(e.get("id")): e for e in manifest.get("entries") or []}

    with gold_csv.open(encoding="utf-8-sig", newline="") as fh:
        all_rows = list(csv.DictReader(fh))
    rows = [r for r in all_rows if (r.get("scorable") or "").strip() == "yes"]

    by_pair = defaultdict(set)
    for r in rows:
        if r.get("pair_key"):
            by_pair[r["pair_key"]].add(r.get("true_block_id") or "")

    findings = []
    for r in rows:
        rid = r.get("id") or ""
        true_ref = r.get("true_block_id") or ""
        material = r.get("material") or ""
        reasons, evidence = [], []

        entry = entries.get(rid)
        if entry is None:
            reasons.append("ORPHAN_ENTRY")

        tb = resolve_ref(true_ref)
        if tb is None:
            reasons.append("MISSING_BLOCK")
        else:
            dm = re.fullmatch(r"(\d{1,2})/(\d{1,2})", (r.get("data_real") or "").strip())
            if dm:
                dd, mm = int(dm.group(1)), int(dm.group(2))
                sess_dates = [str(s.get("date") or "") for s in tb.get("sessions") or []]
                start, end = str(tb.get("period_start") or ""), str(tb.get("period_end") or "")
                year = (sess_dates[0] or start)[:4]
                iso = f"{year}-{mm:02d}-{dd:02d}" if year.isdigit() else ""
                in_sessions = iso in sess_dates
                in_period = bool(start and end and start <= iso <= end)
                if iso and not (in_sessions or in_period):
                    reasons.append("DATE_MISMATCH")
                    evidence.append(f"data_real={iso} periodo={start}..{end} sessoes={sess_dates}")
            kind = str(tb.get("kind") or "")
            if kind in NON_INSTRUCTIONAL and not ASSESS_TITLE_RE.search(norm(material)):
                reasons.append("ADMIN_TRUE")
                evidence.append(f"kind={kind} label={tb.get('period_label') or tb.get('topic_text','')[:40]}")

            sig = tokens(block_signature(tb))
            mat = tokens(material) | tokens(rid.replace("-", " "))
            inter = mat & sig
            if not inter:
                reasons.append("ZERO_OVERLAP")

        card_key = ""
        if entry is not None:
            card_key = norm(str(entry.get("moodle_label") or entry.get("source_section") or ""))
        window = card_windows.get(card_key) or []
        if window and true_ref not in window:
            reasons.append("OUT_OF_WINDOW")
            evidence.append(f"card='{card_key}' janela={window}")

        pk = r.get("pair_key") or ""
        if pk and len(by_pair[pk]) > 1:
            reasons.append("PAIR_MISMATCH")
            evidence.append(f"pair_key={pk} trues={sorted(by_pair[pk])}")

        if reasons:
            findings.append({
                "id": rid, "material": material, "true": true_ref,
                "reasons": reasons, "evidence": "; ".join(evidence),
                "kind": str((tb or {}).get("kind") or "?"),
            })
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--course", nargs="*", default=["SO", "TCC", "IA", "ES2"],
                    choices=sorted(COURSES), metavar="CURSO")
    args = ap.parse_args()

    for code in args.course:
        repo = COURSES[code]
        gold = ROOT / "docs" / "reports" / f"ground_truth_{code}.csv"
        print(f"\n{'=' * 70}\n{code}  repo={repo.name}  gold={gold.name}")
        if not gold.is_file():
            print("  GOLD AUSENTE")
            continue
        if not repo.is_dir():
            print("  REPO AUSENTE")
            continue
        findings = audit_course(code, repo, gold)
        n_rows = sum(1 for _ in gold.open(encoding="utf-8-sig")) - 1
        hard = [f for f in findings if set(f["reasons"]) - {"ZERO_OVERLAP"}]
        print(f"  rows={n_rows}  suspeitas={len(findings)} (hard={len(hard)})")
        for f in findings:
            tag = ",".join(f["reasons"])
            print(f"  [{tag}] {f['id']}  true={f['true']} (kind={f['kind']})")
            print(f"      material: {f['material']}")
            if f["evidence"]:
                print(f"      {f['evidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
