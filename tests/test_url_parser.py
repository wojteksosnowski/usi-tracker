import pytest
from python_worker.url_parser import parse_url


# ── RynekPierwotny ────────────────────────────────────────────────────────────

def test_rp_investment_url():
    url = "https://rynekpierwotny.pl/oferty/acme-dev/projekt-alfa-12345/"
    r = parse_url(url)
    assert r["type"] == "rynekpierwotny"
    assert r["kind"] == "investment"
    assert r["developer_slug"] == "acme-dev"
    assert r["investment_slug"] == "projekt-alfa"
    assert r["offer_id"] == "12345"
    assert r["stage_id"] is None


def test_rp_investment_url_with_stage():
    url = "https://rynekpierwotny.pl/oferty/acme-dev/projekt-alfa-12345/?stage=2"
    r = parse_url(url)
    assert r["stage_id"] == "2"


def test_rp_developer_url():
    url = "https://rynekpierwotny.pl/deweloperzy/acme-dev/"
    r = parse_url(url)
    assert r["type"] == "rynekpierwotny"
    assert r["kind"] == "developer"
    assert r["developer_slug"] == "acme-dev"


# ── Otodom ────────────────────────────────────────────────────────────────────

def test_otodom_investment_inwestycja():
    url = "https://www.otodom.pl/pl/inwestycja/projekt-beta"
    r = parse_url(url)
    assert r["type"] == "otodom"
    assert r["kind"] == "investment"
    assert r["investment_slug"] == "projekt-beta"


def test_otodom_investment_oferta():
    url = "https://www.otodom.pl/pl/oferta/projekt-gamma"
    r = parse_url(url)
    assert r["type"] == "otodom"
    assert r["kind"] == "investment"
    assert r["investment_slug"] == "projekt-gamma"


def test_otodom_developer_url():
    url = "https://www.otodom.pl/pl/firmy/deweloperzy/acme-developer-ID12345"
    r = parse_url(url)
    assert r["type"] == "otodom"
    assert r["kind"] == "developer"
    assert r["agency_id"] == "12345"


# ── TabelaOfert ───────────────────────────────────────────────────────────────

def test_tabelaofert_investment_url():
    url = "https://tabelaofert.pl/inwestycja/projekt-delta,i9876"
    r = parse_url(url)
    assert r["type"] == "tabelaofert"
    assert r["kind"] == "investment"
    assert r["investment_slug"] == "projekt-delta"
    assert r["to_id"] == "9876"


def test_tabelaofert_developer_url():
    url = "https://tabelaofert.pl/katalog-firm/deweloperzy/acme-builders"
    r = parse_url(url)
    assert r["type"] == "tabelaofert"
    assert r["kind"] == "developer"
    assert r["developer_slug"] == "acme-builders"


# ── unknown / unrecognised ────────────────────────────────────────────────────

def test_unknown_domain():
    r = parse_url("https://random-site.com/something")
    assert r["type"] == "unknown"
    assert r["kind"] == "unknown"


def test_rp_url_no_match():
    r = parse_url("https://rynekpierwotny.pl/")
    assert r["type"] == "unknown"


def test_empty_string():
    r = parse_url("")
    assert r["type"] == "unknown"
