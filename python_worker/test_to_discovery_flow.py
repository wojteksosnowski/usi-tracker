import pytest
from unittest.mock import patch, MagicMock
from python_worker.portal_matcher import filter_new_investments
from python_worker.scraper_to import discover_to_investments

def test_to_discovery_deduplication():
    # Mock existing identifiers
    mock_identifiers = {
        "rp_ids": set(),
        "oto_ids": set(),
        "oto_slugs": set(),
        "to_ids": {"12345"}
    }
    
    discovered = [
        {"id": "12345", "name": "Existing", "slug": "existing"},
        {"id": "67890", "name": "New", "slug": "new"}
    ]
    
    with patch("python_worker.developer_manager.DeveloperManager.get_existing_identifiers", return_value=mock_identifiers):
        results = filter_new_investments(discovered, "to")
        
    assert results[0]["is_new"] is False
    assert results[1]["is_new"] is True

def test_to_id_extraction_during_discovery():
    mock_html = """
    <html>
        <a href="/inwestycja/test-investment,i99887">Link</a>
        <a href="/inwestycja/other,i11223">Link 2</a>
    </html>
    """
    
    with patch("python_worker.scraper_to.fetch_to_html", return_value=mock_html):
        results = discover_to_investments("test-dev")
        
    assert len(results) == 2
    assert results[0]["id"] == "99887"
    assert results[0]["slug"] == "test-investment"
    assert results[1]["id"] == "11223"
