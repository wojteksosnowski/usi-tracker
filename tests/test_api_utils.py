import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from python_worker.api.utils import (
    _valid_slug, _valid_filename, _calculate_ocena_log, 
    _calculate_distance, _find_inv_file, _load_investment
)

def test_valid_slug():
    assert _valid_slug("valid-slug_123") is True
    assert _valid_slug("invalid slug!") is False
    assert _valid_slug("") is False

def test_calculate_ocena_log():
    # Example scores
    ratings = {"Balkony": 5, "Fasady": 4}
    score = _calculate_ocena_log(ratings)
    assert score is not None
    assert score > 0

def test_calculate_distance():
    # Warsaw vs Krakow approx distance
    dist = _calculate_distance(52.2297, 21.0122, 50.0647, 19.9450)
    assert 240 < dist < 260

@pytest.fixture
def temp_inv_dir(tmp_path):
    dev_dir = tmp_path / "test-dev"
    inv_dir = dev_dir / "test-inv"
    inv_dir.mkdir(parents=True)
    
    # Create some mock JSONs
    (inv_dir / "usi_rp_123.json").write_text('{"name": "Test RP", "usi_inv_id": "rp_123", "image_paths": []}')
    (inv_dir / "usi_oto_456.json").write_text('{"name": "Test OTO", "usi_inv_id": "oto_456"}')
    
    return tmp_path, dev_dir, inv_dir

def test_find_inv_file(temp_inv_dir):
    data_dir, dev_dir, inv_dir = temp_inv_dir
    
    # Test system ID
    path = _find_inv_file(inv_dir, "test-inv", system_id="rp_123")
    assert path.name == "usi_rp_123.json"
    
    # Test fallback
    path2 = _find_inv_file(inv_dir, "test-inv", system_id="oto_456")
    assert path2.name == "usi_oto_456.json"

@patch("python_worker.services.investment_service.InvestmentService.get_investment_resources")
def test_load_investment_with_system_id(mock_get_resources, temp_inv_dir):
    data_dir, dev_dir, inv_dir = temp_inv_dir
    
    # The Identity Resolver returns correct data overriding the wrong slugs
    mock_get_resources.return_value = {
        "files": {"anchor": inv_dir / "usi_rp_123.json"},
        "metadata": {"slug": "test-dev/test-inv"},
        "base_dir": inv_dir,
        "images_dir": inv_dir,
        "id": "rp_123"
    }
    
    # We pass WRONG slugs, but correct system_id
    result = _load_investment(
        "wrong-dev", "wrong-inv", 
        data_dir=data_dir, 
        public_usi_dir=data_dir, 
        system_id="rp_123"
    )
    
    assert result is not None
    assert result["developer_slug"] == "test-dev"
    assert result["investment_slug"] == "test-inv"
    assert result["name"] == "Test RP"
    assert result["id"] == "rp_123"
