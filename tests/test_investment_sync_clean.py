import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from python_worker.services.investment_sync import InvestmentSyncService

@pytest.fixture
def mock_identity():
    return MagicMock()

@pytest.fixture
def sync_service(mock_identity, tmp_path):
    mock_config = MagicMock()
    mock_config.public_dir = str(tmp_path / "Public")
    (tmp_path / "USIdata").mkdir(parents=True, exist_ok=True)
    with patch("python_worker.config.get_scraper_config", return_value=mock_config):
        return InvestmentSyncService(
            identity_resolver=mock_identity,
            data_dir=tmp_path / "USIdata",
            public_usi_dir=tmp_path / "Public" / "USI"
        )

def test_register_investment_uses_tech_manager_path(sync_service, mock_identity, tmp_path):
    portal = "rp"
    item_id = "123"
    dev_slug = "dev"
    inv_slug = "inv"
    
    # Mock tech_manager
    target_dir = tmp_path / "TechResolved"
    sync_service.tech_manager = MagicMock()
    sync_service.tech_manager.get_investment_path.return_value = target_dir
    
    # Mock other deps
    sync_service._resolve_developer_for_registration = MagicMock(return_value=(dev_slug, "Dev Name", None))
    sync_service._check_investment_exists = MagicMock(return_value=False)
    
    # Mock repo and identity to avoid complex internal calls
    sync_service.repo = MagicMock()
    sync_service.resolver = MagicMock()
    
    # We no longer need to mock _find_inv_file as it is removed.
    # The register_investment method will use tech_manager to resolve paths.
    sync_service.register_investment(portal, "Dev Name", inv_slug, "Inv Name", item_id=item_id)
        
    # Verify tech_manager was used in SyncService

    sync_service.tech_manager.get_investment_path.assert_called_with(portal, str(item_id))
    assert target_dir.exists()

def test_update_investment_uses_id_based_upsert(sync_service, mock_identity, tmp_path):
    system_id = "rp_123"
    
    # Mock resources
    anchor_file = tmp_path / "usi_rp_123.json"
    anchor_file.write_text(json.dumps({"usi_inv_id": system_id, "sources": {"rp": {"id": "123"}}}))
    
    mock_identity.get_investment_resources.return_value = {
        "base_dir": tmp_path / "base",
        "files": {"anchor": anchor_file},
        "metadata": {"slug": "dev/inv"}
    }
    
    # Mock internal methods to skip actual work
    sync_service._fetch_and_transform_portal_data = MagicMock(return_value=({"sources": {"rp": {"id": "123"}}}, "rp", None))
    sync_service._sync_investment_images = MagicMock()
    sync_service.repo = MagicMock()
    sync_service.repo.get_investment_json.return_value = {"usi_inv_id": system_id}
    
    # Pre-create index file to avoid FileNotFoundError in upsert
    index_file = tmp_path / "USIdata" / "_index.json"
    index_file.write_text(json.dumps({"entries": [], "count": 0}))
    
    with patch("python_worker.investment_index.upsert") as mock_upsert, \
         patch("python_worker.adapters.merger.Merger.merge", return_value={"usi_inv_id": system_id}):
        
        sync_service.update_investment(system_id)
        
    # Verify upsert was called with inv_id only
    mock_upsert.assert_called_once()
    kwargs = mock_upsert.call_args.kwargs
    assert kwargs["inv_id"] == system_id
