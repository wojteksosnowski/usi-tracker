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
