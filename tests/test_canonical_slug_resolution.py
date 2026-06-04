import pytest
from unittest.mock import MagicMock, patch
from python_worker.services.investment_sync import InvestmentSyncService
from pathlib import Path

@pytest.fixture
def sync_service():
    mock_resolver = MagicMock()
    data_dir = Path("/tmp/USIdata")
    public_usi_dir = Path("/tmp/USI")
    mock_dm = MagicMock()
    return InvestmentSyncService(mock_resolver, data_dir, public_usi_dir, developer_manager=mock_dm)

def test_canonical_slug_rp_with_id_match(sync_service):
    """Test RP resolution when developer is known by ID."""
    raw_details = {
        "vendor": {"id": 1234, "slug": "rp-slug"}
    }
    sync_service.dm.find_developer_by_id.return_value = {"developer_slug": "usi-canonical-slug"}
    
    with patch("usi_scrapers.resolve_path", side_effect=lambda data, portal, path: "1234" if "id" in path else "rp-slug"):
        result = sync_service._canonical_slug_from_raw("rp", raw_details, "fallback")
        
        assert result == "usi-canonical-slug"
        sync_service.dm.find_developer_by_id.assert_called_once_with("rp", "1234")

def test_canonical_slug_oto_no_id_match(sync_service):
    """Test Otodom resolution when developer is NOT known by ID, falls back to portal slug."""
    raw_details = {
        "ad": {"agency": {"id": 555, "slug": "oto-slug"}}
    }
    sync_service.dm.find_developer_by_id.return_value = None
    
    with patch("usi_scrapers.resolve_path", side_effect=lambda data, portal, path: "555" if "id" in path else "oto-slug"):
        result = sync_service._canonical_slug_from_raw("oto", raw_details, "fallback")
        
        assert result == "oto-slug"

def test_canonical_slug_fallback(sync_service):
    """Test resolution when no data is found, should use provided fallback."""
    raw_details = {}
    sync_service.dm.find_developer_by_id.return_value = None
    
    with patch("usi_scrapers.resolve_path", return_value=None):
        result = sync_service._canonical_slug_from_raw("to", raw_details, "ultimate-fallback")
        assert result == "ultimate-fallback"
