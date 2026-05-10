import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def svc(tmp_path):
    data_dir = tmp_path / "USIdata"
    data_dir.mkdir()
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.services.discovery_service import DiscoveryService
        return DiscoveryService(data_dir=data_dir)


def _write_dev(data_dir, dev_slug, portal_mapping=None):
    dev_dir = data_dir.parent / "USIdev"
    dev_dir.mkdir(parents=True, exist_ok=True)
    profile = {
        "developer_slug": dev_slug, "name": dev_slug.title(),
        "portal_mapping": portal_mapping or {"rp": {"id": "DEV-001"}},
    }
    (dev_dir / f"usi_dev_{dev_slug}.json").write_text(json.dumps(profile))
    return profile


# ── _register_new_investment ──────────────────────────────────────────────────

def test_register_new_investment_creates_skeleton(svc):
    item = {"slug": "nowa-inwestycja", "name": "Nowa Inwestycja", "id": "555", "url": None}
    svc._register_new_investment("acme-dev", item, "rp")
    usi_file = svc.data_dir / "acme-dev" / "nowa-inwestycja" / "usi_nowa-inwestycja.json"
    assert usi_file.exists()
    data = json.loads(usi_file.read_text())
    assert data["sources"]["rp"]["id"] == "555"


def test_register_new_investment_skips_existing_portal(svc):
    item = {"slug": "existing-inv", "name": "Existing", "id": "555", "url": None}
    inv_dir = svc.data_dir / "acme-dev" / "existing-inv"
    inv_dir.mkdir(parents=True)
    existing = {"investment_slug": "existing-inv", "sources": {"rp": {"id": "old-id"}}}
    (inv_dir / "usi_existing-inv.json").write_text(json.dumps(existing))

    svc._register_new_investment("acme-dev", item, "rp")
    data = json.loads((inv_dir / "usi_existing-inv.json").read_text())
    assert data["sources"]["rp"]["id"] == "old-id"  # not overwritten


def test_register_new_investment_oto_uses_url(svc):
    item = {"slug": "oto-inv", "name": "Oto Inv", "id": None, "url": "https://otodom.pl/oto-inv"}
    svc._register_new_investment("acme-dev", item, "otodom")
    data = json.loads((svc.data_dir / "acme-dev" / "oto-inv" / "usi_oto-inv.json").read_text())
    assert data["sources"]["oto"]["url"] == "https://otodom.pl/oto-inv"


# ── discover_for_developer ────────────────────────────────────────────────────

def test_discover_for_developer_unknown_dev_raises(svc):
    with pytest.raises(ValueError, match="not found"):
        svc.discover_for_developer("job-001", "ghost-dev")


def test_discover_for_developer_no_portals_returns_zero(svc):
    _write_dev(svc.data_dir, "acme-dev", portal_mapping={})
    count = svc.discover_for_developer("job-001", "acme-dev")
    assert count == 0


def test_discover_for_developer_null_portal_mapping_values(svc):
    """portal_mapping z wartościami null (z JSONa) nie powinien rzucać wyjątku."""
    _write_dev(svc.data_dir, "platforma", portal_mapping={"rp": None, "oto": None, "to": None})
    count = svc.discover_for_developer("job-001", "platforma")
    assert count == 0


def test_discover_for_developer_null_portal_mapping_updates_progress(svc):
    """Przy null portal_mapping job osiąga 100% z komunikatem o braku powiązań."""
    _write_dev(svc.data_dir, "platforma", portal_mapping={"rp": None, "oto": None, "to": None})
    mock_jm = MagicMock()
    svc.discover_for_developer("job-001", "platforma", job_manager=mock_jm)
    final_call = mock_jm.update_progress.call_args_list[-1]
    assert final_call[0][1] == 100
    assert "Brak" in final_call[0][2]


def test_discover_for_developer_registers_new_items(svc):
    _write_dev(svc.data_dir, "acme-dev", portal_mapping={"rp": {"id": "DEV-001"}})
    new_items = [{"slug": "inv-a", "name": "Inv A", "id": "1", "is_new": True}]
    with patch("python_worker.services.discovery_service.scraper_api.list_investments",
               return_value=new_items), \
         patch("python_worker.portal_matcher.filter_new_investments",
               return_value=new_items):
        count = svc.discover_for_developer("job-001", "acme-dev")
    assert count == 1
    assert (svc.data_dir / "acme-dev" / "inv-a" / "usi_inv-a.json").exists()


def test_discover_for_developer_updates_job_progress(svc):
    _write_dev(svc.data_dir, "acme-dev", portal_mapping={})
    mock_jm = MagicMock()
    svc.discover_for_developer("job-001", "acme-dev", job_manager=mock_jm)
    mock_jm.update_progress.assert_called()
    final_call = mock_jm.update_progress.call_args_list[-1]
    assert final_call[0][1] == 100  # progress=100


def test_discover_for_developer_portal_error_continues(svc):
    _write_dev(svc.data_dir, "acme-dev", portal_mapping={"rp": {"id": "DEV-001"}})
    with patch("python_worker.services.discovery_service.scraper_api.list_investments",
               side_effect=Exception("Network error")):
        count = svc.discover_for_developer("job-001", "acme-dev")
    assert count == 0  # error logged, not raised


# ── discovery_by_portal ───────────────────────────────────────────────────────

def test_discovery_by_portal_returns_filtered_results(svc):
    raw = [{"slug": "inv-x", "name": "Inv X", "is_new": True}]
    with patch("python_worker.services.discovery_service.scraper_api.list_investments",
               return_value=raw), \
         patch("python_worker.portal_matcher.filter_new_investments",
               return_value=raw):
        results = svc.discovery_by_portal("rp", "DEV-001")
    assert len(results) == 1
    assert results[0]["slug"] == "inv-x"


def test_discovery_by_portal_propagates_exceptions(svc):
    with patch("python_worker.services.discovery_service.scraper_api.list_investments",
               side_effect=RuntimeError("API down")):
        with pytest.raises(RuntimeError):
            svc.discovery_by_portal("rp", "DEV-001")
