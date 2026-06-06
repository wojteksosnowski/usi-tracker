import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_worker.services.investment_sync import InvestmentSyncService

@pytest.fixture
def mock_identity():
    identity = MagicMock()
    # Mocking resources for a test investment
    identity.get_investment_resources.return_value = {
        "base_dir": Path("/tmp/usi_test/dev-1/inv-1"),
        "files": {"anchor": Path("/tmp/usi_test/dev-1/inv-1/usi_123.json")},
        "metadata": {"slug": "dev-1/inv-1", "id": "usi_123"}
    }
    return identity

@pytest.fixture
def sync_service(mock_identity, tmp_path):
    data_dir = tmp_path / "USIdata"
    public_usi_dir = tmp_path / "USI"
    data_dir.mkdir()
    public_usi_dir.mkdir()
    
    with patch("python_worker.config.get_scraper_config") as mock_config:
        config_obj = MagicMock()
        config_obj.public_dir = str(tmp_path)
        mock_config.return_value = config_obj
        service = InvestmentSyncService(mock_identity, data_dir, public_usi_dir)
        return service

def test_download_raw_json_uses_scraper_api(sync_service, tmp_path):
    """Verifies that download_raw_json delegates to scraper_api.download_raw."""
    portal = "rp"
    identifier = "12345"
    system_id = "usi_123"
    
    with patch("usi_scrapers.api.download_raw") as mock_download:
        mock_download.return_value = True
        
        result = sync_service.download_raw_json(portal, identifier, system_id)
        
        assert result is True
        mock_download.assert_called_once_with(sync_service.lib_config, sync_service.fetcher, portal, identifier)

def test_fetch_and_transform_portal_data_uses_save_raw(sync_service, mock_identity):
    """Verifies that _fetch_and_transform_portal_data uses the correct API methods."""
    system_id = "usi_123"
    portal = "rp"
    portal_name = "RynekPierwotny"
    raw_prefix = "rp"
    sources = {"rp": {"id": "12345"}}
    
    mock_raw = {"id": 12345, "title": "Test Investment"}
    
    with patch("usi_scrapers.api.refresh_investment_by_id") as mock_refresh, \
         patch("python_worker.adapters.AdapterFactory.get_adapter") as mock_adapter:
        
        mock_refresh.return_value = mock_raw
        mock_adapter.return_value.transform.return_value = {"unified": "data"}
        
        unified, name, error = sync_service._fetch_and_transform_portal_data(
            system_id, portal, portal_name, raw_prefix, sources, use_local_raw=False
        )
        
        assert unified == {"unified": "data"}
        assert name == portal_name
        assert error is None
        
        mock_refresh.assert_called_once_with(
            sync_service.lib_config,
            sync_service.fetcher,
            portal,
            "12345"
        )
