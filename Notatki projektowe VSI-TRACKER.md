# **Notatki projektowe USI-TRACKER**

**Elementy interfejsu i funkcjonalności:**

1. Przycisk do zeskanowania nowości bez pobierania.  
2. Przycisk do pobierania.  
3. Przycisk dropdown wyboru strony lub opcji "wszystkie".  
4. Postęp w formie: napis informujący o aktualnym działaniu oraz tekstowa belka postępu.  
5. Delay między zapytaniami, szczególnie dla Otodom (ryzyko blokowania).  
6. Graficzna informacja o liczbie nowych ofert na inwestycji.

## **Deweloperzy**

1. Potrzebna baza wykrytych deweloperów (katalog /public/usidev).  
2. Surowe JSONy deweloperów ze stron.  
3. JSONy łączące (nadrzędne): łączące w grupy rekordy z różnych portali, grupy kapitałowe spółek, spółki-córki, nowe ID tego samego dewelopera.  
4. Heurystyka wykrywania podobieństw.  
5. Widok listy deweloperów.  
6. Filtrowanie i wyszukiwanie deweloperów.  
7. Widok rekordu dewelopera.  
8. W rekordzie dewelopera sugestie powiązań spółek na podstawie heurystyki.  
9. Przycisk sprawdzania nowych inwestycji na portalach.  
10. Przycisk wysyłający "Job" pobierania.  
11. Statystyki dla miast: liczba inwestycji, liczba mieszkań, średnia ważona ocen inwestycji.

## **Raporty**

1. Podstrona raporty.  
2. Lista raportów generowana na podstawie JSONów.  
3. JSONy raportów określają filtry inwestycji (np. GUS, region, deweloper, odległość od punktu na mapie).  
4. JSONy raportów określają moduły prezentacji pokazywane w raporcie.  
5. Moduły (wymagają danych wejściowych):  
   * Mapa z punktami (wymaga listy).  
   * Wykres zmian cen w czasie (wymaga listy cen).  
   * Wykres zmian oceny w czasie (wymaga listy ocen).  
   * Wykres ceny w zależności od oceny.  
   * Wykres zmian oceny w kategorii w czasie.  
6. Zapewnienie uniwersalności i elastyczności modułów (możliwość osadzania w innych miejscach).

## **Moduły Raportów (VSI-TRACKER)**

1. Każdy widok generuje zestaw zmiennych używanych później przez moduły.  
2. Minimapa w widoku rekordu inwestycji również może funkcjonować jako moduł.  
3. Przemyślenie architektury zmiennych wejściowych dla modułów.  
4. Przemyślenie architektury samych modułów.  
5. Użycie minimapy jako modułu testowego.  
6. Moduły akceptują szerokość obiektu obejmującego.  
7. Potencjalnie przydatne zmienne:  
   * Lista rekordów.  
   * Punkt geo.  
   * Ocena \[0-4\].  
   * Kolor.  
   * Liczba mieszkań z rekordów według kwartałów.  
   * Ocena ważona (suma) z rekordów według kwartałów.

## **Obliczenia**

Formuły stosowane w systemie:

1\. Ocena ważona \= Ocena \* Liczba mieszkań  
2\. Średnia ważona \= Σ Ocena ważona / Σ Liczba mieszkań  
