# Specyfikacja Progress Bar

## Miejsce

Powiadomienia wyświetlane są w bloku `usi-navbar-center`

## Sposob prezentacji

Powiadomienia to czysty tekst, informujacy uzytkownika o obecnie trwajacych zadaniach typu "job" np. process_batch albo pojedynczy scraper.

Powiadomienie jest wyswietlane dopóki trwa zadanie. Postep jest pokazywany przez wskaznik procentowy lub inny licznik w zaleznosci od typu zadania. Przykładowo proces batch pokazyje postep w kategoriach (na podstawie liczby scraperów) a pojedynczy scraper pokazuje licznik scraperów i postep procentowy. Po zakonczeniu zadania postep jest czyszczony.

## Status Implementacji (2026-05-18)

1.  **Backend (`jobs.py`)**: 
    *   `JobManager` zarządza zadaniami w tle (kolejkowanie, wątki). [ZREALIZOWANE]
    *   API `/api/jobs` zwraca status i postęp. [ZREALIZOWANE]
2.  **Frontend (`data.jsx`, `core.jsx`)**:
    *   Polling aktywnych zadań w `DataBus` z mechanizmem "Sticky" (5s). [ZREALIZOWANE]
    *   Komponent `NotificationCenter` wyświetla status tekstowy i kropkowy pasek postępu. [ZREALIZOWANE]

## Wygląd paska ASCII (Kropki)

Pasek postępu jest renderowany w formacie kropkowym o stałej szerokości 10 znaków, co zapobiega przesuwaniu się elementów Navbara.

*   `●` (pełna kropka) - postęp zakończony
*   `○` (pusta kropka) - postęp pozostały

Przykład: `> UPDATE-DEV: Processing... ●●●○○○○○○○ [3/10]`

## Plan Dalszego Rozwoju

1. **Estetyka i animacja**:
    *   Dodanie opcjonalnej animacji "indeterminant" (migające kropki) dla zadań o nieokreślonym czasie trwania.
2. **Integracja ze skryptami CLI**:
    *   Pełna integracja z `InvestmentService.process_batch`, aby pasek odzwierciedlał postęp całej paczki.