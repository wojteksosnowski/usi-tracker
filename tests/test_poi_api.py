import pytest
import json
from unittest.mock import MagicMock, patch
from flask import Flask
from python_worker.api.blueprints.poi import poi_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(poi_bp)
    app.testing = True
    return app.test_client()

def test_get_poi_missing_returns_404(client):
    with patch("python_worker.api.blueprints.poi._poi_path") as mock_path:
        mock_path.return_value = None
        
        # Test fallback
        with patch("python_worker.api.blueprints.investments.investment_service.get_investment", return_value=None):
            resp = client.get("/poi/rp_123")
            assert resp.status_code == 404

def test_get_poi_success(client, tmp_path):
    system_id = "rp_123"
    poi_file = tmp_path / "poi.json"
    poi_file.write_text('{"status": "ok"}')
    
    with patch("python_worker.api.blueprints.poi._poi_path") as mock_path, \
         patch("python_worker.api.blueprints.investments.investment_service.repo.get_investment_json", return_value={"id": "mock"}):
        mock_path.return_value = poi_file
        
        resp = client.get(f"/poi/{system_id}")
        assert resp.status_code == 200
        assert resp.json == {"status": "ok"}

@patch("python_worker.api.blueprints.poi.HereMapsService")
@patch("python_worker.api.blueprints.poi._fetch_wiki_articles")
def test_fetch_poi_success(mock_wiki, mock_here, client, tmp_path):
    system_id = "rp_123"
    poi_file = tmp_path / "poi.json"
    
    mock_here_instance = MagicMock()
    mock_here_instance.fetch_places.return_value = [{"name": "Sklep"}]
    mock_here.return_value = mock_here_instance
    mock_wiki.return_value = [{"title": "Zabytkowa kamienica"}]
    
    mock_inv = {"coords": [52.0, 21.0]}
    
    with patch("python_worker.api.blueprints.investments.investment_service.get_investment", return_value=mock_inv), \
         patch("python_worker.api.blueprints.investments.investment_service.repo.get_investment_json", return_value={"id": "mock"}), \
         patch("python_worker.api.blueprints.investments.investment_service.repo.save_investment_json") as mock_save, \
         patch("python_worker.api.blueprints.poi._poi_path", return_value=poi_file):
             
        resp = client.post(f"/poi/{system_id}/fetch")
        
        assert resp.status_code == 200
        data = resp.json
        assert data["lat"] == 52.0
        assert data["lon"] == 21.0
        assert len(data["here_places"]) == 1
        assert len(data["wiki_articles"]) == 1
        
        assert mock_save.called
        saved_args = mock_save.call_args[0]
        saved = saved_args[1]
        assert "poi" in saved
        assert saved["poi"]["lat"] == 52.0
