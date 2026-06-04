import os

with open("raw_io_usage_report.md", "a", encoding="utf-8") as f:
    f.write("\n## Weryfikacja uprawnień do zapisu plików na dysk\n")
    f.write("Zgodnie z architekturą, wszystkie zapisy danych technicznych i surowych z portali powinny odbywać się przez bibliotekę `usi-scrapers`. Zapisy lokalne w trackerze są dozwolone jedynie dla konfiguracji UI, logów, oraz czystych danych biznesowych w ograniczonym stopniu.\n\n")
    f.write("**Nieuprawnione wystąpienia (do usunięcia lub zamiany na API biblioteki):**\n")
    f.write("1. `investment_editor.py` -> `mark_as_reviewed`, `save_ratings` - modyfikują pliki zamiast używać managera biznesowego z trackera (część I/O powinna być wydzielona).\n")
    f.write("2. `investment_sync.py` -> `_fetch_and_transform_portal_data` - zapis raw jsona, powinno używać `TechnicalDataManager.save_raw_data`.\n")
    f.write("3. `investments.py` -> `download_raw_route` - ręczne zapisywanie pobranych paczek, powinno przejść przez bibliotekę.\n")
    f.write("\n**Wnioski:** Znalezione nieuprawnione zapisy to głównie pozostałości starego kodu pobierającego dane surowe, który nie został zmigrowany do nowego `TechnicalDataManager`.\n")
print("Report updated.")
