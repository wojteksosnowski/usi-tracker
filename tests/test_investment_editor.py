import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_worker.services.investment_editor import InvestmentEditorService

@pytest.fixture
def mock_identity():
    resolver = MagicMock()
    return resolver

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    return repo

@pytest.fixture
def editor_service(mock_identity, mock_repo, tmp_path):
    return InvestmentEditorService(
        identity_resolver=mock_identity,
        data_dir=tmp_path / "USIdata",
        public_usi_dir=tmp_path / "Public" / "USI",
        investment_repo=mock_repo
    )

def test_save_ratings_success(editor_service, mock_identity, mock_repo, tmp_path):
    system_id = "rp_123"
    payload = {"Balkony": 4, "komentarz": "Super", "status": "Wstępna"}
    
    # Mock resources
    anchor_file = tmp_path / "usi_rp_123.json"
    anchor_file.parent.mkdir(parents=True, exist_ok=True)
    anchor_file.write_text(json.dumps({
        "usi_inv_id": system_id,
        "status": "Brak",
        "ratings": {}
    }))
    
    mock_identity.get_investment_resources.return_value = {
        "base_dir": anchor_file.parent,
        "files": {"anchor": anchor_file},
        "metadata": {"slug": "dev/inv"}
    }
    
    mock_repo.get_ratings.return_value = {}
    
    result = editor_service.save_ratings(system_id, payload)
    
    assert result is True
    assert mock_repo.save_investment_json.called
    assert mock_repo.save_ratings.called
    
    # Verify data passed to repo
    saved_data = mock_repo.save_investment_json.call_args[0][1]
    assert saved_data["ratings"]["Balkony"] == 4.0
    assert saved_data["ratings"]["komentarz"] == "Super"
    assert saved_data["status"] == "Wstępna"

def test_save_ratings_invalid_status(editor_service, mock_identity):
    system_id = "rp_123"
    payload = {"status": "INVALID_STATUS"}
    
    mock_identity.get_investment_resources.return_value = {
        "base_dir": Path("/tmp"),
        "files": {"anchor": MagicMock(exists=lambda: True)}
    }
    
    with pytest.raises(ValueError, match="Invalid status"):
        editor_service.save_ratings(system_id, payload)

def test_mark_as_reviewed(editor_service, mock_identity, mock_repo):
    system_id = "rp_123"
    
    mock_identity.get_investment_resources.return_value = {
        "metadata": {"slug": "dev/inv"}
    }
    mock_repo.get_investment_json.return_value = {"usi_inv_id": system_id, "reviewed": False}
    
    result = editor_service.mark_as_reviewed(system_id)
    
    assert result is True
    saved_data = mock_repo.save_investment_json.call_args[0][1]
    assert saved_data["reviewed"] is True
