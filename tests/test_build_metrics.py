from src.builder.artifacts.build_metrics import collect_scan_stats, ScanStats


def test_collect_scan_stats_counts_scanned_pdfs_and_pages():
    entries = [
        {"file_type": "pdf", "document_report": {"page_count": 10, "suspected_scan": True}},
        {"file_type": "pdf", "document_report": {"page_count": 20, "suspected_scan": False}},
        {"file_type": "pdf", "document_report": {"page_count": 30, "suspected_scan": True}},
        {"file_type": "image", "document_report": {"page_count": 1, "suspected_scan": True}},  # ignorado (não-PDF)
        {"file_type": "pdf"},  # sem document_report → conta como pdf, 0 páginas, não-escaneado
    ]
    stats = collect_scan_stats(entries)
    assert stats == ScanStats(pdf_total=4, scanned_count=2, total_pages=60, scanned_pages=40)
