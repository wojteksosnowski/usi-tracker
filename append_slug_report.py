import os

with open("slug_usage_report.md", "a", encoding="utf-8") as f:
    f.write("\n## Analiza użycia i nieuprawnione wystąpienia\n")
    f.write("Większość powyższych funkcji używa sluga wyłącznie w warstwie rutingu (np. API blueprinty w `investments.py` i `discovery.py`), co jest dozwolone jako wejście systemu.\n")
    f.write("Nieuprawnione przekazywanie sluga do głębokich warstw (gdzie powinno być używane ID i API `usi-scrapers`) wykryto w:\n")
    f.write("1. `investment_sync.py` -> `_fetch_and_transform_portal_data`\n")
    f.write("2. `investment_loader.py` -> `load_investment`\n")
    f.write("3. `investment_identity.py` -> `get_investment_resources_by_slug`\n")
    f.write("\nWnioski: Głębokie warstwy (usługi) powinny być zrefaktoryzowane, aby operować wyłącznie na system_id i resolverach z biblioteki usi-scrapers.\n")
print("Report updated.")
