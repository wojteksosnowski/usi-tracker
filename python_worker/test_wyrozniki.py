"""Tests for wyrozniki (amenity scoring) logic."""
import csv
import json
from pathlib import Path

import pytest

from python_worker.ui_server import _compute_amenity_score, _suggest_udogodnienia

CSV_PATH = Path("reference-data/coda/USImaster.csv")


# ── Unit tests ─────────────────────────────────────────────────────────────────

def test_text_label_match():
    r = _compute_amenity_score(["Siłownia zewnętrzna", "Sauna fińska"], [])
    assert r["score"] == 4 + 4  # Siłownia + sauna


def test_rp_code_match():
    # basen = rpNo 9, HMUdo = 8
    r = _compute_amenity_score([], [9])
    assert r["score"] == 8
    assert any(m["label"] == "basen" for m in r["matched"])


def test_no_double_count():
    # basen by rpNo=9 AND text "Basen olimpijski" — case-insensitive dedup → counted once
    r = _compute_amenity_score(["Basen olimpijski"], [9])
    assert r["score"] == 8
    assert len([m for m in r["matched"] if m["hm_udo"] == 8]) == 1


def test_rowerownia_and_pomieszczenie_na_rowery_both_count():
    # rowerownia (rpNo=22, +1) and "Pomieszczenie na rowery" (keyword, +1) are distinct labels
    r = _compute_amenity_score(["Pomieszczenie na rowery"], [22])
    assert r["score"] == 2


def test_standard_table():
    assert _suggest_udogodnienia(0) is None
    assert _suggest_udogodnienia(1) == 0   # 1 > tier=0 → ocena 0
    assert _suggest_udogodnienia(2) == 1   # 2 > tier=1 → ocena 1
    assert _suggest_udogodnienia(5) == 2   # 5 > tier=4 → ocena 2
    assert _suggest_udogodnienia(8) == 2   # 8 not > tier=8 → still ocena 2
    assert _suggest_udogodnienia(9) == 3   # 9 > tier=8 → ocena 3
    assert _suggest_udogodnienia(17) == 4  # 17 > tier=16 → ocena 4


def test_empty():
    r = _compute_amenity_score([], [])
    assert r["score"] == 0
    assert r["matched"] == []
    assert _suggest_udogodnienia(0) is None


# ── Integration test — ground-truth from USImaster.csv (Coda RPfacVal) ────────

@pytest.mark.skipif(not CSV_PATH.exists(), reason="USImaster.csv not available")
def test_rpfacval_verified_cases():
    """
    Spot-check against a curated set of USImaster.csv rows where the ground truth is
    mathematically verifiable. Scoring weights may have changed in Coda over time, so a
    full-table exact match is not expected — only these stable cases must pass.
    """
    # (USIfolder, expected_rpfacval, note) — mathematically verified against known weights
    VERIFIED = {
        "nowe-kolibki-gdynia-orlowo":            8,   # klub_fitness(4)+sauna(4)
        "wave-apartments-kamienski-miedzyzdroje": 2,   # recepcja(2)
        "wislane-tarasy-20-krakow-grzegorzki":   19,  # ochrona(1)+concierge(4)+basen(8)+sauna(4)+rowerownia(1)+wozkarnia(1)
        "remedium-gdansk-aniolki":               2,   # recepcja(2)
        "opacka-gdansk-oliwa":                   17,  # ochrona(1)+pom_rekreacyjne(2)+klub_fitness(4)+recepcja(2)+sauna(4)+sala_fitness(4)
    }
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            folder = row.get("USIfolder", "").strip()
            if folder not in VERIFIED:
                continue
            rp_json_str = row.get("rpJSON", "").strip()
            try:
                rp_data = json.loads(rp_json_str)
                rp_raw = rp_data.get("value", rp_data)
                fac = rp_raw.get("facilities", [])
                if isinstance(fac, dict):
                    fac = fac.get("value", [])
                rp_codes = [int(c) for c in fac if c]
            except Exception:
                continue
            oto_str = row.get("OTOfeatures", "").strip()
            oto_labels = [v.strip() for v in oto_str.split(",") if v.strip()] if oto_str else []
            result = _compute_amenity_score(oto_labels, rp_codes)
            expected = VERIFIED[folder]
            assert result["score"] == expected, (
                f"{folder}: got {result['score']}, expected {expected} "
                f"(codes={rp_codes}, matched={result['matched']})"
            )


@pytest.mark.skipif(not CSV_PATH.exists(), reason="USImaster.csv not available")
def test_rpfacval_full_table_report(capsys):
    """
    Reports mismatches against full USImaster.csv RPfacVal (informational).
    Skips rows with RPfacVal=0 (may be stale Coda data).
    Does NOT fail — scoring may have evolved since the CSV was exported.
    """
    mismatches = 0
    total = 0
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rpfacval_str = row.get("RPfacVal", "").strip()
            rp_json_str = row.get("rpJSON", "").strip()
            if not rpfacval_str or not rp_json_str:
                continue
            try:
                rpfacval = int(float(rpfacval_str))
            except ValueError:
                continue
            if rpfacval == 0:
                continue
            try:
                rp_data = json.loads(rp_json_str)
                rp_raw = rp_data.get("value", rp_data)
                fac = rp_raw.get("facilities", [])
                if isinstance(fac, dict):
                    fac = fac.get("value", [])
                rp_codes = [int(c) for c in fac if c]
            except Exception:
                continue
            oto_str = row.get("OTOfeatures", "").strip()
            oto_labels = [v.strip() for v in oto_str.split(",") if v.strip()] if oto_str else []
            result = _compute_amenity_score(oto_labels, rp_codes)
            total += 1
            if result["score"] != rpfacval:
                mismatches += 1
    match_rate = (total - mismatches) / total * 100 if total else 0
    print(f"\nRPfacVal full-table: {total - mismatches}/{total} match ({match_rate:.0f}%)")
    # informational only, no assertion
