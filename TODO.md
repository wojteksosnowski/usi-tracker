# TODO


### Kamień 19 

# python_worker/investment_identity.py
# ❌ get_investment_resources_by_slug(dev_slug, inv_slug)
# ✅ Tylko get_investment_resources(usi_inv_id)

# Jeśli brakuje ID, fail-fast + log do operacyjnego — nie fallback.

## Kamień 20

# python_worker/services/investment_sync.py
# ❌ Własny scraping dev name:
developer_name = data.get("agency_name")

# ✅ API:
from usi_scrapers.api import identify_developer
name = identify_developer(fetcher, portal, url)

# ❌ Własne zapisy raw:
# ✅ Delegować to usi-scrapers.api.save_raw()


## Kamień 21
Zidentyfikuj skrypty i metody uzywane tylko raz, ktore nie sa wywolywane przez frontend i sluza tylko refactoringowi starych danych.

## Kamień 22
Usi-tracker ma wystaiowe API zeby moglo z niego porzystać UI. Przygotuj test wszystkich endpointów UI.


## Kamień 99 Porządki
Po repo porozrzucane sa pliki nie majace zwiazku z dzialaniem repo. Wyczysc je.
