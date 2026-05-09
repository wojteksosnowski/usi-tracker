"""
Tests for DeveloperManager.merge_developers and related methods.

All tests use tmp_path for isolation — no real Dropbox data is touched.
Raw JSON files (raw_rp_*.json etc.) are never modified by merge operations.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_dev(slug: str, name: str, usi_dev_id: str, portal_mapping: dict = None,
              parent_id: str = None) -> dict:
    d = {
        "developer_slug": slug,
        "name": name,
        "usi_dev_id": usi_dev_id,
        "portal_mapping": portal_mapping or {},
        "audit": {"created_at": datetime.now().isoformat()},
    }
    if parent_id:
        d["parent_id"] = parent_id
    return d


def _write_dev(dev_dir: Path, dev: dict) -> Path:
    slug = dev["developer_slug"]
    p = dev_dir / f"usi_dev_{slug}.json"
    p.write_text(json.dumps(dev, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _dm(tmp_path: Path):
    from python_worker.developer_manager import DeveloperManager
    data_dir = tmp_path / "USIdata"
    dev_dir  = tmp_path / "USIdev"
    data_dir.mkdir()
    dev_dir.mkdir()
    return DeveloperManager(data_dir, dev_dir)


# ── get_developer ─────────────────────────────────────────────────────────────

def test_get_developer_from_usitev(tmp_path):
    dm = _dm(tmp_path)
    dev = _make_dev("alpha", "Alpha", "DEV-0001")
    _write_dev(tmp_path / "USIdev", dev)
    result = dm.get_developer("alpha")
    assert result is not None
    assert result["usi_dev_id"] == "DEV-0001"


def test_get_developer_fallback_legacy_usidata(tmp_path):
    """Dev file stored inside USIdata/{slug}/ (legacy location) must be found."""
    dm = _dm(tmp_path)
    dev = _make_dev("beta", "Beta", "DEV-0002")
    legacy_dir = tmp_path / "USIdata" / "beta"
    legacy_dir.mkdir()
    (legacy_dir / "usi_dev_beta.json").write_text(
        json.dumps(dev, ensure_ascii=False), encoding="utf-8"
    )
    result = dm.get_developer("beta")
    assert result is not None
    assert result["name"] == "Beta"


def test_get_developer_missing_returns_none(tmp_path):
    dm = _dm(tmp_path)
    assert dm.get_developer("no-such-dev") is None


# ── list_developers ───────────────────────────────────────────────────────────

def test_list_developers_excludes_children(tmp_path):
    """Devs with parent_id set must NOT appear in list_developers."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    parent = _make_dev("parent-co", "Parent Co", "DEV-0010")
    child  = _make_dev("child-co",  "Child Co",  "DEV-0011", parent_id="DEV-0010")
    _write_dev(dev_dir, parent)
    _write_dev(dev_dir, child)

    devs = dm.list_developers()
    slugs = [d["developer_slug"] for d in devs]
    assert "parent-co" in slugs
    assert "child-co" not in slugs


# ── merge_developers ──────────────────────────────────────────────────────────

def test_merge_sets_parent_id_on_source(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target Dev", "DEV-0020",
                        portal_mapping={"rp": {"id": "111"}})
    source = _make_dev("source-dev", "Source Dev", "DEV-0021",
                        portal_mapping={"oto": {"agency_ids": [42]}})
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    result = dm.merge_developers("target-dev", "source-dev")
    assert result is True

    saved_source = json.loads((dev_dir / "usi_dev_source-dev.json").read_text())
    assert saved_source["parent_id"] == "DEV-0020"


def test_merge_enriches_target_portal_mapping(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target Dev", "DEV-0020",
                        portal_mapping={"rp": {"id": "111"}})
    source = _make_dev("source-dev", "Source Dev", "DEV-0021",
                        portal_mapping={"oto": {"agency_ids": [42]}})
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_developers("target-dev", "source-dev")

    saved_target = json.loads((dev_dir / "usi_dev_target-dev.json").read_text())
    assert "rp" in saved_target["portal_mapping"]
    assert "oto" in saved_target["portal_mapping"]


def test_merge_does_not_overwrite_existing_target_portal(tmp_path):
    """Source portal mapping must NOT overwrite target's existing mapping."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020",
                        portal_mapping={"rp": {"id": "ORIGINAL"}})
    source = _make_dev("source-dev", "Source", "DEV-0021",
                        portal_mapping={"rp": {"id": "SHOULD-NOT-WIN"}})
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_developers("target-dev", "source-dev")

    saved_target = json.loads((dev_dir / "usi_dev_target-dev.json").read_text())
    assert saved_target["portal_mapping"]["rp"]["id"] == "ORIGINAL"


def test_merge_records_merged_from_on_target(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020")
    source = _make_dev("source-dev", "Source", "DEV-0021")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_developers("target-dev", "source-dev")

    saved_target = json.loads((dev_dir / "usi_dev_target-dev.json").read_text())
    merged_from = saved_target.get("merged_from", [])
    assert any(m["slug"] == "source-dev" for m in merged_from)


def test_merge_appends_event_to_target(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020")
    source = _make_dev("source-dev", "Source", "DEV-0021")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_developers("target-dev", "source-dev")

    saved_target = json.loads((dev_dir / "usi_dev_target-dev.json").read_text())
    events = saved_target.get("events", [])
    assert any(e["type"] == "merge_in" and e["source_slug"] == "source-dev" for e in events)


def test_merge_removes_suggestion_from_target(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020")
    target["suggestions"] = [{"usi_dev_id": "DEV-0021", "developer_slug": "source-dev",
                               "reason": "test", "score": 1.0}]
    source = _make_dev("source-dev", "Source", "DEV-0021")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_developers("target-dev", "source-dev")

    saved_target = json.loads((dev_dir / "usi_dev_target-dev.json").read_text())
    remaining = [s["developer_slug"] for s in saved_target.get("suggestions", [])]
    assert "source-dev" not in remaining


def test_merge_normalizes_legacy_source_to_usitev(tmp_path):
    """Source file in USIdata/{slug}/ must be moved to USIdev/ after merge."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    data_dir = tmp_path / "USIdata"

    target = _make_dev("target-dev", "Target", "DEV-0020")
    _write_dev(dev_dir, target)

    # Source is in legacy location
    source = _make_dev("source-dev", "Source", "DEV-0021")
    legacy_dir = data_dir / "source-dev"
    legacy_dir.mkdir()
    legacy_file = legacy_dir / "usi_dev_source-dev.json"
    legacy_file.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")

    dm.merge_developers("target-dev", "source-dev")

    # Should now exist in USIdev/
    canonical = dev_dir / "usi_dev_source-dev.json"
    assert canonical.exists()
    # Legacy file should be removed
    assert not legacy_file.exists()
    # parent_id must be set
    saved = json.loads(canonical.read_text())
    assert saved["parent_id"] == "DEV-0020"


def test_merge_fails_gracefully_if_source_missing(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020")
    _write_dev(dev_dir, target)

    result = dm.merge_developers("target-dev", "no-such-source")
    assert result is False


def test_merge_source_raw_files_untouched(tmp_path):
    """Raw portal JSONs (raw_rp_*.json etc.) must NEVER be modified by merge."""
    dm = _dm(tmp_path)
    dev_dir  = tmp_path / "USIdev"
    data_dir = tmp_path / "USIdata"

    target = _make_dev("target-dev", "Target", "DEV-0020")
    source = _make_dev("source-dev", "Source", "DEV-0021")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    # Create a fake raw file under source's investment folder
    inv_dir = data_dir / "source-dev" / "some-investment"
    inv_dir.mkdir(parents=True)
    raw_file = inv_dir / "raw_rp_some-investment.json"
    raw_content = '{"portal": "rp", "id": "99999"}'
    raw_file.write_text(raw_content, encoding="utf-8")

    dm.merge_developers("target-dev", "source-dev")

    # Raw file must be byte-for-byte identical after merge
    assert raw_file.read_text(encoding="utf-8") == raw_content


# ── dismiss_suggestion ────────────────────────────────────────────────────────

def test_dismiss_removes_suggestion(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    dev = _make_dev("dev-a", "Dev A", "DEV-0030")
    dev["suggestions"] = [
        {"usi_dev_id": "DEV-0099", "developer_slug": "some-other", "reason": "x", "score": 0.5}
    ]
    _write_dev(dev_dir, dev)

    result = dm.dismiss_suggestion("dev-a", "DEV-0099")
    assert result is True

    saved = json.loads((dev_dir / "usi_dev_dev-a.json").read_text())
    assert not any(s["usi_dev_id"] == "DEV-0099" for s in saved.get("suggestions", []))


def test_dismiss_appends_event(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    dev = _make_dev("dev-a", "Dev A", "DEV-0030")
    dev["suggestions"] = [
        {"usi_dev_id": "DEV-0099", "developer_slug": "some-other", "reason": "x", "score": 0.5}
    ]
    _write_dev(dev_dir, dev)

    dm.dismiss_suggestion("dev-a", "DEV-0099")

    saved = json.loads((dev_dir / "usi_dev_dev-a.json").read_text())
    assert any(e["type"] == "dismiss_suggestion" for e in saved.get("events", []))
