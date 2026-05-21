# USI Tracker - Python Worker

Automatyczny system śledzenia i pobierania danych o inwestycjach deweloperskich z serwisów **RynekPierwotny.pl**, **Otodom.pl** oraz **TabelaOfert.pl**. System składa się z backendu API (Flask), wydajnej szyny danych oraz interfejsu React (Babel standalone).

## 🚀 Główne Funkcje

- **Scraping**: Pobieranie szczegółowych danych o inwestycjach (opisy, ceny, lokalizacje, udogodnienia) za pośrednictwem biblioteki `usi-scrapers`.
- **Zasoby**: Automatyczne pobieranie i katalogowanie zdjęć inwestycji.
- **Interfejs UI**: Lokalna aplikacja webowa do przeglądania, filtrowania i zarządzania danymi.
- **Wędrowiec (Crawler)**: Cykliczne odkrywanie nowych inwestycji i aktualizacja istniejących rekordów.
- **Logowanie**: Prowadzenie historii operacji w każdym folderze inwestycji.

---

## 📁 Struktura Katalogów (Dropbox)

System operuje wewnątrz folderu `/Public/` na Dropboxie:

- `/Public/USI/` - **Grafiki**: Przechowuje zdjęcia w strukturze `{deweloper}/{inwestycja}/`.
- `/Public/USIdata/` - **Dane**: Przechowuje kanoniczne pliki JSON (`usi_*.json`) oraz surowe zrzuty z portali.
- `/Public/USIdev/` - **Deweloperzy**: Profile deweloperów i metadane łączenia kont.

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

Głównym punktem wejścia jest skrypt `python3 -m python_worker.main` lub skróty `.sh`:

### 1. Interfejs UI
Uruchamia serwer Flask i otwiera lokalny interfejs React.
```bash
./start-ui.sh
# lub
python3 -m python_worker.main ui
```

### 2. Odkrywanie (Discover)
Wyszukuje nowe inwestycje dla podanego dewelopera.
```bash
python3 -m python_worker.main discover {dev_slug}
```

### 3. Aktualizacja (Update)
Aktualizuje dane konkretnej inwestycji lub całego dewelopera.
```bash
python3 -m python_worker.main update-inv {dev_slug}/{inv_slug}
python3 -m python_worker.main update-dev {dev_slug}
```

### 4. Wędrowiec (Crawler)
Uruchamia demona w tle, który cyklicznie skanuje portale.
```bash
python3 -m python_worker.main crawl
```

---

## 📝 Zasady Rozwoju
- **Delegacja Scraperów**: Cała logika I/O i pobierania danych z portali musi znajdować się w bibliotece `usi-scrapers`.
- **Niezmienność Slugów**: Slugi i identyfikatory portalowe są nienaruszalne.
- **Format JSON**: Kanoniczne pliki `usi_*.json` są jedynym źródłem prawdy dla UI.
