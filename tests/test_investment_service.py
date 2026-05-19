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


def _write_usi(data_dir, dev_slug, inv_slug, extra=None):
    inv_dir = data_dir / dev_slug / inv_slug
    inv_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "investment_slug": inv_slug, "developer_slug": dev_slug,
        "name": "Test Investment", "sources": {"rp": {"id": "123", "url": "https://rp.pl/123"}},
        "status": "Brak", "ratings": {}, "financials": {"price_avg": 500000},
        "specifications": {}, "location": {}, "amenities": {},
        "audit": {"created_at": "2024-01-01T00:00:00", "history": []},
    }
    if extra:
        data.update(extra)
    (inv_dir / f"usi_{inv_slug}.json").write_text(json.dumps(data))
    return inv_dir, data


# ── get_investment ─────────────────────────────────────────────────────────────

def test_get_investment_returns_data(svc):
    _write_usi(svc.data_dir, "acme-dev", "test-inv")
    result = svc.get_investment("acme-dev", "test-inv")
    assert result is not None
    assert result["name"] == "Test Investment"
    assert result["investment_slug"] == "test-inv"


def test_get_investment_missing_returns_none(svc):
    assert svc.get_investment("nobody", "nothing") is None


def test_get_investment_includes_photo_paths(svc):
    _write_usi(svc.data_dir, "acme-dev", "test-inv")
    img_dir = svc.public_usi_dir / "acme-dev" / "test-inv"
    img_dir.mkdir(parents=True)
    (img_dir / "photo.jpg").write_bytes(b"jpg")
    result = svc.get_investment("acme-dev", "test-inv")
    assert any("photo.jpg" in p for p in result["photos"])


# ── save_ratings ──────────────────────────────────────────────────────────────

def test_save_ratings_writes_file(svc):
    _write_usi(svc.data_dir, "acme-dev", "test-inv")
    result = svc.save_ratings("acme-dev", "test-inv", {"Balkony": 3.0, "status": "Pełna"})
    assert result is True
    ratings_file = svc.data_dir / "acme-dev" / "test-inv" / "meta_test-inv_ratings.json"
    assert ratings_file.exists()
    saved = json.loads(ratings_file.read_text())
    assert saved["Balkony"] == 3.0
    assert saved["status"] == "Pełna"


def test_save_ratings_invalid_value_raises(svc):
    _write_usi(svc.data_dir, "acme-dev", "test-inv")
    with pytest.raises(ValueError, match="Invalid value"):
        svc.save_ratings("acme-dev", "test-inv", {"Balkony": 99})


def test_save_ratings_invalid_status_raises(svc):
    _write_usi(svc.data_dir, "acme-dev", "test-inv")
    with pytest.raises(ValueError, match="Invalid status"):
        svc.save_ratings("acme-dev", "test-inv", {"status": "NIEZNANY"})


def test_save_ratings_missing_investment_returns_false(svc):
    assert svc.save_ratings("nobody", "nothing", {"Balkony": 2.0}) is False


def test_save_ratings_updates_usi_json(svc):
    _write_usi(svc.data_dir, "acme-dev", "test-inv")
    svc.save_ratings("acme-dev", "test-inv", {"Balkony": 4.0})
    usi = json.loads((svc.data_dir / "acme-dev" / "test-inv" / "usi_test-inv.json").read_text())
    assert usi["ratings"]["Balkony"] == 4.0


# ── mark_deleted_photos ───────────────────────────────────────────────────────

def test_mark_deleted_photos_writes_list(svc):
    _write_usi(svc.data_dir, "acme-dev", "test-inv")
    result = svc.mark_deleted_photos("acme-dev", "test-inv", ["photo1.jpg", "photo2.jpg"])
    assert result is True
    dl = json.loads((svc.data_dir / "acme-dev" / "test-inv" / "deletion_list.json").read_text())
    assert dl["paths"] == ["photo1.jpg", "photo2.jpg"]


def test_mark_deleted_photos_missing_investment_returns_false(svc):
    assert svc.mark_deleted_photos("nobody", "nothing", []) is False


# ── update_investment ─────────────────────────────────────────────────────────

def test_update_investment_missing_file_returns_false(svc):
    assert svc.update_investment("nobody", "nothing") is False


def test_update_investment_rebuild_from_raw(svc, tmp_path):
    inv_dir, _ = _write_usi(svc.data_dir, "acme-dev", "test-inv",
                             extra={"sources": {"rp": {"id": "123"}}})
    raw_data = {
        "id": 123, "name": "Test Investment",
        "url": "https://rp.pl/123",
        "main_image": {"m_img_500": "https://cdn.rp.pl/main.jpg"},
        "_raw_gallery": {"gallery": []},
    }
    (inv_dir / "raw_rp_test-inv.json").write_text(json.dumps(raw_data))

    mock_unified = {
        "investment_slug": "test-inv", "developer_slug": "acme-dev",
        "name": "Test Investment Updated", "sources": {"rp": {"id": "123"}},
        "financials": {}, "specifications": {}, "location": {}, "amenities": {},
        "image_urls": [], "images_count": 0, "image_paths": [],
    }
    with patch("python_worker.adapters.AdapterFactory.get_adapter") as mock_factory:
        mock_adapter = MagicMock()
        mock_adapter.transform.return_value = mock_unified
        mock_factory.return_value = mock_adapter
        result = svc.update_investment("acme-dev", "test-inv", use_local_raw=True)

    assert result is True
    # Output uses new canonical: usi_rp_{portal_id}.json (sources.rp.id = "123")
    saved = json.loads((inv_dir / "usi_rp_123.json").read_text())
    assert saved["name"] == "Test Investment Updated"


def test_update_investment_all_portals_fail_raises_runtime_error(svc):
    inv_dir, _ = _write_usi(svc.data_dir, "acme-dev", "test-inv",
                             extra={"sources": {"rp": {"id": "123"}}})
    with patch("usi_scrapers.api.fetch_investment", return_value={"error": "ScraperAPI 500"}):
        with pytest.raises(RuntimeError, match="Fetch failed for all portals"):
            svc.update_investment("acme-dev", "test-inv")


def test_update_investment_fetch_exception_raises_runtime_error(svc):
    inv_dir, _ = _write_usi(svc.data_dir, "acme-dev", "test-inv",
                             extra={"sources": {"rp": {"id": "123"}}})
    with patch("usi_scrapers.api.fetch_investment", side_effect=ConnectionError("timeout")):
        with pytest.raises(RuntimeError, match="Fetch failed for all portals"):
            svc.update_investment("acme-dev", "test-inv")


def test_update_investment_partial_success_logs_failed(svc):
    inv_dir, _ = _write_usi(svc.data_dir, "acme-dev", "test-inv",
                             extra={"sources": {"rp": {"id": "123"}, "oto": {"url": "https://otodom.pl/test"}}})
    mock_unified = {
        "investment_slug": "test-inv", "developer_slug": "acme-dev",
        "name": "Partial", "sources": {"rp": {"id": "123"}},
        "financials": {}, "specifications": {}, "location": {}, "amenities": {},
        "image_urls": [], "images_count": 0, "image_paths": [],
    }

    def _fake_fetch(config, fetcher, portal, *args, **kwargs):
        if portal == "rp":
            return {"source": "rynekpierwotny.pl", "raw_details": {}, "name": "Test",
                    "id": "123", "image_urls": []}
        return {"error": "ScraperAPI 500"}

    with patch("usi_scrapers.api.fetch_investment", side_effect=_fake_fetch):
        with patch("python_worker.adapters.AdapterFactory.get_adapter") as mock_factory:
            mock_adapter = MagicMock()
            mock_adapter.transform.return_value = mock_unified
            mock_factory.return_value = mock_adapter
            result = svc.update_investment("acme-dev", "test-inv")

    assert result is True  # partial success: rp succeeded, oto failed
