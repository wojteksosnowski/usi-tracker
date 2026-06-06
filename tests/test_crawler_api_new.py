import pytest
from python_worker.ui_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_system_status_passive(client):
    """Test the new passive system status endpoint."""
    response = client.get("/api/system/status")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["mode"] == "passive"
    assert response.json["daemons"] == "disabled"

def test_legacy_crawler_endpoints_removed(client):
    """Test that legacy crawler endpoints are indeed removed (should return 404)."""
    response = client.get("/api/crawler/status")
    assert response.status_code == 404
    
    response = client.get("/api/doktor/status")
    assert response.status_code == 404
