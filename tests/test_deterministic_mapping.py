import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_worker.services.investment_identity import InvestmentIdentityResolver

@pytest.fixture
def resolver():
    return InvestmentIdentityResolver("/tmp/USIdata", "/tmp/USI")

def test_map_resources_deterministic_success(resolver):
    """Verify that mapping succeeds when portal_id and config are present."""
    entry = {
        "usi_inv_id": "usi-123",
        "portal": "rp",
        "portal_id": "999",
        "developer_slug": "dev",
        "investment_slug": "inv"
    }
    
    mock_config = MagicMock()
    mock_config.public_dir = Path("/tmp")
    
    with patch("python_worker.config.get_scraper_config", return_value=mock_config), \
         patch("usi_scrapers.manager.TechnicalDataManager.get_investment_path") as mock_get_path, \
         patch("usi_scrapers.manager.TechnicalDataManager.get_image_path") as mock_get_img_path:
        
        expected_dir = Path("/tmp/USIdata/resolved")
        mock_get_path.return_value = expected_dir
        mock_get_img_path.return_value = Path("/tmp/USI/resolved")
        
        result = resolver._map_resources_from_entry(entry)
        
        assert result is not None
        assert result["base_dir"] == expected_dir
        assert result["metadata"]["portal"] == "rp"
        assert result["metadata"]["portal_id"] == "999"

def test_map_resources_fails_without_portal_id(resolver):
    """Verify that mapping returns None when portal_id is missing and cannot be inferred."""
    entry = {
        "usi_inv_id": "usi-456",
        "developer_slug": "dev",
        "investment_slug": "inv",
        "sources": {} # No IDs here
    }
    
    result = resolver._map_resources_from_entry(entry)
    assert result is None

def test_map_resources_fails_when_library_cannot_resolve(resolver):
    """Verify that mapping returns None when TechnicalDataManager returns None."""
    entry = {
        "usi_inv_id": "usi-789",
        "portal": "oto",
        "portal_id": "non-existent"
    }
    
    mock_config = MagicMock()
    with patch("python_worker.config.get_scraper_config", return_value=mock_config), \
         patch("usi_scrapers.manager.TechnicalDataManager.get_investment_path", return_value=None):
        
        result = resolver._map_resources_from_entry(entry)
        assert result is None
