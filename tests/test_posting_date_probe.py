import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.posting_date_probe import summarize_posting_dates

def test_summarize_batch_and_offbatch():
    # 3 em 2026-02 (batch), 1 em 2026-05 (off-batch), 0 stale
    def f(ts): return {"type": "file", "filename": f"{ts}.pdf", "fileurl": "u",
                       "timemodified": ts, "timecreated": ts}
    contents = [{"name": "S", "modules": [{"name": "m", "contents": [
        f(1770336000), f(1770436000), f(1770536000),  # fev/2026
        f(1777536000),                                  # mai/2026
    ]}]}]
    r = summarize_posting_dates(contents, 2026)
    assert r["total"] == 4
    assert r["stale"] == 0
    assert r["batch_month"] == "2026-02"
    assert r["off_batch"] == 1
