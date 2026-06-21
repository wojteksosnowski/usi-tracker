# Analiza wydajności agenta: Dlaczego rozwiązywanie problemów zajmuje dużo czasu i tokenów?

Poniżej zebrano główne przyczyny, dla których agenty LLM wpadają w pętle, marnują tokeny oraz zbyt długo rozwiązują z pozoru proste problemy. Wnioski te posłużą jako fundament do zbudowania skilla (np. `efficiency-protocol`), który narzuci agentowi optymalny workflow.

## 1. Główne przyczyny marnowania czasu i tokenów

### A. Statyczne śledzenie kodu zamiast izolowanych testów (Over-thinking)
Agent często próbuje w pamięci (w bloku `thought`) prześledzić logikę przepływu danych przez 5 różnych plików (np. od API, przez Serwis, Repo, aż po pliki JSON), zamiast napisać prosty, 3-linijkowy skrypt testowy w Pythonie, który natychmiast pokazałby wartość zwracaną przez konkretną funkcję. To prowadzi do błędnych założeń i konieczności czytania kolejnych plików.

### B. Błędy uciekania znaków (Escaping) w poleceniach Bash
Agent uwielbia pisać szybkie skrypty Pythonowe jako "one-linery" w terminalu (np. `python -c 'print(f"Dane: {data.get(\"key\")}")'`). Często prowadzi to do błędów składniowych (`SyntaxError`) związanych z cudzysłowami wewnątrz f-stringów w Bashu. Wygenerowanie błędu oznacza stratę całego kroku (turn) i konieczność ponawiania akcji.

### C. Przeładowanie kontekstu (Context Bloat)
Zamiast precyzyjnego wyszukiwania (`grep_search`) lub czytania tylko fragmentów pliku (`view_file` ze wskazanymi liniami), agent często pobiera całe pliki liczące po 500-1000 linii. Powoduje to zapchanie okna kontekstowego, przez co model "zapomina" lub ignoruje wcześniejsze instrukcje i traci spójność wnioskowania.

### D. Skupienie na architekturze zamiast na danych (Symptom zamiast przyczyny)
Gdy występuje błąd (np. `JSONDecodeError: Extra data`), agent nierzadko zaczyna od analizy endpointu REST API i serwisów pośredniczących, zamiast od razu zajrzeć do fizycznego pliku, który rzucił ten błąd (np. `ratings.json`).

### E. Ignorowanie "Księgi Zasad" (Projektowego DNA)
Zamiast zastosować się do zdefiniowanych reguł globalnych (np. "Wszystkie mapowania portali są w `usi_scrapers/schemas/portal_data_mapping.json`"), agent próbuje szukać logiki przypisywania zmiennych w lokalnych klasach adapterów. Prowadzi to do szukania kodu, który nie istnieje, i wpadania w pętlę.

---

## 2. Założenia dla nowego Skilla (Efficiency Protocol)

Nowy skill powinien wymusić na agencie następujący algorytm postępowania:

1. **Zasada "Scratchpad First" (Izolacja)**:
   - ZAKAZ pisania wielolinijkowych skryptów testowych wprost w argumencie polecenia terminala.
   - NAKAZ tworzenia małych plików testowych w katalogu `scratch/` (np. `write_to_file` -> `scratch/test_parsing.py`), a następnie ich uruchamiania. To eliminuje błędy składniowe basha.

2. **Zasada bezwzględnego ograniczenia I/O (Surgical Precision)**:
   - Nigdy nie ładuj całego pliku, jeśli szukasz jednej definicji. Używaj narzędzi wyszukiwania semantycznego lub `grep_search`.
   - Czytając pliki, wymuszaj stosowanie parametrów `StartLine` i `EndLine`, aby ograniczyć ilość pochłanianych tokenów.

3. **Zasada "Data Over Code" (Dane > Kod)**:
   - Jeśli błąd wskazuje na problem z parsowaniem danych (JSON, baza, plik tekstowy), pierwszym krokiem ZAWSZE musi być podgląd samego pliku z danymi (lub jego fragmentu). Szukanie błędu w kodzie przed obejrzeniem zepsutych danych to strata czasu.

4. **Zasada "Fail Fast, Re-evaluate"**:
   - Jeśli dwa kolejne kroki z użyciem tego samego narzędzia (np. przeglądanie tego samego pliku lub próba znalezienia tego samego ciągu znaków) kończą się fiaskiem, agent MUSI się zatrzymać, przeanalizować sytuację i zmienić podejście (np. zapytać użytkownika lub uruchomić skrypt eksploracyjny). Zakaz prób "do skutku" tym samym sposobem.

5. **Weryfikacja założeń projektowych**:
   - Zanim agent zacznie czytać kod w poszukiwaniu logiki biznesowej, musi sprawdzić metapliki projektu (`GEMINI.md`, dokumentację architektury), aby upewnić się, CZY dany moduł w ogóle odpowiada za funkcjonalność, której szuka (np. unikanie szukania kodu scrapującego w repozytorium UI).
