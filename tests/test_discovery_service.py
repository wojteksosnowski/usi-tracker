import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from python_worker.services.discovery_service import DiscoveryService

@pytest.fixture
def discovery_service(tmp_path):
    with patch("python_worker.services.discovery_service.get_scraper_config") as mock_config:
        mock_config.return_value = MagicMock()
        service = DiscoveryService(data_dir=tmp_path / "USIdata")
        service.isvc = MagicMock()
        return service

def test_discover_for_developer_uses_system_id(discovery_service, tmp_path):
    system_id = "usi_dev_123"
    
    with patch("python_worker.developer_manager.DeveloperManager") as MockDM, \
         patch.object(discovery_service, "_save_discovery_snapshot") as mock_save:
        
        mock_dm = MagicMock()
        MockDM.return_value = mock_dm
        
        mock_dev = {"developer_slug": "dev-slug", "portal_mapping": {"rp": {"id": "123"}}}
        mock_dm.get_developer_by_id.return_value = mock_dev
        
        with patch("usi_scrapers.api.list_investments") as mock_list, \
             patch("python_worker.services.discovery_service.filter_new_investments") as mock_filter:
            
            mock_list.return_value = [{"id": "inv_123", "name": "New Inv", "is_new": True}]
            mock_filter.return_value = [{"id": "inv_123", "name": "New Inv", "is_new": True}]
            
            result = discovery_service.discover_for_developer(system_id, download=False, auto_register=True)
            
            assert result == 1
            mock_dm.get_developer_by_id.assert_called_once_with(system_id)
            mock_save.assert_called_once_with("dev-slug", [{"id": "inv_123", "name": "New Inv", "is_new": True, "registered": True}])
            
            # Check if it was registered using system_id
            discovery_service.isvc.register_investment.assert_called_once()
