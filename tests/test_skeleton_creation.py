import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from python_worker.investment_repository import InvestmentRepository

def test_create_investment_skeleton_uses_tech_manager(tmp_path):
    # Setup
    mock_identity = MagicMock()
    data_dir = tmp_path / "Public" / "USIdata"
    repo = InvestmentRepository(mock_identity, data_dir)
    
    system_id = "rp_12345"
    portal = "rp"
    portal_id = "12345"
    skeleton_data = {"name": "Test Investment", "usi_inv_id": system_id}
    
    # Mock TechnicalDataManager and config
    mock_config = MagicMock()
    mock_tech_manager = MagicMock()
    
    # Define the "correct" path according to the manager
    target_dir = tmp_path / "ResolvedPath" / "rp" / "12345"
    mock_tech_manager.get_investment_path.return_value = target_dir
    
    with patch("python_worker.investment_repository.get_shared_tech_manager", return_value=mock_tech_manager):
        
        # Execute
        target_file = repo.create_investment_skeleton(system_id, portal, portal_id, skeleton_data)
        
        # Verify
        assert target_file == target_dir / f"usi_{system_id}.json"
        assert target_file.exists()
        
        # Verify content
        with open(target_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            assert saved_data["usi_inv_id"] == system_id
            
        # Verify TechnicalDataManager was called correctly
        mock_tech_manager.get_investment_path.assert_called_once_with(portal, portal_id)

def test_create_investment_skeleton_fallback_when_config_missing(tmp_path):
    # Setup
    mock_identity = MagicMock()
    data_dir = tmp_path / "Public" / "USIdata"
    repo = InvestmentRepository(mock_identity, data_dir)
    
    system_id = "rp_12345"
    portal = "rp"
    portal_id = "12345"
    skeleton_data = {
        "name": "Test Investment", 
        "usi_inv_id": system_id,
        "developer_slug": "dev-slug",
        "investment_slug": "inv-slug"
    }
    
    # Mock tech manager as None
    with patch("python_worker.investment_repository.get_shared_tech_manager", return_value=None):
        # Execute
        target_file = repo.create_investment_skeleton(system_id, portal, portal_id, skeleton_data)
        
        # Verify fallback path: data_dir / dev_slug / inv_slug
        expected_dir = data_dir / "dev-slug" / "inv-slug"
        assert target_file == expected_dir / f"usi_{system_id}.json"
        assert target_file.exists()
