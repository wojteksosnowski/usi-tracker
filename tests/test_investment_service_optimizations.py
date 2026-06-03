import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from python_worker.services.investment_service import InvestmentService

@pytest.fixture
def mock_service(tmp_path):
    # Mocking out the config and technical manager to isolate our test
    with patch("python_worker.config.get_scraper_config", return_value=None):
        svc = InvestmentService(data_dir=tmp_path / "USIdata", public_usi_dir=tmp_path / "Public" / "USI")
        # Inject mock tech manager into the sync component
        svc.sync.tech_manager = MagicMock()
        # Also expose it on svc so the test assertion can read it
        svc.tech_manager = svc.sync.tech_manager
        return svc

def test_image_sync_optimizations(mock_service, tmp_path):
    """
    Test that update_investment correctly maps existing image_paths and directory 
    without falling back to os.walk over the entire Public/USI.
    """
    # Setup directories
    dev_dir = mock_service.data_dir / "test-dev"
    inv_dir = dev_dir / "test-inv"
    inv_dir.mkdir(parents=True)
    
    img_dir = mock_service.public_usi_dir / "test-dev" / "test-inv"
    img_dir.mkdir(parents=True)
    
    # Create some mock existing images
    (img_dir / "img2.jpg").write_text("fake image content")
    
    # Create anchor file with existing paths pointing to old locations
    old_path = "/Public/USI/old-dev/old-inv/img1.jpg"
    anchor_data = {
        "sources": {"rp": {"id": "123"}},
        "image_paths": [old_path]
    }
    (inv_dir / "usi_rp_123.json").write_text(json.dumps(anchor_data))
    
    # Create raw file so the local merge proceeds
    (inv_dir / "raw_rp_123.json").write_text("{}")
    
    # Mock get_investment_resources to return our mocked layout
    resources = {
        "base_dir": inv_dir,
        "files": {"anchor": inv_dir / "usi_rp_123.json"},
        "images_dir": img_dir,
        "metadata": {"slug": "test-dev/test-inv"}
    }
    mock_service.identity.get_investment_resources = MagicMock(return_value=resources)
    
    # Mock the fetching process and the adapter merge
    mock_unified = {
        "image_urls": [
            "https://example.com/images/img1.jpg",  # Should map to old_path
            "https://example.com/images/img2.jpg",  # Should map to img_dir/img2.jpg
            "https://example.com/images/img3.jpg"   # Should be downloaded
        ]
    }
    
    # We patch Merger.merge to return our mock_unified
    with patch("python_worker.services.investment_sync.Merger.merge", return_value=mock_unified):
        # We patch the scraper API so we don't do real requests
        with patch("usi_scrapers.api.fetch_investment", return_value={"raw_details": {}}):
            with patch("python_worker.services.investment_sync.AdapterFactory.get_adapter") as mock_factory:
                mock_adapter = MagicMock()
                mock_adapter.transform.return_value = {"some": "data"}
                mock_factory.return_value = mock_adapter
                
                # We need to simulate os.walk to ensure it is NOT called
                with patch("os.walk") as mock_os_walk:
                    
                    mock_service.update_investment("123", use_local_raw=True)
                    
                    # Ensure we didn't do the catastrophic full directory scan
                    mock_os_walk.assert_not_called()
                    
                    # Ensure tech_manager.sync_images was called ONLY for the missing image (img3)
                    # The exact call structure: sync_images(urls_to_download, img_dev_slug, inv_slug)
                    call_args = mock_service.tech_manager.sync_images.call_args
                    assert call_args is not None
                    
                    urls_to_download = call_args[0][0]
                    assert len(urls_to_download) == 1
                    assert urls_to_download[0] == "https://example.com/images/img3.jpg"
