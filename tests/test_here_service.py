import json
import pytest
from unittest.mock import MagicMock, patch
from python_worker.services.here_maps_service import HereMapsService

def test_geocode_address_success():
    api_key = "test_key"
    service = HereMapsService(api_key)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [{"position": {"lat": 52.2297, "lng": 21.0122}}]
    }
    
    with patch("requests.get", return_value=mock_response):
        lat, lon = service.geocode_address("Warszawa")
        assert lat == 52.2297
        assert lon == 21.0122

def test_geocode_address_failure():
    service = HereMapsService("key")
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch("requests.get", return_value=mock_response):
        lat, lon = service.geocode_address("Unknown")
        assert lat is None
        assert lon is None

def test_fetch_places_success():
    service = HereMapsService("key")
    
    mock_data = {
        "items": [
            {
                "id": "1",
                "title": "Test Place",
                "address": {"label": "Test Address"},
                "distance": 100,
                "position": {"lat": 52.1, "lng": 21.1},
                "categories": [{"name": "Test Category"}]
            }
        ]
    }
    
    # Mock urllib.request.urlopen
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_data).encode()
    mock_resp.__enter__.return_value = mock_resp
    
    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = service.fetch_places(52.2, 21.0)
        assert len(results) > 0
        assert results[0]["name"] == "Test Place"
        assert results[0]["category_label"] == "Test Category"

def test_build_here_url():
    service = HereMapsService("test_key")
    url = service.build_here_url(52.2, 21.0, zoom=15)
    
    assert "apiKey=test_key" in url
    assert "point:52.2,21.0" in url
    assert "zoom=15" in url
    assert "explore.satellite.day" in url

def test_build_here_url_dark():
    service = HereMapsService("test_key")
    url = service.build_here_url(52.2, 21.0, dark=True)
    assert "explore.satellite.night" in url
