import pytest
from python_worker.portal_matcher import (
    normalize_name,
    haversine_m,
    find_matches,
    _parse_rp_delivery,
    _parse_oto_delivery,
    _quarters_apart,
)

# ─── normalize_name ──────────────────────────────────────────────────────────

def test_normalize_removes_etap_number():
    assert normalize_name("Nowe Kolibki etap 4") == "nowe kolibki"


def test_normalize_removes_etap_roman():
    assert normalize_name("Rezydencja Świerkowa etap II") == "rezydencja swierkowa"


def test_normalize_removes_faza():
    assert normalize_name("Osiedle Zenit faza 2") == "osiedle zenit"


def test_normalize_empty():
    assert normalize_name("") == ""
    assert normalize_name(None) == ""


def test_normalize_no_stage():
    assert normalize_name("Apartamenty Jasińskiego") == "apartamenty jasinskiego"


# ─── haversine_m ─────────────────────────────────────────────────────────────

def test_haversine_zero():
    assert haversine_m(54.5, 18.5, 54.5, 18.5) == pytest.approx(0.0, abs=0.1)


def test_haversine_known_gdynia():
    # Two points ~38m apart in Gdynia (roughly)
    lat1, lon1 = 54.5189, 18.5312
    lat2, lon2 = 54.5192, 18.5312  # ~33m north
    dist = haversine_m(lat1, lon1, lat2, lon2)
    assert 25 < dist < 45


def test_haversine_far():
    # Warsaw to Gdańsk ~300km
    dist = haversine_m(52.23, 21.01, 54.35, 18.64)
    assert dist > 200_000


# ─── delivery date parsing ────────────────────────────────────────────────────

def test_parse_rp_delivery_q4():
    result = {"construction_date_upper": "2027-12-31"}
    assert _parse_rp_delivery(result) == (2027, 4)


def test_parse_rp_delivery_q1():
    result = {"construction_date_upper": "2026-03-31"}
    assert _parse_rp_delivery(result) == (2026, 1)


def test_parse_rp_delivery_none():
    assert _parse_rp_delivery({}) is None
    assert _parse_rp_delivery({"construction_date_upper": None}) is None


def test_parse_oto_delivery():
    result = {"delivery_quarter": 4, "delivery_year": 2027}
    assert _parse_oto_delivery(result) == (2027, 4)


def test_parse_oto_delivery_none():
    assert _parse_oto_delivery({}) is None


def test_quarters_apart_same():
    assert _quarters_apart((2027, 4), (2027, 4)) == 0


def test_quarters_apart_two():
    assert _quarters_apart((2027, 2), (2027, 4)) == 2


def test_quarters_apart_year_boundary():
    assert _quarters_apart((2026, 4), (2027, 2)) == 2


# ─── find_matches ─────────────────────────────────────────────────────────────

def _rp(lat, lon, dev="deweloper-abc", name="Osiedle Testowe", props=100,
        delivery_upper="2027-12-31", offer_id="100"):
    return {
        "source": "rynekpierwotny.pl",
        "id": offer_id,
        "_folder": f"{dev}/osiedle-testowe",
        "developer_slug": dev,
        "name": name,
        "latitude": lat,
        "longitude": lon,
        "properties_count": props,
        "construction_date_upper": delivery_upper,
    }


def _oto(lat, lon, dev="deweloper-abc", title="Osiedle Testowe",
         delivery_q=4, delivery_y=2027):
    return {
        "source": "otodom.pl",
        "_folder": f"{dev}/osiedle-testowe-IDXXX",
        "developer_slug": dev,
        "title": title,
        "latitude": lat,
        "longitude": lon,
        "delivery_quarter": delivery_q,
        "delivery_year": delivery_y,
    }


def test_exact_match_coords_under_50m():
    results = [
        _rp(54.519, 18.531),
        _oto(54.5192, 18.5311),  # ~25m away
    ]
    suggestions = find_matches(results)
    assert suggestions
    assert suggestions[0].confidence == "exact"


def test_high_match_with_name():
    results = [
        _rp(54.519, 18.531),
        _oto(54.5193, 18.5315),  # ~35m
    ]
    suggestions = find_matches(results)
    assert suggestions
    assert suggestions[0].confidence in ("exact", "high")


def test_no_match_500m():
    results = [
        _rp(54.519, 18.531),
        _oto(54.524, 18.531),  # ~550m north
    ]
    suggestions = find_matches(results)
    assert suggestions == []


def test_medium_match_different_names():
    # ~22m, same dev, different names → at minimum medium confidence (no name match needed for medium)
    results = [
        _rp(54.519, 18.531, name="Osiedle Słoneczne etap 1"),
        _oto(54.5192, 18.5312, title="Zupełnie Inna Nazwa"),
    ]
    suggestions = find_matches(results)
    assert suggestions
    # exact or medium are both valid (close coords + same dev is enough for a suggestion)
    assert suggestions[0].confidence in ("exact", "medium")


def test_low_match_no_coords():
    results = [
        _rp(None, None, name="Apartamenty Zenit etap 2"),
        _oto(None, None, title="Apartamenty Zenit"),
    ]
    suggestions = find_matches(results)
    assert suggestions
    assert suggestions[0].confidence == "low"


def test_delivery_mismatch_downgrades_exact():
    results = [
        _rp(54.519, 18.531, delivery_upper="2024-03-31"),  # Q1 2024
        _oto(54.5192, 18.531, delivery_q=4, delivery_y=2027),  # Q4 2027 — 14 quarters apart
    ]
    suggestions = find_matches(results)
    if suggestions:
        assert suggestions[0].confidence != "exact"


def test_no_self_match():
    r = _rp(54.519, 18.531)
    r["_folder"] = "dev/inv"
    o = _oto(54.519, 18.531)
    o["_folder"] = "dev/inv"  # same folder
    suggestions = find_matches([r, o])
    assert suggestions == []
