import json
from pathlib import Path

from src.builder.artifacts.build_metrics import collect_scan_stats, ScanStats
from src.builder.artifacts.build_metrics import collect_datalab_metrics, DatalabMetrics
from src.builder.artifacts.build_metrics import (
    collect_build_metrics, render_build_metrics_md, BuildMetrics,
)


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


def test_collect_build_metrics_orchestrates(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"selected_pages_count": 4, "parse_quality_score": 0.9})
    manifest = {"entries": [
        {"file_type": "pdf", "document_report": {"page_count": 4, "suspected_scan": True},
         "advanced_backend": "datalab",
         "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"},
        {"file_type": "pdf", "document_report": {"page_count": 6, "suspected_scan": False}},
    ]}
    m = collect_build_metrics(manifest, tmp_path)
    assert m.scan.pdf_total == 2
    assert m.scan.scanned_count == 1
    assert m.datalab.entry_count == 1
    assert m.datalab.processed_pages == 4


def test_collect_build_metrics_missing_entries_key(tmp_path):
    m = collect_build_metrics({}, tmp_path)
    assert m.scan.pdf_total == 0
    assert m.datalab.entry_count == 0


def test_render_build_metrics_md_with_data():
    metrics = BuildMetrics(
        scan=ScanStats(pdf_total=7, scanned_count=2, total_pages=350, scanned_pages=80),
        datalab=DatalabMetrics(entry_count=3, processed_pages=42, avg_parse_quality=0.91),
    )
    lines = render_build_metrics_md(metrics)
    text = "\n".join(lines)
    assert "## Custos e qualidade do build" in text
    assert "páginas processadas via Datalab: 42 (em 3 arquivo(s))" in text
    assert "parse_quality médio (Datalab): 0.91" in text
    assert "PDFs escaneados: 2 de 7 (29%) · 80 de 350 páginas" in text


def test_collect_datalab_metrics_handles_nonnumeric_pages(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"selected_pages_count": "abc", "parse_quality_score": 0.7})
    entries = [{"advanced_backend": "datalab",
                "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"}]
    m = collect_datalab_metrics(entries, tmp_path)
    assert m.entry_count == 1
    assert m.processed_pages == 0  # non-numeric coerced to 0, no crash
    assert m.avg_parse_quality == 0.7


def test_collect_scan_stats_handles_nonnumeric_page_count():
    entries = [{"file_type": "pdf", "document_report": {"page_count": "xx", "suspected_scan": True}}]
    stats = collect_scan_stats(entries)
    assert stats == ScanStats(pdf_total=1, scanned_count=1, total_pages=0, scanned_pages=0)


def test_render_build_metrics_md_empty():
    metrics = BuildMetrics(
        scan=ScanStats(pdf_total=0, scanned_count=0, total_pages=0, scanned_pages=0),
        datalab=DatalabMetrics(entry_count=0, processed_pages=0, avg_parse_quality=None),
    )
    text = "\n".join(render_build_metrics_md(metrics))
    assert "## Custos e qualidade do build" in text
    assert "nenhum arquivo via Datalab" in text
    assert "parse_quality médio (Datalab): —" in text
    assert "PDFs escaneados: 0 de 0" in text


from src.builder.artifacts.repo import write_build_report


def test_write_build_report_includes_metrics_section(tmp_path):
    _write_sidecar(tmp_path, "staging/markdown-auto/datalab/a/datalab-run.json",
                   {"selected_pages_count": 5, "parse_quality_score": 0.88})
    manifest = {
        "generated_at": "2026-06-11T00:00:00",
        "entries": [
            {"file_type": "pdf", "document_report": {"page_count": 5, "suspected_scan": False},
             "advanced_backend": "datalab",
             "advanced_metadata_path": "staging/markdown-auto/datalab/a/datalab-run.json"},
        ],
    }
    captured = {}

    def fake_write_text(path, text):
        captured["path"] = path
        captured["text"] = text

    write_build_report(
        tmp_path,
        manifest,
        preferred_platform="claude",
        has_pymupdf=True,
        has_pymupdf4llm=True,
        has_pdfplumber=True,
        has_datalab_api_key_fn=lambda: True,
        docling_cli=None,
        has_docling_python_api_fn=lambda: False,
        marker_cli=None,
        write_text_fn=fake_write_text,
    )

    assert "## Custos e qualidade do build" in captured["text"]
    assert "páginas processadas via Datalab: 5 (em 1 arquivo(s))" in captured["text"]
    assert "parse_quality médio (Datalab): 0.88" in captured["text"]
