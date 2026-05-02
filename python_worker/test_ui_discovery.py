import pytest
from unittest.mock import patch, MagicMock
from python_worker.ui_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_discovery_rp_global(client):
    mock_results = [{"id": "1", "name": "Inv 1", "slug": "inv-1"}]
    with patch("python_worker.ui_server.discover_rp_investments", return_value=mock_results) as mock_disc:
        with patch("python_worker.portal_matcher.filter_new_investments", side_effect=lambda x, p: x):
            response = client.get("/api/discovery/rp")
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 1
            mock_disc.assert_called_with(None)

def test_discovery_oto_global(client):
    mock_results = [{"id": "oto1", "name": "Oto 1", "slug": "oto-1"}]
    # Mocking config
    with patch("python_worker.config.OTODOM_DISCOVERY_URLS", ["url1", "url2"]):
        with patch("python_worker.scraper_otodom.discover_otodom_listing", return_value=mock_results) as mock_disc:
            with patch("python_worker.portal_matcher.filter_new_investments", side_effect=lambda x, p: x):
                response = client.get("/api/discovery/oto")
                assert response.status_code == 200
                data = response.get_json()
                assert len(data) == 1
                assert mock_disc.call_count == 2
