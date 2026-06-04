import pytest
from flask import Flask
from python_worker.ui_server import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_crawler_status_no_instance(client):
    """Test /api/crawler/status when no crawler instance exists."""
    with patch("python_worker.daemons.get_crawler", return_value=None):
        response = client.get("/api/crawler/status")
        assert response.status_code == 200
        assert response.json == {"running": False, "paused": False}

def test_crawler_status_with_instance(client):
    """Test /api/crawler/status with a mocked crawler instance."""
    mock_crawler = MagicMock()
    mock_crawler.get_status.return_value = {
        "running": True,
        "paused": False,
        "current_task": "visiting",
        "current_dev": "test-dev"
    }
    
    with patch("python_worker.daemons.get_crawler", return_value=mock_crawler):
        response = client.get("/api/crawler/status")
        assert response.status_code == 200
        assert response.json["running"] is True
        assert response.json["current_task"] == "visiting"

def test_crawler_pause_resume(client):
    """Test pause and resume endpoints."""
    mock_crawler = MagicMock()
    
    with patch("python_worker.daemons.get_crawler", return_value=mock_crawler):
        # Pause
        response = client.post("/api/crawler/pause")
        assert response.status_code == 200
        mock_crawler.pause.assert_called_once()
        
        # Resume
        response = client.post("/api/crawler/resume")
        assert response.status_code == 200
        mock_crawler.resume.assert_called_once()

def test_doktor_status(client):
    """Test /api/doktor/status endpoint."""
    mock_doktor = MagicMock()
    mock_doktor.get_status.return_value = {"running": True, "pairs_analyzed": 100}
    
    with patch("python_worker.daemons.get_doktor", return_value=mock_doktor):
        response = client.get("/api/doktor/status")
        assert response.status_code == 200
        assert response.json["running"] is True
        assert response.json["pairs_analyzed"] == 100
