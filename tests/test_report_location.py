from datetime import date

import pytest

from python_worker.gmaps_url import parse_gmaps_location
from python_worker.services.delivery_filter import (
    matches_delivery, parse_delivery, delivery_years, current_quarter_ord, READY, validate_tokens,
)

TODAY = date(2026, 10, 4)


@pytest.mark.parametrize("text,lat,lon", [
    ("https://www.google.com/maps/@50.0647,19.9450,15z", 50.0647, 19.9450),
    ("https://www.google.com/maps/place/Rynek/@50.06,19.93,17z/data=!3m1!4b1!4m6!3d50.0614!4d19.9372", 50.0614, 19.9372),
    ("https://www.google.com/maps?q=50.0647,19.9450", 50.0647, 19.9450),
    ("https://maps.google.com/?ll=50.0647%2C19.9450&z=14", 50.0647, 19.9450),
    ("50.0647, 19.9450", 50.0647, 19.9450),
])
def test_gmaps_coords(text, lat, lon):
    res = parse_gmaps_location(text)
    assert (res["lat"], res["lon"]) == (lat, lon)


def test_gmaps_place_label_and_geocoder_fallback():
    url = "https://www.google.com/maps/place/Lubostro%C5%84+13,+Krak%C3%B3w"
    res = parse_gmaps_location(url, geocoder=lambda a: (50.0, 19.9))
    assert res == {"lat": 50.0, "lon": 19.9, "label": "Lubostroń 13, Kraków"}


def test_gmaps_garbage():
    assert parse_gmaps_location("", geocoder=lambda a: (1, 1)) is None
    assert parse_gmaps_location("https://example.com/x") is None


@pytest.mark.parametrize("value,expected", [
    ("2025-Q4", (2025 * 4 + 4,) * 2),
    ("2024-Q2 / 2024-Q3", (2024 * 4 + 2, 2024 * 4 + 3)),
    ("IV\xa0kwartał 2026", (2026 * 4 + 4,) * 2),
    ("2025-Q4 / gotowe do odbioru", (READY, 2025 * 4 + 4)),
    ("gotowe do odbioru", (READY, READY)),
    ("maj 2026", (2026 * 4 + 2,) * 2),
    (None, None), ("", None),
])
def test_parse_delivery(value, expected):
    assert parse_delivery(value) == expected


def test_matches_delivery():
    assert current_quarter_ord(TODAY) == 2026 * 4 + 4
    assert matches_delivery("2027-Q1", [], TODAY)
    assert matches_delivery("2027-Q1", ["2027"], TODAY)
    assert not matches_delivery("2027-Q1", ["2026"], TODAY)
    assert matches_delivery("2029-Q2", ["2028+"], TODAY)
    assert matches_delivery("2026-Q3", ["ready"], TODAY)
    assert not matches_delivery("2026-Q4", ["ready"], TODAY)
    assert matches_delivery("2026-Q4 / 2027-Q1", ["2027-Q1"], TODAY)
    assert not matches_delivery(None, ["2026"], TODAY)
    assert matches_delivery(None, ["2026", "none"], TODAY)


def test_year_range_token():
    assert matches_delivery("2026-Q1", ["2026-2028"], TODAY)
    assert matches_delivery("2028-Q4", ["2026-2028"], TODAY)
    assert not matches_delivery("2029-Q1", ["2026-2028"], TODAY)
    assert not matches_delivery("2025-Q3", ["2026-2028"], TODAY)
    assert matches_delivery("2025-Q4 / 2026-Q1", ["2026-2028"], TODAY)
    assert not matches_delivery(None, ["2026-2028"], TODAY)
    assert matches_delivery("2024-Q1", ["1900-2025"], TODAY)
    assert matches_delivery("2031-Q1", ["2028+"], TODAY)


def test_reversed_range_rejected():
    with pytest.raises(ValueError):
        validate_tokens(["2028-2026"])


def test_delivery_years():
    assert delivery_years("2025-Q4 / 2026-Q1") == [2025, 2026]
    assert delivery_years("2027-Q2") == [2027]
    assert delivery_years("gotowe do odbioru") == []
    assert delivery_years("2025-Q4 / gotowe do odbioru") == [2025]
    assert delivery_years(None) == []
