import logging
from python_worker.investment_index import get_investment_index
from python_worker.main import update_investment
from python_worker.api.utils import _load_investment

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("rebuild_to")

def main():
    index = get_investment_index()
    all_invs = index.get_all()
    count = 0
    errors = 0
    
    print("Zbieranie inwestycji do przebudowy...")
    targets = []
    for inv in all_invs:
        system_id = inv.get("usi_inv_id")
        if not system_id:
            continue
            
        dev_slug = inv.get("developer_slug")
        inv_slug = inv.get("investment_slug")
        if not dev_slug or not inv_slug:
            continue
            
        full_inv = _load_investment(system_id, fast_index=False)
        if not full_inv:
            continue
            
        sources = full_inv.get("sources", {})
        if "to" in sources:
            targets.append((dev_slug, inv_slug, system_id))
            
    total = len(targets)
    print(f"Znaleziono {total} inwestycji z TabelaOfert do przebudowy.")
    
    for i, (dev_slug, inv_slug, system_id) in enumerate(targets):
        if i % 100 == 0:
            print(f"Postęp: {i}/{total} ({(i/total)*100:.1f}%)")
        
        try:
            success = update_investment(dev_slug, inv_slug, use_local_raw=True)
            if success:
                count += 1
            else:
                errors += 1
        except Exception as e:
            logger.error(f"Error rebuilding {dev_slug}/{inv_slug}: {e}")
            errors += 1

    print(f"\nPrzebudowano pomyślnie: {count}")
    print(f"Błędy: {errors}")
    
    print("Przebudowuję główny indeks...")
    index.rebuild()
    print("Gotowe.")

if __name__ == "__main__":
    main()
