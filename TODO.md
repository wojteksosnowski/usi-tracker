# TODO

### Kamień 18 

# python_worker/here_maps.py
# → Tego nie powinno być w tracker. Jeśli potrzebne, to jako oddzielny moduł.
# Tracker to FETCH-ONLY. Transformacje (takie jak HERE maps) to obowiązek aplikacji matki.

# python_worker/repair_image_paths.py → Cały plik
# Funkcje _find_by_* to heurystyka. Bez pewnych ID + portal_id = brak gwarancji.

# python_worker/investment_loader.py → find_inv_file()
# Zamienić na ID-based lookup:
# ZAMIAST: find_inv_file(dev_slug, inv_slug)
# POWINNO: identity.get_investment_resources(usi_inv_id) → files["anchor"]

### Kamień 19 

# python_worker/investment_identity.py
# ❌ get_investment_resources_by_slug(dev_slug, inv_slug)
# ✅ Tylko get_investment_resources(usi_inv_id)

# Jeśli brakuje ID, fail-fast + log do operacyjnego — nie fallback.

### Kamień 20

# python_worker/services/investment_sync.py
# ❌ Własny scraping dev name:
developer_name = data.get("agency_name")

# ✅ API:
from usi_scrapers.api import identify_developer
name = identify_developer(fetcher, portal, url)

# ❌ Własne zapisy raw:
# ✅ Delegować to usi-scrapers.api.save_raw()


### Kamień 21
Sprawdź czy skrypty typu migrate* oraz audit* w python_worker/ sa jeszcze uzywane. Zidentyfikuj skrypty i metody uzywane tylko raz, ktore nie sa wywolywane przez frontend i sluza tylko refactoringowi starych danych.

### Kamień 22
Usi-tracker ma wystaiowe API zeby moglo z niego porzystać UI. Przygotuj test wszystkich endpointów UI.


### Kamień 99 Porządki
Po repo porozrzucane sa pliki nie majace zwiazku z dzialaniem repo. Wyczysc je.
