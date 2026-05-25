import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from python_worker.services.discovery_service import DiscoveryService
from python_worker.services.investment_service import InvestmentService

@pytest.fixture
def svc_context(tmp_path):
    data_dir = tmp_path / "USIdata"
    data_dir.mkdir()
    
    mock_config = MagicMock()
    mock_config.public_dir = tmp_path
    
    with patch("python_worker.config.get_scraper_config", return_value=mock_config), \
         patch("usi_scrapers.fetcher.Fetcher", return_value=MagicMock()):
        svc = DiscoveryService(data_dir=data_dir)
        isvc = InvestmentService(data_dir=data_dir)
        return svc, isvc, data_dir

def test_otodom_registration_uses_alphanumeric_hash(svc_context):
    """Verifies that Otodom registration now uses the alphanumeric hash as primary ID."""
    svc, isvc, data_dir = svc_context
    
    # Mock item with BOTH numeric ID and alphanumeric hash (standardized in v0.8.2)
    # Note: In real discovery, 'id' is now the hash
    item = {
        "slug": "aura-mokotow-ii-ID4ug2k", 
        "name": "Aura Mokotów II", 
        "id": "4ug2k",  # The hash
        "numeric_id": "64437670", 
        "url": "https://www.otodom.pl/pl/inwestycja/aura-mokotow-ii-ID4ug2k"
    }
    
    # Trigger registration
    svc._register_new_investment("bouygues-immobilier-polska", item, "otodom")
    
    # Verify file name uses HASH
    usi_file = data_dir / "bouygues-immobilier-polska" / "aura-mokotow-ii-ID4ug2k" / "usi_oto_4ug2k.json"
    assert usi_file.exists(), "File should be named usi_oto_4ug2k.json"
    
    # Verify internal sources use HASH
    data = json.loads(usi_file.read_text())
    assert data["sources"]["oto"]["id"] == "4ug2k"
    assert data["sources"]["oto"]["url"] == item["url"]

def test_deduplication_recognizes_hash_and_numeric(svc_context):
    """Verifies that deduplication logic handles both formats correctly."""
    svc, isvc, data_dir = svc_context
    
    # 1. Manually create an OLD numeric record
    inv_dir = data_dir / "dev" / "inv"
    inv_dir.mkdir(parents=True)
    old_data = {
        "investment_slug": "inv",
        "sources": {"oto": {"id": "12345", "url": "https://otodom.pl/inv-IDabcd"}}
    }
    (inv_dir / "usi_oto_12345.json").write_text(json.dumps(old_data))
    
    # 2. Try to register same investment using the NEW hash format
    new_item = {
        "slug": "inv-IDabcd",
        "name": "Inv",
        "id": "abcd", # The hash
        "url": "https://otodom.pl/inv-IDabcd"
    }
    
    # We need to mock DeveloperManager.get_existing_identifiers to return our manual ID
    with patch("python_worker.developer_manager.DeveloperManager.get_existing_identifiers") as mock_ids:
        mock_ids.return_value = {
            "rp_ids": set(),
            "oto_ids": {"12345", "abcd"}, # Standard system logic would find both
            "oto_slugs": {"inv-IDabcd"},
            "to_ids": set()
        }
        
        result_dev, result_inv = svc._register_new_investment("dev", new_item, "otodom")
        
        # Result should be None, None because it's a duplicate
        assert result_dev is None
        assert result_inv is None
