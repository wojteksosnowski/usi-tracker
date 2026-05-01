import pytest
import requests_mock
from .scraper_rp import fetch_rp_details, fetch_rp_gallery

def test_fetch_rp_details():
    offer_id = "123"
    url = f"https://rynekpierwotny.pl/api/v2/offers/offer/{offer_id}/?s=offer-detail"
    mock_response = {"id": 123, "name": "Test Investment"}
    
    with requests_mock.Mocker() as m:
        m.get(url, json=mock_response)
        
        details = fetch_rp_details(offer_id)
        assert details == mock_response

def test_fetch_rp_gallery():
    offer_id = "123"
    url = f"https://rynekpierwotny.pl/api/v2/offers/offer/{offer_id}/?s=offer-detail-gallery"
    mock_response = {
        "gallery": [
            {"image": {"g_img_1500": "https://example.com/1.jpg"}},
            {"image": {"g_img_1500": "https://example.com/2.jpg"}}
        ]
    }
    
    with requests_mock.Mocker() as m:
        m.get(url, json=mock_response)
        
        gallery = fetch_rp_gallery(offer_id)
        assert len(gallery) == 2
        assert "https://example.com/1.jpg" in gallery
        assert "https://example.com/2.jpg" in gallery
