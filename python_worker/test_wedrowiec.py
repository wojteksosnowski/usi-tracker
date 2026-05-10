"""
Tests for Wędrowiec (unified crawler):
  - DeveloperManager.find_by_portal_id
  - Page parsers: _fetch_rp_page, _fetch_oto_page, _fetch_to_page
  - _register_if_new: new dev saved, existing dev skipped
  - Exploration state: persisted and incremented correctly
"""
import json
import re
import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def dirs(tmp_path):
    data_dir = tmp_path / "USIdata"
    dev_dir = tmp_path / "USIdev"
    data_dir.mkdir()
    dev_dir.mkdir()
    return data_dir, dev_dir


@pytest.fixture
def wedrowiec(dirs):
    data_dir, dev_dir = dirs
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.crawler import Wedrowiec
        return Wedrowiec(data_dir, dev_dir)


def _write_dev(dev_dir: Path, slug: str, portal_mapping: dict) -> Path:
    profile = {
        "developer_slug": slug,
        "name": slug.title(),
        "usi_dev_id": f"DEV-TEST-{slug}",
        "portal_mapping": portal_mapping,
        "audit": {"created_at": datetime.now().isoformat()},
    }
    p = dev_dir / f"usi_dev_{slug}.json"
    p.write_text(json.dumps(profile))
    return p


# ── DeveloperManager.find_by_portal_id ────────────────────────────────────────

def test_find_by_portal_id_rp_by_id(dirs):
    data_dir, dev_dir = dirs
    _write_dev(dev_dir, "acme", {"rp": {"id": "999", "slug": "acme"}})
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(data_dir, dev_dir)
    assert dm.find_by_portal_id("rp", "999") is not None


def test_find_by_portal_id_rp_by_slug(dirs):
    data_dir, dev_dir = dirs
    _write_dev(dev_dir, "acme", {"rp": {"id": "", "slug": "acme-rp"}})
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(data_dir, dev_dir)
    assert dm.find_by_portal_id("rp", "acme-rp") is not None


def test_find_by_portal_id_oto_agency_id(dirs):
    data_dir, dev_dir = dirs
    _write_dev(dev_dir, "acme", {"oto": {"agency_id": "5555"}})
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(data_dir, dev_dir)
    assert dm.find_by_portal_id("oto", "5555") is not None


def test_find_by_portal_id_oto_agency_ids_list(dirs):
    data_dir, dev_dir = dirs
    _write_dev(dev_dir, "acme", {"oto": {"agency_ids": ["100", "200"]}})
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(data_dir, dev_dir)
    assert dm.find_by_portal_id("oto", "200") is not None


def test_find_by_portal_id_not_found(dirs):
    data_dir, dev_dir = dirs
    _write_dev(dev_dir, "acme", {"rp": {"id": "111"}})
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(data_dir, dev_dir)
    assert dm.find_by_portal_id("rp", "999") is None


def test_find_by_portal_id_null_portal_mapping(dirs):
    data_dir, dev_dir = dirs
    _write_dev(dev_dir, "acme", {"rp": None, "oto": None})
    with patch("python_worker.config.get_scraper_config", return_value=None):
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(data_dir, dev_dir)
    assert dm.find_by_portal_id("rp", "anything") is None


# ── Page parser: RP ───────────────────────────────────────────────────────────

def _rp_html(dev_pairs: list[tuple]) -> str:
    """Build fake RP developer listing HTML with /deweloperzy/{slug}-{id}/ links."""
    links = "".join(
        f'<a href="/deweloperzy/{slug}-{vid}/">{name}</a>'
        for slug, vid, name in dev_pairs
    )
    return f"<html><body>{links}</body></html>"


def test_fetch_rp_page_parses_links(wedrowiec):
    html = _rp_html([
        ("dom-development-sa", "955", "Dom Development S.A."),
        ("atal-sa", "1084", "ATAL S.A."),
    ])
    import requests as std_requests
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()
    with patch("python_worker.crawler.requests", create=True), \
         patch("requests.get", return_value=mock_resp):
        devs = wedrowiec._fetch_rp_page(1)
    assert len(devs) == 2
    assert devs[0] == {"name": "Dom Development S.A.", "id": "955", "slug": "dom-development-sa"}


def test_fetch_rp_page_deduplicates(wedrowiec):
    """Same vendor ID appearing twice (e.g., in featured + list) counted once."""
    html = _rp_html([("atal-sa", "1084", "ATAL"), ("atal-sa", "1084", "ATAL")])
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_resp):
        devs = wedrowiec._fetch_rp_page(1)
    assert len(devs) == 1


def test_fetch_rp_page_request_failure_returns_empty(wedrowiec):
    with patch("requests.get", side_effect=Exception("timeout")):
        assert wedrowiec._fetch_rp_page(1) == []


# ── Page parser: OTO ──────────────────────────────────────────────────────────

def _oto_html(agencies: list[tuple]) -> str:
    """Build fake OTO legacy HTML with /pl/firmy/deweloperzy/{slug}-ID{id} links."""
    links = "".join(
        f'<a href="/pl/firmy/deweloperzy/{slug}-ID{aid}">{name}</a>'
        for slug, aid, name in agencies
    )
    return f"<html><body>{links}</body></html>"


def test_fetch_oto_page_parses_agencies(wedrowiec):
    html = _oto_html([
        ("alpha-deweloper", "10", "Alpha Deweloper"),
        ("beta-deweloper", "20", "Beta Deweloper"),
    ])
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = html
    with patch.object(wedrowiec, "_get_fetcher", return_value=mock_fetcher):
        devs = wedrowiec._fetch_oto_page(1)
    assert len(devs) == 2
    assert devs[0] == {"name": "Alpha Deweloper", "agency_id": "10"}


def test_fetch_oto_page_no_links_returns_empty(wedrowiec):
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = "<html><body>brak deweloperow</body></html>"
    with patch.object(wedrowiec, "_get_fetcher", return_value=mock_fetcher):
        devs = wedrowiec._fetch_oto_page(1)
    assert devs == []


# ── Page parser: TO ───────────────────────────────────────────────────────────

def _to_html(slugs_names: list[tuple]) -> str:
    links = "".join(
        f'<a href="/katalog-firm/deweloperzy/{s}">{n}</a>' for s, n in slugs_names
    )
    return f"<html><body>{links}</body></html>"


def test_fetch_to_page_parses_links(wedrowiec):
    html = _to_html([("acme-sp", "Acme Sp. z o.o."), ("beta-sa", "Beta S.A.")])
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = html
    with patch.object(wedrowiec, "_get_fetcher", return_value=mock_fetcher):
        devs = wedrowiec._fetch_to_page(1)
    assert len(devs) == 2
    assert devs[0] == {"name": "Acme Sp. z o.o.", "slug": "acme-sp"}


def test_fetch_to_page_deduplicates(wedrowiec):
    # Same slug appearing twice (e.g., in nav + content)
    html = _to_html([("acme-sp", "Acme"), ("acme-sp", "Acme")])
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = html
    with patch.object(wedrowiec, "_get_fetcher", return_value=mock_fetcher):
        devs = wedrowiec._fetch_to_page(1)
    assert len(devs) == 1


# ── _register_if_new ──────────────────────────────────────────────────────────

def test_register_new_dev_from_rp(wedrowiec):
    dev_info = {"name": "Nowy Deweloper", "id": "777", "slug": "nowy-deweloper"}
    result = wedrowiec._register_if_new("rp", dev_info)
    assert result is True
    created = wedrowiec.dev_dir / "usi_dev_nowy-deweloper.json"
    assert created.exists()
    data = json.loads(created.read_text())
    assert data["portal_mapping"]["rp"]["id"] == "777"


def test_register_skips_existing_dev(wedrowiec):
    _write_dev(wedrowiec.dev_dir, "nowy-deweloper", {"rp": {"id": "777"}})
    dev_info = {"name": "Nowy Deweloper", "id": "777", "slug": "nowy-deweloper"}
    result = wedrowiec._register_if_new("rp", dev_info)
    assert result is False


def test_register_new_dev_from_oto(wedrowiec):
    dev_info = {"name": "Otodom Deweloper", "agency_id": "555"}
    result = wedrowiec._register_if_new("oto", dev_info)
    assert result is True
    files = list(wedrowiec.dev_dir.glob("usi_dev_*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["portal_mapping"]["oto"]["agency_id"] == "555"


def test_register_new_dev_from_to(wedrowiec):
    dev_info = {"name": "Tabela Dev", "slug": "tabela-dev"}
    result = wedrowiec._register_if_new("to", dev_info)
    assert result is True
    created = wedrowiec.dev_dir / "usi_dev_tabela-dev.json"
    assert created.exists()


# ── Exploration state persistence ─────────────────────────────────────────────

def test_exploration_state_persists_after_page(wedrowiec):
    """After exploring one page, state file is written with updated page counter."""
    devs = [{"name": "Dev A", "id": "1", "slug": "dev-a"}]
    with patch.object(wedrowiec, "_fetch_dev_page", return_value=devs), \
         patch.object(wedrowiec, "_register_if_new", return_value=True):
        wedrowiec._explore_one_page("rp")

    state = json.loads(wedrowiec._exploration_file.read_text())
    assert state["rp"]["page"] == 1
    assert state["rp"]["total_seen"] == 1
    assert state["rp"]["new_reg"] == 1
    assert "next_at" in state["rp"]


def test_exploration_state_increments_across_pages(wedrowiec):
    devs = [{"name": "Dev X", "id": "9", "slug": "dev-x"}]
    with patch.object(wedrowiec, "_fetch_dev_page", return_value=devs), \
         patch.object(wedrowiec, "_register_if_new", return_value=False):
        wedrowiec._explore_one_page("rp")
        wedrowiec._explore_one_page("rp")

    state = json.loads(wedrowiec._exploration_file.read_text())
    assert state["rp"]["page"] == 2
    assert state["rp"]["total_seen"] == 2
    assert state["rp"]["new_reg"] == 0


def test_exploration_cycle_resets_when_max_pages_reached(wedrowiec):
    # Put state at max_pages so next call triggers reset
    state = {"rp": {"page": 217, "next_at": "2026-01-01T00:00:00Z", "total_seen": 217, "new_reg": 5}}
    wedrowiec._exploration_file.write_text(json.dumps(state))

    wedrowiec._explore_one_page("rp")

    state2 = json.loads(wedrowiec._exploration_file.read_text())
    assert state2["rp"]["page"] == 0
    assert state2["rp"]["cycle_start"] is None


# ── _record_visit dev_log ─────────────────────────────────────────────────────

def _write_simple_dev(dev_dir: Path, slug: str) -> Path:
    profile = {
        "developer_slug": slug,
        "name": slug.title(),
        "usi_dev_id": f"DEV-TEST-{slug}",
        "portal_mapping": {},
        "audit": {"created_at": datetime.now().isoformat()},
    }
    p = dev_dir / f"usi_dev_{slug}.json"
    p.write_text(json.dumps(profile))
    return p


def test_record_visit_writes_dev_log(wedrowiec, dirs):
    data_dir, dev_dir = dirs
    _write_simple_dev(dev_dir, "test-dev")
    with patch("python_worker.logger_utils.USI_DATA_DIR", data_dir):
        wedrowiec._record_visit("test-dev", 3)
    log_file = data_dir / "test-dev" / "dev_log.txt"
    assert log_file.exists()
    content = log_file.read_text()
    assert "Wędrowiec" in content
    assert "3 nowych inwestycji" in content
    assert "Kolejna wizyta" in content


def test_record_visit_appends(wedrowiec, dirs):
    data_dir, dev_dir = dirs
    _write_simple_dev(dev_dir, "test-dev")
    with patch("python_worker.logger_utils.USI_DATA_DIR", data_dir):
        wedrowiec._record_visit("test-dev", 1)
        wedrowiec._record_visit("test-dev", 0)
    log_file = data_dir / "test-dev" / "dev_log.txt"
    lines = [l for l in log_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
