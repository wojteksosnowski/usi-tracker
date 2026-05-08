import pytest
import requests_mock as req_mock
from pathlib import Path
from unittest.mock import patch
from .scraper_to import (
    parse_to_product,
    extract_geo,
    extract_gallery_urls,
    filter_investment_images,
    _cdn_filename,
    _investment_image_prefix,
    extract_additional_prop,
    _extract_to_id,
    scrape_tabelaofert,
)
from .url_parser import parse_url

HTML_PATH = (
    Path(__file__).parent.parent
    / "reference-data"
    / "tabelaofert"
    / "pojedynczy rekord"
    / "Teatralna 3 - budynek A Sosnowiec, Śródmieście - Modena Group mieszkania na sprzedaż _ Tabelaofert.pl.html"
)
LISTING_PATH = (
    Path(__file__).parent.parent
    / "reference-data"
    / "tabelaofert"
    / "strona glowna"
    / "Nowe mieszkania - rynek pierwotny _ Tabelaofert.pl.html"
)
ATAL_HTML_PATH = (
    Path(__file__).parent.parent
    / "reference-data"
    / "tabelaofert"
    / "nowe-miasto-polesie"
    / "Nowe Miasto Polesie IV - ATAL - TabelaOfert.pl.html"
)

TO_URL = "https://tabelaofert.pl/inwestycja/teatralna-3-budynek-a-teatralna-1-sosnowiec-srodmiescie-mieszkania-na-sprzedaz,i9248960"
ATAL_TO_URL = "https://tabelaofert.pl/inwestycja/nowe-miasto-polesie-iv-pienista-lodz-polesie-mieszkania-na-sprzedaz,i8978722"

_skipif_no_html = pytest.mark.skipif(not HTML_PATH.exists(), reason="reference HTML not present")
_skipif_no_listing = pytest.mark.skipif(not LISTING_PATH.exists(), reason="listing HTML not present")
_skipif_no_atal = pytest.mark.skipif(not ATAL_HTML_PATH.exists(), reason="ATAL reference HTML not present")


@pytest.fixture(scope="module")
def html():
    return HTML_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def product(html):
    return parse_to_product(html)


# --- parse_to_product ---

@_skipif_no_html
def test_parse_product_name(product):
    assert "Teatralna 3" in product["name"]

@_skipif_no_html
def test_parse_developer(product):
    assert product["brand"]["name"] == "Modena Group"

@_skipif_no_html
def test_parse_offer_count(product):
    assert product["offers"]["offerCount"] == 61

@_skipif_no_html
def test_parse_price_range(product):
    assert float(product["offers"]["lowPrice"]) == pytest.approx(336474.0)
    assert float(product["offers"]["highPrice"]) == pytest.approx(699608.0)

@_skipif_no_html
def test_parse_has_individual_offers(product):
    assert len(product["offers"]["offers"]) == 61


# --- extract_geo ---

@_skipif_no_html
def test_extract_geo(product):
    lat, lng = extract_geo(product)
    assert lat == pytest.approx(50.274, abs=0.01)
    assert lng == pytest.approx(19.126, abs=0.01)

def test_extract_geo_empty():
    lat, lng = extract_geo({})
    assert lat is None
    assert lng is None

def test_extract_geo_no_geo_in_offers():
    product = {"offers": {"offers": [{"itemOffered": {}}]}}
    lat, lng = extract_geo(product)
    assert lat is None
    assert lng is None


# --- extract_additional_prop ---

@_skipif_no_html
def test_parse_delivery_date(product):
    val = extract_additional_prop(product, "Termin oddania")
    assert val is not None
    assert "2027" in val

@_skipif_no_html
def test_parse_ceiling_height(product):
    val = extract_additional_prop(product, "Wysokość mieszkania")
    assert val is not None
    assert "2,60" in val or "2.60" in val

def test_extract_additional_prop_missing():
    assert extract_additional_prop({}, "Nieistniejące pole") is None

def test_extract_additional_prop_from_list():
    product = {
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Winda", "value": "tak"},
            {"@type": "PropertyValue", "name": "Garaż", "value": "podziemny"},
        ]
    }
    assert extract_additional_prop(product, "Winda") == "tak"
    assert extract_additional_prop(product, "Garaż") == "podziemny"
    assert extract_additional_prop(product, "Brak") is None


# --- extract_gallery_urls ---

@_skipif_no_html
def test_extract_gallery_urls(html):
    urls = extract_gallery_urls(html)
    assert len(urls) > 0
    assert all("content.tabelaofert.pl" in u for u in urls)

def test_extract_gallery_urls_empty():
    assert extract_gallery_urls("<html></html>") == []


# --- filter_investment_images ---

def test_filter_investment_images_synthetic():
    product = {
        "image": "https://content.tabelaofert.pl/thumb_200x200,1035-/teatralna-3-mieszkania-modena-20260305-1_aabbccdd.webp"
    }
    urls = [
        "https://content.tabelaofert.pl/quality_85,scale_3840,110902-/teatralna-3-mieszkania-modena-20260305-1_aabbccdd.webp",
        "https://content.tabelaofert.pl/quality_85,scale_212,110902-/teatralna-3-mieszkania-modena-20260305-1_aabbccdd.webp",
        "https://content.tabelaofert.pl/quality_85,scale_1080,110902-/mapa-i9248960_aabbccdd.webp",
        "https://content.tabelaofert.pl/quality_85,scale_1080,110902-/logo-modena-group.webp",
        "https://content.tabelaofert.pl/quality_85,scale_1080,110902-/inne-osiedle-20250101-1_bbccddee.webp",
    ]
    result = filter_investment_images(urls, product)
    assert len(result) == 1
    assert "scale_3840" in result[0]

def test_filter_investment_images_no_product_image():
    urls = [
        "https://content.tabelaofert.pl/quality_85,scale_1080,110902-/mapa-i123_aa.webp",
        "https://content.tabelaofert.pl/quality_85,scale_1080,110902-/logo-dev.webp",
        "https://content.tabelaofert.pl/quality_85,scale_1080,110902-/galeria-foto-20260101-1_bb.webp",
    ]
    result = filter_investment_images(urls, {})
    fnames = [_cdn_filename(u) for u in result]
    assert not any(f.startswith("mapa-") for f in fnames)
    assert not any(f.startswith("logo-") for f in fnames)
    assert len(result) == 1

def test_investment_image_prefix_with_date():
    url = "https://content.tabelaofert.pl/thumb_200x200,1035-/teatralna-3-mieszkania-modena-teatralna-sosnowiec-20260305-1_aabb.webp"
    assert _investment_image_prefix(url) == "teatralna-3-mieszkania-modena-teatralna-sosnowiec"

def test_investment_image_prefix_no_date():
    url = "https://content.tabelaofert.pl/thumb_200x200,1035-/osiedle-alfa-beta-gamma-delta.webp"
    assert _investment_image_prefix(url) == "osiedle-alfa-beta-gamma"

@_skipif_no_html
def test_filter_removes_maps_logos(html, product):
    urls = extract_gallery_urls(html)
    filtered = filter_investment_images(urls, product)
    fnames = [_cdn_filename(u) for u in filtered]
    assert not any(f.startswith("mapa-") for f in fnames)
    assert not any(f.startswith("logo-") for f in fnames)

@_skipif_no_html
def test_filter_only_teatralna_images(html, product):
    urls = extract_gallery_urls(html)
    filtered = filter_investment_images(urls, product)
    fnames = [_cdn_filename(u) for u in filtered]
    assert len(filtered) > 0
    assert all(f.startswith("teatralna-3-") for f in fnames), f"Unexpected: {fnames}"

@_skipif_no_html
def test_filter_deduplicates_scale_variants(html, product):
    urls = extract_gallery_urls(html)
    filtered = filter_investment_images(urls, product)
    fnames = [_cdn_filename(u) for u in filtered]
    assert len(fnames) == len(set(fnames)), f"Duplicate filenames: {fnames}"


# --- _extract_to_id ---

def test_extract_to_id():
    assert _extract_to_id(TO_URL) == "9248960"

def test_extract_to_id_with_trailing_slash():
    assert _extract_to_id("https://tabelaofert.pl/inwestycja/abc,i12345/") == "12345"

def test_extract_to_id_missing():
    assert _extract_to_id("https://tabelaofert.pl/inwestycja/abc") is None


# --- url_parser ---

def test_url_parser_tabelaofert():
    result = parse_url(TO_URL)
    assert result["type"] == "tabelaofert"
    assert result["to_id"] == "9248960"

def test_url_parser_tabelaofert_slug():
    result = parse_url(TO_URL)
    assert result["investment_slug"] == "teatralna-3-budynek-a-teatralna-1-sosnowiec-srodmiescie-mieszkania-na-sprzedaz"


# --- listing page ---

@pytest.fixture(scope="module")
def atal_html():
    return ATAL_HTML_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def atal_product(atal_html):
    return parse_to_product(atal_html)


@_skipif_no_atal
def test_atal_filter_removes_other_projects(atal_html, atal_product):
    urls = extract_gallery_urls(atal_html)
    filtered = filter_investment_images(urls, atal_product)
    fnames = [_cdn_filename(u) for u in filtered]
    other_projects = ["Apollina", "Heyki", "French-Park", "Naramowice", "Zerniki",
                      "Przystan", "Smugowa", "Modern-Helenow"]
    for project in other_projects:
        assert not any(project.lower() in f.lower() for f in fnames), \
            f"Found image from other project '{project}' in filtered results"

@_skipif_no_atal
def test_atal_filter_reduces_image_count(atal_html, atal_product):
    urls = extract_gallery_urls(atal_html)
    filtered = filter_investment_images(urls, atal_product)
    assert len(filtered) < 100, f"Too many images after filter: {len(filtered)}"
    assert len(filtered) > 0

@_skipif_no_atal
def test_atal_filter_all_investment_images(atal_html, atal_product):
    urls = extract_gallery_urls(atal_html)
    filtered = filter_investment_images(urls, atal_product)
    fnames = [_cdn_filename(u) for u in filtered]
    assert all("nowe-miasto-polesie" in f.lower() for f in fnames), \
        f"Unexpected filenames: {[f for f in fnames if 'nowe-miasto-polesie' not in f.lower()]}"

@_skipif_no_atal
def test_atal_no_duplicate_filenames(atal_html, atal_product):
    urls = extract_gallery_urls(atal_html)
    filtered = filter_investment_images(urls, atal_product)
    fnames = [_cdn_filename(u) for u in filtered]
    assert len(fnames) == len(set(fnames)), "Duplicate filenames after dedup"


@_skipif_no_listing
def test_listing_page_investments():
    import json, re
    html = LISTING_PATH.read_text(encoding="utf-8")
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    product = {}
    for s in scripts:
        if '"@type":"Product"' in s:
            try:
                product = json.loads(s)
                break
            except Exception:
                pass
    offers = product.get("offers", {}).get("offers", [])
    assert len(offers) >= 20
    assert all("tabelaofert.pl" in o.get("url", "") for o in offers)


# --- scrape_tabelaofert (mock) ---

@_skipif_no_html
def test_scrape_tabelaofert_mock(html):
    with req_mock.Mocker() as m:
        m.get(TO_URL, text=html)
        with patch("python_worker.scraper_to.save_images", return_value=[]):
            result = scrape_tabelaofert(TO_URL, "tabelaofert", "teatralna-3")

    assert result["source"] == "tabelaofert.pl"
    assert result["to_id"] == "9248960"
    assert result["developer_slug"] == "modena-group"
    assert result["latitude"] == pytest.approx(50.274, abs=0.01)
    assert result["longitude"] == pytest.approx(19.126, abs=0.01)
    assert result["price_min"] == pytest.approx(336474.0)
    assert result["price_max"] == pytest.approx(699608.0)
    assert result["properties_count"] == 61
    assert result["construction_date_upper"] is not None
    assert "raw_details" in result

@_skipif_no_html
def test_scrape_tabelaofert_no_raw_details_leakage(html):
    with req_mock.Mocker() as m:
        m.get(TO_URL, text=html)
        with patch("python_worker.scraper_to.save_images", return_value=[]):
            result = scrape_tabelaofert(TO_URL, "tabelaofert", "teatralna-3")
    # raw_details is the full product schema — present but separate from lightweight fields
    assert "raw_details" in result
    assert "additionalProperty" not in result  # not leaked at top level

def test_scrape_tabelaofert_fetch_error():
    with req_mock.Mocker() as m:
        m.get(TO_URL, status_code=500)
        import os
        with patch.dict(os.environ, {"SCRAPERAPI_KEY": ""}):
            from importlib import reload
            import python_worker.config as cfg
            with patch("python_worker.scraper_to.SCRAPERAPI_KEY", ""):
                result = scrape_tabelaofert(TO_URL, "tabelaofert", "teatralna-3")
    assert "error" in result

def test_scrape_tabelaofert_missing_schema():
    with req_mock.Mocker() as m:
        m.get(TO_URL, text="<html><body>Strona bez danych</body></html>")
        with patch("python_worker.scraper_to.SCRAPERAPI_KEY", ""):
            result = scrape_tabelaofert(TO_URL, "tabelaofert", "teatralna-3")
    assert "error" in result
