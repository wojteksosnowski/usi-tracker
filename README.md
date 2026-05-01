# USI Tracker - Python Worker

Automatyczny system śledzenia i pobierania danych o inwestycjach deweloperskich z serwisów **RynekPierwotny.pl** oraz **Otodom.pl**. Worker synchronizuje dane z systemem **Coda.io** poprzez współdzielony folder Dropbox.

## 🚀 Główne Funkcje

- **Scraping**: Pobieranie szczegółowych danych o inwestycjach (opisy, ceny, lokalizacje, udogodnienia).
- **Zasoby**: Automatyczne pobieranie i katalogowanie zdjęć inwestycji.
- **Integracja Coda**: Nasłuchiwanie żądań (`coda_request_*.json`) i dostarczanie wyników w formacie JSON.
- **Podsumowania**: Generowanie zbiorczych plików `app_latest_results.json` (pełny) oraz `brief` (lekki) dla szybkiej synchronizacji tabel.
- **Logowanie**: Prowadzenie historii operacji w każdym folderze inwestycji (`processing_log.txt`).

---

## 📁 Struktura Katalogów (Dropbox)

System operuje wewnątrz folderu `/Public/` na Dropboxie:

- `/Public/USI/` - **Grafiki**: Przechowuje zdjęcia w strukturze `{deweloper}/{inwestycja}/`.
- `/Public/USIdata/` - **Dane**: Przechowuje pliki JSON, wyniki oraz podsumowania.
    - `{deweloper}/{inwestycja}/` - Folder konkretnej inwestycji.
    - `app_latest_results.json` - Zbiorczy plik z najnowszymi wynikami (pełny).
    - `app_latest_results_brief.json` - Zbiorczy plik bez surowych danych (szybki).

---

## ⚙️ Konfiguracja

1. **Plik .env**: Stwórz plik `.env` w głównym katalogu:
   ```env
   SCRAPERAPI_KEY=twoj_klucz_scraperapi
   DROPBOX_PATH=/Volumes/Samsam/py/usi-tracker  # Ścieżka do roota projektu
   ```

2. **Instalacja**:
   Zalecane użycie wirtualnego środowiska (venv):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   *(Wymagane biblioteki: `requests`, `watchdog`, `python-dotenv`)*

---

## 🛠️ Instrukcja Obsługi (CLI)

Worker obsługuje kilka trybów uruchomienia poprzez moduł `python_worker.main`:

### 1. Tryb Śledzenia (Watchdog) - DOMYŚLNY
Uruchomienie bez parametrów wprowadza workera w tryb ciągłego monitorowania folderu `USIdata`. Czeka na nowe pliki od Coda.io.
```bash
python3 -m python_worker.main
```

### 2. Tryb Pobierania (Fetch)
Wykonuje pełny skan najnowszych ofert z portali i generuje pliki podsumowania.
```bash
python3 -m python_worker.main fetch
```

### 3. Tryb Testowy (Test)
Pobiera po 3 losowe inwestycje z każdego portalu. Służy do szybkiej weryfikacji działania bez obciążania limitów API.
```bash
python3 -m python_worker.main test
```

### 4. Tryb Ręczny (URL)
Przetwarza konkretny podany adres URL.
```bash
python3 -m python_worker.main https://rynekpierwotny.pl/oferty/...
```

---

## 🔗 Integracja z Coda.io

### Wysyłanie żądania
Aby wymusić pobranie danych dla konkretnej inwestycji, Coda wrzuca plik JSON do odpowiedniego folderu:
`.../USIdata/{developer}/{investment}/coda_request_{id}.json`

**Obsługiwane mapowania pól:**
- `rpID` lub `offer_id` -> Identyfikator RynekPierwotny.
- `otoID` lub `url` -> Identyfikator lub link do Otodom.
- `USIfolder` -> Nazwa folderu inwestycji.

### Otrzymywanie wyników
Worker wygeneruje w tym samym folderze:
- `app_result_{id}.json` - Kluczowe dane (lat/lng, lista ścieżek zdjęć, metadane).
- `rp_details.json` / `oto_details.json` - Surowy zrzut z API dla Twoich formuł `.ParseJSON`.
- `processing_log.txt` - Historia (kiedy i co zostało pobrane).

---

## 📝 Uwagi
- **Nienaruszalność**: Pliki `coda_request_*.json` NIE SĄ usuwane przez workera.
- **Kodowanie**: Wszystkie pliki JSON są zapisywane w formacie UTF-8.
- **Logi systemowe**: Główny log aplikacji znajduje się w pliku `worker.log`.
