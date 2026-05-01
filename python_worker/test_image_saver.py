import pytest
import requests_mock
from pathlib import Path
from .image_saver import clean_filename, download_image
from .config import PUBLIC_USI_DIR

def test_clean_filename():
    assert clean_filename("https://example.com/image.jpg") == "image.jpg"
    assert clean_filename("https://example.com/image.png?width=100") == "image.png"
    assert clean_filename("https://example.com/path/to/my-image.webp") == "my-image.webp"
    # Otodom case (image.jpg/im-123.jpg)
    assert clean_filename("https://otodom.pl/image.jpg/im-123.jpg") == "im-123.jpg"

def test_download_image(tmp_path, monkeypatch):
    # Mock PUBLIC_USI_DIR to use tmp_path
    monkeypatch.setattr("python_worker.image_saver.PUBLIC_USI_DIR", tmp_path)
    
    url = "https://example.com/test.jpg"
    dev_slug = "test-dev"
    inv_slug = "test-inv"
    
    with requests_mock.Mocker() as m:
        m.get(url, content=b"fake image data")
        
        success = download_image(url, dev_slug, inv_slug)
        
        assert success is True
        expected_path = tmp_path / dev_slug / inv_slug / "test.jpg"
        assert expected_path.exists()
        assert expected_path.read_bytes() == b"fake image data"
