import json
import pytest
from pathlib import Path
from python_worker.services.investment_service import InvestmentService
import python_worker.investment_index as inv_index
from unittest.mock import MagicMock

@pytest.fixture
def temp_usi_dirs(tmp_path):
    data_dir = tmp_path / "USIdata"
    public_dir = tmp_path / "USI"
    data_dir.mkdir()
    public_dir.mkdir()
    return data_dir, public_dir

def test_registration_gets_segment(temp_usi_dirs):
    data_dir, public_dir = temp_usi_dirs
    service = InvestmentService(data_dir=data_dir, public_usi_dir=public_dir)
    
    # Register new Otodom investment with 'Mieszkania' in name
    dev_slug, inv_slug = service.register_investment(
        portal="oto",
        developer_name="Dev",
        inv_slug="test-mieszkania",
        name="Mieszkania Testowe",
        item_id="123",
        url="https://otodom.pl/inwestycja/test-mieszkania"
    )
    
    # Check if segment was assigned in skeleton
    usi_file = list((data_dir / dev_slug / inv_slug).glob("usi_oto_123.json"))[0]
    data = json.loads(usi_file.read_text())
    assert data["specifications"]["segment"] == "mieszkania deweloperskie"

def test_update_does_not_overwrite_manual_segment(temp_usi_dirs, monkeypatch):
    data_dir, public_dir = temp_usi_dirs
    service = InvestmentService(data_dir=data_dir, public_usi_dir=public_dir)
    
    # 1. Manually create a USI record with a specific segment
    dev_slug, inv_slug = "dev", "inv"
    inv_dir = data_dir / dev_slug / inv_slug
    inv_dir.mkdir(parents=True)
    usi_file = inv_dir / "usi_rp_999.json"
    
    existing_data = {
        "usi_inv_id": "INV-001",
        "investment_slug": inv_slug,
        "developer_slug": dev_slug,
        "specifications": {"segment": "lokale inwestycyjne"},
        "sources": {"rp": {"id": "999", "url": "http://rp.pl/999"}},
        "audit": {"created_at": "2024-01-01T00:00:00"}
    }
    usi_file.write_text(json.dumps(existing_data))
    
    # 2. Mock scraper_api.fetch_investment and tech_manager
    import usi_scrapers.api as scraper_api
    monkeypatch.setattr(scraper_api, "fetch_investment", lambda *args, **kwargs: {"raw_details": {"type": 1}}) # RP Mieszkania
    
    service.tech_manager = MagicMock()
    service.fetcher = MagicMock()
    
    # 3. Update investment
    service.update_investment(dev_slug, inv_slug)
    
    # 4. Verify that segment was NOT overwritten
    updated_data = json.loads(usi_file.read_text())
    assert updated_data["specifications"]["segment"] == "lokale inwestycyjne"

def test_segment_in_index(temp_usi_dirs):
    data_dir, public_dir = temp_usi_dirs
    service = InvestmentService(data_dir=data_dir, public_usi_dir=public_dir)
    
    # 1. Create index
    index_path = data_dir / "_index.json"
    index_path.write_text(json.dumps({"entries": [], "count": 0}))
    
    # 2. Register investment with 'mieszkania' in name to ensure segment
    dev_slug, inv_slug = service.register_investment(
        portal="rp",
        developer_name="Dev",
        inv_slug="test-inv",
        name="Mieszkania Testowe",
        item_id="777"
    )
    
    # 3. Trigger upsert
    inv_index.upsert(data_dir, public_dir, dev_slug, inv_slug)
    
    # 4. Read index and check segment
    index_data = json.loads(index_path.read_text())
    entry = index_data["entries"][0]
    # Check in specifications (as returned by _load_investment)
    assert entry["specifications"]["segment"] == "mieszkania deweloperskie"
