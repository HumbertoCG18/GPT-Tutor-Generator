from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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
