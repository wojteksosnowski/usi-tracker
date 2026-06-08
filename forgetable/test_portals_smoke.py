import sys
import os
from pathlib import Path
import logging
import json

# Konfiguracja logowania - wyciszamy zbędne info, zostawiamy błędy i nasze komunikaty
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("smoke_test")
logger.setLevel(logging.INFO)

# Setup path
_BASE_DIR = Path.cwd()
sys.path.insert(0, str(_BASE_DIR))
lib_path = str(_BASE_DIR.parent / "usi-scrapers")
if os.path.exists(lib_path):
    sys.path.insert(0, lib_path)

from python_worker.config import get_shared_scraper_gateway

def smoke_test():
    gateway = get_shared_scraper_gateway()
    
    # Konfiguracja testu: (klucz_discovery, klucz_ingest, nazwa_ladna)
    test_configs = [
        ("rp", "rp", "RynekPierwotny"),
        ("otodom", "oto", "Otodom"),
        ("to", "to", "TabelaOfert")
    ]
    
    results_summary = []

    for disc_key, ingest_key, label in test_configs:
        print(f"\n" + "="*50)
        print(f" TEST SMOKE: {label.upper()} ")
        print("="*50)
        
        status = {"portal": label, "discovery": "FAILED", "ingest": "FAILED", "error": None}
        
        try:
            # 1. DISCOVERY
            print(f"[*] Krok 1: Discovery (pobieranie listy najnowszych)...")
            items = gateway.discover_investments(disc_key, limit=1)
            
            if not items:
                print(f"[-] BŁĄD: Nie znaleziono żadnej inwestycji na {label}.")
                status["error"] = "No items found during discovery"
                results_summary.append(status)
                continue
            
            status["discovery"] = "OK"
            first_item = items[0]
            name = first_item.get('name', 'Nieznana')
            url = first_item.get('url')
            item_id = first_item.get('id')
            
            print(f"    + Znaleziono: '{name}'")
            print(f"    + ID: {item_id}")
            print(f"    + URL: {url}")
            
            # 2. INGESTION
            print(f"[*] Krok 2: Ingest (pobieranie pełnych danych surowych)...")
            # Próbujemy pobrać po URL (tryb Ingest) lub ID (tryb Refresh)
            if url:
                print(f"    > Wywołuję ingest_investment_by_url('{ingest_key}', ...)")
                res = gateway.ingest_investment_by_url(ingest_key, url)
            else:
                print(f"    > Wywołuję refresh_investment_by_id('{ingest_key}', '{item_id}')")
                res = gateway.refresh_investment_by_id(ingest_key, str(item_id))
            
            if res and "error" not in res:
                print(f"[+] SUKCES: Pomyślnie pobrano dane dla {label}.")
                status["ingest"] = "OK"
                
                # Sprawdzenie czy dane mają sens
                data_size = len(json.dumps(res))
                print(f"    + Rozmiar JSON: {data_size} bajtów")
                print(f"    + Klucze danych: {list(res.keys())[:8]}...")
            else:
                error_msg = res.get("error", "Nieznany błąd API") if res else "Brak odpowiedzi z bramy"
                print(f"[-] BŁĄD: Pobieranie danych dla {label} nie powiodło się.")
                print(f"    + Szczegóły: {error_msg}")
                status["error"] = error_msg
                
        except Exception as e:
            print(f"[-] BŁĄD KRYTYCZNY dla {label}: {str(e)}")
            status["error"] = str(e)
            
        results_summary.append(status)

    # Podsumowanie końcowe
    print("\n" + "="*50)
    print(" PODSUMOWANIE TESTU SMOKE ")
    print("="*50)
    all_ok = True
    for r in results_summary:
        line = f"{r['portal']:<15} | Discovery: {r['discovery']:<10} | Ingest: {r['ingest']:<10}"
        if r['error']:
            line += f" | Error: {r['error']}"
            all_ok = False
        print(line)
    
    if all_ok:
        print("\n[!!!] SYSTEM USI-SCRAPERS DZIAŁA POPRAWNIE NA WSZYSTKICH PORTALACH [!!!]")
    else:
        print("\n[???] WYKRYTO PROBLEMY W DZIAŁANIU BIBLIOTEKI [???]")

if __name__ == "__main__":
    smoke_test()
