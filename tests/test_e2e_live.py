import pytest
import json
import os
from pathlib import Path
from usi_scrapers.api import list_investments, process_batch_ingest
from usi_scrapers.models import ScraperConfig
from usi_scrapers.fetcher import Fetcher

@pytest.fixture
def scraper_config(tmp_path):
    """Sets up a direct ScraperConfig matching the usi-scrapers internal test pattern."""
    # Try loading from .env files first
    from dotenv import load_dotenv
    load_dotenv() # root .env
    load_dotenv("python_worker/.env.local")
    
    api_key = os.getenv("SCRAPERAPI_API_KEY")

    if not api_key:
        pytest.skip("SCRAPERAPI_API_KEY not found in environment or .env.local")

    public_dir = tmp_path / "tmp_live_public"
    public_dir.mkdir()

    return ScraperConfig(
        public_dir=public_dir,
        scraperapi_key=api_key,
        otodom_discovery_urls=["https://www.otodom.pl/pl/wyniki/sprzedaz/inwestycja/cala-polska"],
        to_discovery_urls=["https://tabelaofert.pl/nowe-mieszkania"]
    )

@pytest.fixture
def scraper_fetcher(scraper_config):
    return Fetcher(scraper_config)

@pytest.mark.live
@pytest.mark.parametrize("portal", ["rp", "otodom", "tabelaofert"])
def test_live_scrapers_api_direct(scraper_config, scraper_fetcher, portal):
    """
    Direct library test: Validates discovery and ingestion via usi-scrapers API.
    Mirrors the internal 'live verification' script.
    """
    # 1. Discover fresh URL
    print(f"\n[LIVE] Discovering fresh {portal} URL via general discovery...")
    items = list_investments(scraper_config, scraper_fetcher, portal, identifier=None)
    
    assert items, f"FAILED: No investments found for {portal} via general discovery"
    
    fresh_url = items[0].get("url")
    assert fresh_url, f"FAILED: Discovery item missing URL: {items[0]}"
    print(f"[LIVE] Found fresh URL: {fresh_url}")

    # 2. Ingest via batch process (simulating real pipeline)
    print(f"[LIVE] Ingesting via process_batch_ingest...")
    results = process_batch_ingest(scraper_config, scraper_fetcher, portal, [fresh_url])
    
    assert results and results[0], f"FAILED: Ingestion produced no results for {portal}"
    
    # 3. Verify physical files on disk
    # The library saves raw_*.json in {public_dir}/USIdata/{dev_slug}/{inv_slug}/
    # Or for developers: {public_dir}/USIdev/{dev_slug}/
    
    portal_short = "oto" if portal == "otodom" else ("to" if portal == "tabelaofert" else "rp")
    
    raw_files = list(scraper_config.public_dir.rglob(f"raw_{portal_short}_*.json"))
    assert len(raw_files) >= 1, f"FAILED: No raw {portal} file found on disk in {scraper_config.public_dir}"
    
    latest_file = max(raw_files, key=lambda p: p.stat().st_mtime)
    print(f"[LIVE] Verifying structure of newest file: {latest_file.name}")
    
    data = json.loads(latest_file.read_text(encoding="utf-8"))
    assert data, f"FAILED: File {latest_file} is empty"
    
    # 4. Portal-specific structural verification
    if portal == "otodom":
        # Check for __NEXT_DATA__ equivalent structure if it's an HTML-scraped payload
        # or check the specific ad data if it was fetched via API.
        # Based on user script, we look for 'props.pageProps'
        if "props" in data:
            print(f"[LIVE] SUCCESS: {latest_file.name} contains 'props' structure.")
            assert "pageProps" in data["props"], f"FAILED: 'pageProps' missing from {latest_file.name}"
        else:
            # If it's pure API response (not __NEXT_DATA__), check for typical keys
            print(f"[LIVE] Checking for non-props keys: {list(data.keys())[:5]}")
            assert "name" in data or "id" in data or "id" in data.get("props", {}).get("pageProps", {}).get("ad", {}), \
                f"FAILED: {latest_file.name} lacks identifying keys"

    if portal == "tabelaofert":
        # Verify TO specifics (like klient-id or specific TO keys)
        # Note: Response might be a developer profile or investment details
        assert any(k in data for k in ["to_id", "klient-id", "klient_id", "name", "nazwa"]), f"FAILED: TabelaOfert structure unknown: {list(data.keys())}"
        print(f"[LIVE] SUCCESS: TabelaOfert raw file looks valid.")

    if portal == "rp":
        # Verify RP specifics
        assert "id" in data or "name" in data or "vendor_id" in data
        print(f"[LIVE] SUCCESS: RynekPierwotny raw file looks valid.")
