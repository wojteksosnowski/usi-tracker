import pytest
from unittest.mock import MagicMock, patch
from flask import Flask, jsonify
from pathlib import Path

from python_worker.api.blueprints.investments import investments_bp
from python_worker.api.blueprints.discovery import discovery_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(investments_bp, url_prefix='/api')
    app.register_blueprint(discovery_bp, url_prefix='/api')
    app.config['TESTING'] = True
    return app.test_client()

@pytest.fixture
def mock_inv_service():
    with patch("python_worker.api.blueprints.investments.investment_service") as mock_svc:
        yield mock_svc

@pytest.fixture
def mock_dev_manager():
    with patch("python_worker.api.blueprints.investments.developer_manager") as mock_dm:
        yield mock_dm

# 1. Test /api/data endpoint using system_id (ID-Only) vs fallback
def test_investment_data_uses_system_id(client, mock_inv_service):
    """Test if providing ?id= resolves using ID-only."""
    mock_inv_service.get_investment.return_value = {"id": "123", "name": "Test Inv"}
    
    response = client.get("/api/data/dev-old/inv-old?id=123")
    assert response.status_code == 200
    assert response.json["name"] == "Test Inv"
    
    # Should ignore dev_slug and inv_slug if system_id is present
    mock_inv_service.get_investment.assert_called_once_with(
        dev_slug=None, inv_slug=None, system_id="123"
    )

def test_investment_data_fallback_to_slugs(client, mock_inv_service):
    """Test if it falls back to slugs when no id is provided."""
    mock_inv_service.get_investment.return_value = {"id": "999", "name": "Fallback Inv"}
    
    response = client.get("/api/data/dev-old/inv-old")
    assert response.status_code == 200
    
    mock_inv_service.get_investment.assert_called_once_with(
        dev_slug="dev-old", inv_slug="inv-old", system_id=None
    )

# 2. Test /api/download-raw endpoint using Resource Resolver vs fallback
def test_download_raw_uses_resolver(client, mock_inv_service):
    """Test if download raw uses Identity Resolver correctly to find physical paths."""
    mock_inv_service.get_investment_resources.return_value = {
        "anchor": Path("/resolver/path/usi_inv_123.json")
    }
    
    # Mock download_raw_json and _find_inv_file
    with patch("python_worker.main.download_raw_json", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value={"sources": {"rp": {"id": "rp123"}}}):
                with patch("pathlib.Path.exists", return_value=True):
                    response = client.post("/api/download-raw/dev-old/inv-old?id=123")
                
                assert response.status_code == 200
                assert response.json == {"ok": True}
                
                # Verified that it called the resolver with system_id
                mock_inv_service.get_investment_resources.assert_called_once_with("123")

# 3. Test /api/developer/logo
def test_serve_logo_uses_resolver(client, mock_dev_manager):
    """Test if logo serving resolves the directory from ID instead of static slugs."""
    mock_dev_manager.get_developer_resources.return_value = {
        "directory": Path("/resolved/dev/directory")
    }
    
    # Mock send_file to just return the path it was given
    with patch("python_worker.api.blueprints.investments.send_file") as mock_send_file:
        mock_send_file.side_effect = lambda path: jsonify({"file_sent": str(path)})
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                response = client.get("/api/developer/dev-old/logo?id=dev123")
                
                assert response.status_code == 200
                assert "file_sent" in response.json
                # Path should be from resolver, not USI_DEV_DIR / dev-old
                assert "resolved/dev/directory/logo.png" in response.json["file_sent"]
                
                mock_dev_manager.get_developer_resources.assert_called_once_with("dev123")

def test_developers_list_global_manager(client, mock_dev_manager):
    """Test if /developers endpoint uses the global manager and is fast."""
    mock_dev_manager.list_developers.return_value = [{"name": "A"}, {"name": "B"}]
    
    response = client.get("/api/developers")
    assert response.status_code == 200
    assert len(response.json) == 2
    mock_dev_manager.list_developers.assert_called_once()
