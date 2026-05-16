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

def test_detect_similar_name_match(tmp_path, monkeypatch):
    data_dir = tmp_path / "USIdata"
    dev_dir = tmp_path / "USIdev"
    data_dir.mkdir()
    dev_dir.mkdir()

    monkeypatch.setattr("python_worker.detect_similar_devs.USI_DATA_DIR", data_dir)
    monkeypatch.setattr("python_worker.detect_similar_devs.USI_DEV_DIR", dev_dir)

    dev1 = {"usi_dev_id": "DEV-001", "developer_slug": "dev-1", "name": "Budimex"}
    dev2 = {"usi_dev_id": "DEV-002", "developer_slug": "dev-2", "name": "Budimex Sp. z o.o."}

    for d in [dev1, dev2]:
        subdir = dev_dir / d["developer_slug"]
        subdir.mkdir()
        with open(subdir / f"usi_dev_{d['developer_slug']}.json", "w") as f:
            json.dump(d, f)

    detect_similar()

    from python_worker.developer_manager import DeveloperManager as DM2
    dm2 = DM2(data_dir, dev_dir)
    d1 = dm2.get_developer("dev-1")
    slugs = [s["developer_slug"] for s in d1.get("suggestions", [])]
    assert "dev-2" in slugs
