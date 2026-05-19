import pytest
from .here_maps import build_here_url, enrich_with_here_map


LAT = 54.15963
LON = 19.39349


def test_build_here_url_basic():
    url = build_here_url(LAT, LON)
    assert "image.maps.hereapi.com" in url
    assert str(LAT) in url
    assert str(LON) in url
    assert "apiKey=" in url
    assert "explore.satellite.day" in url


def test_build_here_url_custom_style():
    url = build_here_url(LAT, LON, style="explore.day")
    assert "explore.day" in url
    assert "satellite" not in url


def test_build_here_url_custom_dimensions():
    url = build_here_url(LAT, LON, width=800, height=400)
    assert "800x400" in url


def test_build_here_url_zoom():
    url = build_here_url(LAT, LON, zoom=14)
    assert "zoom=14" in url.split("?")[0]


def test_build_here_url_poi_format():
    url = build_here_url(LAT, LON)
    assert f"point:{LAT},{LON}" in url


def test_enrich_adds_url():
    result = {"latitude": LAT, "longitude": LON}
    enrich_with_here_map(result)
    assert "here_map_url" in result
    assert result["here_map_url"].startswith("https://")


def test_enrich_no_coords():
    result = {"name": "Test"}
    enrich_with_here_map(result)
    assert "here_map_url" not in result


def test_enrich_none_coords():
    result = {"latitude": None, "longitude": None}
    enrich_with_here_map(result)
    assert "here_map_url" not in result


def test_enrich_pois_disabled_by_default():
    result = {"latitude": LAT, "longitude": LON}
    enrich_with_here_map(result)
    assert "pois:disabled" in result["here_map_url"]


def test_build_here_url_zoom_in_path():
    url = build_here_url(LAT, LON, zoom=14)
    path = url.split("?")[0]
    assert "overlay:zoom=14" in path


def test_build_here_url_no_center_param():
    url = build_here_url(LAT, LON)
    assert "c=" not in url


def test_build_here_url_night_style():
    url = build_here_url(LAT, LON, style="explore.night")
    assert "explore.night" in url


def test_build_here_url_day_style():
    url = build_here_url(LAT, LON, style="explore.day")
    assert "explore.day" in url
    assert "satellite" not in url


def test_build_here_url_ui_dimensions():
    url = build_here_url(LAT, LON, width=560, height=140, zoom=14)
    assert "560x140" in url
    assert "zoom=14" in url.split("?")[0]
