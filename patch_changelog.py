import re

file_path = "CHANGELOG.md"
with open(file_path, "r") as f:
    content = f.read()

new_changelog = """## Wersja 0.9.93 — UI fixes i stabilizacja synchronizacji — 2026-06-14

### Zmieniono
- **Priorytety Identyfikatorów**: W `investment_sync.py` w `IDENTIFIER_PRIORITIES` zmieniono priorytet z `id` na `url`. Rozwiązuje to problem błędu "Brak danych do odświeżenia" w sytuacjach, gdy portale zmieniają numeryczne identyfikatory. System wyciąga nowe ID dynamicznie z URL'a.
- **Odświeżanie "W okolicy"**: W module `NearbyInvestmentsModule` w Reactcie dodano dyskretny przycisk pozwalający przeliczyć ręcznie okoliczne inwestycje. Po kliknięciu wywoływany jest punkt dostępowy API `/api/investment/{id}/recalc-nearby`.
- **Renderowanie oceny "Zero"**: Poprawiono błąd maskujący ocenę "0" jako wartość "Brak oceny" (`null` lub `undefined`) w komponencie okolicy. Wartość `0` jest teraz poprawnie respektowana.
- **Synchronizacja globalnego indeksu**: Zmodyfikowano `invalidate_cache()` w `InvestmentService` dodając rygorystyczny krok synchronizacji. Dotychczas zapis ocen wywoływał jedynie czyszczenie lokalnego cache, przez co `_index.json` pozostawał przestarzały. Obecnie zmiany zapisywane są również za pośrednictwem `get_investment_index().add_or_update()`.

### Wnioski ze zmian
- Caching asynchroniczny: Brak odpowiedniej propagacji zmian w systemach opartych na wielu warstwach cacheowania (frontend bus, RAM serwisu, plik dyskowy) prowadzi do desynchronizacji. Bezpieczne systemy powinny natychmiast odświeżać lub inwalidować globalny "SSOT" (Single Source of Truth).
- Trwałość Identyfikatorów: Numerowane ID na portalach są kruche i potrafią ulec zmianie. Traktowanie pełnego adresu URL jako stałej referencji (z ewentualną ewaluacją identyfikatora podczas pobierania) to bezpieczniejsza strategia architektoniczna.

"""

content = new_changelog + content

with open(file_path, "w") as f:
    f.write(content)

print("Changelog updated!")
