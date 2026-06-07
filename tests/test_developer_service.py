import json
import pytest
from pathlib import Path
from python_worker.services.developer_service import DeveloperService

@pytest.fixture
def dev_svc(tmp_path):
    data_dir = tmp_path / "Public" / "USIdata"
    dev_dir = tmp_path / "Public" / "USIdev"
    data_dir.mkdir(parents=True)
    dev_dir.mkdir(parents=True)
    return DeveloperService(data_dir, dev_dir)

def test_record_maintenance_flattens_data(dev_svc, tmp_path):
    dev_slug = "test-dev"
    dev_subdir = dev_svc.dev_dir / dev_slug
    dev_subdir.mkdir()
    
    # Create a Level 2 file (Old format, but ID-Only rebuilder/manager will rename it)
    dev_file = dev_subdir / f"usi_dev_DEV-00001_{dev_slug}.json"
    initial_data = {
        "usi_dev_id": "DEV-00001",
        "developer_slug": dev_slug,
        "name": "Test Developer"
    }
    dev_file.write_text(json.dumps(initial_data))
    
    # Record maintenance
    dev_svc.record_maintenance(dev_slug, success=True)
    
    # Verify file content
    # With new naming, it should be usi_dev_unknown_unknown.json because initial_data had no portal mapping
    updated_file = dev_subdir / "usi_dev_unknown_unknown.json"
    assert updated_file.exists()
    
    updated_data = json.loads(updated_file.read_text())
    assert "last_maintenance" in updated_data
    assert updated_data["maintenance_success"] is True

def test_get_maintenance_overdue_score_reads_flattened(dev_svc):
    dev_data = {
        "developer_slug": "test-dev",
        "last_maintenance": "2020-01-01T12:00:00Z"
    }
    
    score = dev_svc.get_maintenance_overdue_score(dev_data)
    # 2020 is definitely overdue (> 90 days), so score should be high
    assert score > 100

def test_get_maintenance_overdue_score_id_only(dev_svc):
    dev_slug = "test-dev"
    dev_subdir = dev_svc.dev_dir / dev_slug
    dev_subdir.mkdir()
    
    dev_data = {
        "developer_slug": dev_slug,
        "portal_mapping": {
            "rp": {"id": "12345"},
            "oto": {"agency_id": "67890"}
        },
        "logo": "some-logo.png" # No logo penalty
    }
    
    # CASE 1: Both raw files missing
    score = dev_svc.get_maintenance_overdue_score(dev_data)
    assert score >= 1000 # 500 for RP missing + 500 for OTO missing
    
    # CASE 2: RP file exists (ID based)
    (dev_subdir / "raw_rp_12345.json").write_text("{}")
    score = dev_svc.get_maintenance_overdue_score(dev_data)
    assert 500 <= score < 1000 # only OTO missing
    
    # CASE 3: Both exist
    (dev_subdir / "raw_oto_67890.json").write_text("{}")
    score = dev_svc.get_maintenance_overdue_score(dev_data)
    assert score < 500 # no missing raw files penalty
