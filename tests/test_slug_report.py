import os
from pathlib import Path

def test_slug_report_generated():
    report_path = Path("slug_usage_report.md")
    assert report_path.exists(), "Raport slug_usage_report.md powinien zostać wygenerowany."
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# Raport z użycia slugów w funkcjach" in content
        assert "slug" in content.lower()
