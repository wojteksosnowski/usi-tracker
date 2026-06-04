# TODO


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
Zaktualizuj usi-scrapers. Nowe API pozwala na fallback w przypadku blednych sciezek obrazow.

## Kamień 23
Usi-tracker ma wystaiowe API zeby moglo z niego porzystać UI. Przygotuj test wszystkich endpointów UI.


## Kamień 99 Porządki
Po repo porozrzucane sa pliki nie majace zwiazku z dzialaniem repo. Wyczysc je.
