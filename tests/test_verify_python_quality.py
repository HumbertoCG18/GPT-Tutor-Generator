from collections import Counter
import json

from scripts.verify_python_quality import (
    compare_counts,
    coverage_minimum,
    find_architecture_violations,
    read_coverage_percent,
)


def test_compare_counts_reports_only_fingerprint_increases():
    allowed = Counter({"src/a.py|F401": 2})
    current = Counter(
        {
            "src/a.py|F401": 3,
            "src/b.py|F821": 1,
        }
    )

    assert compare_counts(current, allowed) == {
        "src/a.py|F401": 1,
        "src/b.py|F821": 1,
    }


def test_find_architecture_violations_ignores_ui_adapter(tmp_path):
    src = tmp_path / "src"
    (src / "ui").mkdir(parents=True)
    (src / "builder").mkdir()
    (src / "ui" / "screen.py").write_text(
        "from src.ui.theme import Theme\n", encoding="utf-8"
    )
    (src / "builder" / "core.py").write_text(
        "from src.ui.theme import AppConfig\n", encoding="utf-8"
    )
    (src / "builder" / "relative.py").write_text(
        "from ..ui import theme\n", encoding="utf-8"
    )

    assert find_architecture_violations(tmp_path) == Counter(
        {
            "src/builder/core.py|src.ui.theme": 1,
            "src/builder/relative.py|src.ui": 1,
        }
    )


def test_read_coverage_percent_uses_report_total(tmp_path):
    report = tmp_path / "coverage.json"
    report.write_text(
        json.dumps({"totals": {"percent_covered": 79.68726607335939}}),
        encoding="utf-8",
    )

    assert read_coverage_percent(report) == 79.68726607335939


def test_coverage_minimum_selects_current_platform():
    assert coverage_minimum({"Windows": 79.68, "Linux": 79.62}, "Linux") == 79.62
