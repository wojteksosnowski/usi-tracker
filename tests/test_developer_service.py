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
    
    # Create a Level 2 file
    dev_file = dev_subdir / f"usi_dev_DEV-00001_{dev_slug}.json"
    initial_data = {
        "usi_dev_id": "DEV-00001",
        "developer_slug": dev_slug,
        "name": "Test Developer",
        "crawler": {"old": "data"}
    }
    dev_file.write_text(json.dumps(initial_data))
    
    # Record maintenance
    dev_svc.record_maintenance(dev_slug, success=True)
    
    # Verify file content
    updated_data = json.loads(dev_file.read_text())
    assert "last_maintenance" in updated_data
    assert updated_data["maintenance_success"] is True
    # Ensure crawler dict wasn't used for new data
    assert "last_maintenance" not in updated_data.get("crawler", {})

def test_get_maintenance_overdue_score_reads_flattened(dev_svc):
    dev_data = {
        "developer_slug": "test-dev",
        "last_maintenance": "2020-01-01T12:00:00Z"
    }
    
    score = dev_svc.get_maintenance_overdue_score(dev_data)
    # 2020 is definitely overdue (> 90 days), so score should be high
    assert score > 100
