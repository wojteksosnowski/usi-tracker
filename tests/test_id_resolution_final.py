import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from python_worker.services.investment_identity import InvestmentIdentityResolver

def test_get_investment_resources_strictly_id_based(tmp_path):
    # Setup
    data_dir = tmp_path / "Public" / "USIdata"
    public_usi_dir = tmp_path / "Public" / "USI"
    data_dir.mkdir(parents=True)
    
    resolver = InvestmentIdentityResolver(data_dir, public_usi_dir)
    
    # Create a mock entry in the index
    inv_id = "rp_12345"
    mock_entry = {
        "usi_inv_id": inv_id,
        "developer_slug": "dev-slug",
        "investment_slug": "inv-slug",
        "portal": "rp",
        "portal_id": "12345"
    }
    
    # Mock TechnicalDataManager
    mock_tech_manager = MagicMock()
    target_dir = tmp_path / "Resolved" / "rp" / "12345"
    mock_tech_manager.get_investment_path.return_value = target_dir
    mock_tech_manager.get_image_path.return_value = target_dir / "images"
    
    # Patch index loading and TechnicalDataManager
    with patch("python_worker.investment_index.load", return_value=[mock_entry]), \
         patch("python_worker.services.investment_identity.get_shared_tech_manager", return_value=mock_tech_manager):
        
        # Execute
        res = resolver.get_investment_resources(inv_id)
        
        # Verify
        assert res["id"] == inv_id
        assert res["base_dir"] == target_dir
        assert res["metadata"]["portal"] == "rp"
        assert res["metadata"]["portal_id"] == "12345"
        
        # Verify no slug-based resolution was attempted in a fallback way
        mock_tech_manager.get_investment_path.assert_called_once_with("rp", "12345")

def test_error_when_calling_removed_slug_method():
    # Setup
    resolver = InvestmentIdentityResolver("/tmp", "/tmp")
    
    # Verify method is gone
    with pytest.raises(AttributeError):
        resolver.get_investment_resources_by_slug("dev", "inv")
