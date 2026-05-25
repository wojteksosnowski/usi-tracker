import pytest
from python_worker.adapters import RPAdapter, OtodomAdapter, TOAdapter

def test_rp_segment_classification():
    # Test Mieszkania
    raw_mieszkania = {"type": 1}
    u = RPAdapter.transform(raw_mieszkania, "inv", "dev")
    assert u["specifications"]["segment"] == "mieszkania deweloperskie"

    # Test Domy
    raw_domy = {"type": 2}
    u = RPAdapter.transform(raw_domy, "inv", "dev")
    assert u["specifications"]["segment"] == "segmenty i domy"

    # Test Lokale inwestycyjne
    raw_inv = {"type": 3}
    u = RPAdapter.transform(raw_inv, "inv", "dev")
    assert u["specifications"]["segment"] == "lokale inwestycyjne"

def test_otodom_segment_classification():
    # Test Mieszkania
    raw_mieszkania = {"ad": {"target": {"Offered_estates_type": "flats"}}}
    u = OtodomAdapter.transform(raw_mieszkania, "inv", "dev")
    assert u["specifications"]["segment"] == "mieszkania deweloperskie"

    # Test Domy
    raw_domy = {"ad": {"target": {"Offered_estates_type": "houses"}}}
    u = OtodomAdapter.transform(raw_domy, "inv", "dev")
    assert u["specifications"]["segment"] == "segmenty i domy"

    # Test PRS (Rental)
    raw_prs = {"ad": {"target": {"Offered_estates_type": "flats", "Transaction": "rent"}}}
    u = OtodomAdapter.transform(raw_prs, "inv", "dev")
    assert u["specifications"]["segment"] == "prs"

def test_to_segment_classification():
    # Test Mieszkania
    raw_mieszkania = {"category_name": "Mieszkania na sprzedaż"}
    u = TOAdapter.transform(raw_mieszkania, "inv", "dev")
    assert u["specifications"]["segment"] == "mieszkania deweloperskie"

    # Test Domy
    raw_domy = {"category_name": "Domy i segmenty"}
    u = TOAdapter.transform(raw_domy, "inv", "dev")
    assert u["specifications"]["segment"] == "segmenty i domy"

    # Test Investment (URL signal)
    raw_inv = {"url": "https://tabelaofert.pl/apartamenty-inwestycyjne-warszawa"}
    u = TOAdapter.transform(raw_inv, "inv", "dev")
    assert u["specifications"]["segment"] == "lokale inwestycyjne"
