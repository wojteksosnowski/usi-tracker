import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_worker.services.investment_loader import load_investment

def test_load_investment_fails_without_id_or_file():
    result = load_investment()
    assert result is None

def test_load_investment_fails_on_legacy_id():
    result = load_investment(system_id="legacy_123")
    assert result is None

@patch("python_worker.services.investment_service.InvestmentService")
def test_load_investment_uses_system_id_to_resolve_resources(mock_investment_service, tmp_path):
    mock_svc = MagicMock()
    mock_investment_service.return_value = mock_svc
    
    system_id = "rp_123"
    anchor_file = tmp_path / "dev/inv/usi_rp_123.json"
    anchor_file.parent.mkdir(parents=True, exist_ok=True)
    anchor_file.write_text('{"name": "Test Inv", "usi_inv_id": "rp_123"}')
    
    mock_svc.get_investment_resources.return_value = {
        "files": {"anchor": anchor_file},
        "metadata": {"slug": "dev/inv"},
        "base_dir": anchor_file.parent
    }
    
    result = load_investment(system_id=system_id, data_dir=tmp_path)
    
    assert result is not None
    assert result["name"] == "Test Inv"
    assert result["usi_inv_id"] == "rp_123"
    mock_svc.get_investment_resources.assert_called_once_with(system_id)
