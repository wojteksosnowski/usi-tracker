import pytest
import json
from pathlib import Path
from python_worker.detect_similar_devs import normalize_name, haversine, detect_similar

def test_normalize_name():
    assert normalize_name("Budimex Nieruchomości Sp. z o.o.") == "budimex"
    assert normalize_name("Echo Investment S.A.") == "echo"
    assert normalize_name("Atal S.A.") == "atal"
    assert normalize_name("J.W. Construction Holding S.A.") == "jw construction"

def test_haversine():
    # Warsaw center to somewhere 50m away
    lat1, lon1 = 52.2297, 21.0122
    lat2, lon2 = 52.2297, 21.0129 # roughly 47m east
    dist = haversine(lat1, lon1, lat2, lon2)
    assert 45 < dist < 50

def test_detect_similar_logic(tmp_path, monkeypatch):
    data_dir = tmp_path / "USIdata"
    dev_dir = tmp_path / "USIdev"
    data_dir.mkdir()
    dev_dir.mkdir()
    
    # Mock config
    monkeypatch.setattr("python_worker.detect_similar_devs.USI_DATA_DIR", data_dir)
    monkeypatch.setattr("python_worker.detect_similar_devs.USI_DEV_DIR", dev_dir)
    
    # Create devs
    dev1 = {"usi_dev_id": "DEV-001", "developer_slug": "dev-1", "name": "Budimex"}
    dev2 = {"usi_dev_id": "DEV-002", "developer_slug": "dev-2", "name": "Budimex Sp. z o.o."}
    dev3 = {"usi_dev_id": "DEV-003", "developer_slug": "dev-3", "name": "Other Dev"}
    
    for d in [dev1, dev2, dev3]:
        with open(dev_dir / f"usi_dev_{d['developer_slug']}.json", "w") as f:
            json.dump(d, f)
            
    # Create investments for dev3 and dev1 that are close
    # dev1 investment
    inv1_dir = data_dir / "dev-1" / "inv-1"
    inv1_dir.mkdir(parents=True)
    with open(inv1_dir / "usi_inv-1.json", "w") as f:
        json.dump({"location": {"coords": [52.0, 21.0]}}, f)
        
    # dev3 investment (close to dev1)
    inv3_dir = data_dir / "dev-3" / "inv-3"
    inv3_dir.mkdir(parents=True)
    with open(inv3_dir / "usi_inv-3.json", "w") as f:
        json.dump({"location": {"coords": [52.0001, 21.0001]}}, f) # ~13m away
        
    detect_similar()
    
    # Check results
    with open(dev_dir / "usi_dev_dev-1.json", "r") as f:
        d1 = json.load(f)
        suggestions = d1.get("suggestions", [])
        # Should have dev-2 (name) and dev-3 (location)
        slugs = [s["developer_slug"] for s in suggestions]
        assert "dev-2" in slugs
        assert "dev-3" in slugs
        
        # Verify reasons
        reasons = [s["reason"] for s in suggestions]
        assert any("znormalizowany nazwa" in r for r in reasons)
        assert any("bliskiej lokalizacji" in r for r in reasons)
