import json
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure usi-scrapers is in path
LIB_PATH = "/Volumes/Samsam/claude-py/usi-scrapers"
if LIB_PATH not in sys.path:
    sys.path.append(LIB_PATH)

from python_worker.services.discovery_service import DiscoveryService
from python_worker.services.investment_service import InvestmentService

@pytest.fixture
def test_env(tmp_path):
    # Setup isolated structure
    data_dir = tmp_path / "USIdata"
    data_dir.mkdir()
    usi_dir = tmp_path / "USI"
    usi_dir.mkdir()
    dev_dir = tmp_path / "USIdev"
    dev_dir.mkdir()
    
    # Mock config constants to point to tmp_path
    with patch("python_worker.config.USI_DATA_DIR", data_dir), \
         patch("python_worker.config.PUBLIC_USI_DIR", usi_dir), \
         patch("python_worker.config.USI_DEV_DIR", dev_dir), \
         patch("python_worker.config.DROPBOX_PATH", tmp_path):
        
        from python_worker.config import get_scraper_config
        config = get_scraper_config()
        
        ds = DiscoveryService(data_dir=data_dir)
        isvc = InvestmentService(data_dir=data_dir, public_usi_dir=usi_dir)
        
        yield ds, isvc, data_dir, usi_dir

def test_tabelaofert_full_ingestion_cycle_with_name_protection(test_env):
    """
    Permanent E2E test for TabelaOfert:
    1. Discovery of a known investment.
    2. Registration with a custom 'SEO' name.
    3. Update/Ingestion from live portal.
    4. Verification that the name remains PROTECTED (doesn't change to marketing name).
    """
    ds, isvc, data_dir, usi_dir = test_env
    
    # We use 'Flatta Wilanow' as our stable test case
    target_search_term = "flatta"
    custom_seo_name = "CUSTOM SEO NAME: Flatta Wilanow Warszawa"
    
    print(f"\n[1/4] Discovery...")
    found_item = None
    try:
        results = ds.discovery_by_portal("to", limit=500)
        for item in results:
            if target_search_term in item.get("name", "").lower():
                found_item = item
                break
    except Exception as e:
        pytest.fail(f"Discovery failed: {e}")
        
    assert found_item is not None, f"Could not find '{target_search_term}' in discovery results."
    print(f"      Found: {found_item['name']}")
    
    # Phase 2: Registration with CUSTOM name
    print(f"[2/4] Registration with protection...")
    dev_name = found_item.get("developer_name") or "Discovery Developer"
    inv_slug = found_item["slug"]
    
    try:
        dev_slug, registered_inv_slug = isvc.register_investment(
            portal="to",
            developer_name=dev_name,
            inv_slug=inv_slug,
            name=custom_seo_name, # Registering with a specific name we want to keep
            item_id=found_item.get("id"),
            url=found_item["url"]
        )
    except Exception as e:
        pytest.fail(f"Registration failed: {e}")
        
    usi_file = data_dir / dev_slug / inv_slug / f"usi_{inv_slug}.json"
    with open(usi_file, "r", encoding="utf-8") as f:
        initial_data = json.load(f)
    assert initial_data["name"] == custom_seo_name
    
    # Phase 3: Update (Full Ingestion)
    print(f"[3/4] Ingestion (Merger process)...")
    try:
        success = isvc.update_investment(dev_slug, inv_slug)
        assert success is True
    except Exception as e:
        pytest.fail(f"Update failed: {e}")
        
    # Phase 4: Verification of Name Protection
    print(f"[4/4] Verifying Name Protection...")
    with open(usi_file, "r", encoding="utf-8") as f:
        final_data = json.load(f)
        
    # THE CORE ASSERTION: The name must NOT have changed to "Flatta Wilanów" 
    # (which is what the portal returns) but should stay as our custom_seo_name.
    assert final_data["name"] == custom_seo_name, \
        f"Name Protection FAILED! Expected '{custom_seo_name}', but got '{final_data['name']}'"
    
    # Verify other data WAS ingested
    assert final_data["financials"].get("price_min") is not None
    assert final_data["location"].get("city") == "Warszawa"
    assert (data_dir / dev_slug / inv_slug / f"raw_to_{inv_slug}.json").exists()
    
    print("✅ Full cycle passed. Name Protection verified.")

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-s"]))
