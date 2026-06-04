import pytest
from unittest.mock import patch, MagicMock
from python_worker.adapters import AdapterFactory, RPAdapter, OtodomAdapter, TOAdapter

def test_adapter_factory():
    """Verify that AdapterFactory returns correct classes for portal aliases."""
    assert AdapterFactory.get_adapter("rp") == RPAdapter
    assert AdapterFactory.get_adapter("otodom") == OtodomAdapter
    assert AdapterFactory.get_adapter("oto") == OtodomAdapter
    assert AdapterFactory.get_adapter("tabelaofert") == TOAdapter
    assert AdapterFactory.get_adapter("to") == TOAdapter

def test_rp_adapter_unified_transform():
    """Verify RPAdapter basic transformation using library mapping."""
    raw_details = {
        "id": "12345",
        "name": "Zielone Tarasy",
        "developer": {"name": "Budimex", "slug": "budimex-nieruchomosci"},
        "slug": "zielone-tarasy",
        "location": {"latitude": 52.2, "longitude": 21.0},
        "properties": 100
    }
    
    # We mock the library mapping output to ensure deterministic test without depending 
    # on the current state of portal_data_mapping.json in the external library.
    with patch("usi_scrapers.mapping.transform_to_unified") as mock_transform:
        mock_transform.return_value = {
            "name": "Zielone Tarasy (Unified)",
            "developer_name": "Budimex (Unified)",
            "latitude": 52.22,
            "longitude": 21.11,
            "address": "ul. Testowa 1",
            "city": "Warszawa",
            "id": "12345",
            "url": "https://rp.pl/inv-123",
            "units_count": 100,
            "delivery_date": "2025-12-31"
        }
        
        result = RPAdapter.transform({"raw_details": raw_details}, "zielone-tarasy", "budimex")
        
        assert result["name"] == "Zielone Tarasy (Unified)"
        assert result["developer"] == "Budimex (Unified)"
        assert result["investment_slug"] == "zielone-tarasy"
        assert result["developer_slug"] == "budimex"
        assert result["location"]["coords"] == [52.22, 21.11]
        assert result["specifications"]["units_count"] == 100
        assert result["sources"]["rp"]["id"] == "12345"

def test_otodom_adapter_unified_transform():
    """Verify OtodomAdapter basic transformation."""
    with patch("usi_scrapers.mapping.transform_to_unified") as mock_transform:
        mock_transform.return_value = {
            "name": "Oto Investment",
            "developer_name": "Oto Developer",
            "latitude": 50.0,
            "longitude": 19.0,
            "id": "oto-123",
            "delivery_date": "2024-Q4"
        }
        
        result = OtodomAdapter.transform({"raw_details": {}}, "oto-inv", "oto-dev")
        
        assert result["name"] == "Oto Investment"
        assert result["specifications"]["delivery_date"] == "2024-Q4"
        assert result["sources"]["oto"]["id"] == "oto-123"

def test_to_adapter_unified_transform():
    """Verify TOAdapter basic transformation."""
    with patch("usi_scrapers.mapping.transform_to_unified") as mock_transform:
        mock_transform.return_value = {
            "name": "TO Investment",
            "developer_name": "TO Developer",
            "id": "to-456",
            "price_min": 500000
        }
        
        result = TOAdapter.transform({"raw_details": {}}, "to-inv", "to-dev")
        
        assert result["name"] == "TO Investment"
        assert result["financials"]["price_min"] == 500000
        assert result["sources"]["to"]["id"] == "to-456"
