# Specyfikacja Architektury: Szyna Danych (DataBus)

## 1. Cel i Motywacja
Szyna Danych (DataBus) w systemie USI Tracker została wprowadzona, aby umożliwić luźne powiązanie (loose coupling) między niezależnymi komponentami interfejsu. Pozwala ona na współdzielenie stanu (np. aktualnie wybranej inwestycji, listy widocznych rekordów) bez konieczności przekazywania właściwości (props) przez wiele poziomów komponentów.

## 2. Architektura Techniczna
Szyna danych opiera się na mechanizmie **React Context API**, co zapewnia natywną integrację z cyklem życia komponentów React bez dodatkowych bibliotek zewnętrznych.

### 2.1. Składniki systemu:
- **DataBusContext**: Definiuje strukturę danych i metody dostępu.
- **DataBusProvider**: Komponent opakowujący aplikację, przechowujący aktualny stan szyny w `useState`.
- **useDataBus**: Hook umożliwiający komponentom dostęp do danych (`bus`) oraz metod ich aktualizacji (`setVariable`).

### 2.2. Model Danych (Store)
Obecnie szyna obsługuje następujące kluczowe zmienne:
- `visibleInvestments`: Lista inwestycji aktualnie wyświetlanych na głównej liście (po uwzględnieniu filtrów i wyszukiwania).
- `currentInvestment`: Obiekt inwestycji aktualnie otwartej w widoku szczegółowym.
- `nearbyInvestments`: Lista inwestycji znajdujących się w bezpośrednim sąsiedztwie (domyślnie 5km) od `currentInvestment`.

## 3. Przepływ Danych (Data Flow)

### 3.1. Producenci (Producers)
Komponenty odpowiedzialne za generowanie danych:
- **ListGrid / App**: Aktualizuje `visibleInvestments` przy każdej zmianie filtrów.
- **DetailRightPanel**: Publikuje `currentInvestment` w momencie montowania komponentu i czyści ją przy odmontowywaniu.

### 3.2. Konsumenci (Consumers)
Komponenty reagujące na dane:
- **Moduły Raportowe**: Pobierają listy inwestycji do generowania map i wykresów.
- **Widżety Analityczne**: (W przyszłości) np. widżet "Sąsiednie inwestycje" na karcie szczegółowej.

## 4. Wydajność i Optymalizacje
- **Ograniczenie zdarzeń**: Zrezygnowano z przesyłania zdarzeń o wysokiej częstotliwości (np. `hover` nad elementem listy), aby uniknąć nadmiarowych re-renderów całej aplikacji.
- **Memoizacja**: Metody `setVariable` i `getVariable` są owinięte w `useCallback`, a wartość kontekstu w `useMemo`.
- **Stabilność referencyjna**: Nowe wartości są ustawiane tylko wtedy, gdy faktycznie różnią się od poprzednich (płytkie porównanie).

## 5. Rozszerzalność
System pozwala na łatwe dodawanie nowych zmiennych poprzez prosty wywołanie `setVariable(name, value)`. Nazewnictwo zmiennych powinno być spójne z konwencją `camelCase`.
