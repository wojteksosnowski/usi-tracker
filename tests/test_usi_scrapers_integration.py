import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_worker.config import get_scraper_config
from usi_scrapers.manager import TechnicalDataManager

def test_technical_data_manager_initialization():
    """Verify that TechnicalDataManager initializes correctly with tracker config."""
    config = get_scraper_config()
    manager = TechnicalDataManager(config)
    
    assert manager.config == config
    assert manager.resolver is not None

def test_investment_path_resolution_with_mock():
    """Verify path resolution using portal and portal_id via mock."""
    config = get_scraper_config()
    manager = TechnicalDataManager(config)
    
    portal = "rp"
    portal_id = "12345"
    dev_slug = "dev-test"
    inv_slug = "inv-test"
    
    # Mock the resolver to return our slugs
    manager.resolver.lookup_investment = MagicMock(return_value=(dev_slug, inv_slug))
    
    expected_path = config.public_dir / "USIdata" / dev_slug / inv_slug
    
    path = manager.get_investment_path(portal, portal_id)
    assert path == expected_path
    manager.resolver.lookup_investment.assert_called_once_with(portal, portal_id)

def test_image_path_resolution_with_mock():
    """Verify image path resolution using portal and portal_id via mock."""
    config = get_scraper_config()
    manager = TechnicalDataManager(config)
    
    portal = "oto"
    portal_id = "abc-789"
    dev_slug = "dev-test"
    inv_slug = "inv-test"
    
    manager.resolver.lookup_investment = MagicMock(return_value=(dev_slug, inv_slug))
    
    expected_path = config.public_dir / "USI" / dev_slug / inv_slug
    
    path = manager.get_image_path(portal, portal_id)
    assert path == expected_path

def test_raw_data_filename_standard():
    """Verify that raw data filenames follow the raw_{portal}_{id}.json standard."""
    config = get_scraper_config()
    manager = TechnicalDataManager(config)
    
    portal = "oto"
    portal_id = "123"
    filename = manager.get_raw_filename(portal, portal_id)
    assert filename == f"raw_{portal}_{portal_id}.json"
    
    # Check fallback
    assert manager.get_raw_filename(portal) == f"raw_{portal}.json"
