import pytest
import traceback
import json
from pathlib import Path
from unittest.mock import patch
import python_worker.investment_index as inv_index

def _make_inv_dir(tmp_path, dev="dev", inv="inv", usi_inv_id="inv_123"):
    inv_dir = tmp_path / dev / inv
    inv_dir.mkdir(parents=True, exist_ok=True)
    (inv_dir / f"usi_{inv}.json").write_text(json.dumps({
        "usi_inv_id": usi_inv_id,
        "investment_slug": inv,
        "developer_slug": dev,
        "name": "Test Investment",
        "location": {"coords": [54.0, 18.0]},
        "specifications": {"units_count": 0, "delivery_date": "—"},
        "financials": {"price_avg": 0},
        "amenities": {"labels": [], "raw_codes": []},
        "ratings": {},
        "status": "Brak"
    }))
    return inv_dir

def test_debug():
    import tempfile
    tmp_path = Path(tempfile.mkdtemp())
    data_dir = tmp_path / "USIdata"
    public_dir = tmp_path / "USI"
    data_dir.mkdir()
    public_dir.mkdir()
    
    inv_index._index_cache = None
    inv_index._index_cache_mtime = 0
    
    _make_inv_dir(data_dir, usi_inv_id="inv_123")
    
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.services.investment_service import InvestmentService
        svc = InvestmentService(data_dir=data_dir, public_usi_dir=public_dir)
        
        old_map = svc.editor.identity._map_resources_from_entry
        def _map_resources_from_entry(entry):
            print("ENTRY:", entry)
            try:
                res = old_map(entry)
                print("MAP RESULT:", res)
                return res
            except Exception as e:
                print("CRASH IN MAP!")
                traceback.print_exc()
                raise e
        svc.editor.identity._map_resources_from_entry = _map_resources_from_entry
        
        resources = svc.editor.identity.get_investment_resources("inv_123")
        print("RESOURCES:", resources)

if __name__ == "__main__":
    test_debug()
