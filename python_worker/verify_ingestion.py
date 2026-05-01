
import csv
import json
import os
from pathlib import Path
from python_worker.csv_importer import extract_developer_slug, slugify

USI_DATA_DIR = Path("Public/USIdata")
CSV_PATH = Path("reference-data/coda/USImaster.csv")

def verify():
    if not CSV_PATH.exists():
        print(f"Błąd: Nie znaleziono pliku {CSV_PATH}")
        return

    # 1. Budujemy mapę istniejących plików JSON w bazie
    # Klucz: "developer_slug/investment_slug"
    existing_jsons = {}
    print("Skanowanie bazy JSON...")
    for root, dirs, files in os.walk(USI_DATA_DIR):
        for file in files:
            if file.startswith("usi_") and file.endswith(".json"):
                path = Path(root) / file
                # Wyciągamy dev/inv z bazy
                inv_slug = path.stem.replace("usi_", "")
                dev_slug = path.parent.parent.name
                existing_jsons[f"{dev_slug}/{inv_slug}"] = str(path)

    # 2. Czytamy CSV i sprawdzamy dopasowania
    csv_records = 0
    missing_in_json = []
    found_in_json = 0
    dual_records = 0

    print("Analiza USImaster.csv...")
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_records += 1
            inv_slug = row.get("USIfolder", "").strip()
            if not inv_slug:
                continue
                
            dev_slug = extract_developer_slug(row)
            
            # Sprawdzamy dualność
            has_rp = row.get("rpJSON", "").strip().startswith("{")
            has_oto = row.get("otoJSON", "").strip().startswith("{")
            
            # Scenariusz 1: Sprawdzamy główny rekord (RP lub pojedynczy)
            key = f"{dev_slug}/{inv_slug}"
            if key in existing_jsons:
                found_in_json += 1
                # Usuwamy z mapy "do znalezienia", żeby na końcu zostały tylko te, których nie ma w CSV
                existing_jsons.pop(key, None)
            else:
                missing_in_json.append({"name": row.get("Inwestycja"), "key": key, "type": "Main/RP"})

            # Scenariusz 2: Jeśli dualny, sprawdzamy też wersję -oto
            if has_rp and has_oto:
                dual_records += 1
                oto_key = f"{dev_slug}/{inv_slug}-oto"
                if oto_key in existing_jsons:
                    found_in_json += 1
                    existing_jsons.pop(oto_key, None)
                else:
                    # Nie dodajemy do missing jako błąd krytyczny, bo split_dual mógł nie być jeszcze uruchomiony
                    pass

    # 3. Wyniki
    print("\n--- RAPORT WERYFIKACJI INTEGRALNOŚCI (ZADANIE 37) ---")
    print(f"Wierszy w CSV: {csv_records}")
    print(f"Dopasowanych rekordów w bazie JSON: {found_in_json}")
    print(f"Braki z CSV w bazie JSON: {len(missing_in_json)}")
    print(f"Rekordy w JSON nieobecne w CSV (nowe): {len(existing_jsons)}")
    
    if missing_in_json:
        print("\nPrzykładowe braki (pierwsze 5):")
        for m in missing_in_json[:5]:
            print(f"- {m['name']} ({m['key']})")

    if existing_jsons:
        print("\nPrzykładowe nowe rekordy w JSON (nie ma ich w CSV) - pierwsze 5:")
        for i, (key, path) in enumerate(existing_jsons.items()):
            if i >= 5: break
            print(f"- {key}")

if __name__ == "__main__":
    verify()
