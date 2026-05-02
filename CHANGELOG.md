# CHANGELOG

## Pizzeria — 2026-05-02

- Odświeżono nawigację UI: dodano wysuwaną szufladę (Drawer) z obsługą trybu jasnego/ciemnego i ulepszono spójność designu.
- Przeniesiono silnik scrapowania na bibliotekę `Scrapling` oraz wdrożono mechanizm bezpiecznej aktualizacji rekordów JSON z logowaniem zmian.
- Zaimplementowano w pełni stylizowaną mapę Dashboardu (HERE Maps) z precyzyjnym oznaczaniem inwestycji.
- Zoptymalizowano widok szczegółów: nowe HeroBand z ocenami waźonymi USI oraz przebudowany układ kolumn i udogodnień.
- Stworzono dedykowaną podstronę "Pobieranie" do zarządzania nowościami z portali (RP, Otodom) wraz z dedykowanymi endpointami API.
- Opracowano i sformalizowano dokumentację Design Systemu oraz nazewnictwo komponentów frontendu.

## Buda z kebabem — 2026-05-01

- Zaimplementowano modułowe scrapery dla Otodom, RynekPierwotny i TabelaOfert z obsługą Fetchera (curl_cffi i ScrapperAI).
- Wdrożono integrację z mapami HERE (minimapy, stylizacja, synchronizacja współrzędnych).
- Stworzono responsywny interfejs użytkownika (React) z widokiem listy 6000+ inwestycji, filtrowaniem i zaawansowanym widokiem detali.
- Wprowadzono system oceniania inwestycji w kategoriach oraz automatyczne obliczanie oceny złożonej.
- Zaimplementowano audyt zmian (created_at/updated_at) oraz mechanizm rozdzielania rekordów dualnych (RP+OTO).
- Zoptymalizowano strukturę danych i schematy JSON oraz usprawniono proces importu z CSV (USImaster).
