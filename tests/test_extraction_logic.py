import pytest
from python_worker.adapters import RPAdapter, OtodomAdapter, TOAdapter


# ── RPAdapter ─────────────────────────────────────────────────────────────────
# raw_details path (from raw_rp_*.json on disk)

def test_rp_adapter_extraction():
    raw_data = {
        "id": 12345,
        "name": "Test RP Investment",
        "url": "https://rp.pl/12345",
        "main_image": {"m_img_500": "https://cdn.rp.pl/main.jpg"},
        "_raw_gallery": {
            "gallery": [
                {"image": {"g_img_1500": "https://cdn.rp.pl/1.jpg"}},
                {"image": {"g_img_1500": "https://cdn.rp.pl/2.jpg"}}
            ]
        }
    }
    result = RPAdapter.transform(raw_data, "test-inv", "test-dev")
    assert result["name"] == "Test RP Investment"
    assert "https://cdn.rp.pl/main.jpg" in result["image_urls"]
    assert "https://cdn.rp.pl/1.jpg" in result["image_urls"]
    assert "https://cdn.rp.pl/2.jpg" in result["image_urls"]
    assert len(result["image_urls"]) == 3
    assert result["images_count"] == 3


def test_rp_adapter_geo():
    raw_data = {
        "id": 1,
        "name": "Geo Test",
        "geo_point": {"type": "Point", "coordinates": [21.01, 52.23]},
        "address": "Warszawa, ul. Testowa 1",
    }
    result = RPAdapter.transform(raw_data, "geo-inv", "dev")
    assert result["location"]["coords"] == [52.23, 21.01]
    assert result["location"]["address"] == "Warszawa, ul. Testowa 1"
    assert result["location"]["city"] == "Warszawa"


def test_rp_adapter_get_val_wrapped_name():
    raw_data = {
        "id": 2,
        "name": {"type": "str", "value": "Wrapped Name"},
    }
    result = RPAdapter.transform(raw_data, "inv", "dev")
    assert result["name"] == "Wrapped Name"


# scraper result path (from network fetch)

def test_rp_adapter_from_scraper_result():
    scraper_result = {
        "source": "rynekpierwotny.pl",
        "id": "9999",
        "url": "https://rynekpierwotny.pl/oferty/dev/inv-9999/",
        "name": "Modern Apartments",
        "address": "ul. Nowoczesna 5",
        "latitude": 52.25,
        "longitude": 21.02,
        "construction_date_upper": "2026-06-30",
        "properties_count": 120,
        "image_urls": ["https://cdn.rp.pl/x.jpg", "https://cdn.rp.pl/y.jpg"],
        "raw_details": {},
    }
    result = RPAdapter.transform(scraper_result, "inv", "dev")
    assert result["name"] == "Modern Apartments"
    assert result["sources"]["rp"]["id"] == "9999"
    assert result["location"]["coords"] == [52.25, 21.02]
    assert result["specifications"]["delivery_date"] == "2026-06-30"
    assert result["specifications"]["units_count"] == 120
    assert len(result["image_urls"]) == 2


# ── OtodomAdapter ─────────────────────────────────────────────────────────────
# raw_details path

def test_otodom_adapter_extraction():
    raw_data = {
        "ad": {
            "id": 999,
            "title": "Test Otodom Investment",
            "url": "https://otodom.pl/999",
            "images": [
                {"large": "https://cdn.oto.pl/1.jpg"},
                {"large": "https://cdn.oto.pl/2.jpg"}
            ]
        }
    }
    result = OtodomAdapter.transform(raw_data, "test-inv", "test-dev")
    assert result["name"] == "Test Otodom Investment"
    assert "https://cdn.oto.pl/1.jpg" in result["image_urls"]
    assert "https://cdn.oto.pl/2.jpg" in result["image_urls"]
    assert len(result["image_urls"]) == 2


def test_otodom_adapter_old_nested_format():
    """ad_data saved with wrapping {"ad": {...}} structure."""
    raw_data = {
        "ad": {
            "id": 999,
            "title": "Nested Otodom",
            "url": "https://otodom.pl/999",
            "images": [{"large": "https://cdn.oto.pl/1.jpg"}]
        }
    }
    result = OtodomAdapter.transform(raw_data, "test-inv", "test-dev")
    assert result["name"] == "Nested Otodom"


def test_otodom_adapter_delivery_from_topInformation():
    raw_data = {
        "ad": {
            "title": "Delivery Test",
            "topInformation": [
                {"label": "project_finish_date", "values": ["2025-06-01"]}
            ],
            "images": [],
        }
    }
    result = OtodomAdapter.transform(raw_data, "inv", "dev")
    assert result["specifications"]["delivery_year"] == 2025
    assert result["specifications"]["delivery_quarter"] == 2


# scraper result path

def test_otodom_adapter_from_scraper_result():
    scraper_result = {
        "source": "otodom.pl",
        "url": "https://otodom.pl/pl/inwestycja/test",
        "title": "Nowe Mieszkania",
        "agency_name": "Acme SA",
        "latitude": 52.1,
        "longitude": 21.0,
        "delivery_quarter": 3,
        "delivery_year": 2026,
        "image_urls": ["https://cdn.oto.pl/a.jpg"],
        "raw_details": {},
    }
    result = OtodomAdapter.transform(scraper_result, "inv", "dev")
    assert result["name"] == "Nowe Mieszkania"
    assert result["developer"] == "Acme SA"
    assert result["sources"]["oto"]["url"] == "https://otodom.pl/pl/inwestycja/test"
    assert result["specifications"]["delivery_date"] == "2026-Q3"


# ── TOAdapter ─────────────────────────────────────────────────────────────────
# raw_details path

def test_to_adapter_extraction():
    raw_data = {
        "name": "Test TO Investment",
        "url": "https://to.pl/123",
        "_raw_gallery_urls": [
            "https://cdn.to.pl/1.jpg",
            "https://cdn.to.pl/2.jpg"
        ]
    }
    result = TOAdapter.transform(raw_data, "test-inv", "test-dev")
    assert result["name"] == "Test TO Investment"
    assert "https://cdn.to.pl/1.jpg" in result["image_urls"]
    assert "https://cdn.to.pl/2.jpg" in result["image_urls"]
    assert len(result["image_urls"]) == 2


def test_to_adapter_prices():
    raw_data = {
        "name": "Price Test",
        "offers": {"lowPrice": "500000", "highPrice": "900000"},
        "_raw_gallery_urls": [],
    }
    result = TOAdapter.transform(raw_data, "inv", "dev")
    assert result["financials"]["price_min"] == 500000.0
    assert result["financials"]["price_max"] == 900000.0


# scraper result path

def test_to_adapter_from_scraper_result():
    scraper_result = {
        "source": "tabelaofert.pl",
        "to_url": "https://tabelaofert.pl/inwestycja/test,i1234",
        "name": "Zielone Ogrody",
        "developer_name": "Acme Budowlana",
        "latitude": 52.3,
        "longitude": 21.1,
        "price_min": 450000.0,
        "price_max": 800000.0,
        "properties_count": 80,
        "construction_date_upper": "2025-Q4",
        "amenities": [{"name": "Parking"}, {"name": "Ogród"}],
        "image_urls": ["https://cdn.to.pl/z.jpg"],
        "raw_details": {},
    }
    result = TOAdapter.transform(scraper_result, "inv", "dev")
    assert result["name"] == "Zielone Ogrody"
    assert result["sources"]["to"]["url"] == "https://tabelaofert.pl/inwestycja/test,i1234"
    assert result["financials"]["price_min"] == 450000.0
    assert result["specifications"]["delivery_date"] == "2025-Q4"
    assert "Parking" in result["amenities"]["labels"]
