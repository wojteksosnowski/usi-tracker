import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from python_worker.main import update_investment

@pytest.fixture
def mock_usi_data(tmp_path):
    dev_dir = tmp_path / "test-dev"
    inv_dir = dev_dir / "test-inv"
    inv_dir.mkdir(parents=True)
    
    usi_file = inv_dir / "usi_test-inv.json"
    data = {
        "investment_slug": "test-inv",
        "developer_slug": "test-dev",
        "sources": {
            "rp": {"id": "123"},
            "oto": {"url": "https://otodom.pl/test"}
        }
    }
    usi_file.write_text(json.dumps(data))
    return tmp_path, dev_dir, inv_dir

@patch("python_worker.main.USI_DATA_DIR")
@patch("python_worker.main.scrape_rynek_pierwotny")
@patch("python_worker.main.scrape_otodom")
@patch("python_worker.main.RPAdapter")
@patch("python_worker.main.OtodomAdapter")
@patch("python_worker.main.Merger")
def test_update_investment_flow(mock_merger, mock_oto_adapter, mock_rp_adapter, mock_scrape_oto, mock_scrape_rp, mock_data_dir, mock_usi_data):
    tmp_path, dev_dir, inv_dir = mock_usi_data
    mock_data_dir.__truediv__.return_value = dev_dir # Simplified mock for USI_DATA_DIR / dev_slug
    # Actually, USI_DATA_DIR / dev_slug / inv_slug
    mock_data_dir.__truediv__.side_effect = lambda x: MagicMock(Path) if isinstance(x, str) else mock_data_dir
    
    # Let's use a better mock for Path
    with patch("python_worker.main.USI_DATA_DIR", tmp_path):
        mock_scrape_rp.return_value = {"raw_details": {"rp": "data"}}
        mock_scrape_oto.return_value = {"raw_details": {"oto": "data"}}
        mock_rp_adapter.transform.return_value = {"rp_uni": True}
        mock_oto_adapter.transform.return_value = {"oto_uni": True}
        mock_merger.merge.return_value = {"merged": True, "sources": {"rp": {}, "oto": {}}}
        
        success = update_investment("test-dev", "test-inv")
        
        assert success is True
        assert mock_scrape_rp.called
        assert mock_scrape_oto.called
        assert (inv_dir / "raw_rp_test-inv.json").exists()
        assert (inv_dir / "raw_oto_test-inv.json").exists()
        
        # Verify merged file saved
        with open(inv_dir / "usi_test-inv.json", "r") as f:
            saved = json.load(f)
            assert saved["merged"] is True
