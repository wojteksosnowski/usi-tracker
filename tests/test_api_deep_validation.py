import pytest
import json
import os
from pathlib import Path
from datetime import datetime
from python_worker.ui_server import app
import python_worker.investment_index as inv_index
from python_worker.developer_index import rebuild_master_index

@pytest.fixture
def test_env(tmp_path):
    """Sets up a temporary USI project structure."""
    # We use tmp_path to simulate Public/USIdata
    public_dir = tmp_path / "Public"
    usi_data = public_dir / "USIdata"
    usi_assets = public_dir / "USI"
    usi_dev = public_dir / "USIdev"
    
    for d in [usi_data, usi_assets, usi_dev]:
        d.mkdir(parents=True)
        
    # Seed sample investment
    dev_slug = "dev-test"
    inv_id = "INV-001"
    inv_dir = usi_data / dev_slug / inv_id
    inv_dir.mkdir(parents=True)
    
    anchor_file = inv_dir / f"usi_{inv_id}.json"
    anchor_data = {
        "usi_inv_id": inv_id,
        "developer_slug": dev_slug,
        "investment_slug": "test-inv",
        "name": "UniqueName Investment",
        "reviewed": False,
        "status": "Brak",
        "location": {"city": "Warszawa", "coords": [52.2297, 21.0122]},
        "sources": {"rp": {"id": "12345"}}
    }
    anchor_file.write_text(json.dumps(anchor_data, ensure_ascii=False), encoding="utf-8")
    
    # Create an image
    img_dir = usi_assets / dev_slug / inv_id
    img_dir.mkdir(parents=True)
    (img_dir / "photo.jpg").write_text("fake-image-data")
    
    return {
        "base_dir": tmp_path,
        "public_dir": public_dir,
        "usi_data": usi_data,
        "usi_dev": usi_dev,
        "inv_id": inv_id,
        "anchor_file": anchor_file,
        "dev_slug": dev_slug
    }

@pytest.fixture
def client(test_env, monkeypatch):
    """Configures the Flask client with the test environment."""
    # Monkeypatch config in all relevant places
    dirs = {
        "python_worker.config.DROPBOX_PATH": test_env["base_dir"],
        "python_worker.config.USI_DATA_DIR": test_env["usi_data"],
        "python_worker.config.PUBLIC_USI_DIR": test_env["public_dir"],
        "python_worker.config.USI_DEV_DIR": test_env["usi_dev"],
        "python_worker.api.blueprints.investments.USI_DATA_DIR": test_env["usi_data"],
        "python_worker.api.blueprints.investments.PUBLIC_USI_DIR": test_env["public_dir"],
        "python_worker.api.blueprints.investments.USI_DEV_DIR": test_env["usi_dev"],
        "python_worker.investment_index.USI_DATA_DIR": test_env["usi_data"],
        "python_worker.investment_index.PUBLIC_USI_DIR": test_env["public_dir"],
        "python_worker.db._BASE_PATH": test_env["base_dir"],
        "python_worker.db._INDEX_PATH": test_env["usi_data"] / "_index.json",
    }
    for k, v in dirs.items():
        try:
            monkeypatch.setattr(k, v)
        except (ImportError, AttributeError):
            pass
    
    # Reset and Rebuild index for the new directory
    inv_index.invalidate_cache()
    idx = inv_index.get_investment_index()
    idx.data_dir = test_env["usi_data"]
    idx.public_usi_dir = test_env["public_dir"]
    idx.index_path = idx.data_dir / "_index.json"
    idx.rebuild()
    
    # Re-assign services in the blueprint to fresh instances using test directories
    from python_worker.api.blueprints import investments
    from python_worker.developer_manager import DeveloperManager
    from python_worker.services.developer_service import DeveloperService
    
    investments.developer_manager = DeveloperManager(test_env["usi_data"], test_env["usi_dev"])
    investments.developer_service = DeveloperService(test_env["usi_data"], test_env["usi_dev"])
    
    # Also update the index references if they are used internally by services
    investments.inv_index.USI_DATA_DIR = test_env["usi_data"]
    investments.inv_index.PUBLIC_USI_DIR = test_env["public_dir"]
    
    # Debug: Check if index was built correctly
    entry = inv_index.get_entry_by_id(test_env["inv_id"])
    print(f"DEBUG: Index Entry for {test_env['inv_id']}: {entry}")
    
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_brutal_review_persistence_and_ram_sync(client, test_env):
    """
    Verifies that marking an investment as reviewed:
    1. Updates the file on disk.
    2. Updates the RAM index immediately.
    3. The list API returns the updated state.
    """
    inv_id = test_env["inv_id"]
    anchor_file = test_env["anchor_file"]
    
    # 1. Verify initial state on disk
    initial_data = json.loads(anchor_file.read_text())
    assert initial_data["reviewed"] is False
    
    # 2. Call the API
    response = client.post(f"/api/investment/{inv_id}/review")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    
    # 3. Verify disk persistence
    updated_disk_data = json.loads(anchor_file.read_text())
    assert updated_disk_data["reviewed"] is True
    
    # 4. Verify RAM sync (hot index)
    entry = inv_index.get_entry_by_id(inv_id)
    assert entry["reviewed"] is True
    
    # 5. Verify List API response
    list_response = client.get("/api/investments")
    data = list_response.get_json()["data"]
    inv_in_list = next(i for i in data if i["usi_inv_id"] == inv_id)
    assert inv_in_list["reviewed"] is True

def test_brutal_report_append_persistence(client, test_env):
    """Verifies that adding reports appends them correctly to the disk file."""
    inv_id = test_env["inv_id"]
    anchor_file = test_env["anchor_file"]
    
    # Add first report
    resp1 = client.post(f"/api/investment/{inv_id}/add-report", json={"note": "First note"})
    assert resp1.status_code == 200, f"First report failed: {resp1.get_json()}"
    
    # Add second report
    resp2 = client.post(f"/api/investment/{inv_id}/add-report", json={"note": "Second note"})
    assert resp2.status_code == 200, f"Second report failed: {resp2.get_json()}"
    
    # Verify disk
    data = json.loads(anchor_file.read_text())
    reports = data.get("issue_reports", [])
    print(f"DEBUG: Reports on disk: {reports}")
    assert len(reports) == 2
    # issue_reports prepends (insert(0, ...)), so the second one should be at index 0
    assert reports[0]["note"] == "Second note"
    assert reports[1]["note"] == "First note"
    assert "at" in reports[0]

def test_image_serving_o1_and_placeholder(client, test_env):
    """Verifies O(1) image serving and fallback placeholder logic."""
    inv_id = test_env["inv_id"]
    dev_slug = test_env["dev_slug"]
    
    # 1. Valid image (Path relative to PUBLIC_USI_DIR)
    rel_path = f"USI/{dev_slug}/{inv_id}/photo.jpg"
    response = client.get(f"/api/image/{rel_path}")
    assert response.status_code == 200
    assert b"fake-image-data" in response.data
    assert "Cache-Control" in response.headers
    
    # 2. Invalid image -> Placeholder
    response = client.get("/api/image/invalid/path.jpg")
    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"

def test_filtering_logic_deep(client, test_env):
    """Verifies complex filtering logic combinations."""
    # Add another investment in a different city
    usi_data = test_env["usi_data"]
    dev_slug = test_env["dev_slug"]
    inv_id_2 = "INV-002"
    inv_dir_2 = usi_data / dev_slug / inv_id_2
    inv_dir_2.mkdir(parents=True)
    (inv_dir_2 / f"usi_{inv_id_2}.json").write_text(json.dumps({
        "usi_inv_id": inv_id_2,
        "developer_slug": dev_slug,
        "investment_slug": "inv-krakow",
        "name": "Krakow Residence",
        "reviewed": False,
        "location": {"city": "Kraków"}
    }, ensure_ascii=False), encoding="utf-8")
    
    # Rebuild index to include the new one
    inv_index.get_investment_index().rebuild()
    
    # Log current index state
    all_invs = inv_index.get_index()
    for i in all_invs:
        print(f"DEBUG: Inv {i['usi_inv_id']} city: {repr(i.get('city'))}")
    
    # 1. Filter by city
    resp = client.get("/api/investments?cities=kraków")
    data = resp.get_json()["data"]
    print(f"DEBUG: Filtered by 'kraków' result count: {len(data)}")
    assert len(data) == 1
    assert data[0]["usi_inv_id"] == inv_id_2
    
    # 2. Search
    resp = client.get("/api/investments?search=UniqueName")
    data = resp.get_json()["data"]
    print(f"DEBUG: Search 'UniqueName' result count: {len(data)}")
    assert len(data) == 1
    assert data[0]["usi_inv_id"] == test_env["inv_id"]

def test_ratings_persistence(client, test_env):
    """Verifies ratings and status persistence."""
    inv_id = test_env["inv_id"]
    anchor_file = test_env["anchor_file"]
    
    payload = {
        "ratings": {"Balkony": 4, "Fasady": 5},
        "status": "Pełna"
    }
    
    client.post(f"/api/investment/{inv_id}/ratings", json=payload)
    
    # Verify disk
    data = json.loads(anchor_file.read_text())
    assert data["ratings"]["Balkony"] == 4
    assert data["status"] == "Pełna"
    
    # Verify RAM
    entry = inv_index.get_entry_by_id(inv_id)
    assert entry["status"] == "Pełna"

def test_developer_detail_enriched(client, test_env):
    """Verifies that developer detail API returns aggregated data correctly."""
    dev_slug = test_env["dev_slug"]
    inv_id = test_env["inv_id"]
    
    # We need a developer profile
    usi_dev_id = "DEV-001"
    dev_dir = test_env["usi_dev"] / dev_slug
    dev_dir.mkdir(parents=True, exist_ok=True)
    
    dev_file = dev_dir / f"usi_dev_{usi_dev_id}_{dev_slug}.json"
    dev_data = {
        "usi_dev_id": usi_dev_id,
        "developer_slug": dev_slug,
        "name": "Test Developer",
        "portal_mapping": {"rp": {"id": "123"}}
    }
    dev_file.write_text(json.dumps(dev_data))
    
    # Update investment anchor to link to this developer
    anchor_data = json.loads(test_env["anchor_file"].read_text())
    anchor_data["usi_dev_id"] = usi_dev_id
    test_env["anchor_file"].write_text(json.dumps(anchor_data))
    
    # Rebuild indexes
    inv_index.get_investment_index().rebuild()
    rebuild_master_index(test_env["usi_dev"])
    
    # Call API
    response = client.get(f"/api/developer/{usi_dev_id}")
    assert response.status_code == 200
    data = response.get_json()
    
    assert data["usi_dev_id"] == usi_dev_id
    assert "investments" in data
    assert len(data["investments"]) >= 1
    assert data["investments"][0]["usi_inv_id"] == inv_id
    assert "maintenance_overdue_score" in data
