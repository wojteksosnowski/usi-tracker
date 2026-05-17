# Specyfikacja Progress Bar

## Miejsce

Powiadomienia wyświetlane są w bloku `usi-navbar-center`

## Sposob prezentacji

Powiadomienia to czysty tekst, informujacy uzytkownika o obecnie trwajacych zadaniach typu "job" np. process_batch albo pojedynczy scraper.

Powiadomienie jest wyswietlane dopóki trwa zadanie. Postep jest pokazywany przez wskaznik procentowy lub inny licznik w zaleznosci od typu zadania. Przykładowo proces batch pokazyje postep w kategoriach (na podstawie liczby scraperów) a pojedynczy scraper pokazuje licznik scraperów i postep procentowy. Po zakonczeniu zadania postep jest czyszczony.

Postep moze byc pokazywany takze w sposob grafiki tekstowej ANSII, ktora pozwalaja na wizualny pokaz postepu. 

Czcionka z design system typu monospace powinna byc uzyta do grafiki tekstowej.