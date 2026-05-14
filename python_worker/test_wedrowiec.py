"""
Tests for Wędrowiec (unified crawler):
  - DeveloperManager.find_by_portal_id
  - _fetch_dev_page: delegates to scraper_api.list_developers
  - _register_if_new: new dev saved, existing dev skipped
  - Exploration state: persisted and incremented correctly
"""
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
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


# ── _fetch_dev_page: delegates to scraper_api.list_developers ─────────────────

def test_fetch_dev_page_returns_developer_page(wedrowiec):
    """_fetch_dev_page wraps scraper_api.list_developers and returns DeveloperPage."""
    from usi_scrapers.models import DeveloperPage
    fake_page = DeveloperPage(
        developers=[
            {"url": "https://rynekpierwotny.pl/deweloperzy/dom-development-sa/", "name": "Dom Development", "slug": "dom-development-sa"},
        ],
        total_pages=5,
        page=1,
    )
    with patch("python_worker.config.get_scraper_config", return_value=MagicMock()), \
         patch("usi_scrapers.fetcher.Fetcher"), \
         patch("usi_scrapers.api.list_developers", return_value=fake_page):
        result = wedrowiec._fetch_dev_page("rp", 1)
    assert result is not None
    assert result.total_pages == 5
    assert len(result.developers) == 1
    assert result.developers[0]["slug"] == "dom-development-sa"


def test_fetch_dev_page_returns_none_without_config(wedrowiec):
    """Without a valid config, _fetch_dev_page returns None gracefully."""
    with patch("python_worker.config.get_scraper_config", return_value=None):
        result = wedrowiec._fetch_dev_page("rp", 1)
    assert result is None


# ── _register_if_new ──────────────────────────────────────────────────────────
# dev_info format from usi-scrapers list_developers(): {"url", "name", "slug"}

def _empty_known() -> dict:
    return {"rp": set(), "oto": set(), "to": set()}


def test_register_new_dev_from_rp(wedrowiec):
    dev_info = {
        "url": "https://rynekpierwotny.pl/deweloperzy/nowy-deweloper/",
        "name": "Nowy Deweloper",
        "slug": "nowy-deweloper",
    }
    result = wedrowiec._register_if_new("rp", dev_info, _empty_known())
    assert result is True
    created = wedrowiec.dev_dir / "usi_dev_nowy-deweloper.json"
    assert created.exists()
    data = json.loads(created.read_text())
    assert data["portal_mapping"]["rp"]["slug"] == "nowy-deweloper"


def test_register_skips_existing_dev(wedrowiec):
    known = {"rp": {"nowy-deweloper"}, "oto": set(), "to": set()}
    dev_info = {
        "url": "https://rynekpierwotny.pl/deweloperzy/nowy-deweloper/",
        "name": "Nowy Deweloper",
        "slug": "nowy-deweloper",
    }
    result = wedrowiec._register_if_new("rp", dev_info, known)
    assert result is False


def test_register_new_dev_from_oto(wedrowiec):
    dev_info = {
        "url": "https://www.otodom.pl/pl/firmy/deweloperzy/otodom-deweloper-ID555",
        "name": "Otodom Deweloper",
        "slug": "otodom-deweloper",
    }
    result = wedrowiec._register_if_new("oto", dev_info, _empty_known())
    assert result is True
    files = list(wedrowiec.dev_dir.glob("usi_dev_*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["portal_mapping"]["oto"]["agency_id"] == "555"


def test_register_new_dev_from_to(wedrowiec):
    # TO listing doesn't expose names — name=None, use slug as display name
    dev_info = {
        "url": "https://tabelaofert.pl/katalog-firm/deweloperzy/tabela-dev",
        "name": None,
        "slug": "tabela-dev",
    }
    result = wedrowiec._register_if_new("to", dev_info, _empty_known())
    assert result is True
    created = wedrowiec.dev_dir / "usi_dev_tabela-dev.json"
    assert created.exists()


def test_register_updates_known_ids(wedrowiec):
    """known_ids is updated after registration, preventing same-batch duplicates."""
    known = _empty_known()
    dev_info = {
        "url": "https://rynekpierwotny.pl/deweloperzy/alpha/",
        "name": "Alpha Dev",
        "slug": "alpha",
    }
    wedrowiec._register_if_new("rp", dev_info, known)
    assert "alpha" in known["rp"]
    result = wedrowiec._register_if_new("rp", dev_info, known)
    assert result is False


# ── Exploration state persistence ─────────────────────────────────────────────

def _make_dev_page(devs, total_pages=5, page=1):
    from usi_scrapers.models import DeveloperPage
    return DeveloperPage(developers=devs, total_pages=total_pages, page=page)


def test_exploration_state_persists_after_page(wedrowiec):
    """After exploring one page, state file is written with updated page counter."""
    fake_page = _make_dev_page(
        [{"url": "https://rynekpierwotny.pl/deweloperzy/dev-a/", "name": "Dev A", "slug": "dev-a"}],
        total_pages=5,
    )
    with patch.object(wedrowiec, "_fetch_dev_page", return_value=fake_page), \
         patch.object(wedrowiec, "_build_known_dev_ids", return_value={"rp": set(), "oto": set(), "to": set()}), \
         patch.object(wedrowiec, "_register_if_new", return_value=True):
        wedrowiec._explore_one_page("rp")

    state = json.loads(wedrowiec._exploration_file.read_text())
    assert state["rp"]["page"] == 1
    assert state["rp"]["total_seen"] == 1
    assert state["rp"]["new_reg"] == 1
    assert state["rp"]["total_pages"] == 5
    assert "next_at" in state["rp"]


def test_exploration_state_increments_across_pages(wedrowiec):
    fake_page = _make_dev_page(
        [{"url": "https://rynekpierwotny.pl/deweloperzy/dev-x/", "name": "Dev X", "slug": "dev-x"}],
        total_pages=5,
    )
    with patch.object(wedrowiec, "_fetch_dev_page", return_value=fake_page), \
         patch.object(wedrowiec, "_build_known_dev_ids", return_value={"rp": set(), "oto": set(), "to": set()}), \
         patch.object(wedrowiec, "_register_if_new", return_value=False):
        wedrowiec._explore_one_page("rp")
        wedrowiec._explore_one_page("rp")

    state = json.loads(wedrowiec._exploration_file.read_text())
    assert state["rp"]["page"] == 2
    assert state["rp"]["total_seen"] == 2
    assert state["rp"]["new_reg"] == 0


def test_exploration_cycle_resets_when_max_pages_reached(wedrowiec):
    # Put state at total_pages so next call triggers early reset
    state = {"rp": {"page": 5, "total_pages": 5, "next_at": "2026-01-01T00:00:00Z", "total_seen": 150, "new_reg": 3}}
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

