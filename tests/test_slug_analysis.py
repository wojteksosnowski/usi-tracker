import os
from pathlib import Path

def test_slug_analysis_appended():
    report_path = Path("slug_usage_report.md")
    assert report_path.exists(), "Raport powinien istnieć."
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Analiza użycia i nieuprawnione wystąpienia" in content
        assert "investment_sync.py" in content
