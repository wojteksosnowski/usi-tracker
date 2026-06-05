# TODO

## Kamień 04
Po co wyświetlanie inwestycje uzywa `resolve_images` i skanuje caly dysk w poszukiwaniu obrazow?!?! Przeciez obrazy sa tam gdzie prowadza sciezki?!!? Tylko gdy obrazo nie ma we wskazanym miejscu powinno dojsc do wyszukania z dysku!!!!!!!!

## Kamień 05

Przeanalizowałem cykl życia widoku i backendu. Kiedy wchodzisz w Widok A,
UI renderuje inwestycję z "indeksu" (który jest odchudzony i ma
specjalnie tylko 1 zdjęcie). W tle UI wysyła zapytanie  GET              
/api/investment/<id>/data , aby dociągnąć pełne dane. I to właśnie tutaj
serwer zwalnia na te 0,5 - 1 sekundy.

Dlaczego zwalnia? Ponieważ backend ( investment_loader.py ) w tym
momencie generuje dane w locie, zamiast po prostu odczytać gotowy plik   
usi_*.json . Przy każdym wejściu w inwestycję serwer:

1. Skanuje cały katalog na dysku w poszukiwaniu wszystkich obrazków (    
resolve_images ).
2. Czyta i dołącza osobne pliki  ratings.json ,  deletion_list.json  czy
master_*.json .
3. Oblicza w locie punkty za udogodnienia ( amenities_score ) i
podpowiedzi.

Zgodnie z Twoją dyrektywą:  usi_*.json  jest plikiem właściwym dla
trackera i powinien być ostatecznym "agregatem" wiedzy, a nie pustą
wydmuszką generowaną przy każdym zapytaniu. Część rzeczy (jak sugestie
czy POI) już zapisuje się wewnątrz  usi_*.json , ale lista ścieżek zdjęć,
oceny uogólnień i inne metadane nie są w nim utrwalane.

Aby całkowicie zlikwidować ten lag i wprowadzić Twoją architekturę,
proponuję następujący plan działania:

1. Migracja danych: Napiszę i uruchomię krótki skrypt (np.               
backfill_usi_data.py ), który przejdzie przez wszystkie inwestycje,
wygeneruje dla nich ostateczną listę  photos , wyliczy  amenities_score 
itp. i zapisze to na twardo w każdym pliku  usi_*.json .
2. Uproszczenie Loadera: Przepiszę  investment_loader.py , aby przestał
skanować dysk i przetwarzać dane w locie – będzie jedynie wczytywał i
serwował to, co jest już zapisane w  usi_*.json .
3. Logika aktualizacji: Upewnię się, że wszelkie nowe zmiany (np.
pojawienie się nowego zdjęcia) będą powodowały aktualizację wpisu w      
usi_*.json .