import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from pathlib import Path
import json

from python_worker.api.blueprints.reports import reports_bp
from python_worker.api.blueprints.poi import poi_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(poi_bp, url_prefix='/api')
    app.config['TESTING'] = True
    return app.test_client()

# --- REPORTS TESTS ---

def test_pending_summary_uses_global_manager(client):
    """Test that /reports/pending-summary uses the globally imported DeveloperManager."""
    with patch("python_worker.api.blueprints.investments.developer_manager") as mock_dm:
        mock_dm.get_total_pending_count.return_value = 42
        
        response = client.get("/api/reports/pending-summary")
        assert response.status_code == 200
        assert response.json["total_pending"] == 42
        mock_dm.get_total_pending_count.assert_called_once()

def test_report_data_uses_index(client):
    """Test that /report/<id>/data uses the investment index instead of full disk iteration."""
    
    # Mock the index
    mock_invs = [
        {"id": "inv1", "name": "Investment 1", "address": "Warsaw"},
        {"id": "inv2", "name": "Investment 2", "address": "Krakow"}
    ]
    
    # Mock the filesystem report read
    mock_report = {"id": "test_report", "filters": {"city": "Warsaw"}}
    
    with patch("python_worker.investment_index.get_index", return_value=mock_invs) as mock_get_index:
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_report)):
                response = client.get("/api/report/test_report/data")
                assert response.status_code == 200
                data = response.json["data"]
                
                # Should only return Warsaw
                assert len(data) == 1
                assert data[0]["id"] == "inv1"
                
                mock_get_index.assert_called_once()


# --- POI TESTS ---

def test_get_poi_uses_system_id(client):
    """Test that POI resolution favors system_id via InvestmentService."""
    
    # Mock InvestmentService to return correct slugs
    mock_inv = {"developer_slug": "correct-dev", "investment_slug": "correct-inv"}
    
    with patch("python_worker.api.blueprints.investments.investment_service") as mock_inv_service:
        mock_inv_service.get_investment.return_value = mock_inv
        
        # Mock the path check and file read
        with patch("python_worker.api.blueprints.poi._poi_path") as mock_poi_path:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = '{"poi": "data"}'
            mock_poi_path.return_value = mock_path
            
            response = client.get("/api/poi/wrong-dev/wrong-inv?id=123")
            
            assert response.status_code == 200
            assert response.json == {"poi": "data"}
            
            # Verify investment service was called with system_id
            mock_inv_service.get_investment.assert_called_once_with(None, None, system_id="123")
            
            # Verify _poi_path was called with CORRECT slugs
            mock_poi_path.assert_called_once_with("correct-dev", "correct-inv")

def test_fetch_poi_uses_system_id(client):
    """Test that fetching POI favors system_id via InvestmentService."""
    mock_inv = {
        "developer_slug": "correct-dev", 
        "investment_slug": "correct-inv",
        "location": {"coords": [52.0, 21.0]}
    }
    
    with patch("python_worker.api.blueprints.investments.investment_service") as mock_inv_service:
        mock_inv_service.get_investment.return_value = mock_inv
        
        # We need to mock HERE API and Wikipedia API to avoid real calls
        with patch("python_worker.api.blueprints.poi._fetch_here_places", return_value=[]) as mock_here:
            with patch("python_worker.api.blueprints.poi._fetch_wiki_articles", return_value=[]) as mock_wiki:
                with patch("python_worker.api.blueprints.poi._poi_path") as mock_poi_path:
                    mock_path = MagicMock()
                    mock_poi_path.return_value = mock_path
                    
                    response = client.post("/api/poi/wrong-dev/wrong-inv/fetch?id=123")
                    
                    assert response.status_code == 200
                    
                    # Verify investment service was called
                    mock_inv_service.get_investment.assert_called_once_with(None, None, system_id="123")
                    
                    # Verify path was built correctly
                    mock_poi_path.assert_called_once_with("correct-dev", "correct-inv")
                    mock_path.write_text.assert_called_once()
