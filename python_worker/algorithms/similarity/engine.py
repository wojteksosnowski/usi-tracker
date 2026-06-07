import logging
from typing import List, Dict, Any, Set, Optional
from .strategies import (
    SimilarityStrategy,
    NameSimilarityStrategy,
    GeoProximityStrategy,
    SharedInvestmentStrategy,
    InvestmentTokenOverlapStrategy
)

logger = logging.getLogger(__name__)

class DeveloperMatcher:
    """
    Zoptymalizowany silnik parowania deweloperów. 
    Wprowadza przeszukiwanie lustrzane w RAM oraz tranzytywne przycinanie grafu porównań.
    """
    
    def __init__(self, strategies: Optional[List[SimilarityStrategy]] = None) -> None:
        self.strategies = strategies or [
            NameSimilarityStrategy(threshold=0.85),
            SharedInvestmentStrategy(),
            GeoProximityStrategy(),
            InvestmentTokenOverlapStrategy()
        ]

    def _is_excluded(self, d1: Dict[str, Any], d2: Dict[str, Any], dismissed_cache: Dict[str, Set[str]]) -> bool:
        id1 = d1.get("usi_dev_id")
        id2 = d2.get("usi_dev_id")
        
        if not id1 or not id2 or id1 == id2:
            return True

        # Sprawdzenie odrzuconych par w UI
        if id2 in dismissed_cache.get(id1, set()) or id1 in dismissed_cache.get(id2, set()):
            return True
            
        # Ten sam master_id oznacza, że deweloperzy są już scaleni
        if d1.get("master_id") and d1.get("master_id") == d2.get("master_id"):
            return True
            
        return False

    def find_suggestions_for_developer(
        self, 
        target_dev: Dict[str, Any], 
        all_developers: List[Dict[str, Any]], 
        dismissed_cache: Dict[str, Set[str]]
    ) -> List[Dict[str, Any]]:
        """
        Wyszukuje propozycje dla jednego dewelopera.
        Wykorzystuje pamięć podręczną innych obiektów i reguły tranzytywne w celu ominięcia I/O i CPU.
        """
        suggestions: List[Dict[str, Any]] = []
        target_id = target_dev.get("usi_dev_id")
        target_slug = target_dev.get("developer_slug")
        
        if not target_id:
            return []

        # KROK diagnostic-tranzytywny: Znajdź w pamięci RAM deweloperów skrajnie bliźniaczych do targetu
        # (np. filie, wersje ze sp. z o.o.), którzy zdążyli już wykonać skanowanie.
        clones_suggestions_map = {}
        name_strat = NameSimilarityStrategy()
        
        for candidate in all_developers:
            c_id = candidate.get("usi_dev_id")
            if not c_id or c_id == target_id:
                continue
                
            # Jeśli kandydat jest bliźniakiem (bardzo silne powiązanie nazwowe)
            if target_slug == candidate.get("developer_slug"):
                is_clone = True
            else:
                score, _ = name_strat.calculate(target_dev, candidate)
                is_clone = (score >= 0.95)
                
            if is_clone and candidate.get("suggestions"):
                # Przechwytujemy tylko te klony, które mają numeryczny score
                clones_suggestions_map[c_id] = {
                    s["usi_dev_id"]: s["score"] 
                    for s in candidate["suggestions"] 
                    if "usi_dev_id" in s and "score" in s
                }

        # GŁÓWNA PĘTLA PORÓWNAWCZA
        for candidate in all_developers:
            cand_id = candidate.get("usi_dev_id")
            if self._is_excluded(target_dev, candidate, dismissed_cache):
                continue

            # PANCERNA POPRAWKA: Przeszukanie lustrzane działa WYŁĄCZNIE, 
            # gdy w cache RAM/pliku kandydat posiada jawnie wyliczone i zapisane pole 'score'.
            # Brak tego pola oznacza stary format – wymuszamy wtedy pełne przeliczenie CPU.
            mirror_sug = next((s for s in candidate.get("suggestions", []) if s.get("usi_dev_id") == target_id), None)
            if mirror_sug and "score" in mirror_sug:
                suggestions.append({
                    "source_id": target_id,
                    "target_id": cand_id,
                    "target_slug": candidate.get("developer_slug") or "unknown",
                    "reason": f"[Lustro RAM] {mirror_sug.get('reason')}",
                    "score": float(mirror_sug["score"])
                })
                continue

            # OPTYMALIZACJA 2: Przycinanie tranzytywne (Zasada słabego powiązania).
            # Jeśli nasz bliźniak (B) skanował już tego kandydata (C) i ocenił go na 0.0,
            # to my (A) również przypisujemy mu 0.0 i całkowicie pomijamy CPU-heavy kalkulacje.
            pruned_by_transitivity = False
            for clone_id, clone_sugs in clones_suggestions_map.items():
                if cand_id in clone_sugs and clone_sugs[cand_id] == 0.0:
                    pruned_by_transitivity = True
                    break
            
            if pruned_by_transitivity:
                continue

            # REALNE OBLICZENIA (Tylko gdy brakuje danych w pamięci RAM)
            best_score = 0.0
            best_reason: Optional[str] = None
            
            for strategy in self.strategies:
                try:
                    score, reason = strategy.calculate(target_dev, candidate)
                    if score > best_score:
                        best_score = score
                        best_reason = reason
                except Exception as strategy_error:
                    logger.error(f"Błąd strategii {strategy.__class__.__name__} dla par {target_id} <> {cand_id}: {strategy_error}")
                    
            if best_score > 0.0 and best_reason:
                suggestions.append({
                    "source_id": target_id,
                    "target_id": cand_id,
                    "usi_dev_id": cand_id,  # DUBLOWANIE KLUCZA DLA ABSOLUTNEJ SPÓJNOŚCI API/UI
                    "target_slug": candidate.get("developer_slug") or "unknown",
                    "developer_slug": candidate.get("developer_slug") or "unknown",
                    "reason": best_reason,
                    "score": round(best_score, 4)
                })
                
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions


def calculate_similarities(devs: List[Dict[str, Any]], dismissed_cache: Dict[str, Set[str]] = None) -> List[Dict[str, Any]]:
    """
    Batch wrapper kompatybilny wstecznie. 
    Dzięki lustrzanym odbiciom w pamięci RAM wydajność rośnie drastycznie z każdą kolejną iteracją pętli.
    """
    matcher = DeveloperMatcher()
    all_suggestions = []
    dismissed_cache = dismissed_cache or {}
    
    valid_devs = [d for d in devs if d.get("usi_dev_id")]
    
    for i, dev1 in enumerate(valid_devs):
        # Przekazujemy wszystkich deweloperów. 
        # Z każdym krokiem pętli coraz więcej par jest rozwiązywanych przez OPTYMALIZACJĘ 1 (Mirror).
        remaining_devs = [d for j, d in enumerate(valid_devs) if i != j]
        suggestions = matcher.find_suggestions_for_developer(dev1, remaining_devs, dismissed_cache)
        
        # Filtrujemy tylko wartościowe sugestie do zwrotu
        valid_suggestions = [s for s in suggestions if s["score"] >= 0.75]
        all_suggestions.extend(valid_suggestions)
        
        # Aktualizujemy obiekt w pamięci podręcznej RAM dla kolejnych deweloperów w pętli batcha!
        # To kluczowe, aby następne iteracje widziały co wyliczył dev1.
        # KRYTYCZNA POPRAWKA: Zapisujemy w RAM tylko te sugestie, które spełniają próg (score >= 0.75).
        # Brak filtrowania w tym miejscu powodował zalewanie pamięci tysiącami śmieciowych par o score > 0.0.
        dev1["suggestions"] = [
            {
                "usi_dev_id": s["target_id"],
                "target_id": s["target_id"], # Pancerne powielenie klucza ID
                "developer_slug": s["target_slug"],
                "score": s["score"],
                "reason": s["reason"]
            } for s in suggestions if s["score"] >= 0.75
        ]

    return all_suggestions
