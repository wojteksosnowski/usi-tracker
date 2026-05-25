import os
import sys
from pprint import pprint

# Ensure we are testing from the current venv's usi-scrapers
from usi_scrapers.fetcher import Fetcher
from usi_scrapers.models import ScraperConfig

def run_tests():
    print("Inicjalizacja konfiguracji...")
    # It will pick up the .env from the current directory if needed, or we can just pass an empty one
    config = ScraperConfig(public_dir="/tmp", scraperapi_key=os.environ.get("SCRAPERAPI_KEY", ""))
    fetcher = Fetcher(config)
    
    url = "https://rynekpierwotny.pl/oferty/atal-sa/zerniki-na-novo-iii-wroclaw-zerniki-17906/?show_sold_stage=true"
    print(f"\n--- URL do testów: {url} ---\n")

    # Test 1: Impersonate (curl_cffi)
    print("TEST 1: Impersonate=True, ScraperAPI=False")
    try:
        html1 = fetcher.fetch(url, use_impersonate=True, use_scraperapi=False)
        if html1:
            print(f"[OK] Sukces. Pobrano {len(html1)} bajtów HTML.")
        else:
            print("[FAIL] Zwrócono None.")
    except Exception as e:
        print(f"[ERROR] Wyjątek: {e}")

    # Test 2: ScraperAPI (if key is available)
    print("\nTEST 2: Impersonate=False, ScraperAPI=True")
    if not config.scraperapi_key:
        print("[SKIP] Brak SCRAPERAPI_KEY w zmiennych środowiskowych.")
    else:
        try:
            html2 = fetcher.fetch(url, use_impersonate=False, use_scraperapi=True)
            if html2:
                print(f"[OK] Sukces. Pobrano {len(html2)} bajtów HTML.")
            else:
                print("[FAIL] Zwrócono None.")
        except Exception as e:
            print(f"[ERROR] Wyjątek: {e}")

    # Test 3: Baseline requests (bez bypassu)
    print("\nTEST 3: Standardowa biblioteka requests (baseline)")
    try:
        import requests
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"[OK] Sukces. Pobrano {len(r.text)} bajtów HTML.")
        else:
            print(f"[FAIL] Zwrócono błąd HTTP. Długość: {len(r.text)}")
    except Exception as e:
        print(f"[ERROR] Wyjątek: {e}")

if __name__ == "__main__":
    run_tests()
