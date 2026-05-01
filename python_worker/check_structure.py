import os
from pathlib import Path

def get_inv_paths(base_dir: Path):
    """Zwraca zbiór ścieżek w formacie 'developer_slug/investment_slug'"""
    paths = set()
    if not base_dir.exists(): 
        return paths
    
    for dev in base_dir.iterdir():
        if dev.is_dir() and not dev.name.startswith('.'):
            for inv in dev.iterdir():
                if inv.is_dir() and not inv.name.startswith('.'):
                    paths.add(f"{dev.name}/{inv.name}")
    return paths

from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR

def main():
    usi_dir = PUBLIC_USI_DIR
    data_dir = USI_DATA_DIR

    print(f"Skanowanie katalogu zdjęć: {usi_dir}")
    usi_paths = get_inv_paths(usi_dir)
    
    print(f"Skanowanie katalogu danych: {data_dir}")
    data_paths = get_inv_paths(data_dir)

    common = usi_paths.intersection(data_paths)
    only_in_usi = usi_paths - data_paths
    only_in_data = data_paths - usi_paths

    print("\n" + "="*50)
    print("RAPORT NAKŁADANIA SIĘ STRUKTUR FOLDERÓW")
    print("="*50)
    print(f"Ilość inwestycji w USI (Zdjęcia)     : {len(usi_paths)}")
    print(f"Ilość inwestycji w USIdata (JSONy)   : {len(data_paths)}")
    print(f"IDEALNE DOPASOWANIE (Wspólne)        : {len(common)}")
    print(f"Tylko w USI (Zdjęcia bez danych)     : {len(only_in_usi)}")
    print(f"Tylko w USIdata (Dane bez zdjęć)     : {len(only_in_data)}")
    print("="*50)

    if only_in_data:
        print(f"\n[!] Przykładowe foldery z DANYMI, do których NIE ZNALEZIONO ZDJĘĆ ({len(only_in_data)}):")
        for p in sorted(list(only_in_data))[:15]: 
            print(f"  - {p}")
            
    if only_in_usi:
        print(f"\n[!] Przykładowe foldery ze ZDJĘCIAMI, do których NIE ZNALEZIONO DANYCH ({len(only_in_usi)}):")
        for p in sorted(list(only_in_usi))[:15]: 
            print(f"  - {p}")

if __name__ == "__main__":
    main()
