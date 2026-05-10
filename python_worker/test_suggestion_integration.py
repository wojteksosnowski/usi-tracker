import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from python_worker.ui_server import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

@pytest.fixture
def mock_dirs(tmp_path):
    data_dir = tmp_path / "USIdata"
    dev_dir = tmp_path / "USIdev"
    data_dir.mkdir()
    dev_dir.mkdir()
    return data_dir, dev_dir

def test_api_pending_summary(client, mock_dirs):
    data_dir, dev_dir = mock_dirs
    # Setup 1 pending
    (dev_dir / "usi_dev_test.json").write_text(json.dumps({
        "developer_slug": "test", "name": "Test", "usi_dev_id": "DEV-1"
    }))
    (dev_dir / "test").mkdir()
    (dev_dir / "test" / "discovery.json").write_text(json.dumps({
        "items": [{"portal": "rp", "id": "1", "slug": "inv-1"}]
    }))

    # reports.py imports at top level
    with patch("python_worker.api.blueprints.reports.USI_DATA_DIR", data_dir), \
         patch("python_worker.api.blueprints.reports.USI_DEV_DIR", dev_dir), \
         patch("python_worker.config.USI_DATA_DIR", data_dir), \
         patch("python_worker.config.USI_DEV_DIR", dev_dir), \
         patch("python_worker.developer_manager.DeveloperManager.get_existing_identifiers", return_value={}):
        
        resp = client.get("/api/reports/pending-summary")
        assert resp.status_code == 200
        assert resp.get_json()["total_pending"] == 1

def test_api_trigger_suggestions(client):
    with patch("python_worker.detect_similar_devs.detect_similar") as mock_detect:
        resp = client.post("/api/developer/suggest")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        assert mock_detect.called

def test_api_developers_enrichment(client, mock_dirs):
    data_dir, dev_dir = mock_dirs
    # Setup dev with 1 pending and 2 new_since_review
    (dev_dir / "usi_dev_test.json").write_text(json.dumps({
        "developer_slug": "test", "name": "Test", "usi_dev_id": "DEV-1",
        "crawler": {"new_since_review": 2}
    }))
    (dev_dir / "test").mkdir()
    (dev_dir / "test" / "discovery.json").write_text(json.dumps({
        "items": [{"portal": "rp", "id": "1", "slug": "inv-1"}]
    }))

    # investments.py imports locally, but we patch config just in case
    with patch("python_worker.config.USI_DATA_DIR", data_dir), \
         patch("python_worker.config.USI_DEV_DIR", dev_dir), \
         patch("python_worker.developer_manager.DeveloperManager.get_existing_identifiers", return_value={}):
        
        resp = client.get("/api/developers")
        assert resp.status_code == 200
        data = resp.get_json()
        test_dev = next(d for d in data if d["developer_slug"] == "test")
        assert test_dev["unregistered_count"] == 1
        assert test_dev["new_since_review"] == 2

def test_api_developer_detail_enrichment(client, mock_dirs):
    data_dir, dev_dir = mock_dirs
    # Target dev
    (dev_dir / "usi_dev_target.json").write_text(json.dumps({
        "developer_slug": "target", "name": "Target", "usi_dev_id": "DEV-T",
        "suggestions": [{"usi_dev_id": "DEV-S", "developer_slug": "suggested", "reason": "test"}]
    }))
    # Suggested dev (for enrichment)
    (dev_dir / "usi_dev_suggested.json").write_text(json.dumps({
        "developer_slug": "suggested", "name": "Suggested Dev", "usi_dev_id": "DEV-S",
        "website": "http://suggested.com"
    }))
    
    # Suggested dev has 1 investment folder
    (data_dir / "suggested").mkdir()
    (data_dir / "suggested" / "inv-s").mkdir()
    (data_dir / "suggested" / "inv-s" / "usi_inv-s.json").write_text(json.dumps({"name": "Inv S"}))

    with patch("python_worker.config.USI_DATA_DIR", data_dir), \
         patch("python_worker.config.USI_DEV_DIR", dev_dir), \
         patch("python_worker.developer_manager.DeveloperManager.get_existing_identifiers", return_value={}):
        
        resp = client.get("/api/developer/target")
        assert resp.status_code == 200
        data = resp.get_json()
        s = data["suggestions"][0]
        assert s["name"] == "Suggested Dev"
        assert s["website"] == "http://suggested.com"
        assert s["investments_count"] == 1
