import json
from pathlib import Path

from src.builder.artifacts.build_metrics import collect_scan_stats, ScanStats
from src.builder.artifacts.build_metrics import collect_datalab_metrics, DatalabMetrics


def _write_sidecar(root: Path, rel: str, payload: dict) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def test_collect_datalab_metrics_sums_pages_and_averages_quality(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"selected_pages_count": 5, "page_count": 5, "parse_quality_score": 0.8})
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/b/datalab-run.json",
                   {"selected_pages_count": 3, "page_count": 10, "parse_quality_score": 0.9})
    entries = [
        {"advanced_backend": "datalab", "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"},
        {"advanced_backend": "datalab", "advanced_metadata_path": "staging/markdown-auto/datalab/b/datalab-run.json"},
        {"advanced_backend": "marker", "advanced_metadata_path": "x"},
        {"advanced_backend": "datalab"},
    ]
    m = collect_datalab_metrics(entries, tmp_path)
    assert m.entry_count == 2
    assert m.processed_pages == 8
    assert m.avg_parse_quality == 0.85


def test_collect_datalab_metrics_uses_page_count_fallback(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"page_count": 7, "parse_quality_score": None})
    entries = [{"advanced_backend": "datalab",
                "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"}]
    m = collect_datalab_metrics(entries, tmp_path)
    assert m.processed_pages == 7
    assert m.avg_parse_quality is None


def test_collect_datalab_metrics_skips_broken_sidecar(tmp_path):
    (tmp_path / "staging/markdown-auto/datalab/a").mkdir(parents=True)
    (tmp_path / "staging/markdown-auto/datalab/a/datalab-run.json").write_text("{not json", encoding="utf-8")
    entries = [
        {"advanced_backend": "datalab", "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"},
        {"advanced_backend": "datalab", "advanced_metadata_path": "staging/markdown-auto/datalab/missing/datalab-run.json"},
    ]
    m = collect_datalab_metrics(entries, tmp_path)
    assert m == DatalabMetrics(entry_count=0, processed_pages=0, avg_parse_quality=None)


def test_collect_datalab_metrics_empty():
    m = collect_datalab_metrics([], Path("."))
    assert m == DatalabMetrics(entry_count=0, processed_pages=0, avg_parse_quality=None)


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
