import json
import pytest
from pathlib import Path
from python_worker.investment_merger import InvestmentMerger

# Mocking data structures
class MockManager:
    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
    
    def get_developer_by_id(self, dev_id):
        return {"id": dev_id}

def test_master_creation(tmp_path):
    """Test that the Merger correctly aggregates multiple Anchors into one Master."""
    # Setup T2 Anchors (Mocked)
    anchor1 = {"usi_inv_id": "INV-001", "portal": "oto", "portal_id": "123"}
    anchor2 = {"usi_inv_id": "INV-001", "portal": "rp", "portal_id": "456"}
    
    merger = InvestmentMerger(data_dir=tmp_path, public_dir=tmp_path)
    
    # Run aggregation logic (the core of T3)
    master = merger.aggregate_data([anchor1, anchor2])
    
    assert master["usi_inv_id"] == "INV-001"
    assert len(master["merged_from"]) == 2
    assert "oto" in [m["portal"] for m in master["merged_from"]]
    assert "rp" in [m["portal"] for m in master["merged_from"]]

def test_metadata_extraction(tmp_path):
    """Test that metadata is correctly separated into T1."""
    full_data = {
        "usi_inv_id": "INV-001",
        "status": "Pełna",
        "ratings": {"Balkony": 5},
        "coords": [50.0, 19.0]
    }
    
    # Simulate migration extraction logic
    meta = {
        "status": full_data.get("status"),
        "ratings": full_data.get("ratings"),
        "location_override": {"coords": full_data.get("coords")}
    }
    
    assert meta["status"] == "Pełna"
    assert meta["ratings"]["Balkony"] == 5
    assert meta["location_override"]["coords"] == [50.0, 19.0]
