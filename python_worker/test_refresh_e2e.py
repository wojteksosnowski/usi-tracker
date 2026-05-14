"""
E2E regression tests for the investment refresh pipeline.

These tests mock the network layer (scraper_api.fetch_investment) to verify
the full local pipeline: fetch → save raw → adapt → merge → image sync.
They do NOT make real HTTP calls.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def svc(tmp_path):
    data_dir = tmp_path / "USIdata"
    public_dir = tmp_path / "USI"
    data_dir.mkdir()
    public_dir.mkdir()
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.services.investment_service import InvestmentService
        return InvestmentService(data_dir=data_dir, public_usi_dir=public_dir)


def _write_usi(data_dir, dev_slug, inv_slug, sources=None, extra=None):
    inv_dir = data_dir / dev_slug / inv_slug
    inv_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "investment_slug": inv_slug, "developer_slug": dev_slug,
        "name": "Test", "sources": sources or {},
        "status": "Brak", "ratings": {}, "financials": {}, "specifications": {},
        "location": {"coords": [None, None], "address": None, "city": None, "district": None},
        "amenities": {"labels": [], "raw_codes": []},
        "usi_inv_id": "INV-0001", "usi_dev_id": "DEV-0001",
        "audit": {"created_at": "2024-01-01T00:00:00", "history": []},
    }
    if extra:
        data.update(extra)
    (inv_dir / f"usi_{inv_slug}.json").write_text(json.dumps(data))
    return inv_dir


def _otodom_scraper_result(inv_slug="test-inv", dev_slug="dev"):
    return {
        "source": "otodom.pl",
        "url": "https://otodom.pl/pl/oferta/test-ID123",
        "title": "Test Investment",
        "agency_name": "Test Dev",
        "latitude": 52.0,
        "longitude": 21.0,
        "delivery_quarter": 2,
        "delivery_year": 2027,
        "image_urls": ["https://cdn.oto.pl/a.jpg", "https://cdn.oto.pl/b.jpg"],
        "developer_slug": dev_slug,
        "investment_slug": inv_slug,
        "raw_details": {
            "id": 123,
            "title": "Test Investment",
            "topInformation": [
                {"label": "number_of_units_in_project", "values": ["60"]},
                {"label": "project_finish_date", "values": ["2027-04-30"]},
            ],
            "location": {
                "coordinates": {"latitude": 52.0, "longitude": 21.0},
                "address": {
                    "street": {"name": "Testowa", "number": "5"},
                    "city": {"name": "Warszawa"},
                    "district": {"name": "Mokotów"},
                },
            },
        },
    }


# ── refresh pipeline tests ────────────────────────────────────────────────────

def test_refresh_saves_raw_json(svc):
    """After refresh, raw_oto_*.json appears in the investment directory."""
    inv_dir = _write_usi(svc.data_dir, "dev", "test-inv",
                         sources={"oto": {"url": "https://otodom.pl/pl/oferta/test-ID123"}})

    with patch("usi_scrapers.api.fetch_investment", return_value=_otodom_scraper_result()):
        svc.update_investment("dev", "test-inv")

    assert (inv_dir / "raw_oto_test-inv.json").exists()



def test_refresh_preserves_usi_ids(svc):
    """usi_inv_id and usi_dev_id are not lost during refresh."""
    inv_dir = _write_usi(svc.data_dir, "dev", "test-inv",
                         sources={"oto": {"url": "https://otodom.pl/pl/oferta/test-ID123"}})

    with patch("usi_scrapers.api.fetch_investment", return_value=_otodom_scraper_result()):
        svc.update_investment("dev", "test-inv")

    usi = json.loads((inv_dir / "usi_test-inv.json").read_text())
    assert usi["usi_inv_id"] == "INV-0001"
    assert usi["usi_dev_id"] == "DEV-0001"


def test_refresh_preserves_existing_address_when_portal_returns_null(svc):
    """Fields already in usi_*.json are not zeroed out if the portal returns null."""
    existing_extra = {
        "location": {"coords": [52.0, 21.0], "address": "ul. Stara 1",
                     "city": "Kraków", "district": "Stare Miasto"},
        "specifications": {"units_count": 30, "delivery_date": None},
        "amenities": {"labels": ["Parking", "Balkon"], "raw_codes": []},
    }
    inv_dir = _write_usi(svc.data_dir, "dev", "test-inv",
                         sources={"oto": {"url": "https://otodom.pl/pl/oferta/test-ID123"}},
                         extra=existing_extra)

    # Scraper returns result with no address info in raw_details
    result = _otodom_scraper_result()
    result["raw_details"]["location"] = {"coordinates": {"latitude": 52.0, "longitude": 21.0}}
    result["raw_details"].pop("topInformation", None)

    with patch("usi_scrapers.api.fetch_investment", return_value=result):
        svc.update_investment("dev", "test-inv")

    usi = json.loads((inv_dir / "usi_test-inv.json").read_text())
    assert usi["location"]["address"] == "ul. Stara 1"
    assert usi["location"]["city"] == "Kraków"
    assert usi["specifications"]["units_count"] == 30
    assert "Parking" in usi["amenities"]["labels"]


def test_refresh_all_portals_fail_raises_runtime_error(svc):
    """When all portals return errors, RuntimeError is raised (not silent False)."""
    _write_usi(svc.data_dir, "dev", "test-inv",
               sources={"oto": {"url": "https://otodom.pl/pl/oferta/test-ID123"}})

    with patch("usi_scrapers.api.fetch_investment", return_value={"error": "500 Server Error"}):
        with pytest.raises(RuntimeError, match="Fetch failed for all portals"):
            svc.update_investment("dev", "test-inv")


def test_refresh_oto_uses_url_not_id(svc):
    """For Otodom, the URL (not numeric ID) is passed as the identifier to fetch_investment."""
    _write_usi(svc.data_dir, "dev", "test-inv",
               sources={"oto": {"id": "66662531",
                                "url": "https://otodom.pl/pl/oferta/test-inv-ID4wHY7"}})

    captured = {}

    def _fake_fetch(config, fetcher, portal, identifier, *args, **kwargs):
        captured["identifier"] = identifier
        return _otodom_scraper_result()

    with patch("usi_scrapers.api.fetch_investment", side_effect=_fake_fetch):
        svc.update_investment("dev", "test-inv")

    assert captured["identifier"] == "https://otodom.pl/pl/oferta/test-inv-ID4wHY7"
    assert captured["identifier"] != "66662531"


def test_refresh_rp_uses_id_not_url(svc):
    """For RynekPierwotny, the numeric ID is preferred over URL."""
    _write_usi(svc.data_dir, "dev", "test-inv",
               sources={"rp": {"id": "12345", "url": "https://rp.pl/oferty/dev/test-12345/"}})

    captured = {}

    def _fake_fetch(config, fetcher, portal, identifier, *args, **kwargs):
        captured["identifier"] = identifier
        return {
            "source": "rynekpierwotny.pl",
            "id": "12345", "name": "Test", "url": "https://rp.pl/12345",
            "image_urls": [], "raw_details": {},
        }

    with patch("usi_scrapers.api.fetch_investment", side_effect=_fake_fetch):
        svc.update_investment("dev", "test-inv")

    assert captured["identifier"] == "12345"
