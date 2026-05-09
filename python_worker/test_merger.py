import pytest
from python_worker.adapters.merger import Merger


def _rp(slug="test-inv", dev="test-dev", **kw):
    base = {
        "investment_slug": slug, "developer_slug": dev,
        "name": "RP Investment", "sources": {"rp": {"id": "123", "url": "https://rp.pl/123"}},
        "financials": {"price_min": 400000, "price_max": 600000, "price_avg": 500000,
                       "price_m2_min": 8000, "price_m2_max": 12000},
        "specifications": {"units_count": 50, "delivery_date": "2025-Q3",
                           "delivery_quarter": "Q3", "delivery_year": 2025},
        "location": {"coords": [52.2, 21.0], "address": "ul. Testowa 1", "city": "Warszawa", "district": "Mokotów"},
        "amenities": {"labels": ["Parking"], "raw_codes": [10]},
        "image_urls": ["https://cdn.rp.pl/a.jpg"],
        "images_count": 1, "image_paths": [],
    }
    base.update(kw)
    return base


def _oto(slug="test-inv", dev="test-dev", **kw):
    base = {
        "investment_slug": slug, "developer_slug": dev,
        "name": "Oto Investment", "sources": {"oto": {"url": "https://otodom.pl/x"}},
        "financials": {}, "specifications": {}, "location": {}, "amenities": {},
        "image_urls": ["https://cdn.oto.pl/b.jpg"],
        "images_count": 1, "image_paths": [],
    }
    base.update(kw)
    return base


def _to(slug="test-inv", dev="test-dev", **kw):
    base = {
        "investment_slug": slug, "developer_slug": dev,
        "name": "TO Investment", "sources": {"to": {"url": "https://tabelaofert.pl/y"}},
        "financials": {}, "specifications": {}, "location": {}, "amenities": {},
        "image_urls": [], "images_count": 0, "image_paths": [],
    }
    base.update(kw)
    return base


# ── merge basics ─────────────────────────────────────────────────────────────

def test_merge_rp_only():
    result = Merger.merge(rp_data=_rp())
    assert result["name"] == "RP Investment"
    assert result["sources"]["rp"]["id"] == "123"
    assert result["financials"]["price_avg"] == 500000


def test_merge_oto_only():
    result = Merger.merge(oto_data=_oto())
    assert result["name"] == "Oto Investment"
    assert result["sources"]["oto"]["url"] == "https://otodom.pl/x"


def test_merge_rp_wins_over_oto():
    result = Merger.merge(rp_data=_rp(), oto_data=_oto())
    assert result["name"] == "RP Investment"
    assert "rp" in result["sources"]
    assert "oto" in result["sources"]


def test_merge_image_urls_deduplicated():
    rp = _rp(image_urls=["https://cdn.rp.pl/a.jpg", "https://cdn.rp.pl/b.jpg"])
    oto = _oto(image_urls=["https://cdn.rp.pl/a.jpg", "https://cdn.oto.pl/c.jpg"])
    result = Merger.merge(rp_data=rp, oto_data=oto)
    assert len(result["image_urls"]) == 3


def test_merge_preserves_existing_source_urls():
    existing = {
        "sources": {"rp": {"id": "123", "url": "https://rp.pl/old"}},
        "audit": {"created_at": "2024-01-01T00:00:00", "history": []},
    }
    rp = _rp()
    rp["sources"] = {"rp": {"id": "123"}}  # no url in new data
    result = Merger.merge(rp_data=rp, existing_data=existing)
    assert result["sources"]["rp"]["url"] == "https://rp.pl/old"


def test_merge_empty_returns_empty():
    assert Merger.merge() == {}


def test_merge_location_fallback_to_oto():
    rp = _rp(location={"coords": [None, None]})
    oto = _oto(location={"coords": [52.1, 21.1], "city": "Warszawa"})
    result = Merger.merge(rp_data=rp, oto_data=oto)
    assert result["location"]["coords"] == [52.1, 21.1]
    assert result["location"]["city"] == "Warszawa"


def test_merge_amenities_union():
    rp = _rp(amenities={"labels": ["Parking"], "raw_codes": [10]})
    oto = _oto(amenities={"labels": ["Ogród"], "raw_codes": [20]})
    result = Merger.merge(rp_data=rp, oto_data=oto)
    assert set(result["amenities"]["labels"]) == {"Parking", "Ogród"}
    assert set(result["amenities"]["raw_codes"]) == {10, 20}


def test_merge_existing_data_preserves_ratings():
    existing = {
        "sources": {}, "ratings": {"Balkony": 3.0, "status": "Pełna"},
        "audit": {"created_at": "2024-01-01T00:00:00", "history": []},
    }
    result = Merger.merge(rp_data=_rp(), existing_data=existing)
    assert result["ratings"]["Balkony"] == 3.0


def test_merge_meta_ratings_override_existing():
    existing = {"sources": {}, "ratings": {"Balkony": 1.0},
                "audit": {"created_at": "2024-01-01T00:00:00", "history": []}}
    result = Merger.merge(rp_data=_rp(), meta_ratings={"Balkony": 4.0}, existing_data=existing)
    assert result["ratings"]["Balkony"] == 4.0


# ── None-safety bug fix (sources key missing) ─────────────────────────────────

def test_merge_rp_data_missing_rp_key_in_sources():
    """Adapter returned rp_data but sources dict has no 'rp' key — must not crash."""
    rp = _rp()
    rp["sources"] = {}  # 'rp' key absent
    result = Merger.merge(rp_data=rp)
    assert result["sources"]["rp"] == {}


def test_merge_oto_data_missing_oto_key_in_sources():
    oto = _oto()
    oto["sources"] = {}
    result = Merger.merge(oto_data=oto)
    assert result["sources"]["oto"] == {}


def test_merge_to_data_missing_to_key_in_sources():
    to = _to()
    to["sources"] = {}
    result = Merger.merge(to_data=to)
    assert result["sources"]["to"] == {}


def test_merge_all_portals_missing_source_keys():
    rp = _rp(); rp["sources"] = {}
    oto = _oto(); oto["sources"] = {}
    to = _to(); to["sources"] = {}
    result = Merger.merge(rp_data=rp, oto_data=oto, to_data=to)
    assert result["sources"]["rp"] == {}
    assert result["sources"]["oto"] == {}
    assert result["sources"]["to"] == {}


# ── _detect_changes ───────────────────────────────────────────────────────────

def test_detect_changes_price_change():
    old = {"financials": {"price_avg": 500000}, "specifications": {}, "status": "Brak", "images_count": 0}
    new = {"financials": {"price_avg": 550000}, "specifications": {}, "status": "Brak", "images_count": 0}
    changes = Merger._detect_changes(old, new)
    assert any(c["field"] == "financials.price_avg" and c["new"] == 550000 for c in changes)


def test_detect_changes_no_change():
    data = {"financials": {"price_avg": 500000}, "specifications": {}, "status": "Brak", "images_count": 5}
    assert Merger._detect_changes(data, data) == []


def test_detect_changes_new_value_none_ignored():
    old = {"financials": {"price_avg": 500000}, "specifications": {}, "status": "Brak", "images_count": 0}
    new = {"financials": {"price_avg": None}, "specifications": {}, "status": "Brak", "images_count": 0}
    changes = Merger._detect_changes(old, new)
    assert not any(c["field"] == "financials.price_avg" for c in changes)


def test_detect_changes_status_change():
    old = {"financials": {}, "specifications": {}, "status": "Brak", "images_count": 0}
    new = {"financials": {}, "specifications": {}, "status": "Pełna", "images_count": 0}
    changes = Merger._detect_changes(old, new)
    assert any(c["field"] == "status" and c["new"] == "Pełna" for c in changes)


def test_merge_history_created_on_first_merge():
    result = Merger.merge(rp_data=_rp())
    assert result["audit"]["history"][0]["event"] == "Created"


def test_merge_history_appended_on_update():
    existing = {
        "sources": {}, "financials": {"price_avg": 400000}, "specifications": {},
        "status": "Brak", "images_count": 0,
        "audit": {"created_at": "2024-01-01T00:00:00", "history": []},
    }
    result = Merger.merge(rp_data=_rp(), existing_data=existing, event="Sync: RP")
    assert any(h["event"] == "Sync: RP" for h in result["audit"]["history"])


# ── preserve existing data when portal returns nulls ─────────────────────────

def _existing_full(slug="test-inv", dev="test-dev"):
    return {
        "investment_slug": slug, "developer_slug": dev,
        "name": "Existing", "sources": {"oto": {"url": "https://otodom.pl/x"}},
        "location": {"coords": [52.0, 21.0], "address": "ul. Testowa 1", "city": "Warszawa", "district": "Mokotów"},
        "specifications": {"units_count": 48, "delivery_date": None, "delivery_quarter": None, "delivery_year": None},
        "financials": {"price_min": 500000.0, "price_max": None, "price_avg": None},
        "amenities": {"labels": ["Balkon", "Winda"], "raw_codes": []},
        "ratings": {}, "status": "Brak",
        "usi_inv_id": "INV-0001", "usi_dev_id": "DEV-0001",
        "audit": {"created_at": "2024-01-01T00:00:00", "history": []},
    }


def test_merge_preserves_existing_address_when_portal_returns_null():
    oto = _oto(location={"coords": [52.0, 21.0], "address": None, "city": None, "district": None})
    result = Merger.merge(oto_data=oto, existing_data=_existing_full())
    assert result["location"]["address"] == "ul. Testowa 1"
    assert result["location"]["city"] == "Warszawa"
    assert result["location"]["district"] == "Mokotów"


def test_merge_preserves_existing_units_count_when_portal_returns_null():
    oto = _oto(specifications={"delivery_date": "2027-Q2", "delivery_quarter": 2,
                                "delivery_year": 2027, "units_count": None})
    result = Merger.merge(oto_data=oto, existing_data=_existing_full())
    assert result["specifications"]["units_count"] == 48
    assert result["specifications"]["delivery_date"] == "2027-Q2"


def test_merge_preserves_existing_amenity_labels_when_portal_returns_empty():
    oto = _oto(amenities={"labels": [], "raw_codes": []})
    result = Merger.merge(oto_data=oto, existing_data=_existing_full())
    assert "Balkon" in result["amenities"]["labels"]
    assert "Winda" in result["amenities"]["labels"]


def test_merge_preserves_usi_ids_from_existing():
    result = Merger.merge(oto_data=_oto(), existing_data=_existing_full())
    assert result["usi_inv_id"] == "INV-0001"
    assert result["usi_dev_id"] == "DEV-0001"


def test_merge_new_portal_amenities_union_with_existing():
    oto = _oto(amenities={"labels": ["Parking"], "raw_codes": []})
    result = Merger.merge(oto_data=oto, existing_data=_existing_full())
    assert "Parking" in result["amenities"]["labels"]
    assert "Balkon" in result["amenities"]["labels"]
