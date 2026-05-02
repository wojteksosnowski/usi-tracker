import pytest
import json
from python_worker.adapters import RPAdapter, OtodomAdapter, TOAdapter

def test_rp_adapter_extraction():
    raw_data = {
        "id": 12345,
        "name": "Test RP Investment",
        "url": "https://rp.pl/12345",
        "main_image": {"m_img_500": "https://cdn.rp.pl/main.jpg"},
        "_raw_gallery": {
            "gallery": [
                {"image": {"g_img_1500": "https://cdn.rp.pl/1.jpg"}},
                {"image": {"g_img_1500": "https://cdn.rp.pl/2.jpg"}}
            ]
        }
    }
    
    result = RPAdapter.transform(raw_data, "test-inv", "test-dev")
    
    assert result["name"] == "Test RP Investment"
    assert "https://cdn.rp.pl/main.jpg" in result["image_urls"]
    assert "https://cdn.rp.pl/1.jpg" in result["image_urls"]
    assert "https://cdn.rp.pl/2.jpg" in result["image_urls"]
    assert len(result["image_urls"]) == 3
    assert result["images_count"] == 3

def test_otodom_adapter_extraction():
    raw_data = {
        "ad": {
            "id": 999,
            "title": "Test Otodom Investment",
            "url": "https://otodom.pl/999",
            "images": [
                {"large": "https://cdn.oto.pl/1.jpg"},
                {"large": "https://cdn.oto.pl/2.jpg"}
            ]
        }
    }
    
    result = OtodomAdapter.transform(raw_data, "test-inv", "test-dev")
    
    assert result["name"] == "Test Otodom Investment"
    assert "https://cdn.oto.pl/1.jpg" in result["image_urls"]
    assert "https://cdn.oto.pl/2.jpg" in result["image_urls"]
    assert len(result["image_urls"]) == 2

def test_to_adapter_extraction():
    raw_data = {
        "name": "Test TO Investment",
        "url": "https://to.pl/123",
        "_raw_gallery_urls": [
            "https://cdn.to.pl/1.jpg",
            "https://cdn.to.pl/2.jpg"
        ]
    }
    
    result = TOAdapter.transform(raw_data, "test-inv", "test-dev")
    
    assert result["name"] == "Test TO Investment"
    assert "https://cdn.to.pl/1.jpg" in result["image_urls"]
    assert "https://cdn.to.pl/2.jpg" in result["image_urls"]
    assert len(result["image_urls"]) == 2
