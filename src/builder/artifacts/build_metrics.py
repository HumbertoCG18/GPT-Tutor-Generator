from __future__ import annotations

from dataclasses import dataclass
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
