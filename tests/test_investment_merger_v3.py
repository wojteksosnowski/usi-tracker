import json
import pytest
from pathlib import Path
from python_worker.investment_merger import InvestmentMerger

def test_merger_aggregation(tmp_path):
    """Test unitowy logiki agregacji (T3)."""
    # Create required sub-dirs
    (tmp_path / "USIdata").mkdir()
    
    merger = InvestmentMerger(data_dir=tmp_path, public_dir=tmp_path)
    anchors = [
        {"usi_inv_id": "INV-001", "portal": "oto", "portal_id": "123"},
        {"usi_inv_id": "INV-001", "portal": "rp", "portal_id": "456"}
    ]
    
    master = merger.aggregate_data(anchors)
    
    assert master["master_id"] == "MASTER-INV-001"
    assert len(master["merged_from"]) == 2
    assert "oto" in master["portals"]
    assert "rp" in master["portals"]

def test_sync_master_dry_run(tmp_path):
    """Test zapisu metody sync_master na dysk."""
    (tmp_path / "USIdata").mkdir()
    merger = InvestmentMerger(data_dir=tmp_path, public_dir=tmp_path)
    
    anchors = [{"usi_inv_id": "INV-002", "portal": "oto", "portal_id": "789"}]
    merger.sync_master("INV-002", anchors)
    
    # Check if Master file was created
    expected_master_path = tmp_path / "USIdata" / "inv_master_MASTER-INV-002.json"
    assert expected_master_path.exists()
    
    master_data = json.loads(expected_master_path.read_text())
    assert master_data["usi_inv_id"] == "INV-002"
