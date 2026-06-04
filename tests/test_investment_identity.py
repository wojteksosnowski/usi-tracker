import pytest
from pathlib import Path
from python_worker.services.investment_identity import InvestmentIdentityResolver

def test_investment_identity_resolver_uses_tech_manager(monkeypatch, tmp_path):
    # Setup mock data directory
    data_dir = tmp_path / "USIdata"
    public_dir = tmp_path / "Public"
    
    # Create the resolver
    resolver = InvestmentIdentityResolver(data_dir, public_dir)
    
    # Create mock entry
    entry = {
        "usi_inv_id": "inv_123",
        "developer_slug": "dev_test",
        "investment_slug": "inv_test",
        "portal": "rp",
        "portal_id": "999"
    }

    # Mock the config and tech_manager to avoid hitting real config
    class MockConfig:
        pass
    mock_cfg = MockConfig()
    mock_cfg.public_dir = str(public_dir)

    def mock_get_config():
        return mock_cfg

    class MockTechManager:
        def __init__(self, config):
            self.config = config
        def get_investment_path(self, portal, portal_id):
            return Path(self.config.public_dir) / "USIdata" / "dev_test" / "inv_test"
        def get_image_path(self, portal, portal_id):
            return Path(self.config.public_dir) / "USI" / "dev_test" / "inv_test"

    monkeypatch.setattr("python_worker.config.get_scraper_config", mock_get_config)
    monkeypatch.setattr("usi_scrapers.manager.TechnicalDataManager", MockTechManager)

    expected_inv_dir = Path(public_dir) / "USIdata" / "dev_test" / "inv_test"
    expected_img_dir = Path(public_dir) / "USI" / "dev_test" / "inv_test"
    expected_inv_dir.mkdir(parents=True, exist_ok=True)
    expected_img_dir.mkdir(parents=True, exist_ok=True)

    # Call the method
    resources = resolver._map_resources_from_entry(entry)

    # Verify that paths are correctly resolved
    assert resources["base_dir"] == Path(public_dir) / "USIdata" / "dev_test" / "inv_test"
    assert resources["images_dir"] == Path(public_dir) / "USI" / "dev_test" / "inv_test"
    assert resources["metadata"]["portal"] == "rp"
    assert resources["metadata"]["portal_id"] == "999"
