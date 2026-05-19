import json
import pytest
from python_worker.adapters import RPAdapter, AdapterFactory
from python_worker.adapters.merger import Merger

def test_rp_adapter_extraction():
    raw_data = {
        "id": "12345",
        "name": "Test Inv",
        "website": "http://test-inv.pl",
        "stats": {
            "type": "obj",
            "value": {
                "ranges_height_max": 258
            }
        },
        "geo_point": {"type": "obj", "value": {"type": "Point", "coordinates": {"type": "arr", "value": [21.0, 52.0]}}}
    }
    
    u = RPAdapter.transform(raw_data, "inv-slug", "dev-slug")
    
    assert u["website"] == "http://test-inv.pl"
    assert u["specifications"]["ceiling_height_max"] == 2.58
    assert u["sources"]["rp"]["id"] == "12345"

def test_merger_ceiling_height():
    rp_data = {
        "investment_slug": "inv",
        "developer_slug": "dev",
        "name": "Inv",
        "website": "http://rp.pl",
        "sources": {"rp": {"id": "1"}},
        "specifications": {"ceiling_height_max": 2.70}
    }
    
    merged = Merger.merge(rp_data=rp_data)
    
    assert merged["specifications"]["ceiling_height_max"] == 2.70
    assert merged["website"] == "http://rp.pl"

def test_merger_preserves_ceiling_height():
    existing = {
        "investment_slug": "inv",
        "developer_slug": "dev",
        "specifications": {"ceiling_height_max": 2.60}
    }
    new_rp = {
        "investment_slug": "inv",
        "developer_slug": "dev",
        "sources": {"rp": {"id": "1"}},
        "specifications": {"ceiling_height_max": None}
    }
    
    merged = Merger.merge(rp_data=new_rp, existing_data=existing)
    assert merged["specifications"]["ceiling_height_max"] == 2.60
