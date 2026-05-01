Prowadzę w coda.io bazę inwestycji deweloperskich. W dropbox zapisuję ściągnięte pliki obrazów przedstawiające wizualizacje budowanych inwestycji. Następnie ręcznie analizuję inwestycje pod kątem dopasowania do systemu USI nadając punkty od 0 do 4 w kilku kategoriach.

specyfikacja ma być dla skryptu przechwytującego nowe inwestycje ze stron rynekpierwotny.pl i otodom.pl. Przechowywanie bazuje na lokalnym przechowywaniu i synchronizacji do dropbox. coda.io służy za interfejs i silnik do funkcji logicznych i drobnej automatyki.

oto formuła coda której używam do zaciągania danych z rynekpierwotny.pl:

"ForEach( rpJSONmainV2, If( CurrentValue.ParseJSON("$.value.groups.value.stages.value") .IsBlank(), AddRow( rpScrape, rpScrape.Inwestycja, CurrentValue.ParseJSON("$.value.name"), rpScrape.rpAdres, Concatenate( "https://rynekpierwotny.pl/oferty/", CurrentValue.ParseJSON("$.value.vendor..slug").Trim(), "/", CurrentValue.ParseJSON("$.value.slug").Trim(), "-", CurrentValue.ParseJSON("$.value.id").Trim(), "/" ), rpScrape.rpJSON, PineMintRPUtils::FetchRawTextFile( Concatenate( "https://rynekpierwotny.pl/api/v2/offers/offer/", CurrentValue.ParseJSON("$.value.id"), "/?s=offer-detail" ) ) .ToText() ), ForEach( CurrentValue.ParseJSON("$.value.groups.value.stages.value"), AddRow( rpScrape, rpScrape.Inwestycja, CurrentValue.ParseJSON("$.value.offer.value.name"), rpScrape.rpAdres, Concatenate( "https://rynekpierwotny.pl/oferty/", CurrentValue .ParseJSON( "$.value.offer.value.vendor.value.slug" ) .Trim(), "/", CurrentValue.ParseJSON("$.value.offer.value.slug").Trim(), "-", CurrentValue.ParseJSON("$.value.offer.value.id").Trim(), "/?show_sold_stage=true&stage=", CurrentValue.ParseJSON("$.value.id") ), rpScrape.rpJSON, PineMintRPUtils::FetchRawTextFile( Concatenate( "https://rynekpierwotny.pl/api/v2/offers/offer/", CurrentValue.ParseJSON("$.value.offer.value.id").Trim(), "/?s=offer-detail" ) ) .ToText() ) ) ) )"

Używam też ScraperAPI żeby ominąć blokady na otodom.pl. Stamtąd także pobieram listę inwestycji.

Ponieważ nie mam jak udostępnić ci całości coda.io mogę to robić kawałek po kawałku. Chciałbym, żebyś zadawał mi kolejne pytania, a ja będę wklejał tutaj fragmenty kodu i procedur tego co jest robione przez coda.io.

W efekcie chciałbym uzyskać specyfikację dla skryptu który po pierwsze będzie miał podstawową funkcjonalność uzyskiwaną teraz przez coda (prosty scraping i archiwizacja) i umożliwi w przyszłości bardziej złożone funkcje. Jedną z dodatkowych funkcji w coda. którą obecnie potrzebuje to zapisanie w JSON zgromadzonych w każdym rekordzie inwestycji informacji do dropbox.



Mam jedna tabelę dla wszystkich źródeł. Używam głównie Balkony, Fasady, Wnętrza, Teren, Mieszkania i Udogodnienia. Tak, ścieżki są przechowywane.



1. pobieram automatycznie. Oto funkcja coda.io dla rynekpierwotny.pl "ListCombine( thisRow.rpJSON.ParseJSON("$.main_image.value.m_img_1500") .Trim(), PineMintRPUtils::FetchRawJsonFile( Concatenate( "https://rynekpierwotny.pl/api/v2/offers/offer/", thisRow.rpJSON.ParseJSON("$.id").Trim(), "/?s=offer-detail-gallery" ) ) .ParseJSON( "$.gallery.*.image.g_img_1500" ) ) .Filter( CurrentValue.IsNotBlank() ) .ForEach( PineMintDropbox::DBFastSaveUrlToDropbox( [Wojtek Sosnowski], CurrentValue, Join( "/", "/Public/USI", Konkurenci .Filter( rpID = thisRow.rpJSON.ParseJSON("$.vendor.value.id").Trim() ) .usiFolder, thisRow.rpSlug, RegexExtract(CurrentValue, "(?<=/)[^/]+.(?:jpg|png)") ) .Trim() ) )" struktura jest tworzona na podstawie "slug" z plików JSON.



Pobieram JSON z tego linku: https://rynekpierwotny.pl/api/v2/offers/offer/?s=offer-list&display_type=1&distance=5&for_sale=true&limited_presentation=false&page=1&page_size=

Analizuję ręcznie i nadaje punkty według własnego uznania wedlug metody USI. Mam spisane kryteria. Nie analizujmy głębiej zagadnień oceny. Przyjmijmy że jest to element roz∑iazywany ręcznie.

dowody[...] są placeholderami które zostaną wkrótce usunięte, bo nie spełniały swojego zadania.

Zostawmy fundament na chwilę z boku.



Oto funkcja przetwarzająca dane pobrane przez ScraperAPI z otodom.pl

"ForEach( otoJSONmain, AddRow( otoScrape, otoScrape.otoSlug, CurrentValue.ParseJSON("$.slug") .RegexExtract( "(?:.*)(?=-ID)" ), otoScrape.otoID, CurrentValue.ParseJSON("$.slug").RegexExtract("(?<=ID).+$").Trim(), otoScrape.Inwestycja, CurrentValue.ParseJSON("$.title"), otoScrape.otoJSON, CurrentValue, otoScrape.Termin, Concatenate( CurrentValue .ParseJSON( "$.investmentEstimatedDelivery.quarter" ), " kw. ", CurrentValue.ParseJSON("$.investmentEstimatedDelivery.year") ), otoScrape.otoAdres, Concatenate( "https://www.otodom.pl/pl/inwestycja/", CurrentValue.ParseJSON("$.slug") ) ) )" adres z którego jest wyciągany JSON otodom https://www.otodom.pl/pl/wyniki/sprzedaz/inwestycja/cala-polska?limit=72&investmentEstateType=FLATS&by=LATEST&direction=DESC&viewType=listing



coda pozostanie moim interfejsem bazy danych. baza danych będzie opierać się na drzewie katalogów prowadzonym zgodnie z parametrami slug z plików JSON z rynekpierwotny i otodom. Potrzebuję zapisywać rekordy coda.io do JSON w dropbox aby zmniejszyć moją zależność od coda.io i móc przetwarzać więcej informacji poza coda.io

W momencie gdy skrypt zrobi scraping do dropbox coda musi tylko zaciągnąć informacje o nowych rekordach zeby nie powtarzać scrapingu.




coda identyfikuje inwestycje po indywidualnym ID nadawanym przez otodom i rynekpierwotny. 

mam wrażenie że nie przeanalizowaliśmy jeszcze całej mechaniki coda.io.

pytałeś o przycisk rpReloadJSON - oto jego funkcja: "ModifyRows( thisRow, thisRow.rpJSON, PineMintRPUtils::FetchRawTextFile( Concatenate( "https://rynekpierwotny.pl/api/v2/offers/offer/", thisRow.rpID, "/?s=offer-detail" ) ) .ToText() )"



Gdy rpscrape jest wypełniony przez tę funkcję: "ForEach( rpJSONmainV2, If( CurrentValue.ParseJSON("$.value.groups.value.stages.value") .IsBlank(), AddRow( rpScrape, rpScrape.Inwestycja, CurrentValue.ParseJSON("$.value.name"), rpScrape.rpAdres, Concatenate( "https://rynekpierwotny.pl/oferty/", CurrentValue.ParseJSON("$.value.vendor..slug").Trim(), "/", CurrentValue.ParseJSON("$.value.slug").Trim(), "-", CurrentValue.ParseJSON("$.value.id").Trim(), "/" ), rpScrape.rpJSON, PineMintRPUtils::FetchRawTextFile( Concatenate( "https://rynekpierwotny.pl/api/v2/offers/offer/", CurrentValue.ParseJSON("$.value.id"), "/?s=offer-detail" ) ) .ToText() ), ForEach( CurrentValue.ParseJSON("$.value.groups.value.stages.value"), AddRow( rpScrape, rpScrape.Inwestycja, CurrentValue.ParseJSON("$.value.offer.value.name"), rpScrape.rpAdres, Concatenate( "https://rynekpierwotny.pl/oferty/", CurrentValue .ParseJSON( "$.value.offer.value.vendor.value.slug" ) .Trim(), "/", CurrentValue.ParseJSON("$.value.offer.value.slug").Trim(), "-", CurrentValue.ParseJSON("$.value.offer.value.id").Trim(), "/?show_sold_stage=true&stage=", CurrentValue.ParseJSON("$.value.id") ), rpScrape.rpJSON, PineMintRPUtils::FetchRawTextFile( Concatenate( "https://rynekpierwotny.pl/api/v2/offers/offer/", CurrentValue.ParseJSON("$.value.offer.value.id").Trim(), "/?s=offer-detail" ) ) .ToText() ) ) ) )" naciskam kolejno przyciski z funkcjami

dodajdeweloper uploadJSONrp dodajWidok dodajUSI usunTemp

dodajdeweloper gdy brakuje rozpoznanego dewelopera: 

AddRow( Konkurenci, Konkurenci.rpID, thisRow.rpJSON.ParseJSON("$.vendor.value.id").Trim(), Konkurenci.rpSlug, thisRow.rpJSON.ParseJSON("$.vendor.value.slug").Trim(), Konkurenci.rpWWW, Concatenate( "https://rynekpierwotny.pl/deweloperzy/", thisRow.rpJSON.ParseJSON("$.vendor.value.slug").Trim(), "-", thisRow.rpJSON.ParseJSON("$.vendor.value.id").Trim() ), Konkurenci.Deweloper, thisRow.rpJSON.ParseJSON("$.vendor.value.name").Trim(), Konkurenci.usiFolder, thisRow.rpJSON.ParseJSON("$.vendor.value.slug").Trim() )

uploadjson przekazuje obrazy do dropbox tworząc automatycznie foldery

ListCombine( thisRow.rpJSON.ParseJSON("$.main_image.value.m_img_1500") .Trim(), PineMintRPUtils::FetchRawJsonFile( Concatenate( "https://rynekpierwotny.pl/api/v2/offers/offer/", thisRow.rpJSON.ParseJSON("$.id").Trim(), "/?s=offer-detail-gallery" ) ) .ParseJSON( "$.gallery.*.image.g_img_1500" ) ) .Filter( CurrentValue.IsNotBlank() ) .ForEach( PineMintDropbox::DBFastSaveUrlToDropbox( [Wojtek Sosnowski], CurrentValue, Join( "/", "/Public/USI", Konkurenci .Filter( rpID = thisRow.rpJSON.ParseJSON("$.vendor.value.id").Trim() ) .usiFolder, thisRow.rpSlug, RegexExtract(CurrentValue, "(?<=/)[^/]+.(?:jpg|png)") ) .Trim() ) )




dodajwidok 

ModifyRows( thisRow, thisRow.Widok, PineMintDropbox::DBUpdateImageThumbnail( [Wojtek Sosnowski], Concatenate( "/Public/USI/", thisRow.Deweloper.usiFolder, "/", thisRow.rpSlug, "/", PineMintDropbox::DBQuickListUrls( [Wojtek Sosnowski], Join( "/", "/Public/USI", thisRow.Deweloper.usiFolder, thisRow.rpSlug ) ) .RegexReplace( "dl=0", "dl=1" ) .Split( "," ) .RegexExtract( "[^/]+.(?:jpg|webp|jpeg|png)" ) .Filter( CurrentValue.IsNotBlank() ) .First() ), "w640h480" ) )

dodajUSI

AddRow( USImaster, USImaster.Inwestycja, thisRow.Inwestycja, USImaster.Deweloper, Konkurenci .Filter( rpID = thisRow.rpJSON.ParseJSON("$.vendor.value.id").Trim() ), USImaster.[google-maps], Concatenate( "https://www.google.com/maps/@", thisRow.rpJSON.ParseJSON("$.geo_point.value.coordinates.value").Split(",") .Last() .Trim(), ",", thisRow.rpJSON.ParseJSON("$.geo_point.value.coordinates.value").Split(",") .First() .Trim(), ",17z?hl=pl" ), USImaster.Termin, Concatenate( RoundDown( thisRow.rpJSON.ParseJSON("$.construction_date_range.value.upper").Trim() .ToDate() .Month() / 4 ) + 1, " kw. ", thisRow.rpJSON.ParseJSON("$.construction_date_range.value.upper").Trim() .ToDate() .Year() ), USImaster.strona_rynek, thisRow.rpAdres, USImaster.Ocena, "Brak", USImaster.strona_inwestycji, thisRow.rpJSON.ParseJSON("$.website").Trim(), USImaster.[Liczba Mieszkań], thisRow.rpJSON.ParseJSON("$.properties").Trim(), USImaster.rpJSON, thisRow.rpJSON, USImaster.USIfolder, thisRow.rpSlug, USImaster.rpID, thisRow.rpID, USImaster.Widok, thisRow.Widok )

rpscrape jest tabelą tymczasową

usuntemp czyści

Jeżeli inwestycja się powtarza to usuntemp można nacisnąc od razu a inne przyciski nie działają. Disabled if "USImaster.rpID.Contains(thisRow.rpID).Not()" and " thisRow.rpJSON.ParseJSON("$.type") != 3 AND thisRow.rpJSON.ParseJSON("$.region.value.country") = 1"



mam API key dla dropbox i scraperapi.

w specyfikacji do budowania skryptu trzeba będzie zawrzeć informacje o testach (robiłem wielokrotnie testy żeby to wszystko działało w coda bo trzeba było empirycznie sprawdzać wiele rzeczy)



1. lokalnie na mac os, raz dziennie
    
2. dodawanie dnia miało pomóc ominać cache, rynek pierwotny nie generuje więcej niż 30 wyników za jednym razem. Dla otodom 72 to limit ich strony. geograficznie cała polska
    
3. tryb przyrostowy
    
4. scrape_log.txt, new_investments.json, investments_index.json
    
5. rpJSONmainV2 - to miało pomóc ominąć cache
    
6. te filtry jeżeli są w linku zapytania generujący JSON mają tam pozostać
    
7. ma traktować osobno, matchowanie jest trudne, używam do tego USIojciec



jeszcze: pliki tekstowe mają być zapisywane w równoległym drzewie katalogów naśladującym drzewo z plikami graficznymi

plik JSON generowany przez coda.io ma mieć inną nazwę niż generowany przez skrypt.

przy zasysaniu nowych inwestycji skrypt ma zostawiać plik JSON uproszczony i pełen ze strony

budowa ma być modularna i umożliwiać dodanie kolejnych serwisów jak tabelaofert.pl, gratka.pl itp.

budowa ma umożliwiać sprawdzanie strony internetowej wskazanej przez rynekpierwotny.pl jako strony inwestycji. niestety czasami strona nie jest stroną inwestyji ale stroną domową dewelopera. chciałbym w przyszłości robić prosty scrape galerii ze strony inwestycji, albo jej monitoring.

problem z cache był problemem coda.io która przetrzymywała za długo plik. nie jest to zagadnieniem w przypadku skryptu.


struktura katalogów ma być dokładnie taka sama jak teraz w równoległym drzewie zaczynającym się od USIdata zamiast USI. Te dwa katalogi nadrzędne będę obok siebie.

`/Public/
  ├── USI/                              ← Obrazy (jak obecnie)
  │   ├── {vendor-slug}/
  │   │   ├── {investment-slug}/
  │   │   │   ├── image_001.jpg
  │   │   │   ├── image_002.webp
  │   │   │   └── ...
  │
  └── USIdata/                          ← Dane JSON (nowe, mirror struktury)
      ├── {vendor-slug}/
      │   ├── {investment-slug}/
      │   │   ├── rp_seed.json         ← Pełny JSON z RP API
      │   │   ├── rp_simple.json       ← Uproszczony JSON z RP
      │   │   ├── oto_seed.json        ← Pełny JSON z Otodom (jeśli istnieje)
      │   │   ├── oto_simple.json      ← Uproszczony JSON z Otodom
      │   │   ├── coda_export.json     ← Eksport z Coda (ręcznie/przez API)
      │   │   └── merged_data.json     ← Merged + metadata z Coda`



zostawmy te pola, później będziemy ewentualnie ograniczać. przygotuj specyfikację w pliku .md

specyfikacja jest przeznaczona dla LLM typu Cursor do przeanalizowania wraz z plikami przykładowymi. Specyfikacja nie musi zawierać docelowego kodu tylko wytyczne do jego napisania.


Dropbox musi nadal być wykorzystywany. Skrypt działa lokalnie i zapisuje lokalnie w katalogu dropbox. Pliki są synchronizowane. Alternatywnie skrypt wykorzystuje API dropboxa i kieruje tam pliki tak jak to odbywa się obecnie przez coda.io


ważne jest pozostawienie interoperacyjności z coda.io

  

coda.io zapisze przy użyciu nowej funkcji/packa wszystkie rekordy w formie plików JSON. to stworzy nowe drzewo w katalogu USIdata

  

pliki nadal przechowywane w dropbox z lokalną kopią

  

skrypt będzie dopisywał swoje pliki JSON które będą mogły być czytane przez coda.

  

Pliki tworzone przez coda nie będą modyfikowane przez skrypt i pliki tworzone przez skrypt nie będą modyfikowane przez coda. Ważne jest rozróżnienie nazw.