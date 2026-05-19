import pytest
from python_worker.adapters import RPAdapter, OtodomAdapter, TOAdapter

def test_rp_resolution_choice():
    raw_data = {
        "id": 12345,
        "main_image": {
            "m_img_500": "https://cdn.rp.pl/main_500.jpg",
            "m_img_1500": "https://cdn.rp.pl/main_1500.jpg"
        },
        "_raw_gallery": {
            "gallery": [
                {
                    "image": {
                        "g_img_500": "https://cdn.rp.pl/1_500.jpg",
                        "g_img_1500": "https://cdn.rp.pl/1_1500.jpg",
                        "g_img_2000": "https://cdn.rp.pl/1_2000.jpg"
                    }
                }
            ]
        }
    }
    
    result = RPAdapter.transform(raw_data, "test", "dev")
    
    # Should pick 1500 for main and 2000 for gallery
    assert "https://cdn.rp.pl/main_1500.jpg" in result["image_urls"]
    assert "https://cdn.rp.pl/1_2000.jpg" in result["image_urls"]
    assert "https://cdn.rp.pl/main_500.jpg" not in result["image_urls"]
    assert "https://cdn.rp.pl/1_500.jpg" not in result["image_urls"]
    assert "https://cdn.rp.pl/1_1500.jpg" not in result["image_urls"]

def test_otodom_resolution_choice():
    raw_data = {
        "ad": {
            "images": [
                {
                    "thumbnail": "https://cdn.oto.pl/1_thumb.jpg",
                    "medium": "https://cdn.oto.pl/1_med.jpg",
                    "large": "https://cdn.oto.pl/1_large.jpg"
                }
            ]
        }
    }
    
    result = OtodomAdapter.transform(raw_data, "test", "dev")
    
    assert "https://cdn.oto.pl/1_large.jpg" in result["image_urls"]
    assert "https://cdn.oto.pl/1_med.jpg" not in result["image_urls"]
    assert "https://cdn.oto.pl/1_thumb.jpg" not in result["image_urls"]

def test_to_resolution_choice():
    raw_data = {
        "_raw_gallery_urls": [
            "https://content.tabelaofert.pl/quality_70,scale_500,image-123.jpg",
            "https://content.tabelaofert.pl/quality_70,scale_1584,image-123.jpg",
            "https://content.tabelaofert.pl/quality_70,scale_800,image-123.jpg",
            "https://content.tabelaofert.pl/quality_70,scale_1584,image-456.jpg"
        ]
    }
    
    result = TOAdapter.transform(raw_data, "test", "dev")

    # TOAdapter passes all resolution variants; resolution filtering happens in image_saver
    assert "https://content.tabelaofert.pl/quality_70,scale_1584,image-123.jpg" in result["image_urls"]
    assert "https://content.tabelaofert.pl/quality_70,scale_1584,image-456.jpg" in result["image_urls"]
    assert len(result["image_urls"]) == 4
