# Lista pomysłów uzytkownika

## obecny kamień milowy

1. [x] dodać funkcję wskazywania katalogu roboczego w którym znajduje się /USI oraz /USIdata, bez tego wskazania niech skrypt pracuje w katalogu z którego został uruchomiony
2. [x] dodać do worker, żeby zapisywał JSONy danej inwestycji pobrane ze stron otodom i rynekpierwotny w całości w katalogu w drzewie USIdata
3. [x] przeprowadzić analizę które informacje zbierane w JSON ze stron otodom i rynekpierwotny powtarzają się  w  plikach coda_request_
4. [x] dodać scraping tabelaofert.pl
5. [x] obsługa map HERE (przykład: here.md)
    - [x] modularna budowa
    - [x] mozliwosc stylizacji
    - [x] mozliwosc zapisu do danych inwestycji
6. [x] dodać interfejs do przeglądania bazy danych i pobranych zdjęć
    - [x] plan zawartości interfejsu
    - [x] pierwszy prototyp
7. [x] obecnie coda.io korzysta z ScrapperAI do pobierania z otodom.pl ze względu na sposób renderowania html. zbadań jak mozna to ominąć lekkim rozwiązaniem lokalnym. czy scraper jest potrzebny - zbadać. (Wdrożono curl_cffi w Fetcherze)
8. [x] Oceny w kategoriach - dotyczy całego projektu usi-tracker - oceny w kategoriach przyznawane są w skali od 0-4. W kategorii moze nie zostać przyznana zadna ocena. Jezeli ocena nie jest przyznana wtedy kategoria posiada wartość "brak" - nie jest pokazywane zadne zaznaczenie w danej kategorii. Sprawdz dokument /Volumes/Samsam/claude-py/usi-tracker/reference-data/coda/USImaster-headers.csv
9. [x] Nagłówek inwestycji - "<a class="usi-btn sm" target="_blank" rel="noopener"><span class="usi-source rp">RP</span> Źródło <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10M9 4l4 4-4 4"></path></svg></a>" nie zawiera linku do strony z której został pobrany rekord. Naprawić.
10. [x] Nagłówek inwestycji - minimapa nie pokazuje HERE --> naprawić. klucz API HERE "BDske2zxCqqwwBGMf4IBKA49FRvRZLe4TnfBtYTor9c" dodać do pliku .env
11. [x] Licznik kompletności oceny nalezy zastąpić kalkulowaną oceną złozoną. Ocena złozona pokazana jest w /Volumes/Samsam/claude-py/usi-tracker/reference-data/coda/obliczanie-oceny.md. Kiedy nie ma oceny w danej kategorii algorytm nie bierze pod uwage tej kategorii, tylko kategorie z ocena i z nich liczy srednia eksponentami. dlatego jak jest jedna ocena "4" to średnia wynosi "4". 
12. [x] Brakuje schema JSON tworzonych przez USI-tracker. Uzupełnij.
13. [x] Zastanów się nad istotnością tych problemów
    - bus.py reaguje tylko na nowe pliki; może nie obsłużyć istniejących plików przy starcie
    - config.py domyślnie przyjmuje DROPBOX_PATH=".", co może maskować niepoprawną konfigurację
14. [x] Zastosuj usi-star-... oraz usi-zero-... w elementach graficznych interfejsu. usi-star i usi-zero są częścią systemu identyfikacji brandu USI.
    - oceny kategorii w widoku indywidualnym - zamiast kwadratów z zaokrągleniami --> koła wypełnione kolorem (gdy zaznaczone) zawierające usi-zero (dla oceny "0") lub usi-star
    - oprócz oceny wyrazonej liczbą ocena gwiazdkowa np. 2,98 oznaczna "** 4/5" uzyj usi-star- dla gwiazdek, dla ułamków uzyj znakow specjalnych z uzytej czcionki.
15. [x] Scrapper otodom kompletnie nie radzi sobie ze zdjęciami. Nalezy przeanalizowac metode importu z coda.io /Volumes/Samsam/claude-py/usi-tracker/reference-data/otodom/pojedynczy-rekord/pobieranie-otodom.md
16. [x] Scrapper tabelaofert importuje za duzo zdjec. przeanalizowac ktore rzeczywiscie pasuja do importowanej oferty. /Volumes/Samsam/claude-py/usi-tracker/reference-data/tabelaofert/pojedynczy rekord/pobieranie-tabelaofert.md
17. [x] dodać licznik wykorzystanie ScrapperAI, limit 1000 zapytan miesiecznie (Zaimplementowano w Fetcherze z persistencją w usage.json)
18. [x] upewnij się, ze zmiany w kodzie w jednym scraperze nie psuja działania innych scraperów. pełna modularność. (Zcentralizowano Fetcher)
19. [x] mapa w nagłówku nadal jest źle wyświetlana. sprawdzić czy to kwestia błędnego linku, czy kłopotu z mapami HERE, kluczem API, czy inny problem. 
20. [x] W widoku jednej inwestycji - widok A, zagęść siatkę miniatur z 3 na 5
21. [x] W widoku listy inwestycji zmien na 7 kolumn dla pełnego ekranu. Ustal elastyczna szerokość kolumn. Zwęzajac okno zmniejszaj liczbę kolumn.
22. [x] Interfejs nie pokazuje nadawanych ocen i nie usuwa obrazów. Zapamiętane w tle oceny widoczne są dopiero po przeładowaniu strony. Do poprawienia.
23. [x] Ciagly problem z mapa.

https://image.maps.hereapi.com/mia/v3/base/mc/zoom:14/560x140/png?apiKey=BDske2zxCqqwwBGMf4IBKA49FRvRZLe4TnfBtYTor9c&c=51.993105395629286,20.836496302272685&overlay=point:51.993105395629286,20.836496302272685|size=large;icon=bubble&style=explore.night&scaleBar=km&features=pois:disabled&lang=pl

response:

{"action":"check parameter schema in '/openapi' endpoint for this api version","cause":"parameter does not match OpenAPI schema","code":"E622002","correlationId":"a9b22391-cb85-4709-b92d-5876ebe3e3a7","details":[{"message":"The 'view' parameter in 'path' has an error: unknown key zoom found in view param"}],"parameter":"view","status":400,"title":"invalid parameter"}
24. [x] nalezy uporzadkować udogodnienia.

rynekpierwotny ma facilities - teza orobocza: są rozne w kazdej inwestycji, nie ma stalej listy
otodom ma features - troche ubozsze niz rynekpierwotny
tabelaofert - opis jest w pliku /Volumes/Samsam/claude-py/usi-tracker/reference-data/tabelaofert/pojedynczy rekord/pobieranie-tabelaofert.md ale wymaga identyfikacji czy jest w JSON

udogodnienia wpływają na ocenę w katagorii Udogodnienia. wstepna implementacja z coda.io opisana w tym pliku: /Volumes/Samsam/claude-py/usi-tracker/reference-data/coda/wyrozniki.md

w usi-tracker planuję pokazywanie sugestii dla uzytkownika jaka nalezy przyjac ocene na podstawie zebranych hasel. uzytkownik sam nadaje ocene.


25. [x] widok inwestycji

górna belka w obu widokach.

<div style="display: grid; grid-template-columns: 1fr 280px; gap: 16px; padding: 16px 24px 0px; flex-shrink: 0;"><div><div style="display: flex; align-items: baseline; gap: 10px; margin-bottom: 6px; flex-wrap: wrap;"><h1 class="usi-h1" style="margin: 0px;">CITYFLOW - mieszkania na sprzedaż</h1><span class="usi-body" style="color: var(--usi-ink-3);">Okam Capital</span><div style="flex: 1 1 0%;"></div><div style="display: flex; gap: 6px; flex-wrap: wrap;"><a class="usi-btn sm" href="https://tabelaofert.pl/inwestycja/cityflow-redutowa-9-warszawa-wola-ulrychow-mieszkania-na-sprzedaz,i8620262" target="_blank" rel="noopener"><span class="usi-source to">TO</span> Źródło <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10M9 4l4 4-4 4"></path></svg></a><a class="usi-btn sm" href="https://www.google.com/maps/@52.228796,20.942061,780m/" target="_blank" rel="noopener"><svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4l4-2 4 2 4-2v10l-4 2-4-2-4 2z"></path><path d="M6 2v10M10 4v10"></path></svg> Maps</a></div></div><div style="display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--usi-ink-3);"><span>📍 ul. Redutowa 9, Warszawa</span><span class="usi-mono">12 mieszk.</span><span class="usi-mono">—</span><span>17 udogodnień</span></div></div><a href="https://www.google.com/maps/@52.228796,20.942061,780m/" target="_blank" rel="noopener" title="Otwórz w Google Maps" style="display: block; position: relative; height: 70px; width: 100%; border-radius: 10px; overflow: hidden; text-decoration: none; background: var(--usi-surface-3); border: .5px solid var(--usi-border);"><img src="https://image.maps.hereapi.com/mia/v3/base/mc/overlay:zoom=14/560x140/png?apiKey=BDske2zxCqqwwBGMf4IBKA49FRvRZLe4TnfBtYTor9c&amp;overlay=point:52.228796,20.942061|size=large;icon=bubble&amp;style=explore.night&amp;scaleBar=km&amp;features=pois:disabled&amp;lang=pl" alt="Mapa lokalizacji" style="width: 100%; height: 100%; object-fit: cover; display: block;"></a></div>

po belce następują

widok A:

<div style="display: grid; grid-template-columns: 2fr 1fr 1fr; flex: 1 1 0%; overflow: hidden; margin-top: 16px;">

widok C:

<div style="flex: 1 1 0%; position: relative; overflow: hidden; background: var(--usi-bg);">

w widoku C brakuje marginesu 16px w elemencie nastepujacym po gornej belce.

26. [ ] w USImaster.csv występują inwestycje z podwójnym adresem rynekpierwotn+otodom. nalezy przygotować plan rozdzielenia tych rekordów na dwa osobne. z istniejącego rekordu nalezy wyodrębnić adres rynekpierwotny. zaimportowac rekord z wydzielonego adresu rynekpierwotny. zwalidować pierwotny rekord. nalezy zaplanowac testy dla tej opreacji przed wdrozeniem roll-out na istniejaca baze danych ponad 6000 rekordów.

27. [x] pliki .jsx robią się duze. sprawdź ich modularność. sprawdź czy mozna wykorzystac jakis element wielokrotnie. sprawdz czy nie sa tworzone instancje dla dwoch bardzo podobnych blokow w html UI. zaplanuj testy. celem jest podzielenie kodu UI na mniejsze moduly latwiejsze do zarzadzania i udoskonalania.

28. [x] trzeba naprawic ten element interfejsu <div style="display: flex; align-items: center; gap: 12px; padding: 14px 24px; border-bottom: .5px solid var(--usi-border); background: var(--usi-surface); flex-shrink: 0;"> poniewaz wystaje poza szerokosc okna.

29. [x] potrzebne jest sledzenie kiedy rekord zostal dodany i kiedy zostal zmodyfikowany np. przez zmiane statusu oceny. (Zaimplementowano w audit.created_at i audit.updated_at)

30. [ ] podglad listy 6000+ inwestycji jest powolny. przeanalizowac opcje mitygacji problemu.

32. [ ] Opracuj plan przejscia na pelna baze danych 6000+ rekordow. testy ktore nie zniszczą bazy. 

33. [x] Przegląd .gitignore - zeby odzwieciedlal strukture projektu

34. [ ] W widoku inwestycji nalezy dodac szybkie filtry na zasadzie toggle: źródła danych (trzy portale), 7 głównych miast (nazwy miast). Toggle działa na zasadzie włącza wyłącza filtr. klikniecie z shift powoduje wyłączenie wszystkich pozostałych w danej grupie.

35. [ ] Wejscie do widoku inwestycji a potem powrot do listy inwestycji restuje filtr. poprawic aby nie resetowalo filtra.

36. [ ] Wejscie do widoku inwestycji a potem przelaczanie miedzy rekordami (strzalki na klawiaturze) ignoruje filtr. poprawic zeby nie ignorowalo filtra.

37. [ ] Gleboka weryfikacja czy USImaster.csv zostal prawidlowo przyswojony do bazy.

## nastepny kamien milowy

1. [ ] Wyszukiwanie z API wikipedii interesujących obiektów w okolicy na podstawie lokalizacji

## przyszłe kamienie milowe

1. [ ] uruchomienie na raspberry pi - dopiero po przejsciu rozleglych testow na lokalnym komputerze
2. [x] przejście na https://github.com/D4Vinci/Scrapling 
