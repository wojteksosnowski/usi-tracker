import json
import pytest
from pathlib import Path
from .csv_importer import (
    slugify,
    extract_developer_slug,
    parse_imglist,
    build_rp_result,
    build_oto_result,
    import_csv,
    audit_dual,
    migrate_dual,
)

CSV_PATH = Path(__file__).parent.parent / "reference-data" / "coda" / "USImaster.csv"
GROUND_TRUTH_PATH = (
    Path(__file__).parent.parent
    / "Public/USIdata/bnm-development-sp-z-oo"
    / "male-wilczyce-etap-9-wroclawski-wilczyce"
    / "app_result_manual_rp_20159.json"
)


# --- slugify ---

def test_slugify_polish_chars():
    assert slugify("Spółka Akcyjna") == "spolka-akcyjna"

def test_slugify_special_company():
    result = slugify("Invest Komfort Spółka Akcyjna Sp.K.")
    assert result == "invest-komfort-spolka-akcyjna-sp-k"

def test_slugify_lowercase_and_hyphens():
    assert slugify("BNM Małe Wilczyce") == "bnm-male-wilczyce"


# --- parse_imglist ---

def test_parse_imglist_comma_sep():
    s = "/Public/USI/dev/inv/a.jpg, /Public/USI/dev/inv/b.jpg"
    result = parse_imglist(s)
    assert result == ["/Public/USI/dev/inv/a.jpg", "/Public/USI/dev/inv/b.jpg"]

def test_parse_imglist_space_sep():
    s = "/Public/USI/dev/inv/a.jpg /Public/USI/dev/inv/b.jpg"
    result = parse_imglist(s)
    assert result == ["/Public/USI/dev/inv/a.jpg", "/Public/USI/dev/inv/b.jpg"]

def test_parse_imglist_filters_non_public():
    s = "/Public/USI/dev/inv/a.jpg, , other/path/b.jpg"
    result = parse_imglist(s)
    assert result == ["/Public/USI/dev/inv/a.jpg"]

def test_parse_imglist_empty():
    assert parse_imglist("") == []
    assert parse_imglist(None) == []


# --- extract_developer_slug ---

def test_extract_slug_no_mapping_returns_none():
    # Without a Konkurenci mapping, unknown developers return None — never slugify
    row = {
        "imgList": "/Public/USI/spravia/supernova-gdynia-redlowo/img.jpg",
        "rpJSON": "",
        "otoJSON": "",
        "Deweloper": "Spravia SA",
    }
    assert extract_developer_slug(row) is None

def test_extract_slug_no_mapping_empty_dev_returns_none():
    row = {
        "imgList": "/Public/USI/spravia/supernova-gdynia-redlowo/img.jpg",
        "rpJSON": "",
        "otoJSON": "",
        "Deweloper": "",
    }
    assert extract_developer_slug(row) is None

def test_extract_slug_from_rp_json_no_mapping_returns_none():
    # Without a Konkurenci mapping, rpJSON vendor slug is NOT used — return None
    rp = {"vendor": {"type": "obj", "value": {"slug": "test-developer"}}}
    row = {"imgList": "", "rpJSON": json.dumps(rp), "otoJSON": "", "Deweloper": "Test Dev"}
    assert extract_developer_slug(row) is None

def test_extract_slug_fallback_returns_none():
    # Polish company names without a Konkurenci entry return None, never slugified
    row = {"imgList": "", "rpJSON": "", "otoJSON": "", "Deweloper": "Deweloper Ąęó Sp. z o.o."}
    assert extract_developer_slug(row) is None


# --- build_rp_result ---

def _make_rp_row(offer_id="99", coords=None, extra_rp=None):
    rp = {
        "name": "Test Inv",
        "address": "ul. Testowa 1",
        "website": "https://test.pl",
        "properties": 50,
    }
    if coords:
        rp["geo_point"] = {"type": "obj", "value": {"type": "Point", "coordinates": {"type": "arr", "value": coords}}}
    if extra_rp:
        rp.update(extra_rp)
    return {
        "rpID": offer_id,
        "USIfolder": "test-investment",
        "Deweloper": "Test Dev",
        "imgList": "/Public/USI/test-developer/test-investment/photo.jpg",
        "Latitude": "52.0",
        "Longitude": "21.0",
        "rpJSON": json.dumps(rp),
        "otoJSON": "",
        "strona_otodom": "",
    }

def test_build_rp_result_coords_order():
    row = _make_rp_row(coords=[17.15, 51.14])
    result = build_rp_result(row)
    assert result["longitude"] == 17.15
    assert result["latitude"] == 51.14

def test_build_rp_result_coords_fallback():
    row = _make_rp_row()  # no geo_point in rpJSON
    result = build_rp_result(row)
    assert result["latitude"] == 52.0
    assert result["longitude"] == 21.0

def test_build_rp_result_no_raw_details():
    row = _make_rp_row()
    result = build_rp_result(row)
    assert "raw_details" not in result

def test_build_rp_result_image_paths():
    row = _make_rp_row()
    result = build_rp_result(row)
    assert "/Public/USI/test-developer/test-investment/photo.jpg" in result["image_paths"]

def test_build_rp_result_source():
    row = _make_rp_row()
    assert build_rp_result(row)["source"] == "rynekpierwotny.pl"

@pytest.mark.skipif(not GROUND_TRUTH_PATH.exists(), reason="ground truth file not present")
def test_build_rp_result_ground_truth():
    import csv as csv_mod
    # Find row with rpID=20159 in the CSV
    row = None
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv_mod.DictReader(f):
            if r.get("rpID", "").strip() == "20159":
                row = r
                break
    assert row is not None, "Row rpID=20159 not found in CSV"

    result = build_rp_result(row)
    truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))

    assert result["developer_slug"] == truth["developer_slug"]
    assert result["source"] == truth["source"]
    assert result["id"] == truth["id"]
    assert abs(result["latitude"] - truth["latitude"]) < 0.001
    assert abs(result["longitude"] - truth["longitude"]) < 0.001


# --- build_oto_result ---

def _make_oto_row(oto_id="4uvqs"):
    ad = {
        "title": "Kamienica Testowa",
        "agency": {"name": "Test Agency", "id": 12345},
        "location": {"mapDetails": {"lat": 51.77, "lon": 19.46}},
        "investmentEstimatedDelivery": {"quarter": 2, "year": 2026},
        "images": [],
    }
    page_props = {"ad": ad}
    return {
        "otoID": oto_id,
        "USIfolder": "kamienica-testowa",
        "Deweloper": "Test Dev",
        "imgList": "/Public/USI/test-dev/kamienica-testowa/img1.jpg",
        "Latitude": "51.77",
        "Longitude": "19.46",
        "rpJSON": "",
        "otoJSON": json.dumps(page_props),
        "strona_otodom": "https://www.otodom.pl/pl/inwestycja/test",
    }

def test_build_oto_result_keys():
    row = _make_oto_row()
    result = build_oto_result(row)
    for key in ["source", "url", "developer_slug", "investment_slug", "title",
                "agency_name", "agency_id", "latitude", "longitude",
                "delivery_quarter", "delivery_year", "images_count", "image_paths"]:
        assert key in result, f"Missing key: {key}"

def test_build_oto_result_source():
    assert build_oto_result(_make_oto_row())["source"] == "otodom.pl"

def test_build_oto_result_no_raw_details():
    assert "raw_details" not in build_oto_result(_make_oto_row())

def test_build_oto_result_coords():
    result = build_oto_result(_make_oto_row())
    assert result["latitude"] == 51.77
    assert result["longitude"] == 19.46


# --- import_csv helpers ---

def _write_csv(csv_path: Path, row: dict) -> None:
    """Write a single-row CSV to csv_path."""
    import csv as csv_mod, io
    buf = io.StringIO()
    w = csv_mod.DictWriter(buf, fieldnames=list(row.keys()))
    w.writeheader()
    w.writerow(row)
    csv_path.write_text(buf.getvalue(), encoding="utf-8")


def _write_konkurenci(csv_dir: Path) -> None:
    """Write a minimal Konkurenci.csv mapping the test developer."""
    import csv as csv_mod
    path = csv_dir / "Konkurenci.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv_mod.DictWriter(f, fieldnames=["Deweloper", "usiFolder", "rpID", "otoID"])
        w.writeheader()
        w.writerow({"Deweloper": "Test Dev", "usiFolder": "test-dev", "rpID": "99", "otoID": "4uvqs"})


# --- import_csv ---

@pytest.mark.skipif(not CSV_PATH.exists(), reason="CSV not present")
def test_import_csv_limit_dry_run():
    results = import_csv(CSV_PATH, "/tmp/usi_test", limit=3, dry_run=True)
    assert len(results) == 3
    # No files should be written
    import os
    assert not Path("/tmp/usi_test").exists() or not any(Path("/tmp/usi_test").iterdir())

@pytest.mark.skipif(not CSV_PATH.exists(), reason="CSV not present")
def test_import_csv_folder_filter():
    results = import_csv(
        CSV_PATH, "/tmp/usi_test", folder_filter="supernova-gdynia-redlowo", dry_run=True
    )
    assert len(results) == 1
    assert results[0]["investment_slug"] == "supernova-gdynia-redlowo"

@pytest.mark.skipif(not CSV_PATH.exists(), reason="CSV not present")
def test_import_csv_result_structure():
    results = import_csv(
        CSV_PATH, "/tmp/usi_test", folder_filter="nowe-kolibki-etap-4-gdynia-orlowo", dry_run=True
    )
    assert len(results) == 1
    r = results[0]["result"]
    assert r["source"] == "rynekpierwotny.pl"
    assert r["id"] == "16401"
    assert results[0]["developer_slug"] == "invest-komfort-spolka-akcyjna-spk"


# --- split_dual ---

def _make_dual_row(**overrides):
    """Row z wypełnionym zarówno rpJSON jak i otoJSON."""
    rp_row = _make_rp_row(offer_id="99")
    oto_row = _make_oto_row(oto_id="4uvqs")
    # RP wins on conflicts (imgList, Latitude, Longitude) — OTO JSON is restored explicitly
    row = {**oto_row, **rp_row}
    row["otoJSON"] = oto_row["otoJSON"]
    row["USIfolder"] = "dual-test-investment"
    row["strona_rynek"] = "https://rynekpierwotny.pl/oferty/test-dev/dual-test-99/"
    row["strona_otodom"] = "https://www.otodom.pl/pl/inwestycja/dual-test"
    row.update(overrides)
    return row


def test_dual_split_rp_result_correct():
    row = _make_dual_row()
    rp_single = build_rp_result(_make_rp_row())
    rp_from_dual = build_rp_result(row)
    assert rp_from_dual["source"] == "rynekpierwotny.pl"
    assert rp_from_dual["latitude"] == rp_single["latitude"]
    assert rp_from_dual["longitude"] == rp_single["longitude"]
    assert rp_from_dual["properties_count"] == rp_single["properties_count"]


def test_dual_split_oto_result_correct():
    row = _make_dual_row()
    oto_single = build_oto_result(_make_oto_row())
    oto_from_dual = build_oto_result(row)
    assert oto_from_dual["source"] == "otodom.pl"
    assert oto_from_dual["latitude"] == oto_single["latitude"]
    assert oto_from_dual["longitude"] == oto_single["longitude"]
    assert oto_from_dual["title"] == oto_single["title"]


def test_dual_split_creates_two_results(tmp_path):
    csv_file = tmp_path / "test.csv"
    _write_csv(csv_file, _make_dual_row())
    _write_konkurenci(tmp_path)

    results = import_csv(csv_file, tmp_path / "out", dry_run=True, split_dual=True)
    assert len(results) == 2
    sources = {r["result"]["source"] for r in results}
    assert sources == {"rynekpierwotny.pl", "otodom.pl"}


def test_single_rp_unaffected_by_split(tmp_path):
    csv_file = tmp_path / "test.csv"
    _write_csv(csv_file, _make_rp_row())
    _write_konkurenci(tmp_path)

    results = import_csv(csv_file, tmp_path / "out", dry_run=True, split_dual=True)
    assert len(results) == 1
    assert results[0]["result"]["source"] == "rynekpierwotny.pl"


def test_single_oto_unaffected_by_split(tmp_path):
    csv_file = tmp_path / "test.csv"
    _write_csv(csv_file, _make_oto_row())
    _write_konkurenci(tmp_path)

    results = import_csv(csv_file, tmp_path / "out", dry_run=True, split_dual=True)
    assert len(results) == 1
    assert results[0]["result"]["source"] == "otodom.pl"


def test_dry_run_dual_no_files_written(tmp_path):
    csv_file = tmp_path / "test.csv"
    _write_csv(csv_file, _make_dual_row())
    _write_konkurenci(tmp_path)
    out_dir = tmp_path / "out"

    results = import_csv(csv_file, out_dir, dry_run=True, split_dual=True)
    assert len(results) == 2
    assert not out_dir.exists()


def test_dual_filenames_written(tmp_path):
    csv_file = tmp_path / "test.csv"
    _write_csv(csv_file, _make_dual_row())
    _write_konkurenci(tmp_path)
    out_dir = tmp_path / "out"

    import_csv(csv_file, out_dir, dry_run=False, split_dual=True)

    dev_slug = "test-dev"
    inv_slug = "dual-test-investment"
    inv_dir = out_dir / dev_slug / inv_slug
    assert (inv_dir / "app_result_rp.json").exists()
    assert (inv_dir / "app_result_oto.json").exists()
    assert (inv_dir / "raw_rp_dual-test-investment.json").exists()
    assert (inv_dir / "raw_oto_dual-test-investment.json").exists()


@pytest.mark.skipif(not CSV_PATH.exists(), reason="CSV not present")
def test_audit_dual_count():
    stats = audit_dual(CSV_PATH)
    assert stats["total_rows"] > 0
    assert stats["dual_url"] > 0
    assert stats["dual_importable"] >= 0
    assert isinstance(stats["by_developer_top10"], list)
    assert isinstance(stats["no_oto_id"], list)


# --- migrate_dual ---

def test_migrate_dual_dry_run_no_rename(tmp_path):
    inv_dir = tmp_path / "dev" / "inv"
    inv_dir.mkdir(parents=True)
    (inv_dir / "rp_details.json").write_text("{}", encoding="utf-8")
    (inv_dir / "oto_details.json").write_text("{}", encoding="utf-8")
    result_data = {"source": "rynekpierwotny.pl", "developer_slug": "dev", "investment_slug": "inv"}
    (inv_dir / "app_result_imported.json").write_text(
        json.dumps(result_data), encoding="utf-8"
    )

    actions = migrate_dual(tmp_path, dry_run=True)
    assert len(actions) == 1
    assert actions[0]["new_file"] == "app_result_imported_rp.json"
    assert (inv_dir / "app_result_imported.json").exists()
    assert not (inv_dir / "app_result_imported_rp.json").exists()


def test_migrate_dual_renames_file(tmp_path):
    inv_dir = tmp_path / "dev" / "inv"
    inv_dir.mkdir(parents=True)
    (inv_dir / "rp_details.json").write_text("{}", encoding="utf-8")
    (inv_dir / "oto_details.json").write_text("{}", encoding="utf-8")
    result_data = {"source": "rynekpierwotny.pl", "developer_slug": "dev", "investment_slug": "inv"}
    (inv_dir / "app_result_imported.json").write_text(
        json.dumps(result_data), encoding="utf-8"
    )

    actions = migrate_dual(tmp_path, dry_run=False)
    assert len(actions) == 1
    assert not (inv_dir / "app_result_imported.json").exists()
    assert (inv_dir / "app_result_imported_rp.json").exists()


def test_migrate_dual_skips_single_portal(tmp_path):
    inv_dir = tmp_path / "dev" / "inv"
    inv_dir.mkdir(parents=True)
    (inv_dir / "rp_details.json").write_text("{}", encoding="utf-8")
    # No oto_details.json — single portal
    result_data = {"source": "rynekpierwotny.pl", "developer_slug": "dev", "investment_slug": "inv"}
    (inv_dir / "app_result_imported.json").write_text(
        json.dumps(result_data), encoding="utf-8"
    )

    actions = migrate_dual(tmp_path, dry_run=True)
    assert len(actions) == 0
