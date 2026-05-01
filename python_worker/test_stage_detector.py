import pytest
from .stage_detector import (
    is_multistage,
    extract_groups_id,
    extract_stages,
    build_stage_url,
)
from .url_parser import parse_url

# ─── Fixtures ────────────────────────────────────────────────────────────────

SINGLE_STAGE = {"name": "Apartamenty X", "groups": None}

MULTI_STAGE = {
    "name": "Boska Ksawerowska 2 etap 3",
    "id": 20202,
    "groups": {
        "id": 587,
        "name": "Boska Ksawerowska 2",
        "stages": [
            {
                "id": 1582,
                "name": "Etap 1",
                "current": False,
                "primary": True,
                "sort": 1,
                "status": 1,
                "offer": {
                    "id": 19011,
                    "name": "Boska Ksawerowska 2",
                    "slug": "boska-ksawerowska-2-pabianicki-ksawerow",
                    "vendor": {"slug": "novisa-development-sp-z-oo-sp-j"},
                },
            },
            {
                "id": 1583,
                "name": "Etap 2",
                "current": False,
                "primary": False,
                "sort": 2,
                "status": 1,
                "offer": {
                    "id": 19662,
                    "name": "Boska Ksawerowska 2 etap 2",
                    "slug": "boska-ksawerowska-2-etap-2-lodz-ruda",
                    "vendor": {"slug": "novisa-development-sp-z-oo-sp-j"},
                },
            },
            {
                "id": 1738,
                "name": "Etap 3",
                "current": True,
                "primary": False,
                "sort": 3,
                "status": 1,
                "offer": {
                    "id": 20202,
                    "name": "Boska Ksawerowska 2 etap 3",
                    "slug": "boska-ksawerowska-2-etap-3-lodz-ruda",
                    "vendor": {"slug": "novisa-development-sp-z-oo-sp-j"},
                },
            },
        ],
    },
}

# ─── is_multistage ────────────────────────────────────────────────────────────

def test_single_stage_returns_false():
    assert is_multistage(SINGLE_STAGE) is False


def test_groups_none_returns_false():
    assert is_multistage({}) is False


def test_multistage_returns_true():
    assert is_multistage(MULTI_STAGE) is True


# ─── extract_groups_id ────────────────────────────────────────────────────────

def test_single_stage_groups_id_none():
    assert extract_groups_id(SINGLE_STAGE) is None


def test_multistage_groups_id():
    assert extract_groups_id(MULTI_STAGE) == 587


# ─── extract_stages ──────────────────────────────────────────────────────────

def test_single_stage_empty_list():
    assert extract_stages(SINGLE_STAGE) == []


def test_multistage_extracts_all_three():
    stages = extract_stages(MULTI_STAGE)
    assert len(stages) == 3


def test_stage_fields_present():
    stages = extract_stages(MULTI_STAGE)
    s = stages[0]
    assert s["stage_id"] == 1582
    assert s["offer_id"] == "19011"
    assert s["slug"] == "boska-ksawerowska-2-pabianicki-ksawerow"
    assert s["sort"] == 1
    assert s["primary"] is True
    assert s["current"] is False


def test_current_stage_flagged():
    stages = extract_stages(MULTI_STAGE)
    current = [s for s in stages if s["current"]]
    assert len(current) == 1
    assert current[0]["stage_id"] == 1738


def test_primary_stage_flagged():
    stages = extract_stages(MULTI_STAGE)
    primary = [s for s in stages if s["primary"]]
    assert len(primary) == 1
    assert primary[0]["sort"] == 1


# ─── build_stage_url ─────────────────────────────────────────────────────────

def test_build_url_format():
    url = build_stage_url("novisa-dev", "boska-etap-3-lodz", "20202", 1738)
    assert "?show_sold_stage=true&stage=1738" in url
    assert "novisa-dev" in url
    assert "20202" in url


def test_stage_url_in_extracted_stages():
    stages = extract_stages(MULTI_STAGE)
    for s in stages:
        assert "show_sold_stage=true" in s["url"]
        assert f"stage={s['stage_id']}" in s["url"]


# ─── url_parser ──────────────────────────────────────────────────────────────

def test_url_parser_no_stage():
    result = parse_url("https://rynekpierwotny.pl/oferty/dev-slug/inv-slug-20202/")
    assert result["type"] == "rynekpierwotny"
    assert result["stage_id"] is None
    assert result["show_sold_stage"] is False


def test_url_parser_with_stage():
    result = parse_url(
        "https://rynekpierwotny.pl/oferty/novisa-dev/boska-etap-3-20202/"
        "?show_sold_stage=true&stage=1738"
    )
    assert result["stage_id"] == "1738"
    assert result["show_sold_stage"] is True
    assert result["offer_id"] == "20202"
