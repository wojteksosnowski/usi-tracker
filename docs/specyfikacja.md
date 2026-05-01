# **Specyfikacja Projektu: USI Tracker (Python Worker \+ Coda Pack)**

## **1\. Cel Projektu**

Stworzenie hybrydowego systemu do agregacji i archiwizacji inwestycji deweloperskich, składającego się z dwóch współpracujących komponentów:

1. **Lokalnego Skryptu (Worker):** Działającego w tle na komputerze użytkownika, odpowiedzialnego za "ciężką pracę" – scrapowanie (RynekPierwotny.pl, Otodom.pl), omijanie blokad (ScraperAPI), niestandardowe pobieranie obrazów (Grabber) oraz fizyczny zapis plików do synchronizowanego folderu Dropbox.  
2. **Coda Pack (Interfejs i Logika Coda):** Niestandardowego rozszerzenia w przestrzeni Coda.io, które pozwala użytkownikowi wysyłać zlecenia scrapowania do Workera oraz odbierać przetworzone wyniki, używając Dropboxa jako szyny komunikacyjnej.

## **2\. Stos Technologiczny (Tech Stack)**

*Dla agenta Cursor: Projekt składa się z dwóch odrębnych środowisk, które nie współdzielą bezpośrednio kodu.*

### **A. Lokalny Skrypt (Worker)**

* **Środowisko i Język:** Python 3.10+  
* **Główne biblioteki:**  
  * requests \- do komunikacji HTTP (pobieranie API, stron, ScraperAPI oraz plików binarnych).  
  * watchdog \- do aktywnego nasłuchiwania zmian w katalogu USIdata/ na Dropboxie.  
  * re i json \- (wbudowane) do obsługi wyrażeń regularnych Grabbera i parsowania JSON.  
  * urllib.parse \- do odkodowywania adresów URL (unquote).  
  * python-dotenv \- do przechowywania kluczy API.  
  * **Testowanie:** pytest (główny framework testowy), requests-mock lub responses (do mockowania zapytań HTTP).

### **B. Rozszerzenie Coda (Coda Pack)**

* **Środowisko i Język:** TypeScript (Node.js środowisko kompilacji) \+ @codahq/packs-sdk.  
* **Główne zadania:** \* Wykorzystanie context.fetcher do autoryzowanej komunikacji z Dropbox API (https://content.dropboxapi.com/2/files/upload i download).  
  * Definiowanie niestandardowych formuł (pack.addFormula) i akcji (isAction: true) dostarczających interfejs dla tabel w Coda.io.  
  * **Testowanie:** Mocha \+ Chai (lub Jest) oraz narzędzia testowe z @codahq/packs-sdk (np. executeFormulaFromPackDef).

## **3\. Architektura Danych (Struktura Systemu Plików na Dropbox)**

Głównym wektorem wymiany danych i zapisu jest system plików (Dropbox). Wprowadzono **ścisłe rozróżnienie** między drzewem dla plików graficznych a drzewem dla plików tekstowych logicznych.

Drzewo katalogów:

* \[DROPBOX\_PATH\]/Public/USI/ \- **(Drzewo dla plików graficznych)** Główny katalog przeznaczony WYŁĄCZNIE na zdjęcia i wizualizacje inwestycji (pliki binarne: .jpg, .png, .webp). Zapisuje tu **tylko** skrypt Python. Pliki logiczne JSON nigdy tu nie trafiają.  
  * .../\[developer\_slug\]/\[investment\_slug\]/ \- Folder docelowy dla grafiki konkretnej inwestycji.  
* \[DROPBOX\_PATH\]/USIdata/ \- **(Drzewo dla plików tekstowych)** Szyna wymiany komunikatów i danych (pliki tekstowe: .json). Służy do dwukierunkowej komunikacji między Coda Pack a skryptem Python. Pliki graficzne nigdy tu nie trafiają.  
  * coda\_\*.json \- Pliki zleceń. Generowane i wysyłane przez **Coda Pack** (przez Dropbox API). **Python** je czyta (nasłuchuje) i usuwa po przetworzeniu lub oznacza jako wykonane.  
  * app\_\*.json \- Pliki wyników. Generowane przez **Python** (bezpośredni zapis na dysku). **Coda Pack** je pobiera i wczytuje do tabel.

## **4\. Główne Moduły i Podział Ról**

### **A. Szyna Komunikacyjna (Interoperacyjność JSON)**

* **Wysyłanie zlecenia (TypeScript / Coda Pack):** Użytkownik klika przycisk "Pobierz Inwestycję". Coda Pack wykonuje request do Dropbox API, zapisując plik coda\_request\_\[ID\].json (zawierający np. docelowy URL i typ zadania) wyłącznie w folderze /USIdata/.  
* **Odbiór zlecenia (Python):** Skrypt Python, używając biblioteki watchdog, wykrywa nowy plik coda\_request\_\[ID\].json w katalogu /USIdata/, parsuje go i rozpoczyna proces pobierania danych.  
* **Zwracanie wyników (Python):** Po zescrapowaniu danych, Python zapisuje ustrukturyzowany plik tekstowy app\_result\_\[ID\].json do tego samego folderu /USIdata/.  
* **Wczytywanie wyników (TypeScript / Coda Pack):** Formuła Coda odczytuje przez Dropbox API zawartość app\_result\_\[ID\].json z katalogu /USIdata/ i aktualizuje wiersz w tabeli USImaster.

### **B. Moduł Scrapowania (RynekPierwotny.pl) \- PYTHON**

1. Skrypt odpytuje endpoint JSON https://rynekpierwotny.pl/api/v2/offers/offer/... przy użyciu requests.get().  
2. Parsuje dane, w tym vendor.value.id, geo\_point, construction\_date\_range i listę galerii.  
3. Wyizolowane URL-e zdjęć przekazuje do Modułu Pobierania Obrazów, a resztę tekstu pakuje do JSON-a zwrotnego.

### **C. Moduł Scrapowania (Otodom.pl) \- PYTHON**

1. Wymagane użycie ScraperAPI: https://api.scraperapi.com/?api\_key=...\&url=OTODOM\_URL.  
2. Z pobranego HTML wyciąga tag \<script id="\_\_NEXT\_DATA\_\_" type="application/json"\> używając wyrażenia regularnego lub BeautifulSoup.  
3. Parsuje zawartość i buduje płaski JSON zwrotny dla Coda.

### **D. Moduł "Grabber" (Filtry dla stron deweloperów) \- PYTHON**

1. Pobranie zewnętrznej strony dewelopera przez ScraperAPI.  
2. Zastosowanie zdefiniowanych przez użytkownika filtrów Regex (re.findall(pattern, html\_content, flags)).  
3. Odkodowanie znaków specjalnych (np. %2F na /) za pomocą urllib.parse.unquote().  
4. Usunięcie duplikatów (np. konwersja do set()) i przekazanie linków do pobrania.

### **E. Moduł Zapisywania Obrazów \- PYTHON**

1. Skrypt iteruje po odfiltrowanych URL-ach, wykonując requests.get(url, stream=True).  
2. Używając wbudowanego os i shutil.copyfileobj(), zapisuje fizycznie pliki binarne, zachowując strukturę docelową **wyłącznie w drzewie graficznym**: /Public/USI/{developer.slug}/{investment.slug}/{filename} w lokalnym katalogu Dropboxa.  
3. Czyści nazwy plików z parametrów URL (regex wyłuskujący .jpg, .png, .webp).

### **F. Moduł Generowania Mapy (HERE API) \- CODA PACK (TypeScript)**

1. Formuła w Coda Packu (pack.addFormula), która przyjmuje szerokość i długość geograficzną, a zwraca zmontowany adres URL.

// Przykład dla Coda SDK  
const mapImageUrl \= \`https://image.maps.hereapi.com/mia/v3/base/mc/overlay:padding=64;zoom=16/1536x512/png?apiKey=${process.env.HERE\_API\_KEY}\&overlay=point:${lat},${lng}|size=large;icon=bubble\&style=explore.satellite.day\&scaleBar=km\&features=pois:disabled\&lang=pl\`;

## **5\. Strategia Testowania i Zapewnienie Jakości (Testing)**

Aby zapewnić stabilność i zapobiec kosztownym błędom (np. niepotrzebnemu zużyciu kredytów ScraperAPI), projekt wymaga rygorystycznego pokrycia testami dla obu środowisk.

### **A. Testy w Python Workerze (pytest)**

1. **Mockowanie API:** Nigdy nie wykonuj rzeczywistych zapytań do ScraperAPI, Otodom czy RynekPierwotny.pl w środowisku testowym. Używaj biblioteki requests-mock lub responses, aby zwracać predefiniowane (zapisane lokalnie) pliki HTML/JSON jako odpowiedzi serwera.  
2. **Izolacja Systemu Plików:** Logika zapisująca pliki (os, shutil) oraz czytająca z folderu USIdata/ musi być testowana przy użyciu tymczasowych katalogów (fixture tmp\_path w pytest). Testy **nie mogą** ingerować w rzeczywisty folder Dropbox.  
3. **Testy Regex (Grabber):** Moduł "Grabber" wymaga solidnych testów jednostkowych. Należy przygotować zestaw przykładowych fragmentów kodu HTML stron deweloperów i zweryfikować, czy funkcja poprawnie z nich wyciąga oraz odkodowuje linki.  
4. **Testy Watchdoga:** Należy symulować pojawienie się pliku coda\_\*.json w tymczasowym katalogu i sprawdzać, czy funkcja parsująca zlecenie zostaje poprawnie uruchomiona.

### **B. Testy w Coda Pack (Mocha/Jest \+ Coda SDK)**

1. **Testy Formuł:** Wykorzystaj funkcję executeFormulaFromPackDef dostarczaną przez @codahq/packs-sdk, aby testować, czy moduł poprawnie parsuje parametry wejściowe (np. czy złączy odpowiednie parametry dla Mapy HERE API).  
2. **Mockowanie Fetchera Dropbox:** Zmockuj wbudowany w Codę context.fetcher, aby upewnić się, że ładunek (payload) wysyłany do files/upload Dropboxa posiada poprawną formę JSON oraz wymaganą ścieżkę zaczynającą się od /USIdata/.

## **6\. Wytyczne dla AI (System Prompts dla Cursora)**

Podczas implementacji, AI w Cursorze musi przestrzegać ścisłego podziału na dwa projekty oraz zasady separacji drzew katalogów:

### **1\. Dla kodu w Pythonie (folder np. /python-worker):**

* **Zawsze twórz testy:** Wraz z każdym nowym modułem (np. scraper.py, grabber.py), utwórz odpowiadający mu plik testowy (test\_scraper.py, test\_grabber.py).  
* **Rozróżnienie Ścieżek (KRYTYCZNE):** Ściśle przestrzegaj zasady dwóch drzew. Pliki binarne/obrazki zapisuj TYLKO w \[DROPBOX\_PATH\]/Public/USI/.... Pliki wymiany danych (JSON) zapisuj i odczytuj TYLKO z \[DROPBOX\_PATH\]/USIdata/. Nigdy nie zapisuj danych tekstowych w folderach graficznych i odwrotnie.  
* **Żadnych narzędzi webowych/UI:** Projekt ma być czystym skryptem konsolowym. Używaj wirtualnego środowiska (venv) i pliku requirements.txt (requests, watchdog, python-dotenv, pytest, requests-mock).  
* **Solidny Error Handling:** Ponieważ skrypt działa w tle i łączy się z zewnętrznymi usługami (ScraperAPI) oraz zapisuje duże pliki, koniecznie używaj bloków try-except z odpowiednim logowaniem (np. wbudowany moduł logging). W przypadku błędu zapisu, skrypt musi móc działać dalej.  
* **Bezpieczny Regex w Pythonie:** Zwróć uwagę, że niektóre złożone flagi regex z JavaScript mogą mieć inną składnię w module re Pythona (np. globalne dopasowania osiąga się przez re.findall lub re.finditer).

### **2\. Dla kodu Coda Pack (folder np. /coda-pack):**

* **SDK Coda.io:** Pisz czysty kod zgodny z dokumentacją @codahq/packs-sdk. Nie używaj standardowego fetch z Node.js, tylko context.fetcher.fetch().  
* **Autoryzacja Dropbox:** Kontynuuj używanie uwierzytelniania Dropbox API (jak zarysowano w pierwotnym main-kopia.ts), ale skup się na endpointach files/upload (tworzenie zlecenia coda\_\*.json) i files/download (odczyt zlecenia app\_\*.json). Upewnij się, że wszystkie żądania operują na folderze /USIdata/.  
* **Deklaracje Typów:** Definiując formuły, ściśle określaj resultType (np. coda.ValueType.String dla JSONów jako ciągów tekstowych) i upewnij się, że dodano pack.addNetworkDomain("dropboxapi.com").