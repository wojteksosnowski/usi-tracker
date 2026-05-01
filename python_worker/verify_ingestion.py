
import csv
import json
import os
import sys
from pathlib import Path

# Dodajemy bieżący katalog do ścieżki, aby importy działały
sys.path.append(os.getcwd())

from python_worker.csv_importer import extract_developer_slug, slugify, extract_native_slugs

USI_DATA_DIR = Path("Public/USIdata")
CSV_PATH = Path("reference-data/coda/USImaster.csv")

def verify_deep():
    if not CSV_PATH.exists():
        print(f"Błąd: Nie znaleziono pliku {CSV_PATH}")
        return

    existing_jsons = {}
    print("Skanowanie bazy JSON (Public/USIdata)...")
    for root, dirs, files in os.walk(USI_DATA_DIR):
        for file in files:
            if file.startswith("usi_") or file.endswith("app_result_imported.json"):
                path = Path(root) / file
                # Wyciągamy dev/inv z bazy na podstawie struktury folderów
                # Public/USIdata/{dev_slug}/{inv_slug}/...
                parts = path.parts
                try:
                    usi_idx = parts.index("USIdata")
                    dev_slug = parts[usi_idx + 1]
                    inv_slug = parts[usi_idx + 2]
                    existing_jsons[f"{dev_slug}/{inv_slug}"] = path.parent
                except (ValueError, IndexError):
                    continue

    csv_records = 0
    found_in_json = 0
    missing_in_json = []
    data_mismatches = []
    dual_ok = 0
    dual_fail = 0

    print(f"Analiza {CSV_PATH}...")
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_records += 1
            dev_slug = extract_developer_slug(row)
            inv_name = row.get("Inwestycja", "Unknown")
            
            has_rp = row.get("rpJSON", "").strip().startswith("{")
            has_oto = row.get("otoJSON", "").strip().startswith("{")
            
            rp_native, oto_native = extract_native_slugs(row)

            # 1. Weryfikacja RP (jeśli obecne)
            if has_rp:
                key = f"{dev_slug}/{rp_native}"
                if key in existing_jsons:
                    found_in_json += 1
                    # Sprawdzamy czy deweloper w JSON zgadza się z CSV (źródło prawdy)
                    # Uwaga: sprawdzamy plik app_result_imported.json lub usi_{slug}.json
                    res_path = existing_jsons[key] / "app_result_imported.json"
                    if not res_path.exists():
                        res_path = existing_jsons[key] / f"usi_{rp_native}.json"
                    
                    if res_path.exists():
                        try:
                            with open(res_path, 'r', encoding='utf-8') as jf:
                                data = json.load(jf)
                                if slugify(data.get('developer', '')) != dev_slug:
                                    data_mismatches.append(f"{key}: Dev mismatch (JSON: {data.get('developer')} vs CSV Slug: {dev_slug})")
                        except: pass
                    
                    # Jeśli to był rekord dualny, sprawdzamy czy OTO też jest
                    if has_oto:
                        oto_key = f"{dev_slug}/{oto_native}"
                        if oto_key in existing_jsons:
                            dual_ok += 1
                            found_in_json += 1
                        else:
                            dual_fail += 1
                            missing_in_json.append({"name": f"{inv_name} (OTO-part)", "key": oto_key})
                else:
                    missing_in_json.append({"name": f"{inv_name} (RP-part)", "key": key})
            
            # 2. Weryfikacja tylko OTO (jeśli nie było RP)
            elif has_oto:
                key = f"{dev_slug}/{oto_native}"
                if key in existing_jsons:
                    found_in_json += 1
                else:
                    missing_in_json.append({"name": f"{inv_name} (OTO-only)", "key": key})

    print("\n" + "="*50)
    print("      RAPORT GŁĘBOKIEJ WERYFIKACJI (ZADANIE 37) - NATIVE SLUGS")
    print("="*50)
    print(f"Wierszy w CSV:                 {csv_records}")
    print(f"Prawidłowo znalezione w JSON:  {found_in_json}")
    print(f"Braki (zgodnie z CSV):         {len(missing_in_json)}")
    print(f"Błędy dewelopera (Mismatch):   {len(data_mismatches)}")
    print("-" * 50)
    print(f"Dualne rekordy (Split Check):  OK: {dual_ok} | FAIL: {dual_fail}")
    print("="*50)
    
    if missing_in_json:
        print(f"\nPRZYKŁADOWE BRAKI ({len(missing_in_json)}):")
        for m in missing_in_json[:10]:
            print(f"  - {m['name']} ({m['key']})")

if __name__ == "__main__":
    verify_deep()
