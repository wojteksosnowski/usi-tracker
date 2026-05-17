"""
Tests for DeveloperManager.merge_developers and related methods.

All tests use tmp_path for isolation — no real Dropbox data is touched.
Raw JSON files (raw_rp_*.json etc.) are never modified by merge operations.

Architecture notes (Level 2 / Level 3 split):
- Level 2: usi_dev_{usi_dev_id}_{slug}.json — identity/definition only
- Level 3: dev_master_{DM-NNNNN}.json     — merged_from[], dismissed[]
- Log:     dev_log_{slug}.txt              — event history (JSONL)
- merged_from and events are NOT stored in Level 2 anymore.
  Use dm.get_developer() to get the merged view, or read the log/master files directly.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_dev(slug: str, name: str, usi_dev_id: str, portal_mapping: dict = None) -> dict:
    return {
        "developer_slug": slug,
        "name": name,
        "usi_dev_id": usi_dev_id,
        "portal_mapping": portal_mapping or {},
        "audit": {"created_at": datetime.now().isoformat()},
    }


def _write_dev(dev_dir: Path, dev: dict) -> Path:
    """Writes dev file in new canonical format: USIdev/{slug}/usi_dev_{id}_{slug}.json"""
    slug = dev["developer_slug"]
    usi_dev_id = dev.get("usi_dev_id", "DEV-0000")
    subdir = dev_dir / slug
    subdir.mkdir(parents=True, exist_ok=True)
    p = subdir / f"usi_dev_{usi_dev_id}_{slug}.json"
    p.write_text(json.dumps(dev, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _dm(tmp_path: Path):
    from python_worker.developer_manager import DeveloperManager
    data_dir = tmp_path / "USIdata"
    dev_dir  = tmp_path / "USIdev"
    data_dir.mkdir()
    dev_dir.mkdir()
    return DeveloperManager(data_dir, dev_dir)


def _read_dev_log(dev_dir: Path, slug: str) -> list[dict]:
    log_path = dev_dir / slug / f"dev_log_{slug}.txt"
    if not log_path.exists():
        return []
    events = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


# ── get_developer ─────────────────────────────────────────────────────────────

def test_get_developer_from_usitev(tmp_path):
    dm = _dm(tmp_path)
    dev = _make_dev("alpha", "Alpha", "DEV-0001")
    _write_dev(tmp_path / "USIdev", dev)
    result = dm.get_developer("alpha")
    assert result is not None
    assert result["usi_dev_id"] == "DEV-0001"


def test_get_developer_fallback_legacy_flat(tmp_path):
    """Dev file stored flat in USIdev/ (legacy) must be found."""
    dm = _dm(tmp_path)
    dev = _make_dev("beta", "Beta", "DEV-0002")
    # Write to flat legacy path
    (tmp_path / "USIdev" / "usi_dev_beta.json").write_text(
        json.dumps(dev, ensure_ascii=False), encoding="utf-8"
    )
    result = dm.get_developer("beta")
    assert result is not None
    assert result["name"] == "Beta"


def test_get_developer_fallback_legacy_usidata(tmp_path):
    """Dev file stored inside USIdata/{slug}/ (legacy location) must be found."""
    dm = _dm(tmp_path)
    dev = _make_dev("gamma", "Gamma", "DEV-0003")
    legacy_dir = tmp_path / "USIdata" / "gamma"
    legacy_dir.mkdir()
    (legacy_dir / "usi_dev_gamma.json").write_text(
        json.dumps(dev, ensure_ascii=False), encoding="utf-8"
    )
    result = dm.get_developer("gamma")
    assert result is not None
    assert result["name"] == "Gamma"


def test_get_developer_missing_returns_none(tmp_path):
    dm = _dm(tmp_path)
    assert dm.get_developer("no-such-dev") is None


def test_get_developer_returns_merged_from_from_level3(tmp_path):
    """get_developer must include merged_from from the dev_master file."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-co", "Target", "DEV-0040")
    source = _make_dev("source-co", "Source", "DEV-0041")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_by_id("DEV-0040", "DEV-0041")

    view = dm.get_developer("target-co")
    assert any(m["slug"] == "source-co" for m in view.get("merged_from", []))


# ── list_developers ───────────────────────────────────────────────────────────

def test_list_developers_excludes_children(tmp_path):
    """Merged source records must NOT appear in list_developers (determined from dev_master)."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    parent = _make_dev("parent-co", "Parent Co", "DEV-0010")
    child  = _make_dev("child-co",  "Child Co",  "DEV-0011")
    _write_dev(dev_dir, parent)
    _write_dev(dev_dir, child)

    dm.merge_by_id("DEV-0010", "DEV-0011")

    devs = dm.list_developers()
    slugs = [d["developer_slug"] for d in devs]
    assert "parent-co" in slugs
    assert "child-co" not in slugs


# ── merge_developers ──────────────────────────────────────────────────────────

def test_merge_sets_master_id_on_source(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target Dev", "DEV-0020",
                        portal_mapping={"rp": {"id": "111"}})
    source = _make_dev("source-dev", "Source Dev", "DEV-0021",
                        portal_mapping={"oto": {"agency_ids": [42]}})
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    result = dm.merge_by_id("DEV-0020", "DEV-0021")
    assert result is True

    # Source must have master_id pointing to the DM record; no parent_id (DEV→DEV is redundant)
    saved_source_file = next((dev_dir / "source-dev").glob("usi_dev_DEV-0021_*.json"))
    saved_source_raw = json.loads(saved_source_file.read_text())
    assert saved_source_raw.get("master_id"), "source must have master_id"
    assert "parent_id" not in saved_source_raw, "parent_id must not be written (redundant)"

    # DM must list source in merged_from
    target_view = dm.get_developer("target-dev")
    assert any(m["usi_dev_id"] == "DEV-0021" for m in target_view.get("merged_from", []))


def test_merge_does_not_copy_portal_mapping_to_target(tmp_path):
    """portal_mapping must NOT be copied from source to target — 1:1 rule with raw files."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target Dev", "DEV-0020",
                        portal_mapping={"rp": {"id": "111"}})
    source = _make_dev("source-dev", "Source Dev", "DEV-0021",
                        portal_mapping={"oto": {"agency_ids": [42]}})
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_by_id("DEV-0020", "DEV-0021")

    saved_target = dm.get_developer("target-dev")
    assert "rp" in saved_target["portal_mapping"]
    assert "oto" not in saved_target["portal_mapping"], "Source portal_mapping must not be copied to target"


def test_merge_records_merged_from_in_level3(tmp_path):
    """merged_from is stored in dev_master_*.json (Level 3), returned via get_developer."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020")
    source = _make_dev("source-dev", "Source", "DEV-0021")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_by_id("DEV-0020", "DEV-0021")

    # Level 2 must NOT contain merged_from
    level2_file = next((dev_dir / "target-dev").glob("usi_dev_*.json"))
    level2 = json.loads(level2_file.read_text())
    assert "merged_from" not in level2

    # get_developer returns merged view including merged_from from Level 3
    view = dm.get_developer("target-dev")
    assert any(m["slug"] == "source-dev" for m in view.get("merged_from", []))


def test_merge_appends_event_to_log(tmp_path):
    """merge_in event must be written to dev_log_{slug}.txt, not Level 2."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020")
    source = _make_dev("source-dev", "Source", "DEV-0021")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_by_id("DEV-0020", "DEV-0021")

    events = _read_dev_log(dev_dir, "target-dev")
    assert any(e["type"] == "merge_in" and e["source_slug"] == "source-dev" for e in events)

    # Level 2 must NOT contain events[]
    level2_file = next((dev_dir / "target-dev").glob("usi_dev_*.json"))
    level2 = json.loads(level2_file.read_text())
    assert "events" not in level2


def test_merge_removes_suggestion_from_target(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020")
    target["suggestions"] = [{"usi_dev_id": "DEV-0021", "developer_slug": "source-dev",
                               "reason": "test", "score": 1.0}]
    source = _make_dev("source-dev", "Source", "DEV-0021")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_by_id("DEV-0020", "DEV-0021")

    saved_target = dm.get_developer("target-dev")
    remaining = [s["developer_slug"] for s in saved_target.get("suggestions", [])]
    assert "source-dev" not in remaining


def test_merge_normalizes_legacy_source_to_usitev(tmp_path):
    """Source file in USIdata/{slug}/ must be saved to USIdev/{slug}/ after merge."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    data_dir = tmp_path / "USIdata"

    target = _make_dev("target-dev", "Target", "DEV-0020")
    _write_dev(dev_dir, target)

    # Source is in legacy USIdata location
    source = _make_dev("source-dev", "Source", "DEV-0021")
    legacy_dir = data_dir / "source-dev"
    legacy_dir.mkdir()
    legacy_file = legacy_dir / "usi_dev_source-dev.json"
    legacy_file.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")

    dm.merge_by_id("DEV-0020", "DEV-0021")

    # Should now exist in USIdev/source-dev/ with new format
    canonical_dir = dev_dir / "source-dev"
    assert canonical_dir.exists()
    new_format_files = list(canonical_dir.glob("usi_dev_DEV-0021_source-dev.json"))
    assert new_format_files, f"Expected usi_dev_DEV-0021_source-dev.json in {canonical_dir}"

    # Legacy USIdata file should be removed
    assert not legacy_file.exists()

    # master_id must be set on source; no parent_id (redundant)
    saved = dm.get_developer("source-dev")
    assert saved.get("master_id"), "source must have master_id after legacy merge"
    assert "parent_id" not in saved


def test_merge_fails_gracefully_if_source_missing(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-dev", "Target", "DEV-0020")
    _write_dev(dev_dir, target)

    result = dm.merge_by_id("DEV-0020", "DEV-DOES-NOT-EXIST")
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

    dm.merge_by_id("DEV-0020", "DEV-0021")

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

    result = dm.dismiss_suggestion_by_id("DEV-0030", "DEV-0099")
    assert result is True

    saved = dm.get_developer("dev-a")
    assert not any(s["usi_dev_id"] == "DEV-0099" for s in saved.get("suggestions", []))


def test_dismiss_persists_in_level3(tmp_path):
    """Dismissed pair must be stored in dev_master (Level 3) so it survives re-suggest."""
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    dev = _make_dev("dev-a", "Dev A", "DEV-0030")
    dev["suggestions"] = [
        {"usi_dev_id": "DEV-0099", "developer_slug": "some-other", "reason": "x", "score": 0.5}
    ]
    _write_dev(dev_dir, dev)

    dm.dismiss_suggestion_by_id("DEV-0030", "DEV-0099")

    # Level 2 must NOT have events[]
    level2_file = next((dev_dir / "dev-a").glob("usi_dev_*.json"))
    level2 = json.loads(level2_file.read_text())
    assert "events" not in level2

    # Level 3 master file must have the dismissed entry
    master_id = level2.get("master_id")
    assert master_id, "master_id must be set in Level 2 after dismiss"
    master_file = dev_dir / "dev-a" / f"dev_master_{master_id}.json"
    assert master_file.exists()
    master = json.loads(master_file.read_text())
    assert any(d["usi_dev_id"] == "DEV-0099" for d in master.get("dismissed", []))


def test_dismiss_appends_event_to_log(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    dev = _make_dev("dev-a", "Dev A", "DEV-0030")
    dev["suggestions"] = [
        {"usi_dev_id": "DEV-0099", "developer_slug": "some-other", "reason": "x", "score": 0.5}
    ]
    _write_dev(dev_dir, dev)

    dm.dismiss_suggestion_by_id("DEV-0030", "DEV-0099")

    events = _read_dev_log(dev_dir, "dev-a")
    assert any(e["type"] == "dismiss_suggestion" for e in events)


# ── unmerge_developer ─────────────────────────────────────────────────────────

def test_unmerge_removes_from_merged_from(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-co", "Target", "DEV-0040")
    source = _make_dev("source-co", "Source", "DEV-0041")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_by_id("DEV-0040", "DEV-0041")
    result = dm.unmerge_by_id("DEV-0040", "DEV-0041")
    assert result is True

    view = dm.get_developer("target-co")
    assert not any(m["slug"] == "source-co" for m in view.get("merged_from", []))


def test_unmerge_clears_master_id_on_source(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-co", "Target", "DEV-0040")
    source = _make_dev("source-co", "Source", "DEV-0041")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_by_id("DEV-0040", "DEV-0041")
    dm.unmerge_by_id("DEV-0040", "DEV-0041")

    saved_source = dm.get_developer("source-co")
    assert "master_id" not in saved_source
    assert "parent_id" not in saved_source


def test_unmerge_appends_event_to_log(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-co", "Target", "DEV-0040")
    source = _make_dev("source-co", "Source", "DEV-0041")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    dm.merge_by_id("DEV-0040", "DEV-0041")
    dm.unmerge_by_id("DEV-0040", "DEV-0041")

    events = _read_dev_log(dev_dir, "target-co")
    assert any(e["type"] == "unmerge" for e in events)


def test_unmerge_fails_if_not_merged(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    target = _make_dev("target-co", "Target", "DEV-0040")
    source = _make_dev("not-child", "NotChild", "DEV-0042")
    _write_dev(dev_dir, target)
    _write_dev(dev_dir, source)

    result = dm.unmerge_by_id("DEV-0040", "DEV-0042")
    assert result is False


# ── get_total_pending_count ───────────────────────────────────────────────────

def test_get_total_pending_count(tmp_path):
    dm = _dm(tmp_path)
    dev_dir = tmp_path / "USIdev"
    data_dir = tmp_path / "USIdata"

    dev1 = _make_dev("dev-1", "Dev 1", "DEV-001")
    dev2 = _make_dev("dev-2", "Dev 2", "DEV-002")
    _write_dev(dev_dir, dev1)
    _write_dev(dev_dir, dev2)

    d1_dir = dev_dir / "dev-1"
    (d1_dir / "discovery.json").write_text(json.dumps({
        "items": [
            {"portal": "rp", "id": "101", "slug": "inv-101"},
            {"portal": "rp", "id": "102", "slug": "inv-102"}
        ]
    }))

    d2_dir = dev_dir / "dev-2"
    (d2_dir / "discovery.json").write_text(json.dumps({
        "items": [
            {"portal": "oto", "id": "hash999", "slug": "slug-999"}
        ]
    }))

    inv_dir = data_dir / "dev-1" / "inv-101"
    inv_dir.mkdir(parents=True)
    (inv_dir / "usi_inv-101.json").write_text(json.dumps({
        "sources": {"rp": {"id": "101"}}
    }))

    assert dm.get_total_pending_count() == 2


def test_get_total_pending_count_empty(tmp_path):
    dm = _dm(tmp_path)
    assert dm.get_total_pending_count() == 0
