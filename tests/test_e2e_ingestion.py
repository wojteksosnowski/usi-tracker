import pytest
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_worker.services.investment_sync import InvestmentSyncService
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.developer_manager import DeveloperManager

@pytest.fixture
def test_env(tmp_path):
    """Sets up a realistic USI filesystem structure in a temp directory."""
    data_dir = tmp_path / "Public" / "USIdata"
    dev_dir = tmp_path / "Public" / "USIdev"
    public_usi_dir = tmp_path / "Public" / "USI"
    
    data_dir.mkdir(parents=True)
    dev_dir.mkdir(parents=True)
    public_usi_dir.mkdir(parents=True)
    
    # Pre-create index files to avoid errors
    (data_dir / "_index.json").write_text(json.dumps({"entries": [], "count": 0}))
    (dev_dir / "_dev_index.json").write_text(json.dumps({"entries": [], "count": 0}))
    (dev_dir / "_dev_master_index.json").write_text(json.dumps({"entries": {}}))
    
    # Mock Config
    mock_config = MagicMock()
    mock_config.public_dir = str(tmp_path / "Public")
    mock_config.usi_data_dir = data_dir
    mock_config.usi_dev_dir = dev_dir
    
    # Mock TechnicalDataManager (from usi-scrapers)
    mock_tm = MagicMock()
    # By default, it returns None for new investments (not yet in its index)
    mock_tm.get_investment_path.return_value = None
    mock_tm.get_image_path.return_value = None
    mock_tm.config = MagicMock()
    
    with patch("python_worker.config.get_shared_config", return_value=mock_config), \
         patch("python_worker.config.get_shared_tech_manager", return_value=mock_tm), \
         patch("python_worker.config.USI_DATA_DIR", data_dir), \
         patch("python_worker.config.USI_DEV_DIR", dev_dir), \
         patch("python_worker.config.PUBLIC_USI_DIR", public_usi_dir):
        
        identity = InvestmentIdentityResolver(data_dir, public_usi_dir)
        dm = DeveloperManager(data_dir, dev_dir)
        sync_service = InvestmentSyncService(identity, data_dir, public_usi_dir)
        
        yield {
            "sync": sync_service,
            "dm": dm,
            "identity": identity,
            "tm": mock_tm,
            "data_dir": data_dir,
            "dev_dir": dev_dir,
            "public_usi_dir": public_usi_dir
        }

def test_e2e_batch_ingest_new_otodom(test_env):
    """Tests full pipeline from discovery item to disk for Otodom."""
    sync = test_env["sync"]
    tm = test_env["tm"]
    data_dir = test_env["data_dir"]
    
    portal = "oto"
    item_id = "4BFOJ"
    vendor_id = "11836422"
    dev_name = "Dasta Invest"
    inv_name = "Pekowicka"
    
    # Mock discovery item
    discovery_items = [{
        "id": item_id,
        "url": f"https://www.otodom.pl/pl/oferta/id{item_id}",
        "name": inv_name,
        "developer_name": dev_name,
        "vendor_id": vendor_id
    }]
    
    # Mock Gateway batch results
    raw_payload = {
        "id": item_id,
        "name": inv_name,
        "props": {
            "pageProps": {
                "ad": {
                    "id": 12345,
                    "title": inv_name,
                    "agency": {"id": int(vendor_id), "name": dev_name},
                    "location": {"coordinates": {"latitude": 50.1, "longitude": 19.9}}
                }
            }
        }
    }
    
    # The gateway process_batch returns a list of results
    sync.gateway.process_batch = MagicMock(return_value=[raw_payload])
    sync.gateway.load_raw = MagicMock(return_value=raw_payload)
    
    # Mock transform_to_unified (we'll let the real library handle it if possible, 
    # but here we mock it to control the E2E flow in tracker)
    with patch("usi_scrapers.mapping.transform_to_unified") as mock_transform:
        mock_transform.return_value = {
            "id": item_id,
            "name": inv_name,
            "developer_name": dev_name,
            "vendor_id": vendor_id,
            "latitude": 50.1,
            "longitude": 19.9
        }
        
        # ACT: Run batch process
        count = sync.process_batch(portal, discovery_items)
        
    # ASSERTIONS
    assert count == 1
    
    # 1. Verify directory creation (fallback because tm returns None)
    expected_dev_slug = "unknown" # Since it's a new ID and not in index yet
    # Wait, in our fixed logic, if vendor_id is present and not found, it goes to 'unknown'
    # OR if we have a slugify logic... let's check
    
    # Search for the created usi_*.json file
    usi_files = list(data_dir.rglob(f"usi_{portal}_{item_id}.json"))
    assert len(usi_files) == 1
    usi_file = usi_files[0]
    
    # 2. Verify content
    data = json.loads(usi_file.read_text())
    assert data["usi_inv_id"] == f"{portal}_{item_id}"
    assert data["name"] == inv_name
    assert data["developer"] == dev_name
    
    # 3. Verify index rebuild
    index = json.loads((data_dir / "_index.json").read_text())
    assert index["count"] == 1
    assert index["entries"][0]["usi_inv_id"] == f"{portal}_{item_id}"

def test_e2e_batch_ingest_with_preexisting_developer(test_env):
    """Tests that ingestion correctly links to an existing developer by ID."""
    sync = test_env["sync"]
    dm = test_env["dm"]
    data_dir = test_env["data_dir"]
    dev_dir = test_env["dev_dir"]
    
    # 1. Seed a developer
    dev_slug = "dasta-invest"
    usi_dev_id = "DEV-41897"
    portal = "oto"
    vendor_id = "11836422"
    
    dev_data = {
        "usi_dev_id": usi_dev_id,
        "developer_slug": dev_slug,
        "name": "Dasta Invest",
        "portal_mapping": {
            "oto": {"agency_id": vendor_id}
        }
    }
    # Create physical file and index it
    dm.create_developer_file(dev_data)
    dm.indexer.invalidate_identifiers_cache()
    
    # 2. Mock discovery item
    item_id = "NEW_INV_1"
    discovery_items = [{
        "id": item_id,
        "vendor_id": vendor_id,
        "name": "New Project"
    }]
    
    raw_payload = {"id": item_id, "agency": {"id": int(vendor_id)}}
    sync.gateway.process_batch = MagicMock(return_value=[raw_payload])
    
    with patch("usi_scrapers.mapping.transform_to_unified") as mock_transform:
        mock_transform.return_value = {
            "id": item_id,
            "name": "New Project",
            "developer_name": "Dasta Invest",
            "vendor_id": vendor_id
        }
        
        # ACT
        sync.process_batch(portal, discovery_items)
        
    # ASSERTIONS
    # Verify the investment ended up in the correct developer folder
    expected_path = data_dir / dev_slug / "new-project"
    assert (expected_path / f"usi_{portal}_{item_id}.json").exists()
    
    # Verify the usi file has the correct usi_dev_id
    usi_data = json.loads((expected_path / f"usi_{portal}_{item_id}.json").read_text())
    assert usi_data["usi_dev_id"] == usi_dev_id

def test_e2e_schema_fallback_handling(test_env):
    """Tests that the pipeline handles deep-nested Otodom developer IDs."""
    sync = test_env["sync"]
    data_dir = test_env["data_dir"]
    
    portal = "oto"
    item_id = "4BFOJ"
    vendor_id = "11836422" # Nested one
    
    # Mock discovery item
    discovery_items = [{
        "id": item_id,
        "url": f"https://www.otodom.pl/pl/oferta/id{item_id}"
    }]
    
    # Mock Gateway batch results with NEW NESTED SCHEMA
    raw_payload = {
        "props": {
            "pageProps": {
                "ad": {
                    "agency": {"id": int(vendor_id), "name": "Dasta"}
                }
            }
        }
    }
    sync.gateway.process_batch = MagicMock(return_value=[raw_payload])
    sync.gateway.load_raw = MagicMock(return_value=raw_payload)
    
    # Mock transform_to_unified to FAIL extracting developer_id (mimicking a mapping gap)
    with patch("usi_scrapers.mapping.transform_to_unified") as mock_transform:
        mock_transform.return_value = {
            "id": item_id,
            "name": "Nested Test",
            "developer_id": None # MAPPING GAP
        }
        
        # ACT
        sync.process_batch(portal, discovery_items)
        
    # ASSERTIONS
    # Search for the created usi_*.json file
    usi_files = list(data_dir.rglob(f"usi_{portal}_{item_id}.json"))
    assert len(usi_files) == 1
    
    # Verify it correctly used the fallback extracted ID
    data = json.loads(usi_files[0].read_text())
    # Should have been registered in 'oto-11836422' folder (fallback dev slug)
    assert "oto-11836422" in str(usi_files[0])
